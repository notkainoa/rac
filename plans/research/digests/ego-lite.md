# ego(lite) — digest

Source: `plans/research/ego-lite.md` (2026-10-27). The browser is closed, so evidence is the MIT repo ([citrolabs/ego-lite](https://github.com/citrolabs/ego-lite) at `aecc583`), the [benchmark harness](https://github.com/citrolabs/ego-browser-benchmark-framework), the website, and issues. Nothing was run. **FACT** = read in code, docs, or an issue; **CLAIM** = marketing or self-report; **INFERENCE** = reasoning. The dossier's Verification section (15 rows) is authoritative; its one correction (v2 snapshot defaults to the viewport, not full page) is applied. `ego:` = repo path.

## In plain English

ego(lite) is a free Chromium browser for Mac and Windows with no AI of its own. Your own coding agent drives it. Instead of one tool call per click, the agent writes a short JavaScript program ("open, read, click, fill, print the page") and ego runs it in one go, saving round trips and money. Each task gets its own Space that never grabs your focus. The idea and polish are strong. The safety is thin: the agent's code can read every cookie, nothing asks before a payment, and its guides tell you to switch off your agent's own safety prompts. rac should copy the reach and keep its own guard.

## Key facts

**Licence.** Maker: Citro Labs, Singapore. Free, no account (FACT). Repo is MIT: the Node SDK agents script against (~21k TypeScript lines in `ego:package/ego-browser/src/`), skill text, site learnings, plugins for nine agent hosts, design docs, benchmark harness. Closed: the Chromium fork, native `ego-browser` launcher, native bindings, snapshot engine, Spaces, overlay, updater. The browser terms forbid reverse engineering (FACT, `ego:AGENTS.md:7`, [terms](https://lite.ego.app/terms)). Nothing below the SDK is reusable. Chromium 156 plus Node 24.22.1 (rac is on 154); weekly releases (FACT).

**How outside agents connect** (FACT unless noted).
1. `skills/ego-browser/SKILL.md` is a 40-line stub: run `ego-browser skill`.
2. That prints the guide bundled with the installed SDK between `[ego-browser:skill] ego-browser usage guide v<version>` and `... end of guide v<version>`; a missing end line means the agent's tool truncated it. The guide cannot drift from the binary (`ego:docs/ego-browser-skill-command.md:39-55`).
3. The app writes the stub to `~/.agents/skills/ego-browser` (and `~/.claude/skills`) on every launch if missing and never overwrites a user copy (`:72-85`).
4. The agent runs `ego-browser nodejs <<'EOF' … EOF`. `ego-browser` is a helper inside the app bundle, linked into `~/.local/bin` at onboarding.
5. Transport: Chromium's ProcessSingleton `SingletonSocket` (per-user Unix socket under `/var/folders/.../com.citrolabs.ego.lite.*`), which starts the "ego_cli" bootstrap service; the script runs in a utility process of sub-type `ego.mojom.NodeService` (embedded Node). The CLI launches the app if it is not running (issue [#188](https://github.com/citrolabs/ego-lite/issues/188): maintainer explanation and process args; no public code).

**Auth on that channel.** None beyond the OS user (INFERENCE; ProcessSingleton has no token). Any same-user process can run arbitrary scripts with full SDK power whenever ego runs. Since 0.6.1.9 ego stays in the tray after the last window closes and the CLI still connects (FACT, changelog). Maintainer's threat model: whoever can run `ego-browser` locally can already run commands as that user ([#315](https://github.com/citrolabs/ego-lite/issues/315)). The CLI loads an SDK from `--sdk-path` or `~/Library/Application Support/Citro Labs/debug/index.js` before the bundled one, so a same-user write there changes every agent script (INFERENCE). Whether the socket checks the caller is unknown.

**No CDP port by default.** CDP travels in-process through the `ego.sendCDPMessage` binding, scoped to the selected Task Space; an opt-in port exists in Settings. The bridge refuses CDP when the Space is not agent-owned (FACT, [#285](https://github.com/citrolabs/ego-lite/issues/285); `ego:docs/native-bindings-api.md`).

**Execution** (FACT). Each call is a fresh Node context: stdin code wrapped in `new AsyncFunction(...helpers, code)`; output flushed at the end. A FIFO gate serialises native calls to one Space at a time; parallelism comes from several CLI processes (INFERENCE). No step cap found (INFERENCE).

**In-page methods, v2** (FACT, `public-api-schema.ts`; v1 globals like `click('@5')` remain; public docs still show v1).
- **Spaces:** `taskSpace(nameOrId,{profileId?})`, `listTaskSpaces`, `claimTaskSpace`, `takeOverTaskSpace`, `profiles`.
- **TaskSpace:** `page(label)`, `userPage`, `pages`, `tabs`, `newPage`, `adopt`, `release`, `waitForControl`, `handOff`, `finish({keep})`, `cdp`; fields `spaceId`, `name`, `ownership`.
- **Observe:** `snapshot({scope?,root?,includeActionMarks?,includeStableLocator?})`, `screenshot`, `url`, `title`, `info`.
- **Navigate and wait:** `goto`, `reload`, `waitForURL`, `waitForEvent`, `waitForSelector`, `waitForLoadState`, `waitForFunction`, `waitForTimeout`.
- **Act:** `click`, `dblclick`, `hover`, `dragAndDrop`, `fill`, `selectOption`, `focus`, `press`, `setInputFiles`, `waitForFileChooser`, `close`, `acceptDialog`, `dismissDialog`, `mouse.*`, `keyboard.*`. Pointer actions take an optional 3–6 word `label` shown by the agent cursor.
- **Escape hatches:** `page.evaluate`, `page.fetch` (in page, with cookies), `page.cdp`; plain Node `fetch` and `node:fs/promises` also work.

Targets: `@21`, `ref=21`, `text=…`, `loc=css:`, `loc=role:button[name='Sign in']`, `loc=href:`, `xpath=`, raw CSS. Each must match exactly one actionable element.

**Action mechanics** (FACT). Actions auto-scroll with real wheel input, need an enabled element and real hit target, and send trusted `Input.dispatchMouseEvent` input, including into cross-site iframes. `fill()` verifies the edit. Each action returns a receipt with popups and any open JS dialog; while a dialog is open other CDP commands fail fast. Pages have permanent labels `p1`, `p2`…; page budget defaults to 8; user tabs are protected.

**Snapshot and refs** (FACT unless noted). Built natively by the closed `ego.snapshot()` binding; "from the accessibility tree" is CLAIM. Two-space indented tree, lines `role "name" [ref=N, loc=..., url=...]`. Exact lines from tests (`snapshot-result.test.mjs:312-316, 470-474`):

```
textfield "Prompt" [ref=10, loc=css:#prompt, url=https://example.com/prompt]
button "Save" [ref=11, loc=role:button[name="Save"]]
iframe [ref=12]
```

Public docs show an older `@3 [input type="email"]` format the code no longer prints. The SDK compacts: drops empty text and empty unnamed containers, collapses single-child containers, keeps iframes, images, canvases, table cells. Scope: `only_within_viewport` (v2 default), `full_page`, or `subtree` with `root: "@12"`. No deltas. "200 to 400 tokens" per page is CLAIM. Visible cross-site iframes and open shadow roots are included; sandboxed cross-origin iframes "may not show up fully"; closed shadow roots unmentioned.

Ref identity is `(frameId, backendNodeId, documentId)`. Partial snapshots merge and keep old refs; a full-page snapshot replaces the set; a document change invalidates refs; an invalid ref fails with "take a new snapshot" rather than guessing. Refs persist across processes in `~/.ego-browser/state` (`page-ref-registry.ts:211-219`; `page-ledger.ts:80-86`). `loc=` locators are emitted only when they resolve uniquely to the same node, then re-validated by the SDK (`native-snapshot-ref-requirement.md:62-80`). No redaction of password, payment, or OTP values found (INFERENCE; native side closed).

**Batching** (FACT). The guide tells agents to plan several actions per script, wait for the expected state, and print a fresh snapshot last. Loops, `evaluate` extraction, and file writes run in the same script. Guide example:

```js
const page = task.page("p1");
await page.fill("@21", "user@example.com");
await page.click("loc=role:button[name='Sign in']");
await page.waitForSelector("loc=css:#account-home", { state: "visible" });
console.log(await page.snapshot());
```

Heredoc versus REPL: 44% fewer rounds, 21.6% lower cost (CLAIM, [post](https://lite.ego.app/blog/heredoc-vs-repl-ai-agents-2026)).

**Spaces: isolation and sharing.**
- Ownership: `agent`, `user`, `agentDelegatedToUser`. While the user controls a Space, agent calls fail with `EGO_TASK_SPACE_USER_IN_CONTROL` plus a reason key such as `notifications`, `camera`, or `manual_takeover` (FACT). Agent hands off with `task.handOff()`; user takes back via the bar. Permission prompts and device choosers auto-hand the Space to the user. Spurious "user has taken control" stops hit long tasks and the agent cannot tell automatic from real ([#314](https://github.com/citrolabs/ego-lite/issues/314), open).
- **Cookies are shared, not isolated.** Docs: "One isolated BrowserContext per task, with its own cookies and storage." The shipped skill says the profile's cookie jar and HTTP cache are shared with the user's tabs and every other Space, measured at 3,478 cookies across 1,161 domains visible inside an agent Space (FACT, `clearing-state.md:3`). An agent's `Network.clearBrowserCookies` logged the user out ([#303](https://github.com/citrolabs/ego-lite/issues/303), open). One reporter says a Profile 6 Space read the default profile's cookies (CLAIM, #319). Spaces isolate tabs and focus. Sharing is also the feature: the agent inherits your logins (INFERENCE). A profile can be chosen per task.
- Agent Spaces close after 30 idle minutes (FACT).

**Focus** (FACT, changelog). Agent tabs are muted. Background Space tab changes stopped taking focus in 0.6.1.9; hidden Spaces show no bubbles or dialogs. The address bar is read-only and disruptive shortcuts are blocked during agent control. Earlier versions leaked focus case by case (0.6.0.12; Windows #574), so the guarantee is per case (INFERENCE).

**Overlay cost.** Blue glow, Take over and Stop bar, cursor badge, input lock, dot-matrix mask with dimming. Users measured ~40% GPU plus ~18% WindowServer for one idle agent Space ([#476](https://github.com/citrolabs/ego-lite/issues/476)) (FACT).

**Approvals.** None enforced by the browser for payments, sends, deletes, or cross-site navigation. Safety rests on the host agent's prompts, which every official guide says to disable (`claude --dangerously-skip-permissions`, `codex --dangerously-bypass-approvals-and-sandbox`, `opencode --auto`, `hermes --tui --yolo`); "ego(lite) can only be controlled normally when Claude has Bypass permissions turned on" (sandboxed agents cannot reach the socket, #188). The usage guide never mentions payment. Only a "clearing state" reference asks for approval before profile-wide clears. Verified on the open side only; the closed browser may hold undocumented checks.

**Injection.** Model-written scripts have raw CDP plus unrestricted Node egress, so a page-planted instruction can exfiltrate `HttpOnly` cookies. Open since 2026-08-24; the maintainer replied "I agree that the behaviors you described do exist" but disputes severity (FACT, #315). The skill itself calls `Network.getAllCookies`, contradicting the privacy policy's claim that external AI tools "cannot … read … authentication cookies, or session tokens".

**Telemetry.** README (CLAIM): "deliberately narrow". Privacy policy (FACT): usage analytics with user and device identifiers, feature usage, time zone, referral channel; crash reports "enabled by default during initial setup"; California section says Citro has "sold" and "shared" data with ad networks (applicability to the browser unclear). Browser data stays local; page content goes to the user's own model provider (CLAIM).

**Benchmark** (FACT as published). Ego 398 s, 93.5% success, $1.64/task; chrome-devtools-cli 587 s / 61.3% / $4.95; agent-browser 605 s / 62.9% / $2.66; browser-harness 615 s / 77.4% / $2.43; playwright-cli 648 s / 71.0% / $3.42. Weaknesses:
- 31 tasks; ego and chrome-devtools-cli ran once, others twice. 93.5% is 29/31; about ±9 points (INFERENCE).
- 5 of 31 tasks need login. Ego uses imported sessions; rivals start "with an empty profile and no logins" by ego's description. 5/31 = 16.1 points, equal to ego's lead over browser-harness (INFERENCE: the gap may be logins). Rival configs unpublished.
- Harness ships only the ego adapter; rival adapters and October raw runs are missing despite "raw results are open source". Tasks calibrated by the same team (INFERENCE: skill tuned on them). Agent `gpt-5.6-sol`, judge `gpt-5.6-terra`: same family (INFERENCE).
- Ego's own August report (same tasks, medium thinking): 87.1%, $2.87, 629 s versus marketed 93.5%, $1.64, 398 s. Ego-versus-ego variance rivals the gaps to others (INFERENCE).
- Believable: 26.5 turns versus 44–51 (INFERENCE).

## What rac should take

Ranked. Costs are rough agent-thread estimates (INFERENCE): S = days, M = 1–2 weeks, L = 3–4 weeks. Anchor (FACT): rac's guard and containment are far stronger than ego's; ego's reach and ergonomics are far better. Bring ego's reach to rac's guard. Today rac serves only the ACP agent it launched, during a run, over a 0600 Unix-socket MCP (`docs/internals/ai.md`); its snapshot lines look like `- button "Sign in" [ref=e6] [submit]`.

1. **Outside agents via a bundled helper plus a self-printing skill (M).** Signed `Contents/Helpers/rac` with `rac skill` (guide matching the build, begin and end markers) and `rac mcp` (stdio relay). One-click "Add to my agents" writes a stub to `~/.agents/skills/rac` and `~/.claude/skills/rac` only on click, never overwriting a user copy. Off by default, independent of the AI switch. Highest value.
2. **Agent-owned Spaces with ownership states (L).** Owner (`user`, `agent:<client>`), handoff and takeover, protected user tabs, labelled agent pages that persist, muted background tabs, no focus or window activation, idle auto-close, page budget. Stable error codes with reasons and a distinct code for automatic delegation (avoids #314).
3. **Batched steps, checked one by one (S–M).** A `run_steps` tool and CLI verb taking an ordered list of rac actions plus waits and a final `snapshot`; stops at the first failure or card. Every step still passes `ActionGuard` and containment, at most one card per risky step.
4. **Stable locators (M).** Emit `loc=role:button[name="Save"]` only when it re-resolves uniquely, validated before printing; accept `loc=`, `text=`, role targets, resolved to a ref then guarded like one.
5. **Snapshot scope and compaction (S).** `viewport | full | subtree(ref)`; ego's compaction; keep rac's deltas.
6. **Action receipts (S–M).** Return popups, dialogs, downloads; dialogs gate other tools until handled.
7. **Per-Space ref table for outside clients (S).** In-process, no disk ledger.
8. **Visible action label (S).** 3–6 static words in the tab pill and step rows.
9. **Benchmark with their harness (M plus model spend).** MIT, pluggable adapter. Add a rac adapter, run the 31 tasks and the injection fixture plus rac's own injection suite, at least 3 runs per tool, same logins for all.
10. **Public requirement docs with acceptance tests (S, a habit).** Ego's `docs/native-*.md` brief agent threads well.
11. **Site learnings (L, low priority).** Per-site notes loaded only on that domain; ego has not shipped the accumulation step (three example packs; "up to 5x" is CLAIM).

## What rac should avoid

- **Model-written code with raw CDP and network egress in the real profile.** It bypasses every guard. If rac ever offers scripting: throwaway profile or a CDP allowlist that cannot read or clear cookies.
- **Telling users to disable their agent's approvals.** rac's setup must work with the agent sandbox on,. No level bypasses the risky list, for outside agents too.
- **Calling Spaces "isolated" while sharing cookies.** Say "the agent uses your logins"; offer a separate profile per agent for real isolation.
- **Always-on overlays.** Keep the ring and pill static; honor reduced motion.
- **An always-reachable socket or resident process.** Listen only while "Outside agents" is on, per-profile socket, per-client consent card.
- **Install scripts that strip quarantine** with no signature check; **writable SDK override paths**.
- **Telemetry and crash uploads on by default.** Breaks rac's first rule.
- **Benchmark claims from one run of self-chosen tasks**, or logged-in versus logged-out comparisons.
- **Takeover errors the agent cannot tell apart** from real user takeover.

## Caveats

- Not run; motion, timing, and feel are unknown.
- Transport and auth are INFERENCE from ProcessSingleton plus issue comments, not public code.
- The cookie-leak chain comes from the open SDK, skill, and open issues; later native filtering would change it. Not tested live.
- Snapshot redaction, closed shadow roots, and hidden approval checks are unknown.
- Ego's docs contradict its code: "isolated BrowserContext" versus shared cookies; v1 snapshot format versus v2.
- Open: does the socket check the caller; are agent Spaces separate `BrowserContext`s at all; macOS updater type and whether the #292 signing report is real; is `NodeService` sandboxed (likely not); what roadmap "Browser ACP that hosts any harness agent" means for rac's ACP design; does the CCPA "sold" text cover the browser. Maintainer's call: outside agents in their own Spaces only, or also in a user-attached tab.
- Overlaps `plans/research/agent-stacks.md` items 1–3, 5, 10, 14–16.

## Where to look in the full dossier

All in `plans/research/ego-lite.md`:

- `## Snapshot` (33–48); `## Features` (49–98)
- `## UI, look, and feel` (99–136) — overlay, GPU cost
- `## Architecture` (137–218) — transport, auth, execution, open versus closed
- `## Data and storage` (220–268) — cookie sharing, telemetry
- `## Agents and AI` (270–523): how an agent gets in (272–306); tool model (308–365); Snapshots (367–427); Spaces (429–460); Approvals (462–480); Benchmark (482–523)
- `## Build, release, and engineering` (525–561)
- `## Strengths and weaknesses` (563–599)
- `## What rac should take and avoid` (601–734): comparison table (616–643)
- `## Open questions` (736–758); `## Sources` (760–833)
- `## Verification` (835–860)
