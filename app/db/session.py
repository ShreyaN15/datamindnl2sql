"""
Database Session Configuration

SQLAlchemy session management and database initialization
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import os
from pathlib import Path

from app.db.base import Base

# Database URL - SQLite for simplicity
DATABASE_DIR = Path("data")
DATABASE_DIR.mkdir(exist_ok=True)
DATABASE_URL = f"sqlite:///{DATABASE_DIR}/datamind.db"

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Needed for SQLite
    echo=False  # Set to True for SQL debugging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database - create all tables"""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for getting database session
    
    Usage:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
