---
description: Ask the other agent (Cursor) to critique this, without opening its window — then verify every claim before adopting it
argument-hint: "[path to the plan, or what you want challenged — optional]"
allowed-tools: Bash(cursor-agent:*), Bash(git:*), Bash(pwd), Bash(ls:*), Bash(find:*), Bash(cat:*), Bash(mkdir:*), Read, Grep, Glob
---

## Context (auto-collected)

- Working dir: !`pwd`
- Enclosing git clone: !`git rev-parse --show-toplevel 2>/dev/null || echo "NONE — cwd is not inside a repo"`
- Branch: !`git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "not a repo"`
- Uncommitted: !`git status --porcelain 2>/dev/null | head -20 || true`
- Recently touched markdown: !`find . -maxdepth 2 -name "*.md" -mtime -3 -not -path "*/node_modules/*" 2>/dev/null | head -10`
- cursor-agent: !`command -v cursor-agent >/dev/null && echo "available" || echo "MISSING — install Cursor CLI"`

What I want challenged: $ARGUMENTS

## Step 0 — Establish which clone is under review (do this first)

My repos are cloned many times over, one clone per workspace folder — `app-monorepo-1`
through `-7`, `studio` / `studio-2`, `claw-calendar` / `-2` / `-3`, and so on. Each clone
is a **separate checkout on its own branch at its own dev port**. A review pointed at the
wrong clone reviews the wrong branch and every conclusion is garbage.

`pwd` is not sufficient. This session may be running from `~/Desktop`, which is the parent
of all of them, not any one repo.

Resolve the clone in this order:

1. If I gave a file path, the clone is its nearest ancestor directory containing `.git`.
2. Otherwise, if "Enclosing git clone" above is a real path, use that.
3. Otherwise `pwd` is a workspace parent like `~/Desktop`. **Do not guess and do not
   default to `pwd`** — a review of `~/Desktop` is meaningless. Infer the clone from what
   I named (a ticket, a port number, a branch, "core-3"), and confirm it with me in one
   line before spending the call. If nothing identifies it, ask which clone.

State the resolved clone and its branch in one line before running anything.

Everything below runs **with that clone as the working directory** — pass it explicitly:

```bash
cd "<resolved clone>" && cursor-agent -p --mode ask --trust --model cursor-grok-4.6-high "<prompt>"
```

`cursor-agent` reads the repo from its own cwd. Launching it from the wrong directory is
the single most likely way for this command to produce confident nonsense.

## What this does

`/ask` means "ask the other agent". In Claude Code that is **Cursor**; the mirror-image
`/ask` in Cursor comes back to me. Runs Cursor's model as an independent reviewer, headlessly. No Cursor window, no
screenshot, no copy-paste. A different model family reviewing the same code is worth
real money — it doesn't share my blind spots or my framing.

Then it **verifies that critique before any of it is adopted**, because a critique is a
**claim, not a verdict.** Cursor is confidently wrong often enough that nothing it says gets
adopted unverified. Step 4 is that verification, and it is not optional.

## Step 1 — Decide what's being reviewed

In priority order:

1. A path in my instruction above → review that file.
2. A description in my instruction with no path → review the current diff against it.
3. Nothing given → review the working-tree diff **of the resolved clone**. If that tree is
   clean, review the most recently touched plan markdown listed above.

State in one line what you settled on. If two candidates are plausible, ask rather than guess.

## Step 2 — Build the reviewer prompt

Cursor starts with **no context from this conversation**. It sees only the prompt and the
repo. So the prompt must carry the plan itself, not a reference to it.

Ask for disagreement, not a summary. A reviewer asked "what do you think" produces
agreeable mush. Structure it:

- The plan or diff, inline and complete.
- What specifically to attack — the riskiest assumption, the coupling, the migration order.
- This instruction: *"For each objection give: the file and line, what breaks, and the
  concrete input or state that triggers it. If you cannot name a file and line, say so
  explicitly rather than speculating. If a step is sound, say so and move on — do not
  manufacture objections to seem useful."*

## Step 3 — Run it

Read-only mode, so it can never edit the repo:

```bash
cd "<resolved clone from Step 0>" && cursor-agent -p --mode ask --trust --model cursor-grok-4.6-high "<the prompt>"
```

Notes that matter:

- `--mode ask` is read-only. **Never** use `--force`, `--yolo`, or plain `-p` here — those
  grant write and shell access to an agent whose output I have not reviewed.
- `--trust` is required for non-interactive runs; without it, it refuses with a workspace-trust prompt.
- `--model cursor-grok-4.6-high` is **pinned deliberately — do not drop it.** The CLI's own
  default is `Auto` (`cursor-agent about` → `Model  Auto`), which routes per request and can
  land on `claude-opus-5-thinking-high` or `claude-sonnet-5-thinking-high` — a Claude model
  reviewing Claude output, with no way to tell after the fact. A different family from mine is
  the entire point of this command, so the family is not left to a router.
  Override to another *non-Claude* model (`cursor-grok-4.6-xhigh`, `gpt-5.3-codex-high`) only if
  I name one. Note the CLI's model setting is separate from the Cursor IDE's picker — changing
  the model in the Cursor window has no effect here.
- It can take a couple of minutes on a large diff. Let it run.
- This spends Cursor quota. One call per invocation — do not retry in a loop.

Save the raw output to a file and tell me the path, so it survives compaction:

```bash
mkdir -p "${TMPDIR:-/tmp}/ask-critiques"
# write output to ${TMPDIR:-/tmp}/ask-critiques/cursor-<short-topic>.md
```

## Step 4 — Verify it before adopting any of it

Print the critique in full first — I want to see what it actually said, unfiltered.

Then work through it in this order. Do not skip this because the critique sounds plausible;
sounding plausible is precisely what makes an unverified critique dangerous.

1. **Decompose it into atomic, falsifiable claims.** A numbered list, one row per assertion.
   Split compound complaints apart — "this is racy and also the store is keyed wrong" is two
   claims. Anything not checkable against the codebase (style preferences, "consider also…",
   vague hedges) gets one line at the end as *unfalsifiable — ignored*.

2. **Check each claim against the real code.** Open the file and function it names; if it names
   none, find the code yourself with Grep/Glob. Other models hallucinate file paths, prop names
   and hook signatures constantly — a claim about `useSessionStore` is dead on arrival if that
   hook does not exist. Run something where you can: tests, a typecheck, `git log -S` for when a
   line arrived, `gh pr view` for prior review context. Evidence beats reasoning. Also check that
   the plan actually says what the critique says it says — a large fraction of cross-model
   critiques attack a misreading of the plan.

3. **Give every claim one verdict.** Never write one you did not verify; "probably fine" is not a
   verdict, go look.

   | Verdict | Meaning |
   | --- | --- |
   | **CONFIRMED** | Verified true against the code. The plan is wrong or incomplete here. |
   | **REFUTED** | Verified false. Name the specific evidence that kills it. |
   | **MISREAD** | True of some other code, or of a plan that is not this one. |
   | **UNVERIFIABLE** | Cannot be settled from the codebase — a product or design call. Say whose. |

4. **Print the verdict table before touching the plan.** The evidence column is `file.ts:line`, a
   command's real output, or a commit SHA — not prose. Then: for each REFUTED / MISREAD claim, one
   short paragraph on what Cursor got wrong and what is actually true — do not soften it into "both
   perspectives have merit"; for each CONFIRMED claim, what the plan has to change; for each
   UNVERIFIABLE one, a question to me.

5. **Edit the plan only for CONFIRMED claims.** Surgically — fix the wrong step, add the missing
   one, correct the wrong path — preserving the plan's existing structure, heading style and voice.
   Add a dated entry under `## Cross-check revisions` at the bottom, one line per adopted claim
   (append if that heading exists). If **zero** claims were confirmed, touch nothing and say so
   plainly: the plan stands as written, and here is why each objection failed.

Boundary: findings go in the plan markdown, wherever it lives — Desktop drafts and
`~/Desktop/docs-hub` are both fair game. Do not fix the underlying code as part of this, and
do not commit or push unless I ask.

Verify before you agree — deference to another model is not rigor. Verify before you disagree too:
a confident refutation you did not check is the same failure in the other direction.

## Failure modes

- **"Workspace Trust Required"** → you dropped `--trust`.
- **Hangs past ~3 minutes** → the diff is too large. Narrow to the specific files and rerun once.
- **`Unknown model` / model error** → the roster moved. Re-check with `cursor-agent --list-models`
  and pin the nearest non-Claude equivalent; do not silently fall back to `Auto`.
- **Not logged in / auth error** → tell me to run `cursor-agent` interactively once to authenticate. Do not try to pass credentials yourself.
- **Empty or one-line response** → the prompt didn't carry enough context. Cursor cannot
  see our conversation. Rebuild the prompt with the plan inline and rerun once.
