import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile, readdir } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { fileURLToPath } from 'node:url';
import { join, relative } from 'node:path';
import { useCases } from '../src/content.js';

const output = new URL('../dist/', import.meta.url);
const html = await readFile(new URL('index.html', output), 'utf8');
const ids = [...html.matchAll(/\bid="([^"]+)"/g)].map(match => match[1]);
const links = [...html.matchAll(/\b(?:href|src)="([^"]+)"/g)].map(match => match[1]);
const localFiles = [...new Set(links.filter(link => !link.startsWith('#') && !link.startsWith('https://')))];

test('every local asset, reference and disclosure anchor resolves', async () => {
  assert.equal(new Set(ids).size, ids.length, 'Duplicate IDs');
  for (const link of [...links.filter(link => link.startsWith('#')), ...useCases.map(row => row.link)]) assert.ok(ids.includes(link.slice(1)), link);
  for (const link of localFiles) {
    assert.ok(link.startsWith('./'), `Non-portable path: ${link}`);
    await readFile(new URL(link, output));
  }
});
test('the exact output inventory is covered by SHA-256, without a circular manifest digest', async () => {
  const manifest = JSON.parse(await readFile(new URL('manifest.json', output), 'utf8'));
  const all = await readdir(output, { recursive: true, withFileTypes: true });
  const names = all.filter(entry => entry.isFile()).map(entry => relative(fileURLToPath(output), join(entry.parentPath, entry.name)).split('\\').join('/'));
  assert.deepEqual(names.sort(), [...Object.keys(manifest), 'manifest.json'].sort());
  for (const [path, digest] of Object.entries(manifest)) assert.equal(createHash('sha256').update(await readFile(new URL(path, output))).digest('hex'), digest, path);
  assert.ok(Object.hasOwn(manifest, '.nojekyll'));
});
test('the comparison data and query recipes are verbatim source copies', async () => {
  const data = JSON.parse(await readFile(new URL('data.json', output), 'utf8'));
  const fixture = await readFile(new URL('../../examples/multidimensional-analysis/scalogram.json', import.meta.url), 'utf8');
  assert.deepEqual(data.comparison, JSON.parse(fixture));
  for (const name of ['double-bass.sql', 'double-bass.rq', 'arco-context.json']) assert.equal(await readFile(new URL(`reference/${name}`, output), 'utf8'), await readFile(new URL(`../../examples/queries/${name}`, import.meta.url), 'utf8'));
});
test('the app has no remote runtime assets, trackers or backend dependency', async () => {
  for (const match of html.matchAll(/<(?:script|link|img)\b[^>]*(?:src|href)="([^"]+)"/g)) assert.ok(match[1].startsWith('./'), match[1]);
  const app = await readFile(new URL('app.js', output), 'utf8');
  assert.doesNotMatch(app, /https?:\/\/|localStorage|sessionStorage/);
  assert.doesNotMatch(await readFile(new URL('styles.css', output), 'utf8'), /@import|https?:\/\//);
  assert.match(html, /<noscript>/);
  assert.match(html, /class="skip-link"/);
});

async function startServer(base) {
  const child = spawn(process.execPath, [fileURLToPath(new URL('../scripts/serve.mjs', import.meta.url))], { env: { ...process.env, PORT: '0', OMARO_BASE_PATH: base }, stdio: ['ignore', 'pipe', 'pipe'] });
  const address = await new Promise((resolve, reject) => {
    const timer = setTimeout(() => { child.kill(); reject(new Error('Preview server did not start')); }, 5000);
    child.once('error', error => { clearTimeout(timer); reject(error); });
    child.stdout.on('data', chunk => {
      const match = chunk.toString().match(/Local: (http:\/\/\S+)/);
      if (match) { clearTimeout(timer); resolve(match[1]); }
    });
    child.once('exit', code => { clearTimeout(timer); reject(new Error(`Server exited: ${code}`)); });
  });
  return { child, address };
}
for (const base of ['/', '/a-project/field-guide/']) {
  test(`all static requests work under ${base}`, async () => {
    const { child, address } = await startServer(base);
    try {
      assert.equal((await fetch(address)).status, 200);
      for (const path of [...localFiles, './data.json', './model.js', './content.js']) assert.equal((await fetch(new URL(path, address))).status, 200, path);
      assert.equal((await fetch(new URL('./not-a-route', address))).status, 404);
      assert.equal((await fetch(new URL('./data.json', address), { method: 'POST' })).status, 405);
      assert.equal((await fetch(new URL('../package.json', address))).status, 404);
    } finally {
      const exited = once(child, 'exit');
      child.kill();
      await exited;
    }
  });
}
