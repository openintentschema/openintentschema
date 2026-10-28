# Governance

This document describes how the Open Intent Schema (OIS) is governed during its 0.x phase.
It is itself subject to change through the process below.

## Roles

- **Editors** maintain the specification, schema and reference implementation, and decide
  on RFCs by rough consensus. The initial editors are listed in `MAINTAINERS.md`.
- **Contributors** are anyone who opens an issue, an RFC or a pull request.
- **Design partners** are organizations that test the specification in real pipelines and
  feed back findings. They have no formal vote but their findings are prioritized.

## Changes

1. Any change to the data model, integrity rules, schema, conformance levels or passport
   format starts as an **RFC issue** using the RFC template. Editorial fixes do not.
2. An RFC is open for comment for at least 14 days.
3. Editors decide by rough consensus. Decisions and their rationale are recorded in the RFC.
4. The implementing pull request updates specification text, schema, examples and fixtures together.
5. Every draft gets an entry in the change history of the specification.

## Contributions

All contributions require a Developer Certificate of Origin (DCO) sign-off on each commit
(`git commit -s`). See `CONTRIBUTING.md`.

## Neutrality

OIS is vendor-neutral. The specification must not require, favour or name any product.
Vendor-specific data lives in `extensions` under a reverse-DNS namespace; industry-specific
rules live in profiles. Editors from the same organization must not form a majority.

## Foundation

The editors intend to transfer the specification, its trademark and this repository to a
neutral foundation under the Linux Foundation once the specification reaches 1.0 or has
three independent implementations, whichever comes first. The governance described here is
designed to survive that transfer unchanged.
