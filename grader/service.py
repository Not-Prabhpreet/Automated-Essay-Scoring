"""Runtime grader: score + 90% range + needs_review + similar essays.

Loads artifacts/grader.joblib (built by scripts/train_grader.py). The same object is
used by the API and by the evaluation, so reported numbers come from the code path that
serves /score. A request featurises the essay once (TF-IDF + style features) and reuses
that for the score, the range width and the similar-essay search.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np

from .conformal import SetConformal, knn_sigma
from .data import ROOT, SCORE_RANGES, clip_round, to_ten
from .features import SetModel
from .neighbors import NeighborIndex
from .review import ReviewRule

ARTIFACT_PATH = os.environ.get("GRADER_ARTIFACT", os.path.join(ROOT, "artifacts", "grader.joblib"))


@dataclass
class GraderArtifact:
    config: dict
    models: Dict[int, SetModel]      # one per prompt set
    conformal: SetConformal
    index: NeighborIndex              # training essays only
    review: ReviewRule
    style_columns: List[str] = field(default_factory=list)


class Grader:
    def __init__(self, artifact: GraderArtifact):
        self.a = artifact

    @classmethod
    def load(cls, path: str = ARTIFACT_PATH) -> "Grader":
        import joblib

        return cls(joblib.load(path))

    def style(self, essay: str) -> np.ndarray:
        from .style import style_features

        return style_features([essay])[self.a.style_columns].to_numpy(dtype=np.float32)

    def grade(self, essay: str, essay_set: int, k: int = 3, style: Optional[np.ndarray] = None,
              exclude_id: Optional[int] = None) -> dict:
        cfg = self.a.config
        model = self.a.models[essay_set]
        if style is None:
            style = self.style(essay)
        text = model.text_matrix([essay])
        raw = float(model.predict(text, style)[0])
        lo_s, hi_s = SCORE_RANGES[essay_set]
        raw_c = float(np.clip(raw, lo_s, hi_s))
        point = int(clip_round([raw], essay_set)[0])

        # 90% conformal range; σ from the spread of the nearest training essays' scores
        sim = model.similarity_vectors(text_matrix=text)
        excl = None if exclude_id is None else [exclude_id]
        nscores = self.a.index.neighbor_scores(essay_set, sim, cfg["conformal_k"], excl)
        sigma = knn_sigma(nscores, essay_set, cfg["conformal_beta"])
        lo, hi = self.a.conformal.predict(essay_set, [raw], sigma)
        width = float(2 * self.a.conformal.half_width(essay_set, 1, sigma)[0])
        needs_review = bool(self.a.review.flags(essay_set, [width])[0])

        return {
            "score": round(float(to_ten(raw_c, essay_set)), 2),
            "raw_score": point,
            "raw_score_continuous": round(raw_c, 3),
            "score_scale": {"min": lo_s, "max": hi_s},
            "range": {"low": int(lo[0]), "high": int(hi[0]), "coverage": 1 - cfg["alpha"],
                      "low_normalized": round(float(to_ten(lo[0], essay_set)), 2),
                      "high_normalized": round(float(to_ten(hi[0], essay_set)), 2)},
            "needs_review": needs_review,
            "review_reasons": ["wide_range"] if needs_review else [],
            "similar_essays": self.a.index.neighbors(essay_set, sim, k=k, exclude_id=exclude_id),
            "model": cfg["model_name"],
        }
