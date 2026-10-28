---
title: Build a Quality Passport
description: Collect the records behind a release into a Quality Passport and check it.
---

A Quality Passport collects the intents, evidence, decisions and findings behind a release, so
that an auditor, a customer or a regulator can verify it without access to your tools
([specification section 8](/specification/quality-passport/)). `ois-passport`, part of the
[`ois-validator`](/develop/validator/) package from version 0.3.0, assembles one from the records
you already have.

## What goes in

- **The approved intents** with their approval decisions, for example written with
  [`ois-intent`](/approve-intents/).
- **Evidence** and the test and code artifacts it points to, for example from
  [`ois-junit`](/getting-started/) or from tests derived from the intents.
- **The build artifact** being released, with its digest:

  ```yaml
  ois: "0.1"
  type: artifact
  id: https://ois.acme.example/artifacts/billing-2026.10.4
  createdAt: 2026-10-28T12:00:00Z
  kind: build
  location: pkg:oci/billing?repository_url=registry.acme.example
  digest: {sha256: 4f3c2b1a…}
  producedBy: https://ois.acme.example/actors/ci-build@7
  ```

- **The actors** every record names: who approved, who built, who issues the passport.
- **Open findings** for the listed intents, so the passport does not hide known defects.

A passport must be self-contained: every reference in it resolves to a record inside it (rule R10).

## Build it

```bash
uvx --from ois-validator ois-passport build .ois/ ci-bundles/ \
  --release-name billing --release-version 2026.10.4 \
  --build https://ois.acme.example/artifacts/billing-2026.10.4 \
  --issuer https://ois.acme.example/actors/passport-issuer@0.3.0 \
  --approve-release-by https://ois.acme.example/actors/release-manager-1d2e \
  --output passport.json
```

- **Inputs** are record or bundle files, or whole directories such as `.ois/`, in JSON or YAML.
  The same record in several inputs is kept once. Two different records with the same id are
  refused.
- **Intents:** each intent is listed in its latest approved version, as rule R15 recommends. Name
  them with `--intent` to choose, and narrow the criteria with `--scope`.
- **Release decision:** `--approve-release-by` records who approved the release, bound to the
  build's digest (rule R16). Leave it out if your release gate already recorded the decision.
- **Subject:** the statement's subject is the build artifact and its digest, which is what a
  consumer compares with the artifact they received.

`ois-passport` validates the passport before writing it. If it would break a rule, it names the
rule and writes nothing. Warnings, such as self-declared contexts (R12) or open high findings
(R13), are shown and the passport is written.

## Check it

Anyone can check a passport with the validator:

```bash
uvx ois-validator passport.json
```

Passports are not signed yet. DSSE signing, which Level 3 conformance requires and which lets a
recipient attribute the passport to its issuer, follows in a later version.
