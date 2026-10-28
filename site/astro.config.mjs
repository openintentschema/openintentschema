// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import starlightLinksValidator from 'starlight-links-validator';
import starlightLlmsTxt from 'starlight-llms-txt';
import starlightSidebarTopics from 'starlight-sidebar-topics';

const repo = 'https://github.com/openintentschema/openintentschema';

export default defineConfig({
  site: 'https://openintentschema.io',
  integrations: [
    starlight({
      title: 'Open Intent Schema',
      description: 'What was asked, what was built, and the proof in between.',
      logo: { light: './src/assets/logo-light.svg', dark: './src/assets/logo-dark.svg' },
      favicon: '/favicon.svg',
      customCss: ['./src/styles/custom.css'],
      // src/content/docs/404.md replaces the built-in page
      disable404Route: true,
      social: [{ icon: 'github', label: 'GitHub', href: 'https://github.com/openintentschema' }],
      editLink: { baseUrl: `${repo}/edit/main/site/` },
      components: {
        Header: './src/components/Header.astro',
        Sidebar: './src/components/Sidebar.astro',
      },
      plugins: [
        starlightSidebarTopics(
          [
            {
              label: 'Documentation',
              link: '/',
              items: [
                {
                  label: 'Get started',
                  items: [
                    { label: 'What is OIS?', link: '/' },
                    { label: 'Getting started', slug: 'getting-started' },
                    { label: 'Write and approve intents', slug: 'approve-intents' },
                    { label: 'Build a Quality Passport', slug: 'build-a-passport' },
                    { label: 'Privacy and data flows', slug: 'privacy' },
                  ],
                },
                { label: 'Learn', items: [{ label: 'Core concepts', slug: 'learn/core-concepts' }] },
                {
                  label: 'Develop',
                  items: [
                    { label: 'Reference validator', slug: 'develop/validator' },
                    { label: 'Conformance test suite', slug: 'conformance' },
                  ],
                },
              ],
            },
            {
              label: 'Specification',
              link: '/specification/',
              items: [
                {
                  label: 'Specification v0.1',
                  items: [
                    { label: 'Overview', slug: 'specification' },
                    { autogenerate: { directory: 'specification' } },
                  ],
                },
                {
                  label: 'Reference',
                  items: [
                    { label: 'Passport predicate v0.1', slug: 'passport/v0.1' },
                    { label: 'Coverage method v0.1', slug: 'methods/basic-intent-coverage/v0.1' },
                    // Until RFC #6 sets the $id, the schema is linked on GitHub (scripts/publish-schema.mjs)
                    { label: 'JSON Schema v0.1', link: `${repo}/blob/main/schema/ois.schema.json` },
                    { label: 'Conformance test suite', slug: 'conformance' },
                    { label: 'Profiles', slug: 'profiles' },
                    { label: 'Regulated industries v0.1', slug: 'profiles/regulated/v0.1' },
                  ],
                },
              ],
            },
            {
              label: 'Community',
              link: '/community/governance/',
              items: [
                {
                  label: 'Community',
                  items: [
                    { label: 'Governance', slug: 'community/governance' },
                    { label: 'Contributing', slug: 'community/contributing' },
                    { label: 'Code of Conduct', slug: 'community/code-of-conduct' },
                    { label: 'Security', slug: 'community/security' },
                    { label: 'Maintainers', slug: 'community/maintainers' },
                  ],
                },
                {
                  label: 'Take part',
                  items: [
                    { label: 'Open RFCs', link: `${repo}/issues?q=is%3Aopen+label%3Arfc` },
                    { label: 'GitHub organization', link: 'https://github.com/openintentschema' },
                  ],
                },
              ],
            },
          ],
          { exclude: ['/404'] },
        ),
        starlightLinksValidator(),
        starlightLlmsTxt({
          projectName: 'Open Intent Schema (OIS)',
          description:
            'OIS is an open, vendor-neutral data standard that links what was required (an intent with acceptance criteria) to what was produced and to the evidence that it meets the requirement.',
        }),
      ],
    }),
  ],
});
