"""needs_review: flag essays whose 90% score range is unusually wide.

The signal is the essay's continuous range width (2·q·σ, before rounding). It is put on a
per-prompt percentile scale using the *validation* essays, so one cut-off works across
prompts with very different score scales:

  needs_review = width percentile (within the prompt) >= t_width

t_width is chosen on validation to catch as many large errors as possible while flagging
at most `budget` of essays. A "large error" is |round(prediction) - human| >=
max(2, 0.2 * score range): at least two points, and at least a fifth of the scale on the
wide-scale sets (set 7: >= 5, set 8: >= 12).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

import numpy as np

from .data import SCORE_RANGES

GRID = tuple(np.round(np.arange(0.50, 1.0001, 0.01), 2))  # percentile cut-offs; 1.0 = never


def large_error_threshold(essay_set: int) -> float:
    lo, hi = SCORE_RANGES[essay_set]
    return max(2.0, 0.2 * (hi - lo))


def is_large_error(y, pred_int, essay_set: int) -> np.ndarray:
    return np.abs(np.asarray(pred_int) - np.asarray(y)) >= large_error_threshold(essay_set)


@dataclass
class PercentileScale:
    """Empirical CDF of a signal per set, fitted on validation."""
    ref: Dict[int, np.ndarray] = field(default_factory=dict)

    def fit(self, essay_set: int, values) -> "PercentileScale":
        self.ref[essay_set] = np.sort(np.asarray(values, dtype=float))
        return self

    def transform(self, essay_set: int, values) -> np.ndarray:
        ref = self.ref[essay_set]
        v = np.asarray(values, dtype=float)
        # fraction of validation essays with a strictly smaller value
        return np.searchsorted(ref, v, side="left") / len(ref)


@dataclass
class ReviewRule:
    t_width: float = 1.0
    width_scale: PercentileScale = field(default_factory=PercentileScale)

    def flags(self, essay_set: int, width) -> np.ndarray:
        if self.t_width >= 1.0:
            return np.zeros(np.shape(width), dtype=bool)
        return self.width_scale.transform(essay_set, width) >= self.t_width


def flag_stats(flag: np.ndarray, large: np.ndarray) -> dict:
    flag = np.asarray(flag, bool)
    large = np.asarray(large, bool)
    return {
        "flagged_pct": float(flag.mean()),
        "large_errors": int(large.sum()),
        "large_errors_caught_pct": float(flag[large].mean()) if large.any() else float("nan"),
        "error_rate_unflagged": float(large[~flag].mean()) if (~flag).any() else float("nan"),
        "error_rate_flagged": float(large[flag].mean()) if flag.any() else float("nan"),
    }


def choose_threshold(width_pct: np.ndarray, large: np.ndarray, budget: float) -> float:
    """Grid search on validation: maximise large errors caught s.t. flagged <= budget.
    Ties go to fewer flags."""
    best = None
    for tw in GRID:
        f = width_pct >= tw if tw < 1.0 else np.zeros_like(large, bool)
        rate = f.mean()
        if rate > budget + 1e-9:
            continue
        caught = f[large].mean() if large.any() else 0.0
        key = (caught, -rate)
        if best is None or key > best[0]:
            best = (key, float(tw))
    return 1.0 if best is None else best[1]
