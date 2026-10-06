```yaml
description: Roster of the personal machine-global slash commands — what each is for, which agents get it, how to write one, and the full source of the ones worth copying
globs:
alwaysApply: false
```

# Slash commands (personal, machine-global)

> **Reference only — operator / machine-local.** Tracked in this hub for restore-after-wipe; not copied
> to target repos as adoptable `.mdc` rules.

These are **not** repo commands. They are reachable from `~/.claude/commands/*.md` on each machine,
so they are available in **every** repo — that is the whole point of them.

**They are tracked here.** The real files live in `commands/`, split by
which agent gets them — `shared/` (both), `claude/` (Claude Code only), `cursor/` (Cursor only).
`~/.claude/commands/` is symlinks into those folders, so a wiped machine is restored by cloning
`docs-hub` to the Desktop and running `bash scripts/link-slash-commands.sh`.
Writing a command *is* committing it; there is no separate backup step.

A file named `foo.md` in that folder becomes `/foo`. Claude Code also surfaces it in the skills
list, so it can fire on intent, not just on the typed slash.

**Most of these are shared with Cursor** — `/close-out`, `/ship`, `/pr-description` and `/pr-shots` are
literally one file symlinked into both agents, so they cannot drift. Only
`/ask` is deliberately two files, because each side has to name the *other* agent's binary. See
[091-slash-commands-claude-vs-cursor.md](091-slash-commands-claude-vs-cursor.md) for the two-agent
view, what Cursor ignores in a shared file, and the bar a command has to clear to be shareable.

## Do

- **Keep them repo-agnostic.** A global command resolves the repo it was run in from `pwd` /
  `git rev-parse --show-toplevel` — it never hardcodes one project. Anything project-specific
  belongs in that repo's `.claude/commands/`.
- **Auto-collect context in the frontmatter.** The ``!`command`` lines run *before* the model
  reads the prompt, so it starts with live `git status` / `gh pr list` output instead of asking.
- **Constrain `allowed-tools`.** A command that can only run `git`, `ls`, and `Read` cannot
  surprise you.
- **Write the failure the command exists to prevent.** Every one of these opens with it. That
  paragraph does more work than the step list — it tells the model what "done badly" looks like.
- **Write it in `commands/shared/` and symlink it**, so it is committed the moment it exists and
  both agents get it. Drop to `commands/claude/` only when the command genuinely cannot work in
  Cursor. Then `python3 scripts/build-slash-command-doc.py` refreshes
  `091`'s copies.
- **Resolve, don't assume — the base branch especially.** `git symbolic-ref refs/remotes/origin/HEAD`
  gives `staging` on app-monorepo and `main` nearly everywhere else. A command that hardcodes one is
  a Acme command wearing a global name.
- **Machine-global skills are optional; Acme still vendors for the team.** Coworkers on a
  single-repo checkout use `app-monorepo/.claude/skills/`. The hub copy in
  `commands/shared/<name>/` is for `link-slash-commands.sh` (multi-root workspace on one
  machine). A global command may invoke `code-review` from either path.

## Don't

- **Don't let a command claim completion it did not verify.** The recurring failure across all of
  them is a tidy summary sitting on top of unpushed work. Every command that reports state carries
  a HARD RULES block saying so.
- **Don't make destructive steps automatic.** Archive, delete, `git mv`, push — propose the list,
  wait for a yes.
- **Don't let a merge fire a deploy silently.** Merging is not automatically safe just because the
  operator typed the command: on app-monorepo a push to `staging` publishes to three staging hosts.
  A command that merges must check `.github/workflows/*.yml` for a `push:` trigger on the target
  branch and stop for a yes when it finds one. `/close-out` does this at step 8.

## The roster

| Command | Agents | What it is for |
|---|---|---|
| `/close-out` | both | I've signed off — **land it.** Commit, PR, **thorough review** (repo `/code-review` skill or Bugbot when present; `skip review` opts out), CI, merge to the repo's base branch, then leave the checkout on that branch instead of stranded on the feature branch. Stops for a yes when merging fires a deploy. Closes out the `docs-hub` ticket that drove the work — strike, then archive or mark deferred. |
| `/stack` | both | Multi-PR **GitHub stack** on app-monorepo (or any repo whose `origin` is a `github-work` SSH alias). Drives **`gh-stack-alias`** — never bare `gh stack submit`. Use when the hub plan lists H0…Hn or "PR stack"; `/close-out` still lands one layer at a time. |
| `/ship` | both | Take a behavior from wherever it is now through review and staging to **production**, and prove both sides landed. |
| `/pr-description` | both | Ticket link + a before/after behavior table. Nothing else. |
| `/pr-shots` | both | Before/after **screenshots** in the PR body — shoots each changed surface on the base deploy and on the PR preview, hosts the images, rewrites the body outcome-first (one `## N ·` section per thing that is now true, Base / This PR under each, captions below the images). The only command that edits a PR. |
| `/ask` | both, two files | Ask the *other* agent to critique this without opening its window — then verify every claim before adopting it. |
| `/argue` | both | Bounded **driver ↔ tmux tester** plan debate on Fabric (`plan-critique` / `plan-revise` → `plan-review` → verify → `plan-agree`). Ledger at `<plan>.argue.md`. Not `/debate` (headless CLI). |
| `/docs-update` | Claude | Sweep a project's `docs-hub` `docs/development/` — verify each plan against the real repo, strike what landed, archive what's done, refresh section READMEs. **Full source below.** |
| `/update-markdown` | Claude | Cross off what we actually implemented in the plan markdown we've been following; mark finished sections `✅`. |
| `/explain` | Claude | I'm confused — explain it as a two-column table: how it behaves today vs. how it would behave if we built it. Explanation only, never edits. |

`/close-out` and `/ship` are the two halves of promotion, and they are deliberately separate:
`/close-out` goes to the **base branch** (`staging` on app-monorepo, `main` elsewhere), `/ship`
goes to **production**. Neither one can be talked into doing the other's job.

`/ask` gets the critique **and then refuses to trust it** — its Step 4 breaks the critique into
atomic falsifiable claims, verdicts each against the real code with `file:line` evidence, and edits
the plan only for what survived. That verification was its own command, `/CROSSCHECK`, until
2026-09-02; it is now inlined in both halves of `/ask`, because an LLM critique reads as
authoritative and is frequently wrong about the codebase — see
[`050-anti-slop.md`](../../../docs/tooling/050-anti-slop.md).

## `/argue` vs `/ask` vs `/debate`

| | `/argue` | `/ask` | `/debate` |
|---|---|---|---|
| Opponent | tmux **testers** on a mesh (Fabric) | headless **other agent** CLI | headless `claude -p`, up to 3 rounds |
| Loop | up to 3 `plan-critique` / `plan-revise` rounds | one volley | up to 3 CLI rounds |
| Ledger | `<plan>.argue.md` | none | `<plan>.debate.md` |
| When | driver mesh is up; plan before implement | cold second opinion, any repo | argue without testers |

Shipped 2026-09-10. Engine: `commands/shared/argue-protocol.md` (not symlinked). Command:
`commands/shared/argue.md` (both agents). `/ask` is **not** replaced — it stays the one-volley
headless critique with inline verification.

## Global skills (machine-wide, not slash commands)

These live under `commands/shared/<name>/SKILL.md`. Run `link-slash-commands.sh` to symlink them into
`~/.cursor/skills/` and `~/.claude/skills/` — **one copy per machine**, so a multi-root workspace
does not register eleven skills per Acme checkout. **app-monorepo still ships the same skills in
`.claude/skills/`** for coworkers who open one repo and never run the link script; keep the two
copies in sync when you edit a skill (hub first, then copy or cherry-pick into Acme).

| Skill | What it is for |
|---|---|
| `grill-with-docs` | Interview to sharpen a plan; updates `CONTEXT.md` and ADRs inline |
| `grilling` | Interview primitive behind `grill-with-docs` |
| `domain-modeling` | Glossary (`CONTEXT.md`) and lazy ADRs |
| `to-spec` | Synthesize conversation into a parent GitHub spec issue (Acme) or hub plan |
| `to-tickets` | Break a spec into tracer-bullet GitHub issues |
| `implement` | Branch `issue-<N>-<slug>`, `/tdd`, `/code-review`, PR to base branch |
| `tdd` | Red-green at pre-agreed seams |
| `code-review` | Standards (`AGENTS.md`) + spec fidelity |
| `diagnosing-bugs` | Disciplined bug loop with a feedback loop first |
| `handoff` | Compact session into a handoff doc |
| `sentry-to-ticket` | Sentry URL → implementable fix ticket |
| `app-staging-data` | Staging RDS / campaign wipes (Acme account) |
| `app-staging-lambda-deploy` | Staging lambda deploy helpers |

**Provenance:** adapted from [mattpocock/skills](https://github.com/mattpocock/skills), first
ported into app-monorepo in #403 (Artem Vozniuk). Hub copy is the machine-global install path;
Acme `.claude/skills/` remains the default for single-repo checkout. After hub edits, mirror
into Acme before merging agent workflow changes there.

Walkthrough of the chain (Acme docs hub): `app-monorepo` →
`apps/docs/content/projects/app/docs/technical/agents/spec-driven-workflow.md`.

## Where the house rules they enforce actually live

`/docs-update` deliberately re-reads its rules at runtime rather than embedding them, because they
change:

| Rule | File |
|---|---|
| Where plans live, what every plan carries | `docs-hub/AGENTS.md` |
| Strikethrough → `✅_` → archive | `docs-hub/.cursor/rules/040-plan-lifecycle.mdc` |
| Diagram authoring | `docs-hub/projects/CONVENTIONS.md` |
| Per-section scope | each `docs/development/<Section>/README.md` |

If a command and those files disagree, **the files win** — and the command is what gets corrected.

---

## `/docs-update` — full source

Install: save as `~/.claude/commands/docs-update.md`.

````markdown
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
6. **Trim finished work so it stops reading as pending.** A doc's live surface is its open items.
   History belongs in `git log -p`, not in a checklist that scans as a todo list.
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

This is not cosmetic. The lane is sorted by **name** (`sortByName`, `sidebar-sections.ts`) — folders
and files intermixed, so the `__` prefix pins a doc to the top. A folder therefore **hides its docs'
badges behind a collapsed row**: an untouched proposal inside one is invisible until you expand it,
while a loose doc advertises its state on sight. Status badges are per-row only and never reorder
the list (`AGENTS.md` §2).

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
````
