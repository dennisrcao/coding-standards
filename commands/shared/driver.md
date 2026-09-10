---
description: Fabric driver — own the mission file, fix tester findings, publish retest, wait for done. Cursor normally; implements all fixes.
argument-hint: "[core-N] [wait | no-wait]  e.g. /driver core-2"
allowed-tools: Bash(git:*), Bash(gh:*), Bash(pnpm:*), Bash(npm:*), Bash(pwd), Bash(ls:*), Bash(cat:*), Bash(grep:*), Bash(find:*), Bash(mkdir:*), Bash(date), Read, Grep, Glob, Edit, Write, Shell, mcp__fabric__*, mcp__user-fabric__*
---

## Context (auto-collected)

- Now: !`date '+%Y-%m-%d %H:%M %Z'`
- Active mission: !`cat ~/.agent-mesh/missions/ACTIVE 2>/dev/null || echo "(none)"`
- Mission checkout: !`~/.agent-mesh/bin/mission-field checkout 2>/dev/null || echo "(none)"`
- Mission core: !`~/.agent-mesh/bin/mission-field core 2>/dev/null || echo "(none)"`
- Cwd (not authoritative): !`git rev-parse --show-toplevel 2>/dev/null || pwd`

`$ARGUMENTS`

---

# /driver — implement fixes for the active mission

You are the **driver**. Testers file findings; you reproduce, fix, commit, push, and publish `retest`.
Use the mission file as the durable record. Use Fabric when the bus is up.

**Do not run `/close-out` or merge** from inside `/driver`.

## Multi-root workspace (important)

Dennis keeps **many repos in one Cursor workspace** (app-monorepo-1 … 7, studio, calendar, …).
**Which folder Cursor has focused does not matter.** The mission file declares the driver checkout;
testers and driver both follow that path.

Dennis does **not** need to `cd` into a repo first.

```text
/driver core-2     # declare driver = app-monorepo-2 (from any Cursor window)
/driver            # resume ACTIVE mission (same checkout as before)
tester-up a        # Terminal: launches /tester a in tmux with the channels flag + unique Fabric name
tester-restart a   # kill tmux tester-a and relaunch from ACTIVE mission (after rebind)
```

**Testers must be `tester-up` tmux sessions.** A Claude Code tab inside Cursor cannot receive
Fabric (push mode, no channels flag; every message is drained into a notification the tab never
renders, verified 2026-09-09). If `fabric_discover` shows only `claude` and no `tester-<scope>-*`,
tell Dennis to run `tester-up <scope>` in a terminal; do not publish to that `claude`.

**One slug binds the pair.** `/driver core-1` sets **Driver checkout**, **Driver port**, and
**Driver core** in the mission file. Testers never pick a checkout themselves — they read ACTIVE.
If you move the driver (`/driver core-1` while testers were on Core-3), publish **`rebind`** on
`role.tester` so live testers retarget (see Step 1).

## HARD RULES

- **Reproduce before fixing** — same bar as `/ask` verification. A finding you cannot reproduce gets
  `**Status:** unreproducible` and a log line, not a guess-fix.
- **One active mission** — `~/.agent-mesh/missions/ACTIVE` points at the current file.
- **Driver checkout is explicit** — from `$ARGUMENTS` (`core-2`, `2`, …), or **Driver checkout** in
  ACTIVE mission. Never infer from Cursor's focused folder alone.
- **All git/gh/pnpm in the driver checkout** — `git -C "$CHECKOUT" …`, `cd "$CHECKOUT" && pnpm …`.
- **Stage explicit paths** — never `git add -A`.
- **Never publish or `fabric_request` to `agent.claude`** — use `role.tester` (to testers) and
  `role.driver` (from testers). `agent.claude` fans out to every Claude tab and none can answer.
- **No `fabric_request` in mesh work.** It needs a responder mid-turn within 60 s; testers are idle
  between passes. Publish, end the turn, read `role.driver` on the next `/driver`.
- **No headless `claude -p` as a stand-in for a tester.** A cold process has none of the tester's
  context; if Dennis wants the tester's view, `mission-assign` with `ask` (Step 2).
- **Drain first, every turn.** `fabric_drain({ channel: "role.driver" })` at the start of each
  `/driver` turn: tester replies land after your wait loop ends.

## Step 0 — resolve driver checkout

Resolve in this order (first match wins):

1. **`$ARGUMENTS` contains a core slug** (`core-2`, `2`, `app-monorepo-2`, …):
   - `CHECKOUT=$(resolve-checkout <slug>)`
   - `PORT=$(resolve-checkout --port <slug>)`
   - `CORE=$(resolve-checkout --core <slug>)`
2. **ACTIVE mission exists** and `$ARGUMENTS` does not name a new core:
   - Read **Driver checkout** and **Driver port** from the mission file.
3. **Else** if cwd is under `~/Desktop/app-monorepo-*`, use that as a weak fallback.
4. **Else** stop and tell Dennis: `/driver core-N` once (e.g. `/driver core-2`).

Helper: `~/.agent-mesh/bin/resolve-checkout` (symlinked from agent-mesh hub).

Record **Driver core**, **Driver checkout**, **Driver port**, branch, and PR in the mission header.

## Step 1 — open or refresh the mission

Run `git -C "$CHECKOUT" rev-parse --abbrev-ref HEAD` for branch. Open PR via
`gh pr view --repo …` from that checkout.

Path: `~/.agent-mesh/missions/<branch-slug>.md` (slashes in branch → dashes).

Before overwriting the header, note **previous Driver checkout** from the existing mission file (if
any). After you write the new header, if previous checkout was set and differs from the new
`CHECKOUT`:

1. Append to `## Log`: `rebind <core> checkout <path> port :<port>`.
2. `fabric_publish` on `role.tester`:

```json
{
  "kind": "rebind",
  "core": "core-1",
  "checkout": "~/Desktop/app-monorepo-1",
  "port": "5173",
  "branch": "<branch>",
  "sha": "<short-sha>",
  "previousCheckout": "<old-path>"
}
```

3. Tell Dennis: tmux testers wake on this message (~30 s) and re-align themselves (Step 5 of
   `/tester`). If one does not react within a minute, `tester-restart <scope>`.

If `$ARGUMENTS` named a core slug but checkout did not change, skip `rebind` (resume only).

Create if missing:

```markdown
# Mission: <branch>

**Branch:** …
**Base:** …
**PR:** …
**Driver core:** `core-N`
**Driver checkout:** ~/Desktop/app-monorepo-N
**Driver port:** :5173
**Driver Fabric:** cursor
**Opened:** …

## Scopes

- **a:** _(driver defines)_
- **b:** _(driver defines)_
- **c:** _(optional)_

## Roster

## Findings

## Log
```

Write the path to `~/.agent-mesh/missions/ACTIVE`. Fill in `## Scopes` before telling Dennis to start
testers.

## Step 2 — Fabric setup

1. `fabric_identity`. If down, log it in `## Log` and continue file-only.
2. `fabric_setPresence({ visible: true, meta: { role: "driver", branch, checkout, port, status: "busy" } })`.
3. `fabric_subscribe({ channel: "role.driver" })`.
4. `fabric_drain({ channel: "role.driver" })`.
5. `fabric_publish({ channel: "role.tester", payload: { kind: "driver-online", branch, sha, core, checkout, port } })`.
6. **When the mission is new, or a plan needs the testers' view**, publish `mission-assign`:

```json
{
  "kind": "mission-assign",
  "mission": "~/.agent-mesh/missions/<slug>.md",
  "planPath": "<absolute path to the plan, optional>",
  "scopes": { "a": "<one line>", "b": "<one line>" },
  "ask": "<optional: what you want back, e.g. agree/disagree per section with file:line evidence>"
}
```

Testers answer on `role.driver` with `{ kind: "plan-review", verdict, notes }` and log it in the
mission file (`/tester` Step 5b). End the turn after publishing; read the answer next `/driver`.

If `## Roster` is empty, tell Dennis (Terminal, not a Claude tab):

```bash
tester-up a && tester-up b
```

## Step 3 — fix loop

For each finding with `**Status:** open`:

1. Reproduce from the finding block (browser at mission port, code in driver checkout).
2. Fix under **Driver checkout** only; run the narrowest test there.
3. Commit and push from that checkout.
4. Update finding: `**Status:** fixed @ <short-sha>`.
5. Append to `## Log`: `retest <sha> fixed [F-a-1, …]`.
6. `fabric_publish({ channel: "role.tester", payload: { kind: "retest", branch, sha, fixed: [...] } })`.

## Step 4 — wait mode (default unless `$ARGUMENTS` contains `no-wait`)

- `fabric_wait({ channel: "role.driver", timeout_ms: 55000 })` in a loop.
- Stop after **5** consecutive empty waits or when testers publish `done` for current sha.
- Cursor's Fabric server is pull mode and cannot be woken, so a reply that lands after the loop is
  not lost: it sits in the buffer until the drain at the start of the next `/driver` turn. Say so in
  the report ("waiting on tester-a; run `/driver` to pick up its reply").

`fabric_wait` is **only** allowed inside `/driver` wait mode.

## Step 5 — report

Findings status, commits pushed, tester `done` per scope, whether mission stays active.

## /driver stop

1. Append `mission closed` to `## Log`.
2. `fabric_publish({ channel: "role.tester", payload: { kind: "mission-closed", branch } })`.
3. `fabric_setPresence({ visible: false })`.
4. Remove `~/.agent-mesh/missions/ACTIVE`.
5. `tmux kill-session -t tester-a` (and `-b`, …) if needed.
