# Coding standards — index

**Status:** Reference

Portable rules copied into target repos as `.cursor/rules/<NNN>-<slug>.mdc`. Repo root
[`README.md`](../README.md) covers adoption; start LLM work at [`llm/101-llm-adoption-order.md`](llm/101-llm-adoption-order.md).

## Adoption profiles

**Machine-readable manifest:** [`../standards-adoption.yaml`](../standards-adoption.yaml)

Pick a profile (or compose `adopt` / `skip` by hand), copy each **adoptable** rule to the target
repo, rewrite globs, then record what landed in
[`standards.lock.yaml`](../standards.lock.yaml.example) (copy the example into the target repo).

| Profile | Adopt (rule IDs) | Notes |
|---|---|---|
| `baseline` | 001, 030 | Any repo |
| `react-spa` | 001, 010, 015, 020, 025, 026, 030, 040, 080 | Vite/CRA-style SPA |
| `react-spa-flat` | 001, 010, 020, 025, 026, 030, 040, 080 | Flat `src/` — skips 015 |
| `next-dashboard` | same as `react-spa` | Client Query + RSC fetch where documented |
| `next-rsc-fetch` | 001, 010, 015, 020, 030, 080 | No Query — skips 025, 026 |
| `python-api` | 001, 005, 030 | FastAPI backend |
| `agent-backend` | 001, 005, 030, 100, 101, 105, 110 | Model calls; read 101 first |
| `agent-conversational` | + 120, 125, 140 | Tool-loop agent — **not** 130 |
| `agent-job-pipeline` | + 120, 130, 140 | Invoke-once jobs — **not** 125 |
| `drag-and-drop` | 027 | Add when the repo has *positional* drag (coordinates → a value). Needs 026 |
| `quality-gate` | 050 | Add when Fallow / changed-code CI exists |
| `operator-machine` | *(reference only)* 060, 070, 090, 091 | Machine setup — not `.mdc` rules |

Rule IDs are the filename prefix (`020` → `docs/frontend/020-zustand.md`). **Exception — `030`:**
the full write-up is `docs/tooling/030-lint-format-quality.md`; copy
`docs-hub/.cursor/rules/030-formatting.mdc` whole into the target repo (not a rename of
the `.md`). Workflow docs and `150` are **reference-only** — read from the hub, do not copy to
`.cursor/rules/`.

## General

| Doc | Topic |
|---|---|
| [001-repository-rules.md](general/001-repository-rules.md) | Repo-wide conventions |

## Backend

| Doc | Topic |
|---|---|
| [005-fastapi-python.md](backend/005-fastapi-python.md) | FastAPI / Python (Ruff, async, Pydantic v2) |

## Frontend

| Doc | Topic |
|---|---|
| [010-frontend-scss.md](frontend/010-frontend-scss.md) | SCSS modules — nesting mirrors JSX |
| [015-frontend-folder-organization.md](frontend/015-frontend-folder-organization.md) | Folder layout |
| [020-zustand.md](frontend/020-zustand.md) | Zustand — selector-first stores |
| [025-tanstack-query.md](frontend/025-tanstack-query.md) | TanStack Query — server state |
| [026-optimistic-updates.md](frontend/026-optimistic-updates.md) | Optimistic updates |
| [027-drag-and-drop.md](frontend/027-drag-and-drop.md) | Positional drag and drop — one resolver for preview + write |
| [040-keyboard-shortcuts.md](frontend/040-keyboard-shortcuts.md) | Keyboard shortcuts (`useHotkeys`) |
| [080-unused-scss-classes.md](frontend/080-unused-scss-classes.md) | Orphan CSS-module class lint |

## Tooling & quality

| Doc | Topic |
|---|---|
| [030-lint-format-quality.md](tooling/030-lint-format-quality.md) | ESLint + @stylistic, pack-don't-stack, Fallow |
| [050-anti-slop.md](tooling/050-anti-slop.md) | Fallow anti-slop / PR gate |

## Workflow (operator / agent machine)

| Doc | Topic |
|---|---|
| [060-playwright-mcp-isolation.md](workflow/060-playwright-mcp-isolation.md) | Shared Playwright MCP |
| [070-tmux-shared-dev-server.md](workflow/070-tmux-shared-dev-server.md) | tmux dev servers |
| [090-slash-commands.md](workflow/090-slash-commands.md) | Slash command roster |
| [091-slash-commands-claude-vs-cursor.md](workflow/091-slash-commands-claude-vs-cursor.md) | Claude vs Cursor commands |

## LLM / agents

Read [`101-llm-adoption-order.md`](llm/101-llm-adoption-order.md) first — not every doc is in force on day one.

| Doc | Topic |
|---|---|
| [101-llm-adoption-order.md](llm/101-llm-adoption-order.md) | **Start here** — what to adopt when |
| [100-llm-call-pathway.md](llm/100-llm-call-pathway.md) | Call pathway, validation, retries |
| [105-llm-trust-boundary.md](llm/105-llm-trust-boundary.md) | Trust boundary / confirmation seam |
| [110-llm-observability.md](llm/110-llm-observability.md) | Observability |
| [120-prompt-and-context-budget.md](llm/120-prompt-and-context-budget.md) | Prompt & context budget |
| [125-agent-harness-extension.md](llm/125-agent-harness-extension.md) | Agent harness extension |
| [130-agent-job-contracts.md](llm/130-agent-job-contracts.md) | Job contracts |
| [140-llm-evals.md](llm/140-llm-evals.md) | Evals |
| [150-claude-skill-builder-guide.md](llm/150-claude-skill-builder-guide.md) | Skill builder reference *(not adoptable)* |
