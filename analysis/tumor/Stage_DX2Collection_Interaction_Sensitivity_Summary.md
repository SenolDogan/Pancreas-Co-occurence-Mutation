# DX2COLLECTION_YEAR × combo interaction — sensitivity analysis

Filters:
- ALL: no dx filter
- DX_GE_0: exclude dx<0
- DX_0_TO_5: exclude dx<0 and dx>5 years

Model (adjusted primary): Cox(OS_MONTHS ~ dx_yr + combo + dx_yr×combo + AGE + SEX + DISEASE_STATUS)

## ALL
### Top pair interactions (by adjusted p_int)

**Metastatic**
- TP53+KRAS: HR_int_adj=1.21, p_int_adj=0.00643, FDR_adj=0.0611 (unadj p=0.00225)
- KRAS+SMAD4: HR_int_adj=1.50, p_int_adj=0.00814, FDR_adj=0.0611 (unadj p=0.000263)
- TP53+ARID1A: HR_int_adj=1.56, p_int_adj=0.0592, FDR_adj=0.215 (unadj p=0.0168)
- KRAS+CDKN2A: HR_int_adj=1.40, p_int_adj=0.0619, FDR_adj=0.215 (unadj p=0.0172)
- CDKN2A+SMAD4: HR_int_adj=1.83, p_int_adj=0.0858, FDR_adj=0.215 (unadj p=0.0218)

**Resectable**
- KRAS+SMAD4: HR_int_adj=0.94, p_int_adj=0.251, FDR_adj=0.836 (unadj p=0.253)
- KRAS+RNF43: HR_int_adj=0.88, p_int_adj=0.349, FDR_adj=0.836 (unadj p=0.388)
- KRAS+GNAS: HR_int_adj=0.91, p_int_adj=0.424, FDR_adj=0.836 (unadj p=0.407)
- TP53+CDKN2A: HR_int_adj=1.05, p_int_adj=0.438, FDR_adj=0.836 (unadj p=0.325)
- TP53+KRAS: HR_int_adj=1.02, p_int_adj=0.452, FDR_adj=0.836 (unadj p=0.263)

**Borderline Resectable/Locally Advanced**
- KRAS+ARID1A: HR_int_adj=0.76, p_int_adj=0.0566, FDR_adj=0.403 (unadj p=0.029)
- TP53+ARID1A: HR_int_adj=0.77, p_int_adj=0.0806, FDR_adj=0.403 (unadj p=0.0534)
- KRAS+SMAD4: HR_int_adj=1.03, p_int_adj=0.386, FDR_adj=0.936 (unadj p=0.224)
- TP53+SMAD4: HR_int_adj=1.03, p_int_adj=0.445, FDR_adj=0.936 (unadj p=0.237)
- TP53+KRAS: HR_int_adj=1.02, p_int_adj=0.573, FDR_adj=0.936 (unadj p=0.576)

### Top triple interactions (by adjusted p_int)

**Metastatic**
- TP53+KRAS+SMAD4: HR_int_adj=1.63, p_int_adj=0.00337, FDR_adj=0.027 (unadj p=6.87e-05)
- TP53+KRAS+CDKN2A: HR_int_adj=1.42, p_int_adj=0.0531, FDR_adj=0.144 (unadj p=0.0131)
- TP53+KRAS+ARID1A: HR_int_adj=1.57, p_int_adj=0.0538, FDR_adj=0.144 (unadj p=0.0142)
- KRAS+CDKN2A+SMAD4: HR_int_adj=1.84, p_int_adj=0.0853, FDR_adj=0.149 (unadj p=0.0211)
- TP53+CDKN2A+SMAD4: HR_int_adj=1.82, p_int_adj=0.0931, FDR_adj=0.149 (unadj p=0.0256)

**Resectable**
- TP53+CDKN2A+SMAD4: HR_int_adj=1.22, p_int_adj=0.366, FDR_adj=0.941 (unadj p=0.079)
- TP53+KRAS+CDKN2A: HR_int_adj=1.05, p_int_adj=0.425, FDR_adj=0.941 (unadj p=0.297)
- TP53+KRAS+ARID1A: HR_int_adj=1.03, p_int_adj=0.545, FDR_adj=0.941 (unadj p=0.822)
- TP53+KRAS+SMAD4: HR_int_adj=1.03, p_int_adj=0.692, FDR_adj=0.941 (unadj p=0.482)
- TP53+KRAS+RNF43: HR_int_adj=1.13, p_int_adj=0.796, FDR_adj=0.941 (unadj p=0.634)

**Borderline Resectable/Locally Advanced**
- TP53+KRAS+ARID1A: HR_int_adj=0.77, p_int_adj=0.0806, FDR_adj=0.483 (unadj p=0.0534)
- TP53+KRAS+SMAD4: HR_int_adj=1.03, p_int_adj=0.464, FDR_adj=0.924 (unadj p=0.276)
- TP53+KRAS+RNF43: HR_int_adj=1.01, p_int_adj=0.747, FDR_adj=0.924 (unadj p=0.485)
- KRAS+CDKN2A+SMAD4: HR_int_adj=0.97, p_int_adj=0.749, FDR_adj=0.924 (unadj p=0.571)
- TP53+CDKN2A+SMAD4: HR_int_adj=0.97, p_int_adj=0.77, FDR_adj=0.924 (unadj p=0.62)


## DX_GE_0
### Top pair interactions (by adjusted p_int)

**Metastatic**
- KRAS+SMAD4: HR_int_adj=1.50, p_int_adj=0.00814, FDR_adj=0.0652 (unadj p=0.000256)
- TP53+KRAS: HR_int_adj=1.20, p_int_adj=0.00869, FDR_adj=0.0652 (unadj p=0.00333)
- TP53+ARID1A: HR_int_adj=1.56, p_int_adj=0.0586, FDR_adj=0.215 (unadj p=0.0164)
- KRAS+CDKN2A: HR_int_adj=1.40, p_int_adj=0.0616, FDR_adj=0.215 (unadj p=0.0169)
- TP53+CDKN2A: HR_int_adj=1.35, p_int_adj=0.0855, FDR_adj=0.215 (unadj p=0.0341)

**Resectable**
- KRAS+SMAD4: HR_int_adj=0.94, p_int_adj=0.23, FDR_adj=0.832 (unadj p=0.213)
- KRAS+RNF43: HR_int_adj=0.87, p_int_adj=0.347, FDR_adj=0.832 (unadj p=0.387)
- KRAS+GNAS: HR_int_adj=0.91, p_int_adj=0.424, FDR_adj=0.832 (unadj p=0.405)
- TP53+CDKN2A: HR_int_adj=1.05, p_int_adj=0.444, FDR_adj=0.832 (unadj p=0.34)
- TP53+KRAS: HR_int_adj=1.02, p_int_adj=0.456, FDR_adj=0.832 (unadj p=0.273)

**Borderline Resectable/Locally Advanced**
- KRAS+ARID1A: HR_int_adj=0.76, p_int_adj=0.0627, FDR_adj=0.4 (unadj p=0.0374)
- TP53+ARID1A: HR_int_adj=0.77, p_int_adj=0.0799, FDR_adj=0.4 (unadj p=0.0536)
- KRAS+SMAD4: HR_int_adj=1.03, p_int_adj=0.377, FDR_adj=0.935 (unadj p=0.199)
- TP53+SMAD4: HR_int_adj=1.03, p_int_adj=0.446, FDR_adj=0.935 (unadj p=0.232)
- TP53+KRAS: HR_int_adj=1.02, p_int_adj=0.601, FDR_adj=0.935 (unadj p=0.616)

### Top triple interactions (by adjusted p_int)

**Metastatic**
- TP53+KRAS+SMAD4: HR_int_adj=1.63, p_int_adj=0.00343, FDR_adj=0.0275 (unadj p=7.1e-05)
- TP53+KRAS+CDKN2A: HR_int_adj=1.42, p_int_adj=0.0528, FDR_adj=0.142 (unadj p=0.013)
- TP53+KRAS+ARID1A: HR_int_adj=1.58, p_int_adj=0.0533, FDR_adj=0.142 (unadj p=0.0139)
- KRAS+CDKN2A+SMAD4: HR_int_adj=1.84, p_int_adj=0.0854, FDR_adj=0.149 (unadj p=0.021)
- TP53+CDKN2A+SMAD4: HR_int_adj=1.82, p_int_adj=0.0931, FDR_adj=0.149 (unadj p=0.0254)

**Resectable**
- TP53+CDKN2A+SMAD4: HR_int_adj=1.22, p_int_adj=0.375, FDR_adj=0.957 (unadj p=0.0908)
- TP53+KRAS+CDKN2A: HR_int_adj=1.05, p_int_adj=0.431, FDR_adj=0.957 (unadj p=0.311)
- TP53+KRAS+ARID1A: HR_int_adj=1.03, p_int_adj=0.543, FDR_adj=0.957 (unadj p=0.819)
- TP53+KRAS+SMAD4: HR_int_adj=1.03, p_int_adj=0.704, FDR_adj=0.957 (unadj p=0.505)
- TP53+KRAS+RNF43: HR_int_adj=1.13, p_int_adj=0.798, FDR_adj=0.957 (unadj p=0.633)

**Borderline Resectable/Locally Advanced**
- TP53+KRAS+ARID1A: HR_int_adj=0.77, p_int_adj=0.0799, FDR_adj=0.479 (unadj p=0.0536)
- TP53+KRAS+SMAD4: HR_int_adj=1.03, p_int_adj=0.466, FDR_adj=0.917 (unadj p=0.271)
- KRAS+CDKN2A+SMAD4: HR_int_adj=0.96, p_int_adj=0.743, FDR_adj=0.917 (unadj p=0.571)
- TP53+KRAS+RNF43: HR_int_adj=1.01, p_int_adj=0.755, FDR_adj=0.917 (unadj p=0.504)
- TP53+CDKN2A+SMAD4: HR_int_adj=0.97, p_int_adj=0.764, FDR_adj=0.917 (unadj p=0.621)


## DX_0_TO_5
### Top pair interactions (by adjusted p_int)

**Metastatic**
- KRAS+SMAD4: HR_int_adj=1.39, p_int_adj=0.0282, FDR_adj=0.389 (unadj p=0.00682)
- TP53+KRAS: HR_int_adj=1.16, p_int_adj=0.0798, FDR_adj=0.389 (unadj p=0.205)
- TP53+ARID1A: HR_int_adj=1.44, p_int_adj=0.11, FDR_adj=0.389 (unadj p=0.0854)
- CDKN2A+SMAD4: HR_int_adj=1.70, p_int_adj=0.125, FDR_adj=0.389 (unadj p=0.0605)
- KRAS+CDKN2A: HR_int_adj=1.31, p_int_adj=0.13, FDR_adj=0.389 (unadj p=0.122)

**Resectable**
- TP53+ARID1A: HR_int_adj=1.83, p_int_adj=0.00407, FDR_adj=0.0448 (unadj p=3.22e-05)
- KRAS+ARID1A: HR_int_adj=1.69, p_int_adj=0.014, FDR_adj=0.0771 (unadj p=0.000167)
- KRAS+SMAD4: HR_int_adj=0.89, p_int_adj=0.181, FDR_adj=0.663 (unadj p=0.0553)
- KRAS+RNF43: HR_int_adj=1.39, p_int_adj=0.339, FDR_adj=0.837 (unadj p=0.0721)
- TP53+SMAD4: HR_int_adj=0.91, p_int_adj=0.431, FDR_adj=0.837 (unadj p=0.282)

**Borderline Resectable/Locally Advanced**
- KRAS+SMAD4: HR_int_adj=1.23, p_int_adj=0.0152, FDR_adj=0.084 (unadj p=0.00219)
- TP53+SMAD4: HR_int_adj=1.25, p_int_adj=0.0185, FDR_adj=0.084 (unadj p=0.00338)
- KRAS+ARID1A: HR_int_adj=0.73, p_int_adj=0.0252, FDR_adj=0.084 (unadj p=0.00946)
- TP53+ARID1A: HR_int_adj=0.72, p_int_adj=0.0337, FDR_adj=0.0842 (unadj p=0.0155)
- TP53+RNF43: HR_int_adj=1.40, p_int_adj=0.103, FDR_adj=0.206 (unadj p=0.0171)

### Top triple interactions (by adjusted p_int)

**Metastatic**
- TP53+KRAS+SMAD4: HR_int_adj=1.52, p_int_adj=0.0114, FDR_adj=0.0913 (unadj p=0.0023)
- TP53+KRAS+ARID1A: HR_int_adj=1.46, p_int_adj=0.102, FDR_adj=0.215 (unadj p=0.0758)
- TP53+KRAS+CDKN2A: HR_int_adj=1.32, p_int_adj=0.115, FDR_adj=0.215 (unadj p=0.103)
- KRAS+CDKN2A+SMAD4: HR_int_adj=1.71, p_int_adj=0.124, FDR_adj=0.215 (unadj p=0.059)
- TP53+CDKN2A+SMAD4: HR_int_adj=1.69, p_int_adj=0.134, FDR_adj=0.215 (unadj p=0.0686)

**Resectable**
- TP53+KRAS+ARID1A: HR_int_adj=1.82, p_int_adj=0.00431, FDR_adj=0.0259 (unadj p=3.98e-05)
- TP53+CDKN2A+SMAD4: HR_int_adj=1.21, p_int_adj=0.383, FDR_adj=0.941 (unadj p=0.132)
- TP53+KRAS+SMAD4: HR_int_adj=0.92, p_int_adj=0.474, FDR_adj=0.941 (unadj p=0.347)
- TP53+KRAS+CDKN2A: HR_int_adj=1.03, p_int_adj=0.802, FDR_adj=0.941 (unadj p=0.788)
- TP53+KRAS+RNF43: HR_int_adj=1.12, p_int_adj=0.806, FDR_adj=0.941 (unadj p=0.66)

**Borderline Resectable/Locally Advanced**
- TP53+KRAS+SMAD4: HR_int_adj=1.24, p_int_adj=0.0228, FDR_adj=0.101 (unadj p=0.00575)
- TP53+KRAS+ARID1A: HR_int_adj=0.72, p_int_adj=0.0337, FDR_adj=0.101 (unadj p=0.0155)
- TP53+KRAS+RNF43: HR_int_adj=1.39, p_int_adj=0.111, FDR_adj=0.221 (unadj p=0.0173)
- TP53+KRAS+CDKN2A: HR_int_adj=1.08, p_int_adj=0.562, FDR_adj=0.843 (unadj p=0.688)
- TP53+CDKN2A+SMAD4: HR_int_adj=1.02, p_int_adj=0.88, FDR_adj=0.91 (unadj p=0.937)


