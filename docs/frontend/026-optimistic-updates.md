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

The motivating failure mode: a drag-to-schedule mutation optimistically updated the todo cache but
not the calendar cache, and did so for `schedule` but not for `unschedule`. Typecheck, unit tests, and
lint were green. The server had already created the event on the first try; the second attempt
returned `409 already scheduled`. Nothing was broken except what the screen said — the card updated
instantly and the calendar grid lagged a full refetch behind.

## The four rules

### 1. Update every cache the mutation invalidates

This is the one that actually bites. If `onSettled` invalidates two query keys, then `onMutate` owes
an optimistic write to **both** — or the mutation is only half-optimistic and the slower half looks
broken.

```ts
// WRONG — optimistic write to one cache, invalidate two
onSettled: () => {
  queryClient.invalidateQueries({ queryKey: todoKeys.all });
  queryClient.invalidateQueries({ queryKey: calendarKeys.events() }); // ← never written optimistically
}
```

The card updated instantly and the calendar grid took a full refetch to catch up. **Grep your own
`invalidateQueries` calls against your `setQueryData` calls. They should name the same keys.**

A session-move mutation that writes the session cache *and* every affected week cache in the same
`onMutate` is the reference shape — a session that exists in two week arrays (or none) is a visible
ghost if you only touch one cache.

### 2. The inverse operation is part of the same feature

If you make `schedule` optimistic, `unschedule` is not a follow-up ticket. Users read the pair as one
interaction, and a fast create next to a slow delete feels more broken than two slow operations.

Some codebases treat reverse mutations as first-class: construct the reversing entry from the same
snapshot the forward mutation captured, so undo restores the cache *and* fires the reverse API call.
You do not need that machinery on a small surface, but you do need both directions written at the
same time.

### 3. Snapshot, mutate, roll back — in that order

The canonical shape:

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

**Placeholder ids must be unique and identifiable** — `` `pending-${uniqueId()}` ``. A bare literal
like `"pending"` collides the moment two optimistic rows exist at once and cannot be matched to its
own response.

### 4. Test the rollback and the cache shape, not the happy path

The happy path is the one that already works. Test the error path and the cross-cache invariants:

- *Roll back optimistic update on error* — assert two `setQueryData` calls and inspect the second.
- Invariant-style tests: *session appears in exactly one week (no ghost)*, *updates in place, no
  duplication*, *removes source week from cache when it becomes empty*.

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
- **Anything with a server-side guard you are not replicating.** A schedule route that rejects an
  already-scheduled item with `409`; an optimistic path that does not know that rule shows success
  and then silently reverts.

## Before you call it done

- [ ] Every key in `invalidateQueries` also appears in `setQueryData`.
- [ ] The inverse operation is optimistic too.
- [ ] `cancelQueries` → snapshot → `setQueryData`, rollback in `onError`, reconcile in `onSettled`.
- [ ] Placeholder ids are unique and prefixed, not literals.
- [ ] A test forces the error path and asserts the rollback.
- [ ] A test asserts the cache-shape invariant across every cache you touched.
- [ ] You loaded the page. The motivating failure passed typecheck, lint and the full unit suite while
      the feature was broken on screen.

## Cited implementations

Ground-truth repos that shaped this standard — not required reading for adoption:

- A minimal document-comment mutation hook with rollback test (single-cache shape).
- A multi-week session planner with multi-cache `onMutate`, reverse mutations, and invariant tests.
- A calendar scheduling PR that shipped every anti-pattern named above despite green CI.
