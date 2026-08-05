```yaml
description: JS/TS lint + format + repo-quality baseline — ESLint 9 flat config with @stylistic (no Prettier), and Fallow for dead-code / duplication / PR-risk gating
globs:
  - "**/eslint.config.{js,mjs,cjs}"
  - "apps/web/**/*.{ts,tsx}"
  - "**/.fallowrc.{json,jsonc}"
alwaysApply: false
```

# Lint, format & repo quality (JS/TS)

The baseline tooling for any new JS/TS project (or workspace in a monorepo). Two
layers, both runnable locally and in CI:

1. **ESLint (flat config) + `@stylistic`** — per-file lint **and** formatting. **No Prettier.**
2. **Fallow** — repo-level quality: dead code, duplication, complexity, dependency hygiene, PR-risk gate.

Python is the mirror image: **Ruff** does lint **and** format (see [`005-fastapi-python`](005-fastapi-python.md)). The principle is the same on both sides — **one tool owns both lint and format**, no second formatter.

---

## 1. ESLint — flat config, type-aware, no Prettier

### Why no Prettier

Formatting lives **inside ESLint** via [`@stylistic/eslint-plugin`](https://eslint.style). `@stylistic` exists precisely so you can format with ESLint and drop Prettier — one tool, one config, one command, one pass. Adding Prettier on top reintroduces the rule conflicts and double-tooling that `@stylistic` was built to remove.

**Do not add Prettier** (`prettier`, `.prettierrc`, `eslint-config-prettier`, `eslint-plugin-prettier`) to a new project. If a formatting rule is missing, add the corresponding `@stylistic/*` rule.

### The stack

ESLint **9** flat config (`eslint.config.mjs`), composed with `typescript-eslint`:

- `@eslint/js` → `eslint.configs.recommended`
- `typescript-eslint` → `...tseslint.configs.recommended`, type-aware via `parserOptions.projectService: true` + `tsconfigRootDir`
- `@stylistic/eslint-plugin` → formatting rules under the `@stylistic/*` namespace
- `{ ignores: ['dist/**'] }` for build output

Reference implementation: [`apps/web/eslint.config.mjs`](../../storyboard-agent/) in storyboard-agent:

```js
import eslint from '@eslint/js';
import stylistic from '@stylistic/eslint-plugin';
import tseslint from 'typescript-eslint';

export default tseslint.config(
  { ignores: ['dist/**'] },
  eslint.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: ['src/**/*.{ts,tsx}'],
    plugins: { '@stylistic': stylistic },
    languageOptions: {
      parserOptions: {
        projectService: true,
        tsconfigRootDir: import.meta.dirname,
      },
    },
    rules: {
      '@stylistic/object-curly-newline': [
        'error',
        { ImportDeclaration: 'never', ExportDeclaration: 'never' },
      ],
    },
  },
);
```

### Where the config lives

**Per package, not at the repo root.** In a monorepo, each JS/TS workspace owns its
own `eslint.config.mjs` next to its `tsconfig` so type-aware linting resolves the right
project. The lint **script** stays local (`"lint": "eslint src"`) and an orchestrator
runs it across workspaces — in storyboard-agent that's Nx (`nx lint` / `nx run-many -t lint`).
A standalone (non-monorepo) project just keeps the single config and the `eslint src` script.

### New-project checklist

- [ ] `pnpm add -D eslint @eslint/js typescript-eslint @stylistic/eslint-plugin`
- [ ] `eslint.config.mjs` per package, modelled on the snippet above
- [ ] `"lint": "eslint src"` in that package's `package.json`
- [ ] **No Prettier**, no `eslint-config-prettier` — `@stylistic` owns formatting
- [ ] Ignore build output (`dist/**`)

### Packed named imports (no one-name-per-line)

**Do not** break named imports Prettier-style — one specifier per line. Keep imports
**compact**: multiple names on one line when they fit; when wrapping, **pack** each
continued line with as many names as fit under the line-length budget.

This is the opposite of Prettier's default multiline import style and is intentional:
dense import blocks scan faster and diff more cleanly.

**Line-length budget:** pick one per repo and stick to it — **120** in the studio app
v2 (`apps/studio`), **150** elsewhere unless a project doc says otherwise.

```ts
// GOOD — single line when it fits
import { useCallback, useEffect, useMemo, useRef } from "react";
import { Aperture, Archive, Boxes, FileTextIcon, FolderIcon, Home } from "lucide-react";

// GOOD — wrapped, but still packed (not one name per line)
import {
  Aperture, Archive, Boxes, FileTextIcon, FolderIcon, Home, LayoutGrid,
  Settings, Clapperboard, ShieldCheck, Building2, Undo2,
} from "lucide-react";

// BAD — gratuitous one-name-per-line (Prettier-style)
import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
} from "react";
```

**Pair with `@stylistic/object-curly-newline`** so ESLint does not force imports onto
multiple lines prematurely:

```js
'@stylistic/object-curly-newline': [
  'error',
  { ImportDeclaration: 'never', ExportDeclaration: 'never' },
],
```

**Enforcement in app-monorepo:** custom ESLint rule `local/packed-named-imports`
in `apps/studio/eslint-rules/packed-named-imports.mjs`, enabled for
`src/components/v2/**/*.{ts,tsx}` via `apps/studio/eslint.config.mjs`. It errors on
one-specifier-per-line wrapped imports and auto-fixes by repacking. Documented in
`apps/studio/AGENTS.md` → *Lint and format*.

**Adopt in a new repo:**

1. Copy the rule module (or reimplement the same check).
2. Register it in `eslint.config.mjs` for the TS/TSX trees you care about.
3. Add the good/bad examples above to that package's `AGENTS.md` or a local
   `.cursor/rules/030-formatting.mdc` so agents and reviewers see the same bar.

Cursor rule template: [`.cursor/rules/030-formatting.mdc`](../../../.cursor/rules/030-formatting.mdc)
(relative from this doc — lives at the `docs-hub` repo root).

---

## 2. Fallow — repo-quality baseline & PR gate

[Fallow](https://github.com/fallow-rs/fallow) is a Rust-native static-analysis engine for
JS/TS repos. ESLint catches per-file issues; Fallow catches the **repo-level** ones ESLint
can't see: unreferenced files/exports, unused dependencies, cross-file duplication,
complexity hotspots, and architectural-boundary violations — and gates PRs on the **changed**
code.

> The install/config below is the baseline. For the **anti-slop policy** — advisory
> vs blocking gates, `--gate new-only`, and how to tune `.fallowrc.json` so the gate
> stays useful — see [`050-anti-slop`](050-anti-slop.md).

### Install

```bash
pnpm add -Dw fallow      # -w for the workspace root in a monorepo
npx fallow init          # auto-detects package manager + workspaces, writes .fallowrc.json
```

`fallow init` writes a `.fallowrc.json` and adds `.fallow/` to `.gitignore`. Tune it:

- **`entry`** — real reachability roots so dead-code detection is accurate. For a Vite app
  that's `src/main.tsx` (+ `vite.config.ts`, `index.html`), **not** the default `src/index.js`.
- **`workspaces.packages`** — narrow to the JS/TS packages only.
- **`ignorePatterns`** — exclude non-JS workspaces (e.g. a Python `apps/api/**`) so workspace
  discovery doesn't warn on them.

### npm scripts

```jsonc
{
  "fallow": "fallow",
  "fallow:audit": "fallow audit --base main",   // changed-code PR gate
  "fallow:health": "fallow health --score",      // 0–100 project health
  "fallow:dead-code": "fallow dead-code"
}
```

### CI gate (GitHub Actions)

`audit` exits non-zero on a `fail` verdict, so it gates PRs. Needs full history to diff
against the base branch:

```yaml
name: Fallow — PR audit
on:
  pull_request:
    types: [opened, synchronize, reopened]
permissions:
  contents: read
  pull-requests: write
jobs:
  audit:
    runs-on: ubuntu-latest
    if: github.event.pull_request.head.repo.full_name == github.repository
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - uses: fallow-rs/fallow@v2
        with:
          command: audit
          comment: true
          review-comments: true
```

### Suppressing findings

```ts
// fallow-ignore-next-line unused-export
export const keepThis = 1;
```

### New-project checklist

- [ ] `pnpm add -Dw fallow && npx fallow init`
- [ ] Fix `entry` to the real app entry point(s); narrow `workspaces`; `ignorePatterns` for non-JS dirs
- [ ] `fallow:audit` / `fallow:health` scripts
- [ ] `.github/workflows/fallow.yml` PR gate (no secrets needed — uses `GITHUB_TOKEN`)
- [ ] Record the baseline `fallow health --score` so regressions are visible
