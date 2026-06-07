from datetime import datetime
from typing import Dict, List

from pydantic import UUID4, BaseModel


class AnalysisResult(BaseModel):
    labels: List[str]
    description: str
    objects: List[str]
    attributes: Dict[str, str]


class Recommendation(BaseModel):
    title: str
    description: str
    relevance_score: float


class AnalysisResponse(BaseModel):
    id: str
    image_url: str
    analysis: AnalysisResult
    recommendations: List[Recommendation]
    created_at: str
