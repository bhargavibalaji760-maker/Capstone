"""
Database Initialization Script
This script populates the database with sample trials and enables quick testing
"""
import sys
from pathlib import Path
# Add project root to path so 'from app...' imports work
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy.orm import Session
from app.database import db_connection, models, crud

def init_sample_data():
    """Initialize database with sample trials"""
    
    # Create tables
    models.Base.metadata.create_all(bind=db_connection.engine)
    
    db = db_connection.SessionLocal()
    
    try:
        # Check if data already exists
        existing_trials = db.query(models.Trial).count()
        if existing_trials > 0:
            print(" Database already populated with trials")
            return
        
        # Sample trials
        trials = [
            {
                "nct_id": "NCT045521",
                "title": "Type 2 Diabetes Management Study",
                "inclusion_criteria": "Diabetes,Type 2,Age >= 18",
                "exclusion_criteria": "Pregnancy,Heart Failure",
                "phase": "Phase 3",
                "status": "Recruiting",
                "target_participants": 500
            },
            {
                "nct_id": "NCT045522",
                "title": "Hypertension Control Trial",
                "inclusion_criteria": "Hypertension,Adult",
                "exclusion_criteria": "Renal Disease,Stroke",
                "phase": "Phase 2",
                "status": "Active",
                "target_participants": 200
            },
            {
                "nct_id": "NCT045523",
                "title": "Heart Failure Management",
                "inclusion_criteria": "Heart Failure,Cardiac",
                "exclusion_criteria": "Pregnancy,Sepsis",
                "phase": "Phase 3",
                "status": "Completed",
                "target_participants": 350
            },
            {
                "nct_id": "NCT045524",
                "title": "Sepsis Prevention Study",
                "inclusion_criteria": "Adult,High Risk",
                "exclusion_criteria": "Immunosuppressed",
                "phase": "Phase 1",
                "status": "Recruiting",
                "target_participants": 50
            },
            {
                "nct_id": "NCT045525",
                "title": "Stroke Recovery Program",
                "inclusion_criteria": "Stroke,Recovery",
                "exclusion_criteria": "Active Infection",
                "phase": "Phase 4",
                "status": "Active",
                "target_participants": 1000
            }
        ]
        
        # Add trials to database
        for trial_data in trials:
            existing = db.query(models.Trial).filter(
                models.Trial.nct_id == trial_data['nct_id']
            ).first()
            
            if not existing:
                try:
                    crud.create_trial(db, trial_data)
                    print(f" Added trial: {trial_data['nct_id']} - {trial_data['title']}")
                except Exception as e:
                    print(f" Skipping {trial_data['nct_id']}: {e}")
        
        # Sample patients (from real data, but as DB records)
        patients = [
            {
                "name": "John Smith",
                "age": 45,
                "gender": "M",
                "primary_condition": "Type 2 Diabetes",
                "clinical_notes": "HbA1c 8.2%, controlled with metformin"
            },
            {
                "name": "Jane Doe",
                "age": 62,
                "gender": "F",
                "primary_condition": "Hypertension",
                "clinical_notes": "BP well controlled on lisinopril"
            },
            {
                "name": "Robert Johnson",
                "age": 58,
                "gender": "M",
                "primary_condition": "Heart Failure",
                "clinical_notes": "EF 35%, on standard HF therapy"
            },
            {
                "name": "Maria Garcia",
                "age": 52,
                "gender": "F",
                "primary_condition": "Sepsis",
                "clinical_notes": "Recovered from sepsis, rehabilitation phase"
            },
            {
                "name": "David Lee",
                "age": 71,
                "gender": "M",
                "primary_condition": "Stroke",
                "clinical_notes": "Ischemic stroke 2 months ago, recovering well"
            }
        ]
        
        # Add patients to database
        existing_patients = db.query(models.Patient).count()
        if existing_patients == 0:
            for patient_data in patients:
                crud.create_patient(db, patient_data)
                print(f" Added patient: {patient_data['name']}")
        
        print("\n Database initialization complete!")
        print(f"   Trials: {db.query(models.Trial).count()}")
        print(f"   Patients: {db.query(models.Patient).count()}")
        
    except Exception as e:
        print(f" Error initializing database: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("\n" + "="*50)
    print(" Initializing ClinMatch AI Database")
    print("="*50 + "\n")
    init_sample_data()
