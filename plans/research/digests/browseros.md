# BrowserOS — planning digest

Source: `plans/research/browseros.md` (2026-10-25; `browseros-ai/BrowserOS`
at `9335ee7`, stale `BrowserOS-agent` mirror at `e886782`, GitHub API, docs;
nothing built or run). Its Verification section (43 items) is authoritative.
Tags: **FACT** primary source, **CLAIM** self-report, **INFERENCE** reasoning.

## In plain English

BrowserOS is an open-source Chromium browser from a small YC startup. One
codebase ships two apps: a normal browser with an AI side panel, and neo, a
browser only for AI agents such as Claude Code. The AI is not compiled in. It
runs in a separate helper that starts with the browser and steers it through
Chrome's debugging connection, so it can update daily. That helper always
runs, sends usage data with no off switch, opens unauthenticated local ports,
and one listens on the whole network. For rac, take the one-click Connect
page, labelled agent tabs, a local activity log, hand-back, and credentials by
reference.

## Key facts

### Project, licence, numbers

- BrowserOS (human browser) and neo (agent-only browser) share one monorepo;
  neo is driven over MCP by Claude Code, Codex, Cursor and others. FACT
  (`README.md`).
- Chromium **155.0.8059.26**, base `16c3e55`; not ungoogled (only five Windows
  series patches, four build fixes plus
  `windows-disable-download-warning-prompt.patch`); README stale at 151. FACT.
- **AGPL-3.0**; the CLA grants a right to "sublicense, and/or sell"
  (`CLA.md:15`); the copyright line is in `README.md:233`, not `LICENSE`.
  FACT. INFERENCE: relicense or dual-license is possible.
- **14,095 stars, 1,510 forks, 100 open issues+PRs**; created 2025-05-18;
  4,155 commits; v0.1.0 on 2025-06-24 as Nxtscape. FACT.
- 53 releases v0.1.0–v0.51.0 (2026-10-05), 291 total; 2026 gaps of 2 days–7
  weeks plus **12 weeks 2026-03-21→06-17**; neo 7 releases (first `0.48.1` on
  2026-07-22, latest 0.51.2.4 on 2026-10-24); **15 server + 14 extension
  releases in the 30 days to 2026-10-25**. FACT.
- YC S24, team 4 (CLAIM); free, bring your own key; "Ultrafast" waitlist A/B
  tests **$9 vs $19/month** (CLAIM).
- DMG 203/382/165 MB; sidecar zip 53 MB; **421 patch files** (277 edit: 618
  hunks, +7,835/−401; 144 add: 20,628 lines); ~340,000 lines TS+Rust. FACT.

### Process model and engine integration

- Patched Chromium + a **supervised sidecar** + a bundled WXT/React extension;
  the sidecar steers via **loopback CDP** plus extra domains. FACT.
- The manager starts **unconditionally**: CDP `127.0.0.1:9100` (neo 9110);
  proxy `0.0.0.0:9000/9001` (neo 9010/9011) drops non-loopback peers; sidecar.
  Domains: `Browser.*`, `History.*`, `Bookmarks.*`, `Autofill.*` credentials.
  FACT.
- BrowserOS sidecar: Bun/Hono `0.0.0.0:9200`, `ToolLoopAgent`, SQLite, OAuth,
  Klavis, ACP via `npx`, filesystem tools. neo: Rust axum/rmcp/sea-orm/QuickJS,
  127.0.0.1 only, cockpit API, audit, rrweb, captcha. FACT.
- Supervision: 30 s health, 5 s process, 30 s grace; **3 strikes** switch
  downloaded↔bundled; reset after 30 s; failed cycle waits 30 s; `server.lock`.
  FACT.
- Sidecar OTA: **15 min**, ≤**200 MB**, Ed25519, **2** versions, hot-swap on
  `can_update` (neo has no check); extensions via `cdn.browseros.com`; browser
  via Sparkle. FACT.
- **No AI-off:** `--disable-browseros-server` stops sidecar/proxy but CDP opens
  first; `StopCDPServer()` is never called; only `--remote-debugging-port`
  avoids it (and opens Chromium's own). FACT. INFERENCE: a ~50 MB process, a
  Bun runtime, and an open port on every launch.
- Patches: a cumulative per-file store (not quilt), **39 features** in
  `.features.yaml`; PR #2805 says 384, count 421. FACT.
- `bpatch` (Rust) writes only changed files and **keeps mtimes**; `extract`,
  `annotate`, and agent-drivable `git merge-tree` base bumps. FACT.
- `bos_build` (Python/uv) plan with secret preflight; one `browseros_product`
  flag switches bundle ID, data dir, ports, appcasts, PostHog key, extension.
  FACT.
- Footprint: 289 diffs under `chrome/browser`, 26 `chrome/utility`, 14
  password-manager; rac ~217 files / ~871 hunks. FACT.

### UI and motion

- BrowserOS frame is **stock Chrome**: native vertical tabs default since
  v0.42, toolbar pins, agent side panel; design lives in web pages.
  FACT/INFERENCE.
- BrowserOS UI: shadcn/Radix, Tailwind, Geist; orange
  `oklch(0.646 0.222 41.116)` light / `oklch(0.705 0.213 47.604)` dark;
  glow/confetti `#FB6618`. FACT.
- neo: Base UI/base-vega, Tailwind v4; Signal Blue `#0254ec` the only
  saturated colour, ink `#393f49`, hairlines `#cbd5e1`, cobalt `#0043cd`, dark
  `#1b1e1e`/`#5290ff`; Schibsted Grotesk, Newsreader italic, JetBrains Mono;
  radii 4/6/8/12/16/20 + pill + 9 px; mostly flat, a little frosted glass.
  INFERENCE: editorial dashboard, nearer Linear/Vercel than Arc/Dia.
- Motion: `fade-up` 0.4 s `cubic-bezier(0.2,0.7,0.3,1)`; `fade-in` 0.35 s
  ease; demo rise 0.36 s; bounce 0.8 s `cubic-bezier(0.3,0.1,0.3,1)`; caret
  1.05 s `steps(1)`; LIVE dot 1.4 s infinite, opacity 1→0.35; reduced motion
  0.01 ms once. Glow: inset orange `box-shadow` **3 s infinite at 60%
  opacity**, fade-in 420 ms `cubic-bezier(0.22,1,0.36,1)`. Confetti 80+80, 60
  at 150 ms, 40+40 at 350 ms (**300**), gravity 1.2, decay 0.94, 200 ticks.
  Springs `damping 25, stiffness 300`; neo menus' `animate-none!` likely
  cancels their fade/zoom/slide (INFERENCE). Composer focus 150 ms; message
  actions 0.2 s. FACT.

### Storage, telemetry, network

- Web data in the Chromium profile (usual SQLite/LevelDB, Keychain-backed
  password/cookie encryption). FACT.
- `~/.browseros/db/browseros.sqlite` (Drizzle, WAL, 15 migrations):
  **plaintext** provider API keys, AWS secrets, headers, and `oauth_tokens`;
  plus conversations, jobs, ACP agents. Issue #1033 closed "not planned". FACT.
- `~/.browseros/sessions/` deleted after **30 days**; `tool-output/`
  0700/0600; `server.json`; `agents/acp-workspace/`; `versions/` 2 zips,
  Ed25519. FACT.
- neo `~/.browserclaw/browserclaw.sqlite` (sea-orm/sqlx): audit, tasks,
  sessions, tab claims; args redacted; no encryption. Screenshots one
  JPEG/step; rrweb replays in `~/.browserclaw/replays/` + DB. FACT.
- Replay masks only password, one-time-code, `cc-*`; **ordinary input is
  readable**. 7-day retention for claimed tabs; unclaimed deleted **1 h after
  the last event**. The recorder runs on `<all_urls>` at `document_start`
  despite docs saying otherwise. FACT.
- `analytics.json` `{distinctId, enabled}`, **consent on by default**;
  `jevToken` in settings; **no Keychain/OS store for AI secrets**. FACT.
- Telemetry: native PostHog events with the install ID as `distinct_id`, **no
  opt-out**; BrowserOS sidecar/Sentry; extension `autocapture` +
  `capture_pageview` + session replay. neo server toggle **on by default**
  sends versions, OS, task category, and an agent `task_summary` (≤200 chars),
  with its UUID aliased to Chromium's install ID; cockpit replays **20%** of
  consenting sessions. FACT. INFERENCE: pseudonymous.
- Network: `cdn.browseros.com` feeds (macOS appcast URLs are plain `http://`);
  `llm.browseros.com/klavis` opens a "Strata" session at **every sidecar
  start**; PostHog, Sentry, providers, OAuth, `npx` ACP adapters;
  `api.typesafe.ai`, CapSolver, 2Captcha with keys. Sync removed in v0.51.0.
  FACT.

### Agents and safety

- Where: BrowserOS `/chat` → Bun `ToolLoopAgent`, **100 steps**, compaction,
  own MCP over loopback with a per-conversation lease; ACP coding agents can
  replace the model. neo has **no agent**; the outside agent calls neo's MCP,
  the Rust server executes against CDP, records, and streams to the cockpit.
  FACT.
- Page: accessibility tree as indented text, stable `[ref=eN]`, iframes
  stitched, cursor-pointer nodes; Full/Interactive + depth. `act` returns a
  diff. Settle: 150 ms nav window, MutationObserver stable 100 ms, default
  **600 ms** (50 ms is stale), decision loop 1,500 ms. Results >**5,000 chars**
  go to a file. FACT.
- Tools: BrowserOS **17** browser + **7** Cowork file + Klavis + 2 nudge. neo
  **25 default, up to 27**: 20 catalog incl. `browser_profiles`,
  `browser_target`, `credentials`; `name_session`, `save_skill`,
  `mark_skill_run`; a human-help pair; `pursue`/`solve_captcha` with keys.
  FACT.
- `run`: neo QuickJS **64 MB, 512 KB stack, 30 s**, no
  fetch/require/process/DOM, page access via `page.evaluate` (still network —
  INFERENCE). BrowserOS `run` is an **unsandboxed `new AsyncFunction`**. FACT.
- Credentials: `list|add|fill` via a custom `Autofill` CDP domain; the browser
  matches and fills, never submits; "passwords never appear in results" only
  when filling by `credentialId`, since `add`/`fill` accept raw credentials.
  MCP annotations on every tool. FACT.
- Providers: 13 types incl. Anthropic, OpenAI, Google, OpenRouter, Azure,
  Bedrock, Moonshot, Ollama, LM Studio, plus ChatGPT/Copilot/Qwen
  subscriptions; any model ID. ChatGPT reuses Codex CLI client
  `app_EMoamEEZ73f0CkXaXp7hrann` (INFERENCE). Local context warning ~15,000
  tokens; `OLLAMA_CONTEXT_LENGTH=20000`. neo has none. FACT.
- Permissions: BrowserOS has **no runtime approval**; confirmation appears
  only in the Klavis connector prompt; Chat mode = read-only tools; coding
  agents `approve-all` → `bypassPermissions`/`agent-full-access`; Cowork shell
  unrestricted; 100 steps. neo relies on the caller + `destructiveHint`, no
  server step cap, audit 7 days, human hand-off default, refuses
  `javascript:`/`file:`/`data:`, tab ownership labels not barriers. FACT.
- Injection: per-call nonce fences (16 hex) around page text and
  `run`/`evaluate` output; prompt rules; conformance tests with hostile
  fixtures, **not model evals**; #389 fixed; weekly eval app deleted July
  2026; no injection eval. FACT.
- Outside: MCP streamable HTTP **no token**; `/mcp`, `/status`, `/klavis`,
  `/oauth`, `/system/shutdown` on `0.0.0.0:9200` have no peer check;
  browser-origin requests refused; CDP 9100/9110 open to any local process
  (undoes Chrome 136 hardening — INFERENCE); proxy always binds `0.0.0.0`;
  issue #2424. FACT.
- Connect: `harness-integrations` writes 7 agents' configs (Claude Code,
  Codex, Cursor, OpenCode, Antigravity, VS Code, Zed) + a `SKILL.md`; Claude
  Desktop `.mcpb`, Codex plugin. FACT.

### Build, CI, release, upstream

- CI: 30 workflows, ~9,028 lines; PRs run lint/typecheck/tests, Python tests,
  codegen drift, Claude review, title check, CLA bot; **no Chromium compile or
  unit tests on PRs**. FACT.
- Builders: one self-hosted Mac Mini (`timeout-minutes: 1200`) with a warm
  checkout + APFS copy-on-write clone per build; Linux/Windows on WarpBuild
  Azure BYOC (32 vCPU, 128 GiB) as self-hosted to escape the 6-hour cap; **no
  compiler cache**, cold 4–7 h, warm 3–6 h. FACT.
- Signing: Developer ID + `notarytool`, temp keychain; Team ID `8YMKWU47S5`;
  `com.browseros.BrowserOS`, `com.browseros.BrowserClaw`; optional
  provisioning for passkeys; Windows SSL.com eSigner. FACT.
- Updates: Sparkle 2, full 382 MB DMG, **no deltas**, EdDSA, silent staged
  installs; sidecar appcast; CRX feed. Staged publish: R2 + draft, human
  `release publish`, feed backup, downgrade guard, idempotent component
  versions. FACT.
- Upstream: bumps 142 (2025-12-03), 145, 146, 148, 151, 155 (2026-10-02);
  majors skipped; now 155 vs Chrome 156. #2805: 205 files (+1,468/−2,173),
  same day, macOS arm64 only, dropped MV2. FACT.
- Tests: 370 TS files, **1,661 Rust tests** (659 `#[test]`, 1,002
  `#[tokio::test]`), 11 Chromium `_unittest.cc` not run; claw-mcp nightly;
  `oasdiff`. FACT.
- Removed: MV2/uBlock, accounts/sync/hosted model, skills/SOUL.md/memory,
  Workflows, Go CLI (2026-10-13). FACT.
- Import: Chrome only, reads the "Chrome Safe Storage" Keychain item; no
  Arc/Brave/Edge/Safari. FACT.
- GN: official, `symbol_level=0`, no PGO, proprietary codecs, Widevine, HEVC,
  Sparkle, no Google keys; field-trial *testing* config off only; Safe
  Browsing default; browser sign-in off. FACT.

## What rac should take

Costs: **S** = 1–3 days, **M** = 1–2 weeks, **L** = 3+ weeks. **Licence:**
BrowserOS is AGPL-3.0. GPL-3.0 §13 allows combining, but AGPL's network-use
terms then apply "to the combination as such" (FACT, rac `LICENSE:552-561`).
INFERENCE: treat everything as ideas to re-implement, not code to copy.

1. **Agent access switch + Connect page — M.** A page listing Claude Code,
   Codex, Cursor, OpenCode, VS Code, Zed; one click writes the MCP config and
   a skill file, with a copy-endpoint fallback. Separate from the built-in
   assistant and free when off. Keep rac's transport: Unix socket/loopback, a
   per-agent secret revocable at pairing, per-agent `ask`/`careful`/`auto`.
   Source: `harness-integrations/src/catalog.rs`.
2. **Agent-owned tabs — S–M.** A group named `<agent>/<task>`; the agent is
   told which tabs are the user's and clones one instead of navigating it;
   session end closes the group. In rac: a temporary "Agent" folder per space.
   Source: `prompt.rs` `SHARED_BROWSER_GUIDANCE`.
3. **Local activity log — M.** Every call with redacted args, page, duration,
   and a step screenshot; Running-now card with Watch and Stop; 7 days; on
   disk. No DOM replay first. Later rrweb (**L**) only for agent tabs, only
   during a run, with all input masked. Source: `audit.rs`.
4. **Hand control to me — S–M.** `request_human_help` plus a slim bar on the
   blocked tab ("Sign in, then hand back"). Push from the browser; never poll
   every page. Source: `takeover.content.ts`.
5. **Credentials by reference — M.** List saved logins for the site and fill
   by ID; the password never enters the model, log, or result; never
   auto-submit; confirm at `careful`/`ask`. Source: `credentials.rs:18`.
6. **Tool-surface hygiene — S.** Nonce fences including structured output;
   MCP annotations; diff after `act`; settled readiness; refuse
   `javascript:`/`file:`/`data:`. Check what rac has.
7. **Conformance suite — M.** Real browser, hostile fixtures, nightly; the
   base for injection evals. Source: `contracts/claw-mcp/`.
8. **Warm patch tooling — M.** A `bpatch`-style apply that keeps mtimes, so
   `he unmerge`/`he merge` stop triggering big rebuilds; a per-feature file
   registry. Re-implement, don't copy AGPL.
9. **Self-hosted Mac builder — M + hardware.** Warm checkout, APFS clones,
   long timeouts, staged publish. Fixes rac's 6-hour-phase CI problem.
10. **Logged-in import — M.** Arc import copies cookies/passwords via the
    source browser's "Safe Storage" Keychain key (one prompt). Fresh code from
    Chromium's importer.
11. **Sandboxed scripts, later — L.** A QuickJS `run` with caps, no
    network/files, page access via guarded tools; per-site helpers. After the
    safety work.
12. **Supervised helper, optional — L.** Agent runtime in a helper inside the
    bundle; copy supervision but not the 15-minute feed; ship it with rac's
    Sparkle update.

## What rac should avoid

1. **Agent infrastructure starting when AI is off** — no sidecar, port, update
   check, or connector session unless enabled.
2. **An open debugging port or unauthenticated MCP endpoint** — per-agent
   secret, private socket, CDP closed, never `0.0.0.0`.
3. **Approve-all for coding agents, unsandboxed scripts, an unrestricted
   shell** — no `bypassPermissions`; no `npx -y` adapters at run time.
4. **Telemetry without a switch, autocapture, or session replay** — and
   privacy copy the code doesn't back.
5. **Plaintext secrets on disk** — keys and OAuth tokens belong in the
   Keychain.
6. **Borrowing another app's OAuth client** (the Codex CLI ID).
7. **Recording every page** "because attribution happens later", and polling
   content scripts on every page.
8. **Product churn** — shipping memory, skills, sync, workflows, and a CLI,
   then deleting each within months.
9. **Animations that run forever** (the infinite glow) and celebratory
   confetti.
10. **Dropping a feature during an upstream bump without telling users** (MV2),
    and skipping Chromium majors.
11. **Third-party CAPTCHA solving or a third-party "decision model"** in the
    default product.
12. **A 30-workflow, 9,000-line release system** — take the ideas, not the
    machinery.

## Caveats

- **Nothing was run.** Memory, CPU, startup, and battery cost of the sidecar,
  CDP port, rrweb on every page, and the 3 s poll are unmeasured.
- Unverified: whether production builds ship a PostHog key (the release
  workflow passes `VITE_PUBLIC_POSTHOG_KEY`, so probably yes); what
  `llm.browseros.com/klavis` logs; whether neo's toggle also stops native
  PostHog events; whether 155.0.8059.26 is stable or early; whether the Codex
  CLI OAuth client ID is permitted for third parties; the token-savings
  claims; real team size and funding; whether Chromium's M155 vertical tabs
  change rac's Helium layout; whether neo's "recorder never loads in user
  tabs" was ever true.
- Verification found **~30 of 43** claims correct; errors were counts, people,
  and security details. Three matter most: the sidecar listens on all
  interfaces with no peer check on `/mcp`; no flag turns off the debugging
  port; replays keep ordinary typed text readable. All strengthen the avoid
  list, not the recommendations.
- "Agent updates daily" is not free: it costs an always-running helper, an OTA
  channel, and a 15-minute update check. rac's signed Sparkle update is the
  compatible substitute.
- The AGPL/GPL point is a licensing analysis, not legal advice.

## Where to look in the full dossier

`plans/research/browseros.md` — snapshot 36–50; features 52–167; UI 169–252;
motion table 237–252; feel-bad 273–285; architecture 287–361; engine
integration 363–391; evolution 421–443; **storage table** 445–475; telemetry
477–500, telemetry 501–527, network 529–536; agents: where 539–556, page
representation 558–582, tools 584–627,
providers 629–643, permissions 645–659, **injection** 661–685, outside access
687–725; CI 760–789; updates 802–817; tests 826–837; upstream 839–852;
strengths/weaknesses 854–921; **ranked takes** 922–1005; avoid 1007–1038; open
questions 1040–1063; sources 1065–1130; **Verification (43 items)** 1132–1197.
