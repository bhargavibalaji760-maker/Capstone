"""
Data Loader Module - Load and process patient datasets
"""
import pandas as pd
import os
from pathlib import Path

def get_data_path():
    """Get the data folder path"""
    return Path(__file__).parent.parent / "data"

def load_patient_demographics():
    """Load patient demographics data from CSV"""
    # Priority 1: Cleaned data
    cleaned_path = get_data_path() / "cleaned_patient_demographics.csv"
    if cleaned_path.exists():
        return pd.read_csv(cleaned_path)
    
    # Priority 2: Original data
    path = get_data_path() / "patient_demographics.csv"
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame()

def load_patient_treatments():
    """Load patient treatments data from CSV"""
    # Priority 1: Cleaned data
    cleaned_path = get_data_path() / "cleaned_patient_treatments.csv"
    if cleaned_path.exists():
        return pd.read_csv(cleaned_path)
    
    # Priority 2: Original data
    path = get_data_path() / "patient_treatments.csv"
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame()

def get_patient_by_id(patient_id):
    """Get patient information by subject_id"""
    demos = load_patient_demographics()
    patient = demos[demos['subject_id'] == patient_id]
    
    if len(patient) > 0:
        return patient.iloc[0].to_dict()
    return None

def get_patient_conditions(patient_id):
    """Get patient conditions and medications"""
    treatments = load_patient_treatments()
    patient_treatments = treatments[treatments['subject_id'] == patient_id]
    
    if len(patient_treatments) > 0:
        return patient_treatments.iloc[0].to_dict()
    return None

def get_all_patients():
    """Get all patients from demographics"""
    return load_patient_demographics()

def get_conditions_for_trial(trial_inclusion_keywords, trial_exclusion_keywords):
    """Filter patients matching trial criteria"""
    demos = load_patient_demographics()
    treatments = load_patient_treatments()
    
    # Merge datasets
    merged = demos.merge(treatments, on=['subject_id', 'hadm_id'], how='left')
    
    # Filter by inclusion criteria
    if trial_inclusion_keywords:
        mask = merged['diagnosis'].str.contains('|'.join(trial_inclusion_keywords), case=False, na=False)
        merged = merged[mask]
    
    # Exclude by exclusion criteria
    if trial_exclusion_keywords:
        mask = ~merged['diagnosis'].str.contains('|'.join(trial_exclusion_keywords), case=False, na=False)
        merged = merged[mask]
    
    return merged
