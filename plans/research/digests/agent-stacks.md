# Digest: agent-stacks.md (open browser-agent stacks)

## In plain English

Six open projects let an AI drive a browser. All show the AI the page as a
short list where each button or field gets a tag like `e12`; rac's own agent
already works this way and its line format nearly matches the two most-used
formats.

Three lessons. One: cost is the real problem — four tools in one test scored
the same but differed 3.2× in tokens, mostly from page text sent per step.
Two: developers want to bring their own agent, so the fastest-growing stacks
are tools for outside agents, not agents; Stagehand deleted its built-in
agent. Three: prompt injection is unsolved — the stacks whose browser, not
the AI, holds the "yes" got it right.

## Key facts

The dossier fact-checked itself (33 claims checked, 9 corrected; all applied
below).

### The field (GitHub API 2026-10-25, FACT)

| | Engine driven | License | Stars | Age | Releases tot/6mo |
| --- | --- | --- | --- | --- | --- |
| browser-use (68.8k Py) | Chromium, raw CDP | MIT | 119,110 | ~2 yr | 140/17 |
| Playwright MCP (~28k TS, in the Playwright monorepo) | 3 engines v. Playwright | Apache-2.0 | 38,619 | 19 mo | 73/13, still `0.0.x` |
| DevTools MCP (28.5k TS + 60.8k Lighthouse) | Chrome, Puppeteer | Apache-2.0 | 54,123 | 13 mo | 64/19, ~1–3 wk |
| Stagehand (~106k TS; 49k w/o tests) | Chrome, own CDP; v4 = extension | MIT | 25,806 | 31 mo | 82/26 |
| Nanobrowser (46.7k TS) | host browser, `chrome.debugger` | Apache-2.0 | 14,178 | 22 mo | 16/2, 0.3.0 rewrite 2026-10-15 |
| agent-browser (107.6k Rust) | Chrome for Testing, Rust daemon | Apache-2.0 | 44,574 | 9.5 mo | 114/33, ~weekly |

Extras read: Browser Harness (browser-use's MIT CLI/daemon, 18,611 stars,
2026-04-17) and Anthropic's `browser_toolset_20260801` contract.

### Architecture (FACT)

- browser-use: one Python asyncio process; `BrowserSession` CDP client
  (`session.py` 4,197 lines); DOM+AX+DOMSnapshot merged into HTML-like lines;
  40,000-char prompt cap; screenshot each step.
- Playwright MCP: thin wrapper over monorepo code; ARIA tree computed
  in-page, then a distiller; CLI over a socket daemon; extension mode relays
  CDP over a local WebSocket.
- DevTools MCP: Node/Puppeteer; `pageId` on every page tool for concurrent
  agents; CLI over a Unix-socket daemon.
- Stagehand v4: SDK (TS/Py/Go) on JSON-RPC from one Zod schema; runtime is a
  Chrome extension service worker; built-in `agent()` removed ("built for
  models that couldn't reliably drive a browser on their own").
- Nanobrowser: MV3 extension; agent loop in the worker (0.3.0 removed
  planner/navigator); CDP only via `chrome.debugger`; IndexedDB.
- agent-browser: Rust CLI → per-session daemon (1 h idle exit; never closes
  a headed/user-attached browser); MCP = same binary over stdio.
- rac: in-process (AnnotatedPageContent + actor framework, no CDP); own loop
  or ACP-launched Claude Code/Codex on a per-run Unix-socket MCP.

### Page representation and refs (FACT)

- Playwright/agent-browser/Nanobrowser use `- button "Submit" [ref=e2]` ARIA
  lines; rac's `- button "Sign in" [ref=e6] [submit]` matches the most-used
  formats almost character for character — do not change the basic line
  (INFERENCE).
- Ids: Playwright `e{N}` stored on the element, survives while role+name stay;
  DevTools `{snapshotId}_{n}` reused via `loaderId_backendNodeId`; agent-browser
  keeps refs across snapshots with a same-role-and-name fallback that fails
  when ambiguous; Nanobrowser fails closed. rac is strictest: `e{N}` never
  reused, keyed tab+doc+node, `stale_ref` on navigation, TOCTOU re-checks at
  mouse down/up/between keys.
- Cursor-interactive discovery: agent-browser finds `cursor:pointer`/`onclick`/
  `tabindex`/`contenteditable` elements the AX tree misses
  (`snapshot.rs:772-830`); Playwright marks `[cursor=pointer]`.
- rac snapshot: 48 KiB cap + `[truncated …]`; in-viewport only unless
  `full:true`; passwords/payment redacted; links add `-> host/path?query`.

### Token cost (vendor-run numbers = CLAIM; none reproduced)

Browser Use's matched eval — one agent (Codex CLI 0.144.6, GPT-6 Luna), 100 BU
Bench V2.1 tasks, one shared cloud browser ([Browser Harness
README](https://github.com/browser-use/browser-harness)):

| Tool | Mean score | Median input tokens | Median cost |
| --- | --- | --- | --- |
| Browser Harness | 60.4 | 2.1M | $0.042 |
| Playwright MCP 0.0.83 | 60.0 | 4.4M | $0.066 |
| DevTools MCP 1.10.1 | 61.0 | 6.7M | $0.097 |
| agent-browser 0.39.1 | 56.3 | 3.3M | $0.056 |

"Limit" qualifiers: 100 of 200 tasks, one run each, Codex only, one shared
cloud browser; "no tool wins on score" (all CIs span zero); 3.2× token
spread. Levers: DevTools `includeSnapshot:false` + file outputs + JPEG/WebP
screenshots (3–5× smaller than PNG) + `--slim`;
Playwright writes implicit snapshots to a file and links them; agent-browser
claims ~200–400 tokens/page. Slack's inverse trade (CLI ~85 turns/~6M vs MCP
~40 turns/~3.8M) is second-hand (CLAIM). Turn count matters as much as bytes
(INFERENCE): batching and `fill_form` cut turns.
- **rac's delta is expensive (FACT):** `BuildDelta`
  (`snapshot_serializer.cc:694-728`) emits `- unchanged [ref=eN]` per
  unchanged line → 300 refs + 3 changes ≈ ~1,800 tokens. agent-browser's
  splice delta (`{startLine, deleteCount, lines}`, fallback to full) does the
  same in <100. Ref-less lines always count as changes (`cc:705-728`).

### Safety: who holds the "yes" (FACT)

- browser-use: nobody by default (domain lists only).
- Playwright MCP / DevTools MCP: the MCP client's prompt (`readOnlyHint`,
  "obtain permission" fields) — not a browser-side guard.
- Nanobrowser: the extension — Ask default; per-site Allow/Ask/Block;
  submit/pay/delete gated; "detected payment, access grant, secret input or
  page `prompt` dialog is the user's step in every mode, with no Approve";
  approval basis spans amounts ("Pay $5" ≠ "Pay $500", `gate.ts:103-113`);
  receipts split dispatched / reachedTarget / effect / postcondition.
- agent-browser: all security opt-in (`security.mdx:8`); `--action-policy`,
  `--confirm-actions` (auto-deny after 60 s; the non-TTY auto-deny belongs
  to `--confirm-interactive`); allowlist refused in real-login modes
  (`--cdp`, `--auto-connect`, `--profile`).
- rac: the browser — `ask`/`careful`/`auto`, always-risky list, site rules,
  published-vs-private snapshots, navigation/popup/download containment,
  page-blind critic, 25-call cap. Only rac and Nanobrowser have the browser
  decide (INFERENCE).

### Injection research (CLAIM, papers)

WASP ([arXiv 2504.18575](https://arxiv.org/pdf/2504.18575)): agents hijacked
mid-task 17–86%, end-to-end attacker success ≤16%. BrowseSafe++
([arXiv 2610.17457](https://arxiv.org/html/2610.17457)): adaptive rewrites
lift attack success to 78.79% avg, up to 95.41% (across target agents);
"some models can recognize prompt injections … yet still follow those same
injections". INFERENCE: detection alone won't hold rac's default `auto`;
structural rules must.

### rac's concrete gaps (FACT unless noted)

1. `press_key` is Enter-on-a-ref only (`tool_registry.cc:178`); peers have
   general keys (Escape, Tab, arrows) — the cheapest exit from overlays.
2. No `hover` (5 peers have it).
3. No `handle_dialog` — an alert stalls the agent; Playwright refuses other
   tools while a dialog is open and names the clearing tool.
4. `find_in_page` returns count+snippets, not refs; 4 peers return refs,
   saving a full snapshot.
5. No `fill_form` (DevTools: fewer turns, "more reliable"); collapses N
   confirm cards into one (INFERENCE).
6. No screenshot (agent-browser's `--annotate` labels keep refs in sync); no
   forward/reload, no `wait_for` text.
7. No WebMCP — yet Chromium 154 in rac's tree already ships the `WebMCP`
   runtime feature (experimental + origin trial), a `WebMCP` CDP domain with
   `readOnly`/`untrustedContent`/`consequential`, and actor `ScriptToolHost`
   (`runtime_enabled_features.json5:7026-7039`).
8. rac has only 15 tools (only `readOnlyHint` on them, `mcp_protocol.cc:119`)
   where peers use small defaults with opt-in groups; the dossier corrected
   Playwright's max to 72, not 83.
9. rac's MCP speaks spec versions 2024-11-05…2025-11-25 only; current is
   2026-07-28 (FACT).
10. **Two unguarded CDP doors (FACT; INFERENCE exploitable, not run):**
    - `--remote-debugging-port`'s default-data-dir guard runs only under
      `GOOGLE_CHROME_BRANDING` (`remote_debugging_server.cc:160-183`);
      rac is Chromium-branded → relaunching with that flag gives the whole
      logged-in profile, no prompt, no guard.
    - `chrome://inspect/#remote-debugging` approval mode
      (`kDevToolsAcceptDebuggingConnections`, default-on on macOS,
      `features.cc:206-210`) lets an app `--autoConnect` into the whole
      profile; Browser Harness auto-clicks Chrome's Allow sheet
      (`macos.py:12-48`). No Helium or rac patch touches either path.
11. Known `auto` hole: cross-site navigation + model-written typing in the
    attached tab needs no card (test `AutoAsksOnlyForRiskAndForeignTyping`,
    `patches/rac/agent/13-permission-levels.patch:329-370`; the build tree
    predates patches 13–17).
12. No evals. Nanobrowser's injection eval is the closest template: 68 HTML
    fixture pages, a fake OpenAI-compatible model server, four graded
    outcomes per attack (attempt / gate response / user decision / did the
    fixture server receive the data).
13. No outside-agent path today (no `mcp add`, no CLI, no skill); turning
    rac's AI off also removes its MCP server (maintainer brief).

### Storage and privacy (FACT)

- Telemetry on by default: browser-use (PostHog + persistent device id),
  DevTools MCP (Clearcut + CrUX URL lookups + npm update checks), Nanobrowser
  (PostHog, no ID). No telemetry found in Playwright MCP or agent-browser.
- Profiles: Playwright `~/Library/Caches/ms-playwright/mcp-{channel}-{hash}`
  (per workspace); DevTools `~/.cache/chrome-devtools-mcp/chrome-profile`;
  browser-use `~/.config/browseruse/`; agent-browser `~/.agent-browser/` with
  an always-AES-256-GCM auth vault and `chmod 600/700`; Nanobrowser IndexedDB.
- Stagehand: with Browserbase transport the cache ships raw AX trees to the
  API (`cacheService.ts:16-29`).

### Motion / agent-visible UI (FACT)

- Nanobrowser (only product UI): fixed overlay in a closed shadow root, four
  16 px edges, violet `rgb(124 92 255 / 0.6)` → blue `rgb(0 115 220 / 0.6)`;
  150 ms opacity show/hide; a **2 s infinite "breathe"** while working,
  off under `prefers-reduced-motion` (`border.ts:136-155`). Lives in page DOM
  (`data-nanobrowser-border`), repaints forever — rac's rule "nothing that
  repaints continuously" rules it out.
- agent-browser dashboard: port 4848, live viewport stream ("pair browsing").
- Worth stealing conceptually: Playwright annotate (user draws boxes + notes;
  agent gets screenshot+region+notes); DevTools "selected element" + human
  comments the agent reads; agent-owned tab groups (Playwright extension,
  Nanobrowser). Browser Harness's ♞ title prefix is page-visible
  (`document.title`, INFERENCE).

## What rac should take

Ranked; costs are rough agent-thread days (INFERENCE). 1–9 fix rac's own
agent; 10–11 evals; 12–16 outside agents (options, maintainer chooses).

1. **Splice-based snapshot deltas:** numbered `rev` + `{base_rev, startLine,
   deleteCount, lines}` hunks + removed refs; fallback to full; `unchanged`
   when nothing changed. Local to `snapshot_serializer.cc:694-728`.
   **S (1–2 days).**
2. **Stop attaching a full snapshot to every action:** short receipt
   (dispatched, page reacted, URL/title/tab changes, dialogs, downloads) +
   the splice delta; full snapshot only on document change or request.
   Keep at least the delta — rac binds approvals to the last *published*
   snapshot (INFERENCE). **S–M (3–5 days).**
3. **Fill the tool gaps, each through the guard:** general `press_key`
   (Enter/submit stay risky; Escape/Tab/arrows free on named sites), `hover`,
   `go_forward`, `reload`, `wait_for` text, `handle_dialog` with dialog-
   gating that names the clearing tool (`prompt` dialogs are the user's
   step), ref-returning `find` (≤20 matches), `fill_form` with one masked
   card, `screenshot` (≤1280 px JPEG, off by default for non-vision models,
   optional `--annotate`; never to the critic). **S–M.**
4. **Pre-dispatch cover/usability checks:** fail `covered by <div#consent-
   banner>` when another element covers the target; fail on
   hidden/disabled/off-viewport targets (agent-browser `README.md:101,
   1277`); rac's renderer validator is the home. **M.**
5. **Batch a turn's calls in order; halt at the first failure; answer the
   rest "Not executed: an earlier action in this turn failed"** (Anthropic
   contract); guard runs per call. **S.**
6. **Loop/stall detection:** hash last-20 actions + page fingerprint;
   re-plan nudge after 3 consecutive failures (browser-use
   `agent/views.py:66-131`); keep the 25-call cap. **S.**
7. **WebMCP as untrusted first-class tools:** list page-declared tools from
   the `WebMCP` CDP domain / `ScriptToolHost`; summaries capped (agent-
   browser: 16 tools / 4 KiB); invoke treated as submit unless a read on a
   named site; page-claimed `readOnly` never bypasses the guard. Requires
   the experimental flag. **M.**
8. **Hand payments, secrets, access grants to the user — no Approve button
   in any mode; approval basis includes amounts** (Nanobrowser
   `gate.ts:103-113`). The one place Nanobrowser beats rac. **S–M.**
9. **Option (maintainer's call): serve Anthropic's `browser_toolset_20260801`
   to Claude on the direct provider** — Claude's trained contract +
   Anthropic's server-side injection classifiers (CLAIM). 11 of 12 pointer
   members take coordinates (6 also a ref; `scroll_to` ref-only) → hit-test
   into the guard or refuse when a ref exists. Keep rac's tools for
   MCP/other providers. **M–L.**
10. **Build the injection + reliability eval suite first** — prerequisite for
    evidence about the `auto` default. Localhost fixtures + fake OpenAI-
    compatible model server (Nanobrowser template), four graded outcomes
    per attack + DevTools-style call-assertion scenarios; fake-model part
    in CI. Start with the known `auto` exfiltration chain (open link →
    read logged-in page → type into attached page). **M (1–2 weeks).**
11. **Optional benchmark:** mount a rac surface in Stagehand's harness
    (WebVoyager/Online-Mind2Web) vs Playwright/DevTools MCP. Manual, needs
    keys. **M.**
12. **Close the `--remote-debugging-port` hole now** (recommended
    regardless): a rac hook turning on Chromium's default-data-dir check.
    Dev profiles use other data dirs, so `worktree.sh run` should be
    unaffected (INFERENCE; verify). **S (a day with a test).**
13. **Decide `chrome://inspect` approval mode:** (a) keep and document as
    "expert, unguarded, whole-profile"; (b) disable by default via rac flag
    (**S**); (c) harden the dialog — name the connecting app, reject
    synthetic Accessibility presses (**M**; VoiceOver care). **M.**
14. **Outside agents as their own setting, off by default, independent of
    rac's assistant:** one stable per-profile Unix socket (mode 0600,
    same-user check); when off, nothing listens ("off costs nothing"). A tiny
    signed helper (`Contents/Helpers/rac`) relays stdio to the socket,
    giving one-line setup: `claude mcp add rac --
    "/Applications/rac.app/Contents/Helpers/rac" mcp` (and `codex mcp
    add`); settings shows both lines with copy buttons. Also shell verbs
    (`rac snapshot`, `rac click e12`, `rac tabs`) and a never-stale thin
    skill stub (`rac skill`), installed only on user click.
    **M (1–2 weeks); skill/CLI M.**
15. **Per-client consent, scope, visibility:** first connect shows a card
    (untrusted `clientInfo` + peer identity where macOS can tell it); the
    user picks the client's permission level; the client works only in
    **its own tab group** (Playwright extension pattern: one client per tab;
    drag tabs to grant/revoke); ring/pill/Stop and guard as today; one
    controller turn per client. **L (2–4 weeks) — the main architecture
    item.**
16. **MCP hygiene:** `destructiveHint`/`openWorldHint`; spec 2026-07-28; a
    `core` tool profile. **S.**

## What rac should avoid

- **Telemetry on by default** — browser-use, DevTools MCP (CrUX URLs),
  Nanobrowser all ship it. Breaks rac's first rule.
- **Sending page trees or URLs to a vendor** (Stagehand cache, DevTools CrUX).
- **Arbitrary page script / "code mode" on the logged-in profile** —
  Playwright's default `browser_run_code_unsafe` ("RCE-equivalent") and
  Browser Harness's agent-written Python over raw CDP route around every rac
  guard. If rac offers scripts, use a throwaway profile (INFERENCE).
- **Safety behind flags nobody sets** (agent-browser). Keep protections on
  by default, in the user's real profile.
- **Trusting the MCP client to ask** — users pre-approve tools, then no
  prompt appears (INFERENCE). The browser holds the yes.
- **Consent a script can click** (Browser Harness osascript-clicks Chrome's
  sheet). Reject synthetic presses in rac cards (INFERENCE).
- **Page-visible agent markers and endless motion** — ♞ title prefix is
  readable by pages (via `document.title`); Nanobrowser's border repaints
  forever, in page DOM. Keep rac's UI-side ring/pill.
- **Copying the user's Chrome profile to a temp dir** (agent-browser
  `--profile Default`) — duplicate cookies outside browser control.
- **Huge default tool lists** — Playwright 25/72, DevTools ~60. Small core +
  opt-in groups.
- **Relying on injection detection** — BrowseSafe++: 78.79% avg success for
  adaptive rewrites. Structural rules first.
- **Built-in assistant as the only path to outside agents** — Stagehand
  deleted its agent; developers want tools (FACT + CLAIM). rac's assistant
  stays optional.

## Caveats

- All token/cost figures are vendor-run or third-party and unreproduced
  (Browser Harness eval, Slack-via-TestMu, the "6,600-token toolset
  overhead", Anthropic's "below 0.08%", agent-browser's ~7 MB vs ~140 MB
  RSS); the matched eval ran 100 of 200 tasks, one run each, Codex only,
  one shared cloud browser.
- The two CDP doors rest on confirmed code but are INFERENCE until someone
  launches rac; release-build dialog wording (dev trees rename `Helium` →
  `rac`) and incognito exposure were not checked.
- The maintainer's build tree predates `patches/rac/agent/13…17`; guard-level
  claims come from those patch files, not the tree (FACT).
- Chromium 154's `WebMCP` feature is experimental; whether Helium's flags
  leave it reachable was not checked.
- `claude mcp add` / `codex mcp add` syntax comes from vendor docs, not runs.
- Peer identity on the socket is unresolved (macOS checks will often name
  rac's own helper, not the real client). Same-user is the real boundary;
  consent + scope carry the rest. Open maintainer choices: concurrency model
  (turn per client vs shared), where the "outside agents" setting lives,
  whether it needs AI on, and whether outside clients default to
  `ask`/`careful` until evals exist.

## Where to look in the full dossier

`plans/research/agent-stacks.md` (607 lines); clones read at listed commits
under `/tmp/rac-overhaul/src/`; nothing installed or run. Snapshot + features
21–35, 39–117; page representation, tools, refs 227–282; reliability tricks
284–297; token budgets + rac delta 299–323; multi-tab, session reuse, CDP
doors 325–337; safety table + Nanobrowser gate 339–352; injection, install
paths, evals, Anthropic contract 354–387; motion 131–133; storage 198–207;
strengths/weaknesses 404–439; ranked recommendations 441–515 (avoid 496–508);
open questions 510–524; fact-check log (33 checked, 9 corrected) 565–605.
