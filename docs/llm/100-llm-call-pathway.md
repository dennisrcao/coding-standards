```yaml
description: One LLM call end to end — cheap tier first, constrained output, validate into your own type, a degradation ladder that never regresses, transient-only retry with an idempotency key, pinned models and derived timeouts
globs:
  - "**/agents/**/*.py"
  - "**/*classifier*.{ts,py}"
  - "**/*-llm.{ts,py}"
  - "**/llm/**/*.{ts,py}"
alwaysApply: false
```

# The LLM call pathway (one model call, end to end)

Everything between "I have an input" and "I have a value I can trust." What the validated value is
then *allowed to do* is [`105-llm-trust-boundary.md`](105-llm-trust-boundary.md); whether the path
is alive is [`110-llm-observability.md`](110-llm-observability.md).

**Note on overlap:** [`005-fastapi-python.md`](../backend/005-fastapi-python.md) globs `packages/**/*.py`, so
in a `packages/agents/` layout both files fire. That is correct, not a conflict — `005` governs
transport and framework, this file governs the model call inside it.

**Cited implementations:** `claw-calendar/plugins/sigma-intent` (regex→LLM tiering, response
hardening, measured timeouts), `storyboard-agent/packages/agents` (degradation ladder),
`app-monorepo/apps/py-lambdas/shared_layer` (retry taxonomy), `hermes-agent` (error-body bounding,
config policy). Precedence is per claim:

| This file is… | Precedence |
|---|---|
| **derived from** the cited implementation — tiering, hardening, the ladder, the retry taxonomy | that implementation wins; a disagreement here is a bug in *this* file |
| **deliberately narrower** — retry policy, idempotency, timeout derivation | each narrowing states its reason below and does not defer upward |
| **downstream** — the cited implementation is silent or provably wrong (substring error matching, "retry once", no idempotency key) | this file wins, and says why |

## Do

- **Where a cheap deterministic tier exists, put it first and make it high-precision.** It answers
  only what it matches and returns null otherwise, so novel input falls through to the model instead
  of being dropped. Many pipelines have no such tier — that is not a violation.
- **Ask for constrained output natively** — Anthropic structured outputs or tool use, Gemini
  `response_schema`, OpenAI JSON schema, Ollama `format: "json"`.
- **Validate into your own type.** Per-variant checks and coercion. A cast is not validation.
- **Declare a degradation ladder** and make each rung strictly better-or-equal than the next.
- **Retry only what is provably transient**, classified structurally, with bounded backoff.
- **Carry an idempotency key on any retried call that has a side effect.**
- **Pin the model.** Derive timeouts from a recorded measurement and assert them in a test.

## Don't

- **Don't hand-parse when the provider can constrain.** Hardening is the fallback tier, not the
  contract.
- **Don't classify a retryable error by substring-matching the message** (see below).
- **Don't say "JSON mode."** It is one vendor's spelling; name the provider's actual mechanism.
- **Don't retry a side-effecting call without a key.** That is a duplication policy.
- **Don't put behavioral config in a new env var *as a rule*** — and don't ban it either. See
  *Config plane* below; this is the rule most often over-generalized.

## Two tiers, and why the cheap one must be precise

**This applies only where a deterministic tier is possible** — a closed intent set, a known command
grammar, a lookup. Open-ended generation and image analysis have no cheap tier, and inventing a
brittle one to satisfy this rule is worse than not having it.

```ts
const regexResult = classifyRegex(text);              // returns null when nothing matches
if (regexResult) return { classified: regexResult, source: "regex" };
if (llmClassifier) return { classified: await llmClassifier(text), source: "llm" };
```

Derived from `sigma-intent/src/classify.ts`. The fall-through is what makes this safe: an
unanticipated phrasing reaches the model rather than being silently dropped.

The hazard is the opposite direction — a regex that *hits* on a compound utterance and shadows a
better read. So **record which tier answered** (`source` above is already on the result) and treat a
rising cheap-tier share as a regression signal, not a cost win. Without that number you cannot tell
a precision bug from a traffic-mix change.

## Hardening is the fallback tier — and still necessary

Constrained decoding does not make the parse ladder obsolete. `sigma-intent` sends
`format: "json"` to Ollama **and still** strips `<think>` blocks, because local reasoning models
wrap constrained output in prose. Order matters:

```ts
const cleaned = extractJsonObject(stripCodeFences(stripThinkTags(raw)));
```

Then validate. `validateClassifiedIntent` in `llm-classifier.ts` is the reference: it rejects an
unknown discriminant, requires the fields each variant actually needs, trims strings, and coerces
`amount` to a number — returning `null` rather than a half-built object. A rejected shape is a
**health event** ([`110`](110-llm-observability.md)), not a silent "no answer."

## The degradation ladder

Two stages, in order, and the second may never make the result worse:

- **A — resilience (exceptions):** call → retry → deterministic fallback → minimal last resort.
  This stage never raises. One malformed item must not abort a batch.
- **B — validation (rule violations):** a well-formed result that breaks a prose contract is
  re-rolled **once** with the violation fed back, and the candidate with fewer violations wins.

**Scope this honestly.** Stage B is a *generation* pattern — it works because "fewer violations" is
a real ordering over candidates. It does not transfer to classification, where valid-but-wrong JSON
needs a label and a metric, not a re-roll.

## Retry: right taxonomy, wrong mechanism

Acme's `gemini_retry.py` gets the taxonomy right and this file adopts it wholesale:

| Retryable | Not retryable |
|---|---|
| 504 / deadline exceeded, 503 / unavailable / overloaded, 429 / resource exhausted | 4xx, safety blocks, a genuinely empty response |

Retrying the right column just burns the caller's timeout.

**The mechanism is the part to reject.** It classifies by scanning the error *string*:

```python
GEMINI_TRANSIENT_MARKERS = ("DEADLINE_EXCEEDED", "Deadline expired", "504", ...)
```

This is the bug class hermes bans after ~10 fleet incidents (*"DO NOT infer process identity from
argv substrings"*): a substring is not a type. A message containing `"504"` inside a URL, a
provider rewording its prose, or a wrapped exception all change the answer. **Classify on the
structured signal** — the SDK's typed exception, `response.status`, an error `code` — and fall back
to string matching only where a provider gives you nothing else, with that admission in a comment.

**Bounded exponential backoff honoring `Retry-After`.** "Retry once" is a latency budget, not a
retry policy: a 429 carrying `Retry-After: 5` retried immediately fails again, and you have paid for
two calls and still served the fallback. Bound total attempts so a real outage still fails inside
the caller's own timeout.

## A retry policy without an idempotency key is a duplication policy

Any retried call with a side effect — an image generated, an event created, a message sent, a child
job enqueued — carries a caller-supplied key derived from the unit of work, and the sink dedupes on
it. The retry and the key ship together or neither ships.

Grounded in a live gap: Acme retries `generation_scene` through `gemini_with_retry`, and
`grep -i idempoten` across `agent-contracts`, `shared_layer`, and every handler returns nothing. A
504 on a call the model actually completed bills twice and can deliver twice. The envelope half of
this rule is in [`130-agent-job-contracts.md`](130-agent-job-contracts.md).

## Pins, knobs, and timeouts

- **Pin the model; an alias that silently moves is a defect.** `sigma-intent`'s default proved this
  twice: it 404'd on a model that no longer existed, and the obvious fix (bump the tag) 403'd
  because every `:cloud` tag on that host requires a paid subscription. A default that ships must
  not assume a paid tier.
- **One constant per knob in code, mirrored by any config schema, with a test asserting they
  agree.** The drift test lives in [`140-llm-evals.md`](140-llm-evals.md). `sigma-intent`'s schema
  said 5 s while its code said 15 s; the schema value was never materialized, so the mismatch was
  invisible until every call aborted.
- **Derive timeouts from a recorded measurement and commit the derivation, not a comment.** A
  55 s-cold / 7 s-warm pair measured on one CPU-only host is not a portable default; copy it behind
  API Gateway's 29 s ceiling and the preflight *is* the outage. Name the platform ceiling that
  bounds the number, and assert the relationship (`preflight > cold_p99`, `perMessage < ceiling`) in
  a test — a comment cannot fail.
- **A first-call budget is not a steady-state budget.** A preflight can never hit a warm cache, so
  it gets its own longer timeout; a user-facing call fails fast to the fallback instead.

## Config plane — the rule most often over-generalized

hermes bans new env vars for non-secret config: `.env` is for credentials, behavior goes in
`config.yaml`. **That is a house narrowing of a local CLI, not a portable rule.** Acme's
`shared/config.py` states the opposite for its platform — *"On deployed Lambda: reads environment
variables set by the SAM template"* — and there env **is** the config plane; forcing a code constant
would mean a deploy to change a staging timeout.

The portable rule underneath both: **one source of truth per knob, and the deployment's own config
mechanism is the one to use.** Whether that is a YAML file or an env var is a property of the
platform, not of LLM code.

## Canonical shape

The resilience ladder, reduced from `storyboard_module.py`'s `_extract_image_prompt_resilient`:

```python
def extract_resilient(call, *, item, validate, fallback) -> Result:
    """Never raises. A malformed item must not abort the batch."""
    # --- Stage A: resilience (exceptions) → a well-formed result -------------
    try:
        result = call()
    except Exception as exc:
        logger.warning("extract failed id=%s (%s) — retrying once",
                       item.id, type(exc).__name__)
        try:
            result = call()
        except Exception:
            try:
                return fallback(item)          # deterministic, valid by construction
            except Exception:
                return Result.minimal(item)    # last resort

    # --- Stage B: validation (rule violations) → revise once, never regress --
    violations = validate(result)
    if not violations:
        return result
    try:
        revised = call(revision_note=build_revision_note(violations))
    except Exception:
        return result                          # a failed revision keeps the original
    return revised if len(validate(revised)) <= len(violations) else result
```

Three properties make it a ladder rather than a pile of `try`: every rung returns something
**valid**, each rung is **cheaper and less capable** than the one above, and Stage B can only
improve the result. The `<=` is load-bearing — with `<` a revision that fixes one violation and
introduces another would be accepted.
