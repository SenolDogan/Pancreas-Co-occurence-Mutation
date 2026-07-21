# cBioPortal four-study validation summary
- Discovery: Tumor/Merged.xlsx (N=2330)
- Discovery TP53+KRAS Cox HR=1.27, p=0.000155
- Extended dual-pair Cox table: `Validation_cBioPortal_FivePairs_FourStudies.xlsx`

## paad_tcga_gdc
- Sequenced sample list: `paad_tcga_gdc_sequenced`
- Mutation profile: `paad_tcga_gdc_mutations`
- Patients with OS fields: 185
- Patients used in Cox (OS>0): 184
- TP53+KRAS prevalence: **43.5%** (discovery 71.6%)
- Univariate Cox TP53+KRAS vs others: HR **2.039** 95% CI [1.305, 3.186], p **0.00174** 
- KRAS%=57.3 TP53%=53.5 CDKN2A%=16.2 SMAD4%=19.5

| Dual pair | Prev% | HR | 95% CI | p |
|---|---:|---:|---|---:|
| TP53+KRAS | 43.5 | 2.039 | [1.305, 3.186] | 0.00174 |
| TP53+SMAD4 | 11.4 | 0.951 | [0.524, 1.726] | 0.869 |
| TP53+ARID1A | 1.6 | 1.816 | [0.412, 8.009] | 0.431 |
| KRAS+ARID1A | 2.7 | 1.194 | [0.353, 4.041] | 0.776 |
| TP53+CDKN2A | 14.1 | 1.017 | [0.565, 1.830] | 0.955 |

## paad_tcga_pan_can_atlas_2018
- Sequenced sample list: `paad_tcga_pan_can_atlas_2018_sequenced`
- Mutation profile: `paad_tcga_pan_can_atlas_2018_mutations`
- Patients with OS fields: 184
- Patients used in Cox (OS>0): 183
- TP53+KRAS prevalence: **49.2%** (discovery 71.6%)
- Univariate Cox TP53+KRAS vs others: HR **2.197** 95% CI [1.382, 3.493], p **0.000871** 
- KRAS%=63.6 TP53%=58.2 CDKN2A%=19.0 SMAD4%=20.1

| Dual pair | Prev% | HR | 95% CI | p |
|---|---:|---:|---|---:|
| TP53+KRAS | 49.2 | 2.197 | [1.382, 3.493] | 0.000871 |
| TP53+SMAD4 | 12.6 | 0.974 | [0.549, 1.729] | 0.929 |
| TP53+ARID1A | 1.6 | 1.744 | [0.394, 7.728] | 0.464 |
| KRAS+ARID1A | 3.3 | 1.422 | [0.488, 4.146] | 0.519 |
| TP53+CDKN2A | 16.9 | 0.853 | [0.493, 1.476] | 0.571 |

## pancreas_cptac_gdc
- Sequenced sample list: `pancreas_cptac_gdc_sequenced`
- Mutation profile: `pancreas_cptac_gdc_mutations`
- Patients with OS fields: 161
- Patients used in Cox (OS>0): 129
- TP53+KRAS prevalence: **63.6%** (discovery 71.6%)
- Univariate Cox TP53+KRAS vs others: HR **1.357** 95% CI [0.912, 2.019], p **0.133** 
- KRAS%=83.9 TP53%=70.2 CDKN2A%=21.1 SMAD4%=17.4

| Dual pair | Prev% | HR | 95% CI | p |
|---|---:|---:|---|---:|
| TP53+KRAS | 63.6 | 1.357 | [0.912, 2.019] | 0.133 |
| TP53+SMAD4 | 11.6 | 0.686 | [0.365, 1.290] | 0.242 |
| TP53+ARID1A | 1.6 | 0.985 | [0.124, 7.844] | 0.988 |
| KRAS+ARID1A | 3.1 | 0.698 | [0.168, 2.895] | 0.621 |
| TP53+CDKN2A | 17.1 | 1.321 | [0.781, 2.233] | 0.299 |

## pdac_msk_2024
- Sequenced sample list: `pdac_msk_2024_sequenced`
- Mutation profile: `pdac_msk_2024_mutations`
- Patients with OS fields: 2270
- Patients used in Cox (OS>0): 2260
- TP53+KRAS prevalence: **73.2%** (discovery 71.6%)
- Univariate Cox TP53+KRAS vs others: HR **1.278** 95% CI [1.127, 1.449], p **0.000133** 
- KRAS%=93.6 TP53%=76.2 CDKN2A%=23.3 SMAD4%=21.9

| Dual pair | Prev% | HR | 95% CI | p |
|---|---:|---:|---|---:|
| TP53+KRAS | 73.2 | 1.278 | [1.127, 1.449] | 0.000133 |
| TP53+SMAD4 | 16.8 | 1.060 | [0.926, 1.213] | 0.401 |
| TP53+ARID1A | 6.2 | 1.545 | [1.037, 2.302] | 0.0324 |
| KRAS+ARID1A | 7.8 | 0.939 | [0.654, 1.348] | 0.733 |
| TP53+CDKN2A | 21.0 | 1.115 | [0.981, 1.268] | 0.096 |

