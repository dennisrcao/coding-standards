Start the shared Playwright MCP server in a persistent tmux session so every Claude Code instance across every repo drives ONE browser window. Each session claims its own tab — a step the session must take, see "Working in a shared window".

## Constants
- Session: `playwright`
- Window `mcp` — Playwright MCP over HTTP, port `8931`
- Endpoint every `.mcp.json` points at: `http://127.0.0.1:8931/mcp`
- Shared profile: `$HOME/.cache/pw-mcp/shared/profile`
- Output dir: `$HOME/.cache/pw-mcp/shared/output`

One server, one browser, one window. Every Claude Code session in any repo is an
HTTP client of this server, and each client tracks its own current tab.

**The server does not hand a new client a tab of its own.** A client with no tab
adopts whatever page is already open, so two sessions that both start with
`browser_navigate` end up driving the same tab, silently. Parallel sessions work,
but they need one convention — see "Working in a shared window" below.

The browser is **not** launched when this command runs — it launches on the first
client's first browser tool call, and closes when the last client disconnects.
That is the server's own lifecycle; do not try to manage the browser here.

## Prerequisite
`tmux` must be installed. If `which tmux` returns nothing, stop and tell the user.

## Pre-flight Check 1: Is the tmux session already running?
```bash
tmux has-session -t playwright 2>/dev/null && echo "SESSION_EXISTS" || echo "NO_SESSION"
```

If `SESSION_EXISTS`, check the server process is actually alive inside it:
```bash
lsof -ti:8931 >/dev/null 2>&1 && echo "SERVER_ALIVE" || echo "SERVER_DEAD"
```
- `SESSION_EXISTS` + `SERVER_ALIVE` → the server is running. Report and stop. Do
  not create a duplicate; a second server would mean a second window, which is the
  entire problem this command exists to prevent.
- `SESSION_EXISTS` + `SERVER_DEAD` → the server crashed but tmux is still open.
  Kill the stale session and continue: `tmux kill-session -t playwright`

## Pre-flight Check 2: Is port 8931 used by something else?
```bash
lsof -ti:8931 2>/dev/null && echo "PORT_IN_USE" || echo "PORT_FREE"
```
If in use without a matching tmux session, another process owns it. Report the PID
and process (`lsof -i:8931 | head -5`) and ask the user before killing it.

## Create Session and Start Server

### Step 1: Create the tmux session
```bash
tmux new-session -d -s playwright -n mcp -x 200 -y 50
```

### Step 2: Start the server
Sent with `send-keys` (not inline) so the shell survives a crash and you can still
read the error.

Two flags here are load-bearing — do not "simplify" them:

- **`node …/@playwright/mcp/cli.js` rather than the `playwright-mcp` bin wrapper.**
  Several repos ship a browser-reset step containing `pkill -f playwright-mcp`.
  That pattern matches the bin wrapper's path but not `@playwright/mcp/cli.js`
  (no hyphen), so this server survives another repo's reset instead of dying with it.
- **`--shared-browser-context`, never `--isolated`.** Both make the server reuse
  one browser, but `--isolated` hands each client a *new context* — which Chrome
  renders as a new window. `--shared-browser-context` hands every client
  `browser.contexts()[0]`, giving one window in which every client can open tabs.
- **`--browser chrome`** resolves to `/Applications/Google Chrome.app/…/Google Chrome`,
  which likewise does not match the `pkill -f Chromium` in those same reset steps.
- **`--host 127.0.0.1` and `--allowed-hosts`.** Both were found the hard way and
  are required, not decorative:
  - Without `--host`, the server binds **`[::1]` (IPv6 only)**. A client dialing
    `http://127.0.0.1:8931` gets connection refused — silently, as a dead MCP server.
  - The host check is a **literal string match** against `localhost:8931`
    regardless of what it bound to, so a request that reaches it over `127.0.0.1`
    is answered `403 Access is only allowed at localhost:8931`. Listing both forms
    makes either address work no matter how a client resolves `localhost`.

```bash
tmux send-keys -t playwright:mcp 'node "$HOME/.nvm/versions/node/v22.23.1/lib/node_modules/@playwright/mcp/cli.js" --port 8931 --host 127.0.0.1 --allowed-hosts localhost:8931,127.0.0.1:8931 --shared-browser-context --browser chrome --user-data-dir "$HOME/.cache/pw-mcp/shared/profile" --output-dir "$HOME/.cache/pw-mcp/shared/output" --output-max-size 104857600' Enter
```

### Step 3: Wait and verify
```bash
for i in $(seq 1 20); do lsof -ti:8931 >/dev/null 2>&1 && break; sleep 1; done
lsof -ti:8931 >/dev/null 2>&1 && echo "SERVER_UP" || echo "SERVER_FAILED"
tmux capture-pane -t playwright:mcp -p -S -20
```

Expect a `Listening on http://localhost:8931` line. If `SERVER_FAILED`, capture
more output and report the error — a wrong node path after an nvm upgrade is the
likeliest cause:
```bash
ls "$HOME/.nvm/versions/node/"*/lib/node_modules/@playwright/mcp/cli.js
```

### Step 4: Confirm exactly one server

Counted with `awk` rather than `grep -c`: a plain `grep -c "[@]playwright..."`
self-matches, because the argv of the shell running the command contains that
literal string. The `[@]` trick only hides the grep process itself, not its parent.
```bash
ps -eo pid=,args= | awk '/@playwright\/mcp\/cli\.js/ && !/awk/ {c++} END {print c+0}'
```
Must be `1`. More than one means a duplicate server is running and users will see
multiple windows — kill the extras.

## Instructions
1. Run Pre-flight Check 1. If the server is healthy, stop and report.
2. Run Pre-flight Check 2. Report any port conflict and ask before killing.
3. Run Steps 1–4 sequentially.
4. Report:
   - "Shared Playwright MCP running in tmux session `playwright` on port 8931"
   - Endpoint: http://127.0.0.1:8931/mcp
   - View logs: `tmux attach -t playwright` (detach with `Ctrl-b d`)
   - Read output without attaching: `tmux capture-pane -t playwright:mcp -p -S -50`
   - Stop with `/PLAYWRIGHT-stop`
5. If any session was already open before the server started, remind the user that
   MCP config and connections are established at session start — those sessions
   must be restarted before they can reach the server.

This command is safe to run multiple times (idempotent).

## Working in a shared window

Every session shares one tab list and one cookie jar.

**Claim a tab before you navigate — this is the one that bites.** A client's
current-tab pointer is per session, but it starts out empty, and `_onPageCreated`
fills an empty pointer with the first page it sees, including pages another session
opened. `browser_navigate` only creates a page when that pointer is empty. So session
A navigates and makes tab 1, session B's first call adopts tab 1, and B then drives
A's tab for the rest of its life, with no error anywhere.

So a session's **first** Playwright action is always:

```
browser_tabs({ action: "new", url: "http://localhost:<your port>/" })
```

`action: "new"` points the pointer at the page it just created; after that plain
`browser_navigate` stays put. Opening a tab never disturbs a session that already
holds one, because the pointer is only auto-filled when empty.

Then:

- **Never close a tab you did not open.** `browser_tabs` lists *every* session's
  tabs, so closing by index can close a tab another agent is mid-test in.
  `action: "select"` is intrusive too — it calls `bringToFront()` and physically
  raises that tab in the window another agent is watching.
- **Do not close your own tab and keep working.** Closing your current tab does not
  leave you with none — the pointer slides to the neighbouring tab, which is somebody
  else's. Claim a fresh one with `action: "new"` first.
- `browser_close` is safe: it tears down only your own backend, and the shared browser
  survives while any other client is attached.

Cookies are still separated by origin, and every checkout serves on a distinct
port, so logins do not bleed between repos.

Full rationale, with the source excerpts:
`docs-hub/projects/coding-standards/docs/process/060-playwright-mcp-isolation.md`.

## Cross-window observability

The server runs in a detached tmux session owned by your user account, not by any
one Claude Code process, so any other instance can read its output without having
started it:

```bash
tmux has-session -t playwright 2>/dev/null && tmux capture-pane -t playwright:mcp -p -S -200
```
