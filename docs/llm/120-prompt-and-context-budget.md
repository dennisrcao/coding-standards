```yaml
description: Everything in context is paid for on every call — shared rule fragments composed once and versioned, tool descriptions that teach behavior, no cross-tool references, bounded strings at the dispatch boundary, prompt-cache stability
globs:
  - "**/prompts*.{py,ts}"
  - "**/signatures*.py"
  - "**/schema/*.{yaml,yml}"
  - "**/tools/**/*.{ts,py}"
  - "**/*prompt*.{ts,py}"
alwaysApply: false
```

# Prompts and the context budget

One law, applied five ways: **every token in context is paid for on every call.** Not once — every
call, for the life of the conversation, multiplied by every user.

Two independent codebases arrived at the same sentence — one on tool registries (*"every model tool
we add is sent on every API call, so the bar for a new core tool is high"*), one on signature
docstrings (*"Every word in a signature docstring ships into the LLM prompt on every call."*).

| This file is… | Precedence |
|---|---|
| **derived from** the fragment-composition pattern and the bounding boundary | those patterns win |
| **deliberately narrower** — fragment versioning | states its reason below |
| **downstream / relabelled** — the ≤60-char cap and the cache rules are **house narrowings**, not law | this file wins on scope, and names each condition |

## Do

- **Author a shared rule once and compose it.** Any substrate; the rule is single-authorship.
- **Version prompt fragments**, so evals stay comparable across changes
  ([`140`](140-llm-evals.md)).
- **Write tool descriptions that teach behavior** the parameter schema cannot express.
- **Bound every string entering model context at the dispatch boundary.**
- **Keep a cached prefix byte-stable** — across turns, or across invocations.

## Don't

- **Don't paste the same rule into N prompts.** It drifts, and you pay for it N times.
- **Don't restate the parameter schema in prose.** The schema already says the shape.
- **Don't name another tool inside a schema description.** It may not exist in this session.
- **Don't put an `offset`/`limit` escape hatch on content the model must read in full.**
- **Don't rebuild a system prompt mid-conversation** where prefix caching applies.

## Shared fragments, authored once

Three substrates are all correct — pick by what the surrounding code already is:

| Substrate | Example | Best when |
|---|---|---|
| Module constants composed with f-strings | `_ROLE`, `_OUTPUT_FORMAT`, `_DOMAIN_VOCAB` in `signatures.py` | prompts are typed alongside code and change with it |
| Fragment files loaded and assembled | `schema/{roles,context,instructions,output_format}.yaml` → assembler | prompts are edited by more people than the code, or shipped separately |
| One prompt constant per call site | `CLASSIFIER_PROMPT` in a plugin | there is genuinely one prompt |

What is banned is the same sentence appearing in three prompts. When a rule changes, it changes
once. Both real implementations converge on the same four categories — **role, context,
instructions, output format** — which is a good default decomposition.

**Fragments carry a version id.** Prompt text is the largest uncontrolled input to output quality,
and [`140`](140-llm-evals.md)'s eval results are meaningless if you cannot say which prompt produced
them. A monotonic id on the fragment set, recorded in the eval run, is the minimum.

## Tool descriptions teach behavior

The description is prompt surface, and it is the model's only documentation. The rule is **not** a
length cap:

> the description teaches behavior, not structure the params already define.

A well-written todo tool description runs several hundred characters and spends them on things the
schema cannot express: when to reach for it, that list order is priority, that only one item may be
in-progress, that completion is marked after verification and never on intent. None of that is
derivable from `{ todos: [{ id, content, status }] }`.

**The ≤60-character cap is a different rule with a different subject.** It applies to **SKILL.md
frontmatter descriptions** — a listing line, where many are loaded at once and each one dilutes
attention across the set. Applying it to a tool schema is a category error: truncating a tool
description into ambiguity costs more in wrong calls and retries than the tokens it saves.

**No cross-tool references in a schema description.** `browser_navigate` saying "prefer web_search"
is a hallucinated call waiting to happen in any session where `web_search` is disabled or its key is
missing. If a cross-reference genuinely helps, inject it at assembly time, when you know which tools
this session actually has.

## Pagination: scoped, not banned

**Content the model must read in full gets no `offset`/`limit`** — a skill, a playbook, a rubric, an
instruction file. Models read page one and proceed as if they had the rest. The hatch turns "the
agent read the procedure" into "the agent read the first third of the procedure."

**Everything else must paginate**, and this document's own budget law is why: retrieval results,
search hits, log tails, catalogs, galleries. Dumping a 2,000-row result set into context to avoid
`limit` violates the rule this file exists to state. The distinction is *instructional content* vs
*queried data*, not "tools may not have a limit parameter."

## Bounded strings at the dispatch boundary

An interpolated exception, a provider error body, or a stack trace can be arbitrarily long, and it
enters context **once per retry**, stacking. Bound it **at the boundary that dispatches tool
results**, not by convention at every call site — a convention only holds until one handler
serializes its own exception:

```python
_MAX_TOOL_ERROR_CHARS = 2048
_MAX_LOGGED_ERROR_CHARS = 8192   # logs keep more than the model sees
```

One agent harness applies this at dispatch precisely so *"no registered tool can return an
unbounded error body that stacks across retries."* The asymmetry is deliberate: the log is for a human debugging once;
the context is paid on every subsequent turn. The logging half of this is
[`110`](110-llm-observability.md).

## Prompt-cache stability — an Anthropic-family narrowing

Where the provider caches on a conversation prefix, a long-lived conversation reuses that prefix
every turn and anything that mutates it multiplies cost. The rules:

- Do not alter past context, swap toolsets, or rebuild the system prompt mid-conversation.
  Compression is the one sanctioned exception.
- A command that mutates system-prompt state (installing a skill, toggling a tool) defaults to
  **deferred invalidation** — it takes effect next session — with an opt-in flag for "now."
- Inject session-scoped additions as a **user message**, not by editing the system prompt. One common
  harness routes skill slash-commands this way for exactly this reason.
- Keep role alternation clean: no two same-role messages in a row.

**Scope — two shapes, both real.** These are properties of prefix-caching providers, chiefly the
Anthropic family, and not provider-neutral law. But a long-lived conversation is not the only shape
that benefits, and assuming so is a mistake this file made in its first draft:

- **Across turns** — a conversation reuses its prefix every turn. That is the list above.
- **Across invocations** — a *stateless* agent reuses a cached prefix between runs, inside the
  provider's cache TTL. Serverless agents that mark their system prompt
  `cache_control: {"type": "ephemeral"}` do so because consecutive invocations inside the window skip
  re-reading a large system prompt. The stability law is identical with a different unit — **the
  cached block must be byte-identical between invocations**, so nothing interpolated per request (a
  timestamp, a request id, the user's own input) may appear inside it.

What genuinely does not apply to a stateless agent is the *session* machinery — deferred
invalidation, injecting additions as a user message, role alternation — all of which presume
there is a conversation to invalidate.

**The alternation rule names its exception.** A synthetic turn is sometimes the only legal recovery
— an empty or errored tool result that leaves the conversation unable to continue. Ban the *casual*
injection of synthetic user messages mid-loop; do not ban the recovery, or you have written a rule
that makes a stuck conversation unrecoverable.

## Canonical shape

Fragments authored once, composed at the call site — YAML fragment pipeline, reduced:

```python
# shared/schema/roles.yaml, context.yaml, instructions.yaml, output_format.yaml
# hold the fragments. Each rule is written ONCE and reused across every prompt
# that needs it. lru_cache: parsed once per process, not per call.

@lru_cache(maxsize=8)
def _load(name: str) -> dict:
    for d in (_SCHEMA_DIR, _LAMBDA_DIR):        # local dev, then runtime
        f = d / f"{name}.yaml"
        if f.is_file():
            return yaml.safe_load(f.read_text())
    raise FileNotFoundError(f"Schema file not found: {name}.yaml")


def get_bbox_detection_prompt(product_name: str) -> str:
    r, f = _load("roles")["roles"], _load("output_format")["constraints"]
    return "\n\n".join([
        r["part_detector"].format(product_name=product_name),  # role
        f["json_array"].strip(),                               # output format
        f["json_example"].strip(),
        r["thoroughness"],
        f["json_only"],
    ])
```

The same law in the other substrate — module constants composed at authoring time:

```python
# Every word in a signature docstring ships into the LLM prompt on every call.
# Rules that apply to more than one signature live here so they are written
# once and composed via f-strings into each signature's __doc__.

_ROLE = "You are a domain expert for …"
_NO_PROPRIETARY_NAMES = "Never write a proprietary name as prose …"
```

Both give one editing site per rule. Neither lets a change to "no brand names" reach three prompts
and miss a fourth.
