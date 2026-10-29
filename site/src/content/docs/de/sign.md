---
title: Bundles und Passports signieren
description: Signiere OIS-Bundles und Quality Passports mit deinen eigenen Schlüsseln oder keyless mit Sigstore, damit Empfänger sie zuordnen können und erfasste Kontexte als bestätigt gelten.
---

Eine Signatur macht ein Bundle oder einen Quality Passport zuordenbar: Ein Empfänger kann prüfen, wer
es ausgestellt hat und dass sich seither nichts geändert hat. Erst sie macht einen erfassten `context`
von selbst deklariert zu bestätigt (Regel R12), und Konformität nach Level 3 verlangt sie
(Spezifikation Abschnitte 8.3 und 11.2). `ois key`, `ois sign` und `ois passport build --sign`, Teil
des Pakets [`ois-tools`](/de/develop/tools/), signieren mit DSSE und deinen eigenen Schlüsseln; in
einer Pipeline braucht [keyless Signieren](#keyless-mit-sigstore) über Sigstore überhaupt keinen Schlüssel, und
`ois trust` holt, was Prüfer dafür brauchen.
Die Befehle setzen voraus, dass `ois` installiert und `OIS_NAMESPACE` gesetzt ist
([Erste Schritte](/de/getting-started/#nächste-schritte)).

## 1. Schlüssel erzeugen

Ein Schlüsselpaar pro Actor, der signiert, zum Beispiel für den Aussteller des Passports, für die
Laufzeitumgebung, die deine Agenten ausführt und erfasst, was sie erhalten haben, und für die CI:

```bash
ois key generate issuer             # writes issuer.key (secret) and issuer.pub, prints the key id
ois key generate agent-runtime
ois key generate ci
```

Die Schlüssel sind Ed25519; ECDSA-P-256-Schlüssel aus anderen Quellen funktionieren auch. Der private
Schlüssel wird so geschrieben, dass nur du ihn lesen kannst. Bewahre ihn in einem Secret-Speicher auf,
zum Beispiel als CI-Secret, und committe ihn nie. Ein verschlüsselter Schlüssel wird mit der
Passphrase in `OIS_KEY_PASSPHRASE` geöffnet.

## 2. Jeden Schlüssel an seinen Actor binden

Eine Signatur zählt für den Actor, dessen `identity.keyId` die Key-ID des Schlüssels ist:

```bash
RUNTIME=$(ois record actor --kind tool --name "Agent runtime" --version 4.3 \
  --public-key agent-runtime.pub)
ISSUER=$(ois record actor --kind tool --name "Passport issuer" --version 2 --public-key issuer.pub)
```

Ein Schlüssel ändert den Record eines Actors. Ein Actor, der früher ohne Schlüssel erfasst wurde,
etwa der Aussteller in [Einen Quality Passport erstellen](/de/build-a-passport/), bekommt deshalb eine
neue Version.

Die Key-ID ist der SHA-256 des öffentlichen Schlüssels, sodass jeder, der den öffentlichen Schlüssel
hat, sie ableiten kann (`ois key id agent-runtime.pub`).

## 3. Signieren

Einen Passport in einem Schritt erstellen und signieren:

```bash
ois passport build .ois/ --release-name billing --release-version 2026.10.4 \
  --build "$BUILD" --issuer "$ISSUER" --approve-release-by "$RM" \
  --sign issuer.key --sign agent-runtime.key --output passport.dsse.json
```

Die bestätigte Abdeckung des Passports ist Teil dessen, was signiert wird. Deshalb berücksichtigt
`ois passport build` bei ihrer Berechnung die mit `--sign` angegebenen Schlüssel.

Ein Bundle oder ein Envelope, der eine weitere Signatur tragen soll, signierst du mit `ois sign`:

```bash
ois sign ois-bundle.json --key agent-runtime.key --output ois-bundle.dsse.json
ois sign ois-bundle.dsse.json --key ci.key --output ois-bundle.dsse.json
```

Das Ergebnis ist ein DSSE-Envelope: Payload-Typ `application/vnd.in-toto+json` für einen Passport,
`application/vnd.ois+json` für ein Bundle und eine Signatur pro Schlüssel. `ois sign` lehnt ein
Dokument ab, das eine Regel verletzt, damit nichts Fehlerhaftes eine Signatur erhält.

## 4. Verifizieren

Der Empfänger entscheidet, welchen Schlüsseln er vertraut, bewahrt deren öffentliche Schlüssel auf,
zum Beispiel in einem Verzeichnis `keys/`, und übergibt sie:

```bash
ois validate passport.dsse.json --trusted-key keys/       # a .pub file, a directory, or KEYID=FILE
ois coverage passport.dsse.json --trusted-key keys/
```

| Fall | Meldung |
| --- | --- |
| eine Signatur lässt sich mit einem vertrauenswürdigen Schlüssel verifizieren | keine; Kontexte, die der Actor dieses Schlüssels erfasst hat, gelten als bestätigt |
| die Payload wurde nach dem Signieren geändert | Verletzung `[signature]`; der Envelope gilt als unsigniert |
| der Envelope hat keine Signatur oder den falschen Payload-Typ | Verletzung `[signature]` |
| der Schlüssel gehört nicht zu den vertrauenswürdigen | Warnung `[signature]`: sie kann nicht geprüft werden |

Ein Dokument kann einen Prüfer nie dazu bringen, einem Schlüssel zu vertrauen: Schlüssel kommen nur
vom Prüfer. Tausche öffentliche Schlüssel so aus wie andere Vertrauensanker, zum Beispiel in deiner
Partnervereinbarung oder in einem Repository, das du kontrollierst.

## Wer was signiert

| Signierer | Signiert | Warum |
| --- | --- | --- |
| Aussteller des Passports | den Passport | ordnet die Release-Evidence der ausstellenden Organisation zu |
| Agent-Laufzeitumgebung | Bundles oder Passports mit Kontexten, die sie erfasst hat | macht diese Kontexte zu bestätigten (R12) |
| CI | Bundles mit Testergebnissen | bindet die Evidence an die Pipeline, die die Tests ausgeführt hat |

## Keyless, mit Sigstore

In einer Pipeline muss überhaupt kein Schlüssel aufbewahrt werden. Das CI-System weist Sigstore die
Identität des Workflows nach, Sigstore zertifiziert sie für zehn Minuten, und die Signatur kommt mit
einer unabhängigen Zeitangabe in ein öffentliches Transparency-Log (Rekor). Ein Prüfer vertraut der
Vertrauenswurzel von Sigstore und prüft, dass die Identität im Zertifikat die des Actors ist.

**Auf GitHub** signiert `actions/attest` den Passport und speichert die Attestation beim Repository.
Der Aussteller ist der Workflow selbst; sein Actor nennt den Workflow als seine Identität und wird
erfasst, bevor der Passport erstellt wird:

```bash
ISSUER=$(ois record actor --kind tool --name "Release pipeline" --version "$VERSION" \
  --identity-issuer https://token.actions.githubusercontent.com \
  --identity-subject "https://github.com/acme/billing/.github/workflows/release.yml@refs/tags/v$VERSION")
```


```yaml
permissions:
  contents: read
  id-token: write        # the workflow's identity for Sigstore
  attestations: write    # store the attestation with the repository
steps:
  - uses: openintentschema/tools/.github/actions/setup@v0.13.0
  - id: passport
    run: |
      ois passport build .ois/ --release-name billing --release-version "$VERSION" \
        --build "$BUILD" --issuer "$ISSUER" --approve-release-by "$RM" \
        --keyless-signer "https://token.actions.githubusercontent.com=$GITHUB_SERVER_URL/$GITHUB_WORKFLOW_REF" \
        --output passport.json
      jq .predicate passport.json > predicate.json
      echo "digest=$(jq -r '.subject[0].digest.sha256' passport.json)" >> "$GITHUB_OUTPUT"
  - id: attest
    uses: actions/attest@1e69f48acb82d1966a394da916b4c1698aa569d6 # v4.2.2
    with:
      subject-name: billing
      subject-digest: sha256:${{ steps.passport.outputs.digest }}
      predicate-type: https://ois.example/passport/v0.1   # the predicate type of this draft
      predicate-path: predicate.json
  - run: jq -c . "${{ steps.attest.outputs.bundle-path }}" | head -n 1 | jq . > passport.sigstore.json
```

`--keyless-signer` teilt `ois passport build` mit, wer signieren wird, sodass die bestätigte Abdeckung
im Passport diese Signatur bereits berücksichtigt; ein Actor, dessen Kontexte als bestätigt gelten sollen,
nennt dieselbe Workflow-Identität. Die Action schreibt das Sigstore-Bundle als JSON-Zeilen nach
`bundle-path`; der letzte Schritt behält es als ein Dokument. Prüfe es offline mit einer aktuellen
Vertrauenswurzel (Sigstore rotiert ab und zu seine Schlüssel, aktualisiere sie also):

```bash
pip install 'ois-tools[sigstore]'                     # the container image includes it
ois trust update --output trusted_root.json          # through TUF, the only command with network
ois validate passport.sigstore.json --trusted-root trusted_root.json
```

`gh attestation trusted-root > trusted_root.jsonl` liefert dasselbe, dazu die Wurzel von GitHubs
eigener Instanz, die für private Repositories signiert. Für die eigene Instanz einer Organisation:
`ois trust update --tuf-url https://tuf.acme.example --tuf-root root.json --output acme.json`.

**Andere Anbieter** funktionieren gleich: GitLab CI, Google Cloud, Buildkite oder die eigene
Sigstore-Instanz einer Organisation sind eine weitere Vertrauenswurzel und ein weiterer Aussteller im
Zertifikat. Ausserhalb von GitHub signiert
`cosign attest-blob --type https://ois.example/passport/v0.1 --predicate predicate.json`.
Keyless Signieren deckt Passports ab; Bundles werden mit Schlüsseln signiert.

## Personen

Die öffentliche Sigstore-Instanz schreibt die E-Mail-Adresse einer Person ins Zertifikat, was die
Spezifikation für menschliche Actors nicht erlaubt (Abschnitt 12). Zwei Wege halten Personen pseudonym:

- **In GitHub freigeben, die Pipeline signieren lassen.** Die Person gibt als erforderlicher
  Reviewer eines Environments oder in einem Pull-Request-Review frei, geschützt durch dein Single Sign-on;
  der Workflow erfasst dann die Entscheidung, mit `decidedBy` auf den pseudonymen Actor der Person
  gesetzt, und signiert. Die Signatur zeigt, dass die Pipeline nach der Freigabe lief; das
  Audit-Log von GitHub zeigt, wer freigegeben hat.
- **Ein eigener Schlüssel.** `ois key generate qe-2c9d` gibt einer Person einen Schlüssel mit einer
  pseudonymen Key-ID.

Auch eine eigene Sigstore-Instanz der Organisation, die pseudonyme Identitäten aus ihrem
Identity-Provider ausstellt, wäre eine Möglichkeit.
