---
description: Another LLM critiqued my plan — verify its claims against the codebase, then push back or update the plan
argument-hint: "[path to the plan, path to the critique, or extra context — optional]"
allowed-tools: Bash(git:*), Bash(gh:*), Bash(ls:*), Bash(find:*), Bash(rg:*), Bash(grep:*), Read, Grep, Glob, Edit, Write
---

## Context (auto-collected)

- Working dir: !`pwd`
- Current branch: !`git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "not a repo"`
- Uncommitted files: !`git status --porcelain 2>/dev/null | head -20 || true`
- Recently touched plan/doc markdown: !`( find ~/Desktop -maxdepth 1 -name "*.md" -mtime -3; find ~/Desktop/docs-hub -name "*.md" -not -path "*/node_modules/*" -not -path "*/site/*" -mtime -3 ) 2>/dev/null | head -15`
- Recent screenshots: !`ls -t ~/Desktop/*.png ~/Desktop/Screenshots/*.png ~/Downloads/*.png 2>/dev/null | head -8`
- Recent critique files from /ask: !`ls -t "${TMPDIR:-/tmp}"/crosscheck/*.md 2>/dev/null | head -5 || true`

Extra instruction from me: $ARGUMENTS

## The situation

I took a plan you (or another session) wrote and ran it past a *different* model — `/ask`, the
other agent's window, a live chat, a pasted screenshot. It came back with a critique. That critique
is what you are evaluating. **It is a claim, not a verdict.** A second model is confidently wrong
often enough that adopting its critique unverified is worse than ignoring it: it launders a
hallucinated file path into a plan the next session acts on.

## Step 0 — Pin the clone

These repos are cloned many times over (`app-monorepo-1`..`-7` and `-PR-Review`, `studio`/`studio-2`,
`claw-calendar`/`-2`/`-3`), each on its own branch. Verifying a claim against the wrong checkout
produces a confident REFUTED that is simply false.

**State the clone and branch in one line before you check anything, and run every command from
there.** The context block above is auto-collected in Claude Code but not in Cursor — if it is
empty, run `pwd` and `git rev-parse --abbrev-ref HEAD` yourself rather than assuming.

## Step 1 — Find the critique

In priority order:

1. **A critique file written by `/ask`.** Check the critique files listed in the context above —
   most recent first. This is the usual case: the other model was invoked headlessly, so its
   response is already text on disk and needs no transcription.
2. A path in my extra instruction above.
3. **An image attached to this message** — a screenshot of the other model's response. Read it
   carefully and transcribe every distinct claim, including ones in code blocks and diffs.
4. Pasted text in my extra instruction above.
5. If none of those, check the most recent screenshot. Confirm with me before assuming it is right.

If a critique file and a screenshot are both present, ask which one I mean rather than assuming the
newer. If you cannot find a critique, **stop and ask** — do not invent one.

## Step 2 — Find the plan being critiqued

Look in my extra instruction, then the recently-touched markdown above, then `~/Desktop/*.md`
(drafts often start on the Desktop before they are filed), then
`~/Desktop/docs-hub/projects/*/docs/`. Match on the subject matter of the critique — ticket
number, file names, function names it mentions.

State which file you settled on and why, in one line, before you go further. If two candidates are
plausible, ask.

## Step 3 — Decompose the critique into checkable claims

Write out a numbered list. One row per **atomic, falsifiable** assertion. Split compound complaints
apart — "this is racy and also the store is keyed wrong" is two claims.

Discard anything that is not checkable against the codebase: style preferences, "consider also…",
vague hedges. Note them in a single line at the end as *unfalsifiable — ignored*.

## Step 4 — Verify each claim against the actual codebase

This is the whole point of the command. For each claim:

- **Read the real code.** Open the file and the function it names. If it names no file, find the
  code yourself with Grep/Glob.
- **Check whether the thing it describes actually exists.** Other models hallucinate file paths,
  prop names, hook names, and function signatures constantly. A claim about `useSessionStore` is
  dead on arrival if that hook does not exist.
- **Run something where you can.** Tests, a type check, `git log -S` to see when a line arrived,
  `gh pr view` for prior review context. Evidence beats reasoning.
- **Check the plan actually says what the critique says it says.** A large fraction of cross-model
  critiques attack a misreading of the plan.

Assign one verdict per claim:

| Verdict | Meaning |
| --- | --- |
| **CONFIRMED** | Verified true against the code. The plan is wrong or incomplete here. |
| **REFUTED** | Verified false. Name the specific evidence that kills it. |
| **MISREAD** | True of some other code, or of a plan that is not this one. |
| **UNVERIFIABLE** | Cannot be settled from the codebase — a product or design call. Say whose. |

Never write a verdict you did not verify. "Probably fine" is not a verdict — go look.

## Step 5 — Report

Print this before touching the plan file:

```
## Cross-check verdict

| # | Claim (one line) | Verdict | Evidence |
| --- | --- | --- | --- |
| 1 | ... | REFUTED | `shotlist-store.ts:88` keys by projectId — the critique's `bySession` map does not exist |
```

Evidence column is `file.ts:line`, a command's real output, or a commit SHA. Not prose.

Then:

- **Where I disagree** — for each REFUTED / MISREAD claim, one short paragraph. Be direct: state
  what the other model got wrong and what is actually true. Do not soften it into "both
  perspectives have merit". If it is wrong, say it is wrong and show why. Doubling down on a
  verified position is the correct behavior here — a critique from another model carries no
  authority on its own.
- **Where it is right** — for each CONFIRMED claim, what the plan has to change.
- **Open questions** — UNVERIFIABLE claims, phrased as a question to me.

## Step 6 — Update the plan

Only for **CONFIRMED** claims. Edit the plan markdown in place:

- Fix the wrong step, add the missing step, correct the wrong file path — surgically. Do not
  rewrite sections that were fine.
- Preserve the plan's existing structure, heading style, and voice.
- Add a short changelog entry at the bottom of the plan under `## Cross-check revisions` — date,
  which claims were adopted, one line each. If that heading already exists, append to it.
- Do **not** silently drop or reword anything the critique got wrong. The plan keeps its original
  position on those.

Boundary: edit the plan markdown itself, wherever it lives — Desktop drafts and
`~/Desktop/docs-hub` are both fair game. Do not fix the underlying code as part of a
cross-check; findings go in the plan. Do not commit or push unless I ask.

If **zero** claims were confirmed, do not touch the file. Say so plainly: the plan stands as
written, and here is why each objection failed.

## Style

- Verify before you agree. Deference to another model is not rigor.
- Verify before you disagree too — a confident refutation you did not check is the same failure
  mode in the other direction.
- Specific over general. File paths, line numbers, real command output.
- No "great catch!", no "you're absolutely right", no apology for the original plan.
