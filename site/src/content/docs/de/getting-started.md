---
title: 'Erste Schritte: dein erstes OIS-Bundle'
description: Mach aus dem JUnit XML einer bestehenden Pipeline in rund 15 Minuten OIS-Records.
---

Diese Anleitung nimmt eine Pipeline, die bereits Tests ausführt, und lässt sie Records im Open
Intent Schema (OIS) erzeugen, ohne einen einzigen Test zu ändern. Das dauert rund 15 Minuten. Das
Ergebnis ist Konformität auf Level 1, "Observe" (Spezifikation Abschnitt 11.2).

**Du brauchst:** einen Git-Checkout des getesteten Codes, Tests, die JUnit XML schreiben können, und
entweder [uv](https://docs.astral.sh/uv/) (es bringt Python 3.13 oder neuer mit) oder Docker. Die
Sprache deines Projekts spielt keine Rolle: Die Befehle lesen das JUnit XML und den Git-Checkout,
nicht den Code. Sie funktionieren deshalb gleich für Java, Kotlin, TypeScript, Go oder .NET, auf
deinem Rechner und in CI.

## Was du bekommst

Nach jedem Pipeline-Lauf eine JSON-Datei, ein *Bundle*, die festhält:

- **welche Tests es gibt:** ein *Charakterisierungs-Intent* mit einem Kriterium pro Testfall. Es
  beschreibt, was deine Testsuite heute prüft, als Entwurf, bis jemand es reviewt.
- **in welchen Testdateien sie liegen:** ein *Artefakt* pro Testdatei, festgelegt durch Repository,
  Commit und den `sha256` der Datei, sodass jede spätere Änderung an einem Test erkennbar ist.
- **was jeder Test ergeben hat:** ein *Evidence*-Record pro Ergebnis (pass, fail, skipped, error),
  mit dem Zeitpunkt der Beobachtung und einem Link auf den Pipeline-Lauf.
- **wer was erzeugt hat:** ein *Actor* für deine Testsuite und einer für den Adapter, der die
  Ergebnisse aufgezeichnet hat.

Was es noch nicht behauptet: dass die Tests prüfen, was *gefordert* war. Jeder Evidence-Record sagt
`derivedFrom: unknown`, und die Intent-Abdeckung ist null. Das ist die ehrliche Ausgangslage für ein
bestehendes System und der Startpunkt für Level 2.

## 1. JUnit XML schreiben

Die meisten Test-Frameworks schreiben JUnit XML über eine Option oder einen Reporter. Einige
verbreitete:

| Framework | Wie |
| --- | --- |
| pytest | `pytest --junitxml=reports/junit.xml` |
| Maven Surefire | standardmässig nach `target/surefire-reports/TEST-*.xml` geschrieben |
| Gradle | standardmässig nach `build/test-results/test/TEST-*.xml` geschrieben |
| Jest | der Reporter `jest-junit`: `jest --reporters=default --reporters=jest-junit` |
| Go | `go test -v 2>&1 \| go-junit-report > report.xml` |
| .NET | `dotnet test --logger "junit;LogFilePath=report.xml"` mit `JunitXml.TestLogger` |
| Playwright | der eingebaute Reporter `junit` |

Ausgabepfade und Optionen findest du in der Dokumentation deines Frameworks.

## 2. Namespace und Suite-Namen wählen

- **`--namespace`** ist eine URI unter einer Domain, die deine Organisation kontrolliert, zum
  Beispiel `https://ois.your-company.example`. Jede Record-ID beginnt damit, sodass IDs
  verschiedener Organisationen nie kollidieren. Sie ist nur ein Bezeichner: Nichts ruft sie je ab,
  und sie muss nicht als Webseite existieren. Verwende in jeder Pipeline denselben Namespace.
- **`--suite`** nennt das Team oder die Testsuite, dem bzw. der die Tests gehören, zum Beispiel
  `"Team Billing"`. Der Wert benennt den Actor der Testsuite und erscheint in den Record-IDs.

## 3. Aus dem Report ein Bundle machen

Führe dies im Git-Checkout aus, in dem die Tests gelaufen sind:

```bash
uvx --from ois-tools ois junit reports/junit.xml \
  --namespace https://ois.acme.example \
  --suite "Team Billing" \
  --run https://ci.acme.example/pipelines/billing/runs/42 \
  --output ois-bundle.json
```

`--run` ist optional und verknüpft jedes Ergebnis mit dem Pipeline-Lauf. Du kannst mehrere Reports
auf einmal übergeben, zum Beispiel `target/surefire-reports/*.xml`.

Dasselbe mit dem Container-Image, zum Beispiel für einen Gradle-Build, ohne Python auf dem Rechner:

```bash
docker run --rm -v "$PWD:/work" --user "$(id -u):$(id -g)" \
  ghcr.io/openintentschema/ois-tools junit build/test-results/test/*.xml \
  --namespace https://ois.acme.example --suite "Team Billing" --output ois-bundle.json
```

Das aktuelle Verzeichnis wird unter `/work` eingehängt; `--user` sorgt dafür, dass das Bundle dir
gehört und nicht dem Container. Füge `--network none` hinzu, um zu sehen, dass es kein Netzwerk
braucht.

`ois junit` validiert das Bundle, bevor es geschrieben wird. Es endet mit 0 und schreibt die Datei,
oder es endet mit 1 und schreibt nichts.

## 4. Das Bundle ansehen

Für drei pytest-Tests in `tests/test_invoice.py` enthält das Bundle diese Records, hier gekürzt
(jeder Record trägt ausserdem `ois`, `id` und `createdAt`):

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
  "recordedBy": "https://ois.acme.example/actors/ois-junit@0.11.0",
  "run": "https://ci.acme.example/pipelines/billing/runs/42" }
```

Einige Details:

- **Kriterium-Schlüssel** (`TC-…`) sind ein Hash aus Klassen- und Testname. Sie bleiben von Lauf zu
  Lauf gleich, egal welche Zeichen ein Testname enthält.
- **Testdateien** stammen aus dem Attribut `file` des Reports oder aus dem Klassennamen
  (`com.acme.InvoiceTest` findet `src/test/java/com/acme/InvoiceTest.java`). Der Digest wird aus
  der Datei im ausgecheckten Commit berechnet. Ein Test, dessen Datei nicht gefunden wird, wird
  trotzdem aufgezeichnet, festgelegt allein durch den Commit.
- **Location** ist dein Remote `origin` beim aktuellen Commit. Zugangsdaten in der Remote-URL werden
  entfernt. Mit `--location` setzt du sie selbst.

## 5. Prüfen

`ois junit` hat das Bundle bereits validiert. Jede OIS-Datei lässt sich auch einzeln prüfen:

```bash
uvx --from ois-tools ois validate ois-bundle.json
# ois-bundle.json: conforms
```

Der Validator meldet jedes Problem mit seiner Regel aus Abschnitt 5 der Spezifikation, auf einer von
drei Stufen: violation, warning oder info.

## 6. In die Pipeline einbauen

**GitHub Actions**, nach dem Schritt, der die Tests ausführt:

```yaml
- uses: openintentschema/tools/.github/actions/setup@v0.11.0   # installs ois; pin the tag's commit SHA
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

`if: ${{ !cancelled() }}` zeichnet Ergebnisse auch auf, wenn Tests fehlschlagen; genau diese
Ergebnisse zählen am meisten.

**GitLab CI:** Binde das Template eines Release ein; der Job läuft im Container-Image und behält das
Bundle als Artefakt, auch wenn die Tests fehlgeschlagen sind:

```yaml
include:
  - remote: https://raw.githubusercontent.com/openintentschema/tools/v0.11.0/.gitlab/ci/ois.gitlab-ci.yml

ois:
  extends: .ois-junit
  needs: [test]
  variables:
    OIS_JUNIT_REPORTS: build/test-results/test/*.xml
    OIS_NAMESPACE: https://ois.acme.example
    OIS_SUITE: Team Billing
```

**Jede andere CI** führt das Container-Image nach den Tests im selben Checkout aus, ohne Python auf
dem Runner:

```bash
docker run --rm --network none -v "$PWD:/work" --user "$(id -u):$(id -g)" \
  ghcr.io/openintentschema/ois-tools:0.11.0 junit build/test-results/test/*.xml \
  --namespace https://ois.acme.example --suite "Team Billing" --output ois-bundle.json
```

Die Shell des Runners expandiert den Glob, bevor der Container startet; die Pfade sind daher relativ
zum Checkout, der unter `/work` eingehängt ist. Ohne Docker macht `uvx --from ois-tools==0.11.0
ois junit …` dasselbe. Der Job braucht immer den Checkout, in dem die Tests gelaufen sind, mit
seiner Git-Historie.

## Bevor du ein Bundle weitergibst

Bundles bleiben in deiner Organisation, ausser du entscheidest anders. Bevor du eines weitergibst,
prüfe, was es preisgibt (Spezifikation Abschnitt 12):

- **Testnamen** werden zu Aussagen von Kriterien. Sie dürfen keine Personendaten enthalten.
- **Repository-URLs und Pfade** zeigen interne Hostnamen und die Projektstruktur.
- **Pipeline-Links** (`--run`) zeigen auf deine CI.

## Nächste Schritte

- **Level 2, Intent-aware:** [Intents schreiben und freigeben](/de/approve-intents/) mit
  Akzeptanzkriterien, [in jedem Test sein Kriterium nennen](/de/link-tests/) und den Lauf mit
  `ois junit --intent` aufzeichnen; mit Gherkin [werden Feature-Dateien zum Intent](/de/gherkin-cucumber/). Die Evidence
  sagt dann `derivedFrom: intent`, und die Intent-Abdeckung beginnt zu steigen.
- **Den Rest der Lieferung aufzeichnen:** Actors, Build-Artefakte, Entscheidungen und Findings, mit
  [`ois record`](/de/record/).
- **Quality Passport:** [Intents, Evidence und Entscheidungen für ein Release](/de/build-a-passport/)
  in einer Attestation zusammenführen (Abschnitt 8) und [sie signieren](/de/sign/).
- **Den Standard mitgestalten:** Offene Fragen und vorgeschlagene Änderungen werden als
  [RFC-Issues](https://github.com/openintentschema/openintentschema/issues?q=label%3Arfc)
  diskutiert. Erkenntnisse aus echten Pipelines haben das grösste Gewicht.
