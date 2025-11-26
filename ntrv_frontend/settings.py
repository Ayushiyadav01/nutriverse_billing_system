import os
from typing import List

class Settings:
    # API settings
    API_BASE_URL: str = os.getenv("API_BASE_URL", "http://localhost:8000")
    API_V1_STR: str = os.getenv("API_V1_STR", "/api")
    API_URL: str = os.getenv("API_URL", f"{API_BASE_URL}{API_V1_STR}")
    
    # Frontend settings
    FRONTEND_HOST: str = os.getenv("FRONTEND_HOST", "0.0.0.0")
    FRONTEND_PORT: int = int(os.getenv("FRONTEND_PORT", "8501"))
    
    # File storage settings
    EXPENSE_ATTACHMENTS_DIR: str = os.getenv("EXPENSE_ATTACHMENTS_DIR", "data/expense_attachments")
    
    # App settings
    APP_TITLE: str = os.getenv("APP_TITLE", "Nutriverse - The Nurish House")
    APP_ICON: str = os.getenv("APP_ICON", "🥗")

settings = Settings()

