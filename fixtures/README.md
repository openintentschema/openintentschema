# fixtures

The conformance test suite of section 11.3. A validator conforms if it reports, for every
fixture, exactly the rules and levels the manifest expects.

## Layout

```
manifest.json            every fixture with its description and expected reports
valid/                   inputs that conform: no violation (warnings may be expected)
invalid/schema/          inputs that break Appendix B
invalid/signature/       DSSE envelopes and Sigstore bundles whose signature does not hold
invalid/<rule>/          inputs that trigger one rule of section 5, R1 to R17
keys/                    public test keys and the Sigstore trusted root the verifier trusts
sigstore/                input for keyless signing and the recorded Sigstore bundle
generate.py              builds all of the above
```

Each fixture is one OIS document: a single record, a bundle, or a Quality Passport as an in-toto
Statement v1. Fixtures named `signed-…` are DSSE envelopes around a bundle or passport (section
8.3), `keyless-…` fixtures Sigstore bundles around a passport; `invalid/signature/` holds both. Feed every fixture to a validator as it is, with the keys listed in `trustedKeys` and
the Sigstore trusted roots listed in `trustedRoots` as what it trusts.

## Manifest

```json
{
  "ois": "0.1",
  "trustedKeys": ["keys/agent-runtime.pub", "keys/ci-recorder.pub", "keys/passport-issuer.pub"],
  "trustedRoots": ["keys/sigstore-public-good.trusted_root.json"],
  "fixtures": [
    {
      "path": "invalid/R5/same-producer.json",
      "description": "derivedFrom intent, but the developer agent produced both the test and the code.",
      "expect": [
        { "rule": "R5", "level": "violation" },
        { "rule": "R12", "level": "warning" }
      ]
    }
  ]
}
```

`expect` is the exact set of (rule, level) pairs the validator must report. How often a pair is
reported, the path and the message are up to the validator. A fixture conforms when `expect`
holds no violation.

`rule` is `schema` for Appendix B ([proposed in #1](https://github.com/openintentschema/openintentschema/issues/1)), `signature` for DSSE envelopes and Sigstore bundles
(section 8.3, [proposed in #8](https://github.com/openintentschema/openintentschema/issues/8)) and `R1` to `R17` for section 5. `level` is `violation`,
`warning` or `info` (section 11.1).

Most fixtures are unsigned, so every one whose records carry a `context` expects the R12 warning
for self-declared context. In the signed fixtures, R12 stays silent where the recorder signed.

## How the rules are read

The fixtures pin down choices the specification leaves to the validator. Where this README and
the specification disagree, the specification wins and the fixtures are wrong.

**Scope.** A single record is checked against Appendix B and R17 only. All other rules relate
records to each other and are checked within a bundle or a passport (`predicate.records`). The
fixtures do not use `predicate.bundles`.

**References** are the Ref-typed fields: `producedBy` and `supersedes` (intent); `producedBy`,
`inputs`, `context`, `contextRecordedBy` (artifact); `criterion`, `test`, `subject`, `inputs`,
`recordedBy` (evidence); `subject`, `decidedBy`, `evidence` (decision); `criterion`, `intent`,
`subject`, `reportedBy`, `resolvedBy`, `supersedes` (finding); `intents`, `scope`, `issuedBy`
(passport predicate). URIs such as `source`, `location`, `run`, `ticket` or `policy.id` are not
references.

**Resolution.** `<id>@<version>` resolves to the intent or actor with that `id` and `version`.
`<id>` resolves to a record with that `id` and no `version` (artifact, evidence, decision,
finding, human actor). A plain reference to an agent, tool or intent therefore does not resolve.
`<id>@<version>#<key>` resolves to the intent version and then to its criterion with that `key`.

**No cascades.** A check that needs a record behind an unresolved reference is skipped. The
unresolved reference is reported once, under R10 (record missing) or R2 (criterion key missing).

| Rule | Level | What the fixtures expect |
| --- | --- | --- |
| R1 | violation | Every intent with status `approved` has a decision with gate `intent-approval`, outcome `approved`, `subject` `<id>@<version>` and `subjectDigest` equal to the intent's `digest`. |
| R1 | info | That decision's `decidedBy` is not a human actor. |
| R2 | violation | A criterion reference whose intent version resolves, but which has no criterion with that `key`. |
| R3 | violation | Evidence `test` resolves to an artifact of a kind other than `test`, or `subject` to one other than `code` or `build`. |
| R4 | violation | Evidence with `derivedFrom: intent` whose test artifact has no `context`, a `context` with an artifact of kind `code`, or a `context` that includes neither the criterion reference nor an intent version reference that covers it. A version other than the evidence's covers it only if its criterion with the same `key` has the same digest. |
| R5 | violation | Evidence with `derivedFrom: intent` whose test and subject have `producedBy` actors with the same `id`, in any version. |
| R8 | warning | Evidence `inputs` include a dataset classified `production`. |
| R9 | info | A decision with outcome `waived` whose `decidedBy` is not human. The MUST (rationale) is in Appendix B. |
| R10 | violation | A reference that does not resolve, or two records with the same `id` (and `version` for intents and actors) that differ in content. Intents are compared without `status` and `digest`, so a draft and its approved record count as one; every other record type is compared in full, `digest` included. *Limiting the exception to intents is [proposed in #5](https://github.com/openintentschema/openintentschema/issues/5); not yet in the specification.* `supersedes` is a reference like any other, so the history a document claims is always carried and checkable. |
| R11 | violation | A decision with gate `evidence-revocation` whose `subject` is not an evidence record. Rationale and outcome are in Appendix B. |
| R12 | warning | An artifact with `context` whose `contextRecordedBy` is missing or equals `producedBy` by actor `id`, or whose document is not signed by that actor (see Signatures). |
| R13 | warning | A passport lists an intent version that a current finding with severity `high` or `critical` references through `intent`, or through a `criterion` of that version, and that finding is not resolved. The current finding is the last of its `supersedes` chain. It is resolved if a decision with gate `finding-resolution`, outcome `approved` and the current finding as `subject` exists, made by an actor whose `id` is not `producedBy`, `recordedBy` or `decidedBy` of any record in its `resolvedBy` (R14). |
| R14 | violation | Two findings supersede the same finding. |
| R15 | violation | A passport lists an intent version that is not `approved`, or for which a later version with status `withdrawn` exists. |
| R15 | info | A later version is approved, by a decision made before `issuedAt`. |
| R16 | violation | A passport without a decision with gate `release`, outcome `approved` or `passed`, whose `subject` is an artifact of kind `build` with a digest that matches a digest of the statement's `subject`. *[Proposed in #2](https://github.com/openintentschema/openintentschema/issues/2); not yet in the specification.* |
| R17 | violation | An intent `digest` or criterion `digest` whose `sha256` differs from the value computed by section 6.4. *[Proposed in #3](https://github.com/openintentschema/openintentschema/issues/3); not yet in the specification.* |

R6 and R7 are not checked (section 5) and have no fixtures. The parts of R9 and R11 that
Appendix B already enforces are fixtures under `invalid/schema/`.

## Signatures

The test keys are Ed25519 keys derived from a fixed seed in `generate.py`; anyone can derive the
private keys, so they serve for fixtures only. Ed25519 signs deterministically, which keeps the
signed fixtures reproducible.

- **Envelope.** A DSSE envelope has `payloadType`, `payload` (standard base64) and `signatures`,
  each with `keyid` and `sig` (standard base64). A signature covers the DSSE v1 pre-authentication
  encoding of payload type and payload. The payload is the JSON of a passport (payload type
  `application/vnd.in-toto+json`) or of a bundle (`application/vnd.ois+json`); the rules apply
  to it as to an unwrapped document.
- **Key ids.** A `keyid` is the lowercase hexadecimal SHA-256 of the key's DER-encoded
  SubjectPublicKeyInfo, so a verifier derives it from the key it trusts.
- **Trust.** The verifier decides which public keys it trusts; nothing in the document can make
  it trust a key. The fixtures trust the keys in `trustedKeys`.
- **Attribution.** An actor signed the document when a signature verifies under a trusted key
  whose key id equals the actor's `identity.keyId` (section 8.3), or, for keyless signatures,
  when its certificate identity equals the actor's `identity.issuer` and `identity.subject`.

**Keyless signatures (Sigstore).** A Sigstore bundle (media type
`application/vnd.dev.sigstore.bundle.v0.3+json`, as `actions/attest`, cosign and sigstore-python
write it) carries a DSSE envelope, a short-lived certificate and a transparency log entry. It is
verified against the trusted roots of `trustedRoots`: certificate chain, log entry and signature.
A verified signature is attributed to the actor whose `identity.issuer` equals the certificate's
OIDC issuer (extension 1.3.6.1.4.1.57264.1.8) and whose `identity.subject` equals its subject
alternative name, exactly. For a GitHub Actions workflow these are
`https://token.actions.githubusercontent.com` and
`https://github.com/<owner>/<repo>/.github/workflows/<file>@<ref>`. Without a trusted root the
bundle cannot be checked (warning); a bundle that does not verify counts as unsigned (violation).

Keyless signatures cannot be generated reproducibly, so they are recorded:
`.github/workflows/sigstore-fixtures.yml` signs `sigstore/passport-predicate.json` and its bundle
is committed as `sigstore/passport.sigstore.json`. `generate.py --check` fails when the predicate
changed and the bundle must be recorded again. The trusted root is a snapshot of the public-good
instance's; it keeps verifying the recorded bundle, while bundles signed after a key rotation need
a newer one.

| Rule | Level | What the fixtures expect |
| --- | --- | --- |
| signature | violation | An envelope without signatures, with a payload type other than the one its payload requires, or with a signature under a trusted key id that does not verify. |
| signature | warning | A signature whose key id is not trusted, or a Sigstore bundle without a trusted root: it cannot be checked. |

An envelope with a `signature` violation counts as unsigned: no actor signed it. A signature by
an untrusted key attributes nothing either. R12 then reports the recorded contexts as
self-declared, as for an unsigned document.

## Digests

Intent and criterion digests are computed by `generate.py` with RFC 8785, independently of any
validator. Artifact and passport subject digests stand for external content that no validator
can read; they are stable placeholder values.

## Changing fixtures

Never edit the JSON files by hand. Change `generate.py`, then:

```bash
uv run fixtures/generate.py           # rewrite fixtures and manifest
uv run fixtures/generate.py --check   # what CI runs
```

`--check` fails if a file is out of date or stray, if a fixture outside `invalid/schema/` breaks
the schema, or if one inside it does not.
