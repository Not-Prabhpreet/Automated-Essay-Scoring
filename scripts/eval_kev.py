"""Step 2 results: how well Kev's rubric answers agree with the human raters.

Reads cached Kev answers (scripts/run_kev.py) and reports, on the test split:
  * sets 7 and 8: QWK per rubric trait vs rater 1 and rater 2, with rater 1 vs rater 2
    as the human ceiling; Kev's expected level is rounded to the nearest rubric level;
  * every set with answers: QWK and Spearman of Kev's composite (domain1) estimate vs
    the resolved human score.
Kev is used zero-shot (no training on ASAP), so no split is used for fitting.

Writes results/step2_kev.json.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

import numpy as np  # noqa: E402
from scipy.stats import spearmanr  # noqa: E402

from grader.data import SETS, clip_round, load_with_splits  # noqa: E402
from grader.kev import KevCache, KevClient, summarize  # noqa: E402
from grader.metrics import qwk  # noqa: E402
from grader.rubrics import TRAIT_COLUMNS, TRAIT_MIN  # noqa: E402


def r3(x):
    return None if x is None or np.isnan(x) else round(float(x), 3)


def main(split="test"):
    df = load_with_splits()
    client = KevClient(cache=KevCache())
    out = {"model": "jaredpalmer/kev-0.8b@v1.0 (zero-shot, CPU, float32)", "split": split,
           "traits": {}, "composite": {}}
    for s in SETS:
        d = df[(df.essay_set == s) & (df.split == split)]
        rows = [(r, client.answers(r.essay, s, offline=True)) for r in d.itertuples()]
        rows = [(r, summarize(s, a)) for r, a in rows if a is not None]
        if not rows:
            continue
        y = np.array([r.domain1_score for r, _ in rows])
        k = np.array([sm["domain1"] for _, sm in rows])
        out["composite"][str(s)] = {
            "n": len(rows), "of": int(len(d)),
            "qwk_vs_resolved": r3(qwk(y, clip_round(k, s))),
            "spearman_vs_resolved": r3(spearmanr(y, k).correlation),
        }
        if s in TRAIT_COLUMNS:
            lo, hi = TRAIT_MIN[s], TRAIT_MIN[s] + (3 if s == 7 else 5)
            traits = {}
            for name, col in TRAIT_COLUMNS[s].items():
                kev = np.array([int(np.clip(round(sm["traits"][name]["score"]), lo, hi)) for _, sm in rows])
                r1 = np.array([int(getattr(r, f"rater1_trait{col}")) for r, _ in rows])
                r2 = np.array([int(getattr(r, f"rater2_trait{col}")) for r, _ in rows])
                traits[name] = {
                    "qwk_kev_vs_rater1": r3(qwk(r1, kev, lo, hi)),
                    "qwk_kev_vs_rater2": r3(qwk(r2, kev, lo, hi)),
                    "qwk_rater1_vs_rater2": r3(qwk(r1, r2, lo, hi)),
                    "kev_mean": r3(kev.mean()), "human_mean": r3(r1.mean()),
                    "kev_mean_confidence": r3(np.mean([sm["traits"][name]["confidence"] for _, sm in rows])),
                }
            out["traits"][str(s)] = {"n": len(rows), "scale": [lo, hi], "per_trait": traits}
    os.makedirs("results", exist_ok=True)
    with open("results/step2_kev.json", "w") as f:
        json.dump(out, f, indent=2)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
