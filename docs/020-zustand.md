```yaml
description: Zustand store pattern — selector-first, actions namespace, no persist middleware, no whole-store subscribe, useShallow for object selectors
globs:
  - "apps/*/src/stores/**/*.{ts,tsx}"
  - "apps/*/src/lib/*-store.ts"
  - "src/stores/**/*.{ts,tsx}"
  - "**/*-store.ts"
alwaysApply: false
```

# Zustand (client state)

Applies wherever stores live — `src/stores/`, or `src/lib/*-store.ts`. **Zustand holds client state
only**; see *State ownership* below for the boundary.

**Upstream source of truth:** TkDodo's [*Working with Zustand*](https://tkdodo.eu/blog/working-with-zustand)
(2022-11-20). Precedence is **three-way** — "the post wins" is only true of the first third of this file:

| This file is… | Precedence |
|---|---|
| **derived from the post** — private `create()`, `actions` namespace, atomic selectors, events-not-setters, one store per domain, no whole-store subscribe | the post wins; a disagreement here is a bug in *this* file |
| **deliberately narrower than the post** — the middleware position below | the post is permissive (*"middlewares … are totally optional"*, immer allowed outright). We narrow on purpose; each narrowing states its own reason and does not defer upward |
| **downstream of the post** — v5 `useShallow`, staleness guards, persistence, state ownership | upstream is silent or **stale**. The post predates Zustand v5 and still recommends the `zustand/shallow` second argument that v5 **removed** — following it there ships broken code |

## Do

- **Keep `create()` private** — don't export the hook `create` returns. Export named selector hooks,
  an actions hook, and a `getXxxStore()` helper instead. Upstream, under *Only export custom hooks*:
  *"not exported, so that no one can subscribe to the entire store."*
- **`actions` namespace** — put every mutation in `state.actions.{…}`. Upstream, under *Separate
  Actions from State*: *"As actions never change, it doesn't matter that we subscribe to 'all of
  them'. The actions object can be seen as a single atomic piece."* That stability is what makes
  `useXxxActions()` free, and it's why the namespace is the ergonomic path rather than a ceremony.
- **Atomic selectors** — one exported hook per piece of state, or a tight slice. Prefer primitives.
  Use a hook factory when a selector needs a parameter (`useShotsForSession(id)`).
- **`useXxxActions()` in components** that only dispatch — one stable subscription, zero re-renders.
- **`getXxxStore()` for non-React code** — `export const getXxxStore = () => useXxxStore.getState()`.
- **Compute in the selector.** Don't call instance/getter methods inside it — a returned function
  reference breaks equality and re-renders every time.
- **Model actions as events, not setters** — `markRetouched(imageId)` over
  `setRetouched(imageId, true)`. Logic belongs in the store, not scattered across components.
- **One store per domain.** Keep them small. When a store outgrows its domain, split it rather than
  letting it become the app's god object.

## Don't

- **`useStore()` with no argument, or destructuring the whole store.** Both subscribe to every field.
- **`persist` middleware — hard ban.** The manual pattern below is deliberate: it guards against blob
  URLs that don't survive a refresh, partially-written state, and quota errors `persist` swallows.
- **`immer`, `devtools`, `subscribeWithSelector` — prefer the plain shape; name your reason in the
  PR.** This is a *house narrowing, not upstream doctrine* — the post calls middlewares "totally
  optional" and permits immer outright. The reason is uniformity: every store in every repo reads as
  the canonical shape at the bottom of this file, with no per-repo middleware stack to learn. That is
  a weaker reason than `persist`'s, so the bar for an exception is correspondingly lower —
  `devtools` in particular carries no production cost, and "I was debugging a state bug" is a
  sufficient PR note.
- **`getState()` inside a render body, `useMemo`, or as a `useEffect` dependency.** It captures a
  frozen snapshot and won't update when state changes. Event handlers, modules, and async callbacks
  only. **One exception, under a server-render test harness** — see *The first-paint fallback* below.
  It is narrow, and it is not a licence to reach for `getState()` in render generally.
- **Treat `getState()` + `await` as current.** The value is a snapshot; it may be stale by the time
  the promise resolves. Re-read after the await or design so it can't matter.

## Selectors that return new references (Zustand v5)

v5 removed the `equalityFn` second argument. Any selector returning a **fresh object or array** —
`.map`, `.filter`, a `.find` that builds a sub-object, or `{ a: s.a, b: s.b }` — now re-renders on
every state change unless you opt in:

```ts
import { useShallow } from 'zustand/react/shallow';
const { a, b } = useStore(useShallow((s) => ({ a: s.a, b: s.b })));
```

**Stable sentinels for empty collections.** Returning a literal `[]` is a new reference every call —
a re-render loop wearing a disguise:

```ts
const NO_SHOTS: readonly Shot[] = [];
export const useShotsForSession = (id: string | null) =>
  useShotlistStore((s) => (id ? s.bySession[id]?.shots ?? NO_SHOTS : NO_SHOTS));
```

**Extract at three.** If the same inline selector body appears in 3+ files, it becomes a named hook
in the store file. (With `create()` private this rarely arises — it's the rule for repos that have
taken the documented divergence below.)

## The first-paint fallback (Zustand v5 + `renderToString`)

v5 changed more than `equalityFn`. It also changed which state a selector reads during a **server**
render — `zustand/react.js`:

```js
const slice = React.useSyncExternalStore(
  api.subscribe,
  () => selector(api.getState()),
  () => selector(api.getInitialState()),   // ← the server snapshot, v5
);
```

v4 passed `api.getServerState || api.getState` there. v5 passes **`getInitialState`** — the state the
store was *created* with. So under `renderToString` / `renderToStaticMarkup`, a selector returns the
store's initial state while `getState()` returns the live one. They genuinely disagree, and the
`getState()` read is the correct one.

This matters to any repo whose page tests seed a store and then render to a string, which is a common
shape — the store is populated after module init, so every selector in the tree reads empty and the
page renders its empty state.

**The sanctioned form**, where it is needed:

```ts
const storeShots = useShotsForSession(sessionId);          // live in the browser
const shots = React.useMemo(
  () =>
    storeShots.length > 0 || !sessionId
      ? storeShots
      : (useShotlistStore.getState().bySession[sessionId]?.shots ?? storeShots),
  [storeShots, sessionId],
);
```

Rules for it:

- **Both branches must read the same slice.** The fallback is a different *snapshot* of one value,
  never a second source of truth.
- **Put it behind one named hook.** Hand-copying it per page multiplies a subtle exception and makes
  it read as drift; a reviewer then deletes it and loses the suite. One helper, one comment, one
  place to revisit.
- **Say why in a comment, and name `getInitialState`.** "SSR / first paint" alone does not survive
  review — it reads as cargo cult, and a reader who greps the app for `hydrateRoot` finds nothing.
- **Revisit when the harness changes.** If the page tests move to a DOM renderer (`jsdom` +
  `@testing-library/react`), this exception dies with them. Delete it then.

Only the harness earns this. `getState()` in a `useMemo` for any other reason is still the Don't
above: a memo cannot list store state in its dependency array, so nothing can invalidate it.

## Async actions must guard against staleness

An async store action (`load*`, `fetch*`) that writes results back unguarded will leak one request's
data into another's view — a fast A → B → A switch is enough:

```ts
async loadForProject(projectId) {
  const data = await fetchThings(projectId);
  if (get().loadedForProjectId !== projectId) return;   // ← the guard
  set({ things: data, loadedForProjectId: projectId });
}
```

Prefer `AbortController` where the underlying fetch is cancellable. **When per-action guards stop
being enough, that's the signal to move that data to a real server-state layer** — see
`025-tanstack-query.md` → *Migrating a hand-rolled fetch*.

## Persistence (manual `localStorage`)

- **Persist on change with a top-level subscriber**, not inside setters — a `persistOnChange(store,
  select, persist)` helper that diffs one slice by identity. This decouples persistence from every
  mutation site. Yes — this is `subscribeWithSelector`'s job, hand-rolled. Deliberate: the helper is
  ordinary repo code, so the exclusion list and the try/catch below sit *next to* it and get read in
  review, rather than disappearing into middleware config. Trading four lines for that is the whole
  of the argument; see the middleware bullet above.
- **Wrap every `localStorage` call in try/catch and log the failure**:
  `console.warn("[persist] failed to write app:foo", err)`. **Bare `catch {}` is forbidden** — quota
  and serialization failures must be visible.
- **Document what is deliberately not persisted, and why.** Blob URLs, derived data, and anything
  re-fetched on load are usually exclusions; an undocumented exclusion reads as a bug.

## State ownership

There are **three** kinds of state. Zustand owns two of them. **This table is the canonical copy** —
`025-tanstack-query.md` links here rather than restating it.

| Kind | Owner | Example |
|---|---|---|
| **Server cache** | TanStack Query, or a reactive backend's own hooks | a list you re-fetch and can discard |
| **Local document** | **Zustand** + explicit persistence | shots, picks, fragments — what the user is *editing*, which must survive reload |
| **Ephemeral UI** | **Zustand** | modal open, selected tab, session handles |

- **Fetching over HTTP** → TanStack Query, **in a repo that has adopted it**. Adoption is a per-repo
  call, not a policy handed down here — see `025-tanstack-query.md`. Until a repo makes that call, a
  store-held fetch is tolerated as debt (below), not a violation.
- **Reactive backend** (Convex, Firebase, Replicache) → its subscription hooks *are* the server-state
  layer. Don't stack a query library on top, and don't mirror its data into a store. `~/Desktop/studio`
  is the worked example: Convex `useQuery`/`useMutation`, no TanStack Query, no in-memory mirror.

**Don't hand-roll a cache in Zustand** — no `loadSeq` tokens, no TTL maps in front of a fetch.
Storing a fetched value in a store while a repo has no server-state layer is tolerated *as debt*.

**But a local document is not a cache.** Edited state with local authority, optimistic writes, and
reconciliation rules belongs in Zustand permanently — behind `useQuery` a background refetch could
overwrite unsaved work. The anti-cache rule targets caches masquerading as stores, not documents.

## Documented divergence

A repo may diverge from a rule here **if it writes down which rule, and why, in its own
`AGENTS.md` / `CLAUDE.md`** — with a threshold for revisiting. Silent divergence is drift; explained
divergence is a local decision.

The worked example is Acme's `apps/studio/AGENTS.md`, which exports its store hooks and skips the
`actions` namespace, arguing that individually-selected actions already have stable identities at its
current scale, and naming the condition that would change the answer. That is the right shape for an
exception — and it is still an exception: this file states the upstream rule.

## Canonical shape

```typescript
interface MyState {
  count: number;
  name: string | null;
  actions: {
    increment: () => void;
    setName: (name: string) => void;
  };
}

// Not exported — nobody can subscribe to the whole store.
const useMyStore = create<MyState>((set) => ({
  count: 0,
  name: null,
  actions: {
    increment: () => set((s) => ({ count: s.count + 1 })),
    setName: (name) => set({ name }),
  },
}));

export const useCount = () => useMyStore((s) => s.count);
export const useName = () => useMyStore((s) => s.name);
export const useMyActions = () => useMyStore((s) => s.actions);   // stable; never re-renders
export const getMyStore = () => useMyStore.getState();            // non-React reads only
```

## Cross-check revisions

- **2026-08-06** — Cross-checked against the declared upstream (TkDodo, *Working with Zustand*,
  2022-11-20) and against a two-agent critique of this file and `025`. Both attributed quotes verified
  verbatim. Four corrections adopted:
  - **Precedence is now three-way.** The old single line ("the post wins and this file is the bug")
    was wrong twice: the post predates Zustand v5 and still recommends the `zustand/shallow` second
    argument v5 removed, so it would have overridden the correct v5 section; and it gave no vocabulary
    for a deliberate house narrowing, which made the middleware ban read as a self-declared bug.
  - **Middleware split.** `persist` keeps its hard ban and its stated reason. `immer` / `devtools` /
    `subscribeWithSelector` are demoted to a preference and now carry their own (weaker, honest)
    reason — the post permits all three, so the old blanket ban had no upstream basis.
  - **The `subscribeWithSelector` circularity is named.** The Persistence section prescribes exactly
    what that middleware does; it now says so and says why the hand-rolled version is preferred.
  - **"Fetching over HTTP → TanStack Query" is now conditional on adoption**, matching `025`, which
    states adoption is a per-repo call. The unconditional form contradicted it.
  - The state-ownership table is marked canonical; `025`'s duplicate copy (which had already drifted
    in three cells) was replaced with a link, per `README.md` "cross-link rather than restate".
  - *Rejected:* narrowing `025`'s globs to exclude `*-store.ts` — that would strip "no server state
    cached in Zustand" from the exact files it targets, and globs are rewritten per repo on adoption
    anyway. *Deferred:* a house `staleTime` floor number in `025` — needs a real call, not a default.

- **2026-08-29** — Added *The first-paint fallback*. Found by acting on a code review that flagged
  four `getState()`-in-`useMemo` sites in Acme's `apps/studio` as violations of the Don't above:
  deleting them cost **35 tests across 4 files** against a 2997-pass baseline. The rule was right in
  general and wrong there, and this file gave a reader no way to tell the difference — it is strong
  on v5's `equalityFn` removal but never mentioned that v5 also moved the server snapshot to
  `getInitialState`. The review's own first pass reached the opposite (wrong) conclusion by reasoning
  from **v4**'s `getServerState || getState`, which is the trap this section exists to close.
