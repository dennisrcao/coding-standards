```yaml
description: Run every long-lived dev process (Vite frontend, docs site, watchers) inside a named, detached tmux session so any Claude Code instance — regardless of cwd or window — can read its live output. One instance starts it; all instances read it via `tmux capture-pane`.
globs:
  - "**/.claude/commands/*Start*.md"
  - "**/.claude/commands/*Stop*.md"
alwaysApply: false
```

# Shared dev servers via named tmux sessions

> **Reference only — operator / machine-local.** Session names and port tables below are one machine's
> layout, not portable policy.

A normal foreground `npm run dev` is **trapped** in the terminal of the one Claude
Code instance that launched it. A second instance — different repo, different
window, different cwd — can't see its logs, can't tell if it's already running,
and will happily try to start a duplicate on the same port.

The fix: never run a long-lived dev process in the foreground. Run it in a
**named, detached tmux session**. tmux keeps the session alive independent of any
terminal, so the output becomes a **shared, append-only log** that every instance
can read on demand. **One instance starts it; all instances read it.**

> This is the process-output sibling of [`060-playwright-mcp-isolation`](060-playwright-mcp-isolation.md):
> 060 isolates the *browser profile* so N instances don't fight; this isolates the
> *dev-server lifecycle* so N instances can *share* one server's logs. Same goal —
> make many concurrent Claude Code instances coexist cleanly.

## Why tmux (not `&`, not `nohup`, not a background Bash task)

| Approach | Problem |
|----------|---------|
| Foreground `npm run dev` | Output visible only to the launching instance; blocks its shell. |
| `npm run dev &` / `nohup` | Survives, but output is unaddressable — no clean way for *another* instance to tail just that process's stdout. |
| Background Bash tool task | Scoped to the one Claude session that spawned it; a sibling instance can't attach. |
| **Named tmux session** | **Addressable by name from anywhere** (`-t <session>`), survives detach, and `capture-pane` reads the scrollback without attaching or disturbing it. |

## The pattern

Each shared process is a `*_Start` / `*_Stop` slash-command pair in
`~/.claude/commands/`. The Start command is built from four fixed constants:

- **Session** — stable, unique name (`studio`, `studio2`, `docs`).
- **Window** — `web` (one window per process; add more for multi-process sessions).
- **Port** — fixed per session so collisions are detectable.
- **Dir** — absolute path to the project (commands run from any cwd, so never relative).

### 1. Start — idempotent, with pre-flight checks

```bash
# Pre-flight 1: already running? Read its tail instead of starting a duplicate.
tmux has-session -t studio 2>/dev/null && echo "SESSION_EXISTS" || echo "NO_SESSION"
tmux capture-pane -t studio:web -p -S -20   # if EXISTS — look for "ready in" / "Local: http://localhost:5173"

# Pre-flight 2: port free? (catches a non-tmux process squatting the port)
lsof -ti:5173 2>/dev/null && echo "PORT_IN_USE" || echo "PORT_FREE"

# Start: detached session → window → send the dev command into it
tmux new-session -d -s studio -n web -x 220 -y 50
tmux send-keys -t studio:web 'cd /Users/<you>/Desktop/<Repo>/frontend && npm run dev' Enter

# Verify
sleep 4 && tmux capture-pane -t studio:web -p -S -20   # expect "ready in" / "Local: http://localhost:5173/"
```

Idempotency is the whole point: if the session is healthy, **stop and report — do
not create a duplicate.** Only kill + recreate if it's crashed.

### 2. Read — from any instance, without attaching

```bash
tmux capture-pane -t studio:web -p -S -100   # last 100 lines of scrollback, non-destructive
```

`-p` prints to stdout, `-S -N` includes N lines of history. This is read-only and
safe to run from any instance at any time — it does not steal focus or interrupt
the server. A human can also `tmux attach -t studio` (detach with `Ctrl-b d`).

### 3. Stop — kill the session, free the port

```bash
tmux kill-session -t studio 2>/dev/null
lsof -ti:5173 | xargs kill -9 2>/dev/null   # belt-and-suspenders: reclaim the port
```

## Currently configured

| Session | Port | Process | Dir | Commands |
|---------|------|---------|-----|----------|
| `studio`  | 5173 | studio-app frontend (Vite)   | `studio-app/frontend`   | `/APP_Start` · `/APP_Stop` |
| `studio2` | 5174 | studio-app-2 frontend (Vite) | `studio-app-2/frontend` | `/APP2_Start` · `/APP2_Stop` |
| `docs`    | 9000 | docs-hub diagram site     | `docs-hub/site`      | `/APP_DocsStart` · `/APP_DocsStop` |
| `diao`    | — (IPC) | Diào Ableton extension host (`npm start`) | `ableton-extension-diao` | `/DIAO_Start` · `/DIAO_Logs` · `/DIAO_Stop` |

Each parallel checkout gets its **own session name and port** so they never collide.

**No-port processes** (the Ableton extension host, Python builds like `qie-build`) talk over
IPC/stdout rather than a TCP port — they drop the `lsof` port pre-flight and pair Start with a
`*_Logs` / `*-logs` reader (`tmux capture-pane`) instead of a port check.

## Bonus — the tmux window doubles as a console-log sink

For Vite frontends, `server.forwardConsole` (in `vite.config.ts`) mirrors the
browser's `console.*` and unhandled errors to the dev-server stdout. Since that
stdout lives in the tmux window, **any** browser hitting the dev origin — manual
Chrome, Playwright MCP, other automation — lands its client console in the shared
stream. Smoke-test agents should read logs from `capture-pane` rather than
re-collecting via browser-only console APIs. Lines are prefixed
`[vite] (client) [console.error] …`.

## How to apply — add a new shared process

1. Pick a **unique session name** and a **fixed free port**.
2. Copy `~/.claude/commands/APP_Start.md` → your new `*_Start.md`; swap the four
   constants (Session / Window / Port / Dir). Use **absolute paths** — the command
   must run from any cwd.
3. Copy the matching `*_Stop.md`.
4. Keep both pre-flight checks (session-exists, port-in-use) so re-running Start is
   always safe.
5. If multiple instances run parallel checkouts of the same repo, give **each** its
   own session + port (the `studio` / `studio2` split is the worked example).
```
