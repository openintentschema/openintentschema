---
title: Link tests to criteria
description: Name a criterion key in each test and turn any JUnit XML report into evidence for an approved intent.
---

Once an intent is approved ([Write and approve intents](/approve-intents/)), each test can say
which criterion it checks. `ois junit --intent` then turns the JUnit XML report of the run into
evidence for those criteria, and the [Quality Passport](/build-a-passport/) gets a real intent
coverage. Any test framework that writes JUnit XML works; for Gherkin feature files, see
[Use Gherkin and Cucumber](/gherkin-cucumber/).

## 1. Name the criterion in each test

A test names its criterion by key, for example `AC-1`, in one of two places that reach the
report: a `criterion` property of the test case, or its name as a whole word.

| Framework | How a test names `AC-1` |
| --- | --- |
| pytest | `@pytest.mark.criterion("AC-1")`, with the `conftest.py` below |
| JUnit 5 and 6 (Maven) | `@DisplayName("AC-1 rounds down")`, with the Surefire setting below |
| Jest | `test('AC-1 rounds down', …)`, with `jest-junit` |
| Vitest | `test('AC-1 rounds down', …)`, with `--reporter=junit` |
| Playwright | `annotation: { type: 'criterion', description: 'AC-1' }`, or `AC-1` in the title |

**pytest** writes `user_properties` into the report. This `conftest.py` turns the marker into one:

```python
def pytest_configure(config):
    config.addinivalue_line("markers", "criterion(key): the criterion a test checks")


def pytest_collection_modifyitems(items):
    for item in items:
        for mark in item.iter_markers("criterion"):
            item.user_properties.append(("criterion", mark.args[0]))
```

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

**Playwright** writes annotations as properties when the reporter is configured for it:

```ts
reporter: [['junit', { outputFile: 'results.xml', embedAnnotationsAsProperties: true }]]
```

JUnit's `@Tag` and Playwright's `tag` option do not reach JUnit XML, so use one of the forms in
the table. For Jest, set `addFileAttribute: 'true'` in the `jest-junit` options so that each
test can be traced to its file.

## 2. Record the run

```bash
ois junit build/test-results/*.xml --namespace https://ois.acme.example \
  --intent https://ois.acme.example/intents/INT-7@1 \
  --test-producer https://ois.acme.example/actors/qe-2c9d \
  --subject "$BUILD" --written-from-intent
```

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
  evidence and is reported.

The records go to `.ois/`, where [`ois passport build`](/build-a-passport/) finds them. Error
messages and stack traces are not copied.

## 3. Derived from the intent?

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
