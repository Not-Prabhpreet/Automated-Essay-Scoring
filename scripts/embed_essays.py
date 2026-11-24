"""Embed every ASAP essay with the configured backend (EMBEDDING_BACKEND, default local
bge-small) and cache the vectors under cache/embeddings/."""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from grader.data import load_asap  # noqa: E402
from grader.embeddings import get_embedder  # noqa: E402

if __name__ == "__main__":
    df = load_asap()
    emb = get_embedder()
    t = time.time()
    vecs = emb.embed(df.essay.tolist(), batch_size=64, save_every=512, progress=True)
    print(f"{emb.backend}:{emb.model} -> {vecs.shape} in {time.time() - t:.0f}s; cache {emb.cache.path}")
