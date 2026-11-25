"""Nearest scored training essays (cosine similarity over TF-IDF vectors).

The index only ever contains the *train* split, so an essay from val/calib/test can
never retrieve itself or its own score. For essays that are in the index (training
essays), `query(..., exclude_ids=...)` drops the essay's own id; tests check both.
Vectors are L2-normalised (dense or scipy sparse), so cosine similarity is a dot product.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

import numpy as np
import scipy.sparse as sp
from sklearn.preprocessing import normalize


@dataclass
class SetIndex:
    ids: np.ndarray        # essay_id per row
    scores: np.ndarray     # resolved human score per row
    vecs: object           # (n, d) rows L2-normalised; ndarray or csr_matrix
    excerpts: List[str]


class NeighborIndex:
    def __init__(self):
        self.sets: Dict[int, SetIndex] = {}

    def add_set(self, essay_set: int, ids, scores, vecs, essays: Sequence[str], excerpt_chars: int = 280):
        vecs = sp.csr_matrix(vecs, dtype=np.float32) if sp.issparse(vecs) else np.asarray(vecs, dtype=np.float32)
        vecs = normalize(vecs)
        self.sets[essay_set] = SetIndex(
            ids=np.asarray(ids, dtype=int),
            scores=np.asarray(scores, dtype=int),
            vecs=vecs,
            excerpts=[_excerpt(e, excerpt_chars) for e in essays],
        )
        return self

    def query(self, essay_set: int, q: np.ndarray, k: int = 3,
              exclude_ids: Optional[Sequence[int]] = None):
        """Return (idx, sims) arrays of shape (n_queries, k), most similar first.

        exclude_ids[i] (if given) is removed from query i's results.
        """
        idx = self.sets[essay_set]
        if sp.issparse(q):
            q = normalize(sp.csr_matrix(q, dtype=np.float32))
        else:
            q = normalize(np.atleast_2d(np.asarray(q, dtype=np.float32)))
        sims = q @ idx.vecs.T
        sims = sims.toarray() if sp.issparse(sims) else np.asarray(sims)
        sims = sims.astype(np.float64)
        if exclude_ids is not None:
            for i, eid in enumerate(exclude_ids):
                if eid is not None:
                    sims[i, idx.ids == eid] = -np.inf
        top = np.argsort(-sims, axis=1, kind="stable")[:, :k]
        return top, np.take_along_axis(sims, top, axis=1)

    def neighbors(self, essay_set: int, q: np.ndarray, k: int = 3,
                  exclude_id: Optional[int] = None) -> List[dict]:
        top, sims = self.query(essay_set, q, k, None if exclude_id is None else [exclude_id])
        s = self.sets[essay_set]
        return [
            {"essay_id": int(s.ids[j]), "score": int(s.scores[j]),
             "similarity": round(float(sim), 4), "excerpt": s.excerpts[j]}
            for j, sim in zip(top[0], sims[0])
        ]

    def neighbor_scores(self, essay_set: int, q: np.ndarray, k: int,
                        exclude_ids: Optional[Sequence[int]] = None) -> np.ndarray:
        top, _ = self.query(essay_set, q, k, exclude_ids)
        return self.sets[essay_set].scores[top]


def _excerpt(text: str, n: int) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= n else text[: n - 1].rsplit(" ", 1)[0] + "…"
