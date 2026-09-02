---
description: Explain what we're talking about as a two-column table — how it behaves today vs. how it would behave if we built it
argument-hint: "[what you're confused about — a feature, a bug, a plan, or nothing to explain the current thread]"
allowed-tools: Bash(git:*), Bash(pwd), Bash(ls:*), Bash(cat:*), Bash(gh:*), Read, Grep, Glob
---

## Context (auto-collected)

- Working dir: !`pwd`
- Enclosing clone: !`git rev-parse --show-toplevel 2>/dev/null || echo "NONE — cwd is not inside a repo"`
- Current branch: !`git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "not a repo"`
- Base branch: !`git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@' || echo "unknown"`
- Uncommitted: !`git status --porcelain 2>/dev/null | head -20 || true`
- Recent commits: !`git log --oneline -5 2>/dev/null || true`

What I'm confused about: $ARGUMENTS

## Your task

I am confused. Explain it to me. **This is an explanation, not a work order — do not edit files, do not commit, do not push, do not start implementing.**

If `$ARGUMENTS` is empty, explain whatever we were just discussing in this conversation.

### Step 1 — Ground it in something real

Read before you explain. Do not describe behavior you have not verified:

- Open the actual files that produce the behavior on the **current** branch.
- If the "today" side lives in a different clone or branch than the one I'm sitting in, say so explicitly and name it.
- If part of it is genuinely unknown, write "unverified" in the cell rather than inventing a confident answer.

### Step 2 — Name both sides

**Left column header** = where we are now: `<repo-name> @ <branch>` (e.g. `app-monorepo-1 @ staging`).
Add the environment in parens when it matters (localhost:5173, staging, production).

**Right column header** = if implemented: the feature branch name.
- If a feature branch already exists for this work, use its real name.
- If it doesn't exist yet, propose one following this repo's convention (check recent branches / repo docs — e.g. `issue-<N>-<slug>`) and mark it `(proposed)`.

### Step 3 — The table

Output **one markdown table**. Rows are **user behaviors described from a UI/UX perspective** — what a person sitting in front of the screen sees, clicks, waits for, and gets back. Write cells the way you'd narrate a screen recording.

| What the user does | `<repo> @ <branch>` (today) | `<feature-branch>` (if implemented) |
|---|---|---|
| Clicks "Generate" on an empty moodboard | Button is live; request 500s after ~8s and a red toast says "Something went wrong" | Button is disabled with a tooltip "Add at least one image first" — no request is sent |

Rules for rows:
- **One user-visible moment per row**, in the order the user hits them.
- Cells describe **behavior**, not code. No file paths, function names, or component names inside the table.
- Include the unglamorous states: empty, loading, error, permission-denied, refresh, back button.
- If a row is **identical on both sides**, say "unchanged" — don't pad the table with fake deltas.
- 5–12 rows. If it needs more, the thing is really two features — say that.

### Step 4 — Below the table

Three short sections, a few lines each, plain English:

1. **Why it behaves that way today** — the one mechanism that explains the left column. This is where file paths belong (use clickable `[file.ts:42](path#L42)` links).
2. **What would have to change** — the smallest honest description of the work, and roughly how big it is.
3. **What I'd still be unsure about** — open questions or decisions that are mine to make, not yours.

### Tone

I asked because I'm confused, so assume nothing. Expand jargon the first time it appears. Prefer short sentences. Don't hedge everything into mush — if you're confident, say it plainly; if you're guessing, label the guess.
