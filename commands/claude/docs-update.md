---
description: Sweep this project's docs-hub docs/development/ — verify each plan against the real repo, strike what landed, archive what's done, delete what's dangling, and flatten unearned section folders.
argument-hint: "[optional: project name, section, or a single doc path — e.g. 'design-styles', 'Museum', 'skip archiving']"
allowed-tools: Bash(git:*), Bash(gh:*), Bash(pwd), Bash(ls:*), Bash(cat:*), Bash(sed:*), Bash(find:*), Bash(rg:*), Bash(grep:*), Bash(date), Bash(basename:*), Bash(head:*), Bash(tail:*), Bash(wc:*), Bash(mv:*), Bash(rm:*), Read, Grep, Glob, Edit, Write
---

## Context (auto-collected)

- Now: !`date '+%Y-%m-%d %H:%M %Z'`
- Working dir: !`pwd`
- Enclosing clone: !`git rev-parse --show-toplevel 2>/dev/null || echo "NONE"`
- Branch @ SHA: !`git rev-parse --abbrev-ref HEAD 2>/dev/null` @ !`git rev-parse --short HEAD 2>/dev/null || echo "n/a"`
- Recent commits here: !`git log --oneline -25 2>/dev/null || true`
- Uncommitted here: !`git status --porcelain 2>/dev/null | head -30 || true`
- Merged-in PRs recently: !`gh pr list --state merged --limit 15 --json number,title,mergedAt,baseRefName -q '.[] | "#\(.number) \(.baseRefName) \(.mergedAt[0:10]) \(.title)"' 2>/dev/null || echo "(gh unavailable / not a GitHub repo)"`
- Open PRs: !`gh pr list --state open --limit 15 --json number,title,headRefName -q '.[] | "#\(.number) \(.headRefName) \(.title)"' 2>/dev/null || echo "(none / gh unavailable)"`
- Docs hub projects: !`ls ~/Desktop/docs-hub/projects 2>/dev/null`
- Docs hub state: !`git -C ~/Desktop/docs-hub log --oneline -3 2>/dev/null; echo "--- dirty ---"; git -C ~/Desktop/docs-hub status --porcelain 2>/dev/null | head -20`

Extra instruction from me: $ARGUMENTS

---

# /docs-update

Docs rot in a specific direction: a plan describes work that shipped three days ago as if it
were still pending, a README lists a doc that has since been archived, and a folder
quietly becomes a junk drawer. **The next agent reads that and acts on it.** This command's
job is to make `projects/<project>/docs/development/` tell the truth about the repo as it
exists right now.

The hub is `~/Desktop/docs-hub`.

## HARD RULES

- **Verify against the repo, not against the prose.** A plan step is struck because you found
  the code / the merged PR / the file, not because the doc's own Status line sounds confident.
  If you cannot verify a step, leave it alone and list it as unverified in your report.
- **Never strike a step you only *believe* landed.** Under-striking is recoverable; a struck
  step that never shipped is a lie the next session builds on.
- **Confirm the done-gate before archiving.** If the plan named a PR, that PR must be **merged**
  to the branch it named. An open PR, a local-only fix, or "tests pass" is not done.
- **Ask before deleting or archiving.** Both are `git mv`/`rm` in a shared hub. Propose the list,
  get a yes, then execute. Editing a doc in place needs no permission.
- **Other agents work in this hub concurrently.** Re-read the tree (`git log --oneline -3`,
  `git status`) before writing into it — folders get reorganised underneath you. Stage explicit
  paths; never `git add -A`.
- **Do not rewrite diagnosis or evidence.** Only step/todo lines get struck. The "what was
  actually verified" blocks stay exactly as written — that is the audit trail.

---

## Step 1 — Resolve which project

In priority order:

1. A project named in my extra instruction above.
2. The enclosing clone's basename → `docs-hub/projects/<basename>`. Strip a trailing
   `-2`/`-3` clone suffix (`claw-calendar-2` → `claw-calendar`).
3. If that misses, grep the hub's `projects/*/project.json` for a `repos.*.folder` matching this
   clone's folder name.
4. If I ran this from inside `docs-hub` itself with no argument, list the projects whose
   `docs/development/` has been touched most recently and **ask which one**. Do not sweep all of them.

Say in one line: `Sweeping projects/<project>/docs/development/ against <clone> @ <branch>/<sha>`.

If I named a single section or doc, scope everything below to that.

## Step 2 — Re-read the conventions (do not work from memory)

Read these fresh every run — they are the source of truth and they change:

- `docs-hub/AGENTS.md` — where plans live, what every plan must carry
- `docs-hub/.cursor/rules/040-plan-lifecycle.mdc` — strikethrough → `✅_` → archive
- `docs-hub/projects/CONVENTIONS.md` — **only if** this sweep touches `diagrams/`
- The target project's `docs/archive/README.md`, its `docs/overview.md`, and any
  `docs/development/<Folder>/README.md` that still exists

If a rule in those files contradicts anything below, **the hub's files win** — and tell me which
line disagreed, so the command can be corrected.

## Step 3 — Inventory

Enumerate the tree:

- `docs/development/` (loose docs first, then any subfolder) — every `.md`, its `**Status:**` line (that, not the filename, is
  what the sidebar badges read — `api/_lib/doc-state.js`), any legacy `__`/`✅_` prefix, its
  mtime, and its last commit (`git log -1 --format='%ad %s' --date=short -- <path>`)
- `docs/archive/` — what is already parked there
- Any markdown loose at `docs/` root that looks like a plan (it should be in a section)

## Step 4 — Verify each open plan against the repo

This is the actual work; everything else is bookkeeping. For each plan:

1. **Read it.** Note its Target-repo table (checkout path, branch/SHA, port) and its done-gate.
2. **Go look at that repo.** Not the doc — the repo. Use its Target-repo table to pick the right
   checkout; if the plan targets a machine-local file with no git (e.g. `~/.openclaw/`), say so
   rather than pretending a PR exists.
3. For each step / todo line, decide **landed · open · deferred · unverifiable**, with evidence:
   - a merged PR (number + base branch), or
   - a commit touching the named files, or
   - the code/file/config existing in its stated form (`rg`, `sed -n`, `git show`)
4. Apply per `040-plan-lifecycle.mdc`:
   - landed → `~~step~~` (checkbox form: `- [x] ~~step~~`)
   - deferred/skipped → plain text starting `Deferred:` — **never** struck
   - open → untouched
   - unverifiable → untouched, and it goes in your report
5. **Refresh the plan's Status paragraph** at the top so it opens with what is closed and what is
   still open — in the house voice: specific, bolded verdict, named residue.
   (`**Still open: trustedProxies only.** Deliberately — …`)
6. **Trim finished work so it stops reading as pending.** Per the Financials README convention:
   a doc's live surface is its open items. History belongs in `git log -p`, not in a checklist
   that scans as a todo list.
7. Owner-only leftovers ("confirm this in the bank", "click X in the bank's UI") do **not** keep a
   doc alive in Development. Strike them answered, or write them as deferred, then archive.

## Step 5 — Archive, delete, or leave

Sort every doc into exactly one bucket, then **show me the table and wait**:

| Bucket | Test | Action |
|---|---|---|
| **Archive** | Whole plan implemented **and** its done-gate confirmed merged | `foo.md` → `✅_foo.md`, `git mv` into `projects/<project>/docs/archive/` |
| **Delete** | Superseded, duplicated, or dangling — describes a design that was abandoned or replaced | `git rm`. Do **not** archive it; archive is for finished work, not dead work |
| **Keep** | Anything with an open item | Stays in `development/` |
| **Rename** | Filename does not say what the doc accomplishes, still carries a legacy `__` prefix or a date, or a `✅_` is sitting in Development | Rename to `<what-it-accomplishes>.md` (no prefix, no date) / move the `✅_` to archive |

Acme is the exception: its tickets archive to `projects/app/docs/__MVP2/z_Archived/`.

## Step 6 — Flatten unearned folders, then fix the READMEs that survive

**Development is flat by default** (`AGENTS.md` §2). A subfolder is earned only when one topic is
past roughly five docs that genuinely read as one workstream — acme's `__MVP2/` qualifies; a
folder holding one or two docs does not.

This is not cosmetic. The lane is sorted by how much each doc still demands of you (`sortByDemand`,
`sidebar-sections.ts`): `proposal` 0, `active` 1, **folder 2**, shipped-with-leftovers 2.5,
`shipped` 3, `reference` 5. A folder has no status of its own, so it **hides its docs' badges from
the sort** — an untouched proposal inside one sinks below a loose doc that shipped weeks ago.

So: propose flattening any folder under the threshold (`git mv` the docs up, delete the folder
README), and say what the README said that is worth keeping. Routing rules — *"measured geometry
lives in the app repo, not here"* — move to the project's `docs/overview.md`, which is Reference and
is where a reader looks for them anyway. Folder moves are `git mv`; **ask first**, like archiving.

For a folder that IS earned, create or repair its `README.md` to the house shape:

1. **A one-or-two-line statement of the folder's subject** — what it is *about*, ideally
   naming the split that made it exist.
2. **The doc table**, one row per doc in the folder, links relative:

   ```markdown
   | Doc | What it is | State |
   |---|---|---|
   | [single-scroll-catalog.md](single-scroll-catalog.md) | One line — what it proposes | **Active.** Phases 1–3 shipped; 4 open |
   | [✅_bar.md](✅_bar.md) | The 2026-08-04 defect audit | **Closed.** Ledger of what was fixed where |
   ```

   The **State** column is the point of the table — it is where a reader learns whether to act on
   a doc. Make it specific ("**Active — prototype in the museum.** Later tweaks uncommitted"),
   never just "In progress".
3. **`## What belongs here`** and **`## What does not`** — the second half is load-bearing, and
   it should *point somewhere* (`→ ../../archive/`, `→ the app repo's own docs/`), not just refuse.
4. Add a `## Convention` block only where the section has a local rule the hub-wide one doesn't cover.

Then reconcile: **every doc in the folder appears in the table, every table row points at a file
that exists.** Rows for docs you archived this run either drop out or move to a line noting the
archive — your call per section, but no dead links.

## Step 7 — Cross-link and structural checks

- **Broken relative links.** Resolve every `](...)` in the docs you touched. Archiving a doc breaks
  every sibling section that linked to it under its old path — that is the single most common
  rot in this hub, so check it explicitly rather than assuming.
- **Missing Target-repo table.** Every plan carries one (checkout path, branch/SHA, port) — even
  when the answer is "no repo, this is machine-local config". Flag plans without one; offer to add it
  from what you verified in Step 4.
- **VERIFIED vs CONCLUDED.** Flag any plan that reads as uniformly confident with no "what was
  actually verified" evidence — quoted command output, not assertion. Don't fabricate the evidence;
  flag it so I know that plan can't be audited.
- **Stale dirty-tree claims.** A handoff doc that lists "4 modified files" when `git status` shows 9
  is actively misleading. Re-derive those tables from live `git status` output.
- **Wrong-place docs.** A plan sitting at `docs/` root, or filed in a section whose README says it
  doesn't belong there → propose the move.
- If the sweep touched `diagrams/`, run the pre-draw checklist in `projects/CONVENTIONS.md`.

## Step 8 — Report, then commit

Print one table:

| Doc | Verdict | Evidence | Action taken |
|---|---|---|---|

Then, separately and plainly:

- **Unverifiable** — steps you could not confirm either way, and what would settle each
- **Needs me** — owner-only actions blocking an archive
- **Left alone** — anything you judged too ambiguous to touch, and why

Finally: stage the explicit paths you touched in the hub and commit with a message naming the
project and the sweep (`docs(design-styles): sweep development/ — archive 2, refresh 4 READMEs`).
Push only if I ask. If the hub was dirty from another agent when you started, say so and stage
**only** your own paths.

**A sweep that changes nothing is a valid result.** Say "already accurate" and stop — do not
manufacture edits to look productive.
