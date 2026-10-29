# Profile: regulated industries, v0.1

**URI:** `https://openintentschema.io/profiles/regulated/v0.1`
**Status:** example, draft. It shows how a profile is built and is open for comment by design
partners from regulated industries; it is not a recommendation for any particular regulation.
**Schema:** [`profile.schema.json`](profile.schema.json)

A record that lists this URI in `profiles` must satisfy the core specification and the rules
below. A bundle or passport whose records list it is checked as a whole. Section 10.2 of the
specification gives these four constraints as its example of a profile for regulated industries.

## Rules

| ID | Rule | Checked by |
| --- | --- | --- |
| P1 | Every intent MUST carry `risk`. | schema |
| P2 | The `decidedBy` actor of every decision with gate `intent-approval` or `release` MUST be an actor of kind `human`. In the core, R1 makes this a SHOULD for approvals. | validator, across records |
| P3 | A Quality Passport MUST be wrapped in a DSSE envelope and signed (section 8.3). In the core this is a SHOULD. | validator, on the envelope |
| P4 | An evidence record MUST NOT list an input dataset classified as `production`. In the core, R8 reports this as a warning. | validator, across records |

A validator that supports this profile reports a broken rule as a violation with the rule ID
`regulated/P1` to `regulated/P4`. The conformance fixtures under `fixtures/invalid/regulated/`
test each rule, and `fixtures/README.md` fixes how they are read: P3 asks for an envelope with a
signature, and whether it verifies is the `signature` rule's concern.

## Why these rules

- **P1:** regulated delivery assigns effort and review by risk; an intent without a risk class
  cannot be routed.
- **P2:** an agent approving its own requirements or releases removes the human oversight that
  the profile is meant to show.
- **P3:** a passport handed to an auditor must be attributable to whoever issued it.
- **P4:** production data in tests is a data protection issue in most regulated settings
  (specification section 12.1).

## Open questions

- Should P2 also cover `waived` outcomes at any gate (R9 makes this a SHOULD in the core)?
- Should the profile require `criticality` on every criterion, so that weighted coverage
  (Appendix D) is always defined?
