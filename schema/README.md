# Schema

`ois.schema.json` is the normative JSON Schema 2020-12 of the specification (Appendix B). The
specification embeds it verbatim; keep both identical as parsed JSON.

## How it is built

- The root is `oneOf` a single record or a bundle. `#/$defs/passportPredicate` is not reachable
  from the root: it is checked on its own against the `predicate` of an in-toto Statement.
- Each record type is `allOf: [{ "$ref": "#/$defs/common" }]` plus its own properties, closed with
  `unevaluatedProperties: false`. Shared fields (`ois`, `id`, `createdAt`, `profiles`, `trace`,
  `extensions`) are defined once in `common`. `unevaluatedProperties` needs a real 2020-12
  validator; draft-07 tooling silently accepts unknown fields.
- References are URI strings with a fixed grammar: an `id` has no `@` or `#`, an `intentRef` is
  `<id>@<version>`, a `criterionRef` is `<id>@<version>#<key>`. Approved intents and their criteria
  carry a `digest`.
- The schema checks structure only. Digests, the integrity rules of section 5 and references
  across records are checked by validators.
- `https://ois.example/…` (the `$id` and the passport `predicateType`) are placeholders, to be
  replaced by `openintentschema.io` identifiers ([RFC #6](https://github.com/openintentschema/openintentschema/issues/6)).
  `https://ois.acme.example/…` in examples and fixtures is a fictional producer namespace and stays.

## Changing it

A change to the schema needs an RFC issue and updates, in one pull request, Appendix B,
`examples/`, `fixtures/generate.py` and the change history of the specification. Check the
examples with ajv as `.github/workflows/checks.yml` does; when the `$id` changes, change the
`$ref` of the passport wrapper there too.
