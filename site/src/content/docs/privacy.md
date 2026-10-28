---
title: Privacy and data flows
description: What the OIS tools read, write and transmit, and where OIS records go.
---

OIS is a data format, and its tools run where you run them. `ois-validator` and `ois-junit` open
no network connection: OIS records stay in your organization until you send them somewhere.

[![Data flows: the tools run inside your organization; only installing the package contacts PyPI, and records reach others only when you send them](/images/data-flows.svg)](/images/data-flows.svg)

## Who receives what

| Step | What is transmitted | To | How to limit it |
| --- | --- | --- | --- |
| Installing `ois-validator` with `uvx` or `pip` | The download request: IP address and, as pip and uv document for PyPI's download statistics, installer, Python and operating system version and whether it runs in CI | PyPI, run by the Python Software Foundation | Install from an internal package mirror, or a pinned wheel from your own artifact store |
| Installing `uv` with the `setup-uv` GitHub Action | The download request | GitHub | A runner image with `uv` preinstalled |
| Running `ois-junit` | Nothing. It reads the JUnit XML and the local Git checkout (`git rev-parse`, `ls-files`, `show`, `remote get-url`; never `fetch` or `push`) and writes a file | Nobody | |
| Running `ois-validator` | Nothing. The JSON Schema ships inside the package and is never fetched | Nobody | |
| Storing bundles | The bundle file | Wherever your pipeline keeps artifacts | Your retention rules apply |
| Sharing a bundle or passport | Its records (below) | The recipients you choose, such as an auditor or a customer | Review before sharing (specification section 12) |
| Visiting this website | The request: IP address, page, browser | GitHub Pages, which hosts the site | The site loads nothing from other domains and sets no cookies; your theme choice stays in your browser |
| Opening an issue or pull request | What you write | GitHub, publicly | Report security issues privately |
| Writing to editors@openintentschema.io | Your e-mail | Proton Mail, the project's mail provider | |

## What a bundle from `ois-junit` contains

| Contained | Not contained |
| --- | --- |
| Test names, as criterion statements | Test output, failure messages and stack traces |
| Paths of test files and the `sha256` of their content | The content of test files or any source code |
| Repository URL without credentials, commit hash | User names, e-mail addresses, CI variables or secrets |
| Suite name, the namespace you chose, the pipeline run URL | Host names of build machines |
| Result per test and the time it was observed | Timing or performance data |

Test names and repository URLs can still reveal internal information. Check them before a bundle
leaves your organization; test names must not contain personal data (specification section 12.1).

## How this was checked

`ois-validator` and `ois-junit`, and the validator's whole test suite, were run in a sandbox that
blocks all network access. Both work unchanged; a network request in that sandbox fails. What pip
and uv send to PyPI is taken from their documentation, not measured here.

## In the specification

Section 12 of the specification sets the privacy rules for records: no personal data apart from
actor names and identifiers, pseudonyms for human actors, test data referenced by location and
digest rather than embedded, and datasets with personal data classified as `production` or
`anonymized`.
