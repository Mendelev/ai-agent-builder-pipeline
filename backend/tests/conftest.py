import pytest
import os
import tempfile
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.core.database import Base
from main import app
from app.core.database import get_db


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test using a temporary file"""
    # Create a temporary file for the database
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)  # Close the file descriptor, SQLAlchemy will open it
    
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}"
    
    # Create engine
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False
    )
    
    # Enable foreign key support for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    
    try:
        yield db
    finally:
        db.close()
        engine.dispose()
        # Clean up the temporary database file
        try:
            os.unlink(db_path)
        except OSError:
            pass


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client that uses the test database"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
