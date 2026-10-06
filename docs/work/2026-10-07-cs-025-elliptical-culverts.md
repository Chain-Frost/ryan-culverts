# CS-025 elliptical culvert implementation slice

Status: implemented on `feat/issue-3-elliptical-culverts`, 2026-10-07.

This note records the first implementation slice of
[issue #3](https://github.com/Chain-Frost/ryan-culverts/issues/3). It does not close the
broader additional-shapes/materials issue.

## Shape priority

1. **Horizontal and vertical ellipses — implemented.** Span and rise define an exact ellipse,
   the depth-dependent area and top width are analytical, and the wetted perimeter can be
   evaluated directly from the ellipse arc-length integral. HDS-5 Third Edition Appendix A,
   Table A.2 retains concrete inlet constants for discontinued Charts 29 and 30.
2. **Pipe arches — deferred.** HDS-5 distinguishes multiple corner-radius/profile families.
   Span and rise alone are therefore not enough to identify the physical section without a
   sourced standard-profile definition or manufacturer geometry.
3. **Arches — deferred.** The same profile-identity problem applies; a nominal "arch" label
   is not a hydraulic geometry.
4. **Other closed shapes — deferred until project demand supplies a source-backed geometry
   definition and applicable inlet/loss evidence.**

This ordering follows the issue requirement to add hydraulic geometry rather than labels.

## Implemented hydraulic contract

`HorizontalEllipseGeometry` requires `span > rise`;
`VerticalEllipseGeometry` requires `rise > span`; equality is rejected in favour of
`CircularGeometry`. Both expose the common closed-section contract: span, rise, full area,
full wetted perimeter, depth-dependent area/perimeter/top width, hydraulic radius/depth,
and crown/full behaviour.

Partial area and top width use exact ellipse identities. Incomplete perimeter uses the exact
arc-length integrand evaluated with fixed composite Simpson quadrature. Tests use independent
high-precision perimeter ordinates at quarter depth and analytical area/symmetry identities.

Closed ellipses, like circular conduits, reach maximum Manning conveyance below the crown.
The normal-depth solver therefore locates the ellipse conveyance maximum and solves only on
the rising branch. A regression constructs discharge from a 0.90-rise target depth, where
conveyance is already greater than the full-section value, to prevent regression to the
previous full-capacity shortcut.

## Empirical applicability

FHWA HDS-5 Third Edition Appendix A Table A.2 supplies separate concrete inlet-control
records for horizontal Chart 29 and vertical Chart 30. These are encoded as separate
`GeometryShape` categories; circular, horizontal-ellipse, vertical-ellipse and rectangular
coefficients cannot be interchanged silently.

HDS-5 Appendix C Table C.2 groups outlet-control entrance losses under "Pipe, Concrete".
The square-edge headwall value is represented by separate horizontal- and vertical-ellipse
records rather than broadening the existing circular record. The existing source-traceable
`CONCRETE_PIPE` material remains applicable; this slice does not invent new material
records simply to satisfy the issue heading.

## External validation boundary

The independent analytical tests do not claim HY-8 parity. `run-hy8` currently exposes
only circle and box shapes, so it cannot yet generate a trustworthy ellipse project.
[run-hy8 issue #5](https://github.com/Chain-Frost/run-hy8/issues/5) tracks the required
version-pinned shape code, inlet-index mapping, reader/writer round trips and local HY-8
8.0.1.2 executable probes for both ellipse orientations.

## Remaining CS-025 work

- research a source-backed standard profile representation for pipe-arch families before
  implementing their depth-dependent section properties;
- do the same for arch families;
- add new material/roughness records only when a primary or manufacturer source provides
  values and applicability not already represented by the current material catalogue;
- after `run-hy8` #5 is implemented, add retained ellipse comparison fixtures here.
