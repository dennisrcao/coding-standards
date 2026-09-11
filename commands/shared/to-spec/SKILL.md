---
name: to-spec
description: Turn the current conversation into a spec — no interview, just synthesis of what you've already discussed. Publishes as one parent GitHub issue on the tracker.
disable-model-invocation: true
---

This skill takes the current conversation context and codebase understanding and produces a spec (you may know this document as a PRD). Do NOT interview the user — just synthesize what you already know.

Tracker conventions live in `apps/docs/content/projects/app/docs/technical/agents/issue-tracker.md`.

## Process

1. Explore the repo to understand the current state of the codebase, if you haven't already. Use the project's domain glossary vocabulary throughout the spec, and respect any ADRs in the area you're touching.

2. Sketch out the seams at which you're going to test the feature. Existing seams should be preferred to new ones. Use the highest seam possible. If new seams are needed, propose them at the highest point you can. The fewer seams across the codebase, the better - the ideal number is one.

Check with the user that these seams match their expectations.

3. Publish the spec as **one parent GitHub issue** (template below), titled per the tracker's title convention — `[Spec] <name> — <scope>` — and apply the `ready-for-agent` label; no need for additional triage. The spec issue is ephemeral: it is the plan of record while the work is in flight and is closed when the work ships. Durable knowledge (decisions, how-it-works-today) goes to `technical/adr/` and `technical/reference/` — the spec links those, never restates them. If the grilling session produced CONTEXT.md/ADR updates, land them as their own small PR alongside.

<spec-template>

## Problem Statement

The problem that the user is facing, from the user's perspective.

## Solution

The solution to the problem, from the user's perspective.

## User Stories

A numbered list of user stories covering the feature's real surface. Each in the format:

1. As an <actor>, I want a <feature>, so that <benefit>

<user-story-example>
1. As a retoucher, I want my saved camera angle to survive a scene reload, so that I don't re-frame the shot every session
</user-story-example>

Aim for the ~5–15 stories that actually pin down behaviour and edge cases, not exhaustive enumeration. Cover the happy path plus the failure/edge cases that would otherwise get discovered mid-implementation (empty input, upstream failure, permission/role gates, cancellation).

## Implementation Decisions

A list of implementation decisions that were made. This can include:

- The modules that will be built/modified
- The interfaces of those modules that will be modified
- Technical clarifications from the developer
- Architectural decisions
- Schema changes
- API contracts
- Specific interactions

Do NOT include specific file paths or code snippets. They may end up being outdated very quickly.

Exception: if a prototype produced a snippet that encodes a decision more precisely than prose can (state machine, reducer, schema, type shape), inline it within the relevant decision and note briefly that it came from a prototype. Trim to the decision-rich parts — not a working demo, just the important bits.

## Testing Decisions

A list of testing decisions that were made. Include:

- A description of what makes a good test (only test external behavior, not implementation details)
- Which modules will be tested
- Prior art for the tests (i.e. similar types of tests in the codebase)

## Out of Scope

A description of the things that are out of scope for this spec.

## Production Verification

How we'll confirm the feature actually works in the deployed system, beyond the automated tests — a short checklist of concrete checks tied to the real deployed paths (the staging hosts per client, the api-server API, lambdas, CloudFront/S3 asset delivery, WorkOS auth), since the test suite fakes those. Each item: what to run/observe, and the expected result. Keep it runnable, not aspirational.

## Further Notes

Any further notes about the feature.

</spec-template>
