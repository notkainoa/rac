# Thread briefs

Draft briefs for the five build threads in the [master plan's thread map](../00-master-plan.md#thread-map). Every brief is marked DRAFT and must not launch until the maintainer approves the plans and answers group A of [decisions.md](../decisions.md): D1, D2, D4, D5, D6, D9a/b/c, D11, D14, D16, D17, D19 to D22, D41, D42, and D61 to D64.

Days count from approval, assumed on Wed 2026-10-28 (day 0). The target launch is day 19.

| Thread | Owns | Streams | Starts | Machine |
| --- | --- | --- | --- | --- |
| [Ship](ship.md) | Plan 06 M0 to M5, the sync, the build queue, the merge order, launch gates G9 to G14, later the beta channel and plain-folder move | `ci`, `sync`, `checks`, `site` | Day 0 | The sync on the Air (the Pro, D61, is approved but offline). Free GitHub runners compile releases. Light worktrees for CI and site |
| [UI](ui.md) | Plan 01 M0 to M4 and M6 (M5 with Core), plan 02 M0 to M5, the harness | `tools`, `import`, `bar`, `peek`, `clear`, `design`, `motion` (day 7) | Day 0 | The Air, through the queue |
| [Core](core.md) | Plan 05 M0 (launch gate), plan 03 M0 and M1; after launch the door, warm agent, 05 M2 and M3, thinning | `guard`, `evals`, `doors` (day 4), `table` | Day 0 | The Air, through the queue; `doors` on the 156 base |
| [Data](data.md) | Plan 04 M0, M1, and M2 if ready; after launch partitions and the AI store | `net`, `reader`, `apply` (day 3), `signins` | Day 0 | The Air, through the queue; light unit-test builds |
| [Power](power.md) | Plan 07 M0 to M5 | `logic` | Day 0, code from day 1, pure logic only | The Air, unit-test builds only before launch |

Decisions outside group A are listed in each brief with the day they are needed.

**How launching works.** The maintainer approves the plans, answers group A, and has started step 0 below. Then each thread is a T3 Code thread, started from its brief plus the master plan. A thread's lead opens one worktree per stream and runs each stream with Claude Code subagents (the Agent tool), working in that stream's worktree. Leads never create new threads: no `delegate_task`, `t3_thread_launch`, or `create_threads`. Devin SWE-2, OpenCode, and Cursor models are called from the shell, not as threads. The planning thread is the main thread over all five leads. The maintainer asked for this on 2026-10-27. All five threads start on day 0. The maintainer approves every merge.

# Every thread

Each brief says "Follow 'Every thread' in the README" and adds only what is specific to that thread.

## Read first

`AGENTS.md`, `VISION.md`, [`plans/rulings.md`](../rulings.md) (the rulings the plans cite), and the master plan. Anything borrowed from Cra is read from a fresh clone of `github.com/VictorKildahl/cra` at commit `94c3034`, in a scratch folder, read only.

## Step 0: start from an up-to-date main

The main checkout at `/Users/knewton/Dev/Github/rac` was pulled to d3f0d66 and synced (547 patches applied). Its build tree is **not usable for cheap builds**. Xcode is now 27.1, so `he build` there wanted a full rebuild (84,903 steps). It was stopped after about five minutes, which dirtied most of its `out/Default`. Threads never touch the main checkout.

Until the maintainer decides otherwise, the plan is: no full rebuild of the 154 tree. The full-build budget goes to the Chromium 156 sync tree, which Ship's `sync` stream sets up and builds cold. Worktrees that need to build clone that 156 tree once it compiles (about day 4), with `devutils/rac/worktree.sh setup <sync worktree>`. Don't run `worktree.sh setup` against the main checkout, and don't build a worktree cloned from it. Either one turns into a full rebuild.

So every stream starts in a **light worktree**: `git worktree add -b <branch> <path> origin/main`, with no `setup` and no build tree. It runs the understand and design stages, reading Chromium sources from the main checkout's `build/src`, read only. It drafts new code and unit tests in a git-ignored scratch folder in the worktree. The code becomes a patch through quilt once the stream has a tree cloned from the 156 base. Write against Chromium 156 APIs where they differ; the sync worktree has those sources once its checkout exists.

## Streams

A stream is one worktree, one branch, and one lead agent with helpers. Streams are split so they don't edit the same files. When two streams must touch one file, the brief names the owner, and the other asks or waits. Leads stagger their streams so the Air runs about 10 agent sessions at once, to start, and they watch memory pressure.

## Which model does what

On 2026-10-29 the maintainer got Devin, with free SWE-2 in the Devin CLI through 2026-11-30, and asked to move a lot of work to it. Spend SWE-2 freely: more attempts, more reviewers, more checks. Claude Sonnet and Opus still do the parts where quality depends on judgment.

| Tier | Models | Use it for |
| --- | --- | --- |
| Default worker, free | Devin SWE-2: `swe-2-high`, `swe-2-max` for hard bugs, `swe-2-medium` for quick reads | Most code with a clear spec: logic, prefs, wiring, unit tests, Chromium mapping, porting to 156 APIs, fixing review findings, first-pass and council reviews, attack tests against security code |
| Free backup | OpenCode `opencode/deepseek-v4.1-flash-free`, `opencode/glm-5.3-flash-free` | Second-family council votes, summaries, searches, and work SWE-2 is too slow for |
| Free, vision | `opencode/nemotron-3.5-super-vl-free` | First look at screenshots: blank frames, overlap, clipped text, wrong theme. A Claude model makes the final call |
| When available | Cursor `grok-4.7-medium` (free plan, usually out of usage) | A council vote. If it errors, skip it without retrying |
| Claude | Sonnet 5.5 | Routine UI code (UI goes to Claude), checking SWE-2 output before it lands, judging councils, running a stream |
| Claude, strongest | Opus 5.5 | Security code (guard, sign-in import, Keychain), architecture, UI and motion design, the final review of every PR, anything SWE-2 failed at twice |

How to call them, always from the shell in your own turn, never as threads:
- SWE-2: `cd <stream worktree> && timeout 1800 devin --model swe-2-high --permission-mode dangerous --respect-workspace-trust=false -p -- "<brief>"`, or `--prompt-file <brief.md>` instead of `-p -- "..."`. Run several in parallel when they touch different files. `devin` reads AGENTS.md.
- OpenCode: `timeout 1200 opencode run -m <model> --dir <stream worktree> "<brief>"`. Cursor: `timeout 1200 cursor-agent -p --trust --model grok-4.7-medium --workspace <stream worktree> --output-format text "<brief>"`.
- Give a complete brief: the goal, the exact files, the scorecard (see the hill-climb loop), what done looks like, and "read only" unless it must write.
- SWE-2 may edit files in its stream worktree and build through `devutils/rac/build-queue.sh`. Non-Claude models never write security-sensitive code (they may attack-test it), never write UI or motion design, never see real user data or secrets, and never commit, push, or open PRs. A Claude model reads their diff before it is committed.
- Never use OpenCode `auto` routing, Devin cloud sessions (not free), or the paid models inside Devin (its Claude, GPT, and Gemini options cost money).

## Hill-climb loop

Every batch climbs toward a written scorecard instead of stopping at "looks done."

1. **Scorecard first.** Before code, the lead writes `build/scratch/scorecard.md` (`build/` is git-ignored) for the batch. List each check as pass or fail: it compiles, the named unit tests pass, `he validate series` passes, the hunk budget holds, each spec item from the plan is met, the screenshot matrix items that apply, AI off costs nothing, and for agent work the `feat/agent-evals` scores. Add a number to climb where one exists (tests passing, eval score, findings left).
2. **Attempt.** SWE-2 implements against the scorecard. For risky or unclear work, run two or three attempts in parallel in separate scratch copies and keep the best.
3. **Check.** Build once for the batch, then run every check. Record the round in `build/scratch/hillclimb.md`: the score, what failed, and the commit.
4. **Council.** Three reviewers that don't see each other's answers: SWE-2 Max, an OpenCode model from a different family (or Grok when available), and Sonnet. Each returns findings with a severity and evidence: a line, a repro, or a screenshot. A Claude judge (Sonnet, or Opus for security and gate PRs) keeps only the findings it can confirm.
5. **Climb.** SWE-2 fixes the confirmed findings. Keep a round only if the score went up. If it went down, reset to the last best WIP commit. Repeat from step 3.
6. **Stop.** Stop when every scorecard item passes and the council has no confirmed blocking finding. If two rounds don't improve the score, escalate: Sonnet, then Opus, takes over the stuck item. Then comes the normal final review below.

## The build queue (D63)

Every local build goes through `devutils/rac/build-queue.sh`, never a bare `he build`. Ship writes it on day 0. Until it lands, build one at a time with a manual lock: `mkdir ~/.rac-build-queue/manual` before the build and `rmdir` after. If `mkdir` fails, someone else is building, so wait.

- `devutils/rac/build-queue.sh he build` waits for a slot, builds, and frees the slot, even on failure. `build-queue.sh status` shows who holds and who waits.
- Each Mac has two build slots. A full build takes both. Two run slots cover harness and eval runs.
- The sync and launch-gate work get priority. Everyone else is first come, first served.
- The queue refuses below 20 GB free disk or under critical memory pressure. It stops an incremental build past 20,000 steps unless D6 names it.
- **Verify in batches.** Don't build after every edit. Collect a batch of changes and their unit tests, build once, then run every test, screenshot, and video that batch needs before building again.
- Never hold a slot while thinking or fixing. Release it, fix, and queue again.

## Moving to Chromium 156 (D62)

1. Until the sync compiles, write rac-owned files on 154. When you call a Chromium or Helium API, check it against the 156 sources in the sync worktree's `build/src`, read only.
2. Ship announces the **156 base**, a tagged commit on the sync branch, about day 4. Hooks into Helium-shared files are written only on it.
3. To move a stream, make a new worktree from the 156 base branch with `devutils/rac/worktree.sh setup <sync worktree>`, then rebase your branch onto it. Never use `worktree.sh sync` to move a 154 worktree to 156. That is a full build.
4. Ask the maintainer before removing the old 154 worktree. Disk is tight.
5. When the sync merges, about day 7, rebase onto `main`. Then wait for your turn in Ship's merge order: the harness first, then launch gates, then the rest. Launch merges close at the start of day 13.

## Workflow: five stages per batch

1. **Understand.** Read-only subagents (Haiku or Sonnet) read the plan section, the files it touches, and AGENTS.md, and return a short map.
2. **Design.** Opus writes a one-page design (interfaces, hunk budget, test plan) before any code.
3. **Implement.** SWE-2 by default, per the hill-climb loop. Architecture and security code go to Opus. UI goes to Claude: Opus for design and visible polish, Sonnet for routine UI. Parallel helpers work on separate files.
4. **Verify.** Build once for the batch, then run the hill-climb checks and council until the scorecard passes.
5. **Review.** Before every PR, a fresh Opus reviewer that hasn't seen the design tries to break the diff (attacks, edge cases, missed surfaces, hunk count), then run `/code-review`. Fix or answer every finding. Check subagent output before building on it. Reviews need no build, so they run while the next batch is queued.

## Verification standard

- Build and run it yourself: `devutils/rac/build-queue.sh he build` (after `source dev.sh`), then `devutils/rac/worktree.sh run --rac-window-screenshot=/abs/path.png`. Wait for real pixels.
- Answer AGENTS.md "Cover every surface" item by item. Screenshot matrix: sidebar full, hidden, and edge reveal; light and dark; space themes; multiple windows; incognito; split view; an installed web-app (PWA) window; reduced motion; AI off (no AI button, row, or label).
- When a feature or fix in a worktree is done, post the proof in the thread's chat, not only in the PR. Show before and after screenshots of every changed surface, embedded as markdown images with absolute paths. If the change has an animation or an interaction (a click, a drag, a shortcut, a flow), also record a short video of it and embed or link it in the chat. The maintainer asked for this on 2026-10-27.
- Short videos for motion. Focused unit tests only. `he validate series` after touching `patches/series`.
- Every PR states its net-diff hunk change (D17) and attaches proof with `gh pr create --attach './shot.png#caption'`. Never commit screenshots or videos.
- PRs are opened only as D9b allows (otherwise only when asked). The maintainer approves every merge. Keep PRs small, about one to three per stream before launch, so the merge window moves.

## Hard constraints

- Never push to, open PRs against, or file issues on `imputnet` or `ungoogled-software`.
- Never edit `helium-chromium/`, `patches/helium/`, `patches/rebel/`, or `patches/ungoogled-chromium/`.
- `rac_version.txt` only goes up. The signing key and feed URL never change. Signing keys never leave GitHub.
- **Profiles.** Never launch a rac build without `--user-data-dir`. Always use `devutils/rac/worktree.sh run` or the harness, which pass it. Never use a real profile. Never run `he run` in a worktree, and never `open` rac.app.
- **Default browser.** No step changes the default browser. Link-routing checks use a harness verb (`open-urls URL`, which calls the same `application:openURLs:` router inside the worktree process).
- **Keychain.** No step unlocks the real "Arc Safe Storage" Keychain item. Arc import tests use fixture `Cookies` databases encrypted with a fixed test password, through a test-only seam that never calls the real Keychain.
- **By hand.** Real-Arc and default-browser checks are done by the maintainer, by hand, on a second macOS user.
- Never take the foreground (no foreground automation, no system dialogs).
- No full build, `he reset`, or deleting `build/` without approval. D6 names the five allowed builds. If a worktree build shows tens of thousands of steps, stop.
- **Other machines.** Agents SSH to the MacBook Pro only for D61's work, and only once it is back online (it is offline now, so the Air does everything). Runs there use `--rac-launch-in-background`.
