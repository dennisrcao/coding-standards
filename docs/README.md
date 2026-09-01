# Coding standards — index

**Status:** Reference

Portable rules copied into target repos as `.cursor/rules/<NNN>-<slug>.mdc`. Repo root
[`README.md`](../README.md) covers adoption; start LLM work at [`llm/101-llm-adoption-order.md`](llm/101-llm-adoption-order.md).

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
| [claude-skill-builder-guide.md](llm/claude-skill-builder-guide.md) | Skill builder reference |
