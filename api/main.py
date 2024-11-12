# api/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .schemas.essay import EssayRequest, EssayResponse
from models.essay_scorer import EssayScorer
from models.feedback_generator import QualityFeedback

app = FastAPI(
    title="Essay Scoring System",
    description="Automated essay scoring and feedback API",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize models
scorer = EssayScorer()
feedback_gen = QualityFeedback()

@app.get("/")
async def root():
    return {"message": "Essay Scoring API"}

@app.post("/score", response_model=EssayResponse)
async def score_essay(request: EssayRequest):
    try:
        # Get score
        score = scorer.predict(request.essay, request.essay_set)
        
        # Get feedback
        feedback = feedback_gen.get_feedback(request.essay)
        
        return EssayResponse(
            score=score,
            feedback=feedback
        )
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
