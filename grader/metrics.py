"""Quadratic weighted kappa (the ASAP competition metric)."""
from __future__ import annotations

from typing import Optional

import numpy as np


def qwk(y_true, y_pred, min_rating: Optional[int] = None, max_rating: Optional[int] = None) -> float:
    """Cohen's kappa with quadratic weights over integer ratings.

    Matches sklearn.metrics.cohen_kappa_score(weights="quadratic") when the rating
    range is the union of observed labels; passing min/max fixes the range explicitly.
    """
    a = np.asarray(y_true, dtype=int)
    b = np.asarray(y_pred, dtype=int)
    if a.shape != b.shape:
        raise ValueError("y_true and y_pred must have the same shape")
    if a.size == 0:
        raise ValueError("empty input")
    lo = int(min(a.min(), b.min())) if min_rating is None else int(min_rating)
    hi = int(max(a.max(), b.max())) if max_rating is None else int(max_rating)
    k = hi - lo + 1
    if k == 1:
        return 1.0
    O = np.zeros((k, k), dtype=float)
    np.add.at(O, (a - lo, b - lo), 1.0)
    W = np.subtract.outer(np.arange(k), np.arange(k)) ** 2 / (k - 1) ** 2
    E = np.outer(O.sum(axis=1), O.sum(axis=0)) / O.sum()
    denom = (W * E).sum()
    if denom == 0:
        return 1.0
    return float(1.0 - (W * O).sum() / denom)


def mean_qwk(per_set: dict) -> float:
    """Unweighted mean over prompt sets (the usual ASAP summary)."""
    return float(np.mean(list(per_set.values())))
