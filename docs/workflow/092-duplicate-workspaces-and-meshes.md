```yaml
description: This machine opens the same multi-root workspace twice (TV + laptop). Mesh is /driver core-N, not the focused folder.
globs:
alwaysApply: false
```

# Duplicate workspaces and per-core meshes

**Status:** reference. Companion to
[091-slash-commands-claude-vs-cursor.md](091-slash-commands-claude-vs-cursor.md)
(many clones, one clone per folder) and the standing protocol
[`driver-and-testers-on-fabric.md`](../../../agent-mesh/docs/development/driver-and-testers-on-fabric.md).

## The setup this machine actually runs

The multi-root file `~/Desktop/app-multi.code-workspace` is opened
**twice**: a Cursor window on the TV and a Cursor window on the laptop. Both
see app-monorepo-1 … 7, `docs-hub`, studio, calendar, and the rest.

[091](091-slash-commands-claude-vs-cursor.md) already says there are many clones
and one clone per folder (`app-monorepo-1` … `-7`). It does **not** cover two
windows of the **same** `.code-workspace`. `/driver` used to say "which folder is
focused does not matter" — true for picking a folder inside one window, and
**false** as a way to isolate two windows. They used to share Fabric name
`cursor`, `~/.agent-mesh/missions/ACTIVE`, and `role.tester`.

## What picks the mesh

**`/driver core-N`.** Not the focused folder, not the window title.

| | |
|---|---|
| Pointer | `~/.agent-mesh/missions/ACTIVE-core-N` (no global `ACTIVE`) |
| Channels | `mesh.core-N.driver` / `mesh.core-N.tester` |
| Testers | `tester-up core-N a` → tmux `tester-core-N-a` |
| Optional launch | `mesh-cursor core-N` sets `FABRIC_NAME` / `FABRIC_MESH` |

`/driver` with no core is illegal when two meshes can be live. Wrong core →
`/driver stop` that mesh and start the other. Do not `rebind`.

A Claude tab inside Cursor is not a tester (see the protocol). Playwright is
still one MCP on `:8931` — two meshes at once will steal tabs
([060](060-playwright-mcp-isolation.md)).
