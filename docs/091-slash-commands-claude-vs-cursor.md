```yaml
description: The personal slash commands shared between Claude Code and Cursor — which are one file, which cannot be, how each agent loads them, and the full verbatim source of /close-out, /CROSSCHECK and /ask
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
| `commands/cursor/` | Cursor only — just `/ask` |

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
| `/close-out` | `~/.claude/commands/close-out.md` | `~/.cursor/commands/close-out.md` | **one file** — 180 lines |
| `/CROSSCHECK` | `~/.claude/commands/CROSSCHECK.md` | `~/.cursor/commands/CROSSCHECK.md` | **one file** — 144 lines |
| `/ship` | `~/.claude/commands/ship.md` | `~/.cursor/commands/ship.md` | **one file** — 308 lines |
| `/pr-description` | `~/.claude/commands/pr-description.md` | `~/.cursor/commands/pr-description.md` | **one file** — 76 lines |
| `/ask` | `~/.claude/commands/ask.md` — shells out to `cursor-agent -p --mode ask --trust`. 126 lines. | `~/.cursor/commands/ask.md` — shells out to `claude -p --permission-mode plan`. 48 lines. | **two files, on purpose** |
| `/docs-update` | `~/.claude/commands/docs-update.md` — 207 lines | — none — | Claude only |
| `/update-markdown` | `~/.claude/commands/update-markdown.md` — 94 lines | — none — | Claude only |

## `/close-out` lands the work — in either agent

`/close-out` means one thing now: **I have signed off on this behavior, land it.** Commit what is
left, open a PR, review it, fix what should be fixed, wait for CI, merge to the repo's base branch,
and leave the checkout on that base branch rather than stranded on the merged feature branch.

It is **repo-agnostic**, which is what lets it be one file. Three things it resolves rather than
assumes:

| | How |
|---|---|
| Base branch | `git symbolic-ref refs/remotes/origin/HEAD`, falling back to `gh repo view --json defaultBranchRef` in a fresh clone. `staging` on app-monorepo, `main` nearly everywhere else. |
| Whether merging deploys | greps `.github/workflows/*.yml` for a `push:` trigger on the resolved base branch |
| Review depth | an inline diff review — never a repo's `/code-review` skill, which exists only in app-monorepo |

**The deploy gate is the part worth knowing.** If nothing deploys on merge, it merges without
stopping. If something does, it stops and names what will publish and where. On app-monorepo a push
to `staging` fires the frontend deploy to the staging, client-staging and admin-staging hosts, plus
the docs hub and the AM image — so `/close-out` always stops there for a yes.

`/close-out` goes to the base branch. `/ship` goes to production. They are separate on purpose.

> **Historical note.** `/close-out` used to be a *false cognate*: a session-reporting command in
> Claude and a merge-to-staging command in Cursor. Typing it in the wrong window did not fail — it
> did something confidently, and the something was not what was wanted. That is resolved by the two
> meanings becoming one, not by a disambiguation gate. The old session-report behaviour survives as
> Step 9, the receipt.

## `/ask` is the one that cannot be shared

Each side names the **other** agent's binary, so the two form a loop: Claude asks Cursor, Cursor
asks Claude, and neither adopts what comes back unverified.

Merging them into one file with both directions listed would introduce a silent failure: an agent
that misidentifies itself shells out to *itself*, and returns its own reasoning as a second
opinion. Nothing errors. Two files make that impossible.

`/ask` and `/CROSSCHECK` remain a **pair**: `/ask` fetches the critique, `/CROSSCHECK` refuses to
trust it. That split exists because an LLM critique reads as authoritative and is frequently wrong
about the codebase — see [050-anti-slop.md](050-anti-slop.md).

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
  the shared commands also say in prose what their frontmatter already collects. `/CROSSCHECK`'s
  Step 0 is explicit about it: *"the context block above is auto-collected in Claude Code but not
  in Cursor — if it is empty, run `pwd` and `git rev-parse` yourself."*
- **`allowed-tools` has no Cursor equivalent.** A Cursor command cannot be sandboxed by its own
  file. The safety has to be written as an instruction (`--permission-mode plan`, "never use
  `--dangerously-skip-permissions`", "never merge red") and it is honoured by persuasion, not
  enforcement.

## Writing a command that can be shared

The bar is low, now that frontmatter is free:

- **Resolve, do not assume.** Base branch, repo root, package manager, test command — detect them.
  A command that hardcodes `staging` or `pnpm` is a Acme command wearing a global name.
- **Do not depend on repo-local skills.** `.claude/skills/code-review/` exists in app-monorepo and
  nowhere else. A global command that invokes it is broken in every other repo.
- **Say in prose what the frontmatter collects**, so the Cursor side is not flying blind.
- **Put it in `commands/shared/`** and let `link-slash-commands.sh` wire both agents.

---

## `/close-out` — full source

One file: `~/.claude/commands/close-out.md` and `~/.cursor/commands/close-out.md` are the same
inode, symlinked to `commands/shared/close-out.md`.

`````markdown
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
`````

---

## `/CROSSCHECK` — full source

Also one file. A critique is a **claim, not a verdict** — this is the command that makes that
stick, on whichever side received it.

`````markdown
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
`````

---

## `/ask` — full source

A **mirror pair**: each launches the other agent headlessly, read-only, with the plan carried
inline because the other agent sees none of this conversation. Neither adopts what comes back
without handing it to `/CROSSCHECK` first. These are the only two files here that are not shared.

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
- One call. Do not retry in a loop.

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

`/CROSSCHECK` is that workflow written out in full — atomic claims, a verdict table with
`file:line` evidence, and plan edits only for what survived. Use it rather than improvising the
verification, especially when the critique is long. `/ask` and `/CROSSCHECK` are a pair: one gets
the critique, the other refuses to trust it.
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

Two personal skills are shared the same way, from `commands/shared/`: `app-staging-data` and
`app-staging-lambda-deploy`. They stay *skills* rather than commands because they are meant to
fire on intent, not only on a typed slash.
