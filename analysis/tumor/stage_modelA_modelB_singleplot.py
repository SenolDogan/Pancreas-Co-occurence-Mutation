#!/usr/bin/env python3
"""
Single plot: Model A vs Model B (stage-specific Cox)
====================================================

Creates one forest plot that shows:
  - Model A (signature + AGE + SEX) per stage
  - Model B (TP53/ARID1A/SMAD4 + AGE + SEX + tx proxies) per stage

Input:
  Tumor/Merged.xlsx

Output:
  Tumor/Stage_ModelA_ModelB_ForestPlot.png
"""

from __future__ import annotations

import warnings
warnings.filterwarnings("ignore")

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from lifelines import CoxPHFitter
from manuscript_figure_style import apply_manuscript_figure_style, short_stage_label


STAGES = [
    "Metastatic",
    "Resectable",
    "Borderline Resectable/Locally Advanced",
]

GENES = ["TP53", "KRAS", "CDKN2A", "SMAD4", "ARID1A", "ATM", "PIK3CA", "BRAF", "GNAS", "RNF43"]

MODEL_A_SIG = {
    "Metastatic": "sig_TP53_KRAS_ARID1A",
    "Resectable": "sig_TP53_KRAS_ARID1A",
    "Borderline Resectable/Locally Advanced": "sig_TP53_KRAS_SMAD4",
}


def _to_num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")


def load_patient_level(xlsx: Path) -> pd.DataFrame:
    df = pd.read_excel(xlsx, sheet_name=0)
    pat = df.groupby("PATIENT_ID").first().reset_index()
    mut_list = df.groupby("PATIENT_ID")["Hugo_Symbol"].apply(list)
    for g in GENES:
        pat[g] = pat["PATIENT_ID"].map(mut_list.apply(lambda xs: 1 if g in xs else 0)).fillna(0).astype(int)

    pat["STAGE"] = pat["STAGE"].astype(str)
    pat = pat[pat["STAGE"].isin(STAGES)].copy()

    pat["OS_MONTHS"] = _to_num(pat["OS_MONTHS"])
    pat["event"] = (pat["OS_STATUS"].astype(str) == "1:DECEASED").astype(int)
    pat = pat[pat["OS_MONTHS"].notna() & (pat["OS_MONTHS"] > 0)].copy()

    pat["AGE_num"] = _to_num(pat.get("AGE", np.nan))
    pat["AGE_num"] = pat["AGE_num"].fillna(pat["AGE_num"].median())
    pat["SEX"] = pat.get("SEX", "Missing").where(pat.get("SEX", "Missing").notna(), "Missing").astype(str)

    # treatment proxies
    pat["TARGETED_THERAPY_bin"] = _to_num(pat.get("TARGETED_THERAPY", 0)).fillna(0).clip(0, 1)
    pat["SYSTEMIC_TX_any"] = _to_num(pat.get("SYSTEMIC_TX", 0)).fillna(0).clip(0, 1)

    # signatures
    pat["sig_TP53_KRAS_ARID1A"] = ((pat.TP53 == 1) & (pat.KRAS == 1) & (pat.ARID1A == 1)).astype(int)
    pat["sig_TP53_KRAS_SMAD4"] = ((pat.TP53 == 1) & (pat.KRAS == 1) & (pat.SMAD4 == 1)).astype(int)
    return pat


def design_matrix(stage_df: pd.DataFrame, covs: List[str]) -> pd.DataFrame:
    d = stage_df.copy()
    sex = pd.get_dummies(d["SEX"].astype(str), prefix="SEX", drop_first=True)
    X = pd.concat([d[["OS_MONTHS", "event"] + covs].copy(), sex], axis=1)
    # drop near-constant covariates
    keep = ["OS_MONTHS", "event"]
    cov_cols = [c for c in X.columns if c not in keep]
    var = X[cov_cols].var(numeric_only=True)
    good = var[var > 1e-6].index.tolist()
    return X[keep + good].copy()


def fit_cox_extract(X: pd.DataFrame, feature: str, penalizer: float) -> Dict[str, float]:
    cph = CoxPHFitter(penalizer=penalizer)
    cph.fit(X, duration_col="OS_MONTHS", event_col="event", show_progress=False)
    s = cph.summary
    if feature not in s.index:
        return {}
    coef = float(s.loc[feature, "coef"])
    hr = float(np.exp(coef))
    ci_lo = float(np.exp(s.loc[feature, "coef lower 95%"]))
    ci_hi = float(np.exp(s.loc[feature, "coef upper 95%"]))
    p = float(s.loc[feature, "p"])
    return {"HR": hr, "CI_lo": ci_lo, "CI_hi": ci_hi, "p": p}


def main() -> None:
    tumor_dir = Path(__file__).resolve().parent
    xlsx = tumor_dir / "Merged.xlsx"
    out_png = tumor_dir / "Stage_ModelA_ModelB_ForestPlot.png"

    pat = load_patient_level(xlsx)

    rows = []
    for stage in STAGES:
        sdf = pat[pat["STAGE"] == stage].copy()
        if len(sdf) == 0:
            continue

        # Model A
        sig = MODEL_A_SIG[stage]
        covs_A = [sig, "AGE_num"]
        X_A = design_matrix(sdf, covs_A)
        if sig in X_A.columns and int(X_A[sig].sum()) >= 20:
            st = fit_cox_extract(X_A, sig, penalizer=0.2)
            if st:
                rows.append(
                    {
                        "Stage": stage,
                        "Model": "A",
                        "Feature": sig.replace("sig_", "").replace("_", "+"),
                        "HR": st["HR"],
                        "CI_lo": st["CI_lo"],
                        "CI_hi": st["CI_hi"],
                        "p": st["p"],
                        "n_pos": int(X_A[sig].sum()),
                    }
                )

        # Model B
        covs_B = ["TP53", "ARID1A", "SMAD4", "AGE_num", "TARGETED_THERAPY_bin", "SYSTEMIC_TX_any"]
        X_B = design_matrix(sdf, covs_B)
        for feat in ["TP53", "ARID1A", "SMAD4"]:
            if feat in X_B.columns and int(X_B[feat].sum()) >= 20:
                st = fit_cox_extract(X_B, feat, penalizer=0.5)
                if st:
                    rows.append(
                        {
                            "Stage": stage,
                            "Model": "B",
                            "Feature": feat,
                            "HR": st["HR"],
                            "CI_lo": st["CI_lo"],
                            "CI_hi": st["CI_hi"],
                            "p": st["p"],
                            "n_pos": int(X_B[feat].sum()),
                        }
                    )

    res = pd.DataFrame(rows)
    if len(res) == 0:
        raise RuntimeError("No results to plot.")

    stage_i = {s: i for i, s in enumerate(STAGES)}
    model_i = {"A": 0, "B": 1}
    feat_order = {
        # keep key signatures first
        "TP53+KRAS+ARID1A": 0,
        "TP53+KRAS+SMAD4": 0,
        "TP53": 1,
        "ARID1A": 2,
        "SMAD4": 3,
    }
    res["stage_i"] = res["Stage"].map(stage_i)
    res["model_i"] = res["Model"].map(model_i)
    res["feat_i"] = res["Feature"].map(feat_order).fillna(9)
    res = res.sort_values(["stage_i", "model_i", "feat_i", "p"]).reset_index(drop=True)

    # y positions with gaps between stages
    y = []
    cur = 0
    for st in STAGES:
        block = res[res["Stage"] == st]
        for _ in range(len(block)):
            y.append(cur)
            cur += 1
        cur += 1
    res["y"] = y[: len(res)]

    colors = {"A": "#9467bd", "B": "#1f77b4"}

    apply_manuscript_figure_style()
    fig = plt.figure(figsize=(14, max(8, 0.5 * len(res) + 2)))
    ax = plt.subplot(1, 1, 1)

    for _, r in res.iterrows():
        c = colors.get(r["Model"], "#333333")
        ax.plot([r["CI_lo"], r["CI_hi"]], [r["y"], r["y"]], color=c, lw=2, alpha=0.9)
        ax.scatter([r["HR"]], [r["y"]], color=c, s=55, zorder=3)
        ax.text(
            1.02,
            r["y"],
            f"Model {r['Model']} | n={int(r['n_pos'])} | p={r['p']:.4f}",
            va="center",
            ha="left",
            transform=ax.get_yaxis_transform(),
            fontsize=13,
        )

    ax.axvline(1.0, color="black", ls="--", lw=1, alpha=0.6)
    ax.set_xscale("log")
    ax.set_xlabel("Hazard Ratio (log scale) — HR>1 worse OS")
    ax.set_title("Stage-specific Cox: Model A vs Model B (key effects)", fontweight="bold")

    ax.set_yticks(res["y"].tolist())
    ax.set_yticklabels([f"{short_stage_label(row.Stage)}: {row.Feature}" for row in res.itertuples(index=False)])
    ax.grid(axis="x", alpha=0.25)

    handles = [
        plt.Line2D([0], [0], color=colors["A"], lw=2, marker="o", label="Model A (signature + AGE + SEX)"),
        plt.Line2D([0], [0], color=colors["B"], lw=2, marker="o", label="Model B (genes + AGE + SEX + tx proxies)"),
    ]
    ax.legend(handles=handles, loc="lower right", frameon=True)

    plt.tight_layout()
    plt.savefig(out_png, dpi=350, bbox_inches="tight")
    plt.close()

    print(f"✅ Saved: {out_png}")


if __name__ == "__main__":
    main()
