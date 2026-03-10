from pydantic import BaseModel
from typing import Optional

class PatientBase(BaseModel):
    subject_id: str
    hadm_id: Optional[str] = None
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    medical_history: Optional[str] = None

class PatientCreate(PatientBase):
    pass

class PatientUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    medical_history: Optional[str] = None

class PatientResponse(PatientBase):
    id: int
    class Config:
        from_attributes = True
