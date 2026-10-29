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
      defaultLocale: 'root',
      locales: { root: { label: 'English', lang: 'en' }, de: { label: 'Deutsch', lang: 'de' } },
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
              label: { en: 'Documentation', de: 'Dokumentation' },
              link: '/',
              items: [
                {
                  label: 'Get started',
                  translations: { de: 'Einstieg' },
                  items: [
                    { label: 'What is OIS?', slug: 'index', translations: { de: 'Was ist OIS?' } },
                    { label: 'Getting started', slug: 'getting-started', translations: { de: 'Erste Schritte' } },
                    { label: 'Write and approve intents', slug: 'approve-intents', translations: { de: 'Intents schreiben und freigeben' } },
                    { label: 'Link tests to criteria', slug: 'link-tests', translations: { de: 'Tests mit Kriterien verknüpfen' } },
                    { label: 'Use Gherkin and Cucumber', slug: 'gherkin-cucumber', translations: { de: 'Gherkin und Cucumber verwenden' } },
                    { label: 'Record artifacts, decisions and findings', slug: 'record', translations: { de: 'Artefakte, Entscheidungen und Findings erfassen' } },
                    { label: 'Build a Quality Passport', slug: 'build-a-passport', translations: { de: 'Einen Quality Passport erstellen' } },
                    { label: 'Sign bundles and passports', slug: 'sign', translations: { de: 'Bundles und Passports signieren' } },
                    { label: 'Privacy and data flows', slug: 'privacy', translations: { de: 'Datenschutz und Datenflüsse' } },
                  ],
                },
                {
                  label: 'Learn',
                  translations: { de: 'Verstehen' },
                  items: [{ label: 'Core concepts', slug: 'learn/core-concepts', translations: { de: 'Kernkonzepte' } }],
                },
                {
                  label: 'Develop',
                  translations: { de: 'Entwickeln' },
                  items: [
                    { label: 'Reference tools', slug: 'develop/tools', translations: { de: 'Referenz-Werkzeuge' } },
                    { label: 'Conformance test suite', slug: 'conformance', translations: { de: 'Konformitätstests' } },
                  ],
                },
              ],
            },
            {
              label: { en: 'Specification', de: 'Spezifikation' },
              id: 'specification',
              link: '/specification/',
              items: [
                {
                  label: 'Specification v0.1',
                  translations: { de: 'Spezifikation v0.1' },
                  items: [
                    { label: 'Overview', slug: 'specification', translations: { de: 'Übersicht' } },
                    { autogenerate: { directory: 'specification' } },
                  ],
                },
                {
                  label: 'Reference',
                  translations: { de: 'Referenz' },
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
                  translations: { de: 'Mitmachen' },
                  items: [
                    { label: 'Open RFCs', link: `${repo}/issues?q=is%3Aopen+label%3Arfc` },
                    { label: 'GitHub organization', link: 'https://github.com/openintentschema' },
                  ],
                },
              ],
            },
          ],
          {
            exclude: ['/404'],
            // frozen versions of the specification (scripts/sync-content.mjs)
            topics: { specification: ['{,/de}/specification/v*', '{,/de}/specification/v*/**'] },
          },
        ),
        // German pages link to pages that exist only in English; Starlight shows those as fallbacks.
        starlightLinksValidator({ errorOnFallbackPages: false }),
        starlightLlmsTxt({
          projectName: 'Open Intent Schema (OIS)',
          description:
            'OIS is an open, vendor-neutral data standard that links what was required (an intent with acceptance criteria) to what was produced and to the evidence that it meets the requirement.',
        }),
      ],
    }),
  ],
});
