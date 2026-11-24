# api/schemas/essay.py
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class EssayRequest(BaseModel):
    essay: str = Field(..., min_length=10, description="Essay text to be scored")
    essay_set: int = Field(1, ge=1, le=8, description="Essay set number (1-8)")


class ScoreRange(BaseModel):
    low: int = Field(..., description="Lower end of the range, on the set's native scale")
    high: int = Field(..., description="Upper end of the range, on the set's native scale")
    coverage: float = Field(..., description="Target coverage of the range (0.9 = 90%)")
    low_normalized: float = Field(..., description="low on the 0-10 scale used by `score`")
    high_normalized: float = Field(..., description="high on the 0-10 scale used by `score`")


class TraitScore(BaseModel):
    score: float = Field(..., description="Kev's expected rubric level, on the rater's scale")
    confidence: float = Field(..., description="Kev score confidence (0-1; not an accuracy rate)")


class SimilarEssay(BaseModel):
    essay_id: int
    score: int = Field(..., description="Human (resolved) score of the training essay")
    similarity: float = Field(..., description="Cosine similarity of the embeddings")
    excerpt: str


class ScaleInfo(BaseModel):
    min: int
    max: int


class KevScore(BaseModel):
    score: float
    confidence: float


class EssayResponse(BaseModel):
    # --- original fields (unchanged meaning) ---
    score: float = Field(..., description="Predicted score on a 0-10 scale")
    feedback: Dict[str, List[str]]
    # --- added fields (all optional so older clients are unaffected) ---
    raw_score: Optional[int] = Field(None, description="Predicted score on the set's native scale")
    score_scale: Optional[ScaleInfo] = None
    range: Optional[ScoreRange] = Field(None, description="90% conformal score range")
    trait_scores: Optional[Dict[str, TraitScore]] = Field(
        None, description="Kev rubric-trait scores; null when no Kev server is configured")
    kev_score: Optional[KevScore] = None
    needs_review: Optional[bool] = Field(None, description="True when a human should check this score")
    review_reasons: List[str] = Field(default_factory=list)
    similar_essays: List[SimilarEssay] = Field(default_factory=list)
    model: Optional[str] = None
