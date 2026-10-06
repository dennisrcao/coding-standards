---
description: Bounded driver↔tester plan debate on Fabric until plan-agree or max rounds. Requires tmux testers on the mesh.
argument-hint: "<mesh> [plan-path] [wait | no-wait]  e.g. /argue calendar-1 | /argue core-1 ~/Desktop/docs-hub/.../plan.md wait"
allowed-tools: Bash(git:*), Bash(gh:*), Bash(pwd), Bash(ls:*), Bash(cat:*), Bash(grep:*), Bash(find:*), Bash(mkdir:*), Bash(date), Bash(tmux:*), Read, Grep, Glob, Edit, Write, Shell, mcp__fabric__*, mcp__user-fabric__*
---

## Context (auto-collected)

- Now: !`date '+%Y-%m-%d %H:%M %Z'`
- FABRIC_MESH: !`printf '%s\n' "${FABRIC_MESH:-}"`
- Mesh pointers: !`ls -1 ~/.agent-mesh/missions/ACTIVE-* 2>/dev/null | grep -v '^.*ACTIVE-$' || echo "(none)"`
- Known meshes: !`~/.agent-mesh/bin/mesh-list 2>/dev/null | tail -n +3 || echo "(run link-slash-commands.sh)"`
- Fabric peers: !`command -v fabric_discover >/dev/null 2>&1 && fabric_discover 2>/dev/null | head -20 || echo "(fabric MCP not available in this session)"`

`$ARGUMENTS`

---

# /argue — plan debate on a driver mesh

You are the **driver**. Run the bounded plan-debate loop on **one** mesh until
testers `agree` or max rounds exhaust. Protocol:
`commands/shared/argue-protocol.md` (read it).

**Not** `/debate` (headless `claude -p`). **Not** `/ask` (one volley to the other
agent's binary). **Not** a substitute for `/driver` implementation work — only
plan critique and revision.

## Resolve inputs

1. **Mesh** — first token in `$ARGUMENTS`, else `FABRIC_MESH`, else stop and ask.
   Never infer from focused folder.
2. **Plan path** — next absolute path in `$ARGUMENTS`, else mission `planPath` /
   `**Plan:**` from `~/.agent-mesh/missions/ACTIVE-<mesh>`, else stop and ask.
3. **Wait mode** — default **`wait`** unless `$ARGUMENTS` contains `no-wait`.

```text
CHECKOUT=$(~/.agent-mesh/bin/resolve-checkout <mesh>)
MESH=$(~/.agent-mesh/bin/resolve-checkout --core <mesh>)
```

## Before the loop

1. Read `ACTIVE-<mesh>` mission. Plan must exist on disk.
2. `fabric_identity` — if down, stop (this command needs Fabric).
3. `fabric_setPresence({ visible: true, meta: { role: "driver", core: mesh, status: "arguing" } })`.
4. `fabric_subscribe({ channel: "mesh.<mesh>.driver" })`.
5. `fabric_drain({ channel: "mesh.<mesh>.driver" })`.
6. `fabric_discover` — filter `meta.core === mesh`. Need at least one
   `tester-<mesh>-*`. If none: tell Dennis `tester-up <mesh> a` in Terminal.

## Run one debate chain

Follow **argue-protocol.md** § "One `/argue` turn" for each pass:

- Ledger: `<planPath>.argue.md`
- Publish `plan-critique` (round 1) or `plan-revise` (later rounds)
- Collect `plan-review` from each rostered scope
- Verify claims → update ledger → edit plan for CONFIRMED only
- All agree → `plan-agree` on `mesh.<mesh>.tester`, append mission `## Log`
- Max rounds (3) with OPEN claims → `## ⚠ Unresolved after /argue` on the plan,
  stop for user

In **`wait`** mode, use `fabric_wait({ channel: "mesh.<mesh>.driver", timeout_ms: 55000 })`
up to **5** consecutive empty waits per collection phase, same cap as `/driver`.

In **`no-wait`**, publish, drain once, report what arrived, tell user to run
`/argue <mesh> wait` to continue.

## Report

Mesh, plan path, round, ledger claims table (post-verification), plan edits
applied, each tester's verdict, whether `plan-agree` was sent or debate is
blocked on OPEN claims.

## Related

| Command | Use when |
|---|---|
| `/argue` | Plan on a live mesh; testers in tmux |
| `/debate` | No mesh; bounded `claude -p` rounds + ledger |
| `/ask` | One headless critique; verify yourself |
| `/driver` | Implement, retest, merge prep after plan is agreed |
