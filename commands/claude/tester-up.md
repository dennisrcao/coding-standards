---
description: Launch a Fabric tester in tmux from any Claude tab — runs `tester-up <scope>` (or `tester-restart <scope>` with `restart`). This tab is only the launcher; the tmux session is the tester.
argument-hint: "<scope> [restart]   e.g. a, b, a restart"
allowed-tools: Bash(~/.agent-mesh/bin/tester-up:*), Bash(~/.agent-mesh/bin/tester-restart:*), Bash(tmux:*), Bash(sleep:*), Bash(cat:*), mcp__fabric__fabric_discover
---

`$ARGUMENTS`

# /tester-up — start a tmux tester from this tab

This tab cannot be a tester (a Claude tab inside Cursor cannot receive Fabric). It can start one.

1. Parse `$ARGUMENTS`: first word is the scope (`a`, `b`, …); if a second word is `restart`, use
   `tester-restart` instead of `tester-up`.
2. Run `~/.agent-mesh/bin/tester-up <scope>` (or `~/.agent-mesh/bin/tester-restart <scope>`).
   Show its output verbatim. If it says the tmux session already exists, say so and stop; do not
   kill anything unless `restart` was asked.
3. `sleep 20`, then `tmux capture-pane -p -t tester-<scope> -S -15` and show the last lines so
   Dennis sees the session came up and `/tester <scope>` started.
4. `fabric_discover` and confirm a `tester-<scope>-*` name is present. If not after 60 s, show the
   pane again; the usual causes are no ACTIVE mission (`/driver core-N` in Cursor first) or the
   checkout not on the mission branch.

Report: session name, Fabric name, mission path, and `tmux attach -t tester-<scope>` to watch.
Do not run `/tester` here yourself.
