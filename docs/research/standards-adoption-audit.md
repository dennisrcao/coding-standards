# Standards adoption audit — which rules actually landed, in which repo

**Status:** reference — read-only survey, verified 2026-09-02. No rules changed, none proposed.

Run because a claw-calendar refactor raised the question *"shouldn't we bring in the relevant global
coding standards first?"* The answer for that refactor turned out to be **no** (see
[§5](#5-what-triggered-this)), but the question exposed something worth recording:
**the library has a designed adoption-tracking mechanism, and not one repo uses it.**

`standards-adoption.yaml` and `README.md` both instruct: *"record what landed in
`standards.lock.yaml` (copy the example into the target repo)."* Across nine repos on this Desktop,
**zero have a `standards.lock.yaml`.** So "which standards is repo X missing" has no machine-readable
answer anywhere today; it is reconstructible only by diffing each repo's `.cursor/rules/` against the
manifest by hand — which is what this document is.

**The good news is narrower than expected.** claw-calendar — the repo that prompted the question — is
the best-documented of the nine. Of 19 adoptable rules it carries 12 and explains 6 of the 7 absences
in its own `CLAUDE.md`. **Exactly one rule is unaccounted for, and it is the one written from this
repo's own bug.**

**No target repo for the survey itself** — it is read-only. The follow-ups in §8 that touch
claw-calendar land in **clone 1**, `~/Desktop/claw-calendar` (`:3000`), confirmed by
Dennis 2026-09-02 — not `claw-calendar-2` (`:3001`) or `-3`.

---

## 1. Headline

| Finding | Detail |
|---|---|
| `standards.lock.yaml` adoption | **0 of 9 repos.** The mechanism exists (`standards.lock.yaml.example`), is referenced twice in the library, and has never been used. |
| claw-calendar unaccounted rules | **1** — `026-optimistic-updates` |
| claw-calendar mischaracterized deferrals | **1** — `101-llm-adoption-order` |
| `001-repository-rules` (in the `baseline` profile — *"any repo"*) | adopted in **1 of 5** frontend repos: claw only |
| Repos with no `.cursor/rules/` at all | `dian-nao`, `producer-pal` |
| Repos still on pre-numbering rule names | `storyboard-agent` (`zustand-store-pattern.mdc`, not `020-zustand.mdc`) |

---

## 2. claw-calendar — rule by rule

Adopted set read from `.cursor/rules/` (12 files); deferral reasons quoted from the repo's
`CLAUDE.md` § *Not adopted / deferred*. Adoptable set from `standards-adoption.yaml`.

| Rule | In repo | Verdict |
|---|---|---|
| 001 repository-rules | ✅ | adopted |
| 005 fastapi-python | ✅ | adopted (applypilot is Python) |
| 010 frontend-scss | ✅ | adopted |
| 015 folder-organization | — | **deferred, documented** — *"`hooks/queries/` and `components/<feature>/desktop\|mobile` are retained as repo-native conventions"* |
| 020 zustand | ✅ | adopted |
| 025 tanstack-query | — | **deferred, documented** — *"wrapper pattern is retained; `queryOptions` factory is not mandated across the legacy query suite"* |
| **026 optimistic-updates** | — | ⚠️ **unaccounted for** — see §3 |
| 030 lint-format-quality | ✅ | adopted (`030-formatting.mdc`, copied whole per the manifest's exception) |
| 040 keyboard-shortcuts | ✅ | adopted |
| 050 anti-slop | ✅ | adopted — correct, the repo runs Fallow (`.fallowrc.json`, `npm run fallow:audit`) |
| 080 unused-scss-classes | ✅ | adopted |
| 100 llm-call-pathway | ✅ | adopted |
| **101 llm-adoption-order** | — | ⚠️ **deferred on a wrong premise** — see §4 |
| 105 llm-trust-boundary | ✅ | adopted |
| 110 llm-observability | ✅ | adopted |
| 120 prompt-and-context-budget | — | deferred, documented — local Ollama pathways don't use commercial context budgets |
| 125 agent-harness-extension | — | deferred, documented — same reason |
| 130 agent-job-contracts | — | correctly absent — the manifest says conversational agents take 125, *not* 130 |
| 140 llm-evals | ✅ | adopted |

Not adoptable as `.mdc` and correctly absent everywhere: 060, 070, 090, 091, 150.

**Verdict: 12 adopted, 6 deferred with a written reason, 1 unaccounted, 1 deferred on a wrong
premise.** That is a good result. The two flagged items are both worth a one-line fix in
`CLAUDE.md`, not a refactor.

---

## 3. `026-optimistic-updates` — the repo it came from never adopted it

This is the finding worth acting on.

**026 was written from claw-calendar's own bug.** Its motivating failure mode, quoted from
`docs/frontend/026-optimistic-updates.md`:

> *"a drag-to-schedule mutation optimistically updated the todo cache but not the calendar cache, and
> did so for `schedule` but not for `unschedule`. Typecheck, unit tests, and lint were green… the card
> updated instantly and the calendar grid lagged a full refetch behind."*

That is `useTodoSchedule` in this repo — the bug fixed by commits `d48619d8`
(*"kill the waterfall in scheduling"*) and `4d0ead52` (*"optimistic in BOTH caches, and in both
directions"*).

**And the repo's code cites the standard by name.** From
`sigma-grindset-dashboard/apps/web/hooks/queries/dualCacheWrite.ts:11-13`:

```ts
 * `026-optimistic-updates.md` rule 1: a mutation that invalidates two query keys owes an
 * optimistic write to both. Scheduling shipped once writing only the todo cache while
 * invalidating the calendar's too — the card updated instantly and the event took a full
 * refetch to appear, which read exactly like the drag had failed.
```

So the source file treats 026 as binding authority, while `CLAUDE.md` neither `@`-imports it nor
lists it as deferred. **The rule is in force in practice and absent on paper.** Any future
`hooks/queries/` mutation is written by an agent that has never been shown the rule — which is
precisely the condition that produced the original bug.

**Fix:** copy `docs/frontend/026-optimistic-updates.md` → `claw-calendar/.cursor/rules/026-optimistic-updates.mdc`
and add the `@` import to `CLAUDE.md`. Low risk — the repo already complies.

The globs **do** need rewriting, and the repo's convention is unambiguous. Canonical 026 ships
`apps/*/src/**`, `apps/*/app/**`, `**/hooks/queries/**` — of which only the third would match, since
this repo's tree is `sigma-grindset-dashboard/apps/web/…`. Every rule already in
`claw-calendar/.cursor/rules/` fully qualifies its globs from the repo root (e.g. `020-zustand.mdc`
uses `sigma-grindset-dashboard/apps/web/stores/**/*.ts`), uses `---` frontmatter rather than the
canonical ```` ```yaml ```` fence, and carries a *"Canonical source:"* pointer line back to the hub.
Follow all three.

---

## 4. `101-llm-adoption-order` — deferred as something it isn't

claw's `CLAUDE.md` defers it with: **"101 LLM adoption order: Meta-rule for documentation hub."**

That is not what 101 is. From its own header:

> *"This file tells you **when** each rule inside the `100`+ band starts binding… The library has no
> adoption-timing guidance at all; this file is the only statement of it."*

And `standards-adoption.yaml` puts 101 in both agent profiles, with the note *"101 gates which 100+
claims bind on day one inside the copied files"* and *"read 101 first."*

claw has adopted **four** rules from that band (100, 105, 110, 140) while dismissing the doc that
says which of their claims bind on commit one versus which are trigger-gated. The practical effect:
those four read as uniformly in-force, when 101 would mark parts of them as targets pending a named
event.

**Fix:** either adopt 101, or replace the deferral line with the real reason. This is a documentation
correction, not a code change.

---

## 5. What triggered this

The claw-calendar desktop-shell refactor
([desktop-panel-organization.md](../../../claw-calendar/docs/development/z_proposals/desktop-panel-organization.md))
prompted: *bring in the global standards first, then apply them one by one?*

**Checked, and no — 015 is not a prerequisite for that work:**

1. **Wrong shape.** 015 mandates `src/`, `routes/`, `api/<resource>/queries.ts`, `plugins/`,
   `utilities/`. claw-calendar is Next.js App Router — `apps/web/app/`, no `src/`, no `routes/`. The
   standard was written against the studio app's Vite SPA.
2. **It contradicts a finished migration.** 015 §2 mandates feature-private `<feature>/hooks/`;
   claw's `docs/coding-standards/components-layout.md` says *"Do not add `hooks/` under random
   `components/` subtrees"* and marks its own Phases 1–6 **complete**.
3. **It governs nothing in that plan**, which explicitly rules the folder restructure out of scope.

The standards that *do* govern that refactor — 010, 020, 030, 050, 080 — are all **already adopted**.

**One genuine gap surfaced, recorded here and deliberately not acted on:** none of the seven
frontend standards covers **UI information architecture** — where a control lives relative to the
thing it controls, where a feature's settings live, what a tile's chrome may carry. The refactor
plan's organizing rule (*top-left rail configures what's on screen; top-right rail navigates; one
expand affordance in shared chrome; nothing configures a feature except that feature*) is effectively
a new standard written inline in one repo's proposal. It would apply to studio and portfolio too.
**Per Dennis, 2026-09-02: do not add it yet** — let the rule prove itself in one repo before it is
theorized into three.

---

## 6. Cross-repo observed state

**Observed only.** Rule files listed; profile fit assessed **only for claw-calendar**. Do not read a
blank cell as "missing" for the other repos — several may be correct for their stack.

| Repo | `.cursor/rules/` contents | Stack probe |
|---|---|---|
| claw-calendar | 001, 005, 010, 020, 030, 040, 050, 080, 100, 105, 110, 140 | Next.js · Query · Zustand · SCSS modules |
| app-monorepo-1 | 010, 015, 020, 030, 080 | Vite SPA · Zustand · SCSS modules |
| studio | 010, 020, 030 | Zustand · SCSS modules · no Query |
| portfolio | 010, 020, 030, 080 + local `coding-standards.mdc`, `dev-workflow.mdc` | Zustand · SCSS modules · no Query |
| design-styles | 010, 080 | SCSS modules only |
| storyboard-agent | `fastapi-python`, `frontend-scss-nesting-matches-jsx`, `zustand-store-pattern` — **pre-numbering names** | Query · Zustand · SCSS modules |
| dian-nao | **none** | Zustand · SCSS modules |
| producer-pal | **none** | — |
| \_\_Documentation | 010, 015, 020, 030 + hub-local (`040-plan-lifecycle`, `050-aws-acme-accounts`, `no-tailwind`, `ticket-worktree`) | the hub itself |

Patterns worth a second look, none investigated:

- **`001` is in the `baseline` profile — *"Any repo"* — and only claw has it.** Either the four other
  frontend repos drifted, or `baseline` overstates its reach.
- **`storyboard-agent` uses Query but carries no 025/026**, and its rule filenames predate the
  numbering scheme entirely — it looks like it was set up before the library existed and never
  revisited.
- **`design-styles` has 010 + 080 but not 030**, so it is below `baseline`.
- **`portfolio` carries two local rules** (`coding-standards.mdc`, `dev-workflow.mdc`) that are not
  library rules. Unread — they may duplicate or contradict library content.

---

## 7. What was NOT assessed

- **Content drift.** Only filenames were compared. A repo can carry `020-zustand.mdc` whose body has
  diverged from the canonical `docs/frontend/020-zustand.md`. Nothing here checks that, and a
  filename match is not a content match.
- **Compliance.** Whether code actually follows an adopted rule. 026 is the sole exception — its
  compliance was confirmed by reading `dualCacheWrite.ts`.
- **Profile fit for eight of nine repos.** §6 is observation, not verdict.
- **The two local `portfolio` rules**, unread.
- **Whether app-monorepo uses TanStack Query.** A `package.json` grep found no `@tanstack/react-query`;
  not investigated further, so its 025/026 absence is not called a gap.

## 8. Suggested next steps

Ordered by value per unit of work. **None involve editing a canonical rule** — per Dennis, the
library itself stays as-is unless a genuinely general rule is missing.

1. **Adopt 026 into claw-calendar** (§3). One file copy plus a `CLAUDE.md` line. The repo already
   complies; this closes the gap between a rule the code cites and a rule the agent is shown.
2. **Fix claw's 101 deferral line** (§4). One line, no code.
3. **Decide whether `standards.lock.yaml` is real.** It is documented in two places and used in
   zero repos. Either generate one per repo — this audit is most of the content for claw — or delete
   the example and the instructions, so the library stops promising a mechanism nobody runs.
4. **Look at `001` across the four other frontend repos** (§6). Cheap, and it either finds real drift
   or corrects the `baseline` profile's claim to apply to "any repo".
5. **Re-run this survey after any adoption change.** Research lane — this doc is meant to be
   re-verified, not archived.
