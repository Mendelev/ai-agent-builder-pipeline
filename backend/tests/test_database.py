# backend/tests/test_database.py
import pytest
from sqlalchemy.orm import Session
from app.core.database import get_db, SessionLocal, engine, Base


def test_get_db_generator():
    """Test database session generator."""
    db_gen = get_db()
    db = next(db_gen)
    
    assert isinstance(db, Session)
    assert db.bind == engine
    
    # Test cleanup
    try:
        next(db_gen)
    except StopIteration:
        pass  # Expected behavior


def test_session_local_creation():
    """Test SessionLocal creates valid sessions."""
    db = SessionLocal()
    
    assert isinstance(db, Session)
    assert db.bind == engine
    
    db.close()


def test_base_declarative():
    """Test Base is properly configured."""
    assert Base is not None
    assert hasattr(Base, 'metadata')
    # Note: query attribute is not available in SQLAlchemy 2.0 declarative_base


def test_engine_configuration():
    """Test engine is properly configured."""
    assert engine is not None
    # Access pool properties through engine.pool
    assert engine.pool.size() == 10
    assert engine.pool._max_overflow == 20