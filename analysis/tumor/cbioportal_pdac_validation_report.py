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


def discovery_reference(merged_xlsx: Path) -> Tuple[int, Dict[str, float], float, float, float]:
    df = pd.read_excel(merged_xlsx, usecols=["PATIENT_ID", "Hugo_Symbol", "OS_MONTHS", "OS_STATUS"])
    muts = df.groupby("PATIENT_ID")["Hugo_Symbol"].apply(lambda s: set(s.dropna().astype(str)))
    clin = df.groupby("PATIENT_ID").first()
    patients = list(clin.index)
    n = len(patients)
    freq = {g: sum(g in muts[p] for p in patients) / n * 100 for g in GENES}
    both_pct = sum(("TP53" in muts[p]) and ("KRAS" in muts[p]) for p in patients) / n * 100

    rows = []
    for pid in patients:
        g = muts.get(pid, set())
        om = pd.to_numeric(clin.loc[pid, "OS_MONTHS"], errors="coerce")
        st = str(clin.loc[pid, "OS_STATUS"])
        ev = 1 if st == "1:DECEASED" else 0
        rows.append({"OS_MONTHS": om, "event": ev, "both": 1 if ("TP53" in g and "KRAS" in g) else 0})
    cdf = pd.DataFrame(rows).dropna(subset=["OS_MONTHS"])
    cdf = cdf[cdf["OS_MONTHS"] > 0]
    from lifelines import CoxPHFitter

    cph = CoxPHFitter()
    cph.fit(cdf, duration_col="OS_MONTHS", event_col="event")
    hr = float(np.exp(cph.params_["both"]))
    lo, hi = [float(x) for x in np.exp(cph.confidence_intervals_.loc["both"])]
    pval = float(cph.summary.loc["both", "p"])
    return n, freq, both_pct, hr, pval


def external_cohort_stats(
    study_id: str, mut_profile: str, sample_list_id: str, clin: pd.DataFrame, mut_rows: List[dict]
) -> dict:
    by_p = mutations_to_patient_genes(mut_rows)
    # restrict to patients with clinical OS rows
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
    freq = {}
    for g in GENES:
        freq[g] = sum(g in by_p.get(p, set()) for p in pids) / max(n, 1) * 100
    both_pct = sum(("TP53" in by_p.get(p, set())) and ("KRAS" in by_p.get(p, set())) for p in pids) / max(n, 1) * 100

    rows = []
    for _, r in clin.iterrows():
        pid = str(r["PATIENT_ID"])
        genes = by_p.get(pid, set())
        om = r["OS_MONTHS"]
        ev = int(bool(r["event"]))
        rows.append({"OS_MONTHS": om, "event": ev, "both": 1 if ("TP53" in genes and "KRAS" in genes) else 0})
    cdf = pd.DataFrame(rows).dropna(subset=["OS_MONTHS"])
    cdf = cdf[cdf["OS_MONTHS"] > 0]
    hr = lo = hi = pval = float("nan")
    cox_note = ""
    if len(cdf) >= 15 and cdf["both"].sum() > 0 and (cdf["both"] == 0).sum() > 0:
        from lifelines import CoxPHFitter

        cph = CoxPHFitter()
        cph.fit(cdf, duration_col="OS_MONTHS", event_col="event")
        hr = float(np.exp(cph.params_["both"]))
        lo, hi = [float(x) for x in np.exp(cph.confidence_intervals_.loc["both"])]
        pval = float(cph.summary.loc["both", "p"])
    else:
        cox_note = "Cox not fitted (sparse both-strata or N too small after OS filter)."

    return {
        "study_id": study_id,
        "n_patients_clinical": n,
        "n_cox": int(len(cdf)),
        "freq": freq,
        "both_pct": both_pct,
        "hr_tp53kras": hr,
        "ci_lo": lo,
        "ci_hi": hi,
        "p_tp53kras": pval,
        "cox_note": cox_note,
        "n_patients_any_mutation_record": len(by_p),
    }


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
    n_d, f_d, both_d, hr_d, p_d = discovery_reference(merged)
    print(f"Discovery N={n_d}, TP53+KRAS%={both_d:.1f}, Cox HR={hr_d:.2f}, p={p_d:.3g}\n")

    lines: List[str] = []
    lines.append("# cBioPortal four-study validation summary\n")
    lines.append(f"- Discovery: Tumor/Merged.xlsx (N={n_d})\n")
    lines.append(f"- Discovery TP53+KRAS Cox HR={hr_d:.2f}, p={p_d:.3g}\n\n")

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
        stats = external_cohort_stats(sid, mp, sl, clin, muts)
        print(
            f"  N clinical={stats['n_patients_clinical']}, N cox={stats['n_cox']}, "
            f"TP53+KRAS%={stats['both_pct']:.1f}, HR={stats['hr_tp53kras']:.3f}, "
            f"p={stats['p_tp53kras']:.3g} {stats['cox_note']}"
        )

        lines.append(f"## {sid}\n")
        lines.append(f"- Sequenced sample list: `{sl}`\n")
        lines.append(f"- Mutation profile: `{mp}`\n")
        lines.append(f"- Patients with OS fields: {stats['n_patients_clinical']}\n")
        lines.append(f"- Patients used in Cox (OS>0): {stats['n_cox']}\n")
        lines.append(f"- TP53+KRAS prevalence: **{stats['both_pct']:.1f}%** (discovery {both_d:.1f}%)\n")
        lines.append(
            f"- Univariate Cox TP53+KRAS vs others: HR **{stats['hr_tp53kras']:.3f}** "
            f"95% CI [{stats['ci_lo']:.3f}, {stats['ci_hi']:.3f}], p **{stats['p_tp53kras']:.3g}** {stats['cox_note']}\n"
        )
        lines.append(
            f"- KRAS%={stats['freq']['KRAS']:.1f} TP53%={stats['freq']['TP53']:.1f} "
            f"CDKN2A%={stats['freq']['CDKN2A']:.1f} SMAD4%={stats['freq']['SMAD4']:.1f}\n\n"
        )

    out_md = tumor_dir / "Validation_cBioPortal_FourStudies_Report.md"
    out_md.write_text("".join(lines), encoding="utf-8")
    print(f"\nWrote {out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
