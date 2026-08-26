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
cd "<resolved clone>" && cursor-agent -p --mode ask --trust "<prompt>"
```

`cursor-agent` reads the repo from its own cwd. Launching it from the wrong directory is
the single most likely way for this command to produce confident nonsense.

## What this does

`/ask` means "ask the other agent". In Claude Code that is **Cursor**; the mirror-image
`/ask` in Cursor comes back to me. Runs Cursor's model as an independent reviewer, headlessly. No Cursor window, no
screenshot, no copy-paste. A different model family reviewing the same code is worth
real money — it doesn't share my blind spots or my framing.

Then it hands the critique to `/CROSSCHECK`, because **a critique is a claim, not a
verdict.** Cursor is confidently wrong often enough that nothing it says gets adopted
unverified.

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
cd "<resolved clone from Step 0>" && cursor-agent -p --mode ask --trust "<the prompt>"
```

Notes that matter:

- `--mode ask` is read-only. **Never** use `--force`, `--yolo`, or plain `-p` here — those
  grant write and shell access to an agent whose output I have not reviewed.
- `--trust` is required for non-interactive runs; without it, it refuses with a workspace-trust prompt.
- Add `--model <name>` only if I asked for a specific model. A different family from mine is the point.
- It can take a couple of minutes on a large diff. Let it run.
- This spends Cursor quota. One call per invocation — do not retry in a loop.

Save the raw output to a file and tell me the path, so it survives compaction:

```bash
mkdir -p "${TMPDIR:-/tmp}/crosscheck"
# write output to ${TMPDIR:-/tmp}/crosscheck/cursor-<short-topic>.md
```

## Step 4 — Hand off to verification

Print the critique in full first — I want to see what it actually said, unfiltered.

Then **immediately run the `/CROSSCHECK` workflow on it** (the command at
`~/.claude/commands/CROSSCHECK.md`): decompose it into atomic falsifiable claims, verify
each one against the real code, and report the verdict table before changing anything.

Do not skip this because the critique sounds plausible. Sounding plausible is precisely
what makes an unverified critique dangerous.

## Failure modes

- **"Workspace Trust Required"** → you dropped `--trust`.
- **Hangs past ~3 minutes** → the diff is too large. Narrow to the specific files and rerun once.
- **Not logged in / auth error** → tell me to run `cursor-agent` interactively once to authenticate. Do not try to pass credentials yourself.
- **Empty or one-line response** → the prompt didn't carry enough context. Cursor cannot
  see our conversation. Rebuild the prompt with the plan inline and rerun once.
