---
title: Use Gherkin and Cucumber
description: Turn feature files into an intent and a Cucumber run into evidence derived from it.
---

Teams that write acceptance criteria as Gherkin feature files already have most of an intent.
`ois intent from-gherkin` turns the feature files into one, and `ois cucumber` turns the run of
those scenarios into evidence. Both are part of the [`ois-tools`](/develop/tools/) package. A
scenario that runs exactly as its approved criterion is worded counts as derived from the intent,
without any further step. The commands assume `ois` is installed and `OIS_NAMESPACE` is set
([Getting started](/getting-started/#next-steps)).

## 1. Tag each scenario with its key

A tag names the criterion a scenario stands for. The key stays the same across versions, so
renaming a scenario does not break the link:

```gherkin
Feature: Invoices round to five Rappen
  Background:
    Given the currency is CHF

  @AC-1
  Scenario: Round down
    Given an invoice total of CHF 10.02
    When the invoice is issued
    Then the amount due is CHF 10.00

  @AC-2
  Scenario Outline: Reject negative amounts
    When an amount of <amount> is entered
    Then the invoice is rejected

    Examples:
      | amount |
      | -1     |

  Scenario: Exploratory, large totals
    Given an invoice total of CHF 999999.99
    When the invoice is issued
```

Keys look like `AC-1` or `REQ-12` by default; `--key-pattern` takes another regular expression.
Scenarios without a key tag, for example exploratory ones, are left out.

## 2. Write and approve the intent

```bash
ois intent from-gherkin features/rounding.feature --id https://ois.acme.example/intents/INT-7
PO=$(ois record actor --kind human --name po-7f3a)   # the product owner, who wrote the scenarios
ois intent approve .ois/intents/INT-7-v1.ois.yaml --by "$PO"
```

Each keyed scenario becomes a criterion in `gherkin` notation. Its statement is the scenario's
steps with the background before them, and for an outline its examples. The title is the
feature's name. Approve it as any other intent ([Write and approve intents](/approve-intents/)).

## 3. Run Cucumber with the message formatter

The tools read [Cucumber Messages](https://github.com/cucumber/messages), the structured output
that Cucumber recommends:

| Runner | Option |
| --- | --- |
| cucumber-js | `--format message:cucumber.ndjson` |
| cucumber-jvm | `--plugin message:cucumber.ndjson` |
| Reqnroll (.NET) | the Cucumber Messages formatter |

## 4. Record the run

With the build recorded before the run, as for any test
([Link tests to criteria](/link-tests/#2-record-the-build-before-the-tests-run)):

```bash
ois cucumber cucumber.ndjson --intent https://ois.acme.example/intents/INT-7@1 \
  --test-producer "$PO" --subject "$BUILD"
```

After one line per record it writes, it reports:

```
ois cucumber: 2 results: 2 derived from the intent, 0 not
ois cucumber: no evidence: features/rounding.feature: Exploratory, large totals (no key tag)
```

- **Evidence** per executed scenario, an outline once per example row. A failed step gives
  `fail`, an undefined or ambiguous step `error`, a skipped or pending one `skipped`.
- **A test artifact** per feature file, pinned by its `sha256` and commit, produced by
  `--test-producer`: whoever wrote the scenarios.
- **`derivedFrom: intent`** where a scenario is worded exactly as its approved criterion. The test
  then *is* the criterion; `ois cucumber` checks this and records it as the test's context, with
  itself as `contextRecordedBy`. Rule R12 reports that context as self-declared, because the
  `ois cucumber` actor carries no `identity` a signature could match.
- **A scenario that differs** from its criterion, because one of them changed, is recorded with
  `derivedFrom: unknown` and reported. Approve a new intent version, or bring the scenario back
  in line.

The records go to `.ois/`, where [`ois passport build`](/build-a-passport/) finds them. Error
messages and stack traces from the run are not copied.

## What it does not show

The scenario text is independent of the code when it is written by someone other than the
developers, and rule R5 checks that. The step definitions that make a scenario run are code,
usually written by developers; what a step really checks lives there, and OIS does not describe
it. Review step definitions like any other test code.
