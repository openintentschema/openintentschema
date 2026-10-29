---
title: Gherkin und Cucumber verwenden
description: Mach aus Feature-Dateien ein Intent und aus einem Cucumber-Lauf Evidence, die davon abgeleitet ist.
---

Teams, die Akzeptanzkriterien als Gherkin-Feature-Dateien schreiben, haben den grössten Teil eines
Intents bereits. `ois intent from-gherkin` macht aus den Feature-Dateien ein Intent, und
`ois cucumber` macht aus dem Lauf dieser Szenarien Evidence. Beide sind Teil des Pakets
[`ois-tools`](/de/develop/tools/). Ein Szenario, das genau so läuft, wie sein freigegebenes
Kriterium formuliert ist, gilt ohne weiteren Schritt als vom Intent abgeleitet.
Die Befehle setzen voraus, dass `ois` installiert und `OIS_NAMESPACE` gesetzt ist
([Erste Schritte](/de/getting-started/#nächste-schritte)).

## 1. Jedes Szenario mit seinem Schlüssel taggen

Ein Tag nennt das Kriterium, für das ein Szenario steht. Der Schlüssel bleibt über alle Versionen
gleich, sodass das Umbenennen eines Szenarios die Verknüpfung nicht bricht:

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

Schlüssel sehen standardmässig aus wie `AC-1` oder `REQ-12`; `--key-pattern` nimmt einen anderen
regulären Ausdruck entgegen. Szenarien ohne Schlüssel-Tag, zum Beispiel explorative, werden
weggelassen.

## 2. Das Intent schreiben und freigeben

```bash
ois intent from-gherkin features/rounding.feature --id https://ois.acme.example/intents/INT-7
PO=$(ois record actor --kind human --name po-7f3a)   # the product owner, who wrote the scenarios
ois intent approve .ois/intents/INT-7-v1.ois.yaml --by "$PO"
```

Jedes Szenario mit Schlüssel wird zu einem Kriterium in der Notation `gherkin`. Seine Aussage
besteht aus den Schritten des Szenarios mit dem Background davor, bei einer Outline zusätzlich aus
ihren Examples. Der Titel ist der Name des Features. Gib es frei wie jedes andere Intent
([Intents schreiben und freigeben](/de/approve-intents/)).

## 3. Die Szenarien mit einem Bericht ausführen

`ois cucumber` liest [Cucumber Messages](https://github.com/cucumber/messages), die strukturierte
Ausgabe, die Cucumber empfiehlt, Cucumber JSON und das JSON von behave:

| Runner | Option | Bericht |
| --- | --- | --- |
| cucumber-js | `--format message:cucumber.ndjson` | Cucumber Messages |
| cucumber-jvm | `cucumber.plugin=message:cucumber.ndjson`, oder `json:cucumber.json` | Cucumber Messages oder Cucumber JSON |
| Reqnroll (.NET) | der Formatter für Cucumber Messages | Cucumber Messages |
| Godog | `Format: "cucumber:cucumber.json"` in `godog.Options` | Cucumber JSON |
| pytest-bdd | `--cucumberjson=cucumber.json` | Cucumber JSON |
| behave | `--format json --outfile behave.json` | behave JSON |

Die JSON-Berichte enthalten keinen Szenariotext, der sich vergleichen liesse, nur, wo jedes
Szenario steht. `ois cucumber` liest das Szenario aus der Feature-Datei im Checkout; zeichne den
Lauf deshalb auf dem Commit auf, auf dem er lief. Als Zeitpunkt der Evidence nimmt es den Moment,
in dem der Bericht geschrieben wurde. cucumber-jvm nennt Feature-Dateien auf dem Klassenpfad, etwa
`classpath:features/rounding.feature`; `ois cucumber` nimmt die eine Datei in Git, deren Pfad so
endet.

## 4. Den Lauf aufzeichnen

Mit dem Build, der vor dem Lauf erfasst wurde, wie bei jedem Test
([Tests mit Kriterien verknüpfen](/de/link-tests/#2-den-build-vor-dem-testlauf-erfassen)):

```bash
ois cucumber cucumber.ndjson --intent https://ois.acme.example/intents/INT-7@1 \
  --test-producer "$PO" --subject "$BUILD"         # or cucumber.json, behave.json
```

Nach einer Zeile pro geschriebenem Record meldet es:

```
ois cucumber: 2 results: 2 derived from the intent, 0 not
ois cucumber: no evidence: features/rounding.feature: Exploratory, large totals (no key tag)
```

- **Evidence** pro ausgeführtem Szenario, bei einer Outline einmal pro Zeile der Examples. Ein
  fehlgeschlagener Schritt ergibt `fail`, ein undefinierter oder mehrdeutiger Schritt `error`, ein
  übersprungener oder ausstehender `skipped`.
- **Ein Test-Artefakt** pro Feature-Datei, festgelegt durch ihren `sha256` und den Commit, erzeugt
  von `--test-producer`: wer auch immer die Szenarien geschrieben hat.
- **`derivedFrom: intent`** dort, wo ein Szenario genau so formuliert ist wie sein freigegebenes
  Kriterium. Der Test *ist* dann das Kriterium; `ois cucumber` prüft das und hält es als Kontext
  des Tests fest, mit sich selbst als `contextRecordedBy`. Dieser Actor trägt keine `identity`,
  deshalb meldet Regel R12 den Kontext als selbst deklariert. Nenne stattdessen mit
  `--context-recorded-by "$PIPELINE"` die Pipeline, die `ois cucumber` ausführt und das Bundle
  signiert; ihre Signatur macht den Kontext dann bestätigt
  ([Bundles und Passports signieren](/de/sign/)).
- **Ein Szenario, das abweicht** von seinem Kriterium, weil sich eines von beiden geändert hat, wird
  mit `derivedFrom: unknown` aufgezeichnet und gemeldet. Gib eine neue Intent-Version frei oder
  bring das Szenario wieder in Einklang.

Die Records landen in `.ois/`, wo [`ois passport build`](/de/build-a-passport/) sie findet.
Fehlermeldungen und Stacktraces aus dem Lauf werden nicht übernommen.

## Was es nicht zeigt

Der Text eines Szenarios ist unabhängig vom Code, wenn ihn jemand anderes als die Entwicklerinnen
und Entwickler schreibt, und Regel R5 prüft das. Die Schrittdefinitionen, die ein Szenario ausführbar
machen, sind Code, meist von Entwicklerinnen und Entwicklern geschrieben; was ein Schritt wirklich
prüft, steht dort, und OIS beschreibt es nicht. Reviewe Schrittdefinitionen wie jeden anderen
Testcode.
