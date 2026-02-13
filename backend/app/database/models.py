from sqlalchemy import Column, Integer, String, Float, Text, Boolean
from app.database.db_connection import Base

class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    age = Column(Integer)
    gender = Column(String)
    primary_condition = Column(String)
    # Storing medical notes as raw text for NLP processing
    clinical_notes = Column(Text)

class Trial(Base):
    __tablename__ = "trials"
    id = Column(Integer, primary_key=True, index=True)
    nct_id = Column(String, unique=True, index=True) # e.g., NCT043525
    title = Column(String)
    inclusion_criteria = Column(Text)
    exclusion_criteria = Column(Text)
    phase = Column(String) # Phase 1, 2, 3, 4
    status = Column(String) # Recruiting, Active, Completed, Closed
    target_participants = Column(Integer)

class MatchResult(Base):
    __tablename__ = "matches"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer)
    trial_nct_id = Column(String)
    match_score = Column(Float) # 0 to 100
    reason = Column(Text) # Explanation from AI
    clinician_approval = Column(String, default="Pending") # Pending, Approve, Reject
