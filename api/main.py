# api/main.py
import os

from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from .schemas.essay import EssayRequest, EssayResponse
from models.feedback_generator import QualityFeedback

app = FastAPI(
    title="Essay Scoring System",
    description="Automated essay scoring and feedback API",
    version="1.1.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://essay-scorer-frontend.onrender.com"],  # Your frontend URL
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


@app.post("/score", response_model=EssayResponse)
async def score_essay(request: EssayRequest):
    try:
        return EssayResponse(**await run_in_threadpool(_score, request))
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
