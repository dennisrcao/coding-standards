```yaml
description: Optimistic updates — update every cache the mutation invalidates, give the inverse the same treatment, snapshot and roll back, and test the rollback not just the happy path
globs:
  - "apps/*/src/**/*.{ts,tsx}"
  - "apps/*/app/**/*.{ts,tsx}"
  - "**/hooks/queries/**/*.{ts,tsx}"
alwaysApply: false
```

# Optimistic updates

`025-tanstack-query.md` deliberately punts on this topic and sends you upstream. This is the part
that kept coming up anyway, so it lives here rather than in a blog post.

**An optimistic update is a promise that the UI already knows the answer.** Every rule below exists
because that promise is easy to make in one place and forget in another — and a half-kept promise
reads to the user as a bug, not as latency.

The motivating incident is `claw-calendar` PR #94 (2026-08-31), which shipped drag-a-todo-onto-the-
calendar. It optimistically updated the todo cache and not the calendar cache, and it did so for
`schedule` but not for `unschedule`. Typecheck, 411 tests and lint were green the entire time. The
owner's report was *"it didn't stick"* — the event had in fact been created in Google on the first
try, and the second drag returned `409 already scheduled`. Nothing was broken except what the screen
said.

## The four rules

### 1. Update every cache the mutation invalidates

This is the one that actually bites. If `onSettled` invalidates two query keys, then `onMutate` owes
an optimistic write to **both** — or the mutation is only half-optimistic and the slower half looks
broken.

```ts
// WRONG — the shape that shipped in PR #94
onSettled: () => {
  queryClient.invalidateQueries({ queryKey: todoKeys.all });
  queryClient.invalidateQueries({ queryKey: calendarKeys.events() }); // ← never written optimistically
}
```

The card updated instantly and the calendar grid took a full refetch to catch up, so the event
appeared about a second after the drop. **Grep your own `invalidateQueries` calls against your
`setQueryData` calls. They should name the same keys.**

`farren-base` (`coach-workout-plans/cache/mutations/useSessionMutation.ts`) is the reference here: a
session move writes the session cache *and* the affected week caches in the same `onMutate`, because
a session that exists in two week arrays — or none — is a visible ghost.

### 2. The inverse operation is part of the same feature

If you make `schedule` optimistic, `unschedule` is not a follow-up ticket. Users read the pair as one
interaction, and a fast create next to a slow delete feels more broken than two slow operations.

`farren-base` treats this as a first-class concept rather than discipline: `utils/buildReverseMutation.ts`
constructs the reversing entry from the same snapshot the forward mutation captured, so undo restores
the cache *and* fires the reverse API call. You do not need that machinery on a small surface, but you
do need both directions written at the same time.

### 3. Snapshot, mutate, roll back — in that order

The canonical shape, as implemented in `collaborative-learning`
(`src/hooks/document-comment-hooks.ts`):

```ts
onMutate: async (vars) => {
  await queryClient.cancelQueries({ queryKey });   // in flight refetches would clobber the write
  const rollback = queryClient.getQueryData(queryKey);   // snapshot BEFORE touching anything
  queryClient.setQueryData(queryKey, next);
  return { rollback, queryKey };                   // hand it to onError
},
onError: (_err, _vars, ctx) => {
  ctx?.queryKey && ctx?.rollback && queryClient.setQueryData(ctx.queryKey, ctx.rollback);
},
onSettled: () => queryClient.invalidateQueries({ queryKey }),
```

Three things that are easy to skip and all matter:

- **`cancelQueries` first.** An in-flight refetch that resolves after your `setQueryData` overwrites
  it with stale server data, and the bug is intermittent and timing-dependent.
- **Snapshot before mutating**, and return it as context. Recomputing the previous value in `onError`
  is not the same thing.
- **`onSettled`, not `onSuccess`.** Reconcile with the server on both outcomes.

**Placeholder ids must be unique and identifiable** — `` `pending-${uniqueId()}` ``, the
`collaborative-learning` form. A bare literal like `"pending"` (also PR #94) collides the moment two
optimistic rows exist at once and cannot be matched to its own response.

### 4. Test the rollback and the cache shape, not the happy path

The happy path is the one that already works. Both reference repos test the other two:

- `collaborative-learning/src/hooks/document-comment-hooks.test.ts` — *"should roll back optimistic
  update on error"*, asserting two `setQueryData` calls and inspecting the second.
- `farren-base/.../sessionOptimisticUpdates.test.ts` — invariants rather than outcomes: *"session
  appears in exactly one week (no ghost)"*, *"updates session in place, no duplication"*, *"removes
  source week from cache when it becomes empty"*.

That second style is the one worth copying. **Assert the shape the cache must always have**, because
the multi-cache bug in Rule 1 is invisible to a test that only checks the row you touched.

## When NOT to do this

Optimism is a claim that you can predict the server. Do not make it when you cannot:

- **Server-computed fields** — ids, timestamps, derived totals, anything ordered by the backend.
  Render the row without them rather than inventing values that will visibly change.
- **Destructive or irreversible operations.** Showing a delete as done before it is confirmed teaches
  the user to trust a state you may have to take back.
- **When the operation is already fast.** An optimistic path is real code with a real rollback branch.
  Under roughly 200ms it buys nothing and adds a failure mode.
- **Anything with a server-side guard you are not replicating.** PR #94's schedule route rejects an
  already-scheduled todo with a `409`; an optimistic path that does not know that rule shows success
  and then silently reverts.

## Before you call it done

- [ ] Every key in `invalidateQueries` also appears in `setQueryData`.
- [ ] The inverse operation is optimistic too.
- [ ] `cancelQueries` → snapshot → `setQueryData`, rollback in `onError`, reconcile in `onSettled`.
- [ ] Placeholder ids are unique and prefixed, not literals.
- [ ] A test forces the error path and asserts the rollback.
- [ ] A test asserts the cache-shape invariant across every cache you touched.
- [ ] You loaded the page. Every failure in the motivating incident passed typecheck, lint and the
      full unit suite while the feature was broken on screen.

## Sources

- `collaborative-learning` (`~/Desktop/Research-Repos/collaborative-learning`) — the minimal correct
  shape, and the rollback test.
- `farren-base` (NAS `SOFTWARE/00_Code-Backups/farren-base/.../coach-workout-plans/cache/mutations/`)
  — multi-cache consistency, reverse mutations as a first-class concept, invariant-style tests.
- `claw-calendar` PR #94 — every anti-pattern named above, committed by someone who knew better in
  the abstract.
