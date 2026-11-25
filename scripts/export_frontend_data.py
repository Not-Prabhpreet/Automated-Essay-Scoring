"""Export result numbers and sample essays for the website (frontend/src/data/).

Every number shown on the site comes from results/*.json through this script, so the
site can't drift from the evaluation. Sample essays are real ASAP *test-split* essays
(one per prompt, typical score and length) used by the "Try a sample" button.

Usage: python scripts/export_frontend_data.py
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from grader.data import SCORE_RANGES, SETS, load_with_splits  # noqa: E402

OUT = os.path.join("frontend", "src", "data")


def fix_cp1252(text):
    """ASAP is Windows-1252 read as Latin-1; restore curly quotes and dashes."""
    return "".join(c.encode("latin-1").decode("cp1252", errors="ignore") if 0x80 <= ord(c) <= 0x9F else c for c in text)


def load(name):
    with open(os.path.join("results", name)) as f:
        return json.load(f)


def main():
    os.makedirs(OUT, exist_ok=True)
    base, model = load("baseline.json"), load("step1_model.json")
    conf, review, speed = load("step3_conformal.json"), load("step3_review.json"), load("speed.json")
    df = load_with_splits()
    split_sizes = df.split.value_counts().to_dict()
    at20 = review["budgets"]["0.2"]

    results = {
        "dataset": {"essays": int(len(df)), "sets": len(SETS), "splits": {k: int(v) for k, v in split_sizes.items()}},
        "qwk": {
            "sets": [str(s) for s in SETS],
            "baseline": {"label": "Original LSTM + Random Forest", "mean": base["qwk_mean"],
                         "perSet": base["qwk_per_set"]},
            "deployed": {"label": "TF-IDF + style features (ridge)", "mean": model["test_mean"],
                         "perSet": model["test_per_set"]},
            "ablations": model["ablations_test_mean"],
            "alphas": model["alpha_per_set"],
        },
        "conformal": {
            "target": conf["target_coverage"], "coverage": conf["test_coverage_overall"],
            "widthFrac": conf["test_mean_width_frac_of_range"], "k": conf["k"], "beta": conf["beta"],
            "plain": conf["plain_for_comparison"],
            "perSet": {s: {"coverage": v["coverage"], "width": v["mean_width_points"],
                           "range": v["score_range"], "nCalib": v["n_calib"], "nTest": v["n_test"]}
                       for s, v in conf["per_set"].items()},
        },
        "review": {
            "largeErrorRate": review["test_large_error_rate"],
            "largeErrors": review["test_large_errors"],
            "budgets": {b: {"flagged": v["test"]["flagged_pct"], "caught": v["test"]["large_errors_caught_pct"]}
                        for b, v in review["budgets"].items()},
            "at20": {"flagged": at20["test"]["flagged_pct"], "caught": at20["test"]["large_errors_caught_pct"]},
        },
        "speed": {"inProcessMedianMs": speed["median_ms"], "inProcessP90Ms": speed["p90_ms"]},
    }
    with open(os.path.join(OUT, "results.json"), "w") as f:
        json.dump(results, f, indent=1)

    samples = {}
    te = df[df.split == "test"].copy()
    te["words"] = te.essay.str.split().str.len()
    for s in SETS:
        d = te[te.essay_set == s]
        lo, hi = SCORE_RANGES[s]
        mid = d.domain1_score.median()
        cap = 700 if s == 8 else 260
        cand = d[(d.words >= 60) & (d.words <= cap)]
        cand = cand.iloc[(cand.domain1_score - mid).abs().argsort(kind="stable")]
        row = cand.iloc[0]
        samples[str(s)] = {"essay_id": int(row.essay_id), "human_score": int(row.domain1_score),
                           "essay": fix_cp1252(" ".join(row.essay.split()))}
    with open(os.path.join(OUT, "samples.json"), "w") as f:
        json.dump(samples, f, indent=1)
    print("wrote", os.path.join(OUT, "results.json"), "and samples.json")


if __name__ == "__main__":
    main()
