"""/score keeps its original fields and adds the grader fields."""
import os

import pytest
from fastapi.testclient import TestClient

import api.main as main

ESSAY = "Dear local newspaper, I think computers help people learn about faraway places. " * 5


class FakeGrader:
    def grade(self, essay, essay_set):
        return {
            "score": 6.0, "raw_score": 8, "raw_score_continuous": 8.1,
            "score_scale": {"min": 2, "max": 12},
            "range": {"low": 7, "high": 9, "coverage": 0.9, "low_normalized": 5.0, "high_normalized": 7.0},
            "trait_scores": {"holistic": {"score": 4.2, "confidence": 0.31}},
            "kev_score": {"score": 8.4, "confidence": 0.31},
            "needs_review": False, "review_reasons": [],
            "similar_essays": [{"essay_id": 1, "score": 8, "similarity": 0.91, "excerpt": "Dear..."}] * 3,
            "model": "fake",
        }


class FakeLegacy:
    def predict(self, essay, essay_set):
        return 5.5


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(main, "get_grader", lambda: FakeGrader())
    return TestClient(main.app)


def test_score_returns_original_and_new_fields(client):
    r = client.post("/score", json={"essay": ESSAY, "essay_set": 1})
    assert r.status_code == 200
    body = r.json()
    # original contract
    assert isinstance(body["score"], float) and 0 <= body["score"] <= 10
    assert isinstance(body["feedback"], dict)
    # added fields
    assert body["range"]["low"] <= body["raw_score"] <= body["range"]["high"]
    assert body["range"]["coverage"] == 0.9
    assert body["trait_scores"]["holistic"]["confidence"] == 0.31
    assert body["needs_review"] is False
    assert len(body["similar_essays"]) == 3 and {"essay_id", "score", "similarity", "excerpt"} <= set(body["similar_essays"][0])


def test_fallback_to_legacy_scorer_keeps_contract(monkeypatch):
    monkeypatch.setattr(main, "get_grader", lambda: None)
    monkeypatch.setattr(main, "get_legacy_scorer", lambda: FakeLegacy())
    body = TestClient(main.app).post("/score", json={"essay": ESSAY, "essay_set": 2}).json()
    assert body["score"] == 5.5 and isinstance(body["feedback"], dict)
    assert body["range"] is None and body["similar_essays"] == [] and body["needs_review"] is None


def test_validation(client):
    assert client.post("/score", json={"essay": "short", "essay_set": 1}).status_code == 422
    assert client.post("/score", json={"essay": ESSAY, "essay_set": 9}).status_code == 422


def test_essay_sets_endpoint_unchanged(client):
    sets = client.get("/essay-sets").json()["essay_sets"]
    assert [s["id"] for s in sets] == list(range(1, 9))


@pytest.mark.skipif(not os.path.exists("artifacts/grader.joblib"), reason="run scripts/train_grader.py")
def test_real_grader_end_to_end(monkeypatch):
    """Real artifact + real local embedder, Kev disabled."""
    from grader.service import Grader

    g = Grader.load()
    monkeypatch.setattr(main, "get_grader", lambda: g)
    body = TestClient(main.app).post("/score", json={"essay": ESSAY, "essay_set": 1}).json()
    assert 2 <= body["raw_score"] <= 12 and body["range"]["low"] <= body["raw_score"] <= body["range"]["high"]
    assert body["trait_scores"] is None and isinstance(body["needs_review"], bool)
    sims = [n["similarity"] for n in body["similar_essays"]]
    assert len(sims) == 3 and sims == sorted(sims, reverse=True)
