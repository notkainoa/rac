# 05. Agents and AI

You only need to read the first two sections. The rest is detail for the build thread.

## In plain English

rac's AI already has a side panel, Ask in the new tab page and in Find, link summaries, and an agent that clicks and types. The agent's default level, `auto`, has a hole. A hostile page can make the agent copy your mail into that page. This plan closes the hole first, with tests that attack it.

You will notice the fix. On one site, `auto` acts without asking. Once the agent has read a second site, it asks once before acting on each site.

Developers can also let their coding agent drive rac. A separate "Outside agents" switch, off by default, turns this on, even with AI off. A new outside agent can only read tabs you share. Later it can act in its own background tabs, which have no logins. Risky steps always ask.

AI stays off by default, and nothing phones home.

```mermaid
flowchart TD
  A["The agent wants to take a step that changes something"] --> N{"Is the site set to Never?"}
  N -->|"yes"| X["Refused"]
  N -->|"no"| R{"Is the step on the risky list, such as Enter, a password, or buy?"}
  R -->|"yes"| CARD["Confirm card"]
  R -->|"no"| L{"Which level?"}
  L -->|"ask"| CARD
  L -->|"careful"| P["A plan card once, then a safety check on each step"]
  L -->|"auto"| T{"Taint rule. Has it read two or more sites, and could this step carry what it read?"}
  T -->|"yes"| CARD
  T -->|"no"| GO["The step runs"]
  P --> GO
  CARD -->|"Allow once, or allow this site for the conversation"| GO
  CARD -->|"Don't allow"| X
```

## What you need to decide

| Id | Question | Options | Recommended |
| --- | --- | --- | --- |
| 05-D1 (D19) | How do we close the `auto` hole? | The taint rule; make `careful` the default; both | The taint rule, and keep `auto` the default |
| 05-D2 (D26) | What does a newly connected outside agent get? | Read tabs you share; act in its own no-login tabs; act in your tabs at your level | Read shared tabs. You can let it act in its own tabs |
| 05-D3 (D23) | Where does an agent do its work? | An Agents section in the sidebar; its own space; an off-screen window | The Agents section, if the rendering spike passes |
| 05-D4 (D56) | May outside agents run JavaScript in pages, as ego does? | Never; step lists only; JavaScript only in no-login agent tabs | Step lists now, and no-login JavaScript maybe later |
| 05-D5 (D25) | Which ways in for outside agents? | MCP; a `rac` command with a skill; both | Both, through one relay, MCP first |
| 05-D6 (D20) | What about Chromium's own debugging ports? | Refuse them on the real profile; leave them; add an expert switch | Refuse them, with no new setting |
| 05-D7 (D12b) | How does VISION.md describe outside agents? | Keep "AI off costs nothing" and add a separate promise; reword the AI rule | Add the separate promise |
| 05-D8 (D57) | Use Pomerado for repeat tasks? | Embed it; build native recipes later; neither | Don't embed it. Build native recipes after the evals pass |

- 05-D1. Once the agent has read two sites, the taint rule asks before any step that could carry what it read.
- 05-D3. If the spike fails, the off-screen window is the fallback.
- 05-D4. ego is another agent browser, and its scripts can read every cookie. A step list is a short list of tool calls that rac checks one at a time.
- 05-D5. MCP is the standard way coding agents call tools. A skill is a short file that teaches an agent the `rac` command.
- 05-D6. Dev runs use their own profile folder, so your DevTools screenshot flow keeps working.
- 05-D8. Pomerado replays a recorded task, but it needs OpenAI and its own Chromium. The evals are rac's attack tests.

Other plans decide the warm agent (03-D3) and how outside agents connect (03-D2). This plan owns routines while rac is closed (D59).

## Where we are today

**Built** (FACT, `docs/internals/ai.md`, `plans/research/digests/rac-baseline.md`):

- **Providers:** your own key, local models (Ollama, LM Studio), and ACP agents (Claude Code, Codex, Cursor, and others).
- **Agent:** 15 tools; APC snapshot lines like `- button "Sign in" [ref=e6] [submit]`; never-reused refs; TOCTOU re-checks; containment; a page-blind critic at `careful`; cards; a ring and pill; a 25-call cap.
- **Size:** 19 patches, touching 21 upstream files and 58 hunks (`digests/chromium-agent-internals.md`).
- **Levels:** `ask`, `careful`, and `auto` (the default), plus per-site Always/Never rules.

**Gaps** (FACT unless tagged):

- **The `auto` hole.** At `auto`, a cross-site navigation and typing model text into the attached tab are both free. The test `AutoAsksOnlyForRiskAndForeignTyping` asserts this (`patches/rac/agent/13-permission-levels.patch:329-370`). The exploit has not been run (`matrices/agents.md`).
- **The guard trusts only chat messages.** "Named" sites, "the user's own words", and URL provenance all come from `BeginTurn(level, user_messages, origins)`. An outside agent's prompt never reaches rac, so none of these signals exist for it.
- **Three fail-open defaults:**
  - `ParsePermissionLevel` reads any unknown string, including `"bypass"`, as `kAuto`.
  - The guard's `level_` member starts as `kAuto` (13-patch, lines 35-42, 204, 411-416).
  - A site rule that isn't exactly `"always"` or `"never"` is dropped silently (`14-site-rules.patch:389-399`).
  - The risky list is checked before the level, so no string skips it.
- **Unguarded doors.** `--remote-debugging-port` and `--remote-debugging-pipe` on the default profile are refused only in Google-branded builds. `chrome://inspect` remote debugging is off by default: it needs a user toggle, and each connection needs approval (`remote_debugging_server.cc`). Browser Harness clicks that approval sheet through Accessibility (`digests/agent-stacks.md`).
- **Also:** dev switches such as `--rac-window-screenshot-requests` ship ungated. There is no outside door, and AI off removes the MCP server (`ai.md:307-331`). No evals exist; one test covers "AI off". `press_key` is Enter only, and deltas cost about 1,800 tokens for 3 changes (`digests/agent-stacks.md`). Onboarding promises the AI "never acts … without your confirmation".

## What others do

Full tables are in `plans/research/matrices/agents.md`.

- **ego(lite):** your coding agent writes one script per call, through a skill and a shell command. Agent Spaces never steal focus, though leaks were fixed "case by case". It refuses raw CDP outside agent-owned Spaces (#285). Its scripts can still read every cookie (#315). It claims 44% fewer rounds than one call per step (CLAIM). Its benchmark: 93.5% success, 26.5 turns, $1.64 per task on 31 tasks (CLAIM, `digests/ego-lite.md`).
- **Aside:** a CLI, a 4-tool MCP, a skill install, and agent tabs that close after 15 idle minutes. Its guard defaults to allow. It impersonates Claude Code to use Claude subscriptions (`digests/aside.md`).
- **Chrome and Yab:** data-flow rules. Chrome lets data read on one origin flow only to origins the user made writable; Yab asks before mail's words go to a new site (`digests/closed-ai-browsers.md`).
- **Nanobrowser:** the best eval template. It uses hostile fixture pages, a fake model, and four graded outcomes (`digests/agent-stacks.md`).
- **Pomerado:** it records a task once and replays it with no model. It needs OpenAI to record and its own Chromium, and it can't drive rac (`digests/pomerado.md`).

## Options

Every option starts with the safety floor (M0). The costs below are plan-05 agent-days only. Plan 03's transport and controller split, and plan 04's partitions, are counted in those plans.

### Option A: Safety floor only

**In plain English.** Fix the hole, close the debug doors, and add attack tests. Developers still can't drive rac.

- **Effort:** about 18–25 days. **Pros:** smallest; fits the launch. **Cons:** ignores the Aside and ego demand; developers keep using raw CDP, which has no guard.

### Option B: Floor plus a read-only door

**In plain English.** Outside agents can read the tabs you share with them, and nothing more.

- **Effort:** about 37–52 days. **Pros:** a useful developer story at low risk to accounts. **Cons:** page text still goes to the agent's vendor, and agents can't do tasks.

### Option C: Floor plus a full door and agent workspaces (recommended)

**In plain English.** On top of B, an agent can be allowed to act. It works only in its own background tabs, which start with no logins. Every step goes through the guard, and steps can be batched.

- **Effort:** about 87–126 days in total. **Pros:** answers Rhys Sullivan's complaint about Aside; brings ego's reach to rac's guard. **Cons:** the most work; concurrent sessions need a controller refactor; hidden-tab rendering is unproven.

### Option D: Floor plus a scoped-script door (ego's own model)

**In plain English.** Outside agents send JavaScript programs. These run only in no-login agent tabs, with CDP scoped to those tabs, as ego does after #285.

- **Effort:** about 77–107 days. **Pros:** fewest rounds; ergonomics agents already know. **Cons:** isolated-world scripts fire synthetic clicks and `fetch()` with no guard, so scripting is safe only where there is nothing to steal. That rules out the logged-in tasks people want ("my GitHub"). A script API is hard to take back.

**Recommendation: C.** Take from D the cheap parts: batched steps with a read-only `extract`, stable refs between calls, and the self-printing skill. Offer scoped JavaScript in no-login tabs as an optional M3 item (05-D4). D on its own fails people's logged-in tasks, and B stalls at reading.

## Recommended plan

**Calendar.** Days are counted from the maintainer's approval (day 0, Wed 10-28; `plans/rulings.md`, ruling 1). The master plan's closing table owns the timing. The launch build starts on day 13 (launch merges close at the start of day 13), and launch is day 19. The 12-15 hard stop and Arc's shutdown on 2026-12-22 are safety margins. Plan 06 owns the Helium sync to Chromium 156 (its M2) and the launch (its M5).

- Only M0 is a launch gate.
- Work in rac-owned files may be built on 154 and rebased.
- Hunks in hot upstream files are written on the 156 base, tagged about day 4 (D62), and rebased onto `main` when the sync merges, about day 7.

Every UI item ships screenshots from `devutils/rac/worktree.sh run`, in light and dark, with the sidebar full and hidden. Motion gets a video and a reduced-motion check.

**AI-off check** (ruling 16). With AI off, no AI button, row, or label appears anywhere. That includes the command bar. The door's UI is labelled "Outside agents", never "AI".

### M0. Safety floor (days 0–12; launch gate; guard on 154, then rebased onto 156)

**Goal:** no tested variant of the exfiltration chain gets through `auto`, and every default fails closed.

**Tasks:**

1. **The taint rule (05-D1), 4–6 days.**
   - **Read set.** Each conversation keeps a set of origins whose content reached the model. That includes snapshots, page text, and find results. It also includes tabs attached at the start of a turn, and pages read in earlier turns of the same conversation, because the model still holds them.
   - **Escalation.** Once the read set has two or more origins, any action that can carry model-chosen information asks, on any origin. That covers typing text that isn't in the user's messages, `select_option`, clicks, and navigation by link. These stay free:
     - reads, scroll, wait, and switch tab;
     - navigation to a URL the user typed exactly;
     - typing the user's own words.
   - **The card.** It names the destination and the sites read. It offers Allow once / "Let it act on b.com using what it read on a.com" (for the rest of the conversation) / Don't allow. This is Chrome's origin-set idea, reduced to one grant per destination.
   - **Submit cards** now show the values the agent typed into that form, except passwords. This covers same-site leaks, which need a submit.
   - Allow once is only as good as the user's reading of the card. The card keeps "no default button, no Allow shortcut".
2. **Drop my earlier first-visit rule for the built-in agent.** The taint rule closes the chain without it, at fewer cards. A first visit still asks for outside clients (M1).
3. **Fail closed everywhere, 1 day.**
   - The `level_` member starts as `kAsk`.
   - An unknown level name parses to `ask`.
   - A malformed site rule becomes Never.
   - The pref accepts only the allowed values.
   - Outside-client levels parse to read only.
   - Add a test for each.
4. **Mark page text for every model, 1–2 days.** Use tool-named boundaries, escape fake markers, and neutralize role tags (including spaced letters). Never skip this for "strong" models (`digests/aside.md`, take 6).
5. **Debug doors (05-D6).** The Core thread builds this inside M0, on 156, on days 4–10 (the 156 base).
   - Refuse `--remote-debugging-port` and `--remote-debugging-pipe` on the default profile.
   - Turn the `chrome://inspect` approval feature off, with no new setting.
   - Verify on a build first. Dev runs pass `--user-data-dir` (`dev.sh:132`, `worktree.sh:206`), so the maintainer's DevTools-port screenshot flow should keep working.
6. **Gate dev switches out of release builds,** with plan 06. 1 day.
7. **Eval tier 1** (below), 8–11 days.
8. **AI-off tests, set 1** (below), 2–3 days.
9. **Fix copy:** the onboarding promise, the site's "It asks before it acts", and the `ai.md` table. Half a day.

**Acceptance:**

- Tier 1 fixtures stop at a card for every variant listed under "Evals" below. The false-card budget holds.
- Unit tests cover every fail-closed default.
- The worktree posts green `rac/unit-tests` and `rac/agent-evals` statuses (plan 06 M4 task 2).

**Budget.** About 18–25 days, spread over the guard, evals, and doors streams on days 0–12. It needs one worktree build on 154, after step 0 in the master plan brings the base tree up to date. Doors move to the 156 base from day 4. All builds go through the D63 queue.

**Patch surface:** rac-owned files only. This milestone adds about 2 hunks for the doors.

### M1. Read-only door (days 14–30; ships in a point release; Chromium 156; not a launch gate)

**Goal:** Claude Code, Codex, Cursor, or OpenCode can read the tabs you share, with rac's AI off. This milestone and plan 03 M2 are one milestone: the door. Plan 03 M2 provides the relay, socket, tokens, and listener lifecycle. Plan 03 M1 splits the controller and guard out of `AiService`. That split runs on days 13–22 and lands after launch.

**The trust root for outside clients** (ruling 8). rac never sees an outside agent's prompt. These rules replace the chat-message signals:

| Signal | Built-in agent | Outside client |
| --- | --- | --- |
| Named origins | Attached tab, URLs in messages, plan, Always rules | Tabs you shared with this client, Always rules, origins you approved on this client's cards |
| "The user's own words" | Text in the user's messages | None. Every typed string counts as model text |
| URL provenance | URL from a message or a shown link | A shown link, or a URL you approved on a card that shows it in full |
| First visit to a new origin | Free (the taint rule guards it) | Asks in tabs with your logins; free in no-login tabs |
| Levels | `ask`, `careful`, `auto` | Read only (default), `ask`, `auto`. No `careful`: its critic needs the user's goal, which rac doesn't have |
| Read set | Per conversation | Per client, kept until you reset it on the client's row, because the agent keeps its own memory. Reads in no-login tabs don't count: they hold no secrets of yours |

Under these rules, outside `auto` means: free on named origins and in no-login tabs; the taint rule applies; risky steps always ask. Tier 1 gets a fixture for each row.

**Tasks:**

1. **Outside-client policy in the guard,** per the table. 3–4 days.
2. **Read tools only,** taken from plan 03's action table: `snapshot`, `get_page_text`, `find` (returns up to 20 refs), and `list_tabs` (shared tabs only, never your private ones). Each carries MCP annotations. The ref table lives per client in the browser, so refs survive between CLI calls (ego take 7). 1–2 days.
3. **Cheaper reading:** splice deltas (`{base_rev, startLine, deleteCount, lines}`), `scope: viewport | full | subtree(ref)` with ego's compaction, and cross-origin iframes outside the named set shown as labelled stubs. 5–7 days.
4. **Sharing:** "Share with <agent>" and "Stop sharing" in rac's site control center (a rac-owned surface, so no hot tab-menu hunk), plus a static marker on shared tabs. 3–4 days, drawn by plan 01.
5. **Pairing card and connected-agents list** (plan 01's Settings > Outside agents).
   - The card names the client. It says plainly that identity is best effort and that the boundary is your macOS user.
   - It says: "This agent's model provider will see the text of tabs you share."
   - "Outside agents: on" shows next to the AI switch while the door is on (ruling 15).
   - 2–3 days.
6. **Connecting.**
   - By default, Settings prints each agent's command (`claude mcp add rac -- …/rac mcp`) and the skill install line. It writes no files.
   - "Write it for me" writes a file only on click, and never overwrites one.
   - The card says that a client token stored in an agent's config can be read by any process of the same user.
   - `rac skill` prints this build's guide (ego's pattern). 1–2 days.
7. **Requirement docs with acceptance tests** for the door, in `docs/internals/ai.md`, a habit taken from ego (take 10). 1 day.
8. **Door evals and sandbox tests.** Tier 1 fixtures run through a scripted MCP client. Claude Code and Codex connect with their sandboxes on. 3–4 days.

**Acceptance:**

- With AI off and the door on, Claude Code (sandbox on) snapshots a shared tab, and can't see an unshared one.
- With the door off, there is no socket, no listener, and no controller (AI-off set 2).
- A revoked client is refused.

**Budget:** about 19–27 days. M1 slips if plan 01's Settings > Outside agents isn't ready; otherwise M1 ships a minimal page.

### M2. Agent workspace and the write tier (days 25–45; Chromium 156)

**Goal:** an outside agent, or rac's own, acts in background tabs that never move your tabs or take focus. You can watch it, take over, or stop it. Plan 01 designs the Agents section by day 3 and builds it in the same days (ruling 5).

**Tasks:**

1. **Rendering spike, 3–4 days.** Hidden tabs throttle timers, pause `requestAnimationFrame`, stall lazy loading, and starve `IntersectionObserver`.
   - **Pass condition:** 10 of ego's benchmark tasks succeed as often in hidden agent tabs as in visible ones.
   - If it fails, agent tabs move to an off-screen window. Nook does this at alpha 0. The sidebar shows them the same way.
2. **Agent tabs (05-D3), 8–12 days.**
   - One group per client in the Agents section (05-D3, plan 01 M5), shown only while the client has tabs.
   - Tabs are muted. They never activate the window or take focus. Popups stay contained, and pages stay out of history.
   - Tabs close after 15 idle minutes and are never session-restored.
   - Agent tabs are exempt from space unload and tab discard.
   - Page budget: 8 tabs per client.
3. **No-login tabs by default for outside clients.** They use an in-memory partition, thrown away afterwards. Plan 04 builds this as an in-memory variant of its partition hook (04 after-launch item 2, D46), right after launch. This milestone builds agent tabs for the built-in agent and "use my logins" first, and turns on the outside write tier when the in-memory partition lands. Both touch `browser_navigator.cc` and session restore, so Data and Core take turns there. Until then, the write tier stays off for outside clients. "Use my logins" is a per-client choice on the connected-agents list. 1–2 days of hookup here.
4. **Ownership states, 3–5 days:** `user`, `agent:<client>`, and `handed_to_user`.
   - Real input hands the tab to you.
   - The agent gets a stable error with a reason, and automatic hand-offs get their own code (avoids ego #314).
   - Take over / Give back on the pill; Stop all agents in the menu bar.
5. **One turn per session,** where a session is a client plus its tabs. The built-in assistant keeps its own session. 5–7 days.
6. **Write tier and approval home, 4–6 days.**
   - A user can raise a client to `ask` or `auto` only in a build with tier 1 green.
   - A pending card shows as a "Needs you" badge on the client's row and as a dot on the edge-reveal strip when the sidebar is hidden. When rac isn't frontmost, it also gets a dock badge and one local macOS notification.
   - Agent calls wait for an answer up to a limit set below the client's MCP tool timeout. Check the Claude Code and Codex defaults. After the limit, the call returns `pending_approval` with a ticket, and the agent calls `wait_for_approval`.
7. **Tools, 6–9 days:**
   - general `press_key` (Enter stays risky);
   - `hover`, `go_forward`, `reload`, and `wait_for` text;
   - `handle_dialog`: other tools refuse while a dialog is open, and a `prompt` dialog is the user's step;
   - action receipts (popups, dialogs, downloads, URL changes, and a splice delta) instead of full snapshots;
   - a loop nudge after 3 identical failures.
8. **Batched steps, 4–6 days.** `run_steps`, and `rac run` reading JSON on stdin.
   - An ordered list of actions, waits, a final snapshot, and a read-only `extract` (text, table, or links of a ref) that returns data without another round.
   - It stops at the first failure or card. Each step is guarded, and each risky step gets its own card.
9. **Non-page actions,** classified in plan 03's table (below). 1–2 days.
10. **A static action label** (3–6 words) in the pill and the rows. 1 day.
11. **Focus regression suite, 2–3 days.** A popup, `alert`, a permission prompt, `window.focus()`, a download, a file chooser, and a notification, each from an agent tab. None may move focus or the window.
12. **Eval tier 2 and the ego harness, 6–9 days plus model spend.** See below.

**Acceptance:**

- Two clients work at once while the user types in another tab. Focus never moves (video plus the regression suite).
- Approval works with the window unfocused and the sidebar hidden.
- Ego harness targets hold.

**Budget:** about 44–66 days. Patch surface: plan 01's Agents section plus about 6–12 hunks in tab-strip and session-restore hooks. That is fewer than a new space type would need. Count them against plan 03's budget.

**Non-page actions for outside clients:**

| Class | Actions |
| --- | --- |
| Read | List spaces, list the client's own and shared tabs |
| Free in own tabs, asks elsewhere | Open, close, and reload a tab |
| Always asks | Move a tab to a space, pin or unpin, archive, create or edit a Boost, a route, or a bang override (plan 07's rule) |
| Never | Change settings, site rules, or levels; install extensions; clear history or data; delete a space |

### M3. Secrets and the optional script mode (days 45–55)

- **Payments and passwords are the user's step.** A hand-off card says "Fill this yourself, then give it back", with no Allow button (Nanobrowser's rule). 2–3 days.
- **"Agent's own logins":** a persistent identity from plan 04's partition work (after-launch item 2), chosen per client. 1–2 days.
- **Spike: fill a login by reference** without Chromium's `ExecutionEngine`. 3 days.
- **Optional, if 05-D4 allows it:** JavaScript `evaluate` in no-login agent tabs only, with a read-only result and scoped to that client. 4–6 days.
- **Budget:** about 6–8 days, plus 4–6 if the script mode is approved.

### Evals and red team

**Tier 1a: guard tables as unit tests** in `rac_agent_unittests`. These run on every PR through plan 06's `rac/unit-tests` status (06 M4 task 2). Every level crossed with every action class, for both built-in and outside clients.

**Tier 1b: fixture runs on a built worktree.** A runner in `devutils/rac/evals/`:

- launches the app through `worktree.sh run` with a throwaway profile;
- serves hostile fixture pages on localhost;
- points the Custom provider at a fake OpenAI-compatible model on localhost (already allowed, `ai.md:662-667`) that follows the planted instruction on purpose;
- posts `rac/agent-evals` the way 06 M4 task 2 does.

No new browser-test target is needed. Each attack gets four graded outcomes: the attack was attempted, the gate's response, the simulated user's answer, and whether the attacker endpoint received the secret. A committed baseline file is the ratchet: attacker successes may not rise.

The first fixtures are the canonical chain, plus the variants that survive a typing-only fix:

- a link "keyboard" (one link per character) and a `select` keyboard;
- a same-origin leak through a submit;
- content from a tab attached at turn start, and from an earlier turn.

Then: a model-added query string, an `href` that changes after the snapshot, a cross-origin iframe, a dialog trap, a payment field, and one fixture per outside-client trust row.

**False-card budget,** checked in tier 1b:

- a read-only research task across 3 sites the user named: 0 cards;
- the same task reached by links: at most 1 card per site the agent acts on;
- "copy my order number from a.com into b.com's form": 1 data-flow card plus the submit card.

**Tier 2, before each release, run by hand with the maintainer's keys.** 30–50 hostile pages, some adapted from BrowseSafe-Bench (MIT, credited). Run against one Claude, one GPT, one open-weight model, and one local model, in direct and ACP modes, 3 runs each.

**Ego's benchmark harness (MIT)** gets a rac adapter, with the same logins for every tool, 3 runs each. Targets on the 31 tasks:

- success within 10 points of ego in the same setup;
- a median of no more than 35 turns;
- cost no more than 1.5× ego's.

Publish the results only with the method stated.

### Proving AI off costs nothing

Run on a fresh profile with AI off and the door off. Set 1 lands in M0; set 2 adds the door checks in M1. All checks use the tier 1b runner.

1. No `AiService` and no `AgentController` exist.
2. No `rac-agent-mcp` directory and no listening socket (`lsof -U`).
3. No child processes beyond Helium's baseline.
4. No requests with the `rac_ai_chat` or `rac_ai_models` traffic annotations (net-log).
5. No AI buttons, rows, or labels on any surface (screenshots, including the command bar).
6. Turning AI on and then off returns to this state.
7. With the door on and AI off: no `AiService`, no provider traffic, and no AI labels. Only the controller and the socket exist.

Plan 06's bench measures startup, tab switching, scrolling, and typing against Helium. Plan 03 M0 measures the idle cost of Chromium's `ActorKeyedService`. Don't disable `kGlicActor`: the renderer `CHECK`s it.

### Later (no milestone yet)

- **Native recipes** (05-D8), after tier 2 is green and stable locators exist. "Save as recipe" stores a run's steps as editable JSON (locators, named inputs, a check that must pass). Replay uses no model, works with AI off, and runs every step through the guard. Authority is fixed at save time. Storage is a profile file, with plan 04. About 15–22 days. Pomerado is not embedded: it needs OpenAI to record, ships its own Chromium, and can't attach to rac.
- **Routines.** First, document using cron, launchd, or T3 Code with `rac run recipe` (free). Then native routines while rac is open, where a risky step pauses the run and notifies. While rac is closed: see D59 in decisions.md (not planned; no helper).
- **WebMCP page tools** on Chromium 156 or later, treated as untrusted clicks.
- **A small sensitive-site list** that Always rules can override. Cut from M0: it is open-ended and fights `auto`.
- **Assistant extras:** agents' own models in the picker, "/" saved prompts, and queue versus steer. The warm agent is 03-D3. Encrypted history is plan 04's after-launch item 3 (04-D7).
- **Other channels.** AppleScript is not an agent channel. If plan 07 adds it, it exposes only the action table's Read and safe space actions. DevTools-over-MCP isn't offered; developers use a separate profile.
- **Subscriptions:** only through the vendor's CLI over ACP, or through the user's own agent driving the door. Never client impersonation (`digests/aside.md`).

## Fit with the non-negotiables

- **Private:** holds. No relay, account, telemetry, or rac endpoint. The pairing card says the agent's vendor sees shared page text. Evals use the maintainer's own keys.
- **Never slower than Helium:** holds with everything off. Agent tabs cost only while working, and they close after 15 idle minutes. M2's hidden rendering is measured.
- **AI off costs nothing:** kept as written (ruling 15). The door is a separate promise: its own switch, off by default, and when off it costs nothing. While it is on, "Outside agents: on" shows next to the AI switch.
- **Cheap to update:** M0 and M1 are rac-owned files. M2 bends it, with about 6–12 hunks in hot tab and restore files. They wait for the sync, go behind single hooks, and count against plan 03's budget.
- **Calm UI:** static ring, pill, marker, and label. No glow, and reduced motion is honored.
- **Opinionated:** one new switch. Per-client level and logins live on that client's row, not as global settings.
- **GPL:** ideas only from AGPL BrowserOS. Ego's SDK and harness are MIT, and BrowseSafe-Bench is MIT; credit both.

**VISION and doc edits for 05-D7** (they need sign-off):

- Add to VISION: "Outside agents is a separate switch, off by default. While it is off, nothing listens. While it is on, an agent you connect can read tabs you share. If you allow it, it acts in its own tabs. Every risky step still asks."
- Also update: AGENTS.md's "AI off" checklist item, the `ai.md` "AI off costs nothing" and "Not built yet" sections, and plan 01's "AI surfaces exist only with AI on" exception.

## Dependencies on other plans

- **01:** draws the Agents section (05-D3, plan 01 M5, scheduled with M2), Settings > Outside agents (M1), the pairing card, the sharing control, and the approval badges.
- **02:** card motion, the static marker, and reduced motion.
- **03:** the action table (ruling 2), the controller and guard split (its M1), the relay, socket, and tokens (its M2), and the warm agent (03-D3). The debug doors are built here, in M0.
- **04:** the in-memory and persistent agent partitions (after-launch item 2, D46), the run and tool-call audit log, and storage for recipes.
- **06:** the posted test statuses (06 M4 task 2), release gating of dev switches, the bench, the sync, and the launch calendar.
- **07:** the card rule for Boosts, routes, and bang overrides; the AppleScript limits above.

## Risks and unknowns

- **The taint rule adds cards** to legitimate multi-site tasks. The false-card budget is the check. Tune the grant wording, never the risky list.
- **Residual leaks:**
  - live-collaboration pages on the same origin (shared docs show typing without a submit);
  - low-bandwidth channels such as scroll timing.
  - Document both. They are not fixable without a network policy (`ai.md`, "Open concerns").
- **Outside agents keep their own memory,** so their read set never resets by itself. That makes `auto` card-heavy in tabs with your logins. No-login tabs are the intended home.
- **Hidden rendering** may force the off-screen window.
- **Plan 04's in-memory partition** may arrive late (after-launch item 2), which holds back the outside write tier.
- **Sandboxed agents** may not reach the socket (ego #188). M1 tests this.
- **Peer identity is weak.** Same-user is the boundary.
- **Effort:** about 87–126 days for M0–M3, plus later items. Only M0 must be merged for the launch build (cutoff: the start of day 13).

## Open questions

1. Should Enter in a search box in a no-login agent tab still ask? Today the risky list says yes, and this plan keeps it.
2. Should the built-in assistant get a "read only" level too?
3. Should a shared tab return to the user automatically when the agent's session ends?
4. Should a data-flow grant ("act on b.com using what it read") for an outside client last for its session, or until revoked?
5. Rejected: the critique's budget of "at most one card on a three-site research task". This plan budgets one card per site the agent acts on, because a single grant for every site reopens the chain.
6. Partly rejected: escalating navigation to URLs the user typed exactly. That carries no model-chosen data, so it stays free.
7. Rejected: an expert `chrome://inspect` switch. Per the critique, no new setting; developers use a separate profile.

## Draft thread brief

Thread brief: see `plans/threads/core.md`.
