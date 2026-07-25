import os
from contextlib import contextmanager
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


def connect_args_for_database_url(database_url: str | None) -> dict:
    """Return SQLAlchemy connect_args for the given database URL.

    SQLite requires check_same_thread=False for multi-threaded workers; other
    backends use an empty dict.
    """
    if database_url and "sqlite" in database_url:
        return {"check_same_thread": False}
    return {}


engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args_for_database_url(DATABASE_URL),
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()