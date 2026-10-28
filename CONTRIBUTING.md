# Contributing

Thank you for helping to shape the Open Intent Schema.

## Before you start

- Read the specification in `specification/` and the governance rules in `GOVERNANCE.md`.
- Changes to the data model, rules, schema or passport format need an RFC issue first.
- Editorial fixes (typos, wording, examples) can go straight to a pull request.

## Developer Certificate of Origin

Every commit must carry a DCO sign-off, which states that you have the right to submit the
work under the project licenses:

```
git commit -s -m "Describe your change"
```

## Pull requests

- One topic per pull request.
- When the schema changes, update `specification/`, `schema/`, `examples/` and `fixtures/` in the same PR.
- CI must pass: examples validate against the schema, fixtures behave as tagged.

## Licenses

By contributing you agree that schema, code and fixtures are licensed under Apache-2.0 and
specification text under CC BY 4.0.
