---
title: Sign bundles and passports
description: Sign OIS bundles and Quality Passports with your own keys or keylessly with Sigstore, so that recipients can attribute them and recorded contexts count as attested.
---

A signature makes a bundle or a Quality Passport attributable: a recipient can check who issued
it and that nothing changed since. It is also what turns a recorded `context` from self-declared
into attested (rule R12), and what Level 3 conformance requires (specification sections 8.3 and
11.2). `ois key`, `ois sign` and `ois passport build --sign`, part of the
[`ois-tools`](/develop/tools/) package, sign with DSSE and your own keys; in a pipeline,
[keyless signing](#keyless-with-sigstore) through Sigstore needs no key at all, and `ois trust`
fetches what verifiers need for it.

## 1. Create keys

One key pair per actor that signs, for example the passport issuer and the runtime that runs your
agents and records what they were given:

```bash
ois key generate issuer             # writes issuer.key (secret) and issuer.pub, prints the key id
ois key generate agent-runtime
```

Keys are Ed25519; ECDSA P-256 keys from elsewhere work too. The private key is written readable by
you only. Keep it in a secret store, for example as a CI secret, and never commit it. An encrypted
key is opened with the passphrase in `OIS_KEY_PASSPHRASE`.

## 2. Tie each key to its actor

A signature counts for the actor whose `identity.keyId` is the key's id:

```bash
ois record actor --kind tool --name "Agent runtime" --version 4.3 --public-key agent-runtime.pub
ois record actor --kind tool --name "Passport issuer" --version 1 --public-key issuer.pub
```

The key id is the SHA-256 of the public key, so anyone holding the public key can derive it
(`ois key id agent-runtime.pub`).

## 3. Sign

Build and sign a passport in one step:

```bash
ois passport build .ois/ --release-name billing --release-version 2026.10.4 \
  --build "$BUILD" --issuer "$ISSUER" \
  --sign issuer.key --sign agent-runtime.key --output passport.dsse.json
```

The passport's attested coverage is part of what is signed, so `ois passport build` counts the
keys given with `--sign` when it computes it.

A bundle, or an envelope that should carry one more signature, is signed with `ois sign`:

```bash
ois sign ois-bundle.json --key agent-runtime.key --output ois-bundle.dsse.json
ois sign ois-bundle.dsse.json --key ci.key --output ois-bundle.dsse.json
```

The result is a DSSE envelope: payload type `application/vnd.in-toto+json` for a passport,
`application/vnd.ois+json` for a bundle, and one signature per key. `ois sign` refuses a document
that breaks a rule, so nothing broken gets a signature.

## 4. Verify

The recipient decides which keys to trust, and passes their public keys:

```bash
ois validate passport.dsse.json --trusted-key keys/       # a .pub file, a directory, or KEYID=FILE
ois coverage passport.dsse.json --trusted-key keys/
```

| Case | Report |
| --- | --- |
| a signature verifies under a trusted key | none; contexts recorded by that key's actor count as attested |
| the payload was changed after signing | violation `[signature]`; the envelope counts as unsigned |
| the envelope has no signature, or the wrong payload type | violation `[signature]` |
| the key is not among the trusted ones | warning `[signature]`: it cannot be checked |

A document can never make a verifier trust a key: keys come from the verifier only. Exchange
public keys the way you exchange other trust anchors, for example in your partner agreement or a
repository you control.

## Who signs what

| Signer | Signs | Why |
| --- | --- | --- |
| Passport issuer | the passport | attributes the release evidence to the issuing organization |
| Agent runtime | bundles or passports with contexts it recorded | makes those contexts attested (R12) |
| CI | bundles of test results | ties evidence to the pipeline that ran the tests |

## Keyless, with Sigstore

In a pipeline no key needs to be kept at all. The CI system proves the workflow's identity to
Sigstore, which certifies it for ten minutes, and the signature goes into a public transparency
log (Rekor) with an independent time. A verifier trusts Sigstore's trusted root and checks that
the identity in the certificate is the actor's.

**On GitHub,** `actions/attest` signs the passport and stores the attestation with the repository:

```yaml
permissions:
  contents: read
  id-token: write        # the workflow's identity for Sigstore
  attestations: write    # store the attestation with the repository
steps:
  - uses: openintentschema/tools/.github/actions/setup@v0.10.0
  - id: passport
    run: |
      ois passport build .ois/ --release-name billing --release-version "$VERSION" \
        --build "$BUILD" --issuer "$ISSUER" \
        --keyless-signer "https://token.actions.githubusercontent.com=$GITHUB_SERVER_URL/$GITHUB_WORKFLOW_REF" \
        --output passport.json
      jq .predicate passport.json > predicate.json
      echo "digest=$(jq -r '.subject[0].digest.sha256' passport.json)" >> "$GITHUB_OUTPUT"
  - id: attest
    uses: actions/attest@1e69f48acb82d1966a394da916b4c1698aa569d6 # v4.2.2
    with:
      subject-name: billing
      subject-digest: sha256:${{ steps.passport.outputs.digest }}
      predicate-type: https://ois.example/passport/v0.1
      predicate-path: predicate.json
```

`--keyless-signer` tells `ois passport build` who will sign, so the attested coverage inside the
passport already counts it. The signing actors name the workflow as their identity:

```bash
ois record actor --kind tool --name "Release pipeline" --version "$VERSION" \
  --identity-issuer https://token.actions.githubusercontent.com \
  --identity-subject "https://github.com/acme/billing/.github/workflows/release.yml@refs/tags/v$VERSION"
```

The action's output `bundle-path` is the Sigstore bundle. Verify it offline with a current trusted
root (Sigstore rotates keys now and then, so refresh it):

```bash
pip install 'ois-tools[sigstore]'                     # the container image includes it
ois trust update --output trusted_root.json          # through TUF, the only command with network
ois validate passport.sigstore.json --trusted-root trusted_root.json
```

`gh attestation trusted-root > trusted_root.jsonl` gives the same, plus the root of GitHub's own
instance, which signs for private repositories. An organization's own instance:
`ois trust update --tuf-url https://tuf.acme.example --tuf-root root.json --output acme.json`.

**Other providers** work the same way: GitLab CI, Google Cloud, Buildkite or an organization's own
Sigstore instance are another trusted root and another issuer in the certificate. Outside GitHub,
`cosign attest-blob --type https://ois.example/passport/v0.1 --predicate predicate.json` signs.
Keyless signing covers passports; bundles are signed with keys.

## People

The public Sigstore instance puts a person's e-mail address into the certificate, which the
specification does not allow for human actors (section 12). Two ways keep people pseudonymous:

- **Approve in GitHub, let the pipeline sign.** The person approves as a required reviewer of an
  environment or in a pull request review, protected by your single sign-on; the workflow then
  records the decision with `decidedBy` set to the person's pseudonymous actor and signs. The
  signature shows that the pipeline ran after approval; GitHub's audit log shows who approved.
- **Their own key.** `ois key generate qe-2c9d` gives a person a key with a pseudonymous key id.

An organization's own Sigstore instance, issuing pseudonymous identities from its identity
provider, would also do.
