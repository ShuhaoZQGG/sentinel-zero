"""Database base configuration for SentinelZero."""

import os
from contextlib import contextmanager
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Create base class for models
Base = declarative_base()

# Database configuration
DEFAULT_DB_PATH = Path.home() / ".sentinel" / "sentinel.db"
DB_PATH = os.environ.get("SENTINEL_DB_PATH", str(DEFAULT_DB_PATH))

# Ensure directory exists
Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)

# Create engine
engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False},
    echo=False
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_session() -> Session:
    """Get a database session context manager."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db():
    """Initialize the database."""
    Base.metadata.create_all(bind=engine)


def reset_db():
    """Reset the database (drop all tables and recreate)."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)