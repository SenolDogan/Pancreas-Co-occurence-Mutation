#!/usr/bin/env python3
"""
Stage-specific OS effect summary (single plot)
=============================================

Creates one clean forest plot summarizing the strongest OS-associated
genes / co-occurrences (pairs, triples) within each of the 3 stage groups.

Input:
  Tumor/Merged.xlsx

Output:
  Tumor/Stage_OS_Effect_ForestPlot.png
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from manuscript_figure_style import apply_manuscript_figure_style, short_stage_label


STAGES = [
    "Metastatic",
    "Resectable",
    "Borderline Resectable/Locally Advanced",
]

GENES = ["TP53", "KRAS", "CDKN2A", "SMAD4", "ARID1A", "ATM", "PIK3CA", "BRAF", "GNAS", "RNF43"]


@dataclass(frozen=True)
class Feature:
    stage: str
    label: str
    kind: str  # single/pair/triple
    mask_fn: Callable[[pd.DataFrame], pd.Series]


def _to_num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")


def load_patient_level(merged_xlsx: Path) -> pd.DataFrame:
    df = pd.read_excel(merged_xlsx, sheet_name=0)
    needed = {"PATIENT_ID", "Hugo_Symbol", "STAGE", "OS_MONTHS", "OS_STATUS"}
    missing = needed - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    pat = df.groupby("PATIENT_ID").first().reset_index()
    mut_list = df.groupby("PATIENT_ID")["Hugo_Symbol"].apply(list)
    for g in GENES:
        pat[g] = pat["PATIENT_ID"].map(mut_list.apply(lambda xs: 1 if g in xs else 0)).fillna(0).astype(int)

    pat["STAGE"] = pat["STAGE"].astype(str)
    pat = pat[pat["STAGE"].isin(STAGES)].copy()
    pat["OS_MONTHS"] = _to_num(pat["OS_MONTHS"])
    pat["event"] = (pat["OS_STATUS"].astype(str) == "1:DECEASED").astype(int)

    # clean survival time
    pat = pat[pat["OS_MONTHS"].notna() & (pat["OS_MONTHS"] > 0)].copy()
    return pat


def cox_univariate(stage_df: pd.DataFrame, x: pd.Series) -> Dict[str, float]:
    from lifelines import CoxPHFitter

    tmp = pd.DataFrame({"OS_MONTHS": stage_df["OS_MONTHS"].values, "event": stage_df["event"].values, "x": x.astype(int).values})
    cph = CoxPHFitter()
    cph.fit(tmp, duration_col="OS_MONTHS", event_col="event", show_progress=False)

    beta = float(cph.params_["x"])
    hr = float(np.exp(beta))
    p = float(cph.summary.loc["x", "p"])
    ci = cph.confidence_intervals_.loc["x"].tolist()  # log-scale
    ci_lo = float(np.exp(ci[0]))
    ci_hi = float(np.exp(ci[1]))
    return {"HR": hr, "p": p, "CI_lo": ci_lo, "CI_hi": ci_hi}


def build_features() -> List[Feature]:
    feats: List[Feature] = []

    # Metastatic signatures
    feats += [
        Feature("Metastatic", "TP53", "single", lambda d: d["TP53"] == 1),
        Feature("Metastatic", "TP53+KRAS", "pair", lambda d: (d["TP53"] == 1) & (d["KRAS"] == 1)),
        Feature("Metastatic", "TP53+ARID1A", "pair", lambda d: (d["TP53"] == 1) & (d["ARID1A"] == 1)),
        Feature("Metastatic", "TP53+KRAS+ARID1A", "triple", lambda d: (d["TP53"] == 1) & (d["KRAS"] == 1) & (d["ARID1A"] == 1)),
        Feature("Metastatic", "TP53+KRAS+CDKN2A", "triple", lambda d: (d["TP53"] == 1) & (d["KRAS"] == 1) & (d["CDKN2A"] == 1)),
    ]

    # Resectable signatures
    feats += [
        Feature("Resectable", "TP53", "single", lambda d: d["TP53"] == 1),
        Feature("Resectable", "TP53+KRAS", "pair", lambda d: (d["TP53"] == 1) & (d["KRAS"] == 1)),
        Feature("Resectable", "TP53+ARID1A", "pair", lambda d: (d["TP53"] == 1) & (d["ARID1A"] == 1)),
        Feature("Resectable", "TP53+KRAS+ARID1A", "triple", lambda d: (d["TP53"] == 1) & (d["KRAS"] == 1) & (d["ARID1A"] == 1)),
    ]

    # Borderline/LA signatures (SMAD4 axis)
    feats += [
        Feature("Borderline Resectable/Locally Advanced", "SMAD4", "single", lambda d: d["SMAD4"] == 1),
        Feature("Borderline Resectable/Locally Advanced", "KRAS+SMAD4", "pair", lambda d: (d["KRAS"] == 1) & (d["SMAD4"] == 1)),
        Feature("Borderline Resectable/Locally Advanced", "TP53+SMAD4", "pair", lambda d: (d["TP53"] == 1) & (d["SMAD4"] == 1)),
        Feature("Borderline Resectable/Locally Advanced", "TP53+KRAS+SMAD4", "triple", lambda d: (d["TP53"] == 1) & (d["KRAS"] == 1) & (d["SMAD4"] == 1)),
        Feature("Borderline Resectable/Locally Advanced", "TP53+KRAS", "pair", lambda d: (d["TP53"] == 1) & (d["KRAS"] == 1)),
    ]

    return feats


def main() -> None:
    tumor_dir = Path(__file__).resolve().parent
    merged_xlsx = tumor_dir / "Merged.xlsx"
    out_png = tumor_dir / "Stage_OS_Effect_ForestPlot.png"

    pat = load_patient_level(merged_xlsx)

    # Evaluate features
    rows = []
    for f in build_features():
        sdf = pat[pat["STAGE"] == f.stage].copy()
        if len(sdf) == 0:
            continue
        x = f.mask_fn(sdf).astype(int)
        n_pos = int(x.sum())
        n_neg = int((1 - x).sum())
        # ensure enough samples to avoid unstable fits
        if n_pos < 20 or n_neg < 40:
            continue
        stats = cox_univariate(sdf, x)
        med_pos = float(sdf.loc[x == 1, "OS_MONTHS"].median())
        med_neg = float(sdf.loc[x == 0, "OS_MONTHS"].median())
        rows.append(
            {
                "Stage": f.stage,
                "Feature": f.label,
                "Kind": f.kind,
                "n_pos": n_pos,
                "HR": stats["HR"],
                "CI_lo": stats["CI_lo"],
                "CI_hi": stats["CI_hi"],
                "p": stats["p"],
                "Median_pos": med_pos,
                "Median_neg": med_neg,
                "Delta_median": med_pos - med_neg,
            }
        )

    res = pd.DataFrame(rows)
    if len(res) == 0:
        raise RuntimeError("No features passed thresholds; cannot draw plot.")

    # Order: stage blocks, and within stage by p then HR
    stage_order = {s: i for i, s in enumerate(STAGES)}
    kind_order = {"single": 0, "pair": 1, "triple": 2}
    res["stage_i"] = res["Stage"].map(stage_order)
    res["kind_i"] = res["Kind"].map(kind_order).fillna(9)
    res = res.sort_values(["stage_i", "kind_i", "p"], ascending=[True, True, True]).reset_index(drop=True)

    # y positions with gaps between stages
    y = []
    cur = 0
    stage_breaks = []
    for st in STAGES:
        block = res[res["Stage"] == st]
        if len(block) == 0:
            continue
        start = cur
        for _ in range(len(block)):
            y.append(cur)
            cur += 1
        stage_breaks.append((st, start, cur - 1))
        cur += 1  # gap
    res = res.copy()
    res["y"] = y[: len(res)]

    # Plot
    apply_manuscript_figure_style()
    fig = plt.figure(figsize=(14, max(8, 0.55 * len(res) + 2)))
    ax = plt.subplot(1, 1, 1)

    colors = {"single": "#1f77b4", "pair": "#d62728", "triple": "#9467bd"}

    for _, r in res.iterrows():
        c = colors.get(r["Kind"], "#333333")
        ax.plot([r["CI_lo"], r["CI_hi"]], [r["y"], r["y"]], color=c, lw=2, alpha=0.9)
        ax.scatter([r["HR"]], [r["y"]], color=c, s=55, zorder=3)

        # right-side annotation
        ax.text(
            1.02,
            r["y"],
            f"n={int(r['n_pos'])} | p={r['p']:.4f} | Δmed={r['Delta_median']:+.1f} mo",
            va="center",
            ha="left",
            transform=ax.get_yaxis_transform(),
            fontsize=13,
        )

    ax.axvline(1.0, color="black", ls="--", lw=1, alpha=0.6)
    ax.set_xscale("log")
    ax.set_xlabel("Hazard Ratio (log scale)  —  HR>1 worse OS")
    ax.set_title("Stage-specific OS effect (univariate Cox): key genes & co-occurrences", fontweight="bold")

    ax.set_yticks(res["y"].tolist())
    ax.set_yticklabels([f"{short_stage_label(row.Stage)}: {row.Feature}" for row in res.itertuples(index=False)])
    ax.grid(axis="x", alpha=0.25)

    # legend
    handles = [
        plt.Line2D([0], [0], color=colors["single"], lw=2, marker="o", label="Single gene"),
        plt.Line2D([0], [0], color=colors["pair"], lw=2, marker="o", label="Pair co-occurrence"),
        plt.Line2D([0], [0], color=colors["triple"], lw=2, marker="o", label="Triple co-occurrence"),
    ]
    ax.legend(handles=handles, loc="lower right", frameon=True)

    plt.tight_layout()
    out_png.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_png, dpi=350, bbox_inches="tight")
    plt.close()

    print(f"✅ Saved: {out_png}")


if __name__ == "__main__":
    main()

