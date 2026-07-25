"""Read-only boundary for loading upcoming MLB summaries into the Trends pipeline."""

from abc import ABC, abstractmethod
from datetime import datetime

from db.models.mlb_summaries import MLBSummary


class MlbSummaryRepositoryInterface(ABC):
    @abstractmethod
    def get_mlb_summaries_from_after_now(self, now_utc: datetime) -> list[MLBSummary]:
        """Return all summaries with commence_time strictly after now_utc.

        Caller supplies now_utc so the worker controls timezone policy and tests
        can pin a fixed clock. Excludes started games (commence_time == now_utc).
        """
        pass
