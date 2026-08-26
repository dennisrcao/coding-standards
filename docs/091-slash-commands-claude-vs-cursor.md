```yaml
description: The personal slash commands that exist in BOTH Claude Code and Cursor — where each lives, how each loads, and the full verbatim source of /close-out, /ask and /CROSSCHECK on both sides
globs:
alwaysApply: false
```

# Slash commands across two agents (Claude Code ↔ Cursor)

**Status:** Reference. Companion to [090-slash-commands.md](090-slash-commands.md), which is the
Claude-side roster; this one is the **two-environment** view.

Both agents are used on the same repos, on the same day, often on the same branch. They read
different folders and different file formats, and the three commands that exist on both sides
**cannot be collapsed into one file** — each has to name the other agent's binary.

**The files themselves live in this repo**, under `projects/coding-standards/commands/`.
`~/.claude/commands/` and `~/.cursor/{commands,skills}/` are symlinks into it, so editing a command
from either agent edits the tracked file, and `git pull` carries it to every Mac. A wiped machine is
restored by cloning `docs-hub` to the Desktop and running:

```sh
bash projects/coding-standards/scripts/link-slash-commands.sh
```

That makes **this page a generated view, not the backup** — it used to be the restore path, back
when nothing was in git. Deleting it would still break nothing; deleting `commands/` now would.

## The roster, side by side

| Slash command | Claude Code | Cursor |
|---|---|---|
| `/close-out` | `~/.claude/commands/close-out.md` — **end a work session honestly**: sweep every repo touched, account for every PR, reconcile the plan markdown, name what is blocked on a human, report background jobs, save memory. Merges nothing. 139 lines. | `~/.cursor/skills/close-out/SKILL.md` — **land an open Acme PR onto `staging`**: review, fix blockers, commit WIP, wait for CI, merge, checkout staging, reply `DONE`. 77 lines. |
| `/ask` | `~/.claude/commands/ask.md` — shells out to `cursor-agent -p --mode ask --trust`, saves the critique to disk, hands off to `/CROSSCHECK`. 126 lines. | `~/.cursor/commands/ask.md` — shells out to `claude -p --permission-mode plan`, hands off to `/CROSSCHECK`. 48 lines. |
| `/CROSSCHECK` | `~/.claude/commands/CROSSCHECK.md` — decompose the critique into atomic claims, verify each against the real code, verdict table, edit the plan only for what survived. 106 lines. | `~/.cursor/commands/CROSSCHECK.md` — same workflow, pointed back at Claude's critiques. 94 lines. |
| `/ship` | `~/.claude/commands/ship.md` | **the same file** — `~/.cursor/commands/ship.md` is a symlink to the Claude copy |
| `/docs-update` | `~/.claude/commands/docs-update.md` | — none — |
| `/pr-description` | `~/.claude/commands/pr-description.md` | — none — |
| `/update-markdown` | `~/.claude/commands/update-markdown.md` | — none — |

`/ask` and `/CROSSCHECK` are a **pair, on both sides**: `/ask` fetches the critique, `/CROSSCHECK`
refuses to trust it. That split exists because an LLM critique reads as authoritative and is
frequently wrong about the codebase — see [050-anti-slop.md](050-anti-slop.md). Each agent's `/ask`
names *the other* agent's binary, so the two form a loop: Claude asks Cursor, Cursor asks Claude,
and neither adopts what comes back unverified.

## `/close-out` is a false cognate — now guarded

**The same slash word triggers two unrelated workflows.** In Claude it is a *reporting* command
that deliberately refuses to merge anything ("Do not merge, push, or delete anything the operator
has not asked for"). In Cursor it is a *merging* command whose entire purpose is to land a PR on
`staging` without stopping to ask.

Typing `/close-out` in the wrong window did not fail — it did something confidently, and the
something was not what was wanted. They are not worth collapsing into one file: both are correct
for their agent.

**The fix** is a disambiguation gate at the top of each, naming the other and telling the agent to
stop rather than guess:

> This is not the Cursor `/close-out`. […] If what was actually wanted is *"close out the PR / land
> it on staging"*, say so in one line and stop — that job belongs in the Cursor window, not here.

Both gates are in the verbatim sources below. They cost one paragraph and remove the only way this
pair could silently do the wrong thing.

## How each agent loads them

| | Claude Code | Cursor |
|---|---|---|
| Folder | `~/.claude/commands/*.md` | `~/.cursor/commands/*.md` (commands) **and** `~/.cursor/skills/<name>/SKILL.md` (skills) |
| Name → slash | filename: `foo.md` → `/foo` | commands: filename. skills: the `name:` field |
| Frontmatter | YAML: `description`, `argument-hint`, `allowed-tools` | commands: none. skills: YAML `name`, `description`, `disable-model-invocation` |
| Arguments | `$ARGUMENTS` interpolated into the body | not interpolated — the command reads the chat |
| Context injection | ``!`cmd` `` lines run **before** the model reads the prompt | none — the model runs its own tools |
| Tool constraint | `allowed-tools` narrows what the command may call | none |
| Fires on intent | yes — also surfaces in the skills list | skills only, and `disable-model-invocation: true` turns it off |
| Scope | every repo on this machine | every repo on this machine |

Two consequences worth internalising:

- **A Cursor command starts colder.** No `git status`, no branch, no PR list pre-loaded. Anything a
  Claude command gets for free in its frontmatter, a Cursor command must instruct the model to go
  fetch — which is why both Cursor commands here open by pinning the clone in prose rather than
  resolving it: `/ask` hands it a literal `cd "<the clone under review>"`, and `/CROSSCHECK`
  opens with *"state the clone and branch in one line … and run every command from there."*
- **`allowed-tools` has no Cursor equivalent.** A Cursor command cannot be sandboxed by its own
  file. The safety has to be written as an instruction (`--permission-mode plan`, "never use
  `--dangerously-skip-permissions`") and it is honoured by persuasion, not enforcement.

## `/ship` is the pattern to copy

Every command here is now a symlink into `commands/`, but `/ship` is the one where **both agents
point at the same file**:

```sh
ln -s "$REPO/commands/claude/ship.md" ~/.claude/commands/ship.md
ln -s "$REPO/commands/claude/ship.md" ~/.cursor/commands/ship.md
```

One file, both agents, cannot drift. It works because `/ship` carries no `$ARGUMENTS`
interpolation and no ``!`cmd` `` context lines — the parts Cursor would silently ignore. Any
command written to that restraint should be symlinked rather than copied.

`/ask` cannot be symlinked: each side has to name **the other** agent's binary and flags.
`/CROSSCHECK` is close to symlinkable but not quite — Claude's version reads the critique files
`/ask` drops in `$TMPDIR/crosscheck/` via frontmatter, which Cursor cannot do.

---

## `/close-out` — full source

### Claude Code

Install: save as `~/.claude/commands/close-out.md`.

`````markdown
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
`````

### Cursor

Install: save as `~/.cursor/skills/close-out/SKILL.md`.

`````markdown
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
`````

---

## `/ask` — full source

A **mirror pair**: each launches the other agent headlessly, read-only, with the plan carried
inline because the other agent sees none of this conversation. Neither adopts what comes back
without handing it to `/CROSSCHECK` first.

### Claude Code

Install: save as `~/.claude/commands/ask.md`.

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

Install: save as `~/.cursor/commands/ask.md`.

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

## `/CROSSCHECK` — full source

The other half of the pair. A critique is a **claim, not a verdict** — this is the command that
makes that stick, on whichever side received it.

The two differ in one structural way: Claude's opens with auto-collected context, including the
critique files `/ask` writes to `$TMPDIR/crosscheck/`, so it usually finds the critique without
being told where it is. Cursor's has no context injection, so it has to be pointed at the critique
(a file, an attached screenshot, or pasted text) and it says so explicitly.

### Claude Code

Install: save as `~/.claude/commands/CROSSCHECK.md`.

`````markdown
---
description: Another LLM critiqued my plan — verify its claims against the codebase, then push back or update the plan
argument-hint: "[path to the plan, path to the critique, or extra context — optional]"
allowed-tools: Bash(git:*), Bash(gh:*), Bash(ls:*), Bash(find:*), Bash(rg:*), Read, Grep, Glob, Edit, Write
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

I took a plan you (or another session) wrote and ran it past a *different* model — `/ask`, Claude Code in another window, a live Cursor chat, whatever. It came back with a critique. That critique is what you're evaluating. **It is a claim, not a verdict.** A second model is confidently wrong often enough that you must verify everything before changing a single line of the plan.

## Step 1 — Find the critique

In priority order:

1. **A critique file written by `/ask`.** Check the critique files listed in the context above — most recent first. This is the usual case now: the other model was invoked headlessly, so its response is already text on disk and needs no transcription.
2. A path in my extra instruction above.
3. **An image attached to this message** — a screenshot of the other model's response. Read it carefully and transcribe every distinct claim it makes, including ones in code blocks and diffs.
4. Pasted text in my extra instruction above.
5. If none of those, check the most recent screenshot listed in the context. Confirm with me before assuming it's the right one.

If a critique file and a screenshot are both present, ask which one I mean rather than assuming the newer.

If you cannot find a critique, **stop and ask** — do not invent one.

## Step 2 — Find the plan being critiqued

Look in my extra instruction, then the recently-touched markdown listed above, then `~/Desktop/*.md` (drafts often start on the Desktop before they're filed), then `~/Desktop/docs-hub/projects/*/docs/`. Match on the subject matter of the critique — ticket number, file names, function names it mentions.

State which file you settled on and why, in one line, before you go further. If two candidates are plausible, ask.

## Step 3 — Decompose the critique into checkable claims

Write out a numbered list. One row per **atomic, falsifiable** assertion. Split compound complaints apart — "this is racy and also the store is keyed wrong" is two claims.

Discard anything that isn't checkable against the codebase: style preferences, "consider also…", vague hedges. Note them in a single line at the end as *unfalsifiable — ignored*.

## Step 4 — Verify each claim against the actual codebase

This is the whole point of the command. For each claim:

- **Read the real code.** Open the file and the function it names. If it names no file, find the code yourself with Grep/Glob.
- **Check whether the thing it describes actually exists.** Other models hallucinate file paths, prop names, hook names, and function signatures constantly. A claim about `useSessionStore` is dead on arrival if that hook does not exist.
- **Run something where you can.** Tests, a type check, `git log -S` to see when a line arrived, `gh pr view` for prior review context. Evidence beats reasoning.
- **Check the plan actually says what the critique says it says.** A large fraction of cross-model critiques attack a misreading of the plan.

Assign one verdict per claim:

| Verdict | Meaning |
| --- | --- |
| **CONFIRMED** | Verified true against the code. The plan is wrong or incomplete here. |
| **REFUTED** | Verified false. Name the specific evidence that kills it. |
| **MISREAD** | True of some other code, or of a plan that isn't this one. |
| **UNVERIFIABLE** | Can't be settled from the codebase — a product/design judgment call. Say whose call it is. |

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

- **Where I disagree** — for each REFUTED / MISREAD claim, one short paragraph. Be direct: state what the other model got wrong and what's actually true. Do not soften it into "both perspectives have merit". If it's wrong, say it's wrong and show why. Doubling down on a verified position is the correct behavior here — a critique from another model carries no authority on its own.
- **Where it's right** — for each CONFIRMED claim, what the plan has to change.
- **Open questions** — UNVERIFIABLE claims, phrased as a question to me.

## Step 6 — Update the plan

Only for **CONFIRMED** claims. Edit the plan markdown in place:

- Fix the wrong step, add the missing step, correct the wrong file path — surgically. Don't rewrite sections that were fine.
- Preserve the plan's existing structure, heading style, and voice.
- Add a short changelog entry at the bottom of the plan under `## Cross-check revisions` — date, which claims were adopted, one line each. If that heading already exists, append to it.
- Do **not** silently drop or reword anything the critique got wrong. The plan keeps its original position on those.

Boundary: edit the plan markdown itself, wherever it lives — Desktop drafts and `~/Desktop/docs-hub` are both fair game. Don't fix the underlying code as part of a cross-check; findings go in the plan. Do not commit or push unless I ask.

If **zero** claims were confirmed, do not touch the file. Say so plainly: the plan stands as written, and here is why each objection failed.

## Style

- Verify before you agree. Deference to another model is not rigor.
- Verify before you disagree too — a confident refutation you didn't check is the same failure mode in the other direction.
- Specific over general. File paths, line numbers, real command output.
- No "great catch!", no "you're absolutely right", no apology for the original plan.
`````

### Cursor

Install: save as `~/.cursor/commands/CROSSCHECK.md`.

`````markdown
# /CROSSCHECK — a critique is a claim, not a verdict

Another model critiqued a plan of ours — via `/ask`, a Claude Code window, a pasted screenshot,
whatever. **Verify every claim against the real code before changing a single line of the plan.**
A second model is confidently wrong often enough that adopting its critique unverified is worse
than ignoring it: it launders a hallucinated file path into a plan the next session acts on.

The mirror-image `/CROSSCHECK` in Claude Code does the same job on critiques that came from you.

## Step 0 — Pin the clone

These repos are cloned many times over (`app-monorepo-1`..`-7`, `studio`/`studio-2`,
`claw-calendar`/`-2`/`-3`), each on its own branch. Verifying a claim against the wrong checkout
produces a confident REFUTED that is simply false. State the clone and branch in one line before
you check anything, and run every command from there.

## Step 1 — Find the critique, and the plan it attacks

The critique: a file the user pointed at, an image attached to the message (transcribe every
distinct claim, including ones inside code blocks and diffs), or text they pasted. If you cannot
find one, **stop and ask** — do not invent one.

The plan: match on the critique's subject matter — ticket number, file names, function names it
mentions. Look at what the user named, then recently-touched markdown, then `~/Desktop/*.md`
(drafts start there), then `~/Desktop/docs-hub/projects/*/docs/`.

State which plan file you settled on and why, in one line. If two are plausible, ask.

## Step 2 — Decompose into atomic claims

A numbered list, one row per **falsifiable** assertion. Split compound complaints apart — "this is
racy and also the store is keyed wrong" is two claims.

Discard what cannot be checked against the codebase: style preferences, "consider also…", vague
hedges. Note them in one line at the end as *unfalsifiable — ignored*.

## Step 3 — Verify each one against the actual code

This is the whole point of the command.

- **Open the real file and function it names.** If it names none, find the code yourself.
- **Check the thing it describes exists at all.** Other models hallucinate file paths, prop names,
  hook names and signatures constantly. A claim about `useSessionStore` is dead on arrival if that
  hook does not exist.
- **Run something.** Tests, a type check, `git log -S` for when a line arrived, `gh pr view` for
  prior review context. Evidence beats reasoning.
- **Check the plan actually says what the critique says it says.** A large fraction of cross-model
  critiques attack a misreading of the plan.

One verdict per claim:

| Verdict | Meaning |
| --- | --- |
| **CONFIRMED** | Verified true against the code. The plan is wrong or incomplete here. |
| **REFUTED** | Verified false. Name the specific evidence that kills it. |
| **MISREAD** | True of some other code, or of a plan that isn't this one. |
| **UNVERIFIABLE** | Cannot be settled from the codebase — a product or design call. Say whose. |

Never write a verdict you did not verify. "Probably fine" is not a verdict — go look.

## Step 4 — Report before touching the plan

```
## Cross-check verdict

| # | Claim (one line) | Verdict | Evidence |
| --- | --- | --- | --- |
| 1 | ... | REFUTED | `shotlist-store.ts:88` keys by projectId — the critique's `bySession` map does not exist |
```

Evidence is `file.ts:line`, real command output, or a commit SHA. Not prose.

Then: **where we disagree** (one short paragraph per REFUTED/MISREAD — state plainly what the other
model got wrong and what is actually true; do not soften it into "both perspectives have merit"),
**where it is right** (what each CONFIRMED claim changes in the plan), and **open questions**
(UNVERIFIABLE claims, phrased as a question to the user).

## Step 5 — Update the plan, for CONFIRMED claims only

Edit the plan markdown in place, surgically — fix the wrong step, add the missing one, correct the
wrong path. Preserve its structure and voice. Append a dated entry under `## Cross-check revisions`
at the bottom, one line per adopted claim.

Do **not** silently drop or reword anything the critique got wrong; the plan keeps its original
position there. If **zero** claims were confirmed, do not touch the file — say so plainly: the plan
stands, and here is why each objection failed.

Findings go in the plan, not the code. Do not commit or push unless asked.

## Style

- Verify before you agree. Deference to another model is not rigor.
- Verify before you disagree too — an unchecked refutation is the same failure in the other direction.
- No "great catch", no "you're absolutely right", no apologising for the original plan.
`````

---

## Keeping this file honest

Nothing regenerates this page on its own. Edit a command and the block below goes stale silently —
so regenerate rather than hand-patching a block:

```sh
python3 projects/coding-standards/scripts/build-slash-command-doc.py   # re-reads all six files, rewrites this doc
bash    projects/coding-standards/scripts/link-slash-commands.sh       # re-point a machine at the repo (idempotent)
ls -l ~/.claude/commands/ ~/.claude/skills/ ~/.cursor/commands/ ~/.cursor/skills/
```

Anything in those folders that is **not** a symlink into `commands/` is untracked and will not
survive a wipe — that `ls -l` is the audit.

Two personal Cursor skills are shared with Claude the old way — `~/.claude/skills/app-staging-data`
and `~/.claude/skills/app-staging-lambda-deploy` are symlinks to the `~/.cursor/skills/` copies.
One file each, so they cannot drift between agents, but **they are not in this repo** (they carry a
client's staging infra: Secrets Manager ids, AWS account, RDS paths) and so are not backed up.

`~/.cursor/skills-cursor/` is **Cursor's own shipped skills** (`review`, `loop`, `create-rule`, …),
not personal ones. Nothing there needs mirroring; it comes back with the install.

`~/.claude/commands/CROSSCHECK.md.bak` is a stale pre-`/ask` backup — it predates the critique-file
handoff. Not mirrored here; delete it whenever.
