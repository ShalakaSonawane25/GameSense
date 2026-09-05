"""Database connection and session factory for GameSense."""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.config import settings

# SQLite requires check_same_thread=False when used with FastAPI multi-threading
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Dependency for FastAPI route handlers to obtain a database session."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
