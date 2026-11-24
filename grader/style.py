"""The legacy hand-crafted style features (models/feature_extractor.py), cached per essay.

`legacy_clean` reproduces EssayScorer.preprocess_essay exactly (letters only, lower case,
NLTK stopwords removed), because the shipped Random Forest was trained on features of
the cleaned text. It is duplicated here so feature workers don't import TensorFlow;
tests/test_style.py checks it against the original.

The feature extractor runs TextBlob spell correction per word (~1-3 s per essay), so the
features are computed once for the whole dataset in parallel and cached to disk.
"""
from __future__ import annotations

import os
import re
from typing import Iterable, List

import pandas as pd

from .data import ROOT

CACHE_DIR = os.path.join(ROOT, "cache")
STYLE_CACHE = os.path.join(CACHE_DIR, "style_features.csv")

_FE = None


def _extractor():
    global _FE
    if _FE is None:
        from models.feature_extractor import FeatureExtractor

        _FE = FeatureExtractor()
    return _FE


def legacy_clean(essay: str, stop_words) -> str:
    essay = re.sub(r"[^A-Za-z\s]", "", essay)
    essay = essay.lower()
    words = [w for w in essay.split() if w not in stop_words]
    return " ".join(words)


def style_features(essays: Iterable[str]) -> pd.DataFrame:
    fe = _extractor()
    import contextlib
    import io

    cleaned = [legacy_clean(e, fe.stop_words) for e in essays]
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return fe.transform(cleaned)


def _worker(batch):
    ids, essays = batch
    df = style_features(essays)
    df.insert(0, "essay_id", ids)
    return df


def build_style_cache(df: pd.DataFrame, processes: int = 12, chunk: int = 25) -> pd.DataFrame:
    """Compute (or extend) the cached style features for every essay in df."""
    from multiprocessing import get_context

    os.makedirs(CACHE_DIR, exist_ok=True)
    have = pd.read_csv(STYLE_CACHE) if os.path.exists(STYLE_CACHE) else None
    todo = df if have is None else df[~df.essay_id.isin(have.essay_id)]
    if len(todo):
        ids, essays = todo.essay_id.tolist(), todo.essay.tolist()
        batches = [(ids[i:i + chunk], essays[i:i + chunk]) for i in range(0, len(ids), chunk)]
        parts: List[pd.DataFrame] = [] if have is None else [have]
        with get_context("spawn").Pool(processes) as pool:
            for n, part in enumerate(pool.imap_unordered(_worker, batches), 1):
                parts.append(part)
                if n % 40 == 0 or n == len(batches):
                    pd.concat(parts).to_csv(STYLE_CACHE, index=False)  # checkpoint
                    print(f"style features: {min(n * chunk, len(ids))}/{len(ids)}", flush=True)
        have = pd.concat(parts)
        have.to_csv(STYLE_CACHE, index=False)
    return have


def load_style_cache() -> pd.DataFrame:
    return pd.read_csv(STYLE_CACHE)
