---
title: Link tests to criteria
description: Name a criterion key in each test and turn its test report into evidence for an approved intent.
---

Once an intent is approved ([Write and approve intents](/approve-intents/)), each test can say
which criterion it checks. `ois junit --intent` then turns the report of the run into evidence for
those criteria, and the [Quality Passport](/build-a-passport/) gets a real intent coverage. Any
framework that writes JUnit XML works, and so do the native reports of Playwright, Jest, Vitest,
Go and .NET ([Getting started](/getting-started/#1-write-a-test-report)); for Gherkin feature
files, see [Use Gherkin and Cucumber](/gherkin-cucumber/). The commands assume `ois` is installed
and `OIS_NAMESPACE` is set ([Getting started](/getting-started/#next-steps)).

## 1. Name the criterion in each test

A test names its criterion by key, for example `AC-1`, in a place that reaches the report: a
`criterion` property or annotation, a tag or test category, or its name, where the key stands
between characters that are not letters or digits.

| Framework | How a test names `AC-1` |
| --- | --- |
| pytest | `@pytest.mark.criterion("AC-1")`, with the `conftest.py` below |
| pytest-bdd | `@AC-1` on the scenario, with the same `conftest.py` |
| JUnit 5 and 6 (Maven) | `@DisplayName("AC-1 rounds down")`, with the Surefire setting below |
| JUnit 5 and 6 (Gradle) | `@DisplayName("AC-1 rounds down")`, which Gradle writes as the test name |
| Jest | `test('AC-1 rounds down', …)` |
| Vitest | `test('rounds down', { tags: ['AC-1'] }, …)` with the JSON reporter, or `AC-1` in the title |
| Playwright | `test('rounds down', { tag: '@AC-1' }, …)` with the JSON reporter, `annotation: { type: 'criterion', description: 'AC-1' }`, or `AC-1` in the title |
| Go | `t.Run("AC-1 rounds down", …)` |
| xUnit | `[Fact(DisplayName = "AC-1 rounds down")]` |
| MSTest | `[TestCategory("AC-1")]` |

**pytest** writes `user_properties` into the report. This `conftest.py` turns the marker into one,
and with pytest-bdd a scenario's key tag into the marker:

```python
import re

import pytest


def pytest_configure(config):
    config.addinivalue_line("markers", "criterion(key): the criterion a test checks")


def pytest_collection_modifyitems(items):
    for item in items:
        for mark in item.iter_markers("criterion"):
            item.user_properties.append(("criterion", mark.args[0]))


@pytest.hookimpl(optionalhook=True)
def pytest_bdd_apply_tag(tag, function):  # pytest-bdd: a scenario tag such as @AC-1
    if re.fullmatch(r"[A-Z][A-Z0-9]*-[0-9]+", tag):
        return pytest.mark.criterion(tag)(function)
    return None
```

With pytest-bdd the test artifact is the module that calls `scenarios()`, not the feature file.
To record the feature file and check that each scenario is worded as its criterion, use
[`ois cucumber`](/gherkin-cucumber/) with `--cucumberjson`.

**JUnit with Maven Surefire** writes method names unless told to write display names:

```xml
<plugin>
  <groupId>org.apache.maven.plugins</groupId>
  <artifactId>maven-surefire-plugin</artifactId>
  <configuration>
    <statelessTestsetReporter implementation="org.apache.maven.plugin.surefire.extensions.junit5.JUnit5Xml30StatelessReporter">
      <usePhrasedTestCaseMethodName>true</usePhrasedTestCaseMethodName>
    </statelessTestsetReporter>
  </configuration>
</plugin>
```

**Vitest** accepts only tags declared in its configuration, for example
`test: { tags: [{ name: 'AC-1' }] }`.

**Playwright's JUnit reporter** writes annotations as properties when configured for it; tags
reach only the JSON reporter:

```ts
reporter: [['junit', { outputFile: 'results.xml', embedAnnotationsAsProperties: true }]]
```

JUnit's `@Tag`, xUnit's `[Trait]` and MSTest's display names do not reach the report, so use one
of the forms in the table. With `jest-junit`, set `addFileAttribute: 'true'` so that each test
can be traced to its file; Jest's own JSON report has it.

## 2. Record the build before the tests run

Evidence counts for a build only if it was observed after the build was recorded. Record the
build artifact right after building it, and the actor who wrote the tests:

```bash
CI=$(ois record actor --kind tool --name "CI build" --version 7)
BUILD=$(ois record artifact dist/billing-2026.10.4-py3-none-any.whl --kind build \
  --location pkg:pypi/billing@2026.10.4 --produced-by "$CI")
QE=$(ois record actor --kind human --name qe-2c9d)
```

## 3. Record the run

After the tests:

```bash
ois junit build/test-results/test/*.xml \
  --intent https://ois.acme.example/intents/INT-7@1 \
  --test-producer "$QE" --subject "$BUILD" --written-from-intent
```

After one line per record it writes, it reports:

```
ois junit: 2 results: 2 derived from the intent, 0 not
ois junit: 2 tests without a criterion key
```

- **Evidence** per test and criterion it names: `pass`, `fail`, `skipped` or `error`. A test that
  ran more than once keeps its worst result. Tests without a key are counted and left out.
- **A test artifact** per test file, pinned by its `sha256` and commit, produced by
  `--test-producer`: whoever wrote the tests.
- **`--subject`** names the code or build under test, so that the evidence counts for its release.
- A key that is not a criterion of the intent, or a test whose file is not in Git, gets no
  evidence and is reported. (Without `--intent`, such a test is pinned by the commit instead.)

The records go to `.ois/`, where [`ois passport build`](/build-a-passport/) finds them; with
`--intent`, `ois junit` writes no bundle. Error messages and stack traces are not copied.

**In CI**, intents and their approvals are committed in `.ois/`, while evidence arises per run.
Hand the run's records to the release job as an artifact: upload `.ois/` itself, or one
self-contained bundle of it written with `ois record bundle .ois/ --output ois-bundle.json`.

## 4. Derived from the intent?

Intent coverage counts only evidence with `derivedFrom: intent`, from tests that saw the
criterion and not the code (rules R4 and R5). `ois junit` cannot observe how a test was written,
so it relies on what has been recorded:

- **`--written-from-intent`** says that the tests were written from the criteria they name,
  without the code. It records those criteria as the test file's context, declared by you. The
  validator reports the context as self-declared (R12); it counts in `intentCoverage`, not in
  `intentCoverageAttested`.
- **A test artifact already recorded**, for example by the runtime of a test agent with
  [`ois record artifact --context … --context-recorded-by …`](/record/), is reused for the same
  file. Its context decides, and if a signature by that runtime covers it, it counts as attested.
- **Without either**, evidence says `derivedFrom: unknown`: honest, and still a record of what ran.

If the tests and the subject were produced by the same actor, or a recorded context includes
code, the evidence says `unknown` and the reason is reported.
