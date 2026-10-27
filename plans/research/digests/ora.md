# Digest: Ora

Source dossier: `plans/research/ora.md` (750 lines, fact-checked 2026-10-25
against a clone of `github.com/the-ora/browser` at commit `4e6cfd1`, 2026-09-17,
website source `the-ora/www` at `ff9e694`, GitHub API, whois, dig, curl.
Nothing was ever built or run; all behavioral claims are from code reading).
Tags: FACT = primary source, CLAIM = project's own marketing/self-report,
INFERENCE = researcher's reasoning.

## In plain English

Ora is a free, open-source Mac browser that copies Arc's layout. It runs
inside a small Swift app on WebKit — Safari's engine — not Chromium. It has a
sidebar, spaces, pinned tabs, favorites, a launcher, an ad blocker, and its
own password manager. Each space keeps a separate cookie jar, so work and
personal logins stay apart. It has no AI, no agent, and no extensions.
Its README says it is not ready for daily use; two people wrote most of it;
the last release was April 2026 and its domain expired in September. For rac,
Ora is worth reading for three things: small polish ideas with exact timings,
a working local release-and-notarization chain that bypasses CI, and a list
of mistakes (no per-site permission prompts, page scripts trusted for the
address bar, constant polling loops). It changes nothing about rac's stack —
if anything it confirms staying on Chromium.

## Key facts

### Project snapshot

- Native macOS browser shell around the system WebKit via `WKWebView`. No
  fork, no engine patches (FACT, `ora/Core/BrowserEngine/BrowserPage.swift:23-53`).
  Tagline: "Less noise, more browsing." (`HomeView.swift:41`); README says
  "Fast, native WebKit browser for macOS."
- Repo `github.com/the-ora/browser`, created 2025-08-09; org created
  2025-07-03 (FACT, GitHub API). 2,241 stars, 98 forks, 25 open issues+PRs,
  451 commits at 2026-10-25 (FACT).
- License history: MIT until 2025-10-03, then GPL-2.0, then GPL-3.0 since
  2026-03-12 (FACT, commit `fe66211`, PR #223). The website still says "MIT"
  (FACT, `ora-www/src/components/features.tsx:86`) — stale, not invented.
- Team: two core authors, `yonaries` (223 commits) and `kenenisa` (178) = 89%
  of commits; 21 others with 1–7 each (FACT). Donations-only (GitHub
  Sponsors, Buy Me a Coffee); Vercel OSS Fall '25 cohort (CLAIM).
- Releases: 58 total, 18,524 DMG downloads; first build v0.0.18 on
  2025-09-04. Latest v0.2.14 on 2026-04-07. **No release since; one commit
  since (2026-09-17)** (FACT). 39 test releases on 2025-09-05/06 alone.
- Status: README says "not ready for daily use yet" (FACT). `orabrowser.com`
  expired 2026-09-05, in WHOIS `redemptionPeriod`, no DNS (FACT,
  `whois`/`dig` 2026-10-25). The Sparkle feed on `the-ora.github.io` still
  answered HTTP 200 (FACT, curl 2026-10-25).
- DMG is 9.7 MB; ~25,600 lines of Swift in 171 files (FACT).

### Architecture and process model

- One SwiftUI `App` process (`@main OraApp`) with three `WindowGroup`s:
  normal, private, settings (FACT, `OraApp.swift:68-118`). WebKit spawns its
  own web/networking/GPU processes; Ora manages none.
- One `WKWebView` per live tab, created lazily on first open, destroyed after
  an inactivity timeout (default 1 h; options 1–48 h or never) (FACT,
  `Tab.swift:200-239`, `SettingsStore.swift:295-310`).
- **Each window builds its own full state**: own `TabManager`,
  `HistoryManager`, `DownloadManager`, own `ModelContainer` on the same
  SQLite file, and even its own Sparkle `SPUUpdater` (FACT,
  `OraRoot.swift:15-76`). Two windows can hold duplicate tab objects
  (INFERENCE). Commands fan out over `NotificationCenter` with handlers
  filtering on window identity.
- Engine integration is a thin Swift wrapper (`Core/BrowserEngine/`, split
  out in PR #237, 2026-03-14). Some settings use semi-private KVC on
  `WKPreferences` (FACT, `BrowserPage.swift:27-39`).
- User script bridges registered in the **page world**, not an isolated
  content world, so any page script can post to them (FACT,
  `BrowserEngine.swift:29`, `BrowserPage.swift:58-68`). More below (security).
- Hard-coded Safari 26.0.1 UA via `applicationNameForUserAgent`, sent twice
  (FACT, `BrowserEngine.swift:21`; confirmed in PR #252). Will age.
- Swift 5.9 mode, macOS 15+, sandboxed, XcodeGen; deps: Sparkle 2.6+,
  Inject 1.5.2, FaviconFinder 5.1.5, AdGuard SafariConverterLib 4.2.2 (FACT,
  `project.yml:5-17`). No server, no account, no telemetry in the app.

### Storage locations and formats

| What | Where | Format |
| --- | --- | --- |
| Spaces, tabs, unused folders, history, downloads | `Application Support/Ora/OraData.sqlite` (sandbox container) (FACT, `ModelConfiguration+Shared.swift:10-14`) | SwiftData/SQLite + `-wal`/`-shm` |
| History | same DB | One row per URL per space with visit count — no individual visits (FACT, `History.swift`); search loads all rows on the main thread per keystroke (FACT, `HistoryManager.swift:61-82`) |
| Cookies/storage/cache per space | one `WKWebsiteDataStore(forIdentifier: space.id)` per space (FACT, `BrowserEngineProfile.swift:15`) | WebKit's own |
| Settings | `UserDefaults`, per-space keys like `settings.container.<uuid>.privacy` (FACT, `SettingsStore.swift:145-182`) | plist with JSON structs |
| Passwords | macOS Keychain, service `com.orabrowser.app.passwords`, `kSecAttrSynchronizable`, `AfterFirstUnlock`; metadata JSON in `kSecAttrGeneric`; list locked behind Touch ID/password (FACT, `PasswordManagerService.swift:76,260-272,387-400`) | Keychain items (own format; not Apple Passwords app items — INFERENCE) |
| Favicons | `~/Library/Caches/Favicons/<tab-uuid>.png` (FACT, `Tab.swift:385-393`) | PNG |
| Ad-block artifacts | `Application Support/Ora/ContentBlockers/{raw,compiled}/<list>/<revision>/shard-N.json` (FACT, `ContentBlockerArtifactStore.swift`) | JSON |

- No DB encryption beyond FileVault/Keychain (FACT). On DB open failure Ora
  tries to delete the wrong path and misnames `-shm`/`-wal`, so nothing is
  deleted and the app likely crash-loops on migration failure (FACT code;
  behavior INFERENCE).
- Only passwords are marked iCloud-Keychain-synchronizable; real sync is
  unverified (FACT flag, INFERENCE sync). Tabs/spaces/history never sync.

### Security and privacy posture (the part that matters for rac)

- **Every camera/microphone request from any site is auto-granted, no
  per-site prompt** (FACT, `TabBrowserPageDelegate.swift:129-136`,
  `BrowserPage.swift:398-408`). v0.2.14 lacks the macOS usage strings, so a
  contributor reports capture just hangs (CLAIM, PR #250). `main` added
  strings 2026-09-17, unreleased (FACT).
- **Address-bar spoofing likely works**: the page-world `listener` handler
  sets `tab.url` from a page-supplied `href` without comparing it to
  `webView.url`, and the address bar renders `tab.url` (FACT, code citations
  in dossier; spoofing itself INFERENCE, untested). The password bridge is
  safer — it uses the native `page.currentURL` (FACT).
- Ad blocking (AdGuard lists via SafariConverterLib, recursively split until
  WebKit accepts; keeps last-known-good on refresh failure; tested) is
  **off by default**. So is tracker blocking (hard-coded 25 domains).
  Fingerprint-spoofing JavaScript (fakes `navigator`, canvas, WebGL, audio;
  overrides `navigator.webdriver`) is **on by default** and reportedly
  breaks Google sign-in (CLAIM, open PR #252) (FACT for defaults, code).
- Launcher text goes to `suggestqueries.google.com` (debounced 0.2 s) by
  default because Google is the default engine (FACT,
  `SearchEngineService.swift:240`, `LauncherViewModel.swift:13,247`).
- FaviconFinder fetches each site's homepage through `URLSession.shared`,
  outside the space's cookie jar (FACT, library source at 5.1.5;
  reaching private tabs is INFERENCE).
- Sparkle auto-checks are ON in `Info.plist` even though the in-app toggle
  defaults off; the toggle probably doesn't stop Sparkle's schedule
  (FACT plist/defaults; behavior INFERENCE).
- Steady background cost in every page: 500 ms `setInterval` URL/title poll
  plus a whole-document `MutationObserver` re-running `querySelectorAll`
  on every DOM change; toolbar color snapshot every 0.25 s during load; a
  60 s timer walks every tab (FACT, `OraBrowserScripts.swift:88,209-211`,
  `Tab.swift:168-177`, `TabManager.swift:543`). Violates rac's "AI off (or
  any feature off) costs nothing" rule.

### AI and agent

- **None.** No assistant, agent, MCP, CLI, skills, local models. The only AI
  feature: launcher hands text to ChatGPT/Claude/Grok/Gemini/Perplexity/T3
  Chat/Copilot/Meta AI as a `?q=` URL (FACT,
  `SearchEngineService.swift:74-196`). Building-in an AI chat was closed
  "not planned for now" (PR #136, 2026-03-07); reason unstated — simplicity
  guess only (INFERENCE from issue #135).
- Extension support stalled on missing WebKit APIs ("not available out of
  the box from the webkit api", maintainer 2026-01-24, FACT, PR #137); the
  draft grants every extension `<all_urls>` with no consent. This is likely
  why extension-dependent Arc users can't move to Ora (INFERENCE).
- Design lesson for rac's agent: nothing a browser *acts on* (origin, URL,
  fill safety) may come from page-writable text; isolated worlds everywhere.

### Release, CI, and engineering facts

- Built entirely locally: XcodeGen → `xcodebuild archive` → Developer ID
  manual signing (team `3Y566D2A4G`) → `codesign --verify --deep --strict`
  → `create-dmg` → `notarytool submit --wait` with a keychain profile →
  staple **both DMG and .app** (FACT, `scripts/build.sh:40-60,115-145`).
- Appcast: private EdDSA key piped via stdin into
  `generate_appcast --ed-key-file -` (never written to disk at that step —
  but the key itself lives **in plain text in a local `.env`**, FACT,
  `scripts/publish.sh:69-70`). Appcast committed to `gh-pages`, served from
  GitHub Pages. Homebrew cask updated by a workflow on `v*` tags, using a
  classic PAT with full `repo` scope (FACT, `brew-release.yml:3-6`).
- CI is lint-only (SwiftLint, swiftformat --lint); **never builds or runs
  the 28 Swift Testing tests** (FACT, `.github/workflows/build-and-test.yml`);
  the latest run failed.
- Release notes: `generate-changelog.py` collects merged PRs between tags
  and has an LLM rewrite them under a JSON schema with rules ("Write for
  normal users", "Do not invent features", ignore lint/CI/refactors), plus
  a `--no-llm` fallback (FACT, `scripts/generate-changelog.py:172-227`).
- No upstream to sync at all — WebKit arrives with macOS; the only drift
  cost is the frozen UA string (FACT/INFERENCE).
- Process health red flags: lint-only CI, releaser's laptop as sole release
  machine, 6.5 months without a release, expired domain, 8 issues closed
  `not_planned` in one day by `linear[bot]` (likely a person's calls via
  Linear sync, INFERENCE), community PRs (AI chat, tree tabs, split,
  history) all closed 2026-03-07 (FACT).

### Motion parameters (verified line-by-line, dossier table)

Spring notation: `spring(response, dampingFraction)`; 1.0 damping = no
bounce. One-shot effects, no loops — one exception (a shortcut-recorder
border pulsing `easeOut(1.4).repeatForever`, FACT).

- Sidebar hide/show: `spring(0.2, 1.0)`. Edge-reveal: `.move(edge:)` +
  `easeOut(0.1)`; trigger strip 10 pt, then 40 pt armed padding.
- Launcher: backdrop opacity black 30%, card scale 0.9→1 + blur 2→0,
  `easeOut(0.1)`; anchors 250 pt from top (bug: installed at that fixed
  height regardless of window height, FACT).
- Tab-to-search border sweep: angular gradient 360° `linear(0.8)`, once,
  then fade `easeOut(0.3)`; 2 pt stroke + 8 pt glow stroke, blur 40,
  opacity 0.9.
- Dialogs: y −16, scale 0.96, `spring(0.3, 0.82)`; backdrop black 40%.
- Toasts (Sonner-like stack): show `spring(0.4, bounce: 0.2)`, dismiss
  spring bounce 0.15, restack bounce 0.5; genie-style exit (width −15%,
  height −25%, ~3.4° tilt, 16 pt slide, perspective 1/1200); max 3 visible,
  4.0 s lifetime.
- Downloads swipe (page beside spaces): threshold 25% width; commit
  `spring(0.45, 0.88)`, cancel `spring(0.35, 0.9)`; back layer x 12%·
  progress, scale −0.06·progress, fade to 50%.
- Copy URL roll: ±12 pt roll, `easeOut(0.3)`, holds 1.0 s.
- Tab insert/remove `spring(0.3, 0.8)`; drag `spring(0.2, 0.8)` with 1 pt
  dashed `[5,5]` outline; hovers `easeOut(0.15)`, buttons `easeInOut(0.12)`,
  press scale 0.95.
- **No reduced-motion support anywhere** (FACT, grep for
  `accessibilityReduceMotion` is empty).

### Visual language

Custom-drawn traffic lights from image assets; hidden title bar; window =
`NSVisualEffectView .underWindowBackground` + 30% theme tint; corner radii:
tabs/URL 10, launcher 20, settings cards 16, password popup 18, switcher 32,
capsules 99; macOS 26 uses system `ConcentricRectangle`. One fixed palette:
accent `#F16D34` light / `#FF9B51` dark, dark bg `#0F0E0E`. System font only,
mostly 12–14 pt. Spaces have no themes/colors (color theming explicitly
rejected via issue #153).

## What rac should take (ranked)

Cost scale in agent working days: XS <1, S 1–3, M 4–10, L >10.

1. **Keep rac's update feed on an un-expires-able host and add a Homebrew
   cask.** Ora's domain lapsed yet updates kept working because the Sparkle
   feed lives on `github.io` (FACT + INFERENCE). rac's feed already points
   at GitHub Releases (FACT, `patches/rac/updates/update-feed.patch:138`);
   keep it. Copy the `brew-release.yml` pattern (tag push → SHA-256 → edit
   cask → push tap), but use a fine-grained token limited to the tap, not
   Ora's full-`repo`-scope classic PAT (INFERENCE). Cost XS. Needs a tap
   repo + token.
2. **Ora's local release scripts as proof of the "local signed 0.1.0 build"
   fallback for rac's broken CI** (see `plans/context/ci-status.md`): copy
   the sequence — `notarytool submit --wait` with keychain profile, fetch
   status log on failure, double staple, stdin-piped EdDSA key for
   `generate_appcast` — but never store the key in a plain `.env` like Ora
   does (FACT). 58 releases shipped this way. Cost S; a local full build
   needs maintainer approval (AGENTS.md).
3. **Changelog-from-merged-PRs script with rules + `--no-llm` fallback**,
   reusing Ora's prompt rules and JSON schema. Cost XS–S.
4. **Tab-to-search colored chip with a single border sweep** in rac's
   command/address bar: build on Chromium's existing keyword mode (FACT,
   `omnibox_edit_model.h:345` in rac's tree) and the planned "Bangs".
   Parameters above (0.8 s one-shot sweep, 2 pt + 8 pt glow strokes).
   Under reduced motion, show the chip with no sweep. Cost S–M.
5. **AI websites as plain search destinations** (`claude.ai?q=`,
   `chatgpt.com?q=`, etc.). Cost nothing when unused, works with AI off.
   Offer as bangs — do **not** surface them by default in an empty command
   bar like Ora. These are undocumented URL forms that can break (INFERENCE).
   Cost XS.
6. **Per-site "Clear cookies & reload" / "Clear cache & reload"** in the
   menu bar and site control center; Chromium's `BrowsingDataRemover`
   supports origin filtering (FACT,
   `browsing_data_filter_builder.h:82` in rac's tree). Cost S.
7. **Copy-URL rolling label** (±12 pt, easeOut(0.3), 1.0 s hold) in rac's
   sidebar address bar. Cost S.
8. **Ctrl+Tab recent-tab switcher with thumbnails** (≤5 cards, ~200x125,
   commit on Ctrl release, mouse ignored until it moves); Chromium's tab
   thumbnail code can feed it (INFERENCE). Cost M.
9. **Arc import: reuse Ora's field map of `StorableSidebar.json`** —
   `sidebar.containers[].spaces[]` (`customInfo.iconType.emoji_v2`, `title`,
   `id`, `containerIDs`), `items[]` (`data.tab.savedURL`, `savedTitle`,
   `parentID`, `childrenIds`, `data.itemContainer`), `topAppsContainerIDs`
   for favorites — and fix Ora's gaps: user-granted file access, keep
   folders via `childrenIds`, add favorites once, create tabs unloaded,
   report counts. Cost M–L.
10. **Motion reference values** (dialogs `spring(0.3, 0.82)`, toasts bounce
    0.2/0.15, hovers `easeOut(0.15)`, downloads-swipe numbers) as data
    alongside Ardia's Dia spec. Cost none.
11. **Per-space logins as an option to research, not a decision.** Ora gives
    every space its own cookie jar (one `WKWebsiteDataStore` per space); rac's
    spaces share one profile (FACT, `docs/internals/glossary.md`). Arc's
    optional space↔profile binding is the model to examine; in Chromium a
    profile is heavy (FACT/INFERENCE). Cost L. Maintainer decides.
12. **Downloads as a swipe-in page beside spaces (optional)** reusing rac's
    sliding space pages; use Ora's gesture numbers. Cost M.

## What rac should avoid

1. **Trusting page scripts for anything the browser acts on** — URL, origin,
   whether content is safe to fill. Ora's spoofable `listener` handler is
   the cautionary example. rac's agent/AI scripts must run in isolated
   worlds with engine-supplied origin (INFERENCE grounded in FACT code).
2. **Granting permissions without prompts** (camera/mic bypass) or granting
   extension permissions without consent — Ora did both.
3. **Polling and snapshot loops** (500 ms intervals, per-0.25 s tint
   sampling, whole-document mutation observers). For toolbar tint use
   Chromium's `theme-color` and observer events.
4. **JS-level fingerprint spoofing** (breaks sign-in) — stay on
   ungoogled-chromium/Helium engine-level protections.
5. **Changing page DOM for browser chrome** (mark.js find-in-page, injected
   shield `div`); Chromium's native find bar and views overlays avoid both.
6. **App-modal page dialogs** (one `NSAlert.runModal` blocks the whole app),
   **one updater per window**, **DB-delete-on-failure-then-crash** error
   handling.
7. **Showing AI by default** in empty command-bar/launcher states.
8. **Public-claims drift**: site shows wrong license, advertises
   non-existent Split View, domain expired. rac's `site/` must state
   GPL-3.0, only shipped features, auto-renewing domain.
9. **Lint-only CI and mass un-commented issue closures**.
10. **Moving rac to WebKit.** Ora's extension stalled on missing WebKit
    APIs; staying on Chromium is rac's biggest edge (INFERENCE).

## Caveats

- **No hands-on run of Ora ever happened** (untrusted clone). All
  look/feel/behavior claims come from code reading.
- Address-bar spoofing is INFERENCE (untested); a WebKit behavior or missed
  check could block it. Arc-import failure under the sandbox is a strong
  INFERENCE (`~` resolving into the container, no file-access grant); issue
  #99 (import crash) closed unfixed.
- iCloud Keychain sync, camera-hang in v0.2.14, real project health
  (paused vs abandoned; Discord unchecked), and star-growth timeline are
  unverified.
- The 45.63 Speedometer figure at browserating.com may describe a
  *different* "Ora" — do not cite it for this Ora. No perf numbers exist.
- Space-switch duration is INFERENCE (~0.25 s, AppKit's `NSAnimationContext`
  default; the SwiftUI animation does not reach `NSPageController`).
- The "simplicity" framing for rejecting AI is inferred from a tree-tabs
  comment, not stated about AI.
- Researcher's overall confidence: **high** for counts, code facts, motion
  numbers, storage, release mechanics; **medium** for behavioral inferences.
- Health warning for any plan depending on Ora data: 2-person bus factor, no
  release since 2026-04-07, expired domain — treat Ora as reference
  material, not a dependency. rac's current upstream gap itself (Helium 7
  releases ahead, rac on Chromium 154) is a maintained-brief fact, not an
  Ora fact.

## Where to look in the full dossier

- Dossier: `plans/research/ora.md` (repo `plans/overhaul` branch).
- Snapshot table: lines 27–41. Feature tables (tabs/spaces/navigation/split/
  import/privacy) with exact file:line evidence: 43–155. UI + full motion
  table with per-interaction parameters: 155–237. Architecture/process
  model: 239–299. Storage table + what-leaves-the-machine list: 325–374.
  AI/agent absence and page-bridge lessons: 376–397. Build/release/CI:
  399–454. Strengths/weaknesses (critical): 456–519. Ranked ideas:
  510–587; Avoid list: 588–619. Open questions: 621–647. Full source
  citations (repo paths, GitHub issues/PRs, whois/Dig): 649–686.
  Line-by-line fact-check table (40 items, key corrections: license
  history, release cadence, `.env` key storage, re-tagged CLAIMs):
  688–747.
- rac cross-references cited in the dossier:
  `plans/context/ci-status.md` (local build fallback),
  `plans/context/roadmap-revision-2026-10-22.md` (Bangs),
  `patches/rac/updates/update-feed.patch:138` (feed on GitHub Releases),
  `docs/internals/glossary.md` (rac spaces share one profile).
