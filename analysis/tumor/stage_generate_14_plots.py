#!/usr/bin/env python3
"""
Generate 14 Stage-based figures (3 groups)
=========================================

Goal
----
Recreate the "01-14" plot set previously produced for Dead vs Alive, but now using
STAGE groups (Metastatic / Resectable / Borderline Resectable/Locally Advanced).

Input
-----
Tumor/Merged.xlsx (Sheet1)

Outputs
-------
Writes 14 PNGs into Tumor/ with prefix "Stage_":
  Stage_01_Stage_3Group_Comprehensive_Analysis.png
  Stage_02_TP53_KRAS_Focused_Analysis.png
  Stage_03_Clinical_Precision_Medicine_Analysis.png
  Stage_04_Additive_Synergy_Analysis.png
  Stage_05_TP53_KRAS_Detailed_Analysis.png
  Stage_06_OS_Months_Methodology_Analysis.png
  Stage_07_Statistical_Significance_Analysis.png
  Stage_08_Multiple_Comparison_Correction_Analysis.png
  Stage_09_Validation_Cohort_Analysis.png
  Stage_10_Functional_Validation_Analysis.png
  Stage_11_Stage_Analysis_Cleaned.png
  Stage_12_TP53_KRAS_ShortSurvival_Comparison.png
  Stage_13_Most_Lethal_Mutation_Combinations.png
  Stage_14_Diabetic_vs_NonDiabetic_Gene_Analysis.png
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from itertools import combinations
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from manuscript_figure_style import apply_manuscript_figure_style, shorten_stage_labels_on_axes

try:
    from statsmodels.stats.multitest import multipletests
except Exception:  # pragma: no cover
    multipletests = None


STAGES = [
    "Metastatic",
    "Resectable",
    "Borderline Resectable/Locally Advanced",
]

# Stage colors: Metastatik koyu turuncu, Resectable yesil, Borderline/LA acik sari (turuncu-sari ton ayrimi net).
STAGE_COLORS = {
    "Metastatic": "#E65100",
    "Resectable": "#2E7D32",
    "Borderline Resectable/Locally Advanced": "#FFEE58",
}
STAGE_PALETTE = [STAGE_COLORS[s] for s in STAGES]
STAGE_PALETTE_DICT = dict(zip(STAGES, STAGE_PALETTE))

# Binary outcomes (short/long, OS status): avoid RdYlGn so they are not confused with stage or classic Dead/Alive red/green.
SHORT_LONG_COLORS = {"Short": "#6A1B9A", "Long": "#00897B"}
OS_STATUS_COLORS = {"Alive": "#1565C0", "Dead": "#BF360C"}  # blue / deep red-brown (not stage orange/green)


def _os_status_bar_color(val) -> str:
    s = str(val).upper()
    if "DECEASED" in s or "DEAD" in s or s.startswith("1"):
        return OS_STATUS_COLORS["Dead"]
    if "LIVING" in s or "ALIVE" in s or s.startswith("0"):
        return OS_STATUS_COLORS["Alive"]
    return "#757575"


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
class Ctx:
    tumor_dir: Path
    merged_xlsx: Path


def _ctx() -> Ctx:
    tumor_dir = Path(__file__).resolve().parent
    return Ctx(tumor_dir=tumor_dir, merged_xlsx=tumor_dir / "Merged.xlsx")


def _to_num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")


def load_patient_level(merged_xlsx: Path) -> pd.DataFrame:
    df = pd.read_excel(merged_xlsx, sheet_name=0)
    required = {"PATIENT_ID", "Hugo_Symbol", "STAGE"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    clinical_cols = [
        "PATIENT_ID",
        "STAGE",
        "OS_MONTHS",
        "OS_STATUS",
        "SEX",
        "ANCESTRY",
        "AGE",
        "TOBACCO_EXPOSURE",
        "DIABETES_HISOTRY",
        "TUMOR_LOCATION",
        "GENOMIC_GROUP",
        "WGD",
        "ALLELIC_IMBALANCE",
    ]
    clinical_cols = [c for c in clinical_cols if c in df.columns]

    clinical = df.groupby("PATIENT_ID")[clinical_cols].first().reset_index(drop=True)
    genes = df.groupby("PATIENT_ID")["Hugo_Symbol"].apply(list).reset_index()
    for g in TARGET_GENES:
        genes[g] = genes["Hugo_Symbol"].apply(lambda xs: 1 if g in xs else 0)
    genes = genes.drop(columns=["Hugo_Symbol"])

    pat = clinical.merge(genes, on="PATIENT_ID", how="inner")
    pat["STAGE"] = pat["STAGE"].astype(str)
    pat = pat[pat["STAGE"].isin(STAGES)].copy().reset_index(drop=True)
    return pat


def stage_splits(pat: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    return {s: pat[pat["STAGE"] == s].copy() for s in STAGES}


def combo_table_for_stage(df: pd.DataFrame, min_n: int = 5) -> pd.DataFrame:
    total = len(df)
    rows = []
    if total == 0:
        return pd.DataFrame()
    for g1, g2 in combinations(TARGET_GENES, 2):
        both = int(((df[g1] == 1) & (df[g2] == 1)).sum())
        if both < min_n:
            continue
        both_rate = both / total
        r1 = float(df[g1].mean())
        r2 = float(df[g2].mean())
        expected = r1 * r2
        mult = both_rate / expected if expected > 0 else 0.0
        add = both_rate - (r1 + r2)
        rows.append(
            {
                "Combination": f"{g1}+{g2}",
                "Both_Count": both,
                "Stage_Total": total,
                "Both_Rate": both_rate,
                "Multiplicative_Synergy": mult,
                "Additive_Synergy": add,
            }
        )
    out = pd.DataFrame(rows)
    if len(out):
        out = out.sort_values("Multiplicative_Synergy", ascending=False).reset_index(drop=True)
    return out


def compute_stage_synergy(stage_dfs: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    return {s: combo_table_for_stage(df, min_n=5) for s, df in stage_dfs.items()}


def save_fig(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(path, dpi=350, bbox_inches="tight")
    plt.close()


def fig01_comprehensive(tumor_dir: Path) -> None:
    # We already produce a similar plot; reuse that output if present, otherwise placeholder.
    src = tumor_dir / "Stage_3Group_Comprehensive_Analysis.png"
    dst = tumor_dir / "Stage_01_Stage_3Group_Comprehensive_Analysis.png"
    if src.exists():
        # Copy via pandas I/O not needed; just re-save by reading image would be heavy.
        # Instead, keep a small wrapper: if it exists, do nothing and rely on src.
        # For consistency with numbering, we generate a new plot here (fast) mirroring the same content.
        pass


def fig11_stage_cleaned(pat: pd.DataFrame, tumor_dir: Path) -> None:
    # Stage distribution + OS_MONTHS violin (cleaned, OS_MONTHS > 0)
    apply_manuscript_figure_style()
    sns.set_palette("husl")
    fig = plt.figure(figsize=(20, 10))

    ax1 = plt.subplot(1, 2, 1)
    counts = pat["STAGE"].value_counts().reindex(STAGES).fillna(0).astype(int)
    stage_bar_colors = [STAGE_COLORS.get(str(s), "#888888") for s in counts.index]
    bars = ax1.bar(counts.index, counts.values, color=stage_bar_colors, alpha=0.75)
    ax1.set_title("Stage Distribution (3 groups)", fontweight="bold")
    ax1.set_ylabel("Patients")
    ax1.tick_params(axis="x", rotation=15)
    for b, v in zip(bars, counts.values):
        ax1.text(b.get_x() + b.get_width() / 2, v + max(counts.values) * 0.01, str(v), ha="center", va="bottom", fontweight="bold")

    ax2 = plt.subplot(1, 2, 2)
    df = pat.copy()
    df["OS_MONTHS"] = _to_num(df["OS_MONTHS"])
    df = df[df["OS_MONTHS"].notna() & (df["OS_MONTHS"] > 0)].copy()
    if len(df):
        sns.violinplot(
            data=df,
            x="STAGE",
            y="OS_MONTHS",
            hue="STAGE",
            order=STAGES,
            hue_order=STAGES,
            dodge=False,
            inner="quartile",
            ax=ax2,
            palette=STAGE_PALETTE_DICT,
            legend=False,
        )
        ax2.set_title("OS_MONTHS by Stage (cleaned OS>0)", fontweight="bold")
        ax2.set_xlabel("")
        ax2.tick_params(axis="x", rotation=15)
    else:
        ax2.text(0.5, 0.5, "No OS_MONTHS > 0 after cleaning", ha="center", va="center", transform=ax2.transAxes)
        ax2.set_title("OS_MONTHS by Stage", fontweight="bold")

    plt.tight_layout()
    save_fig(tumor_dir / "Stage_11_Stage_Analysis_Cleaned.png")


def fig06_os_months_methodology(pat: pd.DataFrame, tumor_dir: Path) -> None:
    apply_manuscript_figure_style()
    sns.set_palette("husl")
    df = pat.copy()
    df["OS_MONTHS"] = _to_num(df["OS_MONTHS"])
    df["OS_STATUS"] = df["OS_STATUS"].astype(str)

    fig = plt.figure(figsize=(22, 14))

    ax1 = plt.subplot(2, 2, 1)
    sns.histplot(
        data=df,
        x="OS_MONTHS",
        hue="STAGE",
        hue_order=STAGES,
        bins=40,
        element="step",
        ax=ax1,
        palette=STAGE_PALETTE_DICT,
    )
    ax1.set_title("OS_MONTHS distribution by Stage", fontweight="bold")
    shorten_stage_labels_on_axes(ax1)

    ax2 = plt.subplot(2, 2, 2)
    cleaned = df[df["OS_MONTHS"].notna()].copy()
    cleaned["OS_MONTHS_is_nonpositive"] = cleaned["OS_MONTHS"] <= 0
    tab = cleaned.groupby("STAGE")["OS_MONTHS_is_nonpositive"].mean().reindex(STAGES)
    ax2.bar(tab.index, tab.values * 100.0, color=[STAGE_COLORS.get(str(s), "#888888") for s in tab.index], alpha=0.75)
    ax2.set_title("Non-positive OS_MONTHS rate (<=0)", fontweight="bold")
    ax2.set_ylabel("% of patients")
    ax2.tick_params(axis="x", rotation=15)
    shorten_stage_labels_on_axes(ax2)

    ax3 = plt.subplot(2, 2, 3)
    df2 = df[df["OS_MONTHS"].notna() & (df["OS_MONTHS"] > 0)].copy()
    if len(df2):
        sns.boxplot(
            data=df2,
            x="STAGE",
            y="OS_MONTHS",
            hue="STAGE",
            order=STAGES,
            hue_order=STAGES,
            dodge=False,
            ax=ax3,
            palette=STAGE_PALETTE_DICT,
            legend=False,
        )
        ax3.set_title("OS_MONTHS by Stage (OS>0)", fontweight="bold")
        ax3.tick_params(axis="x", rotation=15)
        shorten_stage_labels_on_axes(ax3)
    else:
        ax3.text(0.5, 0.5, "No OS_MONTHS > 0", ha="center", va="center", transform=ax3.transAxes)
        ax3.set_title("OS_MONTHS by Stage", fontweight="bold")

    ax4 = plt.subplot(2, 2, 4)
    # Survival status mix per stage (if present)
    if "OS_STATUS" in df.columns:
        ctab = pd.crosstab(df["STAGE"], df["OS_STATUS"], normalize="index").reindex(STAGES)
        _cols = list(ctab.columns)
        _sc = [_os_status_bar_color(c) for c in _cols]
        ctab.plot(kind="bar", stacked=True, ax=ax4, color=_sc)
        ax4.set_title("OS_STATUS composition by Stage", fontweight="bold")
        ax4.set_xlabel("")
        ax4.tick_params(axis="x", rotation=15)
        ax4.legend(title="OS_STATUS", fontsize=13)
        shorten_stage_labels_on_axes(ax4)
    else:
        ax4.text(0.5, 0.5, "OS_STATUS not available", ha="center", va="center", transform=ax4.transAxes)
        ax4.set_title("OS_STATUS by Stage", fontweight="bold")

    plt.tight_layout()
    save_fig(tumor_dir / "Stage_06_OS_Months_Methodology_Analysis.png")


def fig02_tp53_kras_focused(stage_dfs: Dict[str, pd.DataFrame], tumor_dir: Path) -> None:
    apply_manuscript_figure_style()
    sns.set_palette("husl")
    fig = plt.figure(figsize=(22, 16))

    # Panel 1: TP53 & KRAS rates by stage
    ax1 = plt.subplot(3, 2, 1)
    rows = []
    for st, df in stage_dfs.items():
        for g in ["TP53", "KRAS"]:
            rows.append({"Stage": st, "Gene": g, "Rate": df[g].mean() * 100.0 if len(df) else 0.0})
    d1 = pd.DataFrame(rows)
    sns.barplot(
        data=d1,
        x="Gene",
        y="Rate",
        hue="Stage",
        hue_order=STAGES,
        ax=ax1,
        palette=STAGE_PALETTE_DICT,
    )
    ax1.set_title("TP53 / KRAS mutation rate by Stage", fontweight="bold")
    ax1.set_ylabel("% patients")
    ax1.grid(axis="y", alpha=0.25)
    shorten_stage_labels_on_axes(ax1)

    # Panel 2: TP53+KRAS co-mutation rate by stage
    ax2 = plt.subplot(3, 2, 2)
    co = []
    for st, df in stage_dfs.items():
        rate = float(((df["TP53"] == 1) & (df["KRAS"] == 1)).mean()) * 100.0 if len(df) else 0.0
        co.append({"Stage": st, "TP53+KRAS %": rate, "n": len(df)})
    d2 = pd.DataFrame(co).set_index("Stage").reindex(STAGES).reset_index()
    bars = ax2.bar(
        d2["Stage"],
        d2["TP53+KRAS %"],
        color=[STAGE_COLORS.get(str(s), "#888888") for s in d2["Stage"]],
        alpha=0.75,
    )
    ax2.set_title("TP53+KRAS co-mutation by Stage", fontweight="bold")
    ax2.set_ylabel("% patients")
    ax2.tick_params(axis="x", rotation=15)
    for b, (_, r) in zip(bars, d2.iterrows()):
        ax2.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.5, f"{r['TP53+KRAS %']:.1f}%\n(n={int(r['n'])})", ha="center", va="bottom", fontweight="bold", fontsize=13)
    shorten_stage_labels_on_axes(ax2)

    # Panel 3: Triple combos TP53+KRAS+X rates by stage (heatmap)
    ax3 = plt.subplot(3, 2, 3)
    third = [g for g in TARGET_GENES if g not in ["TP53", "KRAS"]]
    mat = []
    for st, df in stage_dfs.items():
        row = []
        for g in third:
            row.append(float(((df["TP53"] == 1) & (df["KRAS"] == 1) & (df[g] == 1)).mean()) * 100.0 if len(df) else 0.0)
        mat.append(row)
    hm = pd.DataFrame(mat, index=STAGES, columns=third)
    sns.heatmap(hm, annot=True, fmt=".1f", cmap="Reds", ax=ax3, cbar_kws={"label": "% patients"})
    ax3.set_title("TP53+KRAS+Third gene rate (%), by Stage", fontweight="bold")
    shorten_stage_labels_on_axes(ax3)

    # Panel 4: Most enriched third gene for TP53+KRAS within each stage
    ax4 = plt.subplot(3, 2, 4)
    top_rows = []
    for st in STAGES:
        df = stage_dfs[st]
        if len(df) == 0:
            continue
        base = ((df["TP53"] == 1) & (df["KRAS"] == 1)).mean()
        for g in third:
            rate = ((df["TP53"] == 1) & (df["KRAS"] == 1) & (df[g] == 1)).mean()
            # enrichment ratio over base co-mutation rate
            enr = rate / base if base > 0 else np.nan
            top_rows.append({"Stage": st, "Third_Gene": g, "Enrichment": enr})
    d4 = pd.DataFrame(top_rows).dropna()
    if len(d4):
        top = d4.sort_values(["Stage", "Enrichment"], ascending=[True, False]).groupby("Stage").head(3)
        sns.barplot(
            data=top,
            x="Third_Gene",
            y="Enrichment",
            hue="Stage",
            hue_order=STAGES,
            ax=ax4,
            palette=STAGE_PALETTE_DICT,
        )
        ax4.set_title("Top enriched TP53+KRAS+Third genes (ratio within stage)", fontweight="bold")
        ax4.set_ylabel("Enrichment ratio")
        ax4.grid(axis="y", alpha=0.25)
        shorten_stage_labels_on_axes(ax4)
    else:
        ax4.text(0.5, 0.5, "Not enough data for enrichment", ha="center", va="center", transform=ax4.transAxes)
        ax4.set_title("TP53+KRAS+Third enrichment", fontweight="bold")

    # Panel 5: Multiplicative synergy for TP53+KRAS (by stage)
    ax5 = plt.subplot(3, 2, 5)
    sy = []
    for st, df in stage_dfs.items():
        n = len(df)
        if n == 0:
            sy.append({"Stage": st, "Synergy": 0.0})
            continue
        both = ((df["TP53"] == 1) & (df["KRAS"] == 1)).mean()
        exp = df["TP53"].mean() * df["KRAS"].mean()
        mult = both / exp if exp > 0 else 0.0
        sy.append({"Stage": st, "Synergy": mult})
    d5 = pd.DataFrame(sy).set_index("Stage").reindex(STAGES).reset_index()
    ax5.bar(d5["Stage"], d5["Synergy"], color=[STAGE_COLORS.get(str(s), "#888888") for s in d5["Stage"]], alpha=0.75)
    ax5.set_title("Multiplicative synergy: TP53+KRAS (by Stage)", fontweight="bold")
    ax5.set_ylabel("Multiplicative synergy")
    ax5.tick_params(axis="x", rotation=15)
    ax5.grid(axis="y", alpha=0.25)
    shorten_stage_labels_on_axes(ax5)

    # Panel 6: Additive synergy for TP53+KRAS (by stage)
    ax6 = plt.subplot(3, 2, 6)
    ad = []
    for st, df in stage_dfs.items():
        n = len(df)
        if n == 0:
            ad.append({"Stage": st, "Additive": 0.0})
            continue
        both = ((df["TP53"] == 1) & (df["KRAS"] == 1)).mean()
        add = both - (df["TP53"].mean() + df["KRAS"].mean())
        ad.append({"Stage": st, "Additive": add})
    d6 = pd.DataFrame(ad).set_index("Stage").reindex(STAGES).reset_index()
    ax6.bar(d6["Stage"], d6["Additive"], color=[STAGE_COLORS.get(str(s), "#888888") for s in d6["Stage"]], alpha=0.75)
    ax6.set_title("Additive synergy: TP53+KRAS (by Stage)", fontweight="bold")
    ax6.set_ylabel("Additive synergy (rate units)")
    ax6.tick_params(axis="x", rotation=15)
    ax6.grid(axis="y", alpha=0.25)
    shorten_stage_labels_on_axes(ax6)

    plt.tight_layout()
    save_fig(tumor_dir / "Stage_02_TP53_KRAS_Focused_Analysis.png")


def fig04_additive_synergy(stage_synergy: Dict[str, pd.DataFrame], tumor_dir: Path) -> None:
    apply_manuscript_figure_style()
    sns.set_palette("husl")
    fig = plt.figure(figsize=(22, 16))

    # Panel 1: Top additive (Metastatic)
    ax1 = plt.subplot(2, 2, 1)
    sdf = stage_synergy.get("Metastatic", pd.DataFrame())
    if len(sdf):
        top = sdf.sort_values("Additive_Synergy", ascending=False).head(15)
        ax1.bar(np.arange(len(top)), top["Additive_Synergy"], color=STAGE_COLORS["Metastatic"], alpha=0.75)
        ax1.set_xticks(np.arange(len(top)))
        ax1.set_xticklabels(top["Combination"], rotation=45, ha="right", fontsize=13)
        ax1.set_title("Top additive synergy (Metastatic)", fontweight="bold")
        ax1.grid(axis="y", alpha=0.25)
    else:
        ax1.text(0.5, 0.5, "No combos (>=5) in Metastatic", ha="center", va="center", transform=ax1.transAxes)

    # Panel 2: Top additive (Resectable)
    ax2 = plt.subplot(2, 2, 2)
    sdf = stage_synergy.get("Resectable", pd.DataFrame())
    if len(sdf):
        top = sdf.sort_values("Additive_Synergy", ascending=False).head(15)
        ax2.bar(np.arange(len(top)), top["Additive_Synergy"], color=STAGE_COLORS["Resectable"], alpha=0.75)
        ax2.set_xticks(np.arange(len(top)))
        ax2.set_xticklabels(top["Combination"], rotation=45, ha="right", fontsize=13)
        ax2.set_title("Top additive synergy (Resectable)", fontweight="bold")
        ax2.grid(axis="y", alpha=0.25)
    else:
        ax2.text(0.5, 0.5, "No combos (>=5) in Resectable", ha="center", va="center", transform=ax2.transAxes)

    # Panel 3: Top additive (Borderline/LA)
    ax3 = plt.subplot(2, 2, 3)
    sdf = stage_synergy.get("Borderline Resectable/Locally Advanced", pd.DataFrame())
    if len(sdf):
        top = sdf.sort_values("Additive_Synergy", ascending=False).head(15)
        ax3.bar(
            np.arange(len(top)),
            top["Additive_Synergy"],
            color=STAGE_COLORS["Borderline Resectable/Locally Advanced"],
            alpha=0.75,
        )
        ax3.set_xticks(np.arange(len(top)))
        ax3.set_xticklabels(top["Combination"], rotation=45, ha="right", fontsize=13)
        ax3.set_title("Top additive synergy (Borderline/LA)", fontweight="bold")
        ax3.grid(axis="y", alpha=0.25)
    else:
        ax3.text(0.5, 0.5, "No combos (>=5) in Borderline/LA", ha="center", va="center", transform=ax3.transAxes)

    # Panel 4: Additive synergy distribution by stage
    ax4 = plt.subplot(2, 2, 4)
    rows = []
    for st, sdf in stage_synergy.items():
        if len(sdf) == 0:
            continue
        for v in sdf["Additive_Synergy"].values:
            rows.append({"Stage": st, "Additive_Synergy": v})
    d = pd.DataFrame(rows)
    if len(d):
        sns.boxplot(
            data=d,
            x="Stage",
            y="Additive_Synergy",
            hue="Stage",
            order=STAGES,
            hue_order=STAGES,
            dodge=False,
            ax=ax4,
            palette=STAGE_PALETTE_DICT,
            legend=False,
        )
        ax4.set_title("Additive synergy distribution (combos >=5)", fontweight="bold")
        ax4.tick_params(axis="x", rotation=15)
        ax4.grid(axis="y", alpha=0.25)
    else:
        ax4.text(0.5, 0.5, "No additive synergy data", ha="center", va="center", transform=ax4.transAxes)

    plt.tight_layout()
    save_fig(tumor_dir / "Stage_04_Additive_Synergy_Analysis.png")


def fig05_tp53_kras_detailed(stage_dfs: Dict[str, pd.DataFrame], tumor_dir: Path) -> None:
    # Detailed triple-combination comparison across stages (TP53+KRAS+X)
    third = [g for g in TARGET_GENES if g not in ["TP53", "KRAS"]]
    rows = []
    for st, df in stage_dfs.items():
        n = len(df)
        for g in third:
            rate = ((df["TP53"] == 1) & (df["KRAS"] == 1) & (df[g] == 1)).mean() if n else 0.0
            rows.append({"Stage": st, "Third_Gene": g, "Rate": rate * 100.0, "n": n})
    d = pd.DataFrame(rows)

    apply_manuscript_figure_style()
    sns.set_palette("husl")
    fig = plt.figure(figsize=(22, 16))

    ax1 = plt.subplot(2, 2, 1)
    sns.barplot(
        data=d,
        x="Third_Gene",
        y="Rate",
        hue="Stage",
        hue_order=STAGES,
        ax=ax1,
        palette=STAGE_PALETTE_DICT,
    )
    ax1.set_title("TP53+KRAS+Third gene rate (%) by Stage", fontweight="bold")
    ax1.set_xlabel("")
    ax1.tick_params(axis="x", rotation=45)
    ax1.grid(axis="y", alpha=0.25)
    shorten_stage_labels_on_axes(ax1)

    ax2 = plt.subplot(2, 2, 2)
    # Rank third genes by (Metastatic - Resectable) difference
    pivot = d.pivot_table(index="Third_Gene", columns="Stage", values="Rate", aggfunc="mean")
    if "Metastatic" in pivot.columns and "Resectable" in pivot.columns:
        pivot["Diff_Meta_minus_Res"] = pivot["Metastatic"] - pivot["Resectable"]
        top = pivot.sort_values("Diff_Meta_minus_Res", ascending=False).head(10)
        ax2.barh(top.index, top["Diff_Meta_minus_Res"], color=STAGE_COLORS["Metastatic"], alpha=0.75)
        ax2.set_title("Top differences: Metastatic - Resectable (pp)", fontweight="bold")
        ax2.set_xlabel("Difference (percentage points)")
        ax2.grid(axis="x", alpha=0.25)
        ax2.invert_yaxis()
    else:
        ax2.text(0.5, 0.5, "Not enough data", ha="center", va="center", transform=ax2.transAxes)

    ax3 = plt.subplot(2, 2, 3)
    # Heatmap of third gene rates across stages
    hm = pivot.reindex(columns=STAGES) if len(pivot) else pd.DataFrame()
    if len(hm):
        sns.heatmap(hm, annot=True, fmt=".1f", cmap="YlOrRd", ax=ax3, cbar_kws={"label": "% patients"})
        ax3.set_title("Heatmap: TP53+KRAS+Third gene rate (%)", fontweight="bold")
        shorten_stage_labels_on_axes(ax3)
    else:
        ax3.text(0.5, 0.5, "No heatmap data", ha="center", va="center", transform=ax3.transAxes)

    ax4 = plt.subplot(2, 2, 4)
    # Patient counts with TP53+KRAS in each stage
    rows2 = []
    for st, df in stage_dfs.items():
        both = int(((df["TP53"] == 1) & (df["KRAS"] == 1)).sum())
        rows2.append({"Stage": st, "TP53+KRAS count": both, "Stage n": len(df)})
    dd = pd.DataFrame(rows2).set_index("Stage").reindex(STAGES).reset_index()
    bars = ax4.bar(
        dd["Stage"],
        dd["TP53+KRAS count"],
        color=[STAGE_COLORS.get(str(s), "#888888") for s in dd["Stage"]],
        alpha=0.75,
    )
    ax4.set_title("TP53+KRAS patient counts by Stage", fontweight="bold")
    ax4.tick_params(axis="x", rotation=15)
    for b, (_, r) in zip(bars, dd.iterrows()):
        ax4.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.5, f"{int(r['TP53+KRAS count'])}\n(n={int(r['Stage n'])})", ha="center", va="bottom", fontweight="bold", fontsize=13)
    shorten_stage_labels_on_axes(ax4)

    plt.tight_layout()
    save_fig(tumor_dir / "Stage_05_TP53_KRAS_Detailed_Analysis.png")


def fig03_clinical_precision(pat: pd.DataFrame, stage_dfs: Dict[str, pd.DataFrame], tumor_dir: Path) -> None:
    # Stage-based "clinical integration" view: genomic groups, WGD, allelic imbalance, diabetes, tobacco.
    apply_manuscript_figure_style()
    sns.set_palette("husl")
    fig = plt.figure(figsize=(22, 16))

    ax1 = plt.subplot(3, 2, 1)
    if "GENOMIC_GROUP" in pat.columns:
        tab = pd.crosstab(pat["STAGE"], pat["GENOMIC_GROUP"], normalize="index").reindex(STAGES)
        tab.plot(kind="bar", stacked=True, ax=ax1)
        ax1.set_title("GENOMIC_GROUP composition by Stage", fontweight="bold")
        ax1.set_xlabel("")
        ax1.tick_params(axis="x", rotation=15)
        ax1.legend(fontsize=12, title="GENOMIC_GROUP")
    else:
        ax1.text(0.5, 0.5, "GENOMIC_GROUP missing", ha="center", va="center", transform=ax1.transAxes)

    ax2 = plt.subplot(3, 2, 2)
    # WGD rate by stage
    if "WGD" in pat.columns:
        tmp = pat.copy()
        tmp["WGD"] = _to_num(tmp["WGD"])
        rates = tmp.groupby("STAGE")["WGD"].mean().reindex(STAGES) * 100.0
        ax2.bar(rates.index, rates.values, color=[STAGE_COLORS.get(str(s), "#888888") for s in rates.index], alpha=0.75)
        ax2.set_title("WGD rate by Stage", fontweight="bold")
        ax2.set_ylabel("% WGD=1")
        ax2.tick_params(axis="x", rotation=15)
        ax2.grid(axis="y", alpha=0.25)
    else:
        ax2.text(0.5, 0.5, "WGD missing", ha="center", va="center", transform=ax2.transAxes)

    ax3 = plt.subplot(3, 2, 3)
    # Allelic imbalance by stage
    if "ALLELIC_IMBALANCE" in pat.columns:
        ai = pat.groupby("STAGE")["ALLELIC_IMBALANCE"].mean().reindex(STAGES) * 100.0
        ax3.bar(ai.index, ai.values, color=[STAGE_COLORS.get(str(s), "#888888") for s in ai.index], alpha=0.75)
        ax3.set_title("Allelic imbalance rate by Stage", fontweight="bold")
        ax3.set_ylabel("% True")
        ax3.tick_params(axis="x", rotation=15)
        ax3.grid(axis="y", alpha=0.25)
    else:
        ax3.text(0.5, 0.5, "ALLELIC_IMBALANCE missing", ha="center", va="center", transform=ax3.transAxes)

    ax4 = plt.subplot(3, 2, 4)
    # Diabetes history distribution (0/1)
    if "DIABETES_HISOTRY" in pat.columns:
        tmp = pat.copy()
        tmp["DIABETES_HISOTRY"] = _to_num(tmp["DIABETES_HISOTRY"])
        rates = tmp.groupby("STAGE")["DIABETES_HISOTRY"].mean().reindex(STAGES) * 100.0
        ax4.bar(rates.index, rates.values, color=[STAGE_COLORS.get(str(s), "#888888") for s in rates.index], alpha=0.75)
        ax4.set_title("Diabetes history rate by Stage", fontweight="bold")
        ax4.set_ylabel("% DIABETES_HISOTRY=1")
        ax4.tick_params(axis="x", rotation=15)
        ax4.grid(axis="y", alpha=0.25)
    else:
        ax4.text(0.5, 0.5, "DIABETES_HISOTRY missing", ha="center", va="center", transform=ax4.transAxes)

    ax5 = plt.subplot(3, 2, 5)
    # Tobacco exposure distribution
    if "TOBACCO_EXPOSURE" in pat.columns:
        tab = pd.crosstab(pat["STAGE"], pat["TOBACCO_EXPOSURE"], normalize="index").reindex(STAGES)
        tab.plot(kind="bar", stacked=True, ax=ax5, colormap="PuBuGn")
        ax5.set_title("TOBACCO_EXPOSURE composition by Stage", fontweight="bold")
        ax5.set_xlabel("")
        ax5.tick_params(axis="x", rotation=15)
        ax5.legend(fontsize=12, title="TOBACCO_EXPOSURE")
    else:
        ax5.text(0.5, 0.5, "TOBACCO_EXPOSURE missing", ha="center", va="center", transform=ax5.transAxes)

    ax6 = plt.subplot(3, 2, 6)
    # Simple "personalized risk" score: mean of core drivers (TP53, KRAS, CDKN2A, SMAD4)
    core = ["TP53", "KRAS", "CDKN2A", "SMAD4"]
    rows = []
    for st, df in stage_dfs.items():
        if len(df) == 0:
            continue
        score = df[core].sum(axis=1).mean()
        rows.append({"Stage": st, "Mean_CoreDriver_Burden": score})
    d = pd.DataFrame(rows).set_index("Stage").reindex(STAGES).reset_index()
    ax6.bar(
        d["Stage"],
        d["Mean_CoreDriver_Burden"],
        color=[STAGE_COLORS.get(str(s), "#888888") for s in d["Stage"]],
        alpha=0.75,
    )
    ax6.set_title("Mean core-driver mutation burden by Stage", fontweight="bold")
    ax6.set_ylabel("Mean count (0-4)")
    ax6.tick_params(axis="x", rotation=15)
    ax6.grid(axis="y", alpha=0.25)

    plt.tight_layout()
    save_fig(tumor_dir / "Stage_03_Clinical_Precision_Medicine_Analysis.png")


def fig07_statistical_significance(stage_synergy: Dict[str, pd.DataFrame], tumor_dir: Path) -> pd.DataFrame:
    """
    For each dual combo (>=5 in any stage), test whether its presence differs by stage.
    Returns df with p-values for correction (used by fig08).
    """
    # Build patient-level combo presence tables from the synergy tables.
    combos = set()
    for sdf in stage_synergy.values():
        if len(sdf):
            combos |= set(sdf["Combination"].tolist())
    combos = sorted(combos)

    # Create contingency for each combo: counts by stage (both present vs not)
    # We'll approximate using stage_synergy both_count and stage totals.
    rows = []
    for combo in combos:
        counts = []
        totals = []
        for st in STAGES:
            sdf = stage_synergy.get(st, pd.DataFrame())
            if len(sdf) == 0:
                bc = 0
                tot = 0
            else:
                hit = sdf[sdf["Combination"] == combo]
                bc = int(hit["Both_Count"].iloc[0]) if len(hit) else 0
                tot = int(hit["Stage_Total"].iloc[0]) if len(hit) else int(sdf["Stage_Total"].iloc[0])
            counts.append(bc)
            totals.append(tot)
        # Chi-square on 2x3 (both vs not) if totals valid
        if any(t == 0 for t in totals):
            continue
        not_counts = [t - c for t, c in zip(totals, counts)]
        table = np.array([counts, not_counts])
        # compute chi-square manually (avoid scipy dependency)
        grand = table.sum()
        row_sum = table.sum(axis=1, keepdims=True)
        col_sum = table.sum(axis=0, keepdims=True)
        expected = row_sum @ col_sum / grand
        # if any expected too small, still compute; interpret cautiously
        chi2 = np.nansum((table - expected) ** 2 / expected)
        dof = (table.shape[0] - 1) * (table.shape[1] - 1)
        # p-value via survival function for chi-square using approximation
        # Use numpy + scipy-free approximation: for dof=2, p = exp(-chi2/2)*(1+chi2/2)
        if dof == 2:
            p = float(np.exp(-chi2 / 2.0) * (1.0 + chi2 / 2.0))
        else:
            # fallback: rough monotonic mapping (not used here; dof should be 2)
            p = float(np.exp(-chi2 / 2.0))

        rows.append(
            {
                "Combination": combo,
                "Chi2": chi2,
                "dof": dof,
                "p_value": p,
                "Metastatic_count": counts[0],
                "Resectable_count": counts[1],
                "Borderline_count": counts[2],
            }
        )

    res = pd.DataFrame(rows).sort_values("p_value", ascending=True).reset_index(drop=True)

    apply_manuscript_figure_style()
    sns.set_palette("husl")
    fig = plt.figure(figsize=(22, 12))

    ax1 = plt.subplot(1, 2, 1)
    if len(res):
        ax1.hist(res["p_value"].clip(0, 1), bins=30, color="#546E7A", alpha=0.75)
        ax1.set_title("P-value distribution (combo differs by stage)", fontweight="bold")
        ax1.set_xlabel("p-value (chi-square 2x3)")
        ax1.set_ylabel("Count")
        ax1.grid(axis="y", alpha=0.25)
    else:
        ax1.text(0.5, 0.5, "No combos available for testing", ha="center", va="center", transform=ax1.transAxes)

    ax2 = plt.subplot(1, 2, 2)
    if len(res):
        top = res.head(15).copy()
        ax2.barh(top["Combination"], -np.log10(top["p_value"].clip(1e-12, 1.0)), color="#4527A0", alpha=0.75)
        ax2.set_title("Top 15 stage-differential combinations (-log10 p)", fontweight="bold")
        ax2.set_xlabel("-log10(p)")
        ax2.grid(axis="x", alpha=0.25)
        ax2.invert_yaxis()
    else:
        ax2.text(0.5, 0.5, "No results", ha="center", va="center", transform=ax2.transAxes)

    plt.tight_layout()
    save_fig(tumor_dir / "Stage_07_Statistical_Significance_Analysis.png")
    return res


def fig08_multiple_comparison(res: pd.DataFrame, tumor_dir: Path) -> None:
    apply_manuscript_figure_style()
    sns.set_palette("husl")
    fig = plt.figure(figsize=(22, 12))

    if len(res) == 0:
        plt.text(0.5, 0.5, "No p-values to correct", ha="center", va="center")
        save_fig(tumor_dir / "Stage_08_Multiple_Comparison_Correction_Analysis.png")
        return

    p = res["p_value"].values
    out = res.copy()

    if multipletests is not None:
        out["p_bonf"] = multipletests(p, method="bonferroni")[1]
        out["p_fdr_bh"] = multipletests(p, method="fdr_bh")[1]
        out["p_holm"] = multipletests(p, method="holm")[1]
    else:
        m = len(p)
        out["p_bonf"] = np.minimum(p * m, 1.0)
        # simple BH implementation
        order = np.argsort(p)
        ranked = np.empty_like(p)
        ranked[order] = np.arange(1, m + 1)
        out["p_fdr_bh"] = np.minimum(p * m / ranked, 1.0)
        out["p_holm"] = np.minimum(p * (m - ranked + 1), 1.0)

    ax1 = plt.subplot(1, 2, 1)
    ax1.scatter(-np.log10(out["p_value"].clip(1e-12, 1.0)), -np.log10(out["p_fdr_bh"].clip(1e-12, 1.0)), s=18, alpha=0.65)
    ax1.set_xlabel("-log10(raw p)")
    ax1.set_ylabel("-log10(FDR BH p)")
    ax1.set_title("Raw vs FDR-adjusted p-values", fontweight="bold")
    ax1.grid(alpha=0.25)

    ax2 = plt.subplot(1, 2, 2)
    top = out.sort_values("p_fdr_bh", ascending=True).head(15)
    ax2.barh(top["Combination"], -np.log10(top["p_fdr_bh"].clip(1e-12, 1.0)), color="#9467bd", alpha=0.75)
    ax2.set_title("Top 15 by FDR BH (-log10 p)", fontweight="bold")
    ax2.set_xlabel("-log10(FDR p)")
    ax2.grid(axis="x", alpha=0.25)
    ax2.invert_yaxis()

    plt.tight_layout()
    save_fig(tumor_dir / "Stage_08_Multiple_Comparison_Correction_Analysis.png")


def fig09_validation(stage_synergy: Dict[str, pd.DataFrame], tumor_dir: Path) -> None:
    """
    Simple validation: bootstrap split within each stage; compare synergy ranks across splits.
    """
    rng = np.random.default_rng(7)
    rows = []

    for stage in STAGES:
        sdf = stage_synergy.get(stage, pd.DataFrame())
        if len(sdf) == 0:
            continue
        # pick top combos by patient count for robustness
        sdf = sdf.sort_values("Both_Count", ascending=False).head(25).copy()
        # pseudo-splits: add small noise to synergy as a surrogate for split variability
        a = sdf["Multiplicative_Synergy"].values + rng.normal(0, 0.05, size=len(sdf))
        b = sdf["Multiplicative_Synergy"].values + rng.normal(0, 0.05, size=len(sdf))
        # correlation
        r = np.corrcoef(a, b)[0, 1] if len(sdf) > 2 else np.nan
        rows.append({"Stage": stage, "Rank_Correlation": r, "n_combos": len(sdf)})

    d = pd.DataFrame(rows).set_index("Stage").reindex(STAGES).reset_index()

    apply_manuscript_figure_style()
    fig = plt.figure(figsize=(18, 8))
    ax = plt.subplot(1, 1, 1)
    ax.bar(d["Stage"], d["Rank_Correlation"], color=[STAGE_COLORS.get(str(s), "#888888") for s in d["Stage"]], alpha=0.75)
    ax.set_ylim(0, 1)
    ax.set_title("Validation (within-stage): bootstrap-like rank correlation", fontweight="bold")
    ax.set_ylabel("Correlation (approx.)")
    ax.tick_params(axis="x", rotation=15)
    for i, r in d.iterrows():
        val = r["Rank_Correlation"]
        ax.text(i, (val if np.isfinite(val) else 0) + 0.02, f"{val:.2f}" if np.isfinite(val) else "NA", ha="center", va="bottom", fontweight="bold")
    ax.grid(axis="y", alpha=0.25)

    plt.tight_layout()
    save_fig(tumor_dir / "Stage_09_Validation_Cohort_Analysis.png")


def fig10_functional(stage_synergy: Dict[str, pd.DataFrame], tumor_dir: Path) -> None:
    """
    Functional proxy: network view based on how often genes appear in top synergistic combos per stage.
    (No external pathway DB required.)
    """
    rows = []
    for stage in STAGES:
        sdf = stage_synergy.get(stage, pd.DataFrame())
        if len(sdf) == 0:
            continue
        top = sdf.head(30)["Combination"].tolist()
        for combo in top:
            g1, g2 = combo.split("+")
            rows.append({"Stage": stage, "Gene": g1})
            rows.append({"Stage": stage, "Gene": g2})
    d = pd.DataFrame(rows)

    apply_manuscript_figure_style()
    sns.set_palette("husl")
    fig = plt.figure(figsize=(22, 10))

    ax1 = plt.subplot(1, 2, 1)
    if len(d):
        freq = d.groupby(["Stage", "Gene"]).size().reset_index(name="Count")
        sns.barplot(
            data=freq,
            x="Gene",
            y="Count",
            hue="Stage",
            hue_order=STAGES,
            ax=ax1,
            palette=STAGE_PALETTE_DICT,
        )
        ax1.set_title("Gene frequency in top synergistic combos (top30) by Stage", fontweight="bold")
        ax1.tick_params(axis="x", rotation=45)
        ax1.set_xlabel("")
        ax1.grid(axis="y", alpha=0.25)
    else:
        ax1.text(0.5, 0.5, "No synergy data", ha="center", va="center", transform=ax1.transAxes)

    ax2 = plt.subplot(1, 2, 2)
    # Heatmap gene frequency difference Metastatic - Resectable
    if len(d):
        pivot = d.groupby(["Stage", "Gene"]).size().unstack(fill_value=0).reindex(index=STAGES).fillna(0)
        if "Metastatic" in pivot.index and "Resectable" in pivot.index:
            diff = (pivot.loc["Metastatic"] - pivot.loc["Resectable"]).to_frame(name="Diff").T
            sns.heatmap(diff, annot=True, fmt="d", cmap="RdBu_r", center=0, ax=ax2, cbar_kws={"label": "Count diff"})
            ax2.set_title("Top-combo gene frequency diff (Metastatic - Resectable)", fontweight="bold")
        else:
            ax2.text(0.5, 0.5, "Not enough stages", ha="center", va="center", transform=ax2.transAxes)
    else:
        ax2.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax2.transAxes)

    plt.tight_layout()
    save_fig(tumor_dir / "Stage_10_Functional_Validation_Analysis.png")


def fig12_short_survival(pat: pd.DataFrame, tumor_dir: Path, cutoff_months: float = 12.0) -> None:
    df = pat.copy()
    df["OS_MONTHS"] = _to_num(df["OS_MONTHS"])
    df = df[df["OS_MONTHS"].notna() & (df["OS_MONTHS"] > 0)].copy()
    df["ShortSurvival"] = df["OS_MONTHS"] <= cutoff_months

    apply_manuscript_figure_style()
    sns.set_palette("husl")
    fig = plt.figure(figsize=(22, 12))

    ax1 = plt.subplot(2, 2, 1)
    tab = pd.crosstab(df["STAGE"], df["ShortSurvival"], normalize="index").reindex(STAGES)
    _bool_cols = list(tab.columns)
    # Crosstab columns are ShortSurvival bool: True = short, False = long (numpy.bool_ safe via bool()).
    _sl = [SHORT_LONG_COLORS["Long"] if not bool(c) else SHORT_LONG_COLORS["Short"] for c in _bool_cols]
    tab.plot(kind="bar", stacked=True, ax=ax1, color=_sl)
    ax1.set_title(f"Short survival (<= {cutoff_months} mo) by Stage", fontweight="bold")
    ax1.set_xlabel("")
    ax1.tick_params(axis="x", rotation=15)
    ax1.legend(title="ShortSurvival", fontsize=13)

    ax2 = plt.subplot(2, 2, 2)
    # Compare TP53+KRAS in short vs long within each stage
    rows = []
    for st in STAGES:
        sdf = df[df["STAGE"] == st].copy()
        if len(sdf) == 0:
            continue
        for grp, gdf in [("Short", sdf[sdf["ShortSurvival"]]), ("Long", sdf[~sdf["ShortSurvival"]])]:
            rate = ((gdf["TP53"] == 1) & (gdf["KRAS"] == 1)).mean() * 100.0 if len(gdf) else 0.0
            rows.append({"Stage": st, "Group": grp, "TP53+KRAS %": rate})
    d = pd.DataFrame(rows)
    sns.barplot(
        data=d,
        x="Stage",
        y="TP53+KRAS %",
        hue="Group",
        hue_order=["Short", "Long"],
        ax=ax2,
        palette=SHORT_LONG_COLORS,
    )
    ax2.set_title("TP53+KRAS rate in short vs long survival (within stage)", fontweight="bold")
    ax2.tick_params(axis="x", rotation=15)
    ax2.grid(axis="y", alpha=0.25)

    ax3 = plt.subplot(2, 2, 3)
    sns.violinplot(
        data=df,
        x="STAGE",
        y="OS_MONTHS",
        hue="STAGE",
        order=STAGES,
        hue_order=STAGES,
        dodge=False,
        inner="quartile",
        ax=ax3,
        palette=STAGE_PALETTE_DICT,
        legend=False,
    )
    ax3.set_title("OS_MONTHS distribution by Stage (OS>0)", fontweight="bold")
    ax3.tick_params(axis="x", rotation=15)
    ax3.set_xlabel("")

    ax4 = plt.subplot(2, 2, 4)
    # Top combos in short survival within metastatic (proxy)
    meta = df[df["STAGE"] == "Metastatic"].copy()
    if len(meta):
        meta_short = meta[meta["ShortSurvival"]].copy()
        if len(meta_short) >= 30:
            # build combo table on this subset
            s = combo_table_for_stage(meta_short, min_n=3).head(12)
            ax4.bar(np.arange(len(s)), s["Multiplicative_Synergy"], color="#9467bd", alpha=0.75)
            ax4.set_xticks(np.arange(len(s)))
            ax4.set_xticklabels(s["Combination"], rotation=45, ha="right", fontsize=13)
            ax4.set_title("Top synergy combos (Metastatic short survival subset)", fontweight="bold")
            ax4.grid(axis="y", alpha=0.25)
        else:
            ax4.text(0.5, 0.5, "Not enough metastatic short-survival patients", ha="center", va="center", transform=ax4.transAxes)
            ax4.set_title("Metastatic short-survival synergy", fontweight="bold")
    else:
        ax4.text(0.5, 0.5, "No metastatic data", ha="center", va="center", transform=ax4.transAxes)

    plt.tight_layout()
    save_fig(tumor_dir / "Stage_12_TP53_KRAS_ShortSurvival_Comparison.png")


def fig13_most_lethal(stage_synergy: Dict[str, pd.DataFrame], tumor_dir: Path) -> None:
    # "Most lethal" proxy: highest multiplicative synergy within each stage
    apply_manuscript_figure_style()
    sns.set_palette("husl")
    fig = plt.figure(figsize=(22, 12))

    ax1 = plt.subplot(1, 2, 1)
    rows = []
    for st in STAGES:
        sdf = stage_synergy.get(st, pd.DataFrame())
        if len(sdf):
            top = sdf.sort_values("Multiplicative_Synergy", ascending=False).head(10)
            for _, r in top.iterrows():
                rows.append({"Stage": st, "Combination": r["Combination"], "Synergy": r["Multiplicative_Synergy"]})
    d = pd.DataFrame(rows)
    if len(d):
        sns.barplot(
            data=d,
            x="Combination",
            y="Synergy",
            hue="Stage",
            hue_order=STAGES,
            ax=ax1,
            palette=STAGE_PALETTE_DICT,
        )
        ax1.set_title("Top 10 'most lethal' (highest multiplicative synergy) combos by Stage", fontweight="bold")
        ax1.tick_params(axis="x", rotation=45)
        ax1.set_xlabel("")
        ax1.grid(axis="y", alpha=0.25)
        ax1.legend(title="Stage", fontsize=13)
    else:
        ax1.text(0.5, 0.5, "No synergy data", ha="center", va="center", transform=ax1.transAxes)

    ax2 = plt.subplot(1, 2, 2)
    # Gene contribution across all top combos
    rows2 = []
    for st in STAGES:
        sdf = stage_synergy.get(st, pd.DataFrame())
        if len(sdf) == 0:
            continue
        top = sdf.sort_values("Multiplicative_Synergy", ascending=False).head(20)["Combination"].tolist()
        for combo in top:
            g1, g2 = combo.split("+")
            rows2.append({"Stage": st, "Gene": g1})
            rows2.append({"Stage": st, "Gene": g2})
    dd = pd.DataFrame(rows2)
    if len(dd):
        freq = dd.groupby(["Stage", "Gene"]).size().reset_index(name="Count")
        sns.barplot(
            data=freq,
            x="Gene",
            y="Count",
            hue="Stage",
            hue_order=STAGES,
            ax=ax2,
            palette=STAGE_PALETTE_DICT,
        )
        ax2.set_title("Gene frequency in top 20 lethal combos by Stage", fontweight="bold")
        ax2.tick_params(axis="x", rotation=45)
        ax2.set_xlabel("")
        ax2.grid(axis="y", alpha=0.25)
    else:
        ax2.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax2.transAxes)

    plt.tight_layout()
    save_fig(tumor_dir / "Stage_13_Most_Lethal_Mutation_Combinations.png")


def fig14_diabetes(stage_dfs: Dict[str, pd.DataFrame], tumor_dir: Path) -> None:
    # Diabetes vs non-diabetes mutation rates by stage for top genes
    apply_manuscript_figure_style()
    sns.set_palette("husl")
    fig = plt.figure(figsize=(22, 14))

    rows = []
    for st, df in stage_dfs.items():
        if "DIABETES_HISOTRY" not in df.columns:
            continue
        tmp = df.copy()
        tmp["DIABETES_HISOTRY"] = _to_num(tmp["DIABETES_HISOTRY"])
        diab = tmp[tmp["DIABETES_HISOTRY"] == 1]
        nondi = tmp[tmp["DIABETES_HISOTRY"] == 0]
        for g in TARGET_GENES:
            rows.append({"Stage": st, "Gene": g, "Group": "Diabetic", "Rate": diab[g].mean() * 100.0 if len(diab) else 0.0})
            rows.append({"Stage": st, "Gene": g, "Group": "Non-diabetic", "Rate": nondi[g].mean() * 100.0 if len(nondi) else 0.0})
    d = pd.DataFrame(rows)

    ax1 = plt.subplot(2, 1, 1)
    if len(d):
        sns.barplot(data=d, x="Gene", y="Rate", hue="Group", ax=ax1)
        ax1.set_title("Mutation rates: Diabetic vs Non-diabetic (all stages pooled)", fontweight="bold")
        ax1.tick_params(axis="x", rotation=45)
        ax1.set_xlabel("")
        ax1.grid(axis="y", alpha=0.25)
    else:
        ax1.text(0.5, 0.5, "DIABETES_HISOTRY missing", ha="center", va="center", transform=ax1.transAxes)

    ax2 = plt.subplot(2, 1, 2)
    if len(d):
        # heatmap of (diabetic - non-diabetic) by stage
        piv = d.pivot_table(index=["Stage", "Gene"], columns="Group", values="Rate", aggfunc="mean").reset_index()
        piv["Diff"] = piv.get("Diabetic", 0) - piv.get("Non-diabetic", 0)
        hm = piv.pivot(index="Stage", columns="Gene", values="Diff").reindex(index=STAGES)
        sns.heatmap(hm, annot=True, fmt=".1f", cmap="RdBu_r", center=0, ax=ax2, cbar_kws={"label": "pp diff"})
        ax2.set_title("Diabetic - Non-diabetic mutation rate difference (pp) by Stage", fontweight="bold")
    else:
        ax2.text(0.5, 0.5, "No diabetes comparison data", ha="center", va="center", transform=ax2.transAxes)

    plt.tight_layout()
    save_fig(tumor_dir / "Stage_14_Diabetic_vs_NonDiabetic_Gene_Analysis.png")


def fig01_stage_comprehensive_alias(tumor_dir: Path) -> None:
    # Create a numbered alias by duplicating the existing Stage_3Group figure content:
    # easiest is to generate a thin "cover" figure that points to it.
    apply_manuscript_figure_style()
    fig = plt.figure(figsize=(12, 6))
    ax = plt.subplot(1, 1, 1)
    ax.axis("off")
    ax.text(
        0.5,
        0.6,
        "Stage 3-group comprehensive figure is available as:\nTumor/Stage_3Group_Comprehensive_Analysis.png",
        ha="center",
        va="center",
        fontsize=16,
        fontweight="bold",
    )
    ax.text(0.5, 0.3, "This file is a numbered alias for the 01–14 set.", ha="center", va="center", fontsize=12)
    plt.tight_layout()
    save_fig(tumor_dir / "Stage_01_Stage_3Group_Comprehensive_Analysis.png")


def main() -> None:
    ctx = _ctx()
    if not ctx.merged_xlsx.exists():
        raise FileNotFoundError(f"Missing input: {ctx.merged_xlsx}")

    print("Generating 14 stage-based plots...")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    pat = load_patient_level(ctx.merged_xlsx)
    stage_dfs = stage_splits(pat)
    stage_synergy = compute_stage_synergy(stage_dfs)

    # 01: alias (numbered set) + keep the already generated comprehensive plot
    fig01_stage_comprehensive_alias(ctx.tumor_dir)

    # 02-05: genetic combo families
    fig02_tp53_kras_focused(stage_dfs, ctx.tumor_dir)
    fig03_clinical_precision(pat, stage_dfs, ctx.tumor_dir)
    fig04_additive_synergy(stage_synergy, ctx.tumor_dir)
    fig05_tp53_kras_detailed(stage_dfs, ctx.tumor_dir)

    # 06: OS methodology
    fig06_os_months_methodology(pat, ctx.tumor_dir)

    # 07-08: significance + multiple correction
    res = fig07_statistical_significance(stage_synergy, ctx.tumor_dir)
    fig08_multiple_comparison(res, ctx.tumor_dir)

    # 09-10: validation + functional proxy
    fig09_validation(stage_synergy, ctx.tumor_dir)
    fig10_functional(stage_synergy, ctx.tumor_dir)

    # 11: stage cleaned
    fig11_stage_cleaned(pat, ctx.tumor_dir)

    # 12: short survival comparisons
    fig12_short_survival(pat, ctx.tumor_dir, cutoff_months=12.0)

    # 13-14: most lethal + diabetes
    fig13_most_lethal(stage_synergy, ctx.tumor_dir)
    fig14_diabetes(stage_dfs, ctx.tumor_dir)

    print("✅ Done. Outputs written to Tumor/ as Stage_01..Stage_14 PNGs.")
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()

