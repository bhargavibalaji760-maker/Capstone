from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import Trial, User
from app.routes.auth import get_current_user
from app.services.pdf_service import pdf_service
from app.services.trial_parser import parse_trial_with_llama
from typing import List, Optional
import shutil
import os

router = APIRouter()

@router.get("")
def get_trials(
    limit: int = Query(10, gt=0),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    query = db.query(Trial).order_by(Trial.id.desc())
    
    if search:
        # Search by ID or Title
        if search.isdigit():
            query = query.filter(Trial.id == int(search))
        else:
            query = query.filter(Trial.title.ilike(f"%{search}%"))
        return query.all()
        
    return query.limit(limit).all()

@router.post("")
def create_trial(data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    trial = Trial(**data)
    db.add(trial)
    db.commit()
    db.refresh(trial)
    return trial

@router.post("/upload-protocol")
async def upload_protocol(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    path = f"/tmp/{file.filename}"

    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        extraction = pdf_service.extract_criteria(path)

        smart = await parse_trial_with_llama(
            extraction["inclusion"],
            extraction["exclusion"]
        )

        # Resolve final inclusion/exclusion text — LLM structured list preferred, raw PDF fallback
        inc_list = smart.get("inclusion_criteria", [])
        exc_list = smart.get("exclusion_criteria", [])
        inc_text = "\n".join(inc_list) if inc_list else extraction["inclusion"]
        exc_text = "\n".join(exc_list) if exc_list else extraction["exclusion"]

        # Populate BOTH the JSONB array field AND the legacy Text field so every
        # part of the matching pipeline (which reads one or the other) finds data.
        trial = Trial(
            title=file.filename.replace(".pdf", ""),
            inclusion=inc_list if inc_list else None,        # JSONB — used by scoring_service
            exclusion=exc_list if exc_list else None,        # JSONB — used by scoring_service
            inclusion_criteria=inc_text,                     # Text  — legacy + fallback
            exclusion_criteria=exc_text,                     # Text  — legacy + fallback
            min_age=smart.get("min_age") or 18,
            max_age=smart.get("max_age") or 80,
            gender=smart.get("gender", "All"),
            condition=smart.get("target_condition", "") or "",
            drug=smart.get("drug_name", "") or "",
            description=smart.get("drug_description", "") or "",
            status="Recruiting"
        )

        db.add(trial)
        db.commit()
        db.refresh(trial)

        return {
            "message": "Trial created",
            "trial_id": trial.id,
            "title": trial.title,
            "condition": trial.condition,
            "min_age": trial.min_age,
            "max_age": trial.max_age,
            "inclusion": trial.inclusion_criteria,
            "exclusion": trial.exclusion_criteria,
            "inclusion_list": trial.inclusion,
            "exclusion_list": trial.exclusion,
            "drug": trial.drug,
            "description": smart.get("drug_description", "")
        }
    finally:
        if os.path.exists(path):
            os.remove(path)


@router.get("/{id}")
def get_trial(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    trial = db.query(Trial).filter(Trial.id == id).first()
    if not trial:
        raise HTTPException(status_code=404, detail="Trial not found")
    return trial

@router.delete("/{id}")
def delete_trial(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    trial = db.query(Trial).filter(Trial.id == id).first()
    if not trial:
        raise HTTPException(status_code=404, detail="Trial not found")
    db.delete(trial)
    db.commit()
    return {"message": "Trial deleted"}

