# Research intake status

This directory contains reviewed extracts derived from the primary publications
under `reference_docs/`. The PDFs are evidence inputs; the Markdown extracts are
not executable defaults until their transcription and applicability are tested.

The superseded root-level research prompt and two raw agent reports were removed during
the `0.2.0` release cleanup. One report was incomplete and the other contained non-durable
tool citations from an older baseline. Their reviewed findings are represented by the
source-pinned records below; the original intake remains available in Git history.

Current reviewed extracts:

- [`local_evidence_inventory.md`](local_evidence_inventory.md): SHA-256 and review/
  rejection/pending status for evidence consolidated under `reference_docs/`.
- [`fhwa_box_inlets.md`](fhwa_box_inlets.md): corrected FHWA-HRT-06-138 Tables
  11 and 12, exact local PDF locators, applicability limits, and the Appendix D
  configuration boundary. Implementation still requires typed geometry and inlet rules.
- [`nchrp734_coefficients.md`](nchrp734_coefficients.md): initial slipline and
  multi-barrel findings from NCHRP 734. The report's duplicated final Table 3-2 row
  label is resolved by the immediately preceding narrative but retained as a source typo;
  the separate HY-8 developer correction blocks use of the original embedded coefficients.
- [`fixture_candidates.md`](fixture_candidates.md): the complete Bodhaine example audit,
  selected corrected-box fixtures, and the Austroads worked-example limitation.

The authoritative task status is in
[`docs/work/2026-09-06-phase-0-to-10-remediation.md`](../work/2026-09-06-phase-0-to-10-remediation.md).
CS-001 closed the research gate on 2026-09-09. The resulting deferred implementation
work is tracked separately; research completion is not combined-solver validation.
