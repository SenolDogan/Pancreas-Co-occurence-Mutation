# Stage mutation / additive / OS summary
This report summarizes stage differences, +additive/−additive co-occurrence, and OS associations.
## Stage-differential single genes (chi-square 2×3)
- **TP53**: p=0.0295 (FDR=0.154, Bonf=0.295)
- **CDKN2A**: p=0.0309 (FDR=0.154, Bonf=0.309)
- **GNAS**: p=0.147 (FDR=0.321, Bonf=1)
- **ARID1A**: p=0.172 (FDR=0.321, Bonf=1)
- **PIK3CA**: p=0.187 (FDR=0.321, Bonf=1)
- **RNF43**: p=0.193 (FDR=0.321, Bonf=1)
- **ATM**: p=0.363 (FDR=0.519, Bonf=1)
- **BRAF**: p=0.778 (FDR=0.973, Bonf=1)
- **SMAD4**: p=0.992 (FDR=0.999, Bonf=1)
- **KRAS**: p=0.999 (FDR=0.999, Bonf=1)

## Top +additive / −additive pairs (per stage; filtered by n_AB)

### Metastatic
**Top +additive**
- TP53+CDKN2A: Additive=0.0282, n_AB=218
- TP53+KRAS: Additive=0.0193, n_AB=754
- SMAD4+ARID1A: Additive=0.0073, n_AB=28
- SMAD4+RNF43: Additive=0.0052, n_AB=15
- KRAS+SMAD4: Additive=0.0030, n_AB=204

**Top −additive**
- TP53+SMAD4: Additive=-0.0113, n_AB=155
- CDKN2A+ARID1A: Additive=-0.0065, n_AB=17
- TP53+ARID1A: Additive=-0.0054, n_AB=70
- TP53+GNAS: Additive=-0.0050, n_AB=16
- KRAS+ARID1A: Additive=-0.0041, n_AB=87

### Resectable
**Top +additive**
- TP53+CDKN2A: Additive=0.0290, n_AB=120
- TP53+KRAS: Additive=0.0207, n_AB=473
- CDKN2A+SMAD4: Additive=0.0049, n_AB=32
- KRAS+SMAD4: Additive=0.0042, n_AB=134
- KRAS+CDKN2A: Additive=0.0041, n_AB=133

**Top −additive**
- KRAS+GNAS: Additive=-0.0117, n_AB=22
- KRAS+ARID1A: Additive=-0.0050, n_AB=50
- TP53+RNF43: Additive=-0.0038, n_AB=27
- TP53+ARID1A: Additive=-0.0017, n_AB=40
- KRAS+ATM: Additive=-0.0012, n_AB=17

### Borderline Resectable/Locally Advanced
**Top +additive**
- TP53+CDKN2A: Additive=0.0291, n_AB=87
- CDKN2A+SMAD4: Additive=0.0254, n_AB=36
- TP53+KRAS: Additive=0.0091, n_AB=386
- TP53+SMAD4: Additive=0.0083, n_AB=93
- KRAS+CDKN2A: Additive=0.0069, n_AB=97

**Top −additive**
- TP53+RNF43: Additive=-0.0063, n_AB=27
- KRAS+RNF43: Additive=-0.0008, n_AB=40
- TP53+ARID1A: Additive=-0.0004, n_AB=24
- KRAS+ARID1A: Additive=0.0018, n_AB=33
- KRAS+SMAD4: Additive=0.0060, n_AB=120

## Top +additive / −additive triples (per stage; filtered by n_ABC)

### Metastatic
**Top +additive**
- TP53+KRAS+CDKN2A: Additive=0.0306, n_ABC=209
- KRAS+SMAD4+ARID1A: Additive=0.0066, n_ABC=26
- KRAS+SMAD4+RNF43: Additive=0.0058, n_ABC=15
- TP53+CDKN2A+SMAD4: Additive=0.0036, n_ABC=44
- KRAS+CDKN2A+SMAD4: Additive=0.0022, n_ABC=51

**Top −additive**
- TP53+KRAS+ATM: Additive=-0.0142, n_ABC=12
- KRAS+CDKN2A+ARID1A: Additive=-0.0071, n_ABC=15
- TP53+KRAS+SMAD4: Additive=-0.0062, n_ABC=150
- TP53+KRAS+ARID1A: Additive=-0.0058, n_ABC=65
- TP53+KRAS+GNAS: Additive=-0.0047, n_ABC=15

### Resectable
**Top +additive**
- TP53+KRAS+CDKN2A: Additive=0.0310, n_ABC=115
- TP53+CDKN2A+SMAD4: Additive=0.0108, n_ABC=28
- TP53+CDKN2A+ARID1A: Additive=0.0067, n_ABC=13
- TP53+KRAS+SMAD4: Additive=0.0064, n_ABC=99
- KRAS+CDKN2A+SMAD4: Additive=0.0061, n_ABC=31

**Top −additive**
- TP53+KRAS+RNF43: Additive=-0.0025, n_ABC=26
- TP53+KRAS+ARID1A: Additive=0.0007, n_ABC=39
- KRAS+SMAD4+ARID1A: Additive=0.0015, n_ABC=12
- TP53+SMAD4+ARID1A: Additive=0.0022, n_ABC=10
- KRAS+CDKN2A+ARID1A: Additive=0.0030, n_ABC=13

### Borderline Resectable/Locally Advanced
**Top +additive**
- TP53+KRAS+CDKN2A: Additive=0.0347, n_ABC=86
- KRAS+CDKN2A+SMAD4: Additive=0.0276, n_ABC=36
- TP53+CDKN2A+SMAD4: Additive=0.0275, n_ABC=31
- TP53+KRAS+SMAD4: Additive=0.0123, n_ABC=90
- TP53+CDKN2A+RNF43: Additive=0.0082, n_ABC=10

**Top −additive**
- TP53+KRAS+RNF43: Additive=-0.0049, n_ABC=26
- TP53+KRAS+ARID1A: Additive=0.0022, n_ABC=24
- KRAS+CDKN2A+RNF43: Additive=0.0052, n_ABC=10
- KRAS+SMAD4+RNF43: Additive=0.0056, n_ABC=12
- TP53+CDKN2A+RNF43: Additive=0.0082, n_ABC=10

## OS associations (univariate Cox)
Filters: n_pos>=20 and n_neg>=40 within each stage.

### Single genes (top by p)

**Metastatic**
- TP53: HR=1.36 (CI 1.14-1.61), p=0.000473, medOS(mut)=9.1 vs wt=12.5
- CDKN2A: HR=1.22 (CI 1.03-1.44), p=0.018, medOS(mut)=7.3 vs wt=10.0
- ARID1A: HR=1.32 (CI 1.05-1.66), p=0.0184, medOS(mut)=6.5 vs wt=9.8
- KRAS: HR=1.33 (CI 0.99-1.80), p=0.0593, medOS(mut)=9.4 vs wt=11.9
- ATM: HR=0.77 (CI 0.52-1.13), p=0.183, medOS(mut)=12.6 vs wt=9.4

**Resectable**
- TP53: HR=1.42 (CI 1.12-1.81), p=0.00411, medOS(mut)=20.5 vs wt=23.4
- ARID1A: HR=1.35 (CI 0.95-1.90), p=0.0909, medOS(mut)=16.3 vs wt=21.5
- GNAS: HR=0.75 (CI 0.46-1.23), p=0.256, medOS(mut)=28.4 vs wt=20.9
- KRAS: HR=1.28 (CI 0.81-2.00), p=0.29, medOS(mut)=21.2 vs wt=25.0
- CDKN2A: HR=1.14 (CI 0.88-1.47), p=0.329, medOS(mut)=21.7 vs wt=21.2

**Borderline Resectable/Locally Advanced**
- SMAD4: HR=1.29 (CI 1.02-1.64), p=0.0346, medOS(mut)=14.8 vs wt=14.9
- CDKN2A: HR=1.26 (CI 0.97-1.64), p=0.0795, medOS(mut)=13.5 vs wt=15.0
- TP53: HR=1.11 (CI 0.89-1.38), p=0.353, medOS(mut)=14.2 vs wt=16.4
- ARID1A: HR=1.13 (CI 0.74-1.71), p=0.577, medOS(mut)=14.0 vs wt=15.2
- RNF43: HR=0.94 (CI 0.61-1.43), p=0.763, medOS(mut)=13.1 vs wt=15.1

### Pairs (top by p)

**Metastatic**
- TP53+KRAS: HR=1.35 (CI 1.15-1.59), p=0.000329, Additive=0.0193
- TP53+ARID1A: HR=1.63 (CI 1.25-2.12), p=0.000343, Additive=-0.0054
- TP53+CDKN2A: HR=1.24 (CI 1.05-1.48), p=0.0129, Additive=0.0282
- KRAS+ARID1A: HR=1.35 (CI 1.06-1.72), p=0.015, Additive=-0.0041
- KRAS+CDKN2A: HR=1.23 (CI 1.04-1.45), p=0.0164, Additive=0.0028

**Resectable**
- TP53+ARID1A: HR=1.94 (CI 1.32-2.84), p=0.000672, Additive=-0.0017
- TP53+KRAS: HR=1.42 (CI 1.12-1.79), p=0.0036, Additive=0.0207
- TP53+CDKN2A: HR=1.23 (CI 0.94-1.60), p=0.128, Additive=0.0290
- KRAS+ARID1A: HR=1.29 (CI 0.90-1.85), p=0.159, Additive=-0.0050
- TP53+SMAD4: HR=1.16 (CI 0.87-1.54), p=0.308, Additive=-0.0000

**Borderline Resectable/Locally Advanced**
- KRAS+SMAD4: HR=1.35 (CI 1.06-1.72), p=0.0134, Additive=0.0060
- TP53+SMAD4: HR=1.36 (CI 1.04-1.77), p=0.0233, Additive=0.0083
- TP53+KRAS: HR=1.23 (CI 0.99-1.53), p=0.056, Additive=0.0091
- KRAS+CDKN2A: HR=1.25 (CI 0.96-1.62), p=0.0957, Additive=0.0069
- TP53+CDKN2A: HR=1.21 (CI 0.92-1.59), p=0.183, Additive=0.0291

### Triples (top by p)

**Metastatic**
- TP53+KRAS+ARID1A: HR=1.64 (CI 1.24-2.16), p=0.000488, Additive=-0.0058
- TP53+KRAS+CDKN2A: HR=1.25 (CI 1.05-1.49), p=0.0108, Additive=0.0306
- TP53+KRAS+SMAD4: HR=1.15 (CI 0.95-1.40), p=0.148, Additive=-0.0062
- TP53+CDKN2A+SMAD4: HR=1.12 (CI 0.79-1.59), p=0.526, Additive=0.0036
- KRAS+CDKN2A+SMAD4: HR=1.09 (CI 0.79-1.50), p=0.606, Additive=0.0022

**Resectable**
- TP53+KRAS+ARID1A: HR=1.98 (CI 1.35-2.90), p=0.000441, Additive=0.0007
- TP53+KRAS+CDKN2A: HR=1.18 (CI 0.90-1.55), p=0.222, Additive=0.0310
- TP53+KRAS+SMAD4: HR=1.17 (CI 0.88-1.57), p=0.274, Additive=0.0064
- TP53+CDKN2A+SMAD4: HR=1.26 (CI 0.77-2.05), p=0.356, Additive=0.0108
- KRAS+CDKN2A+SMAD4: HR=1.23 (CI 0.77-1.96), p=0.379, Additive=0.0061

**Borderline Resectable/Locally Advanced**
- TP53+KRAS+SMAD4: HR=1.45 (CI 1.11-1.90), p=0.00637, Additive=0.0123
- TP53+KRAS+CDKN2A: HR=1.19 (CI 0.90-1.57), p=0.219, Additive=0.0347
- KRAS+CDKN2A+SMAD4: HR=1.17 (CI 0.79-1.75), p=0.44, Additive=0.0276
- TP53+CDKN2A+SMAD4: HR=1.12 (CI 0.73-1.72), p=0.61, Additive=0.0275
- TP53+KRAS+ARID1A: HR=1.08 (CI 0.65-1.78), p=0.777, Additive=0.0022
