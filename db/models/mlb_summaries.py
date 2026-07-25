from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import JSON
import datetime

from db.models.base import Base


class MLBSummary(Base):
    __tablename__ = "mlb_summaries"

    event_id = Column(String, index=True, nullable=False, primary_key=True)
    market_key = Column(String, nullable=True, primary_key=True)
    outcome_description = Column(String, nullable=False, primary_key=True)
    commence_time = Column(DateTime, nullable=False)
    home_team = Column(String, nullable=True)
    away_team = Column(String, nullable=True)
    summary_data = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    sport_key = Column(String, nullable=False, primary_key=True)