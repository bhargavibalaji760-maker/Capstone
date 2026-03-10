from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import Patient, Trial, Match, User
from app.services.scoring_service import scoring_service, ScoringService
from app.services.pdf_service import pdf_service
from app.services.spacy_service import spacy_service
from app.services.evaluation import evaluate_system_performance
from app.routes.auth import get_current_user
from app.schemas.matching_schema import RawMatchRequest
from app.services.trial_parser import parse_trial_with_llama
import shutil
import os
import warnings
import pandas as pd
import asyncio
from app.services.nlp_extractor import extractor

# Silence sklearn's F1 warning when there are zero positive predictions
warnings.filterwarnings(
    "ignore",
    message="F-score is ill-defined",
    category=UserWarning,
    module="sklearn"
)

router = APIRouter()

# Protocol extraction has been restored here to match existing frontend flow
@router.post("/extract-criteria")
async def extract_protocol_criteria(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    temp_path = f"temp_{file.filename}"

    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        extraction = pdf_service.extract_criteria(temp_path)

        smart = await parse_trial_with_llama(
            extraction["inclusion"],
            extraction["exclusion"]
        )

        # Resolve final text — prefer LLM structured list, fall back to raw extraction
        inc_list = smart.get("inclusion_criteria", [])
        exc_list = smart.get("exclusion_criteria", [])
        inc_text = "\n".join(inc_list) if inc_list else extraction["inclusion"]
        exc_text = "\n".join(exc_list) if exc_list else extraction["exclusion"]

        # Populate BOTH JSONB array columns AND legacy Text columns
        trial = Trial(
            title=file.filename.replace(".pdf", ""),
            inclusion=inc_list if inc_list else None,
            exclusion=exc_list if exc_list else None,
            inclusion_criteria=inc_text,
            exclusion_criteria=exc_text,
            min_age=smart.get("min_age") or 18,
            max_age=smart.get("max_age") or 80,
            gender=smart.get("gender") or "All",
            condition=smart.get("target_condition") or "Unknown",
            drug=smart.get("drug_name") or "",
            description=smart.get("drug_description") or "",
            status="Recruiting"
        )

        db.add(trial)
        db.commit()
        db.refresh(trial)

        return {
            "success": True,
            "trial_id": trial.id,
            "trial_name": trial.title,
            "drug": trial.drug,
            "description": trial.description,
            "inclusion": trial.inclusion_criteria,
            "exclusion": trial.exclusion_criteria,
            "inclusion_list": trial.inclusion,
            "exclusion_list": trial.exclusion
        }

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


# =====================================================
# MATCH SINGLE PATIENT (FAST ONLY)
# =====================================================
@router.post("/match-patient/{patient_id}")
def match_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    trials = db.query(Trial).all()
    results = []

    for trial in trials:
        match_data = scoring_service.calculate_fast_score(patient, trial)

        db_match = db.query(Match).filter(
            Match.patient_id == patient_id,
            Match.trial_id == trial.id
        ).first()

        if not db_match:
            db_match = Match(patient_id=patient_id, trial_id=trial.id)
            db.add(db_match)

        db_match.score = match_data["score"]
        db_match.explanation = match_data["explanation"]

        results.append({
            "trial_id": trial.id,
            "trial_title": trial.title,
            "score": match_data["score"],
            "explanation": match_data["explanation"]
        })

    db.commit()
    return results


# =====================================================
# MATCH ALL PATIENTS AGAINST RAW PROTOCOL
# =====================================================
@router.post("/match-all-patients-raw")
async def match_all_patients_raw(
    request: RawMatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    import time
    start_time = time.time()
    patients = db.query(Patient).all()

    if request.trial_id:
        trial = db.query(Trial).filter(Trial.id == request.trial_id).first()
        if not trial:
            raise HTTPException(status_code=404, detail="Trial not found")
    else:
        # Fallback to mock trial if raw criteria provided
        class MockTrial:
            def __init__(self, inc, exc, min_a, max_a, cond):
                self.title = "Raw Criteria Request"
                self.condition = cond or ""
                self.inclusion = inc
                self.exclusion = exc
                self.inclusion_criteria = inc
                self.exclusion_criteria = exc
                self.min_age = min_a
                self.max_age = max_a
                self.gender = "All"

        trial = MockTrial(
            request.inclusion_criteria,
            request.exclusion_criteria,
            request.min_age,
            request.max_age,
            request.target_condition
        )

    patient_map = {p.id: p for p in patients}
    print(f"DEBUG: Processing match for '{getattr(trial, 'title', 'Unknown')}' with {len(patients)} patients")
    
    # 1. Build normalized patient texts (SMART CACHED BATCH)
    norm_start = time.time()
    normalized_texts = extractor.normalize_batch(patients)
    print(f"DEBUG: Batch normalization took {time.time() - norm_start:.2f}s")
    
    # 2. Pre-parse trial criteria ONCE using entity extraction with abbreviation expansion
    trial_condition = getattr(trial, 'condition', '') or ''
    
    inc_raw = getattr(trial, 'inclusion', '') or getattr(trial, 'inclusion_criteria', '')
    exc_raw = getattr(trial, 'exclusion', '') or getattr(trial, 'exclusion_criteria', '')
    
    inclusion_terms = ScoringService._extract_keywords(inc_raw, trial_condition)
    exclusion_terms = ScoringService._extract_keywords(exc_raw)


    # 3. Fast matching with pre-normalized data and parsed terms
    scoring_start = time.time()
    patient_data = []
    for i, p in enumerate(patients):
        norm_text = normalized_texts[i]
        fast = scoring_service.calculate_fast_score(
            p, 
            trial, 
            norm_text,
            inclusion_terms,
            exclusion_terms
        )
        
        patient_data.append({
            "patient": p,
            "norm_text": norm_text,
            "result_dict": {
                "patient_id": p.id,
                "patient_name": p.name or f"Patient {p.subject_id}",
                "age": p.age,
                "gender": p.gender,
                "score": fast["score"],
                "explanation": {
                    "summary": fast["explanation"]["clinical_match"][0] if fast["explanation"]["clinical_match"] else (fast["explanation"]["hard_constraints"][0] if fast["explanation"]["hard_constraints"] else "Initial scan completed."),
                    "narrative": " | ".join(fast["explanation"]["hard_constraints"] + fast["explanation"]["clinical_match"])
                },
                "ai_audited": False
            }
        })
    print(f"DEBUG: Fast scoring took {time.time() - scoring_start:.2f}s")

    # 4. Sort and pick top 10 with non-zero scores
    patient_data.sort(key=lambda x: x["result_dict"]["score"], reverse=True)
    results = [item["result_dict"] for item in patient_data]
    top_candidates = [c for c in patient_data[:10] if c["result_dict"]["score"] > 50]

    # 5. PARALLEL LLM audit (Semaphore tuned to Ollama capacity)
    if top_candidates:
        audit_start = time.time()
        sem = asyncio.Semaphore(8)

        async def audit_worker(candidate):
            async with sem:
                full_match = await scoring_service.calculate_match(
                    candidate["patient"], 
                    trial, 
                    candidate["norm_text"],
                    inclusion_terms,
                    exclusion_terms
                )
                candidate["result_dict"].update({
                    "score": full_match["score"],
                    "explanation": {
                        "summary": full_match["explanation"]["clinical_match"][0] if full_match["explanation"]["clinical_match"] else "AI Audit complete.",
                        "narrative": full_match["explanation"]["ai_reasoning"][0] if full_match["explanation"]["ai_reasoning"] else "Clinical profile aligns with trial requirements."
                    },
                    "ai_audited": full_match.get("ai_audited", False)
                })

        await asyncio.gather(*(audit_worker(c) for c in top_candidates))
        print(f"DEBUG: LLM audits took {time.time() - audit_start:.2f}s")
    else:
        print("DEBUG: Skipping LLM audits (no viable candidates)")

    df = pd.DataFrame([{
        "id": r["patient_id"],
        "gender": patient_map[r["patient_id"]].gender,
        "status": "accepted" if r["score"] >= 85 else "pending",
        "score": r["score"]
    } for r in results])

    metrics = evaluate_system_performance(df)
    print(f"DEBUG: Total match request duration: {time.time() - start_time:.2f}s")

    return {
        "results": results,
        "metrics": metrics,
        "ai_audit_count": len(top_candidates),
        "trial_metadata": {
            "drug": getattr(trial, 'drug', ''),
            "condition": getattr(trial, 'condition', '')
        }
    }


@router.post("/run/{trial_id}")
async def run_matching(
    trial_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    import time
    start_time = time.time()
    
    trial = db.query(Trial).filter(Trial.id == trial_id).first()
    if not trial:
        raise HTTPException(status_code=404, detail="Trial not found")

    patients = db.query(Patient).all()
    patient_map = {p.id: p for p in patients}
    
    print(f"DEBUG: Starting matching for trial '{trial.title}' against {len(patients)} patients")

    # 1. Build normalized patient texts (SMART CACHED BATCH)
    norm_start = time.time()
    normalized_texts = extractor.normalize_batch(patients)
    print(f"DEBUG: Batch normalization took {time.time() - norm_start:.2f}s")
    
    # 2. Pre-parse trial criteria ONCE using entity extraction with abbreviation expansion
    trial_condition = getattr(trial, 'condition', '') or ''
    
    inc_raw = getattr(trial, 'inclusion', '') or getattr(trial, 'inclusion_criteria', '')
    exc_raw = getattr(trial, 'exclusion', '') or getattr(trial, 'exclusion_criteria', '')
    
    inclusion_terms = ScoringService._extract_keywords(inc_raw, trial_condition)
    exclusion_terms = ScoringService._extract_keywords(exc_raw)


    # 3. Fast matching with pre-normalized data and parsed terms
    scoring_start = time.time()
    patient_data = []
    for i, p in enumerate(patients):
        norm_text = normalized_texts[i]
        fast = scoring_service.calculate_fast_score(
            p, 
            trial, 
            norm_text,
            inclusion_terms,
            exclusion_terms
        )
        
        patient_data.append({
            "patient": p,
            "norm_text": norm_text,
            "result_dict": {
                "patient_id": p.id,
                "patient_name": p.name or f"Patient {p.subject_id}",
                "age": p.age,
                "gender": p.gender,
                "score": fast["score"],
                "explanation": {
                    "summary": fast["explanation"]["clinical_match"][0] if fast["explanation"]["clinical_match"] else "Rule-based alignment completed.",
                    "narrative": " | ".join(fast["explanation"]["hard_constraints"] + fast["explanation"]["clinical_match"])
                },
                "ai_audited": False
            }
        })
    print(f"DEBUG: Fast scoring took {time.time() - scoring_start:.2f}s")

    # 4. Sort and take top 10 with non-zero scores
    patient_data.sort(key=lambda x: x["result_dict"]["score"], reverse=True)
    results = [item["result_dict"] for item in patient_data]
    top_candidates = [c for c in patient_data[:10] if c["result_dict"]["score"] > 50]
    print(f"DEBUG[run]: top5 scores = {[(c['result_dict']['patient_name'], c['result_dict']['score']) for c in patient_data[:5]]}")

    # 5. PARALLEL LLM audit (Semaphore tuned to Ollama capacity)
    if top_candidates:
        audit_start = time.time()
        sem = asyncio.Semaphore(8)

        async def audit_worker(candidate):
            async with sem:
                full_match = await scoring_service.calculate_match(
                    candidate["patient"], 
                    trial, 
                    candidate["norm_text"],
                    inclusion_terms,
                    exclusion_terms
                )
                candidate["result_dict"].update({
                    "score": full_match["score"],
                    "explanation": {
                        "summary": full_match["explanation"]["clinical_match"][0] if full_match["explanation"]["clinical_match"] else "Deep clinical audit performed.",
                        "narrative": full_match["explanation"]["ai_reasoning"][0] if full_match["explanation"]["ai_reasoning"] else "No specific contraindications found."
                    },
                    "ai_audited": full_match.get("ai_audited", False)
                })

        await asyncio.gather(*(audit_worker(c) for c in top_candidates))
        print(f"DEBUG: LLM audits took {time.time() - audit_start:.2f}s")
    else:
        print("DEBUG: Skipping LLM audits (no viable candidates)")

    df = pd.DataFrame([{
        "id": r["patient_id"],
        "gender": patient_map[r["patient_id"]].gender,
        "status": "accepted" if r["score"] >= 85 else "pending",
        "score": r["score"]
    } for r in results])

    metrics = evaluate_system_performance(df)
    print(f"DEBUG: Total match request duration: {time.time() - start_time:.2f}s")

    return {
        "results": results,
        "metrics": metrics,
        "ai_audit_count": len(top_candidates),
        "theory": "Zero candidates met the minimum clinical relevance standard." if not top_candidates else None
    }


# =====================================================
# UPDATE MATCH STATUS
# =====================================================
@router.put("/update-match-status/{patient_id}/{trial_id}")
def update_match_status(
    patient_id: int,
    trial_id: int,
    status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify both exist before proceeding
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    trial = db.query(Trial).filter(Trial.id == trial_id).first()
    
    if not patient or not trial:
        raise HTTPException(status_code=404, detail="Patient or Trial not found")

    match = db.query(Match).filter(
        Match.patient_id == patient_id,
        Match.trial_id == trial_id
    ).first()

    if not match:
        # Create the match record on the fly if it doesn't exist
        match = Match(
            patient_id=patient_id,
            trial_id=trial_id,
            score=0.0, 
            status=status
        )
        db.add(match)
    else:
        match.status = status
    
    db.commit()

    return {"message": "Updated"}


@router.get("/results/{patient_id}")
def get_results(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    matches = db.query(Match).filter(Match.patient_id == patient_id).all()

    return [{
        "trial_id": m.trial_id,
        "trial_title": m.trial.title,
        "score": m.score,
        "status": m.status,
        "explanation": m.explanation
    } for m in matches]