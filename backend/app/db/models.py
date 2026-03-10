from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, DateTime, Boolean, UniqueConstraint, JSON
from sqlalchemy.orm import relationship
from app.db.session import Base
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime

# Cross-dialect JSON type: uses JSONB on PG, standard JSON on others (SQLite)
JSON_TYPE = JSON().with_variant(JSONB(), "postgresql")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)  # stored as `name` in DB
    email = Column(String, unique=True, index=True)
    hashed_password = Column(Text)  # Text has no length limit - avoids bcrypt hash truncation
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)

    @property
    def full_name(self):
        """Alias for compatibility with API responses expecting full_name."""
        return self.name

class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(String, index=True) # Removed unique=True to allow multiple admissions
    hadm_id = Column(String, index=True, nullable=True)
    
    __table_args__ = (
        UniqueConstraint('subject_id', 'hadm_id', name='_subject_hadm_uc'),
    )
    name = Column(String, nullable=True)
    age = Column(Integer)
    gender = Column(String)
    medical_history = Column(Text, nullable=True)
    diagnoses = Column(Text, nullable=True)
    treatments = Column(Text, nullable=True)
    conditions = Column(Text, nullable=True) # Normalized conditions string
    medications = Column(Text, nullable=True) # Normalized medications string
    deceased = Column(Boolean, default=False)

class Trial(Base):
    __tablename__ = "trials"
    id = Column(Integer, primary_key=True, index=True)
    trial_id = Column(String, unique=True, index=True, nullable=True)
    title = Column(String, index=True)
    drug = Column(String, nullable=True)
    condition = Column(String, index=True)
    description = Column(Text, nullable=True)
    inclusion = Column(JSON_TYPE, nullable=True)
    exclusion = Column(JSON_TYPE, nullable=True)
    inclusion_criteria = Column(Text, nullable=True) # Backward compatibility
    exclusion_criteria = Column(Text, nullable=True) # Backward compatibility
    min_age = Column(Integer, nullable=True)
    max_age = Column(Integer, nullable=True)
    gender = Column(String, nullable=True, default="All")
    phase = Column(String, nullable=True)
    status = Column(String, nullable=True)

class Match(Base):
    __tablename__ = "matches"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    trial_id = Column(Integer, ForeignKey("trials.id"))
    score = Column(Float)
    fairness_score = Column(Float, default=100.0)
    explanation = Column(JSON_TYPE, nullable=True) # Rich structural explanation
    status = Column(String, default="pending") # pending, reviewed, accepted, rejected
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient")
    trial = relationship("Trial")
