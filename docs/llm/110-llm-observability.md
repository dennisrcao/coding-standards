```yaml
description: Knowing the model path is alive — "it failed" vs "it said no", typed health with stable reason tokens, transition-only logging (and its stateless variant), aggregate degradation rate, output-token headroom, trace continuation, startup preflight
globs:
  - "**/agents/**/*.py"
  - "**/*classifier*.{ts,py}"
  - "**/observability*.{ts,py}"
  - "**/py-lambdas/**/*.py"
alwaysApply: false
```

# Observing the LLM path

A model path fails **quietly**. It returns a plausible value, or a legitimate-looking "nothing to
do," and the caller carries on. Every rule here exists to make a dead path loud.

| This file is… | Precedence |
|---|---|
| **derived from** repeated production incidents — typed health, transition logging | those patterns win |
| **deliberately narrower** — the stateless variant, the headroom denominator | states its reason below |
| **downstream** — aggregate degradation rate is named here because no single repo had it | this file wins |

## The incident this is written from

An LLM classifier fallback ran **dead for weeks**. The default model 404'd on every call, and every
failure path returned the same value as a genuine "this message isn't a command":

> Before typed health existed, every failure path returned the empty intent with a `warn`, so "the
> model 403s on every request" and "the user said something unclassifiable" were the same observable
> event.

Intent detection had silently become regex-only. Nothing was broken enough to notice.

A generation pipeline has the same exposure in a different shape: when a frame call degrades to a
deterministic fallback, it logs one line per frame and returns a valid board. A board where **all
frames** fell back emits many `INFO` lines and reports success. There is no number that says "this
run was fully degraded."

## Do

- **Separate "the model failed" from "the model said no."** They are different events with
  different consequences.
- **Type the health**, with a short stable reason token a consumer can group on without parsing
  prose, plus a human-readable detail.
- **Initialise health `unknown`, never `ok`.** A fresh process has proven nothing.
- **Log on transition**, and word a persistent defect differently from a transient one.
- **Report the aggregate degradation rate** of a batch, not only per-item lines.
- **Continue the trace you were given; never self-root one.**
- **Preflight the path at startup**, with its own longer budget.

## Don't

- **Don't collapse failure into the empty answer.** A rejected shape, a 403, and a real "none" must
  not be the same return value.
- **Don't log every call's health.** A wall of identical errors is as unreadable as silence.
- **Don't call the first success a "recovery."** It is a first result; saying otherwise trains the
  reader to ignore the word.
- **Don't put a per-session answer in a process-wide cache.** One process serves many sessions.
- **Don't read the headroom ratio as a cost signal.** It is a truncation alarm. See below.

## Health is a state machine, not a log line

Five reason tokens cover the real failure surface, and each is a different problem:

| reason | means | persistent? |
|---|---|---|
| `http_error` | the endpoint answered, refusing (404 gone, 403 unentitled) | yes |
| `empty_response` | the call succeeded and returned nothing usable | yes |
| `invalid_json` | the body was not parseable | yes |
| `invalid_shape` | it parsed but failed validation ([`100`](100-llm-call-pathway.md)) | yes |
| `transport` | unreachable, or aborted on timeout | no |

The persistent/transient split is not cosmetic — it decides what the operator is told. A 403 means
*every* call fails identically until a human changes something; a timeout means *that* message fell
back and the next one retries. Wording both as an emergency is how a reader learns to skip the line.

**A genuine `{"intent":"none"}` sets health to `ok`.** That is the entire point: a healthy "no."

## Transition-only logging — and its stateless variant

Report when health **changes**, comparing both the boolean and the reason, so `unknown → ok` counts
(the first success must reach the heartbeat) and `403 → timeout` still reports rather than hiding
behind the first 403.

**This shape is correct for a long-lived process and meaningless in a Lambda.** A serverless handler
starts cold, resolves once, and exits; a process-lifetime health object there can never represent
"dead for a week" — it would either log every invocation (the thing transition-logging exists to
avoid) or log nothing.

**The serverless form:** emit one structured outcome per invocation — `{ ok, reason, model,
latency_ms }` — and do transition detection **in the metric store** (an alarm on the rate of a
reason token over a window). The rule is preserved: a human hears about a *change*, not about every
call. Only the place that holds the state moves.

Long-lived gateway processes use the in-process form; one-shot workers use the metric-store form.
Pick by process lifetime, not by taste.

## Report the degradation rate, not the incidents

Per-item warnings are for debugging one item. The operational question is *what fraction of this
run was degraded* — and that number has to exist on the result, not only in the log.

Emit, per batch/run/job: items attempted, items served by the primary path, items served by each
fallback rung ([`100`](100-llm-call-pathway.md)'s ladder), and the resulting rate. Alert on the
rate. "15 of 15 frames took the deterministic fallback" is an outage; fifteen `INFO` lines are not.

## Output-token headroom — a truncation alarm, not a budget

Log `completion_tokens / requested max_tokens` per stage and warn past ~90 %. State the denominator
explicitly: it is the **request's own cap**, not the model's context window. 90 % of `max_tokens:
256` and 90 % of a 128 k window are different events, and only the first is what this measures.

Report a **ratio**, not a raw count, so it is comparable across stages and holds for any input size.
What it tells you: a denser input is approaching the output cap and will start truncating into
retries. What it does **not** tell you: anything about money. Spend caps are a separate concern and
are named in the deferred list in the library README.

## Trace continuation

The job envelope carries the trace context; the entrypoint roots the trace and **agents continue
it**. An agent that self-roots produces one orphan trace per hop and no pipeline view.

- Read the parent context from the envelope (`traceContext` in
  [`130`](130-agent-job-contracts.md)); absent means "start fresh."
- Sampling is the parent's decision. A child sampler set to 0.0 still honors the parent.
- **Release = the deploy-stamped commit SHA**, and never a fake value — a placeholder like
  `"unknown"` lumps every manual deploy into one bucket, which is worse than no release at all.
- One decorator/middleware at the handler boundary, not instrumentation sprinkled per call.

## Preflight

The first call after startup proves the path works before a user's message depends on it. Two
properties: it runs **once per process lifetime**, and it gets its **own longer budget** — by
definition it cannot hit a warm cache, so holding it to a steady-state timeout guarantees it fails
on every restart ([`100`](100-llm-call-pathway.md) covers the budget derivation).

A preflight that fails should set health, not crash the process: regex-only is a degraded service,
not a dead one.

## Related

Bounding strings that enter model context is a context-budget rule and lives in
[`120-prompt-and-context-budget.md`](120-prompt-and-context-budget.md) — but the *logging* half
belongs here: the log may keep a longer prefix than the model sees.

## Canonical shape

The transition function, with the stateless variant beside it:

```ts
type Health = {
  healthy: boolean;
  reason: "unknown" | "ok" | "http_error" | "empty_response"
        | "invalid_json" | "invalid_shape" | "transport";
  detail?: string;
  at: string;
};

// Starts `unknown`, NOT `ok`. Initialising to healthy makes the first SUCCESS a
// no-op transition, so the hook never fires and only FAILURE is ever recorded —
// a value that reads as absence when it is really suppressed success.
let health: Health = { healthy: true, reason: "unknown", at: new Date().toISOString() };

function setHealth(healthy: boolean, reason: Health["reason"], detail?: string) {
  // Compare BOTH fields: unknown→ok must count, and broken→broken with a new
  // reason must still report, while a steady state stays quiet.
  const changed = health.healthy !== healthy || health.reason !== reason;
  const wasBroken = !health.healthy;
  health = { healthy, reason, detail, at: new Date().toISOString() };
  if (!changed) return;

  if (healthy) {
    if (wasBroken) log.info(`classifier RECOVERED — "${model}" is answering again.`);
    return;                                    // a first result is not a recovery
  }
  const persistent = reason !== "transport";
  log.error(
    `classifier ${persistent ? "DISABLED" : "DEGRADED"} — "${model}" ${detail ?? reason}. ` +
    (persistent
      ? "Every classification is failing this way until the model or config changes."
      : "That call fell back; the next one retries and health clears on success."),
  );
  hooks.onHealthChange?.(health);
}
```

Stateless (serverless) variant — same rule, state moved to the metric store:

```python
# One structured outcome per invocation; the ALARM does the transition detection.
logger.info(json.dumps({
    "evt": "llm_outcome", "ok": ok, "reason": reason,
    "model": MODEL, "latency_ms": elapsed_ms,
}))
# Alarm: rate(reason != "ok") over 15m crosses a threshold → page.
# Do NOT keep a module-level `health` here: every cold start resets it.
```
