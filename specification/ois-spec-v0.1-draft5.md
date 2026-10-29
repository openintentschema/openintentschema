# Open Intent Schema Specification v0.1

Oct 25, 2026 · @Louis Stark

## Status of this document

This is working draft 0.1 of the Open Intent Schema (OIS), published for discussion with design partners. It is not stable: any part may change before version 1.0.

- **Version:** 0.1, working draft 5 (see change history).
- **Name:** "Open Intent Schema" is a working title, pending a trademark check.
- **Editors:** listed in the byline. Further editors join through the governance process.
- **License:** this text is licensed under CC BY 4.0. The JSON Schema and reference code are licensed under Apache 2.0. A patent non-assertion covenant for implementers is planned and will be chosen with legal advice, following the practice of specifications hosted at the Linux Foundation.
- **Feedback:** as RFC issues at <https://github.com/openintentschema/openintentschema/issues>; GOVERNANCE.md describes the process.
- **Governance:** changes follow an open RFC process. Contributions require a Developer Certificate of Origin sign-off. RFCs are decided by rough consensus of the editors and recorded in the repository, where GOVERNANCE.md, CONTRIBUTING.md and LICENSE are authoritative. The editors intend to transfer the specification to a neutral foundation.

Sections marked *normative* define requirements for conforming implementations. Sections marked *informative* explain and give examples, but define no requirements.

### Change history

| Draft | Date | Changes |
| --- | --- | --- |
| 0.1-draft.1 | 2026-10-24 | Initial draft. |
| 0.1-draft.2 | 2026-10-25 | Finding record (first named observation); context recorded by the runtime and attestation rule; evidence revocation; gate registry; targets for non-functional criteria; language tags; passport bundles and scope; build inputs; reference method for intent coverage; carry-over fix in R4; forward-compatibility rule; change history. |
| 0.1-draft.3 | 2026-10-25 | Actor identity for signature attribution; subject digests on decisions; Level 3 aligned with R12; observation renamed to finding; validator report levels; releases with several builds; R14 clarified; example completed with build artifact and signed bundle. |
| 0.1-draft.4 | 2026-10-25 | Intent digest excludes status; R10 compares content without status; Level 3 wording for multi-signature bundles; pseudonymous identities for humans; R15 for withdrawn intents; diverse coverage variant; quick start for Level 1. |
| 0.1-draft.5 | in progress | Appendix A uses intent version 1, so the example carries no history it does not show (R10); A.2 names all four records the passport adds, including the QE lead; rule identifier `schema` for Appendix B (RFC #1); R16, release decision in a passport (RFC #2); R17, intent and criterion digests, with computed digests in Appendix A (RFC #3); the R10 exception limited to intents (RFC #5); identifiers under openintentschema.io (RFC #6); coverage over several intents (RFC #7); signature verification, key ids and the rule identifier `signature` (RFC #8). |

## 1. Introduction (informative)

OIS defines a vendor-neutral data model that links what was required (the intent) to what was produced and to the evidence that it meets the requirement. It works for artifacts made by humans, AI agents and tools alike.

### 1.1 Problem

AI agents now write requirements, code and tests. Teams can no longer show, in a verifiable way, that a delivered feature does what was asked:

- Requirements, code, tests and results live in separate tools with no verifiable link between them.
- Generated tests often confirm what was built rather than what was required.
- When one model reviews another model's output, both may share the same blind spots.
- Regulated organizations must increasingly document how AI is used and controlled in software delivery. This evidence is collected by hand or not at all.

### 1.2 Goals

- Record intents and their acceptance criteria as versioned, immutable records.
- Record who or what produced each artifact, and what context the producer could see.
- Record evidence that links each criterion to a concrete test run, including whether the test was derived from the intent or from the implementation.
- Record human and automated decisions at quality gates.
- Bundle these records into a signed Quality Passport for a release.
- Reuse existing standards wherever possible.

### 1.3 Non-goals

- OIS does not define how risk, coverage or trust scores are computed. It only defines where such values are recorded. Appendix D offers one informative reference method for intent coverage, so that at least one comparable figure exists.
- OIS does not prescribe tools, agents, workflows or user interfaces.
- OIS does not interpret laws or regulations. Section 13 maps fields to frameworks for orientation only.
- OIS does not store artifacts. Records reference artifacts by location and digest.

## 2. Conventions and terminology (normative)

The key words MUST, MUST NOT, REQUIRED, SHALL, SHALL NOT, SHOULD, SHOULD NOT, RECOMMENDED, NOT RECOMMENDED, MAY and OPTIONAL are to be interpreted as described in BCP 14 (RFC 2119 and RFC 8174) when, and only when, they appear in all capitals.

JSON terms (object, array, string, number) follow RFC 8259. Timestamps are strings in RFC 3339 format with a time zone offset.

| Term | Definition |
| --- | --- |
| Record | A JSON object of one of the six record types defined in section 4. |
| Intent | A versioned statement of what a change must achieve, with its acceptance criteria. |
| Criterion | One verifiable acceptance criterion inside an intent. |
| Artifact | Anything produced during delivery: code, a test, a contract, a dataset, a document. OIS references it, it does not store it. |
| Actor | A human, an AI agent or a tool that produces artifacts, records evidence or makes decisions. |
| Evidence | A record that a specific test run produced a specific result for a specific criterion. |
| Decision | A record of an approval, rejection or gate outcome, made by an actor. |
| Finding | A record of a defect or incident: behaviour that violates a criterion, or behaviour that nobody required. |
| Bundle | A JSON object that transports several records together. |
| Quality Passport | A signed attestation that collects the intents, evidence, decisions and open findings behind a release. |
| Producer | An implementation that creates OIS records. |
| Consumer | An implementation that reads OIS records. |
| Digest | A cryptographic hash of content, expressed as a map from algorithm name to hex value. |

## 3. Design principles (informative)

Six principles shape every rule in this specification.

1. **Actor-neutral.** Humans, AI agents and tools are all actors, described by the same record type. This makes separation of duties checkable: did the same actor produce both the code and the test that verifies it?
2. **Evidence records its origin.** Every evidence record states whether its test was derived from the intent or from the implementation. "Was the requirement tested, or only the code?" becomes a data field.
3. **References, not copies.** Artifacts stay where they live (Git, an issue tracker, a test tool). OIS stores their location and digest, so any later change to an artifact is detectable.
4. **Versioned and immutable.** An approved intent version never changes. A change creates a new version, and evidence bound to an older version is identifiable as stale.
5. **Small core, extensible edges.** The core covers what every implementation needs. Industry needs are added through profiles and namespaced extensions.
6. **Reuse before invention.** OIS builds on Gherkin, EARS, in-toto, DSSE, CloudEvents, W3C Trace Context and JSON Schema instead of defining its own equivalents.

OIS does not require that an intent exists before the code. Existing systems can start by recording their current tests as evidence with `derivedFrom: unknown` or `implementation`, and by recording defects as findings. Intents are then added for each change, and intent coverage grows from an honest baseline.

## 4. Core data model (normative)

OIS defines six record types (intent, artifact, actor, evidence, decision, finding), one embedded type (criterion) and one transport container (bundle). Fields not listed here MUST NOT appear at the top level of a record. Additional data goes into `extensions` (section 10).

### 4.1 Common fields

Every record MUST carry these fields.

| Field | Type | Req. | Description |
| --- | --- | --- | --- |
| `ois` | string | REQUIRED | Specification version. MUST be `"0.1"` for this version. |
| `type` | string | REQUIRED | One of `intent`, `artifact`, `actor`, `evidence`, `decision`, `finding`. |
| `id` | URI | REQUIRED | Identifier of the record (section 6.1). |
| `createdAt` | timestamp | REQUIRED | When the record was created. |
| `profiles` | array of URI | OPTIONAL | Profiles the record conforms to (section 10.2). |
| `trace` | object | OPTIONAL | W3C Trace Context with `traceId` and optional `spanId`. |
| `extensions` | object | OPTIONAL | Namespaced extension data (section 10.1). |

**Shared types:**

- **Ref:** a URI string that identifies a record or artifact. Versioned and criterion references follow section 6.2.
- **Digest:** an object that maps algorithm names to lowercase hex values, for example `{"sha256": "9f86d0..."}`. This is the in-toto DigestSet format.
- **Measurement:** an object with `name` (string, REQUIRED), `value` (number, string or boolean, REQUIRED), `unit` (string, OPTIONAL) and `method` (URI, OPTIONAL). The method identifies how the value was computed; OIS does not define methods.

### 4.2 Intent

An intent states what a change must achieve. Each version is a separate, immutable record once approved.

| Field | Type | Req. | Description |
| --- | --- | --- | --- |
| `version` | integer ≥ 1 | REQUIRED | Increases by exactly 1 per new version. |
| `title` | string | REQUIRED | Short human-readable title. |
| `status` | enum | REQUIRED | `draft`, `approved` or `withdrawn`. Supersession is derived, not stored (section 6.3). |
| `language` | string | OPTIONAL | BCP 47 language tag of `title` and of criteria that set no language of their own. |
| `criteria` | array of Criterion | REQUIRED | At least one criterion. |
| `producedBy` | Ref | RECOMMENDED | The actor that drafted this version, for example a requirement agent. |
| `source` | URI | OPTIONAL | Origin, for example an issue tracker item. |
| `supersedes` | Ref | OPTIONAL | Versioned reference to the previous version. |
| `risk` | enum | OPTIONAL | `low`, `medium`, `high` or `critical`. How it is assessed is out of scope. |
| `digest` | Digest | REQUIRED when approved | Digest of the intent's canonical form (section 6.4). |

**Criterion** (embedded in an intent):

| Field | Type | Req. | Description |
| --- | --- | --- | --- |
| `key` | string | REQUIRED | Unique within the intent across all its versions, for example `AC-2`. Pattern `[A-Za-z0-9._-]{1,64}`. |
| `statement` | string | REQUIRED | The criterion text. |
| `notation` | enum | REQUIRED | `gherkin`, `ears` or `text`. |
| `kind` | enum | REQUIRED | `functional` or `non-functional`. |
| `language` | string | OPTIONAL | BCP 47 language tag of `statement`. Overrides the intent's `language`. |
| `target` | object | RECOMMENDED for non-functional criteria | Measurable threshold: `metric` (string), `operator` (`lt`, `lte`, `gt`, `gte` or `eq`), `value` (number) and optional `unit`. An evidence measure whose `name` equals `metric` shows whether the target is met. |
| `criticality` | enum | OPTIONAL | `low`, `medium` or `high`. |
| `digest` | Digest | REQUIRED when the intent is approved | Digest of the criterion's canonical form (section 6.4). |

### 4.3 Artifact

An artifact record references something produced during delivery. It never contains the artifact itself.

| Field | Type | Req. | Description |
| --- | --- | --- | --- |
| `kind` | enum | REQUIRED | `code`, `test`, `contract`, `dataset`, `document`, `build` or `other`. |
| `location` | URI | REQUIRED | Where the artifact or its container lives, including the revision, for example a Git repository at a commit. For packages, a Package URL (purl) is RECOMMENDED. |
| `path` | string | OPTIONAL | Path of the artifact inside the container at `location`, for example a file in a repository. |
| `digest` | Digest | REQUIRED | Digest of the artifact's content. |
| `producedBy` | Ref | REQUIRED | Reference to the producing actor (section 6.2). |
| `inputs` | array of Ref | RECOMMENDED for builds | Artifacts this artifact was made from, for example the code commits a build contains. SLSA provenance for the same build MAY be referenced in `extensions`. |
| `context` | array of Ref | OPTIONAL | Everything the producer was given as input. If present, it MUST be complete (section 5). |
| `contextRecordedBy` | Ref | RECOMMENDED | The actor that observed and recorded `context`, usually the runtime or gateway that ran the producer. The context counts as attested only under the conditions of R12; otherwise it is self-declared. |
| `classification` | enum | REQUIRED for datasets | `synthetic`, `anonymized` or `production`. |
| `mediaType` | string | OPTIONAL | IANA media type of the content. |

### 4.4 Actor

An actor is a human, an AI agent or a tool. Each actor version is a separate record.

| Field | Type | Req. | Description |
| --- | --- | --- | --- |
| `kind` | enum | REQUIRED | `human`, `agent` or `tool`. |
| `name` | string | REQUIRED | Display name. For humans, a pseudonym is RECOMMENDED (section 12). |
| `version` | string | REQUIRED for agents and tools | Version of the actor. |
| `model` | object or array | REQUIRED for agents | `provider`, `name` and `version` of the underlying model. Agents that route between several models give an array of such objects. Where a vendor does not disclose the model, `name` MAY be `undisclosed`. |
| `identity` | object | RECOMMENDED, REQUIRED for Level 3 | How signatures are attributed to this actor: `issuer` (URI) and `subject` of a certificate identity, or `keyId` for a long-lived key. Agents and tools SHOULD use workload identities such as SPIFFE IDs. For humans, `subject` MUST NOT be an e-mail address or another direct identifier; use a pseudonymous subject or omit `identity` (section 12). |
| `operator` | string | OPTIONAL | Team or organization responsible for the actor. |
| `autonomyLevel` | integer 0–3 | OPTIONAL | See below. |

When an agent's model, system instructions or tool set change, producers MUST record a new actor version.

Autonomy levels have a fixed meaning. How a level is assigned is out of scope.

| Level | Name | Meaning |
| --- | --- | --- |
| 0 | Suggest | The actor only proposes. A human performs the action. |
| 1 | Full review | Every output is reviewed by a human before it takes effect. |
| 2 | Sampled review | Outputs take effect after risk-based or sampled human review. |
| 3 | Autonomous within policy | Outputs take effect when all policy gates pass. |

### 4.5 Evidence

An evidence record states that one test run produced one result for one criterion.

| Field | Type | Req. | Description |
| --- | --- | --- | --- |
| `criterion` | Ref | REQUIRED | Criterion reference (section 6.2). |
| `test` | Ref | REQUIRED | The test artifact (kind `test`). |
| `subject` | Ref | RECOMMENDED | The implementation artifact under test. |
| `inputs` | array of Ref | OPTIONAL | Further inputs such as datasets or configuration. |
| `derivedFrom` | enum | REQUIRED | `intent`, `implementation` or `unknown`: what the test was derived from. The value is a claim that validators check against R4 and R5 (section 5). |
| `result` | enum | REQUIRED | `pass`, `fail`, `skipped` or `error`. |
| `observedAt` | timestamp | REQUIRED | When the result was observed. |
| `recordedBy` | Ref | REQUIRED | Reference to the actor that ran the test and recorded the result. |
| `measures` | array of Measurement | OPTIONAL | For example a mutation score. |
| `run` | URI | OPTIONAL | Link to the pipeline or test run. |

### 4.6 Decision

A decision records the outcome of a gate.

| Field | Type | Req. | Description |
| --- | --- | --- | --- |
| `gate` | string | REQUIRED | Gate name. Well-known gates are listed below; other names are allowed. |
| `subject` | Ref | REQUIRED | What was decided on: an intent version, an artifact, a finding or a release. |
| `subjectDigest` | Digest | RECOMMENDED, REQUIRED for `intent-approval` and `release` | Digest of the subject as it was when the decision was made, so that the decision binds to content and not only to an identifier. |
| `outcome` | enum | REQUIRED | `approved`, `rejected`, `passed`, `blocked` or `waived`. |
| `decidedBy` | Ref | REQUIRED | Reference to the deciding actor. |
| `decidedAt` | timestamp | REQUIRED | When the decision was made. |
| `policy` | object | OPTIONAL | Policy evaluated: `id` (URI), `version` and optional `digest`. |
| `evidence` | array of Ref | OPTIONAL | Evidence records considered. |
| `assessments` | array of Measurement | OPTIONAL | Values considered, for example a risk score. |
| `rationale` | string | REQUIRED when outcome is `waived` | Why the decision was made. |

**Well-known gates:**

| Gate | Subject | Outcomes | Meaning |
| --- | --- | --- | --- |
| `intent-approval` | Intent version | `approved`, `rejected` | The intent is accepted as the measure for the work. |
| `design-approval` | Artifact of kind `contract` or `document` | `approved`, `rejected` | The design or contract is accepted. |
| `merge` | Artifact of kind `code` | `passed`, `blocked`, `waived` | The change may enter the main line. |
| `release` | Artifact of kind `build`. A release made of several builds uses one build artifact whose `inputs` list the parts. | `approved`, `rejected`, `passed`, `blocked`, `waived` | The build may be released. |
| `evidence-revocation` | Evidence record | `rejected` | The evidence is withdrawn and MUST NOT be counted (section 6.3). `rationale` is REQUIRED. |
| `finding-resolution` | Finding record | `approved`, `rejected` | The resolution listed in `resolvedBy` is confirmed by an actor other than the producers of that resolution (R14). |

### 4.7 Finding

A finding records a defect or incident: behaviour that violates a criterion, or behaviour that nobody required. It is the entry point of the learning loop, and it suits existing systems, where defects usually come before intents.

| Field | Type | Req. | Description |
| --- | --- | --- | --- |
| `criterion` | Ref | OPTIONAL | The criterion that was violated, if one exists. |
| `intent` | Ref | OPTIONAL | Versioned reference to the intent the finding concerns. |
| `subject` | Ref | RECOMMENDED | The artifact in which the behaviour was observed, usually a build or code. |
| `source` | enum | REQUIRED | `production`, `test`, `review`, `customer` or `other`. |
| `severity` | enum | REQUIRED | `low`, `medium`, `high` or `critical`. |
| `summary` | string | REQUIRED | Short description of the behaviour. MUST NOT contain personal data. |
| `observedAt` | timestamp | REQUIRED | When the behaviour was observed. |
| `reportedBy` | Ref | REQUIRED | The reporting actor (section 6.2). |
| `ticket` | URI | OPTIONAL | Issue tracker item. |
| `cause` | enum | OPTIONAL | Root cause once classified: `spec-gap`, `implementation`, `test-gap`, `gate-gap`, `review` or `unknown`. |
| `resolvedBy` | array of Ref | OPTIONAL | Intent versions, artifacts or evidence that resolve the finding. |
| `supersedes` | Ref | OPTIONAL | The previous finding record this one replaces. |

Rules:

- At least one of `criterion`, `intent` or `subject` MUST be present.
- Findings are immutable like every record. To classify or resolve one, a producer records a new finding with `supersedes` pointing to the previous one. The last record in the chain is the current finding. A finding MUST have at most one successor, and a resolution listed in resolvedBy counts only once a decision with gate finding-resolution confirms it (R14).
- A finding with `cause` `spec-gap` SHOULD be resolved by a new intent version whose new criterion describes the expected behaviour. The fix is then an artifact, and its evidence follows the normal path.
- A finding with `cause` `implementation` or `test-gap` SHOULD be resolved by evidence with result `pass` for the violated criterion, recorded after the fix.

```json
{
  "ois": "0.1", "type": "finding", "id": "https://ois.acme.example/findings/FND-18",
  "createdAt": "2026-11-03T07:40:00Z",
  "intent": "https://ois.acme.example/intents/INT-142@1",
  "subject": "https://ois.acme.example/artifacts/ART-305",
  "source": "production",
  "severity": "high",
  "summary": "Address change to a Liechtenstein postcode aborts the premium calculation",
  "observedAt": "2026-11-02T18:12:00Z",
  "reportedBy": "https://ois.acme.example/actors/support-4b1e",
  "ticket": "https://jira.acme.example/browse/PORTAL-1302",
  "cause": "spec-gap"
}
```

### 4.8 Bundle

A bundle transports records together. It has the fields `ois`, `type` (value `bundle`), `id`, `createdAt` and `records` (array of records, REQUIRED). A bundle adds no meaning beyond its contents and MAY be signed (section 8.3).

## 5. Relationships and integrity rules (normative)

Records reference each other by URI. The rules below make those references checkable, above all the independence of a test from the code it verifies.

&#91;embedded content: References checked by the integrity rules\]

An evidence record points to a criterion, a test and the code under test. Because both artifacts name their producers, and the test names its context, a validator can check that the test came from a different actor and never saw the code.

| Rule | Name | Requirement |
| --- | --- | --- |
| R1 | Approval | An intent version with status `approved` MUST be the subject of a decision with gate `intent-approval` and outcome `approved`, whose `subjectDigest` equals the intent's `digest`. Its `decidedBy` actor SHOULD be human. |
| R2 | Criterion references | Every criterion reference MUST resolve to a criterion with that `key` in that intent version. |
| R3 | Evidence targets | `test` MUST reference an artifact of kind `test`. `subject`, if present, MUST reference an artifact of kind `code` or `build`. |
| R4 | Derivation | `derivedFrom` MAY be `intent` only if the test artifact has a `context` that includes the referenced criterion, or any version of the same intent in which the criterion with that `key` has the same digest, and includes no artifact of kind `code`. A declared `derivedFrom` that contradicts R4 or R5 is a violation. |
| R5 | Independence | `derivedFrom` MUST NOT be `intent` if the test and the subject were produced by actors with the same `id`, in any version. |
| R6 | Complete context | If an artifact lists a `context`, the list MUST contain every record and artifact the producer was given. Consumers MAY conclude that the producer had no access to anything not listed. |
| R7 | Stale evidence | Consumers MUST apply the stale evidence rule of section 6.3 before counting evidence for an intent version. |
| R8 | Production data | Validators MUST report a warning when an evidence record lists an input dataset classified as `production`. |
| R9 | Waivers | A decision with outcome `waived` MUST state a `rationale` and SHOULD be made by a human actor. |
| R10 | Resolution | Within a bundle or passport, every reference MUST resolve to exactly one record. No two records MAY share an `id` (and `version`, for intents and actors) while differing in content. For intents, content is compared without `status`, the intent `digest` and the criterion digests; a draft and its approved record therefore count as one record in two states. |
| R11 | Revocation | Evidence that is the subject of an `evidence-revocation` decision MUST NOT be counted for any intent version. The revocation MUST carry a `rationale`; the evidence record itself stays unchanged. |
| R12 | Context attestation | A context counts as attested only if `contextRecordedBy` differs from `producedBy` and the artifact record is carried in a bundle or passport signed by the `contextRecordedBy` actor. Otherwise validators MUST report the context as self-declared (warning), and consumers SHOULD give evidence with `derivedFrom: intent` that rests on it less weight. |
| R13 | Open findings | Validators MUST report a warning when a passport lists an intent that a current finding with severity `high` or `critical` references, directly or through one of its criteria, and that finding is not resolved under R14. |
| R14 | Finding chain | A finding MUST have at most one superseding record; validators MUST report a fork as a violation. A finding counts as resolved only if a decision with gate `finding-resolution`, outcome `approved` and the finding as `subject` exists, made by an actor that does not appear as `producedBy`, `recordedBy` or `decidedBy` in any record listed in `resolvedBy`. |
| R15 | Passport intents | Every intent listed in a passport's `intents` MUST be an approved version that is not withdrawn, and SHOULD be the latest approved version at `issuedAt`. |
| R16 | Release decision | A passport's records, or a bundle listed in `bundles`, MUST contain a decision with gate `release` and outcome `approved` or `passed` whose `subject` is an artifact of kind `build` with a digest that matches a digest of the statement's `subject`. |
| R17 | Digests | The `sha256` value of an intent's `digest` and of each criterion's `digest`, where present, MUST equal the value computed as section 6.4 describes. |

Validators check R1 to R5 and R8 to R17 from the records at hand; R17 also applies to a single record. R6 cannot be checked mechanically and rests on the producer's declaration, which is why signing (section 8.3) matters. R7 applies to consumers.

## 6. Identifiers, versioning and digests (normative)

### 6.1 Identifiers

- Every `id` MUST be an absolute URI (RFC 3986) and MUST NOT contain the characters `@` or `#`, which are reserved for references.
- Producers SHOULD use URIs under a domain they control, for example `https://ois.acme.example/intents/INT-142`.
- An intent `id` and an actor `id` identify the thing across all its versions. A single version is identified by the pair of `id` and `version`.
- Artifact, evidence and decision `id` values MUST be unique per record.
- Producers MUST NOT use unregistered URN namespaces. No URN namespace for OIS is registered yet (Appendix C).

### 6.2 References

| Form | Syntax | Used for |
| --- | --- | --- |
| Plain | `<id>` | Artifacts, evidence, decisions |
| Versioned | `<id>@<version>` | Intents, agents and tools |
| Criterion | `<intent-id>@<version>#<key>` | A criterion within one intent version |

Example of a criterion reference: `https://ois.acme.example/intents/INT-142@3#AC-2`. References to intents, agents and tools MUST use the versioned form. Human actors have no version and are referenced in plain form.

### 6.3 Versioning

- **Intents:** a draft version MAY change. Once a version has `status` `approved`, its record MUST NOT change. Any change creates a new version with `version` increased by 1 and `supersedes` pointing to the previous version.
- **Supersession:** a version is superseded when a newer approved version of the same intent exists. Consumers derive this; it is not stored.
- **Withdrawal:** an intent is withdrawn by recording a new version with `status` `withdrawn`.
- **Stale evidence:** evidence bound to version *n* remains current for a later version *m* only if version *m* contains a criterion with the same `key` and an identical criterion `digest`. Otherwise consumers MUST treat the evidence as stale for version *m*.
- **Actors:** `version` is a free-form string. Section 4.4 defines when a new version is required.
- **Specification:** during 0.x, versions MAY be incompatible. From 1.0, minor versions will only add optional fields.

**Revocation:** records are never deleted or edited. Evidence that turns out to be wrong, for example from a flaky test, is withdrawn by a decision with gate `evidence-revocation` whose `subject` is the evidence record (R11). Consumers MUST stop counting revoked evidence.

### 6.4 Digests

- Producers MUST include a `sha256` value, except for artifacts located in Git, which MAY use the `gitCommit` key alone. Consumers MUST support `sha256`.
- **Artifacts:** the digest is computed over the raw bytes of the artifact content.
- **Criteria:** the digest is computed over an object that contains only the criterion's `key`, `statement`, `notation`, `kind`, `target` and `language`, in JSON Canonicalization Scheme form (RFC 8785). `criticality` is excluded, so changing it does not make evidence stale.
- **Intents:** criterion digests are computed first. The intent digest is then computed over the intent record without its top-level `digest` and status members, in RFC 8785 form. It therefore stays the same when a draft becomes approved, and the intent-approval decision binds it through subjectDigest.
- Other records are protected by signing the bundle or passport that carries them (section 8.3).

## 7. Serialization (normative)

JSON is the canonical format. Records MUST be valid UTF-8 JSON (RFC 8259) and MUST validate against the JSON Schema in Appendix B.

- **YAML for authoring:** producers MAY author records in YAML 1.2, for example intents kept in a repository. YAML MUST be converted to JSON without loss before validation, digest computation or exchange. YAML features without a JSON equivalent, such as tags, merge keys or non-string keys, MUST NOT be used.
- **Strict core, open extensions:** consumers MUST reject records whose `ois` major version they do not support. Within a supported major version, consumers MUST accept unknown top-level fields added by a later minor version, MUST NOT remove them when storing or forwarding the record, and MUST reject fields that the declared version itself does not define. During 0.x, each minor version counts as its own major version. Unknown entries inside `extensions` MUST be ignored (section 10.1).
- **Timestamps:** producers SHOULD write timestamps in UTC.
- **Media type:** `application/vnd.ois+json` is proposed for exchange. It is not yet registered with IANA (Appendix C).
- **File names:** records SHOULD use the extension `.ois.json`, or `.ois.yaml` when authored in YAML.

When records are kept in a repository, this layout is RECOMMENDED:

| Path | Content |
| --- | --- |
| `.ois/intents/` | Intent records, one file per intent version |
| `.ois/actors/` | Actor records |
| `.ois/artifacts/` | Artifact records |
| `.ois/evidence/` | Evidence records |
| `.ois/decisions/` | Decision records |

Evidence and decisions MAY instead be stored outside the repository, for example in an artifact store, and exchanged as bundles.

## 8. Quality Passport (normative)

A Quality Passport is an in-toto attestation that collects every record behind a release, so that a third party can verify it without access to internal tools.

### 8.1 Statement

A passport MUST be an in-toto Statement v1. Its `subject` lists the released artifacts with their digests. Its `predicateType` identifies the OIS passport predicate.

```json
{
  "_type": "https://in-toto.io/Statement/v1",
  "subject": [
    { "name": "customer-portal", "digest": { "sha256": "<release digest>" } }
  ],
  "predicateType": "https://openintentschema.io/passport/v0.1",
  "predicate": { }
}
```

The predicate type URI serves a description of the predicate.

### 8.2 Predicate

| Field | Type | Req. | Description |
| --- | --- | --- | --- |
| `ois` | string | REQUIRED | Specification version, `"0.1"`. |
| `release` | object | REQUIRED | `name` and `version` of the release, optional `location` (URI). |
| `intents` | array of Ref | REQUIRED | Versioned references to the intents the release delivers. |
| `scope` | array of Ref | OPTIONAL | Criterion references the release is meant to deliver. When present, coverage methods count only these; when absent, all criteria of the listed intents. |
| `records` | array of records | REQUIRED | Records the passport relies on, embedded. MAY be empty when `bundles` carries them. |
| `bundles` | array of object | OPTIONAL | External bundles whose records count as embedded: each with `location` (URI) and `digest`. Keeps large passports small. |
| `assessments` | array of Measurement | OPTIONAL | Summary values such as intent coverage, each with its `method`. |
| `issuedBy` | Ref | REQUIRED | Reference to the actor that assembled the passport. |
| `issuedAt` | timestamp | REQUIRED | When the passport was assembled. |

Rules:

- A passport MUST be self-contained: every reference to an intent, actor, artifact, evidence or decision record MUST resolve to a record inside `records` or inside a bundle listed in `bundles` (R10). Consumers MUST verify the digest of each listed bundle before using its records.
- `records`, or a bundle listed in `bundles`, MUST contain a decision with gate `release` and outcome `approved` or `passed` for a build whose digest matches the statement's `subject` (R16).
- For every listed intent, `records` MUST contain the approved intent version and its `intent-approval` decision. This follows from R10, R15 and R1.

`records` SHOULD also include every current finding that references a listed intent, so that a passport does not hide known defects (R13).

### 8.3 Signing

- Passports SHOULD be wrapped in a DSSE envelope with payload type `application/vnd.in-toto+json` and signed. Level 3 conformance requires this (section 11).
- Bundles MAY be signed the same way, with payload type `application/vnd.ois+json`.
- Sigstore keyless signing is RECOMMENDED where public verification matters. Organizations MAY use their own keys instead.
- Consumers MUST verify the signature before relying on a signed passport, and MUST check that the subject digests match the released artifacts.
- A passport MAY be stored next to SLSA provenance for the same release. The two complement each other: SLSA states how it was built, the passport states that it does what was required.

A signature is attributed to an actor through that actor's `identity`. Consumers MUST treat a bundle or passport as signed by an actor only when the signer identity in the DSSE envelope or its certificate matches the actor's `identity`.

A key id for a long-lived key (`identity.keyId` and the DSSE `keyid`) SHOULD be the lowercase hexadecimal SHA-256 of the key's DER-encoded SubjectPublicKeyInfo. Which public keys and certificate identities a verifier trusts is its own decision, made outside OIS; a document cannot establish trust in a key. A bundle or passport counts as signed by an actor only if a signature verifies under a key the verifier trusts and that key's id or certificate identity matches the actor's `identity`.

An envelope counts as unsigned when it carries no signature, when its payload type is not `application/vnd.in-toto+json` for a passport or `application/vnd.ois+json` for a bundle, or when a signature under a trusted key does not verify.

A Sigstore bundle carrying a DSSE envelope is verified against the trusted roots the verifier chooses (certificate chain, transparency log entry, signature). Its signer is the certificate identity: the OIDC issuer (extension 1.3.6.1.4.1.57264.1.8) as `identity.issuer` and the subject alternative name as `identity.subject`, compared exactly.

Level 3 producers SHOULD also record each signature in a transparency log such as Sigstore Rekor. The log gives an independent time and order for every signature, so `observedAt` and `decidedAt` no longer rest on the producer's own clock.

## 9. Events (informative)

Implementations that exchange OIS records as events SHOULD use CloudEvents 1.0. This section is informative in v0.1 and is expected to become normative once design partners have tested it.

Each event carries one record as `data`, with `datacontenttype` `application/vnd.ois+json`. The `subject` attribute holds the record `id`, and `source` identifies the producer. Trace context MAY be propagated with the CloudEvents distributed tracing extension.

| Event type | Emitted when |
| --- | --- |
| `io.openintentschema.intent.approved` | An intent version reaches status `approved` |
| `io.openintentschema.intent.withdrawn` | An intent version with status `withdrawn` is recorded |
| `io.openintentschema.artifact.recorded` | An artifact record is created |
| `io.openintentschema.evidence.recorded` | An evidence record is created |
| `io.openintentschema.decision.recorded` | A decision record is created |
| `io.openintentschema.finding.recorded` | A finding record is created, including one that supersedes another |
| `io.openintentschema.passport.issued` | A Quality Passport is issued |

Event types carry the reverse-DNS prefix `io.openintentschema.` of the project domain, as CloudEvents recommends.

```json
{
  "specversion": "1.0",
  "type": "io.openintentschema.evidence.recorded",
  "source": "https://ci.acme.example/pipelines/portal",
  "id": "b6f1c2e0-5a8d-4c1e-9a77-2f3e8d1c0b44",
  "subject": "https://ois.acme.example/evidence/EV-9021",
  "time": "2026-10-20T14:32:05Z",
  "datacontenttype": "application/vnd.ois+json",
  "data": { "ois": "0.1", "type": "evidence", "id": "https://ois.acme.example/evidence/EV-9021" }
}
```

The `data` member is shortened here. A real event carries the complete record.

## 10. Extensions and profiles (normative)

Extensions add data, profiles add rules. Neither may change what the core means.

### 10.1 Extensions

- Each key in `extensions` MUST be a namespace: a reverse-DNS name such as `com.acme.jira` or an absolute URI. Its value MAY be any JSON value.
- Extensions MUST NOT change the meaning of core fields.
- Consumers MUST ignore namespaces they do not understand and MUST NOT reject a record because of them. When storing or forwarding a record, consumers MUST preserve all extensions unchanged, because digests cover them.
- Extensions are part of the record. For intents, they are therefore covered by the intent digest, and changing them requires a new version.

```json
"extensions": {
  "com.acme.jira": { "issueKey": "PORTAL-1187", "sprint": "2026-21" }
}
```

### 10.2 Profiles

- A profile is a published document, identified by an absolute URI, that adds constraints to the core. It can make optional fields required, narrow enumerations, require signing or define extension namespaces with their schemas.
- A profile MUST NOT relax any core requirement.
- A record that lists a profile in `profiles` MUST satisfy that profile.
- A profile SHOULD publish a JSON Schema that composes with Appendix B through `allOf`.
- Profiles are listed in a registry in the public repository.

As an example of the intended use, a profile for regulated industries could require `risk` on every intent, a human actor for every `intent-approval` and `release` decision, signed passports, and no `production` datasets as test inputs.

## 11. Conformance (normative)

An implementation claims conformance for a role and, as a producer, for a level, for example "OIS 0.1 Producer, Level 2".

### 11.1 Roles

- **Producer:** emits records that validate against Appendix B, satisfies the integrity rules of section 5 for the records it creates, and computes digests as section 6.4 requires.
- **Consumer:** accepts valid records, applies the stale evidence rule (section 6.3), ignores unknown extensions and verifies signatures where present (section 8.3).
- **Validator:** checks a record, bundle or passport against Appendix B and against every rule of section 5 that can be checked from the records at hand. It reports each violation with its rule identifier (R1 to R17). A violation of Appendix B is reported with the identifier `schema`, a signature that does not hold with `signature`.

Validators report at three levels. A *violation* means a MUST is broken and the input does not conform. A *warning* means a rule asks for a report while the input still conforms (R8, R12 and R13). An *info* report points to a SHOULD that is not followed. The conformance test suite tags every invalid fixture with the expected level and rule.

For signed bundles and passports (section 8.3), validators report:

| Rule | Level | Condition |
| --- | --- | --- |
| `signature` | violation | An envelope without signatures, with a payload type other than the one its payload requires, or with a signature under a trusted key that does not verify. |
| `signature` | warning | A signature under a key the verifier does not trust; it cannot be checked. |

The rules of section 5 apply to the payload as to an unwrapped document.

### 11.2 Producer levels

| Level | Name | Requirements | Typical producer |
| --- | --- | --- | --- |
| 1 | Observe | Emits artifact and evidence records for its own outputs. `derivedFrom` MAY be `unknown`. | An adapter that reads JUnit XML results |
| 2 | Intent-aware | Level 1, plus: reads intents, references criteria explicitly, records `context` completely for the artifacts it produces, and sets `derivedFrom` to `unknown` only for test artifacts it did not produce. | A test agent that generates tests from criteria |
| 3 | Attested | Level 2, plus: carries an `identity`, signs the bundles and passports it emits with DSSE under that identity, includes artifacts only in bundles that also carry the signature of each artifact's `contextRecordedBy` actor (R12; a DSSE envelope accepts several signatures), and SHOULD record signatures in a transparency log. | A platform or tool with native OIS support |

### 11.3 Conformance test suite

The public repository provides a conformance test suite of valid and invalid fixtures. Each invalid fixture names the rule it violates; fixtures for Appendix B are tagged with the rule `schema`, those for signatures with `signature`. The suite lists the public keys and Sigstore trusted roots a validator trusts for its signed fixtures.

- A validator conforms if it accepts every valid fixture and rejects every invalid fixture with the correct rule identifier.
- A producer demonstrates conformance by passing its output through a conforming validator, for the level it claims.

### 11.4 Quick start for Level 1 (informative)

A Level 1 adapter, for example one that reads JUnit XML from an existing pipeline, needs five things. Everything else can wait.

1. **One actor record for the adapter itself:** kind `tool`, `name`, `version`.
2. **One actor record for the existing test suite:** kind `tool`, named for the team that owns the tests, used as `producedBy` while the real authors are unknown.
3. **One characterization intent per test suite:** status `draft`, one criterion per test case with `notation: text`, the test name as `statement` and `kind: functional`. It describes what the suite checks today and becomes an approved intent once a human has reviewed it.
4. **One artifact record per test file:** kind `test`, `location` (repository at commit), `path`, `digest` (`sha256` of the file), `producedBy` from step 2.
5. **One evidence record per test result:** `criterion` from step 3, `test` from step 4, `derivedFrom: unknown`, `result`, `observedAt`, `recordedBy` from step 1.

This gives a complete, valid bundle after one pipeline run. Intent coverage will be zero until intents are approved and tests are derived from them, which is the honest baseline for an existing system.

## 12. Security and privacy considerations (normative)

OIS records are evidence, so their main risks are forgery, tampering and leaking personal data.

### 12.1 Privacy

- Records MUST NOT contain personal data, apart from actor names and identifiers.
- Human actors SHOULD be identified by pseudonyms that only the operating organization can resolve.
- Test data MUST be referenced as dataset artifacts by location and digest, never embedded. Criterion statements and examples MUST NOT contain real personal data.
- Datasets that contain personal data MUST be classified as `production` or `anonymized`, so that policies can detect them.

The `identity` of a human actor MUST be pseudonymous. OIDC identities that expose an e-mail address or a real name MUST NOT be recorded; organizations map pseudonymous subjects to people outside OIS.

### 12.2 Threats and mitigations

| Threat | Mitigation |
| --- | --- |
| Forged evidence from an unknown recorder | Consumers SHOULD only rely on evidence from signed bundles or passports, and SHOULD check that `recordedBy` is a known actor. |
| Actor impersonation, for example an agent posing as a human | Actor identity SHOULD be bound to a credential such as a workload identity or a Sigstore OIDC identity. Level 3 requires this. |
| Self-declared context that hides what an agent saw | `context` SHOULD be recorded by the runtime that ran the producer (`contextRecordedBy`), not by the producer itself. Validators flag self-declared context (R12). |
| Backdated or false timestamps | Level 3 producers SHOULD record signatures in a transparency log, which gives an independent time and order (section 8.3). |
| Artifact changed after evidence was recorded | Consumers SHOULD recompute artifact digests where the artifact is reachable and treat a mismatch as a failed check. |
| Replay of old evidence for a new intent version | Evidence is bound to an intent version and criterion digest; the stale evidence rule applies (section 6.3). |
| Instructions hidden in criterion text | Consumers that pass statements, rationales or extensions to AI models MUST treat them as untrusted data, not as instructions. |
| Leaking internal information through passports | Producers SHOULD review what a passport reveals before sharing it outside the organization. Access control is out of scope. |

## 13. Relationship to existing standards (informative)

OIS reuses existing standards for notation, packaging, signing and events, and adds only the link between intent and evidence.

| Standard | Role in OIS |
| --- | --- |
| Gherkin | Criterion notation (`notation: gherkin`) |
| EARS | Criterion notation (`notation: ears`) |
| in-toto Attestation Framework | Statement format of the Quality Passport, DigestSet format for digests |
| DSSE | Signing envelope for passports and bundles |
| Sigstore | Recommended keyless signing |
| SLSA | Build provenance for the same release; complements the passport |
| CloudEvents | Event format (section 9) |
| W3C Trace Context, OpenTelemetry | The `trace` field links records to distributed traces |
| JSON Schema 2020-12 | Validation (Appendix B) |
| RFC 8785 (JCS) | Canonical JSON form for digests |
| OpenAPI | Contracts recorded as artifacts of kind `contract` |
| JUnit XML | Common input format for Level 1 adapters |
| SPDX, CycloneDX | SBOMs state what software contains; OIS states what it must do and how that is proven |
| ISO/IEC 42001 | Records can support documentation and traceability of AI use in delivery processes |
| EU AI Act | Records can support documentation and human oversight duties where such duties apply |
| NIST AI RMF | Records provide measurable evidence for the Measure and Manage functions |

The last three rows are orientation only. They are not a legal or certification interpretation, and using OIS does not by itself establish compliance with any framework.

## Appendix A: Complete example (informative)

The example follows one feature, "Customers change their address in the portal", from approved intent to Quality Passport. The intent and criterion digests are computed as section 6.4 describes (R17). The digests of artifacts are illustrative, since their content is not part of the example.

### A.1 Bundle

The bundle holds the actors, the approved intent, four artifacts, one evidence record and the intent approval. Note that the test was written by a different agent, on a different model, that never saw the code, and that the agent runtime, not the agent, recorded what each agent was given. The bundle is exchanged in a DSSE envelope signed under the agent runtime's identity, so these contexts count as attested (R12).

```json
{
  "ois": "0.1",
  "type": "bundle",
  "id": "https://ois.acme.example/bundles/B-2026-10-20-01",
  "createdAt": "2026-10-20T15:00:00Z",
  "records": [
    { "ois": "0.1", "type": "actor", "id": "https://ois.acme.example/actors/po-7f3a",
      "createdAt": "2026-09-01T08:00:00Z", "kind": "human", "name": "PO 7f3a", "operator": "Team Portal" },
    { "ois": "0.1", "type": "actor", "id": "https://ois.acme.example/actors/requirement-agent",
      "createdAt": "2026-09-01T08:00:00Z", "kind": "agent", "name": "Requirement agent", "version": "1.4",
      "model": { "provider": "ExampleAI", "name": "model-a", "version": "2026-09" }, "autonomyLevel": 1 },
    { "ois": "0.1", "type": "actor", "id": "https://ois.acme.example/actors/dev-agent",
      "createdAt": "2026-09-01T08:00:00Z", "kind": "agent", "name": "Developer agent", "version": "3.0",
      "model": { "provider": "ExampleAI", "name": "model-a", "version": "2026-09" }, "autonomyLevel": 2 },
    { "ois": "0.1", "type": "actor", "id": "https://ois.acme.example/actors/qe-agent",
      "createdAt": "2026-09-01T08:00:00Z", "kind": "agent", "name": "QE agent", "version": "2.1",
      "model": { "provider": "OtherAI", "name": "model-b", "version": "2026-08" }, "autonomyLevel": 2 },
    { "ois": "0.1", "type": "actor", "id": "https://ois.acme.example/actors/agent-runtime",
      "createdAt": "2026-09-01T08:00:00Z", "kind": "tool", "name": "Agent runtime and gateway", "version": "4.3",
      "identity": { "issuer": "https://oidc.acme.example", "subject": "spiffe://acme.example/agent-runtime" } },
    { "ois": "0.1", "type": "actor", "id": "https://ois.acme.example/actors/testdata-generator",
      "createdAt": "2026-09-01T08:00:00Z", "kind": "tool", "name": "Synthetic test data generator", "version": "5.2" },
    { "ois": "0.1", "type": "actor", "id": "https://ois.acme.example/actors/ci-recorder",
      "createdAt": "2026-09-01T08:00:00Z", "kind": "tool", "name": "CI evidence recorder", "version": "1.2" },
    {
      "ois": "0.1", "type": "intent", "id": "https://ois.acme.example/intents/INT-142",
      "createdAt": "2026-10-14T09:12:00Z", "version": 1,
      "title": "Customers change their address in the portal",
      "status": "approved",
      "language": "en",
      "producedBy": "https://ois.acme.example/actors/requirement-agent@1.4",
      "source": "https://jira.acme.example/browse/PORTAL-1187",
      "risk": "high",
      "criteria": [
        { "key": "AC-1", "notation": "gherkin", "kind": "functional", "criticality": "high",
          "statement": "Given a logged-in customer, when they submit a valid Swiss address, then the new address is saved with the chosen effective date",
          "digest": { "sha256": "c6aa1922fdd002acc1087b24060aa2a20650536b8693725f5c74761660df1d3a" } },
        { "key": "AC-2", "notation": "ears", "kind": "functional", "criticality": "high",
          "statement": "WHEN an address cannot be assigned to a canton, THE portal SHALL flag the premium region for manual review",
          "digest": { "sha256": "ebd6350ec92d58cc7c77e62ebf40ea2d26922f8ec95ad85c626ff6b39f8599f6" } },
        { "key": "NFR-1", "notation": "ears", "kind": "non-functional", "criticality": "medium",
          "statement": "THE portal SHALL confirm an address change within 500 milliseconds at the 95th percentile",
          "target": { "metric": "responseTimeP95", "operator": "lte", "value": 500, "unit": "ms" },
          "digest": { "sha256": "eccddffcc90a273e6f6663b1f4bd31de390acd914bfb076f8d4cf54ca443904b" } }
      ],
      "digest": { "sha256": "1358302ab5174e32bff0df5c244bac5eca011e9d0b6c2cd3d4166db2f0223552" }
    },
    {
      "ois": "0.1", "type": "artifact", "id": "https://ois.acme.example/artifacts/ART-301",
      "createdAt": "2026-10-15T11:20:00Z", "kind": "contract", "mediaType": "application/yaml",
      "location": "git+https://git.acme.example/portal.git@a1b2c3d4e5f60718293a4b5c6d7e8f9012345678",
      "path": "api/address.openapi.yaml",
      "digest": { "sha256": "5f2b8c41a9e07d36c4b18f92e6a05d7c3b91e48f20a6d5c7b39e81f4a2c60d95" },
      "producedBy": "https://ois.acme.example/actors/dev-agent@3.0",
      "context": ["https://ois.acme.example/intents/INT-142@1"],
      "contextRecordedBy": "https://ois.acme.example/actors/agent-runtime@4.3"
    },
    {
      "ois": "0.1", "type": "artifact", "id": "https://ois.acme.example/artifacts/ART-302",
      "createdAt": "2026-10-18T16:40:00Z", "kind": "code",
      "location": "git+https://git.acme.example/portal.git@a1b2c3d4e5f60718293a4b5c6d7e8f9012345678",
      "digest": { "gitCommit": "a1b2c3d4e5f60718293a4b5c6d7e8f9012345678" },
      "producedBy": "https://ois.acme.example/actors/dev-agent@3.0",
      "context": ["https://ois.acme.example/intents/INT-142@1", "https://ois.acme.example/artifacts/ART-301"],
      "contextRecordedBy": "https://ois.acme.example/actors/agent-runtime@4.3"
    },
    {
      "ois": "0.1", "type": "artifact", "id": "https://ois.acme.example/artifacts/ART-303",
      "createdAt": "2026-10-16T08:05:00Z", "kind": "dataset", "classification": "synthetic",
      "location": "https://testdata.acme.example/sets/addresses-without-canton-v1",
      "digest": { "sha256": "8a41c7e29b05f3d68e17a4c92b6f0d3e5a78c19b42e6f0a3d57c81b9e4f20a6c" },
      "producedBy": "https://ois.acme.example/actors/testdata-generator@5.2",
      "context": ["https://ois.acme.example/intents/INT-142@1#AC-2"],
      "contextRecordedBy": "https://ois.acme.example/actors/agent-runtime@4.3"
    },
    {
      "ois": "0.1", "type": "artifact", "id": "https://ois.acme.example/artifacts/ART-304",
      "createdAt": "2026-10-18T17:05:00Z", "kind": "test",
      "location": "git+https://git.acme.example/portal.git@a1b2c3d4e5f60718293a4b5c6d7e8f9012345678",
      "path": "tests/address.spec.ts",
      "digest": { "sha256": "c39e5a17f482b06d9e3c71a5b48f20e6d1a9c74b3e58f02a6d91c4b7e3f05a28" },
      "producedBy": "https://ois.acme.example/actors/qe-agent@2.1",
      "context": ["https://ois.acme.example/intents/INT-142@1", "https://ois.acme.example/artifacts/ART-301",
                  "https://ois.acme.example/artifacts/ART-303"],
      "contextRecordedBy": "https://ois.acme.example/actors/agent-runtime@4.3"
    },
    {
      "ois": "0.1", "type": "evidence", "id": "https://ois.acme.example/evidence/EV-9021",
      "createdAt": "2026-10-20T14:32:05Z",
      "criterion": "https://ois.acme.example/intents/INT-142@1#AC-2",
      "test": "https://ois.acme.example/artifacts/ART-304",
      "subject": "https://ois.acme.example/artifacts/ART-302",
      "inputs": ["https://ois.acme.example/artifacts/ART-303"],
      "derivedFrom": "intent",
      "result": "pass",
      "observedAt": "2026-10-20T14:31:58Z",
      "recordedBy": "https://ois.acme.example/actors/ci-recorder@1.2",
      "measures": [{ "name": "mutationScore", "value": 0.84,
                     "method": "https://ois.acme.example/methods/mutation-score" }],
      "run": "https://ci.acme.example/pipelines/portal/runs/5531"
    },
    {
      "ois": "0.1", "type": "decision", "id": "https://ois.acme.example/decisions/DEC-77",
      "createdAt": "2026-10-14T10:05:00Z",
      "gate": "intent-approval",
      "subject": "https://ois.acme.example/intents/INT-142@1",
      "subjectDigest": { "sha256": "1358302ab5174e32bff0df5c244bac5eca011e9d0b6c2cd3d4166db2f0223552" },
      "outcome": "approved",
      "decidedBy": "https://ois.acme.example/actors/po-7f3a",
      "decidedAt": "2026-10-14T10:05:00Z",
      "policy": { "id": "https://ois.acme.example/policies/definition-of-ready", "version": "4" }
    }
  ]
}
```

### A.2 Quality Passport

The passport for the release adds four records: a build artifact, the release decision, the QE lead who made that decision and the issuing actor. Its `records` array contains every record from A.1 plus these four; the build artifact and the release decision are shown.

```json
{
  "_type": "https://in-toto.io/Statement/v1",
  "subject": [
    { "name": "customer-portal",
      "digest": { "sha256": "0d4f7a2c9e15b83d6a0c47e91f5b28d3c6e09a4f71b2d58e3a96c0f4d7b12e85" } }
  ],
  "predicateType": "https://openintentschema.io/passport/v0.1",
  "predicate": {
    "ois": "0.1",
    "release": { "name": "customer-portal", "version": "2026.10.3" },
    "intents": ["https://ois.acme.example/intents/INT-142@1"],
    "scope": ["https://ois.acme.example/intents/INT-142@1#AC-1", "https://ois.acme.example/intents/INT-142@1#AC-2"],
    "records": [
      {
        "ois": "0.1", "type": "artifact", "id": "https://ois.acme.example/artifacts/ART-305",
        "createdAt": "2026-10-20T16:10:00Z", "kind": "build",
        "location": "pkg:oci/customer-portal@sha256%3A0d4f7a2c9e15b83d6a0c47e91f5b28d3c6e09a4f71b2d58e3a96c0f4d7b12e85?repository_url=registry.acme.example",
        "digest": { "sha256": "0d4f7a2c9e15b83d6a0c47e91f5b28d3c6e09a4f71b2d58e3a96c0f4d7b12e85" },
        "producedBy": "https://ois.acme.example/actors/ci-recorder@1.2",
        "inputs": ["https://ois.acme.example/artifacts/ART-302"]
      },
      {
        "ois": "0.1", "type": "decision", "id": "https://ois.acme.example/decisions/DEC-81",
        "createdAt": "2026-10-21T08:45:00Z",
        "gate": "release",
        "subject": "https://ois.acme.example/artifacts/ART-305",
        "subjectDigest": { "sha256": "0d4f7a2c9e15b83d6a0c47e91f5b28d3c6e09a4f71b2d58e3a96c0f4d7b12e85" },
        "outcome": "approved",
        "decidedBy": "https://ois.acme.example/actors/qe-2c9d",
        "decidedAt": "2026-10-21T08:45:00Z",
        "evidence": ["https://ois.acme.example/evidence/EV-9021"],
        "assessments": [{ "name": "intentCoverage", "value": 0.5,
                          "method": "https://openintentschema.io/methods/basic-intent-coverage/v0.1" }]
      }
    ],
    "assessments": [{ "name": "intentCoverage", "value": 0.5,
                      "method": "https://openintentschema.io/methods/basic-intent-coverage/v0.1" }],
    "issuedBy": "https://ois.acme.example/actors/passport-issuer@1.0",
    "issuedAt": "2026-10-21T09:00:00Z"
  }
}
```

The intent coverage of 0.5 follows the reference method of Appendix D: of the two criteria in scope, only AC-2 has counted evidence. Its `method` URI tells consumers how it was computed; OIS does not define the method.

## Appendix B: JSON Schema (normative)

The schema below is normative and is also published as a separate file at its `$id`. It uses JSON Schema 2020-12.

- Validators MUST treat the `format` keywords `uri` and `date-time` as assertions, or check them in an equivalent way.
- The schema checks single records, bundles and passport predicates. Rules that span several records, such as R1 to R16, are defined in section 5 and checked by validators separately. The schema relies on unevaluatedProperties and on format assertions, so a conformance claim requires a JSON Schema 2020-12 validator with the format-assertion vocabulary enabled. Older validators give only an approximate result.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://openintentschema.io/schema/v0.1/ois.schema.json",
  "title": "Open Intent Schema v0.1",
  "oneOf": [
    { "$ref": "#/$defs/record" },
    { "$ref": "#/$defs/bundle" }
  ],
  "$defs": {
    "uri": { "type": "string", "format": "uri" },
    "id": { "type": "string", "format": "uri", "pattern": "^[^@#]+$" },
    "ref": { "type": "string", "format": "uri" },
    "intentRef": { "type": "string", "format": "uri", "pattern": "^[^@#]+@[1-9][0-9]*$" },
    "criterionRef": { "type": "string", "format": "uri", "pattern": "^[^@#]+@[1-9][0-9]*#[A-Za-z0-9._-]{1,64}$" },
    "timestamp": { "type": "string", "format": "date-time" },
    "language": { "type": "string", "pattern": "^[A-Za-z]{2,3}(-[A-Za-z0-9]{1,8})*$" },
    "digest": {
      "type": "object",
      "minProperties": 1,
      "propertyNames": { "pattern": "^[A-Za-z0-9]+$" },
      "additionalProperties": { "type": "string", "pattern": "^[0-9a-f]+$" },
      "anyOf": [ { "required": ["sha256"] }, { "required": ["gitCommit"] } ]
    },
    "measurement": {
      "type": "object",
      "required": ["name", "value"],
      "properties": {
        "name": { "type": "string", "minLength": 1 },
        "value": { "type": ["number", "string", "boolean"] },
        "unit": { "type": "string" },
        "method": { "$ref": "#/$defs/uri" }
      },
      "additionalProperties": false
    },
    "target": {
      "type": "object",
      "required": ["metric", "operator", "value"],
      "properties": {
        "metric": { "type": "string", "minLength": 1 },
        "operator": { "enum": ["lt", "lte", "gt", "gte", "eq"] },
        "value": { "type": "number" },
        "unit": { "type": "string" }
      },
      "additionalProperties": false
    },
    "model": {
      "type": "object",
      "required": ["provider", "name", "version"],
      "properties": {
        "provider": { "type": "string" },
        "name": { "type": "string", "minLength": 1 },
        "version": { "type": "string" }
      },
      "additionalProperties": false
    },
    "identity": {
      "type": "object",
      "properties": {
        "issuer": { "$ref": "#/$defs/uri" },
        "subject": { "type": "string", "minLength": 1 },
        "keyId": { "type": "string", "minLength": 1 }
      },
      "anyOf": [ { "required": ["issuer", "subject"] }, { "required": ["keyId"] } ],
      "additionalProperties": false
    },
    "common": {
      "type": "object",
      "required": ["ois", "type", "id", "createdAt"],
      "properties": {
        "ois": { "const": "0.1" },
        "id": { "$ref": "#/$defs/id" },
        "createdAt": { "$ref": "#/$defs/timestamp" },
        "profiles": { "type": "array", "items": { "$ref": "#/$defs/uri" } },
        "trace": {
          "type": "object",
          "required": ["traceId"],
          "properties": {
            "traceId": { "type": "string", "pattern": "^[0-9a-f]{32}$" },
            "spanId": { "type": "string", "pattern": "^[0-9a-f]{16}$" }
          },
          "additionalProperties": false
        },
        "extensions": {
          "type": "object",
          "propertyNames": {
            "anyOf": [
              { "pattern": "^([a-z0-9-]+\\.)+[a-z0-9-]+$" },
              { "pattern": "^[A-Za-z][A-Za-z0-9+.-]*:\\S+$" }
            ]
          }
        }
      }
    },
    "criterion": {
      "type": "object",
      "required": ["key", "statement", "notation", "kind"],
      "properties": {
        "key": { "type": "string", "pattern": "^[A-Za-z0-9._-]{1,64}$" },
        "statement": { "type": "string", "minLength": 1 },
        "notation": { "enum": ["gherkin", "ears", "text"] },
        "kind": { "enum": ["functional", "non-functional"] },
        "language": { "$ref": "#/$defs/language" },
        "target": { "$ref": "#/$defs/target" },
        "criticality": { "enum": ["low", "medium", "high"] },
        "digest": { "$ref": "#/$defs/digest" }
      },
      "additionalProperties": false
    },
    "intent": {
      "allOf": [
        { "$ref": "#/$defs/common" },
        {
          "if": { "properties": { "status": { "const": "approved" } } },
          "then": {
            "required": ["digest"],
            "properties": { "criteria": { "items": { "required": ["digest"] } } }
          }
        }
      ],
      "required": ["version", "title", "status", "criteria"],
      "properties": {
        "type": { "const": "intent" },
        "version": { "type": "integer", "minimum": 1 },
        "title": { "type": "string", "minLength": 1 },
        "status": { "enum": ["draft", "approved", "withdrawn"] },
        "language": { "$ref": "#/$defs/language" },
        "criteria": { "type": "array", "minItems": 1, "items": { "$ref": "#/$defs/criterion" } },
        "producedBy": { "$ref": "#/$defs/ref" },
        "source": { "$ref": "#/$defs/uri" },
        "supersedes": { "$ref": "#/$defs/intentRef" },
        "risk": { "enum": ["low", "medium", "high", "critical"] },
        "digest": { "$ref": "#/$defs/digest" }
      },
      "unevaluatedProperties": false
    },
    "artifact": {
      "allOf": [
        { "$ref": "#/$defs/common" },
        {
          "if": { "properties": { "kind": { "const": "dataset" } } },
          "then": { "required": ["classification"] }
        }
      ],
      "required": ["kind", "location", "digest", "producedBy"],
      "properties": {
        "type": { "const": "artifact" },
        "kind": { "enum": ["code", "test", "contract", "dataset", "document", "build", "other"] },
        "location": { "$ref": "#/$defs/uri" },
        "path": { "type": "string", "minLength": 1 },
        "digest": { "$ref": "#/$defs/digest" },
        "producedBy": { "$ref": "#/$defs/ref" },
        "inputs": { "type": "array", "items": { "$ref": "#/$defs/ref" } },
        "context": { "type": "array", "items": { "$ref": "#/$defs/ref" } },
        "contextRecordedBy": { "$ref": "#/$defs/ref" },
        "classification": { "enum": ["synthetic", "anonymized", "production"] },
        "mediaType": { "type": "string" }
      },
      "unevaluatedProperties": false
    },
    "actor": {
      "allOf": [
        { "$ref": "#/$defs/common" },
        {
          "if": { "properties": { "kind": { "enum": ["agent", "tool"] } } },
          "then": { "required": ["version"] }
        },
        {
          "if": { "properties": { "kind": { "const": "agent" } } },
          "then": { "required": ["model"] }
        }
      ],
      "required": ["kind", "name"],
      "properties": {
        "type": { "const": "actor" },
        "kind": { "enum": ["human", "agent", "tool"] },
        "name": { "type": "string", "minLength": 1 },
        "version": { "type": "string", "pattern": "^[^@#]+$" },
        "model": {
          "oneOf": [
            { "$ref": "#/$defs/model" },
            { "type": "array", "minItems": 1, "items": { "$ref": "#/$defs/model" } }
          ]
        },
        "identity": { "$ref": "#/$defs/identity" },
        "operator": { "type": "string" },
        "autonomyLevel": { "type": "integer", "minimum": 0, "maximum": 3 }
      },
      "unevaluatedProperties": false
    },
    "evidence": {
      "allOf": [ { "$ref": "#/$defs/common" } ],
      "required": ["criterion", "test", "derivedFrom", "result", "observedAt", "recordedBy"],
      "properties": {
        "type": { "const": "evidence" },
        "criterion": { "$ref": "#/$defs/criterionRef" },
        "test": { "$ref": "#/$defs/ref" },
        "subject": { "$ref": "#/$defs/ref" },
        "inputs": { "type": "array", "items": { "$ref": "#/$defs/ref" } },
        "derivedFrom": { "enum": ["intent", "implementation", "unknown"] },
        "result": { "enum": ["pass", "fail", "skipped", "error"] },
        "observedAt": { "$ref": "#/$defs/timestamp" },
        "recordedBy": { "$ref": "#/$defs/ref" },
        "measures": { "type": "array", "items": { "$ref": "#/$defs/measurement" } },
        "run": { "$ref": "#/$defs/uri" }
      },
      "unevaluatedProperties": false
    },
    "decision": {
      "allOf": [
        { "$ref": "#/$defs/common" },
        {
          "if": { "properties": { "outcome": { "const": "waived" } } },
          "then": { "required": ["rationale"] }
        },
        {
          "if": { "properties": { "gate": { "const": "evidence-revocation" } } },
          "then": { "required": ["rationale"], "properties": { "outcome": { "const": "rejected" } } }
        },
        {
          "if": { "properties": { "gate": { "enum": ["intent-approval", "release"] } } },
          "then": { "required": ["subjectDigest"] }
        }
      ],
      "required": ["gate", "subject", "outcome", "decidedBy", "decidedAt"],
      "properties": {
        "type": { "const": "decision" },
        "gate": { "type": "string", "minLength": 1 },
        "subject": { "$ref": "#/$defs/ref" },
        "subjectDigest": { "$ref": "#/$defs/digest" },
        "outcome": { "enum": ["approved", "rejected", "passed", "blocked", "waived"] },
        "decidedBy": { "$ref": "#/$defs/ref" },
        "decidedAt": { "$ref": "#/$defs/timestamp" },
        "policy": {
          "type": "object",
          "required": ["id"],
          "properties": {
            "id": { "$ref": "#/$defs/uri" },
            "version": { "type": "string" },
            "digest": { "$ref": "#/$defs/digest" }
          },
          "additionalProperties": false
        },
        "evidence": { "type": "array", "items": { "$ref": "#/$defs/ref" } },
        "assessments": { "type": "array", "items": { "$ref": "#/$defs/measurement" } },
        "rationale": { "type": "string" }
      },
      "unevaluatedProperties": false
    },
    "finding": {
      "allOf": [
        { "$ref": "#/$defs/common" },
        { "anyOf": [ { "required": ["criterion"] }, { "required": ["intent"] }, { "required": ["subject"] } ] }
      ],
      "required": ["source", "severity", "summary", "observedAt", "reportedBy"],
      "properties": {
        "type": { "const": "finding" },
        "criterion": { "$ref": "#/$defs/criterionRef" },
        "intent": { "$ref": "#/$defs/intentRef" },
        "subject": { "$ref": "#/$defs/ref" },
        "source": { "enum": ["production", "test", "review", "customer", "other"] },
        "severity": { "enum": ["low", "medium", "high", "critical"] },
        "summary": { "type": "string", "minLength": 1 },
        "observedAt": { "$ref": "#/$defs/timestamp" },
        "reportedBy": { "$ref": "#/$defs/ref" },
        "ticket": { "$ref": "#/$defs/uri" },
        "cause": { "enum": ["spec-gap", "implementation", "test-gap", "gate-gap", "review", "unknown"] },
        "resolvedBy": { "type": "array", "items": { "$ref": "#/$defs/ref" } },
        "supersedes": { "$ref": "#/$defs/ref" }
      },
      "unevaluatedProperties": false
    },
    "record": {
      "oneOf": [
        { "$ref": "#/$defs/intent" },
        { "$ref": "#/$defs/artifact" },
        { "$ref": "#/$defs/actor" },
        { "$ref": "#/$defs/evidence" },
        { "$ref": "#/$defs/decision" },
        { "$ref": "#/$defs/finding" }
      ]
    },
    "bundle": {
      "allOf": [ { "$ref": "#/$defs/common" } ],
      "required": ["records"],
      "properties": {
        "type": { "const": "bundle" },
        "records": { "type": "array", "items": { "$ref": "#/$defs/record" } }
      },
      "unevaluatedProperties": false
    },
    "passportPredicate": {
      "type": "object",
      "required": ["ois", "release", "intents", "records", "issuedBy", "issuedAt"],
      "properties": {
        "ois": { "const": "0.1" },
        "release": {
          "type": "object",
          "required": ["name", "version"],
          "properties": {
            "name": { "type": "string" },
            "version": { "type": "string" },
            "location": { "$ref": "#/$defs/uri" }
          },
          "additionalProperties": false
        },
        "intents": { "type": "array", "minItems": 1, "items": { "$ref": "#/$defs/intentRef" } },
        "scope": { "type": "array", "items": { "$ref": "#/$defs/criterionRef" } },
        "records": { "type": "array", "items": { "$ref": "#/$defs/record" } },
        "bundles": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["location", "digest"],
            "properties": {
              "location": { "$ref": "#/$defs/uri" },
              "digest": { "$ref": "#/$defs/digest" }
            },
            "additionalProperties": false
          }
        },
        "assessments": { "type": "array", "items": { "$ref": "#/$defs/measurement" } },
        "issuedBy": { "$ref": "#/$defs/ref" },
        "issuedAt": { "$ref": "#/$defs/timestamp" }
      },
      "additionalProperties": false
    }
  }
}
```

## Appendix C: Open questions

These questions are open for v0.1 and are the main topics for the first design partner rounds.

- [ ] **Non-functional requirements:** is `kind: non-functional` enough, or do NFRs need structured, measurable thresholds such as a latency budget?
- [ ] **One evidence per criterion:** v0.1 binds each evidence record to one criterion, so a test run covering three criteria produces three records. Is that practical?
- [ ] **Actor granularity:** v0.1 treats the model as an attribute of the actor and requires a new actor version when it changes. Should the model be an actor of its own?
- [ ] **Human approval:** should the core require a human actor for `intent-approval` and `release` decisions, or only regulated profiles?
- [ ] **Proof of derivation:** `derivedFrom: intent` relies on a complete `context`. How can producers show completeness beyond declaring it?
- [ ] **Evidence across versions:** is the digest-based rule in section 6.3 workable in practice?
- [ ] **Git digests:** `gitCommit` is SHA-1 in most repositories. Should a `sha256` value be required as well?
- [ ] **Autonomy levels:** do the four levels belong in the core or in a profile?
- [ ] **Identifiers:** IANA registration of the media type `application/vnd.ois+json` and a possible URN namespace.
- [ ] **Name:** "Open Intent Schema" is a working title and needs a trademark check.
- [ ] **Foundation:** which neutral home fits best, for example the Linux Foundation, CNCF or OpenSSF?

* [ ] **Runtime attestation:** partly addressed in draft 2 by R12 and the actor `identity`. Still open: how a runtime proves that it recorded `context` faithfully, for example through sandbox attestation or signed session logs.
* [ ] **IPR policy:** which patent covenant should cover the specification text and the schema?
* [ ] **Reference method:** Appendix D now defines an informative method. Should it become normative in 1.0?

## Appendix D: Reference method for intent coverage (informative)

This appendix defines one way to compute intent coverage, so that producers who use it report comparable figures. Other methods remain allowed; each is identified by its own `method` URI.

**Method URI:** `https://openintentschema.io/methods/basic-intent-coverage/v0.1`.

**Inputs:** the intent versions *V* a passport lists in `intents`, one release subject *s* (the code or build artifact being released) and the criteria in scope: the passport's `scope` entries, or all criteria of every version in *V* when `scope` is absent. A criterion belongs to exactly one version in *V*.

**Counted evidence:** an evidence record counts if all of the following hold:

- it references a criterion of a version *v* in *V*, or carries over to *v* under the stale evidence rule (section 6.3);
- its `result` is `pass`;
- its `derivedFrom` is `intent`;
- its `subject` is *s*, or an artifact listed in the inputs of *s*;
- it has not been revoked (R11);
- its `observedAt` is later than the `createdAt` of its `subject`.

**Covered criterion:** a criterion is covered if at least one counted evidence record references it. A criterion with a `target` is covered only if that evidence carries a measure whose `name` equals the target's `metric` and whose `value` satisfies the target's `operator` and `value`.

**Coverage:** the number of covered criteria in scope divided by the number of criteria in scope, over all versions in *V* together, reported as a Measurement named `intentCoverage` with a value between 0 and 1. With one intent version this is the coverage of that version. A passport with no criteria in scope reports no coverage.

**Attested variant:** `intentCoverageAttested` applies the same method but excludes evidence whose test artifact has a self-declared context (R12). Passports SHOULD report both values when they differ.

**Weighted variant:** `intentCoverageWeighted` weights each criterion by `criticality` (`high` 3, `medium` 2, `low` 1, unset 1) and divides the weight of covered criteria in scope by the total weight of all criteria in scope.

**Diverse variant:** `intentCoverageDiverse` counts evidence only when the producers of the test and of the subject are agents on different models (`provider` or `name` differ in every listed model), or when at least one of them is human. It addresses the shared blind spots of agents on the same model, which R5 alone does not catch.
