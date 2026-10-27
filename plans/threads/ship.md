# Thread brief: Ship (engineering and shipping)

> **DRAFT: do not launch until the maintainer approves the plans.**

## Goal

Get a signed, notarized rac out before Arc shuts down on 2026-12-22: a release chain that finishes, a quiet 0.1.0 on Chromium 154, the sync to Helium 0.20.1.1 / Chromium 156, 0.2.0 proving in-place updates, and the launch candidate started by 12-15.

## Owns

Plan 06 M0 to M5 and launch gates G9 to G14. Also the freeze, `patches/series` order, the base-tree rebuild, cadence syncs, the drift detector, the bench, the host list, launch site pages, and later the beta channel, crash reports, and the plain-folder move (D58).

## Decisions it depends on

- **Before it starts:** D1, D2, D4 (Depot, $300 cap), D5 (which Mac), D6 (named full builds), D9, D11 (freeze and defaults).
- **Later, by need:** D3 (before M1), D7 (before the `arches` input), D17 (W1), D10 (W2 to W5), D8 (end of W4), D18 (W6), D58 (after launch).

## Read first

`AGENTS.md`, `VISION.md`, `plans/06-engineering-and-shipping.md`, `plans/00-master-plan.md`, `plans/context/ci-status.md`, `docs/operations/*.md`, `plans/research/digests/helium.md`.

## Machine and worktree

- **Sync:** the Mac from D5, in `sync/helium-0.20.1.1`: `git worktree add -b sync/helium-0.20.1.1 <path> main`, then `devutils/rac/worktree.sh setup`. Build with `he build`; run with `worktree.sh run`, never `he run`.
- **CI, site, docs:** light worktrees with no build tree (`ci/<name>`, no `setup`).
- **Releases** build on Depot. The timed W1 cold 156 build and the base rebuild with `he reset` are full builds: run them only as D6 names them.

## How to use multi-agent Claude Code workflows inside the thread

Run each milestone through five stages.

1. **Understand.** Read-only subagents (Haiku or Sonnet) read the plan section, the files it touches, and AGENTS.md, and return a short map.
2. **Design.** Opus writes a one-page design (interfaces, hunk budget, test plan) before any code.
3. **Implement.** Hard architecture and security go to Opus. Routine, scoped code and tests go to Sonnet or a strong open-weight model (`kimi-k3`, `glm-5.3`, `deepseek-v4-pro`, `minimax-m3`). UI work goes to Claude Opus (routine UI to Sonnet), never open-weight models.
4. **Verify.** You build, run, and capture. A Haiku subagent may run tests and summarize.
5. **Review.** Before every PR, a fresh Opus reviewer that hasn't seen the design tries to break the diff (attacks, edge cases, missed surfaces, hunk count), then run `/code-review`. Fix or answer every finding. Check subagent output before building on it.

## Verification standard

- Build and run it yourself: `source dev.sh && he build`, then `devutils/rac/worktree.sh run --rac-window-screenshot=/abs/path.png`. Wait for real pixels.
- Answer AGENTS.md "Cover every surface" item by item. Screenshot matrix: sidebar full, hidden, and edge reveal; light and dark; space themes; multiple windows; incognito; split view; an installed web-app (PWA) window; reduced motion; AI off (no AI button, row, or label).
- Short videos for motion. Focused unit tests only. `he validate series` after touching `patches/series`.
- Every PR states its net-diff hunk change (D17) and attaches proof with `gh pr create --attach './shot.png#caption'`. Never commit screenshots or videos.
- No PR unless the maintainer asks, or D9 grants standing permission. The maintainer approves every merge.
- Ship adds: CI run links with timings and peak memory; `install-smoke` and `update-smoke` logs; an update video (0.1.0 to 0.2.0); the sync's matrix screenshots. Use temporary keychains so no dialog appears. The maintainer posts all launch text. Publish or un-publish a release only on the maintainer's word.

## Hard constraints from AGENTS.md

- Never push to, open PRs against, or file issues on `imputnet` or `ungoogled-software`.
- Never edit `helium-chromium/`, `patches/helium/`, `patches/rebel/`, or `patches/ungoogled-chromium/`.
- `rac_version.txt` only goes up. The signing key and feed URL never change.
- Never take the foreground (no `open`, no `he run`, no foreground automation). Never use a real profile.
- No full build, `he reset`, or deleting `build/` without approval (D6 names the allowed ones). If a worktree build shows tens of thousands of steps, stop.

## Coordination

- **You own the freeze.** Nothing under `patches/` merges until the sync does (D11). Docs, site, CI, and plans may. Announce the sync merge and base rebuild so every thread runs `worktree.sh sync` or recreates its worktree.
- Only you edit `.github/`, `dev.sh`, `devutils/shared.sh`, `docs/operations/`, and `site/`. You settle `patches/series` order; others append inside their block.
- After the sync, hand `patches/rac/sidebar-reveal/` to UI with one constant per timing.
- Build slots: tell Core, Data, and UI when a full build starts and ends. The Air allows one full build or two incremental ones, never both.

## First milestone

M0 (W1, about 3 agent-days):

1. Maintainer creates the Depot account on day 1.
2. Merge PR #20. Harden the checkpoint download in `build-phase.yml` (retry, digest check, clear failure after 3 attempts).
3. Add the `arches` input (default `arm64`) and `fail-fast: false`.
4. Point the build at `depot-macos-latest` with Depot Cache; run one free `macos-latest` attempt alongside.
5. Add Linux PR checks: Python tests, `he validate series`, no-fuzz sparse apply, patch-surface counter. Make `sanity-check.sh` fail on fuzz. Delete `pullfrog.yml`.
6. Create the sync worktree and, once D6 allows, start the timed cold 156 build.

## Done means

rac is public on Chromium 156 or later, has updated in place at least once, and `main` is protected. Every launch gate has evidence. The bad-release runbook exists. Each milestone is a PR with proof and a short report.
