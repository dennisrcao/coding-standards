# /ask — ask the other agent

`/ask` means "ask the other agent". In Cursor that is **Claude Code**; the mirror-image
`/ask` in Claude Code comes back to you. Runs it headlessly — no window needed.

Run it from the specific repo clone under review. These repos are cloned many times over
(`app-monorepo-1`..`-7`, `studio`/`studio-2`, `claw-calendar`/`-2`/`-3`), each on its own
branch. `cd` into the right clone first — reviewing the wrong clone reviews the wrong branch.

## When to use

The user asked you to cross-check with Claude, get a second opinion, or verify a plan
against another model. Do not run this unprompted — it costs the user's Claude quota.

## How

Claude Code starts with **no context from this chat**. It sees only your prompt and the
repo, so the prompt must carry the plan or diff inline — not a reference to it.

```bash
cd "<the clone under review>" && claude -p --permission-mode plan "<your prompt>"
```

- `--permission-mode plan` keeps it read-only. Never use `--dangerously-skip-permissions`.
- Add `--model opus` for the strongest review; omit for the default.
- It may take a minute or two on a large diff. Let it finish.
- One call. Do not retry in a loop. For a multi-round argument use `/debate`, which bounds
  each round (no subagents, no MCP, `--max-turns`) and carries a claims ledger between rounds.

Ask for disagreement, not a summary. Include:

- The plan or diff, complete and inline.
- What specifically to attack.
- "For each objection give the file and line, what breaks, and the input or state that
  triggers it. If you cannot name a file and line, say so rather than speculating. If a
  step is sound, say so — do not manufacture objections."

## Then verify it

Show the user the raw response first. Then **check its claims against the actual code
before accepting any of them.** Claude Code is confidently wrong often enough that an
unverified critique is a liability. For each claim, open the file it names and confirm the
thing it describes exists. Report which claims held up and which did not, with file:line
evidence. Do not soften a refutation into "both views have merit" — if it is wrong, say so.

Work it as **atomic claims, not a verdict**, especially when the critique is long: split it into
a numbered list of falsifiable assertions, give each one CONFIRMED / REFUTED / MISREAD /
UNVERIFIABLE with `file:line` evidence, print that table before touching anything, and edit the
plan only for what survived. If nothing was confirmed, say the plan stands as written. `/ask`
fetches the critique; this step is what refuses to trust it.
