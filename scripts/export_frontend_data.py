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
    base, heads = load("baseline.json"), load("step1_heads.json")
    conf, review, kev = load("step3_conformal.json"), load("step3_review.json"), load("step2_kev.json")
    dep = heads["deployed"]
    df = load_with_splits()
    split_sizes = df.split.value_counts().to_dict()

    results = {
        "dataset": {"essays": int(len(df)), "sets": len(SETS), "splits": {k: int(v) for k, v in split_sizes.items()}},
        "qwk": {
            "sets": [str(s) for s in SETS],
            "baseline": {"label": "Original LSTM + Random Forest", "mean": base["qwk_mean"],
                         "perSet": base["qwk_per_set"]},
            "deployed": {"label": "Embeddings + style features (ridge)", "mean": heads["variants"][dep]["test_mean"],
                         "perSet": heads["variants"][dep]["test_per_set"]},
            "variants": {k: v["test_mean"] for k, v in heads["variants"].items()},
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
            "largeErrors": review["budgets"]["0.2"]["width_only"]["test"]["large_errors"],
            "kevCoverage": review["kev_answers_available"]["test"],
            "at20": {k: {"flagged": v["test"]["flagged_pct"], "caught": v["test"]["large_errors_caught_pct"]}
                     for k, v in review["budgets"]["0.2"].items()},
        },
        "kev": kev,
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
