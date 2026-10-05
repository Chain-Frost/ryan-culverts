# Austroads Section 3.15.1 velocity reconstruction

Status: CS-015 resolved by independent reconstruction on 2026-10-06.

## Source status

The source is Austroads `AGRD05B-23`, *Guide to Road Design Part 5B: Drainage – Open
Channels, Culverts and Floodway Crossings*, edition 1.2, published 30 January 2023.
The official Austroads publication page still identifies edition 1.2 as the current edition
reviewed on 2026-10-06. Its edition 1.2 change log lists rewrites to Sections 4.1, 4.2,
4.5, 4.6 and 4.7 plus terminology changes; it does not identify a correction to Section
3.15.1. Searches of the Austroads site for an AGRD05B-23 erratum, corrigendum or
amendment did not locate a separate correction for this worked example.

Official publication record:
<https://austroads.gov.au/publications/road-design/agrd05b>

The repository copy is
`reference_docs/AGRD05B-23_Guide_to_Road_Design_Part-5B_Drainage_Open_Channels_Culverts_and_Floodway_Crossings.pdf`,
SHA-256 `76b40bf481d1d268e37343be216abea5707dffae6f7972467f9fa9343809f0cd`.

## Exact source locators

- Section 2.3.3, printed page 12: Equation 1, `Q = V A`.
- Section 2.3.3, printed page 13: Equation 3, Manning velocity
  `V = R^(2/3) S^(1/2) / n`, and Equation 4, `R = A / P`.
- Section 3.10.9, printed page 93: inlet-control outlet velocity is `Vo = Q / A`;
  normal depth/velocity are based on Manning flow in the barrel.
- Section 3.15.1, printed page 105: Step 7 gives `Qf = 2.4 m³/s` and first states
  `Vf = 2.5 m/s`, but the immediately following calculation and table use
  `Vf = 2.75 m/s`; the part-flow velocity is reported as `2.75 × 1.12 = 3.08 m/s`.
- Appendix C.1, printed page 179: inlet-control outlet velocity may be taken as normal
  velocity computed by Manning's equation.
- Figure C 1, printed page 180: discharge and velocity for round pipes flowing full.
- Figure C 2, printed page 181: part-full discharge, velocity, depth and area factors.
- Appendix E, Table E 1, printed pages 196–197: circular uniform-flow relationships;
  the table note uses `n = 0.012` for concrete pipe.

## Independent reconstruction

The worked example uses three `1.05 m` RCP barrels at slope `S = 0.0065`. For the
full circular section:

```text
D = 1.05 m
A_f = pi D^2 / 4 = 0.865901475 m²
R_f = D / 4 = 0.2625 m
n = 0.012
S = 0.0065

V_f = R_f^(2/3) S^(1/2) / n
    = 2.754408209 m/s

Q_f = V_f A_f
    = 2.385046132 m³/s
```

At the source's displayed precision this reconstructs `Vf = 2.75 m/s` and
`Qf = 2.4 m³/s`, matching the Step 7 table and the Figure C 1 reading. A second
independent continuity check using only the printed Step 7 values gives
`2.40 / 0.867 = 2.768 m/s`, again consistent with about `2.75 m/s` and not
`2.5 m/s`.

The published part-flow result is also internally tied to the tabulated full-flow
velocity: `2.75 × 1.12 = 3.08 m/s` after source rounding. The printed `Qp`, area and
Figure C 2 factors are nomograph-read and rounded, so recomputing from those displayed
numbers does not reproduce every downstream value exactly.

## Disposition

`2.75 m/s` is the supported full-flow velocity for interpreting this example.
The isolated `2.5 m/s` statement on printed page 105 is inconsistent with Equation 1,
Manning's Equation, the printed full-flow discharge and area, the following calculation,
and the Step 7 table. It is therefore treated in this project as an identified source
transcription error. This is a project disposition based on reconstruction, not a claim
that Austroads has issued a formal erratum.

The `2.5 m/s` value also appears earlier in the example as the maximum allowable stream
velocity used for initial sizing. That makes carry-over into the Step 7 sentence plausible,
but the source does not state the cause of the error.

## Validation use and precision

The discrepancy is resolved, but the complete Section 3.15.1 example remains a workflow
and reporting check rather than a strict combined-solver acceptance fixture. Its inlet and
outlet-control heads, full-flow discharge and part-flow factors include nomograph readings
and displayed rounding. No solver coefficient or tolerance should be tuned to force exact
agreement with those rounded values.

For the resolved full-flow velocity subcalculation:

- reconstructed value: `2.754408209 m/s` from the stated geometry, slope and `n = 0.012`;
- source-reported value supported by the reconstruction: `2.75 m/s`;
- source display precision: `0.01 m/s` for the Step 7 table velocity;
- solver tolerance: not defined by the source display precision and must be chosen
  separately if this subcalculation is later promoted to executable validation.

No executable numerical fixture is added by CS-015 because the full worked example still
contains nomograph-read inputs/expected values whose precision is not independently
specified.
