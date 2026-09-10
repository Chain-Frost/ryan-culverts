# ryan-culverts

`ryan-culverts` is an independent Python library for SI culvert hydraulics. It is built
from primary hydraulic references, analytical fixtures, and explicit applicability
limits rather than by reproducing one external program.

The current package is an alpha integration release. Circular and rectangular barrels,
mixed culvert groups, rating curves, and constant-crest unsubmerged roadway overtopping
are implemented. Combined-system calculations remain provisional and require engineering
review.

## Start here

| Install | Build |
| --- | --- |
| Install a verified wheel and confirm the supported Python version. [Packaging and installation](packaging.md) | Find inputs, solver entry points, result types, and lower-level methods. [API reference](api.md) |

| Validate | Track changes |
| --- | --- |
| Understand the evidence, limitations, and provisional engineering status. [Validation boundary](validation.md) | Review compatibility policy and user-visible changes. [Public API policy](public_api.md) · [Changelog](changelog.md) |

## Engineering status

Passing tests establish software and equation-fixture behaviour; they do not make this
package engineering design software. The [computational basis](computational_basis.md),
[reference register](references.md), and [progress record](progress.md) distinguish
implemented methods from independently accepted methods.
