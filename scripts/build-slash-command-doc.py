#!/usr/bin/env python3
"""Regenerate 091-slash-commands-claude-vs-cursor.md from the live command files."""
import pathlib

HOME = pathlib.Path.home()
OUT = pathlib.Path('~/coding-standards/docs'
                   '/workflow/091-slash-commands-claude-vs-cursor.md')

# Shared commands are read from the Claude side; the Cursor path is the same file
# via symlink, so reading either gives identical bytes.
SRC = {
    'closeout':   HOME / '.claude/commands/close-out.md',
    'ship':       HOME / '.claude/commands/ship.md',
    'prdesc':     HOME / '.claude/commands/pr-description.md',
    'claude_ask': HOME / '.claude/commands/ask.md',
    'cursor_ask': HOME / '.cursor/commands/ask.md',
    'docsupd':    HOME / '.claude/commands/docs-update.md',
    'updmd':      HOME / '.claude/commands/update-markdown.md',
    'explain':    HOME / '.claude/commands/explain.md',
}
missing = [str(v) for v in SRC.values() if not v.exists()]
if missing:
    raise SystemExit('missing source file(s):\n  ' + '\n  '.join(missing) +
                     '\n\nRun link-slash-commands.sh first.')

txt = {k: v.read_text() for k, v in SRC.items()}
n   = {k: len(v.splitlines()) for k, v in txt.items()}

def block(key):
    return "`````markdown\n" + txt[key] + "`````\n"

doc = f"""```yaml
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
| `commands/cursor/` | Cursor only — just `/ask` |

`~/.claude/commands/` and `~/.cursor/{{commands,skills}}/` are symlinks into those, so editing a
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
| `/close-out` | `~/.claude/commands/close-out.md` | `~/.cursor/commands/close-out.md` | **one file** — {n['closeout']} lines |
| `/ship` | `~/.claude/commands/ship.md` | `~/.cursor/commands/ship.md` | **one file** — {n['ship']} lines |
| `/pr-description` | `~/.claude/commands/pr-description.md` | `~/.cursor/commands/pr-description.md` | **one file** — {n['prdesc']} lines |
| `/ask` | `~/.claude/commands/ask.md` — shells out to `cursor-agent -p --mode ask --trust`. {n['claude_ask']} lines. | `~/.cursor/commands/ask.md` — shells out to `claude -p --permission-mode plan`. {n['cursor_ask']} lines. | **two files, on purpose** |
| `/docs-update` | `~/.claude/commands/docs-update.md` — {n['docsupd']} lines | — none — | Claude only |
| `/update-markdown` | `~/.claude/commands/update-markdown.md` — {n['updmd']} lines | — none — | Claude only |
| `/explain` | `~/.claude/commands/explain.md` — {n['explain']} lines | — none — | Claude only |

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
- **Do not depend on repo-local skills.** `.claude/skills/code-review/` exists in app-monorepo and
  nowhere else. A global command that invokes it is broken in every other repo.
- **Say in prose what the frontmatter collects**, so the Cursor side is not flying blind.
- **Put it in `commands/shared/`** and let `link-slash-commands.sh` wire both agents.

---

## `/close-out` — full source

One file: `~/.claude/commands/close-out.md` and `~/.cursor/commands/close-out.md` are the same
inode, symlinked to `commands/shared/close-out.md`.

{block('closeout')}
---

## `/ask` — full source

A **mirror pair**: each launches the other agent headlessly, read-only, with the plan carried
inline because the other agent sees none of this conversation. Neither adopts what comes back
until it has verified it claim by claim against the code. These are the only two files here that
are not shared.

### Claude Code

`~/.claude/commands/ask.md` → `commands/claude/ask.md`

{block('claude_ask')}
### Cursor

`~/.cursor/commands/ask.md` → `commands/cursor/ask.md`

{block('cursor_ask')}
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
"""

OUT.write_text(doc)
print(f"wrote {OUT.name}: {len(doc.splitlines())} lines")
print(f"embedded {len([k for k in ('closeout','claude_ask','cursor_ask')])} sources verbatim ✓")
