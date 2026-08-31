Stop the shared Playwright MCP server by killing its tmux session and freeing port 8931.

## Constants
- Session: `playwright` (window `mcp`)
- Port: `8931`

Stopping the server disconnects every Claude Code session using it, and the
browser window closes with the last client. Sessions do not reconnect on their
own — after `/PLAYWRIGHT-start` they must be restarted to pick the server back up.
Prefer closing your own tabs over stopping the server; reach for this only for a
genuine reset or when the server is wedged.

## Step 1: Kill the tmux session
```bash
tmux kill-session -t playwright 2>/dev/null && echo "SESSION_KILLED" || echo "NO_SESSION"
```

## Step 2: Port-based fallback cleanup
The node process may linger after the session dies. Force-kill anything on 8931:
```bash
lsof -ti:8931 | xargs kill -9 2>/dev/null && echo "PORT_CLEANED" || echo "PORT_ALREADY_FREE"
```

## Step 3: Verify
```bash
tmux has-session -t playwright 2>/dev/null && echo "WARNING: Session still exists" || echo "Session confirmed dead"
lsof -ti:8931 2>/dev/null && echo "WARNING: Port 8931 still in use" || echo "Port 8931 confirmed free"
ps -eo pid=,args= | awk '/@playwright\/mcp\/cli\.js/ && !/awk/ {c++} END {print c+0}'
```
The last number should be `0`. Anything higher means a server survived outside the
tmux session — find it with `ps aux | grep "[@]playwright/mcp/cli.js"` and report
the PID before killing it.

## Instructions
- Run Steps 1, 2, and 3 sequentially.
- Report based on results:
  - SESSION_KILLED + PORT_CLEANED/FREE: "Stopped the shared Playwright MCP server and freed port 8931"
  - NO_SESSION + PORT_CLEANED: "No tmux session found, but killed an orphan process on port 8931"
  - NO_SESSION + PORT_ALREADY_FREE: "Nothing was running"
  - Any WARNING in Step 3: report it as an issue
- This command is safe to run multiple times (idempotent).
