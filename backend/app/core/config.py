import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "MediTrial AI"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-super-secret-key-12345")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # PostgreSQL (Primary storage for Patients, Trials, Matches)
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "meditrial_db")
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    
    # LLM Settings
    HF_API_TOKEN: Optional[str] = os.getenv("HF_API_TOKEN", "")
    USE_LLM: bool = os.getenv("USE_LLM", "false").lower() == "true"
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "mistralai/Mistral-7B-Instruct-v0.3")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_HOST") or os.getenv("OLLAMA_BASE_URL") or "http://localhost:11434"

    @property
    def SQLALCHEMY_DATABASE_URL(self) -> str:
        # Check if running in Docker (usually 'db' host)
        host = self.POSTGRES_SERVER
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{host}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }

def ensure_default_admin():
    """
    Placeholder for system initialization logic.
    """
    print("System initialization: Verifying administrative governance...")
    pass

settings = Settings()
