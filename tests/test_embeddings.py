from types import SimpleNamespace

import numpy as np

from grader.embeddings import DiskCache, Embedder, OpenAIEmbedder


class CountingEmbedder(Embedder):
    backend, model = "fake", "fake-1"

    def __init__(self, cache):
        self.calls = []
        super().__init__(cache)

    def _embed_uncached(self, texts):
        self.calls.append(list(texts))
        return np.array([[len(t), 1.0] for t in texts], dtype=np.float32)


def test_cache_batches_dedupes_and_persists(tmp_path):
    e = CountingEmbedder(DiskCache("fake", "fake-1", str(tmp_path)))
    v = e.embed(["a", "bb", "a", "ccc"], batch_size=2)
    assert v.shape == (4, 2) and np.allclose(v[0], v[2])
    assert sum(len(c) for c in e.calls) == 3          # "a" embedded once
    assert all(len(c) <= 2 for c in e.calls)          # batched
    e2 = CountingEmbedder(DiskCache("fake", "fake-1", str(tmp_path)))
    assert np.allclose(e2.embed(["bb"]), v[1]) and e2.calls == []  # served from disk


def test_openai_backend_batches_and_normalises(tmp_path):
    seen = []

    class FakeEmbeddings:
        def create(self, model, input):
            seen.append((model, list(input)))
            data = [SimpleNamespace(index=i, embedding=[3.0, 4.0]) for i in range(len(input))][::-1]
            return SimpleNamespace(data=data)

    client = SimpleNamespace(embeddings=FakeEmbeddings())
    e = OpenAIEmbedder(cache=DiskCache("openai", "text-embedding-3-small", str(tmp_path)), client=client)
    v = e.embed([f"essay {i}" for i in range(5)], batch_size=2)
    assert [len(x[1]) for x in seen] == [2, 2, 1]
    assert seen[0][0] == "text-embedding-3-small"
    assert np.allclose(v, [[0.6, 0.8]] * 5)
