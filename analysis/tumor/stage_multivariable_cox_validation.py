#!/usr/bin/env python3
"""
Stage-specific multivariable Cox models + internal validation
============================================================

What this does
--------------
For each stage group, fits multivariable Cox models that include:
  - Key genetic signatures (single/pair/triple)
  - Clinical covariates (AGE, SEX, ANCESTRY)
  - Treatment proxies (TARGETED_THERAPY, ADJ/NEOADJ, SYSTEMIC_TX presence)

Then performs repeated stratified train/validation splits to estimate:
  - C-index on validation
  - Stability of HR direction for each key genetic signature

Input:
  Tumor/Merged.xlsx

Outputs:
  Tumor/Stage_Multivariable_Cox_Report.xlsx
  Tumor/Stage_Multivariable_Cox_Validation.png
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from manuscript_figure_style import apply_manuscript_figure_style


STAGES = [
    "Metastatic",
    "Resectable",
    "Borderline Resectable/Locally Advanced",
]

STAGE_COLORS = {
    "Metastatic": "#E65100",
    "Resectable": "#2E7D32",
    "Borderline Resectable/Locally Advanced": "#FFEE58",
}

GENES = ["TP53", "KRAS", "CDKN2A", "SMAD4", "ARID1A", "ATM", "PIK3CA", "BRAF", "GNAS", "RNF43"]


def _to_num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")


def load_patient_level(merged_xlsx: Path) -> pd.DataFrame:
    df = pd.read_excel(merged_xlsx, sheet_name=0)
    needed = {"PATIENT_ID", "Hugo_Symbol", "STAGE", "OS_MONTHS", "OS_STATUS"}
    missing = needed - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    # patient-level clinical (first row per patient)
    clinical_cols = [
        "PATIENT_ID",
        "STAGE",
        "OS_MONTHS",
        "OS_STATUS",
        "AGE",
        "SEX",
        "ANCESTRY",
        "TARGETED_THERAPY",
        "ADJ_TREATMENT",
        "NEOADJ_TREATMENT",
        "SYSTEMIC_TX",
        "SYSTEMIC_TX_1",
    ]
    clinical_cols = [c for c in clinical_cols if c in df.columns]
    pat = df.groupby("PATIENT_ID")[clinical_cols].first().reset_index(drop=True)

    # mutation presence per patient
    mut_list = df.groupby("PATIENT_ID")["Hugo_Symbol"].apply(list)
    for g in GENES:
        pat[g] = pat["PATIENT_ID"].map(mut_list.apply(lambda xs: 1 if g in xs else 0)).fillna(0).astype(int)

    pat["STAGE"] = pat["STAGE"].astype(str)
    pat = pat[pat["STAGE"].isin(STAGES)].copy()
    pat["OS_MONTHS"] = _to_num(pat["OS_MONTHS"])
    pat["event"] = (pat["OS_STATUS"].astype(str) == "1:DECEASED").astype(int)
    pat = pat[pat["OS_MONTHS"].notna() & (pat["OS_MONTHS"] > 0)].copy()

    # covariates
    pat["AGE_num"] = _to_num(pat.get("AGE", np.nan))
    pat["SEX"] = pat.get("SEX", "Missing").where(pat.get("SEX", "Missing").notna(), "Missing").astype(str)
    pat["ANCESTRY"] = pat.get("ANCESTRY", "Missing").where(pat.get("ANCESTRY", "Missing").notna(), "Missing").astype(str)

    # treatment proxies (binary presence)
    if "TARGETED_THERAPY" in pat.columns:
        pat["TARGETED_THERAPY_bin"] = _to_num(pat["TARGETED_THERAPY"]).fillna(0).clip(0, 1)
    else:
        pat["TARGETED_THERAPY_bin"] = 0

    def nonnull_nonempty(x):
        if pd.isna(x):
            return 0
        s = str(x).strip().lower()
        return 0 if s in ("", "nan", "none") else 1

    if "ADJ_TREATMENT" in pat.columns:
        pat["ADJ_TREATMENT_any"] = pat["ADJ_TREATMENT"].apply(nonnull_nonempty).astype(int)
    else:
        pat["ADJ_TREATMENT_any"] = 0

    if "NEOADJ_TREATMENT" in pat.columns:
        pat["NEOADJ_TREATMENT_any"] = pat["NEOADJ_TREATMENT"].apply(nonnull_nonempty).astype(int)
    else:
        pat["NEOADJ_TREATMENT_any"] = 0

    if "SYSTEMIC_TX" in pat.columns:
        # already looks like 0/1 with missing; treat missing as 0
        pat["SYSTEMIC_TX_any"] = _to_num(pat["SYSTEMIC_TX"]).fillna(0).clip(0, 1)
    else:
        pat["SYSTEMIC_TX_any"] = 0

    return pat


def add_signature_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    # signatures from the univariate screening
    out["sig_TP53_ARID1A"] = ((out["TP53"] == 1) & (out["ARID1A"] == 1)).astype(int)
    out["sig_TP53_KRAS"] = ((out["TP53"] == 1) & (out["KRAS"] == 1)).astype(int)
    out["sig_TP53_KRAS_ARID1A"] = ((out["TP53"] == 1) & (out["KRAS"] == 1) & (out["ARID1A"] == 1)).astype(int)
    out["sig_TP53_KRAS_CDKN2A"] = ((out["TP53"] == 1) & (out["KRAS"] == 1) & (out["CDKN2A"] == 1)).astype(int)
    out["sig_KRAS_SMAD4"] = ((out["KRAS"] == 1) & (out["SMAD4"] == 1)).astype(int)
    out["sig_TP53_SMAD4"] = ((out["TP53"] == 1) & (out["SMAD4"] == 1)).astype(int)
    out["sig_TP53_KRAS_SMAD4"] = ((out["TP53"] == 1) & (out["KRAS"] == 1) & (out["SMAD4"] == 1)).astype(int)
    return out


def prepare_design(stage_df: pd.DataFrame, min_pos: int = 20) -> Tuple[pd.DataFrame, List[str]]:
    """
    Returns a modeling dataframe with:
      OS_MONTHS, event, and covariates (numeric + one-hot categorical)
    """
    d = stage_df.copy()

    # Base covariates
    base_cols = ["AGE_num", "TARGETED_THERAPY_bin", "ADJ_TREATMENT_any", "NEOADJ_TREATMENT_any", "SYSTEMIC_TX_any"]
    for c in base_cols:
        if c not in d.columns:
            d[c] = 0

    # Key signatures; drop those with too few positives in this stage
    sig_cols = [
        "TP53",
        "SMAD4",
        "ARID1A",
        "sig_TP53_ARID1A",
        "sig_TP53_KRAS",
        "sig_TP53_KRAS_ARID1A",
        "sig_TP53_KRAS_CDKN2A",
        "sig_KRAS_SMAD4",
        "sig_TP53_SMAD4",
        "sig_TP53_KRAS_SMAD4",
    ]
    sig_keep = []
    for c in sig_cols:
        if c in d.columns and int(d[c].sum()) >= min_pos and int((1 - d[c]).sum()) >= 40:
            sig_keep.append(c)

    # One-hot for SEX and ANCESTRY (drop first)
    cat = pd.get_dummies(d[["SEX", "ANCESTRY"]].astype(str), drop_first=True, prefix=["SEX", "ANC"])

    model_df = pd.concat(
        [
            d[["OS_MONTHS", "event"] + base_cols + sig_keep].copy(),
            cat,
        ],
        axis=1,
    )

    # clean missing
    model_df["AGE_num"] = _to_num(model_df["AGE_num"])
    model_df = model_df.dropna(subset=["OS_MONTHS", "event"])
    model_df["AGE_num"] = model_df["AGE_num"].fillna(model_df["AGE_num"].median())

    covariates = [c for c in model_df.columns if c not in ("OS_MONTHS", "event")]
    return model_df, covariates


def fit_cox(model_df: pd.DataFrame, penalizer: float = 0.1) -> pd.DataFrame:
    from lifelines import CoxPHFitter

    cph = CoxPHFitter(penalizer=penalizer)
    cph.fit(model_df, duration_col="OS_MONTHS", event_col="event", show_progress=False)
    summ = cph.summary.copy()
    # Return HR-scale
    out = pd.DataFrame(
        {
            "coef": summ["coef"],
            "HR": np.exp(summ["coef"]),
            "p": summ["p"],
            "CI_lo": np.exp(summ["coef lower 95%"]),
            "CI_hi": np.exp(summ["coef upper 95%"]),
        }
    ).reset_index(names=["Covariate"])
    return out


def drop_low_variance_covariates(df: pd.DataFrame, min_var: float = 1e-6) -> pd.DataFrame:
    """
    Drop covariate columns with (near) zero variance to improve convergence.
    Keeps OS_MONTHS and event always.
    """
    keep = ["OS_MONTHS", "event"]
    covs = [c for c in df.columns if c not in keep]
    variances = df[covs].var(numeric_only=True)
    good = variances[variances > min_var].index.tolist()
    return df[keep + good].copy()


def stratified_split(df: pd.DataFrame, event_col: str = "event", train_frac: float = 0.7, rng=None):
    if rng is None:
        rng = np.random.default_rng(0)
    ev = df[df[event_col] == 1].index.to_numpy()
    ne = df[df[event_col] == 0].index.to_numpy()
    rng.shuffle(ev)
    rng.shuffle(ne)
    n_ev = int(len(ev) * train_frac)
    n_ne = int(len(ne) * train_frac)
    train_idx = np.concatenate([ev[:n_ev], ne[:n_ne]])
    val_idx = np.concatenate([ev[n_ev:], ne[n_ne:]])
    return df.loc[train_idx].copy(), df.loc[val_idx].copy()


def c_index_on_val(train_df: pd.DataFrame, val_df: pd.DataFrame, penalizer: float = 0.1) -> float:
    from lifelines import CoxPHFitter
    from lifelines.utils import concordance_index

    cph = CoxPHFitter(penalizer=penalizer)
    cph.fit(train_df, duration_col="OS_MONTHS", event_col="event", show_progress=False)
    # partial hazard as risk score
    risk = cph.predict_partial_hazard(val_df)
    return float(concordance_index(val_df["OS_MONTHS"], -risk.values.ravel(), val_df["event"]))


def main() -> None:
    tumor_dir = Path(__file__).resolve().parent
    merged = tumor_dir / "Merged.xlsx"
    out_xlsx = tumor_dir / "Stage_Multivariable_Cox_Report.xlsx"
    out_png = tumor_dir / "Stage_Multivariable_Cox_Validation.png"

    pat = add_signature_columns(load_patient_level(merged))

    stage_results = {}
    val_rows = []

    # Fit per stage + validation
    for stage in STAGES:
        sdf = pat[pat["STAGE"] == stage].copy().reset_index(drop=True)
        model_df, covs = prepare_design(sdf, min_pos=20)
        model_df = drop_low_variance_covariates(model_df, min_var=1e-6)
        if len(model_df) < 200:
            continue

        # Fit model
        # Use stronger penalization to reduce singular matrix risk
        fit_df = fit_cox(model_df, penalizer=0.5)
        fit_df.insert(0, "Stage", stage)
        stage_results[stage] = fit_df

        # Repeated internal validation splits
        rng = np.random.default_rng(42)
        cidx = []
        # track HR direction consistency for key signatures (if present)
        key = ["sig_TP53_ARID1A", "sig_TP53_KRAS_ARID1A", "sig_TP53_KRAS_SMAD4", "sig_KRAS_SMAD4", "TP53", "SMAD4", "ARID1A"]
        key = [k for k in key if k in model_df.columns]
        dir_counts = {k: 0 for k in key}
        dir_total = {k: 0 for k in key}

        for i in range(50):
            tr, va = stratified_split(model_df, train_frac=0.7, rng=rng)
            if len(va) < 50 or tr["event"].sum() < 20 or va["event"].sum() < 10:
                continue
            # During splits, drop any newly-constant columns in train and align val.
            tr2 = drop_low_variance_covariates(tr, min_var=1e-6)
            cols = tr2.columns.tolist()
            va2 = va[[c for c in cols if c in va.columns]].copy()
            # Ensure identical column order; fill missing columns with 0
            for c in cols:
                if c not in va2.columns:
                    va2[c] = 0
            va2 = va2[cols]
            try:
                cidx.append(c_index_on_val(tr2, va2, penalizer=0.5))
            except Exception:
                continue

            # refit and record sign of coef for keys
            from lifelines import CoxPHFitter

            cph = CoxPHFitter(penalizer=0.5)
            try:
                cph.fit(tr2, duration_col="OS_MONTHS", event_col="event", show_progress=False)
            except Exception:
                continue
            for k in key:
                if k in cph.params_.index:
                    dir_total[k] += 1
                    if float(cph.params_[k]) > 0:
                        dir_counts[k] += 1

        val_rows.append(
            {
                "Stage": stage,
                "n_patients": len(model_df),
                "events": int(model_df["event"].sum()),
                "covariates": len(covs),
                "cindex_mean": float(np.mean(cidx)) if cidx else np.nan,
                "cindex_std": float(np.std(cidx)) if cidx else np.nan,
                "splits_used": len(cidx),
                **{f"{k}_poscoef_frac": (dir_counts[k] / dir_total[k] if dir_total[k] else np.nan) for k in key},
            }
        )

    validation_df = pd.DataFrame(val_rows)

    # Save Excel
    with pd.ExcelWriter(out_xlsx, engine="openpyxl") as writer:
        validation_df.to_excel(writer, sheet_name="Validation_Summary", index=False)
        for stage, fit_df in stage_results.items():
            sheet = stage.replace("/", "_").replace(" ", "_")[:31]
            fit_df.sort_values("p", ascending=True).to_excel(writer, sheet_name=f"Cox_{sheet}", index=False)

    # Plot validation summary
    apply_manuscript_figure_style()
    fig = plt.figure(figsize=(12, 5))
    ax = plt.subplot(1, 1, 1)
    if len(validation_df):
        tmp = validation_df.set_index("Stage").reindex(STAGES).reset_index()
        bar_colors = [STAGE_COLORS.get(str(s), "#888888") for s in tmp["Stage"]]
        ax.bar(tmp["Stage"], tmp["cindex_mean"], yerr=tmp["cindex_std"], color=bar_colors, alpha=0.75, capsize=6)
        ax.set_ylim(0.45, 0.85)
        ax.set_title("Internal validation (repeated 70/30 splits): C-index by Stage", fontweight="bold")
        ax.set_ylabel("C-index (mean ± std)")
        ax.tick_params(axis="x", rotation=15)
        for i, r in tmp.iterrows():
            if np.isfinite(r["cindex_mean"]):
                ax.text(i, r["cindex_mean"] + 0.01, f"{r['cindex_mean']:.2f}\\n(n={int(r['n_patients'])})", ha="center", va="bottom", fontweight="bold")
        ax.grid(axis="y", alpha=0.25)
    else:
        ax.text(0.5, 0.5, "No validation results", ha="center", va="center", transform=ax.transAxes)
    plt.tight_layout()
    plt.savefig(out_png, dpi=350, bbox_inches="tight")
    plt.close()

    print(f"✅ Saved: {out_xlsx}")
    print(f"✅ Saved: {out_png}")


if __name__ == "__main__":
    main()

