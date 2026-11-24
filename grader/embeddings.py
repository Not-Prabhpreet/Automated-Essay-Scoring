"""Essay embeddings, batched and cached to disk.

Backends (EMBEDDING_BACKEND env var, default "local"):
  local  - BAAI/bge-small-en-v1.5 via sentence-transformers (open source, Apache-2.0,
           384-d, CPU friendly). Its window is 512 tokens, so longer essays are split
           into token windows that are embedded separately and averaged (weighted by
           window length), then L2-normalised.
  openai - text-embedding-3-small via the OpenAI API (OPENAI_API_KEY from .env),
           sent in batches. Drop-in alternative if a key is available.

The cache is keyed by sha256(backend, model, text), so re-running never re-embeds an
essay, and switching backends never mixes vectors from different models.
"""
from __future__ import annotations

import hashlib
import os
from typing import Dict, List, Optional, Sequence

import numpy as np

from .data import ROOT

CACHE_DIR = os.path.join(ROOT, "cache", "embeddings")
LOCAL_MODEL = os.environ.get("LOCAL_EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
OPENAI_MODEL = "text-embedding-3-small"


def _key(backend: str, model: str, text: str) -> str:
    return hashlib.sha256(f"{backend}\x00{model}\x00{text}".encode("utf-8")).hexdigest()


class DiskCache:
    """One .npz per (backend, model): parallel arrays of keys and vectors."""

    def __init__(self, backend: str, model: str, cache_dir: str = CACHE_DIR):
        safe = model.replace("/", "__")
        self.path = os.path.join(cache_dir, f"{backend}__{safe}.npz")
        self._vecs: Dict[str, np.ndarray] = {}
        if os.path.exists(self.path):
            z = np.load(self.path, allow_pickle=False)
            self._vecs = dict(zip(z["keys"].tolist(), z["vecs"]))

    def get(self, key: str) -> Optional[np.ndarray]:
        return self._vecs.get(key)

    def put_many(self, keys: Sequence[str], vecs: np.ndarray) -> None:
        for k, v in zip(keys, vecs):
            self._vecs[k] = np.asarray(v, dtype=np.float32)

    def save(self) -> None:
        if not self._vecs:
            return
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        keys = np.array(list(self._vecs.keys()))
        vecs = np.stack(list(self._vecs.values())).astype(np.float32)
        tmp = self.path + ".tmp.npz"
        np.savez(tmp, keys=keys, vecs=vecs)
        os.replace(tmp, self.path)


class Embedder:
    backend = "base"
    model = ""
    dim = 0

    def __init__(self, cache: Optional[DiskCache] = None):
        self.cache = cache if cache is not None else DiskCache(self.backend, self.model)

    def _embed_uncached(self, texts: List[str]) -> np.ndarray:  # pragma: no cover
        raise NotImplementedError

    def embed(self, texts: Sequence[str], batch_size: int = 64, save_every: int = 1024,
              progress: bool = False) -> np.ndarray:
        keys = [_key(self.backend, self.model, t) for t in texts]
        todo = [i for i, k in enumerate(keys) if self.cache.get(k) is None]
        # de-duplicate identical texts inside one call
        seen: Dict[str, int] = {}
        uniq = [i for i in todo if not (keys[i] in seen or seen.setdefault(keys[i], i) != i)]
        done = 0
        for start in range(0, len(uniq), batch_size):
            idx = uniq[start:start + batch_size]
            vecs = self._embed_uncached([texts[i] for i in idx])
            self.cache.put_many([keys[i] for i in idx], vecs)
            done += len(idx)
            if done % save_every < batch_size:
                self.cache.save()
                if progress:
                    print(f"embedded {done}/{len(uniq)}", flush=True)
        if uniq:
            self.cache.save()
        return np.stack([self.cache.get(k) for k in keys]).astype(np.float32)


class LocalEmbedder(Embedder):
    backend = "local"

    def __init__(self, model: str = LOCAL_MODEL, cache: Optional[DiskCache] = None,
                 max_tokens: int = 510, stride: int = 384):
        self.model = model
        self.max_tokens = max_tokens  # leave room for [CLS]/[SEP]
        self.stride = stride
        self._st = None
        super().__init__(cache)

    @property
    def st(self):
        if self._st is None:
            from sentence_transformers import SentenceTransformer

            self._st = SentenceTransformer(self.model, device="cpu")
            self.dim = self._st.get_sentence_embedding_dimension()
        return self._st

    def _windows(self, text: str) -> List[str]:
        tok = self.st.tokenizer
        ids = tok(text, add_special_tokens=False, verbose=False)["input_ids"]  # we window long texts ourselves
        if len(ids) <= self.max_tokens:
            return [text]
        out = []
        for start in range(0, len(ids), self.stride):
            out.append(tok.decode(ids[start:start + self.max_tokens]))
            if start + self.max_tokens >= len(ids):
                break
        return out

    def _embed_uncached(self, texts: List[str]) -> np.ndarray:
        pieces, owner, weight = [], [], []
        for i, t in enumerate(texts):
            ws = self._windows(t)
            pieces += ws
            owner += [i] * len(ws)
            weight += [max(len(w), 1) for w in ws]
        vecs = self.st.encode(pieces, batch_size=32, normalize_embeddings=True,
                              convert_to_numpy=True, show_progress_bar=False)
        out = np.zeros((len(texts), vecs.shape[1]), dtype=np.float32)
        np.add.at(out, np.array(owner), vecs * np.array(weight, dtype=np.float32)[:, None])
        out /= np.linalg.norm(out, axis=1, keepdims=True) + 1e-12
        return out


class OpenAIEmbedder(Embedder):
    backend = "openai"

    def __init__(self, model: str = OPENAI_MODEL, cache: Optional[DiskCache] = None, client=None):
        self.model = model
        self._client = client
        super().__init__(cache)

    @property
    def client(self):
        if self._client is None:
            try:
                from dotenv import load_dotenv

                load_dotenv(os.path.join(ROOT, ".env"))
            except ImportError:  # pragma: no cover
                pass
            from openai import OpenAI

            self._client = OpenAI()  # reads OPENAI_API_KEY
        return self._client

    def _embed_uncached(self, texts: List[str]) -> np.ndarray:
        resp = self.client.embeddings.create(model=self.model, input=list(texts))
        vecs = np.array([d.embedding for d in sorted(resp.data, key=lambda d: d.index)], dtype=np.float32)
        return vecs / (np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-12)


def get_embedder(backend: Optional[str] = None) -> Embedder:
    backend = (backend or os.environ.get("EMBEDDING_BACKEND", "local")).lower()
    if backend == "openai":
        return OpenAIEmbedder()
    if backend == "local":
        return LocalEmbedder()
    raise ValueError(f"unknown EMBEDDING_BACKEND={backend!r}")
