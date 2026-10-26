# Ardia: research dossier

Researched 2026-10-25 from a shallow clone of `mantrakp04/ardia` at commit
`4309c1563a51283e06e4ea9925acb1eadebed946` (2026-10-25 11:29 PDT), plus the GitHub API, ardia.dev and a few
third-party pages. Paths written `A:<path>:<lines>` are inside that clone
(`/tmp/rac-overhaul/src/ardia`). The same file on GitHub is
`https://github.com/mantrakp04/ardia/blob/4309c1563a51283e06e4ea9925acb1eadebed946/<path>`.
Tags: **FACT** means a primary source (code, docs in the repo, GitHub API). **CLAIM** means the project's own
marketing or self-report. **INFERENCE** means my reasoning.

## In plain English (at most 150 words)

Ardia is a free Mac browser, made mostly by one person directing AI coding agents. It looks like Dia, with Arc's
sidebar habits. Pages run on Chrome's real engine, as in rac. The sidebar, buttons and menus are drawn by React
Native, a JavaScript toolkit, not by Chrome. It shipped 80 builds in its first month, all built on the owner's Mac.
There is no AI inside, but an outside agent can drive it with an `ardia` command once the user turns that on. It
imports from Arc, including spaces, pins and themes. It syncs through a folder in your iCloud Drive, locked with a
24-word phrase. Its docs time Dia's animations to the millisecond. It sends some data home: update counts and,
in today's nightly, a daily "opened" count. rac should borrow its shipping habits, speed patches, import design and motion
numbers. It should not copy the UI toolkit.

## Snapshot

| Item | Value |
|---|---|
| What it is | A macOS browser that copies Dia's UI and adds Arc's sidebar habits, with no AI (FACT: `A:AGENTS.md:3,53`; `A:README.md:7-9`). |
| Engine | Chromium 155.0.8059.84 with Helium 0.19.4 (helium-chromium) and 0.19.4.1 (helium-macos) applied, minus 15 skipped patches, then 60 Ardia patches, 46 scripted hooks and two code layers. Chrome's own `Chromium Framework.framework` is embedded and driven by Ardia's layer, "ArdiaCore" (FACT: `A:docs/engine-build.md:3-9,440-453`; `A:engine/patches/build/helium-pins.ini`; skip list `A:engine/patches/build/03-helium.py:46-65`). A per-site WebKit engine for DRM video arrived in 0.2.41-nightly.2 (notes dated 2026-10-24, published 2026-10-25 04:50 UTC) (FACT: `A:docs/release-notes/0.2.41-nightly.2.md:2,9`; releases API). |
| Platforms | macOS 14+, Apple silicon only (FACT: `A:README.md:17`). The Intel engine CI build was added 2026-10-25. All six `engine-x64.yml` runs that day failed or were cancelled, the last at 19:48 UTC, so no Intel engine exists yet (FACT: Actions runs API). Linux is a request (issue #1). |
| License | Distributed app: GPL-3.0, since 2026-10-23, because the engine now carries Helium's GPL patches. Ardia's own files: Apache-2.0. Before 2026-10-23 the whole repo was Apache-2.0 (FACT: `A:NOTICE:1-13`, `A:LICENSE` is the GPL-3.0 text, `A:LICENSE.Apache-2.0`; commits `2bbe12a6` 2026-09-26 "License: Apache 2.0" and `8129b3d4` 2026-10-23 "Ardia as distributed is GPL-3.0"). That explains why sources disagree. A CLA added 2026-10-24 lets the owner relicense contributions, including as proprietary (FACT: `A:CLA.md`, §2). |
| Repo | github.com/mantrakp04/ardia. Created 2026-06-19; history before 2026-09-25 is squashed into three commits (FACT: architecture review, written at `b885f89c` on 2026-10-01, read at `2713787d`, lines 3-8). |
| Stars, forks, issues | 807 stars, 82 forks, 211 issues (106 open), 135 PRs (61 open), 1,809 commits (FACT: GitHub API, 2026-10-25 about 19:50 UTC; an earlier pass that day saw 805 stars and 1,805 commits). |
| Age | First public release 2026-09-25 (v0.1.0, then named "Netnyahoo"). Renamed to Ardia in 0.2.33, 2026-10-12. The rename moved the bundle ID (`com.netnyahoo.browser` to `com.ardia.browser`) and the feed URL (`netnyahoo.com/appcast.xml` to `ardia.dev/appcast.xml`); it kept the EdDSA key and team, and the old domain stays attached for good (FACT: releases API; `A:docs/releasing.md:294-305`). |
| Release cadence | 80 app releases in 31 days: 48 stable, 32 nightly. The releases API also lists 2 engine-only prereleases (`engine-154.0.28+g564dd6c-*`, 2026-10-01). All 32 nightlies came on or after 2026-10-15 (about 3 a day), with 5 stables in that span, one every 2 to 3 days (FACT: releases API). 4,351 DMG and 2,094 update-zip downloads by 2026-10-25 about 19:50 UTC; 2,953 of the DMG downloads are 0.2.39 alone (FACT: asset `download_count`). |
| Team | Mantra Patel ("mantrakp04"), 1,787 of 1,809 commits; 11 outside people with 1 to 5 commits each, plus one `posthog-eu[bot]` commit (FACT: contributors API, 2026-10-25 about 19:50 UTC). All of the last 100 commits carry "Co-Authored-By: Claude Opus 5.5" (FACT: commits API). The owner's process runs Opus subagents in one checkout and asks Codex for reviews (FACT: `A:AGENTS.md:13-24`). |
| Business model | Free. "No paid tier, no catch" (CLAIM: ardia.dev FAQ). No revenue stated. The CLA names "a company the Owner forms" (FACT: `A:CLA.md`, §1). A future commercial turn is possible (INFERENCE). |
| Infrastructure | ardia.dev (Astro site, nginx), self-hosted telemetry (ClickHouse, OpenTelemetry Collector, SeaweedFS) on Hexclave; GitHub Releases for binaries; Homebrew tap (FACT: `A:infra/`, `A:docs/growth.md:110-160`, `A:docs/releasing.md:197-207`). |

## Features

Status: **shipped** (in a stable release), **beta** (nightly only), **planned** (open issue or stated plan).
Evidence for most rows: `A:docs/dia-feature-parity.md` (307 rows, audited 2026-09-26, 230 done), the release
notes in `A:docs/release-notes/`, and the code paths named.

### Tabs, sidebar, spaces

- shipped: Vertical sidebar or top tab strip, per window (⇧⌘S). Sidebar default 190 pt, resizable with rubber band at min and max (FACT: `A:docs/dia-spec.md:667`).
- shipped: Pinned tiles ("Top Apps"), 41 pt tall, 6 pt apart; folder tiles that hold several pins (FACT: `A:docs/dia-spec.md:150-151`; 0.2.40 notes).
- shipped: Arc-style pinned rows above the tabs, pinned groups, nested folders, arranged in any order, synced (FACT: `A:docs/release-notes/0.2.40.md`).
- shipped: Tab groups. Dropping a tab on a tab makes a group, auto-named with a deterministic heuristic, no AI (FACT: `A:apps/browser/src/store/groupNames.ts:70`).
- shipped: Live folders: GitHub and Bitbucket pull requests, Google Drive, Notion and Confluence documents, and calendar meeting groups with countdowns (FACT: `A:apps/browser/src/live/`, `A:apps/browser/src/live/net.ts:15-22`).
- shipped: Clean Up Tabs (⌥⌘K) into "Recently Cleaned", kept a week; Arc's "Clear" above unpinned tabs; Tidy for pins (FACT: `A:docs/dia-spec.md:276-291`; 0.2.40 notes).
- shipped: Rename tab, emoji icon, mute per site, multi-select, Search Tabs (⇧⌘A), ⌃Tab switcher, ⌘1 to ⌘9 (FACT: parity §2).
- shipped: Profiles with their own logins, history, extensions and colour; swipe between them; dots in the footer. Profiles can share another profile's data (FACT: parity §5).
- shipped: Auto-hide sidebar (⌘S) with an edge peek; toolbar hides while scrolling (FACT: parity §4).
- planned: Arc-style spaces that share one profile. Today a space is a profile. Arc import turns each Arc space into its own profile, so users must sign in again in each (FACT: issue #50, open, with 3 user reports).
- planned: Air Traffic Control (issue #26), shared Top Apps across profiles (issue #279).

### Navigation and command bar

- shipped: Command bar (⌘L) anchored over the URL field, no scrim; history (frecency), bookmarks, open tabs, inline autocomplete, calculator, "doc.new and 16 friends" (FACT: parity §7; `A:README.md:64`).
- shipped: !bangs (Helium's list, refreshed at most once a day from `services.helium.imput.net`) (FACT: `A:packages/shell/ios/ShellModule.swift:21`; 0.2.40 notes).
- shipped: Extensions and actions in the command bar; ⌘T lists open tabs; opt-in Arc behaviours (⌘L in the middle, new tab opens the bar) (FACT: 0.2.40 notes).
- shipped: Dia breadcrumb URL (host only), hover reveals full URL, Show Full URL (FACT: `A:docs/dia-spec.md:647-661`).
- shipped: Two-finger swipe back and forward with its own UI; hold Back for history; find, zoom; clean-link copy; Copy as Markdown; text-fragment "quote link" (FACT: parity §8).
- shipped: Search inside Settings with fuzzy match (FACT: 0.2.40 notes).

### Split view, Peek, small windows

- shipped: Split view up to 3 panes, side by side or stacked, by dragging a tab onto the page (FACT: `A:README.md:33-36`; `A:docs/dia-spec.md:769-810`).
- shipped: Little Ardia (⌥⌘N), a small window with one page and no sidebar, with a profile picker (FACT: `A:README.md:58`).
- shipped: Peek. Shift-click (or ⌥-click) opens a link in a small window over the page; ⌘O promotes it to a tab; a Peek is never saved, synced or kept in Recently Closed (FACT: 0.2.40 notes; `A:engine/patches/chromium-temporary-tab-restore-hook.patch`).
- planned: 4 panes (issue #332).

### Import, sync, profiles

- shipped: Import from Chromium-family browsers (Chrome, Edge, Brave, Opera, Vivaldi, Helium, Island, Dia), Arc, Firefox, Zen, Safari (direct with Full Disk Access, or its export zip), bookmark HTML and password CSV (FACT: `A:packages/import/README.md:8-36`).
- shipped: Arc import of spaces, pinned tabs, folders, live folders, split views, custom names, emoji icons and themes (FACT: `A:packages/import/ios/Core/ArcSidebar.swift:9-60,132-137,198,221-254`).
- partial: Dia sidebar import (open and pinned tabs over AppleScript; Dia's SQLCipher `tabs.db` is not read) (FACT: `A:packages/import/README.md:28-29`).
- shipped: End-to-end encrypted sync through a folder (iCloud Drive by default): settings, profiles, themes, bookmarks, 90 days of history, open tabs per device, pins, passwords, Web Store extensions (FACT: `A:docs/sync.md:224-307`).

### Privacy and blocking

- shipped: Full uBlock Origin (MV2) bundled from the signed app bundle, with cookie-banner lists; restricted from the Web Store and other extensions' pages (FACT: `A:docs/engine-build.md:29-30,232-234`).
- shipped: Helium's privacy patches: Google services stripped, Safe Browsing compiled out, fingerprint noise (canvas, audio, CPU cores), HTTPS-First, automatic Secure DNS (FACT: `A:docs/engine-build.md:509-516`).
- shipped: Component updater limited to security components (CRLSet, PKI Metadata, SSL error assistant), with an allowlist of request fields (FACT: `A:docs/engine-build.md:52`).
- shipped: Web Store installs and extension updates go straight to Google, undoing Helium's proxy (FACT: `A:docs/engine-build.md:50-51`).
- shipped: Crash reports and usage stats opt-in (FACT: `A:apps/browser/src/telemetry/copy.ts:1-25`).
- beta: A daily "opened today" count, always on, no persistent ID (FACT: 0.2.41-nightly.3 notes; `A:docs/growth.md:137-145`).

### AI assistant

- None, by the owner's decision. 59 Dia AI rows are deferred on purpose (FACT: `A:AGENTS.md:53-54`; `A:docs/dia-feature-parity.md:20-28`).

### Agent

- None built in. Outside agents can drive the browser with the `ardia` command (see "Agents and AI").

### Extensibility (CLI, MCP, API, extensions, mods)

- shipped: `ardia` CLI (Python 3.13 + pydoll over a token-gated DevTools socket): `exec`, `skills install` for Codex, Claude Code, Cursor and OpenCode, and `scripts` for userscripts. Off by default (FACT: `A:docs/cli.md:1-37`; `A:apps/browser/src/store/settings.ts:148`).
- shipped: Userscripts in TypeScript or JavaScript, Violentmonkey-compatible, bundled with esbuild into an unpacked "Ardia Scripts" extension that may only hold content scripts (FACT: `A:docs/cli.md:76-176`; `A:docs/engine-build.md:54`).
- shipped: AppleScript dictionary (windows, tabs, profiles, `execute javascript`) and a Raycast extension (FACT: `A:apps/browser/macos/Ardia-macOS/Ardia.sdef`; `A:extras/raycast-ardia/`).
- shipped: Chrome Web Store extensions with popups, side panels, commands; native messaging for password managers (user-test pending) (FACT: parity §15).
- not present: MCP server, plugin or boost store.

### Other

- shipped: Picture in Picture restyled as Dia's, with auto-PiP on tab switch, ±10 s buttons and a "throw to a corner" gesture (FACT: `A:docs/dia-spec.md:868-966`).
- shipped: Video super-resolution on Apple silicon (FACT: `A:engine/patches/chromium-video-super-resolution.patch`, 702 lines).
- shipped: Page translation on the Mac with Apple's Translation framework (macOS 26) (FACT: `A:packages/shell/ios/TranslateModule.swift:5,50-55`).
- shipped: Docked DevTools, Task Manager, Cast, screen share with "Share this tab instead", Handoff, downloads panel with a "magnet" fly-in (FACT: parity §14, §18, §23-24).
- shipped: Liquid Glass pinned tiles and URL field on macOS 26 (FACT: `A:packages/shell/ios/ShellModule.swift:1724-1741`).
- shipped: Sparkle updates with stable and nightly channels; the release notes open in a tab after an update (FACT: `A:docs/releasing.md:32-73`).
- beta: Open a page in WebKit (per-site rule) so FairPlay DRM such as Netflix plays (FACT: 0.2.41-nightly.2 notes; `A:apps/browser/src/lib/engines.ts`).
- blocked: Widevine (Google has not signed Ardia's CDM host) and iCloud Keychain passkeys (Apple has not granted the browser entitlement) (FACT: `A:README.md:82-84`; `A:docs/releasing.md:158-160`).

## UI, look, and feel

### Layout (Dia's numbers, matched)

All from `A:docs/dia-spec.md` (measured from Dia 1.49.1 to 1.53, FACT as a record of what Ardia measured).

- Window: sidebar 190 pt by default; traffic lights centred about (24.75, 26.75) (lines 10-11, 667-673).
- Content card: starts at the sidebar's width; inset top 6, right 7, bottom 7; radius 10 (lines 84-89).
- Toolbar inside the card: 41 pt tall; glyphs SF Symbols at 13 pt; hover square ~30 pt, radius 7, white 10% (lines 91-99).
- Sidebar rows: 34 pt tall on a 37 pt pitch, inset 6; favicon 16 pt at x 15; title at x 39; titles fade at the trailing edge instead of an ellipsis (lines 173-177).
- Pinned tiles: 41 pt tall, 6 pt apart, radius ~10, resting hairline 0.5 pt white 0.14 (lines 150-152).
- The selected pinned tile is themed from its favicon: a colourful icon gets a blurred copy of itself as fill and a 3 pt ring; a one-colour icon gets a flat fill and a white template icon (lines 153-171). This is Dia's best small touch (INFERENCE).
- Panels from the address field share one grid: inset 16, radius 12, rows 32 tall, 20 pt icon slot (lines 130-145).
- Top strip: tabs 173 wide on a 177 pitch; the selected tab joins the card with concave flares of radius 15 (lines 703-731).

### Visual language and materials

- Window: a behind-window `NSVisualEffectView` with private material raw value 29 in dark and 13 (`.hudWindow`) in light, then a base tint (black 0.4 dark, white 0.8 light), then a vertical profile-colour gradient at alpha 0.5 dark / 0.75 light whose bottom stop is the tint with HSL lightness +0.25 (FACT: `A:docs/dia-spec.md:27-57`; `A:packages/shaders/ios/WindowBackdropView.swift:400-467`).
- Content card fill: #121212 at 0.5 (dark) or white at 0.7 (light), so the blur shows at half strength (FACT: `A:docs/dia-spec.md:52-53,503-505`).
- Custom Arc-like themes: up to three colours mixed in OKLab, grain multiply-blended (default opacity 0.1), optional pass-through blur (FACT: `A:packages/shaders/ios/WindowBackdropView.swift:5-11,121-160`; `A:README.md:62`).
- Liquid Glass (`NSGlassEffectView`) for pinned tiles and the URL field on macOS 26, tinted 15% toward the profile colour (FACT: `A:apps/browser/src/components/glass.tsx:7-9`).
- Uses private API: material 29 and `CAFilter` "gaussianBlur" via `NSClassFromString` (FACT: `A:packages/shaders/ios/PowerUpView.swift:38-42`). Both can break on a macOS update (INFERENCE).

### Typography

- SF system font throughout. 12 pt and 13 pt dominate (127 and 95 uses), then 11, 11.5, 15 (FACT: grep of `fontSize` in `A:apps/browser/src/components`).
- Tab titles 13 to 14 pt; top-strip titles 12 pt regular; profile name 13 pt semibold (FACT: `A:docs/dia-spec.md:173-174,720,674`).
- Title colours: unselected white 0.78 (dark) / black 0.68 (light); selected 1.0 (FACT: `A:docs/dia-spec.md:176`).

### Colour and themes

- Dia's asset-catalog tokens are copied as a table: hover white 0.16 / 0.55, pressed 0.31 / 0.70, selected primary black / white, and so on (FACT: `A:docs/dia-spec.md:405-429`).
- Each profile has a colour; the window tint, New Tab band, edge light and profile name all derive from it (FACT: `A:docs/dia-spec.md:48-51,394,677`).
- New Tab "power-up" band and halo: Metal shaders rebuilt from Dia's disassembled metallib (FACT: `A:README.md:156-195`; `A:packages/shaders/ios/PowerUpView.swift`).

### Motion (exact numbers)

Ardia converts every spring with Apple's convention: stiffness = (2π / response)², damping = 4πζ / response,
mass 1 (FACT: `A:apps/browser/src/components/layout/dockMotion.ts:12-15`;
`A:apps/browser/src/components/layout/swipeMotion.ts:19-21`; `A:docs/dia-spec.md:205`).
"Dia measured" is Ardia's record of Dia, taken from 60 to 240 fps screen recordings and, for some rows,
disassembly of Dia's binary (FACT that Ardia recorded these; their accuracy is CLAIM).

| Interaction | Dia measured | Ardia constant (file) | Spec lines |
|---|---|---|---|
| Tab hover card, show | Delay 0.5 s (or 0.1 s by a flag), 0 s if a card is already up. Opacity 0→1 over 0.10 s, cubic-bezier(0.25, 0.46, 0.45, 0.94). Scale 0.92→1, spring response 0.25 s, ζ 0.75. Anchored at the top-left corner. Starts from current values, so it is interruptible. | Same; show delay 500 ms, leave delay 160 ms, aim 200 ms. Peak scale 1.0022 at 180 ms, settled by 340 ms (`sidebar/hoverMotion.ts:6-11`, `sidebar/hover.ts:10-12`) | 196-217 |
| Tab hover card, hide | Opacity →0 over 0.10 s, same curve; scale →0.92, spring response 0.2 s, ζ 0.6. Row to row: the card jumps, no glide. | Same | 206-210 |
| Open a tab | New row appears in place at once, already selected. Rows below slide down one pitch, drawn under the new row. | `sidebar/listMotion.tsx:10-13` | 219-224 |
| Close a tab | Row drops its selected fill at once and fades out in place: 0.10 s, cubic-bezier(0, 0, 0.58, 1). Rows below slide up: 0.14 s, cubic-bezier(0.25, 0.1, 0.25, 1) (fits a spring ω≈40 rad/s, ζ 0.9). Hover follows the final layout at once. | SLIDE_MS 140, FADE_MS 100, same curves | 225-238 |
| Hide or show sidebar (Dia, 240 fps) | One spring both ways: response 0.215 s, ζ 0.79. 90% of travel in 100 ms, 1 to 2 pt overshoot at ~0.15 s, at rest ~0.27 s. The page is resized every frame. | DOCK_SPRING (0.215, 0.79) (`layout/dockMotion.ts:3`) | 240-253 |
| Arc edge peek, in | Panel slides from past the edge, no fade: spring response 0.185 s, ζ 0.77; 93% in 66 ms, 1.5% (3.5 pt) overshoot at ~0.12 s, rest ~0.22 s. Panel inset 5 pt, 227.5 pt wide. | ARC_PEEK_SPRING (0.185, 0.77) (`layout/dockMotion.ts:5`) | 260-267 |
| Arc edge peek, out | Ease-in-out over ~150 ms. | ARC_PEEK_OUT_MS 150, easeInOutCubic (`layout/usePeek.ts:17-18`) | 267 |
| Arc hide docked sidebar | Ease-out cubic, 100 ms. Docking from the peek is instant. | ARC_HIDE_MS 100 | 268-271 |
| Dia-style edge peek | not recorded | SLIDE_MS 180, ease-out cubic; hide delay 120 ms (`layout/usePeek.ts:5-6`) | n/a |
| Command bar opens from the URL field (Dia 1.52) | The panel grows out of the field's box: 63%, 82%, 92%, 95%, 99% per 60 fps frame, an exponential ease-out of ~130 ms. Content does not move; the growing shape uncovers it. Text keeps its exact x and baseline. | GROW_MS 130, `Easing.out(Easing.exp)` (`CommandPanel.tsx:30-31`) | 358-367 |
| New Tab bar entrance (1.49) | Elevation spring 0→10 mm, response 0.7, ζ 1.0; scale 0.99 + 0.01·mm/10; starts +0.25 s; skipped with Reduce Motion. In 1.50 it no longer runs (scale 1 from the first frame). | n/a (matches 1.50) | 302-307, 396-400, 500-502 |
| New Tab power-up band (1.50) | Shader speed 1.0 (t = 0.75·time + 0.45); peaks 0.10–0.20 s; head passes the bar ~0.3 s; plateau 0.4–1.2 s; linear fade to nothing at ~3.25 s. Layer blur radius 24. 60 fps, stops at T = 3.75 s. | `PowerUpView.swift:33-37,123-125` (60 fps, pauses at 3.75 s; paused under Reduce Motion, line 90) | 377-403, 581-586 |
| New Tab halo (1.50) | Delay 0.18; sweep = 1.25·(1 − 2^(−10t)). Lit arc starts at the bottom at 0.225 ± 0.007 s, sides peak ~0.30 s, top at 0.376 ± 0.007 s, top gone at 0.529 ± 0.006 s; faded by 1.725 s. | HaloView, 60 fps, stops at 2 s (`PowerUpView.swift:143-148,187-189`) | 588-610 |
| New Tab area light (1.49, now removed) | intro delay 0.05 s, intro 0.4 s; 30 fps display link while key; breathing on a 6 s cycle; stops at T ≥ 60 s. | Was approximated as quartic ease-out 1.1 s and ±7% intensity on a 5.5 s sine (`A:README.md:186-190`) | 309-338 |
| New Tab logo rise (Ardia's own mark) | n/a | Springs: sun (0.56, 0.9) after 250 ms, back hill (0.46, 0.84) after 170 ms, front hill (0.42, 0.76) after 80 ms; drift (0.6, 1.0) (`NewTabPage.tsx:28-35`) | n/a |
| Profile (space) swipe | Tracks at −0.5 × scroll delta. Rubber band 255·(1 − 1/(0.15·x/255 + 1)). Release ≥ 5 pt/s goes to the next page. Settle: 0.25 s critically damped spring (0.4 s without Dia's flag), sampled at 1/240 s. Page-detent haptics. Mouse wheel: deltas within 0.049 s add up, page once the sum passes 1 pt, then ignore 0.25 s. | WHEEL_BURST_MS 49, WHEEL_COOLDOWN_MS 250 (`layout/profilePager.ts:19-20`); rubber band coefficient 0.15 (`layout/swipeMotion.ts:5-10`) | 507-509, 527-547 |
| Space switcher dots | 6 pt dots, 12 pt per item, up to 7 (84 pt) then scroll with edge dots scaled 0.75–1; alpha 0.85 selected, 0.4 hovered, 0.2 otherwise. | Implemented (`profiles/ProfileDots.tsx`) | 548-555 |
| Tab loading spinner (1.50) | Rotation 0 → −2π (clockwise), 1.88 s, linear, repeating. 12×12 pt, ring 1.5 pt, strokeEnd 0.72. | Implemented in shell | 510-516 |
| Tab row background change (1.50) | Fades 0.3 s ease-out. | n/a | 517 |
| Sidebar scroll-edge hairline | 1 pt line under the pinned tiles fades in or out over 0.1 s on the hover-card curve when the list scrolls. | `sidebar/ScrollEdge.tsx` | 689-695 |
| Top-strip group expand / collapse | One spring both ways: response 0.30 s, ζ 0.82 (~1% overshoot, within 1% at ~0.3 s). Members slide out of the first slot and fade in by half-way. "–" on a collapsed group's tab fades it in ~0.12 s. | GROUP_SPRING (0.3, 0.82), TUCK_FADE_MS 120 (`layout/stripGroups.ts:16-17`) | 752-767 |
| Drag a tab toward a split | Targets appear when the pointer is 26 pt below the strip; slide in ~0.11 s; grow to 322×532 over ~0.12 s, no overshoot. The target under the dragged card grows to 362×600 and leans 43% toward the pointer. Let go away from a target: a window grows from the card in ~0.2 s. Over another strip: the card becomes a pill in ~0.05 s. | ZONE_SLIDE_MS 110; ZONE_SPRING stiffness 987, damping 56.5 (= response 0.2, ζ 0.9) (`layout/SplitChrome.tsx:171-172`); pill 30 ms then 60 ms into the card; new window grows 0.2 s then fades 0.1 s | 769-810 |
| Reorder tabs in the strip | The neighbour slides into the gap: 91% in 43 ms, 97% in 60 ms, done ~76 ms (critically damped, ω ≈ 90 rad/s). The dragged tab tracks the pointer within a frame. | `layout/stripReorder.ts` | 811-821 |
| Press on a row (Ardia only) | Dia has no pressed state for the selected tab. | Scale 0.99 and opacity 0.95; 80 ms in, 180 ms out, ease-out cubic; no scale with Reduce Motion (`sidebar/PressFeedback.tsx:6-7`) | 181-183 |
| Picture in Picture | Appears ~125 ms after the tab switch, no fade. Hover: black scrim 35%, fade in over 200 ms ease-in-out. Close: fade ~100 ms ease-out. Back to tab: fade ~70 ms. | Same: 200 ms (measured ~190), 100 ms, 70 ms (`ArdiaCorePictureInPicture.mm`) | 868-906 |
| Throw the PiP window (Dia 1.53 binary) | Fling if release speed > 350 pt/s (drag) or last scroll delta > 6 pt (×90 /s). Nearest screen corner within ±45° of the throw wins; 10 pt inset. Spring response 0.9 s, ζ 0.9: 50% at 0.23 s, 90% at 0.49 s, 99% at 0.74 s, ≤ 0.15% overshoot, settles within 0.2 pt. Tilt 0.005 × speed while dragged. | Same thresholds and spring; no tilt; 28 pt edge stash (`ArdiaCorePiPThrow.h`) | 915-966 |
| Other Ardia timings | n/a | Toolbar auto-hide: hide 150 ms ease-out quad, show 200 ms ease-out cubic (`AutoHideToolbar.tsx:16-19`). Group fold 150 ms, cubic-bezier(0.2, 0.9, 0.3, 1) (`sidebar/Fold.tsx:4-5`). Peek: grow spring (0.22, 0.9) without overshoot, close 150 ms, expand to tab 170 ms (`peek/PeekOverlay.tsx:19-21`). Tooltip delay 500 ms, fade 100 ms (`TooltipAbove.tsx:6-7`). ⌃Tab switcher shows after 140 ms (`sidebar/switcher.ts:6`). Strip lift 150 ms (`layout/TopTabStrip.tsx:79`). Settings search highlight: 120 ms in, 900 ms hold, 700 ms out (`settings/controls.tsx:353-355`). | n/a |

Animation plumbing: React Native's `Animated` (no Reanimated on macOS), 94 animations on the native driver
and 22 on the JS thread (FACT: grep of `useNativeDriver` in `A:apps/browser/src`). On 2026-10-01 it was 4 native
and 86 JS (FACT: `git show 2713787d:docs/architecture-review.md`, recommendation 6).

### Signature interactions that feel great (from the spec and notes)

- Pinned tile selection themed from the favicon (blurred-icon ring) (`A:docs/dia-spec.md:153-171`).
- Hover cards that grow from the corner nearest the row and jump row to row without re-animating (lines 196-217).
- Tab close: the row fades in place while rows below slide over it; hover follows the final layout at once (lines 225-238).
- Drag a tab onto the page: split targets slide in, grow, and lean toward the pointer (lines 776-800).
- PiP throw to a corner with a velocity-seeded spring and pointer warp (lines 915-949).
- Profile swipe with rubber band and detent haptics (lines 527-547).
- Peek on shift-click; the page can become a tab without reloading (0.2.40 notes).
- After an update, the release notes open in a tab (`A:docs/releasing.md:32-36`).
- Launch shows a saved picture of the last window, then swaps to the live window "without a dark moment" (0.2.40 notes; `A:packages/ardiacore/ios/ArdiaCoreEarlyWindow.mm:259,654`).

### Things that feel bad, or are risky

- Tab switch is slower than Helium: 40 ms vs 8.5 ms on 2026-10-16, cut to 10–16 ms on 2026-10-17. About 25 ms was the JS and React round trip (FACT: `A:docs/perf/vs-browsers.md:10-60`).
- Memory with 20 tabs is 29% above Chrome and 5% above Helium (1,183 MB vs 919 MB and 1,125 MB). At 1 tab it is the lowest of the four (290 MB vs Helium 375 MB) (FACT: same file, results table, 2026-10-16).
- Spaces are profiles: Arc users lose shared logins after import (FACT: issue #50).
- Open bugs that touch feel: scrolling drops frames while the vertical sidebar shows (#333); closing a tab skips unload handlers, so Discord logs out (#342); launch flicker (#317); text blurry on an external monitor (#151, closed).
- macOS 27 stopped honouring the drag-to-window hand-off, so Ardia moves windows itself (FACT: 0.2.40 notes). Custom chrome breaks on OS updates (INFERENCE).
- Many Arc habits ship "behind a switch that's off" (FACT: 0.2.40 notes). That grows the settings surface (INFERENCE).

## Architecture

### How it got here (all FACT, from release notes and docs)

| Date | Version | Change |
|---|---|---|
| 2026-09-25 | 0.1.0 | CEF 154 (Chrome style runtime) + ungoogled-chromium, React Native shell (`A:docs/release-notes/0.1.0.md`) |
| 2026-10-01 | n/a | Architecture review: "Most of our fighting is with CEF, not with Chrome"; 42% of the week's app and engine commits touched the CEF seam (`git show 2713787d:docs/architecture-review.md:10-21`) |
| 2026-10-02 | 0.2.22 | "Ardia moves out of CEF and into Chrome's own framework" (ArdiaCore) |
| 2026-10-09 | 0.2.31 | Last of CEF removed; plain Chromium 154.0.8037.97 |
| 2026-10-19 | 0.2.38 | Chromium 155, official build with ThinLTO and PGO |
| 2026-10-23/24 | 0.2.40 | Engine rebased from ungoogled-chromium onto Helium 0.19.4; app relicensed GPL-3.0 |
| 2026-10-25 | nightly | Per-site WebKit engine; daily ping; CI release workflow and x64 engine CI added |

### Process model

- One app process is Chrome's browser process. `main.swift` calls `ArdiaCoreHost.run`, which runs `ChromeMain`
  with Ardia's `ACMainDelegate`. `NSApp` is Chrome's `BrowserCrApplication`. The React Native host (Expo's
  `AppDelegate`, Hermes JS engine) starts inside Chrome's run loop (FACT: `A:docs/agent-brief.md:17-19`;
  `A:apps/browser/macos/Ardia-macOS/main.swift`; `A:apps/browser/macos/Ardia-macOS/AppDelegate.swift:9-26`).
- Chrome's usual helpers run beside it: renderer, GPU, utility (named "Chromium Helper (...)") (FACT:
  `A:docs/releasing.md:287-292`).
- Each app window is one `ArdiaCoreWindow`, a Views-backed `NSWindow`. Each profile shown in it has its own Chrome
  `Browser`, with no `BrowserView`, tab strip or toolbar. Every tab is a real Chrome tab; its `WebContents` view is
  placed inside a React Native view (`ArdiaCoreWebView`) (FACT: `A:docs/agent-brief.md:20-25`).
- Each window gets its own React Native root view (`"main"` with a `windowId`) from one shared React host (FACT:
  `A:apps/browser/macos/Ardia-macOS/AppDelegate.swift:19-24`).
- Ardia keeps its own session file (`session.json`). Chrome's SessionService is told to ignore Ardia's browsers
  (FACT: `A:docs/engine-build.md:74`).
- This mirrors how The Browser Company built Arc and Dia on their own SDK over Chromium (CLAIM: Ardia's review
  calls it "as Dia does with ArcCore"; TechCrunch reports Arc runs on the "Arc Development Kit (ADK)").

### How React Native talks to Chromium

```
JS (apps/browser/src, Hermes)
  → Expo module (Swift: packages/ardiacore/ios/*Module.swift)
    → ObjC++ host (ArdiaCoreHost.mm, ArdiaCoreWebView.mm)
      → public/ArdiaCore.h (plain ObjC, exported from Chrome's framework)
        → ardiacore_api.mm → ac_*.mm (engine/ardiacore, compiled as //ardia/core)
          → Chrome classes (Browser, WebContents, TabStripModel …)

JS → ArdiaCoreEngineBridge (dlsym) → ac_<domain>_<verb>(profile_dir, args_json, reply, ctx)
     (engine/chromium, compiled as //chrome/browser/ardia: passwords, autofill, history, bookmarks,
      extensions, zoom, search engines, cookies, site settings …; JSON in, JSON out, UI thread only)

Events back: ArdiaCore*Delegate → -emit:payload: → Expo events → JS store (zustand)
Page ↔ app: page_script.js (1,138 lines) runs in the page's main world of every http(s) and file frame;
            post(kind, json) crosses a Mojo page channel to ArdiaCoreWebView
```

Sources (FACT): `A:docs/agent-brief.md:94-109`; `A:docs/engine-build.md:253-277`;
`A:engine/ardiacore/src/ardia/core/renderer/ac_content_renderer_client.cc:106-116`;
`A:packages/ardiacore/ios/CefModule.swift:8` (seven event streams, about 120 functions in that one module).
On 2026-10-01 the bridge had 264 native functions and 20–50 events per page load (FACT: architecture review §D).

### Which UI lives where

| Surface | Lives in | Notes |
|---|---|---|
| Sidebar, tabs, pinned tiles, groups, live folders | React Native (`A:apps/browser/src/components/sidebar/`) | Native primitives for symbols, shadows, menus, drag regions (`A:packages/shell/ios`) |
| Toolbar, URL breadcrumb, command bar, suggestions | React Native + pure TS (`A:packages/core`) | History and bookmarks come from Chrome through `ac_*` calls |
| New Tab page | React Native + Metal (`PowerUp`) | |
| Settings, import wizard, onboarding, downloads, history page | React Native windows | Passwords, autofill and extensions panes call Chrome's services directly; "No chrome:// page is scripted" (`A:docs/agent-brief.md:26-29`) |
| Menu bar, shortcuts, window chrome, profile swipe pager | Native Swift / ObjC (`A:packages/shell`, `A:packages/ardiacore/ios/ACSwipe.mm`) | Pager drives `Animated` values |
| Window backdrop | Native: `NSVisualEffectView` + CALayers; Metal for custom gradient and grain | |
| Web page | Chrome's `WebContentsViewCocoa` inside `ArdiaCoreWebView` | |
| Permission prompts, password save, address save, extension install prompt, device chooser, Cast picker | Hooks in Chrome (`g_ardia_*`) hand them to React Native components (`components/site/Prompts.tsx`) | `A:docs/engine-build.md:39-45,114-139` |
| Autofill dropdown, passkey sheet, extension popups, docked DevTools, context menus | Chrome's own views or panels, attached to Ardia's window | `A:docs/ardiacore-spike.md:62-74` |
| PiP window | Chrome's `VideoOverlayWindowViews`, subclassed and restyled (`ArdiaVideoOverlayWindow`) | `A:docs/engine-build.md:83` |
| Find bar | React Native; Chrome's `FindTabHelper` searches headlessly | `A:docs/ardiacore-spike.md:71` |

### Engine integration: fork, patches, layers

- **Base:** Chromium tag fetched at depth 1, then Helium's series and helium-macos's applied with no fuzz, minus 15
  skipped patches (password manager off and its autofill link, the mDNS removal, Memory Saver, keychain rename,
  product dir, four Sparkle patches, crash dialog, three build-setup patches, Helium's signing) (FACT:
  `A:engine/patches/build/03-helium.py:46-65`; `A:docs/engine-build.md:433-460`).
- **Substitutions:** Helium's domain substitution (minus Web Store hosts), name substitution, then Ardia's own
  rename pass that fails if any string still says Helium or imput (FACT: lines 464-482).
- **Patches:** 60 patches, 492 hunks, 9,533 lines, touching 205 files, 4 of them new (84 under `chrome/browser`, 93 under `chrome/`)
  (FACT: count of `A:engine/patches/*.patch`). One concern per patch; `series` gives order (FACT:
  `A:engine/patches/series`).
- **Scripted hooks:** `engine/ardiacore/apply.sh` inserts 46 marker-guarded hooks into 46 Chrome files, 44 of which no patch touches;
  `--check` reports drift (FACT: `A:engine/ardiacore/apply.sh`, 1,635 lines; `A:docs/engine-build.md:242-251`).
- **Layers (new files only):** `//chrome/browser/ardia` (about 11,000 lines) and `//ardia/core` (about 17,100 lines of source; about 18,700
  counting `apply.sh` and the rest of `engine/ardiacore`), copied in
  by `apply.sh` (FACT: line counts; `A:docs/engine-build.md:253-277`).
- **Hook style:** a `g_ardia_*` function pointer declared once in a shared header that both sides include, so a
  signature drift is a compile error (FACT: `A:docs/engine-build.md:114-121`).
- **Proof the series reproduces the tree:** `series.py check` applies the whole series strictly to a saved base and
  compares every touched file byte for byte (FACT: lines 279-314).
- **Compared with rac (INFERENCE):** rac has about 180 patches and 871 hunks across 217 files, about 320 hunks in
  `ui/views` (maintainer brief). Ardia has few: 26 hunks in 8 files with `ui/views` in the path (7 under `chrome/browser/ui/views`, mostly the PiP
  overlay and bubbles; 1 in `ui/views/style`) (FACT: count of `A:engine/patches/*.patch`), because its UI lives outside Chrome. Its cost moves
  elsewhere: Chrome internals such as a `Browser` without a `BrowserView`, which Chrome does not support.

### Metal shaders

- `MetalSurface` base: one `MTKView`, a full-screen triangle strip, shader source embedded in Swift and compiled at
  runtime once per class (FACT: `A:packages/shaders/ios/MetalSurface.swift:1-100`; `A:README.md:216-218`).
- Frame pacing: the backdrop draws on demand (`isPaused`, `enableSetNeedsDisplay`); the New Tab band runs at 60 fps
  and pauses after 3.75 s, the halo after 2 s; both pause under Reduce Motion (FACT:
  `A:packages/shaders/ios/WindowBackdropView.swift:24-25`; `A:packages/shaders/ios/PowerUpView.swift:37,90,123-125`).
  Nothing repaints continuously at rest (INFERENCE from the above).
- Provenance: rebuilt from Dia's disassembled `default.metallib` with `xcrun metal-objdump`; "only math and colour
  values are reused" (CLAIM: `A:README.md:156-197`).
- 1,527 lines in total (FACT).

### Languages and code size (lines, non-vendored, FACT)

| Area | Lines | Language |
|---|---|---|
| `apps/browser` (UI, store, scripts) | 97,898 (62,154 in `src`, non-test) | TypeScript/TSX, Swift |
| `packages/ardiacore` (app side of the engine bridge) | 28,055 | ObjC++, Swift, TS |
| `packages/core` (omnibox, suggestions, URL rules) | 14,812 | TS |
| `packages/shell` (menus, windows, updater, native views) | 10,894 | Swift |
| `packages/import` | 8,206 | Swift |
| `packages/sync` | 6,645 | Swift, TS |
| `packages/shaders` | 1,527 | Swift, Metal |
| `engine/ardiacore` + `engine/chromium` | 29,756 | C++, ObjC++ |
| `engine/patches` | 11,217 | diff, Python, shell |
| `apps/cli` | 4,929 | Python |
| `apps/site`, `apps/dashboard`, `apps/videos`, `apps/demo` | ~34,000 | Astro, TS, Remotion |

Stack versions: Expo SDK 54, react-native-macos 0.81 on the legacy architecture, no Reanimated, Metro through the
react-native-macos CLI, pnpm 11 hoisted, Turborepo (FACT: `A:README.md:202-215`; `A:docs/agent-brief.md:10-12`).
Three patched dependencies (react-native-macos, expo-modules-core, expo-constants) (FACT: `A:patches/`).
The README says react-native-macos "tops out at 0.81" (CLAIM: `A:README.md:202`). That is out of date:
react-native-macos 0.83.0 shipped 2026-09-30 (FACT: github.com/microsoft/react-native-macos/releases). Ardia pins
0.81.9 (FACT: `A:apps/browser/package.json:25`).

## Data and storage

| What | Where | Format, protection |
|---|---|---|
| Chrome profiles (cookies, history, passwords, autofill, bookmarks, extensions, prefs) | `~/Library/Application Support/com.ardia.browser/Chromium/` (`Default`, `Profile <id>`) | Chrome's SQLite and JSON; secrets encrypted with the "Ardia Safe Storage" key in the login keychain (FACT: `A:docs/releasing.md:268-273`; `A:docs/engine-build.md:42`) |
| App state: windows, tabs, pins, groups, settings | `.../com.ardia.browser/session.json` and siblings (`downloads.json`, `bookmarks-cache.json`, `live.json` …) | Plain JSON, saved 800 ms after a change (FACT: `A:apps/browser/src/lib/persist.ts:16`) |
| Launch picture of the last window | `launch-picture-<window>.png`, `launch-layout.json` | Plain PNG of the active tab's page (FACT: `A:packages/ardiacore/ios/ArdiaCoreEarlyWindow.mm:259,535,654`). Page content on disk unencrypted (INFERENCE) |
| Live folder tokens (GitHub, Notion, Bitbucket, Confluence, Google) | macOS Keychain generic passwords | (FACT: `A:packages/shell/ios/Keychain.swift:51`; `A:apps/browser/src/live/sources.ts:16`) |
| Sync key | Keychain item "Ardia Sync Key", this device only, not iCloud Keychain | (FACT: `A:docs/sync.md:81-85`) |
| Sync local state | `sync.json`, `sync-state.nns` (sealed), `sync-journal.nns` | AES-256-GCM (FACT: `A:docs/sync.md:377-388`) |
| Sync remote | `~/Library/Mobile Documents/com~apple~CloudDocs/Ardia Sync/<chain>/<scope>/<random>.nns` | See below |
| CLI control token | `Chromium/ArdiaControl.json`, mode 0600, deleted on stop | (FACT: `A:docs/cli.md:190-195`) |
| Userscripts | `Scripts/` (records, generated extension, generation counter, status) | (FACT: `A:docs/cli.md:138-176`) |
| Telemetry queue, daily ping state, kill-switch cache | `telemetry-queue.json`, `telemetry-daily.json`, `switches-cache.json` | Plain JSON (FACT: grep of file names) |

There is no Crashpad. Crash signatures, if sharing is on, come from macOS's own reports in
`~/Library/Logs/DiagnosticReports` (FACT: `A:docs/engine-build.md:9`; `A:packages/shell/ios/AppModule.swift:555`).

### iCloud Drive sync, end to end (FACT unless marked: `A:docs/sync.md`)

- **No server, no account, no Apple entitlement.** Every Mac reads and writes sealed files in a folder the user
  picks. The default is a plain folder in iCloud Drive. Dropbox, a NAS or a USB drive work the same (lines 1-9).
- **Keys:** 24 BIP-39 words encode 256 bits from `SecRandomCopyBytes`. HKDF-SHA256 derives `file-key`
  (AES-256-GCM) and `name-key` (HMAC-SHA256 for folder names). No password stretching, since the phrase already has
  256 bits (lines 66-95). Pairing a second Mac means typing the phrase; a Recovery Kit is a PDF, text sheet and QR.
- **File format:** `"NNS1" | nonce(12) | ciphertext | tag(16)`. The AAD binds the file to `chain/scope/file`, so a
  file can't be moved or renamed. Plaintext is padded to 1 KiB steps and never compressed, against CRIME-style
  probing (lines 38-46, 96-130).
- **Write model:** files are immutable, each under a fresh random name, written whole then moved in under
  `NSFileCoordinator`. Two Macs never write the same file, so iCloud never sees a conflict. A local sealed journal
  replays a batch after a crash (lines 117-130).
- **Merge:** per-record last-writer-wins by hybrid logical clock; tombstones for deletes; three-way base; version
  vectors; fractional positions for order (lines 143-222). Snapshots compact a scope past 40 files; tombstones are
  kept 45 days (90 while a gap exists) (lines 172-215).
- **What it hides:** contents, names and kinds. **What it leaks:** profile and device counts, write times and
  sizes to 1 KiB, and that it is Ardia data (lines 47-50).
- **Passwords:** sync reads Chrome's `Login Data` directly with the importer's decryptor, and writes through
  Chrome's API. Passwords do cross into JS (lines 307-326; `A:packages/import/README.md:60`).
- **Cycle:** every 15 s, 3 s after an edit, and on Sync Now (lines 377-388).
- **Unverified:** "A real two-Mac run over iCloud Drive" is listed as "Left for a person"; tests use a temp folder
  (lines 452-457). Four open security issues touch sync: #299-#302 (FACT: issues API).

### What leaves the machine, by default

| Request | When | Carries | Evidence |
|---|---|---|---|
| Sparkle update check to `ardia.dev/appcast.xml`, 302 to GitHub | Launch (if 8 h passed) and every 8 h | Version in the User-Agent; `first=1` on a copy's first check. nginx mirrors a count `{version, first}` to the collector, IP not stored | FACT: `A:apps/browser/macos/Ardia-macOS/Info.plist` (`SUScheduledCheckInterval` 28800, `SUAutomaticallyUpdate` true); `A:docs/growth.md:68-100` |
| Kill-switch file `ardia.dev/switches.json` | Once per launch, only if update checks are on | Nothing: no cookies, no ID, no query | FACT: `A:docs/kill-switches.md:27-34` |
| `daily_active` ping | Once per UTC day, ~30 s after launch, even with sharing off | Version, channel, macOS major, arch, first/daily/weekly/monthly flags; fresh random UUID per day; geo-IP disabled | FACT (nightly 0.2.41-nightly.3 only): `A:docs/growth.md:137-145`; `A:apps/browser/src/telemetry/copy.ts:13-15` |
| Helium's !bang list from `services.helium.imput.net/bangs.json` | At most once a day, never at launch, with ETag | Plain GET | FACT: `A:packages/shell/ios/ShellModule.swift:21`; 0.2.40 notes |
| Google: Web Store, extension updates, component updater (security components only), extension malware kill-switch | As Chrome does | Allowlisted request fields for components; IP visible | FACT: `A:docs/engine-build.md:50-53` |
| Opt-in telemetry (off by default) | Batched, flushed every 30 s | Random install ID, counts, timings, cleaned error stacks, crash signatures | FACT: `A:apps/browser/src/telemetry/copy.ts:27-74`; `A:apps/browser/src/telemetry/client.ts:15-17` |

The website runs first-party analytics with session replays (rrweb, inputs masked, kept 30 days) (FACT:
`A:docs/growth.md:110-135,183`). An AI agent ("hekuto") reads the telemetry tables through a Composio connection
(FACT: `A:docs/growth.md:156-157`), so a third party sits in that read path despite "No third parties" (INFERENCE).
Before 2026-09-30 the site and the app's opt-in telemetry went to PostHog Cloud EU, a third party. Copies on 0.2.17
or earlier still post their opt-in events there, and nobody reads them (FACT: `A:docs/growth.md:5,160-164`).

## Agents and AI

- **No built-in assistant or agent.** The owner decided "No AI features" (FACT: `A:AGENTS.md:53`). No models, no
  providers, no local models, no prompt-injection work inside the browser.
- **Outside agents drive it through the `ardia` command.** Python 3.13 with pydoll 3.0 over the Chrome DevTools
  Protocol. Not in the app bundle; the app installs it from a GitHub release, pinned by a SHA-256 baked into the
  signed bundle. Off by default; turned on in onboarding or Settings ("Let the ardia command control Ardia") (FACT:
  `A:docs/cli.md:1-16,202-232`; `A:apps/browser/src/store/settings.ts:148`).
- **How it connects:** the app runs a DevTools server in "token mode": a new random token per start, written to a
  0600 `ArdiaControl.json`. Every WebSocket needs `?token=`, compared in constant time. `/json*` routes answer 404;
  any `Origin` is refused (FACT: `A:docs/engine-build.md:61`; `A:engine/chromium/src/chrome/browser/ardia/ac_cli_control.cc`).
- **What a token client may do:** an allowlist of exactly 70 CDP methods: target discovery and attach, DOM and
  accessibility reads, Page navigate/reload/screenshot/print, Runtime evaluate in the page's main world, Input
  (keys limited to reviewed editing commands, no clipboard, no native key events, so no app shortcuts), and
  Network body reads (FACT: `A:engine/chromium/src/chrome/browser/ardia/ac_cli_token_policy.cc:51-122,143-200`).
  The list also has `Page.addScriptToEvaluateOnNewDocument`, `Page.createIsolatedWorld`, `Target.createTarget`, and
  `Target.closeTarget`/`Page.close`, so a client can open and close tabs and plant scripts that run on each new
  document in a tab while it stays attached (FACT: same file; INFERENCE on CDP's per-session script scope).
- **What it may not do:** attach to Ardia's own windows, extension pages, chrome:// or DevTools; read local files;
  use extension isolated worlds; see `Cookie`, `Set-Cookie`, `Authorization` headers; close or crash the browser
  (FACT: `A:docs/engine-build.md:61`; `A:docs/cli.md:39-44`).
- **Page representation:** none of its own. The agent gets raw CDP: DOM, accessibility tree, screenshots, JS (FACT:
  allowlist above).
- **Permissions and safety:** one global switch, a "ardia is controlling Ardia · Stop" pill over the page, and
  token redaction in all output (FACT: `A:docs/cli.md:7-11,196-200`). There are no per-site rules, no confirmations,
  no risky-action list. The shipped `SKILL.md` asks the agent to "Ask before anything with consequences" (FACT:
  `A:apps/cli/ardia_cli/skill/SKILL.md`). A connected agent has page-script power plus input in every signed-in
  web tab, including reading authenticated responses and non-HttpOnly cookies through JS (INFERENCE).
- **Skills:** `ardia skills install --target general|codex|claude-code|cursor|opencode [--project]` (FACT:
  `A:docs/cli.md:32-35`).
- **Automations:** "daily report" helpers `history()` and `pinned()` read `session.json` and a snapshot copy of
  Chrome's History SQLite (FACT: `A:docs/cli.md:46-74`). AppleScript (`execute javascript`) and Raycast are other
  ways in (FACT: `A:apps/browser/macos/Ardia-macOS/Ardia.sdef`).
- **AI in the engineering process:** Opus subagents implement, a main session verifies, Codex reviews risky logic;
  a dev harness (`scripts/agent/ac eval`) drives hidden test instances; agents may cut releases end to end
  (FACT: `A:AGENTS.md:13-25,82-84,109-110`).

## Build, release, and engineering

- **Build systems:** pnpm + Turborepo for JS; CocoaPods + Xcode for the app; GN + autoninja for the engine (FACT:
  `A:README.md:115-150`).
- **Engine builds happen on the owner's Mac.** `~/chromium-build` on an M5 Pro: first full build 2.5 h (official,
  ThinLTO, PGO), incremental compile plus ThinLTO relink about 7 min; 45 GB of disk (FACT:
  `A:docs/engine-build.md:340-364`). One agent at a time holds a "chromium lock" (FACT: `A:docs/agent-brief.md:60-69`).
- **App and engine are decoupled.** The engine is versioned by the git tree hash of `engine/`
  (`git rev-parse HEAD:engine`). A locally built engine is attached as `ArdiaCore-<tree>.tar.xz` to the first app
  release that uses it; a CI-built engine goes to its own `engine-<tree:12>` prerelease. An app build downloads the matching prebuilt
  framework and checks its SHA-256 (FACT: `A:docs/releasing.md:23-30,251-260`). A JS-only change needs no app
  rebuild; Metro reloads it (FACT: `A:AGENTS.md:79`).
- **How 80 releases happened:** every release so far was built and signed by `scripts/release.sh` on the owner's
  Mac (FACT: the CI Release workflow's first commit is `e8ec213e` at 2026-10-25 18:14 UTC, after all 80 app
  releases). By 19:29 UTC two CI runs had succeeded, both dry runs: the publish job skipped its Tag step, which runs
  only when `dry_run` is false, and no new release appeared (FACT: Actions runs 40221031458 and 40225253957;
  `A:.github/workflows/release.yml:19-22,266-267`). A third run was in progress at 19:44 UTC. 25 of the 42 releases
  since 0.2.31 carried a new engine (25 rows in `A:packages/ardiacore/prebuilt-engines.tsv`), each an incremental
  local build (FACT, INFERENCE on the build type). The owner pre-authorized agents to release "all the way through"
  (FACT: `A:AGENTS.md:109-110`).
- **CI:** CLA and linked-issue checks, site deploy, a manual Release workflow (both arches, signs from repository
  secrets, dry run by default), and a 10-phase x64 engine build on a 3-core runner that checkpoints the tree and
  `out/` as a zstd tar artifact between 6-hour jobs, with sccache on the Actions cache (FACT:
  `A:.github/workflows/*.yml`; `A:.github/engine/x64.sh:95-138`; `A:docs/engine-build.md:403-431`). Its checkpoint
  uses `tar` with bsdtar's default format (FACT: `x64.sh:134`), which rac found drops sub-second mtimes and makes
  siso rebuild (rac's `plans/context/ci-status.md`). It also passes `--no-mac-metadata`, which drops xattrs, so
  likely no file keeps a sub-second mtime (INFERENCE). No x64 run has finished: all six on 2026-10-25 failed or
  were cancelled (FACT: Actions runs API). So the problem is unproven for Ardia (INFERENCE).
- **Signing and notarization:** Developer ID (team U5L5T3NGVV), hardened runtime with library validation, `allow-jit`
  only for renderer and GPU helpers, notarized and stapled since 0.2.1. The release launches the exported app once
  and re-verifies the signature, so nothing may write into the bundle (FACT: `A:docs/releasing.md:91-114,153-163`;
  `A:docs/engine-build.md:216-238`).
- **Update mechanism:** Sparkle 2.9.6, EdDSA-signed zip, one appcast for both channels (`<sparkle:channel>nightly`),
  monotonic build numbers, 3 items kept per channel, phased rollout available, a hidden "prewarm" first run of a
  staged update (FACT: `A:docs/releasing.md:38-73`; `A:docs/kill-switches.md:47,68-70`;
  `A:packages/shell/ios/Updater.swift:290,318-353`).
- **Release smoke test:** hidden launch over CDP, Gatekeeper, Sparkle actually updating a copy of the previous build,
  previous data opening in the new build (`carryover.sh`), rollback (`rollback.sh`) (FACT:
  `A:docs/releasing.md:185-199,277-292`).
- **Perf gate:** stable releases only, against the previous stable; native bench (launch, idle CPU and wakeups,
  memory, tab and window latency), JS bench, render census, a ratchet of counts that may only go down; plus a
  cross-browser bench against Dia, Helium and Chrome (FACT: `A:docs/perf/README.md`; `A:docs/perf/vs-browsers.md`).
- **Kill switches:** a static JSON file, at most 8 live switches, each with an owner and a removal date, on by
  default, with tests of both paths (FACT: `A:docs/kill-switches.md:7-15`).
- **Tests:** the doc's headline says 333 unit cases on 2026-10-12, but its own table sums to 361 (228 app, 32 core,
  66 + 9 sync, 26 import), so both are stale. Today there are 90 `.test.mjs` files, 11 `.test.ts` files and 13
  Swift test files; many end-to-end scripts run by hand (FACT: `A:docs/testing.md:3-11`; `find` in the clone).
- **Tracking upstream:** Helium pinned by tag and commit; step 3's `guard` stage refuses a Helium update that
  changes what a skip protects; a new Chromium needs the owner's OK and a full rebuild (FACT:
  `A:docs/engine-build.md:378-401,455-459`). Ardia adopted Helium 0.19.4.1 (released 2026-10-17) on 2026-10-23.
  Helium 0.20.1.1 (Chromium 156) shipped 2026-10-22 and is not adopted yet (FACT: helium-macos releases API).
- **Process rules:** commit straight to `main`, no git worktrees, no comments in code, issues before PRs (FACT:
  `A:AGENTS.md:26-40`). Doc drift exists: `AGENTS.md` still says Chromium 154 and "The license is Apache-2.0" (FACT: `A:AGENTS.md:3,123`).

## Strengths and weaknesses

### Strengths

- **It ships.** 80 signed, notarized app builds in 31 days, with a nightly channel, release notes per version, and an
  update smoke test that runs Sparkle for real (FACT).
- **Measured craft.** The Dia spec is the most detailed public record of Dia's motion and layout I have seen:
  springs, curves, thresholds and frame-by-frame traces (FACT: `A:docs/dia-spec.md`).
- **Honest perf work.** It publishes where it loses to Helium and Chrome and why (FACT: `A:docs/perf/vs-browsers.md`).
  Its engine patches cut idle wakeups and hold 120 Hz only during input (FACT: `A:docs/engine-build.md:69-75,140-184`).
- **Serious data safety.** Safe Storage never silently replaced; sync files sealed, immutable and authenticated;
  importer keeps cookies and cards out of JS (FACT).
- **Outside-agent access done carefully at the protocol level**: token, allowlist, web-only targets, header
  stripping, off by default (FACT).
- **Broad Arc import**, including themes and live folders (FACT).

### Weaknesses

- **React Native tax.** Tab switch and memory trail Helium; 85 pods; legacy architecture on react-native-macos
  0.81.9, with 0.83.0 available but not adopted; a dozen RN workarounds (FACT: `A:docs/perf/vs-browsers.md`; architecture review §D).
- **Fragile embedding.** Chrome does not support a `Browser` without a `BrowserView`. Each Chromium bump can break
  the 46 hooks and the CHECK relaxations (INFERENCE from `A:docs/engine-build.md:121`).
- **Spaces equal profiles**, which breaks Arc's model and its import (FACT: issue #50).
- **Privacy drift.** Since today a ping is always on; update checks are counted; Web Store and extension updates go
  to Google directly; a bang list comes from imput's server; site visitors are recorded; until 2026-09-30 telemetry went to PostHog Cloud EU (FACT, see table and notes above).
- **Legal exposure.** Ardia disassembled Dia's binary and metallib (FACT: `A:README.md:174-176`;
  `A:docs/dia-spec.md:3-4,915-920`). Dia's Terms of Use forbid using Dia to "decompile, reverse engineer, or
  otherwise attempt to obtain the source code or underlying ideas" (item 10) and to build competing products
  (item 11) (FACT: diabrowser.com/termsofuse). Not legal advice; a risk for Ardia (INFERENCE).
- **Unproven pieces.** Two-Mac iCloud sync never run by the team; x64 CI not finished; passkeys and Widevine blocked
  (FACT).
- **Agent-driven churn.** 1,805 commits in 31 days, straight to `main`, release notes full of regressions fixed
  days later (FACT: commits API; e.g. 0.2.39-nightly.5 "tabs needed two clicks", `A:docs/testing.md:31`).
- **Licence history.** Apache-2.0 for its first month, GPL-3.0 now, plus a CLA that permits proprietary relicensing
  (FACT). Users may doubt its long-term openness (INFERENCE).

## What rac should take (ranked, concrete, with rough cost) and what rac should avoid

Porting note: Ardia's own files are Apache-2.0, which can be combined into GPL-3.0 rac with credit and the
Apache NOTICE kept (FACT: `A:NOTICE:6-7` says the same). Patches marked `SPDX-License-Identifier: GPL-3.0-only`
are already GPL (FACT: `A:docs/engine-build.md:527-529`).

### Take

1. **Ship from the Mac first, like every Ardia release so far.** Build, sign, notarize and publish 0.1.0 locally;
   add a nightly channel inside the same appcast (`<sparkle:channel>nightly`, monotonic build numbers, never
   downgrade); keep release notes as one file per version and open them after an update. Add an update smoke test
   that runs the previous build's Sparkle against the new zip, plus a data carry-over check. Keeps rac's fixed
   feed URL and key. Cost: 2–4 days. Evidence: `A:docs/releasing.md:38-73,185-199`.
2. **Port the Safe Storage "no silent reset" fix.** Chromium may create a new key when the keychain item is briefly
   invisible at login, which makes every saved password and cookie unreadable (FACT: 0.2.40 notes;
   `A:engine/patches/chromium-safe-storage-no-silent-reset.patch`). rac's tree has the same code path. On
   `errSecItemNotFound` it adds a fresh random key, and the add overwrites the item if it has appeared by then
   (FACT: `/Users/knewton/Dev/Github/rac/build/src/components/os_crypt/common/keychain_password_mac.mm:64-65,92-95`;
   `/Users/knewton/Dev/Github/rac/build/src/crypto/apple/keychain_v2.mm:189-211`). That the trigger happens at a
   slow login is Ardia's report (CLAIM). Ardia's 554-line patch includes its own `ardia/core/ac_content_hooks.h`, so
   it needs a rewrite for rac, not a copy (FACT: patch hunk for `keychain_password_mac.mm`). Cost: 1–2 days. High value: it prevents silent data loss for the maintainer and users.
3. **Arc import, with spaces kept as spaces.** Reuse Ardia's reader design: `StorableSidebar.json` (`sidebar.containers`,
   `spaces`, `items`, `topAppsContainerIDs`, `customInfo.windowTheme`, emoji `iconType`, `splitView`, live folders),
   SQLite read through a WAL-safe snapshot copy, a keychain prompt only after an explicit unlock step, secrets kept
   out of the UI layer, fixtures for every source. Map Arc profile → rac profile and Arc space → rac space, which
   Ardia gets wrong (issue #50). Cost: 1–2 weeks. Evidence: `A:packages/import/`.
4. **Bundle Ardia's power and idle patches behind switches**, then measure against Helium:
   (a) idle wakeups: no 15 s CPU health sampling, 60 s disk-space check, Bluetooth polling and hybrid passkey scans
   only on demand; (b) uBO first-write cost (lazy storage usage, ~180 ms on a performance core) and content-script
   load timing; (c) tab freezing that never freezes tabs with WebSocket or WebRTC and thaws others every 600 s;
   (d) main frames at 60 Hz on 120 Hz displays except during input, scrolling and the first second after a show,
   and Battery Saver lifting its 30 Hz cap during input. Cost: 1–3 days each, about 2 weeks in total. Evidence:
   `A:docs/engine-build.md:69-75,140-184`; `A:packages/ardiacore/ios/ArdiaCoreHost.mm:621-640`.
5. **A cross-browser perf bench and a stable-only gate.** Interleaved, rotated rounds; medians with min–max and n;
   rows for cold launch, new tab, tab switch, memory at 1/10/20 tabs, idle CPU and wakeups. This turns "never slower
   than Helium" into a number. Cost: about 1 week. Evidence: `A:docs/perf/vs-browsers.md:1-30`.
6. **Motion tokens from measured numbers, plus a spring helper for Views.** Add `(response, dampingRatio)` springs
   with Apple's conversion and closed-form position, then retune: sidebar hide/show (0.215, 0.79), edge reveal in
   (0.185, 0.77) and out 150 ms, hover card 0.92→1 (0.25, 0.75) with a 100 ms fade, tab close 100 ms fade with a
   140 ms slide, command bar grow 130 ms exponential ease-out, group expand (0.30, 0.82), space settle 0.25 s
   critically damped with Dia's rubber band, PiP throw (0.9, 0.9). rac's patches today use fixed tweens (100, 150,
   300 ms, `FAST_OUT_SLOW_IN`) (FACT: grep of `patches/rac`). Re-measure from rac's own recordings of Dia's screen
   instead of disassembly. Cost: 3–5 days.
7. **An outside-agent control channel that does not depend on rac's AI switch.** Copy the protocol hygiene: random
   token in a 0600 file, method allowlist, web-only targets, no extension worlds, stripped auth headers, no
   browser-close, a "controlled by X · Stop" pill, off by default, and a skill installer for Claude Code, Codex,
   Cursor and OpenCode. Add what Ardia lacks: rac's per-site Always/Never rules and risky-action confirmations
   applied to outside agents too. Cost: 1–2 weeks. Evidence: `A:docs/cli.md`; `A:engine/chromium/src/chrome/browser/ardia/ac_cli_token_policy.cc`.
8. **Folder-based end-to-end sync for phase 6.** Same promise as rac's: no server, no account. Reuse the threat
   model and file format (BIP-39 phrase, HKDF, AES-GCM with path-bound AAD, 1 KiB padding, immutable files, HLC
   last-writer-wins, snapshots). Cost: 4–8 weeks; needs a real two-Mac test Ardia never ran. Evidence: `A:docs/sync.md`.
9. **Small, cheap wins.** Deterministic group auto-naming for AI-off (1 day, `A:apps/browser/src/store/groupNames.ts`);
   a build check that fails if the binary or paks name a forbidden host (1 day, `helium-check-build.py`); a
   `series check` that reproduces the patched tree byte for byte (2 days); on-device translation with Apple's
   Translation framework on macOS 26 (about 1 week, `A:packages/shell/ios/TranslateModule.swift`); PiP throw to a
   corner (about 1 week, `A:docs/dia-spec.md:915-966`).
10. **Peek and Little Arc.** Both rivals ship them. Keep a Peek out of session restore and Recently Closed, as
    Ardia's hook does. Cost: 1–2 weeks. Evidence: `A:engine/patches/chromium-temporary-tab-restore-hook.patch`.

### Avoid

1. **A React Native (or any second UI toolkit) shell.** It costs tab-switch latency, memory and a large dependency
   tree, and it would be a rewrite of rac's Views patches. Ardia's own review keeps RN mainly for agent dev speed
   (FACT: architecture review §6).
2. **Disassembling Dia or Arc binaries.** Dia's terms forbid it (FACT). Measure from screen recordings and say so.
3. **Phoning home by default:** daily pings, counted update checks through rac's own server, a remote kill-switch
   file on rac's server, site session replays, third-party readers of telemetry. Each breaks rac's first
   non-negotiable. If kill switches are wanted, consider a static file on GitHub next to the existing feed, read
   only when update checks are on. That is a decision for the maintainer.
4. **Reverting Helium's extension download proxy** so the Web Store and extension updates reach Google directly
   (FACT: `A:docs/engine-build.md:50`). It trades privacy for convenience. Decide this deliberately.
5. **Spaces as profiles.** Keep rac's spaces separate from profiles.
6. **A script injected into the main world of every page** (`A:engine/ardiacore/src/ardia/core/renderer/ac_content_renderer_client.cc:106-116`).
   Pages can see and tamper with it. Prefer isolated worlds.
7. **Private macOS APIs without a fallback** (material 29, `CAFilter`).
8. **Ardia's process rules:** commits straight to `main`, no worktrees, no comments, agents releasing with no human
   review. rac's worktree and PR flow is safer for a browser people trust with logins.
9. **A switch for every Arc habit.** rac is opinionated; pick defaults instead.
10. **Outside-agent access with no per-site scope.**

## Open questions and things you could not verify

- Whether Ardia's 10-phase x64 CI finishes, and whether its bsdtar checkpoint hits the sub-second mtime problem rac
  found with siso. No run had finished by 2026-10-25 19:48 UTC; all six failed or were cancelled.
- Whether iCloud Drive sync works across two real Macs; the team lists it as untested by hand.
- Whether the measured Dia numbers are right. I could not run Dia. The figures are Ardia's own records.
- How many people use Ardia. The daily ping started today; GitHub counts 4,351 DMG downloads, which double-count
  reinstalls and Homebrew.
- Whether the Safe Storage silent reset actually fires on rac. rac's tree has the same find-then-add code (see
  Take 2), but nobody has reproduced the trigger on rac.
- Whether Helium already ships some of Ardia's power patches. Ardia says Helium turns `InfiniteTabsFreezing` on
  by default (`A:docs/engine-build.md:515`); the rest I did not check against helium-chromium.
- Whether the launch picture PNG is skipped for incognito windows. The backdrop skips them
  (`A:apps/browser/src/lib/launchBackdrop.ts`); I did not trace the picture capture fully.
- Whether Ardia will stay open source. The CLA allows proprietary relicensing of contributions.
- The licence of Ardia's patches to Chromium files not derived from Helium (Apache-2.0 per file headers, e.g.
  `ac_cli_control.cc:1`). Porting any of them into rac needs a per-file check.
- No independent reviews or Hacker News threads surfaced; only listicles (Toolfolio, Macfolio) mention Ardia.

## Sources

Primary (repo, at commit `4309c156`):
- https://github.com/mantrakp04/ardia (README, NOTICE, LICENSE, LICENSE.Apache-2.0, CLA.md, AGENTS.md)
- `A:docs/dia-spec.md`, `A:docs/dia-feature-parity.md`, `A:docs/agent-brief.md`, `A:docs/ardiacore-spike.md`
- `A:docs/engine-build.md`, `A:engine/patches/series`, `A:engine/patches/*.patch`, `A:engine/ardiacore/apply.sh`,
  `A:engine/patches/build/{env.sh,helium-pins.ini,gn_defines.sh}`
- `A:docs/releasing.md`, `A:docs/kill-switches.md`, `A:docs/growth.md`, `A:docs/sync.md`, `A:docs/cli.md`,
  `A:docs/testing.md`, `A:docs/perf/README.md`, `A:docs/perf/vs-browsers.md`, `A:docs/release-notes/*.md`
- `A:packages/import/README.md`, `A:packages/import/ios/Core/ArcSidebar.swift`
- `A:packages/shaders/ios/{MetalSurface,WindowBackdropView,PowerUpView}.swift`
- `A:apps/browser/src/components/{sidebar,layout,peek}/*`, `A:apps/browser/src/lib/tabLifecycle.ts`,
  `A:apps/browser/src/telemetry/copy.ts`, `A:apps/browser/src/store/groupNames.ts`
- `A:packages/ardiacore/ios/ArdiaCoreHost.mm`, `A:packages/ardiacore/ios/ArdiaCoreEarlyWindow.mm`,
  `A:packages/shell/ios/{ShellModule,Updater,AppModule,TranslateModule}.swift`
- `A:engine/chromium/src/chrome/browser/ardia/{ac_cli_control.cc,ac_cli_token_policy.cc}`
- `A:.github/workflows/{release,engine-x64,engine-x64-phase}.yml`, `A:.github/engine/x64.sh`
- Architecture review (2026-10-01): `gh api repos/mantrakp04/ardia/contents/docs/architecture-review.md?ref=2713787d`

GitHub API (read-only, 2026-10-25): repo metadata, contributors, commits, releases and asset download counts,
issues #26, #50, #151, #299-#302, #317, #333, #342; Actions runs of `engine-x64.yml` and `release.yml`;
`imputnet/helium-macos` releases; `imputnet/helium-chromium` `chromium_version.txt`.

Web:
- https://ardia.dev/ (FAQ, benchmarks, privacy claims)
- https://www.diabrowser.com/termsofuse (items 10 and 11)
- https://techcrunch.com/2026/10/22/arc-browser-sunsets-december-22-as-the-browser-company-doubles-down-on-dia/
- https://toolfolio.com/articles/best-arc-browser-alternatives-for-mac-and-windows-after-the-december-2026-shutdown-dia-zen-and-ai-browsers
- https://macfolio.com/blog/best-arc-browser-alternatives-for-mac

rac context: `plans/context/maintainer-brief.md`, `plans/context/ci-status.md`,
`plans/context/competitors-ardia-yab-2026-10-23.md`, `patches/rac/` (grep of animation durations).

## Verification

Adversarial fact-check on 2026-10-25, about 19:30 to 19:55 UTC. Sources: the same clone (`/tmp/rac-overhaul/src/ardia`,
confirmed at `4309c156`), `gh api` read-only (repo, contributors, commits, issues, releases, Actions runs), the
architecture review fetched at `2713787d`, `microsoft/react-native-macos` and `imputnet/helium-macos` releases, Dia's
terms page, and a read-only grep of rac's Chromium tree. GitHub counts move by the hour, so live numbers carry a time.

| # | Claim checked | Result | Change made |
|---|---|---|---|
| 1 | Engine is Chromium 155.0.8059.84 + Helium 0.19.4 / 0.19.4.1 | Confirmed (`helium-pins.ini`, `engine-build.md:3-5`) | None |
| 2 | 13 Helium patches skipped | Wrong: `SKIP` in `03-helium.py:46-65` has 15 entries | Fixed in Snapshot and Base |
| 3 | 60 patches, 492 hunks, 9,533 lines, 205 files | Confirmed by count | None |
| 4 | 93 of those files under `chrome/browser` | Wrong: 84 under `chrome/browser`; 93 is all of `chrome/` | Fixed |
| 5 | 46 hooks in "46 more" files; `apply.sh` 1,635 lines | Confirmed; 2 of the 46 files are also patched | Reworded |
| 6 | "Ardia has none in `ui/views`" | Wrong: 26 hunks in 8 files with `ui/views` in the path | Fixed |
| 7 | Layer sizes 11,071 and 18,685 lines | Roughly right: 11,039 and 17,071 (18,706 with `apply.sh`) | Made approximate |
| 8 | Licence: GPL-3.0 as distributed, Apache-2.0 own files; commits `2bbe12a6`, `8129b3d4`; CLA allows proprietary relicensing | Confirmed (`NOTICE`, `LICENSE`, `CLA.md` §1-2, commits API) | None |
| 9 | macOS 14+, Apple silicon only | Confirmed (`README.md:17`) | None |
| 10 | 805 stars, 210 issues, 1,805 commits; 1,783 by owner; 10 outside contributors | Drifted: 807, 211, 1,809, 1,787; 11 people plus a PostHog bot | Updated with time |
| 11 | 82 releases: 48 stable, 34 nightly | Wrong: 80 app releases (48 + 32); the other 2 are engine-only prereleases | Fixed in 4 places |
| 12 | v0.1.0 "Netnyahoo" on 2026-09-25; rename at 0.2.33 on 2026-10-12 | Confirmed (releases API) | Added that the bundle ID and feed URL moved at the rename |
| 13 | Last 100 commits all co-authored by Claude Opus 5.5 | Confirmed (checked newest 100 and commits 401-500) | None |
| 14 | Motion constants: dock (0.215, 0.79), Arc peek (0.185, 0.77), 150/100 ms, hover 0.92 / 100 ms / (0.25, 0.75) / (0.2, 0.6), delays 500/160/200 ms, close 140/100 ms with both curves, command bar 130 ms exp, group (0.3, 0.82), tuck 120 ms, zone 987/56.5, press 0.99/0.95/80/180 ms, wheel 49/250 ms, rubber band 0.15 | All confirmed in the cited files | None |
| 15 | Spring conversion stiffness (2π/response)², damping 4πζ/response | Confirmed (`swipeMotion.ts:19-21`; `dockMotion.ts:12-15` gives the same value as 2ζω) | None |
| 16 | 94 native-driver vs 22 JS animations today; 4 vs 86 on 2026-10-01 | Confirmed (grep; review line 298) | Fixed the review's provenance (written at `b885f89c`) |
| 17 | `session.json` saved 800 ms after a change | Confirmed (`persist.ts:16`) | None |
| 18 | Sync: 24 BIP-39 words, HKDF-SHA256, AES-256-GCM, HMAC names, `NNS1` format, 1 KiB padding, HLC, 40-file snapshots, 45/90-day tombstones, 15 s cycle, two-Mac test "left for a person" | Confirmed (`docs/sync.md`) | None |
| 19 | CLI: bundled CPython 3.13, pydoll 3.0, off by default, 0600 token file | Confirmed (`apps/cli/scripts/build.sh:2,14`; `pyproject.toml:20`; `settings.ts:148`; `cli.md:190-195`) | None |
| 20 | "About 70" allowed CDP methods | Exactly 70. The list also lets a client create and close tabs and add scripts that run on new documents | Fixed count and line refs, added those powers |
| 21 | Daily ping, update-check count, kill-switch file, Composio reader, rrweb replays kept 30 days | Confirmed (`growth.md`, `kill-switches.md`, `copy.ts`) | Added that PostHog Cloud EU got telemetry until 2026-09-30, and pre-0.2.18 copies still send it there |
| 22 | Sparkle: 8 h checks, auto update, 2.9.6, one appcast with a nightly channel, 3 items per channel, team U5L5T3NGVV | Confirmed (`Info.plist:119-128`; `releasing.md:38-73,93`) | None |
| 23 | Tab switch 40 ms vs Helium 8.5 ms, then 10-16 ms; 20-tab memory 1,183 vs 919 MB | Confirmed (`vs-browsers.md`) | Added Helium's 1,125 MB and Ardia's 1-tab lead |
| 24 | CI Release workflow: first commit `e8ec213e`; "only successful run is a dry run" | Out of date: two dry-run successes by 19:29 UTC, none published | Updated with run IDs |
| 25 | x64 engine CI "not finished yet / still in progress"; 10 phases on a 3-core runner; bsdtar checkpoint | Phases, runner and `tar` line confirmed. Status is wrong: all six runs failed or were cancelled | Fixed in 2 places; noted `--no-mac-metadata` |
| 26 | Local engine build: M5 Pro, 2.5 h full, about 7 min incremental, 45 GB | Confirmed (`engine-build.md:351-364`). `AGENTS.md:43` says a full rebuild is about 5 h | None |
| 27 | Engine "published as a prerelease asset" | Partly wrong: local engines ride on the app release; only CI engines get a prerelease | Fixed |
| 28 | "About half" of releases since 0.2.31 carried a new engine | 25 of 42 (60%) | Made exact |
| 29 | 333 unit tests (228/32/75/26) | The doc's headline says 333, but its own table sums to 361 | Fixed |
| 30 | react-native-macos "tops out at 0.81" | Ardia's own README says so (CLAIM), and it is out of date: 0.83.0 shipped 2026-09-30 | Re-tagged and corrected in two places |
| 31 | AGENTS.md line refs (69-71, 92-93, 9-24, 83-96) | Wrong lines; content is at 13-25, 79, 82-84, 109-110 | Fixed; added the stale Apache line at 123 |
| 32 | Dia's terms items 10 and 11 | Confirmed (diabrowser.com/termsofuse) | None |
| 33 | Helium 0.19.4.1 on 2026-10-17; 0.20.1.1 on 2026-10-22 on Chromium 156; Ardia adopted Helium 2026-10-23 | Confirmed (helium-macos releases; `chromium_version.txt` at 0.20.1 is 156.0.8078.47; commit `d730de33`) | None |
| 34 | `page_script.js` is 1,138 lines, injected in the main world | Confirmed (`ac_content_renderer_client.cc:106-116` checks `ISOLATED_WORLD_ID_GLOBAL`) | None |
| 35 | Issues #1, #26, #50, #151, #279, #299-#302, #317, #332, #333, #342 | All exist with the stated state and topic | None |
| 36 | Safe Storage patch, and whether rac has the same bug | Patch exists (554 lines). rac's built tree has the same find-then-add code that can overwrite the key | Take 2 and the open question rewritten with rac file paths |

Not re-checked (left as written): the Dia layout numbers and the remaining motion rows that cite only `dia-spec.md`;
code-size rows other than `packages/*` and `apps/cli` (those matched within 3%); the Hexclave and Homebrew details;
TechCrunch's "ADK" line, which was already tagged CLAIM.

Overall confidence: **medium-high.** The architecture, storage, sync, agent-protocol and motion facts held up against
the code. The errors were in counts (releases, skipped patches, files, tests), in CI status that changed during the
day, and in a few line references. None of them changes a recommendation. Two corrections make the recommendations
stronger: rac's tree has the Safe Storage code path, and Ardia's earlier PostHog use adds to "Privacy drift".
