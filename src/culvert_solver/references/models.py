"""Immutable provenance for equations and future empirical coefficient records."""

from dataclasses import dataclass

from ..exceptions import InvalidInputError


@dataclass(frozen=True, slots=True)
class SourceReference:
    """A specific publication locator and its documented applicability.

    ``locator`` should identify an equation, table, figure or section. Free-text
    applicability is provenance, not executable range enforcement; coefficient
    models must add explicit shape/configuration/range validation in Phase 4.
    ``url`` may be omitted for controlled manufacturer specifications or other
    non-public documents; publication, edition, and locator remain mandatory.
    """

    source_id: str
    publication: str
    edition: str
    locator: str
    url: str | None
    applicability: str
    notes: str = ""

    def __post_init__(self) -> None:
        for name in ("source_id", "publication", "edition", "locator", "applicability"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise InvalidInputError(f"{name} must be nonempty text.")
        if self.url is not None and not self.url.startswith(("https://", "http://")):
            raise InvalidInputError("url must be an HTTP(S) source link.")
