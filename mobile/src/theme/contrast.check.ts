// Run: node src/theme/contrast.check.ts
// WCAG 2.1 contrast of text tokens on the surfaces they sit on: 4.5:1 for body text, 3:1 for large text and icons.
import assert from 'node:assert/strict';

function lum(hex: string): number {
  const c = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255)
    .map((v) => (v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4));
  return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
}
export function ratio(a: string, b: string): number {
  const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p);
  return (x + 0.05) / (y + 0.05);
}

const themes = {
  dark: { bg: ['#0C111C', '#182031'], body: ['#F1F5F9', '#CBD5E1', '#9AA8BF'], large: ['#22C55E', '#EAB308', '#EF4444', '#818CF8'] },
  light: { bg: ['#F3F1EC', '#FBFAF7'], body: ['#25291F', '#585B4F', '#696C60'], large: ['#15803D', '#A16207', '#B91C1C'] },
};
const failures: string[] = [];
for (const [name, t] of Object.entries(themes)) {
  for (const bg of t.bg) {
    for (const fg of t.body) if (ratio(fg, bg) < 4.5) failures.push(`${name} body ${fg} on ${bg}: ${ratio(fg, bg).toFixed(2)}`);
    for (const fg of t.large) if (ratio(fg, bg) < 3) failures.push(`${name} large ${fg} on ${bg}: ${ratio(fg, bg).toFixed(2)}`);
  }
}
assert.deepEqual(failures, []);
