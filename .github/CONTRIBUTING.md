# Contributing

Thank you for helping to shape the Open Intent Schema.

## Before you start

- Read the specification in `specification/` and the governance rules in
  [GOVERNANCE.md](../GOVERNANCE.md).
- Changes to the data model, rules, schema, conformance levels or passport format need an RFC
  issue first; use the RFC issue template.
- Editorial fixes (typos, wording, examples) can go straight to a pull request.
- Security issues are reported privately, see [SECURITY.md](SECURITY.md).
- Everyone taking part follows the [Code of Conduct](CODE_OF_CONDUCT.md).

## Developer Certificate of Origin

Every commit must carry a DCO sign-off, which states that you have the right to submit the
work under the project licenses:

```
git commit -s -m "Describe your change"
```

## Pull requests

- One topic per pull request.
- When the schema or a rule changes, update `specification/`, `schema/`, `examples/` and
  `fixtures/` in the same PR, and add a line to the change history of the specification.
- Appendix A and B embed `examples/` and `schema/ois.schema.json`; keep them identical as parsed
  JSON.
- Fixtures are generated: change `fixtures/generate.py`, never the JSON files, and describe how a
  rule is read in `fixtures/README.md`. The keyless signed passport cannot be generated: when
  `generate.py --check` asks for it, a maintainer runs the workflow "Record the keyless signed
  fixtures" and commits its artifact as `fixtures/sigstore/passport.sigstore.json`.
- CI must pass: examples validate against the schema, fixtures are up to date and behave as
  tagged.

## Checks

Run these before opening a pull request ([uv](https://docs.astral.sh/uv/) and Node.js needed):

```bash
uv run fixtures/generate.py           # regenerate fixtures and manifest after changing generate.py
uv run fixtures/generate.py --check   # what CI runs

npx -y -p ajv-cli@5.0.0 -p ajv-formats@3.0.1 ajv validate --spec=draft2020 -c ajv-formats \
  --strict=false -s schema/ois.schema.json -d examples/bundle.json -d examples/finding.json
```

The passport example is checked against `#/$defs/passportPredicate`; the CI workflow
`.github/workflows/checks.yml` shows how. Changes to the website are previewed with
`npm run dev` in `site/` (see `site/README.md`).

## Licenses

By contributing you agree that schema, code and fixtures are licensed under Apache-2.0 and
specification text under CC BY 4.0.
