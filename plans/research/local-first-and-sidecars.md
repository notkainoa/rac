# Local servers, sidecars, and local-first storage for rac: research dossier

Researched 2026-10-25. This dossier compares patterns, not one product. It answers the maintainer's question:
how could rac run its own backend as a local server, and should it?

Sources and notation:

- `Z:<path>:<lines>` is a sparse shallow clone of `zed-industries/zed` at `876c1b0c5fb0ed7c15703a1955ef4b3580bd73fa`
  (2026-10-25) in `/tmp/rac-overhaul/src/zed`.
- `ACP:<path>` is `agentclientprotocol/agent-client-protocol` at `66ff8076ec2320d85e84fedc83cb779e9d906a89`
  (2026-10-25). `CAA:<path>` is `agentclientprotocol/claude-agent-acp` at `739dde3ae5bb848bdb90e2c9150e2cc4687d480c`.
- `CR:<path>` is the read-only Chromium 154 tree with Helium and rac patches at `/Users/knewton/Dev/Github/rac/build/src`.
- `R:<path>` is the rac worktree. `R:plans/research/t3code.md` and `R:plans/research/browseros.md` are the separate
  dossiers on T3 Code and BrowserOS; this file only summarizes them.
- **Measured** numbers come from my own scripts in `/tmp/rac-overhaul/bench` on the maintainer's Mac (macOS 26.6.2,
  arm64), warm file cache, median of 10 to 20 runs, using runtimes and binaries already installed. I compiled nothing.
  The startup timer spawns through `/bin/sh`, which alone costs 4.3 ms (`/usr/bin/true`), so subtract about 4 ms.
  Memory is RSS from `ps` and "physical footprint" from `vmmap --summary`.
- Tags: **FACT** (primary source: code, official docs, API, my own listing or measurement), **CLAIM** (vendor
  marketing, self-report, or a third party), **INFERENCE** (my reasoning).

This is not a browser, so some template sections are mapped. "Features" lists what a local service enables, with
status in the products that have it. "UI, look, and feel" covers the visible surfaces of a background service.

## In plain English (at most 150 words)

rac today is one program. Everything, including the AI agent, runs inside the browser. This dossier asks whether rac
should add a small helper program, a "local server", and how. Other apps show the options. Zed starts each outside
agent as a child program and talks to it through a pipe. Raycast and T3 Code keep a helper running all the time,
which costs them 150 to 400 MB of memory. Obsidian lets terminal tools control the running app. The safest door for
outside agents is a small command inside rac.app. It talks to rac privately, with no network port. rac's safety
checks should stay in the browser, whatever else moves. A Rust helper uses about 5 to 15 MB at rest. A TypeScript
one uses 10 to 70 MB, and more when busy. Nothing should start until you turn a feature on.

## Snapshot

| Item | What it is | Engine or runtime | Platforms | License | Repo, stars | Age | Release cadence | Team | Business model |
|---|---|---|---|---|---|---|---|---|---|
| **Zed** | Rust code editor; runs outside agents over ACP, which Zed created | Own GPU UI (GPUI). Downloads Node v24.22.1 for npx-based agents if system Node is older than 22 (FACT `Z:crates/node_runtime/src/node_runtime.rs:609,703,910`) | macOS, Linux, Windows | GPL-3.0 for the editor, Apache-2.0 for GPUI and libraries (FACT: `LICENSE-GPL`, `LICENSE-APACHE` at repo root) | zed-industries/zed, 92,169 (FACT, API) | Repo created 2021-02-20 (FACT) | Weekly: v1.23.3 on 10-12, v1.24.2 on 10-14, v1.24.4 on 10-20, v1.25.2 on 10-21, v1.25.3 on 10-23 (FACT, releases API) | 45 to 57 staff (CLAIM: [Tracxn](https://tracxn.com/d/companies/zed/__3jn1wtnWJjfLtgOSDXECkHFjHmFm7BkEKtVzcAABH3A), [Dealroom](https://dealroom.co/companies/zed/)); 2,356 contributors with anonymous (FACT, API) | Paid AI plans; over $42M venture funding, $32M Series B led by Sequoia on 2025-08-20 (CLAIM, [Zed blog](https://zed.dev/blog/sequoia-backs-zed)) |
| **ACP** (Agent Client Protocol) | JSON-RPC between an editor ("client") and an agent, over stdio | SDKs: TypeScript, Rust, Python, Kotlin, Java; community C++, Go, Swift, Dart, C# (FACT `ACP:docs/libraries/*.mdx`) | Any | Apache-2.0 (FACT) | agentclientprotocol/agent-client-protocol, 4,505 (FACT) | Announced 2025-08-27 with Gemini CLI; registry opened 2026-01-28 (CLAIM, [Zed blog](https://zed.dev/blog/bring-your-own-agent-to-zed), [zed.dev/acp](https://zed.dev/acp)) | RFD process; v2 being drafted (FACT `ACP:docs/docs.json:182-262`) | Lead maintainers Ben Brandt (Zed) and Sergey Ignatov (JetBrains) (FACT `ACP:MAINTAINERS.md`) | Open standard |
| **Raycast** | Launcher with extensions | v1: Swift/AppKit app plus one Node child for all extensions. v2 (public beta 2026-05-14): Swift (Mac) or C#/WPF (Windows) shell, WKWebView or WebView2 UI, one long-lived Node backend, Rust core (CLAIM, [Raycast blog](https://www.raycast.com/blog/a-technical-deep-dive-into-the-new-raycast)) | macOS, Windows (v2), iOS | Proprietary; extensions repo MIT | raycast/extensions, 7,810 (FACT) | Not checked | Not checked | Not checked | Pro subscription; MCP is "Pro Exclusive" (CLAIM, [manual](https://manual.raycast.com/ai/model-context-protocol)) |
| **Obsidian** | Markdown notes in a folder you own | Electron; a native `obsidian-cli` binary inside the bundle (FACT, [help](https://obsidian.md/help/cli)) | macOS, Windows, Linux, iOS, Android | Proprietary, free; API types MIT | obsidianmd/obsidian-api, 2,340 (FACT) | Started 2020 (CLAIM, [about](https://obsidian.md/about)) | CLI early access in 1.12.0 (2026-02-10), general in 1.12.4 (2026-02-27) (CLAIM, third-party guides) | Seven named staff (CLAIM, about page) | Paid Sync and Publish; "100% supported by our users, not investors" (CLAIM) |
| **Linear** | Issue tracker whose sync engine makes a web app feel local | IndexedDB, MobX, WebSocket "delta packets" | Web, desktop | Closed | Reverse-engineered study: wzhudev/reverse-linear-sync-engine, 2,875 (FACT) | Not checked | Not checked | Not checked | SaaS |
| **T3 Code** | Local server plus thin clients (summary only) | Node server (Electron binary as Node), Electron desktop, web, phone (FACT `R:plans/research/t3code.md:27-41`) | macOS, Windows, Linux, web, iOS, Android | MIT | pingdotgg/t3code, 30,044 | Since 2026-02-08 | About 3 nightlies a day | T3 Tools Inc. | Free; Cloudflare relay |
| **BrowserOS** | Chromium fork driven by a sidecar server (summary only) | Bun sidecar, then a Rust sidecar for "neo" (FACT `R:plans/research/browseros.md:289-352,413-435`) | macOS, Windows, Linux | AGPL-3.0 | browseros-ai/BrowserOS | Since 2025-06 | Every 2 to 5 weeks in 2026 | Not checked | Not checked |
| **Electron `utilityProcess`** | A Node child "launched with Chromium's Services API", talking over MessagePorts (FACT, [Electron docs](https://www.electronjs.org/docs/latest/api/utility-process)) | Electron | Desktop | MIT | electron/electron, 123,544 | 2013 | n/a | n/a | n/a |
| **Tauri sidecars** | Extra binaries bundled next to a Rust app, started through the shell plugin with argument allowlists (FACT, [Tauri docs](https://v2.tauri.app/develop/sidecar/)) | Rust plus the system web view | Desktop, mobile | Apache-2.0 or MIT | tauri-apps/tauri, 112,185 | 2019 | n/a | n/a | n/a |
| **Chromium's service model** | Utility processes hosting Mojo services, native messaging hosts, app shims (FACT, `CR:` paths below) | C++ | All | BSD-3 | In rac's tree | n/a | Follows Chromium | n/a | n/a |

## Features

Status words: **shipped**, **beta** (preview, feature flag, or draft spec), **planned**. "rac today" closes each group.

### Tabs, sidebar, spaces (agents and tabs)

- shipped: BrowserOS neo puts each agent task's tabs in a colored tab group titled `<client>/<task>`, closed when the
  session ends (FACT `R:plans/research/browseros.md:67`).
- shipped: BrowserOS neo labels tabs "yours", "other agents'", and "the user's", as a label and "never a barrier"
  (FACT `R:plans/research/browseros.md:68`).
- shipped: Zed's Threads Sidebar runs many agent threads at once, grouped by project, with Git worktree isolation
  (FACT `Z:docs/src/ai/parallel-agents.md:1-20`).
- shipped: Zed "Terminal Threads" run an agent's own TUI in a terminal that Zed files as a thread
  (FACT `Z:docs/src/ai/terminal-threads.md:1-12`).
- shipped: T3 Code threads grouped by project, with settle, snooze, and a 5-second Undo (FACT `R:plans/research/t3code.md:49-60`).
- rac today: the agent acts only in tabs the user attached and tabs it opened, marked by a ring and a pill (FACT
  `R:docs/internals/ai.md:363-366,638-641`). No grouping of agent tabs.

### Navigation and command bar

- shipped: Obsidian CLI, about 115 commands in 25 groups, a TUI with history and `Ctrl+R`, and `command id=<id>` to
  run any palette command, including plugin commands (FACT, [Obsidian help](https://obsidian.md/help/cli)).
- shipped: Raycast's "Install MCP Server" and "Manage MCP Servers" commands (FACT, [Raycast manual](https://manual.raycast.com/ai/model-context-protocol)).
- shipped: Zed exposes each external agent as an action that a keybinding can start (`agent::NewExternalAgentThread`)
  (FACT `Z:docs/src/ai/external-agents.md:120`).
- rac today: no CLI and no command bar yet (planned for phase 5, `R:docs/roadmap.md:137`; FACT `R:plans/research/rac-baseline.md:98`).

### Split view, peek, small windows

- shipped: Zed's "Agentic" panel layout puts the agent panel and threads on the left (FACT
  `Z:docs/src/ai/parallel-agents.md:14`). Nothing else in this group depends on a local server. Not applicable.

### Import, sync, profiles

- shipped: Linear's sync engine: a local IndexedDB copy, transactions sent to the server, "delta packets" broadcast
  back with a monotonically increasing sync id, last-writer-wins on updates (FACT for the study,
  [README](https://github.com/wzhudev/reverse-linear-sync-engine), chapters 1-4).
- shipped: Obsidian Sync, end-to-end encrypted with AES-256-GCM and a scrypt-derived key; the server still sees which
  device changed what and when (FACT, [Obsidian help](https://obsidian.md/help/sync/security)).
- shipped, not tested on two Macs by its team: Ardia's folder sync over iCloud Drive with sealed immutable files,
  per-record last-writer-wins by hybrid logical clock (FACT `R:plans/research/ardia.md:359-381`).
- shipped: Arc's sync uses Google Firestore; Arc.app bundles `FirebaseFirestoreInternal.framework` and gRPC (FACT, my
  listing of `/Applications/Arc.app/Contents/Frameworks`). Arc shuts down 2026-12-22 (brief).
- shipped: Zed remote development: Zed uploads or downloads `zed-remote-server` to `~/.zed_server` on the remote host,
  runs it as a daemon in "proxy mode", and reconnects after drops (FACT `Z:docs/src/remote-development.md:223-257`).
- beta: Raycast v2's Rust sync engine "shares a schema with its server counterpart" (CLAIM, Raycast blog).
- shipped: T3 Code has no sync; all clients read one server live (FACT `R:plans/research/t3code.md:456-468`).
- rac today: no sync; "Sync (maybe later)" (FACT `R:VISION.md:130`).

### Privacy and blocking (local-service security)

- shipped: Chromium 142+ "Local Network Access" asks before a public site reaches loopback or LAN addresses (CLAIM,
  [OpenReplay](https://blog.openreplay.com/chrome-local-network-access-lna-permission/)). rac is on Chromium 154, so it
  should inherit this (INFERENCE; not checked against Helium's patches).
- shipped: Chromium 144+ remote debugging "approval mode": turned on at `chrome://inspect/#remote-debugging`, each
  incoming connection needs a click on Allow (FACT `CR:chrome/browser/devtools/remote_debugging_server.cc:185-190`;
  `CR:chrome/browser/devtools/devtools_connection_dialog.cc:49-83`).
- beta: Zed runs agent terminal commands under macOS Seatbelt (`sandbox-exec`) with network blocked by default and a
  proxy allowlist for approved hosts, behind a feature flag (FACT `Z:crates/agent/src/sandboxing.rs:1-25`;
  `Z:docs/src/ai/sandboxing.md:55-66,193-208`).
- shipped: 1Password CLI asks for Touch ID per terminal window; the session refreshes for 10 minutes of use with a
  12-hour hard cap (FACT, [1Password docs](https://www.1password.dev/cli/app-integration-security/)).
- shipped: Obsidian runs in Restricted Mode by default; plugins are not sandboxed once enabled (FACT,
  [Obsidian help](https://obsidian.md/help/plugin-security)).

### AI assistant

- shipped: Raycast AI uses MCP servers over stdio or HTTP, with OAuth (dynamic or static client registration) (FACT,
  Raycast manual).
- shipped: Zed's own agent, with `disable_ai: true` to turn all AI off (FACT `Z:docs/src/ai/quick-start.md:88`).
- rac today: shipped (side panel, new tab Ask, find Ask, link summaries), off by default (FACT `R:docs/internals/ai.md`).

### Agent

- shipped: Zed external agents over ACP, installed from the ACP Registry. The registry lists 43 agents: 21 as npx
  packages, 18 as binaries, 2 as both, 2 through uvx (FACT, `https://cdn.agentclientprotocol.com/registry/v1/latest/registry.json`,
  fetched 2026-10-25; URL from `Z:crates/project/src/agent_registry_store.rs:20`).
- beta: ACP v2, a set of breaking changes (new prompt lifecycle, permission requests, tool call updates). Zed already
  builds with `unstable_protocol_v2` (FACT `ACP:docs/rfds/v2/overview.mdx`; `Z:Cargo.toml:533`). The Claude adapter
  serves v1, v2, or both (FACT `CAA:src/serve.ts:1-20`).
- beta: ACP remote transport: one `/acp` endpoint with HTTP/2 SSE streams and a WebSocket alternative (FACT
  `ACP:docs/rfds/streamable-http-websocket-transport.mdx:1-30`; "Active" group in `ACP:docs/docs.json:200-205`).
- beta: MCP-over-ACP: the client serves MCP tools over the ACP pipe it already has, with no socket or second process
  (FACT `ACP:docs/rfds/mcp-over-acp.mdx:1-30`). It targets MCP 2026-07-28 only.
- shipped: BrowserOS neo has no built-in agent; outside agents drive it (FACT `R:plans/research/browseros.md:138`).
- shipped: T3 Code keeps provider sessions alive 30 idle minutes (FACT `R:plans/research/t3code.md:333`).
- rac today: ACP v1 client; one agent process per message; MCP only for that run (FACT `R:docs/internals/ai.md:241-272`).

### Extensibility (CLI, MCP, API, extensions, mods)

- shipped: Obsidian CLI "connects to the running Obsidian instance" and launches it if closed; includes `eval` (run
  JavaScript) and `dev:cdp`; no authentication is documented (FACT, Obsidian help).
- shipped (community plugin): Obsidian Local REST API with MCP at `https://127.0.0.1:27124/mcp/`, a bearer key, and a
  self-made certificate authority "name-constrained" to `127.0.0.1` and `localhost` (FACT,
  [README](https://github.com/coddingtonbear/obsidian-local-rest-api)).
- shipped: Raycast extensions run in "a single child Node.js process", each in "its own v8 isolate (worker thread)",
  rendered natively through a custom React reconciler (FACT, [Raycast security](https://developers.raycast.com/information/security);
  [FAQ](https://developers.raycast.com/misc/faq)).
- shipped: Zed WASM extensions; extension-provided agents are deprecated in favor of the registry (FACT
  `Z:docs/src/ai/external-agents.md:182`).
- shipped: T3 `/mcp` for outside agents, OAuth 2.1 with PKCE, read-only by default (FACT `R:plans/research/t3code.md:528-534`).
- shipped: Ardia's `ardia` CLI over a token-gated DevTools socket with about 70 allowed CDP methods (FACT
  `R:plans/research/ardia.md:400-424`).
- shipped: Chromium native messaging hosts for extensions (FACT `CR:chrome/browser/extensions/api/messaging/native_message_process_host.cc:45`).
- rac today: no outside-agent access. "Letting outside agents (not started by rac) use the browser tools" is listed as
  not built (FACT `R:docs/internals/ai.md:747-750`). Turning AI off also removes the MCP server (brief).

### Other

- shipped: T3 `t3 service install` runs the server as a per-user launchd service that listens on LAN and Tailscale
  addresses by default (FACT `/tmp/rac-overhaul/src/t3code/docs/user/background-service.md`, "Local network access").
- shipped: BrowserOS updates its sidecar on its own feed every 15 minutes, Ed25519-signed (FACT `R:plans/research/browseros.md:339-346`).
- beta: Raycast v2 runs a separate Rust file-indexer process (CLAIM, Raycast blog).

## UI, look, and feel

A local service is mostly invisible. Its look is the handful of moments where it asks, waits, or shows status. Those
moments decide whether it feels calm or intrusive.

### Layout: where a background service shows up

- **System surfaces it cannot style.** A launchd agent registered with `SMAppService` lands in System Settings,
  General, Login Items, and macOS posts its own "Background Items Added" notice, which apps cannot suppress (FACT for
  the API, Apple's `SMAppService` doc via `developer.apple.com/tutorials/data/documentation/servicemanagement/smappservice.json`;
  CLAIM for the notice wording, [MacPaw](https://macpaw.com/how-to/stop-background-items-added-mac)). Legacy plists in
  `~/Library/LaunchAgents` show as generic "exec" entries unless the Team IDs match (CLAIM,
  [memql issue #545](https://github.com/znasllc-io/memql-cockpit/issues/545)). A helper spawned by the app, an XPC
  service, or a Chromium utility process shows none of this (INFERENCE from where each lives).
- **Local Network alert.** On macOS 15+, outgoing connections to LAN addresses trigger a one-time alert, attributed to
  the "responsible" app even when a helper makes the call. Listening and accepting TCP needs no permission (FACT,
  Apple TN3179 via `developer.apple.com/tutorials/data/documentation/technotes/tn3179-understanding-local-network-privacy.json`).
  A loopback-only rac service never triggers it (INFERENCE).
- **In-app status.** Zed shows each external agent in the new-thread menu and a "Log in" action when an agent needs
  auth (FACT `Z:docs/src/ai/external-agents.md:91,119`). BrowserOS neo shows a "Running now" card per connected agent
  with a live preview, Watch, and Stop (FACT `R:plans/research/browseros.md:138`). rac shows a tab ring and a pill
  with Resume and Stop (FACT `R:docs/internals/ai.md:638-641`).

### Visual language, materials, typography, color

- Not applicable to a service as such. The only rule worth copying: Raycast v2 avoids web tells in a web UI, with
  "No `cursor: pointer` on interactive controls", most hover highlights dropped, and popovers as native windows so they
  can cross window edges (CLAIM, Raycast blog). rac's existing Views and WebUI style should host every new surface.

### Motion (values from code)

- Zed's agent panel "generating" indicator pulses opacity between 0.4 and 0.8 over 2 s and repeats; a lighter one
  pulses 0.2 to 0.6 over 1 s (FACT `Z:crates/agent_ui/src/agent_panel.rs:5444-5446,6133-6135`). It repaints only while
  an agent works (INFERENCE).
- T3 Code's agent cursor moves with a 150 ms `ease-out` on opacity and transform (FACT
  `R:plans/research/t3code.md:211`).
- Raycast v2 tears down hidden windows, so a cold window opens with "a short delay"; they plan warm grace periods
  (CLAIM, Raycast blog). This is the motion cost of an always-on web UI: either keep it resident or pay a delay.

### Signature interactions that feel great

- **1Password's terminal prompt.** The prompt names the requesting process ("`iTerm2` or `Terminal`") and the
  account, uses Touch ID, and covers one terminal window and its subshells; it refreshes for 10 minutes of use, with
  a 12-hour cap, and locking the app revokes it (FACT, [1Password docs](https://www.1password.dev/cli/app-integration-security/)).
  For rac: an outside agent's first request could show one card naming the agent and its program, scoped to that
  agent's session (INFERENCE).
- **Chrome's per-connection Allow.** With remote debugging turned on in `chrome://inspect`, each new DevTools client
  gets a dialog with Allow and a way to turn the feature off (FACT `CR:chrome/browser/devtools/devtools_connection_dialog.cc:49-83`).
- **Zed's permission choices.** "Allow once", "Always allow", "Reject" map directly onto ACP permission option kinds
  (FACT `Z:crates/agent_ui/src/conversation_view.rs:699-729`; `Z:docs/src/ai/tool-permissions.md:184`).
- **Obsidian's one switch.** Settings, General, "Command line interface", then "Register CLI". The terminal command
  then just works (FACT, Obsidian help).
- **Zed's registry install.** Pick an agent from a list; Zed downloads it, checks its SHA-256 against the registry or
  the GitHub release digest, and caches it per version (FACT `Z:crates/project/src/agent_server_store.rs:1213-1260`).

### Things that feel bad

- **rac's cold agent per message.** Cursor about 15 s and Claude Code about 25 s from Send to first tool call, every
  message, because each run starts a new agent (FACT `R:docs/internals/ai.md:707-716`). Zed keeps one agent process per
  agent per project and reuses it across threads (FACT `Z:crates/agent_ui/src/agent_connection_store.rs:87-92,330-375`).
- **Always-on cost you did not ask for.** Raycast v2 rests at 350 to 450 MB, with 150 to 200 MB in the Node backend
  (CLAIM, Raycast blog). T3's server process here uses 323 MB physical footprint after 22 hours (FACT, `vmmap` on PID
  67823, 2026-10-25). BrowserOS starts its sidecar and debugging port on every launch, with no setting to stop it (FACT
  `R:plans/research/browseros.md:348-353`).
- **Admin prompt for a CLI.** Obsidian's macOS registration writes `/usr/local/bin/obsidian` and "requires
  administrator privileges" (FACT, Obsidian help). A user-owned folder such as `~/.local/bin` would avoid the prompt (INFERENCE).
- **Gatekeeper and quarantine on helpers.** Every file a rac-launched agent writes is quarantined, and a native
  library it unpacks can hang on Gatekeeper (FACT `R:docs/internals/ai.md:212-224`).

## Architecture

### Process models compared

| Product | Processes | Who starts the service, and when | Transport between parts | Where the policy lives | Evidence |
|---|---|---|---|---|---|
| **Zed** | One Rust app. One child per external agent. A remote daemon per SSH project | Zed spawns an agent when a thread for it opens, through the system shell, non-interactive, with literal args, in the project root. One connection per agent per project is shared by its threads, and dropping it kills the child | ACP JSON-RPC on the child's stdin and stdout. For remote projects the same command runs on the remote host through the remote server | In Zed: permission prompts, the tool forwarding, and the terminal sandbox | FACT `Z:crates/agent_servers/src/acp/transport.rs:16-20,31-80`; `Z:crates/agent_ui/src/agent_connection_store.rs:87-92` |
| **Raycast v1** | Swift app, plus one Node child for all extensions, each in a V8 worker isolate with "limited heap memory" | Raycast, on demand; extensions "loaded and unloaded as needed" | "Standard file handles and a thin RPC protocol" | Native app; extensions are "not further sandboxed" for file, network, or Node features | FACT, [Raycast security](https://developers.raycast.com/information/security) |
| **Raycast v2** | Swift shell, WKWebView content, WebKit GPU and network processes, one long-lived Node backend that "owns the app's business logic", a Rust core, a separate Rust indexer | The shell at launch; always on | "A mix of platform message handlers and stdio transport"; interfaces "defined once" with generated typed clients | Node backend | CLAIM, [Raycast blog](https://www.raycast.com/blog/a-technical-deep-dive-into-the-new-raycast) |
| **Obsidian** | Electron main and renderers; plugins inside the renderer with full Node access; a native `obsidian-cli` | The user turns on the CLI in Settings; the CLI starts the app if needed | Not documented. A third-party guide reports a socket at `~/.obsidian-cli.sock` (CLAIM, [Medium guide](https://kurtis-redux.medium.com/obsidian-cli-how-the-command-line-will-change-note-taking-26c90f03de17)) | In the app; no CLI authentication is documented | FACT, [Obsidian CLI help](https://obsidian.md/help/cli) |
| **Linear** | Web or desktop client holding an in-memory object pool, IndexedDB, and a transaction queue | Always, while the app runs | Batched transactions up; WebSocket "delta packets" down | The server: it orders everything by sync id and may add side effects | FACT for the study, [README](https://github.com/wzhudev/reverse-linear-sync-engine) chapters 3-4 |
| **T3 Code** | Electron main, a Node server child, provider CLIs as grandchildren, optional relay | The desktop app at launch (bootstrap secret on file descriptor 3), or a launchd service | WebSocket RPC, 203 methods, on `127.0.0.1:3773` by default | The server | FACT `R:plans/research/t3code.md:250-297` |
| **BrowserOS** | Chromium, a sidecar (Bun, then Rust for neo), a bundled extension | The browser, at every start, with health checks every 30 s and 3-strike fallback | Loopback CDP on `127.0.0.1:9100`, with extra BrowserOS CDP domains; MCP proxy | The sidecar | FACT `R:plans/research/browseros.md:289-352` |
| **Arc and Dia** | One Swift app embedding Chromium as `ArcCore.framework`, plus Chromium's own helpers | n/a | In-process | In-process | FACT, my listing: Dia bundles `ArcCore.framework`, `GRDB.framework`, `libAIInfra.dylib`; Arc bundles Firestore and gRPC frameworks; neither has an XPC service, login item, or launch agent besides Sparkle's |
| **Electron `utilityProcess`** | A Chromium-launched child with Node | The main process, after `ready` | `postMessage` and transferable MessagePorts; stdin unsupported | Main process | FACT, [Electron docs](https://www.electronjs.org/docs/latest/api/utility-process) |
| **Tauri sidecar** | A bundled binary named `<name>-<target triple>` | Rust or JS through the shell plugin, if a capability allows `shell:allow-execute` or `shell:allow-spawn` for that sidecar | stdio; arguments matched against static values or regexes | Capability files | FACT, [Tauri docs](https://v2.tauri.app/develop/sidecar/) |
| **rac today** | Chromium's processes only. ACP agents are children, one per message. `/usr/bin/nc -U` is the agent's MCP bridge | rac, when a message is sent with an agent selected | ACP on stdio; MCP on a Unix socket under the profile, same-UID only, no secret | Browser process: `AgentController`, `ActionGuard`, cards | FACT `R:plans/research/rac-baseline.md:253-263`; `R:docs/internals/ai.md:241-272,307-332` |

Two lessons stand out (INFERENCE):

1. **Every product that keeps policy in one place keeps it next to the data it protects.** Zed's permissions sit in
   the editor that owns the files. Linear's ordering sits on the server that owns the records. rac's guard needs live
   DOM nodes, refs, and Chromium's actor framework, so it must stay in the browser process whatever else moves out.
2. **The always-on designs are the memory-heavy ones.** Raycast v2 and T3 Code run a Node process for the app's
   whole life. Zed, Raycast v1, and Tauri sidecars start a child only when a feature needs it.

### Ways two local programs can talk

| Mechanism | Who can connect | Secret | Peer identity the server gets | Good for in rac | Evidence |
|---|---|---|---|---|---|
| stdio pipes to a child | Only the parent | None needed | Implicit (it is your child) | Browser to sidecar; sidecar to ACP agents; outside agent to a bundled bridge | FACT: ACP and MCP stdio bindings; `Z:crates/agent_servers/src/acp/transport.rs:31-80` |
| Inherited socket or descriptor | Only the parent and child | Can travel on the descriptor | Implicit | Browser to sidecar, two-way, with no name on disk | FACT: T3 passes bootstrap JSON on fd 3 (`R:plans/research/t3code.md:262-266`) |
| Unix domain socket | Any process that can reach the path | Optional | UID (`getpeereid`), PID, and the **audit token** (`LOCAL_PEERTOKEN`), which can be checked against a code-signing requirement | A signed `rac` bridge connecting to the running browser | FACT: macOS SDK `sys/un.h:88-93`; `CR:base/mac/code_signature.h:31-39`. rac checks only the UID today (FACT `R:patches/rac/agent/04-mcp-server.patch:735-740`) |
| Mach bootstrap name | Any process in the user's session | Optional | Audit token from the message trailer | A bridge built in Chromium's tree, as Chromium's app shims do | FACT `CR:chrome/browser/apps/app_shim/app_shim_listener.mm:73-85`; `CR:chrome/browser/apps/app_shim/mach_bootstrap_acceptor.cc:57-87`; `CR:chrome/browser/apps/app_shim/app_shim_manager_mac.cc:183` |
| XPC service in `Contents/XPCServices` | Only the containing app ("private, and is available only to the main application") | Not needed | Code-signing requirement checks (`xpc_connection_set_peer_code_signing_requirement` on macOS 12+, `NSXPCConnection.setCodeSigningRequirement:` on 13+) | A stateless helper the browser calls | FACT: [Apple archive doc](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingXPCServices.html); macOS SDK `xpc/connection.h:772`, `NSXPCConnection.h:155` |
| Loopback HTTP or WebSocket | Any local process, and web pages through DNS rebinding unless `Origin` and `Host` are checked | Needed (bearer or OAuth) | None beyond the token | Only for clients that cannot run a command, such as hosted or phone clients | FACT: MCP 2026-07-28 says servers "MUST validate the `Origin` header", "SHOULD bind only to localhost", "SHOULD implement proper authentication" ([spec](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http)) |
| Chrome DevTools Protocol | Whoever has the port, the pipe, or approval | Approval per connection (Chromium 144+) or a token (Ardia) | None | Debugging, not agent policy: CDP bypasses the guard | FACT `CR:chrome/browser/devtools/remote_debugging_server.cc:160-190`; `R:plans/research/ardia.md:405-418` |
| Native messaging | Only an extension named in the host manifest | None | Extension origin | Not needed; rac's UI is not an extension | FACT `CR:chrome/browser/extensions/api/messaging/native_message_process_host.cc:45` (1 MiB cap from host); `CR:chrome/common/chrome_paths.cc:461-497` |

A note on Chromium-branded builds: the check that refuses `--remote-debugging-port` on the default profile is on only
for Google Chrome branding; for other brandings it is a testing switch (FACT
`CR:chrome/browser/devtools/remote_debugging_server.cc:168-180`). So rac accepts that flag on a real profile
(INFERENCE). That is a debugging door outside the guard, worth knowing about when writing the threat model.

### Chromium's own service model, and what rac can reuse

- **Utility-process services.** `ServiceProcessHost::Launch<mojom::Foo>()` starts a Mojo service in a helper process.
  The sandbox comes from a `[ServiceSandbox=...]` attribute on the interface, and `set_idle_handler` can kill the
  process after an idle timeout (the header's own example uses 5 s) (FACT
  `CR:content/public/browser/service_process_host.h:42-71`).
- **Sandbox choices.** `kService` is "computation only"; `kServiceWithJit` adds dynamic code; `kUtility` has "limited
  access to system services"; `kNoSandbox` "runs with the same rights as the browser", meant for "code that interacts
  with third party code in another process" (FACT `CR:sandbox/policy/mojom/sandbox.mojom:14-56`). Spawning ACP agents
  needs `kNoSandbox`; parsing untrusted agent output could use `kService` (INFERENCE).
- **Cost of one more Chromium helper.** Helium's helper processes on this Mac use 15.9 to 37.9 MB RSS each (FACT, `ps`,
  2026-10-25).
- **Out-of-tree programs can speak Mojo only by linking Chromium's Mojo.** Chrome's updater, enterprise companion, and
  remote desktop host do this through `components/named_mojo_ipc_server`, whose validator receives the peer's PID and,
  on macOS, its audit token (FACT `CR:components/named_mojo_ipc_server/README.md`;
  `CR:components/named_mojo_ipc_server/connection_info.h:24-42`; BUILD.gn users in `chrome/updater`,
  `chrome/enterprise_companion`, `remoting/host`).
- **App shims are the closest precedent for a rac CLI.** The browser publishes a Mojo `NamedPlatformChannel` (a Mach
  bootstrap name) derived from a SHA-256 of the profile folder; the separate shim executable connects to it, and the browser checks the shim's
  code signature from the audit token. A version symlink makes the shim load the same framework version as the running
  browser (FACT `CR:chrome/browser/apps/app_shim/app_shim_listener.mm:73-95`; `CR:chrome/browser/apps/app_shim/mach_bootstrap_acceptor.cc:34-36`; `CR:chrome/app_shim/app_shim_controller.mm:547,580`; `CR:base/mac/code_signature.h:31-39`).
- **An HTTP server already exists.** `net::HttpServer` backs DevTools' HTTP and WebSocket handler (FACT
  `CR:content/browser/devtools/devtools_http_handler.cc`; `CR:net/server/http_server.h`).
- **Rust in the tree is limited.** Chromium vendors 276 Rust crates, including `serde_json`, `anyhow`, and `futures`,
  but not `tokio`, `hyper`, or `axum` (FACT, `ls CR:third_party/rust`). INFERENCE: an async Rust service would be built
  with cargo outside GN, not inside Chromium's build.
- **Swift in the tree is iOS-only today.** `build/config/apple/swift_source_set.gni` exists, and the only user I found
  is an iOS target (FACT `CR:components/password_manager/services/csv_password/ios/BUILD.gn`). Calling Apple-only Swift
  APIs from rac would need a separate helper (INFERENCE).

### macOS helper models

| Helper type | Where it lives | Lifetime | Who can talk to it | What the user sees | Fits rac for |
|---|---|---|---|---|---|
| Child executable | `Contents/Helpers`, `Contents/MacOS`, or the framework's `Helpers` | Parent decides | Parent, unless it opens a socket | Nothing. macOS treats rac as the "responsible" app for privacy prompts (FACT, TN3179) | The sidecar and the bridge |
| XPC service | `Contents/XPCServices/<name>.xpc` | launchd "launches them on demand, restarts them if they crash, and terminates them (by sending `SIGKILL`) when they are idle"; should "hold on to minimal state" | The containing app only | Nothing | Stateless jobs, such as an Apple on-device model call (INFERENCE) |
| Login item | `Contents/Library/LoginItems/<name>.app`, registered with `SMAppService.loginItem` | From login | Any process, through its own XPC Mach service | An entry in Login Items | 1Password's "1Password Browser Helper" is the XPC relay between its CLI and app (FACT, my listing; [1Password docs](https://www.1password.dev/cli/app-integration-security/)) |
| Launch agent | Plist in `Contents/Library/LaunchAgents` with `BundleProgram`, registered with `SMAppService.agent` (macOS 13+) | launchd; can run while rac is closed | Any process, through its Mach service or socket | Login Items entry and a "Background Items Added" notice; status can be `requiresApproval` | Only for automations or remote access while rac is closed |
| Launch daemon | `Contents/Library/LaunchDaemons` | Root | System | Approval | Never for rac |

Evidence: Apple's `SMAppService` and `SMAppService.agent(plistName:)` docs ("must correspond to a property list in the
calling app's `Contents/Library/LaunchAgents` directory") and the XPC archive doc above (FACT).

**Launch constraints** let a helper refuse to start unless its parent, or the "responsible" process, matches a team
identifier and signing identifier (FACT, Apple "Defining launch environment and library constraints" via
`developer.apple.com/tutorials/data/documentation/security/defining-launch-environment-and-library-constraints.json`).
Apple's WWDC23 session 10266 introduced them for third-party apps, enforced from macOS 13.3 and Sonoma (CLAIM,
[WWDC23](https://developer.apple.com/videos/play/wwdc2023/10266/); [Eclectic Light](https://eclecticlight.co/2024/08/23/why-launch-constraints-can-crash-apps/)).
For rac: a `rac-agentd` helper could refuse to run unless rac.app launched it. A bridge that outside agents run
cannot use a parent constraint, because Claude Code or Terminal is its parent (INFERENCE).

**Quarantine is inherited.** Chromium's Info.plist sets `LSFileQuarantineEnabled`, so files a rac child writes are
quarantined and a child cannot clear the flag (FACT `R:docs/internals/ai.md:212-224`). Any sidecar that downloads or
unpacks code inherits this trap (INFERENCE).

### UI technology, languages, code layout and size (reference points)

- Zed: 251 workspace crates (FACT, count of `crates/` members in `Z:Cargo.toml`). Its ACP client alone is 20,469 lines
  in `crates/agent_servers/src/acp/` plus 34,573 in `crates/acp_thread/src/` (FACT, `wc -l`).
- rac's ACP client is 17 C++ files and 4,317 lines; its MCP server patch is 2,349 lines (FACT
  `R:plans/research/rac-baseline.md:288`; `wc -l R:patches/rac/agent/04-mcp-server.patch`).
- BrowserOS neo's Rust server: 80,121 lines; its retired Bun sidecar: 44,111 lines (FACT `R:plans/research/browseros.md:401-404`).
- T3 Code's Node server: 460,870 lines of TypeScript (FACT `R:plans/research/t3code.md:386`).
- The Claude ACP adapter is TypeScript, version 0.95.0, on `@agentclientprotocol/sdk` 2.0.1 and
  `@anthropic-ai/claude-agent-sdk` 0.3.309 (FACT `CAA:package.json:6,68-69`).

## Data and storage

### What each stores, where, and how

| Product | What | Where and format | Encryption | Evidence |
|---|---|---|---|---|
| **Zed** | Agent threads | `<data dir>/threads/threads.db`, SQLite table `threads(id, summary, updated_at, data_type, data BLOB, parent_id)`; one row per thread holding zstd-compressed JSON (level 3), versioned `0.3.0` with upgrade code for older formats | None at rest (FileVault only) | FACT `Z:crates/agent/src/db.rs:175-190,448-470` |
| Zed | SQLite settings for every Zed database | WAL, `synchronous=NORMAL`, `busy_timeout=1`, foreign keys on | n/a | FACT `Z:crates/sqlez/src/thread_safe_connection.rs:339-344` |
| Zed | Settings, registry cache, agent downloads | `~/.config/zed/settings.json`; registry JSON and icons in a cache folder; agent archives in per-version folders named by a hash of URL and SHA-256, with stale folders removed | Provider API keys in the Keychain | FACT `Z:docs/src/ai/external-agents.md:99,157`; `Z:crates/project/src/agent_registry_store.rs:371-374,535`; `Z:crates/project/src/agent_server_store.rs:1023-1111` |
| **Raycast** | App data and extension storage | "A local encrypted database"; secure data in the Keychain; extension data readable only by that extension | Yes | CLAIM, [Raycast security](https://developers.raycast.com/information/security) |
| **Obsidian** | Notes | Plain Markdown files in a folder the user picks; "Obsidian doesn't encrypt your local vault" | Local: none. Sync: AES-256-GCM, scrypt-derived key; encrypted paths and contents, deterministic encrypted hashes | FACT, [Obsidian Sync security](https://obsidian.md/help/sync/security) |
| **Linear** | Workspace models | IndexedDB: one `linear_databases` index plus `linear_database_<id>` per workspace with models, metadata, and queued transactions | Not covered by the study | FACT for the study, chapter 2 |
| **T3 Code** | Every event, projections, receipts, outbox | One SQLite file, WAL; 69 migrations; 2.68 GB plus a 30.7 MB WAL after 14 days on the maintainer's Mac; users report 17 to 40 GB | Secrets as plain files in a 0700 folder | FACT `R:plans/research/t3code.md:408-433,438-444` |
| **BrowserOS** | Provider keys, OAuth tokens, chats, schedules | `~/.browseros/db/browseros.sqlite` (Drizzle, WAL) | Keys and tokens in **plaintext** columns | FACT `R:plans/research/browseros.md:444-446` |
| **Ardia** | Sync state and remote files | Sealed `.nns` files in a folder (iCloud Drive by default); key in a this-device-only Keychain item | AES-256-GCM, HKDF from a 256-bit phrase | FACT `R:plans/research/ardia.md:349-378` |
| **Dia** | App data | Ships `GRDB.framework`, a Swift SQLite library | Not checked | FACT, my bundle listing |
| **rac today** | Spaces, pins, AI settings, chat history | Prefs JSON; `<profile>/rac spaces` JSON; `<profile>/rac_ai_history.json` plaintext JSON capped at 16 MB on read; no SQLite of rac's own | Only API keys, through `os_crypt_async` and the "rac Storage Key" Keychain item | FACT `R:plans/research/rac-baseline.md:317-345` |

### Storage patterns compared

| Pattern | Example | Good at | Bad at | Fit for rac (INFERENCE) |
|---|---|---|---|---|
| Prefs and JSON files | rac today; Zed settings | Small settings; atomic writes are solved by Chromium's `ImportantFileWriter` | History, queries, growth; the whole file is rewritten | Keep for settings and spaces |
| One row per document, compressed | Zed threads | Simple, bounded, fast to list, easy to delete | Queries inside a conversation | Good first shape for agent run history |
| Normalized SQLite with retention | BrowserOS conversations and schedules | Audit logs, "what did agent X do on site Y", retention by age | Migrations to maintain | Agent runs plus one row per tool call (never per token), 30-day retention |
| Event log plus projections | T3 Code; [LiveStore](https://github.com/livestorejs/livestore) ("reactive embedded SQLite ... via event-sourcing") | Replay, undo, sync, resumable clients | Growth: storing streamed updates as permanent events filled T3 databases to tens of GB, and an offline `VACUUM` took 27 minutes (FACT `R:plans/research/t3code.md:424-433`) | Avoid for browser state. Use only for a small, bounded log, if ever |
| Server-ordered transactions | Linear: sync id order, last-writer-wins on updates, server side effects in the deltas | Consistency across many clients | Needs a server that rac does not have | Not applicable |
| CRDT documents | [Automerge 3](https://automerge.org/blog/automerge-3/) (Rust core; "cut ... memory usage by over 10x"; pasting Moby Dick went from 700 MB to 1.3 MB), Yjs (v14 in release candidates, FACT, releases API), Loro (`loro-crdt` 1.17.1, 2026-10-22, FACT) | Offline edits on several devices merged without a server | Tombstones and history to manage; more machinery than rac's data needs | Only if rac ever syncs collaboratively edited rich data |
| Sealed files in a synced folder | Ardia | No server, no account; works on iCloud Drive, Dropbox, a NAS | Slow cycle (15 s); untested on two real Macs | Best fit for syncing spaces, pins, and settings later |
| Hosted database SDK | Arc with Firestore | Easy sync | An account and a server | Breaks rac's privacy rule |

### Encryption and keys

- **Keychain-backed keys are the norm in the careful apps:** rac's `os_crypt_async` for API keys, Zed's provider keys,
  Raycast, 1Password, and Ardia's this-device-only sync key (FACT, rows above). Electron's `safeStorage` is the same idea
  for T3's desktop (FACT `R:plans/research/t3code.md:450-452`).
- **The plaintext cases are the cautionary ones:** BrowserOS provider keys and OAuth tokens in SQLite columns, closed
  "not planned" (FACT `R:plans/research/browseros.md:444-445`); T3's server secrets as files (FACT
  `R:plans/research/t3code.md:438-444`); rac's chat history as plaintext JSON (FACT `R:plans/research/rac-baseline.md:333`).
- **A sidecar that holds secrets should ask the Keychain itself, or get a key from the browser over its private
  channel.** It should never write tokens to a world-readable or discoverable file (INFERENCE).
- **Profile folders are increasingly protected by macOS.** Chrome DevTools MCP's docs report that "on recent macOS
  versions, macOS blocks other applications from reading browser profile folders under
  `~/Library/Application Support/Google/Chrome` without showing a permission prompt (TCC
  `kTCCServiceSystemPolicyAppDataDetailed`)" (FACT that the doc says so:
  `/tmp/rac-overhaul/src/chrome-devtools-mcp/docs/troubleshooting.md:65-69`). If that applies to rac's folder, an outside
  agent that reads a token or socket inside `~/Library/Application Support/me.kainoa.rac` may trigger a prompt
  (INFERENCE, not tested). A Mach name, or a socket in the per-user `$TMPDIR`, avoids the question.

### Sync and server components

- None of the patterns here needs a rac server. Zed's remote development runs over the user's own SSH connection
  (FACT `Z:docs/src/remote-development.md:223-257`). Linear and Obsidian Sync need the vendor's server (FACT, above).
- **A local service adds no network traffic by itself.** The traffic comes from features: Zed fetches the ACP registry
  from `cdn.agentclientprotocol.com` with a 30-second timeout and icons from `raw.githubusercontent.com`, and downloads
  Node from `nodejs.org` when needed (FACT `Z:crates/project/src/agent_registry_store.rs:20-25,582`;
  `Z:crates/node_runtime/src/node_runtime.rs:703`).

### Telemetry and what leaves the machine

- Zed: anonymous usage metrics and crash reports, which "you can disable in settings" (FACT `Z:docs/src/telemetry.md:8-18`).
  "All code and agent interactions stay local" for external agents (CLAIM, as reported by
  [Tessl](https://tessl.io/blog/zed-debuts-agent-client-protocol-to-connect-ai-coding-agents-to-any-editor)).
- T3 Code: analytics on by default, with an environment variable as the only off switch (FACT
  `R:plans/research/t3code.md:87`). BrowserOS: browser telemetry that "cannot be disabled through settings" (FACT
  `R:plans/research/browseros.md:494`).
- For rac (INFERENCE): a sidecar must carry the same rule as the browser: no telemetry, no update check of its own,
  and a written list of every host it may contact, reviewed the way Chromium reviews traffic annotations.

## Agents and AI

### Where the agent runs

| Product | Agent location | How tools reach it | Session lifetime | Evidence |
|---|---|---|---|---|
| Zed | Zed Agent in-process, or an external agent as a child over ACP | Zed's own MCP "context servers" are forwarded in `session/new`, stdio ones with args and env, HTTP ones with headers; ACP client methods for files and terminals | One process per agent per project, shared by threads | FACT `Z:crates/agent_servers/src/acp/v2.rs:649-683`; `Z:crates/agent_ui/src/agent_connection_store.rs:87-92` |
| Raycast | Raycast AI; MCP servers launched by Raycast (stdio) or remote (HTTP, OAuth) | MCP | Not documented | FACT, Raycast manual |
| T3 Code | Provider CLIs and SDKs under the Node server | T3's own `/mcp` and per-provider adapters | 30 idle minutes, 4 hours when pinned | FACT `R:plans/research/t3code.md:321-341` |
| BrowserOS | Agent loop in the Bun sidecar (AI SDK); neo has none | MCP over loopback HTTP | Per request | FACT `R:plans/research/browseros.md:136-149` |
| rac | Browser process (direct providers) or an ACP child | rac MCP server on a per-run Unix socket, reached with `nc -U` | One prompt; "nothing of it outlives it" | FACT `R:docs/internals/ai.md:241-272,307-332` |

### Page representation, providers, and local models

- **Page representation does not move.** In every option below, the snapshot is built in the browser from Chromium's
  AnnotatedPageContent, with refs tied to live nodes (FACT `R:docs/internals/ai.md:92-130,367-390`). A helper would only
  pass along the text a tool returns (INFERENCE). Other products' snapshot formats are in their own dossiers.
- **Providers belong to the agent.** In Zed, model choice, auth, and billing are "usually owned by the External Agent"
  (FACT `Z:docs/src/ai/external-agents.md:126-131`). A rac helper needs no LLM SDK unless direct-provider chat moves out
  of the browser, which nothing here requires (INFERENCE).
- **Local models are already local servers.** rac reaches Ollama and LM Studio through their OpenAI-compatible
  endpoints, and allows plain `http` only for localhost (FACT `R:docs/internals/ai.md:52-60`). Apple's Foundation Models
  is a framework, not a server: on-device, Private Cloud Compute, or a server provider, from macOS 26.0, Swift only
  (FACT, Apple docs JSON for `foundationmodels`).

### How Zed runs outside agents, step by step

1. **Install.** The registry (`https://cdn.agentclientprotocol.com/registry/v1/latest/registry.json`, 30 s timeout) names
   each agent as an npx package or a binary archive per platform (FACT `Z:crates/project/src/agent_registry_store.rs:20-25`).
   Binary archives are checked against a SHA-256 from the registry or from the GitHub release asset's digest, and
   unpacked into a versioned cache folder (FACT `Z:crates/project/src/agent_server_store.rs:1213-1260,1023-1111`). npx
   agents run on the system Node if it is 22 or newer, otherwise on Node v24.22.1 downloaded from `nodejs.org` (FACT
   `Z:crates/node_runtime/src/node_runtime.rs:609,703,910`).
2. **Launch.** Through the system shell, non-interactive, with literal arguments, in the project's first root, with
   Zed's proxy settings added to the environment (FACT `Z:crates/agent_servers/src/acp/transport.rs:31-80`;
   `Z:crates/agent_servers/src/agent_servers.rs:113-125`). For SSH, WSL, or container projects, the same command runs on
   the remote side through Zed's remote server (FACT `Z:crates/agent_servers/src/acp/transport.rs:43-55`;
   `Z:crates/project/src/agent_server_store.rs:821`).
3. **Lifetime.** The child dies when its connection object drops (FACT `Z:crates/agent_servers/src/acp/transport.rs:16-20`).
   Connections are kept per agent per project and shut down with the project (FACT
   `Z:crates/agent_ui/src/agent_connection_store.rs:87-120`).
4. **Protocol versions.** Zed pins `agent-client-protocol = "=3.5.0"` with `unstable_protocol_v2` and has both v1 and v2
   code paths (FACT `Z:Cargo.toml:533`; `Z:crates/agent_servers/src/acp/v1.rs`, `v2.rs`).
5. **Permissions.** The agent sends `session/request_permission`; Zed shows the offered options (allow once, allow
   always, reject once) (FACT `Z:crates/agent_ui/src/conversation_view.rs:699-729`).
6. **Sandbox.** Commands run through Zed's terminal can be wrapped in Seatbelt on macOS: writes limited to the project
   (with `.git` protected), network blocked unless approved, and approved hosts enforced through an HTTP proxy. It is
   behind a feature flag (FACT `Z:crates/agent/src/sandboxing.rs:1-25`; `Z:crates/acp_thread/src/terminal.rs:24-53`;
   `Z:docs/src/ai/sandboxing.md:55-66,193-208`). Whether an external agent's own shell tool is covered depends on
   whether it uses ACP's client terminal (INFERENCE).
7. **Configuration boundary.** Zed states plainly that model choice, auth, and native tool permissions belong to the
   agent, and Zed's permissions apply only to what Zed forwards (FACT `Z:docs/src/ai/external-agents.md:122-139`).

### What is changing in the protocols

- **MCP 2026-07-28 is stateless.** There is no `initialize` handshake; every request carries its version and client
  capabilities in `_meta`. Servers no longer send requests to clients; they return "input required" results instead
  (MRTR). Streamable HTTP dropped the GET stream and `Mcp-Session-Id` (FACT,
  [transports](https://modelcontextprotocol.io/specification/latest/basic/transports),
  [Streamable HTTP](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http)).
- **rac's MCP server speaks the older, initialize-based revisions** 2024-11-05 through 2025-11-25, defaulting to
  2024-11-05 (FACT `R:patches/rac/agent/04-mcp-server.patch:181-182,475`). New clients try the modern form first and fall
  back on a `400` whose body is not a modern error (FACT, spec "Backward Compatibility"). So rac keeps working for now,
  but every future revision is hand-written C++ (INFERENCE).
- **rac's ACP client is v1 only** (`protocolVersion` 1) (FACT `R:patches/rac/ai/20-acp-client.patch:147,318`). The
  Claude adapter already serves v1 and v2 (FACT `CAA:src/serve.ts:1-20`).
- **MCP-over-ACP would remove rac's socket for rac-launched agents.** The client declares `{"type": "acp", "serverId":
  ...}` in `session/new` and answers `mcp/message` requests on the same pipe (FACT `ACP:docs/rfds/mcp-over-acp.mdx:24-80`).
  It is an "Active" draft and targets MCP 2026-07-28 only (FACT `ACP:docs/docs.json:200-205`). Today the Claude adapter
  advertises `mcpCapabilities` `http` and `sse` only (FACT `CAA:src/acp-agent.ts:2980-2983`).
- **A cheap interim fix exists (INFERENCE).** Because the Claude adapter accepts HTTP MCP servers and ACP's HTTP server
  entry carries headers, rac could hand rac-launched agents a loopback MCP URL with an `Authorization` header inside
  `session/new`. The secret would travel on the stdio pipe, not on a command line, unlike `nc -U <socket>`, which shows
  the path in `ps` and carries no secret (FACT `R:docs/internals/ai.md:316-321`). Check Codex and Cursor support first.

### Outside-agent access: patterns and their auth

| Pattern | Example | How an agent connects | Auth | Policy | Notes |
|---|---|---|---|---|---|
| Bundled stdio bridge | Obsidian's `obsidian-cli` inside the app bundle is the closest model (FACT, Obsidian help) | Agent config runs a command, such as `rac mcp` | Pairing in the app; the bridge's code signature can be checked from the socket's audit token | In the app | No TCP port, so no DNS rebinding, no `Origin` checks, no Local Network Access prompt (INFERENCE) |
| Loopback HTTP with a bearer key | Obsidian Local REST API (`https://127.0.0.1:27124/mcp/`, name-constrained local CA) | `claude mcp add --transport http ...` | Bearer key | Plugin | Needs `Origin` and `Host` checks to be safe (FACT, MCP spec) |
| Loopback HTTP with OAuth 2.1 and PKCE | T3 Code `/mcp` | `mcp login` flows | OAuth, pairing code, 30-day sign-ins, read-only default | Server | Heaviest to build (FACT `R:plans/research/t3code.md:528-534`) |
| Loopback HTTP, no auth | BrowserOS MCP on port 9000 | URL | None; loopback check only | Sidecar | Any local process can drive it (FACT `R:plans/research/browseros.md:149`) |
| CDP with a token | Ardia, token in a 0600 file, about 70 allowed methods | `ardia` CLI | Token, constant-time compare, any `Origin` refused | One switch, no per-site rules | Page-script power in every tab (FACT `R:plans/research/ardia.md:400-424`) |
| CDP with per-connection approval | Chromium 144+ `chrome://inspect` mode, used by `chrome-devtools-mcp --autoConnect` | Agent reads `DevToolsActivePort` | Click Allow per connection | None | Full browser power, outside rac's guard (FACT `/tmp/rac-overhaul/src/chrome-devtools-mcp/docs/advanced-usage.md:50-75`) |
| XPC relay in a login item | 1Password CLI | CLI binary | Code signatures on both ends, Touch ID per terminal, 10-minute rolling session, 12-hour cap | App | Strongest local model found (FACT, 1Password docs) |

### Local auth for local servers: a checklist distilled from the evidence

1. **No listening TCP port unless a client truly needs one.** Every outside agent rac targets can run a stdio MCP
   command (CLAIM for Claude Code, [docs](https://docs.anthropic.com/en/docs/claude-code/mcp); the Obsidian REST API
   README shows both forms).
2. **Unix socket hygiene, plus identity.** Keep rac's 0700 folder, 0600 socket, and UID check (FACT
   `R:docs/internals/ai.md:312-325`). Add `LOCAL_PEERTOKEN` and `base::mac::ProcessIsSignedAndFulfillsRequirement` so
   only rac's own signed bridge can connect (FACT for the APIs: SDK `sys/un.h:93`; `CR:base/mac/code_signature.h:31-39`).
   Development builds are ad-hoc signed, so they need a same-UID fallback that the UI labels (INFERENCE; Chromium's app
   shim code has the same unsigned case, `CR:chrome/browser/apps/app_shim/app_shim_manager_mac.cc:161-172`, which skips the check when the browser itself is unsigned or ad-hoc signed).
3. **Pair each agent once, with a card that names it.** The bridge reports the program that launched it; rac shows its
   name, path, and signing team, with "Allow for this session", "Always allow", and "Don't allow" (INFERENCE, modeled
   on 1Password and Chrome's DevTools dialog above).
4. **Secrets never on a command line or in a guessable file.** Use the pipe, an inherited descriptor (T3's fd 3), or
   the Keychain (FACT for T3: `R:plans/research/t3code.md:261-266`).
5. **If HTTP is ever needed:** bind `127.0.0.1` and `::1` only; reject a present but unexpected `Origin` with 403; check
   `Host` exactly; require a bearer token; send no CORS headers (FACT for the MCP rules; INFERENCE for the rest).
   Chromium's Local Network Access prompt protects only pages inside Chromium browsers, not Safari (INFERENCE).
6. **Remember that a same-user attacker is the threat model on a Mac, and macOS raises the bar.** Hardened runtime
   with library validation blocks code injection into rac's own processes (FACT: Helium's helpers are signed with
   `kill,restrict,library-validation,runtime`, my `codesign -dv` of `/Applications/Helium.app`). A door that any
   same-user process can open without a check is then the weakest link (INFERENCE).

### Remote access

| Option | How it works | What leaves the machine | Fit for rac (INFERENCE) |
|---|---|---|---|
| None (default) | Loopback and stdio only | Nothing | Default |
| Tailscale Serve to a loopback port | The user's Tailscale proxies `https://<device>.<tailnet>.ts.net` to `http://127.0.0.1:<port>` and adds `Tailscale-User-Login` and `Tailscale-User-Name`, stripping spoofed copies; Funnel (public) adds no identity headers; needs tailnet HTTPS certificates | Traffic over the user's tailnet; Tailscale's coordination server | Best option for "control rac from my phone", opt-in, with an allowlist of logins plus pairing (FACT, [Tailscale Serve](https://tailscale.com/kb/1312/serve)) |
| Embedded Tailscale (`tsnet`, or `libtailscale` built from Go as a C archive, with Swift bindings in the repo) | rac becomes its own tailnet node | Same, plus a Tailscale login inside rac | Only in a Go sidecar; adds a third-party account flow (FACT, [libtailscale](https://github.com/tailscale/libtailscale) README and file list) |
| iroh (Rust) | "Dial keys instead" of IPs: QUIC with NAT traversal and relays | Relay traffic via n0's relays unless self-hosted (INFERENCE) | Interesting for a Rust sidecar; v1.4.1 shipped 2026-10-22 (FACT, releases API) |
| Cloud tunnel and relay | T3 Connect: Clerk accounts, Cloudflare tunnels, push through a relay | Titles and status via the relay (FACT `R:plans/research/t3code.md:456-468`) | Breaks rac's rules |
| SSH | Zed remote development | The user's SSH | Developer-only; not a browser feature |
| LAN listening | T3's background service listens on LAN and Tailscale addresses by default | LAN | Avoid as a default |

### Prompt injection and containment

- **The guard stays in the browser.** None of these architectures changes rac's known gap at the `auto` level, where
  cross-site navigation plus typing model-written text needs no card (FACT, brief and
  `R:patches/rac/agent/13-permission-levels.patch`). That is a policy fix, not a process-model fix (INFERENCE).
- **Seatbelt for agent processes is the transferable idea.** Zed blocks the network by default for sandboxed commands
  and routes approved hosts through a proxy (FACT, above). rac could launch each ACP agent under a Seatbelt profile that
  allows writes only to its scratch folder and network only to a local proxy that forwards to the agent's provider
  hosts (INFERENCE). `/usr/bin/sandbox-exec` ships on macOS 26.6.2 but its man page is titled "(DEPRECATED)" (FACT, my
  check). Codex and Zed still rely on Seatbelt (FACT for Zed; FACT for Codex from file names via GitHub code search:
  `openai/codex` `codex-rs/sandboxing/src/seatbelt.rs` and `seatbelt_base_policy.sbpl`).
- **Untrusted framing and short outputs** are covered in the T3 dossier (`R:plans/research/t3code.md:670-676`).

### Skills and automations

- Skills: Ardia installs a `SKILL.md` for Codex, Claude Code, Cursor, and OpenCode (FACT `R:plans/research/ardia.md:422`);
  Aside does the same (brief). For rac, a `rac skills install` command fits the bridge (INFERENCE).
- Automations need a clock. While rac runs, a browser timer is enough. While rac is closed, only a launch agent can
  run them, with Login Items approval and a "Background Items Added" notice (FACT for macOS behavior, above). T3's
  webhooks need its relay to be public (FACT `R:plans/research/t3code.md:535-540`).

## Build, release, and engineering

### Signing and notarizing a helper inside a Chromium app

- **rac signs with Chromium's own pipeline.** `sign_and_package_app.sh` runs `sign_chrome.py --notarize` with the
  Developer ID identity (FACT `R:sign_and_package_app.sh:26-33`). That pipeline signs only the parts listed in
  `chrome/installer/mac/signing/parts.py`, each with options and an optional entitlements file (FACT
  `CR:chrome/installer/mac/signing/parts.py:39-161`).
- **Helium already shows how to add a binary.** Its signing patch adds Sparkle's `Autoupdate` and `Updater.app` to
  `parts.py` with `FULL_HARDENED_RUNTIME_OPTIONS` (FACT `R:patches/helium/macos/chromium-signing.patch:1-20`). A rac
  helper needs one more entry of the same kind, in a file Helium already patches, so one small, separate hunk
  (INFERENCE).
- **Apple's notarization rules apply to every executable:** Developer ID signature, Hardened Runtime, a secure
  timestamp, and no `get-task-allow` (FACT, Apple "Notarizing macOS software before distribution" via
  `developer.apple.com/tutorials/data/documentation/security/notarizing-macos-software-before-distribution.json`).
- **JavaScript runtimes need weaker code-signing settings.** Bun's docs tell you to sign compiled executables with
  `allow-jit`, `allow-unsigned-executable-memory`, `disable-executable-page-protection`,
  `allow-dyld-environment-variables`, and `disable-library-validation`, and codesign support "requires Bun v1.2.4 or
  newer" (FACT, [Bun executables](https://bun.com/docs/bundler/executables)). What shipping products actually use
  (FACT, my `codesign -d --entitlements` on 2026-10-25):

| Binary | Runtime | Hardened Runtime | Entitlements |
|---|---|---|---|
| Claude Code 2.1.310 | Bun-compiled | yes | `allow-jit`, `allow-unsigned-executable-memory`, `disable-library-validation`, plus Apple Events and microphone |
| opencode | Bun-compiled | yes | `allow-jit`, `allow-unsigned-executable-memory`, `disable-executable-page-protection`, `allow-dyld-environment-variables`, `disable-library-validation` |
| codex 0.164.0 | Rust | yes | `allow-jit`, `allow-unsigned-executable-memory` (reason not checked; it ships a separate 68.5 MB `codex-code-mode-host`) |
| T3 Code (Nightly) | Electron | yes | `allow-jit`, `allow-unsigned-executable-memory`, `disable-library-validation`, camera, microphone |
| Helium.app (browser) | Chromium | yes, flags `kill,restrict,library-validation,runtime` | none of the JIT ones |
| Helium Helper (Renderer) | Chromium | yes, `kill,restrict,runtime` | `allow-jit` only |
| Helium Helper (utility) | Chromium | yes, `kill,restrict,library-validation,runtime` | none |

  INFERENCE: a Rust, Go, Swift, or Chromium-built helper can be signed like Helium's utility helper, with library
  validation on and no JIT. A Bun or Node helper cannot. The helper that brokers browser tools would then be the
  least-hardened process in rac.

- **Launch constraints** can stop other apps from launching rac's helper (see Architecture). `codesign` embeds them
  with `--launch-constraint-self`, `--launch-constraint-parent`, and `--launch-constraint-responsible`, each taking a
  plist (FACT, `man codesign` on macOS 26.6.2). They are enforced from macOS 13.3 for launch constraints and from
  Sonoma for library constraints (CLAIM, WWDC23 10266). Chromium's signing scripts never mention them (FACT: no match for
  "launch constraint" in `CR:chrome/installer/mac/signing/*.py`), so using them needs a small change to rac's signing
  step (INFERENCE).

### Building a helper in CI

- rac's release build has never finished: a chain of 6-hour phases, each of which restarted siso from step zero; a tar
  format fix (PR #20) was being validated on 2026-10-25 (FACT `R:plans/context/ci-status.md`; brief). CI never compiles rac's 284 unit tests (FACT, brief).
- A cargo, Go, or Bun helper builds in minutes in its own job, runs its own tests there, and is copied into
  `out/Default/rac.app` before `sign_chrome.py` runs (INFERENCE). This is the one part of rac whose tests CI could run
  on every pull request from day one.
- Development loop: a worktree `he build` takes minutes (FACT, `R:AGENTS.md`, "Worktrees"). A helper rebuilds in
  seconds and restarts without restarting the browser (INFERENCE; I built nothing).
- Version lock: Zed refuses a remote server whose version differs from Zed's by even the commit (FACT
  `Z:docs/src/remote-development.md:243`). rac's browser and helper ship in one bundle, so the private protocol can
  require an exact build id and avoid compatibility code (INFERENCE).

### Updates

- **Keep one update channel.** rac's Sparkle feed URL and signing key must never change (FACT `R:AGENTS.md`, rule 6).
  The helper should update only inside app updates. BrowserOS's separate sidecar feed, checked every 15 minutes, is a
  second channel and a second phone-home (FACT `R:plans/research/browseros.md:339-346`).
- Size matters for updates: Helium.app is 341 MB on disk here (FACT, `du -sh`). rac already has a Sparkle delta script
  (FACT `R:devutils/generate_sparkle_deltas.py`). An unchanged runtime inside the helper should delta well (INFERENCE).

### Tests

- **MCP conformance tests exist:** `modelcontextprotocol/conformance` (136 stars, updated 2026-10-19) (FACT, API). rac's
  MCP server, in C++ or in a helper, could run them in CI (INFERENCE).
- **ACP's TCK tests agents, not clients** (FACT, `agentclientprotocol/acp-tck` description). For rac's client side,
  Zed's approach is a fake ACP agent harness in test support (FACT `Z:crates/agent_servers/src/agent_servers.rs:20-24`).
- Replay fixtures through the real controller and guard are covered in the T3 dossier (`R:plans/research/t3code.md:690-693`).

### Tracking upstream protocols

- Zed pins the ACP crate to an exact version (`=3.5.0`) and carries v1 and v2 code paths side by side (FACT
  `Z:Cargo.toml:533`; `Z:crates/agent_servers/src/acp/`). The Claude adapter picks v1 or v2 from the client's
  `initialize` (FACT `CAA:src/serve.ts:1-20`). T3 negotiates features by advertised capabilities, never by version
  (FACT `R:plans/research/t3code.md:294-296`).
- For rac (INFERENCE): protocol churn (MCP, ACP) and engine churn (Chromium, Helium) move at different speeds. Code that
  speaks MCP and ACP in a helper can take a dependency bump in a day; the same change in a rac patch waits for a
  Chromium build and touches the patch stack that the Helium sync must carry.

### Runtime comparison for a rac helper

All "measured" values are mine, on this Mac, warm, 2026-10-25. Startup includes about 4 ms of shell spawn.

| | **Bun 1.4 (TypeScript)** | **Node 24 or 26 (TypeScript)** | **Rust** | **Go** | **Swift** | **C++ inside Chromium** |
|---|---|---|---|---|---|---|
| Binary on disk | Runtime 63.6 MB (Bun 1.4.0). Real compiled apps: opencode 180.8 MB, Claude Code 274.1 MB (measured) | Official `node`: 116.9 MB (v24.5.0), 121.3 MB (v24.19.0), 145.8 MB (v26.8.1) (measured); a single-executable app adds its code | Small tools: T3's `t3-resource-monitor` 0.58 MB; 1Password's browser support host 8.4 MB. Large app: codex 260.3 MB (measured) | tailscale CLI 16.4 MB, tailscaled 23.3 MB, cloudflared 39.4 MB, gh 40.0 MB (measured) | Not measured for a small helper; cua-driver is 80.7 MB (large app) | Nothing new; code joins the browser framework |
| Startup | 7.2 ms for a trivial script (measured); Bun reports bytecode builds start "2x faster" (CLAIM) | 35 to 37 ms (measured) | `codex --version` 13.8 ms (measured) | `tailscale version` 10.7 ms; `gh --version` 50.4 ms (measured) | Not measured | None |
| Idle memory | Minimal `node:http` server: 22.5 MB RSS, 10.0 MB footprint (measured); third-party: 23 MB on `node:http`, 16 MB on `Bun.serve` (CLAIM, [DEV](https://dev.to/fabwaseem/bun-vs-nodejs-in-2026-bun-14-vs-node-24-and-26-benchmarked-4pab)) | Minimal `node:http` server: 54.3 MB RSS and 19.7 MB footprint on v24.21; 67.0 MB and 21.4 MB on v26.8 (measured) | `t3-resource-monitor` 5.1 MB RSS, 2.7 MB footprint; 1Password browser helper 10.1 MB RSS, 8.6 MB footprint (measured) | tailscaled 34.5 MB RSS; cloudflared 43.3 MB RSS, both busy daemons (measured) | cua-driver 14 to 16 MB RSS (measured) | In the browser process; a new utility process would cost 16 to 38 MB like Helium's helpers (measured) |
| Memory in real use | Not measured for Bun | T3 Code server (Electron as Node): 323 MB footprint after 22 h (measured); Raycast v2 Node backend: 150 to 200 MB (CLAIM) | Not measured; BrowserOS moved its server to Rust for neo (FACT) | tailscaled and cloudflared above are real daemons | Not measured | In the browser process |
| MCP SDK | Official TypeScript SDK, v2.4.0 on 2026-10-23 (FACT, releases API) | Same | Official `rmcp` 3.7.0, 2026-10-22 (FACT) | Official `go-sdk` v1.8.0, "maintained in collaboration with Google" (FACT) | Official `swift-sdk` 0.12.1, 2026-05-07, slower cadence (FACT) | None; rac's own C++ server |
| ACP SDK | Official `@agentclientprotocol/sdk` (FACT `ACP:docs/libraries/typescript.mdx`) | Same | Official crate; Zed's own client uses it (FACT `Z:Cargo.toml:533`) | Community only, such as `coder/acp-go-sdk` (FACT `ACP:docs/libraries/community.mdx:36-44`) | Community only (FACT, same file `:58-62`) | Community `acp-cpp` only; rac's own v1 client |
| LLM SDKs | Richest: AI SDK 7 (`ai@7.0.153`, 2026-10-24), Claude Agent SDK, OpenAI SDK and Agents SDK (FACT, releases and org listings) | Same | No official Anthropic or OpenAI SDK (FACT, org repo listings) | Official `anthropic-sdk-go` and `openai-go` (FACT) | None official; Apple's Foundation Models framework (on-device, Private Cloud Compute, or a server provider) is Swift-only (FACT, Apple docs JSON, macOS 26.0+) | rac's own providers in C++ |
| Signing | JIT entitlements, see table above | JIT entitlements | Like a Chromium utility helper | Like a utility helper | Like a utility helper; native XPC and `SMAppService` | Nothing new |
| License fit with GPL-3.0 | Bun is MIT and statically links JavaScriptCore under LGPL-2, which asks that users can relink (FACT, [Bun licensing](https://bun.com/docs/project/licensing)); fine for open-source rac (INFERENCE) | MIT, with OpenSSL under Apache-2.0, which GPL-3.0 accepts (INFERENCE) | MIT or Apache-2.0 crates; Zed's GPL-3.0 code can be reused with credit (INFERENCE) | BSD-3; Tailscale BSD-3 | Apache-2.0 | BSD-3 |
| Build | `bun build --compile`, seconds | Node SEA tooling, then re-sign | cargo, minutes, outside GN | `go build`, seconds | swiftc or Xcode | Every change is a Chromium rebuild |

Reading the table (INFERENCE):

- **Footprint at rest:** Rust under 10 MB, Bun about 10 to 25 MB, Node about 20 to 70 MB. All are small next to the
  agents they would host: two long-running Claude Code CLI sessions on this Mac were 705 MB and 1.09 GB RSS (measured, `ps`; an idle ACP
  adapter would likely use less, not measured).
- **Hardening:** only the JS runtimes need JIT and, in practice, `disable-library-validation`.
- **Ecosystem:** TypeScript is richest. Rust has both official protocol SDKs (MCP and ACP), which is what a broker
  needs; LLM calls can stay in the browser.
- **Precedent:** BrowserOS rewrote its Bun sidecar in Rust for neo; Zed (Rust, GPL-3.0) is reusable reference code.
  T3 (Node) and Raycast v2 (Node) are the memory warnings.

## Strengths and weaknesses (critical)

| Pattern | Strengths | Weaknesses |
|---|---|---|
| **Zed: one child per agent over stdio** | No ports at all. Lifetime is obvious: the child dies with its connection. Threads share one warm process, so follow-ups are fast. Installs are hash-checked (FACT, above) | Each warm agent is a large process (two long-running Claude Code sessions here: 705 MB and 1.09 GB RSS, measured). The full ACP client grew to about 55,000 lines (FACT). The registry is a fetch from a third-party CDN (FACT). The sandbox is still behind a flag (FACT) |
| **Raycast v1: one Node child, a V8 isolate per extension** | A crash or heap blow-up stays in one worker; a thin RPC limits what extensions can ask (FACT) | Extensions are "not further sandboxed" for files and network (FACT). Node was downloaded on first use (FACT) |
| **Raycast v2: always-on Node backend under a web UI** | Features built once for two platforms; typed interfaces "defined once" across four runtimes (CLAIM) | 350 to 450 MB at rest, up from 200 to 300 MB; cold windows open with a delay; four runtimes to debug (CLAIM) |
| **Obsidian: CLI that remote-controls the running app** | One switch; a native binary in the bundle; full app power; launches the app on demand (FACT) | No documented authentication, while `eval` and `dev:cdp` exist; registration needs an admin password; plugins are unsandboxed (FACT) |
| **Linear: server-ordered sync** | Simple ordering by sync id; last-writer-wins; transactions double as undo (FACT, study) | Needs a vendor server; local data is a cache of the server's truth (INFERENCE) |
| **T3 Code: local server, thin clients** | One contract for every client and agent; capability negotiation; remote clients for free (FACT, T3 dossier) | 323 MB footprint (measured); multi-GB database growth; analytics on by default; a relay with accounts (FACT, T3 dossier) |
| **BrowserOS: always-on sidecar over CDP** | Crash isolation; supervision with strikes and fallback; the agent can ship daily without a browser build (FACT) | Starts on every launch with no off switch; a loopback CDP port; an MCP endpoint with no token; plaintext keys; a second update feed (FACT, BrowserOS dossier) |
| **Electron `utilityProcess` and Tauri sidecars** | Mature, documented spawn models; Tauri checks each argument against an allowlist (FACT) | JS helpers need JIT entitlements; Tauri's docs say nothing about signing sidecars (FACT) |
| **Chromium utility process with Mojo** | Typed IPC; real sandbox types; idle kill; crash isolation; no new signing work (FACT) | C++ only; each process 16 to 38 MB (measured); Mojo clients outside the tree must link Chromium (FACT) |
| **Chromium app-shim pattern (Mach name, audit token, code signature)** | The strongest same-machine identity check available, already in rac's tree (FACT) | The client must be built from Chromium's tree to speak Mojo; ad-hoc dev builds skip the check (FACT) |
| **XPC service** | Private to the app; launchd starts it on demand and restarts it after crashes; per-service sandbox (FACT, Apple) | Killed when idle, so it suits stateless work; outside agents cannot connect (FACT, Apple) |
| **Launch agent through `SMAppService`** | Runs while rac is closed; managed by launchd (FACT) | Login Items entry, a "Background Items Added" notice, user approval; looks like persistence to wary users (FACT, CLAIM) |
| **Loopback HTTP** | Every MCP client supports it; phones and hosted tools can reach it through a tunnel (FACT) | DNS rebinding and cross-site requests unless `Origin`, `Host`, and a token are all checked; Local Network Access helps only inside Chromium browsers (FACT for MCP rules; INFERENCE for the rest) |
| **Event log or CRDT storage** | Replay, undo, offline merge (FACT) | Growth and compaction work; T3's tens of GB (FACT); more machinery than rac's small records need (INFERENCE) |

Critical notes on rac itself (INFERENCE unless marked):

- rac's per-run design is principled ("nothing of it outlives it", FACT `R:docs/internals/ai.md:243`) but is the main
  reason agents feel slow: 15 to 25 s per message (FACT `R:docs/internals/ai.md:707-716`).
- rac's MCP door is weaker than the rest of rac: any same-user process can connect during a run, there is no secret,
  and the socket path is visible in `ps` (FACT `R:docs/internals/ai.md:316-321`).
- Protocol upkeep is the hidden cost of C++: MCP moved to a stateless revision in 2026-07-28 and ACP is drafting v2,
  while rac hand-maintains both (FACT, above).
- A helper process does not fix the `auto`-level exfiltration gap. Only a policy change does (FACT, brief).

## What rac should take (ranked, concrete, with rough cost) and what rac should avoid

Cost scale for one maintainer directing agents: **S** about 1 to 3 days, **M** about 1 to 2 weeks, **L** 3 weeks or more.
All costs are INFERENCE.

### In plain English (at most 200 words)

Today rac's agent tools open only for an agent that rac itself starts. They close when its answer ends. The plan
below opens a second door, for agents you already use, like Claude Code in Terminal. That door is a small command
inside rac.app. Your agent runs it, and rac shows one card: "Claude Code wants to use rac." You choose how much it may
do. Risky steps still ask, as they do now. Nothing listens on the network. When the setting is off, nothing runs.
Next, rac keeps an agent awake while its panel is open, so a follow-up takes a few seconds, not up to 25. Later, if
automations or history grow, rac can move this work into a helper program. The helper never decides what is
allowed. The browser still decides. A Rust helper is the safest and smallest choice. TypeScript is the fastest to
write but needs looser security settings and more memory. Phone access, if ever, goes only through your own
Tailscale. Sync, if ever, goes through your own iCloud folder.

### Take

1. **Keep every permission decision in the browser, and give it one rac-owned contract.** Define a small JSON-RPC
   "browser tools" interface (list tools, call a tool with caller identity, stream events, ask for a card) in rac-owned
   files. The in-browser MCP server, the outside-agent door, and any future helper all call
   `AgentController::HandleToolCall` through it, never around it (FACT for today's rule: `R:docs/internals/ai.md:326-332`).
   The contract is rac's, so it does not churn with MCP or ACP revisions. Cost **S to M**.
2. **Ship the outside-agent door as a bundled stdio command, with no TCP port.** A signed `rac` binary in `rac.app`
   (for example `Contents/Helpers/rac`), linked into `~/.local/bin` so no admin prompt appears. Agents add it with a
   command such as `claude mcp add rac -- rac mcp`. A setting "Let other apps' agents use rac", off by default and
   independent of the AI switch, makes the browser listen on a per-user socket or Mach name only while on. The browser
   checks the peer's audit token against rac's code-signing requirement, then shows a pairing card naming the program
   that launched the bridge. Each agent gets a level (read-only, `ask`, `careful`, `auto`), and the risky list always
   asks. Settings lists agents with last use and Revoke. Sessions expire like 1Password's (10 minutes rolling, 12-hour
   cap) unless "Always allow" was chosen. Cost **M**. Evidence: Obsidian CLI, 1Password, Chrome's DevTools dialog,
   `R:plans/context/roadmap-revision-2026-10-22.md:79-80` ("Design this before the rest of the agent work").
3. **Keep a rac-launched agent warm while its panel is open.** One process per agent per profile, reused across
   messages as Zed does; exit after 5 idle minutes and when the panel closes; at most one or two warm agents, because
   each can hold hundreds of MB (two long-running Claude Code sessions here: 705 MB and 1.09 GB RSS, measured). This changes the "a run is one prompt" rule, which the maintainer must
   approve (FACT `R:docs/internals/ai.md:243-250`). Cost **S to M**.
4. **Give rac-launched agents a secret-bearing MCP channel.** Short term: a loopback MCP URL with a random bearer
   header passed inside `session/new`, for agents whose adapters accept HTTP servers (Claude's does, FACT
   `CAA:src/acp-agent.ts:2980-2983`). Keep `nc -U` only for agents that need stdio. Long term: MCP-over-ACP, once
   adapters support it (FACT `ACP:docs/rfds/mcp-over-acp.mdx`). Cost **S**.
5. **Store agent history in SQLite with bounded growth.** One row per run and one per tool call (never per token),
   30-day retention, message text encrypted with a Keychain-backed key like API keys are. In the browser that is
   Chromium's `sql::Database` with WAL (FACT `CR:sql/database.h:113-227`); in a helper, SQLite through Rust. It also
   becomes the audit log outside agents need. Cost **S to M**.
6. **Run ACP agents inside a Seatbelt profile.** Writes only to the scratch folder and the agent's own config;
   network only through a local proxy that allows the provider's hosts. This is a second wall behind the per-agent
   recipes, as Zed does for terminals (FACT `Z:docs/src/ai/sandboxing.md:193-208`). Test each agent; `sandbox-exec` is
   marked deprecated (FACT). Cost **M**.
7. **If a helper is built, write it in Rust, sign it like Chromium's utility helper, and constrain its launch.**
   Use `rmcp` and the official ACP crate; borrow from Zed's GPL-3.0 ACP client and sandbox code with credit. Add one
   `parts.py` entry and a launch constraint that requires rac.app as parent. Build and test it in its own CI job. Cost
   **L** for the helper; **S** for signing and CI.
8. **Update the protocols on purpose.** Run the MCP conformance suite against rac's server; plan support for MCP
   2026-07-28 and ACP v2 (FACT, above). Cost **S** each.
9. **Offer `rac skills install`** for Claude Code, Codex, Cursor, and OpenCode, as Ardia and Aside do (FACT
   `R:plans/research/ardia.md:422`). Cost **S**.
10. **Phone or remote control, later, only through the user's Tailscale Serve to a loopback endpoint**, with a login
    allowlist and pairing (FACT for Tailscale behavior, above). Cost **M**.
11. **Sync, later, through sealed files in a user-chosen folder**, Ardia's model, before any CRDT (FACT
    `R:plans/research/ardia.md:359-378`). Cost **L**.
12. **Optional: an on-device model through a tiny Swift XPC helper** using Apple's Foundation Models (macOS 26+, Apple
    Intelligence Macs) for link summaries and the critic, with no setup and no network (FACT for the framework; the
    helper design is INFERENCE). Restrict it to the on-device model, since Private Cloud Compute leaves the Mac. Cost **M**.

### Avoid

1. **An always-on helper.** BrowserOS, Raycast v2, and T3 pay hundreds of MB for it (FACT, above). rac's rule is that a
   feature that is off does no work (FACT `R:VISION.md:44-47`).
2. **Listening on `0.0.0.0`, on LAN by default, or on loopback without a token** (FACT: BrowserOS and T3 behaviors above).
3. **A second update channel for the helper** (FACT: BrowserOS's 15-minute feed). One Sparkle feed only.
4. **Event-sourcing browser state or saving streamed tokens** (FACT: T3's growth).
5. **Raw CDP as the outside-agent API.** It bypasses the guard, cards, and site rules (FACT: Ardia allowlist; Chromium
   approval mode).
6. **A JavaScript runtime in the process that brokers browser tools,** unless the maintainer accepts JIT and
   library-validation exceptions (FACT: entitlement table).
7. **Plaintext secrets in SQLite or files** (FACT: BrowserOS, T3).
8. **Registering a launch agent by default.** Only an explicit "run automations while rac is closed" switch justifies it.
9. **Thin web clients talking to the helper over WebSocket.** Keep rac's WebUI talking to the browser, which talks to
   the helper (INFERENCE; avoids a listening socket).
10. **Downloading runtimes on first use** (Zed's Node, Raycast v1's Node). It adds a network call and hits the
    quarantine trap; bundle instead (FACT for both behaviors, above).
11. **Cloud relays and accounts** for remote access (FACT: T3 Connect needs Clerk and Cloudflare).

### Options table for rac

All options keep tabs, spaces, windows, the guard, and the cards in the browser process. "Off" means the user has not
turned the feature on.

| Option | What it is | New binary | Cost when off | Cost when on, at rest | Dev loop | Protocol upkeep | Security | Upstream merge cost | Effort | Verdict (INFERENCE) |
|---|---|---|---|---|---|---|---|---|---|---|
| **O1. Door in the browser (C++)** | Today's MCP server made long-lived and opt-in, plus a tiny bundled bridge (Unix socket with audit-token check, or Mach name like app shims) | A small C++ bridge built in tree | None | A listening socket; no process | Chromium rebuild per change | Hand-written MCP and ACP | Good: policy in place, signed bridge | Low: new files plus `parts.py` | **M** | **Do first** |
| **O2. Utility-process service (C++ Mojo)** | Move the ACP client and MCP server into a `ServiceProcessHost` process (`kNoSandbox` to spawn agents) with an idle handler | None (a Chromium helper) | None | 16 to 38 MB | Chromium rebuild | Hand-written | Crash isolation; same policy | Low to medium | **M** | Only if crashes in agent parsing become a real problem |
| **O3. Rust helper ("agent host")** | `rac-agentd` launched lazily by the browser over an inherited socket; owns ACP agents, the outside-agent MCP door, history, schedules; doubles as the `rac` CLI | Yes, about 2 to 10 MB (estimate) | None | About 5 to 15 MB | Seconds; restart without the browser | Official `rmcp` and ACP crate | Strong: no JIT, library validation, launch constraint | Low | **L** | **Best long-term shape** if agent work keeps growing |
| **O4. TypeScript helper (Bun)** | Same as O3 in TypeScript | Yes, 64 MB or more | None | About 10 to 25 MB (Bun), more under load | Seconds | Official TS SDKs, AI SDK, Claude Agent SDK | Weaker: JIT and library-validation exceptions | Low | **M to L** | Choose only if the helper must run TypeScript skills or automations |
| **O5. Swift XPC helper** | A private, stateless service for Apple-only APIs (Foundation Models, `SMAppService`) | Yes, small (estimate) | None | Launched on demand, killed when idle | Seconds | Official MCP Swift SDK lags | Strong; private to the app | Low | **M** | Add only for an on-device model |
| **O6. Background service (launch agent)** | O3 or O4 registered with `SMAppService.agent` so it runs while rac is closed | Same as O3 or O4 | None if never registered | Always running once approved | As O3 or O4 | As O3 or O4 | Login Items approval; visible notice | Low | **S** on top of O3 | Only for "automations while closed" or phone access |
| **O7. Be a target only** | Ship O1's door and let T3 Code, Claude Code, or Codex be the "server" for history and schedules | As O1 | None | As O1 | As O1 | As O1 | As O1 | Low | **S to M** | A fine stopping point if automations stay out of scope |

| Remote access | Verdict (INFERENCE) |
|---|---|
| R0. None | Default |
| R1. Tailscale Serve to a loopback endpoint in O1 or O3, login allowlist plus pairing | The only acceptable remote option found |
| R2. Embedded `tsnet` (Go) or iroh (Rust) | Possible inside a helper; adds a third-party login or relay |
| R3. Cloud relay or tunnel | Reject |

| Storage | Verdict (INFERENCE) |
|---|---|
| S0. Prefs and JSON files | Keep for settings, spaces, and pins |
| S1. SQLite: runs and tool calls, retention, encrypted text | Adopt for agent history and audit |
| S2. Event log | Reject for browser state |
| S3. CRDT documents | Defer until rac syncs collaboratively edited rich data |
| S4. Sealed files in a user folder | Adopt when sync is scheduled |

A suggested order (INFERENCE): take items 1, 4, and 2 (O1 plus a signed bridge), then 3 and 5, then decide between
O7 and O3 once the maintainer knows whether automations and long-lived agent history are wanted.

## Open questions and things you could not verify

- **macOS "App Data" prompts.** Does reaching a socket or reading a file inside `~/Library/Application Support/me.kainoa.rac`
  from an agent started in Terminal trigger a privacy prompt, as Chrome DevTools MCP reports for Chrome's folder? Not
  tested. If yes, the rendezvous must live in `$TMPDIR` or be a Mach name.
- **Minimum entitlements for a Bun helper.** Bun's docs list five exceptions; Claude Code ships with three of them
  (plus Apple Events and microphone). I did not test which are truly required for a Bun binary under Hardened Runtime.
- **Which adapters accept an HTTP MCP server with headers.** Verified only for the Claude adapter
  (`CAA:src/acp-agent.ts:2980-2983`). Codex, Cursor, Gemini, OpenCode, Copilot, and Goose are unchecked.
- **Nested sandboxes.** Codex and some agents apply their own Seatbelt profile. macOS may refuse a second profile inside
  a sandboxed process, which would break those agents under a rac Seatbelt wrapper. Not tested.
- **rac's remote-debugging behavior.** The default-profile refusal is a Google-branding check (FACT,
  `CR:chrome/browser/devtools/remote_debugging_server.cc:168-180`). I did not check whether Helium or
  ungoogled-chromium patches change it, or whether `chrome://inspect` approval mode is reachable in rac. Test in a dev
  profile only.
- **Local Network Access in rac.** I did not confirm that Helium leaves Chromium's LNA enforcement on.
- **Obsidian CLI transport and authentication** are undocumented. A third-party guide reports `~/.obsidian-cli.sock`.
- **Raycast v2 details:** bundle size of its Node runtime, its database format, and startup numbers are not published.
- **Linear facts** come from an unofficial reverse-engineering study of 2024 to 2025 code; the shipping engine may differ.
  Team size and cadence not checked.
- **Rust and Go minimal-server numbers** are from existing binaries on this Mac, not from a minimal server, because I
  compiled nothing. A minimal `tokio` plus `axum` server's size and memory are estimates.
- **Cold start.** All startup numbers are warm. First launch after install adds Gatekeeper's check, which I did not measure.
- **XPC lifetime with open connections.** Apple's archive doc says idle services are killed; whether an XPC service with
  a live connection and long agent sessions stays up reliably is untested.
- **Launch-constraint versions.** Enforcement from macOS 13.3 and Sonoma comes from WWDC23 and Eclectic Light, not from
  Apple's reference page.
- **Protocol timelines.** When ACP v2, ACP's remote transport, and MCP-over-ACP become stable is unknown; all are
  "Active" drafts on 2026-10-25.
- **Launch constraints in Chromium's signing pipeline.** The scripts have no option for them (FACT, grep). Whether a
  rac patch can pass `--launch-constraint-parent` for one part without touching shared code is unverified.
- **Identifying the agent behind the bridge.** The bridge's parent may be a shell or an npx wrapper, not the agent's
  signed binary. How reliably a pairing card can name "Claude Code" needs a prototype.
- **Apple Foundation Models from a Chromium app.** Whether an XPC helper inside rac.app can use it without extra
  entitlements, and whether the on-device model is good enough for summaries and the critic, are untested.
- **The `auto`-level exfiltration gap** remains open and is independent of every option here (FACT, brief).

## Sources

Code and repositories (read-only clones under `/tmp/rac-overhaul/src`):

- Zed: https://github.com/zed-industries/zed (commit `876c1b0c5fb0ed7c15703a1955ef4b3580bd73fa`); files cited as `Z:`.
- Agent Client Protocol: https://github.com/agentclientprotocol/agent-client-protocol (commit `66ff8076ec2320d85e84fedc83cb779e9d906a89`);
  registry JSON https://cdn.agentclientprotocol.com/registry/v1/latest/registry.json; https://github.com/agentclientprotocol/registry;
  https://github.com/agentclientprotocol/acp-tck.
- Claude ACP adapter: https://github.com/agentclientprotocol/claude-agent-acp (commit `739dde3ae5bb848bdb90e2c9150e2cc4687d480c`).
- Chrome DevTools MCP: https://github.com/ChromeDevTools/chrome-devtools-mcp (local clone, commit `ada7963246c0c91eae185125a57aecd13cbe0376`).
- T3 Code (via `R:plans/research/t3code.md`, clone at `1eb4071a497cf1388a41040283a4065245dbe977`): https://github.com/pingdotgg/t3code.
- BrowserOS (via `R:plans/research/browseros.md`): https://github.com/browseros-ai/BrowserOS.
- Ardia (via `R:plans/research/ardia.md`).
- Chromium 154 with Helium and rac patches: `/Users/knewton/Dev/Github/rac/build/src` (files cited as `CR:`).
- rac: `/Users/knewton/.t3/worktrees/rac/t3-bb0e4397` (files cited as `R:`).
- GitHub API (stars, licenses, releases, contributors) for zed-industries/zed, agentclientprotocol/*, raycast/extensions,
  obsidianmd/obsidian-api, coddingtonbear/obsidian-local-rest-api, wzhudev/reverse-linear-sync-engine, tauri-apps/tauri,
  electron/electron, automerge/automerge, yjs/yjs, loro-dev/loro, modelcontextprotocol/{typescript,rust,go,swift}-sdk,
  modelcontextprotocol/conformance, oven-sh/bun, tailscale/tailscale, tailscale/libtailscale, n0-computer/iroh,
  livestorejs/livestore, vlcn-io/cr-sqlite, rocicorp/mono, vercel/ai, anthropics and openai org repo lists.

Documentation and articles:

- Zed: https://zed.dev/blog/bring-your-own-agent-to-zed ; https://zed.dev/acp ; https://zed.dev/blog/sequoia-backs-zed ;
  https://tessl.io/blog/zed-debuts-agent-client-protocol-to-connect-ai-coding-agents-to-any-editor ;
  https://tracxn.com/d/companies/zed/__3jn1wtnWJjfLtgOSDXECkHFjHmFm7BkEKtVzcAABH3A ; https://dealroom.co/companies/zed/
- Raycast: https://www.raycast.com/blog/a-technical-deep-dive-into-the-new-raycast ; https://developers.raycast.com/information/security ;
  https://developers.raycast.com/misc/faq ; https://manual.raycast.com/ai/model-context-protocol
- Obsidian: https://obsidian.md/help/cli ; https://obsidian.md/help/sync/security ; https://obsidian.md/help/plugin-security ;
  https://obsidian.md/about ; https://github.com/coddingtonbear/obsidian-local-rest-api ;
  https://kurtis-redux.medium.com/obsidian-cli-how-the-command-line-will-change-note-taking-26c90f03de17
- Linear: https://github.com/wzhudev/reverse-linear-sync-engine ; https://linear.app/blog/scaling-the-linear-sync-engine
- Electron: https://www.electronjs.org/docs/latest/api/utility-process
- Tauri: https://v2.tauri.app/develop/sidecar/ ; https://v2.tauri.app/learn/sidecar-nodejs/ ; https://v2.tauri.app/distribute/sign/macos/
- MCP: https://modelcontextprotocol.io/specification/latest/basic/transports ;
  https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http
- Claude Code MCP: https://docs.anthropic.com/en/docs/claude-code/mcp
- Bun: https://bun.com/docs/bundler/executables ; https://bun.com/docs/project/licensing ;
  https://www.anthropic.com/news/anthropic-acquires-bun-as-claude-code-reaches-usd1b-milestone ; https://bun.com/blog/bun-joins-anthropic
- Benchmarks: https://dev.to/fabwaseem/bun-vs-nodejs-in-2026-bun-14-vs-node-24-and-26-benchmarked-4pab
- Apple (fetched as JSON from `developer.apple.com/tutorials/data/documentation/...`): ServiceManagement `SMAppService` and
  `SMAppService.agent(plistName:)`; XPC "Creating XPC services"; "Defining launch environment and library constraints";
  "Notarizing macOS software before distribution"; TN3179 "Understanding local network privacy"; Foundation Models.
  Archive: https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingXPCServices.html ;
  WWDC23 10266: https://developer.apple.com/videos/play/wwdc2023/10266/ ; macOS SDK headers `sys/un.h`, `xpc/connection.h`,
  `Foundation/NSXPCConnection.h` (Xcode SDK on this Mac).
- macOS behavior: https://eclecticlight.co/2024/08/23/why-launch-constraints-can-crash-apps/ ;
  https://macpaw.com/how-to/stop-background-items-added-mac ; https://github.com/znasllc-io/memql-cockpit/issues/545
- 1Password: https://www.1password.dev/cli/app-integration-security/
- Chromium Local Network Access: https://blog.openreplay.com/chrome-local-network-access-lna-permission/
- Tailscale: https://tailscale.com/kb/1312/serve ; https://github.com/tailscale/libtailscale
- Storage: https://automerge.org/blog/automerge-3/ ; https://github.com/livestorejs/livestore ;
  https://www.inkandswitch.com/local-first/ (background on local-first ideals)

Local measurements and listings (2026-10-25, this Mac): `ls -la`, `codesign -dv`, `codesign -d --entitlements`, `ps`,
`vmmap --summary`, and timing scripts in `/tmp/rac-overhaul/bench` (`t.pl`, `one.js`, `srv.mjs`) against Bun 1.4.0,
Homebrew Node 24.21.0, bundled Node v24.19.0 and v26.8.1, Claude Code 2.1.310, opencode, codex 0.164.0, tailscale
1.104.1, gh 2.102.0, cloudflared 2026.10.0, and the installed apps Helium, Arc, Dia, 1Password, T3 Code (Nightly),
CuaDriver.
