import os

class Settings:
    PROJECT_NAME: str = "ClinMatch AI"
    PROJECT_VERSION: str = "1.0.0"
    # Primary DB URL from environment, fall back to PostgreSQL (from docker-compose settings)
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://postgres:postgres@localhost:5432/clinical_trials"
    )


    
    # LLM Configuration
    HF_API_TOKEN: str = os.getenv("HF_API_TOKEN", "")
    USE_LLM: bool = os.getenv("USE_LLM", "false").lower() == "true"
    DEFAULT_MODEL: str = "mistralai/Mistral-7B-Instruct-v0.2"

settings = Settings()
