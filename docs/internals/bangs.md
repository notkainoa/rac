# Bangs (work in progress)

## How bangs work today

Bangs come from Helium (`helium/core/add-native-bangs.patch` and
`helium/ui/bangs-ui.patch`). Typing `!w cats` in the address bar searches
Wikipedia for "cats".

- The list is a file, `bangs.json`, downloaded from Helium services by
  `components/search_engines/template_url_bang_manager.cc`. It's behind the
  "Allow downloading the !bangs list" setting. When that's off, only a copy
  already in the browser's cache is used.
- Each bang becomes a search engine entry (a `TemplateURL` with a
  `bang_id`), the same kind of entry as the site search shortcuts in
  Settings.
- A bang works at the start of the query (`!w cats`), and in the middle or
  at the end (`cats !w`) once a space or Return follows it.

## What's built

### The Bangs settings page (patches/rac/power/)

`chrome://settings/bangs`, a subpage of the General settings page. A "Bangs"
row on the General page's search engine card opens it, and a row on the
site-search page points back to it. Three sections, top to bottom:

- **Yours**: the user's own bangs — site-search entries whose keyword starts
  with `!`. Adding and editing go through the usual search-engine dialog,
  which the page puts in bang mode (`isBang`): the title says "bang" and the
  keyword is normalized to carry the `!` marker.
- **Bangs**: the downloaded list, searchable and capped at 100 rows (the
  full list has thousands of entries). Editing a downloaded bang replaces
  it: the original is marked deleted and the edited copy becomes the
  user's own entry, so it lands under Yours.
- **Deleted bangs**: triggers removed from the downloaded list, with a
  Restore button.

The page reuses `SearchEnginesHandler`: `getSearchEnginesList` already
carries `bangs` and `deletedBangs`, and `removeBang`, `restoreBang`, and the
edit callbacks handle the rows. When the page is closed it costs nothing.

### Edits that survive list updates (bangs-deleted.patch)

`rac.bangs.deleted`, a profile pref, holds the triggers of downloaded bangs
the user deleted. `TemplateURLService` skips them when it applies a fresh
`bangs.json`, and `RestoreDeletedBang` un-marks and re-adds one. `Remove`
records the trigger when the removed engine is a bang, so deleting in the
page (or anywhere else) sticks.

- A **deleted** bang stays deleted across updates.
- An **edited** bang is deleted-then-added: the downloaded trigger is marked
  deleted, and the user's version is a normal site-search entry that keeps
  working without the list.
- The user's **own** bangs are plain TemplateURLs; a user keyword shadows a
  downloaded bang with the same `!trigger`, so adding `!w` overrides the
  downloaded `w` without touching the list. Deleting the user's entry lets
  the downloaded one return on the next list update.

### Design answers, so far

- **Edits as deltas.** Yes: the deleted-trigger set is the delta, and
  user entries shadow the list by keyword. When an update changes a bang
  the user edited, the user's version wins — the downloaded trigger is
  either deleted or shadowed.
- **Its own page.** The editor is its own subpage, not a section inside
  site search: the downloaded list is far too long to share a page, and
  bangs deserve a single place that owns "your bangs + the list + deleted".
- **Helium services off.** The user's own bangs still work — they are
  ordinary keyword search engines and never needed the network.
- **Cost when unused.** Nothing: the pref is only read when the downloaded
  list is applied, and the page only exists while it's open.

### What the address bar should do (M5, not built)

Today, typing a bang at the end of a query (`cats !w`) still shows "Google
search" in the address bar, plus a badge for the bang. That's wrong: when a
bang is there, the search isn't a Google search.

Direction: a recognized `!x` token should make the whole input a search on
that engine — the same end state as keyword activation (pressing Tab on a
site-search keyword): the site's name and icon become the search target,
the bang token is consumed, and the rest of the input is the query. Position
of the token (start, middle, end) shouldn't matter once it's unambiguous.
The pieces already exist: bangs are keyword `TemplateURL`s, so matching can
reuse the keyword engine path rather than a parallel bang badge mechanism.
Open questions for M5: what to show while the user is mid-token (`!` alone,
or a partial trigger that matches nothing), how this interacts with the
command bar (phase 5), and whether a nonexistent trigger should hint that
the bang can be created on the Bangs page.

## Open questions

- Should the Bangs page live somewhere more prominent than the General
  page's search card? For now it sits next to site search, which is where
  Chromium puts keyword engines.
