# profiles

The registry of OIS profiles (specification section 10.2). A profile is a published document,
identified by an absolute URI, that adds constraints to the core: it can make optional fields
required, narrow enumerations, require signing or define extension namespaces with their schemas.
A profile never relaxes a core requirement, and a record that lists a profile in `profiles` must
satisfy it.

## Registered profiles

| Profile | URI | Status | Owner |
| --- | --- | --- | --- |
| [Regulated industries](regulated/v0.1/) | `https://openintentschema.io/profiles/regulated/v0.1` | example, draft | OIS editors |

## What a profile provides

- **A document** that states each constraint, normatively, with an identifier per rule so that
  validators can report it (for example `regulated/P1`).
- **A JSON Schema** for every constraint a schema can express, composed with Appendix B through
  `allOf` (section 10.2 says SHOULD). Constraints across records, such as who made a decision,
  stay in the document.
- **A versioned URI.** Like the core identifiers, a published profile version never changes; a
  change gets a new version.

## Checking a profile

The reference tools check `regulated/v0.1`: `ois validate` applies it when a record lists its
URI, or with `--profile regulated/v0.1`. The conformance fixtures test each rule
(`fixtures/invalid/regulated/`).

## Registering a profile

Open a pull request that adds a row to the table above and, if the profile is maintained here, a
folder `<name>/v<version>/` with its document and schema. A profile maintained elsewhere is listed
with its URI and owner only. A profile name says what it is for, never which product or vendor it
favours (`GOVERNANCE.md`, Neutrality).

Profile URIs live under `https://openintentschema.io/`, as the core identifiers do; a profile
schema refers to the core schema by its `$id`.
