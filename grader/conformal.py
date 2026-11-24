"""Split conformal prediction for integer essay scores, calibrated per prompt set.

Given a fitted point predictor f and a held-out calibration set (never used to train f
or choose its hyper-parameters), for each prompt set s:

  nonconformity  r_i = |y_i - f(x_i)| / sigma(x_i)          (i in calib, set s)
  q_s            = the ceil((n+1)(1-alpha))-th smallest r_i
  range(x)       = [f(x) - q_s * sigma(x), f(x) + q_s * sigma(x)]  -> integers, clipped

If calibration and test essays are exchangeable, P(y in range) >= 1 - alpha for each set
(Vovk et al.; Lei et al. 2018). Because scores are integers we report
[ceil(lower), floor(upper)], which contains exactly the same integers, so the guarantee
carries over.

sigma(x) = 1 gives the plain (constant-width per set) method. The "normalized" variant
uses sigma(x) = beta + spread of the scores of x's k nearest *training* essays, so
essays in a region where similar essays got very different human scores get wider
ranges. sigma only uses the training split, so calibration stays valid.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, Optional

import numpy as np

from .data import SCORE_RANGES


def conformal_quantile(scores: np.ndarray, alpha: float) -> float:
    """Finite-sample split-conformal quantile."""
    scores = np.sort(np.asarray(scores, dtype=float))
    n = len(scores)
    if n == 0:
        raise ValueError("empty calibration set")
    k = math.ceil((n + 1) * (1 - alpha))
    if k > n:  # not enough calibration points for this alpha
        return float("inf")
    return float(scores[k - 1])


def integer_range(pred, half_width, essay_set: int):
    lo_s, hi_s = SCORE_RANGES[essay_set]
    pred = np.asarray(pred, dtype=float)
    hw = np.asarray(half_width, dtype=float)
    eps = 1e-9  # guard against ceil/floor float noise at exact integers
    lo = np.clip(np.ceil(pred - hw - eps), lo_s, hi_s).astype(int)
    hi = np.clip(np.floor(pred + hw + eps), lo_s, hi_s).astype(int)
    # the rounded point prediction must always lie inside its own range
    point = np.clip(np.rint(pred), lo_s, hi_s).astype(int)
    lo = np.minimum(lo, point)
    hi = np.maximum(hi, point)
    return lo, hi


@dataclass
class SetConformal:
    alpha: float
    normalized: bool
    q: Dict[int, float] = field(default_factory=dict)
    n_calib: Dict[int, int] = field(default_factory=dict)

    def fit(self, essay_set: int, y, pred, sigma: Optional[np.ndarray] = None) -> "SetConformal":
        y = np.asarray(y, dtype=float)
        pred = np.asarray(pred, dtype=float)
        s = np.ones_like(pred) if (sigma is None or not self.normalized) else np.asarray(sigma, float)
        self.q[essay_set] = conformal_quantile(np.abs(y - pred) / s, self.alpha)
        self.n_calib[essay_set] = len(y)
        return self

    def half_width(self, essay_set: int, n: int, sigma: Optional[np.ndarray] = None) -> np.ndarray:
        """Continuous half-width q * sigma(x) before rounding to integers. Used to rank
        essays by how wide their range is (integer widths tie heavily on 0-3 scales)."""
        s = np.ones(n) if (sigma is None or not self.normalized) else np.asarray(sigma, float)
        return self.q[essay_set] * s

    def predict(self, essay_set: int, pred, sigma: Optional[np.ndarray] = None):
        pred = np.asarray(pred, dtype=float)
        s = np.ones_like(pred) if (sigma is None or not self.normalized) else np.asarray(sigma, float)
        return integer_range(pred, self.q[essay_set] * s, essay_set)


def coverage(y, lo, hi) -> float:
    y = np.asarray(y)
    return float(np.mean((y >= lo) & (y <= hi)))


def knn_sigma(neighbor_scores: np.ndarray, essay_set: int, beta_frac: float) -> np.ndarray:
    """Difficulty estimate from the k nearest training essays' human scores.

    neighbor_scores: (n, k) array. Spread = std of the neighbours' scores. beta keeps
    sigma > 0 and is expressed as a fraction of the set's score range.
    """
    lo, hi = SCORE_RANGES[essay_set]
    return beta_frac * (hi - lo) + np.std(np.asarray(neighbor_scores, float), axis=1)
