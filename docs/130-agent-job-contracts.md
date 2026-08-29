```yaml
description: Pipeline agents that talk through a queue — a typed registry mapping agent to payload and result schema, routing as data, strict on consumed fields and must-ignore on extras, and an envelope carrying schema version, trace context and an idempotency key
globs:
  - "**/agent-contracts/**/*.ts"
  - "**/py-lambdas/**/*.py"
  - "**/node-lambdas/**/*.{ts,mjs}"
  - "**/*job*.{ts,py}"
alwaysApply: false
```

# Agent job contracts (pipeline agents behind a queue)

**Scope, first paragraph:** this file governs an agent that is **invoked with a payload, runs once,
and returns a result** — a worker behind a queue, a Lambda, a step in a fan-out. A **long-lived
conversational agent** extended by plugins and skills uses
[`125-agent-harness-extension.md`](125-agent-harness-extension.md) instead. There is no skill rung
here and no queue there; applying either file to the other's architecture manufactures wrong
answers.

**Cited implementation:** `app-monorepo/libs/agent-contracts` — a zod registry mapping agent name to
payload schema, result schema, and execution weight class, tested by `contracts.spec.ts`. This is
the most mature architecture of the four codebases that seeded this band, and most of this file is
derived from it.

| This file is… | Precedence |
|---|---|
| **derived from** `agent-contracts` — the registry, weight class → queue, shallow result schemas, must-ignore payloads | that implementation wins |
| **deliberately narrower** — the safety conditions on must-ignore | states its reason below |
| **downstream** — the envelope has no idempotency key today | this file wins; the omission is the grounding |

## Do

- **Keep one registry** mapping agent name → payload schema + result schema + execution class.
- **Make routing data.** The execution class picks the queue; nothing switches on the agent's name.
- **Be strict about the fields you consume** and tolerant of fields you do not.
- **Version the envelope** and carry the version on every message.
- **Carry an idempotency key** on any job whose agent has a side effect.
- **Continue the trace** the envelope hands you ([`110`](110-llm-observability.md)).

## Don't

- **Don't accept an untyped payload** because "the handler knows what it needs." The handler is the
  only thing that knows, which is the problem.
- **Don't switch on the agent name to pick infrastructure.** That is a registry with extra steps
  and it drifts.
- **Don't model result fields nobody reads.** A deep schema over a `jsonb` column is a migration
  you did not need.
- **Don't spread an envelope payload into a prompt.** See the extras rule below —
  [`105`](105-llm-trust-boundary.md) is the enforcement.

## One registry, and routing is data

Every agent has a row: what it accepts, what it returns, and what class of machine it needs. The
class picks the queue — I/O-bound work, memory-buffering image work, CPU-heavy native work, and
external-GPU work do not belong in the same lane, and the mapping from class to lane is a lookup,
not a conditional.

**Derive the schemas from the live handlers**, not from an aspiration: every required key is one the
handler hard-fails without, every optional key is one it reads with a default. A schema written
ahead of the handler is a second source of truth that will disagree with the first.

**Result schemas are shallow and own their shape.** Model the keys downstream code actually reaches
for; when results land in a `jsonb` column, over-modelling buys nothing and costs a migration.

## Strict on what you consume, must-ignore on extras

Payload objects are **loose**: unknown keys pass through rather than failing validation. In Acme
this is load-bearing — the dispatcher spreads a request body into `payload`, so *"unknown extras are
the contract, not a validation failure."*

**This is not a relaxation of [`100`](100-llm-call-pathway.md)'s validation rule.** A loose schema
still enforces every **declared** key's presence and type; it only declines to reject the undeclared
ones. That is must-ignore semantics, the standard way a versioned contract evolves without
lock-step deploys.

Two things make it safe, and both must be true:

1. **The envelope is versioned.** The schema version is what stops yesterday's silently-ignored
   extra from becoming today's declared field carrying a value nobody validated. Without a version,
   must-ignore is just an unvalidated field with better manners.
2. **Extras never reach a prompt.** They may travel through the system; they may never be
   concatenated into prompt text. A field nobody declared is a field nobody validated, and a prompt
   is where unvalidated text becomes instructions. Build prompts from declared, validated fields —
   never by spreading a payload. This is the precise line between this file and
   [`105`](105-llm-trust-boundary.md), and it is stated in both.

## What the envelope carries

Beyond the payload itself, four fields earn their place on every message:

| Field | Why |
|---|---|
| **schema version** | makes must-ignore safe (above) and makes a rolling deploy possible |
| **trace context** | the entrypoint roots the trace; agents continue it ([`110`](110-llm-observability.md)) |
| **idempotency key** | makes retry safe (below) |
| **correlation ids** — job, project, org, connection | so a result can be routed and a failure attributed |

### The idempotency key

[`100`](100-llm-call-pathway.md) requires retrying transient failures. That requirement is only safe
if the work is dedupable, and **the envelope is where the key lives** — the producer derives it from
the unit of work, every retry of that job reuses it, and the sink dedupes on it.

Grounded in a live gap in the cited implementation: the job envelope carries `jobId`, `traceContext`
and a schema version, and `grep -i idempoten` across `agent-contracts`, the shared layer, and every
handler returns **nothing** — while the shared Gemini wrapper retries **image generation**. A
provider deadline on a call the model actually completed bills twice and can deliver twice.

`jobId` is not automatically an idempotency key. It is one only if a retry reuses the same job id
*and* the sink treats it as a dedupe key. If a retry mints a new job, it is a correlation id and
nothing more — say which one you have.

## Canonical shape

A registry entry — the `agents.ts` contract, reduced:

```ts
/** Execution class decides the queue. Routing is a lookup, never a switch. */
export const weightClassSchema = z.enum([
  "thin",   // provider SDK call + glue        → agent-jobs
  "image",  // buffers pixels in RAM           → agent-jobs-image
  "heavy",  // native CPU work                 → agent-jobs-heavy
  "gpu",    // external GPU box                → agent-jobs-gpu
]);

// Payloads are LOOSE: the dispatcher spreads a request body in, so unknown
// extras are the contract. Loose still enforces every DECLARED key — this is
// must-ignore, not "unvalidated". Safe only because the envelope is versioned
// and extras never reach a prompt (see 105).
const geminiTextPayload = z.object({
  prompt: z.string().min(1),
  gemini_model: z.string().optional(),
  temperature: z.number().optional(),
  webhook_url: z.string().url().optional(),
}).loose();

// Result schemas are SHALLOW and model only what downstream reads.
const geminiTextResult = z.object({
  text: z.string(),
  model: z.string(),
  grounding: z.unknown().optional(),
}).loose();

export const AGENTS = {
  gemini_text: {
    weightClass: "thin",
    payload: geminiTextPayload,
    result: geminiTextResult,
  },
  // …one row per agent. Adding an agent is a row, not a code path.
} as const;
```

And the envelope those payloads travel in:

```ts
export const jobEnvelope = z.object({
  v: z.literal(1).default(1),          // makes must-ignore safe; enables rolling deploys
  jobId: z.string().min(1),
  agent: z.string().min(1),
  payload: z.record(z.string(), z.unknown()),
  idempotencyKey: z.string().min(1),   // derived from the unit of work; stable across retries
  traceContext: traceContextSchema.nullish(),   // continue it, never self-root — see 110
  projectId: z.string().nullish(),
  orgId: z.string().nullish(),
  enqueuedAt: z.iso.datetime(),
});
```

The whole contract is one file both sides import: the dispatcher validates on the way in, the
handler is a typed `(payload) → result` function, and `contracts.spec.ts` asserts the registry stays
consistent with itself. A new agent is a new row — not a new branch in a router.
