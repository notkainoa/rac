# Start here

These plans take rac from today, when nobody can install it, to a launch for
Arc users before Arc shuts down on 2026-12-22, and past it.

## The conclusions

1. **Ship first.** A signed release, the catch-up to Helium, and proof that
   updates work come before the redesign. Release builds compile on paid
   Depot machines, where Helium's take about 7 hours.
2. **No separate server.** The browser is its own server. After launch,
   outside agents get a private door with its own switch, off by default.
3. **Safety before reach.** Close the agent's `auto` hole and add attack tests
   before any outside agent can act.
4. **Arc import is the launch feature.** It brings spaces, pins, favorites,
   and themes, plus sign-ins if they're ready. Each Arc profile becomes a rac
   profile.
5. **Stay on Chromium's Views UI and edit Chromium less.** There is no new
   shell. The command bar is native and reads from one shared action table.
6. **One calm design system.** It has shared values, springs for things that
   move, and nothing that repaints while idle. With AI off, no AI appears
   anywhere.

If you approve by 11-02, rac launches the week of 11-30.

## What to read

Required, in this order:

1. This page.
2. [overview.html](overview.html), open in a browser. It is the whole plan on
   one page.
3. [00-master-plan.md](00-master-plan.md). It has the order of work, the
   calendar, the threads, and the launch gates.
4. Group A of [decisions.md](decisions.md). These are the 16 decisions needed
   in week 1, in one table.
5. The first two sections of each plan, "In plain English" and "What you need
   to decide":
   [01 UI shell](01-ui-shell.md),
   [02 design and motion](02-visual-design-and-motion.md),
   [03 core architecture](03-core-architecture.md),
   [04 data and import](04-data-storage-import-sync.md),
   [05 agents and AI](05-agents-and-ai.md),
   [06 engineering and shipping](06-engineering-and-shipping.md), and
   [07 power features](07-power-features.md).

The rest of each plan is written for the build threads. Read it only if you
want to change something. Groups B and C of decisions.md can wait until a
thread reaches that milestone.

The research behind the plans is in [research/](research/).

## Words used here

- **W1 to W6:** the weeks after you approve.
- **M0, M1, and so on:** a plan's milestones.
- **D1 to D60:** decisions in decisions.md. **G1 to G15:** launch gates in the
  master plan.
- **The sync:** catching up to Helium 0.20.1.1 on Chromium 156. **The
  freeze:** nothing under `patches/` merges until the sync does.
- **Hunk:** one edited block in a Chromium file. Fewer hunks make Helium
  updates cheaper.
- **Action table:** one list of everything rac can do, shared by the sidebar,
  command bar, shortcuts, and agents.
- **The `auto` hole:** at the default level, a hostile page can make the agent
  copy data from one site into another. **Taint rule:** once the agent has
  read a second site, it asks before acting.
- **Debug doors:** Chromium's remote-debugging switches, which get around
  rac's guard.
- **The door:** the opt-in way for your own coding agent, such as Claude Code
  or Codex, to drive rac through a private socket with a revocable token per
  agent.
- **Agent-day:** one agent's working day.

## What happens next

1. You fast-forward your main checkout, which is 71 commits behind
   `origin/main`, and approve one incremental build there. The master plan's
   "After your review" has the commands.
2. You edit the plans and answer group A.
3. VISION.md, AGENTS.md, and the roadmap change only where you sign off.
4. The build threads launch from their briefs in [threads/](threads/): Ship,
   UI, Core, and Data now, and Power after launch. Nothing launches before you
   approve.

## Your questions, answered

**Should rac run a local server like T3 Code?** No (D21). T3 Code needs one
because its clients are remote. rac's work happens inside the browser, so the
browser is the server. Outside agents connect through a private socket, open
only while "Outside agents" is on, with no network port. The cost is that
runs end when rac quits and no phone can connect.

**Should rac use Pomerado?** Not inside rac (D57). It needs an OpenAI key,
Node 24, and its own Chromium, and it can't drive rac. Its API breaks almost
daily. rac takes the idea instead. A "recipe" records a task once and replays
it with no AI. Recipes come after the agent evals pass.

**What should rac take from ego(lite)?** The `rac` helper with a skill that
prints its own guide, background agent tabs that never steal focus, batched
steps, stable element references, smaller snapshots, and its MIT benchmark.
rac leaves out agents running their own JavaScript in signed-in tabs (D56)
and advice to turn off approval prompts.

**What should rac take from Cra?** Its Arc import key paths and cookie-import
method (MIT, with credit), its bounded archive, its daily check for upstream
drift, its release pipeline shape, and its measured Arc motion numbers. rac
skips its engine choice, CEF (D22), and its disabled sandbox.

**What should rac take from Aside and T3 Code?** From Aside, a CLI, MCP, and
a one-line skill install for coding agents, plus agent tabs that close when
idle. rac skips its always-on Node daemon and default-on analytics. From T3
Code, rac passes the agent's token on an inherited file handle so it never
shows in `ps`. The door works with rac's AI off (D12a).

**What about the Arc-refugee wishlist tweet?** Two lessons are now rules in
every plan. With AI off, no AI button, row, or label appears anywhere (gate
G15). Installed web apps (PWAs) must work, so plan 01 tests them in its first
two weeks and they join every screenshot check (gate G8).
