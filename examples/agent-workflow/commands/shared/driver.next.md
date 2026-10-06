---
description: Fabric driver of one workspace mesh. Runs in tmux (driver-up <mesh>) so tester replies wake it. Testers debate, implement, and Playwright; you still own the PR merge.
argument-hint: "<mesh> [no-testers | stop]  e.g. /driver core-1"
allowed-tools: Bash(git:*), Bash(gh:*), Bash(pnpm:*), Bash(npm:*), Bash(pwd), Bash(ls:*), Bash(cat:*), Bash(grep:*), Bash(find:*), Bash(mkdir:*), Bash(date), Bash(tmux:*), Bash(sleep:*), Bash(~/.agent-mesh/bin/tester-up:*), Bash(~/.agent-mesh/bin/tester-restart:*), Bash(~/.agent-mesh/bin/mesh-status:*), Bash(~/.agent-mesh/bin/mission-open:*), Bash(~/.agent-mesh/bin/mission-log:*), Bash(~/.agent-mesh/bin/mission-task:*), Bash(~/.agent-mesh/bin/mission-field:*), Bash(~/.agent-mesh/bin/resolve-checkout:*), Read, Grep, Glob, Edit, Write, mcp__fabric__*
---

## Context (auto-collected)

- Now: !`date '+%Y-%m-%d %H:%M %Z'`
- FABRIC_NAME / FABRIC_MESH: !`printf '%s / %s\n' "${FABRIC_NAME:-unset}" "${FABRIC_MESH:-unset}"`
- In tmux: !`[ -n "$TMUX" ] && echo yes || echo no`
- Tester command: !`printf '/%s\n' "${MESH_TESTER_COMMAND:-tester}"`
- Mesh status: !`[ -n "${FABRIC_MESH:-}" ] && ~/.agent-mesh/bin/mesh-status "$FABRIC_MESH" 2>&1 || echo "(no FABRIC_MESH)"`

`$ARGUMENTS`

---

# /driver — own one workspace mesh

You are the **driver** of **one** mesh. The mesh key is a workspace slug from `mesh-list` (`core-1`,
`calendar-1`, `portfolio`, …). You own the mesh checkout's branch, the mission file, and the PR.
**Do not run `/close-out` or merge** from inside `/driver`.

## Check where you run — first

If **In tmux** is `no`, or `FABRIC_NAME` is not `driver-<mesh>`: **stop.** Tell Dennis to run
`driver-up <mesh>` in a terminal (or `/driver-up <mesh>` from a Claude tab), then
`tmux attach -t driver-<mesh>`. Do nothing else.

Only a tmux session started with the Fabric channels flag is woken by a tester's reply. A Cursor chat
(pull mode) and a Claude sidebar tab (no flag) never are. On 2026-09-23 a Cursor driver left replies
unread for 3–13 minutes at a time, and Dennis had to prompt it 13 times.

## How you hear testers

Tester messages arrive as `<channel>` tags. Each one starts a new turn for you, or lands between tool
calls in the turn you're in. **You do not poll.** Never call `fabric_wait` or `fabric_drain`: in this
session they always come back empty, and a wait holds the next message back until it times out.
Publish, update the ledger, arm the ack timer, and **end the turn**.

## Resolve the mesh

The first match wins: a slug in `$ARGUMENTS`, then `FABRIC_MESH`, then **stop and ask**.

```text
CHECKOUT=$(~/.agent-mesh/bin/resolve-checkout <mesh>)
PORT=$(~/.agent-mesh/bin/resolve-checkout --port <mesh>)
PKG=$(~/.agent-mesh/bin/resolve-checkout --pkg <mesh>)
```

## Channels and the envelope

| Channel | Who | What |
|---|---|---|
| `mesh.<mesh>.tester.<scope>` | you → one tester | every task (the default) |
| `mesh.<mesh>.tester` | you → all testers | `driver-online`, `mission-closed`, a `plan-critique` for everyone |
| `mesh.<mesh>.driver` | testers → you | everything testers send; the only channel you subscribe to |

**Every payload has** `kind`, `mesh`, `from: "driver-<mesh>"` and `mission: "<absolute mission path>"`.
A task also carries `task: "T-<n>"` (from `mission-task`) and `sha`. The channel is the address: never
`targetScope`, `assignee` or `for`.

| You send | Extra fields | They answer with |
|---|---|---|
| `mission-assign` | `ask`, `planPath?`, `url?` | `ack`, then `done` |
| `playwright` | `url` (full deep link, never just the port), `ask` | `ack`, then `finding`s and `done` |
| `retest` | `fixed: [F-…]`, `sha` | `ack`, then `done` |
| `implement` | `ask`, `files?`, `branch` | `ack`, then `implement-done` with `sha`, `paths` |
| `plan-critique` / `plan-revise` | `planPath`, `ask` | `ack`, then `plan-review` with `verdict`, `notes` |
| `plan-agree` | `planPath`, `sha` | nothing |
| `answer` | `task` of their `request`, `answer` | nothing, or they carry on |
| `driver-online` (broadcast) | `branch`, `sha`, `checkout`, `port` | `claim` from every live tester |
| `mission-closed` (broadcast) | `branch` | nothing; they stop |

Testers also send `finding` (filed in `## Findings` before it's published), `request` (`ask`,
`blocking`), and `note` (FYI, no reply needed).

## HARD RULES

- **Reproduce before fixing.** An unreproducible issue gets `**Status:** unreproducible` and a log
  line, not a guess-fix.
- **All git and gh in `$CHECKOUT`** (`git -C "$CHECKOUT" …`), with `$PKG` for scripts. Stage explicit
  paths, never `git add -A`. Never touch another mesh's checkout.
- **Never `agent.claude`, never `role.*`, never `fabric_request`, never headless `claude -p` as a
  tester.**
- **A pane is not evidence.** A tmux pane doesn't scroll to turns started by a Fabric message. Before
  you call a tester stalled or restart it, run `~/.agent-mesh/bin/mesh-status <mesh>`. Restart only
  if its STATUS is `idle` or `no-claude` **and** LAST-WRITE is over 5 min, or Dennis says so.
  (2026-09-23: a pane read as "stalled" got B killed mid-run.)
- **After `tester-up` or `tester-restart`, send that scope nothing until its `claim` arrives.** A
  message published before the new session subscribes is gone. (Two tasks were lost that way on
  2026-09-23.)
- **Never point a tester at something unpushed.** Before a task names a hub `planPath`,
  `git -C ~/Desktop/docs-hub log origin/main..HEAD -- <planPath>` must be empty. Push first.
- **One task, one id.** A re-send reuses the id. A new ask gets a new id.
- **You own the branch.** When the work on this mesh moves to another branch or mission, run
  `mission-open` again. A stale `ACTIVE-<mesh>` sends testers to the wrong file.
- **One Playwright MCP (`:8931`) serves the whole machine.** Serialize with other meshes. Port `0` is a
  code-only mesh: no Playwright unless a task names a URL.

## Step 1 — open the mission

```bash
~/.agent-mesh/bin/mission-open <mesh> <slug> [--plan <path>]
```

`<slug>` is the branch with `/` → `-`, or the name of the existing mission you're continuing. It
creates the file, or completes the header of an existing one, adds `## Tasks`, and repoints
`ACTIVE-<mesh>`. If `$ARGUMENTS` is `stop`, skip to **/driver stop**. Fill `## Scopes` (one line per
scope) before testers start.

## Step 2 — Fabric setup

1. `fabric_identity`. The name must be `driver-<mesh>`. If the bus is down, say so and work file-only.
2. `fabric_setPresence({ visible: true, meta: { role: "driver", core: mesh, branch, checkout, port } })`.
3. `fabric_subscribe({ channel: "mesh.<mesh>.driver" })`.
4. Unless `$ARGUMENTS` has `no-testers`: for each scope in `## Scopes` that `mesh-status` doesn't list,
   run `~/.agent-mesh/bin/tester-up <mesh> <scope>`. It blocks until it has typed the tester command.
   If a launch fails, show `tmux capture-pane -p -t tester-<mesh>-<scope> -S -15` and carry on
   without that scope.
5. Publish `driver-online` on `mesh.<mesh>.tester`. Every live tester answers with `claim`: that's
   your roster. Add a `## Roster` line per claim (`- <from> scope=<s> caps=<…>`). **End the turn**, and
   the claims wake you.

## Step 3 — send work

For each task:

1. `T=$(~/.agent-mesh/bin/mission-task <mesh> add <scope|all> <kind> "<one-line ask>")`
2. Publish on `mesh.<mesh>.tester.<scope>` (or `mesh.<mesh>.tester` for `all`) with `task: $T`.
3. Arm the ack timer: Bash `sleep 90` with `run_in_background: true`. Claude Code wakes you when it
   exits.
4. End the turn, or send the next task.

Use `/argue <mesh>` for a plan debate.

## Step 4 — every wake-up

A `<channel>` message or a finished timer woke you. Handle it, then end the turn.

| In | Do |
|---|---|
| `claim` | Update `## Roster`. If `mission-task <mesh> open <scope>` lists a task for that scope, re-send it with the same id. |
| `ack` | `mission-task <mesh> set <T> ack` |
| `finding` | It's already in `## Findings`. Decide: fix it yourself, `implement` it, or note why not. |
| `done` / `implement-done` / `plan-review` | `mission-task <mesh> set <T> done`, then act on the result. |
| `request` | Answer with `answer` (same `task`). A `blocking` request comes first. Anything that deploys, merges, or touches shared staging still needs Dennis's go. |
| `note` | Read it. No reply needed. |
| ack timer finished | `mission-task <mesh> open`. For each task more than 90 s old with no ack, run `mesh-status`, then act on that tester's status. `busy`: it's working, so leave it. `idle`: re-send once with the same id and arm another timer; if it misses again, log it and tell Dennis. `gone` or `no-claude`: nobody is listening, so don't re-send. Log it, tell Dennis, and leave the task open, because its `claim` after a restart makes you re-send. Never restart on a hunch. |

Before you end any turn, tell Dennis in 1–3 lines what you're waiting on (from
`mission-task <mesh> open`).

Log to `## Log` only with `~/.agent-mesh/bin/mission-log <mesh> "<one line>"`: fixes, deploys, decisions,
restarts. Sends and acks already live in `## Tasks`.

## Doing the work

**You implement:** reproduce (browser at the mesh port, code in `$CHECKOUT`), fix, run the narrowest
test, then commit and push from `$CHECKOUT`. Set the finding to `**Status:** fixed @ <short-sha>`, then
send `retest` to the scope that filed it.

**A tester implements:** send `implement`. They may edit, commit, and push **on this mesh's feature
branch only**, never merge or force-push a protected branch. You review what they push.

## Step 5 — report

Mesh, open tasks, findings by status, commits, and whether `ACTIVE-<mesh>` stays.

## /driver stop

1. `mission-log <mesh> "mission closed"`.
2. Publish `mission-closed` on `mesh.<mesh>.tester`.
3. `fabric_setPresence({ visible: false })`.
4. Remove `~/.agent-mesh/missions/ACTIVE-<mesh>` only.
5. `tmux kill-session` each `tester-<mesh>-*`. Leave other meshes alone.
6. Tell Dennis this driver session can be closed (`/exit`, or `tmux kill-session -t driver-<mesh>`).
