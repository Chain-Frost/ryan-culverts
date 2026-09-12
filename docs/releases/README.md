# Release notes

## Current packaged release

`pyproject.toml` identifies the current packaged version. It remains an alpha package, is
not engineering design software, and has not been published to a package index. The
artifact of record is the sole pure-Python `py3-none-any` wheel under `dist/`; its filename
and embedded version metadata must match `pyproject.toml`. Python 3.14 is its tested
interpreter baseline.

The current `main` source may contain changes listed as [unreleased](../changelog.md) that
are not in this wheel. Creating the next wheel must increment the calendar version.

## Included capability

- Typed SI geometry and hydraulic primitives for circular, rectangular, and filleted
  rectangular culverts, plus rectangular and asymmetric trapezoidal receiving channels.
- Critical depth, normal depth, HDS-5 inlet-control branches, full-flow losses, and
  supported direct-step outlet-control profiles.
- Provisional barrel, identical-barrel group, mixed-group crossing, rating-curve, inverse
  discharge-for-headwater, constant-crest roadway-overtopping, and road-level inventory
  calculations.
- Fixed and discharge-dependent Manning normal-depth tailwater boundaries.
- Structured convergence records, adopted coefficient and roughness provenance, hydraulic
  warnings, and applicability notices.

## Packaging behaviour

- `package.bat` advances the normalized `yy.m.d.vv` calendar version automatically.
- CI builds the declared version without bumping it.
- Candidate wheels are verified in temporary storage before replacing the previous project
  wheel under `dist/`; failed builds retain the previous wheel and restore `pyproject.toml`.
- No source archive is produced or retained.

## Evidence boundary and limitations

HDS-5 and independently calculated fixtures are the calculation evidence. HY-8 8.0.1.2 is
comparison evidence and does not define correctness. The combined solver remains
provisional; review the [computational basis](../computational_basis.md) and
[validation record](../validation.md) before interpreting results.

The packaged artifact does not include design-option search, irregular or submerged
roadway crests, user-supplied tailwater rating tables, uncertainty analysis, plotting, GIS
integration, or a versioned JSON/spreadsheet interface.
Supported shapes, inlets, materials, and profile families remain deliberately limited.

## Installation

Use the maintained installer so it selects the sole current wheel:

```powershell
.\install-latest-wheel.bat
```

The Sustainable Use License 1.0 applies; see the packaged `LICENSE` file.
