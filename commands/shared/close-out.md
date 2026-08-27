---
description: Land the work — commit, PR, review, CI, merge to the repo's base branch, sync local, and report honestly what landed and what did not.
argument-hint: "[optional: e.g. 'skip review', 'no merge', 'base=main']"
allowed-tools: Bash(git:*), Bash(gh:*), Bash(pnpm:*), Bash(npm:*), Bash(pwd), Bash(ls:*), Bash(cat:*), Bash(grep:*), Bash(find:*), Bash(date), Bash(pgrep:*), Read, Grep, Glob, Edit, Write
---

## Context (auto-collected)

- Now: !`date '+%Y-%m-%d %H:%M %Z'`
- Repo: !`git rev-parse --show-toplevel 2>/dev/null || echo "NOT A REPO"`
- Branch: !`git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "n/a"`
- Base branch: !`git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's#^origin/##' || gh repo view --json defaultBranchRef -q .defaultBranchRef.name 2>/dev/null || echo "UNRESOLVED"`
- Uncommitted: !`git status --porcelain 2>/dev/null | head -30 || true`
- Unpushed: !`git log --oneline @{u}..HEAD 2>/dev/null | head -10 || echo "(no upstream or nothing ahead)"`
- Open PR for this branch: !`gh pr view --json number,state,baseRefName,url 2>/dev/null || echo "(none)"`
- Background jobs still alive: !`pgrep -fl "vitest|jest|pnpm|npm run|vite|tsc|cursor-agent" 2>/dev/null | head -10 || echo "(none)"`

`$ARGUMENTS`

---

# /close-out

**I have signed off on the behavior. Land it.** Commit what is left, open a PR, review it, fix
what should be fixed, wait for CI, merge to this repo's base branch, and leave this checkout on
that base branch — not stranded on the feature branch.

This is repo-agnostic. It resolves the base branch rather than assuming one: `staging` on
app-monorepo, `main` almost everywhere else. Never hardcode either.

**The failure this exists to prevent is a merge that leaves the operator worse off than before** —
merged on red CI, merged with someone else's uncommitted work swept into the commit, merged and
then abandoned on a stale feature branch, or a deploy fired that nobody knew was coming.

## HARD RULES

- **Other agents are working in these repos right now.** Stage explicit paths, never `git add -A`
  or `git add .`. Re-read the tree before writing to it — branches and folders move underneath you.
- **Never merge red.** A failing or pending required check is a stop, not a judgment call.
- **Never merge to `production`.** This command goes to the repo's *base* branch. Production
  promotion is `/ship`, and it is a separate, deliberate act.
- **No force-push, no `--no-verify`, no amending a pushed commit.**
- **Never report as landed what you did not verify.** Confirm the merge SHA and the local branch
  state by reading them back, not by assuming the command worked.
- **Do not kill background jobs.** Report them.

---

## Step 0 — Resolve the ground

Establish and state in one line: **repo root, current branch, base branch.**

Base branch resolution, in order:

```sh
git symbolic-ref --short refs/remotes/origin/HEAD | sed 's#^origin/##'   # preferred
gh repo view --json defaultBranchRef -q .defaultBranchRef.name           # fresh clone fallback
```

If `$ARGUMENTS` names a base, that wins. If both fail, **stop and ask** — do not guess `main`.

Stop conditions, each of which ends the command:

- **Already on the base branch** → there is nothing to land. Say so and stop.
- **Not a git repo** → stop.
- **Nothing to land** — clean tree, nothing unpushed, no open PR → say so and stop.

## Step 1 — Review the diff

Review `origin/<base>...HEAD` plus the working tree, looking for **merge blockers** — the things
you would not let through, not a style pass. Use the repo's own conventions: read its `CLAUDE.md` /
`AGENTS.md` first if you have not already.

This is a quick inline review on purpose. Do **not** invoke a repo's `/code-review` skill unless
`$ARGUMENTS` asks — it is slow, and it does not exist in most repos.

## Step 2 — Fix what should be fixed

Fix anything from Step 1 you would not merge. Then run what the repo gates on — its test command
and its lint/typecheck (`pnpm validate`, `pnpm test`, whatever that repo actually uses).

If a fix is larger than the change being landed, **stop and say so** rather than growing the PR.

## Step 3 — Commit what is left

Explicit paths only. Check whether uncommitted work is *yours*: `git log -3` timestamps and
`.git/index` mtime tell you if another agent is mid-edit. If it is not yours, **leave it and say
so** — do not stage it, stash it, or switch branches under it.

HEREDOC commit message. Split unrelated changes into separate commits.

## Step 4 — Push

```sh
git push -u origin HEAD
```

## Step 5 — PR

`gh pr view` first — reuse the open PR if there is one. Otherwise:

```sh
gh pr create --base <base> --title "<title>" --body "<body>"
```

Body: what changed and why, in the repo's house style. If the repo has a PR template, use it.

## Step 6 — Wait for CI

```sh
gh pr checks <N> --watch
```

Red or still-failing required checks → stop and report. Do not merge.

## Step 7 — Merge, with the deploy gate

**Before merging, find out whether merging deploys anything:**

```sh
for f in .github/workflows/*.yml; do
  grep -A6 '^on:' "$f" | grep -qE "branches:.*\b<base>\b" && echo "$f"
done
```

Read what those workflows actually do — a CI workflow that runs tests on push is not a deploy.

- **No workflow deploys on merge** → merge. Do not stop to ask.
- **Something deploys on merge** → **stop.** Name the workflow, what it publishes, and where, in
  two lines. Wait for an explicit yes.

  On app-monorepo this always fires: a push to `staging` deploys the frontend to the staging,
  client-staging and admin-staging hosts, plus the docs hub and the AM image. That is a real
  environment real people are looking at.

Then:

```sh
gh pr merge <N> --merge --delete-branch=false
```

Confirm `state: MERGED` and capture the merge SHA.

## Step 8 — Sync this checkout

The whole point of the last step: do not leave the repo stranded on the merged feature branch.

```sh
git fetch origin <base>
git checkout <base>
git pull origin <base>
```

Confirm `HEAD` is the merge commit and the branch tracks `origin/<base>`.

## Step 9 — The receipt

Keep it scannable. No victory lap.

**Landed** — the PR number and URL, the merge SHA, what deployed (if anything), and this checkout's
branch. State how each was verified, not that it "should" have worked.
**Open** — anything deliberately left behind: unstaged work that was not yours, a fix judged too
big for this PR, a follow-up worth a ticket.
**Blocked on you** — decisions you could not make. The question, what it gates, and what changes on
each answer. If you have been carrying an unanswered question for several turns, it goes here even
if the operator seems to have moved on. Especially then.
**Still running** — background jobs, how long they have been going, where their output lands, and
whether they will survive this session.

Finally, one line if — and only if — another clone has uncommitted work:

```sh
for d in ~/Desktop/app-monorepo-* ~/Desktop/claw-calendar* ~/Desktop/docs-hub; do
  [ -d "$d/.git" ] && [ -n "$(git -C "$d" status --porcelain 2>/dev/null)" ] && echo "$d has uncommitted work"
done
```

That is a pointer, not a task. Do not go clean them up.

End with the single most useful next action — one line, not a menu.
