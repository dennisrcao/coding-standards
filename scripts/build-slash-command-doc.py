#!/usr/bin/env python3
"""Regenerate 091-slash-commands-claude-vs-cursor.md from the live command files."""
import pathlib

HOME = pathlib.Path.home()
OUT = pathlib.Path('~/coding-standards/docs'
                   '/091-slash-commands-claude-vs-cursor.md')

SRC = {
    'claude_closeout': HOME / '.claude/commands/close-out.md',
    'cursor_closeout': HOME / '.cursor/skills/close-out/SKILL.md',
    'claude_ask':      HOME / '.claude/commands/ask.md',
    'cursor_ask':      HOME / '.cursor/commands/ask.md',
    'claude_xcheck':   HOME / '.claude/commands/CROSSCHECK.md',
    'cursor_xcheck':   HOME / '.cursor/commands/CROSSCHECK.md',
}
txt = {k: v.read_text() for k, v in SRC.items()}
n   = {k: len(v.splitlines()) for k, v in txt.items()}

def block(key):
    return "`````markdown\n" + txt[key] + "`````\n"

doc = f"""```yaml
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
`~/.claude/commands/` and `~/.cursor/{{commands,skills}}/` are symlinks into it, so editing a command
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
| `/close-out` | `~/.claude/commands/close-out.md` — **end a work session honestly**: sweep every repo touched, account for every PR, reconcile the plan markdown, name what is blocked on a human, report background jobs, save memory. Merges nothing. {n['claude_closeout']} lines. | `~/.cursor/skills/close-out/SKILL.md` — **land an open Acme PR onto `staging`**: review, fix blockers, commit WIP, wait for CI, merge, checkout staging, reply `DONE`. {n['cursor_closeout']} lines. |
| `/ask` | `~/.claude/commands/ask.md` — shells out to `cursor-agent -p --mode ask --trust`, saves the critique to disk, hands off to `/CROSSCHECK`. {n['claude_ask']} lines. | `~/.cursor/commands/ask.md` — shells out to `claude -p --permission-mode plan`, hands off to `/CROSSCHECK`. {n['cursor_ask']} lines. |
| `/CROSSCHECK` | `~/.claude/commands/CROSSCHECK.md` — decompose the critique into atomic claims, verify each against the real code, verdict table, edit the plan only for what survived. {n['claude_xcheck']} lines. | `~/.cursor/commands/CROSSCHECK.md` — same workflow, pointed back at Claude's critiques. {n['cursor_xcheck']} lines. |
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

{block('claude_closeout')}
### Cursor

Install: save as `~/.cursor/skills/close-out/SKILL.md`.

{block('cursor_closeout')}
---

## `/ask` — full source

A **mirror pair**: each launches the other agent headlessly, read-only, with the plan carried
inline because the other agent sees none of this conversation. Neither adopts what comes back
without handing it to `/CROSSCHECK` first.

### Claude Code

Install: save as `~/.claude/commands/ask.md`.

{block('claude_ask')}
### Cursor

Install: save as `~/.cursor/commands/ask.md`.

{block('cursor_ask')}
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

{block('claude_xcheck')}
### Cursor

Install: save as `~/.cursor/commands/CROSSCHECK.md`.

{block('cursor_xcheck')}
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
"""

OUT.write_text(doc)
print(f"wrote {OUT.name}: {len(doc.splitlines())} lines")
for k in SRC:
    assert txt[k] in doc, f"{k} not embedded verbatim"
print("all six sources embedded verbatim ✓")
