#!/usr/bin/env python3
"""
Nat Commun feasibility analyses on existing Merged.xlsx + prior outputs.
Outputs: NatCommun_Feasibility_Report.md, Excel summary, KM PNGs.
"""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from itertools import combinations
from pathlib import Path
from typing import Dict, List, Set, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

TUMOR = Path(__file__).resolve().parent
MERGED = TUMOR / "Merged.xlsx"
OUT_MD = TUMOR / "NatCommun_Feasibility_Report.md"
OUT_XLSX = TUMOR / "NatCommun_Feasibility_Summary.xlsx"

STAGES = ["Metastatic", "Resectable", "Borderline Resectable/Locally Advanced"]
GENES = ["TP53", "KRAS", "CDKN2A", "SMAD4", "ARID1A", "ATM", "PIK3CA", "BRAF", "GNAS", "RNF43"]

# Prespecified dual pairs (Table 3 / main text)
TOP_PAIRS = [
    "TP53+KRAS",
    "TP53+SMAD4",
    "TP53+ARID1A",
    "KRAS+ARID1A",
    "TP53+CDKN2A",
]
TOP_TRIPLE = "TP53+KRAS+SMAD4"

CBIO_BASE = "https://www.cbioportal.org/api"
GENE_ENTREZ = {
    "TP53": 7157,
    "KRAS": 3845,
    "CDKN2A": 1029,
    "SMAD4": 4089,
    "ARID1A": 8289,
    "ATM": 472,
    "PIK3CA": 5290,
    "BRAF": 673,
    "GNAS": 2778,
    "RNF43": 54894,
}


def load_patients() -> pd.DataFrame:
    df = pd.read_excel(MERGED, sheet_name=0)
    pid = "PATIENT_ID"
    clinical = [
        pid,
        "STAGE",
        "OS_MONTHS",
        "OS_STATUS",
        "AGE",
        "SEX",
        "DX2COLLECTION_YEAR",
        "TARGETED_THERAPY",
        "ADJ_TREATMENT",
        "NEOADJ_TREATMENT",
        "SYSTEMIC_TX",
        "DISEASE_STATUS",
    ]
    clinical = [c for c in clinical if c in df.columns and c != pid]
    pat = df.groupby(pid)[clinical].first()
    pat = pat.reset_index()
    muts = df.groupby(pid)["Hugo_Symbol"].apply(lambda s: set(s.dropna().astype(str)))
    for g in GENES:
        pat[g] = pat[pid].map(lambda p: int(g in muts[p]))
    for combo in TOP_PAIRS:
        a, b = combo.split("+")
        pat[combo.replace("+", "_")] = ((pat[a] == 1) & (pat[b] == 1)).astype(int)
    a, b, c = "TP53", "KRAS", "SMAD4"
    pat["TP53_KRAS_SMAD4"] = ((pat[a] == 1) & (pat[b] == 1) & (pat[c] == 1)).astype(int)

    pat["STAGE"] = pat["STAGE"].astype(str)
    pat = pat[pat["STAGE"].isin(STAGES)].copy()
    pat["OS_MONTHS"] = pd.to_numeric(pat["OS_MONTHS"], errors="coerce")
    pat["event"] = (pat["OS_STATUS"].astype(str) == "1:DECEASED").astype(int)
    pat["dx_yr"] = pd.to_numeric(pat.get("DX2COLLECTION_YEAR", np.nan), errors="coerce")
    pat["AGE"] = pd.to_numeric(pat.get("AGE", np.nan), errors="coerce")
    return pat


def format_logrank_p(p: float) -> str:
    if p < 1e-300:
        return "<1e-300"
    if p >= 1e-3:
        return f"{p:.4f}"
    return f"{p:.3e}"


def km_logrank_report(pat: pd.DataFrame, combo_col: str, stage: str | None, out_png: Path) -> dict:
    from lifelines import KaplanMeierFitter
    from lifelines.statistics import logrank_test

    sub = pat.copy()
    if stage:
        sub = sub[sub["STAGE"] == stage]
    sub = sub.dropna(subset=["OS_MONTHS"])
    sub = sub[sub["OS_MONTHS"] > 0]
    pos = sub[sub[combo_col] == 1]
    neg = sub[sub[combo_col] == 0]
    if len(pos) < 5 or len(neg) < 5:
        return {"ok": False, "reason": f"N+={len(pos)}, N-={len(neg)}"}

    lr = logrank_test(
        pos["OS_MONTHS"],
        neg["OS_MONTHS"],
        pos["event"],
        neg["event"],
    )
    fig, ax = plt.subplots(figsize=(6, 4.5))
    kmf = KaplanMeierFitter()
    for label, df_g in [("Combo+", pos), ("Combo−", neg)]:
        kmf.fit(df_g["OS_MONTHS"], event_observed=df_g["event"], label=f"{label} (n={len(df_g)})")
        kmf.plot_survival_function(ax=ax)
    title_stage = stage or "All stages"
    ax.set_title(f"OS — {combo_col.replace('_', '+')} ({title_stage})")
    ax.set_xlabel("Months")
    ax.set_ylabel("Survival probability")
    pv = format_logrank_p(float(lr.p_value))
    ax.text(
        0.02,
        0.02,
        f"Log-rank p={pv}",
        transform=ax.transAxes,
        fontsize=10,
        verticalalignment="bottom",
        bbox={"boxstyle": "round,pad=0.35", "facecolor": "white", "edgecolor": "#666666", "alpha": 0.92},
    )
    fig.tight_layout()
    fig.savefig(out_png, dpi=150)
    plt.close(fig)
    med_pos = float(pos["OS_MONTHS"].median())
    med_neg = float(neg["OS_MONTHS"].median())
    return {
        "ok": True,
        "n_pos": len(pos),
        "n_neg": len(neg),
        "logrank_p": float(lr.p_value),
        "median_os_pos": med_pos,
        "median_os_neg": med_neg,
        "png": str(out_png.name),
    }


def km_tp53kras_discovery_supplementary_panels(os_ok: pd.DataFrame, out_png: Path) -> dict[str, dict]:
    """Single row: (A) all stages, (B) metastatic; log-rank p annotated on each panel."""
    from lifelines import KaplanMeierFitter
    from lifelines.statistics import logrank_test

    combo_col = "TP53_KRAS"
    specs: List[Tuple[str | None, str, str]] = [
        (None, "All prespecified stage groups", "A"),
        ("Metastatic", "Metastatic", "B"),
    ]
    out: dict[str, dict] = {}
    fig, axes = plt.subplots(1, 2, figsize=(11.3, 4.7))

    for ax, (stage, title_mid, panel) in zip(axes, specs):
        sub = os_ok.copy()
        if stage:
            sub = sub[sub["STAGE"] == stage]
        pos = sub[sub[combo_col] == 1]
        neg = sub[sub[combo_col] == 0]
        if len(pos) < 5 or len(neg) < 5:
            ax.axis("off")
            ax.text(0.5, 0.5, "Insufficient N", ha="center", va="center", transform=ax.transAxes)
            out[panel.lower()] = {"ok": False, "reason": f"N+={len(pos)}, N−={len(neg)}"}
            continue

        lr = logrank_test(
            pos["OS_MONTHS"], neg["OS_MONTHS"], pos["event"], neg["event"]
        )
        pfmt = format_logrank_p(float(lr.p_value))
        kmf = KaplanMeierFitter()
        for grp_label, df_g in [("TP53+KRAS+", pos), ("Other", neg)]:
            kmf.fit(df_g["OS_MONTHS"], event_observed=df_g["event"], label=f"{grp_label} (n={len(df_g)})")
            kmf.plot_survival_function(ax=ax)

        ax.set_title(f"{panel}: {title_mid}\n(OS; discovery cohort)")
        ax.set_xlabel("Months")
        ax.set_ylabel("Survival probability")
        ax.legend(loc="upper right", fontsize=8)
        ax.text(
            0.02,
            0.02,
            f"({panel}) Log-rank p={pfmt}",
            transform=ax.transAxes,
            fontsize=10,
            verticalalignment="bottom",
            bbox={"boxstyle": "round,pad=0.35", "facecolor": "white", "edgecolor": "#666666", "alpha": 0.92},
        )
        out[panel.lower()] = {
            "ok": True,
            "stage": stage,
            "logrank_p": float(lr.p_value),
            "p_formatted": pfmt,
            "n_pos": len(pos),
            "n_neg": len(neg),
        }

    fig.suptitle("Supplementary Kaplan–Meier: TP53+KRAS versus others (discovery)", fontsize=11, fontweight="bold")
    fig.tight_layout(rect=[0, 0.02, 1, 0.96])
    fig.savefig(out_png, dpi=175)
    plt.close(fig)
    return out


def univariate_cox(pat: pd.DataFrame, combo_col: str, stage: str | None, adjust_tx: bool = False) -> dict:
    from lifelines import CoxPHFitter

    sub = pat.copy()
    if stage:
        sub = sub[sub["STAGE"] == stage]
    sub = sub.dropna(subset=["OS_MONTHS"])
    sub = sub[sub["OS_MONTHS"] > 0]
    cols = [combo_col, "OS_MONTHS", "event"]
    if adjust_tx:
        sub["SYSTEMIC_TX_bin"] = pd.to_numeric(sub.get("SYSTEMIC_TX", 0), errors="coerce").fillna(0)
        sub["AGE_c"] = sub["AGE"]
        cols += ["SYSTEMIC_TX_bin", "AGE_c"]
        sub = sub.dropna(subset=["AGE_c"])
    if sub[combo_col].sum() < 5 or (sub[combo_col] == 0).sum() < 5:
        return {"ok": False}
    try:
        cph = CoxPHFitter()
        cph.fit(sub[cols], duration_col="OS_MONTHS", event_col="event")
        hr = float(np.exp(cph.params_[combo_col]))
        lo, hi = [float(x) for x in np.exp(cph.confidence_intervals_.loc[combo_col])]
        p = float(cph.summary.loc[combo_col, "p"])
        return {"ok": True, "hr": hr, "ci_lo": lo, "ci_hi": hi, "p": p, "n": len(sub)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def cindex_from_existing() -> pd.DataFrame:
    p = TUMOR / "Stage_Multivariable_Cox_Report.xlsx"
    if not p.is_file():
        return pd.DataFrame()
    return pd.read_excel(p, sheet_name="Validation_Summary")


def timing_top_hits() -> pd.DataFrame:
    p = TUMOR / "Stage_DX2Collection_Combo_OS_Interaction.xlsx"
    if not p.is_file():
        return pd.DataFrame()
    df = pd.read_excel(p, sheet_name="Interaction_Cox_All")
    if "p_int_adj_ALL" in df.columns:
        df = df.sort_values("p_int_adj_ALL")
    return df.head(10)


def http_get(url: str) -> list | dict:
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode())


def msk_external_combo_hr(combo_genes: List[str]) -> dict:
    """Quick MSK-only external Cox for one combination (reuse mutation fetch)."""
    study = "pdac_msk_2024"
    try:
        lists = http_get(f"{CBIO_BASE}/studies/{study}/clinical-data?clinicalDataType=PATIENT&pageSize=50000&pageNumber=0&projection=DETAILED")
        # fallback: use cbioportal script pattern - simplified patient clinical
        profs = http_get(f"{CBIO_BASE}/studies/{study}/molecular-profiles")
        mp = next(p["molecularProfileId"] for p in profs if p.get("molecularAlterationType") == "MUTATION_EXTENDED")
        slists = http_get(f"{CBIO_BASE}/studies/{study}/sample-lists")
        sl = next(s["sampleListId"] for s in slists if s.get("category") == "all_cases_with_mutation_data")

        entrez = [GENE_ENTREZ[g] for g in GENES]
        muts: list = []
        for eid in entrez:
            q = urllib.parse.urlencode(
                {"sampleListId": sl, "entrezGeneId": str(eid), "pageSize": "100000", "pageNumber": "0", "projection": "SUMMARY"}
            )
            muts.extend(http_get(f"{CBIO_BASE}/molecular-profiles/{mp}/mutations?{q}") or [])
            time.sleep(0.05)

        # patient clinical from study patients endpoint
        patients = http_get(f"{CBIO_BASE}/studies/{study}/patients?projection=SUMMARY&pageSize=10000&pageNumber=0")
        pids = [p["patientId"] for p in patients]
        clin_rows = []
        for page in range(0, 50):
            q = urllib.parse.urlencode(
                {"clinicalDataType": "PATIENT", "pageSize": "10000", "pageNumber": str(page), "projection": "DETAILED"}
            )
            batch = http_get(f"{CBIO_BASE}/studies/{study}/clinical-data?{q}")
            if not batch:
                break
            clin_rows.extend(batch)
            if len(batch) < 10000:
                break

        os_m, os_s, by_p = {}, {}, {}
        for row in clin_rows:
            pid = str(row.get("patientId", ""))
            attr = row.get("clinicalAttributeId", "")
            val = row.get("value")
            if attr in ("OS_MONTHS", "OS_MONTHS_SURVIVAL"):
                os_m[pid] = float(val) if val not in (None, "", "NA") else np.nan
            if attr in ("OS_STATUS", "OS_STATUS_SURVIVAL"):
                os_s[pid] = str(val)

        by_mut: Dict[str, Set[str]] = {}
        for m in muts:
            g = m.get("gene", {}).get("hugoGeneSymbol") if isinstance(m.get("gene"), dict) else None
            if not g:
                continue
            sid = m.get("sampleId", "")
            # map sample to patient via prefix
            pid = sid.split("-")[0] if "-" in str(sid) else str(sid)
            by_mut.setdefault(pid, set()).add(g)

        rows = []
        for pid in pids:
            pid = str(pid)
            if pid not in os_m:
                continue
            genes = by_mut.get(pid, set())
            hit = all(g in genes for g in combo_genes)
            om = os_m.get(pid, np.nan)
            st = os_s.get(pid, "")
            ev = 1 if str(st).upper().startswith("1") or "DECEASED" in str(st).upper() else 0
            rows.append({"OS_MONTHS": om, "event": ev, "combo": int(hit)})
        cdf = pd.DataFrame(rows).dropna(subset=["OS_MONTHS"])
        cdf = cdf[cdf["OS_MONTHS"] > 0]
        if cdf["combo"].sum() < 10 or (cdf["combo"] == 0).sum() < 10:
            return {"ok": False, "reason": "sparse strata"}
        from lifelines import CoxPHFitter

        cph = CoxPHFitter()
        cph.fit(cdf, duration_col="OS_MONTHS", event_col="event")
        hr = float(np.exp(cph.params_["combo"]))
        lo, hi = [float(x) for x in np.exp(cph.confidence_intervals_.loc["combo"])]
        p = float(cph.summary.loc["combo", "p"])
        return {"ok": True, "study": study, "n": len(cdf), "hr": hr, "ci_lo": lo, "ci_hi": hi, "p": p, "prev_pct": cdf["combo"].mean() * 100}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def main() -> None:
    lines: List[str] = ["# Nat Commun feasibility analysis report\n", f"Generated from `{MERGED.name}` and Tumor outputs.\n\n"]
    pat = load_patients()
    os_ok = pat.dropna(subset=["OS_MONTHS"])
    os_ok = os_ok[os_ok["OS_MONTHS"] > 0]

    lines.append("## 1. Discovery cohort summary\n\n")
    lines.append(f"- Patients (3 stage groups, OS>0): **{len(os_ok)}**\n")
    lines.append(f"- With DX2COLLECTION_YEAR: **{pat['dx_yr'].notna().sum()}**\n")
    lines.append(f"- With SYSTEMIC_TX recorded: **{pat['SYSTEMIC_TX'].notna().sum()}** ({pat['SYSTEMIC_TX'].notna().mean()*100:.1f}%)\n")
    lines.append(f"- TP53+KRAS prevalence: **{pat['TP53_KRAS'].mean()*100:.1f}%**\n\n")

    # KM analyses
    lines.append("## 2. Kaplan–Meier + log-rank (discovery)\n\n")
    km_rows = []
    km_specs = [
        ("TP53_KRAS", None, "KM_TP53_KRAS_all_stages.png"),
        ("TP53_KRAS", "Metastatic", "KM_TP53_KRAS_Metastatic.png"),
        ("TP53_KRAS_SMAD4", "Metastatic", "KM_TP53_KRAS_SMAD4_Metastatic.png"),
    ]
    for col, stage, png in km_specs:
        res = km_logrank_report(os_ok, col, stage, TUMOR / png)
        label = col.replace("_", "+") + (f" / {stage}" if stage else "")
        if res.get("ok"):
            lines.append(
                f"- **{label}**: N+={res['n_pos']}, N−={res['n_neg']}, "
                f"log-rank p={res['logrank_p']:.4g}, median OS +/− = {res['median_os_pos']:.1f} / {res['median_os_neg']:.1f} mo "
                f"(`{res['png']}`)\n"
            )
            km_rows.append({"combo": label, **res})
        else:
            lines.append(f"- **{label}**: not run ({res.get('reason', 'failed')})\n")

    sf14_png = TUMOR / "KM_TP53_KRAS_SuppFigure14_AB.png"
    dp = km_tp53kras_discovery_supplementary_panels(os_ok, sf14_png)
    lines.append("\n### Combined panels for Supplementary Figure 14 (`KM_TP53_KRAS_SuppFigure14_AB.png`)\n\n")
    for key in ["a", "b"]:
        r = dp.get(key, {})
        if r.get("ok"):
            lines.append(
                f"- Panel **({key.upper()})**: log-rank p={r['p_formatted']} (raw {r['logrank_p']:.4g}), "
                f"N+={r['n_pos']}, N−={r['n_neg']}\n"
            )
        else:
            lines.append(f"- Panel **({key.upper()})**: skipped ({r.get('reason')})\n")
    lines.append("\n")

    # Univariate Cox discovery
    lines.append("## 3. Discovery univariate Cox (OS>0)\n\n")
    cox_rows = []
    for combo in TOP_PAIRS:
        col = combo.replace("+", "_")
        for stage in [None, "Metastatic"]:
            r = univariate_cox(os_ok, col, stage, adjust_tx=False)
            r_tx = univariate_cox(os_ok[os_ok["SYSTEMIC_TX"].notna()], col, stage, adjust_tx=True)
            label = combo + (f" ({stage})" if stage else " (all)")
            if r.get("ok"):
                lines.append(f"- {label}: HR={r['hr']:.2f} [{r['ci_lo']:.2f}–{r['ci_hi']:.2f}], p={r['p']:.3g}, n={r['n']}\n")
                cox_rows.append({"combo": label, "adjusted": "no", **r})
            if r_tx.get("ok"):
                lines.append(
                    f"- {label} + AGE + SYSTEMIC_TX (complete-case n={r_tx['n']}): "
                    f"HR={r_tx['hr']:.2f} [{r_tx['ci_lo']:.2f}–{r_tx['ci_hi']:.2f}], p={r_tx['p']:.3g}\n"
                )
                cox_rows.append({"combo": label, "adjusted": "SYSTEMIC_TX+AGE", **r_tx})
    lines.append("\n")

    # C-index
    lines.append("## 4. Internal validation (C-index, existing output)\n\n")
    val = cindex_from_existing()
    if len(val):
        lines.append(val.to_string(index=False) + "\n\n")
    else:
        lines.append("_Stage_Multivariable_Cox_Report.xlsx not found._\n\n")

    # Timing
    lines.append("## 5. Top timing-interaction hits (discovery)\n\n")
    th = timing_top_hits()
    if len(th):
        cols = [c for c in ["Stage", "Feature", "HR_int_adj_ALL", "p_int_adj_ALL", "stable_FDR_lt_0p10"] if c in th.columns]
        lines.append(th[cols].to_string(index=False) + "\n\n")
    else:
        lines.append("_Interaction file not found._\n\n")

    # External MSK for top pairs (network)
    lines.append("## 6. External validation — MSK (pdac_msk_2024), univariate Cox\n\n")
    ext_rows = []
    for combo in TOP_PAIRS[:3]:  # limit API calls
        genes = combo.split("+")
        print(f"MSK Cox for {combo} …")
        er = msk_external_combo_hr(genes)
        if er.get("ok"):
            lines.append(
                f"- **{combo}**: N={er['n']}, prevalence={er['prev_pct']:.1f}%, "
                f"HR={er['hr']:.2f} [{er['ci_lo']:.2f}–{er['ci_hi']:.2f}], p={er['p']:.3g}\n"
            )
            ext_rows.append({"combo": combo, **er})
        else:
            lines.append(f"- **{combo}**: {er.get('reason', er.get('error', 'failed'))}\n")
    lines.append("\n")

    # Feasibility verdict
    lines.append("## 7. Feasibility verdict (Nat Commun boosts)\n\n")
    lines.append("| Analysis | Status | Notes |\n")
    lines.append("|----------|--------|-------|\n")
    lines.append("| KM + log-rank | Done | PNGs in Tumor/ |\n")
    lines.append("| Discovery Cox by stage | Done | Table above |\n")
    lines.append("| Treatment sensitivity | Partial | SYSTEMIC_TX subset only |\n")
    lines.append("| C-index internal validation | From existing file | Already in pipeline |\n")
    lines.append("| MSK external multi-combo | Partial (top 3 pairs) | Full 5 + 4 cohorts: extend script |\n")
    lines.append("| Timing external replication | Not feasible | No dx_yr in cBioPortal |\n")
    lines.append("| MR / functional RNA | Not feasible | No data |\n\n")

    OUT_MD.write_text("".join(lines), encoding="utf-8")
    with pd.ExcelWriter(OUT_XLSX, engine="openpyxl") as w:
        if km_rows:
            pd.DataFrame(km_rows).to_excel(w, sheet_name="KM", index=False)
        if cox_rows:
            pd.DataFrame(cox_rows).to_excel(w, sheet_name="Discovery_Cox", index=False)
        if len(val):
            val.to_excel(w, sheet_name="C_index", index=False)
        if len(th):
            th.to_excel(w, sheet_name="Timing_top10", index=False)
        if ext_rows:
            pd.DataFrame(ext_rows).to_excel(w, sheet_name="MSK_external", index=False)
    print(f"Wrote {OUT_MD}")
    print(f"Wrote {OUT_XLSX}")


if __name__ == "__main__":
    main()
