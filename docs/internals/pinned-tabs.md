# Favorites and pinned tabs

How rac's favorites and pinned tabs (see the [glossary](glossary.md)) are
kept in step with the tab strip, and the traps in that code. Dragging has its
own page: [pinned-tabs-drag.md](pinned-tabs-drag.md). The patches are in
`patches/rac/pinned/`. `sidebar-store.patch` holds the data and the sync;
the `fix-*`, `observer-lifetime`, and `space-tag-persistence` patches
correct it, so read the code, not the first patch, to see how it behaves
now.

## Items are the source of truth, tabs follow

`rac::SidebarItems`, a profile keyed service, holds the favorites list and
one pinned list per space in the `rac.sidebar.lists` pref. The pinned list's
key is `pinned.<space id>`. Each item remembers the page it was pinned on.
Pinned lists also hold folders, one level deep.

Every normal window has a `SidebarWindowSync` that makes its tab strip match
the items: favorites, then the pinned tabs of the space the window shows,
then open tabs. `Reconcile()` is the only code that should create, remove,
pin, or reorder those tabs. Other code changes the items and lets the sync
follow; changing the tab strip directly gets undone on the next reconcile.
It runs from a posted task, never inline, and stops during a drag.

- **Favorites are Chromium's pinned tabs.** Helium's pinning, session
  restore, and extensions keep working, and any tab pinned by them becomes
  a favorite. Helium's existing pinned tabs became favorites once, on first
  run (`rac.sidebar.migrated_pinned_tabs`).
- **Pinned tabs are the first unpinned tabs.** They're never in a tab
  group. `PinnedSection` draws their folders, the space name, and the
  divider by laying out the open tabs container itself, so Chromium's tab
  views, hover cards, and drag code still work on them.
- **Items without a tab are opened unloaded.** A window opens a tab for each
  item it doesn't show yet, so a favorite appears in every window of the
  profile.
- **A tab that stops being an item stays open if it's in use** (active or
  loaded) and closes otherwise. Removing an item in one window therefore
  closes its idle copies in the others.
- **Incognito and guest windows have no items.** `SidebarItems::Get()` is
  null, so they keep Chromium's behavior. The hooks in Chromium files (pin
  command, closing, address bar navigation, startup tabs) all check for a
  sync first and do nothing without one.

## Tags link tabs to items

A tab knows its item by a tag on its `WebContents` (`sidebar_tab_tag.h`). A
tab without a tag is an open tab. The tag is also saved in the session, as
tab extra data, so a restored tab takes its item back instead of the window
opening a second copy. Anything that replaces a tab's `WebContents` has to
carry the tag over:

- Discarding and `ResetTab()` swap in a new `WebContents`. The sync copies
  the tag across in `OnTabStripModelChanged()` (`kReplaced`).
- A space that has no window is stored as a snapshot of its tabs, which
  includes each tab's item id (`StoredTab::sidebar_item_id`). Without it,
  reopening the space restores untagged tabs and the sync opens a second
  copy of every pinned tab. Recently closed tabs carry their item id too.

`Reconcile()` drops a tag when its item was removed or when a second tab
already shows the item, such as after a tab is dragged in from another
window. It keeps the copy that's in use.

## Spaces

Favorites belong to the profile and stay visible in every space. Pinned tabs
belong to one space. The seam is `pinned_tabs_space.cc`: it's the only file
that asks which space a window shows. Constraints that cross the spaces and
pinned patches:

- **Hidden spaces' tabs are still in the tab strip.** A window holds every
  space's tabs in one `TabStripModel` and `SpacesWindowManager` hides the
  other spaces'. A pinned tab of a hidden space is tagged with an item that
  isn't in the window's list, so `Reconcile()` must not read that as a
  removed item and strip or close it. The exception is a Chromium-pinned
  tab whose item is in a pinned list: that's a favorite that moved into a
  space, and other windows must unpin it, or a stale favorite tile stays in
  each of them.
- **A space tag lives in two places.** `SpaceTabTag` on the `WebContents`
  and the session's extra data for the tab. When a favorite becomes a pinned
  tab or an open tab, or a pinned item moves into the window's space, set
  both through `AssignSidebarTabToSpace()`. Setting only the first loses the
  space on the next restore.
- **A window with no active space has no pinned tabs.** While it shows the
  "space is open elsewhere" screen, or before it claims a space, its space
  id is invalid: the sync opens no pinned tabs and a drag can't pin.
- **Deleting a space deletes its pinned list**, but only after the close
  path accepts the deletion. If a page's beforeunload cancels it, the space
  and its pinned tabs stay.
- **Early builds used one placeholder list**, `pinned.default`. `Load()`
  moves it to the profile's first space so those items and folders keep
  their ids. Don't remove this until nobody can still have the old pref.

## Closing, navigating, and folders

- **Closing resets in place.** Closing a favorite or pinned tab doesn't
  close it. `ResetTab()` puts it back as the window first opened it:
  unloaded, on its pinned page, with no history. It does nothing to the
  active tab, so the code first moves to the loaded tab used most recently
  (or a new tab) with `LeaveActiveTab()`. Otherwise resetting the active
  tab would load it again, or closing would load the pinned tab beside it.
  Pages that ask before leaving (beforeunload) and split tabs close the
  usual way, and the window opens their item again. A loaded tab is
  recorded as recently closed before it's reset, so reopening a closed tab
  brings back the page the user left.
- **Typed addresses open a new tab.** An address typed in the address bar
  while a favorite or pinned tab is active opens in a new tab, so the tab
  stays on its pinned page. Links still open in place. This is a hook in
  `browser_navigator.cc`.
- **Deleting a folder waits for its tabs to close.** The items are removed
  only once every tab is gone. Until then `Reconcile()` skips those items,
  or it would reopen each tab as it closes. If a tab's beforeunload is
  canceled or a tab can't close, the folder and its items stay.
- **A new folder stays until it has held an item and been emptied**, so
  creating one and dragging into it works. Removing a folder's last item
  removes the folder.
- **A pinned tab's name replaces the page title** in the tab strip, hover
  card, and tab search. They read it through `TabUIHelper`, and renaming
  has to invalidate the title in every window.

## Commands

The Tab menu's Unpin, Add to Favorites, and Remove from Favorites items are
rac's own commands (`IDC_RAC_*`, `menu-bar.patch`). They're hidden unless
they apply to the active tab, and Chromium's pin command is routed to the
sidebar in any window with a sync: it pins to the space's pinned tabs, or
turns pinned tabs and favorites back into open tabs. Without a sync it keeps
Chromium's behavior. Chromium's own startup list of pinned tabs is skipped
whenever items exist, since favorites open them already.

## Tests

`spaces_store_unittest.cc` (added by `fix-restored-item-id-test.patch`)
checks that a stored tab keeps its item id. The rest is covered by running
the browser: see [Cover every surface](../../AGENTS.md#cover-every-surface),
especially several windows, several spaces, and incognito.
