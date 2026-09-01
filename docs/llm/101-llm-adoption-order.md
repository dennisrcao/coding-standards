```yaml
description: Which of the 100+ agent/LLM standards are binding on day one of a new project and which are targets until a named event fires — plus the gate question, do you need an agent at all
globs:
alwaysApply: false
```

# Adopting the `100`+ band (what is in force on day one)

The rest of this library tells you **how** to adopt a standard — copy `docs/<category>/<NNN>-*.md`
into the target repo's `.cursor/rules/`, rewrite the globs, `@`-import it. This file tells you **when** each
rule inside the `100`+ band starts binding.

That gap matters more here than for the SCSS or Zustand rules. Several docs in this band solve
problems a new project does not have yet, and adopting them on commit one builds exactly the
speculative infrastructure [`125`](125-agent-harness-extension.md) warns against — a hook with no
consumer, an envelope with no queue, a confirmation seam on a pipeline that cannot actuate.

| This file is… | Precedence |
|---|---|
| **derived from** the seven docs it sequences | those docs win on *what* the rule is; this file only says *when* |
| **deliberately narrower** — the two day-one rules the band has no doc for | stated in *Not in any doc yet* below |
| **downstream** — the library has no adoption-timing guidance at all | this file is the only statement of it |

## How to read this

**You still copy whole files.** The library's adoption procedure copies a doc; step 4 already
permits trimming a downstream copy to a narrow extract, but gives no guidance on which extract.
That is this file's only job. It does **not** tell you to scissors a file, and it is not a licence
to skip the parts you find inconvenient.

- **In force** — binding from commit one. If you cannot satisfy it, you have a decision to record,
  not a rule to ignore.
- **Trigger-gated** — present in the file you copied, not yet binding. Each names a **checkable
  event**, not a feeling. When the event fires, the rule is in force.

---

## First: do you need an agent at all?

Before copying anything, answer this. **If there is no tool loop you do not control** — if your
system is one structured model call, or a fixed chain of them, with no model-chosen next step —
then [`125`](125-agent-harness-extension.md) and [`130`](130-agent-job-contracts.md) do not apply to
you at all. Take `100`, `105`, `110` and `140` as a structured-call subset and stop.

This is the cheapest decision on the list and the one most often skipped. The band was derived from
four codebases that had all already chosen "agent," so none of them can tell you this — which is
precisely why it is written down here.

---

## From [`100-llm-call-pathway`](100-llm-call-pathway.md)

**In force**

- **Ask for constrained output natively, and validate into your own type.** A cast is not
  validation. Always.
- **Pin the model** — a dated snapshot, never a moving alias. Always. An alias that silently moves
  is how a working classifier rots without a deploy.
- **Retry only provably-transient failures, classified structurally** — a typed exception or a
  status code, never a substring of the error message. This is a *constraint on retry*, not a
  feature to build: it binds the moment you add your first retry, and costs nothing before then.
- **First timeout sits under a named platform ceiling** (API Gateway's 29 s, your ingress' limit,
  the caller's own budget). You do not need a measured p99 to name a ceiling, and the ceiling is
  what stops the copied-from-elsewhere timeout that turns every cold call into a 504.
- **An idempotency key on any retried call with a side effect** — image generated, event created,
  message sent, job enqueued — *if such a call exists on day one*. Free at design time, a migration
  later.

**Trigger-gated**

| Rule | Adopt when |
|---|---|
| A cheap deterministic tier before the model | you have a **closed intent set or command grammar**. Generation and image analysis have no cheap tier, and inventing a brittle one is worse than not having one — the doc says so itself |
| The full degradation ladder (retry → fallback → last-resort-valid) | you have a **batch whose items must not abort each other**, *and* `110`'s aggregate degradation rate is already reported. Last-resort-valid without that rate re-creates the silent-dead-path `110` exists to stop |
| Timeout derived from a recorded cold/warm p99 | **you have a measurement.** The ceiling above does not wait for it |

## From [`105-llm-trust-boundary`](105-llm-trust-boundary.md)

**In force**

- **The actor comes from the authenticated request or session, never from a model field.** Always,
  and before everything else in this doc — every ownership check below is meaningless if the model
  chose the subject.
- **Never concatenate retrieved or untrusted text into the system prompt**, and **redact at the log
  boundary** — *if any untrusted text enters context*, which for most projects is day one.
  Credentials never appear in prompts, tool arguments, or logs.

**Trigger-gated**

| Rule | Adopt when |
|---|---|
| Allowlisted tool arguments + a confirmation seam on irreversible actions | **the model can actuate** — there is an action table, a tool that writes, sends, spends, or deletes. A pipeline that only returns JSON does not need `ctx.confirm` stubbed to `true`; that is the speculative infrastructure this band warns about |

## From [`110-llm-observability`](110-llm-observability.md)

**In force**

- **"The model failed" and "the model said no" are different events.** One typed outcome carrying a
  stable reason token, initialised `unknown` — not `ok`. Always. This is roughly ten lines on day
  one and it is the rule that ends the class of failure where a dead path runs unnoticed for weeks.

**Trigger-gated**

| Rule | Adopt when |
|---|---|
| The stateless variant (structured per-invocation outcome, transition detection in the metric store) | the process is **serverless or short-lived**. In-process health in a Lambda resets every cold start and can never represent "dead for a week" |
| Aggregate degradation rate on the result | you have a **batch or fan-out** — the same trigger as `100`'s ladder, and they must land together |
| Trace continuation and release stamping | there is **more than one hop**, or a deploy pipeline that can stamp a commit SHA |
| Output-token headroom alerting | you have **a stage whose output can approach its own `max_tokens`** — long generation, not a short classification |

## From [`120-prompt-and-context-budget`](120-prompt-and-context-budget.md)

**In force**

- **Bound every string entering model context at the dispatch boundary.** This is a **sibling of
  `100`'s retry rule**, not a later concern: an unbounded provider error body enters context once
  per retry and stacks. Adopt it on the same day you add retry.

**Trigger-gated**

| Rule | Adopt when |
|---|---|
| Compose shared prompt fragments | **the same prose appears in a second prompt.** The doc itself permits one prompt constant per call site when there is genuinely one prompt — splitting a single prompt into four YAML fragments on commit one *causes* the drift it exists to prevent |
| Fragment version ids | the offline eval has **run against two different prompt texts** |
| Prompt-cache stability rules | the provider documents prefix caching **and** either `cache_control` (or its equivalent) is set, or you persist conversation history across turns |
| Tool-description discipline (teaches behavior, no cross-tool references) | **you have tools.** Not applicable to a single-call pipeline |

## From [`125-agent-harness-extension`](125-agent-harness-extension.md)

Answer the gate question first — most new projects do not need this file at all.

**In force**

- Nothing on day one. This entire document is trigger-gated, which is consistent with its own thesis.

**Trigger-gated**

| Rule | Adopt when |
|---|---|
| The footprint ladder | the diff **adds a second tool, skill, command, or plugin**, *or* behavior would be implemented by **patching vendored or core harness code**. Not gated on having contributors — one author is entirely capable of creating a thousands-of-files fork tax |
| Session-scoped capability resolution | the process **serves more than one session** |

## From [`130-agent-job-contracts`](130-agent-job-contracts.md)

Answer the gate question first.

**In force**

- Nothing on day one *of an LLM project*. The rules below are day one **of a queue**, which is a
  different birthday.

**Trigger-gated**

| Rule | Adopt when |
|---|---|
| Typed registry (agent → payload schema + result schema) | **two named agents** — two dispatchable functions with payload shapes. Not five: the doc's whole point is "a new agent is a row, not a branch," and migrating two live payload shapes into a registry later is the work you were trying to avoid |
| The job envelope (`v`, `jobId`, `traceContext`, correlation ids, idempotency key) | **a queue exists.** Note the idempotency key is *also* required by `100` at the call level as soon as a retried side-effecting call exists — same obligation, two places, and the call-level one usually comes first |
| Execution class → queue routing | a job **misses its SLO because it queued behind a different class of work.** An incident, not a count |

## From [`140-llm-evals`](140-llm-evals.md)

**In force**

- **One invariant that is already stated in your prompt, made executable — plus the CI path
  filter.** Always. If your prompt says "durations must sum" or "return one of these six labels,"
  that sentence is a scorer. One test file and a path-filtered workflow is a home for the harness to
  grow into; without it, the first eval never gets written.
- **Do not write change-detector tests**, and **do not read source text as a proxy for behavior.**
  These are free — they only cost you the tests you were about to write badly.

**Trigger-gated**

| Rule | Adopt when |
|---|---|
| A structurally diverse corpus | **a second real input differs on an axis your prompt already names** — length, entity count, density, language. Do *not* wait until "you know what varies": the doc is explicit that building the corpus is how you learn that, and a demo-only corpus tests nothing |
| Labeled gold sets | the task **has a right answer** — classification, extraction, recall. Invariants alone leave "the JSON parsed" as a passing score |
| An LLM judge | a pure function **provably cannot** check the property, and you can state what you are measuring (recall against gold, not "quality") |
| Scheduled live evals | the calls are **cheap enough to run unattended**. Leaving them manual is a spend decision to make explicitly, not a default to inherit — a provider moving a model alias is exactly what it catches |

---

## Not in any doc yet — but day one anyway

The band does not cover these; the library README names them as gaps. On a *new* project they are
still commit-one events, so they are listed here rather than discovered later.

| Rule | Why day one |
|---|---|
| **Settle provider training / data-retention opt-out before the first call carrying customer data** | a later standard cannot unsend it. This is a legal event with a deadline, not an architecture decision |
| **Never retry a started stream** | `100`'s retry taxonomy does not cover partial streams. Retrying one either double-charges or concatenates half a reply onto another half. If you stream on day one — most chat surfaces do — this binds on day one |

## What this band cannot vouch for

Stated as triggers, because the honest form of "we have not covered this" is "here is when you will
need to." These are **not** reasons to distrust the rules above.

| Gap | Decide when |
|---|---|
| Spend caps on unbounded loops | a tool loop or batch can issue N calls with no hard stop |
| Multi-tenant cache isolation | two tenants share a process or a cached prefix — `120` assumes one tenant per conversation |
| Provider abstraction / model routing | you have a second provider, or a routing decision. Pinning (`100`) is not routing |

One caveat about the caveat: the band's silence on cost is **not** evidence that its rules are
economically optional. The idempotency gap that produced `100`'s retry rule *is* a double-billing
exposure — the source codebases hit economics and filed it as correctness.

## Canonical shape

Adopting the band into a new repo, with this file's answer applied:

```bash
# 1. Copy WHOLE files — this doc does not scissors them.
for n in 101-llm-adoption-order 100-llm-call-pathway 105-llm-trust-boundary \
         110-llm-observability 120-prompt-and-context-budget 140-llm-evals; do
  cp "$STANDARDS/docs/llm/$n.md" ".cursor/rules/$n.mdc"
done
# 125 and 130 only if the gate question said you need an agent / a queue.

# 2. Swap the ```yaml fence for --- frontmatter, and rewrite globs for THIS repo's layout.
#    A rule whose globs don't match is a rule that never fires.
```

```markdown
<!-- 3. CLAUDE.md — 101 goes first: it is how the others are read. -->
@.cursor/rules/101-llm-adoption-order.mdc
@.cursor/rules/100-llm-call-pathway.mdc
@.cursor/rules/105-llm-trust-boundary.mdc
@.cursor/rules/110-llm-observability.mdc
@.cursor/rules/120-prompt-and-context-budget.mdc
@.cursor/rules/140-llm-evals.mdc

Adoption order: `101`. Not every rule in these files is in force yet — `101` says which,
and names the event that makes each of the rest binding. Canonical copies live in
`docs-hub/projects/coding-standards/docs/` (see [`README.md`](../README.md) for folders).
```

The last paragraph is the load-bearing part. Without it the next reader finds five rule files, sees
rules the codebase visibly does not follow, and concludes the standards are aspirational — which is
how a rule set stops being followed at all.
