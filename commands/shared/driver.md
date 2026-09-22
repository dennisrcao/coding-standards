---
description: Fabric driver of one workspace mesh. Mesh slug required. Testers on that mesh may debate, implement, and Playwright; you still own the PR merge.
argument-hint: "<mesh> [wait | no-wait | no-testers | stop]  e.g. /driver core-1 | /driver calendar-1"
allowed-tools: Bash(git:*), Bash(gh:*), Bash(pnpm:*), Bash(npm:*), Bash(pwd), Bash(ls:*), Bash(cat:*), Bash(grep:*), Bash(find:*), Bash(mkdir:*), Bash(date), Bash(tmux:*), Bash(sleep:*), Bash(~/.agent-mesh/bin/tester-up:*), Bash(~/.agent-mesh/bin/tester-restart:*), Read, Grep, Glob, Edit, Write, Shell, mcp__fabric__*, mcp__user-fabric__*
---

## Context (auto-collected)

- Now: !`date '+%Y-%m-%d %H:%M %Z'`
- FABRIC_MESH: !`printf '%s\n' "${FABRIC_MESH:-}"`
- Mesh pointers: !`ls -1 ~/.agent-mesh/missions/ACTIVE-* 2>/dev/null | grep -v '^.*ACTIVE-$' || echo "(none)"`
- Known meshes: !`~/.agent-mesh/bin/mesh-list 2>/dev/null | tail -n +3 || echo "(run link-slash-commands.sh)"`
- Cwd (not authoritative): !`git rev-parse --show-toplevel 2>/dev/null || pwd`

`$ARGUMENTS`

---

# /driver — own one workspace mesh

You are the **driver** of **one** mesh. Mesh key is a **workspace slug** from
`app-multi.code-workspace` (`core-1`, `calendar-1`, `portfolio`, …) — not the Cursor
window, not the focused folder. TV Cursor and laptop Cursor can open the same `.code-workspace`;
they must not share `cursor`, a global `ACTIVE`, or `role.*`.

**Do not run `/close-out` or merge** from inside `/driver`.

## Resolve mesh (do this first)

First match wins:

1. `$ARGUMENTS` contains a mesh slug (`core-1`, `calendar-1`, `claw-calendar`, `sigma`, `stop`
   plus a mesh, …). Run `mesh-list` when unsure.
2. Else `FABRIC_MESH` from `mesh-cursor` / the environment.
3. **Else stop and ask.** Do not fall back to focused folder, cwd, or a single `ACTIVE`.
   `/driver` with no mesh is illegal when two meshes can be live.

```text
CHECKOUT=$(~/.agent-mesh/bin/resolve-checkout <slug>)
PORT=$(~/.agent-mesh/bin/resolve-checkout --port <slug>)
PKG=$(~/.agent-mesh/bin/resolve-checkout --pkg <slug>)
MESH=$(~/.agent-mesh/bin/resolve-checkout --core <slug>)
```

Channels (never `role.tester` / `role.driver`):

- Publish to testers: `mesh.<mesh>.tester`
- Subscribe / drain / wait: `mesh.<mesh>.driver`

Pointer: `~/.agent-mesh/missions/ACTIVE-<mesh>` (e.g. `ACTIVE-calendar-1`). Never write the
global `ACTIVE`. Identity to advertise: `cursor-<mesh>` in `meta.core` even if the Fabric process
is still named `cursor`.

## Testers are tmux, bound to this mesh

A Claude Code tab inside Cursor **cannot receive Fabric** (push mode, no channels flag, every
tab named `claude`). Spike 2026-09-10: unique `FABRIC_NAME` + pull delivery is not available
to those tabs — do not tell Dennis to `/tester` there.

```bash
tester-up calendar-1 a      # tmux session tester-calendar-1-a
tester-up core-1 a          # tmux session tester-core-1-a
tester-restart calendar-1 a
```

You launch them yourself (Step 2, item 5) — `tester-up` is a plain script, runnable from this tab.
The rule above is about where the tester *lives* (tmux), not who starts it. Never publish to a
`claude`.

**Wrong mesh:** `/driver stop` this mesh, then `/driver` the other. Do **not** `rebind`. A mesh
does not move. Testers on `calendar-2` never wake for `calendar-1` traffic.

## HARD RULES

- **Reproduce before fixing** — same bar as `/ask` verification. Unreproducible →
  `**Status:** unreproducible` and a log line, not a guess-fix.
- **All git/gh in this mesh's checkout** — `git -C "$CHECKOUT" …`. Use `$PKG` (`pnpm` or `npm`)
  for that repo's scripts. Never touch another mesh's checkout.
- **Stage explicit paths** — never `git add -A`.
- **Never publish or `fabric_request` to `agent.claude`.** Never naked `role.tester` /
  `role.driver`.
- **No `fabric_request` in mesh work.** Publish, end the turn, drain `mesh.<mesh>.driver` on
  the next `/driver`.
- **No headless `claude -p` as a stand-in for a tester.**
- **Drain first, every turn.** `fabric_drain({ channel: "mesh.<mesh>.driver" })`.
- **Port 0** (e.g. `producer-pal`) — code-only mesh; skip Playwright unless the mission names a URL.
- **`fabric_discover`:** filter by `meta.core`. Ignore other meshes' testers.
- **Delegation is optional.** You may still implement yourself. `implement` is not a replacement
  for you coding.

## Step 1 — open or refresh the mission

`git -C "$CHECKOUT" rev-parse --abbrev-ref HEAD`. PR via `gh pr view` from that checkout.

Path: `~/.agent-mesh/missions/<branch-slug>.md` (slashes in branch → dashes).

Create if missing:

```markdown
# Mission: <branch>

**Mesh:** `calendar-1`
**Branch:** …
**Base:** …
**PR:** …
**Driver mesh:** `calendar-1`
**Driver checkout:** ~/Desktop/claw-calendar
**Driver port:** :3000
**Driver pkg:** npm
**Driver Fabric:** cursor-calendar-1
**Opened:** …

## Scopes

- **a:** _(driver defines)_
- **b:** _(driver defines)_

## Roster

## Findings

## Log
```

Write the path to `~/.agent-mesh/missions/ACTIVE-<mesh>` only. Fill `## Scopes` before testers
start. Roster lines include mesh (`mesh=calendar-1`).

If `$ARGUMENTS` is `stop` (with the mesh already resolved), skip to **/driver stop**.

## Step 2 — Fabric setup

1. `fabric_identity`. If down, log it and continue file-only.
2. `fabric_setPresence({ visible: true, meta: { role: "driver", core: mesh, branch, checkout, port, status: "busy" } })`.
3. `fabric_subscribe({ channel: "mesh.<mesh>.driver" })`.
4. `fabric_drain({ channel: "mesh.<mesh>.driver" })`.
5. **Launch missing testers** (skip if Fabric is down or `$ARGUMENTS` has `no-testers`).
   `fabric_discover`, filter `meta.core == <mesh>`. For each scope in `## Scopes` with no
   `tester-<mesh>-<scope>-*`, run `~/.agent-mesh/bin/tester-up <mesh> <scope>` (it needs
   `ACTIVE-<mesh>` from Step 1, blocks until it has typed `/tester`, and refuses an existing
   session — don't kill one, use `tester-restart` only if that tester is wedged). Then poll
   `fabric_discover` (`sleep 15`, up to 4×) until each appears; add a Roster line per tester.
   A launch that fails or never shows up → log it, show `tmux capture-pane -p -t
   tester-<mesh>-<scope> -S -15`, and carry on without that scope. Launch **before** step 6 —
   push delivery drops messages published before a tester subscribes.
6. `fabric_publish({ channel: "mesh.<mesh>.tester", payload: { kind: "driver-online", mesh, branch, sha, checkout, port } })`.
7. When the mission is new, or a plan needs testers, publish `mission-assign` or `plan-critique`
   on `mesh.<mesh>.tester`.

```json
{
  "kind": "mission-assign",
  "mesh": "calendar-1",
  "mission": "~/.agent-mesh/missions/<slug>.md",
  "planPath": "<absolute path, optional>",
  "scopes": { "a": "<one line>", "b": "<one line>" },
  "ask": "<optional>"
}
```

Plan debate (loop until `plan-agree` or you stop). Prefer **`/argue <mesh>`** — it runs the
bounded loop, ledger (`<plan>.argue.md`), verification, and `plan-agree` per
`argue-protocol.md`. Manual publish still works:

```json
{ "kind": "plan-critique", "mesh": "calendar-1", "planPath": "…", "sha": "<sha>", "ask": "agree/disagree per section, file:line" }
```

Tester replies `{ kind: "plan-review", verdict, notes }` on `mesh.<mesh>.driver`. You may
`plan-revise` and send it back, then `{ kind: "plan-agree", mesh, planPath, sha }`.

If `## Roster` is still empty after step 5, say which launches failed and why.

## Step 3 — work loop

For each finding with `**Status:** open`, either fix it yourself **or** delegate:

### You implement

1. Reproduce (browser at mesh port, code in mesh checkout).
2. Fix under **Driver checkout** only; narrowest test there.
3. Commit and push from that checkout.
4. Update finding: `**Status:** fixed @ <short-sha>`.
5. Append `## Log`: `retest <sha> fixed [F-a-1, …]`.
6. `fabric_publish` on `mesh.<mesh>.tester`: `{ kind: "retest", mesh, branch, sha, fixed: [...] }`.

### Tester implements (`implement`)

Optional, per task. Tester may edit, commit, and push **on this mesh's feature branch only**.

```json
{
  "kind": "implement",
  "mesh": "calendar-1",
  "task": "<what to do>",
  "files": ["<optional paths>"],
  "sha": "<base sha>",
  "branch": "<feature branch>"
}
```

They reply `{ kind: "implement-done", mesh, sha, paths, tester }` on `mesh.<mesh>.driver`. You
review, then `retest` or merge-prep yourself. They must not merge, force-push protected branches,
or touch another mesh's checkout.

### Playwright on the mesh port

```json
{ "kind": "playwright", "mesh": "calendar-1", "url": "http://localhost:<port>/", "task": "<flow>" }
```

One Playwright MCP on `:8931` for the **whole machine**. Two meshes Playwright-ing at once
steal tabs. Serialize, or skip Playwright on one mesh. Not a second server in v1.

## Step 4 — wait mode (default unless `$ARGUMENTS` contains `no-wait`)

- `fabric_wait({ channel: "mesh.<mesh>.driver", timeout_ms: 55000 })` in a loop.
- Stop after **5** consecutive empty waits or when testers publish `done` / `implement-done`
  for the current sha.
- Cursor's Fabric server is pull mode and cannot be woken. A late reply sits until the next
  drain. Say so ("waiting on tester-calendar-1-a; run `/driver calendar-1` to pick it up").

`fabric_wait` is **only** allowed inside `/driver` wait mode.

## Step 5 — report

Mesh, findings, commits, tester `done` / `implement-done` per scope, whether `ACTIVE-<mesh>`
stays.

## /driver stop

Only this mesh:

1. Append `mission closed` to `## Log`.
2. `fabric_publish` on `mesh.<mesh>.tester`: `{ kind: "mission-closed", mesh, branch }`.
3. `fabric_setPresence({ visible: false })`.
4. Remove `~/.agent-mesh/missions/ACTIVE-<mesh>` only. Leave other `ACTIVE-*` alone.
5. Kill tmux sessions matching `tester-<mesh>-*` (e.g. `tester-calendar-1-a`). Do not kill
   other meshes' `tester-*` sessions.
