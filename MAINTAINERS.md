# Maintainers

| Name | Role | Organization |
| --- | --- | --- |
| Louis Stark | Editor | intellon |

Editors from one organization must not form a majority once more than one organization participates.

## Before the first stable release

Decided 2026-10-28: once the first stable version goes live, set up GitHub rulesets in this
repository and in [openintentschema/tools](https://github.com/openintentschema/tools):

- block force pushes and deletions on `main`;
- require a pull request (admin bypass optional) and the CI checks;
- in the tools repository, a tag ruleset for `v*` that only admins may push;
- require contributors to sign off on web-based commits (covers the website's "Edit page" link);
- require approval for workflow runs from fork pull requests.

Until then `main` is unprotected.
