---
title: Tests mit Kriterien verknüpfen
description: Nenne in jedem Test einen Kriterien-Schlüssel und mach aus jedem JUnit-XML-Bericht Evidence für ein freigegebenes Intent.
---

Sobald ein Intent freigegeben ist ([Intents schreiben und freigeben](/de/approve-intents/)), kann
jeder Test angeben, welches Kriterium er prüft. `ois junit --intent` macht dann aus dem
JUnit-XML-Bericht des Laufs Evidence für diese Kriterien, und der
[Quality Passport](/de/build-a-passport/) bekommt eine echte Intent-Abdeckung. Jedes
Test-Framework, das JUnit XML schreibt, funktioniert; für Gherkin-Feature-Dateien siehe
[Gherkin und Cucumber verwenden](/de/gherkin-cucumber/).

## 1. In jedem Test das Kriterium nennen

Ein Test nennt sein Kriterium über den Schlüssel, zum Beispiel `AC-1`, an einer von zwei Stellen,
die im Bericht ankommen: in einer Property `criterion` des Testfalls oder als ganzes Wort in
seinem Namen.

| Framework | Wie ein Test `AC-1` nennt |
| --- | --- |
| pytest | `@pytest.mark.criterion("AC-1")`, mit der `conftest.py` unten |
| JUnit 5 und 6 (Maven) | `@DisplayName("AC-1 rounds down")`, mit der Surefire-Einstellung unten |
| Jest | `test('AC-1 rounds down', …)`, mit `jest-junit` |
| Vitest | `test('AC-1 rounds down', …)`, mit `--reporter=junit` |
| Playwright | `annotation: { type: 'criterion', description: 'AC-1' }`, oder `AC-1` im Titel |

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

**Playwright** schreibt Annotationen als Properties, wenn der Reporter dafür eingestellt ist:

```ts
reporter: [['junit', { outputFile: 'results.xml', embedAnnotationsAsProperties: true }]]
```

`@Tag` von JUnit und die Option `tag` von Playwright kommen nicht im JUnit XML an; nimm deshalb
eine der Formen aus der Tabelle. Für Jest setzt du in den Optionen von `jest-junit`
`addFileAttribute: 'true'`, damit sich jeder Test seiner Datei zuordnen lässt.

## 2. Den Lauf aufzeichnen

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

- **Evidence** pro Test und genanntem Kriterium: `pass`, `fail`, `skipped` oder `error`. Ein Test,
  der mehrmals lief, behält sein schlechtestes Ergebnis. Tests ohne Schlüssel werden gezählt und
  ausgelassen.
- **Ein Test-Artefakt** pro Testdatei, festgelegt durch ihren `sha256` und den Commit, erzeugt von
  `--test-producer`: von dem, der die Tests geschrieben hat.
- **`--subject`** nennt den Code oder Build unter Test, damit die Evidence für dessen Release
  zählt.
- Ein Schlüssel, der kein Kriterium des Intents ist, oder ein Test, dessen Datei nicht in Git
  liegt, bekommt keine Evidence und wird gemeldet.

Die Records landen in `.ois/`, wo [`ois passport build`](/de/build-a-passport/) sie findet.
Fehlermeldungen und Stacktraces werden nicht übernommen.

## 3. Aus dem Intent abgeleitet?

Die Intent-Abdeckung zählt nur Evidence mit `derivedFrom: intent`, von Tests, die das Kriterium
und nicht den Code gesehen haben (Regeln R4 und R5). `ois junit` kann nicht beobachten, wie ein
Test geschrieben wurde, und stützt sich deshalb auf das, was festgehalten ist:

- **`--written-from-intent`** sagt, dass die Tests aus den genannten Kriterien geschrieben wurden,
  ohne den Code. Es hält diese Kriterien als Kontext der Testdatei fest, erklärt von dir. Der
  Validator meldet den Kontext als selbst erklärt (R12); er zählt in `intentCoverage`, nicht in
  `intentCoverageAttested`.
- **Ein bereits festgehaltenes Test-Artefakt**, zum Beispiel von der Laufzeitumgebung eines
  Test-Agenten mit [`ois record artifact --context … --context-recorded-by …`](/de/record/), wird
  für dieselbe Datei wiederverwendet. Sein Kontext entscheidet, und wenn eine Signatur dieser
  Laufzeitumgebung ihn abdeckt, gilt er als bestätigt.
- **Ohne beides** sagt die Evidence `derivedFrom: unknown`: ehrlich, und trotzdem ein Nachweis
  dessen, was gelaufen ist.

Wenn Tests und Subject vom selben Actor stammen oder ein festgehaltener Kontext Code enthält, sagt
die Evidence `unknown`, und der Grund wird gemeldet.
