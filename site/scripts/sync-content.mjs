// Turn documents that live elsewhere in the repository into site pages, so they have one source:
// the specification (one page per top-level section), the community documents, the conformance
// fixtures README and the profile registry. Output goes to src/content/docs/{specification,
// community,profiles}/ and is not committed; edit the sources instead.
import { mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';

const root = new URL('../../', import.meta.url);
const docs = new URL('../src/content/docs/', import.meta.url);
const repo = 'https://github.com/openintentschema/openintentschema';
const specFile = 'specification/ois-spec-v0.1-draft4.md';

// Repository files that are pages on the site; other relative links point to GitHub.
const pages = {
  'GOVERNANCE.md': '/community/governance/',
  '.github/CONTRIBUTING.md': '/community/contributing/',
  '.github/CODE_OF_CONDUCT.md': '/community/code-of-conduct/',
  '.github/SECURITY.md': '/community/security/',
  'MAINTAINERS.md': '/community/maintainers/',
  'fixtures/README.md': '/conformance/',
  'profiles/README.md': '/profiles/',
  'profiles/regulated/v0.1/README.md': '/profiles/regulated/v0.1/',
};

const read = (path) => readFileSync(new URL(path, root), 'utf8');

function write(slug, title, body, { source, order, description } = {}) {
  const front = [
    '---',
    `title: ${JSON.stringify(title)}`,
    ...(description ? [`description: ${JSON.stringify(description)}`] : []),
    `slug: ${slug}`,
    ...(source ? [`editUrl: ${JSON.stringify(`${repo}/edit/main/${source}`)}`] : []),
    ...(order !== undefined ? ['sidebar:', `  order: ${order}`] : []),
    '---',
    '',
  ].join('\n');
  const file = new URL(`${slug}.md`, docs);
  mkdirSync(new URL('.', file), { recursive: true });
  writeFileSync(file, `${front}${body.trim()}\n`);
}

// Rewrite relative links of a document at `source` to site pages or GitHub.
function links(markdown, source) {
  const base = new URL(source, 'file:///');
  return markdown.replace(/\]\((?!https?:|#|mailto:)([^)\s]+)\)/g, (_, target) => {
    const [path, anchor = ''] = target.split('#');
    const resolved = new URL(path, base).pathname.slice(1).replace(/\/$/, '');
    const page = pages[resolved] ?? pages[`${resolved}/README.md`];
    if (page) return `](${page}${anchor ? `#${anchor}` : ''})`;
    return `](${repo}/blob/main/${resolved}${anchor ? `#${anchor}` : ''})`;
  });
}

// A Markdown document whose first line is "# Title": title and body.
function titled(source) {
  const text = links(read(source), source);
  const [first, ...rest] = text.split('\n');
  return { title: first.replace(/^#\s+/, ''), body: rest.join('\n') };
}

// Headings one level up, so that a "##" section becomes a page with "##" subsections.
const promote = (body) => body.replace(/^###(#*) /gm, '##$1 ');

const slugify = (text) =>
  text.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');

function specification() {
  const lines = read(specFile)
    .split('\n')
    // The export dropped the section 5 diagram; the site draws it.
    .map((line) =>
      line.startsWith('&#91;embedded content: References checked by the integrity rules')
        ? '![The references that the integrity rules check: evidence points to a criterion, a test and a subject; test and subject name their producers; the test names its context.](/images/integrity-references.svg)'
        : line,
    );
  const sections = [];
  for (const line of lines.slice(1)) {
    if (line.startsWith('## ')) sections.push({ heading: line.slice(3).trim(), lines: [] });
    else if (sections.length) sections.at(-1).lines.push(line);
  }
  const intro = lines.slice(1, lines.findIndex((l) => l.startsWith('## '))).join('\n');

  const [status, ...rest] = sections;
  write(
    'specification',
    'Open Intent Schema Specification v0.1',
    `${intro.replace('@', '')}\n\n## ${status.heading}\n${promote(status.lines.join('\n'))}`,
    { source: specFile, order: 0, description: 'The OIS specification v0.1, working draft.' },
  );

  rest.forEach((section, index) => {
    const marking = /\((normative|informative)\)\s*$/.exec(section.heading)?.[1];
    const title = section.heading.replace(/\s*\((normative|informative)\)\s*$/, '');
    const name = title.replace(/^\d+\.\s*/, '').replace(/^Appendix ([A-Z]):\s*/, 'appendix $1 ');
    const note = marking ? `*This section is ${marking}.*\n\n` : '';
    write(`specification/${slugify(name)}`, title, note + promote(section.lines.join('\n')), {
      source: specFile,
      order: index + 1,
    });
  });
}

function community() {
  const docs = [
    ['GOVERNANCE.md', 'community/governance', 1],
    ['.github/CONTRIBUTING.md', 'community/contributing', 2],
    ['.github/CODE_OF_CONDUCT.md', 'community/code-of-conduct', 3],
    ['.github/SECURITY.md', 'community/security', 4],
    ['MAINTAINERS.md', 'community/maintainers', 5],
  ];
  for (const [source, slug, order] of docs) {
    const { title, body } = titled(source);
    write(slug, title, body, { source, order });
  }
}

function reference() {
  const fixtures = titled('fixtures/README.md');
  write('conformance', 'Conformance test suite', fixtures.body, {
    source: 'fixtures/README.md',
    description: 'Valid and invalid fixtures with the reports a validator must give.',
  });
  const registry = titled('profiles/README.md');
  write('profiles', 'Profiles', registry.body, { source: 'profiles/README.md' });
  const regulated = titled('profiles/regulated/v0.1/README.md');
  write('profiles/regulated/v0.1', regulated.title, regulated.body, {
    source: 'profiles/regulated/v0.1/README.md',
  });
}

for (const dir of ['specification', 'community', 'profiles', 'conformance']) {
  rmSync(new URL(dir, docs), { recursive: true, force: true });
  rmSync(new URL(`${dir}.md`, docs), { force: true });
}
specification();
community();
reference();
console.log('synced specification, community, conformance and profile pages');
