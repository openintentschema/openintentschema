// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

const repo = 'https://github.com/openintentschema/openintentschema';

export default defineConfig({
  site: 'https://openintentschema.io',
  integrations: [
    starlight({
      title: 'Open Intent Schema',
      description: 'What was asked, what was built, and the proof in between.',
      favicon: '/favicon.svg',
      // src/content/docs/404.md replaces the built-in page
      disable404Route: true,
      social: [{ icon: 'github', label: 'GitHub', href: 'https://github.com/openintentschema' }],
      editLink: { baseUrl: `${repo}/edit/main/site/` },
      sidebar: [
        { label: 'Start', items: [{ label: 'Getting started', slug: 'getting-started' }] },
        {
          label: 'Reference',
          items: [
            { label: 'Passport predicate v0.1', link: '/passport/v0.1/' },
            { label: 'Coverage method v0.1', link: '/methods/basic-intent-coverage/v0.1/' },
            { label: 'JSON Schema v0.1', link: '/schema/v0.1/ois.schema.json' },
          ],
        },
        {
          label: 'Project',
          items: [
            { label: 'Specification', link: `${repo}/tree/main/specification` },
            { label: 'Conformance fixtures', link: `${repo}/tree/main/fixtures` },
            { label: 'Reference validator', link: 'https://github.com/openintentschema/validator' },
            { label: 'Open RFCs', link: `${repo}/issues?q=is%3Aopen+label%3Arfc` },
          ],
        },
      ],
    }),
  ],
});
