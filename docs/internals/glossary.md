# Glossary

Use these words consistently in code, docs, issues, and PRs.

## People

- **The maintainer**: the person who runs rac and decides what gets merged.
- **Contributor**: anyone sending a change, whether written by hand or with
  AI.
- **User**: someone using rac as their browser.
- **You** (in `AGENTS.md`): the AI agent reading the instructions.

## Browser concepts

- **Profile**: a separate set of logins, cookies, history, and settings. Each
  profile opens in its own **profile window**, as in Helium.
- **Space**: a set of tabs inside a profile, with its own color theme and
  icon. Each profile has its own spaces.
- **Space switcher**: the dots at the bottom of the sidebar that switch
  between spaces.
- **Favorites**: site icons at the top of the sidebar, shared by every space
  in a profile. Helium calls these "pinned." In rac, they're "favorites."
- **Pinned tabs**: Arc-style tabs that belong to one space and stay in its
  sidebar permanently, above that space's open tabs. They are not
  favorites.
- **Open tabs**: the regular, unpinned tabs in a space.
- **Sidebar**: the vertical panel on the left with favorites, pinned tabs,
  open tabs, and the space switcher. It has three states:
  - **full**: shows titles and icons
  - **compact**: shows icons only (Helium's "collapsed")
  - **hidden**: not shown at all
- **Edge reveal**: moving the mouse to the left or top edge of the screen to
  temporarily show the hidden sidebar or toolbar.
- **Command bar**: the quick launcher for tabs, history, and actions. Users
  can choose it in place of the new tab page.
- **New tab page**: the page that opens in a new tab.
- **Boost**: a user's custom CSS and JavaScript for a specific site.
- **Theme**: the colors of a space, including gradients.
- **Split view**: two or more tabs shown side by side in one window.

## AI concepts (provisional)

AI design isn't decided yet (see [ai.md](ai.md)). These words are placeholders
until it is:

- **AI sidebar**: the AI panel on the right side of the window.
- **Agent**: AI that takes actions in the browser, such as clicking, typing,
  or opening tabs.
- **Provider**: where the AI comes from: an API key, a local model, or an
  existing subscription such as Claude Code or Codex.

## Project and build

- **Upstream**: the projects rac builds on. The direct upstream is
  [helium-macos](https://github.com/imputnet/helium-macos).
- **Helium core**: [imputnet/helium](https://github.com/imputnet/helium), the
  platform-independent part of Helium, included as the `helium-chromium/`
  submodule.
- **Layer**: one set of patches in the build: Chromium, then
  ungoogled-chromium, then the Helium core, then Helium macOS, then rac. See
  [overview.md](overview.md).
- **Patch**: a diff applied to the Chromium source. rac patches live in
  `patches/rac/`.
- **Series**: a `series` file listing patches in the order they're applied.
- **Patch group**: the patches for one rac feature, in one folder such as
  `patches/rac/spaces/`.
- **Sync**: merging a new helium-macos release into rac and refreshing rac's
  patches. See [upstream-sync.md](../operations/upstream-sync.md).
- **`he`**: the dev command from `dev.sh` (Helium's name; rac keeps it).
