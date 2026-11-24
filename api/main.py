# api/main.py
import asyncio
import os
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .schemas.essay import EssayRequest, EssayResponse
from models.feedback_generator import QualityFeedback

app = FastAPI(
    title="Essay Scoring System",
    description="Automated essay scoring and feedback API",
    version="1.1.0"
)

# CORS configuration
# Allowed frontend origins: CORS_ORIGINS (comma-separated) and/or CORS_ORIGIN_REGEX.
_origins = os.environ.get(
    "CORS_ORIGINS", "https://essay-scorer-frontend.onrender.com,http://localhost:5173"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _origins.split(",") if o.strip()],
    allow_origin_regex=os.environ.get("CORS_ORIGIN_REGEX") or None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Initialize models.
# The grader (embeddings + per-set head + conformal range + evidence) is used when its
# artifact exists; otherwise /score falls back to the original LSTM + RF scorer and the
# added fields are left empty. Kev trait feedback is used only when KEV_URL is set.
feedback_gen = QualityFeedback()
_grader = None
_legacy = None


def get_grader():
    global _grader
    if _grader is None:
        from grader.service import ARTIFACT_PATH, Grader

        if not os.path.exists(ARTIFACT_PATH):
            return None
        kev = None
        if os.environ.get("KEV_URL"):
            from grader.kev import KevClient

            kev = KevClient(os.environ["KEV_URL"])
        _grader = Grader.load(ARTIFACT_PATH, kev_client=kev)
    return _grader


def get_legacy_scorer():
    global _legacy
    if _legacy is None:
        from models.essay_scorer import EssayScorer

        _legacy = EssayScorer()
    return _legacy


@app.get("/")
async def root():
    return {"message": "Essay Scoring API"}


def _score(request: EssayRequest) -> dict:
    feedback = feedback_gen.get_feedback(request.essay)
    grader = get_grader()
    if grader is None:
        return {"score": get_legacy_scorer().predict(request.essay, request.essay_set),
                "feedback": feedback}
    result = grader.grade(request.essay, request.essay_set)
    result["feedback"] = feedback
    return result


# All scoring runs on one dedicated worker thread. On a small (1 vCPU) machine requests
# queue instead of fighting over the CPU, and PyTorch keeps reusing the thread pool it
# set up on that thread instead of meeting a new thread on every request.
_worker = ThreadPoolExecutor(max_workers=1, thread_name_prefix="scorer")


@app.on_event("startup")
async def _warm_up():
    """Load the grader and run one essay before taking traffic, so the first real
    request doesn't pay for model loading."""
    if os.environ.get("SKIP_WARMUP"):
        return

    def warm():
        if get_grader() is not None:
            _score(EssayRequest(essay="This is a short warm-up essay about computers.", essay_set=1))

    await asyncio.get_running_loop().run_in_executor(_worker, warm)


@app.post("/score", response_model=EssayResponse)
async def score_essay(request: EssayRequest):
    try:
        result = await asyncio.get_running_loop().run_in_executor(_worker, _score, request)
        return EssayResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/essay-sets")
async def get_essay_sets():
    """Get information about available essay sets"""
    return {
        "essay_sets": [
            {
                "id": 1,
                "description": "Persuasive essay about computers in education",
                "score_range": "2-12"
            },
            {
                "id": 2,
                "description": "Library censorship essay",
                "score_range": "1-6"
            },
            {
                "id": 3,
                "description": "Text analysis and comprehension",
                "score_range": "0-3"
            },
            {
                "id": 4,
                "description": "Narrative analysis and interpretation",
                "score_range": "0-3"
            },
            {
                "id": 5,
                "description": "Memoir analysis and interpretation",
                "score_range": "0-4"
            },
            {
                "id": 6,
                "description": "Historical analysis essay",
                "score_range": "0-4"
            },
            {
                "id": 7,
                "description": "Extended response on patience",
                "score_range": "0-30"
            },
            {
                "id": 8,
                "description": "Extended narrative response",
                "score_range": "0-60"
            }
        ]
    }
