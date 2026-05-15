#!/usr/bin/env python3
"""
Additive Synergy Analysis Visualization
=====================================

This script creates a visualization showing additive synergy results
similar to the multiplicative synergy plot in figure 3.

Author: AI Assistant
Date: 2024
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

def load_synergy_data():
    """
    Load synergy data from the comprehensive analysis
    """
    print("="*80)
    print("LOADING SYNERGY DATA FOR ADDITIVE ANALYSIS")
    print("="*80)
    
    try:
        # Load the comprehensive analysis results
        synergy_df = pd.read_excel('/Users/senol/Desktop/pancreas/survival/New/New 2/Dead_Alive_Comprehensive_Analysis.xlsx', 
                                  sheet_name='Synergy_Analysis')
        print(f"✅ Loaded synergy data: {len(synergy_df)} combinations")
        
        # Filter combinations with sufficient patients
        synergy_df_filtered = synergy_df[synergy_df['Total_Patients'] >= 5].copy()
        print(f"✅ Filtered combinations with ≥5 patients: {len(synergy_df_filtered)}")

        # Canonicalize combination labels so A+B and B+A collapse
        def _canon(combo: str) -> str:
            genes = [g.strip() for g in str(combo).split('+') if g.strip()]
            return '+'.join(sorted(genes))

        synergy_df_filtered['Combination_Canon'] = synergy_df_filtered['Combination'].apply(_canon)

        # Collapse any duplicates produced by ordering differences (or repeated rows)
        agg_cols = {
            'Additive_Synergy_Dead': 'mean',
            'Additive_Synergy_Alive': 'mean',
            'Total_Patients': 'sum',
        }
        for col in ['Multiplicative_Synergy_Dead', 'Multiplicative_Synergy_Alive',
                    'P_Value', 'P_Value_Dead', 'P_Value_Alive',
                    'Odds_Ratio', 'Odds_Ratio_Dead', 'Odds_Ratio_Alive',
                    'Cramers_V']:
            if col in synergy_df_filtered.columns:
                agg_cols[col] = 'mean'

        synergy_df_filtered = (
            synergy_df_filtered
            .groupby('Combination_Canon', as_index=False)
            .agg(agg_cols)
            .rename(columns={'Combination_Canon': 'Combination'})
        )
        print(f"✅ Collapsed to canonical unique combinations: {len(synergy_df_filtered)}")
        
        return synergy_df_filtered
        
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return None

def create_additive_synergy_visualization(synergy_df):
    """
    Create additive synergy visualization similar to figure 3
    """
    print("\n" + "="*80)
    print("CREATING ADDITIVE SYNERGY VISUALIZATION")
    print("="*80)
    
    # Set style
    plt.style.use('default')
    sns.set_palette("husl")
    
    # Create figure with multiple subplots (reduced from 6 to 4 subplots, Panel 6 removed)
    fig = plt.figure(figsize=(22, 16))
    
    # Use GridSpec for better control
    from matplotlib.gridspec import GridSpec
    gs = GridSpec(2, 2, figure=fig, hspace=0.3, wspace=0.3)
    
    # 1. Additive Synergy Scores (Dead Patients) - Similar to Figure 3
    ax1 = fig.add_subplot(gs[0, 0])
    
    top_additive_dead = synergy_df.sort_values('Additive_Synergy_Dead', ascending=False).head(15)
    
    x_pos = np.arange(len(top_additive_dead))
    bars = ax1.bar(x_pos, top_additive_dead['Additive_Synergy_Dead'], 
                  color='#e377c2', alpha=0.7, label='Dead Patients')
    
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels(top_additive_dead['Combination'], rotation=45, ha='right', fontsize=10)
    ax1.set_ylabel('Additive Synergy Score', fontsize=12)
    ax1.set_title('Top 15 Genetic Combinations: Additive Synergy (Dead Patients)', fontsize=14, fontweight='bold')
    ax1.grid(axis='y', alpha=0.3)
    ax1.tick_params(axis='both', labelsize=10)
    
    # Add value labels
    for bar, score in zip(bars, top_additive_dead['Additive_Synergy_Dead']):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                f'{score:.3f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    # 2. Additive Synergy Scores (Alive Patients)
    ax2 = fig.add_subplot(gs[0, 1])
    
    top_additive_alive = synergy_df.sort_values('Additive_Synergy_Alive', ascending=False).head(15)
    
    x_pos = np.arange(len(top_additive_alive))
    bars = ax2.bar(x_pos, top_additive_alive['Additive_Synergy_Alive'], 
                  color='#17becf', alpha=0.7, label='Alive Patients')
    
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(top_additive_alive['Combination'], rotation=45, ha='right', fontsize=10)
    ax2.set_ylabel('Additive Synergy Score', fontsize=12)
    ax2.set_title('Top 15 Genetic Combinations: Additive Synergy (Alive Patients)', fontsize=14, fontweight='bold')
    ax2.grid(axis='y', alpha=0.3)
    ax2.tick_params(axis='both', labelsize=10)
    
    # Add value labels
    for bar, score in zip(bars, top_additive_alive['Additive_Synergy_Alive']):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                f'{score:.3f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    # 3. Comparison: Dead vs Alive Additive Synergy
    ax3 = fig.add_subplot(gs[1, 1])
    
    # Get top 10 combinations for comparison
    top_10_combinations = synergy_df.nlargest(10, 'Total_Patients')
    
    x_pos = np.arange(len(top_10_combinations))
    width = 0.35
    
    bars1 = ax3.bar(x_pos - width/2, top_10_combinations['Additive_Synergy_Dead'], 
                   width, label='Dead Patients', color='#e377c2', alpha=0.7)
    bars2 = ax3.bar(x_pos + width/2, top_10_combinations['Additive_Synergy_Alive'], 
                   width, label='Alive Patients', color='#17becf', alpha=0.7)
    
    ax3.set_xticks(x_pos)
    ax3.set_xticklabels(top_10_combinations['Combination'], rotation=45, ha='right', fontsize=10)
    ax3.set_ylabel('Additive Synergy Score', fontsize=12)
    ax3.set_title('Additive Synergy Comparison: Dead vs Alive (Top 10 by Patient Count)', fontsize=14, fontweight='bold')
    ax3.legend(fontsize=10)
    ax3.grid(axis='y', alpha=0.3)
    ax3.tick_params(axis='both', labelsize=10)
    
    # 4. Additive Synergy Distribution (removed to make space for extended Panel 5)
    # ax4 removed - Panel 5 extended instead
    
    # 5. Most Synergistic vs Most Antagonistic (Extended - Panel 6 removed, Panel 4)
    ax5 = fig.add_subplot(gs[1, 0])
    
    # Get most synergistic (positive) and most antagonistic (negative)
    most_synergistic = synergy_df.nlargest(10, 'Additive_Synergy_Dead')
    most_antagonistic = synergy_df.nsmallest(10, 'Additive_Synergy_Dead')
    
    # Combine, de-duplicate (some combos can appear in both lists), and sort
    extreme_combinations = (
        pd.concat([most_synergistic, most_antagonistic], ignore_index=True)
        .drop_duplicates(subset=['Combination'], keep='first')
        .sort_values('Additive_Synergy_Dead', ascending=False)
    )
    
    colors = ['#2ca02c' if x > 0 else '#d62728' for x in extreme_combinations['Additive_Synergy_Dead']]
    
    bars = ax5.barh(range(len(extreme_combinations)), extreme_combinations['Additive_Synergy_Dead'], 
                   color=colors, alpha=0.7)
    
    ax5.set_yticks(range(len(extreme_combinations)))
    ax5.set_yticklabels(extreme_combinations['Combination'], fontsize=10)
    ax5.set_xlabel('Additive Synergy Score', fontsize=12)
    ax5.set_title('Most Synergistic vs Most Antagonistic Combinations', fontsize=14, fontweight='bold')
    ax5.grid(axis='x', alpha=0.3)
    ax5.axvline(x=0, color='black', linestyle='--', alpha=0.5)
    ax5.tick_params(axis='both', labelsize=10)
    
    # Add value labels
    for i, (bar, score) in enumerate(zip(bars, extreme_combinations['Additive_Synergy_Dead'])):
        ax5.text(bar.get_width() + 0.001 if score >= 0 else bar.get_width() - 0.001, 
                bar.get_y() + bar.get_height()/2,
                f'{score:.3f}', ha='left' if score >= 0 else 'right', va='center', fontweight='bold', fontsize=9)
    
    # Panel 6 removed as requested
    
    plt.tight_layout()
    
    # Summary box removed as requested
    
    plt.savefig('/Users/senol/Desktop/pancreas/survival/New/New 2/04_Additive_Synergy_Analysis.png', 
                dpi=300, bbox_inches='tight')
    plt.show()
    
    print("✅ Additive synergy visualization saved as: 04_Additive_Synergy_Analysis.png")

def print_additive_synergy_results(synergy_df):
    """
    Print detailed additive synergy results
    """
    print("\n" + "="*80)
    print("ADDITIVE SYNERGY DETAILED RESULTS")
    print("="*80)
    
    # Sort by additive synergy (Dead patients)
    synergy_sorted = synergy_df.sort_values('Additive_Synergy_Dead', ascending=False)
    
    print("\nTop 15 Most Synergistic Combinations (Dead Patients):")
    print("="*60)
    for i, (_, row) in enumerate(synergy_sorted.head(15).iterrows(), 1):
        print(f"{i:2d}. {row['Combination']:15s} | "
              f"Dead: {row['Additive_Synergy_Dead']:7.3f} | "
              f"Alive: {row['Additive_Synergy_Alive']:7.3f} | "
              f"Patients: {row['Total_Patients']:3d}")
    
    print("\nTop 15 Most Antagonistic Combinations (Dead Patients):")
    print("="*60)
    for i, (_, row) in enumerate(synergy_sorted.tail(15).iterrows(), 1):
        print(f"{i:2d}. {row['Combination']:15s} | "
              f"Dead: {row['Additive_Synergy_Dead']:7.3f} | "
              f"Alive: {row['Additive_Synergy_Alive']:7.3f} | "
              f"Patients: {row['Total_Patients']:3d}")
    
    print(f"\nSummary Statistics:")
    print(f"Dead Patients - Mean: {synergy_df['Additive_Synergy_Dead'].mean():.3f}, "
          f"Std: {synergy_df['Additive_Synergy_Dead'].std():.3f}")
    print(f"Alive Patients - Mean: {synergy_df['Additive_Synergy_Alive'].mean():.3f}, "
          f"Std: {synergy_df['Additive_Synergy_Alive'].std():.3f}")

def save_additive_synergy_results(synergy_df):
    """
    Save additive synergy results to Excel
    """
    print("\n" + "="*80)
    print("SAVING ADDITIVE SYNERGY RESULTS")
    print("="*80)
    
    try:
        with pd.ExcelWriter('/Users/senol/Desktop/pancreas/survival/New/New 2/Additive_Synergy_Analysis.xlsx', 
                           engine='openpyxl') as writer:
            
            # All additive synergy results
            synergy_df.to_excel(writer, sheet_name='All_Additive_Synergy', index=False)
            
            # Top synergistic combinations
            top_synergistic = synergy_df.nlargest(20, 'Additive_Synergy_Dead')
            top_synergistic.to_excel(writer, sheet_name='Top_Synergistic', index=False)
            
            # Most antagonistic combinations
            most_antagonistic = synergy_df.nsmallest(20, 'Additive_Synergy_Dead')
            most_antagonistic.to_excel(writer, sheet_name='Most_Antagonistic', index=False)
            
            print("✅ Additive synergy results saved to: Additive_Synergy_Analysis.xlsx")
            
    except Exception as e:
        print(f"❌ Error saving results: {e}")

def main():
    """
    Main function to run additive synergy analysis
    """
    print("ADDITIVE SYNERGY ANALYSIS")
    print("="*80)
    print(f"Analysis started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load synergy data
    synergy_df = load_synergy_data()
    
    if synergy_df is None:
        print("❌ Failed to load data. Exiting.")
        return
    
    # Print detailed results
    print_additive_synergy_results(synergy_df)
    
    # Create visualization
    create_additive_synergy_visualization(synergy_df)
    
    # Save results
    save_additive_synergy_results(synergy_df)
    
    print("\n" + "="*80)
    print("ADDITIVE SYNERGY ANALYSIS COMPLETED SUCCESSFULLY")
    print("="*80)
    print(f"Analysis finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()

