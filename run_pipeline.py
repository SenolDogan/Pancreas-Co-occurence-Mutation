#!/usr/bin/env python3
"""
Reproduce the NewManuscript analysis pipeline end-to-end.

Usage:
    python run_pipeline.py              # full pipeline
    python run_pipeline.py --step 3   # single step (1-based index)
    python run_pipeline.py --list     # show steps

Requires: pip install -r requirements.txt
Input:    analysis/tumor/Merged.xlsx (see data/README.md)
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from config import ANALYSIS_DIR, REPO_ROOT, TUMOR_DIR

STEPS: list[tuple[str, Path, Path]] = [
    (
        "Dead vs alive enrichment (Figure 1 / synergy screen)",
        ANALYSIS_DIR / "dead_alive_comprehensive_analysis.py",
        ANALYSIS_DIR,
    ),
    (
        "Three-group stage comprehensive landscape",
        ANALYSIS_DIR / "stage_3group_comprehensive_analysis.py",
        ANALYSIS_DIR,
    ),
    (
        "TP53/KRAS focused and detailed panels",
        ANALYSIS_DIR / "tp53_kras_focused_analysis.py",
        ANALYSIS_DIR,
    ),
    (
        "TP53/KRAS detailed stage comparison (Figure 5)",
        ANALYSIS_DIR / "tp53_kras_detailed_analysis.py",
        ANALYSIS_DIR,
    ),
    (
        "OS months methodology (Figure 4)",
        ANALYSIS_DIR / "os_months_methodology_analysis.py",
        ANALYSIS_DIR,
    ),
    (
        "Stage-based 14-figure suite + synergy diagnostics",
        TUMOR_DIR / "stage_generate_14_plots.py",
        TUMOR_DIR,
    ),
    (
        "Stage mutation / additive co-occurrence / OS report",
        TUMOR_DIR / "stage_mutation_additive_os_report.py",
        TUMOR_DIR,
    ),
    (
        "DX2COLLECTION_YEAR × combination interaction Cox",
        TUMOR_DIR / "stage_dx_collection_interaction_combo_os.py",
        TUMOR_DIR,
    ),
    (
        "Multivariable Cox + internal validation (Figure 3 / Supp Fig 12)",
        TUMOR_DIR / "stage_multivariable_cox_validation.py",
        TUMOR_DIR,
    ),
    (
        "Timing-interaction sensitivity comparison table",
        TUMOR_DIR / "build_dx_interaction_sensitivity_comparison_table.py",
        TUMOR_DIR,
    ),
    (
        "External validation — four cBioPortal PDAC cohorts",
        TUMOR_DIR / "cbioportal_pdac_validation_report.py",
        TUMOR_DIR,
    ),
    (
        "Compose manuscript figure composites",
        TUMOR_DIR / "compose_stage_manuscript_figures.py",
        TUMOR_DIR,
    ),
    (
        "Build supplementary tables/figures package (optional)",
        TUMOR_DIR / "build_supplementary_materials.py",
        TUMOR_DIR,
    ),
]


def run_step(name: str, script: Path, cwd: Path) -> None:
    if not script.is_file():
        raise FileNotFoundError(f"Missing script: {script}")
    print(f"\n{'=' * 72}\n>>> {name}\n    {script.relative_to(REPO_ROOT)}\n{'=' * 72}")
    subprocess.run([sys.executable, str(script)], cwd=str(cwd), check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run NewManuscript analysis pipeline")
    parser.add_argument("--step", type=int, help="Run only this 1-based step index")
    parser.add_argument("--list", action="store_true", help="List pipeline steps")
    parser.add_argument("--skip-supp", action="store_true", help="Skip supplementary build (step 13)")
    args = parser.parse_args()

    merged = TUMOR_DIR / "Merged.xlsx"
    if not merged.is_file():
        print(f"ERROR: Missing cohort file: {merged}\nSee data/README.md")
        return 1

    steps = STEPS if not args.skip_supp else STEPS[:-1]

    if args.list:
        for i, (name, script, _) in enumerate(steps, start=1):
            flag = "OK" if script.is_file() else "MISSING"
            print(f"{i:2d}. [{flag}] {name}")
        return 0

    if args.step is not None:
        if args.step < 1 or args.step > len(steps):
            print(f"Step must be 1–{len(steps)}")
            return 1
        name, script, cwd = steps[args.step - 1]
        run_step(name, script, cwd)
        return 0

    for name, script, cwd in steps:
        if not script.is_file():
            print(f"Skip (not found): {script}")
            continue
        run_step(name, script, cwd)

    print("\nPipeline complete. See outputs/figures and analysis/tumor/ for generated files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
