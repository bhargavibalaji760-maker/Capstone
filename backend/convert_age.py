import pandas as pd
import os

files = [
    r'd:\bharg\Documents\Capstone\app\data\cleaned_patient_demographics.csv',
    r'd:\bharg\Documents\Capstone\app\data\patient_demographics.csv'
]

for file_path in files:
    if os.path.exists(file_path):
        print(f"Processing {file_path}...")
        df = pd.read_csv(file_path)
        if 'age' in df.columns:
            # Convert age to integer (rounding or truncating - typically clinical age is truncated or rounded to nearest)
            # Let's use round() and cast to int
            df['age'] = df['age'].round().astype(int)
            df.to_csv(file_path, index=False)
            print(f"Successfully converted 'age' in {file_path}")
        else:
            print(f"'age' column not found in {file_path}")
    else:
        print(f"File {file_path} does not exist")
