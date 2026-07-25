from interfaces.trend_getter import TrendGetter
from schemas.trend_getter_input import TrendGetterInput
import logging

logger = logging.getLogger(__name__)

class MLBTrendGetter(TrendGetter):
    def get_trends(self, trend_getter_input: TrendGetterInput) -> None:
        pass


    def get_summaries_from_after_now(self, now_utc: datetime) -> list[MLBSummary]:
        pass