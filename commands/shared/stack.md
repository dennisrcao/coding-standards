---
description: Create or update a GitHub PR stack (app-monorepo and any repo using github-work SSH remotes)
argument-hint: [init | add <branch> | submit | sync | view | status]
allowed-tools: Bash(git:*), Bash(gh:*), Bash(gh-stack-alias:*), Read, Grep, Glob
---

## Context (auto-collected)

- Repo: !`git rev-parse --show-toplevel 2>/dev/null || echo "NOT A REPO"`
- Branch: !`git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "n/a"`
- Origin: !`git remote get-url origin 2>/dev/null || echo "(none)"`
- ghstack remote: !`git remote get-url ghstack 2>/dev/null || echo "(not set — wrapper will add on submit)"`
- Stack view: !`gh stack view 2>/dev/null | head -20 || echo "(no stack in this checkout)"`
- Open PR on this branch: !`gh pr view --json number,title,url 2>/dev/null || echo "(none)"`

`$ARGUMENTS`

---

# /stack

Drive **`gh stack`** for a multi-PR change. Use this when the hub plan says "ship as a PR stack"
instead of one megacommit. For a **single** PR, use `/close-out` instead.

## HARD RULES

- **Never run bare `gh stack submit`.** On this machine, `origin` is usually
  `git@github-work:your-org/…`. `gh stack` cannot read that host alias. Always go through
  **`gh-stack-alias`** (see below).
- **Trunk on app-monorepo is `staging`**, not `main`.
- **One stack per checkout.** Do not start a second stack in the same app-monorepo-N worktree
  without finishing or abandoning the first.
- **PR titles for Acme stacks:** `[STACK <theme> i/n] <conventional subject>` — e.g.
  `[STACK hygiene 3/12] docs(agents): …`. Pick one theme for the whole stack; `n` is total PR count.
- **Do not merge stack PRs out of order.** Merge bottom-up (trunk → layer 1 → layer 2 → …) or let
  GitHub's stack UI guide you.

## Wrapper (always use this)

```bash
# On PATH after: ln -sf ~/coding-standards/scripts/gh-stack-alias.sh ~/.local/bin/gh-stack-alias
gh-stack-alias <subcommand> [args]
```

It ensures an `ghstack` HTTPS remote exists and passes `--remote ghstack` to `submit` / `sync` /
`push`. Plain `git push` stays on `origin` (`github-work` SSH).

## Workflow

### 1. Start a new stack

```bash
git fetch origin staging
git checkout -b chore/my-theme-layer-1 origin/staging
# … edit, commit …
gh-stack-alias init --trunk staging
```

Or turn existing branches into a stack:

```bash
gh-stack-alias init branch-1 branch-2 branch-3 --trunk staging
```

### 2. Add the next layer

On the tip branch, after committing layer N:

```bash
git checkout -b chore/my-theme-layer-2
# … edit, commit …
gh-stack-alias add chore/my-theme-layer-2
```

Repeat until the plan's layers are done.

### 3. Push and open / update PRs on GitHub

```bash
gh-stack-alias submit
```

`submit` defaults to **`--auto`** (draft PRs, auto titles). Pass `--open` when ready for review:

```bash
gh-stack-alias submit --open
```

### 4. Day-to-day

| Need | Command |
|---|---|
| See the chain | `gh stack view` |
| Pull remote stack state | `gh-stack-alias sync` |
| Jump to a layer | `gh stack checkout <branch-or-pr>` |

## When to use stack vs `/close-out`

| Situation | Use |
|---|---|
| Hub plan lists H0, H1, H2… or "PR stack" | `/stack` |
| One bugfix, one feature, one doc | `/close-out` |
| Stack layer ready to merge | Merge that PR (bottom-up); do not `/close-out` the whole stack at once |

## app-monorepo checkout discipline

Match the hub plan's **Target repo** table: one `app-monorepo-N` per stack, correct Vite port.
Name branches `issue-<theme>-<layer>` or `chore/<theme>-<layer>` so `gh stack view` stays readable.

### Stack layers by deploy surface (required on app-monorepo)

**Do not ship one megacommit on the stack tip** that mixes api-server, Studio, and
py-lambdas when the plan needs staging QA on a preview URL. Previews deploy **frontend only**;
they always call **staging api-server** (`VITE_AM_API_BASE` → staging `/api/v1`). There is
no preview AM. Until the AM layer merges to `staging`, the top preview cannot exercise new
backend routes or migrations.

Split the stack **by what deploys when merged to `staging`**, not only by plan phase number:

| Layer kind | Typical paths | Merge to `staging` unlocks |
|---|---|---|
| **AM / backend** | `apps/api-server/**`, migrations, `libs/shared-types` (codegen), compose slices in `libs/agent-contracts` that AM imports | Migrations run, new APIs live on staging AM |
| **Studio / frontend** | `apps/studio/**`, `libs/data-access-am/**`, `libs/studio-types/**`, admin UI | Top-of-stack **preview URL** (`client.staging.example.com/preview/<branch-slug>/`) |
| **Py-lambdas / agents** | `apps/py-lambdas/**`, agent registry entries for new lambdas | Agent deploy workflow (separate from AM + FE) |

**Default order (bottom → top):** prior stack layers → **AM layer** → **Studio layer** →
(optional) **agents layer**. Name branches so the suffix shows the surface, e.g.
`issue-brand-kit-phase-3-am` then `issue-brand-kit-phase-3` (studio).

**Plan PR-stack table** — list every layer with branch, deploy surface, and QA gate:

```markdown
| Layer | Branch | Deploy surface | QA on preview after merge to staging |
|---|---|---|---|
| 3 | `issue-…-phase-2` | none (tooling/docs) | n/a |
| 4 | `issue-…-phase-3-am` | AM + migrations | staging AM has API; preview still old UI until layer 5 |
| 5 | `issue-…-phase-3` | Studio (preview tip) | full E2E on preview URL |
| 6 | `issue-…-agents` | py-lambdas | agent jobs pick up kit slices |
```

**Coworker QA link** — put the **top Studio layer** preview in the plan and PR body:

`https://client.staging.example.com/preview/<branch-slug>/`

**Merge for backend QA:** merge only the **AM layer** to `staging` first (bottom-up). That
deploys AM + runs migrations; the existing preview URL on the tip branch then talks to real
kit APIs. Do not wait for the whole stack to merge before unblocking backend QA.

**Implementing a split after a megacommit landed:**

```bash
git checkout <parent-layer>
git checkout -b issue-<theme>-<n>-am
git checkout <megacommit> -- apps/api-server/ libs/shared-types/ …  # AM paths only
# commit, push, gh stack add issue-<theme>-<n>-am
git checkout -b issue-<theme>-<n> issue-<theme>-<n>-am
git checkout <megacommit> -- apps/studio/ apps/py-lambdas/ …  # remaining paths
# commit, push, gh stack add issue-<theme>-<n>
gh-stack-alias submit --open
```

Reference: `apps/docs/content/projects/app/docs/technical/deployed-environments.md` (PR
previews + staging AM).

## If submit fails

| Error | Fix |
|---|---|
| `none of the git remotes … point to a known GitHub host` | You used bare `gh stack submit`. Use `gh-stack-alias submit`. |
| `ghstack` missing | Wrapper adds it on first run; or `git remote add ghstack https://github.com/<org>/<repo>.git` |
| PRs exist but no stack on GitHub | `gh-stack-alias submit` links existing PRs into a stack |

## What to do now

Parse `$ARGUMENTS` as the subcommand (`init`, `add`, `submit`, `sync`, `view`, or empty → `view`).

1. Confirm you are in the intended repo and on the right branch.
2. Run the matching **`gh-stack-alias`** command (never bare `gh stack submit`).
3. Print `gh stack view` after `init`, `add`, or `submit`.
4. If the hub plan has a stack section, report which layer just landed and what is next.
