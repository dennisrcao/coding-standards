```yaml
description: TanStack Query v5 — queryOptions factories, staleTime tuning, broad invalidation, thin queryFns; never hand-roll fetch/loading/error
globs:
  - "apps/*/src/**/*.{ts,tsx}"
  - "apps/*/app/**/*.{ts,tsx}"
alwaysApply: false
```

# TanStack Query (server state)

**TanStack Query is the sanctioned server-state layer for HTTP fetching — in repos that adopt one.**
It is the only sanctioned option, not a mandatory one; see the adoption note below. Client state (UI
flags, selections, session handles) stays in Zustand — see `020-zustand.md`. Repos on a *reactive*
backend (Convex, Firebase) use that backend's subscription hooks instead; don't stack a query library
on top.

This standard exists because the alternative is common and expensive: dozens of hand-rolled fetch
wrappers, the same `useState(data/loading/error)` + `useEffect(cancelled)` quadruple in nearly every
screen, and server state cached in client stores behind manual sequence guards.

> **This standard governs *how* to use TanStack Query — not *whether* to adopt it.** Adoption is a
> per-codebase call — weigh read-path pain (duplicate fetches, stale UI, loading boilerplate) against
> write-path cost (mutations, optimistic updates, invalidation surface). A codebase that is mostly
> writes with heavy local document state may legitimately defer adoption. What is *not* legitimate is
> bolting the library onto one feature — adopt it with the `queryOptions` factory below, or not at all.

### Query never owns editable state

There are **three** kinds of state, not two. **The table lives in `020-zustand.md` → *State
ownership*, and is not restated here** — one copy, or the two drift. Query owns exactly one of the
three: **server cache**.

A document the user edits is not a cache of the server — it has local authority, optimistic writes,
and reconciliation rules a cache has no opinion about. Putting it behind `useQuery` means a background
refetch can silently overwrite unsaved work.

This is why "don't hand-roll the cache in Zustand" (`020-zustand.md`) is **not** an argument against
a store that owns a document. A session store holding the artifact the user is actively editing is
the **local document** kind, not the server cache.

**Upstream source of truth:** TkDodo (TanStack Query maintainer) — <https://tkdodo.eu/blog>, whose
guidance every rule below is derived from. Where this file and that blog disagree, **the blog wins
and this file is the bug** — with one qualifier: the blog spans years and **later posts supersede
earlier ones**, often without an update notice on the earlier post. The custom-hook rule below is the
live example. Check the date before treating a post as current. (Unlike `020-zustand.md`, which cites
a single 2022 post and therefore needs a full three-way precedence rule, this file tracks a maintained
blog — so "the blog wins" holds, once you read the right post.)

## Do

- **Export a `queryOptions()` factory per resource** — not a bare key factory, and not a custom hook
  per query. `queryOptions()` is the identity function at runtime but it (a) catches typos that a
  plain object silently swallows, (b) tags the key with its return type so
  `queryClient.getQueryData(opts.queryKey)` is typed with no manual generics, and (c) works in route
  loaders, prefetching, event handlers, and `useQueries` — everywhere hooks can't go.
- **Always use the object form** — `useQuery({ queryKey, queryFn })`, never the v4 positional form.
- **Set a global `staleTime` floor** in `QueryClient.defaultOptions`, then override per key-scope
  with `setQueryDefaults` or on the individual `queryOptions`. `staleTime` is the single most
  important knob; almost nobody needs to touch `gcTime`.
- **`placeholderData: (previous) => previous`** on paginated or filtered lists, or the list blanks
  on every page change.
- **Search is a `useQuery` with the term in the key** — never a `useMutation`. Re-searching a prior
  term becomes a cache hit.
- **Debounce the value feeding the key** (300 ms house default), not the fetch. Debouncing inside
  the `queryFn` still creates a cache entry per keystroke.
- **Every scope belongs in the key** — tenant, org, workspace, selected-coach. A key missing its
  scope serves one tenant's cached data to another after a switch. Correctness, not performance.
- **Gate with `enabled`** (`!authLoading`, `!!id`) — never conditional hooks.
- **Keep `queryFn` to three lines**: pure param builder → typed API client → return. Both halves are
  then testable without React.
- **Invalidate broadly by default** (see *Invalidation*).

## Don't

- **`useState(data/loading/error)` + `useEffect(cancelled)`.** Writing a cancellation flag means
  reimplementing the library.
- **Disable `refetchOnMount` / `refetchOnWindowFocus` to "reduce requests."** This is the most common
  misuse — it turns off the synchronization mechanism and you ship stale UIs. **Raise `staleTime`
  instead**; it cuts requests while keeping the safety net.
- **Wrap every query in a custom hook** — *except subscription/mutation encapsulation; see
  **Exception — custom Query hooks** below.*
- **Server state cached in Zustand** — no `loadSeq` tokens, no manual sequence guards.

### Exception — custom Query hooks

Don't wrap every query in a custom hook. The escalation is predictable and ends in broken types:
`useThing(id)` → `useThing(id, staleTime?)` → `useThing(id, options?: Partial<UseQueryOptions>)`,
at which point `data` becomes `unknown`. *"The best abstractions are not configurable."* Spread
overrides at the call site: `useQuery({ ...invoiceOptions(1), select: (i) => i.createdAt })`.
Custom hooks remain correct when they share **logic** (reading router/context, combining queries) —
not when they merely share **configuration**.

*Note:* the 2020 *Practical React Query* post says to create a custom hook "even if it's only for
wrapping one `useQuery` call", and carries no update notice. **The later posts reverse that
default** — *The Query Options API* and *Creating Query Abstractions* put `queryOptions()` first.
We follow the later guidance.

Use a custom hook when it manages **active side effects** — Realtime channels invalidating on
`postgres_changes`, WebSocket events, kiosk polling intervals — or combines query state with
mutations or derived domain lookups. Forcing bare `queryOptions` onto subscription-managing hooks
pushes connection lifecycle boilerplate onto consuming components.

**File placement** defers to [`015-frontend-folder-organization.md`](015-frontend-folder-organization.md):
one feature → `components/<feature>/hooks/`; shared across features → `hooks/queries/`. Factories
stay in `api/<resource>/queries.ts`, never in either hooks folder.

- **A hand-rolled TTL cache or in-flight dedup in front of a query.** Both are built in; two cache
  layers means two things to invalidate.
- **Prop-drill query data to avoid "duplicate fetches."** Any number of components may call the same
  query; they dedupe into one request and one cache entry. Prop-drilling to "fix" this is solving a
  problem the library already solved.
- **Inline closures in `queryFn` whose dependencies aren't all in the key.** Nothing warns you when
  they drift; you get stale cache reads that are miserable to debug.
- **Fat `queryFn`s.** A hundred lines of conditional `queryParams.append(...)` can't be tested, reused,
  or read.
- **One hook straddling two endpoints with different response shapes.** If empty query hits `/things`
  and non-empty hits `/things/search`, and only one returns `total`, the hook is hiding a backend
  inconsistency — fix the API or ship two hooks.
- **Deprecated-param mapping inside a hook.** That belongs in the API client.

## Canonical shape

```typescript
// api/exercises/queries.ts — one factory per resource. Key helpers stay plain arrays;
// leaf entries return queryOptions() so they carry queryFn + defaults + DataTag typing.
import { queryOptions } from '@tanstack/react-query';

export const exerciseQueries = {
  all: () => ['exercises'] as const,
  lists: () => [...exerciseQueries.all(), 'list'] as const,
  search: (params: SearchParams, coachId: string) =>
    queryOptions({
      queryKey: [...exerciseQueries.lists(), params, coachId] as const,
      queryFn: () => fetchJson<SearchResponse>('/exercises/search', buildSearchParams(params)),
      placeholderData: (previous) => previous,  // no blank frame between pages
      staleTime: 2 * 60 * 1000,                 // results churn as the library is edited
    }),
  detail: (id: string) =>
    queryOptions({
      queryKey: [...exerciseQueries.all(), 'detail', id] as const,
      queryFn: () => fetchJson<Exercise>(`/exercises/${id}`),
    }),
};

// api/exercises/params.ts — pure, unit-testable, no React
export function buildSearchParams(p: SearchParams): URLSearchParams { /* … */ }
```

```typescript
// Call site. Overrides are spread, not baked into a configurable wrapper.
const { data, isFetching } = useQuery({
  ...exerciseQueries.search({ query: debouncedQuery, ...filters }, coachId),
  enabled: !authLoading,
});

// The same object works everywhere hooks don't:
queryClient.prefetchQuery(exerciseQueries.detail(id));
const cached = queryClient.getQueryData(exerciseQueries.detail(id).queryKey); // typed as Exercise
```

A thin custom hook is still justified when it reads context the call site shouldn't have to —
`useSelectedCoachId()`, auth state — but it should wrap the factory, never replace it.

## Invalidation

**Invalidation is not "refetch everything."** It refetches *active* matching queries and marks the
rest stale for later, so broad invalidation is far cheaper than it sounds.

**Default to global**, which removes the entire "forgot to invalidate X" bug class:

```typescript
new QueryClient({
  mutationCache: new MutationCache({
    onSuccess: () => queryClient.invalidateQueries(),
  }),
});
```

Fine-grained mutation→query maps are the tempting anti-pattern: every new related resource means
auditing every mutation callback. Reach for scoping (`mutationKey`, or declarative `meta.invalidates`)
only when you have a measured reason.

### When to narrow invalidation

Keep the global default for greenfield apps and small surfaces — it removes the "forgot to invalidate
X" bug class. **Narrow** when you have evidence of over-invalidation: high-traffic list keys refetching
on unrelated mutations, measurable UI jank, or API rate limits. Then:

- Scope with `queryKey` prefixes or `meta.invalidates` on the mutation, not per-callback maps that
  drift from the factory.
- Record the divergence in the repo's `standards.lock.yaml` under `exceptions` (see
  [`standards.lock.yaml.example`](../../standards.lock.yaml.example)).

⚠️ `invalidateQueries` defaults to `cancelRefetch: true`, which cancels in-flight requests. Pass
`false` to piggyback on a refetch already running.

## Seeding the cache

`placeholderData` and `initialData` are not interchangeable. `initialData` is **written to the cache
and treated as fresh** — with a `staleTime` set, it can suppress the fetch entirely. `placeholderData`
is explicitly *not* cached and never suppresses a fetch. Seeding a detail view from a list row that
lacks fields the detail endpoint returns? Use `placeholderData`.

## Migrating a hand-rolled fetch

1. Move URL building into a pure `buildXxxParams()`; write its unit test first — it's where quiet
   bugs accumulate.
2. Add the `queryOptions()` factory for the resource.
3. Replace the `useState`/`useEffect` quadruple with `useQuery`. Delete the cancellation flag.
4. Delete any TTL cache or `loadSeq` guard in front of it — never keep both.
5. Confirm the scope (tenant/org/coach) is in the key before shipping.

## Further reading

<https://tkdodo.eu/blog> — the source for everything above. This standard deliberately covers only the
rules that keep coming up in practice. Go upstream for `select` and data transformation, render
optimization, error handling, Suspense/React 19, infinite queries, WebSockets,
offline/`networkMode`, forms, and testing.

**Optimistic updates now have their own standard — [`026-optimistic-updates.md`](026-optimistic-updates.md).**
They kept coming up, and the failure mode is specific enough to be worth writing down: a mutation
that optimistically updates one cache but invalidates two.

Posts worth reading in full before writing much query code: *Practical React Query*, *Effective React
Query Keys*, *The Query Options API*, *Mastering Mutations*, and *Automatic Query Invalidation after
Mutations*.
