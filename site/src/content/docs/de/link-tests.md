---
title: Tests mit Kriterien verknüpfen
description: Nenne in jedem Test einen Kriterien-Schlüssel und mach aus seinem Testbericht Evidence für ein freigegebenes Intent.
---

Sobald ein Intent freigegeben ist ([Intents schreiben und freigeben](/de/approve-intents/)), kann
jeder Test angeben, welches Kriterium er prüft. `ois junit --intent` macht dann aus dem Bericht
des Laufs Evidence für diese Kriterien, und der [Quality Passport](/de/build-a-passport/) bekommt
eine echte Intent-Abdeckung. Jedes Framework, das JUnit XML schreibt, funktioniert, ebenso die
eigenen Berichte von Playwright, Jest, Vitest, Go und .NET
([Erste Schritte](/de/getting-started/#1-einen-testbericht-schreiben)); für Gherkin-Feature-Dateien
siehe [Gherkin und Cucumber verwenden](/de/gherkin-cucumber/).
Die Befehle setzen voraus, dass `ois` installiert und `OIS_NAMESPACE` gesetzt ist
([Erste Schritte](/de/getting-started/#nächste-schritte)).

## 1. In jedem Test das Kriterium nennen

Ein Test nennt sein Kriterium über den Schlüssel, zum Beispiel `AC-1`, an einer Stelle, die im
Bericht ankommt: in einer Property oder Annotation `criterion`, in einem Tag oder einer
Testkategorie oder in seinem Namen, wo der Schlüssel zwischen Zeichen steht, die keine Buchstaben
oder Ziffern sind.

| Framework | Wie ein Test `AC-1` nennt |
| --- | --- |
| pytest | `@pytest.mark.criterion("AC-1")`, mit der `conftest.py` unten |
| JUnit 5 und 6 (Maven) | `@DisplayName("AC-1 rounds down")`, mit der Surefire-Einstellung unten |
| Jest | `test('AC-1 rounds down', …)` |
| Vitest | `test('rounds down', { tags: ['AC-1'] }, …)` mit dem JSON-Reporter, oder `AC-1` im Titel |
| Playwright | `test('rounds down', { tag: '@AC-1' }, …)` mit dem JSON-Reporter, `annotation: { type: 'criterion', description: 'AC-1' }`, oder `AC-1` im Titel |
| Go | `t.Run("AC-1 rounds down", …)` |
| xUnit | `[Fact(DisplayName = "AC-1 rounds down")]` |
| MSTest | `[TestCategory("AC-1")]` |

**pytest** schreibt `user_properties` in den Bericht. Diese `conftest.py` macht aus dem Marker
eine:

```python
def pytest_configure(config):
    config.addinivalue_line("markers", "criterion(key): the criterion a test checks")


def pytest_collection_modifyitems(items):
    for item in items:
        for mark in item.iter_markers("criterion"):
            item.user_properties.append(("criterion", mark.args[0]))
```

**JUnit mit Maven Surefire** schreibt Methodennamen, ausser es soll Anzeigenamen schreiben:

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

**Vitest** nimmt nur Tags an, die in seiner Konfiguration deklariert sind, zum Beispiel
`test: { tags: [{ name: 'AC-1' }] }`.

**Der JUnit-Reporter von Playwright** schreibt Annotationen als Properties, wenn er dafür
eingestellt ist; Tags kommen nur im JSON-Reporter an:

```ts
reporter: [['junit', { outputFile: 'results.xml', embedAnnotationsAsProperties: true }]]
```

`@Tag` von JUnit, `[Trait]` von xUnit und die Anzeigenamen von MSTest kommen nicht im Bericht an;
nimm deshalb eine der Formen aus der Tabelle. Mit `jest-junit` setzt du `addFileAttribute: 'true'`,
damit sich jeder Test seiner Datei zuordnen lässt; der eigene JSON-Bericht von Jest enthält sie.

## 2. Den Build vor dem Testlauf erfassen

Evidence zählt für einen Build nur, wenn sie nach der Erfassung des Builds beobachtet wurde.
Erfasse das Build-Artefakt direkt nach dem Bauen, und den Actor, der die Tests geschrieben hat:

```bash
CI=$(ois record actor --kind tool --name "CI build" --version 7)
BUILD=$(ois record artifact dist/billing-2026.10.4-py3-none-any.whl --kind build \
  --location pkg:pypi/billing@2026.10.4 --produced-by "$CI")
QE=$(ois record actor --kind human --name qe-2c9d)
```

## 3. Den Lauf aufzeichnen

Nach den Tests:

```bash
ois junit build/test-results/test/*.xml \
  --intent https://ois.acme.example/intents/INT-7@1 \
  --test-producer "$QE" --subject "$BUILD" --written-from-intent
```

Nach einer Zeile pro geschriebenem Record meldet es:

```
ois junit: 2 results: 2 derived from the intent, 0 not
ois junit: 2 tests without a criterion key
```

- **Evidence** pro Test und genanntem Kriterium: `pass`, `fail`, `skipped` oder `error`. Ein Test,
  der mehrmals lief, behält sein schlechtestes Ergebnis. Tests ohne Schlüssel werden gezählt und
  ausgelassen.
- **Ein Test-Artefakt** pro Testdatei, festgelegt durch ihren `sha256` und den Commit, erzeugt von
  `--test-producer`: von dem, der die Tests geschrieben hat.
- **`--subject`** nennt den Code oder Build unter Test, damit die Evidence für dessen Release
  zählt.
- Ein Schlüssel, der kein Kriterium des Intents ist, oder ein Test, dessen Datei nicht in Git
  liegt, bekommt keine Evidence und wird gemeldet. (Ohne `--intent` wird ein solcher Test
  stattdessen durch den Commit festgelegt.)

Die Records landen in `.ois/`, wo [`ois passport build`](/de/build-a-passport/) sie findet; mit
`--intent` schreibt `ois junit` kein Bundle. Fehlermeldungen und Stacktraces werden nicht übernommen.

**In der CI** sind Intents und ihre Freigaben in `.ois/` committet, während Evidence pro Lauf
entsteht. Gib die Records des Laufs als Artefakt an den Release-Job weiter: Lade `.ois/` selbst hoch
oder ein in sich geschlossenes Bundle davon, geschrieben mit `ois record bundle .ois/ --output ois-bundle.json`.

## 4. Aus dem Intent abgeleitet?

Die Intent-Abdeckung zählt nur Evidence mit `derivedFrom: intent`, von Tests, die das Kriterium
und nicht den Code gesehen haben (Regeln R4 und R5). `ois junit` kann nicht beobachten, wie ein
Test geschrieben wurde, und stützt sich deshalb auf das, was festgehalten ist:

- **`--written-from-intent`** sagt, dass die Tests aus den genannten Kriterien geschrieben wurden,
  ohne den Code. Es hält diese Kriterien als Kontext der Testdatei fest, erklärt von dir. Der
  Validator meldet den Kontext als selbst deklariert (R12); er zählt in `intentCoverage`, nicht in
  `intentCoverageAttested`.
- **Ein bereits festgehaltenes Test-Artefakt**, zum Beispiel von der Laufzeitumgebung eines
  Test-Agenten mit [`ois record artifact --context … --context-recorded-by …`](/de/record/), wird
  für dieselbe Datei wiederverwendet. Sein Kontext entscheidet, und wenn eine Signatur dieser
  Laufzeitumgebung ihn abdeckt, gilt er als bestätigt.
- **Ohne beides** sagt die Evidence `derivedFrom: unknown`: ehrlich, und trotzdem ein Nachweis
  dessen, was gelaufen ist.

Wenn Tests und Subject vom selben Actor stammen oder ein festgehaltener Kontext Code enthält, sagt
die Evidence `unknown`, und der Grund wird gemeldet.
