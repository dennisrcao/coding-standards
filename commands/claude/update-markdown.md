---
description: Cross off what we actually implemented in the plan markdown we've been following, and mark finished sections with ✅
argument-hint: "[path to the markdown, or which plan I mean — optional]"
allowed-tools: Bash(git:*), Bash(ls:*), Bash(find:*), Bash(rg:*), Read, Grep, Glob, Edit
---

## Context (auto-collected)

- Working dir: !`pwd`
- Current branch: !`git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "not a repo"`
- Commits today: !`git log --oneline --since=midnight 2>/dev/null | head -20 || true`
- Uncommitted files: !`git status --porcelain 2>/dev/null | head -30 || true`
- Recently touched plan/doc markdown: !`( find ~/Desktop -maxdepth 1 -name "*.md" -mtime -3; find ~/Desktop/docs-hub -name "*.md" -not -path "*/node_modules/*" -not -path "*/site/*" -mtime -3 ) 2>/dev/null | head -20`

Extra instruction from me: $ARGUMENTS

## Your task

We've been working through a plan written in a markdown file. Update that file in place so it reflects what is **actually done** as of right now.

## Step 1 — Identify the markdown

In priority order:

1. A path in my extra instruction above.
2. The plan file we've been reading, editing, or referring to **in this conversation**. This is the usual case — you already know which one it is.
3. If neither is clear, list the two or three most likely candidates from the context above with their titles, and **ask me which one**. Do not guess and start editing.

Then say, in one line, which file you're updating: `Updating <path>`.

## Step 2 — Establish what's actually done

**Do not trust the conversation alone.** Before striking anything, verify against the repo:

- Read the current state of the files the plan says to change — is the change actually there?
- `git log` / `git diff` for work done this session.
- Ran tests, passing builds, verified behavior — only what genuinely happened.

An item is **done** only if the change exists in the working tree (or is committed). An item that we discussed, planned, or half-started is **not** done.

If an item's status is genuinely unclear, leave it untouched and list it under "Ambiguous" in your summary rather than guessing either way.

## Step 3 — Edit the markdown, line by line

Work through the file top to bottom. Preserve everything — structure, ordering, indentation, code blocks, tables. You are annotating, never rewriting or deleting.

**Completed line items** — wrap the item's text in `~~ ~~`:

```
- ~~Add `keepOwnedBy` filter to the campaigns query~~
- [ ] Update the FTU lane to count own sessions   →   - [x] ~~Update the FTU lane to count own sessions~~
```

- If the doc uses checkboxes, flip `- [ ]` to `- [x]` **and** strike the text.
- Strike only the item text. Keep the bullet marker, the checkbox, the indentation, and any nested children on their own lines (strike those separately if they're done).
- Never strike inside a fenced code block — code stays literal.
- Leave inline file paths and identifiers readable: `~~Add the filter to `campaigns.service.ts`~~` is fine, don't mangle backticks.

**Fully completed sections** — when every item under a heading is struck, prefix that heading with ✅:

```
### ✅ Change 2 — Campaigns page render-level filtering
```

**The whole document** — when every section is complete, prefix the document's H1 title with ✅:

```
# ✅ Own-only campaigns — master plan
```

Only the H1 title text changes. **Do not rename the file.**

**Partially complete sections** get no emoji — the struck lines already show the progress.

If the plan has a status line, metadata block, or "Next steps" section, update it to match reality too (e.g. drop next-steps that are now done). Don't invent one if it isn't there.

## Step 4 — Report back

Short summary, no ceremony:

- The path you edited.
- Count: `7 of 11 items struck, 2 sections marked ✅`.
- What's **still open**, as a short list — this is the part I actually read.
- Anything you found that the plan didn't anticipate, or where the implementation diverged from what the plan described.
- Anything ambiguous you deliberately left alone.

## Rules

- **Never strike something you didn't verify.** A false ✅ is worse than an unmarked done item — I'll trust it and stop checking.
- Never delete a plan item because it's done. Struck-through is the record.
- Never delete a plan item because it's obsolete — strike it if implemented, otherwise leave it and note it in your summary.
- Don't add new items, don't reword existing ones, don't reorder.
- Don't commit or push. Just edit the file.
- ✅ is the only emoji. No 🎉, no 🚀.
