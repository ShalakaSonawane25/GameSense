"""Balance Recommendation database model."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from app.database import Base

class BalanceRecommendation(Base):
    __tablename__ = "balance_recommendations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    level_name = Column(String(64), index=True, default="Level_1", nullable=False)
    issue_category = Column(String(64), nullable=False)  # DIFFICULTY_SPIKE, WEAPON_IMBALANCE, UNDER_CHALLENGING, PACING
    severity = Column(String(32), default="MEDIUM", nullable=False)  # HIGH, MEDIUM, LOW
    
    message = Column(Text, nullable=False)
    suggested_action = Column(Text, nullable=False)
    target_coordinates = Column(String(128), nullable=True)  # JSON e.g. '{"x": 34.2, "y": 12.0}'
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
