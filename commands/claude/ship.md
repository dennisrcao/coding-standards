---
description: Take a behavior from wherever it is now, through review and staging, all the way to production — and prove both sides landed.
argument-hint: [PR# | branch | "description of the behavior"] [--staging-only] [--dry-run]
---

# /ship

app-monorepo has four deploy surfaces with four different promotion mechanisms, and
only two of them are automatic — on the staging side only. The default outcome of any
merge is therefore **more staging/production drift**, and nothing in the process records
what got left behind. This command exists to make that impossible: it drives one behavior
all the way to both environments and emits a receipt proving where every surface landed.

`$ARGUMENTS`

---

## HARD RULES

**No permission prompts. Real brakes.** The operator has explicitly chosen unattended
promotion, so do NOT stop to ask "shall I continue?". But ABORT the run — loudly, with
the reason and the exact recovery command — on any of these:

| Abort trigger | Why |
|---|---|
| `pnpm validate` or affected tests fail | never ship red |
| api-server touched and its **Docker image build** fails | direct imports pass CI, then `pnpm deploy --prod` prunes them and kills ECS |
| an unresolved CONFIRMED `/code-review` finding | review must converge, not be outrun |
| any CI check red on the PR | — |
| a surface the table PREDICTED produced no workflow run | the classification is wrong; everything downstream is untrustworthy |
| **staging verification fails** | leaves staging shipped, production untouched — the safe direction of asymmetry |
| production task-def revision changed since preflight | someone else is mid-deploy |
| the SAM account guard trips | `require_lambda_deploy_account` is protecting you from account 051 |
| production verification fails | stop and report; do NOT auto-roll-back, a human decides |

Abort means: stop, print what already landed, print the surface table with the reached
state of each row, and print the exact next command. Never leave the operator guessing
which half of the pipeline completed.

**Never merge or push to `production` outside this command's own phase 9.**
**Never re-template production env/secrets.** Phase 10 swaps an image and nothing else.

---

## Phase 0 — Detect the input

Auto-detect from `$ARGUMENTS` and the repo state. Do not guess; run the checks.

```
arg is all digits             → PR number. gh pr view <n>; gh pr checkout <n>
arg names a local/remote branch → git checkout that branch
working tree is dirty         → the uncommitted diff IS the change;
                                arg (if any) is the behavior description
clean tree + a bare sentence  → build it: reproduce on staging first (phase 8 protocol),
                                then write the fix, then continue
```

Ambiguity (dirty tree AND the arg is a PR number) is the one case you must resolve with
the operator before doing anything.

Record the **behavior statement** — one sentence, checkable in a browser, e.g. "campaign
cards show the real image and product counts, not inflated ones". Phases 8 and 12 both
test exactly this sentence. If you cannot phrase it as something observable in a browser,
say so and ask for one before proceeding.

## Phase 1 — Classify surfaces (the spine)

Diff against `origin/staging`. Map every changed path through the **actual workflow path
filters**, not intuition:

| Surface | Paths | → staging | → production |
|---|---|---|---|
| **FRONTEND** | `apps/studio/**`, `clients/**`, `libs/data-access-am/**`, `libs/studio-types/**`, `libs/shared-types/**`, `pnpm-lock.yaml`, `.github/workflows/deploy-frontend.yml` | auto on push to `staging` | auto on push to `production` |
| **API-SERVER** | `apps/api-server/**`, `libs/auth-core/**`, `pnpm-lock.yaml`, `.github/workflows/build-and-push-api-server-staging.yml` | auto on push to `staging` | **MANUAL** (phase 10) |
| **LAMBDAS** | `apps/py-lambdas/**`, `apps/node-lambdas/**`, `infra/sam/**`, `layers/**` | **MANUAL** (phase 7) | **MANUAL** (phase 11) |
| **MIGRATIONS** | `apps/api-server/**/migrations/**` | rides the AM deploy | rides the AM deploy |

Two traps to state explicitly in the printed table when they apply:

- **`pnpm-lock.yaml` fires BOTH** frontend and api-server.
- **Path filters match on path, not on build impact.** `apps/studio/AGENTS.md` or
  `apps/studio/.env.example` triggers a full frontend deploy exactly like a `.tsx` file.
  A docs-only change under `apps/studio/` is NOT deploy-inert.

FRONTEND always means **three hosts per environment** (core + client + admin) — a single
push fans out to all of them. Say so in the table; it is the blast radius.

Print the surface table now. It is the contract every later phase is checked against.

## Phase 2 — Local gate

```bash
pnpm validate          # studio: lint then typecheck — what CI gates on
pnpm test              # affected
```

**If API-SERVER is in the table, build the Docker image locally before going further.**
This is not optional and CI will not catch it for you: a direct import in AM's `main.ts`
type-checks and tests clean, then `pnpm deploy --prod` prunes the dependency and the ECS
task crash-loops on boot. Build the image, and only proceed if it builds.

If MIGRATIONS is in the table, list the migration filenames by name — they will run
against the production database in phase 10 and belong in the receipt.

## Phase 3 — PR

Branch if needed (`claude/<slug>`), commit, push, open the PR. Body follows the house
style: ticket link if there is one, then a **before/after behavior table** — what the
user saw, what the user now sees. Paste the phase-1 surface table into the PR body too,
so the reviewer sees the blast radius without deriving it.

Tickets live in org Project #32 (your-org), not per-repo Issues.

## Phase 4 — Review

Run `/code-review high` on the PR.

Every finding must end resolved: either fixed with a commit, or dismissed with a stated
reason posted as a PR comment. An unresolved CONFIRMED finding aborts the run. Do not
argue a finding away silently — if you disagree, say why in the comment and move on.

## Phase 5 — CI

Wait for all checks. Red aborts.

## Phase 6 — Merge to `staging`

Squash-merge. Then **verify the prediction**: watch for the workflow runs the phase-1
table said would fire —

- FRONTEND → `Deploy Frontend to S3` on `staging`
- API-SERVER → `Build & deploy api-server (staging)`

A predicted run that never appears aborts the run: it means the path classification is
wrong, and every later phase is built on it. A run that appears but was NOT predicted is
equally an abort — you under-called the blast radius.

Wait for each to go green before continuing.

## Phase 7 — Staging lambdas (only if LAMBDAS)

Lambdas never auto-deploy on either side. This is precisely where drift is born: a merge
ships the frontend that calls a lambda that was never deployed. Deploy to staging now,
scoped to the stacks actually touched — do not blanket-deploy.

Use `AWS_PROFILE=app-staging` (account `123456789012`; the default profile has no creds).

## Phase 8 — VERIFY ON STAGING  ← the load-bearing phase

Test the **behavior statement** from phase 0 in a real browser, on the staging host that
matches the client the change affects:

| VITE_CLIENT | staging URL |
|---|---|
| core | `https://staging.example.com/studio/` |
| client | `https://client.staging.example.com/` |
| admin | `https://admin.staging.example.com/` |

Follow the **Browser verification protocol** at the bottom of this file — it branches on
which harness you are running in.

Record an explicit **PASS** or **FAIL**, with a screenshot and the concrete observation
that decided it. "The page loaded" is not a pass. "Looks fine" is not a pass. Name the
thing you saw that proves the behavior statement true.

**FAIL aborts the run.** Staging carries the change, production does not, and that is the
correct place to stop. Print the receipt for what landed and stop.

If `--staging-only` was passed, stop here on PASS and emit the receipt with production
rows marked `deliberately held — --staging-only` .

## Phase 9 — Promote to `production`

> A push to `production` is a **live, triple-host production release**. It writes the
> distributions real users hit immediately — not a dark or staged write. `aws s3 sync
> --delete` means there is no bucket-level time-travel; rollback is re-pointing
> `production` at a known-good commit and pushing.

Record the current `production` SHA **before** pushing and print it as the rollback
target. Then fast-forward `staging` into `production` and push. If it will not
fast-forward, abort — a diverged `production` needs a human, not a merge commit.

Watch `Deploy Frontend to S3` on `production` and confirm all three production targets
go green: `production-562`, `client-production`, `admin-production`.

## Phase 10 — Production api-server (only if API-SERVER)

There is **no `task-definition.production.json`** in this repo. Do not invent one and do
not reuse the staging file — that would push staging config into production and create
exactly the drift this command exists to close.

Instead, image-swap the live definition:

1. `describe-services` on the production AM service → current task-def ARN.
   Resolve cluster/service/ECR repo **from what is actually deployed**, never hardcoded.
2. Confirm that revision matches what you recorded at preflight. Changed → abort,
   someone else is mid-deploy.
3. `describe-task-definition` → JSON.
4. Build the AM image (already proven to build in phase 2), push to the production ECR
   repo discovered in step 1.
5. Swap **only** `containerDefinitions[].image`. Strip the read-only fields
   (`taskDefinitionArn`, `revision`, `status`, `requiresAttributes`,
   `compatibilities`, `registeredAt`, `registeredBy`). Change nothing else — env,
   secrets and role stay exactly as production has them.
6. `register-task-definition` → `update-service --force-new-deployment` → wait
   services-stable.
7. Confirm the service settled on the new revision and tasks are RUNNING, not cycling.

MIGRATIONS ride this deploy. Name each migration that just ran against production in the
receipt.

Note: deployed task roles are known to lag the ECS template in this account. If the new
task fails on a permissions error rather than on your code, say so plainly rather than
retrying.

## Phase 11 — Production lambdas (only if LAMBDAS)

```bash
AWS_PROFILE=app-staging bash infra/sam/scripts/lambda-deploy/deploy-production.sh --stack <NAME>
```

One invocation per stack actually touched. The script pins
`STACK_PREFIX=production-app` and `AM_DEPLOY_ACCOUNT_ID=123456789012` itself, and
`require_lambda_deploy_account` will refuse if the active account is wrong. **That guard
is a brake, not an obstacle — never work around it.**

## Phase 12 — VERIFY ON PRODUCTION

Re-run the phase-8 script verbatim against the production host:

| VITE_CLIENT | production URL |
|---|---|
| core | `https://app.example.com/studio/` |
| client | `https://client.example.com/` |
| admin | `https://admin.example.com/` |

Same PASS/FAIL discipline, same evidence bar. On FAIL: stop, print the rollback target
SHA from phase 9 and the exact rollback command, and hand it to the operator. Do **not**
auto-roll-back — a human decides whether a partial state or a revert is worse.

Client production is live tenant traffic. Treat a client FAIL as the most urgent case.

## Phase 13 — Receipt

Emit this table — it is the deliverable, and it replaces hand-writing "where it landed"
into Slack after the fact:

```
BEHAVIOR   <the phase-0 statement>
PR         #<n>          MERGED <sha>
PROMOTE    staging -> production <sha>     rollback target: <previous production sha>

| Surface        | staging          | production       | evidence            |
|----------------|------------------|------------------|---------------------|
| FRONTEND (x3)  | shipped <run>    | shipped <run>    | verify PASS <shot>  |
| API-SERVER  | shipped <run>    | rev <n>          | tasks stable        |
| LAMBDAS        | <stacks>         | <stacks>         | —                   |
| MIGRATIONS     | <names>          | <names>          | ran on deploy       |
| not touched    | —                | —                | —                   |
```

Every row must read shipped-on-both, or carry an explicit recorded reason it did not.
A row you cannot fill in is a finding, not a formatting problem — say which surface you
could not account for. Post the table as a comment on the merged PR, and print it.

---

## Flags

- `--staging-only` — run phases 0–8, stop on PASS, mark production rows deliberately held.
- `--dry-run` — run phases 0–1 only. Print the surface table, the behavior statement, and
  the full list of commands each phase would run. Execute nothing, mutate nothing.

---

## Browser verification protocol (phases 8 and 12)

**Detect your harness by which tools you actually have, not by assumption.**

### If you are Cursor

Use Cursor's **internal browser**. Navigate to the environment URL, sign in if the session
is not already live, drive the UI to the behavior under test, and capture a screenshot as
the evidence artifact. Cursor's browser carries its own profile — the staging and
production sessions are separate logins because auth is origin-scoped.

### If you are Claude Code

Use the **Playwright MCP** browser tools (`mcp__pw-5173__*`, `mcp__pw-5174__*`, or
`mcp__playwright-docs__*` — these servers differ only in browser-profile directory).
Prefer a profile that is not one of the localhost dev profiles, so a deployed-environment
session does not pollute local dev.

Sequence: `browser_navigate` → `browser_snapshot` to read state → interact →
`browser_take_screenshot` for the evidence artifact. Prefer `browser_snapshot` over
screenshots for deciding PASS/FAIL; use the screenshot as the record.

### Both harnesses

- Auth is **origin-scoped localStorage**. Staging and production are different origins and
  each needs its own sign-in. One browser profile can hold both at once.
- A stale session can eject you to the wrong environment's console. If you land somewhere
  unexpected, clear site data for that origin and sign in again — do not report the bounce
  as a verification failure of the change.
- Hard-reload past the CDN before judging a frontend change. A cached bundle showing old
  behavior is not a FAIL; confirm the deployed bundle hash actually changed first.
- If you cannot reach the environment at all — auth wall, network, no browser tool — that
  is **UNVERIFIED**, not PASS. UNVERIFIED at phase 8 aborts the run exactly like FAIL.
