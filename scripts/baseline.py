"""Step 0: QWK of the shipped model (LSTM + Random Forest) on the fixed test split.

Runs the *unchanged* EssayScorer.predict (RF/LSTM weighting and calibrate_prediction
included). The only substitutions are mechanical:
  * RF / LSTM weights are loaded with grader.legacy_io (sklearn 0.24 pickle, Keras 2 h5),
  * extract_features() returns the cached features (identical code path, computed once
    by scripts/build_style_features.py) instead of recomputing them per call.
predict() returns a 0-10 score; it is mapped back to each set's native scale with the
same per-set ranges EssayScorer.normalize_score uses, then rounded and clipped.

Writes results/baseline.json.
"""
import contextlib
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from grader.data import SETS, clip_round, load_with_splits  # noqa: E402
from grader.legacy_io import legacy_rf_predict, load_legacy_lstm, load_legacy_rf  # noqa: E402
from grader.metrics import mean_qwk, qwk  # noqa: E402
from grader.style import load_style_cache  # noqa: E402

# EssayScorer.normalize_score's ranges (what the shipped model was trained against)
LEGACY_RANGES = {1: (2, 12), 2: (1, 6), 3: (0, 3), 4: (0, 3), 5: (0, 4), 6: (0, 4), 7: (0, 30), 8: (0, 60)}


class _RF:
    def __init__(self, m):
        self.m = m

    def predict(self, X):
        return legacy_rf_predict(self.m, X)


def load_scorer():
    with contextlib.redirect_stdout(io.StringIO()):
        from models.essay_scorer import EssayScorer

        scorer = EssayScorer()
    scorer.rf_model = _RF(load_legacy_rf("saved_models/rf_model.joblib"))
    scorer.lstm_model = load_legacy_lstm("saved_models/final_lstm.h5")
    assert scorer.word2vec_model is not None
    return scorer


def main(split="test"):
    df = load_with_splits()
    df = df[df.split == split].reset_index(drop=True)
    style = load_style_cache().set_index("essay_id")
    feat_cols = list(style.columns)
    scorer = load_scorer()

    current = {}
    scorer.extract_features = lambda essays: style.loc[[current["id"]], feat_cols].reset_index(drop=True)

    preds = []
    for row in df.itertuples():
        current["id"] = row.essay_id
        with contextlib.redirect_stdout(io.StringIO()):
            p10 = scorer.predict(row.essay, row.essay_set)
        lo, hi = LEGACY_RANGES[row.essay_set]
        preds.append(lo + p10 / 10.0 * (hi - lo))
    df["pred"] = preds

    per_set = {}
    for s in SETS:
        d = df[df.essay_set == s]
        per_set[s] = qwk(d.domain1_score, clip_round(d.pred, s))
    first500 = set(pd.read_csv("data/training_set_rel3.tsv", sep="\t", encoding="ISO-8859-1").essay_id.head(500))
    d1 = df[df.essay_set == 1]
    leaked = d1.essay_id.isin(first500)
    out = {
        "model": "shipped LSTM + RF (saved_models/)",
        "split": split,
        "n": int(len(df)),
        "qwk_per_set": {str(k): round(v, 4) for k, v in per_set.items()},
        "qwk_mean": round(mean_qwk(per_set), 4),
        "notes": {
            "rf_training_rows": "first 500 rows of training_set_rel3.tsv (all set 1); "
                                f"{int(leaked.sum())} of {len(d1)} set-1 test essays were in it",
            "set1_qwk_excluding_rf_training_rows": round(
                qwk(d1[~leaked].domain1_score, clip_round(d1[~leaked].pred, 1)), 4),
            "lstm_training_data": "unknown (notebooks/ are empty); may overlap the test split",
        },
    }
    os.makedirs("results", exist_ok=True)
    with open("results/baseline.json", "w") as f:
        json.dump(out, f, indent=2)
    df[["essay_id", "essay_set", "domain1_score", "pred"]].to_csv("results/baseline_test_predictions.csv", index=False)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
