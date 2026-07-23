from contextlib import contextmanager
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import Generator

from .models import Base

def get_engine(db_path: Path):
    """Creates a SQLAlchemy engine for SQLite."""
    # check_same_thread is False to allow usage in different threads (like Streamlit apps)
    engine_url = f"sqlite:///{db_path}"
    return create_engine(engine_url, connect_args={"check_same_thread": False})

# Global sessionmaker - will be bound to an engine later or instantiated dynamically
SessionLocal = sessionmaker(autocommit=False, autoflush=False)

@contextmanager
def get_session(engine) -> Generator:
    """Context manager yielding a SQLAlchemy session."""
    SessionLocal.configure(bind=engine)
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def init_db(engine):
    """Creates all tables from Base.metadata."""
    Base.metadata.create_all(bind=engine)
