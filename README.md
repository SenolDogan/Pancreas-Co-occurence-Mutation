# Pancreas co-occurrence mutation analysis (NewManuscript)

Reproducible code for the integrated PDAC cohort analysis (**N≈2,330**): dual/triple mutation co-occurrence, synergy-style enrichment (deceased vs living), stage-stratified Cox models, diagnosis-to-collection timing interactions, internal validation, and external replication in four cBioPortal cohorts.

Repository: [github.com/SenolDogan/Pancreas-Co-occurence-Mutation](https://github.com/SenolDogan/Pancreas-Co-occurence-Mutation)

## Quick start

```bash
git clone https://github.com/SenolDogan/Pancreas-Co-occurence-Mutation.git
cd Pancreas-Co-occurence-Mutation

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Requires analysis/tumor/Merged.xlsx (included in data/)
python run_pipeline.py --list    # show steps
python run_pipeline.py           # run all analyses
```

## Repository layout

```
├── run_pipeline.py          # Master runner (13 steps)
├── config.py                # Paths and gene/stage constants
├── data/
│   └── Merged.xlsx          # Integrated discovery cohort
├── analysis/
│   ├── dead_alive_comprehensive_analysis.py
│   ├── stage_3group_comprehensive_analysis.py
│   ├── tp53_kras_*.py
│   └── tumor/               # Stage Cox, timing interaction, supplementary build
├── outputs/figures/         # Curated main-text figure PNGs
├── manuscript/
│   └── NewManuscript.docx
└── docs/
    ├── REPRODUCIBILITY.md
    └── FIGURES_AND_TABLES.md
```

## Main results produced

| Analysis | Key outputs |
|----------|-------------|
| Enrichment (dead vs alive) | `01_Dead_Alive_Comprehensive_Analysis.png`, synergy tables |
| Three-group stage landscape | `Stage_3Group_Comprehensive_Analysis.png` |
| Stage-stratified Cox | `Stage_Figure2_AB_ForestPlots_VSTACK.png`, `Stage_Multivariable_Cox_Report.xlsx` |
| Timing × genotype (novel) | `Stage_DX2Collection_*_Volcano.png`, sensitivity Excel |
| External validation | `Validation_cBioPortal_FourStudies_Report.md` |
| Supplementary package | `build_supplementary_materials.py` → Word/Excel under `analysis/tumor/supplementary/` |

See [docs/FIGURES_AND_TABLES.md](docs/FIGURES_AND_TABLES.md) for the full mapping to manuscript Figures 1–7 and Tables 1–5.

## Manuscript utilities

Word-only helpers (citations, supplementary numbering, figure embedding) live in `analysis/tumor/`:

- `restore_manuscript_figures.py` — embed PNGs above legends in `manuscript/NewManuscript.docx`
- `fix_supplementary_sequential_order.py` — supplementary Methods/Figures/Tables citation order
- `audit_supplementary_references.py` — check in-text vs end-matter inventory

## Data and ethics

The discovery cohort is a merged patient-level table (`Merged.xlsx`) with binary mutation calls and clinical fields. External cohorts are downloaded from the public cBioPortal API at runtime (no credentials required).

## Requirements

Python 3.10+, packages in [requirements.txt](requirements.txt). Network access needed for cBioPortal step (pipeline step 11).

## Citation

Please cite the accompanying manuscript when available and link to this repository.

## Contact

Senol Dogan — issues via GitHub Issues on this repository.
