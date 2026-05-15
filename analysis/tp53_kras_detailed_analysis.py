#!/usr/bin/env python3
"""
TP53+KRAS Combination Detailed Analysis
======================================

This script provides detailed analysis of TP53+KRAS combination patients
including survival statistics, age analysis, and clinical characteristics.

Author: AI Assistant
Date: 2024
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "tumor"))
from manuscript_figure_style import apply_manuscript_figure_style
import warnings
warnings.filterwarnings('ignore')

def load_and_prepare_data():
    """
    Load and prepare data for TP53+KRAS detailed analysis
    """
    print("="*80)
    print("LOADING DATA FOR TP53+KRAS DETAILED ANALYSIS")
    print("="*80)
    
    try:
        # Load merged data
        df = pd.read_excel('/Users/senol/Desktop/pancreas/Merged.xlsx')
        print(f"✅ Loaded merged data: {len(df)} rows")
        
        # Get unique patients
        unique_patients = df['Patient_ID'].nunique()
        print(f"Unique patients: {unique_patients}")
        
        # Create patient-level data
        print("\nCreating patient-level data...")
        
        # Get unique patients with their survival status
        patient_survival = df.groupby('Patient_ID')['OS_STATUS'].first().reset_index()
        
        # Get genetic mutations for each patient
        genetic_mutations = ['TP53', 'KRAS', 'CDKN2A', 'SMAD4', 'ARID1A', 'ATM', 
                            'PIK3CA', 'BRAF', 'GNAS', 'RNF43']
        
        patient_mutations = df.groupby('Patient_ID')['Hugo_Symbol'].apply(list).reset_index()
        
        # Create binary mutation columns
        for mutation in genetic_mutations:
            patient_mutations[mutation] = patient_mutations['Hugo_Symbol'].apply(
                lambda x: 1 if mutation in x else 0
            )
        
        # Get clinical factors for each patient
        clinical_factors = ['SEX', 'AGE', 'TOBACCO_EXPOSURE', 'CANCER_HISTORY', 'STAGE', 
                           'CAD_HISTORY', 'HYPERTENSION_HISTORY', 'TUMOR_LOCATION',
                           'DIABETES_HISOTRY', 'PANCREATITIS_HISOTRY', 'AUTOIMMUNE_HISOTRY']
        
        patient_clinical = df.groupby('Patient_ID')[clinical_factors].first().reset_index()
        
        # Get OS_MONTHS for each patient
        patient_os = df.groupby('Patient_ID')['OS_MONTHS'].first().reset_index()
        
        # Merge all data
        patient_data = patient_survival.merge(patient_mutations, on='Patient_ID')
        patient_data = patient_data.merge(patient_clinical, on='Patient_ID')
        patient_data = patient_data.merge(patient_os, on='Patient_ID')
        
        print(f"\nPatient data created: {len(patient_data)} patients")
        
        return patient_data
        
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return None

def analyze_tp53_kras_combination(patient_data):
    """
    Detailed analysis of TP53+KRAS combination patients
    """
    print("\n" + "="*80)
    print("TP53+KRAS COMBINATION DETAILED ANALYSIS")
    print("="*80)
    
    # Filter patients with both TP53 and KRAS mutations
    tp53_kras_patients = patient_data[
        (patient_data['TP53'] == 1) & (patient_data['KRAS'] == 1)
    ].copy()
    
    print(f"Total patients with TP53+KRAS combination: {len(tp53_kras_patients)}")
    
    # Separate Dead and Alive patients
    dead_tp53_kras = tp53_kras_patients[tp53_kras_patients['OS_STATUS'] == '1:DECEASED'].copy()
    alive_tp53_kras = tp53_kras_patients[tp53_kras_patients['OS_STATUS'] == '0:LIVING'].copy()
    
    print(f"\nDead patients with TP53+KRAS: {len(dead_tp53_kras)}")
    print(f"Alive patients with TP53+KRAS: {len(alive_tp53_kras)}")
    
    # Calculate survival rates
    total_tp53_kras = len(tp53_kras_patients)
    dead_rate = len(dead_tp53_kras) / total_tp53_kras * 100
    alive_rate = len(alive_tp53_kras) / total_tp53_kras * 100
    
    print(f"\nSurvival rates:")
    print(f"Dead rate: {dead_rate:.1f}%")
    print(f"Alive rate: {alive_rate:.1f}%")
    
    # Analyze OS_MONTHS for dead patients
    if len(dead_tp53_kras) > 0:
        # Convert OS_MONTHS to numeric, handling any non-numeric values
        dead_os_numeric = pd.to_numeric(dead_tp53_kras['OS_MONTHS'], errors='coerce')
        
        # Remove NaN values
        dead_os_clean = dead_os_numeric.dropna()
        
        if len(dead_os_clean) > 0:
            mean_os_dead = dead_os_clean.mean()
            median_os_dead = dead_os_clean.median()
            std_os_dead = dead_os_clean.std()
            min_os_dead = dead_os_clean.min()
            max_os_dead = dead_os_clean.max()
            
            print(f"\nOverall Survival Analysis (Dead Patients):")
            print(f"Mean OS: {mean_os_dead:.1f} months")
            print(f"Median OS: {median_os_dead:.1f} months")
            print(f"Standard Deviation: {std_os_dead:.1f} months")
            print(f"Range: {min_os_dead:.1f} - {max_os_dead:.1f} months")
            print(f"Patients with OS data: {len(dead_os_clean)}")
        else:
            print(f"\nNo valid OS data found for dead patients")
    
    # Analyze OS_MONTHS for alive patients
    if len(alive_tp53_kras) > 0:
        alive_os_numeric = pd.to_numeric(alive_tp53_kras['OS_MONTHS'], errors='coerce')
        alive_os_clean = alive_os_numeric.dropna()
        
        if len(alive_os_clean) > 0:
            mean_os_alive = alive_os_clean.mean()
            median_os_alive = alive_os_clean.median()
            std_os_alive = alive_os_clean.std()
            min_os_alive = alive_os_clean.min()
            max_os_alive = alive_os_clean.max()
            
            print(f"\nOverall Survival Analysis (Alive Patients):")
            print(f"Mean OS: {mean_os_alive:.1f} months")
            print(f"Median OS: {median_os_alive:.1f} months")
            print(f"Standard Deviation: {std_os_alive:.1f} months")
            print(f"Range: {min_os_alive:.1f} - {max_os_alive:.1f} months")
            print(f"Patients with OS data: {len(alive_os_clean)}")
        else:
            print(f"\nNo valid OS data found for alive patients")
    
    # Age analysis
    if 'AGE' in tp53_kras_patients.columns:
        print(f"\nAge Analysis:")
        
        # Dead patients age
        dead_age_numeric = pd.to_numeric(dead_tp53_kras['AGE'], errors='coerce')
        dead_age_clean = dead_age_numeric.dropna()
        
        if len(dead_age_clean) > 0:
            mean_age_dead = dead_age_clean.mean()
            print(f"Dead patients - Mean age: {mean_age_dead:.1f} years")
        
        # Alive patients age
        alive_age_numeric = pd.to_numeric(alive_tp53_kras['AGE'], errors='coerce')
        alive_age_clean = alive_age_numeric.dropna()
        
        if len(alive_age_clean) > 0:
            mean_age_alive = alive_age_clean.mean()
            print(f"Alive patients - Mean age: {mean_age_alive:.1f} years")
    
    # Clinical factors analysis
    print(f"\nClinical Factors Analysis:")
    
    clinical_factors = ['STAGE', 'SEX', 'TUMOR_LOCATION', 'DIABETES_HISOTRY']
    
    for factor in clinical_factors:
        if factor in tp53_kras_patients.columns:
            print(f"\n{factor} distribution:")
            
            # Dead patients
            dead_factor = dead_tp53_kras[factor].value_counts()
            print(f"  Dead patients:")
            for value, count in dead_factor.items():
                percentage = count / len(dead_tp53_kras) * 100
                print(f"    {value}: {count} ({percentage:.1f}%)")
            
            # Alive patients
            alive_factor = alive_tp53_kras[factor].value_counts()
            print(f"  Alive patients:")
            for value, count in alive_factor.items():
                percentage = count / len(alive_tp53_kras) * 100
                print(f"    {value}: {count} ({percentage:.1f}%)")
    
    return tp53_kras_patients, dead_tp53_kras, alive_tp53_kras

def create_tp53_kras_visualization(tp53_kras_patients, dead_tp53_kras, alive_tp53_kras):
    """
    Create visualization for TP53+KRAS combination analysis
    """
    print("\n" + "="*80)
    print("CREATING TP53+KRAS VISUALIZATION")
    print("="*80)
    
    # Set style
    apply_manuscript_figure_style()
    sns.set_palette("husl")
    
    # Create figure with multiple subplots (reduced from 9 to 6 subplots, Panel 7, 8, 9 removed)
    fig = plt.figure(figsize=(20, 12))
    
    # 1. Survival Distribution
    ax1 = plt.subplot(3, 3, 1)
    categories = ['Dead', 'Alive']
    counts = [len(dead_tp53_kras), len(alive_tp53_kras)]
    colors = ['#d62728', '#2ca02c']
    
    bars = ax1.bar(categories, counts, color=colors, alpha=0.7)
    ax1.set_title('TP53+KRAS: Survival Distribution', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Number of Patients')
    
    # Add value labels on bars (moved down for better readability)
    total_patients = len(tp53_kras_patients)
    for bar, count in zip(bars, counts):
        height = bar.get_height()
        percentage = count / total_patients * 100
        # Move text down inside the bar, near the bottom
        ax1.text(bar.get_x() + bar.get_width()/2., height * 0.15,
                f'{count}\n({percentage:.1f}%)',
                ha='center', va='bottom', fontweight='bold', fontsize=11)
    
    # 2. Overall Survival Distribution (Dead Patients)
    ax2 = plt.subplot(3, 3, 2)
    if len(dead_tp53_kras) > 0:
        dead_os_numeric = pd.to_numeric(dead_tp53_kras['OS_MONTHS'], errors='coerce')
        dead_os_clean = dead_os_numeric.dropna()
        
        if len(dead_os_clean) > 0:
            ax2.hist(dead_os_clean, bins=20, color='#d62728', alpha=0.7, edgecolor='black')
            ax2.set_title('Overall Survival Distribution (Dead Patients)', fontsize=14, fontweight='bold')
            ax2.set_xlabel('Overall Survival (Months)')
            ax2.set_ylabel('Number of Patients')
            ax2.grid(axis='y', alpha=0.3)
            
            # Add mean line
            mean_os = dead_os_clean.mean()
            ax2.axvline(mean_os, color='red', linestyle='--', linewidth=2, 
                       label=f'Mean: {mean_os:.1f} months')
            ax2.legend()
    
    # 3. Overall Survival Distribution (Alive Patients)
    ax3 = plt.subplot(3, 3, 3)
    if len(alive_tp53_kras) > 0:
        alive_os_numeric = pd.to_numeric(alive_tp53_kras['OS_MONTHS'], errors='coerce')
        alive_os_clean = alive_os_numeric.dropna()
        
        if len(alive_os_clean) > 0:
            ax3.hist(alive_os_clean, bins=20, color='#2ca02c', alpha=0.7, edgecolor='black')
            ax3.set_title('Overall Survival Distribution (Alive Patients)', fontsize=14, fontweight='bold')
            ax3.set_xlabel('Overall Survival (Months)')
            ax3.set_ylabel('Number of Patients')
            ax3.grid(axis='y', alpha=0.3)
            
            # Add mean line
            mean_os = alive_os_clean.mean()
            ax3.axvline(mean_os, color='green', linestyle='--', linewidth=2, 
                       label=f'Mean: {mean_os:.1f} months')
            ax3.legend()
    
    # 4. Age Distribution
    ax4 = plt.subplot(3, 3, 4)
    if 'AGE' in tp53_kras_patients.columns:
        dead_age_numeric = pd.to_numeric(dead_tp53_kras['AGE'], errors='coerce')
        alive_age_numeric = pd.to_numeric(alive_tp53_kras['AGE'], errors='coerce')
        
        dead_age_clean = dead_age_numeric.dropna()
        alive_age_clean = alive_age_numeric.dropna()
        
        if len(dead_age_clean) > 0 and len(alive_age_clean) > 0:
            ax4.hist(dead_age_clean, bins=15, alpha=0.7, color='#d62728', label='Dead', density=True)
            ax4.hist(alive_age_clean, bins=15, alpha=0.7, color='#2ca02c', label='Alive', density=True)
            ax4.set_title('Age Distribution', fontsize=14, fontweight='bold')
            ax4.set_xlabel('Age (Years)')
            ax4.set_ylabel('Density')
            ax4.legend()
            ax4.grid(axis='y', alpha=0.3)
    
    # 5. Stage Distribution
    ax5 = plt.subplot(3, 3, 5)
    if 'STAGE' in tp53_kras_patients.columns:
        stage_dead = dead_tp53_kras['STAGE'].value_counts()
        stage_alive = alive_tp53_kras['STAGE'].value_counts()
        
        stages = list(set(stage_dead.index) | set(stage_alive.index))
        dead_counts = [stage_dead.get(stage, 0) for stage in stages]
        alive_counts = [stage_alive.get(stage, 0) for stage in stages]
        
        # Abbreviate long stage names
        def abbreviate_stage(stage):
            if 'Borderline Resectable/Locally Advanced' in str(stage):
                return str(stage).replace('Borderline Resectable/Locally Advanced', 'Bor.Res.Loc.Adv.')
            return str(stage)
        
        stages_abbreviated = [abbreviate_stage(stage) for stage in stages]
        
        x_pos = np.arange(len(stages))
        width = 0.35
        
        bars1 = ax5.bar(x_pos - width/2, dead_counts, width, label='Dead', color='#d62728', alpha=0.7)
        bars2 = ax5.bar(x_pos + width/2, alive_counts, width, label='Alive', color='#2ca02c', alpha=0.7)
        
        ax5.set_xticks(x_pos)
        ax5.set_xticklabels(stages_abbreviated, rotation=45, ha='right')
        ax5.set_ylabel('Number of Patients')
        ax5.set_title('Stage Distribution', fontsize=14, fontweight='bold')
        ax5.legend()
        ax5.grid(axis='y', alpha=0.3)
    
    # 6. Gender Distribution
    ax6 = plt.subplot(3, 3, 6)
    if 'SEX' in tp53_kras_patients.columns:
        sex_dead = dead_tp53_kras['SEX'].value_counts()
        sex_alive = alive_tp53_kras['SEX'].value_counts()
        
        sexes = list(set(sex_dead.index) | set(sex_alive.index))
        dead_counts = [sex_dead.get(sex, 0) for sex in sexes]
        alive_counts = [sex_alive.get(sex, 0) for sex in sexes]
        
        x_pos = np.arange(len(sexes))
        width = 0.35
        
        bars1 = ax6.bar(x_pos - width/2, dead_counts, width, label='Dead', color='#d62728', alpha=0.7)
        bars2 = ax6.bar(x_pos + width/2, alive_counts, width, label='Alive', color='#2ca02c', alpha=0.7)
        
        ax6.set_xticks(x_pos)
        ax6.set_xticklabels(sexes)
        ax6.set_ylabel('Number of Patients')
        ax6.set_title('Gender Distribution', fontsize=14, fontweight='bold')
        ax6.legend()
        ax6.grid(axis='y', alpha=0.3)
    
    # 7. Summary Statistics (removed as requested)
    # ax7 removed
    
    # 8. OS Comparison Box Plot (removed as requested)
    # ax8 removed
    
    # 9. Methodological Notes (removed as requested)
    # ax9 removed
    
    plt.tight_layout()
    plt.savefig('/Users/senol/Desktop/pancreas/survival/New/New 2/05_TP53_KRAS_Detailed_Analysis.png', 
                dpi=300, bbox_inches='tight')
    plt.show()
    
    print("✅ TP53+KRAS detailed visualization saved as: 05_TP53_KRAS_Detailed_Analysis.png")

def save_tp53_kras_results(tp53_kras_patients, dead_tp53_kras, alive_tp53_kras):
    """
    Save TP53+KRAS analysis results to Excel
    """
    print("\n" + "="*80)
    print("SAVING TP53+KRAS RESULTS")
    print("="*80)
    
    try:
        with pd.ExcelWriter('/Users/senol/Desktop/pancreas/survival/New/New 2/TP53_KRAS_Detailed_Analysis.xlsx', 
                           engine='openpyxl') as writer:
            
            # All TP53+KRAS patients
            tp53_kras_patients.to_excel(writer, sheet_name='All_TP53_KRAS_Patients', index=False)
            
            # Dead TP53+KRAS patients
            dead_tp53_kras.to_excel(writer, sheet_name='Dead_TP53_KRAS_Patients', index=False)
            
            # Alive TP53+KRAS patients
            alive_tp53_kras.to_excel(writer, sheet_name='Alive_TP53_KRAS_Patients', index=False)
            
            # Summary statistics
            summary_data = {
                'Metric': ['Total Patients', 'Dead Patients', 'Alive Patients', 'Dead Rate (%)', 'Alive Rate (%)'],
                'Value': [len(tp53_kras_patients), len(dead_tp53_kras), len(alive_tp53_kras), 
                         len(dead_tp53_kras)/len(tp53_kras_patients)*100, 
                         len(alive_tp53_kras)/len(tp53_kras_patients)*100]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary_Statistics', index=False)
            
            print("✅ TP53+KRAS results saved to: TP53_KRAS_Detailed_Analysis.xlsx")
            
    except Exception as e:
        print(f"❌ Error saving results: {e}")

def main():
    """
    Main function to run TP53+KRAS detailed analysis
    """
    print("TP53+KRAS COMBINATION DETAILED ANALYSIS")
    print("="*80)
    print(f"Analysis started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load and prepare data
    patient_data = load_and_prepare_data()
    
    if patient_data is None:
        print("❌ Failed to load data. Exiting.")
        return
    
    # Analyze TP53+KRAS combination
    tp53_kras_patients, dead_tp53_kras, alive_tp53_kras = analyze_tp53_kras_combination(patient_data)
    
    # Create visualization
    create_tp53_kras_visualization(tp53_kras_patients, dead_tp53_kras, alive_tp53_kras)
    
    # Save results
    save_tp53_kras_results(tp53_kras_patients, dead_tp53_kras, alive_tp53_kras)
    
    print("\n" + "="*80)
    print("TP53+KRAS ANALYSIS COMPLETED SUCCESSFULLY")
    print("="*80)
    print(f"Analysis finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()

