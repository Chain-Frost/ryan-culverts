# FHWA-HRT-06-138 (Corrected) Inlet Configuration Catalog

**Reference:**

- Title: Effects of Inlet Geometry on Hydraulic Performance of Box Culverts
- Report: FHWA-HRT-06-138 (Corrected Errata Version)
- Publisher: Federal Highway Administration
- Year: 2006 / Corrected 2007

## 1. Overview

This document extracts the corrected Table 11 and Table 12 coefficients for new inlet geometries introduced in this report. These coefficients are intended to supplement HDS-5 and replace or extend existing box culvert models, primarily resolving inlet control polynomial regressions and HDS-5 Form 1/2 regressions.

## 2. Table 11 Extracted Coefficients (Form 1 / Form 2)

| Description | $K_e$ | $K_1$ | $M_1$ | $K_2$ | $M_2$ | $c$ | $Y$ |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 30° flared wingwalls, top edge beveled at 45° | - | - | - | - | - | - | - |
| Single barrel | 0.26 | 0.005 | 1.05 | 0.44 | 0.74 | 0.04 | 0.48 |
| 2, 3, and 4 multiple barrels | 0.32 | - | - | 0.47 | 0.68 | 0.04 | 0.62 |
| 2:1 to 4:1 span-to-rise ratio | 0.20 | - | - | 0.48 | 0.65 | 0.041 | 0.57 |
| 15° skewed headwall, multiple barrels | 0.36 | - | - | 0.69 | 0.49 | 0.029 | 0.95 |
| 30° to 45° skewed headwall, multiple barrels | 0.45 | - | - | 0.69 | 0.49 | 0.027 | 1.02 |
| 0° flared wingwalls, extended sides | - | - | - | - | - | - | - |
| Square-edged at crown | 0.79 | 0.055 | 0.68 | 0.55 | 0.64 | 0.047 | 0.55 |
| 45° straight bevel at crown, 0/6-in corner fillets | 0.48 | - | - | 0.56 | 0.62 | 0.045 | 0.55 |
| 45° straight bevel at crown, multiple barrels | 0.52 | - | - | 0.55 | 0.59 | 0.038 | 0.69 |
| 45° straight bevel at crown, 2:1 to 4:1 S/R ratio | 0.37 | - | - | 0.61 | 0.57 | 0.041 | 0.67 |
| Crown rounded at 8-in rad, 0/6-in corner fillets | 0.24 | - | - | 0.56 | 0.62 | 0.038 | 0.67 |
| Crown rounded at 8-in rad, 12-in corner fillets | 0.3 | - | - | 0.56 | 0.62 | 0.038 | 0.67 |
| Crown rounded at 8-in rad, 12-in fillets, multiple b. | 0.54 | - | - | 0.55 | 0.60 | 0.023 | 0.96 |
| Crown rounded at 8-in rad, no fillets, 2:1 to 4:1 S/R | 0.30 | - | - | 0.61 | 0.57 | 0.033 | 0.79 |

Note: Dashes indicate missing, uncomputed, or group-heading cells.

## 3. Table 12 Extracted Polynomial Coefficients

The polynomial regression approach (Eq. 24) is given as:

$ \frac{HW}{D} = a + b X + c X^2 + d X^3 + e X^4 + f X^5 $

where $X = \frac{Q}{A \sqrt{gD}}$. This is the dimensionless discharge used by
the report; omitting $g$ changes the independent variable and invalidates the fit.

| Description | a | b | c | d | e | f |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 30° flared wingwalls, top edge beveled at 45° | - | - | - | - | - | - |
| Single barrel | 0.163450 | 0.127103 | 0.256193 | -0.131630 | 0.025211 | -0.001600 |
| 2, 3, and 4 multiple barrels | 0.112542 | 0.375074 | 0.002657 | -0.026380 | 0.006867 | -0.000470 |
| 2:1 to 4:1 span-to-rise ratio | 0.182681 | 0.209471 | 0.158774 | -0.092970 | 0.019381 | -0.001310 |
| 15° skewed headwall, multiple barrels | 0.182031 | 0.686256 | -0.277040 | 0.0821130 | -0.011670 | 0.000654 |
| 30° to 45° skewed headwall, multiple barrels | 0.363958 | 0.283523 | 0.069040 | -0.044221 | 0.008965 | -0.000595 |
| 0° flared wingwalls, extended sides | - | - | - | - | - | - |
| Square-edged at crown | 0.278122 | -0.002930 | 0.448521 | -0.228310 | 0.044973 | -0.00299 |
| 45° straight bevel at crown, 0/6-in corner fillets | 0.244295 | 0.129322 | 0.339620 | -0.189660 | 0.038635 | -0.0026 |
| 45° straight bevel at crown, multiple barrels | 0.164261 | 0.43842 | -0.03128 | -0.01919 | 0.006288 | -0.00046 |

| 45-degree straight bevel at crown, 2:1 to 4:1 S/R ratio | 0.254968 | 0.273934 | 0.154712 | -0.09911 | 0.020506 | -0.00135 |
| Crown rounded at 8-in radius, 0/6-in corner fillets | 0.203424 | 0.31092 | 0.10783 | -0.07609 | 0.015779 | -0.00102 |
| Crown rounded at 8-in radius, 12-in corner fillets | 0.203424 | 0.31092 | 0.10783 | -0.07609 | 0.015779 | -0.00102 |
| Crown rounded at 8-in radius, 12-in fillets, multiple barrels | 0.10315 | 0.619895 | -0.23147 | 0.071093 | -0.01075 | 0.000628 |
| Crown rounded at 8-in radius, no fillets, 2:1 to 4:1 S/R | 0.199715 | 0.446748 | -0.02414 | -0.02334 | 0.006761 | -0.00048 |

Source locator: corrected Table 12, printed page 86 (local PDF page 99).
Table 11 is on printed page 85 (local PDF page 98). Values remain research
transcriptions until independently checked and represented with executable
applicability constraints.

## 4. Analysis and Impact

- Multi-barrel configurations have a pronounced effect on both the entrance loss coefficient $K_e$ and the polynomial regression fits.
- The repository's `resolve_inlet_coefficients` will need to be capable of resolving based on span-to-rise ratios and multi-barrel quantities if these box geometries are fully supported.
