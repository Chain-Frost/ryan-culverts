# Release notes

## Current packaged release

Version `26.9.9.2` was built locally for packaging and integration testing on 2026-09-09.
It remains an alpha package, is not engineering design software, and has not been published
to a package index. The artifact of record is the pure-Python `py3-none-any` wheel under
`dist/`; Python 3.14 is its tested interpreter baseline.

The current `main` source may contain changes listed as [unreleased](../changelog.md) that
are not in this wheel. Creating the next wheel must increment the calendar version.

## Included capability

- Typed SI geometry and hydraulic primitives for circular and rectangular culverts.
- Critical depth, normal depth, HDS-5 inlet-control branches, full-flow losses, and
  supported direct-step outlet-control profiles.
- Provisional barrel, identical-barrel group, mixed-group crossing, rating-curve, and
  road-level inventory calculations.
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

The packaged `26.9.9.2` artifact does not include roadway overtopping, design-option search,
uncertainty analysis, plotting, GIS integration, or a versioned JSON/spreadsheet interface.
Supported shapes, inlets, materials, and profile families remain deliberately limited.

## Installation

Use the maintained installer so it selects the sole current wheel:

```powershell
.\install-latest-wheel.bat
```

The Sustainable Use License 1.0 applies; see the packaged `LICENSE` file.
