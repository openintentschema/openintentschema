---
title: Build a Quality Passport
description: Collect the records behind a release into a Quality Passport and check it.
---

A Quality Passport collects the intents, evidence, decisions and findings behind a release, so
that an auditor, a customer or a regulator can verify it without access to your tools
([specification section 8](/specification/quality-passport/)). `ois passport`, part of the
[`ois-tools`](/develop/tools/) package, assembles one from the records
you already have.

## What goes in

- **The approved intents** with their approval decisions, for example written with
  [`ois intent`](/approve-intents/).
- **Evidence** and the test and code artifacts it points to, for example from
  [`ois junit`](/getting-started/) or from tests derived from the intents.
- **The build artifact** being released, with its digest, and **the actors** every record names:
  who approved, who built and who issues the passport. [`ois record`](/record/) writes them:

  ```bash
  CI=$(ois record actor --kind tool --name "CI build" --version 7)
  ISSUER=$(ois record actor --kind tool --name "Passport issuer" --version 1)
  BUILD=$(ois record artifact dist/billing-2026.10.4-py3-none-any.whl --kind build \
    --location pkg:pypi/billing@2026.10.4 --produced-by "$CI")
  ```

- **Open findings** for the listed intents, so the passport does not hide known defects, and the
  decisions that resolved earlier ones (`ois record finding`, `supersede` and `decision`).

A passport must be self-contained: every reference in it resolves to a record inside it (rule R10).

## Build it

```bash
uvx --from ois-tools ois passport build .ois/ ci-bundles/ \
  --release-name billing --release-version 2026.10.4 \
  --build "$BUILD" --issuer "$ISSUER" \
  --approve-release-by https://ois.acme.example/actors/release-manager-1d2e \
  --output passport.json
```

- **Inputs** are record or bundle files, or whole directories such as `.ois/`, in JSON or YAML.
  The same record in several inputs is kept once. Two different records with the same id are
  refused.
- **Intents:** each intent is listed in its latest approved version, as rule R15 recommends. Name
  them with `--intent` to choose, and narrow the criteria with `--scope`.
- **Release decision:** `--approve-release-by` records who approved the release, bound to the
  build's digest (rule R16). Leave it out if your release gate already recorded the decision, for
  example with `ois record decision --gate release`.
- **Subject:** the statement's subject is the build artifact and its digest, which is what a
  consumer compares with the artifact they received.
- **Coverage:** the passport reports intent coverage by the
  [reference method](/methods/basic-intent-coverage/v0.1/) in `assessments`. Leave it out with
  `--no-coverage` if you report your own method.

`ois passport` validates the passport before writing it. If it would break a rule, it names the
rule and writes nothing. Warnings, such as self-declared contexts (R12) or open high findings
(R13), are shown and the passport is written.

## Check it

Anyone can check a passport with the validator, and recompute the coverage it declares:

```bash
uvx --from ois-tools ois validate passport.json
uvx --from ois-tools ois coverage passport.json
```

```
https://ois.acme.example/intents/INT-142@1#AC-1  not covered
    https://ois.acme.example/evidence/EV-9022: derivedFrom is unknown
https://ois.acme.example/intents/INT-142@1#AC-2  covered  https://ois.acme.example/evidence/EV-9021
intentCoverage 0.5 (declared 0.5)
```

`ois coverage` shows per criterion which evidence counts and why the rest does not. It exits with
1 if a declared value differs from the computed one. Before the passport exists,
`ois coverage .ois/ --build "$BUILD"` shows what is still missing.

`--format markdown` writes the same as tables, for a CI job summary or a pull request comment.
On GitHub:

```yaml
- run: ois coverage .ois/ --build "$BUILD" --format markdown >> "$GITHUB_STEP_SUMMARY"
```

`intentCoverageAttested` counts only evidence whose test context was recorded by another actor
who signed the passport (rule R12). In an unsigned passport it is 0.

## Sign it

Level 3 conformance requires a signed passport, and a recipient can then attribute it to its
issuer. Add `--sign issuer.key` (and the key of the runtime that recorded the contexts) to
`ois passport build`, and check the result with `ois validate passport.dsse.json --trusted-key
keys/`. In a pipeline, the passport can also be signed keylessly, for example with
`actions/attest` on GitHub. See [Sign bundles and passports](/sign/).
