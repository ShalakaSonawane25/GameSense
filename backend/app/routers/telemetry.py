"""Telemetry ingestion router for Unity and AI playtesting clients."""
import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.session import GameSession
from app.models.telemetry import PositionSample, GameplayEvent
from app.schemas.telemetry import (
    SessionStartRequest,
    SessionStartResponse,
    PositionBatchRequest,
    GameplayEventCreate,
    SessionEndRequest,
    SessionEndResponse,
    GenericBatchResponse,
)

router = APIRouter(prefix="/telemetry", tags=["Telemetry"])

@router.post("/session/start", response_model=SessionStartResponse, status_code=status.HTTP_201_CREATED)
def start_session(payload: SessionStartRequest, db: Session = Depends(get_db)):
    """Registers a new playtesting session before gameplay begins."""
    existing = db.query(GameSession).filter(GameSession.session_id == payload.session_id).first()
    if existing:
        return SessionStartResponse(
            status="success",
            session_id=payload.session_id,
            message="Session already registered and in progress."
        )

    new_session = GameSession(
        session_id=payload.session_id,
        persona_type=payload.persona_type.upper(),
        level_name=payload.level_name,
        game_version=payload.game_version,
        start_time=datetime.utcnow(),
        status="IN_PROGRESS"
    )
    db.add(new_session)
    db.commit()

    return SessionStartResponse(
        status="success",
        session_id=payload.session_id,
        message="Session successfully started."
    )

@router.post("/positions/batch", response_model=GenericBatchResponse)
def log_position_batch(payload: PositionBatchRequest, db: Session = Depends(get_db)):
    """Receives a batch of position samples every few seconds to reduce HTTP overhead."""
    if not payload.positions:
        return GenericBatchResponse(status="success", records_saved=0)

    # Verify session exists
    session = db.query(GameSession).filter(GameSession.session_id == payload.session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with ID '{payload.session_id}' not found. Call /session/start first."
        )

    records = [
        PositionSample(
            session_id=payload.session_id,
            level_name=payload.level_name or session.level_name,
            timestamp=p.timestamp,
            x=p.x,
            y=p.y,
            z=p.z,
            health=p.health
        )
        for p in payload.positions
    ]

    db.bulk_save_objects(records)
    db.commit()

    return GenericBatchResponse(status="success", records_saved=len(records))

@router.post("/events", status_code=status.HTTP_201_CREATED)
def log_gameplay_event(payload: GameplayEventCreate, db: Session = Depends(get_db)):
    """Records discrete gameplay events like DEATH, CHECKPOINT, ITEM_PICKUP, or ENEMY_KILLED."""
    session = db.query(GameSession).filter(GameSession.session_id == payload.session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{payload.session_id}' not found."
        )

    event_record = GameplayEvent(
        session_id=payload.session_id,
        event_type=payload.event_type.upper(),
        level_name=payload.level_name or session.level_name,
        timestamp=payload.timestamp,
        x=payload.x,
        y=payload.y,
        z=payload.z,
        cause_or_source=payload.cause_or_source,
        additional_data=json.dumps(payload.additional_data) if payload.additional_data else None
    )
    db.add(event_record)

    # Dynamically update session counters
    if payload.event_type.upper() == "DEATH":
        session.total_deaths += 1
    elif payload.event_type.upper() in ["ITEM_PICKUP", "ITEM_COLLECTED"]:
        session.items_collected += 1
    elif payload.event_type.upper() in ["ENEMY_KILLED", "ENEMY_DEFEATED"]:
        session.enemies_defeated += 1

    db.commit()
    return {"status": "success", "event_id": event_record.id, "event_type": event_record.event_type}

@router.post("/session/end", response_model=SessionEndResponse)
def end_session(payload: SessionEndRequest, db: Session = Depends(get_db)):
    """Closes an active session with final metrics and outcome status."""
    session = db.query(GameSession).filter(GameSession.session_id == payload.session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{payload.session_id}' not found."
        )

    session.end_time = datetime.utcnow()
    session.status = payload.status.upper()
    session.duration_seconds = payload.duration_seconds
    
    # Update totals if non-zero payload values provided
    if payload.total_score > 0:
        session.total_score = payload.total_score
    if payload.total_deaths > 0:
        session.total_deaths = max(session.total_deaths, payload.total_deaths)
    if payload.items_collected > 0:
        session.items_collected = max(session.items_collected, payload.items_collected)
    if payload.enemies_defeated > 0:
        session.enemies_defeated = max(session.enemies_defeated, payload.enemies_defeated)

    db.commit()

    return SessionEndResponse(
        status="success",
        session_id=session.session_id,
        final_status=session.status,
        duration_seconds=session.duration_seconds
    )
