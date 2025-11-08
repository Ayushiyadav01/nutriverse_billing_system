import os
from pathlib import Path
from typing import Optional

class Settings:
    PROJECT_NAME: str = "Nutriverse API"
    PROJECT_VERSION: str = "0.1.0"
    
    # Database settings
    SQLITE_DB_PATH: str = os.getenv("SQLITE_DB_PATH", "nutriverse.db")
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{SQLITE_DB_PATH}")
    
    # API settings
    API_V1_STR: str = "/api"
    
    # Tax and billing defaults
    DEFAULT_TAX_PERCENT: float = 0.0  # Default tax percentage
    
    # CORS settings
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:8501",  # Streamlit default
        "http://localhost:3000",  # For any other frontend
        "http://localhost",
        "http://localhost:8080",
    ]
    
    # Order number prefix
    ORDER_NUMBER_PREFIX: str = "NV"

settings = Settings()

