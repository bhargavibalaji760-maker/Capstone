"""
CRUD Operations - Create, Read, Update, Delete database operations
"""
from sqlalchemy.orm import Session
from app.database import models

# PATIENT OPERATIONS

def create_patient(db: Session, patient_data: dict):
    """Create a new patient record"""
    db_patient = models.Patient(
        name=patient_data.get('name'),
        age=patient_data.get('age'),
        gender=patient_data.get('gender'),
        primary_condition=patient_data.get('primary_condition'),
        clinical_notes=patient_data.get('clinical_notes')
    )
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    return db_patient

def get_patient(db: Session, patient_id: int):
    """Get a patient by ID"""
    return db.query(models.Patient).filter(models.Patient.id == patient_id).first()

def get_all_patients(db: Session):
    """Get all patients"""
    return db.query(models.Patient).all()

def update_patient(db: Session, patient_id: int, patient_data: dict):
    """Update a patient record"""
    db_patient = get_patient(db, patient_id)
    if db_patient:
        for key, value in patient_data.items():
            setattr(db_patient, key, value)
        db.commit()
        db.refresh(db_patient)
    return db_patient

def delete_patient(db: Session, patient_id: int):
    """Delete a patient record"""
    db_patient = get_patient(db, patient_id)
    if db_patient:
        db.delete(db_patient)
        db.commit()
    return db_patient

# TRIAL OPERATIONS

def create_trial(db: Session, trial_data: dict):
    """Create a new trial record"""
    db_trial = models.Trial(
        nct_id=trial_data.get('nct_id'),
        title=trial_data.get('title'),
        inclusion_criteria=trial_data.get('inclusion_criteria'),
        exclusion_criteria=trial_data.get('exclusion_criteria'),
        phase=trial_data.get('phase'),
        status=trial_data.get('status'),
        target_participants=trial_data.get('target_participants')
    )
    db.add(db_trial)
    db.commit()
    db.refresh(db_trial)
    return db_trial

def get_trial(db: Session, trial_id: int):
    """Get a trial by ID"""
    return db.query(models.Trial).filter(models.Trial.id == trial_id).first()

def get_trial_by_nct(db: Session, nct_id: str):
    """Get a trial by NCT ID"""
    return db.query(models.Trial).filter(models.Trial.nct_id == nct_id).first()

def get_all_trials(db: Session):
    """Get all trials"""
    return db.query(models.Trial).all()

def update_trial(db: Session, trial_id: int, trial_data: dict):
    """Update a trial record"""
    db_trial = get_trial(db, trial_id)
    if db_trial:
        for key, value in trial_data.items():
            setattr(db_trial, key, value)
        db.commit()
        db.refresh(db_trial)
    return db_trial

# MATCH RESULT OPERATIONS

def create_match_result(db: Session, match_data: dict):
    """Create a new match result"""
    db_match = models.MatchResult(
        patient_id=match_data.get('patient_id'),
        trial_nct_id=match_data.get('trial_nct_id'),
        match_score=match_data.get('match_score'),
        reason=match_data.get('reason'),
        clinician_approval=match_data.get('clinician_approval', 'Pending')
    )
    db.add(db_match)
    db.commit()
    db.refresh(db_match)
    return db_match

def get_match_result(db: Session, match_id: int):
    """Get a match result by ID"""
    return db.query(models.MatchResult).filter(models.MatchResult.id == match_id).first()

def get_matches_for_patient(db: Session, patient_id: int):
    """Get all match results for a patient"""
    return db.query(models.MatchResult).filter(models.MatchResult.patient_id == patient_id).all()

def get_matches_for_trial(db: Session, trial_nct_id: str):
    """Get all match results for a trial"""
    return db.query(models.MatchResult).filter(models.MatchResult.trial_nct_id == trial_nct_id).all()

def get_all_match_results(db: Session):
    """Get all match results"""
    return db.query(models.MatchResult).all()

def update_match_result(db: Session, match_id: int, match_data: dict):
    """Update a match result"""
    db_match = get_match_result(db, match_id)
    if db_match:
        for key, value in match_data.items():
            setattr(db_match, key, value)
        db.commit()
        db.refresh(db_match)
    return db_match
