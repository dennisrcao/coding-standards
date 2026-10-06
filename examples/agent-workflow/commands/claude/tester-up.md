---
description: Launch a Fabric tester in tmux from any Claude tab — runs tester-up <mesh> <scope>. This tab is only the launcher; the tmux session is the tester.
argument-hint: "<mesh> <scope> [restart]  e.g. calendar-1 a, core-1 a restart"
allowed-tools: Bash(~/.agent-mesh/bin/tester-up:*), Bash(~/.agent-mesh/bin/tester-restart:*), Bash(tmux:*), Bash(sleep:*), Bash(cat:*), mcp__fabric__fabric_discover
---

`$ARGUMENTS`

# /tester-up — start a tmux tester from this tab

This tab cannot be a tester (a Claude tab inside Cursor cannot receive Fabric). It can start one.

1. Parse `$ARGUMENTS`: first word is the mesh (`calendar-1`, `core-1`, …); second is the scope
   (`a`, `b`, …). If a later word is `restart`, use `tester-restart` instead of `tester-up`. If
   mesh is missing and `FABRIC_MESH` is set, use that.
2. Run `~/.agent-mesh/bin/tester-up <mesh> <scope>` (or `tester-restart <mesh> <scope>`).
   Show its output verbatim. If it says the tmux session already exists, say so and stop; do not
   kill anything unless `restart` was asked.
3. `sleep 20`, then `tmux capture-pane -p -t tester-<mesh>-<scope> -S -15` and show the last
   lines so Dennis sees the session came up and `/tester <mesh> <scope>` started.
4. `fabric_discover` and confirm a `tester-<mesh>-<scope>-*` name is present (filter
   `meta.core`). If not after 60 s, show the pane again; the usual causes are no
   `ACTIVE-<mesh>` (`/driver calendar-1` in Cursor first) or the checkout not on the mission branch.

Report: session `tester-<mesh>-<scope>`, Fabric name, mission path, and
`tmux attach -t tester-<mesh>-<scope>` to watch.
Do not run `/tester` here yourself.
