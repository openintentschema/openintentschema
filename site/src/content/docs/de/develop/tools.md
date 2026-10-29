---
title: Referenz-Werkzeuge
description: Ein Befehl, ois, um OIS-Evidence entlang des Lieferzyklus festzuhalten und Records, Bundles und Quality Passports zu prüfen.
---

Die Referenz-Werkzeuge halten OIS-Evidence dort fest, wo sie entsteht, und prüfen sie gegen die
Spezifikation. Sie sind ein einziger Befehl, `ois`, Open Source unter Apache-2.0, auf PyPI als
[`ois-tools`](https://pypi.org/project/ois-tools/) und als Container-Image veröffentlicht; der
Quellcode liegt in [openintentschema/tools](https://github.com/openintentschema/tools).

## Entlang des Lieferzyklus

| Phase | Was festgehalten wird | Befehl | Anleitung |
| --- | --- | --- | --- |
| Anforderung | Intent mit Akzeptanzkriterien, seine Freigabe | `ois intent`, `ois intent from-gherkin` | [Intents schreiben und freigeben](/de/approve-intents/), [Gherkin](/de/gherkin-cucumber/) |
| Design | Design-Freigabe | `ois record decision --gate design-approval` | [Artefakte, Entscheidungen und Findings erfassen](/de/record/) |
| Implementierung | Code-Artefakt, der Kontext, den ein Agent bekommen hat | `ois record artifact` | [Artefakte, Entscheidungen und Findings festhalten](/de/record/) |
| Test | Evidence pro Kriterium, Messwerte für nicht funktionale | `ois junit --intent`, `ois cucumber`, `ois measure`, `ois record evidence` | [Tests verknüpfen](/de/link-tests/), [Messen](/de/measure/), [Cucumber](/de/gherkin-cucumber/), [Erste Schritte](/de/getting-started/) |
| Merge | Merge-Entscheidung | `ois record decision --gate merge` | [Artefakte, Entscheidungen und Findings festhalten](/de/record/) |
| Release | Build, Release-Entscheidung, signierter Passport mit Intent-Abdeckung | `ois record`, `ois passport build --sign` | [Einen Quality Passport erstellen](/de/build-a-passport/), [Signieren](/de/sign/) |
| Betrieb | Findings, ihre Klassifizierung und Auflösung | `ois record finding`, `ois record supersede` | [Artefakte, Entscheidungen und Findings festhalten](/de/record/) |
| Prüfung durch andere | einen Passport prüfen und seine Abdeckung neu berechnen | `ois validate`, `ois coverage` | [Einen Quality Passport erstellen](/de/build-a-passport/#prüfen) |

`ois key`, `ois sign` und `ois trust` signieren und verifizieren unterwegs: DSSE mit deinen
eigenen Schlüsseln, oder schlüssellos über Sigstore, zum Beispiel mit GitHub Actions; siehe
[Bundles und Passports signieren](/de/sign/).

Die Werkzeuge halten fest und prüfen; sie setzen nichts durch. Ob ein Merge oder ein Release
blockiert wird, etwa unter einer Abdeckungsschwelle oder bei einem offenen kritischen Finding, ist
die Policy deiner Pipeline, die die Exit-Codes und Kennzahlen der Befehle auswertet.

## Installieren und ausführen

```bash
uvx --from ois-tools ois validate bundle.json    # run without installing
pip install ois-tools                            # or install; Python 3.13 or later
ois --help                                       # the commands
```

Die Befehle funktionieren für Projekte in jeder Sprache: Sie lesen JSON, YAML, Testberichte und den
Git-Checkout, nicht den Code. Ohne Python nimmst du das Container-Image, das `ois` ausführt und
git enthält (linux/amd64 und linux/arm64):

```bash
docker run --rm --network none -v "$PWD:/work" --user "$(id -u):$(id -g)" \
  ghcr.io/openintentschema/ois-tools validate bundle.json
```

Zum Validieren mit Node.js bringt das npm-Paket `ois-tools` dasselbe `ois validate` mit; die
übrigen Befehle gibt es im Python-Paket ([Mit Node.js](#mit-nodejs)):

```bash
npx ois-tools validate bundle.json               # run without installing
npm install -g ois-tools                         # or install; Node.js 24 or later
```

In CI installiert `uses: openintentschema/tools/.github/actions/setup@v0.12.0` `ois` auf GitHub Actions, und
`.gitlab/ci/ois.gitlab-ci.yml` im Tools-Repository ist ein Template für GitLab CI; siehe
[Erste Schritte](/de/getting-started/#6-in-die-pipeline-einbauen).

Die Argumente nach dem Image-Namen gehen an `ois`. In einem CI-Job, der das Image als sein Image
verwendet, überschreibst du den Entrypoint (GitLab: `entrypoint: [""]`) und rufst `ois` im Script
auf. Jedes Image trägt eine signierte Build-Provenance und eine SBOM; prüf sie mit
`gh attestation verify oci://ghcr.io/openintentschema/ois-tools:<version> --owner openintentschema`.

Bis Version 0.5.0 hiess das Paket `ois-validator`, mit einem Befehl pro Werkzeug
(`ois-validator`, `ois-junit`, …).

## Validieren

```bash
ois validate bundle.json passport.json
ois validate --format json finding.json
ois validate --format sarif passport.json > ois.sarif   # for GitHub code scanning and IDEs
```

Jede Datei enthält ein JSON-Dokument: einen einzelnen Record, ein Bundle oder einen Passport als
in-toto Statement v1. Exit-Code 0 heisst, dass jede Datei konform ist, 1 heisst mindestens eine
violation, 2 heisst, dass eine Datei nicht gelesen werden konnte. Meldungen zeigen auf das
betroffene Feld:

```
same-producer.json: violation [R5] $.records[12].derivedFrom: test and subject are both produced by https://ois.acme.example/actors/dev-agent
```

| Level | Bedeutung | Regeln |
| --- | --- | --- |
| violation | Ein MUST ist verletzt; die Eingabe ist nicht konform. | das Schema, die Signatur, R1–R5, R10, R11, R14–R17 |
| warning | Eine Regel verlangt eine Meldung; die Eingabe ist trotzdem konform. | die Signatur (Schlüssel oder Vertrauenswurzel nicht vertrauenswürdig), R8, R12, R13 |
| info | Ein SHOULD wird nicht befolgt. | R1, R9, R15 |

Profile fügen Regeln für eine Branche hinzu: `ois validate` prüft [regulated/v0.1](/de/profiles/regulated/v0.1/)
(Regeln `regulated/P1` bis `regulated/P4`), wenn ein Record es aufführt, oder mit
`--profile regulated/v0.1`.

R16, R17 und die Regel-IDs `schema` und `signature` sind in RFCs vorgeschlagen. Ein signiertes
Dokument wird mit den öffentlichen Schlüsseln verifiziert, die als `--trusted-key` übergeben
werden, ein Sigstore-Bundle gegen die Vertrauenswurzeln, die als `--trusted-root` übergeben
werden; ein festgehaltener Kontext gilt als bestätigt, wenn der Actor, der ihn festgehalten hat,
signiert hat (R12). Siehe [Bundles und Passports signieren](/de/sign/).


### Mit Node.js

Eine zweite Implementierung des Validators, für Node.js 24 oder neuer, ist auf npm als
[`ois-tools`](https://www.npmjs.com/package/ois-tools) veröffentlicht; der Quellcode liegt in
[openintentschema/tools-js](https://github.com/openintentschema/tools-js). Sie prüft dasselbe:
Appendix B, R1 bis R17, das Profil `regulated/v0.1`, DSSE- und keyless Sigstore-Signaturen, mit
denselben Optionen, Meldungen und Exit-Codes:

```bash
npx ois-tools validate passport.json --trusted-root trusted_root.json
npm install -g ois-tools    # danach: ois validate passport.json
```

Beide Implementierungen bestehen jede Conformance-Fixture der Spezifikation. In JavaScript ist
sie auch eine Bibliothek: `import { validate } from 'ois-tools'`.

## Deine eigene Implementierung testen

Ein Validator ist konform, wenn er für jede Fixture genau das meldet, was die
[Konformitäts-Testsuite](/de/conformance/) erwartet. `ois validate` führt in seinen Tests die
gesamte Suite aus; jede andere Implementierung kann dieselben Fixtures und dasselbe Manifest
verwenden.
