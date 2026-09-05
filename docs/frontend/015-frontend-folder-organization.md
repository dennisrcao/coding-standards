```yaml
description: Frontend folder structure, domain slicing, hook placement, and the reusable-component bucket across React/SPA and Next.js App Router codebases.
globs:
  - "apps/*/src/**/*.{ts,tsx}"
  - "src/**/*.{ts,tsx}"
  - "apps/*/app/**/*.{ts,tsx}"
  - "apps/*/components/**/*.{ts,tsx}"
  - "apps/*/hooks/**/*.{ts,tsx}"
alwaysApply: false
```

# Frontend folder organization & hook placement

This standard establishes the canonical directory structure and module scoping rules for React/Vite
and Next.js client trees. **Lowest caller scope** decides hook placement; **technical role**
decides where server-state *factories* live — see §3 and [`025-tanstack-query.md`](025-tanstack-query.md).

Rules marked **[observed]** are ones where a long-lived production codebase was examined and
the prescription was changed to match what actually held up. §9 records what was dropped.

---

## 1. Core Principles

1. **Domain-Sliced Presentation over Technical Role Dumps:** Group components by feature domain (e.g. `campaigns/`, `session/`, `retouch/`, `library/`), never by generic technical roles (`containers/`, `screens/`, `views/`).
2. **One bucket for reusable presentation.** Exactly one folder holds components that more than one feature imports. Not two tiers, not three. See §4.
3. **Lowest-Scope Placement for Hooks:** A hook belongs in the lowest directory that contains all its callers. Do not treat `src/hooks/` as a universal dumping ground.
4. **A feature that grows owns its own structure.** Past ~12 files a feature gets internal folders rather than spilling siblings into the components root.
5. **Pure Utilities vs. Infrastructure Services:** Isolate pure stateless helper functions (`utilities/`) from network-connected services, API clients, and auth bridges (`lib/`).
6. **Isolated Engines & Plugins:** Encapsulate heavy viewport, canvas, 3D, and modular engine subsystems in dedicated feature folders or `plugins/` — but only when the traits in §5 hold.
7. **Colocated Styles & Tests:** Keep `.module.scss` and `*.test.ts(x)` directly alongside the component they belong to.

---

## 2. Canonical Directory Layout

Two shapes, same rules. Vite/SPA trees root at `src/`; Next.js App Router trees root at the app
directory and use `app/` for routing in place of `routes/`.

```
src/  (or apps/web/ for Next.js)
├── app/  |  routes/          # Routing only. Next: page.tsx, layout.tsx, route handlers.
│                             # Vite: routes.ts, content.tsx, flow-registry.ts.
│                             # Pages compose features; they do not own components.
├── components/
│   ├── _ui/                  # THE reusable bucket — every component 2+ features import. §4
│   ├── _template/            # Copy-me scaffold for a new feature. §7
│   ├── <feature-area>/       # Domain directory (session/, campaigns/, calendar/, jobs/)
│   │   ├── hooks/            # Feature-private hooks, once there are 3+
│   │   ├── components/       # Feature-private subcomponents, once the folder passes ~12 files
│   │   ├── desktop/ mobile/  # Only where platforms genuinely diverge
│   │   ├── FeaturePage.tsx   # + FeaturePage.module.scss + FeaturePage.test.tsx
│   │   └── README.md         # Required past ~20 files — contents specified in §3
│   └── <shell>/              # App chrome as ordinary named folders — app-shell/,
│                             # desktop-shell/, mobile-shell/, navbar/. Not merged, not
│                             # prefixed. §6
│
├── stores/                   # Zustand / client stores. Selectors + actions colocated.
├── hooks/                    # Cross-cutting only — 2+ unrelated features. §3
│   └── queries/              # Shared server-state hooks (subscriptions, polling)
├── api/                      # VITE/SPA ONLY. Server-state factories — not React hooks.
│   └── <resource>/           # Next.js uses lib/queries/<resource>.ts instead, since
│       ├── queries.ts        # app/api/ already means route handlers. See 025.
│       └── params.ts         # Pure URL/param builders (unit-tested, no React)
├── lib/                      # Infrastructure: API clients, auth, ws, telemetry, persistence
├── utilities/  |  utils/     # Pure stateless helpers. §5 decides the boundary, not the name.
├── plugins/                  # Registry-driven subsystems ONLY — see §5
├── types/
├── styles/                   # _tokens.scss, _mixins.scss, root.scss
└── assets/
```

Server-state factories are required wherever [`025-tanstack-query.md`](025-tanstack-query.md) is
adopted, but the directory differs by tree shape: **Vite/SPA** uses a top-level `api/<resource>/`;
**Next.js App Router** uses `lib/queries/<resource>.ts`, because `app/api/` already means route
handlers and a second `api/` at the root reads as the same thing. Repos on the `next-rsc-fetch`
profile (which skips 025) have neither.

---

## 3. Hook Placement Hierarchy (The Lowest-Scope Rule)

Hooks must be organized by **scope**, not dumped into a single flat directory:

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Feature-Private Hooks (1 caller or local to 1 feature)   │
│    └── Colocate or feature/hooks/                           │
├─────────────────────────────────────────────────────────────┤
│ 2. Area-Shared / Shell Composer Hooks                       │
│    └── the shell folder's hooks/, or parent feature hooks/   │
├─────────────────────────────────────────────────────────────┤
│ 3. Shared server-state hooks (Query + side effects)         │
│    └── hooks/queries/ when 2+ features consume it;          │
│        else stay in feature/hooks/ (lowest scope wins)      │
├─────────────────────────────────────────────────────────────┤
│ 4. App-Wide Cross-Cutting Hooks (2+ unrelated top domains)  │
│    └── hooks/ — UI/session only, not Query factories        │
├─────────────────────────────────────────────────────────────┤
│ 5. Store Selector & Action Hooks                            │
│    └── Colocated in the Zustand store file (stores/*)       │
└─────────────────────────────────────────────────────────────┘
```

**TanStack Query is not a hook file by default.** `queryOptions()` factories live under
`api/<resource>/queries.ts` (Vite/SPA) or `lib/queries/<resource>.ts` (Next.js App Router) — see
§2 for why the directory differs. Call sites use `useQuery({ ...factory })`
directly. Custom hooks are only for shared *logic* — Realtime invalidation, kiosk polling, reading
router/context — per [`025-tanstack-query.md`](025-tanstack-query.md).

### The Promotion Rules

Code moves **up** only on evidence, never in anticipation.

| Trigger | Action |
|---|---|
| Component imported by a **2nd feature** | Move to `components/_ui/` |
| Single-caller hook | Colocate next to the component (`components/invoices/use-line-scroll.ts`) |
| Feature accumulates **3+ hooks** | Create `<feature>/hooks/` |
| Feature passes **~12 files** | Create `<feature>/components/` for its private parts |
| Feature passes **~20 files** | Add `<feature>/README.md` |
| Subscription/polling hook serving **2+ features** | Promote to `hooks/queries/` |
| Cross-cutting **UI** hook across unrelated domains | Promote to `hooks/` — never Query factories |
| Store selector or action | Always stays in the store file |

**Corollary:** a component used by exactly one feature belongs *inside* that feature, however
generic it looks. Genericity is not the trigger; a second caller is.

### How to count

The thresholds above are mechanical. Apply them literally.

- **"files"** means every file in the feature folder, counted recursively, including
  `.module.scss`, `.test.tsx`, and non-component `.ts`. One component is often three files, so
  ~12 files is roughly four components — this is deliberate: styles and tests are part of what
  makes a folder hard to scan.
- **"a feature"** means a top-level directory under `components/`. A subdirectory of a feature
  (`<feature>/desktop/`) is not a second feature, so two imports from inside one feature do
  **not** trigger promotion to `_ui/`.
- **"2+ features import"** counts *distinct* top-level feature directories containing at least
  one import, not the number of import statements.
- Shell directories count as features for this purpose — chrome importing a component is a real
  second caller.
- Thresholds prefixed `~` are guidance, not gates; a folder at 13 files does not fail review.
  Fixed numbers (`2+`, `3+`) are exact.

### What a feature `README.md` must contain

Four sections, nothing else. It exists so the next reader does not have to infer the folder's
shape from its filenames:

1. **What this feature is** — one or two sentences, in domain terms.
2. **Entry points** — which files the rest of the app imports, and from where. Everything else
   in the folder is private.
3. **State** — which stores, query keys, or context this feature reads and writes.
4. **Anything structurally surprising** — a platform split, a legacy file kept deliberately, a
   dependency that looks wrong but is not.

Do not restate this standard in it, and do not list every file — that list goes stale in a week.

**[observed]** At scale, a feature folder that recurses — owning its own `components/`,
`hooks/`, `models/`, `utilities/` and `README.md` — is what keeps a tree navigable. The
alternative is dozens of flat siblings and a components root nobody can scan.

---

## 4. One reusable bucket, named `_ui/`

**Rule: a component imported by 2+ features lives in `components/_ui/`. There is no second tier.**

**[observed]** This replaces an earlier prescription of `ui/` (domain-agnostic primitives) plus
`shared/` (presentational widgets). Where that two-tier split has run for years, it reliably
produces three folders instead of two:

| Folder | Typical outcome |
|---|---|
| `ui/` | Withers — a handful of files, sometimes one |
| `shared/` | Fills with domain-specific widgets, contradicting its own definition |
| a third folder | Accumulates the actual primitives — dialogs, icon buttons, toggles, alerts |

The third folder is usually named `utilities/` or `common/`, which then collides with the
pure-helper folder one level up.

Nobody decided that. It is what a "primitive vs. widget" distinction degrades into when many
people apply it over years: the boundary is not self-evident at the moment you create a file, so
it gets guessed, and the guesses diverge. One bucket has one failure mode — it gets large — and
that is visible and fixable. Split later along a line the code has revealed, not one predicted up
front.

**Never name a component folder `utilities/` or `utils/`.** Those names are reserved for pure
functions (§5).

---

## 5. `utilities/` vs. `lib/`, and what counts as a plugin

### The purity boundary

| Dimension | `utilities/` (or `utils/`) | `lib/` |
|---|---|---|
| **Purity** | 100% pure, stateless functions | May hold state, singletons, network connections |
| **Dependencies** | Zero external APIs, zero DOM state | Talks to APIs, DBs, WebSockets, LocalStorage |
| **Testing** | Simple unit tests (`input -> output`) | Mocked network/integration tests |
| **Examples** | `string-utils.ts`, `math-utils.ts`, `url-utils.ts`, `color-utils.ts` | `api-client.ts`, `auth-client.ts`, `persist-utils.ts`, `ws-client.ts` |

**If a file needs a mock to test, it belongs in `lib/`.** Pick one folder name per repo and keep it.

### What qualifies as a plugin

`plugins/` is warranted only for genuinely pluggable subsystems. **All four traits must hold:**

| Trait | What it looks like in practice |
|---|---|
| **Satisfies a contract** | A registration call taking the type, its model, its component and its assets — e.g. `registerContentInfo({type, modelClass, defaultContent})` + `registerComponentInfo({type, Component, Icon})` |
| **Registers itself** | The app never imports the component; a central registry maps a type *string* to a dynamic import |
| **Code-split** | A dynamic `import()` with its own chunk — loaded on demand, absent from the main bundle |
| **Instantiated from data** | Which plugins exist comes from content/config at runtime, not from developer code |

The last trait is the deciding test. **A feature is named by the app; a plugin is discovered by
it.** If a new one can be added without editing app code, it is a plugin. If the shell has to
learn its name, it is a feature in a folder — a static `activeId === "x" && <X/>` dispatch chain
is a shell, not a registry.

Structure when the traits hold:

```
plugins/<name>/
├── <name>-registration.ts    # the only entry point the app knows about
├── components/  hooks/  models/  utilities/  assets/
└── README.md
plugins/starter/              # copy-me template for a new plugin
```

**Do not create `plugins/` speculatively.** A folder of statically imported features named
`plugins/` is a lie the tree tells every future reader.

---

## 6. The underscore prefix

**Rule: `_` prefixes folders that are not a feature — `_ui/`, `_template/`. Nothing else.**

The prefix exists because of [`001-repository-rules.md`](../general/001-repository-rules.md), which
pins the editor to `sortOrder: mixed` — files and folders interleaved in one alphabetical list.
Under the folders-first default, folders group at the top anyway and `_` is cosmetic. Under
`mixed` they do not, so `_` is the only thing that lifts a folder above the features. **The two
standards are coupled: adopt `mixed` and the prefix becomes load-bearing.**

Keep the set tiny. Two prefixed folders read as "not a feature"; eight read as noise and the sort
order stops meaning anything.

### `_shell/` is not one of them

**[evidence]** An earlier version of this standard prescribed merging app chrome into
`components/_shell/`. Dropped. Codebases many times larger than the ones this standard governs
carry no shell folder at all — chrome sits as flat files at the components root (`app.tsx`,
`app-content.tsx`, `app-header.ts`) with `navigation/`, `toolbar/`, `workspace/` as ordinary
named folders, and nothing suffers. Where a repo already has platform-split chrome such as
`desktop-shell/` and `mobile-shell/`, those already name themselves; collapsing them into one
folder loses that distinction to gain a sort position the prefix does not need.

Shell folders keep their own `hooks/` under tier 2 of §3.

---

## 7. Enforcement

A standard nothing checks is a standard that drifts.

1. **Structure lint.** Adopt `dependency-cruiser` — a committed `.dependency-cruiser.js` plus
   `npx depcruise <src root>` in CI. Minimum viable ruleset:
   - no route/page file importing another feature's internals
   - no feature importing another feature's private `components/` or `hooks/`
   - no `utilities/**` importing from `lib/**` (enforces §5)
2. **A starter template.** **[observed]** Long-lived codebases that stay consistent keep a
   copy-me folder for new features. Keep `components/_template/` — convention by scaffold
   outlives convention by document.
3. **This document is the only copy.** Repos adopt it per
   [`../README.md`](../README.md) — copy whole, rewrite globs, record in `standards.lock.yaml`.
   Repos do not restate it in local docs.

---

## 8. Migration & Refactoring Policy (Avoiding the `v2/` Trap)

When redesigning or rewriting a frontend surface:

1. **Do not create permanent `v2/` parallel directory hierarchies.**
   - Temporary namespaces (`components/v2/`) create split-brain codebases, duplicate primitives, and hardcoded linter rules that anchor debt.
2. **Quarantine legacy code instead:**
   - Move deprecated files into `components/v1/delete-candidates/` or `components/v1/unported-features/`.
   - Keep the modern code as the canonical root structure (`components/<feature>/`).
3. **Invert tooling rules before directory promotion:**
   - Update ESLint globs, SCSS linters, and Vite `loadPaths` *before* moving directories so CI never breaks on intermediate states.
4. **SCSS Path Independence:**
   - Use bare imports (`@use "tokens" as *;`) via build-tool include paths (`loadPaths`) rather than deep relative imports (`@use "../../../styles/tokens"`), so file moves don't break stylesheet resolution.

---

## 9. Deliberately rejected

Recorded so they are not re-proposed.

| Rejected | Why |
|---|---|
| `ui/` + `shared/` as separate tiers | Degenerates into three folders wherever it runs long enough (§4) |
| `_shell/` as a merged chrome folder | Much larger codebases carry no shell folder at all; platform-split chrome already names itself (§6) |
| Naming a component folder `utilities/` | Collides with the pure-helper folder of the same name (§4, §5) |
| Speculative `plugins/` | Four traits in §5 must hold first; otherwise it is a folder of features under a misleading name |
| kebab-case component files as a mandate | Component file casing follows the repo's existing convention. A whole-tree rename buys consistency with a document and nothing else |
