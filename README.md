# Coding Standards — a library, not this repo's rules

**Read this before adding, editing, or applying anything in `docs/`.**

This project is a **portable library of coding conventions meant to be copied into other
repos**. Nothing here configures `docs-hub` itself. A standard lands in `docs/` first,
then travels — adapted — into whichever repo needs it.

## Single source of truth

`projects/coding-standards/docs/<NNN>-<slug>.md` is the **only** canonical copy of a standard.

- **Do not** keep a second copy of a standard inside this repo (no mirrored `.mdc` under
  `.cursor/rules/`). Two files drift, and nothing checks that they agree.
- Copies live in **target repos**, where they are expected to diverge slightly — globs get
  rewritten for that repo's layout.
- If a rule needs changing, change it here and re-copy outward. Never edit a downstream copy
  and hope it flows back.

> `.cursor/rules/` **in this repo** is a different thing entirely: it governs how agents edit
> `docs-hub` (a docs site). A standard about, say, React data fetching has no business
> there. Don't confuse "rules for working here" with "the library we ship."

## The consumer is Claude Code *or* Cursor — one file serves both

Assume the reader uses either. Both tools load the same `.mdc` file in the target repo:

| Tool | How it loads the rule |
|------|----------------------|
| **Cursor** | auto-discovers `.cursor/rules/*.mdc` as Project Rules, matched by `globs` |
| **Claude Code** | `CLAUDE.md` `@`-imports the same file: `@.cursor/rules/020-zustand.mdc` |

This is why every doc in `docs/` **opens with a fenced `yaml` block carrying exactly Cursor's
frontmatter fields** (`description`, `globs`, `alwaysApply`). That block is not decoration — it
is the frontmatter of the file this doc becomes.

## Adopting a standard into a target repo

1. Copy `docs/<NNN>-<slug>.md` → `<repo>/.cursor/rules/<NNN>-<slug>.mdc`.
2. Swap the opening ` ```yaml ` fence for `---` frontmatter (drop the closing fence too).
3. **Rewrite `globs` for that repo's layout.** The library assumes `apps/web/src/…`; a flat repo
   needs `src/…`. A rule whose globs don't match is a rule that never fires.
4. Trim to what that repo needs — a downstream copy may be a narrow extract, not the whole doc.
5. Add `@.cursor/rules/<NNN>-<slug>.mdc` to the repo's `CLAUDE.md` so Claude reads it too, and
   note in `CLAUDE.md` that the canonical copy lives here.

`~/Desktop/studio` is the worked example: three rules adopted, globs flattened to `src/…`, all
three `@`-imported at the bottom of its `CLAUDE.md`.

## Writing a new standard

- **Numbering** — `001` general, `005` backend, `010`–`029` frontend, `030`–`049` tooling &
  quality, `050`+ process and environment. Leave gaps; standards get inserted between.
- **Shape** — fenced `yaml` frontmatter block → `# Title (scope)` → **Do** / **Don't** →
  `## Canonical shape` with real code. Rules carry their reason inline; a rule without a
  rationale gets argued with instead of followed.
- **Ground it.** Cite the real repo and file the pattern (or the bug) came from. Standards
  derived from problems this codebase actually hit get followed; generic advice does not.
- **Cross-link** rather than restate — e.g. `020-zustand.md` points at `025-tanstack-query.md`
  for the server/client-state boundary instead of duplicating it.

## What else lives here

| Path | What it is |
|------|-----------|
| `docs/` | the standards — canonical, portable |
| `docs/090-slash-commands.md` | **the one exception** — a reference copy of the personal `~/.claude/commands/*.md`, which live outside git. Not a standard to copy into a repo; a restore path if a machine is wiped |
| `eslint-rules/` | custom rules the standards depend on (`packed-named-imports.mjs` + test) |
| `scripts/` | tooling a standard calls for (`find-unused-scss-classes.mjs`) |

Those are copied outward the same way: the standard that needs them says so, and names the file.
