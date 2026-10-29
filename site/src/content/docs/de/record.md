---
title: Artefakte, Entscheidungen und Findings erfassen
description: Schreibe die Actors, Artefakte, Evidence, Entscheidungen und Findings einer Lieferung mit ois record, Digests inklusive.
---

Zwischen einem freigegebenen Intent und einem Quality Passport liegen die Records der Lieferung selbst:
wer daran gearbeitet hat, was dabei entstanden ist, welche Tests bestanden haben, welche Gates
entschieden wurden und welche Fehler aufgetaucht sind. `ois record`, Teil des Pakets
[`ois-tools`](/de/develop/tools/), schreibt jeden davon mit einem Befehl. Es berechnet Digests, IDs
und Zeitstempel, prüft den Record und gibt die Referenz aus, mit der andere Records auf ihn verweisen.

## Einrichten

```bash
pip install ois-tools              # or: uv tool install ois-tools
export OIS_NAMESPACE=https://ois.acme.example
```

IDs werden unter dem Namespace abgeleitet, einer URI unter deiner Domain. Mit `--id` wählst du selbst
eine. Records landen in `.ois/<type>s/`, neben den Intents, die [`ois intent`](/de/approve-intents/) schreibt.

## Actors

Jeder Record nennt, wer ihn produziert, erfasst oder entschieden hat (Spezifikation Abschnitt 4.4):

```bash
PO=$(ois record actor --kind human --name po-7f3a)
DEV=$(ois record actor --kind agent --name "Dev Agent" --version 2.1 \
  --model acme-ai:coder:2026-09 --autonomy-level 1)
CI=$(ois record actor --kind tool --name "CI build" --version 7)
```

Jeder Befehl gibt die Referenz aus, zum Beispiel `https://ois.acme.example/actors/ci-build@7`, damit
der nächste Befehl sie verwenden kann. Agenten und Werkzeuge tragen eine Version, Agenten zusätzlich
ihr Modell. Ändern sich Modell, Anweisungen oder Werkzeuge eines Agenten, erfasse eine neue
`--version`. Für Personen verwendest du ein Pseudonym als Namen. Das Subjekt einer Identität darf
keine E-Mail-Adresse sein (Abschnitt 12). Ein Actor, der signiert, erhält seinen Schlüssel mit
`--public-key`, siehe [Bundles und Passports signieren](/de/sign/).

## Artefakte

```bash
CODE=$(ois record artifact src/invoice.py --kind code --produced-by "$DEV")
COMMIT=$(ois record artifact --commit . --kind code --produced-by "$DEV")
BUILD=$(ois record artifact dist/billing-2026.10.4-py3-none-any.whl --kind build \
  --location pkg:pypi/billing@2026.10.4 --produced-by "$CI" --input "$CODE")
IMAGE=$(ois record artifact --digest sha256:4f3c2b1a… --location pkg:oci/billing \
  --kind build --produced-by "$CI")
```

- **Eine Datei in Git** erhält ihren `sha256`, den Commit, den Repository-Ort
  `git+<origin>@<commit>` (ohne Zugangsdaten) und ihren Pfad. Sie muss committet und unverändert sein.
- **Eine Datei anderswo**, etwa ein gebautes Paket, braucht `--location`. Empfohlen ist eine Package URL.
- **Ein Commit** (`--commit`) oder ein bekannter Digest (`--digest`, zum Beispiel ein Image in einer
  Registry) braucht keine Datei. Ein Commit wird nach seinem Origin-Repository benannt, daher ist die
  ID in jedem Klon und im Container-Image dieselbe.

Ein Test, der aus einem Intent abgeleitet wurde, listet in `--context` auf, was sein Produzent erhalten hat:

```bash
TEST=$(ois record artifact tests/test_invoice.py --kind test --produced-by "$TEST_AGENT" \
  --context https://ois.acme.example/intents/INT-7@1#AC-1)
```

Der Kontext muss vollständig sein (Regel R6). Nenne mit `--context-recorded-by` die
Laufzeitumgebung, die ihn beobachtet hat. Bis diese Laufzeitumgebung das Bundle oder den Passport
signiert, meldet der Validator den Kontext als selbst deklariert (R12); siehe
[Bundles und Passports signieren](/de/sign/).

## Evidence

Ein Ergebnis eines Tests für ein Kriterium:

```bash
ois record evidence --criterion https://ois.acme.example/intents/INT-7@1#AC-1 \
  --test "$TEST" --subject "$CODE" --derived-from intent --result pass --recorded-by "$CI" \
  --measure responseTimeP95=420ms
```

`--derived-from` ist eine Behauptung. Der Validator prüft sie gegen den Kontext und die Produzenten
des Tests (R4, R5). Für einen Testlauf schreibt [`ois junit --intent`](/de/link-tests/) die Evidence in
einem Schritt.

## Entscheidungen

```bash
ois record decision --gate merge --subject "$CODE" --outcome passed --by "$CI"
ois record decision --gate release --subject "$BUILD" --outcome approved --by "$QE"
ois record decision --gate evidence-revocation --subject "$FLAKY" --by "$QE" \
  --rationale "flaky test, see BILL-31"
```

- Die Entscheidung bindet den **Digest ihres Subjekts**, entnommen aus dem Record des Subjekts in
  `.ois/` oder in `--records`. Ohne ihn lässt sich keine Release-Entscheidung schreiben (R16).
- Bei den **vordefinierten Gates** aus Spezifikation Abschnitt 4.6 werden Subjekt und Ergebnis
  geprüft. Eine Merge-Entscheidung nimmt Code, ein Release einen Build. Ein Evidence-Widerruf ist
  immer `rejected` und nennt seine Begründung (R11).
- Intent-Freigaben schreibt `ois intent approve`, das das Intent zugleich versiegelt.

## Findings

Ein Fehler oder Vorfall, aus der Produktion, einem Test, einem Review oder von einem Kunden:

```bash
ois record finding --summary "Rounding is off for credit notes" --severity high \
  --source production --reported-by "$SUPPORT" --intent https://ois.acme.example/intents/INT-7@1 \
  --ticket https://jira.acme.example/browse/BILL-12
```

Findings ändern sich nie. Um eines zu klassifizieren oder aufzulösen, erfasst du seinen Nachfolger:

```bash
ois record supersede .ois/findings/F-519bc77f0ab6.ois.json --cause implementation \
  --resolved-by "$FIX_EVIDENCE"
ois record decision --gate finding-resolution \
  --subject https://ois.acme.example/findings/F-519bc77f0ab6-r2 --outcome approved --by "$QE"
```

Die Auflösung zählt, sobald ein Actor sie bestätigt, der keinen Teil davon produziert, erfasst oder
entschieden hat (R14). `ois record` lehnt eine Bestätigung durch einen solchen Actor ab, ebenso einen
zweiten Nachfolger desselben Findings. Bis dahin trägt ein Passport, der das Intent auflistet, bei
einem offenen Finding mit `high` oder `critical` eine Warnung (R13).

## Records ändern sich nie

Führst du einen Befehl für dieselbe Sache erneut aus, gibt er dieselbe Referenz aus und behält die
Datei. Ein anderer Record unter einer bestehenden ID wird abgelehnt. Nichts wird überschrieben, wie es
die Spezifikation verlangt (Abschnitt 6.3). Exit-Code 0 bedeutet, dass der Record geschrieben wurde
oder schon vorhanden ist, und 1, dass er eine Regel verletzen würde und nichts geschrieben wurde.
Exit-Code 2 bedeutet, dass eine Datei nicht gelesen werden konnte oder ein Argument fehlerhaft ist.

## Weitergeben

`ois record bundle .ois/ --output ois-bundle.json` packt Records in ein in sich geschlossenes Bundle,
jeden Record einmal, und validiert es. Für ein Release [erstellst du einen Quality Passport](/de/build-a-passport/).
