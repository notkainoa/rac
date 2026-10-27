# Decisions

Every open choice from the seven plans, each with a recommendation. Group A
is needed on day 0, the day you approve. Groups B and C wait until their
thread reaches that milestone. Days count from approval, assumed on Wed
2026-10-28. The D-numbers never change. The id after each D-number is the
plan's own, such as 06-D5. Ids that start with M come from fitting the plans
together.

The 15 conflicts between plans (C1 to C15) are resolved, and the fixes are
written into the plans.

## Your answers (2026-10-27)

Group A is accepted as recommended, with these changes:

- **D4 is answered: free first.** Free GitHub runners for Apple Silicon only, with fail-fast off, the checkpoint download retried, and PR #20 merged. You will ask Depot about open-source sponsorship later, not on day 0. Paid Depot is the fallback only if a free build fails twice, and paying needs your word at that time.
- **D5 has no answer yet.** It also decides how much the Pro does under D61. The Air does everything until the Pro is online and you give its RAM and free disk.
- **New direction: much shorter and more parallel.** You expect the work to take a couple of weeks. Full builds are rare and run in the background, and nobody waits on them. More work runs in parallel. So D1, D6, D8, D9a, D11, and D16 are rewritten, every date-tied decision now names a day, and D61 to D64 are new. The rewritten and new ones need your answer again.

Later answers, also 2026-10-27:

- **D3 is answered: no.** There is no quiet 0.1.0 on Chromium 154.
- **D64 is answered: two release builds,** both from the synced Chromium 156 tree, both fire-and-forget on free GitHub runners. Build 1 is 0.1.0, quiet and unannounced, fired once the sync merges, about day 7. Build 2 is the launch build, 0.2.0, fired on day 13. It proves the in-place update from 0.1.0 before it is announced. If build 1 slips, the update proof moves to the first point release, and launch is not blocked on it unless you say so.
- **D6 is approved.** Step 0 is done: the main checkout was pulled to d3f0d66 and synced, and its incremental build is running.
- **D61 is approved,** but the Pro is offline (last seen on Tailscale 2 days ago). The Air does everything until it comes online. D5 is still unknown.
- **Accepted as recommended:** D1, D8, D9a, D11, D16, D62, and D63.

You also set a rule for every thread: when a feature in a worktree is done, the agent posts before and after screenshots in the chat, plus a video when the change has an animation or an interaction. See [threads/README.md](threads/README.md).

## Answers from day 0 (2026-10-27, evening)

- D13: yes. Cmd+T opens the command bar, with one setting for the normal new tab page. The VISION.md change is approved.
- D28 to D31: as recommended. Opt+Cmd+N goes to the little window, and Helium's new-split-tab action loses that default.
- Command bar details: suggestions only when two or fewer local rows match and typing pauses for 300 ms; "+" and File > New Tab keep the normal new tab; Enter opens in place and Cmd+Enter in a new tab; pinned tabs and favorites in one section; accent matching later.
- Clear: the divider shows even without pinned tabs; the label is always visible; video-call and tab-group tabs are spared; no Clear in incognito at launch; the one-hunk hook makes one Clear one Undo.
- A minimal action table may merge before the day-13 cutoff (ready day 10, merged day 11).
- PR #20 is merged (d8b2a87).
- The signins stream stays on Opus 5.5 with a narrower brief. No automatic model switching.

## Group A at a glance

These are the 20 day-0 decisions. D9 has three parts. Rows marked **Answered**
were settled on 2026-10-27. Only D5 is still unknown.

| D | Question | Recommended | Flag |
| --- | --- | --- | --- |
| D1 | By when do you approve the plans? | Wed 10-28, for a launch on Mon 11-16 (day 19) | Answered |
| D2 | In what order does the work happen? | A stable track ships while the revamp runs in parallel streams | |
| D4 | How are release builds compiled, and for how much? | Answered: free GitHub runners first, Depot sponsorship asked later, paid Depot only if a free build fails twice and you say so | Money, Answered |
| D5 | What are the MacBook Pro's RAM and free disk? | Still unknown. The Pro is offline, so the Air does everything for now | Open |
| D6 | Which full builds do you approve now? | Approved: the five named in the master plan, and no others. Step 0 is done | AGENTS, Answered |
| D9a | Which threads launch? | All five on day 0. Power writes pure logic only until Core's table lands | Answered |
| D9b | May threads open PRs without asking each time? | Yes. You still approve every merge | AGENTS |
| D9c | May threads drive rac through the test tools? | Yes, on throwaway profiles only | AGENTS |
| D11 | Accept plan 06's default list? | Accept all, with the freeze replaced by D62 | Answered |
| D14 | Build Peek, and does it enter history? | Yes, and history only once a Peek is expanded | VISION |
| D16 | Is the command bar a launch gate? | No. It ships if merged by day 13, else in the first point release, about day 26 | Answered |
| D17 | Which patch-size number do the plans hold to? | Net-diff hunks plus first failures per sync | |
| D19 | How do we close the agent's `auto` hole? | The taint rule, with `auto` kept as the default | |
| D20 | What happens to Chromium's debug doors? | Refuse them on the real profile, with no new setting | |
| D21 | Does rac run a separate local server or helper? | No. The browser is the server | |
| D22 | How do we shrink rac's Chromium edits? | Stay on Views and thin the hooks | |
| D41 | What real Arc data can we test on? | You scrub your own Arc now, volunteers after beta | Real data |
| D42 | How big is the safety net before launch? | A snapshot, one rolling backup, and the Keychain fix | |
| D61 | Does the MacBook Pro become a second build Mac? | Approved, but the Pro is offline. The Air does everything until it is back | AGENTS, Answered |
| D62 | What replaces the three-week freeze? | A one-week freeze, with streams stacked on the 156 base from day 4 | Answered |
| D63 | How do many agents share one Mac's builds? | A build queue with two slots, and verification in batches | AGENTS, Answered |
| D64 | How many release builds before launch? | Answered: two from the 156 tree, 0.1.0 about day 7 and the launch build 0.2.0 on day 13 | Answered |

Reply with the D-numbers you disagree with; everything else is accepted.

## A. Needed on day 0

**D1 (M-1). By when do you approve the plans?** Wed 10-28, or later.
**Answered on 2026-10-27: as recommended, Wed 10-28.** Launch is then Mon 11-16 (day 19), with room for
one retry of the launch build. Each day later moves launch one day. The 12-15
hard stop still holds for approval by about 12-02.
[06 critical path](06-engineering-and-shipping.md#critical-path)

**D2 (06-D5). In what order does the work happen?** (a) Ship, sync, and
launch, and only then revamp. (b) Revamp first and launch later. (c) A stable
track ships 0.1, the sync, and the launch, while the revamp is built on
branches in rac-owned files and merged after the sync.
**Recommended: (c).** No thread waits idle. The revamp runs in parallel
streams and stacks on the 156 base once the sync compiles (D62). Plan 06's
sequencing section calls this C1 plus ruling 1.
[Master plan](00-master-plan.md#order-of-work)

**D4 (06-D2). How are release builds compiled, and for how much?** Free
GitHub runners, Depot runners (sponsored or paid), or a local Mac.
**Answered on 2026-10-27: free first.** Free GitHub runners build Apple
Silicon only, with fail-fast off, the flaky checkpoint download retried, and
PR #20's pax fix merged. You will ask Depot about open-source sponsorship
later, not on day 0.
Each free build takes about 1.5 days, which is fine because nothing waits on
it. Signing and notarizing still run on GitHub's own runner, so the keys
never leave GitHub.
**Trigger for paid Depot:** a free build fails twice in a row, or can't finish
its framework link inside a 6-hour phase. Paying needs your word at that
time. The cap is $300 a month, about $35 to $70 a build.
[06 build route](06-engineering-and-shipping.md#build-route-a1-to-a3)

The routes considered on 2026-10-27:

1. Free GitHub runners, Apple Silicon only. It costs nothing but time: a build is a chain of 6-hour jobs that takes about 1.5 days. It has never finished. In the last run the Apple Silicon chain had about 3,400 steps left when the Intel chain failed and cancelled it. Turning off that cancel and retrying the flaky download may be enough.
2. Ask Depot for free open-source runners. Helium's Depot runners are sponsored. Only you can ask.
3. A self-hosted runner on one of your Macs. The keys stay in GitHub, but the job runs on your Mac and uses it for hours. On the 16 GB Air it competes with every worktree build.
4. Build and sign on your Mac by hand. It is free, but the signing keys sit on a laptop.

You chose route 1, with route 2 asked later and paid Depot as the fallback.

**D5 (06-D1). What are the MacBook Pro's RAM and free disk?** Tell us both,
or let an agent read them with
`ssh knewton@kainoas-macbook-pro 'sysctl -n hw.memsize; df -h ~'`.
**Still unknown, and the Pro is offline (last seen on Tailscale 2 days ago).
The Air runs the sync and the 156 base for now.** Rule once it is back: with at
least 32 GB of RAM and 150 GB free, the Pro takes over the sync's base work
(D61). Otherwise the Air keeps it. The Air has 16 GB and 101 GB
free. The Pro is your main machine, so long builds will slow it.
[06](06-engineering-and-shipping.md#what-you-need-to-decide)

**D6 (M-2). Which full builds do you approve now?** The named list below, or
ask each time.
**Approved on 2026-10-27: these, and no others, before launch.** AGENTS.md
requires your approval for full builds and `he reset`.
1. Day 0, done: one incremental `he build` in your main checkout. It was pulled
   to d3f0d66 and synced, and the build is running.
2. Day 0: one cold 156 build in the sync worktree. Helium's patches build
   first, overnight, then rac's build on top, incrementally.
3. From day 4: worktrees on the same Mac clone the sync worktree's built
   tree with `worktree.sh setup <sync worktree>`. No new full build.
4. Only if the sync moves to the Pro (D61): one cold 156 build on the Air, in a
   `base-156` worktree, on day 4, overnight. This is the one base rebuild. It
   doesn't apply while the Pro is offline.
5. The CI release builds in D64.

Not approved: `he reset` in the main checkout before launch. It stays on 154
until after launch. Its one 156 rebuild then is optional, and asked for
separately. Removing a stream's old 154 worktree once its branch is on 156
also needs your OK, under AGENTS.md.
[06 M2](06-engineering-and-shipping.md#m2-sync-to-helium-02011--chromium-156-days-0-7-slack-to-day-10)

**D9a (M-3). Which threads launch?** All five on day 0, or four now and Power
after launch.
**Recommended: all five on day 0.** You asked for this on 2026-10-27. Power
writes pure logic with unit tests until Core's action table lands, about day
16. Its hooks also wait for UI's link router.
[Master plan](00-master-plan.md#thread-map)

**D9b (M-3). May threads open PRs without asking each time?** Yes, or ask for
each PR. You approve every merge either way.
**Recommended: yes.** AGENTS.md says "never open a PR unless asked", so this
needs your sign-off. Ship still asks you to merge PR #20 and before deleting
`pullfrog.yml`.

**D9c (M-3). May threads drive rac through the screenshot harness, bench, and
eval runner?** Yes, on throwaway profiles with no other automation, or ask
each time.
**Recommended: yes.** AGENTS.md says to ask before driving the browser with
automation, so this needs your sign-off.

**D11 (plan 06 defaults). Accept plan 06's "I'll do these unless you object"
list?** The list has one jump to Helium 0.20.1.1, the freeze, C++ tests in
worktrees first, no Chromium 157 before launch, and the beta channel and
crash reports after launch, and publishing speed numbers against Helium
(D60).
**Recommended: accept all, with the freeze replaced by D62.** Nothing under
`patches/` merges until the sync does, because every new patch edits
`patches/series`, the one file the sync conflicts on. Docs, the site, CI, and
plans may merge. Under D62 that wait is about a week, and nobody stops
working during it.
[06](06-engineering-and-shipping.md#what-you-need-to-decide)

**D14 (01-D4). Build Peek, and does it enter history?** Yes with history only
once expanded, yes and always in history, or no.
**Recommended: yes, history only once expanded.** VISION.md lists Peek as
"not planned". It is needed on day 0 because a "no" cancels a 2 to 3 day spike.
[01](01-ui-shell.md#what-you-need-to-decide)

**D16 (M-5). Is the command bar a launch gate?** It could be a gate, ship
only if it merges in time, or wait for January.
**Recommended: not a gate. It ships in the launch if merged by the start of
day 13. Otherwise it ships in the first point release, about day 26, only if
`update-smoke` passes.** Day 13 is tight for it, so plan on the point
release.
[01 M2](01-ui-shell.md#milestones)

**D17 (03-D5). Which patch-size number do the plans hold to?** Net-diff hunks
plus first failures per sync, or raw stacked hunks.
**Recommended: net-diff hunks plus first failures per sync.** Until Ship's counter reports a baseline, about day 2, stacked hunks stay at 630 or fewer, aiming
for 550. Every plan's new hunks count against this budget.
[03](03-core-architecture.md#how-to-shrink-the-patch-surface-03-d4-03-d5)

**D19 (05-D1). How do we close the `auto` hole?** The taint rule, `careful` as
the default, or both.
**Recommended: the taint rule, with `auto` kept as the default.** Once the
agent has read a second site, it asks before acting on each site. Core builds
it in M0.
[05](05-agents-and-ai.md#what-you-need-to-decide)

**D20 (05-D6). What happens to Chromium's debug doors?** Refuse them on the
real profile with no new setting, leave them, or add an expert switch.
**Recommended: refuse, with no new setting.** Dev runs use `--user-data-dir`,
so the DevTools-port screenshot flow keeps working. It is launch gate G5.
[05](05-agents-and-ai.md#what-you-need-to-decide)

**D21 (03-D1). Does rac run a separate local server or helper?** No, a Rust
helper, or a Node sidecar.
**Recommended: no.** The browser is the server. There is no Swift helper
either, so local models stay on Ollama and LM Studio.
[03](03-core-architecture.md#where-the-backend-runs-03-d1)

**D22 (03-D4). How do we shrink rac's Chromium edits?** Stay on Views and thin
the hooks, or build a native AppKit shell now.
**Recommended: Views.** Spike a native shell only if D17's target is missed
after the second sync. UI's plan assumes Views, so this is needed on day 0.
[03](03-core-architecture.md#what-you-need-to-decide)

**D41 (04-D4). What real Arc data can we test on?** You run a scrubbing script
on your own Arc, volunteer samples after beta, or synthetic data only.
**Recommended: the scrubbing script now, and volunteers after beta.** Without
a real sample, tests only prove the reader matches Cra's notes. You run the
script on your own data (see below).
[04](04-data-storage-import-sync.md#what-you-need-to-decide)

**D42 (04-D5). How big is the safety net before launch?** A pre-import
snapshot, one rolling backup, and the Keychain fix, or a full 14-day rotation
and a Restore UI now.
**Recommended: the minimal set now, the rest after launch.**
[04](04-data-storage-import-sync.md#what-you-need-to-decide)

**D61 (M-7). Does the MacBook Pro become a second build Mac?** (a) Yes: it
hosts the sync and a 156 base from day 0, with its own build queue. (b) No:
the Air does everything. (c) Only after launch.
**Answered on 2026-10-27: (a) approved, but the Pro is offline** (last seen on
Tailscale 2 days ago). The Air does everything until it comes online, and D5
is still unknown. The recommendation was (a) if D5 shows at least 32 GB and
150 GB free, otherwise (b). It roughly doubles build capacity in the busiest week. It keeps the
sync's overnight cold build off the Air, so the Air's two slots stay with
the feature streams. The costs:
- About half an agent-day to set it up: a clone of rac, Xcode, and the
  Homebrew tools.
- One extra cold build on the Air (D6, item 4), because clones work only
  inside one Mac.
- A slower Pro while it builds. It runs one build at a time and pauses when
  you ask.

Approving (a) is asking agents to SSH to the Pro for this work only. Runs
there use `--rac-launch-in-background` and throwaway profiles, and never
take the foreground.
[Master plan](00-master-plan.md#machine-rules)

**D62 (M-8). What replaces the three-week freeze?** (a) Features build on
154 and rebase once onto 156 after the sync. (b) The sync worktree rebases
each feature patch as it lands on `main`. (c) A one-week freeze, with
streams stacked on the 156 base.
**Recommended: (c).** Before the sync compiles, streams write rac-owned files
on 154 and check every API they call against the 156 sources, read from the
sync worktree. About day 4, Ship tags the compiling sync as the 156 base.
Streams clone its built tree and write their hooks in Helium-shared files on
156. When the sync merges, about day 7, they rebase onto `main` with almost
nothing to fix, and merge in Ship's order: the harness, then launch gates,
then the rest.
- (a) finds hot-file conflicts and compile breaks late, and every worktree
  still needs a 156 tree.
- (b) puts every rebase on the sync, the one serial thread, and verifies each
  feature twice, on 154 and again on 156.
- (c) moves hooks onto 156 about three days earlier than (a). Its cost is
  rebasing stacked worktrees on late sync fixes. Those are small changes late
  in the series, so they rebuild little.

[Master plan](00-master-plan.md#order-of-work)

**D63 (M-9). How do many agents share one Mac's builds?** (a) A build queue
on each Mac, with verification in batches. (b) Leads agree on slots by
message. (c) No limit.
**Recommended: (a).** `devutils/rac/build-queue.sh` wraps `he build`. It has
two build slots, and a full build takes both. Two run slots cover harness and
eval runs. It refuses below 20 GB free or under critical memory pressure, and
stops an incremental build that shows more than 20,000 steps. Agents write
code, tests, and reviews without building, then build once per batch and run
every check that build allows. Ship writes it on day 0. It changes AGENTS.md's
"Build with `source dev.sh && he build`".
[06 build queue](06-engineering-and-shipping.md#build-queue-d63)

**D64 (M-10). How many release builds before launch?** (a) Two: 0.1.0 and the
launch build. (b) Three: add a 0.2.0 update proof from the synced `main` on
day 7. (c) More, as needed.
**Answered on 2026-10-27: (a), two builds,** both from the synced Chromium 156
tree and both fire-and-forget on free GitHub runners.
- Build 1 is 0.1.0, quiet and unannounced. It is fired once the sync merges,
  about day 7, and published about day 9.
- Build 2 is the launch build, 0.2.0, fired on day 13. On day 15 it proves the
  in-place update from 0.1.0, before it is announced.
- If build 1 slips, the update proof moves to the first point release, and
  launch is not blocked on it unless you say so.

After launch, at most one point release a week, plus security fixes.
[06 M1](06-engineering-and-shipping.md#m1-010-the-first-signed-release-days-1-10-build-1)

## B. Needed later, by thread

### Ship (plan 06)

**D3 (06-D4). Publish a quiet 0.1.0 on Chromium 154 first?** Yes, labeled
"Preview", or wait for the synced build.
**Answered on 2026-10-27: no.** 0.1.0 is built from the synced 156 tree
instead (D64), and 0.1.0 to the launch build proves updates.

**D7 (06-D3). Support Intel Macs at launch?** (Money) Yes, at about $99 a
build on Depot, or no. Needed on day 0, before the `arches` input.
**Recommended: no, Apple Silicon only for 0.x.**
[06](06-engineering-and-shipping.md#intel-b1-b2)

**D8 (06-D6). What if the sync isn't merged by day 10?** Launch on 154 as a
labeled preview, or hold the launch.
**Answered on 2026-10-27: hold, as recommended.** Arc's shutdown is a month after the target, so holding
is cheap, and the other streams keep working on the 156 base. Decide on a 154
launch only if the sync isn't merged by day 30 (11-27). That fallback must
start by 12-15.

**D10 (plan 06 default). Protect `main` and add a `rac-bot` machine user?**
Yes, or no. With yes, PRs need Linux checks and your approval, and agents push
as `rac-bot` while commits stay authored by Kainoa Newton. Needed by day 5,
before the merge window.
**Recommended: yes, by day 5.** It adds a short PR-flow section to
AGENTS.md.
[06 M4](06-engineering-and-shipping.md#m4-checks-protection-and-evidence-days-0-10)

**D18 (06-D7). How often does rac sync after launch?** Every Chromium major
within 14 days, or every other major. Security fixes go out in 7 days if
exploited, otherwise 14. Needed by launch, day 19.
**Recommended: every major, reviewed after three cycles.**
[06](06-engineering-and-shipping.md#cadence-e1-e2)

**D60 (plan 06 default). If speed numbers against Helium aren't ready, does
the site soften "never slower"?** (VISION) Yes until the numbers are
published, or keep the line and delay the site. Needed by day 10.
**Recommended: yes.** It is launch gate G11.

### UI (plans 01 and 02)

**D13 (01-D1). Does Cmd+T open the command bar?** (VISION) Yes with one
setting to get the new tab page back, yes with no setting, or no. Needed by
day 2.
**Recommended: yes, plus one setting.** VISION.md makes the command bar a
choice today.

**D15 (M-4). Move the command bar and the little window ahead of
`docs/roadmap.md`'s order?** Yes and rewrite the roadmap, or keep the order.
Needed by day 10.
**Recommended: yes.** The roadmap puts the command bar in phase 5 and the
little window in "Later".

**D28 (01-D2). What do Cmd+L and a click on the address bar do?** Both open
the command bar, Cmd+L opens it and a click edits in place, or both edit in
place. Needed on day 0 for 01 M2.
**Recommended: Cmd+L opens it, and a click edits in place.**

**D29 (01-D3). When do command bar queries reach the search engine?** Same as
the address bar, only after local results run out and typing pauses, or
never.
**Recommended: only after local results run out and typing pauses.**

**D30 (01-D8). Move Ask from the AI new tab page into the command bar?** Yes
and retire the AI new tab page, or keep both.
**Recommended: yes.** It removes one AI surface.

**D31 (01-D6 and 07-D7). Whose keyboard shortcuts?** Chrome's for standard
actions and Arc's for rac's own, Arc's everywhere, or new keys that clash with
nothing.
**Recommended: Chrome's for standard actions, Arc's for rac's own, and Cmd+O
only inside Peek and the little window.** Taking Opt+Cmd+N moves Helium's
split-view shortcut, so it needs your OK under AGENTS.md.

**D32 (02-D2). Glass or solid?** Solid as today, or blur behind the window by
default. Needed by day 3.
**Recommended: solid.**

**D33 (02-D3). Which space themes?** Eight presets, presets plus custom
colors, or a full gradient editor. Needed by day 3.
**Recommended: presets plus custom colors.** This also fixes dark mode for
imported Arc spaces.

**D34 (02-D4). Do buttons shrink when pressed?** Never, favorites tiles only,
or every icon button.
**Recommended: never.**

**D35 (02-D5). Do keyboard shortcuts animate?** Spatial changes only, or
never.
**Recommended: spatial changes only.**

**D36 (02-D6). What corner does the page card get?** (a) Concentric with the
window, which is 11 px on macOS 26 and 10 px on older macOS. (b) Dia's 10 px
everywhere.
**Recommended: (a).**

**D37 (02-D7). Under Reduce Motion, does a swipe follow your fingers?** No,
or yes with a fade on release.
**Recommended: yes.**

**D38 (01-D5). Do links from other apps open in a little window?** Yes by
default, opt-in, or not built. Needed by day 5, before 01 M3's build.
**Recommended: yes by default, in the last-used space, keeping nothing when
closed.** Testing it touches your real data (see below).

**D39 (01-D7). How does clean-up work?** (VISION, for auto-archive) Manual
Clear only, Clear now with opt-in auto-archive later, or auto-archive on.
**Recommended: Clear now with Undo. Auto-archive comes later as an opt-in,
off by default, and keeps an imported Arc user's own setting.**
[01 Clear](01-ui-shell.md#clear-and-archive-owned-here-ruling-4)

**D40 (02-D1). How springy is Cmd+S?** Dia's spring with about 3.4 px of
bounce, a calmer 1.2 px, or none. Needed by day 7, for 02 M4.
**Recommended: the calmer spring, confirmed by a side-by-side video.**

Links for this group: [01](01-ui-shell.md#what-you-need-to-decide) and
[02](02-visual-design-and-motion.md#what-you-need-to-decide).

### Core (plans 03 and 05)

**D12a (03-D6 and 05-D7). Does the outside-agent door work with rac's AI
off?** Yes, or no. Needed by day 14, when the door starts.
**Recommended: yes.** "AI off costs nothing" still holds, because the door
has its own switch, off by default, and nothing listens while it's off.

**D12b (03-D6 and 05-D7). Add a separate outside-agent promise to
VISION.md?** (VISION) Add a scoped promise, or reword the AI rule. The
promise says the door has its own switch, off by default, nothing listens
while it's off, and "Outside agents: on" shows next to the AI switch.
**Recommended: add the scoped promise.** Plan 05 has draft text.
[05 fit](05-agents-and-ai.md#fit-with-the-non-negotiables)

**D23 (05-D3). What is an agent's workspace?** An Agents section in the
sidebar, its own space, or an off-screen window. Needed by day 3, when UI designs
the rows.
**Recommended: the Agents section, with one group per client, shown only
while it has tabs.** The off-screen window is the fallback if the rendering
spike fails.

**D24 (03-D2). How do outside agents connect?** A per-profile socket, a signed
relay, and per-client tokens, or loopback HTTP with OAuth. Needed before the
door milestone.
**Recommended: the socket, relay, and tokens.** Add HTTP only if 03 M0's
spike shows a client needs it.
[03](03-core-architecture.md#how-outside-agents-connect-03-d2)

**D25 (05-D5). Which doors?** MCP, a `rac` CLI with a skill, or both.
**Recommended: both, from one relay, with MCP first.**

**D26 (05-D2). What does a newly connected outside agent get?** Read the tabs
you share, act in its own no-login tabs, or act in your tabs at your level.
**Recommended: it reads the tabs you share. You can raise it to act in its
own tabs.** The door is one milestone, 03 M2 with 05 M1, days 14 to 30.

**D27 (03-D3). Keep rac's own agent warm between messages?** Restart for
every message, or keep one warm agent per profile with a 5-minute idle cap.
Needed by day 22, before 03 M3.
**Recommended: warm, one per profile, 5-minute cap.** This changes `ai.md`'s
"a run is one prompt".

Links for this group: [03](03-core-architecture.md#what-you-need-to-decide)
and [05](05-agents-and-ai.md#what-you-need-to-decide).

### Data (plan 04)

**D43 (04-D1). What does the pre-launch import bring?** The sidebar only, the
sidebar plus sign-ins, or those plus passwords. Needed by day 8, when sign-ins either chase the launch or move to
the first point release.
**Recommended: the sidebar plus sign-ins, from Arc only. If sign-ins aren't
merged by day 13, launch with the sidebar and ship sign-ins in the first
point release.**

**D44 (04-D2). How do Arc profiles map?** Everything into one profile, each
Arc profile to a rac profile, or per-space sign-ins in one window.
**Recommended: each Arc profile becomes a rac profile.** It is the cheapest
correct path before 12-22. Users with two Arc profiles get two windows.

**D45 (04-D3). How do saved passwords move?** (a) A plaintext CSV on a RAM
disk, never on the SSD, which any app you run can read until it unmounts. (b)
Guide Arc's own export. (c) A plaintext temp file on the SSD. (d) Turn on
Chromium's password manager.
**Recommended: (a) if the one-day spike passes, otherwise (b).** Both briefly
create a plaintext file, but (a) never touches the SSD. (c) needs your
sign-off.
[04 M2](04-data-storage-import-sync.md#m2-arc-profiles-and-sign-ins-m-6-8-agent-days)

**D46 (04-D6). After launch, how do spaces get separate sign-ins in one
window?** A storage partition per space, or a full profile per space.
**Recommended: a partition per space, after a spike.** The in-memory
no-login variant comes first, because the outside-agent write tier waits for
it. This bends VISION.md, since spaces would then keep logins apart too.
[04 after launch](04-data-storage-import-sync.md#after-the-launch)

**D47 (04-D7). After launch, how are AI chats and agent runs stored?**
Encrypt today's JSON, or one encrypted SQLite store with retention.
**Recommended: encrypted SQLite.** It covers plan 05's chat-encryption item
too.

Links for this group: [04](04-data-storage-import-sync.md#what-you-need-to-decide).

### Power (plan 07, after launch)

**D48 (07-D8). In what order?** By Arc-refugee demand (Boosts, routing, then
bangs), or by the roadmap with bangs first.
**Recommended: by demand.**

**D49 (07-D3). Where does clean-link copy apply?** Shift+Cmd+C and the tab
menu, or also the page's "Copy link address".
**Recommended: Shift+Cmd+C and the tab menu only, with no setting.**

**D50 (07-D4). How are tab groups named?** A simple rule, or the rule plus a
"Name with AI" button when AI is on.
**Recommended: the rule plus the button.** With AI off there is no button.

**D51 (07-D2). Which links does Air Traffic Control route?** Links from other
apps, or every link.
**Recommended: links from other apps only.**

**D52 (07-D5). How much bangs work?** An editor page, or the editor plus an
address-bar rework.
**Recommended: the editor now.** The rework gets its own go or no-go after the
sync.

**D53 (07-D6). Chrome Web Store themes or space colors?** The store theme
wins with a notice, or space colors always win.
**Recommended: the store theme wins, with a notice in the space editor.**

Links for this group: [07](07-power-features.md#what-you-need-to-decide).

## C. Can wait

**D54 (07-D1). What can a Boost do?** (VISION) Looks plus a CSS editor, or
JavaScript too.
**Recommended: looks only.** VISION.md's "CSS and JavaScript" line changes to
match.

**D55 (04-D8). Sync between devices?** (VISION) None, an export file, encrypted
folder sync, or Helium's vault.
**Recommended: an export file after launch.** Folder sync comes only if you
change VISION.md.

**D56 (05-D4). May outside agents run JavaScript in pages, as in ego(lite)?**
Never, step lists only, or JavaScript only in no-login agent tabs.
**Recommended: step lists now.** No-login JavaScript stays a later option.

**D57 (05-D8). Use Pomerado for repeat tasks?** Embed it, build native
recipes later, or neither.
**Recommended: don't embed it. Build native recipes after the evals pass.**
[05 later](05-agents-and-ai.md#later-no-milestone-yet)

**D58 (06-D12). Move rac's own source files out of patches into a plain
folder?** Yes after launch, or no.
**Recommended: yes, after launch.** It runs in a quiet week with no open PRs,
before plan 03's hunk thinning (03 M4). Ship does it after a spike on copying
versus linking.
[06](06-engineering-and-shipping.md#source-overlay-for-06-d12-i1-i2)

**D59 (M-6). Do routines ever run while rac is closed?** Not planned, so use
cron or launchd with `rac run` while rac is running, or a helper process
later.
**Recommended: not planned, and no helper (D21).** Plan 05 owns this.

## Changes to VISION.md and AGENTS.md (your sign-off)

These recommendations change VISION.md:

1. D12b adds the separate promise for the outside-agent door.
2. D13 makes Cmd+T open the command bar by default. Today it is a choice.
3. D14 builds Peek, which VISION.md lists as "not planned".
4. D39 adds opt-in auto-archive, which VISION.md lists as "not planned".
5. D54 makes Boosts "restyle a site's look", not "CSS and JavaScript".
6. D55 changes VISION.md only if you choose folder sync.
7. D46 lets spaces have separate sign-ins after launch, not only profiles.
8. D60 softens "never slower than Helium" on the site if speed numbers aren't
   ready. The site also fixes "thin layer", "It asks before it acts", and
   "four weeks".

These change AGENTS.md:

1. D9b and D9c let threads open PRs and drive rac through the test tools
   without asking each time.
2. D10 protects `main`, adds `rac-bot`, and adds a PR-flow section.
3. D6 gives standing approval for the five named builds, and no `he reset`
   before launch.
4. D63 routes every build through `devutils/rac/build-queue.sh`, in place of
   a bare `he build`.
5. D61 and D62 change "The main checkout is the base". After the sync, new
   worktrees clone the 156 base, and the Pro may host worktrees.
6. D58 moves rac-owned source out of patches. This rewrites "All of rac's
   changes live in its own patches", the "Where changes go" table, and the
   quilt workflow.
7. D12a adds the door checks to the "AI off" item in "Cover every surface".
8. D31 takes Opt+Cmd+N from Helium's split view.
9. Some plans edit files Helium also edits, which bends "Cheap to update".
   These are plan 02 M4, plan 05 M2 (6 to 12 hunks), plan 04's Keychain and
   partition hooks, and plan 07 M5's omnibox. All count against D17's budget.

Other docs change too. D15 rewrites `docs/roadmap.md`. D27 changes `ai.md`'s
"a run is one prompt". D24 to D26 change the roadmap's "rac's MCP serves only
the agent it launched".

## Money

| Item | Cost | Decision |
| --- | --- | --- |
| Depot runners | $0 if sponsored (you ask later). Paid only on D4's trigger and with your word: about $20 a month for the plan, about $35 per warm arm64 build and maybe $70 cold. About $150 a month at two builds before launch and one a week after, capped at $300 | D4, D64 |
| Intel builds | About $99 per two-architecture build on Depot | D7 |
| Free GitHub runners | $0, about 30 to 40 hours a build, and it has never finished. The chosen first route | D4 |
| Tier 2 agent evals before each release | Your API keys. 30 to 50 pages, 4 models, 2 modes, 3 runs. Likely tens to a few hundred dollars a release (estimate) | 05 M0, M2 |
| ego(lite) benchmark | Your API keys. 31 tasks, 3 runs. About $150 per model per pass at ego's claimed $1.64 a task (estimate) | 05 M2 |
| Larger GitHub runners | Rejected. They need a paid organization, which moves the update feed path | 06 |

## Anything that touches your real data

- **D41, your Arc folder.** You run `devutils/rac/arc_scrub.py` yourself.
  Agents never read the original. Check the scrubbed output before it's
  committed.
- **A real Arc install (04 M2).** "Arc Safe Storage" is one Keychain item
  shared by every Arc profile, so a throwaway Arc profile doesn't protect your
  real cookies. Agents test only on fixture `Cookies` databases with a fixed
  test password. You run real-Arc checks by hand on a second macOS user, with
  test accounts.
- **The password spike (D45).** It uses a synthetic `Login Data` file only.
- **Default browser (D38, 07 M3).** Changing it edits a system setting and
  shows a macOS dialog. You run these checks by hand on a second macOS user.
  Agents use the harness's `open-urls URL` instead.
- **Agent configs (03 M0, 05 M1).** `claude mcp add` and "Write it for me"
  edit your real `~/.claude.json` and Codex config. Agents use a throwaway
  `HOME` or a project-scoped config.
- **Eval logins (05 M2).** The ego(lite) benchmark needs logins. It uses test
  accounts only.
- **Local signing (06, emergency path only).** The signing keys and the
  Sparkle key would sit on a Mac next to your real profile.
- **Bench (06 M4).** The release-gate run needs an idle real Mac, so it runs
  at night when the queue is empty. It uses throwaway profiles.
- **Your MacBook Pro (D61).** Builds and runs there sit next to your daily
  data. Agents use throwaway profiles only, never `open` rac.app, and never
  take the foreground. They SSH there only because D61 asks for it, and only
  once it is back online.

## Open questions

None of these blocks the start.

- Is the little window called "Little rac" or "little window"? [01](01-ui-shell.md#open-questions)
- Should the top bar stay the default layout over the sidebar URL? [01](01-ui-shell.md#open-questions)
- Do pinned folders ever nest, or does Arc's nesting stay flattened? [01](01-ui-shell.md#open-questions)
- Do space dots show the space name on hover, as Nook does? [01](01-ui-shell.md#open-questions)
- Do color values that cite Dia's asset catalogs get replaced before any public design-system doc? [02](02-visual-design-and-motion.md#open-questions)
- Does a client with no token get a "pair this agent?" card, or only a refusal? Plan 05 decides. [03](03-core-architecture.md#open-questions)
- Is a 1 MiB frame cap right for large snapshots? [03](03-core-architecture.md#open-questions)
- Does the warm agent start when the panel opens, or after the first message? [03](03-core-architecture.md#open-questions)
- Will Helium's vault sync carry `rac.*` prefs? This affects plan 04. [03](03-core-architecture.md#open-questions)
- Does Anthropic's rule on third-party use of Claude credentials touch the ACP adapter path? [03](03-core-architecture.md#open-questions)
- Should imported cookies skip known tracker domains? [04](04-data-storage-import-sync.md#open-questions)
- Does Arc's `profile` field give readable names, or only ids? [04](04-data-storage-import-sync.md#open-questions)
- Is 7 days the right Undo window for imports? [04](04-data-storage-import-sync.md#open-questions)
- Should plan 01 add a quick profile hop in the space switcher? [04](04-data-storage-import-sync.md#open-questions)
- Should a later tool merge an imported profile into one window as spaces? [04](04-data-storage-import-sync.md#open-questions)
- Should the sync key ever live in iCloud Keychain? That needs a team ID, and `MAC_TEAM_ID` is empty today. [04](04-data-storage-import-sync.md#open-questions)
- Should Enter in a search box in a no-login agent tab still ask? [05](05-agents-and-ai.md#open-questions)
- Should the built-in assistant get a read-only level? [05](05-agents-and-ai.md#open-questions)
- Should a shared tab return to you when the agent's session ends? [05](05-agents-and-ai.md#open-questions)
- Does a data-flow grant last for the session or until revoked? [05](05-agents-and-ai.md#open-questions)
- Will Depot offer open-source terms when you ask, and what does a cold rac build cost? [06](06-engineering-and-shipping.md#open-questions)
- Does an official build tree compile the five test targets cheaply? [06](06-engineering-and-shipping.md#open-questions)
- Does a signed first launch ask for update consent, and does Keychain prompt across an update? [06](06-engineering-and-shipping.md#open-questions)
- Is 5% the right speed tolerance against Helium, or 0% for typing and tab switching? [06](06-engineering-and-shipping.md#open-questions)
- Does the site-search page already list all 13,421 bang triggers? [07](07-power-features.md#open-questions)
- Does Violentmonkey run in rac, and does Tampermonkey need a toggle? [07](07-power-features.md#open-questions)
- Do the 1Password and Bitwarden desktop apps connect to rac? [07](07-power-features.md#open-questions)
- Can Arc's local Boosts be read at all? Plan 04's spike decides. [07](07-power-features.md#open-questions)
- Should Boosts and routes become per space once sign-ins separate? [07](07-power-features.md#open-questions)
- Who owns the localhost developer bar, AppleScript for spaces, and new tabs that clear themselves when abandoned? Nobody yet. [07](07-power-features.md#open-questions)
