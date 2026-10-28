---
title: Reference validator
description: Check OIS records, bundles and Quality Passports against the schema and the integrity rules.
---

The reference validator checks OIS documents against the JSON Schema and every integrity rule
that can be checked from the records at hand, and reports each problem with its rule and level.
It is open source under Apache-2.0 and published on PyPI as
[`ois-validator`](https://pypi.org/project/ois-validator/); the source is in
[openintentschema/validator](https://github.com/openintentschema/validator).

## Install and run

```bash
uvx ois-validator bundle.json          # run without installing
pip install ois-validator              # or install; Python 3.13 or later
```

```bash
ois-validator bundle.json passport.json
ois-validator --format json finding.json
```

Each file holds one JSON document: a single record, a bundle, or a passport as an in-toto
Statement v1. Exit code 0 means every file conforms, 1 means at least one violation, 2 means a
file could not be read. Reports point at the field concerned:

```
same-producer.json: violation [R5] $.records[12].derivedFrom: test and subject are both produced by https://ois.acme.example/actors/dev-agent
```

## What it checks

| Level | Meaning | Rules |
| --- | --- | --- |
| violation | A MUST is broken; the input does not conform. | the schema, R1–R5, R10, R11, R14–R17 |
| warning | A rule asks for a report; the input still conforms. | R8, R12, R13 |
| info | A SHOULD is not followed. | R1, R9, R15 |

R16 and R17 are proposed in open RFCs. Signatures are not verified yet, so R12 reports every
recorded context as self-declared.

## Commands that write records

The package also brings commands that write OIS records and validate them before writing:

| Command | Writes | Guide |
| --- | --- | --- |
| `ois-junit` | A Level 1 bundle from JUnit XML | [Getting started](/getting-started/) |
| `ois-intent` | Sealed and approved intents, new versions | [Write and approve intents](/approve-intents/) |
| `ois-record` | Actors, artifacts, evidence, decisions, findings, bundles | [Record artifacts, decisions and findings](/record/) |
| `ois-passport` | A Quality Passport for a release | [Build a Quality Passport](/build-a-passport/) |

## Test your own implementation

A validator conforms if it reports exactly what the
[conformance test suite](/conformance/) expects for every fixture. The reference validator runs
the whole suite in its tests; any other implementation can use the same fixtures and manifest.
