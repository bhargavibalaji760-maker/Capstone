from fastapi import APIRouter, Depends, HTTPException, Query
import re
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import Patient, User
from app.routes.auth import get_current_user
from app.services.nlp_extractor import extractor
from typing import List, Optional

router = APIRouter()

@router.get("")
def get_patients(
    limit: int = Query(10, gt=0),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    query = db.query(Patient).order_by(Patient.id.desc())
    
    if search:
        # Search by subject_id (exact) or name (case-insensitive)
        query = query.filter(
            (Patient.subject_id == search) | 
            (Patient.name.ilike(f"%{search}%"))
        )
        # If searching, we likely want all matches, or a larger limit
        return query.all()
    
    return query.limit(limit).all()

from app.schemas.patient_schema import PatientCreate
from sqlalchemy.exc import IntegrityError

@router.post("")
def create_patient(
    data: PatientCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    # Convert Pydantic model to dict for processing
    patient_data = data.model_dump()
    
    # Enhanced Extraction: Pull medical entities from the history
    history = patient_data.get("medical_history", "")
    entities = extractor.extract_entities(history)
    
    # Improved heuristic for conditions vs medications
    drug_suffixes = r'.*(in|ol|am|an|id|ate|ine|one|ide|ole)$'
    
    conditions = [e for e in entities if not re.match(drug_suffixes, e.lower())]
    medications = [e for e in entities if re.match(drug_suffixes, e.lower())]
    
    patient_data["conditions"] = "|".join(conditions)
    patient_data["medications"] = "|".join(medications)
    
    try:
        patient = Patient(**patient_data)
        db.add(patient)
        db.commit()
        db.refresh(patient)
        return patient
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400, 
            detail=f"Patient with Subject ID {data.subject_id} and Admission ID {data.hadm_id} already exists."
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{id}")
def get_patient(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    patient = db.query(Patient).filter(Patient.id == id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient

@router.delete("/{id}")
def delete_patient(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    patient = db.query(Patient).filter(Patient.id == id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    db.delete(patient)
    db.commit()
    return {"message": "Patient deleted"}
