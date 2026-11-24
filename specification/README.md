# specification

- `ois-spec-v0.1-draft5.md`: Open Intent Schema Specification v0.1, working draft 5 (see its
  change history). Licensed under CC BY 4.0 (`../LICENSE-docs`).
- `archive/`: earlier drafts as published, frozen; the website shows them under
  `/specification/v<version>/`.

Appendix B of the specification embeds `../schema/ois.schema.json` verbatim, and Appendix A
embeds the examples in `../examples/`. Change them together.

The diagram in section 5 is a placeholder in this Markdown version; the website draws it.

## Publishing a draft

A draft is prepared on a branch in this repository and, for a change validators must follow, on
branches of [tools](https://github.com/openintentschema/tools) and
[tools-js](https://github.com/openintentschema/tools-js). The order matters:

1. Decide every RFC the draft carries and record the decision in its issue (`../GOVERNANCE.md`).
2. Set the date of the draft in the byline and in the change history, copy the previous draft to
   `archive/` and list both in `../site/spec-versions.json` (`../site/README.md`).
3. Merge to `main`. If the passport predicate of the keyless fixture changed,
   `fixtures/generate.py --check` fails on the branch and on `main` until the fixture is recorded
   again: run the workflow "Record the keyless signed fixtures" on `main`, commit the downloaded
   bundle as `../fixtures/sigstore/passport.sigstore.json` and run `uv run fixtures/generate.py`.
   The signer identity names `refs/heads/main`, so it cannot be recorded on a branch.
4. In tools, then in tools-js: sync the copies from this repository's `main`, merge and release.
   The Python tools go first, because the comparison job of tools-js installs that release.
5. Update the versions and outputs in the guides of the website from the released tools.
