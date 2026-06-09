```yaml
description: Give every repo its own Playwright MCP browser profile via a committed per-repo .mcp.json, so multiple Claude Code instances can drive Playwright at the same time without fighting over a single shared Chrome profile.
globs:
  - "**/.mcp.json"
alwaysApply: false
```

# Playwright MCP — per-repo browser isolation

When several Claude Code instances are open at once (different repos, different
windows) and each one smoke-tests its frontend through **Playwright MCP**, they
collide. The collision is **not** about ports — it's the browser profile.

## Why they collide

The `playwright` MCP server is defined **globally** in `~/.claude.json`
(`mcpServers.playwright`), so every instance inherits the same launch command:

```json
"playwright": { "command": "npx", "args": ["@playwright/mcp@latest"] }
```

Because it's a **stdio** server, each instance already spawns its *own*
Playwright MCP process — they don't share a server or a port. The contention is
one level down: with no args, Playwright MCP launches Chrome against a **single
shared persistent profile** (`~/Library/Caches/ms-playwright/mcp-chrome-*`).
Chrome enforces **one process per `user-data-dir`**, so the second instance
either fails to launch or hijacks the window the first one is mid-test in. That
is the "competing for control" symptom.

> Dev-server ports are already separated (5173 / 5174 / 9000 / …) — that part is
> fine. The fix here is isolating the **browser profile**, not the port.

## The fix — a committed per-repo `.mcp.json`

Drop a `.mcp.json` at the repo root that **overrides** the global `playwright`
server with a repo-specific one. Keep the server name `playwright` so every
existing `mcp__playwright__*` tool and `*_TestFrontend` skill keeps working
unchanged — **project scope wins over the global user scope** for a same-named
server. Point it at a per-repo `--user-data-dir` (and `--output-dir`) so the
profiles can never lock each other out:

```json
{
  "mcpServers": {
    "playwright": {
      "type": "stdio",
      "command": "npx",
      "args": [
        "@playwright/mcp@latest",
        "--user-data-dir", "/Users/<you>/.cache/pw-mcp/<RepoName>/profile",
        "--output-dir",    "/Users/<you>/.cache/pw-mcp/<RepoName>/output"
      ],
      "env": {}
    }
  }
}
```

Each repo gets its own logged-in Chrome profile that persists across sessions and
is invisible to every other repo. N instances → N independent browsers.

Currently configured: `studio-app`, `studio-app-2`, `studio-app-3`,
`studio`, `docs-hub`.

### How to apply — extend to a new repo

1. Pick a profile dir keyed by the repo name and create it:

   ```bash
   REPO=My-New-Repo
   mkdir -p "$HOME/.cache/pw-mcp/$REPO/profile" "$HOME/.cache/pw-mcp/$REPO/output"
   ```

2. Create `<repo>/.mcp.json` with the snippet above, substituting your absolute
   home path and `$REPO` for both `--user-data-dir` and `--output-dir`. **Use
   absolute paths** — MCP configs do not expand `~`.

3. Commit `.mcp.json`. On first launch in that repo, Claude Code prompts once to
   trust the project MCP server — approve it.

That's it. The global `playwright` server in `~/.claude.json` stays as the
fallback for any repo that doesn't ship its own `.mcp.json`.

### Caveat — don't nuke other repos' profiles

Old recovery snippets that clear "stale" Playwright state are now **wrong and
destructive**:

```bash
# ❌ clears the GLOBAL profile (no longer where per-repo profiles live)
rm -rf ~/Library/Caches/ms-playwright/mcp-chrome-*
# ❌ kills EVERY repo's Playwright browser, not just this repo's
pkill -f playwright-mcp; pkill -f Chromium
```

Per-repo profiles now live under `~/.cache/pw-mcp/<RepoName>/profile`. To reset
**only the current repo**, clear that one dir instead:

```bash
rm -rf ~/.cache/pw-mcp/<RepoName>/profile && \
  mkdir -p ~/.cache/pw-mcp/<RepoName>/profile
```

Any `*_TestFrontend` skill that still references the global `mcp-chrome-*` path
or an unscoped `pkill Chromium` should be updated to the per-repo path above.

### Alternative isolation modes (for reference)

- **`--isolated --storage-state <file>`** — fresh in-memory browser each run with
  auth injected from a saved Playwright storageState JSON. Best for heavy
  parallelism (zero shared on-disk state); use only if your saved auth blob is a
  real storageState file.
- **`--port <n>`** — runs Playwright MCP as a standalone HTTP server you connect
  to via `url`. Not needed for stdio isolation; only useful if you want to attach
  to / watch a specific browser independently.
