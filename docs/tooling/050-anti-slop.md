```yaml
description: Anti-slop policy — Fallow as the repo-level gate against AI-generated dead code, duplication, complexity and dependency cruft. Adopt advisory (new-only) first, graduate to blocking. Pairs with 030 lint/format baseline.
globs:
  - "**/.fallowrc.{json,jsonc}"
  - "**/.github/workflows/*fallow*.{yml,yaml}"
  - "**/.github/workflows/ci.{yml,yaml}"
alwaysApply: false
```

# Anti-slop (Fallow)

**Slop** is plausible-looking code that nobody needs: dead exports and files no
one imports, the same block copy-pasted across five components, functions that
balloon in complexity, dependencies pulled in and never used. It is the natural
exhaust of fast, AI-assisted development — every generated file *looks* finished,
so the cruft accumulates silently and no single diff looks wrong.

ESLint and Ruff catch **per-file** problems. They cannot see slop, because slop is
a **repo-level, cross-file** property: a file is only dead relative to the whole
import graph; a clone only exists relative to its copies. That gap is what
[**Fallow**](https://github.com/fallow-rs/fallow) closes, and it's why anti-slop
is its own standard rather than a lint rule.

> Base install, `.fallowrc.json` anatomy, and the ESLint half of the baseline live
> in [`030-lint-format-quality`](030-lint-format-quality.md). This doc is the
> **policy**: how we run Fallow as a PR gate and how we tune it.

---

## What Fallow flags as slop

| Finding | The slop it catches |
|---|---|
| `unused-files` | Modules nothing imports — orphaned by a refactor or generated and forgotten |
| `unused-exports` / `unused-types` | Exported symbols with no consumer |
| `unused-dependencies` | `package.json` deps nothing references |
| Duplication | The same logic copy-pasted across N sites instead of shared |
| Complexity (cyclomatic / cognitive / CRAP) | Functions too branchy to safely change |

It scores all of this against the **changed** code in a PR, so the gate is about
*new* slop, not the whole backlog.

---

## Two gate strategies (pick by repo maturity)

Run Fallow two ways in practice. **Adopt advisory first; graduate to blocking once a repo's
new-code findings are reliably clean.**

### 1. Advisory `deslop` — new-only, never blocks

The CI job is often named `deslop`. On every PR touching the frontend it audits the changed files
and posts a **sticky bot comment** splitting *new* vs *inherited* findings — but it **never fails the
check**. This is the right entry point for a repo that already carries a backlog: you get the signal
without blocking feature work.

```yaml
deslop:
  if: github.event_name == 'pull_request'
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
      with: { fetch-depth: 0 }                 # full history → new-vs-inherited attribution
    - run: git fetch --no-tags origin "+refs/heads/${{ github.base_ref }}:refs/remotes/origin/${{ github.base_ref }}"
    - uses: actions/setup-node@v4
      with: { node-version: "22" }
    - run: npm ci
    - name: fallow audit
      id: audit
      run: |
        set +e
        npx fallow audit --base "origin/${{ github.base_ref }}" --gate new-only \
          --format pr-comment-github > "$RUNNER_TEMP/fallow-report.md"
        echo "exit_code=$?" >> "$GITHUB_OUTPUT"
    # …then post $RUNNER_TEMP/fallow-report.md as a sticky comment keyed by a
    #   <!-- fallow-id: fallow-results --> marker (upsert, don't spam).
```

The two flags that make it advisory and scoped:

- **`--gate new-only`** — only *new* findings count toward the verdict; inherited
  backlog is reported but never gates.
- The job **doesn't** `exit 1` on `steps.audit.outputs.exit_code`. To make it
  blocking later, add a final step that exits non-zero on that output.

### 2. Blocking audit — gates the PR

The audit **exits 1 on a `fail` verdict**, posts a PR comment **and inline review comments**, and is
scoped to the changed files by `.fallowrc.json` at the root. Forks are skipped so a write-scoped
token never runs on untrusted PRs.

```yaml
# .github/workflows/fallow.yml
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

No secrets — both modes use the default `GITHUB_TOKEN`.

---

## Deslop your own diff first

Don't let CI be the first time you see your slop. Before you push, gate locally
against the same base the PR will use:

```bash
fallow audit --base main      # changed-code verdict (add --gate new-only to match advisory CI)
fallow health --score         # 0–100 project health; record the baseline so regressions are visible
fallow dead-code              # just the unreferenced files/exports
```

Wire them as scripts so they're one keystroke:

```jsonc
{
  "fallow": "fallow",
  "fallow:audit": "fallow audit --base main",
  "fallow:health": "fallow health --score",
  "fallow:dead-code": "fallow dead-code"
}
```

Suppress a deliberate exception inline (use it sparingly — each one is debt):

```ts
// fallow-ignore-next-line unused-export
export const keepThis = 1;
```

---

## Tuning `.fallowrc.json` (don't fight the tool — configure it)

A noisy gate gets ignored, which is worse than no gate. Every override below is load-bearing and
should carry a comment saying **why** (jsonc comments are fine):

- **`ignoreDependencies`** — deps Fallow genuinely can't see are *used*, e.g. a build-tool plugin
  invoked by a non-JS executor, or `tslib` emitted by tsc under `importHelpers: true`. Without this,
  real deps get flagged as unused. Don't silence findings you could fix — only the ones the analysis
  structurally can't see.
- **`duplicates.minOccurrences`** — raise it (e.g. `4`) so 3-site boilerplate that's cheaper to
  leave inline isn't flagged. Abstract clones when they're *widely* copied, not on the second paste.
- **`health` thresholds** — keep `maxCyclomatic` / `maxCognitive` near defaults so the gate catches
  genuinely branchy functions. **Watch `maxCrap`:** with no coverage data fed in, CRAP collapses to
  `cyclomatic² + cyclomatic`, so the default trips on ordinary p90 functions — raise it (e.g. `120`)
  so it only catches genuinely high-risk code, and lean on the cyclomatic/cognitive gates instead.
- **`rules` as `warn`** — set `unused-exports`/`unused-types`/`unused-files` to
  `warn` so a feature PR that merely *touches* a file with a pre-existing unused
  export isn't hard-failed. Dead code is signal, not a blocker on unrelated work.
- **`entry`** — point at the *real* reachability roots (a Vite app:
  `src/main.tsx`, `vite.config.ts`, `index.html`), or dead-code detection is wrong.

---

## Adoption checklist

- [ ] `pnpm add -Dw fallow && npx fallow init` (see [`030`](030-lint-format-quality.md) for the base setup)
- [ ] Tune `.fallowrc.json` — fix `entry`, narrow `workspaces`, add `ignoreDependencies` / `ignorePatterns`, set the `health`/`duplicates` overrides above, each with a *why* comment
- [ ] Add `fallow:audit` / `fallow:health` / `fallow:dead-code` scripts
- [ ] Start **advisory**: a `deslop` CI job running `fallow audit --base origin/<base> --gate new-only` that posts a sticky comment and never blocks
- [ ] Record the baseline `fallow health --score`
- [ ] **Graduate to blocking** (`fallow-rs/fallow@v2`, `command: audit`, exit-1-on-fail) once new-code findings stay clean
