# Thread brief: Data (storage and Arc import)

> **DRAFT: do not launch until the maintainer approves the plans.**

Follow ["Every thread"](README.md#every-thread) in the README: reading, step 0, workflow stages, verification standard, and hard constraints. This brief adds only what is specific to Data.

## Goal

An Arc user sees their spaces, pins, favorites, and themes in rac within a minute, with a safety net under it. M0 and M1 are in the launch build by 12-15; sign-ins (M2) too if ready. After launch: the full safety net, the partition spike, the encrypted AI store.

## Owns

Plan 04 M0 (snapshots, restore prompt, Keychain "no silent reset" fix) and M1 (Arc reader, mapping, applier, Undo), M2 if ready, and G2, G3, and the import half of G1. After launch: partitions (in-memory variant first), the AI store schema, export file, more importers.

## Decisions it depends on

- **Group A:** D1, D2, D9a/b, D17 (hunk budget), D41 (scrub script run by the maintainer, W1), D42 (minimal safety net).
- **By milestone:** D43 and D44 (M2 scope, W4), D45 (password spike; synthetic `Login Data` only), D46 (partitions, after launch), D47 (AI store), D55.

## Plan-specific reading

Plans 04, 01 (M1), and 06 (M2, M5), `docs/internals/pinned-tabs.md`, `plans/research/cra.md` (MIT, credit it), `plans/research/ardia.md`. For Cra's key paths, clone `github.com/VictorKildahl/cra` at commit `94c3034` into a scratch folder and read only `Sources/Cra/Services/Import/`.

## Machine and worktree

0. Step 0 in the README first: the main checkout is pulled and its base build approved by the maintainer.
- The base Mac, one worktree: `git worktree add -b feat/import-<m> <path> main`, then `devutils/rac/worktree.sh setup`. After the sync, `worktree.sh setup <checkout>` may clone the sync worktree's 156 tree if the maintainer OKs it (D6).
- The reader and fixtures are pure parsing and need only the unit-test target, a light build.
- Never read real Arc, Dia, Helium, or rac profiles; use the maintainer's scrubbed sample and `--rac-import-source-root` (compiled out of release builds).
- **Arc credentials.** Test the credential reader only on fixture `Cookies` databases encrypted with a fixed test password, through a test-only seam. The reader never calls the real Keychain in tests, and nothing unlocks the real "Arc Safe Storage" item. Real-Arc checks are the maintainer's, by hand, on a second macOS user.

## Data adds to the verification standard

A rerun adds nothing and Undo restores the sidebar; a net log with zero import requests; corrupt `Preferences` restores in one click; the fake-keychain test writes no second key. Shots: sidebar before and after, restore prompt, two profile windows, incognito unchanged. Videos of the import.

## Coordination

- During Ship's freeze (W1 to W3) write new files only, on Chromium 154, and do not merge. After the sync merges and the base rebuilds (or is cloned): M0b, M1b, and M2 on 156. `keychain_password_mac.mm` is patched by Helium too, so M0b waits for the sync.
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
