import pandas as pd
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.db.models import Patient, Base, Match

def etl():
    print(" Starting Aggregated CSV to PostgreSQL ETL...")
    
    # Paths
    base_dir = "/app"
    demo_path = os.path.join(base_dir, "data", "patient_demographics (1).csv")
    treat_path = os.path.join(base_dir, "data", "patient_treatments (1).csv")
    
    if not os.path.exists(demo_path) or not os.path.exists(treat_path):
        print(f"Error: CSV files not found at {demo_path} or {treat_path}.")
        return

    try:
        print("Reading CSVs...")
        df_demo = pd.read_csv(demo_path)
        df_treat = pd.read_csv(treat_path)
        
        print(" Merging datasets...")
        # Merge on both subject_id and hadm_id for accuracy at admission level
        df = pd.merge(df_demo, df_treat, on=["subject_id", "hadm_id"], how="left")
        
        # FIX: Fill NaN values to avoid "nan" strings in DB
        df = df.fillna("")
        
        print(f"Total admission-level records to load: {len(df)}")
        
        # Database connection
        engine = create_engine(settings.SQLALCHEMY_DATABASE_URL)
        Base.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        print("Clearing existing patients and matches from PostgreSQL...")
        db.execute(text("TRUNCATE TABLE matches, patients RESTART IDENTITY CASCADE"))
        db.commit()
        
        print(f"Loading {len(df)} records into PostgreSQL...")
        
        patients = []
        count = 0
        success_count = 0
        
        for _, row in df.iterrows():
            # Robust extraction with fallback to empty string
            def get_val(col):
                val = row.get(col, "")
                if pd.isna(val) or val == "nan": return ""
                return str(val).strip()

            patient = Patient(
                subject_id=get_val('subject_id'),
                hadm_id=get_val('hadm_id') or None,
                gender=get_val('gender'),
                age=int(float(row['age'])) if row.get('age') and str(row['age']).replace('.','').isdigit() else 0,
                deceased=bool(row.get('deceased', False)),
                medical_history=get_val('diagnosis'),
                diagnoses=get_val('diagnosis'),
                conditions=get_val('conditions'),
                medications=get_val('medications'),
                treatments=get_val('medications')
            )
            patients.append(patient)
            count += 1
            
            if len(patients) >= 100:
                try:
                    db.add_all(patients)
                    db.commit()
                    success_count += len(patients)
                    print(f" Loaded {count} records...")
                    patients = []
                except Exception as e:
                    print(f" Batch failure at record {count}: {e}")
                    db.rollback()
                    # Fallback to one by one for this batch
                    for p in patients:
                        try:
                            db.add(p)
                            db.commit()
                            success_count += 1
                        except Exception as ie:
                            db.rollback()
                            print(f"  - Record {p.subject_id} failed: {ie}")
                    patients = []
        
        if patients:
            db.add_all(patients)
            db.commit()
            success_count += len(patients)
            
        print(f"\n Successfully loaded {success_count} unique patient records into PostgreSQL.")
        db.close()
        
    except Exception as e:
        print(f" ETL Global Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    etl()
