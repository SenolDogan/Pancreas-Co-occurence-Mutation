#!/usr/bin/env python3
"""
Stage mutation differences + additive co-occurrence + OS impact report
=====================================================================

What this produces (Tumor/):
  - Stage_Mutation_Additive_OS_Report.xlsx
  - Stage_Mutation_Additive_OS_Scatter.png
  - Stage_Mutation_Additive_OS_Summary.md

Purpose
-------
Unify, per STAGE group (Metastatic / Resectable / Borderline Resectable/Locally Advanced):
  - single-gene mutation frequency differences across stages
  - pairwise co-occurrence (+additive / -additive) lists
  - OS impact (univariate Cox) for single genes and for co-occurrence indicators

Notes
-----
DX2COLLECTION_YEAR defines diagnosis->collection interval (years) and OS_MONTHS is defined from
collection to death/last follow-up in the clinical dictionary; this report keeps OS definitions consistent
with existing Tumor stage scripts (OS_MONTHS > 0; event from OS_STATUS).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from manuscript_figure_style import short_stage_label

try:
    from statsmodels.stats.multitest import multipletests
except Exception:  # pragma: no cover
    multipletests = None


STAGES = [
    "Metastatic",
    "Resectable",
    "Borderline Resectable/Locally Advanced",
]

GENES = ["TP53", "KRAS", "CDKN2A", "SMAD4", "ARID1A", "ATM", "PIK3CA", "BRAF", "GNAS", "RNF43"]

# Force non-GUI backend to avoid macOSX aborts in headless/sandbox runs.
os.environ.setdefault("MPLBACKEND", "Agg")

# stage colors (koyu turuncu / yesil / acik sari)
STAGE_COLORS = {
    "Metastatic": "#E65100",
    "Resectable": "#2E7D32",
    "Borderline Resectable/Locally Advanced": "#FFEE58",
}


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

    # keep survival definition consistent with existing stage scripts
    pat = pat[pat["OS_MONTHS"].notna() & (pat["OS_MONTHS"] > 0)].copy()
    return pat


def chi2_2xk(counts_yes: List[int], counts_no: List[int]) -> float:
    """
    Pearson chi-square for 2xK table without scipy dependency.
    Returns p-value using dof = K-1 approximation (for K=3 dof=2 exact closed-form).
    """
    table = np.array([counts_yes, counts_no], dtype=float)
    table = table[:, ~np.isnan(table).any(axis=0)]
    if table.size == 0:
        return np.nan
    row_sum = table.sum(axis=1, keepdims=True)
    col_sum = table.sum(axis=0, keepdims=True)
    grand = table.sum()
    if grand <= 0:
        return np.nan
    expected = row_sum @ col_sum / grand
    with np.errstate(divide="ignore", invalid="ignore"):
        chi2 = np.nansum((table - expected) ** 2 / expected)
    dof = (table.shape[0] - 1) * (table.shape[1] - 1)
    if dof == 2:
        # chi-square survival function for dof=2: exp(-x/2)*(1+x/2)
        return float(np.exp(-chi2 / 2.0) * (1.0 + chi2 / 2.0))
    # fallback monotone approx
    return float(np.exp(-chi2 / 2.0))


def cox_univariate(stage_df: pd.DataFrame, x: pd.Series, penalizer: float = 0.0) -> Dict[str, float]:
    from lifelines import CoxPHFitter

    tmp = pd.DataFrame({"OS_MONTHS": stage_df["OS_MONTHS"].values, "event": stage_df["event"].values, "x": x.astype(int).values})
    cph = CoxPHFitter(penalizer=penalizer)
    cph.fit(tmp, duration_col="OS_MONTHS", event_col="event", show_progress=False)

    beta = float(cph.params_["x"])
    hr = float(np.exp(beta))
    p = float(cph.summary.loc["x", "p"])
    ci = cph.confidence_intervals_.loc["x"].tolist()  # log-scale
    ci_lo = float(np.exp(ci[0]))
    ci_hi = float(np.exp(ci[1]))
    return {"HR": hr, "p": p, "CI_lo": ci_lo, "CI_hi": ci_hi}


def build_single_gene_tables(pat: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Returns:
      - freq_long: Stage x Gene frequency (%) + counts
      - diff_tests: chi2 p-values for stage difference per gene + FDR/Bonferroni (if available)
    """
    rows = []
    for st in STAGES:
        sdf = pat[pat["STAGE"] == st]
        n = len(sdf)
        for g in GENES:
            k = int(sdf[g].sum())
            rows.append({"Stage": st, "Gene": g, "n_stage": n, "n_mut": k, "freq_pct": (100.0 * k / n) if n else np.nan})
    freq_long = pd.DataFrame(rows)

    test_rows = []
    for g in GENES:
        yes = []
        no = []
        for st in STAGES:
            sdf = pat[pat["STAGE"] == st]
            n = len(sdf)
            k = int(sdf[g].sum())
            yes.append(k)
            no.append(n - k)
        p = chi2_2xk(yes, no)
        test_rows.append({"Gene": g, "p_chi2_2x3": p, "Metastatic_n": yes[0], "Resectable_n": yes[1], "Borderline_n": yes[2]})
    diff_tests = pd.DataFrame(test_rows).sort_values("p_chi2_2x3", ascending=True).reset_index(drop=True)

    if multipletests is not None and diff_tests["p_chi2_2x3"].notna().any():
        pvals = diff_tests["p_chi2_2x3"].fillna(1.0).values
        diff_tests["p_fdr_bh"] = multipletests(pvals, method="fdr_bh")[1]
        diff_tests["p_bonf"] = multipletests(pvals, method="bonferroni")[1]
    else:
        m = len(diff_tests)
        diff_tests["p_fdr_bh"] = np.nan
        diff_tests["p_bonf"] = np.minimum(diff_tests["p_chi2_2x3"] * m, 1.0)
    return freq_long, diff_tests


def build_pair_additive_tables(pat: pd.DataFrame, min_n_pos: int = 15) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    For each stage and each gene pair:
      additive = P(A&B) - P(A)P(B)   (above/below independence; can be +/-)
      multiplicative = P(A&B) / (P(A)P(B)) if denom>0
    Returns:
      - pairs_long: per-stage pair metrics
      - top_posneg: top +additive and -additive pairs per stage (filtered by min_n_pos)
    """
    rows = []
    for st in STAGES:
        sdf = pat[pat["STAGE"] == st].copy()
        n = len(sdf)
        if n == 0:
            continue
        for a, b in combinations(GENES, 2):
            pa = float(sdf[a].mean())
            pb = float(sdf[b].mean())
            both = float(((sdf[a] == 1) & (sdf[b] == 1)).mean())
            n_pos = int(((sdf[a] == 1) & (sdf[b] == 1)).sum())
            additive = both - (pa * pb)
            additive_legacy = both - (pa + pb)  # legacy form (almost always negative)
            mult = both / (pa * pb) if (pa * pb) > 0 else np.nan
            rows.append(
                {
                    "Stage": st,
                    "Pair": f"{a}+{b}",
                    "GeneA": a,
                    "GeneB": b,
                    "n_stage": n,
                    "n_AB": n_pos,
                    "pA": pa,
                    "pB": pb,
                    "pAB": both,
                    "Additive": additive,
                    "Additive_Legacy_pAB_minus_pA_minus_pB": additive_legacy,
                    "Multiplicative": mult,
                }
            )
    pairs_long = pd.DataFrame(rows)
    if len(pairs_long) == 0:
        return pairs_long, pairs_long

    filt = pairs_long[pairs_long["n_AB"] >= min_n_pos].copy()
    out_rows = []
    for st in STAGES:
        sdf = filt[filt["Stage"] == st].copy()
        if len(sdf) == 0:
            continue
        pos = sdf.sort_values("Additive", ascending=False).head(15)
        neg = sdf.sort_values("Additive", ascending=True).head(15)
        pos["Additive_Sign"] = "+additive"
        neg["Additive_Sign"] = "-additive"
        out_rows.append(pos)
        out_rows.append(neg)
    top_posneg = pd.concat(out_rows, ignore_index=True) if out_rows else filt.head(0)
    return pairs_long, top_posneg


def build_os_effect_tables(pat: pd.DataFrame, min_n_pos: int = 20, min_n_neg: int = 40) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Returns:
      - single_os: per-stage HR for each single gene
      - pair_os: per-stage HR for each pair indicator A&B
    """
    single_rows = []
    pair_rows = []
    for st in STAGES:
        sdf = pat[pat["STAGE"] == st].copy()
        if len(sdf) == 0:
            continue
        # single genes
        for g in GENES:
            x = (sdf[g] == 1).astype(int)
            n_pos = int(x.sum())
            n_neg = int((1 - x).sum())
            if n_pos < min_n_pos or n_neg < min_n_neg:
                continue
            stats = cox_univariate(sdf, x, penalizer=0.0)
            med_pos = float(sdf.loc[x == 1, "OS_MONTHS"].median())
            med_neg = float(sdf.loc[x == 0, "OS_MONTHS"].median())
            single_rows.append(
                {
                    "Stage": st,
                    "Feature": g,
                    "kind": "single",
                    "n_pos": n_pos,
                    "n_neg": n_neg,
                    "median_OS_pos": med_pos,
                    "median_OS_neg": med_neg,
                    **stats,
                }
            )
        # pairs
        for a, b in combinations(GENES, 2):
            x = ((sdf[a] == 1) & (sdf[b] == 1)).astype(int)
            n_pos = int(x.sum())
            n_neg = int((1 - x).sum())
            if n_pos < min_n_pos or n_neg < min_n_neg:
                continue
            stats = cox_univariate(sdf, x, penalizer=0.0)
            med_pos = float(sdf.loc[x == 1, "OS_MONTHS"].median())
            med_neg = float(sdf.loc[x == 0, "OS_MONTHS"].median())
            pair_rows.append(
                {
                    "Stage": st,
                    "Feature": f"{a}+{b}",
                    "kind": "pair",
                    "n_pos": n_pos,
                    "n_neg": n_neg,
                    "median_OS_pos": med_pos,
                    "median_OS_neg": med_neg,
                    **stats,
                }
            )
    single_os = pd.DataFrame(single_rows)
    pair_os = pd.DataFrame(pair_rows)
    return single_os, pair_os


def build_triple_additive_tables(pat: pd.DataFrame, min_n_pos: int = 10) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    For each stage and each gene triple:
      additive = P(A&B&C) - P(A)P(B)P(C)   (above/below independence; can be +/-)
      multiplicative = P(ABC) / (P(A)P(B)P(C)) if denom>0
    Returns:
      - triples_long: per-stage triple metrics
      - top_posneg: top +additive and -additive triples per stage (filtered by min_n_ABC)
    """
    rows = []
    for st in STAGES:
        sdf = pat[pat["STAGE"] == st].copy()
        n = len(sdf)
        if n == 0:
            continue
        # precompute gene rates
        rates = {g: float(sdf[g].mean()) for g in GENES}
        for a, b, c in combinations(GENES, 3):
            pa, pb, pc = rates[a], rates[b], rates[c]
            both3 = float(((sdf[a] == 1) & (sdf[b] == 1) & (sdf[c] == 1)).mean())
            n_pos = int(((sdf[a] == 1) & (sdf[b] == 1) & (sdf[c] == 1)).sum())
            denom = pa * pb * pc
            additive = both3 - denom
            mult = both3 / denom if denom > 0 else np.nan
            rows.append(
                {
                    "Stage": st,
                    "Triple": f"{a}+{b}+{c}",
                    "GeneA": a,
                    "GeneB": b,
                    "GeneC": c,
                    "n_stage": n,
                    "n_ABC": n_pos,
                    "pA": pa,
                    "pB": pb,
                    "pC": pc,
                    "pABC": both3,
                    "Additive": additive,
                    "Multiplicative": mult,
                }
            )
    triples_long = pd.DataFrame(rows)
    if len(triples_long) == 0:
        return triples_long, triples_long

    filt = triples_long[triples_long["n_ABC"] >= min_n_pos].copy()
    out_rows = []
    for st in STAGES:
        sdf = filt[filt["Stage"] == st].copy()
        if len(sdf) == 0:
            continue
        pos = sdf.sort_values("Additive", ascending=False).head(15)
        neg = sdf.sort_values("Additive", ascending=True).head(15)
        pos["Additive_Sign"] = "+additive"
        neg["Additive_Sign"] = "-additive"
        out_rows.append(pos)
        out_rows.append(neg)
    top_posneg = pd.concat(out_rows, ignore_index=True) if out_rows else filt.head(0)
    return triples_long, top_posneg


def build_triple_os_effect_table(pat: pd.DataFrame, min_n_pos: int = 20, min_n_neg: int = 40) -> pd.DataFrame:
    """
    Univariate Cox per stage for triple indicator A&B&C.
    """
    rows = []
    for st in STAGES:
        sdf = pat[pat["STAGE"] == st].copy()
        if len(sdf) == 0:
            continue
        for a, b, c in combinations(GENES, 3):
            x = ((sdf[a] == 1) & (sdf[b] == 1) & (sdf[c] == 1)).astype(int)
            n_pos = int(x.sum())
            n_neg = int((1 - x).sum())
            if n_pos < min_n_pos or n_neg < min_n_neg:
                continue
            stats = cox_univariate(sdf, x, penalizer=0.0)
            med_pos = float(sdf.loc[x == 1, "OS_MONTHS"].median())
            med_neg = float(sdf.loc[x == 0, "OS_MONTHS"].median())
            rows.append(
                {
                    "Stage": st,
                    "Feature": f"{a}+{b}+{c}",
                    "kind": "triple",
                    "n_pos": n_pos,
                    "n_neg": n_neg,
                    "median_OS_pos": med_pos,
                    "median_OS_neg": med_neg,
                    **stats,
                }
            )
    return pd.DataFrame(rows)


def merge_triple_additive_with_os(triples_long: pd.DataFrame, triple_os: pd.DataFrame) -> pd.DataFrame:
    if len(triple_os) == 0 or len(triples_long) == 0:
        return triple_os
    base = triple_os.merge(
        triples_long[["Stage", "Triple", "n_ABC", "Additive", "Multiplicative"]],
        left_on=["Stage", "Feature"],
        right_on=["Stage", "Triple"],
        how="left",
    )
    base = base.drop(columns=["Triple"], errors="ignore")
    return base


def merge_pair_additive_with_os(pairs_long: pd.DataFrame, pair_os: pd.DataFrame) -> pd.DataFrame:
    if len(pair_os) == 0 or len(pairs_long) == 0:
        return pair_os
    base = pair_os.merge(
        pairs_long[
            [
                "Stage",
                "Pair",
                "n_AB",
                "Additive",
                "Additive_Legacy_pAB_minus_pA_minus_pB",
                "Multiplicative",
            ]
        ],
        left_on=["Stage", "Feature"],
        right_on=["Stage", "Pair"],
        how="left",
    )
    base = base.drop(columns=["Pair"], errors="ignore")
    return base


def plot_additive_vs_hr(pair_os_add: pd.DataFrame, out_png: Path) -> None:
    """
    Optional visualization. On some machines fontconfig/matplotlib cache is not writable and can abort the process.
    We therefore import matplotlib lazily and skip plotting if it fails.
    """
    try:
        import matplotlib  # noqa: WPS433
        matplotlib.use("Agg", force=True)
        import matplotlib.pyplot as plt  # noqa: WPS433
        from manuscript_figure_style import apply_manuscript_figure_style, short_stage_label

        apply_manuscript_figure_style()
    except Exception:
        # Skip plotting if matplotlib can't initialize.
        return

    if len(pair_os_add) == 0 or "Additive" not in pair_os_add.columns:
        fig = plt.figure(figsize=(10, 6))
        plt.text(0.5, 0.5, "No pair OS/additive data available", ha="center", va="center")
        plt.axis("off")
        plt.savefig(out_png, dpi=350, bbox_inches="tight")
        plt.close(fig)
        return

    df = pair_os_add.copy()
    df = df[df["Additive"].notna() & df["HR"].notna()].copy()
    if len(df) == 0:
        fig = plt.figure(figsize=(10, 6))
        plt.text(0.5, 0.5, "No pair OS/additive data available", ha="center", va="center")
        plt.axis("off")
        plt.savefig(out_png, dpi=350, bbox_inches="tight")
        plt.close(fig)
        return

    fig, axes = plt.subplots(1, 3, figsize=(18, 5), sharey=True)
    for ax, st in zip(axes, STAGES):
        sdf = df[df["Stage"] == st].copy()
        if len(sdf) == 0:
            ax.text(0.5, 0.5, f"No data\n{short_stage_label(st)}", ha="center", va="center", transform=ax.transAxes)
            ax.set_axis_off()
            continue
        x = sdf["Additive"].values
        y = np.log(sdf["HR"].clip(1e-6, None).values)
        ax.scatter(x, y, s=25, alpha=0.7, color=STAGE_COLORS.get(st, "#777777"))
        ax.axhline(0, color="#444444", lw=1, alpha=0.6)
        ax.axvline(0, color="#444444", lw=1, alpha=0.6)
        ax.set_title(short_stage_label(st), fontweight="bold")
        ax.set_xlabel("Additive vs independence (P(A&B) - P(A)P(B))")
        ax.grid(alpha=0.2)
    axes[0].set_ylabel("log(HR) from univariate Cox (pair indicator)")
    fig.suptitle("Pairwise +/−additive vs OS hazard by Stage", fontweight="bold", y=1.02)
    plt.tight_layout()
    plt.savefig(out_png, dpi=350, bbox_inches="tight")
    plt.close(fig)


def _safe_mpl():
    import matplotlib  # noqa: WPS433
    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt  # noqa: WPS433
    from manuscript_figure_style import apply_manuscript_figure_style

    apply_manuscript_figure_style()
    return plt


def plot_gene_freq_heatmap(freq_long: pd.DataFrame, out_png: Path) -> None:
    plt = _safe_mpl()
    if len(freq_long) == 0:
        fig = plt.figure(figsize=(10, 4))
        plt.text(0.5, 0.5, "No gene frequency data", ha="center", va="center")
        plt.axis("off")
        plt.savefig(out_png, dpi=350, bbox_inches="tight")
        plt.close(fig)
        return
    piv = freq_long.pivot(index="Gene", columns="Stage", values="freq_pct").reindex(index=GENES, columns=STAGES)
    fig = plt.figure(figsize=(8.5, 4.8))
    ax = plt.gca()
    im = ax.imshow(piv.values, aspect="auto", cmap="YlOrRd")
    ax.set_xticks(np.arange(len(STAGES)))
    ax.set_xticklabels([short_stage_label(s) for s in STAGES], rotation=15, ha="right")
    ax.set_yticks(np.arange(len(GENES)))
    ax.set_yticklabels(GENES)
    for i in range(piv.shape[0]):
        for j in range(piv.shape[1]):
            v = piv.values[i, j]
            if np.isfinite(v):
                ax.text(j, i, f"{v:.1f}", ha="center", va="center", fontsize=11, color="#1b1b1b")
    ax.set_title("Mutation frequency (%) by Stage", fontweight="bold")
    cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("% mutated")
    plt.tight_layout()
    plt.savefig(out_png, dpi=350, bbox_inches="tight")
    plt.close(fig)


def plot_top_additive_bars(
    top_posneg: pd.DataFrame,
    out_png: Path,
    label_col: str,
    additive_col: str = "Additive",
    ncol: str = "n_AB",
    title: str = "Top +additive / −additive (vs independence)",
) -> None:
    plt = _safe_mpl()
    if len(top_posneg) == 0:
        fig = plt.figure(figsize=(10, 4))
        plt.text(0.5, 0.5, "No additive ranking data", ha="center", va="center")
        plt.axis("off")
        plt.savefig(out_png, dpi=350, bbox_inches="tight")
        plt.close(fig)
        return

    fig, axes = plt.subplots(3, 2, figsize=(14, 12), gridspec_kw={"width_ratios": [1, 1]})
    for i, st in enumerate(STAGES):
        sdf = top_posneg[top_posneg["Stage"] == st].copy()
        axL = axes[i, 0]
        axR = axes[i, 1]
        if len(sdf) == 0:
            axL.set_axis_off()
            axR.set_axis_off()
            continue
        pos = sdf[sdf["Additive_Sign"] == "+additive"].head(10).copy()
        neg = sdf[sdf["Additive_Sign"] == "-additive"].head(10).copy()

        axL.barh(pos[label_col], pos[additive_col], color=STAGE_COLORS.get(st, "#777777"), alpha=0.8)
        axL.axvline(0, color="#444444", lw=1)
        axL.set_title(f"{short_stage_label(st)} — top +additive", fontweight="bold")
        axL.invert_yaxis()
        axL.grid(axis="x", alpha=0.25)
        for y, (lbl, addv, n) in enumerate(zip(pos[label_col], pos[additive_col], pos[ncol])):
            axL.text(addv, y, f" n={int(n)}", va="center", ha="left", fontsize=9)

        axR.barh(neg[label_col], neg[additive_col], color="#455A64", alpha=0.85)
        axR.axvline(0, color="#444444", lw=1)
        axR.set_title(f"{short_stage_label(st)} — top −additive", fontweight="bold")
        axR.invert_yaxis()
        axR.grid(axis="x", alpha=0.25)
        for y, (lbl, addv, n) in enumerate(zip(neg[label_col], neg[additive_col], neg[ncol])):
            axR.text(addv, y, f" n={int(n)}", va="center", ha="left", fontsize=9)

    fig.suptitle(title, fontweight="bold", y=1.01)
    plt.tight_layout()
    plt.savefig(out_png, dpi=350, bbox_inches="tight")
    plt.close(fig)


def plot_top_cox_forest(
    df: pd.DataFrame,
    out_png: Path,
    title: str,
    per_stage_top: int = 10,
) -> None:
    plt = _safe_mpl()
    if len(df) == 0:
        fig = plt.figure(figsize=(10, 4))
        plt.text(0.5, 0.5, "No Cox results", ha="center", va="center")
        plt.axis("off")
        plt.savefig(out_png, dpi=350, bbox_inches="tight")
        plt.close(fig)
        return

    # take top per stage by p-value
    take = []
    for st in STAGES:
        sdf = df[df["Stage"] == st].sort_values("p").head(per_stage_top)
        take.append(sdf)
    d = pd.concat(take, ignore_index=True)
    if len(d) == 0:
        fig = plt.figure(figsize=(10, 4))
        plt.text(0.5, 0.5, "No Cox results after filtering", ha="center", va="center")
        plt.axis("off")
        plt.savefig(out_png, dpi=350, bbox_inches="tight")
        plt.close(fig)
        return

    # create y positions grouped by stage
    rows = []
    y = 0
    for st in STAGES:
        sdf = d[d["Stage"] == st].sort_values("p").copy()
        for _, r in sdf.iterrows():
            rows.append({**r.to_dict(), "y": y, "Stage": st})
            y += 1
        y += 1  # blank gap
    plot_df = pd.DataFrame(rows)

    fig = plt.figure(figsize=(12, max(6, 0.35 * len(plot_df))))
    ax = plt.gca()
    for st in STAGES:
        sdf = plot_df[plot_df["Stage"] == st]
        if len(sdf) == 0:
            continue
        ax.errorbar(
            sdf["HR"].values,
            sdf["y"].values,
            xerr=[sdf["HR"].values - sdf["CI_lo"].values, sdf["CI_hi"].values - sdf["HR"].values],
            fmt="o",
            color=STAGE_COLORS.get(st, "#777777"),
            ecolor=STAGE_COLORS.get(st, "#777777"),
            capsize=3,
            alpha=0.9,
            label=short_stage_label(st),
        )
    ax.axvline(1.0, color="#333333", lw=1)
    ax.set_yticks(plot_df["y"].values)
    ax.set_yticklabels(
        [f"{short_stage_label(r['Stage'])}: {r['Feature']} (n={int(r['n_pos'])})" for _, r in plot_df.iterrows()],
        fontsize=9,
    )
    ax.set_xlabel("Hazard ratio (univariate Cox)")
    ax.set_title(title, fontweight="bold")
    ax.grid(axis="x", alpha=0.25)
    ax.legend(loc="lower right", fontsize=9)
    plt.tight_layout()
    plt.savefig(out_png, dpi=350, bbox_inches="tight")
    plt.close(fig)


def write_markdown_summary(
    out_md: Path,
    freq_tests: pd.DataFrame,
    top_posneg: pd.DataFrame,
    top_posneg_triples: pd.DataFrame,
    single_os: pd.DataFrame,
    pair_os_add: pd.DataFrame,
    triple_os_add: pd.DataFrame,
) -> None:
    lines: List[str] = []
    lines.append("# Stage mutation / additive / OS summary\n")
    lines.append("This report summarizes stage differences, +additive/−additive co-occurrence, and OS associations.\n")

    lines.append("## Stage-differential single genes (chi-square 2×3)\n")
    top = freq_tests.head(10).copy()
    for _, r in top.iterrows():
        lines.append(f"- **{r['Gene']}**: p={r['p_chi2_2x3']:.3g} (FDR={r.get('p_fdr_bh', np.nan):.3g}, Bonf={r.get('p_bonf', np.nan):.3g})\n")

    lines.append("\n## Top +additive / −additive pairs (per stage; filtered by n_AB)\n")
    if len(top_posneg) == 0:
        lines.append("- No pairs passed filters.\n")
    else:
        for st in STAGES:
            sdf = top_posneg[top_posneg["Stage"] == st].copy()
            if len(sdf) == 0:
                continue
            lines.append(f"\n### {st}\n")
            pos = sdf[sdf["Additive_Sign"] == "+additive"].head(5)
            neg = sdf[sdf["Additive_Sign"] == "-additive"].head(5)
            lines.append("**Top +additive**\n")
            for _, r in pos.iterrows():
                lines.append(f"- {r['Pair']}: Additive={r['Additive']:.4f}, n_AB={int(r['n_AB'])}\n")
            lines.append("\n**Top −additive**\n")
            for _, r in neg.iterrows():
                lines.append(f"- {r['Pair']}: Additive={r['Additive']:.4f}, n_AB={int(r['n_AB'])}\n")

    lines.append("\n## Top +additive / −additive triples (per stage; filtered by n_ABC)\n")
    if len(top_posneg_triples) == 0:
        lines.append("- No triples passed filters.\n")
    else:
        for st in STAGES:
            sdf = top_posneg_triples[top_posneg_triples["Stage"] == st].copy()
            if len(sdf) == 0:
                continue
            lines.append(f"\n### {st}\n")
            pos = sdf[sdf["Additive_Sign"] == "+additive"].head(5)
            neg = sdf[sdf["Additive_Sign"] == "-additive"].head(5)
            lines.append("**Top +additive**\n")
            for _, r in pos.iterrows():
                lines.append(f"- {r['Triple']}: Additive={r['Additive']:.4f}, n_ABC={int(r['n_ABC'])}\n")
            lines.append("\n**Top −additive**\n")
            for _, r in neg.iterrows():
                lines.append(f"- {r['Triple']}: Additive={r['Additive']:.4f}, n_ABC={int(r['n_ABC'])}\n")

    lines.append("\n## OS associations (univariate Cox)\n")
    lines.append("Filters: n_pos>=20 and n_neg>=40 within each stage.\n")

    if len(single_os):  # top by p
        lines.append("\n### Single genes (top by p)\n")
        for st in STAGES:
            sdf = single_os[single_os["Stage"] == st].sort_values("p").head(5)
            if len(sdf) == 0:
                continue
            lines.append(f"\n**{st}**\n")
            for _, r in sdf.iterrows():
                lines.append(f"- {r['Feature']}: HR={r['HR']:.2f} (CI {r['CI_lo']:.2f}-{r['CI_hi']:.2f}), p={r['p']:.3g}, medOS(mut)={r['median_OS_pos']:.1f} vs wt={r['median_OS_neg']:.1f}\n")

    if len(pair_os_add):
        lines.append("\n### Pairs (top by p)\n")
        for st in STAGES:
            sdf = pair_os_add[pair_os_add["Stage"] == st].sort_values("p").head(5)
            if len(sdf) == 0:
                continue
            lines.append(f"\n**{st}**\n")
            for _, r in sdf.iterrows():
                add = r.get("Additive", np.nan)
                lines.append(
                    f"- {r['Feature']}: HR={r['HR']:.2f} (CI {r['CI_lo']:.2f}-{r['CI_hi']:.2f}), "
                    f"p={r['p']:.3g}, Additive={float(add):.4f}\n"
                )

    if len(triple_os_add):
        lines.append("\n### Triples (top by p)\n")
        for st in STAGES:
            sdf = triple_os_add[triple_os_add["Stage"] == st].sort_values("p").head(5)
            if len(sdf) == 0:
                continue
            lines.append(f"\n**{st}**\n")
            for _, r in sdf.iterrows():
                add = r.get("Additive", np.nan)
                lines.append(
                    f"- {r['Feature']}: HR={r['HR']:.2f} (CI {r['CI_lo']:.2f}-{r['CI_hi']:.2f}), "
                    f"p={r['p']:.3g}, Additive={float(add):.4f}\n"
                )

    out_md.write_text("".join(lines), encoding="utf-8")


def main() -> None:
    tumor_dir = Path(__file__).resolve().parent
    merged_xlsx = tumor_dir / "Merged.xlsx"

    out_xlsx = tumor_dir / "Stage_Mutation_Additive_OS_Report.xlsx"
    out_png = tumor_dir / "Stage_Mutation_Additive_OS_Scatter.png"
    out_md = tumor_dir / "Stage_Mutation_Additive_OS_Summary.md"
    out_png_gene_hm = tumor_dir / "Stage_Gene_Frequency_Heatmap.png"
    out_png_pair_add = tumor_dir / "Stage_Pair_Additive_TopBars.png"
    out_png_triple_add = tumor_dir / "Stage_Triple_Additive_TopBars.png"
    out_png_pair_forest = tumor_dir / "Stage_Cox_Pairs_TopForest.png"
    out_png_triple_forest = tumor_dir / "Stage_Cox_Triples_TopForest.png"

    pat = load_patient_level(merged_xlsx)

    freq_long, freq_tests = build_single_gene_tables(pat)
    pairs_long, top_posneg = build_pair_additive_tables(pat, min_n_pos=15)
    single_os, pair_os = build_os_effect_tables(pat, min_n_pos=20, min_n_neg=40)
    pair_os_add = merge_pair_additive_with_os(pairs_long, pair_os)

    triples_long, top_posneg_triples = build_triple_additive_tables(pat, min_n_pos=10)
    triple_os = build_triple_os_effect_table(pat, min_n_pos=20, min_n_neg=40)
    triple_os_add = merge_triple_additive_with_os(triples_long, triple_os)

    # Stage-level basic counts
    stage_counts = pat["STAGE"].value_counts().reindex(STAGES).reset_index()
    stage_counts.columns = ["Stage", "n_survival_filtered"]

    # Write Excel
    with pd.ExcelWriter(out_xlsx, engine="openpyxl") as xw:
        stage_counts.to_excel(xw, sheet_name="Stage_Counts", index=False)
        freq_long.to_excel(xw, sheet_name="Gene_Frequency_ByStage", index=False)
        freq_tests.to_excel(xw, sheet_name="Gene_StageDiff_Tests", index=False)
        pairs_long.to_excel(xw, sheet_name="Pair_Additive_ByStage", index=False)
        top_posneg.to_excel(xw, sheet_name="Pair_Top_PosNeg", index=False)
        triples_long.to_excel(xw, sheet_name="Triple_Additive_ByStage", index=False)
        top_posneg_triples.to_excel(xw, sheet_name="Triple_Top_PosNeg", index=False)
        single_os.to_excel(xw, sheet_name="Cox_Single_ByStage", index=False)
        pair_os_add.to_excel(xw, sheet_name="Cox_Pair_ByStage", index=False)
        triple_os_add.to_excel(xw, sheet_name="Cox_Triple_ByStage", index=False)

    plot_additive_vs_hr(pair_os_add, out_png)
    plot_gene_freq_heatmap(freq_long, out_png_gene_hm)
    plot_top_additive_bars(
        top_posneg,
        out_png_pair_add,
        label_col="Pair",
        additive_col="Additive",
        ncol="n_AB",
        title="Top +additive / −additive PAIRS by stage (Additive = pAB - pA·pB)",
    )
    plot_top_additive_bars(
        top_posneg_triples,
        out_png_triple_add,
        label_col="Triple",
        additive_col="Additive",
        ncol="n_ABC",
        title="Top +additive / −additive TRIPLES by stage (Additive = pABC - pA·pB·pC)",
    )
    plot_top_cox_forest(pair_os_add, out_png_pair_forest, title="Top pairwise Cox OS effects by stage (univariate)")
    plot_top_cox_forest(triple_os_add, out_png_triple_forest, title="Top triple Cox OS effects by stage (univariate)")
    write_markdown_summary(out_md, freq_tests, top_posneg, top_posneg_triples, single_os, pair_os_add, triple_os_add)

    print(f"✅ Saved: {out_xlsx}")
    print(f"✅ Saved: {out_png}")
    print(f"✅ Saved: {out_png_gene_hm}")
    print(f"✅ Saved: {out_png_pair_add}")
    print(f"✅ Saved: {out_png_triple_add}")
    print(f"✅ Saved: {out_png_pair_forest}")
    print(f"✅ Saved: {out_png_triple_forest}")
    print(f"✅ Saved: {out_md}")


if __name__ == "__main__":
    main()

