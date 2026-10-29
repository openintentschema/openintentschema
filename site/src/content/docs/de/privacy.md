---
title: Datenschutz und Datenflüsse
description: Was die OIS-Werkzeuge lesen, schreiben und übertragen, und wohin OIS-Records gehen.
---

OIS ist ein Datenformat, und seine Werkzeuge laufen dort, wo du sie ausführst. Kein `ois`-Befehl
öffnet eine Netzwerkverbindung, ausser `ois trust update`, wenn du es ausführst, um eine
Sigstore-Vertrauenswurzel zu holen: OIS-Records bleiben in deiner Organisation, bis du sie
irgendwohin sendest.

[![Datenflüsse: Die Werkzeuge laufen in deiner Organisation; das Installieren, das Pullen des Images, das schlüssellose Signieren und das Holen einer Vertrauenswurzel kontaktieren externe Dienste, und Records erreichen andere nur, wenn du sie sendest](/images/data-flows.svg)](/images/data-flows.svg)

## Wer was erhält

| Schritt | Was übertragen wird | An | Wie du es einschränkst |
| --- | --- | --- | --- |
| `ois-tools` mit `uvx` oder `pip` installieren | Die Download-Anfrage: IP-Adresse und, wie pip und uv es für die Download-Statistik von PyPI dokumentieren, Installer, Python- und Betriebssystemversion sowie ob es in CI läuft | PyPI, betrieben von der Python Software Foundation | Aus einem internen Paket-Mirror installieren, oder ein gepinntes Wheel aus deinem eigenen Artefakt-Speicher |
| `uv` mit der GitHub Action `setup-uv` installieren | Die Download-Anfrage | GitHub | Ein Runner-Image mit vorinstalliertem `uv` |
| Die Setup-Action `openintentschema/tools/.github/actions/setup` ausführen | Die Download-Anfragen für `uv` und für `ois-tools` | GitHub und PyPI | Stattdessen aus einem internen Mirror installieren |
| SARIF mit `github/codeql-action/upload-sarif` hochladen | Die Meldungen von `ois validate`: Regel, Nachricht, Datei und Zeile | GitHub Code Scanning deines Repositorys | Den Upload weglassen; die SARIF-Datei bleibt lokal |
| Das GitLab-CI-Template einbinden | Die Anfrage nach der Template-Datei, dann der Image-Pull | GitHub (`raw.githubusercontent.com`, `ghcr.io`) | Template und Image in deine eigene GitLab-Instanz und Registry kopieren |
| `uvx` ausführen, wo kein passendes Python installiert ist | Die Download-Anfrage für einen Python-Build | GitHub, das die Python-Builds von uv hostet | Python 3.13 oder neuer selbst installieren, oder `UV_PYTHON_INSTALL_MIRROR` auf einen internen Mirror setzen |
| Das Container-Image `ghcr.io/openintentschema/ois-tools` pullen | Die Download-Anfrage: IP-Adresse und das angeforderte Image | GitHub Container Registry | Das Image in deine eigene Registry spiegeln, per Digest gepinnt |
| `ois junit` ausführen | Nichts. Es liest die Testberichte und den lokalen Git-Checkout (`git rev-parse`, `ls-files`, `show`, `remote get-url`; nie `fetch` oder `push`) und schreibt eine Datei | Niemand | |
| `ois validate` ausführen | Nichts. Das JSON Schema wird im Paket mitgeliefert und nie abgerufen | Niemand | |
| `ois intent` ausführen | Nichts. Es liest und schreibt Intent- und Entscheidungsdateien lokal | Niemand | |
| `ois cucumber` ausführen | Nichts. Es liest die Cucumber-Messages-Datei und die Feature-Dateien im lokalen Git-Checkout und schreibt Records; Fehlermeldungen und Stacktraces werden nicht übernommen | Niemand | |
| `ois record` ausführen | Nichts. Es liest die Dateien, die es festhält, und den lokalen Git-Checkout (`git rev-parse`, `ls-files`, `diff`, `remote get-url`; nie `fetch` oder `push`) und schreibt Record-Dateien | Niemand | |
| `ois passport` ausführen | Nichts. Es liest Records und schreibt die Passport-Datei lokal | Niemand | |
| `ois coverage` ausführen | Nichts. Es liest Records oder einen Passport und gibt das Ergebnis aus | Niemand | |
| `ois key` und `ois sign` ausführen | Nichts. Schlüssel werden lokal erzeugt und verwendet; der private Schlüssel verlässt nie die Datei, in der du ihn aufbewahrst | Niemand | Private Schlüssel in einem Secret Store aufbewahren |
| Schlüssellos signieren mit `actions/attest` oder cosign | Das Identitäts-Token des Workflows und die Signatur | Sigstore (Fulcio und das öffentliche Transparenz-Log Rekor) oder deine eigene Instanz; auf GitHub zusätzlich die Attestations des Repositorys | Das Log ist absichtlich öffentlich: Es hält die Identität, den Zeitpunkt und den Digest fest, nicht den Passport |
| Eine Vertrauenswurzel mit `ois trust update` holen | Die Anfrage nach den signierten TUF-Metadaten und der Vertrauenswurzel von Sigstore | Das TUF-Repository von Sigstore (`tuf-repo-cdn.sigstore.dev`) oder das deiner eigenen Instanz | Eine geprüfte Kopie aufbewahren und sie nach deinem eigenen Zeitplan aktualisieren |
| Eine Vertrauenswurzel mit `gh attestation trusted-root` holen | Die Anfrage | GitHub | Eine geprüfte Kopie aufbewahren und sie nach deinem eigenen Zeitplan aktualisieren |
| Ein Sigstore-Bundle mit `ois validate`, `ois coverage` oder `ois passport build` verifizieren | Nichts. Die Vertrauenswurzel ist eine lokale Datei | Niemand | |
| Ein signiertes Bundle oder einen signierten Passport teilen | Seine Records, die Signaturen und die Schlüssel-IDs | Die Empfänger, die du wählst | Empfänger verifizieren mit den öffentlichen Schlüsseln, die du ihnen gibst, oder bei schlüssellosen Signaturen mit einer Sigstore-Vertrauenswurzel |
| Bundles speichern | Die Bundle-Datei | Dort, wo deine Pipeline Artefakte aufbewahrt | Deine Aufbewahrungsregeln gelten |
| Ein Bundle oder einen Passport teilen | Seine Records (siehe unten) | Die Empfänger, die du wählst, etwa ein Auditor oder ein Kunde | Vor dem Teilen prüfen (Spezifikation Abschnitt 12) |
| Diese Website besuchen | Die Anfrage: IP-Adresse, Seite, Browser | GitHub Pages, das die Website hostet | Die Website lädt nichts von anderen Domains und setzt keine Cookies; deine Theme-Wahl bleibt in deinem Browser |
| Ein Issue oder einen Pull Request eröffnen | Was du schreibst | GitHub, öffentlich | Sicherheitsprobleme vertraulich melden |
| An editors@openintentschema.io schreiben | Deine E-Mail | Proton Mail, der Mail-Anbieter des Projekts | |

## Was ein Bundle aus `ois junit` enthält

| Enthalten | Nicht enthalten |
| --- | --- |
| Testnamen, als Aussagen von Kriterien | Testausgaben, Fehlermeldungen und Stacktraces |
| Pfade der Testdateien und der `sha256` ihres Inhalts | Der Inhalt der Testdateien oder jeglicher Quellcode |
| Repository-URL ohne Zugangsdaten, Commit-Hash | Benutzernamen, E-Mail-Adressen, CI-Variablen oder Secrets |
| Suite-Name, der von dir gewählte Namespace, die URL des Pipeline-Laufs | Hostnamen von Build-Maschinen |
| Ergebnis pro Test und der Zeitpunkt, zu dem es beobachtet wurde | Timing- oder Performance-Daten |

Testnamen und Repository-URLs können trotzdem interne Informationen preisgeben. Prüfe sie, bevor
ein Bundle deine Organisation verlässt; Testnamen dürfen keine Personendaten enthalten
(Spezifikation Abschnitt 12.1).

## Wie das geprüft wurde

Jeder `ois`-Befehl ausser `ois trust update`, dessen Aufgabe das Holen einer Vertrauenswurzel ist,
sowie die gesamte Testsuite der Werkzeuge liefen in einer Sandbox, die jeden Netzwerkzugriff blockiert. Alle funktionieren unverändert;
eine Netzwerkanfrage in dieser Sandbox schlägt fehl. Das Container-Image führt sie im CI der
Werkzeuge mit `docker run --network none` aus. Was pip
und uv an PyPI senden, stammt aus ihrer Dokumentation und wurde hier nicht gemessen.

## In der Spezifikation

Abschnitt 12 der Spezifikation legt die Datenschutzregeln für Records fest: keine Personendaten
ausser Namen und Kennungen von Actors, Pseudonyme für menschliche Actors, Testdaten per Ort und
Digest referenziert statt eingebettet, und Datensätze mit Personendaten als `production` oder
`anonymized` klassifiziert.
