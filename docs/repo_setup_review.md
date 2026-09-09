# Repository setup and packaging review

Reviewed 2026-09-06. Scope: local setup/packaging documentation and selected build
configuration, not a full audit of the other repositories. No files in those
repositories were modified.

## Sources inspected

Windows paths:

- `E:\Library\Automation\ryan-tools\docs\ENVIRONMENTS.md`
- `E:\Library\Automation\ryan-tools\docs\DEVELOPMENT_GUIDE.md`
- `E:\Library\Automation\ryan-tools\requirements.txt`
- `E:\Library\Automation\ryan-tools\pyproject.toml`
- `E:\Library\Automation\ryan-tools\repo-scripts\build_library.py`
- `E:\Github\run-hy8\README.md`
- `E:\Github\run-hy8\pyproject.toml`
- `E:\Github\run-hy8\build_package.bat`
- `E:\Github\run-hy8\install_package.bat`

The supplied `docs\DEVELOPMENT\_GUIDE.md` path did not exist; the actual filename
is `docs\DEVELOPMENT_GUIDE.md`.

## Practices adopted here

| Practice | Decision for ryan-culverts |
| --- | --- |
| Explicit Python selection | Use the selected `python`; version-specific launcher commands are optional |
| Editable development | Install `.[dev]` into normal user Python |
| Separate deployment validation | Test wheel imports away from the editable checkout |
| One dependency definition | Keep dependencies and dev extra in `pyproject.toml` |
| Thin human wrappers | Add only when repeated workflows justify them |
| Documentation ownership | Packaging owns setup; architecture owns design; progress owns phase status |
| Library/process separation | Keep pauses, installers and external executables outside the hydraulic core |
| Concurrent-agent safety | Separate artifact paths and avoid replacing shared editable installs |

`ryan-tools/requirements.txt` contains only `-e .[dev]`. It is an install shortcut,
not a duplicate dependency list or lockfile. That approach is valid; this repo
currently uses the equivalent direct pip command, so another file is unnecessary.

Hatchling and setuptools both implement standard Python builds. Changing backend
alone offers no demonstrated benefit to the existing repositories. Keep their
working resource/package mappings unless a specific maintenance problem warrants
a separately tested migration.

## Improvements worth considering in run-hy8

1. Raise the build requirement from `setuptools>=69` to at least the documented
   `77.0.3` baseline for the modern SPDX licence expression and `license-files`.
   Its existing lower bound allows versions predating those metadata features.
   See the [PyPA guide][pypa]. A normal build resolving latest setuptools can mask
   this lower-bound mismatch.
2. Replace the `Codex scaffolding` author placeholder with actual maintainer
   metadata. Confirm ownership there before editing it.
3. Align quick-start and contribution instructions with the intended interpreter
   policy. The README currently requires `.venv` activation, unlike ryan-tools'
   normal user-Python instructions. Virtual environments are valid, but the
   inconsistency makes the shared workflow harder to follow.
4. Give each build a unique staging directory. `build_package.bat` currently
   reuses and deletes a fixed `run-hy8-build` directory and deletes repository
   `dist/` before build success. Concurrent builds can interfere and a failed
   build can remove the previous artifact.
5. Propagate explicit nonzero exit codes from every failure branch. Several build
   branches end with `goto :EOF` after other commands, rather than returning the
   captured build error deterministically.
6. Separate installing a new package wheel from forced dependency refresh.
   `install_package.bat` currently uses `--force-reinstall` without `--no-deps`,
   affecting the dependency environment too. Routine installs should let pip
   satisfy declared dependencies; same-version development should use editable
   installs, or a deliberate targeted reinstall with dependencies already checked.
7. Correct the README terminology: `build` is the frontend; setuptools is the
   backend. Consider validating the wheel built from the sdist, as this repo does.

## Improvements worth considering in ryan-tools

The documentation separates normal Python, QGIS and OSGeo4W clearly. Preserve
that distinction and the specialized geospatial dependency bootstrap: this small
pure-Python solver has no need for those mechanisms.

The build helper explicitly combines version selection/update and artifact
construction. That may suit copied-wrapper releases, but separating an ordinary
validation build from a deliberate version bump would reduce shared-worktree
churn. Preserve any established release workflow when making that change.

Keep its one-line requirements shortcut if existing tasks/users rely on it.
Setuptools resource packaging and vendored/submodule mappings require their own
installed-wheel validation; do not replace them just to match this repository.

## Verification and delivery

Subsequent user clarification: Python 3.14 is a tested baseline, not a fixed
interpreter requirement. Adopt 3.15 after validation when available. This repo
allows unsupported Python 3 interpreters to attempt builds/installs without a
minor-version gate. Setup commands therefore use the selected `python`.

The MIT metadata and archive-content checks for this repo passed before this
documentation review. This pass verified the Windows launcher resolves to Python
3.14 and linted the changed Markdown. Other repositories' builds/installers were
read, not executed. No claims are made about their full current test status.

[pypa]: https://packaging.python.org/en/latest/guides/writing-pyproject-toml/
