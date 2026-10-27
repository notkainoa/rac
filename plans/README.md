# Start here

## Overview

We studied the open-source Arc and Dia alternatives (Zen, Nook, Ora, Ardia,
Cra, and others), the closed AI browsers (Arc, Dia, Aside, Yab, Atlas),
BrowserOS, and three tools: T3 Code, ego(lite), and Pomerado. We compared
features, UI, motion, and above all architecture. That produced 18 digests, 5
comparison matrices, and 7 plans.

The big conclusions:

1. **Ship first.** Nobody can install rac yet. A signed release, the Helium
   catch-up, and proof that updates work come before the redesign. Paid build
   machines (Depot) should let release builds finish; Helium's take about 7
   hours there.
2. **No separate server.** The browser is its own server. Outside agents get
   a private door after launch, with its own switch, off by default.
3. **Safety before reach.** Close the agent's `auto` hole and add attack tests
   before any outside agent can act.
4. **Arc import is the launch feature.** Spaces, pins, favorites, and themes,
   plus sign-ins if they're ready. Each Arc profile becomes a rac profile.
5. **Stay on Chromium's Views UI and edit Chromium less.** No new shell. The
   command bar is native, built on one shared action table.
6. **One calm design system.** Shared values, springs for things that move,
   nothing repainting while idle. With AI off, no AI anywhere.

What happens next: you review and edit the plans and answer the decisions.
Then the build threads launch. If you approve by 11-02, rac launches the week
of 11-30, ahead of Arc's shutdown on 12-22.

## Words used here

- **W1 to W6:** weeks after you approve.
- **M0, M1:** a plan's milestones.
- **D1 to D60:** decisions. **G1 to G15:** launch gates. **C1 to C15:**
  conflicts between plans. **Ruling N:** item N in [rulings.md](rulings.md).
- **Agent-day:** one agent's working day.
- **Hunk:** one edited block in a Chromium file. Fewer make Helium updates
  cheaper. **Hot file:** a Chromium file Helium also edits.
- **The sync:** catching up to Helium 0.20.1.1 / Chromium 156. **The freeze:**
  nothing under `patches/` merges until the sync does.
- **Base Mac:** the Mac whose built Chromium every worktree copies.
- **Views:** Chromium's native UI toolkit.
- **Action table:** one list of everything rac can do, shared by the sidebar,
  command bar, shortcuts, and agents.
- **The door:** the opt-in way for your own coding agent (Claude Code, Codex)
  to drive rac, through a private socket and a revocable token per agent.
- **The `auto` hole:** at the default level, a hostile page can make the agent
  copy data from one site into another. **Taint rule:** once the agent has
  read two sites, it asks before acting.
- **Debug doors:** Chromium's remote-debugging switches, which bypass rac's
  guard.

## Reading order

Required:

1. [00-master-plan.md](00-master-plan.md): fit, calendar, threads, launch gates.
2. [decisions.md](decisions.md): every open choice, with a recommendation.
3. [06-engineering-and-shipping.md](06-engineering-and-shipping.md): builds, the sync, releases.
4. [04-data-storage-import-sync.md](04-data-storage-import-sync.md): Arc import, backups, storage.
5. [05-agents-and-ai.md](05-agents-and-ai.md): agent safety, the door, evals.
6. [01-ui-shell.md](01-ui-shell.md): command bar, Peek, Clear, sidebar.
7. [02-visual-design-and-motion.md](02-visual-design-and-motion.md): springs, materials, themes.
8. [03-core-architecture.md](03-core-architecture.md): no server, action table, fewer edits.
9. [07-power-features.md](07-power-features.md): Boosts, Air Traffic Control, bangs.

Evidence, if you want it (all optional):

10. [rulings.md](rulings.md): the 18 cross-plan rulings the plans cite.
11. [research/matrices/](research/matrices/): five comparisons.
12. [research/digests/](research/digests/): one short digest per product. Full dossiers sit in [research/](research/).
13. [context/](context/): your brief, CI status, earlier notes.

## Decided versus open

**Already decided** (by you, or shipped): AI is off by default and costs
nothing when off. Three permission levels (`ask`, `careful`, `auto`), with
`auto` the default and the risky list always asking. Per-site Always and Never
rules. No accounts, nothing phones home. Never edit Helium's code, and send
nothing upstream.

**Settled across the plans** (you can still overrule), per
[rulings.md](rulings.md): one action table, owned by plan 03. The command bar
is native Views. Plan 01 owns Clear and the archive. Plan 06 owns the calendar
and the sync. With AI off, no AI button, row, or label appears, which is an
acceptance check everywhere. Installed web app windows join every screenshot
matrix.

**Open:** 60 decisions in [decisions.md](decisions.md). 16 are needed in week
1 (group A): the approval date, the order of work, money, which Mac, thread
permissions, Peek, the command bar's status, the `auto` hole, the debug doors,
the server and shell questions, and Arc test data. The rest wait for their
thread's milestone. It also lists 15 conflicts between plans with proposed
fixes, the VISION.md and AGENTS.md bends, and the open questions from every
plan.

## How the next step works

0. Your main checkout's `main` is 71 commits behind origin/main. It needs a
   fast-forward and one incremental build, which needs your approval (master
   plan, "After your review").
1. You read, edit, and comment on the plans. Change anything.
2. You answer decisions.md, group A first. Group B can wait until its thread
   reaches that milestone.
3. The plans get one cleanup pass: the conflict fixes you accept are written
   in.
4. VISION.md, AGENTS.md, and the roadmap change only where you signed off.
5. Then the build threads launch: Ship, UI, Core, and Data, and Power after
   launch. Each one starts from its brief in `plans/threads/` plus the master
   plan's thread map. **Not before your approval.**

## Your questions, answered

**Should rac run a local server like T3 Code?** No (D21). T3 Code needs a
server because its clients are remote, like a phone or the web, and its work
needs no browser. rac's work happens inside the browser, so the browser is the
server. For outside agents, rac opens a private socket per profile, only while
"Outside agents" is on. Agents reach it through a tiny signed `rac` command
inside the app (`rac mcp`), with a revocable token per agent. No network port
is involved. You give up four things: runs end when rac quits, no phone can
connect, sessions don't survive a restart, and nothing runs with rac closed.
Node or Bun sidecars are rejected: they cost memory, need weaker code-signing
rules, and every product that used one ended up running it all the time.

**Should rac use Pomerado?** Not inside rac (D57). Pomerado needs an OpenAI
key to build its integrations, plus Node 24 and its own Chromium. It can't
drive rac. Its "self-healing" is a paid hosted feature, not in the open code.
Its API still has breaking changes almost daily. Take the idea instead: record
a task once, then replay it with no AI. That becomes rac's "recipes", after
the agent evals pass, still behind rac's guard and working with AI off.

**What should rac take from ego(lite)?** Its reach and ergonomics, behind
rac's guard: the `rac` helper with a skill that prints its own guide,
background agent tabs that never steal focus (with take over and give back),
batched steps, stable element refs, smaller snapshots, action receipts, a
static action label, and its MIT benchmark. Leave out agents running their own
JavaScript in your signed-in tabs (later, no-login tabs only, D56), and
telling users to turn off their agent's approval prompts.

**What should rac take from Cra?** Its exact Arc import key paths and its
cookie-import method (MIT, ported with credit), its bounded archive, its daily check for upstream drift, its
release pipeline shape, and its measured Arc motion numbers. Don't take its engine choice (CEF, D22), its
disabled sandbox, its one-laptop engine builds, or "no phone-home" claims with
no network capture behind them.

**What should rac take from Aside and T3 Code?** From Aside: a CLI, MCP, and
a one-line skill install for coding agents, and agent tabs that close when
idle. Leave out its always-on 159 MB Node daemon on a local port, its
analytics on by default, its guard that allows by default, and its use of
Claude subscriptions by posing as Claude Code. rac's answer to Rhys Sullivan's
"let me kill the built-in agent" is that the door works with rac's AI off
(D12a). From T3 Code: passing the agent's token on an inherited file handle,
so it never shows in `ps`, and loops that pause off screen. Not its server
(D21).

**The Arc-refugee wishlist (no AI buttons, PWAs).** Two lessons are now rules in
every plan. First, with AI off, no AI button, row, or label appears anywhere,
including the command bar. With AI on, Ask moves into the command bar and the
AI new tab page retires (D30). Second, installed web apps (PWAs) should work
in rac, but nobody has tested them with rac's patches. Plan 01 checks them in
its first two weeks, and they join every screenshot matrix (gate G8).
