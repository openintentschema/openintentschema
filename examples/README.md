# examples

Worked example from Appendix A of the specification: the feature "Customers change their
address in the portal".

- `bundle.json`: actors, the approved intent (version 1), four artifacts, one evidence record and
  the intent approval. Validates against `../schema/ois.schema.json` as a bundle.
- `passport.json`: the Quality Passport for the release as an in-toto Statement v1. Only the
  build artifact and the release decision are shown in `records`; a real passport also embeds
  every record from `bundle.json`, the QE lead who decided the release and the issuing actor.
  The predicate validates against `#/$defs/passportPredicate`.
- `finding.json`: a finding from production (section 4.7), cause classified as a spec gap.

The intent and criterion digests are computed as section 6.4 describes (R17). The digests of
artifacts and of the passport's subject are illustrative: they stand for content that is not part
of the example. The passport is not self-contained on purpose (see above);
`../fixtures/valid/passport.json` is a complete one.

The examples must match Appendix A of the specification as parsed JSON; change both together. CI
validates them against the schema.
