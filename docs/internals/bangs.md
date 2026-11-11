# Bangs

Bangs come from Helium (`helium/core/add-native-bangs.patch` and
`helium/ui/bangs-ui.patch`). Typing `!w cats` in the address bar searches
Wikipedia for "cats".

- The list is a file, `bangs.json`, downloaded from Helium services by
  `components/search_engines/template_url_bang_manager.cc`. It's behind the
  "Allow downloading the !bangs list" setting. When that's off, only a copy
  already in the browser's cache is used.
- Each downloaded bang becomes an in-memory search engine entry (a
  `TemplateURL` with a `bang_id`). They aren't saved; the list is applied
  again at every start.
- The list is applied only after the saved engines have loaded
  (`rac/power/bangs-deleted.patch`). A list already in memory, as in every
  profile after the first, used to arrive first: its bangs took the ids the
  saved engines then loaded with, and a downloaded `!x` slipped in next to
  the user's own `!x`. Applying a list that added bangs tells the
  service's observers once, so an open Bangs page sees a list that arrives
  late.
- A bang works at the start of the query (`!w cats`), and in the middle or
  at the end (`cats !w`) once a space or Return follows it.

## Edits that survive list updates

Patches: `rac/power/bangs-deleted.patch`, `rac/power/bangs-page.patch`.

- **Deleted bangs** are a profile pref, `rac.bangs.deleted`: a list of
  triggers, without the `!`. `TemplateURLService::BangsLoadedCallback`
  skips them each time it applies the list, so a deleted bang stays deleted
  whatever the next `bangs.json` holds. Restoring removes the trigger and
  re-applies the list already in memory. It never downloads it.
- **The user's own bangs** are ordinary site search entries whose keyword
  starts with `!`. They're saved like any search engine and work without
  the list or with Helium services off. A downloaded bang is skipped when
  the user's own entry has its keyword.
- **Editing a downloaded bang is a delete plus an add**: its trigger goes
  into the deleted list, and the user's version becomes their own entry.
  Editing an entry in place wouldn't last, since downloaded entries are
  rebuilt from the list at every start. Saving with nothing changed does
  nothing.
- Deleting the user's own bang lets a downloaded bang it hid come back. The
  default search engine is never replaced or deleted from here.

The rules live in `components/search_engines/rac_bangs_edit.cc` and are
tested in `rac_search_engines_unittests`.

## The Bangs page

`chrome://settings/bangs`, opened from the Bangs row on the General page's
search engine card. It's its own page because the downloaded list has
thousands of entries, too many to share the site search page. Three lists:

- **Yours**, with Add, Edit and Delete. Deleting asks first, since it
  can't be undone.
- **Bangs list**: the downloaded bangs that match the page's search field,
  at most 100 rows: by name with no search, best match first with one. The
  browser does the matching, so the page never holds the whole list.
  Deleting doesn't ask, since it can be restored.
- **Deleted**, with Restore. A row whose trigger the user's own bang took
  says "Replaced by yours" and can't be restored until that bang is gone.

Rows are keyed by the engine's sync GUID rather than its id.
Row icons come only from the favicons already stored on the Mac; the page
fetches nothing. The browser side does no work until the page opens, and
stops watching the engines when it closes.

## Dev fixture

Dev builds take `--rac-bangs-fixture=<file>`
(`rac/power/bangs-dev-fixture.patch`). The file sets the bangs list (loaded
in place of the download, once the profile's engines have loaded), the
deleted triggers, and the user's own bangs, so the page can be shown in a
known state without clicks. The switch is compiled out of release builds.
Examples are in `devutils/rac/fixtures/bangs/`. Use a fresh profile for
each: the user's own bangs from an earlier run stay in the profile.

## Still open

- **The address bar.** Typing a bang at the end of a query (`cats !w`)
  still shows a search on the default engine as the top suggestion, plus a
  badge for the bang. When a bang is there, the search isn't a search on
  the default engine. The fix isn't just the label: rethink what the
  address bar shows while typing a bang, at the start versus the end, and
  for a bang that doesn't exist.
- How bangs relate to the command bar (phase 5) and to Chromium's keyword
  search, which also uses the address bar.
- Matching must not slow typing in the address bar, even with no bangs in
  use.
