# Thread brief: Ship (engineering and shipping)

> **DRAFT: do not launch until the maintainer approves the plans.**

Follow ["Every thread"](README.md#every-thread) in the README: reading, step 0, workflow stages, verification standard, and hard constraints. This brief adds only what is specific to Ship.

## Goal

Get a signed, notarized rac out before Arc shuts down on 2026-12-22: a release chain that finishes, a quiet 0.1.0 on Chromium 154, the sync to Helium 0.20.1.1 / Chromium 156, 0.2.0 proving in-place updates, and the launch candidate started by 12-15.

## Owns

Plan 06 M0 to M5 and launch gates G9 to G14. Also the freeze, `patches/series` order, the base-tree rebuild, cadence syncs, the drift detector, the bench, the host list, launch site pages, and later the beta channel, crash reports, and the plain-folder move (D58).

## Decisions it depends on

- **Group A:** D1, D2, D4 (Depot compiles, $300 cap), D5 (which Mac), D6 (named full builds, and cloning the sync worktree's tree), D9a/b/c, D11 (freeze and defaults), D17 (hunk counter, W1).
- **Later, by need:** D3 (before M1), D7 (before the `arches` input), D10 (W2 to W5), D8 (end of W4), D18 (W6), D58 (after launch).

## Plan-specific reading

`plans/06-engineering-and-shipping.md`, `plans/context/ci-status.md`, `docs/operations/*.md`, `plans/research/digests/helium.md`.

## Machine and worktree

0. Step 0 in the README first: the main checkout is pulled and its base build approved by the maintainer. Don't create the sync worktree before that.
- **Sync:** the Mac from D5, in `sync/helium-0.20.1.1`: `git worktree add -b sync/helium-0.20.1.1 <path> main`, then `devutils/rac/worktree.sh setup`. Build with `he build`; run with `worktree.sh run`.
- **CI, site, docs:** light worktrees with no build tree (`ci/<name>`, no `setup`).
- **Releases** compile on Depot. Signing, notarization, stapling, and appcast signing run in a final job on GitHub's own `macos-latest` runner. The Developer ID certificate, notary key, and Sparkle key never go to Depot.
- The timed W1 cold 156 build and the base rebuild with `he reset` are full builds: run them only as D6 names them.
- **Faster than a base rebuild:** in W3, on a throwaway worktree, check that `worktree.sh setup <sync worktree>` works from the built 156 tree. If it does and the maintainer OKs it (D6), new and rebased worktrees use it, and the main checkout's rebuild moves to a quiet night or waits for the next sync.

## Ship adds to the verification standard

CI run links with timings and peak memory; `install-smoke` and `update-smoke` logs; an update video (0.1.0 to 0.2.0); the sync's matrix screenshots. Use temporary keychains so no dialog appears. The maintainer posts all launch text. Publish or un-publish a release only on the maintainer's word. Ship may touch `.github/` but asks before changing `pullfrog.yml`.

## Coordination

- **You own the freeze.** Nothing under `patches/` merges until the sync does (D11). Docs, site, CI, and plans may. Announce the sync merge and the base rebuild (or the clone option) so every thread runs `worktree.sh sync` or recreates its worktree.
- Only you edit `.github/`, `dev.sh`, `devutils/shared.sh`, `docs/operations/`, and `site/`. You settle `patches/series` order; others append inside their block.
- After the sync, hand `patches/rac/sidebar-reveal/` to UI with one constant per timing.
- Build slots: tell Core, Data, and UI when a full build starts and ends. The Air allows one full build or two incremental ones, never both.

## First milestone

M0 (W1, about 3 agent-days):

1. Maintainer creates the Depot account on day 1.
2. Ask the maintainer to merge PR #20. Harden the checkpoint download in `build-phase.yml` (retry, digest check, clear failure after 3 attempts).
3. Add the `arches` input (default `arm64`) and `fail-fast: false`.
4. Point the compile at `depot-macos-latest` with Depot Cache; run one free `macos-latest` attempt alongside. Put signing, notarization, stapling, and appcast signing in a final job on GitHub's `macos-latest`, so the secrets never reach Depot.
5. Add Linux PR checks: Python tests, `he validate series`, no-fuzz sparse apply, patch-surface counter. Make `sanity-check.sh` fail on fuzz. Ask before touching `pullfrog.yml`.
6. Restore the fetch-only upstream remote if `git remote -v` shows none: `git remote add upstream https://github.com/imputnet/helium-macos && git remote set-url --push upstream no_push`.
7. Create the sync worktree and, once D6 allows, start the timed cold 156 build.

## Done means

rac is public on Chromium 156 or later, has updated in place at least once, and `main` is protected. Every launch gate has evidence. The bad-release runbook exists. Each milestone is a PR with proof and a short report.
