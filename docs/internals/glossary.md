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
  sidebar permanently, above that space's open tabs. They can be loose or
  inside folders. Each one remembers the page it was pinned on and can be
  reset back to it. They are not favorites.
- **Open tabs**: the regular, unpinned tabs in a space.
- **Sidebar**: the vertical panel on the left with favorites, pinned tabs,
  open tabs, and the space switcher. It has two states:
  - **full**: shows titles and icons
  - **hidden**: not shown at all

  Helium's icons-only sidebar ("collapsed" in code) is turned off in rac.
- **Frameless mode**: Helium's mode that hides the sidebar until you hover
  the window edge, while the top bar stays. Cmd+S turns it on and off; it's
  no longer a setting on the Appearance page. The code calls it "zen mode"
  (`helium.browser.zen_mode`).
- **Edge reveal**: moving the mouse to the left edge of the screen to
  temporarily show the full sidebar over the page while it's hidden,
  or to the top edge to show the hidden toolbar.
- **Command bar**: the quick launcher for tabs, history, and actions. ⌘T
  and ⌘L open it; one setting gives ⌘T back to the new tab page.
- **New tab page**: the page that opens in a new tab.
- **Boost**: a user's custom CSS and JavaScript for a specific site.
- **Theme**: the colors of a space, including gradients.
- **Split view**: two or more tabs shown side by side in one window.

## AI concepts

See [ai.md](ai.md) for how these fit together.

- **Assistant**: rac's AI chat. It lives in the **AI sidebar**, the panel on
  the right side of the window, and in the new tab page. The code and the
  settings page call it "Assistant."
- **Provider**: where the AI comes from: an API key, a local model, or an
  installed agent.
- **Agent**: either of two things, so say which. In the UI, an **agent** is a
  coding agent you already have installed (Claude Code, Codex, Cursor, and
  others) that rac runs as a provider. In the code and in ai.md, "the agent"
  is **browser control**: the AI clicking, typing, and opening tabs. A
  direct provider or an installed agent can do browser control.
- **ACP**: the Agent Client Protocol rac uses to talk to installed agents.
- **Plan card**: the card that asks the user to allow the agent to start
  working on the listed sites.
- **Confirmation card**: the card that asks before one consequential step,
  such as a sign-in, a purchase, or sending a form.
- **Safety check** (the **critic** in code): a quick model call that reviews
  each low-risk step against the user's request. It never sees the page.
- **Tab indicator**: the ring and pill on the tab the agent is using, with
  Resume and Stop.
- **Summary card**: the small card that summarizes a link without opening it.

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
