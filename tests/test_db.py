"""Unit and integration tests for db.db session lifecycle and connect args."""

import os
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import Integer, create_engine, select
from sqlalchemy.orm import Mapped, mapped_column, sessionmaker

# db.db creates the engine at import time; tests patch SessionLocal and never use it.
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from db.db import connect_args_for_database_url, get_db
from db.models.base import Base


@pytest.mark.parametrize(
    ("database_url", "expected"),
    [
        ("sqlite:///./local.db", {"check_same_thread": False}),
        ("sqlite:///:memory:", {"check_same_thread": False}),
        ("postgresql://host/db", {}),
        (None, {}),
    ],
)
def test_connect_args_for_database_url(database_url, expected):
    assert connect_args_for_database_url(database_url) == expected


def test_get_db_yields_session():
    mock_session = MagicMock()
    mock_session_local = MagicMock(return_value=mock_session)

    with patch("db.db.SessionLocal", mock_session_local):
        with get_db() as session:
            assert session is mock_session

    mock_session_local.assert_called_once_with()


def test_get_db_closes_session_after_block():
    mock_session = MagicMock()
    mock_session_local = MagicMock(return_value=mock_session)

    with patch("db.db.SessionLocal", mock_session_local):
        with get_db():
            pass

    mock_session.close.assert_called_once_with()


def test_get_db_closes_session_on_exception():
    mock_session = MagicMock()
    mock_session_local = MagicMock(return_value=mock_session)

    with patch("db.db.SessionLocal", mock_session_local):
        with pytest.raises(RuntimeError, match="boom"):
            with get_db():
                raise RuntimeError("boom")

    mock_session.close.assert_called_once_with()


class _SmokeRow(Base):
    __tablename__ = "test_db_smoke"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)


def test_get_db_sqlite_integration():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine, tables=[_SmokeRow.__table__])
    test_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    with patch("db.db.SessionLocal", test_session_local):
        with get_db() as session:
            session.add(_SmokeRow(id=1))
            session.commit()
            row = session.execute(select(_SmokeRow)).scalar_one()
            assert row.id == 1
