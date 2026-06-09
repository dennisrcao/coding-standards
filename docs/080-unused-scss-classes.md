```yaml
description: Detect unused CSS-Module classes with a zero-dep Node script (ecosystem tools are abandoned & break on ESLint 9/10)
globs:
  - "**/*.module.scss"
  - "**/*.module.css"
alwaysApply: false
```

# Unused CSS-Module classes

Companion to [010 Frontend SCSS](010-frontend-scss.md). The nesting rule keeps SCSS aligned
with JSX; this rule catches the classes that fall out of sync — defined in a `*.module.scss`
but never referenced in the component.

## Why a script, not a plugin or VS Code extension

We evaluated the real tools. They're all dead ends on a modern stack:

| Tool | Last shipped | Verdict on ESLint 9/10 |
|------|--------------|------------------------|
| `eslint-plugin-css-modules` (`no-unused-class`) | **2023** | Hard-crashes — `TypeError: context.getFilename is not a function` (calls an API ESLint removed in v9). Would only run if you *downgrade* ESLint. |
| `stylelint-no-unused-selectors` | **2022** | Abandoned; flaky with CSS Modules' dynamic access. |
| VS Code extensions (CSS Modules, etc.) | — | Editor-only, no commit/CI gate. **Can't squiggle an unused class** — the SCSS language server analyzes each stylesheet in isolation and has no idea which classes a `.tsx` consumes. |

The only editor-time signal available is the **opposite** direction: `typescript-plugin-css-modules`
types the `styles` object, so referencing a *missing* class (`styles.doesNotExist`) red-squiggles
in the `.tsx`. It does **not** flag an orphaned class in the `.scss`.

So: a zero-dependency Node script is the robust choice here — not a general preference for scripts,
but because the ecosystem for *this specific check* is unmaintained and incompatible with current
ESLint.

## How it works

CSS Modules are **file-scoped**: `X.module.scss` is imported by exactly its same-basename
partner (`X.tsx/.ts/.jsx/.js`), so each pair is checked in isolation. The script:

1. finds every `*.module.{scss,css}` under the root and extracts its class selectors (skipping
   Sass namespace calls like `map.get` and numeric `.5`);
2. finds the partner component and the **binding** it imports the stylesheet under (`import
   styles from …`, `import s from …` — not assumed to be `styles`);
3. collects every `binding.foo` / `binding['foo']` reference;
4. reports classes defined but never referenced.

**Dynamic access is the one trap, and it's handled conservatively.** `binding[expr]` (e.g.
``className={`${styles.chip} ${styles[tone]}`}``) can resolve to any class at runtime, so a
component using it can't be statically verified. Those files' otherwise-unreferenced classes are
reported `UNVERIFIED` (never deleted), not `UNUSED`. Only static-only files produce a
confirmed `UNUSED` finding and a non-zero exit code — safe to gate a hook or CI on.

## Adopt it in a repo

1. Drop the script at `scripts/find-unused-scss-classes.mjs` (or `ui/scripts/…` for a `ui/`
   workspace — see source below).
2. Add a script: `"lint:css": "node scripts/find-unused-scss-classes.mjs"` (pass a root dir as
   `$1`; defaults to `src`, falling back to `.`).
3. Optional gate: add `npm run lint:css` to the pre-commit hook or CI. It exits non-zero only on
   confirmed-unused classes, so `UNVERIFIED` won't block.
4. Optional editor visibility: a `tasks.json` problemMatcher can surface findings in the VS Code
   Problems panel (the closest thing to a squiggle for the orphan direction).

## Script

`scripts/find-unused-scss-classes.mjs` — zero dependencies, Node ≥ 18:

```js
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
```

## Limitations

- **Dynamic access blinds a whole file.** A component with any `binding[expr]` can hide a
  genuinely-dead class among its `UNVERIFIED` list (e.g. a `.safe` that no runtime value ever
  produces). Conservative by design — it never deletes — but means dynamic-heavy files need a
  human eye. Keep dynamic class names to a small, enumerable union type so review stays easy.
- **Cross-file class sharing isn't modelled.** If a repo deliberately imports one module's
  classes into another component, the pairing assumption breaks. Standard colocated CSS Modules
  don't do this.
- **Selectors only.** It checks class selectors, not custom properties, keyframes, or element
  selectors.
