---
title: Core concepts
description: The OIS record types, how they reference each other, and the conformance levels.
---

OIS describes software delivery with six record types, the criterion embedded in an intent, and
the bundle as transport container. All records are JSON and share the fields `ois`, `type`, `id` and `createdAt`. The
normative definitions are in [section 4 of the specification](/specification/core-data-model/).

## Records

| Record | States | Example |
| --- | --- | --- |
| **Intent** | What a change must achieve, with acceptance **criteria**. Versioned; immutable once approved. | "Customers change their address in the portal", criterion AC-2 in EARS |
| **Artifact** | Something produced: code, a test, a contract, a dataset, a document or a build. Referenced by location and digest, never stored. | The test file `tests/address.spec.ts` at a commit |
| **Actor** | A human, an AI agent or a tool. Agents name their model. | A QE agent on model B, version 2.1 |
| **Evidence** | That one test run produced one result for one criterion, and whether the test was derived from the intent, the implementation or neither. | AC-2 passed, derived from the intent |
| **Decision** | The outcome of a gate, bound to the content it was made on. | The product owner approves an intent version, bound to its digest |
| **Finding** | A defect or incident; resolved only by an independent decision. | A postcode case nobody required breaks the premium calculation |

A **bundle** carries several records together. A **Quality Passport** is an in-toto attestation
that collects every record behind a release.

## References and integrity rules

Records point to each other by URI: an evidence record names a criterion as
`<intent-id>@<version>#<key>`, its test and the code under test. Because every artifact names
its producer and what the producer was given (`context`), a validator can check claims that would
otherwise rest on trust, for example:

- **R4, derivation:** a test that claims to be derived from the intent saw the criterion and no
  code.
- **R5, independence:** a test derived from the intent was not written by the actor that wrote
  the code.
- **R1, approval:** an approved intent is bound to its approval by a digest, so an edit after
  approval is detectable.

All rules are in [section 5](/specification/relationships-and-integrity-rules/).

## Versions and history

Nothing is deleted. An approved intent changes only by a new version; evidence for an older
version counts for a newer one only if the criterion is unchanged, which a digest shows
([section 6.3](/specification/identifiers-versioning-and-digests/)). Wrong evidence is revoked by
a decision, and findings are superseded by new records.

## Conformance levels

| Level | Name | What a producer does |
| --- | --- | --- |
| 1 | Observe | Emits artifact and evidence records for its own outputs. `derivedFrom` may be `unknown`. |
| 2 | Intent-aware | Reads intents, references criteria and records the complete context of what it produces. |
| 3 | Attested | Carries an identity and signs the bundles and passports it emits. |

A validator checks records against the schema and the integrity rules and reports each problem
as a violation, warning or info, with its rule. The
[conformance test suite](/conformance/) defines what it must report.
