# Start here

## Overview

We studied the open-source Arc and Dia alternatives (Zen, Nook, Ora, Ardia,
Cra, and others), the closed AI browsers (Arc, Dia, Aside, Yab, Atlas), and
four tools: T3 Code, ego(lite), BrowserOS, and Pomerado. We compared features,
UI, motion, and above all architecture: what runs where, how agents drive the
browser, and what is stored locally or on a server. That produced 18 digests,
5 comparison matrices, and 7 plans.

The big conclusions:

1. **Ship first.** Nobody can install rac yet. A signed release, the Helium
   catch-up, and proof that updates work come before the redesign. Paid build
   machines (Depot) make release builds finish.
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

## Reading order

1. [00-master-plan.md](00-master-plan.md): how it all fits, the calendar, the threads, the launch gates.
2. [decisions.md](decisions.md): every open choice, with a recommendation. Group A first.
3. [06-engineering-and-shipping.md](06-engineering-and-shipping.md): builds, the Helium sync, releases, the calendar.
4. [04-data-storage-import-sync.md](04-data-storage-import-sync.md): Arc import, backups, storage, sync.
5. [05-agents-and-ai.md](05-agents-and-ai.md): agent safety, outside agents, evals.
6. [01-ui-shell.md](01-ui-shell.md): command bar, Peek, little window, Clear, sidebar.
7. [02-visual-design-and-motion.md](02-visual-design-and-motion.md): tokens, springs, materials, themes.
8. [03-core-architecture.md](03-core-architecture.md): no server, the action table, the door, fewer Chromium edits.
9. [07-power-features.md](07-power-features.md): clean links, Boosts, Air Traffic Control, bangs.
10. [research/matrices/features.md](research/matrices/features.md): features, rac against 13 browsers.
11. [research/matrices/ui-and-feel.md](research/matrices/ui-and-feel.md): looks, motion, and feel.
12. [research/matrices/architecture-and-storage.md](research/matrices/architecture-and-storage.md): processes, servers, local storage.
13. [research/matrices/agents.md](research/matrices/agents.md): how each agent reads, acts, and asks.
14. [research/matrices/engineering-and-shipping.md](research/matrices/engineering-and-shipping.md): builds, upstream tracking, releases.
15. [research/digests/](research/digests/): one short digest per product, each with "take" and "avoid" lists. Full dossiers sit in [research/](research/).
16. [context/](context/): your brief, CI status, the Ardia and Yab notes, the earlier roadmap, and the Inbox Zero council.

## Decided versus open

**Already decided** (by you, or shipped): AI is off by default, and AI off
costs nothing. Three permission levels (`ask`, `careful`, `auto`), with `auto`
the default and the risky list always asking. Per-site Always and Never rules.
Quiet tool rows. No accounts, nothing phones home. Never edit Helium's code,
and send nothing upstream.

**Settled across the plans** (you can still overrule): one action table,
owned by plan 03. The command bar is native Views. Plan 01 owns Clear and the
archive. Plan 06 owns the calendar and the sync. With AI off, no AI button,
row, or label appears, which is an acceptance check everywhere. Installed web
app windows join every screenshot matrix.

**Open:** 59 decisions in [decisions.md](decisions.md). 16 come before
anything starts: the approval date, the order of work, the build budget,
which Mac, full-build approvals, thread permissions, and VISION.md changes.
It also lists 15 conflicts between plans with proposed fixes, the VISION.md
and AGENTS.md bends, the money, and what touches your real data.

## How the next step works

1. You read, edit, and comment on the plans. Change anything.
2. You answer decisions.md, group A first. Group B can wait until its thread
   reaches that milestone.
3. The plans get one cleanup pass. Broken cross-references are fixed, and the
   conflict fixes you accept are written in.
4. VISION.md, AGENTS.md, and the roadmap change only where you signed off.
5. Then the build threads launch: Ship, UI, Core, and Data, and Power after
   launch. Each one starts from its plan's draft brief and the master plan's
   thread map. **Not before your approval.**

## Your questions, answered

**Should rac run a local server like T3 Code?** No (03-D1). T3 Code needs a
server because its clients are remote, like a phone or the web, and its work
needs no browser. rac's work happens inside the browser, so the browser is the
server. For outside agents, rac opens a private socket per profile, only while
"Outside agents" is on. Agents reach it through a tiny signed `rac` command
inside the app (`rac mcp`), with a revocable token per agent. No network port
is involved. You give up four things: runs end when rac quits, no phone can
connect, sessions don't survive a restart, and nothing runs with rac closed. A
separate helper is added only if a named feature must run with rac closed.
Node or Bun sidecars are rejected: they cost memory, need weaker code-signing
rules, and every product that used one ended up running it all the time.

**Should rac use Pomerado?** Not inside rac (05-D8). Pomerado needs an
OpenAI key to build its integrations, plus Node 24 and its own Chromium. It
can't drive rac. Its "self-healing" is a paid hosted feature, not in the open
code. Its API also changes weekly. Take the idea instead: record a task once,
then replay it with no AI. That becomes rac's "recipes", after the agent evals
pass. Every replayed step still goes through rac's guard, and recipes work
with AI off. Anyone can still run Pomerado as their own outside tool.

**What should rac take from ego(lite)?** Its reach and ergonomics, behind
rac's guard: the `rac` helper with a skill that prints its own guide,
background agent tabs that never steal focus (with take over and give back),
batched steps, stable element refs, smaller snapshots, action receipts, a
static action label, and its MIT benchmark. Leave out agents running their own
JavaScript in your signed-in tabs (later, no-login tabs only, 05-D4), and
telling users to turn off their agent's approval prompts.

**What should rac take from Cra?** Its exact Arc import key paths and its
cookie-import method (MIT, ported with credit), its bounded archive (1,500
entries), its daily check for upstream drift, its release pipeline shape, and
its measured Arc motion numbers. Don't take its engine choice (CEF, 03-D4),
its disabled sandbox, its one-laptop engine builds, or "no phone-home" claims
with no network capture behind them.

**The Arc-refugee wishlist (no AI buttons, PWAs).** rac already fits the list
on paper: Chromium, a sidebar, split view, pins and folders, profiles and
spaces. Two lessons are now rules in every plan. First, with AI off, no AI
button, row, or label appears anywhere, including the command bar, and every
plan checks it. With AI on, rac keeps few AI surfaces. Ask moves into the
command bar and the AI new tab page retires (01-D8). Second, installed web
apps (PWAs) work in rac because Chromium supports them, but nobody has tested
them with rac's look and sidebar patches. Plan 01 checks them on today's build
in its first two weeks and fixes what breaks. PWA windows also join the sync
checks and every screenshot matrix, as part of launch gate G8.
