# Security policy

## Reporting a vulnerability

Please do not open a public issue. Report it privately through GitHub: **Security → Report a
vulnerability** in this repository.

Relevant here are weaknesses in the specification, the JSON Schema or the conformance fixtures,
for example:

- a rule or a gap between rules that lets forged, replayed or tampered evidence pass in every
  conforming validator;
- a way to make a Quality Passport look complete or signed when it is not;
- a field that forces producers to disclose personal or confidential data.

Section 12 of the specification lists the threats it already addresses. A bug in the reference
tools (the `ois` command) belongs to
[openintentschema/tools](https://github.com/openintentschema/tools/security).

Confirmed weaknesses are fixed through the RFC process once a fix can be discussed publicly.
