# Open browser-agent stacks: research dossier

Subjects: [browser-use](https://github.com/browser-use/browser-use), [microsoft/playwright-mcp](https://github.com/microsoft/playwright-mcp), [ChromeDevTools/chrome-devtools-mcp](https://github.com/ChromeDevTools/chrome-devtools-mcp), [browserbase/stagehand](https://github.com/browserbase/stagehand), [nanobrowser/nanobrowser](https://github.com/nanobrowser/nanobrowser), [vercel-labs/agent-browser](https://github.com/vercel-labs/agent-browser). Two reference points are added where they set the bar: Browser Use's newer [Browser Harness](https://github.com/browser-use/browser-harness) CLI, and Anthropic's [`browser_toolset_20260801`](https://platform.claude.com/docs/en/agents-and-tools/tool-use/browser-use-tool) tool contract.

Research date: 2026-10-25. Code read at these shallow-clone commits (all under `/tmp/rac-overhaul/src/`): browser-use `3df5806` (2026-10-22), playwright-mcp `0c4107a` (2026-10-22), playwright monorepo `8c1b148` (2026-10-25, sparse: `packages/playwright-core/src/tools`, `packages/injected`), chrome-devtools-mcp `ada7963` (2026-10-23), stagehand `8023f34` (2026-10-23), nanobrowser `19dc8e8` (2026-10-24), agent-browser `372ac5c` (2026-10-23), browser-harness `4ced8e0` (2026-10-24). Nothing was installed or run. rac's own code was read in `/Users/knewton/Dev/Github/rac/build/src` (Chromium 154 with Helium and rac patches). That build tree predates `patches/rac/agent/13-permission-levels.patch` through `17-ask-offers-no-site-rule.patch` (its `.pc/applied-patches` ends before them), so claims about the `ask`/`careful`/`auto` levels and site rules come from those patch files and `docs/internals/ai.md`, not from the tree (FACT, checked by the fact-checker; see Verification).

Tags: **FACT** = primary source (code, official docs, GitHub API). **CLAIM** = vendor marketing or self-report, or a third-party write-up. **INFERENCE** = my reasoning.

## In plain English (at most 150 words)

These six open projects let an AI drive a web browser. Most show the AI the page as a short text list of buttons, links, and fields. Each item gets a tag like `e12`. The AI says "click e12", and the tool clicks it. rac already works this way.

The biggest lesson is about cost, not accuracy. In a test Browser Use ran, four such tools scored about the same. Yet one used three times fewer tokens than another. Savings come from sending less text: big page dumps go to a file, repeat views send only changes, and tool lists stay short.

Second, developers want to bring their own agent. They add these tools to Claude Code or Codex with one command. rac can't offer that yet.

Third, nobody has solved prompt injection. The safest designs let the browser, not the AI, hold the "yes".

## Snapshot

Stars, dates, release counts, and contributor counts are from the GitHub API on 2026-10-25 (FACT). "Team size" is the GitHub contributor count, which overstates the core team (INFERENCE).

| | browser-use | Playwright MCP | Chrome DevTools MCP | Stagehand | Nanobrowser | agent-browser |
| --- | --- | --- | --- | --- | --- | --- |
| What it is | Python agent library with its own loop; plus an MCP server, a CLI and skill, and a hosted cloud | MCP server for Playwright; sister `playwright-cli` with skills | MCP server plus `chrome-devtools` CLI, skills, and plugin, for coding agents | SDK (TypeScript, Python, Go) with `act`/`extract`/`observe`; `browse` CLI; eval harness | Chrome/Edge extension: one agent in the side panel, in your real browser | Rust CLI and daemon for agents; MCP server; skills |
| Engine it drives | Chromium over raw CDP (`cdp-use`) | Chromium, Firefox, WebKit through Playwright | Chrome (stable, beta, dev, canary) through Puppeteer; "other Chromium-based browsers may work" (`README.md`) | Chrome over its own CDP driver ("understudy"); v4 runtime runs as a Chrome extension service worker | The browser it is installed in, through `chrome.debugger` | Chrome for Testing over raw CDP; also Lightpanda, Obscura, Safari/iOS through WebDriver |
| Platforms | Any OS with Python 3.11+ | Any OS, Node 18+ | Any OS, Node LTS; Android over adb | Any OS; Node 22.18+ for the CLI | Chrome and Edge only | macOS arm64/x64, Linux arm64/x64, Windows x64 native binaries |
| License | MIT | Apache-2.0 | Apache-2.0 | MIT | Apache-2.0 | Apache-2.0 |
| Repo | [browser-use/browser-use](https://github.com/browser-use/browser-use) | [microsoft/playwright-mcp](https://github.com/microsoft/playwright-mcp) (source in [microsoft/playwright](https://github.com/microsoft/playwright) `packages/playwright-core/src/tools`) | [ChromeDevTools/chrome-devtools-mcp](https://github.com/ChromeDevTools/chrome-devtools-mcp) | [browserbase/stagehand](https://github.com/browserbase/stagehand) | [nanobrowser/nanobrowser](https://github.com/nanobrowser/nanobrowser) | [vercel-labs/agent-browser](https://github.com/vercel-labs/agent-browser) |
| Stars | 119,110 | 38,619 | 54,123 | 25,806 | 14,178 | 44,574 |
| Age (repo created) | 2024-10-31 (about 2 years) | 2025-03-21 (19 months) | 2025-09-11 (13 months) | 2024-03-24 (31 months) | 2024-12-31 (22 months) | 2026-01-11 (9.5 months) |
| Release cadence (releases total / last 6 months) | 140 / 17; latest 0.13.13 on 2026-10-15 | 73 / 13; still `0.0.x` (0.0.83 on 2026-09-28) | 64 / 19; 1.12.0 on 2026-10-22, about every 1–3 weeks | 82 / 26 across several packages (server, SDK, `browse`) | 16 / 2; 0.3.0 rewrite on 2026-10-15 | 114 / 33; 0.39.2 on 2026-10-22, about weekly |
| Team size (GitHub contributors) | 360 | 69 (wrapper repo; real code is in the Playwright monorepo) | 156 | 48 | 25 | 117 (332 open issues plus 369 open pull requests; GitHub's `open_issues_count` of 701 counts both) |
| Business model | Browser Use Cloud: stealth browsers at $0.02/browser-hour, BU2 model through a paid gateway, hosted agent API (CLAIM, `README.md`) | None; Microsoft developer tool | None; Google developer tool; usage statistics on by default | Browserbase cloud browsers, model gateway, server-side action cache (CLAIM, `README.md`) | Free; GitHub sponsors; anonymous PostHog counts on by default | Free Vercel Labs project; ties into Vercel Sandbox and AI Gateway |
| Code size (measured) | 68.8k Python lines in `browser_use/` | ~28.0k TypeScript lines in `playwright-core/src/tools` + `packages/injected` (31.8k counting every file, including Markdown skills) | 28.5k own TypeScript lines (plus a 60.8k-line bundled Lighthouse) | ~106k TypeScript lines in `extension`, `sdk-ts`, `protocol`, `cli` including tests; ~49k without test files | 46.7k TypeScript lines (non-test) | 107.6k Rust lines in `cli/src` |

## Features

These are agent stacks, not browsers, so the browser-shaped groups map loosely. **S** = shipped, **B** = beta, experimental, or behind a flag, **P** = planned, **—** = absent, **n/a** = does not apply. All FACT from each repo's README or code unless marked.

### Tabs, sidebar, spaces (here: tabs and isolation)

| Feature | browser-use | Playwright MCP | DevTools MCP | Stagehand | Nanobrowser | agent-browser |
| --- | --- | --- | --- | --- | --- | --- |
| Multi-tab tools | S (`switch`, `close` by short tab id) | S (`browser_tabs`: list/new/close/select by index) | S (`pageId` required on every page tool; `--page-id-routing` default true) | S (`context.pages()`) | S (`tabs` tool) | S (`tab list/new`, `--pin-tab`, `tab_gone` error) |
| Agent gets its own tab group | — | S (extension: one named, colored group per client; "a tab can belong to a single client at a time") | — | — | S (each task in its own tab group) | — (per-session tab binding instead) |
| Isolated cookie context per tab | — | S (`tab-new --isolated-context`) | S (`new_page` `isolatedContext`) | — | — | S (`--session`) |
| Background tabs without focus steal | S (Harness: `new_tab()` does not change the visible tab) | S | S (`new_page` `background`) | S | S | S |

### Navigation and command bar

| Feature | browser-use | Playwright MCP | DevTools MCP | Stagehand | Nanobrowser | agent-browser |
| --- | --- | --- | --- | --- | --- | --- |
| Navigate, back, forward, reload | S | S | S (`navigate_page` type url/back/forward/reload) | S | S | S |
| Web search tool | S (`search`) | — | — | S (Browserbase Search API, cloud) | — | — |
| Fetch a URL as Markdown without a browser | — | — | — | S (`browse` Fetch API, cloud) | — | S (`read`, with `llms.txt` and `.md` discovery) |
| Natural-language action | S (agent) | — | — | S (`act("click the sign in button")`) | S (agent) | B (`chat`, needs Vercel AI Gateway key) |

### Split view, peek, small windows

n/a for all six. Related: viewport resize (Playwright, DevTools MCP, agent-browser), mobile emulation (Playwright `--mobile`, "mobile pages are usually lighter, which saves tokens"; agent-browser `mobile` profile).

### Import, sync, profiles (here: logged-in sessions)

| Feature | browser-use | Playwright MCP | DevTools MCP | Stagehand | Nanobrowser | agent-browser |
| --- | --- | --- | --- | --- | --- | --- |
| Own persistent profile | S | S (one per MCP workspace hash under `~/Library/Caches/ms-playwright/mcp-{channel}-{hash}`) | S (`~/.cache/chrome-devtools-mcp/chrome-profile`) | S (`userDataDir`) | n/a (is the user's browser) | S (`--profile <path>`) |
| Attach to the user's running browser | S (Harness via `chrome://inspect` + Allow) | S (`--extension` with approval or token; CLI `attach --cdp=chrome`) | S (`--autoConnect`, Chrome 144+, Allow dialog) | S (`--auto-connect`, `--cdp`) | S (native) | S (`--auto-connect`, `--cdp`) |
| Copy of the user's profile | — | — | — | — | — | S (`--profile Default` copies to a temp dir) |
| Save/load storage state | S (cloud profile sync, cookies only) | S (`--storage-state`, `state-save`) | — | S (Browserbase Contexts) | — | S (`state save`, `--restore`, AES-256-GCM option) |
| Credential handling | S (`sensitive_data` placeholders, `<secret>name</secret>`) | S (`--secrets` dotenv: response redaction only) | — | S (`observe()` returns a selector; your code fills the secret) | S (password, card, and code values masked; secret entry is the user's step) | S (`auth` vault, encrypted; "The LLM never sees passwords") |

### Privacy and blocking

| Feature | browser-use | Playwright MCP | DevTools MCP | Stagehand | Nanobrowser | agent-browser |
| --- | --- | --- | --- | --- | --- | --- |
| Domain allow/block | S (`allowed_domains`, `prohibited_domains`, `block_ip_addresses`) | S (`--allowed-origins`, `--blocked-origins`; "*does not* serve as a security boundary and *does not* affect redirects") | S (URLPattern allow/block, enforced on redirects and subresources; unenforceable patterns rejected) | S (`domainPolicy.ts`, CDP Fetch) | S (site Block) | S opt-in (`--allowed-domains` also blocks WebSocket, EventSource, `sendBeacon`, WebRTC, workers) |
| Output redaction | S (sensitive data filter) | S (`secrets`, `redactUrlParams`) | B (`--redactNetworkHeaders`, default off) | — | S (masking) | S (`--max-output`, `--content-boundaries`) |
| Telemetry by default | **On**: PostHog EU, keyed to a persistent device id (a UUID saved at `~/.config/browseruse/device_id`, else a hash of MAC address and hostname) (`config.py:58-59`, `telemetry/service.py:22-63, 136-141`) | None found in `tools/` | **On**: Google Clearcut usage stats; CrUX URL lookups on; npm update checks (`README.md:35-60`) | Your own OTel sink; Browserbase only if configured | **On**: PostHog daily count and usage counts, no ID (`PRIVACY.md`) | None found |

### AI assistant

| Feature | browser-use | Playwright MCP | DevTools MCP | Stagehand | Nanobrowser | agent-browser |
| --- | --- | --- | --- | --- | --- | --- |
| Built-in chat UI | — (library) | — | — | — | S (side panel, history, edit and rerun, export) | B (`chat` CLI and dashboard tab) |
| Providers | OpenAI, Anthropic, Google, Ollama, Browser Use gateway, more | n/a (client brings model) | n/a | Any via AI SDK, or Browserbase model gateway | Anthropic, OpenAI, Gemini, OpenRouter, xAI, DeepSeek, Mistral, OpenAI-compatible, Ollama, LM Studio | Vercel AI Gateway only |
| Local models | S (Ollama) | n/a | n/a | S (OpenAI-compatible) | S (Ollama, LM Studio; recommends Qwen3.8 27B, 16k+ context) | — |
| Voice, attachments, memory | — | — | — | — | S (voice via OpenAI/Gemini, images, files, custom instructions) | — |

### Agent

| Feature | browser-use | Playwright MCP | DevTools MCP | Stagehand | Nanobrowser | agent-browser |
| --- | --- | --- | --- | --- | --- | --- |
| Own agent loop | S (planning, judge, loop detection) | — (the MCP client is the agent) | — | **Removed in v4**: "`agent()` is gone" (`packages/docs/v4/migrations/v3.mdx:9-24`) | S (one loop; old planner and navigator removed in 0.3.0) | B (`chat`) |
| Permission modes | — (domains only) | — (relies on client prompts) | — (relies on client prompts) | — | S (Ask default, Auto; site Allow/Ask/Block) | S opt-in (`--action-policy`, `--confirm-actions`) |
| Screenshots / vision | S (`use_vision` default true) | S (screenshot; coordinate tools behind `--caps=vision`) | S (screenshot; `click_at` behind `--experimentalVision`) | S | S (vision models only) | S (`screenshot --annotate`: numbered labels match refs) |
| WebMCP (page-declared tools) | — | S (default on; offered as dynamic MCP tools) | B (category flag; Chrome 150+ with `--enable-features=WebMCP`) | S | — | B (default on in managed Chrome) |
| Deterministic replay | S (`load_and_rerun` with variables) | S (each response shows equivalent Playwright code) | — | S (action cache, "self-heals") | — | S (`batch`, saved state) |

### Extensibility (CLI, MCP, API, extensions, mods)

| Feature | browser-use | Playwright MCP | DevTools MCP | Stagehand | Nanobrowser | agent-browser |
| --- | --- | --- | --- | --- | --- | --- |
| MCP server | S (`uvx browser-use --mcp`, 16 tools incl. `retry_with_browser_use_agent`; `mcp/server.py:221-451`) | S (25 tools by default, 72 in all with every `--caps` group; the monorepo defines 83, but 11 are CLI-only `skillOnly` tools that MCP never serves) | S (~60 tools; `--slim` 3 tools) | via eval surfaces and Browserbase's separate MCP (not verified) | **P**: "Applications outside the extension will use it through an MCP bridge in future" (`AGENTS.md:25`) | S (`agent-browser mcp`, profiles `core` … `all`) |
| CLI for shell agents | S (`browser-use` with Python heredocs) | S (`playwright-cli`) | S (`chrome-devtools`, background daemon) | S (`browse`) | — | S (the product) |
| Skills | S (`browser-use skill install`) | S (`playwright-cli install --skills=claude\|agents`) | S (7 skills; Claude Code plugin marketplace; Gemini extension) | S (`browse skills add <site>` from browse.sh) | P ("skills the model loads" not in first release) | S (`npx skills add vercel-labs/agent-browser`; thin stub; `skills get core`) |
| Code mode (agent writes a script) | S (Harness: agent edits `agent_helpers.py`) | S (`browser_run_code_unsafe`, "RCE-equivalent", in the default set) | S (`evaluate_script`) | S (recommended path in v4) | — (page script needs approval) | S (`eval`) |
| Plugins | S (custom tools, `@tools.action`) | — | — | — | — | S (out-of-process plugins with declared capabilities) |

### Other

| Feature | browser-use | Playwright MCP | DevTools MCP | Stagehand | Nanobrowser | agent-browser |
| --- | --- | --- | --- | --- | --- | --- |
| Tracing, video, HAR | S (HAR, GIF, recordings) | S (trace, video, chapters, action callouts) | S (performance traces, screencast) | S (OTel) | — | S (HAR, trace, video, profiling) |
| Debugging depth | — | S (console, network, routes) | **S, best in class** (Lighthouse, heap snapshots, CSS cascade, source-mapped console, CrUX) | — | — | S (console, React tree, Web Vitals) |
| Live view for humans | S (cloud) | S (`show --annotate` dashboard) | S (DevTools comments for the agent) | S (cloud) | S (glowing page border) | S (dashboard on port 4848, live viewport stream) |
| Evals in repo | S (eval-on-PR via private platform) | Tests only | S (30 Gemini-driven scenarios) | S (WebVoyager, Online-Mind2Web, WebTailBench, Odysseys, HardBench; tool-surface comparisons) | S (fixture tasks and injection attacks, run by hand) | S (skill-loading evals, CLI-vs-MCP context footprint) |

## UI, look, and feel

Five of the six are libraries or CLIs with no user-facing chrome. What they do show is still instructive for rac's agent surfaces.

### Layout and visual language

- **Nanobrowser** is the only one with a product UI: a per-tab side panel with a chat transcript, confirmation cards, model and effort pickers per chat, `/` shortcuts, and voice input (`README.md` "Key Features"; `src/side-panel/`). It speaks plain words to users ("You decide what the agent may do", `README.md:56-64`). FACT.
- **agent-browser** ships an observability dashboard on port 4848 with session tabs, a live viewport stream over WebSocket for "pair browsing", and an optional chat tab (`README.md` "Observability Dashboard", "Streaming"). FACT.
- **Playwright** has a dashboard with an annotation mode: the user draws boxes on the live page and types notes; the agent receives "the annotated screenshot, the snapshot of the marked region, and the user's notes" (`playwright-core/src/tools/skills/playwright-cli/SKILL.md`, "Example: Interactive session"). FACT.
- **Chrome DevTools MCP** lets a human point at things through DevTools: the snapshot marks the element "selected in the DevTools Elements panel" (`src/formatters/SnapshotFormatter.ts:44-49`), and `get_devtools_comments` / `resolve_devtools_comment` read comments a human left in DevTools (`src/tools/comments.ts:49-122`). FACT.
- **Browser Harness** prefixes the attached tab's title with a horse marker (♞) by default; `BH_TAB_MARKER=0` turns it off (`browser-use/skills/browser-use/SKILL.md`, Usage). FACT. This changes page-visible state (INFERENCE: a page can read `document.title`).

### Motion (exact values from code)

- **Nanobrowser page border** (`src/extension/border.ts:136-155`, FACT): a fixed, `pointer-events:none` overlay injected into the page inside a closed shadow root. Four 16 px edges with a gradient from violet `rgb(124 92 255 / 0.6)` to blue `rgb(0 115 220 / 0.6)`, masked to fade inward. Show/hide: `transition: opacity 150ms ease`. While working: `animation: breathe 2s ease-in-out infinite alternate` from opacity 0.6 to 1, removed under `prefers-reduced-motion: reduce`. A 2 s `setInterval` removes the border if the extension goes away; `pagehide` removes it for back/forward cache.
- **Playwright video callouts**: `video-show-actions --duration=600 --position=top-right` (ms) annotate each action in recordings (`SKILL.md`, DevTools section). FACT.
- No other stack ships UI motion.

### Signature interactions that feel great

- A human can point and the agent gets a ref: Playwright annotate, DevTools "selected element" (FACT above). rac has nothing like this; a "point at this" pick mode in the sidebar would map directly onto rac refs (INFERENCE).
- The agent lives in a tab group it owns (Playwright extension, Nanobrowser, and Claude in Chrome per the Browser Harness comparison table, `browser-harness/README.md`). Users see at a glance which tabs the agent can touch, and can drag tabs in or out (Playwright extension README, fetched 2026-10-25). FACT for the feature; INFERENCE that it "feels great".
- Working in the background without stealing focus is an explicit rule in Browser Harness ("Never call `activate_tab(target)` automatically") and agent-browser. FACT.

### Things that feel bad

- Per-connection consent fatigue. Chrome's "Allow remote debugging?" sheet appears for every new controller; Browser Harness tells agents to call `mac-approve`, which clicks Allow through macOS Accessibility (`browser-harness/src/browser_harness/macos.py:12-48`). FACT. Consent that a script clicks is not consent (INFERENCE).
- Nanobrowser's infinite 2 s breathing border repaints continuously and lives in page DOM (`data-nanobrowser-border` is visible to page script). FACT for the code; the repaint cost is INFERENCE. rac's rule "nothing that repaints continuously" (`AGENTS.md`) rules this out.
- agent-browser has 332 open issues plus 369 open pull requests, and a 5,587-line `mcp.rs` and 18,698-line `actions.rs`; surface breadth outpaces polish (FACT for counts, INFERENCE for the judgment).
- Playwright MCP is still versioned `0.0.83` after 19 months (FACT), which makes pinning and change tracking awkward (INFERENCE).

## Architecture

### browser-use

- **Process model.** One Python asyncio process. `BrowserSession` (`browser/session.py`, 4,197 lines) talks CDP to Chromium through `cdp-use`, with an event bus and "watchdogs" for actions, DOM, downloads, HAR (`browser/watchdogs/`, `default_action_watchdog.py` 3,758 lines). The `Agent` (`agent/service.py`, 4,188 lines) runs the loop; `tools/service.py` (2,327 lines) registers actions. FACT.
- **Page model.** `dom/service.py` merges the DOM tree, the accessibility tree, and the DOMSnapshot layout (bounds, paint order) into "enhanced" nodes; `dom/serializer/serializer.py` (1,406 lines) turns them into the model text. FACT.
- **Browser Harness** (separate MIT repo, 18,611 stars, created 2026-04-17): a daemon holds one CDP connection to the user's running Chrome; the agent pipes Python to `browser-use <<'PY' … PY`; helpers are pre-imported and the agent may add its own to `agent-workspace/agent_helpers.py` while `src/browser_harness/` "stays protected" (`browser-harness/README.md`). FACT.

### Playwright MCP

- **Process model.** `@playwright/mcp` is a 30-line wrapper (`playwright-mcp/cli.js`) around `playwright-core/lib/tools`. The MCP server runs stdio or HTTP/SSE; HTTP checks `allowedHosts` against DNS rebinding (`mcp/config.d.ts`, `server.allowedHosts`). `BrowserBackend.callTool` parses arguments with Zod, runs the tool, and serializes a sectioned Markdown response (`backend/browserBackend.ts:91-139`, `backend/response.ts`). FACT.
- **Page model.** An injected script computes the ARIA tree in the page (`packages/injected/src/ariaSnapshot.ts`, 554 lines; `roleUtils.ts`, 1,456 lines), then a plugin "distiller" compresses it (`ariaSnapshotDistiller.ts`, 263 lines). FACT.
- **CLI.** `playwright-cli` is a client plus a background daemon over a socket (`tools/cli-client/`, `tools/cli-daemon/`); the same tools run with `skillOnly` extras (`backend/tool.ts`, `skillOnly`). FACT.
- **Extension mode.** `CDPRelayServer` opens a local WebSocket with random `/cdp/<uuid>` and `/extension/<uuid>` paths and relays CDP to the Playwright Chrome extension; without `PLAYWRIGHT_MCP_EXTENSION_TOKEN` "the user has to approve the connection in the browser" (`mcp/cdpRelay.ts:86-160`). FACT.

### Chrome DevTools MCP

- **Process model.** Node server on Puppeteer. `McpContext` (1,328 lines) owns pages; `McpPage` (1,634 lines) wraps each; `McpResponse` (1,958 lines) formats output; collectors keep network and console per navigation (`--maxNavigationSaved` default 3). A separate telemetry watchdog process sends Clearcut events (`src/telemetry/watchdog/`). FACT.
- **CLI.** `chrome-devtools <tool> <pageId> --flags` talks to a background daemon over a Unix socket; the daemon starts the server and browser on first use (`docs/cli.md`, "How it works"). FACT.
- **Connection.** Launch its own Chrome, or attach via `--browserUrl`, `--wsEndpoint`, or `--autoConnect`, which reads `DevToolsActivePort` from the user data dir (`src/BrowserManager.ts:375-420`). FACT.

### Stagehand (v4)

- **Process model.** SDKs (TypeScript, Python, Go) speak bidirectional JSON-RPC defined once in Zod (`packages/protocol/README.md`, `stagehand.v4.json`). The runtime is a Chrome extension service worker (`packages/extension/service-worker.ts`, `rpcRouter.ts`), "next to the browser, cutting round-trip latency on every action" (CLAIM, `README.md`). `understudy/` is its own CDP driver with frames, locators, and "deep locators" through iframes and closed shadow roots. FACT.
- **Services.** `actService`, `observeService`, `extractService`, `cacheService`, `llmService` (`packages/extension/services/`). FACT.

### Nanobrowser (0.3)

- **Process model.** A WXT MV3 extension. The service worker hosts the `RunManager` (1,420 lines), the agent loop (`src/agent/loop.ts`, 1,108 lines), and a deterministic "browser control layer" that reaches CDP only through `chrome.debugger`, uses Puppeteer only as a frame manager, and injects one "probe" as its only in-page code (`AGENTS.md:19-30`). The side panel is React and talks to the worker through one typed message protocol. Data lives in IndexedDB. FACT.
- **Layer invariants** (`AGENTS.md:33-43`, FACT): one identity per action; refs fail closed; retries only before dispatch; no hidden substitution; three outcomes reported separately (dispatched, page reacted, expected state reached); observation is read-only; degrade loudly; bounded everything; disposable state; no model inside; consequential actions need a person. These read almost like rac's own guard rules (INFERENCE).

### agent-browser

- **Process model.** A Rust CLI parses each command and sends it to a per-session Rust daemon over a local socket; the daemon speaks raw CDP (`cli/src/native/cdp/client.rs`) with no Node or Playwright. The daemon exits after 1 hour idle by default, except that the default never closes a headed or user-attached browser (`README.md:1718`). The MCP server is the same binary over stdio (`cli/src/mcp.rs`, 5,587 lines). FACT.
- **Modules.** `native/snapshot.rs` (1,760), `native/element.rs` (1,877, ref map), `native/actions.rs` (18,698), `native/interaction.rs`, `native/webmcp.rs`, `native/stream/` (dashboard and viewport stream), `native/providers.rs` (Browserbase, Browser Use, Kernel, AgentCore and others), `plugins.rs`. FACT.

### How each integrates the engine

| | Integration | Who launches the browser |
| --- | --- | --- |
| browser-use | Raw CDP client | Library, or attach to user's Chrome |
| Playwright MCP | Playwright protocol (patched engines), or CDP relay through an extension | Server, or the user's browser via extension |
| DevTools MCP | Puppeteer over CDP (pipe or WebSocket) | Server, or attach |
| Stagehand | Own CDP driver; runtime as an extension | SDK `localBrowser.launch()` or Browserbase |
| Nanobrowser | `chrome.debugger` from inside the browser | n/a |
| agent-browser | Raw CDP (Rust), WebDriver for Safari | Daemon, or attach |
| **rac (for contrast)** | In-process: Chromium's AnnotatedPageContent and actor framework, no CDP | rac is the browser |

## Data and storage

| | What is stored, where | Encryption | Server component | What leaves the machine by default |
| --- | --- | --- | --- | --- |
| browser-use | Config and profiles under `~/.config/browseruse/` (`config.py:92-107`); saved histories as JSON | None noted for histories; `sensitive_data` saved as placeholders, but "page snapshots and results are saved as they were and can still contain them" (`README.md` FAQ) | Optional Browser Use Cloud; cloud event sync only when authenticated (`sync/service.py:29-55`) | PostHog telemetry on unless `ANONYMIZED_TELEMETRY=false` (FACT, `config.py:58-59`); LLM calls to the chosen provider |
| Playwright MCP | Persistent profile per workspace hash; outputs in `.playwright-mcp/` (CLI: `.playwright-cli/`) in the workspace (`backend/context.ts:554`); optional session log | None | None | Only what the client's model sees; no telemetry found (FACT, grep of `tools/`) |
| DevTools MCP | Profile at `~/.cache/chrome-devtools-mcp/chrome-profile`; files only in allowed roots (temp dir by default) | None | Google Clearcut, CrUX API | Usage stats (tool success, latency, environment; `uid`/`reqid`/`msgid` params blocklisted, `telemetry/transformation.ts`), trace URLs to CrUX, npm update checks (FACT, `README.md:35-60`) |
| Stagehand | Local `userDataDir`; Browserbase Contexts in cloud | n/a | Browserbase API, model gateway, Redis-backed cache | With Browserbase transport, the cache "ships the raw accessibility tree(s) plus the request params" to the API (FACT, `packages/extension/services/cacheService.ts:16-29`) |
| Nanobrowser | IndexedDB in the extension; keys in browser storage | Not stated | None ("There is no Nanobrowser server, and no account", `PRIVACY.md`) | PostHog daily count and usage counts, both on by default, no ID; page content to the chosen model (FACT, `PRIVACY.md`) |
| agent-browser | `~/.agent-browser/` (sessions, auth, config, plugins) | Auth vault always AES-256-GCM, key auto-generated at `~/.agent-browser/.encryption-key`; session state encrypted when `AGENT_BROWSER_ENCRYPTION_KEY` is set; files `chmod 600/700` (`docs/content/docs/security.mdx`) | None; optional cloud providers | Nothing found; `chat` calls Vercel AI Gateway only with a key |

## Agents and AI

This is the core of the dossier. Each subsection ends with how rac compares today. rac's current agent is described in `docs/internals/ai.md` and `plans/research/rac-baseline.md`.

### Where the agent runs

| | Agent runs where | Who is "the agent" |
| --- | --- | --- |
| browser-use | Your Python process (library), or Browser Use Cloud | browser-use's own loop, or the coding agent using the CLI/MCP |
| Playwright MCP | The MCP client (Claude Code, Codex, Cursor, …) | The client's model |
| DevTools MCP | The MCP client | The client's model; Gemini CLI builds its browser subagent on it (`README.md`, "Integrating as a browser subagent") |
| Stagehand | Your code ("code mode") or your own tool loop; v4 removed the built-in agent | You or your coding assistant |
| Nanobrowser | The extension's service worker | Its single built-in agent |
| agent-browser | The coding agent calling the CLI or MCP; optional built-in `chat` | Mostly the outside agent |
| rac | The browser process: direct-provider loop, or an ACP agent rac launches, which calls rac's MCP over a per-run Unix socket | rac's assistant, or Claude Code/Codex/… launched by rac |

**Trend (INFERENCE from the table):** the stacks that grew fastest in 2026 (agent-browser, chrome-devtools-mcp, Browser Harness) are tools for outside agents, not agents. Stagehand deleted its agent: "`agent()` was built for models that couldn't reliably drive a browser on their own" (FACT, `packages/docs/v4/migrations/v3.mdx:16`). This matches the developer comment in the maintainer brief: he wanted Aside's CLI and MCP, not its built-in agent.

### Page representation

| | Source | One line looks like | What gets an id | Notable filters |
| --- | --- | --- | --- | --- |
| browser-use | CDP DOM + accessibility tree + DOMSnapshot layout | `*[4211]<button aria-label=Search />` (HTML-like, tab-indented; `*` = new since last step) (`dom/serializer/serializer.py:1110-1120`) | Visible interactive, scrollable, and iframe elements | Drops elements hidden by paint order; drops children ≥99% inside a "propagating" parent such as `<a>` or `<button>` (`serializer.py:46-58`); collapses SVG; prompt cap 40,000 characters (`agent/views.py:92`); screenshot each step by default (`use_vision=True`, `views.py:62`) |
| Playwright MCP | In-page ARIA computation (own role/name code) | `- button "Submit" [ref=e2]`, plus `[active]`, `[cursor=pointer]`, link URLs (`ariaSnapshot.ts:203-206, 499`; `tests/click.spec.ts`) | In "ai" mode, only elements with a visible box that receive pointer events (`ariaSnapshot.ts:60-70, 225-238`) | Distiller plugins: merge text, drop nameless images, drop names that repeat their content, inline text, unwrap single-child generics (`ariaSnapshotDistiller.ts:256-263`); optional `depth`, `boxes`, subtree `target` |
| DevTools MCP | CDP accessibility tree via Puppeteer, `interestingOnly` unless `verbose` | `uid=1_5 button "Submit" focusable` (2-space indent, no dash) (`formatters/SnapshotFormatter.ts:88-140`) | Every node with a DOM backend id | Drops InlineTextBox; hides text children that only repeat the name; 10 s timeout with a self-healing error (`TextSnapshot.ts:18-80`) |
| Stagehand | Hybrid: accessibility tree + DOM, stitched across frames | `[0-12] button: Submit [checked]` (`understudy/a11y/snapshot/treeFormatUtils.ts:8-15`) | Nodes with a DOM id; id = `frameOrdinal-backendNodeId`, mapped to an XPath (`capture.ts:259, 423`) | Scopes to a focus selector; pierces shadow roots; `ignoreLocators` |
| Nanobrowser | CDP accessibility tree + a probe for layout and form facts | `[e12]` refs on an outline with states and values (`protocol/catalogue.ts:41-47`) | Interactive roles from agent-browser's list plus `DisclosureTriangle` (`core/perception/outline.ts:16-36`) | Masks password, card, and one-time-code values; "states every omission" (`outline.ts:1-4`) |
| agent-browser | CDP `Accessibility.getFullAXTree` + one JS pass for "cursor-interactive" elements | `- button "Submit" [ref=e2]` (`README.md:1257-1270`) | 18 interactive roles (`native/snapshot.rs:107-126`) plus elements with `cursor:pointer`, `onclick`, `tabindex`, or `contenteditable` (`snapshot.rs:772-830`) | `-i` interactive only, `-c` compact, `-d` depth, `-s` scope, `-u` URLs, `--delta`; screenshot `--annotate` labels `[N]` = `@eN` (`README.md:982-1033`) |
| Anthropic toolset (contract) | Executor's choice | `button "Search" [ref_4]` | Executor's choice; `filter: "interactive"` or `"all"` | `depth` default 15; cap 50,000 characters and say so (docs, fetched 2026-10-25) |
| **rac** | Chromium AnnotatedPageContent (actionable mode), in-process | `- button "Sign in" [ref=e6] [submit]`; links add `-> host/path?query`; forms add `[submission=… method=… target=…]` (`snapshot_serializer.cc:472-485, 588-594`) | Actionable controls, links, headings, and list items, keyed on tab + document + DOM node. Every emitted line except a redacted iframe carries a ref; body text is not in the snapshot (`get_page_text` reads it). Only in-viewport elements unless `full:true` (`snapshot_serializer.cc:468-470`) | Hidden-text filter; passwords and payment values `[redacted]`; 48 KiB cap with a visible `[truncated …]` line (`snapshot_serializer.h:22`, `snapshot_serializer.cc:367-379`); deltas for the same URL and title |

FACT for every cell except the "Anthropic toolset" row, which is FACT from Anthropic's docs page.

**What this means for rac (INFERENCE).** rac's line format already matches the two most-used formats (Playwright, agent-browser) almost character for character. Models have seen this format a great deal in 2025–2026 agent traffic. There is no reason to change the basic line. The differences worth acting on are elsewhere: how much is sent per step, how deltas look, and what the agent can do when the tree is not enough (screenshots, coordinates, WebMCP).

### Tool sets and naming

| | Default tool count | Naming | Core set in practice |
| --- | --- | --- | --- |
| browser-use (agent) | about 24 actions | Bare verbs: `navigate`, `click`, `input`, `scroll`, `extract`, `done` (`tools/service.py:458-2178`) | Plus `write_file`/`read_file`/`replace_file` for a scratch file system, `evaluate`, `search` |
| browser-use (MCP) | 16 | `browser_*` | `browser_get_state`, `browser_click`, `browser_type`, … plus `retry_with_browser_use_agent` |
| Playwright MCP | 25 by default, 72 in all (capabilities `vision`, `pdf`, `devtools`, `network`, `storage`, `testing`, `config` opt in). The monorepo's `browserTools` list has 83, but `filteredTools` drops 11 `skillOnly` CLI tools such as `browser_reload`, `browser_navigate_forward`, `browser_webmcp_call` (FACT, README "Tools" lists 72; `backend/tools.ts:83-84`) | `browser_*` | `browser_snapshot`, `browser_click`, `browser_type`, `browser_fill_form`, `browser_find`, `browser_tabs`, `browser_wait_for`, `browser_handle_dialog`, `browser_evaluate`, **`browser_run_code_unsafe`** |
| DevTools MCP | ~60 listed in `docs/tool-reference.md` (several behind flags); `--slim` = 3 | Bare snake_case: `click`, `fill`, `fill_form`, `take_snapshot`, `navigate_page`, `list_pages` | Every page tool takes `pageId` |
| Stagehand | 3 AI primitives + a full Playwright-style page API | camelCase methods | `act`, `observe`, `extract` |
| Nanobrowser | 17 (`protocol/catalogue.ts:41-174`) | Bare verbs | `snapshot`, `find`, `read`, `screenshot`, `click`, `set`, `fill_form`, `type`, `press`, `hover`, `scroll`, `wait`, `navigate`, `tabs`, `upload`, `handle_dialog`, `ask_user` |
| agent-browser (MCP) | `core` profile by default; `all` for full parity (`README.md:585-640`) | `agent_browser_*` | `open`, `snapshot`, `click`, `fill`, `type`, `press`, `wait_for_selector`, `screenshot`, `get_url`, `eval`, `close` |
| Anthropic toolset | 27 default + 4 optional | Bare verbs, `toolset_name: "browser"` | `navigate`, `read_page`, `find`, `get_page_text`, `form_input`, 12 pointer members (11 take viewport coordinates; 6 of those also take a ref), `type`, `key`, tab members |
| **rac** | 15 (`tool_registry.cc`) | Bare verbs; Claude Code sees `mcp__rac__click` | `snapshot`, `get_page_text`, `list_tabs`, `find_in_page`, `click`, `type`, `select_option`, `press_key`, `scroll`, `navigate`, `go_back`, `open_tab`, `switch_tab`, `close_tab`, `wait_for_settle` |

**Gaps in rac's tool set compared with the field (FACT for what rac has, INFERENCE for what matters):**

1. `press_key` is "Press Enter on an element ref" only (`tool_registry.cc:178`). Every peer has general keys (Escape to close a modal, Tab, arrows, shortcuts). Escape is the cheapest way out of most overlays.
2. No `hover`. Menus that open on hover are common (Playwright, DevTools MCP, agent-browser, Nanobrowser, and the Anthropic toolset all have it).
3. No `handle_dialog`. A JavaScript `alert`/`confirm` stalls an agent. Playwright refuses every other tool while a dialog is open and names the one that clears it (`backend/tool.ts:70-82`, modal states).
4. `find_in_page` returns "count + snippets" (`tool_registry.cc:123`), not refs. Playwright's `browser_find`, the Anthropic `find` (up to 20 matches), Nanobrowser's `find`, and agent-browser's `find role … click` all return actionable refs, which saves a full snapshot.
5. No `fill_form`. DevTools MCP's description says "ALWAYS prefer this tool over multiple individual 'fill' or 'click' calls … significantly faster, more reliable, and reduces turn count" (`docs/tool-reference.md:121`). For rac it would also mean one confirm card for a whole form instead of one per field (INFERENCE).
6. No screenshot. Every peer offers one for canvas, icon-only buttons, and visual checks. agent-browser's annotated screenshot keeps refs and labels in sync (`README.md:1012-1033`).
7. No forward or reload. No `wait_for` text.
8. No WebMCP. Chromium 154 in rac's tree already has the `WebMCP` runtime feature (experimental plus origin trial, `third_party/blink/renderer/platform/runtime_enabled_features.json5:7026-7039`), a `WebMCP` CDP domain with `readOnly`, `untrustedContent`, and `consequential` annotations (`third_party/blink/public/devtools_protocol/domains/WebMCP.pdl`), and an actor `ScriptToolHost` (`chrome/browser/actor/tools/script_tool_host.h`). FACT.

### Element addressing and stability

| | Id format | Survives a re-snapshot? | Invalidated by | Fallback when the element is gone |
| --- | --- | --- | --- | --- |
| browser-use | CDP `backendNodeId` used directly as the index when unique, else a synthetic index (`serializer.py:637-658`) | Yes, within a document | Navigation | Re-plan |
| Playwright | `e{N}` from a counter per injected script; iframe prefix such as `f1e2` | Yes, while the element's role and name stay the same (stored on the element as `_ariaRef`, `ariaSnapshot.ts:225-238`) | Role or name change, new document | Also accepts a selector or locator string (`target` = "Exact target element reference from the page snapshot, or a unique element selector", `backend/snapshot.ts:23`) |
| DevTools MCP | `{snapshotId}_{counter}` | Yes: reused when `loaderId_backendNodeId` matches (`TextSnapshot.ts:94-110`) | New document (new `loaderId`) | "Take a fresh snapshot" error |
| Stagehand | `{frameOrdinal}-{backendNodeId}` → XPath | Per snapshot; actions resolve via XPath | DOM change | Self-healing `act()` re-observes |
| Nanobrowser | `e{N}` | "valid only for the document it was seen in and only if the agent was shown it" (`AGENTS.md:34`) | Document change | Typed error, "not a guess" |
| agent-browser | `e{N}`, written `@e2` in the CLI | Yes, "Surviving DOM elements keep their refs across snapshots" (`README.md:984`); keyed by CDP session + document `loaderId` + backend id, with regression tests (`snapshot.rs`, `durable_refs_*` tests) | Replaced document or session | "uses the one element with the same role and name. When duplicates make that ambiguous, the action fails" (`README.md:1279`) |
| Anthropic contract | `ref_N` | "stay valid until that tab navigates or its DOM changes materially"; "Don't renumber references you've already handed out for a tab until it navigates" | Navigation | Executor returns "ref_3 is stale or not found … Re-read the page" |
| **rac** | `e{N}`, never reused | Yes, keyed on tab + document + DOM node | Replaced document → `stale_ref` | None; plus TOCTOU re-checks at mouse down, mouse up, between keys |

**Verdict (INFERENCE).** rac's addressing is the strictest of the group and is in line with Nanobrowser's fail-closed rule. agent-browser's "same role and name, else fail" fallback is the one relaxation worth considering, and only for read-only or already-approved steps, because rac binds approvals to the exact node.

### Reliability tricks worth knowing

All FACT from the cited code; the "use in rac" notes are INFERENCE.

- **Wait after every action, with numbers.** DevTools MCP: wait up to 100 ms for a navigation to start, then up to 3,000 ms for it, then until the DOM has been quiet for 100 ms, capped at 3,000 ms, all scaled by CPU and network multipliers (`src/utils/WaitForHelper.ts:39-42, 250-300`). Playwright: a configurable "settle" of 500 ms after triggered work (`config.d.ts`, `timeouts.settle`). rac: Chromium's page-settled monitor with a 4 s cap (10 s around navigations).
- **Refuse to act on covered or unusable targets.** agent-browser: "Clicks fail early when another element covers the target's click point, for example a consent banner" and the error names the cover, such as `covered by <div#consent-banner>`; it also fails on hidden, disabled, or off-viewport targets instead of "reporting success" (`README.md:101, 1277`).
- **Modal-state gating.** Playwright refuses every tool except the one that clears a pending dialog or file chooser (`backend/tool.ts:70-82`).
- **Three outcomes in every receipt.** Nanobrowser's `ActionReceipt` separates `dispatched`, `reachedTarget`, `effect` (`changed`/`unattributable`/`none` with signals) and `postcondition` (`met`/`unmet`/`not_checked`) (`protocol/results.ts:25-46`). This stops the model from assuming a click worked.
- **Multiple actions per model call.** browser-use runs up to 5 actions per step (`max_actions_per_step=5`, `agent/views.py:71`) and stops the sequence after any action marked `terminates_sequence` (navigation, `tools/service.py:583`). Anthropic's contract: run a turn's calls in order and stop at the first failure, answering the rest with "Not executed: an earlier action in this turn failed." agent-browser: `batch --bail`.
- **Loop and stall detection.** browser-use hashes recent actions over a 20-step window and fingerprints the page (URL, element count, text hash), nudges to re-plan after 3 consecutive failures, and gives up after 5 (`agent/views.py:66-131`). It also runs a judge by default (`use_judge=True`).
- **Self-healing and caching.** Stagehand caches resolved actions and re-observes when the page changes (`services/cacheService.ts`). browser-use replays a saved run with new variables and "raises `RuntimeError` at the first step it cannot match" (`README.md` FAQ).
- **Show equivalent code.** Every Playwright MCP action response includes the Playwright code it ran (`Ran Playwright code` section, `backend/response.ts:280-286`), which lets a coding agent turn an exploration into a test.
- **Cursor-interactive discovery.** agent-browser finds clickable `div`s with `cursor:pointer`, `onclick`, `tabindex`, or `contenteditable` that the accessibility tree misses, skipping elements that only inherit the pointer from a parent (`snapshot.rs:772-830`). Playwright marks the same thing as `[cursor=pointer]`.
- **Page-declared tools first.** agent-browser's core skill: if a WebMCP tool "directly matches the authorized task, prefer that tool to reconstructing the same operation with DOM interactions" (`skill-data/core/SKILL.md`). Playwright: "a single call replaces a sequence of clicks and fills — and it cannot be blocked by a cookie banner" (`playwright-cli/SKILL.md`, WebMCP).

### Token budgets

| | Biggest lever | Default per-step page cost | Notes |
| --- | --- | --- | --- |
| browser-use | Capped DOM text + screenshot | Up to 40,000 characters of elements plus an image (`agent/views.py:92`) | Message compaction; `flash_mode` drops reasoning fields |
| Playwright MCP | **Snapshots after actions are written to a file**; the response carries a link | A few hundred characters plus the link | `snapshotToFile` is true for every implicit snapshot (`backend/response.ts:289`); a re-run benchmark found the old ~4× MCP-vs-CLI gap "has essentially closed" (CLAIM, [DEV Community, 2026-07-24](https://dev.to/aswani25/playwright-cli-vs-playwright-mcp-which-should-you-use-with-claude-code-1olh)); fixed cost is the ~24-tool schema list (~18k characters, same source) |
| DevTools MCP | `includeSnapshot` defaults to **false** on input tools (`docs/tool-reference.md:89`) | The action's one-line result | `filePath` for big outputs; screenshot `--screenshotMaxWidth/Height` and JPEG/WebP (3–5× smaller than PNG, `docs/configuration.md`); `--slim` |
| Stagehand | Trimmed hybrid tree; cache hits cost zero tokens (CLAIM) | n/a | `observe` once, then plain selectors |
| Nanobrowser | Compaction that keeps every user message in full | n/a | Degrades loudly when truncated |
| agent-browser | `snapshot -i`, `--delta` splices, `--max-output`, `screenshot --if-changed`; WebMCP summaries capped at 16 tools and 4 KiB (`README.md:168`) | "~200-400 tokens" per page (CLAIM, `skill-data/core/SKILL.md`) | Thin skill stub; full reference loaded on demand |
| Anthropic toolset | Tree read cap 50,000 characters; `find` ≤20 matches | n/a | Toolset definition adds "roughly 6,600 input tokens per request" (CLAIM, third-party: [digitalapplied.com](https://www.digitalapplied.com/blog/anthropic-browser-use-tool-ga-new-agent-toolset)) |
| **rac** | 48 KiB snapshot cap (~12k tokens at 4 characters per token); delta for the same URL and title | A fresh snapshot (or delta) after every action | Delta format below |

**Matched measurement (CLAIM, vendor-run).** Browser Use ran the same agent (Codex CLI 0.144.6, GPT-6 Luna, medium reasoning) on 100 BU Bench V2.1 tasks with four tools against the same cloud browser on 2026-10-14 (`browser-harness/README.md:58-80`):

| Tool | Mean score (95% CI) | Median input tokens per task | Median cost per task |
| --- | --- | --- | --- |
| Browser Harness | 60.4 (55.2–65.4) | 2.1M | $0.042 |
| Playwright MCP 0.0.83 | 60.0 (55.1–65.0) | 4.4M | $0.066 |
| Chrome DevTools MCP 1.10.1 | 61.0 (55.8–65.9) | 6.7M | $0.097 |
| agent-browser 0.39.1 | 56.3 (51.1–61.5) | 3.3M | $0.056 |

"No tool wins on score: every paired difference … has a 95% CI that includes zero." The token spread is 3.2× (FACT that they published this; the numbers are CLAIM). Limits stated in the same README: only 100 of the 200 tasks, one run per task, Codex only, and every tool drove a shared Browser Use cloud browser, so it "does not measure each tool's default or local-Chrome mode" (FACT, `browser-harness/README.md:58-63, 77`). The maker of one entrant ran it (INFERENCE: treat as indicative). Slack Engineering reportedly saw the opposite trade on one long flow: MCP took ~40 turns and ~3.8M tokens; the CLI took ~85 turns and ~6M (CLAIM, second-hand via [TestMu AI](https://www.testmuai.com/blog/playwright-cli-vs-mcp-vs-kane-cli/)). **INFERENCE:** turn count matters as much as bytes per turn; batching and `fill_form` cut turns, and file-backed or delta snapshots cut bytes.

**rac's delta format costs more than it should (FACT for the code, INFERENCE for the size).** `BuildDelta` writes `- unchanged [ref=eN]` for every unchanged line that has a ref, then the changed lines, then `- removed [ref=eN]` (`snapshot_serializer.cc:694-728`). On a page with 300 refs and 3 changes, that is still ~300 lines of about 6 tokens each, roughly 1,800 tokens, for 3 lines of news. agent-browser's delta is a line splice against a numbered baseline: `startLine`, `deleteCount`, and new `lines`, falling back to full when the splice would not save space (`skill-data/core/references/commands.md:55-59`). A splice for the same change is well under 100 tokens. A second, smaller issue: a line without a ref (the redacted-iframe line or the truncation marker) always counts as a change, so such a page can never get the cheap `unchanged` reply (`snapshot_serializer.cc:705-728`).

### Multi-tab handling

- **Tab ids on every call** win for concurrency. DevTools MCP made `pageId` required on page tools by default "useful for concurrent agent sessions" (`docs/configuration.md:159-162`) and has eval scenarios that check fills land on the right page (`scripts/eval_scenarios/page_id_routing_*`). The Anthropic contract puts an optional `tab_id` on most members and returns a full tab inventory plus `state_changes` (`tab_opened`, downloads) in a `browser_state` block. FACT.
- **Ownership by tab group.** Playwright's extension gives each client its own named, colored tab group; "a tab can belong to a single client at a time"; the user drags tabs in or out to grant or revoke (extension README). Nanobrowser runs each task in its own tab group. FACT.
- **Strict binding.** agent-browser `--pin-tab` makes a closed bound tab a `tab_gone` error with recovery metadata instead of "silently acting on another tab" (`README.md:758-781`). FACT.
- **rac** acts only in tabs the user attached and tabs the agent opened, and has one active turn per profile (`docs/internals/ai.md`, "Who may act" and "The agent"). That is right for rac's own assistant. It will not hold once several outside agents connect at once (INFERENCE).

### Reuse of logged-in sessions

- Three patterns exist (FACT, cited in Features): a dedicated persistent profile the user logs into once (Playwright, DevTools MCP, Stagehand, agent-browser); attaching to the user's real browser over CDP after a consent step (all except Nanobrowser, which is already inside); and moving cookies (agent-browser state files, Browser Use cloud profile sync, Playwright storage state).
- The real-browser path in 2026 is Chrome 144+'s approval mode: tick "Allow remote debugging for this browser instance" at `chrome://inspect/#remote-debugging`, then click Allow per connection (`chrome-devtools-mcp/docs/advanced-usage.md:55-92`; Browser Harness README). DevTools MCP warns: "The MCP server has access to all open windows for the selected profile." FACT.
- **rac already has this path, unpatched (FACT, rac's build tree).** `kDevToolsAcceptDebuggingConnections` is enabled by default on macOS (`chrome/browser/devtools/features.cc:206-210`); approval mode starts when the user flips the pref (`chrome/browser/devtools/remote_debugging_server.cc:216-283, 399-417`); the consent dialog reads "An external app wants full control over this rac session … access to your saved data, cookies and site data, and the ability to navigate to any URL" (`chrome/app/generated_resources.grd:4571-4583`, after rac's dev-name substitution). No Helium or rac patch touches this code (grep of `patches/` and `helium-chromium/patches/`). So `chrome-devtools-mcp --autoConnect --userDataDir=<rac data dir>`, `agent-browser --cdp`, and `playwright-cli attach --cdp` can likely drive rac today, with none of rac's guard, cards, containment, or tab scoping (INFERENCE; not run).
- **rac also accepts `--remote-debugging-port` on the real profile (FACT, INFERENCE on impact).** Chrome 136+ ignores `--remote-debugging-port` and `--remote-debugging-pipe` on the default user data dir to stop infostealers dumping cookies ([Chrome blog](https://developer.chrome.com/blog/remote-debugging-port)). In the code, that check only runs under `GOOGLE_CHROME_BRANDING`; Chromium-branded builds skip it unless a test turns it on (`remote_debugging_server.cc:160-183, 353-395`). rac is Chromium-branded, so a process that relaunches rac with that flag gets the user's whole logged-in profile with no prompt.

### Safety and permission hooks

| | Who holds the "yes" | Mechanisms |
| --- | --- | --- |
| browser-use | Nobody by default | Domain allow/block and IP blocking; loud warning when `sensitive_data` is set without `allowed_domains` ("your sensitive_data may be exposed!", `agent/service.py:534-580`) |
| Playwright MCP | The MCP client's permission prompt | Every element tool has an `element` field: "Human-readable element description used to obtain permission to interact with the element" (`backend/snapshot.ts:25-33`); origins lists "not a security boundary"; file access limited to workspace roots ("a convenience defense … not a secure boundary", `config.d.ts`); `secrets` redaction "is a convenience and not a security feature" |
| DevTools MCP | The MCP client | `readOnlyHint` per tool (`ToolDefinition.ts:124-129`); `--no-javascript-evaluation` ("not a JavaScript sandbox"); `--no-file-navigations`; URL allow/block enforced on redirects and subresources |
| Stagehand | Your code | Domain policy; secrets stay in your code |
| Nanobrowser | **The extension** | Ask (default) or Auto; per-site Allow/Ask/Block; submit, pay, delete detected and gated; "A detected payment, access grant, secret input or page `prompt` dialog is the user's step in every mode, with no Approve" (`AGENTS.md` "For the agent and the extension"); approval bound to a "basis" so "Pay $5" and "Pay $500" differ (`core/interaction/gate.ts:103-113`); re-classified at each input boundary (`assertJudged`) |
| agent-browser | The daemon, if you opt in | "All security features are opt-in" (`security.mdx:8`). `--action-policy` JSON with `default` and `allow`/`deny` categories; a missing or invalid file blocks everything (`security.mdx:221-268`); `--confirm-actions eval,download` returns `confirmation_required` with an id for `confirm`/`deny`, auto-denies after 60 s (`security.mdx:31, 295`); a separate `--confirm-interactive` mode auto-denies when stdin is not a TTY (`security.mdx:32`); MCP tools reject global policy flags in arguments (`README.md:623`) |
| Anthropic toolset | Your executor | Six precautions: dedicated VM, fresh credential-free profile, network-layer allowlist re-checked after redirects, untrusted page data, http(s)-only `navigate`, human confirmation of consequential actions "in your executor before each call, because one turn can carry several" (docs) |
| **rac** | **The browser** | Guard with `ask`/`careful`/`auto`, always-risky list, site rules, published-vs-private snapshots, TOCTOU re-checks, navigation/popup/download containment, critic at `careful`, 25-call cap (`docs/internals/ai.md`) |

**Verdict (INFERENCE).** rac and Nanobrowser are the only two where the browser decides. Everything else defers to the MCP client, the developer's code, or flags nobody sets. rac's design is stronger than Nanobrowser's in containment and TOCTOU, and weaker in one place Nanobrowser got right: payments, secrets, and access grants are handed to the user with no Approve button at all, in every mode.

### Prompt-injection defenses

- **Boundaries with nonces.** agent-browser wraps page output in `--- AGENT_BROWSER_PAGE_CONTENT nonce=… origin=… ---` markers, and calls them "defense-in-depth" that "rely on the LLM and orchestrator respecting the structural markers" (`security.mdx:161-191`). Nanobrowser and rac do the same. FACT.
- **Page-declared tools are untrusted.** agent-browser: "Page-provided `readOnlyHint` or `untrustedContentHint` claims cannot bypass those controls" (`README.md:181`). Playwright labels the list "page-provided, untrusted". FACT.
- **Classifiers.** Anthropic scans what the browser returns "to flag potential prompt injections" for API users of the toolset (docs), and Claude in Chrome adds an action classifier; Anthropic reports attack success "below 0.08% in internal testing" with Opus 4.8 (CLAIM, [support.claude.com](https://support.claude.com/en/articles/12902428-use-claude-in-chrome-safely)).
- **What research says (CLAIM, papers).** WASP: agents were hijacked mid-task 17–86% of the time, but end-to-end attacker goals succeeded at most 16%, "security by incompetence" ([arXiv 2504.18575](https://arxiv.org/pdf/2504.18575)). BrowseSafe++ (2026-10): adaptive rewrites lift success from a few percent to 78.79% on average and up to 95.41%; "some models can recognize prompt injections when asked to detect them, yet still follow those same injections" ([arXiv 2610.17457](https://arxiv.org/html/2610.17457)). INFERENCE: detection-only defenses will not hold for rac's default `auto` level; structural rules (who may type what, where) must.

### Outside-agent access: how each installs into Claude Code and Codex

| | Claude Code | Codex | Shell/skill route |
| --- | --- | --- | --- |
| Playwright MCP | `claude mcp add playwright npx @playwright/mcp@latest` (README) | `codex mcp add playwright npx "@playwright/mcp@latest"` or `[mcp_servers.playwright]` in `~/.codex/config.toml` (README) | `npm install -g @playwright/cli@latest`; `playwright-cli install --skills=claude` or `--skills=agents`, `--global` for home dir (`cli-client/program.ts:205-210, 326-332`) |
| DevTools MCP | Plugin: `/plugin marketplace add ChromeDevTools/chrome-devtools-mcp`, then `/plugin install chrome-devtools-mcp@chrome-devtools-plugins` (README) | MCP config `npx -y chrome-devtools-mcp@latest` | `npm i -g chrome-devtools-mcp`; copy `skills/chrome-devtools-cli` into `~/.claude/skills`; "Update the skills each time you update" (README) |
| agent-browser | `npx skills add vercel-labs/agent-browser` writes a thin stub to `.claude/skills/agent-browser/SKILL.md` (`README.md:1756-1764`) | Same `skills` installer; MCP `agent-browser mcp` | The stub tells the agent to run `agent-browser skills get core` so content "always matches the installed CLI version" |
| browser-use | Paste one setup prompt; `browser-use skill install` (README "Path 2: CLI") | Same | `uvx browser-use --mcp` for MCP |
| Stagehand | `npm i -g browse`; `browse skills add <site>` | Same | Evals can mount it under Claude Code or Codex (`packages/evals/framework/claudeCodeRunner.ts`, `codexRunner.ts`) |
| Nanobrowser | None | None | None (MCP bridge "in future") |
| **rac** | None for outside agents; rac can launch Claude Code itself over ACP | Same | None |

Ergonomics that recur (FACT from the rows above; INFERENCE that rac should copy them): a one-line `claude mcp add` / `codex mcp add` command; a CLI that keeps a background daemon so each call is cheap; a skill that is either tiny and fetches live docs from the binary (agent-browser) or ships with the package (DevTools MCP); tool profiles so the default schema is small (agent-browser `core`, DevTools `--slim`, Playwright capabilities).

### Evals and benchmarks

- **Task benchmarks.** Stagehand's harness runs WebVoyager, Online-Mind2Web, WebTailBench, Odysseys, and HardBench, and can swap the tool surface: `playwright_mcp`, `chrome_devtools_mcp`, `browse_cli`, `anthropic_browser_toolset`, `google_computer_use`, `cdp_code`, and others (`packages/evals/core/tools/registry.ts:1-75`), under harnesses including Claude Code, Codex, and Cursor. FACT. Browser Use publishes BU Bench v2.1 (180 tasks, 2026-10-17 leaderboard) and claimed 97% on Online-Mind2Web with its hosted "bu-max", self-judged (CLAIM, [browser-use.com/benchmarks/agents](https://browser-use.com/benchmarks/agents); [Steel leaderboard note](https://leaderboard.steel.dev/leaderboards/online-mind2web/)).
- **Scenario evals.** DevTools MCP keeps 30 scenarios (`scripts/eval_scenarios/`), each a prompt, a turn cap, and assertions on the tool calls the model made, run with Gemini (`scripts/eval_gemini.ts`). FACT.
- **Injection evals.** Nanobrowser's set has fixture tasks with deterministic graders and "three attacked fixtures with four outcomes each (the attempt, the gate's response, the user's decision, the completed objective)", graded against what the fixture server received at `/submit` (`src/background/checks/eval-tasks.ts:1-80`); 68 HTML fixture pages (plus one stylesheet in `fixtures/pages/`) and a fake OpenAI-compatible model server (`fixtures/`). FACT. This is the closest existing template for the red-team suite rac lacks.
- **Context-cost evals.** agent-browser measures bytes and approximate tokens for its skill, CLI output, MCP `initialize`, the `core` profile, and `--tools all` (`evals/context-footprint.ts`). FACT.
- **CI.** browser-use triggers a private eval platform on PRs from members (`.github/workflows/eval-on-pr.yml`). Nanobrowser runs browser checks and model evals by hand before merges that touch them (`AGENTS.md`, Toolchain). FACT.

### The Anthropic browser toolset as a contract rac could implement

FACT from [the docs page](https://platform.claude.com/docs/en/agents-and-tools/tool-use/browser-use-tool) (fetched 2026-10-25) unless marked. One `{"type": "browser_toolset_20260801"}` entry gives Claude 27 member tools; four more (`javascript_exec`, `file_upload`, `read_console`, `read_network`) are off by default. It went GA on 2026-08-19 (CLAIM, search summary; the docs page marks the tool `ga` but gives no date). The executor, which is the app, assigns `ref_N` refs and `tab_id`s, must validate inputs, must run a turn's calls in order and halt on the first failure, and must "Have a human confirm consequential actions." Browser Use already implements it on its own engine (`browser_use/integrations/anthropic/browser_use.py`, class `BrowserUse(BetaAsyncAbstractBrowserToolset20260801)`).

INFERENCE for rac: for Claude models on the direct Anthropic provider, serving this contract instead of rac's custom tools would put Claude on tools it was trained for and add Anthropic's server-side injection classifier. The cost: 11 of the 12 pointer members accept viewport coordinates, and rac's guard reasons about nodes. Six of them (the five clicks and `hover`) accept a ref instead, and `scroll_to` takes only a ref (FACT, docs "Targets" table). The other five (`left_click_drag`, `left_mouse_down`, `left_mouse_up`, `mouse_move`, `scroll`) take coordinates only. rac would hit-test each coordinate to a node and run the same guard, or refuse coordinate targets when a ref exists.

## Build, release, and engineering

| | Build | CI (`.github/workflows/`) | Ships as | Tests and evals | Tracks upstream |
| --- | --- | --- | --- | --- | --- |
| browser-use | Python, `uv` | `test.yaml`, `lint.yml`, `docker.yml`, `publish.yml`, `eval-on-pr.yml` (private eval platform) | PyPI; Docker | `tests/`; PR evals | Chrome stable via CDP |
| Playwright MCP | Node; the wrapper's `build` is `echo OK` (`package.json`) | `ci.yml`, `publish.yml`; Azure Pipelines publish | npm; Docker; MCP registry `server.json` | Playwright Test across Chromium, Firefox, WebKit, Docker (`package.json` scripts) | Pins Playwright alpha builds, rolled by `roll.js` (`CLAUDE.md`) |
| DevTools MCP | Node, Rollup, release-please | `presubmit.yml`, `run-tests.yml`, `test-memory-leaks.yml`, `publish-to-npm-on-tag.yml`, `publish-to-mcp-registry-on-tag.yml` | npm; Claude Code plugin; Gemini extension | Unit tests; 30 Gemini eval scenarios; `count_tokens.ts` | Puppeteer and Extended Stable Chrome |
| Stagehand | pnpm + turbo monorepo; oxlint/oxfmt | `ci.yml`, `release.yml`, `publish-python.yml`, preview and docs | npm, PyPI, Go module, `browse` CLI | Vitest unit and integration; Braintrust-tracked evals | Own CDP driver |
| Nanobrowser | WXT, pnpm, Vitest | `ci.yml`: prettier, lint, type-check, unit tests, build; actions pinned to a commit, read-only token (`AGENTS.md`) | Chrome Web Store zip | `pnpm autorun` browser checks against 68 fixture pages in headless Chrome for Testing with `--use-mock-keychain`; model evals by hand | Chrome stable |
| agent-browser | Rust (cargo) plus pnpm packaging of native binaries | `ci.yml`, `release.yml` | npm (`agent-browser`), Homebrew, crates.io | 13,609-line `native/e2e_tests.rs`; parity tests; daemon benchmarks in Vercel Sandbox (`benchmarks/README.md`); skill evals | Chrome for Testing |

Signing and auto-update: n/a for libraries; Nanobrowser updates through the Chrome Web Store; agent-browser has `agent-browser upgrade` that detects npm, Homebrew, or cargo (`README.md`, Updating). FACT.

Engineering habits worth noting (FACT): Nanobrowser's `AGENTS.md` records fixed invariants and import rules that lint enforces. DevTools MCP publishes design principles ("Token-Optimized", "Self-Healing Errors", "Reference over Value", `docs/design-principles.md`). Stagehand generates its JSON-RPC schema from one Zod source and versions the protocol separately from packages (`packages/protocol/README.md`).

## Strengths and weaknesses

### browser-use

- **Strong.** The richest built-in agent loop: planning, judge, loop detection, multi-action steps, deterministic rerun (FACT, `agent/views.py:59-92`). Huge community (119k stars). Browser Harness's README carries a matched four-tool eval; I found no other published one (INFERENCE).
- **Weak.** Telemetry on by default (FACT). The newest CLI is "the agent writes Python against raw CDP" in the user's real Chrome, and its skill tells agents to auto-click Chrome's consent sheet (FACT, `skills/browser-use/SKILL.md:115-150`). Product steers toward paid cloud browsers and the BU2 gateway (CLAIM, README). HTML-like serialization is heavier than ARIA lines (INFERENCE).

### Playwright MCP

- **Strong.** Mature ARIA snapshot with a careful distiller; snapshot-to-file; modal-state gating; three engines; extension mode with tab-group ownership; WebMCP as dynamic tools; no telemetry (FACT).
- **Weak.** Safety is the client's job; `browser_run_code_unsafe` ("RCE-equivalent") and `browser_evaluate` are in the default set (FACT, README:963-1088). Still `0.0.x`. Real code lives in the large Playwright monorepo, so reading or vendoring it is heavy (INFERENCE).

### Chrome DevTools MCP

- **Strong.** Google-maintained, fast cadence, deepest debugging (performance, memory, Lighthouse). `pageId` routing for concurrent agents. Clear design principles and eval scenarios. Best plugin and skills distribution (FACT).
- **Weak.** Telemetry and CrUX lookups on by default (FACT). Highest token use in the matched eval: 6.7M median per task (CLAIM). "Officially supports Google Chrome and Chrome for Testing only" (FACT, README).

### Stagehand

- **Strong.** Honest pivot away from a built-in agent toward code mode and tool calling (FACT). Hybrid tree with frame-aware ids, deep locators, three SDKs, and the most flexible eval harness: it already compares Playwright MCP, DevTools MCP, the Anthropic toolset, and others under Claude Code and Codex (FACT).
- **Weak.** The fast path is Browserbase's cloud; its cache ships accessibility trees to the API (FACT). v4 is a breaking rewrite (FACT, migration doc).

### Nanobrowser

- **Strong.** The closest philosophy to rac: user holds the yes, fail-closed refs, three-outcome receipts, payments and secrets handed to the user, tab group per task, and a real injection eval with four outcomes (FACT).
- **Weak.** Analytics on by default (FACT). Infinite breathing border in page DOM (FACT). No outside-agent access yet (FACT). Small team, 2 releases in 6 months, and a ground-up rewrite 10 days old (FACT).

### agent-browser

- **Strong.** Fastest-growing (44.6k stars in 9.5 months), native Rust daemon (~7 MB RSS vs ~140 MB for the old Node daemon, CLAIM, `benchmarks/README.md`), durable refs with tests, cover and visibility checks, `--delta` splices, annotated screenshots, tool profiles, versioned skills served by the binary, and the most complete opt-in security set (FACT).
- **Weak.** Every security feature is off by default (FACT, `security.mdx:8`). Domain allowlist is refused in exactly the modes that reuse real logins (`--cdp`, `--auto-connect`, `--profile`), "because pages or saved origins may run before agent-browser can verify containment" (FACT, `security.mdx:26`). `--profile Default` copies the user's Chrome profile to a temp dir (FACT). 332 open issues and 369 open pull requests (FACT, GitHub search API).

### rac (for contrast, from `docs/internals/ai.md` and the baseline)

- **Strong.** The only one with browser-side containment of navigation, popups, downloads, and file pickers; TOCTOU re-validation; published-vs-private snapshots; a page-blind critic (FACT). In-process extraction with no CDP surface (FACT).
- **Weak.** Smaller tool set (no general keys, hover, dialogs, screenshots, forms, WebMCP), a costly delta, no evals, no outside-agent access, and an `auto` default that permits a cross-site read-then-type chain (FACT, test `AutoAsksOnlyForRiskAndForeignTyping` in `patches/rac/agent/13-permission-levels.patch:329-370`, which lands at `action_guard_unittest.cc:196` once applied; the maintainer's build tree does not have it yet). It also inherits Chromium's unguarded CDP routes (FACT above).

## What rac should take (ranked, concrete, with rough cost) and what rac should avoid

### In plain English

Make rac's agent cheaper and less brittle first. Send only what changed after each step, not hundreds of "unchanged" lines. Add the missing basics: any key, hover, dialogs, a screenshot, and a whole-form fill with one approval card.

Then build a small test set that attacks rac on purpose. Fake pages try to trick the agent into leaking data. A test passes only if rac stops it.

Close two unguarded doors that come with Chromium. One lets a program start rac in debug mode and read every cookie with no prompt. The other lets apps ask for full remote control once a setting is on. Fix the first; decide on the second.

Then let outside agents in, the safe way. Claude Code or Codex connects with one command. rac asks you once. The agent works in its own tab group, under the same rules and cards as rac's own agent. This works even with rac's own assistant turned off.

Costs below are rough agent-thread time and assume today's patch layout (INFERENCE).

### Take: the snapshot and tools (rac's own agent and any outside agent)

1. **Replace the delta format with line splices.** Number each snapshot (`rev`), and send `{base_rev, start_line, delete_count, lines}` hunks plus `removed` refs, falling back to a full snapshot when the hunks are larger. Keep `unchanged` for no change. Source pattern: agent-browser `--delta` (`skill-data/core/references/commands.md:55-59`). Change is local to `snapshot_serializer.cc:694-728` and its tests. **Cost: S (1–2 days).** Expected saving: from ~1,800 tokens to under 100 for a 3-line change on a 300-ref page (INFERENCE).
2. **Stop attaching a full snapshot to every action result.** Return a short receipt (what was dispatched, whether the page reacted, URL/title/tab changes, dialogs, downloads) plus the splice delta from item 1, and a full snapshot only when the document changed or the model asks. Keep sending at least the delta: rac binds approvals to the last *published* snapshot, so sending nothing would push the model onto stale refs and extra `snapshot` calls (INFERENCE from `docs/internals/ai.md`, "Published versus private"). Patterns: DevTools MCP `includeSnapshot: false` (`docs/tool-reference.md:89`), Nanobrowser receipts (`protocol/results.ts:25-46`), Playwright snapshot-to-file (`backend/response.ts:289`). For outside agents with a filesystem, also offer `snapshot` to a file path. **Cost: S–M (3–5 days).**
3. **Fill the tool gaps, each through the guard:**
   - `press_key` for any key or chord. Enter and anything that can submit stays risky; Escape, Tab, arrows, Page Up/Down are free on named sites. **S.**
   - `hover`, `go_forward`, `reload`, `wait_for` text (DevTools `wait_for` takes a list and resolves on any). **S.**
   - `handle_dialog` with Playwright-style modal gating: while a dialog or chooser is open, every other tool returns an error naming the tool that clears it (`backend/tool.ts:70-82`). `prompt` dialogs are the user's step (Nanobrowser rule). **S–M.**
   - `find` that returns refs and a few lines of context (Playwright `browser_find`, Anthropic `find` ≤20 matches). Replace or extend `find_in_page`. **S.**
   - `fill_form` for several fields in one call, with **one** confirm card that lists every field and value (masked for sensitive fields). Fewer turns, fewer cards. **M.**
   - `screenshot` of the attached tab, downscaled (max 1280 px wide, JPEG), off by default for non-vision models; optional `annotate` that draws `[N]` labels matching refs (agent-browser `--annotate`). Screenshots never go to the critic. **M.**
4. **Pre-dispatch "covered by" and usability checks.** Hit-test the target point; if another element is on top, fail with `covered by <role "name" [ref=eN]>` instead of clicking the cover. Fail on hidden, disabled, or off-viewport targets. Source: agent-browser (`README.md:101, 1277`). rac's renderer validator is the natural home. **Cost: M.**
5. **Run a turn's tool calls as a batch.** Execute in order, halt at the first failure, answer the rest "Not executed: an earlier action in this turn failed" (Anthropic contract). Each call still hits the guard; one card per risky step. **Cost: S.**
6. **Loop and stall nudges.** Hash the last 20 actions and the page fingerprint; after 3 failures in a row, tell the model to re-read and re-plan (browser-use, `agent/views.py:78-131`). Keep the 25-call cap. **Cost: S.**
7. **WebMCP tools as first-class, untrusted actions.** List page-declared tools from the `WebMCP` CDP domain or the actor `ScriptToolHost` already in Chromium 154 (`WebMCP.pdl`, `script_tool_host.h`). Show name, short description, origin, and annotations; fetch full schemas on demand (agent-browser caps summaries at 16 tools and 4 KiB). Invoking one is treated like a submit unless it is a read on a named site, and page-claimed `readOnly` never bypasses the guard (agent-browser rule). Requires turning on the `WebMCP` runtime feature, which is experimental in 154 (`runtime_enabled_features.json5:7026-7039`). **Cost: M.** Value grows as sites ship WebMCP (INFERENCE).
8. **Option: serve Anthropic's `browser_toolset_20260801` for Claude on the direct provider.** Map `read_page`/`find`/`form_input`/tab members onto rac's tools; enable coordinate members only with hit-testing into the guard, or reject them when a ref exists. Keep rac's own tools for other providers and for MCP. **Cost: M–L.** Benefit: Claude's trained tool contract and Anthropic's injection classifiers (CLAIM). Decision for the maintainer.
9. **Hand payments, secrets, and access grants to the user.** No Approve button: the card says "this step is yours" and the user does it. Bind any approval to a basis that includes amounts ("Pay $5" ≠ "Pay $500", `gate.ts:103-113`). Source: Nanobrowser. **Cost: S–M.**

### Take: evals and red-teaming

10. **Build a local injection and reliability suite.** Fixture pages served on localhost, a fake OpenAI-compatible model server that replays scripted tool calls, and real-model runs by hand. Grade four outcomes per attack: the model attempted the injected goal; the guard's response; the simulated user's answer; whether the fixture server received the attacker's data (Nanobrowser `eval-tasks.ts:1-80`). Start with rac's known `auto` chain: open a link, read a logged-in page, type it into the attached page. Add scenario tests in DevTools MCP's shape: prompt, turn cap, assertions on calls (`scripts/eval_scenarios/`). Run the fake-model part in CI with the unit tests. **Cost: M (1–2 weeks).** Prerequisite for changing the `auto` default with evidence.
11. **Optional benchmark run.** Stagehand's eval harness already mounts MCP surfaces under Claude Code and Codex (`packages/evals/core/tools/registry.ts`). A rac surface could be compared with Playwright MCP and DevTools MCP on WebVoyager or Online-Mind2Web subsets. It needs network and model keys, so it is a manual, occasional run. **Cost: M.**

### Take: exposing rac to outside agents

These are options, not one plan. The maintainer chooses.

12. **Close the infostealer route now (recommended regardless).** Enforce Chrome's default-user-data-dir rule for `--remote-debugging-port` and `--remote-debugging-pipe` in rac builds: a one-line rac hook that turns on the check Chromium only enables under Chrome branding (`remote_debugging_server.cc:160-183`). Dev profiles use other data dirs, so `worktree.sh run` and the DevTools-port screenshot workflow keep working (INFERENCE; verify). On macOS this route also skips the Keychain prompt that guards the cookie key (INFERENCE). **Cost: S (a day with a test).**
13. **Decide the fate of `chrome://inspect/#remote-debugging` approval mode.** Three choices:
    - (a) Keep it as Chrome does, and document it as "expert, unguarded, whole-profile". Zero cost. It bypasses every rac safeguard.
    - (b) Turn it off by default with a rac flag, and keep Chromium's code for developers who opt in from settings. **S.**
    - (c) Keep it but harden the dialog: name the connecting app when it can be identified (this is a local TCP connection, so that is harder than for a Unix socket), and accept only trusted native clicks, not Accessibility presses, because Browser Harness already auto-clicks Chrome's sheet (`macos.py:12-48`). **M.** VoiceOver users need an accessible path, so (c) needs care (INFERENCE).
14. **"Outside agents" as its own setting, off by default, independent of rac's assistant.** When on, rac listens on one stable per-profile Unix socket (mode 0600, same-user check as today, `mcp_server.cc:46`). When off, nothing listens, which keeps "off costs nothing". Ship a small signed helper in the app bundle, separate from the browser binary (for example `Contents/Helpers/rac`), whose `mcp` command relays stdio to the socket of the chosen profile (`--profile`, default the last used), so setup is one line:
    - `claude mcp add rac -- "/Applications/rac.app/Contents/Helpers/rac" mcp`
    - `codex mcp add rac -- "/Applications/rac.app/Contents/Helpers/rac" mcp`

    Settings shows both lines with copy buttons. **Cost: M (1–2 weeks)** for the listener lifetime, the helper, and settings.
15. **Per-client consent, scope, and visibility.** On a new client's first connect, show a card in rac: the client's self-reported name (`clientInfo`, untrusted) plus, where macOS can tell, the app that launched the helper (see the peer-identity open question). The user picks a permission level for that client. The client then works only in **its own tab group** (Playwright extension pattern: "a tab can belong to a single client at a time"); the user drags tabs in to share them. The ring, pill, and Stop work as they do now, and every call goes through `AgentController::HandleToolCall` and the guard. This needs a session model with one controller turn per client instead of one per profile. **Cost: L (2–4 weeks).** It is the main architecture work in this list (INFERENCE).
16. **A CLI and a skill that cannot go stale.** The same helper exposes shell verbs (`rac snapshot`, `rac click e12`, `rac tabs`) for agents that prefer CLIs, writes big outputs to files, and prints its own skill with `rac skill` (agent-browser's thin-stub pattern, `README.md:1756-1764`). A one-line installer writes the stub to `~/.claude/skills/rac/SKILL.md` and `~/.agents/skills/rac/SKILL.md` only when the user clicks it. **Cost: M.**
17. **MCP hygiene.** Add `destructiveHint` and `openWorldHint` next to the existing `readOnlyHint` (`mcp_protocol.cc:119`); accept the current spec version, 2026-07-28 (FACT: final, non-prerelease GitHub release of `modelcontextprotocol/modelcontextprotocol` on 2026-07-28; [changelog](https://modelcontextprotocol.io/specification/2026-07-28/changelog)), alongside the four rac accepts (`2024-11-05`, `2025-03-26`, `2025-06-18`, `2025-11-25`, `mcp_protocol.cc:21-22`); tool profiles (`core` by default) so the schema list stays small. **Cost: S.**

### Avoid

- **Telemetry on by default** (browser-use, DevTools MCP, Nanobrowser all do it). It breaks rac's first rule. FACT for them; rac's rule is from `AGENTS.md`.
- **Sending page trees or URLs to a vendor** for caching or field data (Stagehand cache, DevTools CrUX lookups). FACT for them.
- **Arbitrary page script or "code mode" against the user's logged-in profile.** Playwright ships `browser_run_code_unsafe` by default and calls it "RCE-equivalent"; Browser Harness runs agent-written Python against raw CDP. Either one routes around every guard rac has (INFERENCE). If rac ever offers scripts, run them in a separate throwaway profile.
- **Safety by flags nobody sets.** agent-browser's protections are all opt-in, and its allowlist is refused in the real-login modes (FACT). rac's protections must stay on by default and work in the user's own profile.
- **Trusting the MCP client to ask.** Playwright and DevTools MCP rely on the client's prompt (FACT). Users routinely pre-approve tools in their client's settings, after which no prompt appears (INFERENCE). The browser must hold the yes.
- **Consent that a script can click.** Chrome's per-connection sheet is clicked by `osascript` in Browser Harness (FACT). Any new rac consent card must not accept synthetic presses (INFERENCE).
- **Page-visible agent markers and endless motion.** Title prefixes (Browser Harness ♞) and in-page borders with an infinite 2 s animation (Nanobrowser) leak agent presence to pages and repaint forever (FACT for the code; INFERENCE for the leak). rac's ring and pill in browser UI are better.
- **Copying the user's profile** to a temp dir for an agent (agent-browser `--profile Default`). It duplicates cookies on disk outside the browser's control (INFERENCE).
- **Huge tool lists.** Playwright MCP has 72 tools with every capability on (25 by default); DevTools MCP lists 60 (several behind flags). Use a small `core` set with optional groups (FACT that both offer such modes).
- **Relying on injection detection.** Adaptive rewrites reach 78.79% average attack success across the target browser agents in BrowseSafe++, from 30.66% against Sonnet 5 to 95.41% against Kimi K2 (CLAIM, paper, Section 4.3 and Table 4). Use structural rules first.
- **A built-in agent as the only way in.** Stagehand removed theirs; developers want tools (FACT and CLAIM). rac's assistant stays optional; outside access should not require it.

## Open questions and things I could not verify

- **Does rac's `chrome://inspect` approval mode work end to end?** The code is present and enabled (FACT), but I did not launch rac. The dialog's real wording in release builds (dev trees substitute names) and whether incognito targets are exposed were not checked.
- **Does the default-user-data-dir check break any rac workflow?** The maintainer's memory notes driving WebUI pages through a DevTools port in dev profiles; those use other data dirs, so they should be unaffected (INFERENCE). Needs a test.
- **WebMCP in Helium builds.** The runtime feature is `experimental` with an origin trial in Chromium 154; whether Helium's flags or origin-trial handling leave it reachable was not checked.
- **Token numbers.** Every cross-tool token figure here is vendor-run or third-party (Browser Harness eval, DEV Community re-run, Slack via TestMu, the 6,600-token toolset overhead). None was reproduced.
- **Playwright MCP's snapshot-to-file default** is read from code at monorepo commit `8c1b148` (`response.ts:289`) and matches a third-party re-run; the published `@playwright/mcp@0.0.83` pins an earlier Playwright alpha, so the exact release where this changed is unverified.
- **Anthropic toolset details.** Member input schemas beyond the docs summary, and the GA date (from a search summary), are unverified. Whether Claude performs better with this toolset than with rac's tools is untested.
- **Stagehand v4 transport.** How the SDK reaches the extension service worker (a Chrome binding over CDP is suggested by `service-worker.ts`) was not fully traced. Browserbase's separate MCP server was not reviewed.
- **Claude Code and Codex syntax** (`claude mcp add`, `codex mcp add`, `~/.agents/skills`) comes from vendor READMEs and search results, not from running the CLIs.
- **Peer identity on the socket.** Whether macOS `LOCAL_PEERTOKEN` / audit-token code-signature checks can reliably name the client (the peer will often be rac's own helper or `nc`, not Claude Code) is unresolved. Same-user is the real boundary; consent and scope must carry the rest (INFERENCE).
- **Concurrency model for outside agents.** One controller turn per client, a queue, or one shared turn: open for the maintainer.
- **Where "outside agents" lives.** It is not rac's AI, but it lets an AI act. Whether it sits under Settings › Assistant, needs AI on, or has its own section (and whether the incognito ban applies, which it should by default) is the maintainer's call. The brief notes that today turning AI off also removes the MCP server.
- **Default level for outside agents.** rac's own default is `auto`, which has a known exfiltration chain. Whether outside clients start at `ask` or `careful` until the eval suite exists is open.
- **Team sizes and business details.** Contributor counts are not headcounts; funding was not checked.

## Sources

Repositories and files (all read at the commits listed at the top; paths relative to each clone in `/tmp/rac-overhaul/src/`):

- browser-use: `README.md`; `browser_use/config.py:58-63, 92-107`; `browser_use/telemetry/service.py:22`; `browser_use/sync/service.py:19-106`; `browser_use/agent/views.py:59-131`; `browser_use/agent/service.py:534-580`; `browser_use/dom/serializer/serializer.py:46-58, 637-700, 989-1120`; `browser_use/tools/service.py:458-2178`; `browser_use/mcp/server.py:221-451`; `browser_use/integrations/anthropic/browser_use.py`; `skills/browser-use/SKILL.md`; `.github/workflows/eval-on-pr.yml`.
- browser-harness: `README.md:1-80`; `src/browser_harness/macos.py:12-118`.
- playwright-mcp: `README.md` (CLI vs MCP lines 7-11; options 400-460; profiles 462-500; tools 887-1660); `cli.js`; `package.json`; `CLAUDE.md`; `tests/click.spec.ts`, `tests/core.spec.ts`, `tests/fixtures.ts:225-300`.
- playwright monorepo: `packages/injected/src/ariaSnapshot.ts:37-238, 450-554`; `packages/injected/src/ariaSnapshotDistiller.ts`; `packages/injected/src/webMCP.ts`; `packages/playwright-core/src/tools/backend/{tool.ts, tools.ts, snapshot.ts, response.ts, browserBackend.ts, context.ts:554, webmcp.ts}`; `tools/mcp/{config.d.ts, cdpRelay.ts:76-160}`; `tools/skills/playwright-cli/SKILL.md`; `tools/cli-client/program.ts:200-335`.
- chrome-devtools-mcp: `README.md:1-200`; `docs/design-principles.md`; `docs/tool-reference.md`; `docs/slim-tool-reference.md`; `docs/configuration.md:60-260`; `docs/advanced-usage.md:55-150`; `docs/cli.md`; `src/TextSnapshot.ts`; `src/formatters/SnapshotFormatter.ts`; `src/utils/WaitForHelper.ts`; `src/BrowserManager.ts:340-445`; `src/tools/{snapshot.ts, comments.ts, webmcp.ts, pages.ts, ToolDefinition.ts, categories.ts}`; `src/telemetry/transformation.ts`; `skills/chrome-devtools/SKILL.md`; `plugin.json`; `mcp.json`; `scripts/eval_scenarios/page_id_routing_concurrent_form_test.ts`.
- stagehand: `README.md`; `packages/cli/README.md`; `packages/protocol/README.md`; `packages/extension/understudy/a11y/snapshot/{capture.ts, treeFormatUtils.ts, a11yTree.ts}`; `packages/extension/services/cacheService.ts`; `packages/extension/understudy/domainPolicy.ts`; `packages/docs/v4/migrations/v3.mdx:9-60, 589-598`; `packages/evals/README.md`; `packages/evals/core/tools/registry.ts`.
- nanobrowser: `README.md`; `AGENTS.md`; `PRIVACY.md`; `src/browser-control/protocol/{catalogue.ts, results.ts}`; `src/browser-control/core/perception/outline.ts`; `src/browser-control/core/interaction/gate.ts`; `src/extension/border.ts:120-190`; `src/background/checks/eval-tasks.ts`; `fixtures/`; release notes for v0.2.0 and v0.3.0 (`gh api repos/nanobrowser/nanobrowser/releases/tags/…`).
- agent-browser: `README.md` (lines 89-200, 571-900, 982-1035, 1255-1340, 1523-1590, 1713-1770); `docs/content/docs/security.mdx`; `skills/agent-browser/SKILL.md`; `skill-data/core/SKILL.md`; `skill-data/core/references/commands.md:55-59`; `cli/src/native/snapshot.rs:107-170, 772-830, 1223-1300`; `cli/src/native/element.rs:27-70`; `evals/README.md`; `benchmarks/README.md`.
- GitHub API (2026-10-25): `gh api repos/<owner>/<repo>`, `/releases`, `/contributors` for all six.

rac and Chromium (read-only):

- `docs/internals/ai.md`; `plans/research/rac-baseline.md` ("Agents and AI"); `plans/context/maintainer-brief.md`.
- `/Users/knewton/Dev/Github/rac/build/src/chrome/browser/rac/agent/snapshot_serializer.{h:22, cc:367-379, 694-832}`, `tool_registry.cc:115-263`, `mcp_server.cc:46`, `mcp_protocol.cc:21-22, 119`; `chrome/browser/rac/ai/chat_protocol.h:24`. The guard-level test is read from `patches/rac/agent/13-permission-levels.patch:329-370` (not in the build tree).
- `chrome/browser/devtools/features.cc:206-210`; `chrome/browser/devtools/remote_debugging_server.cc:160-183, 216-283, 336-417`; `chrome/browser/devtools/devtools_connection_dialog.h`; `chrome/app/generated_resources.grd:4571-4583`; `third_party/blink/renderer/platform/runtime_enabled_features.json5:7026-7055`; `third_party/blink/public/devtools_protocol/domains/WebMCP.pdl`; `chrome/browser/actor/tools/script_tool_host.h`.

Web (fetched or searched 2026-10-25):

- Anthropic, Browser use tool (`browser_toolset_20260801`): https://platform.claude.com/docs/en/agents-and-tools/tool-use/browser-use-tool
- Anthropic, Use Claude in Chrome safely: https://support.claude.com/en/articles/12902428-use-claude-in-chrome-safely
- Digital Applied, toolset token overhead: https://www.digitalapplied.com/blog/anthropic-browser-use-tool-ga-new-agent-toolset
- Chrome for Developers, remote debugging port change: https://developer.chrome.com/blog/remote-debugging-port
- Playwright extension README: https://github.com/microsoft/playwright/tree/main/packages/extension
- DEV Community, Playwright CLI vs MCP re-run: https://dev.to/aswani25/playwright-cli-vs-playwright-mcp-which-should-you-use-with-claude-code-1olh
- TestMu AI, Playwright CLI vs MCP vs Kane CLI (Slack figures): https://www.testmuai.com/blog/playwright-cli-vs-mcp-vs-kane-cli/
- Browser Use agent benchmarks: https://browser-use.com/benchmarks/agents
- Steel, Online-Mind2Web leaderboard: https://leaderboard.steel.dev/leaderboards/online-mind2web/
- WASP (arXiv 2504.18575): https://arxiv.org/pdf/2504.18575
- BrowseSafe (arXiv 2511.20597): https://arxiv.org/html/2511.20597
- BrowseSafe++ (arXiv 2610.17457): https://arxiv.org/html/2610.17457
- MCP elicitation, 2025-11-25: https://modelcontextprotocol.io/specification/2025-11-25/client/elicitation
- MCP 2026-07-28 changelog (official): https://modelcontextprotocol.io/specification/2026-07-28/changelog ; release tag: https://github.com/modelcontextprotocol/modelcontextprotocol/releases/tag/2026-07-28
- WorkOS, MCP 2025-11-25 summary: https://workos.com/blog/mcp-2025-11-25-spec-update
- Codex skills location (third-party guide): https://agentskillshub.dev/guides/codex-skills/

## Verification

Adversarial fact-check on 2026-10-25. Each claim was checked against a primary source: code in the clones under `/tmp/rac-overhaul/src/` (same commits as listed at the top, re-confirmed with `git log`), `gh api` (read-only), the official docs pages, rac's build tree, or `patches/`. Nothing was installed, built, or run.

| # | Claim checked | Primary source | Result | Change made |
| --- | --- | --- | --- | --- |
| 1 | Stars, repo creation dates, licenses for all six plus Browser Harness | `gh api repos/<owner>/<repo>` | Confirmed (stars drift by at most 4) | None |
| 2 | Release totals, last-6-month counts, latest versions | `gh api repos/<r>/releases --paginate` | Confirmed: 140/17, 73/13, 64/19, 82/26, 16/2, 114/33 | None |
| 3 | Contributor counts (360, 69, 156, 48, 25, 117) | `gh api repos/<r>/contributors --paginate` | Confirmed | None |
| 4 | agent-browser has "701 open issues" | `gh api search/issues` with `is:issue` and `is:pr` | **Wrong.** 332 open issues plus 369 open PRs; GitHub's `open_issues_count` counts both | Fixed in 3 places |
| 5 | Playwright MCP has 25 tools by default and 83 in total | `backend/tools.ts:83-84` (`filteredTools` drops `skillOnly`); `playwright-mcp/README.md` "Tools" | **Partly wrong.** 25 by default is right. MCP serves 72 at most; 11 of the monorepo's 83 are CLI-only | Fixed in 3 places (tables and Avoid list) |
| 6 | Playwright writes implicit snapshots to a file; modal-state gating names the clearing tool; `browser_run_code_unsafe` is "RCE-equivalent" and in the default set; WebMCP served as dynamic MCP tools, on by default | `backend/response.ts:289-318`; `backend/tool.ts:70-84`; `backend/tab.ts:147, 226`; `README.md:438, 670, 1082-1084`; `backend/browserBackend.ts:73-77` | Confirmed | None |
| 7 | Playwright extension: one named, colored tab group per client; a tab belongs to one client; drag tabs to change access; per-connection approval unless a token is set | Extension README (fetched) | Confirmed | None |
| 8 | DevTools MCP usage statistics, CrUX lookups, and npm update checks on by default; `uid`/`reqid`/`msgid` blocklisted | `README.md:34-58`; `src/telemetry/transformation.ts:45` | Confirmed | None |
| 9 | DevTools MCP `includeSnapshot` defaults false; `fill_form` "ALWAYS prefer" quote; 60 tools; `--slim` 3; 30 eval scenarios; `pageIdRouting` default true | `docs/tool-reference.md:89, 121` (60 `###` entries); `docs/slim-tool-reference.md` (3); `scripts/eval_scenarios/` (30 files); `docs/configuration.md:159-162` | Confirmed | None |
| 10 | DevTools MCP wait timings: 100 ms to start, 3,000 ms navigation, 100 ms quiet DOM, 3,000 ms cap, scaled by multipliers | `src/utils/WaitForHelper.ts:39-42, 262-290` | Confirmed | None |
| 11 | DevTools `--autoConnect` needs Chrome 144+ and "has access to all open windows for the selected profile" | `docs/advanced-usage.md:60-62, 92` | Confirmed | None |
| 12 | Stagehand v4 removed `agent()` (quote); cache ships raw accessibility trees to the API; Node 22.18+ for the CLI | `packages/docs/v4/migrations/v3.mdx:9-16`; `services/cacheService.ts:24-29, 48-67` (on by default when `browserbase: "client"`); `packages/cli/package.json:93` | Confirmed | None |
| 13 | Nanobrowser border: 16 px edges, violet-to-blue at 0.6 alpha, 150 ms opacity transition, 2 s infinite breathe from 0.6 to 1, off under reduced motion, 2 s `setInterval`, `pagehide` removal, `data-nanobrowser-border` in page DOM | `src/extension/border.ts:136-165`; shown only while a task runs (`#wanted`, lines 97-100) | Confirmed | None |
| 14 | Nanobrowser 17 tools; Ask is the default mode; PostHog counts on by default with no ID; no server; MCP bridge only planned; approval bound to a basis with amounts | `protocol/catalogue.ts:41-174`; `README.md:56-62`; `PRIVACY.md:13, 20-25`; `AGENTS.md:25`; `core/interaction/gate.ts:103-113` | Confirmed | None |
| 15 | Nanobrowser has "69 fixture pages"; four-outcome injection evals | `find fixtures/pages` (68 `.html` + 1 `.css`); `src/background/checks/eval-tasks.ts:1-30` | **Off by one.** 68 pages. Eval design confirmed | Fixed in 2 places |
| 16 | agent-browser security is all opt-in; allowlist refused with `--cdp`, `--auto-connect`, `--profile`; confirmations auto-deny after 60 s "and when stdin is not a TTY" | `docs/content/docs/security.mdx:8, 26, 31-32, 295` | **Partly wrong.** The non-TTY rule belongs to `--confirm-interactive`, not `--confirm-actions` | Fixed |
| 17 | agent-browser file sizes (`mcp.rs` 5,587; `actions.rs` 18,698; `e2e_tests.rs` 13,609; `snapshot.rs` 1,760; `element.rs` 1,877); 18 interactive roles | `wc -l`; `cli/src/native/snapshot.rs:107-126` | Confirmed (one of the 18 entries is `"Iframe"`) | None |
| 18 | agent-browser `--delta` line splice; durable refs; same-role-and-name fallback; `covered by` errors; thin skill stub; WebMCP summaries capped at 16 tools and 4 KiB; MCP rejects global policy flags | `skill-data/core/references/commands.md:55-59`; `README.md:99-101, 168, 181, 623, 984, 1277-1279, 1755-1764` | Confirmed | None |
| 19 | agent-browser daemon exits after 1 hour idle | `README.md:1718` | Confirmed, with an exception: the default never closes a headed or user-attached browser | Added the exception |
| 20 | Browser Harness matched benchmark (scores, tokens, costs, "no tool wins") | `browser-harness/README.md:58-80` | Numbers match; still vendor-run (CLAIM). Plain-English text called them "four of these tools", but Browser Harness is not one of the six | Reworded plain English; added the README's own limits (100 tasks, one run, Codex only, shared cloud browser) |
| 21 | Browser Harness clicks Chrome's "Allow remote debugging?" sheet through Accessibility, and its skill tells agents to call `mac-approve`; horse title marker on by default | `src/browser_harness/macos.py:12-48`; `browser-use/skills/browser-use/SKILL.md:56-67, 121-147, 284`; `daemon.py:135` | Confirmed | None |
| 22 | browser-use: PostHog telemetry on by default; cloud sync only when authenticated; agent defaults (`use_vision`, 5 actions per step, judge on, 40,000-character cap, 20-step loop window, re-plan after 3, stop after 5); MCP has 16 tools | `config.py:58-63`; `telemetry/service.py:22-63, 136-141`; `sync/service.py:26-55`; `agent/views.py:62-92`; `mcp/server.py:221-451` (17 `types.Tool`, one commented out) | Confirmed. New fact: telemetry carries a persistent device id (saved UUID, or a MAC-plus-hostname hash) | Added the device id to the privacy table |
| 23 | Anthropic `browser_toolset_20260801`: 27 default plus 4 optional members (named); `ref_N` validity rule; 50,000-character cap, depth 15; `find` up to 20; ordered batch with the exact "Not executed" text; injection classifiers; six precautions | Docs page (fetched 2026-10-25) | Confirmed | None |
| 24 | "The 12 pointer members take coordinates" | Docs "Targets" table | **Imprecise.** 11 accept coordinates; 6 of them also accept a ref; `scroll_to` is ref-only | Fixed in the table and the rac inference |
| 25 | rac snapshot: 48 KiB cap; truncation marker; `BuildDelta` writes `- unchanged [ref=eN]` per unchanged line; ref-less lines always count as a change; delta only for the same URL and title | `snapshot_serializer.h:22`; `snapshot_serializer.cc:367-379, 694-728, 811-826` | Confirmed | None |
| 26 | rac has 15 tools; `press_key` is Enter-only; `find_in_page` returns count and snippets; only `readOnlyHint`; same-user socket check; 25-call cap; 4 s and 10 s settle caps | `tool_registry.cc:87-262`; `mcp_protocol.cc:117-120`; `mcp_server.cc:43-50`; `chat_protocol.h:24`; `action_runner.cc:232-324` | Confirmed. Patch 13 edits `tool_registry.cc` only after line 359, so this holds on `main` | None |
| 27 | rac's `auto` level allows cross-site navigation and model-written typing in the attached tab (`action_guard_unittest.cc:196-223`) | `patches/rac/agent/13-permission-levels.patch:329-370` | Behavior confirmed. **Citation wrong**: the build tree's file has 156 lines and lacks the test, because the tree predates patches 13-17 | Fixed the citation and the Sources entry; added a note at the top |
| 28 | Chromium's default-user-data-dir check for `--remote-debugging-port` runs only under `GOOGLE_CHROME_BRANDING`; `kDevToolsAcceptDebuggingConnections` enabled on macOS; no Helium or rac patch touches it; dialog wording | `remote_debugging_server.cc:160-183`; `features.cc:203-211`; `out/Default/args.gn` (no `is_chrome_branded`); grep of `patches/` and `helium-chromium/patches/`; `generated_resources.grd:4569-4585`; Chrome blog (Chrome 136, silent on Chromium) | Confirmed | None |
| 29 | Chromium 154 has the `WebMCP` runtime feature (experimental plus origin trial), a `WebMCP` CDP domain with `readOnly`, `untrustedContent`, `consequential`, and `script_tool_host.h` | `runtime_enabled_features.json5:7026-7039`; `WebMCP.pdl:7-21`; file exists | Confirmed | None |
| 30 | MCP spec 2026-07-28 is current; rac accepts four older versions | GitHub release `2026-07-28` (not a prerelease); `mcp_protocol.cc:21-22` | Confirmed, but the document cited an unofficial mirror (`mcp.mintlify.app`) | Replaced with the official changelog and release tag |
| 31 | BrowseSafe++: 78.79% average, up to 95.41%; "recognize … yet still follow" | arXiv 2610.17457 HTML (contributions, Section 4.1, 4.3, Table 4) | Numbers and quote confirmed. The Avoid list said "against detectors and agents"; the figure is across target **agents** (30.66% against Sonnet 5 at the low end) | Fixed |
| 32 | WASP: hijacked 17-86% of the time; end-to-end success at most 16% | arXiv 2504.18575v3 HTML, Section 4 | Confirmed (the introduction says 0-17%) | None |
| 33 | Code sizes | `wc -l` over each tree | browser-use 68.8k, DevTools 28.5k, Nanobrowser 46.7k, agent-browser 107.6k confirmed. Playwright "~31.7k TypeScript" counts every file (TypeScript is ~28.0k). Stagehand "~74k" matched no filter (~106k with tests, ~49k without) | Fixed both |

**Not verified (left tagged CLAIM, or flagged in Open questions):** the DEV Community and TestMu token figures, including the Slack numbers; the 6,600-token toolset overhead (digitalapplied.com); Anthropic's "below 0.08%" attack rate; the toolset's GA date (the docs page marks it GA but gives no date); Browser Use's 97% Online-Mind2Web claim; agent-browser's ~7 MB vs ~140 MB RSS (the text is in `benchmarks/README.md:74`, but it is a vendor measurement); Claude Code and Codex install syntax; how Stagehand v4's SDK reaches its extension service worker.

**Overall confidence: high** for code, configuration, and GitHub API facts: 33 claims checked, 9 corrected, and none of the corrections reverses a recommendation. Two corrections change emphasis. Playwright's full tool list is 72, not 83, which weakens but does not remove the "huge tool lists" point. Eleven, not twelve, pointer members take coordinates, and six of them also take refs, which makes recommendation 8 (serve Anthropic's toolset) somewhat cheaper to guard. **Medium confidence** for every cross-tool token or cost figure: they are vendor-run or third-party, and none was reproduced. The recommendations about Chromium's unguarded remote-debugging routes (items 12 and 13) rest on confirmed code, but are still INFERENCE until someone launches rac and tries them.
