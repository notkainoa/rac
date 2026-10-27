# Thread brief: UI (shell, design, and motion)

> **DRAFT: do not launch until the maintainer approves the plans.**

## Goal

Land the Arc import screens for the launch build, then make rac feel like one calm product: the command bar, Peek and the little window, Clear with Undo, and a shared token and spring system. Build in rac-owned files on Chromium 154 now, rebase onto 156 after the sync.

## Owns

Plan 01 M0 to M4 and M6, M5 jointly with Core; plan 02 M0 to M5. G1's screens (01 M1), G8's PWA check, and the harness in `patches/rac/dev/`. It draws screens for others: import and restore (Data); Settings > Outside agents, pairing, sharing, and the Agents section (Core).

## Decisions it depends on

- **Before it starts:** D1, D2, D5, D9, D14 (a "no" cancels the Peek spike), D22 (Views), D16 (command bar timing).
- **By milestone:** D13 and D28 to D31 (01 M2, W1), D23 (agent rows, W2), D32 to D37 (02 M2, W2), D33 (02 M3), D15, D38 and D39 (01 M3), D40 (02 M4), D12 (door wording).

## Read first

`AGENTS.md`, `VISION.md`, plans 01, 02, and 00, `docs/internals/` (glossary, pinned-tabs, ai), `plans/research/digests/motion-and-feel.md`.

## Machine and worktree

The base Mac. At most two worktrees at once: `git worktree add -b feat/ui-<m> <path> main` and `feat/motion-<m>`, each followed by `devutils/rac/worktree.sh setup`. Plan 01's and plan 02's harness work go in one worktree, in turn. Use `worktree.sh run`, never `he run`. Force Reduce Motion and Increase Contrast with dev flags. Run `dev_names.py unsub` before editing string files.

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
- UI adds: before and after shots; per changed interaction, videos at real time and 4x, a `motion_trace.py` report within one frame of the token, a frame log, and idle frames at 0 with AI off and on; Reduce Motion and Increase Contrast captures; both address-bar layouts; a Tier 1 run on the synced build per milestone.

## Hard constraints from AGENTS.md

- Never push to, open PRs against, or file issues on `imputnet` or `ungoogled-software`.
- Never edit `helium-chromium/`, `patches/helium/`, `patches/rebel/`, or `patches/ungoogled-chromium/`.
- `rac_version.txt` only goes up. The signing key and feed URL never change.
- Never take the foreground (no `open`, no `he run`, no foreground automation). Never use a real profile.
- No full build, `he reset`, or deleting `build/` without approval (D6 names the allowed ones). If a worktree build shows tens of thousands of steps, stop.

## Coordination

- Fix interfaces in W1 and W2: token names (02), the action table schema (Core), `import_plan.h` (Data), agent-row design (you).
- Shared files: `rac_strings.grdp`, onboarding (Data), site control center and command ids (Core, Power), `ui_features.cc`, settings pages. Ask the owner or wait.
- Land nothing under `patches/` during Ship's freeze. Hooks into hot files wait for the sync and base rebuild. Launch merges close at the start of W5.
- Take `sidebar-reveal` from Ship after the sync. Core's 03 M1 table lands before command bar rows; Power builds on your router (01 M3).
- Build slots: 01 M0 PWA check and 01 M1 first, then 01 M2, then 02 M1 to M3.

## First milestone

M0 (W1 to W2, Chromium 154, dev and rac-owned files only), in one worktree, in turn:

1. Plan 02 M0: the frame log, the frames-to-video tool, `motion_trace.py`, and the forced Reduce Motion and Increase Contrast flags, compiled out of release builds.
2. Plan 01 M0: harness verbs for a named secondary window, a space's theme and mode, a second profile window, and incognito.
3. Record Cmd+S and edge reveal to confirm or retire the snap inference.
4. Check installed web-app windows on today's build; file fixes.
5. Spikes: Peek and the little window (2 to 3 days, only if D14 is yes), Clear and Undo (half a day).
6. Start the command bar's panel, rows, and merge as rac-owned code, no hooks.

Report each result before feature work.

## Done means

Import screens are in the launch build with plan 04's fixtures matching (G1), and AI-off is clean on every screen. Each PR has shots, videos for motion, unit tests, the surface list answered, and the "I tested" block. The command bar ships by W5 if merged, else as a point release (D16).
