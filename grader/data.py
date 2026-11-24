"""ASAP data loading, score ranges and the fixed, seeded train/val/calib/test split.

Every experiment reads the split from data/splits.csv so all models are compared on
exactly the same essays. The split is per prompt set (each set is its own task with
its own score scale) and is created once with SEED; `make_splits` is deterministic,
and tests check that re-creating it reproduces the committed file.
"""
from __future__ import annotations

import os
from typing import Dict, Tuple

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(ROOT, "data", "training_set_rel3.tsv")
SPLITS_PATH = os.path.join(ROOT, "data", "splits.csv")

SEED = 42
SETS = tuple(range(1, 9))
# Fractions per prompt set. calib is used only by split conformal prediction;
# val is used for every model-selection / threshold choice; test is read for reporting.
SPLIT_FRACTIONS = (("train", 0.60), ("val", 0.10), ("calib", 0.15), ("test", 0.15))

# Resolved (domain1) score range per set, as observed in ASAP and documented in the
# set descriptions. Set 7 is documented as 0-30 but resolved scores span 0-24
# (2 raters x 0-12, see rubrics.to_domain1); the data's max is 24.
SCORE_RANGES: Dict[int, Tuple[int, int]] = {
    1: (2, 12),
    2: (1, 6),
    3: (0, 3),
    4: (0, 3),
    5: (0, 4),
    6: (0, 4),
    7: (0, 24),
    8: (0, 60),
}


def load_asap(path: str = DATA_PATH) -> pd.DataFrame:
    df = pd.read_csv(path, sep="\t", encoding="ISO-8859-1")
    df = df.dropna(subset=["essay", "domain1_score"])
    df["domain1_score"] = df["domain1_score"].astype(int)
    return df.reset_index(drop=True)


def make_splits(df: pd.DataFrame, seed: int = SEED) -> pd.DataFrame:
    """Deterministic per-set random split. Returns DataFrame[essay_id, essay_set, split]."""
    rows = []
    rng = np.random.default_rng(seed)
    for s in SETS:
        ids = np.sort(df.loc[df.essay_set == s, "essay_id"].to_numpy())
        ids = ids[rng.permutation(len(ids))]
        n = len(ids)
        start = 0
        for i, (name, frac) in enumerate(SPLIT_FRACTIONS):
            end = n if i == len(SPLIT_FRACTIONS) - 1 else start + int(round(frac * n))
            rows += [(int(e), s, name) for e in ids[start:end]]
            start = end
    return pd.DataFrame(rows, columns=["essay_id", "essay_set", "split"])


def load_splits(df: pd.DataFrame | None = None, path: str = SPLITS_PATH) -> pd.DataFrame:
    """Load the committed split, creating it on first use."""
    if not os.path.exists(path):
        if df is None:
            df = load_asap()
        make_splits(df).to_csv(path, index=False)
    return pd.read_csv(path)


def load_with_splits() -> pd.DataFrame:
    df = load_asap()
    splits = load_splits(df)
    out = df.merge(splits[["essay_id", "split"]], on="essay_id", how="inner", validate="one_to_one")
    assert len(out) == len(df), "every essay must have a split"
    return out


def clip_round(pred, essay_set: int) -> np.ndarray:
    lo, hi = SCORE_RANGES[essay_set]
    return np.clip(np.rint(np.asarray(pred, dtype=float)), lo, hi).astype(int)


def to_unit(score, essay_set: int) -> np.ndarray:
    """Map a native-scale score to [0, 1] (used for cross-set comparisons/thresholds)."""
    lo, hi = SCORE_RANGES[essay_set]
    return (np.asarray(score, dtype=float) - lo) / (hi - lo)


def to_ten(score, essay_set: int) -> np.ndarray:
    """Native score -> the API's legacy 0-10 scale."""
    return np.clip(10.0 * to_unit(score, essay_set), 0.0, 10.0)
