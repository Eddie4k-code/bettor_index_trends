"""Read-only SQLAlchemy access to upcoming MLB summaries for the Trends worker.

Loads the full upcoming slate (commence_time strictly after now_utc) for
MlbTrendGetter; no pagination or hit-rate filters unlike the REST API repo.
"""

import logging
from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from db.models.mlb_summaries import MLBSummary
from interfaces.summary_repository_interface import SummaryRepositoryInterface

logger = logging.getLogger(__name__)


class MlbSummaryRepository(SummaryRepositoryInterface):
    """PostgreSQL/SQLite read implementation for MLBSummary rows."""

    def __init__(self, db: Session):
        self.db = db

    def get_summaries_from_after_now(self, now_utc: datetime) -> list[MLBSummary]:
        """Return all upcoming summaries ordered by commence_time ascending.

        Strict ``>`` excludes games that have already started (including
        commence_time equal to now_utc).

        Raises:
            SQLAlchemyError: Logged with now_utc context before re-raising.
        """
        try:
            return (
                self.db.query(MLBSummary)
                .filter(MLBSummary.commence_time > now_utc)
                .order_by(MLBSummary.commence_time.asc())
                .all()
            )
        except SQLAlchemyError:
            logger.exception(
                "Failed to load upcoming MLB summaries after now_utc=%s",
                now_utc.isoformat(),
            )
            raise
