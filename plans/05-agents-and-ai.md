# 05. Agents and AI

## In plain English

rac's AI already works: a side panel, Ask in the new tab and in Find, link summaries, and an agent that clicks and types. It is careful, but its default level has one hole. A hostile page can make the agent read your mail and type it back into that page. We close that first, with tests that try to break it.

Next, developers get what Aside and ego(lite) give them: their own coding agent can drive rac. One switch, separate from rac's AI, turns this on. With it off, nothing listens. With rac's AI off, outside agents still work. Every outside call goes through the same "ask before risky steps" checks as rac's own agent.

Then agents get their own space. Their tabs stay in the background, never steal focus, and you can watch or take over at any time. Later, a task that worked once can be saved as a "recipe" and replayed without any AI. Routines can run recipes on a schedule.

What stays the same: AI is off by default. rac never sees your conversations. Nothing phones home. Subscriptions connect only through the vendor's own tools, never by pretending to be them.

## What you need to decide

1. **05-D1. How do we close the `auto` hole?** Fix `auto` itself / make `careful` the default / both. **Recommended: fix `auto` and keep it the default.**
2. **05-D2. Do outside agents work with rac's AI off?** Yes, own switch / no, needs AI on. **Recommended: yes, with its own switch, off by default.** This changes one sentence in VISION.md.
3. **05-D3. What can a newly connected outside agent do?** Read only / ask for each step / the user's level. **Recommended: read only until the user raises it.**
4. **05-D4. Where do outside agents act?** Only their own agent space / also any tab you share / any tab. **Recommended: own space, plus tabs you share by hand.**
5. **05-D5. What is an agent space?** A section in your current space / its own space per agent / an off-screen window. **Recommended: its own space per agent, if the rendering spike passes.**
6. **05-D6. Whose logins does an agent space use?** Yours / none (thrown away after) / the agent's own saved logins. **Recommended: you choose per agent; outside agents start with none.**
7. **05-D7. Should agents run JavaScript in pages, like ego?** Never / lists of rac steps only / JavaScript only in no-login spaces. **Recommended: step lists now; JavaScript only in no-login spaces, later.**
8. **05-D8. Which door for outside agents?** MCP / a `rac` CLI with a skill / both. **Recommended: both, from one small helper; MCP first.**
9. **05-D9. What about Chromium's own remote-debugging doors?** Leave them / turn them off with an expert switch / harden the dialog. **Recommended: off by default, expert switch labelled "unguarded".**
10. **05-D10. Repeat tasks: Pomerado or our own recipes?** Embed Pomerado / native recipes / neither. **Recommended: native recipes, after the evals pass. Don't embed Pomerado.**
11. **05-D11. Routines: when do they run?** Not built (use your own scheduler and the CLI) / while rac is open / also while closed. **Recommended: CLI first; while-open routines later; while-closed only if plan 03 adds a helper.**
12. **05-D12. Keep rac-launched agents warm between messages?** Cold start each message / warm while the panel is open, 5-minute idle limit. **Recommended: warm, with the limit.**

## Where we are today

**Built** (FACT, `docs/internals/ai.md`, `plans/research/digests/rac-baseline.md`):

- **Assistant surfaces:** side panel chat, new tab page Ask, Cmd+F Ask, and Option-hover link summaries. Patches `patches/rac/ai/01`–`23`.
- **Providers:** your own key (OpenAI, Anthropic, Gemini, OpenRouter, custom), local models (Ollama, LM Studio), and ACP agents (Claude Code, Codex, Cursor, Gemini, Copilot, OpenCode, Goose, custom). Keys are encrypted with `os_crypt_async` (`ai.md:49-66`).
- **Agent:** 15 tools, APC-based snapshot lines like `- button "Sign in" [ref=e6] [submit]`, never-reused refs, TOCTOU re-checks, containment, a page-blind critic at `careful`, cards, a ring and pill, and a 25-call cap (`ai.md:333-577`). It is 19 patches in `patches/rac/agent/`, touching 21 upstream files and 58 hunks (`digests/chromium-agent-internals.md`).
- **Levels:** `ask`, `careful`, `auto` (default), per-site Always/Never, no level skips the risky list (`patches/rac/agent/13-permission-levels.patch`, `14-site-rules.patch`).

**Gaps** (FACT unless tagged):

- **The `auto` hole.** At `auto`, a cross-site navigation and typing model-written text into the attached tab are both free. Test `AutoAsksOnlyForRiskAndForeignTyping` asserts it (`13-permission-levels.patch:329-370`). Chain: open a shown link to mail, read it, type it into the hostile page, and the page's script sends it out. The exploit has not been run (`matrices/agents.md`, "The exfiltration gap").
- **Fail-open parsing.** `ParsePermissionLevel` reads any unknown string, including `"bypass"`, as `kAuto` (`13-permission-levels.patch:33-41, 411-417`). Harmless while `auto` is the default. It becomes a trap if the default moves.
- **Unguarded doors.** `--remote-debugging-port` on the real profile and `chrome://inspect` approval mode both give a local app the whole logged-in profile with none of rac's guard. Neither is patched (`digests/agent-stacks.md`, gap 10; INFERENCE, not run).
- **Dev switches ship in every build:** `--rac-window-screenshot-requests` (can click and type), `--rac-agent-debug`, `--rac-agent-mcp-echo` (`digests/rac-baseline.md`).
- **No outside door.** The MCP server serves only the agent rac launched, only during its run. Turning AI off removes it (`ai.md:307-331`).
- **No evals.** About 284 unit tests exist; CI never runs them. Only one test (`MasterSwitchGatesEntryPoints`) checks "AI off costs nothing".
- **Tool gaps:** `press_key` is Enter only; no hover, dialog handling, ref-returning find, or screenshot. Snapshot deltas cost about 1,800 tokens for 3 changes (`digests/agent-stacks.md`, "rac's concrete gaps").
- **Speed:** ACP agents cold-start on every message, 15–25 s (CLAIM, `ai.md:708-718`).
- **Copy drift:** onboarding says the AI "never acts … without your confirmation", which default `auto` contradicts (`digests/rac-baseline.md`).

## What others do

Full tables are in `plans/research/matrices/agents.md`. The short version:

- **ego(lite)** has no AI. Your coding agent writes one JavaScript program per call, through a skill and the `ego-browser` command. Its agent Spaces never steal focus and its refs are stable. Safety is thin: scripts can read every cookie (issue #315), and its guides tell you to turn your agent's approvals off (`digests/ego-lite.md`).
- **Aside** ships a CLI, a 4-tool MCP, skills install, and agent tabs that close after 15 idle minutes. Its guard defaults to allow. It connects Claude subscriptions by impersonating Claude Code, with a forged billing header (`digests/aside.md`).
- **BrowserOS** has a one-click Connect page for 7 agents. It also has unauthenticated ports and no AI-off (`digests/browseros.md`).
- **Open stacks** converged on outside-agent tools. Stagehand deleted its built-in agent. Nanobrowser has the best eval template: 68 hostile fixture pages, a fake model server, four graded outcomes (`digests/agent-stacks.md`).
- **Chrome** limits data flow with "Agent Origin Sets". It asks on new origins by default from M158 (`digests/chromium-agent-internals.md`).
- **Closed browsers** found that detection fails and fixed rules hold. Yab asks before mail's words go to a new site. Dia only fetches URLs the user or a viewed page supplied (`digests/closed-ai-browsers.md`).
- **T3 Code** keeps agent sessions warm for 30 minutes. It uses one tool service for every door (`digests/t3code.md`).
- **Pomerado** records once and replays with no model. It needs OpenAI to record, ships its own Chromium, and can't drive rac (`digests/pomerado.md`).

## Options

The matrix recommends a staged path: (d) close the gap and doors and add evals, then (a) one guarded door, then (c) agent spaces, then batching and recipes (`matrices/agents.md`, "Recommendation"). I agree with the order of risk. I challenge it in three places:

1. **The door's read-only tier need not wait for the full eval suite.** Reading can't type anything into a page. It can be built alongside the evals.
2. **A door that can write needs agent-owned tabs from day one.** An outside agent has no "attached tab" to act in. So a minimal agent space must ship with the write tier, not after it.
3. **Batching adds no new power.** Each step still passes the guard. It belongs with the write tier, not at the very end.

### Option A: Safety floor only

**In plain English.** We fix the hole, close the debug doors, and write attack tests. We add nothing new. Users see a few more cards at `auto`. Developers still can't drive rac with their own agent.

- **Details:** the guard fixes in M0 below; CDP door fixes; dev switches gated; eval tier 1.
- **Pros:** smallest; strictly safer; ships before Arc closes.
- **Cons:** ignores the Aside and ego demand; developers keep reaching for raw CDP, which has no guard.
- **Effort:** S–M, about 14–20 agent-days.
- **Risk:** low.
- **Locks in:** nothing.

### Option B: Built-in first, one guarded door (the matrix's option a, plus my challenges)

**In plain English.** rac's own assistant stays the main story. Outside agents get one door with its own switch. They start read-only. When raised, they act in their own agent space, through the same guard. Later come sign-in modes, recipes, and routines.

- **Details:** one tool layer (`AgentController::HandleToolCall`) serves the built-in loop, ACP agents, MCP, and the CLI. The controller moves out from under the AI switch.
- **Pros:** reuses the guard, cards, snapshot, and refs; answers the Rhys Sullivan complaint; each stage ships on its own.
- **Cons:** several clients at once break "one turn per profile", so the controller needs a refactor; agent spaces touch hot Views and session-restore files.
- **Effort:** XL overall, about 90–130 agent-days across M0–M5. M0 and M1 alone are about 35–45.
- **Risk:** medium; the hidden-tab rendering spike is the main unknown.
- **Locks in:** the guard sits on every path; no raw CDP or script runner on the real profile.

### Option C: Outside agents first, like ego

**In plain English.** rac becomes "the browser your agent drives". The built-in assistant is one client among many. The main work goes into ego-style scripting: in-page JavaScript, batches, and stable locators.

- **Details:** a `rac` CLI accepts JavaScript programs; `page.evaluate` runs in an isolated world; raw CDP is scoped to agent spaces.
- **Pros:** strongest developer story; matches where open stacks went; best token cost.
- **Cons:** in-page JavaScript on a logged-in profile bypasses every guard. A script can call `element.click()` or `fetch()` with your cookies. That is ego's #315 again. It also repositions rac away from VISION's calm assistant, and leaves people without a coding agent behind.
- **Effort:** L, about 40–60 agent-days for the scripting core.
- **Risk:** high (safety), plus a VISION change.
- **Locks in:** a script API that is hard to take back.

### Option D: Separate agent app or helper owns all agent work

**In plain English.** A small rac helper program runs the agent, the door, recipes, and routines. The browser only executes guarded actions. Routines could run while rac is closed.

- **Details:** this is plan 03's "Rust helper" option, applied to AI (`matrices/architecture-and-storage.md`, Option 3).
- **Pros:** faster iteration without Chromium rebuilds; crash isolation; routines while closed.
- **Cons:** a second signed binary while the release build has never finished; two places for state.
- **Effort:** L–XL.
- **Risk:** medium-high for one maintainer.
- **Locks in:** a second runtime.

**Recommendation: Option B,** starting with Option A as M0.

- **Graft from C:** batched step lists, stable locators, snapshot scope, the self-printing skill, and agent spaces that never steal focus. JavaScript runs only in no-login spaces, and only later (05-D7).
- **Graft from D:** keep the tool contract transport-neutral, so plan 03 can move agent-side work into a helper later without changing callers.

C is rejected because its signature feature is a guard bypass. D waits for a trigger that plan 03 owns.

## Recommended plan

Each milestone lists its goal, its tasks, how we know it is done, and its patch surface. Day counts are agent-days (INFERENCE). Every UI milestone ships screenshots from `devutils/rac/worktree.sh run` with `--rac-window-screenshot`, in light and dark, with both sidebar states. Motion gets a short video and a reduced-motion check.

### M0. Safety floor (before the first public release; about 2 weeks)

**Goal:** the default level can't be walked into the exfiltration chain. Doors are closed. Evals exist.

Tasks:

1. **First visit to an unnamed site asks, even at `auto`.** On the first navigation, open-tab, or cross-site click to an origin outside the turn's named set, show one card: Allow once / Always on this site / Don't allow. "Allow once" adds the origin to the turn's named set. This cuts the chain at step 2 (`matrices/agents.md`, fix 1). About 2–3 days.
2. **Data-flow rule on typing.** Once the agent has read any origin other than the one it is typing into, typing text that isn't in the user's messages asks. The card shows the exact text. No taint tracking, just "you read elsewhere, so ask". This cuts the chain at step 3 even when both sites are named (fix 2). About 3–4 days.
3. **A local sensitive-site list.** A curated, built-in list covers banks, payments, health, government, and webmail. The first action on such a site is a card at every level. It has no network fetch, and a `--rac-agent-sensitive-sites=` switch serves tests (`digests/chromium-agent-internals.md`, take 7). About 2–3 days. Most of the work is the list.
4. **Fail closed on unknown level names.** Unknown strings parse to `ask`, and the registered default stays `auto`. Update `UnknownLevelNameIsAuto`. Under 1 day.
5. **Mark page text for every model.** Use tool-named boundary markers, escape fake markers, and neutralize role tags (including spaced letters), on top of today's nonces. Never skip this for "strong" models, as Aside does (`digests/aside.md`, take 6). 1–2 days.
6. **Close the CDP doors.** Turn on Chromium's default-data-dir check for `--remote-debugging-port` in rac builds (today it runs only under Google branding). Turn `chrome://inspect` approval mode off by default, with an expert switch in Outside agents labelled "Unguarded: gives an app your whole profile" (05-D9). Dev runs pass `--user-data-dir` (`dev.sh:132`, `worktree.sh:206`), so the DevTools-port screenshot workflow should keep working. Verify that. 1–2 days.
7. **Gate dev switches out of release builds** (with plan 06): `--rac-window-screenshot-requests`, `--rac-agent-debug`, `--rac-agent-mcp-echo`. Under 1 day.
8. **Eval tier 1** (see "Evals and red team" below). About 5–8 days.
9. **AI-off tests, first set** (see "Proving AI off costs nothing" below). 2–3 days.
10. **Fix copy:** the onboarding promise, the site's "It asks before it acts", and the `ai.md` permission table. Half a day.

Acceptance:

- The chain fixture stops at a card, on every level, for each model in the tier-2 set.
- `AutoAsksOnlyForRiskAndForeignTyping` is rewritten to assert the new cards.
- A release build ignores the dev switches.
- `--remote-debugging-port` on the default profile is refused.

Verification: unit tests in `rac_agent_unittests`; screenshots of the new first-visit and data-flow cards, light and dark, with the sidebar shown and hidden.

Patch surface: rac-owned files (`action_guard.*`, `agent_controller.*`), plus about 3–5 upstream hunks for the CDP checks and switch gating.

### M1. The door, read-only tier (about 3 weeks; can overlap M0 tasks 8–9)

**Goal:** Claude Code, Codex, Cursor, or OpenCode can read rac, with rac's AI off.

Tasks:

1. **Split browser control from the assistant.**
   - Today `AgentController` exists only when AI and browser control are both on (`ai.md:165-166`).
   - Create it when either the assistant's browser control or the Outside agents switch needs it.
   - The new pref `rac.agents.outside_access` defaults to false. Off means no controller, no socket, and no work.
   - Plan 03 decides where the controller lives (a profile `KeyedService`, per its Option 1/5).
   - About 4–6 days.
2. **The helper and socket** (plan 03 owns transport). A signed `Contents/Helpers/rac` with:
   - `rac mcp`: a stdio relay to a per-profile 0600 socket. Each client gets its own token, written into that agent's MCP config, revocable.
   - `rac skill`: prints the guide that matches this build, between begin and end markers (ego's rule).
   - A few verbs: `rac tabs`, `rac snapshot`, `rac text`, `rac find`.
   - MCP spec 2026-07-28, with `readOnlyHint`, `destructiveHint`, and `openWorldHint` on every tool.
   - About 5–8 days with plan 03.
3. **Settings › Outside agents** (UI by plan 01).
   - The switch, one-click "Add to Claude Code / Codex / Cursor / OpenCode", and copy-paste lines.
   - A connected-agents list with a level and a Revoke button per agent.
   - "Add" writes a skill stub to `~/.agents/skills/rac` and `~/.claude/skills/rac` only on click, never overwriting a user copy.
   - About 4–6 days.
4. **Pairing card.** On first connect, a card names the client. It uses the client's self-reported name plus, where macOS can tell, the signing identity of the helper's parent process. It says plainly that this is "best effort". The client starts at **read only** (05-D3). Synthetic Accessibility presses can't approve it (`digests/agent-stacks.md`, avoid list). 2–3 days.
5. **Cheaper reading.**
   - Splice deltas (`{base_rev, startLine, deleteCount, lines}`) replace the `- unchanged` lines (`snapshot_serializer.cc:694-728`).
   - `find` returns up to 20 refs.
   - `scope: viewport | full | subtree(ref)` with ego's compaction rules.
   - Cross-origin iframe content outside the named set becomes a labelled stub.
   - About 5–7 days.
6. **Rac-launched ACP agents use the same helper** with a token passed on an inherited descriptor, not a path visible in `ps` (T3's fd-3 pattern, `digests/t3code.md`, take 11). 1–2 days.

Acceptance:

- With AI off and the door on, `claude mcp add rac -- …/rac mcp` lists tabs and snapshots a page.
- With the door off, there is no socket file, no listener (`lsof`), and no controller (AI-off test set 2).
- A revoked client is refused on its next call.

Verification: screenshots of the Outside agents settings page, the pairing card, and the connected-agents list; a video of connecting Claude Code.

Patch surface: mostly rac-owned files. Expect about 2–4 upstream hunks for packaging the helper (`chrome/installer/mac/signing/parts.py` and its build entry) and about 2 for prefs and settings strings.

### M2. Agent spaces and the write tier (about 5–6 weeks)

**Goal:** an outside agent, or rac's own, works in its own background space. It never moves your tabs or takes focus. You can watch, take over, or stop it.

Tasks:

1. **Spike first (2–3 days): do hidden agent tabs keep rendering?**
   - Tabs in a non-active space are hidden WebContents.
   - Test APC extraction and actor tools there, with and without Chromium's capturer count.
   - Fallback: Nook's alpha-0 off-screen window (`digests/nook.md`).
   - The result picks 05-D5. If it fails, agent tabs live in an off-screen window, and the sidebar still shows them as an agent space.
2. **Agent space model** (UI with plan 01):
   - Each client gets one space, created on first use, owned by `agent:<client>`.
   - It shows as a distinct dot only while it has tabs.
   - Tabs are muted. They never activate the window or take focus.
   - Popups stay contained. Pages stay out of history.
   - Tabs close after 15 idle minutes and are never session-restored.
   - Page budget: 8 tabs per client.
   - About 10–15 days. This is the hot-files part (Views, session restore).
3. **Ownership states:** `user`, `agent:<client>`, and `handed_to_user`.
   - Any real input in an agent tab hands it to you and pauses the agent.
   - The agent gets a stable error with a reason (`user_in_control: manual_takeover`), with a different code for automatic hand-offs such as permission prompts (avoids ego #314).
   - Ways in and out: "Take over" / "Give back to <agent>" on the pill; "Share this tab with <agent>" / "Stop sharing" in the tab context menu (05-D4); "Stop all agents" in the menu bar.
   - About 4–6 days.
4. **One turn per session, not per profile.** A session is one client plus its space. The built-in assistant keeps its own session. Each session has its own guard state, named set, and step budget. About 5–7 days.
5. **Write tier for outside agents.** The user can raise a client to `ask`, `careful`, or `auto`. Raising it needs evals tier 1 green in that build. Risky steps always ask.
   - A card makes the agent's call wait up to 60 s. After that it returns `pending_approval` with a ticket, and the agent calls `wait_for_approval(ticket)`. With no answer, nothing runs.
   - With AI off there is no critic, so `careful` means every step is a card, and the card says so (`ai.md:559-560`).
6. **Tools** (each through the guard; `digests/agent-stacks.md`, take 3):
   - General `press_key`: Enter and submit stay risky; Escape, Tab, and arrows are free on named sites.
   - `hover`, `go_forward`, `reload`, and `wait_for` text.
   - `handle_dialog`: other tools refuse while a dialog is open. A `prompt` dialog is the user's step.
   - Action receipts: popups, dialogs, downloads, URL changes, and a splice delta, instead of a full snapshot.
   - Loop detection: a nudge after 3 identical failures.
   - About 6–9 days.
7. **Batched steps (`run_steps`, and `rac run` reading JSON on stdin).**
   - An ordered list of rac actions, waits, and a final snapshot.
   - It stops at the first failure or card, and returns per-step receipts.
   - Each step is guarded. A risky step gets its own card, never one card per batch.
   - This is data, not code (05-D7).
   - About 3–5 days.
8. **A static action label** (3–6 words) in the pill and the step rows. No glow and no looping motion. Honor reduced motion. 1–2 days.
9. **Eval tier 2** with real models, and the red-team set grows to 30–50 pages.

Acceptance:

- Two clients work at once in separate spaces while the user types in a third. Focus never moves (video).
- Take over and give back work from the pill and the context menu.
- Idle close happens at 15 minutes.
- Nothing is restored after a crash.

Patch surface: the largest. Estimate 15–30 upstream hunks in tab, Views, and session-restore files. Route them through single hooks into `chrome/browser/ui/rac/` so plan 03's hunk budget holds.

### M3. Sign-in modes and secrets (about 2 weeks; after plan 04's per-space partitions)

- **Three modes per agent space** (05-D6):
  - "Your sign-ins": the default partition, with honest copy that says "the agent uses your logins".
  - "No sign-ins": an in-memory partition, thrown away after.
  - "Agent sign-ins": a persistent partition where you sign in only to what the agent should use.
  - Built on Stedding's fixed `StoragePartition` per space, with Brave's restore prefix (`digests/long-tail.md`).
  - Outside agents start at "No sign-ins".
- **Payments and passwords are the user's step.** The card hands the tab to you ("Fill this yourself, then give it back"), with no Allow button (Nanobrowser's rule, `digests/agent-stacks.md`, take 8). 2–3 days.
- **Spike: fill a login by reference** through `password_manager` without Chrome's `ExecutionEngine` (open per `digests/chromium-agent-internals.md`). 3 days. Build it only if the spike passes.
- **JavaScript `evaluate`, optional,** only in "No sign-ins" spaces, read-only result, behind the client's level. Build it only if the maintainer wants it (05-D7).

### M4. Stable locators and recipes (about 3–4 weeks; after evals tier 2 is green)

- **Locators:** emit `loc=role:button[name="Save"]` only when it re-resolves uniquely to the same node. Accept `loc=` and `text=` targets, resolved to a ref and then guarded like a ref. 5–7 days.
- **Recipes** (05-D10):
  - After a good run, "Save as recipe" stores the steps as JSON: navigate, click or type by locator, named inputs, and a check that must pass.
  - Recipes are readable, editable, and deletable in Settings. Plan 04 owns where they live (the profile).
  - No credentials are stored.
  - Replay uses the same runner with no model, so it works with AI off, and every step passes the guard.
  - A failed check stops the replay. With AI on, the agent may propose a fix, shown as a diff for you to approve.
  - Authority is fixed at save time (read or write), as in Pomerado.
  - `run_recipe` is exposed on the door; `rac run recipe <name>` on the CLI.
  - About 10–15 days.
- **Pomerado:** don't embed it. It needs OpenAI to mint, ships its own Chromium, can't attach to rac, and breaks its API daily (`digests/pomerado.md`). Mention it in docs as a tool developers can use themselves.

### M5. Routines (about 2 weeks; after M4)

- **Now (free):** document scheduling with the user's own cron, launchd, or T3 Code calling `rac run recipe`. The CLI starts rac in the background if it isn't running.
- **Later:** native routines that run a recipe or an agent prompt on a schedule while rac is open.
  - Local only.
  - Overlapping runs are skipped.
  - A routine pauses if its space is gone.
  - Each routine has its own level, capped by its client's.
  - A risky step pauses the run and posts one macOS notification. No step is ever auto-approved (`digests/aside.md`, take 9).
- **While rac is closed:** only if plan 03 adds a helper with a launch agent (05-D11).

### Assistant track (parallel; about 3 weeks in total)

- **Warm ACP sessions** (05-D12). Keep the agent alive while its panel is open, with a 5-minute idle limit. Its MCP access is scoped to that session, and it is killed on AI off or Stop. This cuts the 15–25 s per message on follow-ups. It changes the "nothing outlives the run" rule in `ai.md:243-249`. 4–6 days.
- **Show agents' own models** in the picker. Each agent reports them in `session/new` (`ai.md:719-726`). 3–4 days.
- **Saved prompts with "/"** ("skills" in Dia, Yab, and Comet). 3–4 days.
- **Queue versus steer:** Enter queues, Cmd+Enter steers. 3–5 days.
- **Encrypt chat history at rest** with the key-store path (with plan 04). 2 days.
- **Subscriptions** (settled by policy, not a decision):
  - Connect only through the vendor's official CLI over ACP, or by the user's own agent driving rac through the door.
  - Never OAuth client reuse, first-party user agents, identity prompts, or billing blocks, as Aside does (`digests/aside.md`, "avoid"). Anthropic forbids third-party Claude.ai login (FACT, cited there).
- **Local models:** keep Ollama and LM Studio. Add Apple Foundation Models only if plan 03 adds a Swift helper (`digests/local-first-and-sidecars.md`, take 12). Local models obey planted text more often (Nook's eval, CLAIM), and the guard is deterministic, so no special case is needed. The eval tier 2 set must include one local model.
- **WebMCP page tools:** after the Helium sync to Chromium 156 or later, which has the permission-policy check. Show them as untrusted snapshot lines. Treat a call as a click on a named site; `consequentialHint`, or a missing `readOnlyHint`, makes it risky (`digests/chromium-agent-internals.md`, take 5).

### Evals and red team

**Tier 1, in CI once plan 06 compiles tests.**

- Guard tables as unit tests, covering every level crossed with every action class.
- Local fixture pages served by a test server.
- A fake OpenAI-compatible model that follows the planted instruction on purpose.
- Four graded outcomes per attack, after Nanobrowser: the attack was attempted, the gate's response, the simulated user's answer, and whether the fixture's "attacker" endpoint received the secret.
- The first cases:
  - the `auto` chain;
  - a hidden-text instruction;
  - a URL with a query string the model added;
  - a link whose `href` changes after the snapshot;
  - a cross-origin iframe;
  - a dialog trap;
  - a payment field;
  - a "copy my order number" legitimate case, which measures false cards.
- Ratchet: the attacker success rate may never rise. The false-card count is tracked.

**Tier 2, nightly or before each release, run by hand with the maintainer's keys.**

- 30–50 hostile pages, some adapted from BrowseSafe-Bench (MIT, credited).
- Against 3–4 models: one Claude, one GPT, one open-weight model, and one local model.
- Both run modes: direct and ACP.
- At least 3 runs each. Results go to a local JSON trace, modeled on `--actor-trace-path`.

**Capability.** Run ego's MIT benchmark harness with a rac adapter, with the same logins for every tool and 3 or more runs. Publish it only with that method stated.

**Outside agents.** The same fixtures, driven through `rac mcp` by a scripted MCP client. This proves that the door enforces the same cards.

### Proving AI off costs nothing

Test set 1 (M0) and set 2 (M1) run on a fresh profile with AI off and the door off. They check that:

1. `AiServiceFactory::GetForProfile` returns null, and no `AgentController` exists (browser test).
2. No `rac-agent-mcp` directory and no listening socket exist (`lsof -U`).
3. No child processes appear beyond Helium's baseline (process list diff).
4. No network requests carry the `rac_ai_chat` or `rac_ai_models` traffic annotations (net-log check).
5. No AI or agent WebUI loads, and no AI views are created (counters exposed to tests only).
6. Turning AI on and then off returns to that state: requests cancelled, processes gone, socket removed.
7. With the door on and AI off, there is still no `AiService` and no provider traffic. Only the controller and the socket exist.

Plan 06's performance bench adds startup, tab switching, scrolling, and typing, compared with Helium, with AI off and with AI on but idle. Measure the idle cost of Chromium's own `ActorKeyedService` objects, but don't disable `kGlicActor`: the renderer `CHECK`s it (`digests/chromium-agent-internals.md`).

## Fit with the non-negotiables

- **Private:** holds. There is no relay, account, telemetry, or rac endpoint. Evals use the maintainer's own keys. Recipes and routines are local. Pomerado is not embedded, because it sends pages to OpenAI.
- **Never slower than Helium:** holds when everything is off. Agent spaces render hidden tabs only while an agent works, and they close after 15 idle minutes. Warm ACP sessions keep one process alive while the panel is open; that is bounded by the idle limit. Measure all of it.
- **AI off costs nothing: bent, on purpose (05-D2).** VISION says "When AI is off, none of its code does any work." With the door on and AI off, agent code (controller, guard, socket) runs. I propose new wording: "Every feature that is off costs nothing." The door is its own feature, off by default. This needs the maintainer's sign-off and a VISION edit.
- **Cheap to update:** M0, M1, M4, and M5 are mostly rac-owned files. **M2 bends it:** agent spaces add Views and session-restore hunks in hot files. Keep them behind single hooks, and count them against plan 03's budget. Avoid Chrome's `ExecutionEngine` and Glic, which churn daily.
- **Calm UI:** holds. The ring, pill, and label are static. There is no glow or idle loop, and reduced motion is honored. Cards keep "no default button, no Allow shortcut".
- **Opinionated:** two new settings (Outside agents, per-client level). Sign-in mode is a per-space choice, not a global setting.
- **GPL:** take ideas only from AGPL BrowserOS. Ego's SDK and benchmark harness are MIT; Nanobrowser is Apache-2.0; BrowseSafe-Bench is MIT. Credit each where it's used.

## Dependencies on other plans

- **01 ui-shell:** the agent space dot and tab list, the Outside agents settings page, the pairing card, take-over controls, the "/" prompts UI, and the queue/steer composer.
- **02 visual-design-and-motion:** the card motion, a static acting marker, the agent-space dot style, and reduced motion.
- **03 core-architecture:** owns the process model, the socket and helper transport, the token and peer-identity scheme, where `AgentController` lives, the "one service, many doors" contract, and whether a helper exists (which gates routines while closed and Foundation Models). This plan asks 03 for:
  - a per-profile socket that exists only while the switch is on;
  - per-client revocable tokens;
  - working with agents that keep their sandbox on;
  - a transport-neutral tool contract.
- **04 data-storage-import-sync:** per-space `StoragePartition` (needed for M3), agent run history (one row per tool call, with retention), encrypted chat history, and recipe storage.
- **06 engineering-and-shipping:** CI that compiles and runs `rac_agent_unittests` and eval tier 1, release-build gating of dev switches, the perf bench, and the Helium sync (Chromium 156 or later is needed for WebMCP; the M158 API breaks are in `digests/chromium-agent-internals.md`).
- **07 power-features:** a command bar that shares the same action table as the agent tools; Boosts' JavaScript never runs on sensitive-list sites.

## Risks and unknowns

- **Hidden-tab rendering** may need Nook's off-screen-window trick. That changes the M2 UI (spike first).
- **Sandboxed agents and Unix sockets.** ego says sandboxed agents can't reach its socket (#188). INFERENCE: MCP servers started by Claude Code run outside its Bash sandbox, so `rac mcp` works while the shell CLI may need a socket allowlist. Verify with Claude Code and Codex, sandbox on.
- **Peer identity is weak.** macOS may only name rac's helper. The same user is the real boundary, and the card must say so.
- **More cards at `auto`.** The data-flow rule will fire on some legitimate copy tasks. Tier 1 tracks false cards. Tune the rule, never the risky list.
- **Fixes not proven live.** The `auto` chain and the CDP doors are confirmed from code, not from runs. The main build tree predates agent patches 13–17.
- **Concurrent sessions** may expose single-turn assumptions in `AgentController`, as in the history in `ai.md:262-272`.
- **Locators may not survive redesigns,** so recipes can break. Stop and show it; never guess.
- **Upstream churn.** Chromium's actor layer changes about 7 times a day. M158 has 2 compile breaks and about 4 failed hunks (low risk).
- **Effort.** About 90–130 agent-days is a lot next to the Arc deadline. Only M0 is needed before the first release.

## Open questions

1. Do `claude mcp login` and `codex mcp login` need loopback HTTP with OAuth, or is a stdio relay with a config token enough? (Shared with plan 03.)
2. Should the built-in assistant also get "read only" as a level, for chat-only users who want page reading without clicking?
3. Is "Agent sign-ins" worth building, or are "Yours" and "None" enough?
4. Should a shared user tab return to the user automatically when the agent's turn ends?
5. Should routines notify through macOS notifications, the sidebar, or both?
6. Should the Anthropic `browser_toolset_20260801` contract be offered to Claude on the direct provider? (Deferred: it is coordinate-based and needs hit-testing into the guard; `digests/agent-stacks.md`, take 9.)
7. Can `components/origin_gating` carry rac's named sets without Glic, or should rac keep its own table? (Default: keep rac's own.)
8. Should the eval results be published on racbrowser.com as a security page?

## Draft thread brief

**DRAFT. Do not launch until the maintainer approves plan 05 and its decisions.**

> **Thread: agents and AI (plan 05).** You are building rac's agent overhaul in feature worktrees, following `plans/05-agents-and-ai.md` and the maintainer's answers to 05-D1 through 05-D12. Read `AGENTS.md`, `VISION.md`, `docs/internals/ai.md`, and `patches/rac/agent/` first.
>
> Order: M0 (safety floor), then M1 (read-only door), then M2 (agent spaces and the write tier), then M3–M5. The assistant track runs in parallel. Start M2 only after the hidden-tab rendering spike reports. Start M4 only after eval tier 2 is green.
>
> Rules:
> - Every tool call from every client enters `AgentController::HandleToolCall` and the guard.
> - No level skips the risky list.
> - No raw CDP or script runner on a logged-in profile.
> - The door's switch is off by default. With it off, nothing listens.
> - Coordinate transport with the plan 03 thread and partitions with plan 04. Don't build them yourself.
> - Keep upstream edits to single hooks.
> - One feature per patch group, under `patches/rac/agent/` or new groups such as `patches/rac/agent-door/` and `patches/rac/agent-spaces/`.
>
> Proof:
> - Every PR carries unit tests and the eval tier 1 result.
> - Every UI change carries screenshots from `devutils/rac/worktree.sh run` (light and dark, sidebar full and hidden, reduced motion), plus a video for motion and focus behavior.
> - Run only `rac_agent_unittests` and `rac_ai_unittests`.
>
> Models: UI and cards go to Claude Opus. Guard, controller, and concurrency go to Claude Opus. Tool additions and fixtures can go to Sonnet or a strong open-weight model, reviewed by Opus.
>
> Open PRs only when the maintainer asks. End each PR body with the model and tool used.
