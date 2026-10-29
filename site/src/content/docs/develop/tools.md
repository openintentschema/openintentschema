---
title: Reference tools
description: One command, ois, to record OIS evidence along the delivery lifecycle and to check records, bundles and Quality Passports.
---

The reference tools record OIS evidence where it arises and check it against the specification.
They are one command, `ois`, open source under Apache-2.0, published on PyPI as
[`ois-tools`](https://pypi.org/project/ois-tools/) and as a container image; the source is in
[openintentschema/tools](https://github.com/openintentschema/tools).

## Along the delivery lifecycle

| Phase | What is recorded | Command | Guide |
| --- | --- | --- | --- |
| Requirement | intent with acceptance criteria, its approval | `ois intent`, `ois intent from-gherkin` | [Write and approve intents](/approve-intents/), [Gherkin](/gherkin-cucumber/) |
| Design | design approval | `ois record decision --gate design-approval` | [Record artifacts, decisions and findings](/record/) |
| Implementation | code artifact, the context an agent was given | `ois record artifact` | [Record artifacts, decisions and findings](/record/) |
| Test | evidence per criterion, measures for non-functional ones | `ois junit --intent`, `ois cucumber`, `ois measure`, `ois record evidence` | [Link tests](/link-tests/), [Measure](/measure/), [Cucumber](/gherkin-cucumber/), [Getting started](/getting-started/) |
| Merge | merge decision | `ois record decision --gate merge` | [Record artifacts, decisions and findings](/record/) |
| Release | build, release decision, signed passport with intent coverage | `ois record`, `ois passport build --sign` | [Build a Quality Passport](/build-a-passport/), [Sign](/sign/) |
| Operation | findings, their classification and resolution | `ois record finding`, `ois record supersede` | [Record artifacts, decisions and findings](/record/) |
| Review by others | check a passport and recompute its coverage | `ois validate`, `ois coverage` | [Build a Quality Passport](/build-a-passport/#check-it) |

`ois key`, `ois sign` and `ois trust` sign and verify along the way: DSSE with your own keys, or
keylessly through Sigstore, for example with GitHub Actions; see
[Sign bundles and passports](/sign/).

The tools record and check; they do not enforce. Whether a merge or a release is blocked, for
example below a coverage threshold or with an open critical finding, is the policy of your
pipeline, which reads the commands' exit codes and figures.

## Install and run

```bash
uvx --from ois-tools ois validate bundle.json    # run without installing
pip install ois-tools                            # or install; Python 3.13 or later
ois --help                                       # the commands
```

The commands work for projects in any language: they read JSON, YAML, test reports and the Git
checkout, not the code. Without Python, use the container image, which runs `ois` and holds git
(linux/amd64 and linux/arm64):

```bash
docker run --rm --network none -v "$PWD:/work" --user "$(id -u):$(id -g)" \
  ghcr.io/openintentschema/ois-tools validate bundle.json
```

To check with Node.js, the npm package `ois-tools` brings the same `ois validate` and
`ois coverage`; the commands that write records are in the Python package
([With Node.js](#with-nodejs)):

```bash
npx ois-tools validate bundle.json               # run without installing
npm install -g ois-tools                         # or install; Node.js 24 or later
```

In CI, `uses: openintentschema/tools/.github/actions/setup@v0.13.0` installs `ois` on GitHub Actions, and
`.gitlab/ci/ois.gitlab-ci.yml` in the tools repository is a template for GitLab CI; see
[Getting started](/getting-started/#6-add-it-to-your-pipeline).

The arguments after the image name go to `ois`. In a CI job that uses the image as its image,
override the entrypoint (GitLab: `entrypoint: [""]`) and call `ois` in the script. Each image
carries a signed build provenance and an SBOM; check it with
`gh attestation verify oci://ghcr.io/openintentschema/ois-tools:<version> --owner openintentschema`.

Up to version 0.5.0 the package was called `ois-validator`, with one command per tool
(`ois-validator`, `ois-junit`, …).

## Official packages

The tools are published only under these names, each built and signed by a workflow of the
`openintentschema` organization on GitHub:

| Package | Registry | Built in |
| --- | --- | --- |
| `ois-tools` for Python | [PyPI](https://pypi.org/project/ois-tools/) | [openintentschema/tools](https://github.com/openintentschema/tools) |
| `ois-tools` for Node.js | [npm](https://www.npmjs.com/package/ois-tools) | [openintentschema/tools-js](https://github.com/openintentschema/tools-js) |
| `ghcr.io/openintentschema/ois-tools` | GitHub Container Registry | [openintentschema/tools](https://github.com/openintentschema/tools) |

A package under another name or scope is not part of the project, even if it carries
"openintentschema" in its name. Check where a download was built:

```bash
uvx pypi-attestations@0.0.30 verify pypi --repository https://github.com/openintentschema/tools \
  pypi:ois_tools-0.13.0-py3-none-any.whl
npm audit signatures        # in a project that installed ois-tools
gh attestation verify oci://ghcr.io/openintentschema/ois-tools:0.13.0 --owner openintentschema
```

The first command checks the PyPI attestation and fails for a package built elsewhere; the second
verifies the provenance npm recorded; the third the build provenance of the image. Report a package
that impersonates the project privately, as the
[security policy](https://github.com/openintentschema/tools/security/policy) describes.

## Validate

```bash
ois validate bundle.json passport.json
ois validate --format json finding.json
ois validate --format sarif passport.json > ois.sarif   # for GitHub code scanning and IDEs
```

Each file holds one JSON document: a single record, a bundle, or a passport as an in-toto
Statement v1. Exit code 0 means every file conforms, 1 means at least one violation, 2 means a
file could not be read. Reports point at the field concerned:

```
same-producer.json: violation [R5] $.records[12].derivedFrom: test and subject are both produced by https://ois.acme.example/actors/dev-agent
```

| Level | Meaning | Rules |
| --- | --- | --- |
| violation | A MUST is broken; the input does not conform. | the schema, the signature, R1–R5, R10, R11, R14–R17 |
| warning | A rule asks for a report; the input still conforms. | the signature (key or root not trusted), R8, R12, R13 |
| info | A SHOULD is not followed. | R1, R9, R15 |

Profiles add rules for an industry: `ois validate` checks [regulated/v0.1](/profiles/regulated/v0.1/)
(rules `regulated/P1` to `regulated/P4`) when a record lists it, or with
`--profile regulated/v0.1`.

R16, R17 and the rule IDs `schema` and `signature` are proposed in RFCs. A signed document is
verified with the public keys passed as `--trusted-key`, a Sigstore bundle against the trusted
roots passed as `--trusted-root`; a recorded context is attested when its recorder signed (R12).
See [Sign bundles and passports](/sign/).


### With Node.js

A second implementation of the validator and of `ois coverage`, for Node.js 24 or later, is
published on npm as
[`ois-tools`](https://www.npmjs.com/package/ois-tools); the source is in
[openintentschema/tools-js](https://github.com/openintentschema/tools-js). It checks the same:
Appendix B, R1 to R5 and R8 to R17, the profile `regulated/v0.1`, DSSE and keyless Sigstore
signatures, with the same options, reports and exit codes. It reads JSON; YAML drafts of intents
are read by the Python package only:

```bash
npx ois-tools validate passport.json --trusted-root trusted_root.json
npx ois-tools coverage passport.json --format markdown
npm install -g ois-tools    # then: ois validate passport.json
```

Both implementations pass every conformance fixture of the specification and compute the same
coverage. In JavaScript they are also a library: `import { validate, passportCoverage } from
'ois-tools'`.

## Test your own implementation

A validator conforms if it reports exactly what the
[conformance test suite](/conformance/) expects for every fixture. `ois validate` runs the whole
suite in its tests; any other implementation can use the same fixtures and manifest.
