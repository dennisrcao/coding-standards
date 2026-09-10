# /debate — argue a plan with Claude Code until you agree

`/ask` is one volley. `/debate` runs up to **three** bounded rounds of `/ask` against a plan,
carries the argument in a ledger file between rounds, and stops the moment the two of you agree
or the objections run out. You are the judge in every round: nothing enters the ledger as
CONFIRMED until you have opened the file it names.

Run it from the specific repo clone under review (`app-monorepo-1`..`-7`, `studio`/`studio-2`,
`claw-calendar`/`-2`/`-3`) — each is on its own branch. Reviewing the wrong clone reviews the
wrong branch.

## When to use

The user asked for a back-and-forth, "argue it out", "keep going until you agree", or a
second opinion they want pushed past the first answer. Do not run this unprompted — every
round is one `claude -p` call on the user's Claude quota. For a single cold read use `/ask`.

## Why each round is bounded

An unbounded headless `claude -p` on a plan-review prompt spawns subagents, shells out, and
takes seven-plus minutes — longer than this shell tool will wait, so it looks like a hang even
though it finishes. Plan mode does not stop that; the flags below do. Do not drop them.

| Flag | Why |
|---|---|
| `--permission-mode plan` | read-only |
| `--max-turns 12` | hard stop on wandering |
| `--disallowedTools "Agent,Task,TaskOutput"` | no subagents — the single biggest time sink |
| `--strict-mcp-config --mcp-config '{"mcpServers":{}}'` | no MCP servers; also keeps the headless run off Fabric, where it would otherwise join as a second `claude` identity |
| `< /dev/null` | never wait on stdin |

Never use `--dangerously-skip-permissions`.

## The ledger

One file next to the plan: `<plan-file>.debate.md`. It is the whole memory of the debate —
Claude Code remembers nothing between rounds, so every round's prompt is built from it.

```markdown
# Debate: <plan title>
Plan: <absolute path>   Clone: <absolute path>   Round: N of 3

## Claims
| # | Claim | Status | File:line | Evidence |
| 1 | ... | OPEN / CONFIRMED / REFUTED / MISREAD | ... | one line |

## Plan edits applied
- round 1: ...

## Round log
- round 1: VERDICT=... · N new claims · M confirmed · K refuted
```

Status is yours to set, not Claude Code's. Its output proposes; your verification disposes.

## One round

1. Build the prompt from the ledger. Inline the **complete current plan** and the **complete
   claims table** — paths are not enough, it has no context. Then:

   > For each OPEN claim: CONFIRMED or REFUTED, with file and line, what breaks, and the input
   > or state that triggers it. Raise a new claim only if you can name a file and line; if you
   > cannot, say so rather than speculating. If a step is sound, say so — do not manufacture
   > objections. End with one line `VERDICT: AGREE` or `VERDICT: AGREE_WITH_CHANGES` or
   > `VERDICT: DISAGREE`, then a table `Claim | Status | File:line | Evidence`.

2. Run it in the background to a file so the shell wait is never the limiter:

   ```bash
   cd "<clone under review>" && OUT="<plan-file>.round-N.txt" && \
   nohup claude -p --permission-mode plan --max-turns 12 \
     --disallowedTools "Agent,Task,TaskOutput" \
     --strict-mcp-config --mcp-config '{"mcpServers":{}}' \
     --output-format text \
     "$(cat <<'PROMPT'
   <prompt>
   PROMPT
   )" < /dev/null > "$OUT" 2>&1 &
   ```

   Add `--model opus` for the strongest review; omit for the default.

3. Poll with short separate commands — `sleep 45; grep -c '^VERDICT:' "$OUT"; tail -c 3000 "$OUT"` —
   at most ten times. If no `VERDICT:` line after ten polls, `pkill -f "claude -p --permission-mode plan"`,
   log the round as TIMED_OUT, and stop the debate; tell the user.

4. **Verify before recording.** Show the user the raw response. Then for every claim it made or
   re-argued, open the file at the line it names and decide CONFIRMED / REFUTED / MISREAD /
   UNVERIFIABLE yourself. Print that table. Only then update the ledger. Do not soften a
   refutation into "both views have merit" — if it is wrong, say so.

5. Edit the plan only for CONFIRMED claims. Record each edit under "Plan edits applied" with
   the round number.

## Stop conditions — check after every round, in this order

1. `VERDICT: AGREE` → done. Say so and stop.
2. No claim is OPEN after your verification → done, even if the verdict said otherwise; the
   remaining disagreement is unfounded and you have the file:line to show it.
3. Round 3 finished → stop regardless. List the OPEN claims for the user as the unresolved set.
   The user decides, not a fourth round.

Never exceed three rounds. Two models will manufacture objections indefinitely if allowed to.

## Report

Rounds run, final verdict, the ledger table, and the plan edits applied. If it stopped on
condition 3, lead with the unresolved claims. Do not present Claude Code's last verdict as the
outcome — the outcome is the ledger after your verification.
