from pydantic import BaseModel
from interfaces.insights_identifier import InsightsIdentifier

class TrendGetterInput(BaseModel):
    sport_insights_indentifier: InsightsIdentifier