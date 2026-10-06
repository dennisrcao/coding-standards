---
description: Write a simple PR description — ticket link + a before/after behavior table
argument-hint: "[ticket URL or number, or extra context — optional]"
allowed-tools: Bash(git:*), Bash(gh:*), Read, Grep, Glob
---

## Context (auto-collected)

- Current branch: !`git rev-parse --abbrev-ref HEAD`
- Base branch: !`git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@' || echo staging`
- Commits on this branch: !`git log --oneline origin/HEAD..HEAD 2>/dev/null | head -30`
- Files changed: !`git diff --stat origin/HEAD...HEAD 2>/dev/null | tail -40`
- Existing PR for this branch (if any): !`gh pr view --json number,title,url -q '"#\(.number) \(.title) — \(.url)"' 2>/dev/null || echo "none"`

Extra instruction from me: $ARGUMENTS

## Your task

Write the PR description for this branch. **Do not push, do not create or edit the PR, do not commit.** Print the markdown body in a fenced block so I can copy it.

Read the actual diff first — `git diff origin/HEAD...HEAD` — and open the changed files where the diff alone doesn't explain the change. Never describe a change you have not read.

### Find and link the ticket

Look for the ticket in my extra instruction, the branch name, and the commit messages. Then:

- If it's a repo issue: `gh issue view <n>` to read it, and link it as `Fixes <org>/<repo>#<n>`.
- If it's a URL (project board item, Linear, Jira, etc.): link the URL directly.
- If you can't find one, say so in one line rather than inventing a reference.

The ticket link goes on the **first body line**, before anything else.

### Structure

Title line: conventional-commit style, scoped, with the ticket number — e.g. `fix(am+studio): make campaign sessions addressable (#389)`.

First body line: the ticket link.

Then one short paragraph — two sentences max — on what broke and why, naming the specific file or function responsible.

Then the behavior table. This is the core of the description:

```
## Behavior

| Behavior | `staging` (before) | This branch (after) |
| --- | --- | --- |
| <the specific action a user or system takes> | <exactly what happens today> | <exactly what happens now> |
```

Rules for the table:

- Use the real base branch name from the context above in the left column header.
- One row per distinct behavior that changed. If only one thing changed, one row.
- Each row is a concrete, observable action — "Open a shotlist link with `?session=`", not "session handling".
- Both cells describe **what actually happens**, specifically. `Redirects to the first session, dropping the param` — not `broken` or `works correctly`.
- Never write "N/A", "unchanged", or "fixed" in a cell. If a behavior didn't change, it doesn't get a row.

Then, only if they add something the table doesn't already say:

- **`## Files changed`** — one bullet per file, `**\`filename.ts\`**` bolded and backticked, followed by what changed there. Mark new files `(new)`.
- **`## Verification`** — how you confirmed it, with real numbers (`751 passed / 68 files`, `0 errors`). Only include checks you actually ran in this session.
- **`## Not covered`** — anything a reviewer might wrongly assume is fixed, or that you couldn't verify locally.

Close with:

```
🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

### Style rules

- Specific over general. Names, numbers, file paths, real output. No "improved robustness", no "enhanced the experience".
- Keep it short. If the change is three lines, the description is a title, a ticket link, and a one-row table.
- No emoji beyond the closing line. No exclamation marks.
- Never claim a test passed, a check ran, or a behavior was verified unless it actually happened in this session. Put it under `## Not covered` instead.
