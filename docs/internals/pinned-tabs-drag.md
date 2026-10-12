# Dragging favorites and pinned tabs

How a drag moves tabs between the favorites grid, the pinned section, its
folders, and the open tabs, and the traps in that code. The patches are in
`patches/rac/pinned/`: `drag.patch`, `motion.patch`, `snap.patch`, in that
order, after the patches that add the item store and the sections.

## Dragging

Chromium's vertical tab strip never moves a tab between its pinned and
unpinned containers during a drag. rac does, and that breaks assumptions:

- **Pinning a tab recreates its views.** The drag session holds pointers to
  the dragged views, so `MatchDraggedTabsToContainer()` clears them, pins or
  unpins, and points the session at the new views. Any other code that
  changes a dragged tab's pin state while a `TabDragController` exists will
  leave dangling pointers and crash. That's why a canceled drag restores pin
  states from a posted task, after the controller is gone.
- **The sync stops during a drag.** `SidebarWindowSync::Reconcile()` and
  favorite reordering wait until the drop, so the drag can move tabs freely.
  The drop decides what the tabs become; anything else puts them back.
- **Chromium creates a window to carry tabs dragged out of the tab strip.**
  Its sync sees the drag before it starts, so it doesn't fill the window
  with items. Otherwise that window would stay open after the tabs move on.
- The pointer, not the tab, picks the container: above the open tabs'
  scroll view means favorites.
- **The old views must not show.** After a pin change mid-drag, Chromium
  animates the old view out right under the new one. Its layer is hidden,
  since the animation keeps resetting its opacity.
- **Pinned drops go to the window's active space.** A drop into the pinned
  section adds the tab to `pinned.<space id>` of the space the window shows
  when the drop happens. Tabs of other spaces stay hidden in the tab strip and
  are never drop targets.

## Motion

Chromium's animating layout manager moves every row from its last bounds to
its new ones. A row that's hidden still has bounds, so lay it out where it
will appear. That's why, with no pinned tabs, the divider waits closed above
the first open tab. It opens only when a drag reaches the top of the open
tabs, so other drags don't shift the open tabs under the pointer.

The layout manager takes its duration from `gfx::Animation::RichAnimationDuration`,
so Reduce Motion makes these changes instant.

A dragged tab is drawn pulled toward the slot it would drop into
(`drag_snap.cc`): favorites stay near their cell and glide to the next one,
and rows follow the pointer most of the way. Only the pointer picks the drop
slot. The layouts record each dragged view's slot while they're
calculated. A slot is a drag offset, not bounds, because Chromium lays out a
dragged view at the origin and moves it with a transform. The favorites grid
records slots only when laid out at its real width, since preferred-size
passes use other widths and would record wrong cells. The glide runs only
while a drag is in progress and for at most 150 ms after a slot changes; when
nothing is dragged, no animation exists.
