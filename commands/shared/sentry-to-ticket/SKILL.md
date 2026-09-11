---
name: sentry-to-ticket
description: "Investigate a Sentry issue (URL or short ID) and file an implementable fix ticket on the tracker — without fixing anything in this session. Use when the user shares a Sentry issue and wants it triaged into a ticket rather than fixed on the spot."
---

# Sentry → Ticket

Turn a Sentry issue into an investigated, implementable **fix ticket**. This
session investigates and files the ticket — it does **not** fix. The fix runs
through `/implement` in a fresh session, so every implementation rule (branch
naming, TDD seams, code review, handoff comment) applies to Sentry fixes too.

Tracker conventions live in
`apps/docs/content/projects/app/docs/technical/agents/issue-tracker.md`.

## 1. Pull the Sentry side

Fetch the issue with the Sentry MCP tools (`get_sentry_resource` on the URL or
short ID; load schemas via ToolSearch). Collect: message, culprit/transaction,
level, environment, release SHA, first/last seen, event and user counts, and
the tags. Widen once — `search_issues`/`search_events` for sibling issues (same
message family, other environments) and the event's trace: volume and spread
drive severity, and siblings often share one root cause and one ticket.

## 2. Investigate in the repo

Find the emitting code (grep the message / culprit), then establish, with
file:line evidence:

- **Root cause** — the code path and the conditions that fire it, and every
  caller/writer involved (races and duplicates have at least two).
- **Blast radius** — what is actually lost, corrupted, or user-visible, versus
  an alarm firing as designed. Read the area's ADRs and per-app agent notes
  before judging design intent.
- **Age** — `git log`/blame against the event's release SHA: a new defect, or
  old behavior newly made visible?

## 3. Verdict to the user

Report criticality, root cause, and the recommended response **before**
touching the tracker. Not every issue earns a fix ticket — noise-by-design may
instead need grouping/severity tuning or a Sentry ignore rule; ask when
unclear. A critical user-facing defect is also worth saying out loud here: the
user may want a hotfix path instead of the ticket queue.

## 4. File the fix ticket

One standalone GitHub issue (no parent spec), labelled `ready-for-agent`,
titled `[Sentry] <SHORT-ID> — <plain-language summary>` (e.g.
`[Sentry] NODE-BACKEND-2 — duplicate terminal "failed" write`). Body:

<issue-template>

## Sentry

Link, short ID, level, environment, release SHA, first seen, events/users.

## What happens

The failure in user/domain terms — what breaks, for whom.

## Root cause

The mechanism, with the file:line evidence from step 2. (Unlike spec tickets,
precise pointers belong here — these tickets are implemented promptly, and the
Sentry link stays the ground truth.)

## Fix direction

The smallest change that removes the cause, and the suggested regression-test
seam. Direction, not a patch — `/implement` decides the code.

## Acceptance criteria

- [ ] Criterion 1 (include the regression test where a seam exists)
- [ ] Commit message includes `Fixes <SHORT-ID>` — Sentry auto-resolves the
      issue when that commit merges.

## Production verification

How the verifier confirms on staging — including that the Sentry issue stops
receiving events after the deploy.

</issue-template>

## 5. Hand off

No code changes in this session. Point the user at `/implement` (fresh session)
with the ticket number. If the root cause could not be pinned down, say so in
the ticket: record the facts, the ruled-out paths, and the feedback loop to
build — the implementing session then starts with `/diagnosing-bugs` instead of
a guessed cause.
