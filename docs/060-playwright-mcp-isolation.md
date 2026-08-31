```yaml
description: Run one shared Playwright MCP server for the whole workspace, so every Claude Code session across every repo drives a single browser window and works in its own tab instead of each repo spawning its own browser.
globs:
  - "**/.mcp.json"
alwaysApply: false
```

# Playwright MCP — one shared browser for the workspace

## The rule

There is **one** Playwright MCP server for the entire machine. Every repo's
`.mcp.json` points at it, byte-identical:

```json
{
  "mcpServers": {
    "playwright": {
      "type": "http",
      "url": "http://127.0.0.1:8931/mcp"
    }
  }
}
```

Start it with `/PLAYWRIGHT-start`, stop it with `/PLAYWRIGHT-stop`. Keep the server
name `playwright` so every `mcp__playwright__*` call and every `*_TestFrontend`
skill resolves without per-repo edits.

**Do not** add a per-repo stdio server with its own `--user-data-dir`. That is the
setup this document used to prescribe, and it is what caused the problem below.

## Why this replaced per-repo profiles

The old rule gave each repo its own `playwright-mcp` process and browser profile.
In a multi-root workspace where every tab loads `app-monorepo-1/.mcp.json`, that
produced, measured on 2026-08-31:

- **20 idle `playwright-mcp` processes** (~110 MB each, ≈2 GB) — 4 sessions × 4
  servers, because that one config had accumulated four server entries.
- **Two Chrome windows at once**, on two different profiles.
- Profile collisions: Chromium holds a `SingletonLock` per `--user-data-dir`, so
  two sessions sharing a profile got `Browser is already in use for …`.

The stated reason for keying profiles by port was that studio auth is
origin-scoped `localStorage`. That reason does not survive inspection: **port is
part of the origin**, so `localhost:5173` and `localhost:5174` already have
separate `localStorage` inside a single profile. The split bought nothing the
origin boundary did not already provide.

## How one server yields one window

From `@playwright/mcp` v0.0.79 (`playwright-core/lib/coreBundle.js`):

- `--shared-browser-context` sets a single `sharedBrowserPromise` → **one** browser
  launch total.
- Each connected client receives `browser.contexts()[0]` — the **same** context, so
  one window rather than one window per client.
- Each client still gets its **own `BrowserBackend`**, so every session tracks its
  own current tab. Sessions genuinely run in parallel; one session's navigation
  does not move another's tab.
- Teardown is `if (sharedBrowserPromise && clientCount > 0) return;` — the browser
  survives while any client is attached and closes when the last one leaves. Nothing
  needs to manage the browser lifecycle by hand.

## Flags that are load-bearing

Do not "simplify" these; each was found by a failure.

| Flag | Why |
|---|---|
| `--shared-browser-context` | **Not** `--isolated`. Both reuse one browser, but `--isolated` gives each client a *new context*, which Chrome renders as a new window — the original bug. |
| `--host 127.0.0.1` | Without it the server binds **`[::1]` only**, and a client dialing `127.0.0.1:8931` gets connection-refused, presenting as a dead MCP server. |
| `--allowed-hosts localhost:8931,127.0.0.1:8931` | The host check is a **literal string match** against `localhost:8931` regardless of what was bound, so a request arriving via `127.0.0.1` is answered `403 Access is only allowed at localhost:8931`. |
| `node …/@playwright/mcp/cli.js` | Invoke the module, **not** the `playwright-mcp` bin wrapper. Several repos ship a reset step containing `pkill -f playwright-mcp`; the wrapper's path matches that pattern and the module path does not, so the shared server survives another repo's reset. |
| `--browser chrome` | Resolves to `/Applications/Google Chrome.app/…/Google Chrome`, which likewise does not match the `pkill -f Chromium` in those same reset steps. |

## Working in a shared window

One context means one tab list and one cookie jar.

- **Navigate in your own tab.** Each client's current-tab pointer is already isolated.
- **Never close a tab you did not open.** `browser_tabs` lists *every* session's
  tabs, so closing by index can close a tab another agent is mid-test in.
- **Keep the shared profile lean.** Sign in only to what testing needs. The old
  per-port profiles had accreted live sessions for Gmail, the AWS console, Slack,
  GitHub, Venmo and brokerage accounts; in a browser every repo's agent shares,
  that is a blast radius, not a convenience. Cookies remain separated by origin,
  and each checkout serves on a distinct port, so logins do not bleed between repos.

## Verifying a change to this setup

The failure mode is a *window count*, so test observationally, not by unit test:

```bash
# exactly one server (awk, not grep -c: grep self-matches via the parent shell argv)
ps -eo pid=,args= | awk '/@playwright\/mcp\/cli\.js/ && !/awk/ {c++} END {print c+0}'

# count browsers on the shared profile
ps -eo args= | grep "[G]oogle Chrome.app/Contents/MacOS/Google Chrome " \
  | grep -c "pw-mcp/shared/profile"
```

Drive two sessions in two different repos and confirm the browser count goes
`0 → 1 → 1`, not `0 → 1 → 2`.

## Anti-patterns

- `pkill -f playwright-mcp; pkill -f Chromium` as a "reset". Against a shared server
  this is a workspace-wide kill switch. Use `/PLAYWRIGHT-stop` then
  `/PLAYWRIGHT-start`, or just close your own tabs. (The flag choices above make the
  shared server immune to the copies of this block still living in repo skills.)
- Re-introducing `--user-data-dir` per repo. See the whole first half of this file.
- Committing `.mcp.json` in a repo shared with collaborators who do not run this
  server — they would inherit a Playwright entry pointing at a port nothing is
  listening on. Keep it in `.git/info/exclude` or `.gitignore` there.
