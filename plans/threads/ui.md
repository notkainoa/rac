# Thread brief: UI (shell, design, and motion)

> **DRAFT: do not launch until the maintainer approves the plans.**

Follow ["Every thread"](README.md#every-thread) in the README: reading, step 0, streams, the build queue, moving to 156, workflow stages, verification standard, and hard constraints. This brief adds only what is specific to UI.

## Goal

Land the Arc import screens for the launch build (merged by day 13), then make rac feel like one calm product: the command bar, Peek and the little window, Clear with Undo, and a shared token and spring system. Seven streams run at once, each in its own worktree. What misses day 13 ships in the first point release, about day 26.

## Owns

Plan 01 M0 to M4 and M6, M5 jointly with Core; plan 02 M0 to M5. G1's screens (01 M1), G8's PWA check, and the harness in `patches/rac/dev/`. It draws screens for others: import and restore (Data); Settings > Outside agents, pairing, sharing, and the Agents section (Core).

## Decisions it depends on

- **Group A:** D1, D2, D5, D9a/b/c, D14 (a "no" cancels the Peek spike), D16 (command bar timing), D22 (Views), D62, D63.
- **By day:** D13 (day 2), D28 to D31 (day 0, for 01 M2), D23 (day 3, agent rows), D32 to D37 (day 3, 02 M2), D38 (day 5, little window), D15 and D39 (day 10), D40 (day 7, 02 M4), D12a/b (door wording, day 14).

## Plan-specific reading

Plans 01, 02, and 00, `docs/internals/` (glossary, pinned-tabs, ai), `plans/research/digests/motion-and-feel.md`.

## Streams

All are Claude models only: Opus for the hard or visible parts, Sonnet for routine UI.

| Stream | Branch | Days | Work | Main files |
| --- | --- | --- | --- | --- |
| `tools` | `feat/ui-tools` | 0-5 | 02 M0 frame log, frames-to-video, `motion_trace.py`, forced Reduce Motion and Increase Contrast. 01 M0 harness verbs: named secondary window, space theme and mode, second profile window, incognito, `open-urls`. PWA check on today's build. Baseline videos of Cmd+S and edge reveal | `patches/rac/dev/`, `devutils/rac/` |
| `import` | `feat/ui-import` | 1-12 | 01 M1 import screens, the result screen, the restore prompt screen, PWA fixes. Launch gate | Onboarding and settings files |
| `bar` | `feat/ui-bar` | 0-16 | 01 M2. Panel, rows, ranking, and merge on 154 first; hooks on the 156 base from day 4 | `chrome/browser/ui/views/rac/command_bar/` |
| `peek` | `feat/ui-peek` | 0-24 | Peek and little window spike (days 0-3, only if D14 is yes), then 01 M3's build on 156. Agent-row design for Core by day 3 | New Peek and little-window files; `app_controller_mac.mm` hook |
| `clear` | `feat/ui-clear` | 0-12 | Clear and Undo spike (day 0), then Clear with MayClear and Undo through recently-closed restore | Sidebar Clear files |
| `design` | `feat/ui-design` | 0-12 | 02 M1 tokens and springs (fix token names by day 1), then 02 M2 polish and 02 M3 space colors | `rac_tokens.h`, `motion/`, `rac_tokens.css`, spaces theme files |
| `motion` | `feat/ui-motion` | 7-20 | 02 M4 and 01 M4 on 156, after Ship hands over `sidebar-reveal` at the sync merge | `sidebar-reveal`, `ui_features.cc` hook, tab animation hooks |

## Machine and worktree

- The Air, through the queue. Each stream starts as a light worktree and runs `devutils/rac/worktree.sh setup` when its first batch is ready to build.
- `bar`, `peek`, and `motion` write their hooks into Helium-shared files only on the 156 base (README, "Moving to Chromium 156").
- Run with `worktree.sh run` or the harness only. Force Reduce Motion and Increase Contrast with dev flags. Run `dev_names.py unsub` before editing string files.
- `tools` adds the harness verb `open-urls URL`, which calls `application:openURLs:` inside the worktree process. Plan 01 M3's link-routing checks use it, never `open URL` from a terminal.
- Until `tools` merges after the sync, other streams may apply its dev patches locally for their own checks, but never merge them.

## UI adds to the verification standard

Before and after shots; per changed interaction, videos at real time and 4x, a `motion_trace.py` report within one frame of the token, a frame log, and idle frames at 0 with AI off and on; Reduce Motion and Increase Contrast captures; both address-bar layouts; one Tier 1 run on the 156 base per milestone. Use the queue's run slots for harness sessions.

## Coordination

- Fix interfaces on days 0 and 1: token names (`design`), the action table schema (Core `table`), `import_plan.h` (Data `reader`), agent-row design (`peek`, by day 3).
- File owners inside UI: `design` owns tokens and `motion/`; `motion` owns `sidebar-reveal` after the handover; `bar` owns command ids it adds; `import` owns onboarding. `design`'s polish touches other groups' buttons only after asking that group's stream, and rebases last.
- Shared with other threads: `rac_strings.grdp` (each stream appends in its own block), onboarding (Data), site control center and command ids (Core, Power), `ui_features.cc`, settings pages. Ask the owner or wait.
- Nothing under `patches/` merges before the sync. In Ship's merge order, `tools` goes first, then `import`, then the rest. Launch merges close at the start of day 13.
- Core's 03 M1 table lands before command bar rows that read it. Until then, `bar` uses a small local list behind the same interface. Power builds on your router (01 M3).

## First steps

Day 0, in parallel, one lead per stream:

1. `tools`: frame log and forced flags, compiled out of release builds; then the harness verbs; then the PWA check and baseline recordings on today's build. Report each result.
2. `design`: publish the token names by day 1. Write `rac::Spring` and its unit tests.
3. `bar`: the panel, rows, and merge as rac-owned code, no hooks.
4. `peek`: the Peek and little window spike (if D14 is yes). `clear`: the half-day Clear and Undo spike, then the build.
5. `import`: agree `import_plan.h` with Data on day 1, then draw screens 1 and 2 and the result screen.

## Done means

Import screens are in the launch build with plan 04's fixtures matching (G1), and AI-off is clean on every screen. Each PR has shots, videos for motion, unit tests, the surface list answered, and the "I tested" block. The command bar and Clear ship in the launch if merged by day 13, else in the first point release (D16).
