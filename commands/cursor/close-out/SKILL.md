---
name: close-out
description: >-
  Close out an open Acme PR onto staging: quick review, fix blockers,
  commit leftover WIP, wait for CI, merge, checkout latest staging, reply DONE.
  Use when the user says CLOSE-OUT, /CLOSE-OUT, close out this PR, land it on
  staging, or merge to staging.
disable-model-invocation: true
---

# /CLOSE-OUT

> **This is not the Claude Code `/close-out`.** Claude's command of the same name
> (`~/.claude/commands/close-out.md`) ends a *work session* honestly — what landed, what is still
> open, what is blocked on a human — and it deliberately merges nothing. This one merges a PR to
> `staging`. If what was actually wanted is *"close out the session"*, say so in one line and stop
> — that job belongs in the Claude Code window, not here.

Dennis's land-it workflow. Default destination is **`staging`**, never `production`.

Do not stop to ask between steps unless merge is blocked (conflicts, failing CI, missing PR, wrong checkout).

## Pin the tree

Work only on the checkout that owns this PR. Infer from the branch / open PR / ticket Target-repo table. Do not use another Core-N because Vite is already up.

| Checkout | Default Vite |
|---|---|
| app-monorepo-1 | `:5173` |
| app-monorepo-2 | `:5174` |
| app-monorepo-3 | `:5175` |
| app-monorepo-4 | `:5176` |
| app-monorepo-5 | `:5178` |
| app-monorepo-6 | `:5179` |
| app-monorepo-7 | `:5180` |
| app-monorepo-review | `:5181` |
| `docs-hub` | `:9000` |

## Sequence

1. **Identify the PR.** `gh pr view` on this branch (base must be `staging`). No PR → stop.
2. **Quick review** of `origin/staging...HEAD` plus the working tree. Look for merge blockers (wrong client, broken bounce, SCSS 2–4 in `v2/`, packed imports, tests that only source-grep a now-moved string). Skip a full two-axis `/code-review` unless the user asked for that.
3. **Fix** anything you would not merge. Run the affected app's tests + `validate` when studio/AM changed.
4. **Commit leftover WIP.** Close-out authorizes commits. Follow the git commit user rule (status/diff/log, HEREDOC message, no `--no-verify`, no force-push, no amend of pushed commits). Split bounce vs refactor if they are unrelated.
5. **Push** `git push -u origin HEAD`.
6. **Wait for CI.** `gh pr checks <N> --watch`. Do not merge red.
7. **Merge** with a merge commit, keep the branch:

   ```bash
   gh pr merge <N> --merge --delete-branch=false
   ```

   Confirm `state: MERGED` and a merge SHA.
8. **Local staging.** On this checkout:

   ```bash
   git fetch origin staging
   git checkout staging
   git pull origin staging
   ```

   Confirm `HEAD` is the merge commit and `## staging...origin/staging`.
9. **Archive the ticket** if one lives under `docs-hub/projects/app/docs/__MVP2/`:
   - `__foo.md` → `z_Archived/✅_foo.md`
   - `git mv` if tracked; plain `mv` if untracked
   - Do not commit unrelated dirty docs-hub files
10. **Reply.** First line is exactly `DONE`. Then the PR URL, merge SHA, and that this checkout is on `staging`.

## Do not

- Merge to `production` / `main`
- Force-push, skip hooks, or `--no-verify`
- Merge with failing required checks
- Switch a *different* Core-N to staging
- Exercise Reset-to-FTU against staging
- Stay on the feature branch after merge
- Archive the ticket before the staging merge is confirmed
