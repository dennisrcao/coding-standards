---
description: Launch a mesh's wakeable Fabric driver in tmux — runs driver-up <mesh> (driver-next inside). Use for implement/Playwright loops; keep /driver in Cursor for plan and one-shot dispatch.
argument-hint: "<mesh>  e.g. core-2"
allowed-tools: Bash(~/.agent-mesh/bin/driver-up:*), Bash(~/.agent-mesh/bin/mesh-status:*), Bash(tmux:*), Bash(sleep:*)
---

`$ARGUMENTS`

# /driver-up — start a tmux driver from Cursor

Cursor Fabric is **pull mode**: tester `done` does not start a new chat turn. This command starts
the **tmux** driver (`driver-<mesh>`) that **does** wake on replies (`/driver-next`).

1. The first word of `$ARGUMENTS` is the mesh (`core-1`, `calendar-1`, …). If it's missing and
   `FABRIC_MESH` is set, use that. Otherwise ask.
2. Run `~/.agent-mesh/bin/driver-up <mesh>` and show its output verbatim. If it says the driver is
   already running, say so and stop. Don't kill anything.
3. `sleep 20`, then `tmux capture-pane -p -t driver-<mesh> -S -15`, so Dennis sees `/driver-next
   <mesh>` started.
4. `~/.agent-mesh/bin/mesh-status <mesh>`, to show the driver row and any testers.

Report: session `driver-<mesh>`, and `tmux attach -t driver-<mesh>` to talk to it. Don't run
`/driver` for implement loops in this Cursor tab — attach tmux instead.
