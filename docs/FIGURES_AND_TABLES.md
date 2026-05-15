# Main figures and tables — script mapping

## Main manuscript figures (NewManuscript.docx)

| Figure | Content | Primary script | Output file(s) |
|--------|---------|----------------|----------------|
| 1 | Deceased vs living enrichment | `analysis/dead_alive_comprehensive_analysis.py` | `01_Dead_Alive_Comprehensive_Analysis.png` |
| 2 | Three-group stage landscape | `analysis/stage_3group_comprehensive_analysis.py` | `analysis/tumor/Stage_3Group_Comprehensive_Analysis.png` |
| 3 | Stage-stratified Cox (A–B) | `analysis/tumor/stage_multivariable_cox_validation.py` | `Stage_Figure2_AB_ForestPlots_VSTACK.png` |
| 4 | OS / timing framework | `analysis/os_months_methodology_analysis.py` | `Stage_06_OS_Months_Methodology_Analysis.png` |
| 5 | TP53+KRAS(+X) by stage | `analysis/tp53_kras_detailed_analysis.py` | `Stage_05_TP53_KRAS_Detailed_Analysis.png` |
| 6 | TP53/KRAS-focused panels | `analysis/tp53_kras_focused_analysis.py` | `Stage_02_TP53_KRAS_Focused_Analysis.png` |
| 7 | Pairwise additive + Cox pairs | `analysis/tumor/compose_stage_manuscript_figures.py` | `Stage_Figure6_AB_AdditiveBars_CoxPairsForest.png` |

Embed figures into Word: `analysis/tumor/restore_manuscript_figures.py` (run from `analysis/tumor/` with `NewManuscript.docx` in `manuscript/`).

## Main tables

| Table | Content | Source |
|-------|---------|--------|
| 1 | Timing-interaction highlights | `build_dx_interaction_sensitivity_comparison_table.py` |
| 2 | Single-gene frequencies / lethality ratios | `dead_alive_comprehensive_analysis.py` |
| 3 | FDR-significant dual combinations | `stage_generate_14_plots.py` / synergy screen |
| 4 | Top synergistic dual pairs | `dead_alive_comprehensive_analysis.py` |
| 5 | Triple lethality / protective scores | `dead_alive_comprehensive_analysis.py` |

## Supplementary package

| Item | Script |
|------|--------|
| Supplementary Methods / Figures / Tables Word + Excel | `analysis/tumor/build_supplementary_materials.py` |
| Supplementary numbering audit | `analysis/tumor/audit_supplementary_references.py` |

## Full stage figure suite (14 panels)

`analysis/tumor/stage_generate_14_plots.py` writes `Stage_01_…` through `Stage_14_…` PNGs used in supplementary material and sensitivity sections.
