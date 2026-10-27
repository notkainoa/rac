# Zen Browser — planning digest

Source dossier: `plans/research/zen.md` (researched 2026-10-25 against
`zen-browser/desktop` at `9b604fe` and `surfer` at `b3fc8ab`; clones in
`/tmp/rac-overhaul/src/{zen,surfer}`). Its Verification section (44 items
re-checked) is authoritative here. Tags: **FACT** = primary source,
**CLAIM** = self-report, **INFERENCE** = reasoning.

## In plain English

Zen is a free, open-source Arc clone built on Firefox. It has vertical tabs,
spaces, favorites ("Essentials"), a link-peek (Glance), split view, and a
hide-until-hover sidebar (Compact Mode). No AI — the lead developer actively
turns Firefox's AI off. One person writes 85% of the code and ships a release
every ~5.4 days; each Firefox release lands within days. Users love the look
but complain about lost tabs, performance, and defaults they can't turn off.
For rac: process lessons (a sync bot, cheap UI rebuilds, a motion grammar)
plus three features (tab backups, Glance, forgiving edge reveal). rac already
matches Zen's patch-surface size — the architecture is a proven shape, but
the UI tech differs (see caveats).

## Key facts

- Arc-style browser on Gecko. Stable ships Firefox 158.0.1; on 2026-10-25
  `dev` synced the Firefox 159.0 release candidate; still beta ("1.23.4b")
  after 195 releases (**FACT**: `zen/surfer.json`; releases).
- License MPL-2.0, no files marked "Incompatible With Secondary Licenses"
  (**FACT**); adapting into GPL-3.0 rac with credit and retained MPL notices
  is possible (**INFERENCE**, not legal advice).
- 45,275 stars (2024-03-28); 30.3 M release-asset downloads all-time; 63,277
  macOS update-file downloads in the 4 days after 1.23.4b (install proxy —
  INFERENCE) (**FACT**: GitHub API). macOS universal DMG, Windows x64/arm64,
  Linux x64/arm64.
- Cadence: 67 stable releases in 12 months (~1 per 5.4 days); "Twilight"
  nightly every 2 days (**FACT**).
- One lead (`mr-cheffy`, formerly `mauro-balades`): 85% of all commits, sole
  `CODEOWNERS` entry; donations only, no accounts (account link INFERENCE
  from issue #7000). (**FACT**: API, `zen/README.md`).
- **Spaces** (code: "workspaces"): name, emoji, gradient theme; each can bind
  a Firefox **container** (separate cookie jar). Switch by swipe,
  Ctrl+scroll, keyboard, footer; wrap-around. Swiping past the last space
  creates a new one; past the first opens the Library. **Essentials** (rac
  favorites): max 12, per-container sets. **Pinned tabs per space**:
  remembered URL; 6 Cmd+W options, default `reset-unload-switch`; restore on
  demand at startup. **Folders**: nested max 5 levels, hover-to-search after
  500 ms (1.15b). **Live folders** (1.19b): auto-refresh from RSS/Atom or
  GitHub (default 30 min; the GitHub provider scrapes with your cookies —
  no API token) (**FACT** for all).
- **Window sync** (1.18b, on by default, **no settings toggle** — only
  `about:config`): every window mirrors the same tabs; picking a tab moves
  its live page into the focused window; others show a dimmed preview
  (**FACT**: `ZenWindowSync.sys.mjs:41-70`).
- **Space routing** (Arc Air Traffic Control, 1.21b): "contains",
  "equal-to" (Verification #17), case-insensitive regex; context menu
  "Add route for domain"; external links routed at startup (1.23.4b)
  (**FACT**: `ZenSpaceRoutingManager.sys.mjs:487-516`).
- **Library panel** (1.23b): history, downloads, media, spaces, boosts, space
  routing; Opt+Shift+L or swipe. **Split view**: up to 4 tabs, 5 ways in
  (**FACT**).
- **Command bar**: floating address bar default (`floating-on-type`; Cmd+T
  opens it instead of a new tab page); ~40 declarative actions with
  `l10nId`/`command`/`icon`/`isAvailable`; per-command learned score −5..+5
  in one pref (**FACT**).
- **CLI**: only `--space <name|UUID> [url]` and `--blank-window [url]`. No
  scripting CLI, no MCP, no API (**FACT**).
- **AI**: none, deliberately — every Firefox AI/ML pref locked off, AI Window
  hook neutered; visible anti-AI community voices (**FACT**: `ai.yaml:6-28`;
  discussions #12762, #14678). **No agent** of any kind (**FACT**).
- Telemetry locked off (20+ prefs), Mozilla promos off, GPC on, crash
  reporter not compiled, uBlock offered at onboarding (not bundled);
  speculative preconnect to Essentials kept on ("No, it won't be disabled by
  default") (**FACT**: `privacy.yaml:6-90`; issue #7000).
- Profile at `~/Library/Application Support/zen/Profiles/<id>/` (**CLAIM**:
  bleachbit PR #2394).
- **Session store**: `zen-sessions.jsonlz4` (LZ4 JSON) replaced a
  `places.sqlite` table; Firefox's sessionstore still written too, so its
  save interval was raised 15 s → 40 s. **Backups**: one file per 3-hour
  bucket, newest 20 kept (can cover as little as ~60 h — INFERENCE), at most
  every 10 min; `clean.jsonlz4` = **the previous file copied aside before
  every save** (not a clean-shutdown copy — Verification #7). Recovery: if
  the loaded file has no spaces, Zen tries **exactly two** more files —
  `clean.jsonlz4`, then the newest bucket; nothing encrypted at rest beyond
  Firefox's own (**FACT**:
  `ZenSessionManager.sys.mjs:30-58,105-190,254-279,600-707`).
- Cross-device spaces sync is a custom Firefox Sync engine ("Spaces",
  version 3; six record kinds: container/space/tab/folder/split/layout),
  opt-in on stable, default on in Twilight; a wipe never deletes local data
  (**FACT**: `ZenSpacesSync.sys.mjs:70-72,125,140`).
- Process model: parent runs chrome UI + all Zen JS; pages in site-isolated
  content processes; Zen↔page via Firefox per-window actor pairs (**FACT**).
- **Integration**: `surfer download` fetches a Firefox source tarball from
  archive.mozilla.org — patches on a tarball, not a git fork (**FACT**:
  `surfer/src/commands/download/firefox.ts:139-173`). **One patch per
  upstream file**, applied with `git apply --ignore-space-change
  --ignore-whitespace` in glob order, no series file; warn at 8,000 chars.
  New files under `src/` are **symlinked** into `engine/`, so editing them
  needs no patch refresh; the `browser.xhtml` hook is +5/−1. External
  patches (pending Mozilla diffs, one LibreWolf patch) pulled by manifest ID
  (**FACT**: `surfer/src/commands/export-file.ts:9-60`, `copy-patches.ts:34-130`).
- **Patch surface**: 264 own patches, 868 hunks, +3,677/−1,052; 7 external
  patch files add 90 hunks over 27 files; together 958 hunks over 287
  upstream files (Verification #33); biggest `Tabbrowser.sys.mjs` at 101
  hunks. rac comparison: ~180 patches, 871 hunks, 217 files — similar
  footprint; the difference is ~83,000 raw lines of feature code in **new
  files** under `src/zen/` (~67,500 JS, ~12,500 CSS, ~3,200 C++/Obj-C++)
  (**FACT**: Verification #35).
- **UI is HTML/CSS/privileged JS** (the Firefox chrome document), so a
  UI-only rebuild is `npm run build:ui` → `mach build faster` (front-end
  only) — a structural advantage over Chromium's C++ Views (**FACT** for the
  mechanics; comparison INFERENCE). Prefs: 40 YAML files (28 Zen's) compiled
  by a Rust tool; 156 declared `zen.*` prefs (**FACT**).
- Tests: ~683 test files (184 Zen's + ~500 imported + C++ Boosts) —
  **CI runs none**; PR check is apply+lint only; `dev` has no required
  checks (**FACT**: `pr-test.yml`; Verification #29).
- **macOS cross-compiled on Linux** (8-vCPU CI runners): 42–49 min
  per architecture cold (sccache off in run 39497770166); full 3-stage PGO
  pipeline ~4.5 h; only 2 steps need a Mac (profile collection, universal
  merge/sign/notarize). Chromium has no official macOS-on-Linux build, so
  rac can't copy this (**FACT** for Zen; Chromium statement INFERENCE).
- **PGO trained on Zen's own UI**: tab switch ×200; compact mode, sidebar
  hover, Glance, Library, space switch, address bar ×50; split ×20; folders
  ×30; Boosts ×10. Profiles cached but **only Twilight reuses them** (c-25);
  LTO `cross,thin`; arm64 `-mcpu=apple-m1`; release flags `--enable-release`,
  `--disable-tests`, `--disable-crashreporter`, `--disable-geckodriver`
  (**FACT**: `ZenPGOTraining.sys.mjs:38-49`).
- Signing: macOS `rcodesign` (.p12) + `notarytool` + stapler; Windows
  `signtool` with a named identity and Certum's timestamp server (cert
  INFERENCE; manual Windows signing step INFERENCE, backed by a ~12 h gap
  before publish). Publish needs a reviewer in the `Deploy-Release`
  environment (**FACT**: Verification #27).
- **Updates**: Firefox's updater with Zen's own 4,096-bit RSA MAR key valid
  to year 9999; static `update.xml` on GitHub Pages
  (`updates.zen-browser.app`); full packages only (macOS 170.5 MB), no
  deltas — ~220 MB/week per Mac at their cadence (weekly total INFERENCE)
  (**FACT**: `mar_sign.sh`; Verification #6, #22, #23).
- **Security**: until 1.19.9b (2026-04-24) the updater shipped with
  signature checks removed, serving unsigned updates (GHSA-qpj9-m8jc-mw6q,
  high). Also GHSA-vpvg-hp3v-rm5q (context menus loading page links with
  system privileges; low), GHSA-vjfv-85qf-v25c (fullscreen hid the origin
  warning; high), GHSA-7p2r-fp29-9w69 (address-bar spoofing; medium)
  (**FACT**: Verification #21).
- **Sync bot**: weekly Tuesday 04:59 UTC job pings on a Firefox release
  candidate and opens a bot PR re-applying all patches, reporting "applies
  cleanly" or naming failures. Zen synced Firefox 155–159 within days;
  Firefox 2-week majors started with 155 (2026-09-01), Chrome with 153
  (2026-09-08) → Helium/rac sees upstream releases twice as often
  (**FACT**; cadence implication INFERENCE).

## What rac should take (ranked)

Cost: XS <1 d; S 1–3 d; M 1–2 w; L 3–6 w. "Thread" = UI or architecture.

1. **Automatic backups of spaces/pinned tabs/favorites with ordered recovery**
   — S–M, architecture. Save in 3-hour buckets, keep newest 20 **plus one
   file per day for older days**, keep a copy of the previous save, and try
   *every* backup newest-first on load failure (Zen tries only two). Data
   loss is Zen's most common complaint: 230 issues mention "lost" tabs, 99
   "pinned tabs gone", 48 "workspaces disappeared" (e.g. #5817, #12028 right
   after the 1.18 session-file move).
2. **Upstream-sync bot PR on a schedule** — S, architecture. Weekly CI job:
   check for a new helium-macos tag, bump on a branch, test patch application
   (no full build), open a PR stating "applies cleanly" or listing failures.
   Source: `sync-upstream.yml`, `check-candidate-release.yml`.
3. **Glance (link peek)** — L, UI. Opt-click opens a live overlay at 80%
   width; page behind scales to 0.97, dims to 0.3; outside links clicked
   inside favorites open in Glance. Motion: open from the link's box along
   an arc (91 keyframes, 350 ms, easeOutBack 0.6, arc cap
   min(0.4×dist, 30 px, 0.6×free space)), close with `1-(1-t)^6`, background
   spring bounce 0.2 / 0.35 s. **Load with the initiator's origin, never
   privileged** (Zen's GHSA-vpvg bug). Source: `ZenGlanceManager.mjs`.
4. **Forgiving edge reveal** — S, UI. While the revealed sidebar shows and
   the pointer leaves the window, an `NSEvent` monitor keeps it open within
   200 px sideways / 100 px vertically, gives up past the offset; keep open
   150 ms after leaving; hide the toolbar 1,000 ms after hover. Monitor runs
   only under those conditions — nothing when unused. Three of Zen's top
   6-month issues were this bug pre-fix (#15995, #16002, #16054). Source:
   `compact-mode.yaml:14-28`, `ZenMouseTrackerCocoa.mm`.
5. **Arc import following Zen's field mapping** — M, architecture, time-boxed
   (Arc closes 2026-12-22). History/passwords via Chromium's Chrome importer
   pointed at Arc's "User Data"; parse
   `~/Library/Application Support/Arc/StorableSidebar.json` for spaces,
   favorites (`topAppsContainerIDs`), pinned tabs and folders from
   `["pinned", id, "unpinned", id]` pairs, emoji, theme colors;
   containers→spaces. Dia pinned tabs can't be imported (encrypted DB) —
   say so plainly. Source: `ZenMigrationUtils.sys.mjs:88-330`.
6. **Declarative command-bar action table + learned ranking** — S–M, UI.
   String ID, command, icon, `isAvailable(window)` per action; per-action
   score −5..+5 learned from use. Makes "ways in" auditable in one file.
   Source: `ZenUBGlobalActions.sys.mjs`, `ZenUBResultsLearner.sys.mjs`.
7. **UI perf bench driving real flows** — M, architecture. Script tab switch
   ×200, sidebar reveal ×50, space switch ×50, command bar ×50, split ×20,
   folders ×30; record frame times and CPU vs Helium — turns "never slower
   than Helium" into a number. Source: `ZenPGOTraining.sys.mjs:38-49`.
8. **A written motion grammar** — XS doc + S to apply, UI. Zero-bounce
   springs for structure (space switch 250 ms, bounce 0, safety timeout
   duration+50 ms); exits faster than entries (tab open 120 ms scale
   0.95→1, close 100 ms); small bounce only on arrivals (toast 0.2, split
   drop 0.4); 0.98 press scale; swipe rubber band (1 − |x|/(4.5×strip
   width)); a hard per-animation timeout so input is never blocked. Full
   parameter table: dossier lines 200–224.
9. **Small Arc behaviors Zen proved popular** — S each, UI. Back with no
   history closes the tab; Cmd+W on pinned tab = reset, unload, switch away;
   "Unload all other spaces"; tab rename + custom icon; pinned tabs load on
   demand at startup.
10. **Haptic ticks on snap points** — XS, UI.
    `NSHapticFeedbackPatternAlignment` when a dragged tab snaps into
    favorites/folders/split.
11. **Space routing with rule types** — M, UI+architecture (on rac's
    roadmap already).
12. **Theme harmony presets** — S–M, UI, if rac allows multi-color themes:
    complementary 180°; split-complementary 150°/210°; analogous 50°/310°;
    triadic 120°/240°; grain-opacity slider.

## What rac should avoid

1. **Mirroring every window by default with no toggle.** #12008 (81
   reactions) vs 416 voters requesting it in #924 — the failure was forcing
   it on with no setting; one window's tab change even exited fullscreen in
   another ("It will never be disabled by default" — lead dev, 2026-01-25).
   (**FACT**)
2. **Effects that defeat compositor caching.** Rounded content corners kept
   WebRender from caching scrolled layers (#6302, 117 reactions; 30–45% GPU
   use reported; blend-mode theory retracted; fixed for Zen with Firefox 141
   — Verification #37). Measure scroll CPU/GPU with and without any edge
   decoration before shipping it. (**FACT**)
3. **Shipping updates without signature checks, even once.**
   GHSA-qpj9-m8jc-mw6q; rac's Sparkle EdDSA key must stay mandatory. (**FACT**)
4. **Privileged loads of page-chosen URLs** from new surfaces (peek, split,
   command bar). GHSA-vpvg-hp3v-rm5q. (**FACT**)
5. **Hiding security UI in compact layouts** — fullscreen origin notice
   (GHSA-vjfv, high), address-bar origin display (GHSA-7p2r, medium).
   (**FACT**)
6. **Forcing a new interaction with no way back** — the floating address bar
    needed an opt-out after 90 reactions (#3539); window sync never got one.
    (**FACT**)
7. **First-run network calls to third-party sites** — ~45 first-run
   connections pre-fix (issue #7000); bundle default-favorite icons
   locally; don't preload favorites. (**FACT**)
8. **Storage migrations without a preceding backup** — loss reports cluster
   around UI/storage changes (#5817, #12028; causal link INFERENCE).
   (**FACT** for the pattern)
9. **Tests CI never runs** — Zen's gap and rac's exact gap today. (**FACT**)
10. **Full-size updates every release** — Sparkle supports deltas; Zen's
    170 MB no-delta updates waste ~220 MB/week per Mac.
11. **A settings surface of 150+ prefs** (156 declared, mostly
    `about:config`-only) — contradicts rac's "opinionated" principle.
12. **A hosted share-link server** — Zen's share needs a Cloudflare Worker
    (KV, 30-day retention, 25 MiB cap, 2 creates/min per client IP,
    `share.zen-browser.app`) and an API key built into each release —
    conflicts with "nothing phones home" (mechanics FACT; conflict
    INFERENCE).

**Not transferable:** macOS cross-compile (Firefox-only — INFERENCE), 45-min
engine builds vs rac's ~130k-step Chromium build (the CI gap is the engine
— INFERENCE from FACT numbers), cookie-isolated spaces (Firefox containers;
Chromium can do this too, via a fixed StoragePartition per space as Stedding and Brave Containers do; see the long-tail digest, which corrects an earlier claim here),
HTML/CSS chrome UI (CSS `linear()` springs and front-end-only rebuilds vs
rac's Views `gfx::Tween`; a WebUI surface could get similar tools at
memory/startup cost — open choice for heavy panels like Library).

## Caveats

- **No AI, no agent, no MCP** — the dossier contributes nothing on agent
  mechanics, permissions, or injection defense; look to ego(lite), Ardia,
  and Aside for those (per the maintainer brief).
- The transferable parts are the sync bot and one-patch-per-file layout, not
  build speed; don't expect Zen's process to fix rac's CI — the engine
  difference dominates.
- Performance evidence is thin: one third-party Speedometer 3 run from Jan
  2025 (Zen 1.7.3b: 31.6 vs Firefox 34.8 vs Chrome 37.7 — CLAIM, never
  re-verified); open issues #8932 (meta, 183 comments), #9727, #14793 (GPU
  helper at 700% CPU). No current Apple Silicon numbers.
- Not re-verified in the dossier's pass: profile path (CLAIM), visual
  constants (squircles, tab colors, CSS totals), ship versions known only
  from release notes (folders 1.15b, iframe translation 1.21.15b), WebDriver
  BiDi in release builds (INFERENCE from `--disable-geckodriver` only), user
  counts, minimum macOS version, spaces sync pre-check on sign-in, Zen's
  embedded Mozilla API key abuse, Chromium macOS-on-Linux cross-compile
  feasibility.
- Privacy policy (2025-02-05, "no telemetry or crash reports") predates its
  share server and Safe Browsing use and omits them (contents FACT;
  out-of-date INFERENCE).

## Where to look in the full dossier

`plans/research/zen.md` — snapshot/market 30–44; feature tables 46–152; UI
layout and the **motion parameter table** (richest section) 153–254; "things
that feel bad" 256–288; architecture 292–361; **data & storage** 376–394;
servers/telemetry 401–417; agents/AI 419–436; build/CI/release/signing
438–542; ranked take/avoid lists 596–721; sources 746–790; **Verification
table** (44 items) 791–866.
