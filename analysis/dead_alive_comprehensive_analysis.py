#!/usr/bin/env python3
"""
Dead vs Alive Comprehensive Analysis
===================================

This script performs comprehensive analysis comparing Dead vs Alive patients
using novel synergy methodology and multiplicative synergy scoring.

Key Analyses:
1. Dead vs Alive patient groups and basic statistics
2. Most lethal and most protective genetic mutations comparison
3. Novel synergy methodology and multiplicative synergy results
4. Lethal and protective clinical factors analysis
5. Mutation combinations affecting clinical factors
6. Comprehensive genetic-clinical interaction analysis

Author: AI Assistant
Date: 2024
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg", force=True)
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime
import sys
import warnings
warnings.filterwarnings('ignore')

sys.path.insert(0, str(Path(__file__).resolve().parent / "tumor"))
from manuscript_figure_style import apply_manuscript_figure_style


def _set_publication_font() -> None:
    """Times New Roman + larger bold defaults for manuscript figures."""
    apply_manuscript_figure_style()

def load_and_prepare_data():
    """
    Load and prepare data for Dead vs Alive analysis
    """
    print("="*80)
    print("LOADING DATA FOR DEAD VS ALIVE ANALYSIS")
    print("="*80)
    
    try:
        # Load master mutation-level analytic table (patient + mutation records)
        this_dir = Path(__file__).resolve().parent
        tumor_dir = this_dir / "tumor"
        merged_path = tumor_dir / "Merged.xlsx"
        df = pd.read_excel(merged_path)
        print(f"✅ Loaded master merged table: {len(df)} rows")

        pid_col = "PATIENT_ID" if "PATIENT_ID" in df.columns else ("Patient_ID" if "Patient_ID" in df.columns else None)
        if pid_col is None:
            raise ValueError("No patient identifier column found (expected PATIENT_ID or Patient_ID).")
        
        # Get unique patients
        unique_patients = df[pid_col].nunique()
        print(f"Unique patients: {unique_patients}")
        
        # Check survival status
        print(f"\nSurvival status distribution:")
        if "OS_STATUS" not in df.columns:
            raise ValueError("OS_STATUS is missing from master table; cannot build Dead vs Alive figure.")
        survival_counts = df["OS_STATUS"].value_counts()
        print(survival_counts)
        
        # Create patient-level data
        print("\nCreating patient-level data...")
        
        # Get unique patients with their survival status
        patient_survival = df.groupby(pid_col)["OS_STATUS"].first().reset_index().rename(columns={pid_col: "PATIENT_ID"})
        
        # Get genetic mutations for each patient
        genetic_mutations = [
            'TP53', 'KRAS', 'CDKN2A', 'SMAD4', 'ARID1A', 'ATM',
            'PIK3CA', 'BRAF', 'GNAS', 'RNF43'
        ]
        
        if "Hugo_Symbol" not in df.columns:
            raise ValueError("Hugo_Symbol is missing from master table; cannot derive mutation indicators.")
        patient_mutations = (
            df.groupby(pid_col)["Hugo_Symbol"]
            .apply(lambda x: [str(v) for v in x.dropna().tolist()])
            .reset_index()
            .rename(columns={pid_col: "PATIENT_ID"})
        )
        
        # Create binary mutation columns
        for mutation in genetic_mutations:
            patient_mutations[mutation] = patient_mutations['Hugo_Symbol'].apply(
                lambda x: 1 if mutation in x else 0
            )

        # Drop genes that are entirely absent (no mutated patients)
        present_genes = [g for g in genetic_mutations if patient_mutations[g].sum() > 0]
        absent_genes = [g for g in genetic_mutations if g not in present_genes]
        if absent_genes:
            print(f"Removing absent genes (no mutations observed): {absent_genes}")
        genetic_mutations = present_genes
        # Keep only present mutation columns (plus Hugo_Symbol for debug, dropped later)
        keep_cols = ["PATIENT_ID", "Hugo_Symbol"] + genetic_mutations
        patient_mutations = patient_mutations[keep_cols]
        
        # Get clinical factors for each patient.
        # As requested, we do not use: SEX, RACE, ETHNICITY, PRIMARY_SITE_PATIENT in panels E/F.
        # In the master table, multiple categorical clinical columns exist; we still prefer a single
        # reviewer-friendly derived factor (AGE_BIN) for panels E/F to avoid noisy demographic labels.
        clinical_factors = ['AGE']
        
        # Only include factors that exist in the dataframe
        available_factors = [f for f in clinical_factors if f in df.columns]
        patient_clinical = df.groupby(pid_col)[available_factors].first().reset_index().rename(columns={pid_col: "PATIENT_ID"})

        # Derive AGE_BIN for categorical clinical summaries
        if "AGE" in patient_clinical.columns:
            age_num = pd.to_numeric(patient_clinical["AGE"], errors="coerce")
            bins = [0, 50, 60, 70, 80, 120]
            labels = ["<50", "50–59", "60–69", "70–79", "80+"]
            patient_clinical["AGE_BIN"] = pd.cut(age_num, bins=bins, labels=labels, right=False, include_lowest=True)
        
        # Merge all data
        patient_data = patient_survival.merge(patient_mutations, on='PATIENT_ID')
        patient_data = patient_data.merge(patient_clinical, on='PATIENT_ID')
        
        # Separate Dead and Alive patients
        dead_patients = patient_data[patient_data["OS_STATUS"] == "1:DECEASED"].copy()
        alive_patients = patient_data[patient_data["OS_STATUS"] == "0:LIVING"].copy()
        
        print(f"\nDead patients: {len(dead_patients)}")
        print(f"Alive patients: {len(alive_patients)}")
        
        return patient_data, dead_patients, alive_patients
        
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return None, None, None

def calculate_basic_statistics(dead_patients, alive_patients):
    """
    Calculate basic statistics for Dead vs Alive patients
    """
    print("\n" + "="*80)
    print("BASIC STATISTICS: DEAD VS ALIVE")
    print("="*80)
    
    stats = {}
    
    # Overall survival rates
    total_patients = len(dead_patients) + len(alive_patients)
    dead_rate = len(dead_patients) / total_patients * 100
    alive_rate = len(alive_patients) / total_patients * 100
    
    stats['total_patients'] = total_patients
    stats['dead_patients'] = len(dead_patients)
    stats['alive_patients'] = len(alive_patients)
    stats['dead_rate'] = dead_rate
    stats['alive_rate'] = alive_rate
    
    print(f"Total patients: {total_patients}")
    print(f"Dead patients: {len(dead_patients)} ({dead_rate:.1f}%)")
    print(f"Alive patients: {len(alive_patients)} ({alive_rate:.1f}%)")
    
    # Age statistics
    if 'AGE' in dead_patients.columns and 'AGE' in alive_patients.columns:
        try:
            # Convert AGE to numeric, handling any non-numeric values
            dead_age_numeric = pd.to_numeric(dead_patients['AGE'], errors='coerce')
            alive_age_numeric = pd.to_numeric(alive_patients['AGE'], errors='coerce')
            
            dead_age_mean = dead_age_numeric.mean()
            alive_age_mean = alive_age_numeric.mean()
            
            stats['dead_age_mean'] = dead_age_mean
            stats['alive_age_mean'] = alive_age_mean
            
            print(f"\nAge statistics:")
            print(f"Dead patients mean age: {dead_age_mean:.1f}")
            print(f"Alive patients mean age: {alive_age_mean:.1f}")
        except Exception as e:
            print(f"\nAge statistics: Error processing age data - {e}")
            stats['dead_age_mean'] = None
            stats['alive_age_mean'] = None
    
    # Gender distribution
    if 'SEX' in dead_patients.columns and 'SEX' in alive_patients.columns:
        dead_gender = dead_patients['SEX'].value_counts()
        alive_gender = alive_patients['SEX'].value_counts()
        
        print(f"\nGender distribution:")
        print(f"Dead patients: {dict(dead_gender)}")
        print(f"Alive patients: {dict(alive_gender)}")
    
    return stats

def analyze_genetic_mutations(dead_patients, alive_patients):
    """
    Analyze genetic mutations in Dead vs Alive patients
    """
    print("\n" + "="*80)
    print("GENETIC MUTATIONS ANALYSIS: DEAD VS ALIVE")
    print("="*80)
    
    # Define genetic mutations to analyze (only those present as columns)
    genetic_mutations = [
        g
        for g in ['TP53', 'KRAS', 'CDKN2A', 'SMAD4', 'ARID1A', 'ATM', 'PIK3CA', 'BRAF', 'GNAS', 'RNF43']
        if g in dead_patients.columns and g in alive_patients.columns
    ]
    
    mutation_analysis = []
    
    for mutation in genetic_mutations:
        if mutation in dead_patients.columns and mutation in alive_patients.columns:
            # Calculate mutation rates
            dead_mutated = dead_patients[mutation].sum()
            dead_total = len(dead_patients)
            dead_rate = dead_mutated / dead_total * 100
            
            alive_mutated = alive_patients[mutation].sum()
            alive_total = len(alive_patients)
            alive_rate = alive_mutated / alive_total * 100
            
            # Calculate lethality ratio
            lethality_ratio = dead_rate / alive_rate if alive_rate > 0 else float('inf')
            
            mutation_data = {
                'Mutation': mutation,
                'Dead_Mutated': dead_mutated,
                'Dead_Total': dead_total,
                'Dead_Rate': dead_rate,
                'Alive_Mutated': alive_mutated,
                'Alive_Total': alive_total,
                'Alive_Rate': alive_rate,
                'Lethality_Ratio': lethality_ratio
            }
            
            mutation_analysis.append(mutation_data)
            
            print(f"{mutation}:")
            print(f"  Dead: {dead_mutated}/{dead_total} ({dead_rate:.1f}%)")
            print(f"  Alive: {alive_mutated}/{alive_total} ({alive_rate:.1f}%)")
            print(f"  Lethality Ratio: {lethality_ratio:.2f}")
            print()
    
    mutation_df = pd.DataFrame(mutation_analysis)
    
    # Sort by lethality ratio
    mutation_df_sorted = mutation_df.sort_values('Lethality_Ratio', ascending=False)
    
    print("Most lethal mutations (highest lethality ratio):")
    print(mutation_df_sorted[['Mutation', 'Lethality_Ratio', 'Dead_Rate', 'Alive_Rate']].head())
    
    print("\nMost protective mutations (lowest lethality ratio):")
    print(mutation_df_sorted[['Mutation', 'Lethality_Ratio', 'Dead_Rate', 'Alive_Rate']].tail())
    
    return mutation_df_sorted

def calculate_synergy_scores(dead_patients, alive_patients, mutation_df):
    """
    Calculate synergy scores for genetic combinations
    """
    print("\n" + "="*80)
    print("SYNERGY SCORES CALCULATION: DEAD VS ALIVE")
    print("="*80)
    
    genetic_mutations = ['TP53', 'KRAS', 'CDKN2A', 'SMAD4', 'ARID1A', 'ATM', 
                        'PIK3CA', 'BRAF', 'GNAS', 'RNF43']
    
    synergy_results = []
    
    # Calculate dual combinations
    print("Calculating dual gene combinations...")
    
    for i, mut1 in enumerate(genetic_mutations):
        for j, mut2 in enumerate(genetic_mutations):
            if i < j and mut1 in dead_patients.columns and mut2 in dead_patients.columns:
                
                # Dead patients with both mutations
                dead_both = dead_patients[(dead_patients[mut1] == 1) & (dead_patients[mut2] == 1)]
                dead_both_count = len(dead_both)
                dead_total = len(dead_patients)
                dead_both_rate = dead_both_count / dead_total if dead_total > 0 else 0
                
                # Alive patients with both mutations
                alive_both = alive_patients[(alive_patients[mut1] == 1) & (alive_patients[mut2] == 1)]
                alive_both_count = len(alive_both)
                alive_total = len(alive_patients)
                alive_both_rate = alive_both_count / alive_total if alive_total > 0 else 0
                
                # Individual mutation rates
                dead_mut1_rate = dead_patients[mut1].sum() / dead_total if dead_total > 0 else 0
                dead_mut2_rate = dead_patients[mut2].sum() / dead_total if dead_total > 0 else 0
                alive_mut1_rate = alive_patients[mut1].sum() / alive_total if alive_total > 0 else 0
                alive_mut2_rate = alive_patients[mut2].sum() / alive_total if alive_total > 0 else 0
                
                # Calculate synergy scores
                # Multiplicative synergy for dead patients
                expected_dead_rate = dead_mut1_rate * dead_mut2_rate
                multiplicative_synergy_dead = dead_both_rate / expected_dead_rate if expected_dead_rate > 0 else 0
                
                # Multiplicative synergy for alive patients
                expected_alive_rate = alive_mut1_rate * alive_mut2_rate
                multiplicative_synergy_alive = alive_both_rate / expected_alive_rate if expected_alive_rate > 0 else 0
                
                # Additive synergy
                additive_synergy_dead = dead_both_rate - (dead_mut1_rate + dead_mut2_rate)
                additive_synergy_alive = alive_both_rate - (alive_mut1_rate + alive_mut2_rate)
                
                # Protective score (negative means protective)
                protective_score = -(dead_both_rate - alive_both_rate)
                
                synergy_data = {
                    'Combination': f"{mut1}+{mut2}",
                    'Dead_Both_Count': dead_both_count,
                    'Dead_Both_Rate': dead_both_rate,
                    'Alive_Both_Count': alive_both_count,
                    'Alive_Both_Rate': alive_both_rate,
                    'Dead_Mut1_Rate': dead_mut1_rate,
                    'Dead_Mut2_Rate': dead_mut2_rate,
                    'Alive_Mut1_Rate': alive_mut1_rate,
                    'Alive_Mut2_Rate': alive_mut2_rate,
                    'Multiplicative_Synergy_Dead': multiplicative_synergy_dead,
                    'Multiplicative_Synergy_Alive': multiplicative_synergy_alive,
                    'Additive_Synergy_Dead': additive_synergy_dead,
                    'Additive_Synergy_Alive': additive_synergy_alive,
                    'Protective_Score': protective_score,
                    'Total_Patients': dead_both_count + alive_both_count
                }
                
                synergy_results.append(synergy_data)
    
    synergy_df = pd.DataFrame(synergy_results)
    
    # Filter combinations with sufficient patients
    synergy_df_filtered = synergy_df[synergy_df['Total_Patients'] >= 5].copy()
    
    # Sort by multiplicative synergy (dead patients)
    synergy_df_sorted = synergy_df_filtered.sort_values('Multiplicative_Synergy_Dead', ascending=False)
    
    print(f"Analyzed {len(synergy_df_filtered)} combinations with ≥5 patients")
    print("\nTop 10 most synergistic combinations (Dead patients):")
    print(synergy_df_sorted[['Combination', 'Multiplicative_Synergy_Dead', 'Dead_Both_Rate', 'Alive_Both_Rate', 'Protective_Score']].head(10))
    
    print("\nTop 10 most protective combinations:")
    synergy_df_protective = synergy_df_filtered.sort_values('Protective_Score', ascending=False)
    print(synergy_df_protective[['Combination', 'Protective_Score', 'Dead_Both_Rate', 'Alive_Both_Rate']].head(10))
    
    return synergy_df_sorted

def analyze_clinical_factors(dead_patients, alive_patients):
    """
    Analyze clinical factors in Dead vs Alive patients
    """
    print("\n" + "="*80)
    print("CLINICAL FACTORS ANALYSIS: DEAD VS ALIVE")
    print("="*80)
    
    # Define clinical factors to analyze (categorical only).
    # Panels E/F should not include SEX/RACE/ETHNICITY/PRIMARY_SITE_PATIENT.
    clinical_factors = [f for f in ["AGE_BIN"] if f in dead_patients.columns and f in alive_patients.columns]
    
    clinical_analysis = []
    
    for factor in clinical_factors:
        if factor in dead_patients.columns and factor in alive_patients.columns:
            print(f"\nAnalyzing {factor}:")
            
            # Get unique values
            dead_values = dead_patients[factor].value_counts()
            alive_values = alive_patients[factor].value_counts()
            
            all_values = set(dead_values.index) | set(alive_values.index)
            
            for value in all_values:
                dead_count = dead_values.get(value, 0)
                dead_total = len(dead_patients)
                dead_rate = dead_count / dead_total * 100 if dead_total > 0 else 0
                
                alive_count = alive_values.get(value, 0)
                alive_total = len(alive_patients)
                alive_rate = alive_count / alive_total * 100 if alive_total > 0 else 0
                
                # Calculate lethality ratio
                lethality_ratio = dead_rate / alive_rate if alive_rate > 0 else float('inf')
                
                # Protective score (negative means protective)
                protective_score = -(dead_rate - alive_rate)
                
                clinical_data = {
                    'Factor': factor,
                    'Value': value,
                    'Dead_Count': dead_count,
                    'Dead_Rate': dead_rate,
                    'Alive_Count': alive_count,
                    'Alive_Rate': alive_rate,
                    'Lethality_Ratio': lethality_ratio,
                    'Protective_Score': protective_score
                }
                
                clinical_analysis.append(clinical_data)
                
                print(f"  {value}: Dead {dead_count}/{dead_total} ({dead_rate:.1f}%), Alive {alive_count}/{alive_total} ({alive_rate:.1f}%), Ratio: {lethality_ratio:.2f}")
    
    clinical_df = pd.DataFrame(clinical_analysis)
    if len(clinical_df) == 0:
        return clinical_df
    
    # Sort by protective score
    clinical_df_sorted = clinical_df.sort_values('Protective_Score', ascending=False)
    
    print("\nMost protective clinical factors:")
    print(clinical_df_sorted[['Factor', 'Value', 'Protective_Score', 'Dead_Rate', 'Alive_Rate']].head(10))
    
    print("\nMost lethal clinical factors:")
    print(clinical_df_sorted[['Factor', 'Value', 'Protective_Score', 'Dead_Rate', 'Alive_Rate']].tail(10))
    
    return clinical_df_sorted

def comprehensive_genetic_clinical_analysis(dead_patients, alive_patients, synergy_df, clinical_df):
    """
    Comprehensive analysis of genetic-clinical interactions
    """
    print("\n" + "="*80)
    print("COMPREHENSIVE GENETIC-CLINICAL INTERACTION ANALYSIS")
    print("="*80)
    
    # If no clinical factors are available, skip interaction analysis cleanly.
    if clinical_df is None or len(clinical_df) == 0:
        print("No clinical factors available; skipping genetic-clinical interaction analysis.")
        return pd.DataFrame()
    
    # Get top genetic combinations
    top_genetic_combinations = synergy_df.head(10)['Combination'].tolist()
    
    # Get top clinical factors (keep as (Factor, Value) pairs; do NOT concatenate with '_' because
    # factor names can include underscores, e.g., AGE_BIN).
    top_clinical_pairs = clinical_df.head(10)[["Factor", "Value"]].values.tolist()
    
    print(f"Analyzing {len(top_genetic_combinations)} top genetic combinations")
    print(f"Analyzing {len(top_clinical_pairs)} top clinical factors")
    
    interaction_results = []
    
    for genetic_combo in top_genetic_combinations:
        mut1, mut2 = genetic_combo.split('+')
        
        for factor_name, factor_value in top_clinical_pairs:
            
            if factor_name in dead_patients.columns and mut1 in dead_patients.columns and mut2 in dead_patients.columns:
                
                # Dead patients with genetic combo + clinical factor
                dead_genetic_clinical = dead_patients[
                    (dead_patients[mut1] == 1) & 
                    (dead_patients[mut2] == 1) & 
                    (dead_patients[factor_name].astype(str) == factor_value)
                ]
                dead_count = len(dead_genetic_clinical)
                dead_total = len(dead_patients)
                dead_rate = dead_count / dead_total * 100 if dead_total > 0 else 0
                
                # Alive patients with genetic combo + clinical factor
                alive_genetic_clinical = alive_patients[
                    (alive_patients[mut1] == 1) & 
                    (alive_patients[mut2] == 1) & 
                    (alive_patients[factor_name].astype(str) == factor_value)
                ]
                alive_count = len(alive_genetic_clinical)
                alive_total = len(alive_patients)
                alive_rate = alive_count / alive_total * 100 if alive_total > 0 else 0
                
                # Calculate interaction score
                interaction_score = -(dead_rate - alive_rate)
                
                # Keep Panel F non-empty: include low-count interactions, but they remain descriptive.
                if dead_count + alive_count >= 1:  # Minimum 1 patient
                    interaction_data = {
                        'Genetic_Combination': genetic_combo,
                        'Clinical_Factor': f"{factor_name}: {factor_value}",
                        'Dead_Count': dead_count,
                        'Dead_Rate': dead_rate,
                        'Alive_Count': alive_count,
                        'Alive_Rate': alive_rate,
                        'Interaction_Score': interaction_score,
                        'Total_Patients': dead_count + alive_count
                    }
                    
                    interaction_results.append(interaction_data)
    
    interaction_df = pd.DataFrame(interaction_results)
    
    if len(interaction_df) > 0:
        # Sort by interaction score
        interaction_df_sorted = interaction_df.sort_values('Interaction_Score', ascending=False)
        
        print(f"\nAnalyzed {len(interaction_df)} genetic-clinical interactions")
        print("\nMost protective genetic-clinical combinations:")
        print(interaction_df_sorted[['Genetic_Combination', 'Clinical_Factor', 'Interaction_Score', 'Dead_Rate', 'Alive_Rate']].head(10))
        
        print("\nMost lethal genetic-clinical combinations:")
        print(interaction_df_sorted[['Genetic_Combination', 'Clinical_Factor', 'Interaction_Score', 'Dead_Rate', 'Alive_Rate']].tail(10))
    
    return interaction_df

def _embolden_ticks(ax, labelsize: float = 14.0) -> None:
    """Larger, bold tick labels for publication readability."""
    for lab in list(ax.get_xticklabels()) + list(ax.get_yticklabels()):
        lab.set_fontweight("bold")
        lab.set_fontsize(labelsize)


def create_comprehensive_visualizations(stats, mutation_df, synergy_df, clinical_df, interaction_df):
    """
    Create comprehensive visualizations for Dead vs Alive analysis
    """
    print("\n" + "="*80)
    print("CREATING COMPREHENSIVE VISUALIZATIONS")
    print("="*80)
    
    _set_publication_font()
    sns.set_palette("husl")
    
    # Create figure with multiple subplots (reduced from 8 to 6 subplots)
    # Larger canvas + higher DPI improves readability when embedded in PPT.
    fig = plt.figure(figsize=(24, 18))
    
    # 1. Basic Statistics
    ax1 = plt.subplot(3, 2, 1)
    categories = ['Dead', 'Alive']
    counts = [stats['dead_patients'], stats['alive_patients']]
    colors = ['#d62728', '#2ca02c']
    
    bars = ax1.bar(categories, counts, color=colors, alpha=0.7)
    ax1.set_title('Patient Distribution: Dead vs Alive', fontsize=24, fontweight='bold')
    ax1.set_ylabel('Number of Patients', fontsize=19, fontweight='bold')
    
    # Add value labels on bars
    for bar, count in zip(bars, counts):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                f'{count}\n({count/stats["total_patients"]*100:.1f}%)',
                ha='center', va='bottom', fontsize=17, fontweight='bold')
    _embolden_ticks(ax1, 16)
    
    # 2. Genetic Mutations Lethality Ratio
    ax2 = plt.subplot(3, 2, 2)
    # Only force-include genes if they have non-zero counts; otherwise drop them.
    must_include = {'GNAS', 'PIK3CA', 'ATM'}
    if all(c in mutation_df.columns for c in ["Dead_Mutated", "Alive_Mutated"]):
        present_force = set(
            mutation_df.loc[
                (mutation_df["Mutation"].isin(must_include))
                & ((mutation_df["Dead_Mutated"].fillna(0) + mutation_df["Alive_Mutated"].fillna(0)) > 0),
                "Mutation",
            ].tolist()
        )
        must_include = present_force
    top_base = mutation_df.head(10).copy()
    force_rows = mutation_df[mutation_df['Mutation'].isin(must_include)].copy()
    non_forced = top_base[~top_base['Mutation'].isin(must_include)].copy()
    keep_slots = max(0, 10 - len(force_rows))
    top_mutations = (
        pd.concat([force_rows, non_forced.head(keep_slots)], ignore_index=True)
        .drop_duplicates(subset=['Mutation'], keep='first')
        .sort_values('Lethality_Ratio', ascending=False)
    )
    
    ratios_raw = top_mutations['Lethality_Ratio'].astype(float)
    finite = ratios_raw[np.isfinite(ratios_raw)]
    max_finite = finite.max() if len(finite) > 0 else 1.0
    plot_vals = ratios_raw.replace([np.inf, -np.inf], max_finite + 0.6)
    
    bars = ax2.barh(range(len(top_mutations)), plot_vals, 
                   color='#ff7f0e', alpha=0.7)
    ax2.set_yticks(range(len(top_mutations)))
    ax2.set_yticklabels(top_mutations['Mutation'])
    ax2.set_xlabel('Lethality Ratio (Dead Rate / Alive Rate)', fontsize=19, fontweight='bold')
    ax2.set_title('Top 10 Most Lethal Genetic Mutations', fontsize=24, fontweight='bold')
    ax2.grid(axis='x', alpha=0.3)
    ax2.tick_params(axis='y', labelsize=15)
    for lab in ax2.get_yticklabels():
        lab.set_fontweight('bold')
    ax2.set_xlim(0, max_finite + 1.0)
    
    # Add value labels
    for i, (bar, ratio) in enumerate(zip(bars, ratios_raw)):
        label = '∞' if np.isinf(ratio) else f'{ratio:.2f}'
        x_pos = min(bar.get_width() + 0.03, max_finite + 0.85)
        ax2.text(x_pos, bar.get_y() + bar.get_height()/2,
                label, ha='left', va='center', fontsize=15, fontweight='bold')
    _embolden_ticks(ax2, 14)
    
    # 3. Synergy Scores Distribution
    ax3 = plt.subplot(3, 2, 3)
    top_synergy = synergy_df.head(15)
    
    x_pos = np.arange(len(top_synergy))
    bars = ax3.bar(x_pos, top_synergy['Multiplicative_Synergy_Dead'], 
                  color='#1f77b4', alpha=0.7, label='Dead Patients')
    
    ax3.set_xticks(x_pos)
    ax3.set_xticklabels(top_synergy['Combination'], rotation=45, ha='right')
    ax3.set_ylabel('Multiplicative Synergy Score', fontsize=19, fontweight='bold')
    ax3.set_title('Top 15 Genetic Combinations: Multiplicative Synergy', fontsize=24, fontweight='bold')
    ax3.grid(axis='y', alpha=0.3)
    ax3.tick_params(axis='x', labelsize=13)
    _embolden_ticks(ax3, 13)
    
    # Add value labels
    for bar, score in zip(bars, top_synergy['Multiplicative_Synergy_Dead']):
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                f'{score:.1f}', ha='center', va='bottom', fontsize=14, fontweight='bold')
    
    # 4. Additive Scores (requested label change from "Protective" to "Additive")
    ax4 = plt.subplot(3, 2, 4)
    if "Additive_Synergy_Dead" in synergy_df.columns:
        top_additive = synergy_df.sort_values('Additive_Synergy_Dead', ascending=False).head(15)
        yvals = top_additive["Additive_Synergy_Dead"]
        combs = top_additive["Combination"]
    else:
        top_additive = synergy_df.sort_values('Protective_Score', ascending=False).head(15)
        yvals = top_additive["Protective_Score"]
        combs = top_additive["Combination"]
    
    x_pos = np.arange(len(top_additive))
    bars = ax4.bar(x_pos, yvals, 
                  color='#2ca02c', alpha=0.7)
    
    ax4.set_xticks(x_pos)
    ax4.set_xticklabels(combs, rotation=45, ha='right')
    ax4.set_ylabel('Additive Score', fontsize=19, fontweight='bold')
    ax4.set_title('Top 15 Additive Genetic Combinations', fontsize=24, fontweight='bold')
    ax4.grid(axis='y', alpha=0.3)
    ax4.tick_params(axis='x', labelsize=13)
    _embolden_ticks(ax4, 13)
    
    # Add value labels
    for bar, score in zip(bars, yvals):
        height = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                f'{score:.3f}', ha='center', va='bottom', fontsize=14, fontweight='bold')
    
    # 5. Clinical Factors Analysis (requested label: Additive; remove AGE_BIN_ prefix)
    ax5 = plt.subplot(3, 2, 5)
    if clinical_df is None or len(clinical_df) == 0:
        ax5.text(0.5, 0.5, 'Clinical factor panels omitted\n(SEX/RACE/ETHNICITY/PRIMARY_SITE removed)',
                 ha='center', va='center', transform=ax5.transAxes, fontsize=16, fontweight='bold')
        ax5.set_title('Clinical Factors (omitted)', fontsize=24, fontweight='bold')
        ax5.axis('off')
        top_clinical = None
    else:
        top_clinical = clinical_df.head(15)
    
    # Create labels for clinical factors (with abbreviation for long names)
    def abbreviate_clinical_factor(factor):
        """Abbreviate long clinical factor names for better visualization"""
        if 'Borderline Resectable/Locally Advanced' in factor:
            return factor.replace('Borderline Resectable/Locally Advanced', 'Bor. Resec,/Loc.Adv.')
        return factor
    
    if top_clinical is not None:
        labels = []
        for _, row in top_clinical.iterrows():
            # Remove AGE_BIN_ prefix and show only the category label (e.g., 60–69).
            if str(row.get("Factor", "")) == "AGE_BIN":
                labels.append(str(row.get("Value", "")).strip())
            else:
                labels.append(abbreviate_clinical_factor(f"{row['Factor']}_{row['Value']}"))
    
    if top_clinical is not None:
        x_pos = np.arange(len(top_clinical))
        bars = ax5.barh(x_pos, top_clinical['Protective_Score'], 
                       color='#9467bd', alpha=0.7)
    
    if top_clinical is not None:
        ax5.set_yticks(x_pos)
        ax5.set_yticklabels(labels, fontsize=14, fontweight='bold')
        ax5.set_xlabel('Additive Score', fontsize=19, fontweight='bold')
        ax5.set_title('Top 15 Additive Clinical Factors', fontsize=24, fontweight='bold')
        ax5.grid(axis='x', alpha=0.3)
        _embolden_ticks(ax5, 14)
    
    # 6. Genetic-Clinical Interactions
    ax6 = plt.subplot(3, 2, 6)
    if len(interaction_df) > 0:
        top_interactions = interaction_df.head(15)
        
        # Create labels for interactions (with abbreviation for long clinical factor names)
        # abbreviate_clinical_factor function defined above for panel 5
        # Panel F: strip "_BIN" from display only (e.g. AGE_BIN -> AGE).
        interaction_labels = [
            f"{row['Genetic_Combination']}\n+ {abbreviate_clinical_factor(row['Clinical_Factor']).replace('_BIN', '')}"
            for _, row in top_interactions.iterrows()
        ]
        
        x_pos = np.arange(len(top_interactions))
        bars = ax6.bar(x_pos, top_interactions['Interaction_Score'], 
                      color='#e377c2', alpha=0.7)
        
        ax6.set_xticks(x_pos)
        ax6.set_xticklabels(interaction_labels, rotation=45, ha='right', fontsize=13, fontweight='bold')
        ax6.set_ylabel('Interaction Score', fontsize=19, fontweight='bold')
        ax6.set_title('Top 15 Genetic-Clinical Interactions', fontsize=24, fontweight='bold')
        ax6.grid(axis='y', alpha=0.3)
        _embolden_ticks(ax6, 13)
        
        # Add value labels
        for bar, score in zip(bars, top_interactions['Interaction_Score']):
            height = bar.get_height()
            ax6.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                    f'{score:.3f}', ha='center', va='bottom', fontsize=14, fontweight='bold')
    else:
        ax6.text(0.5, 0.5, 'No significant interactions found',
                ha='center', va='center', transform=ax6.transAxes, fontsize=18, fontweight='bold')
        ax6.set_title('Genetic-Clinical Interactions', fontsize=24, fontweight='bold')
    
    # Remove summary and methodology subplots - will add to legend
    # ax7 and ax8 removed - information moved to figure legend
    
    plt.tight_layout(pad=2.0)
    
    # Legend removed as requested - no longer needed
    
    base_dir = '/Users/senol/Desktop/pancreas/survival/New/New 2/PDAC 2025'
    out1 = f'{base_dir}/01_Dead_Alive_Comprehensive_Analysis.png'
    # Also save a copy next to this script (used by the PPT generator).
    out2 = str((Path(__file__).resolve().parent / '01_Dead_Alive_Comprehensive_Analysis.png'))
    plt.savefig(out1, dpi=350, bbox_inches='tight')
    plt.savefig(out2, dpi=350, bbox_inches='tight')
    plt.close()
    
    print(f"✅ Comprehensive visualization saved as: {out1}")
    print(f"✅ Comprehensive visualization saved as: {out2}")

def save_results_to_excel(stats, mutation_df, synergy_df, clinical_df, interaction_df):
    """
    Save all results to Excel file
    """
    print("\n" + "="*80)
    print("SAVING RESULTS TO EXCEL")
    print("="*80)
    
    try:
        base_dir = '/Users/senol/Desktop/pancreas/survival/New/New 2/PDAC 2025'
        with pd.ExcelWriter(f'{base_dir}/Dead_Alive_Comprehensive_Analysis.xlsx', 
                           engine='openpyxl') as writer:
            
            # Summary statistics
            summary_data = {
                'Metric': ['Total Patients', 'Dead Patients', 'Alive Patients', 'Dead Rate (%)', 'Alive Rate (%)'],
                'Value': [stats['total_patients'], stats['dead_patients'], stats['alive_patients'], 
                         stats['dead_rate'], stats['alive_rate']]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary_Statistics', index=False)
            
            # Genetic mutations analysis
            mutation_df.to_excel(writer, sheet_name='Genetic_Mutations', index=False)
            
            # Synergy analysis
            synergy_df.to_excel(writer, sheet_name='Synergy_Analysis', index=False)
            
            # Clinical factors analysis
            clinical_df.to_excel(writer, sheet_name='Clinical_Factors', index=False)
            
            # Genetic-clinical interactions
            if len(interaction_df) > 0:
                interaction_df.to_excel(writer, sheet_name='Genetic_Clinical_Interactions', index=False)
            
            print(f"✅ Results saved to: {base_dir}/Dead_Alive_Comprehensive_Analysis.xlsx")
            
    except Exception as e:
        print(f"❌ Error saving results: {e}")

def main():
    """
    Main function to run Dead vs Alive comprehensive analysis
    """
    print("DEAD VS ALIVE COMPREHENSIVE ANALYSIS")
    print("="*80)
    print(f"Analysis started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load and prepare data
    patient_data, dead_patients, alive_patients = load_and_prepare_data()
    
    if patient_data is None:
        print("❌ Failed to load data. Exiting.")
        return
    
    # Calculate basic statistics
    stats = calculate_basic_statistics(dead_patients, alive_patients)
    
    # Analyze genetic mutations
    mutation_df = analyze_genetic_mutations(dead_patients, alive_patients)
    
    # Calculate synergy scores
    synergy_df = calculate_synergy_scores(dead_patients, alive_patients, mutation_df)
    
    # Analyze clinical factors
    clinical_df = analyze_clinical_factors(dead_patients, alive_patients)
    
    # Comprehensive genetic-clinical analysis
    interaction_df = comprehensive_genetic_clinical_analysis(dead_patients, alive_patients, synergy_df, clinical_df)
    
    # Create visualizations
    create_comprehensive_visualizations(stats, mutation_df, synergy_df, clinical_df, interaction_df)
    
    # Save results
    save_results_to_excel(stats, mutation_df, synergy_df, clinical_df, interaction_df)
    
    print("\n" + "="*80)
    print("ANALYSIS COMPLETED SUCCESSFULLY")
    print("="*80)
    print(f"Analysis finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()