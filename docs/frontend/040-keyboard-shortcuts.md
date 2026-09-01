```yaml
description: Centralized keyboard-shortcut pattern for React apps — one useHotkeys hook with combo strings, cmd→platform canonicalization, and a handled-return convention; no hand-rolled window keydown listeners
globs:
  - "apps/web/src/**/*.{ts,tsx}"
  - "**/src/**/*.{ts,tsx}"
alwaysApply: false
```

# Keyboard shortcuts (React)

App-level (global) keyboard shortcuts go through **one** small `useHotkeys` hook,
not through a `window.addEventListener("keydown", …)` written by hand in each
component. The pattern is a registry table plus a hook that canonicalizes `cmd` → platform client/ctrl.

When adopting this standard, copy the canonical hook at the bottom of this file into
`src/hooks/use-hotkeys.ts` (or `src/utilities/hot-keys.ts`) in the target repo.

## Do

- **Register through `useHotkeys`** — pass a map of combo string → handler:
  ```tsx
  useHotkeys({
    "cmd+s": () => { void save(); return true; },
    "cmd+b": () => { toggleSidebar(); return true; },
  });
  ```
- **Write `cmd` for the platform command key** — the hook canonicalizes `cmd`
  (alias `mod`/`command`) to `meta` on macOS and `ctrl` on Windows/Linux. Use
  `ctrl`/`meta` explicitly only when you genuinely need that specific key.
- **Return truthy when you handled it** — a handler returning a truthy value
  triggers `preventDefault()` + `stopPropagation()`. Return `false`/`void` to let
  the event fall through (e.g. Backspace while typing in an input).
- **Guard text entry with `isEditableTarget(e)`** — for printable / destructive
  keys (Backspace, Delete, single letters), bail when the event came from an
  `<input>`/`<textarea>`/`<select>`/contentEditable so you don't hijack typing:
  ```tsx
  const onDelete = (e: KeyboardEvent) => {
    if (isEditableTarget(e)) return false;        // let the field handle it
    if (!hasSelection()) return false;
    deleteSelection();
    return true;
  };
  useHotkeys({ delete: onDelete, backspace: onDelete });
  ```
- **Read fresh state via the ref, not a deps array** — the hook keeps the latest
  handler map in a ref, so handlers see current closures with **one** listener for
  the component's lifetime. No deps to thread, no re-attaching on every render.

## Don't

- **No ad-hoc `window.addEventListener("keydown", …)`** in components for app
  shortcuts. One implementation, one place to reason about ordering, modifiers,
  and platform differences.
- **Don't re-implement `cmd`/`ctrl` branching** (`e.metaKey || e.ctrlKey`) inline
  per component — that's exactly what `cmd+…` canonicalization centralizes.
- **Don't `preventDefault()` unconditionally** — only when the handler actually
  acted; otherwise you swallow keystrokes the page still needs.

## Registry: write the key down before you bind it

The hook alone answers "how do I bind a key", not "which keys are already taken".
That knowledge tends to live in a comment in whichever component was written
first, which goes stale the moment someone adds a shortcut somewhere else. So the
app that owns the shortcuts also owns a table, and registers through it:

```ts
export const SHORTCUTS = {
  personal:  { combo: "cmd+j", where: "anywhere",        does: "Toggle the Personal dashboard" },
  sidebar:   { combo: "cmd+b", where: "project screens", does: "Show / hide the sidebar" },
  save:      { combo: "cmd+s", where: "board · diagram", does: "Save" },
} as const;

export type ShortcutCombo = (typeof SHORTCUTS)[keyof typeof SHORTCUTS]["combo"];

/** Same hook, narrowed: a combo that is not in the table does not compile. */
export function useShortcuts(map: Partial<Record<ShortcutCombo, HotkeyHandler>>): void {
  useHotkeys(map);
}
```

```tsx
useShortcuts({
  [SHORTCUTS.sidebar.combo]: () => { toggleSidebar(); return true; },
});
```

- **A table, not a uniqueness constraint.** Matching is per listener, so two
  screens may claim the same combo — ⌘S saves whichever of them is mounted. The
  `where` column is what records that, and reviewing it is how you notice a real
  collision.
- **Narrow the wrapper, not the hook.** `useHotkeys` and `HotkeyMap` keep their
  generic signatures so this file stays copy-pasteable between repos; each app's
  own combos are its own type.

## Element-scoped keys are NOT hotkeys

Local UX on a specific control — **Enter** to submit a create form, **Escape** to
cancel a rename or blur a field — stays as an inline `onKeyDown` on that
`<input>`/`<textarea>`. Those are element-scoped interactions, not global
shortcuts; routing them through `useHotkeys` would be over-engineering.

| Use `useHotkeys` (global)            | Use inline `onKeyDown` (element-scoped) |
| ------------------------------------ | --------------------------------------- |
| Save (`cmd+s`), toggle panel (`cmd+b`) | Enter-to-submit on a form input         |
| Delete selected canvas node          | Escape-to-cancel an inline rename       |

## Canonical hook

```ts
export type HotkeyHandler = (e: KeyboardEvent) => boolean | void;
export type HotkeyMap = Record<string, HotkeyHandler>;

export function useHotkeys(map: HotkeyMap): void {
  const mapRef = useRef(map);
  mapRef.current = map;                          // fresh closures, no deps array

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      const combo = eventCombo(e);               // "meta+s", "delete", …
      for (const [keys, handler] of Object.entries(mapRef.current)) {
        if (canonicalize(keys) !== combo) continue;  // "cmd+s" → "meta+s" on mac
        if (handler(e)) { e.preventDefault(); e.stopPropagation(); }
        return;
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);
}
```
