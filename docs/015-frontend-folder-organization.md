```yaml
description: Frontend folder structure, domain slicing, and hook placement rules across React/SPA codebases.
globs:
  - "apps/*/src/**/*.{ts,tsx}"
  - "src/**/*.{ts,tsx}"
alwaysApply: false
```

# Frontend folder organization & hook placement

This standard establishes the canonical directory structure and module scoping rules for frontend SPA applications across our repositories (Acme, Studio, CLUE / collaborative-learning, Storyboard).

---

## 1. Core Principles

1. **Domain-Sliced Presentation over Technical Role Dumps:** Group components by feature domain (e.g. `campaigns/`, `session/`, `retouch/`, `library/`), never by generic technical roles (`containers/`, `screens/`, `views/`).
2. **Lowest-Scope Placement for Hooks:** A hook belongs in the lowest directory that contains all its callers. Do not treat `src/hooks/` as a universal dumping ground.
3. **Pure Utilities vs. Infrastructure Services:** Isolate pure stateless helper functions (`utilities/`) from network-connected services, API clients, and auth bridges (`lib/`).
4. **Isolated Engines & Plugins:** Encapsulate heavy viewport, canvas, 3D, and modular engine subsystems in dedicated feature folders or `plugins/`, rather than scattering them into flat UI component trees.
5. **Colocated Styles & Tests:** Keep `.module.scss` and `*.test.ts(x)` directly alongside the component they belong to.

---

## 2. Canonical `src/` Directory Layout

```
src/
├── components/               # Presentation & UI components (SCSS modules colocated)
│   ├── _shell/               # Application shell, layout framing, navigation rails, chrome
│   │   ├── hooks/            # Shell-composer orchestration hooks
│   │   ├── app-shell.tsx
│   │   ├── page-header.tsx
│   │   └── page-frame.tsx
│   ├── <feature-area>/       # Domain feature directory (e.g. session/, campaigns/, library/)
│   │   ├── hooks/            # Feature-private orchestration hooks (when 3+ shared hooks)
│   │   ├── FeaturePage.tsx
│   │   ├── FeaturePage.module.scss
│   │   └── FeaturePage.test.tsx
│   ├── ui/                   # Reusable, domain-agnostic UI primitives (Button, Dialog, Menu, Tag)
│   ├── shared/               # Reusable presentational widgets (LoadingState, ImagePlaceholder)
│   └── redirects/            # Legacy route redirect resolvers
│
├── routes/                   # Application routing and view dispatching
│   ├── routes.ts             # Central route path registry & URL matchers
│   ├── content.tsx           # Route content-switch dispatcher
│   └── flow-registry.ts      # Workspace flow registration
│
├── stores/                   # Domain state management (Zustand / client stores)
│   ├── store.ts              # Core domain store
│   ├── auth-store.ts         # Authentication & tenancy
│   └── <domain>-store.ts     # Domain-scoped slices
│
├── hooks/                    # True cross-cutting, app-wide React hooks only
│   ├── use-theme.ts
│   ├── use-network-status.ts
│   └── use-keyboard-shortcuts.ts
│
├── lib/                      # Infrastructure, API clients, DB connectors, auth, telemetry
│   ├── api-client.ts         # REST / GraphQL client
│   ├── auth-service.ts       # Auth tokens & handshake logic
│   ├── ws/                   # WebSocket listeners & dispatchers
│   └── logger.ts             # Telemetry & error logging
│
├── utilities/                # Pure stateless helpers (math, strings, URLs, dates, colors)
│   ├── string-utils.ts       # Formatting, truncation, slugs
│   ├── url-utils.ts          # Query param builders & URL parsers
│   ├── color-utils.ts        # Color space conversion & contrast
│   ├── hot-keys.ts           # Keyboard event normalization
│   └── math-utils.ts         # Clamping, interpolation, geometry
│
├── plugins/                  # Modular, heavy rendering engines & pluggable subsystems
│   ├── canvas-2d/            # 2D infinite canvas / Fabric.js / SVG engines
│   └── viewport-3d/          # WebGL / Three.js 3D viewports & gizmos
│
├── types/                    # Domain models & central TypeScript declarations
│   ├── domain.ts             # Business entity contracts
│   └── api-schema.ts         # Generated API / OpenAPI interfaces
│
├── styles/                   # Global design tokens, mixins, and theme root
│   ├── _tokens.scss          # CSS variables, color palette, spacing, radii
│   ├── _mixins.scss          # Breakpoints, surface mixins, layout columns
│   ├── root.scss             # Top-level theme scope
│   └── globals.css           # Base resets & font definitions
│
├── assets/                   # Static SVG icons, brand graphics, images
├── main.tsx                  # Application root entry, router, and providers
└── index.html                # HTML entry template (at project/app root)
```

---

## 3. Hook Placement Hierarchy (The Lowest-Scope Rule)

Hooks must be organized by **scope**, not dumped into a single flat directory:

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Feature-Private Hooks (1 caller or local to 1 feature)   │
│    └── Colocated inside that feature (or feature/hooks/)    │
├─────────────────────────────────────────────────────────────┤
│ 2. Area-Shared / Shell Composer Hooks                       │
│    └── components/_shell/hooks/ or parent feature hooks/    │
├─────────────────────────────────────────────────────────────┤
│ 3. App-Wide Cross-Cutting Hooks (Crosses 2+ top domains)   │
│    └── src/hooks/                                           │
├─────────────────────────────────────────────────────────────┤
│ 4. Store Selector & Action Hooks                            │
│    └── Colocated in the Zustand store file (src/stores/*)   │
└─────────────────────────────────────────────────────────────┘
```

### The Promotion Rules:
1. **Single-caller hook:** Colocate directly next to the component (`components/session/use-shot-scroll.ts`).
2. **Feature Area (3+ hooks in an area):** Create a dedicated `<area>/hooks/` subfolder (e.g. `components/retouch/hooks/`).
3. **Shell Composer:** Shell orchestration hooks called only by shell layout components (`studio-shell.tsx` / `content.tsx`) live in `components/_shell/hooks/`.
4. **App-Wide Promotion:** Move to `src/hooks/` **only** when a hook is consumed across multiple unrelated top-level domains.
5. **Store Selectors:** Always keep named selectors and action hooks in the store file itself (`src/stores/*-store.ts`).

---

## 4. `utilities/` vs. `lib/` Boundary

A clear separation prevents infrastructural dependencies from tangling with pure logic:

| Dimension | `src/utilities/` | `src/lib/` |
|---|---|---|
| **Purity** | 100% pure, stateless functions | May hold state, singletons, network connections |
| **Dependencies** | Zero external APIs, zero DOM state | Talks to APIs, DBs, WebSockets, LocalStorage |
| **Testing** | Simple unit tests (`input -> output`) | Mocked network/integration tests |
| **Examples** | `string-utils.ts`, `math-utils.ts`, `url-utils.ts`, `color-utils.ts` | `am-api.ts`, `auth-client.ts`, `persist-utils.ts`, `ws-client.ts` |

---

## 5. Migration & Refactoring Policy (Avoiding the `v2/` Trap)

When redesigning or rewriting a frontend surface:

1. **Do not create permanent `v2/` parallel directory hierarchies.**
   - Temporary namespaces (`components/v2/`) create split-brain codebases, duplicate primitives, and hardcoded linter rules that anchor debt.
2. **Quarantine legacy code instead:**
   - Move deprecated files into `components/v1/delete-candidates/` or `components/v1/unported-features/`.
   - Keep the modern code as the canonical root structure (`components/<feature>/`).
3. **Invert tooling rules before directory promotion:**
   - Update ESLint globs, SCSS linters, and Vite `loadPaths` *before* moving directories to ensure CI never breaks on intermediate states.
4. **SCSS Path Independence:**
   - Use bare imports (`@use "tokens" as *;`) via build-tool include paths (`loadPaths`) rather than deep relative imports (`@use "../../../styles/tokens"`), so file moves don't break stylesheet resolution.
