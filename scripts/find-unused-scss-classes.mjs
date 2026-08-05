#!/usr/bin/env node
// find-unused-scss-classes — report CSS-Module classes defined in *.module.{scss,css}
// that are never referenced in their colocated component.
//
// Model: CSS Modules are file-scoped — `X.module.scss` is imported (under some binding) only by
// its same-basename partner (`X.tsx/.ts/.jsx/.js`), so each pair is checked in isolation.
// Dynamic access (`binding[expr]`) can't be statically resolved → those files' unreferenced
// classes are UNVERIFIED (never deleted), not UNUSED. Confirmed-unused sets exit code 1.
//
// Usage:  node find-unused-scss-classes.mjs [rootDir]   (rootDir default: "src", else ".")
import { readFileSync, readdirSync, existsSync, statSync } from 'node:fs';
import { join, dirname, basename } from 'node:path';

const arg = process.argv[2];
const root = arg ?? (existsSync('src') ? 'src' : '.');
if (!existsSync(root) || !statSync(root).isDirectory()) {
  console.error(`find-unused-scss-classes: "${root}" is not a directory`);
  process.exit(2);
}

const SKIP = new Set(['node_modules', 'dist', 'build', '.git', 'coverage']);
function walk(dir) {
  return readdirSync(dir, { withFileTypes: true }).flatMap((e) => {
    if (e.name.startsWith('.') && e.name !== '.') return [];
    if (SKIP.has(e.name)) return [];
    const p = join(dir, e.name);
    return e.isDirectory() ? walk(p) : [p];
  });
}

// Class selectors: `.name`, excluding Sass namespace calls (`map.get`) and numbers.
function classesIn(scss) {
  const out = new Set();
  const re = /(^|[^\w\-.])\.(-?[a-zA-Z_][\w-]*)/g;
  let m;
  while ((m = re.exec(scss))) out.add(m[2]);
  return out;
}

// The local binding a stylesheet is imported under, e.g. `import styles from './X.module.scss'`.
function bindingFor(code, base) {
  const re = new RegExp(`import\\s+(\\w+)\\s+from\\s+['"\`][^'"\`]*${base}\\.module\\.(?:scss|css)['"\`]`);
  return code.match(re)?.[1] ?? null;
}

const files = walk(root);
const styleFiles = files.filter((f) => /\.module\.(scss|css)$/.test(f));
let unusedTotal = 0;
let checked = 0;

for (const stylePath of styleFiles) {
  const base = basename(stylePath).replace(/\.module\.(scss|css)$/, '');
  const partner = ['tsx', 'ts', 'jsx', 'js']
    .map((ext) => join(dirname(stylePath), `${base}.${ext}`))
    .find(existsSync);

  if (!partner) {
    console.log(`⚠ ${stylePath} — no colocated component (${base}.tsx/.ts/.jsx/.js), skipped`);
    continue;
  }
  checked++;

  const code = readFileSync(partner, 'utf8');
  const binding = bindingFor(code, base);
  if (!binding) {
    console.log(`⚠ ${stylePath} — couldn't find its import binding in ${partner}, skipped`);
    continue;
  }

  const classes = classesIn(readFileSync(stylePath, 'utf8'));
  const hasDynamic = new RegExp(`\\b${binding}\\[`).test(code);

  const used = new Set();
  const refRe = new RegExp(`\\b${binding}(?:\\.(-?[a-zA-Z_][\\w-]*)|\\[['"\`](-?[a-zA-Z_][\\w-]*)['"\`]\\])`, 'g');
  let m;
  while ((m = refRe.exec(code))) used.add(m[1] ?? m[2]);

  const orphans = [...classes].filter((c) => !used.has(c)).sort();
  if (!orphans.length) continue;

  if (hasDynamic) {
    console.log(`? ${stylePath} — UNVERIFIED (component uses dynamic ${binding}[…], can't confirm):`);
    for (const c of orphans) console.log(`    .${c}`);
  } else {
    console.log(`✗ ${stylePath} — UNUSED:`);
    for (const c of orphans) console.log(`    .${c}`);
    unusedTotal += orphans.length;
  }
}

console.log(
  unusedTotal
    ? `\n✗ ${unusedTotal} confirmed-unused class(es) across ${checked} module(s).`
    : `\n✓ No confirmed-unused classes across ${checked} module(s).`,
);
process.exit(unusedTotal ? 1 : 0);
