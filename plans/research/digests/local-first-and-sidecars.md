# Digest: local-first and sidecars research dossier

Source: `R:plans/research/local-first-and-sidecars.md` (905 lines, 2026-10-25). NOT adversarially verified.
`Z:` = Zed clone, `CAA:` = claude-agent-acp, `CR:` = rac's read-only Chromium 154 tree, `R:` = rac worktree. Tags FACT / CLAIM / INFERENCE are the dossier's. "Measured" =
author's scripts on the maintainer's Mac (macOS 26.6.2, arm64, warm cache, median of 10-20 runs, nothing
compiled). "(checked here)" = I re-verified it in `CR:`.

## In plain English

rac is one program today and its agent runs inside it. The question is whether to add a helper program, a
"local server". The dossier says: not yet, and never always-on. First add a second door for agents you already
use, like Claude Code in Terminal: a small signed command inside rac.app that talks to the browser over a
private socket, with no network port. The browser keeps every permission decision. Keep a rac-launched agent
warm while its panel is open. Store agent history in SQLite with a retention limit. Build a Rust helper only if
automations or history outgrow the browser. Sync, if ever, uses sealed files in the user's own iCloud folder,
not a CRDT or a server.

## Key facts

### Reference products

- **Zed** (GPL-3.0 editor, Apache-2.0 libraries): spawns each outside agent as a child over ACP JSON-RPC on
  stdin/stdout, via the shell, in the project root; one connection per agent per project, shared by threads; child
  dies when the connection drops (FACT `Z:crates/agent_servers/src/acp/transport.rs:16-80`,
  `agent_connection_store.rs:87-120`). Permissions stay in Zed; model choice, auth, native tool permissions belong
  to the agent. Its ACP client is about 55,000 lines.
- **ACP** (Apache-2.0): official SDKs TS, Rust, Python, Kotlin, Java; community C++, Go, Swift. Registry lists 43
  agents (21 npx, 18 binary). ACP v2 is a breaking draft; the Claude adapter serves v1, v2 or both.
  Drafts: remote transport (HTTP/2 SSE or WebSocket); MCP-over-ACP (MCP tools over the existing pipe, no socket;
  MCP 2026-07-28 only). Claude adapter advertises MCP `http` and `sse` only (`CAA:src/acp-agent.ts:2980-2983`).
- **Raycast** v2 (beta 2026-05-14): always-on Node backend; 350-450 MB at rest, 150-200 MB Node (CLAIM).
- **Obsidian**: native `obsidian-cli` in the bundle controls the running app, launches it if closed, has `eval`,
  documents no authentication; registration writes `/usr/local/bin/obsidian` and needs admin (FACT).
- **T3 Code**: Node server child, 323 MB footprint after 22 h (measured), WebSocket on `127.0.0.1:3773`, secret on
  fd 3, SQLite 2.68 GB in 14 days; its launchd service listens on LAN and Tailscale by default (see T3 digest).
- **BrowserOS**: sidecar (Bun, then Rust) started on every launch with no off switch, loopback CDP `127.0.0.1:9100`,
  MCP on port 9000 with no token, own 15-minute update feed, plaintext keys in `~/.browseros/db/browseros.sqlite`.
- **Arc and Dia**: one Swift app embedding Chromium; no XPC service, login item, or launch agent. Dia ships
  `GRDB.framework` (SQLite). Arc sync = Firestore.

### rac today (FACT)

- Chromium processes only. ACP agents are children, one per message: 15 s (Cursor) to 25 s (Claude Code) to first
  tool call (`R:docs/internals/ai.md:707-716`). MCP server on a per-run Unix socket under the profile
  (0700 folder, 0600 socket, same-UID check only, no secret), bridged by `/usr/bin/nc -U`, so the path is in `ps`
  (`R:docs/internals/ai.md:307-332`; `04-mcp-server.patch:735-740`). It dies with AI off.
- MCP server speaks initialize-based revisions 2024-11-05 to 2025-11-25; MCP 2026-07-28 is stateless (no
  `initialize`), and new clients fall back on a `400`. ACP client is v1 only (4,317 lines); MCP patch 2,349 lines.
- Storage: prefs JSON, `<profile>/rac spaces` JSON, `<profile>/rac_ai_history.json` plaintext (16 MB read cap), no
  SQLite; API keys via `os_crypt_async` and the "rac Storage Key" Keychain item. No sync (`R:VISION.md:130`).
- Quarantine trap: `LSFileQuarantineEnabled` is set (checked here, `chrome/app/app-Info.plist:210`); files a rac
  child writes are quarantined; unpacked native libraries can hang on Gatekeeper.

### IPC, auth, and identity

- stdio / inherited fd: only the parent; a secret can ride the fd (T3 fd 3). Unix socket: any process that reaches
  the path; peer UID, PID, and audit token (`LOCAL_PEERTOKEN`, checked here in SDK `sys/un.h:93`), which
  `base::mac::ProcessIsSignedAndFulfillsRequirement(audit_token_t, SecRequirementRef, ...)` can test (checked here,
  `CR:base/mac/code_signature.h:34`).
- Mach bootstrap name: Chromium app shims use a Mojo `NamedPlatformChannel` named from a SHA-256 of the profile
  folder and check the shim's signature from the audit token (`CR:chrome/browser/apps/app_shim/
  app_shim_listener.mm:73-95`); skipped for unsigned or ad-hoc dev builds (`app_shim_manager_mac.cc:161-172`).
- XPC service (`Contents/XPCServices`): private to the app; killed when idle, so stateless only.
- Loopback HTTP needs a token plus `Origin`/`Host` checks (MCP spec). CDP bypasses rac's guard; Chromium 144+
  approval mode asks Allow per connection.
- The default-profile refusal for `--remote-debugging-port` is Google-branding only (checked here,
  `remote_debugging_server.cc:160-180`), so rac probably accepts it on a real profile: a door outside the guard
  (INFERENCE).
- Local Network Access (Chromium 142+) gates public sites reaching loopback/LAN (CLAIM); Helium keeps a
  `LOCAL_NETWORK_ACCESS` content setting (checked here). macOS 15+'s local-network alert covers outgoing LAN
  connections only, not listening (TN3179).
- Possible TCC prompt: Chrome DevTools MCP docs say macOS blocks other apps reading Chrome's profile folder
  (`kTCCServiceSystemPolicyAppDataDetailed`). Untested for `me.kainoa.rac`; a Mach name or `$TMPDIR` socket avoids it.
- If HTTP is ever needed (INFERENCE): loopback only, 403 on unexpected `Origin`, exact `Host`, bearer token, no CORS.

### Chromium service model and in-tree languages

- `ServiceProcessHost::Launch<mojom::Foo>()` with `[ServiceSandbox=...]`; `set_idle_handler` kills after a timeout
  (example 5 s) (checked here). Sandboxes `kService`, `kServiceWithJit`, `kUtility`, `kNoSandbox` (checked here);
  spawning agents needs `kNoSandbox` (INFERENCE). Each Helium helper: 15.9-37.9 MB RSS (measured).
- Out-of-tree programs speak Mojo only by linking Chromium's Mojo. `net::HttpServer` and `sql::Database` (WAL)
  exist. Rust in tree has no `tokio`, `hyper`, `axum` (checked here), so async Rust builds with cargo outside GN.
  Swift in tree is iOS-only.

### macOS helper models and packaging

- Child executable (`Contents/Helpers`): invisible; rac is the "responsible" app for privacy prompts.
- Login item (`Contents/Library/LoginItems`) and launch agent (`Contents/Library/LaunchAgents`, `SMAppService.agent`,
  macOS 13+) appear in Login Items; the agent runs while rac is closed, triggers a "Background Items Added" notice
  (wording CLAIM) and may need approval. 1Password's CLI uses an XPC relay in a login item.
- Launch constraints (`codesign --launch-constraint-self/-parent/-responsible`) can force "only rac.app may launch
  me"; enforced from macOS 13.3 / Sonoma (CLAIM, WWDC23 10266). Chromium signing scripts never mention them (FACT,
  grep). A bridge run by Claude Code or Terminal cannot use a parent constraint (INFERENCE).
- Signing: `sign_and_package_app.sh` runs `sign_chrome.py --notarize`; only parts listed in `chrome/installer/mac/
  signing/parts.py` are signed. Helium's `chromium-signing.patch` already adds Sparkle's `Autoupdate` and
  `Updater.app` there, so a helper needs one more entry (INFERENCE). Notarization needs Hardened Runtime and a
  secure timestamp.
- Entitlements shipped (measured): Claude Code and opencode (Bun) use `allow-jit`, `allow-unsigned-executable-memory`,
  `disable-library-validation` (opencode adds two more); codex (Rust) `allow-jit` and `allow-unsigned-executable-
  memory`; Helium.app and its utility helper: library validation, no JIT. INFERENCE: Rust/Go/Swift helpers sign like
  Helium's utility helper; Bun/Node cannot and would be rac's least-hardened process.
- CI: the release build has never finished. A cargo/Go/Bun helper would build and test in minutes in its own job,
  copied into `out/Default/rac.app` before `sign_chrome.py` (INFERENCE). MCP conformance tests could run there.

### Runtime comparison for a helper (measured unless noted)

- Bun 1.4: runtime 63.6 MB (opencode 180.8, Claude Code 274.1); startup 7.2 ms; idle 22.5 MB RSS; official TS
  MCP SDK 2.4.0 and ACP SDK.
- Node 24/26: 116.9-145.8 MB; 35-37 ms; 54.3-67.0 MB RSS; same SDKs.
- Rust: small tools 0.58-8.4 MB (codex 260.3); codex --version 13.8 ms; 5.1 and 10.1 MB RSS; official `rmcp` 3.7.0
  and ACP crate.
- Go: tailscale 16.4 MB; 10.7 ms; 34.5-43.3 MB RSS (busy daemons); `go-sdk` 1.8.0; ACP community only.
- C++ in Chromium: nothing new; a utility process costs 16-38 MB; own MCP, community `acp-cpp`.

Startup includes about 4 ms of shell spawn. Rust/Go figures are from existing binaries, not minimal servers.
Swift: `swift-sdk` 0.12.1. Licenses: Bun MIT with JavaScriptCore
LGPL-2, Node MIT, Go BSD-3, Swift Apache-2.0; all fit GPL-3.0 (INFERENCE). Two long-running Claude Code sessions: 705 MB and 1.09 GB
RSS. Only Rust has official MCP and ACP SDKs plus no JIT.

### Storage and sync

- **Zed**: `<data dir>/threads/threads.db`, one row per thread (`id, summary, updated_at, data_type, data BLOB,
  parent_id`), zstd-3 JSON, versioned, no encryption at rest; WAL, `synchronous=NORMAL` (FACT `Z:crates/agent/src/
  db.rs`). Provider keys in Keychain.
- **Obsidian**: plain Markdown folder; Sync is AES-256-GCM. **Linear**: server-ordered deltas (unofficial study).
- **Ardia**: sealed immutable `.nns` files in a folder (iCloud Drive default), AES-256-GCM, this-device-only Keychain
  key, per-record last-writer-wins (hybrid logical clock), 15 s cycle, untested on two real Macs.
- **CRDTs**: Automerge 3 (Rust core; memory "cut by over 10x", vendor CLAIM), Yjs (v14 release candidates), Loro
  (`loro-crdt` 1.17.1). The dossier gives no licenses or sizes. Costs: tombstones, history, more machinery than rac
  needs. Event logs (T3, LiveStore) grow without bound: tens of GB, 27-minute offline `VACUUM`.
- Keychain-backed keys are the norm; plaintext (BrowserOS, T3, rac chat JSON) is the cautionary case. A sidecar
  should ask the Keychain itself or get a key over the private channel.
- A local service adds no traffic by itself; features do (Zed fetches the ACP registry from
  `cdn.agentclientprotocol.com` and may download Node v24.22.1).

### Remote access and containment

- Tailscale Serve to a loopback port adds `Tailscale-User-Login`/`-Name` (strips spoofed copies; Funnel adds none):
  best opt-in phone option. `tsnet`/`libtailscale` (Go) and iroh (Rust) add a third-party login or relay. Cloud
  relay (T3: Clerk, Cloudflare) and LAN listening: reject.
- Zed wraps terminal commands in Seatbelt (`sandbox-exec`): writes limited to the project, network blocked, approved
  hosts via a proxy, behind a flag. `sandbox-exec` is marked DEPRECATED on macOS 26.6.2; Codex still uses it.
- The `auto`-level exfiltration gap is a policy gap that no process model closes.

## What rac should take (ranked)

Cost S ~1-3 days, M ~1-2 weeks, L 3+ weeks (INFERENCE).

1. **One rac-owned JSON-RPC contract; all permission decisions stay in the browser** (S-M). In-browser MCP, the
   outside-agent door, and any helper call `AgentController::HandleToolCall` through it. Immune to MCP/ACP churn.
2. **Outside-agent door as a bundled stdio command, no TCP port** (M). Signed `rac` at `Contents/Helpers/rac`,
   linked into `~/.local/bin` (no admin prompt); `claude mcp add rac -- rac mcp`. Setting "Let other apps' agents
   use rac", off by default, independent of the AI switch; per-user socket or Mach name only while on; audit-token
   signature check; pairing card naming the launching program; per-agent level (read-only, `ask`, `careful`,
   `auto`); risky list always asks; Revoke in Settings; 1Password-style sessions (10 min rolling, 12 h cap).
3. **Keep a rac-launched agent warm while its panel is open** (S-M): one process per agent per profile, 5 idle
   minutes, one or two at most. Changes "a run is one prompt"; maintainer must approve.
4. **Secret-bearing MCP channel for rac-launched agents** (S): loopback MCP URL with a random bearer header inside
   `session/new` (secret rides stdio, not argv); `nc -U` only for stdio-only agents. Verified for Claude only.
5. **SQLite agent history with bounded growth** (S-M): one row per run and per tool call (never per token), 30-day
   retention, text encrypted with a Keychain key; Chromium `sql::Database` or Rust SQLite. Doubles as the audit log.
6. **Seatbelt around ACP agents** (M): writes to scratch only, network via a local allowlist proxy.
7. **If a helper is built, Rust** (L; S for signing/CI): signed like Chromium's utility helper, one `parts.py`
   entry, parent launch constraint, `rmcp` plus the official ACP crate, Zed's GPL-3.0 code reusable with credit.
8. **Update protocols on purpose** (S each): MCP conformance suite; plan MCP 2026-07-28 and ACP v2.
9. **`rac skills install`** for Claude Code, Codex, Cursor, OpenCode (S).
10. **Remote control later, only via the user's Tailscale Serve**, with pairing (M).
11. **Sync later via sealed files in a user-chosen folder**, before any CRDT (L).
12. **Optional on-device model via a Swift XPC helper** (Apple Foundation Models, macOS 26+) (M).

Dossier option verdicts (INFERENCE): **O1** door in the browser (C++) plus small bridge, M, do first. **O2** Mojo
utility-process service, only if agent parsing crashes. **O3** Rust helper `rac-agentd` (lazy launch over an
inherited socket; owns ACP agents, outside-agent MCP, history, schedules; doubles as the CLI), L, best long-term
shape. **O4** Bun helper, only for TypeScript skills. **O5** Swift XPC for Apple-only APIs. **O6** launch agent,
only for "automations while closed". **O7** be a target only, S-M, a fine stopping point. Storage: JSON/prefs for
settings, spaces, pins; SQLite for agent runs; reject event log; defer CRDT; sealed files when sync is scheduled.
Suggested order: items 1, 4, 2, then 3 and 5, then O7 vs O3.

## What rac should avoid

1. An always-on helper (BrowserOS, Raycast v2, T3 pay hundreds of MB; VISION: off means no work).
2. Listening on `0.0.0.0`, LAN by default, or loopback without a token.
3. A second update channel for a helper.
4. Event-sourcing browser state or storing streamed tokens.
5. Raw CDP as the outside-agent API (bypasses guard, cards, site rules).
6. A JavaScript runtime in the process that brokers browser tools (JIT and library-validation exceptions).
7. Plaintext secrets in SQLite or files.
8. A launch agent by default.
9. Web clients talking to a helper over WebSocket.
10. Downloading runtimes on first use; bundle instead.
11. Cloud relays and accounts for remote access.

## Caveats

- **Not adversarially verified.** Beyond the "(checked here)" items, every claim is the dossier author's.
- **Unverified and decision-driving:**
  - All measured numbers are single-machine, warm-cache, one author; Rust/Go figures are from existing binaries;
    "5-15 MB at rest" for a Rust helper is an estimate. Cold start and Gatekeeper first-launch cost not measured.
  - Raycast figures are vendor CLAIMs; Linear internals come from an unofficial study.
  - CRDT licenses, sizes, and fit were not researched beyond versions and one vendor memory claim.
  - Untested: TCC prompt for rac's folder; nested Seatbelt; minimum Bun entitlements; XPC survival with long
    connections; `--launch-constraint-parent` for one signing part; naming "Claude Code" behind the bridge;
    Foundation Models in an XPC helper; HTTP MCP with headers in agents other than Claude.
  - Launch-constraint versions and notice wording rest on WWDC and third-party posts. ACP v2 and MCP-over-ACP
    timelines are unknown.
  - Whether Helium leaves Local Network Access on and whether approval mode is reachable in rac. I found no
    Helium/rac patch mentioning `IsRemoteDebuggingAllowed` or `remote_debugging_server`, a hint but not proof.
- **Checked here in `CR:`, all confirmed:** branding check and approval mode; `ProcessIsSignedAndFulfillsRequirement`;
  `ServiceProcessHost` idle handler; sandbox enum; no launch-constraint text in signing scripts;
  `LSFileQuarantineEnabled`; no tokio/hyper/axum; SDK `LOCAL_PEERTOKEN`.
- **Slightly off:** "276 Rust crates" is 270 crate directories plus 6 non-crate files. No decision impact.
- Conclusions (O1 first, O3 if agent work grows) are INFERENCE. The maintainer chooses.

## Where to look in the full dossier

`plans/research/local-first-and-sidecars.md` (905 lines). Snapshot 35-49; Features 50-163; UI, look, and feel
164-231; Architecture 233-341 (process models 235-257; IPC 259-275; Chromium service model 277-305; macOS helper
models 307-330); Data and storage 343-410 (per product 345-359; patterns 361-372; encryption and TCC 374-390;
sync 392-399); Agents and AI 412-553 (Zed 437-463; protocol changes 465-485; outside-agent auth 487-520; remote
522-532; Seatbelt 534-545); Build and release 555-634 (signing 557-595; CI 597-608); runtime comparison 636-662; strengths and weaknesses 664-691; ranked take, avoid, option tables 693-808;
open questions 810-845; sources 847-905.
