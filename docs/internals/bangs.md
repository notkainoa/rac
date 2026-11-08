# Bangs (work in progress)

**Status: nothing on this page is a design.** It records what the maintainer
wants and what's wrong today, so it isn't lost. When this work starts,
rethink the whole experience from scratch, deeper than the notes below, and
rewrite this page as decisions get made.

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

## What the maintainer wants

### Editable bangs

Implemented in `rac/power/bangs-deleted.patch` and
`rac/power/bangs-editor.patch`:

- The "Manage search engines and site search" page
  (`chrome://settings/searchEngines`) has a **Bangs** section listing the
  downloaded bangs, searchable through the page's search field (the list is
  capped at the first 100 matches). A **Deleted bangs** section appears once
  something is deleted, with a Restore button.
- Users can edit any bang, delete it, and add their own. Editing a
  downloaded bang opens the site-search edit dialog; saving removes the
  downloaded entry and creates the user's own `!trigger` site-search entry,
  which already beats the downloaded list and works with services off.
- Deleting records the trigger in the `rac.bangs.deleted` pref, which
  `TemplateURLService::BangsLoadedCallback` checks, so a deleted bang stays
  deleted when a new `bangs.json` arrives. Restore clears the mark and
  re-adds the bang on the spot.
- Bangs the user adds or edits appear under Site search, not in the Bangs
  section: they are the user's own entries.

Still open: the dedicated searchable Bangs page from plan 07 task M4 item 3
(the section above is the interim surface), and the address-bar rework
below.

### A better address bar experience

Today, typing a bang at the end of a query (`cats !w`) still shows "Google
search" in the address bar, plus a badge for the bang. That's wrong: when a
bang is there, the search isn't a Google search. The fix isn't just the
label. Rethink how bangs look and behave in the address bar as a whole.

## Questions for the design

- Should the user's edits be stored as changes on top of the downloaded
  list (added, changed, deleted, keyed by the bang's trigger), so updates
  merge cleanly? What happens when an update changes a bang the user edited?
- Should the editor build on Chromium's existing site search settings, which
  already add, edit, and delete shortcuts, or be its own page?
- What should the address bar show at each moment: while typing a bang, with
  the bang at the start versus the end, and when the bang doesn't exist?
- How should bangs relate to the command bar (phase 5) and to Chromium's
  keyword search, which also uses the address bar?
- What happens with Helium services off: are the user's own bangs still
  available? (They should be; they don't need the network.)
- Does it cost anything when nobody uses bangs? Loading and matching the
  list must not slow typing in the address bar.
