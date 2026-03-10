from pydantic import BaseModel
from typing import Optional

class TrialBase(BaseModel):
    trial_id: Optional[str] = None
    title: str
    condition: str
    description: Optional[str] = None
    inclusion_criteria: Optional[str] = None
    exclusion_criteria: Optional[str] = None
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    gender: Optional[str] = None
    phase: Optional[str] = None
    status: Optional[str] = "Recruiting"

class TrialCreate(TrialBase):
    pass

class TrialResponse(TrialBase):
    id: int
    class Config:
        from_attributes = True
