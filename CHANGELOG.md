# Changelog

All notable changes to this project. Format: Keep a Changelog 1.1.
Versions follow Semantic Versioning; no release is tagged yet.

## [Unreleased]

### Changed
- 2026-11-08: Adopted the portfolio standard v2. README opens with the
  question, headline, field, job family and verdict (Functional), then
  reproduce, lifecycle and a layout table mapping the locked file
  names to their roles. AUDIT.md is the report: it now scores every
  hypothesis and adds "How the evidence is protected" and "Threats to
  validity"; its grade moved out of the public repo (grades are
  internal), and each deduction's substance stays as a threat to
  validity. A test pins the SHA-256 of PREREGISTRATION.md as committed
  at aa4e555. CI runs with read-only permissions and checks that
  RESULTS.md and results/ regenerate unchanged from the raw evidence.
  CodeQL and Dependabot added; Dependabot does not bump the langchain
  and langchain-core pins, because the pins are part of the result.

### Fixed
- 2026-11-08: CI invokes `python -m pytest` (DECISIONS D10).

### Added
- 2026-11-08: Results of the one registered suite pass: H1 CONFIRMED,
  H2 REFUTED (wall ratio 0.459), H3 CONFIRMED (68c43f0).
- 2026-11-08: Harness: shared core and native arm imported verbatim
  from the sibling study (hash-gated), LangChain LCEL arm, suite,
  analysis, tests (d6ad6b7).
- 2026-11-08: Pre-registration (aa4e555), before any code or run.
