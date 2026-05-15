#!/usr/bin/env python3
"""
DX2COLLECTION_YEAR (diagnosis->collection time) vs OS, stratified by mutation combinations
========================================================================================

Goal
----
Quantify how the association between sample collection timing (DX2COLLECTION_YEAR, years)
and overall survival measured from collection (OS_MONTHS) differs by:
  - pair co-occurrence (A&B)
  - triple co-occurrence (A&B&C)
within each STAGE group.

Model
-----
For each stage and each combination indicator x in {0,1}:
  Cox: OS_MONTHS ~ dx_yr + x + dx_yr:x

Interpretation
--------------
- beta_dx: effect of dx_yr when x=0 (reference).
- beta_int: change in dx_yr effect when x=1 (interaction).
  exp(beta_int) > 1 suggests dx_yr is *more harmful* (higher hazard per year) in combo-positive group.
  exp(beta_int) < 1 suggests dx_yr is *less harmful* (or more protective) in combo-positive group.

Outputs (Tumor/)
---------------
- Stage_DX2Collection_Combo_OS_Interaction.xlsx
- Stage_DX2Collection_Pair_Interaction_Volcano.png
- Stage_DX2Collection_Triple_Interaction_Volcano.png
- Stage_DX2Collection_Interaction_Summary.md
"""

from __future__ import annotations

import os
from itertools import combinations
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

try:
    from statsmodels.stats.multitest import multipletests
except Exception:  # pragma: no cover
    multipletests = None

os.environ.setdefault("MPLBACKEND", "Agg")

STAGES = [
    "Metastatic",
    "Resectable",
    "Borderline Resectable/Locally Advanced",
]

GENES = ["TP53", "KRAS", "CDKN2A", "SMAD4", "ARID1A", "ATM", "PIK3CA", "BRAF", "GNAS", "RNF43"]

STAGE_COLORS = {
    "Metastatic": "#E65100",
    "Resectable": "#2E7D32",
    "Borderline Resectable/Locally Advanced": "#FFEE58",
}


def _to_num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")


def load_patient_level(merged_xlsx: Path) -> pd.DataFrame:
    df = pd.read_excel(merged_xlsx, sheet_name=0)
    needed = {"PATIENT_ID", "Hugo_Symbol", "STAGE", "OS_MONTHS", "OS_STATUS", "DX2COLLECTION_YEAR"}
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
    pat["dx_yr"] = _to_num(pat["DX2COLLECTION_YEAR"])
    pat["event"] = (pat["OS_STATUS"].astype(str) == "1:DECEASED").astype(int)

    # Optional covariates (if present). We keep as-is; encoding happens in model-building.
    if "AGE" in pat.columns:
        pat["AGE"] = _to_num(pat["AGE"])
    if "SEX" in pat.columns:
        pat["SEX"] = pat["SEX"].astype(str)
    if "DISEASE_STATUS" in pat.columns:
        pat["DISEASE_STATUS"] = pat["DISEASE_STATUS"].astype(str)

    # keep same survival filtering as other stage scripts
    pat = pat[pat["OS_MONTHS"].notna() & (pat["OS_MONTHS"] > 0)].copy()
    pat = pat[pat["dx_yr"].notna()].copy()
    return pat


def _safe_mpl():
    import matplotlib  # noqa: WPS433

    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt  # noqa: WPS433

    from manuscript_figure_style import apply_manuscript_figure_style

    apply_manuscript_figure_style()
    return plt


def _encode_covariates(stage_df: pd.DataFrame) -> pd.DataFrame:
    """
    Encode clinical covariates for adjusted Cox:
      - AGE numeric
      - SEX: Male/Female -> 1/0 if possible
      - DISEASE_STATUS: Metastatic vs Primary -> 1/0 if possible
    Drops covariates that are missing or constant within the stage subset.
    """
    out = pd.DataFrame(index=stage_df.index)

    if "AGE" in stage_df.columns:
        age = _to_num(stage_df["AGE"])
        if age.notna().sum() > 0 and float(age.nunique(dropna=True)) > 1:
            out["AGE"] = age

    if "SEX" in stage_df.columns:
        sex = stage_df["SEX"].astype(str).str.lower()
        # map common labels
        sex_bin = sex.map({"male": 1, "m": 1, "female": 0, "f": 0})
        if sex_bin.notna().sum() > 0 and int(sex_bin.nunique(dropna=True)) > 1:
            out["SEX_Male"] = sex_bin.astype(float)

    if "DISEASE_STATUS" in stage_df.columns:
        ds = stage_df["DISEASE_STATUS"].astype(str).str.lower()
        ds_bin = ds.map({"metastatic": 1, "primary": 0})
        if ds_bin.notna().sum() > 0 and int(ds_bin.nunique(dropna=True)) > 1:
            out["DISEASE_STATUS_Metastatic"] = ds_bin.astype(float)

    return out


def fit_interaction_cox(stage_df: pd.DataFrame, x: pd.Series, penalizer: float = 0.1) -> Dict[str, float]:
    from lifelines import CoxPHFitter

    tmp = pd.DataFrame(
        {
            "OS_MONTHS": stage_df["OS_MONTHS"].values,
            "event": stage_df["event"].values,
            "dx_yr": stage_df["dx_yr"].values,
            "x": x.astype(int).values,
        }
    )
    tmp["dx_x"] = tmp["dx_yr"] * tmp["x"]

    cph = CoxPHFitter(penalizer=penalizer)
    cph.fit(tmp, duration_col="OS_MONTHS", event_col="event", show_progress=False)

    def _row(name: str) -> Dict[str, float]:
        beta = float(cph.params_[name])
        p = float(cph.summary.loc[name, "p"])
        ci = cph.confidence_intervals_.loc[name].tolist()  # log-scale
        return {
            f"beta_{name}": beta,
            f"HR_{name}": float(np.exp(beta)),
            f"p_{name}": p,
            f"CIlo_{name}": float(np.exp(ci[0])),
            f"CIhi_{name}": float(np.exp(ci[1])),
        }

    out = {}
    out.update(_row("dx_yr"))
    out.update(_row("x"))
    out.update(_row("dx_x"))
    return out


def fit_interaction_cox_adjusted(stage_df: pd.DataFrame, x: pd.Series, penalizer: float = 0.5) -> Dict[str, float]:
    """
    Adjusted interaction model including AGE/SEX/DISEASE_STATUS (when non-constant within stage subset).
    Uses a stronger penalizer for stability.
    """
    from lifelines import CoxPHFitter

    tmp = pd.DataFrame(
        {
            "OS_MONTHS": stage_df["OS_MONTHS"].values,
            "event": stage_df["event"].values,
            "dx_yr": stage_df["dx_yr"].values,
            "x": x.astype(int).values,
        }
    )
    tmp["dx_x"] = tmp["dx_yr"] * tmp["x"]

    cov = _encode_covariates(stage_df)
    tmp = pd.concat([tmp, cov.reset_index(drop=True)], axis=1)

    # Drop any columns with near-zero variance to avoid singular fits.
    drop_cols = []
    for c in tmp.columns:
        if c in ("OS_MONTHS", "event"):
            continue
        s = tmp[c]
        if s.notna().sum() == 0:
            drop_cols.append(c)
            continue
        if float(s.nunique(dropna=True)) <= 1:
            drop_cols.append(c)
    if drop_cols:
        tmp = tmp.drop(columns=drop_cols)

    # Drop rows with missing covariates used in the adjusted model.
    cov_cols = [c for c in tmp.columns if c not in ("OS_MONTHS", "event")]
    tmp = tmp.dropna(subset=cov_cols)

    cph = CoxPHFitter(penalizer=penalizer)
    cph.fit(tmp, duration_col="OS_MONTHS", event_col="event", show_progress=False)

    def _row(name: str) -> Dict[str, float]:
        beta = float(cph.params_[name])
        p = float(cph.summary.loc[name, "p"])
        ci = cph.confidence_intervals_.loc[name].tolist()  # log-scale
        return {
            f"beta_{name}": beta,
            f"HR_{name}": float(np.exp(beta)),
            f"p_{name}": p,
            f"CIlo_{name}": float(np.exp(ci[0])),
            f"CIhi_{name}": float(np.exp(ci[1])),
        }

    out = {}
    out.update(_row("dx_yr"))
    out.update(_row("x"))
    out.update(_row("dx_x"))
    out["adjusted_covariates"] = ",".join([c for c in tmp.columns if c not in ("OS_MONTHS", "event", "dx_yr", "x", "dx_x")])
    return out


def summarize_feature(
    stage_df: pd.DataFrame,
    x: pd.Series,
) -> Dict[str, float]:
    # Spearman within x=1 (if enough) and within x=0 (optional)
    from scipy import stats

    out: Dict[str, float] = {}
    for label, mask in [("pos", x == 1), ("neg", x == 0)]:
        sub = stage_df.loc[mask, ["dx_yr", "OS_MONTHS"]].dropna()
        out[f"n_{label}"] = int(len(sub))
        out[f"median_dx_{label}"] = float(sub["dx_yr"].median()) if len(sub) else np.nan
        out[f"median_OS_{label}"] = float(sub["OS_MONTHS"].median()) if len(sub) else np.nan
        if len(sub) >= 20:
            rho, p = stats.spearmanr(sub["dx_yr"], sub["OS_MONTHS"])
            out[f"spearman_rho_dx_OS_{label}"] = float(rho)
            out[f"spearman_p_dx_OS_{label}"] = float(p)
        else:
            out[f"spearman_rho_dx_OS_{label}"] = np.nan
            out[f"spearman_p_dx_OS_{label}"] = np.nan
    return out


def run_interactions(pat: pd.DataFrame, kind: str, min_pos: int = 20, min_neg: int = 40) -> pd.DataFrame:
    rows = []
    for st in STAGES:
        sdf = pat[pat["STAGE"] == st].copy()
        if len(sdf) == 0:
            continue

        if kind == "pair":
            feats = [(f"{a}+{b}", (sdf[a] == 1) & (sdf[b] == 1)) for a, b in combinations(GENES, 2)]
        elif kind == "triple":
            feats = [
                (f"{a}+{b}+{c}", (sdf[a] == 1) & (sdf[b] == 1) & (sdf[c] == 1)) for a, b, c in combinations(GENES, 3)
            ]
        else:
            raise ValueError("kind must be pair or triple")

        for label, mask in feats:
            x = mask.astype(int)
            n_pos = int(x.sum())
            n_neg = int((1 - x).sum())
            if n_pos < min_pos or n_neg < min_neg:
                continue

            try:
                stats = fit_interaction_cox(sdf, x, penalizer=0.1)
            except Exception:
                # skip unstable fits
                continue

            # adjusted model (may fail if covariates cause singularity; then keep NaNs)
            try:
                stats_adj = fit_interaction_cox_adjusted(sdf, x, penalizer=0.5)
            except Exception:
                stats_adj = {
                    "beta_dx_yr_adj": np.nan,
                    "HR_dx_yr_adj": np.nan,
                    "p_dx_yr_adj": np.nan,
                    "CIlo_dx_yr_adj": np.nan,
                    "CIhi_dx_yr_adj": np.nan,
                    "beta_x_adj": np.nan,
                    "HR_x_adj": np.nan,
                    "p_x_adj": np.nan,
                    "CIlo_x_adj": np.nan,
                    "CIhi_x_adj": np.nan,
                    "beta_dx_x_adj": np.nan,
                    "HR_dx_x_adj": np.nan,
                    "p_dx_x_adj": np.nan,
                    "CIlo_dx_x_adj": np.nan,
                    "CIhi_dx_x_adj": np.nan,
                    "adjusted_covariates": "",
                }

            # rename adjusted keys to *_adj (avoid collision)
            stats_adj_ren = {}
            for k, v in stats_adj.items():
                if k == "adjusted_covariates":
                    stats_adj_ren[k] = v
                elif k.startswith(("beta_", "HR_", "p_", "CIlo_", "CIhi_")):
                    stats_adj_ren[k + "_adj"] = v
                else:
                    stats_adj_ren[k + "_adj"] = v
            summ = summarize_feature(sdf, x)
            rows.append(
                {
                    "Stage": st,
                    "kind": kind,
                    "Feature": label,
                    "n_pos": n_pos,
                    "n_neg": n_neg,
                    **stats,
                    **stats_adj_ren,
                    **summ,
                }
            )
    df = pd.DataFrame(rows)
    if len(df) == 0:
        return df

    # multiple testing correction on interaction p-value within each stage+kind
    df["p_int"] = df["p_dx_x"]
    df["p_int_adj"] = df["p_dx_x_adj"]
    df["p_int_fdr_bh"] = np.nan
    df["p_int_bonf"] = np.nan
    df["p_int_adj_fdr_bh"] = np.nan
    df["p_int_adj_bonf"] = np.nan
    for st in STAGES:
        for k in ["pair", "triple"]:
            idx = df.index[(df["Stage"] == st) & (df["kind"] == k) & df["p_int"].notna()]
            if len(idx) == 0:
                continue
            p = df.loc[idx, "p_int"].values
            if multipletests is not None:
                df.loc[idx, "p_int_fdr_bh"] = multipletests(p, method="fdr_bh")[1]
                df.loc[idx, "p_int_bonf"] = multipletests(p, method="bonferroni")[1]
            else:
                m = len(p)
                df.loc[idx, "p_int_bonf"] = np.minimum(p * m, 1.0)

            idx2 = df.index[(df["Stage"] == st) & (df["kind"] == k) & df["p_int_adj"].notna()]
            if len(idx2) == 0:
                continue
            p2 = df.loc[idx2, "p_int_adj"].values
            if multipletests is not None:
                df.loc[idx2, "p_int_adj_fdr_bh"] = multipletests(p2, method="fdr_bh")[1]
                df.loc[idx2, "p_int_adj_bonf"] = multipletests(p2, method="bonferroni")[1]
            else:
                m2 = len(p2)
                df.loc[idx2, "p_int_adj_bonf"] = np.minimum(p2 * m2, 1.0)
    return df


def plot_volcano(df: pd.DataFrame, out_png: Path, kind: str) -> None:
    plt = _safe_mpl()
    d = df[df["kind"] == kind].copy()
    if len(d) == 0:
        fig = plt.figure(figsize=(10, 4))
        plt.text(0.5, 0.5, f"No {kind} interaction results", ha="center", va="center")
        plt.axis("off")
        plt.savefig(out_png, dpi=350, bbox_inches="tight")
        plt.close(fig)
        return

    fig, axes = plt.subplots(1, 3, figsize=(18, 5), sharey=True)
    for ax, st in zip(axes, STAGES):
        sdf = d[d["Stage"] == st].copy()
        if len(sdf) == 0:
            ax.set_axis_off()
            continue
        # adjusted interaction by default (fallback to unadjusted if missing)
        bx = sdf["beta_dx_x_adj"].where(sdf["beta_dx_x_adj"].notna(), sdf["beta_dx_x"]).values
        pv = sdf["p_int_adj"].where(sdf["p_int_adj"].notna(), sdf["p_int"]).values
        x = bx
        y = -np.log10(np.clip(pv, 1e-300, 1.0))
        ax.scatter(x, y, s=20, alpha=0.75, color=STAGE_COLORS.get(st, "#777777"))
        ax.axvline(0, color="#444444", lw=1)
        ax.set_title(st, fontweight="bold")
        ax.set_xlabel("Interaction beta (dx_yr × combo)")
        ax.grid(alpha=0.2)
    axes[0].set_ylabel("-log10(p) for interaction (adjusted if available)")
    fig.suptitle(f"{kind.title()} interactions: does dx_yr↔OS differ by combo (adjusted)?", fontweight="bold", y=1.02)
    plt.tight_layout()
    plt.savefig(out_png, dpi=350, bbox_inches="tight")
    plt.close(fig)


def write_md(out_md: Path, df: pd.DataFrame) -> None:
    lines: List[str] = []
    lines.append("# DX2COLLECTION_YEAR × combo interaction with OS (stage-stratified)\n\n")
    lines.append("- Unadjusted model: Cox(OS_MONTHS ~ dx_yr + combo + dx_yr×combo)\n")
    lines.append("- Adjusted model:   Cox(OS_MONTHS ~ dx_yr + combo + dx_yr×combo + AGE + SEX + DISEASE_STATUS) (when available)\n")
    lines.append("- dx_yr: years from diagnosis to sample collection\n")
    lines.append("- OS_MONTHS: months from collection to death/last follow-up (per clinical dictionary)\n\n")

    if len(df) == 0:
        out_md.write_text("".join(lines) + "\nNo results.\n", encoding="utf-8")
        return

    for kind in ["pair", "triple"]:
        lines.append(f"## Top {kind} interactions by stage (lowest adjusted p_int)\n")
        d = df[df["kind"] == kind].copy()
        for st in STAGES:
            sdf = d[d["Stage"] == st].sort_values("p_int_adj").head(8)
            if len(sdf) == 0:
                continue
            lines.append(f"\n### {st}\n")
            for _, r in sdf.iterrows():
                p_adj = r.get("p_int_adj", np.nan)
                fdr_adj = r.get("p_int_adj_fdr_bh", np.nan)
                hr_adj = r.get("HR_dx_x_adj", np.nan)
                beta_adj = r.get("beta_dx_x_adj", np.nan)
                lines.append(
                    f"- **{r['Feature']}**: beta_int_adj={beta_adj:.3f} (HR_int_adj={hr_adj:.2f}), "
                    f"p_int_adj={p_adj:.3g}, FDR_adj={fdr_adj:.3g} | "
                    f"beta_int_unadj={r['beta_dx_x']:.3f} (HR_int_unadj={r['HR_dx_x']:.2f}), p_int_unadj={r['p_int']:.3g} | "
                    f"median dx (pos/neg)={r['median_dx_pos']:.3g}/{r['median_dx_neg']:.3g}, "
                    f"median OS (pos/neg)={r['median_OS_pos']:.2f}/{r['median_OS_neg']:.2f}\n"
                )
        lines.append("\n")

    out_md.write_text("".join(lines), encoding="utf-8")


def main() -> None:
    tumor_dir = Path(__file__).resolve().parent
    merged_xlsx = tumor_dir / "Merged.xlsx"

    out_xlsx = tumor_dir / "Stage_DX2Collection_Combo_OS_Interaction_Sensitivity.xlsx"
    out_md = tumor_dir / "Stage_DX2Collection_Interaction_Sensitivity_Summary.md"

    filters = [
        ("ALL", lambda d: d),
        ("DX_GE_0", lambda d: d[d["dx_yr"] >= 0].copy()),
        ("DX_0_TO_5", lambda d: d[(d["dx_yr"] >= 0) & (d["dx_yr"] <= 5)].copy()),
    ]

    pat0 = load_patient_level(merged_xlsx)

    all_runs: Dict[str, pd.DataFrame] = {}
    with pd.ExcelWriter(out_xlsx, engine="openpyxl") as xw:
        # stage counts per filter
        counts_rows = []
        for tag, fn in filters:
            pat = fn(pat0)
            counts_rows.append({"Filter": tag, **{s: int((pat["STAGE"] == s).sum()) for s in STAGES}, "Total": int(len(pat))})
        pd.DataFrame(counts_rows).to_excel(xw, sheet_name="Stage_Counts_ByFilter", index=False)

        for tag, fn in filters:
            pat = fn(pat0)
            pair_df = run_interactions(pat, kind="pair", min_pos=20, min_neg=40)
            triple_df = run_interactions(pat, kind="triple", min_pos=20, min_neg=40)
            df = pd.concat([pair_df, triple_df], ignore_index=True) if len(pair_df) or len(triple_df) else pd.DataFrame()
            all_runs[tag] = df

            sheet = f"All_{tag}"
            if len(sheet) > 31:
                sheet = sheet[:31]
            df.to_excel(xw, sheet_name=sheet, index=False)
            if len(df):
                df[df["kind"] == "pair"].sort_values(["Stage", "p_int_adj"]).head(200).to_excel(xw, sheet_name=f"Pairs_{tag}"[:31], index=False)
                df[df["kind"] == "triple"].sort_values(["Stage", "p_int_adj"]).head(200).to_excel(xw, sheet_name=f"Triples_{tag}"[:31], index=False)

    # Plots for each filter (adjusted volc)
    for tag in all_runs:
        df = all_runs[tag]
        if len(df) == 0:
            continue
        plot_volcano(df, tumor_dir / f"Stage_DX2Collection_Pair_Interaction_Volcano_{tag}.png", kind="pair")
        plot_volcano(df, tumor_dir / f"Stage_DX2Collection_Triple_Interaction_Volcano_{tag}.png", kind="triple")

    # Markdown summary comparing top interaction across filters
    lines: List[str] = []
    lines.append("# DX2COLLECTION_YEAR × combo interaction — sensitivity analysis\n\n")
    lines.append("Filters:\n- ALL: no dx filter\n- DX_GE_0: exclude dx<0\n- DX_0_TO_5: exclude dx<0 and dx>5 years\n\n")
    lines.append("Model (adjusted primary): Cox(OS_MONTHS ~ dx_yr + combo + dx_yr×combo + AGE + SEX + DISEASE_STATUS)\n\n")

    for tag, _ in filters:
        df = all_runs.get(tag, pd.DataFrame())
        lines.append(f"## {tag}\n")
        if len(df) == 0:
            lines.append("- No results.\n\n")
            continue
        for kind in ["pair", "triple"]:
            lines.append(f"### Top {kind} interactions (by adjusted p_int)\n")
            d = df[df["kind"] == kind].copy()
            for st in STAGES:
                sdf = d[d["Stage"] == st].sort_values("p_int_adj").head(5)
                if len(sdf) == 0:
                    continue
                lines.append(f"\n**{st}**\n")
                for _, r in sdf.iterrows():
                    lines.append(
                        f"- {r['Feature']}: HR_int_adj={r['HR_dx_x_adj']:.2f}, p_int_adj={r['p_int_adj']:.3g}, "
                        f"FDR_adj={r['p_int_adj_fdr_bh']:.3g} (unadj p={r['p_int']:.3g})\n"
                    )
            lines.append("\n")
        lines.append("\n")

    out_md.write_text("".join(lines), encoding="utf-8")

    print(f"✅ Saved: {out_xlsx}")
    print(f"✅ Saved: {out_md}")


if __name__ == "__main__":
    main()

