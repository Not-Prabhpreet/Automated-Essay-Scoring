# Essay Grader: project overview

An automated essay scorer for the eight prompts of the ASAP dataset. It returns a score together with the evidence needed to judge it: a 90% score range, the three most similar essays human raters already graded, and a flag when a teacher should check the score. It answers in about a tenth of a second on a single shared CPU.

- Live site: https://essay-grader-ai.vercel.app
- API: https://aes-grader-api.fly.dev (`POST /score`)
- Code: https://github.com/Not-Prabhpreet/Automated-Essay-Scoring

All numbers below are measured on held-out test essays and come from the scripts and `results/*.json` files in the repository.

## Contents

1. [Results at a glance](#1-results-at-a-glance)
2. [Architecture](#2-architecture)
3. [Data and evaluation protocol](#3-data-and-evaluation-protocol)
4. [The original model (baseline)](#4-the-original-model-baseline)
5. [Features: TF-IDF and style](#5-features-tf-idf-and-style)
6. [Scoring model](#6-scoring-model)
7. [Score ranges: split conformal prediction](#7-score-ranges-split-conformal-prediction)
8. [Similar essays as evidence](#8-similar-essays-as-evidence)
9. [The review flag](#9-the-review-flag)
10. [API](#10-api)
11. [Performance engineering](#11-performance-engineering)
12. [Deployment](#12-deployment)
13. [Website](#13-website)
14. [Tests](#14-tests)
15. [Reproducing the results](#15-reproducing-the-results)
16. [Limitations and next steps](#16-limitations-and-next-steps)

---

## 1. Results at a glance

| | Result |
|---|---|
| Agreement with human raters (mean QWK over 8 prompts) | **0.747**, against 0.579 for the original LSTM + Random Forest |
| 90% score ranges, actual coverage on test | **90.8%**, average width 21.6% of the score scale |
| Review flag | flags 19.4% of essays and catches 32.7% of large errors |
| Grading time | **16 ms** median to grade an essay; ~0.1 s per request on the live server, network included |
| Server | 1 shared vCPU, 512 MB; ~350 MB used; 147 MB Docker image |

QWK (quadratic weighted kappa) is the ASAP competition metric: 1 means perfect agreement with the human score, 0 means chance, and a miss of two points costs four times as much as a miss of one.

## 2. Architecture

```
                   ┌───────────────────────────────┐
 essay + prompt ──▶│ TF-IDF: word 1-2 + char 2-5   │──┬──────────────▶ nearest training essays ──▶ similar essays
 (one of 8 sets)│  └───────────────────────────────┘  │  (word TF-IDF cosine)  │
                │  ┌───────────────────────────────┐  ▼                        │ spread of their scores = σ
                └─▶│ style features (20)           │─▶ ridge model (per set) ──┴─▶ score ─▶ 90% range = score ± q·σ
                   └───────────────────────────────┘                                            │
                                                                                                 ▼
                                                                         needs_review (range unusually wide)
```

| Component | Where |
|---|---|
| Data, splits, QWK | `grader/data.py`, `grader/metrics.py`, `data/splits.csv` |
| TF-IDF features and per-prompt model | `grader/features.py` |
| Style features (legacy, sped up) | `models/feature_extractor.py`, `grader/style.py` |
| Conformal ranges | `grader/conformal.py` |
| Similar essays | `grader/neighbors.py` |
| Review flag | `grader/review.py` |
| Runtime grader used by the API | `grader/service.py` |
| API | `api/main.py`, `api/schemas/essay.py` |
| Training and evaluation | `scripts/` |
| Website | `frontend/` |

## 3. Data and evaluation protocol

**ASAP** (Automated Student Assessment Prize, Hewlett Foundation, 2012): 12,976 essays by students in grades 7–10, written for eight prompts and scored by trained human raters. Each prompt has its own rubric and scale:

| Set | Prompt | Type | Grade | Resolved score |
|---|---|---|---|---|
| 1 | Effects of computers (letter to a newspaper) | Persuasive | 8 | 2–12 (two raters × 1–6) |
| 2 | Censorship in libraries | Persuasive | 10 | 1–6 |
| 3 | “Rough Road Ahead”: setting and the cyclist | Response to a text | 10 | 0–3 |
| 4 | “Winter Hibiscus”: why the story ends this way | Response to a text | 10 | 0–3 |
| 5 | “Narciso Rodriguez”: mood of the memoir | Response to a text | 8 | 0–4 |
| 6 | “The Mooring Mast”: docking dirigibles | Response to a text | 10 | 0–4 |
| 7 | Patience | Narrative | 7 | 0–24 (two raters × four traits 0–3) |
| 8 | Laughter | Narrative | 10 | 0–60 (composite of six traits 1–6) |

**Fixed split.** Each prompt's essays are shuffled with seed 42 and split 60/10/15/15. The split is committed (`data/splits.csv`), so every model sees the same test essays, and a test checks that it can be recreated from the seed.

| Split | Essays | Used for |
|---|---|---|
| train | 7,786 | TF-IDF vocabularies, the ridge models, the similar-essay index |
| val | 1,297 | every choice: ridge penalty, conformal variant, review threshold |
| calib | 1,946 | only the conformal quantiles |
| test | 1,947 | read once, for reported numbers |

## 4. The original model (baseline)

The repository started with an LSTM on averaged Word2Vec vectors and a Random Forest on 20 hand-crafted features, outputting a 0–10 score. Before evaluating it unchanged (`scripts/baseline.py`), two compatibility problems had to be solved:

- The RF was pickled with scikit-learn 0.24.2, and current scikit-learn refuses its tree format. `grader/legacy_io.py` adds the missing `missing_go_to_left` field (all zeros, which doesn't change predictions) and computes the forest's prediction directly from the trees.
- The LSTM was saved by TensorFlow 2.8 as Keras 2 HDF5, so it is loaded with `tf_keras`.

**Baseline: mean QWK 0.579 on test** (set 1: 0.852; set 4: 0.334). Findings worth knowing:

- The RF was trained on only the first 500 rows of the data file, all from set 1. 73 of the 268 set 1 test essays were among them; without them its set 1 QWK is 0.824.
- The notebooks are empty, so what the LSTM was trained on is unknown.
- One RF and one LSTM served all eight prompts, with hand-tuned per-set multipliers instead of a model per prompt.

## 5. Features: TF-IDF and style

### TF-IDF

**TF-IDF** (term frequency × inverse document frequency) gives every term a weight for each essay. The weight is high when the term is frequent in this essay but rare across the prompt's training essays, and near zero for terms every essay uses. Term frequency is sublinear (`1 + log tf`), and each essay's vector is L2-normalised so long essays don't get larger weights just for being long.

Two vocabularies are learned per prompt, from that prompt's training essays only (`grader/features.py`):

| Block | Terms | Settings | What it captures |
|---|---|---|---|
| Word n-grams | single words and word pairs | `ngram_range=(1, 2)`, `min_df=2`, up to 30,000 terms | what the essay talks about, its phrasing |
| Character n-grams | 2–5 letters inside word boundaries (`char_wb`) | `min_df=3`, up to 40,000 terms | spelling, word forms, vocabulary level; still matches when a word is misspelled |

Each prompt's model has 22,900–60,615 columns. Any single essay uses only a few hundred to a few thousand of them, so the features are stored as sparse matrices.

**A real example** (sample essay #17969, set 7, the patience prompt): the highest-weighted word terms are `location3` (0.23), `to location3` (0.20), `mood` (0.19), `eat` (0.15) and `bored` (0.14), while `the` gets 0.04 because every essay uses it. ASAP replaced names and places with placeholders like `@LOCATION3`, so those become terms too. Among the character n-grams, `paite` and `aiten` (0.09) come from the student's misspelling "paitent".

### Style features

The 20 measurements from the original project (`models/feature_extractor.py`), computed on the essay after removing punctuation and stop words: word, sentence and paragraph counts, average word and sentence length, likely spelling mistakes, unique-word ratio, long-word ratio, transition words and a sentiment score, plus two combined scores. They are standardised before modelling.

The spelling count uses TextBlob's spell checker. Section 11 describes how it was made fast without changing its answers.

## 6. Scoring model

Each prompt gets its own **ridge regression** on `[word TF-IDF | char TF-IDF | standardised style features]`, trained only on that prompt's essays. Ridge is a weighted sum of all columns with a penalty that keeps weights small, so it doesn't memorise ~1,000 training essays. The penalty α ∈ {0.3, 1, 3, 10} is chosen per prompt on val (chosen: 3, 1, 10, 1, 10, 0.3, 0.3, 0.3 for sets 1–8). Predictions are rounded and clipped to the prompt's scale.

| Variant (each tuned on val) | Mean test QWK |
|---|---|
| Original model (LSTM + RF) | 0.579 |
| Style features only (ridge) | 0.684 |
| TF-IDF only (ridge) | 0.680 |
| **TF-IDF + style (ridge), deployed** | **0.747** |

Neither half is enough on its own; together they gain about 0.07. TF-IDF captures content and phrasing; the style features capture length and surface quality.

Per prompt (test QWK):

| Set | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | Mean |
|---|---|---|---|---|---|---|---|---|---|
| Original LSTM + RF | 0.852 | 0.585 | 0.463 | 0.334 | 0.653 | 0.644 | 0.415 | 0.684 | 0.579 |
| TF-IDF + style (ridge) | 0.850 | 0.642 | 0.607 | 0.808 | 0.799 | 0.805 | 0.760 | 0.702 | **0.747** |

The new model is better on seven of eight prompts and about equal on set 1, where the original model had seen 73 of the test essays during training.

## 7. Score ranges: split conformal prediction

A single number hides how uncertain the model is. **Split conformal prediction** turns errors on held-out essays into a range with a coverage guarantee: if a new essay is exchangeable with the calibration essays, its human score lies in the range with probability at least 90%. No assumption about the error distribution is needed.

For each prompt s:

1. Predict the calibration essays (which never touched training or hyper-parameter choice).
2. Compute the nonconformity score `r_i = |y_i − ŷ_i| / σ_i`.
3. Take `q_s`, the ⌈(n+1)·0.9⌉-th smallest `r_i`.
4. For a new essay, the range is `ŷ ± q_s·σ`, rounded inward to integers and clipped to the scale. A score lies in the continuous interval exactly when it lies in the integer one, so the guarantee carries over.

**Difficulty σ.** σ = 0.1 × scale + the standard deviation of the human scores of the essay's 25 nearest training essays (word TF-IDF cosine). Essays that resemble essays humans scored very differently get wider ranges. This *normalised* variant was chosen over plain conformal (σ = 1), which gives every essay of a prompt the same width and so can't single out uncertain essays. The deployed setting (k = 25, β = 0.1) is the narrowest normalised option on val.

| | Test coverage | Average width |
|---|---|---|
| **Normalised (deployed)** | **90.8%** | 21.6% of the scale |
| Plain (for comparison) | 90.1% | 20.8% of the scale |

| Set | Scale | Test coverage | Average width |
|---|---|---|---|
| 1 | 2–12 | 92.2% | 1.8 points |
| 2 | 1–6 | 91.1% | 0.7 |
| 3 | 0–3 | 88.0% | 0.8 |
| 4 | 0–3 | 90.9% | 0.7 |
| 5 | 0–4 | 95.6% | 0.8 |
| 6 | 0–4 | 93.3% | 0.8 |
| 7 | 0–24 | 85.6% | 7.6 |
| 8 | 0–60 | 85.3% | 11.7 |

The guarantee holds on average over essays, so per-set coverage scatters around 90% with 109–271 test essays per set. Sets 7 and 8 land at about 85%, which is within sampling noise for 236 and 109 essays but worth watching.

## 8. Similar essays as evidence

For every essay the API returns the three training essays for the same prompt whose **word TF-IDF vectors** are closest by cosine similarity, with their human scores and an excerpt. Essays that share distinctive words and phrases tend to make similar points. If the neighbours scored close to the prediction, the score is easy to believe; if they're scattered, it isn't.

Only the word block is used for similarity. It's far sparser than the character block, which keeps the index small (the whole model file is 13 MB) and the search fast. TF-IDF cosine values are naturally low (the top match is typically 0.14–0.27), so the website shows neighbours by rank ("closest match") and puts the exact value in a tooltip.

**Leakage guard:** the index contains only the train split, so a val, calib or test essay can never retrieve itself or its own score. If a training essay is graded, the service can exclude its own id. Tests check both, plus that every essay is in exactly one split.

## 9. The review flag

`needs_review` is true when the essay's continuous range width (2·q·σ, before rounding) is high compared with val essays of the same prompt. Widths are turned into within-prompt percentiles, so one cut-off works across very different scales. The cut-off is chosen on val to catch as many **large errors** as possible while flagging at most the budgeted share of essays. A large error is `|round(prediction) − human| ≥ max(2, 0.2 × scale)`: at least two points, and at least a fifth of the scale on the wide sets (set 7: ≥ 5, set 8: ≥ 12).

Large errors are rare: **55 of 1,947 test essays (2.8%)**.

| Budget | Essays flagged (test) | Large errors caught |
|---|---|---|
| 10% | 9.0% | 16.4% |
| **20% (deployed)** | **19.4%** | **32.7%** |
| 30% | 26.0% | 43.6% |

At the deployed budget the flag catches about 1.7× as many large errors as flagging the same share at random would. It helps, but an unflagged score can still be wrong, and with 55 large errors these rates are noisy.

## 10. API

`POST /score` with `{"essay": "...", "essay_set": 1-8}`. The original fields keep their meaning (`score` on a 0–10 scale, `feedback`), so older clients still work. Added fields:

| Field | Meaning |
|---|---|
| `raw_score`, `score_scale` | Score on the prompt's own scale |
| `range` | 90% range: `low`, `high` (native scale), `low_normalized`, `high_normalized` (0–10), `coverage` |
| `needs_review`, `review_reasons` | `["wide_range"]` when flagged |
| `similar_essays` | Three nearest training essays: `essay_id`, human `score`, `similarity`, `excerpt` |
| `model` | Which model produced the score |

`feedback` is the original project's rule-based writing hints (sentence variety, spelling, transitions); it doesn't affect the score. If the model artifact is missing, `/score` falls back to the original model and leaves the new fields empty.

## 11. Performance engineering

| Technique | Effect |
|---|---|
| TF-IDF and a linear model, sparse throughout | Scoring is one sparse dot product; no GPU, no model download |
| Spelling: dictionary lookup first; for an unknown lowercase word, TextBlob's `correct()` changes it exactly when a dictionary word is within two edits, so that existence is answered directly. The first edit is enumerated with TextBlob's own generator (~500 strings); the second uses a precomputed index of one-letter deletions of the 29,157-word dictionary (plain and position-keyed) instead of ~500 more lookups per string. | Same answers as TextBlob: 0 mismatches on 1,798 tokens and 14,300 essay words, identical counts on 3,000 essays. Per essay from ~2 s to ~9 ms. |
| `models/__init__.py` imports the TensorFlow-based legacy scorer lazily | ~350 MB of memory instead of ~850 MB |
| One scoring thread, `OMP_NUM_THREADS=1`, warm-up request at start-up (which also builds the spelling index) | No thread contention on one vCPU; the first visitor doesn't wait |
| Slim Python 3.12 image, only FastAPI / scikit-learn / NLTK / TextBlob | 147 MB image |

Measured: 16 ms median (34 ms p90) to grade an essay in-process; 45 ms median through the API in a clean single-thread environment; ~108 ms median on the live server, measured from a client including the network.

## 12. Deployment

| Part | Host | Details |
|---|---|---|
| API | Fly.io (`aes-grader-api`, Toronto) | Docker, 1 shared vCPU, 512 MB + 512 MB swap, always on, health check on `/`, CORS limited to the site |
| Website | Vercel (`essay-grader-ai`) | Static Vite build, SPA rewrites, `VITE_API_URL` points at the API |

## 13. Website

React + Vite + Tailwind, in a paper-and-ink palette with light and dark themes.

- **Home:** a real API response for a held-out test essay, and measured headline numbers.
- **Grade:** the eight real ASAP prompts, a real held-out sample essay for each (its human score is shown for comparison), Ctrl + Enter to grade, the time each grade took, and the full result: score, range bar, review flag, feedback, similar essays.
- **How it works:** diagrams of the pipeline, data split, TF-IDF features (real weights for a sample essay) and conformal ranges; a QWK chart with tooltips and a table view; tables for every result.

Every number on the site is generated from `results/*.json` by `scripts/export_frontend_data.py`.

## 14. Tests

`pytest` (47 tests) covers:

- **QWK:** matches scikit-learn on random data, plus edge cases.
- **Conformal:** the finite-sample quantile; average coverage of at least 90% over 300 synthetic draws for both variants; reported test coverage within 0.87–0.95.
- **Leakage:** splits are disjoint and reproducible from the seed; the similarity index holds only training essays; a training essay graded through the service finds itself first and never appears once its id is excluded; calibration size matches the calib split.
- **Model:** TF-IDF features are sparse, similarity vectors have unit length, the model learns a toy task and picks its penalty on val.
- **API:** original and new fields, no removed fields, legacy fallback, validation errors, and an end-to-end request through the real artifact.
- **Spelling:** the fast check equals TextBlob's original on edge cases, real essay words and features computed with the original code; the deletion-index distance check equals brute force.

## 15. Reproducing the results

```bash
# Python 3.12
pip install -r requirements-grader.txt

python scripts/build_style_features.py      # style features for all essays (cached)
python scripts/baseline.py                  # original model -> results/baseline.json
python scripts/train_grader.py              # model, ranges, review flag, speed -> results/*.json, artifacts/grader.joblib
python scripts/export_frontend_data.py      # numbers for the website
pytest -q
uvicorn api.main:app --port 8000
```

## 16. Limitations and next steps

**Limitations**

- Only the eight ASAP prompts. An essay on any other topic gets a meaningless score.
- Scores reflect how 2012 raters graded grade 7–10 students. The reading-response prompts assume a source text the model never sees.
- TF-IDF rewards the vocabulary good essays for a prompt tend to use, so an essay could be gamed by stuffing in the right words.
- The coverage guarantee is marginal and assumes new essays resemble the calibration essays; sets 7 and 8 land near 85% on test.
- The review flag's numbers rest on 55 large errors.

**Next steps**

- Tune TF-IDF vocabulary sizes and n-gram ranges per prompt on val.
- Add prompt-relevance checks so off-topic essays are flagged instead of scored.
- Calibrate conformal ranges per score band to even out coverage across sets 7 and 8.
