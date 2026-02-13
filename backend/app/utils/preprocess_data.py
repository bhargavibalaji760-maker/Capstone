"""
Data Preprocessing Script - Clean and standardize medical datasets
"""
import pandas as pd
import os
from pathlib import Path

def preprocess_medical_data():
    # Define paths relative to script
    base_path = Path(__file__).parent.parent / "data"
    save_path = base_path
    
    # Files to process
    demographics_file = base_path / "patient_demographics.csv"
    treatments_file = base_path / "patient_treatments.csv"
    
    print("Starting Data Preprocessing...")
    
    # 1. Process Demographics
    if demographics_file.exists():
        df_demos = pd.read_csv(demographics_file)
        print(f"Processing demographics ({len(df_demos)} records)...")
        
        # Clean diagnosis text
        df_demos['diagnosis'] = df_demos['diagnosis'].str.strip().str.upper()
        
        # Handle age outliers (MIMIC standard: ages > 89 are often de-identified as large values like 300)
        # We'll normalize these to 90 for this decision support system
        df_demos.loc[df_demos['age'] > 89, 'age'] = 90.0
        
        # Standardize common acronyms in diagnosis
        acronyms = {
            "MI": "MYOCARDIAL INFARCTION",
            "CAD": "CORONARY ARTERY DISEASE",
            "CHF": "CONGESTIVE HEART FAILURE",
            "COPD": "CHRONIC OBSTRUCTIVE PULMONARY DISEASE",
            "UTI": "URINARY TRACT INFECTION",
            "AKI": "ACUTE KIDNEY INJURY",
            "CVA": "CEREBROVASCULAR ACCIDENT"
        }
        
        for short, full in acronyms.items():
            # Match whole words or terms separated by delimiters
            df_demos['diagnosis'] = df_demos['diagnosis'].str.replace(rf'\b{short}\b', full, regex=True)
        
        # Save cleaned demographics
        cleaned_demos_path = save_path / "cleaned_patient_demographics.csv"
        df_demos.to_csv(cleaned_demos_path, index=False)
        print(f"Saved cleaned demographics to {cleaned_demos_path}")
    else:
        print(f"Demographics file not found at {demographics_file}")

    # 2. Process Treatments
    if treatments_file.exists():
        df_treatments = pd.read_csv(treatments_file)
        print(f"Processing treatments ({len(df_treatments)} records)...")
        
        # Clean strings and handle missing values
        df_treatments['conditions'] = df_treatments['conditions'].astype(str).str.strip().str.upper()
        df_treatments['medications'] = df_treatments['medications'].astype(str).str.strip().str.upper()
        
        # Remove 'nan' strings
        df_treatments.replace('NAN', '', inplace=True)
        
        # Save cleaned treatments
        cleaned_treatments_path = save_path / "cleaned_patient_treatments.csv"
        df_treatments.to_csv(cleaned_treatments_path, index=False)
        print(f"Saved cleaned treatments to {cleaned_treatments_path}")
    else:
        print(f"Treatments file not found at {treatments_file}")

    print("Preprocessing Complete!")

if __name__ == "__main__":
    preprocess_medical_data()
