# Primary-source fixture candidates

Reviewed 2026-09-09 for CS-001. These records preserve source-native inputs and
published results. They are research fixtures, not automatic engineering acceptance.
CS-003 and CS-004 own method implementation; CS-006 owns executable cross-phase
fixtures.

Use the source's customary-unit values when reproducing an old worked example. Convert
to SI with exact unit definitions (`1 ft = 0.3048 m` and `1 ft³/s = 0.028316846592
m³/s`) in the test setup, and do not substitute a publication's independently rounded SI
caption. Solver tolerances must be wider than the source's displayed precision and must
also allow for chart-reading precision where a nomograph supplies an intermediate value.

## Bodhaine worked-example audit

The ten examples in USGS TWRI Book 3, Chapter A3 were reviewed on printed pages 52-60
(local PDF pages 61-69). They demonstrate the 1968 indirect peak-discharge procedure,
including its coefficient charts; they do not define the project's HDS-5 inlet method.

| Example | Published case | Final discharge | Locator | Disposition |
| --- | --- | ---: | --- | --- |
| 1 | Type 1, corrugated-metal pipe | 725 ft³/s | Printed p. 52; local PDF p. 61 | Selected classification/reproduction candidate |
| 2 | Type 1, concrete box | 531 ft³/s | Printed p. 53; local PDF p. 62 | Selected box reproduction candidate |
| 3 | Type 2, corrugated-metal pipe | 268 ft³/s | Printed pp. 53-54; local PDF pp. 62-63 | Reviewed; redundant with Example 4 |
| 4 | Type 2, concrete box | 523 ft³/s | Printed pp. 54-55; local PDF pp. 63-64 | Reviewed; chart-dependent |
| 5 | Type 3, corrugated-metal pipe | 251 ft³/s | Printed pp. 55-56; local PDF pp. 64-65 | Reviewed; backwater iteration |
| 6 | Type 4, concrete pipe | 125 ft³/s | Printed pp. 56-57; local PDF pp. 65-66 | Selected full-flow reproduction candidate |
| 7 | Type 5, corrugated-metal pipe | 120 ft³/s | Printed p. 57; local PDF p. 66 | Reviewed; chart-dependent |
| 8 | Type 6, concrete pipe | 209 ft³/s | Printed pp. 57-58; local PDF pp. 66-67 | Selected Type 6 comparison candidate |
| 9 | Routing method, Type 3 | 251 ft³/s | Printed pp. 58-59; local PDF pp. 67-68 | Reviewed; reproduces Example 5 |
| 10 | Type 3, irregular culvert | 250 ft³/s | Printed pp. 59-60; local PDF pp. 68-69 | Reviewed; geometry outside initial scope |

### BOD-A3-EX1

- Inputs: 10 ft diameter corrugated-metal pipe in a concrete headwall; `r/D =
  0.006`; 100 ft length; slope `0.02`; Manning `n = 0.024`; headwater `h1 =
  12.00 ft`; invert fall `z = 2.00 ft`; downstream depth `h4 = 6.00 ft`;
  approach area `1,000 ft²`; approach conveyance `300,000` in the source's customary
  units.
- Expected quantity: final discharge `725 ft³/s` (`20.5297 m³/s` after exact
  conversion), classified and proved as Type 1.
- Published precision: whole ft³/s; intermediate chart coefficients are displayed to
  three or four significant figures.
- Applicability: reproduction of Bodhaine's Type 1 reasoning for this steep circular
  case. It is not an HDS-5 inlet-control acceptance value because the result depends on
  Bodhaine Figures 9, 10, 20 and 21 and the historical coefficient formulation.

### BOD-A3-EX2

- Inputs: 8 ft square concrete box with square-edged entrance; 100 ft length; slope
  `0.02`; Manning `n = 0.015`; headwater `h1 = 10.00 ft`; invert fall `z =
  2.00 ft`; downstream depth `h4 = 4.00 ft`; approach area `330 ft²`; approach
  conveyance `38,900` in the source's customary units.
- Expected quantity: final discharge `531 ft³/s` (`15.0362 m³/s` after exact
  conversion), classified and proved as Type 1.
- Published precision: whole ft³/s; critical depth and losses are shown to 0.01 ft.
- Applicability: simple rectangular geometry is representable, but the expected result
  uses Bodhaine Figure 23 and its critical-depth discharge coefficient. Keep it as an
  external historical-method reproduction, not a production-method oracle.

### BOD-A3-EX6

- Inputs: 4 ft diameter concrete pipe with bell entrance; 50 ft length; Manning `n =
  0.012`; relative rounding `w/D = 0.075`; `h1 = 7.00 ft`, `h4 = 5.00 ft`,
  and zero invert fall.
- Expected quantity: `125 ft³/s` (`3.53961 m³/s` after exact conversion), Type 4.
- Published precision: whole ft³/s; the source coefficient is `C = 0.955`.
- Applicability: useful as a full-flow energy reproduction. The entrance geometry and
  Bodhaine coefficient must be supplied explicitly; neither may be inferred from concrete
  material.

### BOD-A3-EX8

- Inputs: 4 ft diameter concrete pipe with beveled entrance; 50 ft length; Manning `n =
  0.012`; relative rounding `w/D = 0.075`; `h1 = 8.00 ft`, `h4 = 1.00 ft`,
  and 1 ft invert fall.
- Expected quantity: `209 ft³/s` (`5.91822 m³/s` after exact conversion), Type 6.
- Published precision: whole ft³/s; the adjusted chart factor is displayed as `8.31`.
- Applicability: an independent classical Type 6 comparison, but not a direct fixture
  for the current high-head HDS-5 extension. Reproduction requires the source's Figure 17
  relationship and explicit beveled-inlet context.

## Corrected FHWA box example

FHWA-HRT-06-138 Appendix D, printed pages 127-140 (local PDF pages 140-153),
provides the selected modern-box case. The authoritative reproduction basis is the
customary-unit column because the example's independently rounded SI and customary-unit
flow labels are not exact conversions.

Shared inputs are two 9 by 8 ft cells, 84 ft long, inlet invert 78.81 ft, outlet
invert 78.79 ft, Manning `n = 0.012`, the downstream rating in Table 21, and the
cross-section coordinates in Table 20. The field-cast FC-D-30 configuration has 6 in
corner fillets, 30° flared wingwalls, a 45° top-edge bevel, and Table 11 Sketch 2
entrance-loss coefficient `Ke = 0.32`.

| Case | Flow | Expected quantity | Published precision | Locator |
| --- | ---: | ---: | --- | --- |
| BOX-APPD-Q25 | 773 ft³/s total | Headwater elevation 85.907 ft | 0.001 ft | Table 25, local PDF p. 150 |
| BOX-APPD-Q100 | 1,602 ft³/s total | Headwater elevation 89.251 ft | 0.001 ft | Table 26; local PDF p. 151 |

The intermediate expected values include critical depths in Table 22, normal depths in
Table 23, outlet starting conditions in Table 24, and inlet HGL/EGL values in Tables 25
and 26. The case is fixture-ready as a source record but not executable with the current
plain `RectangularGeometry`: net area, corner fillets, the top-edge bevel, approach and
tailwater sections, and the precise multi-cell inlet configuration must be represented
first. CS-013 owns that future configuration work. Substituting a sharp-corner rectangle
would change the published problem.

The report's Table 12 fifth-order polynomial is not the expected method for this outlet-
controlled Appendix D result. Printed pages 72-73 (local PDF pages 85-86) limit those
polynomials to their measured range, approximately `0.4 < HW/D < 2.3`, and warn of
low- and high-end numerical errors.

## Austroads design-workflow case

AGRD05B-23 Section 3.15.1, printed pages 101-106 (local PDF pages 111-116), uses
three 1,050 mm RCP barrels, 15.6 m long at slope `0.0065`, carrying `6.25 m³/s`
total with tailwater `0.96 m`. It publishes inlet headwater `1.40 m`, outlet
headwater `1.36 m`, inlet control, outlet depth `0.75 m`, outlet area `0.67 m²`,
outlet velocity `3.08 m/s`, and Froude number `1.17`.

This case is accepted as a workflow and reporting checklist, not as a strict numerical
fixture. Printed page 105 states full-flow velocity `2.5 m/s`, then tabulates `2.75
m/s` and uses `2.75 × 1.12 = 3.08 m/s`. Its inlet and full-flow heads are also read
from nomographs. CS-015 must reconcile that source inconsistency or identify a corrected
edition before numerical acceptance; no solver value is tuned to it.
