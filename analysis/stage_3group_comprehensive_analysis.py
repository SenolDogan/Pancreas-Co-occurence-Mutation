#!/usr/bin/env python3
"""
Stage (3-group) Comprehensive Analysis
=====================================

This script reproduces the spirit of the previous "Dead vs Alive" panels, but
compares the 3 clinical stage groups instead:
  - Metastatic
  - Resectable
  - Borderline Resectable/Locally Advanced

Input:
  Tumor/Merged.xlsx (Sheet1)  (mutation-level rows; clinical columns repeated)

Outputs (all written under Tumor/):
  - Stage_3Group_Comprehensive_Analysis.png
  - Stage_3Group_Comprehensive_Analysis.xlsx
  - Stage_3Group_Top_Synergy_ByStage.xlsx (optional convenience)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg", force=True)
import matplotlib.pyplot as plt
import seaborn as sns
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "tumor"))
from manuscript_figure_style import apply_manuscript_figure_style, shorten_stage_labels_on_axes, short_stage_label


def _set_publication_font() -> None:
    apply_manuscript_figure_style()


STAGES = [
    "Metastatic",
    "Resectable",
    "Borderline Resectable/Locally Advanced",
]

# Metastatik: koyu turuncu (#E65100); Resectable: yesil (#2E7D32); Borderline/LA: acik sari (#FFEE58).
STAGE_COLORS = {
    "Metastatic": "#E65100",
    "Resectable": "#2E7D32",
    "Borderline Resectable/Locally Advanced": "#FFEE58",
}
STAGE_PALETTE = [STAGE_COLORS[s] for s in STAGES]
STAGE_PALETTE_DICT = dict(zip(STAGES, STAGE_PALETTE))

TARGET_GENES = [
    "TP53",
    "KRAS",
    "CDKN2A",
    "SMAD4",
    "ARID1A",
    "ATM",
    "PIK3CA",
    "BRAF",
    "GNAS",
    "RNF43",
]


@dataclass(frozen=True)
class Paths:
    base_dir: Path
    tumor_dir: Path
    merged_xlsx: Path
    out_png: Path
    out_xlsx: Path
    out_synergy_xlsx: Path


def get_paths() -> Paths:
    base_dir = Path(__file__).resolve().parent
    tumor_dir = base_dir / "tumor"
    merged_xlsx = tumor_dir / "Merged.xlsx"
    return Paths(
        base_dir=base_dir,
        tumor_dir=tumor_dir,
        merged_xlsx=merged_xlsx,
        out_png=tumor_dir / "Stage_3Group_Comprehensive_Analysis.png",
        out_xlsx=tumor_dir / "Stage_3Group_Comprehensive_Analysis.xlsx",
        out_synergy_xlsx=tumor_dir / "Stage_3Group_Top_Synergy_ByStage.xlsx",
    )


def load_patient_level_data(merged_xlsx: Path) -> pd.DataFrame:
    df = pd.read_excel(merged_xlsx, sheet_name=0)

    required = {"PATIENT_ID", "Hugo_Symbol", "STAGE"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in merged dataset: {sorted(missing)}")

    # Patient-level survival/clinical columns are duplicated across mutation rows; take first.
    clinical_cols = [
        "PATIENT_ID",
        "STAGE",
        "SEX",
        "ANCESTRY",
        "AGE",
        "OS_MONTHS",
        "OS_STATUS",
        "TOBACCO_EXPOSURE",
        "DIABETES_HISOTRY",
        "TUMOR_LOCATION",
        "GENOMIC_GROUP",
        "WGD",
        "ALLELIC_IMBALANCE",
    ]
    clinical_cols = [c for c in clinical_cols if c in df.columns]

    patient_clinical = df.groupby("PATIENT_ID")[clinical_cols].first().reset_index(drop=True)

    # Mutation presence (binary) for target genes.
    patient_genes = df.groupby("PATIENT_ID")["Hugo_Symbol"].apply(list).reset_index()
    for g in TARGET_GENES:
        patient_genes[g] = patient_genes["Hugo_Symbol"].apply(lambda xs: 1 if g in xs else 0)
    patient_genes = patient_genes.drop(columns=["Hugo_Symbol"])

    patient_data = patient_clinical.merge(patient_genes, on="PATIENT_ID", how="inner")

    # Keep only the 3 stage groups of interest.
    patient_data["STAGE"] = patient_data["STAGE"].astype(str)
    patient_data = patient_data[patient_data["STAGE"].isin(STAGES)].copy()
    patient_data.reset_index(drop=True, inplace=True)

    return patient_data


def split_by_stage(patient_data: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    out = {}
    for s in STAGES:
        out[s] = patient_data[patient_data["STAGE"] == s].copy()
    return out


def _to_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def basic_stats_by_stage(stage_dfs: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    total = sum(len(df) for df in stage_dfs.values())
    for stage, sdf in stage_dfs.items():
        row = {
            "Stage": stage,
            "Patients": len(sdf),
            "Percent": (len(sdf) / total * 100.0) if total else 0.0,
        }
        if "AGE" in sdf.columns:
            age = _to_numeric(sdf["AGE"])
            row.update(
                {
                    "Age_Mean": float(age.mean()) if age.notna().any() else np.nan,
                    "Age_Median": float(age.median()) if age.notna().any() else np.nan,
                }
            )
        if "OS_MONTHS" in sdf.columns:
            os_m = _to_numeric(sdf["OS_MONTHS"])
            row.update(
                {
                    "OS_MONTHS_Median": float(os_m.median()) if os_m.notna().any() else np.nan,
                    "OS_MONTHS_Q1": float(os_m.quantile(0.25)) if os_m.notna().any() else np.nan,
                    "OS_MONTHS_Q3": float(os_m.quantile(0.75)) if os_m.notna().any() else np.nan,
                }
            )
        rows.append(row)
    return pd.DataFrame(rows).sort_values("Patients", ascending=False).reset_index(drop=True)


def mutation_rates_by_stage(stage_dfs: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for gene in TARGET_GENES:
        if any(gene not in sdf.columns for sdf in stage_dfs.values()):
            continue
        for stage, sdf in stage_dfs.items():
            total = len(sdf)
            mutated = int(sdf[gene].sum())
            rate = (mutated / total * 100.0) if total else 0.0
            rows.append(
                {
                    "Gene": gene,
                    "Stage": stage,
                    "Mutated": mutated,
                    "Total": total,
                    "Rate_Percent": rate,
                }
            )
    mdf = pd.DataFrame(rows)

    # Convenience ratios relative to Resectable (if present).
    pivot = mdf.pivot_table(index="Gene", columns="Stage", values="Rate_Percent", aggfunc="first")
    if "Resectable" in pivot.columns:
        for st in STAGES:
            if st == "Resectable" or st not in pivot.columns:
                continue
            pivot[f"Ratio_{st}_vs_Resectable"] = pivot[st] / pivot["Resectable"].replace(0, np.nan)
    pivot = pivot.reset_index()
    return mdf, pivot


def _combo_rate(df: pd.DataFrame, a: str, b: str) -> Tuple[int, float]:
    both = df[(df[a] == 1) & (df[b] == 1)]
    count = len(both)
    total = len(df)
    rate = (count / total) if total else 0.0
    return count, rate


def synergy_by_stage(stage_dfs: Dict[str, pd.DataFrame], min_patients: int = 5) -> Dict[str, pd.DataFrame]:
    out = {}
    for stage, sdf in stage_dfs.items():
        rows = []
        total = len(sdf)
        if total == 0:
            out[stage] = pd.DataFrame()
            continue
        for i, g1 in enumerate(TARGET_GENES):
            for j, g2 in enumerate(TARGET_GENES):
                if i >= j:
                    continue
                if g1 not in sdf.columns or g2 not in sdf.columns:
                    continue
                both_count, both_rate = _combo_rate(sdf, g1, g2)
                if both_count < min_patients:
                    continue
                r1 = float(sdf[g1].sum()) / total
                r2 = float(sdf[g2].sum()) / total
                expected = r1 * r2
                mult_synergy = (both_rate / expected) if expected > 0 else 0.0
                add_synergy = both_rate - (r1 + r2)
                rows.append(
                    {
                        "Stage": stage,
                        "Combination": f"{g1}+{g2}",
                        "Both_Count": both_count,
                        "Stage_Total": total,
                        "Both_Rate": both_rate,
                        "Gene1_Rate": r1,
                        "Gene2_Rate": r2,
                        "Expected_Rate": expected,
                        "Multiplicative_Synergy": mult_synergy,
                        "Additive_Synergy": add_synergy,
                    }
                )
        sdf_out = pd.DataFrame(rows)
        if len(sdf_out):
            sdf_out = sdf_out.sort_values("Multiplicative_Synergy", ascending=False).reset_index(drop=True)
        out[stage] = sdf_out
    return out


def clinical_factor_stage_association(patient_data: pd.DataFrame, factors: List[str]) -> pd.DataFrame:
    """
    For each factor/value and each stage, compute:
      - Rate_in_stage = % of patients in that stage with this factor=value
      - Rate_outside_stage = % of patients in all other stages with this factor=value
      - Association_Score = Rate_in_stage - Rate_outside_stage  (percentage points, pp)
    """
    rows = []
    for factor in factors:
        if factor not in patient_data.columns:
            continue
        # treat NaN as 'Missing' for transparent reporting
        vals = patient_data[factor].copy()
        vals = vals.where(vals.notna(), "Missing")
        for stage in STAGES:
            in_stage = patient_data["STAGE"] == stage
            out_stage = ~in_stage
            denom_in = int(in_stage.sum())
            denom_out = int(out_stage.sum())
            if denom_in == 0 or denom_out == 0:
                continue
            vc_in = vals[in_stage].value_counts()
            vc_out = vals[out_stage].value_counts()
            all_values = set(vc_in.index) | set(vc_out.index)
            for v in all_values:
                c_in = int(vc_in.get(v, 0))
                c_out = int(vc_out.get(v, 0))
                r_in = c_in / denom_in * 100.0
                r_out = c_out / denom_out * 100.0
                rows.append(
                    {
                        "Stage": stage,
                        "Factor": factor,
                        "Value": v,
                        "InStage_Count": c_in,
                        "InStage_Rate": r_in,
                        "OutStage_Count": c_out,
                        "OutStage_Rate": r_out,
                        "Association_Score": r_in - r_out,
                    }
                )
    out = pd.DataFrame(rows)
    if len(out):
        out = out.sort_values(["Stage", "Association_Score"], ascending=[True, False]).reset_index(drop=True)
    return out


def genetic_clinical_interactions_within_stage(
    stage_df: pd.DataFrame,
    synergy_df: pd.DataFrame,
    assoc_df: pd.DataFrame,
    stage: str,
    top_combo_n: int = 10,
    top_factor_n: int = 10,
    min_patients: int = 3,
) -> pd.DataFrame:
    """
    Within a stage, evaluate how often (combo + clinical value) co-occur compared to
    expectation under independence.
      Interaction_Score = Observed_Both_Rate / Expected_Both_Rate
    """
    if len(stage_df) == 0 or len(synergy_df) == 0 or len(assoc_df) == 0:
        return pd.DataFrame()

    top_combos = synergy_df.head(top_combo_n)["Combination"].astype(str).tolist()
    # Ensure CDKN2A+BRAF × Other-MAPK-MUT can appear in Panel F (often very high interaction score).
    _prio_combo = "CDKN2A+BRAF"
    if _prio_combo in top_combos:
        top_combos = [_prio_combo] + [c for c in top_combos if c != _prio_combo]
    else:
        rest = [c for c in top_combos if c != _prio_combo]
        top_combos = [_prio_combo] + rest[: max(0, top_combo_n - 1)]
    top_combos = top_combos[:top_combo_n]

    top_factors = (
        assoc_df[assoc_df["Stage"] == stage]
        .sort_values("Association_Score", ascending=False)
        .head(top_factor_n)[["Factor", "Value"]]
        .to_records(index=False)
        .tolist()
    )
    # Ensure Other-MAPK-MUT genomic subgroup is evaluated with CDKN2A+BRAF for Panel F.
    _mapk_pair = ("GENOMIC_GROUP", "Other-MAPK-MUT")

    def _factors_include_mapk(factors: list) -> bool:
        for fac, val in factors:
            if str(fac) == "GENOMIC_GROUP" and "Other-MAPK-MUT" in str(val):
                return True
        return False

    if "GENOMIC_GROUP" in stage_df.columns and not _factors_include_mapk(top_factors):
        top_factors = [_mapk_pair] + [t for t in top_factors if not (str(t[0]) == "GENOMIC_GROUP" and "Other-MAPK-MUT" in str(t[1]))][
            : max(0, top_factor_n - 1)
        ]

    rows = []
    total = len(stage_df)
    for combo in top_combos:
        g1, g2 = combo.split("+")
        if g1 not in stage_df.columns or g2 not in stage_df.columns:
            continue
        combo_mask = (stage_df[g1] == 1) & (stage_df[g2] == 1)
        combo_rate = combo_mask.mean() if total else 0.0
        for factor, value in top_factors:
            if factor not in stage_df.columns:
                continue
            fac_series = stage_df[factor].where(stage_df[factor].notna(), "Missing").astype(str)
            fac_mask = fac_series == str(value)
            fac_rate = fac_mask.mean() if total else 0.0

            both_mask = combo_mask & fac_mask
            both_count = int(both_mask.sum())
            if both_count < min_patients:
                continue
            both_rate = both_count / total
            expected = combo_rate * fac_rate
            score = (both_rate / expected) if expected > 0 else np.nan
            rows.append(
                {
                    "Stage": stage,
                    "Genetic_Combination": combo,
                    "Clinical": f"{factor}={value}",
                    "Both_Count": both_count,
                    "Both_Rate": both_rate,
                    "Expected_Rate": expected,
                    "Interaction_Score": score,
                }
            )
    out = pd.DataFrame(rows)
    if len(out):
        out = out.sort_values("Interaction_Score", ascending=False).reset_index(drop=True)
    return out


def create_visualization(
    stats_df: pd.DataFrame,
    mutation_long: pd.DataFrame,
    mutation_pivot: pd.DataFrame,
    synergy_by_st: Dict[str, pd.DataFrame],
    assoc_df: pd.DataFrame,
    interactions: pd.DataFrame,
    out_png: Path,
) -> None:
    apply_manuscript_figure_style()
    sns.set_palette("husl")

    fig = plt.figure(figsize=(26, 18))

    # 1) Patient distribution by stage
    ax1 = plt.subplot(3, 2, 1)
    n = len(stats_df)
    xpos = np.arange(n)
    stages_list = stats_df["Stage"].astype(str).tolist()
    ax1.bar(
        xpos,
        stats_df["Patients"],
        color=[STAGE_COLORS.get(str(s), "#888888") for s in stages_list],
        alpha=0.75,
    )
    ax1.set_xticks(xpos)
    ax1.set_xticklabels([short_stage_label(s) for s in stages_list], rotation=18)
    ax1.set_title("Patient Distribution by Stage", fontweight="bold")
    ax1.set_ylabel("Number of Patients")
    ymax = max(stats_df["Patients"]) if len(stats_df) else 0
    for pos, (_, r) in enumerate(stats_df.iterrows()):
        ax1.text(
            pos,
            r["Patients"] + ymax * 0.01,
            f"{int(r['Patients'])}\n({r['Percent']:.1f}%)",
            ha="center",
            va="bottom",
            fontweight="bold",
        )

    # 2) Top genes enriched in Metastatic vs Resectable (ratio)
    ax2 = plt.subplot(3, 2, 2)
    col_ratio = "Ratio_Metastatic_vs_Resectable"
    if col_ratio in mutation_pivot.columns:
        top = mutation_pivot[["Gene", col_ratio]].dropna().sort_values(col_ratio, ascending=False).head(10)
        vals = top[col_ratio].replace([np.inf, -np.inf], np.nan).fillna(0.0)
        ax2.barh(top["Gene"], vals, color="#ff7f0e", alpha=0.75)
        ax2.set_xlabel("Rate Ratio (Metastatic / Resectable)")
        ax2.set_title("Top 10 Genes Enriched in Metastatic Stage", fontweight="bold")
        ax2.grid(axis="x", alpha=0.25)
        ax2.invert_yaxis()
    else:
        ax2.text(0.5, 0.5, "Ratio Metastatic/Resectable not available", ha="center", va="center", transform=ax2.transAxes)
        ax2.set_title("Gene Enrichment", fontweight="bold")

    # 3) Top synergy in each stage (Metastatic shown)
    ax3 = plt.subplot(3, 2, 3)
    meta = synergy_by_st.get("Metastatic", pd.DataFrame())
    if len(meta):
        top = meta.head(12)
        ax3.bar(np.arange(len(top)), top["Multiplicative_Synergy"], color="#9467bd", alpha=0.75)
        ax3.set_xticks(np.arange(len(top)))
        ax3.set_xticklabels(top["Combination"], rotation=45, ha="right")
        ax3.set_ylabel("Multiplicative Synergy")
        ax3.set_title("Top Synergistic Combinations (Metastatic)", fontweight="bold")
        ax3.grid(axis="y", alpha=0.25)
    else:
        ax3.text(0.5, 0.5, "No synergy combos (>=5 patients) in Metastatic", ha="center", va="center", transform=ax3.transAxes)
        ax3.set_title("Synergy (Metastatic)", fontweight="bold")

    # 4) Compare synergy for top metastatic combos across stages
    ax4 = plt.subplot(3, 2, 4)
    if len(meta):
        top_combos = meta.head(8)["Combination"].tolist()
        comp_rows = []
        for st in STAGES:
            sdf = synergy_by_st.get(st, pd.DataFrame())
            if len(sdf) == 0:
                continue
            sdf = sdf[sdf["Combination"].isin(top_combos)][["Combination", "Multiplicative_Synergy"]].copy()
            sdf["Stage"] = st
            comp_rows.append(sdf)
        if comp_rows:
            comp = pd.concat(comp_rows, ignore_index=True)
            sns.barplot(
                data=comp,
                x="Combination",
                y="Multiplicative_Synergy",
                hue="Stage",
                hue_order=STAGES,
                ax=ax4,
                palette=STAGE_PALETTE_DICT,
            )
            ax4.set_title("Synergy Comparison Across Stages (Top Metastatic Combos)", fontweight="bold")
            ax4.set_ylabel("Multiplicative Synergy")
            ax4.set_xlabel("")
            ax4.tick_params(axis="x", rotation=45)
            ax4.grid(axis="y", alpha=0.25)
            ax4.legend(title="Stage", loc="best")
            shorten_stage_labels_on_axes(ax4)
        else:
            ax4.text(0.5, 0.5, "Not enough data to compare stages", ha="center", va="center", transform=ax4.transAxes)
            ax4.set_title("Synergy Comparison", fontweight="bold")
    else:
        ax4.text(0.5, 0.5, "No metastatic synergy results", ha="center", va="center", transform=ax4.transAxes)
        ax4.set_title("Synergy Comparison", fontweight="bold")

    # 5) Clinical factor association with Metastatic (top)
    ax5 = plt.subplot(3, 2, 5)
    meta_assoc = assoc_df[assoc_df["Stage"] == "Metastatic"].copy() if len(assoc_df) else pd.DataFrame()
    if len(meta_assoc):
        # Panel E label cleanup (publication-facing): remove requested noisy labels and missing-only entries
        drop_factors = {"ANCESTRY", "SEX"}
        meta_assoc = meta_assoc[~meta_assoc["Factor"].astype(str).isin(drop_factors)].copy()

        # Drop specific value-level labels
        fac = meta_assoc["Factor"].astype(str)
        val = meta_assoc["Value"].astype(str)
        is_missing = val.str.lower().eq("missing")
        meta_assoc = meta_assoc[~((fac == "GENOMIC_GROUP") & val.str.lower().eq("other"))].copy()
        meta_assoc = meta_assoc[~((fac.isin(["TUMOR_LOCATION", "TOBACCO_EXPOSURE", "DIABETES_HISOTRY"])) & is_missing)].copy()
        # Drop WGD missing entirely (remove the value and its bar)
        meta_assoc = meta_assoc[~((fac == "WGD") & is_missing)].copy()
        # refresh views after filtering
        fac = meta_assoc["Factor"].astype(str)

        # Rename factor/value display labels
        factor_display = {
            "ALLELIC_IMBALANCE": "All.Imb.",
            "TUMOR_LOCATION": "Tum.Loc.",
            "GENOMIC_GROUP": "Gen.Gr.",
            "DIABETES_HISOTRY": "Diab.His",
            "TOBACCO_EXPOSURE": "Tob.Exp.",
        }
        meta_assoc["Factor_Display"] = (
            meta_assoc["Factor"].astype(str).map(factor_display).fillna(meta_assoc["Factor"].astype(str))
        )

        # Value recoding rules
        val_raw = meta_assoc["Value"].astype(str)
        val_norm = val_raw.copy()
        # Genomic group: shorten specific token
        val_norm = val_norm.where(~((fac == "GENOMIC_GROUP") & (val_raw == "Other-MAPK-MUT")), "Other")
        # WGD: map 1.0/0.0 to Yes/No, drop missing already done above
        val_norm = val_norm.where(~((fac == "WGD") & (val_raw.isin(["1.0", "1", "True"]))), "Yes")
        val_norm = val_norm.where(~((fac == "WGD") & (val_raw.isin(["0.0", "0", "False"]))), "No")
        # Diabetes history: map common numeric encodings to Yes/No
        val_norm = val_norm.where(~((fac == "DIABETES_HISOTRY") & (val_raw.isin(["1.0", "1", "True"]))), "Yes")
        val_norm = val_norm.where(~((fac == "DIABETES_HISOTRY") & (val_raw.isin(["0.0", "0", "False"]))), "No")

        meta_assoc["Value_Display"] = val_norm
        meta_assoc["Label"] = meta_assoc["Factor_Display"].astype(str) + "=" + meta_assoc["Value_Display"].astype(str)

        top = meta_assoc.sort_values("Association_Score", ascending=False).head(12)
        ax5.barh(top["Label"], top["Association_Score"], color="#2ca02c", alpha=0.75)
        ax5.set_xlabel("Difference in prevalence")
        ax5.set_title("Top Clinical Values Associated with Metastatic Stage", fontweight="bold")
        ax5.grid(axis="x", alpha=0.25)
        ax5.invert_yaxis()
    else:
        ax5.text(0.5, 0.5, "No clinical association results", ha="center", va="center", transform=ax5.transAxes)
        ax5.set_title("Clinical Associations", fontweight="bold")

    # 6) Genetic-clinical interactions (within metastatic)
    ax6 = plt.subplot(3, 2, 6)
    if len(interactions):
        # Keep GENOMIC_GROUP only for Other-MAPK-MUT (two-line x-label: CDKN2A+BRAF+ / Other MAPK-MUT); drop other genomic rows.
        clin = interactions["Clinical"].astype(str)

        def _drop_other_genomic(c: str) -> bool:
            s = str(c)
            if not s.startswith("GENOMIC_GROUP="):
                return False
            return "Other-MAPK-MUT" not in s

        disp = interactions[~clin.map(_drop_other_genomic)].copy()
        if len(disp) == 0:
            disp = interactions.copy()

        _prio_mask = (disp["Genetic_Combination"].astype(str) == "CDKN2A+BRAF") & disp["Clinical"].astype(str).str.contains(
            "Other-MAPK-MUT", na=False
        )
        prio_df = disp[_prio_mask].head(1)
        rest = disp[~_prio_mask].sort_values("Interaction_Score", ascending=False)
        disp2 = pd.concat([prio_df, rest], ignore_index=True)
        disp2 = disp2.drop_duplicates(subset=["Genetic_Combination", "Clinical"], keep="first")
        top = disp2.head(10).copy()

        def _fmt_panel_f_clinical(clin: str) -> str:
            s = str(clin)
            repl = (
                ("DIABETES_HISOTRY=", "Dia.Hist="),
                ("DIABETES_HISTORY=", "Dia.Hist="),
                ("TOBACCO_EXPOSURE=", "Tob.Exp="),
                ("TUMOR_LOCATION=", "Tum.Loc="),
            )
            for old, new in repl:
                if s.startswith(old):
                    return new + s[len(old) :]
            return s

        labels = []
        for _, row in top.iterrows():
            if str(row["Genetic_Combination"]) == "CDKN2A+BRAF" and "Other-MAPK-MUT" in str(row["Clinical"]):
                labels.append("CDKN2A+BRAF+\nOther MAPK-MUT")
            else:
                labels.append(str(row["Genetic_Combination"]) + "\n" + _fmt_panel_f_clinical(str(row["Clinical"])))
        ax6.bar(np.arange(len(top)), top["Interaction_Score"], color="#e377c2", alpha=0.75)
        ax6.set_xticks(np.arange(len(top)))
        ax6.set_xticklabels(labels, rotation=45, ha="right")
        ax6.set_ylabel("Interaction Score (Observed/Expected)")
        ax6.set_title("Top Genetic-Clinical Interactions (Metastatic)", fontweight="bold")
        ax6.grid(axis="y", alpha=0.25)
    else:
        ax6.text(0.5, 0.5, "No interactions (>=3 patients) found", ha="center", va="center", transform=ax6.transAxes)
        ax6.set_title("Genetic-Clinical Interactions (Metastatic)", fontweight="bold")

    plt.tight_layout(pad=2.0)
    out_png.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_png, dpi=350, bbox_inches="tight")
    plt.close()


def save_to_excel(
    out_xlsx: Path,
    stats_df: pd.DataFrame,
    mutation_long: pd.DataFrame,
    mutation_pivot: pd.DataFrame,
    synergy_by_st: Dict[str, pd.DataFrame],
    assoc_df: pd.DataFrame,
    interactions: pd.DataFrame,
) -> None:
    out_xlsx.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(out_xlsx, engine="openpyxl") as writer:
        stats_df.to_excel(writer, sheet_name="Stage_Summary", index=False)
        mutation_long.to_excel(writer, sheet_name="Mutation_Rates_Long", index=False)
        mutation_pivot.to_excel(writer, sheet_name="Mutation_Rates_Pivot", index=False)
        assoc_df.to_excel(writer, sheet_name="Clinical_Associations", index=False)
        interactions.to_excel(writer, sheet_name="Metastatic_Interactions", index=False)

        for stage, sdf in synergy_by_st.items():
            name = stage.replace("/", "_").replace(" ", "_")[:28]
            sheet = f"Synergy_{name}"
            if len(sdf) == 0:
                pd.DataFrame({"info": [f"No synergy combos (>=5 patients) for stage: {stage}"]}).to_excel(
                    writer, sheet_name=sheet, index=False
                )
            else:
                sdf.to_excel(writer, sheet_name=sheet, index=False)


def main() -> None:
    print("STAGE (3-GROUP) COMPREHENSIVE ANALYSIS")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    _set_publication_font()
    paths = get_paths()
    if not paths.merged_xlsx.exists():
        raise FileNotFoundError(f"Missing input file: {paths.merged_xlsx}")

    patient_data = load_patient_level_data(paths.merged_xlsx)
    stage_dfs = split_by_stage(patient_data)

    stats_df = basic_stats_by_stage(stage_dfs)
    mutation_long, mutation_pivot = mutation_rates_by_stage(stage_dfs)
    synergy = synergy_by_stage(stage_dfs, min_patients=5)

    # Clinical factors to compare across stage (excluding STAGE itself).
    clinical_factors = [
        "SEX",
        "ANCESTRY",
        "TOBACCO_EXPOSURE",
        "DIABETES_HISOTRY",
        "TUMOR_LOCATION",
        "GENOMIC_GROUP",
        "WGD",
        "ALLELIC_IMBALANCE",
    ]
    assoc_df = clinical_factor_stage_association(patient_data, clinical_factors)

    interactions = genetic_clinical_interactions_within_stage(
        stage_df=stage_dfs.get("Metastatic", pd.DataFrame()),
        synergy_df=synergy.get("Metastatic", pd.DataFrame()),
        assoc_df=assoc_df,
        stage="Metastatic",
        top_combo_n=10,
        top_factor_n=10,
        min_patients=3,
    )

    create_visualization(
        stats_df=stats_df,
        mutation_long=mutation_long,
        mutation_pivot=mutation_pivot,
        synergy_by_st=synergy,
        assoc_df=assoc_df,
        interactions=interactions,
        out_png=paths.out_png,
    )

    save_to_excel(
        out_xlsx=paths.out_xlsx,
        stats_df=stats_df,
        mutation_long=mutation_long,
        mutation_pivot=mutation_pivot,
        synergy_by_st=synergy,
        assoc_df=assoc_df,
        interactions=interactions,
    )

    # Convenience: a small workbook with only top synergy per stage.
    try:
        with pd.ExcelWriter(paths.out_synergy_xlsx, engine="openpyxl") as writer:
            for stage in STAGES:
                sdf = synergy.get(stage, pd.DataFrame())
                sheet = stage.replace("/", "_").replace(" ", "_")[:31]
                if len(sdf):
                    sdf.head(50).to_excel(writer, sheet_name=sheet, index=False)
                else:
                    pd.DataFrame({"info": [f"No synergy combos (>=5 patients) for stage: {stage}"]}).to_excel(
                        writer, sheet_name=sheet, index=False
                    )
    except Exception:
        # Non-critical convenience output
        pass

    print(f"✅ Saved figure: {paths.out_png}")
    print(f"✅ Saved results: {paths.out_xlsx}")
    if paths.out_synergy_xlsx.exists():
        print(f"✅ Saved synergy summary: {paths.out_synergy_xlsx}")
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()

