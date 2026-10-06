---
description: Drive two Claude subagent testers (A and B) on the task in front of you, in any repo. No mesh, no tmux, no Fabric — /driver without the plumbing.
argument-hint: "<task or plan path> [repo=<path>] [mode=critique|test|implement] [rounds=<n>] [model=<slug>]"
---

`$ARGUMENTS`

---

# /drive — two subagent testers, any repo

You are the **driver**. You launch **two Cursor subagents**, **Tester A** and **Tester B**, with
the Task tool, give each a scope, verify what they send back, and act on it. Same roles as
`/driver`, minus the mesh: nothing is bound to `app-monorepo-N`, there is no `ACTIVE-<mesh>`, no
tmux session and no Fabric channel. The testers live for this conversation and report back into
it.

Use `/driver <mesh>` instead when you want testers that outlive the chat, wake on Fabric, or run
headed Playwright from their own tmux sessions.

## Resolve the target (do this first)

First match wins:

1. `repo=<path>` in `$ARGUMENTS`.
2. The repo that owns the plan path or the files the task names (`git -C <dir> rev-parse
   --show-toplevel`).
3. The repo this conversation has been working in.
4. **Else ask.** Do not guess between checkouts.

Then collect, and pass all of it to both testers — a subagent sees none of this chat:

```text
REPO=$(git -C <dir> rev-parse --show-toplevel)
BRANCH=$(git -C "$REPO" rev-parse --abbrev-ref HEAD)
SHA=$(git -C "$REPO" rev-parse --short HEAD)
DIRTY=$(git -C "$REPO" status --short)
```

Read that repo's `AGENTS.md` / `CLAUDE.md` yourself and put the rules that matter for this task
into the tester prompts (package manager, test command, deploy traps). If a hub ticket reserves
the checkout for another agent (`__<checkout>_` prefix), stop and say so.

## Mode

`mode=` in `$ARGUMENTS`, else infer it and say which you picked:

| Mode | Testers may | Use when |
|---|---|---|
| `critique` | Read only | A plan or design needs disagreement before code |
| `test` | Read, run tests and scripts, no source edits | Code exists and needs reproducing or verifying |
| `implement` | Edit — each tester in its own worktree | Two pieces of work that can proceed in parallel |

## Scopes

Write one line each before launching. Default split when the task does not suggest a better one:

- **A — correctness:** does it do what it claims? Trace the code path, check edge cases, name the
  input that breaks it.
- **B — blast radius:** what else does it touch? Callers, tests, config, deploy triggers, docs that
  now lie.

The two scopes must not overlap. Two testers checking the same thing is one tester's result twice.

## Launch — both in one message

Call the Task tool **twice in the same message** so they run in parallel:

- `description`: `Tester A — <scope>` / `Tester B — <scope>`
- `subagent_type`: `generalPurpose` (`explore` is fine for a read-only `critique`)
- `model`: `inherit` unless `model=` was given. Both testers use the same model.
- `implement` mode: `subagent_type: best-of-n-runner` so each gets its own branch and worktree.
  Two testers editing one working tree will overwrite each other.
- Pass `file_attachments` for any image the user attached that bears on the task.

Tester prompt template — fill every `<…>`:

```text
You are Tester <A|B> on a two-tester review. Another tester covers <other scope>; stay out of it.

Repo: <REPO>   Branch: <BRANCH> @ <SHA>
Uncommitted changes: <DIRTY or "none">
Task: <the task, in full — you cannot see the conversation>
Plan / diff to read: <paths, or the git diff command to run>
Your scope: <one line>
Mode: <critique|test|implement>
Repo rules that apply: <from AGENTS.md / CLAUDE.md>

Rules:
- <critique: do not edit anything | test: run anything read-only, edit nothing |
  implement: edit only <files>, commit on your worktree branch, never push, never merge>
- Never deploy, never write to a shared database, never force-push.
- Every finding carries evidence: file:line, command + output, or a failing test.
  No evidence, no finding. "Looks fine" is not a result — say what you checked.

Reply with exactly:
1. Verdict: agree | disagree | blocked
2. Findings: F-<a|b>-<n> — severity (fix-now | defer | nit) — claim — evidence
3. Checked and fine: what you verified and how
4. Not checked: what you could not reach, and why
```

## Verify, then act

Treat tester output the way `/ask` treats a cold read: **re-check every finding against the code
before you adopt it.** Then show one table:

| Finding | Tester | Verdict | Evidence |
|---|---|---|---|

Verdicts: **fix-now**, **defer** (with a reason), **false positive** (with the file:line that
disproves it).

- Fix the fix-now items yourself, or send them back to the tester that found them with `resume`
  set to that tester's agent ID — it keeps its context.
- `rounds=<n>` (default **2**) caps the back-and-forth. After the cap, stop and report what is still
  open instead of looping.
- `implement` mode: review each tester's branch diff before you take any of it. You merge the
  worktree branches into the working branch; the testers never do.

## Browser work

Only one tester touches a browser at a time — there is one shared browser. Follow
`playwright-headed-mcp.mdc` if the Playwright MCP is available; if it is not, the tester reports
the UI as **not verified** rather than substituting another browser.

## You still own

- Every commit on the working branch, every push, every PR, every merge. Do not run `/close-out`
  from inside `/drive`.
- The final word. Two testers agreeing is evidence, not proof — verify it.

## Report

Target (repo, branch, SHA) · mode · each tester's scope and verdict (link them as
`[Tester A](<agent-id>)`) · the findings table · what you changed · what is still open.
