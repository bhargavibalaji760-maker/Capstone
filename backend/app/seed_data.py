import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import Patient, User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def seed():
    db = SessionLocal()
    try:
        # 1. Create Default Admin if not exists
        admin = db.query(User).filter(User.email == "admin@meditrial.ai").first()
        if not admin:
            admin = User(
                name="Clinical Admin",
                email="admin@meditrial.ai",
                hashed_password=pwd_context.hash("admin123"),
                is_admin=True
            )
            db.add(admin)
            print("Created admin user")

        # 2. Add Test Patients
        if db.query(Patient).count() == 0:
            patients = [
                Patient(
                    subject_id="SUB-001",
                    name="Sarah Johnson",
                    age=34,
                    gender="Female",
                    medical_history="Multiple Sclerosis (Relapsing-Remitting) since 2018. Previously treated with Glatiramer acetate. No history of malignancy.",
                    conditions="Multiple Sclerosis|Relapsing-Remitting MS",
                    medications="Glatiramer acetate|Vitamin D",
                    diagnoses="ICD-10: G35",
                    treatments="DMT|Injectables"
                ),
                Patient(
                    subject_id="SUB-002",
                    name="Michael Chen",
                    age=45,
                    gender="Male",
                    medical_history="Secondary Progressive Multiple Sclerosis diagnosed 2 years ago. Stable on current therapy. No confirmed relapses in last 6 months.",
                    conditions="Multiple Sclerosis|SPMS",
                    medications="Interferon beta-1a",
                    diagnoses="ICD-10: G35",
                    treatments="DMT|Oral"
                ),
                Patient(
                    subject_id="SUB-003",
                    name="Elena Rodriguez",
                    age=28,
                    gender="Female",
                    medical_history="Newly diagnosed MS. Candidate for first-line DMT. Currently pregnant (24 weeks).",
                    conditions="Multiple Sclerosis|Recently Diagnosed",
                    medications="None",
                    diagnoses="ICD-10: G35",
                    treatments="None"
                )
            ]
            db.add_all(patients)
            print(f"Seeded {len(patients)} test patients")
        
        db.commit()
        print("Success: Database seeded.")
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed()
