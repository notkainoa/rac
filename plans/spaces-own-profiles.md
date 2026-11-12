# Plan: spaces own their profile (the Arc model)

Status: phase 1 (research and plan). Nothing is built. Branch
`plan/spaces-own-profiles` only; this file never goes to `main`.

Date: 2026-11-12. Base: rac `main` at `3a0ad80c` (Chromium 156, Helium
0.20.1.1).

## The goal

The maintainer's words: "There is no switching-profiles button and no new
window for each profile. We just have spaces, and the user picks which
profile each space uses. It's all managed in Settings or the space
settings."

What a user sees:

- One window shows every space. The dots at the bottom of the sidebar list
  all of them, whatever profile they use.
- Switching to a space that uses another profile switches cookies, logins,
  history, passwords, and extensions with it. No second window appears.
- No profile button, profile menu, or profile picker. Profiles are created,
  renamed, and deleted in Settings, and picked in a space's edit sheet.
- Favorites belong to the profile (as in Arc), so spaces that share a profile
  share favorites. Pinned tabs belong to the space, as today.

This replaces today's model ("each profile opens in its own window, each
profile has its own spaces"). VISION.md lists the Arc model under "not
planned for now", so VISION, the glossary, and the roadmap change with it
(see [Docs](#docs-that-change)).

## How it works today

Short version. File references are in the applied tree
(`build/src`).

**Spaces are per profile.**

- `rac.spaces` (profile pref) holds the list: id, name, icon, theme,
  last active. `SpacesService` is a profile-keyed service.
- `SpacesWindowManager` (profile-keyed) decides which space each window of
  that profile shows. A space is open in at most one window; another window
  pointing at it shows the "open in another window" screen.
- **All of a window's spaces live in one `TabStripModel`.** Each tab carries
  a `SpaceTabTag`. Tabs of other spaces are hidden in the views
  (`owned-tabs.patch` hooks `tab_strip_model.cc`, `tab_container_impl.cc`,
  the layout helpers, and `browser_commands.cc`). A same-profile switch
  moves nothing; it changes visibility.
- A closed window's spaces are saved as snapshots in `<profile>/rac spaces`
  (`SpacesStore`). Live windows rely on Chromium's session restore, with the
  space stored as window and tab extra data (`rac.space`).
- Hidden spaces unload after 15 minutes (proactive discard).
- The sliding-pages switch animation uses recordings of the old sidebar
  page (`SpacePager`), not live views. It does not need both spaces in one
  tab strip.
- About 12,900 lines of rac code across `chrome/browser/rac/spaces`,
  `ui/rac/spaces`, `ui/views/rac/spaces`, `ui/rac/sidebar`.

**Favorites and pinned tabs are per profile.**

- `SidebarItems` (profile-keyed) stores favorites and one pinned list per
  space (`pinned.<space id>`) in the profile pref `rac.sidebar.lists`.
- Favorites are Chromium-pinned tabs, synced into every window of the
  profile by `SidebarWindowSync`.

**Profile UI.**

- The sidebar footer shows Chromium's avatar button (`kFooterOuterControls`
  in `sidebar_header_view.cc`, UI lead's area). It opens the stock profile
  menu, which lists other profiles, Add profile, and Manage profiles. Picking
  another profile opens that profile's window.
- Also reachable: the Profiles menu in the menu bar
  (`main_menu_builder.mm`, `profile_menu_controller.mm`), profile items in the
  Dock menu, Cmd+Shift+M, the profile picker at launch (two or more profiles
  and the "show on startup" pref), "Open link in profile" in the page context
  menu, Helium's show-avatar toolbar setting, and Settings → People →
  manage profile (name and avatar).

**Arc importer (Data lead's area).** Each non-default Arc profile becomes a
new rac profile, holding all of that Arc profile's spaces, favorites, and
cookies. The default Arc profile goes into the profile the import started
from. `RealArcImportBackend::OpenProfile` then opens a window for each new
profile. So the importer already knows each Arc space's profile; today it
just can't express "this space uses that profile" in one window.

**AI (Core lead's area).** Everything is per profile: `rac.ai.enabled`,
provider, encrypted API keys, agent choice, permission level, site rules,
saved prompts, history file. `AiServiceFactory` returns null when a
profile's AI is off. Installed agents (Claude Code, Codex) sign in through
the user's real `HOME`, so their logins are shared already. The assistant
page and `WindowAssistant` are per window.

**Settings.** Every rac pref except updates and the keychain flags is a
profile pref: layout, address bar in the sidebar, command bar, Cmd+S
behavior, the Helium defaults rac overrides (frameless mode, minimal
address bar, MRU cycling), AI, and spaces themselves.

**Chromium facts that shape the design** (from reading the 156 tree):

- A tab's `WebContents` is bound to one profile forever
  (`NavigationControllerImpl::browser_context_` is const). Moving a tab to
  another profile means reopening its URL there.
- A `Browser` belongs to one profile. Around 920 window-level
  `GetProfile()` calls in `chrome/browser/ui` assume that: omnibox
  suggestions, the extensions toolbar and extension tab APIs, downloads,
  bookmarks, session saving, navigation of new tabs.
- Hiding a browser window on Mac (`orderOut`) suspends its compositor and
  marks its tabs hidden immediately, the same as a background tab.
- A profile unloads when its last browser window closes
  (`kDestroyProfileOnBrowserClose` is on for Mac). Each `Browser` holds a
  keep-alive.
- At launch, Chromium synchronously loads every profile that had a window
  open at quit (`GetLastOpenedProfiles`), and each restores its own session.
- Each fullscreen window on macOS is its own macOS Space.

## The hard part, and three ways to do it

Chromium can't put tabs from two profiles in one window's tab strip without
breaking things. These are the realistic options.

### A. Stacked profile windows (recommended)

**How it works.** A "rac window" is a small group of real Chromium browser
windows, one per profile it has used, stacked at the same frame. Only the
one whose profile owns the current space is on screen. The others are
ordered out: no painting, tabs hidden, like background tabs.

- Switching to a space with the **same** profile works exactly as today.
- Switching to a space with **another** profile: if this rac window already
  has that profile's browser, rac gives it the same frame and window state,
  orders it in just below the current one, waits for its first frame, then
  orders the current one out. If not, rac loads the profile (async), creates
  its browser hidden, shows the space, then swaps.
- The space list moves from each profile to one browser-wide list in Local
  State, with a profile on each space. Each member browser's sidebar shows
  the whole list.
- Everything else stays per profile and keeps working unchanged: the tab
  strip, favorites, pinned tabs, session restore, extensions, downloads,
  passwords, history, the omnibox, devtools, split view.
- A standby browser keeps its profile loaded. After it has been hidden for
  15 minutes (the same timer that unloads hidden spaces), rac snapshots its
  spaces to the existing `rac spaces` store and closes it, so the profile
  unloads. **A profile no visible space uses costs nothing.**
- This is Arc's observable behavior. Nobody has published how Arc does it;
  it's built on Chromium too, and swapping per-profile content behind one
  frame is the likely shape.

**Upstream hunks.** Roughly 20–30 small hooks in about 15 upstream files.
Everything else is new rac files.

| Hook | File | Why |
| --- | --- | --- |
| Load only the visible profiles at launch | `profile_manager.cc` (`GetLastOpenedProfiles`) or `chrome_browser_main.cc` | Idle profiles cost nothing; startup gets faster than today |
| Restore a standby member hidden into its group | `session_restore.cc` (`ShowBrowser`) | Otherwise a lazily loaded profile pops up a second visible window |
| A hidden member asked to show itself becomes a space switch | `browser_view.cc` (`Show`/`Activate`) | Notification clicks, extensions, and "open link" all activate windows |
| Skip standby browsers when picking a window for new tabs | `profile_browser_collection.cc` (`FindTabbedBrowser`) | Otherwise links open into a hidden window |
| Closing the visible member closes the group | rac's existing `OnWindowClosing` hook in `browser_view.cc` | One window to the user |
| Retiring a standby isn't a "closed window" in History | `tab_restore_service_helper.cc` or `browser_live_tab_context.cc` | No phantom Recently Closed windows |
| Remove profile UI | `main_menu_builder.mm`, `app_controller_mac.mm` (Dock), `accelerator_table.cc` and `global_keyboard_shortcuts_mac.mm` (Cmd+Shift+M), `render_view_context_menu.cc` (open link in profile → open in space), `profile_picker.cc` (never show at launch) | No profile switcher anywhere |
| Fullscreen handoff | `native_widget_ns_window_bridge.mm` or a rac `.mm` file using the window directly (see risk) | Each fullscreen window is its own macOS Space |

**Risks.**

- **Fullscreen.** When the visible member is fullscreen, the incoming one
  can't just be ordered in; it would land on the desktop. Two candidate
  fixes, neither proven: show the incoming member as a full-screen-sized
  auxiliary window inside the current fullscreen Space (Chromium does this
  for tab dragging, `SetCanAppearInExistingFullscreenSpaces`), or use
  AppKit native window tabs with the tab bar hidden (Chromium turns window
  tabbing off globally and overrides the titlebar, so this fights upstream).
  **The spike must settle this first.**
- **First switch to a cold profile** waits for the profile to load
  (extensions start, history opens). Unmeasured; the spike measures it.
- **Things that track one specific window lose it on a cross-profile
  switch,** because it's a different macOS window: sharing a single window
  in Zoom or Meet, tiling window managers (yabai, AeroSpace), Stage Manager
  grouping. Sharing the whole screen is unaffected.
- **Sheets** (file pickers, permission sheets) must close before a member is
  ordered out; AppKit loses sheets on hidden windows (crbug 667602).
- Window-level state has to be copied to the incoming member on every swap:
  frame and display, frameless mode, sidebar width, AI panel open and width.

**Performance.** Same-profile switching: unchanged. Startup: faster than
today for anyone with several profiles, since only the visible spaces'
profiles load. Cross-profile switch, warm: one window order change plus one
frame, target under 50 ms. Cross-profile, cold: profile load time (measure).
Standby members: memory only, no painting, retired after 15 minutes.

### B. Containers: one profile, one cookie jar per space

**How it works.** Keep a single profile. Give each space's tabs their own
storage partition (cookies, local storage, cache), the way `<webview>`
guests and isolated web apps do (`SiteInstance::CreateForFixedStoragePartition`).
One real tab strip, so no window swapping. This is what Zen (Firefox
containers) and SigmaOS do.

**Upstream hunks.** About 8–12, but in the riskiest code in the browser:
a `content/` change so `target=_blank` popups don't escape to the default
cookie jar (`WebContentsImpl::CreateNewWindow`), new-tab and tab-restore
hooks, session cookies (non-default partitions drop them on restart), the
`chrome.cookies` API, the password manager's network context, and Clear
browsing data. Any miss leaks cookies across spaces.

**What it doesn't give.** Separate history, passwords, autofill,
extensions, site permissions, or bookmarks. That is not what the
maintainer asked for ("cookies, logins, history, extensions"). Existing
users' profiles also can't be turned into containers without merging their
data, which risks loss.

**Verdict:** don't. Worth knowing as a possible future "quick identity"
add-on for one space, nothing more.

### C. One tab strip holding several profiles' tabs

**How it works.** Let one browser window hold tabs from several profiles.

**Why not.** Nothing stops it at insert time, but about 920 window-level
code paths would quietly use the window's profile for another profile's
tab. Concrete failures: profile B's tabs visible to profile A's extensions
(and invisible to B's), omnibox suggestions from the wrong history, new
tabs from a B page opening as A, B's tabs saved in A's session and restored
as A, B's downloads never shown. That's a privacy failure and a fork of
the whole browser UI layer, hundreds of upstream hunks.

**Verdict:** rejected.

### Also rejected: one native window hosting several browsers' views

Moving a `BrowserView` between native windows would fork Chromium's frame
and widget code. Same idea as A with far more upstream surface.

## What breaks or changes, with A

| Area | What happens | Fix |
| --- | --- | --- |
| Extensions | Per profile. The toolbar shows the space's profile's extensions. A standby window is listed by its own profile's `chrome.windows` | None; matches Arc. Verify `windows.update({focused})` becomes a switch |
| Downloads | Per profile. A download started in a work space shows in work spaces only | None; matches Arc |
| Incognito | Cmd+Shift+N opens an incognito window for the current space's profile, as its own window, as today | None |
| Passwords, keychain | Per profile. All profiles already share rac's one Keychain key | None |
| DevTools | Docked: fine. An undocked DevTools window stays on screen when its profile goes standby | Leave it; it's inspecting a live tab |
| Split view | Only tabs in the same tab strip, so only same-profile tabs. Cross-profile split is impossible | Filter menus; say why if asked |
| Move a tab to a space with another profile | Can't move a `WebContents`. Reopens the URL in the other profile; page state and logins don't follow | Arc-style warning with "Don't ask again" |
| Drag a tab onto another profile's space | Same as above | Same |
| Session restore | Each profile restores its own windows. Standby members restore hidden into their group, and only when their profile loads | Two hooks (launch filter, hidden restore) |
| Crash | A standby member's tabs are in its profile's session; they come back when that profile next loads | None |
| Fullscreen | See risks | Spike |
| AI | Would switch provider and history with the space, since it's all per profile | Decision 4 |
| Settings | Every rac and Helium look-and-feel pref is per profile, so they'd change with the space | Decision 3 |
| "Open link in profile X" | Gone | Becomes "Open link in space…" |
| Links from other apps, little window | Open in the profile of the last active space (Arc does this) | Little window picks the profile from the space |
| Screen sharing one window, window managers | Lose the window on a cross-profile switch | Document |

## Migration

rac is the maintainer's daily driver. Nothing may be lost, and the old data
stays readable.

1. **Back up first.** Before touching anything, run the existing
   `data-backups` snapshot for every profile (`rac.spaces`,
   `rac.sidebar.lists`). Never delete the old per-profile `rac.spaces`
   pref; the new code just stops reading it after migration.
2. **Build the one space list.** For each profile in the profile list, read
   its spaces. Loaded profiles read their prefs; profiles not loaded have
   their `Preferences` file read once, read-only, on a background thread,
   so migration doesn't load every profile. Each space keeps its id, name,
   icon, and theme, and gets `profile = <that profile's folder>`. Order:
   the last-used profile's spaces first, then the other profiles in profile
   list order, each keeping its own order. Mark done in Local State.
3. **Profiles with no spaces** (never opened since spaces shipped) get no
   space. They show in Settings and can be picked for any space.
4. **Pinned tabs and favorites don't move.** Pinned lists are keyed by
   space id inside the space's own profile, which is still right.
5. **Open windows.** On the first launch after the update, every window
   that was open comes back as its own rac window (Chromium restores each
   profile as usual, one last time). Each can now show any space. Nothing
   is merged or moved; the user closes extra windows when they like. From
   the next launch on, only visible spaces' profiles load.
6. **Arc import records** stay where they are (per profile). Re-running an
   import keeps working; it now adds spaces to the one list.
7. **Downgrade.** An older rac ignores the Local State list and reads the
   untouched per-profile prefs, so it still works (spaces added after the
   update won't appear in it).
8. Test the migration against fixture profiles only, never a real profile
   folder.

## Decisions for the maintainer

Recommendation first in each.

1. **Approach.** Stacked profile windows (A). Containers don't separate
   history or extensions; a mixed tab strip leaks between profiles.
2. **Favorites.** Per profile, like Arc. Spaces that share a profile share
   favorites. (Per space or global would mean reopening favorites in each
   profile.)
3. **Which settings follow the space.** Look and behavior are the same
   everywhere (layout, sidebar, address bar, command bar, Cmd+S, frameless
   mode, MRU cycling, picture-in-picture). rac keeps them in step across
   profiles. Privacy, passwords, site permissions, downloads folder, and
   search engine stay with the profile, and Settings shows which profile
   you're editing. (Alternative: search engine shared too.)
4. **AI.** Set up once, works in every space: on/off, provider, keys,
   agent, permission level. Chat history and per-site rules stay with the
   profile. (Core lead builds it.)
5. **Changing a space's profile.** Ask first, then reopen the space's open
   tabs in the new profile and move its pinned tabs over. Logins don't come
   along.
6. **Moving a tab to another profile's space.** Allowed, with Arc's warning
   ("you might get logged out") and a "Don't ask again".
7. **Deleting a profile that spaces use.** Settings lists those spaces and
   asks: move them to another profile, or delete them too. The last profile
   can't be deleted. Back up first.
8. **New spaces** use the current space's profile. The edit sheet has a
   Profile row with "New profile…".
9. **Showing the profile in the sidebar.** Nothing on the dots. The
   profile's name shows in the space's edit sheet and right-click menu.
10. **Keep the old layout as an option?** No. One model. Build it behind a
    hidden dev switch, flip it on when you've used it for a while, then
    delete the old path.
11. **Windows open at update time.** Keep each as its own window the first
    time. No merging.
12. **Hidden profiles.** Close a profile's hidden window after 15 minutes
    unused (same as space unloading) so the profile unloads.
13. **First switch to an unloaded profile.** The dot moves right away; the
    window swaps when the profile is ready. No pre-loading.
14. **Links from other apps and the little window.** Use the profile of the
    last active space, like Arc.
15. **Where profiles are managed.** A "Spaces and profiles" section on
    Settings → General (create, rename, avatar, delete, which spaces use
    each), plus the Profile row in the edit sheet. Settings → People goes
    away.
16. **Docs.** Approve rewriting VISION.md's "Profiles, spaces, and tabs"
    section and the glossary for the new model.

## Size and order

About 12 PRs, after a spike. Rough effort: 3–5 weeks of agent time. The
riskiest parts (fullscreen, session restore) are early.

0. **Spike (not merged).** Two profiles, one stacked window, a hard-coded
   cross-profile switch. Measure: warm swap time and any flash, cold
   profile load time, standby memory, fullscreen behavior with both
   candidate fixes, Stage Manager and multiple displays. Results go back
   into this plan before PR 1. Builds on the Pro.
1. **One space list.** `Space` gets a profile; the list moves to Local
   State; migration and backups; unit tests. Each window still shows only
   its own profile's spaces, so nothing visible changes.
2. **Stacked windows.** The group object, standby members, swap, copying
   window state, closing the group, show/activate becomes a switch. Behind
   the dev switch.
3. **Switch across profiles.** The switcher shows every space; cold
   profile loading; retiring standby members.
4. **Launch and restore.** Load only visible profiles; restore standby
   members hidden; quit and crash tests.
5. **Fullscreen**, using whatever the spike proved.
6. **Space ↔ profile.** Profile row in the edit sheet, new-space default,
   change-profile flow (reopen tabs, move pinned list), move tab to another
   profile's space, "Open link in space…".
7. **Settings.** "Spaces and profiles" section; profile create, rename,
   delete flow.
8. **Remove the profile switcher.** Footer avatar, profile menu, menu bar
   Profiles menu, Dock items, Cmd+Shift+M, profile picker, Helium's avatar
   toolbar setting (hidden by a rac hook, not by editing Helium).
9. **Shared settings.** Keep look-and-behavior prefs in step across
   profiles (decision 3).
10. **AI set up once** (decision 4). Core lead.
11. **Arc import keeps Arc's profile per space**, no new windows. Data lead.
12. **Turn it on.** Flip the default, delete the per-profile-window path,
    update docs.

### Changes in other leads' areas

- **UI lead.** Sidebar footer loses the avatar (`kFooterOuterControls`,
  `footer_fit.h` and its test, the `top_bar.cc` slot that uses the avatar's
  place for Chat). Switcher lists every space. Edit-space sheet gains a
  Profile row. The space pager hands its recording to the incoming window
  so a cross-profile switch can still slide.
- **Core lead (AI).** AI setup becomes browser-wide; chat history stays per
  profile; the AI panel's open state and width copy across a swap. An agent
  run stays inside the profile it started in.
- **Data lead (importer).** Create the space with the Arc profile's rac
  profile instead of opening a window for it; the record maps Arc profiles
  to rac profiles; undo no longer fans out per window.
- **Little window and command bar.** Pick the profile from the last active
  space instead of the last-used profile.

## Docs that change

- `VISION.md` lines 64–70 ("Each profile opens in its own window", "Each
  profile has its own spaces", favorites "in a profile") and lines 131–133
  (the "maybe later" Arc layout).
- `docs/internals/glossary.md` Profile, Space, Favorites.
- `docs/roadmap.md` line 73 and lines 157–163.
- `docs/internals/pinned-tabs.md` (favorites per profile still right;
  windows wording changes).
- New `docs/internals/spaces-and-profiles.md`: the stacked windows, why
  not containers, the hooks, the traps (sheets, fullscreen, standby
  retirement).

## Sources

- rac code: `patches/rac/spaces/`, `patches/rac/pinned/`,
  `patches/rac/cleanup/footer-switcher-first.patch`,
  `patches/rac/import/`, `patches/rac/onboarding/arc-import-*`,
  `patches/rac/ai/`, `patches/rac/agent/`, `patches/rac/storage/`.
- Chromium 156: `browser_view.cc` (`Show`/`Hide`),
  `native_widget_ns_window_bridge.mm`, `native_widget_mac_ns_window_host.mm`,
  `profile_manager.cc`, `browser_features.cc`
  (`kDestroyProfileOnBrowserClose`), `session_service.cc`,
  `tab_drag_controller.cc`, `site_instance.h`, `web_contents_impl.cc`
  (`CreateNewWindow`), `extension_tab_util.cc`.
- Arc behavior: third-party write-ups (Arc's own help pages were not
  reachable): alexandergoller.com/journal/14870/arc-browser,
  talk.macpowerusers.com/t/arc-browser-spaces-and-profiles/35872, the
  Arc-clone PR quoting Arc's cross-profile move warning
  (github.com/MartinPTielemans/browser/pull/112). Arc is in maintenance
  mode.
- Chromium: issues.chromium.org/issues/40896879 (per-tab profiles request;
  storage partitions suggested instead).
