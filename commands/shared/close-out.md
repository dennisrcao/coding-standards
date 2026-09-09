---
description: Land the work — commit, PR, review, CI, merge to the repo's base branch, sync local, archive the docs-hub ticket that drove it, and report honestly what landed and what did not.
argument-hint: "[optional: e.g. 'skip review', 'no merge', 'base=main']"
allowed-tools: Bash(git:*), Bash(gh:*), Bash(pnpm:*), Bash(npm:*), Bash(pwd), Bash(ls:*), Bash(cat:*), Bash(grep:*), Bash(find:*), Bash(mkdir:*), Bash(date), Bash(pgrep:*), Read, Grep, Glob, Edit, Write
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

**I have signed off on the behavior. Land it.** Commit what is left, open a PR, **thoroughly
review it** (unless `$ARGUMENTS` contains `skip review`), fix what should be fixed, wait for CI,
merge to this repo's base branch, leave this checkout on that base branch — not stranded on the
feature branch — and close out the `docs-hub` ticket that drove the work, if there was one.

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
- **Never merge with open `fix-now` review findings.** Step 2 must finish — verified and either
  fixed or reclassified with evidence — before merge.
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

## Step 1 — Merge-blocker scan (quick)

60-second pass on `origin/<base>...HEAD` plus the working tree. Look for **merge blockers only** —
secrets in the diff, debug-only flags left on, broken redirects, API contract breaks you can spot
without a deep read, prod-data footguns. Read the repo's `CLAUDE.md` / `AGENTS.md` if you have not
already. Not a style pass.

## Step 2 — Thorough review (default)

Skip this step only when `$ARGUMENTS` contains `skip review`.

Review as if production breaks are on you. **`fix-now` findings block the merge** until resolved or
reclassified with `file:line` evidence.

### 2a — Gather

- `git diff origin/<base>...HEAD` and `git log origin/<base>..HEAD --oneline`
- Open PR body, hub ticket, or the user sign-off from this conversation — what behavior was promised
- Per-app agent notes for every area the diff touches

### 2b — Repo `/code-review` skill (when it exists)

If the repo root has `.claude/skills/code-review/SKILL.md`, follow it with fixed point
`origin/<base>`. Run **both** Standards and Spec axes — `/close-out` is not an excuse to skip Spec.

### 2c — Cursor Bugbot (when 2b does not apply, or as a second lens in Cursor)

When there is no `code-review` skill, launch the **Bugbot** subagent on `origin/<base>...HEAD`
(`Diff: branch changes`). Put PR intent in `Change Description` only when the diff alone is not
enough context.

In Cursor you may run 2b **and** 2c when both exist — Spec/standards from the skill, bug-hunt from
Bugbot. Do not merge duplicate findings; verify once.

### 2d — Structured pass (when neither 2b nor 2c ran)

Work through the diff explicitly:

| Axis | Question |
|------|----------|
| Correctness | Edge cases, off-by-one, null/empty, timezone and date boundaries |
| Regression | Legacy URLs, API response shapes, feature flags, shared prod backends |
| Tests | Does each changed behavior have a test or a documented reason it does not? |
| Security / data | Auth, RLS, secrets, destructive SQL, single prod Supabase instances |

### 2e — Verify every finding

No finding becomes **fix-now** until you open the cited file and confirm with `file:line`
evidence — same bar as `/ask` Step 4. Drop false positives; say so in the report.

### 2f — Report before fixing

Short table: **Finding | Verdict (`fix-now` / `defer` / `false positive`) | evidence**

Only **fix-now** items are fixed in Step 3. **Defer** items go in the PR body and the Step 11
receipt. Do not grow scope fixing defers.

## Step 3 — Fix what should be fixed

Fix every **fix-now** item from Step 2. Then run what the repo gates on — its test command and its
lint/typecheck (`pnpm validate`, `pnpm test`, whatever that repo actually uses).

If a fix is larger than the change being landed, **stop and say so** rather than growing the PR.

## Step 4 — Commit what is left

Explicit paths only. Check whether uncommitted work is *yours*: `git log -3` timestamps and
`.git/index` mtime tell you if another agent is mid-edit. If it is not yours, **leave it and say
so** — do not stage it, stash it, or switch branches under it.

HEREDOC commit message. Split unrelated changes into separate commits.

## Step 5 — Push

```sh
git push -u origin HEAD
```

## Step 6 — PR

`gh pr view` first — reuse the open PR if there is one. Otherwise:

```sh
gh pr create --base <base> --title "<title>" --body "<body>"
```

Body: what changed and why, in the repo's house style. If the repo has a PR template, use it.

## Step 7 — Wait for CI

```sh
gh pr checks <N> --watch
```

Red or still-failing required checks → stop and report. Do not merge.

## Step 8 — Merge, with the deploy gate

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

## Step 9 — Sync this checkout

The whole point of the last step: do not leave the repo stranded on the merged feature branch.

```sh
git fetch origin <base>
git checkout <base>
git pull origin <base>
```

Confirm `HEAD` is the merge commit and the branch tracks `origin/<base>`.

## Step 10 — Close out the hub ticket, if there was one

**Only if this work was driven by a markdown doc under
`~/Desktop/docs-hub/projects/<project>/docs/`.** If it was not — no doc, or a plan that
lived only in this conversation — skip this step silently. Do not go hunting for a ticket to
archive, and do not invent one.

The hub owns a document lifecycle this repo knows nothing about, and **merging is the event that
fires its done-gate.** A ticket left in Development after its PR merged is why that lane fills up
with work that is actually finished.

Read `~/Desktop/docs-hub/AGENTS.md` and
`~/Desktop/docs-hub/.cursor/rules/040-plan-lifecycle.mdc` before writing to the hub — they
are the source of truth, they move, and this repo does not load them. The mechanics:

1. **Strike what landed.** `~~step~~` on the steps this PR actually shipped (`- [x] ~~step~~` for
   checkboxes). Leave the diagnosis and the evidence alone. Work you skipped is written as
   **deferred** in plain text, not struck.

2. **Check the doc's own done-gate before archiving anything.** If it named a PR and a branch, that
   PR must be merged **to the branch it named**. `/close-out` merges to the base branch — so a
   ticket whose gate is *production* is not done yet; `/ship` closes that one. Leave it in
   Development and say so in the receipt.

3. **Shipped with leftovers → it does not archive.** Add the word `deferred` to the doc's
   `**Status:**` line and leave it where it is; the badge gains a `+` and the doc keeps its place
   in Development. Only a doc with nothing left owed gets archived.

4. **Otherwise archive it**, into the day folder for **the day the PR merged, in local time** —
   not today. `gh pr view <N> --json mergedAt` returns **UTC**, so an evening merge is the previous
   day in PT. Create the day folder if it is missing; never rename or renumber one that exists —
   two checkouts landing in the same day folder is the design.

   Every path below is **hub-relative**. Step 9 left you in the code repo, so address the hub
   explicitly rather than `cd`-ing out of the checkout you just put back on its base branch:

   ```sh
   HUB=~/Desktop/docs-hub
   mkdir -p "$HUB/projects/<project>/docs/archive/<YYYY-MM-DD>"
   git -C "$HUB" mv projects/<project>/docs/<lane>/__<checkout>_<slug>.md \
                    projects/<project>/docs/archive/<YYYY-MM-DD>/✅_<slug>.md
   ```

   The rename drops the `__<checkout>_` prefix — that prefix reserved this checkout while the work
   was live, and a pulsing row nobody is working on trains the reader to ignore the pulse. `✅_` is
   the load-bearing one: it routes the doc to the Archive lane.

5. **Commit it in the hub, explicit paths, and push.** The hub is a *separate repo* from the one you
   just merged — this is a second commit, not part of the PR, and it does not go through a PR:

   ```sh
   git -C "$HUB" add projects/<project>/docs/archive/<YYYY-MM-DD>
   git -C "$HUB" commit -m "docs(<project>): archive <slug> — landed in #<N>"
   git -C "$HUB" push
   ```

   **Never `git add -A` there.** Several agents write that hub at once, and its tree usually holds
   someone else's half-finished doc. Push for the same reason: a change of yours left uncommitted
   or unpushed gets swept into another agent's unrelated commit, and the record of what landed ends
   up filed under someone else's message.

If the ticket is superseded, duplicated, or dangling rather than done, **delete it** instead of
archiving it. Do not leave it in the live tree for the next agent to re-read.

## Step 11 — The receipt

Keep it scannable. No victory lap.

**Landed** — the PR number and URL, the merge SHA, what deployed (if anything), and this checkout's
branch. State how each was verified, not that it "should" have worked. If a hub ticket drove the
work, name its new path — archived to `<day>/✅_<slug>.md`, or left in Development as Shipped+ with
what is still deferred.
**Open** — anything deliberately left behind: unstaged work that was not yours, a fix judged too
big for this PR, **defer** review findings from Step 2, a follow-up worth a ticket.
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
