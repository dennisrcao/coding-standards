```yaml
description: Positional drag and drop — one drag context per layout, one resolver shared by the preview and the write, a ghost that is a shadow not a tile, pointer truth over library delta, and an optimistic commit; never draw the preview with different math than the write
globs:
  - "apps/*/src/**/*.{ts,tsx}"
  - "apps/*/app/**/*.{ts,tsx}"
  - "**/components/**/*.{ts,tsx}"
alwaysApply: false
```

# Drag and drop (positional)

**Scope: drags where the drop *coordinates mean something*.** An item dropped on a time grid becomes
an 11:15 start. A node dropped on a canvas becomes an x/y. A card dropped on a Gantt row becomes a
date. The pointer position is an *input to a calculation*, and that calculation's answer is written
to a server.

**Reordering a list is not this.** `useSortable` over a stable array is a much smaller problem —
there are no coordinates, only a before and an after — and it needs roughly rules 1, 13 and 14 and
nothing else. Do not pay for the rest of this document on a sortable list.

Examples below use dnd-kit, because that is what the reference implementations use. Rules 4 and 16
are dnd-kit specifics; every other rule is about the *shape* of the feature and survives a library
swap.

> **The motivating failure.** A drag-to-schedule feature where the preview said 22:00 and the write
> produced 23:00; where a second drag context silently made the target undroppable; where the ghost
> rendered at half the height of the block that appeared; where the item cache updated instantly and
> the grid cache lagged a full refetch behind. Typecheck, lint and the unit suite were green through
> all of it. Every rule below is one of those.

## The pipeline

A positional drag has four stages, and each gets exactly one owner:

| Stage | Owner | Answers |
|---|---|---|
| **Sense** | the drag provider | What is being dragged, and where is the pointer? |
| **Resolve** | one pure resolver | What would this drop produce? |
| **Preview** | a store + a dedicated ghost component | Draw that, cheaply, at pointer rate |
| **Commit** | the mutation hook | Write it optimistically; roll back if the server disagrees |

**The preview and the commit consume the same resolver output.** That is the load-bearing idea in
this document. Most of what follows is a consequence of it.

---

## Structure

### 1. One drag context per layout, at a root that spans every source and every target

dnd-kit binds `useDraggable` / `useDroppable` to the **nearest** provider. Two contexts is two
worlds: wrap a second one around a grid that is already inside one and the grid's droppables bind to
the inner context while the draggables bind to the outer — and nothing can be dragged between them.
There is no error. The item simply never drops.

So the context lives at the layout root that contains every source *and* every target, even when
that root is a shell component that otherwise does nothing. A feature component that already owns a
context gives it up when a second feature needs to drag into it.

**A new surface joining an existing drag joins that context. It does not grow its own.**

### 2. One resolver decides where a drop lands

```ts
resolveDrop(payload: DragPayload, geometry: DropGeometry): DropResult | null
```

The move handler calls it to draw the preview. The end handler calls it to build the mutation. Same
arguments, same answer.

**The point is not deduplication.** Different drag kinds legitimately share almost no math — an item
with no position of its own must read the pointer's offset inside the target, while an item being
*moved* already has a position and should apply the drag's delta to it. Those two branches stay
separate inside the resolver. The point is that **a preview drawn by one function and a write
committed by another will diverge on the first edge case only one of them handles** — and it will do
so silently, because the user only sees the second one after they have let go.

Two consequences:

- **Return `null` rather than guessing.** An unresolvable drop means *no preview and no write*, not
  a default value. A resolver that invents an answer makes the preview lie instead of disappear.
- **Different consumers may need different output shapes** — one route posts UTC, another posts a
  naive local string with no zone. Carry both through the result untouched rather than adding a
  shared "just give me a string" field, which has to pick one and be wrong for the other caller.

### 3. Build the geometry once

```ts
// One function, called from both handlers
function geometryFrom(e, over, target, livePointer): DropGeometry
```

Rule 2 is worthless if each call site hand-rolls the object literal it passes in. Two copies agree
right up until someone edits one of them. **An invariant that depends on two spellings staying
identical is not an invariant.**

---

## Truth

### 4. Trust the pointer, not the library's delta

```ts
// WRONG — this is not where the cursor is
const pointerY = activatorEvent.clientY + delta.y;

// RIGHT — a live pointermove reading, with the reconstruction as fallback
const pointerY = livePointerY ?? reconstructFromActivator(activatorEvent, delta.y);
```

dnd-kit's `delta` accumulates **the dragged node's translate, not the cursor's travel.** Move the
pointer before the activation constraint is satisfied and the reconstruction drifts by however far
you moved — measured at ~18px after a 20px pre-activation jog. The drop then lands slightly off from
where you pointed, biased by how you happened to start the drag.

**Snapping hides this.** On a 15-minute grid the error only surfaces near a boundary, which is why
this kind of bug survives for months and gets reported as "sometimes it puts it in the wrong slot."

Track the real thing — `window.addEventListener("pointermove", …, { passive: true })` on drag start,
into a ref, removed on end. Seed the ref from the activator so a drag that ends without a single move
still has a position. Keep the reconstruction *only* as the fallback for inputs that emit no move at
all (some touch sequences).

**Both the preview and the commit must read through the same resolution helper.** A preview from the
live pointer and a write from the reconstruction is exactly the divergence rule 2 exists to prevent.

### 5. Size the preview with the renderer's own geometry function

```ts
// The function that positions real items — not its own arithmetic
const box = calculatePositionAndSize(result.start, result.end);
```

Renderers usually enforce constraints the raw math does not know about: a minimum height for
readability, a snap, a maximum. A preview drawn from raw percentages renders a short item at half
the size of the thing that actually appears.

**A preview that lies about the outcome is worse than no preview** — the user aims with it.

### 6. Clamp so the whole item fits, and clamp against the target you dropped on

Two ceilings, and the lower one wins:

- The **surface** ceiling keeps the drop on the grid at all. Without it, a drop past the edge lands
  outside the rendered range where nothing is visible.
- The **extent** ceiling keeps the item's *far edge* on it too. A 90-minute block dropped at the
  bottom of a day starts at 23:00 and ends at 00:30 tomorrow — a real record, on a surface nobody is
  looking at, drawn clipped.

**Floor when snapping a ceiling, never round** — rounding up puts the tail back over the edge it was
just pulled in from.

And clamp against **the target under the pointer**, not against whatever the arithmetic produced. A
scrollable surface is usually shorter than the range it represents, so a full-height drag is worth
more than the range's own extent; clamping against the computed value silently lands the item on the
*next* target. **The drop target decides the container; the math only decides the position inside
it.**

Make the item's extent a **required** argument to the resolver, not an optional one. It was optional
once, and an optional extent is precisely how the off-the-end bug gets written. A caller without one
still has an answer — the default — so there is no honest reason to omit it.

### 7. Identity keys are local fields; wire formats convert at the boundary

```ts
// WRONG — toISOString() is UTC; west of Greenwich an evening drop keys to tomorrow
const key = date.toISOString().slice(0, 10);

// RIGHT — the same local fields the surface labelled itself with
const key = `${d.getFullYear()}-${d.getMonth() + 1}-${d.getDate()}`;
```

The preview matches a resolved drop to a target by key. If the two sides derive that key differently
— or via UTC — the ghost appears on the neighbouring column and nobody can reproduce it outside their
own timezone.

The same discipline applies outward: convert to the wire format at the call that sends it, once, and
never let a half-converted value into the shared result type.

---

## The ghost

### 8. The ghost is a shadow, not a tile

Render the preview **full-size on the target**, ignoring the packing rules that make real items share
space with their neighbours.

That is a product decision, not an oversight. A drop is not claiming a slice beside the item already
there — it is asking about the whole slot, overlaps and all. Squeezing the ghost into a half-width
column tells the user something false about what they are about to create.

Three properties it must keep:

- **`pointer-events: none`.** It answers a question about the surface; it must never intercept the
  drag asking it.
- **Stacked above every real item.** Compute the ceiling of your item z-index formula and go above
  it, with a comment saying so.
- **Visually unfinished on purpose** — dashed or translucent, no texture, no shadow, none of the
  chrome that makes a real item read as real. The user must never be unsure which one is the ghost.

### 9. Drag state goes in a store with a narrow selector, not the provider's `useState`

The provider wraps the whole layout. `useState` set from the move handler re-renders all of it at
pointer rate — on a low-powered display this is the difference between a smooth drag and a
slideshow.

Put the preview in a store (Zustand — see `020-zustand.md`) with a **per-target selector**, so only
the one ghost whose key matches re-renders. Every other target's selector returns the same `null` it
returned last frame and React skips it.

```ts
export function useGhostFor(key: string): Ghost | null {
  return useGhostStore((s) => (s.ghost?.key === key ? s.ghost : null));
}
```

**Return the stored object itself, never a derived one.** A fresh object per call re-renders every
subscriber on every read, which is the opposite of the point.

**Give the ghost its own component** with its own subscription. Put the selector on the target
container instead and every pointer move re-renders the container — and every item inside it.

**Bail on an equal write.** Pointer movement is continuous; a snapped grid is not. Most frames of a
drag resolve to the block the previous frame already resolved to, and setting an equal value still
notifies subscribers:

```ts
show: (next) => {
  const cur = get().ghost;
  if (cur && cur.key === next.key && cur.top === next.top && cur.size === next.size) return;
  set({ ghost: next });
},
```

### 10. Coalesce moves into one animation frame — and take the last, not the first

```ts
onDragMove: (e) => {
  pending.current = e;                        // last write wins
  if (frame.current === null) frame.current = requestAnimationFrame(paint);
}
```

A 120Hz pointer otherwise resolves the same result eight times per frame. Storing the **latest**
event in a ref — rather than a leading-edge throttle — means the ghost still ends up where the
pointer actually is.

### 11. Cancel the queued frame when the drag ends — but do not clear the pointer with it

Painting after the drop leaves a ghost on the surface with nothing dragging. One `stopPainting()`,
called from the end handler, the cancel handler, **and** an unmount effect.

The trap, which deserves a comment in your code: `stopPainting` must **not** clear the pointer ref.
The end handler calls it first — to kill the queued frame before anything mutates — and *then* reads
the pointer to decide where the drop lands. Clearing it there routes that read to the fallback in
rule 4, and the write disagrees with the ghost by one snap unit. Re-seed on the next drag start
instead.

---

## Commit

### 12. Commit optimistically, into every cache the mutation invalidates

The drop handler decides **what** was dropped **where**. It does not touch caches. Mutation hooks own
the optimistic write, the rollback and the reconciliation — the full rules are
`026-optimistic-updates.md`, whose motivating bug *is* a positional drag.

The parts a drag makes unmissable:

- A mutation that invalidates two query keys owes an optimistic write to **both**. Writing one and
  invalidating two reads to the user as the drag having failed: one surface updates instantly, the
  other takes a full refetch to agree.
- Extract `cancelQueries → snapshot → rollback → settle` into a shared helper the moment a second
  mutation needs the same pair. The reverse drag (rule 13) *is* that second mutation.
- Write **per key**, not with a blanket `setQueriesData`. Only a cached view whose range actually
  covers the drop may hold the placeholder; anything else is a phantom that never resolves.

### 13. The reverse drag ships in the same change

If dragging **onto** the surface is optimistic, dragging **off** it is not a follow-up ticket. Users
read the pair as one interaction, and a fast create beside a slow delete feels more broken than two
slow operations.

**Guard the reverse against records you do not own.** A surface that shows both your records and
records synced from elsewhere must only unschedule/delete the ones your app created — decided
**server-side**, with the client's optimistic path replicating the same test. Getting this wrong on a
shared calendar or shared board sends a cancellation to other people.

---

## Surfaces

### 14. Listeners get their own node; nested controls are siblings

```tsx
// WRONG — listeners on the root, so a nested control shares the drag's pointerdown
<div ref={setNodeRef} {...attributes} {...listeners}>
  <ToggleButton />
  <Body />
</div>

// RIGHT — the control is a sibling of the node that carries the listeners
<div ref={setNodeRef}>
  <ToggleButton />
  <div {...attributes} {...listeners}><Body /></div>
</div>
```

An explicit drag handle is the same rule stated loudly: the handle carries the listeners and every
other control sits beside it.

**Gate draggability at the hook, not at the render** — `useDraggable({ …, disabled: !canDrag })` —
and spread `attributes` / `listeners` conditionally. Read-only records and items with no positional
meaning are not draggable, and a `cursor: grab` on something that cannot be grabbed is a lie.

### 15. Hidden surfaces reject drops

Alternate views kept mounted under `display: none` are still registered droppables with real
measured rects. Without an explicit enabled flag — checked in **both** the ghost painter and the drop
handler — an item lands on a surface nobody can see.

### 16. Route collisions when several drag kinds share one context

When one context carries more than one kind of draggable, write a custom `CollisionDetection` rather
than hoping the default sorts it out:

- **Filter `droppableContainers` by what the active drag may legally target.** A group header must
  not be droppable onto a leaf row, or onto another parent's children.
- **`pointerWithin` first, then fall back to `closestCorners`.** Pointer-within is what lets an
  *empty* container accept a drop; the fallback covers the pointer being over nothing.

---

## Testing

### 17. The math is pure and tested; the drag is not

Everything that turns coordinates into values belongs in a plain module as a pure function with a
colocated unit test. The provider stays thin — it senses, delegates, commits — and needs no DOM test
because it does no arithmetic.

**Test the edges, not the middle.** The far edge of the surface; an item longer than the space left;
a zero or negative extent; a null pointer; a drag that rolls over into the next container. The middle
of the surface has never been the bug.

**Then load the page and drag it yourself.** Synthetic pointer events plus an activation constraint
make automated drag tests slow and flaky, and they do not prove the thing that actually breaks — that
what you saw is what got written. The motivating failure passed typecheck, lint and the full unit
suite while the feature was visibly wrong on screen.

---

## Before you call a drag done

- [ ] One drag context, at a root that spans every source and target.
- [ ] Preview and write come from **one resolver**, on geometry built by **one function**.
- [ ] The resolver returns `null` rather than guessing.
- [ ] Pointer position reads a live `pointermove`; the library's delta is the fallback, not the source.
- [ ] The preview is sized by the same function that sizes real items.
- [ ] The drop is clamped so the whole item fits, against the target under the pointer.
- [ ] Identity keys use local fields; wire formats convert once, at the boundary.
- [ ] The ghost is full-size, `pointer-events: none`, above every item, and visibly unfinished.
- [ ] Ghost state is in a store with a per-target selector; equal writes are dropped.
- [ ] Moves coalesce into one `requestAnimationFrame`, taking the latest event.
- [ ] The queued frame is cancelled on end / cancel / unmount — **without** clearing the pointer ref.
- [ ] Every key in `invalidateQueries` also appears in `setQueryData`; the rollback is tested.
- [ ] The reverse drag exists, is equally optimistic, and refuses records you do not own.
- [ ] Listeners are on their own node; nested controls are siblings; `disabled` is set at the hook.
- [ ] Hidden surfaces reject drops.
- [ ] Collision detection is routed when kinds share a context.
- [ ] The coordinate math is pure, colocated and tested at the edges.
- [ ] **You dragged it yourself, on screen.**
