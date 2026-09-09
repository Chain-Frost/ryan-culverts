# Packaging and dependencies

## One dependency definition

`pyproject.toml` is authoritative. No `requirements.txt`, `setup.py`, Poetry
configuration or Hatch environment is required.

| Setting | Purpose |
| --- | --- |
| `[project].dependencies` | Runtime dependencies; currently empty |
| `[project.optional-dependencies].dev` | Tests, linting, typing and build frontend |
| `[build-system]` | Hatchling build backend |
| `[tool.hatch.build.targets]` | Wheel and source-archive contents |

The distribution name is `ryan-culverts`; the Python import is `culvert_solver`.
Version `0.2.0.dev1` is a development version recorded once in `pyproject.toml`,
not an engineering-ready release.

## Python support policy

Python 3.14 is the current tested and supported baseline. Move that baseline to
Python 3.15 when available and validated, updating tool targets and classifiers
alongside the checks. Supporting every older interpreter is not a project goal.

Other Python versions may attempt to build, install and run the project, but are
unsupported until explicitly validated. Metadata declares only `requires-python
>=3`, with no minor-version floor or runtime version guard. This is permission to try,
not a compatibility guarantee: syntax, dependencies or build tools may still fail.

The Pyright and Ruff version targets describe the supported development baseline;
they do not select or restrict the interpreter used to build the package.

Dependency minimums express compatibility, not a locked environment. There is
currently no lockfile or claim of identical dependency resolution across dates.
If reproducible CI environments become necessary, add a generated lock/constraint
artifact rather than maintaining a second hand-written dependency list.

## Install for development

From the repository root, using your selected Python installation:

```powershell
python -m pip install --user -e ".[dev]"
```

Editable installation makes source edits visible without reinstalling. Rerun the
command after dependency or package-metadata changes. This does not require a
manually created virtual environment.

For a regular local installation without developer tools:

```powershell
python -m pip install --user .
```

The README lists the active verification commands.

## Build and share

After installing the development extra:

```powershell
python -m build
```

The `build` frontend invokes Hatchling, building an sdist and then a wheel from
that sdist. Its temporary isolated build environment installs `[build-system]`
requirements automatically; this is separate from your user Python setup.

Outputs go into Git-ignored `dist/`. The wheel contains the import package,
typed marker and package metadata/licence. The sdist also contains tests,
development documentation and the work plan. Historical CSV/HY-8 fixtures,
the local reference PDF, caches and generated reports are excluded.

Install a built wheel by passing its actual path to pip. For the current version:

```powershell
python -m pip install --user dist/ryan_culverts-0.2.0.dev1-py3-none-any.whl
```

No publication or release automation is configured. Building does not upload
anything. Update the version deliberately before producing a distinct release.

## Windows and concurrent work

Use `python` for the interpreter selected in your terminal. In VS Code, select
that same installation. Confirm it with `python -c "import sys; print(sys.executable)"`.
The Windows launcher can select a version explicitly when needed, for example
`py -3.14`; it is not required by the workflow.
For an explicit executable path containing spaces, PowerShell needs the call
operator, for example `& "C:\Program Files\Python314\python.exe" -m pip --version`.

Keep development editable while source changes are underway. A regular wheel
installation replaces an editable installation of the same distribution in that
interpreter. Validate wheels in a temporary target or dedicated test environment
to avoid disrupting another agent's imports. Source-based pytest checks alone do
not verify the contents of an installed wheel.

Build from a stable checkout for release evidence. For simultaneous scratch builds,
give each invocation a different output directory, for example
`python -m build --outdir dist/packaging-review`. Separate output folders prevent
artifact collisions; they do not make concurrently edited source a stable snapshot.
Do not delete shared `dist/` before a build, silently bump versions, or stage Git
changes as part of packaging.

See the [cross-repository setup review](repo_setup_review.md) for practices assessed
from `ryan-tools` and `run-hy8`. Those repositories were inspected read-only.

## Licence and metadata

The project uses the SPDX expression `SUL-1.0` and includes the root `LICENSE` in
distribution metadata. The copyright holder is Ryan Brook. External literature
and third-party code retain their own licences; the project licence does not
relicense those sources.

The configuration follows the [PyPA project metadata guide][pypa] and
[Hatch build configuration][hatch].

[pypa]: https://packaging.python.org/en/latest/guides/writing-pyproject-toml/
[hatch]: https://hatch.pypa.io/latest/config/build/
