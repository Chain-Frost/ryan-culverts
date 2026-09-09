# Reference intake

This is an initial reference intake note, not the completed Phase 0 literature
review. The authoritative source hierarchy remains in the updated work plan.

## alejandroechev/culvertflow

User-supplied repository: https://github.com/alejandroechev/culvertflow

Reviewed the README and selected engine sources on the `master` branch on
2026-09-06. These links are mutable; pin a commit before formal comparison or reuse.

The [README](https://github.com/alejandroechev/culvertflow#readme) describes a
TypeScript hydraulic engine separated from a browser UI, rating curves, and inlet
coefficient tables. It states MIT licensing; verify the applicable licence text
and attribution before copying any code. No code has been imported.

Useful as a secondary implementation reference for module separation, coefficient
organisation and eventual reporting ideas. It is not a primary hydraulic authority
or a validated benchmark for this project.

Specific observations from the source:

- [Outlet control](https://github.com/alejandroechev/culvertflow/blob/master/packages/engine/src/outlet-control.ts)
  uses feet/cfs and a fixed critical-depth approximation of `0.6 * D`; it does not
  solve a free-surface profile in that function. Review equations against primary
  references and derive SI forms before considering any adaptation.
- [Controlling headwater](https://github.com/alejandroechev/culvertflow/blob/master/packages/engine/src/controlling.ts)
  simply selects the maximum of inlet and outlet headwaters. This does not implement
  the physical-consistency checks required by Phase 6 of our plan.
- [Coefficient tables](https://github.com/alejandroechev/culvertflow/blob/master/packages/engine/src/reference.ts)
  provide a compact shape/inlet mapping, but lack the edition, equation/table and
  applicability metadata required by our plan. Elliptical entries repeat circular
  values; validate each relationship independently before use.

This limited source review did not execute the project, validate its coefficients,
or audit its complete test suite. It does not change the decision to retire our
old `culvertflow` package; the similarly named external project is a separate codebase.
