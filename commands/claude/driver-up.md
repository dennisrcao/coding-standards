---
description: Launch a mesh's Fabric driver in tmux from any Claude tab — runs driver-up <mesh>. This tab is only the launcher; the tmux session is the driver, and tester replies wake it.
argument-hint: "<mesh>  e.g. core-1"
allowed-tools: Bash(~/.agent-mesh/bin/driver-up:*), Bash(~/.agent-mesh/bin/mesh-status:*), Bash(tmux:*), Bash(sleep:*)
---

`$ARGUMENTS`

# /driver-up — start a tmux driver from this tab

This tab can't be the driver: a Claude tab inside an editor never hears a tester's reply. It can start
one.

1. The first word of `$ARGUMENTS` is the mesh (`core-1`, `calendar-1`, …). If it's missing and
   `FABRIC_MESH` is set, use that. Otherwise ask.
2. Run `~/.agent-mesh/bin/driver-up <mesh>` and show its output verbatim. If it says the driver is
   already running, say so and stop. Don't kill anything.
3. `sleep 20`, then `tmux capture-pane -p -t driver-<mesh> -S -15`, so Dennis sees `/driver <mesh>`
   started.
4. `~/.agent-mesh/bin/mesh-status <mesh>`, to show the driver row and any testers.

Report: session `driver-<mesh>`, and `tmux attach -t driver-<mesh>` to talk to it. Don't run
`/driver` here yourself.
