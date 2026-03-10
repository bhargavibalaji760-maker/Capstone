import sys
import os

# Add the parent directory to sys.path to find 'app'
# Using absolute path to be sure
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(os.path.dirname(current_dir))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from app.db.session import engine, Base
from app.db.models import Patient, Trial, Match, User

def init_db():
    print(f"Initializing database at {engine.url}")
    # Drop all tables to ensure a clean start
    Base.metadata.drop_all(bind=engine)
    print("Dropped all tables.")
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("Created all tables.")

if __name__ == "__main__":
    init_db()
