"""GameSession database model."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from app.database import Base

class GameSession(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String(64), unique=True, index=True, nullable=False)
    persona_type = Column(String(32), index=True, default="HUMAN", nullable=False)
    level_name = Column(String(64), index=True, default="Level_1", nullable=False)
    game_version = Column(String(32), default="1.0.0", nullable=False)
    
    start_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    end_time = Column(DateTime, nullable=True)
    status = Column(String(32), default="IN_PROGRESS", nullable=False)  # IN_PROGRESS, COMPLETED, FAILED, ABORTED
    
    duration_seconds = Column(Float, default=0.0, nullable=False)
    total_score = Column(Integer, default=0, nullable=False)
    total_deaths = Column(Integer, default=0, nullable=False)
    items_collected = Column(Integer, default=0, nullable=False)
    enemies_defeated = Column(Integer, default=0, nullable=False)

    # Relationships
    positions = relationship("PositionSample", back_populates="session", cascade="all, delete-orphan")
    events = relationship("GameplayEvent", back_populates="session", cascade="all, delete-orphan")
