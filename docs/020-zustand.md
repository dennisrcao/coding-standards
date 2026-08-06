```yaml
description: Zustand store pattern — selector-first, actions namespace, no middleware, no whole-store subscribe, useShallow for object selectors
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

**Upstream source of truth:** TkDodo's [*Working with Zustand*](https://tkdodo.eu/blog/working-with-zustand).
Where this file and that post disagree, the post wins and this file is the bug.

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
- **Middleware — `persist`, `immer`, `devtools`, `subscribeWithSelector`.** The manual patterns below
  are deliberate: they guard against blob URLs that don't survive a refresh, partially-written state,
  and quota errors that `persist` swallows. If you think you need middleware, say why in the PR.
- **`getState()` inside a render body, `useMemo`, or as a `useEffect` dependency.** It captures a
  frozen snapshot and won't update when state changes. Event handlers, modules, and async callbacks
  only.
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
  mutation site.
- **Wrap every `localStorage` call in try/catch and log the failure**:
  `console.warn("[persist] failed to write app:foo", err)`. **Bare `catch {}` is forbidden** — quota
  and serialization failures must be visible.
- **Document what is deliberately not persisted, and why.** Blob URLs, derived data, and anything
  re-fetched on load are usually exclusions; an undocumented exclusion reads as a bug.

## State ownership

There are **three** kinds of state. Zustand owns two of them.

| Kind | Owner | Example |
|---|---|---|
| **Server cache** | TanStack Query, or a reactive backend's own hooks | a list you re-fetch and can discard |
| **Local document** | **Zustand** + explicit persistence | shots, picks, fragments — what the user is *editing*, which must survive reload |
| **Ephemeral UI** | **Zustand** | modal open, selected tab, session handles |

- **Fetching over HTTP** → TanStack Query. See `025-tanstack-query.md`.
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
