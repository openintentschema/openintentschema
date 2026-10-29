---
title: Intents schreiben und freigeben
description: Schreib eine Anforderung mit Akzeptanzkriterien als OIS-Intent, gib es frei und versioniere es.
---

Der erste Schritt zu Level 2, "Intent-aware": Anforderungen werden zu Intents mit
Akzeptanzkriterien, von einer Person freigegeben und an ihren exakten Wortlaut gebunden. Tests, die
daraus abgeleitet werden, können dann auf ein Kriterium verweisen, und die Evidence sagt
`derivedFrom: intent`.

`ois intent`, Teil des Pakets [`ois-tools`](/de/develop/tools/), berechnet die Digests und schreibt
die Freigabe, was von Hand fehleranfällig ist.
Die Befehle setzen voraus, dass `ois` installiert und `OIS_NAMESPACE` gesetzt ist
([Erste Schritte](/de/getting-started/#nächste-schritte)).

## 1. Das Intent schreiben

Intents lassen sich in YAML schreiben (Spezifikation Abschnitt 7); Feature-Dateien in Gherkin werden
mit `ois intent from-gherkin` zu einem Intent ([Gherkin und Cucumber verwenden](/de/gherkin-cucumber/)).
Lege eine Datei pro Intent-Version an, zum Beispiel unter `.ois/intents/`:

```yaml
# .ois/intents/INT-7-v1.ois.yaml
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

- **`id`** ist eine URI unter deinem Namespace; dieselbe ID umfasst jede Version des Intents.
- **`risk`** (`low`, `medium`, `high` oder `critical`) sagt, wie viel auf dem Spiel steht; das
  Profil `regulated/v0.1` verlangt es.
- **`key`** benennt ein Kriterium dauerhaft: Der Schlüssel bleibt über alle Versionen gleich. Ein
  optionales **`criticality`** (`low`, `medium` oder `high`) gewichtet das Kriterium in der
  gewichteten Abdeckung.
- **`notation`** ist `gherkin`, `ears` oder `text`; **`kind`** ist `functional` oder
  `non-functional`. Ein nicht funktionales Kriterium kann ein messbares `target` tragen, zum
  Beispiel `{metric: responseTimeP95, operator: lte, value: 500, unit: ms}`;
  [`ois measure`](/de/measure/) zeichnet einen Lasttest dagegen auf.

YAML wird so gelesen, dass es sich verlustfrei in JSON umwandeln lässt: Datumsangaben bleiben Text,
und Tags, Merge-Keys und doppelte Schlüssel werden abgelehnt.

## 2. Das Intent freigeben

```bash
PO=$(ois record actor --kind human --name po-7f3a)   # the approver; prints its reference
ois intent approve .ois/intents/INT-7-v1.ois.yaml --by "$PO"
```

Das schreibt zwei Records:

- `.ois/intents/INT-7-v1.ois.json`: das Intent mit Status `approved`, einem Digest pro Kriterium
  und einem Digest des ganzen Intents (Abschnitt 6.4);
- `.ois/decisions/INT-7-v1-approval.ois.json`: die Entscheidung vom Typ intent-approval, deren
  `subjectDigest` dem Digest des Intents entspricht (Regel R1).

`--by` nennt den freigebenden Actor; Regel R1 erwartet einen Menschen. [`ois record`](/de/record/)
schreibt die übrigen Actors und Artefakte auf dieselbe Weise. Mit `--policy` und `--policy-version` hältst du die Richtlinie fest, der die
Freigabe gefolgt ist, zum Beispiel deine Definition of Ready.

Ein freigegebenes Intent ändert sich nie. Passt sein Inhalt nicht mehr zu seinem Digest, lehnt
`ois intent approve` es ab.

## 3. Das Intent ändern: eine neue Version

```bash
ois intent next .ois/intents/INT-7-v1.ois.json
```

schreibt `.ois/intents/INT-7-v2.ois.yaml`: Version 2, ein Entwurf, der Version 1 ersetzt
(`supersedes`). Bearbeite ihn und sieh dann nach, welche Evidence gültig bleibt:

```bash
ois intent compare .ois/intents/INT-7-v1.ois.json .ois/intents/INT-7-v2.ois.yaml
```

```
AC-1: unchanged, evidence carries over
AC-2: changed, evidence is stale
```

Evidence für Version 1 zählt für Version 2 nur dort, wo das Kriterium unverändert ist (Abschnitt
6.3). Eine Änderung von `criticality` macht Evidence nicht veraltet. Gib Version 2 genauso frei wie
Version 1.

## 4. Tests aus den Kriterien ableiten

Sobald freigegebene Intents vorliegen, lassen sich Tests gegen ein Kriterium schreiben, von einer
Person oder von einem Agenten, der den Code nie sieht. Ihre Evidence verweist auf das Kriterium,
zum Beispiel `https://ois.acme.example/intents/INT-7@1#AC-2`, und gibt `derivedFrom: intent` an.
Der Validator prüft dann, dass der Test das Kriterium und keinen Code gesehen hat (R4) und dass sein
Producer ein anderer ist als der des Codes (R5); siehe [Kernkonzepte](/de/learn/core-concepts/).
[Tests mit Kriterien verknüpfen](/de/link-tests/) zeigt, wie ein Test sein Kriterium nennt und wie
`ois junit --intent` den Lauf aufzeichnet; [`ois record`](/de/record/) schreibt einzelne Records.

Wenn das Release bereit ist, [erstelle daraus einen Quality Passport](/de/build-a-passport/).
