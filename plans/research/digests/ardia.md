# Digest: Ardia

Source: `plans/research/ardia.md` (718 lines), fact-checked 2026-10-25 from
`github.com/mantrakp04/ardia` at `4309c1563a51283e06e4ea9925acb1eadebed946`.
`A:<path>` is inside that clone
(`https://github.com/mantrakp04/ardia/blob/4309c156/<path>`). **FACT** =
primary, **CLAIM** = self-report, **INFERENCE** = reasoning; Verification
corrections are folded in.

## In plain English

Ardia is a free Mac browser built mostly by one person directing AI agents.
Pages run on Chrome's engine; the sidebar and menus are React Native. It
shipped 80 signed builds in 31 days, all from the owner's Mac. It has no AI,
but an outside agent can drive it with an `ardia` command, off by default. It
imports Arc spaces, pins and themes, and syncs through an encrypted iCloud
Drive folder. It sends a few counts home by default. Its docs time Dia's
animations to the millisecond. rac should copy the shipping habits, the
password-key safety fix, the Arc import, the perf patches and the motion
numbers; not the second UI toolkit.

## Key facts

### Project and licence

- macOS 14+, Apple silicon only (FACT, `A:README.md:17`); Intel CI added
  2026-10-25 but all six runs failed; Linux is issue #1.
- Distributed app **GPL-3.0** since 2026-10-23 (engine carries Helium's GPL);
  own files **Apache-2.0**, both kept (FACT, `A:NOTICE:1-13`; `8129b3d4`
  10-23). CLA permits proprietary relicensing (FACT, `A:CLA.md` §2).
- 807 stars, 82 forks, 211 issues (106 open), 1,809 commits at 2026-10-25;
  owner 1,787, 11 outsiders; newest 100 commits Claude 5.5 co-authored (FACT,
  API).
- **80 app releases in 31 days: 48 stable, 32 nightly**, plus 2 engine-only
  prereleases; 4,351 DMG and 2,094 zip downloads (FACT). Free, "no catch"
  (CLAIM); the CLA names "a company the Owner forms", so a commercial turn is
  possible (INFERENCE).

### Architecture and process model

- Engine: **Chromium 155.0.8059.84 + Helium 0.19.4 / 0.19.4.1**, minus **15
  skipped** Helium patches, then 60 Ardia patches, 46 hooks, 2 layers (FACT,
  `A:docs/engine-build.md:3-9`; skips `03-helium.py:46-65`: password manager +
  autofill link, mDNS, Memory Saver, keychain rename, product dir, 4 Sparkle,
  crash dialog, 3 build-setup, Helium signing).
- **One process is Chrome's browser process:** `main.swift` → `ChromeMain`;
  `NSApp` is Chrome's `BrowserCrApplication`; Expo/RN runs inside Chrome's loop
  (FACT, `agent-brief.md:17-19`).
- Each window is one Views-backed `NSWindow`; each profile has its own Chrome
  `Browser` with **no `BrowserView`, tab strip or toolbar**; each tab is a real
  Chrome tab in an RN `ArdiaCoreWebView`; Chrome's `SessionService` ignores them
  (FACT, `agent-brief.md:20-25`, `engine-build.md:74`).
- Bridge: JS → Swift → ObjC++ → `ac_*.mm` (`//ardia/core`) → Chrome, plus dlsym
  `ac_<domain>_<verb>` with JSON on the UI thread. `page_script.js` (1,138
  lines) runs in the **main world** of every frame over Mojo (FACT,
  `agent-brief.md:94-109`).
- **Patch surface: 60 patches, 492 hunks, 9,533 lines, 205 files** (84
  `chrome/browser`, 93 `chrome/`); only **26 hunks in 8 files** touch
  `ui/views`, vs rac ~180 patches / 871 hunks / ~320 in `ui/views` (FACT;
  INFERENCE; rac from brief). Cost moves to unsupported internals (a `Browser`
  without `BrowserView`).
- Hooks: `apply.sh` inserts 46 marker-guarded hooks into 46 files (44
  unpatched); `--check` reports drift and a `g_ardia_*` pointer makes it a
  compile error; `series.py check` reproduces the tree byte for byte (FACT,
  `engine-build.md:114-121,242-251`).

### Storage and sync

Profiles are Chrome SQLite/JSON under
`~/Library/Application Support/com.ardia.browser/Chromium/`; app state is plain
JSON saved 800 ms after a change (FACT, `persist.ts:16`), and
`launch-picture-<window>.png` is an unencrypted PNG of the active tab
(INFERENCE). The sync key is device-only in Keychain "Ardia Sync Key"; remote
files are
`~/Library/Mobile Documents/com~apple~CloudDocs/Ardia Sync/<chain>/<scope>/<random>.nns`;
the CLI token is 0600. No Crashpad; crashes come from
`~/Library/Logs/DiagnosticReports` (FACT).

Sync needs no server, account or Apple entitlement. 24 BIP-39 words encode 256
bits; HKDF-SHA256 derives `file-key` (AES-256-GCM) and `name-key` (HMAC-SHA256).
Format `"NNS1" | nonce | ciphertext | tag`, AAD bound to path, padded to 1 KiB,
never compressed; immutable files under random names moved in with
`NSFileCoordinator`. Merge is hybrid-logical-clock last-writer-wins with
tombstones and a three-way base; snapshots past 40 files. Leaks profile/device
counts, times and sizes; passwords cross into JS. Cycle 15 s, 3 s after an edit.
**Two-Mac run never tested**; #299–#302.

### What leaves the machine by default

- Sparkle check to `ardia.dev/appcast.xml` at launch if 8 h passed, then every
  8 h; version in the User-Agent, `first=1` on a copy's first check; IP not
  stored (FACT).
- `switches.json` once per launch if update checks are on. A `daily_active` ping
  once per UTC day ~30 s after launch, **even with sharing off**: version,
  channel, macOS major, arch, period flags, fresh UUID, geo-IP off (FACT).
- Helium !bang list daily; Google gets Web Store/extension traffic, a
  security-only component updater and the malware kill-switch. Opt-in telemetry
  (off) every 30 s: install ID, counts, timings, cleaned stacks, crash
  signatures (FACT).

Website: first-party rrweb replays (masked inputs, 30 days) read by an AI agent
via Composio; until 2026-09-30 data went to **PostHog Cloud EU**
(FACT/INFERENCE).

### Agents and AI

- **No built-in assistant or agent**; 59 Dia AI parity rows deferred (FACT,
  `A:AGENTS.md:53-54`). Outside agents use the **`ardia` CLI**: Python 3.13 +
  pydoll 3.0 over CDP, not in the bundle, pinned by a SHA-256 in the signed
  bundle; **off by default** (FACT, `A:docs/cli.md:1-16,202-232`).
- Token mode: random per-start token in a 0600 `ArdiaControl.json`; every
  WebSocket needs `?token=`, constant-time compare; `/json*` 404s; any `Origin`
  refused (FACT).
- Allowed: exactly **70 CDP methods** — discovery/attach, DOM and accessibility
  reads, navigate/reload/screenshot/print, evaluate in the page's main world,
  reviewed Input keys (no clipboard, no native events), Network bodies; plus
  `Page.addScriptToEvaluateOnNewDocument`, `Page.createIsolatedWorld` and
  `Target.createTarget`/`closeTarget`, so a client can open/close tabs and plant
  per-document scripts (FACT, `ac_cli_token_policy.cc:51-122,143-200`).
- Forbidden: Ardia's windows, extension pages, chrome://, DevTools, local files,
  extension worlds, auth headers, closing or crashing the browser (FACT).
- Safety: one global switch, a "controlling · Stop" pill, token redaction, **no
  per-site rules or confirmations**; `SKILL.md` only asks the agent to "Ask
  before anything with consequences" (FACT). A connected agent thus has
  page-script power and input in every signed-in tab (INFERENCE).
- Skills install for `general|codex|claude-code|cursor|opencode`; AppleScript,
  Raycast, `history()`/`pinned()` helpers. Engineering: Opus subagents implement,
  a main session verifies, Codex reviews, agents may release (FACT,
  `AGENTS.md:13-25,82-84,109-110`).

### Motion (exact numbers)

Every spring uses Apple's convention: **stiffness = (2π/response)², damping =
4πζ/response, mass 1** (FACT, `dockMotion.ts:12-15`). "Dia measured" is
Ardia's record from 60–240 fps recordings plus some disassembly; accuracy is
CLAIM.

| Interaction | Numbers |
|---|---|
| Tab hover card | Show 500 ms (100 ms by flag); 100 ms fade `cubic-bezier(.25,.46,.45,.94)`; scale 0.92→1 (0.25, 0.75); hide 100 ms |
| Close tab | Row fades 100 ms; rows below slide 140 ms (ω≈40, ζ 0.9) |
| Sidebar hide/show | One spring both ways **(0.215, 0.79)**; 90% in 100 ms, 1–2 pt overshoot |
| Arc edge peek | In **(0.185, 0.77)**, 93% in 66 ms; out 150 ms ease-in-out |
| Command bar | Grows from the URL field ≈130 ms exponential ease-out |
| Space swipe | Rubber band `255·(1−1/(0.15·x/255+1))`; settle 0.25 s critically damped; detent haptics |
| Group / PiP throw | Group **(0.30, 0.82)**, tuck 120 ms. PiP: fling >350 pt/s, nearest corner ±45°, spring (0.9, 0.9) |

RN `Animated`, no Reanimated: **94 animations native-driver, 22 JS-thread**
(FACT). Backdrop: private `NSVisualEffectView` material **29** dark / **13**
light, card #121212 at 0.5 / white at 0.7, private `CAFilter` "gaussianBlur"
(breaks on OS updates, INFERENCE). Metal: one `MTKView`, 1,527 lines; New Tab
band 3.75 s, halo 2 s, both paused under Reduce Motion.

### Features, perf, build, release, CI

- Features (FACT): sidebar or top strip per window (⇧⌘S); pinned "Top Apps"
  tiles/folders, Arc-style pinned rows and groups, nested folders; tab groups by
  dropping a tab on a tab, auto-named by a deterministic heuristic, no AI
  (`groupNames.ts:70`); live folders (GitHub/Bitbucket PRs, Drive, Notion,
  calendar); **spaces are profiles**, so Arc import loses logins (#50). Command
  bar (⌘L, no scrim) with frecency, bookmarks, open tabs, calculator, `doc.new`
  shortcuts, extensions, !bangs. Split view up to 3 panes; Little Ardia (⌥⌘N);
  **Peek** on shift/⌥-click, ⌘O promotes, never saved/synced/Recently Closed.
  Full uBO (MV2); Helium privacy patches; **Web Store and extension updates go
  straight to Google, undoing Helium's proxy**; auto-PiP with throw-to-corner;
  Apple Translation (macOS 26). Blocked: Widevine, iCloud Keychain passkeys.
- Import: Chrome, Edge, Brave, Opera, Vivaldi, Helium, Island, Dia, Arc, Firefox,
  Zen, Safari, bookmark HTML, password CSV; Arc covers spaces, pins, folders,
  live folders, split views, names, emoji icons, themes; Dia is partial.
- Perf (FACT): tab switch **40 ms vs Helium 8.5 ms** (10-16), cut to **10–16 ms**
  on 10-17 (~25 ms was the JS/React round trip); 20 tabs **1,183 MB** vs Chrome
  919 and Helium 1,125 (29% / 5% worse); 1 tab 290 vs 375 MB. Bugs: dropped
  frames with the vertical sidebar (#333); close skips unload handlers, so
  Discord logs out (#342); launch flicker (#317).
- Build: pnpm + Turborepo, CocoaPods + Xcode, GN + autoninja. Engine on the
  owner's M5 Pro: first full official build **2.5 h**, incremental + ThinLTO
  relink **~7 min**, **45 GB**; one "chromium lock" at a time. Engine versioned
  by `git rev-parse HEAD:engine`; a local engine rides on the first app release
  as `ArdiaCore-<tree>.tar.xz`, a CI engine gets an `engine-<tree:12>`
  prerelease; JS-only changes need no rebuild. 25 of 42 releases since 0.2.31
  carried a new engine.
- **All 80 releases were built and signed locally by `scripts/release.sh`.** The
  CI Release workflow's first commit is `e8ec213e` at 2026-10-25 18:14 UTC, after
  all 80; two runs succeeded by 19:29 UTC, both **dry runs** (Tag runs only when
  `dry_run` is false), so nothing published (FACT, runs 40221031458, 40225253957).
- CI: CLA and linked-issue checks, site deploy, manual Release workflow (both
  arches, dry run by default), and a **10-phase x64 engine build on a 3-core
  runner** checkpointing tree and `out/` as a zstd tar between 6-hour jobs. The
  checkpoint uses bsdtar's default format, which rac found drops sub-second
  mtimes; it also passes `--no-mac-metadata`, so likely none survive
  (FACT/INFERENCE). **No x64 run has finished**; all six on 2026-10-25 failed or
  were cancelled.
- Signing: Developer ID team **U5L5T3NGVV**, hardened runtime, `allow-jit` only
  for renderer and GPU helpers, notarized and stapled since 0.2.1; the release
  launches the exported app once and re-verifies the signature, so nothing may
  write into the bundle (FACT).
- Updates: **Sparkle 2.9.6**, EdDSA zip, one appcast with
  `<sparkle:channel>nightly`, monotonic builds, 3 items per channel, phased
  rollout, hidden "prewarm" first run; `SUScheduledCheckInterval` 28800 (FACT).
  Smoke test: hidden launch over CDP, Gatekeeper, Sparkle updating a copy of the
  previous build, data carry-over, rollback. Perf gate: stable only vs the
  previous stable — native bench, JS bench, render-census ratchet, cross-browser
  bench. Kill switches: static JSON, **at most 8 live**, each with an owner and
  removal date (FACT).
- Tests: the doc's headline **333** unit cases but its table sums to **361**;
  today 90 `.test.mjs`, 11 `.test.ts`, 13 Swift test files (FACT).
- Upstream: Helium pinned by tag/commit; a `guard` stage refuses an update that
  changes what a skip protects; a new Chromium needs the owner's OK and a full
  rebuild. Adopted 0.19.4.1 on 2026-10-23; 0.20.1.1 (Chromium 156) not adopted.
  Process: commits straight to `main`, no worktrees, no comments; `AGENTS.md`
  still says Chromium 154 and Apache-2.0 (FACT).

## What rac should take (ranked)

Cost: XS <1 day, S 1–3, M 4–10, L >10. Ardia's own files are Apache-2.0 and can
go into GPL-3.0 rac with credit and the NOTICE kept (FACT, `A:NOTICE:6-7`); a
patch to a non-Helium Chromium file needs a per-file licence check (INFERENCE).

1. **Ship 0.1.0 from the Mac first**, as all 80 Ardia releases were: nightly in
   the same appcast with monotonic build numbers, a release note opened after an
   update, and a smoke test running the previous build's Sparkle against the new
   zip plus data carry-over. **S–M, 2–4 days.**
2. **Port the Safe Storage "no silent reset" fix.** Chromium can mint a new key
   when the keychain item is briefly invisible at login, making saved passwords
   and cookies unreadable; on `errSecItemNotFound` Ardia adds a random key, and
   the add overwrites the item if it has appeared. **rac has the same
   find-then-add code** (`components/os_crypt/common/keychain_password_mac.mm:64-65,92-95`;
   `crypto/apple/keychain_v2.mm:189-211`); the path exists (FACT), the slow-login
   trigger is CLAIM. Rewrite Ardia's 554-line patch. **S, 1–2 days. Prevents
   silent data loss.**
3. **Arc import, spaces kept as spaces.** Reuse the reader:
   `StorableSidebar.json` (`sidebar.containers`, `spaces`, `items`,
   `topAppsContainerIDs`, `customInfo.windowTheme`, emoji icons, `splitView`,
   live folders), WAL-safe SQLite snapshot, keychain prompt only after an
   explicit unlock, fixtures per source. Map **Arc profile → rac profile, Arc
   space → rac space**, which Ardia gets wrong (#50). **M–L, 1–2 weeks.**
4. **Bundle Ardia's power/idle patches behind switches, then measure against
   Helium:** (a) no 15 s CPU sampling, 60 s disk check, Bluetooth polling or
   hybrid passkey scans except on demand; (b) uBO first-write cost (lazy storage,
   ~180 ms on a performance core) and content-script load timing; (c) tab
   freezing that spares WebSocket/WebRTC tabs and thaws others every 600 s;
   (d) main frames at 60 Hz on 120 Hz displays except during input, scrolling and
   the first second, with Battery Saver lifting its 30 Hz cap on input. **S–M
   each, ~2 weeks.**
5. **Cross-browser perf bench and a stable-only gate.** Interleaved rotated
   rounds, medians with min–max and n: cold launch, new tab, tab switch, memory
   at 1/10/20 tabs, idle CPU and wakeups. **S–M, ~1 week.**
6. **Motion tokens plus a spring helper for Views.** Add `(response,
   dampingRatio)` springs with Apple's conversion and closed-form position, then
   retune: sidebar (0.215, 0.79); edge reveal (0.185, 0.77), out 150 ms; hover
   0.92→1 (0.25, 0.75) with 100 ms fade; close 100 ms fade / 140 ms slide;
   command bar 130 ms exp ease-out; group (0.30, 0.82); space 0.25 s; PiP (0.9,
   0.9). rac uses fixed tweens (FACT). Re-measure from rac's recordings. **S,
   3–5 days.**
7. **An outside-agent control channel independent of rac's AI switch.** Copy the
   hygiene: random 0600 token, method allowlist, web-only targets, no extension
   worlds, stripped auth headers, no browser-close, a "controlled · Stop" pill,
   off by default, skill installer for Claude Code, Codex, Cursor, OpenCode. Add
   per-site Always/Never and confirmations for outside agents. **M–L, 1–2 weeks.**
8. **Folder-based end-to-end sync for phase 6**, same no-server promise: BIP-39,
   HKDF, AES-GCM with path-bound AAD, 1 KiB padding, immutable files, HLC
   last-writer-wins, snapshots. **L, 4–8 weeks**; needs the two-Mac test Ardia
   never ran.
9. **Small wins:** deterministic group auto-naming for AI-off (XS); a build check
   that fails if the binary or paks name a forbidden host (XS); `series check`
   reproducing the patched tree byte for byte (S); Apple Translation on macOS 26
   (M); PiP throw (M); Peek and Little Arc, with Peek kept out of session restore
   and Recently Closed (M).

## What rac should avoid

1. **A React Native (or any second UI toolkit) shell.** It costs tab-switch
   latency, memory and a large dependency tree, and would rewrite rac's Views
   patches; Ardia's own review keeps RN mainly for agent dev speed (FACT,
   review §6).
2. **Disassembling Dia or Arc binaries.** Dia's Terms of Use forbid using Dia
   to "decompile, reverse engineer, or otherwise attempt to obtain the source
   code or underlying ideas" (item 10) and to build competing products (item
   11) (FACT, diabrowser.com/termsofuse). Measure from screen recordings.
3. **Phoning home by default:** daily pings, counted update checks through rac's
   own server, a remote kill-switch on rac's server, site session replays,
   third-party readers of telemetry. Each breaks rac's first non-negotiable. If
   kill switches are wanted, consider a static file on GitHub next to the
   existing feed, read only when update checks are on — a maintainer decision.
4. **Reverting Helium's extension download proxy** so the Web Store and
   extension updates reach Google directly. Decide deliberately.
5. **Spaces as profiles.** Keep rac's spaces separate.
6. **A script in the main world of every page**
   (`ac_content_renderer_client.cc:106-116`); pages can see and tamper with it.
   Prefer isolated worlds.
7. **Private macOS APIs without a fallback** (material 29, `CAFilter`).
8. **Ardia's process rules:** commits straight to `main`, no worktrees, no
   comments, agents releasing with no human review. rac's worktree/PR flow is
   safer for a browser people trust with logins.
9. **A switch for every Arc habit.** rac is opinionated; pick defaults.
10. **Outside-agent access with no per-site scope.**

## Caveats

- Dia's numbers are Ardia's own records (recordings, some disassembly); the
  researcher could not run Dia. Treat them as reference values to re-measure.
- GitHub counts move hourly; all figures carry 2026-10-25 ~19:50 UTC.
- Unverified by Ardia: two-Mac iCloud sync; the 10-phase x64 CI (all six runs
  failed/cancelled); whether its bsdtar checkpoint hits rac's sub-second-mtime /
  siso problem (the `--no-mac-metadata` flag makes it unlikely, INFERENCE).
- Whether the Safe Storage reset fires on rac is unproven; the code path is
  present. Whether Helium already ships some power patches: Ardia says Helium
  enables `InfiniteTabsFreezing` by default; the rest was not checked.
- Licences of Ardia's patches to non-Helium Chromium files (Apache-2.0 headers)
  need per-file checks; the CLA permits proprietary relicensing. Usage unknown:
  4,351 DMG downloads double-count reinstalls and Homebrew; no independent
  reviews surfaced, only listicles. Not re-checked: Dia layout/motion rows
  citing only `dia-spec.md`; code-size rows outside `packages/*` and `apps/cli`.
  Overall confidence **medium-high**.

## Where to look in the full dossier

`plans/research/ardia.md`: features 22–116; layout and motion 117–213 (motion
152–188, feel 194–204, bad/risky 206–213); architecture 215–345 (process
229–245, bridge 247–269, engine integration 287–310); storage/sync/outbound
347–404; agents 406–441; build/release/CI 443–495; strengths/weaknesses
497–531; ranked take/avoid 533–611; open questions 613–630; sources 632–663;
**Verification (authoritative) 665–718**. Key clone files:
`A:docs/{dia-spec,engine-build,agent-brief,sync,cli,releasing}.md`,
`A:docs/perf/vs-browsers.md`, `A:packages/import/`,
`A:engine/patches/build/03-helium.py`,
`A:engine/chromium/src/chrome/browser/ardia/ac_cli_token_policy.cc`,
`A:.github/engine/x64.sh`.
