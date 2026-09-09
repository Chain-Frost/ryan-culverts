# Packaging and dependencies

## One dependency definition

`pyproject.toml` is authoritative. No `requirements.txt`, `setup.py`, Poetry
configuration or Hatch environment is required.

| Setting | Purpose |
| --- | --- |
| `[project].dependencies` | Runtime dependencies; currently empty |
| `[project.optional-dependencies].dev` | Tests, linting, typing and build frontend |
| `[build-system]` | Hatchling build backend |
| `[tool.hatch.build.targets.wheel]` | Universal-wheel package contents |

The distribution name is `ryan-culverts`; the Python import is `culvert_solver`.
Version `26.9.9.2` is the current packaged alpha release. `pyproject.toml` is the version
authority. Releases use the PEP 440-normalized calendar scheme `yy.m.d.vv`, where `vv`
starts at `1` and increments for each release made on the same local date. It is intended
for integration and packaging tests, not engineering design acceptance.

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

The Windows convenience workflow follows the established `ryan-tools` pattern:

```powershell
.\package.bat
.\install-latest-wheel.bat --dry-run
.\package_and_install.bat
.\force-reinstall.bat --dry-run
.\package_and_force_install.bat --dry-run
```

`package.bat` advances `yy.m.d.vv`, updates `pyproject.toml`, and builds into temporary
storage. It verifies version and licence metadata, exact packaged licence text, `py.typed`,
and exclusion of development/reference inputs before promoting the new wheel. Only after
successful verification does it remove older top-level `ryan_culverts-*` distributions
from `dist/`. A failed build or verification restores `pyproject.toml` and retains the
previous wheel.

Use an explicit newer version when required:

```powershell
.\package.bat --version 26.9.9.5
```

CI uses `python scripts/build_package.py --no-bump` to build the version already declared
in `pyproject.toml` without editing it. `install-latest-wheel.bat` selects the newest
matching wheel and installs it into the user site-packages. The combined script stops if
the build fails and otherwise performs both operations. All wrappers preserve the
underlying Python or pip exit status. Run `.\verify-package.bat` to repeat wheel checks
without rebuilding.

`force-reinstall.bat` passes `--force-reinstall --no-deps` to pip for the newest existing
wheel. `package_and_force_install.bat` rebuilds and verifies first. These are recovery and
testing operations; prefer the normal installer unless replacement is intentional.

For release verification, install without disturbing an editable or user installation:

```powershell
.\install-latest-wheel.bat --target C:\path\to\temporary-target
```

After installing the development extra, the direct build command remains:

```powershell
python -m build --wheel
```

The `build` frontend invokes Hatchling in an isolated build environment and installs
`[build-system]` requirements automatically. This is separate from your user Python setup.

Outputs go into `dist/`. The wheel contains the import package,
typed marker and package metadata/licence. Tests, development documentation, research PDFs,
historical fixtures, caches, and generated reports are excluded. The `py3-none-any` tag
identifies pure Python 3 code with no platform-specific ABI, so the same wheel can be used
on Windows, Linux, and macOS. Only Python 3.14 is presently tested.

Install a built wheel directly by passing its actual path to pip. For the current version:

```powershell
.\install-latest-wheel.bat
```

No package-index or GitHub Release publication is configured. Building does not upload or
copy anything. The office network distribution folder is a Git checkout of this repository,
and its tracked `dist/` directory is the installation source. After a release is committed
and pushed, update that clean checkout with `git pull`; do not maintain or copy the wheel to
a second distribution folder.

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
