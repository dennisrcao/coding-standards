```yaml
description: The personal slash commands shared between Claude Code and Cursor — which are one file, which cannot be, how each agent loads them, and the full verbatim source of /close-out and /ask
globs:
alwaysApply: false
```

# Slash commands across two agents (Claude Code ↔ Cursor)

**Status:** Reference. Companion to [090-slash-commands.md](090-slash-commands.md), which is the
Claude-side roster; this one is the **two-environment** view.

Both agents are used on the same repos, on the same day, often on the same branch. **Every command
that exists on both sides is now literally one file**, symlinked into both agents — with a single
deliberate exception, `/ask`, which cannot be shared because each side has to name the *other*
agent's binary.

**The files themselves live in this repo**, under `projects/coding-standards/commands/`:

| Folder | Goes to |
|---|---|
| `commands/shared/` | **both** agents — one file, cannot drift |
| `commands/claude/` | Claude Code only |
| `commands/cursor/` | Cursor only — `/ask` and `/debate` (up to three bounded `/ask` rounds with a claims ledger) |

`~/.claude/commands/` and `~/.cursor/{commands,skills}/` are symlinks into those, so editing a
command from either agent edits the tracked file, and `git pull` carries it to every Mac. A wiped
machine is restored by cloning `docs-hub` to the Desktop and running:

```sh
bash projects/coding-standards/scripts/link-slash-commands.sh
```

That makes **this page a generated view, not the backup** — it used to be the restore path, back
when nothing was in git. Deleting it would still break nothing; deleting `commands/` now would.

## The roster, side by side

| Slash command | Claude Code | Cursor | Shared? |
|---|---|---|---|
| `/argue` | `~/.claude/commands/argue.md` | `~/.cursor/commands/argue.md` | **one file** — 83 lines — Fabric plan debate; `argue-protocol.md` is the engine |
| `/close-out` | `~/.claude/commands/close-out.md` | `~/.cursor/commands/close-out.md` | **one file** — 297 lines |
| `/ship` | `~/.claude/commands/ship.md` | `~/.cursor/commands/ship.md` | **one file** — 310 lines |
| `/pr-description` | `~/.claude/commands/pr-description.md` | `~/.cursor/commands/pr-description.md` | **one file** — 76 lines |
| `/pr-shots` | `~/.claude/commands/pr-shots.md` | `~/.cursor/commands/pr-shots.md` | **one file** — 364 lines |
| `/ask` | `~/.claude/commands/ask.md` — shells out to `cursor-agent -p --mode ask --trust`. 173 lines. | `~/.cursor/commands/ask.md` — shells out to `claude -p --permission-mode plan`. 50 lines. | **two files, on purpose** |
| `/debate` | — | `~/.cursor/commands/debate.md` — up to three bounded `claude -p` rounds (no subagents, no MCP, `--max-turns 12`), claims ledger next to the plan, Cursor verifies every claim before recording it. 109 lines. | **Cursor only** |
| `/docs-update` | `~/.claude/commands/docs-update.md` — 207 lines | — none — | Claude only |
| `/update-markdown` | `~/.claude/commands/update-markdown.md` — 94 lines | — none — | Claude only |
| `/explain` | `~/.claude/commands/explain.md` — 66 lines | — none — | Claude only |

## `/close-out` lands the work — in either agent

`/close-out` means one thing now: **I have signed off on this behavior, land it.** Commit what is
left, open a PR, thoroughly review it (unless `skip review`), fix what should be fixed, wait for CI, merge to the repo's base branch,
leave the checkout on that base branch rather than stranded on the merged feature branch, and close
out the `docs-hub` ticket that drove the work.

It is **repo-agnostic**, which is what lets it be one file. Three things it resolves rather than
assumes:

| | How |
|---|---|
| Base branch | `git symbolic-ref refs/remotes/origin/HEAD`, falling back to `gh repo view --json defaultBranchRef` in a fresh clone. `staging` on app-monorepo, `main` nearly everywhere else. |
| Whether merging deploys | greps `.github/workflows/*.yml` for a `push:` trigger on the resolved base branch |
| Review depth | merge-blocker scan always; then thorough review by default — repo `/code-review` skill when present, else Bugbot (Cursor) or a structured pass. `skip review` in `$ARGUMENTS` opts out. `fix-now` findings block merge. |

**The deploy gate is the part worth knowing.** If nothing deploys on merge, it merges without
stopping. If something does, it stops and names what will publish and where. On app-monorepo a push
to `staging` fires the frontend deploy to the staging, client-staging and admin-staging hosts, plus
the docs hub and the AM image — so `/close-out` always stops there for a yes.

**Merging is also what fires the hub's done-gate.** Step 10 strikes the landed steps in the
`docs-hub` markdown that drove the work, then either archives it to
`docs/archive/<day the PR merged>/✅_<slug>.md` or — if something shipped with leftovers — marks it
`deferred` and leaves it in Development. It is skipped silently when no hub doc drove the work, and
it commits in the hub with explicit paths, because that repo has several agents writing to it at
once. That lifecycle is the hub's, not the code repo's: `~/Desktop/docs-hub/AGENTS.md` and
`.cursor/rules/040-plan-lifecycle.mdc` remain the source of truth, and a `app-monorepo-N` checkout
loads neither.

`/close-out` goes to the base branch. `/ship` goes to production. They are separate on purpose.

> **Historical note.** `/close-out` used to be a *false cognate*: a session-reporting command in
> Claude and a merge-to-staging command in Cursor. Typing it in the wrong window did not fail — it
> did something confidently, and the something was not what was wanted. That is resolved by the two
> meanings becoming one, not by a disambiguation gate. The old session-report behaviour survives as
> Step 11, the receipt.

## `/ask` is the one that cannot be shared

Each side names the **other** agent's binary, so the two form a loop: Claude asks Cursor, Cursor
asks Claude, and neither adopts what comes back unverified.

Merging them into one file with both directions listed would introduce a silent failure: an agent
that misidentifies itself shells out to *itself*, and returns its own reasoning as a second
opinion. Nothing errors. Two files make that impossible.

`/ask` fetches the critique **and then refuses to trust it**: its Step 4 decomposes the critique
into atomic falsifiable claims, verdicts each one against the real code with `file:line` evidence,
and edits the plan only for what survived. That verification used to be a second command,
`/CROSSCHECK`; it is now inlined in both halves of the pair, because a critique that arrives
without it reads as authoritative and is frequently wrong about the codebase — see
[050-anti-slop.md](../tooling/050-anti-slop.md).

## How each agent loads them

| | Claude Code | Cursor |
|---|---|---|
| Folder | `~/.claude/commands/*.md` | `~/.cursor/commands/*.md` (commands) **and** `~/.cursor/skills/<name>/SKILL.md` (skills) |
| Name → slash | filename: `foo.md` → `/foo` | commands: filename. skills: the `name:` field |
| Frontmatter | YAML: `description`, `argument-hint`, `allowed-tools` | commands: **ignored**. skills: YAML `name`, `description`, `disable-model-invocation` |
| Arguments | `$ARGUMENTS` interpolated into the body | not interpolated — the command reads the chat |
| Context injection | ``!`cmd` `` lines run **before** the model reads the prompt | none — the model runs its own tools |
| Tool constraint | `allowed-tools` narrows what the command may call | none |
| Fires on intent | yes — also surfaces in the skills list | skills only, and `disable-model-invocation: true` turns it off |
| Scope | every repo on this machine | every repo on this machine |

**That Cursor *ignores* frontmatter rather than choking on it is what makes sharing possible.** A
shared file keeps its `allowed-tools` and its ``!`cmd` `` context lines; Claude honours them and
starts warm and sandboxed, Cursor renders them as a few lines of literal text near the top and
starts cold. The cost is cosmetic noise in one agent. The alternative — stripping them so both
agents see the same thing — would make every shared command strictly worse in Claude, and violates
090's own house rules (*"auto-collect context in the frontmatter"*, *"constrain `allowed-tools`"*).

Two consequences worth internalising:

- **A Cursor command starts colder.** No `git status`, no branch, no PR list pre-loaded. Anything a
  Claude command gets for free in its frontmatter, a Cursor command must go fetch — which is why
  the shared commands also say in prose what their frontmatter already collects — `/close-out`'s
  Step 0 restates its whole base-branch resolution as runnable `sh`, rather than leaning on the
  `Base branch:` line its frontmatter collects for Claude and not for Cursor.
- **`allowed-tools` has no Cursor equivalent.** A Cursor command cannot be sandboxed by its own
  file. The safety has to be written as an instruction (`--permission-mode plan`, "never use
  `--dangerously-skip-permissions`", "never merge red") and it is honoured by persuasion, not
  enforcement.

## Writing a command that can be shared

The bar is low, now that frontmatter is free:

- **Resolve, do not assume.** Base branch, repo root, package manager, test command — detect them.
  A command that hardcodes `staging` or `pnpm` is a Acme command wearing a global name.
- **Two install paths, same content.** app-monorepo vendors `.claude/skills/` for coworkers on a
  single-repo checkout. `commands/shared/<name>/` → `link-slash-commands.sh` is for a
  multi-root workspace (one global copy). `/close-out` invokes `code-review` from whichever path
  is present; multi-checkout workspaces should run the link script and treat globals as canonical.
- **Say in prose what the frontmatter collects**, so the Cursor side is not flying blind.
- **Put it in `commands/shared/`** and let `link-slash-commands.sh` wire both agents.

---

## `/close-out` — full source

One file: `~/.claude/commands/close-out.md` and `~/.cursor/commands/close-out.md` are the same
inode, symlinked to `commands/shared/close-out.md`.

`````markdown
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
`````

---

## `/ask` — full source

A **mirror pair**: each launches the other agent headlessly, read-only, with the plan carried
inline because the other agent sees none of this conversation. Neither adopts what comes back
until it has verified it claim by claim against the code. These are the only two files here that
are not shared.

### Claude Code

`~/.claude/commands/ask.md` → `commands/claude/ask.md`

`````markdown
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
`````

### Cursor

`~/.cursor/commands/ask.md` → `commands/cursor/ask.md`

`````markdown
# /ask — ask the other agent

`/ask` means "ask the other agent". In Cursor that is **Claude Code**; the mirror-image
`/ask` in Claude Code comes back to you. Runs it headlessly — no window needed.

Run it from the specific repo clone under review. These repos are cloned many times over
(`app-monorepo-1`..`-7`, `studio`/`studio-2`, `claw-calendar`/`-2`/`-3`), each on its own
branch. `cd` into the right clone first — reviewing the wrong clone reviews the wrong branch.

## When to use

The user asked you to cross-check with Claude, get a second opinion, or verify a plan
against another model. Do not run this unprompted — it costs the user's Claude quota.

## How

Claude Code starts with **no context from this chat**. It sees only your prompt and the
repo, so the prompt must carry the plan or diff inline — not a reference to it.

```bash
cd "<the clone under review>" && claude -p --permission-mode plan "<your prompt>"
```

- `--permission-mode plan` keeps it read-only. Never use `--dangerously-skip-permissions`.
- Add `--model opus` for the strongest review; omit for the default.
- It may take a minute or two on a large diff. Let it finish.
- One call. Do not retry in a loop. For a multi-round argument use `/debate`, which bounds
  each round (no subagents, no MCP, `--max-turns`) and carries a claims ledger between rounds.

Ask for disagreement, not a summary. Include:

- The plan or diff, complete and inline.
- What specifically to attack.
- "For each objection give the file and line, what breaks, and the input or state that
  triggers it. If you cannot name a file and line, say so rather than speculating. If a
  step is sound, say so — do not manufacture objections."

## Then verify it

Show the user the raw response first. Then **check its claims against the actual code
before accepting any of them.** Claude Code is confidently wrong often enough that an
unverified critique is a liability. For each claim, open the file it names and confirm the
thing it describes exists. Report which claims held up and which did not, with file:line
evidence. Do not soften a refutation into "both views have merit" — if it is wrong, say so.

Work it as **atomic claims, not a verdict**, especially when the critique is long: split it into
a numbered list of falsifiable assertions, give each one CONFIRMED / REFUTED / MISREAD /
UNVERIFIABLE with `file:line` evidence, print that table before touching anything, and edit the
plan only for what survived. If nothing was confirmed, say the plan stands as written. `/ask`
fetches the critique; this step is what refuses to trust it.
`````

---

## Keeping this file honest

Nothing regenerates this page on its own. Edit a command and the blocks above go stale silently —
so regenerate rather than hand-patching a block:

```sh
python3 projects/coding-standards/scripts/build-slash-command-doc.py   # re-reads the live files, rewrites this doc
bash    projects/coding-standards/scripts/link-slash-commands.sh       # re-point a machine at the repo (idempotent)
ls -l ~/.claude/commands/ ~/.claude/skills/ ~/.cursor/commands/ ~/.cursor/skills/
```

Anything in those folders that is **not** a symlink into `commands/` is untracked and will not
survive a wipe — that `ls -l` is the audit. The link script also **prunes**: it deletes obsolete
and dangling links, which is how the old `~/.cursor/skills/close-out/` skill gets removed rather
than lingering as a second, stale `/close-out`.

Personal skills are shared the same way, from `commands/shared/<name>/SKILL.md` — see the roster in
[090-slash-commands.md](090-slash-commands.md) under **Global skills**. They stay *skills* rather
than commands because they are meant to fire on intent, not only on a typed slash. After adding or
renaming one, extend the `SHARED_SKILLS` array in `link-slash-commands.sh` and re-run the script.
