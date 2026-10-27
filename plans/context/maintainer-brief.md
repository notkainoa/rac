# Maintainer brief for the overhaul research (2026-10-25)

Every research and planning agent reads this first. It records what the
maintainer has already decided, what they asked for, and where rac stands.
"The maintainer" is the one person who runs rac (they/them). They direct AI
coding agents in parallel worktrees and use rac as their daily browser.

## What the maintainer asked for

A research and planning phase, before a deep revamp of the app:

- Study the good open-source Arc and Dia alternatives, plus Aside and T3 Code.
  Compare features, UI, how it looks, animations and feel, and above all the
  architecture: the backend, how agents work, how data is stored locally,
  whether a server is involved, and how rac could run its own "server" locally.
- Produce many plans. Where a choice is open, give several options and let the
  maintainer choose. Leave open questions open and list them.
- Every plan needs a short plain-English section that explains it simply, so the
  maintainer can review everything quickly.
- Take the existing plans and decisions seriously (many are wanted), but don't
  take them for granted: research them and challenge them where warranted.
- After the maintainer reviews and edits the plans, the work will be split into
  a few long-running threads: one for UI, and one or more for architecture and
  the backend ("we really want to overhaul how this works"). Each thread will use
  multi-agent workflows to build, test with screenshots and videos, and open PRs.
- This work lives on the `plans/overhaul` branch, not on `main`.

## What rac is (from VISION.md and AGENTS.md; read those too)

A private, fast, beautiful macOS browser. A fork of helium-macos (Helium is an
ungoogled-chromium browser), with Arc-inspired features. All rac changes are
quilt patches in `patches/rac/<group>/`, applied after Helium's. GPL-3.0.

Non-negotiables, as written today: private (nothing phones home to rac; no
accounts); never slower than Helium (a feature that's off does no work); calm
and beautiful (tasteful motion, nothing that repaints continuously); opinionated
(few settings); cheap to update (prefer new files and small hooks over edits to
upstream files). AI is optional and off by default, and "AI off costs nothing".

Hard constraints from AGENTS.md: never send anything upstream to imputnet or
ungoogled-software (Helium bans AI-written contributions); never edit
`helium-chromium/` or Helium's patch folders; never point a build at the
maintainer's real profile; never run a full build or `he reset` without approval;
the update signing key, feed URL, and rising version number never change.

## Where rac stands on 2026-10-25

- Built and merged on `main`: spaces (switching, dots, saving, unloading, sliding
  pages), pinned tabs and favorites (folders, drag, snap, reset), sidebar hide and
  edge reveal (full or hidden only, no icons-only mode), address bar in the
  sidebar plus a site control center, auto picture-in-picture, onboarding,
  branding/app icon/DMG art, AI basics (side panel that reads the page, new tab
  page ask, Cmd+F Ask, link hover summaries; providers are BYO API key, local
  models via Ollama/LM Studio, or installed ACP agents like Claude Code, Codex,
  Cursor), and the browser agent.
- The agent: snapshot and refs, tools, an MCP server over a Unix socket that only
  serves the agent rac launched and only during a run, a guard, a critic, confirm
  cards, a tab indicator with Stop, and a step cap. In this session the maintainer
  chose three permission levels: `ask`, `careful`, `auto` (default `auto`, Yab-like
  "YOLO" but risky actions always ask), plus per-site Always/Never rules, and no
  level that bypasses the risky list. They also asked for the agent's tool calls
  and errors to show as quiet, simple rows that expand on click. Both shipped in
  PRs #11–#14, #17, #18.
- A known gap (verified in `patches/rac/agent/13-permission-levels.patch`, test
  `AutoAsksOnlyForRiskAndForeignTyping`): at `auto`, cross-site navigation and
  typing model-written text into the attached tab need no card, which allows a
  prompt-injection exfiltration chain. No evals or red-team suite exist.
- Marketing site: `site/` (Astro, pnpm workspace, monorepo-light), live at
  racbrowser.com, download page hidden behind `RELEASE_READY`.
- Releases: zero. `rac_version.txt` is 0.1.0. All Apple Developer ID signing,
  notarization, and Sparkle secrets are configured. The CI release workflow has
  never completed. sccache now works (fixed in PR #19), but each 6-hour build
  phase restarts siso from step zero, so the 10-phase chain can't finish. That is
  under investigation (see `plans/context/ci-status.md` if present).
- Upstream gap: rac is on Helium 0.18.2.1 / Chromium 154.0.8037.92. helium-macos
  is at 0.20.1.1 (2026-10-22), seven releases ahead. rac has never synced.
- Engineering: about 180 rac patches, about 871 hunks across 217 upstream files
  (about 320 in `ui/views`). About 284 unit tests in 5 targets; CI never compiles
  or runs them. 96% of commits are AI co-authored; 70% landed directly on `main`.

## Market context

- Arc shuts down on 2026-12-22. Arc refugees are the near-term market.
- Ardia (open source, Chromium, Expo/React Native macOS shell, ~70 releases, Arc
  import, iCloud end-to-end sync, no AI) and Yab (closed, WebKit, AI-first, agent
  defaults to Auto, MCP with 69 tools, CLI) are shipping. See
  `plans/context/competitors-ardia-yab-2026-10-23.md`.
- Aside (YC, Chromium, closed) ships a CLI, an MCP server, skills install for
  coding agents, routines, Slack/Telegram, and lets you connect an existing Claude
  or ChatGPT subscription. A developer (Rhys Sullivan, 2026-10-24) praised the
  CLI and MCP as "so obviously good features" but wished he could kill Aside's
  built-in agent because he has his own. rac today can't be driven by an outside
  agent at all, and turning AI off also removes its MCP server.
- ego(lite) by Citro Labs (lite.ego.app, github.com/citrolabs/ego-lite) is a
  Chromium browser that doubles as the browser your own coding agents drive
  through a skill and shell commands, with in-page JavaScript tools, batched
  steps, stable element refs, and isolated agent Spaces that never steal focus.
  The maintainer said it does "a lot of the agent in a browser stuff really
  really well". Treat it as a primary reference for rac's agent design.
- An Inbox Zero comparison and a three-model council (in
  `plans/context/inboxzero/`) concluded: ship one signed release and prove the
  update loop; do the first Helium sync now; make the agent default safe and add
  injection evals; build Arc import; make CI compile and run tests and protect
  `main`. Correction to those files: Inbox Zero's default "Notify sender" mail
  goes out from Inbox Zero's address, not the user's account; and rac does have
  an Apple Developer ID.

## Earlier plans that the maintainer saw but did not commit

`plans/context/roadmap-revision-2026-10-22.md` is a proposed roadmap: phase 3
"finish what's built", phase 4 "ready to release" (icons, onboarding, Helium
sync, perf bench, signing and nightly channel, CI, power/frame patches, crash
reports), phase 5 "after the release" (agent refine and open up to outside
agents with per-agent permissions; import from every browser; command bar;
Air Traffic Control; clean links; tab clean-up; auto-named groups; Little Arc;
boosts), phase 6 one at a time (hand-off to agents on other devices, video
upscaling, on-device translation, automations, 1Password, sync). Some items are
already built since then (onboarding, icons/DMG).

## Taste and working preferences

- The maintainer cares a lot about UI quality: "immaculate", calm, Arc's
  personality with Dia's simplicity, tasteful micro-interactions. For the site
  they liked animations.dev, orchid.ai, aiforui.dev, akeru-bot.com, mastra.ai,
  email-sdk.dev, gradients.sh.
- UI and design work goes to Claude Opus. Hard architecture goes to Opus.
- They want plain, concise explanations; short sentences; no jargon without a
  definition.
- They want everything tested by the agent with screenshots and videos before
  they look, and PRs with visual proof.

## Where to look in the repo

Repo root for reading: `/Users/knewton/.t3/worktrees/rac/t3-bb0e4397` (branch
`plans/overhaul`, identical to `main` at d3f0d66 apart from `plans/`).
Key files: `VISION.md`, `AGENTS.md`, `docs/roadmap.md`, `docs/internals/*.md`
(especially `ai.md`, `overview.md`, `glossary.md`), `docs/operations/*.md`,
`patches/series`, `patches/rac/*/`, `site/`, `.github/`.
The main checkout with a built Chromium tree (read-only for you):
`/Users/knewton/Dev/Github/rac/build/src` (Chromium 154 with Helium and rac
patches applied).

## Added 2026-10-27

- Cra (crabrowser.app, github.com/VictorKildahl/cra, MIT, created 2026-10-24) is a
  new, independent, privacy-first Arc replacement for macOS 14+. Swift plus
  Objective-C++ around what looks like an embedded Chromium (Chrome extensions
  and DevTools work). Spaces with their own pinned tabs and Today list, a shared
  favorites grid, folders, a command bar over tabs, archive, history and actions,
  auto-archive, Little Windows, split view up to 4 panes, auto PiP, Arc/Dia/Chrome
  and other imports, a built-in blocker, no AI, no account, no server, data as
  plain JSON in Application Support. It is the closest positioning match to rac
  minus AI, and its "native shell around Chromium" approach matters for the
  architecture plan (patch surface).
- Pomerado (YC F26, github.com/Pomerado/pomerado, MIT) turns any website into a
  deterministic, self-healing API/MCP integration for agents, minted from a
  natural-language task (it uses OpenAI models to build integrations; Node 24).
  The maintainer asked whether rac should use it. Treat it as an outside-agent
  tool and an idea source (deterministic replayable "recipes" instead of an LLM
  loop for repeat tasks), not as something to embed by default.

## Added 2026-10-27 (later)

- An Arc-refugee wishlist on X (ZaynHao, 2026-10-27, in Chinese): Chromium-based, PWA
  support, a sidebar, split view, pins or folders, multiple profiles or spaces, and
  "as few AI buttons as possible, chat or summaries". rac fits this on paper. Two
  lessons: with AI off, no AI button, row, or label may appear anywhere; and
  installed web-app (PWA) windows have never been tested with rac's look and
  sidebar patches.
