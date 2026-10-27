# Thread brief: Data (storage and Arc import)

> **DRAFT: do not launch until the maintainer approves the plans.**

## Goal

An Arc user sees their spaces, pins, favorites, and themes in rac within a minute, with a safety net under it. M0 and M1 are in the launch build by 12-15; sign-ins (M2) too if ready. After launch: the full safety net, the partition spike, the encrypted AI store.

## Owns

Plan 04 M0 (snapshots, restore prompt, Keychain "no silent reset" fix) and M1 (Arc reader, mapping, applier, Undo), M2 if ready, and G2, G3, and the import half of G1. After launch: partitions (in-memory variant first), the AI store schema, export file, more importers.

## Decisions it depends on

- **Before it starts:** D1, D2, D9, D41 (scrub script run by the maintainer, W1), D42 (minimal safety net).
- **By milestone:** D43 and D44 (M2 scope, W4), D45 (password spike; synthetic `Login Data` only), D46 (partitions, after launch), D47 (AI store), D55, D17 (hunk budget).

## Read first

`AGENTS.md`, `VISION.md`, plans 04, 01 (M1), and 06 (M2, M5), `docs/internals/pinned-tabs.md`, `plans/research/cra.md` (MIT, credit it), `plans/research/ardia.md`.

## Machine and worktree

The base Mac, one worktree: `git worktree add -b feat/import-<m> <path> main`, then `devutils/rac/worktree.sh setup`. The reader and fixtures are pure parsing and need only the unit-test target, a light build. Never read real Arc, Dia, Helium, or rac profiles; use the maintainer's scrubbed sample and `--rac-import-source-root` (compiled out of release builds). Real-Arc credential tests use a throwaway profile or second macOS user with test accounts.

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
- Data adds: a rerun adds nothing and Undo restores the sidebar; a net log with zero import requests; corrupt `Preferences` restores in one click; the fake-keychain test writes no second key. Shots: sidebar before and after, restore prompt, two profile windows, incognito unchanged. Videos of the import.

## Hard constraints from AGENTS.md

- Never push to, open PRs against, or file issues on `imputnet` or `ungoogled-software`.
- Never edit `helium-chromium/`, `patches/helium/`, `patches/rebel/`, or `patches/ungoogled-chromium/`.
- `rac_version.txt` only goes up. The signing key and feed URL never change.
- Never take the foreground (no `open`, no `he run`, no foreground automation). Never use a real profile.
- No full build, `he reset`, or deleting `build/` without approval (D6 names the allowed ones). If a worktree build shows tens of thousands of steps, stop.

## Coordination

- During Ship's freeze (W1 to W3) write new files only, on Chromium 154, and do not merge. After the sync merges and the base rebuilds: M0b, M1b, and M2 on 156. `keychain_password_mac.mm` is patched by Helium too, so M0b waits for the sync.
- Agree `import_plan.h` with UI in W1; UI draws the import screens and restore prompt.
- Write only through `SpacesService` and `SidebarItems`. Coordinate with UI on the `rac spaces` store.
- `browser_navigator.cc` and session restore are shared with Core's 05 M2: take turns. Data owns the AI store schema; Core reviews it.
- Code goes in `chrome/browser/rac/storage/` and `chrome/browser/rac/import/`; each PR reports hunks. Never edit Helium's importer files. No network requests; no plaintext password file without sign-off.

## First milestone

M0a and M1a, new files only (W1 to W2, light build):

1. `DataBackups` service in `chrome/browser/rac/storage/`: named pre-import snapshot of `rac.spaces`, `rac.sidebar.lists`, agent rules, and the `rac spaces` file; one rolling daily backup; 0600 via `ImportantFileWriter`.
2. Restore prompt when `Preferences.bad` exists and `rac.spaces` is empty. Never restore silently.
3. `arc_reader` and `import_plan.h`: pure parsing with `base::JSONReader`, Cra's key paths, source-neutral tree.
4. Ask the maintainer to run `devutils/rac/arc_scrub.py` on their own Arc; check the output before committing. Add synthetic edge cases (nested folders, splits, emoji, light and dark themes).
5. Unit tests for all of it.

## Done means

G1 (with UI's screens), G2, and G3 pass. A rerun adds nothing, Undo works, the import makes zero requests, and `he validate series` is green. If M2 slips, launch sidebar-only and follow Ship for a point release.
