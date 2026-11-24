import React from 'react';
import { Link } from 'react-router-dom';
import R from '../data/results.json';
import KEV_EXAMPLE from '../data/kev_example.json';
import { PROMPTS } from '../data/prompts';
import { AgreementPlot, QwkChart } from '../components/Charts';
import { ConformalDiagram, KevDiagram, PipelineDiagram, SplitDiagram, WindowDiagram } from '../components/Diagrams';
import { REPO_URL } from '../components/Layout';

const p1 = (x) => `${(x * 100).toFixed(1)}%`;
const f3 = (x) => Number(x).toFixed(3);

const SECTIONS = [
  ['overview', 'Overview'], ['data', 'The data'], ['embeddings', 'Embeddings'], ['scoring', 'Scoring heads'],
  ['results', 'Results'], ['ranges', 'Score ranges'], ['evidence', 'Similar essays'], ['review', 'Review flag'],
  ['kev', 'Kev'], ['engineering', 'Making it fast'], ['limits', 'Limits'],
];

function Section({ id, eyebrow, title, children }) {
  return (
    <section id={id} className="scroll-mt-24 border-t border-rule pt-12 first:border-t-0 first:pt-0">
      {eyebrow && <p className="eyebrow">{eyebrow}</p>}
      <h2 className="mt-2 text-3xl font-semibold">{title}</h2>
      <div className="prose-body mt-5 max-w-prose">{children}</div>
    </section>
  );
}

function Table({ head, rows, caption }) {
  return (
    <figure className="my-6 max-w-none">
      <div className="overflow-x-auto rounded-xl border border-rule bg-surface">
        <table className="w-full text-sm num">
          <thead><tr className="border-b border-rule bg-sunk/60 text-left text-muted">
            {head.map((h) => <th key={h} className="px-4 py-2.5 font-medium">{h}</th>)}
          </tr></thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={i} className="border-b border-rule/60 last:border-0">
                {r.map((c, j) => <td key={j} className={`px-4 py-2 ${j === 0 ? 'text-ink' : 'text-ink2'}`}>{c}</td>)}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {caption && <figcaption className="mt-2 text-sm text-muted">{caption}</figcaption>}
    </figure>
  );
}

export default function HowItWorks() {
  const kevTraits = Object.entries(R.kev.traits).map(([set, t]) => ({ set, per: t.per_trait }));
  const v = R.qwk.variants;
  const at20 = R.review.at20;
  return (
    <div className="container-page py-10 sm:py-14">
      <header className="max-w-prose">
        <p className="eyebrow">How it works</p>
        <h1 className="mt-2 text-4xl font-semibold sm:text-[48px] sm:leading-[1.08]">The models, the data, and how far to trust them</h1>
        <p className="mt-4 text-lg text-ink2">
          Every number on this page comes from the evaluation scripts in the{' '}
          <a className="link" href={REPO_URL} target="_blank" rel="noreferrer">repository</a> and is measured on essays the
          models never saw.
        </p>
      </header>

      <div className="mt-12 grid gap-12 lg:grid-cols-[200px_1fr]">
        <nav className="hidden lg:block" aria-label="On this page">
          <ul className="sticky top-24 space-y-1 border-l border-rule text-sm">
            {SECTIONS.map(([id, label]) => (
              <li key={id}><a href={`#${id}`} className="-ml-px block border-l border-transparent py-1 pl-4 text-ink2 hover:border-accent hover:text-ink">{label}</a></li>
            ))}
          </ul>
        </nav>

        <div className="min-w-0 space-y-14">
          <Section id="overview" eyebrow="1" title="Overview">
            <p>
              The grader turns an essay into numbers two ways. A sentence-embedding model reads the whole text and outputs
              384 numbers that capture what it says and how. A small set of hand-written style features counts things like
              length, spelling mistakes and vocabulary. A separate regression model for each prompt maps those numbers to a
              score on that prompt’s scale.
            </p>
            <p>
              Around that score sit three things a single number can’t tell you: how wide the plausible range is, which
              human-graded essays it resembles, and whether a teacher should check it.
            </p>
          </Section>
          <PipelineDiagram />

          <Section id="data" eyebrow="2" title="The data">
            <p>
              The <a className="link" href="https://www.kaggle.com/c/asap-aes" target="_blank" rel="noreferrer">Automated Student
              Assessment Prize</a> (ASAP) dataset has {R.dataset.essays.toLocaleString()} essays written by students in grades 7
              to 10 for eight prompts, each scored by trained human raters. Four prompts are argument or story essays; four ask
              students to respond to a short text they had just read. Each prompt has its own rubric and scale, from 0–3 up to 0–60.
            </p>
            <p>
              The essays are split once, per prompt, with a fixed random seed. The split is committed to the repository, so
              every model is compared on exactly the same test essays.
            </p>
          </Section>
          <SplitDiagram splits={R.dataset.splits} />
          <Table head={['Set', 'Prompt', 'Type', 'Grade', 'Score scale']}
            rows={PROMPTS.map((p) => [p.id, p.title, p.kind, p.grade, `${p.scale[0]}–${p.scale[1]}`])} />

          <Section id="embeddings" eyebrow="3" title="Embeddings">
            <p>
              An embedding model reads a piece of text and returns a fixed-length list of numbers, a vector, so that texts
              with similar meaning end up close together. Two essays that make the same argument with similar
              detail get similar vectors, even if they share few exact words.
            </p>
            <p>
              The grader uses <code>BAAI/bge-small-en-v1.5</code>, an open-source model with 33 million parameters that outputs
              384 numbers. It runs on a CPU, which keeps the server small and cheap. Essays are embedded once and cached, so
              re-training never re-reads them. (The code can also use OpenAI’s <code>text-embedding-3-small</code> with one
              setting.)
            </p>
            <p>
              The model reads at most 512 tokens at a time and the longest essays run past 1,000 words, so long essays are cut
              into overlapping windows that are embedded separately and averaged:
            </p>
          </Section>
          <WindowDiagram />
          <div className="prose-body max-w-prose">
            <p>
              “Close together” is measured with cosine similarity: the cosine of the angle between two vectors, 1 when they
              point the same way. The same vectors power the similar-essay evidence and the range width below.
            </p>
          </div>

          <Section id="scoring" eyebrow="4" title="Scoring heads">
            <p>
              Each prompt gets its own small model, a <em>head</em>, trained only on that prompt’s training essays. Its input is the
              384-number embedding plus the 20 style features (rescaled to comparable units). The head is a ridge regression:
              a weighted sum of the inputs with a penalty that keeps weights small, so it doesn’t memorise ~1,000 training
              essays. The penalty strength is chosen per prompt on the validation essays.
            </p>
            <p>
              I also tried a small neural network (one hidden layer) and leaving the style features out. All choices were made
              on validation essays only:
            </p>
          </Section>
          <Table head={['Variant', 'Mean QWK (test)']}
            caption="Mean QWK across the eight prompts on the test essays. The deployed variant is the one with the best validation score."
            rows={[
              ['Original model (LSTM + Random Forest)', f3(R.qwk.baseline.mean)],
              ['Style features only, Random Forest per prompt', f3(v['style-only RF (retrained per set)'])],
              ['Embeddings, ridge', f3(v.ridge)],
              ['Embeddings, small neural net', f3(v.mlp)],
              ['Embeddings + style, small neural net', f3(v['mlp+style'])],
              ['Embeddings + style, ridge (deployed)', f3(v['ridge+style'])],
            ]} />
          <div className="prose-body max-w-prose">
            <p>
              The style features matter: on their own they already beat the original model, and adding them to the
              embeddings lifts the mean from {f3(v.ridge)} to {f3(v['ridge+style'])}. The embedding catches content and
              argument; the features catch surface quality, such as spelling, that an embedding barely notices.
            </p>
          </div>

          <Section id="results" eyebrow="5" title="Results per prompt">
            <p>
              Agreement is measured with quadratic weighted kappa (QWK), the ASAP competition metric. It is 1 for perfect
              agreement with the human score and 0 for chance, and it penalises a miss of two points four times as much as a
              miss of one.
            </p>
          </Section>
          <QwkChart qwk={R.qwk} />
          <div className="prose-body max-w-prose">
            <p>
              The new grader is better on seven of eight prompts; on set 1 the two are close (the original model was partly
              trained on set 1’s test essays, which flatters it there). The biggest gains are on the short reading responses (sets
              3 and 4) and the narrative prompt (set 7), where the original model was weakest.
            </p>
          </div>

          <Section id="ranges" eyebrow="6" title="Score ranges (conformal prediction)">
            <p>
              A single predicted score hides how sure the model is. The grader also returns a range built with{' '}
              <em>split conformal prediction</em>, a method that makes few assumptions: if a new essay is like the essays
              set aside for calibration, its human score falls inside the range at least 90% of the time.
            </p>
            <p>
              It works by looking at the model’s errors on {Object.values(R.conformal.perSet).reduce((a, s) => a + s.nCalib, 0).toLocaleString()} calibration
              essays the model never trained on. Each error is divided by a difficulty estimate σ: how much the human scores of
              the essay’s 25 nearest training essays disagree with each other. q is the size of error that 90% of calibration
              essays stay under, and a new essay gets <code>score ± q·σ</code>. Essays that look like essays humans scored very differently
              get wider ranges.
            </p>
          </Section>
          <ConformalDiagram />
          <Table head={['Set', 'Scale', 'Coverage (target 90%)', 'Average width', 'Calibration essays']}
            caption={`Test essays inside their range: ${p1(R.conformal.coverage)} overall, with ranges averaging ${p1(R.conformal.widthFrac)} of the score scale. The simpler fixed-width version covers ${p1(R.conformal.plain.test_coverage_overall)} at ${p1(R.conformal.plain.test_mean_width_frac_of_range)}, but gives every essay of a prompt the same width.`}
            rows={Object.entries(R.conformal.perSet).map(([s, c]) => [s, `${c.range[0]}–${c.range[1]}`, p1(c.coverage), `${c.width.toFixed(1)} points`, c.nCalib])} />

          <Section id="evidence" eyebrow="7" title="Similar essays as evidence">
            <p>
              For every essay the grader returns the three training essays for the same prompt with the most similar
              embeddings, and the score humans gave them. If your essay scored 3 and its closest neighbours scored 2, 3 and 3,
              the score is easy to believe. If they scored 1, 4 and 2, be careful.
            </p>
            <p>
              The search only covers the training essays, so a test essay can never retrieve itself or its own score. Tests in the
              repository check this, along with the rule that each essay sits in exactly one split.
            </p>
          </Section>

          <Section id="review" eyebrow="8" title="The review flag">
            <p>
              <code>needs_review</code> is set when the range is unusually wide for that prompt, or when Kev (next section) disagrees
              with the score. The cut-offs are chosen on validation essays to catch as many large errors as possible while
              flagging at most about 20% of essays. A large error is a miss of at least 2 points and at least a fifth of the scale.
            </p>
            <p>
              Large errors are rare: {R.review.largeErrors} of {R.dataset.splits.test.toLocaleString()} test essays ({p1(R.review.largeErrorRate)}).
              Range width alone is a weak signal. Kev’s disagreement is a much better one, even though Kev on its own scores
              poorly. Kev answers were available for {p1(R.review.kevCoverage)} of test essays, and with this few large errors these rates
              are noisy.
            </p>
          </Section>
          <Table head={['Rule', 'Essays flagged', 'Large errors caught']}
            caption="Test essays, cut-offs chosen on validation. The live server uses the width-only rule because Kev is off there."
            rows={[
              ['Range is wide', p1(at20.width_only.flagged), p1(at20.width_only.caught)],
              ['Kev disagrees', p1(at20.kev_only.flagged), p1(at20.kev_only.caught)],
              ['Range is wide or Kev disagrees', p1(at20.width_or_kev.flagged), p1(at20.width_or_kev.caught)],
            ]} />

          <Section id="kev" eyebrow="9" title="Kev: rubric-trait feedback">
            <p>
              <a className="link" href="https://github.com/jaredpalmer/kev" target="_blank" rel="noreferrer">Kev</a> is an open
              family of small <em>decision models</em>. Instead of writing text, it reads a document (the <em>state</em>) and answers
              typed questions about it by putting a probability on each answer it is offered. I used Kev-0.8B: a small LoRA adapter and a
              “pointer head” on the open Qwen3.5-0.8B base model. The head scores each answer option against the question and a
              softmax turns the scores into probabilities, with a temperature fitted so the probabilities are calibrated.
            </p>
            <p>
              For each essay I ask one <code>score</code> question per rubric trait, using the rubric’s own wording, ordered from lowest to
              highest. Set 7 asks about Ideas, Organization, Style and Conventions (0–3). Set 8 asks about six traits (1–6), and
              the other prompts ask about their single holistic rubric. Kev returns a probability for every level, the expected level,
              and a confidence. The essay is read once and cached, and the questions can’t see each other. The trait answers are
              combined with each prompt’s official scoring rule into an overall estimate, and that is compared with the grader’s
              score to produce the “Kev disagrees” signal.
            </p>
          </Section>
          <KevDiagram example={KEV_EXAMPLE} />
          <div className="prose-body max-w-prose">
            <p>
              Used zero-shot (never trained on these essays), Kev-0.8B agrees with human raters far less than they agree with
              each other. Set 7 is close to chance; set 8 is better but still well short of the human raters:
            </p>
          </div>
          <AgreementPlot traits={kevTraits} />
          <div className="prose-body max-w-prose">
            <p>
              Its probabilities are spread across most levels (average confidence 0.04–0.27), so it tends to answer “middle of the
              scale” for everyone. That matches its model card, which says the 0.8B is markedly less accurate on tasks unlike its
              training data. Even so, where its ranking differs sharply from the grader’s, the grader is more often wrong, which
              is why it helps the review flag.
            </p>
            <p>
              <strong className="text-ink">Why it’s off on the live server.</strong> Kev-0.8B needs about 4 GB of memory and 2–14 seconds
              per essay on a CPU, against roughly 450 MB and 1 second for everything else. The live API supports it through one
              setting (<code>KEV_URL</code>) and returns trait scores when it is on. The next steps are fine-tuning Kev on the ASAP
              trait labels (Kev supports this from a released checkpoint) and serving it on a GPU that scales to zero, so it
              only costs money while grading.
            </p>
          </div>

          <Section id="engineering" eyebrow="10" title="Making it fast enough to host cheaply">
            <p>The first version took several seconds per essay and needed more memory than a small server has. Four fixes:</p>
          </Section>
          <Table head={['Change', 'Before', 'After']} rows={[
            ['Spelling feature: dictionary lookup first, TextBlob’s slow edit-distance search only for unknown words (same answers, tested on 3,000 essays)', '~2 s per essay', '~50 ms'],
            ['Stop loading TensorFlow (only the retired model needed it)', '847 MB memory', '229 MB'],
            ['Match PyTorch threads to the server’s single CPU and score on one worker thread', 'minutes under load', '~1 s median'],
            ['Bake the embedding model into the Docker image', 'download at start-up', 'starts offline'],
          ]} />

          <Section id="limits" eyebrow="11" title="Limits">
            <p>
              The grader only knows these eight prompts and the way 2012 raters scored grade 7–10 students. Scores for essays on
              other topics are meaningless, and the reading-response prompts assume the student read a text the model never sees.
              A mean QWK of 0.75 is strong agreement, but individual scores still miss. The range and the flag exist so you
              don’t have to take any one number on trust.
            </p>
            <p>
              <Link to="/grade" className="link">Try it on a real test essay</Link>, or read the{' '}
              <a className="link" href={REPO_URL} target="_blank" rel="noreferrer">code and evaluation scripts</a>.
            </p>
          </Section>
        </div>
      </div>
    </div>
  );
}
