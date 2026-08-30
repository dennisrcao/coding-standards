```yaml
description: Colocated React + SCSS modules — nesting follows JSX, design tokens, className patterns
globs:
  - "apps/web/src/**/*.tsx"
  - "apps/web/src/**/*.module.scss"
alwaysApply: false
```

# Frontend (`apps/web/src/`)

## Basics

- **Colocate** `ComponentName.tsx` with `ComponentName.module.scss` under the same folder.
- **Tokens:** Reuse your shared variables file where appropriate (e.g. `apps/web/src/styles/_variables.scss` with `$bg`, `$text`, `$border`, `$accent`, etc.).
- **className:** Ternary or `[a, b].filter(Boolean).join(' ')`; stay consistent with existing components and any global stylesheet.
- **Types:** Inline `type` for small props; stable list keys (prefer domain ids, not array index when data allows).
- **Path alias:** Prefer `@/` → `apps/web/src/` (or match whatever the repo configures in Vite/TS).

## SCSS nesting mirrors JSX (2–4 levels)

The Sass nesting hierarchy must follow the same shape as the JSX tree (same order of regions and depth). That keeps styles easy to read next to the markup and makes refactors safer.

**Do**

- **Root** — One block for the root element's `className` (e.g. `.page`, `.card`) holds layout for the whole component tree.
- **Nested** — For each child using `styles.foo`, add a nested rule for `.foo` under the root (or the correct parent) so the file reads top-to-bottom like the component.
- **Rename together** — If you restructure JSX (new wrapper, split a section), update the same levels in the SCSS; avoid orphan classes at the top level that only apply deep inside a subtree unless shared on purpose.

**Don't**

- **Flat list of unrelated class blocks** that don't reflect component sections when the JSX is clearly nested.
- **Diverging order** where SCSS section order fights the top-to-bottom flow of the TSX (mixins/variables at the top of the file are fine).

**Example**

If JSX is `div.root > div.toolbar > button.btn`, the module should have `.root { … .toolbar { … .btn { … } } }`, not `.btn` as a top-level block sitting far from `.root` in a way that hides the parent relationship.

## Pairing

If you change layout/styling in TSX, update the colocated `.module.scss` in the same change. Shared design tokens live under your styles folder (e.g. `apps/web/src/styles/_variables.scss` with Sass `@use`).

## Unused classes

Classes can drift out of sync — defined in the `.module.scss` but no longer referenced. No maintained linter or VS Code extension catches this on a modern ESLint; see [080 Unused CSS-Module classes](080-unused-scss-classes.md) for a zero-dep script and the rationale.

## Responsive: fluid containers need fluid type

A layout sized in viewport units (`vw`/`vh`) whose type is sized in fixed units (`px`/`rem`)
is not responsive — it is a **zoom that only half-works**. The boxes shrink with the viewport;
the text inside them does not. Every such pair has a width where the two curves cross and the
text no longer fits its box, and the symptom is clipped or overflowing labels rather than an
obviously broken page, so it survives review.

If a container is `vw`, its type should scale too. `min()` / `max()` let you do that without
touching the width the design was authored at:

```scss
// 1.574vw resolves to 27.2px at 1728px wide, so min() keeps the original size at
// the reference width and scales down only below it. Nothing above it changes.
font-size: min(1.7rem, 1.574vw);
```

Prefer this over widening the container. Widening a sidebar or rail to fit its text takes that
width from the content column — and if the content's own children are sized in `vw` rather than
`%` of their parent, they will not reflow into the narrower column, they will just overflow and
be hidden. Scaling the type costs no layout width at all.

**Watch the fixed costs.** Scrollbar gutters (`overflow-y: scroll` reserves one even when
nothing scrolls) and hardcoded padding do not shrink with the viewport, so proportional type
scaling alone stops being enough at small sizes. Measure at the narrow end, not just the wide
one.

### Breakpoint mixins

Keep a `below()` helper next to the variables rather than hand-writing media queries:

```scss
// _mixins.scss
@use 'variables' as *;

@mixin below($breakpoint) {
  @media (max-width: $breakpoint) { @content; }
}
```

**A breakpoint value belongs in exactly one place.** Sass variables are compile-time and CSS
custom properties are **not legal in `@media` conditions**, so a `--breakpoint-*` custom
property cannot drive a media query — do not build that bridge expecting it to work. If a
threshold is consumed only by CSS, it lives in `_variables.scss` and nowhere else; if it is
consumed only by JS (e.g. a layout that swaps component trees rather than restyling), it lives
in a TS constant and nowhere else. Duplicating it in both and hoping they stay in sync is how
you end up with breakpoint variables no one uses and literals scattered through components.

### Verifying

Assert that text fits, not that an element is visible — a clipped label is still `visible`. In
a browser test, measure a `Range` over the text node against the element's **content box**:
`clientWidth` includes padding and reads falsely clean. Wait for `document.fonts.ready` first,
or you measure the fallback font. Don't assert exact pixel widths for anything that reserves a
scrollbar gutter: headed and headless browsers disagree, and so do platforms.
