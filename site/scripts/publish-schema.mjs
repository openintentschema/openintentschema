// Publish the JSON Schema at the path its $id names (/schema/v0.1/, /schema/v0.2/, ...); a $id
// outside openintentschema.io is not published.
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
