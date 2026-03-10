from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import Patient, Trial, Match, User
from app.routes.auth import get_current_user
from sqlalchemy import func

router = APIRouter()

@router.get("/stats")
def get_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    total_patients = db.query(Patient).count()
    total_trials = db.query(Trial).count()
    total_matches = db.query(Match).count()
    
    avg_score = db.query(func.avg(Match.score)).scalar() or 0.0
    
    return {
        "total_patients": total_patients,
        "total_trials": total_trials,
        "total_matches": total_matches,
        "avg_match_score": round(float(avg_score), 2)
    }
