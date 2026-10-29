---
title: Einen Quality Passport erstellen
description: Sammle die Records hinter einem Release in einem Quality Passport und prüfe ihn.
---

Ein Quality Passport sammelt die Intents, Evidence, Entscheidungen und Findings hinter einem Release,
damit ein Auditor, ein Kunde oder eine Aufsichtsbehörde es ohne Zugriff auf deine Werkzeuge prüfen
kann ([Spezifikation Abschnitt 8](/de/specification/quality-passport/)). `ois passport`, Teil des
Pakets [`ois-tools`](/de/develop/tools/), stellt einen aus den Records zusammen, die du bereits hast.
Die Befehle setzen voraus, dass `ois` installiert und `OIS_NAMESPACE` gesetzt ist
([Erste Schritte](/de/getting-started/#nächste-schritte)).

## Was hineingehört

- **Die freigegebenen Intents** mit ihren Freigabe-Entscheidungen, zum Beispiel mit
  [`ois intent`](/de/approve-intents/) geschrieben.
- **Evidence** und die Test- und Code-Artefakte, auf die sie verweist, zum Beispiel aus
  [`ois junit`](/de/getting-started/) oder aus Tests, die aus den Intents abgeleitet wurden.
- **Das Build-Artefakt** des Release mit seinem Digest und **die Actors**, die jeder Record nennt:
  wer freigegeben hat, wer gebaut hat, wer über das Release entscheidet und wer den Passport ausstellt.
  [`ois record`](/de/record/) schreibt sie; erfasse den Build direkt nach dem Bauen, bevor die Tests
  laufen ([Tests mit Kriterien verknüpfen](/de/link-tests/#2-den-build-vor-dem-testlauf-erfassen)):

  ```bash
  CI=$(ois record actor --kind tool --name "CI build" --version 7)
  BUILD=$(ois record artifact dist/billing-2026.10.4-py3-none-any.whl --kind build \
    --location pkg:pypi/billing@2026.10.4 --produced-by "$CI")
  RM=$(ois record actor --kind human --name release-manager-1d2e)
  ISSUER=$(ois record actor --kind tool --name "Passport issuer" --version 1)
  ```

- **Offene Findings** zu den aufgeführten Intents, damit der Passport keine bekannten Fehler verbirgt,
  und die Entscheidungen, die frühere aufgelöst haben (`ois record finding`, `supersede` und `decision`).

Ein Passport muss in sich geschlossen sein: Jede Referenz darin wird zu einem Record in ihm aufgelöst (Regel R10).

## Erstellen

```bash
ois passport build .ois/ --release-name billing --release-version 2026.10.4 \
  --build "$BUILD" --issuer "$ISSUER" --approve-release-by "$RM" --output passport.json
```

- **Eingaben** sind Record- oder Bundle-Dateien oder ganze Verzeichnisse wie `.ois/`, in JSON oder
  YAML; füge die Bundles oder `.ois/`-Ordner hinzu, die deine Testjobs als Artefakte weitergegeben
  haben. Derselbe Record in mehreren Eingaben wird einmal übernommen. Zwei verschiedene Records mit
  derselben ID werden abgelehnt.
- **Intents:** Jedes Intent wird in seiner neuesten freigegebenen Version aufgeführt, wie Regel R15
  empfiehlt. Mit `--intent` wählst du sie selbst aus, mit `--scope` grenzt du die Kriterien ein.
- **Release-Entscheidung:** `--approve-release-by` erfasst, wer das Release freigegeben hat, gebunden an
  den Digest des Builds (Regel R16). Lass die Option weg, wenn dein Release-Gate die Entscheidung
  bereits erfasst hat, zum Beispiel mit `ois record decision --gate release`.
- **Subjekt:** Das Subjekt des Statements ist das Build-Artefakt mit seinem Digest. Damit vergleicht
  ein Konsument das Artefakt, das er erhalten hat.
- **Abdeckung:** Der Passport meldet in `assessments` die Intent-Abdeckung nach der
  [Referenzmethode](/de/methods/basic-intent-coverage/v0.1/). Lass sie mit `--no-coverage` weg, wenn
  du deine eigene Methode meldest.

`ois passport` validiert den Passport, bevor es ihn schreibt. Würde er eine Regel verletzen, nennt es
die Regel und schreibt nichts. Warnungen, etwa zu selbst deklarierten Kontexten (R12) oder offenen
Findings mit hohem Schweregrad (R13), werden angezeigt, und der Passport wird geschrieben.

## Prüfen

Jeder kann einen Passport mit dem Validator prüfen und die Abdeckung nachrechnen, die er deklariert:

```bash
ois validate passport.json
ois coverage passport.json
```

Für das ausgearbeitete Beispiel der Spezifikation:

```
https://ois.acme.example/intents/INT-142@1#AC-1  not covered
    no evidence
https://ois.acme.example/intents/INT-142@1#AC-2  covered  https://ois.acme.example/evidence/EV-9021
intentCoverage 0.5 (declared 0.5)
intentCoverageAttested 0.0
intentCoverageWeighted 0.5
intentCoverageDiverse 0.5
```

`ois coverage` zeigt pro Kriterium, welche Evidence zählt und warum der Rest nicht zählt. Es endet mit
Exit-Code 1, wenn ein deklarierter Wert vom berechneten abweicht. Bevor der Passport existiert, zeigt
`ois coverage .ois/ --build "$BUILD"`, was noch fehlt.

`--format markdown` schreibt dasselbe als Tabellen, für die Zusammenfassung eines CI-Jobs oder
einen Kommentar im Pull Request. Auf GitHub:

```yaml
- run: ois coverage .ois/ --build "$BUILD" --format markdown >> "$GITHUB_STEP_SUMMARY"
```

`intentCoverageAttested` zählt nur Evidence, deren Testkontext von einem anderen Actor erfasst wurde,
der den Passport signiert hat (Regel R12). In einem unsignierten Passport ist der Wert 0.

## Signieren

Konformität nach Level 3 verlangt einen signierten Passport, und ein Empfänger kann ihn dann seinem
Aussteller zuordnen. Ergänze `ois passport build` um `--sign issuer.key` (und den Schlüssel der
Laufzeitumgebung, die die Kontexte erfasst hat), und prüfe das Ergebnis mit
`ois validate passport.dsse.json --trusted-key keys/`. In einer Pipeline lässt sich der Passport auch
keyless (ohne Schlüssel) signieren, zum Beispiel mit `actions/attest` auf GitHub. Siehe
[Bundles und Passports signieren](/de/sign/).
