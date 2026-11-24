"""Per-prompt-set regression heads on essay embeddings (+ optional style features).

Each ASAP prompt set has its own task and score scale, so each gets its own small head
that maps [embedding | standardised style features] -> resolved domain1 score.
Hyper-parameters are chosen on the val split only; test is never touched here.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np
from sklearn.linear_model import Ridge
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .data import SEED, clip_round
from .metrics import qwk

RIDGE_ALPHAS = (0.1, 0.3, 1.0, 3.0, 10.0, 30.0)
MLP_HIDDEN = (128,)
MLP_ALPHAS = (1e-3, 1e-2, 1e-1)


def make_inputs(emb: Optional[np.ndarray], style: Optional[np.ndarray]) -> np.ndarray:
    parts = [p for p in (emb, style) if p is not None]
    if not parts:
        raise ValueError("need embeddings and/or style features")
    return np.hstack(parts).astype(np.float32)


@dataclass
class SetHead:
    essay_set: int
    kind: str  # "ridge" | "mlp"
    param: float
    use_style: bool
    model: object = None
    style_scaler: Optional[StandardScaler] = None
    val_qwk: float = float("nan")

    def _x(self, emb, style):
        s = None
        if self.use_style:
            s = self.style_scaler.transform(style)
        return make_inputs(emb, s)

    def fit(self, emb, style, y):
        if self.use_style:
            self.style_scaler = StandardScaler().fit(style)
        X = self._x(emb, style)
        if self.kind == "ridge":
            self.model = Ridge(alpha=self.param, random_state=SEED)
        elif self.kind == "mlp":
            self.model = make_pipeline(
                StandardScaler(),
                MLPRegressor(hidden_layer_sizes=MLP_HIDDEN, alpha=self.param, max_iter=500,
                             early_stopping=True, validation_fraction=0.15,
                             n_iter_no_change=20, random_state=SEED),
            )
        else:
            raise ValueError(self.kind)
        self.model.fit(X, y)
        return self

    def predict(self, emb, style=None) -> np.ndarray:
        return np.asarray(self.model.predict(self._x(emb, style)), dtype=float)


def candidates(kinds=("ridge", "mlp")) -> List[tuple]:
    out = []
    if "ridge" in kinds:
        out += [("ridge", a) for a in RIDGE_ALPHAS]
    if "mlp" in kinds:
        out += [("mlp", a) for a in MLP_ALPHAS]
    return out


def select_head(essay_set: int, emb_tr, sty_tr, y_tr, emb_va, sty_va, y_va,
                kind: str, use_style: bool) -> SetHead:
    """Best hyper-parameter for one (set, kind, use_style) by val QWK."""
    best = None
    for k, p in candidates((kind,)):
        h = SetHead(essay_set, k, p, use_style).fit(emb_tr, sty_tr, y_tr)
        score = qwk(y_va, clip_round(h.predict(emb_va, sty_va), essay_set))
        h.val_qwk = score
        if best is None or score > best.val_qwk:
            best = h
    return best


@dataclass
class HeadBundle:
    """One fitted head per set, plus the config they were selected with."""
    kind: str
    use_style: bool
    heads: Dict[int, SetHead] = field(default_factory=dict)

    def predict(self, essay_set: int, emb, style=None) -> np.ndarray:
        return self.heads[essay_set].predict(emb, style)
