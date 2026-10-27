# Matrix: architecture, backend, and local storage

Built 2026-10-27 from the 18 digests and the dossiers in `plans/research/`. Cells are short. Unmarked cells are facts from the digests. `(inf)` = inference by a dossier author. `(claim)` = self-report, unverified. `?` = unknown. `n/a` = does not apply. T3 Code and Pomerado are not browsers, so browser rows say so.

## In plain English

rac is one program today. It has no server, and an outside agent such as Claude Code cannot drive it. T3 Code and Aside both run a separate local program: T3 a Node server, Aside a Node daemon that is always on. They pay in memory, open ports, and extra signing and updating. Cra, Zen, Nook, and Ardia show the cheaper pattern: no local server at all.

This file compares 14 products, then offers five ways for rac to get a local "core". My pick: keep the core inside the browser, and add one opt-in door for outside agents (a small signed command plus a private socket). Store agent history in a small SQLite file with a retention limit. Add a Rust helper only if routines that run while rac is closed become a priority.

## Matrix A: the shape of the system

| | rac today | Helium | Arc | Dia | Zen | Ardia | Cra | Nook | Ora | BrowserOS | Aside | ego(lite) | T3 Code | Pomerado |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Engine and embedding | Chromium 154 patch fork via Helium 0.18.2.1; ~180 quilt patches | Chromium 156 patch stack (0.20.1.1); 346 core + 23 macOS patches | Own Chromium wrapped in internal SDK "ADK"; closed | Same ADK base; framework "ArcCore"; M156 | Firefox/Gecko 158; patches on source tarball | Chromium 155 + Helium 0.19.4 patch fork; Chrome's browser process is the app | CEF 156.0.14, Chrome-style runtime; 5 own patches | System WKWebView; no patches | System WKWebView; no patches | Chromium 155 patch fork (421 patch files); not ungoogled | Chromium 154.0.8037.100 C++ fork; not ungoogled; closed | Closed Chromium 156 fork plus embedded Node 24 | n/a. Electron 44.9.3 (Chromium 152) shell; panel uses `<webview>` and `chrome-headless-shell` 156 | n/a. Playwright-launched own Chromium |
| UI layer | C++ Views (67 files in `ui/views/rac`); WebUI TS (`chrome://rac-ai`); Lit/Polymer settings | C++ Views; WebUI TS/Lit; onboarding Svelte 5 | SwiftUI + TCA | AppKit-heavy (dropped TCA/SwiftUI) | HTML/CSS/privileged JS (Firefox chrome doc) | React Native (Expo) inside Chrome's loop | AppKit + SwiftUI; each tab a frameless Chrome window | SwiftUI/AppKit | SwiftUI | Stock Chrome frame + React MV3 extension + web pages | Native Views chrome; React MV3 for NTP/side panel; Swift helpers | ? Closed native UI; overlay and bar | React web UI (shadcn, Tailwind) in Electron; RN mobile | none (CLI/MCP only) |
| Process model | Chromium multi-process; AI/agent on UI thread; MCP on IO thread; ACP agents and `nc -U` as children; no rac daemon | Unchanged Chromium; importers in utility process | ? (in-process framework, inf) | ? Page reading moved out of process (1.34.1) | Parent runs chrome JS; site-isolated content processes | One browser process runs Chrome and RN; one `Browser` per profile with no BrowserView | Swift app plus 5 CEF helper apps; `no_sandbox=true` | One app process plus WebKit processes; Sparkle XPC | One app process; each window builds its own state | Chromium plus supervised sidecar plus extension; CDP always open | Aside.app plus Daemon.app plus CLI.app plus Updater.app | App plus utility process `ego.mojom.NodeService` (embedded Node); tray-resident | Node server; desktop spawns it as Electron-as-Node; web/mobile are clients | Node 24 MCP stdio server per coding agent plus its own Chromium |
| Sidecar or daemon: language, lifecycle | None | None (remote `helium-services` only) | None known | None known | None | None. `ardia` CLI is Python 3.13 + pydoll, outside the bundle, off by default | None | None (stdio MCP clients and native-messaging hosts are children) | None | Bun/Hono (TS) sidecar; neo is Rust axum. Starts every launch, no off switch; 30 s health checks, 3-strike restart | Node 26.5 SEA daemon (159 MB, LSUIElement), always on; Rust `aside-memory` downloaded | No daemon. Helper `ego-browser` inside bundle; app stays in tray after last window closes | Node 26 server: `t3 serve`, launchd service, or desktop child; warm sessions 30 min idle | Per-session Node stdio; saved integrations run as their own MCP servers |
| IPC transport and auth | Per-run Unix socket in profile (0700 dir, 0600 socket), same-UID check only, no secret; `nc -U` bridge shows path in `ps` | n/a. AppleScript for outside control | ? | ? | n/a. CLI only `--space`, `--blank-window` | CDP over WebSocket; random per-start token in 0600 `ArdiaControl.json`; Origin refused | `cra://` scheme; 3 safe external verbs; private CDP pipe for extensions | HTTP `127.0.0.1:47823/mcp`; 0600 bearer token; non-local Origin gets 403 | n/a | CDP `127.0.0.1:9100` no auth; proxy `0.0.0.0:9000`; sidecar `0.0.0.0:9200` no token or peer check | HTTP+WS `127.0.0.1:21420`; Secure Enclave signed challenge then bearer; patched CDP `localhost:45103` | ProcessSingleton Unix socket under `/var/folders`; same OS user only (inf); in-process CDP binding, no port | WS `127.0.0.1:3773` (LAN opt-in); bootstrap token on fd 3; per-RPC scopes; OAuth 2.1 + PKCE for outside MCP | stdio |
| RPC protocol | MCP (rev 2024-11-05 to 2025-11-25) for the launched agent; ACP v1 to agents; Mojo and `chrome.send` inside | Mojo; Apple Events | ? | ? | Firefox actors (internal) | CDP (70-method allowlist); JS-Swift-ObjC++ bridge | `cra://`; CDP pipe | MCP streamable HTTP (31 tools); MCP client | n/a | CDP plus MCP streamable HTTP; ACP; HTTP `/chat` | tRPC over HTTP/WS; CDP; MCP stdio (4 tools) | Scripts on stdin over socket; CDP in-process | Effect RPC over WebSocket (203 methods, 31 streams); MCP (84 tools) | MCP stdio (`mint`, `get_job`, `provide_input`, `cancel_job`) |
| Exposed to outside agents | Nothing. MCP exists only for rac's launched agent during a run; AI off removes it | AppleScript dictionary (tabs, URL, execute JS) plus `select` | Nothing | Nothing | Nothing | `ardia` CLI over CDP, skill install; off by default; no per-site rules | 3 `cra://` verbs (commandbar, dismiss, open) | DevMCP 31 tools, hidden Agent space; needs Developer Mode and Browser Control | Nothing | MCP (neo 25-27 tools), CDP; Connect page writes 7 agents' configs | `aside` CLI; `aside mcp` (exec, repl, memory_search, browser_profiles); skill install | `ego-browser nodejs` scripts via SDK; self-printing skill | `/mcp` 84 tools; `t3 thread` CLI | Minted integrations as MCP servers |

## Matrix B: data

| | rac today | Helium | Arc | Dia | Zen | Ardia | Cra | Nook | Ora | BrowserOS | Aside | ego(lite) | T3 Code | Pomerado |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Storage engine | Chromium prefs JSON plus own JSON files; no rac SQLite | Chromium formats (prefs JSON, SQLite, LevelDB) | Chromium profile plus `StorableSidebar.json`; Firebase | Chromium profile plus SQLCipher `tabs.db` | `zen-sessions.jsonlz4` (LZ4 JSON) | Chrome SQLite/JSON plus app JSON (800 ms debounce) | Plain JSON files via one `JSONStore<T>` | JSON structure file; SwiftData SQLite; FTS5 page-text DB | SwiftData SQLite; UserDefaults; Keychain | Chromium profile; `browseros.sqlite` (Drizzle, WAL); neo `browserclaw.sqlite` | Chromium profile; per-account `state.db` (SQLite WAL); JSON; Markdown memory; encrypted vault SQLite | ? Chromium profile; ref ledger in `~/.ego-browser/state` (format ?) | One SQLite `statev2.sqlite` (WAL): event store, ~18 projections, FTS5 | Folder of source files plus `pomerado.json`; no DB |
| File locations | `~/Library/Application Support/me.kainoa.rac` (dev `.dev`): prefs, `<profile>/rac spaces`, `<profile>/rac_ai_history.json` (plaintext), MCP socket in profile | `…/net.imput.helium` | `…/Arc/User Data`, `…/Arc/StorableSidebar.json` | `…/Dia/User Data` | `…/zen/Profiles/<id>/` (claim) | `…/com.ardia.browser/Chromium/`; iCloud `Ardia Sync/` | `…/Application Support/Cra/*.json` | `…/com.gstudios.nook/Tabs/`, `~/Library/WebKit/com.gstudios.nook` | `…/Ora/OraData.sqlite` (sandbox container) | `~/.browseros/db/`, `~/.browserclaw/` | `…/Application Support/Aside/`; `~/.aside/u/<accountId>/` | `~/.ego-browser/state`; `…/Citro Labs/` | `~/.t3/userdata/`; `~/.t3/worktrees/` | User-chosen `--root` folder |
| Schema style | Not event-sourced; dictionary prefs; versioned spaces file (`kVersion=1`) | Prefs; `helium.*` keys | Flat item dictionary with child lists | ? | Session JSON; sync has 6 record kinds | JSON; sealed sync records, per-record last-writer-wins (hybrid logical clock) | Flat item dictionary; `tab/folder/container/split` | JSON with `formatVersion`, 30-day tombstones, fractional keys | Row per URL per space | Relational; not event-sourced | Relational sessions/turns plus `messages.jsonl`; not event-sourced | ? | Event-sourced with outbox; 45 event types, 68 commands | n/a |
| Migrations | `kVersion=1` on spaces file; others ? | Chromium prefs migrations | ? | ? | 1.18 moved sessions out of `places.sqlite`; loss reports followed | ? | Corrupt file moved aside; version scheme ? | `formatVersion`; DB mismatch backs up then resets | SwiftData; failure handler deletes wrong path, likely crash loop | Drizzle, 15 migrations | ? | ? | 69 migrations; DB snapshot before server update, rollback if trial fails | Recipes versioned (sign-in at v8); breaking changes daily |
| Sync: protocol, E2E, provider | None | Experimental "private vault": AEAD immutable commits via `syncVaultProvider` extension (17 patches, off) | Firebase "Arc Sync", encrypted (claim); Arc ends 2026-12-22 | E2E: device seed, HKDF to AES-256-GCM and Ed25519, 24-word phrase, SPAKE pairing; Dia servers | Custom Firefox Sync engine "Spaces" v3; Mozilla account; opt-in on stable | Folder sync (iCloud Drive default): sealed `.nns`, AES-256-GCM, BIP-39, no server; two-Mac test never run | None | iCloud `CKSyncEngine`, branch only | None (passwords flagged iCloud-synchronizable) | Removed in v0.51.0 | Chromium sync to `browser-sync.asidehq.com`, daemon-held passphrase (Nigori, inf); experimental plaintext cookie snapshot | None known | None for data; remote access via T3 Connect (Clerk, Cloudflare tunnel) | None (Cloud is a paid separate product) |
| Import formats | None. Arc import not built | `ArcSidebarImporter` (`StorableSidebar.json`) plus Chromium importers | Export Data (format unpublished) | Imports Arc (spaces become profiles) | Arc `StorableSidebar.json`; Chrome importer | Chrome, Edge, Brave, Opera, Vivaldi, Helium, Island, Dia, Arc, Firefox, Zen, Safari, bookmark HTML, password CSV | Arc (sidebar, favicons, archive, windows, link routing), Dia, Chromium browsers | Arc (no passwords, cookies, history), Safari, Dia | Arc `StorableSidebar.json` (likely fails under sandbox, inf) | Chrome only | Password managers and CSV; browser import incl. cookies; Arc spaces not | Imported sessions (cookies); format ? | Cookie import from 10 browsers (panel only) | n/a |
| Backup | `.bak`, atomic write, 1 s coalesce on spaces file; no dated backups | ? | ? | ? | 3-hour buckets, newest 20; previous-save copy; tries only 2 fallbacks | ? (sync folder doubles as copy) | One `.bak`; corrupt file moved aside | Daily dated folders kept 7 days; falls back to newest backup, else read-only | None | None; sessions pruned at 30 days | ? | ? | DB snapshot before server update only | n/a (folder is user-owned) |

## Matrix C: cost and risk

| | rac today | Helium | Arc | Dia | Zen | Ardia | Cra | Nook | Ora | BrowserOS | Aside | ego(lite) | T3 Code | Pomerado |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Idle memory and CPU | ? Unmeasured. AI off still builds idle `ActorKeyedService` objects (unmeasured) | Helpers 15.9-37.9 MB RSS each; no totals | ? | ? | ? GPU helper at 700% CPU in issue #14793 | 1 tab 290 MB (Helium 375); 20 tabs 1,183 MB (Helium 1,125) | ? | ? Global mouse monitor and forever glow repaint | 500 ms JS poll and mutation observer in every page | ? Sidecar always on (~50 MB, inf) | ? Daemon binary 159 MB; RSS ? | One idle agent Space ~40% GPU plus ~18% WindowServer (#476) | 323 MB after 22 h | ? |
| Startup cost | ? No benchmark exists | ? | ? | ? | ? | Tab switch 40 ms cut to 10-16 ms (Helium 8.5); launch ? | ? | First paint 2,147 to 607 ms (claim) | ? | ? Sidecar plus Klavis session at every start | ? | ? | ? Native modules kept off startup path | ? Node 24 cold |
| Patch surface on engine | ~870 hunks, ~217 files; 320 hunks in `ui/views`; agent: 21 files, 58 hunks | Core 346 patches (1,645 files); macOS 23 | ? (ADK avoids C++ UI) | ? | 264 patches, 868 hunks (+90 external), 287 files | 60 patches, 492 hunks, 205 files; 26 hunks in `ui/views`; 46 hooks | 5 patches, 11 hunks, 6 files; under CEF 118 patches, 1,044 hunks | 0 (WebKit); ~20 private selectors | 0 (WebKit) | 421 patch files; 277 edits, 618 hunks | ? ~48 `aside_*` files visible | ? Closed | n/a (Electron unpatched) | n/a |
| Engine update cadence | Never synced; 154 vs 156; Helium 6 releases ahead; 121/180 patches apply to 0.20.1.1 | Each Chromium major 2-4 days after stable (two-week train) | Chromium 155 in v1.169.0 (2026-10-15) | Weekly; M156 | ~1 release per 5.4 days; Firefox within days | 80 releases in 31 days; Helium 0.19.4.1 adopted, 0.20.1.1 not | CEF pin; 154 to 156 in one afternoon; manual engine build | With macOS only | With macOS; last release 2026-04-07 | Skips majors (155 vs 156); sidecar OTA every 15 min | ~7 builds a month; 14-30 days behind stable; components ~1 per 1.3 days | Weekly; Chromium 156 | ~27 merges and ~3 releases a day; Electron 2 majors behind | 0.x; breaking changes weekly |
| Sandboxing | Chromium sandbox; ACP agents: scrubbed env, own process group; no Seatbelt | Chromium sandbox | ? | ? | Firefox content processes (sandbox not checked) | Hardened runtime; `allow-jit` only for renderer and GPU helpers | None: `no_sandbox=true`, `USE_SANDBOX=OFF` | WebKit sandbox; app not sandboxed | App sandboxed | None for sidecar; `run` unsandboxed (BrowserOS) or QuickJS 64 MB (neo) | Seatbelt deny-default for bash; QuickJS-wasm REPL; Node binaries have JIT and library-validation exceptions | `NodeService` likely unsandboxed (inf) | `<webview>` `sandbox:true`; agents Full access by default | None ("not an OS sandbox") |
| Incidents and weak spots | `auto` exfiltration gap; two unguarded CDP doors (inf); plaintext chat history; dev flags ungated | Services terms silent on forks | CVE-2024-45489 (9.8, Boost sync rule) | CVE-2025-15032, CVE-2025-13132; content data on by default | Updater shipped without signature checks until 1.19.9b; 3 more GHSAs | Daily ping even with sharing off; no per-site rules; main-world script | Fixed in 0.1.11: public mock-keychain key; pages could call `cra://` | Token file is the approval; page-world JS | Camera/mic auto-granted; address-bar spoof (inf) | Plaintext keys; unauthenticated `0.0.0.0` ports; no telemetry opt-out | Allow-by-default; impersonates Claude Code; unencrypted cookie snapshot; relay allows `cli.replRun` | Raw CDP + Node egress can read cookies (#315); agent cleared user cookies (#303) | Plaintext secret files; analytics on; 40 GB DB; Full access default | Unsandboxed generated JS; page content to OpenAI |

## Options for a local rac core

Shared ground (from the digests): the browser keeps every permission decision. Every option routes outside-agent calls through one rac-owned contract that ends in `AgentController::HandleToolCall` and the guard. No option exposes raw CDP. The `auto`-level exfiltration gap is a policy gap, and no process model closes it. Sizes are inference unless noted.

### Option 1: In-browser core (KeyedService plus Mojo, no extra process)

**What it is.** A rac `KeyedService` per profile inside the browser process becomes the one place that owns browser actions (open tab, move to space, pin, archive, agent tools). The sidebar, command bar, shortcuts, built-in agent, and an outside-agent door all call it. The door is a long-lived opt-in Unix socket in the profile, plus a tiny signed `rac` command in `Contents/Helpers` that relays stdio to the socket (`claude mcp add rac -- …/rac mcp`). The relay holds no state and lives only as long as the agent's session. Agent history goes in Chromium's `sql::Database`. Spaces, pins, and favorites stay in prefs and JSON.

**Enables.**
- Outside-agent MCP and CLI (`rac mcp`, `rac skill`, `rac snapshot`), with a pairing card, per-agent level, and revoke list.
- One call table that generates MCP schemas and command bar rows.
- Agent history as one row per run and per tool call, with retention.
- Routines only while rac is running. Nothing runs when rac is closed. The CLI can launch rac hidden, as Obsidian, ego, and Yab do.
- Sync later via sealed files in a user folder, with no server.

**Cost against the non-negotiables.**
- Private: no new network surface; no port if the socket is used; Keychain key for history text. Strong.
- Never slower: a listener exists only while "Let other apps' agents use rac" is on; no extra process. Strong.
- AI off costs nothing: the door gets its own switch, off by default, independent of the AI switch, so outside agents work with the built-in assistant off. Strong.
- Cheap to update: more C++ in rac-owned files, but the Chromium symbols stay behind two adapter files. Medium. The existing MCP patch is 2,349 lines; reuse it.

**Notarization and launch.** One new signed part (the relay) listed in `chrome/installer/mac/signing/parts.py`, as Helium already does for Sparkle's `Autoupdate`. Build it as a small in-tree GN C++ target, so no new toolchain. Link into `~/.local/bin` on click (no admin prompt). Sandboxed agents cannot reach a Unix socket (ego #188). A parent-launch constraint cannot cover a relay run by Claude Code or Terminal. Loopback HTTP with OAuth and PKCE is needed only if `mcp login` flows require it.

**Patch surface.** Estimate: 5-10 new upstream hunks in 4-6 files (prefs registration, one `BUILD.gn`, factory registration, `parts.py`), mostly new files. Small.

**Resembles.** T3 Code Option A and C (a door plus "be a good MCP target"); Nook DevMCP; Crest's in-bundle stdio helper; Yab's `yab mcp`; the dossier's O1 and O7.

### Option 2: A Chromium utility process or service

**What it is.** The agent-side work (ACP client, outside-agent MCP parsing, history writes) runs in a Mojo service launched with `ServiceProcessHost::Launch<mojom::RacCore>()`. Chromium kills it when idle. A crash in agent parsing then cannot take the browser down. The browser process still owns the guard and the socket, because a service can only speak Mojo.

**Enables.**
- Crash isolation for the agent stack; a place to run parsing off the UI thread.
- Everything Option 1 does, since it still needs Option 1's door.
- It adds no new capability for outside agents or sync.

**Cost against the non-negotiables.**
- Private: same as Option 1. Strong.
- Never slower: a utility process costs 16-38 MB RSS while alive; idle handler can stop it. Medium.
- AI off costs nothing: launched on demand only. Strong.
- Cheap to update: extra mojom and service plumbing on top of Option 1, and spawning agents needs `kNoSandbox` (inf). Medium-weak.

**Notarization and launch.** None new. It reuses Chromium's already-signed utility helper. Nothing for the user to approve. Dies with the browser.

**Patch surface.** Estimate: Option 1 plus 8-15 hunks (mojom, service registration, sandbox type, `BUILD.gn`). Medium.

**Resembles.** ego(lite)'s `ego.mojom.NodeService` utility process; Helium's importers in the utility process; Atlas's Mojo split (much bigger). Dossier O2: only if agent parsing crashes.

### Option 3: A bundled helper daemon in Rust (or Swift), Unix socket plus token

**What it is.** A rac-owned executable at `rac.app/Contents/Helpers/rac-agentd`. The browser starts it lazily when outside agents, routines, or a warm agent are needed, and passes a bootstrap secret on an inherited file descriptor (T3 uses fd 3), never on the command line. It owns outside-agent MCP (`rmcp`), ACP agent processes, SQLite history, and schedules. Its socket is 0600 and checks the caller's signature through the audit token. It also doubles as the `rac` CLI. Every browser action still goes back to the browser's guard and cards. An optional launch agent (`SMAppService`) is the only way to run routines while rac is closed. Default: no launch agent.

**Enables.**
- Everything in Option 1, plus a warm agent (T3 keeps sessions 30 min; rac pays 15-25 s per message today), history, and local routines.
- Routines while rac is closed, only with the launch agent (a "Background Items Added" notice; needs approval).
- Fast iteration without rebuilding Chromium; a crash cannot take the browser down.
- Sync later via sealed files, run by the helper.

**Cost against the non-negotiables.**
- Private: loopback or socket only; keys from Keychain, never plaintext. Strong if built that way (BrowserOS and T3 are the cautionary cases).
- Never slower: Rust helper estimated 5-10 MB idle RSS, ~14 ms start (measured on existing Rust binaries, not a minimal server); zero when not launched. Medium-strong.
- AI off costs nothing: never launched when no feature needs it. Strong, if enforced.
- Cheap to update: the contract is narrow and stable; the helper does not rebase against Chromium every two weeks. But there is a second binary to build, sign, and test, and MCP and ACP revisions to track. Medium.

**Notarization and launch.** One `parts.py` entry, Hardened Runtime, secure timestamp. Rust, Go, and Swift sign like Helium's utility helper, with no JIT. A parent launch constraint (`--launch-constraint-parent`) can force "only rac.app may launch me" (enforced from macOS 13.3; unverified here). Files a helper writes get quarantined (`LSFileQuarantineEnabled`). Rust builds with cargo outside GN, because tokio, hyper, and axum are not in the Chromium tree. CI would build it in minutes in its own job. Swift would build outside GN too, gives Keychain, XPC, and Apple Foundation Models, but has only a community ACP library (MCP `swift-sdk` 0.12.1). Rust has official MCP and ACP crates, so Rust is preferred.

**Patch surface.** Estimate: the Option 1 hunks plus 2-4 for packaging and launch. The helper itself is 0 engine hunks.

**Resembles.** agent-browser (Rust CLI plus per-session daemon, 1 h idle exit); BrowserOS neo (Rust axum, but always on); T3 Code's fd-3 bootstrap; Zed's agent servers. Dossier O3 ("best long-term shape", L).

### Option 4: A Node or Bun sidecar, like T3 Code or Aside

**What it is.** The agent runtime and outside-agent server are written in TypeScript and shipped as a bundled single-file Node or Bun program. The browser starts it on demand and talks to it over HTTP or WebSocket on loopback or a Unix socket. The TypeScript SDKs for MCP and ACP are the official ones, and a web UI could share code with the assistant panel.

**Enables.**
- The same outside-agent door, history, and routines as Option 3, with the fastest development speed and the official MCP and ACP SDKs.
- Possible out-of-band updates of the agent layer, which is exactly what rac should not copy (BrowserOS's 15-minute feed).

**Cost against the non-negotiables.**
- Private: depends on discipline; T3 and BrowserOS both ended up with plaintext secrets, default telemetry, or open ports. Medium.
- Never slower: Bun runtime 63.6 MB, ~22.5 MB idle RSS, 7 ms start; Node 117-146 MB, 54-67 MB idle RSS, 35 ms start. T3's server held 323 MB after 22 h; Aside's daemon is a 159 MB binary; Raycast v2's Node backend is 350-450 MB at rest (claim). Weak when always on; acceptable only if lazy.
- AI off costs nothing: BrowserOS and Aside start theirs regardless. Needs strict lazy start. Medium.
- Cheap to update: a JavaScript runtime in the process that brokers browser tools is the least hardened process in the app. Node and npm dependencies churn. Weak.

**Notarization and launch.** Needs `allow-jit`, `allow-unsigned-executable-memory`, and `disable-library-validation` (measured on Claude Code and opencode, which are Bun). Aside's Node binaries carry the same exceptions. Never download runtimes at first use; bundle them. Quarantine on unpacked native modules can hang on Gatekeeper.

**Patch surface.** Same as Option 3: Option 1 hunks plus 2-4 packaging hunks; helper has 0 engine hunks.

**Resembles.** T3 Code (Node server, SQLite, fd-3 token); Aside (Node SEA daemon, always on); BrowserOS (Bun sidecar). Dossier O4: only if TypeScript skills become the point.

### Option 5: Contract first, staged (Option 1 now, Option 3 later behind the same contract)

**What it is.** Build Option 1, but define the rac core API as one versioned JSON-RPC contract (browser actions, tool calls, events, typed errors), implemented in rac-owned C++ files. The in-browser service is the first implementation. If routines while closed, warm agents, or history outgrow the browser, a Rust helper takes over agent-side work behind the same contract. Callers do not change. Nothing outside the contract depends on where it runs.

**Enables.**
- Option 1's capabilities on day one, with a clean path to Option 3's.
- Immunity to MCP and ACP churn: the outside world speaks MCP, the inside speaks the rac contract.
- Agent history now (SQLite, bounded), sync later.

**Cost against the non-negotiables.**
- Private: as Option 1. Strong.
- Never slower: as Option 1 until the helper exists; helper is lazy.
- AI off costs nothing: as Option 1; the door has its own switch.
- Cheap to update: the contract costs a few days of design now and saves a rewrite later. Strong.

**Notarization and launch.** Stage 1: the relay only (see Option 1). Stage 2: one more signed part (see Option 3).

**Patch surface.** Stage 1: 5-10 hunks. Stage 2: +2-4.

**Resembles.** Dossier order "O1 first, O3 if agent work grows"; T3 "one service, many doors"; Crest's intents model (UI sends intents, reads state).

### Comparison at a glance

| | 1 In-browser | 2 Utility process | 3 Rust helper | 4 Node/Bun sidecar | 5 Staged |
|---|---|---|---|---|---|
| Outside agents (MCP/CLI) | Yes | Needs Option 1's door | Yes | Yes | Yes |
| Routines while rac closed | No | No | Only with launch agent | Only with launch agent | Later |
| Extra idle process | None | 16-38 MB, idle-killed | ~5-10 MB, lazy (est.) | 22-67 MB, lazy | None, then lazy |
| New signed binary | Relay only | None | Relay/helper | Runtime plus JIT exceptions | Relay, later helper |
| Engine hunks (est.) | 5-10 | 13-25 | 7-14 | 7-14 | 5-10, later +2-4 |
| Crash isolation from browser | No | Yes | Yes | Yes | Later |
| Speed to ship | Fast | Medium | Slow | Medium | Fast |

### Recommendation

**Option 5: do Option 1 now, behind one versioned core contract, and add the Rust helper (Option 3) only if a trigger appears.** Triggers: the maintainer wants routines while rac is closed; the warm-agent change is approved; agent history or parsing crashes outgrow the browser process. Reject Option 4 for rac: it breaks "never slower" and "AI off costs nothing" in the same way Aside and BrowserOS did, and puts a JIT runtime beside the guard. Take Option 2 only if agent parsing proves crash-prone.

Order of work (from the digests): (1) close the two unguarded CDP doors (`--remote-debugging-port` on a real profile, `chrome://inspect` approval mode); (2) the core contract and the opt-in door with pairing and per-agent levels; (3) a secret on the MCP channel for rac-launched agents (no `nc -U` path in `ps`); (4) SQLite agent history with retention and a Keychain-encrypted text column; (5) decide O3 vs staying put. Keep JSON or prefs for settings, spaces, pins, and favorites. Reject an event log: T3's reached 17-40 GB. Defer CRDTs. Move sync to sealed files in a user folder when scheduled. Add dated backups with ordered recovery to the spaces file (Zen and Nook lessons) before any storage change.

### Open questions

1. Does the maintainer want routines or automations to run while rac is closed? That is the only thing that justifies a launch agent and Option 3.
2. Do Claude Code and Codex `mcp login` flows need loopback HTTP with OAuth and PKCE, or is a stdio relay enough? Sandboxed agents cannot reach the socket (ego #188).
3. Is a warm agent (5-minute idle cap while the panel is open) allowed? It changes "a run is one prompt" and "nothing outlives the run".
4. Does a socket in `Application Support/me.kainoa.rac` trigger a macOS TCC prompt? Untested. A Mach name or `$TMPDIR` socket avoids it.
5. Can the relay's peer be named for the pairing card? macOS checks often name rac's own helper, not the real client. Same-user is the real boundary.
6. Should outside agents default to read-only, or to `ask` or `careful` until the injection evals exist?
7. One socket per profile, or one per app? How should multiple profiles and incognito behave?
8. Will Helium's sync (`syncVaultProvider`) carry `rac.*` prefs, and when? Shape `rac.spaces` and `rac.sidebar.lists` so it can.
9. Is the Rust helper worth a second CI job while the release build has never finished?
10. Does the Anthropic rule on third-party use of Claude credentials apply to the ACP adapter rac runs? Unclear (long-tail dossier).

## Unknowns

- Idle memory, CPU, and startup for rac, Arc, Dia, Zen, Cra, Nook, Ora, BrowserOS, Aside, and Pomerado. No product here was run by the researchers, and rac has no benchmark. "Never slower than Helium" is unmeasured.
- Arc and Dia process models, migrations, and backups (closed). Arc's Chromium-in-process claim is inference.
- ego(lite) storage formats, whether its socket checks the caller, whether agent Spaces are separate `BrowserContext`s, whether `NodeService` is sandboxed.
- Aside's patch count (~48 `aside_*` files visible), migrations, backups, and whether Chromium sync is end-to-end.
- Helper numbers for Rust (5-10 MB) and Go come from existing binaries, not a minimal server. Cold start and Gatekeeper first-launch cost were not measured.
- Whether `--launch-constraint-parent` works for one signing part, whether nested Seatbelt works, minimum Bun entitlements, and XPC survival with long connections: all untested.
- Whether rac accepts `--remote-debugging-port` on a real profile and whether `chrome://inspect` approval mode is reachable: code reading only.
- Two-Mac sync was never tested by Ardia. CRDT licenses and sizes were not researched.
- The local-first dossier was not adversarially verified. Its measurements are one machine, warm cache.
- Patch-surface hunk estimates for Options 1-5 are my inference, not counts.

## Sources

Digests, all in `/Users/knewton/.t3/worktrees/rac/t3-bb0e4397/plans/research/digests/`: `t3code.md`, `aside.md`, `browseros.md`, `ego-lite.md`, `local-first-and-sidecars.md`, `chromium-agent-internals.md`, `cra.md`, `ardia.md`, `helium.md`, `rac-baseline.md`, `agent-stacks.md`, `zen.md`, `nook.md`, `ora.md`, `long-tail.md`, `closed-ai-browsers.md`, `pomerado.md`, `motion-and-feel.md` (read, no architecture facts used).

Context: `/Users/knewton/.t3/worktrees/rac/t3-bb0e4397/plans/context/maintainer-brief.md`.

Dossiers opened for detail, in `/Users/knewton/.t3/worktrees/rac/t3-bb0e4397/plans/research/`: `closed-ai-browsers.md` (Architecture and Data tables, lines 407-447), `aside.md` (Architecture, lines 220-330), `ego-lite.md` (overlay cost, lines 118-130), `ardia.md` (memory line 209), `t3code.md` (CLI and service, lines 119 and 259), `cra.md` (process model, lines 165-300).
