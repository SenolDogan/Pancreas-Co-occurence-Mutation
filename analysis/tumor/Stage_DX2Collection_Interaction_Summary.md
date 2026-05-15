# DX2COLLECTION_YEAR × combo interaction with OS (stage-stratified)

- Unadjusted model: Cox(OS_MONTHS ~ dx_yr + combo + dx_yr×combo)
- Adjusted model:   Cox(OS_MONTHS ~ dx_yr + combo + dx_yr×combo + AGE + SEX + DISEASE_STATUS) (when available)
- dx_yr: years from diagnosis to sample collection
- OS_MONTHS: months from collection to death/last follow-up (per clinical dictionary)

## Top pair interactions by stage (lowest adjusted p_int)

### Metastatic
- **TP53+KRAS**: beta_int_adj=0.190 (HR_int_adj=1.21), p_int_adj=0.00643, FDR_adj=0.0611 | beta_int_unadj=0.282 (HR_int_unadj=1.33), p_int_unadj=0.00225 | median dx (pos/neg)=0.00684/0.0205, median OS (pos/neg)=9.11/12.28
- **KRAS+SMAD4**: beta_int_adj=0.404 (HR_int_adj=1.50), p_int_adj=0.00814, FDR_adj=0.0611 | beta_int_unadj=0.636 (HR_int_unadj=1.89), p_int_unadj=0.000263 | median dx (pos/neg)=0.0205/0.0109, median OS (pos/neg)=9.63/9.42
- **TP53+ARID1A**: beta_int_adj=0.446 (HR_int_adj=1.56), p_int_adj=0.0592, FDR_adj=0.215 | beta_int_unadj=0.607 (HR_int_unadj=1.83), p_int_unadj=0.0168 | median dx (pos/neg)=0/0.0151, median OS (pos/neg)=5.51/9.83
- **KRAS+CDKN2A**: beta_int_adj=0.338 (HR_int_adj=1.40), p_int_adj=0.0619, FDR_adj=0.215 | beta_int_unadj=0.483 (HR_int_unadj=1.62), p_int_unadj=0.0172 | median dx (pos/neg)=0/0.0164, median OS (pos/neg)=7.45/9.99
- **CDKN2A+SMAD4**: beta_int_adj=0.607 (HR_int_adj=1.83), p_int_adj=0.0858, FDR_adj=0.215 | beta_int_unadj=0.898 (HR_int_unadj=2.45), p_int_unadj=0.0218 | median dx (pos/neg)=0.0164/0.0137, median OS (pos/neg)=7.13/9.53
- **TP53+CDKN2A**: beta_int_adj=0.301 (HR_int_adj=1.35), p_int_adj=0.0859, FDR_adj=0.215 | beta_int_unadj=0.426 (HR_int_unadj=1.53), p_int_unadj=0.0345 | median dx (pos/neg)=0/0.0164, median OS (pos/neg)=7.13/10.01
- **TP53+SMAD4**: beta_int_adj=0.173 (HR_int_adj=1.19), p_int_adj=0.178, FDR_adj=0.382 | beta_int_unadj=0.173 (HR_int_unadj=1.19), p_int_unadj=0.23 | median dx (pos/neg)=0.0164/0.0137, median OS (pos/neg)=8.45/9.73
- **KRAS+ARID1A**: beta_int_adj=0.254 (HR_int_adj=1.29), p_int_adj=0.231, FDR_adj=0.405 | beta_int_unadj=0.329 (HR_int_unadj=1.39), p_int_unadj=0.189 | median dx (pos/neg)=0.0192/0.0109, median OS (pos/neg)=6.34/9.80

### Resectable
- **KRAS+SMAD4**: beta_int_adj=-0.062 (HR_int_adj=0.94), p_int_adj=0.251, FDR_adj=0.836 | beta_int_unadj=-0.085 (HR_int_unadj=0.92), p_int_unadj=0.253 | median dx (pos/neg)=0.0534/0.0602, median OS (pos/neg)=21.83/21.17
- **KRAS+RNF43**: beta_int_adj=-0.133 (HR_int_adj=0.88), p_int_adj=0.349, FDR_adj=0.836 | beta_int_unadj=-0.175 (HR_int_unadj=0.84), p_int_unadj=0.388 | median dx (pos/neg)=0.00547/0.0575, median OS (pos/neg)=21.70/21.24
- **KRAS+GNAS**: beta_int_adj=-0.091 (HR_int_adj=0.91), p_int_adj=0.424, FDR_adj=0.836 | beta_int_unadj=-0.136 (HR_int_unadj=0.87), p_int_unadj=0.407 | median dx (pos/neg)=0.0561/0.0575, median OS (pos/neg)=26.81/21.17
- **TP53+CDKN2A**: beta_int_adj=0.046 (HR_int_adj=1.05), p_int_adj=0.438, FDR_adj=0.836 | beta_int_unadj=0.068 (HR_int_unadj=1.07), p_int_unadj=0.325 | median dx (pos/neg)=0.0493/0.0575, median OS (pos/neg)=21.32/21.30
- **TP53+KRAS**: beta_int_adj=0.019 (HR_int_adj=1.02), p_int_adj=0.452, FDR_adj=0.836 | beta_int_unadj=0.047 (HR_int_unadj=1.05), p_int_unadj=0.263 | median dx (pos/neg)=0.0575/0.0575, median OS (pos/neg)=20.51/23.27
- **KRAS+CDKN2A**: beta_int_adj=0.039 (HR_int_adj=1.04), p_int_adj=0.499, FDR_adj=0.836 | beta_int_unadj=0.067 (HR_int_unadj=1.07), p_int_unadj=0.325 | median dx (pos/neg)=0.0438/0.0588, median OS (pos/neg)=21.96/20.92
- **TP53+ARID1A**: beta_int_adj=0.033 (HR_int_adj=1.03), p_int_adj=0.532, FDR_adj=0.836 | beta_int_unadj=0.017 (HR_int_unadj=1.02), p_int_unadj=0.793 | median dx (pos/neg)=0.0616/0.0575, median OS (pos/neg)=14.51/21.56
- **TP53+SMAD4**: beta_int_adj=0.024 (HR_int_adj=1.02), p_int_adj=0.725, FDR_adj=0.966 | beta_int_unadj=0.054 (HR_int_unadj=1.06), p_int_unadj=0.529 | median dx (pos/neg)=0.0493/0.0602, median OS (pos/neg)=20.64/21.40

### Borderline Resectable/Locally Advanced
- **KRAS+ARID1A**: beta_int_adj=-0.270 (HR_int_adj=0.76), p_int_adj=0.0566, FDR_adj=0.403 | beta_int_unadj=-0.440 (HR_int_unadj=0.64), p_int_unadj=0.029 | median dx (pos/neg)=0.0192/0.0862, median OS (pos/neg)=14.00/15.17
- **TP53+ARID1A**: beta_int_adj=-0.267 (HR_int_adj=0.77), p_int_adj=0.0806, FDR_adj=0.403 | beta_int_unadj=-0.415 (HR_int_unadj=0.66), p_int_unadj=0.0534 | median dx (pos/neg)=0.0109/0.0876, median OS (pos/neg)=14.50/14.92
- **KRAS+SMAD4**: beta_int_adj=0.032 (HR_int_adj=1.03), p_int_adj=0.386, FDR_adj=0.936 | beta_int_unadj=0.076 (HR_int_unadj=1.08), p_int_unadj=0.224 | median dx (pos/neg)=0.0534/0.093, median OS (pos/neg)=13.64/15.19
- **TP53+SMAD4**: beta_int_adj=0.030 (HR_int_adj=1.03), p_int_adj=0.445, FDR_adj=0.936 | beta_int_unadj=0.083 (HR_int_unadj=1.09), p_int_unadj=0.237 | median dx (pos/neg)=0.0848/0.0753, median OS (pos/neg)=13.61/15.07
- **TP53+KRAS**: beta_int_adj=0.017 (HR_int_adj=1.02), p_int_adj=0.573, FDR_adj=0.936 | beta_int_unadj=0.030 (HR_int_unadj=1.03), p_int_unadj=0.576 | median dx (pos/neg)=0.0807/0.0712, median OS (pos/neg)=13.94/16.54
- **KRAS+RNF43**: beta_int_adj=0.015 (HR_int_adj=1.02), p_int_adj=0.732, FDR_adj=0.936 | beta_int_unadj=0.071 (HR_int_unadj=1.07), p_int_unadj=0.456 | median dx (pos/neg)=0.23/0.0739, median OS (pos/neg)=13.10/15.15
- **TP53+RNF43**: beta_int_adj=0.015 (HR_int_adj=1.01), p_int_adj=0.74, FDR_adj=0.936 | beta_int_unadj=0.070 (HR_int_unadj=1.07), p_int_unadj=0.477 | median dx (pos/neg)=0.285/0.0725, median OS (pos/neg)=13.05/14.94
- **CDKN2A+SMAD4**: beta_int_adj=-0.035 (HR_int_adj=0.97), p_int_adj=0.749, FDR_adj=0.936 | beta_int_unadj=-0.083 (HR_int_unadj=0.92), p_int_unadj=0.571 | median dx (pos/neg)=0.0753/0.0766, median OS (pos/neg)=16.96/14.73

## Top triple interactions by stage (lowest adjusted p_int)

### Metastatic
- **TP53+KRAS+SMAD4**: beta_int_adj=0.489 (HR_int_adj=1.63), p_int_adj=0.00337, FDR_adj=0.027 | beta_int_unadj=0.724 (HR_int_unadj=2.06), p_int_unadj=6.87e-05 | median dx (pos/neg)=0.0109/0.0137, median OS (pos/neg)=8.20/9.75
- **TP53+KRAS+CDKN2A**: beta_int_adj=0.348 (HR_int_adj=1.42), p_int_adj=0.0531, FDR_adj=0.144 | beta_int_unadj=0.495 (HR_int_unadj=1.64), p_int_unadj=0.0131 | median dx (pos/neg)=0/0.0164, median OS (pos/neg)=7.13/9.99
- **TP53+KRAS+ARID1A**: beta_int_adj=0.454 (HR_int_adj=1.57), p_int_adj=0.0538, FDR_adj=0.144 | beta_int_unadj=0.617 (HR_int_unadj=1.85), p_int_unadj=0.0142 | median dx (pos/neg)=0/0.0137, median OS (pos/neg)=5.42/9.83
- **KRAS+CDKN2A+SMAD4**: beta_int_adj=0.609 (HR_int_adj=1.84), p_int_adj=0.0853, FDR_adj=0.149 | beta_int_unadj=0.903 (HR_int_unadj=2.47), p_int_unadj=0.0211 | median dx (pos/neg)=0.0164/0.0137, median OS (pos/neg)=7.13/9.53
- **TP53+CDKN2A+SMAD4**: beta_int_adj=0.598 (HR_int_adj=1.82), p_int_adj=0.0931, FDR_adj=0.149 | beta_int_unadj=0.885 (HR_int_unadj=2.42), p_int_unadj=0.0256 | median dx (pos/neg)=0.00274/0.0137, median OS (pos/neg)=6.95/9.55
- **KRAS+SMAD4+ARID1A**: beta_int_adj=0.279 (HR_int_adj=1.32), p_int_adj=0.255, FDR_adj=0.341 | beta_int_unadj=0.473 (HR_int_unadj=1.60), p_int_unadj=0.114 | median dx (pos/neg)=0.0383/0.0109, median OS (pos/neg)=10.31/9.42
- **TP53+KRAS+RNF43**: beta_int_adj=0.048 (HR_int_adj=1.05), p_int_adj=0.768, FDR_adj=0.878 | beta_int_unadj=0.059 (HR_int_unadj=1.06), p_int_unadj=0.755 | median dx (pos/neg)=0.00958/0.0137, median OS (pos/neg)=9.96/9.43
- **TP53+KRAS+PIK3CA**: beta_int_adj=0.076 (HR_int_adj=1.08), p_int_adj=0.898, FDR_adj=0.898 | beta_int_unadj=0.103 (HR_int_unadj=1.11), p_int_unadj=0.897 | median dx (pos/neg)=0/0.0151, median OS (pos/neg)=9.48/9.43

### Resectable
- **TP53+CDKN2A+SMAD4**: beta_int_adj=0.200 (HR_int_adj=1.22), p_int_adj=0.366, FDR_adj=0.941 | beta_int_unadj=0.489 (HR_int_unadj=1.63), p_int_unadj=0.079 | median dx (pos/neg)=0.00547/0.0602, median OS (pos/neg)=21.50/21.30
- **TP53+KRAS+CDKN2A**: beta_int_adj=0.047 (HR_int_adj=1.05), p_int_adj=0.425, FDR_adj=0.941 | beta_int_unadj=0.072 (HR_int_unadj=1.07), p_int_unadj=0.297 | median dx (pos/neg)=0.0547/0.0575, median OS (pos/neg)=21.70/21.15
- **TP53+KRAS+ARID1A**: beta_int_adj=0.032 (HR_int_adj=1.03), p_int_adj=0.545, FDR_adj=0.941 | beta_int_unadj=0.015 (HR_int_unadj=1.01), p_int_unadj=0.822 | median dx (pos/neg)=0.0629/0.0575, median OS (pos/neg)=14.46/21.53
- **TP53+KRAS+SMAD4**: beta_int_adj=0.027 (HR_int_adj=1.03), p_int_adj=0.692, FDR_adj=0.941 | beta_int_unadj=0.060 (HR_int_unadj=1.06), p_int_unadj=0.482 | median dx (pos/neg)=0.0465/0.0602, median OS (pos/neg)=20.61/21.48
- **TP53+KRAS+RNF43**: beta_int_adj=0.121 (HR_int_adj=1.13), p_int_adj=0.796, FDR_adj=0.941 | beta_int_unadj=0.379 (HR_int_unadj=1.46), p_int_unadj=0.634 | median dx (pos/neg)=0.026/0.0575, median OS (pos/neg)=20.78/21.30
- **KRAS+CDKN2A+SMAD4**: beta_int_adj=0.010 (HR_int_adj=1.01), p_int_adj=0.941, FDR_adj=0.941 | beta_int_unadj=0.031 (HR_int_unadj=1.03), p_int_unadj=0.856 | median dx (pos/neg)=0.00547/0.0588, median OS (pos/neg)=21.70/21.24

### Borderline Resectable/Locally Advanced
- **TP53+KRAS+ARID1A**: beta_int_adj=-0.267 (HR_int_adj=0.77), p_int_adj=0.0806, FDR_adj=0.483 | beta_int_unadj=-0.415 (HR_int_unadj=0.66), p_int_unadj=0.0534 | median dx (pos/neg)=0.0109/0.0876, median OS (pos/neg)=14.50/14.92
- **TP53+KRAS+SMAD4**: beta_int_adj=0.029 (HR_int_adj=1.03), p_int_adj=0.464, FDR_adj=0.924 | beta_int_unadj=0.076 (HR_int_unadj=1.08), p_int_unadj=0.276 | median dx (pos/neg)=0.0862/0.0739, median OS (pos/neg)=13.43/15.29
- **TP53+KRAS+RNF43**: beta_int_adj=0.014 (HR_int_adj=1.01), p_int_adj=0.747, FDR_adj=0.924 | beta_int_unadj=0.068 (HR_int_unadj=1.07), p_int_unadj=0.485 | median dx (pos/neg)=0.264/0.0739, median OS (pos/neg)=13.18/14.92
- **KRAS+CDKN2A+SMAD4**: beta_int_adj=-0.035 (HR_int_adj=0.97), p_int_adj=0.749, FDR_adj=0.924 | beta_int_unadj=-0.083 (HR_int_unadj=0.92), p_int_unadj=0.571 | median dx (pos/neg)=0.0753/0.0766, median OS (pos/neg)=16.96/14.73
- **TP53+CDKN2A+SMAD4**: beta_int_adj=-0.032 (HR_int_adj=0.97), p_int_adj=0.77, FDR_adj=0.924 | beta_int_unadj=-0.073 (HR_int_unadj=0.93), p_int_unadj=0.62 | median dx (pos/neg)=0.0848/0.0753, median OS (pos/neg)=16.93/14.81
- **TP53+KRAS+CDKN2A**: beta_int_adj=0.006 (HR_int_adj=1.01), p_int_adj=0.953, FDR_adj=0.953 | beta_int_unadj=-0.028 (HR_int_unadj=0.97), p_int_unadj=0.824 | median dx (pos/neg)=0.0602/0.104, median OS (pos/neg)=13.61/14.92

