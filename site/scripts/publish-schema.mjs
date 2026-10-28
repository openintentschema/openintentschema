// Publish the JSON Schema at the URL its own $id names, so that every version lives at its own
// path (/schema/v0.1/, later /schema/v0.2/, ...) and a new version never overwrites an old one.
// While the $id is still a placeholder outside openintentschema.io (RFC #6), nothing is
// published: a versioned URL must not serve content that will change.
import { copyFileSync, mkdirSync, readFileSync } from 'node:fs';

const source = new URL('../../schema/ois.schema.json', import.meta.url);
const { $id } = JSON.parse(readFileSync(source, 'utf8'));
const match = /^https:\/\/openintentschema\.io\/(schema\/v[0-9][^/]*\/ois\.schema\.json)$/.exec($id);

if (!match) {
  console.log(`schema $id ${$id} is not under openintentschema.io yet; not published`);
  process.exit(0);
}

const target = new URL(`../dist/${match[1]}`, import.meta.url);
mkdirSync(new URL('.', target), { recursive: true });
copyFileSync(source, target);
if (!readFileSync(source).equals(readFileSync(target))) {
  console.error(`published ${match[1]} differs from schema/ois.schema.json`);
  process.exit(1);
}
console.log(`published ${match[1]}`);
