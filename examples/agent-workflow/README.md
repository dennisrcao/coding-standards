# Agent workflow — a worked example

**Not standards, and not meant to install as-is.** This is how I run the standards day to day with
Claude Code and Cursor: the slash commands, agent skills and machine setup I actually use. It is
here because people ask how the pieces fit together, and the real files answer that better than a
description would.

It assumes my setup, and much of it will not run anywhere else without edits:

- **A separate docs repo** that holds plans and tickets. Several commands read and archive files in it.
- **A monorepo that deploys from `staging`, then `production`**, with PR preview deploys.
- **A multi-agent mesh**: one "driver" agent and several "tester" agents in tmux sessions, talking
  over a local message bus (Fabric). `/driver`, `/tester`, `/argue` and the `*-up` launchers only
  make sense with that running.
- **Several clones of the same repo side by side**, each on its own branch and dev-server port.

Read it for ideas and copy what fits.

## What's here

| Path | What it is |
|---|---|
| `commands/shared/` | One file for both agents: `/close-out`, `/ship`, `/stack`, `/pr-description`, `/pr-shots`, the mesh commands, and the spec-driven skill chain (`grilling` → `to-spec` → `to-tickets` → `implement` → `tdd` → `code-review`, plus `diagnosing-bugs`, `domain-modeling`, `handoff`, `sentry-to-ticket`) |
| `commands/claude/` | Claude Code only — `/ask` (a second opinion from Cursor), `/explain`, docs-repo upkeep |
| `commands/cursor/` | Cursor only — `/ask` and `/debate` (the mirror image), `/drive` |
| `docs/060`, `docs/070` | One shared Playwright MCP browser for every agent; dev servers in tmux so any agent can read their logs |
| `docs/090`–`092` | How to write a command, the Claude vs Cursor split, and running duplicate workspaces |
| `scripts/link-slash-commands.sh` | Symlinks `commands/` into `~/.claude` and `~/.cursor` so both agents read the tracked files |

## Credit

The spec-driven chain (`code-review`, `diagnosing-bugs`, `domain-modeling`, `grill-with-docs`,
`grilling`, `handoff`, `implement`, `tdd`, `to-spec`, `to-tickets`) is adapted from Matt Pocock's
[mattpocock/skills](https://github.com/mattpocock/skills) (MIT). My copies are wired to my
monorepo's issue tracker and branches; **for generic versions, start from his originals.** License
text: [`THIRD_PARTY_NOTICES.md`](../../THIRD_PARTY_NOTICES.md).
