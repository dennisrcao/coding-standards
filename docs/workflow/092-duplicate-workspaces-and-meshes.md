```yaml
description: This machine opens the same multi-root workspace twice (TV + laptop). Mesh is /driver <slug>, not the focused folder.
globs:
alwaysApply: false
```

# Duplicate workspaces and per-core meshes

**Status:** reference. Companion to
[091-slash-commands-claude-vs-cursor.md](091-slash-commands-claude-vs-cursor.md)
(many clones, one clone per folder) and the standing protocol
`driver-and-testers-on-fabric.md` (a separate repo).

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

**`/driver <mesh>`.** Slugs match `app-multi.code-workspace` (`core-1`,
`calendar-1`, `portfolio`, …). Not the focused folder, not the window title.

| | |
|---|---|
| Pointer | `~/.agent-mesh/missions/ACTIVE-<mesh>` (no global `ACTIVE`) |
| Channels | `mesh.<mesh>.driver` / `mesh.<mesh>.tester` |
| Testers | `tester-up calendar-1 a` → tmux `tester-calendar-1-a` |
| Registry | `mesh-list` — all slugs, checkouts, ports |
| Optional launch | `mesh-cursor calendar-1` sets `FABRIC_NAME` / `FABRIC_MESH` |

`/driver` with no mesh is illegal when two meshes can be live. Wrong mesh →
`/driver stop` that mesh and start the other. Do not `rebind`.

A Claude tab inside Cursor is not a tester (see the protocol). Playwright is
still one MCP on `:8931` — two meshes at once will steal tabs
([060](060-playwright-mcp-isolation.md)).
