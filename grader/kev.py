"""Kev rubric feedback through Kev's System One endpoint (POST /v1/systemone).

Request/response shapes follow the Kev README (github.com/jaredpalmer/kev, "API"):
  request:  {"state": str, "model": "kev-latest", "questions": {id: {"type": "score",
             "instructions": str, "criteria": [level, ...]}}}
  response: {"answers": {id: {"type": "score", "score": <mean level index, from 0>,
             "confidence": float, "legend": {...}, "probabilities": {"0": p, ...}}}, ...}

Kev runs as a separate server (`python -m kev.serve --run jaredpalmer/kev-0.8b`), so
this module only needs httpx. Answers are cached on disk keyed by a hash of the exact
request, so the offline evaluation runs once and the API can reuse cached essays.
"""
from __future__ import annotations

import hashlib
import json
import os
import threading
from typing import Dict, Optional

from .data import ROOT
import numpy as np

from .rubrics import questions_for, to_domain1, trait_rater_value

KEV_CACHE = os.path.join(ROOT, "cache", "kev_answers.jsonl")
DEFAULT_URL = os.environ.get("KEV_URL", "http://127.0.0.1:8009")
MODEL = "kev-latest"


def request_body(essay: str, essay_set: int) -> dict:
    return {"state": essay, "model": MODEL, "questions": questions_for(essay_set)}


def request_key(body: dict) -> str:
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode("utf-8")).hexdigest()


class KevCache:
    """Append-only JSONL cache: one {"key", "answers"} line per request."""

    def __init__(self, path: str = KEV_CACHE):
        self.path = path
        self._lock = threading.Lock()
        self._data: Dict[str, dict] = {}
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        rec = json.loads(line)
                        self._data[rec["key"]] = rec["answers"]

    def get(self, key: str) -> Optional[dict]:
        return self._data.get(key)

    def put(self, key: str, answers: dict) -> None:
        with self._lock:
            self._data[key] = answers
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps({"key": key, "answers": answers}) + "\n")

    def __len__(self) -> int:
        return len(self._data)


class KevClient:
    def __init__(self, base_url: str = DEFAULT_URL, cache: Optional[KevCache] = None,
                 api_key: Optional[str] = None, timeout: float = 600.0):
        self.base_url = base_url.rstrip("/")
        self.cache = cache if cache is not None else KevCache()
        self.api_key = api_key or os.environ.get("KEV_API_KEY")
        self.timeout = timeout

    def _post(self, body: dict) -> dict:
        import httpx

        headers = {"content-type": "application/json"}
        if self.api_key:
            headers["authorization"] = f"Bearer {self.api_key}"
        r = httpx.post(f"{self.base_url}/v1/systemone", json=body, headers=headers, timeout=self.timeout)
        r.raise_for_status()
        return r.json()["answers"]

    def answers(self, essay: str, essay_set: int, offline: bool = False) -> Optional[dict]:
        """Raw Kev answers for an essay (cached). offline=True never calls the server."""
        body = request_body(essay, essay_set)
        key = request_key(body)
        hit = self.cache.get(key)
        if hit is not None or offline:
            return hit
        ans = self._post(body)
        self.cache.put(key, ans)
        return ans

    def is_up(self) -> bool:
        try:
            import httpx

            return httpx.get(f"{self.base_url}/v1/models", timeout=3.0).status_code == 200
        except Exception:
            return False


def summarize(essay_set: int, answers: dict) -> dict:
    """Kev answers -> per-trait scores on the rater scale, confidences, domain1 estimate.

    "Traits" are the rubric's own dimensions: four for set 7, six for set 8, the
    holistic rubric for sets 1-6, plus Language Conventions for set 2.
    """
    traits = {}
    for name, a in answers.items():
        traits[name] = {
            "score": round(trait_rater_value(essay_set, float(a["score"]), name), 3),
            "confidence": round(float(a["confidence"]), 3),
            "probabilities": {
                str(int(trait_rater_value(essay_set, int(k), name))): round(float(p), 4)
                for k, p in a["probabilities"].items()
            },
        }
    idx = {name: float(a["score"]) for name, a in answers.items()}
    if "holistic" in answers:
        conf = float(answers["holistic"]["confidence"])
    else:
        conf = float(np.mean([t["confidence"] for t in traits.values()]))
    return {"traits": traits, "domain1": to_domain1(essay_set, idx), "confidence": conf}
