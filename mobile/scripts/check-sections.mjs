// Every screen must be listed in exactly one section (or be a flow screen reached
// from another screen), and every route the app links to must exist.
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { SECTIONS, MORE, FLOW_SCREENS } from '../src/navigation/sections.ts';

const root = fileURLToPath(new URL('..', import.meta.url));
const screens = [join(root, 'app'), join(root, 'app', '(tabs)')]
  .flatMap((dir) => readdirSync(dir).filter((f) => f.endsWith('.tsx') && f !== '_layout.tsx'))
  .map((f) => f.replace(/\.tsx$/, ''));

const errors = [];
const tabs = [...SECTIONS.map((s) => (s.tab === '/' ? 'index' : s.tab.slice(1))), 'menu'];
const listed = [...tabs, ...[...SECTIONS.flatMap((s) => s.items), ...MORE].map((i) => i.route.slice(1))];
for (const name of screens) {
  const count = listed.filter((r) => r === name).length + (FLOW_SCREENS.includes(name) ? 1 : 0);
  if (count !== 1) errors.push(`${name}: listed ${count} times`);
}
for (const route of listed) if (!screens.includes(route)) errors.push(`${route}: listed but no screen`);

function walk(dir) {
  return readdirSync(dir).flatMap((f) => {
    const p = join(dir, f);
    if (statSync(p).isDirectory()) return walk(p);
    return /\.tsx?$/.test(f) ? [p] : [];
  });
}
const linkPattern = /(?:push|replace|navigate|href|route)\s*[(=:]\s*\{?\s*(?:pathname:\s*)?['"`](\/[a-z0-9\-/()]*)/g;
for (const file of [...walk(join(root, 'app')), ...walk(join(root, 'src'))]) {
  for (const [, link] of readFileSync(file, 'utf8').matchAll(linkPattern)) {
    const name = link.replace('/(tabs)', '').split('/').filter(Boolean)[0] ?? 'index';
    if (!screens.includes(name)) errors.push(`${file.slice(root.length)}: dead link ${link}`);
  }
}

if (errors.length) {
  console.error(errors.join('\n'));
  process.exit(1);
}
console.log(`sections: ${screens.length} screens, each reachable once; no dead links`);
