# Thread brief: UI (shell, design, and motion)

> **DRAFT: do not launch until the maintainer approves the plans.**

Follow ["Every thread"](README.md#every-thread) in the README: reading, step 0, workflow stages, verification standard, and hard constraints. This brief adds only what is specific to UI.

## Goal

Land the Arc import screens for the launch build, then make rac feel like one calm product: the command bar, Peek and the little window, Clear with Undo, and a shared token and spring system. Build in rac-owned files on Chromium 154 now, rebase onto 156 after the sync.

## Owns

Plan 01 M0 to M4 and M6, M5 jointly with Core; plan 02 M0 to M5. G1's screens (01 M1), G8's PWA check, and the harness in `patches/rac/dev/`. It draws screens for others: import and restore (Data); Settings > Outside agents, pairing, sharing, and the Agents section (Core).

## Decisions it depends on

- **Group A:** D1, D2, D5, D9a/b/c, D14 (a "no" cancels the Peek spike), D16 (command bar timing), D22 (Views).
- **By milestone:** D13 and D28 to D31 (01 M2, W1), D23 (agent rows, W2), D32 to D37 (02 M2, W2), D33 (02 M3), D15, D38 and D39 (01 M3), D40 (02 M4), D12a/b (door wording).

## Plan-specific reading

Plans 01, 02, and 00, `docs/internals/` (glossary, pinned-tabs, ai), `plans/research/digests/motion-and-feel.md`.

## Machine and worktree

0. Step 0 in the README first: the main checkout is pulled and its base build approved by the maintainer.
- The base Mac. At most two worktrees at once: `git worktree add -b feat/ui-<m> <path> main` and `feat/motion-<m>`, each followed by `devutils/rac/worktree.sh setup`. Plan 01's and plan 02's harness work go in one worktree, in turn.
- Run with `worktree.sh run` or the harness only. Force Reduce Motion and Increase Contrast with dev flags. Run `dev_names.py unsub` before editing string files.
- After the sync, worktrees may clone the sync worktree's 156 tree with `worktree.sh setup <checkout>` if the maintainer OKs it (D6).
- Add a harness verb `open-urls URL` that calls `application:openURLs:` inside the worktree process. Plan 01 M3's link-routing checks use it, never `open URL` from a terminal.

## UI adds to the verification standard

Before and after shots; per changed interaction, videos at real time and 4x, a `motion_trace.py` report within one frame of the token, a frame log, and idle frames at 0 with AI off and on; Reduce Motion and Increase Contrast captures; both address-bar layouts; a Tier 1 run on the synced build per milestone.

## Coordination

- Fix interfaces in W1 and W2: token names (02), the action table schema (Core), `import_plan.h` (Data), agent-row design (you).
- Shared files: `rac_strings.grdp`, onboarding (Data), site control center and command ids (Core, Power), `ui_features.cc`, settings pages. Ask the owner or wait.
- Land nothing under `patches/` during Ship's freeze. Hooks into hot files wait for the sync and base rebuild. Launch merges close at the start of W5.
- Take `sidebar-reveal` from Ship after the sync. Core's 03 M1 table lands before command bar rows; Power builds on your router (01 M3).
- Build slots: 01 M0 PWA check and 01 M1 first, then 01 M2, then 02 M1 to M3.

## First milestone

M0 (W1 to W2, Chromium 154, dev and rac-owned files only), in one worktree, in turn:

1. Plan 02 M0: the frame log, the frames-to-video tool, `motion_trace.py`, and the forced Reduce Motion and Increase Contrast flags, compiled out of release builds.
2. Plan 01 M0: harness verbs for a named secondary window, a space's theme and mode, a second profile window, incognito, and `open-urls`.
3. Record Cmd+S and edge reveal to confirm or retire the snap inference.
4. Check installed web-app windows on today's build; file fixes.
5. Spikes: Peek and the little window (2 to 3 days, only if D14 is yes), Clear and Undo (half a day).
6. Start the command bar's panel, rows, and merge as rac-owned code, no hooks.

Report each result before feature work.

## Done means

Import screens are in the launch build with plan 04's fixtures matching (G1), and AI-off is clean on every screen. Each PR has shots, videos for motion, unit tests, the surface list answered, and the "I tested" block. The command bar ships by W5 if merged, else as a point release (D16).
