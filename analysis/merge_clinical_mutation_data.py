#!/usr/bin/env python3
"""
Script to merge Clinical.txt and Mutation.txt files based on PATIENT_ID
"""

import pandas as pd
import re
from pathlib import Path

def extract_patient_id_from_barcode(barcode):
    """
    Extract PATIENT_ID from Tumor_Sample_Barcode
    Example: 'C3L-04475-02' -> 'C3L-04475'
    """
    if pd.isna(barcode) or barcode == '':
        return None
    # Remove the last part after the last dash (e.g., '-02')
    parts = str(barcode).split('-')
    if len(parts) >= 3:
        # Rejoin first two parts (e.g., 'C3L-04475')
        return '-'.join(parts[:2])
    return str(barcode)

def read_clinical_data(file_path):
    """Read Clinical.txt file, skipping header lines"""
    print(f"Reading clinical data from {file_path}...")
    
    # Read the file line by line to find the header
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find the header row (starts with PATIENT_ID)
    header_idx = None
    for i, line in enumerate(lines):
        if line.startswith('PATIENT_ID'):
            header_idx = i
            break
    
    if header_idx is None:
        raise ValueError("Could not find PATIENT_ID header in Clinical.txt")
    
    # Read the data starting from the header row
    clinical_df = pd.read_csv(file_path, sep='\t', skiprows=header_idx, encoding='utf-8')
    
    # Clean column names (remove leading/trailing whitespace)
    clinical_df.columns = clinical_df.columns.str.strip()
    
    print(f"  Found {len(clinical_df)} patients in clinical data")
    print(f"  Columns: {list(clinical_df.columns)}")
    
    return clinical_df

def read_mutation_data(file_path):
    """Read Mutation.txt file, skipping header lines"""
    print(f"Reading mutation data from {file_path}...")
    
    # Read the file line by line to find the header
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find the header row (contains Tumor_Sample_Barcode)
    header_idx = None
    for i, line in enumerate(lines):
        if 'Tumor_Sample_Barcode' in line:
            header_idx = i
            break
    
    if header_idx is None:
        raise ValueError("Could not find Tumor_Sample_Barcode header in Mutation.txt")
    
    # Read the data starting from the header row
    # Use low_memory=False to avoid dtype warnings for large files
    mutation_df = pd.read_csv(file_path, sep='\t', skiprows=header_idx, encoding='utf-8', low_memory=False)
    
    # Clean column names
    mutation_df.columns = mutation_df.columns.str.strip()
    
    print(f"  Found {len(mutation_df)} mutation records")
    print(f"  Columns: {list(mutation_df.columns[:10])}... (showing first 10)")
    
    # Extract PATIENT_ID from Tumor_Sample_Barcode
    print("  Extracting PATIENT_ID from Tumor_Sample_Barcode...")
    mutation_df['PATIENT_ID'] = mutation_df['Tumor_Sample_Barcode'].apply(extract_patient_id_from_barcode)
    
    # Count unique patients
    unique_patients = mutation_df['PATIENT_ID'].nunique()
    print(f"  Found {unique_patients} unique patients in mutation data")
    
    return mutation_df

def merge_data(clinical_df, mutation_df):
    """Merge clinical and mutation data on PATIENT_ID"""
    print("\nMerging data on PATIENT_ID...")
    
    # Perform left join to keep all mutation records
    merged_df = mutation_df.merge(
        clinical_df,
        on='PATIENT_ID',
        how='left',
        suffixes=('', '_clinical')
    )
    
    print(f"  Merged dataset has {len(merged_df)} rows")
    print(f"  Patients with clinical data: {merged_df['PATIENT_ID'].notna().sum()}")
    print(f"  Patients without clinical data: {merged_df['PATIENT_ID'].isna().sum()}")
    
    # Check for patients in mutations but not in clinical
    mutation_patients = set(mutation_df['PATIENT_ID'].dropna().unique())
    clinical_patients = set(clinical_df['PATIENT_ID'].dropna().unique())
    missing_patients = mutation_patients - clinical_patients
    
    if missing_patients:
        print(f"\n  Warning: {len(missing_patients)} patients in mutation data but not in clinical data:")
        print(f"    Examples: {list(missing_patients)[:5]}")
    
    return merged_df

def main():
    # Define file paths
    base_dir = Path("/Users/senol/Desktop/pancreas/survival/New/New 2/PDAC 2025")
    clinical_file = base_dir / "Clinical.txt"
    mutation_file = base_dir / "Mutation.txt"
    output_file = base_dir.parent / "Merged_Clinical_Mutation_Data.txt"
    
    # Check if files exist
    if not clinical_file.exists():
        raise FileNotFoundError(f"Clinical file not found: {clinical_file}")
    if not mutation_file.exists():
        raise FileNotFoundError(f"Mutation file not found: {mutation_file}")
    
    # Read data
    clinical_df = read_clinical_data(clinical_file)
    mutation_df = read_mutation_data(mutation_file)
    
    # Merge data
    merged_df = merge_data(clinical_df, mutation_df)
    
    # Save merged data
    print(f"\nSaving merged data to {output_file}...")
    merged_df.to_csv(output_file, sep='\t', index=False, encoding='utf-8')
    print(f"  Saved {len(merged_df)} rows to {output_file}")
    
    # Also save as Excel for easier viewing
    excel_file = base_dir.parent / "Merged_Clinical_Mutation_Data.xlsx"
    print(f"\nSaving merged data to {excel_file}...")
    # For large files, we might need to use openpyxl engine
    try:
        merged_df.to_excel(excel_file, index=False, engine='openpyxl')
        print(f"  Saved to Excel format")
    except Exception as e:
        print(f"  Warning: Could not save to Excel: {e}")
        print(f"  You may need to install openpyxl: pip install openpyxl")
    
    # Print summary statistics
    print("\n" + "="*60)
    print("MERGE SUMMARY")
    print("="*60)
    print(f"Total mutation records: {len(merged_df)}")
    print(f"Unique patients: {merged_df['PATIENT_ID'].nunique()}")
    print(f"Patients with clinical data: {merged_df[clinical_df.columns[0]].notna().sum()}")
    
    # Show sample of merged data
    print("\nSample of merged data (first 3 rows, key columns):")
    key_cols = ['PATIENT_ID', 'Hugo_Symbol', 'Variant_Classification', 
                'SEX', 'AGE', 'OS_STATUS', 'OS_MONTHS']
    available_cols = [col for col in key_cols if col in merged_df.columns]
    print(merged_df[available_cols].head(3).to_string())
    
    print(f"\n✓ Merge completed successfully!")
    print(f"  Output file: {output_file}")

if __name__ == "__main__":
    main()




