# ryan-culverts

An early-stage culvert hydraulics library built around primary hydraulic references,
analytical validation, and mixed-group crossings. Version `26.9.9.1` is the first packaged
alpha release for integration testing; it is not engineering design software.

The [long-term development plan](docs/work/long-term-development-plan.md) defines the scope and
development sequence. The `culvert_solver` package contains provisional circular and box
hydraulics through rating-curve generation, including mixed groups and road-level
inventories. Geometry, numerical foundations, and several equation-level calculations
have analytical or published-example tests; combined-system validation remains bounded.
See the [26.9.9.1 release notes](docs/releases/26.9.9.1.md) before using the package.

Agents should start with the [work register](docs/work/README.md), which separates
active remediation from deferred scope and links the current acceptance criteria.

The previous `culvertflow` prototype has been retired. See the
[cleanup review](docs/legacy/README.md) for retained evidence, potential reuse from
the preserved scenarios, and decisions made before implementation.

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
python -m ruff check .
python -m pyright
python -m pymarkdown -d MD013 scan -r README.md docs
```

The Markdown check allows long lines for tables and source URLs. Heading rules,
including MD025, remain enabled.

Dependencies and build metadata live in `pyproject.toml`; there is no separate
`requirements.txt`. Pip installs the package and its `dev` extra, while Hatchling
builds the universal wheel through `python -m build --wheel`. See the
[packaging workflow](docs/packaging.md) for install and build commands.

On Windows, `.\package.bat` builds and verifies the universal wheel,
`.\install-latest-wheel.bat` installs the newest local wheel, and
`.\package_and_install.bat` performs both steps with fail-fast exit handling. Use
`.\force-reinstall.bat` for the existing wheel or `.\package_and_force_install.bat` to
rebuild before forcing replacement of the installed package.

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
