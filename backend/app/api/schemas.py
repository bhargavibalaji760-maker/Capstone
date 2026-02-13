"""
Pydantic schemas for API request/response validation
"""
from pydantic import BaseModel
from typing import Optional, List

# PATIENT SCHEMAS

class PatientBase(BaseModel):
    name: str
    age: int
    gender: str
    primary_condition: str
    clinical_notes: Optional[str] = None

class PatientCreate(PatientBase):
    pass

class PatientResponse(PatientBase):
    id: int
    
    class Config:
        from_attributes = True

# TRIAL SCHEMAS

class TrialBase(BaseModel):
    nct_id: str
    title: str
    inclusion_criteria: str
    exclusion_criteria: str

class TrialCreate(TrialBase):
    pass

class TrialResponse(TrialBase):
    id: int
    
    class Config:
        from_attributes = True

# MATCH RESULT SCHEMAS

class MatchResultBase(BaseModel):
    patient_id: int
    trial_nct_id: str
    match_score: float
    reason: str
    clinician_approval: Optional[str] = "Pending"

class MatchResultCreate(MatchResultBase):
    pass

class MatchResultResponse(MatchResultBase):
    id: int
    
    class Config:
        from_attributes = True

class MatchResultUpdate(BaseModel):
    clinician_approval: Optional[str] = None
    match_score: Optional[float] = None
    reason: Optional[str] = None

# ANALYSIS SCHEMAS

class ProtocolAnalysisRequest(BaseModel):
    protocol_text: str
    trial_nct_id: Optional[str] = None

class ProtocolAnalysisResponse(BaseModel):
    nct_id: Optional[str]
    inclusion_keywords: List[str]
    exclusion_keywords: List[str]
    min_age: Optional[int] = None
    max_age: Optional[int] = None

class ScreeningRequest(BaseModel):
    patient_id: int
    trial_nct_id: str

class ScreeningResponse(BaseModel):
    patient_id: int
    trial_nct_id: str
    score: float
    eligible: bool
    checks: List[dict]
    message: str

class CandidateMatchMetric(BaseModel):
    patient_id: int
    patient_name: str
    age: int
    gender: str
    diagnosis: str
    score: float
    eligible: bool
    passed_checks: int
    total_checks: int
    priority: str  # High, Medium, Low
    checks: List[dict]

class TrialCandidatesResponse(BaseModel):
    trial_nct_id: str
    trial_title: str
    total_patients_screened: int
    eligible_count: int
    candidates: List[CandidateMatchMetric]
