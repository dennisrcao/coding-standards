```yaml
description: Extending a conversational agent harness — the footprint ladder, plugin over local fork patch (and when upstreaming a generic widening is the right fix), session-scoped capability, registration that co-locates schema, handler and availability
globs:
  - "**/plugins/**/*.{ts,py}"
  - "**/extensions/**/*.{ts,py}"
  - "**/tools/**/*.{ts,py}"
  - "**/skills/**/SKILL.md"
alwaysApply: false
```

# Extending a conversational agent harness

**Scope, first paragraph, because getting this wrong is the failure mode:** this file governs a
**long-lived conversational agent** — one that holds a session, is offered a toolset on every call,
and is extended by plugins, skills, and commands. A **job-pipeline agent** — invoked with a payload,
runs once, returns a result — has none of these rungs and uses
[`130-agent-job-contracts.md`](130-agent-job-contracts.md) instead. A Lambda has no skill rung; a
CLI has no queue. Applying either file to the other's architecture manufactures wrong answers.

**Cited implementations:** `hermes-agent` (the footprint ladder, `tools/registry.py`, the
session-vs-env rule — all from its `AGENTS.md`), `claw-calendar/plugins/sigma-*` (the plugin route,
and the fork cost this file is written against).

| This file is… | Precedence |
|---|---|
| **derived from** hermes' footprint ladder and registration contract | hermes wins |
| **deliberately narrower** — the fork-patch/upstream distinction | states its reason below |
| **downstream** — session-vs-env is scoped here, hermes states it unconditionally | this file wins on scope: the counter-case is named |

## Do

- **Take the highest rung of the ladder that correctly solves the problem.**
- **Reach for a plugin before a core change**, and for an existing mechanism before a plugin.
- **Resolve session-scoped capability from the session.**
- **Co-locate a tool's schema, handler, and availability check** in one registration.
- **Return one typed envelope** from every handler.

## Don't

- **Don't add a core tool because it is the shortest path.** Every core tool ships on every API call
  ([`120`](120-prompt-and-context-budget.md)).
- **Don't carry a local fork patch when a plugin will do.**
- **Don't build speculative extension points.** A hook with no consumer is easy to add and hard to
  remove once plugins depend on it.
- **Don't gate a capability on a process env var when the capability belongs to the session.**
- **Don't let auto-discovery imply auto-exposure.**

## The footprint ladder

Each rung adds more permanent surface than the one above. Choose the **highest** that correctly
solves the problem:

| # | Rung | Model-schema footprint | Use when |
|---|---|---|---|
| 1 | **Extend existing code** | none | the capability is a variation of something that already exists |
| 2 | **Command + skill** | none | it manages config/state/infra expressible as commands; the agent runs the command guided by a skill |
| 3 | **Gated tool** (availability check) | none unless configured | it needs structured params/returns *and* only appears when a prerequisite exists |
| 4 | **Plugin** | none in core | third-party, niche, or user-specific; discovered at runtime |
| 5 | **MCP server** | none in core | it genuinely must be a tool but isn't fundamental; reusable by any MCP host |
| 6 | **New core tool** | permanent, every call | fundamental, near-universal, and unreachable via the rungs above |

The bar is high at rung 6 and low everywhere else. **This is not a rule against the product
growing** — new surfaces, channels, providers, and features are cheap at the edges. It is a rule
about the one place every addition is paid for on every call.

**When three or more contributions want the same *category*** (memory backends, providers,
notifiers), stop merging them one at a time: design one interface, wrap the existing built-in as its
first implementation, and turn the rest into plugins against it.

## Plugin over fork patch — and the distinction that makes it workable

**Carrying a local patch to a vendored core is a permanent tax.** The measured cost in this
codebase: the openclaw fork diverges by **9,227 files for 99 real changes**, and an entire migration
project exists to undo it. Every upstream release is a rebase against that.

**Upstreaming a generic widening is not a fork patch.** These are different acts:

| | Local special-case | Generic widening, upstreamed |
|---|---|---|
| Lives in | your fork, forever | the vendor's tree |
| Costs | a rebase every release | one review |
| Shape | "make core do *my* thing" | "make the extension surface able to express *a class of* things" |

The worked example is `sigma-intent`. It needed to invoke a capability another plugin already had;
the plugin API exposes no `getTool`/`invokeTool`, so it **built a second Google Calendar client**.
That duplication is the cost of not widening. The right fix was never a local patch pinning one
plugin to another — it was a generic registry lookup, upstreamed, that any plugin could use.

The test: **would anyone but you use this widening?** If yes, upstream it. If no, it is a
special-case and belongs in your plugin.

## Session-scoped capability

A tool that works only because of *who is on the other end of the connection* — a GUI pane, an
in-app browser, message reactions — must resolve its availability from the **session's own source**,
not from an env var on the backend process.

The client and the backend are separate machines on separate clocks. One backend may serve a locally
spawned app, an SSH connection, a plain URL + token, and a cloud session; only some of those carry
the env var the gate reads. The failure is invisible — the tool is stripped from the schema before
the model ever sees it, on the same backend whose platform hint tells the model it *is* in that GUI.

The pattern that works:

- **The toolset is the surface gate.** Keep such tools out of the default bundle and in a named
  toolset the session's platform folds in. One resolver, every topology.
- **An availability check answers reachability or user opt-in, not surface.** "Is the bridge
  wired?", "did the user enable this?" — fine. "Was I spawned by the desktop app?" — not fine.
  Availability results are typically cached **process-wide**, so a per-session answer must never
  live there: one process serves many sessions.
- **Test it with the env var absent.** That is the assertion the original gate could never pass.

**The counter-case, named:** in a job-pipeline agent the process *is* the request — there is no
session to resolve from, and capability is a property of the invocation and its IAM role. Do not
apply this rule there; it inverts into "look for a session object that does not exist."

## Registration

One call declares everything about a tool: its schema, its handler, its toolset membership, and its
availability check. Splitting these across files is how a tool ends up registered but unreachable,
or exposed without its prerequisite.

**Discovery may be automatic; exposure stays deliberate.** Auto-importing every tool module is
convenient and safe. Auto-*exposing* every discovered tool is neither — membership in a toolset is
the reviewable decision about who pays for its schema, and it should require an explicit edit.

**Every handler returns one typed envelope.** Uniform success and error shapes are what let the
dispatch boundary bound error bodies ([`120`](120-prompt-and-context-budget.md)) and what let the
model learn one result format instead of N.

## Canonical shape

A registration that co-locates all four concerns — the `registry.register()` contract:

```python
from tools.registry import registry

def check_requirements() -> bool:
    """Availability = reachability or opt-in. NEVER 'which process spawned me'.
    Results are cached process-wide, so this must not be per-session."""
    return bool(os.getenv("EXAMPLE_API_KEY"))

def example_tool(param: str, task_id: str | None = None) -> str:
    # One typed envelope, always. The dispatch boundary bounds `error` bodies.
    return json.dumps({"success": True, "data": ...})

registry.register(
    name="example_tool",
    toolset="example",              # membership, not the default bundle
    schema={
        "name": "example_tool",
        # Teaches BEHAVIOR the params cannot express. No cross-tool references:
        # the referenced tool may be absent in this session. See 120.
        "description": "…",
        "parameters": {...},
    },
    handler=lambda args, **kw: example_tool(
        param=args.get("param", ""), task_id=kw.get("task_id")
    ),
    check_fn=check_requirements,
    requires_env=["EXAMPLE_API_KEY"],
)
```

Discovery imports any module with a top-level `register()` call — **but the tool is only offered to
an agent once its name appears in a toolset.** That second step is manual on purpose: it is the
moment someone decides every session should pay for this schema.
