"""Game Balancing Recommendations Router."""
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.balance_service import BalanceService
from app.schemas.recommendation import (
    RecommendationResponse,
    RecommendationAnalyzeRequest,
    RecommendationAnalyzeResponse,
)

router = APIRouter(prefix="/recommendations", tags=["Game Balancing"])

@router.get("", response_model=list[RecommendationResponse])
def get_recommendations(
    level_name: Optional[str] = Query(None, description="Filter recommendations by level"),
    db: Session = Depends(get_db)
):
    """Fetch existing game balancing suggestions stored in the database."""
    return BalanceService.get_existing_recommendations(db, level_name=level_name)

@router.post("/analyze", response_model=RecommendationAnalyzeResponse, status_code=status.HTTP_200_OK)
def trigger_balance_analysis(
    payload: RecommendationAnalyzeRequest,
    db: Session = Depends(get_db)
):
    """
    Triggers the rule-based balancing engine on current telemetry records
    to identify bottlenecks, severe hazards, and persona disparities.
    """
    new_recs = BalanceService.analyze_and_generate_recommendations(
        db,
        level_name=payload.level_name
    )
    
    return RecommendationAnalyzeResponse(
        status="success",
        recommendations_created=len(new_recs),
        recommendations=new_recs
    )
