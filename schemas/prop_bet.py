from pydantic import BaseModel
from typing import Literal


class PropBet(BaseModel):
    event_id: str
    market_key: str
    outcome_description: str
    commence_time: datetime.datetime
    home_team: str
    away_team: str
    summary_data: dict
    created_at: datetime.datetime
    updated_at: datetime.datetime
    sport_key: Sport