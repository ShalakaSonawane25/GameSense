"""Session management router for browsing and inspecting game runs."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.session import GameSession
from app.schemas.analytics import SessionSummaryResponse

router = APIRouter(prefix="/sessions", tags=["Sessions"])

@router.get("", response_model=list[SessionSummaryResponse])
def list_sessions(
    level_name: Optional[str] = Query(None, description="Filter by level"),
    persona_type: Optional[str] = Query(None, description="Filter by persona type"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (COMPLETED, FAILED)"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Retrieve list of playtest sessions sorted by start time descending."""
    query = db.query(GameSession)
    if level_name:
        query = query.filter(GameSession.level_name == level_name)
    if persona_type and persona_type.upper() != "ALL":
        query = query.filter(GameSession.persona_type == persona_type.upper())
    if status_filter:
        query = query.filter(GameSession.status == status_filter.upper())

    return query.order_by(GameSession.start_time.desc()).offset(offset).limit(limit).all()

@router.get("/{session_id}", response_model=SessionSummaryResponse)
def get_session_detail(session_id: str, db: Session = Depends(get_db)):
    """Fetch full summary of a specific playtest session."""
    session = db.query(GameSession).filter(GameSession.session_id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with ID '{session_id}' not found."
        )
    return session
