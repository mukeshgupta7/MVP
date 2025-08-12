from __future__ import annotations
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class AskRequest(BaseModel):
    question: str = Field(..., description="User question in natural language")
    district: Optional[str] = Field(None, description="District name (optional but helps retrieval)")
    crop: Optional[str] = Field(None, description="Crop name (optional)")
    lang: Optional[str] = Field("en", description="Language code: en|hi")
    date: Optional[str] = Field(None, description="ISO date (YYYY-MM-DD)")

class Citation(BaseModel):
    source: str
    url: Optional[str] = None
    dataset: Optional[str] = None
    note: Optional[str] = None

class Answer(BaseModel):
    answer: str
    confidence: float
    reasons: List[str]
    citations: List[Citation] = []
    followups: List[str] = []
    debug: Optional[Dict[str, Any]] = None