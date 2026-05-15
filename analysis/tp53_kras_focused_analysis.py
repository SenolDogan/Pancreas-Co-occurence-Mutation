#!/usr/bin/env python3
"""
TP53 and KRAS Focused Analysis: Dead vs Alive
============================================

This script performs detailed analysis focusing on TP53 and KRAS mutations
and their combinations with third genes in Dead vs Alive patients.

Key Analyses:
1. TP53 and KRAS individual effects in Dead vs Alive
2. TP53+KRAS combination effects
3. TP53+KRAS+Third Gene triple combinations
4. Most lethal and protective triple combinations
5. Synergetic and Multiplicative Synergy scores
6. Comprehensive visualization and reporting

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
from scipy.stats import chi2_contingency, fisher_exact, binomtest
from statsmodels.stats.multitest import multipletests
import warnings
warnings.filterwarnings('ignore')

def load_and_prepare_data():
    """
    Load and prepare data for TP53/KRAS focused analysis
    """
    print("="*80)
    print("LOADING DATA FOR TP53/KRAS FOCUSED ANALYSIS")
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
        
        # Merge all data
        patient_data = patient_survival.merge(patient_mutations, on='Patient_ID')
        patient_data = patient_data.merge(patient_clinical, on='Patient_ID')
        
        # Separate Dead and Alive patients
        dead_patients = patient_data[patient_data['OS_STATUS'] == '1:DECEASED'].copy()
        alive_patients = patient_data[patient_data['OS_STATUS'] == '0:LIVING'].copy()
        
        print(f"\nDead patients: {len(dead_patients)}")
        print(f"Alive patients: {len(alive_patients)}")
        
        return patient_data, dead_patients, alive_patients
        
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return None, None, None

def analyze_tp53_kras_individual_effects(dead_patients, alive_patients):
    """
    Analyze individual TP53 and KRAS effects in Dead vs Alive patients
    """
    print("\n" + "="*80)
    print("TP53 AND KRAS INDIVIDUAL EFFECTS ANALYSIS")
    print("="*80)
    
    results = {}
    
    for gene in ['TP53', 'KRAS']:
        if gene in dead_patients.columns and gene in alive_patients.columns:
            print(f"\n{gene} Analysis:")
            
            # Dead patients
            dead_mutated = dead_patients[dead_patients[gene] == 1]
            dead_wildtype = dead_patients[dead_patients[gene] == 0]
            
            dead_mutated_count = len(dead_mutated)
            dead_wildtype_count = len(dead_wildtype)
            dead_total = len(dead_patients)
            
            dead_mutated_rate = dead_mutated_count / dead_total * 100
            dead_wildtype_rate = dead_wildtype_count / dead_total * 100
            
            # Alive patients
            alive_mutated = alive_patients[alive_patients[gene] == 1]
            alive_wildtype = alive_patients[alive_patients[gene] == 0]
            
            alive_mutated_count = len(alive_mutated)
            alive_wildtype_count = len(alive_wildtype)
            alive_total = len(alive_patients)
            
            alive_mutated_rate = alive_mutated_count / alive_total * 100
            alive_wildtype_rate = alive_wildtype_count / alive_total * 100
            
            # Calculate lethality ratio
            lethality_ratio = dead_mutated_rate / alive_mutated_rate if alive_mutated_rate > 0 else float('inf')
            
            # Calculate protective score
            protective_score = -(dead_mutated_rate - alive_mutated_rate)
            
            print(f"  Dead patients:")
            print(f"    Mutated: {dead_mutated_count}/{dead_total} ({dead_mutated_rate:.1f}%)")
            print(f"    Wildtype: {dead_wildtype_count}/{dead_total} ({dead_wildtype_rate:.1f}%)")
            
            print(f"  Alive patients:")
            print(f"    Mutated: {alive_mutated_count}/{alive_total} ({alive_mutated_rate:.1f}%)")
            print(f"    Wildtype: {alive_wildtype_count}/{alive_total} ({alive_wildtype_rate:.1f}%)")
            
            print(f"  Lethality Ratio: {lethality_ratio:.2f}")
            print(f"  Protective Score: {protective_score:.3f}")
            
            results[gene] = {
                'Dead_Mutated_Count': dead_mutated_count,
                'Dead_Mutated_Rate': dead_mutated_rate,
                'Dead_Wildtype_Count': dead_wildtype_count,
                'Dead_Wildtype_Rate': dead_wildtype_rate,
                'Alive_Mutated_Count': alive_mutated_count,
                'Alive_Mutated_Rate': alive_mutated_rate,
                'Alive_Wildtype_Count': alive_wildtype_count,
                'Alive_Wildtype_Rate': alive_wildtype_rate,
                'Lethality_Ratio': lethality_ratio,
                'Protective_Score': protective_score
            }
    
    return results

def analyze_tp53_kras_combination(dead_patients, alive_patients):
    """
    Analyze TP53+KRAS combination effects
    """
    print("\n" + "="*80)
    print("TP53+KRAS COMBINATION ANALYSIS")
    print("="*80)
    
    # Define all possible combinations
    combinations = [
        ('TP53', 'KRAS', 'Both'),
        ('TP53', 'KRAS', 'TP53_only'),
        ('TP53', 'KRAS', 'KRAS_only'),
        ('TP53', 'KRAS', 'Neither')
    ]
    
    combination_results = []
    
    for mut1, mut2, combo_type in combinations:
        print(f"\n{combo_type} Analysis:")
        
        if combo_type == 'Both':
            # Both mutations
            dead_combo = dead_patients[(dead_patients[mut1] == 1) & (dead_patients[mut2] == 1)]
            alive_combo = alive_patients[(alive_patients[mut1] == 1) & (alive_patients[mut2] == 1)]
        elif combo_type == 'TP53_only':
            # TP53 only
            dead_combo = dead_patients[(dead_patients[mut1] == 1) & (dead_patients[mut2] == 0)]
            alive_combo = alive_patients[(alive_patients[mut1] == 1) & (alive_patients[mut2] == 0)]
        elif combo_type == 'KRAS_only':
            # KRAS only
            dead_combo = dead_patients[(dead_patients[mut1] == 0) & (dead_patients[mut2] == 1)]
            alive_combo = alive_patients[(alive_patients[mut1] == 0) & (alive_patients[mut2] == 1)]
        else:  # Neither
            dead_combo = dead_patients[(dead_patients[mut1] == 0) & (dead_patients[mut2] == 0)]
            alive_combo = alive_patients[(alive_patients[mut1] == 0) & (alive_patients[mut2] == 0)]
        
        dead_count = len(dead_combo)
        alive_count = len(alive_combo)
        dead_total = len(dead_patients)
        alive_total = len(alive_patients)
        
        dead_rate = dead_count / dead_total * 100 if dead_total > 0 else 0
        alive_rate = alive_count / alive_total * 100 if alive_total > 0 else 0
        
        # Calculate lethality ratio
        lethality_ratio = dead_rate / alive_rate if alive_rate > 0 else float('inf')
        
        # Calculate protective score
        protective_score = -(dead_rate - alive_rate)
        
        print(f"  Dead: {dead_count}/{dead_total} ({dead_rate:.1f}%)")
        print(f"  Alive: {alive_count}/{alive_total} ({alive_rate:.1f}%)")
        print(f"  Lethality Ratio: {lethality_ratio:.2f}")
        print(f"  Protective Score: {protective_score:.3f}")
        
        combination_results.append({
            'Combination_Type': combo_type,
            'Dead_Count': dead_count,
            'Dead_Rate': dead_rate,
            'Alive_Count': alive_count,
            'Alive_Rate': alive_rate,
            'Lethality_Ratio': lethality_ratio,
            'Protective_Score': protective_score,
            'Total_Patients': dead_count + alive_count
        })
    
    return pd.DataFrame(combination_results)

def analyze_triple_combinations(dead_patients, alive_patients):
    """
    Analyze TP53+KRAS+Third Gene triple combinations
    """
    print("\n" + "="*80)
    print("TRIPLE COMBINATIONS ANALYSIS: TP53+KRAS+THIRD GENE")
    print("="*80)
    
    # Define third genes to analyze
    third_genes = ['CDKN2A', 'SMAD4', 'ARID1A', 'ATM', 'PIK3CA', 'BRAF', 'GNAS', 'RNF43']
    
    triple_results = []
    
    for third_gene in third_genes:
        if third_gene in dead_patients.columns and third_gene in alive_patients.columns:
            print(f"\nTP53+KRAS+{third_gene} Analysis:")
            
            # Dead patients with all three mutations
            dead_triple = dead_patients[
                (dead_patients['TP53'] == 1) & 
                (dead_patients['KRAS'] == 1) & 
                (dead_patients[third_gene] == 1)
            ]
            dead_triple_count = len(dead_triple)
            dead_total = len(dead_patients)
            dead_triple_rate_pct = dead_triple_count / dead_total * 100 if dead_total > 0 else 0
            dead_triple_rate = dead_triple_count / dead_total if dead_total > 0 else 0  # 0-1 arası for calculations
            
            # Alive patients with all three mutations
            alive_triple = alive_patients[
                (alive_patients['TP53'] == 1) & 
                (alive_patients['KRAS'] == 1) & 
                (alive_patients[third_gene] == 1)
            ]
            alive_triple_count = len(alive_triple)
            alive_total = len(alive_patients)
            alive_triple_rate_pct = alive_triple_count / alive_total * 100 if alive_total > 0 else 0
            alive_triple_rate = alive_triple_count / alive_total if alive_total > 0 else 0  # 0-1 arası for calculations
            
            # Individual mutation rates for synergy calculation (0-1 arası)
            dead_tp53_rate = dead_patients['TP53'].sum() / dead_total if dead_total > 0 else 0
            dead_kras_rate = dead_patients['KRAS'].sum() / dead_total if dead_total > 0 else 0
            dead_third_rate = dead_patients[third_gene].sum() / dead_total if dead_total > 0 else 0
            
            alive_tp53_rate = alive_patients['TP53'].sum() / alive_total if alive_total > 0 else 0
            alive_kras_rate = alive_patients['KRAS'].sum() / alive_total if alive_total > 0 else 0
            alive_third_rate = alive_patients[third_gene].sum() / alive_total if alive_total > 0 else 0
            
            # Individual mutation rates in percentage for additive synergy
            dead_tp53_rate_pct = dead_tp53_rate * 100
            dead_kras_rate_pct = dead_kras_rate * 100
            dead_third_rate_pct = dead_third_rate * 100
            
            alive_tp53_rate_pct = alive_tp53_rate * 100
            alive_kras_rate_pct = alive_kras_rate * 100
            alive_third_rate_pct = alive_third_rate * 100
            
            # Calculate synergy scores
            # Multiplicative synergy for dead patients (using 0-1 rates)
            expected_dead_rate = dead_tp53_rate * dead_kras_rate * dead_third_rate
            expected_dead_rate_pct = expected_dead_rate * 100  # Convert to percentage
            multiplicative_synergy_dead = dead_triple_rate / expected_dead_rate if expected_dead_rate > 0 else 0
            
            # Multiplicative synergy for alive patients (using 0-1 rates)
            expected_alive_rate = alive_tp53_rate * alive_kras_rate * alive_third_rate
            expected_alive_rate_pct = expected_alive_rate * 100  # Convert to percentage
            multiplicative_synergy_alive = alive_triple_rate / expected_alive_rate if expected_alive_rate > 0 else 0
            
            # Additive synergy (DOĞRU YÖNTEM: Observed - Expected Multiplicative)
            # Bu, gerçek farkı gösterir (yüzde puanı cinsinden)
            additive_synergy_dead = dead_triple_rate_pct - expected_dead_rate_pct
            additive_synergy_alive = alive_triple_rate_pct - expected_alive_rate_pct
            
            # Protective score (using percentage rates)
            protective_score = -(dead_triple_rate_pct - alive_triple_rate_pct)
            
            # Lethality ratio (using percentage rates)
            lethality_ratio = dead_triple_rate_pct / alive_triple_rate_pct if alive_triple_rate_pct > 0 else float('inf')
            
            # STATISTICAL TESTS FOR P-VALUES
            
            # Test 1: Panel 3 & 4 - Dead vs Alive comparison (Chi-square or Fisher's exact)
            dead_not_triple = dead_total - dead_triple_count
            alive_not_triple = alive_total - alive_triple_count
            
            contingency_table = np.array([[dead_triple_count, alive_triple_count],
                                         [dead_not_triple, alive_not_triple]])
            
            # Calculate expected values
            total = dead_triple_count + alive_triple_count + dead_not_triple + alive_not_triple
            expected_a = (dead_triple_count + alive_triple_count) * (dead_triple_count + dead_not_triple) / total
            expected_b = (dead_triple_count + alive_triple_count) * (alive_triple_count + alive_not_triple) / total
            expected_c = (dead_not_triple + alive_not_triple) * (dead_triple_count + dead_not_triple) / total
            expected_d = (dead_not_triple + alive_not_triple) * (alive_triple_count + alive_not_triple) / total
            
            min_expected = min(expected_a, expected_b, expected_c, expected_d)
            
            # Choose test for Panel 3 & 4
            if min_expected >= 5 and dead_triple_count + alive_triple_count >= 3:
                chi2_stat, p_value_panel34, dof, expected = chi2_contingency(contingency_table)
                test_type_panel34 = 'Chi-Square'
            elif dead_triple_count + alive_triple_count >= 3:
                odds_ratio, p_value_panel34 = fisher_exact(contingency_table)
                test_type_panel34 = 'Fisher\'s Exact'
            else:
                p_value_panel34 = float('nan')
                test_type_panel34 = 'N/A (n<3)'
            
            # Test 2: Panel 5 & 6 - Multiplicative/Additive Synergy (Goodness-of-fit test)
            expected_triple_count = expected_dead_rate * dead_total
            if dead_triple_count >= 3 and expected_triple_count > 0:
                binom_result = binomtest(dead_triple_count, dead_total, expected_dead_rate, alternative='two-sided')
                p_value_panel56 = binom_result.pvalue
                test_type_panel56 = 'Binomial'
            else:
                p_value_panel56 = float('nan')
                test_type_panel56 = 'N/A (n<3)'
            
            print(f"  Dead: {dead_triple_count}/{dead_total} ({dead_triple_rate_pct:.1f}%)")
            print(f"  Alive: {alive_triple_count}/{alive_total} ({alive_triple_rate_pct:.1f}%)")
            print(f"  Lethality Ratio: {lethality_ratio:.2f}")
            print(f"  Protective Score: {protective_score:.3f}")
            print(f"  Multiplicative Synergy (Dead): {multiplicative_synergy_dead:.2f}x")
            print(f"  Multiplicative Synergy (Alive): {multiplicative_synergy_alive:.2f}x")
            print(f"  Additive Synergy (Dead): {additive_synergy_dead:.3f}")
            print(f"  Additive Synergy (Alive): {additive_synergy_alive:.3f}")
            
            triple_data = {
                'Third_Gene': third_gene,
                'Combination': f"TP53+KRAS+{third_gene}",
                'Dead_Count': dead_triple_count,
                'Dead_Rate': dead_triple_rate_pct,  # Percentage for display
                'Alive_Count': alive_triple_count,
                'Alive_Rate': alive_triple_rate_pct,  # Percentage for display
                'Lethality_Ratio': lethality_ratio,
                'Protective_Score': protective_score,
                'Multiplicative_Synergy_Dead': multiplicative_synergy_dead,
                'Multiplicative_Synergy_Alive': multiplicative_synergy_alive,
                'Additive_Synergy_Dead': additive_synergy_dead,
                'Additive_Synergy_Alive': additive_synergy_alive,
                'Total_Patients': dead_triple_count + alive_triple_count,
                'Dead_TP53_Rate': dead_tp53_rate_pct,  # Percentage for display
                'Dead_KRAS_Rate': dead_kras_rate_pct,  # Percentage for display
                'Dead_Third_Rate': dead_third_rate_pct,  # Percentage for display
                'Alive_TP53_Rate': alive_tp53_rate_pct,  # Percentage for display
                'Alive_KRAS_Rate': alive_kras_rate_pct,  # Percentage for display
                'Alive_Third_Rate': alive_third_rate_pct,  # Percentage for display
                'Panel3_P_Value': p_value_panel34,  # P-value for Panel 3 (Lethality Ratio)
                'Panel4_P_Value': p_value_panel34,  # P-value for Panel 4 (Protective Score)
                'Panel5_P_Value': p_value_panel56,  # P-value for Panel 5 (Multiplicative Synergy)
                'Panel6_P_Value': p_value_panel56,  # P-value for Panel 6 (Additive Synergy)
                'Panel3_Test_Type': test_type_panel34,
                'Panel4_Test_Type': test_type_panel34,
                'Panel5_Test_Type': test_type_panel56,
                'Panel6_Test_Type': test_type_panel56
            }
            
            triple_results.append(triple_data)
    
    triple_df = pd.DataFrame(triple_results)
    
    # Sort by different criteria
    print(f"\nAnalyzed {len(triple_df)} triple combinations")
    
    # Most lethal combinations
    print("\nMost lethal triple combinations (highest lethality ratio):")
    lethal_df = triple_df.sort_values('Lethality_Ratio', ascending=False)
    print(lethal_df[['Third_Gene', 'Lethality_Ratio', 'Dead_Rate', 'Alive_Rate']].head())
    
    # Most protective combinations
    print("\nMost protective triple combinations (highest protective score):")
    protective_df = triple_df.sort_values('Protective_Score', ascending=False)
    print(protective_df[['Third_Gene', 'Protective_Score', 'Dead_Rate', 'Alive_Rate']].head())
    
    # Highest multiplicative synergy
    print("\nHighest multiplicative synergy (Dead patients):")
    synergy_df = triple_df.sort_values('Multiplicative_Synergy_Dead', ascending=False)
    print(synergy_df[['Third_Gene', 'Multiplicative_Synergy_Dead', 'Dead_Rate', 'Alive_Rate']].head())
    
    return triple_df

def create_comprehensive_visualizations(individual_results, combination_df, triple_df):
    """
    Create comprehensive visualizations for TP53/KRAS analysis
    """
    print("\n" + "="*80)
    print("CREATING COMPREHENSIVE VISUALIZATIONS")
    print("="*80)
    
    # Set style - Times New Roman, larger bold defaults (manuscript figures)
    apply_manuscript_figure_style()
    sns.set_palette("husl")
    
    # Create figure with multiple subplots (reduced from 8 to 6 subplots)
    fig = plt.figure(figsize=(20, 18))
    
    # 1. Individual TP53 and KRAS Effects
    ax1 = plt.subplot(3, 2, 1)
    genes = ['TP53', 'KRAS']
    lethality_ratios = [individual_results[gene]['Lethality_Ratio'] for gene in genes]
    
    bars = ax1.bar(genes, lethality_ratios, color=['#ff7f0e', '#2ca02c'], alpha=0.7)
    ax1.set_title('TP53 and KRAS Individual Lethality Ratios', fontsize=16, fontweight='bold')
    ax1.set_ylabel('Lethality Ratio (Dead Rate / Alive Rate)')
    ax1.grid(axis='y', alpha=0.3)
    
    # Add value labels
    for bar, ratio in zip(bars, lethality_ratios):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                f'{ratio:.2f}', ha='center', va='bottom', fontweight='bold')
    
    # 2. TP53+KRAS Combination Types
    ax2 = plt.subplot(3, 2, 2)
    combo_types = combination_df['Combination_Type']
    combo_ratios = combination_df['Lethality_Ratio']
    
    bars = ax2.bar(range(len(combo_types)), combo_ratios, color='#1f77b4', alpha=0.7)
    ax2.set_xticks(range(len(combo_types)))
    ax2.set_xticklabels(combo_types, rotation=45, ha='right')
    ax2.set_ylabel('Lethality Ratio')
    ax2.set_title('TP53+KRAS Combination Types: Lethality Ratios', fontsize=16, fontweight='bold')
    ax2.grid(axis='y', alpha=0.3)
    
    # Add value labels
    for bar, ratio in zip(bars, combo_ratios):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                f'{ratio:.2f}', ha='center', va='bottom', fontweight='bold')
    
    # 3. Triple Combinations Lethality Ratios
    ax3 = plt.subplot(3, 2, 3)
    
    # Handle infinite values for plotting
    triple_df_plot = triple_df.copy()
    triple_df_plot['Lethality_Ratio_Plot'] = triple_df_plot['Lethality_Ratio'].replace([np.inf, -np.inf], np.nan)
    
    # Sort by lethality ratio, handling infinite values
    triple_lethal = triple_df_plot.sort_values('Lethality_Ratio_Plot', ascending=False, na_position='last')
    
    # Create bars with finite values
    finite_ratios = triple_lethal['Lethality_Ratio_Plot'].fillna(0)
    bars = ax3.barh(range(len(triple_lethal)), finite_ratios, 
                   color='#d62728', alpha=0.7)
    
    ax3.set_yticks(range(len(triple_lethal)))
    ax3.set_yticklabels(triple_lethal['Third_Gene'])
    ax3.set_xlabel('Lethality Ratio')
    ax3.set_title('Triple Combinations: Lethality Ratios', fontsize=16, fontweight='bold')
    ax3.grid(axis='x', alpha=0.3)
    
    # Add value labels with special handling for infinite values
    for i, (bar, ratio) in enumerate(zip(bars, triple_lethal['Lethality_Ratio'])):
        if np.isinf(ratio):
            ax3.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2,
                    '∞', ha='left', va='center', fontweight='bold', fontsize=12)
        else:
            ax3.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2,
                    f'{ratio:.2f}', ha='left', va='center', fontweight='bold')
    
    # 4. Triple Combinations Protective Scores
    ax4 = plt.subplot(3, 2, 4)
    triple_protective = triple_df.sort_values('Protective_Score', ascending=False)
    
    bars = ax4.barh(range(len(triple_protective)), triple_protective['Protective_Score'], 
                   color='#2ca02c', alpha=0.7)
    ax4.set_yticks(range(len(triple_protective)))
    ax4.set_yticklabels(triple_protective['Third_Gene'])
    ax4.set_xlabel('Protective Score')
    ax4.set_title('Triple Combinations: Protective Scores', fontsize=16, fontweight='bold')
    ax4.grid(axis='x', alpha=0.3)
    
    # Add value labels
    for i, (bar, score) in enumerate(zip(bars, triple_protective['Protective_Score'])):
        ax4.text(bar.get_width() + 0.001, bar.get_y() + bar.get_height()/2,
                f'{score:.3f}', ha='left', va='center', fontweight='bold')
    
    # 5. Multiplicative Synergy Scores
    ax5 = plt.subplot(3, 2, 5)
    triple_synergy = triple_df.sort_values('Multiplicative_Synergy_Dead', ascending=False)
    
    x_pos = np.arange(len(triple_synergy))
    bars = ax5.bar(x_pos, triple_synergy['Multiplicative_Synergy_Dead'], 
                  color='#9467bd', alpha=0.7)
    
    ax5.set_xticks(x_pos)
    # Replace p-values with patient counts (n)
    xticklabels = []
    for _, row in triple_synergy.iterrows():
        gene = row['Third_Gene']
        n_patients = int(row.get('Total_Patients', row.get('Dead_Count', 0) + row.get('Alive_Count', 0)))
        xticklabels.append(f'{gene}\n(n={n_patients})')
    ax5.set_xticklabels(xticklabels, rotation=45, ha='right', fontsize=12)
    ax5.set_ylabel('Multiplicative Synergy Score')
    ax5.set_title('Triple Combinations: Multiplicative Synergy', fontsize=16, fontweight='bold')
    ax5.grid(axis='y', alpha=0.3)
    
    # Add value labels
    for bar, score in zip(bars, triple_synergy['Multiplicative_Synergy_Dead']):
        height = bar.get_height()
        ax5.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                f'{score:.2f}x', ha='center', va='bottom', fontsize=12, fontweight='bold')
    
    # 6. Additive Synergy Scores
    ax6 = plt.subplot(3, 2, 6)
    triple_additive = triple_df.sort_values('Additive_Synergy_Dead', ascending=False)
    
    x_pos = np.arange(len(triple_additive))
    bars = ax6.bar(x_pos, triple_additive['Additive_Synergy_Dead'], 
                  color='#e377c2', alpha=0.7)
    
    ax6.set_xticks(x_pos)
    # Replace p-values with patient counts (n)
    xticklabels = []
    for _, row in triple_additive.iterrows():
        gene = row['Third_Gene']
        n_patients = int(row.get('Total_Patients', row.get('Dead_Count', 0) + row.get('Alive_Count', 0)))
        xticklabels.append(f'{gene}\n(n={n_patients})')
    ax6.set_xticklabels(xticklabels, rotation=45, ha='right', fontsize=12)
    ax6.set_ylabel('Additive Synergy Score')
    ax6.set_title('Triple Combinations: Additive Synergy', fontsize=16, fontweight='bold')
    ax6.grid(axis='y', alpha=0.3)
    
    # Add value labels
    for bar, score in zip(bars, triple_additive['Additive_Synergy_Dead']):
        height = bar.get_height()
        ax6.text(bar.get_x() + bar.get_width()/2., height + abs(height)*0.01,
                f'{score:.2f}%', ha='center', va='bottom', fontsize=12, fontweight='bold')
    
    # Remove summary and methodology subplots - will add to legend
    # ax7 and ax8 removed - information moved to figure legend
    
    # Summary legend removed as requested - text was overlapping
    
    plt.tight_layout()
    
    plt.savefig('/Users/senol/Desktop/pancreas/survival/New/New 2/02_TP53_KRAS_Focused_Analysis.png', 
                dpi=300, bbox_inches='tight')
    plt.show()
    
    print("✅ Comprehensive visualization saved as: 02_TP53_KRAS_Focused_Analysis.png")

def save_results_to_excel(individual_results, combination_df, triple_df):
    """
    Save all results to Excel file
    """
    print("\n" + "="*80)
    print("SAVING RESULTS TO EXCEL")
    print("="*80)
    
    try:
        with pd.ExcelWriter('/Users/senol/Desktop/pancreas/survival/New/New 2/TP53_KRAS_Focused_Analysis.xlsx', 
                           engine='openpyxl') as writer:
            
            # Individual effects
            individual_data = []
            for gene, data in individual_results.items():
                individual_data.append({
                    'Gene': gene,
                    'Dead_Mutated_Count': data['Dead_Mutated_Count'],
                    'Dead_Mutated_Rate': data['Dead_Mutated_Rate'],
                    'Alive_Mutated_Count': data['Alive_Mutated_Count'],
                    'Alive_Mutated_Rate': data['Alive_Mutated_Rate'],
                    'Lethality_Ratio': data['Lethality_Ratio'],
                    'Protective_Score': data['Protective_Score']
                })
            
            individual_df = pd.DataFrame(individual_data)
            individual_df.to_excel(writer, sheet_name='Individual_Effects', index=False)
            
            # Combination analysis
            combination_df.to_excel(writer, sheet_name='TP53_KRAS_Combinations', index=False)
            
            # Triple combinations analysis
            triple_df.to_excel(writer, sheet_name='Triple_Combinations', index=False)
            
            print("✅ Results saved to: TP53_KRAS_Focused_Analysis.xlsx")
            
    except Exception as e:
        print(f"❌ Error saving results: {e}")

def main():
    """
    Main function to run TP53/KRAS focused analysis
    """
    print("TP53 AND KRAS FOCUSED ANALYSIS: DEAD VS ALIVE")
    print("="*80)
    print(f"Analysis started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load and prepare data
    patient_data, dead_patients, alive_patients = load_and_prepare_data()
    
    if patient_data is None:
        print("❌ Failed to load data. Exiting.")
        return
    
    # Analyze individual TP53 and KRAS effects
    individual_results = analyze_tp53_kras_individual_effects(dead_patients, alive_patients)
    
    # Analyze TP53+KRAS combinations
    combination_df = analyze_tp53_kras_combination(dead_patients, alive_patients)
    
    # Analyze triple combinations
    triple_df = analyze_triple_combinations(dead_patients, alive_patients)
    
    # Create visualizations
    create_comprehensive_visualizations(individual_results, combination_df, triple_df)
    
    # Save results
    save_results_to_excel(individual_results, combination_df, triple_df)
    
    print("\n" + "="*80)
    print("ANALYSIS COMPLETED SUCCESSFULLY")
    print("="*80)
    print(f"Analysis finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
