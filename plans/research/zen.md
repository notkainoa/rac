# Zen Browser: research dossier

Research date: 2026-10-25. I read the code of `zen-browser/desktop` at commit
`9b604fe` (2026-10-25) and of its build tool `zen-browser/surfer` at `b3fc8ab`
(2026-10-20). Both are shallow clones at `/tmp/rac-overhaul/src/zen` and
`/tmp/rac-overhaul/src/surfer`. Paths below that start with `zen/` or `surfer/`
are relative to those clones, and `:N-M` gives line numbers.

Tags: **FACT** means a primary source (code, GitHub API, an official doc or
release note). **CLAIM** means a vendor's or third party's own report.
**INFERENCE** means my reasoning.

Terms: Zen's **Essentials** are rac's **favorites**. Zen's **pinned tabs** are
rac's **pinned tabs**. A Zen **space** (code: "workspace") is a rac **space**.

## In plain English

Zen is a free, open-source browser built on Firefox. It copies Arc's layout.
Tabs sit in a left sidebar. Spaces slide sideways when you switch. Favorite
sites, called Essentials, sit in a grid at the top. Two extras stand out.
Glance opens a link in a floating preview when you Option-click it. Compact Mode
hides the sidebar until you point at the edge. Zen has no AI, on purpose. One
developer writes most of the code. A new version ships about every five days.
Each new Firefox arrives within days. Users love the look and the calm feel.
They complain about lost tabs after updates, slowdowns, and a feature that
mirrored every window without asking. For rac, four lessons stand out. They are
automatic tab backups, the link preview, forgiving sidebar hover, and a routine
for keeping up with upstream.

## Snapshot

| Field | Value | Tag and source |
| --- | --- | --- |
| What it is | Arc-style desktop browser: vertical tabs, spaces, Essentials, Glance, split view, Compact Mode, Boosts, CSS "Mods". No AI. | FACT: `zen/prefs/zen/*.yaml`, `zen/src/zen/` |
| Engine | Gecko. Stable is Firefox 158.0.1. On 2026-10-25 the `dev` branch synced the Firefox 159.0 release candidate: its `surfer.json` keeps `version: 158.0.1` and sets `candidate: 159.0`, build 1. | FACT: `zen/surfer.json:6-11`; `surfer.json` on the `stable` branch via GitHub API; commit bc8e7ed "Sync upstream Firefox to version `159.0`" (gh-16147) |
| Platforms | macOS universal DMG (x86_64 + arm64), Windows x64 and arm64, Linux x64 and arm64 (tarball, AppImage, Flatpak). | FACT: assets of release 1.23.4b via `gh api repos/zen-browser/desktop/releases/latest` |
| License | MPL-2.0. No source file is marked "Incompatible With Secondary Licenses". | FACT: `zen/LICENSE`; grep of the tree |
| Repo | github.com/zen-browser/desktop (default branch `dev`) | FACT |
| Stars, forks | 45,275 stars, 1,899 forks, 3,641 discussions, 808 open issues + PRs (76 PRs) on 2026-10-25 | FACT: GitHub API |
| Age | Repo created 2024-03-28. First public alpha 2024-07-07. Still labelled beta ("1.23.4b"). | FACT: GitHub API, releases list |
| Release cadence | 67 stable releases in the 12 months to 2026-10-25, about one every 5.4 days (4 to 8 a month). "Twilight" nightly-style build every 2 days. | FACT: releases API; `zen/.github/workflows/twilight-release-schedule.yml:4-5` (`cron: "0 23 */2 * *"`) |
| Team size | One lead (GitHub `mr-cheffy`, the founder's current account; the founder previously used `mauro-balades`): 5,909 of 6,951 all-time commits (85%) and 293 of 482 commits in the last 6 months (61%). 14 public org members, 258 contributors. `CODEOWNERS` lists only `@mr-cheffy`. | FACT: contributors and commits APIs; `zen/CODEOWNERS`. Account link: INFERENCE from issue #7000 comments |
| Business model | Donations (Patreon, Ko-fi). Blacksmith (CI runners) listed as partner. No paid tier, no ads, no accounts. | CLAIM: https://zen-browser.app/donate ; FACT: `zen/README.md` "Partners" |
| Reach (proxy) | 30.3 M release-asset downloads all-time. In the 4 days after 1.23.4b: Windows update file 184,030, macOS 63,277, Linux 16,167 downloads. macOS DMG all-time 3.0 M. | FACT: releases API. Treating update-file downloads as active installs is INFERENCE |

## Features

Status: **shipped** = in a stable release; **beta** = Twilight or `dev` only, or
off by default; **planned** = stated but not built; **no** = absent or refused.

### Tabs, sidebar, spaces

| Feature | Status | Details | Source |
| --- | --- | --- | --- |
| Vertical tab sidebar, left or right | shipped | `zen.tabs.vertical.right-side`. Expanded (titles) or collapsed (icons only) states. Max width 500 px, min 163 px, drag to resize. | FACT: `zen/prefs/zen/zen.yaml`, `view.yaml`; `zen/src/zen/tabs/zen-tabs/vertical-tabs.css:552` |
| Single toolbar (address bar inside the sidebar) | shipped, default | `zen.view.use-single-toolbar: true`. Shows domain only in the sidebar. | FACT: `zen/prefs/zen/view.yaml`, `zen-urlbar.yaml:20` |
| Spaces | shipped | Name, emoji icon, gradient theme. Each space can be bound to a Firefox **container**, which is a separate cookie jar. Switch by trackpad swipe, Ctrl+scroll, keyboard, or footer icons. Wrap-around on by default. | FACT: `zen/prefs/zen/workspaces.yaml:17-41`; `zen/src/zen/spaces/` |
| Swipe edge actions | shipped (1.23b) | Swiping past the last space starts a new space. Swiping past the first opens the Library. | FACT: `zen/src/zen/spaces/ZenSpacesSwipe.mjs:247-263` |
| Essentials (rac favorites) | shipped | Up to 12, shown as a favicon grid. Separate sets per container (`zen.workspaces.separate-essentials: true`). | FACT: `zen/prefs/zen/zen.yaml:14`, `workspaces.yaml:38` |
| Pinned tabs per space | shipped | Remember their pinned URL. Cmd+W behavior has 6 options; default `reset-unload-switch` (reset to pinned URL, unload, switch away). "Edit pinned tab" since 1.21.4b. Pinned tabs restore on demand at startup. | FACT: `zen/src/zen/tabs/ZenPinnedTabManager.mjs:357-452`; `zen/prefs/zen/workspaces.yaml:57`; `zen/prefs/firefox/browser.yaml:8` |
| Folders | shipped (1.15b) | Nested, max 5 levels. Hover-to-search after 500 ms. Collapse all pinned tabs by clicking the space name (1.18b). | FACT: `zen/prefs/zen/folders.yaml`; release notes |
| Live folders | shipped (1.19b) | Auto-refreshing folders from RSS/Atom or GitHub (your PRs or assigned issues). Default refresh 30 min. The GitHub provider scrapes github.com pages with your cookies; there is no API token. | FACT: `zen/docs/live-folders-specs.md`; `zen/src/zen/live-folders/providers/GithubLiveFolder.sys.mjs:16-17,404` |
| Tab rename, custom tab icon | shipped (1.18b) | | FACT: release notes; `zen/src/zen/tabs/ZenTabRenamer.mjs` |
| Close on Back with no history | shipped | Back on a tab with no history closes it (Arc behavior). | FACT: `zen/prefs/zen/zen.yaml:47` |
| "Clear" unpinned tabs button | shipped | | FACT: `zen/prefs/zen/view.yaml` (`show-clear-tabs-button`) |
| Unload tabs / "Unload all spaces except current" | shipped (1.19.3b) | Unloaded tabs fade out. | FACT: release notes; `zen/prefs/firefox/browser.yaml:14-17` |
| Window sync (every window mirrors the same spaces and tabs) | shipped (1.18b), on by default | One live page per tab. Selecting a tab moves its page into the focused window; other windows show a dimmed preview. Option "sync only pinned tabs". "New blank window" (Cmd+Shift+N) is unsynced and temporary. No settings toggle to turn sync off; only `about:config`. | FACT: `zen/src/zen/sessionstore/ZenWindowSync.sys.mjs:41-70,749-910`; https://docs.zen-browser.app/user-manual/window-sync ; `zen/src/browser/components/preferences/zenTabsManagement.inc.xhtml:25` |
| Space routing (Arc's Air Traffic Control) | shipped (1.21b) | Rules of type "contains", "equal-to" (ignores the protocol) or case-insensitive regex send URLs to a space. Context menu "Add route for domain". External links routed at startup (1.23.4b). | FACT: `zen/src/zen/space-routing/ZenSpaceRoutingManager.sys.mjs:487-516` |
| Library panel | shipped (1.23b) | Arc-style panel: history, downloads (with speed), media files from Downloads/Documents/Pictures, spaces, boosts, space routing. Opt+Shift+L or swipe. | FACT: `zen/src/zen/library/sections/`; release notes |
| Sidebar media controls | shipped (1.21.11b) | Several players at once. A minimized picture-in-picture window collapses into the sidebar player. | FACT: `zen/src/zen/media/ZenMediaController.sys.mjs`; issue #14710 |
| Horizontal tabs | no | Top request in 2024 (253 votes). Thread locked as "too heated". | FACT: discussion #889 |
| Auto-archive idle tabs | no | 234 votes, open. A user calls it Arc's "killer feature" (2026-10-24). | FACT: discussion #2326 |
| Per-space profiles | no (containers only) | 223 votes, open. One user left for Phi Browser over it. | FACT: discussion #2337 |

### Navigation and command bar

| Feature | Status | Details | Source |
| --- | --- | --- | --- |
| Floating address bar | shipped, default | `zen.urlbar.behavior: floating-on-type`. Cmd+T opens the floating bar instead of a new tab page (`replace-newtab: true`). Typed text survives 45 s. | FACT: `zen/prefs/zen/zen-urlbar.yaml:5,14,17` |
| Command actions in the address bar | shipped (grew 1.22.2b to 1.23.2b) | About 40 declarative actions: compact mode, theme picker, library, split, new space or folder, copy URL, pin, reset pinned tab, duplicate, reopen closed, theme scheme. Each has `l10nId`, `command`, `icon`, `isAvailable`. `@actions`, `@spaces`, tabs and folders search. | FACT: `zen/src/zen/urlbar/ZenUBGlobalActions.sys.mjs:36-340` |
| Command ranking that learns | shipped | Per-command score from -5 to +5 stored in one pref (`zen.urlbar.suggestions-learner`). | FACT: `zen/src/zen/urlbar/ZenUBResultsLearner.sys.mjs:12-13` |
| Keyboard shortcut editor | shipped | GUI editor with conflict warnings; option to disable all Zen defaults. Stored in `zen-keyboard-shortcuts.json`. (A 2026 review says shortcuts need `about:config`; the code shows otherwise.) | FACT: `zen/locales/en-US/browser/browser/preferences/zen-preferences.ftl:119-120,201-205`; `zen/src/zen/kbs/ZenKeyboardShortcuts.mjs:697` |
| Command-line flags | shipped (1.18.6b, 1.23.3b) | `--space <name or UUID> [url]`, `--blank-window [url]`. | FACT: `zen/src/browser/components/BrowserContentHandler-sys-mjs.patch:19-81` |
| Drag the window from the top of a page | shipped (1.21.11b) | Top 5% of the page acts as a title bar. | FACT: `zen/prefs/zen/view.yaml` (`drag-window-from-content.height-percentage: 5`) |

### Split view, peek, small windows

| Feature | Status | Details | Source |
| --- | --- | --- | --- |
| Split view | shipped | Up to 4 tabs. Layouts: side by side, stacked, grid, with a resizable layout tree. Ways in: drag a tab onto the page (500 ms hover), hover a tab over a tab for 1 s, Opt-click a tab, context menu "Join tabs", command bar. | FACT: `zen/src/zen/split-view/ZenViewSplitter.mjs:87,1639-1660`; `zen/prefs/zen/split-view.yaml:20-23`; release notes 1.19b, 1.19.9b |
| Glance (peek) | shipped | Opt-click a link (configurable: Ctrl, Alt, Shift, Cmd). Opens a live page over the current one at 80% width. Buttons to close, expand to a full tab, or split. Clicks that drag more than 4 px are ignored. Context-menu search results and external links clicked inside Essentials open in Glance. | FACT: `zen/prefs/zen/glance.yaml:5-20`; `zen/src/zen/glance/actors/ZenGlanceChild.sys.mjs:29,160`; `zen/src/zen/glance/ZenGlanceManager.mjs:816` |
| Mini window for outside links (Arc's Little Arc) | no | | FACT: no such code |
| Picture-in-picture | shipped (inherited) | Zen adds "minimize into sidebar". | FACT: `zen/src/toolkit/components/pictureinpicture/*.patch` |

### Import, sync, profiles

| Feature | Status | Details | Source |
| --- | --- | --- | --- |
| Import from Chrome, Safari, Edge, etc. | shipped (inherited) | Firefox migrator. Zen turns imported bookmarks into pinned folders, capped at 250 tabs. | FACT: `zen/prefs/zen/migration.yaml` |
| Arc and Dia import | beta (merged to `dev` 2026-10-24) | Arc: reads `~/Library/Application Support/Arc/StorableSidebar.json` and maps containers to spaces, `topAppsContainerIDs` to Essentials, `["pinned", id, "unpinned", id]` pairs to pinned tabs and folders, `savedURL`/`savedTitle`, emoji (`emoji_v2` or code point) and theme colors. Web data (history, passwords via "Arc Safe Storage" keychain) goes through the Chrome importer. Dia: "pinned tabs are kept in an encrypted database and cannot be imported." | FACT: `zen/src/zen/migration/ZenProfileMigrators.sys.mjs:16-124`; `ZenMigrationUtils.sys.mjs:88,131,244-330`; commit gh-16130 |
| Firefox Sync (bookmarks, history, passwords, add-ons, prefs) | shipped (inherited) | Needs a Mozilla account. End-to-end encrypted; data on Mozilla's servers. | FACT: Firefox design; CLAIM: https://zen-browser.app/privacy-policy/ |
| Spaces sync across devices | shipped (1.22b); opt-in on stable, default on in Twilight | A custom Firefox Sync engine named "Spaces", version 3. Record kinds: container, space, tab, folder, split, layout. Normal (unpinned) tabs only if `zen.spaces-sync.normal-tabs`. An engine wipe never deletes local data. | FACT: `zen/src/zen/sync/ZenSpacesSync.sys.mjs:70-72,125,140`; `ZenSpacesSyncModel.sys.mjs:47-64`; `zen/prefs/zen/sync.yaml:5-15`; `zen/tools/ffprefs/src/main.rs:234-243` |
| Share a space, folder, or split by link | shipped (1.22.1b) | Uploads the tab list to `share.zen-browser.app`. Server is a Cloudflare Worker with KV storage, 30-day retention, 25 MiB cap, 2 creates per minute. | FACT: `zen/src/zen/share/ZenShareClient.sys.mjs:35,72`; `wrangler.toml` in github.com/zen-browser/share |
| Profiles | partial | Firefox's new profile switcher is turned off. Containers per space replace it. | FACT: `zen/prefs/firefox/browser.yaml:53` |
| Session backups and recovery | shipped (1.18b) | See "Data and storage". | FACT: `zen/src/zen/sessionstore/ZenSessionManager.sys.mjs` |

### Privacy and blocking

| Feature | Status | Details | Source |
| --- | --- | --- | --- |
| Telemetry off | shipped | 20+ telemetry, health-report, studies and Normandy prefs locked off. Crash reporter not compiled into release builds. | FACT: `zen/prefs/privatefox/privacy.yaml:6-90`; `zen/configs/common/mozconfig` (`--disable-crashreporter`) |
| Mozilla promos off | shipped | VPN promos, "More from Mozilla", add-on recommendations, sponsored new-tab items. | FACT: `zen/prefs/privatefox/disablemozilla.yaml` |
| Global Privacy Control | shipped | `privacy.globalprivacycontrol.enabled: true`. | FACT: `zen/prefs/privatefox/privacy.yaml` |
| Ad blocking | shipped (1.22.1b) | Onboarding offers to install uBlock Origin from Mozilla's add-on store. Not bundled. | FACT: `zen/locales/en-US/browser/browser/zen-welcome.ftl:26-29` |
| Tracking protection, fingerprinting protection | shipped (inherited) | Firefox defaults. No Zen-specific changes found. | FACT: grep of prefs and patches |
| First-run network calls | improved 2025 | A privacy audit counted about 45 first-run connections. Zen bundled icons locally and stopped preloading default Essentials. The maintainer kept speculative preconnect on: "No, it won't be disabled by default." | FACT: issue #7000 comments 2025-04-27 to 04-30 |

### AI assistant

| Feature | Status | Details | Source |
| --- | --- | --- | --- |
| Any assistant | no | Every Firefox AI pref is off: chatbot, chatbot sidebar, shortcuts, link previews, on-device ML (`browser.ml.enable`), AI controls page. Firefox's AI Window hamburger code is short-circuited. | FACT: `zen/prefs/firefox/ai.yaml:6-28`; `zen/src/browser/components/aiwindow/ui/modules/AIWindow-sys-mjs.patch` |
| Community stance | — | Visible anti-AI voices: "stop using AI for this project" (20 votes), "explicit policy on LLMs" (8 votes). Requests for AI sidebars exist too (22 votes). | FACT: discussions #12762, #14678, #1691 |

### Agent

None. No browser-control agent, no tools, no permissions model. FACT: no such
code in `zen/src/zen/`.

### Extensibility (CLI, MCP, API, extensions, mods)

| Feature | Status | Details | Source |
| --- | --- | --- | --- |
| WebExtensions | shipped (inherited) | Firefox add-ons (Manifest V2 and V3), so full uBlock Origin works. Chrome Web Store extensions do not. | FACT: Firefox platform; CLAIM: reviews |
| Zen Mods | shipped | CSS-only theme packages: `chrome.css`, `preferences.json` (checkbox or string-valued options, written into the browser DOM for the CSS to read), `readme.md`. Installed from a website store (77 approved, 274 open submission PRs). Auto-update every 20 days. Assets must be HTTPS; there is no signature or hash check. The store page talks to the browser through a privileged actor allowed only on `https://zen-browser.app/*`. | FACT: `zen/src/zen/mods/ZenMods.mjs:53-61,323-330,417-425`; `zen/prefs/zen/mods.yaml:8-22`; theme-store repo tree and PR count via GitHub API |
| userChrome.css | shipped (inherited) | Re-enabled automatically if the file exists. | FACT: `zen/src/zen/common/sys/ZenUIMigration.sys.mjs:94-118` |
| Boosts (per-site restyling) | shipped (1.20b) | Recolor a site from an accent color (color math in OKLab, done in the style engine in C++ so every page color is filtered once), contrast, brightness, saturation, invert (dark mode), font, size, letter case, "Zap" to remove elements (with a 1,400 ms WebGL dissolve), custom CSS with element picker, "Focus" (1.23.4b), save and load. CSS only; no JavaScript. | FACT: `zen/src/zen/boosts/nsZenBoostsBackend.h`; `ZenZapDissolve.sys.mjs:150`; `actors/ZenBoostsChild.sys.mjs:5,470-490`; `zen/locales/en-US/browser/browser/zen-boosts.ftl` |
| CLI | partial | Only the two flags above. No scripting CLI. | FACT |
| MCP server, local API | no | | FACT: no such code |
| Automation protocol | unverified | Firefox's WebDriver BiDi remote agent is probably still built in (only `geckodriver` is disabled), but Zen does not document it. | INFERENCE: `zen/configs/common/mozconfig` (`--disable-geckodriver`) |
| Enterprise policies | shipped (inherited) | `policies.json`. Users report updates overwrite it. | FACT: discussion #15045 |

### Other

| Feature | Status | Details | Source |
| --- | --- | --- | --- |
| Onboarding | shipped (1.22b) | Import, default browser, search engine, pick Essentials, ad blocking, space colors. Skipped in kiosk mode. | FACT: `zen/locales/en-US/browser/browser/zen-welcome.ftl:5-36` |
| Theme picker | shipped | Up to 3 color dots on a wheel with harmony modes, opacity, grain texture. See UI section. | FACT: `zen/src/zen/spaces/ZenGradientGenerator.mjs:76,201-210,1453` |
| macOS polish | shipped | Window vibrancy (`NSVisualEffectView`, default material HUD window), native popovers, single-color window buttons hidden until hover, inactive windows greyed, trackpad haptics on snaps and drops, launch at login (1.22.2b). | FACT: `zen/prefs/zen/macos.yaml`; `zen/src/widget/cocoa/nsCocoaWindow-mm.patch:21-60`; `zen/src/zen/toolkit/common/cocoa/ZenHapticFeedback.mm` |
| Acrylic blur on sidebar and address bar | beta (Twilight default) | `backdrop-filter: blur(42px) saturate(110%) brightness(0.5)`, skipped when the OS asks for reduced transparency. | FACT: `zen/prefs/zen/theme.yaml:20-30`; `zen/src/zen/compact-mode/sidebar.inc.css:278-281` |
| Download animation | shipped | Icon flies along an arc to the downloads button. | FACT: `zen/src/zen/downloads/ZenDownloadAnimation.mjs:259-266` |

## UI, look, and feel

### Layout

- The sidebar, top to bottom: window buttons (hidden until hover), the address
  bar, the Essentials grid, the space header (44 px tall), pinned tabs, a
  separator with "Clear", then open tabs. The new-tab button sits at the top. The
  footer holds an expand-sidebar button, space icons, and a "+" menu. FACT:
  `zen/src/browser/base/content/zen-sidebar-icons.inc.xhtml`;
  `zen/src/zen/common/styles/zen-theme.css:232`.
- Space icons shrink to 4 px dots when they overflow and grow back on hover
  (150 ms). FACT: `zen/src/zen/spaces/overflow-icons.inc.css`.
- The page is a floating card. It is inset by `zen.theme.content-element-separation`
  = 8 px and has the shadow `rgba(0,0,0,0.24) 0 3px 8px`. FACT:
  `zen/prefs/zen/theme.yaml:8`; `zen/src/zen/common/styles/zen-theme.css:262`;
  `zen-browser-container.css:11-15`.
- Address-bar page actions (site info, extensions) are invisible until the
  sidebar is hovered (fade 150 ms). FACT: `zen/src/zen/common/styles/zen-omnibox.css:150-172`.
- Compact Mode hides the sidebar, the toolbar, or both. It shows them when the
  pointer reaches the edge. FACT: `zen/prefs/zen/compact-mode.yaml:5-8`.

### Visual language

- Corners are squircles. Zen turns on CSS `corner-shape` and scales radii by a
  "squircle value" of 1.3 (2.3 on Windows). Base radius 7 px; tab radius 8 px;
  tab margin 2 px. FACT: `zen/prefs/firefox/browser.yaml` (`layout.css.corner-shape.enabled`);
  `zen/src/zen/common/styles/zen-theme.css:10,220-223`; `vertical-tabs.css:262,331`.
- Tab states: selected is white at 85% (light) or 20% (dark). Hover is black at
  10% (light). Pressing a tab scales it to 0.98. FACT: `vertical-tabs.css:366,1192,1215`;
  `zen-theme.css:263`.
- Type: SF Pro on macOS. Toolbar height 38 px (42 px in some modes). FACT:
  `zen-theme.css:154-156,294`.
- Color: each space gets a gradient from up to 3 dots on a color wheel. Harmony
  modes are complementary (180°), single analogous (310°), split complementary
  (150° and 210°), analogous (50° and 310°), triadic (120° and 240°), and free.
  A grain PNG sits on top with adjustable opacity. Since 2026-10-25 text is also
  tinted by the accent. FACT: `zen/src/zen/spaces/ZenGradientGenerator.mjs:76,201-210,1453`;
  `zen-gradient-generator.css:398-399`; commit gh-16157.
- Material: on macOS the window background is an `NSVisualEffectView` behind
  the window. FACT: `zen/src/widget/cocoa/nsCocoaWindow-mm.patch:21-60`.

### Motion (exact values from code)

Zen vendors the Motion library (motion.dev) v13.2.0 and loads it lazily, on the
first animation. It also uses the Web Animations API and CSS transitions. FACT:
`zen/src/zen/vendor/motion.dep`; `zen/src/zen/common/modules/ZenUIManager.mjs:99-107`.

| Interaction | Technique | Parameters | Source |
| --- | --- | --- | --- |
| Space switch | Motion spring on `transform` | `bounce: 0`, `duration: 0.25 s` (pref 250 ms). Each space is offset by 100% per index, with wrap-around. Background cross-fades via `--zen-background-opacity`. Essentials slide only when the next space has a different set. A safety timeout ends the switch at duration + 50 ms. | FACT: `zen/src/zen/spaces/ZenSpaceManager.mjs:2299-2301,2368-2378,2396,2413-2428,2479-2489,2499`; `zen/prefs/zen/workspaces.yaml:26` |
| Space swipe | rubber band | Resistance = `1 - abs(x) / (4.5 × strip width)`; tracking stops below 0.5. | FACT: `zen/src/zen/spaces/ZenSpacesSwipe.mjs:204-216` |
| Compact sidebar reveal | CSS `translate` | 0.25 s with a CSS `linear()` curve sampled from a spring. It overshoots to 1.0109 at 73%, then settles. | FACT: `zen/src/zen/compact-mode/sidebar.inc.css:172-276` |
| Compact sidebar hide | CSS `translate` | 0.15 s `ease`. | FACT: `sidebar.inc.css:83-85` |
| Compact Mode on or off | Motion spring on margins | `bounce: 0`, `duration: 0.1 s`. | FACT: `zen/src/zen/compact-mode/ZenCompactMode.mjs:470-535` |
| Compact hover timing | prefs | Keep open 150 ms after leaving. Toolbar hides 1,000 ms after hover. Popup flash 800 ms. The pointer may go 200 px (sideways) or 100 px (up or down) outside the window before the sidebar closes. | FACT: `zen/prefs/zen/compact-mode.yaml:14-28` |
| Glance open | Web Animations, 91 keyframes along an arc | 350 ms. Each keyframe uses easeOutBack (c1 = 0.6), under an overall `ease-in-out`. Arc height = min(0.4 × distance, 30 px, 0.6 × free space), bending toward the larger free side. Starts at the clicked link's box; ends at 80% width, full height. Content fades in over the first 87 ms. | FACT: `zen/src/zen/glance/ZenGlanceManager.mjs:36-40,146-154,726-737,816-905` |
| Glance close | same arc, reversed | 350 ms, ease-out-sextic `1 - (1-t)^6`. Shrinks back into a snapshot image of the original link. | FACT: `ZenGlanceManager.mjs:877,1251-1266` |
| Glance background | Motion spring | Page behind scales 1 → 0.97 and fades to 0.3, `bounce: 0.2`, 0.35 s. Return: 0.233 s, `bounce: 0`. | FACT: `ZenGlanceManager.mjs:9,635-646,1211-1220` |
| Glance side buttons | Motion spring | Opacity 0 → 1 and slide 20 px, 0.2 s, delay 0.15 s, `bounce: 0`. | FACT: `ZenGlanceManager.mjs:446-458` |
| Glance expand to tab | Web Animations | `scale [1, 1.005, 1]`, 250 ms `ease-in-out`. | FACT: `ZenGlanceManager.mjs:1864-1873` |
| Tab open | Motion | Opacity 0 → 1, scale 0.95 → 1, space opens, 0.12 s ease-out. Skipped when reduced motion is on. | FACT: `zen/src/zen/common/modules/ZenVerticalTabsManager.mjs:101,152-166` |
| Tab close | Motion | Opacity 1 → 0, scale 1 → 0.95, space collapses, 0.1 s. | FACT: `ZenVerticalTabsManager.mjs:180-209` |
| Folder open or close | Web Animations | 0.18 s `ease-in-out`; reveal 0.2 s. | FACT: `zen/src/zen/folders/ZenFolders.mjs:1710-1716,1625-1628` |
| Split drop | Motion spring | Scale 0.97 → 1, opacity 0 → 1, `bounce: 0.4`, 0.2 s, delay 0.1 s. | FACT: `zen/src/zen/split-view/ZenViewSplitter.mjs:2338-2352` |
| Library open | Motion spring driving a JS value | stiffness 720, damping 47, mass 1.2 (damping ratio about 0.80, settles in about 0.2 s). | FACT: `zen/src/zen/library/ZenLibrary.mjs:597-610`; ratio is INFERENCE (my arithmetic) |
| Library CSS | CSS | 0.3 s `cubic-bezier(0.22, 1, 0.36, 1)`; entries use `linear(0, 0.34 12%, 0.7 24%, 0.93 38%, 1.03 55%, 1)`. | FACT: `zen/src/zen/common/styles/zen-library-widget.css:10-12` |
| Toast | Motion spring | Scale 0 → 1, `bounce: 0.2`, 0.5 s. Hide: opacity and scale to 0.5, 0.2 s. Hovering pauses auto-hide. | FACT: `zen/src/zen/common/modules/ZenToasts.mjs:47-82` |
| Theme dots | Motion spring | 0.4 s, `bounce: 0.3`. | FACT: `ZenGradientGenerator.mjs:930-948` |
| Download | Motion along an arc | 1,000 ms `cubic-bezier(0.37, 0, 0.63, 1)`; button pops to 1.1 over 0.35 s. | FACT: `ZenDownloadAnimation.mjs:259-266,405-500` |
| Address bar search mode | Motion and CSS | Scale `[1, 0.98, 1]` 0.25 s; a 1 s accent glow. Skipped when reduced motion is on. | FACT: `zen/src/zen/urlbar/ZenUrlbarController.mjs:307-316`; `zen-animations.css` |
| Error shake | Web Animations | x `[0, -12, 8, -4, 2, 0]` px, 600 ms ease-out. | FACT: `ZenUIManager.mjs:177-182` |
| Onboarding | Motion springs | `bounce: 0.35`, visual duration 0.35 s; exits 0.12 s ease-in; fades 0.25 s. One spring is stiffness 300, damping 20, mass 1.8 (damping ratio about 0.43, visibly bouncy). | FACT: `zen/src/zen/welcome/ZenWelcome.mjs:229-231,960-989` |

CSS totals across Zen's own styles: the most common durations are 0.1 s (28
uses), 0.2 s (21) and 0.15 s (12). The most common easings are `ease-in-out`
(44) and `ease-out` (16). Boosts use `cubic-bezier(0.075, 0.82, 0.165, 1)`
(12). FACT: grep of `zen/src/zen/**/*.css`.

Reduced motion is honored in some places (tab open and close, search mode,
space creation, 11 CSS rules). Toasts pass `reduceMotion: false`. There is no
global "disable animations" switch; the request has 87 votes and is open. FACT:
`ZenVerticalTabsManager.mjs:101,186`; `ZenToasts.mjs:52,66,81`; discussion #830.

### Signature interactions that feel great

- **Glance from the link and back.** The preview grows out of the exact link you
  clicked, along a slight arc, and shrinks back into a snapshot of that link.
  The page behind dims and sinks to 97%. FACT: code above.
- **Space swipe with physical resistance** and useful ends (new space, Library).
  FACT: `ZenSpacesSwipe.mjs`.
- **Compact Mode that forgives.** A native pointer monitor keeps the sidebar open
  while you overshoot the window edge. It runs only after the pointer leaves the
  window while the sidebar is showing. It uses a local and a global `NSEvent`
  monitor. It gives up once the pointer passes the offset, or leaves the
  window's span on the other axis. Linux has no tracker. FACT:
  `zen/src/zen/compact-mode/nsIZenMouseTracker.idl:9-40`;
  `ZenMouseTrackerCocoa.mm:29-63`; `ZenCompactMode.mjs:953-983`.
- **Haptic clicks** on drag snaps, split drops, pinning, and theme dots
  (`NSHapticFeedbackPatternAlignment`). FACT: 12 call sites, e.g.
  `zen/src/zen/split-view/ZenViewSplitter.mjs:416`.
- **Small press and arrival details:** tab press at 0.98, split drop bounce 0.4,
  toast spring 0.2. FACT: table above.

### Things that feel bad

- **Sidebar closes while you are still on it.** Three of the top issues from the
  last six months: #15995 (17 reactions), #16002 (17), #16054 (12). A fix landed
  in 1.23.4b. FACT: GitHub search, release notes.
- **Window mirroring surprised people.** #12008 "Disable window/tab sync by
  default" has 81 reactions. Discussion #12025 has 155 votes. The lead
  developer replied there: "It will never be disabled by default" (2026-01-25).
  The #12008 report says switching a tab in one window exits fullscreen in
  another. The feature was itself a popular request: discussion #924 "Sync
  workspace tabs across windows" has 416 votes. FACT: issue #12008;
  discussions #12025 and #924.
- **Forced floating address bar.** #3539 "Please add an option to disable the
  floating URL bar. It is *VERY* annoying" (90 reactions). An option followed.
  FACT.
- **Choppy scrolling from rounded content corners.** A Mozilla graphics engineer
  (`nical`) opened #6302 (117 reactions). Zen's UI kept WebRender from caching
  scrolled content as layers. He first blamed blend modes, then withdrew that
  ("apologies for the hasty conclusion"). The lead developer later tied it to
  the rounded-corner clip. Users reported 30 to 45% GPU use with corners on.
  The lead developer reported it fixed with Firefox 141 in July 2025. A
  Linux-only leftover, rounded bottom window corners, made Zen turn those off in
  1.18.10b. That Gecko fix (bug 1979083) landed in Firefox 150. FACT: issue
  #6302 body and comments (nical 2025-03-10 and 03-11; mr-cheffy 2025-04-15,
  07-17 to 07-24); 1.18.10b release notes;
  https://bugzilla.mozilla.org/show_bug.cgi?id=1979083 (Linux GTK, "150 Branch").
- **Settings sprawl.** 156 `zen.*` prefs are declared in the 28 files of
  `zen/prefs/zen/*.yaml`; about 180 distinct `zen.*` names appear in the source.
  FACT: grep at 9b604fe. That most are reachable only in `about:config`, and
  calling this "sprawl", are INFERENCE.
- **Some motion runs on the main thread.** The Library spring updates a JS value
  every frame through `onUpdate`. FACT: `ZenLibrary.mjs:597-610`. That this can
  stutter under load is INFERENCE.

## Architecture

### Process model

Zen keeps Firefox's model. The parent process runs the browser window ("chrome")
and every line of Zen's JavaScript. Web pages run in site-isolated content
processes. GPU, media and utility work have their own processes. Zen talks to
pages through Firefox's per-window actor pairs (parent and child): Glance, Boosts,
window drag, Mods store. FACT: `zen/src/zen/*/actors/`. A review found several helper processes ("Isolated WebContent", "Utility",
"WebExtensions") and that counting them doubled its RAM figure. CLAIM: https://supasidebar.com/blog/zen-browser-mac-review-2026

### How it integrates the engine

- **Patches on a source tarball, not a git fork.** `surfer download` fetches
  `firefox-<version>.source.tar.xz` from archive.mozilla.org (release or release
  candidate) into `engine/`. FACT: `surfer/src/commands/download/firefox.ts:139-173`.
- **One patch per upstream file.** `surfer export <file>` writes `git diff` of
  one file to `src/<same path>/<file name with dots as dashes>.patch`. It warns
  when a patch passes 8,000 characters. Patches apply with `git apply
  --ignore-space-change --ignore-whitespace` in glob order. There is no series
  file. Each of Zen's own patches is the only one for its file; just 3 files
  also get an external patch. FACT: `surfer/src/commands/export-file.ts:9-60`;
  `surfer/src/commands/patches/git-patch.ts:16-30`; `surfer/src/constants/index.ts:14-18`.
- **New files are symlinked, not patched.** Every non-patch file under `src/`
  is symlinked into `engine/`, so editing it in the engine edits the repo. Only
  edits to upstream files need a patch refresh. FACT:
  `surfer/src/commands/patches/copy-patches.ts:34-60,84-130`.
- **Small hooks.** The `browser.xhtml` patch is +5 / -1 lines: two `#include
  zen-*.inc.xhtml` lines, one attribute, and a wrapper `<hbox>`. It drops the
  upstream `navigator-toolbox` include. Zen modules load from one preload script. FACT:
  `zen/src/browser/base/content/browser-xhtml.patch`;
  `zen/src/zen/common/ZenPreloadedScripts.js`.
- **External patches by manifest.** Pending Mozilla fixes (Phabricator diffs)
  and a LibreWolf patch are pulled by ID into `src/external-patches/`, with
  text replacements when they don't apply. Examples: "Backdrop filter reads web
  content", "Fix HEVC video stutters". FACT:
  `zen/src/external-patches/manifest.json`; `zen/scripts/update_external_patches.py`.
- **Prefs as YAML.** 40 YAML files (28 of them Zen's own) compile, through a small Rust tool, into
  Firefox's default prefs and its static (C++-visible) pref list, with
  conditions per platform and channel. FACT: `zen/tools/ffprefs/src/main.rs:200-260,334`.
- **Size of the patch layer.** 264 own patch files, one per upstream file:
  868 hunks, +3,677 / -1,052 lines. The 7 external patch files in the tree add
  90 hunks over 27 files. Together: 958 hunks over 287 distinct upstream files.
  Biggest:
  `Tabbrowser.sys.mjs` (101 hunks), `SessionStore.sys.mjs` (40),
  `UrlbarInputBase.mjs` (35). By area: 71 in browser components, 24 in browser
  base, 13 in browser themes, 9 in the style engine, 8 in SVG, 5 in macOS
  widget code. FACT: `grep -c '^@@'` and `git apply --numstat` over
  `zen/src/**/*.patch` at 9b604fe.
- **Comparison with rac.** rac has about 180 patches, 871 hunks and 217 upstream
  files. Zen's own patches are 868 hunks over 264 files, a similar footprint.
  The difference is where feature code lives: Zen keeps about 83,000 raw lines
  of JS, CSS and C++ in new files under `src/zen/` (tests, types and vendored
  code excluded). FACT for Zen; rac numbers from
  `plans/context/maintainer-brief.md`.

### UI technology

Firefox's browser window is itself a web document: XUL and HTML custom elements,
CSS, and privileged JavaScript modules. So Zen's UI is about 67,500 lines of JS
(about 55,800 without blank and comment lines) and 12,500 lines of CSS. Native
work (pointer tracking, drag and drop, the Boosts color filter, the Mods
stylesheet cache, library file access, haptics, sharing) is about 3,200 lines of
C++ and Objective-C++ (2,900 without the Boosts unit tests), exposed as XPCOM
components. FACT: `wc -l` over `zen/src/zen/` excluding `tests/`, `@types/` and
`vendor/`.

A UI-only change rebuilds with `npm run build:ui`, which runs
`mach build faster` (front-end files only). FACT: `zen/package.json:11`;
`surfer/src/commands/build.ts:126-130`. This is a structural advantage over
Chromium's C++ Views UI, where every UI change recompiles. INFERENCE.

### Languages and code layout

- `src/zen/<feature>/`: one folder per feature (boosts, compact-mode, folders,
  glance, library, live-folders, mods, sessionstore, spaces, split-view, sync,
  tabs, urlbar, welcome, and more). FACT.
- `src/zen/tests/`: 184 Zen test files in 25 feature folders, plus 351 imported
  Firefox browser tests and about 148 more imported xpcshell-style test files,
  plus C++ unit tests for the Boosts color math. FACT:
  `zen/src/zen/tests/moz.build`; `zen/src/zen/boosts/gtest/`.
- `src/zen/@types/`: about 80,000 lines of generated TypeScript types for Gecko
  APIs, used for editor checking only. FACT.
- Python and shell scripts for syncing, signing and packaging; one Rust tool for
  prefs. FACT: `zen/scripts/`, `zen/tools/ffprefs/`.

## Data and storage

All paths are inside the profile folder,
`~/Library/Application Support/zen/Profiles/<id>/` on macOS. CLAIM (tested by a
BleachBit contributor): https://github.com/bleachbit/bleachbit/pull/2394

| Data | File and format | Notes | Source |
| --- | --- | --- | --- |
| Spaces, tabs, groups, folders, split layouts | `zen-sessions.jsonlz4` (JSON compressed with LZ4, written through Firefox's `JSONFile`) | Replaced an older `zen_workspaces` table in `places.sqlite`; migrated once. Firefox's own `sessionstore.jsonlz4` is still written too, so the save interval was raised from 15 s to 40 s. | FACT: `zen/src/zen/sessionstore/ZenSessionManager.sys.mjs:48,105-130,155-190`; `zen/prefs/firefox/browser.yaml:124` |
| Session backups | `zen-sessions-backup/zen-sessions-YYYY-MM-DD-HH.jsonlz4` | One file per 3-hour bucket (local time). The newest 20 are kept, with no thinning of older days, so they can cover as little as 60 hours of use (INFERENCE from the code). Written at most every 10 minutes. `clean.jsonlz4` is not a clean-shutdown copy: it is the previous file, copied aside before every session save (every 40 s). `recovery.baklz4` is Firefox `JSONFile`'s own pre-write backup, read when the main file is missing or corrupt. If the loaded data still has no spaces, Zen tries exactly two more files: `clean.jsonlz4`, then the newest bucket file. | FACT: `ZenSessionManager.sys.mjs:31-58,102-118,137-152,254-279,600-614,661-707`; `zen/src/browser/components/sessionstore/SessionSaver-sys-mjs.patch:26`; `JSONFile` docs at https://searchfox.org/mozilla-central/source/toolkit/modules/JSONFile.sys.mjs |
| Per-space bookmarks | `places.sqlite` tables `zen_bookmarks_workspaces` and `..._changes` | Schema version kept in `moz_meta`. | FACT: `zen/src/zen/spaces/ZenSpaceBookmarksStorage.js` |
| Space routing rules | `zen-space-routing.jsonlz4` | | FACT: `ZenSpaceRoutingManager.sys.mjs:16` |
| Live folders | `zen-live-folders.jsonlz4` | | FACT: `ZenLiveFoldersManager.sys.mjs:35` |
| Boosts | `zen-boosts.jsonlz4` and `zen-boosts/` | | FACT: `ZenBoostsManager.sys.mjs:12,456-467` |
| Shortcuts | `zen-keyboard-shortcuts.json` | | FACT: `ZenKeyboardShortcuts.mjs:697` |
| Mods | `zen-themes.json`, `chrome/zen-themes/<id>/{chrome.css, preferences.json, readme.md}`, merged into `chrome/zen-themes.css` | | FACT: `ZenMods.mjs:53-61,417-425` |
| Spaces sync snapshot | `zen-spaces-sync.json` | Last state sent, for diffing. | FACT: `ZenSpacesSyncModel.sys.mjs:64` |
| Command ranking | pref `zen.urlbar.suggestions-learner` in `prefs.js` | | FACT: `ZenUBResultsLearner.sys.mjs` |
| Passwords, cookies, history | Firefox's normal files | Passwords encrypted with Firefox's key store (`key4.db`) and an optional primary password. No Zen changes. | INFERENCE from Firefox design; no Zen patch touches them |

**Encryption.** Nothing beyond Firefox's own at rest. Sync data, including the
custom Spaces records, is end-to-end encrypted by Firefox Sync with keys derived
from the Mozilla account. FACT: `ZenSpacesSync.sys.mjs` uses `CryptoWrapper`
records.

**Servers and what leaves the machine.**

| Destination | When | What | Source |
| --- | --- | --- | --- |
| `updates.zen-browser.app` (GitHub Pages) and GitHub Releases | Update checks and downloads | A static `update.xml` per platform and channel; full update files only (macOS 170 MB) | FACT: `zen/src/build/moz-build.patch:10`; updates-server repo |
| `zen-browser.github.io/theme-store` | Installing or updating mods | JSON and CSS | FACT: `ZenMods.mjs:323` |
| `share.zen-browser.app` (Cloudflare Worker) | Only when you share | Tab titles and URLs of the shared item; authenticated with the Mozilla API key built into each release, or a personal secret key for permanent links | FACT: `ZenShareClient.sys.mjs:50-75`; share repo |
| Mozilla (accounts, Sync, add-ons, remote settings, push, captive-portal check) | Inherited | Firefox defaults | FACT: issue #7000; privacy policy |
| Google Safe Browsing, Widevine and OpenH264 downloads | Inherited | Built with Zen's own Safe Browsing key | FACT: `zen/.github/workflows/src/release-build.sh:22-34` |
| Websites in Essentials | Hover over an Essential | Speculative preconnect, kept on by choice | FACT: issue #7000 |

**Telemetry.** None from Zen. Firefox telemetry is locked off and the crash
reporter is not built. The privacy policy is dated 2025-02-05 and says "We do not
collect any telemetry data or crash reports." It predates the share server (2026)
and does not mention it or Safe Browsing. FACT: prefs above;
https://zen-browser.app/privacy-policy/ . The policy being out of date is
INFERENCE.

## Agents and AI

Zen has no assistant and no agent. It turns off every Firefox AI and ML feature
(chatbot, sidebar chatbot, link previews, on-device ML engine, AI settings page)
and neuters Firefox's AI Window hook. FACT: `zen/prefs/firefox/ai.yaml:6-28`;
`zen/src/browser/components/aiwindow/ui/modules/AIWindow-sys-mjs.patch`.

- Where an agent runs, page representation, tools, providers, local models,
  permissions, injection defenses, skills, automations: not applicable. FACT.
- Outside-agent access: no MCP server, no API, no scripting CLI. Only
  `--space` and `--blank-window` flags. Firefox's WebDriver BiDi remote agent is
  probably present but undocumented. FACT for the absence; INFERENCE for BiDi.
- Firefox's on-device translation (not generative) stays on; 1.21.15b added
  translation inside iframes. FACT: release notes.
- Market signal: Zen's community includes vocal opponents of AI (discussions
  #12762 and #14678). Arc users who want AI are told to look at Dia or Brave by
  third-party reviews. FACT for discussions; CLAIM for reviews. For rac this
  supports "AI off by default and costs nothing". INFERENCE.

## Build, release, and engineering

### Build system

`npm` scripts wrap `surfer`, which wraps Mozilla's `mach`:
`npm run init` (download, import, bootstrap), `npm run build`,
`npm run build:ui`, `npm start`. Needs about 30 GB free. FACT: `zen/package.json:8-37`;
https://docs.zen-browser.app/contribute/desktop/building

### CI and how they build the engine

- **macOS is cross-compiled on Linux.** Each architecture builds on a
  Blacksmith 8-vCPU Ubuntu runner with Mozilla's `cctools-port`, `libdmg` and
  `hfsplus` tools. sccache on the GitHub Actions cache is optional (input
  `use-sccache`, default `false`); Twilight turns it on. Only two
  steps need a Mac: running the instrumented build to collect profile data
  (`macos-15-intel`, `macos-26`), and the final universal merge, signing and
  notarization (`macos-26`). FACT:
  `zen/.github/workflows/macos-release-build.yml:46-200`;
  `macos-profile-build.yml:31`; `macos-universal-release-build.yml:18`;
  `zen/configs/macos/mozconfig`; `build.yml:24-28`;
  `twilight-release-schedule.yml:23`.
- **Real timings, release run 39497770166 (1.23.4b).** A full optimized
  macOS build took 42 to 49 minutes per architecture, with no compiler cache:
  the run's input log shows `use sccache: false`. Profile collection took
  38 to 62 minutes. The whole three-stage pipeline for all platforms finished in
  about 4.5 hours of wall time (21:07 to 01:37 UTC). The release step started about
  12 hours later. FACT: jobs API and "Generate build ID" job log for that run.
  The `Deploy-Release` environment requires a reviewer (FACT: environments API),
  and the job downloads Windows files signed outside the run. That those two
  explain the 12-hour gap is INFERENCE.
- **Profile-guided optimization (PGO) trained on Zen's own UI.** The training
  script drives tab switches ×200 and compact mode, sidebar hover, Glance,
  Library, space switch and address bar ×50 each, plus split view ×20, folders
  ×30, Boosts ×10. Profiles are cached, keyed on the Firefox version and a hash
  of the training inputs, but only Twilight reuses them; release builds always
  retrain. Link-time
  optimization is on (`cross,thin`); arm64 builds use `-mcpu=apple-m1`. Windows
  added context-sensitive PGO in 1.23.4b. FACT:
  `zen/src/zen/common/sys/ZenPGOTraining.sys.mjs:38-49`; `zen/.github/workflows/build.yml:277-310` (gate at `:290-300`);
  `zen/configs/macos/mozconfig`.
- **Release builds** use `--enable-release`, `--disable-tests`,
  `--disable-crashreporter`, a clang plugin, and Rust SIMD. FACT:
  `zen/configs/common/mozconfig`.

### Signing, notarization, updates

- macOS: `mach macos-sign` with `rcodesign` and a `.p12`, then `codesign` on the
  DMG, `notarytool submit`, and `stapler staple`. FACT:
  `macos-universal-release-build.yml:159-224`.
- Windows: `signtool` with a named signing identity and Certum's timestamp
  server (`time.certum.pl`). That the certificate itself is from Certum is
  INFERENCE. Signed files come back through
  a per-run release on the `zen-browser/windows-binaries` repo. FACT:
  `zen/build/windows/sign.ps1:123,219`; `build.yml:663-680`. That signing runs
  on a maintainer machine outside CI is INFERENCE.
- Updates: Firefox's built-in updater. Zen generates its own 4,096-bit RSA
  signing certificate, valid to the year 9999, and swaps it into the updater in
  place of Mozilla's. FACT: `zen/scripts/mar_sign.sh:9-60`.
- **Security lesson.** Until 1.19.9b (released 2026-04-24 UTC) the updater shipped with
  signature checks removed and served unsigned update files (advisory
  GHSA-qpj9-m8jc-mw6q, high). FACT: GitHub advisory.
- Update files are always full packages (macOS 170.5 MB), never deltas. At about
  1.3 releases a week, that is roughly 220 MB a week per Mac. FACT for size;
  weekly total is INFERENCE.

### Channels and cadence

- **Release**: built by hand-dispatched workflow from the `stable` branch; the
  publish job needs approval in the `Deploy-Release` environment. FACT:
  `build.yml:1-24,631-645`.
- **Twilight**: built from `dev` every 2 days at 23:00 UTC; one rolling GitHub
  release tag (`twilight-1`). FACT: `twilight-release-schedule.yml`; `build.yml:735-760`.
- 67 releases in the last 12 months, 4 to 8 a month. The busiest month was 2024-08 with 23 releases (the alpha period), then 2024-09 with 11. FACT: releases API.

### Tests and code review

- 535 browser test files exist, but CI never runs them. Pull requests get one
  check: apply patches and lint. The `dev` branch is protected with no required
  checks. FACT: `zen/.github/workflows/pr-test.yml`; grep of `.github/`; branch API.
- Commit titles follow `gh-<issue>: <message> (gh-<PR>)`. FACT:
  `zen/.formal-git/template`.
- Triage is fast. February 2026: median first response 2 h 8 min; median time
  to close 3 h 31 min. FACT: `zen/docs/issue-metrics/2026_2026-02-01..2026-02-28.md`.

### How they track upstream

- A weekly job (Tuesdays 04:59 UTC) checks for a new Firefox release candidate
  and pings Discord. A sync workflow downloads the new source, re-applies all
  patches, pulls external patches and tests, and opens a bot PR titled "Sync
  upstream Firefox to version X". The PR body says either "All patches applied
  cleanly" or "Some patches did not apply cleanly". FACT:
  `zen/.github/workflows/check-candidate-release.yml`; `sync-upstream.yml:1-141`.
- `scripts/recalculate-patches.sh` re-exports every patch after fixes. FACT.
- Firefox moved to two-week major releases with Firefox 155 on 2026-09-01. Zen
  synced 155, 156, 157, 158 and 159 within days of each, plus every point
  release. It ships release candidates to Twilight first. FACT: Zen commit log
  2026-04-25 to 2026-10-25; https://blog.mozilla.org/sumo/2026/08/19/firefox-new-release-cadence-and-what-to-expect/
- Chrome also moved to two-week majors, starting with Chrome 153 on
  2026-09-08. FACT: https://developer.chrome.com/blog/chrome-two-week-release ;
  https://techcrunch.com/2026/09/08/chrome-is-now-shipping-updates-every-2-weeks-as-ai-changes-the-security-landscape/ .
  So Helium, and therefore rac, will see upstream releases twice as often.
  INFERENCE.

## Strengths and weaknesses (critical)

### Strengths

1. **Relentless upstream tracking.** Two-week Firefox majors land within days,
   driven by a bot PR and a one-patch-per-file layout. FACT. This is the most
   transferable process lesson. INFERENCE.
2. **Cheap UI iteration.** Features are JS and CSS in new files; a UI rebuild is
   front-end only. FACT.
3. **Feature breadth matching Arc and beyond.** Spaces with cookie-jar
   containers, Essentials, Glance, 4-way split, Compact Mode, folders, live
   folders, space routing, Library, Boosts, cross-device space sync. FACT.
4. **Motion with intent.** One library, mostly zero-bounce springs for
   structure, small bounces for arrivals, 100 to 250 ms for most moves. FACT.
5. **Data-loss defenses.** Rotating 3-hour backups, a copy of the previous
   save, and automatic recovery from two fallbacks. FACT. That these exist
   because of past losses is INFERENCE.
6. **Fast CI for a whole browser.** About 45 minutes for an optimized macOS
   build on 8 cores with no compiler cache, 4.5 hours for the full three-stage
   PGO pipeline. FACT.
7. **Privacy defaults.** Telemetry locked off, no crash reports, no accounts of
   its own. FACT.

### Weaknesses

1. **Bus factor of one.** 85% of all commits and the only code owner are one
   person. FACT.
2. **Data loss history.** 230 issues mention "lost" tabs; 48 mention workspaces
   disappearing; 99 mention pinned tabs gone (search counts, with some noise).
   Examples: #5817 (2025-02, "ALL workspaces lost") and #12028 (2026-01, after
   1.18.1b). FACT: GitHub search.
3. **Defaults pushed on users.** Window mirroring with no settings toggle, a
   forced floating address bar, speculative preconnect kept on. FACT.
4. **Performance complaints persist.** The performance meta-issue #8932 is open
   with 183 comments. Open reports include a content process pegging all cores
   after media playback (#9727) and the GPU helper at 700% CPU (#14793). The
   only public Speedometer 3.0 run (Zen 1.7.3b, January 2025) scored 31.6 versus
   Firefox 34.8 and Chrome 37.7. FACT for issues; CLAIM for the benchmark:
   https://www.jitbit.com/alexblog/zen-review-benchmark/
5. **Security slips at the seams.** Unsigned updates (GHSA-qpj9-m8jc-mw6q).
   Glance and split context menus loaded page links with system privileges
   (GHSA-vpvg-hp3v-rm5q). Fullscreen hid the origin warning (GHSA-vjfv-85qf-v25c,
   high). Address-bar spoofing via long subdomains (GHSA-7p2r-fp29-9w69). FACT:
   GitHub advisories.
6. **Tests that never run in CI.** FACT.
7. **Unsigned mods.** HTTPS only, no signature or hash, auto-updating. FACT.
8. **"Beta" forever.** Version numbers still end in "b" after 195 releases.
   FACT. Users ask when it ends (discussion #14539). FACT.
9. **Engine limits it inherits.** Firefox-only extensions; reports of passkey,
   security-key, iCloud Passwords and Microsoft SSO problems (#437 with 150
   reactions, #479, #11161, #6315, #10498). FACT. Some may be fixed upstream
   since. INFERENCE.
10. **Update size.** Full 170 MB update on every release. FACT.

## What rac should take (ranked, concrete, with rough cost) and what rac should avoid

Cost scale: XS under a day; S 1 to 3 days; M 1 to 2 weeks; L 3 to 6 weeks.
"Thread" says whether it belongs to the UI thread or the architecture thread.

### Take

1. **Automatic backups of spaces and tabs, with ordered recovery.** Copy rac's
   space, pinned-tab and favorites store into a backup folder in 3-hour buckets,
   keep the newest 20, and keep a copy of the previous save. If the main file
   fails to load, try every backup, newest first. Zen itself tries only two
   fallbacks, and its 20 three-hour files can cover just 2.5 days, so rac should
   also keep one file per day for older days (INFERENCE). Document a two-step
   manual restore.
   Why: data loss is Zen's most common complaint, and Arc refugees will bring
   years of pinned tabs. Cost: S to M. Thread: architecture. Source:
   `ZenSessionManager.sys.mjs:30-58,139-145,660-700`.
2. **An upstream-sync bot PR on a schedule.** A weekly CI job that checks for a
   new helium-macos tag, bumps to it on a branch, runs patch application
   (`he validate`-style, no full build), and opens a PR that says "applies
   cleanly" or lists failing patches. Chromium is now on two-week majors, so the
   7-release gap will widen fast without this. Cost: S. Thread: architecture.
   Source: `sync-upstream.yml`, `check-candidate-release.yml`.
3. **Peek (Glance) for links.** Opt-click a link to open it at 80% width over
   the current page. The page behind scales to 0.97 and dims to 0.3. Buttons:
   close, open as tab, split. Open outside links clicked inside favorites in
   peek. Animate from the clicked link's box along a short arc (max 30 px),
   350 ms, and close back into a snapshot. Use the initiator's origin when
   loading, never a privileged one (Zen's GHSA-vpvg bug). Cost: L in Views
   (overlay `WebContents`, snapshot, keyboard focus, Esc). Thread: UI. Source:
   `ZenGlanceManager.mjs`.
4. **Forgiving edge reveal.** While rac's revealed sidebar is showing and the
   pointer leaves the window, watch the pointer with an `NSEvent` monitor and
   keep the sidebar open within 200 px sideways or 100 px vertically. Keep it
   150 ms after leaving; hide the toolbar 1,000 ms after hover. Stop the monitor
   once hidden, so it costs nothing when unused. Cost: S. Thread: UI. Source:
   `compact-mode.yaml:14-28`, `ZenMouseTrackerCocoa.mm`.
5. **Arc import that follows Zen's field mapping.** Use Chromium's existing
   Chrome importer pointed at Arc's "User Data" folder for history and
   passwords. Parse `StorableSidebar.json` for spaces, favorites, pinned tabs,
   folders, emoji and colors. Say plainly that Dia pinned tabs can't be
   imported. Arc closes on 2026-12-22, so this is time-boxed. Zen's code is
   MPL-2.0 with no incompatibility notice, so it can be adapted into GPL-3.0 rac
   with credit, keeping MPL notices on the copied files. Cost: M. Thread:
   architecture. Source: `ZenMigrationUtils.sys.mjs:88-330`. License reading is
   INFERENCE, not legal advice.
6. **A declarative action table for rac's command bar.** Each action: string
   ID, command, icon, `isAvailable(window)`. Add a per-action score from -5 to +5
   that learns from use. It makes "ways in" auditable in one file. Cost: S to M.
   Thread: UI. Source: `ZenUBGlobalActions.sys.mjs:36-340`,
   `ZenUBResultsLearner.sys.mjs`.
7. **A UI performance bench that drives real flows.** Script tab switch ×200,
   sidebar reveal ×50, space switch ×50, command bar ×50, split ×20, folders
   ×30. Record frame times and CPU, and compare with Helium. This turns "never
   slower than Helium" into a number. Cost: M. Thread: architecture. Source:
   `ZenPGOTraining.sys.mjs:38-49` (Zen uses it for PGO; rac would use it for
   measurement).
8. **A motion grammar written down.** Zero-bounce springs for structure (space
   switch 250 ms). Exits faster than entries (tab close 100 ms, open 120 ms with
   scale 0.95). Small bounce only for arrivals (toast 0.2, split drop 0.4). A
   0.98 press scale. Rubber band at swipe ends. A hard timeout per animation so
   input is never blocked. Cost: XS for the doc, S to apply. Thread: UI. Source:
   motion table above.
9. **Small Arc behaviors Zen proved popular.** Back with no history closes the
   tab. Cmd+W on a pinned tab resets, unloads and moves away. "Unload all other
   spaces". Rename tab. Pinned tabs load on demand at startup. Cost: S each.
   Thread: UI. Source: `zen.yaml:47`, `workspaces.yaml:57`.
10. **Haptic ticks on snap points.** `NSHapticFeedbackPatternAlignment` when a
    dragged tab snaps into favorites, a folder, or a split. Cost: XS. Thread:
    UI. Source: `ZenHapticFeedback.mm`.
11. **Space routing (Air Traffic Control).** "Contains" and regex rules, a
    context-menu "Add route for this site", and routing for links from other
    apps at startup. Already on rac's roadmap. Cost: M. Thread: UI plus
    architecture. Source: `ZenSpaceRoutingManager.sys.mjs`.
12. **Theme picker harmonies.** If rac's space themes allow multiple colors,
    offer Zen's harmony presets (180°; 150° and 210°; 50° and 310°; 120° and
    240°) and a grain slider. Cost: S to M. Thread: UI. Source:
    `ZenGradientGenerator.mjs:201-210`.

### Avoid

1. **Mirroring every window by default.** If rac ever shares spaces across
   windows, make it opt-in with a visible toggle, and never let one window's
   tab change exit fullscreen in another. Source: #12008, discussion #12025.
2. **Effects that defeat compositor caching.** Before keeping rounded or blurred
   content edges, measure scroll CPU and GPU with and without them, the way
   #6302 did. Source: issue #6302.
3. **Shipping updates without signature checks**, even once. rac's Sparkle EdDSA
   key must stay mandatory. Source: GHSA-qpj9-m8jc-mw6q.
4. **Privileged loads of page-chosen URLs** from new surfaces (peek, split,
   command bar). Source: GHSA-vpvg-hp3v-rm5q.
5. **Hiding security UI.** Keep the fullscreen origin notice and full origin
   display in compact layouts. Source: GHSA-vjfv-85qf-v25c, GHSA-7p2r-fp29-9w69.
6. **Forcing a new interaction with no way back.** The floating address bar
   needed an opt-out after 90 reactions. Source: #3539.
7. **First-run network calls to third-party sites.** Don't preload default
   favorites; bundle their icons. Source: issue #7000.
8. **Storage migrations without a backup.** Loss reports followed Zen's UI and
   storage changes (#5817 in 2025-02; #12028 right after the 1.18 session-file
   move). The link is INFERENCE. Back up before every format change. Source:
   `ZenSessionManager.sys.mjs:155-190`.
9. **Tests that CI never runs.** rac has the same gap today. Source:
   `pr-test.yml`.
10. **Full-size updates every release.** Sparkle supports delta updates; use
    them, especially with two-week upstream releases. INFERENCE.
11. **A settings surface of 150+ prefs.** It contradicts rac's "opinionated"
    principle. Source: `zen/prefs/zen/`.
12. **A server for sharing.** Zen's share link needs a hosted service with
    retention and rate limits. That conflicts with rac's "nothing phones home".
    INFERENCE.

### Not transferable (engine differences)

- Cross-compiling macOS builds on Linux is a Firefox capability. Chromium does
  not officially support building macOS on Linux, so rac's CI cannot copy it.
  INFERENCE; worth a quick check.
- A Firefox build is far smaller than Chromium's (about 45 minutes on 8 cores
  with no compiler cache, versus rac's roughly 130,000 build steps that don't finish in 6 hours). The
  CI gap is mostly the engine, not Zen's cleverness. FACT for both numbers;
  conclusion INFERENCE. Source: run 39497770166; `plans/context/ci-status.md`.
- Cookie-isolated spaces come cheap in Firefox (containers). Chromium has no
  per-tab cookie jar in a normal window. INFERENCE.
- Firefox's UI is HTML and CSS, so Zen gets CSS springs (`linear()` curves) and
  instant UI rebuilds. rac's Views UI uses `gfx::Tween`. A WebUI surface could
  get the same tools at a cost in memory and startup. Whether to use WebUI for
  heavy panels (a Library, onboarding) is an open choice. INFERENCE.

## Open questions and things you could not verify

- Whether Zen's Firefox WebDriver BiDi remote agent works in release builds.
  Not tested; I could not run the binary.
- Real performance and battery numbers for current Zen (1.23) on Apple Silicon.
  The only Speedometer run is from January 2025 on 1.7.3b.
- Actual active users. Update-file downloads (63,277 macOS in 4 days) are a
  proxy, and one install may fetch more than once.
- Minimum macOS version. A review says macOS 14; Zen sets nothing itself, so it
  probably inherits Firefox's (10.15). Not verified.
- Whether spaces sync is on by default for release users who already use
  Firefox Sync. The pref is off on stable, but the settings checkbox might be
  pre-checked during sign-in.
- How often the Mozilla API key embedded for sharing gets abused or rotated.
- Whether an AI bot answers GitHub issues, as discussion #12762 claims.
- Exact Firefox 158 and 159 release days. I inferred them from the two-week
  calendar starting with Firefox 155 on 2026-09-01.
- Whether Zen's Windows signing step is manual. The script runs `signtool` with
  a named identity outside CI; the 12-hour gap in the release run suggests a
  person in the loop.
- Exact unsupported-site and DRM state today. Older issues (#10689) describe DRM
  failures; Zen enables Widevine, but streaming quality limits were not tested.

## Sources

Code (clones; GitHub permalinks start with
`https://github.com/zen-browser/desktop/blob/9b604fe/`):

- `zen/surfer.json`, `zen/package.json`, `zen/README.md`, `zen/CODEOWNERS`, `zen/LICENSE`
- `zen/prefs/zen/*.yaml`, `zen/prefs/firefox/{ai,browser,performance}.yaml`, `zen/prefs/privatefox/*.yaml`, `zen/prefs/fastfox/smoothscroll.yaml`
- `zen/configs/common/mozconfig`, `zen/configs/macos/mozconfig`
- `zen/src/zen/spaces/{ZenSpaceManager,ZenSpacesSwipe,ZenGradientGenerator,ZenSpaceCreation}.mjs`, `ZenSpaceBookmarksStorage.js`, `overflow-icons.inc.css`
- `zen/src/zen/glance/ZenGlanceManager.mjs`, `zen/src/zen/glance/actors/ZenGlanceChild.sys.mjs`
- `zen/src/zen/compact-mode/{ZenCompactMode.mjs,sidebar.inc.css,nsIZenMouseTracker.idl,ZenMouseTrackerCocoa.mm}`
- `zen/src/zen/common/modules/{ZenUIManager,ZenVerticalTabsManager,ZenToasts}.mjs`, `zen/src/zen/common/styles/{zen-theme,zen-animations,zen-omnibox,zen-browser-container,zen-library-widget}.css`, `zen/src/zen/common/sys/{ZenPGOTraining,ZenUIMigration}.sys.mjs`, `zen/src/zen/common/ZenPreloadedScripts.js`
- `zen/src/zen/tabs/{ZenPinnedTabManager.mjs,zen-tabs/vertical-tabs.css}`, `zen/src/zen/folders/ZenFolders.mjs`
- `zen/src/zen/split-view/ZenViewSplitter.mjs`, `zen/src/zen/library/ZenLibrary.mjs`, `zen/src/zen/downloads/ZenDownloadAnimation.mjs`, `zen/src/zen/welcome/ZenWelcome.mjs`
- `zen/src/zen/sessionstore/{ZenSessionManager,ZenWindowSync}.sys.mjs`
- `zen/src/zen/sync/{ZenSpacesSync,ZenSpacesSyncModel,ZenSpacesSyncApplier}.sys.mjs`
- `zen/src/zen/share/ZenShareClient.sys.mjs`, `zen/src/zen/mods/ZenMods.mjs`, `zen/src/zen/boosts/*`, `zen/src/zen/live-folders/*`, `zen/src/zen/space-routing/*`, `zen/src/zen/migration/*`, `zen/src/zen/urlbar/*`, `zen/src/zen/kbs/ZenKeyboardShortcuts.mjs`
- `zen/src/browser/base/content/browser-xhtml.patch`, `zen/src/browser/components/BrowserContentHandler-sys-mjs.patch`, `zen/src/browser/components/aiwindow/ui/modules/AIWindow-sys-mjs.patch`, `zen/src/widget/cocoa/nsCocoaWindow-mm.patch`, `zen/src/external-patches/manifest.json`
- `zen/.github/workflows/{build,macos-release-build,macos-profile-build,macos-universal-release-build,pr-test,sync-upstream,check-candidate-release,twilight-release-schedule}.yml`, `zen/.github/workflows/src/release-build.sh`
- `zen/scripts/{update_ff.py,recalculate-patches.sh,mar_sign.sh,run_tests.py}`, `zen/build/windows/sign.ps1`, `zen/tools/ffprefs/src/main.rs`, `zen/docs/{contribute.md,live-folders-specs.md,issue-metrics/}`
- `surfer/src/commands/patches/{command,copy-patches,git-patch}.ts`, `surfer/src/commands/{export-file,update,build}.ts`, `surfer/src/commands/download/firefox.ts`, `surfer/src/constants/index.ts`, `surfer/README.md` (https://github.com/zen-browser/surfer)

GitHub data (via `gh api`, read on 2026-10-25):

- Repo, org, members, contributors, commits since 2026-04-25, releases (196), latest release assets, workflow run 39497770166 and its jobs, branch protection for `dev`.
- Issues: https://github.com/zen-browser/desktop/issues/7079 , /437 , /6302 , /3539 , /12008 , /8932 , /8606 , /7000 , /5817 , /12028 , /15995 , /16002 , /16054 , /9727 , /14793 , /13494 , /10689 , /11161 , /10498
- Discussions: https://github.com/zen-browser/desktop/discussions/2400 , /924 , /3152 , /869 , /889 , /2326 , /2337 , /820 , /800 , /4092 , /830 , /12025 , /12762 , /14678 , /14539 , /15045
- Advisories: https://github.com/zen-browser/desktop/security/advisories/GHSA-qpj9-m8jc-mw6q , GHSA-vjfv-85qf-v25c , GHSA-vpvg-hp3v-rm5q , GHSA-7p2r-fp29-9w69 , GHSA-cc9c-mmmf-c5j6
- Related repos: https://github.com/zen-browser/updates-server (static `update.xml`), https://github.com/zen-browser/share (Cloudflare Worker, `wrangler.toml`), https://github.com/zen-browser/theme-store , https://github.com/zen-browser/windows-binaries

Web:

- Zen release notes: https://zen-browser.app/release-notes/
- Zen privacy policy: https://zen-browser.app/privacy-policy/
- Zen donate page: https://zen-browser.app/donate
- Zen docs, building: https://docs.zen-browser.app/contribute/desktop/building
- Zen docs, window sync: https://docs.zen-browser.app/user-manual/window-sync
- Mozilla bug 1979083: https://bugzilla.mozilla.org/show_bug.cgi?id=1979083
- Firefox two-week cadence: https://blog.mozilla.org/sumo/2026/08/19/firefox-new-release-cadence-and-what-to-expect/ ; https://www.theregister.com/software/2026/07/17/mozilla-speeds-firefox-release-schedule-to-biweekly/5274423
- Chrome two-week cadence: https://developer.chrome.com/blog/chrome-two-week-release ; https://techcrunch.com/2026/09/08/chrome-is-now-shipping-updates-every-2-weeks-as-ai-changes-the-security-landscape/
- Benchmark: https://www.jitbit.com/alexblog/zen-review-benchmark/
- Reviews (third-party; some promote competing products): https://supasidebar.com/blog/zen-browser-mac-review-2026 ; https://www.producthunt.com/products/zen-browser/reviews ; https://en.wikipedia.org/wiki/Zen_Browser
- Profile location: https://github.com/bleachbit/bleachbit/pull/2394
- Coverage of recent releases: https://piunikaweb.com/2026/10/23/zen-browser-v1-23-4b-blocks-compromised-emudhra-certificates-and-adds-new-boosts-focus/

## Verification

Adversarial fact-check on 2026-10-25. I re-read the code at `9b604fe` (Zen) and
`b3fc8ab` (surfer), and re-queried the GitHub API, the `zen-browser/share` and
`zen-browser/updates-server` repos, Bugzilla, and the Mozilla and Chrome blogs.
"Confirmed" means a primary source matched. "Corrected" means the text above
was changed.

| # | Claim checked | Result | Primary source |
| --- | --- | --- | --- |
| 1 | MPL-2.0, no file marked "Incompatible With Secondary Licenses" | Confirmed. The phrase appears only inside MPL license texts. Every non-test `.mjs` under `src/zen/` has the MPL header. | `zen/LICENSE`; grep of the tree |
| 2 | Stable on Firefox 158.0.1, `dev` on 159.0 | Corrected wording: `dev` synced the 159.0 release candidate; `version` is still 158.0.1 | `surfer.json` on `dev` and `stable`; commit bc8e7ed |
| 3 | 45,275 stars, 1,899 forks, 808 open, 76 PRs, created 2024-03-28 | Confirmed (45,279 stars on recheck) | repo and search API |
| 4 | 67 releases in 12 months; Twilight every 2 days | Confirmed. Corrected the peak month: 23 releases in 2024-08, not 11 in 2024-09 | releases API (196 entries incl. `twilight-1`); `twilight-release-schedule.yml:5` |
| 5 | Lead dev 5,909 of 6,951 commits; 293 of 482 in 6 months; 14 members; 258 contributors; sole code owner | Confirmed | contributors, commits, members APIs; `CODEOWNERS` |
| 6 | Full 170.5 MB macOS update every release, no deltas; download counts | Confirmed. `update.xml` lists only `type="complete"` | releases API; `updates-server/.../Darwin_aarch64-gcc3/release/update.xml` |
| 7 | Session backups: 3-hour buckets, newest 20, every 10 min, clean copy, ordered recovery | Corrected. `clean.jsonlz4` is the previous file copied before every save, not a clean-shutdown copy. Recovery tries only two fallbacks. Take 1 and Strength 5 updated | `ZenSessionManager.sys.mjs:102-152,254-279,600-707` |
| 8 | Session save interval raised from 15 s to 40 s | Confirmed | `prefs/firefox/browser.yaml:124-126` |
| 9 | Compact Mode timings (150, 1,000, 800 ms; 200 and 100 px) | Confirmed. Added how the native tracker gives up, and that Linux has none | `compact-mode.yaml:14-29`; `nsIZenMouseTracker.idl` |
| 10 | Glance motion: 80% width, 350 ms, 91 keyframes, easeOutBack 0.6, arc cap 30 px, 87 ms fade, sextic close, background 0.97 and 0.3, 4 px drag threshold, Cmd allowed | Confirmed | `ZenGlanceManager.mjs:9,36-40,441-458,630-646,726-757,816,867-905,945-960,1211-1220,1862-1873`; `ZenGlanceChild.sys.mjs:29,159-167` |
| 11 | Space switch spring 250 ms, bounce 0, +50 ms timeout; swipe resistance | Confirmed | `ZenSpaceManager.mjs:2300,2368-2378,2499`; `ZenSpacesSwipe.mjs:204-216` |
| 12 | Tab open 0.12 s, close 0.1 s, scale 0.95, skipped on reduced motion | Confirmed | `ZenVerticalTabsManager.mjs:99-209` |
| 13 | Library spring 720/47/1.2 (ratio 0.80); onboarding 300/20/1.8 (ratio 0.43) | Confirmed, arithmetic rechecked | `ZenLibrary.mjs:597-610`; `ZenWelcome.mjs:229,987-989` |
| 14 | Motion v13.2.0, loaded on first use | Confirmed | `vendor/motion.dep`; `ZenUIManager.mjs:99-107` |
| 15 | Arc import field mapping; Dia pinned tabs encrypted; on `dev` only | Confirmed. `stable` does not contain commit 2ad1945 | `ZenProfileMigrators.sys.mjs:14-142`; `ChromeMigrationUtils-sys-mjs.patch:27-28`; compare API |
| 16 | Window sync on by default, no settings toggle; user quote | Toggle claim confirmed. The quote "This should have never been implemented as a default..." was not found in #12008 or #12025, so I replaced it with the lead developer's verified reply. Added that #924 requested the feature (416 votes); the fullscreen bug comes from #12008, not #924 | `prefs/zen/window-sync.yaml:5-6`; `zenTabsManagement.inc.xhtml`; GraphQL on discussions |
| 17 | Space routing rule types | Corrected: there is also an "equal-to" type | `ZenSpaceRoutingManager.sys.mjs:487-516` |
| 18 | Share server: Cloudflare Worker, KV, 30 days, 25 MiB, 2 creates per minute; API-key or secret-key auth | Confirmed (rate limit is per client IP) | `zen-browser/share` `wrangler.toml`, `worker.js:5,39-44`; `ZenShareClient.sys.mjs:35,66-73` |
| 19 | GitHub live folders scrape github.com with your cookies | Confirmed (`SEC_COOKIES_INCLUDE`) | `ZenLiveFolder.sys.mjs:125-155`; `GithubLiveFolder.sys.mjs:14-17,404` |
| 20 | Mods: 20-day auto-update, HTTPS only, no hash, store actor only on `zen-browser.app`; 77 mods, 274 open PRs | Confirmed | `prefs/zen/mods.yaml:8-24`; `ZenMods.mjs:321-330`; theme-store tree and search API |
| 21 | Advisories and severities | Confirmed. Fixed the 1.19.9b date to 2026-04-24. GHSA-vpvg is rated low, GHSA-7p2r medium | advisories API |
| 22 | Zen's own 4,096-bit MAR key valid to 9999 | Confirmed | `scripts/mar_sign.sh:17-26,54-69` |
| 23 | Updates from `updates.zen-browser.app` on GitHub Pages | Confirmed | `src/build/moz-build.patch:10`; Pages API |
| 24 | macOS cross-compiled on 8-vCPU Linux runners; 42 to 49 min builds; 4.5 h pipeline | Confirmed. Corrected sccache: optional and off in the 1.23.4b release run, so the times are cold builds | jobs API and job log of run 39497770166; `build.yml:24-28,95` |
| 25 | PGO training counts, LTO, `-mcpu=apple-m1`, cached profiles | Confirmed. Corrected: only Twilight reuses cached profiles | `ZenPGOTraining.sys.mjs:38-49`; `build.yml:290-310`; `configs/macos/mozconfig:51-64` |
| 26 | Release flags incl. `--disable-crashreporter`, `--disable-geckodriver` | Confirmed | `configs/common/mozconfig:53-90` |
| 27 | Release publish needs approval | Upgraded to FACT: `Deploy-Release` has required reviewers | environments API |
| 28 | Windows signed with a Certum certificate | Re-tagged INFERENCE: only the timestamp server is Certum's | `build/windows/sign.ps1:123,217-237` |
| 29 | Tests never run in CI; PR check is apply plus lint; `dev` has no required checks | Confirmed. Test count refined (plus about 148 imported xpcshell-style files) | `pr-test.yml`; grep of `.github/`; branch API; `src/zen/tests/` |
| 30 | Weekly Tuesday 04:59 UTC check, Discord ping, bot sync PR with "applied cleanly" text | Confirmed. The check job calls the sync workflow in release-candidate mode | `check-candidate-release.yml:4-33`; `sync-upstream.yml:60-141` |
| 31 | Firefox two-week majors from 155 on 2026-09-01; Chrome from 153 on 2026-09-08 | Confirmed | Mozilla SUMO blog; Chrome developer blog |
| 32 | Zen synced Firefox 155 to 159 within days | Confirmed; several synced from release candidates | commits API since 2026-04-25 |
| 33 | Patch layer: 265 + 6 patches, 958 hunks, 291 files, +4,087/-1,046 | Corrected: 264 own + 7 external; 958 hunks and 287 files only when both are counted; own patches +3,677/-1,052 | `grep` and `git apply --numstat` over `zen/src/**/*.patch` |
| 34 | `browser.xhtml` hook is 6 added lines | Corrected: +5 / -1, of which 2 are includes | `browser-xhtml.patch` |
| 35 | 56,300 lines of JS, 72,000 lines in new files | Corrected: 67,500 raw JS lines (55,800 without blanks and comments); about 83,000 raw lines in total | `wc -l` over `src/zen/` |
| 36 | About 200 Zen prefs; about 30 YAML files | Corrected: 156 declared `zen.*` prefs; 40 YAML files, 28 of them Zen's | grep of `prefs/` |
| 37 | #6302 story (blend modes; fix in Firefox 150) | Corrected: nical withdrew the blend-mode cause; the main fix reached Zen with Firefox 141; bug 1979083 is a Linux-only leftover fixed in 150 | #6302 comments; Bugzilla REST for bug 1979083 |
| 38 | Reaction and vote counts (#12008, #6302, #3539, #8932, #437, #889, #2326, #2337, #830, #12762, #14678, #1691) | Confirmed | issues API; GraphQL `upvoteCount` |
| 39 | Data-loss search counts 230, 48, 99 | Confirmed with queries "lost tabs", "workspaces disappeared", "pinned tabs gone" | search API |
| 40 | Preconnect stays on ("No, it won't be disabled by default"); icons bundled locally | Confirmed (lead dev, 2025-04-29 and 04-30) | #7000 comments |
| 41 | February 2026 median first response 2 h 8 min; close 3 h 31 min | Confirmed (averages are over a day) | `docs/issue-metrics/2026_2026-02-01..2026-02-28.md:5-6` |
| 42 | Privacy policy dated 2025-02-05, says no telemetry or crash reports, omits sharing and Safe Browsing | Confirmed | https://zen-browser.app/privacy-policy/ |
| 43 | Spaces Sync engine version 3, six record kinds, opt-in on stable | Confirmed | `ZenSpacesSync.sys.mjs:125-141`; `ZenSpacesSyncModel.sys.mjs:46-53`; `prefs/zen/sync.yaml:5-7` |
| 44 | 12 haptic call sites; 6 pinned-tab Cmd+W options; Essentials max 12; split max 4 | Confirmed | grep `playHapticFeedback()`; `ZenPinnedTabManager.mjs:357-452`; `zen.yaml`; `ZenViewSplitter.mjs:87` |

**Not re-verified (tags left as they were):** the Speedometer run and the
third-party reviews (CLAIM); the profile folder path (CLAIM); the
`mauro-balades` to `mr-cheffy` account link (INFERENCE, though #7000 comments
address `mr-cheffy` posts as `@mauro-balades`, which supports it); visual
values such as squircle factors, tab colors and CSS totals; ship versions known
only from release notes (folders 1.15b, iframe translation 1.21.15b); whether
WebDriver BiDi works in release builds; and whether Chromium can cross-compile
macOS on Linux.

**What changed for rac's plans.** Take 1 now says to keep a copy of the previous
save and to try every backup, because Zen tries only two fallbacks. The CI
comparison is stronger than first written: Zen's 45-minute macOS builds run with
no compiler cache. The window-sync lesson now notes that the feature was a
popular request; the failure was forcing it on with no setting.

**No fabrications found.** Every cited file, issue, discussion, advisory and run
exists. The errors were miscounts, one misread mechanism (`clean.jsonlz4`), one
quote I could not find, and a source mix-up (#924).

**Overall confidence: high** for the code-backed facts above. Medium for
counts that move daily (stars, downloads) and for anything tagged CLAIM.
