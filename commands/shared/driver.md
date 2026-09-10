---
description: Fabric driver of one app-monorepo mesh. Core required. Testers on that mesh may debate, implement, and Playwright; you still own the PR merge.
argument-hint: "<core-N> [wait | no-wait | stop]  e.g. /driver core-1"
allowed-tools: Bash(git:*), Bash(gh:*), Bash(pnpm:*), Bash(npm:*), Bash(pwd), Bash(ls:*), Bash(cat:*), Bash(grep:*), Bash(find:*), Bash(mkdir:*), Bash(date), Bash(tmux:*), Read, Grep, Glob, Edit, Write, Shell, mcp__fabric__*, mcp__user-fabric__*
---

## Context (auto-collected)

- Now: !`date '+%Y-%m-%d %H:%M %Z'`
- FABRIC_MESH: !`printf '%s\n' "${FABRIC_MESH:-}"`
- Mesh pointers: !`ls -1 ~/.agent-mesh/missions/ACTIVE-core-* 2>/dev/null || echo "(none)"`
- Cwd (not authoritative): !`git rev-parse --show-toplevel 2>/dev/null || pwd`

`$ARGUMENTS`

---

# /driver — own one per-core mesh

You are the **driver** of **one** mesh. Mesh key is `core-N` (a app-monorepo checkout), not
the Cursor window, not the focused folder. TV Cursor and laptop Cursor can open the same
`.code-workspace`; they must not share `cursor`, a global `ACTIVE`, or `role.*`.

**Do not run `/close-out` or merge** from inside `/driver`.

## Resolve core (do this first)

First match wins:

1. `$ARGUMENTS` contains a core slug (`core-1`, `1`, `app-monorepo-1`, `stop` plus a core, …).
2. Else `FABRIC_MESH` from `mesh-cursor` / the environment.
3. **Else stop and ask.** Do not fall back to focused folder, cwd, or a single `ACTIVE`.
   `/driver` with no core is illegal when two meshes can be live.

```text
CHECKOUT=$(~/.agent-mesh/bin/resolve-checkout <slug>)
PORT=$(~/.agent-mesh/bin/resolve-checkout --port <slug>)
CORE=$(~/.agent-mesh/bin/resolve-checkout --core <slug>)
```

Channels (never `role.tester` / `role.driver`):

- Publish to testers: `mesh.<core>.tester`
- Subscribe / drain / wait: `mesh.<core>.driver`

Pointer: `~/.agent-mesh/missions/ACTIVE-<core>` (e.g. `ACTIVE-core-1`). Never write the global
`ACTIVE`. Identity to advertise: `cursor-<core>` in `meta.core` even if the Fabric process is
still named `cursor`.

## Testers are tmux, bound to this mesh

A Claude Code tab inside Cursor **cannot receive Fabric** (push mode, no channels flag, every
tab named `claude`). Spike 2026-09-10: unique `FABRIC_NAME` + pull delivery is not available
to those tabs — do not tell Dennis to `/tester` there.

```bash
tester-up core-1 a          # tmux session tester-core-1-a
tester-restart core-1 a
```

If `fabric_discover` shows no `tester-core-1-*` (filter `meta.core`), tell Dennis to run
`tester-up <core> a` in a terminal. Never publish to a `claude`.

**Wrong core:** `/driver stop` this mesh, then `/driver` the other. Do **not** `rebind`. A mesh
does not move. Testers on core-2 never wake for core-1 traffic.

## HARD RULES

- **Reproduce before fixing** — same bar as `/ask` verification. Unreproducible →
  `**Status:** unreproducible` and a log line, not a guess-fix.
- **All git/gh/pnpm in this mesh's checkout** — `git -C "$CHECKOUT" …`. Never touch another
  `app-monorepo-N`.
- **Stage explicit paths** — never `git add -A`.
- **Never publish or `fabric_request` to `agent.claude`.** Never naked `role.tester` /
  `role.driver`.
- **No `fabric_request` in mesh work.** Publish, end the turn, drain `mesh.<core>.driver` on
  the next `/driver`.
- **No headless `claude -p` as a stand-in for a tester.**
- **Drain first, every turn.** `fabric_drain({ channel: "mesh.<core>.driver" })`.
- **`fabric_discover`:** filter by `meta.core`. Ignore other meshes' testers.
- **Delegation is optional.** You may still implement yourself. `implement` is not a replacement
  for you coding.

## Step 1 — open or refresh the mission

`git -C "$CHECKOUT" rev-parse --abbrev-ref HEAD`. PR via `gh pr view` from that checkout.

Path: `~/.agent-mesh/missions/<branch-slug>.md` (slashes in branch → dashes).

Create if missing:

```markdown
# Mission: <branch>

**Mesh:** `core-N`
**Branch:** …
**Base:** …
**PR:** …
**Driver core:** `core-N`
**Driver checkout:** ~/Desktop/app-monorepo-N
**Driver port:** :5173
**Driver Fabric:** cursor-core-N
**Opened:** …

## Scopes

- **a:** _(driver defines)_
- **b:** _(driver defines)_

## Roster

## Findings

## Log
```

Write the path to `~/.agent-mesh/missions/ACTIVE-<core>` only. Fill `## Scopes` before testers
start. Roster lines include mesh (`mesh=core-1`).

If `$ARGUMENTS` is `stop` (with the core already resolved), skip to **/driver stop**.

## Step 2 — Fabric setup

1. `fabric_identity`. If down, log it and continue file-only.
2. `fabric_setPresence({ visible: true, meta: { role: "driver", core, branch, checkout, port, status: "busy" } })`.
3. `fabric_subscribe({ channel: "mesh.<core>.driver" })`.
4. `fabric_drain({ channel: "mesh.<core>.driver" })`.
5. `fabric_publish({ channel: "mesh.<core>.tester", payload: { kind: "driver-online", mesh: "<core>", branch, sha, checkout, port } })`.
6. When the mission is new, or a plan needs testers, publish `mission-assign` or `plan-critique`
   on `mesh.<core>.tester`.

```json
{
  "kind": "mission-assign",
  "mesh": "core-1",
  "mission": "~/.agent-mesh/missions/<slug>.md",
  "planPath": "<absolute path, optional>",
  "scopes": { "a": "<one line>", "b": "<one line>" },
  "ask": "<optional>"
}
```

Plan debate (loop until `plan-agree` or you stop):

```json
{ "kind": "plan-critique", "mesh": "core-1", "planPath": "…", "sha": "<sha>", "ask": "agree/disagree per section, file:line" }
```

Tester replies `{ kind: "plan-review", verdict, notes }` on `mesh.<core>.driver`. You may
`plan-revise` and send it back, then `{ kind: "plan-agree", mesh, planPath, sha }`.

If `## Roster` is empty, tell Dennis (Terminal, not a Claude tab):

```bash
tester-up core-1 a && tester-up core-1 b
```

## Step 3 — work loop

For each finding with `**Status:** open`, either fix it yourself **or** delegate:

### You implement

1. Reproduce (browser at mesh port, code in mesh checkout).
2. Fix under **Driver checkout** only; narrowest test there.
3. Commit and push from that checkout.
4. Update finding: `**Status:** fixed @ <short-sha>`.
5. Append `## Log`: `retest <sha> fixed [F-a-1, …]`.
6. `fabric_publish` on `mesh.<core>.tester`: `{ kind: "retest", mesh, branch, sha, fixed: [...] }`.

### Tester implements (`implement`)

Optional, per task. Tester may edit, commit, and push **on this mesh's feature branch only**.

```json
{
  "kind": "implement",
  "mesh": "core-1",
  "task": "<what to do>",
  "files": ["<optional paths>"],
  "sha": "<base sha>",
  "branch": "<feature branch>"
}
```

They reply `{ kind: "implement-done", mesh, sha, paths, tester }` on `mesh.<core>.driver`. You
review, then `retest` or merge-prep yourself. They must not merge, force-push `main`/`staging`,
or touch another Core-N.

### Playwright on the mesh port

```json
{ "kind": "playwright", "mesh": "core-1", "url": "http://localhost:<port>/", "task": "<flow>" }
```

One Playwright MCP on `:8931` for the **whole machine**. Two meshes Playwright-ing at once
steal tabs. Serialize, or skip Playwright on one mesh. Not a second server in v1.

## Step 4 — wait mode (default unless `$ARGUMENTS` contains `no-wait`)

- `fabric_wait({ channel: "mesh.<core>.driver", timeout_ms: 55000 })` in a loop.
- Stop after **5** consecutive empty waits or when testers publish `done` / `implement-done`
  for the current sha.
- Cursor's Fabric server is pull mode and cannot be woken. A late reply sits until the next
  drain. Say so ("waiting on tester-core-1-a; run `/driver core-1` to pick it up").

`fabric_wait` is **only** allowed inside `/driver` wait mode.

## Step 5 — report

Mesh, findings, commits, tester `done` / `implement-done` per scope, whether `ACTIVE-<core>`
stays.

## /driver stop

Only this mesh:

1. Append `mission closed` to `## Log`.
2. `fabric_publish` on `mesh.<core>.tester`: `{ kind: "mission-closed", mesh, branch }`.
3. `fabric_setPresence({ visible: false })`.
4. Remove `~/.agent-mesh/missions/ACTIVE-<core>` only. Leave other `ACTIVE-core-*` alone.
5. Kill tmux sessions matching `tester-<core>-*` (e.g. `tester-core-1-a`). Do not kill
   `tester-core-2-*`.
