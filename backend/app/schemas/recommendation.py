"""Recommendation Pydantic schemas."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class RecommendationResponse(BaseModel):
    id: int
    level_name: str
    issue_category: str
    severity: str
    message: str
    suggested_action: str
    target_coordinates: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class RecommendationAnalyzeRequest(BaseModel):
    level_name: Optional[str] = "Level_1"

class RecommendationAnalyzeResponse(BaseModel):
    status: str
    recommendations_created: int
    recommendations: list[RecommendationResponse]
