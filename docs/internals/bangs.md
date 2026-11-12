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
- A bang works at the start, middle or end of the query: `!w cats`,
  `ca !w ts`, `cats !w`. Helium's `SplitKeywordFromInput` looks only at the
  first `!` in the input, and only when whitespace comes before it, so
  `wow! cats !w` has no bang (its first token, `wow!`, is the keyword) and
  in `cats !w !wa` the `!wa` is part of the query.

## The address bar

Patch: `rac/power/bangs-omnibox.patch`.

While the user types, Chromium turns exact keyword matching off, so a
typed `w cats` doesn't jump to the `w` engine. That also meant no
suggestion searched a bang's engine: `cats !w` showed a search on the
default engine, with the bang only as a badge.

`KeywordProvider` now makes one extra suggestion when exact matching is off
and the keyword starts with `!`: the bang's engine searching the rest of
the input. It ranks above the default engine's search, so it's the top
row and Enter or a click searches the bang's engine. Its transition is
`GENERATED`, not `KEYWORD`. A `KEYWORD` default match makes the address
bar turn the keyword into a chip, and nearly every short bang is the
start of a longer one, so typing `cats !wa` would have chipped `!w` and
put the `a` in the query.

Deleted and unknown bangs aren't engines, so they fall through to a plain
search. Keywords without `!`, keyword mode, and the command bar (which
allows exact matching) are unchanged. Input with no `!` does no extra
work.

The classifier is unchanged on purpose. `AutocompleteClassifier` turns
text into one match for the context menu's "Search <default engine> for",
paste and go, text dropped on the tab strip, and paste into a new tab. It
omits asynchronous matches, and the bang suggestion requires that they
aren't omitted, so those still search the default engine with the text as
it is. The context menu names the default engine, so it must not open
another one.

The rules are tested in `rac_omnibox_unittests`
(`chrome/browser/rac/power`).

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

- **How the bang row looks.** It still carries Helium's keyword hint (the
  badge) and reads "cats · Wikipedia Search", and the default engine's
  search stays second with its suggestions. Whether to drop the badge,
  reword the row, or hide the default row is a design call; dropping the
  badge also removes Helium's "space after `!w` makes a chip" and "Return
  accepts the hint" paths.
- How bangs relate to the command bar (phase 5) and to Chromium's keyword
  search, which also uses the address bar.
- Matching must not slow typing in the address bar, even with no bangs in
  use.
