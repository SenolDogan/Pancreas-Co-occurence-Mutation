# Supplementary Reference Audit Report

**Manuscript:** `NewManuscript.docx`  
**Date:** 2026-05-15  
**Status:** ✓ Passed (structural + semantic checks)

## Numbering scheme

| Section | Range | End list order |
|---------|-------|----------------|
| Supplementary Methods | 1–9 | Sequential 1→9 under **Supplementary Methods** heading |
| Supplementary Figures | 1–12 | Sequential 1→12 under **Supplementary Figures** heading |
| Supplementary Tables | 1–11 | Sequential 1→11 under **Supplementary Tables** heading |

Each type restarts at 1. Numbers in the manuscript body match the end **Supplementary Materials** list and the separate files (`supplementary/Supplementary Methods.docx`, `Supplementary Figures.docx`, `Supplementary Tables.xlsx`).

## Coverage (manuscript body)

| Type | Cited in text | End list | Match |
|------|---------------|----------|-------|
| Methods | 1–9 (all) | 1–9 | ✓ |
| Figures | 1–12 (all) | 1–12 | ✓ |
| Tables | 1–11 (all) | 1–11 | ✓ |

## Semantic placement (key anchors)

| Location | Expected | Verified |
|----------|----------|----------|
| Statistical Analysis | Method 1 | ✓ |
| Master cohort (N=2330) | Method 2; Tables 3, 7, 11 | ✓ |
| Internal validation | Method 6; Figure 9; Table 9 | ✓ |
| cBioPortal external validation | Method 7; Table 2 | ✓ |
| Functional mapping | Method 8; Figure 10; Figures 5–6 | ✓ |
| Software / packages | Method 9; Tables 1–10 | ✓ |
| DX2COLLECTION timing | Method 5; Tables 1, 5; Figures 3–4, 7 | ✓ |
| Stage Cox (Figure 3) | Method 4; Table 6; Figure 12 | ✓ |
| Table 1 (timing highlights) | Table 1 | ✓ |
| Figure 1 (dead vs alive) | Figure 11; Table 11 | ✓ |
| Dual-combination screen | Table 10 | ✓ |
| Triple combinations | Tables 3, 8 | ✓ |
| Pairwise summary (Figure 6 text) | Figures 1–2; Figures 3–4, 7 | ✓ |
| Abstract external replication | Method 7; Table 2 | ✓ (after fix) |

## End list ↔ supplementary files

- **Methods.docx:** Headings `Supplementary Method 1` … `9` match end list titles.
- **Figures.docx:** `Supplementary Figure 1` … `12` in order.
- **Tables.xlsx:** `Table_Index` rows `Supplementary Table 1` … `11` with legacy sheets `S1_` … `S11_`.

## Re-run audit

```bash
cd Tumor
python3 audit_supplementary_references.py
python3 fix_manuscript_supplementary_citations.py   # repair citations if needed
```

Exit code `0` = no structural errors.
