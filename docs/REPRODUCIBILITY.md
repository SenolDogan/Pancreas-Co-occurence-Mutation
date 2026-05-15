# Reproducibility guide (editors / reviewers)

## Environment

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Python **3.10+** recommended.

## Quick start

```bash
# 1. Confirm cohort file
ls analysis/tumor/Merged.xlsx

# 2. Run full pipeline (~minutes to tens of minutes depending on network for cBioPortal)
python run_pipeline.py

# 3. List steps without running
python run_pipeline.py --list

# 4. Run a single step (example: interaction Cox)
python run_pipeline.py --step 8
```

## Expected outputs

| Location | Contents |
|----------|----------|
| `analysis/tumor/Stage_*.png` | Stage-stratified figures |
| `analysis/tumor/Stage_DX2Collection_*.xlsx` | Timing-interaction Cox tables |
| `analysis/tumor/Stage_Multivariable_Cox_Report.xlsx` | Multivariable Cox by stage |
| `analysis/tumor/Validation_cBioPortal_FourStudies_Report.md` | External cohort summary |
| `outputs/figures/` | Curated copies of main-text figure PNGs |
| `manuscript/NewManuscript.docx` | Manuscript (figures embedded separately) |

## Synergy metrics (definitions)

- **Multiplicative synergy (dead):** observed joint prevalence ÷ (marginal₁ × marginal₂) among deceased patients.
- **Additive deviation:** observed joint − (marginal₁ + marginal₂).
- **Protective score:** −(joint rate deceased − joint rate living).
- **Lethality ratio:** single-gene or joint frequency in deceased ÷ frequency in living.

Multiplicity control for the 45 dual-pair screen: Benjamini–Hochberg FDR q < 0.05 (Bonferroni/Holm reported in supplementary tables).

## Manuscript-only utilities

Scripts under `analysis/tumor/fix_*.py` and `restore_manuscript_figures.py` adjust Word citations and embedded images; they do not change statistical results.

## Citation

If you use this code, please cite the accompanying manuscript (in preparation) and link to this repository:
https://github.com/SenolDogan/Pancreas-Co-occurence-Mutation
