---
description: Design for /argue — a bounded two-round adversarial loop between Claude Code and Cursor that replaces the /ask + /CROSSCHECK pair
status: design approved, not yet implemented
date: 2026-08-27
---

# `/argue` — design

## Summary

`/ask` fetches a critique from the other agent. `/CROSSCHECK` refuses to trust it. They are a
pair, and running them is two manual steps that end after one exchange: the other model states
an objection, we verify it, and the conversation stops there — even when the objection was
refuted and the other model never got to answer the refutation.

`/argue` replaces both with a single command that runs a **bounded two-round argument**: the
opponent objects, we verify every objection against real code, we send back a rebuttal carrying
`file:line` evidence, and the opponent either concedes or produces a counter-example. Objections
that survive that exchange without evidence on either side are named as unresolved rather than
silently dropped.

## Goals

- One command, not two, for "get a second model to attack this and tell me what actually held up".
- Every objection ends in one of five explicit states — never in ambiguity.
- The other model gets to answer our refutation, so a refutation we got wrong is caught.
- Bounded cost: at most two calls to the opponent per invocation.
- Unresolved disagreements survive the session by being written into the plan file.

## Non-goals

- Convergence at any cost. The loop stops at two rounds whether or not everything settled.
- Editing code. `/argue` edits plan markdown only; findings about code go into the plan.
- Committing or pushing. Never, unless separately asked.
- Replacing `/close-out`, `/ship`, or code review. This is about plans and diffs under debate.

---

## File layout

Source of truth is `docs-hub/projects/coding-standards/commands/`, symlinked into
`~/.claude/commands/` and `~/.cursor/commands/` by `scripts/link-slash-commands.sh`.

| Path | Action |
| --- | --- |
| `commands/shared/argue-protocol.md` | **new** — the engine: rounds, verdicts, report, plan edits |
| `commands/claude/argue.md` | **new** — thin wrapper; opponent is `cursor-agent` |
| `commands/cursor/argue.md` | **new** — thin wrapper; opponent is `claude` |
| `commands/claude/ask.md` | **delete** |
| `commands/cursor/ask.md` | **delete** |
| `commands/shared/CROSSCHECK.md` | **delete** |
| `~/.claude/commands/CROSSCHECK.md.bak` | **delete** — stale real file, not a symlink |

`argue-protocol.md` is **not** a slash command and is **not** symlinked. Both wrappers read it
at runtime by absolute path:

```
~/coding-standards/commands/shared/argue-protocol.md
```

### Why thin wrappers plus a shared core

The two existing `ask.md` files have already drifted badly — the Claude copy carries the
clone-resolution step, the transcript-to-disk step and a failure-modes section; the Cursor copy
is a third the length and has none of them. Duplicating the protocol is what caused that.

A single fully shared file was rejected for the reason `link-slash-commands.sh` already states
in its own comments: an agent that misidentifies which side it is on *"would shell out to itself
and return its own reasoning as a second opinion, silently"* — the worst possible failure for
this command, because it is invisible in the output. The wrapper names its opponent's binary
literally, so misidentification is impossible; everything that does not depend on which side you
are on lives in the one shared file and physically cannot drift.

---

## Modes

Determined in Round 0.

| Mode | Trigger | Behavior |
| --- | --- | --- |
| **Argue** | Normal invocation | Full two-round loop against the opponent CLI |
| **Verify-only** | Invoked with a screenshot or pasted critique | Skips both CLI calls; treats the pasted text as Round 1 and verifies it |

Verify-only preserves the `/CROSSCHECK` use case — a critique from ChatGPT, a live Cursor
window, or a screenshot. There is no session to argue back into, so the command must say so
plainly in its report: **"no rebuttal channel — one-way verification."** It must not imply the
opponent conceded anything.

---

## The loop

### Round 0 — resolve

Carried forward verbatim from `claude/ask.md`, which is the highest-value part of the current
command and must not be lost in the rewrite:

- These repos are cloned many times over (`app-monorepo-1`..`-7`, `studio`/`studio-2`,
  `claw-calendar`/`-2`/`-3`, `storyboard-agent`/`-2`/`-3`), each a separate checkout on its own
  branch. Arguing against the wrong clone argues against the wrong branch and every conclusion
  is garbage.
- `pwd` is not sufficient — the session may be running from `~/Desktop`, the parent of all of
  them. Never default to `pwd`. If the clone cannot be resolved from a given path, the enclosing
  git root, or something the user named, **ask**.
- State the resolved clone and branch in one line before spending a call.

Then state, in one line each: what is under review (a given path → the diff → the most recently
touched plan markdown), and which mode.

### Round 1 — the opponent attacks

Read-only, with the session captured so Round 2 can resume it:

```bash
cd "<clone>" && cursor-agent -p --mode ask --trust --output-format json "<prompt>"
```

The opponent starts with **no context from this conversation**. The prompt must carry the plan
or diff inline and complete — never a reference to it.

The prompt demands, verbatim:

> For each objection give: the file and line, what breaks, and the concrete input or state that
> triggers it. If you cannot name a file and line, say so explicitly rather than speculating. If
> a step is sound, say so and move on — do not manufacture objections to seem useful.

Capture the chat id from the JSON for Round 2. Save the raw response under `$TMPDIR/argue/` and
report the path, so it survives compaction.

### Verify

Decompose the response into **atomic, falsifiable claims** — one row per assertion, compound
complaints split apart. Discard unfalsifiable material (style preferences, "consider also…") in
a single line at the end as *unfalsifiable — ignored*.

Then, for each claim: open the real file. Check the thing it describes actually exists — other
models hallucinate file paths, hook names and signatures constantly. Run something where
possible (tests, typecheck, `git log -S`). Check the plan actually says what the critique says
it says; a large share of cross-model objections attack a misreading.

| Verdict | Meaning |
| --- | --- |
| **CONFIRMED** | Verified true. The plan is wrong or incomplete here. |
| **REFUTED** | Verified false, with the specific evidence that kills it. |
| **MISREAD** | True of other code, or of a plan that is not this one. |
| **UNVERIFIABLE** | Cannot be settled from the codebase — a product or design call. Say whose. |
| **OPEN** | Not closed by evidence from either side. |

**The evidence rule — the load-bearing rule of this command.** An objection may only leave the
board via `file:line` evidence, real command output, or a commit SHA. Disagreement without
evidence does not close an objection; it becomes OPEN. "Probably fine" is not a verdict.

### Round 2 — rebut into the same session

```bash
cursor-agent --resume <chatId> -p --mode ask --trust "<rebuttal>"
```

Resuming means the opponent argues with its own reasoning rather than re-reading a wall of
text. The rebuttal contains:

- Concessions, named explicitly — every CONFIRMED claim, stated as conceded.
- Refutations, each with its `file:line` evidence.
- This instruction: *"For each refutation: concede it, or give a `file:line` counter-example. Do
  not repeat an objection without new evidence."*

**Fallback:** if the chat id cannot be captured or `--resume` fails, make one stateless call
carrying Round 1's objections and the rebuttal inline. Note the fallback in the report — the
opponent's answer is weaker without its own context.

### Verify the reply

Any *new* claim in the reply goes through the same verification. This is reading code, not a
third CLI call — two calls per invocation is the hard cap.

Final state per objection: CONFIRMED, REFUTED, MISREAD, UNVERIFIABLE, or OPEN.

---

## Report

Printed before any file is touched:

```
## Argue verdict — <clone> @ <branch>, <n> rounds

| # | Objection | Round 1 | After rebuttal | Evidence |
| --- | --- | --- | --- | --- |
| 1 | ... | REFUTED | conceded | `shotlist-store.ts:88` keys by projectId |
| 2 | ... | CONFIRMED | stands | `service.py:212` has no rollback path |
| 3 | ... | REFUTED | disputed, no new evidence | OPEN |
```

Then:

- **Where it was right** — each CONFIRMED claim and what the plan has to change.
- **Where I disagree** — each REFUTED / MISREAD claim, direct. State what the other model got
  wrong and what is actually true. Never soften into "both perspectives have merit."
- **Still open** — each OPEN and UNVERIFIABLE item, with both sides' best evidence.
- **Transcripts** — paths under `$TMPDIR/argue/`.

---

## Plan edits

- **CONFIRMED** → edit the plan markdown surgically. Fix the wrong step, add the missing one,
  correct the wrong path. Preserve the plan's structure, heading style and voice. Do not rewrite
  sections that were fine. Append a dated entry under `## Argue revisions`, one line per adopted
  claim.
- **REFUTED / MISREAD** → the plan keeps its original position. Do not silently reword.
- **OPEN / UNVERIFIABLE** → write a `## ⚠ Unresolved after /argue` section: the objection, both
  sides' best evidence, and why it did not settle. This is why they go in the file rather than
  only the terminal — whoever executes the plan later sees the live disputes instead of a
  clean-looking document that hid them.
- If **zero** claims were confirmed and nothing is open, do not touch the file. Say so: the plan
  stands as written, and here is why each objection failed.
- **Never commit or push.**

### Stop for the user's ruling

If anything is OPEN or UNVERIFIABLE, the run is not finished. After writing the section, stop
and ask the user to rule on each item, listing them. A two-round cap guarantees some runs end
contested; those endings must be explicit, not absorbed.

---

## Guardrails

- The opponent is **always read-only**: `--mode ask` (Cursor) / `--permission-mode plan`
  (Claude). Never `--force`, `--yolo`, or `--dangerously-skip-permissions` — those grant write
  and shell access to an agent whose output has not been reviewed.
- `--trust` is required for non-interactive `cursor-agent` runs; without it, it refuses with a
  workspace-trust prompt.
- Two opponent calls per invocation, maximum. Never retry in a loop — each call spends real
  quota.
- `--model` only when the user asked for a specific one. A different model family from our own
  is the entire point.

### Failure modes

| Symptom | Cause |
| --- | --- |
| "Workspace Trust Required" | `--trust` was dropped |
| Hangs past ~3 minutes | Diff too large — narrow to specific files, rerun once |
| Auth error | Tell the user to run the opponent CLI interactively once. Never handle credentials |
| Empty or one-line response | Prompt did not carry enough context — rebuild with the plan inline, rerun once |
| Chat id missing from JSON | Use the stateless Round 2 fallback and say so in the report |

---

## Known weakness

Whoever runs `/argue` is both debater and judge. The mitigation is structural rather than good
intentions: an objection can only leave the board with evidence, and everything else lands in
OPEN — which is loud, written into the plan file, and blocks on the user. A run where the judge
talked past an objection reads *worse* in the report than one where it conceded.

Style, inherited from `/CROSSCHECK` and still binding:

- Verify before you agree. Deference to another model is not rigor.
- Verify before you disagree too — an unchecked confident refutation is the same failure in the
  other direction.
- Specific over general: file paths, line numbers, real output.
- No "great catch", no "you're absolutely right", no apologising for the original plan.

---

## Downstream work

Deleting the two commands breaks three tracked things that name them:

1. **`scripts/build-slash-command-doc.py`** hardcodes `~/.claude/commands/ask.md`,
   `~/.cursor/commands/ask.md` and `~/.claude/commands/CROSSCHECK.md` in its `SRC` map and
   hard-fails on missing files. Its emitted prose also explains at length why `/ask` cannot be
   shared. Must be updated to the new set, then re-run.
2. **`scripts/link-slash-commands.sh`** lists `CROSSCHECK` in its shared loop, `ask` in its
   Claude loop, and links `cursor/ask.md` explicitly. Must be updated to link
   `claude/argue.md` and `cursor/argue.md`, and must **not** link `shared/argue-protocol.md`,
   which is not a command. Its existing dangling-symlink sweep removes the four stale symlinks
   automatically once the repo files are gone — no manual `rm` needed.
3. **`docs/process/090-slash-commands.md`** (hand-written) and **`docs/process/091-slash-commands-claude-vs-cursor.md`**
   (generated) both document the `/ask` + `/CROSSCHECK` pair by name, including the "two files,
   on purpose" table row and a full verbatim source dump. `090` is edited by hand; `091` is
   regenerated. `README.md:69` describes `091` in terms of `/ask` and `/CROSSCHECK` and needs the
   same update.

## Verification

The change is done when all of the following hold:

- `bash scripts/link-slash-commands.sh` runs clean, reports the four stale symlinks pruned, and
  `ls -l ~/.claude/commands/ ~/.cursor/commands/` shows `argue.md` on both sides and no `ask.md`
  or `CROSSCHECK.md`.
- `python3 scripts/build-slash-command-doc.py` exits 0 and the regenerated `091` contains no
  reference to `/ask` or `/CROSSCHECK`.
- `grep -rn "CROSSCHECK\|/ask" docs/ README.md commands/` returns nothing but intentional
  historical mentions.
- A live `/argue` run against a real plan in a real clone produces the verdict table, and the
  Round 2 `--resume` call demonstrably continues the Round 1 session rather than starting fresh.
