---
name: implement
description: "Implement a piece of work based on a spec or set of tickets."
disable-model-invocation: true
---

Implement the work described by the user in the spec or tickets.

Tracker conventions (branch naming, labels, handoff comment) live in
`apps/docs/content/projects/app/docs/technical/agents/issue-tracker.md`.

**First action — claim the ticket**: swap its status label
`ready-for-agent → in-progress` (see the tracker doc) so no parallel session
grabs it. If the ticket is already `in-progress`, stop and check with the
user — another session may be working on it.

Before the first commit, put the work on a **ticket-named branch**:
`issue-<N>-<short-slug>`. If the session started on an auto-generated branch
(`claude/…`), rename it — see the tracker doc.

Use /tdd where possible, at pre-agreed seams (per-app seams are in the root
`CLAUDE.md`; read the app's own `AGENTS.md`/`CLAUDE.md` before touching it).

**Code comments** follow the repo-wide rule in
`.cursor/rules/005-code-comments.mdc` (in the target repo)
(imported by the root `CLAUDE.md`): one or two lines, addressed to the next
reader of the code, never a narration of the change — that story is the commit
message and the PR description.

**Error/warning text — keep variable parts out of the message.** Sentry groups
events by message text, so an interpolated id/URL/value splinters one problem
into a separate issue per occurrence. The message states the invariant; ids and
values go into `tags`/context (log lines may keep them), and an explicit
`fingerprint` pins grouping when it must follow specific fields.

Run typechecking regularly, single test files regularly, and the full test suite
for the affected app once at the end.

Once done, use /code-review to review the work.

Commit your work to the current branch and open a **draft PR to `staging`**
linking the ticket with `Closes #<N>`. Draft is deliberate: the PR appears only
after the work is done and code-reviewed, and it stays draft so teammates don't
start reviewing changes the ticket's author hasn't verified yet — marking it
ready for review (and merging) is the author's move, after verification passes.
Never push to `staging` or `production` directly.

When the work is committed and the review is clean, move the ticket to
**`in-review`** instead of closing it: swap `in-progress → in-review` on the
issue (see the tracker doc). Keep the issue open — the ticket's author closes it
once human verification (eye-check on the staging host, smoke test) passes.

In the same step, post the **handoff comment** on the issue: branch, PR, commit,
and a paste-ready block of commands that reproduces the ticket's *Production
Verification* locally (template in the tracker doc). A ticket flipped to
`in-review` without that comment is not done — the verifier has no way to check
it out.
