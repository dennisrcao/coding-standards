# Argue protocol — driver ↔ tester plan debate on Fabric

Not a slash command. `/argue` and `/driver` include this by reference.

## Purpose

Run a **bounded** plan debate on one mesh: driver publishes `plan-critique` /
`plan-revise`, testers reply with `plan-review`, driver **verifies every claim**
before editing the plan, loop until all testers `agree` or a stop condition fires.

This is the Fabric mesh loop. It is **not** `/debate` (headless `claude -p`) and
**not** `/ask` (one volley to the other agent's binary).

## Prerequisites

- Mesh slug resolved (`calendar-1`, `core-1`, …).
- `~/.agent-mesh/missions/ACTIVE-<mesh>` points at the mission file.
- Mission has `## Scopes` filled and at least one tester in `## Roster`, or
  `fabric_discover` shows `tester-<mesh>-*` with `meta.core` matching.
- Plan path: absolute path in `$ARGUMENTS`, or `planPath` / `**Plan:**` in the
  mission header.
- Testers are **tmux** (`tester-up <mesh> a`). Sidebar Claude tabs cannot receive
  Fabric — do not substitute `claude -p`.

## Channels

Same as `/driver`:

- Publish to testers: `mesh.<mesh>.tester`
- Drain / wait: `mesh.<mesh>.driver`

Never `role.tester`, `role.driver`, or `agent.claude`. No `fabric_request`.

## Ledger

`<planPath>.argue.md` beside the plan. Memory across `/argue` turns — each
`/argue` turn reads and updates it.

```markdown
# Argue: <plan title>
Mesh: calendar-1   Plan: <abs path>   Checkout: <abs path>   Round: N of 3

## Claims
| # | Claim | Tester | Status | File:line | Evidence |
| 1 | … | a | OPEN | … | one line |

## Plan edits applied
- round 1: …

## Round log
- round 1: published plan-critique · testers a=disagree b=agree · 2 CONFIRMED · 1 REFUTED
```

**Status** (driver sets after verification, not the tester):

| Status | Meaning |
|---|---|
| **CONFIRMED** | Verified true; plan was wrong or incomplete here |
| **REFUTED** | Verified false, with evidence |
| **MISREAD** | True of other code / another plan |
| **UNVERIFIABLE** | Product or design call — name whose |
| **OPEN** | Not closed by evidence from either side |

Evidence rule: a claim may only leave OPEN via `file:line`, real command output,
or a commit SHA.

## Payloads

**Round 1 — critique**

```json
{
  "kind": "plan-critique",
  "mesh": "calendar-1",
  "planPath": "/absolute/path/plan.md",
  "sha": "<git sha at checkout>",
  "round": 1,
  "maxRounds": 3,
  "ask": "Agree or disagree per section. Disagreement needs file:line, what breaks, and the state that triggers it. End with verdict agree | disagree | blockers."
}
```

**Round 2+ — revise**

```json
{
  "kind": "plan-revise",
  "mesh": "calendar-1",
  "planPath": "/absolute/path/plan.md",
  "sha": "<sha after edits>",
  "round": 2,
  "changes": "<one paragraph: what changed since last round>",
  "openClaims": [1, 4],
  "ask": "Re-review OPEN claims and anything you disagreed with last round."
}
```

**Tester reply** (on `mesh.<mesh>.driver`):

```json
{
  "kind": "plan-review",
  "mesh": "calendar-1",
  "scope": "a",
  "planPath": "…",
  "verdict": "agree | disagree | blockers",
  "notes": "…",
  "tester": "tester-calendar-1-a-…"
}
```

**Done**

```json
{
  "kind": "plan-agree",
  "mesh": "calendar-1",
  "planPath": "…",
  "sha": "<final sha>",
  "rounds": 2
}
```

Append to mission `## Log`: `plan-agree @ <sha> after <n> rounds`.

## One `/argue` turn (driver)

1. **Drain first.** `fabric_drain({ channel: "mesh.<mesh>.driver" })`.
2. **Resolve** mesh, checkout, plan path, sha (`git -C "$CHECKOUT" rev-parse HEAD`).
3. **Open ledger** — create if missing; read current round.
4. **Roster check.** If no testers visible, stop: `tester-up <mesh> a`.
5. **Publish** `plan-critique` (round 1) or `plan-revise` (round > 1) on
   `mesh.<mesh>.tester`.
6. **Collect** `plan-review` messages:
   - Default **`wait`**: `fabric_wait` loop on `mesh.<mesh>.driver`, up to **5**
     consecutive empty 55 s waits, or until every rostered scope has replied for
     this round.
   - **`no-wait`**: drain once, process what arrived, tell user to run
     `/argue <mesh> wait` to continue.
7. **Verify** every objection in each `plan-review.notes` — atomic claims,
   verdict each CONFIRMED / REFUTED / MISREAD / UNVERIFIABLE / OPEN with
   `file:line`. Update the ledger table. Show the user the verification table
   before editing the plan.
8. **Edit plan** only for CONFIRMED claims. Record under "Plan edits applied".
9. **Stop check** (in order):
   - All testers `verdict: agree` → publish `plan-agree`, mark ledger done, stop.
   - No OPEN claims after verification and all testers `agree` or only REFUTED
     objections remain → `plan-agree`, stop.
   - Round ≥ `maxRounds` (default **3**) → append to plan:

     ```markdown
     ## ⚠ Unresolved after /argue

     <table of OPEN / UNVERIFIABLE claims with tester scope>
     ```

     Stop; user decides. Do **not** `plan-agree`.
   - Else → increment round, publish `plan-revise`, end turn (user runs
     `/argue <mesh> wait` for the next collection pass, or one turn does
     publish + wait if time allows).

## Max rounds

Default **3** critique rounds per `/argue` invocation chain. Do not exceed —
testers and drivers will manufacture objections indefinitely. Round count is in
the ledger; resetting requires a new ledger file (rename or delete
`<plan>.argue.md`).

## HARD RULES

- **Plan markdown only** — no product code edits, no commit/push from `/argue`.
- **Verify before edit** — same bar as `/ask` Step 4.
- **All file reads in mesh checkout** — `git -C "$CHECKOUT" …`.
- **Stage explicit paths** if the plan lives in a repo and you commit later from
  `/driver` — not inside `/argue`.
