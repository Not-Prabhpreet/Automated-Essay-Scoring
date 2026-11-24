"""Runtime grader: score + 90% range + Kev trait feedback + needs_review + evidence.

Loads artifacts/grader.joblib (built by scripts/train_grader.py). The same object is
used by the API and by the evaluation, so reported numbers come from the code path
that serves /score.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np

from .conformal import SetConformal, knn_sigma
from .data import ROOT, SCORE_RANGES, clip_round, to_ten
from .neighbors import NeighborIndex
from .review import PercentileScale, ReviewRule

ARTIFACT_PATH = os.environ.get("GRADER_ARTIFACT", os.path.join(ROOT, "artifacts", "grader.joblib"))


def rank_disagreement(pred_scale: PercentileScale, kev_scale: PercentileScale, essay_set: int,
                      pred, kev) -> np.ndarray:
    """|percentile(model score) - percentile(Kev score)| within the set (val CDFs).

    Rank-based, so a constant Kev bias (e.g. zero-shot Kev scoring everyone a bit high)
    does not count as disagreement; only ordering differences do.
    """
    return np.abs(pred_scale.transform(essay_set, pred) - kev_scale.transform(essay_set, kev))


@dataclass
class GraderArtifact:
    config: dict
    heads: dict                      # set -> SetHead
    conformal: SetConformal
    index: NeighborIndex
    rule_with_kev: ReviewRule
    rule_without_kev: ReviewRule
    pred_scale: PercentileScale      # val CDF of model predictions per set
    kev_scale: PercentileScale       # val CDF of Kev domain1 estimates per set
    style_columns: List[str] = field(default_factory=list)


class Grader:
    def __init__(self, artifact: GraderArtifact, embedder=None, kev_client=None):
        self.a = artifact
        self._embedder = embedder
        self.kev = kev_client

    @classmethod
    def load(cls, path: str = ARTIFACT_PATH, embedder=None, kev_client=None) -> "Grader":
        import joblib

        return cls(joblib.load(path), embedder=embedder, kev_client=kev_client)

    @property
    def embedder(self):
        if self._embedder is None:
            from .embeddings import get_embedder

            self._embedder = get_embedder(self.a.config["embedding_backend"])
        return self._embedder

    # -- pieces -----------------------------------------------------------------------
    def _style(self, essay: str) -> Optional[np.ndarray]:
        if not self.a.config["use_style"]:
            return None
        from .style import style_features

        return style_features([essay])[self.a.style_columns].to_numpy(dtype=np.float32)

    def _kev(self, essay: str, essay_set: int) -> Optional[dict]:
        if self.kev is None:
            return None
        from .kev import summarize

        try:
            ans = self.kev.answers(essay, essay_set)
        except Exception:
            return None
        return None if ans is None else summarize(essay_set, ans)

    # -- main entry point ---------------------------------------------------------------
    def grade(self, essay: str, essay_set: int, k: int = 3, emb: Optional[np.ndarray] = None,
              style: Optional[np.ndarray] = None, kev: Optional[dict] = "auto",
              exclude_id: Optional[int] = None) -> dict:
        cfg = self.a.config
        if emb is None:
            emb = self.embedder.embed([essay])
        emb = np.atleast_2d(emb)
        if style is None and cfg["use_style"]:
            style = self._style(essay)
        raw = float(self.a.heads[essay_set].predict(emb, style)[0])
        lo_s, hi_s = SCORE_RANGES[essay_set]
        raw_c = float(np.clip(raw, lo_s, hi_s))
        point = int(clip_round([raw], essay_set)[0])

        # conformal range
        excl = None if exclude_id is None else [exclude_id]
        nscores = self.a.index.neighbor_scores(essay_set, emb, cfg["conformal_k"], excl)
        sigma = knn_sigma(nscores, essay_set, cfg["conformal_beta"])
        lo, hi = self.a.conformal.predict(essay_set, [raw], sigma)
        lo, hi = int(lo[0]), int(hi[0])
        width = float(2 * self.a.conformal.half_width(essay_set, 1, sigma)[0])  # continuous

        # Kev rubric feedback
        if isinstance(kev, str) and kev == "auto":
            kev = self._kev(essay, essay_set)
        reasons = []
        if kev is not None:
            dis = rank_disagreement(self.a.pred_scale, self.a.kev_scale, essay_set, [raw], [kev["domain1"]])
            w_flag, k_flag = self.a.rule_with_kev.flags(essay_set, [width], dis)
        else:
            w_flag, k_flag = self.a.rule_without_kev.flags(essay_set, [width], None)
        if w_flag[0]:
            reasons.append("wide_range")
        if k_flag[0]:
            reasons.append("kev_disagrees")

        similar = self.a.index.neighbors(essay_set, emb, k=k, exclude_id=exclude_id)
        return {
            "score": round(float(to_ten(raw_c, essay_set)), 2),
            "raw_score": point,
            "raw_score_continuous": round(raw_c, 3),
            "score_scale": {"min": lo_s, "max": hi_s},
            "range": {"low": lo, "high": hi, "coverage": 1 - cfg["alpha"],
                      "low_normalized": round(float(to_ten(lo, essay_set)), 2),
                      "high_normalized": round(float(to_ten(hi, essay_set)), 2)},
            "trait_scores": None if kev is None or not kev["traits"] else {
                name: {"score": t["score"], "confidence": t["confidence"]} for name, t in kev["traits"].items()
            },
            "kev_score": None if kev is None else {"score": round(float(kev["domain1"]), 2),
                                                   "confidence": round(float(kev["confidence"]), 3)},
            "needs_review": bool(reasons),
            "review_reasons": reasons,
            "similar_essays": similar,
            "model": cfg["model_name"],
        }
