import pandas as pd
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the project root to sys.path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.core.config import settings
from app.db.models import Patient, Base

def load_patients():
    print("🐘 Starting Patient ETL process...")
    
    # Path to data (inside container or local)
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "data")
    demo_path = os.path.join(data_dir, "patient_demographics (1).csv")
    treat_path = os.path.join(data_dir, "patient_treatments (1).csv")
    
    if not os.path.exists(demo_path) or not os.path.exists(treat_path):
        print(f"❌ Error: CSV files not found in {data_dir}")
        return

    try:
        # Load CSVs
        print(f"📖 Reading {demo_path}...")
        df_demo = pd.read_csv(demo_path)
        print(f"📖 Reading {treat_path}...")
        df_treat = pd.read_csv(treat_path)
        
        # Merge on both subject_id and hadm_id
        print("🔗 Merging datasets...")
        df = pd.merge(df_demo, df_treat, on=["subject_id", "hadm_id"], how="left")
        
        # Initialize Database connection
        engine = create_engine(settings.SQLALCHEMY_DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        print(f"💾 Loading {len(df)} records into PostgreSQL...")
        
        count = 0
        for _, row in df.iterrows():
            # Check unique constraint (subject_id, hadm_id)
            subj_id = str(row['subject_id'])
            hadm_id = str(int(row['hadm_id'])) if pd.notnull(row['hadm_id']) else None
            
            existing = db.query(Patient).filter(
                Patient.subject_id == subj_id,
                Patient.hadm_id == hadm_id
            ).first()
            
            if not existing:
                patient = Patient(
                    subject_id=subj_id,
                    hadm_id=hadm_id,
                    gender=str(row['gender']),
                    age=int(float(row['age'])),
                    deceased=bool(row['deceased']) if 'deceased' in row else False,
                    medical_history=str(row.get('diagnosis', '')),
                    diagnoses=str(row.get('diagnosis', '')),
                    conditions=str(row.get('conditions', '')),
                    medications=str(row.get('medications', '')),
                    treatments=str(row.get('medications', ''))
                )
                db.add(patient)
                count += 1
            
            if count % 100 == 0 and count > 0:
                db.commit()
                print(f"✅ Committed {count} records...")

        db.commit()
        print(f"✨ Successfully loaded {count} NEW patient records.")
        db.close()
        
    except Exception as e:
        print(f"💥 ETL Error: {e}")

if __name__ == "__main__":
    load_patients()
