# Nook: research dossier

Researched 2026-10-25 from a shallow clone of `nook-browser/Nook` at `develop`
commit `242c7fb` (1.3.0, build 119, 2026-10-24), its branches, the
`nook-browser/www` site repo, the GitHub API, the live Sparkle feed, and public
discussion. Paths below are relative to the Nook repo root unless they start
with `/`. Tags: **FACT** (primary source: code, config, API, release data),
**CLAIM** (the project's own words, unmeasured by me), **INFERENCE** (my
reasoning).

## In plain English (at most 150 words)

Nook is a free, open-source Mac browser that copies Arc's sidebar. It is a
Swift app around Apple's own web engine, the one inside Safari. So the download
is small (18 MB), but sites built only for Chrome can misbehave. It has spaces,
favorites, pinned tabs, link previews, split view, a mini window for outside
links, and Arc import. Its ad blocker is strong but starts switched off. Its AI
chat can run on Apple's on-device model with no key or account. A hidden "Agent
space" lets coding agents like Claude Code drive the browser without changing
what you see. One person revived it in September 2026 and ships about twice a
week, often with AI help. It has almost no automated tests. For rac, the
useful parts are ideas, not code: the agent space, the "did the person name
it?" safety check, motion values, and tab data rules.

## Snapshot

| Field | Value |
| --- | --- |
| What it is | Arc-style, sidebar-first browser for macOS. A native SwiftUI/AppKit shell around the system `WKWebView`. (FACT, `README.md`, `CLAUDE.md:7`) |
| Engine | System WebKit, whatever version macOS ships. No fork, no patches; about 20 private selectors, mostly WebKit: 15 written as literals in `NSSelectorFromString`, plus about 5 built from strings at run time (for example `_resetNavigationGestureStateForTesting`). (FACT, grep of `NSSelectorFromString`; `Packages/NookWeb/Sources/NookWeb/PageSession+SwipeBack+macOS.swift:59-79`) |
| Platforms | macOS 15.5+, Apple Silicon only (both workflows build with `-arch arm64`). An iOS app target exists at version 0.1.0 and is unreleased. (FACT, `Nook.xcodeproj/project.pbxproj:419,589-635`; `.github/workflows/macos-notarize.yml:86`; `.github/workflows/macos-build.yml:33`) |
| License | GPL-3.0. The name, wordmark, and icon are trademarks of Bain Gurley; forks must rename. (FACT, `LICENSE`, `TRADEMARK.md`) |
| Repo | <https://github.com/nook-browser/Nook>, default branch `develop`, releases fast-forward `main`. (FACT, `CLAUDE.md:107-109`) |
| Stars | 1,980 stars, 84 forks, 21 open issues and PRs on 2026-10-25. (FACT, GitHub API) |
| Age | Repo created 2025-08-01. First release v1.0.1 on 2025-10-07. Near-dormant Dec 2025 to Aug 2026 (0 to 6 commits a month, apart from Feb–Mar 2026). Bain Gurley's fork `l984-451/Nook` carried on from March to September 2026. The original lead asked for a new maintainer on 2026-08-06 (#349); Gurley took over on 2026-09-17. (FACT, GitHub API; issue #349; `CLAUDE.md:9`) |
| Release cadence | 9 releases from 2026-09-18 to 2026-10-24, about two a week. The 1.0.x line had 7 releases from Oct 2025 to Mar 2026. (FACT, releases API) |
| Team size | One active maintainer. 465 commits on `develop` since 2026-09-01: 461 by Bain Gurley (GitHub login `l984-451`); about 190 disclose AI help in the message, mostly as "AI-assisted: implemented with Claude Code" or "Assisted by Claude Code" (188 start with "AI-assisted" or "Assisted by Claude Code"; 195 counting every phrasing). The 2025 core team of 7 is still listed on the site but inactive. 17 contributors all-time. (FACT, commits and contributors API; `nook-browser/www` `src/data/team.ts`) |
| Business model | None visible. Free, no accounts, no paid tier, no funding file. (FACT, absence in repo and site; CLAIM, browsewithnook.com "open-source and free to use") |
| Size | DMG 18.3 MB (1.3.0; 18,251,990 bytes). About 65,600 lines of first-party Swift (70,100 with vendored and iOS code), 1,500 lines of Rust FFI including its tests, 2,500 lines of first-party JS. (FACT, releases API; `wc -l`) Release binary 54.2 MB. (CLAIM, the project's own measurement, `CLAUDE.md:90-91`) |

## Features

Status key: **shipped** (in 1.3.0), **beta** (gated or labeled work in
progress), **planned** (issue, branch, or open PR only), **absent**.

### Tabs, sidebar, spaces

- **Three-part sidebar**: favorites grid (44 pt tiles), pinned section,
  regular tabs, split by a hairline separator with Clear and Organize buttons
  on hover. Shipped. (FACT, `Packages/NookDesign/Sources/NookDesign/NookDesign.swift:72`;
  `Packages/NookUI/Sources/NookUI/Rows/SpaceSeparator.swift`)
- **Favorites and pinned tabs keep a home URL.** Closing ends the page but keeps
  the item. A reset arrow appears on hover when the page has left home.
  Shipped. (FACT, `CLAUDE.md:254`)
- **Spaces**: each has an accent color and no icon. Switch with a row of dots,
  Ctrl+1–9, Cmd+Opt+arrows, or a two-finger trackpad swipe. Hovering a dot for
  0.7 s shows the space name. Shipped. (FACT, `CLAUDE.md:243`;
  `Packages/NookUI/Sources/NookUI/Spaces/SpacesList.swift:42-46`; `CHANGELOG.md` 1.3.0)
- **Profiles = spaces that share a website data store** (cookies, logins,
  history). Extensions, settings, and the blocker stay app-wide. Shipped in
  1.3.0. (FACT, `CLAUDE.md:360`)
- **Folders**, nesting up to depth 5. Shipped. (FACT, `CLAUDE.md:253`)
- **Trails**: a tab opened from a page becomes that tab's child. Back on a child
  with no history closes it and returns to the parent, like Safari and Zen.
  Shipped in 1.1.1. (FACT, `CLAUDE.md:255`)
- **Live folders**: a "Pull Requests" folder that fills itself with your open
  GitHub PRs, using your GitHub cookies and an undocumented endpoint. No timer;
  it refreshes on activation, at most once per 120 s. Shipped in 1.2.3.
  (FACT, `CLAUDE.md:256`)
- **Favorite hover cards**: resting 0.6 s on a github.com favorite lists the
  space's open PRs. GitHub only. Shipped. (FACT, `CLAUDE.md:364`)
- **Tab unloading**: Power Saving (5 min idle, max 8 loaded, unload on
  background), Standard (30 min), Performance (4 h). Memory pressure unloads 50%
  (Standard) or 25% (Performance); Power Saving keeps only 2 besides the current
  tab. Pages off screen for 5 min drop their
  back/forward cache. Shipped. (FACT,
  `Packages/NookSettings/Sources/NookSettings/NookSettingsService.swift:798-839`;
  `Nook/Components/Browser/Window/TabCompositorView.swift:48`)
- **Sidebar hide with edge reveal**, left or right side; optional address bar
  in a top bar. Shipped. (FACT, `Nook/Managers/HoverSidebarManager/HoverSidebarManager.swift`)
- **Sidebar picture-in-picture**: a playing video's live web view moves into the
  sidebar above the media bar, drags out into a floating panel, and docks back.
  Shipped; called "WIP" in 1.1.0. (FACT, `Nook/Components/Sidebar/MediaControls/SidebarPiPPanel.swift:1-9`)
- **On-device tab organizer**: groups loose tabs into folders, renames pinned
  tabs, closes duplicates. Needs macOS 26 and Apple Intelligence. Off by
  default. Shipped. (FACT, `CLAUDE.md:150`; `NookSettingsService.swift:483`)
- **Auto-archive of old tabs** (Arc's "Today" clean-up): absent. (FACT, no
  archive code found by grep)

### Navigation and command bar

- **Command palette**: typed URL or search, open tabs from every space, history,
  and web suggestions. The first row is always what Return does. Words match
  in any order. Shipped. (FACT, `CLAUDE.md:362`)
- **No commands in the palette.** Suggestion types are only search, url, tab,
  and history. (FACT, `Packages/NookWeb/Sources/NookWeb/SearchManager.swift:65-69`)
- **Site search chips** (Arc-style "tab to search") for 14 sites, including
  ChatGPT, Claude, Perplexity, YouTube, GitHub. Shipped. (FACT,
  `Packages/NookSettings/Sources/NookSettings/SiteSearch.swift`)
- **Full-text history search**: the text of each visited page (first 20,000
  characters) goes into a local SQLite FTS5 index. On by default. Shipped.
  (FACT, `Packages/NookWeb/Sources/NookWeb/PageSession+Navigation.swift:465-489`;
  `Packages/NookWeb/Sources/NookWeb/HistoryTextIndex.swift:1-6`;
  `NookSettingsService.swift:478`)
- **Redirect skipping** (uBO `urlskip=`) and tracking-parameter stripping.
  Shipped, active only with the blocker on. (FACT, `CLAUDE.md:319,321`)
- **Back, forward, reload beside the window buttons**; two-finger swipe back;
  Escape routed to the page, then Peek, never out of full screen. Shipped.
  (FACT, `CHANGELOG.md` 1.1.1; `CLAUDE.md:255,389`)
- **57 customizable shortcut actions**, with detection of conflicts with a
  site's own shortcuts. Shipped. (FACT, `Nook/Models/KeyboardShortcut/KeyboardShortcut.swift`)
- **`nook://` URL scheme for launchers**: requested, not built (#378).

### Split view, Peek, small windows

- **Split view**: two panes per window, saved with the window. Drag a tab over
  the page and "magnetic" drop cards pull toward the cursor. Shipped. (FACT,
  `CLAUDE.md:359`; `Nook/Components/WebsiteView/WebsiteView.swift:467-475`)
- **Peek** (a link preview card): opens on its own only for links from a
  favorite or pinned tab to another site, or on Option-click anywhere. The card
  is 80% of the web area wide and 90% of the window tall. Shipped. (FACT,
  `CLAUDE.md:157`; `Nook/Components/Peek/PeekOverlayView.swift:121-127`)
- **Mini window** for links from other apps and sign-in popups, with "Open in
  Space". Shipped. (FACT, `CLAUDE.md:168`)
- **Air Traffic Control**: route a domain or path prefix to a space; a rule
  covers subdomains; the longest match wins; sign-in URLs are never routed.
  Shipped. (FACT, `CLAUDE.md:144`)
- **Floating PiP player** with seek bar and Return to Tab. Shipped. (FACT,
  `CHANGELOG.md` 1.2.1, 1.2.3)

### Import, sync, profiles

- **Arc import**: spaces in order, nested folders, custom tab names, theme color
  as accent, each profile's favorites copied into each of its spaces, one Nook
  profile per Arc profile, extensions reinstalled from the Chrome Web Store, and
  Arc's member card kept as a keepsake. No passwords, cookies, or history.
  Shipped in 1.3.0. (FACT, `Nook/Managers/BrowserManager/BrowserManager+Import.swift:14-57`;
  `Nook/Managers/ImportManager/ImportManager.swift:15-50`)
- **Safari import** (bookmarks and history from a Safari export folder) and
  **Dia import** (favorites and window tabs). Shipped. (FACT, `Nook/Managers/ImportManager/`)
- **iCloud sync** of spaces, favorites, pinned tabs and folders through
  `CKSyncEngine`. Names, titles, and URLs go in CloudKit `encryptedValues`.
  Planned: branch `feature/icloud-sync` (last commit 2026-09-23), issue #382.
  (FACT, `git show origin/feature/icloud-sync:Packages/NookSync/Sources/NookSync/RecordMapper.swift:26-66`)
- **Private windows**: a non-persistent store, no extensions, no AI tools or
  page context, nothing written to disk. Shipped. (FACT, `CLAUDE.md:261`;
  `Nook/Managers/AIManager/AIService.swift:314-317`)

### Privacy and blocking

- **Built-in content blocker**: Brave's adblock-rust converts lists into WebKit
  content rule lists (30,000-entry chunks); uBlock Origin's scriptlet library is
  vendored; a cosmetic engine fills gaps; snapshots of every default list ship
  in the app. Shipped, but **off by default on macOS**
  (`adBlockerEnabledKey: false`; the iOS target turns it on). (FACT,
  `docs/adblocker-architecture.md`; `NookSettingsService.swift:459`;
  `NookiOS/BrowserModel.swift:73-74`)
- **Site tweaks**: hide YouTube Shorts and shelves, Facebook Reels and suggested
  posts, Meta feed ads removed from JSON before render, X t.co links rewritten,
  Reddit sorted by Hot, a media download button on listed sites, SponsorBlock
  (off by default). Shipped. (FACT, `CLAUDE.md:145-149,316-320`)
- **Blocked-page card** with Continue, drawn in SwiftUI so a page cannot press
  it. Shipped. (FACT, `CLAUDE.md:318`)
- **Pages ask before opening another app** unless the user clicked a link.
  Shipped in 1.2.3. (FACT, `CLAUDE.md:376`)
- **Passkeys**: only through password-manager extensions. Apple declined the
  browser passkey entitlement, so iCloud Keychain passkeys do not work. (FACT,
  `CLAUDE.md:17`)
- **Password manager**: none built in; relies on Bitwarden or 1Password
  extensions. Bitwarden biometric unlock works without its desktop app. (FACT,
  `Nook/Managers/ExtensionManager/CLAUDE.md` file table; INFERENCE for "none
  built in", from grep)
- **On-device page translation** through Apple's Translation framework, with an
  offer bar. Shipped. (FACT, `Nook/Components/WebsiteView/TranslateOfferView.swift`)
- **Privacy Cleanup menu**: clear third-party, high-risk, or expired cookies,
  per-site cache, and more. Shipped. (FACT, `App/NookCommands.swift`)

### AI assistant

- **"Ask Nook"** chat in a right-hand column. Reads the current page, streams
  answers, can search the web (OpenRouter `:online` or Gemini grounding), and
  calls tools. On by default (`showAIAssistantKey: true`): the menu item and
  toggle work, but the column starts closed and web search starts off. Shipped.
  (FACT, `NookSettingsService.swift:466,472`;
  `Packages/NookWeb/Sources/NookWeb/BrowserWindowState.swift:52`; `Nook/Managers/AIManager/Providers/OpenRouterProvider.swift:92-115`)
- **Providers**: Apple Intelligence on-device (default when nothing else
  works), Google Gemini, OpenRouter, Ollama, any OpenAI-compatible endpoint.
  API keys in the Keychain. Shipped. (FACT, `CLAUDE.md:286-287`;
  `Nook/Managers/AIManager/AIConfigService.swift:118-146`)
- **MCP client**: Nook can call outside MCP servers over stdio or SSE. Shipped.
  (FACT, `Nook/Managers/AIManager/MCP/MCPTransport.swift:22,195`)

### Agent

- **In-chat tool loop**: up to 20 tool rounds with 12 browser tools (navigate,
  read, click by selector or text, list elements, structured data, search in
  page, tabs, selection, run JavaScript). A rotating glow frames the page while
  tools run. Shipped. (FACT, `AIService.swift:45`;
  `Nook/Managers/AIManager/Tools/BrowserTools.swift:156-162`;
  `Nook/Components/Window/ToolExecutionGlowView.swift`)
- **No separate agent mode**, no plans, no step cards, no critic. (INFERENCE,
  from reading `AIService.swift` end to end)
- **Agent space for outside agents** (see Agents and AI). Shipped behind
  Developer Mode, off by default. (FACT, `CLAUDE.md:143,382`)

### Extensibility

- **Web extensions** through `WKWebExtension`: Chrome Web Store (an injected
  "Add to Nook" button), Firefox Add-ons, Safari `.appex`, `.zip`, `.crx`.
  Store installs update daily. Native messaging honors `allowed_origins`.
  Shipped. Limits: no `webRequestBlocking`, so a Firefox uBO build installs but
  cannot block. (FACT, `Nook/Managers/ExtensionManager/CLAUDE.md`)
- **DevMCP server**: Streamable HTTP MCP on `127.0.0.1:47823/mcp`, bearer token
  file, 31 tools. Off unless Developer Mode and Browser Control are on.
  Shipped. (FACT, `Nook/Managers/DevMCPServer/DevMCPServer.swift:24-29,227-356`)
- **Developer panel**: console, network, perf, blocker log, element picker
  (Cmd+Shift+X) with "Send to Agent", docked Web Inspector. Developer Mode
  only. Shipped. (FACT, `CLAUDE.md:297-303`)
- **CLI, AppleScript dictionary, URL scheme, mods, boosts**: absent. Boosts
  were still in the code when `ASSESSMENT.md` was written (dated 2026-03-20,
  §4 and §5); no Boost code remains now. (FACT, no `.sdef`; `Nook/Info.plist:12-16`
  registers only `http` and `https`; grep finds no Boost code)

### Other

- **PDF controls** drawn by Nook (zoom, print, save, open in Preview); one print
  path for Cmd+P, the menu, and `window.print()`. Shipped. (FACT, `CLAUDE.md:386-387`)
- **Downloads** with a "flight" animation from page to button; quit asks while
  downloads run. Shipped. (FACT, `NookDesign.swift:140`; `CLAUDE.md:376`)
- **Onboarding**: four stages ending in a Metal noise-reveal transition.
  Shipped. (FACT, `Onboarding/Components/ViewTransition.metal`)
- **Arc-style title-band drag**: pressing on an empty spot of the page's top
  band moves the window after 3 pt of movement. Shipped. (FACT, `CLAUDE.md:388`)
- **Refreshed Arc-like look** with space icons and themed frame: open PR #392,
  not merged. **Interruptible space switching** with cross-fades and Reduce
  Motion: open PR #395. Planned. (FACT, PRs #392, #395)

## UI, look, and feel

**Layout.** Sidebar on the left (or right). From the top: window buttons with
back, forward, reload; the address field; the favorites grid; the pinned
section; a separator; the regular tabs; a bottom bar with space dots and
library buttons. The page sits in a rounded card beside it, unless "Hide
border" makes it flush. The AI chat or developer panel opens as a column on the
other side. (FACT, `CLAUDE.md:243`; `CHANGELOG.md` 1.1.1;
`App/Window/WindowView.swift:31-58`)

**Visual language.** Every value comes from one token file, `NookDesign.swift`,
and the rules forbid literals elsewhere. (FACT, `CLAUDE.md:231`) In practice
38 animation literals remain outside it, not counting vendored code (FACT,
grep; see the motion table).

- **Radii** (all continuous squircles): 4 favicon, 6 small button, 8 row and URL
  bar, 12 tile and card, 16 dialog and toast, 24 command palette. (FACT,
  `NookDesign.swift:22-28`)
- **Spacing** scale 2/4/6/8/12/16/20/24. Rows 32 pt tall with 2 pt gaps, folders
  indent 20 pt, sidebar minimum 206 pt. (FACT, `NookDesign.swift:37-97`)
- **Elevation**, not ad-hoc shadows: `floating` = black 16%, radius 32, y 12;
  `raised` = black 5%, radius 2, y 1. Branch-free, so shadows animate. (FACT,
  `NookDesign.swift:227-236`)
- **Surfaces**: hover fill `primary` at 4.5%, pressed 8%, hairline 8%,
  unloaded tabs at 55% opacity, modal scrim black 40%. (FACT, `NookDesign.swift:147-157`)

**Materials.** No blur, no vibrancy, no Liquid Glass. Liquid Glass came in
1.1.1 and 1.2.0 and was removed in 1.2.1 because "it did not match our calm
browser philosophy". The sidebar is a static two-stop gradient from the space
accent, blended 55% toward the window background (80% when the window is
inactive). The code says this is cheaper than the blur it replaced because
nothing samples the backdrop per frame. (FACT, `CHANGELOG.md` 1.2.1;
`NookDesign.swift:193-213`; CLAIM on cost, `CLAUDE.md:243`)

**Typography.** System font only. Body 13 pt medium for tab titles; 12 pt for
the URL bar; 11 pt captions; 15 pt palette input; 17 pt dialog titles. (FACT,
`NookDesign.swift:117-129`)

**Color and themes.** One accent per space. It tints the sidebar gradient,
folder icons, the active space dot, the empty-page view ("Ah, peace."), and the
load bar. Private windows use neutral gray plus a purple overlay at 38%. The
Agent space has a fixed amber-to-magenta gradient no user accent can match.
Light, dark, or system appearance. (FACT, `NookDesign.swift:156-167`;
`CLAUDE.md:243`)

**Motion, from code.**

| Element | Value | Source |
| --- | --- | --- |
| Token `quick` (hover, press) | `easeOut`, 0.12 s | `NookDesign.swift:135` |
| Token `standard` (selection, reveal, fold) | `smooth`, 0.22 s | `NookDesign.swift:136-137` |
| Token `spring` (palette, dialog, toast, drag reorder, Peek) | `snappy`, 0.3 s | `NookDesign.swift:141` |
| Token `settle` (separator wave rising and flattening) | `smooth`, 0.6 s; wave period 1.6 s, amplitude 3 pt, wavelength 56 pt | `NookDesign.swift:88-89,138-139` |
| Token `flight` (download to its button) | `easeIn`, 0.6 s | `NookDesign.swift:140` |
| Space swipe settle | 0.18 s, cubic-bezier(0.16, 1, 0.3, 1); haptic at 15% travel; commits past 30% or a flick faster than 0.8 widths/s | `Nook/ThirdParty/BigUIPaging/Implementations/PageView/Platform/PlatformPageView+macOS.swift:87-88,163-176` |
| Space change (data store, chrome) | `easeInOut`, 0.2 s | `Nook/Managers/BrowserManager/BrowserManager.swift:618,633` |
| Sidebar show and hide | `easeInOut`, 0.1 s | `BrowserManager.swift:664,673` |
| Edge-reveal overlay | `easeInOut` 0.15 s (or `quick` from the hotspot); slide from the edge plus fade. Trigger 6 pt, overshoot slack 12 pt, keep-open zone 52 pt past the sidebar, vertical slack 24 pt | `HoverSidebarManager.swift:23-29,140`; `Nook/Components/Sidebar/SidebarHoverOverlayView.swift:36,56-59` |
| AI column show and hide | `easeInOut`, 0.2 s, move from edge plus fade | `BrowserManager.swift:711`; `WindowView.swift:343-346` |
| Peek open | scale from 0.001 plus opacity, `snappy` 0.3 s; scrim black 30% | `PeekOverlayView.swift:37-49` |
| Dialog | in: y +30 plus blur 3; out: y −30 plus blur 3; `snappy` 0.3 s | `Nook/Components/Dialog/DialogView.swift:21-28` |
| Toasts | opacity plus blur 8 → 0; `smooth` 0.25 s | `Packages/NookUI/Sources/NookUI/Toasts/ToastView.swift:30-36`; `WindowView.swift:102-104` |
| Zoom popup | scale from 0 at top; `spring(response: 0.5, dampingFraction: 0.8)` | `WindowView.swift:116-117` |
| Split drop cards | pull 45% toward the cursor within 50 pt; haptic on enter and exit; `snappy` 0.3 s | `WebsiteView.swift:438-475` |
| Palette icon and site chip | scale 0.6 plus blur 2 (icon) or 8 (chip) | `CommandPalette/CommandPaletteView.swift:122,135-138` |
| Onboarding finish | Metal noise-distorted radial reveal over a window snapshot, `easeInOut` 0.55 s | `Onboarding/Components/TransitionView.swift:96`; `ViewTransition.metal` |
| AI tool glow | three angular gradients, line widths 4/8/12, blur 4/12/24, rotating forever at 2/2.5/3 s | `Nook/Components/Window/ToolExecutionGlowView.swift:28-72` |

**Signature interactions that feel great** (INFERENCE from code, unless
marked):

1. **Space swipe.** A real `trackSwipeEvent` pager with direction lock, one
   haptic tick, a flick threshold, and a short expo-out settle that takes over
   from system momentum.
2. **The separator is the progress bar.** While the organizer runs, the hairline
   becomes a travelling sine wave, then settles flat. `TimelineView` is paused
   when idle, and Reduce Motion swaps in a spinner.
   (`SpaceSeparator.swift:39-63`)
3. **Magnetic split cards.** Drop targets lean toward the dragged tab and tick
   on entry.
4. **Trails.** Child tabs nest under their opener, and Back on a child returns
   you to it.
5. **Video follows you into the sidebar.** The same live web view changes
   parent, so playback never restarts.
6. **Arc's title-band drag** and Escape that never drops you out of full screen.
7. **Download flight** into the downloads button.

**Things that feel bad or are risky.**

- **AI approvals are blocking system alerts** (`NSAlert.runModal`) titled "AI
  Tool Request", with Deny first. They freeze the app while open. (FACT,
  `AIService.swift:439-482`)
- **Reduce Motion is honored in one place only**, the separator. Space swipes,
  Peek, dialogs, and toasts ignore it. PR #395 adds it to space switching.
  (FACT, grep for `accessibilityReduceMotion`)
- **The token rule leaks.** `BrowserManager` uses literal 0.1 s and 0.2 s;
  onboarding 0.25 s; the zoom popup its own spring. (FACT, grep)
- **Continuous animations.** The tool glow (three blurred rotating gradients)
  and the update card's repeating gradient repaint every frame while shown.
  (FACT, `ToolExecutionGlowView.swift:66-72`;
  `Nook/Components/Sidebar/UpdateNotification/SidebarUpdateNotification.swift:112`)
- **Global mouse monitor.** Edge reveal listens to every mouse move system-wide,
  once per window, and hops to the main queue each time. The monitors start
  when a window appears, even while the sidebar is shown. (FACT,
  `HoverSidebarManager.swift:51-59,72-77`; `App/Window/WindowView.swift:27,125-130`;
  INFERENCE on cost)
- **Space switch polish.** A contributor says chrome color, space name, and page
  change after the slide rather than during it, and the gesture is not
  interruptible. (CLAIM, PR #395)
- **Design churn.** Liquid Glass added, then removed within two weeks; a large
  "Arc-like refresh" PR from a contributor is pending. (FACT, `CHANGELOG.md`; PR #392)

## Architecture

**Process model.** One app process holds all UI and state, all on the main
actor. Pages, extension background pages, and service workers run in WebKit's
own processes: sandboxed WebContent processes, plus WebKit's shared networking
and GPU processes. (FACT, `CLAUDE.md:351,369`) Nook adds its own child
processes only for Sparkle's XPC updater, extension native-messaging hosts, and
stdio MCP servers. (FACT, `Nook/Managers/AIManager/MCP/MCPTransport.swift:54-58`;
`Nook/Managers/ExtensionManager/NativeMessagingHandler.swift`) The app is **not
sandboxed**; it runs with the hardened runtime and no JIT exception. (FACT,
`CLAUDE.md:16,351`) `WKProcessPool` is gone from the code. (FACT, grep)

**How it integrates the engine.** A separate shell over the system framework.
No fork, no patches. Each space's profile is a
`WKWebsiteDataStore(forIdentifier: uuid)`. (FACT,
`Packages/NookWeb/Sources/NookWeb/Profile.swift:51`) Every tab configuration
must be `.copy()`-derived from the one configuration the extension controller
was built with. (FACT, `Nook/Managers/ExtensionManager/CLAUDE.md` "Critical")
Where public API stops, Nook calls about 20 private WebKit selectors
(`_setWindowOcclusionDetectionEnabled:`, `_clearBackForwardCache`,
`_resetNavigationGestureStateForTesting`, `_setEnabled:forFeature:`,
`_inspector`, and more). It also patches two AppKit methods: the title-band
drag region and `NSWindow cancelOperation:`. (FACT, grep; `CLAUDE.md:388-389`)
INFERENCE: each macOS release can break these, and Nook cannot patch WebKit
when a site breaks.

**One live view per page.** A page has one `WKWebView`. The coordinator moves it
into whichever window selected it last; other windows draw a placeholder.
Never resize a web view before it is in a window; never move one WebKit holds
in full screen. (FACT, `CLAUDE.md:358,371-372`)

**UI technology.** SwiftUI views inside AppKit windows. AppKit handles windows,
drag and drop (`NSView` drag sources, a custom pasteboard type), hover
(`NSTrackingArea`), floating panels, and the space pager. (FACT,
`CLAUDE.md:264-277,366`) State uses Swift Observation for the new model and
Combine `ObservableObject` for older managers. (FACT, `CLAUDE.md:170-177`)

**Languages.** Swift 5 language mode (Swift 6 strict concurrency is off). Rust
for the adblock FFI, shipped as a committed `xcframework`. JavaScript for
blocker, tweak, and dev scripts. One C target (`MuteableWKWebView`). One Metal
shader. (FACT, `CLAUDE.md:13,103,322`)

**Code layout and size.** ~65,600 lines of first-party Swift.

| Area | Lines | Notes |
| --- | --- | --- |
| `Nook/` (managers, components, models, utils) | 38,300 | 21 manager folders; `BrowserManager.swift` 1,285 lines is the hub. Not counted: 2,983 lines of vendored, Nook-modified BigUIPaging in `Nook/ThirdParty/` |
| `Packages/` (7 local SPM packages) | 22,273 | `NookTabsCore` (Foundation only), `NookSettings`, `NookDesign`, `NookBlocker`, `NookTweaks`, `NookWeb`, `NookUI` |
| `App/` | 1,916 | entry, window, menu commands |
| `CommandPalette/`, `Navigation/`, `Onboarding/`, `UI/` | 2,810 | |
| `NookiOS/` | 1,519 | unreleased iOS target |

(FACT, `wc -l`; `CLAUDE.md:189-205`. The first four rows sum to 65,299;
`scripts/tests/` adds 348.) The packages exist so an iOS app can reuse
the model, blocker, and views. (FACT, `README.md` Project Structure) A Hacker
News thread in December 2025 criticized the "Managers" structure and a
hard-coded two-part domain list. (FACT, <https://news.ycombinator.com/item?id=46170402>)

**Doc drift.** `README.md` says the tab organizer depends on MLX; no MLX package
is resolved and nothing imports it. `CLAUDE.md:27` says nothing targets iOS; the
project has an iOS target. `CLAUDE.md:366` says edge hover uses
`NSTrackingArea`; the manager uses global `NSEvent` monitors, and only the 6 pt
hotspot uses a tracking modifier. `CLAUDE.md:427` dates the run that published
`v1.2.1` to 2026-09-14; the Actions API shows that run on 2026-10-08. (FACT, each
file cited; `README.md:59`; Actions runs API)

## Data and storage

| What | Where | Format | Notes |
| --- | --- | --- | --- |
| Spaces, favorites, pinned, folders (synced scope) | `~/Library/Application Support/com.gstudios.nook/Tabs/structure.json` | JSON with `formatVersion`, 30-day tombstones | FACT, `CLAUDE.md:257` |
| Regular tabs and device state (open folders, windows, reopen list of 50) | `…/Tabs/device.json` | JSON | FACT, `CLAUDE.md:253,257` |
| Tab file backups | `…/Tabs/Backups/<yyyy-MM-dd>/`, 7 days | JSON copies | Saves coalesce 500 ms, atomic writes, sync flush on quit. A corrupt file loads the newest backup; with none, the app runs read-only and says why. (FACT, `Packages/NookTabsCore/Sources/NookTabsCore/TabStore.swift:29-30`; `CLAUDE.md:257`) |
| Ordering | inside the JSON | base-62 fractional keys, compared as strings; a move writes one item | FACT, `Packages/NookTabsCore/Sources/NookTabsCore/OrderKey.swift` |
| History and installed extensions | `…/default.store` (+ `-wal`, `-shm`) | SwiftData (SQLite) | Four unused legacy tables stay in the schema to avoid a migration. Schema mismatch backs up, then resets. 100-day retention. (FACT, `BrowserManager.swift:24-43,78-140`; `CLAUDE.md:175`; `Packages/NookWeb/Sources/NookWeb/HistoryManager.swift:33`) |
| Page text for history search | `…/History/page-text.sqlite` | SQLite FTS5, ≤20,000 chars per URL | On by default; not for private windows or the Agent space. (FACT, `BrowserManager.swift:459`; `PageSession+Navigation.swift:465-475`) |
| Session-only cookies | `…/SessionCookies/<space-uuid>.plist` | binary plist, mode 0600 | So a relaunch keeps you signed in. (FACT, `Profile.swift:160-215`) |
| Website data (cookies, storage, cache) per profile | `~/Library/WebKit/com.gstudios.nook/WebsiteDataStore/<uuid>/` | WebKit-managed | FACT, `App/LegacyDataMigration.swift:44-45` |
| Settings | UserDefaults domain `com.gstudios.nook` | plist | FACT, `CLAUDE.md:176` |
| AI provider config (no keys) | `~/Library/Application Support/Nook/ai_config.json` | JSON | FACT, `AIConfigService.swift:65-67` |
| AI API keys, HTTP auth credentials | macOS Keychain | Keychain items | Plaintext keys migrated out of UserDefaults. (FACT, `AIConfigService.swift:118-146,391-406`) |
| Extensions | `~/Library/Application Support/Nook/Extensions/<id>/` | unpacked | FACT, `Nook/Managers/ExtensionManager/CLAUDE.md` Installation step 6 |
| Favicons | `~/Library/Caches/FaviconCache/<host>.png` | PNG | Not namespaced by bundle id; ignores port (#380). (FACT, `Packages/NookWeb/Sources/NookWeb/FaviconCache.swift:32-33`) |
| Parsed blocker engine | `ContentBlocker/Cache/engine.dat` | 32-byte key + serialized engine | FACT, `CLAUDE.md:312` |
| DevMCP token | `…/dev-mcp-token`, mode 0600 | text | FACT, `DevMCPServer.swift:84-96` |
| AI chat history | memory only | — | INFERENCE, no persistence code found |

**Encryption.** No app-level encryption. Secrets go to the Keychain; token and
cookie files are 0600; everything else relies on FileVault. (FACT, files cited;
INFERENCE on FileVault)

**Data moves with the bundle id.** Nook has used three bundle ids
(`io.browsewithnook.nook` for 1.0.x, `com.baingurley.nook` for 1.1 to 1.2.1,
then `com.gstudios.nook`).
`LegacyDataMigration` copies the store, tabs, and WebKit data on first launch
under a new id. 1.0.x users could not auto-update and had to download a new DMG.
(FACT, `App/LegacyDataMigration.swift:6-13`; `CHANGELOG.md` 1.1.0)

**Shared state between builds.** Every build shares one bundle id, so two copies
running at once corrupt each other's tab files. (CLAIM, `CLAUDE.md:114`; the
shared paths are FACT, `TabStore.swift:50-52`)

**Sync.** None shipped. The iCloud branch uses `CKSyncEngine` in the private
database, with `encryptedValues` for space names, tab titles, and URLs; open
tabs from other Macs are published every 30 s. (FACT, branch files cited above;
`CloudSyncEngine.swift` `devicePublishInterval`)

**Server component.** None for the app. No accounts, no Nook backend. The
website is an Astro site that a Cloudflare Worker renders on each request
(every page sets `prerender = false`). It reads GitHub's release Atom feed.
(FACT, `CLAUDE.md:109`; `nook-browser/www` `wrangler.jsonc`, `astro.config.mjs`,
`src/lib/releases.ts:1-3`, `src/pages/index.astro:14`)

**Telemetry.** None found in app code. Sparkle system profiling is not enabled.
(FACT, grep; `Nook/Info.plist` SU keys) A file named `telemetry-id` with a UUID
sits at the repo root, committed 2026-02-17 in "various fixes"; nothing reads
it. (FACT, repo root; GitHub commits API)

**What leaves the machine, with default settings.**

- Sparkle checks `nook-browser.github.io/Nook/appcast.xml` daily and **installs
  updates automatically**. (FACT, `Nook/Info.plist`: `SUScheduledCheckInterval`
  86400, `SUAutomaticallyUpdate` true)
- What you type in the command bar goes to `suggestqueries.google.com` after
  each 125 ms pause in typing, because Google is the default engine. Private
  windows send none; other engines get none. (FACT,
  `SearchManager.swift:154-163,282-299`; `NookSettingsService.swift:456`)
- Favicon fetches from visited sites; Chrome Web Store, Edge, and AMO update
  checks for installed extensions, plus `versionhistory.googleapis.com` to learn
  the current Chrome version. (FACT, `Nook/Utils/WebStoreDownloader.swift:182-191`)
- Only when turned on: filter-list downloads, SponsorBlock (hashed video id
  prefix), AI provider calls, GitHub PR folder requests with your cookies.
  (FACT, files cited above; INFERENCE that lists refresh only while the blocker
  is on, from `ContentBlockerManager.swift:138-159`)

## Agents and AI

**Where it runs.** All in the app process, on the main actor. Tool calls go to
the page through `evaluateJavaScript`, mostly in the page's own JavaScript
world, so a hostile page can tamper with what the tools read. (FACT,
`Nook/Managers/AIManager/Tools/BrowserToolExecutor.swift:201-530`; INFERENCE
on tampering)

**Page representation.**

- Chat: page text extracted by script, cut to a token budget, plus the
  selection as `<selected_text>`. If the text is cut, a note outside the
  untrusted tag says so. (FACT, `CLAUDE.md:287`; `AIService.swift:501-563`)
- Tools: `getInteractiveElements` returns 50 elements with CSS selectors by
  default; the model can pass a higher `limit`, and nothing caps it. Clicks use
  a selector or visible text. No ref ids. (FACT, `BrowserTools.swift:37-58`;
  `BrowserToolExecutor.swift:276`)
- DevMCP `snapshot`: an accessibility outline (role, name, state), default 300
  nodes (capped at 2,000) and depth 12. A repeat call returns only changed
  lines. (FACT, `DevMCPServer.swift:262-268,537-547`)

**Tools.** Chat has 12 browser tools. DevMCP serves 31: those minus
`executeJavaScript`, plus `evaluate`, `download`, `screenshot`, `console`,
`network`, `perf`, `blocker_log`, `snapshot`, `pick`, `selection`, `reload`,
`wait_for_load`, `blocker_status`, `set_blocking`, `check_urls`, `closeTabs`,
`pinTab`, `user_scripts`, `pages`, `clear_page_cache`. (FACT,
`DevMCPServer.swift:227-356`)

**Providers and models.** Apple Intelligence (`FoundationModels`, 4,096-token
context on macOS 26, 8,192 on 27), Gemini, OpenRouter (a fixed list includes
free DeepSeek and GLM models), Ollama (`localhost:11434`, default `llama3`), and
custom OpenAI-compatible endpoints. Quirks are handled in code: Gemini 3's
`thoughtSignature`, GPT-5 rejecting `max_tokens`. (FACT, `CLAUDE.md:287-289`;
`NookSettingsService.swift:642-719`. The two context sizes are CLAIM: they are
Nook's budget comments, `AppleIntelligenceProvider.swift:34-39`, not Apple's docs.)

**Local models.** On-device Apple model by default when nothing else is set up;
no key, no download. The tab organizer uses the same model with greedy
sampling, a pinned array length per call, and a token cap on every call. (FACT,
`CLAUDE.md:150,287`)

**Permissions and safety.**

- Three modes: `auto`, `ask` (the default), `disabled`. (FACT,
  `Packages/NookSettings/Sources/NookSettings/AIModels.swift:199-202,228`)
- In `ask`, navigate, click, new tab, and switch tab prompt. "Allow All This
  Chat" turns prompts off for the rest of the chat. (FACT, `AIService.swift:56-59,338-350`)
- `executeJavaScript` prompts on every call, even in `auto` or after Allow All.
  (FACT, `AIService.swift:352-357`)
- MCP tools prompt even in `auto`, since a server may touch files or a shell;
  Allow All still covers them. (FACT, `AIService.swift:369-386`)
- Private windows get no tools and no page context. (FACT, `AIService.swift:140,314-317`)

**Prompt-injection defenses.**

- Page content and tool results are wrapped in a tag with a random suffix per
  request (`page_context_<8 hex>`); the tag name is stripped from the text; the
  system prompt says the content is data. (FACT, `AIService.swift:130,161,496-499`)
- For the on-device model, the project ran a 22-case eval and found the model
  "followed instructions planted in page text on every eval run whatever the
  prompt said". So its navigate and click tools ask, **even in `auto`**, unless
  the person's own message names the site or the button text (`personNamed`).
  A click by selector always asks. (CLAIM for the eval, `CLAUDE.md:287`; FACT
  for the rule, `Nook/Managers/AIManager/Providers/AppleIntelligenceProvider.swift:54-76`;
  `AIService.swift:401-430`)
- `personNamed` uses a seven-entry country-suffix list, not the public suffix
  list; it errs toward asking. (FACT, `AppleIntelligenceProvider.swift:61-66`)
- Cloud models in `auto` have no such check: mutating tools prompt only in
  `ask` mode. (FACT, `AIService.swift:338-350`) They also have no navigation
  containment and no critic. (INFERENCE, from reading `AIService.swift`)
- The eval files live in a gitignored folder, so I could not read them.

**Outside-agent access (DevMCP).**

- HTTP on loopback only; bearer token from a 0600 file; requests with a
  non-localhost `Origin` get 403 (the host is parsed, so
  `localhost.attacker.example` fails). 30 s per tool call. (FACT,
  `DevMCPServer.swift:33,67-70,134-141`)
- Off by default: needs Developer Mode and the Browser Control toggle; starts
  and stops without relaunch. (FACT, `CLAUDE.md:143`) It does not depend on the
  AI chat setting; turning Ask Nook off leaves it running. (FACT,
  `App/NookApp.swift:189`)
- **Agent space.** Every tool except `pick` and `selection` acts in a dedicated
  space, created on first use, last in order, found by a marker, never by name.
  It **borrows the logins** of the space the person had open when the Agent
  space was created; that link is fixed at creation. Read-only tools (`pages`,
  `check_urls`, `getTabList`, `clear_page_cache`) do not create it. Agent activity
  never changes what any window shows. Agent pages get no extensions, no
  history, no Peek or mini windows, no other apps, and answer dialogs, file
  pickers, and auth without UI. (FACT, `CLAUDE.md:382`;
  `Packages/NookTabsCore/Sources/NookTabsCore/AgentSpace.swift:13-26`;
  `DevMCPServer.swift:357-359`)
- **Keeping a hidden page alive.** WebKit stops rendering pages outside a
  window. Nook hosts the agent's page in the active window at alpha 0, 20,000 pt
  off to the left, and turns off occlusion detection before it enters the
  window. Measured: 60 frames a second, IntersectionObserver fires. After 30 s
  idle it is parked. (FACT, `Nook/Managers/BrowserManager/BrowserManager+Agent.swift:9,22,58,97`;
  `Nook/Utils/WebKit/FocusableWKWebView.swift:90-96` for the occlusion switch;
  CLAIM for the measurement, `CLAUDE.md:382`)
- Chrome around it: the Agent space has its own gradient, a sparkle icon, a
  framed page with an "Agent" label, and a sidebar row that pulses while calls
  run. (FACT, `CLAUDE.md:382`; `NookDesign.swift:162-167,179`)
- **The token is the approval.** `evaluate` runs any JavaScript with no prompt,
  in the page's world by default or an isolated world on request
  (`DevMCPServer.swift:233,429`).
  `download` and `saveTo` write only under `~/Downloads/Nook MCP`. The project
  states: "Anything that can read the token file can drive the browser,
  including shipped Release builds." (FACT, `CLAUDE.md:382`;
  `Nook/Managers/DevMCPServer/DevMCPFiles.swift`)
- **Human hand-off.** `pick` starts the element picker and waits 25 s for the
  person's click; `selection` returns what the person sent with "Send to Agent":
  selector, HTML, changed styles, React or Vue component names, recent errors,
  and a screenshot. (FACT, `DevMCPServer.swift:274-285`)

**Skills, automations, CLI.** None. (FACT, absence)

## Build, release, and engineering

**Build system.** One Xcode project, one app scheme (plus the iOS target), seven
local SPM packages, three remote packages at the app level (Sparkle, Garnish
pinned to an untagged commit, FaviconFinder). `Package.resolved` holds 8 once
the local packages' dependencies are added (SwiftSoup, LRUCache, Chronicle,
swift-log, swift-atomics). Filesystem-synchronized groups add new files
automatically. (FACT, `CLAUDE.md:189-205,368,395-412`) Code coverage must be turned off
on the command line; otherwise package targets ship profiling counters (81.7 MB
vs 54.2 MB binary). (FACT, `CLAUDE.md:84-93`)

**CI.**

- `macos-build.yml`: on every PR and push to `develop`, builds unsigned Release
  on `macos-26`, then launches it on a `macos-15` runner and checks it is still
  running after 20 s. (FACT, `.github/workflows/macos-build.yml`)
- No tests run in CI. (FACT, same file)

**How they build the engine in CI.** They do not. WebKit is the system
framework. The nine tag runs of the release workflow (build, sign, notarize,
DMG, appcast) took 5 min 40 s to 15 min 37 s, median 6 min 39 s. (FACT, Actions
runs API for `macos-notarize.yml`, 2026-09-18 to 2026-10-24)

**Signing and notarization.** On a `v*` tag: import a Developer ID cert into a
temporary keychain, build Release with a reduced entitlements file (no push, no
autofill), re-sign Sparkle's binaries inside-out, re-sign the app with
`--options runtime`, notarize with `notarytool --wait`, staple, verify with
`spctl`, build a UDZO DMG. (FACT, `.github/workflows/macos-notarize.yml`)

**Update mechanism.** Sparkle 2 with an EdDSA key. The workflow signs the DMG
with `sign_update`, uploads it to the GitHub release, and appends an item to
`appcast.xml` on `gh-pages`. Each item carries `minimumSystemVersion` and an
`informationalUpdate` for builds below 110, so old installs see a link instead
of a broken install. Release notes come from the matching `CHANGELOG.md`
section. One channel; betas are retired. Every tag needs a new build number,
since Sparkle orders by it. (FACT, `macos-notarize.yml`; live feed has 16 items,
latest `sparkle:version="119"`; `CLAUDE.md:109`)

**Release cadence.** 1.1.0-beta.1 (Sep 18), 1.1.0 (Sep 22), 1.1.1 (Sep 24), 1.2.0 (Oct 6), 1.2.1 (Oct 8),
1.2.2 (Oct 11), 1.2.3 (Oct 13), 1.2.4 (Oct 23), 1.3.0 (Oct 24), all 2026.
Release-asset download counts for 1.1.0 to 1.3.0 are 175 to 665 per version on
2026-10-25 (1.1.0-beta.1: 74), and include Sparkle updates. The 1.0.x line peaked at 4,848 downloads (1.0.2). (FACT, releases API)

**Tests.** No Xcode test target (the project has two app targets and nothing
else); `xcodebuild test` fails. `NookTabsCore` has a
`swift test` suite (63 test functions in packages). Other logic is checked by
"Checks": tiny `@main` programs of `precondition`s compiled against the shipped
source (`Packages/*/Checks/`, `scripts/tests/`), about 1,130 lines. With the
`NookTabsCore` suite (about 1,300 lines) and the Rust tests (about 280), test
code is about 2,700 lines in all. Rust
tests guard blocker rules (`tests/no_overbroad_rules.rs`). Node scripts guard
scriptlet globals and redirect rules. (FACT, `CLAUDE.md:95,324`; `scripts/`;
`Nook.xcodeproj/project.pbxproj:252,281`; grep and `wc -l` counts)

**Verification without stealing focus.** Their agent instructions say: launch
with `open -g`, drive through DevMCP over `curl`, read state from logs and JSON
files, and call out what needs a human (dialogs, drag, Peek, PiP). Power and
memory are measured with `proc_pid_rusage` on a copy with its own bundle id.
(FACT, `CLAUDE.md:380,384`)

**How they track upstream.** No engine to track. New macOS APIs go behind small
wrappers with fallbacks. Filter lists refresh in CI before each release. uBO
scriptlets are vendored at a pinned commit with a refresh script. CI uses the
runner's default Xcode, unpinned. (FACT, `CLAUDE.md:365,312,325,427`)

**Process.** Gitflow with `develop`, `main`, tags. One worktree per agent. Agent
notes and plans stay in a gitignored `docs/`. User-visible text may not change
without the maintainer's approval. AI use must be disclosed by contributors.
(FACT, `CLAUDE.md:105-119,429-435`; `CONTRIBUTING.md`)

## Strengths and weaknesses (critical)

**Strengths**

1. **Small and native.** An 18 MB DMG and a CI release run of about 6.5
   minutes (median), against rac's hours-long Chromium build. (FACT for the DMG
   and the run time; INFERENCE on the comparison)
2. **Engineering notes are unusually honest and specific.** `CLAUDE.md` records
   measured numbers (launch to first paint 2,147 → 607 ms; 3.5 GB of suspended
   back/forward pages across six tabs) and the traps behind each rule. (CLAIM
   for the numbers, `CLAUDE.md:262,361`)
3. **Agent space is a clean answer to "let my own agent drive the browser".**
   Separate space, borrowed logins, no change to what the person sees, visible
   chrome when they look. (FACT)
4. **Tab model is careful.** Two scopes (synced vs device), fractional order
   keys, tombstones, daily backups, and read-only mode instead of data loss.
   (FACT)
5. **Blocker depth.** adblock-rust plus uBO scriptlets plus site-specific JSON
   pruning, with regression guards. (FACT)
6. **Calm, cheap visuals by policy.** No blur, a static gradient, one token file,
   and they removed Liquid Glass on purpose. (FACT)
7. **Small-model honesty.** They tested the on-device model against injection,
   saw it fail, and gated its actions on what the person said. (CLAIM + FACT)

**Weaknesses**

1. **WebKit bet.** Sites tested only in Chrome can fail (Canvas LMS and Kaltura,
   #371). No Widevine; FairPlay only. No iCloud Keychain passkeys. The engine
   updates only with macOS. (FACT, #371 is open, `CLAUDE.md:17`; CLAIM for DRM,
   from comments in the closed #263)
2. **Private SPI and swizzles** in about 20 places. Each OS release is a risk.
   (FACT; INFERENCE on risk)
3. **Bus factor of one**, with a year-long near-stall before the revival and
   heavy AI-written code since. (FACT)
4. **Almost no automated tests, none in CI.** Verification is build plus manual
   run. (FACT)
5. **Defaults undercut the privacy story.** Blocker off; typed text sent to
   Google for suggestions; auto-installing updates; AI chat on by default. (FACT)
6. **Weak AI safety for cloud models.** Blocking alerts, a broad "Allow All This
   Chat", page-world scripts, and an MCP token that grants unprompted
   JavaScript on logged-in sessions. (FACT; INFERENCE on severity)
7. **Identity churn.** Three bundle ids and two signing teams in a year broke
   auto-update for 1.0.x users. (FACT)
8. **Doc drift** between `README.md`, `CLAUDE.md`, and code (MLX, iOS target,
   hover method). (FACT)
9. **Reduce Motion mostly ignored**; several continuous animations. (FACT)
10. **No command actions in the palette**, no tab auto-archive, two-pane split
    only. (FACT)

## What rac should take (ranked, concrete, with rough cost) and what rac should avoid

Cost: **S** = a few days of one agent thread; **M** = one to two weeks;
**L** = three to six weeks. Costs assume rac's patch workflow and are
INFERENCE.

**Plain English.** The best things to borrow are about how outside agents and
the built-in agent behave. Give outside agents their own hidden space with your
logins, so they never move your tabs. Make the agent ask before going somewhere
you didn't name. Then copy a handful of motion numbers and the tab-file safety
rules. Skip Nook's engine choice and its loose defaults.

### Take

1. **"Did the person name it?" check for rac's `auto` level (S–M).** Closes the
   known gap where `auto` lets cross-site navigation and model-written typing
   through with no card. Nook's rule (`AppleIntelligenceProvider.swift:54-76`):
   a navigation or new tab to a site whose name is not in the person's own
   message asks, even at `auto`. So does a click whose button text the person
   did not write. Nook applies it to the on-device model only. Two parts would
   be rac's own additions, since Nook has neither (INFERENCE): exempt the
   attached tab's own site, and ask before typing text the user did not supply
   on a site they did not name (Nook has no typing tool). Use Chromium's
   registrable-domain helper instead of Nook's seven-suffix list. Pair it with
   the first injection evals: Nook's claim that a small model obeyed planted
   text "on every eval run" is the case to reproduce.
2. **Agent space for outside agents (L).** Rac's MCP server today serves only the
   agent rac launched, during its run, and turns off with AI. Copy Nook's
   shape: a reserved space, created on first use, marked by an id rather than a
   name, that borrows the login profile of the space the user had open; agent
   tabs never take focus; popups stay inside it; no history, no extensions; a
   distinct frame and a pulsing sidebar row while calls run. Keep rac's guard,
   cards, and containment in front of it. Do not copy the "token is the
   approval" rule for script execution. Chromium-side, a hidden tab has to keep
   rendering; Chromium's capture-count mechanism may do what Nook's alpha-0
   trick does. (INFERENCE; needs a spike)
3. **Developer tools over MCP, plus "Send to Agent" (M).** `console`, `network`
   with a `since` cursor, `perf`, `screenshot`, an outline `snapshot` that
   returns only changed lines, and `pick`/`selection` for "this element". Rac's
   own agents would use it to test rac with screenshots, which the maintainer
   wants. Chromium already has most data via DevTools; the work is a curated,
   permissioned surface. Gate it the way Nook does: off unless a developer
   setting is on.
4. **One motion-token file and the numbers that work (S).** Adopt four tokens:
   quick 120 ms ease-out (hover, press); standard 220 ms smooth (selection,
   reveal); spring ≈ snappy 300 ms (overlays, dialogs, drag); settle 600 ms.
   Space swipe: 180 ms settle on cubic-bezier(0.16, 1, 0.3, 1), one haptic at
   15%, commit past 30% or 0.8 widths/s. Edge reveal: 6 pt trigger, 12 pt
   overshoot, 52 pt keep-open hysteresis. Unlike Nook, honor Reduce Motion
   everywhere from day one.
5. **Tab-store safety rules (S–M).** For rac's spaces and pinned data: atomic
   writes coalesced at 500 ms, dated daily backups kept 7 days, load the newest
   good backup on decode failure, and a read-only mode with an alert rather than
   overwriting. Tombstones (30 days) prepare for sync. Fractional order keys make
   a move write one item.
6. **Trails (M).** A link opened from a tab nests under it; closing the parent
   promotes children; Back on a child with no history returns to the parent and
   closes the child. Arc refugees know the idea from Zen and Safari.
7. **Small, calm micro-interactions (S each).** The separator that becomes a
   wave while something works (paused when idle; a spinner under Reduce Motion);
   magnetic split-drop targets (45% pull within 50 pt, one haptic tick); a space
   dot that shows its name after a 0.7 s hover; the blur-plus-opacity toast
   (blur 8). Skip the always-rotating AI glow.
8. **Full-text history search (M).** Local FTS5 of the first 20,000 characters
   of each page, off in incognito, deleted with its history row. Ship it off by
   default or ask during onboarding, given rac's privacy stance. Needs a privacy
   review.
9. **Arc import details worth matching (S, inside rac's planned Arc import).**
   Read `StorableSidebar.json` as a tree, map each Arc profile to a profile with
   Arc's name from `Local State`, copy favorites into each space of that
   profile, reinstall extensions by store id, and keep the member card. Arc
   users reported flattened subfolders and silent repeat imports that made
   duplicate spaces (#143, 2025).
10. **Live folders and favorite hover cards (M, after release).** A pinned
    folder that fills from a source (GitHub PRs) refreshed on activation, never
    on a timer. Nook uses an undocumented GitHub endpoint and the user's cookies;
    rac should prefer a documented API and an explicit opt-in.
11. **Process habits (S).** A launch-on-oldest-macOS smoke job in CI; changelog
    sections that become release notes and Sparkle notes automatically; an
    `informationalUpdate` item for builds that cannot install an update; a
    `TRADEMARK.md` that asks forks to rename.

### Avoid

- **Blocking system alerts for agent approvals** and a chat-wide "Allow All".
  Rac's inline cards and per-site rules are better. (FACT, `AIService.swift:439-482`)
- **"The token is the approval" for arbitrary JavaScript** on logged-in
  sessions. Any process that reads the file owns the browser. (FACT, `CLAUDE.md:382`)
- **Tools that read through the page's own JavaScript world.** Use isolated
  worlds or browser-side extraction, as rac's snapshot does.
- **Privacy-weak defaults**: typed text sent to Google for suggestions (after a
  125 ms pause), AI chat on by default, silent auto-install of updates. Rac's "AI off costs
  nothing" rule is stricter; Nook starts configured MCP servers at launch
  whether or not chat is used. (FACT, `App/NookApp.swift:115-125`)
- **Changing the bundle id or signing team.** It stranded every 1.0.x install.
  Rac's AGENTS.md already forbids the equivalent; Nook is the cautionary tale.
- **System-wide mouse monitors** for edge reveal, and **animations that run
  forever** (the three-layer glow, repeating gradients).
- **Style churn** like adding then removing Liquid Glass inside two weeks.
- **Docs that drift from code.** Nook's `CLAUDE.md` is rich but wrong in places.
- **Switching engines.** Nook shows the WebKit ceiling: compatibility gaps,
  no Widevine, no system passkeys, and no way to patch the engine. Rac's
  Chromium base is the right call for Arc refugees. (INFERENCE)

## Open questions and things you could not verify

1. Nook's performance claims ("up to 3x faster launch", "measured against other
   browsers", `CHANGELOG.md:63,66`) rest on a gitignored `docs/perf/`; I could not see the data or
   method.
2. The 22-case on-device injection eval lives in a gitignored folder; I could
   not check the cases, the scoring, or the cloud-model behavior.
3. I did not run Nook. Motion feel, hover timing, and real memory use are read
   from code, not observed.
4. Whether the ad blocker being off by default is deliberate for macOS (the iOS
   target turns it on) is unclear; `CLAUDE.md` calls blocking a top priority.
5. What the root `telemetry-id` file is for. Nothing in the app reads it.
6. Whether Chromium's capture count (or another mechanism) keeps a hidden agent
   tab rendering at full rate, as Nook's alpha-0 window trick does for WebKit.
7. Whether rac can call Apple's on-device model (`FoundationModels`, Swift-only)
   from Chromium's build without a large Swift bridge. Nook proves the model
   is usable for chat and grouping, but also that it obeys injected text.
8. How many people actually use Nook. GitHub download counts mix new installs
   and Sparkle updates, and there is no telemetry.
9. Whether PR #392 (an Arc-like visual refresh) and PR #395 (interruptible space
   switching) will merge, which would change the look described here.
10. Whether the iCloud sync branch will ship, and how it will handle trails,
    which it currently ignores.

## Sources

Repository and code (shallow clone at `/tmp/rac-overhaul/src/Nook`, `develop`
@ `242c7fbcb49279a50de18ad8e5e699fd3a60e3d9`):

- `README.md`, `CHANGELOG.md`, `CLAUDE.md` (453 lines), `ASSESSMENT.md`,
  `CONTRIBUTING.md`, `TRADEMARK.md`, `docs/adblocker-architecture.md`
- `Packages/NookDesign/Sources/NookDesign/NookDesign.swift`
- `Nook/ThirdParty/BigUIPaging/Implementations/PageView/Platform/PlatformPageView+macOS.swift`
- `Nook/Managers/HoverSidebarManager/HoverSidebarManager.swift`
- `Nook/Managers/BrowserManager/BrowserManager.swift`, `BrowserManager+Agent.swift`, `BrowserManager+Import.swift`
- `App/Window/WindowView.swift`, `App/NookApp.swift`, `App/LegacyDataMigration.swift`
- `Nook/Components/Peek/PeekOverlayView.swift`, `Nook/Components/Dialog/DialogView.swift`,
  `Nook/Components/WebsiteView/WebsiteView.swift`, `Nook/Components/Window/ToolExecutionGlowView.swift`,
  `Nook/Components/Sidebar/SidebarHoverOverlayView.swift`, `Nook/Components/Sidebar/MediaControls/SidebarPiPPanel.swift`
- `Packages/NookUI/Sources/NookUI/Rows/SpaceSeparator.swift`, `Spaces/SpacesList.swift`,
  `Toasts/ToastView.swift`, `BlurModifier.swift`
- `CommandPalette/CommandPaletteView.swift`, `CommandPalette/CommandPalette.swift`
- `Nook/Managers/AIManager/AIService.swift`, `AIConfigService.swift`,
  `Tools/BrowserTools.swift`, `Tools/BrowserToolExecutor.swift`,
  `Providers/AppleIntelligenceProvider.swift`, `Providers/OpenRouterProvider.swift`,
  `MCP/MCPTransport.swift`, `MCP/MCPManager.swift`
- `Nook/Managers/DevMCPServer/DevMCPServer.swift`, `DevMCPFiles.swift`
- `Packages/NookTabsCore/Sources/NookTabsCore/AgentSpace.swift`, `TabStore.swift`, `OrderKey.swift`
- `Packages/NookSettings/Sources/NookSettings/NookSettingsService.swift`, `AIModels.swift`, `SiteSearch.swift`
- `Packages/NookWeb/Sources/NookWeb/SearchManager.swift`, `Profile.swift`,
  `PageSession+Navigation.swift`, `HistoryTextIndex.swift`, `HistoryManager.swift`,
  `FaviconCache.swift`, `BrowserConfig.swift`
- `Nook/Managers/ExtensionManager/CLAUDE.md`, `Nook/Utils/WebStoreDownloader.swift`
- `Nook/Managers/ImportManager/ImportManager.swift`, `Arc.swift`
- `Nook/Components/Browser/Window/TabCompositorView.swift`
- `Onboarding/Components/ViewTransition.metal`, `Onboarding/Components/TransitionView.swift`
- `Nook/Info.plist`, `Nook/Nook.entitlements`, `Nook.xcodeproj/project.pbxproj`,
  `Nook.xcodeproj/project.xcworkspace/xcshareddata/swiftpm/Package.resolved`
- `.github/workflows/macos-build.yml`, `.github/workflows/macos-notarize.yml`
- Branch `origin/feature/icloud-sync`: `Packages/NookSync/Sources/NookSync/CloudSyncEngine.swift`,
  `RecordMapper.swift`, `Nook/Nook-CI-iCloud.entitlements`
- `NookiOS/BrowserModel.swift`

Website repo (shallow clone at `/tmp/rac-overhaul/src/nook-www`): `src/data/team.ts`,
`src/pages/roadmap.astro`, `wrangler.jsonc`, `astro.config.mjs`, `src/lib/releases.ts`.

GitHub API (read-only, 2026-10-25):

- Repo metadata: <https://api.github.com/repos/nook-browser/Nook>
- Releases: <https://github.com/nook-browser/Nook/releases>
- Contributors and commits per month on `develop`
- Actions runs for `macos-notarize.yml`: <https://api.github.com/repos/nook-browser/Nook/actions/runs>
- Issues and PRs: <https://github.com/nook-browser/Nook/issues/349>,
  <https://github.com/nook-browser/Nook/issues/285>, <https://github.com/nook-browser/Nook/issues/263>,
  <https://github.com/nook-browser/Nook/issues/143>, <https://github.com/nook-browser/Nook/issues/371>,
  <https://github.com/nook-browser/Nook/issues/378>, <https://github.com/nook-browser/Nook/issues/380>,
  <https://github.com/nook-browser/Nook/issues/382>, <https://github.com/nook-browser/Nook/issues/386>,
  <https://github.com/nook-browser/Nook/issues/387>, <https://github.com/nook-browser/Nook/pull/392>,
  <https://github.com/nook-browser/Nook/pull/395>

Web:

- Sparkle feed: <https://nook-browser.github.io/Nook/appcast.xml>
- Site: <https://browsewithnook.com/>
- Hacker News, "Nook Browser" (2025-12-06, 138 points, 119 comments):
  <https://news.ycombinator.com/item?id=46170402>
- Product Hunt: <https://www.producthunt.com/products/nook-an-open-source-arc-alternative>
- gitpicks.dev write-up (low reliability; dates conflict with GitHub):
  <https://gitpicks.dev/featured/featured-nook-browser-gpl-arc-alternative>

rac context: `plans/context/maintainer-brief.md`, `docs/internals/ai.md`
(sections "The rac MCP server", "Containment"),
`patches/rac/sidebar-reveal/edge-reveal.patch`.

## Verification

Fact-checked on 2026-10-25 by a second agent. Sources: the clone at
`/tmp/rac-overhaul/src/Nook` (`develop` @ `242c7fb`, still the branch head per
`gh api repos/nook-browser/Nook/commits/develop`), the `nook-www` clone
(`b5838b6`), the GitHub REST API (repo, releases, commits, contributors,
issues, branches, Actions runs), `appcast.xml` on `gh-pages`, and the Hacker
News API. Every row was checked against one of these primary sources.

| # | Claim checked | Result | Change made |
| --- | --- | --- | --- |
| 1 | GPL-3.0; name, wordmark, and icon are Gurley's trademarks | Confirmed: `LICENSE`, `TRADEMARK.md:1-10`, API `license.spdx_id` | None |
| 2 | 1,980 stars, 84 forks, 21 open issues and PRs; created 2025-08-01 | Confirmed: repo API | None |
| 3 | #349 opened 2026-08-06; Gurley took over 2026-09-17 | Confirmed: #349 comments; closed 2026-09-17T20:09Z | None |
| 4 | 9 releases since 2026-09-18; 7 in 1.0.x; 1.0.2 peaked at 4,848 | Confirmed: releases API. The download range was stale (164 to 665); it is now 175 to 665 | Updated range; added the beta to the cadence list |
| 5 | 465 `develop` commits since 2026-09-01, 461 by Gurley, 192 disclose AI | 465 and 461 confirmed. Disclosures are 188 (the two stock prefixes) to 195 (every phrasing), not exactly 192 | Changed to "about 190" with the range |
| 6 | 17 contributors | Confirmed (18 with anonymous) | None |
| 7 | DMG 18.3 MB; binary 54.2 MB | DMG confirmed (18,251,990 bytes). The binary size appears only in the project's own notes | Binary re-tagged CLAIM |
| 8 | About 65,600 first-party Swift lines; 70,100 in all | Confirmed: 65,647 and 70,149. The `Nook/` row (41,283) included 2,983 vendored lines | Row corrected to 38,300; vendored lines noted |
| 9 | macOS 15.5+, Apple Silicon only, iOS target 0.1.0 | Confirmed: `project.pbxproj:419,596-604`; `-arch arm64` in both workflows | Workflow citations added |
| 10 | About 20 private selectors; two AppKit method patches | Confirmed: 15 literal selectors plus about 5 built at run time; `method_setImplementation` in `TitlebarDragRegion.swift:48` and `EscapeKey.swift:38` | Wording made exact |
| 11 | Motion tokens 0.12 / 0.22 / snappy 0.3 / 0.6 / 0.6; wave 1.6 s, 3 pt, 56 pt | Confirmed: `NookDesign.swift:88-89,135-141` | None |
| 12 | Space swipe 0.18 s, curve (0.16, 1, 0.3, 1), haptic at 15%, commit past 30% or 0.8 widths/s | Confirmed: `PlatformPageView+macOS.swift:87-88,163-173,222-225` | None |
| 13 | Edge reveal 6 / 12 / 52 / 24 pt, 0.15 s, global monitor | Confirmed: `HoverSidebarManager.swift:23-29,51-59,140`. Also found: the monitors run even while the sidebar is shown | Added that finding |
| 14 | Reduce Motion is honored only in the separator | Confirmed: the only hit is `SpaceSeparator.swift:19` | None |
| 15 | Tab store: two JSON files, 500 ms coalesce, 7 dated backups, read-only fallback, 30-day tombstones, base-62 keys | Confirmed: `TabStore.swift:24-32,50-52,101-104`; `TabTree+Repair.swift:5`; `OrderKey.swift:4-7` | None |
| 16 | Full-text history: FTS5, 20,000 chars, on by default, skipped for private and Agent pages | Confirmed: `HistoryTextIndex.swift:6,122`; `PageSession+Navigation.swift:466,473`; `NookSettingsService.swift:478` | None |
| 17 | Defaults: blocker off, Google, DevMCP off, organizer off, "AI chat visible" | Confirmed, except the AI column starts closed (`BrowserWindowState.swift:52`). Only the feature is on | "Visible" changed to "on" in three places |
| 18 | Google gets "every keystroke" | Inaccurate: the request waits for a 125 ms pause (`SearchManager.swift:155`) | Corrected in three places |
| 19 | Sparkle checks daily and installs on its own; 16 feed items; latest build 119; `informationalUpdate` below 110 | Confirmed: `Info.plist:45-60`; live appcast; `macos-notarize.yml:244-256` | None |
| 20 | PR CI builds on `macos-26`, launches on `macos-15` for 20 s, runs no tests | Confirmed: `macos-build.yml:20,55,64-70` | None |
| 21 | Release run "7 min 33 s" (CLAIM) | Replaced with Actions API data: nine tag runs, 5:40 to 15:37, median 6:39. Also, `CLAUDE.md:427` misdates the `v1.2.1` run | Upgraded to FACT; added to doc drift |
| 22 | 63 test functions; no test target; Checks "about 2,700 lines" | 63 and no test target confirmed (`pbxproj` has two app targets). Checks are about 1,130 lines; 2,700 is all test code | Split the count |
| 23 | Chat agent: 20 rounds, 12 tools, `auto`/`ask`/`disabled` (default `ask`), JS always asks, MCP asks in `auto`, `NSAlert` with Deny first | Confirmed: `AIService.swift:45,51-59,338-357,369-386,439-482`; `AIModels.swift:198-201,228`; `BrowserToolExecutor.swift:48-60` | None |
| 24 | `getInteractiveElements` returns "up to 50" | Wrong: 50 is the default and nothing caps it (`BrowserToolExecutor.swift:276`) | Corrected |
| 25 | `page_context_<8 hex>` tag, stripped from the text | Confirmed: `AIService.swift:130,161,497-499` | None |
| 26 | `personNamed`: seven-entry suffix list, on-device only, a click by selector asks | Confirmed: `AppleIntelligenceProvider.swift:54-76`; `AIService.swift:403-430`. Cloud models in `auto` have no check, a FACT. Take #1 implied that Nook exempts the attached tab and gates typing. It does neither, and it has no typing tool | Upgraded that tag to FACT; Take #1 rewritten, rac's additions tagged INFERENCE |
| 27 | 22-case on-device injection eval | Cannot be checked: `docs/` is gitignored (`.gitignore:136-139`) | Stays CLAIM |
| 28 | DevMCP: `127.0.0.1:47823`, 0600 token, Origin host check, 30 s per call, 31 tools | Confirmed: `DevMCPServer.swift:24-33,84-96,134-141,227-356`; 11 chat tools plus 20 dev tools | Added: isolated-world option, 2,000-node cap, and independence from the AI setting (`NookApp.swift:189`) |
| 29 | Agent space: marker, borrowed logins, alpha 0, 20,000 pt offset, 30 s park, occlusion SPI | Confirmed: `AgentSpace.swift:13-26`; `BrowserManager+Agent.swift:22,58,97`; `FocusableWKWebView.swift:90-96` | Login link fixed at creation and read-only tools noted; citations fixed |
| 30 | Storage: session cookies (binary plist, 0600), AI config path, favicon path, legacy SwiftData tables, 100-day history | Confirmed: `Profile.swift:160-215`; `AIConfigService.swift:65-67`; `FaviconCache.swift:31-35`; `CLAUDE.md:175`; `HistoryManager.swift:33` | None |
| 31 | No telemetry; `telemetry-id` committed 2026-02-17 in "various fixes" | Confirmed: grep finds no analytics SDK; commits API (author `jonathancaudill`) | None |
| 32 | Website is "a static Cloudflare site" | Wrong: Astro with the Cloudflare adapter, every page `prerender = false`, so a Worker renders it | Corrected |
| 33 | Site search chips for 15 sites | Wrong: 14 (`SiteSearch.swift:61-131`) | Corrected |
| 34 | 57 shortcut actions | Confirmed: `KeyboardShortcut.swift:35-212` | None |
| 35 | Boosts "existed in 2025 and were removed" | Imprecise: `ASSESSMENT.md` (dated 2026-03-20) still lists Boosts code | Corrected |
| 36 | Three remote packages | Confirmed at the app level; `Package.resolved` lists 8 | Added |
| 37 | Liquid Glass added in 1.1.1 and 1.2.0, removed in 1.2.1 with the quoted reason | Confirmed: `CHANGELOG.md:83,105,123` | None |
| 38 | PRs #392 and #395 open; #395 describes the space-switch lag | Confirmed: issues API; PR body | Stays CLAIM |
| 39 | HN thread: 2025-12-06, 138 points, 119 comments, "Managers" and domain-list criticism | Confirmed: HN API item 46170402 and the thread | None |
| 40 | #143 is about folder flattening | Partly: the issue reports no feedback and duplicate spaces; flattening comes up in the comments | Reworded |
| 41 | No Widevine, FairPlay only | #263 is a closed request; its comments say FairPlay works | Re-tagged CLAIM |
| 42 | iCloud branch: `CKSyncEngine`, private database, `encryptedValues`, 30 s publish, last commit 2026-09-23 | Confirmed: branch files; branches API | None |

**Not checked:** the Arc and Safari import details beyond the file headers,
the extension install paths, and most `CLAUDE.md`-only behavior notes, such as
the PDF, print, and Escape routing. The 2,147 → 607 ms launch figure and the
3.5 GB figure appear verbatim in `CLAUDE.md:361` and
`TabCompositorView.swift:46-47`. Both stay CLAIM because the method lives in the
gitignored `docs/perf/`.

**Overall confidence: high.** Every code-level number I checked matched the
cited file. Line ranges drifted in a few places, and I fixed those. The errors
were in counts (site chips, AI disclosures, line totals), two
characterizations (the "static" site and "every keystroke"), and one
overreach in Take #1. Live counts (stars, downloads) will drift after
2026-10-25.
