# Favorites and pinned tabs

How rac's favorites and pinned tabs (see the
[glossary](glossary.md)) are built, and the traps in that code. The patches
are in `patches/rac/pinned-tabs/`, in this order:

| Patch | What it adds |
| --- | --- |
| `sidebar-store.patch` | The item store, the per-window sync, and the tab tags |
| `favorites.patch` | Favorites as tiles at the top of the sidebar |
| `pinned-section.patch` | Pinned tabs and folders above the open tabs |
| `menus.patch` | Context menus, the folder menu, renaming, and the Tab menu |
| `close-and-navigate.patch` | Closing resets in place; the reset button; typed addresses open a new tab |
| `drag.patch` | Dragging between favorites, pinned tabs, folders, and open tabs |

## Items are the source of truth, tabs follow

`rac::SidebarItems`, a profile keyed service, holds the favorites list and one
pinned list per space in the `rac.sidebar.lists` pref. Each item remembers
the page it was pinned on. Pinned lists also hold folders, one level deep.

Every normal window has a `SidebarWindowSync` that makes its tab strip match
the items. Every window shows every item as a real tab, unloaded until used,
so the same favorites and pinned tabs appear in every window. The sync's
`Reconcile()` is the only code that should create, remove, pin, or reorder
those tabs. Other code changes the items and lets the sync follow; changing
the tab strip directly gets undone on the next reconcile.

- **Favorites are Chromium's pinned tabs.** Helium's pinning, session
  restore, and extensions keep working, and any tab pinned by them becomes a
  favorite. Helium's existing pinned tabs became favorites once, on first
  run (`rac.sidebar.migrated_pinned_tabs`).
- **Pinned tabs are the first unpinned tabs.** They're never in a tab group.
  `PinnedSection` draws their folders and the divider by laying out the
  unpinned tab container itself, so Chromium's tab views, hover cards, and
  drag code still work on them.
- **Tabs know their item by a tag** (`sidebar_tab_tag.h`), saved in the
  session as tab extra data, so restored tabs match their items again. A
  tab without a tag is an open tab.

## The space seam

Pinned tabs belong to one space, and favorites belong to the profile. Until
Spaces lands, `pinned_tabs_space.cc` says every window shows the same space,
`default`. It's the only file that knows about spaces. Connecting Spaces
means changing that file, and moving each window's open tabs per space is
Spaces' job. The pinned list key is `pinned.<space id>`.

## Dragging

Chromium's vertical tab strip never moves a tab between its pinned and
unpinned containers during a drag. rac does, and that breaks assumptions:

- **Pinning a tab recreates its views.** The drag session holds pointers to
  the dragged views, so `MatchDraggedTabsToContainer()` clears them, pins or
  unpins, and points the session at the new views. Any other code that
  changes a dragged tab's pin state while a `TabDragController` exists will
  leave dangling pointers and crash. That's why a canceled drag restores pin
  states from a posted task, after the controller is gone.
- **The sync stops during a drag.** Reconcile and favorite reordering wait
  until the drop, so the drag can move tabs freely. The drop decides what
  the tabs become; anything else puts them back.
- **Chromium creates a window to carry tabs dragged out of the tab strip.**
  Its sync sees the drag before it starts, so it doesn't fill the window
  with items. Otherwise that window would stay open after the tabs move on.
- The pointer, not the tab, picks the container: above the open tabs'
  scroll view means favorites.
