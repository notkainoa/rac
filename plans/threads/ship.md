# Thread brief: Ship (engineering and shipping)

> **DRAFT: do not launch until the maintainer approves the plans.**

Follow ["Every thread"](README.md#every-thread) in the README: reading, step 0, streams, the build queue, moving to 156, workflow stages, verification standard, and hard constraints. This brief adds only what is specific to Ship.

## Goal

Launch a signed, notarized rac on Chromium 156 on day 19 (Mon 11-16), with updates proven. On the way: the build queue on day 0, the sync to Helium 0.20.1.1 merged by day 7, a quiet 0.1.0 built from the synced 156 tree (fired about day 7, published about day 9), and the launch build 0.2.0 fired on day 13, which proves the in-place update from 0.1.0 on day 15. There is no 154 build (D3). Release builds are fire-and-forget: start one and keep working.

## Owns

Plan 06 M0 to M5 and launch gates G9 to G14. Also the build queue (D63), the short freeze and the 156 base (D62), the merge order, `patches/series` order, cadence syncs, the drift detector, the bench, the host list, launch site pages, and later the beta channel, crash reports, and the plain-folder move (D58).

## Decisions it depends on

- **Group A:** D1, D2, D4 (free first, Depot asked later by the maintainer, paid only if a free build fails twice and the maintainer says so), D5 and D61 (the Pro is approved but offline, so the Air syncs), D6 (the five named builds, approved), D9a/b/c, D11 and D62 (short freeze), D17 (hunk counter, day 2), D63 (queue), D64 (two release builds).
- **Answered:** D3 (no 154 build) and D8 (hold the launch if the sync slips).
- **Later, by need:** D7 (before the `arches` input), D10 (day 5), D60 (day 10), D18 (day 19), D58 (after launch).

## Plan-specific reading

`plans/06-engineering-and-shipping.md`, `plans/context/ci-status.md`, `docs/operations/*.md`, `plans/research/digests/helium.md`.

## Streams

| Stream | Worktree | Days | Work |
| --- | --- | --- | --- |
| `ci` | Light (`ci/pipeline`), no build tree | 0-19 | Build queue first. CI fixes, the two release builds, `install-smoke` and `update-smoke`, publishing on the maintainer's word |
| `sync` | `sync/helium-0.20.1.1`, full 156 tree | 0-7, slack to 10 | M2. Tags the 156 base about day 4. Many helper agents, one per patch group |
| `checks` | Light (`ci/checks`) | 0-10 | Linux PR checks, the patch counter, `main` protection, drift detector, network capture, bench, runbook |
| `site` | Light (`site/launch`) | 2-13 | "Moving from Arc" page, comparison pages, public copy fixes (G7 with Core), launch post drafts. Claude models only |

## Machine and worktree

- **The queue first.** `ci` writes `devutils/rac/build-queue.sh` in the first hours of day 0 (06 "Build queue"). Until it lands, use the manual lock in the README.
- **Sync:** on the Air, since the Pro is offline (D61). Branch from `origin/main`: `git worktree add -b sync/helium-0.20.1.1 <path> origin/main`. It doesn't need step 0's 154 tree, because it fetches 156 sources. On the Air, its cold build waits in the queue until step 0's incremental build finishes, then runs alone overnight.
- **CI, site, docs:** light worktrees with no build tree.
- **Releases** compile on free GitHub runners for Apple Silicon only. Signing, notarization, stapling, and appcast signing run in a final job on GitHub's own `macos-latest` runner. The Developer ID certificate, notary key, and Sparkle key never leave GitHub. If D4's trigger fires and the maintainer picks paid Depot, only the compile moves.
- **The 156 base.** Once the sync tree compiles and launches, tag it and announce it to every thread with the exact `worktree.sh setup <sync worktree>` command. Keep that worktree's tree clean: later fixes land as small late-series patch changes. After the merge, fast-forward it to `main` and keep it built, through the queue, as the base for new worktrees.
- **If the sync later moves to the Pro,** once it is online and D5 qualifies, the Air needs its own base: once the 156 base is tagged, create a `base-156` worktree on the Air and run its one cold build overnight (D6 item 4).
- Builds D6 doesn't name need the maintainer's approval. No `he reset` in the main checkout before launch.

## Ship adds to the verification standard

CI run links with timings and peak memory; `install-smoke` and `update-smoke` logs; an update video (0.1.0 to the launch build, 0.2.0); the sync's matrix screenshots; queue logs showing two slots in use and a third request waiting. Use temporary keychains so no dialog appears. The maintainer posts all launch text. Publish or un-publish a release only on the maintainer's word. Ship may touch `.github/` but asks before changing `pullfrog.yml`.

## Coordination

- **You own the short freeze (D62).** Nothing under `patches/` merges until the sync does. Docs, site, CI, and plans may. Announce the 156 base, the sync merge, and the merge order: the harness (UI `tools`), then launch gates (Data, Core, UI `import`), then the rest. Launch merges close at the start of day 13.
- **Release builds.** Tell every thread when a build fires and when it finishes. No thread waits on one.
- Only you edit `.github/`, `dev.sh`, `devutils/shared.sh`, `devutils/rac/worktree.sh`, `devutils/rac/build-queue.sh`, `docs/operations/`, and `site/`. You settle `patches/series` order; others append inside their block.
- After the sync, hand `patches/rac/sidebar-reveal/` to UI `motion` with one constant per timing.

## First steps

Day 0, in parallel:

1. `ci`: write the build queue. Then ask the maintainer to merge PR #20. Harden the checkpoint download in `build-phase.yml` (retry, digest check, clear failure after 3 attempts). Add the `arches` input (default `arm64`) and `fail-fast: false`. Keep signing in a final job on GitHub's `macos-latest`.
2. `ci`: preflight `MAC_TEAM_ID`, entitlements, and notarization, and write `install-smoke`, `update-smoke`, and the runbook (days 1-7). Fire build 1, 0.1.0, from `main` as soon as the sync merges, about day 7. Keep working.
3. `sync`: restore the fetch-only upstream remote if `git remote -v` shows none (`git remote add upstream https://github.com/imputnet/helium-macos && git remote set-url --push upstream no_push`). Merge the tag, fetch the 156 sources, push Helium's patches only, and queue the cold build for tonight.
4. `sync`: split rac's patch rejects among helper agents by patch group, as text fixes against the 156 sources. An Opus agent starts the sidebar-reveal and Layout design merges.
5. `checks`: Linux PR checks (Python tests, `he validate series`, no-fuzz sparse apply, patch-surface counter). Make `sanity-check.sh` fail on fuzz. Ask before touching `pullfrog.yml`.
6. Remind the maintainer: `rac-bot` and protection (day 5), publishing 0.1.0 (about day 9), and the Depot sponsorship ask, later and not on day 0.

## Done means

rac is public on Chromium 156, has updated in place from 0.1.0 (or the proof is queued for the first point release, if build 1 slipped), and `main` is protected. Every launch gate has evidence. The bad-release runbook exists. Each milestone is a PR with proof and a short report.
