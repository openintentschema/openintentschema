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
| Requirement | intent with acceptance criteria, its approval | `ois intent` | [Write and approve intents](/approve-intents/) |
| Design | design approval | `ois record decision --gate design-approval` | [Record artifacts, decisions and findings](/record/) |
| Implementation | code artifact, the context an agent was given | `ois record artifact` | [Record artifacts, decisions and findings](/record/) |
| Test | evidence per criterion | `ois junit`, `ois record evidence` | [Getting started](/getting-started/) |
| Merge | merge decision | `ois record decision --gate merge` | [Record artifacts, decisions and findings](/record/) |
| Release | build, release decision, signed passport with intent coverage | `ois record`, `ois passport --sign` | [Build a Quality Passport](/build-a-passport/), [Sign](/sign/) |
| Operation | findings, their classification and resolution | `ois record finding`, `ois record supersede` | [Record artifacts, decisions and findings](/record/) |
| Review by others | check a passport and recompute its coverage | `ois validate`, `ois coverage` | [Build a Quality Passport](/build-a-passport/#check-it) |

The tools record and check; they do not enforce. Whether a merge or a release is blocked, for
example below a coverage threshold or with an open critical finding, is the policy of your
pipeline, which reads the commands' exit codes and figures.

## Install and run

```bash
uvx --from ois-tools ois validate bundle.json    # run without installing
pip install ois-tools                            # or install; Python 3.13 or later
ois --help                                       # the commands
```

The commands work for projects in any language: they read JSON, YAML, JUnit XML and the Git
checkout, not the code. Without Python, use the container image, which runs `ois` and holds git
(linux/amd64 and linux/arm64):

```bash
docker run --rm --network none -v "$PWD:/work" --user "$(id -u):$(id -g)" \
  ghcr.io/openintentschema/ois-tools validate bundle.json
```

The arguments after the image name go to `ois`. In a CI job that uses the image as its image,
override the entrypoint (GitLab: `entrypoint: [""]`) and call `ois` in the script. Each image
carries a signed build provenance and an SBOM; check it with
`gh attestation verify oci://ghcr.io/openintentschema/ois-tools:<version> --owner openintentschema`.

Up to version 0.5.0 the package was called `ois-validator`, with one command per tool
(`ois-validator`, `ois-junit`, …).

## Validate

```bash
ois validate bundle.json passport.json
ois validate --format json finding.json
```

Each file holds one JSON document: a single record, a bundle, or a passport as an in-toto
Statement v1. Exit code 0 means every file conforms, 1 means at least one violation, 2 means a
file could not be read. Reports point at the field concerned:

```
same-producer.json: violation [R5] $.records[12].derivedFrom: test and subject are both produced by https://ois.acme.example/actors/dev-agent
```

| Level | Meaning | Rules |
| --- | --- | --- |
| violation | A MUST is broken; the input does not conform. | the schema, R1–R5, R10, R11, R14–R17 |
| warning | A rule asks for a report; the input still conforms. | R8, R12, R13 |
| info | A SHOULD is not followed. | R1, R9, R15 |

R16, R17 and the rule IDs `schema` and `signature` are proposed in RFCs. A signed document is
verified with the public keys passed as `--trusted-key`; a recorded context is attested when its
recorder signed (R12). Sigstore keyless signatures are not verified yet. See
[Sign bundles and passports](/sign/).

## Test your own implementation

A validator conforms if it reports exactly what the
[conformance test suite](/conformance/) expects for every fixture. `ois validate` runs the whole
suite in its tests; any other implementation can use the same fixtures and manifest.
