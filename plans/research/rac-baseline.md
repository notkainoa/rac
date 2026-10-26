# rac (baseline, 2026-10-25): research dossier

Audited against `main` at `d3f0d66` (worktree `/Users/knewton/.t3/worktrees/rac/t3-bb0e4397`, branch `plans/overhaul`). I read files, ran read-only `git` and `gh api` calls, and parsed every patch myself. I built nothing and launched nothing.

Evidence tags: **FACT** (read in code, docs, git, or a primary web source), **CLAIM** (self-report or marketing, including rac's own site and docs where code does not confirm them), **INFERENCE** (my reasoning). File references without a repo prefix such as `chrome/browser/...:NN` point at the *final state* of rac-owned files. I rebuilt that state by applying the rac-owned file sections of all 180 rac patches, in series order, into `/tmp/rac-overhaul/racfiles` (all applied cleanly). The patch that creates each file is named where it matters.

## In plain English

rac is one person's Mac browser. AI coding agents wrote almost all of it, in 23 days. It is Chromium with Helium's privacy changes, plus 180 rac "patch" files (lists of edits) on top. It has Arc-style spaces, pinned tabs, favorites, and a sidebar that hides. It also has an optional AI chat, and an AI that can click and type in your tabs. All of this works in the maintainer's own build. Nobody else can use it yet, because there has been no release. The code is careful in places, especially the AI safety checks. But the patches edit 216 files rac didn't write, from Chromium and Helium. Chromium now ships a new version every two weeks, and rac is already two versions behind. Tests exist, but nothing runs them automatically. Plans should start from this map: what exists, what it costs to keep, and what is already decided.

## Snapshot

| Field | rac today |
| --- | --- |
| What it is | A private macOS browser: Helium plus Arc/Dia-style tabs, spaces, and sidebar, plus an optional AI assistant and browser agent. FACT (`VISION.md:1-12`) |
| Engine | Chromium 154.0.8037.92 via Helium 0.18.2.1 (ungoogled-chromium plus Helium core). rac's `main` is exactly tag `0.18.2.1` plus 286 commits (`gh api compare 0.18.2.1...d3f0d66`: ahead 286, behind 0). FACT (`helium-chromium/chromium_version.txt`) |
| Platforms | macOS only, arm64 and x86_64 builds (`.github/workflows/build.yml:23`). The site says "macOS 13 or later" (`site/src/pages/index.astro:133`), which matches Chromium 154's `mac_deployment_target = "13.0"`. FACT (`build/src/build/config/mac/mac_sdk.gni:29`, main checkout) |
| License | GPL-3.0, inherited from Helium. FACT (`LICENSE`, `gh api repos/notkainoa/rac`) |
| Repo | `github.com/notkainoa/rac`. Still a GitHub fork of `imputnet/helium-macos`, description "Helium Browser for macOS", homepage `racbrowser.vercel.app`. FACT (`gh api repos/notkainoa/rac`) |
| Stars | 0 stars, 0 forks, 0 watchers, 0 issues ever. FACT (`gh api`, 2026-10-25) |
| Age | Repo created 2026-10-02. First rac commit `fa36c77` on 2026-10-02. Non-merge commits on 12 distinct days (13 counting merge commits). FACT (`git log`) |
| Release cadence | 0 releases. `rac_version.txt` = `0.1.0`. 4 release-workflow runs: 3 failed, 1 cancelled; a 5th (run 40222453249, for PR #20) was in progress on `ci/tar-pax-checkpoint`. FACT (`gh run list --workflow build.yml`) |
| Team size | 1 human. 269 non-merge commits, all authored by Kainoa Newton; 259 (96%) carry an AI co-author trailer (factory-droid 131, Claude Opus 5.5 108, Claude Fable 5.1 17, Cursor 13, Claude Sonnet 5.5 3; some commits have two). FACT (`git log d3f0d66`) |
| Business model | None. No accounts, no server, AI is the user's own key, local model, or installed agent. FACT (`VISION.md:38-43`, `docs/internals/ai.md:20-21`) |
| Upstream position | Helium-macos is at 0.20.1.1 (Chromium 156.0.8078.47, 2026-10-22). rac is 6 releases behind (0.18.3.1, 0.19.1.2 prerelease, 0.19.2.1, 0.19.3.1, 0.19.4.1, 0.20.1.1) and 2 Chromium majors behind. FACT (`gh api repos/imputnet/helium-macos/releases`; Chromium version read from the submodule at tag 0.20.1.1). The brief's "seven releases" comes from `plans/context/inboxzero/rac-audit.md:226`, which lists a 0.19.1.1 that has no tag or release. FACT (`gh api repos/imputnet/helium-macos/tags`) |
| Chromium cadence | Chromium moved to a new stable major every two weeks from M153 (2026-09-08). M154 stable 2026-09-22, M155 2026-10-06, M156 2026-10-20, M157 2026-11-03. FACT ([Chrome blog](https://developer.chrome.com/blog/chrome-two-week-release), [chromiumdash M157](https://chromiumdash.appspot.com/fetch_milestone_schedule?mstone=157)). `docs/internals/overview.md:69` still says "roughly every four weeks" |
| Helium cadence | Helium's minor version tracks the Chromium major (0.17=153, 0.18=154, 0.19=155, 0.20=156). 12 helium-macos releases from 2026-09-12 to 2026-10-22, about one every 3.3 days. FACT (`gh api` releases; submodule `chromium_version.txt` read at tags 0.17.2.2, 0.18.2.1, 0.19.4.1, 0.20.1.1) |

## Features

Status words. Nothing is **shipped**, because nothing has been released. I use:

- **Built**: merged on `main`, never released. (The maintainer's base build may lag `main`; see Open questions.)
- **Inherited**: comes from Helium or Chromium; rac did not write it.
- **Planned**: in `docs/roadmap.md` with no patch yet.
- **Proposed**: only in `plans/context/roadmap-revision-2026-10-22.md` (not committed).
- **Not planned**: excluded by `VISION.md`.

### Patch groups at a glance

Measured by my own parser over `patches/series` (rac entries are lines 29-208). "Upstream" means a file rac did not create (Chromium, ungoogled-chromium, or Helium). "rac-own edits" are later patches editing files an earlier rac patch created. FACT.

| Group | Patches | Patch lines | New files (lines) | Upstream file entries | Upstream hunks | Upstream +/− | rac-own edits +/− |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ai | 39 | 39,146 | 107 (13,139) | 56 | 98 | +299/−41 | +12,695/−2,935 |
| agent | 19 | 24,310 | 72 (10,456) | 26 | 58 | +198/−9 | +6,557/−1,252 |
| spaces | 26 | 15,079 | 48 (7,782) | 69 | 127 | +526/−64 | +2,100/−871 |
| pinned | 18 | 7,841 | 26 (3,920) | 44 | 95 | +377/−45 | +1,365/−40 |
| look | 20 | 6,747 | 13 (792) | 71 | **161** | **+1,020/−324** | +1,232/−324 |
| onboarding | 6 | 4,647 | 14 (2,101) | 13 | 24 | +47/−22 | +718/−432 |
| sidebar-address-bar | 10 | 4,180 | 11 (2,643) | 24 | 64 | +216/−35 | +260/−58 |
| settings | 13 | 2,475 | 12 (793) | 44 | 91 | +342/−320 | +84/−8 |
| sidebar | 4 | 1,948 | 4 (526) | 6 | 11 | +34/−28 | +391/−310 |
| dev | 5 | 1,147 | 2 (345) | 2 | 3 | +3/−0 | +502/−32 |
| sidebar-reveal | 5 | 1,136 | 4 (139) | 29 | 58 | +135/−79 | +23/−83 |
| pip | 5 | 1,067 | 7 (419) | 17 | 28 | +99/−7 | +149/−14 |
| updates | 4 | 746 | 5 (227) | 19 | 34 | +92/−28 | +38/−7 |
| branding | 4 | 176 | 0 | 9 | 11 | +35/−16 | +2/−2 |
| privacy | 2 | 96 | 0 | 6 | 6 | +6/−31 | 0 |
| **Total** | **180** | **110,741** | **325 (43,282)** | **435** | **869** | **+3,429/−1,049** | **+26,116/−6,368** |

My totals differ slightly from `plans/context/inboxzero/rac-audit.md` (437 entries, 871 hunks, 217 files, −1,096). The gap in entries, hunks, and removed lines (2, 2, and 47) matches exactly two rac-created files (`chrome/browser/ui/rac/sidebar_reveal_prefs.{h,cc}`, 20 + 27 lines) that `sidebar-reveal/frameless-shortcut-settings.patch` later deletes; I count those deletions as rac-own, the audit counted them as upstream. INFERENCE. The one-file gap in distinct files is unexplained.

The roadmap revision says "AI basics … 42 patches" and "the 21 patches" for the agent. Those counts were right when it was written (42 and 21 at `9b4d949`, 2026-10-22). PR #11 then folded 13 fix patches (6 ai, 7 agent) and later PRs added new ones, so the series now has 39 and 19. FACT (`git show <commit>:patches/series` at `9b4d949`, `6ffec8a`, `d3f0d66`).

### Tabs, sidebar, and spaces

| Feature | Status | Evidence |
| --- | --- | --- |
| Vertical sidebar, restyled (no fill at rest, solid selected card with 0 2 8 shadow) | Built on Helium's vertical tabs | `look/sidebar-restyle.patch`, `chrome/browser/ui/views/rac/rac_look.cc:25,63-91` |
| Layout locked to vertical; horizontal and compact layouts removed from settings and shortcuts | Built | `chrome/browser/ui/rac/appearance_locks.cc:30-35,53-56`; `settings/appearance-locks.patch:297-303` |
| Two layouts: **Top bar** (Dia: 40 px bar with address pill and Chat button) and **Sidebar** (Arc: address bar at the top of the sidebar). Top bar is the default | Built | `chrome/browser/ui/rac/layout_prefs.cc:15`, `look/top-bar-default.patch`, `chrome/browser/ui/views/rac/top_bar.h:27-30` |
| Sidebar on the right | Built | `look/right-sidebar.patch`, `sidebar-address-bar/right-side.patch` |
| Sidebar states: full or hidden only; Helium's icons-only state turned off | Built | `docs/internals/glossary.md:29-33`, `sidebar-reveal/full-or-hidden.patch` |
| Cmd+S toggles frameless mode (hidden sidebar) | Built | `VISION.md:79`, `sidebar-reveal/toggle.patch` |
| Edge reveal: left edge shows the sidebar over the page after a 100 ms dwell; top edge shows the toolbar | Built | `sidebar-reveal/edge-reveal.patch:84-87` |
| Spaces: per-profile sets of tabs; one space per window; "open in another window" screen | Built | `chrome/browser/ui/rac/spaces/spaces_window_manager.h:47-56` |
| Space switching: dots, Ctrl+1–9, next/previous, menu bar, two-finger trackpad swipe with sliding pages | Built | `spaces/commands.patch:52-60`, `spaces/switcher.patch`, `spaces/sliding-pages.patch` |
| Space editing: name, emoji icon (954-line icon set plus emoji picker), 8 color themes, Light/Dark/Auto | Built | `spaces/edit-space.patch`, `chrome/browser/rac/spaces/space.cc:44-53` |
| Move tab to space or to a new space; delete space | Built | `spaces/commands.patch`, `chrome/browser/ui/rac/spaces/move_tab_to_space_sub_menu_model.cc` |
| Hidden spaces unload after 15 min (tabs playing audio, in PiP, or loading stay live) | Built | `spaces_window_manager.h:65,134-137` |
| Favorites: Chromium's pinned tabs shown as tiles 44 px tall, shared by every space. In the full sidebar the tiles stretch to share each row, at most 3 per row (4 make a 2×2 square, "as in Dia"). The 44 px width and `kMaxFavoritesPerRow = 4` apply only outside the full state | Built | `chrome/browser/ui/views/rac/sidebar/sidebar_style.cc:46-53`, `sidebar_style.h:31-37`, `sidebar/favorite-grid.patch:78-85` (same code in the main checkout's `pinned_tab_container_view.cc:423`), `docs/internals/pinned-tabs.md:25-28` |
| Pinned tabs: per space, loose or in one-level folders, remember their page, reset, rename; closing resets in place; a typed address opens a new tab | Built | `docs/internals/pinned-tabs.md:93-118` |
| Drag between favorites, pinned section, folders, and open tabs, with a snap glide | Built | `docs/internals/pinned-tabs-drag.md`, `pinned/drag.patch`, `pinned/snap.patch` |
| New tab row in the sidebar | Built | `sidebar/new-tab-row.patch` |
| MRU tab cycling on by default; tab groups not auto-pinned | Built | `settings/behavior-mru-cycling-default-on.patch`, `settings/behavior-autopin-tab-groups-off.patch` |
| Media controls in the sidebar | Planned (phase 3). No patch exists | `docs/roadmap.md:109`; `patches/series` |
| Auto-archive / tab clean-up | Not planned in `VISION.md:127`; Proposed as "Tab clean-up" | conflict between `VISION.md:127` and `roadmap-revision-2026-10-22.md` |
| Auto-named tab groups | Proposed | `roadmap-revision-2026-10-22.md` |

### Navigation and command bar

| Feature | Status | Evidence |
| --- | --- | --- |
| Chromium address bar, restyled as a quiet pill; host-only URL in the sidebar layout; "center contents" option | Built | `look/quiet-address-bar.patch`, `sidebar-address-bar/host-only-url.patch`, `chrome/browser/ui/rac/appearance_prefs.h` |
| Site control center: Share, Bookmark, Developer tools, Copy URL; extension tiles; sound, PiP, and asked-for permissions; "…" for Print, Clear cache, Clear cookies, All site settings; connection security | Built | `chrome/browser/ui/views/rac/site_controls/site_controls_bubble.h:22-39` |
| Bangs (`!w cats`) | Inherited from Helium. Editor and address bar redesign Planned (phase 4); "nothing on this page is a design" | `docs/internals/bangs.md:3-6` |
| Command bar | Planned (phase 5). None exists | `docs/roadmap.md:137` |
| Clean links on copy; Air Traffic Control | Proposed / Later | `docs/roadmap.md:155`, roadmap revision |

### Split view, peek, small windows

| Feature | Status | Evidence |
| --- | --- | --- |
| Split view | Inherited from Helium; rac fixed a crash with spaces | `VISION.md:93`, `spaces/fix-split-view-replace-crash.patch` |
| Automatic picture-in-picture: any single playing video, on tab switch, app switch, or window hidden; floats over full-screen apps; Allow by default; off in incognito unless enabled | Built | `docs/internals/picture-in-picture.md:9-44` |
| Peek-style previews | Not planned | `VISION.md:128` |
| Little Arc (mini window for outside links) | Later / Proposed | `docs/roadmap.md:156` |

### Import, sync, profiles

| Feature | Status | Evidence |
| --- | --- | --- |
| Each profile opens in its own windows (profiles never share a window); spaces are per profile; a window shows one space, and a space is open in at most one window | Inherited plus Built | `VISION.md:64-68`; `spaces_window_manager.h:50-53` |
| Import through Chromium's importer, in onboarding ("Bring your stuff along") | Built (uses Chromium's importer) | `chrome/browser/resources/rac_onboarding/index.html:34`, `browser_proxy.ts:101-115` |
| Arc import (spaces, pinned tabs, favorites) and Dia import | Planned (phase 5). None exists | `docs/roadmap.md:139-140` |
| Sync | Not planned ("maybe later"); also listed under the roadmap's "Later" with no promises | `VISION.md:130`; `docs/roadmap.md:158` |

### Privacy and blocking

| Feature | Status | Evidence |
| --- | --- | --- |
| ungoogled-chromium removals; Helium's uBlock Origin, Helium services behind a consent screen | Inherited | `docs/internals/overview.md:145-151`; site "uBlock Origin, built in" (CLAIM) |
| Crash uploads off (URL emptied, mode forced "disabled", setting hidden); reports still written locally then deleted | Built | `docs/internals/overview.md:150` |
| No reset-report upload | Built | `privacy/no-reset-report.patch` |
| rac's own update check to GitHub, "Update rac automatically" toggle on About rac | Built, never exercised by a real release | `docs/internals/overview.md:199-203` |
| No rac endpoints in rac code beyond provider default URLs, the GitHub feed, and Helium's privacy/terms links | FACT (grep of every URL literal in the final rac files) | `/tmp/rac-overhaul/racfiles` |
| rac's own crash reports, per-crash yes | Later | `docs/internals/overview.md:155-176` |

### AI assistant (all Built; AI off by default)

| Feature | Evidence |
| --- | --- |
| Settings › Assistant: on/off, provider, server address, key, models, new tab page toggle, attach-current-tab toggle, "Let AI use the browser", "How much the AI asks", site rules, agents, chat history | `chrome/browser/ui/webui/settings/rac_ai_strings.cc` (strings), `chrome/browser/resources/settings/privacy_page/rac_ai_page.{html,ts}` (553 + 760 lines) |
| Right side panel chat (Dia-style thread, composer, model chips, native menus, right-edge pull handle, top-bar Chat button) | `ai/03`, `ai/09`–`ai/13`, `chrome/browser/ui/views/rac/ai/assistant_edge_handle.cc` |
| Attach tabs and text files (only text files) | `rac_ai_ui.cc` strings `fileNotText` |
| Chat history and saved prompts | `chrome/browser/rac/ai/history_store.h:13-16`, `saved_prompts.cc` |
| AI new tab page that decides Search or Ask on every keystroke, locally | `chrome/browser/rac/ai/new_tab_page.h:16`, `chrome/browser/resources/rac_ai/intent.ts` |
| Cmd+F "Ask" pill when no match and ≥3 words or a trailing question mark | `chrome/browser/rac/ai/ask_query.cc:12-38` |
| Link summaries: hold Option on a link for 500 ms, or context menu | `chrome/browser/rac/ai/link_summary.h:28-35` |
| Providers: OpenAI, Anthropic, Gemini, OpenRouter, Ollama, LM Studio, custom OpenAI-compatible | `chrome/browser/rac/ai/providers.cc:17-38` |
| Installed agents over ACP: Claude Code, Codex, Cursor, Gemini, Copilot, OpenCode, Goose, custom command | `docs/internals/ai.md:59-61`, `chrome/browser/rac/ai/acp/agent_recipes.cc` |

### Agent (browser control; Built, needs AI on)

15 tools, three permission levels (`ask`, `careful`, `auto`, default `auto`), per-site Always/Never, plan card (careful only), confirmation cards, critic (careful only), tab ring and pill with Resume/Stop, Cmd+. to stop, 25-call step cap, quiet step rows. Details in [Agents and AI](#agents-and-ai). FACT.

Not built: outside agents using rac's tools (Later, `docs/roadmap.md:152-153`), automations, cloud agents, 1Password/wallet (`docs/internals/ai.md:747-751`).

### Extensibility (CLI, MCP, API, extensions, mods)

| Surface | Status |
| --- | --- |
| Chrome extensions | Inherited (Helium serves Web Store downloads behind consent) |
| CLI | None |
| MCP for outside agents | None. rac's MCP server serves only the ACP agent rac launched, only during a run (`docs/internals/ai.md:307-331`) |
| Public API or local server | None |
| Boosts (per-site CSS/JS) | Planned (phase 5) |
| Dev switches compiled into every build: `--rac-window-screenshot` (plus `-requests`, `-command`, `-delay`, `-activate`), `--rac-launch-in-background`, `--rac-agent-debug`, `--rac-agent-mcp-echo` | Built. The `-requests` file lets anything that can launch rac with that switch drive it: run commands, click, type, swipe, press native keys (`chrome/browser/ui/views/rac/window_screenshot.mm:469-547`). No build flag gates them: `window_screenshot.mm` sits unconditionally in the `look` source set (`chrome/browser/ui/views/rac/BUILD.gn:7-15`). FACT |

### Other

| Feature | Status | Evidence |
| --- | --- | --- |
| Onboarding tour in its own 940×620 window, 7 steps: Welcome; where the address bar lives; first space color; import; assistant opt-in; Helium services; done | Built | `chrome/browser/ui/views/rac/onboarding/onboarding_window.cc:58-63`, `rac_onboarding/index.html:22-55` |
| Branding: name pass over strings, `rac://` alias, app icon, DMG art (normal and beta), tour logo, default-browser bar icon | Built | `docs/internals/overview.md:85-143`, PRs #7–#9 |
| Settings cleanup: General page (startup card, reset "danger zone"), Appearance trimmed and locked, About page updates toggle | Built (partial per roadmap) | `patches/rac/settings/*` |
| Marketing site (Astro 7, Tailwind 4, React 19 islands, Motion 14; ~6k lines) at racbrowser.com, downloads hidden | Built | `site/package.json`, `site/src/config.ts:4` |
| Strings: 100 grit messages in `chrome/app/rac_strings.grdp`; all assistant page strings hard-coded English in C++ ("English only for now; rac has no translation pipeline yet") | Built | `chrome/browser/ui/webui/rac_ai/rac_ai_ui.cc:30` |

## UI, look, and feel

I did not run the browser, so nothing here is a visual judgment. Values are read from code. Where I say something "feels" a certain way, it is INFERENCE from the code or a CLAIM from rac's docs.

### Layout

- **Window = sidebar + one page card.** The page sits in a rounded "content card" inset 6 px from the window, with a 10 px gap beside the sidebar (`chrome/browser/ui/views/rac/rac_look.h` constants `kContentCardInset = 6`, `kContentCardGapBesideSidebar = 10`). The inset changed 8 → 10 → 6 across three patches (`look/sidebar-restyle.patch:430`, `look/chrome-polish.patch:176-177`, `look/tighter-card-margins.patch:10-12`). FACT. The look is still being tuned. INFERENCE.
- **Top bar layout (default).** A 40 px bar above the card with a URL pill (radius 10) and a Chat button (radius 8). FACT (`top_bar.h:27-30`, `top_bar.cc:71`).
- **Sidebar layout.** The sidebar's top row borrows the real toolbar views (back, forward, reload, location bar), so bubbles and shortcuts keep working. The bottom row holds the profile button, the space dots, and the app menu. While focused, the address bar grows over the page if its suggestions don't fit. FACT (`chrome/browser/ui/views/rac/sidebar_address_bar/sidebar_header_view.h:38-78`).
- **Sidebar top to bottom:** favorites grid (44 px tall tiles, at most 3 per row in the full sidebar), the space header (icon, name, "more" button), pinned tabs and folders, a divider, open tabs, a new tab row, then the space dots. FACT (`sidebar_style.h:31-33`, `sidebar_style.cc:46-53`, `space_tab_list_header.cc:46-50`, `docs/internals/pinned-tabs.md:18-20`).
- **Infobars become cards** (radius 10, margin 8) above the top bar. FACT (`chrome/browser/ui/views/rac/infobar_card.h:30-36`, `look/infobar-card-everywhere.patch`).
- **Assistant** is a right-side panel (or a full tab on the new tab page). Agent confirm cards sit inside the chat thread. FACT (`docs/internals/ai.md:611-626`).

### Visual language and materials

- **Translucent window tint** over Helium's frame: dark `#121212` at alpha 0x99, light white at 0xCC. Sidebar and the margin around the card are painted with it. FACT (`chrome/browser/ui/color/rac_color_mixer.cc:21-23`, `:107-112`).
- **Tabs at rest have no fill** ("As in Arc and Dia"). Hover is a translucent fill. The selected tab is solid white (light) or black (dark) with a `0 2px 8px` shadow and a 1 px hairline. FACT (`rac_look.cc:25,63-91`).
- **Values copied from The Browser Company's apps.** Comments name the sources: "BoostBrowser_TabUI asset catalog" and "ARCClients_BaseAssets" for tab surfaces and text colors; "SharedAssets Menu/HairlineBorder" for menus. FACT (`rac_color_mixer.cc:34,54,97`). Colors are facts more than expression, but the provenance is worth knowing before publishing a design system. INFERENCE.
- **Radius scale:** 12 for popups, menus, link cards, and the space editor; 10 for the URL pill and infobar cards; 11 for the find Ask pill; 8 for tiles, controls, and swatches; 6 for menu rows; 4 for the pinned page button; dots 3 / 3.5 px. FACT (grep of `k*Radius` across `chrome/browser/ui/views/rac/**`).
- **Accent** `#FCBF49` (assistant); the URL pill's focused border is `#6395FC` (`kColorRacUrlPillBorderFocused`). FACT (`rac_color_mixer.cc:75,85`).

### Typography

- Native chrome uses the system font through Chromium's typography contexts, with semibold for titles and −2/+1 size deltas. FACT (grep of `Weight::` and `DeriveWithSizeDelta` in rac views).
- The assistant page uses `system-ui` at 15 px/1.5 for the thread, 12–13 px for controls, weights 500 and 600, SF Mono for code. "Spacing, type, and colors follow Dia's chat." FACT (`chrome/browser/resources/rac_ai/app.css:24,160`).

### Color and themes

- **8 space themes**, named and colored after Dia's `ColorPalette.BrandColors`: Neutral, Red, Orange, Yellow, Green, Blue, Pink, Purple. Each has a light pair and a dark pair of gradient stops. Neutral paints flat gray. Eight older Arc-style presets migrate to Dia ones. FACT (`chrome/browser/rac/spaces/space.cc:38-66`).
- **Each space owns its color mode** (Auto follows macOS; Light or Dark forces the window). The browser-wide color scheme and seed color are reset because "rac has no setting for" them. FACT (`spaces_window_manager.h:184-189`).
- The assistant panel takes the window's space colors for its bubbles, links, and send button. FACT (`app.css:160-200`).

### Motion (exact values from code)

| Where | Duration and curve | Source |
| --- | --- | --- |
| Space page slide after a swipe | Critically damped spring, ω = 2π/0.25 s ("Arc's page spring … 0.25 s response"); pages move at 0.5× the scroll delta; rubber band coefficient 0.15, dimension 255; a flick over 300 DIP/s turns the page; sampled at 240 Hz to find rest (≤1.5 s); runs as a compositor curve | `chrome/browser/ui/views/rac/spaces/space_pager.cc:44-63,107,307-330` |
| Space cross-fade (no swipe) | 150 ms | `space_pager.cc:63` |
| Space switch in the sidebar | 180 ms `FAST_OUT_SLOW_IN` (140 ms with Reduce Motion) | `spaces/sidebar-motion.patch:282-284` |
| Trackpad swipe gesture | Axis lock 15 DIP, switch threshold 75 DIP, reset after 300 ms | `spaces/switcher.patch:206-209` |
| Edge reveal | 100 ms dwell before revealing; Helium's 200 ms reveal (Reduce Motion aware); hover-exit grace 150 → 300 ms; cursor-exit grace 3 s; expand-on-hover delay 350 → 100 ms with the velocity heuristic turned off | `sidebar-reveal/edge-reveal.patch:10,84-87,142-143`; `build/src/chrome/browser/ui/views/frame/browser_view.cc:443-444` (main checkout) |
| Pinned and favorite drag | Snap glide 150 ms, 100 ms hand-off; row moves use Chromium's `RichAnimationDuration` (Reduce Motion makes them instant) | `chrome/browser/ui/views/rac/sidebar/drag_snap.cc:23,35`; `docs/internals/pinned-tabs-drag.md:43-55` |
| Top bar Chat button, site control tiles | 150 ms / 120 ms hover fades; alpha 0x10→0x22 and 0x0F→0x1C | `top_bar.cc:115,158`; `site_controls_bubble.cc:115,137,170,196` |
| Find bar Ask pill | 120 ms `LINEAR` | `chrome/browser/ui/views/rac/ai/find_ask.cc:107-115` |
| Link summary card | 120 ms fade in/out, 100 ms height coalescing, 700 ms loading throb; card appears after a 500 ms hover | `link_summary_card.cc:52-53,68`; `link_summary.h:28` |
| Agent tab ring and pill | Fade in 240 ms, fade out 160 ms, `EASE_OUT`; skipped with Reduce Motion | `chrome/browser/ui/views/rac/agent/agent_tab_indicator.cc:89-90,144-153` |
| Assistant page (CSS) | `--ease-out: cubic-bezier(0.23, 1, 0.32, 1)`; agent card in 240 ms; row expand by `grid-template-rows` 150–200 ms; chevrons 150–200 ms; hovers 120–140 ms; empty state 400 ms | `chrome/browser/resources/rac_ai/app.css:175,1768,1953,2218,1024,2117,1315` |
| Assistant busy signals | Two orb layers rotate (4 s and 2.8 s, infinite) and a shimmer runs (2.4 s, infinite) only while a reply streams and nothing else shows progress; a step spinner (0.8 s) only while a step runs; all off with Reduce Motion | `app.css:540-556,925-970,1074,1274-1300` |
| Onboarding | `--ease: cubic-bezier(0.2, 0.8, 0.2, 1)`; overshoot `cubic-bezier(0.34, 1.4, 0.64, 1)` at 180–220 ms; 120–400 ms elsewhere; Reduce Motion block | `chrome/browser/resources/rac_onboarding/app.css:31,375,530,728` |

Observations:

- Reduce Motion is handled in every moving animation I found. FACT (grep of `PrefersReducedMotion`, `ShouldRenderRichAnimation`, `RichAnimationDuration`, `prefers-reduced-motion`). The exceptions are two hover color fades: the top bar Chat button (150 ms) and the site control tiles (120 ms) use Chromium's standard `views::Button` hover animation, which never checks Reduce Motion (`top_bar.cc:115`; `site_controls_bubble.cc:170,196`; main checkout `build/src/ui/views/controls/button/button.cc:230-250`). FACT. Fades are the usual stand-in for motion under Reduce Motion, so this is minor. INFERENCE.
- Durations are scattered constants in about 15 files, with no shared motion tokens in C++ or CSS. FACT. Consistency depends on review, not structure. INFERENCE.
- The infinite CSS animations are scoped on purpose: a comment explains that a waiting reply "could wait for hours, so it holds still" (`app.css:541-545`). This respects "nothing that repaints continuously". FACT.
- Row expansion animates `grid-template-rows`, which runs layout every frame rather than only compositing. INFERENCE (standard browser rendering behavior). Cheap at this size, but it breaks the composite-only pattern used elsewhere.

### Signature interactions (likely to feel great)

- **Swiping between spaces** with a compositor-driven spring that matches Arc's constants, rubber-banding at the ends, and the pages beside it moving in the same frame. FACT (code); feel is INFERENCE.
- **Edge reveal with a dwell**, so brushing the edge doesn't pop the sidebar. FACT (`edge-reveal.patch:85-87`).
- **Drag snap**: a dragged favorite stays near its cell and glides; rows follow the pointer. FACT (`docs/internals/pinned-tabs-drag.md:46-55`).
- **Option-hover link summaries** in a private, cookie-less fetch. FACT (`docs/internals/ai.md:130-142`).
- **Agent steps as one quiet row** ("7 steps") that opens on click; failures never fold. FACT (`docs/internals/ai.md:611-626`).

### Things that feel bad, or will

- **ACP agents are slow to start, on every message.** Send to first tool call: Cursor about 15 s, Claude Code about 25 s, because "every message starts it again" by design. CLAIM (measured by the maintainer, `docs/internals/ai.md:708-718`).
- **Two layouts double the surfaces.** Top bar and Sidebar layouts, each with left and right sidebars, full and hidden states, and edge reveal. AGENTS.md's "Cover every surface" list multiplies with each. INFERENCE. "Opinionated" (`VISION.md:51-53`) argues for one.
- **Auto PiP guesses.** macOS rarely reports a window as covered, so rac uses app focus; PiP can open while the video is still visible on a second display. FACT (`docs/internals/picture-in-picture.md:68-79`).
- **The assistant can't be read in other languages.** Every assistant string is English in C++. FACT (`rac_ai_ui.cc:30`).
- **Settings ask for AI vocabulary.** Users pick "Ask every step", "Careful", or "Auto" under "How much the AI asks", plus per-site rules and an agents list with paths, Node.js, and sign-in help. FACT (`rac_ai_strings.cc`). Hard for non-developers, as `docs/internals/ai.md:705-707` admits. CLAIM.
- **No visual proof is in the repo**, by policy (screenshots go in PRs). I could not check any of the above by eye. FACT (`AGENTS.md:165-188`).

## Architecture

### How it integrates the engine

rac is a **patch layer**, not a wrapper or a separate shell. The build applies, in order: Chromium source → ungoogled-chromium patches → Helium core patches (343 entries together in `helium-chromium/patches/series`: 254 `helium/`, 71 `ungoogled-chromium/`, 18 from Brave, Bromite, Inox, Iridium, Debian, and upstream fixes) → Helium macOS patches (24 entries, `patches/series:1-27`) → rac's 180 patches (`patches/series:29-208`). Then Helium's name and domain substitution run, then rac's name pass, then resources are copied. FACT (`docs/internals/overview.md:6-45`). Quilt manages the merged stack in `build/src` (`he merge` / `he unmerge`).

Every rac feature therefore compiles into Chromium's own binary, in Chromium's own processes. There is no rac process, daemon, or server.

### Process model (who runs what)

| Process | rac code there | Evidence |
| --- | --- | --- |
| **Browser process (UI thread)** | Almost everything: spaces (`SpacesService`, `SpacesWindowManager`), sidebar items (`SidebarItems`, per-window `SidebarWindowSync`), all Views UI, AI service, chat streaming, ACP client, `AgentController` and `ActionGuard`, critic calls, link summary controller, onboarding window | `chrome/browser/rac/**`, `chrome/browser/ui/rac/**`, `chrome/browser/ui/views/rac/**` |
| **Browser process (IO / pool threads)** | MCP server listening on a Unix socket; ACP agent stdio on a dedicated IO thread; spaces file and chat history writes on background sequences | `docs/internals/ai.md:204-206,322-325`; `chrome/browser/rac/spaces/spaces_store.h` |
| **Network service** | Provider calls through `SimpleURLLoader` with two traffic annotations, `rac_ai_chat` and `rac_ai_models` | `chrome/browser/rac/ai/chat_stream.cc:29`, `model_list.cc:41` |
| **Renderers (web pages)** | rac's `semantic_validator` and `snapshot_agent` behind a rac-owned Mojo interface (`chrome/common/rac/agent/snapshot.mojom`), plus edits to Chromium's renderer actor tools (`type_tool.cc`, `key_dispatcher.cc`, `click_dispatcher.cc`, `tool_executor.cc`) | `patches/rac/agent/06-guard.patch`, `12-hardening.patch` |
| **WebUI renderers** | `chrome://rac-ai` (assistant panel and AI new tab page), `chrome://setup/?tour` (onboarding), rac pages inside `chrome://settings` | `rac_ai_ui.cc:24`, `onboarding_window.cc:62` |
| **Hidden off-the-record WebContents** | One throwaway profile per link summary fetch: cookies blocked, JS, images, plugins off, downloads denied | `docs/internals/ai.md:136-142` |
| **Child processes** | Installed ACP agents (own process group, scrubbed environment, empty scratch directory), and `/usr/bin/nc -U <socket>` started by the agent as its MCP bridge | `docs/internals/ai.md:199-239,316-321` |

### UI technology

- **Native chrome is Chromium Views (C++).** Sidebar, favorites grid, pinned section, space switcher, edit-space bubble, emoji picker, site control center, link summary card, find-bar Ask pill, agent tab ring and pill, assistant menus (native, 676 lines), top bar, infobar cards, onboarding window. FACT (`chrome/browser/ui/views/rac/**`: 67 files, 16,108 lines).
- **The assistant is a WebUI page in plain TypeScript and CSS.** No Lit, no Polymer, no framework: DOM built by hand, `chrome.send` message passing (30 message names registered in `chrome/browser/ui/webui/rac_ai/rac_ai_page_handler.cc:175-271`, plus 11 in the settings handler `rac_ai_handler.cc`), not Mojo. `app.ts` is 2,822 lines and `app.css` 2,484 lines. FACT (`chrome/browser/resources/rac_ai/BUILD.gn`, `app.ts:5-19`).
- **Onboarding is the same style**: plain TS (596 lines) and CSS (746 lines), `chrome.send` "like Helium's" setup page. FACT (`rac_onboarding/browser_proxy.ts:5`).
- **Settings additions use Chromium's settings framework, in two styles.** The Assistant page is a Polymer element (`rac_ai_page.ts:20,123`, 760 lines); the General page is Lit (`general_page_index.ts:28,49`). FACT.
- **Colors** go through a rac color mixer added to Chromium's `ColorProvider` pipeline (`AddRacColorMixer`), so light/dark and space themes resolve like Chromium's own colors. FACT (`chrome/browser/ui/color/rac_color_mixer.cc`).

### Languages and code layout (final state of rac-owned files)

323 live files, 63,030 lines. FACT (my reconstruction).

| Language | Files | Lines |
| --- | --- | --- |
| C++ `.cc` / `.h` | 151 / 126 | 50,805 together with Objective-C++ (of which 5,937 are unit tests) |
| Objective-C++ `.mm` | 7 | (in the line above) |
| TypeScript | 17 | 11,017 together with CSS and HTML |
| CSS / HTML | 5 / 3 | (in the line above) |
| GN 11, grdp 1, mojom 1, Python 1 (emoji data generator) | 14 | about 1,200 |

| Directory | Files | Lines | What |
| --- | --- | --- | --- |
| `chrome/browser/rac/agent` | 59 | 10,961 | snapshot, refs, tools, runner, guard, critic, MCP server, controller, events, containment |
| `chrome/browser/rac/ai` (incl. `acp/` 17 files, 4,317 lines) | 73 | 10,795 | prefs, providers, chat protocol, SSE, history, prompts, page text, link summary, model lists, ACP |
| `chrome/browser/ui/views/rac` | 67 | 16,108 | spaces 4,402; ai 3,564; sidebar 2,124; sidebar address bar 1,478; site controls 1,402; agent 930; onboarding 358; look, top bar, infobar, screenshot harness |
| `chrome/browser/ui/rac` | 52 | 7,103 | sidebar items and sync 3,373; spaces window manager 3,067; prefs; onboarding 339 |
| `chrome/browser/resources/rac_ai` | 11 | 7,396 | assistant WebUI |
| `chrome/browser/ui/webui` | 8 | 3,087 | assistant page handler, settings handler and strings |
| `chrome/browser/rac/spaces` | 15 | 2,047 | space model, service, store |
| `chrome/browser/resources/settings` | 11 | 2,013 | Assistant and General settings pages |
| `chrome/browser/resources/rac_onboarding` | 5 | 1,664 | tour WebUI |
| `chrome/browser/rac/pip`, `updates` | 11 | 794 | auto PiP prefs and app-focus observer; update feed |
| `chrome/renderer/rac`, `chrome/common/rac` | 7 | 571 | renderer-side agent validation and snapshot Mojo |

AI and agent code is about 38.6k of the 63k lines (61%). INFERENCE (sum of the AI/agent directories above plus the Assistant settings page).

### Hooks into upstream files

- **435 upstream file entries, 869 hunks, 216 distinct upstream files.** 36 files are edited by three or more rac patches. The worst: `chrome/browser/ui/BUILD.gn` (26 patches), `settings_localized_strings_provider.cc` (13), `prefs_util.cc` (11), `browser_command_controller.cc` (10), `browser_view.cc` (9), `vertical_tab_strip_region_view.cc` (9), `browser_view_tabbed_layout_impl.cc` (8). FACT (my parser).
- **320 of 869 hunks (37%) are in `chrome/browser/ui/views/`**, the area `docs/internals/overview.md:82-83` says changes most often. Next: settings resources 110, `ui/tabs` 63, `ui/webui` 39. FACT.
- **The UI groups break the "small hooks" rule; the AI groups mostly keep it.** `look` alone has 161 upstream hunks (+1,020/−324) for 792 lines of new files. `ai` + `agent` add 23.6k lines of new files against 156 upstream hunks. FACT.
- **66 of 180 patches touch no upstream file at all**; 47 touch 1–3 hunks; 29 touch more than 10. The heaviest: `spaces/owned-tabs.patch` (46 hunks in 18 files), `sidebar-address-bar/header.patch` (34), `look/dia-chrome.patch` (29), `agent/12-hardening.patch` (29). FACT.
- **Overlap with Helium is the real rebase risk.** 139 of the 216 upstream files rac edits are also patched by Helium or ungoogled-chromium; 663 of 869 rac hunks (76%) live in them. Between rac's base and Helium 0.20.1.1, at least 206 Helium core patch files changed, and at least 117 of rac's upstream files (624 hunks, 72%) are files those changed Helium patches touch. FACT for the counts; "at least" because GitHub's compare API lists at most 300 files. Whether each becomes a conflict is INFERENCE; many will only shift line numbers.
- **Patch-on-patch layering.** 658 later edits to rac-created files (+26,116/−6,368). Some patches are mostly repairs of earlier ones: `ai/11-dia-chat-composer` (+1,350/−684 on earlier files), `agent/12-hardening` (+1,648/−233), `agent/15-quiet-step-rows` (+1,045/−310), `ai/fix-agent-run-lifecycle` (+557/−511), `ai/fix-review-followups` (+964/−92). 24 patches are named `fix-*`. FACT. PR #11 already folded 13 fix patches into their parents (`git log 6ffec8a`). FACT.
- **Dead or vestigial code exists.** `look/horizontal-tabs.patch` restyles horizontal tabs, but `appearance_locks.cc:53-56` locks the layout to vertical. Two prefs added early (`rac.browser.address_bar_in_sidebar`, `rac.browser.cmd_s_collapses_to_icons`) were added then removed by later patches. FACT. Candidates for deletion. INFERENCE.

### Dependence on moving Chromium internals

- Page reading and the agent use `optimization_guide` AnnotatedPageContent in actionable mode (34 `optimization_guide::` references in 18 rac-owned non-test files; 21 files counting tests). FACT (grep of the final-state rac files).
- Actions run through Chromium's Glic **actor** renderer tools (`chrome/renderer/actor/*`), with rac edits to eight files under `chrome/renderer/actor/` (type, key, click, tool executor, tool base, BUILD.gn) plus `chrome/common/actor.mojom`, and a flipped default: `kGlicActorToctouValidation` enabled. FACT (`agent/03-actions.patch:2142-2147`).
- These are Google's Gemini-in-Chrome internals. With a two-week Chromium cadence they can change shape twice a month. INFERENCE.

## Data and storage

### Where rac keeps things

The data directory is `~/Library/Application Support/me.kainoa.rac`, permanent once people install rac. FACT (`docs/internals/overview.md:90-93`). rac adds **no SQLite database** of its own (no `sql::` use in any rac file). Chromium's own History, Cookies, Login Data, and so on stay as they are. FACT (grep).

| What | Where | Format | Notes |
| --- | --- | --- | --- |
| Spaces list (id, name, emoji, theme, last active, unknown fields kept for newer versions) | Profile prefs `rac.spaces` | JSON inside Chromium's `Preferences` file, plaintext | `chrome/browser/rac/spaces/spaces_prefs.h:22`, `space.h` |
| Hidden spaces' tabs (navigations, groups, active tab, pinned item id) | `<profile>/rac spaces`, previous copy `rac spaces.bak` | JSON, `kVersion = 1`, atomic writes coalesced 1 s, background sequence | `chrome/browser/rac/spaces/spaces_store.h:50-74`, `spaces_store.cc:56-58,305` |
| Which space a window shows; which item and space a tab belongs to | Chromium session files (window and tab "extra data") | Chromium session format | `spaces_window_manager.h:44,191-192`; `docs/internals/pinned-tabs.md:46-57,78-82` |
| Favorites and pinned tabs, per space (`pinned.<space id>`), folders, pinned URLs, names | Profile prefs `rac.sidebar.lists` | JSON in `Preferences` | `chrome/browser/ui/rac/sidebar/sidebar_items.cc:32`; `docs/internals/pinned-tabs.md:13-16` |
| Layout, centered address bar, onboarding choice, auto PiP in incognito | Profile prefs `rac.browser.layout`, `rac.browser.center_address_bar_contents`, `rac.onboarding.skip_assistant`, `rac.auto_pip_in_incognito` | JSON in `Preferences` | `layout_prefs.h`, `appearance_prefs.h`, `onboarding_prefs.h`, `auto_pip_prefs.cc:12` |
| "Update rac automatically" | Local State `rac.browser_updates` (default on) | JSON in `Local State` | `patches/rac/updates/update-feed.patch:88-92` |
| AI settings: on/off, provider, base URL and model per provider, saved prompts, agent id, agent paths, custom command, browser control, permission level, site rules | Profile prefs `rac.ai.*` | JSON in `Preferences`, plaintext | `chrome/browser/rac/ai/ai_prefs.h:20-58` |
| AI provider API keys | Profile pref `rac.ai.encrypted_keys` | Base64 of ciphertext from `os_crypt_async` (keychain item "rac Storage Key") | `chrome/browser/rac/ai/key_store.cc:20-34`; `overview.md:91-92` |
| Chat history: conversation id, title, updated time, each message's role and text, titles of attached tabs (not page text) | `<profile>/rac_ai_history.json` | **Plaintext JSON**, read lazily, capped at 16 MB on read, written with `ImportantFileWriter` | `chrome/browser/rac/ai/ai_service.cc:26`, `history_store.h:13-16`, `history_store.cc:18`, `chat_history.cc:62-73`. Saving is on by default (`ai_prefs.cc:31`) |
| ACP agent scratch dirs, npx cache, temp | `<profile>/Cache/rac-agent/scratch/<agent>` | Files the agent writes (quarantined) | `chrome/browser/rac/ai/acp/acp_service.cc:203-207`, `agent_recipes.cc:164-172`; `docs/internals/ai.md:212-218` |
| MCP socket during an agent run | `<profile>/rac-agent-mcp/<token>/s` (dir 0700, socket 0600), or `/tmp/rac-mcp-<uid>-<token>/s` when the path is over 103 bytes | Unix domain socket | `chrome/browser/rac/agent/mcp_server.cc:41-65,111,444-462` |
| Link summaries, model lists, pending find-Ask prompt | Memory only (model lists a few minutes; the prompt 15 s) | — | `docs/internals/ai.md:68-76,136-148`; `assistant_side_panel.cc:128` |
| Sparkle updater state | `me.kainoa.rac` user defaults and `~/Library/Caches/me.kainoa.rac` | plist / files | `docs/operations/releases.md:124-125` |
| Crash dumps | Crashpad writes locally, then deletes; never uploaded | minidumps | `docs/internals/overview.md:150` |

### Encryption and keys

- Only AI keys get rac-level encryption, through Chromium's `os_crypt_async` and the macOS keychain item "rac Storage Key" (which also protects cookies and passwords). FACT (`key_store.cc`, `branding/identity.patch:45-54`).
- Chat history and every rac pref are plaintext on disk. FileVault covers the disk, but any process running as the user can read them. INFERENCE. A privacy-first plan should decide whether chat history deserves the same `os_crypt_async` treatment as keys.
- `MAC_TEAM_ID` is still empty in `chrome/app/theme/chromium/BRANDING` (`branding/identity.patch:32-33`), even though Developer ID secrets now exist (`gh secret list`: 9 secrets). FACT. What an empty team ID breaks under a real Developer ID (keychain access groups, passkeys) is unverified. INFERENCE.

### Sync and servers

- No sync, no accounts, no rac server of any kind. FACT (`VISION.md:38-43,130`; no rac endpoints in rac code).
- The website is static (Astro on Vercel) with no analytics, cookies, third-party scripts, or remote fonts. CLAIM (`docs/operations/site.md:3-6,63-65`); the site bundles Inter via `@fontsource-variable/inter` (`site/package.json`), which fits the claim. FACT.

### What leaves the machine (defaults)

| Destination | When | Default | Evidence |
| --- | --- | --- | --- |
| rac | Never | — | FACT (no rac endpoints in code) |
| GitHub (`github.com/notkainoa/rac/releases/latest/download/appcast-<arch>.xml`) | Update check at launch and then hourly; download in background | On (toggle on About rac) | `patches/rac/updates/update-feed.patch:138-143`. Hourly: Helium's `sparkle_check_interval` defaults to 3600 s and is written as `SUScheduledCheckInterval` (`patches/helium/macos/updater/sparkle2-integration.patch:28,174`); nothing in `devutils/shared.sh:59-69` or `flags.macos.gn` overrides it; the glue turns automatic checks on and checks once at launch (`patches/helium/macos/updater/fixup-sparkle-glue.patch:614-633`). FACT for the settings; the live schedule is INFERENCE from Sparkle's documented key |
| Helium (imput) servers | Extension downloads, uBlock lists, spell check, bangs list, component updates | Behind Helium's consent screen, asked in onboarding | `docs/internals/overview.md:151`; `rac_onboarding/index.html:49` |
| Chosen AI provider | Chat (page text up to 8,192 tokens per block when a tab is attached), model list fetches (`GET /models` with the key when the menu or settings page opens), connection checks on save, link summary text (≤3,000 tokens), critic metadata (careful level only) | Only with AI on (AI is off by default) | `docs/internals/ai.md:68-90,130-142,552-558`; `page_text.h:17`; `link_summary.h:35` |
| ACP agent's cloud (Anthropic, OpenAI, Cursor, Google, GitHub, and so on) | Whatever the user's CLI sends | Only with AI on and an agent selected | `docs/internals/ai.md:59-61` |
| The linked site, from the user's IP | Option-hover link summary fetch (cookie-less, JS off) | Only with AI on | `docs/internals/ai.md:136-142` |
| Google | Whatever ungoogled-chromium and Helium leave; rac adds none | — | INFERENCE (not audited here) |

### Telemetry

None from rac. The site's own table lists "Telemetry and crash reports: None". FACT for code, CLAIM for the site ([racbrowser.com](https://racbrowser.com)).

## Agents and AI

### Turning it on, and the defaults that follow

- `rac.ai.enabled` defaults to **false**; onboarding asks, with "Later" as the default. FACT (`ai_prefs.cc:25`; `docs/internals/ai.md:15-17`).
- Once AI is on, these defaults apply: **"Let AI use the browser" on** (`ai_prefs.cc:36`), **permission level `auto`** (`ai_prefs.cc:37`), **attach the current tab to new chats on** (`ai_prefs.cc:30`), **save chat history on** (`ai_prefs.cc:31`), **AI new tab page on** (`ai_prefs.cc:29`). FACT.
- "With browser control on, every send starts a turn", so a plain question asked with a tab attached runs with the browser tools available. FACT (`docs/internals/ai.md:346-348`).
- AI is for regular profiles only. Incognito and guest get no panel, agents, summaries, or Ask. FACT (`docs/internals/ai.md:27-30`).

### "AI off costs nothing"

`AiServiceFactory` returns null unless the profile is regular and AI is on; history, key store, ACP service, and MCP server all hang off it. `AgentController` is created only when AI and browser control are on. Pref listeners stay registered; visible pieces are created only while AI is on. FACT (`docs/internals/ai.md:157-191`). With AI off, a link hover costs one pref read and returns (`chrome/browser/ui/views/rac/ai/link_hover_watcher.cc:147-170`). FACT. There is no automated test or benchmark of the guarantee beyond one pref test: `RacAiPrefsTest.MasterSwitchGatesEntryPoints`, added by `ai/14-off-audit.patch`, checks that `IsAiEnabled` and the AI new tab page follow the switch (`ai_prefs_unittest.cc:17-29`). The file's other 5 cases, added by later patches, cover defaults and model lists. FACT. Once turned on and off, built services stay in memory, dormant. FACT (`ai.md:172-174`).

### Providers and models

| Kind | Providers | Default model in code | Transport |
| --- | --- | --- | --- |
| Own key | OpenAI, Anthropic, Google Gemini (OpenAI-compatible endpoint), OpenRouter, Custom OpenAI-compatible | `gpt-4.1-mini`, `claude-sonnet-4-5`, `gemini-2.5-flash`, `openai/gpt-4o-mini`, none | HTTPS only (HTTP only for localhost), SSE streaming, OpenAI- and Anthropic-style tool streaming (`providers.cc:17-38,50-57`; `chat_protocol.cc`) |
| Local | Ollama (`localhost:11434/v1`), LM Studio (`localhost:1234/v1`) | `llama3.2`, none | OpenAI-compatible over localhost |
| Installed agent (ACP v1, JSON-RPC over stdio) | Claude Code via `npx @agentclientprotocol/claude-agent-acp@0.93.0`; Codex via `npx @agentclientprotocol/codex-acp@2.2.2`; Cursor `cursor-agent acp`; Gemini `gemini --acp`; Copilot `copilot --acp --stdio` with shell, write, and URL tools denied; OpenCode `opencode acp`; Goose `goose acp`; custom command | The agent's own default; rac doesn't show agents' model lists | `agent_recipes.cc:23-43,69-76`; `docs/internals/ai.md:719-726` |

- Model menus fetch live lists (`GET {base}/models`, Anthropic `GET {base}/v1/models`), filter to chat models, and cache per profile for a few minutes. FACT (`ai.md:68-76`). The hard-coded defaults are a year or more old by October 2026. INFERENCE.
- Only direct providers can run the critic. An ACP agent "is never asked to judge its own actions". FACT (`ai.md:63-66`).
- ACP `initialize` advertises no file reads, no file writes, and no terminal (`acp_client.cc:207-212`). Each recipe also strips the agent's own shell, file, and web tools, which the docs call a "second layer". FACT (`ai.md:232-239`).
- Timeouts: ACP initialize 45 s, cancel 3 s, first answer 90 s (`acp_client.cc:201,552`; `acp_client.h:24`). FACT.
- Speed: every message cold-starts the agent; 15 s (Cursor) to 25 s (Claude Code) to the first tool call. CLAIM (`ai.md:708-718`).

### Where the agent runs

```
Direct provider:  sidebar WebUI ─chrome.send→ PageHandler → ChatSession (tool loop in the browser process)
                                                          ↘ AgentController::HandleToolCall(kDirect)
ACP agent:        sidebar WebUI → AcpService::Prompt → spawns agent (child process, own group)
                  agent → /usr/bin/nc -U <socket> → McpServer (browser IO thread) → AgentMcpTools
                                                          ↘ AgentController::HandleToolCall(kMcp)
Both:             AgentController → ActionGuard::Evaluate → (card | critic | allow | block)
                  → ActionRunner → Chromium actor renderer tools (+ rac semantic_validator) → page
```

FACT (`docs/internals/ai.md:333-353,388-405`). One active turn per profile, owned by the page that started it; a send from another assistant page ends the running task. FACT (`ai.md:343-353`).

### Page representation

- Chromium **AnnotatedPageContent** in actionable mode (for geometry and `aria-hidden`), shared by chat and agent. FACT (`ai.md:92-99`).
- The agent sees accessibility-style lines such as `- button "Sign in" [ref=e6] [submit]`. Refs are keyed on tab, document, and DOM node, never reused; stale refs fail. Password and payment values show as `[redacted]`. Later snapshots of the same URL may be deltas. FACT (`ai.md:367-379`).
- **Published versus private snapshots**: approvals bind to what the model was shown, so a page can't swap a link's `href` between snapshot and click. FACT (`ai.md:380-386`).
- Hidden-text filter drops `display:none`, `visibility:hidden`, `aria-hidden`, transparent text, tiny boxes, and off-left boxes. It **misses `opacity:0` text and text pushed above the page**. FACT (`ai.md:103-108`; the filter itself is `chrome/browser/rac/ai/page_text.cc:272-305`).

### Tools

Read: `snapshot`, `get_page_text`, `list_tabs`, `find_in_page`. Action: `click`, `type`, `select_option`, `press_key` (Enter on an element only), `scroll`, `navigate`, `go_back`, `open_tab`, `switch_tab`, `close_tab` (only agent-opened tabs), `wait_for_settle`. FACT (`ai.md:390-392,727-730`; `chrome/browser/rac/agent/tool_registry.cc`). After each action the runner waits for the page to settle (4 s cap; 10 s around navigations) and returns a fresh snapshot. FACT (`ai.md:402-405`; `action_runner.cc:232,277,293,301,324`). The MCP server accepts protocol versions `2024-11-05`, `2025-03-26`, `2025-06-18`, `2025-11-25`. FACT (`mcp_protocol.cc:20-21`).

### Permissions and safety

| Action | `ask` | `careful` | `auto` (default) |
| --- | --- | --- | --- |
| Reads | free | free | free |
| Scroll, wait, switch tabs | free | like a click | free |
| Click or type on a named site | asks | plan card once, then critic per step | free |
| Navigate or click to a site the user didn't name | asks | asks | **free** |
| Typing text not in the user's messages | asks | asks | asks only on a site the user didn't name |
| Plain text field or select | asks | asks | free |
| Risky (submit, Enter, password/payment/file fields, buy/send/post/delete/sign in/upload words, unclassifiable clicks, `go_back`) | asks | asks | asks |

Source: `docs/internals/ai.md:436-444`, FACT. Always blocked at every level: unknown tools, closing the user's tabs, downloads, non-http(s) URLs, URLs not from a user message or a shown snapshot link, and `never` sites (`ai.md:416-420`). "Named" means the attached tab, a URL in a message, a plan-approved site, or an `always` rule (`ai.md:431-434`). The test `AutoAsksOnlyForRiskAndForeignTyping` asserts `navigate` to `https://other.com/` and typing model text into the attached tab are both `kAllow` at `auto` (`chrome/browser/rac/agent/action_guard_unittest.cc:196-223`). FACT, re-checked. The test turns off URL provenance for its `navigate` case (`requires_url_provenance = false`), so a real cross-site navigation still needs a URL from a user message or a shown snapshot link. A hostile page can supply such a link, so this does not close the gap below. INFERENCE.

Other safety machinery, all FACT from `docs/internals/ai.md`:

- **Confirm cards**: Allow / Don't allow, no default button, no keyboard shortcut for Allow, Esc stops the turn (`:475-485`).
- **TOCTOU re-validation** of element identity, target URL, and form submission (action, method, target, submitter) before mouse down, before release, between key events, and after the answer (`:487-500`).
- **Containment**: while an action is live, navigation goes only to approved origins; popups, downloads, and file pickers are refused; restrictions survive Stop and are lifted only by trusted user input (`:502-544`).
- **Critic** (careful only): sees the goal (≤4,000 bytes), tool, role, control type, origins, and booleans, never page text; fails closed after 4 s or any malformed reply (`:546-561`; `agent_controller.cc:755`).
- **Pause on real user input**, **Stop** (sidebar, pill, Cmd+., Esc), **25 tool calls per turn** (`:563-577`; `chat_protocol.h:24`).
- **ACP permission rule**: auto-approve only rac's own MCP tools, proven by runtime-set fields; verified for Claude and Codex; Cursor uses its own allowlist; Gemini, Copilot, and Goose cannot use rac's tools (`:274-305,690-700`).

### Prompt-injection defenses, and the known gap

- Page text goes in a nonce-delimited block; the system prompt says it is reference material; the nonce is defused if it appears in page fields. Soft: it depends on the model obeying. FACT (`ai.md:122-128`).
- URL provenance, published refs, containment, and a page-blind critic are structural. FACT.
- **Gap at the default level.** At `auto`, a hostile attached page can ask the agent to open a link (free), read a logged-in page (free), and type what it read into a field on the attached page (free). The page's own script can then send it out with no submit. FACT for the policy (`action_guard_unittest.cc:196-223`), CLAIM/INFERENCE for exploitability (`plans/context/inboxzero/rac-audit.md` §3; ERRATA confirms). Page script after an approval is an admitted open concern (`ai.md:679-689`).
- **No red-team suite or eval exists** in the repo. FACT (no eval files; tests are unit tests only).
- The site and README still say "It asks before it acts" (`site/src/pages/index.astro:104`; `README.md:28`). The in-product onboarding promises "It never acts in your browser without your confirmation." (`chrome/browser/resources/rac_onboarding/index.html:44`, from `onboarding/04-window-first-and-polish.patch:943`). `docs/roadmap.md:141` still describes plan-then-confirm. All three predate `auto` as default (PR #12, merged 2026-10-24). FACT.

### Outside-agent access, skills, automations

- **None.** The MCP server serves only the agent rac launched, only during that run; "any process of the same user can connect while a run is live" and gets that run's tools through the same guard. FACT (`ai.md:316-325`). Turning AI off also removes it. FACT (`ai.md:329-331`).
- No CLI, no HTTP API, no skills install, no scheduled routines, no Slack/Telegram. FACT (`ai.md:747-751`; `docs/roadmap.md:152-154`).
- Seeds a local "rac server" could grow from (INFERENCE): the MCP server and protocol code (`mcp_server.cc` 672 lines, `mcp_protocol.cc` 286 lines, peer-UID check via `getpeereid` at `mcp_server.cc:46`); the single controller entry point that already serves two transports; the event contract (`agent_events.cc` / `agent_events.ts`); and the dev request channel in `window_screenshot.mm:469-547`, which shows how far a file-driven automation channel already reaches.

### UI contract for AI

Controller events (`step_started`, `step_finished`, `plan_request`, `confirm_request`, `paused`, `resumed`, `run_state`, `summary`) are built only in `agent_events.cc` and parsed only by `parseAgentEvent` in `agent_events.ts`, which drops malformed input and caps strings. ACP agents' own progress arrives separately as raw `rac-ai-agent-update`. FACT (`ai.md:579-636`). This is a clean seam for a UI rewrite. INFERENCE.

## Build, release, and engineering

### Build system and local workflow

- Helium's tooling: `build.sh` for a full release build, `dev.sh` / `he` for development, quilt for the patch stack, GN plus siso for Chromium. FACT (`docs/internals/overview.md:16-45`). Helium-macos moved from ninja to siso on 2026-09-13. FACT (helium-macos commit `5a87a3e`, "build: use siso everywhere (#359)", from `gh api repos/imputnet/helium-macos/commits`).
- **Feature worktrees** get an APFS copy-on-write clone of the main checkout's ~100 GB `build/src` in about 30 s; a first build takes "a minute or two". CLAIM (`docs/operations/worktrees.md:6-10`). Each worktree has its own profile in `build/profile`. FACT (`worktrees.md:45-52`).
- The main checkout (`/Users/knewton/Dev/Github/rac`) is at `9b4d949` (2026-10-22), **71 commits behind `main`**, in merged state. New worktrees cloned from it start from an older base and must sync. FACT (`git log 9b4d949..d3f0d66 | wc -l`).
- Dev trees show rac's names by rewriting `.grd`, `.grdp`, and `.xtb` files in place; editing string files needs an `unsub` / `sync` dance. FACT (`overview.md:120-143`). This is a recurring trap for agents. INFERENCE.

### CI

| Workflow | What it does | Record |
| --- | --- | --- |
| `lint.yml` | Helium's `devutils/lint.py` over the series (Ubuntu) | passes |
| `sanity.yml` | Applies all patches to a cached Chromium tarball on macOS, fails on patch offsets, then runs the build for **30 s and passes on timeout** (`.github/scripts/sanity-check.sh:56-57`); a second job checks the name pass | 139 runs: 103 success, 30 failure, 6 cancelled (re-checked later on 2026-10-25; the 2 runs first seen queued passed). FACT (`gh run list`) |
| `build.yml` → `building.yml` → 10 chained `build-phase.yml` jobs per arch | Full build in 6-hour jobs, one hour reserved for checkpoint upload (`.github/scripts/github_build.sh:9-11`), sccache on the GitHub Actions cache (PR #19), then sign, package, appcasts, release | 4 runs: 3 failure, 1 cancelled; a 5th (40222453249) in progress. FACT |
| `pullfrog.yml` | An AI agent action, manual dispatch | 53 runs, all manual: 50 failure, 3 cancelled, 0 success. FACT |

- **Why the release chain can't finish (current hypothesis).** The dry run 40149762883 did three ~5-hour phases per arch and was cancelled in phase 4 (2026-10-25 18:08Z). Each phase restarted siso near step 0. Another agent's investigation says macOS `tar` stores whole-second mtimes in the checkpoint, siso compares nanoseconds, and 50,287 of 59,933 reruns in phase 3 were `stale-deps` from that truncation; the proposed fix is `tar --format pax` in `github_prepare_artifacts.sh`. CLAIM (secondary: `/tmp/rac-siso-checkpoint.md`, summarized in `plans/context/ci-status.md`). The fix is open as PR #20, "ci: keep sub-second mtimes in the build checkpoint" (opened 18:41Z, unmerged), and its validation run 40222453249 was in progress when I checked. FACT (`gh api pulls/20`, `gh run view`).
- **CI never compiles or runs a single rac test.** No workflow references `rac_*_unittests`, the Python tool tests, or `test-spaces.mjs`. FACT (grep of `.github/`).
- `main` has **no branch protection**. FACT (`gh api .../branches/main/protection` → 404 "Branch not protected").

### Signing, notarization, updates

- `sign_and_package_app.sh` signs with Developer ID and notarizes through `notarytool` when `MACOS_CERTIFICATE_NAME` is set, else falls back to ad-hoc `codesign --sign -` and skips notarization. FACT (`sign_and_package_app.sh:7-36`).
- All 9 release secrets exist: 7 `PROD_MACOS_*` signing and notarization secrets, `PROD_MACOS_SPARKLE_ED_PUB_KEY`, `RAC_SPARKLE_ED_PRIVATE_KEY`. The optional entitlements profile and the site deploy hook are absent. FACT (`gh secret list`, names only). The path has never completed. FACT.
- Updates: Helium's Sparkle 2 integration pointed at `github.com/notkainoa/rac/releases/latest/download/appcast-<arch>.xml`, EdDSA-signed by `devutils/rac/sparkle.py`, with deltas from recent releases; releases must not be prereleases or drafts because `latest` skips them; the workflow refuses a non-increasing version (`.github/scripts/github_prepare_release.sh:7-15`) and publishes with `draft: false`, `prerelease: false` (`.github/workflows/build.yml:91-94`). FACT (`docs/internals/overview.md:178-214`; `docs/operations/releases.md:65-87`).
- Dev builds have no updater (Sparkle is built only when the public key is set, which only CI does). FACT (`overview.md:208-210`).

### Release cadence

Zero releases. The site's download page is hidden behind `RELEASE_READY = false`. FACT (`site/src/config.ts:4`).

### Tests

Final-state count, one case per `TEST`/`TEST_F`/`IN_PROC_BROWSER_TEST_F` at line start. FACT (my count; the audit's "about 284" counted additions across patches).

| Target | Cases | Main files |
| --- | --- | --- |
| `rac_ai_unittests` (plus `browser_tests` source set with 1 browser test) | 153 | ACP client 21, page text 19, link summary 19, chat protocol 18, model catalog 11, ACP service 10, history 9, prompt 7, prefs 6, providers 6, recipes 6 |
| `rac_agent_unittests` | 85 | guard 18, snapshot serializer 13, events 11, containment 10, MCP protocol 9, ref table 8 |
| `rac_spaces_unittests` | 25 | spaces service 14 (incl. 2 theme tests from `look/dia-chrome.patch`), spaces store 11 (incl. the only pinned-tabs test) |
| `rac_pip_tests` | 9 | app focus observer 7, permissions 2 |
| `rac_updates_unittests` | 6 | feed override hardening |
| **Total** | **278** in 33 files | |

- **Zero tests** for sidebar, sidebar-reveal, sidebar-address-bar, site controls, settings, onboarding, branding, privacy, and the agent's UI. Pinned tabs (18 patches) has 1. FACT.
- Tooling tests: 71 Python test functions in `devutils/rac/test_{dev_names,name_pass,worktree}.py`, and one Node end-to-end script, `devutils/rac/test-spaces.mjs` (398 lines), that drives a fresh-profile build over the Chrome DevTools Protocol on loopback. FACT. Neither runs in CI. FACT.
- Verification policy is human-visible: agents must attach screenshots of the running build (`--rac-window-screenshot`). FACT (`AGENTS.md:165-188`).

### Process and review

- 19 PRs through #19: 14 merged, 5 closed unmerged (#1–#5, the early 5–8k-line feature PRs); #20 opened today. FACT (`gh api pulls`).
- 112 reviews, **all `COMMENTED`**: 74 by the maintainer's account, 25 cubic-dev-ai, 13 greptile-apps. **0 approvals.** FACT.
- 189 of 269 non-merge commits (70%) landed on `main` directly (first-parent). FACT.
- Commit types: fix 121, feat 99, docs 31, others 18. Fix commits by scope: ai 45, agent 22, spaces 9, pinned 9, settings 8, look 5. FACT (`git log --format=%s`).

### How it tracks upstream

- Procedure: merge `imputnet/helium-macos`, update the submodule to the tested Helium core, `quilt push -a --refresh`, fix rejects in rac patches only. CLAIM (untested, `docs/operations/upstream-sync.md:21-47`).
- **rac has never synced.** Neither the worktree nor the main checkout has the `upstream` remote the doc describes. FACT (`git remote -v` in both).
- **Upstream also changed rac's CI and build files.** From 0.18.2.1 to 0.20.1.1 (15 commits, 32 files), helium-macos changed `sanity-check.sh`, `sanity.yml`, `building.yml`, `build-phase.yml`, `github_prepare_xcode.sh`, `github_setup_env_toolchain.sh`, `dev.sh`, `build.sh`, `env.sh`, `devutils/shared.sh`, added `downloads.arm64.ini` and `downloads.x64.ini`, and **removed** `retrieve_and_unpack_resource.sh` and `devutils/build_tools.sh`, both of which rac's scripts call (`sanity-check.sh:16-17`, `devutils/shared.sh:12,31,35`). FACT (`gh api compare 0.18.2.1...0.20.1.1`; grep). The first sync will rework CI, not only patches. INFERENCE.
- Helium core moved 85 commits with ≥300 files changed (≥199 `patches/helium/*` files). FACT (`gh api compare`, capped at 300 files).
- Exposure: see [Hooks into upstream files](#hooks-into-upstream-files). At Chromium's two-week cadence, that refresh is due about 26 times a year, double the rate `overview.md:69` assumes. INFERENCE from FACT cadence.

### Doc drift found while verifying

| Doc says | Code or evidence says |
| --- | --- |
| `docs/roadmap.md:125-129`, `upstream-sync.md:76-78`, `overview.md:98`: no Apple Developer account yet | 9 secrets, including Developer ID and notarization, exist (`gh secret list`); `MAC_TEAM_ID` still empty |
| `overview.md:69`: Chromium majors "roughly every four weeks" | Two weeks since M153 ([Chrome blog](https://developer.chrome.com/blog/chrome-two-week-release)) |
| `docs/roadmap.md:141`, `README.md:28`, site: plan, then confirm; "It asks before it acts" | Default `auto` has no plan card and acts freely on named sites (`ai.md:436-454`) |
| Site: "A thin layer on top of Helium" (`site/src/pages/index.astro:118`) | 110,741 patch lines; 216 upstream files |
| `upstream-sync.md:9-19`: an `upstream` remote, fetch-only | No `upstream` remote in either checkout |
| `mcp_server.h:29` cites `acp-design.md` | No such file in the repo |
| Brief and audit: "seven releases behind" | Six helium-macos releases (no `0.19.1.1` tag) |
| Roadmap revision: AI basics 42 patches, agent 21 | Right when written (`9b4d949`); 39 and 19 now, after PR #11's fold and later patches. Stale, not wrong |
| Onboarding: "It never acts in your browser without your confirmation." (`rac_onboarding/index.html:44`) | Default `auto` acts without asking on named sites (`ai.md:436-454`) |

## Strengths and weaknesses

### Strengths (what is genuinely good)

1. **The privacy story holds in code.** rac adds no endpoint of its own (every URL literal checked), keeps AI off by default, excludes incognito from AI, encrypts provider keys with the keychain-backed `os_crypt_async`, and fetches link summaries in a throwaway cookie-less profile. FACT (see [Data and storage](#data-and-storage)).
2. **The agent's safety engineering is unusually deep.** TOCTOU re-validation at every script boundary, published versus private refs, URL provenance, containment that survives Stop, a page-blind critic that fails closed, and ACP permission checks bound to runtime-set fields. Each has unit tests (guard 18, containment 10, ref table 8, events 11). FACT.
3. **The AI layer follows the "new files, small hooks" rule.** `ai` and `agent` add 23.6k lines of new files against 156 upstream hunks. FACT.
4. **The motion has a real source.** The space pager reproduces Arc's spring, damping, rubber band, and flick constants on the compositor; Reduce Motion is respected in every moving animation I found (two hover fades are the exception); infinite animations run only while a reply streams. FACT.
5. **Sensible data model choices.** Sidebar items are the source of truth and tabs reconcile to them; spaces and stored tabs keep `unknown_fields` written by newer versions; the spaces file is written atomically with a `.bak`; history loads lazily. FACT (`docs/internals/pinned-tabs.md:11-22`; `space.h`; `spaces_store.h:50-74`; `history_store.h:13-16`).
6. **Any model.** Own key, Ollama or LM Studio, or seven named ACP agents plus a custom one, all through one controller. FACT.
7. **Docs record the traps.** `docs/internals/ai.md` (751 lines) and the pinned-tabs pages explain why, not what. FACT.
8. **Agent-friendly engineering.** Worktrees with 30-second clones, per-worktree profiles, and an in-process screenshot and input harness that works on macOS 26. FACT (`docs/operations/worktrees.md`; `window_screenshot.mm`).

### Weaknesses (critical)

1. **Nothing has shipped, and the release path has never completed.** 0 releases; 4 failed or cancelled release runs; signing and notarization configured but unproven; the update feed has never served a real update. FACT. The feed URL, signing key, and version rule can never change after release (`AGENTS.md:78-82`), so the first release locks in its mistakes. INFERENCE.
2. **Two Chromium majors behind, at a two-week cadence, never synced.** 76% of rac's upstream hunks sit in files Helium also patches; upstream removed two scripts rac's CI calls. FACT. Each month of delay adds two majors of drift and known security fixes. INFERENCE.
3. **The UI layer is expensive to keep.** `look` has 161 upstream hunks; 320 hunks sit in `chrome/browser/ui/views`; `chrome/browser/ui/BUILD.gn` is edited by 26 patches. FACT. The UI groups are where every sync will hurt. INFERENCE.
4. **The patch stack repairs itself.** 658 edits to rac's own earlier files, 24 `fix-*` patches, and several 1,000-line repair patches, all strictly ordered. FACT. A reader cannot learn behavior from the first patch of a group; `docs/internals/pinned-tabs.md:6-9` says so. FACT.
5. **No automated check of rac code.** 278 unit tests that CI never compiles; sanity "passes on timeout" after 30 s; zero tests for seven UI groups; one test for pinned tabs. FACT.
6. **The default agent policy contradicts the public promise.** Default `auto` lets cross-site navigation and model-written typing on the attached site run free, which allows a known injection chain, while the site and README say "It asks before it acts" and onboarding says it "never acts in your browser without your confirmation". No eval exists. FACT (policy, wording); exploitability unmeasured.
7. **Built on Google's moving AI internals.** About 34 `optimization_guide::` call sites plus edits to eight files under `chrome/renderer/actor/` and `actor.mojom`. FACT. Expect breakage at a two-week cadence. INFERENCE.
8. **Review is AI reviewing AI.** 0 approvals on 112 reviews; 70% of commits skip PRs; no branch protection; one human. FACT.
9. **Effort has gone to the optional part.** About 61% of rac's final code is AI and agent. Arc import, command bar, boosts, media controls, bangs editing, and a performance check don't exist. FACT (code); the judgment that this is inverted for an Arc-refugee window is INFERENCE, shared by the earlier audit and council (`plans/context/maintainer-brief.md`).
10. **UI technology is uneven.** The assistant is a 2,822-line hand-built TypeScript file with `chrome.send` and English-only strings; settings use both Polymer and Lit; native popups are hand-painted Views. FACT. A UI revamp starts by choosing one way. INFERENCE.
11. **More surfaces than "opinionated" suggests.** Two layouts × left/right sidebar × full/hidden × edge reveal, before themes and dark mode. FACT (prefs and patches). Each surface multiplies the screenshot matrix in `AGENTS.md:142-163`. INFERENCE.
12. **Small but real:** chat history in plaintext JSON; dev automation switches compiled into release builds; stale default model names; the base checkout 71 commits behind `main`. FACT.

## Decisions already made

Quoted from the repo and the brief. "Tension" notes where a decision conflicts with another source or with likely plans. Treat these as binding until the maintainer changes them.

### Product principles

| Decision | Quote | Source | Tension |
| --- | --- | --- | --- |
| Private | "rac never sees, keeps, or sells your data. There are no rac accounts, no rac servers holding your browsing, no ads, and no sponsored content." | `VISION.md:38-40` | A local "rac server" process is fine; a hosted one is not |
| Crash reports are the only exception | "The one thing rac may ever receive is a crash report, only if you turn crash reports on, and only when you say yes after that crash." | `VISION.md:41-43`; `docs/internals/overview.md:167-171` ("There's no \"send automatically\" choice") | — |
| Never slower than Helium | "Features that are turned off cost nothing: no background work, no network calls, no processes." | `VISION.md:44-47` | No benchmark exists to prove it |
| Beautiful and calm | "Arc's playful color and personality, combined with Dia's simplicity and elegance. Tasteful micro-interactions … never animation for its own sake." | `VISION.md:48-50`; `AGENTS.md:25-27` ("nothing that repaints continuously") | — |
| Opinionated | "A setting exists only when people genuinely need different behavior." | `VISION.md:51-53` | Two layouts plus left/right sidebar |
| AI optional and quiet | "AI is off until you turn it on. … it never takes an action you didn't ask for." | `VISION.md:54-56` | Default `auto` acts without asking on named sites |
| Open, tracks Helium | "rac is GPL-3.0, developed in the open, and tracks Helium closely instead of drifting into a separate codebase." | `VISION.md:57-58`, `:134-140` | Never synced so far |
| Cheap to update | "Every edit to an upstream file is a future merge conflict. Prefer new files and small hooks." | `AGENTS.md:30-31`; patch rules `AGENTS.md:127-139` | UI groups break it |
| Never do | "Collect, keep, sell, or look at your data", "Show ads", "Require an account", "Include a built-in VPN", "Include crypto features" | `VISION.md:115-121` | — |
| Not planned for now | "Auto-archiving old tabs", "Peek-style link previews in a floating window", "A settings page for everything", "Sync (maybe later)", "Linux and Windows (maybe someday)", "iOS (probably someday)" | `VISION.md:123-132` | Roadmap revision proposes "Tab clean-up" (an auto-archive) and Little Arc; the competitor note calls Peek expected |

### Hard constraints (AGENTS.md "Ways to hurt yourself")

| Decision | Quote | Source |
| --- | --- | --- |
| Nothing upstream | "Never push to, open PRs against, or file issues on any `imputnet` or `ungoogled-software` repository. Helium bans contributors for AI-written submissions." | `AGENTS.md:51-54`; Helium's own rule `helium-chromium/AGENTS.md:3,13` |
| Don't edit Helium | "Never edit files in `helium-chromium/` … Never edit Helium's patches … Change their behavior with a rac patch that applies afterward." | `AGENTS.md:55-60` |
| Protect real data | "Never point a build at a real profile folder in `~/Library/Application Support/`" | `AGENTS.md:61-66` |
| Protect the build tree | "Don't run `he reset`, delete `build/`, or start a full build without the maintainer's approval." | `AGENTS.md:67-73` |
| Submodule moves only with a release | "The Helium core version only changes when a helium-macos release is merged." | `AGENTS.md:74-77` |
| Never break updates | "The version in `rac_version.txt` only goes up, the update signing key never changes, and the feed URL in `rac/updates/update-feed.patch` never moves." | `AGENTS.md:78-82` |
| Permanent identity | "The bundle ID and data directory are permanent once people install rac." Bundle ID `me.kainoa.rac`. | `docs/internals/overview.md:90-93`; `docs/roadmap.md:53` |

### Browser features and words

| Decision | Quote or fact | Source |
| --- | --- | --- |
| Favorites vs pinned tabs | "Helium's 'pinned' items are rac's **favorites**. rac's **pinned tabs** are a separate Arc-style feature." | `AGENTS.md:44-46`; `docs/internals/glossary.md:21-26` |
| Sidebar states | "full: shows titles and icons; hidden: not shown at all. Helium's icons-only sidebar ('collapsed' in code) is turned off in rac." | `docs/internals/glossary.md:29-33` |
| Cmd+S | "Cmd+S turns frameless mode on and off, which fully hides and shows the sidebar." | `VISION.md:79-80` |
| Pinned tab behavior | "Closing resets in place." "Typed addresses open a new tab." | `docs/internals/pinned-tabs.md:95,105` |
| Build on Helium | "Build on what Helium already has (vertical layout, split view, side panels, zen mode, the keyboard shortcut system) instead of replacing it." | `AGENTS.md:138-139` |
| Helium services stay | "Helium's services (extensions, bangs, spell check, uBlock lists, component updates) stay as they are, labeled as Helium's and behind its consent screen. rac may host its own copy later." | `docs/roadmap.md:56-58` |
| Own updater | "rac has its own version number and checks only its own GitHub releases for updates, with its own setting on the About rac page." | `docs/roadmap.md:54-55` |
| Auto PiP defaults | "Allowed by default." "Off in incognito unless turned on." | `docs/internals/picture-in-picture.md:31,36` |
| Layout default (code decision) | Top bar is the default layout | `look/top-bar-default.patch` → `layout_prefs.cc:15` |
| Bangs | Wanted: editable bangs that survive list updates and a rethought address bar flow; "nothing on this page is a design" | `docs/internals/bangs.md:3,24-39` |

### AI and agent

| Decision | Quote | Source | Tension |
| --- | --- | --- | --- |
| Off by default | "AI is off by default (`rac.ai.enabled`, default false). … Onboarding asks whether you want it, with 'Later' as the default." | `docs/internals/ai.md:15-17` | — |
| No rac AI service | "rac never sees AI conversations. Only the user and their chosen provider do. There is no rac-hosted AI service." | `docs/internals/ai.md:20-21` | — |
| Risky always asks; three levels | "There is no level that skips the risky list." Levels "`ask`, `careful`, or `auto` (the default), plus per-site rules." | `docs/internals/ai.md:22-26`; brief ("chose three permission levels … default `auto`") | Free cross-site navigation at `auto` |
| Quiet rows | "Everything a reply does is one quiet row, with the detail a click away." | `docs/internals/ai.md:611-612`; brief | — |
| Regular profiles only | "AI is for regular profiles only. Incognito gets no assistant panel, no agents, no link summaries, and no find-in-page Ask." | `docs/internals/ai.md:27-29` | — |
| Page content is untrusted | "It is never allowed to give instructions to the assistant, and it never reaches the agent's safety check." | `docs/internals/ai.md:31-32` | Enforced softly for the model itself |
| Official CLIs, not reused logins | "Like T3 Code, it runs the provider's official tool instead of reusing its login." | `docs/internals/ai.md:195-197` | — |
| A run is one prompt | "Every message therefore starts the agent again; there is no idle agent between messages." "… which the run model rules out on purpose." | `docs/internals/ai.md:247-248,713-715` | 15–25 s per message |
| MCP scope | "It lives exactly as long as its run." "Don't add policy at the MCP layer, and don't route calls around the controller." | `docs/internals/ai.md:322,326-328` | Outside agents (Later, `docs/roadmap.md:152-153`) need a longer-lived server |
| Don't design the unbuilt | "Scheduled and triggered automations, 1Password sign-in, a wallet, letting outside agents … and cloud agents. Don't design these from this page. Ask the maintainer." | `docs/internals/ai.md:749-751` | This overhaul is that ask |

### Working rules

| Decision | Quote | Source |
| --- | --- | --- |
| Agents verify with screenshots | "You test it. The maintainer does not take first look." "UI changes must ship with screenshots in your reply." | `AGENTS.md:167-168,175-178` |
| PRs | "Never open a PR unless the maintainer asks." "One problem per PR." | `AGENTS.md:226,235` |
| UI and hard work go to Claude Opus | "UI / frontend / design work goes to Claude models." "Really hard work goes to Claude Opus 5.5." | `~/.claude/CLAUDE.md` (global instructions); brief |
| Branch for this work | "This work lives on the `plans/overhaul` branch, not on `main`." | `plans/context/maintainer-brief.md` |

## What rac should take (ranked, concrete, with rough cost) and what rac should avoid

For the baseline, "take" means: what to keep and build on from rac's own code, and what to fix first because every later plan depends on it. Costs are rough, for one maintainer with agents. All costs are INFERENCE.

### Take

1. **Keep the agent's safety core, and close the `auto` chain before any release.** Keep TOCTOU checks, published refs, containment, and the page-blind critic as they are. Change one rule set: after the agent reads a site the user didn't name, typing model-written text anywhere needs a card; or make cross-site navigation ask at `auto` when the turn has typed model text. Add an injection eval set (30–50 hostile local pages, run against 3–4 models and both run modes) using the existing `--rac-agent-debug` and custom-provider hooks. *Cost: guard change 1–2 days; eval harness 1–2 weeks.* Keeps the decided three levels and `auto` default; changes what `auto` allows. Needs sign-off.
2. **Do the first Helium sync now, and plan for a two-week cadence.** Sync to 0.20.1.1 (Chromium 156), rework the CI scripts upstream changed, and restore the `upstream` remote. Then pick a cadence on purpose: every Helium release, or every Chromium Extended Stable milestone (eight weeks; secondary coverage names 156 and 160, while the Chrome blog names none) plus security point releases. *Cost: first sync 3–7 days plus a full rebuild (needs approval); then about 1–2 days per sync if hunks shrink.*
3. **Shrink the UI groups' upstream surface.** Target: under 400 upstream hunks total (from 869) and under 150 in `chrome/browser/ui/views` (from 320). Move `look`, `settings`, `spaces`, and `sidebar-address-bar` logic into rac-owned files behind single hooks; add one `//chrome/browser/ui/rac` dependency instead of 26 patches editing `chrome/browser/ui/BUILD.gn`, where Chromium's dependency rules allow it (many Views files sit in the `ui` target to avoid cycles, so some may have to stay). *Cost: 2–4 weeks; repays on every sync.*
4. **Fold repair patches into their parents.** PR #11 did this for 13 fix patches (6 ai, 7 agent). It kept 7 others separate because each fixes several patches, so those need splitting first (`git show 6ffec8a`). Do it for the 24 `fix-*` patches and the large repair patches (`ai/11`, `ai/fix-review-followups`, `ai/fix-agent-run-lifecycle`, `ai/polish-sidebar-ui`). Target about 120 patches, each readable on its own. *Cost: 1–3 days per group, with a local build each.*
5. **Grow the per-run MCP server into an opt-in local endpoint for outside agents.** Reuse `mcp_server.cc`, `mcp_protocol.cc` (already speaks MCP 2024-11-05 to 2025-11-25), the single `AgentController::HandleToolCall` entry, the guard, and the cards. Add per-client permissions and a visible "connected agents" list, and decouple it from the assistant so a user can turn off rac's own chat but keep the endpoint (the Rhys Sullivan point in the brief). *Cost: 2–4 weeks plus design.* Conflicts with "lives exactly as long as its run" (`ai.md:322`) and with "AI off costs nothing" coupling; needs sign-off.
6. **Put tests in CI.** Run the 71 Python tool tests on a cheap runner now (minutes to set up; some worktree tests may need macOS, unchecked). Compile and run the five rac C++ test targets on a self-hosted Mac using the worktree clone trick, or in the release chain once the checkpoint fix lands. Protect `main` with "tests pass". *Cost: Python 1 hour; C++ 1–3 days plus a machine.*
7. **Keep the event contract and quiet rows as the UI seam.** `agent_events.cc` → `parseAgentEvent` is a single, capped, typed boundary. A rebuilt assistant UI can replace `app.ts` without touching the controller. *Cost: none to keep.*
8. **Keep the Arc spring and collect motion into tokens.** One C++ header and one CSS file for durations and curves (today about 15 files hold literals). Keep Reduce Motion handling as is. *Cost: 1–2 days.*
9. **Encrypt chat history at rest** with the same `os_crypt_async` path used for keys. *Cost: 1–2 days, plus a migration of existing files.*
10. **Put one seam around Chromium's AI internals.** Route every APC and actor call through `apc_extract` and `renderer_tools` (already partly so), so a Chromium change breaks one file. *Cost: about 1 week.*
11. **Fix public claims and doc drift.** "Thin layer", "It asks before it acts", the Apple-account notes, the four-week cadence, the missing `acp-design.md`. *Cost: hours.* (Site edits deploy to production on push, per `docs/operations/site.md:72-75`.)
12. **Gate the dev harness out of release builds,** or keep it only in a signed "test" variant. Especially `--rac-window-screenshot-requests`, which can drive the browser. *Cost: hours, plus a CI variant if the harness must run on release artifacts.*

### Avoid

- **Adding features as more edits to hot upstream files** (`browser_view.cc`, `browser_view_tabbed_layout_impl.cc`, `vertical_tab_strip_region_view.cc`, `tab_strip_model.cc`, `prefs_util.cc`, `settings_localized_strings_provider.cc`). Each is already patched by 3–37 Helium or ungoogled patches and 4–13 rac patches (for example `settings_localized_strings_provider.cc`: 37 and 13; `browser_view.cc`: 13 and 9). FACT for counts.
- **Landing big features as chains of follow-up fix patches on `main` without CI.** The 121 fix commits and 658 self-edits are the result. FACT.
- **Expanding the agent (outside agents, automations, hand-off) before injection evals exist.** Capability grows the blast radius of the known `auto` chain. INFERENCE.
- **Growing `app.ts` further.** A 2,822-line hand-built page with English-only strings is a poor base for a design-led revamp; choose a structure (Chromium already ships Lit) first. INFERENCE.
- **Assuming a four-week Chromium cycle** in any schedule. FACT that it is two weeks.
- **Publishing a design system built on values lifted from Arc's and Dia's asset catalogs and palettes** without deciding that this is acceptable. The comments cite those catalogs. FACT for provenance; risk is INFERENCE.
- **Treating "every message cold-starts the agent" as fixed for interactive features.** It is a deliberate choice (`ai.md:713-715`), but it costs 15–25 s per message. Revisit it explicitly rather than building more on it. INFERENCE.
- **More layouts and toggles.** Two layouts and a right sidebar already strain "opinionated" and the screenshot matrix. INFERENCE.

## Open questions and things you could not verify

- **Visual quality.** I did not launch rac. No screenshots, no video, no feel. All look-and-motion notes come from code.
- **Performance.** No benchmark exists anywhere in the repo, so "never slower than Helium" and "AI off costs nothing" are unmeasured. FACT that no benchmark exists.
- **Real sync cost.** I measured exposure (files and hunks in Helium-patched files), not actual conflicts. GitHub's compare API stops at 300 files, so my counts of changed Helium patches are lower bounds.
- **Whether Chromium 155–156 changed the APC and actor APIs** rac uses. Not checked.
- **Whether Helium 0.19–0.20 added features rac duplicates** (vertical tabs, zen mode, split view, AI). `VISION.md:136-138` says rac should consider adopting Helium's version. Not checked.
- **The siso checkpoint fix.** The diagnosis is another agent's report; PR #20's validation run was still in progress.
- **Empty `MAC_TEAM_ID` under a real Developer ID.** Effects on keychain access groups, passkeys, or entitlements are unknown.
- **Update check interval.** Mostly resolved: the build writes `SUScheduledCheckInterval` = 3600 s and the glue turns automatic checks on (`build/src/chrome/browser/mac/sparkle_glue.mm:368`, main checkout; see [What leaves the machine](#what-leaves-the-machine-defaults)). Not yet observed on a real install.
- **Exploitability of the `auto` chain.** Policy confirmed; no model was tested.
- **Helium's services for a fork.** No agreement exists for rac to use Helium's extension, filter list, spell check, and bangs servers. Whether imput minds is unknown.
- **Audit numbers I did not redo:** repo traffic, PR merge-time medians, and per-week commit counts. I re-verified commits, trailers, PR states, reviews, runs, secrets, branch protection, and upstream gaps.
- **Translations of rac's 100 grit strings.** Whether they pick up translations in release builds was not checked; assistant strings cannot.
- **The main checkout's build** is 71 commits behind `main`, so the maintainer's daily build may not include PRs #11–#19. Unverified which build the maintainer runs day to day.

## Sources

Repository (read at `d3f0d66`, worktree `/Users/knewton/.t3/worktrees/rac/t3-bb0e4397`):

- `VISION.md`, `AGENTS.md`, `README.md`, `CONTRIBUTING.md`
- `docs/roadmap.md`, `docs/internals/{ai,overview,glossary,pinned-tabs,pinned-tabs-drag,picture-in-picture,bangs}.md`, `docs/operations/{releases,upstream-sync,worktrees,site}.md`
- `patches/series` (rac entries at lines 29–208) and all 180 files in `patches/rac/*/`
- Final-state rac files reconstructed at `/tmp/rac-overhaul/racfiles` by `/tmp/rac-overhaul/scripts/extract.py` plus `patch -p1`; patch statistics by `/tmp/rac-overhaul/scripts/patchstats.py`; Helium overlap by `/tmp/rac-overhaul/scripts/overlap.py`
- `.github/workflows/{build,building,build-phase,sanity,lint,pullfrog}.yml`, `.github/scripts/{sanity-check,github_build,github_prepare_artifacts}.sh`, `.github/actions/do-build/action.yml`, `sign_and_package_app.sh`
- `devutils/rac/*` (tool tests, `test-spaces.mjs`, `worktree.sh`, `sparkle.py`), `resources/branding.txt`
- `site/src/config.ts`, `site/src/pages/index.astro`, `site/package.json`
- `helium-chromium/chromium_version.txt`, `helium-chromium/patches/series`, `helium-chromium/AGENTS.md`
- Main checkout (read-only): `/Users/knewton/Dev/Github/rac` at `9b4d949`; `build/src/chrome/browser/ui/views/frame/browser_view.cc:443-444`; `build/src/chrome/browser/mac/sparkle_glue.mm:368`
- Context: `plans/context/maintainer-brief.md`, `plans/context/ci-status.md`, `plans/context/inboxzero/rac-audit.md` (with its ERRATA), `plans/context/roadmap-revision-2026-10-22.md`, `plans/context/competitors-ardia-yab-2026-10-23.md`; `/tmp/rac-siso-checkpoint.md` (another agent's CI report)

GitHub (read-only `gh` calls, 2026-10-25):

- `gh api repos/notkainoa/rac` (metadata), `.../releases`, `.../pulls?state=all`, `.../pulls/{1..19}/reviews`, `.../branches/main/protection`
- `gh run list -R notkainoa/rac` for `build.yml`, `sanity.yml`, `pullfrog.yml`; `gh run view 40149762883`
- `gh secret list -R notkainoa/rac` (names only)
- `gh api repos/imputnet/helium-macos/releases`, `.../compare/0.18.2.1...0.20.1.1`, `.../compare/<d3f0d66>...main`, `.../contents/helium-chromium?ref=<tag>`
- `gh api repos/imputnet/helium/compare/76141e1...f29a259`, `.../contents/chromium_version.txt?ref=<sha>`

Web:

- Chrome two-week release cycle: https://developer.chrome.com/blog/chrome-two-week-release
- Milestone schedules: https://chromiumdash.appspot.com/fetch_milestone_schedule?mstone=154 , `?mstone=155`, `?mstone=156` (via search), `?mstone=157`
- Chrome 156 stable: https://chromereleases.googleblog.com/2026/10/stable-channel-update-for-desktop_02018666648.html
- Coverage of the switch: https://techcrunch.com/2026/09/08/chrome-is-now-shipping-updates-every-2-weeks-as-ai-changes-the-security-landscape/ , https://9to5google.com/2026/03/03/chrome-two-week-updates/
- Extended Stable milestone names (156, 160) come from a web search summary of secondary coverage, for example https://www.androidenterprise.community/product-updates/chrome-browser-moving-to-a-2-week-release-cycle-2435 (not fetched directly)
- rac's site: https://racbrowser.com

## Verification

Adversarial fact-check, 2026-10-25. I re-checked 32 load-bearing claims against primary sources: the repo at `d3f0d66`, `git`, read-only `gh api` / `gh run` / `gh secret list`, the main checkout's applied tree (`/Users/knewton/Dev/Github/rac/build/src`), and Google's own release pages. I did not trust the author's reconstruction blindly. I rebuilt 10 rac files from `patches/series` with my own script (`/tmp/rac-overhaul/fc/scripts/recon.py`), and all 10 matched `/tmp/rac-overhaul/racfiles` byte for byte. I also recounted the patch statistics with my own parsers (`/tmp/rac-overhaul/fc/scripts/{count,overlap,perpatch,hot}.py`). Nothing was built or launched.

### In plain English

Most of this dossier holds up. I checked 32 of its biggest claims against the code, git, GitHub, and Google's pages. 26 were right as written. Six needed a fix, and none of the fixes changes a conclusion. The biggest: favorites show at most 3 per row in the full sidebar, not 4. Only one test checks "AI off", not six. I also found a third public promise. Onboarding says the AI "never acts in your browser without your confirmation", which the default `auto` level breaks. Three things the author had only marked as reported are now confirmed. rac needs macOS 13. Helium switched its build tool to siso on 2026-09-13. Installed copies check for updates hourly. Along the way I fixed five smaller slips, listed under Other edits. The patch counts, Helium overlap, test counts, release history, and agent defaults all matched my own recount exactly.

### Claims checked

| # | Claim | Primary source I used | Result |
| --- | --- | --- | --- |
| 1 | Chromium 154.0.8037.92, Helium 0.18.2.1; `main` = tag `0.18.2.1` + 286 commits, behind 0 | `helium-chromium/chromium_version.txt`; `git rev-list --count 0.18.2.1..d3f0d66` = 286, reverse = 0 | Confirmed |
| 2 | helium-macos 0.20.1.1 = Chromium 156.0.8078.47; 6 releases ahead; 0.17/0.18/0.19/0.20 = 153/154/155/156 | `gh api .../helium-macos/releases`, submodule SHA per tag, then `imputnet/helium` `chromium_version.txt` | Confirmed. Added the source of the brief's "seven" (`rac-audit.md:226` lists a nonexistent 0.19.1.1) |
| 3 | Chromium two-week cadence from M153 (2026-09-08); M154–M157 stable dates; Extended Stable stays 8 weeks | developer.chrome.com/blog/chrome-two-week-release; chromiumdash `fetch_milestone_schedule` for 154–157 | Confirmed |
| 4 | GPL-3.0; fork of `imputnet/helium-macos`; 0 stars/forks/watchers; 0 non-PR issues; created 2026-10-02 | `gh api repos/notkainoa/rac`, `.../issues?state=all` | Confirmed (`open_issues_count` 1 is PR #20) |
| 5 | 269 non-merge commits, all by one author; 259 with AI co-author trailers; trailer counts | `git log --no-merges 0.18.2.1..d3f0d66` | Confirmed. 12 distinct days is for non-merge commits; 13 with merges (edited) |
| 6 | 189 of 269 commits landed on `main` directly | `git rev-list --first-parent --no-merges --count` = 189 | Confirmed |
| 7 | 20 PRs: #1–#5 closed unmerged, #6–#19 merged, #20 open | `gh api .../pulls?state=all` | Confirmed |
| 8 | 112 reviews, all `COMMENTED` (74 maintainer, 25 cubic, 13 greptile), 0 approvals | `gh api .../pulls/N/reviews` for N = 1–20 | Confirmed |
| 9 | No branch protection on `main` | `.../branches/main/protection` → 404; also `.../rulesets` and `.../rules/branches/main` → `[]` | Confirmed, and no rulesets either |
| 10 | 0 releases; `build.yml` runs: 3 failed, 1 cancelled, 1 in progress; dry run 40149762883 did three ~5 h phases per arch and was cancelled in phase 4 at 18:08Z | `gh api .../releases`; `gh run list`; `gh run view 40149762883` job times | Confirmed. Sanity and Pullfrog counts updated to the later values |
| 11 | 9 release secrets exist; entitlements profile absent; `MAC_TEAM_ID` empty | `gh secret list`; `.github/workflows/*.yml` secret refs; `branding/identity.patch:32-33` | Confirmed |
| 12 | Sanity passes only when the 30 s build is still running | `.github/scripts/sanity-check.sh:56-57` (`test "$_status_code" -eq 124`) | Confirmed |
| 13 | CI references no rac test target | grep of `.github/` for `rac_*_unittests`, `rac_pip_tests`, Python tests, `test-spaces` | Confirmed (no hits) |
| 14 | 180 rac patches at series lines 29–208; 110,741 patch lines; 24 `fix-*` patches | `patches/series`; `wc -l`; `ls` | Confirmed |
| 15 | 435 upstream entries, 869 hunks, 216 files, +3,429/−1,049; 320 hunks in `ui/views`; 66 patches with no upstream hunk; 36 files hit by ≥3 patches; `ui/BUILD.gn` 26 | My own parser over all 180 patches | Confirmed exactly |
| 16 | 139 of 216 upstream files are also Helium/ungoogled-patched, holding 663 hunks (76%); hot-file counts (37/13, 13/9, 28/11, …) | My own overlap parser over `helium-chromium/patches/series` and `patches/series` | Confirmed exactly |
| 17 | "343 Helium core entries" | `helium-chromium/patches/series` | Partly wrong framing: the 343 include 71 ungoogled-chromium and 18 other entries. Edited |
| 18 | Upstream removed `retrieve_and_unpack_resource.sh` and `devutils/build_tools.sh`, which rac's scripts call | `gh api .../compare/0.18.2.1...0.20.1.1` (15 commits, 32 files); 404 for both files at 0.20.1.1; `devutils/shared.sh:12,31,35`; `sanity-check.sh:16-17` | Confirmed. Added the 5 other changed or added files the list missed |
| 19 | Helium core moved 85 commits, ≥199 `patches/helium/*` files, ≥206 patch files | `gh api imputnet/helium/compare/76141e1...f29a259` (300-file cap) | Confirmed |
| 20 | AI defaults: off; browser control on; level `auto`; attach tab on; save history on; AI new tab page on | `ai_prefs.cc:25-37` in both reconstructions; `agent/13-permission-levels.patch:561`, `ai/01-prefs-settings.patch:138` | Confirmed, line numbers exact |
| 21 | Test `AutoAsksOnlyForRiskAndForeignTyping` allows cross-site `navigate` and model text typed into the attached tab at `auto` | `action_guard_unittest.cc:196-223` (own rebuild) | Confirmed. Added that the test turns off URL provenance for `navigate` |
| 22 | Provider default models; ACP recipes and pinned npx versions; Copilot denies shell/write/url | `providers.cc:17-38`; `agent_recipes.cc:23-82`; `ai/21-agent-providers.patch:662,668` | Confirmed |
| 23 | MCP protocol versions; 25-call step cap; ACP timeouts 45 s / 3 s / 90 s; critic 4 s and 4,000-byte goal; settle caps 4 s / 10 s | `mcp_protocol.cc:20-21`; `chat_protocol.h:24` used at `agent_controller.cc:369` and `chat_session.cc:195`; `acp_client.cc:201,552`; `acp_client.h:24`; `agent_controller.cc:755`; `critic_protocol.cc:17`; `action_runner.cc:232-324` | Confirmed. MCP line numbers corrected; `mcp_server.cc` is 672 lines, not 680 |
| 24 | 15 agent tools | `tool_registry.cc:87-262` | Confirmed |
| 25 | Chat history is plaintext JSON at `<profile>/rac_ai_history.json`, 16 MB read cap, `ImportantFileWriter`; keys are `os_crypt_async` ciphertext under keychain "rac Storage Key" | `ai_service.cc:26`; `history_store.cc:18`; `history_store.h:26,52`; `key_store.cc:20-34`; `branding/identity.patch:53` | Confirmed (no encryption call in the history code) |
| 26 | Link summaries use a throwaway off-the-record profile with JS, images, plugins off and cookies blocked | `chrome/browser/rac/ai/link_fetcher.cc:40-57` | Confirmed in code, not only docs |
| 27 | Motion values: Arc spring ω = 2π/0.25 s, 0.5× drag, rubber band 0.15/255, flick 300, 240 Hz sampling ≤1.5 s, 150 ms cross-fade; sidebar 180/140 ms; swipe 15/75 DIP, 300 ms; edge-reveal 100 ms dwell, 150→300 ms, 350→100 ms, velocity heuristic off, Helium's 200 ms; indicator 240/160 ms `EASE_OUT`; drag 150/100 ms; CSS curves and infinite loops | `space_pager.cc:44-63,307-330` (own rebuild); `spaces/sidebar-motion.patch:282-284`; `spaces/switcher.patch:206-209`; `sidebar-reveal/edge-reveal.patch:1-20,80-90`; main checkout `browser_view.cc:443-444`; `agent_tab_indicator.cc:89-90,144-153`; `drag_snap.cc:23,35`; `app.css:175,547,553,934,1074` | All values confirmed. "Reduce Motion handled everywhere" was overstated: two hover fades skip it. Edited |
| 28 | Favorites: 44×44 tiles, up to 4 per row | `sidebar_style.cc:46-53` (`kMaxColumns = 3`); `sidebar/favorite-grid.patch:78-85`; main checkout `pinned_tab_container_view.cc:423` | **Wrong.** In the full sidebar, tiles stretch, at most 3 per row; 4 per row and 44 px width apply only outside the full state. Fixed in two places |
| 29 | "`ai/14-off-audit.patch` adds 6 pref tests" | per-patch count of `+TEST` lines in `ai_prefs_unittest.cc` sections | **Wrong.** It adds 1 (`MasterSwitchGatesEntryPoints`); `22-agent-settings-ui` adds 1, `model-chips` adds 4. Fixed |
| 30 | 278 test cases in 33 files across 5 targets; 71 Python tool tests | grep of the final-state files; the 5 `test(...)` targets in `BUILD.gn`; `def test` count in `devutils/rac/test_*.py`; 284 `+TEST` lines across patches matches the audit's "about 284" | Confirmed |
| 31 | Updates hourly (was CLAIM); macOS 13 minimum (was CLAIM); ninja→siso on 2026-09-13 (was CLAIM) | `sparkle2-integration.patch:28,174` + `fixup-sparkle-glue.patch:614-633` + `devutils/shared.sh:59-69`; main checkout `build/config/mac/mac_sdk.gni:29`; helium-macos commit `5a87a3e` (#359) | Upgraded to FACT (the live update schedule stays INFERENCE from Sparkle's key) |
| 32 | No rac endpoints in code; public "asks before it acts" promises | URL-host scan of all `+` lines in `patches/rac` and of the final-state files; grep of `site/`, `README.md`, onboarding | Endpoints confirmed (only provider defaults, the GitHub feed, Helium's policy links, and test hosts). Found a third promise, in onboarding (`rac_onboarding/index.html:44`). Added in three places |

### Other edits

- The roadmap revision's "42 / 21 patches" was not drift. It was right at `9b4d949` (2026-10-22); PR #11's fold made it stale. Reworded in two places.
- "PR #11 did this for 13 agent patches" → 13 fix patches, 6 ai and 7 agent. PR #11 kept 7 more separate on purpose because each fixes several patches (`git show 6ffec8a`). Fixed in Take 4.
- "One window per profile" misread `VISION.md:64-68`. A profile can have several windows. Each window shows one space, and a space is open in at most one window (`spaces_window_manager.h:50-53`).
- `optimization_guide::` use: 34 references in 18 non-test files (21 with tests), not 23 files.
- "Focus ring `#6395FC`" is the URL pill's focused border (`kColorRacUrlPillBorderFocused`).
- Small citation fixes: `build.yml:23`, `rac_color_mixer.cc:97`, `spaces_store.h:50-74`, `mcp_server.cc:46`. Added that Sync also sits in the roadmap's "Later" list (`docs/roadmap.md:158`). Added the `BUILD.gn` line that shows the dev harness is ungated, and the code source for the version guard.

### Not re-verified

- The siso stale-mtime diagnosis (50,287 of 59,933 reruns) and the bsdtar "restricted pax" explanation. The numbers match `/tmp/rac-siso-checkpoint.md:37-39`, which is another agent's report. I did not read the CI artifact or libarchive. It stays CLAIM.
- "At least 117 of rac's upstream files (624 hunks) sit in files that changed Helium patches touch." This needs the content of 206 changed Helium patches, and I did not fetch it.
- Extended Stable milestone numbers (156, 160): secondary source only.
- Per-file line counts in the directory table, except the ones I spot-checked (`app.ts` 2,822, `app.css` 2,484, `rac_ai_page.{html,ts}` 553/760, the directory totals, 323 live files and 63,030 lines). Those matched.
- The ACP start-up times (15 s / 25 s) are the maintainer's own measurement in `docs/internals/ai.md:708-718`. They stay CLAIM.

### Confidence

High for the numbers, licenses, storage, agent defaults, CI and release facts, and the upstream gap. Each was reproduced from a primary source, and most exactly. Medium for the motion and UI descriptions. The values are right, but nothing was looked at on screen, and one layout claim (favorites per row) was wrong in a way only the call site showed. The plans' cost estimates and judgments are INFERENCE and were not fact-checked.
