"""GameSense FastAPI Application Entrypoint."""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.config import settings
from app.database import Base, engine, get_db
import app.models  # Ensures all models are registered with Base metadata
from app.schemas.telemetry import (
    GameplayEventCreate,
    SessionStartRequest,
    SessionStartResponse,
    SessionEndRequest,
    SessionEndResponse,
)
from app.routers import telemetry, sessions, analytics, recommendations
from app.routers.telemetry import log_gameplay_event, start_session, end_session

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create database tables if they do not exist
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown logic (if any)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AI-Powered Automated Game Playtesting and Game Balancing API",
    lifespan=lifespan
)

# Configure CORS so React dashboard can communicate seamlessly
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount feature routers under API prefix
app.include_router(telemetry.router, prefix=settings.API_V1_PREFIX)
app.include_router(sessions.router, prefix=settings.API_V1_PREFIX)
app.include_router(analytics.router, prefix=settings.API_V1_PREFIX)
app.include_router(recommendations.router, prefix=settings.API_V1_PREFIX)

@app.get("/", tags=["Health"])
def root():
    """Root health check and information endpoint."""
    return {
        "status": "online",
        "project": "GameSense",
        "version": settings.VERSION,
        "docs_url": "/docs",
        "message": "GameSense Backend API is running."
    }

@app.get("/health", tags=["Health"])
@app.get(f"{settings.API_V1_PREFIX}/health", tags=["Health"])
def health_check():
    """API health check endpoint."""
    return {"status": "healthy"}
    
@app.post("/telemetry", status_code=status.HTTP_201_CREATED, tags=["Telemetry"])
def log_telemetry(payload: GameplayEventCreate, db: Session = Depends(get_db)):
    """Root-level telemetry event ingestion endpoint (Member 3 - Task 3)."""
    return log_gameplay_event(payload=payload, db=db)

@app.post("/session/start", response_model=SessionStartResponse, status_code=status.HTTP_201_CREATED, tags=["Sessions"])
def start_session_root(payload: SessionStartRequest, db: Session = Depends(get_db)):
    """Root-level session start endpoint (Member 3 - Task 6)."""
    return start_session(payload=payload, db=db)

@app.post("/session/end", response_model=SessionEndResponse, tags=["Sessions"])
def end_session_root(payload: SessionEndRequest, db: Session = Depends(get_db)):
    """Root-level session end endpoint (Member 3 - Task 6)."""
    return end_session(payload=payload, db=db)


