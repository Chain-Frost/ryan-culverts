# ryan-culverts

A pre-alpha culvert hydraulics library being redesigned around primary hydraulic
references, analytical validation, and mixed-group crossings.

The [updated work plan](culvert_solver_updated_work_plan.md) defines the scope and
development sequence. The `culvert_solver` package now contains provisional circular
and box hydraulics through rating-curve generation. Geometry, numerical foundations,
and several equation-level calculations have internal tests; the combined hydraulic
solver is not yet engineering-validated and must not be treated as design software.

Agents should start with the [work register](docs/work/README.md), which separates
active remediation from deferred scope and links the current acceptance criteria.

The previous `culvertflow` prototype has been retired. See the
[cleanup review](docs/legacy/README.md) for retained evidence, potential reuse from
Git history, and decisions needed before implementation.

Additional implementation references are recorded in the
[reference register](docs/references.md).

Development records: [progress](docs/progress.md),
[computational basis](docs/computational_basis.md),
[architecture](docs/architecture.md), [validation](docs/validation.md) and
[HY-8 capability matrix](docs/hy8_feature_parity.md).

Use your selected Python installation. Python 3.14 is the current tested baseline;
other versions are not blocked but are unsupported. See the
[Python support policy](docs/packaging.md#python-support-policy).

```powershell
python -m pip install --user -e ".[dev]"
python -m pytest -q
python -m ruff check src tests
python -m pyright
python -m pymarkdown -d MD013 scan -r README.md culvert_solver_updated_work_plan.md docs
```

The Markdown check allows long lines for tables and source URLs. Heading rules,
including MD025, remain enabled.

Dependencies and build metadata live in `pyproject.toml`; there is no separate
`requirements.txt`. Pip installs the package and its `dev` extra, while Hatchling
builds distributions through `python -m build`. See the
[packaging workflow](docs/packaging.md) for install and build commands.

## License

This project is licensed under the [Sustainable Use License v1.0](LICENSE)
(`SUL-1.0`).

The software may be used and modified for personal, non-commercial, and internal
business purposes, including commercial professional and consulting work where the
software itself is not provided as a commercial product or service.

Commercial distribution, incorporation into software supplied commercially to third
parties, or provision of the software or its functionality as a paid hosted service,
SaaS, or API is not permitted under the free licence.

Separate commercial licensing may be available on request.
