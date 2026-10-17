# Publishing ryan-culverts to PyPI

## One-time setup

Add a pending publisher at [PyPI account publishing](https://pypi.org/manage/account/publishing/)
for the first release, or use the project's Publishing settings if it already exists.
Enable two-factor authentication on your PyPI account.

| Field | Value |
| --- | --- |
| PyPI project | `ryan-culverts` |
| GitHub owner | `Chain-Frost` |
| GitHub repository | `ryan-culverts` |
| Workflow filename | `pypi-publish.yml` |
| Environment | `pypi` |

The GitHub `pypi` environment allows `v*` tags without a required reviewer, so publication
is automatic after release validation. Actions must be allowed to create PRs; the
workflows request write permissions only in the preparation/finalization jobs.
No PyPI API token or GitHub personal access token is stored.
A pending publisher does not reserve the project name.

The main ruleset requires PRs, squash merges, resolved review conversations and successful
up-to-date CI. Required approvals remain zero for the solo-maintainer workflow. The
maintainer bypass is limited to PRs. Release tags require CI and cannot normally be
updated or deleted; tag creation remains permitted for the workflow token. Merged
branches are automatically deleted. The PR records live configuration and validation.

## Automatic release after successful main CI

Every approved code merge that passes `Python CI` on `main` triggers a
fresh, **automatically versioned** PyPI release. No manual release PR,
version bump, tag creation or Actions dispatch is required.

The publisher compares every historical PyPI version and Git tag with the
source version before allocating the next strictly greater Perth-calendar
version. Same-day releases increment the revision, and publication is
serialized using GitHub Actions `queue: max`. Version conflicts, unknown
historical schemes and PyPI access failures stop publication rather than
silently downgrading or reusing a version.

The release Git tag points to the exact CI-verified `main` source commit.
Its version is stamped into **both** `pyproject.toml` and
`src/culvert_solver/_version.py` in the isolated publication checkout.
The tagged source commit can retain an older baseline version. The source
is never pushed back to protected `main`; the generated wheel metadata and
release tag carry the published version. Rebuild through the tag-aware
workflow to reproduce it. The existing build verification, installed-wheel
smoke and OIDC Trusted Publishing gates remain.

Details and recovery procedures are recorded in
[automatic release policy](AUTO_PYPI_RELEASES.md).

## Recovery and legacy manual releases

The older `Actions > Release to PyPI > Run workflow` preparation workflow
remains available, but it is no longer needed for ordinary releases. It
creates a release PR; the legacy finalizer handles that specific merge, and
the new publisher deliberately skips its automatic main-merge path.

A manually published stable GitHub Release may also trigger publication,
provided the tag identifies a `main` ancestor, metadata is stamped from
the tag during the publication build and PyPI has no equal or newer version.
Never move a release tag or overwrite an already published distribution.
On failure, inspect the reserved GitHub tag and release and rerun only if its
version remains newer than every PyPI version.

After publication, install or upgrade with:

```powershell
python -m pip install --upgrade ryan-culverts
```

The Python import remains `culvert_solver`. An automated wheel smoke test
does not replace engineering verification or executable HY-8 validation.

## CI scope

CI checks workflows using checksum-verified Actionlint 1.7.12. Superseded PR runs cancel;
main push runs remain independent for release finalization. Multi-command PowerShell
steps stop at the first failed check. Builders verify their candidates, so immediately
repeating that verification is unnecessary; retained-wheel verification remains separate.
Test duration reports identify future bottlenecks without disabling hydraulic tests.

The Windows verification job retains offline tests, Ruff, strict Pyright, Markdown and
strict MkDocs. Windows/Linux/macOS installed-wheel and vendored-package smoke jobs remain
separate platform checks. They install only the build frontend and the wheel; the core
has no runtime dependencies. No run-hy8/HY-8 dependency is added to ordinary CI.

References:

- [PyPI pending publishers](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/)
- [GitHub workflow triggers](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow)

Publication also rejects direct URL dependencies, including optional extras, before
upload. Publish run-hy8 before testing the optional ryan-culverts external-validation
extra; that extra now resolves run-hy8 from PyPI rather than from Git.

## Finalization retries

Finalization checks PyPI before dispatching publication. If the version already exists,
it skips dispatch; if publication for that SHA is active, it also skips duplicate work.
A missing version with no active run can be dispatched again after a failed attempt.
Unexpected PyPI responses or lookup timeouts fail visibly rather than guessing. Existing
tag/SHA and stable-release checks still apply before these recovery decisions.
