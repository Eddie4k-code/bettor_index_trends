"""Unit tests for MlbSummaryRepository upcoming-slate query."""

import logging
import os
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from db.models.mlb_summaries import MLBSummary
from repositories.mlb_summary_repository import MlbSummaryRepository


def _make_summary(
    event_id: str,
    commence_time: datetime,
    *,
    outcome_description: str = "Test Player Hits",
) -> MLBSummary:
    return MLBSummary(
        event_id=event_id,
        market_key="player_hits",
        outcome_description=outcome_description,
        commence_time=commence_time,
        home_team="LAD",
        away_team="SD",
        summary_data={"foo": "bar"},
        sport_key="baseball_mlb",
    )


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    MLBSummary.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def repo(db_session):
    return MlbSummaryRepository(db_session)


def test_returns_future_summaries_only(repo, db_session):
    now = datetime(2026, 7, 25, 18, 0, 0)
    db_session.add_all(
        [
            _make_summary("E1", now + timedelta(hours=1)),
            _make_summary("E2", now + timedelta(hours=2)),
            _make_summary("E3", now - timedelta(hours=1)),
        ]
    )
    db_session.commit()

    results = repo.get_mlb_summaries_from_after_now(now)
    event_ids = {summary.event_id for summary in results}

    assert event_ids == {"E1", "E2"}


def test_excludes_commence_time_equal_to_now(repo, db_session):
    now = datetime(2026, 7, 25, 18, 0, 0)
    db_session.add_all(
        [
            _make_summary("E1", now),
            _make_summary("E2", now + timedelta(hours=1)),
        ]
    )
    db_session.commit()

    results = repo.get_mlb_summaries_from_after_now(now)
    event_ids = {summary.event_id for summary in results}

    assert event_ids == {"E2"}


def test_returns_empty_list_when_no_upcoming(repo, db_session):
    now = datetime(2026, 7, 25, 18, 0, 0)
    db_session.add_all(
        [
            _make_summary("E1", now - timedelta(hours=1)),
            _make_summary("E2", now),
        ]
    )
    db_session.commit()

    results = repo.get_mlb_summaries_from_after_now(now)

    assert results == []


def test_orders_by_commence_time_asc(repo, db_session):
    now = datetime(2026, 7, 25, 18, 0, 0)
    db_session.add_all(
        [
            _make_summary("E2", now + timedelta(hours=2)),
            _make_summary("E1", now + timedelta(hours=1)),
        ]
    )
    db_session.commit()

    results = repo.get_mlb_summaries_from_after_now(now)

    assert [summary.event_id for summary in results] == ["E1", "E2"]


def test_logs_and_reraises_on_query_failure(repo, db_session, caplog):
    now = datetime(2026, 7, 25, 18, 0, 0)
    caplog.set_level(logging.ERROR, logger="repositories.mlb_summary_repository")

    with patch.object(
        db_session,
        "query",
        side_effect=SQLAlchemyError("connection lost"),
    ):
        with pytest.raises(SQLAlchemyError, match="connection lost"):
            repo.get_mlb_summaries_from_after_now(now)

    assert "Failed to load upcoming MLB summaries" in caplog.text
    assert now.isoformat() in caplog.text
