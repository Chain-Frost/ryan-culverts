# Public API and compatibility policy

## Supported import boundary

Names listed in `culvert_solver.__all__` and documented across the [API reference](api.md) are
the package's public Python surface. Import those names from `culvert_solver`; direct
imports from package submodules are not a compatibility promise.

The package version is available as `culvert_solver.__version__` and comes from the
installed distribution metadata. A source checkout imported before installation reports
`0+unknown` rather than guessing a release version.

## Alpha stability

The calendar-versioned package is still alpha software. Public names are intentional, but
hydraulic behaviour marked provisional may change when stronger primary evidence or
validation requires a correction. A change that can safely preserve the old interface
should use a deprecation notice for at least one packaged version. Incorrect or unsafe
engineering behaviour may be removed immediately and will be called out in the changelog
and release notes.

Adding a new optional field or public name is normally compatible. Renaming or removing a
public name, changing units, changing default coefficient selection, or changing the
meaning of a result field is a compatibility change and must be documented explicitly.

## Version and release records

`pyproject.toml` is the version authority. User-visible changes are summarised in the
[changelog](changelog.md), while version-specific evidence and limitations are retained
in the maintained [release notes](releases/README.md).
