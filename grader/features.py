"""Per-prompt scoring model: TF-IDF text features + style features -> ridge regression.

Each ASAP prompt gets its own model, trained only on that prompt's training essays:

  word TF-IDF   1-2 word n-grams (what the essay talks about, phrasing)
  char TF-IDF   2-5 character n-grams inside words (spelling, morphology, word forms)
  style         the 20 legacy features (length, spelling errors, vocabulary...), standardised

TF-IDF weights a term by how often it appears in this essay (sublinear) against how
common it is across the prompt's essays, so rare, telling phrases count more than
"the". Each TF-IDF block is L2-normalised per essay. The word block is also the vector
used to find similar essays (cosine similarity).

Everything here is sparse linear algebra: a new essay is featurised and scored in a few
milliseconds, with no neural network.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Sequence

import numpy as np
import scipy.sparse as sp
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler, normalize

ALPHAS = (0.3, 1.0, 3.0, 10.0)


def _word_vectorizer() -> TfidfVectorizer:
    return TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=30000, sublinear_tf=True,
                           dtype=np.float32)


def _char_vectorizer() -> TfidfVectorizer:
    return TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=3, max_features=40000,
                           sublinear_tf=True, dtype=np.float32)


@dataclass
class SetModel:
    essay_set: int
    alpha: float = 1.0
    word: TfidfVectorizer = field(default_factory=_word_vectorizer)
    char: TfidfVectorizer = field(default_factory=_char_vectorizer)
    scaler: StandardScaler = field(default_factory=StandardScaler)
    ridge: Optional[Ridge] = None
    val_qwk: float = float("nan")

    # -- features ---------------------------------------------------------------------
    def fit_text(self, texts: Sequence[str]) -> "SetModel":
        self.word.fit(texts)
        self.char.fit(texts)
        return self

    def text_matrix(self, texts: Sequence[str]) -> sp.csr_matrix:
        return sp.hstack([self.word.transform(texts), self.char.transform(texts)]).tocsr()

    def similarity_vectors(self, texts: Sequence[str] = None, text_matrix=None) -> sp.csr_matrix:
        """Word TF-IDF rows with unit length, so cosine similarity is a dot product.

        Only the word block is used: it captures what essays say, and it is far sparser
        than the character block, which keeps the similar-essay index small and fast."""
        m = self.text_matrix(texts) if text_matrix is None else text_matrix
        return normalize(m[:, : len(self.word.vocabulary_)])

    def features(self, text_matrix: sp.csr_matrix, style: np.ndarray) -> sp.csr_matrix:
        s = self.scaler.transform(np.asarray(style, dtype=np.float32))
        return sp.hstack([text_matrix, sp.csr_matrix(s)]).tocsr()

    # -- model ------------------------------------------------------------------------
    def fit(self, text_matrix, style, y, alpha: float) -> "SetModel":
        self.alpha = alpha
        self.scaler.fit(np.asarray(style, dtype=np.float32))
        self.ridge = Ridge(alpha=alpha).fit(self.features(text_matrix, style), y)
        return self

    def predict(self, text_matrix, style) -> np.ndarray:
        return np.asarray(self.ridge.predict(self.features(text_matrix, style)), dtype=float)


def select_model(essay_set: int, texts_tr, style_tr, y_tr, texts_va, style_va, y_va,
                 alphas: Sequence[float] = ALPHAS) -> SetModel:
    """Fit TF-IDF on the training essays, pick ridge alpha by val QWK."""
    from .data import clip_round
    from .metrics import qwk

    base = SetModel(essay_set).fit_text(texts_tr)
    Xtr, Xva = base.text_matrix(texts_tr), base.text_matrix(texts_va)
    best = None
    for a in alphas:
        m = SetModel(essay_set, word=base.word, char=base.char).fit(Xtr, style_tr, y_tr, a)
        m.val_qwk = qwk(y_va, clip_round(m.predict(Xva, style_va), essay_set))
        if best is None or m.val_qwk > best.val_qwk:
            best = m
    return best
