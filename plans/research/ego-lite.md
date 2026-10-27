# ego(lite) by Citro Labs: research dossier

Researched 2026-10-27. Subject: [lite.ego.app](https://lite.ego.app/) and
[github.com/citrolabs/ego-lite](https://github.com/citrolabs/ego-lite) at commit
`aecc583` (2026-10-26), shallow-cloned to `/tmp/rac-overhaul/src/ego-lite-latest`
(read only, nothing run). Also cloned the benchmark harness
[citrolabs/ego-browser-benchmark-framework](https://github.com/citrolabs/ego-browser-benchmark-framework)
at `f566ac2` to `/tmp/rac-overhaul/src/ego-browser-benchmark-framework`. Repo paths
below are relative to those clones (`ego:` and `bench:` prefixes). Website pages were
saved as text under `/tmp/rac-overhaul/ego-site/`. The ego browser binary was not
downloaded or run.

Tags: **FACT** (read in code, docs, or an issue), **CLAIM** (marketing or
self-report), **INFERENCE** (my reasoning).

## In plain English (at most 150 words)

ego(lite) is a free Chromium browser for Mac and Windows. You browse in it
normally. Your own coding agent (Claude Code, Codex, and others) can also use it.
The agent doesn't call one tool at a time. It writes a short JavaScript program
("open this page, read it, click that, fill this") and ego runs the whole program
in one go. That saves round trips, time, and money.

Each agent task gets its own "Space": a set of tabs that never steals your mouse,
focus, or tabs. You can watch, take over, or stop it.

The idea is excellent and the polish is real. The safety is thin. The agent's
program gets raw low-level browser access and can read every cookie. Nothing in
the browser asks before a payment or a send. Their setup guides tell you to turn
off your agent's safety prompts. Their best benchmark numbers are a single run on
their own test.

## Snapshot

| | ego(lite) |
| --- | --- |
| What it is | Chromium browser (closed source) plus an open-source Node.js automation SDK and an agent skill (`ego-browser`) that any shell-capable agent uses. FACT ([README](https://github.com/citrolabs/ego-lite#readme); `ego:AGENTS.md:1-8`) |
| Maker | CITRO LABS PTE. LIMITED, Singapore. FACT ([privacy policy](https://lite.ego.app/privacy), EEA addendum §A). A fuller "ego" product exists with a personal agent, cloud sandbox, and memory. CLAIM ([launch post](https://lite.ego.app/blog/browser-for-run-browser-automation-tasks-in-parallel), "Why are we called ego") |
| Platforms | macOS (Apple Silicon and Intel), Windows beta; Linux planned. FACT ([download page](https://lite.ego.app/download); [roadmap](https://lite.ego.app/roadmap)) |
| License | Repo MIT. The browser is a "separate, free download" under terms that forbid reverse engineering. FACT (`ego:README.md`, License; [terms](https://lite.ego.app/terms)) |
| Engine | Chromium 156.0.8078.48 and embedded Node.js v24.22.1 as of 0.6.1.9 (2026-10-24). FACT ([changelog](https://lite.ego.app/changelog)) |
| Latest app | 0.6.1.13 (2026-10-26). FACT ([changelog](https://lite.ego.app/changelog)) |
| Skill/SDK version | 2.1.0 (2026-10-08, released 2026-10-16). FACT (`ego:skills/ego-browser/SKILL.md` frontmatter; `gh release list`) |
| Repo stats | 20,071 stars, 1,116 forks, created 2026-04-16, 242 open issues plus PRs. FACT (GitHub API, 2026-10-27) |
| Code in repo | ~21k TypeScript lines in `package/ego-browser/src` (non-test), plus skill, plugins for nine agent hosts, and design docs. FACT (`wc -l`) |
| Price | Free for individuals; "Business" plan by contact. FACT ([enterprise](https://lite.ego.app/enterprise)) |
| Account | None needed. FACT ([product intro](https://lite.ego.app/document/en/docs/product-introduce), Privacy) |

## Features

### Browser (for the human)

- Chromium with tabs, tab groups, profiles, extensions, incognito, DevTools (F12).
  FACT ([FAQ on home](https://lite.ego.app/); [changelog](https://lite.ego.app/changelog) 0.4.2.21).
- **Spaces** as a user feature too: pin Spaces, a Spaces Overview (⌥S, hold ⌥ and
  press S or arrows to cycle, ⌥W closes), custom per-Space shortcuts, open a Space
  in a new window, media state per Space, profile per Space. FACT (changelog
  0.4.6.12, 0.4.6.13, 0.5.0.28, 0.5.1.11).
- Vertical tab strip (since 0.6.0.12, 2026-10-15) that hides fully and reveals at
  the left edge; floating tab strip; pinned tabs as an icon grid. FACT (changelog
  0.6.0.12).
- Import from Chrome, Edge, Brave, Safari, Comet, Opera, Vivaldi, Yandex, Dia, Arc,
  Firefox, Zen: tabs, groups, bookmarks, passwords, extensions, cookies and
  sessions, profiles, reading list, site permissions. FACT (changelog 0.5.1.11,
  0.6.1.9; [download FAQ](https://lite.ego.app/download)).
- "Keep browser data up to date": periodic re-sync of bookmarks and history from a
  detected source browser, only while ego isn't the default browser. FACT
  (changelog 0.4.4.15, 0.4.5.5).
- Passkeys from iCloud Keychain with Touch ID; DRM playback (Widevine) since
  0.6.1.9. FACT (changelog 0.5.1.12, 0.6.1.9).
- Experimental frosted-glass window background (off by default at first, a
  `glass-frame` flag); only the active window gets glass since 0.6.0.15. FACT
  (changelog 0.5.0.28, 0.6.0.15; issue
  [#476](https://github.com/citrolabs/ego-lite/issues/476) comments).
- An "On-device AI" switch (0.6.1.9) after a user found ego silently downloading
  Chrome's 2.7 GB on-device model. FACT (changelog 0.6.1.9; issue
  [#548](https://github.com/citrolabs/ego-lite/issues/548)).
- No built-in AI assistant in the browser. The agent is always yours. FACT
  ([product intro](https://lite.ego.app/document/en/docs/product-introduce)). Roadmap
  lists "Browser ACP that hosts any harness agent" as in progress. FACT
  ([roadmap](https://lite.ego.app/roadmap)).

### Agent-facing

- `ego-browser` CLI and skill, installed into `~/.agents/skills` and
  `~/.claude/skills` on first launch for every detected agent. FACT
  ([quick start](https://lite.ego.app/document/en/docs/quick-start), Tip).
- Plugins for nine hosts: Claude Code, Codex, Cursor, GitHub Copilot, Grok Build,
  WorkBuddy, QwenWork, OpenCode, DeepSeek Harness. FACT (`ego:plugins/ego/README.md:20-32`).
- Task Spaces, handoff and takeover, profile selection per task, downloads,
  uploads, dialogs, popups, raw CDP, `page.fetch` in page context. FACT
  (`ego:package/ego-browser/skill-body/SKILL.md`).
- Opt-in CDP port in Settings (added after a user request). FACT (issue
  [#285](https://github.com/citrolabs/ego-lite/issues/285), maintainer reply).
- "Experience accumulation" (site learnings) is "coming soon"; three example packs
  ship (GitHub, Google, X). FACT for the packs (`ego:skills/ego-browser/learnings/`);
  CLAIM for the speedup ("up to 5x", README).

## UI, look, and feel

From changelog text, docs, issues, and the repo images. I did not run the app, so
motion values are unknown.

- **Brand.** Monochrome: black three-lens mark, light gray gradient, wordmark
  "ego (lite)" with an italic light "(lite)". FACT (`ego:docs/assets/banner.png`).
  The site uses Mona Sans. FACT (font URL in page HTML).
- **Space button and overview.** A Space button at the top right opens a Space
  management panel with thumbnails. The Space the agent works in has "a blue
  glow". FACT ([quick start](https://lite.ego.app/document/en/docs/quick-start),
  "Watch and take over").
- **Agent control overlay.** While an agent controls a Space: a blue border glow,
  a bottom control bar with Take over and Stop, a cursor badge showing the action's
  short `label`, a full-screen input lock, and a dense dot-matrix mask with a
  dimming spotlight. FACT (issue [#557](https://github.com/citrolabs/ego-lite/issues/557)
  describes all parts; `label` option in `ego:package/ego-browser/skill-body/SKILL.md`,
  "Only these pointer actions accept an optional label"; `ego:package/ego-browser/src/driver/pointer.ts:591-597`
  calls `animationHighlightMouseToPosition` and `setAgentTaskState`).
- The address bar is read-only while the agent is in control. Browser and Space
  shortcuts that would disrupt a task are blocked. Captions and Translate are
  suppressed. Agent tabs are muted by default. The Mac doesn't sleep during a task.
  FACT (changelog 0.5.0.32, 0.4.6.12, 0.4.7.1, 0.4.4.15, 0.6.1.9).
- **Cost of the overlay.** Users measured ~40% GPU in ego's GPU process plus ~18%
  in WindowServer for one idle agent Space on `about:blank`, dropping to 0–6% when
  closed, and halved WebGL frame rate in other windows. FACT (issue
  [#476](https://github.com/citrolabs/ego-lite/issues/476), user measurements with
  `ioreg`). Similar complaints: [#304](https://github.com/citrolabs/ego-lite/issues/304)
  (>90% GPU during the takeover animation), [#69](https://github.com/citrolabs/ego-lite/issues/69)
  (idle GPU 6.7% → 38.5% with ego open, per `powermetrics`),
  [#520](https://github.com/citrolabs/ego-lite/issues/520) (high CPU),
  [#382](https://github.com/citrolabs/ego-lite/issues/382) (Space animations stutter on M5).
  This is exactly the "nothing that repaints continuously" failure rac's vision
  forbids (INFERENCE).
- Praise is about setup and speed: "installed in just a few minutes, with one-click
  copying of Chrome's login info", "Most beautiful changelog". CLAIM (curated
  quotes on [home](https://lite.ego.app/)).

## Architecture

```
agent (Claude Code, Codex, ...) ──shell──▶ ego-browser nodejs <<'EOF' … EOF
                                              │  (native helper inside the app bundle)
                                              ▼
              Chromium ProcessSingleton socket ──▶ ego lite.app (browser process)
                                              │     starts "ego_cli" bootstrap service
                                              ▼
                       utility process  ego.mojom.NodeService  (embedded Node.js 24)
                         loads SDK index.js → globalThis.ego bindings
                                              │
                    ego.sendCDPMessage / ego.snapshot / task-space calls (in-process)
                                              ▼
                  Task Spaces (tabs per task) in the same browser and profile
```

- **Open versus closed.** Open (MIT): the Node SDK that agents script against
  (`ego:package/ego-browser/src/`), the skill text, site learnings, plugin
  packaging, design docs that tell the native team what to build
  (`ego:docs/native-*.md`), and the benchmark harness. Closed: the Chromium fork,
  the native `ego-browser` launcher, the `ego` native bindings, the snapshot
  engine, Spaces, the overlay, the updater. FACT (`ego:AGENTS.md:7`: "This repo
  contains the open-source harness and the agent skill package — not the browser
  itself"; `ego:docs/native-bindings-api.md:6-9`).
- **Launcher.** `ego-browser` is a helper executable at
  `ego lite.app/Contents/Frameworks/*.framework/Versions/Current/Helpers/ego-browser`,
  linked into `~/.local/bin` during onboarding. FACT
  (`ego:skills/ego-browser/scripts/install.sh:83-95`;
  `ego:skills/ego-browser/references/install.md`, Onboarding).
- **Transport.** The CLI connects to the running app through Chromium's
  ProcessSingleton (the `SingletonSocket` Unix socket under
  `/var/folders/.../com.citrolabs.ego.lite.*`), asks it to start the "ego_cli
  bootstrap" server service (also startable with `--startup-ego-browser-service`),
  and the script runs in a utility process with sub-type `ego.mojom.NodeService`.
  If the app isn't running, the CLI launches it. FACT (issue
  [#188](https://github.com/citrolabs/ego-lite/issues/188): reporter's diagnosis
  plus maintainer `liuwd8`'s explanation; process args show
  `--utility-sub-type=ego.mojom.NodeService`). On Windows a medium-integrity
  "relay" child handles elevated terminals. FACT (changelog 0.6.0.20, 0.6.0.22;
  issues [#547](https://github.com/citrolabs/ego-lite/issues/547),
  [#559](https://github.com/citrolabs/ego-lite/issues/559)).
  The CLI can target an instance by "server name". FACT (changelog 0.4.5.5, 0.4.7.1).
- **No remote-debugging port by default.** CDP travels in-process through the
  `ego.sendCDPMessage` binding, scoped to the selected Task Space. "Exposing a CDP
  port can be abused by malware running on the local machine, so we avoid enabling
  it by default." FACT ([#285](https://github.com/citrolabs/ego-lite/issues/285);
  `ego:docs/native-bindings-api.md`, "Chrome DevTools Protocol"). The bridge
  refuses CDP when the Space is not agent-owned and was fixed to refuse
  `Target.createTarget`. FACT (`ego:docs/native-bindings-api.md`; changelog 0.4.5.5).
- **Authentication between agent and browser.** None beyond the OS user. Any
  process of the same user can reach the singleton socket (its directory is
  per-user) and run arbitrary scripts with full SDK powers, at any time ego is
  running. Ego now stays alive in the tray after the last window closes "and the
  ego-browser CLI can still connect". INFERENCE from the transport (Chromium's
  ProcessSingleton has no token) plus FACT for the tray change (changelog 0.6.1.9)
  and the maintainer's stated threat model: "if someone is already able to execute
  ego-browser locally, they can also execute arbitrary local commands with the same
  local user privileges" (issue [#315](https://github.com/citrolabs/ego-lite/issues/315)).
  Nothing stops another local process from driving it except that it must be the
  same user (INFERENCE).
- **SDK override paths.** The CLI loads `--sdk-path <file>`, else
  `~/Library/Application Support/Citro Labs/debug/index.js`, else the bundled SDK.
  FACT (`ego:docs/ego-browser-skill-command.md:43-46`; `ego:CONTRIBUTING.md:80-130`).
  Any same-user process that writes that debug file changes the code every agent
  script runs inside ego (INFERENCE). Not a new capability for a same-user
  attacker, but a persistence spot rac should not copy.
- **Execution model.** Each `ego-browser nodejs` call is a fresh Node context:
  stdin JavaScript is wrapped in `new AsyncFunction(...helpers, code)` with helpers
  injected as parameters. Output is buffered and flushed at the end (discarded on
  a hard stop). FACT (`ego:package/ego-browser/src/run.ts:95-123`;
  `ego:package/ego-browser/src/index.ts:120-130`).
- **Concurrency inside one script.** Native task selection is process-wide, so
  the SDK serializes every native call through a FIFO "gate" bound to one Space at
  a time. FACT (`ego:package/ego-browser/src/native-gate.ts:31-37`). Parallelism
  comes from several CLI processes (several agents or tasks), not from one script.
  INFERENCE.
- **Why JavaScript and an embedded Node.** One language for orchestration and
  in-page code, and no dependency on the user's Python or shell; Node reuses the
  browser's V8 and adds "6MB" (launch post) or "10 MB" (Skills doc). CLAIM, and the
  two numbers disagree ([launch post](https://lite.ego.app/blog/browser-for-run-browser-automation-tasks-in-parallel);
  [Skills](https://lite.ego.app/document/en/docs/skills)).

## Data and storage

- **Browser data** stays local like Chrome's: history, cookies, passwords,
  bookmarks. FACT as stated in the privacy policy ("stores ... locally on your
  device"). Google services are used for search suggestions and Safe Browsing.
  FACT ([privacy policy](https://lite.ego.app/privacy), "Browser Activity Data").
- **Agent state on disk.** Each Space's Page labels and ref mappings persist in a
  "Page ledger" at `~/.ego-browser/state` (override `EGO_BROWSER_STATE_DIR`),
  written atomically. FACT (`ego:package/ego-browser/src/page-ledger.ts:80-86, 465`).
  Downloads go to round-local temp files deleted when the script ends unless
  `saveAs()` is called. FACT (SKILL.md, "Files and requests").
- **Space "isolation" is not storage isolation.** The docs say a Space is "One
  isolated BrowserContext per task, with its own cookies and storage" (FACT,
  [Space doc](https://lite.ego.app/document/en/docs/space)). Their own skill says
  the opposite: a Space's "profile's cookie jar and HTTP cache are shared with the
  user's own tabs and with every other task space on the same profile", measured
  at 3,478 cookies across 1,161 domains visible from inside an agent space. FACT
  (`ego:skills/ego-browser/references/clearing-state.md:3`). An agent's
  `Network.clearBrowserCookies` logged the user out of their main Space (FACT,
  issue [#303](https://github.com/citrolabs/ego-lite/issues/303), open), and
  `Storage.getCookies` from a Space on Profile 6 returned the default profile's
  1,105 cookies (CLAIM by reporter, issue
  [#319](https://github.com/citrolabs/ego-lite/issues/319), open). Spaces isolate
  *tabs and focus*, not cookies. That sharing is also the feature ("the agent
  inherits the same logged-in state"). INFERENCE.
- **Telemetry.** README: "data collection deliberately narrow: simple product
  signals, like whether you've set ego lite as your default browser" (CLAIM,
  `ego:README.md`, Quick Start). The privacy policy is broader: usage analytics
  sent to Citro's servers with "user and device identifiers, feature usage status
  and outcomes, and time zone", referral channel; crash reports "enabled by default
  during initial setup" (opt-out); installer and updater logs. FACT
  ([privacy policy](https://lite.ego.app/privacy), "Safeguarding"). The policy's
  California section says Citro has "sold" and "shared" device, browsing and usage
  data with advertising networks. FACT that the text says it; whether it applies
  to the browser or only to the website and the wider "ego" service is unclear
  (INFERENCE: likely shared boilerplate across Citro products, but it is the
  policy that covers the browser).
- **What goes to the model.** Page content the agent reads goes to whichever model
  the user's agent uses; ego says it doesn't receive it. CLAIM
  ([privacy policy](https://lite.ego.app/privacy), "External AI tool connections").
- **Credential claim contradicted.** The policy says "External AI tools cannot use
  the browser interfaces to read or export passwords saved in the browser,
  authentication cookies, or session tokens." (FACT that it says so.) The shipped
  skill shows agents calling `page.cdp("Network.getAllCookies")`, which returns
  `httpOnly` auth cookies, and the open security report
  [#315](https://github.com/citrolabs/ego-lite/issues/315) says model-written code
  can read `HttpOnly` session cookies and send them anywhere through Node `fetch`;
  the maintainer replied "I agree that the behaviors you described do exist."
  FACT (`ego:skills/ego-browser/references/clearing-state.md:47-55`; #315).

## Agents and AI

### How an agent gets in

1. The entry skill (`skills/ego-browser/SKILL.md`, 40 lines) only says: run
   `ego-browser skill` and follow its output. FACT.
2. `ego-browser skill` prints the usage guide bundled with the installed SDK,
   bracketed by `[ego-browser:skill] ego-browser usage guide v<version>` and
   `... end of guide v<version>`, so the guide always matches the binary. A missing
   end line means the agent's tool truncated it. FACT
   (`ego:docs/ego-browser-skill-command.md:39-55`). This two-layer skill is the same
   "thin stub plus self-printing guide" pattern agent-browser uses (see
   `plans/research/agent-stacks.md`, item 16).
3. The agent runs `ego-browser nodejs <<'EOF' ... EOF` (or `-e '...'`, or a `.mjs`
   file on Windows). FACT (SKILL.md, "Run browser scripts").
4. The app writes the stub into `~/.agents/skills/ego-browser` on every launch if
   missing, and never overwrites a user-installed copy. FACT
   (`ego:docs/ego-browser-skill-command.md:72-85`).
5. Update notice: if the browser's updater has a new version, the script output
   ends with `[ego-browser:notice] ... ask the user before running
   ego-browser upgrade`. FACT (`ego:package/ego-browser/src/update-notice.ts:31-36`).

Host permissions: every official agent guide tells the user to run the agent with
its sandbox and approvals off: `claude --dangerously-skip-permissions`,
`codex --dangerously-bypass-approvals-and-sandbox`, `opencode --auto`,
`hermes --tui --yolo`, OpenClaw's no-approval preset. "ego(lite) can only be
controlled normally when Claude has Bypass permissions turned on." FACT
([Claude Code guide](https://lite.ego.app/document/en/docs/claude-code);
[Codex](https://lite.ego.app/document/en/docs/codex);
[OpenCode](https://lite.ego.app/document/en/docs/opencode);
[Hermes](https://lite.ego.app/document/en/docs/hermes-agent);
[OpenClaw](https://lite.ego.app/document/en/docs/openclaw)). The reason is that
sandboxed agents can't reach the singleton socket or launch the app (FACT, #188).
The custom-harness guide is more careful ("prefer a host-command allowlist").
FACT ([custom harness](https://lite.ego.app/document/en/docs/custom-agent-harness),
Step 2). An allowlist of just `ego-browser` would not limit what the script does,
since the script is arbitrary code (INFERENCE).

### The tool model: code, not commands

The agent writes a Node script against a small API. The v2 surface (the
v1 global helpers like `snapshotText()`, `click('@5')` remain for old scripts;
the public docs pages still show v1) is:

| Group | Exact signatures (FACT, `ego:package/ego-browser/src/public-api-schema.ts`) |
| --- | --- |
| Spaces | `await taskSpace(nameOrId, { profileId? })`, `await listTaskSpaces()`, `await claimTaskSpace(spaceId)`, `await takeOverTaskSpace(spaceId)`, `await profiles()` |
| TaskSpace | `task.spaceId`, `task.name`, `task.ownership`, `task.page(label)`, `task.userPage()`, `await task.pages()`, `await task.tabs()`, `await task.newPage()`, `await task.adopt(page, { as? })`, `await task.release(label)`, `await task.waitForControl({ interval?, timeout? })`, `await task.handOff()`, `await task.finish({ keep })`, `await task.cdp(method, params?, { timeout? })` |
| Observe | `await page.snapshot({ scope?, root?, includeActionMarks?, includeStableLocator? })`, `await page.screenshot({ path?, fullPage?, clip?, scale?, raw? })`, `url()`, `title()`, `info()` |
| Navigate and wait | `await page.goto(url, { referer?, timeout?, waitUntil? })`, `reload()`, `waitForURL(matcher)`, `waitForEvent("popup"|"download"|...)`, `waitForSelector(sel, { state? })`, `waitForLoadState(state?, { idleMs? })`, `waitForFunction(fn, arg, opts)`, `waitForTimeout(ms)` |
| Act | `click`, `dblclick`, `hover`, `dragAndDrop`, `fill`, `selectOption`, `focus`, `press`, `setInputFiles`, `waitForFileChooser`, `close`; `acceptDialog(promptText?)`, `dismissDialog()`; `mouse.click/move/down/up/wheel`; `keyboard.down/up/press/type/insertText/paste` |
| Escape hatches | `await page.evaluate(fnOrString, arg)`, `await page.fetch(url, opts)` (in page, with cookies), `await page.cdp(method, params)`; plain Node `fetch` and `import("node:fs/promises")` also work. FACT (SKILL.md, "Page JavaScript and CDP") |

Targets accept `@21` or `ref=21`, `text=...` (quoted means exact), `loc=css:`,
`loc=role:button[name='Sign in']`, `loc=href:`, `xpath=`, raw CSS, plus a small
Playwright subset (`:has-text()`, `:text-is()`, `>> nth=N`). Every selector must
match exactly one actionable element; the top document is searched first, then
frames. FACT (SKILL.md, "Semantic pages").

**Batching.** The guide tells the agent to plan several actions per script, wait
for the expected state, and print a fresh snapshot last so the next round can act
without an extra observe call. FACT (SKILL.md, "Semantic pages: snapshot and
selectors"). Example from the guide:

```js
const page = task.page("p1");
await page.fill("@21", "user@example.com");
await page.click("loc=role:button[name='Sign in']");
await page.waitForSelector("loc=css:#account-home", { state: "visible" });
console.log(await page.snapshot());
```

Loops, filters, extraction with `page.evaluate`, and writing a file all happen in
the same script. FACT (SKILL.md; [ego-browser doc](https://lite.ego.app/document/en/docs/ego-browser),
"Recommended workflow"). Their REPL-versus-heredoc test claims 44% fewer rounds,
35.5% fewer tool calls, and 21.6% lower cost for heredoc. CLAIM
([heredoc post](https://lite.ego.app/blog/heredoc-vs-repl-ai-agents-2026)).

**Action mechanics.** Clicks, fills, hovers, and drags auto-scroll the target into
view with real wheel input, require an enabled element and a real hit target, and
dispatch trusted input through CDP (`Input.dispatchMouseEvent`), including into
cross-site iframes through their own sessions. FACT
(`ego:package/ego-browser/README.md`, "Design constraints";
`ego:package/ego-browser/scripts/real-browser-e2e/cases/page-oopif.mjs:30-60`).
`fill()` verifies the edit took. Each action returns a receipt with any popups
(`receipt.popups[].label`) and an open JavaScript dialog; while a dialog is open,
other CDP commands fail fast with "handle it with page.acceptDialog() or
page.dismissDialog()". FACT (`ego:package/ego-browser/src/browser-runtime.ts:33-38, 113-142`;
SKILL.md, "Action receipts").

**Pages and budgets.** Pages get permanent labels `p1`, `p2`...; a Space starts
with `p1`; the Page budget defaults to 8 (`EGO_BROWSER_PAGE_BUDGET`). User tabs and
tabs of unknown origin are protected; `finish({ keep: [] })` closes only
agent-made Pages. FACT (`ego:package/ego-browser/src/page-model.ts:3689-3692`;
SKILL.md, "Spaces, rounds, and pages"). There is no step cap: a script can do
anything in one call (INFERENCE from the API; no cap found in `src/`).

### Snapshots

- **Where built.** Natively in the browser through the closed `ego.snapshot()`
  binding, not by injected page script. The docs say it is "built from the
  browser's accessibility tree". FACT for the binding
  (`ego:docs/native-bindings-api.md`, "Snapshot"); CLAIM for the AX-tree source
  ([Snapshot doc](https://lite.ego.app/document/en/docs/snapshot)).
- **Format.** Two-space indented tree under `root`; each line is
  `role "name" [ref=N, loc=..., url=...]`. Real example from tests:

  ```
  textfield "Prompt" [ref=10, loc=css:#prompt, url=https://example.com/prompt]
  button "Save" [ref=11, loc=role:button[name="Save"]]
  iframe [ref=12]
  ```

  FACT (`ego:package/ego-browser/src/snapshot-result.test.mjs:312-316, 470-474`).
  The public docs show an older `@3 [input type="email"]` format that the code no
  longer prints (FACT: [product intro](https://lite.ego.app/document/en/docs/product-introduce)
  versus the tests). The SDK compacts the tree: drops empty text, empty unnamed
  containers, and collapses single-child containers, keeping iframes, images,
  canvases, and table cells. FACT (`ego:docs/native-snapshot-ref-requirement.md:1-25`;
  `snapshot-result.ts:44-100`).
- **Options.** `scope`: `only_within_viewport` (default in v2), `full_page`, or
  `subtree` with `root: "@12"` (for example, an iframe's ref). Native options also
  include `interactiveOnly` and `maxResultLength`. FACT
  (`ego:package/ego-browser/src/public-api-schema.ts:235-253`;
  `ego:docs/native-bindings-api.md`). "A typical page fits in 200 to 400 tokens."
  CLAIM ([product intro](https://lite.ego.app/document/en/docs/product-introduce)).
- **Iframes, shadow DOM, widgets.** The viewport snapshot includes visible iframe
  content including cross-site OOPIFs; the e2e suite tests a cross-site iframe
  below the fold and an open shadow root; CSS selectors search nested *open*
  shadow roots. FACT (`page-oopif.mjs`; `page-shadow-dom.mjs`; SKILL.md). Their own
  requirement doc says native refs for actionable iframe nodes were missing at one
  point and the SDK backfills `frameId` from the frame AX tree when unambiguous.
  FACT (`ego:docs/native-snapshot-ref-requirement.md:30-60`). The docs admit
  "sandboxed cross-origin iframes may not show up fully". FACT
  ([Snapshot doc](https://lite.ego.app/document/en/docs/snapshot), FAQ). "Reaches
  Stripe, Salesforce, Intercom, React portals" is CLAIM (home page); nothing in the
  open repo tests those vendors. Closed shadow roots are not mentioned (open
  question).
- **Refs that survive change.** Page refs are SDK-assigned ids bound to identity
  `(frameId, backendNodeId, documentId)`. A partial snapshot merges by identity and
  keeps old refs; a full-page snapshot replaces the active set; a document change
  invalidates refs from that document; invalid refs fail with "take a new
  snapshot" rather than guessing by role and name. Ref state persists across
  processes in the Page ledger, and actions keep refs to unchanged nodes valid so
  several ref actions can run in a row. FACT
  (`ego:package/ego-browser/src/page-ref-registry.ts:18-130, 211-219`;
  `ego:package/ego-browser/README.md`, "Design constraints"). A snapshot that spans
  a document change throws "Page changed during snapshot". FACT
  (`page-model.ts:1736-1748`).
- **Stable locators (`loc=`).** The native side emits a locator only when it
  resolves uniquely to the same node; the SDK re-validates and drops bad ones. The
  agent can reuse `loc=` across rounds when refs expire. FACT
  (`ego:docs/native-snapshot-ref-requirement.md:62-80`;
  `snapshot-result.ts:86-95`). This is also the basis for site learnings. FACT
  ([ego-browser doc](https://lite.ego.app/document/en/docs/ego-browser), "Ref scope").
- **Redaction.** I found no redaction of password, payment, or one-time-code values
  in snapshots in the open SDK or docs. INFERENCE (absence in `src/` and docs); the
  native side is closed.

### Spaces: parallel, focus-free work, handoff

- Ownership states `agent`, `user`, and a third `agentDelegatedToUser`. Agent
  calls to tabs, snapshot, raw CDP, and the overlay are blocked while the user
  controls the Space, with `EGO_TASK_SPACE_USER_IN_CONTROL` and a reason key
  (`notifications`, `location`, `camera`, `microphone`, `usb`, `hid`,
  `protocol_handler`, `manual_takeover`, ...). FACT
  (`ego:docs/native-bindings-api.md`, "Tabs", "Task Control").
- Agent to user: `task.handOff()`; user to agent: the user clicks the bar, then
  `takeOverTaskSpace(id)`. Claiming a user's own Space needs the user's explicit
  request. FACT (SKILL.md, "User control and completion").
- Permission prompts and device choosers auto-hand the Space to the user. JS
  `alert/confirm/prompt` stay under agent control since 0.5.0.x (after users
  complained that confirm dialogs stopped their scripts). FACT
  ([#302](https://github.com/citrolabs/ego-lite/issues/302);
  `ego:docs/native-javascript-dialog-requirement.md`). Spurious "user has taken
  control" stops still hit long tasks, and the agent can't tell an automatic
  delegation from a real takeover. FACT (issue
  [#314](https://github.com/citrolabs/ego-lite/issues/314), open, many +1s).
- Never steals focus: background Space tab changes stopped taking focus in
  0.6.1.9; hidden Spaces no longer show bubbles, prompts, or dialogs. FACT
  (changelog 0.6.1.9, 0.4.7.1). Earlier versions had several focus leaks fixed one
  by one (changelog 0.6.0.12, "hidden window appearing when an Agent creates a task
  tab"; issue [#574](https://github.com/citrolabs/ego-lite/issues/574) Windows
  regression). The guarantee is therefore implemented case by case, not
  structurally (INFERENCE).
- Agent Spaces close after 30 minutes without a command (pinned, user-made, and
  handed-back Spaces excepted). FACT (changelog 0.6.0.12).
- Resource model: "six-way" test, separate instances ~15 GB and ~84 processes
  versus Spaces ~0.9 GB and ~6 processes. CLAIM, self-labelled "not a precise
  benchmark" ([Space doc](https://lite.ego.app/document/en/docs/space)). Users report
  20 GB+ in batch scraping. CLAIM ([#343](https://github.com/citrolabs/ego-lite/issues/343)).

### Approvals for risky steps

There is no browser-enforced approval for payments, sends, deletes, or
cross-site navigation. Safety rests on (a) the host agent's own prompts, which ego
tells users to turn off; (b) prose in docs ("the agent should pause ... Payment,
ordering, transfers"; [Space doc](https://lite.ego.app/document/en/docs/space),
"Logged-in state"); (c) the user watching. The shipped usage guide has zero
mentions of payment or purchase. FACT (`grep` of `skill-body/SKILL.md`; no
guard code in `src/`). The only guidance on destructive CDP is a
"clearing state" reference asking for user approval before profile-wide clears.
FACT (`clearing-state.md`, last section). The launch post's safety advice is
"make sure the agent you let drive it comes from a source you trust". FACT.

Prompt injection: an external report shows model-generated scripts have
unrestricted raw CDP plus unrestricted Node egress, so a page-planted
instruction can exfiltrate cookies. Open, unfixed; the maintainer disputes the
severity. FACT ([#315](https://github.com/citrolabs/ego-lite/issues/315)). Their
benchmark does include one injection fixture (a résumé that tells form-fillers to
tick every box). FACT (`bench:data/README.md`, "attachments/ fixtures").

### Benchmark: do the numbers hold up?

Headline: 398 s per task, 93.5% full success, $1.64 per task, against
chrome-devtools-cli 587 s / 61.3% / $4.95, agent-browser 605 s / 62.9% / $2.66,
browser-harness 615 s / 77.4% / $2.43, playwright-cli 648 s / 71.0% / $3.42.
FACT that they publish these ([home](https://lite.ego.app/);
`ego:docs/assets/real-world-bench.jpg`).

What the chart's own footnote and the harness show (FACT unless marked):

- **Sample size.** 31 tasks. "ego-browser and chrome-devtools-cli ran once, the
  other three twice." ego's figures are build `be48d11` (2.0.0-beta-dev), the
  2026-08-25 batch, judged at "xhigh". FACT (chart footnote). 93.5% is 29 of 31;
  77.4% is 24 of 31 per run on average. A single run of 31 has a 95% interval of
  roughly ±9 points (INFERENCE, binomial).
- **Login advantage.** 5 of the 31 tasks have `requires_login: true` (X, Redfin,
  Expedia, Cars.com, Yelp/OpenTable). FACT (`bench:data/real_world_bench.json`).
  Ego runs with the user's imported sessions; the others "start a browser with an
  empty profile and no logins" by ego's own description (FACT,
  [product intro](https://lite.ego.app/document/en/docs/product-introduce)). 5/31 is
  16.1 points, almost exactly ego's lead over browser-harness (93.5 − 77.4 = 16.1).
  INFERENCE: the success gap may be mostly logins, not tooling. How competitors were
  configured for these tasks is not published.
- **Home turf.** The harness ships only the ego-browser adapter ("Only ego-browser
  ships in the box"); the competitor adapters and the October raw runs are not in
  the repo, despite "tasks, rubrics, and raw results are open source". FACT
  (`bench:config.yaml`, browser tools comment; no `runs/` directory; only
  `bench:reports/ego-benchmark-model-metrics-2026-08-04.md`). Tasks are "calibrated
  against live sites" by the same team (FACT, `bench:data/README.md`). The skill is
  tuned on the same tasks (INFERENCE).
- **Same-family judge.** Agent `gpt-5.6-sol`, judge `openai/gpt-5.6-terra`. FACT
  (`bench:config.yaml`). Not wrong, but not independent (INFERENCE).
- **Internal inconsistency.** Their August model report, also ego-browser with
  GPT-5.6-sol on the same 31 tasks (medium thinking), shows 87.1% perfect, $2.87
  per task, 629 s. FACT (`bench:reports/ego-benchmark-model-metrics-2026-08-04.md`).
  The marketed run (max thinking) is cheaper and 37% faster with a higher score.
  Possible because the SDK changed between batches, but it shows ego-vs-ego
  variance as large as the ego-vs-others gaps. INFERENCE.
- **What does look real.** Turns: 26.5 for ego versus 44–51 for the others (FACT,
  chart). Fewer turns from batching is mechanically plausible and consistent with
  their separate heredoc experiment. INFERENCE. The success rate and per-task cost
  claims are weakly supported; the "fewer turns" claim is the one to believe.

## Build, release, and engineering

- **Cadence.** 24 macOS versions from 0.4.2.21 (2026-06-24) to 0.6.1.11
  (2026-10-26), about weekly, plus a parallel Windows line. FACT
  ([changelog](https://lite.ego.app/changelog)). Chromium moved 150 → 152 → 154 →
  156 between July and October. FACT (changelog 0.5.0.28, 0.6.0.12, 0.6.1.9;
  issue [#314](https://github.com/citrolabs/ego-lite/issues/314) env). Ego is two
  Chromium majors ahead of rac's 154. FACT for both versions.
- **Signing.** A user reports official macOS builds 0.4.1.7–0.4.6.14 fail strict
  `codesign` verification with an invalid entitlements blob though notarized;
  maintainers could not reproduce. Open. CLAIM by reporter
  ([#292](https://github.com/citrolabs/ego-lite/issues/292)). The agent install
  script strips `com.apple.quarantine` (with sudo if needed) and runs no
  signature or hash check before launching. FACT
  (`ego:skills/ego-browser/scripts/install.sh:69-74, 185-188`). Windows builds get
  antivirus false positives (FACT, [blog post 2026-10-20](https://lite.ego.app/blog/how-to-troubleshoot-anti-virus-software-flagging-ego-for-windows-as-a-virus)).
- **Updates.** In-app updater with reminders, `ego-browser upgrade`, and the CLI
  and skill auto-sync after a browser update. FACT (changelog 0.4.3.9, 0.4.4.15).
  The macOS update mechanism (Sparkle, Omaha, custom) is not documented (open
  question). Download URLs carry referral channels (`/channel/github_github_referral/`)
  that feed the acquisition analytics. FACT (#292 archive URL; privacy policy).
- **Repo engineering.** Node's built-in test runner, colocated tests, a
  self-contained real-browser e2e suite (40 case files: OOPIF, shadow DOM, dialogs,
  downloads, drag, keyboard, popups) run against the installed app, lefthook, CI
  with `npm audit`, style, tests, plugin tests, release payload as a tarball. FACT
  (`ego:package/ego-browser/scripts/real-browser-e2e/cases/`;
  `ego:.github/workflows/ci.yml`). The maintainers use Codex to answer issues
  ("Written by liuwd8, sent by Codex operating ego-lite"). FACT (#285, #343).
- **Writing the browser spec in public.** The `docs/native-*.md` files are
  requirement docs with acceptance tests the closed native team must pass (dialog
  handling, snapshot compaction, iframe refs, SDK disposal). FACT. A nice pattern
  for a small team where one side is agent-written (INFERENCE).
- **Stability.** Many crash fixes per release (SIGTRAP in CrBrowserMain, UAF in
  AppKit mouse path, snapshot crash on openai.com/news). FACT (changelog; issues
  [#555](https://github.com/citrolabs/ego-lite/issues/555),
  [#459](https://github.com/citrolabs/ego-lite/issues/459),
  [#558](https://github.com/citrolabs/ego-lite/issues/558)).

## Strengths and weaknesses

**Strengths**

1. **Code, not commands.** One script does many steps with loops and data
   handling, then prints the next snapshot. Fewer turns is the most credible win.
   FACT for the design; the 26.5-vs-44+ turns figure is CLAIM but plausible.
2. **Bring your own agent, zero config.** Install the app, and every agent on the
   machine has a skill whose guide can't drift from the binary. FACT.
3. **Spaces as the unit of agent work.** Parallel tasks, labelled pages that
   persist across calls, handoff and takeover, and the user's tabs protected.
   FACT.
4. **Refs designed properly.** Identity keyed on frame, node, and document;
   partial-merge; persisted across processes; plus validated stable locators.
   FACT.
5. **No CDP port by default**, CDP scoped to the selected Space in-process. FACT.
6. **Shipping speed and Chromium currency.** Weekly releases, Chromium 156. FACT.
7. **Honest internal docs.** `clearing-state.md` measures and warns about the
   profile-wide reach of cookie commands. FACT.

**Weaknesses**

1. **Model-written code gets raw CDP plus network egress in the user's real
   profile**, so cookies and sessions are exfiltratable by injection. Open since
   2026-08-24. FACT (#315, #319, #303).
2. **No approval layer** for payments, sends, deletes; official guides tell users
   to disable their agent's approvals. FACT.
3. **"Isolated" Spaces share the cookie jar**, and the docs say otherwise. FACT.
4. **Any same-user process can drive the browser at any time** through the
   singleton socket; ego even stays resident in the tray. INFERENCE plus FACT.
5. **Telemetry and crash reports on by default**, with identifiers; a privacy
   policy that mentions selling data. FACT that the policy says so.
6. **GPU and CPU cost of the agent overlay** measured by several users. FACT.
7. **Benchmark marketing** rests on one run of 31 self-chosen tasks with a likely
   login advantage. FACT and INFERENCE.
8. **Closed browser**; terms ban reverse engineering. Nothing to reuse below the
   SDK. FACT.

## What rac should take and avoid

### In plain English

Copy how ego lets *outside* agents in: one install, a skill that prints its own
up-to-date guide, and agent work in its own space that never grabs your mouse. Copy
the idea of doing several steps per call, but as a list of steps rac checks one by
one, not as free code. Copy ego's stable element names so an agent can find a
button again after the page changes.

Don't copy the danger. Ego hands the agent's code the keys to every cookie and
doesn't ask before you pay. rac already asks before risky steps; keep that, and
apply it to outside agents too. Don't copy the always-on glow that eats the GPU,
the telemetry, or the benchmark marketing.

### Precise comparison with rac today

rac facts below are from `docs/internals/ai.md` ("The rac MCP server", "The
agent", "The guard", "Containment") and `patches/rac/agent/01-snapshot.patch`.

| Topic | rac today | ego(lite) |
| --- | --- | --- |
| Who can drive it | Only the ACP agent rac launched, only during a run, only with AI on and browser control on (FACT, ai.md:307-331, 355-361) | Any shell-capable agent, any time the app runs, no AI setting involved (FACT) |
| Transport | Per-run MCP over a Unix socket at `<profile>/rac-agent-mcp/<token>/s`, dir 0700, socket 0600, same-UID check; reached with `nc -U`; any same-user process can connect during a live run (FACT, ai.md:312-321) | CLI helper over Chromium's ProcessSingleton socket into a Node utility process; no token; same-user only by OS permissions; available whenever ego runs (FACT for transport, INFERENCE for auth) |
| Tool style | One MCP or direct tool call per action; 4 read tools, 11 action tools; 25-call cap per turn (FACT, ai.md:388-392, 575-577) | One Node script per call with ~60 methods, `evaluate`, `fetch`, raw CDP, Node `fetch` and `fs`; no cap (FACT) |
| Snapshot source | Browser-assembled APC (renderer layout walk), walking into iframes by document token; a redacted iframe becomes `- iframe [redacted]` (FACT, `01-snapshot.patch:789-818`) | Native closed engine, AX-tree based (CLAIM), includes OOPIF content (FACT) |
| Snapshot line | `- button "Sign in" [ref=e6] [submit]` (FACT, ai.md:369-371) | `button "Save" [ref=11, loc=role:button[name="Save"]]` (FACT) |
| Scope and size | Viewport-ish with deltas on the same URL; `full:true` for offscreen (FACT, ai.md:377-379) | Viewport default, `full_page`, `subtree` by ref; compaction; no deltas (FACT) |
| Ref identity | Tab + document + DOM node; numbers never reused; `stale_ref` after document replacement (FACT, ai.md:373-375) | Frame + backend node + document; persisted across processes; partial-merge; invalid ref means re-snapshot (FACT) |
| Stable re-find | None beyond refs (INFERENCE from ai.md) | `loc=` locators validated unique, plus text/role/CSS/XPath selectors (FACT) |
| Redaction | Password and payment values `[redacted]` (FACT, ai.md:376) | None documented (INFERENCE) |
| Published vs private | Approvals bound to the last snapshot shown to the model; TOCTOU re-checks at mouse down, up, between keys (FACT, ai.md:380-386, 487-495) | None; actions resolve current DOM (INFERENCE from `element-resolver.ts`) |
| Risky steps | Always a card at every level: submits, Enter, password/payment/file fields, buy/send/post/delete/sign in/upload, unclassifiable targets (FACT, ai.md:422-429) | No card; agent prose only; host approvals recommended off (FACT) |
| Levels and rules | `ask` / `careful` / `auto` plus per-site Always/Never (FACT, ai.md:436-468) | None (FACT) |
| Containment | Navigation, download, popup, file picker hooks bound to approved origins; survives Stop (FACT, ai.md:502-544) | Permission prompts and device choosers hand the Space to the user; CDP refused while user-owned (FACT) |
| Where the agent acts | Attached tabs and tabs it opened, in the user's window; ring and pill on the tab; pause on real user input (FACT, ai.md:363-365, 565-569) | Its own Space, never focused; overlay with input lock; user takes over explicitly (FACT) |
| Parallelism | One active turn per profile (FACT, ai.md:343-353) | Many Spaces at once (FACT) |
| Known gap | At `auto`, cross-site navigation plus typing model text into the attached tab needs no card: an exfiltration chain (FACT, maintainer brief) | Raw CDP cookie read plus Node egress: a stronger exfiltration chain (FACT, #315) |

Bottom line: rac's **guard and containment are far stronger** than anything ego
has. Ego's **reach and ergonomics** are far better: outside agents, batching,
parallel Spaces, stable locators, persistent refs. The overhaul should bring ego's
reach to rac's guard, not the reverse. INFERENCE.

### Ranked: what rac should copy, with cost

Costs are rough agent-thread time on today's patch layout (INFERENCE). Items marked
"see agent-stacks" overlap that dossier's ranked list and should be planned
together.

1. **Outside agents through a bundled helper plus a self-printing skill.** A
   signed `Contents/Helpers/rac` with `rac skill` (prints the guide that matches
   this build, with begin and end marker lines so truncation is visible) and `rac
   mcp` (stdio relay for MCP clients). A one-click "Add to my agents" writes a
   two-line stub to `~/.agents/skills/rac` and `~/.claude/skills/rac` only when the
   user clicks, and never overwrites a user copy (ego's rule,
   `ego-browser-skill-command.md:72-85`). Off by default, independent of AI on/off,
   per the "Outside agents" setting in agent-stacks items 14 and 16. **Cost: M
   (1–2 weeks).** Highest value: rac can't be driven from outside at all today.
2. **Agent-owned Spaces with ownership states.** rac already has spaces. Add an
   owner (`user`, `agent:<client>`), a handoff and takeover pair, protected user
   tabs, labelled agent pages that persist across calls, background tabs muted, no
   focus or window activation from agent Spaces, auto-close after idle, and a page
   budget. Stable error codes with reasons (`USER_IN_CONTROL: notifications`) and a
   distinct code for automatic delegation, so agents don't stall like ego's #314.
   Replaces "one turn per profile" with one turn per agent Space. **Cost: L (3–4
   weeks).** This is the agent-stacks item 15 session model, with ego's Space
   semantics as the spec.
3. **Batched steps, checked one by one.** A `run_steps` tool (and CLI verb) that
   takes an ordered list of rac actions plus waits and a final `snapshot`, runs them
   in one call, stops at the first failure or card, and returns per-step receipts
   and the last snapshot. Every step still passes `ActionGuard` and containment;
   at most one card per risky step. This captures ego's turn savings without
   arbitrary code. **Cost: S–M (3–6 days)** on top of agent-stacks item 5.
4. **Stable locators in the snapshot.** Emit `loc=role:button[name="Save"]` (or a
   CSS id) only when it re-resolves uniquely to the same node, validated before
   printing (ego's rule, `native-snapshot-ref-requirement.md:62-80`). Accept `loc=`,
   `text=`, and role selectors as targets, resolved to a ref and then guarded like
   a ref. Approvals still bind to the published node. **Cost: M (1 week).**
5. **Snapshot scope and compaction.** `scope: viewport | full | subtree(ref)` where
   a subtree root can be an iframe's ref; ego's compaction rules (drop empty text,
   collapse single-child unnamed containers, keep iframe/image/canvas/cell). Keep
   rac's deltas (agent-stacks item 1). **Cost: S (2–3 days).**
6. **Action receipts.** Return popups opened (as new agent pages), a dialog that
   opened, and downloads, instead of always a full snapshot; dialogs gate other
   tools until handled. Same as agent-stacks items 2 and 3 (`handle_dialog`); ego is
   one more data point that receipts work. **Cost: S–M.**
7. **Persistent ref state for outside clients.** If an outside agent calls rac once
   per shell command, refs must survive between calls: keep the ref table per agent
   Space in the browser (rac already owns it in-process, unlike ego's Node, so no
   disk ledger is needed). **Cost: S.** INFERENCE: rac's browser-side ref table
   makes this cheaper than ego's design.
8. **A visible action label.** Ego's 3–6 word `label` per pointer action, shown
   next to the agent cursor and in the Space's status text. rac can show it in the
   tab pill and the quiet step rows. Static text, no continuous animation.
   **Cost: S.**
9. **Benchmark with their harness.** `ego-browser-benchmark-framework` is MIT with
   a pluggable browser-tool adapter (`bench:config.yaml`, "browser_tools"). Add a
   rac adapter, run Real-World Bench (31 tasks) and its injection fixture, and the
   rac injection suite from agent-stacks item 10. Run each tool at least 3 times and
   give every tool the same logins. **Cost: M (1 week plus model spend).**
10. **Public requirement docs for the native layer.** Ego's `docs/native-*.md` with
    acceptance tests is a good way to brief agent threads on browser-side work.
    **Cost: S (a habit).**
11. **Site learnings, later.** Per-site notes and small read-only extraction tools,
    loaded only on that domain. Ego hasn't shipped the accumulation step. Treat as
    an idea alongside Pomerado-style recipes. **Cost: L. Low priority.**

### Avoid

- **Arbitrary model-written code with raw CDP and network egress in the user's
  real profile.** It routes around every guard (cookie export, profile-wide clears,
  hidden navigation). If rac ever offers scripting, run it only against a
  throwaway profile, or expose a restricted CDP allowlist that can't read or clear
  cookies. FACT for ego's exposure (#315, #303, #319); INFERENCE for rac.
- **Telling users to disable their agent's approvals.** rac's setup must work with
  the agent's sandbox on, by approving one helper command; the browser holds the
  yes. FACT for ego's guides.
- **Calling Spaces "isolated" when cookies are shared.** Say plainly: "the agent
  uses your logins". If rac wants true isolation, offer an explicitly separate
  profile per agent. FACT for ego's contradiction.
- **Always-on overlays.** Ego's dot-matrix mask, dimming, and glow cost ~40% GPU
  while idle. rac's ring and pill should stay static, with reduced-motion honored.
  FACT for ego's cost.
- **An always-reachable control socket.** Listen only while the "Outside agents"
  setting is on, and only on a per-profile socket with a per-client consent card.
  Don't keep the browser resident just for agents. INFERENCE.
- **Stripping quarantine in an install script** and skipping signature checks.
  FACT for ego.
- **Telemetry and crash uploads on by default.** Breaks rac rule 1. FACT for ego.
- **Benchmark claims from one run of self-chosen tasks**, and comparing a
  logged-in tool against logged-out ones. INFERENCE.
- **Automatic takeover with an error the agent can't distinguish** from a real
  user takeover (#314). FACT.

## Open questions

1. Does ego's ProcessSingleton path or the `ego_cli` service check anything about
   the connecting process (code signature, parent)? Nothing public says so.
2. Does the native bridge now filter `Network.getAllCookies`,
   `Storage.getCookies`, or `Network.clearBrowserCookies`? #303, #315, #319 are
   open; the shipped skill still uses `getAllCookies`.
3. Are agent Spaces separate `BrowserContext`s at all, or tab groups in the
   profile's context? The Space doc and the skill disagree.
4. How were the competitors configured for the 5 login tasks? Where are the
   October raw runs?
5. Does the native snapshot redact password, payment, or OTP values? Does it reach
   closed shadow roots?
6. What is the macOS updater (Sparkle, Omaha, custom), and is the signing problem
   in #292 real? I did not download the DMG to check, per the brief.
7. Is the `NodeService` utility process sandboxed? The script can `fetch` and use
   `fs`, so it likely isn't (INFERENCE).
8. What will "Browser ACP that hosts any harness agent" (roadmap) look like? It
   would overlap rac's ACP design.
9. Does the CCPA "sold and shared" text in the privacy policy apply to the browser?
10. For rac: should outside agents get their own Spaces only (ego's model), or also
    be allowed into a tab the user attaches (rac's current model)? Maintainer's
    call.

## Sources

Website (fetched 2026-10-27; text copies in `/tmp/rac-overhaul/ego-site/`):
[home](https://lite.ego.app/),
[quick start](https://lite.ego.app/document/en/docs/quick-start),
[what is ego(lite)](https://lite.ego.app/document/en/docs/product-introduce),
[Space](https://lite.ego.app/document/en/docs/space),
[Snapshot](https://lite.ego.app/document/en/docs/snapshot),
[ego-browser](https://lite.ego.app/document/en/docs/ego-browser),
[Skills](https://lite.ego.app/document/en/docs/skills),
[Claude Code](https://lite.ego.app/document/en/docs/claude-code),
[Codex](https://lite.ego.app/document/en/docs/codex),
[Cursor](https://lite.ego.app/document/en/docs/cursor),
[OpenCode](https://lite.ego.app/document/en/docs/opencode),
[Hermes](https://lite.ego.app/document/en/docs/hermes-agent),
[OpenClaw](https://lite.ego.app/document/en/docs/openclaw),
[WorkBuddy](https://lite.ego.app/document/en/docs/workbuddy),
[DeepSeek Harness](https://lite.ego.app/document/en/docs/deepseek-harness),
[custom harness](https://lite.ego.app/document/en/docs/custom-agent-harness),
[local model](https://lite.ego.app/document/en/docs/qwen-local),
[Windows quick start](https://lite.ego.app/document/en/docs/windows/quick-start),
[changelog](https://lite.ego.app/changelog),
[roadmap](https://lite.ego.app/roadmap),
[blog](https://lite.ego.app/blog),
[launch post](https://lite.ego.app/blog/browser-for-run-browser-automation-tasks-in-parallel),
[heredoc vs REPL](https://lite.ego.app/blog/heredoc-vs-repl-ai-agents-2026),
[migration safety](https://lite.ego.app/blog/safety-and-privacy-in-ego-lite-browser-migration),
[antivirus post](https://lite.ego.app/blog/how-to-troubleshoot-anti-virus-software-flagging-ego-for-windows-as-a-virus),
[enterprise](https://lite.ego.app/enterprise),
[download](https://lite.ego.app/download),
[privacy](https://lite.ego.app/privacy),
[terms](https://lite.ego.app/terms).

Repo `citrolabs/ego-lite` at `aecc583`: `README.md`, `AGENTS.md`, `CONTRIBUTING.md`,
`install.md`, `spec/agent-skills-spec.md` (a pointer to agentskills.io),
`docs/native-bindings-api.md`, `docs/native-snapshot-ref-requirement.md`,
`docs/native-javascript-dialog-requirement.md`,
`docs/native-sdk-lifecycle-requirement.md`, `docs/ego-browser-skill-command.md`,
`docs/local-runtime-development.md`, `docs/assets/ego-lite-architecture.png`,
`docs/assets/real-world-bench.jpg`, `skills/ego-browser/` (SKILL.md, references,
scripts/install.sh, learnings), `package/ego-browser/skill-body/SKILL.md`,
`package/ego-browser/src/{index,run,helpers,public-api-schema,page-model,page-ref-registry,page-ledger,snapshot-result,browser-runtime,native-gate,page-context-guard,http,update-notice,env,state}.ts`,
`package/ego-browser/src/driver/pointer.ts`,
`package/ego-browser/scripts/real-browser-e2e/cases/{page-oopif,event-isolation,page-shadow-dom}.mjs`,
`plugins/ego/README.md`, `.claude-plugin/marketplace.json`,
`.agents/plugins/marketplace.json`, `.codex/skills/`, `.github/workflows/ci.yml`.

Repo `citrolabs/ego-browser-benchmark-framework` at `f566ac2`: `README.md`,
`config.yaml`, `data/README.md`, `data/real_world_bench.json`,
`ego_bench/{metrics,captcha}.py`, `ego_bench/browser_tools/ego_browser.py`,
`reports/ego-benchmark-model-metrics-2026-08-04.md`.

GitHub issues on `citrolabs/ego-lite`:
[#69](https://github.com/citrolabs/ego-lite/issues/69),
[#188](https://github.com/citrolabs/ego-lite/issues/188),
[#285](https://github.com/citrolabs/ego-lite/issues/285),
[#292](https://github.com/citrolabs/ego-lite/issues/292),
[#302](https://github.com/citrolabs/ego-lite/issues/302),
[#303](https://github.com/citrolabs/ego-lite/issues/303),
[#304](https://github.com/citrolabs/ego-lite/issues/304),
[#314](https://github.com/citrolabs/ego-lite/issues/314),
[#315](https://github.com/citrolabs/ego-lite/issues/315),
[#319](https://github.com/citrolabs/ego-lite/issues/319),
[#343](https://github.com/citrolabs/ego-lite/issues/343),
[#454](https://github.com/citrolabs/ego-lite/issues/454),
[#476](https://github.com/citrolabs/ego-lite/issues/476),
[#548](https://github.com/citrolabs/ego-lite/issues/548),
[#553](https://github.com/citrolabs/ego-lite/issues/553),
[#557](https://github.com/citrolabs/ego-lite/issues/557),
[#574](https://github.com/citrolabs/ego-lite/issues/574); issue list via `gh issue list`
(2026-10-27). Release list and repo stats via `gh` and the GitHub API.

rac: `docs/internals/ai.md` (lines 193–578), `patches/rac/agent/01-snapshot.patch`,
`plans/research/agent-stacks.md`, `plans/context/maintainer-brief.md`.

## Verification

I re-checked the 15 most load-bearing claims against primary sources on
2026-10-27 with direct `grep`, `gh`, and file reads.

| # | Claim | Source checked | Result |
| --- | --- | --- | --- |
| 1 | Repo is MIT with about 20k stars | GitHub API: 20,071 stars, `MIT` | Confirmed |
| 2 | Engine is Chromium 156.0.8078.48 with Node 24.22.1 | Changelog 0.6.1.9 line | Confirmed |
| 3 | v2 snapshot defaults to the viewport | `public-api-schema.ts:243` "defaults to only_within_viewport" | Confirmed. Native default is `full_page` and v1 docs say full page; the v2 SDK overrides it (`page-model.ts:1718`) |
| 4 | Ref identity is (frameId, backendNodeId, documentId) | `page-ref-registry.ts:211-219` | Confirmed |
| 5 | Ref state persists to `~/.ego-browser/state` | `page-ledger.ts:83-86` | Confirmed |
| 6 | Page budget defaults to 8 | `page-model.ts:3689-3692` | Confirmed |
| 7 | CLI reaches the app through the singleton socket and a `ego.mojom.NodeService` utility process | Issue #188 comments (process args, maintainer explanation) | Confirmed as maintainer statement plus observed process args; no public code |
| 8 | No CDP port by default; opt-in in Settings | Issue #285 maintainer replies | Confirmed |
| 9 | Spaces share the profile cookie jar despite the docs' "isolated BrowserContext" | `clearing-state.md:3, 12-14`; Space doc line "One isolated BrowserContext per task"; #303 | Confirmed contradiction |
| 10 | Agents can read auth cookies via raw CDP, contrary to the privacy policy | `clearing-state.md:48` uses `Network.getAllCookies`; privacy policy "cannot ... read ... authentication cookies"; #315 maintainer "behaviors ... do exist" | Confirmed. Not tested live; native filtering added after 2.1.0 would change this |
| 11 | No payment or purchase approval in the SDK or guide | `grep` of `skill-body/SKILL.md` for payment/purchase: 0; no guard code in `src/` | Confirmed for the open side; the closed browser could have hidden checks, but none are documented |
| 12 | Official guides tell users to bypass agent approvals | Claude Code doc ("can only be controlled normally when Claude has Bypass permissions turned on", `--dangerously-skip-permissions`); Codex doc (`--dangerously-bypass-approvals-and-sandbox`) | Confirmed |
| 13 | Crash reports on by default; analytics with user and device identifiers | Privacy policy "Crash reports" and "Usage analytics" paragraphs | Confirmed |
| 14 | Benchmark is one run for ego on 31 tasks, with 5 login tasks | Chart footnote ("ego-browser and chrome-devtools-cli ran once"); `real_world_bench.json` (31 tasks, 5 `requires_login`) | Confirmed. The login-advantage explanation remains INFERENCE |
| 15 | Install script strips quarantine without signature checks; agent Spaces auto-close after 30 idle minutes | `install.sh:72, 187` (`xattr -dr com.apple.quarantine`, no `codesign`/`spctl`); changelog 0.6.0.12 | Confirmed |

One correction made during verification: I first assumed the v2 snapshot default
was full page (the website docs say so). The code says viewport; the dossier now
says viewport for v2 and notes the older default.
