# 00. Master plan

How the seven plans fit together, in what order, on which machines, and what
must be true before rac launches for Arc users. The open choices are in
[decisions.md](decisions.md), cited here as D1, D2, and so on. "Ruling N"
means item N in [rulings.md](rulings.md). Terms such as W1, M0, the freeze,
and the door are defined in the [README](README.md#words-used-here).

## In plain English

Nobody can install rac yet, and Arc shuts down on 2026-12-22. So the first
job is shipping, not redesigning. One thread gets a signed build out, catches
rac up with Helium, and proves that updates work. In parallel, three other
threads build what launch needs: Arc import, a safer agent, and the import
screens. They also start the redesign in rac's own files, so nothing collides
with the Helium update.

rac stays one app. The browser is its own "server", and nothing runs in the
background. Outside agents such as Claude Code get a private door after
launch, behind its own switch. It is off by default.

The real limit is machines, not ideas. One 16 GB laptop can run two builds at
once at most. So launch work gets the build slots first.

If you approve by 11-02, rac launches in the week of 11-30, with a spare week
before the 12-15 hard stop. The command bar follows as a quick update if it
misses that week. Bigger changes land in January.

## Product direction

**At launch (W5).** Helium 0.20.1.1 on Chromium 156, with today's sidebar,
spaces, pinned tabs, and favorites. Arc import keeps spaces, pins, favorites,
and themes, plus sign-ins if they make it in time. The agent's hole is closed
and tested. With AI off, no AI button, row, or label appears anywhere. The
release is signed, updates are proven, and its network hosts are published.
It's for Arc refugees, many of whom want "as few AI buttons as possible".

**Right after launch (December to January).** The command bar becomes the
front door (Cmd+T, plus one setting to keep the new tab page, D13). Then Peek,
the little window for links from other apps, and Clear with Undo. One design
system: shared values, springs for things that move, nothing that repaints
while idle. Cmd+S and edge reveal move onto it. Custom space colors work in
dark mode.

**The architecture overhaul (January onward).** One action table drives the
sidebar, command bar, shortcuts, rac's agent, and outside agents, so safety
rules live in one place. An opt-in door lets your own coding agent drive rac
through MCP or a `rac` CLI. It reads only the tabs you share at first, and
later acts in its own background tabs with no logins and no focus stealing.
rac's agent stays warm between messages. Chats and runs move to an encrypted
local store. Spaces can get separate sign-ins. Then Boosts, Air Traffic
Control, and bangs.

**What does not change.** No server, no accounts, nothing phones home. AI is
off by default and costs nothing when off. rac stays on Chromium's Views UI,
as quilt patches on Helium. The goal is fewer edits to Chromium, not a new
shell.

## How the seven plans fit

```
06 Ship: sync to 156, signed builds, calendar, CI, bench
 │  (everything that touches Helium's hot files waits for 06's sync + base rebuild)
 ├─ 04 Data: Arc import, backups ─────► 01 draws the import screens
 │       └─ later: partitions ────────► 05 write tier (no-login agent tabs)
 ├─ 05 Agents: safety floor (launch) ─► later: door policy, agent workspace
 ├─ 03 Core: action table, core split ► 01 command bar rows, 05 tools, 07 shortcuts
 │       └─ door transport, warm agent, patch thinning
 ├─ 02 Design: tokens, springs ───────► 01, 05, 07 surfaces use them
 ├─ 01 Shell: command bar, Peek, little window, Clear, agent section
 └─ 07 Power: clean copy, Boosts, Air Traffic Control, bangs (on 01's router, 03's table)
```

**Order.**

1. Plan 06's pipeline and quiet 0.1.0, then the sync to 156.
2. The launch gates: 04 M0 and M1, 05 M0, and 01 M1's screens.
3. Pre-launch extras in rac-owned files, if build slots allow: 01 M0 and M2,
   02 M0 to M3, 03 M0 and M1.
4. After launch: the door (03 M2 with 05 M1), the warm agent (03 M3), 02 M4,
   01 M3 to M5, 04's storage work, 05 M2 and M3, and 07.
5. Then the plain-folder move (D58) and patch thinning (03 M4).

**Owners** ([rulings](rulings.md)): 06 the calendar, sync, and reveal port; 03
the action table and hunk metric; 01 Clear, archive, media controls, and
reveal timings; 02 motion and token names; 05 agent policy, debug doors, and
the agent workspace; 04 the Keychain fix and all storage.

## Sequencing against Arc's shutdown

Fixed dates: the launch build must start by **Tue 2026-12-15**, and Arc shuts
down on **Tue 2026-12-22**. Weeks count from approval (plan 06).

### Options

**A. Ship 0.1, then revamp, one after the other.** Only the Ship thread works
before launch. The revamp starts after it.
- For: no collisions, and the shared Mac is free for the sync.
- Against: five weeks with nobody working on the UI or architecture.
  Command bar and polish slip to February.

**B. Revamp first, launch later.** Redesign and re-architect, then sync and
ship.
- For: Arc users see the new rac on day one.
- Against: misses 12-22. Sync debt grows each week: failed hunks went from 43
  to 104 in one Helium release. Every revamp patch gets rebased twice.

**C. A stable track ships while the revamp runs on branches (recommended).**
Ship runs plan 06 M0 to M5 on `main`. The launch-gate work merges into `main`
after the sync. Revamp threads build in rac-owned files on Chromium 154
branches, rebase onto 156, and merge only what is ready by the start of W5.
The rest ships in point releases and in January.
- For: hits 12-22 with the update loop proven. No work waits idle.
- Against: build slots are the bottleneck (see machine rules). Some revamp
  work must code ahead and build later.

**D. Launch on 154, sync after.** The plan 06 slip path (D8).
- For: the fastest launch.
- Against: Chromium two majors old, and the 156 pipeline unproven. Use it
  only if the sync misses the end of W4 plus a one-week hold.

**Recommendation: C, approved by 11-02 (D1, D2).** If approval slips to 11-09,
there is no spare week: plan sidebar-only import (D43) and expect the command
bar as a point release. After 11-09, D falls back in.

### Calendar (approval by Mon 11-02)

| Week | Dates | Ship (06) | Core (03, 05) | Data (04) | UI (01, 02) |
| --- | --- | --- | --- | --- | --- |
| W1 | 11-02 to 11-08 | Depot signup on day 1; CI fixes; sync worktree; cold 156 build, timed | 05 M0 guard on 154; 03 M0 spikes | 04 M0a, M1a (new files); you run the scrub script | 01 M0 spikes, PWA check; 02 M0 rig |
| W2 | 11-09 to 11-15 | 0.1.0 smoke, then publish; sync design merges | 05 M0 evals; 03 M1 table (154) if slot | M1a fixtures | 01 M2 rac-owned code; agent rows design |
| W3 | 11-16 to 11-22 | **sync merged** (target); base rebuild starts | 05 M0 | M1a | 02 M1 to M3 in rac-owned files, if slot |
| W4 | 11-23 to 11-29 | base rebuilt; worktrees resync; 0.2.0 and `update-smoke`; `main` protected | debug doors on 156; rebase M0 | M0b Keychain; M1b applier; M2 sign-ins | rebase; 01 M1 screens; 01 M2 hooks |
| W5 | 11-30 to 12-06 | **merge cutoff at the start**; launch candidate; launch | fixes only | M2 only if green | fixes only |
| W6 | 12-07 to 12-13 | float; optional point release (D16) | | sign-ins point release | command bar, if it missed W5 |
| | 12-15 | hard stop: the launch build has started | | | |
| | 12-22 | Arc shuts down | | | |

**After launch (W7 on):** the first cadence sync in W6 or W7 (D18). Core:
the door, then the warm agent, then 05 M2 with UI's agent section. Data: the
full safety net, the partition spike with its in-memory variant first (D46),
then the AI store. UI: 02 M4 (springs on Cmd+S and reveal), 01 M3 and M4,
then M5 with Core. Power starts. Ship: beta channel, crash reports, the
plain-folder move. Core: thinning (03 M4), last.

**Effort before launch** (sums of the plans' estimates): 114 to 156
agent-days in five weeks: Ship 26 to 34, Data 16 to 21, Core 30 to 42, UI 42
to 59. Two build slots on the Air can't serve all of it. Only the launch-gate
share, about 57 to 77 days, is required.

## Thread map

Five threads. Four start after approval. Power starts after launch. Each
thread runs multi-agent workflows, tests with screenshots and video, and opens
PRs (D9b); you approve every merge. Opus leads every thread. Sonnet or a strong
open-weight model does scoped work under Opus review. UI work stays on Claude.

### Ship: engineering and shipping (plan 06)

- **Owns:** 06 M0 to M5, the sync, the base-tree rebuild, cadence syncs, the
  drift detector, the bench, the host list, the launch site pages, and later
  the beta channel, crash reports, and the plain-folder move (D58). It also
  owns the order of `patches/series` and the launch gate checklist. It asks
  you to merge PR #20, and asks before deleting `pullfrog.yml`; neither
  happens without you.
- **Mac and worktrees:** the sync Mac from D5, in `sync/helium-0.20.1.1`. CI,
  site, and docs work in light worktrees with no build tree (`ci/<name>`,
  `site/<name>`). Release builds compile on Depot, not on a laptop. Signing,
  notarizing, and the appcast run in a final job on a GitHub-hosted runner, so
  the keys never reach Depot (D4).
- **Can collide on:** `patches/series`; every hot patch during the sync;
  `patches/rac/sidebar-reveal/` and `patches/rac/settings/` (the port and the
  Layout move); `.github/`; `dev.sh` and `devutils/shared.sh`;
  `docs/operations/`; AGENTS.md; `site/`.
- **Avoid by:** the freeze (nothing under `patches/` merges until the sync
  does, D11). Ship alone edits `.github/` and the series order. After the sync,
  Ship hands `sidebar-reveal` to UI with one constant per timing.

### UI: shell, design, and motion (plans 01 and 02)

- **Owns:** 01 M0 to M4 and M6, 01 M5 jointly with Core, and 02 M0 to M5. It
  draws screens for the other threads: the import screens and restore prompt
  (Data), and Settings > Outside agents, the pairing card, the sharing control,
  and the Agents section (Core). It owns the screenshot harness in
  `patches/rac/dev/`.
- **Mac and worktrees:** the base Mac. At most two worktrees at once:
  `feat/ui-<milestone>` and `feat/motion-<milestone>`. Before the sync it has
  one build slot, shared by turns.
- **Can collide on:** `patches/rac/dev/` (C12); `chrome/browser/ui/views/rac/**`
  and the token files; `rac_strings.grdp`; onboarding (Data); the site control
  center (Core, Power); `app_controller_mac.mm` (Power); command ids and
  accelerators (Core, Power); the tab list layout manager (Core's 05 M2);
  `ui_features.cc`; settings pages.
- **Avoid by:** fixing interfaces in W1 and W2: token names (02), the action
  table schema (Core), `import_plan.h` (Data), and UI's agent-row design (W2).
  Plan 02's and plan 01's harness work go in one worktree, in turn.

### Core: rac core and agents (plans 03 and 05)

- **Owns:** before launch, 05 M0 (the launch gate, including the debug doors
  and gating dev switches with Ship), 03 M0 spikes, and 03 M1 (the action
  table and `RacCoreService`) if a slot allows. After launch: the door (03 M2
  with 05 M1, as one milestone), the warm agent (03 M3), 05 M2 and M3, native
  recipes later, and thinning (03 M4) last.
- **Mac and worktrees:** the base Mac, one worktree at a time
  (`feat/agent-<milestone>`, `feat/core-<milestone>`). The eval runner uses
  that worktree's build.
- **Can collide on:** `patches/rac/agent/` and `ai/`; `chrome/browser/rac/ai/`
  (Data's AI store); `rac_actions.{h,cc}` (UI, Power); the factory list in
  `chrome_browser_main_extra_parts_profiles.cc`; prefs and strings registries;
  `chrome/BUILD.gn` and `parts.py` (Ship's signing); tab-strip and
  session-restore hooks (Data's partitions); `docs/internals/ai.md`.
- **Avoid by:** landing the action table first, with plan 07's fields already
  in it, so Power only adds rows. Once 03 M1's one-hook registries exist,
  others register there, not in upstream files. Thinning touches a group only
  when nobody has an open PR on it.

### Data: storage and import (plan 04)

- **Owns:** 04 M0 and M1 (launch gates), and M2 (sign-ins) if it's ready.
  After launch: the full safety net, the partition spike and the in-memory
  variant Core needs (D46), the encrypted AI store, the export file, more
  importers, and sync if you change VISION.md.
- **Mac and worktrees:** the base Mac, one worktree (`feat/import-<milestone>`).
  The reader and fixtures are pure parsing, so they need only the unit-test
  target, which is a light build.
- **Can collide on:** the onboarding import handler (UI); `SpacesService`,
  `SidebarItems`, and the `rac spaces` store (UI, Core thinning);
  `keychain_password_mac.mm` (Helium patches it too, so after the sync);
  `browser_navigator.cc` and session restore (Core's 05 M2);
  `rac_ai_history.json` (Core); Local State prefs (Power's routes).
- **Avoid by:** writing only through `SpacesService` and `SidebarItems`;
  agreeing `import_plan.h` with UI in W1; taking turns with Core on navigator
  and restore. Data owns the AI store schema; Core reviews it.

### Power: power features (plan 07, after launch)

- **Owns:** 07 M0 to M5. Before launch, a UI subagent may write 07 M1's pure
  logic (the strip table, the naming rule) with unit tests only, using no
  build slot.
- **Mac and worktrees:** whichever Mac has a free slot after launch,
  `feat/power-<milestone>`.
- **Can collide on:** `rac_actions` rows (Core); `browser_shortcut_metadata.cc`
  and `spaces/commands.patch`; `browser_commands.cc`; the site control center
  (UI, Core); plan 01's router; omnibox and bangs files (UI, Helium).
- **Avoid by:** 07 M0 after Core's table lands, 07 M3 after UI's router lands,
  and 07 M5 after a Helium diff check.

### Rules for every thread

1. **One owner per shared file**, as listed above. Others ask or wait.
2. **The freeze.** Nothing under `patches/` merges until the sync does. Then
   every branch rebases.
3. **`patches/series`.** Append only inside your group's block, run `he
   validate series` in every PR, and let Ship settle the order.
4. **Strings.** `dev_names.py unsub` before editing a string file,
   `worktree.sh sync` after `quilt refresh`. If collisions get frequent, split
   `rac_strings.grdp` into one part per area.
5. **Hunk counts.** Every PR states its net-diff change (D17).
6. **Big refactors** (the plain-folder move, thinning) run in announced quiet
   windows with no open PRs on those groups.
7. **No foreground, no real profiles.** Only the `--rac-window-screenshot`
   harness and `worktree.sh run`.

### Machine rules (plan 06 limits)

- **The Air** (base Mac today): M1, 8 cores, 16 GB, 101 GB free. One full
  build, or at most two incremental worktree builds, never both. During a full
  build, its threads write code and queue their builds.
- **The base-tree rebuild after the sync** (W3 to W4) blocks every worktree
  on that Mac. Each then runs `worktree.sh sync` or is recreated. Its length is
  unknown until Ship times the W1 cold build. Stop any worktree build that
  shows tens of thousands of steps (AGENTS.md).
- **A cheaper path (D6).** The sync worktree already holds a built 156 tree.
  After the sync merges, new and rebased worktrees can run `worktree.sh setup
  <sync worktree>` instead, and the main checkout's rebuild moves to a quiet
  night or waits for the next sync. Ship checks this in W3 on a throwaway
  worktree.
- **Slot priority:** launch gates first (05 M0, 04 M0 and M1, 01 M0's PWA
  check, 01 M1), then 01 M2, then 02 M1 to M3 and 03 M1.
- **If the Pro qualifies (D5),** it runs the sync and holds the 156 base. New
  worktrees are cloned there after W4, while the Air finishes its 154
  branches. Set the Pro's build limit once the W1 build measures its memory.
  It's your main machine, so it will be slow while it builds.
- **kainoas-linux-mba** can run patch-only checks (Python tests, `he validate
  series`, dry runs, the hunk counter). It can't build the Mac app.

## Launch gates

The one gate list, merged from all plans. Other plans point here and keep no
list of their own. Plan 06 M5 checks every item before the launch candidate
builds.

| # | Gate | From |
| --- | --- | --- |
| G1 | Arc sidebar import: spaces, pins, favorites, open tabs, themes. A rerun adds nothing, Undo works, and the import makes zero network requests. Includes plan 01's import screens and the "what didn't come over" list. Sign-ins are not required | 04 M1, 01 M1 |
| G2 | A snapshot before every import, and the restore prompt after a corrupt `Preferences` | 04 M0a |
| G3 | The Keychain "no silent reset" fix, with its unit test | 04 M0b (ruling 13) |
| G4 | Agent safety floor: the taint rule, fail-closed defaults, page-text marking, tier 1 evals green within the false-card budget, AI-off test set 1 | 05 M0 |
| G5 | Debug doors refused on the real profile | 05 M0 (D20) |
| G6 | Dev switches compiled out of release builds, including plan 02's frame-log and contrast flags and plan 04's `--rac-import-source-root` | 05 M0, 02 M0, 04 M1, 06 |
| G7 | Public copy matches behavior: the onboarding promise, "It asks before it acts", "thin layer", "four weeks", and the `ai.md` table | 05 M0, 06 M5 |
| G8 | The synced build passes the surface matrix, including an installed web app (PWA) window, with no AI labels when AI is off | 06 M2, 01 M0 and M1 (rulings 16, 17) |
| G9 | The signed, notarized, synced build passes `install-smoke` and `update-smoke` (0.1.0 to 0.2.0). The bad-release runbook exists | 06 M1, M3 |
| G10 | The network host list is published from a capture | 06 M4 |
| G11 | Speed numbers against Helium are published, or the site line is softened (D60) | 06 M4 |
| G12 | A DRM test page is checked before any Widevine claim | 06 M5 |
| G13 | `main` is protected (D10) | 06 M4 |
| G14 | A clean runner goes from download to imported Arc spaces in under 5 minutes, on video | 06 M5 |
| G15 | With AI off, no AI button, row, or label appears on any surface a launch PR touched | ruling 16, all plans |

**Not gates:** the command bar (D16), sign-in import (04 M2), plan 02's
polish, plan 07 M1, and Peek, the little window, and Clear.

## After your review

0. **Update your main checkout first.** Its `main` is 71 commits behind
   origin/main (verified 2026-10-27), so every worktree would clone a stale
   base. Fast-forwarding it with `git -C /Users/knewton/Dev/Github/rac pull
   --ff-only` and running one incremental `source dev.sh && he build` there
   needs your approval (D6). That checkout has an uncommitted `.gitignore`
   change and is in the merged state, so deal with both first. No thread
   starts before this is done.
1. You edit the plans and answer [decisions.md](decisions.md), group A first.
2. The conflict resolutions you accept get written into the plans.
3. VISION.md, AGENTS.md, and `docs/roadmap.md` changes land only with your
   sign-off.
4. Then the four threads launch, each from its brief in `plans/threads/` plus
   this thread map. Not before.
