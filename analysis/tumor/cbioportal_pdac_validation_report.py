#!/usr/bin/env python3
"""
Fetch four cBioPortal PDAC studies, align to discovery-style metrics, print a validation summary.

Studies (editor-facing external cohorts):
  - paad_tcga_gdc
  - paad_tcga_pan_can_atlas_2018
  - pancreas_cptac_gdc
  - pdac_msk_2024

Metrics (match Tumor/Merged.xlsx conventions where possible):
  - Patient-level binary presence for 10 genes (any mutation row in MAF for that patient/sample).
  - OS: OS_MONTHS > 0, event = OS_STATUS starting with "1" (DECEASED) or "1:" pattern.
  - Univariate Cox: covariate = TP53+KRAS both mutated vs not (lifelines).

Requires: pandas, numpy, lifelines, urllib (stdlib).
"""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd

BASE = "https://www.cbioportal.org/api"
GENE_TO_ENTREZ: Dict[str, int] = {
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
GENES = list(GENE_TO_ENTREZ.keys())
ENTREZ_TO_GENE = {v: k for k, v in GENE_TO_ENTREZ.items()}

# Prespecified dual pairs (discovery Table 3 / Nat Commun extension)
DUAL_PAIRS: List[Tuple[str, str]] = [
    ("TP53", "KRAS"),
    ("TP53", "SMAD4"),
    ("TP53", "ARID1A"),
    ("KRAS", "ARID1A"),
    ("TP53", "CDKN2A"),
]
STUDY_LABELS: Dict[str, str] = {
    "paad_tcga_gdc": "TCGA PAAD (GDC 2025)",
    "paad_tcga_pan_can_atlas_2018": "TCGA Pan-Cancer Atlas",
    "pancreas_cptac_gdc": "CPTAC Pancreatic (GDC 2025)",
    "pdac_msk_2024": "MSK PDAC (Nat Med 2024)",
    "DISCOVERY": "Primary integrated cohort",
}


def http_get(url: str, timeout: int = 180) -> Any:
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_sequenced_sample_list_id(study_id: str) -> str:
    lists = http_get(f"{BASE}/studies/{study_id}/sample-lists")
    for sl in lists:
        if sl.get("category") == "all_cases_with_mutation_data":
            return sl["sampleListId"]
    for sl in lists:
        if sl.get("category") == "all_cases_in_study":
            return sl["sampleListId"]
    raise RuntimeError(f"No sample list for {study_id}")


def get_mutation_profile_id(study_id: str) -> str:
    profs = http_get(f"{BASE}/studies/{study_id}/molecular-profiles")
    for p in profs:
        if p.get("molecularAlterationType") == "MUTATION_EXTENDED":
            return p["molecularProfileId"]
    raise RuntimeError(f"No mutation profile for {study_id}")


def fetch_all_mutations_for_genes(
    molecular_profile_id: str, sample_list_id: str, entrez_ids: List[int]
) -> List[dict]:
    out: List[dict] = []
    for eid in entrez_ids:
        page = 0
        while True:
            q = urllib.parse.urlencode(
                {
                    "sampleListId": sample_list_id,
                    "entrezGeneId": str(eid),
                    "pageSize": "100000",
                    "pageNumber": str(page),
                    "projection": "SUMMARY",
                }
            )
            url = f"{BASE}/molecular-profiles/{molecular_profile_id}/mutations?{q}"
            batch = http_get(url)
            if not batch:
                break
            out.extend(batch)
            if len(batch) < 100000:
                break
            page += 1
            time.sleep(0.05)
        time.sleep(0.05)
    return out


def fetch_patient_clinical_os(study_id: str) -> pd.DataFrame:
    """Pivot OS_MONTHS / OS_STATUS from patient clinical-data endpoint (paginated)."""
    rows: List[dict] = []
    page = 0
    page_size = 10000
    while True:
        q = urllib.parse.urlencode(
            {
                "clinicalDataType": "PATIENT",
                "pageSize": str(page_size),
                "pageNumber": str(page),
                "projection": "DETAILED",
            }
        )
        url = f"{BASE}/studies/{study_id}/clinical-data?{q}"
        batch = http_get(url)
        if not batch:
            break
        rows.extend(batch)
        if len(batch) < page_size:
            break
        page += 1
        time.sleep(0.05)

    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(columns=["patientId", "OS_MONTHS", "OS_STATUS"])

    sub = df[df["clinicalAttributeId"].isin(["OS_MONTHS", "OS_STATUS"])].copy()
    wide = sub.pivot_table(
        index=["studyId", "patientId"],
        columns="clinicalAttributeId",
        values="value",
        aggfunc="first",
    ).reset_index()
    wide.columns.name = None
    if "OS_MONTHS" not in wide.columns:
        wide["OS_MONTHS"] = np.nan
    if "OS_STATUS" not in wide.columns:
        wide["OS_STATUS"] = np.nan
    return wide.rename(columns={"patientId": "PATIENT_ID"})


def sample_to_patient(sample_id: str) -> str:
    parts = sample_id.split("-")
    if len(parts) >= 3:
        return "-".join(parts[:3])
    return sample_id


def mutations_to_patient_genes(mut_rows: List[dict]) -> Dict[str, Set[str]]:
    """Map patientId -> set of gene symbols mutated (any row; SUMMARY uses entrezGeneId)."""
    by_patient: Dict[str, Set[str]] = defaultdict(set)
    for m in mut_rows:
        eid = m.get("entrezGeneId")
        hugo = ENTREZ_TO_GENE.get(int(eid)) if eid is not None else None
        if not hugo:
            g = m.get("gene")
            if isinstance(g, dict):
                hugo = g.get("hugoGeneSymbol")
            elif isinstance(g, str):
                hugo = g
        if not hugo:
            continue
        pid = m.get("patientId")
        if not pid:
            sid = m.get("sampleId")
            if not sid:
                continue
            pid = sample_to_patient(str(sid))
        by_patient[str(pid)].add(str(hugo))
    return by_patient


def combo_label(g1: str, g2: str) -> str:
    return f"{g1}+{g2}"


def fit_univariate_cox(cdf: pd.DataFrame, cov_col: str) -> Tuple[float, float, float, float, int, str]:
    """Return HR, CI lo, CI hi, p, n_cox, note."""
    hr = lo = hi = pval = float("nan")
    note = ""
    n_cox = int(len(cdf))
    if n_cox < 15 or cdf[cov_col].sum() == 0 or (cdf[cov_col] == 0).sum() == 0:
        note = "Cox not fitted (sparse strata or N too small after OS filter)."
        return hr, lo, hi, pval, n_cox, note
    from lifelines import CoxPHFitter

    cph = CoxPHFitter()
    cph.fit(cdf, duration_col="OS_MONTHS", event_col="event")
    hr = float(np.exp(cph.params_[cov_col]))
    lo, hi = [float(x) for x in np.exp(cph.confidence_intervals_.loc[cov_col])]
    pval = float(cph.summary.loc[cov_col, "p"])
    return hr, lo, hi, pval, n_cox, note


def discovery_reference(merged_xlsx: Path) -> Tuple[int, Dict[str, float], List[dict]]:
    df = pd.read_excel(merged_xlsx, usecols=["PATIENT_ID", "Hugo_Symbol", "OS_MONTHS", "OS_STATUS"])
    muts = df.groupby("PATIENT_ID")["Hugo_Symbol"].apply(lambda s: set(s.dropna().astype(str)))
    clin = df.groupby("PATIENT_ID").first()
    patients = list(clin.index)
    n = len(patients)
    freq = {g: sum(g in muts[p] for p in patients) / n * 100 for g in GENES}

    rows = []
    for pid in patients:
        g = muts.get(pid, set())
        om = pd.to_numeric(clin.loc[pid, "OS_MONTHS"], errors="coerce")
        st = str(clin.loc[pid, "OS_STATUS"])
        ev = 1 if st == "1:DECEASED" else 0
        rec: dict = {"OS_MONTHS": om, "event": ev}
        for g1, g2 in DUAL_PAIRS:
            rec[combo_label(g1, g2)] = 1 if (g1 in g and g2 in g) else 0
        rows.append(rec)
    cdf = pd.DataFrame(rows).dropna(subset=["OS_MONTHS"])
    cdf = cdf[cdf["OS_MONTHS"] > 0]

    pair_rows: List[dict] = []
    for g1, g2 in DUAL_PAIRS:
        lab = combo_label(g1, g2)
        prev = float(cdf[lab].mean() * 100)
        hr, lo, hi, pval, n_cox, note = fit_univariate_cox(cdf, lab)
        pair_rows.append(
            {
                "study_id": "DISCOVERY",
                "study_label": STUDY_LABELS["DISCOVERY"],
                "dual_pair": lab,
                "n_patients_clinical": n,
                "n_cox": n_cox,
                "combo_prevalence_pct": prev,
                "hr": hr,
                "ci_lo": lo,
                "ci_hi": hi,
                "p_value": pval,
                "cox_note": note,
            }
        )
    return n, freq, pair_rows


def external_cohort_stats(
    study_id: str, mut_profile: str, sample_list_id: str, clin: pd.DataFrame, mut_rows: List[dict]
) -> Tuple[dict, List[dict]]:
    by_p = mutations_to_patient_genes(mut_rows)
    clin = clin[clin["studyId"] == study_id].copy() if "studyId" in clin.columns else clin
    clin["OS_MONTHS"] = pd.to_numeric(clin["OS_MONTHS"], errors="coerce")

    def parse_event(st: Any) -> int:
        s = str(st).upper()
        if s.startswith("1:") or s.startswith("1"):
            return 1
        if "DECEASED" in s or "DEAD" in s:
            return 1
        return 0

    clin["event"] = clin["OS_STATUS"].map(parse_event)
    pids = clin["PATIENT_ID"].astype(str).tolist()
    n = len(pids)
    freq = {g: sum(g in by_p.get(p, set()) for p in pids) / max(n, 1) * 100 for g in GENES}

    rows = []
    for _, r in clin.iterrows():
        pid = str(r["PATIENT_ID"])
        genes = by_p.get(pid, set())
        rec: dict = {"OS_MONTHS": r["OS_MONTHS"], "event": int(bool(r["event"]))}
        for g1, g2 in DUAL_PAIRS:
            rec[combo_label(g1, g2)] = 1 if (g1 in genes and g2 in genes) else 0
        rows.append(rec)
    cdf = pd.DataFrame(rows).dropna(subset=["OS_MONTHS"])
    cdf = cdf[cdf["OS_MONTHS"] > 0]

    pair_rows: List[dict] = []
    for g1, g2 in DUAL_PAIRS:
        lab = combo_label(g1, g2)
        prev = float(cdf[lab].mean() * 100) if len(cdf) else float("nan")
        hr, lo, hi, pval, n_cox, note = fit_univariate_cox(cdf, lab)
        pair_rows.append(
            {
                "study_id": study_id,
                "study_label": STUDY_LABELS.get(study_id, study_id),
                "dual_pair": lab,
                "n_patients_clinical": n,
                "n_cox": n_cox,
                "combo_prevalence_pct": prev,
                "hr": hr,
                "ci_lo": lo,
                "ci_hi": hi,
                "p_value": pval,
                "cox_note": note,
            }
        )

    meta = {
        "study_id": study_id,
        "n_patients_clinical": n,
        "n_cox": int(len(cdf)),
        "freq": freq,
        "n_patients_any_mutation_record": len(by_p),
        "sample_list_id": sample_list_id,
        "mutation_profile_id": mut_profile,
    }
    return meta, pair_rows


def main() -> int:
    tumor_dir = Path(__file__).resolve().parent
    merged = tumor_dir / "Merged.xlsx"
    if not merged.is_file():
        print(f"Missing {merged}", file=sys.stderr)
        return 1

    studies = [
        "paad_tcga_gdc",
        "paad_tcga_pan_can_atlas_2018",
        "pancreas_cptac_gdc",
        "pdac_msk_2024",
    ]

    print("Loading discovery reference from Merged.xlsx …")
    n_d, f_d, disc_pairs = discovery_reference(merged)
    tp53_kras_d = next(r for r in disc_pairs if r["dual_pair"] == "TP53+KRAS")
    print(
        f"Discovery N={n_d}, TP53+KRAS%={tp53_kras_d['combo_prevalence_pct']:.1f}, "
        f"Cox HR={tp53_kras_d['hr']:.2f}, p={tp53_kras_d['p_value']:.3g}\n"
    )

    all_rows: List[dict] = list(disc_pairs)
    lines: List[str] = []
    lines.append("# cBioPortal four-study validation summary\n")
    lines.append(f"- Discovery: Tumor/Merged.xlsx (N={n_d})\n")
    lines.append(
        f"- Discovery TP53+KRAS Cox HR={tp53_kras_d['hr']:.2f}, p={tp53_kras_d['p_value']:.3g}\n"
    )
    lines.append("- Extended dual-pair Cox table: `Validation_cBioPortal_FivePairs_FourStudies.xlsx`\n\n")

    for sid in studies:
        print(f"=== {sid} ===")
        sl = get_sequenced_sample_list_id(sid)
        mp = get_mutation_profile_id(sid)
        print(f"  sampleList={sl}, mutationProfile={mp}")
        print("  fetching mutations (10 genes) …")
        muts = fetch_all_mutations_for_genes(mp, sl, list(GENE_TO_ENTREZ.values()))
        print(f"  mutation rows: {len(muts)}")
        print("  fetching clinical OS …")
        clin = fetch_patient_clinical_os(sid)
        meta, pair_rows = external_cohort_stats(sid, mp, sl, clin, muts)
        all_rows.extend(pair_rows)
        tk = next(r for r in pair_rows if r["dual_pair"] == "TP53+KRAS")
        print(
            f"  N clinical={meta['n_patients_clinical']}, N cox={meta['n_cox']}, "
            f"TP53+KRAS%={tk['combo_prevalence_pct']:.1f}, HR={tk['hr']:.3f}, "
            f"p={tk['p_value']:.3g} {tk['cox_note']}"
        )

        lines.append(f"## {sid}\n")
        lines.append(f"- Sequenced sample list: `{sl}`\n")
        lines.append(f"- Mutation profile: `{mp}`\n")
        lines.append(f"- Patients with OS fields: {meta['n_patients_clinical']}\n")
        lines.append(f"- Patients used in Cox (OS>0): {meta['n_cox']}\n")
        lines.append(
            f"- TP53+KRAS prevalence: **{tk['combo_prevalence_pct']:.1f}%** "
            f"(discovery {tp53_kras_d['combo_prevalence_pct']:.1f}%)\n"
        )
        lines.append(
            f"- Univariate Cox TP53+KRAS vs others: HR **{tk['hr']:.3f}** "
            f"95% CI [{tk['ci_lo']:.3f}, {tk['ci_hi']:.3f}], p **{tk['p_value']:.3g}** {tk['cox_note']}\n"
        )
        lines.append(
            f"- KRAS%={meta['freq']['KRAS']:.1f} TP53%={meta['freq']['TP53']:.1f} "
            f"CDKN2A%={meta['freq']['CDKN2A']:.1f} SMAD4%={meta['freq']['SMAD4']:.1f}\n"
        )
        lines.append("\n| Dual pair | Prev% | HR | 95% CI | p |\n")
        lines.append("|---|---:|---:|---|---:|\n")
        for pr in pair_rows:
            lines.append(
                f"| {pr['dual_pair']} | {pr['combo_prevalence_pct']:.1f} | "
                f"{pr['hr']:.3f} | [{pr['ci_lo']:.3f}, {pr['ci_hi']:.3f}] | {pr['p_value']:.3g} |\n"
            )
        lines.append("\n")

    tbl = pd.DataFrame(all_rows)
    out_xlsx = tumor_dir / "Validation_cBioPortal_FivePairs_FourStudies.xlsx"
    pivot_hr = tbl.pivot_table(
        index="dual_pair", columns="study_id", values="hr", aggfunc="first"
    )
    with pd.ExcelWriter(out_xlsx, engine="openpyxl") as w:
        tbl.to_excel(w, sheet_name="All_rows", index=False)
        pivot_hr.to_excel(w, sheet_name="HR_pivot")
        tbl.pivot_table(
            index="dual_pair", columns="study_id", values="p_value", aggfunc="first"
        ).to_excel(w, sheet_name="P_pivot")

    out_md = tumor_dir / "Validation_cBioPortal_FourStudies_Report.md"
    out_md.write_text("".join(lines), encoding="utf-8")
    print(f"\nWrote {out_md}")
    print(f"Wrote {out_xlsx} ({len(tbl)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
