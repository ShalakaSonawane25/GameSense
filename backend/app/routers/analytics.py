"""Analytics endpoints serving aggregated metrics and heatmaps to React Dashboard."""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.analytics_service import AnalyticsService
from app.schemas.analytics import (
    OverviewStatsResponse,
    HeatmapPointResponse,
    PersonaComparisonResponse,
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/overview", response_model=OverviewStatsResponse)
def get_overview_statistics(
    level_name: Optional[str] = Query(None, description="Optional level name filter"),
    db: Session = Depends(get_db)
):
    """Retrieve high-level KPIs across all playtests (win rate, average duration, casualties)."""
    return AnalyticsService.get_overview_stats(db, level_name=level_name)

@router.get("/heatmaps", response_model=list[HeatmapPointResponse])
def get_heatmap_coordinates(
    type: str = Query("DEATH", description="Heatmap type: 'DEATH' or 'MOVEMENT'"),
    level_name: Optional[str] = Query("Level_1", description="Level name"),
    persona_type: Optional[str] = Query(None, description="Optional persona filter (e.g. BEGINNER, EXPLORER)"),
    grid_precision: float = Query(1.0, ge=0.5, le=10.0, description="Spatial binning resolution"),
    db: Session = Depends(get_db)
):
    """
    Returns pre-aggregated coordinate weights for rendering on the 2D/3D map canvas in React.
    Avoids client-side heavy computation.
    """
    return AnalyticsService.get_heatmap_points(
        db,
        heatmap_type=type,
        level_name=level_name,
        persona_type=persona_type,
        grid_precision=grid_precision
    )

@router.get("/personas/comparison", response_model=PersonaComparisonResponse)
def get_persona_comparison(
    level_name: Optional[str] = Query(None, description="Optional level filter"),
    db: Session = Depends(get_db)
):
    """Returns comparative metrics across all AI Personas and Human sessions."""
    return AnalyticsService.get_persona_comparison(db, level_name=level_name)
