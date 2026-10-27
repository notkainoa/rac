# Decisions

Every open decision across the seven plans, in one list. Each item is one
question, with short options and a recommended answer. The plan's own id is
kept (for example 03-D2). Ids that start with **M-** are new here: they come
from fitting the plans together.

Answer group A first: it is everything the threads need in week 1. Nothing
launches until group A is answered and the plans are approved (see
[00-master-plan.md](00-master-plan.md)). "Ruling N" means item N in
[rulings.md](rulings.md).

Threads named below: **Ship** (plan 06), **UI** (plans 01 and 02), **Core**
(plans 03 and 05), **Data** (plan 04), **Power** (plan 07). Weeks are "W1 =
the first week after approval", from plan 06.

Totals: 60 decisions (D1 to D60; D9 and D12 each have parts). Group A: 16.
Group B: 38. Group C: 6. 15 conflicts. Numbers are stable: moving a decision
between groups never renumbers it.

## A. Needed in week 1

**D1 · M-1 · By when do you approve the plans?**
By Mon 11-02 / by Mon 11-09 / later.
**Recommended: by 11-02.** That gives one spare week before the 12-15 hard
stop. 11-09 leaves none. Later means launching on Chromium 154 (D8).
[06 critical path](06-engineering-and-shipping.md#critical-path)

**D2 · 06-D5 · In what order does the work happen?**
(a) Ship 0.1, sync, launch, and only then start the revamp / (b) revamp first,
launch later / (c) a stable track ships 0.1, the sync, and the launch while the
revamp is built on branches in rac-owned files and merged after the sync.
**Recommended: (c).** It is plan 06's C1 plus ruling 1, made explicit.
[06 sequencing](06-engineering-and-shipping.md#sequencing-c1-to-c3)

**D4 · 06-D2 · How are releases built, and for how much?** (money)
Depot paid runners / free GitHub runners / a local Mac.
**Recommended: Depot with a $300 monthly cap, plus one free attempt in W1.**
You create the account on day 1 (about an hour). Keys stay on GitHub's own
runners in every option: Depot only compiles. Signing, notarizing, and the
appcast run in a final job on a GitHub-hosted runner, not on Depot. The
engineering matrix preferred a local build first; plan 06 rejects that because
the signing keys would leave GitHub and the build would fight the sync for the
same Mac.
[06 build route](06-engineering-and-shipping.md#build-route-a1-to-a3)

**D5 · 06-D1 · What are the MacBook Pro's RAM and free disk?**
Please supply both. (Or say yes and an agent reads them:
`ssh knewton@kainoas-macbook-pro 'sysctl -n hw.memsize; df -h ~'`.) They
decide which Mac runs the sync and holds the Chromium 156 base: the Pro, with
feature worktrees moving there after W4 / the Air does everything / the Pro
syncs, then the Air rebuilds its own base.
**Rule: at least 32 GB of RAM and 150 GB free means the Pro syncs and holds
the 156 base. Otherwise the Air.** For reference, the Air is an M1 with 8
cores, 16 GB, and 101 GB free (re-checked 2026-10-27). The Pro is also your
main machine, so long builds will slow it.
**CONFLICT (C11):** in W1 to W3, plans 01, 02, 03, 04 and 05 together want
five or more worktree builds, but the Air allows at most two incremental
builds at once, and none during a full build. *Resolution:* the build-slot
rule in the master plan. Launch-gate work gets slots first. Plan 02 M2 and M3
and plan 03 M1 write code and wait for a free slot.
[06](06-engineering-and-shipping.md#what-you-need-to-decide)

**D6 · M-2 · Do you approve the full builds now?**
(a) The W1 cold 156 build, the base-tree rebuild with `he reset` in W3 to W4,
and one rebuild per later sync / (b) the W1 cold build only. After the sync
merges, new and rebased worktrees run `worktree.sh setup <sync worktree>`,
which clones the sync worktree's built 156 tree, and the main checkout's
rebuild moves to a quiet night or waits for the next sync / (c) ask each time.
**Recommended: (b), if Ship's W3 check of the clone path on a throwaway
worktree passes. If it fails, (a)'s rebuild is approved too.** AGENTS.md
requires your approval for these. Any other full build still asks. This also
covers the one incremental `he build` in your main checkout after its
fast-forward (master plan, step 0).
[06 M2](06-engineering-and-shipping.md#m2-sync-to-helium-02011--chromium-156-w1-w3-slack-to-w4)

**D9a · M-3 · Which threads launch?**
Four now (Ship, UI, Core, Data) and Power after launch / three (Data folded
into Core) / all five now.
**Recommended: four now, Power after launch.**
[Master: thread map](00-master-plan.md#thread-map)

**D9b · M-3 · May threads open PRs without asking? (You still approve every merge.)**
Yes / ask for each PR.
**Recommended: yes.** AGENTS.md says "never open a PR unless asked", so this
needs your sign-off. It does not cover merging: Ship asks you to merge PR #20,
and asks before deleting `pullfrog.yml`.

**D9c · M-3 · May threads drive rac through the harness, bench, and eval runner on throwaway profiles?**
Yes, with no other automation, and never a real profile / ask each time.
**Recommended: yes.** AGENTS.md says "ask before driving the browser with
automation", so this needs your sign-off.

**D11 · 06 defaults · Accept plan 06's "I'll do these unless you object" list?**
One jump to Helium 0.20.1.1; a sync freeze; C++ tests run in worktrees first;
no Chromium 157 before launch; beta channel and crash reports after launch;
publish speed numbers against Helium (D60 covers what happens if they aren't
ready).
**Recommended: accept all.**
**CONFLICT (C10):** plan 06 lets new rac-owned files merge during the freeze.
Plan 04 says nothing merges, and dates the sync to weeks 1 to 2 instead of
W1 to W3. *Resolution:* nothing under `patches/` merges until the sync
merges, because every new patch also edits `patches/series`, the one file the
sync conflicts on. Docs, the site, CI, and plans may merge. Plan 06's weeks
win.
[06](06-engineering-and-shipping.md#what-you-need-to-decide)

**D14 · 01-D4 · Build Peek, and does it enter history?** (VISION)
Yes, history only once expanded / yes, always in history / no.
**Recommended: yes, history only once expanded.** VISION.md lists Peek as
"not planned". Needed in W1, because a "no" cancels a 2 to 3 day spike.
[01](01-ui-shell.md#what-you-need-to-decide)

**D16 · M-5 · Is the command bar in the launch build?**
A launch gate / ships in the launch if merged by the start of W5, otherwise as
a point release in W6 / January.
**Recommended: not a gate. Launch if merged by the start of W5. Otherwise a W6
point release before 12-22, only if `update-smoke` passes.**
**CONFLICT (C8):** the merge cutoff differs. Plan 06 says the start of W5.
Plans 01 and 02 say about a week before 12-15, and plan 02 adds "sync by
12-01". *Resolution:* one rule, from plan 06: launch merges close at the start
of W5.
**CONFLICT (C9):** plan 01 promises the command bar "as an update before
12-22", but plan 06's calendar has no release slot after launch, only float.
*Resolution:* plan 06 holds one optional point release in W6.
[01 M2](01-ui-shell.md#milestones), [06 gates](06-engineering-and-shipping.md#critical-path)

**D17 · 03-D5 · Which patch-surface number do we hold?** Net-diff hunks plus
first failures per sync / raw stacked hunks.
**Recommended: net-diff hunks plus first failures per sync.** Until Ship's
counter reports a net-diff baseline in W1, hold stacked hunks at 630 or fewer,
aiming for 550. Needed: Ship M0 builds the counter in W1. Every plan's new hunks count
against this budget.
[03](03-core-architecture.md#how-to-shrink-the-patch-surface-03-d4-03-d5)

**D19 · 05-D1 · How do we close the `auto` hole?** Taint rule (once a second
site was read, ask before acting on each site) / make `careful` the default /
both.
**Recommended: the taint rule; keep `auto` the default.** Needed: Core M0, W1.
[05](05-agents-and-ai.md#what-you-need-to-decide)

**D20 · 05-D6 · Chromium's own debugging doors?** Refuse them on the real
profile, no new setting / leave them / add an expert switch.
**Recommended: refuse, no new setting.** Dev runs use `--user-data-dir`, so
the DevTools-port screenshot flow keeps working. Needed: Core M0 (launch gate).
**CONFLICT (C5):** plans 03, 06 and 07 call this 05-D9. Plan 05
says plan 03 M1 builds it, but plan 03 M1 doesn't list it. *Resolution:* the
id is 05-D6. The Core thread builds it inside 05 M0, on 156 after the sync.
[05](05-agents-and-ai.md#what-you-need-to-decide)

**D21 · 03-D1 · Does rac run a separate local server or helper?** No, the
browser is the server / Rust helper / Node sidecar.
**Recommended: no.** No Swift helper either; local models stay Ollama and LM
Studio. Needed: before 03 M1, W2.
[03](03-core-architecture.md#where-the-backend-runs-03-d1)

**D22 · 03-D4 · How do we shrink rac's Chromium edits?** Stay on Views and
thin the hooks / a native AppKit shell now.
**Recommended: Views. Spike a native shell only if 03-D5's target is missed
after the second sync.** Needed: W1, because UI's plan assumes Views. Plan 01
calls this "03-D7".
[03](03-core-architecture.md#what-you-need-to-decide)

**D41 · 04-D4 · What real Arc data can we test on?** You run a scrubbing
script on your own Arc / volunteer samples after beta / synthetic only.
**Recommended: the scrubbing script now, volunteers after beta.** Needed: W1.
It touches your real data (see below).
[04](04-data-storage-import-sync.md#what-you-need-to-decide)

**D42 · 04-D5 · How big is the safety net before launch?** Pre-import
snapshot, one rolling backup, and the Keychain fix / full 14-day rotation and a
Restore UI now.
**Recommended: the minimal set now, the rest after launch.** Needed: 04 M0, W1.
[04](04-data-storage-import-sync.md#what-you-need-to-decide)

## B. Needed later, by thread

### Ship (plan 06)

**D3 · 06-D4 · Publish a quiet 0.1.0 on Chromium 154 first?**
Yes, labeled "Preview" / no, wait for the synced build.
**Recommended: yes.** It proves signing now, and 0.1.0 to 0.2.0 proves updates.
Needed by: W2, before the 0.1.0 smoke test.
[06](06-engineering-and-shipping.md#what-you-need-to-decide)

**D7 · 06-D3 · Support Intel Macs at launch?** (money)
Yes, about $99 a build on Depot / no.
**Recommended: no, Apple Silicon only for 0.x.** Needed by: W3, before the
release workflow is finalized.
[06](06-engineering-and-shipping.md#intel-b1-b2)

**D8 · 06-D6 · What if the sync isn't merged by the end of W4?**
Launch on 154 as a labeled preview / hold the launch / hold one week, then 154.
**Recommended: hold one week, then launch on 154.** The 154 fallback must
start by 12-15.
[06](06-engineering-and-shipping.md#what-you-need-to-decide)

**D10 · 06 default · Protect `main` and add a `rac-bot` machine user?**
Yes: PRs required, Linux checks plus your approval, agents push as `rac-bot`,
commits still authored by Kainoa Newton / no.
**Recommended: yes, in W2 to W5.** Needed by: W2. It adds a short PR-flow section to AGENTS.md.
[06 M4](06-engineering-and-shipping.md#m4-checks-protection-and-evidence-w2-w5)

**D18 · 06-D7 · Sync cadence after launch?** Every Chromium major within 14
days / every other major. Security fixes in 7 days if exploited, else 14.
**Recommended: every major. Review after three cycles.** Needed by: W6, before
the first cadence sync.
[06](06-engineering-and-shipping.md#cadence-e1-e2)

**D60 · 06 default · If speed numbers against Helium aren't ready, soften "never slower" on the site?** (VISION)
Yes, soften the site line until the numbers are published / no, keep the line
and delay the site.
**Recommended: yes.** It is launch gate G11. Needed by: W4, before the launch
site copy is final. This is the one item split out of D11.
[06 M4](06-engineering-and-shipping.md#what-you-need-to-decide)

### UI (plans 01 and 02)

**D13 · 01-D1 · Does Cmd+T open the command bar?** (VISION)
Yes, plus one setting to get the new tab page back / yes, no setting / no.
**Recommended: yes, plus one setting.** VISION.md makes the command bar a
choice today. Needed by: 01 M2, W2.
[01](01-ui-shell.md#what-you-need-to-decide)

**D15 · M-4 · Move the command bar and the little window ahead of `docs/roadmap.md`?**
Yes, and rewrite the roadmap after approval / no, keep the roadmap order.
**Recommended: yes.** The roadmap puts the command bar in phase 5 and Little
Arc in "Later". Needed by: W4, before the roadmap is rewritten.
[01 fit](01-ui-shell.md#fit-with-the-non-negotiables)

**D28 · 01-D2 · What do Cmd+L and a click on the address bar do?** Both open
the command bar / Cmd+L opens it, a click edits in place / both edit in place.
**Recommended: Cmd+L opens it; a click edits in place.** Needed: 01 M2, W1.
[01](01-ui-shell.md#what-you-need-to-decide)

**D29 · 01-D3 · When do command bar queries reach the search engine?** Same
as the address bar / only after local results run out and typing pauses /
never.
**Recommended: only after local results run out and typing pauses.** Needed:
01 M2.
[01](01-ui-shell.md#what-you-need-to-decide)

**D30 · 01-D8 · Move Ask from the AI new tab page into the command bar?** Yes,
retire the AI new tab page / keep both.
**Recommended: yes.** One fewer AI surface. Needed: 01 M2.
[01](01-ui-shell.md#what-you-need-to-decide)

**D31 · 01-D6 + 07-D7 · Whose keyboard shortcuts?** Chrome's for standard
actions and Arc's for rac's own, with Cmd+O only inside Peek and the little
window / Arc's everywhere / new keys that clash with nothing.
**Recommended: Chrome's for standard actions, Arc's for rac's own, Cmd+O
scoped.** Taking Opt+Cmd+N moves Helium's split-view shortcut, so it needs
your OK under AGENTS.md. Needed: 01 M2.
[01](01-ui-shell.md#notes-on-each-decision), [07](07-power-features.md#what-you-need-to-decide)

**D32 · 02-D2 · Glass or solid?** Solid, as today / blur behind the window by
default.
**Recommended: solid.** Needed: 02 M2, W2.
[02](02-visual-design-and-motion.md#what-you-need-to-decide)

**D33 · 02-D3 · Space themes?** Eight presets / presets plus custom colors / a
full gradient editor.
**Recommended: presets plus custom colors.** It also fixes dark mode for
imported Arc spaces. Needed: 02 M3, W2.
[02](02-visual-design-and-motion.md#space-themes)

**D34 · 02-D4 · Do buttons shrink when pressed?** Never / favorites tiles only
/ every icon button.
**Recommended: never.** Needed: 02 M2.
[02](02-visual-design-and-motion.md#what-you-need-to-decide)

**D35 · 02-D5 · Do keyboard shortcuts animate?** Spatial changes only / never.
**Recommended: spatial changes only.** Needed: 02 M2.
[02](02-visual-design-and-motion.md#what-you-need-to-decide)

**D36 · 02-D6 · Page card corner?** (a) Concentric with the window: 11 px on
macOS 26 (17 px minus the 6 px inset), 10 px on older macOS / (b) Dia's 10 px
everywhere.
**Recommended: (a).** Needed: 02 M2.
[02](02-visual-design-and-motion.md#what-you-need-to-decide)

**D37 · 02-D7 · Under Reduce Motion, does a swipe follow your fingers?** No /
yes, then a fade on release.
**Recommended: yes.** Needed: 02 M2.
[02](02-visual-design-and-motion.md#what-you-need-to-decide)

**D38 · 01-D5 · Do links from other apps open in a little window?** Yes by
default / opt-in / not built.
**Recommended: yes by default, in the last-used space, keeping nothing when
closed.** Needed: 01 M3, after the sync. Testing it touches your real data
(see below).
[01](01-ui-shell.md#what-you-need-to-decide)

**D39 · 01-D7 · How does clean-up work?** (VISION, for auto-archive) Manual
Clear only / Clear now, opt-in auto-archive later / auto-archive on.
**Recommended: Clear now with Undo; opt-in auto-archive later, off by default,
keeping an imported Arc user's own setting.** Needed: 01 M3.
**CONFLICT (C7):** plan 01's MayClear rule spares tabs "holding unsent form
text". Plan 07 says Chromium keeps no general dirty-form flag, so drop it, and
spare tabs with downloads in progress. *Resolution:* plan 01 owns the rule and
takes plan 07's fix: spare downloads, and spare only pages that registered
`beforeunload`.
[01 Clear](01-ui-shell.md#clear-and-archive-owned-here-ruling-4)

**D40 · 02-D1 · How springy is Cmd+S?** Dia's spring (about 3.4 px of bounce)
/ calmer (1.2 px) / none.
**Recommended: calmer, confirmed by a side-by-side video.** Needed: 02 M4,
after the sync.
[02](02-visual-design-and-motion.md#what-you-need-to-decide)

### Core (plans 03 and 05)

**D12a · 03-D6 = 05-D7 · Does the outside-agent door work with rac's AI off?**
Yes / no.
**Recommended: yes.** Keep "AI off costs nothing" as written: the door has
its own switch, off by default, and nothing listens while it's off. Needed by:
the door milestone, after launch; decide with the plans.
**CONFLICT (C13):** plan 03 says 05-D2 decides whether the door works with AI
off. 05-D2 doesn't ask it, though plan 05's text assumes yes. *Resolution:*
decide it here.
[03](03-core-architecture.md#what-you-need-to-decide),
[05 fit](05-agents-and-ai.md#fit-with-the-non-negotiables)

**D12b · 03-D6 = 05-D7 · Add the separate outside-agent promise to VISION.md?** (VISION)
Add a scoped promise: its own switch, off by default, nothing listens while
it's off, and "Outside agents: on" shows next to the AI switch / reword the AI
rule instead.
**Recommended: add the scoped promise.** Plan 05 has draft text. Needed by:
the door milestone, after launch.
[05 fit](05-agents-and-ai.md#fit-with-the-non-negotiables)

**D23 · 05-D3 · What is an agent's workspace?** An Agents section in the
sidebar / its own space / an off-screen window.
**Recommended: the Agents section. The off-screen window is the fallback if
the rendering spike fails.** Needed: in principle by W2, when UI designs the
rows. Final after plan 05's spike.
**CONFLICT (C1):** plan 01 draws agent work as an agent *space* (a space dot,
M5 "agent space dot") and cites "05-D5". Plan 05 recommends a sidebar
*section* and cites a plan 01 decision "01-D9" that doesn't exist. Ruling 5
lets plan 05 decide. *Resolution:* adopt the Agents section. Plan 01 updates
its window tree and M5 to "one group per client, shown only while it has
tabs", with no space dot.
[05](05-agents-and-ai.md#what-you-need-to-decide), [01 M5](01-ui-shell.md#milestones)

**D24 · 03-D2 · How do outside agents connect?** Per-profile socket, signed
relay, per-client tokens / loopback HTTP with OAuth.
**Recommended: socket, relay, and tokens. Add HTTP only if 03 M0's spike shows
a client needs it.** Needed: before the door milestone, after launch.
[03](03-core-architecture.md#how-outside-agents-connect-03-d2)

**D25 · 05-D5 · Which doors?** MCP / a `rac` CLI with a skill / both.
**Recommended: both, from one relay; MCP first.** Needed: with D24.
[05](05-agents-and-ai.md#what-you-need-to-decide)

**D26 · 05-D2 · What does a newly connected outside agent get?** Read the tabs
you share / act in its own no-login tabs / act in your tabs at your level.
**Recommended: read the shared tabs. You can raise it to act in its own tabs.**
Needed: before the door milestone.
**CONFLICT (C2):** plan 05 M1 (read-only door) is set for weeks 4 to 7, before
launch. It needs plan 03's door, which plan 03 schedules after launch and gates
on 05 M0's evals. Plan 05 also swaps plan 03's milestone numbers (it calls the
door "03 M3" and the split "03 M2"; they are M2 and M1). *Resolution:* the
door is one milestone, 03 M2 plus 05 M1, after launch (W7 or later), built on
a branch from W4 if a slot is free. 03 M1's split may still land before
launch.
[05 M1](05-agents-and-ai.md#m1-read-only-door-after-launch-w7-or-later-chromium-156-not-a-launch-gate),
[03 M2](03-core-architecture.md#m2-the-outside-agent-door-after-launch-chromium-156-9-to-13-agent-days)

**D27 · 03-D3 · Keep rac's own agent warm between messages?** Restart every
message / one warm agent per profile, 5-minute idle cap.
**Recommended: warm, one per profile, 5-minute cap.** It changes `ai.md`'s
"a run is one prompt". Needed: before 03 M3, after launch.
[03](03-core-architecture.md#what-you-need-to-decide)

### Data (plan 04)

**D43 · 04-D1 · What does the pre-launch import bring?** Sidebar only /
sidebar plus sign-ins / plus passwords.
**Recommended: sidebar plus sign-ins, from Arc only. If sign-ins slip, launch
with the sidebar.** If approval comes after 11-02, plan sidebar only.
Needed: 04 M2, W4.
[04](04-data-storage-import-sync.md#what-you-need-to-decide)

**D44 · 04-D2 · How do Arc profiles map?** Everything into one profile / Arc
profile to rac profile, Arc space to rac space / per-space sign-ins in one
window.
**Recommended: Arc profile to rac profile.** It's the cheapest correct path
before 12-22 (ruling 14). Users with two Arc profiles get two windows.
Needed: 04 M2.
[04 options](04-data-storage-import-sync.md#options)

**D45 · 04-D3 · How do saved passwords move?** (a) A plaintext CSV on a RAM
disk, never on the SSD. Any app you run can read it until it unmounts / (b)
guide Arc's own export / (c) a plaintext temp file on the SSD / (d) turn on
Chromium's password manager.
**Recommended: (a) if the one-day spike passes, else (b).** Both briefly
create a plaintext file; (a) never touches the SSD. (c) needs your sign-off.
Needed: 04 M2.
[04 M2](04-data-storage-import-sync.md#m2-arc-profiles-and-sign-ins-m-6-8-agent-days)

**D46 · 04-D6 · After launch, how are separate sign-ins in one window built?**
A storage partition per space / a full profile per space.
**Recommended: a partition per space, spike first.** (VISION: spaces would
then keep logins apart too.)
**CONFLICT (C3):** plan 05 M2's write tier for outside agents waits for
plan 04's in-memory "no-login" partition. Plan 05 calls it "04 M4, late
January". Plan 04 has no M4 and no date. It lists partitions as after-launch
item 2 and names plan 05 *M3*, not M2, as the user. *Resolution:* plan 04
schedules, right after launch, the partition spike plus the in-memory variant
first, ahead of the per-space toggle. Plan 05 M2 builds agent tabs for the
built-in agent and "use my logins" first. It turns on the outside write tier
when the in-memory partition lands. Both touch `browser_navigator.cc` and
session restore, so Data and Core take turns there.
[04 after launch](04-data-storage-import-sync.md#after-the-launch),
[05 M2](05-agents-and-ai.md#m2-agent-workspace-and-the-write-tier-weeks-815-chromium-156)

**D47 · 04-D7 · After launch, how are AI chats and agent runs stored?**
Encrypt today's JSON / one encrypted SQLite store with retention.
**Recommended: encrypted SQLite.** It absorbs plan 05's chat-encryption item.
[04](04-data-storage-import-sync.md#what-you-need-to-decide)

### Power (plan 07, after launch)

**D48 · 07-D8 · In what order?** By Arc-refugee demand (Boosts, routing,
bangs) / by the roadmap (bangs first).
**Recommended: by demand.**
[07](07-power-features.md#what-you-need-to-decide)

**D49 · 07-D3 · Where does clean-link copy apply?** Shift+Cmd+C and the tab
menu / also the page's "Copy link address".
**Recommended: Shift+Cmd+C and the tab menu only. No setting.**
[07](07-power-features.md#what-you-need-to-decide)

**D50 · 07-D4 · How are tab groups named?** A simple rule / the rule plus a
"Name with AI" button when AI is on.
**Recommended: the rule plus the button.** With AI off there is no button.
[07](07-power-features.md#what-you-need-to-decide)

**D51 · 07-D2 · Which links does Air Traffic Control route?** Links from other
apps / every link.
**Recommended: links from other apps only.**
[07](07-power-features.md#what-you-need-to-decide)

**D52 · 07-D5 · How much bangs work?** An editor page / editor plus an
address-bar rework.
**Recommended: the editor now; the rework gets its own go or no-go after the
sync.**
[07](07-power-features.md#what-you-need-to-decide)

**D53 · 07-D6 · Chrome Web Store themes versus space colors?** The store theme
wins, with a notice / space colors always win.
**Recommended: the store theme wins, with a notice in the space editor.**
[07](07-power-features.md#what-you-need-to-decide)

## C. Can wait

**D54 · 07-D1 · What can a Boost do?** (VISION) Looks plus a CSS editor / also
JavaScript.
**Recommended: looks only.** VISION.md's "CSS and JavaScript" line changes to
match.
[07](07-power-features.md#what-you-need-to-decide)

**D55 · 04-D8 · Sync?** (VISION) None / an export file / encrypted folder
sync / Helium's vault.
**Recommended: an export file after launch. Folder sync only if you change
VISION.md.**
[04](04-data-storage-import-sync.md#what-you-need-to-decide)

**D56 · 05-D4 · May outside agents run JavaScript in pages, as in ego?** Never
/ step lists only / JavaScript only in no-login agent tabs.
**Recommended: step lists now; no-login JavaScript is a later option.**
[05](05-agents-and-ai.md#what-you-need-to-decide)

**D57 · 05-D8 · Pomerado for repeat tasks?** Embed it / build native recipes
later / neither.
**Recommended: don't embed it; build native recipes after the evals pass.**
[05 later](05-agents-and-ai.md#later-no-milestone-yet)

**D58 · 06-D12 · Move rac's own source files out of patches into a plain folder?**
Yes, after launch / no.
**Recommended: yes, after launch, in a quiet week with no open PRs, and before
plan 03's hunk thinning (03 M4).**
**CONFLICT (C4):** plan 06 says "plan 03 M7 implements it". Plan 03 has no M7
and says plan 06 owns the move. Plan 02 cites "03-D8", which doesn't exist.
*Resolution:* one decision, 06-D12. The Ship thread implements it after a
throwaway-worktree spike on copy versus link.
[06](06-engineering-and-shipping.md#source-overlay-for-06-d12-i1-i2)

**D59 · M-6 · Do routines ever run while rac is closed?** Not planned; use
cron or launchd with `rac run` while rac is running / a helper process later.
**Recommended: not planned. No helper (D21).**
**CONFLICT (C6):** plan 03 points to "05-D11", plan 07 to "05-D10, 05-D11",
and plan 05 to "03-D4", which is the shell decision. No plan owns it.
*Resolution:* plan 05 owns it, and this is the answer for now.
[05 later](05-agents-and-ai.md#later-no-milestone-yet)

## Other conflicts (no decision of their own)

- **C12. Two harness builders.** Plan 01 M0 and plan 02 M0 both add a
  frame-timing method and a frames-to-video tool in `patches/rac/dev/`.
  *Resolution:* plan 02 M0 builds the frame log and the video tool. Plan 01 M0
  adds the window, profile, and incognito capture verbs. Both happen in one UI
  worktree, one after the other.
- **C14. The settings page's name.** Plans 01 and 03 say "Settings > Outside
  agents". Plan 05 says "Settings › Agents". *Resolution:* "Outside agents".
  With AI off, the bare word "Agents" could read as an AI label.
- **C15. The import gate.** Plan 01 calls its import screens (M1) a launch
  gate. Plan 06's gate table lists only plan 04 M1. *Resolution:* the Arc
  import gate includes plan 01's screens (master plan, gate G1).

## Broken cross-references to fix when the plans are edited

| Plan | Says | Should say |
| --- | --- | --- |
| 01 | 03-D7 (Views) | 03-D4 |
| 01, ruling 5 | 05-D5 (agent workspace) | 05-D3 |
| 01 | 04-D3 (separate sign-ins; profile mapping) | 04-D6; 04-D2 |
| 01 | 05-D2 (the door's own switch) | D12 here |
| 02 | 03-D8 (source move) | 06-D12 |
| 03, 06, 07 | 05-D9 (debug doors) | 05-D6 |
| 03, 04 | 06-D13 (freeze) | plan 06's default list (D11) |
| 03 | 06-D6 (cadence) | 06-D7 |
| 04 | 01-D10 (sign-ins toggle) | 04-D6, plan 01 screen 15 |
| 04 | 06-D9 (posted test status) | 06 M4 task 2 |
| 04 | 03 M5 (history schema); 06 M6 | plan 04 itself; 06 "Later" |
| 04 | sync in weeks 1 to 2 | W1 to W3, slack to W4 |
| 05 | 01-D9 (Agents section) | 05-D3, plan 01 M5 |
| 05 | 03-D4 (routines); 03-D5 and 03-D6 (transport) | D59; 03-D2 |
| 05 | 03 M3 (relay), 03 M2 (split) | 03 M2, 03 M1 |
| 05 | 04 M4 (ephemeral identity) | 04 after-launch item 2 (D46) |
| 05 | plan 06 F1 statuses | 06 M4 task 2 |
| 06 | 04 M0 task 5 (Keychain) | 04 M0 task 3 (M0b) |
| 06 | 05 M0 task 7 (dev switches) | 05 M0 task 6 |
| 06 | 01-D12 (command bar) | D16 here |
| 07 | 01-D6 (Clear) | 01-D7 |
| 07 | 05-D10, 05-D11 (routines, recipes) | D59, 05-D8 |
| 07 | plan 01 M2 task 2 (router) | plan 01 M3 |
| 07 | plan 03 M2 (action table) | plan 03 M1 |

## Items that bend VISION.md or AGENTS.md (your sign-off)

**VISION.md**

1. D12b: add the separate promise for the outside-agent door.
2. D13: Cmd+T opens the command bar by default. Today VISION.md makes it a
   choice.
3. D14: Peek is listed as "not planned".
4. D39: auto-archive is listed as "not planned" (opt-in, off by default).
5. D54: Boosts become "restyle a site's look", not "CSS and JavaScript".
6. D55: sync is listed as "not planned". Only folder sync needs this.
7. D46: after launch, spaces can have separate sign-ins, not only profiles.
8. D60: if speed numbers aren't ready, the site softens "never slower than
   Helium". The site also fixes "thin layer", "It asks before it acts", and
   "four weeks" (06 M5, 05 M0).

**Other docs** (not VISION, but recorded decisions): D15 rewrites
`docs/roadmap.md`. D27 changes `ai.md`'s "a run is one prompt". D24 to D26
change the roadmap's "rac's MCP serves only the agent it launched".

**AGENTS.md**

1. D9b and D9c: threads open PRs without a per-PR ask, and drive rac through
   the harness, bench, and eval runner without asking each time.
2. D10: protected `main`, the `rac-bot` user, and a new PR-flow section.
3. D6: standing approval for the named full builds and `he reset`.
4. D58: rac-owned source leaves patches. This rewrites "All of rac's changes
   live in its own patches", the "Where changes go" table, and the quilt
   workflow.
5. D12a: the "AI off" item in "Cover every surface" gains the door checks.
6. D31: taking Opt+Cmd+N from Helium's split view needs an OK.
7. "Cheap to update" bends: hot-file hunks in plan 02 M4, plan 05 M2 (6 to 12),
   plan 04's Keychain and partition hooks, and plan 07 M5's omnibox. All of
   these are counted against D17's budget.

## Money

| Item | Cost | Decision |
| --- | --- | --- |
| Depot runners | about $20 a month plan; about $35 per warm arm64 build, maybe $70 cold; about $150 to $300 a month; $300 cap | D4 |
| Intel builds | about $99 per two-arch build on Depot | D7 |
| Free GitHub attempt | $0, about 30 to 40 hours, never finished yet | D4 |
| Tier 2 agent evals, before each release (plan 05) | your API keys; 30 to 50 pages, 4 models, 2 modes, 3 runs. Cost unknown; likely tens to a few hundred dollars a release (estimate) | 05 M0, M2 |
| ego benchmark harness (plan 05 M2) | your API keys; 31 tasks, 3 runs. At ego's claimed $1.64 a task, about $150 per model per pass (estimate) | 05 M2 |
| Larger GitHub runners | rejected: needs a paid organization, which moves the feed path | 06 |

## Anything that touches your real data

- **D41, your real Arc folder.** You run `devutils/rac/arc_scrub.py` yourself.
  Agents never read the original. Check the scrubbed output before it's
  committed.
- **Testing a real Arc install (04 M2).** "Arc Safe Storage" is one Keychain
  item per macOS user, shared by every Arc profile, so a throwaway Arc profile
  doesn't protect your real Arc cookies. Agents test the credential reader only
  on fixture `Cookies` databases encrypted with a fixed test password, through
  a test-only seam. The reader never calls the real Keychain in tests.
  Real-Arc checks happen on a second macOS user, run by you by hand, with test
  accounts on Google, GitHub, and a bank-style site, never your own.
- **The password spike (D45).** Use a synthetic `Login Data` file only.
- **Default browser (D38, 07 M3).** Changing the default browser edits a
  system setting and shows a macOS confirmation dialog. You run these checks
  by hand on a second macOS user. Agents use the harness verb (`open-urls
  URL`), which calls the same link router inside the worktree process.
- **Agent configs (03 M0, 05 M1).** `claude mcp add` and "Write it for me"
  edit your real `~/.claude.json` and Codex config. Use a throwaway `HOME` or a
  project-scoped config.
- **Eval logins (05 M2).** The ego harness needs "the same logins for every
  tool". Use test accounts only.
- **Local signing (06 A3, emergency path only).** Signing keys and the Sparkle
  private key would sit on a Mac next to your real profile.
- **Bench (06 M4).** The release-gate run needs an idle real Mac, so other
  agents must pause. It uses throwaway profiles.

## Open questions

Genuinely open questions from the plans that no decision above covers. None
blocks the start. Each is one line, with its plan.

- **Little window name**: "Little rac" or "little window"? [01](01-ui-shell.md#open-questions)
- **Top bar versus sidebar URL**: should the top bar stay the default layout? [01](01-ui-shell.md#open-questions)
- **Pinned folders**: do they ever nest, or does Arc's nesting stay flattened? [01](01-ui-shell.md#open-questions)
- **Space dots**: show the space name on hover, as Nook does? [01](01-ui-shell.md#open-questions)
- **Design values**: keep the color values that cite Dia's asset catalogs, or replace them before any public design-system doc? [02](02-visual-design-and-motion.md#open-questions)
- **Pairing card**: should a client with no token trigger a "pair this agent?" card, or only a refusal? Plan 05's call. [03](03-core-architecture.md#open-questions)
- **Frame cap**: is 1 MiB right for large snapshots? [03](03-core-architecture.md#open-questions)
- **Warm agent**: prewarm when the panel opens, or only after the first message? [03](03-core-architecture.md#open-questions)
- **Helium vault sync**: will it carry `rac.*` prefs? This affects plan 04. [03](03-core-architecture.md#open-questions)
- **Claude credentials**: does Anthropic's rule on third-party use touch the ACP adapter path? [03](03-core-architecture.md#open-questions)
- **Tracker cookies**: should imported cookies skip known tracker domains? [04](04-data-storage-import-sync.md#open-questions)
- **Arc profile names**: does Arc's `profile` field give readable names, or only ids? [04](04-data-storage-import-sync.md#open-questions)
- **Undo window**: is 7 days right? [04](04-data-storage-import-sync.md#open-questions)
- **Profile hop**: should plan 01 add a quick profile hop in the space switcher? [04](04-data-storage-import-sync.md#open-questions)
- **Merged profiles**: should a later tool merge an imported profile into one window as spaces? [04](04-data-storage-import-sync.md#open-questions)
- **Sync key**: should it ever live in iCloud Keychain? That needs a team ID, and `MAC_TEAM_ID` is empty today. [04](04-data-storage-import-sync.md#open-questions)
- **Search box in agent tabs**: should Enter in a search box in a no-login agent tab still ask? [05](05-agents-and-ai.md#open-questions)
- **Read-only level**: should the built-in assistant get one? [05](05-agents-and-ai.md#open-questions)
- **Shared tab handback**: should it return to you automatically when the agent's session ends? [05](05-agents-and-ai.md#open-questions)
- **Data-flow grant**: should it last for the session or until revoked? [05](05-agents-and-ai.md#open-questions)
- **Depot terms**: does Depot offer open-source terms, and what does a cold rac build cost? [06](06-engineering-and-shipping.md#open-questions)
- **Test targets**: does an official build tree compile the five test targets cheaply? [06](06-engineering-and-shipping.md#open-questions)
- **First launch**: does a signed first launch ask for update consent, and does Keychain prompt across an update? [06](06-engineering-and-shipping.md#open-questions)
- **Speed tolerance**: is 5% against Helium right, or 0% for typing and tab switch? [06](06-engineering-and-shipping.md#open-questions)
- **Bang triggers**: does the site-search page already list all 13,421? [07](07-power-features.md#open-questions)
- **Userscripts**: does Violentmonkey run in rac, and does Tampermonkey need a toggle? [07](07-power-features.md#open-questions)
- **Password managers**: do 1Password and Bitwarden desktop apps connect to rac? [07](07-power-features.md#open-questions)
- **Arc Boosts**: can Arc's local Boosts be read at all? Plan 04's spike decides. [07](07-power-features.md#open-questions)
- **Per-space Boosts**: should Boosts and routes become per space once sign-ins separate? [07](07-power-features.md#open-questions)
- **Deferred, no owner**: localhost developer bar, AppleScript for spaces, abandoned new tabs clearing themselves. [07](07-power-features.md#open-questions)
