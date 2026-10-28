---
title: Record artifacts, decisions and findings
description: Write the actors, artifacts, evidence, decisions and findings of a delivery with ois record, digests included.
---

Between an approved intent and a Quality Passport lie the records of the delivery itself: who
worked on it, what they produced, which tests passed, which gates were decided and which defects
turned up. `ois record`, part of the [`ois-tools`](/develop/tools/) package, writes each of them with one command. It computes digests, ids and timestamps, checks the
record and prints the reference other records use for it.

## Set up

```bash
pip install ois-tools              # or: uv tool install ois-tools
export OIS_NAMESPACE=https://ois.acme.example
```

Ids are derived under the namespace, a URI under your domain. Pass `--id` to choose one yourself.
Records go to `.ois/<type>s/`, next to the intents that [`ois intent`](/approve-intents/) writes.

## Actors

Every record names who produced, recorded or decided it (specification section 4.4):

```bash
PO=$(ois record actor --kind human --name po-7f3a)
DEV=$(ois record actor --kind agent --name "Dev Agent" --version 2.1 \
  --model acme-ai:coder:2026-09 --autonomy-level 1)
CI=$(ois record actor --kind tool --name "CI build" --version 7)
```

Each command prints the reference, for example `https://ois.acme.example/actors/ci-build@7`, so the
next command can use it. Agents and tools carry a version, and agents their model. When an agent's
model, instructions or tools change, record a new `--version`. For people, use a pseudonym as the
name. An identity subject must not be an e-mail address (section 12). An actor that signs gets
its key with `--public-key`, see [Sign bundles and passports](/sign/).

## Artifacts

```bash
CODE=$(ois record artifact src/invoice.py --kind code --produced-by "$DEV")
COMMIT=$(ois record artifact --commit . --kind code --produced-by "$DEV")
BUILD=$(ois record artifact dist/billing-2026.10.4-py3-none-any.whl --kind build \
  --location pkg:pypi/billing@2026.10.4 --produced-by "$CI" --input "$CODE")
IMAGE=$(ois record artifact --digest sha256:4f3c2b1a… --location pkg:oci/billing \
  --kind build --produced-by "$CI")
```

- **A file in Git** gets its `sha256`, the commit, the repository location
  `git+<origin>@<commit>` (credentials removed) and its path. It must be committed and unchanged.
- **A file elsewhere**, such as a built package, needs `--location`. A Package URL is recommended.
- **A commit** (`--commit`) or a known digest (`--digest`, for example an image in a registry)
  needs no file. A commit is named after its origin repository, so the id is the same in every
  clone and in the container image.

A test that was derived from an intent lists what its producer was given in `--context`:

```bash
TEST=$(ois record artifact tests/test_invoice.py --kind test --produced-by "$TEST_AGENT" \
  --context https://ois.acme.example/intents/INT-7@1#AC-1)
```

The context must be complete (rule R6). Name the runtime that observed it with
`--context-recorded-by`. Until that runtime signs the bundle or passport, the validator reports
the context as self-declared (R12); see [Sign bundles and passports](/sign/).

## Evidence

One result of one test for one criterion:

```bash
ois record evidence --criterion https://ois.acme.example/intents/INT-7@1#AC-1 \
  --test "$TEST" --subject "$CODE" --derived-from intent --result pass --recorded-by "$CI" \
  --measure responseTimeP95=420ms
```

`--derived-from` is a claim. The validator checks it against the test's context and producers (R4,
R5). For test results from JUnit XML, [`ois junit`](/getting-started/) writes the evidence in one
step.

## Decisions

```bash
ois record decision --gate merge --subject "$CODE" --outcome passed --by "$CI"
ois record decision --gate release --subject "$BUILD" --outcome approved --by "$QE"
ois record decision --gate evidence-revocation --subject "$FLAKY" --by "$QE" \
  --rationale "flaky test, see BILL-31"
```

- The decision binds the **digest of its subject**, taken from the subject's record in `.ois/` or
  in `--records`. A release decision cannot be written without it (R16).
- For the **well-known gates** of specification section 4.6, the subject and the outcome are
  checked. A merge decision takes code, and a release takes a build. An evidence revocation is always
  `rejected` and states its rationale (R11).
- Intent approvals are written by `ois intent approve`, which also seals the intent.

## Findings

A defect or incident, from production, a test, a review or a customer:

```bash
ois record finding --summary "Rounding is off for credit notes" --severity high \
  --source production --reported-by "$SUPPORT" --intent https://ois.acme.example/intents/INT-7@1 \
  --ticket https://jira.acme.example/browse/BILL-12
```

Findings never change. To classify or resolve one, record its successor:

```bash
ois record supersede .ois/findings/F-519bc77f0ab6.ois.json --cause implementation \
  --resolved-by "$FIX_EVIDENCE"
ois record decision --gate finding-resolution \
  --subject https://ois.acme.example/findings/F-519bc77f0ab6-r2 --outcome approved --by "$QE"
```

The resolution counts once an actor confirms it who did not produce, record or decide any part of
it (R14). `ois record` refuses a confirmation by such an actor, and a second successor of the same
finding. Until then, a passport that lists the intent carries a warning for an open `high` or
`critical` finding (R13).

## Records never change

Running a command again for the same thing prints the same reference and keeps the file. A
different record under an existing id is refused. Nothing is overwritten, as the specification
requires (section 6.3). Exit code 0 means the record is written or already there, and 1 means it
would break a rule and nothing was written. Exit code 2 means a file could not be read or an
argument is malformed.

## Pass them on

`ois record bundle .ois/ --output ois-bundle.json` packs records into one self-contained bundle,
each record once, and validates it. For a release, [build a Quality Passport](/build-a-passport/).
