# Ora: research dossier

Researched 2026-10-25 from a shallow clone of `github.com/the-ora/browser`
(commit `4e6cfd1`, 2026-09-17) at `/tmp/rac-overhaul/src/ora`, the website
source `github.com/the-ora/www` at `/tmp/rac-overhaul/src/ora-www`, the GitHub
API, and web sources. I did not run Ora: cloned code is untrusted and the
rules forbid building it. Everything about how it looks and feels comes from
reading the code, not from using the app.

Tags: **FACT** = primary source (code, API, whois). **CLAIM** = the project's
own marketing or a self-report. **INFERENCE** = my reasoning from the code.

## In plain English (at most 150 words)

Ora is a free, open-source Mac browser that copies Arc's layout. It runs
inside a small Swift app on WebKit, the engine Safari uses. It has a sidebar,
spaces, pinned tabs, favorites, a quick launcher, an ad blocker, and a
password manager. Each space keeps its own logins, so work and personal
sites stay apart. It has no AI assistant, no agent, and no extensions. Its
README says it is not ready for daily use. Two people wrote most of it.
The last release came out in April 2026. The website's domain expired in
September. For rac, Ora is mostly a source of small polish ideas with exact
timings. It is also a list of mistakes to avoid. Ora never asks a site
before it uses the camera or microphone. Only macOS asks, once, for the
whole app. The code also suggests a page could fake the address Ora shows.

## Snapshot

| Field | Value |
| --- | --- |
| What it is | A native macOS browser shell, styled after Arc, around the system WebKit. The home page says "Less noise, more browsing." (FACT, `ora/Features/Browser/Views/HomeView.swift:41`). The README's tagline is "Fast, native WebKit browser for macOS." (FACT, `README.md:4`) |
| Engine | Apple's system WebKit, used through the public `WKWebView` API. No fork and no patches. The engine version is whatever Safari version the user's macOS has (FACT, `ora/Core/BrowserEngine/BrowserPage.swift:23-53`) |
| Platforms | macOS 15 or later only (FACT, `project.yml` `deploymentTarget: "15.0"`). A Windows build would need a rewrite, because the app is SwiftUI, AppKit, and `WKWebView` (INFERENCE, the code). Issue #247's comments say the same, but they come from users; no maintainer replied (FACT, issue #247) |
| License | MIT until 2025-10-03, then GPL-2.0, then GPL-3.0 since 2026-03-12 (FACT, commit `fe66211` "Change license from MIT to GPL-2.0", commit `df68105`, PR #223). The website still says "MIT licensed". That is stale, not invented (FACT, `ora-www/src/components/features.tsx:86`, `public/llms.txt:10`) |
| Repo | `github.com/the-ora/browser`. Org `the-ora` created 2025-07-03. Repo created 2025-08-09 (FACT, GitHub API) |
| Stars and activity | 2,241 stars, 98 forks, 11 watchers, 25 open issues and PRs (FACT, API 2026-10-25). 451 commits in total. 18,524 DMG downloads across 58 releases. The latest release, v0.2.14, has 4,390 (FACT, API) |
| Age | About 16 months since the org was created. First public build was v0.0.18 on 2025-09-04 (FACT, releases API). A test file says "Created by keni on 6/21/25" (FACT, `oraTests/oraTests.swift:5`) |
| Release cadence | 39 releases on 2025-09-05/06 while testing the pipeline. Then 13 releases from 2025-09-08 to 2025-10-29, usually days apart, and one on 2025-12-11. Then 0.2.12 to 0.2.14 in March and April 2026. **No release since 2026-04-07.** One commit since then (2026-09-17) (FACT, `git log`, releases API) |
| Team size | Two core authors: `yonaries` (223 commits) and `kenenisa` (178), which is 89% of all commits. 21 other contributors have 1 to 7 commits each (FACT, contributors API). Yonathan calls himself a "co-creator" (CLAIM, [Vercel community post](https://community.vercel.com/t/ora-browser-the-open-source-arc-alternative-for-macos/29424)) |
| Business model | Donations through GitHub Sponsors and Buy Me a Coffee (FACT, `README.md`, `.github/FUNDING.yml`). Member of the Vercel OSS Fall '25 cohort (CLAIM, Vercel post; the README shows the Vercel OSS Program badge, FACT, `README.md:5-7`). No paid tier and no accounts |
| Status signals | The README says "not ready for daily use yet" (FACT). `orabrowser.com` expired on 2026-09-05 and is in the registry's `redemptionPeriod` (FACT, `whois`, 2026-10-25). It does not resolve in DNS. A user reported "The website is down" on 2026-10-23 (FACT, issue #247) |

## Features

Status key: **shipped** = in `main` and reachable in the UI. **partial** = in
the code but incomplete or not wired. **planned** = in the roadmap or an
issue. **rejected** = closed as "not planned".

### Tabs, sidebar, spaces

| Feature | Status | Evidence and notes |
| --- | --- | --- |
| Vertical sidebar, on the left or right | shipped | Menu item "Right Side Tabs" / "Left Side Tabs" (FACT, `ora/App/OraCommands.swift:93-95`). Width is a fraction of the window, default 0.20 and range 0.16 to 0.30 (FACT, `SidebarManager.swift:13-14`, `FloatingSidebarOverlay.swift:4-5`) |
| Hide sidebar (Cmd+S) and edge reveal | shipped | The sidebar floats over the page when the mouse reaches the edge. Trigger strip is 10 pt; after that 40 pt of "armed" padding and 8 pt of vertical slack (FACT, `FloatingSidebarOverlay.swift:47,75-76`, `GlobalMouseTrackingArea.swift`). Ora inserts an invisible full-height `div` into the page under the floating sidebar to block hover effects (FACT, `BrowserView.swift:38-63`) |
| Spaces ("containers") with emoji icon and name | shipped | SwiftData `TabContainer` (FACT, `Tabs/Models/TabContainer.swift`). The default emoji for a new model is "💩" (FACT, line 22). Spaces have no colors or themes. "Add theme colour selection" was closed as not planned (FACT, issue #153) |
| Switch spaces with a two-finger swipe, plus dots at the bottom | shipped | `NSPageController` with `.horizontalStrip` (FACT, `Shared/Layout/NSPageView.swift:65`). Emoji switcher with a compact mode when crowded (FACT, `ContainerSwitcher.swift`). Pages are keyed by space **name**, so two spaces with the same name may confuse the pager (INFERENCE, `SidebarView.swift:163`) |
| Each space has its own cookies, storage, and cache | shipped | `WKWebsiteDataStore(forIdentifier: space.id)` (FACT, `BrowserEngineProfile.swift:15`, PR #79, 2025-09-11). Each space is effectively a separate login profile |
| Per-space settings | shipped | Default search engine, default "AI chat" site, auto-clear tabs after a set time (never, 1 hour, 1 day, 1 week), tracker blocking, fingerprinting protection, ad-block lists and update policy, cookie policy (FACT, `SettingsStore.swift:168-182`, `SpacesSettingsView.swift`) |
| Favorites (icon grid) | shipped | `TabType.fav`. Favorites belong to **one space**, not the whole browser (FACT, `Tab.swift:5-9`). The grid has up to N columns and animates column changes (FACT, `FavTabsList.swift:21-28,64`) |
| Pinned tabs that remember their URL | shipped | `savedURL` is set when a tab is pinned and loaded on restore (FACT, `TabManager.swift:113-123`, `Tab.swift:235`). There is **no "reset to pinned URL"** action (FACT, the context menu has none, `TabItem.swift:210-253`) |
| Folders | planned | The `Folder` model and a `TabContainer.folders` relationship exist, but no code creates a folder. Only space deletion touches them (FACT, `TabContainer.swift:15`, `TabManager.swift:678`). Issue #182 is open |
| Drag to reorder and to move between sections | shipped | `TabDropDelegate`, `SectionDropDelegate`. Issue #174 reports laggy drags and empty tabs (FACT) |
| Move a tab to another space | shipped | Context menu "Move to Container" (FACT, `TabItem.swift:233-246`) |
| Suspend inactive tabs | shipped | The WebView is destroyed after 1 hour by default. Options are 1, 6, 12, 24, or 48 hours, or "Never" (FACT, `SettingsStore.swift:295-310`) |
| Auto-close old tabs (like Arc's archive) | shipped | Normal tabs close after 24 hours by default (FACT, `SettingsStore.swift:312-319`). A 60-second timer checks every tab in every space (FACT, `TabManager.swift:543`). Closed tabs are **not archived**. Only the last 5 can be reopened, and that list lives in memory (FACT, `TabManager.swift:62`) |
| Reopen closed tab (Cmd+Shift+T) | shipped | 5 tabs, in memory only (FACT) |
| Tree-style tabs | rejected | PR #152 had a working prototype and was closed as "not planned" (FACT, 2026-03-07) |
| Rename tab titles | rejected | PR #204 closed as "stale" by `yonaries` on 2026-03-13. Issue #201 closed as not planned by `linear[bot]` on 2026-07-07 (FACT) |

### Navigation and command bar

| Feature | Status | Evidence and notes |
| --- | --- | --- |
| Launcher (command bar) on Cmd+T and on the empty home page | shipped | Cmd+T opens the launcher instead of a blank tab (FACT, `OraCommands.swift:19-21`, `HomeView.swift:48`). It shows open tabs, a "go to URL" row, the default search, Google suggestions, history, and AI-chat rows (FACT, `LauncherViewModel.swift:49-80`) |
| Engine aliases plus Tab to scope a search | shipped | 16 built-in engines with aliases, such as `yt`, `g`, `ddg`, `kg`, `cl`, `pplx`, `t3`, `gem` (FACT, `SearchEngineService.swift:66-196`). Pressing Tab turns the alias into a colored capsule and sweeps a brand-colored border around the launcher (FACT, `LauncherView.swift:23-34,90-93`, `SearchCapsule.swift`) |
| Custom search engines | shipped | `{query}` templates. The favicon and its average color are fetched for the capsule (FACT, `SettingsStore.swift:36-136`) |
| URL bar in the toolbar, or in the sidebar when the toolbar is hidden | shipped | Cmd+Shift+D hides the toolbar. The URL then shows in the sidebar (`SidebarURLDisplay`) or as a floating bar when the sidebar is on the right (FACT, `BrowserView.swift:92-97`, `ContainerView.swift:20`) |
| Toolbar tinted with the page's top color | shipped | Ora snapshots the top 24 px of the page and shrinks it to one pixel to get the color. Text turns white or black at luminance 0.5 (FACT, `TabBrowserPageDelegate.swift:209-227,263-289`, `URLBar.swift:39-42,254`) |
| Ctrl+Tab switcher of recent tabs with thumbnails | shipped | Up to 5 cards, each 200x125. Releasing Ctrl picks the tab (FACT, `FloatingTabSwitcher.swift:23-28,63`) |
| Cmd+1 to Cmd+9 | shipped | Order is favorites, then pinned, then open tabs. Cmd+9 picks the last tab (FACT, `TabManager.swift:569-595`) |
| Find in page | shipped | Wraps matches in `<mark>` elements with mark.js, which changes the page's DOM (FACT, `FindInPage/FindController.swift:14-70`) |
| Copy URL (Cmd+Shift+C) with an animated label | shipped | FACT, `CopiedURLOverlay.swift`, `ClipboardUtils.swift` |
| "Clear cache & reload" (Cmd+Shift+R), "Clear cookies & reload" (Cmd+Opt+Shift+R) for the current site | shipped | FACT, `OraCommands.swift:109-117`, `OraRoot.swift:290-332` |
| Hover link preview at the bottom left | shipped | It also always shows the app version string (FACT, `LinkPreview.swift:28`) |
| Middle-click opens in new tab; mouse buttons 4 and 5 go back and forward | shipped | Done with a JavaScript `elementFromPoint` lookup (FACT, `BrowserPageView.swift:178-253`) |
| Zoom, history window (Cmd+Y), DevTools toggle shortcuts | partial | Defined in `KeyboardShortcuts.swift:228-266` but not wired to anything (FACT, no callers). Pinch-to-zoom works (FACT, `BrowserPage.swift:72`) |
| Custom keyboard shortcuts | shipped | Settings, then Shortcuts (FACT, `ShortcutsSettingsView.swift`) |
| History view | planned | Issue #185. A community PR (#130) was closed as "stale" (FACT) |
| `window.open` popups (for example OAuth) | partial | Popups open as normal tabs, and the opener link is lost (FACT, `BrowserPage.swift:426-436`). Issue #172 is open |
| External URL schemes (`mailto:`, `zoommtg:`) | missing | Dropped silently. A fix PR (#251) was closed by its author (FACT) |

### Split view, peek, small windows

| Feature | Status | Evidence |
| --- | --- | --- |
| Split tabs | planned, earlier attempt rejected | Issue #167 is open. PR #152's split was closed as "not planned" (FACT). The website advertises "Split View" anyway (FACT, `ora-www/src/components/features.tsx:36`) |
| Peek (preview a link in an overlay) | planned | Issue #169 (FACT) |
| Little Arc (a small quick window) | rejected | Issue #203 closed as not planned (FACT) |
| Auto picture-in-picture on tab switch | shipped, on by default | FACT, `TabManager.swift:445-450`, `OraBrowserScripts.swift:272-294` |
| Mini media player in the sidebar for media playing in other tabs | shipped | FACT, `Player/Views/GlobalMediaPlayer.swift`. Issue #187 says it shows up with no media playing |

### Import, sync, profiles

| Feature | Status | Evidence and notes |
| --- | --- | --- |
| Arc import (menu File, Import Data, Arc) | shipped, likely broken | Reads `~/Library/Application Support/Arc/StorableSidebar.json` (FACT, `Importer.swift:154`). Imports each space's pinned tabs and the favorites (`topAppsContainerIDs`). No folders, history, passwords, or open tabs (FACT, `Importer.swift:182-271`). Because the app is sandboxed, `~` points inside Ora's own container, so the file is probably never found (INFERENCE, `project.yml` `app-sandbox: true`). It loads a live WebView for every imported tab (FACT, `ImportDataButton.swift:33-42` calls `addTab`, which loads at `TabManager.swift:276`). It adds every favorite to **every** new space (FACT, `ImportDataButton.swift:53-86`). Issue #99, a crash on import, was closed by the Linear bot as not planned (FACT) |
| Safari and Chrome import | missing | Empty button handlers (FACT, `ImportDataButton.swift:96-101`) |
| Sync | passwords only, maybe | Ora marks password items as synchronizable for iCloud Keychain (FACT, `PasswordManagerService.swift:266`). Whether they really sync is unverified; the code sets no keychain access group (INFERENCE). Tabs, spaces, and history do not sync (FACT) |
| Profiles | via spaces | Each space is its own cookie jar (see above). There is no separate profile concept |
| Private windows | shipped | Cmd+Shift+N. In-memory database. Each private **tab** gets its own temporary data store, so logins do not carry between private tabs (FACT, `BrowserEngine.swift:46-49`) |
| Session restore | shipped | Tabs live in SwiftData. A tab's WebView is only created when you open it (FACT, `TabManager.swift:452-482`) |

### Privacy and blocking

| Feature | Status | Evidence and notes |
| --- | --- | --- |
| Ad blocking with AdGuard lists | shipped, **off by default** | Built-in lists: AdGuard Base and Mobile Ads (recommended), Tracking Protection, URL Tracking, Annoyances, plus custom list URLs (FACT, `FilterListCatalogService.swift:12-68`). AdGuard's `SafariConverterLib` turns them into WebKit rule lists. A list is split in half again and again until WebKit accepts it (FACT, `ContentBlockerCompileService.swift:58-75`). If a refresh fails, the last working version stays in use (FACT, test `failedAdBlockRefreshPreservesLastKnownGoodRevision`). Refresh modes: on launch plus daily, every 6 hours, or manual (FACT, `AdBlockModels.swift:3-33`). Off by default (FACT, `SpacePrivacySettings.swift:12`) |
| Tracker blocking | shipped, off by default | A hard-coded list of 25 domains (FACT, `BrowserPrivacyService.swift:598-624`) |
| Fingerprinting protection | shipped, **on by default** | A JavaScript script fakes `navigator`, screen, WebGL, canvas, and audio values (FACT, `BrowserPrivacyService.swift:5-370`). It overrides `navigator.webdriver` with a script getter (FACT, `BrowserPrivacyService.swift:247`). A contributor reports this breaks Google sign-in ("This browser or app may not be secure"), tested on macOS 26 only (CLAIM, PR #252, open and unmerged since 2026-10-15) |
| Cookie policy per space | shipped | Allow all (default), block third-party, block all (FACT) |
| Site permissions | **missing** | Every camera and microphone request from a site is granted with no per-site prompt (FACT, `TabBrowserPageDelegate.swift:129-136`, `BrowserPage.swift:398-408`). The latest release, v0.2.14, lacks the macOS usage strings; a contributor reports camera and mic just hang there (CLAIM, PR #250). Since 2026-09-17, `main` has the strings, so macOS asks once for the whole app. That fix is unreleased (FACT, `project.yml:62-63`, commit `4e6cfd1`). A `sitePermissions` setting is stored but never read (FACT, a grep finds no users) |
| Password manager | shipped, on by default | Fills from a popup over the field, generates strong passwords, offers to save on submit, and can submit after filling (on by default). Its own window, Passwords, then Manage Passwords (FACT, `PasswordAutofillCoordinator.swift`, `SettingsStore.swift:325-335`) |
| Passkeys | planned | Holds the `web-browser.public-key-credential` entitlement (FACT, `ora.entitlements`). Listed as near-term (FACT, `ROADMAP.md`) |
| 1Password and Bitwarden integration | planned, commented out | FACT, `PasswordManagerProviderRegistry.swift:51-66` |

### AI assistant

| Feature | Status | Evidence |
| --- | --- | --- |
| Built-in assistant or chat | **rejected** | PR #136, an AI chat with your own OpenAI key opened with Cmd+/, was closed with "not planned for now" by `yonaries` on 2026-03-07 (FACT) |
| "AI chat" as search destinations | shipped | The launcher hands your text to ChatGPT, Claude, Grok, Gemini, Perplexity, T3 Chat, Copilot, GitHub Copilot, or Meta AI as a `?q=` URL (FACT, `SearchEngineService.swift:74-196`). The empty launcher shows Grok, ChatGPT, Claude, and Gemini rows by default (FACT, `LauncherViewModel.swift:94-108`). Each space can pick a default AI site (FACT, `SettingsStore.swift:351-358`) |

### Agent

None. No browser control, no automation, no tool calls (FACT, nothing in the
code).

### Extensibility (CLI, MCP, API, extensions, mods)

| Feature | Status | Evidence |
| --- | --- | --- |
| Web extensions | planned. Prototype stalled | Draft PR #137 (+4,405 lines, conflicting with `main`, last updated 2026-03-14) uses `WKWebExtensionController`. It grants every extension `<all_urls>` and a fixed list of permissions without asking (FACT, `feat/extensions:ora/Services/Extentions/ExtensionManager.swift:88-120`). A tester reported the 1Password extension failing with `runtime.connect()` errors (CLAIM, a user's PR comment, 2025-10-07). Maintainer `kenenisa` on 2026-01-24: too many APIs are "not available out of the box from the webkit api" (FACT) |
| CLI, MCP, local API, AppleScript | none | FACT, no such code |
| Boosts or mods (custom CSS/JS per site) | none | FACT |
| Developer tools | shipped | Safari Web Inspector (`developerExtrasEnabled`, `isInspectable`) (FACT, `BrowserPage.swift:27-30,75`) |

### Other

- Downloads: progress widget in the sidebar, plus a downloads history "page" you swipe to from the first space (FACT, `SidebarView.swift:64-146`, `Downloads/`).
- Quit confirmation dialog on Cmd+Q (FACT, `OraRoot.swift:152-167`).
- Set as default browser from Settings (FACT, `DefaultBrowserManager.swift`).
- Web notifications: planned (FACT, issue #183).
- Reader mode and bookmarks: on the website's "planned" list, not in the code (CLAIM, `ora-www/public/llms.txt`; FACT, absent from the code).

## UI, look, and feel

### Layout

- A window with the title bar hidden and its own traffic-light buttons drawn from image assets (FACT, `OraApp.swift:83`, `Assets/Catalogs/WindowControls.xcassets`). Default size 1440x900, minimum 500x360 (FACT, `OraApp.swift:79-84`).
- Sidebar and content sit in a vendored SwiftUI `HSplit` with an invisible divider. You can drag the sidebar to hide it (FACT, `BrowserSplitView.swift:40-53`, `Shared/Layout/SplitView`, MIT, from stevengharris/SplitView).
- Sidebar from top to bottom: header, the URL display (when the toolbar is hidden), favorites grid, pinned tabs, open tabs, mini media player, then a bottom row with downloads, space dots, and new space (FACT, `SidebarView.swift:151-209`, `ContainerView.swift`).
- Above the page: a toolbar (back, forward, reload, URL field, share menu) tinted with the page's color (FACT, `URLBar.swift:180-256`).
- Overlays: launcher, Ctrl+Tab switcher, toasts, dialogs, find bar at the top right, link preview at the bottom left (FACT, `BrowserView.swift:74-81`, `BrowserWebContentView.swift:69-90`).

### Visual language and materials

- Window background: `NSVisualEffectView` `.underWindowBackground`, `.behindWindow`, with a 30% theme tint on top (FACT, `BrowserView.swift:69-73`, `Theme.swift:28-30`).
- Popover-style surfaces: the switcher uses `.popover` within the window. The find bar uses `.ultraThinMaterial` (FACT, `FloatingTabSwitcher.swift:103`, `FindView.swift:264`).
- On macOS 26, built with Xcode 26, corners use the system `ConcentricRectangle` (Liquid Glass-era nested corners). Older builds fall back to rounded rectangles (FACT, `Shared/Shapes/ConditionallyConcentricRectangle.swift`).
- Corner radii: tabs and URL field 10, launcher 20, settings cards 16, password popup 18, dialogs 11, switcher frame 32, Tab-to-search capsule 99 (fully round) (FACT, grep of `cornerRadius`).
- Shadows are soft and large. Launcher: black 10%, radius 40, y 24. Password popup: 12%, r 20, y 8. Settings card: 6%, r 12, y 6 (FACT, `LauncherMain.swift:91-94`, `PasswordAutofillOverlayView.swift:26`, `SettingsCard.swift:39`).

### Typography

- Only the system font (SF). Sizes are hard-coded, mostly 12 to 14 pt, with `.caption` the most common style (32 uses) (FACT, a grep of `.font(`). No custom typeface.

### Color and themes

- One fixed brand palette. Light primary `#f3e5d6` (cream). Dark primary `#141414`, dark background `#0F0E0E`. Accent `#F16D34` in light mode and `#FF9B51` in dark (FACT, `Core/Constants/Theme.swift:8-22`).
- Light, dark, and system appearance (FACT, `OraCommands.swift:61-75`). Spaces have no themes and no gradients (FACT).
- The search capsules use brand colors, for example Claude `#d97757` and Perplexity `#20808D` (FACT, `Theme.swift:96-134`).

### Motion (exact parameters from code)

SwiftUI `spring(response:dampingFraction:)` means: response = seconds to
settle, damping 1.0 = no bounce. `spring(duration:bounce:)` is Apple's newer
form.

| Interaction | Parameters | Source |
| --- | --- | --- |
| Hide or show the sidebar (Cmd+S) | `spring(response: 0.2, dampingFraction: 1.0)` | `SidebarManager.swift:27` |
| Edge-reveal floating sidebar | `.move(edge:)` transition, `easeOut(0.1)` | `FloatingSidebarOverlay.swift:30`, `BrowserView.swift:101` |
| Space switch from the dots | `easeOut(0.1)` wraps the SwiftUI state change. The page move itself runs in `NSAnimationContext` with no duration set, so AppKit's default applies, about 0.25 s (INFERENCE) | `SidebarView.swift:211-214`, `NSPageView.swift:155-163` |
| Downloads page swipe | `DragGesture(minimumDistance: 30)`. Commits past 25% of the width, or when the predicted end passes 50%. Commit `spring(0.45, 0.88)`. Cancel `spring(0.35, 0.9)`. The spaces layer behind it moves x by 12% times progress, scales by 1 minus 0.06 times progress, and fades to 50% | `SidebarView.swift:64-146` |
| Launcher open | Backdrop black 30%. Card scale 0.9 to 1, opacity 0 to 1, blur 2 to 0, `easeOut(0.1)`. Fixed 250 pt from the top. Width 320 to 814 | `LauncherView.swift:69-99`, `LauncherMain.swift:78` |
| Tab-to-search border sweep | Angular gradient spins 360 degrees, `linear(0.8)`, once. Then fades out with `easeOut(0.3)`. 2 pt main stroke plus an 8 pt glow stroke, blur 40, opacity 0.9, radius 16 | `Shared/Modifiers/GradientAnimatingBorder.swift` |
| URL field to inline launcher | `.blurReplace` transition, `easeOut(0.25)`. Suggestions use `.move(edge: .top)` plus opacity. Page dims to black 15%, `easeOut(0.2)` | `URLBar.swift:79,214-256`, `BrowserWebContentView.swift:33-46` |
| Toolbar hide (Cmd+Shift+D) | `easeInOut(0.2)`. Push from top on show, push from bottom on hide | `OraRoot.swift:206`, `BrowserWebContentView.swift:21-26` |
| Copy URL "wheel" | The URL label rolls out by ±12 pt and "Copied Current URL" rolls in, `easeOut(0.3)`. Stays 1.0 s | `CopiedURLOverlay.swift`, `ClipboardUtils.swift:18-36` |
| Tab insert and remove | Insert from the bottom, remove to the top, with opacity. `spring(0.3, 0.8)` | `NormalTabsList.swift:48-52` |
| Tab drag | `spring(0.2, 0.8)`. 1 pt dashed outline `[5, 5]`. Drop reorder `spring(0.3, 0.8)` | `TabItem.swift:145-172`, `TabDropDelegate.swift:45-48` |
| Ctrl+Tab switcher | Backdrop `easeOut(0.3)`. Focus moves with `easeOut(0.1)`. The focused card gets a glow, theme primary 30%, r 8 | `FloatingTabSwitcher.swift:74,118-124` |
| Dialogs | In and out: y −16, scale 0.96, opacity. `spring(0.3, 0.82)` on the overlay; the manager's `withAnimation` uses `spring(0.3, 0.8)`. Backdrop black 40% | `Shared/Components/Dialog/DialogView.swift:95-115`, `DialogManager.swift:9-71` |
| Toasts (stacked like the Sonner library) | Show `spring(duration: 0.4, bounce: 0.2)`. Dismiss `spring(0.3, bounce: 0.15)`. Restack `spring(0.3, bounce: 0.5)`. Exit is a "genie" warp: width −15%, height −25%, tilt about 3.4 degrees, slide 16 pt, perspective 1/1200. Swipe away `easeIn(0.15)`; snap back `spring(0.3, bounce: 0.3)`. 3 visible at most, collapsed offset 8, each step back 5% smaller. Lasts 4.0 s | `Shared/Components/Toast/ToastView.swift:16-90,125-175`, `ToastManager.swift:12-47` |
| Hover states | `easeOut(0.15)` nearly everywhere. Buttons `easeInOut(0.12)`. Press scale 0.95 | `ContainerSwitcher.swift:74`, `OraButton.swift:163`, `FindView.swift:330` |
| Reduced motion | **Not handled anywhere.** No reads of `accessibilityReduceMotion` | FACT, grep |

### Signature interactions that probably feel great (INFERENCE from code)

1. **Tab to search with a color sweep.** Type `cl`, press Tab, and the
   input becomes a Claude-orange capsule while a single 0.8 s orange glow
   circles the launcher. It plays once, so nothing keeps repainting.
2. **Copy URL as a rolling label** in place of a toast. The feedback appears
   where your eyes already are.
3. **Downloads as a page beside your spaces.** Swiping left from the first
   space slides downloads in and pushes the spaces back. The space-swipe
   gesture now also covers downloads.
4. **Ctrl+Tab recent-tab cards with live thumbnails.** Release Ctrl to
   switch. The mouse only takes over after it moves.
5. **Tuned springs.** Dialogs use response 0.3 and damping 0.82. Toasts bounce
   0.2 in and 0.15 out. These are consistent and calm.

### Things that feel bad (FACT unless marked)

- Cursor glitches across the UI (issue #245). Laggy tab drags that leave
  empty tabs (#174). Hidden WebViews show hover tooltips from layers
  underneath (#173). A single Esc exits full screen (#179). Sites can grab
  Cmd+S (#151).
- JavaScript alerts, confirms, and prompts use `NSAlert.runModal()`, which
  blocks the whole app, not just the tab (`TabBrowserPageDelegate.swift:152-193`).
- The launcher always sits 250 pt from the top, whatever the window height
  (`LauncherView.swift:95`).
- The toolbar tint is sampled every 0.25 s while a page loads
  (`Tab.swift:168-177`). Expect color flicker on pages that change their
  header (INFERENCE).
- No reduced-motion support. The empty launcher shows four AI rows (Grok,
  ChatGPT, Claude, Gemini) to everyone (`LauncherViewModel.swift:94-108`).

## Architecture

### Process model

- A single SwiftUI `App` process (`@main OraApp`) with three
  `WindowGroup`s: normal, private, settings (FACT, `OraApp.swift:68-118`).
- WebKit runs its own web content, networking, and GPU processes for each
  `WKWebView`. Ora does not manage processes itself (INFERENCE, standard
  `WKWebView` behavior).
- One `WKWebView` per live tab, created when you first open the tab and
  destroyed after the inactivity timeout (FACT, `Tab.swift:200-239,295-300`).
- **Each window builds its own state:** `TabManager`, `HistoryManager`,
  `DownloadManager`, a new `ModelContainer` and `ModelContext` on the same
  SQLite file, and even its own Sparkle `UpdateService`, which starts its
  own `SPUUpdater` (FACT, `OraRoot.swift:15-76`, `UpdateService.swift:19-41`). Two windows
  can hold two copies of the same tab objects (INFERENCE).
- Commands travel over `NotificationCenter`. Each handler checks
  `note.object === window` to target the key window (FACT, `OraRoot.swift:152-332`).

### Engine integration

- **A separate shell around the system framework.** There is no fork and
  there are no patches. A thin `BrowserEngine` layer (`BrowserEngine`,
  `BrowserEngineProfile`, `BrowserPage`, `BrowserPageDelegate`, plain Swift
  types) was split out in PR #237 on 2026-03-14 (FACT,
  `ora/Core/BrowserEngine/`). The split hints at a possible engine swap later
  (INFERENCE).
- Some settings go through key-value coding on `WKPreferences`
  (`developerExtrasEnabled`, `allowsPictureInPictureMediaPlayback`), which is
  semi-private API (FACT, `BrowserPage.swift:27-39`).
- The page bridge is message handlers registered in the **page world**:
  `listener`, `linkHover`, `mediaEvent`, `passwordManager`. All scripts are
  injected without an isolated content world (FACT, `BrowserEngine.swift:29`,
  `BrowserPage.swift:58-68`). So any page script can post to them
  (INFERENCE, WebKit's default world semantics).
  - The `listener` handler sets `tab.url` from the page-supplied `href`
    without comparing it to `webView.url` (FACT, `TabBrowserPageDelegate.swift:113-114,229-241`).
    The address bar renders `tab.url` (FACT, `URLBar.swift:61`,
    `SidebarURLDisplay.swift:138`). So a page can probably make the
    address bar show another site's address, and write that address into
    history (INFERENCE, untested).
  - The password bridge is safer. Save and fill use the native
    `page.currentURL`, not the hostname sent by the page (FACT,
    `PasswordAutofillCoordinator.swift:284-292,347-356`).
- User agent: a hard-coded Safari 26.0.1 string is set through
  `applicationNameForUserAgent`. WebKit appends that to its own UA, so the
  UA is sent twice (FACT, `BrowserEngine.swift:21`, `BrowserPage.swift:24`;
  confirmed by PR #252).
- Background work in every page: a `setInterval` every 500 ms checks the
  URL and title, and a `MutationObserver` on the whole document re-runs
  `querySelectorAll('video, audio')` on every DOM change (FACT,
  `OraBrowserScripts.swift:88,209-211`).

### UI technology

- SwiftUI with AppKit pieces: `NSPageController`, `NSVisualEffectView`,
  `NSEvent` local monitors for mouse and keys, and custom window controls
  (FACT, `Core/Platform/Representables/`).
- Hot reload in debug builds through InjectionIII and the `Inject` package
  (FACT, `OraApp.swift:11-14`, `project.yml`).

### Languages and dependencies

- Swift, in 5.9 language mode. About 25,600 lines in 171 files. Of that,
  1,956 lines are hand-drawn icons and 1,501 lines are vendored SplitView
  (FACT, `wc -l`). JavaScript: `password-manager.js` (409 lines), inline
  scripts (about 300 lines), and vendored mark.js 8.11.1.
- Swift packages: Sparkle 2.6 or later, Inject 1.5.2, FaviconFinder 5.1.5,
  AdGuard SafariConverterLib 4.2.2 (FACT, `project.yml:5-17`).

### Code layout (lines of Swift)

| Folder | Lines | What it holds |
| --- | --- | --- |
| `ora/Shared` | 5,166 | Buttons, dialogs, toasts, icons, SplitView, page view, emoji picker |
| `ora/Core` | 4,043 | Browser engine wrapper, settings store, shortcuts, theme, services (favicons, updates, appearance) |
| `ora/Features/Tabs` | 2,593 | Tab and space models, `TabManager`, drag and drop, Ctrl+Tab switcher |
| `ora/Features/Settings` | 1,966 | Settings window sections |
| `ora/Features/Browser` | 1,884 | Browser view, URL bar, overlays |
| `ora/Features/Passwords` | 1,844 | Keychain vault, autofill popup, passwords window |
| `ora/Features/Privacy` | 1,728 | Ad blocking, fingerprinting script, rule lists |
| `ora/Features/Sidebar` | 1,425 | Sidebar, space switcher, floating sidebar |
| `ora/Features/Downloads` | 1,278 | Download manager and views |
| `ora/Features/Launcher` | 1,096 | Command bar |
| Others | about 2,600 | App, find, player, importer, search, history |

## Data and storage

| What | Where | Format |
| --- | --- | --- |
| Spaces, tabs, folders (unused), history, downloads | `Application Support/Ora/OraData.sqlite` (FACT, `ModelConfiguration+Shared.swift:10-14`). Under the sandbox that is `~/Library/Containers/com.orabrowser.app/Data/Library/Application Support/Ora/` (INFERENCE). The wiki gives a different, outdated path (FACT, [wiki: Data Persistence](https://github.com/the-ora/browser/wiki/Data-Persistence)) | SwiftData over SQLite (with `-wal` and `-shm` files). One database and one schema: `TabContainer`, `History`, `Download`, with `Tab` and `Folder` hanging off them |
| History | Same database | **One row per URL per space**, with a visit count and last-visit time. There is no list of individual visits (FACT, `History.swift`). Search loads all of a space's history on the main thread on every keystroke and filters it in memory (FACT, `HistoryManager.swift:61-82`) |
| Cookies, local storage, cache | One WebKit data store per space, named by the space's UUID (FACT, `BrowserEngineProfile.swift:15`). On disk it lives somewhere under the container's `Library/WebKit/` (INFERENCE) | WebKit's own formats |
| Settings | `UserDefaults` (`com.orabrowser.app.plist`). Per-space keys look like `settings.container.<uuid>.privacy` (FACT, `SettingsStore.swift:145-182`). UI flags use `@AppStorage` (FACT, `SidebarManager.swift:10-11`) | plist, with JSON-encoded structs inside |
| Passwords | macOS keychain, generic-password items under the service `com.orabrowser.app.passwords`, with `kSecAttrSynchronizable = true` (iCloud Keychain) and `AfterFirstUnlock` (FACT, `PasswordManagerService.swift:76,260-272`). Metadata (host, username, space ID) is JSON in `kSecAttrGeneric`. Opening the saved-passwords list requires Touch ID or the login password (FACT, `PasswordManagerService.swift:387-400`, `PasswordsWindow.swift:423`). These are Ora's own items, not the Apple Passwords app's website logins (INFERENCE, the item class and service name) | Keychain |
| Favicons | `~/Library/Caches/Favicons/<tab-uuid>.png`, inside the container (FACT, `Tab.swift:385-393`) | PNG |
| Ad-block artifacts | `Application Support/Ora/ContentBlockers/{raw,compiled}/<list>/<revision>/shard-N.json` plus `manifest.json`, compiled into `WKContentRuleListStore.default()` (FACT, `ContentBlockerArtifactStore.swift:10-160`) | JSON |

- **Encryption:** only what macOS provides (FileVault and the keychain). The
  SQLite file is not encrypted (FACT, no encryption code).
- **Failure handling:** if the database cannot open, Ora tries to delete
  `Application Support/OraData.sqlite`, then calls `fatalError` (FACT,
  `OraRoot.swift:40-46`, `OraApp.swift:49-57`). That path misses the real
  file (`Ora/OraData.sqlite`), and the `-shm` and `-wal` names are built
  wrong (`OraRoot.swift:44`, `OraApp.swift:49-57`). So in practice nothing
  is deleted, and a failed schema migration would probably crash Ora on
  every launch (INFERENCE).
- **Sync and server:** there is no server and no account (FACT). Only
  passwords are marked to sync, through iCloud Keychain (FACT for the flag;
  whether they really sync is unverified).
- **Telemetry:** none in the app. No analytics package. The only hosts in
  the code are search engines, AdGuard lists, and the update feed (FACT, a
  grep of the hosts in `ora/`). The website used Vercel Analytics, Vercel
  Speed Insights, Databuddy analytics, an Upstash Redis email waitlist, and
  Resend email (FACT, `ora-www/src/app/layout.tsx:5-7,143-145`,
  `src/actions/waitlist.ts`).
- **What leaves the machine besides normal browsing:**
  - What you type in the launcher goes to `suggestqueries.google.com`
    (with `client=firefox`) each time typing pauses for 0.2 s, when Google
    is the default engine,
    which it is out of the box (FACT, `SearchEngineService.swift:240,297-316`,
    `LauncherViewModel.swift:13,244-286`).
  - FaviconFinder fetches each site's homepage through `URLSession.shared`,
    outside the space's cookie jar, private windows included (FACT,
    `FaviconService.swift:136-147`, `Tab.swift:111-134`; the
    `URLSession.shared` calls are inside FaviconFinder 5.1.5,
    `Sources/FaviconFinder/Toolbox/FaviconURLSession.swift:227,270,297`;
    reaching private tabs is INFERENCE). It runs on every URL or title
    message from the page (FACT, `TabBrowserPageDelegate.swift:240`).
  - AdGuard list downloads from `filters.adtidy.org`, only when ad blocking
    is on (FACT).
  - A Sparkle check of `the-ora.github.io/browser/appcast.xml`. Sparkle's
    automatic checks are on in `Info.plist` (`SUEnableAutomaticChecks: YES`),
    even though the in-app "Auto-check for updates" toggle defaults to off
    (FACT, `project.yml`, `SettingsStore.swift:268`). The toggle probably
    does not stop Sparkle's own daily schedule (INFERENCE).

## Agents and AI

Ora ships no assistant, no agent, no model integration, no local models, no
MCP, no CLI, no skills, and no automations (FACT, the code; PR #136 closed
as not planned). The only AI feature is handing launcher text to an AI
website through a `?q=` URL (FACT, `SearchEngineService.swift:74-196`). PR
#136 was closed with only "not planned for now" (FACT). The team gave no
reason for leaving out AI. Simplicity is a guess from a comment on tree tabs,
where `yonaries` wrote "it introduces complexity than being simple which what
we are intended for Ora" (FACT, issue #135, 2025-10-29; applying it to AI is
INFERENCE).

Lessons for rac's agent from Ora's page bridge, even without AI:

- Ora trusts messages from page scripts for the tab URL and title (see
  Architecture). rac's agent snapshot, link-hover summaries, and Cmd+F Ask
  read page content through scripts too. Any value the browser *acts* on,
  such as origin, URL, or what is safe to fill, must come from the engine,
  never from text the page can write (INFERENCE).
- Ora's extension prototype grants `<all_urls>` to every extension silently.
  That is the same "no consent" pattern rac's maintainer rejected for the
  agent (FACT, PR #137; maintainer brief).

## Build, release, and engineering

- **Build system:** XcodeGen (`project.yml`) generates `Ora.xcodeproj`.
  `xcodebuild` builds it. `scripts/setup.sh` installs the tools. Lefthook
  runs `swiftformat` and `swiftlint` before each commit and a debug build
  before each push (FACT, `lefthook.yml`, `CONTRIBUTING.md`).
- **CI:** one GitHub Actions job, "Lint and Formatting", on `macos-latest`.
  It runs SwiftLint, `swiftformat --lint`, and package resolution. **It never
  builds or tests** (FACT, `.github/workflows/build-and-test.yml`). The
  latest `main` run, on 2026-09-17, failed; 13 of the last 89 lint runs
  failed (FACT, `gh api repos/the-ora/browser/actions/runs`). A second
  workflow bumps the Homebrew cask in `the-ora/homebrew-ora` when a `v*` tag
  is pushed (FACT, `.github/workflows/brew-release.yml`). It pushes with a
  classic personal access token with full `repo` scope (FACT,
  `brew-release.yml:3-6`). The cask is at 0.2.14 (FACT,
  `the-ora/homebrew-ora/Casks/ora.rb`).
- **Engine in CI:** not needed. The system's WebKit is used. The DMG is
  9.7 MB (FACT, `appcast.xml` enclosure length 9,668,821).
- **Signing and notarization, all local:** `scripts/release.sh` bumps the
  version, then `build.sh` runs `xcodebuild archive`, exports with Developer
  ID and manual signing (team `3Y566D2A4G`, provisioning profile
  `ora-profile-working`), verifies with `codesign --verify --deep --strict`,
  builds the DMG with `create-dmg`, signs it, runs `notarytool submit --wait`
  with a keychain profile, and staples **both** the DMG and the app (FACT,
  `scripts/build.sh`). The secrets live in a local `.env` (FACT,
  `.env.example`, `SECURITY.md`).
- **Update mechanism:** Sparkle 2 with an EdDSA key (public key in
  `Info.plist` and `ora_public_key.pem`). `publish.sh` pipes the private key
  from `.env` into `generate_appcast --ed-key-file -`, uploads the DMG to a
  GitHub Release, commits `appcast.xml`, and pushes it to the `gh-pages`
  branch, which serves the feed URL (FACT, `scripts/publish.sh`). The feed
  sits on `github.io` and still answered HTTP 200 on 2026-10-25, after
  `orabrowser.com` expired (FACT, `curl -I`).
- **Release notes:** `generate-changelog.py` collects the merged PRs between
  tags and has the Codex CLI rewrite them under a JSON schema. The prompt
  says "Write for normal users", "Do not invent features", and lists
  low-signal work to ignore (type fixes, lint, CI, refactors). A `--no-llm`
  fallback produces plain notes (FACT, `scripts/prompts/changelog_prompt.txt`,
  `scripts/generate-changelog.py:172-227`).
- **Tests:** 28 Swift Testing tests covering password matching, per-space
  privacy settings, ad-block catalog and refresh, fingerprint profile
  consistency, and page host view reparenting. The UI test target is the
  Xcode template (FACT, `oraTests/`, `oraUITests/`). CI does not run them
  (FACT).
- **Tracking upstream:** there is nothing to merge, because WebKit updates
  arrive with macOS and Safari. The cost is a frozen Safari 26.0.1 UA string
  that will age (FACT, `BrowserEngine.swift:21`), and engine features that
  depend on the user's macOS version (INFERENCE).
- **Process:** PRs must say whether AI was used (FACT, `CONTRIBUTING.md`).
  Bots (Tembo, Greptile) open or review PRs (FACT, PRs #223, #251). Issues
  are triaged in Linear. `linear[bot]` closed 8 issues as "not planned"
  on 2026-09-14, including #99, #135, #153, and #203 (FACT, issues API).
  Linear's sync closes a GitHub issue when someone cancels it in Linear, so
  a person probably made these calls (INFERENCE). Community PRs for tree
  tabs, split view, AI chat, and history were all closed on 2026-03-07
  (FACT).

## Strengths and weaknesses (critical)

### Strengths

1. **Small and fast to change.** About 22,000 lines of real app code and a
   9.7 MB download. 58 releases in 7 months (FACT). One person can understand
   it all, which rac's 871 hunks across 217 upstream files cannot match
   (INFERENCE).
2. **Per-space logins.** Each space has its own cookie jar, and deleting a
   space deletes its website data, passwords, and history (FACT,
   `TabManager.swift:182-212`). Arc users who split work and personal
   accounts get that without managing profiles.
3. **A thoughtful ad-block pipeline.** It converts standard AdGuard lists,
   splits them until WebKit accepts them, caches by content hash, keeps the
   last working version, and has tests (FACT).
4. **Polished micro-interactions with consistent springs**, and one-shot
   effects instead of loops (FACT, Motion table). One exception: the
   shortcut recorder's border pulses forever while shown,
   `easeOut(1.4).repeatForever` (FACT, `ShortcutsSettingsView.swift:131-145`).
5. **A release chain that works without CI.** Signing, notarization, an
   EdDSA appcast on GitHub Pages, and a Homebrew cask (FACT).
6. **No telemetry and no server** (FACT).

### Weaknesses

1. **Security basics are missing.** Sites get the camera and microphone
   with no per-site prompt (FACT). The address bar can probably be spoofed through
   the page-world `listener` handler (INFERENCE). JavaScript dialogs block
   the whole app (FACT). External URL schemes do nothing (FACT, PR #251).
2. **Privacy defaults are inconsistent.** Ad and tracker blocking are off,
   but fingerprint spoofing is on (FACT), and a contributor reports it
   breaks Google sign-in (CLAIM, PR #252). Typed text goes to Google
   Suggest by default (FACT).
3. **Steady background cost.** Every page polls every 500 ms and runs a
   whole-document mutation observer. The toolbar color is snapshotted every
   0.25 s while loading. A 60 s timer walks every tab (FACT). That breaks
   rac's "a feature that's off does no work" rule.
4. **Thin data model.** History keeps one row per URL. Closed tabs vanish
   after 5. Folders exist only as a model. Main-thread SwiftData saves happen
   on almost every action (FACT). A migration failure probably crash-loops
   (INFERENCE).
5. **WebKit's extension gap.** Extensions stalled. Maintainer `kenenisa`
   said many APIs are "not available out of the box" in macOS's WebKit
   (FACT, PR #137 thread, 2026-01-24). That 1Password needs exactly those
   APIs is INFERENCE from one user's error report. This is likely the main
   reason Arc users who depend on extensions cannot move to Ora (INFERENCE).
6. **Maturity and bus factor.** Two core authors, lint-only CI, a releaser's
   laptop as the only release machine, 6.5 months without a release, an
   expired domain, and a website that still shows the old MIT license and
   advertises Split View, which does not exist (FACT).
7. **Arc import probably does not work** in the sandboxed build, and when it
   runs it loads every tab at once (INFERENCE, FACT).
8. **No reduced-motion support** (FACT).

## What rac should take (ranked, concrete, with rough cost) and what rac should avoid

Cost scale in agent working days: XS under 1, S 1 to 3, M 4 to 10, L over 10.

### Take

1. **Keep the update feed on a host that cannot expire, and add a Homebrew
   cask.** `orabrowser.com` lapsed on 2026-09-05, but Sparkle updates kept
   working because the feed lives on `github.io` (FACT, INFERENCE). rac's
   feed already points at GitHub Releases (FACT,
   `patches/rac/updates/update-feed.patch:138`). Keep it there. Copy
   `brew-release.yml` (tag push, compute SHA-256, edit `Casks/*.rb`, push to
   a tap repo). Cost: XS. Needs a tap repo and a token. Ora uses a classic
   token with full `repo` scope (FACT, `brew-release.yml:3-6`). A
   fine-grained token limited to the tap is safer (INFERENCE).
2. **Treat Ora's local release scripts as proof for the "build and sign
   0.1.0 locally" fallback** already listed in `plans/context/ci-status.md`.
   Use the same order: `notarytool submit --wait` with a keychain profile,
   check the status in the result plist and fetch the log on failure, staple
   both the DMG and the `.app`, and pipe the EdDSA key into
   `generate_appcast --ed-key-file -` so no key file is written. Do not copy
   where Ora keeps that key: in plain text in a local `.env` (FACT,
   `.env.example`, `scripts/publish.sh:69-70`). Ora shipped
   58 releases this way (FACT). Cost: S for the scripts. The local full
   build needs the maintainer's approval (AGENTS.md).
3. **Release notes generated from merged PRs, with rules and a fallback.**
   Reuse the prompt's rules ("Write for normal users", "Do not invent
   features", ignore lint, CI, and refactors) and its JSON output schema.
   Run it with any installed agent, and keep `--no-llm` deterministic notes.
   Cost: XS to S.
4. **A colored Tab-to-search chip with a single border sweep** in rac's
   command bar and address bar. Chromium's omnibox already has keyword mode
   on Tab (FACT, `AcceptKeyword` in
   `chrome/browser/ui/omnibox/omnibox_edit_model.h:345` of rac's tree), and
   rac plans "Bangs" (FACT, `plans/context/roadmap-revision-2026-10-22.md:50`). Take the
   brand-color capsule and the one-shot sweep: linear 0.8 s rotation, 2 pt
   stroke plus an 8 pt glow at blur 40, then a 0.3 s fade. Under reduced
   motion, show the chip with no sweep. Cost: S to M.
5. **AI websites as plain search destinations** (`claude.ai?q=`,
   `chatgpt.com?q=`, `perplexity.ai/search?q=`, `t3.chat/new?q=`, as in
   Ora's code). They cost nothing when unused and work with AI off, which
   suits "AI off costs nothing" (INFERENCE). These URL forms are not
   documented APIs, so they can break without notice (INFERENCE). Do **not** show them by default in an empty command
   bar the way Ora does. Offer them as bangs. Cost: XS.
6. **Copy URL with a rolling label** for Cmd+Shift+C in rac's sidebar
   address bar. The label rolls ±12 pt with `easeOut(0.3)`, says "Copied"
   for 1.0 s, then rolls back. Cost: S.
7. **Per-site "Clear cookies and reload" and "Clear cache and reload"** in
   the menu bar and the site control center, with a short confirmation.
   Chromium's `BrowsingDataRemover` can filter by origin (FACT,
   `BrowsingDataFilterBuilder::AddOrigin` in
   `content/public/browser/browsing_data_filter_builder.h:82`). Cost: S.
8. **A Ctrl+Tab switcher of recent tabs with thumbnails.** Up to 5 cards at
   200x125. Releasing Ctrl commits. The mouse is ignored until it moves.
   Chromium's tab thumbnail code can feed it (INFERENCE). Cost: M.
9. **Arc import: start from Ora's map of `StorableSidebar.json`, and fix
   what it misses.** Fields: `sidebar.containers[].spaces[]`
   (`customInfo.iconType.emoji_v2`, `title`, `id`, `containerIDs`),
   `items[]` (`data.tab.savedURL`, `savedTitle`, `parentID`, `childrenIds`,
   `data.itemContainer`), and `topAppsContainerIDs` for favorites (FACT,
   `Importer.swift:6-147`). Fixes: get file access the user grants, keep
   folders through `childrenIds`, add favorites once (they are profile-wide
   in rac), create tabs unloaded, and report counts. Cost: M to L.
10. **Downloads as a page beside the spaces (optional).** It reuses rac's
    sliding space pages. Ora's numbers: 25% width threshold, commit
    `spring(0.45, 0.88)`, cancel `spring(0.35, 0.9)`, back layer at scale
    0.94, 12% offset, 50% opacity. Cost: M.
11. **Spring and toast numbers as reference values** next to Ardia's Dia
    spec: dialogs `spring(0.3, 0.82)` with y −16 and scale 0.96, toasts in
    at bounce 0.2 and out at bounce 0.15, hovers `easeOut(0.15)`. Cost: none.
    Use them as data.
12. **Per-space logins, as an option to research, not a decision.** Ora
    gives each space its own cookie jar. rac's spaces share one profile
    (FACT, `docs/internals/glossary.md`). One option is Arc's model, where a
    space can be tied to a profile. In Chromium a profile is heavy: separate
    history, extensions, and processes (INFERENCE). Cost: L. The maintainer
    should choose.

### Avoid

1. **Trusting page scripts for anything the browser acts on.** Ora sets the
   address bar from a page-world message (`TabBrowserPageDelegate.swift:229-241`).
   rac's agent and AI page scripts should run in isolated worlds, and should
   take origin and URL from the engine only.
2. **Granting permissions without a prompt** (`TabBrowserPageDelegate.swift:129-136`),
   or extension permissions without consent (PR #137).
3. **Polling and snapshot loops** (`OraBrowserScripts.swift:88,209`,
   `Tab.swift:168-177`, `TabManager.swift:543`). For toolbar tint, use
   Chromium's `theme-color` and observer events instead.
4. **JavaScript fingerprint spoofing that breaks sign-in** (PR #252). Keep
   relying on the engine-level protections from ungoogled-chromium and
   Helium.
5. **Changing the page's DOM for browser chrome:** find-in-page through
   mark.js, and the hover "shield" `div` (`BrowserView.swift:38-63`).
   Chromium's find bar and views overlays avoid both.
6. **App-modal page dialogs** (`NSAlert.runModal`). **One updater per
   window** (`OraRoot.swift:17`). **Trying to delete the database when it
   fails to open, then crashing** (`OraRoot.swift:43-45`).
7. **Showing AI by default.** Ora lists four AI rows in every empty
   launcher. That would break rac's "AI is off by default" (VISION).
8. **Letting public claims drift.** Ora's site says MIT and advertises Split
   View. Its domain expired. rac's site (`site/`, racbrowser.com) should
   state the GPL-3.0 license and only shipped features, and the domain
   should renew automatically.
9. **Lint-only CI and mass "not planned" closures with no comment.** Both
   appear in Ora. rac already has the first gap: CI never compiles its tests.
10. **Moving rac to WebKit.** Ora's extension support stalled on missing
    WebKit APIs (FACT, PR #137). That this is what holds Ora back is
    INFERENCE. Staying on Chromium is rac's biggest edge
    over Ora (INFERENCE).

## Open questions and things you could not verify

- **No hands-on run.** I could not build or launch Ora (cloned code is
  untrusted). All feel and visual claims come from code. I saw no
  screenshots, because the README has none and the website is offline.
- **Address-bar spoofing** through the `listener` handler is reasoned from
  code and untested. A WebKit change or a check I missed could block it.
- **Arc import under the sandbox:** I did not confirm that `~` resolves into
  the container. Issue #99 (an import crash) was closed without a fix.
- **Performance:** I found no independent numbers for memory, energy, or
  speed. A Speedometer listing at
  [browserating.com](https://www.browserating.com/browsers/ora) (45.63)
  describes "integrated AI tools", so it may be a different "Ora".
- **iCloud Keychain behavior:** whether synced items need extra
  entitlements in practice, and whether they show up in the Apple Passwords
  app.
- **Camera and microphone in v0.2.14:** whether they hang, as PR #250
  reports. I could not run the app to check.
- **Project health:** whether Ora is paused or abandoned. Signals: an
  expired domain, no release since April, one commit since then, and open
  community PRs with no reply. The Discord is unchecked.
- **Team:** only two core authors are visible. I did not verify funding or
  employment.
- **The stargazer timeline** API returned 404, so star growth over time is
  unknown.
- **Space-switch duration:** the real number depends on AppKit's default
  animator duration, inferred as about 0.25 s.

## Sources

Code (clone of `the-ora/browser` at `4e6cfd1`, 2026-09-17; paths relative to `/tmp/rac-overhaul/src/ora/`):

- `README.md`, `ROADMAP.md`, `CONTRIBUTING.md`, `SECURITY.md`, `THIRD_PARTY_NOTICES.md`, `project.yml`, `appcast.xml`, `lefthook.yml`, `.env.example`
- `ora/App/OraApp.swift`, `ora/App/OraRoot.swift`, `ora/App/OraCommands.swift`
- `ora/Core/BrowserEngine/{BrowserEngine,BrowserEngineProfile,BrowserEngineTypes,BrowserPage,BrowserPageView}.swift`, `ora/Core/BrowserEngine/Scripts/OraBrowserScripts.swift`
- `ora/Core/Utilities/SettingsStore.swift`, `ora/Core/Constants/{Theme,KeyboardShortcuts}.swift`, `ora/Core/Services/App/UpdateService.swift`, `ora/Core/Services/Web/FaviconService.swift`, `ora/Core/Extensions/ModelConfiguration+Shared.swift`, `ora/Core/Platform/Representables/GlobalMouseTrackingArea.swift`
- `ora/Features/Tabs/Models/{Tab,TabContainer,Folder}.swift`, `ora/Features/Tabs/State/TabManager.swift`, `ora/Features/Tabs/Browser/TabBrowserPageDelegate.swift`, `ora/Features/Tabs/Switcher/FloatingTabSwitcher.swift`, `ora/Features/Tabs/Views/TabItem.swift`
- `ora/Features/Sidebar/{State/SidebarManager,Views/SidebarView,Views/BottomOption/ContainerSwitcher,Views/TabList/*}.swift`, `ora/Features/Browser/{Views/BrowserView,Views/BrowserSplitView,Views/BrowserWebContentView,Views/FloatingSidebarOverlay,URLBar/URLBar,Components/CopiedURLOverlay,Components/LinkPreview}.swift`
- `ora/Features/Launcher/{LauncherView,Main/LauncherMain,Main/SearchCapsule,State/LauncherViewModel}.swift`, `ora/Features/Search/Services/SearchEngineService.swift`
- `ora/Features/Privacy/{Models/*,Services/*}.swift`, `ora/Features/Passwords/Services/*.swift`, `ora/Resources/WebScripts/password-manager.js`, `ora/Features/FindInPage/FindController.swift`
- `ora/Features/Importer/{Services/Importer,Views/ImportDataButton}.swift`, `ora/Features/History/{Models/History,Services/HistoryManager}.swift`
- `ora/Shared/{Layout/NSPageView,Modifiers/GradientAnimatingBorder,Shapes/ConditionallyConcentricRectangle,Components/Toast/*,Components/Dialog/*}.swift`
- `ora/Info/ora.entitlements`, `oraTests/*.swift`
- `scripts/{_common,build,publish,release}.sh`, `scripts/generate-changelog.py`, `scripts/prompts/changelog_prompt.txt`, `.github/workflows/{build-and-test,brew-release}.yml`
- Branch `feat/extensions`: `ora/Services/Extentions/ExtensionManager.swift` (via `gh api`)

Website source (clone of `the-ora/www` at `ff9e694`, 2026-01-10; `/tmp/rac-overhaul/src/ora-www/`): `public/llms.txt`, `src/components/features.tsx`, `src/lib/seo.ts`, `src/app/layout.tsx`, `src/actions/waitlist.ts`, `src/app/api/ip/route.ts`.

GitHub API (read-only, 2026-10-25):

- Repo metadata: `repos/the-ora/browser`
- Releases (58, download counts): `repos/the-ora/browser/releases`
- Contributors: `repos/the-ora/browser/contributors`
- Org repos: `orgs/the-ora/repos`. Cask: `repos/the-ora/homebrew-ora/contents/Casks/ora.rb`
- Issues and PRs: [#99](https://github.com/the-ora/browser/issues/99), [#135](https://github.com/the-ora/browser/issues/135), [#136](https://github.com/the-ora/browser/pull/136), [#137](https://github.com/the-ora/browser/pull/137), [#151](https://github.com/the-ora/browser/issues/151), [#152](https://github.com/the-ora/browser/pull/152), [#153](https://github.com/the-ora/browser/issues/153), [#165](https://github.com/the-ora/browser/issues/165), [#167](https://github.com/the-ora/browser/issues/167), [#169](https://github.com/the-ora/browser/issues/169), [#172](https://github.com/the-ora/browser/issues/172), [#173](https://github.com/the-ora/browser/issues/173), [#174](https://github.com/the-ora/browser/issues/174), [#179](https://github.com/the-ora/browser/issues/179), [#182](https://github.com/the-ora/browser/issues/182), [#185](https://github.com/the-ora/browser/issues/185), [#187](https://github.com/the-ora/browser/issues/187), [#203](https://github.com/the-ora/browser/issues/203), [#208](https://github.com/the-ora/browser/issues/208), [#223](https://github.com/the-ora/browser/pull/223), [#237](https://github.com/the-ora/browser/pull/237), [#245](https://github.com/the-ora/browser/issues/245), [#247](https://github.com/the-ora/browser/issues/247), [#251](https://github.com/the-ora/browser/pull/251), [#252](https://github.com/the-ora/browser/pull/252)

Web:

- [GitHub: the-ora/browser](https://github.com/the-ora/browser) and [wiki](https://github.com/the-ora/browser/wiki), [wiki: Data Persistence](https://github.com/the-ora/browser/wiki/Data-Persistence)
- [Vercel Community post by Yonathan, 2025-12-08](https://community.vercel.com/t/ora-browser-the-open-source-arc-alternative-for-macos/29424)
- [Hysen Labs project review, 2026-10-07](https://hysenlabs.com/projects/the-ora-browser)
- [BrowseRating listing (may be a different "Ora")](https://www.browserating.com/browsers/ora)
- [BrightCoding blog post (unreliable comparison table)](https://converter.brightcoding.dev/blog/ora-browser-the-sleek-macos-browser-every-developer-needs)
- `whois orabrowser.com` (2026-10-25): Registry Expiry Date 2026-09-05, status `redemptionPeriod`. `dig orabrowser.com`: no records.

rac files cited: `plans/context/maintainer-brief.md`, `plans/context/ci-status.md`, `plans/context/roadmap-revision-2026-10-22.md`, `docs/internals/glossary.md`, `patches/rac/updates/update-feed.patch:138`.

## Verification

Adversarial fact-check on 2026-10-25 against the clone at `4e6cfd1`, the
`ora-www` clone at `ff9e694`, `gh api` (read-only), `whois`, `dig`, `curl -I`,
the Vercel community post, FaviconFinder's source at tag 5.1.5, and rac's
Chromium tree (read-only). Nothing was built or run.

| # | Claim checked | Result | Change made |
| --- | --- | --- | --- |
| 1 | 2,241 stars, 98 forks, 11 watchers, 25 open issues and PRs; repo created 2025-08-09; org 2025-07-03 | Confirmed (`repos/the-ora/browser`, `orgs/the-ora`). 25 = 19 issues + 6 PRs | None |
| 2 | 451 commits; `yonaries` 223, `kenenisa` 178, 89%; 21 others | Confirmed (contributors API: 23 contributors, sum 451; commits API last page 451) | None |
| 3 | 58 releases, 18,524 DMG downloads, v0.2.14 has 4,390, first build v0.0.18 on 2025-09-04, none since 2026-04-07 | Confirmed (releases API) | None |
| 4 | "About 40 tags on 2025-09-05/06, then a release every 1 to 3 weeks until 2025-12-11" | Partly wrong. 39 releases on those two days; then 13 releases 2025-09-08 to 2025-10-29, often days apart; then a 6-week gap | Rewrote the cadence row |
| 5 | License GPL-3.0 since 2026-03-12, GPL-2.0 before | Incomplete. Ora was MIT until commit `fe66211` (2025-10-03), then GPL-2.0, then GPL-3.0 (PR #223, merged 2026-03-12) | Fixed the License row; the website's "MIT" is stale, not invented |
| 6 | Tagline "Less noise, more browsing." is in `README.md` | Wrong source. It is in `HomeView.swift:41` and the website; the README says "Fast, native WebKit browser for macOS." | Fixed citation |
| 7 | "Windows is not possible (FACT, issue #247 comments)" | Comments are from users, not maintainers | Re-tagged as INFERENCE from the code |
| 8 | macOS 15 target, Swift 5.9, sandboxed, package versions | Confirmed (`project.yml:5-17,23,99,118`) | None |
| 9 | One `WKWebsiteDataStore(forIdentifier:)` per space; a new non-persistent store per private tab | Confirmed (`BrowserEngineProfile.swift:12-16`, `BrowserEngine.swift`, `Tab.swift:213-214`) | None |
| 10 | Camera and mic granted with no prompt | Confirmed per site (`TabBrowserPageDelegate.swift:135`, `BrowserPage.swift:398-408`). But v0.2.14 has no usage strings, so a contributor says capture hangs (PR #250, CLAIM). `main` added them on 2026-09-17, unreleased | Added the release nuance to the plain-English section, the Site permissions row, and Weakness 1 |
| 11 | `listener` handler sets `tab.url` from page `href`; handlers and scripts are in the page world | Confirmed (`TabBrowserPageDelegate.swift:229-241`; `BrowserPage.swift:58-67` uses `add(_:name:)` and `WKUserScript` with no content world). Polling posts only on change, so a forged value would persist until the real URL or title changes | Spoofing kept as INFERENCE (untested) |
| 12 | 500 ms `setInterval` and whole-document `MutationObserver` | Confirmed (`OraBrowserScripts.swift:88,209-210`); main frame only | None |
| 13 | Tab suspend 1 h default; auto-close 24 h; 60 s timer; 5 reopenable tabs | Confirmed (`SettingsStore.swift:294-319`, `TabManager.swift:62,542-549`) | None |
| 14 | Ad block and trackers off, fingerprinting on by default; 25 tracker domains | Confirmed (`SpacePrivacySettings.swift:9-14`, `BrowserPrivacyService.swift:598-624`) | None |
| 15 | Fingerprinting breaks Google sign-in (FACT, PR #252) | The `webdriver` override is FACT (`BrowserPrivacyService.swift:247`). The breakage is a contributor's report in an open PR | Re-tagged as CLAIM |
| 16 | UA sent twice via `applicationNameForUserAgent` | Confirmed (`BrowserEngine.swift:21`, `BrowserPage.swift:24`; PR #252 body) | None |
| 17 | Motion: sidebar `spring(0.2, 1.0)`, downloads swipe numbers, launcher, border sweep, toasts, copy URL, Ctrl+Tab, hovers | Confirmed line by line. Dialogs use `spring(0.3, 0.8)` in `DialogManager` and `spring(0.3, 0.82)` on the overlay. Toasts also have a `spring(0.3, bounce: 0.3)` snap-back | Added both details |
| 18 | No reduced-motion support; "one-shot effects instead of loops" | No reduced-motion reads (grep). One infinite loop exists: `PulsingBorderView` (`ShortcutsSettingsView.swift:131-145`) | Added the exception to Strength 4 |
| 19 | Space-switch `easeOut(0.1)` "handed to" `NSPageController` | Misleading. The SwiftUI animation does not reach AppKit; `NSAnimationContext` runs with its default duration (`NSPageView.swift:154-163`) | Reworded; duration stays INFERENCE |
| 20 | `Folder` model has no references | Slightly wrong. `TabContainer.folders` exists and space deletion iterates it; nothing creates folders | Fixed the Folders row |
| 21 | Storage: `Ora/OraData.sqlite`, one row per URL per space, main-thread history search | Confirmed (`ModelConfiguration+Shared.swift:10-14`, `HistoryManager.swift:17-50,58-80`, `@MainActor`) | None |
| 22 | Failed open deletes the wrong path and builds wrong `-shm`/`-wal` names | Confirmed (`OraApp.swift:49-57`: `appendingPathExtension("-shm")`). So nothing is actually deleted | Reworded the failure note and Avoid 6 |
| 23 | Each window builds its own state and updater | Confirmed, and stronger: each window builds a new `ModelContainer` and starts its own `SPUUpdater` (`OraRoot.swift:34-75`, `UpdateService.swift:19-41`) | Expanded |
| 24 | Passwords in keychain, synchronizable, `AfterFirstUnlock`, Touch ID for the list | Code confirmed (`PasswordManagerService.swift:76,262-267,388-400`). Real iCloud sync is unproven; no access group is set | Sync row re-tagged; open question kept |
| 25 | Google Suggest on "every keystroke" | Debounced 0.2 s (`LauncherViewModel.swift:13,247`); falls back to Google (`SearchEngineService.swift:240`) | Reworded |
| 26 | FaviconFinder uses `URLSession.shared` | Not in Ora's code; it is inside FaviconFinder 5.1.5 (`FaviconURLSession.swift:227,270,297`) | Added the library citation |
| 27 | Sparkle auto checks on in `Info.plist`, in-app toggle defaults off | Confirmed (`project.yml:66`, `SettingsStore.swift:268`, `OraRoot.swift:169`) | None |
| 28 | Updates survive the expired domain (INFERENCE) | Feed `the-ora.github.io/browser/appcast.xml` returned HTTP 200 on 2026-10-25 | Upgraded to FACT |
| 29 | `orabrowser.com` expired 2026-09-05, `redemptionPeriod`, no DNS | Confirmed (`whois`, `dig`) | None |
| 30 | DMG 9.7 MB, enclosure length 9,668,821 | Confirmed (`appcast.xml:29`, release asset size) | None |
| 31 | Local signing, notarization, double staple, appcast via piped key | Confirmed (`scripts/build.sh:40-60,115-145`, `scripts/publish.sh:69-70`). But the private key lives in plain text in `.env`, so "never touches disk" was wrong | Fixed Take 2 |
| 32 | CI is lint-only; brew workflow on `v*` tags | Confirmed. Also: latest `main` lint run failed (2026-09-17); the brew workflow uses a classic PAT with `repo` scope | Added both |
| 33 | 28 Swift Testing tests; UI tests are templates | Confirmed (28 `@Test`; 3 template `func test`) | None |
| 34 | Code size: 25,600 lines, 171 files, 1,956 icon lines, 1,501 SplitView lines, folder table | Confirmed exactly (`wc -l`) | None |
| 35 | PR #136 closed "not planned for now" by `yonaries` 2026-03-07; "stated reason is simplicity" | Close comment confirmed. The simplicity quote is about tree tabs (issue #135), not AI | Re-tagged the AI reason as INFERENCE |
| 36 | PR #137 grants `<all_urls>` and a fixed permission list; maintainer quote | Confirmed (`feat/extensions:ExtensionManager.swift:88-120`, comment 2026-01-24). 1Password error is a user report | Re-tagged; softened Weakness 5 and Avoid 10 |
| 37 | `linear[bot]` closed "many" issues on 2026-09-14 | 8 issues, all `not_planned` | Gave the count; added that Linear sync means a person likely decided (INFERENCE) |
| 38 | Website uses Vercel Analytics, Upstash, Resend; says MIT; advertises Split View | Confirmed, and it also loads Vercel Speed Insights and Databuddy (`layout.tsx:6-7,143-145`) | Added the two trackers |
| 39 | Vercel post: "co-creator", Fall '25 cohort, 2025-12-08 | Confirmed (WebFetch of the post) | Kept as CLAIM |
| 40 | rac side: feed on GitHub Releases at `update-feed.patch:138`; Chromium keyword mode; origin-filtered data removal | Confirmed (`patches/rac/updates/update-feed.patch:138`; `omnibox_edit_model.h:345`; `browsing_data_filter_builder.h:82`) | Upgraded Takes 4 and 7 from INFERENCE to FACT |

Not verified: the address-bar spoof works in practice; Arc import fails
under the sandbox (strong INFERENCE: tilde expansion resolves inside the
container and no file access is requested); real iCloud Keychain sync;
camera behavior in v0.2.14; the BrowseRating and Hysen Labs pages; Discord.

No fabrications found. The errors were stale or wrong sources, tag
overreach (user reports and contributor PRs labeled FACT), and two wrong
details that a plan could rely on: the license history and Ora's key
handling.

**Overall confidence: high** for counts, code facts, motion numbers,
storage, and release mechanics. **Medium** for the behavioral inferences
(spoofing, import, sync), which nobody has run.
