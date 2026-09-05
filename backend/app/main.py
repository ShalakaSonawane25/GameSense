"""GameSense FastAPI Application Entrypoint."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import Base, engine
import app.models  # Ensures all models are registered with Base metadata
from app.routers import telemetry, sessions, analytics, recommendations

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

@app.get(f"{settings.API_V1_PREFIX}/health", tags=["Health"])
def health_check():
    """API health check endpoint."""
    return {"status": "healthy"}
