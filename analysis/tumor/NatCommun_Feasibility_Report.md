# Nat Commun feasibility analysis report
Generated from `Merged.xlsx` and Tumor outputs.

## 1. Discovery cohort summary

- Patients (3 stage groups, OS>0): **2254**
- With DX2COLLECTION_YEAR: **2264**
- With SYSTEMIC_TX recorded: **1478** (63.4%)
- TP53+KRAS prevalence: **71.6%**

## 2. Kaplan–Meier + log-rank (discovery)

- **TP53+KRAS**: N+=1613, N−=641, log-rank p=1.945e-07, median OS +/− = 12.7 / 16.4 mo (`KM_TP53_KRAS_all_stages.png`)
- **TP53+KRAS / Metastatic**: N+=754, N−=252, log-rank p=0.0003145, median OS +/− = 9.1 / 12.3 mo (`KM_TP53_KRAS_Metastatic.png`)
- **TP53+KRAS+SMAD4 / Metastatic**: N+=150, N−=856, log-rank p=0.1472, median OS +/− = 8.2 / 9.7 mo (`KM_TP53_KRAS_SMAD4_Metastatic.png`)

### Combined panels for Supplementary Figure 14 (`KM_TP53_KRAS_SuppFigure14_AB.png`)

- Panel **(A)**: log-rank p=1.945e-07 (raw 1.945e-07), N+=1613, N−=641
- Panel **(B)**: log-rank p=3.145e-04 (raw 0.0003145), N+=754, N−=252

## 3. Discovery univariate Cox (OS>0)

- TP53+KRAS (all): HR=1.35 [1.21–1.51], p=2.15e-07, n=2254
- TP53+KRAS (all) + AGE + SYSTEMIC_TX (complete-case n=1408): HR=1.33 [1.16–1.53], p=4.06e-05
- TP53+KRAS (Metastatic): HR=1.35 [1.15–1.59], p=0.000329, n=1006
- TP53+KRAS (Metastatic) + AGE + SYSTEMIC_TX (complete-case n=600): HR=1.31 [1.06–1.60], p=0.0106
- TP53+SMAD4 (all): HR=1.18 [1.03–1.35], p=0.0186, n=2254
- TP53+SMAD4 (all) + AGE + SYSTEMIC_TX (complete-case n=1408): HR=1.14 [0.97–1.35], p=0.12
- TP53+SMAD4 (Metastatic): HR=1.15 [0.95–1.39], p=0.157, n=1006
- TP53+SMAD4 (Metastatic) + AGE + SYSTEMIC_TX (complete-case n=600): HR=0.98 [0.77–1.26], p=0.887
- TP53+ARID1A (all): HR=1.55 [1.27–1.90], p=1.43e-05, n=2254
- TP53+ARID1A (all) + AGE + SYSTEMIC_TX (complete-case n=1408): HR=1.37 [1.06–1.76], p=0.0163
- TP53+ARID1A (Metastatic): HR=1.63 [1.25–2.12], p=0.000343, n=1006
- TP53+ARID1A (Metastatic) + AGE + SYSTEMIC_TX (complete-case n=600): HR=1.42 [0.99–2.03], p=0.0575
- KRAS+ARID1A (all): HR=1.29 [1.08–1.55], p=0.00559, n=2254
- KRAS+ARID1A (all) + AGE + SYSTEMIC_TX (complete-case n=1408): HR=1.12 [0.89–1.41], p=0.319
- KRAS+ARID1A (Metastatic): HR=1.35 [1.06–1.72], p=0.015, n=1006
- KRAS+ARID1A (Metastatic) + AGE + SYSTEMIC_TX (complete-case n=600): HR=1.28 [0.93–1.74], p=0.125
- TP53+CDKN2A (all): HR=1.23 [1.08–1.39], p=0.00166, n=2254
- TP53+CDKN2A (all) + AGE + SYSTEMIC_TX (complete-case n=1408): HR=1.23 [1.05–1.44], p=0.0109
- TP53+CDKN2A (Metastatic): HR=1.24 [1.05–1.48], p=0.0129, n=1006
- TP53+CDKN2A (Metastatic) + AGE + SYSTEMIC_TX (complete-case n=600): HR=1.29 [1.03–1.62], p=0.0281

## 4. Internal validation (C-index, existing output)

                                 Stage  n_patients  events  covariates  cindex_mean  cindex_std  splits_used  sig_TP53_ARID1A_poscoef_frac  sig_TP53_KRAS_ARID1A_poscoef_frac  sig_TP53_KRAS_SMAD4_poscoef_frac  sig_KRAS_SMAD4_poscoef_frac  TP53_poscoef_frac  SMAD4_poscoef_frac  ARID1A_poscoef_frac
                            Metastatic        1006     783          20     0.565180    0.015631           50                          1.00                               1.00                              0.92                         0.02               1.00                0.04                 0.94
                            Resectable         679     353          20     0.583708    0.027870           50                          1.00                               1.00                              0.94                         0.22               1.00                0.14                 0.56
Borderline Resectable/Locally Advanced         569     381          20     0.575201    0.022694           50                          0.64                               0.64                              1.00                         0.96               0.16                0.82                 0.82

## 5. Top timing-interaction hits (discovery)

     Stage     Feature
Metastatic   TP53+KRAS
Metastatic TP53+CDKN2A
Metastatic  TP53+SMAD4
Metastatic TP53+ARID1A
Metastatic TP53+PIK3CA
Metastatic  TP53+RNF43
Metastatic KRAS+CDKN2A
Metastatic  KRAS+SMAD4
Metastatic KRAS+ARID1A
Metastatic    KRAS+ATM

## 6. External validation — MSK (pdac_msk_2024), univariate Cox

- **TP53+KRAS**: <urlopen error [Errno 1] Operation not permitted>
- **TP53+SMAD4**: <urlopen error Tunnel connection failed: 403 Forbidden>
- **TP53+ARID1A**: <urlopen error Tunnel connection failed: 403 Forbidden>

## 7. Feasibility verdict (Nat Commun boosts)

| Analysis | Status | Notes |
|----------|--------|-------|
| KM + log-rank | Done | PNGs in Tumor/ |
| Discovery Cox by stage | Done | Table above |
| Treatment sensitivity | Partial | SYSTEMIC_TX subset only |
| C-index internal validation | From existing file | Already in pipeline |
| MSK external multi-combo | Partial (top 3 pairs) | Full 5 + 4 cohorts: extend script |
| Timing external replication | Not feasible | No dx_yr in cBioPortal |
| MR / functional RNA | Not feasible | No data |

