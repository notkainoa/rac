# Thread brief: Data (storage and Arc import)

> **DRAFT: do not launch until the maintainer approves the plans.**

Follow ["Every thread"](README.md#every-thread) in the README: reading, step 0, streams, the build queue, moving to 156, workflow stages, verification standard, and hard constraints. This brief adds only what is specific to Data.

## Goal

An Arc user sees their spaces, pins, favorites, and themes in rac within a minute, with a safety net under it. M0 and M1 merge by day 13 for the launch build; sign-ins (M2) too if ready, otherwise the first point release, about day 26. After launch: the full safety net, the partition spike, the encrypted AI store.

## Owns

Plan 04 M0 (snapshots, restore prompt, Keychain "no silent reset" fix) and M1 (Arc reader, mapping, applier, Undo), M2 if ready, and G2, G3, and the import half of G1. After launch: partitions (in-memory variant first), the AI store schema, export file, more importers.

## Decisions it depends on

- **Group A:** D1, D2, D9a/b, D17 (hunk budget), D41 (scrub script run by the maintainer, day 0), D42 (minimal safety net), D62, D63.
- **By day:** D43 and D44 (day 8, whether sign-ins chase the launch), D45 (password spike, day 1; synthetic `Login Data` only), D46 (partitions, day 14), D47 (AI store, day 20), D55.

## Plan-specific reading

Plans 04, 01 (M1), and 06 (M2, M5), `docs/internals/pinned-tabs.md`, `plans/research/cra.md` (MIT, credit it), `plans/research/ardia.md`. For Cra's key paths, clone `github.com/VictorKildahl/cra` at commit `94c3034` into a scratch folder and read only `Sources/Cra/Services/Import/`.

## Streams

| Stream | Branch | Days | Work | Main files |
| --- | --- | --- | --- | --- |
| `net` | `feat/import-net` | 0-8 | M0a `DataBackups` and the restore prompt on 154 (days 0-6). Then M0b, the Keychain fix, on the 156 base (days 4-8, Opus) | `chrome/browser/rac/storage/`; `keychain_password_mac.mm` hook |
| `reader` | `feat/import-reader` | 0-5 | M1a `arc_reader`, `import_plan.h` (agreed with UI by day 1), the scrubbed sample, synthetic fixtures, unit tests | `chrome/browser/rac/import/arc_reader.*`, `import_plan.h`, fixtures |
| `apply` | `feat/import-apply` | 3-11 | M1b mapping (rac-owned, from day 3), then the applier, idempotence record, Undo, and hooks on the 156 base | `chrome/browser/rac/import/` mapping and applier files |
| `signins` | `feat/import-signins` | 0-14 | M2. Credential reader on fixture `Cookies` databases (days 0-6), the one-day password RAM-disk spike (day 1), then profiles and the cookie writer | `credential_reader_mac.mm`, cookie writer, profile creation |

`reader` and `apply` share a folder but not files. `apply` reads `import_plan.h` and never edits it; changes go through `reader`.

## Machine and worktree

- The Air, through the queue. Start as light worktrees. The reader and fixtures are pure parsing and need only the unit-test target, a light build.
- `net`'s Keychain fix, `apply`'s hooks, and `signins`' profile creation are written only on the 156 base (README, "Moving to Chromium 156"). `keychain_password_mac.mm` is patched by Helium too.
- Never read real Arc, Dia, Helium, or rac profiles; use the maintainer's scrubbed sample and `--rac-import-source-root` (compiled out of release builds).
- **Arc credentials.** Test the credential reader only on fixture `Cookies` databases encrypted with a fixed test password, through a test-only seam. The reader never calls the real Keychain in tests, and nothing unlocks the real "Arc Safe Storage" item. Real-Arc checks are the maintainer's, by hand, on a second macOS user, about day 12.

## Data adds to the verification standard

A rerun adds nothing and Undo restores the sidebar; a net log with zero import requests; corrupt `Preferences` restores in one click; the fake-keychain test writes no second key. Shots: sidebar before and after, restore prompt, two profile windows, incognito unchanged. Videos of the import.

## Coordination

- Nothing under `patches/` merges before the sync. In Ship's merge order, `net`, `reader`, and `apply` are launch gates. `signins` merges by day 13 only if the maintainer's by-hand check is done.
- Agree `import_plan.h` with UI `import` on day 1; UI draws the import screens and the restore prompt.
- Write only through `SpacesService` and `SidebarItems`. Coordinate with UI on the `rac spaces` store.
- `browser_navigator.cc` and session restore are shared with Core's 05 M2: take turns. Data owns the AI store schema; Core reviews it.
- Code goes in `chrome/browser/rac/storage/` and `chrome/browser/rac/import/`; each PR reports hunks. Never edit Helium's importer files. No network requests; no plaintext password file without sign-off.

## First steps

Day 0, in parallel:

1. Ask the maintainer to run `devutils/rac/arc_scrub.py` on their own Arc; check the output before committing. `reader` adds synthetic edge cases (nested folders, splits, emoji, light and dark themes).
2. `reader`: `arc_reader` and `import_plan.h`: pure parsing with `base::JSONReader`, Cra's key paths, a source-neutral tree. Unit tests for all of it.
3. `net`: the `DataBackups` service in `chrome/browser/rac/storage/`: a named pre-import snapshot of `rac.spaces`, `rac.sidebar.lists`, agent rules, and the `rac spaces` file; one rolling daily backup; 0600 via `ImportantFileWriter`. Then the restore prompt when `Preferences.bad` exists and `rac.spaces` is empty. Never restore silently.
4. `signins`: the cookie decryption on fixtures, and the password spike plan on synthetic `Login Data`.
5. `apply` starts on day 3, from the agreed `import_plan.h`.

## Done means

G1 (with UI's screens), G2, and G3 pass. A rerun adds nothing, Undo works, the import makes zero requests, and `he validate series` is green. If M2 misses day 13, launch sidebar-only and ship sign-ins in the first point release.
