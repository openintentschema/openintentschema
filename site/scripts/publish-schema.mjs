// Publish the JSON Schema at its versioned URL and fail if the copy differs from the source.
// The file under /schema/v0.1/ must always be exactly schema/ois.schema.json (RFC #6).
import { copyFileSync, mkdirSync, readFileSync } from 'node:fs';

const source = new URL('../../schema/ois.schema.json', import.meta.url);
const target = new URL('../dist/schema/v0.1/ois.schema.json', import.meta.url);

mkdirSync(new URL('.', target), { recursive: true });
copyFileSync(source, target);
if (!readFileSync(source).equals(readFileSync(target))) {
  console.error('published schema differs from schema/ois.schema.json');
  process.exit(1);
}
console.log('published schema/v0.1/ois.schema.json');
