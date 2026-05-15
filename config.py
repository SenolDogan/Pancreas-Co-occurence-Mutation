"""Repository paths for the NewManuscript PDAC co-mutation analysis pipeline."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
ANALYSIS_DIR = REPO_ROOT / "analysis"
TUMOR_DIR = ANALYSIS_DIR / "tumor"
DATA_DIR = REPO_ROOT / "data"
OUTPUTS_DIR = REPO_ROOT / "outputs"
FIGURES_DIR = OUTPUTS_DIR / "figures"
TABLES_DIR = OUTPUTS_DIR / "tables"
REPORTS_DIR = OUTPUTS_DIR / "reports"
MANUSCRIPT_DIR = REPO_ROOT / "manuscript"

MERGED_COHORT = TUMOR_DIR / "Merged.xlsx"

GENES = [
    "TP53",
    "KRAS",
    "CDKN2A",
    "SMAD4",
    "ARID1A",
    "ATM",
    "PIK3CA",
    "BRAF",
    "GNAS",
    "RNF43",
]

STAGES = [
    "Metastatic",
    "Resectable",
    "Borderline Resectable/Locally Advanced",
]
