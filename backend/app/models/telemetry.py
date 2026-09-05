"""Telemetry database models: PositionSample and GameplayEvent."""
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class PositionSample(Base):
    __tablename__ = "position_samples"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String(64), ForeignKey("sessions.session_id", ondelete="CASCADE"), index=True, nullable=False)
    level_name = Column(String(64), index=True, default="Level_1", nullable=False)
    
    timestamp = Column(Float, nullable=False)  # Seconds from session start
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    z = Column(Float, default=0.0, nullable=False)
    health = Column(Integer, default=100, nullable=False)

    session = relationship("GameSession", back_populates="positions")


class GameplayEvent(Base):
    __tablename__ = "gameplay_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String(64), ForeignKey("sessions.session_id", ondelete="CASCADE"), index=True, nullable=False)
    event_type = Column(String(64), index=True, nullable=False)  # DEATH, CHECKPOINT, ITEM_PICKUP, ENEMY_KILLED
    level_name = Column(String(64), index=True, default="Level_1", nullable=False)
    
    timestamp = Column(Float, nullable=False)
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    z = Column(Float, default=0.0, nullable=False)
    
    cause_or_source = Column(String(128), nullable=True)  # e.g., "Spike_Pit_A", "Goblin_Archer", "Health_Vial"
    additional_data = Column(Text, nullable=True)         # JSON string for arbitrary extra details

    session = relationship("GameSession", back_populates="events")
