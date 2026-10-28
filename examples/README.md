# examples

Worked example from Appendix A of the specification: the feature "Customers change their
address in the portal".

- `bundle.json`: actors, the approved intent (version 3), four artifacts, one evidence record and
  the intent approval. Validates against `../schema/ois.schema.json` as a bundle.
- `passport.json`: the Quality Passport for the release as an in-toto Statement v1. Only the
  build artifact and the release decision are shown in `records`; a real passport also embeds
  every record from `bundle.json` and the issuing actor. The predicate validates against
  `#/$defs/passportPredicate`.
- `finding.json`: a finding from production (section 4.7), cause classified as a spec gap.

All digests are illustrative and were not computed from real content. The passport is not
self-contained on purpose (see note above); the conformance fixtures will carry a complete one.
