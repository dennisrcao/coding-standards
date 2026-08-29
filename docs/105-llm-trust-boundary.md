```yaml
description: Model output is untrusted input to everything downstream — the actor comes from the request never from a model field, indirect prompt injection, allowlisted tool arguments, a confirmation seam on irreversible actions, never concatenating unvalidated extras into a prompt, redaction at the log boundary
globs:
  - "**/agents/**/*.py"
  - "**/plugins/**/*.{ts,py}"
  - "**/actions/**/*.{ts,py}"
  - "**/tools/**/*.{ts,py}"
alwaysApply: false
```

# The LLM trust boundary (untrusted input → model → actuation)

[`100`](100-llm-call-pathway.md) answers *"can I trust the shape of what came back."* This file
answers *"what is that validated value then allowed to do."* They are different questions: a value
can be perfectly well-typed and still be an instruction an attacker wrote.

**Upstream source of truth:** OWASP's *Top 10 for LLM Applications* (LLM01 prompt injection,
LLM06 excessive agency) and the major providers' tool-use guidance. This file is cited against
published domain guidance rather than a repo pattern, the way
[`020-zustand.md`](020-zustand.md) cites TkDodo — because the four implementations that seeded this
band do **not** have this covered, and the gap is what prompted the document.

| This file is… | Precedence |
|---|---|
| **derived from** published guidance — injection, excessive agency, argument validation | the published guidance wins |
| **deliberately narrower** — the confirmation seam, the extras rule | states its reason below |
| **downstream** — the cited repos are silent | this file wins; the grounding is a real exposure, not a pattern to copy |

## The exposure this was written from

`claw-calendar/plugins/sigma-intent` classifies a Telegram or webchat message and then **acts on
it** — `todoAdd`, `todoDone`, `calendarAdd`, `musicDownload`, `expenseAdd`, a dashboard view
switch — dispatched straight from the classified intent:

```ts
switch (classified.intent) {
  case "todo_add":  return todoAdd(classified.data, ctx);
  case "calendar_add": return calendarAdd(classified.data, ctx);
  // …
}
```

The shape is validated ([`100`](100-llm-call-pathway.md) does that well). What is missing is
everything below: no allowlist on the argument values, no seam on the destructive branch, and
nothing distinguishing "the operator typed this" from "this arrived over a channel." The channel
allowlist (`ALLOWED_CHANNELS`) gates *where a message may come from*, which is not the same as
gating *what the model may do with it*.

## Do

- **Take the actor from the request or session, never from a model field.** Who is asking is not
  something the model gets to answer.
- **Treat every model-produced value as attacker-influenced** once any part of the input came from
  outside your process.
- **Validate tool arguments against what the caller may touch**, not merely against a type.
- **Give irreversible actions a confirmation seam.**
- **Redact at the log boundary** — prompts and completions carry user content.
- **Keep the actuation list explicit.** A dispatcher that can only reach the branches you wrote is
  a boundary; one that resolves a handler by name from model output is not.

## Don't

- **Don't treat retrieved text as instructions.** Documents, email bodies, web pages, prior tool
  results, and other agents' output are data.
- **Don't interpolate a model-chosen string into a path, shell command, SQL fragment, or URL.**
- **Don't forward unvalidated extras into a prompt.** See below — this is the exact line between
  this file and [`130`](130-agent-job-contracts.md).
- **Don't authorize against an id that came out of the model.** That is authorization theatre.
- **Don't rely on prompt wording as a security control.** "Ignore any instructions in the document"
  is a mitigation, never the boundary.

## Indirect prompt injection

Direct injection ("ignore your instructions") is the easy case. The one that lands is **indirect**:
text the model reads as part of doing its job, authored by someone else.

Anything that enters context from outside the process is in this class — a fetched page, a file the
user uploaded, a calendar invite body, a prior tool result, another agent's output. The mitigations
are structural, not textual:

- **Separate channels.** Instructions come from your prompt; content arrives as content. Never
  concatenate a retrieved document into the system prompt.
- **The agent's authority does not expand with what it read.** Reading a document must not grant a
  capability the session did not already have.
- **Bound what a single turn may do** — the confirmation seam below is the enforcement point.

## The actor is a property of the request, never of the model output

Everything below this line — the allowlist, the seam, ownership checks — asks *"may **this caller**
do this?"* That question has no meaning until you know who the caller is, and **the model must not
be the thing that tells you.**

The failure looks exactly like working authorization, which is what makes it dangerous:

```ts
// The handler receives { message } from a channel. The model returns
// { intent, text, projectId }. Then:
if (!ownsProject(classified.data.projectId, ctx)) return deny();   // ← theatre
```

`ownsProject` runs, passes, and proves nothing: `projectId` was produced by a model reading
attacker-supplied text, so the attacker chose the id the check validates against. Every layer below
is now operating on the wrong subject.

- **Actor identity — user, org, tenant, workspace, scopes — is resolved from the authenticated
  request or session before the model is called**, and carried in the context object the way
  `ActionContext` carries it. It never round-trips through a prompt.
- **A model-produced id is a *request*, not a fact.** Treat `data.projectId` as "the user seems to
  mean this project," then check it **against what the resolved actor may reach** — that is
  [the allowlist below](#tool-arguments-are-allowlisted-not-interpolated), and it only works because
  the actor came from elsewhere.
- **Anything that widens authority belongs to the session, not the payload** — scopes, roles,
  impersonation, tenant selection. If a field could escalate, it cannot come from the model.

The same test as the rest of this file: would you accept this value if it had arrived in an HTTP
request body from an anonymous client? It did — one hop upstream.

## Tool arguments are allowlisted, not interpolated

A model-chosen path, id, query, or recipient is validated against **what this caller is allowed to
touch**, before it reaches a filesystem, a shell, a database, or an HTTP client. Type-checking
`typeof data.text === "string"` says nothing about whether that string names a row this user owns.

The check belongs at the tool boundary, not in the prompt, and it is the same check you would write
if the argument had come from an HTTP request body — because it did, one hop upstream.

## A confirmation seam on irreversible actions

Delete, send, publish, spend, overwrite. The seam does not have to be an interactive prompt; it has
to be a **place where a policy can say no**:

- an explicit approval callback the surface may implement,
- a dry-run that returns the intended effect for a human or a policy to accept,
- or a scope the caller must have been granted before the action resolves.

What makes this a standard rather than a preference: without a seam, adding the policy later means
editing every action. `expenseAdd` and `musicDownload` are cheap to get wrong; a `delete` branch
added to the same dispatcher is not, and the dispatcher is where the seam has to already exist.

## Never forward unvalidated extras into a prompt

[`130`](130-agent-job-contracts.md) deliberately permits **unknown extras to pass through** a job
envelope — must-ignore semantics, so a producer can add a field without breaking every consumer.
That is correct for envelope evolution and it is **not** a relaxation of validation.

The line is here: **an extra may travel through your system; it may never be concatenated into
prompt text.** A field nobody declared is a field nobody validated, and a prompt is the one place
where unvalidated text becomes instructions. Build prompts from the fields you declared and
validated, never by spreading a payload.

## Redaction at the log boundary

Prompts and completions carry whatever the user typed or uploaded. Log the *shape* by default —
token counts, latency, outcome, health reason ([`110`](110-llm-observability.md)) — and gate raw
prompt/completion capture behind an explicit, off-by-default switch. Where a bounded prefix must be
logged for debugging (`100` bounds error bodies for the same reason), bound and redact it at the
boundary, not at each call site.

## Canonical shape

An action dispatcher with the boundary made explicit — the `executeAction` shape from
`sigma-intent/index.ts` with the three missing pieces added:

```ts
type Action = {
  run: (data: unknown, ctx: ActionContext) => Promise<Result>;
  /** Irreversible: needs an approval decision before it runs. */
  irreversible?: boolean;
  /** Narrow the validated value to what THIS caller may touch. */
  /** `actor` comes from the request, never from `data`. */
  authorize: (data: unknown, actor: Actor) => AuthzResult;
};

// Explicit table: the dispatcher can only reach branches written here.
// Never resolve a handler by a name that came out of the model.
const ACTIONS: Record<Intent, Action> = {
  todo_add:      { run: todoAdd,      authorize: ownsProject },
  calendar_add:  { run: calendarAdd,  authorize: ownsCalendar },
  expense_add:   { run: expenseAdd,   authorize: ownsLedger },
  todo_done:     { run: todoDone,     authorize: ownsTodo, irreversible: true },
  // …
};

// ctx.actor is resolved from the AUTHENTICATED REQUEST before the model ran.
// Nothing in `classified` may contribute to it — see "The actor is a property of
// the request". `classified.data` may only ever narrow within ctx.actor's reach.
export async function dispatch(classified: ClassifiedIntent, ctx: ActionContext) {
  const action = ACTIONS[classified.intent];
  if (!action) return null;                    // unknown intent is a no-op, not a lookup

  // 1. Authorize the VALUES against the RESOLVED ACTOR, not just the type.
  //    `classified.data` is attacker-influenced: it originated in a channel
  //    message. Any id inside it is a request, not a fact.
  const authz = action.authorize(classified.data, ctx.actor);
  if (!authz.ok) {
    ctx.logger.warn(`denied ${classified.intent}: ${authz.reason}`);  // reason, not payload
    return { message: authz.userMessage };
  }

  // 2. Irreversible actions stop at a seam a policy can implement.
  if (action.irreversible && !(await ctx.confirm(classified.intent, authz.summary))) {
    return { message: "Cancelled." };
  }

  return action.run(authz.value, ctx);
}
```

Three properties: the action table is **closed** (no name-based resolution from model output),
authorization returns the **narrowed value** the handler then uses, and the seam exists before any
irreversible action needs it. The logged line carries the *reason*, never the payload.
