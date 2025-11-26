import os
from pathlib import Path
from typing import Optional, List

class Settings:
    PROJECT_NAME: str = "Nutriverse API"
    PROJECT_VERSION: str = "0.1.0"
    
    # Server settings
    BACKEND_HOST: str = os.getenv("BACKEND_HOST", "0.0.0.0")
    BACKEND_PORT: int = int(os.getenv("BACKEND_PORT", "8000"))
    
    # Database settings
    SQLITE_DB_PATH: str = os.getenv("SQLITE_DB_PATH", "nutriverse.db")
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{SQLITE_DB_PATH}")
    
    # API settings
    API_V1_STR: str = os.getenv("API_V1_STR", "/api")
    
    # Tax and billing defaults
    DEFAULT_TAX_PERCENT: float = float(os.getenv("DEFAULT_TAX_PERCENT", "0.0"))
    
    # CORS settings - parse from env or use defaults
    _cors_origins_env = os.getenv("BACKEND_CORS_ORIGINS")
    if _cors_origins_env:
        BACKEND_CORS_ORIGINS: List[str] = [origin.strip() for origin in _cors_origins_env.split(",")]
    else:
        BACKEND_CORS_ORIGINS: List[str] = [
            "http://localhost:8501",  # Streamlit default
            "http://localhost:3000",  # For any other frontend
            "http://localhost",
            "http://localhost:8080",
        ]
    
    # Order number prefix
    ORDER_NUMBER_PREFIX: str = os.getenv("ORDER_NUMBER_PREFIX", "NV")
    
    # File storage settings
    EXPENSE_ATTACHMENTS_DIR: str = os.getenv("EXPENSE_ATTACHMENTS_DIR", "data/expense_attachments")

settings = Settings()

