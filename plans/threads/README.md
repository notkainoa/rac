# Thread briefs

Draft briefs for the five build threads in the [master plan's thread map](../00-master-plan.md#thread-map). Every brief is marked DRAFT and must not launch until the maintainer approves the plans and answers group A of [decisions.md](../decisions.md): D1, D2, D4, D5, D6, D9a/b/c, D11, D14, D16, D17, D19 to D22, D41, D42.

| Thread | Owns | Starts when | Needs from group A | Machine |
| --- | --- | --- | --- | --- |
| [Ship](ship.md) | Plan 06 M0 to M5, the sync, the freeze, launch gates G9 to G14, later the beta channel and plain-folder move | W1, right after approval (Depot signup on day 1) | D1, D2, D4, D5, D6, D9a/b/c, D11, D17 | The Mac from D5 for the sync (`sync/helium-0.20.1.1`); Depot compiles releases; light worktrees for CI and site |
| [UI](ui.md) | Plan 01 M0 to M4 and M6 (M5 with Core), plan 02 M0 to M5, the harness | W1 | D1, D2, D5, D9a/b/c, D14, D16, D22 | The base Mac, at most two worktrees |
| [Core](core.md) | Plan 05 M0 (launch gate), plan 03 M0 and M1; after launch the door, warm agent, 05 M2 and M3, thinning | W1 | D1, D2, D9a/b/c, D17, D19 to D22 | The base Mac, one worktree at a time |
| [Data](data.md) | Plan 04 M0, M1, and M2 if ready; after launch partitions and the AI store | W1 (new files only during the freeze) | D1, D2, D9a/b, D17, D41, D42 | The base Mac, one worktree (light unit-test build) |
| [Power](power.md) | Plan 07 M0 to M5 | After launch (W7 on), once Core's table and UI's router land | D9a/b/c | Whichever Mac has a free slot |

Decisions outside group A are listed in each brief with the week they are needed.

**How launching works.** The maintainer approves the plans, answers group A, and does step 0 below. Then each thread is a T3 Code thread in its own worktree, started from its brief plus the master plan's thread map. Ship, UI, Core, and Data start at W1. Power starts after launch. The maintainer approves every merge.

# Every thread

Each brief says "Follow 'Every thread' in the README" and adds only what is specific to that thread.

## Read first

`AGENTS.md`, `VISION.md`, [`plans/rulings.md`](../rulings.md) (the rulings the plans cite), and the master plan's thread map. Anything borrowed from Cra is read from a fresh clone of `github.com/VictorKildahl/cra` at commit `94c3034`, in a scratch folder, read only.

## Step 0: start from an up-to-date main

Worktrees must branch from an up-to-date `main`. The main checkout at `/Users/knewton/Dev/Github/rac` has a local `main` 71 commits behind `origin/main`, and its `build/src` was built from that. Before any thread starts, the maintainer fast-forwards it (`git -C /Users/knewton/Dev/Github/rac pull --ff-only`, after dealing with its uncommitted `.gitignore` change) and approves one incremental `source dev.sh && he build` there, so every worktree clones a base that matches `main`. Threads never do this themselves. If `git log origin/main..main` or `git merge-base --is-ancestor origin/main main` says `main` is behind, stop and tell the maintainer.

After the sync merges, worktrees may clone the sync worktree's built 156 tree with `devutils/rac/worktree.sh setup <checkout>` instead of waiting for a base rebuild. This needs the maintainer's OK (D6).

## Workflow: five stages per milestone

1. **Understand.** Read-only subagents (Haiku or Sonnet) read the plan section, the files it touches, and AGENTS.md, and return a short map.
2. **Design.** Opus writes a one-page design (interfaces, hunk budget, test plan) before any code.
3. **Implement.** Hard architecture and security go to Opus. Routine, scoped code and tests go to Sonnet or a strong open-weight model (`kimi-k3`, `glm-5.3`, `deepseek-v4-pro`, `minimax-m3`). UI work goes to Claude Opus (routine UI to Sonnet), never open-weight models.
4. **Verify.** You build, run, and capture. A Haiku subagent may run tests and summarize.
5. **Review.** Before every PR, a fresh Opus reviewer that hasn't seen the design tries to break the diff (attacks, edge cases, missed surfaces, hunk count), then run `/code-review`. Fix or answer every finding. Check subagent output before building on it.

## Verification standard

- Build and run it yourself: `source dev.sh && he build`, then `devutils/rac/worktree.sh run --rac-window-screenshot=/abs/path.png`. Wait for real pixels.
- Answer AGENTS.md "Cover every surface" item by item. Screenshot matrix: sidebar full, hidden, and edge reveal; light and dark; space themes; multiple windows; incognito; split view; an installed web-app (PWA) window; reduced motion; AI off (no AI button, row, or label).
- When a feature or fix in a worktree is done, post the proof in the thread's chat, not only in the PR. Show before and after screenshots of every changed surface, embedded as markdown images with absolute paths. If the change has an animation or an interaction (a click, a drag, a shortcut, a flow), also record a short video of it and embed or link it in the chat. The maintainer asked for this on 2026-10-27.
- Short videos for motion. Focused unit tests only. `he validate series` after touching `patches/series`.
- Every PR states its net-diff hunk change (D17) and attaches proof with `gh pr create --attach './shot.png#caption'`. Never commit screenshots or videos.
- PRs are opened only as D9b allows (otherwise only when asked). The maintainer approves every merge.

## Hard constraints

- Never push to, open PRs against, or file issues on `imputnet` or `ungoogled-software`.
- Never edit `helium-chromium/`, `patches/helium/`, `patches/rebel/`, or `patches/ungoogled-chromium/`.
- `rac_version.txt` only goes up. The signing key and feed URL never change.
- **Profiles.** Never launch a rac build without `--user-data-dir`. Always use `devutils/rac/worktree.sh run` or the harness, which pass it. Never use a real profile. Never run `he run` in a worktree, and never `open` rac.app.
- **Default browser.** No step changes the default browser. Link-routing checks use a harness verb (`open-urls URL`, which calls the same `application:openURLs:` router inside the worktree process).
- **Keychain.** No step unlocks the real "Arc Safe Storage" Keychain item. Arc import tests use fixture `Cookies` databases encrypted with a fixed test password, through a test-only seam that never calls the real Keychain.
- **By hand.** Real-Arc and default-browser checks are done by the maintainer, by hand, on a second macOS user.
- Never take the foreground (no foreground automation, no system dialogs).
- No full build, `he reset`, or deleting `build/` without approval (D6 names the allowed ones). If a worktree build shows tens of thousands of steps, stop.
