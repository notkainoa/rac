# Matrix: engineering and shipping

Topic: how rac and nine comparable projects build, track upstream, release, update and test. Built 2026-10-27 from the context pack and the 18 digests in `plans/research/digests/`, with the full dossiers checked for CI, release and branch-protection details. Nothing was run or built.

Legend: `?` = not found in the research. `(inf.)` = my inference, not a fact from a source. Numbers carry the date of their dossier (2026-10-25 unless noted). Where sources differ I give the audited figure: rac's patch stack is 869 to 871 hunks, its tests are 278 cases (the brief says about 284), and rac is 6 Helium releases behind (the brief says 7).

## In plain English

rac cannot ship yet for two reasons. Its automated build is too slow on free GitHub Macs. And it has never caught up with Helium, so it sits two Chromium versions back. The other projects got around the build problem in three ways: they build on the owner's Mac (Ardia, Ora, Cra's engine), they pay for fast cloud Macs (Helium), or they have no engine to build (Nook, Ora). The fastest route for rac is to build, sign and notarize an Apple Silicon-only 0.1.0 on the maintainer's Mac. Then sync with Helium and ship 0.1.1 to prove updates work. The free-runner fix continues as the long-term path. To stay current, add a daily check like Cra's that tests whether rac's patches still apply, and cut the places where rac edits Chromium. Run the cheap tests in CI now. Run the heavy ones on a Mac.

## The matrix

Columns: rac, Helium, Ardia, Cra, Zen, Nook, Ora, BrowserOS, T3 Code, Aside. T3 Code is not a browser (a coding-agent harness), so many cells read "n/a". Aside is closed source, so its cells come from docs and inspection of the shipped app.

### A. Engine and upstream tracking

| Row | rac | Helium | Ardia | Cra | Zen | Nook | Ora | BrowserOS | T3 Code | Aside |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Engine and lag behind upstream | Chromium 154.0.8037.92 via Helium 0.18.2.1. 2 majors and 6 Helium releases behind (156 / 0.20.1.1). 157 is due 11-03 | Chromium 156.0.8078.47 (0.20.1.1). Ships 2-4 days after Chrome stable | Chromium 155.0.8059.84 + Helium 0.19.4.1. 1 major behind; 0.20.1.1 not adopted | CEF 156.0.14 = Chromium 156.0.8078.48. Current | Gecko. Firefox 158.0.1 stable; dev on 159 RC. Days behind | System WebKit. No engine to lag; moves with macOS | System WebKit. Same. Frozen Safari 26.0.1 user-agent string | Chromium 155.0.8059.26. 1 behind Chrome 156; has skipped majors | n/a. Electron 44.9.3 pins Chromium 152.0.7977.167 (2 majors behind rac) | Chromium 154.0.8037.100. Same 2 milestones behind as rac |
| Patches / hunks and how managed | About 180 patches, about 870 hunks, about 217 files (320 hunks in `ui/views`), 325 new files. Quilt on top of Helium's 346 + 23 | Core: 346 patches, about 91k lines, 1,645 files. macOS: 23. GNU `patch`; sanity fails on any offset | 60 patches, 492 hunks, 205 files (only 26 hunks in `ui/views`). Plus 46 marker-guarded hooks. Skips 15 Helium patches | 5 patch files, 11 hunks, 6 files, 195 lines. CEF itself carries 118 patch files, 1,044 hunks (maintained by CEF) | 264 patches, 868 hunks (958 with external) over 287 files. One patch per file; new files symlinked in | None. About 20 private WebKit selectors and 2 AppKit swizzles | None. Semi-private KVC on `WKPreferences` | 421 patch files (277 edits = 618 hunks; 144 new files). Per-file store, not quilt. 39 features. `bpatch` keeps mtimes | None | C++ fork; count ? (about 48 `aside_*` files seen) |
| Update cadence and tracking | Manual. Never synced. No `upstream` remote. Docs wrongly say a 4-week Chromium cycle (it is 2 weeks). No detector | `bump-platform` bot opens an update PR per Chromium bump. 12 releases in 40 days (one per 3.3 days) | Pinned by tag or commit. A `guard` stage refuses an update that changes what a skip protects. Each new Chromium needs the owner's OK and a full rebuild. No detector found | Daily `cef-updates.yml` on a free Linux runner compares the pin with Spotify's index and opens an issue with the exact command. Build is by hand: 154 to 156 in an afternoon (engines 5.5 h apart) | Weekly Tuesday bot PR re-applies all patches on a Firefox release candidate. Synced Firefox 155-159 within days | n/a (follows macOS) | n/a (follows macOS) | Manual bumps (142, 145, 146, 148, 151, 155). Agent-drivable `git merge-tree` base bump | Pinned tools (Chrome, cloudflared); provider CLIs tracked by manifest and capability probes. No engine to sync | Follows Chromium milestones; 6 builds sat 6 to 30 days behind stable. Tooling ? |

### B. Build, CI and caching

| Row | rac | Helium | Ardia | Cra | Zen | Nook | Ora | BrowserOS | T3 Code | Aside |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Build system | GN + siso (since 2026-09-13), quilt. `build.sh`, `dev.sh` / `he` | GN + siso/autoninja. Official build + PGO phase 2. Prepared Chromium tarballs (1.98 GB base + about 1.4 GB per arch) | pnpm + Turborepo, CocoaPods + Xcode. Engine: GN + autoninja | Swift / ObjC++, `build.sh`, CMake + Xcode. CEF via `automate-git.py` | `surfer` + mach (Firefox build). `npm run build:ui` rebuilds only the UI | One Xcode project, 7 local + 3 remote SPM packages | XcodeGen + xcodebuild | `bos_build` (Python/uv) + `bpatch` (Rust). GN official, no PGO, `symbol_level=0` | `vp` (Vite+) over pnpm. Electron arrives prebuilt | Chromium build (Xcode 27.1) + pnpm/rolldown monorepo. Node SEA daemon and CLI |
| CI provider and runners | GitHub Actions, free `macos-latest` (3 M1 cores, 7 GB RAM, 14 GB disk). `lint`, `sanity`, `build.yml` (10 chained phases per arch) | GitHub Actions on sponsored Depot `depot-macos-latest` (M4, 8 cores, 24 GB, $0.08/min) | GitHub Actions. Engine job on a 3-core runner (10 phases). Release job has only run as a dry run | GitHub Actions `macos-26` (app), free Linux (detector). Engine is not built in CI | GitHub Actions Linux 8-vCPU runners cross-compiling macOS. A Mac only for 2 steps | GitHub Actions `macos-26`; launch check on `macos-15` | GitHub Actions, lint only | GitHub Actions, 30 workflows. Self-hosted Mac Mini (macOS); WarpBuild BYOC 32 vCPU (Linux/Windows) | GitHub Actions on Blacksmith 2-8 vCPU | GitHub Actions macOS runners; how Chromium builds there ? |
| Build time | Never finished. Free runner: about 1 Blink file per 6.5 s. arm64 would finish in phase 6 (up to about 36 h, inf.). x86_64 still had 46,220 steps left after phase 5 | 14 h 21 min end to end. arm64: 2 phases (6 h 43 min). x86_64: 3 phases (13 h 05 min) | Owner's M5 Pro: first full official build 2.5 h; incremental + ThinLTO relink about 7 min; 45 GB | Engine by hand: 1-2 h same major, 3-4 h new major (self-report). App CI time ? | 42-49 min per arch cold; full 3-stage PGO about 4.5 h | Median 6 min 39 s per tag release (5:40 to 15:37) | ? (local builds) | Cold 4-7 h, warm 3-6 h | ? (JS packaging only) | ? |
| Caching | sccache on the GitHub Actions cache. 10 GB cap thrashes: about 96% hits in phase 3 of the first dry run, about 0% after phase 1 of the validation run. Checkpoint tar between phases | sccache on Depot Cache (WebDAV, about 3x faster than rac's). Plain-tar checkpoints | ? (zstd checkpoint between jobs; compiler cache not stated) | GitHub cache of prebuilt `vendor/cef`, keyed on the pin hash | sccache off in the observed run; PGO profiles cached (only Twilight reuses them) | ? | ? | No compiler cache. Warm checkout + APFS clone per build | ? | ? |

### C. Releases and updates

| Row | rac | Helium | Ardia | Cra | Zen | Nook | Ora | BrowserOS | T3 Code | Aside |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Who builds releases | Nobody yet. CI never completed. Local build is a fallback that needs approval | CI (Depot) | Owner's Mac for all 80 (`scripts/release.sh`). CI release workflow only dry-ran, after all 80 | CI signs and publishes on a tag push; the engine comes from the owner's Mac | CI. `Deploy-Release` environment needs a reviewer. Windows signing step likely manual (inf.) | CI on tag | Owner's laptop (local scripts) | Self-hosted Mac Mini CI; a human runs `release publish` | CI. Nightly is automatic; stable promotes a nightly's commit | ? |
| Signing and notarization | Developer ID, notarization and Sparkle EdDSA: 9 secrets set, never exercised. `MAC_TEAM_ID` empty | `sign_chrome.py` + `notarytool`. Sparkle EdDSA | Developer ID (U5L5T3NGVV), hardened runtime, notarized + stapled. Relaunches the exported app and re-verifies | Developer ID in a temp keychain; notarize + staple. Ad-hoc build if secrets are missing. Renderer sandbox is off | `rcodesign` + `notarytool` + stapler. Own RSA-4096 MAR key | Developer ID, hardened, `notarytool --wait`, staple | Developer ID, `notarytool`, staple app and DMG. EdDSA key kept in a plain `.env` | Developer ID + `notarytool`, temp keychain | Developer ID + notarization (App Store Connect key). Provisioning profile for passkeys | Developer ID (8CPD4K4TBB), hardened runtime. Notarization of the app ? |
| Update framework and channels | Sparkle 2. Feed on GitHub `releases/latest`. Hourly check. One channel; no prereleases or drafts allowed | Sparkle 2 EdDSA. `sparkler` builds the appcast from GitHub releases. Deltas vs the last 5. Channels ? | Sparkle 2.9.6. One appcast with stable + nightly channel. Phased rollout. 8 h check | Sparkle 2. GitHub appcast. 8 h check. One channel (inf.) | Firefox updater + MAR. Static `update.xml` on GitHub Pages. Twilight nightly. No deltas | Sparkle 2. Appcast on `gh-pages`. Channels ? | Sparkle 2 (one updater per window). Appcast on `gh-pages`. Homebrew cask | Sparkle 2, full 382 MB DMG, no deltas. Plus a sidecar OTA feed (15 min) and extension feed | electron-updater on GitHub Releases. Nightly, preview (no feed), stable. Deltas | Chromium's Omaha updater + component updater |
| Release count and frequency | 0 | 134 since 2025-05-04; 25 in the last 90 days | 80 in 31 days (48 stable, 32 nightly) | 14 in 3 days | 196 total; 67 stable in 12 months (one per 5.4 days); Twilight every 2 days | 9 between 09-18 and 10-24 | 58 total; none since 2026-04-07 | 291 total (53 browser); 15 server + 14 extension in 30 days | 730 in 237 days (619 nightly, 52 preview, 58 stable/alpha) | 54 browser builds in 8 months (about 7 per month); 122 component builds |

### D. Quality, license and people

| Row | rac | Helium | Ardia | Cra | Zen | Nook | Ora | BrowserOS | T3 Code | Aside |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Tests run in CI | None compiled or run. `sanity` applies patches and passes on a 30 s build timeout. 278 C++ cases in 5 targets and 71 Python tests exist but never run | Lint, `sanity` (fails on any patch offset), pytest on its own utils. No Chromium tests | CLA and linked-issue checks in CI; ? for unit tests. Release script: smoke test + perf gate. 90 `.test.mjs`, 11 `.test.ts`, 13 Swift test files | Build + `codesign --verify`. No tests exist | Apply + lint only. About 683 test files, none run | Build + launch alive after 20 s. No Xcode test target | SwiftLint only. 28 tests never run | TS lint/typecheck/tests, Python, codegen drift, 1,661 Rust tests. No Chromium compile or unit tests on PRs | 1,556 test files: unit, Playwright browser tests, 8 server shards, Rust, replay fixtures | ? (browser tests not visible) |
| Branch protection | None. No rulesets. 70% of commits go straight to `main`; 112 reviews, 0 approvals | ? | ? (owner commits straight to `main`) | ? | `dev` protected, no required checks | ? | ? | ? | ? (vouch-list bot on PRs) | n/a |
| Crash reporting | Uploads off; Crashpad writes locally then deletes. Opt-in per crash is planned | Own `minidumpster` at `crash.helium.computer`; kept 30 days, org-only. Consent gate ? | No Crashpad. Opt-in telemetry (off) carries crash signatures | ? | Crash reporter not compiled in | ? | ? | Sentry on the sidecar; PostHog events with no opt-out | ? (analytics on by default) | Crashpad to `browser-crashpad.aside.com` |
| License | GPL-3.0 | Browser GPL-3.0; services AGPL-3.0; ungoogled code BSD-3-Clause | App GPL-3.0; own files Apache-2.0; CLA permits relicensing | MIT | MPL-2.0 | GPL-3.0 (name and icon are trademarks) | GPL-3.0 (site still says MIT) | AGPL-3.0; CLA grants sublicense and sell rights | MIT | Proprietary |
| Contributors | 1 maintainer; 96% of commits AI co-authored | 2 maintainers; ungoogled supplies Chromium bumps | Owner 1,787 of 1,809 commits; 11 outsiders | 1 author (27 commits, 23 Claude co-authored) | Lead 85% of commits; 258 contributors | 1 maintainer (461 of 465 recent commits); 17 contributors | 2 core = 89% of commits; 23 total | Team of 4 (self-report); contributor count ? | 473 contributors; 7,119 merged PRs | 8 on the YC profile; 15 public repos |

Also seen in the long-tail digest (not given columns): Crest ships a native shell through one patch touching 95 files / 205 hunks (plus a 14k-line overlay) and a self-hosted Mac engine build (1,440 min timeout), a 6-hourly upstream check that needs every hunk to apply without fuzz, and 268 releases in 66 days. Stedding carries 103 patches / 3,086 hunks on plain Chromium 156 and ships security fixes within 7 days (actively exploited) or 14. Refrax carries 7 patches / 42 hunks plus a 6.8k-line overlay by running Chromium out of process.

## What the matrix says

- Nobody else compiles Chromium on free GitHub Macs and finishes. Helium pays for Depot. BrowserOS uses its own Mac Mini. Crest and Cra build the engine on a Mac they own. Ardia's CI engine build has also never finished. Zen finishes in under an hour only because Firefox cross-compiles from Linux, which Chromium cannot do (inf.).
- Several projects depend on a Mac they control for the heavy step: Ardia and Ora build every release there, Cra builds its engine there, BrowserOS runs CI on a self-hosted Mac Mini. Ardia shipped 80 releases that way in 31 days.
- The automatic upstream-drift checks found are Zen's weekly bot, Helium's `bump-platform`, Cra's daily detector and Crest's 6-hourly check. rac has none and has never synced.
- The patch-surface leaders are Ardia (492 hunks, 26 in `ui/views`) and Cra (11 hunks, but CEF carries 1,044 more). rac is near Zen's size (868 hunks) and well above Ardia in `ui/views`.
- Among the engine-based browsers, none runs tests of its engine-side code in CI. Only T3 Code and BrowserOS run real test suites, and those are TypeScript and Rust. rac's gap is common but not good.
- Branch protection is known for only two projects: rac has none, and Zen's `dev` is protected with no required checks. For the rest the answer is `?`.

## Options to get rac's first release out

Context from `ci-status.md`: the tar fix (PR #20) works, so phases resume. The new limits are raw CPU on 3-core free runners, a 10 GB Actions cache that thrashes, and one flaky 5.36 GB checkpoint download that killed arm64 one phase from the end. On the validation run arm64 had 3,391 steps left after phase 5; x86_64 had 46,220.

Costs are in money and calendar time for the maintainer plus agents. Estimates marked (inf.) are mine.

**Do regardless (small, prerequisite for options 2 to 5): harden the checkpoint download.** Retry the artifact download, verify `sums.txt`, and re-download on a mismatch, so one bad download cannot cancel a 30-hour chain. Cost: $0; about a day. It would have saved the validation run's arm64 build.

### Ranking

1. **Build, sign and notarize an Apple Silicon-only 0.1.0 on the maintainer's Mac (Ardia, Ora and Cra pattern).**
   - Cost: $0 in cash. Time: days. Ardia's first full official build took 2.5 h on an M5 Pro (45 GB); the maintainer's Mac spec and a release-config build time are not in the research (?). Add a script modeled on Ora's `build.sh` (`notarytool submit --wait` with a keychain profile, fetch the log on failure, staple both app and DMG) and feed the EdDSA key by stdin, never a `.env`.
   - Risk: needs the maintainer's approval for a full build (AGENTS.md). One machine is a single point of failure (Ora, Ardia). It does not prove CI. A release build is `is_official_build`, not the dev tree, and the dev tree has rac's names substituted into string files, so build from a clean flow or confirm the dev tree produces an identical product (?, see `docs/internals/overview.md`). A signed app that claims an entitlement its provisioning profile does not grant will not launch (T3 Code's warning), so launch the signed result before publishing.
   - Unblocks: the first signed, notarized, Sparkle-updatable release. Then a second local release (0.1.1, after the Helium sync) proves the update loop, which is the part nobody has seen work. Download page stays hidden until then (`RELEASE_READY`).
   - Note: 0.1.0 would ship Chromium 154, two majors old. Keep it as the unannounced proof release, and make the first public one the synced build.

2. **Finish the free-runner path for Apple Silicon only.** Merge PR #20, add the download retry, and make the release job accept a missing `appcast-x86_64.xml` (PR #16 made it fail on missing feeds, and `docs/operations/releases.md` expects both).
   - Cost: $0. Time: about 2 days of CI work, then one chain of about 6 phases (up to about 36 h per release, inf.).
   - Risk: sccache is about 0% after phase 1 because of the 10 GB cap; the chain has never finished once. Intel Macs get nothing at first. Helium notes macOS 27 is Apple-silicon only, and Ardia, Nook and Crest are Apple Silicon only too, so the loss is small.
   - Unblocks: releases that do not need the maintainer's Mac, and the base for tests in the same chain.

3. **Paid fast runners: Depot first, with a second look at GitHub larger runners or Namespace.**
   - Cost: from Helium's own timings, arm64 is about 6.7 h, about $34 per release; both architectures about 14 h and about $99; plus about $20/month (inf., from `helium.md`). At one release per two weeks that is roughly $900 a year for arm64 only and $2,600 for both, plus the plan (my arithmetic). Depot Cache also fixes the sccache thrash. Price for GitHub larger macOS runners and anything about Namespace: ? (not researched). Helium's Depot runners are sponsored; ask Depot about open-source terms.
   - Time: about a day to switch runner labels and add the cache.
   - Risk: ongoing spend and a vendor dependency; a free-tier plan is unknown.
   - Unblocks: 2-phase arm64 builds and room for test compilation. Best fit if releases come every two weeks.

4. **Local build plus CI signing (hybrid).** Build the app locally, upload the unsigned bundle as an artifact, and let a tag-triggered CI job sign, notarize, build the appcast and publish (Cra's release workflow shape).
   - Cost: $0; about 2-3 days to write the job. Upload size is not in the research (?; Helium's arm64 DMG is 113 MB).
   - Risk: still needs the local build; CI signing is as untested as it was. Keeps the keys off the laptop.
   - Unblocks: a repeatable publish step and a reviewed path for secrets, without waiting on the engine build.

5. **Self-hosted runner on the maintainer's Mac (BrowserOS and Crest pattern).** Warm checkout, APFS-clone per build, long timeouts (BrowserOS 1,200 min, Crest 1,440 min).
   - Cost: $0 if it is the existing Mac, or the price of a dedicated Mac (not researched, ?). Time: 1-2 days. Warm builds ran 3-6 h at BrowserOS.
   - Risk: highest. The repo is public, so a fork PR could run code on a machine that holds the real browser profile and signing keys. Needs a dedicated user or machine, runs only for `workflow_dispatch` and tags, and no PR triggers. Several agents already share each Mac.
   - Unblocks: tests (option under "Testing") and fast incremental builds. It is the best home for C++ unit tests and screenshot runs.

6. **Keep both architectures on free runners.** x86_64 builds a second (arm64) host copy for the V8 snapshot and had 46,220 steps left after 5 phases. At the observed slope of 5k to 10k steps per late phase it needs about 8 to 10 more phases (inf.), more than the 10-phase chain allows. Not recommended.

Decision for the maintainer: option 1 gets a signed release out in days and proves signing and Sparkle; option 2 is the free long-term path; option 3 is the paid shortcut if option 2's chain proves too slow. Options 1 and 2 can run in parallel.

## Options for staying current with Helium

### Cadence

Facts: Chromium ships a major every two weeks from M153. Helium follows in 2-4 days, with a minor bump per major and point releases in between (12 releases in 40 days). The dry run shows the cost of waiting: at 0.19.4.1 (one major ahead) 43 hunks fail; at 0.20.1.1 (two majors ahead) 104 fail, and 121 of 180 patches apply with fuzz 2, 107 with fuzz 0. The gap doubled in one release.

| Option | What it means | Cost and risk |
| --- | --- | --- |
| A. Every Helium tag | Sync and release for each of about 9 tags a month | Not feasible by hand. Use only for detection |
| B. Every Chromium major | Sync within about 1 to 2 weeks of Helium's first release per major; take point releases of the same major as they land | Keeps rac at most one major behind (Ardia's position). Needs a fast build (options 2 or 3 above). First sync: 3 to 7 days plus a rebuild; later syncs 1 to 2 days if hunks shrink (baseline, inf.) |
| C. Every other major, plus security | Sync every 4 weeks; take Helium point releases for security in between | Cheaper. Stedding's rule is security fixes in 7 days (exploited) or 14. Aside shows even funded teams sit 6 to 30 days behind |
| D. Extended-stable milestones (8 weeks) plus security | The baseline's suggestion | Slowest; the gap and failed hunks grow between syncs. Helium itself tracks stable majors, not extended stable, so fit is unverified (?) |

Suggested order: B if builds can be made cheap (option 3 or a warm Mac), otherwise C. First step either way: sync now to 0.20.1.1. Two ways, from `helium.md`: one jump (about 46 first-failure hunks plus the sidebar design merge, one rebuild) or two steps via 0.19.4.1 (19 first-failure hunks, two rebuilds). The first sync must also rework CI: upstream deleted `retrieve_and_unpack_resource.sh` and `devutils/build_tools.sh`, which rac's scripts still call, and added new `prepare_sources` / `configure_build` signatures.

### Reduce the patch surface

Where the hunks are (from `rac-baseline.md`, `helium.md`, `chromium-agent-internals.md`):

| rac area | Patches / upstream hunks | Sync result at 0.20.1.1 | What to do |
| --- | --- | --- | --- |
| `look` | 20 / 161 (only 792 lines of new files) | 9 of 20 fail (14 hunks) | Biggest hunks for the least code. Move behind single hooks; delete the dead `horizontal-tabs` restyle |
| `spaces` | 26 / 127 | 11 of 26 fail (18 hunks) | Keep logic in rac-owned views; thin hooks |
| `ai` | 39 / 98 | 7 of 39 fail (7 hunks) | Mostly rac-owned files already; fold the `fix-*` patches |
| `pinned` | 18 / 95 | 6 of 18 fail (7 hunks) | As above |
| `settings` | 13 / 91 (110 hunks across settings resources) | 6 of 13 fail (15 hunks) | Take Helium's new Layout section instead of re-patching; hide unsupported layouts with one hook |
| `sidebar-address-bar` | 10 / 64 | 3 of 10 fail (12 hunks) | Same |
| `agent` | 19 / 58 (21 upstream files, about 207 lines) | Low: about 4 failed hunks, 2 compile fixes | Put one rac-owned adapter between the agent and Chromium's actor layer, which Chromium and Helium both churn |
| `sidebar-reveal` | 5 / ? | 5 of 5 fail (12 hunks) | Hard design merge: Helium rebuilt frameless mode around expand-on-hover. Rebuild on its overlay and keep only rac's semantics (full or hidden, 100 ms dwell) |

Hot files (patches by rac): `chrome/browser/ui/BUILD.gn` (26; 25 mechanical hunks at 0.20.1.1), `settings_localized_strings_provider.cc` (13), `prefs_util.cc` (11), `browser_command_controller.cc` (10), `browser_view.cc` (9), `vertical_tab_strip_region_view.cc` (9; 16 conflicting hunks), `browser_view_tabbed_layout_impl.cc` (8). 320 hunks (37%) are in `ui/views`; 76% of all hunks sit in files Helium also patches.

Moves, with who proves them:
- **A hunk budget in CI.** Count hunks per area on every PR and fail on a ceiling. Targets from the baseline: under 400 total (from 869), under 150 in `ui/views` (from 320). Cra's 11-hunk set and Ardia's 492 show the range. About a day to build the counter; 2 to 4 weeks of refactoring (baseline, inf.).
- **Marker-guarded hooks with a drift check (Ardia).** `apply.sh --check` reports drift and a `g_ardia_*` pointer turns a lost hook into a compile error. Good for the many one-line registrations.
- **New files symlinked into the tree (Zen).** Editing a new file then needs no patch refresh. rac already puts feature code in new files; this removes the refresh step.
- **One `//chrome/browser/ui/rac` dependency instead of 26 BUILD.gn patches**, where visibility rules allow.
- **Fold the 24 `fix-*` patches** (target about 120 patches). Splits the 658 self-edits into patches a reviewer can read.
- **No-offset sanity gate (Helium and Crest).** rac's `sanity` tolerates fuzz; Helium fails on any offset and Crest needs every hunk to apply without fuzz.
- **Do not move to CEF.** CEF carries 1,044 hunks of its own; Cra moves the cost into private-API swizzles and loses Helium's privacy patches. Ardia tried CEF and left. Do not build deeper into Chromium's tab strip either: files move each release (the Unified Tabstrip moves already hit `tabs/`).

### A drift detector like Cra's

Cra's daily workflow compares one pin with an index and opens an issue with the command to run. Zen's weekly bot goes further and re-applies patches. For rac:

1. A daily scheduled job on a free Linux runner reads the latest helium-macos tag with the GitHub API (read-only; it posts nothing upstream, per AGENTS.md).
2. On a new tag it merges the tag into a scratch branch (conflicts expected only in `patches/series`), applies Helium's series and then rac's with fuzz 0, using the sparse method in `helium.md` (runs in minutes on free runners).
3. It opens an issue in rac's own repo: patches failing per group, hunks per area against the budget, and the exact commands to sync.
4. It must be built after the first sync, since it depends on the new CI script signatures.

Cost: about 1 to 3 days (Helium's take #1: S). Needs no secrets and no build. Risk: the text-only apply cannot see compile errors in rac's 325 new files, behavior changes in frameless mode, or `.grd` string conflicts (stated caveat in `helium.md`).

## Testing and quality gates

What exists: 278 unit cases in 33 files across 5 standalone GN `test()` targets (`rac_ai_unittests` 153, `rac_agent_unittests` 85, `rac_spaces_unittests` 25, `rac_pip_tests` 9, `rac_updates_unittests` 6), 71 Python tests, and `test-spaces.mjs` (398 lines). CI runs none of them. There are no UI tests for most groups (pinned tabs has 1) and no agent evals.

### Which unit tests to compile in CI, and how

Because the targets are standalone (`autoninja -C out/Default chrome/browser/rac/ai:rac_ai_unittests`, as a patch comment shows), a build compiles only each target's dependency closure, not Chromium's whole `unit_tests`. How many extra steps that is: ? Measure on a worktree first.

Order by value per cost:
1. **`rac_agent_unittests` (85).** The guard, TOCTOU re-validation and the permission levels live here, including `AutoAsksOnlyForRiskAndForeignTyping`. This is the safety core; compile and run it first.
2. **`rac_spaces_unittests` (25).** Guards storage and data-loss behavior. Its first version depends only on base, prefs test support and gtest, so it is the cheapest closure; later patches add sessions and tab-group dependencies.
3. **`rac_updates_unittests` (6).** Tiny and guards the update path nobody has exercised.
4. **`rac_ai_unittests` (153).** Largest; pulls `//chrome/browser/rac/ai:browser` and `//net`.
5. **`rac_pip_tests` (9).** Heaviest closure (`chrome/test:test_support_unit`, content test support, page info). Last.

How, in order of fit:
- **Now, free, on every PR:** wire the 71 Python tests and the existing `he validate series` (about 1 hour; baseline item 6). Add the no-offset sanity gate and hunk counter.
- **Release gate, in the build chain:** after the final phase, build and run the five targets from the same `out/Default`, and put it before the "Create a release" step. Open question: whether an `is_official_build` configuration builds test targets at all (?). If not, a second non-official out directory is a second large build, so prefer the Mac route.
- **Nightly or pre-release on a warm Mac** (maintainer's Mac or a dedicated self-hosted runner, option 5): incremental builds of the five targets take far less than a full build (minutes in a worktree per the AGENTS.md claim, ? for the test closure).
- **Not on free runners per PR.** A test target in the 6-hour phase chain adds steps to a build that already cannot finish; and the cache is about 0% after phase 1.

Also protect `main`: require the cheap checks and a PR, with the maintainer able to bypass. Today 70% of commits skip PRs and 112 reviews have 0 approvals. Zen shows a protected branch without required checks is not enough.

### Screenshot and smoke tests

rac already has a harness: `--rac-window-screenshot=<path>` writes rac's own window after first paint (needed because `screencapture -l` is blank on macOS 26), with `-requests` able to click, type and swipe, and `--force-prefers-reduced-motion`. Plan:
- **Run against the built DMG, not a compile.** After the release build, a free macOS runner downloads the artifact, launches it with a throwaway profile and takes screenshots. That needs no Chromium compile, so it fits free runners. Whether a headless runner renders GPU content correctly: ?.
- **A fixed matrix:** sidebar full and hidden, light and dark, two space themes, reduced motion, onboarding, an agent confirm card, the site control center. Start with "PNG has real pixels" (not blank, not all black; the rule AGENTS.md already states), then add golden comparison. Where to store goldens is a maintainer call: AGENTS.md forbids committing PR-only screenshots, so use release assets or a separate branch instead of `main`.
- **Update smoke test (Ardia and the local-test recipe in `docs/operations/releases.md`):** launch the previous build, let Sparkle update to the new one against a local feed, check data carries over, and check rollback. Add Nook's habit of launching on the oldest supported macOS (rac supports 13+; availability of such runners: ?).
- **Network capture (Stedding):** a fresh-profile run that logs the hosts contacted and compares them to a published list. Supports the first non-negotiable with evidence; today "never phones home" is a claim.
- **Perf versus Helium (Ardia and Zen):** tab switch, sidebar reveal, memory at 1/10/20 tabs, idle CPU. Needs both builds on one Mac, so it belongs on a warm machine, not a free runner. Turns "never slower than Helium" (unmeasured today) into a number.
- **Tension to settle:** the screenshot flags are in every build, and the baseline recommends gating them out of release builds (hours of work). If they are gated out, screenshot CI needs a build variant that keeps them.

### Agent evals

No eval or red-team suite exists, and the known `auto` gap (cross-site navigate and model-typed text with no card) is untested for exploitability. Tiers:
1. **Deterministic, every PR, no model:** extend `rac_agent_unittests` with fixtures for the guard and critic, and add T3 Code's tool-risk annotation test (every tool declares readonly/destructive/idempotent/open-world, and a missing declaration fails the test). Cost: days.
2. **Recorded replay, nightly:** record real ACP sessions and hostile test pages once, then replay them through the real ACP client, guard and controller, replacing only the agent process (T3 Code's replay fixtures). Needs a built browser, so a warm Mac. Cost: 1-2 weeks.
3. **Model evals, weekly or before a release:** 30 to 50 hostile local pages (baseline target), 3 to 4 models, both run modes (`ask`, `careful`, `auto`), at least 3 runs per case because the ego(lite) benchmark's own variance rivals its gaps. Include the planted-text case where a small model obeyed instructions every run (Nook's claimed result). Cost: 1-2 weeks to build plus model spend per run (not estimated, ?). BrowserOS's conformance suite shows the fixture pattern (real browser, hostile pages, nightly), though it tests tools rather than models. ego(lite)'s MIT benchmark harness has a pluggable adapter if rac wants outside tasks too.
4. **Do first:** fix the `auto` chain (guard change, 1-2 days; needs sign-off), then write the eval that proves the fix, before the agent is opened to outside agents.

## Unknowns

- How long a release-config arm64 build takes on the maintainer's Mac, and whether the main checkout's dev tree (71 commits behind `main`, rac names substituted) can produce a release-identical build.
- Whether Depot gives open-source terms; GitHub larger-runner and Namespace pricing and speed (not researched).
- Whether an `is_official_build` config builds the unit-test targets, and how many extra ninja steps each of the five test closures adds.
- Whether the checkpoint tar fix keeps working over a full 6-phase arm64 chain; the 10 GB cache cap will keep thrashing without a bigger cache.
- The effect of the empty `MAC_TEAM_ID` under a real Developer ID, and whether `PROD_MACOS_SPECIAL_ENTITLEMENTS_PROFILE_B64` exists and covers the passkey entitlement (T3 Code warns an app claiming more than its profile will not launch).
- Branch protection, crash-report handling and CI details marked `?` in the matrix for Helium, Cra, Nook, Ora, BrowserOS, T3 Code and Aside. Aside's CI and notarization are not visible. Ardia's CI test coverage is not stated.
- Whether Helium's x86_64 timings (13 h vs 6.7 h arm64) transfer to rac, and whether Helium's phase-2 resume was checked against its logs (inference).
- Cost of the dry-run's fuzz-2 results is an estimate (text-only, not re-run, medium confidence). Compile errors and behavior changes in rac's new files are unmeasured.
- Whether a Helium-aligned cadence (B) is affordable for one maintainer; that depends on build cost and how much the sync shrinks once hunks drop.
- Whether a golden-screenshot store outside `main` fits the AGENTS.md rule on committed screenshots.
- Numbers drift: stars, release counts and run states were taken 2026-10-25 to 10-27; the validation run (40222453249) results are the latest in `ci-status.md`.

## Sources

Context (all under `plans/context/`):
- `maintainer-brief.md`, `ci-status.md` (including the validation run 40222453249 and the root cause for the tar fix).

Digests (all under `plans/research/digests/`): `rac-baseline.md`, `helium.md`, `ardia.md`, `cra.md`, `zen.md`, `nook.md`, `ora.md`, `browseros.md`, `t3code.md`, `aside.md`, `long-tail.md`, `ego-lite.md`, `pomerado.md`, `chromium-agent-internals.md` (agent patch surface, dry-run), `local-first-and-sidecars.md` (signing parts, CI note), `agent-stacks.md`, `closed-ai-browsers.md`, `motion-and-feel.md` (read for engineering facts; little used).

Dossiers checked for exact details (under `plans/research/`): `cra.md` (CI, release pipeline, CEF detector), `t3code.md` (build, release, CI), `zen.md` (branch protection, contributors), `rac-baseline.md` (no branch protection or rulesets), `helium.md` (crash handler, services), `aside.md` (crash server), `browseros.md` (contributor and telemetry rows), `ardia.md`, `nook.md`, `ora.md`.

Repo files read: `docs/operations/releases.md` (release steps, secrets, local update test), `.github/workflows/` (file list), and `test()` targets in `patches/rac/{agent,ai,spaces,pip,updates}/*.patch` (target names and dependency lists).
