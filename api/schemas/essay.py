# api/schemas/essay.py
from pydantic import BaseModel, Field
from typing import Dict, List, Optional

class EssayRequest(BaseModel):
    essay: str = Field(..., min_length=10, description="Essay text to be scored")
    essay_set: int = Field(1, ge=1, le=8, description="Essay set number (1-8)")

class EssayResponse(BaseModel):
    score: float
    feedback: Dict[str, List[str]]