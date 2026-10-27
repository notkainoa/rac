# Cra: research dossier

Researched 2026-10-27 from a shallow clone of `github.com/VictorKildahl/cra`
(commit `94c3034`, 2026-10-27 13:25 +0100) at `/tmp/rac-overhaul/src/cra`, a
shallow clone of `chromiumembedded/cef` (commit `e537569`, 2026-10-23) at
`/tmp/rac-overhaul/src/cef`, the GitHub API, `crabrowser.app` (home, help,
design-notes, roadmap, release-notes, changelog, privacy, build), and Spotify's
public CEF index. I did not run, build, or download Cra. Paths written
`C:<path>` are inside the Cra clone; `E:<path>` are inside the CEF clone.

Tags: **FACT** = primary source (code, scripts, API, site text read as
written). **CLAIM** = the project's own marketing or self-report. **INFERENCE**
= my reasoning.

## In plain English (at most 150 words)

Cra is a free, open-source Mac browser that copies Arc closely. It is a Swift
app that wraps Chromium through CEF, a library built to embed Chromium in other
apps. The author builds the engine on their own Mac and downloads it in CI.
Cra adds only 5 small patches to Chromium. That looks cheap next to rac's
roughly 180. It is not free, though. CEF itself carries 118 patches touching
about 470 files, and someone else maintains them. Cra pays instead at the seam,
with private-API hacks and a loss of Helium's privacy patches. It is three
days old, with 14 releases, one developer, and Claude co-authoring most
commits. It has no AI, no sync, and a domain-list ad blocker. Take its Arc
import and its exact Arc measurements. Do not copy the engine choice.

## Snapshot

| Field | Value |
| --- | --- |
| What it is | "A native macOS browser with a sidebar instead of a tab strip" (FACT, GitHub description). Swift (AppKit + SwiftUI) shell around Chromium Embedded Framework (FACT, `C:README.md:7-12`) |
| Engine | CEF `156.0.14+g4fa4ab5+chromium-156.0.8078.48`, pinned in `C:scripts/fetch-cef.sh:12`. A custom CEF build, not Spotify's (FACT, `C:docs/release.md`, "The Chromium engine (CEF)") |
| Platform | macOS 14+, **Apple silicon only** (FACT, `C:README.md`, `C:scripts/fetch-cef.sh` pins `macosarm64`). Intel is "Later" on the roadmap (CLAIM, crabrowser.app/roadmap) |
| License | MIT (FACT, `C:LICENSE`, API) |
| Repo | Created 2026-10-24 17:47 UTC. Pushed 2026-10-27. 49 stars, 4 forks, 0 open issues, 2 issues ever (both closed) (FACT, API) |
| Authors | One person, `VictorKildahl` (27 commits, contributors API), Copenhagen. A second person reported two security bugs (credited as "Rainatsu", changelog 0.1.11) |
| AI use | 23 of the 27 commits carry `Co-Authored-By: Claude` (FACT, commits API). 85%, against rac's 96% |
| Size | 80 Swift files, 21,878 lines; 2,384 lines of Objective-C++/C++ bridge; no `Tests/` directory (FACT, `wc`, `find`) |
| Releases | 14 app releases from v0.1.0 (2026-10-25) to v0.1.13 (2026-10-27 12:30 UTC), plus 3 engine pre-releases (FACT, releases API) |
| Downloads | About 400 DMG downloads in total. v0.1.10 alone has 139 (FACT, summed from `download_count`) |
| Business model | None. Free, no account, no server (FACT, site) |

## Features

Source for the list: changelog and help page (CLAIM), checked against code
where noted.

**Sidebar and spaces.** Favorites grid, pinned tabs with a remembered "home
URL" and reset, a per-space "Today" list, nested folders, a space dock with
emoji, per-space colour theme (one or two colours, intensity, grain). Switch
with Ctrl+1..9, Option+Cmd+arrows, or the dock. Drag spaces to reorder
(0.1.13). Floating sidebar on left-edge touch. Click a space name to collapse
its pinned tabs (FACT, changelog 0.1.0, 0.1.5, 0.1.13; `C:Sources/Cra/UI/Windows/FloatingSidebar.swift`).

**Favorites are per space now.** Since 0.1.9 each space has its own favorites;
the home page and help page still say "shared across all spaces" (FACT,
changelog 0.1.9 vs. crabrowser.app home and help). Stale marketing.

**Command bar.** Cmd+T or Cmd+L, 766 pt wide. Searches open tabs, archive,
history, a bundled domain list, and actions. Ranks by recency, switch
frequency, and what you picked for the same prefix. All local (FACT,
`C:Sources/Cra/Services/SuggestionEngine.swift`, `C:Sources/Cra/Model/SidebarModel.swift`
`RankingData`).

**Archive.** Today tabs auto-archive after 12 h, 24 h, 7 d, 30 d, or never. The
archive records why a tab left: manual, auto, cleared, or space removed (FACT,
`ArchiveReason`, `AutoArchiveThreshold`).

**Split view.** Up to 4 panes, horizontal or vertical, saved as one sidebar row.
Gap 10 pt, minimum pane 200 pt. Pane add/remove has no animation by design
("Arc lays the new pane out within a single frame", `transitionDuration = 0`)
(FACT, `C:Sources/Cra/UI/SplitView/SplitPaneLayout.swift:21-32`).

**Little Windows.** Links from other apps open in a small sidebar-less window;
Cmd+W archives it, Cmd+O moves it into a space. **Air Traffic Control**: rules
route links to a space or a Little Window (FACT, changelog 0.1.10).

**Other.** Picture in Picture with auto-pop-out when you leave a playing tab.
Site Control Center. Tab switcher on Ctrl+Tab with previews. Download "flight"
animation into the Library button. Multiple windows and incognito (0.1.11).
Profiles, assignable per space (0.1.11). Per-site Developer Mode (Ctrl+D) with
docked Chrome DevTools. Rebindable shortcuts. Find with match count. Four
search engines (Google, DuckDuckGo, Bing, Kagi) (FACT, changelog).

**Not there.** Easels, Boosts, Peek, Notes, AI, sync, Windows/Linux, Intel
(CLAIM, home, roadmap). Next: "GitHub live folders" (CLAIM).

## UI, look, and feel

**Toolkit.** AppKit owns windows, layout, animation, and anything touching the
engine. SwiftUI draws the sidebar rows, command bar, settings, onboarding, and
toolbar, hosted in `NSHostingView`. The README says "AppKit + SwiftUI" and the
code agrees (FACT, `C:README.md:9`, `C:Sources/Cra/UI/ShellView.swift`,
`C:Sources/Cra/UI/Windows/MainWindowController.swift`).

**Window anatomy.** One `NSWindow` (full-size content view, transparent
titlebar). Its content is a `ShellView` with a behind-window blur, a gradient
background, the sidebar, and a rounded content card per pane. Each page is **not**
a view in that card. Each page is its own frameless Chrome window, attached as
a child window and moved to follow the card's frame (FACT,
`C:Sources/Cra/UI/ShellView.swift:1-20`, `C:Sources/CraCEF/CraCEF.mm:1277-1296,
1372-1377`, `C:Sources/Cra/UI/Windows/MainWindowController.swift:711-730`).
Details in Architecture.

**Look.** Arc clone, measured. The author wrote down Arc 1.170 and Dia 1.54
measurements in 1,514 lines of notes (`C:docs/arc-reverse-engineering.md`) and
fitted the sidebar blur to Arc's output pixels. `CraTuning` exposes lift,
dim, alpha, and `NSVisualEffectView` material as live knobs through
`cra://debug?...` (FACT, `C:Sources/Cra/UI/Tuning.swift`). Fitted values:
active lift 0.35 (bottom 0.37), blur dim 0.36, inactive lift 0.28 with dim
1.0, toolbar black overlay 0.40, default material `.hudWindow`. The light
vibrant path uses private `CABackdropLayer` and `CAFilter` gaussian blur
(FACT, `ShellView.swift:104-112,162`).

**Metrics** (FACT, `C:Sources/Cra/UI/Theme.swift:317-336`): sidebar 220 to 520
pt, default 328; row height 40, row spacing 1, row corner 10, indent 18;
content card corner 6 (square at the toolbar join in 0.1.12); toolbar 32;
title row centre 24; command bar 766 wide; find bar 300x38.

**Motion parameters.** All values below are FACT from the code, with the file
cited. They are the most reusable part of Cra for rac.

| Interaction | Parameters | Where |
| --- | --- | --- |
| Sidebar hide/show (Cmd+S) | 0.085 s, bezier (0.15, 0.7, 0.3, 1). Comment: "66 / 87 / 96 / 99 % of the travel after frames 1-4" at 60 fps, fitted to Arc | `ShellView.swift:601-622` |
| Floating sidebar in/out | Same 0.085 s curve. 2 pt edge trigger, 24 pt leave slack, 12 pt corners, 8 pt margin | `FloatingSidebar.swift:30-37,172-196` |
| Space page settle | `.interpolatingSpring(duration: 0.4, bounce: 0, initialVelocity: <release speed>)` | `SidebarUIState.swift:70-73` |
| Row move, folder open, archive | `.snappy(duration: 0.22, extraBounce: 0)` | `SidebarItemView.swift:152,223,249,362` |
| Drag drop indicator | `.snappy(duration: 0.2, extraBounce: 0)` | `SidebarListDrop.swift:111` |
| Pinned collapse | `.easeInOut(0.25)` | `SidebarRootView.swift:458` |
| Hover fills | `.easeOut(0.15)` | many |
| Downloads tray | open 0.12 s with 25 ms stagger per row from the bottom, close 0.05 s with 15 ms stagger | `DownloadsTray.swift:45` |
| Download thumbnail dropping into the Library bin | y keyframes: -6, then 12 (0.15 s cubic), hold 0.05, then -2 (0.13), then 0 (0.07); opacity 0 to 1 in 0.05 s | `SpaceDock.swift:244-252` |
| Split pane add/remove | 0 s (none) | `SplitPaneLayout.swift:30` |
| PiP controls | fade in 0.15 s, out 0.25 s, ease-out | `PictureInPictureControls.swift:84-112` |
| Onboarding springs | `response 0.35 to 0.6, dampingFraction 0.7 to 0.85` | `OnboardingSteps.swift:510`, `ImportFlowArt.swift` |

Space cells are 34x32 pt with no gap, 6 pt hover corners, white at about 7.8%
on dark spaces (FACT, commit `94c3034` message). The space swipe follows the
trackpad live and settles with the zero-bounce spring, copied from Dia's
`PageSwipeController` (FACT, `SidebarUIState.swift:60-70`).

**Reduced motion.** I found no use of `accessibilityReduceMotion` or
`NSWorkspace.accessibilityDisplayShouldReduceMotion` in `Sources/` (FACT,
`grep`). INFERENCE: Cra ignores that setting. rac's rules say reduced motion must work.

**Website.** Instrument Serif headings, Geist body, near-white background, one
cobalt accent, product images drawn in CSS (CLAIM, `/design-notes`). The site
source is a private repo (FACT, `C:README.md`).

## Architecture

### How Cra embeds Chromium: the direct answer

**CEF, with a custom-built distribution, using CEF's Chrome-style runtime in
Views windows.** Not the content API directly, not a stock prebuilt
framework, and not a Helium-style fork.

1. **Library.** `libcef_dll_wrapper` (CEF's C++ wrapper, built by CMake in
   `vendor/cef`) is linked into an Objective-C++ target `CraCEF`
   (`C:Package.swift:22-48`). `CraCEF` exposes `CraBrowser` and
   `CraCEFRuntime` to Swift (`C:Sources/CraCEF/include/CraCEF.h`, 242 lines).
   `CraCEF.mm` is 1,984 lines. Swift never sees a C++ type.
2. **Processes.** Five helper apps ("Cra Helper", Alerts, GPU, Plugin,
   Renderer) copied from one `CraHelper` binary whose `main` is 8 lines:
   load the framework, call `CefExecuteProcess` (FACT,
   `C:Sources/CraHelper/main.cc`, `C:scripts/build.sh:51-62`).
3. **Run loop.** `CraApplication` is an `NSApplication` subclass that
   implements `CefAppProtocol`. `main.swift` calls `CefInitialize`, then
   `CefRunMessageLoop()`, so Chromium owns the AppKit run loop (FACT,
   `C:Sources/Cra/App/main.swift:48-82`).
4. **Two hosting modes** (FACT, `CraCEF.mm:1366-1390`):
   - **Chrome hosting (default, `chromeEngine = true`).** Each tab is
     `CefBrowserView` inside `CefWindow::CreateTopLevelWindow` with
     `CEF_RUNTIME_STYLE_CHROME`, frameless, hidden Chrome toolbar. Cra attaches
     that window as a child of its main `NSWindow` and resizes it with the
     card. The setting is "Chrome engine for pages (extensions, Chrome
     DevTools)" in Settings, Advanced (`AdvancedPane.swift:19`).
   - **Alloy fallback.** `windowInfo.SetAsChild(containerView)` puts
     Chromium into a plain `NSView`. No extensions, no Chrome DevTools UI.
5. **Why child windows.** Chrome style needs Chromium's own Views window to
   get extensions, the extension toolbar container, and Chrome's DevTools dock.
   A hidden Chrome toolbar is kept alive on purpose because "extension popups
   need its extensions container as their anchor, and
   `Extensions.triggerAction` crashes without one" (FACT,
   `CraCEF.mm:1228-1236`).

### Which Chromium version, and how it updates

- **Now:** Chromium 156.0.8078.48 (CEF 156.0.14). Helium's 0.20.1.1 is also on
  156 (FACT, `plans/research/helium.md:42`), so Cra is on current stable. rac is
  on 154 (brief).
- **Pin.** One line in `C:scripts/fetch-cef.sh` holds the CEF version. CI
  caches `vendor/cef` keyed on its hash (FACT, `C:.github/workflows/ci.yml`).
- **Custom build, hosted on GitHub.** `scripts/build-cef.sh` checks out
  Chromium and CEF through CEF's `automate-git.py`, applies Cra's 5 patches,
  and builds with `is_official_build=true proprietary_codecs=true
  ffmpeg_branding=Chrome symbol_level=0`. Output is a 135 MB
  `cef_binary_macosarm64_minimal.tar.bz2`, uploaded by `publish-cef.sh` as a
  GitHub **pre-release** named `cef-156.0.14-codecs2` (FACT, scripts; releases
  API). Reason given: Spotify's builds lack H.264 and AAC, so MP4 and HLS video
  failed on X, Instagram, Reddit (FACT, `C:docs/release.md`, changelog 0.1.8).
- **The build runs on the author's Mac, by hand.** "GitHub's free macOS runners
  are too small (3 cores, 14 GB disk, 6 hour jobs)." Needs about 80 GB free.
  Same-major update: 1 to 2 hours. New major: "3-4 hours" (CLAIM, `release.md`).
- **Detection is automated, building is not.** A daily workflow
  (`cef-updates.yml`, free Linux runner) compares the pin with Spotify's
  `index.json` and opens one issue "Chromium engine update available" with the
  command `scripts/update-cef.sh <version>` (FACT, `check-cef-update.sh`).
  Issue #1 shows it fired on 2026-10-26 and was closed 19:45 UTC the same day
  (FACT, `gh issue list`).
- **Observed speed.** `cef-154.0.34-codecs1` published 2026-10-26 14:06 UTC;
  `cef-156.0.14-codecs1` 19:40 UTC, 5.5 hours later; v0.1.10 "Chromium 156"
  shipped 19:58 UTC (FACT, releases API). INFERENCE: either the 156 build was
  already running before the 154 build finished, or a full major compile is
  faster than the docs say on this machine. Either way, one person changed
  Chromium major in one afternoon.
- **Spotify's index** lists CEF 156.0.14, 156.0.8, 156.0.7, 154.0.34 as stable
  macOS arm64 builds (FACT, `index.json`, 2026-10-27). INFERENCE: CEF follows
  Chrome stable within days.

### Patch surface: Cra versus rac

| | rac | Cra |
| --- | --- | --- |
| Own patches on Chromium | about 180 patch files, about 870 hunks, about 216 upstream files (brief; `plans/research/rac-baseline.md`) | **5 patches, 11 hunks, 6 files**, 195 diff lines in total (FACT, `C:scripts/cef-patches/`) |
| Patches under that, owned by someone else | Helium and ungoogled-chromium: Helium merges them each release | **CEF: 118 patch files, 475 file diffs (473 distinct files), 1,044 hunks** (FACT, `E:patch/patches/*.patch`, counted with `grep -c`) |
| Code outside Chromium | rac code is inside Chromium's tree under `chrome/browser/ui/rac/` etc. | 21.9k lines Swift + 2.4k lines ObjC++ in a separate app, plus CEF's `libcef` (488 files, about 89k lines of C++/ObjC++/headers, FACT, `E:libcef`) |
| Who rebases for a new Chromium | The maintainer, on top of Helium's rebase | CEF's maintainers, then Cra re-applies 5 patches and rebuilds |
| Who builds the engine | rac CI (never finished a release) | The author's Mac, 80 GB, hours |
| Privacy patches | Helium's (Google services removed, uBlock Origin built in) | **None of Helium's or ungoogled-chromium's** |

**Reading the table.** INFERENCE:

1. **Cra did not delete the patch surface. It moved most of it under CEF.**
   CEF's patch set (1,044 hunks across 473 files) is larger than rac's
   (about 870 across about 216). Cra gets it free because the CEF project
   keeps it current for every Chromium branch.
2. **What Cra owns is small because the seam is a public C++ API.** The 5
   patches fix gaps in how CEF's Chrome style handles extensions and
   passkeys. They are small and have clear comments. That is the lesson for
   rac's "cheap to update" rule: a narrow, stable seam with a few documented
   hooks.
3. **The cost moved to the shell.** Cra's Swift app swizzles private AppKit
   and Chromium methods to make child windows behave (FACT):
   - `ChromiumWindowCorners` overrides `_shouldRoundCornersForSurface`,
     `topCornerRounded`, `bottomCornerRounded`, `_cornerRadius`,
     `_getCachedWindowCornerRadius`, `_cornerMask` on the frame view class
     (`ChromiumWindowCorners.swift:30-60`). Its comment says macOS 26 behaves
     differently depending on which SDK the app was linked against, and a
     release built on the macos-15 runner showed a notch (changelog 0.1.12).
   - `ChromiumChildHover` replaces `-[RenderWidgetHostViewCocoa
     shouldIgnoreMouseEvent:]` so hover works across sibling windows.
   - `CraApplication` redirects the accessibility focused window to the
     parent so window managers move Cra, not a page.
   - Eleven `NSClassFromString`/`NSSelectorFromString` sites in `Sources/Cra`,
     including `CAFilter` and `CABackdropLayer`.
   These break silently on a macOS or Chromium change and no test covers them
   (there are no tests).
4. **Ardia reached the same conclusion from experience.** Ardia began on CEF
   (Chrome style) on 2026-09-25 and had removed it by 2026-10-09, two weeks later. Its architecture
   review on 2026-10-01 said "Most of our fighting is with CEF, not with
   Chrome," with 42% of a week's commits touching the CEF seam (FACT,
   `plans/research/ardia.md:221-226`, citing `A:docs/architecture-review.md`).
   Cra's patches and swizzles are the same fights: extension windows,
   popup anchoring, window type reported to extensions, hover, corners.
5. **Cra lives with extra limits that rac does not have** (INFERENCE from
   code): every page is a window, so Mission Control, fullscreen, and
   Spaces integration need workarounds. 0.1.11 fixed "Video fullscreen left
   an empty desktop behind in Mission Control." Tab hiding is
   window ordering, not a view toggle. No measurement of tab-switch latency or
   memory exists anywhere in the repo or docs.

### What Cra patches in Chromium, and why

All five apply to a CEF-patched Chromium 156 tree (FACT, `C:scripts/cef-patches/`):

| Patch | Files | Why |
| --- | --- | --- |
| `extensions-normal-windows.patch` | `extension_action_api.cc`, `browser_extension_window_controller.cc` (4 hunks) | CEF hosts pages in popup-type Browsers. Extensions then see every tab as a popup, so password managers treat each tab as a sign-in popup. Patch reports "normal" for CEF-hosted views and lets `chrome.action.openPopup` work |
| `extension-install-ui-null-tab.patch` | `extension_install_ui_desktop.cc` (2 hunks) | Web Store install crashed when the browser has no active tab ("made Cra quit", changelog 0.1.8) |
| `cors-origin-header.patch` | `proxy_url_loader_factory.cc` (1 hunk) | CEF's proxy sanitized the `Origin` header to `null` for `chrome-extension://`, and 1Password's servers refused it |
| `keychain-service-name.patch` | `keychain_password_mac.mm` (1 hunk) | Keychain item "Chromium Safe Storage" is shared by every Chromium app; rename to "Cra Safe Storage" |
| `webauthn-keychain-access-group.patch` | `chrome_web_authentication_delegate.cc` (3 hunks) | Derive the Touch ID passkey keychain group from the app's own `application-identifier` |

Cra also patches a **binary**, not source, as a stopgap: for CEF
156.0.14-codecs2 it overwrites the string and two instruction immediates in the
framework with `dd` at fixed offsets (`0xc4fcaa1`, `0x215fe50`, `0x215ff8c`) to
rename the keychain item, guarded by a SHA-256 of the framework (FACT,
`C:scripts/fetch-cef.sh:41-57`). That is brittle by design, and the script
refuses any other build.

### Process model and security posture

- **No Chromium sandbox.** `settings.no_sandbox = true`, `-DUSE_SANDBOX=OFF`,
  and the helper `main` never calls the sandbox initializer (FACT,
  `CraCEF.mm:1824`, `C:scripts/fetch-cef.sh:35`, `C:Sources/CraHelper/main.cc`).
  INFERENCE: renderer processes run with the user's full rights. A renderer
  exploit becomes full local access. Helium and Chrome do sandbox. This is
  the biggest security gap I found, and the site never mentions it.
- **Hardened-runtime exceptions:** JIT, unsigned executable memory, library
  validation off, DYLD environment variables allowed, plus camera, microphone,
  location, and Apple Events (FACT, `C:resources/Cra.entitlements`).
- **Past bugs:** until 0.1.11 cookies and passwords were encrypted with the
  mock keychain's public constant `"mock_password"`, and web pages could run
  `cra://` scripting commands from a new tab (FACT, changelog 0.1.11,
  `C:Sources/Cra/Services/SafeStorage.swift:5-14`). Fixed on 2026-10-27.
- **Browser-level DevTools pipe.** Cra passes `--remote-debugging-pipe` on fds
  3 and 4 so its shell can call `Extensions.triggerAction`, `Target.*`, and
  `Page.captureScreenshot` without a TCP port. It disables the Blink
  `AutomationControlled` feature in renderers, or Google sign-in refuses
  ("This browser or app may not be secure") (FACT, `CraCEF.mm:415-430`).
- **Network posture beyond blocklist:** disables `WebRtcHideLocalIpsWithMdns`
  and sets WebRTC IP handling so no local address is offered, to avoid the
  macOS Local Network prompt (FACT, `CraCEF.mm:400-410`). Not otherwise
  hardened: I found no code that turns off Safe Browsing, the component
  updater, variations, or Google API calls, and no ungoogled-chromium-style
  patches. Whether Cra's CEF phones Google is **unmeasured** (see Open
  questions).

### Extensions

- **Chrome extensions work** through the Chrome-style runtime: Web Store
  install ("Add to Chrome"), unpacked folders, and import from Chromium
  browsers, Arc, and Dia (FACT, changelog 0.1.4, 0.1.8; `ExtensionStore.swift`).
- **Folders:** unpacked extensions live in `~/Library/Application
  Support/Cra/Extensions/<name>/`. Cra passes them all as one
  `--load-extension=a,b,c` switch at launch. Extensions installed from the
  Web Store live in Chromium's own profile folder and are discovered by
  scanning it (FACT, `CraCEF.mm:392-400`, `ExtensionStore.swift:60-75`).
  A change needs a restart ("Extensions load when Cra starts", help).
- **Toolbar buttons.** Cra draws its own pinned-extension buttons and clicks
  them by calling `Extensions.triggerAction` over the private DevTools pipe.
  Chrome opens the real popup; Cra repositions the popup window under its
  button (FACT, `ExtensionActions.swift:1-60`). Pinned list is
  `pinned-extensions.json`; the first time it reads `extensions.pinned_extensions`
  from Arc, Dia, or Chrome preferences.
- **Native messaging.** Before Chromium starts, Cra symlinks every
  `NativeMessagingHosts/*.json` from Chrome, Chromium, Edge, Brave, Arc, and
  Dia into its own profile, so 1Password and Bitwarden desktop apps connect.
  It excludes one: `com.openai.codexextension.json`, because ChatGPT's
  computer use switched to Cra instead of Chrome (FACT,
  `NativeMessagingHosts.swift`, changelog 0.1.10).
- **MV2:** the site says nothing. INFERENCE (unverified): stock Chromium 156
  has MV2 off, which may be why Cra's blocker is a domain list and not
  uBlock Origin. Ardia notes it bundled MV2
  uBO separately (`plans/research/ardia.md:83`).

### The blocker

- **Mechanism.** A CEF `CefResourceRequestHandler::OnBeforeResourceLoad`
  runs on the IO thread for every non-main-frame request. It cancels the
  request when (a) the host or a parent domain is in the list and (b) the
  request is **third-party** to the tab's top-level page (FACT,
  `CraCEF.mm:711-722`, `C:Sources/CraCEF/CraContentBlocker.h`).
- **List.** `resources/blocklist/domains.txt`, 22,513 lines, bundled in the
  app. It is the union of AdAway (CC BY 3.0) and Anudeep's adservers (MIT),
  fetched 2026-10-25, reduced to bare domains with covered subdomains dropped
  (FACT, `NOTICE.txt`). "Nothing is downloaded or reported" (CLAIM, help). No
  list updates ship except with an app update (INFERENCE).
- **Data structure.** An immutable `unordered_set<string>` published through
  an atomic pointer; lookups lock nothing. Old sets are never freed (FACT,
  `CraContentBlocker.h` comments). First-party test uses an approximate eTLD+1
  (last two labels, or three under a short list of `co.uk`-style suffixes),
  not the Public Suffix List. It fails open (FACT, comment in the same file).
- **What it cannot do** (INFERENCE from the mechanism): no cosmetic filtering,
  no URL-path rules, no scriptlets, no YouTube or first-party ad handling,
  no per-site toggle in the code I read (the setting is one boolean,
  `blockAdsAndTrackers`). It is a hosts-file blocker. It will miss anything
  served from the site's own domain.
- **Cost.** One hash lookup per subresource, per label of the host. When off,
  the handler returns early (FACT).

## Data and storage

**Everything is in `~/Library/Application Support/Cra/`**, or `$CRA_DATA_DIR`
for a second test instance (FACT, `C:Sources/Cra/Services/Persistence.swift:19-28`).
No database. No server. Every Cra file is one `Codable` JSON document written
by one class:

```swift
JSONStore<T>   // load once, save 0.4 s debounced, atomic write,
               // previous copy kept as <name>.bak, corrupt file moved to <name>.corrupt
```

Encoder: pretty-printed, sorted keys, ISO-8601 dates (FACT, `Persistence.swift:46-100`).

| File | Type | Contents |
| --- | --- | --- |
| `sidebar.json` | `SidebarDocument` | `version`(1), `spaceOrder`, `spaces[]`, `items[]`, `profiles[]?`, legacy `favoritesContainerID?` |
| `archive.json` | `[ArchivedItem]` | `archivedAt`, `reason`, `sourceSpaceID`, `wasPinned`, `item` (full `SidebarItem`), `fromLittleWindow?` |
| `windows.json` | `WindowPrefs` | `sidebarWidth`(328), `expandedFolders`, `collapsedPinnedSpaces`, `windows[]` (`WindowSession`: `focusedSpaceID`, `selectedTabPerSpace`, `frame`), `littleWindowSize` |
| `settings.json` | `AppSettings` | `autoArchive`, `searchEngine`, `showToolbar`, `developerHosts`, `chromeEngine`, `defaultLinkDestination`, `linkRoutes`, `autoPictureInPicture`, `blockAdsAndTrackers`, `warnBeforeQuitting`, and more |
| `history.json` | `[HistoryEntry]` | `url`, `title`, `lastVisit`, `visitCount` |
| `commandbar.json` | `RankingData` | `recentlySwitchedToTabs`, `queriesToSelected`, `commandUsage` |
| `keybindings.json` | `[String:[Shortcut]]` | overrides only |
| `downloads.json`, `pinned-extensions.json`, `deleted-profiles.json`, `extensions-welcomed.json` | small arrays | |
| `pending-credentials.json` | staged import | passwords and cookies **already encrypted** with Cra's key, mode 0600, applied at next launch then deleted |
| `Favicons/`, `chromium.log` | cache, log | |
| `Chromium/` | Chrome-style profile | `Default/`, `Profile <UUID>/` per Cra profile; History, Cookies, Login Data, Extensions, cache. **Not JSON**: Chromium's SQLite |
| `Extensions/<name>/` | unpacked extensions | |

**Item model** (`C:Sources/Cra/Model/SidebarModel.swift`, FACT). A flat
dictionary of `SidebarItem` keyed by UUID with explicit `children[]` ordering,
like Arc: `id`, `parentID`, `title?` (custom name, wins over page title),
`children`, `isUnread`, `createdAt`, and `data` as an enum:
`tab(TabData)` | `folder` | `container(ContainerKind)` | `split(SplitData)`.
`ContainerKind` is `favorites|pinned|today` plus `spaceID`. `TabData`: `url`,
`savedURL` (home), `savedTitle`, `muted`, `timeLastActiveAt`, `faviconKey`,
`customIconKey`, `tileColor`. `SplitData`: `widthFactors`, `orientation`,
`focusTabID`. `Space`: `id`, `title`, `emoji`, `theme` (`colors[]`,
`intensity`, `noise`, `appearance`, `vibrant`, `accent`), three container ids,
`profileID?`.

**Observations.**
- The help and privacy pages say "timestamped backups". The code keeps one
  `.bak` per file, and a comment says "minus the pile-up" (FACT,
  `Persistence.swift:43`). The site is wrong.
- Whole-file rewrite on every change, including `history.json`. Fine at 3 days,
  untested at 100k history entries (INFERENCE).
- `repair()` runs at every launch: drops dead child references, re-creates
  missing containers, rescues orphans into the first space's Today list
  (FACT, `SidebarStore.swift:62-90`).
- Tab runtimes are created lazily; archiving destroys the Chromium browser
  (FACT, `BrowserManager.swift:5-6`). I found no memory-pressure unload and
  no discard logic. A tab with a runtime stays live (INFERENCE).
- The model is Arc's on purpose, so Arc import is a near-direct mapping, and
  an Arc user who leaves Cra can in principle read the files by eye.

## Agents and AI

**There is no AI and no agent.** The site says "Arc Max will not be, because
Cra has no built-in AI," and the roadmap lists a built-in assistant as "Not
planned: Cra stays a browser" (CLAIM, home, roadmap). I found no model client,
no prompt, and no MCP server in the code (FACT, `grep` of `Sources`).

What does matter for rac's agent plans:

- **A scriptable shell.** `cra://action/<id>`, `cra://commandbar?query=`,
  `cra://open?url=&background=1&little=1`, `cra://import?source=arc&...`,
  `cra://dismiss`, plus `navigate`, `key`, `debug`. External links reach only
  `commandbar`, `dismiss`, and `open` with http(s). The rest need
  `defaults write dk.kildahl.cra scriptingURLs -bool YES` or a test instance's
  `CRA_COMMAND_FILE` (FACT, `C:README.md`, `AppDelegate.swift:225-232,381`).
  Pages cannot reach `cra://` (`OnProtocolExecution` blocks it, `CraCEF.mm:724-730`).
- **Raw CDP is one call away.** `navigate`/`debug` accept a DevTools method and
  JSON params and run them on the current page (`AppDelegate.swift:414-467`). With
  the private pipe, Cra already has the plumbing for an outside agent. It does
  not expose it.
- **A caution.** The author excluded ChatGPT's native-messaging host because
  its computer-use feature "took over Cra instead of Chrome" (changelog 0.1.10).
  Outside agents that look for "Chrome" will find any Chromium browser that
  copies Chrome's host manifests. rac should decide what an outside agent can
  see.

## Build, release, and engineering

**Build.** SwiftPM (`swift-tools-version:5.10`, Swift 5 mode) with three
targets. `scripts/build.sh` assembles `Cra.app` by hand (framework, five
helper apps, Sparkle), signs innermost first, and syncs into `build/Cra.app`.
Needs Xcode 16+ and CMake. `scripts/dev.sh` rebuilds and relaunches a debug
`CraDev.app` in about 4 s on save (CLAIM, README). The site says the build
needs about 1 GB (CLAIM, `/build`). The 135 MB CEF download is on top of that.

**CI.** `ci.yml` on `macos-26`: restores the cached CEF, runs `build.sh debug`,
verifies the bundle with `codesign --verify`. **No tests run and none exist**
(FACT, `C:.github/workflows/ci.yml`; no `Tests/` dir). Same gap as rac.

**Release pipeline.** Push a `v*` tag, then `release.yml` on `macos-26`
imports a Developer ID cert into a temporary keychain, runs `release.sh`
(build, sign, notarize, staple the app, DMG with `dmgbuild`, staple the DMG,
`spctl` check, sign the zip with the Sparkle EdDSA key, write `appcast.xml`),
and `gh release create` publishes `Cra.dmg`, `Cra.zip`, `SHA256SUMS.txt`,
`appcast.xml`. Names carry no version so `releases/latest/download/Cra.dmg`
always resolves (FACT, `docs/release.md`, `release.yml`). If secrets are
missing the workflow still publishes an ad-hoc build with install steps. The first two releases were probably built that way (INFERENCE: the help page says copies from before notarization, 0.1.0 and 0.1.1, show a malware warning). The pipeline works end to end. rac's has never finished a
release (brief).

**Update mechanism.** Sparkle 2, pinned and checksummed in `vendor/sparkle`.
`Info.plist` keys: feed `https://github.com/VictorKildahl/cra/releases/latest/download/appcast.xml`,
`SUPublicEDKey`, `SUEnableAutomaticChecks`, `SUAutomaticallyUpdate`,
`SUScheduledCheckInterval` 28800 (8 h) (FACT, `C:resources/Info.plist`).
A custom `SPUUserDriver` replaces Sparkle's windows with Arc-style banners and
an updater window. A downloaded update installs on quit, or restarts by itself
after 10 min in the background with 2 min idle, or 30 min idle, and holds off
for downloads, sheets, PiP, and power assertions (FACT, `docs/arc-reverse-engineering.md`
"Software updates"). Dev builds drop `SUFeedURL`. Sparkle compares
`CFBundleVersion`, taken from the clock so it always rises. Releases 0.1.0
and 0.1.1 cannot self-update (FACT, changelog 0.1.2). Sparkle's private key is
in a login keychain and in a GitHub secret (FACT, `release.md`).

**Contradiction.** The privacy page says "Cra does not check for updates or
phone home." The app checks GitHub every 8 hours by default (FACT, plist vs.
`/privacy`). The updates go only to GitHub, but the sentence is false as written.

**Passkeys.** Touch ID passkeys need a provisioning profile; iCloud Keychain passkeys need a managed Apple entitlement that `release.md` tells the account holder to request. The roadmap still lists passkeys under "Later" (FACT, `release.md` "Passkeys"; CLAIM, roadmap).

**Pace and maturity.** 27 commits and 14 releases in 3 days. A user's request for multiple windows
(issue #2) was closed at 10:01 UTC on 2026-10-27, five minutes after 0.1.11,
which added them (FACT, issues and releases APIs). That is fast. It is also an
early product with real faults (see Process model and security posture). Open issues: 0. The engine, the sandbox, MV2, and the network
footprint have not been looked at in public.

**Licensing risk worth noting.** The notes in `arc-reverse-engineering.md` read
Arc's binary strings, analytics keys, and view names, and the app reuses Arc's
copy ("An update is ready!"), tooltips, and pixel metrics. The site disclaims
affiliation. INFERENCE: rac should copy behavior, not strings or assets.

## Strengths and weaknesses

**Strengths**
1. A **working release loop** after three days: signed, notarized, stapled,
   Sparkle-updated, with a DMG that looks right. This is what rac lacks.
2. **Arc import is deep and exact**, and it also takes Zen, Firefox, Safari,
   and Chromium browsers, with passwords and cookies re-encrypted correctly.
3. **A tiny owned engine patch set** (11 hunks) with clear reasons.
4. **Motion and metric data from measuring Arc**, written next to the code as
   comments, with the fitting method. Reusable.
5. **Honest, simple privacy story:** no account, no server, plain JSON.
6. **Fast engine updates** by one person (154 to 156 in an afternoon).
7. **Self-describing scripting** (`cra://`) with an explicit security model
   after the 0.1.11 fix.

**Weaknesses**
1. **No renderer sandbox** (see Architecture). Not disclosed.
2. **No Helium-style privacy patches.** Google endpoints and Chromium services
   are unaudited. The "telemetry off" toggle on the site is a statement about
   Cra's own code, not about Chromium inside it (INFERENCE).
3. **A weak blocker:** domain list only, third-party only.
4. **Private-API swizzles** for corners, hover, and accessibility, with no
   tests, on a changing macOS.
5. **One-person, Apple-silicon-only, three days old, no tests.** Every release
   so far has fixed real bugs.
6. **The engine build is a manual 80 GB job** on one laptop. If it is lost or
   the author is away, there is no engine update. Binary patching is on the
   release path.
7. **Doc drift on the site:** favorites, backups, update checks, and "Chromium
   is not compiled locally" on `/build` (it is compiled, once, by the author;
   `fetch-cef.sh` now downloads that build). `docs/arc-reverse-engineering.md`
   still says "Cra uses WKWebView instead" (FACT, line 15).
8. **Arc-only audience.** Arc will close on 2026-12-22 (brief). After that the
   copy-Arc positioning has no source to copy and no new features to track.

## What rac should take and avoid

### Take

1. **Arc import design, with exact keys.** See the list below. rac has no Arc
   import yet (brief). Cra's reader is about 220 lines of Swift and handles the
   odd shapes (`[id, obj, id, obj]` lists, `_0` enum wrappers, Apple reference
   dates). A rac importer would run inside Chromium, so the reading must be in
   C++; the key paths transfer unchanged.
2. **Dia import.** Cra reads `Dia/StorableProfileContainers.json`, Dia's
   `User Data/<profile>/Bookmarks`, and optionally `StorableAutoArchive.json`.
3. **Credential re-encryption through a staged file** applied before the
   browser opens the databases. Pattern: read other browser's Keychain secret
   with the system prompt, PBKDF2-SHA1 to key, AES-128-CBC "v10", stage encrypted
   rows at mode 0600, insert at next launch.
4. **The release pipeline shape.** Tag-triggered, secrets-optional, stable
   asset names, appcast signed in the same job, retry on stapling. Compare to
   `docs/operations/releases.md`.
5. **Daily engine-update detector** that opens an issue with the exact command.
   rac can do the same for helium-macos releases (`gh api repos/imputnet/helium-macos/releases`
   is read-only; never post upstream).
6. **Motion numbers** (table above), especially the sidebar hide curve
   `(0.15, 0.7, 0.3, 1)` at 85 ms, the zero-bounce space settle spring, the
   `snappy(0.22)` row moves, and "no animation on split pane add/remove."
7. **Tab runtime laziness:** a tab has no browser until first opened.
   rac already unloads spaces; check whether pinned tabs are lazy too.
8. **Auto-archive with reasons** (manual, auto, cleared, space removed) and a
   searchable archive that feeds the command bar.
9. **Native-messaging host handling.** If rac wants 1Password to work, link
   hosts from Chrome's folders. Decide the exclusion list on purpose.
10. **An allow-listed scripting door.** Links from other apps get three safe
    verbs; everything else needs an explicit switch. A good default for rac's
    outside-agent door (see `ego-lite.md`, `aside.md`).

### Avoid

1. **Do not switch rac to CEF.** rac's value rests on being inside Chromium's
   Views UI with Helium's privacy patches. A CEF shell would give up Helium's
   patches, the in-process sidebar, and the zero-cost "AI off". It would add
   per-tab windows, private-API swizzles, and a CEF seam Ardia dropped after two weeks. It would also not remove the patch surface (CEF's own is larger).
2. **Do not run without the sandbox.** If rac ever embeds anything, keep it.
3. **Do not rely on a manual engine build on one machine.** If rac's CI cannot
   finish, fix CI, don't move the build to a laptop.
4. **Do not copy Arc's text or assets.**
5. **Do not claim "no phone-home" without a network capture.** Cra's
   privacy page already contradicts its own updater.
6. **Do not use binary patching** of a shipped framework.
7. **Do not ignore Reduce Motion.**

### Options for the engine question (maintainer to choose)

- **A. Stay on Helium + quilt** (today). Pro: keeps privacy, UI inside
  Chromium, one process model. Con: ~870 hunks to rebase; two majors behind.
- **B. Stay, and shrink the seam.** Move rac code into new files, and
  consolidate hooks into a few small "seam" patches. Cra's 11-hunk set shows
  the target. Needs a hunk budget per area and a CI check that counts hunks.

INFERENCE: A with B fits best. This is the maintainer's call.

### Arc import: exactly what Cra reads

All FACT, from `C:Sources/Cra/Services/Import/Importers.swift:97-243` and
`BrowserSources.swift:30-40`.

- `~/Library/Application Support/Arc/StorableSidebar.json`:
  `sidebar.containers[]`, the one containing `spaces`. Lists are flat
  `[id, object, id, object, ...]`. `items`: `title` (custom), `childrenIds`,
  `createdAt` (seconds since 2001), `data.tab.{savedURL,savedTitle}`,
  `data.list` (folder), `data.splitView`/`data.tabGroup` (flattened to
  tabs), `data.itemContainer.containerType.topApps._0` (favorites per
  profile). `spaces`: `title`, `containerIDs` as `["pinned", id, "unpinned", id]`,
  `profile`, `customInfo.iconType.emoji_v2` or `.emoji` (code point),
  `customInfo.windowTheme.background` → `appearanceBased.{dark,light}` or
  `single._0` → `style.color._0.blendedGradient._0.{baseColors[],overlayColors[],modifiers.{intensityFactor,noiseFactor}}`
  plus `isVibrant` and `contentOverBackgroundAppearance`.
- `.../Arc/SidebarItemsFaviconCache/<md5(item id)>`: 32 px PNG favicons.
- `.../Arc/StorableArchiveItems.json`: `items[].{sidebarItem, reason("auto"|other), archivedAt, source.space._0}`. Newest 1,500 kept.
- `.../Arc/StorableWindows.json`: `sidebarViewPreferences.sidebarWidth`.
- `.../Arc/StorableLinkRouting.json`: `defaultDestination`,
  `rules[].{sourceComponents[0].componentType.urlMatch{_0:{contains|matches},_1:text}, destination}`;
  destination is `littleArc` or `space` (mostRecent or an id mapped to a title).
- `defaults` domain `company.thebrowser.Browser`: `topBarURLEnabled`,
  `autoArchiveTimeThreshold`.
- `.../Arc/User Data/` (Arc's own Chromium profile): Bookmarks, Login Data,
  Cookies, Extensions, Preferences (`extensions.pinned_extensions`); passwords
  and cookies decrypted with Keychain item "Arc Safe Storage"/"Arc", after a
  macOS prompt.

Merge rule: spaces with the same title merge; tabs already present (same URL
in that section) are skipped, so it is safe to rerun (FACT, `Importers.swift`
`apply`, help page).

Not read: Arc's Boosts, Easels, Notes, live folders (Ardia reads live
folders, per `plans/research/ardia.md:77`), `StorableKeyBindings.json`.

## Open questions

1. **Does Cra's Chromium contact Google or others by default?** Safe
   Browsing, component updater, variations seed, CRLSets, Google API calls
   (no API keys in a CEF build is likely but unverified). Needs a network
   capture on a quiet Mac, which I was told not to do (no downloading or
   running Cra).
2. **Is there any sandbox in the helper processes?** Code says no. A runtime
   check (`sandbox-exec`/`ps`) was not possible.
3. **Does uBO or any MV2 extension load in CEF 156?** Not tested.
4. **Real tab-switch cost and memory** with one window per page. No numbers
   exist, and rac's "never slower than Helium" rule would need them.
5. **How long can one person keep up with a two-week Chromium cadence?**
   Cra's first major bump took an afternoon.
6. **Will CEF keep Alloy style?** Cra uses it as a fallback. The header still
   documents both styles (FACT, `E:include/cef_browser.h:1079`). I did not check
   CEF's forum for plans to retire it.
7. **Would the maintainer want a rac Arc importer in C++ inside Chromium, or
   as an out-of-process helper?** Both are possible. Helper binary is simpler
   to update; in-process shares the profile code.
8. **Does the maintainer want a "hunk budget" for rac** (option B)?

## Sources

**Primary (read in full or in the relevant parts)**
- Repo: https://github.com/VictorKildahl/cra, commit `94c3034`. Files cited
  as `C:` above: `README.md`, `Package.swift`, `docs/release.md`,
  `docs/arc-reverse-engineering.md`, `scripts/{fetch-cef,build-cef,update-cef,check-cef-update,publish-cef,build}.sh`,
  `scripts/cef-patches/*.patch`, `Sources/CraCEF/**`, `Sources/CraHelper/main.cc`,
  `Sources/Cra/**`, `resources/{Info.plist,Cra.entitlements}`,
  `resources/blocklist/*`, `.github/workflows/*.yml`.
- GitHub API: repo, releases (14 app + 3 engine), commits, contributors,
  issues (`gh api`, `gh issue list`, 2026-10-27).
- CEF: https://github.com/chromiumembedded/cef, commit `e537569`
  (`patch/patches/`, `libcef/`, `AI_POLICY.md`, `CHROMIUM_BUILD_COMPATIBILITY.txt`,
  `include/cef_browser.h`).
- Spotify CEF index: https://cef-builds.spotifycdn.com/index.json
- Site: https://crabrowser.app/ , /help , /design-notes , /roadmap ,
  /release-notes , /changelog , /privacy , /build (read 2026-10-27 through a
  summarizing fetch tool; quotes are as relayed by that tool).

**Cross-references inside this repo**
- `plans/context/maintainer-brief.md`
- `plans/research/ardia.md` (CEF history at lines 221-226, Helium privacy at 84)
- `plans/research/helium.md` (release cadence at line 42)
- `plans/research/rac-baseline.md` (patch counts, group table)

**Limits.** I did not run Cra. Everything about look and feel is from code and
the author's own notes, not from using the app. Site text was fetched through a
summarizer, so exact wording should be re-checked before quoting it publicly.
