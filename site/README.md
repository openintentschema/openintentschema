# site

Source of the website [openintentschema.io](https://openintentschema.io), built with
[Astro Starlight](https://starlight.astro.build/) and published to GitHub Pages by
`.github/workflows/site.yml` on every push to `main` that touches `site/` or `schema/`.

```bash
cd site
npm ci            # Node.js version in .nvmrc
npm run dev       # local preview at http://localhost:4321
npm run build     # static site in dist/, then publishes the schema (below)
```

## Pages

Content lives in `src/content/docs/` as Markdown; the sidebar is set in `astro.config.mjs`.

| URL | Source |
| --- | --- |
| `/` | `src/content/docs/index.mdx` |
| `/getting-started/` | `src/content/docs/getting-started.md` |
| `/passport/v0.1/` | `src/content/docs/passport/v0.1.md` |
| `/methods/basic-intent-coverage/v0.1/` | `src/content/docs/methods/basic-intent-coverage/v0.1.md` |
| `/schema/v0.1/ois.schema.json` | `../schema/ois.schema.json`, copied by `scripts/publish-schema.mjs` |

## Versioned URLs never change

`/schema/v0.1/…`, `/passport/v0.1/` and `/methods/basic-intent-coverage/v0.1/` are identifiers
that records refer to (RFC #6). Once published, their meaning does not change: a correction gets
a new version and a new URL. The build fails if the published schema differs from
`schema/ois.schema.json`.

## Privacy

The site loads nothing from third parties: no web fonts, scripts, images or analytics from other
domains. Search runs in the browser on a local index. GitHub Pages, which serves the site, sees
the requests like any web server.
