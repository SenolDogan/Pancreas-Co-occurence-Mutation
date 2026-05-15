# Data

## Primary cohort (`Merged.xlsx`)

The integrated discovery cohort (N≈2,330 patients) is stored as:

- `data/Merged.xlsx` (canonical copy)
- `analysis/tumor/Merged.xlsx` (used by analysis scripts)

Columns include binary mutation calls for ten prespecified genes, clinical stage (three groups), overall survival, and `DX2COLLECTION_YEAR` for timing-interaction models.

## Rebuilding from raw TCGA-style files

If you have separate `Clinical.txt` and `Mutation.txt` exports, run from the repository root:

```bash
# Place Clinical.txt and Mutation.txt in data/raw/ then:
python analysis/merge_clinical_mutation_data.py   # if added to repo
```

The merge script in the parent project is `merge_clinical_mutation_data.py` (copy to `analysis/` if needed).

## External validation (cBioPortal)

No local download is required for step 11 of `run_pipeline.py`; cohorts are fetched via the [cBioPortal public API](https://www.cbioportal.org/api).
