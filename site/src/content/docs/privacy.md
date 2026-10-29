---
title: Privacy and data flows
description: What the OIS tools read, write and transmit, and where OIS records go.
---

OIS is a data format, and its tools run where you run them. No `ois` command opens a network
connection, except `ois trust update` when you run it to fetch a Sigstore trusted root: OIS
records stay in your organization until you send them somewhere.

[![Data flows: the tools run inside your organization; installing, pulling the image, keyless signing and fetching a trusted root contact outside services, and records reach others only when you send them](/images/data-flows.svg)](/images/data-flows.svg)

## Who receives what

| Step | What is transmitted | To | How to limit it |
| --- | --- | --- | --- |
| Installing `ois-tools` with `uvx` or `pip` | The download request: IP address and, as pip and uv document for PyPI's download statistics, installer, Python and operating system version and whether it runs in CI | PyPI, run by the Python Software Foundation | Install from an internal package mirror, or a pinned wheel from your own artifact store |
| Installing `uv` with the `setup-uv` GitHub Action | The download request | GitHub | A runner image with `uv` preinstalled |
| Running the setup action `openintentschema/tools/.github/actions/setup` | The download requests for `uv` and for `ois-tools` | GitHub and PyPI | Install from an internal mirror instead |
| Uploading SARIF with `github/codeql-action/upload-sarif` | The reports of `ois validate`: rule, message, file and line | GitHub code scanning of your repository | Leave the upload out; the SARIF file stays local |
| Including the GitLab CI template | The request for the template file, then the image pull | GitHub (`raw.githubusercontent.com`, `ghcr.io`) | Copy the template and the image into your own GitLab instance and registry |
| Running `uvx` where no suitable Python is installed | The download request for a Python build | GitHub, which hosts uv's Python builds | Install Python 3.13 or later yourself, or set `UV_PYTHON_INSTALL_MIRROR` to an internal mirror |
| Pulling the container image `ghcr.io/openintentschema/ois-tools` | The download request: IP address and the image requested | GitHub Container Registry | Mirror the image into your own registry, pinned by digest |
| Running `ois junit` | Nothing. It reads the test reports and the local Git checkout (`git rev-parse`, `ls-files`, `show`, `remote get-url`; never `fetch` or `push`) and writes a file | Nobody | |
| Running `ois validate` | Nothing. The JSON Schema ships inside the package and is never fetched | Nobody | |
| Running `ois intent` | Nothing. It reads and writes intent and decision files locally | Nobody | |
| Running `ois cucumber` | Nothing. It reads the Cucumber Messages file and the feature files in the local Git checkout and writes records; error messages and stack traces are not copied | Nobody | |
| Running `ois record` | Nothing. It reads the files it records and the local Git checkout (`git rev-parse`, `ls-files`, `diff`, `remote get-url`; never `fetch` or `push`) and writes record files | Nobody | |
| Running `ois passport` | Nothing. It reads records and writes the passport file locally | Nobody | |
| Running `ois coverage` | Nothing. It reads records or a passport and prints the result | Nobody | |
| Running `ois key` and `ois sign` | Nothing. Keys are created and used locally; the private key never leaves the file you keep it in | Nobody | Keep private keys in a secret store |
| Signing keylessly with `actions/attest` or cosign | The workflow's identity token and the signature | Sigstore (Fulcio and the public transparency log Rekor) or your own instance; on GitHub also the repository's attestations | The log is public by design: it records the identity, the time and the digest, not the passport |
| Fetching a trusted root with `ois trust update` | The request for Sigstore's signed TUF metadata and trusted root | Sigstore's TUF repository (`tuf-repo-cdn.sigstore.dev`), or your own instance's | Keep a reviewed copy and refresh it on your schedule |
| Fetching a trusted root with `gh attestation trusted-root` | The request | GitHub | Keep a reviewed copy and refresh it on your schedule |
| Verifying a Sigstore bundle with `ois validate`, `ois coverage` or `ois passport build` | Nothing. The trusted root is a local file | Nobody | |
| Sharing a signed bundle or passport | Its records, the signatures and the key ids | The recipients you choose | Recipients verify with the public keys you give them, or with a Sigstore trusted root for keyless signatures |
| Storing bundles | The bundle file | Wherever your pipeline keeps artifacts | Your retention rules apply |
| Sharing a bundle or passport | Its records (below) | The recipients you choose, such as an auditor or a customer | Review before sharing (specification section 12) |
| Visiting this website | The request: IP address, page, browser | GitHub Pages, which hosts the site | The site loads nothing from other domains and sets no cookies; your theme choice stays in your browser |
| Opening an issue or pull request | What you write | GitHub, publicly | Report security issues privately |
| Writing to editors@openintentschema.io | Your e-mail | Proton Mail, the project's mail provider | |

## What a bundle from `ois junit` contains

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

Every `ois` command except `ois trust update`, whose job is fetching a trusted root, and the whole
test suite of the tools, were run in a sandbox that blocks all network access. All of them work unchanged;
a network request in that sandbox fails. The container image runs them with
`docker run --network none` in the CI of the tools. What pip
and uv send to PyPI is taken from their documentation, not measured here.

## In the specification

Section 12 of the specification sets the privacy rules for records: no personal data apart from
actor names and identifiers, pseudonyms for human actors, test data referenced by location and
digest rather than embedded, and datasets with personal data classified as `production` or
`anonymized`.
