// Fails on any high or critical advisory in production dependencies, except
// the ones listed here: no patched release exists and docs/SECURITY.md says why.
import { execSync } from 'node:child_process';

const ACCEPTED = new Set([
  'GHSA-vfj7-8cjw-p6xm', // braces <=3.0.3, Metro's file watcher at build time
  'GHSA-86w9-cpqp-85rv', // node-forge <=1.4.0, Expo CLI code signing at build time
]);

let raw;
try {
  raw = execSync('npm audit --omit=dev --json', { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] });
} catch (err) {
  raw = err.stdout; // npm audit exits non-zero whenever it finds anything
}
const vulns = JSON.parse(raw).vulnerabilities ?? {};
const blocking = [];
for (const [name, v] of Object.entries(vulns)) {
  for (const via of v.via) {
    if (typeof via !== 'object' || !['high', 'critical'].includes(via.severity)) continue;
    const id = via.url.split('/').pop();
    if (!ACCEPTED.has(id)) blocking.push(`${name} ${via.severity} ${id} ${via.title}`);
  }
}
if (blocking.length) {
  console.error(blocking.join('\n'));
  process.exit(1);
}
console.log('npm audit: no unaccepted high or critical advisories');
