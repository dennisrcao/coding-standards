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
import { packedNamedImportsRule } from './eslint-rules/packed-named-imports.mjs';

export default tseslint.config(
  { ignores: ['dist/**'] },
  eslint.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: ['src/**/*.{ts,tsx}'],
    plugins: {
      '@stylistic': stylistic,
      local: { rules: { 'packed-named-imports': packedNamedImportsRule } },
    },
    languageOptions: {
      parserOptions: {
        projectService: true,
        tsconfigRootDir: import.meta.dirname,
      },
    },
    rules: {
      'local/packed-named-imports': ['error', { maxLineLength: 150 }],
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

### Pack, don't stack — imports, hook deps, parameter lists

**One rule, three places.** Named imports, React hook dependency arrays, and function /
component parameter lists all follow the same form:

1. Keep the list on **one line** when it fits the 150-char budget. This is the common case —
   it should cover the large majority of every one of the three.
2. When it genuinely will not fit, **wrap and pack**: fill each continued line with as many
   entries as fit under the budget.
3. **Never one entry per line.** That is Prettier's default shape, and it is the one form
   this standard rejects.

This is deliberate, and it is the opposite of what an LLM will produce unprompted — the
training distribution is overwhelmingly Prettier-at-80 open-source React, so agents drift to
one-per-line in *all three* positions unless the repo says otherwise. Dense lists scan faster,
diff more cleanly, and a wrapped line can carry a **related set** rather than an arbitrary
slice.

> **The exception: JSX props stay one per line.** A JSX attribute is a `name={expression}`
> pair, often a multi-line arrow — packing those produces genuinely worse code. Keep the
> familiar one-attribute-per-line form for JSX. This section is about *identifier lists*
> (imports, deps, params), not JSX.

#### Named imports

**Line-length budget: 150.** One number, every repo — for this rule and for
`@stylistic/max-len` where that is enabled. There is deliberately **no per-repo escape hatch**;
the previous "pick one per repo" wording is what let claw-calendar pack at 120 while citing
the studio app v2, a repo it is not.

When a wrap is unavoidable, use the **brace-newline form**: `{` ends the `import` line, names
follow on 2-space-indented lines packed as densely as the budget allows, and `} from "…";`
closes on its own line. **Keep the trailing comma** — the closing brace sits on its own line,
so it reads cleanly.

Where the names have a natural grouping, put each group on its own line. That is the whole
reason this form wins: a line can carry a related set.

```ts
// GOOD — brace-newline, packed. Wrapped because 196 chars will not fit on one line.
import {
  isCancelledJobError, isWorkerRenderConfigured, workerAttachJob, workerCancelJob,
  workerFirstImageUrl, workerRenderMetaProduct, type WorkerMetaProductSuccess,
} from "@/lib/c4d/worker-api";

// BAD — the same import, one name per line. The only form the rule flags.
import {
  isCancelledJobError,
  isWorkerRenderConfigured,
  workerAttachJob,
  workerCancelJob,
  workerFirstImageUrl,
  workerRenderMetaProduct,
  type WorkerMetaProductSuccess,
} from "@/lib/c4d/worker-api";
```

A real example of the grouping paying off, from
`studio/src/components/LaunchControl/LaunchControlSheet.tsx` — geometry, knobs, buttons and
side cells each get a line:

```ts
import {
  PAGE, STYLE, mm, COL_CX, COL_W,
  KNOB_ROW_CY, KNOB, FADER_CX, FADER, FADER_TICK_YS,
  BTN_BOTTOM, BTN_BOTTOM_CELL_H, BTN_LABEL, BTN_CELL, SIDE_PAIR, SIDE_PAIR_CELL_W,
  SIDE_QUAD, SIDE_QUAD_CELL_H, SLOT_LABEL, OUTLINE,
} from '@/lib/launchcontrol/geometry.ts';
```

#### Hook dependency arrays

A `useMemo` / `useCallback` / `useEffect` dependency array is an identifier list, so it packs
the same way. In practice almost every dep array fits on one line and should stay there.

```ts
// GOOD — one line. The overwhelmingly common case.
}, [showSidePanel, mood, analyzing, imageCount, uploading, projectId]);

// GOOD — wrapped and packed, because 20 deps will not fit in 150 chars.
}, [
  showSidePanel, mood, analyzing, imageCount, uploading, projectId, savingBrief, briefSaved,
  fragments, savedPrompts, activeSessionId, handleAddPromptToShotlist, handleDeletePrompt,
  handleUpdateFragment, handleCreateFragment, handleDeleteFragment, handleMoodCommit,
]);

// BAD — one dependency per line.
}, [
  showSidePanel,
  mood,
  analyzing,
  imageCount,
]);
```

A dep array that needs three packed lines is also a **design signal**, not just a formatting
one: it usually means the component is doing several unrelated jobs and the memo should be
split. Pack it, then ask whether it wants extracting.

#### Function & component parameter lists

Same form. Keep the destructured props on the signature line when they fit; when they do not,
open the brace and pack the names.

```ts
// GOOD — fits on one line at 150, so it stays there.
function ImagesPage({ projectId, onBack, onSelectProducts, onNeedProject, returnToShotlist = false }: ImagesPageProps) {

// GOOD — wrapped and packed, trailing comma kept.
const AddNodeButton = ({
  disabled, i, nodeType, nodeDisplayName, onNodeCreateClick, tileId, onActivate,
}: IAddNodeButtonProps) => {

// GOOD — many destructured props (15+), still packed — not one name per line.
// Ground truth: collaborative-learning wraps long signatures the same way.
export function ConsoleButton({
  label, subLabel, variant = "idle", className, onClick, sfx, fieldView, fieldCamera,
  borderOuter, borderInner, showBackground = true, showBorderOuter = true, showBorderInner = true,
  behavior, pinBorderInner = false, pinBorderOuter = false,
}: ConsoleButtonProps) {

// GOOD — positional params, packed the same way.
function handleSocketKeyDown(
  e: React.KeyboardEvent<HTMLDivElement>, nodeId: string, socketKey: string,
  side: "input" | "output", reteManager: ReteManager,
) {

// BAD — one parameter per line. Prettier's default; what LLMs write unprompted.
function ImagesPage({
  projectId,
  onBack,
  onSelectProducts,
}: ImagesPageProps) {

// BAD — same mistake at scale. ESLint will not catch this; only this doc + the Cursor rule will.
export function ConsoleButton({
  label,
  subLabel,
  variant = "idle",
  className,
  onClick,
}: ConsoleButtonProps) {
```

Interface and type members are **not** covered — `interface Props { … }` keeps one member per
line, because each member carries its own type, optionality and doc comment.

##### For agents — the drift after import lint lands

Repos that adopt the ESLint rule often see imports fixed on the first pass, then **params and
hook deps stay Prettier-shaped forever** — because nothing autofixes them. When you write or
edit a function signature or hook dependency array:

1. **One line when it fits** under 150 chars (most small components).
2. **Wrap and pack** when it does not — multiple names per continued line, trailing comma before
   the closing `}` / `]`.
3. **Never one name per line** in destructuring, positional params, or dep arrays.

A clean `eslint` run proves **imports only**. Treat packed params and deps as part of the same
rule, not a separate style preference.

### `object-curly-newline` is deliberately NOT part of this standard

It used to be, with `ImportDeclaration: 'never'`. That setting forbids a line break straight
after `{` — which is precisely the brace-newline form above. Keeping it would make the house
style unlintable, so it is **removed from the standard entirely. Do not add it back.**

Its `ExportDeclaration` half was independently hazardous: the fixer only *deletes* newlines and
the packing rule covers imports alone, so on a repo with multi-line barrel files it yields
`export {useFoo,` … `type Bar,}`, and it cannot touch comment-interleaved export blocks at all.

**Enforcement (imports only):** custom ESLint rule, canonical at
[`../../eslint-rules/packed-named-imports.mjs`](../../eslint-rules/packed-named-imports.mjs). Copy
that file into the consuming repo's `eslint-rules/` and wire it as in the config above.

**Hook deps and parameter lists are not linted** — the rule covers `ImportDeclaration` only.
They are a **review-level and agent-level** expectation, carried by this doc and by the Cursor
rule template. A clean `eslint` run says nothing about them; a scoped rule that plugs only the
import hole is exactly how one-per-line leaks back into deps and params.

The rule reports **two** shapes, and autofixes both:

| Shape | Message | Fix |
|-------|---------|-----|
| Every specifier on its own line | `onePerLine` | repack into the brace-newline form |
| Wrapped at all, but the single-line form fits the budget | `fitsOnOneLine` | collapse to one line |

`fitsOnOneLine` exists because rule 1 of this standard is *one line when it fits* — a
gratuitous wrap violates it just as much as one-per-line does. It is also the shape that
**accumulates**, precisely because a linter looking only for one-per-line never sees it: in
`studio`, the first adoption pass found 9 one-per-line imports and **10** gratuitously wrapped
ones. Both counts are now enforced.

An import that genuinely exceeds the budget and is already packed — brace-newline or hanging —
is left alone, so adopting the rule in an existing repo still produces no mass reformat.

**Two things it deliberately will not do.** It skips any import with a comment inside the
braces, because both fixes rewrite the whole declaration from its specifier list and would
delete the comment. And above the budget it still cannot tell brace-newline from the *hanging*
form (`{` followed by names on the same line, continued at an indent), since both put two or
more names on a line — preferring brace-newline there stays a **review-level** call.

**Adopt in a new repo:**

1. Copy [`../../eslint-rules/packed-named-imports.mjs`](../../eslint-rules/packed-named-imports.mjs)
   into the repo's `eslint-rules/`. Copy the file — do not retype it.
2. Register it in `eslint.config.mjs` for the TS/TSX trees you care about, at
   `maxLineLength: 150`.
3. Copy [`.cursor/rules/030-formatting.mdc`](../../../../.cursor/rules/030-formatting.mdc) into
   the target repo **whole** — rewrite `globs` for that repo's layout, but **do not trim** the
   hook-deps or parameter-list sections. ESLint covers imports only; those sections are what
   keeps agents from writing Prettier-style signatures. Optionally `@`-import it from
   `CLAUDE.md` (see [`README.md`](../../README.md)).
4. Run `npx eslint .` once before committing. The rule reports only
   one-name-per-line imports, so a clean repo should stay clean; anything it does flag is
   real.

**Changing the rule:** edit the canonical file, then re-run its fixtures from a repo that has
`eslint` + `@typescript-eslint/parser` installed, and re-copy downstream:

```sh
cd ~/Desktop/studio
node ~/coding-standards/eslint-rules/packed-named-imports.test.mjs
```

Cursor rule template: [`.cursor/rules/030-formatting.mdc`](../../../../.cursor/rules/030-formatting.mdc)
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
