"""Configuration settings for GameSense Backend."""
from pathlib import Path
from pydantic import BaseModel

# Base directory for the backend project
BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseModel):
    PROJECT_NAME: str = "GameSense Backend"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api"
    
    # SQLite Database location: stored in backend/gamesense.db
    DATABASE_PATH: Path = BASE_DIR / "gamesense.db"
    DATABASE_URL: str = f"sqlite:///{DATABASE_PATH}"
    
    # Allowed CORS origins (for React Vite / Create React App dashboard)
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8080",
        "*"  # Allow all during development to avoid blocking Member 1
    ]

settings = Settings()
