---
description: End a work session honestly — what landed, what's still open, what's blocked on you — and leave the tree, the plans, and the next agent in a state that survives the window closing.
argument-hint: "[optional: scope, e.g. 'claw-calendar only' or 'skip memory']"
allowed-tools: Bash(git:*), Bash(gh:*), Bash(pwd), Bash(ls:*), Bash(cat:*), Bash(date), Bash(pgrep:*), Bash(find:*), Read, Grep, Glob, Edit, Write
---

## Context (auto-collected)

- Now: !`date '+%Y-%m-%d %H:%M %Z'`
- Working dir: !`pwd`
- Enclosing clone: !`git rev-parse --show-toplevel 2>/dev/null || echo "NONE"`
- Branch: !`git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "n/a"`
- Uncommitted here: !`git status --porcelain 2>/dev/null | head -20 || true`
- Unpushed here: !`git log --oneline @{u}..HEAD 2>/dev/null | head -10 || echo "(no upstream or nothing ahead)"`
- Background jobs still alive: !`pgrep -fl "vitest|pnpm|npm run|vite|tsc|cursor-agent" 2>/dev/null | head -10 || echo "(none)"`

`$ARGUMENTS`

---

# /close-out

> **This is not the Cursor `/close-out`.** Cursor's skill of the same name
> (`~/.cursor/skills/close-out/SKILL.md`) lands an open Acme PR on `staging` — it reviews,
> commits, waits for CI, and **merges**. This command merges nothing and pushes nothing unasked;
> it reports. If what was actually wanted is *"close out the PR / land it on staging"*, say so in
> one line and stop — that job belongs in the Cursor window, not here.

A session ends whether or not anyone closes it out. The window gets closed, the laptop
sleeps, context gets compacted. What survives is the tree, the branches, the plan markdown,
and memory — so this command's job is to make those four things tell the truth about what
just happened, and to hand the next agent (or the next you) something better than a scroll
of chat.

**The failure this exists to prevent is a tidy-sounding summary that overstates completion.**
"All done!" on top of an unpushed branch, a still-running test suite, and two unanswered
questions is worse than no summary at all — it is a lie the next session will act on.

## HARD RULES

- **Never report as done what you have not verified in this session.** A green CI badge is
  not verification if the job did not exercise the change. Say what actually ran.
- **Never invent completion to make the receipt look clean.** An honest "blocked, waiting on
  a human decision" is a successful close-out.
- **Other agents are working in these repos right now.** Stage explicit paths, never `git add -A`
  or `git add .`. Re-read the tree before writing to it — branches and folders move underneath you.
- **Do not merge, push, or delete anything the operator has not asked for.** Committing your own
  work is in scope. Merging a PR is not, unless they said so in `$ARGUMENTS`.
- **Do not kill background jobs.** Report them. A suite that has been running for 20 minutes may
  be the most valuable thing in the session.

---

## Phase 1 — Sweep every repo you touched, not just this one

This setup is multi-repo and multi-clone (`claw-calendar` / `-2` / `-3`, `app-monorepo-1..7`,
`studio` / `studio-2`, `docs-hub`, …). Work in one session routinely spans several.

For each repo touched this session:

```sh
git -C <repo> rev-parse --abbrev-ref HEAD
git -C <repo> status --porcelain
git -C <repo> log --oneline @{u}..HEAD 2>/dev/null
```

Report per repo: **branch, uncommitted paths, unpushed commits.** Then, for each:

- **Is anything uncommitted MINE?** If yes → commit it on a branch (never straight to the
  default branch), scoping `git add` to explicit paths.
- **Is anything uncommitted SOMEONE ELSE'S?** Check `git log -3` timestamps and `.git/index`
  mtime. If another agent is active, **leave it alone and say so** — do not stage it, do not
  switch branches under it, do not stash it.
- **Did the branch change under me mid-session?** Say so explicitly and say where the work
  actually landed, because it may not be where the operator expects.

## Phase 2 — Account for every PR

```sh
gh pr list --state open --json number,title,headRefName
gh pr checks <n>
```

For each PR opened or touched this session, one row: **number, state, checks, merged or not.**
Where a check is green but did not actually cover the change, say that in the same breath —
a badge that tests something else is a trap, not a reassurance.

## Phase 3 — Reconcile the plan markdown

Per `docs-hub/AGENTS.md`: plans live in
`projects/<project>/docs/development/<Section>/__<date>-<slug>.md`.

- **Strikethrough what actually landed** (`~~step~~`), and only that.
- **Correct anything this session proved wrong.** A plan that kept a refuted claim is worse
  than one never written — the next agent will act on it. Mark corrections inline rather than
  silently editing, so the reader can see the plan learned something.
- **Update the status line** to match reality, including partial and withdrawn steps.
- `__foo.md` → `✅_foo.md` in the project's `docs/archive/` **only** when genuinely done.

## Phase 4 — Name what is blocked on a human

The highest-value output of a close-out. For each open decision:

- the **question**, in one line
- **what it gates** — which phase, PR, or step cannot proceed
- **what changes on each answer**
- why you did not just pick one

If you have been carrying an unanswered question for several turns, it goes here even if the
operator seems to have moved on. Especially then.

## Phase 5 — Report background work truthfully

Anything still running (test suites, builds, watchers, agents): **what it is, how long it has
been going, where its output lands, and what to do with the result.** If it will not survive
the session ending, say that plainly so nobody waits on a notification that will never come.

## Phase 6 — Memory

Save only what is **durable and non-obvious** — gotchas, decisions and their reasoning, the
shape of a system that surprised you. Per the memory rules: one fact per file, update rather
than duplicate, and **do not save what the repo already records**. A commit message is not a
memory. Skip this phase entirely if `$ARGUMENTS` says to.

---

## Output — the receipt

Keep it scannable. No victory lap.

**Landed** — what is committed, pushed, merged, deployed, and *verified how*.
**Open** — branches, PRs, uncommitted work, with where each one sits.
**Blocked on you** — the decisions from Phase 4.
**Still running** — from Phase 5.
**Corrected** — anything this session proved wrong that a doc, plan, or earlier claim now
reflects. If a cross-check refuted something you asserted, it belongs here; a close-out that
quietly drops its own errors teaches the next session nothing.

End with the single most useful next action — one line, not a menu.
