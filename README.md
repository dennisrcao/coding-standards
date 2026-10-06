# Coding Standards

[![ci](https://github.com/dennisrcao/coding-standards/actions/workflows/ci.yml/badge.svg)](https://github.com/dennisrcao/coding-standards/actions/workflows/ci.yml)

A library of coding standards for React/TypeScript front ends, Python services and LLM
pipelines, written to be **copied into other repos** and read by people and coding agents
alike. Every standard is one Markdown file that becomes a Cursor rule and a Claude Code import
without edits.

Each rule carries its reason inline and a canonical code shape, and says where it came from:
the bug, the refactor or the review finding that earned it. A rule without a mechanism behind
it gets argued with instead of followed.

**Start here:**

- [`docs/README.md`](docs/README.md) — the index, every standard in one table
- [`docs/llm/101-llm-adoption-order.md`](docs/llm/101-llm-adoption-order.md) — which agent/LLM
  rules a new project needs on day one, and which wait for a named event
- [`docs/frontend/020-zustand.md`](docs/frontend/020-zustand.md) — the template every other
  standard follows: an upstream source, what is derived, what is deliberately narrower
- [Adopting a standard into a target repo](#adopting-a-standard-into-a-target-repo)

`npm ci && npm run check && npm test` checks that every standard carries the frontmatter its
`.mdc` copy needs, that every relative link resolves, and runs the fixtures for the one custom
ESLint rule the standards depend on. CI runs the same three.

## Origins

These started as a few lines of personal preferences in a Cursor rules file in June 2025
([`d05ef07`](https://github.com/dennisrcao/coding-standards/commit/d05ef07)). In April 2026 they
became the first portable rules: FastAPI, SCSS modules and Zustand
([`4686cc6`](https://github.com/dennisrcao/coding-standards/commit/4686cc6)). From June 2026
they grew into this library inside my docs hub, while I applied them across several
production codebases: a React/NestJS monorepo with Python LLM agents, a personal dashboard, and
a portfolio site. Most rules here exist because one of those codebases needed them. In
October 2026 the library moved out of the hub into this repo, with its history and with names
specific to those codebases replaced by generic ones.

## Single source of truth

`docs/<category>/<NNN>-<slug>.md` is the **only** canonical copy of a
standard. Categories on disk:

| Folder | Prefix band |
|---|---|
| `docs/general/` | `001` |
| `docs/backend/` | `005` (FastAPI / Python) |
| `docs/frontend/` | `010`–`029`, plus `040` (hotkeys) and `080` |
| `docs/tooling/` | `030`–`039` (lint / format), plus `050` (anti-slop / Fallow) |
| `docs/workflow/` | `060`–`099` (Playwright MCP, tmux, slash commands) |
| `docs/llm/` | `100`–`140` adoptable rules; `150`+ reference guides |

Index: [`docs/README.md`](docs/README.md). **Adoption profiles:**
[`standards-adoption.yaml`](standards-adoption.yaml). **Downstream lock file template:**
[`standards.lock.yaml.example`](standards.lock.yaml.example).

- **Do not** keep a second copy of a standard inside this repo (no mirrored `.mdc` under
  `.cursor/rules/`). Two files drift, and nothing checks that they agree.
- Copies live in **target repos**, where they are expected to diverge slightly — globs get
  rewritten for that repo's layout.
- If a rule needs changing, change it here and re-copy outward. Never edit a downstream copy
  and hope it flows back.


## The consumer is Claude Code *or* Cursor — one file serves both

Assume the reader uses either. Both tools load the same `.mdc` file in the target repo:

| Tool | How it loads the rule |
|------|----------------------|
| **Cursor** | auto-discovers `.cursor/rules/*.mdc` as Project Rules, matched by `globs` |
| **Claude Code** | `CLAUDE.md` `@`-imports the same file: `@.cursor/rules/020-zustand.mdc` |

This is why every doc in `docs/` **opens with a fenced `yaml` block carrying exactly Cursor's
frontmatter fields** (`description`, `globs`, `alwaysApply`). That block is not decoration — it
is the frontmatter of the file this doc becomes.

## Adopting a standard into a target repo

1. Pick a profile in [`standards-adoption.yaml`](standards-adoption.yaml) (or list rule IDs by
   hand). Skip `adoptable: false` entries — workflow operator docs and `150` stay hub-only.
2. Copy `docs/<category>/<NNN>-<slug>.md` → `<repo>/.cursor/rules/<NNN>-<slug>.mdc` — **except
   `030`** (see step 5).
3. Swap the opening ` ```yaml ` fence for `---` frontmatter (drop the closing fence too).
4. **Rewrite `globs` for that repo's layout.** The library assumes `apps/web/src/…`; a flat repo
   needs `src/…`. A rule whose globs don't match is a rule that never fires.
5. **Rule `030` — two hub files, one target `.mdc`:**
   - **Reference / Fallow setup:** `docs/tooling/030-lint-format-quality.md` (this library).
   - **Copy to target repo:** `rules/030-formatting.mdc` →
     `<repo>/.cursor/rules/030-formatting.mdc` **whole**. Do not rename the `.md` or trim the
     hook-deps and parameter-list sections — ESLint only lints imports; the `.mdc` carries the
     rest for agents.
   - Also copy `eslint-rules/packed-named-imports.mjs` into the target
     repo and wire it in `eslint.config.mjs`.
6. Trim other rules to what that repo needs — a downstream copy may be a narrow extract, not the
   whole doc.
7. Add `@.cursor/rules/<NNN>-<slug>.mdc` to the repo's `CLAUDE.md` so Claude reads it too, and
   note in `CLAUDE.md` that the canonical copy lives here. For `030`, `@`-import
   `030-formatting.mdc`.
8. Copy [`standards.lock.yaml.example`](standards.lock.yaml.example) → `<repo>/standards.lock.yaml`
   and fill in `hub_commit`, `profile`, `adopted`, `skip`, and `exceptions`. For `030`, record
   both `hub_doc` and `mdc` (see the example).

A typical adoption: pick three rules (e.g. SCSS nesting, Zustand selectors, packed imports),
flatten globs to the target's `src/…` layout, copy the `.mdc` files into `.cursor/rules/`, and
`@`-import them at the bottom of the repo's `CLAUDE.md` or `AGENTS.md`.

## Writing a new standard

- **Numbering** — `001` general, `005` backend, `010`–`029` / `040` / `080` frontend,
  `030`–`039` + `050` tooling & quality, `060`–`099` workflow (operator/agent machine),
  `100`–`140` adoptable LLM/agent rules, `150`+ reference guides (not copied to `.mdc`).
  Leave gaps; standards get inserted between.
- **Shape** — fenced `yaml` frontmatter block → `# Title (scope)` → **Do** / **Don't** →
  `## Canonical shape` with real code. Rules carry their reason inline; a rule without a
  rationale gets argued with instead of followed.
- **Keep adoptable docs portable.** Adoptable standards (`adoptable: true` in
  `standards-adoption.yaml`) must not name a specific repo, checkout path, or production file.
  Ground the rule in the *mechanism* — what failed, what pattern fixed it — and show it with
  **generic snippets** (`@/api/todos/queries.ts`, fictional module names). Repo-specific war
  stories belong in workflow/operator docs (`adoptable: false`) or in this hub's archive/research,
  not in a file downstream repos copy.
- **Precedence is per claim, never per repo.** `020-zustand.md` is the pattern to copy: name an
  upstream source of truth, then a three-way table saying which parts are *derived from* it,
  which are *deliberately narrower*, and which are *downstream* of a silent or stale upstream —
  plus the **Documented divergence** clause for a target repo that legitimately disagrees. Do not
  rank source repositories by reputation; a rule wins on mechanism, not on where it came from.
- **Cross-link** rather than restate — e.g. `020-zustand.md` points at `025-tanstack-query.md`
  for the server/client-state boundary instead of duplicating it.

### The `100`+ band — start with `101`

The agent/LLM band is eight docs, and **a new project should not import all of them.** Several
solve problems a greenfield codebase does not have yet, and adopting them early builds the
speculative infrastructure `125` itself warns against.

[`101-llm-adoption-order.md`](docs/llm/101-llm-adoption-order.md) is the entry point: it goes doc by
doc saying which rules are **in force on day one** and which are **trigger-gated**, each with a
checkable event rather than a feeling. It also asks the gate question the four source codebases
could not — *do you need an agent at all?* — because if there is no tool loop you don't control,
`125` and `130` never apply. Copy `101` into a target repo alongside the rules and `@`-import it
first.

### The `100`+ band — what it does not yet cover

The band's seven rule docs (`100` · `105` · `110` · `120` · `125` · `130` · `140`, sequenced by
`101`) are not the whole domain. These
are deliberately **out of scope** and are named here so nobody infers the band is complete:

| Gap | Why deferred |
|---|---|
| **Cost & rate-limit budgets** — per-job/tenant spend caps, what to do at the cap | `110`'s token-headroom rule is a truncation alarm and says so; money is a separate concern |
| **Data retention / PII / provider training opt-out** | an *adoption* gate for a repo handling customer data, not a library-ship gate |
| **Provider abstraction & model routing** | pinning is in `100`; a routing layer is its own doc |
| **Human-in-the-loop beyond `105`'s confirmation seam** | the seam exists; the workflow around it does not |
| **Concurrency, cancellation, streaming retry** | health under concurrent in-flight calls is undefined today |
| **Multi-tenant cache isolation** | `120`'s cache rules assume one tenant per conversation |

## What else lives here

| Path | What it is |
|------|-----------|
| `docs/` | the standards — canonical, portable |
| `standards-adoption.yaml` | machine-readable profiles — which rule IDs to copy for each repo shape |
| `standards.lock.yaml.example` | template for a target repo's adoption record (commit, profile, skips) |
| `commands/` | slash commands and agent skills for Claude Code and Cursor (`/ship`, `/close-out`, `/argue`, `/tdd`, `/code-review`, …) — the workflow side of the standards. They assume a docs hub that holds plans and tickets, and a monorepo with staging and production; treat them as worked examples to adapt |
| `docs/workflow/090-slash-commands.md` | how to write one, and the full roster with which agents get it |
| `docs/workflow/091-slash-commands-claude-vs-cursor.md` | the Claude Code vs Cursor split — which commands are one shared file, why `/ask` cannot be, what Cursor ignores in a shared file, and the verbatim source of `/close-out` and `/ask`. Generated by `scripts/build-slash-command-doc.py` |
| `eslint-rules/` | custom rules the standards depend on (`packed-named-imports.mjs` + test) |
| `rules/` | `.mdc` files copied whole rather than generated from a doc (`030-formatting.mdc`) |
| `scripts/` | `check-docs.mjs` (the CI gate), tooling a standard calls for (`find-unused-scss-classes.mjs`), plus `build-slash-command-doc.py` (regenerates `docs/workflow/091` from the live files), `link-slash-commands.sh` (points a fresh Mac's Claude Code + Cursor at `commands/` + `gh-stack-alias` on PATH), and `gh-stack-alias.sh` (wraps `gh stack submit` when `origin` is a `github-work` SSH alias) |

Those are copied outward the same way: the standard that needs them says so, and names the file.
