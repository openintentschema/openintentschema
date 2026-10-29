---
title: Write and approve intents
description: Write a requirement with acceptance criteria as an OIS intent, approve it and version it.
---

The first step towards Level 2, "Intent-aware": requirements become intents with acceptance
criteria, approved by a person and bound to their exact text. Tests derived from them can then
reference a criterion, and evidence says `derivedFrom: intent`.

`ois intent`, part of the [`ois-tools`](/develop/tools/) package, computes the digests and
writes the approval, which are error-prone by hand.

## 1. Write the intent

Intents can be written in YAML (specification section 7); feature files in Gherkin become one with
`ois intent from-gherkin` ([Use Gherkin and Cucumber](/gherkin-cucumber/)). Keep one file per intent
version, for example under `.ois/intents/`:

```yaml
# .ois/intents/INT-7.ois.yaml
id: https://ois.acme.example/intents/INT-7
createdAt: 2026-10-28T09:00:00Z
version: 1
title: Invoices round to five Rappen
status: draft
language: en
risk: medium
criteria:
  - key: AC-1
    notation: gherkin
    kind: functional
    statement: >-
      Given an invoice total of CHF 10.02, when the invoice is issued,
      then the amount due is CHF 10.00
  - key: AC-2
    notation: ears
    kind: functional
    statement: WHEN an amount is negative, THE billing service SHALL reject the invoice
```

- **`id`** is a URI under your namespace; the same id holds every version of the intent.
- **`key`** names a criterion for good: it stays the same across versions.
- **`notation`** is `gherkin`, `ears` or `text`; **`kind`** is `functional` or `non-functional`. A
  non-functional criterion can carry a measurable `target`, for example
  `{metric: responseTimeP95, operator: lte, value: 500, unit: ms}`; [`ois measure`](/measure/)
  records a load test against it.

YAML is read so that it converts to JSON without loss: dates stay text, and tags, merge keys and
duplicate keys are refused.

## 2. Approve it

```bash
uvx --from ois-tools ois intent approve .ois/intents/INT-7.ois.yaml \
  --by https://ois.acme.example/actors/po-7f3a
```

This writes two records:

- `.ois/intents/INT-7-v1.ois.json`: the intent with status `approved`, a digest per criterion and
  a digest of the whole intent (section 6.4);
- `.ois/decisions/INT-7-v1-approval.ois.json`: the intent-approval decision, whose `subjectDigest`
  equals the intent's digest (rule R1).

`--by` names the approving actor. Rule R1 expects a human. Its record comes from
[`ois record`](/record/): `ois record actor --kind human --name po-7f3a` prints the reference to pass.
Add `--policy` and `--policy-version` to record the policy the approval followed, for example your
definition of ready.

An approved intent never changes. If its content no longer matches its digest, `ois intent approve`
refuses it.

## 3. Change it: a new version

```bash
uvx --from ois-tools ois intent next .ois/intents/INT-7-v1.ois.json
```

writes `.ois/intents/INT-7-v2.ois.yaml`: version 2, a draft that `supersedes` version 1. Edit it,
then see which evidence stays valid:

```bash
uvx --from ois-tools ois intent compare .ois/intents/INT-7-v1.ois.json .ois/intents/INT-7-v2.ois.yaml
```

```
AC-1: unchanged, evidence carries over
AC-2: changed, evidence is stale
```

Evidence for version 1 counts for version 2 only where the criterion is unchanged (section 6.3).
Changing `criticality` does not make evidence stale. Approve version 2 the same way as version 1.

## 4. Derive tests from the criteria

With approved intents in place, tests can be written against a criterion, by a person or by an
agent that never sees the code. Their evidence references the criterion, for example
`https://ois.acme.example/intents/INT-7@1#AC-2`, and states `derivedFrom: intent`. The validator then
checks that the test saw the criterion and no code (R4) and that its producer differs from the
code's (R5); see [Core concepts](/learn/core-concepts/). [Link tests to criteria](/link-tests/)
shows how a test names its criterion and how `ois junit --intent` records the run; [`ois
record`](/record/) writes single records.

When the release is ready, [build a Quality Passport](/build-a-passport/) from these records.
