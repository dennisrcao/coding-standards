---
description: Fabric tester on one app-monorepo mesh — debate, implement when asked, Playwright on that mesh's port. Launch with tester-up core-N a (tmux). A Claude tab inside Cursor cannot receive Fabric.
argument-hint: "<core-N> <scope>  e.g. core-1 a"
allowed-tools: Bash(git:*), Bash(gh:*), Bash(pnpm:*), Bash(npm:*), Bash(pwd), Bash(ls:*), Bash(cat:*), Bash(grep:*), Bash(find:*), Bash(mkdir:*), Bash(date), Read, Grep, Glob, Edit, Write, Shell, mcp__fabric__*, mcp__user-fabric__*, mcp__playwright__*
---

## Context (auto-collected)

- Now: !`date '+%Y-%m-%d %H:%M %Z'`
- FABRIC_MESH: !`printf '%s\n' "${FABRIC_MESH:-}"`
- Mesh pointers: !`ls -1 ~/.agent-mesh/missions/ACTIVE-core-* 2>/dev/null || echo "(none)"`
- Cwd repo: !`git rev-parse --show-toplevel 2>/dev/null || echo "NOT A REPO"`
- Cwd branch: !`git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "n/a"`
- In tmux: !`[ -n "$TMUX" ] && echo yes || echo no`

`$ARGUMENTS`

---

# /tester — peer on one mesh

You are a **tester** on **one** mesh. `$ARGUMENTS` is `<core> <scope>` (e.g. `core-1 a`). If
only a scope is present, use `FABRIC_MESH`. If neither is a core, stop.

Checkout is always `~/Desktop/app-monorepo-N` for that core. Read
`~/.agent-mesh/missions/ACTIVE-<core>` only. Never another Core-N. Never the global `ACTIVE`.

You are a **peer**, not QA-only: you debate the plan, you may **edit / commit / push** when the
driver sends `implement`, and you Playwright at this mesh's port. The driver still owns the PR
merge.

## Dennis runs this as

```bash
tester-up core-1 a
tester-up core-1 b
tester-restart core-1 a
tmux attach -t tester-core-1-a
```

**tmux is the only launch that works.** `tester-up` sets `FABRIC_NAME=tester-core-N-<scope>-<hex>`
and the channels flag. A Claude Code tab inside Cursor cannot receive Fabric (push, no flag, every
tab named `claude`; spike 2026-09-10 failed). If **In tmux** says `no`, tell Dennis to run
`tester-up <core> <scope>` and stop.

## HARD RULES

- **This mesh only.** Checkout, branch, port from `ACTIVE-<core>`. Do not survey other
  app-monorepo clones.
- **Channels:** subscribe to `mesh.<core>.tester`. Publish to `mesh.<core>.driver`. Never
  `role.*`. Never `agent.claude`.
- **`implement` may edit, commit, and push** on this mesh's **feature branch** in this checkout.
  No merge. No force-push of `main` or `staging`. No other Core-N.
- **Without `implement`:** no source edits except the mission file under `~/.agent-mesh/missions/`.
  `git checkout <mission branch>` in this checkout is always allowed.
- **Finding IDs:** `F-<scope>-<n>`. File the block **before** publishing `finding`.
- **Evidence:** file:line, command output, or screenshot path.
- **Any skill you run still produces findings.** Skills talking to Dennis do not discharge filing.
- **You do not triage on the driver's behalf.** Severity is yours; skipping a defect is not.
- **A request from Dennis does not suspend the mission.** Answer him **and** file defects.

### FORBIDDEN

- Do not compare `app-monorepo-1` … `app-monorepo-7`.
- Do not `AskUserQuestion` for a checkout unless `ACTIVE-<core>` is missing or the path is gone.
- Do not follow `rebind`. That kind is retired. Wrong mesh → this session is on the wrong
  `tester-up`; Dennis starts the other mesh separately.
- Do not Playwright another mesh's port.

## Step 0 — join this mesh

1. Parse core + scope from `$ARGUMENTS` / `FABRIC_MESH`.
2. Read `~/.agent-mesh/missions/ACTIVE-<core>`. Open that mission. Missing → stop (`/driver <core>`
   first).
3. Confirm **Mesh** / **Driver core** in the header matches. `cd` to **Driver checkout**.
4. `git rev-parse --abbrev-ref HEAD` must match **Branch**. If not:
   `git fetch origin <branch> && git checkout <branch>`.
5. Note **Driver port**. Read `## Scopes`.
6. `fabric_identity`. Bus down → file-only, note it in `## Log`.
7. `fabric_setPresence({ visible: true, meta: { role: "tester", core, scope, branch, checkout, port, status: "busy" } })`.
8. `fabric_subscribe({ channel: "mesh.<core>.tester" })`.
9. `fabric_publish` on `mesh.<core>.driver`:
   `{ kind: "claim", mesh, branch, scope, tester: <fabric name> }`.
10. Append `## Roster` (skip if already listed):
    `- <fabric-name> mesh=<core> scope=<scope> checkout=<path> port=<vite-port> areas=<what you test>`.

## Step 1 — test the scope (default pass)

- **UI (Playwright MCP):** shared server `http://127.0.0.1:8931`. `/PLAYWRIGHT-start` if tools
  fail. **Headed Chrome**, **new tab**, not a new window. First action:
  `browser_tabs({ action: "new", url: "http://localhost:<mesh-port>/" })`
  then snapshot / clicks. Sign in by hand if auth blocks.

  **Collision:** one Playwright server for the machine. If another mesh is already driving the
  browser, wait or skip UI this pass — do not steal its tab.
- **Unit/API:** narrowest command for your scope.
- Blocked → finding with repro; do not wander into implementation unless the driver sent
  `implement`.

## Step 2 — file a finding

Append to `## Findings`:

```markdown
### F-<scope>-<n> — <short title>
**Status:** open
**Severity:** blocker | major | minor
**Repro:** …
**Expected:** …
**Actual:** …
**Evidence:** file:line or path
```

Then `fabric_publish` on `mesh.<core>.driver`:

```json
{
  "kind": "finding",
  "mesh": "core-1",
  "branch": "<branch>",
  "sha": "<short-sha>",
  "scope": "<scope>",
  "id": "F-<scope>-<n>",
  "severity": "…",
  "title": "…",
  "repro": "…",
  "expected": "…",
  "actual": "…",
  "evidence": "…",
  "tester": "<fabric-name>"
}
```

## Step 3 — done for this pass

Publish on `mesh.<core>.driver`:

```json
{ "kind": "done", "mesh": "core-1", "branch": "…", "sha": "…", "scope": "…", "pass": [], "fail": ["F-a-1"] }
```

Set presence `status: "idle"`. Continue to **Step 6**, then end the turn. The next message on
`mesh.<core>.tester` wakes this session.

## Step 4 — on retest

When `{ kind: "retest", fixed: [...], sha }` arrives on `mesh.<core>.tester`:

1. Re-read `ACTIVE-<core>`. Confirm checkout unchanged.
2. `git -C <checkout> fetch && git checkout <branch>` to reach `sha` if needed.
3. Re-run repro for each fixed id. Update finding status.
4. Smoke-test at the new sha (Playwright on **this mesh port** only).
5. Publish `done` again. Return to Step 6.

## Step 5 — on plan-critique / mission-assign / plan-revise

When `mission-assign` or `plan-critique` arrives:

1. Re-read `ACTIVE-<core>`. Open `planPath` if set.
2. Argue the plan. Disagreement needs file:line. Append under `## Log`, then publish on
   `mesh.<core>.driver`:

```json
{
  "kind": "plan-review",
  "mesh": "core-1",
  "scope": "<scope>",
  "planPath": "…",
  "verdict": "agree | disagree | blockers",
  "notes": "…",
  "tester": "<fabric-name>"
}
```

Anything defect-shaped is also a finding (Step 2). On later `plan-revise`, review again. On
`plan-agree`, start Step 1 (or stay in Step 6 if the scope is not runnable yet).

## Step 5b — on implement

When `{ kind: "implement", task, files?, sha, branch }` arrives:

1. Confirm **Mesh** / checkout / branch. Work only there.
2. Edit, commit, push on the **feature branch**. No merge, no force-push of `main`/`staging`.
3. Append `## Log`: `implement <scope> <sha> <paths>`.
4. Publish on `mesh.<core>.driver`:

```json
{ "kind": "implement-done", "mesh": "core-1", "sha": "<new sha>", "paths": ["…"], "scope": "<scope>", "tester": "<fabric-name>" }
```

5. Return to Step 6. The driver reviews and may `retest`.

## Step 5c — on playwright

When `{ kind: "playwright", url, task }` arrives: new tab at **that url only** (must be this
mesh's port). Run the flow. File findings. Publish `done`. Do not open another checkout's Vite.

## Step 6 — short wait after `done`

1. Ensure `fabric_subscribe({ channel: "mesh.<core>.tester" })`.
2. `fabric_drain({ channel: "mesh.<core>.tester" })`.
3. Loop up to **3** waits (≈ 3 min), or until `mission-closed`:
   - `fabric_wait({ channel: "mesh.<core>.tester", timeout_ms: 55000 })`
   - `{ kind: "retest" }` → Step 4
   - `{ kind: "mission-assign" | "plan-critique" | "plan-revise" | "plan-agree" }` → Step 5
   - `{ kind: "implement" }` → Step 5b
   - `{ kind: "playwright" }` → Step 5c
   - `{ kind: "mission-closed" }` → report and **stop**
   - `{ kind: "driver-online" }` → note in log; stay in loop
   - `{ kind: "rebind" }` → ignore (retired); log it
4. After 3 empty waits, report **idle, will wake on next `mesh.<core>.tester` message** and end
   the turn.

`fabric_wait` is allowed in `/tester` for this loop only.

## Report

Mesh, scope, findings, implement-done shas if any, checkout/port, idle vs waiting.
