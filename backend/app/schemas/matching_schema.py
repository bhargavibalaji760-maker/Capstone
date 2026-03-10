from pydantic import BaseModel
from typing import Optional, List

class RawMatchRequest(BaseModel):
    inclusion_criteria: Optional[str] = None
    exclusion_criteria: Optional[str] = None
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    trial_id: Optional[int] = None
    target_condition: Optional[str] = None

class BulkMatchResponse(BaseModel):
    patient_id: int
    patient_name: str
    score: float
    explanation: str
    fairness_alert: bool
    fairness_score: float
