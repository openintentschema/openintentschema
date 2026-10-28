# Open Intent Schema (OIS)

**What was asked, what was built, and the proof in between.**

OIS is an open, vendor-neutral data standard that links requirements to independent
evidence that software does what was asked, even when AI agents built it. It records
intents and their acceptance criteria, the artifacts produced, who or what produced them
and with which context, the evidence from test runs, the decisions at quality gates, and
the findings when something goes wrong. A signed Quality Passport bundles all of it for a release.

Think of it as an SBOM for requirements.

## Status

Working draft v0.1 (draft 4), open for discussion with design partners. Any part may change
before 1.0. See `specification/` for the specification, `schema/` for the JSON Schema and `examples/`
for a complete worked example.

## Reuse before invention

OIS builds on Gherkin and EARS (criteria), in-toto and DSSE (passport and signing),
Sigstore (keyless signing), SLSA (build provenance), CloudEvents (events), W3C Trace Context,
JSON Schema 2020-12 and RFC 8785 (canonical JSON for digests).

## Conformance

Producers claim a level: Level 1 Observe (emit records for existing outputs), Level 2
Intent-aware (read intents, record complete context), Level 3 Attested (signed bundles and
passports, verifiable identity). A validator checks the schema and integrity rules R1–R15.

## Licenses

Schema, code and fixtures: Apache-2.0. Specification text: CC BY 4.0.

## Governance

See `GOVERNANCE.md`. The editors intend to transfer the specification to a neutral foundation.
