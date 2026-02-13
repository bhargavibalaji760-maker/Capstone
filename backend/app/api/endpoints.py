"""
API Endpoints - All FastAPI routes
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.db_connection import get_db
from app.database import models, crud
from app.api import schemas
from app.services.nlp import text_processor
from app.services.matching import rules_engine, scorer
from app.utils import data_loader, formatters
from app.core import security

router = APIRouter()
# To apply security to all routes in this router:
# router = APIRouter(dependencies=[Depends(security.get_current_user)])

# ==================== PATIENT ENDPOINTS ====================

@router.post("/patients/", response_model=schemas.PatientResponse)
def create_patient(patient: schemas.PatientCreate, db: Session = Depends(get_db)):
    """Create a new patient record"""
    return crud.create_patient(db, patient.dict())

@router.get("/patients/{patient_id}", response_model=schemas.PatientResponse)
def read_patient(patient_id: int, db: Session = Depends(get_db)):
    """Get patient by ID"""
    db_patient = crud.get_patient(db, patient_id)
    if not db_patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return db_patient

@router.get("/patients/", response_model=list[schemas.PatientResponse])
def read_all_patients(db: Session = Depends(get_db)):
    """Get all patients"""
    return crud.get_all_patients(db)

@router.put("/patients/{patient_id}", response_model=schemas.PatientResponse)
def update_patient(patient_id: int, patient: schemas.PatientCreate, db: Session = Depends(get_db)):
    """Update a patient"""
    db_patient = crud.update_patient(db, patient_id, patient.dict())
    if not db_patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return db_patient

@router.delete("/patients/{patient_id}")
def delete_patient(patient_id: int, db: Session = Depends(get_db)):
    """Delete a patient"""
    db_patient = crud.delete_patient(db, patient_id)
    if not db_patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return {"message": "Patient deleted"}

# ==================== TRIAL ENDPOINTS ====================

@router.post("/trials/", response_model=schemas.TrialResponse)
def create_trial(trial: schemas.TrialCreate, db: Session = Depends(get_db)):
    """Create a new trial"""
    return crud.create_trial(db, trial.dict())

@router.get("/trials/{trial_id}", response_model=schemas.TrialResponse)
def read_trial(trial_id: int, db: Session = Depends(get_db)):
    """Get trial by ID"""
    db_trial = crud.get_trial(db, trial_id)
    if not db_trial:
        raise HTTPException(status_code=404, detail="Trial not found")
    return db_trial

@router.get("/trials/nct/{nct_id}", response_model=schemas.TrialResponse)
def read_trial_by_nct(nct_id: str, db: Session = Depends(get_db)):
    """Get trial by NCT ID"""
    db_trial = crud.get_trial_by_nct(db, nct_id)
    if not db_trial:
        raise HTTPException(status_code=404, detail="Trial not found")
    return db_trial

@router.get("/trials/", response_model=list[schemas.TrialResponse])
def read_all_trials(db: Session = Depends(get_db)):
    """Get all trials"""
    return crud.get_all_trials(db)

@router.put("/trials/{trial_id}", response_model=schemas.TrialResponse)
def update_trial(trial_id: int, trial: schemas.TrialCreate, db: Session = Depends(get_db)):
    """Update a trial"""
    db_trial = crud.update_trial(db, trial_id, trial.dict())
    if not db_trial:
        raise HTTPException(status_code=404, detail="Trial not found")
    return db_trial

# ==================== ANALYSIS ENDPOINTS ====================

@router.post("/analyze_protocol/", response_model=schemas.ProtocolAnalysisResponse)
def analyze_protocol(request: schemas.ProtocolAnalysisRequest):
    """Analyze trial protocol and extract criteria"""
    result = text_processor.parse_protocol(request.protocol_text)
    result['nct_id'] = request.trial_nct_id
    return result

@router.post("/run_screening/", response_model=schemas.ScreeningResponse)
def run_screening(
    request: schemas.ScreeningRequest, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(security.get_current_user)
):
    """Run patient-trial screening (Requires Authentication)"""
    # Get patient from database
    db_patient = crud.get_patient(db, request.patient_id)
    if not db_patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Get trial from database
    db_trial = crud.get_trial_by_nct(db, request.trial_nct_id)
    if not db_trial:
        raise HTTPException(status_code=404, detail="Trial not found")
    
    # Build trial rules from trial data
    trial_rules = {
        "inclusion_keywords": db_trial.inclusion_criteria.split(',') if db_trial.inclusion_criteria else [],
        "exclusion_keywords": db_trial.exclusion_criteria.split(',') if db_trial.exclusion_criteria else []
    }
    
    # Apply rules
    patient_data = {
        'age': db_patient.age,
        'gender': db_patient.gender,
        'diagnosis': db_patient.primary_condition
    }
    
    result = rules_engine.apply_rules(patient_data, trial_rules)
    
    # Store result in database
    match_record = {
        'patient_id': request.patient_id,
        'trial_nct_id': request.trial_nct_id,
        'match_score': result['score'],
        'reason': ' | '.join([f"{c['check']}: {c['message']}" for c in result['checks']]),
        'clinician_approval': 'Pending'
    }
    crud.create_match_result(db, match_record)
    
    return {
        "patient_id": request.patient_id,
        "trial_nct_id": request.trial_nct_id,
        "score": result['score'],
        "eligible": result['eligible'],
        "checks": result['checks'],
        "message": f"Passed {result['passed_checks']}/{result['total_checks']} checks"
    }

@router.get("/trials/nct/{nct_id}/candidates/", response_model=schemas.TrialCandidatesResponse)
def get_trial_candidates(
    nct_id: str, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(security.get_current_user)
):
    """Find and rank all suitable patients for a specific trial"""
    # 1. Get trial details
    db_trial = crud.get_trial_by_nct(db, nct_id)
    if not db_trial:
        raise HTTPException(status_code=404, detail="Trial not found")
    
    # 2. Get all patients
    patients = crud.get_all_patients(db)
    
    # 3. Build trial rules
    trial_rules = {
        "inclusion_keywords": [k.strip() for k in db_trial.inclusion_criteria.split(',')] if db_trial.inclusion_criteria else [],
        "exclusion_keywords": [k.strip() for k in db_trial.exclusion_criteria.split(',')] if db_trial.exclusion_criteria else []
    }
    
    candidates = []
    eligible_count = 0
    
    # 4. Process each patient
    for p in patients:
        patient_data = {
            'age': p.age,
            'gender': p.gender,
            'diagnosis': p.primary_condition
        }
        
        match_result = rules_engine.apply_rules(patient_data, trial_rules)
        
        # Determine Priority
        priority = "Low"
        if match_result['score'] >= 90:
            priority = "High"
        elif match_result['score'] >= 75:
            priority = "Medium"
            
        if match_result['eligible']:
            eligible_count += 1
            
        candidates.append({
            "patient_id": p.id,
            "patient_name": p.name,
            "age": p.age,
            "gender": p.gender,
            "diagnosis": p.primary_condition,
            "score": match_result['score'],
            "eligible": match_result['eligible'],
            "passed_checks": match_result['passed_checks'],
            "total_checks": match_result['total_checks'],
            "priority": priority,
            "checks": match_result['checks']
        })
    
    # 5. Rank candidates by score (descending)
    candidates.sort(key=lambda x: x['score'], reverse=True)
    
    return {
        "trial_nct_id": nct_id,
        "trial_title": db_trial.title,
        "total_patients_screened": len(patients),
        "eligible_count": eligible_count,
        "candidates": candidates
    }

# ==================== MATCH RESULT ENDPOINTS ====================

@router.get("/matches/", response_model=list[schemas.MatchResultResponse])
def read_all_matches(db: Session = Depends(get_db)):
    """Get all match results"""
    return crud.get_all_match_results(db)

@router.get("/matches/{match_id}", response_model=schemas.MatchResultResponse)
def read_match(match_id: int, db: Session = Depends(get_db)):
    """Get match result by ID"""
    db_match = crud.get_match_result(db, match_id)
    if not db_match:
        raise HTTPException(status_code=404, detail="Match result not found")
    return db_match

@router.get("/matches/patient/{patient_id}", response_model=list[schemas.MatchResultResponse])
def read_matches_for_patient(patient_id: int, db: Session = Depends(get_db)):
    """Get all matches for a patient"""
    return crud.get_matches_for_patient(db, patient_id)

@router.get("/matches/trial/{trial_nct_id}", response_model=list[schemas.MatchResultResponse])
def read_matches_for_trial(trial_nct_id: str, db: Session = Depends(get_db)):
    """Get all matches for a trial"""
    return crud.get_matches_for_trial(db, trial_nct_id)

@router.put("/matches/{match_id}", response_model=schemas.MatchResultResponse)
def update_match(match_id: int, match_update: schemas.MatchResultUpdate, db: Session = Depends(get_db)):
    """Update a match result (e.g., clinician approval)"""
    db_match = crud.update_match_result(db, match_id, match_update.dict(exclude_unset=True))
    if not db_match:
        raise HTTPException(status_code=404, detail="Match result not found")
    return db_match

# ==================== HEALTH CHECK ====================

@router.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "ClinMatch AI API is running"}
