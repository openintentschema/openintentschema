# Open Intent Schema (OIS)

**What was asked, what was built, and the proof in between.**

OIS is an open, vendor-neutral data standard that links requirements to independent
evidence that software does what was asked, even when AI agents built it. It records
intents and their acceptance criteria, the artifacts produced, who or what produced them
and with which context, the evidence from test runs, the decisions at quality gates, and
the findings when something goes wrong. A signed Quality Passport bundles all of it for a release.

Think of it as an SBOM for requirements: an SBOM lists what software contains; OIS states what
it must do and how that is proven.

**New here?** [Getting started](https://openintentschema.io/getting-started/) turns the JUnit XML of an existing
pipeline into OIS records in about 15 minutes.

## Status

Specification v0.1, working draft 5, open for discussion with design partners (see the change
history in the specification). Any part may change before 1.0.

## Repository layout

| Path | Content |
| --- | --- |
| [`specification/`](specification/) | The specification (normative and informative sections) |
| [`schema/`](schema/) | `ois.schema.json`, the normative JSON Schema 2020-12 (Appendix B) |
| [`examples/`](examples/) | The worked example of Appendix A |
| [`fixtures/`](fixtures/) | The conformance test suite: valid and invalid documents with the reports a validator must give |
| [`profiles/`](profiles/) | The registry of profiles (section 10.2), with an example profile for regulated industries |
| [`site/`](site/) | The website [openintentschema.io](https://openintentschema.io): getting started, reference pages, the published schema |
| [`.github/`](.github/) | CI for examples, fixtures and the website, and the workflow that records the keyless signed fixture; issue and pull request templates; contributing guide, Code of Conduct and security policy |

## Conformance

Producers claim a level: Level 1 Observe (emit records for existing outputs), Level 2
Intent-aware (read intents, record complete context), Level 3 Attested (signed bundles and
passports, verifiable identity).

A validator checks the schema and the integrity rules R1–R15 of section 5 and reports each
problem with its rule and level. The conformance fixtures are the test suite it must pass; they
also cover the rules R16 and R17 and the clarifications proposed in the open RFCs.

The reference tools, one command `ois` with the validator (`ois validate`) and the tools that
write records (test report and Cucumber adapters, intents, records, passports, intent coverage) and sign and
verify them (DSSE with own keys, Sigstore keyless), live in
[openintentschema/tools](https://github.com/openintentschema/tools) and are published on
PyPI as [`ois-tools`](https://pypi.org/project/ois-tools/) and as the container image
`ghcr.io/openintentschema/ois-tools`, for projects in any language. A second implementation of
the validator, for Node.js, lives in [openintentschema/tools-js](https://github.com/openintentschema/tools-js)
and is published on npm as [`ois-tools`](https://www.npmjs.com/package/ois-tools).

## Reuse before invention

OIS builds on Gherkin and EARS (criteria), in-toto and DSSE (passport and signing),
Sigstore (keyless signing), SLSA (build provenance), CloudEvents (events), W3C Trace Context,
JSON Schema 2020-12 and RFC 8785 (canonical JSON for digests).

## Contributing

Changes to the data model, rules, schema, conformance levels or passport format start as an
[RFC issue](https://github.com/openintentschema/openintentschema/issues?q=label%3Arfc); editorial
fixes go straight to a pull request. See [CONTRIBUTING.md](.github/CONTRIBUTING.md) and
[GOVERNANCE.md](GOVERNANCE.md). Everyone taking part follows the
[Code of Conduct](.github/CODE_OF_CONDUCT.md). Security issues: [SECURITY.md](.github/SECURITY.md).

## Licenses

Schema, code and fixtures: Apache-2.0 ([LICENSE](LICENSE)). Specification text: CC BY 4.0
([LICENSE-docs](LICENSE-docs)).

## Governance

Editors decide by rough consensus after an open RFC process; see [GOVERNANCE.md](GOVERNANCE.md)
and [MAINTAINERS.md](MAINTAINERS.md). The editors intend to transfer the specification to a
neutral foundation.
