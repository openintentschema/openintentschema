---
title: 'Getting started: your first OIS bundle'
description: Turn the JUnit XML of an existing pipeline into OIS records in about 15 minutes.
---

This guide takes a pipeline that already runs tests and makes it emit Open Intent Schema (OIS)
records, without changing a single test. It takes about 15 minutes. The result is Level 1
conformance, "Observe" (specification section 11.2).

**You need:** a Git checkout of the code under test, tests that can write JUnit XML, and either
[uv](https://docs.astral.sh/uv/) (it brings Python 3.13 or later along) or Docker. The language of
your project does not matter: the commands read the JUnit XML and the Git checkout, not the code,
so they work the same for Java, Kotlin, TypeScript, Go or .NET, on your machine and in CI.

## What you get

After every pipeline run, one JSON file, a *bundle*, that records:

- **which tests exist:** a *characterization intent* with one criterion per test case. It
  describes what your suite checks today, in draft, until someone reviews it.
- **which test files they live in:** one *artifact* per test file, pinned by repository, commit
  and the `sha256` of the file, so any later change to a test is detectable.
- **what each test returned:** one *evidence* record per result (pass, fail, skipped, error),
  with the time it was observed and a link to the pipeline run.
- **who produced what:** an *actor* for your test suite and one for the adapter that recorded
  the results.

What it does not claim yet: that the tests check what was *required*. Every evidence record says
`derivedFrom: unknown`, and intent coverage is zero. That is the honest baseline for an existing
system, and the starting point for Level 2.

## 1. Write JUnit XML

Most test frameworks write JUnit XML with a flag or a reporter. A few common ones:

| Framework | How |
| --- | --- |
| pytest | `pytest --junitxml=reports/junit.xml` |
| Maven Surefire | written by default to `target/surefire-reports/TEST-*.xml` |
| Gradle | written by default to `build/test-results/test/TEST-*.xml` |
| Jest | the `jest-junit` reporter: `jest --reporters=default --reporters=jest-junit` |
| Go | `go test -v 2>&1 \| go-junit-report > report.xml` |
| .NET | `dotnet test --logger "junit;LogFilePath=report.xml"` with `JunitXml.TestLogger` |
| Playwright | the built-in `junit` reporter |

See your framework's documentation for output paths and options.

## 2. Choose a namespace and a suite name

- **`--namespace`** is a URI under a domain your organization controls, for example
  `https://ois.your-company.example`. Every record id starts with it, so ids from different
  organizations never collide. It is an identifier only: nothing ever requests it, and it does
  not need to exist as a web page. Use the same namespace in every pipeline.
- **`--suite`** names the team or suite that owns the tests, for example `"Team Billing"`. It
  names the test suite actor and appears in the record ids.

## 3. Turn the report into a bundle

Run this in the Git checkout the tests ran in:

```bash
uvx --from ois-tools ois junit reports/junit.xml \
  --namespace https://ois.acme.example \
  --suite "Team Billing" \
  --run https://ci.acme.example/pipelines/billing/runs/42 \
  --output ois-bundle.json
```

`--run` is optional and links every result to the pipeline run. Several reports can be passed at
once, for example `target/surefire-reports/*.xml`.

The same with the container image, for example for a Gradle build, without Python on the machine:

```bash
docker run --rm -v "$PWD:/work" --user "$(id -u):$(id -g)" \
  ghcr.io/openintentschema/ois-tools junit build/test-results/test/*.xml \
  --namespace https://ois.acme.example --suite "Team Billing" --output ois-bundle.json
```

The current directory is mounted at `/work`; `--user` makes the bundle yours rather than the
container's. Add `--network none` to see that it needs no network.

`ois junit` validates the bundle before writing it. It exits with 0 and writes the file, or
exits with 1 and writes nothing.

## 4. Look at the bundle

For three pytest tests in `tests/test_invoice.py`, the bundle holds these records, shortened
here (every record also carries `ois`, `id` and `createdAt`):

```json
{ "type": "actor", "id": "https://ois.acme.example/actors/team-billing-tests",
  "kind": "tool", "name": "Team Billing test suite", "version": "unknown" }

{ "type": "intent", "id": "https://ois.acme.example/intents/team-billing-characterization",
  "version": 1, "title": "Characterization of the Team Billing test suite", "status": "draft",
  "criteria": [
    { "key": "TC-f8c16e8744a9", "statement": "tests.test_invoice.test_rounds_to_five_rappen",
      "notation": "text", "kind": "functional" } ] }

{ "type": "artifact", "id": "https://ois.acme.example/artifacts/test-eaf5767278f44715",
  "kind": "test", "path": "tests/test_invoice.py",
  "location": "git+https://git.acme.example/billing.git@dd5f22c81c845665cf67e6033601d242a54de29b",
  "digest": { "sha256": "5a756a0a…", "gitCommit": "dd5f22c8…" },
  "producedBy": "https://ois.acme.example/actors/team-billing-tests@unknown" }

{ "type": "evidence",
  "criterion": "https://ois.acme.example/intents/team-billing-characterization@1#TC-f8c16e8744a9",
  "test": "https://ois.acme.example/artifacts/test-eaf5767278f44715",
  "derivedFrom": "unknown", "result": "pass", "observedAt": "2026-10-28T15:19:57Z",
  "recordedBy": "https://ois.acme.example/actors/ois-junit@0.10.0",
  "run": "https://ci.acme.example/pipelines/billing/runs/42" }
```

A few details:

- **Criterion keys** (`TC-…`) are a hash of class and test name. They stay the same from run to
  run, whatever characters a test name contains.
- **Test files** come from the report's `file` attribute or from the class name
  (`com.acme.InvoiceTest` finds `src/test/java/com/acme/InvoiceTest.java`). The digest is taken
  from the file at the checked-out commit. A test whose file cannot be found is still recorded,
  pinned by the commit alone.
- **Location** is your `origin` remote at the current commit. Credentials in the remote URL are
  removed. Pass `--location` to set it yourself.

## 5. Check it

`ois junit` has already validated the bundle. Any OIS file can also be checked on its own:

```bash
uvx --from ois-tools ois validate ois-bundle.json
# ois-bundle.json: conforms
```

The validator reports every problem with its rule from section 5 of the specification, at one of
three levels: violation, warning or info.

## 6. Add it to your pipeline

**GitHub Actions**, after the step that runs the tests:

```yaml
- uses: openintentschema/tools/.github/actions/setup@v0.10.0   # installs ois; pin the tag's commit SHA
- name: Record test results as OIS
  if: ${{ !cancelled() }}
  run: >
    ois junit reports/junit.xml
    --namespace https://ois.acme.example --suite "Team Billing"
    --run "${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}"
    --output ois-bundle.json
- uses: actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9 # v7.0.2
  if: ${{ !cancelled() }}
  with:
    name: ois-bundle
    path: ois-bundle.json
```

`if: ${{ !cancelled() }}` records results when tests fail too; those are the results that matter
most.

**GitLab CI:** include the template of a release; the job runs in the container image and keeps
the bundle as an artifact, also when the tests failed:

```yaml
include:
  - remote: https://raw.githubusercontent.com/openintentschema/tools/v0.10.0/.gitlab/ci/ois.gitlab-ci.yml

ois:
  extends: .ois-junit
  needs: [test]
  variables:
    OIS_JUNIT_REPORTS: build/test-results/test/*.xml
    OIS_NAMESPACE: https://ois.acme.example
    OIS_SUITE: Team Billing
```

**Any other CI** runs the container image after the tests, in the same checkout, without Python on
the runner:

```bash
docker run --rm --network none -v "$PWD:/work" --user "$(id -u):$(id -g)" \
  ghcr.io/openintentschema/ois-tools:0.10.0 junit build/test-results/test/*.xml \
  --namespace https://ois.acme.example --suite "Team Billing" --output ois-bundle.json
```

The glob is expanded by the runner's shell before the container starts, so the paths are
relative to the checkout, which is mounted at `/work`. Without Docker, `uvx --from ois-tools==0.10.0
ois junit …` does the same. The job always needs the checkout the tests ran in, with its Git
history.

## Before you share a bundle

Bundles stay inside your organization unless you decide otherwise. Before passing one on, check
what it reveals (specification section 12):

- **Test names** become criterion statements. They must not contain personal data.
- **Repository URLs and paths** show internal host names and project structure.
- **Pipeline links** (`--run`) point to your CI.

## Next steps

- **Level 2, intent-aware:** [write and approve intents](/approve-intents/) with acceptance
  criteria, derive tests from them and record what each test producer was given (`context`);
  with Gherkin, [feature files become the intent](/gherkin-cucumber/). Evidence then says
  `derivedFrom: intent`, and intent coverage starts to rise.
- **Record the rest of the delivery:** actors, build artifacts, decisions and findings, with
  [`ois record`](/record/).
- **Quality Passport:** [collect intents, evidence and decisions for a release](/build-a-passport/)
  into one attestation (section 8), and [sign it](/sign/).
- **Shape the standard:** open questions and proposed changes are discussed as
  [RFC issues](https://github.com/openintentschema/openintentschema/issues?q=label%3Arfc).
  Findings from real pipelines carry the most weight.
