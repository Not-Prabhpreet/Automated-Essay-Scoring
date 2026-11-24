"""Shared helpers for the training/evaluation scripts: aligned arrays per split."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import numpy as np
import pandas as pd

from .data import SETS, load_with_splits
from .embeddings import get_embedder
from .style import load_style_cache

SPLITS = ("train", "val", "calib", "test")


@dataclass
class SetData:
    df: pd.DataFrame            # rows of this set+split, original columns
    emb: np.ndarray
    style: np.ndarray
    y: np.ndarray


def load_all(backend: str | None = None):
    """Returns (df, emb, style_df) aligned row-by-row with df."""
    df = load_with_splits()
    emb = get_embedder(backend).embed(df.essay.tolist())
    style = load_style_cache().set_index("essay_id").loc[df.essay_id]
    return df, emb, style


def by_set_split(df, emb, style) -> Dict[int, Dict[str, SetData]]:
    out: Dict[int, Dict[str, SetData]] = {}
    S = style.to_numpy(dtype=np.float32)
    for s in SETS:
        out[s] = {}
        for sp in SPLITS:
            m = ((df.essay_set == s) & (df.split == sp)).to_numpy()
            out[s][sp] = SetData(df[m].reset_index(drop=True), emb[m], S[m],
                                 df.loc[m, "domain1_score"].to_numpy())
    return out
