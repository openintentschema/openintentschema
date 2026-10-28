---
title: Sign bundles and passports
description: Sign OIS bundles and Quality Passports with DSSE, so that recipients can attribute them and recorded contexts count as attested.
---

A signature makes a bundle or a Quality Passport attributable: a recipient can check who issued
it and that nothing changed since. It is also what turns a recorded `context` from self-declared
into attested (rule R12), and what Level 3 conformance requires (specification sections 8.3 and
11.2). `ois sign`, `ois key` and `ois passport build --sign`, part of the
[`ois-tools`](/develop/tools/) package, sign with DSSE.

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

## Not yet supported

With your own keys, "attested" means signed by a key the verifier trusts. Which person or system
holds that key is the verifier's knowledge, not part of the signature. Sigstore keyless signing,
where a short-lived certificate names the workload identity (for example a CI workflow or a
SPIFFE ID), and transparency logs such as Rekor, which give each signature an independent time,
follow in a later version.
