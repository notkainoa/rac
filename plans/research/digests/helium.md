# Helium: planning digest

Digest of `plans/research/helium.md` (researched and fact-checked
2026-10-25). Subject: imputnet/helium core at `f29a259` (Chromium
156.0.8078.47) and imputnet/helium-macos tag `0.20.1.1` (`9aa975a`); rac is
based on helium-macos `0.18.2.1` (`992a020`), Helium core `76141e1`,
Chromium 154.0.8037.92. The dossier's Verification section audited 41
claims; corrections are authoritative.

## In plain English

Helium is the browser rac is built on, made by two people. It is Chrome
with Google taken out, a built-in ad blocker, and a calm look.
Nothing phones home until you consent in onboarding; then Helium's servers
fetch extensions (via an anonymizing proxy), filter lists, and !bangs
without knowing who you are. It has four tab layouts, a "frameless" mode
hiding chrome until you touch a window edge, split view, shortcuts.
No AI, no spaces, no sync, no Widevine. Chrome ships every two weeks;
Helium follows in 2-4 days. rac is six releases behind. A dry run shows
121 of rac's 180 patches still apply to the newest Helium; the rest
mostly touch sidebar and settings code Helium rebuilt.

## Key facts

### What Helium is

- "Private, fast, honest web browser"; officially beta. Chromium 156 at
  0.20.1.1; stack derived from ungoogled-chromium; version scheme
  `0.<Chromium major − 136>.<core rev>.<platform rev>`. Licenses: browser
  GPL-3.0, services AGPL-3.0, imported ungoogled code BSD-3-Clause. FACT.
- Team: exactly two maintainers (`wukko`, `dumbmoron`). 166 of 169 merged
  core PRs since 2026-07-25 are theirs; Chromium bumps from ungoogled's
  Blaise (`Ahrotahn`). Funding: tips only; no paid features. FACT/CLAIM.
- Org: `helium` (core), `helium-macos/-linux/-windows`, `helium-services`
  (AGPL), `helium-onboarding` (Svelte 5), chromium-tarballs, an uBlock
  fork, and more. helium has 21,983 stars, helium-macos 1,172
  (2026-10-25); both created 2025-02-15; first macOS release 2025-05-04;
  134 releases since, 25 in the last 90 days. FACT.
- Helium is NOT a fork of ungoogled-chromium (it merges ungoogled's
  history). Patch stack on a Chromium tarball, all counts FACT
  (recounted): GNU `patch -p1 --ignore-whitespace --forward`; fuzz
  allowed by default, `--fuzz=0` for bot and dry runs (H
  `utils/patches.py` L93-145). Core: 346 patches, ~91k lines (71
  ungoogled, 6 inox, 4 brave, 3 bromite, 3 iridium, 1 debian, 2
  upstream-fixes, 256 helium); touches 1,645 files, creates 195.
  helium-macos: 23 patches, ~4.8k lines. rac: 180 patches, ~110.7k lines
  — larger than Helium's own macOS layer.

### Cadence and upstream tracking

- Chrome moved to a two-week stable cycle from Chrome 153 (2026-09-08);
  Chrome 157 due 2026-11-03 (tarball exists). FACT
  ([chrome blog](https://developer.chrome.com/blog/chrome-two-week-release)).
- Helium ships each new Chromium major 2-4 days after Chrome stable:
  153→0.17.0.1 (Sep 12), 154→0.18.1.1 (Sep 24), 155→0.19.2.1 (Oct 9),
  156→0.20.1.1 (Oct 22). FACT.
- Upstream loop: ungoogled bumps Chromium → Helium merges and refreshes
  core patches → a `bump-platform` bot opens an update PR in helium-macos
  → maintainer builds. FACT.

### rac sync difficulty (the studied question)

Text-only dry-run: apply Helium core + macOS series to Chromium files at
the target tag, then rac's 180 patches. On today's base all 180 apply with
0 failures. FACT.

| Target | Fuzz | rac patches clean | Failed hunks |
| --- | --- | --- | --- |
| Current base (154 / 0.18.2.1) | 0 | 180 / 180 | 0 |
| 0.19.4.1 (155.0.8059.84) | 2 | 143 / 180 | 43 |
| **0.20.1.1 (156.0.8078.47)** | **2** | **121 / 180** | **104** |
| 0.20.1.1 | 0 | 107 / 180 | 173 |

- At 0.20.1.1 fuzz 2, only **46 hunks in 32 patch-file pairs fail first**
  (68 cascades). rac has 3,341 hunks total. FACT (re-summed from logs,
  not re-run — medium confidence).
- Failure groups (failing/total patches, hunks): sidebar-reveal 5/5 (12),
  settings 6/13 (15), sidebar-address-bar 3/10 (12), spaces 11/26 (18),
  look 9/20 (14), pinned 6/18 (7), ai 7/39 (7); privacy and dev clean.
  FACT.
- Hard conflict = design merge in `vertical_tab_strip_region_view.cc` (16
  hunks) and `vertical_tab_strip_state_controller.cc` (13): Helium reworked
  frameless mode around expand-on-hover; rac's sidebar-reveal (which sets a
  350 → 100 ms dwell) edits the same parameters. Also `appearance_page.ts`
  (11) + `.html.ts` (9) — Helium's new Layout settings section;
  `chrome/browser/ui/BUILD.gn` (25 hunks) is mechanical. FACT.
- Chromium Unified Tabstrip moved files under `chrome/browser/ui/views/`:
  `tabs/{horizontal,vertical}_tab_style_views.cc` → `tabs/common/`,
  `new_tab_button_menu_model.h` → `tabs/shared/` (commit
  [8277d76](https://github.com/chromium/chromium/commit/8277d76b10) moved
  only the latter — dossier fixed the over-claim). Of 470 non-generated
  headers rac includes, only that one is gone in 156; Helium also removed
  `SetZenModeFloatingStyleForLayout`. FACT.
- 0.18.2.1 → 0.20.1.1 = six tagged releases (brief's "seven" is wrong):
  85 core commits, 277 core patch files changed. FACT.

### Architecture and storage

- Process model: unchanged Chromium multi-process; importers (e.g.
  `chrome/utility/importer/arc_sidebar_importer.cc`) in the utility
  process. UI: chrome in C++ Views; settings/WebUI in TypeScript/Lit;
  onboarding (`helium://setup`) a separate Svelte 5 + Vite repo shipped
  as a prebuilt tarball + `.grd(p)` strings; macOS in Objective-C++
  (Sparkle 2, private `TranslationUI.framework`). FACT.
- Profile: `~/Library/Application Support/net.imput.helium` (dev builds
  `.dev`). Standard Chromium formats (Preferences JSON, SQLite, LevelDB);
  Helium settings are plain `helium.*` prefs. Keychain item "Helium
  Storage Key", with retry-preserving error handling so a denied Keychain
  never wipes data. rac's `rac.spaces` and `rac.sidebar.lists` are
  dictionary prefs today — syncable if shaped to fit. FACT.
- Sync: experimental "private vault" behind `FEATURE_DISABLED_BY_DEFAULT`
  (17 patches): AEAD immutable commits; a `syncVaultProvider` extension
  stores opaque blobs. FACT.
- Server: helium-services (AGPL, public): nginx + Deno services
  (extension-proxy ×2, uBO list mirror, bangs, `minidumpster` crash
  handler) + `sparkler` (Sparkle appcast from GitHub releases), at
  `services.helium.imput.net`, `updates.helium.computer` (Cloudflare),
  `crash.helium.computer`. Logs ≤ 24 h; crashes 30 days, org-only access.
  **Fork risk:** terms are silent on third-party builds; the privacy
  policy excludes them. FACT.

### Privacy features worth copying

- One gate `ShouldAccessServices` guards every service (`services.enabled`
  true AND `services.user_consented` false by default, set in onboarding);
  per-service prefs `helium.services.*`; self-host `origin_override`
  accepts HTTPS or localhost only; versioned consent schema
  (`kHeliumCurrentSchemaVersion = 1`) with changelog. FACT.
- Extension proxy anonymization: normalized requests (RAM size 4/8/16 GB
  random, fresh UUIDs, shuffled) + `ceil(2*(1+log2(n)))` decoy extensions
  from a pool of 2,048 (HS `mixins.ts`, `request.ts`). A rac copy would
  serve fewer users and hide less. INFERENCE.
- uBlock Origin MV2 fork (1.75.0) as built-in component + CNAME
  uncloaking; fingerprint noise; WebRTC public-only; HTTPS-first;
  password manager forced off in code; no Widevine (CLAIM, licensing).

### Agents and AI

- Helium has no AI and strips Chromium's: `disable-ai.patch`; 0.19.3.1
  removed Glic/Lens/Compose/actor WebUIs (~1.45 MiB). FACT.
- Chromium actor churn: `type_tool.cc` changed 332 lines between 154 and
  156; `ToolBase::ExecutionObservationDelay` removed. rac's agent drives
  these symbols directly. FACT.
- AppleScript: Chromium's dictionary (tabs, URL, `execute` javascript)
  plus Helium's new `select` command — a zero-cost outside-agent channel;
  macOS gates Apple Events per-app. FACT.

### Motion, shape, theme numbers (reusable baseline)

All FACT (patch lines verified). Only `RichAnimationDuration` animations
honor reduced motion.

| Token | Value |
| --- | --- |
| Frameless reveal | 200 ms, `FAST_OUT_SLOW_IN_3`, via `RichAnimationDuration` |
| Frameless trigger/hide | 6 px edge strip, 8 px hover leeway; 150 ms hide grace; 3,000 ms after window exit |
| Vertical tabs | 250 ms expand and collapse |
| Toast in/out/fade | 300 / 150 / 50 ms, `ACCEL_5_70_DECEL_90` / `ACCEL_30_DECEL_20_85` |
| Progress line | 180 ms move, 700 ms pulse, 320 ms fade |
| Split drop target | 300 ms (Chromium 450); 500 ms timers |
| Hibernated favicon | 250 ms fade (1 s discard ring removed) |
| Radii | generic frame 8 px; macOS window 17 px (macOS 26+) / 12 px older; buttons 7 px (`kMSmall`); dialogs/menus/find 8 px; button padding 14 px |
| Accent | indigo palette, tone 50 `#516BEC`; active tab contrast 1.5 dark / 1.25 light vs frame |
| Materials | vibrancy off by default; `NSVisualEffectView`, Sidebar (dark) / Menu (light), behind-window blending; self-warned "may cause UI clarity issues" |

### Build, CI, release

- Build: GN + siso/autoninja; release `is_official_build` + PGO phase 2;
  sccache (Depot Cache) in CI; sources from prepared Chromium archives on
  `tarballs.imput.net` (base 1.98 GB + per-arch layer 1.39-1.43 GB,
  toolchains included, since 0.19.3.1). FACT.
- CI: lint → sanity (quilt-apply all patches, **fails on any patch
  offset**, 30-second build passes on timeout) → manual build: up to 10
  chained phases per arch, 6 h each, checkpointing `build/src` as plain
  `tar -c` + `zstd -11` → prerelease via `action-gh-release@v2.5`
  (`sanity-check.sh` L44-54, `building.yml` L46-140). FACT.
- 0.20.1.1 run: all jobs on Depot `depot-macos-latest` (macOS 26, M4,
  8 cores, 24 GB, 400 GB, $0.08/min). 14 h 21 min end to end; arm64 2
  phases (4h31m + 2h12m); x86_64 3 (4h31m + 5h16m + 3h18m). GitHub free
  `macos-latest` = 3 M1 cores, 7 GB, 14 GB disk. FACT.
- Helium uses the same plain-tar checkpoint rac found to drop sub-second
  mtimes (siso reset; fix `tar --format pax`, rac PR #20); it is likely
  rescued only by fast runners and warm cache. INFERENCE.
- Cost of a rac release at Helium's timings on Depot: ~20.6 runner hours ≈
  $99 both arches, ≈ $34 arm64, plus $20/month. INFERENCE.
- Signing: `sign_chrome.py` + `notarytool`; Sparkle 2 EdDSA, deltas vs the
  last 5 releases; DMG 113 MB arm64 / 130 MB x86_64; deltas 40-53 MB.
  FACT.
- Tests: no Chromium unit/browser tests run in any Helium CI; core CI runs
  yapf/pylint/pytest on its own utils plus patch lint. FACT.

## What rac should take (ranked)

Effort estimates (S ≤ 1 day, M = 2-5 days, L > 1 week), all INFERENCE
unless noted.

1. **A per-release "Helium fit" CI check. Cost S.** Mirror `bump-platform`:
   on every helium-macos tag, merge into a scratch branch, apply all
   patches, report which rac patches fail; the dossier's sparse method
   runs in minutes on free runners. Must run every two weeks.
2. **Sync to 0.20.1.1 now. Cost M.** Two options: (a) one jump — one tree
   rebuild, ~46 first-failure hunks plus the sidebar design merge; or (b)
   two steps via 0.19.4.1 — only 19 first-failure hunks there (mostly
   BUILD.gn), then the layout/settings conflicts, but two rebuilds.
   Either way: adopt Helium's new `prepare_sources` / `configure_build`
   CI signatures (rac's CI calls the deleted script —
   `sanity-check.sh` L16-17), refresh every rac patch for the strict
   no-offset sanity check; the tag merge conflicts only in
   `patches/series`.
3. **Rebuild sidebar hide/reveal on Helium 0.20's frameless overlay. Cost
   M, during the sync.** Helium now floats the sidebar via expand-on-hover
   with a keep-expanded lock. Keep only rac's semantics: full-or-hidden,
   100 ms dwell, top-edge toolbar reveal.
4. **Release CI with big macOS runners + warm compiler cache. Cost S.**
   Depot's 8-core M4 runners finished Helium in 2-3 phases; free 3-core
   M1 hasn't finished rac. After the tar-pax fix (rac PR #20) free
   runners may pass, making Depot a speed choice (~14 h vs 1+ day).
   Ask Depot about open-source terms.
5. **Ship arm64 first. Cost S.** macOS 27 is Apple-silicon only
   ([Tom's Hardware](https://www.tomshardware.com/software/macos/macos-tahoe-is-the-last-release-for-intel-macs-apple-silicon-exclusivity-will-mark-end-of-hackintoshes));
   Helium's x86_64 build took 13 h vs 6.7 h arm64. Intel Macs wait.
6. **Arc import built on Helium's `ArcSidebarImporter`. Cost M.** Helium
   parses `StorableSidebar.json` and made `ChromeImporter::ImportBookmarks`
   virtual; a rac subclass can map Top Apps → favorites and per-space
   pinned containers → pinned-tab folders with rac spaces (Helium only
   uses the internal space ID; whether Arc stores readable titles is
   unverified). Arc shuts down 2026-12-22; reuse the macOS 27 prompt
   flow.
7. **Take Helium's settings/Layout work instead of re-patching it. Cost
   S-M.** Use the new Layout section with skeleton previews; hide
   unsupported layouts with one small hook, then refresh rac's settings
   patches.
8. **Keep Helium's services; `origin_override` as the escape hatch.**
   Cost S. Don't self-host yet: the proxy's decoy mixing weakens at low
   user counts.
9. **Shape rac data now for Helium's coming sync. Cost S now, M later.**
   Format `rac.spaces` / `rac.sidebar.lists` so a `syncVaultProvider` can
   carry them. Build no rac sync server.
10. **Reuse the versioned-consent pattern. Cost S.** Schema version +
    changelog (services-prefs.patch L700-743) fits rac's AI opt-in and
    future crash-report prompts.
11. **AppleScript as the first outside-agent channel. Cost S-M.** Works
    with AI off, costs nothing until used, macOS-native per-app gating;
    add rac spaces to the dictionary later.
12. **Adopt Helium's motion/shape constants as rac's baseline. Cost S.**
    See table above; reuse `ShouldUseNativeFrameMaterials` for sidebar
    vibrancy (rac adds only 1 of its 9 references as a call — dossier
    fixed that claim).
13. **Later:** LLM-batch translation for rac strings (Helium scale: 81
    locales; rac is English-only) and self-host `minidumpster` for opt-in
    crash reports. Cost M each.

## What rac should avoid

- **Letting the sync gap grow.** Failed hunks doubled 0.19.4.1 → 0.20.1.1
  (43 → 104) in one release; each Chromium also carries security fixes.
- **Building deeper into Chromium's tab strip.** Files move every release
  (Unified Tabstrip). Keep rac's sidebar in rac-owned views with thin
  hooks.
- **Lines-by-line edits to Helium-created files or its settings templates.**
  rac already carries 20 hunks on 8 Helium-created files.
- **Spreading the agent across `chrome/renderer/actor/*`.** Both Helium
  and Chromium prune/rewrite it. Put one rac-owned adapter between rac's
  agent and the actor layer.
- **Planning on any upstream Helium fix** — its AGENTS.md makes agents
  refuse all code changes and CONTRIBUTING bans AI-written PRs with
  permanent bans; record agrees (3 outside PRs merged in ~3 months).
- **Promising Netflix/DRM playback** in marketing to Arc users: no
  Widevine. Decide before go-live.
- **Copying Helium's many toggles** (4 layouts, per-button switches).
  rac is opinionated; pick one layout story and hide the rest — every
  hide is a patch to rebase later.
- **Depending indefinitely on unverified fork access to Helium's
  services.** Terms don't cover forks; self-hosting later would weaken
  the proxy's cover.
- **Stale rac docs:** `docs/internals/overview.md` L69 says Chromium ships
  "roughly every four weeks" — it's two; `docs/operations/upstream-sync.md`
  L78 says rac has no Apple developer account — the brief says it does.

## Caveats

- **Dry-run limits.** Sync numbers are text-apply results, re-summed from
  logs but not re-run (medium confidence). They can't see compile errors
  in rac's 325 new files, behavior regressions in frameless / layout
  settings / onboarding, or `.grd(p)` string-file conflicts from rac's
  name pass.
- **Estimates** (Depot $99/$34, S/M/L) are derived arithmetic on one Helium
  run, not quotes; Depot terms unpublished. Helium's phase-2 resume wasn't
  checked against its logs (INFERENCE).
- **Left as CLAIM:** no Widevine, zero first-launch requests, mobile "Not
  yet"; user reports #1971/#1887/#2733 (frameless UX jank). Feature rows
  citing only patch names were spot-checks only.
- **Open questions:** Does Helium plan spaces or a command palette (#1351,
  #317 open, no maintainer reply)? When does sync ship, and will it carry
  `rac.*` prefs? No statement on forks using Helium's services. Does
  macOS 27's Files & Folders gate apply to Arc's data? Is "Allow
  JavaScript from Apple Events" still reachable in Helium's menu? Does
  imputnet run a NativeLink build cluster? How long MV2 survives?

## Where to look in the full dossier

`plans/research/helium.md` (899 lines, rac worktree `cfdcf83` on
`plans/overhaul`).

- L9-44 snapshot; L46-155 feature tables; L156-235 UI, feel, motion,
  shape tables
- L240-325 architecture, process model, patch-stack diagram, coupling
  counts, storage, servers; L327-348 agents & AI
- L350-501 build, CI, release, cadence, changes 0.18.2.1 → 0.20.1.1
- L503-581 sync-difficulty study; L582-599 reproducible dry-run script
  (seed for the per-release fit check)
- L601-767 strengths/weaknesses, ranked lists, open questions
- L768-819 sources; L821-899 Verification table (41 claims audited)
