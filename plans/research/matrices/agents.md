## In plain English

Every browser agent does three things: it reads the page as a short outline, it clicks and types by tags like `e12`, and it asks a human before risky steps. They differ in who runs the loop and who holds the "yes". ego(lite) and Aside let your own coding agent drive the browser. ego asks nobody; Aside asks very little by default. rac asks the most, but only its own agent can use that guard, and its default level has a hole: a hostile page can make the agent read a logged-in site, then type what it read back into the hostile page. My advice: close that hole and write injection evals first, then open one guarded door for outside agents behind its own switch, then add agent-owned tabs.

# How agents work: comparison matrices (2026-10-27)

Topic: how browser agents work, for rac's agent overhaul. Built only from the 18 digests, the dossiers they point to, rac's agent patches, and `docs/internals/ai.md`. Nothing was run. "?" means the sources do not say. Tags: (claim) = vendor or third-party self-report; (inf.) = my reasoning from the sources, not stated by them. Untagged cells are facts from code, docs, or primary pages as reported in the digests. Counts of tools are as reported; where I counted from a list I say so.

Each matrix is split into three tables with the same rows, so the columns stay readable:

- Part 1: rac today, ego(lite), Aside, BrowserOS (the AI browser plus its agent-only sibling neo).
- Part 2: Dia, Comet, Atlas, Yab (closed AI browsers).
- Part 3: open agent stacks (browser-use, Playwright MCP, DevTools MCP, agent-browser, Stagehand, Nanobrowser), other browsers' outside-agent doors (Crest, Nook, Ardia, Opera Neon, T3 Code), Chrome's own agent, and Pomerado.

Coverage is uneven. Dia has no general clicking agent, Atlas was shut down on 2026-08-09, and the closed products were not adversarially verified, so their cells are thinner.

---

## Matrix A: mechanics

### A, part 1: rac, ego(lite), Aside, BrowserOS

| | rac today | ego(lite) | Aside | BrowserOS (and neo) |
| --- | --- | --- | --- | --- |
| How it sees the page | Chromium's AnnotatedPageContent (layout-tree based), in-process, as text lines. Separate `get_page_text`. No screenshot tool | Native accessibility-style snapshot from a closed binding (viewport by default in v2). Screenshot available. Everything is a script, so the agent chooses | Accessibility snapshot `{tree, diff}`; also `annotatedScreenshot` (boxes labelled with refs) and raw screenshots; coordinate-click fallback | Accessibility tree as indented text, iframes stitched, cursor-pointer nodes added. `act` returns a diff. Screenshot per step in neo audit |
| Snapshot format, example line | `- button "Sign in" [ref=e6] [submit]`; links add `-> host/path`; forms add submission info; passwords and payment values `[redacted]`; 48 KiB cap | `button "Save" [ref=11, loc=role:button[name="Save"]]`; 2-space indent; older docs show `@3 [input type="email"]` | Not given in the digest; refs look like `e12`, iframes `f1e1` | `[ref=eN]` on indented lines; Full or Interactive mode plus depth. Exact line ? |
| Ref stability | `eN` never reused; keyed on tab + document + DOM node; `stale_ref` after a replaced document; re-checked at mouse down, mouse up, between keys | `(frameId, backendNodeId, documentId)`; partial snapshots merge and keep refs; document change invalidates; fails with "take a new snapshot"; refs persist across processes on disk | Each snapshot invalidates earlier refs | "Stable" `eN` per the digest; invalidation rules ? |
| Tool count and groups | 15: read 4 (`snapshot`, `get_page_text`, `list_tabs`, `find_in_page`), act 11 (`click`, `type`, `select_option`, `press_key` Enter-only, `scroll`, `navigate`, `go_back`, `open_tab`, `switch_tab`, `close_tab`, `wait_for_settle`) | Not tools: a Node SDK of methods in 6 groups (Spaces, TaskSpace, Observe, Navigate and wait, Act, escape hatches). Count not stated | 2 core (`repl`, `bash`). About 38 registered by my count: bash and background (8), files (3), web (2), delegation (5), context and memory (8), control and automations (12) | BrowserOS 17 browser + 7 file + Klavis + 2 nudge. neo 25 default, up to 27 (catalog of 20 incl. `credentials`, `browser_target`; `save_skill`; human-help pair; `run`) |
| In-page JS, CDP, or native | In-page: none. Native: Chromium actor renderer tools through Mojo, trusted input. No CDP | All three: `page.evaluate` and `page.fetch` in page, CDP through an in-process binding scoped to the agent Space (no open port by default), native trusted `Input.dispatchMouseEvent`. Plus plain Node `fetch` and `fs` | Authenticated CDP (patched DevTools HTTP on localhost:45103), private extension APIs, QuickJS-wasm REPL with a Playwright-style `page` | Loopback CDP on `127.0.0.1:9100` (neo 9110) with custom domains (`Browser.*`, `History.*`, `Autofill`). `run` JS: neo in QuickJS (64 MB, 30 s, no fetch); BrowserOS `run` is an unsandboxed `new AsyncFunction` |
| Batching or scripted steps | None found. One call at a time, 25-call cap per turn. Batching is a proposal only | The core idea: one JS program per call (open, fill, click, wait, print snapshot). 44% fewer rounds (claim) | REPL scripts; `workflow` and `subagent` tools | `run` scripts; ? beyond that |
| Tab and focus behavior | Acts in the attached tab and tabs the agent opened. One active turn per profile. Ring + pill on the tab. Pauses on real user input. No isolated space or window. Focus behavior of `open_tab` ? | Agent Spaces; background tab changes stop taking focus (0.6.1.9); muted; user tabs protected; page budget 8; closes after 30 idle minutes. Cookie jar is shared with your tabs. Overlay costs ~40% GPU for one idle Space (users) | Agent tabs: muted, backgrounded, return on leave, close after 15 idle minutes, close on quit; separate "Agent tabs" sidebar section | Agent-owned tab groups with ownership labels (labels, not barriers); human hand-off; session end closes the group |
| How the agent runs | Both: (1) rac's own tool loop on a direct provider; (2) an ACP agent rac launches (Claude Code, Codex, Cursor, others) calling rac's per-run MCP. Cold start 15-25 s per message (claim) | No built-in agent. Your coding agent writes the scripts | In a separate Node daemon (Pi-fork harness), local, remote, or cloud; or your outside agent via CLI and MCP | BrowserOS: Bun sidecar `ToolLoopAgent`, 100 steps, or ACP coding agents. neo: no agent, the outside agent calls it |
| Model providers | BYO key (OpenAI-style, Anthropic-style, Gemini, OpenRouter), local (Ollama, LM Studio), installed ACP agents (subscription via the vendor CLI) | Whatever your agent uses. ego has no AI | Aside credits (hosted), OAuth subscriptions (ChatGPT, Claude Pro and Max, Copilot), API keys, Ollama and LM Studio. The Claude login works by impersonating Claude Code | 13 types: Anthropic, OpenAI, Google, OpenRouter, Azure, Bedrock, Moonshot, Ollama, LM Studio, plus ChatGPT, Copilot, Qwen subscriptions. Free, bring your key |

### A, part 2: Dia, Comet, Atlas, Yab

| | Dia | Comet | Atlas (retired 2026-08-09) | Yab |
| --- | --- | --- | --- | --- |
| How it sees the page | Page text read out of process; "only sees what you saw and approved". No general clicking agent | Accessibility tree as YAML; HTML to markdown; screenshots with pixel actions | One screenshot per step for a computer-use model; `<select>` popups composited in | `snapshot` (accessibility tree with refs), `text`, `screenshot` |
| Snapshot format, example line | ? | YAML with `ref_N` ids on interactable elements; exact line ? | None (pixels) | ?; refs are "ref ids" |
| Ref stability | ? | ? | n/a | ? |
| Tool count and groups | Tools act through APIs and drafts: @Tabs open and close tabs, Gmail and Calendar drafts, Autofill. Count ? | ?; includes `ComputerBatch` for pixel actions | ? (screen actions) | 69 tools at the 0.0.18 snapshot (newer may have more); groups ? |
| In-page JS, CDP, or native | ? (own SDK "ArcCore" on Chromium) | Execution in three hidden built-in extensions; mechanism ? | Input routed straight to the renderer, never through the privileged browser layer (OWL) | `run` and `eval` run JS in an isolated world; WebKit engine, so not CDP; rest ? |
| Batching or scripted steps | No | `ComputerBatch` (pixel actions) | ? | `run` JS; routines |
| Tab and focus behavior | Chat starts with no other-tab access | Agent in your signed-in tabs; Background Assistants run in parallel (Max) | Your session, or "logged-out" mode with fresh in-memory storage thrown away after | Agent tabs live in an off-screen window beside yours, signed in as you |
| How the agent runs | Cloud (TBC servers to model vendors); small on-device models route the command bar | Planner on Perplexity servers; execution in the browser | OpenAI cloud | Local: Claude Code, Codex, Gemini, or Cursor run as child processes on the user's plan |
| Model providers | OpenAI, Anthropic, Google via Dia's servers (GPT-5 for all queries as of 2025-09); no local chat model | Perplexity's choice; none local | OpenAI; none local | The user's own CLI plan; no local LLM beyond Apple's |

### A, part 3: open stacks, other doors, Chrome, Pomerado

| | Open agent stacks | Other browsers' outside-agent doors | Chrome (Gemini auto browse) | Pomerado |
| --- | --- | --- | --- | --- |
| How it sees the page | Mostly accessibility or ARIA text. browser-use mixes DOM + accessibility + layout snapshot and sends a screenshot each step. Stagehand hybrid AX + DOM | Crest: DevTools-MCP-style snapshots with uids. Nook: AX outline. T3 Code: Playwright ARIA "ai" snapshot. Ardia: DOM, accessibility, screenshots over CDP | Layout-tree page content (rendered content only) plus screenshot, each voted per action | The minter model explores with page observations; after minting no model reads the page |
| Snapshot format, example line | Playwright MCP / agent-browser: `- button "Submit" [ref=e2]`. DevTools MCP: `uid=1_5 button "Submit" focusable`. browser-use: `*[4211]<button aria-label=Search />`. Stagehand: `[0-12] button: Submit [checked]`. Nanobrowser: `[e12]` outline | Nook: role, name, state; default 300 nodes, cap 2,000; changed lines only on repeat. Others ? | Protobuf page content, not text lines; targets are node ids or screen coordinates | n/a (operation modules call the site) |
| Ref stability | Playwright: kept while role and name stay. DevTools: reused if loader id + backend id match. agent-browser: kept across snapshots, same-role-and-name fallback, fails if ambiguous. Nanobrowser: fails closed. Stagehand: per snapshot, XPath | Nook: no ref ids in chat, selectors or text. T3: refs die on navigation, new snapshot, or control handoff | Node ids; rac's never-reused refs judged more robust (inf.) | n/a |
| Tool count and groups | Playwright MCP 25 default, 72 in all. DevTools MCP about 60 (`--slim` 3). browser-use about 24 (MCP: 16). Nanobrowser 17. Stagehand 3 primitives (`act`, `observe`, `extract`). agent-browser MCP: `core` profile | Crest 29. Nook 31. Ardia: 70 allowed CDP methods. T3 Code 84 tools in 11 toolkits (preview 19). Neon: read tools plus write tools off by default | Server proto has 25 action kinds (8 run in the renderer); client registry 40 tool ids on main | `pomerado-mcp mint` has 4 tools (`mint`, `get_job`, `provide_input`, `cancel_job`); each saved integration is its own MCP server |
| In-page JS, CDP, or native | Playwright, DevTools, browser-use, agent-browser, Stagehand: CDP. Nanobrowser: `chrome.debugger` only. Playwright MCP also has `browser_run_code_unsafe` (called RCE-equivalent) | Crest: native helper; page-world scripts behind a toggle. Nook: WebKit APIs; `evaluate` runs any JS. Ardia: CDP, 70 methods. T3: Electron webview + Playwright | Native renderer tools plus Google-hosted planner. Not CDP | Playwright-launched Chromium; generated JS "operation modules" run with the user's file and network access |
| Batching or scripted steps | browser-use up to 5 actions per step. agent-browser `batch --bail`. DevTools `fill_form`. Playwright: responses show the code run | Nook/Crest: ? | One action at a time (inf.) | Whole task becomes a deterministic script |
| Tab and focus behavior | Playwright extension: own tab group per client. Nanobrowser: tab group per task. DevTools: `pageId` on every call. agent-browser: never closes a user-attached browser | Nook: hidden Agent space, found by marker, never changes what a window shows, borrows logins of the space open at creation. Crest: per enabled space, badge and outline in agent colour. Ardia: any tab, "controlling - Stop" pill | Acts in the user's tab, glow and cursor UI; headless surface landed 2026-09 | Own headless Chromium, fresh context, no cookies. "Doesn't attach over CDP": cannot drive your browser |
| How the agent runs | Mostly outside agent (Playwright MCP, DevTools MCP, agent-browser). In-browser loop: browser-use (Python), Nanobrowser (extension). Stagehand v4 deleted its built-in agent | Outside agent in all of them (Crest, Nook, Ardia, Neon, T3 harness). Neon also has Do (local) and Make (cloud VM) | Google cloud planner, actions on device | Outside agent calls it. Minting needs OpenAI models |
| Model providers | Client supplies the model for MCP tools. browser-use, Nanobrowser: BYO ? | T3 drives provider CLIs (Claude, Codex, Cursor, OpenCode). Others: your agent | Gemini only; paid US tiers | `gpt-6.1-sol` and `gpt-6-luna` hardcoded; `OPENAI_API_KEY` required to mint. Replay: no model |

---

## Matrix B: outside-agent access

### B, part 1: rac today, ego(lite), Aside, BrowserOS

| | rac today | ego(lite) | Aside | BrowserOS (and neo) |
| --- | --- | --- | --- | --- |
| MCP | Only for the agent rac launched, only during a run. 15 tools | No MCP; shell commands | `aside mcp` (stdio), 4 tools: `exec` (Aside's own agent as a subagent), `repl` (Playwright-style JS), `memory_search`, `browser_profiles` | neo MCP (Rust, 127.0.0.1). BrowserOS `/mcp` on `0.0.0.0:9200` |
| CLI | None | `ego-browser` helper in the app bundle, linked to `~/.local/bin`; `ego-browser nodejs <<EOF` | `aside` CLI: run, resume, steer, queue, stop, memory, skills, host, settings, guide | Go CLI removed 2026-10-13 |
| Skills install | None | Stub written at launch to `~/.agents/skills` and `~/.claude/skills` if missing; never overwrites; `ego-browser skill` prints the guide that matches the binary. Plugins for nine hosts | `aside skills install --target codex, claude-code, cursor, opencode, general`; 15-line stub that says run `aside guide` | Connect page writes 7 agents' configs plus a `SKILL.md` (Claude Code, Codex, Cursor, OpenCode, Antigravity, VS Code, Zed); Claude Desktop `.mcpb` |
| Transport and auth | Unix socket `<profile>/rac-agent-mcp/<token>/s`, folder 0700, socket 0600, reached with `nc -U`. No secret; same-user check only; path visible in `ps` | Chromium ProcessSingleton Unix socket. No auth beyond the OS user (inf.). Open: does it check the caller | CLI to daemon on `127.0.0.1:21420`, WebSocket tRPC, signed challenge with a Secure Enclave key; CLI tokens in `auth.json` (0600) | MCP with no token; no peer check; CDP 9100 and 9110 open to any local process; proxy always binds `0.0.0.0` |
| Works with AI off | No. AI off removes the MCP server | Yes: ego has no AI. Stays in the tray after the last window closes | Needs the daemon and an account for local MCP. Signed-out local profile ? | No. Sidecar and open CDP port start on every launch; no off switch |
| Per-agent permissions | None. One global level for whatever runs | None. Docs tell you to run your agent with its approvals off | Per-task mode (read-only, guard, full-access). Per-client scope ? | None. MCP annotations (`destructiveHint`); coding agents run approve-all |

### B, part 2: Dia, Comet, Atlas, Yab

| | Dia | Comet | Atlas | Yab |
| --- | --- | --- | --- | --- |
| MCP | None | None public. A hidden `chrome.perplexity.mcp.addStdioServer` API was disabled after SquareX's report (2025-11-19) | None | `yab mcp`, 69 tools |
| CLI | AppleScript and Raycast only | None | None | `yab "task"`, `yab serve`, `yab setup` |
| Skills install | n/a | n/a | n/a | One-click install into Claude Code and Codex; plugin with a skill |
| Transport and auth | n/a | n/a | n/a | Stdio bridged to a socket "only your macOS user can open". Remote assistants pair by 8-character code through a Cloudflare Worker relay |
| Works with AI off | n/a | n/a | n/a | ? |
| Per-agent permissions | n/a | n/a | n/a | Ask, Auto, Bypass modes; per-site "Always here" and "Never here" |

### B, part 3: open stacks, other doors, Chrome, Pomerado

| | Open agent stacks | Other browsers' outside-agent doors | Chrome | Pomerado |
| --- | --- | --- | --- | --- |
| MCP | Playwright MCP, DevTools MCP, agent-browser (same binary over stdio) | Crest stdio helper per space (29 tools). Nook streamable HTTP `127.0.0.1:47823/mcp` (31 tools). Neon MCP Connector through an Opera-run proxy. T3 `/mcp`. Ardia: none (CLI) | WebMCP: sites offer tools to agents. DevTools MCP can attach after a consent dialog (Chrome 144+) | `pomerado-mcp` (stdio); every saved integration is its own MCP server |
| CLI | Playwright CLI and agent-browser over a daemon socket; DevTools CLI over a Unix-socket daemon | Ardia `ardia` CLI (Python 3.13 + pydoll, pinned by SHA-256). Neon `opera-browser-cli` over CDP on 9224. T3 `t3 thread ...`. Cra/Helium: URL scheme and AppleScript | n/a | `mint` and `run` only |
| Skills install | agent-browser: thin skill stub, full text loaded on demand | Ardia: `general, codex, claude-code, cursor, opencode`. Neon: ? | n/a | ? |
| Transport and auth | Mostly stdio (client owns the process). Playwright extension mode: local WebSocket. Attach to real Chrome: approval dialog per connection | Crest: Unix socket, peer identity by code signature (audit token), interpreters vouch for nothing. Nook: 0600 bearer token, non-localhost `Origin` gets 403. Ardia: random 0600 token, constant-time compare. Neon proxy: Opera account OAuth. T3: OAuth 2.1 + PKCE, pairing codes, 30-day sign-ins. Floorp OS: empty token, `Access-Control-Allow-Origin: *` | Per-connection approval in `chrome://inspect/#remote-debugging`; none of the agent guard applies | Local stdio; ? |
| Works with AI off | Yes (no browser AI involved) | Crest, Nook, Ardia: yes, independent of any AI switch. Nook needs Developer Mode and Browser Control on | Yes, but unguarded (inf.) | Replay: yes. Minting needs an OpenAI key |
| Per-agent permissions | Playwright extension: one client per tab group, user drags tabs to grant or revoke. Otherwise the MCP client's prompt | Crest: only spaces the user enabled; asks once per agent. T3: read-only default or a mode ceiling. Neon: read tools on, writes off until enabled. Ardia: one global switch, no per-site rules | Origin gating applies to Google's agent only | Authority `read` or `write` fixed at mint time |

---

## Matrix C: safety

### C, part 1: rac today, ego(lite), Aside, BrowserOS

| | rac today | ego(lite) | Aside | BrowserOS (and neo) |
| --- | --- | --- | --- | --- |
| Approval levels | `ask`, `careful`, `auto` (default `auto`) plus per-site Always/Never. No level skips the risky list | None enforced by the browser | `read-only`, `guard` (default), `full-access`. Guard's rules default to allow; only outside-folder reads and writes ask. Final confirm ("Ask first") is off by default and skipped for routines and channels | None at runtime in BrowserOS. Chat mode is read-only tools. neo relies on the caller; human hand-off by default |
| Risky-action list | Always asks: native submit controls, Enter in a field, password, payment and file fields, words like buy, send, post, delete, sign in, upload, unclassifiable targets, `go_back` | None. Guide never mentions payment | When final confirm is on: send, post, buy, delete, invite, settings changes, final form submits | None. neo tools carry `destructiveHint` |
| Cross-origin rules | Blocks non-http(s) and any URL not from a user message or a link the model was shown (exact match). Containment: navigation only to approved origins; popups, downloads, file pickers refused. **At `auto`, cross-site navigation is free** | None | Rule kinds `tool/browser/network/computer`, deny over ask over allow; no origin-flow rule found | Refuses `javascript:`, `file:`, `data:`. Tab ownership labels are not barriers |
| Prompt-injection defenses | Page text nonce-wrapped and labelled untrusted; page-blind critic at `careful` only (fails closed, 4 s); published-vs-private snapshots; TOCTOU re-checks. No origin pinning | None. Raw CDP plus Node egress in model-written scripts | Spotlighting wrapper `[BEGIN_UNTRUSTED_TOOL_OUTPUT ...]`, role-tag neutralizer, "stop on suspected injection" prompt. **Skipped for a hard-coded list of strong models** (GPT-5.4 to 6.1, Opus 4.6 to 5.5, and more) | Per-call random nonce fences (16 hex) around page text and `run` output; prompt rules |
| Credential handling | Password and payment values redacted in snapshots and logs; those fields always ask. No fill-by-reference | No redaction found; agent can read all cookies, including HttpOnly | Vault: agent gets opaque `passwordRef`; origin checks, cross-site fill block, none in incognito, audit log. Default **Always allow** | neo: `credentials` list, add, fill through a browser-side domain; fills, never submits; no password in results when filling by id. BrowserOS keys stored **plaintext** in SQLite |
| Logging and replay | Step rows (args with password text redacted, first 2,000 bytes of result, guard decision). Chat history plaintext JSON. No audit log, no trace, no replay | Action receipts (popups, dialogs); ref ledger on disk. No audit log | JSONL transcripts and SQLite per session. Replay ? | neo: SQLite audit (redacted args), a JPEG per step, rrweb replays (masks only password, OTP, card fields; **other typed text readable**), 7-day retention |
| Known incidents or exfiltration demos | None public. Known `auto` policy gap (below), exploitability untested | Issue #315 (open since 2026-08-24): page-planted instruction can exfiltrate HttpOnly cookies; maintainer disputes severity. #303: agent cleared cookies and logged the user out | None found. Privacy findings instead: hourly whole-profile cookie snapshot with sync on, Claude Code impersonation | Issue #2424: unauthenticated MCP and CDP; no public exfiltration demo found |
| Evals or red-team suite | None. About 284 unit tests including guard tests (CI never runs them) | Benchmark of 31 tasks with one injection fixture (a résumé that says tick every box); vendor-run | Pi fork has `evals`; no public red-team suite | Conformance tests with hostile fixtures, not model evals; weekly eval app deleted 2026-07 |

### C, part 2: Dia, Comet, Atlas, Yab

| | Dia | Comet | Atlas | Yab |
| --- | --- | --- | --- | --- |
| Approval levels | Chat starts with no other-tab access and no write actions | One mode; per-site "Block tasks" | Logged-in or logged-out mode; "Watch Mode" on sensitive sites | Ask, Auto, Bypass; Cmd-Return approves strong actions, Return weak, Esc "Not now". Auto is the default per rac's own comparison (the manual never says "default") |
| Risky-action list | Inserting data into third-party sites needs approval in a Dia-controlled view; calendar events stay drafts | Confirms email and messages, calendar changes, final orders, entering user details | Sensitive sites (banks); cannot run code, download, install extensions, use autofill or memories | Auto asks for Mac access and send, pay, delete, upload. Money thresholds ($20, $50, $100) and a monthly cap |
| Cross-origin rules | **URL provenance**: a URL is fetchable only if it came from the user or a page they viewed; added query parameters rejected | ? | Fresh in-memory storage in logged-out mode | A task that read your mail asks before sending its words to a site you have not visited |
| Prompt-injection defenses | Password fields and irreversible buttons invisible to the agent; detection abandoned after every detector was bypassed in-house | Four layers incl. BrowseSafe classifier (36% bypass, claim); confirmations regardless of detection | Adversarially trained model; OpenAI says injection "may never be fully solved" | "The browser holds that yes, not the model" |
| Credential handling | Passwords invisible to the agent | "Never has access" (claim); Guardio showed saved-card autofill | No saved passwords or autofill for the agent | Passwords filled and never shown; card numbers after Touch ID; "private tabs don't exist for agents" |
| Logging and replay | ? | ? | Agent pages stay out of history | ? |
| Known incidents or exfiltration demos | In-house fetch-tool leak, disclosed 2026-02-12; UI spoofing CVE-2025-15032 and CVE-2025-13132 | Brave (Reddit text leaked email and OTP), Guardio fake shop, CometJacking (link query), screenshot text, HashJack, SquareX MCP API | Omnibox prompt trick (NeuralTrust), Tainted Memories (LayerX), OpenAI's RL attacker found long attack chains | None found in the digests |
| Evals or red-team suite | ? | BrowseSafe-Bench (14,719 examples, MIT); Trail of Bits audit | OpenAI RL attacker | ? |

### C, part 3: open stacks, other doors, Chrome, Pomerado

| | Open agent stacks | Other browsers' doors | Chrome | Pomerado |
| --- | --- | --- | --- | --- |
| Approval levels | browser-use: none by default (domain lists). Playwright and DevTools MCP: the MCP client's prompt. agent-browser: opt-in `--confirm-actions`, `--action-policy`. Nanobrowser: Ask default, per-site Allow, Ask, Block | Nook: `auto`, `ask` (default), `disabled`; "token is the approval" for scripts. Crest: reach limits, history deletes and opening windows ask. Ardia: none (a pill and a switch). Neon: writes off until enabled. T3 Code: **Full access by default**, no card on browser actions | Confirms sensitive sites, sign-in, purchases and messages; "Take over task" | `read` or `write` authority fixed at mint; the agent is told to ask the user before writes |
| Risky-action list | Nanobrowser: submit, pay, delete gated; payment, access grants, secret input or page `prompt` are the user's step in every mode; amounts count ("Pay $5" differs from "Pay $500") | Nook: navigate, click, new tab ask in `ask`. Crest: password values omitted from reads | Deterministic sensitive-site list (not inspectable) | Declared questions only |
| Cross-origin rules | Nanobrowser: per-site. agent-browser: allowlist refused in real-login modes | Nook: `personNamed` check asks on unnamed sites even at `auto`, on-device models only; cloud models have no check. Crest: http/https only | Agent Origin Sets: readable data may flow only to writable origins; 19-predicate origin gating; new-origin confirm on by default from M158 | Credentials typed only on declared origins |
| Prompt-injection defenses | Nanobrowser fails closed on refs. Research: injection hijacks 17-86% of agents (WASP); adaptive rewrites reach 78.79% (BrowseSafe++) (claims) | Nook: `page_context_<8 hex>` wrapper. T3: tag with random id, U+2060 inserted after `$`, `@`, leading `/`. Crest: page-world scripts behind a toggle | Critic sees only action metadata; server-side classifier (claim) | Architectural: after minting, no model reads the page. During minting, a model reviewer (Guardian) |
| Credential handling | agent-browser: AES-256-GCM auth vault, chmod 600. Playwright: profile per workspace | Crest: passwords omitted, cookies and auth headers hidden. Ardia: auth headers stripped. T3: one-use `secret-ref` | Model never sees passwords | Saved logins are Cloud-only; password retyped per call |
| Logging and replay | Playwright: response lists the code it ran. agent-browser: ? | Crest: bar naming the agent. T3: ? | Actor journal in memory; `--actor-trace-path` writes a trace | Saved integration is a folder you own |
| Known incidents or exfiltration demos | Playwright's `browser_run_code_unsafe` is "RCE-equivalent"; Stagehand cache sends raw AX trees to Browserbase | Neon: Brave showed invisible HTML exfiltrating account details (2025-10). Floorp OS: wildcard CORS | None public | None; generated JS runs with user file and network access, no sandbox |
| Evals or red-team suite | Nanobrowser: 68 HTML fixtures, a fake model server, four graded outcomes per attack (the best template). DevTools MCP: call-assertion scenarios | Nook: a 22-case on-device eval reportedly obeyed planted text every run (claim). Crest: none | Automated attack sites, bounty up to $20,000 (claim) | No red-team suite; 70 browser tests on fixture sites |

---

## Matrix D: repeatability

### D, part 1: rac today, ego(lite), Aside, BrowserOS

| | rac today | ego(lite) | Aside | BrowserOS (and neo) |
| --- | --- | --- | --- | --- |
| Routines or scheduled runs | None. Planned for phase 6 | None | Cron, heartbeat (wake an existing chat), event-triggered. RRULE schedules. Overlapping runs skipped; pauses if the target chat is gone; each run can carry its own permissions. Local or cloud; prompts stored server-side. Free 3, Pro unlimited | A `jobs` table exists in SQLite; details ? |
| Recipes or deterministic replay | None | Refs persist across processes, but no recorded replay. Heredoc scripts are replayable by hand | REPL scripts; skills. No deterministic replay | neo `save_skill`, `mark_skill_run`. rrweb replays are for viewing, not re-running |
| Memory | Chat history in plaintext JSON (16 MB cap), saved by default. No agent memory | None in lite. Site learnings: 3 example packs (GitHub, Google, X); the accumulation step is "coming soon" | Markdown memory (`MEMORY.md`, `people/`, `sites/`...), on by default, nightly consolidation; retention never, 30, or 90 days | Memory, skills, workflows, and sync were shipped and removed |

### D, part 2: Dia, Comet, Atlas, Yab

| | Dia | Comet | Atlas | Yab |
| --- | --- | --- | --- | --- |
| Routines or scheduled runs | Morning Brief | Background Assistants (Max) | None | Routines on any schedule (0.18); watch a thread every two hours |
| Recipes or deterministic replay | Skills (slash prompts, can call other skills) | Shortcuts (`/tldr` and similar) | Saved Prompts | Site "skills" for agents (Gmail, GitHub, LinkedIn, Amazon) |
| Memory | Retired 2026-09-24 and deleted; replaced by on-demand search of chats and history | Unclear | Opt-in browser memories; gone with the app | Markdown notes on the Mac, editable, with an off switch; short notes go with every task |

### D, part 3: open stacks, other doors, Chrome, Pomerado

| | Open agent stacks | Other browsers' doors | Chrome | Pomerado |
| --- | --- | --- | --- | --- |
| Routines or scheduled runs | ? | Neon: scheduled tasks (paid). Others ? | None | Hosted Cloud only (claim) |
| Recipes or deterministic replay | browser-use replays a saved run with new variables and stops at the first unmatched step. Stagehand caches resolved actions and re-observes when the page changes. Playwright: shows the code it ran | Crest, Nook, Ardia: none | Skills and presets (50+) | **Core idea**: an AI explores once, then saves a small program; replay needs no model or key. Writes its own tests, 70% must pass. Self-healing is a hosted feature, not in the open repo |
| Memory | ? | Neon: "long memory" (paid, claim) | Personal Intelligence, opt-in | Not applicable |

---

## The exfiltration gap in rac's auto level

**What the brief describes.** At `auto` (rac's default), three things need no confirmation card: opening a link to a site the user did not name, reading any page, and typing model-written text into the tab the user attached. Put those together and a prompt-injection chain exists:

1. The user attaches a tab. The page there (a hostile site, or an ordinary site with a hostile comment) contains hidden instructions and a visible link to a logged-in site, such as the user's mail.
2. The agent opens that link. Rac's URL rule is satisfied because the link was shown to the model, and cross-site navigation is free at `auto`. Reading the page is free.
3. The agent switches back and types what it read into a text field on the attached page. Typing on an attached tab is free even when the text came from the model, and the page's own script sees every keystroke. Pressing Enter would ask, but the script does not need it.
4. The page sends the text to the attacker. Rac's containment limits navigation, popups, downloads, and file pickers. It is not a network sandbox, so the page can still make requests.

Facts behind this: the permission table in `docs/internals/ai.md` and the unit test `AutoAsksOnlyForRiskAndForeignTyping` in `patches/rac/agent/13-permission-levels.patch`. That test shows navigation to another site, and typing model text on the attached tab, both allowed. It also switches off URL provenance for its navigate case, so a hostile page's link still counts. The policy is confirmed in code; the exploit has not been run. No evals exist.

**How the others would or would not block it**

| Product | Blocks it? | Why |
| --- | --- | --- |
| ego(lite) | No | Nothing is enforced. Model-written scripts have raw CDP and unrestricted Node network access; reading cookies and sending them is the same class of attack and is open as #315. Every official guide says to turn off the host agent's own prompts |
| Aside | Probably not by default | Guard defaults to allow; final confirm is off by default and skipped for routines. Spotlighting is skipped for the strongest models. I found no deterministic gate on typing or navigation (absence in a 15 MB bundle is not proof) |
| BrowserOS / neo | No | No runtime approval; step cap only; neo relies on the calling agent |
| Yab | Partly, by design | Auto asks before mail's words go to a site not yet visited. That is a data-flow rule. How wide it applies beyond mail is ? |
| Chrome (Gemini) | Yes, by design | Agent Origin Sets: readable data may flow only to writable origins; new-origin confirm on by default from M158; a critic that sees only metadata. The first shipped version was write-set only |
| Nook | The navigation step, on-device models only | `personNamed` asks on unnamed sites even at `auto`. Cloud models have no check. Nook has no typing tool |
| Nanobrowser | Partly | Per-site Ask by default; payments and secrets are the user's step. Typing exfiltration ? |
| Edge (Balanced default) | Likely the navigation step | Asks on unfamiliar sites (claim, from guides) |
| Dia | The URL variant only | URL provenance stops model-built URLs. Chat starts with no other-tab access |
| Comet, Atlas | No reliable block | Confirmations cover sends and orders, not typing into a page. Comet leaked a one-time code by posting a comment (Brave) |
| Atlas logged-out mode, Brave | Yes, by removing the secret | A fresh storage partition has no mail to read |

The lesson from the closed browsers: detection (classifiers, prompts) was bypassed everywhere; the defenses that hold are rules that work even if the model is fooled.

**Fix options for rac**

1. **First visit to an unnamed site asks, even at `auto` (about 1 to 3 days plus tests).** One card on the first navigation or open-tab to an origin the user did not name: Allow once, Always on this site, Don't allow. After that it counts as named for the turn. Chrome made new-origin confirmation the default from M158; Nook does the same on-device. Cuts the chain at step 2. Trade-off: more cards in `auto`, and `auto` stops feeling like Yab's Auto. Does not help if the user named both sites, or if the hostile text is on a site that already holds the data.
2. **A data-flow rule on typing (about 3 to 5 days plus tests).** After the agent has read any origin other than the one it is typing into, typing text that is not in the user's own messages asks, and the card shows the exact text. This is the Chrome and Yab idea in a cheap form: no taint tracking, just "you read elsewhere, so ask". Cuts the chain at step 3 even if option 1 is bypassed. Trade-off: some false cards on legitimate tasks like "copy my order number into this form". The model can launder text, but the card still shows the text.
3. **A clean agent context (about 1 to 2 weeks).** Agent tabs run in an in-memory partition with no logins, thrown away afterward (Atlas, Brave). "Use my sign-ins" becomes an explicit, per-run or per-site choice. Removes the secret rather than policing the flow. Trade-off: the agent is far less useful on logged-in tasks unless the user opts in, and Views and profile work is needed. It also belongs to the agent-space work below.

**Recommended:** 1 and 2 together (they edit the same table in `ActionGuard`), then 3 as part of agent spaces. A zero-code stopgap is to make `careful` the default until the evals exist, since `careful` asks for unnamed sites; but without a direct provider every `careful` step becomes a card. Whatever ships, write the eval first: reproduce the chain on local fixture pages against 3 to 4 models, and ratchet it in CI.

---

## Options for rac's agent architecture

All four keep the rule that the browser holds the "yes". They differ in who drives, and how much new surface rac carries.

### Option (a): keep the built-in agent, add one guarded door for outside agents

**What it is.** Today rac has one entry point for tool calls, `AgentController::HandleToolCall`, used by both the built-in loop and rac-launched ACP agents. Make that the shared tool layer. Grow today's per-run MCP socket into a long-lived endpoint with its own switch ("Let other apps' agents use rac"), off by default and independent of the AI switch. Ship a signed `rac` helper in `Contents/Helpers` with `rac mcp` (stdio relay to a per-user 0600 socket), a few shell verbs, `rac skill` (a thin stub that prints the guide matching the build), and a one-click "Add to my agents" in Settings. Every call passes the existing guard, cards, containment, and site rules. No raw CDP, no script runner.

**Pros.**
- Reuses the guard, cards, snapshot, and refs that already exist.
- Fixes the developer's wish: use your own agent, leave rac's off.
- Cost is moderate (about 2 to 4 weeks with per-client consent).
- Nothing listens unless the switch is on.

**Cons.**
- Several clients at once break "one active turn per profile".
- Peer identity on a Unix socket is weak: macOS may name the helper, not the real client.
- Adds an MCP surface to maintain (spec 2026-07-28 is stateless).
- Works in the user's tabs, so risk is the same as today's.

**Safety impact.** Neutral to good if the `auto` fix ships first. Outside agents default to read-only or `ask` until evals exist. Risky actions always ask, for every client.

**What changes for a user.** A new "Outside agents" setting with a copy-paste line and a connect button. A card on first connect names the agent and asks for a level. A "connected agents" list with Revoke. Without the setting, nothing changes.

### Option (b): outside agents first, like ego; the built-in agent becomes one client

**What it is.** Treat rac as the browser your coding agent drives, and put the main work there: batched steps (`run_steps`, stops at the first failure or card), stable locators, action receipts, hover, dialogs, screenshots, and a compact snapshot with scope. The built-in assistant and ACP agents use the same door and get no special path. The product story moves from "an assistant in your browser" to "the browser agents drive".

**Pros.**
- Matches where open stacks went: Stagehand deleted its built-in agent, and the fastest-growing stacks are tools for outside agents.
- One path to test, one tool layer.
- Strongest answer to Aside's developers.
- Cuts rac's cold-start problem for people who already run a warm agent.

**Cons.**
- Repositions rac away from the Dia-like assistant that VISION describes, and the maintainer must approve that.
- The built-in agent stops being a differentiator, and it is what makes rac usable for people with no coding agent.
- A bigger tool surface means more to guard and test before any evals exist.
- ego's safety is thin; copying its ergonomics without a guard on every client would be a regression.

**Safety impact.** Larger blast radius for the same guard, so evals must come first. Batching needs one card per risky step, not one per batch.

**What changes for a user.** The side panel assistant becomes secondary or optional. The default install shows "Connect your agent" first. Heavier use of agents in the background.

### Option (c): hybrid, door plus agent-owned spaces

**What it is.** Option (a), plus the part ego, Nook, Yab, and Crest all built: agent-owned tab groups or a reserved Agent space. Agent tabs are muted and backgrounded, never steal focus, are labelled by client, and close after idle (15 to 30 minutes, not restored after a crash). Ownership has states (user, agent, handed off). The user can take over a tab at any time, and any real input pauses the agent. Each client gets its own group, which solves the multi-client problem. An optional "clean" mode runs with no sign-ins, which is fix option 3 above. Be honest in the UI: if cookies are shared, say "the agent uses your logins", not "isolated".

**Pros.**
- Real answer to focus theft and multi-client concurrency.
- Takes away the secret for exfiltration when clean mode is chosen.
- Matches what the field converged on.
- The most polished user story: tell the agent, watch it work in the background.

**Cons.**
- The largest build (about 4 to 8 weeks), mostly in Views and session-restore hooks, which are the hot upstream files.
- A hidden tab must keep rendering. Nook uses an alpha-0, off-screen window; whether Chromium's capture count does the same job is an open spike.
- More upstream hunks, against rac's "cheap to update" rule.

**Safety impact.** Best of the four. Clean context plus per-client groups plus the guard. The visible ring and pill stay static (no endless glow).

**What changes for a user.** Agent work appears in its own labelled group and never moves their tabs. There is a Stop all agents control and a Take over button on each agent tab.

### Option (d): close the unguarded doors, ship no new door yet

**What it is.** Do the safety work only: fix the `auto` gap, add the eval suite, and turn on Chromium's default-profile check for `--remote-debugging-port` and decide the `chrome://inspect` approval mode (both give any local app the whole logged-in profile, with none of rac's guard; neither is patched today). Optionally add a small allow-listed verb set (URL scheme or AppleScript, as Cra and Helium do).

**Pros.**
- Smallest change (days to about 2 weeks).
- Removes real exposure that exists today, with AI off.
- Gets evals in place before capability grows.

**Cons.**
- Does not give outside agents a guarded way in, so developers keep reaching for raw CDP, which has no guard.
- Does nothing about the Aside comparison.

**Safety impact.** Strictly better than today.

**What changes for a user.** Almost nothing visible, apart from new cards at `auto`.

### Recommendation

**Go in stages, ending at (c), starting with (d).**

1. **Now (days):** close both CDP doors and fix the `auto` gap (options 1 and 2). Build the injection eval harness (local fixture pages plus a fake model server, graded on four outcomes). This is the one non-negotiable step, because every later step adds capability and blast radius.
2. **Next (2 to 4 weeks):** option (a). A separate "Outside agents" switch, `rac` helper with `mcp` and `skill`, per-client consent card and level, read-only by default. Fold in the cheap tool gaps that outside agents will hit at once: a general `press_key`, `hover`, `handle_dialog`, a ref-returning `find`, and cheaper snapshot deltas. Keep the tool list small.
3. **Then (4 to 8 weeks):** the agent-space part of (c), with clean mode and per-client groups.
4. **Later, and not before the evals are green:** batching (`run_steps`) and local recipes (a data-only record-and-replay in the Pomerado spirit, always through the guard). No scripting runner on the real profile.

Why not (b) first: it changes what rac is, and it expands capability faster than safety. Why not stop at (a): several clients and focus theft will hurt as soon as the door opens, and the developer's request is really "drive it from my agent, in the background".

---

## Unknowns

- Whether the `auto` chain works end to end on a real build. The policy is confirmed from code and the unit test; it has not been run. The main checkout's build tree predates agent patches 13 to 17.
- Whether `chrome://inspect/#remote-debugging` approval mode and `--remote-debugging-port` really give a guard-free door on rac. Code reading only.
- ego: does the singleton socket check the caller; are agent Spaces separate browser contexts at all (the docs say yes, the code shows shared cookies); does the closed native side redact password values.
- Aside: any deterministic gate on risky clicks; whether `aside mcp` and `repl` work with a signed-out local profile; whether Remote Control sees REPL code in plaintext.
- BrowserOS: exact snapshot line; ref invalidation rules; what the `jobs` table does.
- Dia, Comet, Atlas: snapshot lines, ref stability, tool counts, and logging are not published in the sources I have. Comet's current state and why Atlas was shut down are unknown.
- Yab: tool groups, whether its agent defaults to Auto (the manual does not say "default"), how far the mail data-flow rule reaches, whether it works with AI off.
- Open stacks: which model providers browser-use and Nanobrowser support; agent-browser's logging; scheduling anywhere in this group.
- Chrome: whether rac can use `components/origin_gating` without Glic; what the sensitive-site list contains.
- Pomerado: tweet unread (403); whether the minter ever sees a raw password; whether a different base URL for the model works; how hosted repair works.
- Whether a Unix-socket MCP can use `claude mcp login` or `codex mcp login`. T3 uses loopback HTTP with OAuth for that; a stdio helper may be enough for `mcp add`.
- Whether Chromium keeps a hidden agent tab rendering without Nook's alpha-0 off-screen trick.
- Costs and phase estimates are inferences from the dossiers, not agent-thread measurements.
- Maintainer choices still open: whether outside agents may use the user's attached tab or only their own groups; whether the outside-agent switch needs AI on; whether outside clients start at `ask` or `careful`; whether the built-in assistant stays the default story.

## Sources

Read in full or in the sections named, all under `/Users/knewton/.t3/worktrees/rac/t3-bb0e4397/`:

- `plans/context/maintainer-brief.md`
- Digests in `plans/research/digests/`: `ego-lite.md`, `aside.md`, `browseros.md`, `agent-stacks.md`, `chromium-agent-internals.md`, `closed-ai-browsers.md`, `t3code.md`, `pomerado.md`, `rac-baseline.md`, `long-tail.md` (agent sections), `local-first-and-sidecars.md`, plus agent sections of `nook.md`, `ardia.md`, `helium.md`, `cra.md`, `ora.md`, `zen.md`, `motion-and-feel.md`
- Dossier sections: `plans/research/agent-stacks.md` (page representation, tool sets, element addressing, token budgets, multi-tab, safety), `plans/research/closed-ai-browsers.md` (Agents and AI: how each agent works, outside-agent table, incident table, defense ranking), `plans/research/ego-lite.md` (how an agent gets in, tool model, approvals), `plans/research/aside.md` (tools, memory, routines, permissions)
- `docs/internals/ai.md` (MCP server, agent, snapshot, tools, guard, containment, critic)
- `patches/rac/agent/13-permission-levels.patch` (test `AutoAsksOnlyForRiskAndForeignTyping`)
- Cross-check for Yab and rac: `plans/context/competitors-ardia-yab-2026-10-23.md`
