# NCHRP Report 734: Hydraulic Loss Coefficients for Culverts

**Reference:**

- Title: Hydraulic Loss Coefficients for Culverts
- Report: NCHRP Report 734
- Publisher: Transportation Research Board
- Year: 2012

## 1. Overview

NCHRP 734 expands on the traditional hydraulic design of highway culverts by providing empirically derived loss coefficients for modern geometries, specifically addressing:

1. Slip-lined culverts
2. Buried-invert (embedded) culverts
3. Multi-barrel culvert installations

## 2. Slip-Lined Culverts

### Entrance Loss Coefficients ($K_e$)

Slip-lined culverts typically result in a projecting pipe inlet condition because the smaller liner pipe extends beyond the original host pipe. The report provides the following entrance loss coefficients for slip-lined conditions (derived from Table 3-1):

- **Traditional thin-wall projecting**: $K_e = 0.80$
- **Slip-lined, untapered**: average $K_e = 0.77$
- **Slip-lined, tapered 2-in. projection**: $K_e = 0.71$
- **Slip-lined, tapered 4-in. projection**: $K_e = 0.70$

The report gives approximately 1.5% uncertainty for these measurements. Source:
Chapter 3 results, printed page 22 (local PDF page 30).

### Inlet Control Constants

Derived from Table 3-2 for Form 1 and Form 2 HDS-5 unsubmerged/submerged equations:

| Test Culvert Inlet End Treatment | Unsubmerged Form 1 (c, Y) | Unsubmerged Form 2 (K, M) | Submerged |
| :--- | :--- | :--- | :--- |
| **Traditional projecting** | c = 0.0946, Y = 0.60 | K = 0.5812, M = 0.58 | c = 0.0513, Y = 0.69 |
| **Slip-lined, 2-in. projecting** | c = 0.0971, Y = 0.55 | K = 0.5830, M = 0.57 | c = 0.0520, Y = 0.64 |
| **Slip-lined, 4-in. projecting** | c = 0.0945, Y = 0.54 | K = 0.5808, M = 0.57 | c = 0.0520, Y = 0.66 |
| **Slip-lined, tapered 2-in. projection** | c = 0.0908, Y = 0.54 | K = 0.5772, M = 0.57 | c = 0.0467, Y = 0.69 |
| **Slip-lined, tapered 4-in. projection** | c = 0.0841, Y = 0.52 | K = 0.5697, M = 0.56 | c = 0.0473, Y = 0.65 |

Source locator: Table 3-2, printed page 23 (local PDF page 31). The final row
label is interpreted from the test sequence and surrounding discussion because
the extracted table text repeats the 2-in. label; verify against the rendered
page before implementation.

Observation: Under inlet control, there is no appreciable difference between the
head-discharge relationships for the traditional thin-wall projecting inlet and the
slip-lined thin-wall projecting inlet.

## 3. Multi-Barrel Interactions

The report found that a representative average-barrel relationship correlated
well with single-barrel results and concluded that superposition is likely
appropriate for most total-flow calculations. Nonuniform approach flow produced
differences up to about 10%, and a depressed barrel up to about 4%. Individual
middle-barrel discharge could differ by about 7% (and barrels in a two-barrel
test by about 5%), which matters for barrel-specific outlet protection or fish
passage. Source: Chapter 5 conclusions, printed page 49 (local PDF page 57).

## 4. Applicability to the Repository

- **Slip-lined configurations** should be added to the inlet configuration catalogue with their associated $K_e$ and inlet control regression constants.
- **Embedded culverts (composite roughness)** will be required if the domain model is expanded to natural-bottom or partially buried culverts.
- Multi-barrel superposition remains a reasonable total-flow architecture for
  `CulvertCrossing`; document the approach-flow and per-barrel limitations rather
  than applying an unsupported blanket efficiency reduction.
