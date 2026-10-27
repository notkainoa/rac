# 06. Engineering platform and shipping

Citation keys used below. `ci-status` = `plans/context/ci-status.md`. `brief` = `plans/context/maintainer-brief.md`. `eng-matrix` = `plans/research/matrices/engineering-and-shipping.md`. Digests are `plans/research/digests/<slug>.md`, cited by slug (for example `helium` or `ardia`). The council is `plans/context/inboxzero/{opus,sonnet,kimi-k3}.md`. FACT = checked in a primary source or the repo. CLAIM = someone's self-report. INFERENCE = my reasoning.

## In plain English

Nobody can install rac yet. This plan fixes that, then keeps rac current.

First, we build one signed Apple Silicon copy on GitHub's free build machines. The last test run nearly finished. It died one step early on a bad download. A retry fixes that. If it fails again, we pay about $35 for a faster build machine. We don't build on the shared MacBook Air unless both fail.

Then we publish 0.1.0 and 0.1.1 quietly. That proves updates reach installed copies. Next we catch up with Helium. That moves rac from Chromium 154 to the current version, and the work gets harder every week we wait. After that, a daily robot checks each new Helium release and reports what broke.

Every change then goes through a pull request. Automatic checks run on each one, including the tests that exist but never run today.

The public launch for Arc users follows, aimed at early December. It ships the synced build with Arc import and a safer agent. The big redesign comes after the launch, on top of the synced code.

## What you need to decide

1. **06-D1. Where is the first release built?** Free runners, paid runners, or the maintainer's Mac. **Recommended: free runners (Apple Silicon, with a download retry) now; Depot the same day if that fails; the Mac last.**
2. **06-D2. Do Intel Macs get rac at launch?** Yes, or no. **Recommended: Apple Silicon only for 0.x.**
3. **06-D3. Ship a quiet release on today's Chromium 154 first?** Quiet 0.1.0 and 0.1.1, or wait for the sync. **Recommended: quiet preview now; the first announced release is synced.**
4. **06-D4. Ship first or revamp first?** **Recommended: ship, sync, launch, then revamp. Revamp design starts now.**
5. **06-D5. First sync path?** One jump to 0.20.1.1, or two steps via 0.19.4.1. **Recommended: one jump, then a small hop to Chromium 157.**
6. **06-D6. Sync how often?** Every Chromium major, or every other major plus security. **Recommended: every major, with a 7/14-day security rule; review after three cycles.**
7. **06-D7. Pay for build machines?** About $35 per release, or $0. **Recommended: yes, capped near $100 a month; ask Depot for open-source terms first.**
8. **06-D8. How strict is `main`?** PRs plus checks, or approvals too. **Recommended: PRs and checks required, 0 approvals, maintainer bypass.**
9. **06-D9. Where do C++ tests run?** Worktree-posted status, self-hosted runner, or release chain. **Recommended: worktree status now, release chain later; no self-hosted runner.**
10. **06-D10. Release channels?** Stable only, or stable plus beta. **Recommended: stable for launch; opt-in beta in December.**
11. **06-D11. Crash reports?** None, server-free user-posted reports, or a rac server. **Recommended: server-free, after launch.**
12. **06-D12. Move rac's own files out of patches into a plain folder?** **Recommended: yes, after the sync.**
13. **06-D13. Freeze `patches/rac` merges during the sync?** **Recommended: yes, for its 1 to 2 weeks.**
14. **06-D14. "Never slower than Helium" at launch?** Publish numbers, or soften the line. **Recommended: publish numbers; soften if the bench isn't ready.**

## Where we are today

**Releases.** Zero. `rac_version.txt` is 0.1.0. All nine signing, notarization and Sparkle secrets exist (FACT, `ci-status`). `MAC_TEAM_ID` is empty, and its effect on a signed build is unknown (FACT, `rac-baseline`). The feed is `releases/latest/download/appcast-<arch>.xml` (FACT, `patches/rac/updates/update-feed.patch:138`). GitHub's `latest` skips prereleases, so every real release must be a full release (FACT, `docs/operations/releases.md`).

**CI build.** `build.yml` builds both architectures in up to 10 chained 6-hour phases, with `fail-fast: true`, and the release job needs both artifacts (FACT, `.github/workflows/build.yml`). PR #20 (`tar --format pax`) is still open; `main` still checkpoints with plain `tar -c` (FACT, `.github/scripts/github_prepare_artifacts.sh`). Validation run 40222453249 used the fix and ran 26 h 21 min (FACT, `gh run list`). arm64 had 3,391 steps left after phase 5. x86_64 had 46,220, because it also builds a host arm64 Blink for the V8 snapshot. Phase 6 died when the 5.36 GB checkpoint arrived without `sums.txt`. After phase 1, sccache hits are about 0% because the 10 GB Actions cache thrashes (FACT, `ci-status`).

**Local machine.** The rac main checkout lives on kainoas-macbook-air: an Apple M1 (8 cores), 16 GB RAM, 101 GB free (FACT, `sysctl` and `df`, 2026-10-27). Its `build/src` is the base every worktree clones, and several agents share it (`AGENTS.md`). A local `build.sh` release has no updater: `write_gn_args` adds `enable_sparkle` only in `ci` mode (FACT, `devutils/shared.sh:58-66`). The MacBook Pro's specs are unknown.

**Checks.** `lint` passes. `sanity` applies all patches, fails on any "offset" line, and passes on a 30-second build timeout. It does not fail on fuzz (FACT, `.github/scripts/sanity-check.sh`). `pullfrog.yml` has 53 runs and 0 successes (FACT, `rac-baseline`). CI never compiles or runs 278 C++ test cases in 5 targets (`rac_ai` 153, `rac_agent` 85, `rac_spaces` 25, `rac_pip` 9, `rac_updates` 6). The 71 Python tests in `devutils/rac/test_*.py` don't run either (FACT, `rac-baseline`; 19 + 13 + 39 `def test` counted).

**Process.** No branch protection and no rulesets. 70% of commits went straight to `main`. There were 112 reviews and 0 approvals (FACT, `rac-baseline`).

**Upstream.** rac is on Helium 0.18.2.1 / Chromium 154, six releases and two majors behind 0.20.1.1 / 156. It has never synced and has no `upstream` remote (FACT, `rac-baseline`, `helium`). Chromium ships every two weeks; 157 lands 11-03. Two docs are wrong: `docs/internals/overview.md:69` ("four weeks") and `docs/operations/upstream-sync.md` ("no Apple developer account") (FACT, `helium`).

**Patch stack.** 180 patches and 869 upstream hunks in 216 files. 320 hunks (37%) are in `ui/views`, and 76% sit in files Helium also patches. There are 325 new files (43,282 lines) and 658 self-edits. 24 are `fix-*` patches (FACT, `rac-baseline`). At 0.20.1.1, 104 hunks fail with fuzz 2; only 46 fail first. At 0.19.4.1, 43 fail (FACT, `helium`).

**Crash reports.** Crashpad writes reports locally, then deletes them. Upload is off. The vision allows opt-in, per-crash sending (FACT, `docs/internals/overview.md`, `VISION.md`).

**Perf.** No benchmark exists. "Never slower than Helium" has never been measured (FACT, `rac-baseline`).

## What others do

- **Nobody finishes Chromium on free GitHub Macs.** Helium pays for Depot M4 runners: arm64 took 2 phases (6 h 43 min), at about $34 a release (FACT/INFERENCE, `helium`). Ardia built all 80 releases on the owner's M5 Pro, 2.5 h cold (FACT, `ardia`). Cra and Crest build the engine on a Mac they own (FACT, `cra`, `long-tail`). BrowserOS uses a self-hosted Mac Mini (`eng-matrix`). Ardia's x64 CI chain never finished (FACT, `ardia`).
- **Drift detection.** Cra: a daily free Linux job opens an issue with the exact command (FACT, `cra`). Zen: a weekly bot PR re-applies every patch (FACT, `zen`). Crest: every 6 hours, no fuzz allowed (FACT, `long-tail`). Helium: `bump-platform` opens a PR per bump (FACT, `helium`).
- **Patch surface.** Ardia has 492 hunks, only 26 in `ui/views`, and marker-guarded hooks with a `--check` (FACT, `ardia`). Zen symlinks new files into the tree, so editing them needs no patch refresh (FACT, `zen`). Cra has 11 hunks, but sits on CEF's 1,044 (FACT, `cra`).
- **Channels and gates.** Ardia: one appcast with a `nightly` channel, a smoke test that updates the previous build, and a stable-only perf gate (FACT, `ardia`). T3 Code promotes a nightly's commit to stable (`eng-matrix`).
- **Tests.** No engine-based browser runs engine-side tests in CI; Zen has 683 test files and runs none (FACT, `zen`, `eng-matrix`).
- **Privacy evidence.** Stedding publishes a recorded run of every host a fresh profile contacts (FACT, `long-tail`).
- **Security cadence.** Stedding ships fixes within 7 days if exploited in the wild, otherwise 14 (FACT, `long-tail`).
- **Council.** All three reviewers put the same items first: one signed release with the update loop proven, the first sync, Arc import, a safe agent default, and CI plus a protected `main` (FACT, `opus.md` §8, `sonnet.md` §8, `kimi-k3.md` §8).

## Options

### Build route for the first release (A1 to A5)

**A1. Free GitHub runners, Apple Silicon only, with a hardened download.** We keep today's CI but drop Intel. We add a retry around the checkpoint download that killed the last run. Then we run the chain. It costs nothing and doesn't touch the shared Mac. One build takes about a day and a half.
- Details: merge PR #20. Wrap the checkpoint download in a retry. Up to 3 attempts, each checking that `sums.txt` exists and `sha256sum -c` passes. Add an `arches` input (default `arm64`). Make the release job download and publish only the arches built, and let `github_write_appcasts.sh` skip a missing arch. Set `fail-fast: false`.
- Pros: $0. It proves the real CI signing path. The secrets live only in GitHub. The validation run says arm64 would have finished (FACT, `ci-status`).
- Cons: about 28 to 36 h a build (INFERENCE from 26 h 21 min reaching phase 6). It has never finished once. Each failure costs a day.
- Effort S: about 2 agent-days. Risk: medium. Locks in nothing.

**A2. Paid fast runners (Depot first; GitHub larger runners or Namespace as alternates).** We point the same CI at faster rented Macs. A release builds in about 7 hours instead of 30. It costs money each time.
- Details: change the runner label and move sccache to Depot Cache. Helium's numbers give about $34 per arm64 release, plus about $20 a month (INFERENCE, `helium`). Helium's runners are sponsored, so ask Depot about open-source terms. GitHub larger-runner and Namespace prices were not researched (?).
- Pros: 2 phases instead of 6. It also fixes the cache thrash. It leaves room to compile test targets. It makes a two-week cadence realistic.
- Cons: ongoing spend, about $900 a year for arm64 at one release per two weeks (`eng-matrix`). It adds a vendor dependency.
- Effort S: about 1 agent-day. Risk: low. Locks in a vendor, but switching back is a label change.

**A3. Build, sign and notarize on the maintainer's Mac.** One Mac does the whole release, as Ardia does (the matrix's first choice). It looks fast and free. On this Mac it is neither.
- Details: the rac Mac is a shared M1 Air with 16 GB RAM and 101 GB free (FACT). An official ThinLTO build needs its own tree, because the main checkout's component-mode tree is the worktree base. That tree fits only as an APFS clone with other space freed (INFERENCE). A cold build could take 10 to 16 h at full CPU and may swap during the link (INFERENCE: free runners are 3 virtual M1 cores). Other agents' builds stall meanwhile. Scripts need `enable_sparkle` and the key, a temporary keychain with `set-key-partition-list`, an App Store Connect API key for `notarytool`, and a stapled DMG.
- Fit with "never take the foreground": the build is background work. Keychain dialogs are foreground, so they must be made impossible, not clicked. Test launches use `--rac-launch-in-background` and a throwaway profile (FACT, `patches/rac/dev/launch-in-background.patch`), and DMGs mount with `hdiutil attach -nobrowse`.
- Pros: no cloud spend. Ardia shows it works on a fast Mac.
- Cons: needs approval for a full build (AGENTS.md). It ties up the shared Mac for most of a day and doesn't prove CI. Signing keys sit next to the real profile.
- Effort M: about 3 agent-days plus a 10 to 16 h build. Risk: high on this hardware. Locks in a manual release step.

**A4. Hybrid: build locally, sign in CI.** We build on the Mac, upload the unsigned app, and let a tag-triggered CI job sign and publish it, as Cra does. It keeps keys off the laptop. It still needs A3's heavy local build.
- Effort M: 2 to 3 agent-days plus A3's build. Risk: medium-high. Not recommended unless A1 and A2 both fail.

**A5. Self-hosted runner on the maintainer's Mac.** GitHub would run jobs on the Mac itself. The repo is public, so a pull request from a stranger could run code on the machine that holds the real profile and other agents' work (`eng-matrix`). **Rejected.**

**Recommendation: A1 now, A2 as the same-day fallback, A3 only if both fail.** This differs from the matrix's ranking. The matrix didn't know the Mac's specs, which are now measured. A1 is the cheapest real proof of CI, and it nearly finished already. A2 is a label change away if A1 breaks. If a two-week cadence is chosen (06-D6), A2 likely becomes the default, because 30 h builds leave no slack for a failed run.

### Intel Macs (B1, B2)

**B1. Apple Silicon only for 0.x.** Intel Mac owners can't use rac at first. macOS 27 is Apple Silicon only. Ardia, Nook and Crest are too (FACT, `helium`, `eng-matrix`). This halves CI time and cost.
- Trap: once an Intel build ships, every later release must carry `appcast-x86_64.xml`. Otherwise Intel copies stop updating silently (INFERENCE from the fixed feed path). The site must say "Apple silicon only".

**B2. Both from day one.** On free runners x86_64 needs about 8 to 10 more phases than the chain allows (INFERENCE, `eng-matrix`). It is affordable only with A2, at about $99 a release (INFERENCE, `helium`).

**Recommendation: B1.** Revisit in Q1 2027, once paid runners and demand data exist.

### Sequencing: ship or revamp first (C1 to C3)

**C1. Ship today's code quietly, sync, launch, then revamp.** We prove the release machinery on what exists. Then we catch up with Helium. Then we launch for Arc users. The redesign lands after that, on current code.
- Pros: the update loop exists before strangers install anything. The sync happens while cheapest: failed hunks went from 43 to 104 in one Helium release (FACT, `helium`). Revamp patches are written once, on 156 or later. Arc users arrive before 12-22. This matches the council (`opus.md` §8, `sonnet.md` §8).
- Cons: launch ships today's UI, and a redesign follows soon after. Zen shows forced new interactions with no way back anger users (FACT, `zen`), so keep familiar behavior reachable.

**C2. Revamp first, ship once.** Sync debt grows weekly, revamp patches on 154 need rebasing, and the Arc window likely closes first.

**C3. Ship, revamp, then sync.** The revamp lands on the stale base: the worst of both.

**Recommendation: C1.** Revamp threads (plans 01 to 03) can design, prototype and spike now. They shouldn't land patches on hot upstream files until the sync merges.

### First sync path (D1, D2)

**D1. One jump to 0.20.1.1.** About 46 first-failure hunks plus the sidebar design merge, and one rebuild (FACT/INFERENCE, `helium`).

**D2. Two steps through 0.19.4.1.** 19 first-failure hunks in the first step, but two full rebuilds (FACT, `helium`). Rebuilds are the scarce resource on the Air.

**Recommendation: D1.** Then hop to Helium 0.21.x (Chromium 157, expected about 11-06) right away. That second hop is the first real cadence test.

### Cadence (E1 to E3)

**E1. Every Chromium major.** Sync within 7 days of Helium's first release for each major. Take point releases as they land. rac stays at most one major behind. It needs fast builds (A2). Effort per cycle: 1 to 3 agent-days plus a build, if hunks shrink (INFERENCE, `rac-baseline`).

**E2. Every other major, plus security point releases.** Half the syncs, but each roughly doubles in size (INFERENCE from 43 to 104).

**E3. Extended-stable milestones (8 weeks).** Too slow. Helium doesn't track extended stable (`eng-matrix`).

**Recommendation: E1, with E2 as the fallback.** Security rule: a Helium release carrying a fix for a bug exploited in the wild ships within 7 days, any other security fix within 14 (Stedding's rule, `long-tail`). Review after three cycles: if a sync takes more than 3 agent-days, fall back to E2.

### How the C++ tests run (F1 to F4)

**F1. A status posted from the worktree.** The agent already builds in its worktree. Before opening a PR, it runs the five test targets there. A script posts a commit status (`rac/unit-tests`) for that exact commit with `gh api`. Branch protection requires it on PRs that touch `patches/rac/`. No stranger's code runs on the Mac.
- Pros: free, minutes per run (incremental builds), works today.
- Cons: the result is trusted, not reproduced; anyone with write access could post it. Closure build times are unknown (?, `eng-matrix`).
- Effort S: about 1 to 2 agent-days.

**F2. In the release chain.** After the last build phase, build and run the five targets from the same `out/Default`, before the release step. Whether an `is_official_build` configuration builds test targets cheaply is unknown (?, `eng-matrix`). With A2 this is realistic.
- Effort S to M: about 2 agent-days plus measuring.

**F3. A self-hosted runner.** Rejected for the reason given under A5.

**F4. Per-PR compile on free runners.** It can't finish (`eng-matrix`). Rejected.

**Recommendation: F1 now, plus F2 once A2 or a finished A1 chain exists.** Run `rac_agent_unittests` first, because it guards the safety core, then spaces, updates, ai and pip (`eng-matrix`).

### Release channels (G1 to G3)

**G1. Stable only.** One feed, as today.

**G2. Stable plus opt-in beta in the same appcast.** Ardia does this with `<sparkle:channel>` (FACT, `ardia`). Beta DMGs sit on GitHub prereleases, whose download links work; only the `latest` alias skips them. The latest stable release's appcast gains a beta item, re-uploaded with `--clobber` (INFERENCE). Betas take the next patch numbers, and a good beta's build is promoted unchanged (the T3 Code pattern). The feed URL never moves. `RAC_DMG_STYLE=beta` packaging exists (FACT, `sign_and_package_app.sh`). Users get one "Get beta updates" switch on About rac. Effort S: about 2 agent-days. Risk: low. Locks in the channel name.

**G3. A separate "rac Beta" app.** It would have its own bundle ID and profile. That means a second identity to keep permanent, and a second profile users must move. Rejected.

**Recommendation: G1 for launch, G2 in December.** The beta switch is a justified setting: some users genuinely want early builds.

### Crash reports (H1 to H3)

**H1. None.** Users write issues by hand. That gives the least information.

**H2. Server-free, per crash.** After a crash, the next launch shows one calm line: "rac quit unexpectedly. Send a report?" Yes shows the report: stack frames and loaded modules, no page memory. The user opens a prefilled GitHub issue or copies the text. The maintainer symbolicates it with the release's stored `.dSYM` files. rac runs no server, and every report needs a yes for that crash (`docs/internals/overview.md`). Unverified: whether the source is a stack-only text from Crashpad's minidump, or macOS's `.ips` file (?).
- Effort M: about 4 to 6 agent-days. It replaces `disable-crash-uploads.patch`.

**H3. rac crash server.** Host Helium's `minidumpster` (AGPL) with per-crash uploads and 30-day retention (FACT, `helium`). Richer data, but it is rac's first server: operations, a privacy policy, AGPL duties if modified.
- Effort L: about 8 to 12 agent-days, plus hosting.

**Recommendation: H2, in January.** Move to H3 only if H2 reports are too thin to fix crashes.

### Patch hygiene (I1, I2)

**I1. Ratchet and refactor in place.** A hunk counter, a no-fuzz gate, folded `fix-*` patches, deleting dead code, thinner hooks.

**I2. I1 plus moving rac's own files out of patches.** The 325 new files (43k lines) move into a plain `rac-src/` folder. A step like `replace_resources.py` copies them into `build/src` (FACT, `devutils/shared.sh:14-20`), or dev trees symlink them, as Zen does (FACT, `zen`). Patches then hold only upstream hooks. PR diffs of rac's code become normal diffs, not diffs of diffs; today 658 self-edits carry 26k lines of patch-on-patch churn (FACT, `rac-baseline`).
- Cons: a one-time migration that changes every agent's workflow. String and GN files need care. It overlaps plan 03.
- Effort M: about 5 to 8 agent-days.

**Recommendation: I2, started after the sync merges.** Doing it during the sync doubles the risk.

## Recommended plan

Dates assume work starts 2026-10-28. "Agent-days" are one agent working one day. The maintainer's time is review and approvals.

### M0. Unblock the pipe (10-28 to 10-31)

Goal: a CI chain that can finish for arm64, and cheap checks on every PR.

Tasks:
1. Merge PR #20. Add the checkpoint download retry and verification to `build-phase.yml` and `github_unpack_archive.sh`. If `sums.txt` is missing or the checksum fails, retry up to 3 times, then fail clearly.
2. Add an `arches` input to `build.yml` (default `arm64`). Set `fail-fast: false`. Make the release job, `github_prepare_release.sh` and `github_write_appcasts.sh` handle arm64 only. PR #16 made missing feeds fail; keep that, but only for the arches built.
3. Add free PR checks on Linux: the 71 Python tests, `he validate series`, a hunk counter, and a no-fuzz apply. The hunk counter prints upstream hunks per group and in `ui/views`. The sparse apply method is in `plans/research/helium.md` (lines 582-599). Make `sanity-check.sh` fail on "with fuzz", not only on offsets.
4. Delete `pullfrog.yml`, or fix it if the maintainer wants it.
5. Ask Depot about open-source terms. Price GitHub larger macOS runners.
6. Start a build-only arm64 run on the PR branch.

Acceptance: the arm64 chain reaches "build finished" once. A forced bad download is retried and recovered. PR checks run in under 15 minutes.

Verification: CI run links. A test run with a corrupted artifact. Check output in a PR.

Patch surface: none. These are CI and script files only. Effort: about 3 agent-days (Sonnet).

### M1. Quiet 0.1.0 and 0.1.1; prove the update loop (11-01 to 11-05)

Goal: the first signed, notarized release reaches a clean Mac and updates itself.

Tasks:
1. Release preflight. Confirm what an empty `MAC_TEAM_ID` does under real signing. Check whether `PROD_MACOS_SPECIAL_ENTITLEMENTS_PROFILE_B64` covers every claimed entitlement: T3 Code warns that an app claiming more than its profile grants won't launch (`eng-matrix`). Notarize and staple the DMG too, or verify Gatekeeper accepts it as is.
2. Gate the input-injecting dev switch `--rac-window-screenshot-requests` out of release builds behind a GN arg. It can click and type (FACT, `rac-baseline`). The passive `--rac-window-screenshot` can stay.
3. Run the release workflow for 0.1.0. Release notes say "Preview. Not for daily use. Chromium 154."
4. Add an `install-smoke` job on a free macOS runner (a clean Mac). It attaches the DMG with `-nobrowse` and runs `spctl -a -vv`, `codesign --verify --deep --strict` and `stapler validate`. It launches rac with a throwaway profile and `--rac-window-screenshot`, and checks the PNG has real pixels.
5. Ship 0.1.1 (a one-line, visible change). Add an `update-smoke` job: install 0.1.0, make a space and a pinned tab, let Sparkle update from the real feed, relaunch. Confirm version 0.1.1, data carried over, and no Keychain prompt.
6. Keep `RELEASE_READY = false`.

Acceptance: both releases are public on GitHub. The smoke jobs pass. Screenshots of both versions' About rac pages.

Verification: job logs, screenshots and a short video of the update from the runner. Nothing runs on the shared Mac.

Patch surface: one small `dev/` patch for the gate. Effort: about 3 agent-days (Opus for signing, Sonnet for the jobs).

If A1 fails twice here, switch to A2 that day. If A2 is refused, ask the maintainer about A3.

### M2. First Helium sync to 0.20.1.1 (10-29 to about 11-12, in parallel with M0 and M1)

Goal: rac on Chromium 156, with every feature working.

Tasks:
1. Restore the fetch-only `upstream` remote. Freeze `patches/rac` merges (06-D13).
2. Free disk on the Air first (101 GB free), with approval, or run the sync on the MacBook Pro.
3. In a `sync/helium-0.20.1.1` worktree, merge the tag; only `patches/series` should conflict (FACT, `helium`). Adopt the new `prepare_sources` and `configure_build` signatures, drop calls to the deleted `retrieve_and_unpack_resource.sh` and `devutils/build_tools.sh`, and use Helium's prepared tarballs.
4. Mechanical failures first (`ui/BUILD.gn`, moved `tabs/` files, context drift), by Sonnet or an open-weight agent.
5. Design merges by Opus. Rebuild sidebar-reveal on Helium's expand-on-hover overlay, keeping only rac's behavior: full or hidden, 100 ms dwell, top-edge toolbar reveal (`helium`). Move settings onto Helium's Layout section, hiding unsupported layouts with one hook.
6. Fix compile errors in rac's 325 new files and the agent's actor-layer calls (`type_tool.cc` changed 332 lines, FACT, `helium`).
7. Refresh every patch with no fuzz and no offset. Fix the two wrong docs.
8. Full build with approval. Run all five test targets, the Python tests, and the surface checklist from AGENTS.md.

Acceptance: `quilt push -a` is clean with fuzz 0. The five test targets pass. The hunk count doesn't grow (target: fewer than 869). Screenshots show sidebar full and hidden, edge reveal, light and dark, two space themes, address bar in the toolbar and in the sidebar, incognito, split view, and onboarding. A short video shows edge reveal and a space swipe.

Patch surface: shrinks sidebar-reveal and settings by adopting Helium's work. Effort: L, about 6 to 10 agent-days and 1 to 2 full builds. Calendar: 1 to 2 weeks.

### M3. Drift detector and the second hop to Chromium 157 (about 11-10 to 11-20)

Goal: prove the cadence on a small sync.

Tasks:
1. A daily scheduled job on a free Linux runner. It reads the latest helium-macos tag through the GitHub API (read-only; it posts nothing upstream). On a new tag, it does a sparse apply with fuzz 0. It then opens or updates one issue in rac's own repo listing failing patches by group, the hunk budget, and the exact commands to run (the Cra and Zen patterns).
2. Sync to Helium 0.21.x. Record the agent-days spent.
3. Release 0.2.0 on Chromium 157 (a minor bump for a sync, per `docs/operations/releases.md`). Use A2 if A1 is too slow to fit.

Acceptance: the detector opened the 0.21 issue itself, the hop took 3 agent-days or fewer, and `update-smoke` moves 0.1.1 to 0.2.0.

Effort: M, about 2 agent-days for the detector and 2 to 4 for the hop.

### M4. Gates, protection and evidence (about 11-03 to 11-25, overlapping M2 and M3)

Goal: every change passes automatic checks, and rac's claims are measured.

Tasks:
1. **Branch protection** (06-D8). A ruleset on `main`: PR required, the M0 checks required, plus `rac/unit-tests` on PRs that touch `patches/rac/`. Block force-pushes and deletion. The maintainer can bypass. **Do not require linear history**: Helium syncs are merge commits (FACT, `docs/operations/upstream-sync.md`). Use 0 required approvals, since agents push as the maintainer.
2. **Agent PR flow,** as one short `AGENTS.md` section: worktree → branch → `devutils/rac/test.sh` (runs the affected test targets, posts the status) → `gh pr create` with screenshots → a review agent comments → the maintainer merges. A label check flags PRs that raise the hunk count or touch the seven hot files (`rac-baseline`).
3. **`test.sh` and the posted status** (F1).
4. **Network capture.** A free macOS runner installs the release DMG. It runs a fresh profile for 10 minutes with `--log-net-log`, before and after Helium-services consent, and compares the contacted hosts with a published list (the Stedding pattern, `long-tail`). The list goes on the site's privacy page.
5. **Perf harness vs Helium** (06-D14). Add `devutils/rac/bench/`, driving both browsers over the DevTools protocol with throwaway profiles. Measure cold launch to first paint, new tab, tab switch, sidebar reveal, memory at 1, 10 and 20 tabs, and idle CPU and wakeups. Use interleaved, rotated rounds and report medians with min and max (Ardia's method, `ardia`). Compare with the Helium release on the same Chromium major. Run it on a free macOS runner against downloaded DMGs: no compile, and no noisy shared Mac. Confirm once on an idle real Mac, since runner GPU timing is unknown. Gate stable releases: fail if a median is over 5% worse than the previous stable or Helium.

Acceptance: a PR without checks can't merge. One measured bench table and one host list are published.

Effort: M, about 6 to 8 agent-days in total.

### M5. Arc-refugee launch (target week of 11-30; hard stop 12-15)

Goal: Arc users can move to rac before Arc stops on 12-22.

Launch requires all of these:
- The synced, signed build passing `install-smoke` and `update-smoke`.
- Arc import from plan 04.
- The agent default fix and the first injection evals from plan 05. Brand risk is too high without them (`opus.md` §8 item 3).
- The network host list published, and perf numbers published or the site line softened.

Tasks:
1. Fix public claims: "thin layer", "It asks before it acts", "four weeks" (`rac-baseline`).
2. Site says "Apple silicon, macOS 13+" and, plainly, no Netflix-class DRM (no Widevine; CLAIM, `helium`).
3. A "Moving from Arc" page and comparison pages.
4. Flip `RELEASE_READY` and add the Vercel deploy hook (`docs/operations/releases.md`).
5. Draft Show HN, r/ArcBrowser and Product Hunt posts for the maintainer to post.
6. Measure success only by GitHub download counts. No analytics.
7. Issue templates for crashes and import problems; a triage agent labels, never closes.

Acceptance: the download page shows the release. A fresh Mac goes from download to imported Arc spaces in under 5 minutes. Record that on a runner or a clean user account.

Effort: M, about 4 agent-days (Sonnet or Opus for site work, per the UI rule).

### M6. After launch (December to February)

- **Beta channel (G2)** in December, right after launch.
- **Cadence:** Chromium 158, 159 and 160 land 11-17, 12-01 and 12-15. Run each through detector → sync worktree → beta → stable within 7 days.
- **Patch hygiene (I2):** hunk targets of under 600 by end of January, then under 400 total and under 150 in `ui/views` by end of February (`rac-baseline`). Order, per the group table in `eng-matrix`: delete the dead `look/horizontal-tabs` restyle; fold the 24 `fix-*` patches (target about 120 patches); one `//chrome/browser/ui/rac` dependency instead of 26 `ui/BUILD.gn` edits where visibility allows; Ardia-style marker hooks with a drift check for one-line registrations (`ardia`); one rac-owned adapter in front of Chromium's actor layer (with plan 05). The counter becomes a ratchet: no increase without a `hunk-budget-ok` label.
- **Unit tests in the release chain (F2)** once builds finish in 2 phases.
- **Crash reports (H2)** in January.
- **Intel (B2)** reconsidered in Q1, only with A2.
- **Golden screenshots** in Q1: comparisons from the release DMG on a runner, with goldens stored as release assets, not on `main` (AGENTS.md forbids committed PR screenshots).

## Fit with the non-negotiables

- **Private.** Nothing new phones home. Download counts come from GitHub, not analytics. Crash reports stay server-free and per-crash (H2). The network capture turns "never phones home" into evidence. GitHub still sees each hourly update check, as today (FACT, `rac-baseline`). Watch item: the launch sends more users to Helium's services, whose terms don't cover forks (FACT, `helium`); keep `origin_override` as the fallback.
- **Never slower than Helium.** The bench and its stable-only gate measure this for the first time. Until numbers exist, the site line is a promise, so 06-D14 asks whether to soften it.
- **AI off costs nothing.** Unchanged. The F1 status runs `rac_ai_unittests`, including `MasterSwitchGatesEntryPoints`. Plan 05 owns a broader check.
- **Cheap to update.** This plan is mostly about this rule: the detector, the cadence, the no-fuzz gate, the hunk ratchet, and the overlay folder.
- **Calm UI.** Only two visible surfaces are new: the crash prompt (one line, per crash) and the beta switch. Neither animates.
- **GPL-3.0.** Paid runners don't affect the license. Ardia's Apache-2.0 files may come in with credit and its NOTICE kept. Hosting `minidumpster` (H3, not recommended) would carry AGPL duties if modified (FACT, `helium`).
- **Opinionated.** Only one setting is added: the beta switch.
- **Bent, with reasons.** (1) The first releases ship Chromium 154, two majors old, as labeled quiet previews, so the update loop is proven before anyone relies on it. (2) PRs need 0 approvals: a solo maintainer can't approve their own PRs, and automated gates matter more (`opus.md` §9 item 5).

## Dependencies on other plans

- **01 ui-shell.** The sync rebuilds edge reveal on Helium's overlay; plan 01 starts from that result. UI patches on hot files wait for M2.
- **02 visual-design-and-motion.** The bench measures frame times and sidebar reveal, so motion changes get numbers. Golden screenshots cover themes and dark mode.
- **03 core-architecture.** It owns the overlay folder (I2), the actor-layer adapter, hook style, and the Views or native-shell spike (`long-tail` C6). The hunk targets here are its budget.
- **04 data-storage-import-sync.** Arc import is a launch gate, and so is Ardia's Keychain no-silent-reset fix (`ardia` item 2), which prevents silent data loss. Backups must precede any storage migration a sync forces.
- **05 agents-and-ai.** The safe default and the first injection evals are launch gates. It also owns the `chrome://inspect` remote-debugging decision (`long-tail` B1). Recorded-replay and model evals need M4's runners or F2.
- **07 power-features.** Ardia's power and frame patches land only after the bench exists, so each is measured. New features wait for the sync and should respect the hunk budget.

## Risks and unknowns

- **The free chain may still fail** for a new reason. Mitigation: A2 the same day. Each A1 attempt costs about 1.5 days.
- **The shared Air is the bottleneck.** Every Chromium major needs a base-tree rebuild there, every two weeks. The rebuild time is unknown. Over about 8 h, the cadence crowds out feature work. Then use the MacBook Pro, more disk, or remote execution (`SISO_REAPI_ADDRESS` is supported, FACT, `devutils/shared.sh:68`).
- **First signed build surprises:** the empty `MAC_TEAM_ID`, an entitlements mismatch, an unnotarized DMG, or Sparkle asking for update consent on the first or second launch (?). M1's smoke jobs exist to catch these.
- **The sync's compile cost is unmeasured.** The dry run sees text only (FACT, `helium`). Chromium 157 may arrive mid-sync. Do the hop after, not a re-target during.
- **The PR flow may slow agents.** Keep checks under 15 minutes; let docs and plans bypass.
- **F1's posted status can be faked** by anyone with write access (today, only the maintainer).
- **Runner GPU timing** may make bench numbers noisy (?).
- **Crash report source:** whether macOS still writes `.ips` files when Crashpad handles the crash (?).
- **Launch timing:** if plan 04's import or plan 05's evals slip past 12-15, decide between launching without import and missing Arc's last week.
- **Helium's services and forks** (above). Anthropic's terms for `claude-agent-acp` belong to plan 05 (`long-tail`).

## Open questions

1. What are the MacBook Pro's specs, and may it be used for syncs or builds?
2. Will Depot sponsor rac? What do GitHub larger runners and Namespace cost and deliver for Chromium?
3. Does an `is_official_build` tree build the five test targets cheaply? How many extra steps does each closure add?
4. How long does a component-build base rebuild take on the Air after a Chromium major?
5. Does the first signed launch prompt for update consent? Does Keychain prompt across an update?
6. Should golden screenshots live in release assets or a separate branch?
7. Is a 5% perf tolerance against Helium right, or should it be 0% for tab switch and typing?
8. Should agents get a bot GitHub identity, so the maintainer's approval becomes a real gate?
9. What launch date does the maintainer want inside the 11-30 to 12-15 window?

## Draft thread brief

**DRAFT. Not to launch until the maintainer approves this plan and its decisions.**

Thread: **Engineering and shipping** (one long-running thread, multi-agent).

Goal: ship rac's first signed releases, sync rac with Helium, and keep it current. Gate every change with checks. Launch for Arc users by mid-December. Follow `plans/06-engineering-and-shipping.md` milestones M0 to M6, with the maintainer's answers to 06-D1 to 06-D14.

Read first: `AGENTS.md`, `VISION.md`, `plans/context/ci-status.md`, `docs/operations/{releases,upstream-sync,worktrees}.md`, `plans/research/matrices/engineering-and-shipping.md`, `plans/research/digests/helium.md`.

Hard rules:
- Nothing goes to any `imputnet` or `ungoogled-software` repo. The detector only reads.
- Never edit `helium-chromium/` or Helium's patch folders.
- No full local build, `he reset`, or new Chromium tree without the maintainer's OK.
- Never take the foreground. Use temporary keychains and API keys so no dialog appears. Launch rac only via `worktree.sh run`, or with `--rac-launch-in-background` and a throwaway profile.
- Never change the update key or feed URL, or lower the version. Never mark a release as a prerelease or draft.
- The maintainer posts all launch text.

Work split: CI scripts, smoke jobs, detector and hunk counter go to Sonnet or a strong open-weight model. Signing preflight, sync design merges and branch protection go to Opus. Site pages follow the UI rule. A separate review agent comments on each PR.

Deliverables, each a PR with proof: M0 a green arm64 chain; M1 0.1.0 and 0.1.1 with smoke logs, screenshots and an update video; M2 the sync with the surface screenshot matrix and test results; M3 the detector issue and 0.2.0; M4 the ruleset, `test.sh`, host list and bench table; M5 the checked launch list.

Done when: rac is public, on a Chromium no more than one major behind Helium, updated in place by Sparkle at least twice. `main` is protected. The tests run. Each later sync takes 3 agent-days or fewer.
