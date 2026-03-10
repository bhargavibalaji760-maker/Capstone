from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
import os

import time

# Try PostgreSQL with retries, fall back to SQLite
def _make_engine():
    pg_url = settings.SQLALCHEMY_DATABASE_URL
    retries = 5
    while retries > 0:
        try:
            engine = create_engine(
                pg_url, 
                pool_pre_ping=True, 
                connect_args={"connect_timeout": 5}
            )
            # Test connection
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("Successfully connected to PostgreSQL")
            return engine
        except Exception as e:
            retries -= 1
            if retries > 0:
                print(f"PostgreSQL not ready ({e}). Retrying in 2s... ({retries} attempts left)")
                time.sleep(2)
            else:
                print(f"PostgreSQL failed after 5 attempts. Falling back to local SQLite.")
                sqlite_path = os.path.join(os.path.dirname(__file__), "meditrial_clean.db")
                return create_engine(
                    f"sqlite:///{sqlite_path}",
                    connect_args={"check_same_thread": False}
                )

engine = _make_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
