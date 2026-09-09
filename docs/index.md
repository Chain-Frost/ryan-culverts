# ryan-culverts

`ryan-culverts` is an independent Python library for SI culvert hydraulics. It is built
from primary hydraulic references, analytical fixtures, and explicit applicability
limits rather than by reproducing one external program.

The current package is an alpha integration release. Circular and rectangular barrels,
mixed culvert groups, rating curves, and constant-crest unsubmerged roadway overtopping
are implemented. Combined-system calculations remain provisional and require engineering
review.

## Start here

- Read [packaging and installation](packaging.md) to install a verified wheel.
- Use the [API reference](api.md) for the supported top-level import surface.
- Check the [public API policy](public_api.md) before depending on compatibility.
- Review the [validation boundary](validation.md) before using hydraulic results.
- Consult the [changelog](changelog.md) for user-visible changes.

## Engineering status

Passing tests establish software and equation-fixture behaviour; they do not make this
package engineering design software. The [computational basis](computational_basis.md),
[reference register](references.md), and [progress record](progress.md) distinguish
implemented methods from independently accepted methods.
