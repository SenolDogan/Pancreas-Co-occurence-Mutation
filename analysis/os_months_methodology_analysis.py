#!/usr/bin/env python3
"""
OS_MONTHS Analysis for Alive Patients
=====================================

This script analyzes how OS_MONTHS is calculated for alive patients
and explains the methodology.

Author: AI Assistant
Date: 2024
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
import sys
from pathlib import Path

warnings.filterwarnings('ignore')

sys.path.insert(0, str(Path(__file__).resolve().parent / "tumor"))
from manuscript_figure_style import apply_manuscript_figure_style


def _set_publication_font() -> None:
    apply_manuscript_figure_style()

def analyze_os_months_methodology():
    """
    Analyze how OS_MONTHS is calculated for alive patients
    """
    print("="*80)
    print("OS_MONTHS METHODOLOGY ANALYSIS")
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
        
        # Get unique patients with their survival status and OS_MONTHS
        patient_data = df.groupby('Patient_ID').agg({
            'OS_STATUS': 'first',
            'OS_MONTHS': 'first'
        }).reset_index()
        
        print(f"Patient data created: {len(patient_data)} patients")
        
        # Separate Dead and Alive patients
        dead_patients = patient_data[patient_data['OS_STATUS'] == '1:DECEASED'].copy()
        alive_patients = patient_data[patient_data['OS_STATUS'] == '0:LIVING'].copy()
        
        print(f"\nDead patients: {len(dead_patients)}")
        print(f"Alive patients: {len(alive_patients)}")
        
        # Analyze OS_MONTHS for dead patients
        print(f"\n" + "="*60)
        print("DEAD PATIENTS OS_MONTHS ANALYSIS")
        print("="*60)
        
        dead_os_numeric = pd.to_numeric(dead_patients['OS_MONTHS'], errors='coerce')
        dead_os_clean = dead_os_numeric.dropna()
        
        print(f"Dead patients with valid OS_MONTHS: {len(dead_os_clean)}")
        print(f"Mean OS: {dead_os_clean.mean():.1f} months")
        print(f"Median OS: {dead_os_clean.median():.1f} months")
        print(f"Min OS: {dead_os_clean.min():.1f} months")
        print(f"Max OS: {dead_os_clean.max():.1f} months")
        print(f"Standard Deviation: {dead_os_clean.std():.1f} months")
        
        # Analyze OS_MONTHS for alive patients
        print(f"\n" + "="*60)
        print("ALIVE PATIENTS OS_MONTHS ANALYSIS")
        print("="*60)
        
        alive_os_numeric = pd.to_numeric(alive_patients['OS_MONTHS'], errors='coerce')
        alive_os_clean = alive_os_numeric.dropna()
        
        print(f"Alive patients with valid OS_MONTHS: {len(alive_os_clean)}")
        print(f"Mean OS: {alive_os_clean.mean():.1f} months")
        print(f"Median OS: {alive_os_clean.median():.1f} months")
        print(f"Min OS: {alive_os_clean.min():.1f} months")
        print(f"Max OS: {alive_os_clean.max():.1f} months")
        print(f"Standard Deviation: {alive_os_clean.std():.1f} months")
        
        # Check for censored data (alive patients with high OS_MONTHS)
        print(f"\n" + "="*60)
        print("CENSORED DATA ANALYSIS")
        print("="*60)
        
        # Define high OS_MONTHS as potential censoring
        high_os_threshold = alive_os_clean.quantile(0.75)  # 75th percentile
        high_os_alive = alive_os_clean[alive_os_clean >= high_os_threshold]
        
        print(f"75th percentile OS_MONTHS for alive patients: {high_os_threshold:.1f} months")
        print(f"Alive patients with OS_MONTHS >= {high_os_threshold:.1f}: {len(high_os_alive)}")
        print(f"Percentage of alive patients with high OS: {len(high_os_alive)/len(alive_os_clean)*100:.1f}%")
        
        # Show distribution of OS_MONTHS for alive patients
        print(f"\nOS_MONTHS distribution for alive patients:")
        print(f"0-12 months: {len(alive_os_clean[alive_os_clean <= 12])} patients")
        print(f"12-24 months: {len(alive_os_clean[(alive_os_clean > 12) & (alive_os_clean <= 24)])} patients")
        print(f"24-36 months: {len(alive_os_clean[(alive_os_clean > 24) & (alive_os_clean <= 36)])} patients")
        print(f"36+ months: {len(alive_os_clean[alive_os_clean > 36])} patients")
        
        # Check for potential data issues
        print(f"\n" + "="*60)
        print("DATA QUALITY CHECK")
        print("="*60)
        
        # Check for negative OS_MONTHS
        negative_os = alive_os_clean[alive_os_clean < 0]
        print(f"Alive patients with negative OS_MONTHS: {len(negative_os)}")
        
        # Check for zero OS_MONTHS
        zero_os = alive_os_clean[alive_os_clean == 0]
        print(f"Alive patients with zero OS_MONTHS: {len(zero_os)}")
        
        # Check for very high OS_MONTHS (potential outliers)
        very_high_os = alive_os_clean[alive_os_clean > 100]
        print(f"Alive patients with OS_MONTHS > 100: {len(very_high_os)}")
        
        return patient_data, dead_patients, alive_patients
        
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return None, None, None

def explain_os_methodology():
    """
    Explain how OS_MONTHS is calculated for alive patients
    """
    print(f"\n" + "="*80)
    print("OS_MONTHS METHODOLOGY EXPLANATION")
    print("="*80)
    
    explanation_text = """
    OVERALL SURVIVAL (OS_MONTHS) METHODOLOGY FOR ALIVE PATIENTS:
    
    1. DEFINITION:
       • OS_MONTHS = Time from diagnosis to death OR last follow-up
       • For alive patients: Time from diagnosis to last known contact
    
    2. CALCULATION METHODS:
       • Method 1: Last follow-up date - Diagnosis date
       • Method 2: Last contact date - Diagnosis date  
       • Method 3: Data cutoff date - Diagnosis date
    
    3. CENSORING:
       • Alive patients are "censored" observations
       • Their true survival time is unknown (could be longer)
       • OS_MONTHS represents minimum survival time
    
    4. CLINICAL MEANING:
       • Dead patients: Actual survival time
       • Alive patients: Minimum survival time (censored)
       • Both groups: Time from diagnosis to event/censoring
    
    5. STATISTICAL IMPLICATIONS:
       • Kaplan-Meier analysis handles censoring
       • Median survival can be calculated
       • Mean survival is biased (underestimated for alive patients)
    
    6. DATA INTERPRETATION:
       • High OS_MONTHS in alive patients = Long follow-up
       • Low OS_MONTHS in alive patients = Recent diagnosis
       • Zero OS_MONTHS = Diagnosis date = last contact date
    """
    
    print(explanation_text)

def create_os_methodology_visualization(dead_patients, alive_patients):
    """
    Create visualization explaining OS_MONTHS methodology
    """
    print("\n" + "="*80)
    print("CREATING OS METHODOLOGY VISUALIZATION")
    print("="*80)
    
    # Set style (clinic-friendly readability)
    plt.style.use('default')
    sns.set_palette("husl")
    _set_publication_font()
    plt.rcParams.update(
        {
            "font.size": 14,
            "axes.titlesize": 22,
            "axes.labelsize": 16,
            "xtick.labelsize": 13,
            "ytick.labelsize": 13,
            "legend.fontsize": 13,
        }
    )
    
    # Create figure with multiple subplots (reduced from 6 to 4 subplots, Panel 4 and 6 removed)
    fig = plt.figure(figsize=(24, 10))
    
    # 1. OS_MONTHS Distribution Comparison
    ax1 = plt.subplot(2, 2, 1)
    
    dead_os_numeric = pd.to_numeric(dead_patients['OS_MONTHS'], errors='coerce')
    alive_os_numeric = pd.to_numeric(alive_patients['OS_MONTHS'], errors='coerce')
    
    dead_os_clean = dead_os_numeric.dropna()
    alive_os_clean = alive_os_numeric.dropna()
    
    ax1.hist(dead_os_clean, bins=20, alpha=0.7, color='#d62728', label='Dead Patients', density=True)
    ax1.hist(alive_os_clean, bins=20, alpha=0.7, color='#2ca02c', label='Alive Patients', density=True)
    ax1.set_xlabel('OS_MONTHS')
    ax1.set_ylabel('Density')
    ax1.set_title('OS_MONTHS Distribution: Dead vs Alive', fontsize=14, fontweight='bold')
    ax1.legend()
    ax1.grid(axis='y', alpha=0.3)
    
    # 2. Box Plot Comparison
    ax2 = plt.subplot(2, 2, 2)
    
    data_to_plot = [dead_os_clean, alive_os_clean]
    labels = ['Dead', 'Alive']
    
    bp = ax2.boxplot(data_to_plot, labels=labels, patch_artist=True)
    bp['boxes'][0].set_facecolor('#d62728')
    bp['boxes'][1].set_facecolor('#2ca02c')
    
    ax2.set_ylabel('OS_MONTHS')
    ax2.set_title('OS_MONTHS Box Plot Comparison', fontsize=14, fontweight='bold')
    ax2.grid(axis='y', alpha=0.3)
    
    # 3. Cumulative Distribution
    ax3 = plt.subplot(2, 2, 3)
    
    dead_sorted = np.sort(dead_os_clean)
    alive_sorted = np.sort(alive_os_clean)
    
    dead_cumulative = np.arange(1, len(dead_sorted) + 1) / len(dead_sorted)
    alive_cumulative = np.arange(1, len(alive_sorted) + 1) / len(alive_sorted)
    
    ax3.plot(dead_sorted, dead_cumulative, color='#d62728', label='Dead Patients', linewidth=2)
    ax3.plot(alive_sorted, alive_cumulative, color='#2ca02c', label='Alive Patients', linewidth=2)
    ax3.set_xlabel('OS_MONTHS')
    ax3.set_ylabel('Cumulative Probability')
    ax3.set_title('Cumulative Distribution of OS_MONTHS', fontsize=14, fontweight='bold')
    ax3.legend()
    ax3.grid(axis='y', alpha=0.3)
    
    # 4. Methodology Explanation (removed as requested)
    # ax4 removed
    
    # 5. Survival Time Categories
    ax5 = plt.subplot(2, 2, 4)
    
    # Categorize OS_MONTHS
    categories = ['0-6', '6-12', '12-24', '24-36', '36+']
    
    dead_counts = [
        len(dead_os_clean[dead_os_clean <= 6]),
        len(dead_os_clean[(dead_os_clean > 6) & (dead_os_clean <= 12)]),
        len(dead_os_clean[(dead_os_clean > 12) & (dead_os_clean <= 24)]),
        len(dead_os_clean[(dead_os_clean > 24) & (dead_os_clean <= 36)]),
        len(dead_os_clean[dead_os_clean > 36])
    ]
    
    alive_counts = [
        len(alive_os_clean[alive_os_clean <= 6]),
        len(alive_os_clean[(alive_os_clean > 6) & (alive_os_clean <= 12)]),
        len(alive_os_clean[(alive_os_clean > 12) & (alive_os_clean <= 24)]),
        len(alive_os_clean[(alive_os_clean > 24) & (alive_os_clean <= 36)]),
        len(alive_os_clean[alive_os_clean > 36])
    ]
    
    x_pos = np.arange(len(categories))
    width = 0.35
    
    bars1 = ax5.bar(x_pos - width/2, dead_counts, width, label='Dead', color='#d62728', alpha=0.7)
    bars2 = ax5.bar(x_pos + width/2, alive_counts, width, label='Alive', color='#2ca02c', alpha=0.7)
    
    ax5.set_xticks(x_pos)
    ax5.set_xticklabels(categories)
    ax5.set_ylabel('Number of Patients')
    ax5.set_title('OS_MONTHS Categories Distribution', fontsize=14, fontweight='bold')
    ax5.legend()
    ax5.grid(axis='y', alpha=0.3)
    
    # 6. Data Quality Summary (removed as requested)
    # ax6 removed
    
    plt.tight_layout(pad=2.0)
    out1 = '/Users/senol/Desktop/pancreas/survival/New/New 2/06_OS_Months_Methodology_Analysis.png'
    plt.savefig(out1, dpi=350, bbox_inches='tight')
    plt.close()
    
    print(f"✅ OS_MONTHS methodology visualization saved as: {out1}")

def main():
    """
    Main function to run OS_MONTHS methodology analysis
    """
    print("OS_MONTHS METHODOLOGY ANALYSIS")
    print("="*80)
    print(f"Analysis started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Analyze OS_MONTHS methodology
    patient_data, dead_patients, alive_patients = analyze_os_months_methodology()
    
    if patient_data is None:
        print("❌ Failed to load data. Exiting.")
        return
    
    # Explain methodology
    explain_os_methodology()
    
    # Create visualization
    create_os_methodology_visualization(dead_patients, alive_patients)
    
    print("\n" + "="*80)
    print("OS_MONTHS METHODOLOGY ANALYSIS COMPLETED")
    print("="*80)
    print(f"Analysis finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()

