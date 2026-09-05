"""Analytics Pydantic schemas for the React Dashboard."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class SessionSummaryResponse(BaseModel):
    id: int
    session_id: str
    persona_type: str
    level_name: str
    game_version: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str
    duration_seconds: float
    total_score: int
    total_deaths: int
    items_collected: int
    enemies_defeated: int

    model_config = ConfigDict(from_attributes=True)

class OverviewStatsResponse(BaseModel):
    total_sessions: int
    completed_sessions: int
    failed_sessions: int
    win_rate_percentage: float
    avg_duration_seconds: float
    total_deaths_recorded: int
    total_items_collected: int
    total_enemies_defeated: int
    active_personas_count: int

class HeatmapPointResponse(BaseModel):
    x: float
    y: float
    weight: int = 1
    cause: Optional[str] = None

class PersonaMetricResponse(BaseModel):
    persona_type: str
    session_count: int
    win_rate_percentage: float
    avg_duration_seconds: float
    avg_deaths: float
    avg_score: float
    avg_items_collected: float

class PersonaComparisonResponse(BaseModel):
    personas: list[PersonaMetricResponse]
