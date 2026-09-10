# API reference

The supported compatibility boundary is the names exported directly from
`culvert_solver`. Import these names from the package root; submodule paths remain
implementation details unless another document explicitly promotes them.

```python
from culvert_solver import CulvertBarrel, solve_barrel_hydraulics
```

The reference is grouped by how callers use the library:

- [Inputs and configuration](api/inputs.md) covers culvert geometry, crossings,
  tailwater boundaries, roadway inputs, and solver settings.
- [Results and diagnostics](api/results.md) covers solver outputs, profiles,
  warnings, convergence evidence, and inventory summaries.
- [Solvers and rating curves](api/solvers.md) covers the main forward and inverse
  entry points.
- [Hydraulic methods](api/methods.md) covers lower-level equations, numerical roots,
  profiles, losses, and coefficient selection.
- [Built-ins and references](api/builtins.md) covers standard materials, coefficients,
  physical constants, and source records.

The installed package version is available as `culvert_solver.__version__`.
