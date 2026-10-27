# 03. Core architecture and a local "rac core" service

Paths are relative to the repo root unless they start with `CR:`, which means the read-only Chromium tree at `/Users/knewton/Dev/Github/rac/build/src`. Digests live in `plans/research/digests/`, matrices in `plans/research/matrices/`. Tags: FACT (primary source), CLAIM (self-report), INFERENCE (reasoning).

## In plain English

For most people nothing changes. rac stays one app. There is no background server and no new process.

Developers get one new switch: "Let other apps' agents use rac." Turn it on, and Claude Code or Codex can drive rac through a small command inside the app. Turn it off, and nothing listens.

rac's own assistant gets faster follow-ups. Its agent can stay ready while the panel is open, instead of restarting for every message.

Behind the scenes, everything rac can do goes into one list of actions. The sidebar, the command bar, rac's agent, and outside agents all use that list. So the safety rules live in one place.

We also cut how much of Chromium rac edits. Today rac changes about 869 spots in 216 Chromium files. The goal is under 400. Each Helium update then costs less.

We do not move to CEF, React Native, or a separate native shell. Each costs speed, safety, or a full rewrite, and none is cheaper in the end.

## What you need to decide

1. **03-D1. Where does rac's own backend run?** In the browser process / a Chromium utility process / a bundled Rust helper / a Node or Bun sidecar. **Recommended: in the browser process, as one "rac core" service per profile. No resident helper.**
2. **03-D2. Should rac ever ship a background helper (daemon)?** Never / only on a named feature that must run with rac fully closed / now. **Recommended: not now. The matrix's two triggers (warm agent, routines while closed) can be met without one.**
3. **03-D3. May a rac-launched agent stay warm between messages?** No, restart each message (today) / warm while its panel is open, 5-minute idle cap / prewarm on panel open. **Recommended: warm while the panel is open, 5-minute cap, one per profile.** This changes the rule "a run is one prompt".
4. **03-D4. Should routines run while rac is closed?** Never / a launchd timer that opens rac hidden / a resident daemon. **Recommended: not in this plan. If wanted later, a launchd timer that opens rac, never a daemon.**
5. **03-D5. How do outside agents reach rac?** Unix socket plus a signed `rac` relay command / loopback HTTP with OAuth / Chromium's ProcessSingleton socket / raw CDP. **Recommended: socket plus relay. Add loopback HTTP only if a real client needs `mcp login`.**
6. **03-D6. Is the outside-agent switch separate from the AI switch?** Separate / tied to AI on. **Recommended: separate, off by default.**
7. **03-D7. How do we shrink the patch surface?** Stay on Views and thin the hooks / native AppKit shell inside Chromium (Ardia, Dia) / out-of-process Chromium (Atlas OWL) / CEF (Cra) / HTML browser UI (`kWebium`). **Recommended: stay on Views and thin the hooks, with a hunk budget in CI. Spike a native shell only if the budget fails after two syncs.**
8. **03-D8. Move rac-owned source files out of quilt patches into a real source folder?** Keep in patches / overlay folder copied into the tree. **Recommended: yes, after the first Helium sync.** It changes the workflow in `AGENTS.md`.
9. **03-D9. Close the two unguarded debugging doors now?** Yes / leave as is. **Recommended: yes.** Developers who need CDP use a separate profile.

## Where we are today

**One process, no server.** rac compiles into Chromium's own binary. There is no rac process, daemon, or server (FACT, `digests/rac-baseline.md`, "Patch stack"). Almost everything runs on the browser UI thread: spaces, sidebar, AI service, ACP client, agent controller, guard, critic. The MCP socket and ACP stdio run on an IO thread (FACT, `docs/internals/ai.md:199-239`).

**Services.** rac has two `KeyedService`s: `SpacesService` and `AiService` (FACT, `CR:chrome/browser/rac/spaces/spaces_service.h:34`, `CR:chrome/browser/rac/ai/ai_service.h:33`). Each factory is registered by its own hunk in `CR:chrome/browser/profiles/chrome_browser_main_extra_parts_profiles.cc:210-211`.

**AI off.** `AiServiceFactory` returns null unless the profile is regular and AI is on. History, key store, ACP service and MCP server all hang off it (FACT, `docs/internals/ai.md:157-191`). Only one test guards this (`MasterSwitchGatesEntryPoints`). Nothing is measured (FACT, `digests/rac-baseline.md`).

**Agent runs.** A run is one prompt. Each message launches the agent again, so Cursor takes about 15 s and Claude Code about 25 s to the first tool call (FACT for the rule, CLAIM for timings, `docs/internals/ai.md:241-272,707-716`).

**MCP.** A per-run Unix socket at `<profile>/rac-agent-mcp/<token>/s`, 0700 folder, 0600 socket. Agents reach it with `/usr/bin/nc -U`, so the path shows in `ps` and there is no secret. It dies with the run and with AI off (FACT, `docs/internals/ai.md:307-332`). All authorization is in `AgentController::HandleToolCall` (FACT, same lines). Outside agents cannot reach rac at all.

**Storage.** Prefs JSON, a versioned `rac spaces` file, and plaintext `rac_ai_history.json`. No rac SQLite (FACT, `digests/rac-baseline.md`, "Storage").

**JSON parsing is already memory-safe.** `base::JSONReader` is backed by Rust `serde_json_lenient` in this tree (FACT, `CR:base/json/json_reader.cc:14-20`). rac's MCP, ACP and chat parsers use it (FACT, grep of `CR:chrome/browser/rac`). This weakens the case for moving parsing out of process.

**Two side doors with no guard.** Chromium refuses `--remote-debugging-port` on the default profile only in Google-branded builds (FACT, `CR:chrome/browser/devtools/remote_debugging_server.cc:160-180`). `chrome://inspect` approval mode is on by default on macOS (FACT, `plans/research/long-tail.md:339,630`). Neither Helium nor rac patches them. Either gives a local program the logged-in profile with none of rac's guard (INFERENCE).

**Patch surface.** 180 patches, 869 hunks in 216 upstream files. 320 hunks (37%) are in `ui/views`. 663 hunks (76%) sit in 139 files Helium or ungoogled also patch (FACT, `digests/rac-baseline.md`). A text dry run to Helium 0.20.1.1 fails 104 hunks at fuzz 2, 46 of them first failures (FACT, `digests/helium.md`). The agent layer is small: 21 upstream files, 58 hunks (FACT, `digests/chromium-agent-internals.md`).

**Signing.** Only parts in `chrome/installer/mac/signing/parts.py` are signed. Helium already patches it to add Sparkle's `Autoupdate` and `Updater.app` (FACT, `CR:chrome/installer/mac/signing/parts.py:261-266`).

## What others do

Full tables: `matrices/architecture-and-storage.md` (Matrices A and C) and `matrices/agents.md` (Matrix B).

- **T3 Code** runs a Node server as the hub. It holds 323 MB after 22 hours. Its SQLite event store reached 17 to 40 GB for some users. It needs a server because its clients are remote (phone, web) and its work needs no browser (FACT, `digests/t3code.md`).
- **Aside** runs an always-on 159 MB Node daemon on `127.0.0.1:21420`. It ships a CLI, a 4-tool `aside mcp`, and skill install. Analytics are on by default (FACT, `digests/aside.md`).
- **BrowserOS** starts a Bun sidecar and an open CDP port on every launch, with no off switch. Its MCP has no token and binds `0.0.0.0` (FACT, `digests/browseros.md`).
- **ego(lite)** has no daemon. A helper in the bundle talks over Chromium's ProcessSingleton socket to an embedded Node utility process. No auth beyond the OS user (INFERENCE, `digests/ego-lite.md`).
- **Crest** ships a stdio MCP helper that names the caller from the audit token and parent chain. **Cra, Zen, Nook, Ardia, Arc, Dia** run no local server (FACT, `digests/long-tail.md`; `matrices/architecture-and-storage.md`).
- **Shells.** Ardia runs Chrome's browser process with a React Native UI and no `BrowserView`: 60 patches, 492 hunks, 205 files, only 26 hunks in `ui/views` (FACT, `digests/ardia.md`). Cra wraps CEF: 11 hunks of its own, but CEF carries 1,044 hunks and Cra runs with no sandbox (FACT, `digests/cra.md`). Atlas runs Chromium out of process ("OWL"), built by a funded team (FACT, `digests/closed-ai-browsers.md`).

## Options

### Where the backend runs (03-D1, 03-D2)

All options keep one rule from the matrix: the browser holds every permission decision. Every call ends in `AgentController::HandleToolCall` and the guard. None exposes raw CDP (`matrices/architecture-and-storage.md`, "Shared ground").

#### Option A: in-browser "rac core" service, no extra process

rac's backend stays inside the browser. One new service per profile owns a single table of actions: open a tab, move it to a space, pin, archive, snapshot, click. Every surface calls the table. Outside agents reach it through a tiny signed relay command in the app bundle and a private socket. The socket exists only while the switch is on.

- **Details.** `RacCoreService` (a `KeyedService`) plus `rac_actions.{h,cc}`. Each action has an id, a JSON schema, MCP-style annotations (read-only, destructive, idempotent, open-world), rac's risk class, and which surfaces offer it. MCP `tools/list` and command bar rows are generated from the table. JSON exists only at the door. Inside, calls are typed C++.
- **Pros.** No new process or runtime. Reuses the guard, cards, snapshot, and refs. Smallest engine diff. Fast to ship.
- **Cons.** More C++ in the browser. Each change needs a Chromium rebuild (minutes in a worktree). Nothing runs while rac is closed.
- **Effort.** M: 15 to 25 agent-days for the service, door, relay, and warm agent.
- **Risk.** Low. A crash in rac code takes the browser down, as today.
- **Locks in.** C++ for the backend. The table keeps a later helper possible.

#### Option B: Chromium utility process

Agent-side parsing and the ACP client move into a Chromium-managed child process. Chromium kills it when idle. The browser still owns the guard and the socket.

- **Details.** `ServiceProcessHost::Launch<mojom::RacCore>()` with `set_idle_handler` (FACT, `CR:content/public/browser/service_process_host.h:67`). Spawning agents needs `kNoSandbox` (INFERENCE, `digests/local-first-and-sidecars.md`).
- **Pros.** Crash isolation. No new signed binary.
- **Cons.** Still needs Option A's door, plus mojom and sandbox plumbing. JSON parsing is already Rust, so the crash case is weak.
- **Effort.** M+: Option A plus 5 to 8 agent-days.
- **Risk.** Medium. Mojo service plumbing churns upstream.
- **Locks in.** Mojo interfaces between rac's own code.

#### Option C: bundled Rust helper, started on demand

A rac-owned program at `rac.app/Contents/Helpers/rac-agentd` owns outside-agent MCP, ACP processes, history, and schedules. The browser starts it lazily and passes a secret on an inherited file descriptor. Every browser action still goes back to the browser's guard.

- **Details.** Rust with the official `rmcp` and ACP crates, built by cargo outside GN, since the tree has no `tokio` or `hyper` (FACT, `digests/local-first-and-sidecars.md`). One `parts.py` entry. Optional `SMAppService` launch agent for work while rac is closed.
- **Pros.** Iterates without Chromium rebuilds. A crash cannot take the browser down. Official protocol SDKs.
- **Cons.** A second binary to build, sign, and update. Two places for state. An IPC hop per action. A second CI job before the first release build has ever finished.
- **Effort.** L: 25 to 40 agent-days.
- **Risk.** Medium. Launch constraints and Gatekeeper behavior are untested.
- **Locks in.** A second language and toolchain.

#### Option D: Node or Bun sidecar (T3, Aside, BrowserOS)

The agent runtime is TypeScript, shipped as a bundled single-file program and reached over loopback or a socket.

- **Pros.** Fastest to write. Official TypeScript SDKs.
- **Cons.** Needs JIT, unsigned-memory, and disabled library-validation entitlements, so it becomes rac's least hardened process (FACT, `digests/local-first-and-sidecars.md`). Every product that took this path ended up always on, with telemetry or open ports.
- **Effort.** L. **Risk.** High for speed and privacy.

#### Option E: be only an MCP target (T3 Option C)

Ship the door only; outside harnesses own history and schedules. Least code, but rac's own assistant gets no better. S to M.

#### The numbers

Sizes and timings are measured on existing binaries on the maintainer's Mac, warm cache, not on a minimal rac server (`digests/local-first-and-sidecars.md`, "Runtime comparison"). Engine hunks are estimates (`matrices/architecture-and-storage.md`, "Comparison at a glance").

| | A. In-browser | B. Utility process | C. Rust helper | D. Bun / Node sidecar |
| --- | --- | --- | --- | --- |
| Memory, feature off | 0 | 0 | 0 | 0 if strictly lazy |
| Memory, door on and idle | No new process; KB of objects (INFERENCE) | 16 to 38 MB while alive | 5 to 10 MB (estimate) | Bun 22.5 MB; Node 54 to 67 MB; T3 323 MB after 22 h |
| Start cost | 0 at browser launch (lazy) | Process spawn, unmeasured | About 14 ms | Bun 7 ms; Node 35 ms |
| Added to the app | Relay under 1 MB (INFERENCE) plus code in the framework | 0 | 1 to 8 MB | Bun 64 MB; Node 117 to 146 MB; Aside's daemon 159 MB |
| New entitlements | None | None | None | JIT, unsigned memory, no library validation |
| Engine hunks | 5 to 10 | 13 to 25 | 7 to 14 | 7 to 14 |
| Rebase cost per sync | Low: new files, a few hooks | Medium: mojom and sandbox code | Low engine; plus cargo crates and protocol revisions | Low engine; plus npm churn |
| Works while rac is closed | No | No | Only with a launch agent | Only with a launch agent |

A warm agent is not free under any option. Long Claude Code sessions measured 705 MB and 1.09 GB RSS (FACT, `digests/local-first-and-sidecars.md`). That is the agent's own memory, so the cap matters more than where the runtime lives.

#### Recommendation: Option A, and challenge the helper triggers

**How would rac run a server-style backend locally?** As a service inside the browser process. It owns one action table and a private socket that listens only while the user allows outside agents. A small signed relay turns that socket into a standard MCP stdio server and a few CLI verbs. The browser is the server.

**Should it run a separate server?** No, not now. T3 Code needs a server because its clients are remote and its work needs no browser. rac's work always needs the browser: its tabs, cookies, and guard. A separate process adds a hop, a signed part, an IPC channel to secure, and two places for state. It adds no capability rac needs.

The architecture matrix recommends Option A now and a Rust helper "only if routines-while-closed or a warm agent are approved". I agree with A and disagree with both triggers.

- **Warm agent.** It needs only a lifecycle change in rac's ACP service: keep the child alive while the panel is open. No helper is involved (INFERENCE, `docs/internals/ai.md:241-272`).
- **Routines while closed.** A routine drives logged-in pages, so it needs the browser anyway. A helper could only start rac. A launchd timer can do that with no resident process (INFERENCE).
- **History size.** SQLite with retention, in the profile, through Chromium's `sql::Database` (FACT that it exists, `CR:sql/database.h`). Plan 04 owns the schema.
- **Crash isolation.** Parsing is already Rust-backed. ACP agents already run as separate child processes.

What would justify a helper: a feature that must run with rac fully closed and must not open it. Examples: phone remote control, or Slack and Telegram bots. None is planned, and both strain the privacy rule. The action table keeps that door open at low cost.

Graft from C: the inherited-descriptor secret (T3's fd 3) for any child rac launches. Graft from E: keep the door small and standard, so outside harnesses can be the "server" for people who want one.

### How outside agents reach the core (03-D5, 03-D6)

| Transport | For | Against |
| --- | --- | --- |
| **Unix socket plus signed `rac` relay (stdio MCP)** | No TCP port. Works with `claude mcp add rac -- rac mcp`. Peer audit token can be checked with `ProcessIsSignedAndFulfillsRequirement` (FACT, `CR:base/mac/code_signature.h:34`) | Sandboxed agents cannot reach a socket (ego #188, `digests/ego-lite.md`). Peer identity names the relay, not the agent |
| Loopback HTTP with OAuth and PKCE (T3) | Needed if `mcp login` flows require it | A port, Origin and Host checks, token storage. More surface |
| ProcessSingleton socket (ego) | Already exists (FACT, `CR:chrome/browser/process_singleton_posix.cc:141-143`) | Patches a hot upstream file. No auth beyond the user |
| Raw CDP (Ardia) | Agents know it | Bypasses the guard, cards, and site rules. Rejected by every digest |

Recommended: socket plus relay, with its own switch, off by default and independent of AI. The relay replaces `nc -U` for rac-launched agents too, so the socket path leaves `ps` and a one-run secret rides the environment. Add loopback HTTP only if testing shows a client cannot work over stdio.

### How to shrink the patch surface (03-D7, 03-D8)

The big hunk counts come from UI. `ui/views` holds 320 hunks, settings resources 110, `ui/tabs` 63, `ui/webui` 39. That is 532 of 869, or 61% (FACT, `digests/rac-baseline.md`). So the shell choice drives rebase cost.

#### Option S1: stay on Views, thin the hooks

Keep Chromium's own window and Views, and keep building on Helium's vertical tabs, frameless mode, and split view. Move rac logic into rac-owned files and leave one call per upstream spot.

- **Details.** One hook per upstream registry: factories, prefs allowlists, localized strings, browser commands, WebUI configs, color mixers. Today `prefs_util.cc` carries 11 rac patches, `settings_localized_strings_provider.cc` 13, `browser_command_controller.cc` 10, and `ui/BUILD.gn` 26 (FACT, `digests/rac-baseline.md`). Each becomes one call into a `rac::` function. Adopt Helium's new Layout settings and expand-on-hover frameless mode instead of re-patching them (FACT that Helium rebuilt both, `digests/helium.md`). Delete the dead `look/horizontal-tabs` restyle. Fold the 24 `fix-*` patches. Add Ardia-style marker hooks that turn a lost hook into a compile error. Fail CI on any patch offset, as Helium does.
- **Targets.** Under 400 hunks (from 869) and under 150 in `ui/views` (from 320) (`digests/rac-baseline.md`, take 3).
- **Pros.** No rewrite. Keeps every Chrome dialog, extension, and sandbox for free. Matches VISION: "build on what Helium already has".
- **Cons.** Views is harder for motion than Core Animation or SwiftUI. Plan 02 handles that with a spring helper for Views (Ardia take 6).
- **Effort.** M to L: 15 to 25 agent-days, spread across groups after the first sync. **Risk.** Low to medium; regressions without UI tests. **Locks in.** Views.

#### Option S2: native AppKit or SwiftUI shell inside Chromium's process (Ardia, Dia, Crest)

Replace Chromium's window with rac's own. Chrome's browser process still runs, but without `BrowserView`, toolbar, or tab strip.

- **Evidence.** Ardia's version has 492 hunks in 205 files, but only 26 in `ui/views` (FACT, `digests/ardia.md`). Crest's native host is 205 hunks in 95 files, plus a 14,406-line overlay and 4,963 lines of Swift glue. Every Chrome dialog must be re-hosted (FACT, `digests/long-tail.md`). Ardia's own estimate was 12 to 20+ engineer-weeks (FACT, `/tmp/rac-overhaul/ardia-arch-review.md`, section 5).
- **Speed.** Ardia's React Native layer made tab switches 40 ms, later 10 to 16 ms, against Helium's 8.5 ms. At 20 tabs it used 1,183 MB against Helium's 1,125 MB (FACT, `digests/ardia.md`). That fails "never slower than Helium" on tab switching. React Native itself was not the cause of Chrome fights, but it is the cause of the latency tax (FACT, Ardia review section D).
- **Pros.** Fewer `ui/views` hunks; native motion.
- **Cons.** Rewrites rac's 67 Views files (16,108 lines) (FACT, `digests/rac-baseline.md`). Drops Helium's frameless mode, split view, and vertical tabs. Swift in the tree is iOS-only, so it needs a second build system (FACT, `digests/local-first-and-sidecars.md`). Ardia's 492 hunks is not much better than S1's target of 400.
- **Effort.** XL: 40 to 80 agent-days. **Risk.** High. **Locks in.** A second UI stack.

#### Option S3: out-of-process Chromium (Atlas OWL, Refrax)

The app is a separate client. Chromium runs as a service and sends pixels over remote layers. Refrax needs only 42 hunks plus a 6,812-line overlay, but extension support is unverified (FACT, `digests/long-tail.md`). Atlas needed a funded team (INFERENCE, `digests/closed-ai-browsers.md`). **Effort.** XL+. Reject for now.

#### Option S4: CEF (Cra)

Reject. CEF carries 1,044 hunks in 473 files of its own. Cra runs with `no_sandbox = true`, swizzles private AppKit methods, and loses Helium's privacy patches (FACT, `digests/cra.md`). Ardia started on CEF on 2026-09-25 and removed it by 2026-10-09. 42% of its commits and 56% of its fixes that week touched the CEF seam (FACT, Ardia review section A). Mori also left CEF (FACT, `plans/research/long-tail.md:76`).

#### Option S5: HTML browser UI (`kWebium`)

Chromium's experiment is in the tree, off by default (FACT, `CR:chrome/common/chrome_features.cc:1966`). Mori rejected it (FACT, `plans/research/long-tail.md:76`). Experimental upstream code is the opposite of cheap to update. Reject.

#### Recommendation: S1, with a trigger for a one-week S2 spike

Do S1 right after the first Helium sync, so the refactor lands on the new base. Spike S2 for one week only if, after two syncs on the thinner base, a Chromium major still costs more than 3 agent-days of conflict work. The spike measures files touched, dialogs to rebuild, tab-switch time, and memory (`digests/long-tail.md`, item C6).

**Why rebase cost matters.** Chromium ships a major every two weeks, so 26 a year (FACT, `digests/helium.md`). At 2 agent-days per major, that is about 52 agent-days a year. At 5, it is 130 (INFERENCE). The dry run doubled from 43 to 104 failed hunks between one and two majors behind (FACT, `digests/helium.md`).

**03-D8, source overlay.** rac's 325 new files (43,282 lines) live inside patches. Later patches edit them 658 times (FACT, `digests/rac-baseline.md`). Moving them to a real folder that is copied or linked into `build/src` (Zen's pattern, `matrices/engineering-and-shipping.md`) makes PR diffs show real code. Patches then hold only upstream hunks. New-file patches rarely conflict, so the sync gain is small. The win is review and refresh speed.

## Recommended plan

Each milestone lists its patch-surface impact. "Hunks" means hunks in upstream files.

### M0. Measure before changing (2 to 3 agent-days)

- **Goal.** Numbers for "never slower" and "AI off costs nothing", and a hunk counter.
- **Tasks.** Share plan 06's benchmark: cold start, tab switch, idle memory, idle wakeups, against Helium, with AI and the door off. Add a script that counts hunks per group and per upstream file and writes a budget file.
- **Acceptance.** A baseline table in the PR. The counter reproduces 869 hunks and 216 files, or explains the difference.
- **Verification.** `ps` and `lsof` listings in a fresh profile with AI off: no rac children, no rac sockets.
- **Patch surface.** None.

### M1. Close the side doors (1 to 2 agent-days, with plan 05)

- **Goal.** No local program reaches the logged-in profile without rac's guard.
- **Tasks.** Turn on the default-profile refusal for `--remote-debugging-port` under rac's branding. Set `kDevToolsAcceptDebuggingConnections` off by default, or require approval each time (03-D9).
- **Acceptance.** `--remote-debugging-port=9222` against the real profile logs a refusal. A throwaway `--user-data-dir` still works.
- **Verification.** Unit test on `IsRemoteDebuggingAllowed`. Screenshot of `chrome://inspect` showing the off state.
- **Patch surface.** +2 hunks in 2 files.

### M2. The rac core service and action table (6 to 9 agent-days)

- **Goal.** One list of actions that every surface uses.
- **Tasks.**
  - Add `RacCoreService` per regular profile, created on first use.
  - Add the action table with schemas, annotations, risk class, and surfaces.
  - Route the agent's 15 tools through it. Keep `AgentController::HandleToolCall` as the only path to the guard.
  - Generate MCP `tools/list` from the table.
  - Add one `rac::EnsureFactoriesBuilt()` hook and move the spaces and AI factory registrations behind it.
  - Use Chrome's tool names where they exist (`navigate`, `click`, `type`, `switch_tab`) (`digests/chromium-agent-internals.md`, take 11).
- **Acceptance.** A unit test fails if any action lacks an annotation or risk class. MCP output matches today's for the 15 tools. With AI and the door off, `RacCoreService` is never built.
- **Verification.** Unit tests in `rac_agent_unittests`. A video of one agent turn showing behavior unchanged.
- **Patch surface.** Net 0 to +1 hunk: the new hook replaces two registrations.

### M3. The outside-agent door: transport and lifecycle (8 to 12 agent-days, with plan 05)

- **Goal.** Claude Code, Codex, Cursor, and OpenCode can drive rac through the guard, with rac's own AI off.
- **Tasks.**
  - Add the signed relay `rac.app/Contents/Helpers/rac`: a small GN C++ target that copies bytes between stdio and the socket. Commands: `rac mcp`, `rac skill`, and a few verbs that map one-to-one to actions (`open`, `tabs`).
  - Add the pref `rac.agents.outside_access`, off by default and separate from `rac.ai.enabled`. The listener exists only while it is on.
  - Put the socket at a short per-user path with a 0700 folder and 0600 socket. Accept only peers whose audit token is rac's signed relay. Skip that check in unsigned dev builds, as app shims do (FACT, `digests/local-first-and-sidecars.md`).
  - Make the relay walk its parent chain, Crest-style, to name the agent on the pairing card (`digests/long-tail.md`).
  - Make `rac skill` print a guide that matches the build, ego-style. "Add to my agents" writes stubs only on click.
  - Add one `parts.py` entry, Hardened Runtime, and no new entitlements.
  - Link `~/.local/bin/rac` on click, with no admin prompt.
  - When rac is closed, the relay opens it in the background, with no window and no focus change.
  - Plan 05 owns the tool list, pairing card, per-agent levels, and the read-only default.
- **Acceptance.**
  - `claude mcp add rac -- rac mcp` works and lists tools.
  - With the switch off, `lsof` shows no rac socket.
  - A process not signed as the relay is refused.
  - Every call passes the guard. Risky actions show a card.
  - `codesign --verify --deep --strict` and notarization pass.
- **Verification.** Screenshots of the Settings switch, connected-agents list, and pairing card, in light and dark mode. A video of Claude Code in Terminal driving a background tab with rac's AI off. Unit tests for the peer check and relay framing.
- **Patch surface.** +1 to 2 hunks (`parts.py`, which Helium also patches) plus new files.

### M4. Agent lifecycle: secret channel and warm agent (4 to 6 agent-days)

- **Goal.** No socket path in `ps`, and fast follow-ups.
- **Tasks.**
  - rac-launched ACP agents use the relay instead of `nc -U`, with a one-run secret in the environment. Extend this to an inherited descriptor where the agent supports it.
  - If 03-D3 is approved, keep one ACP agent per profile alive while its panel is open. End it after 5 idle minutes, on panel close, Stop, AI off, or memory pressure. Re-scope its MCP tools at each turn.
  - Update `docs/internals/ai.md`, "Runs".
- **Acceptance.** A second message reaches its first tool call in under 3 s on Claude Code (today about 25 s). No agent process remains 5 minutes after the panel closes.
- **Verification.** A side-by-side video, cold versus warm. `ps` after close. Unit tests on run ids across warm turns.
- **Patch surface.** 0 hunks.

### M5. Storage placement (with plan 04)

- **Goal.** Conversation and agent history in the browser process, bounded and encrypted.
- **Decision recorded here.** History goes to SQLite through `sql::Database` in the profile, one row per turn and per tool call, never per token. Text is encrypted with `os_crypt_async`. Plan 04 owns schema, retention, migration from `rac_ai_history.json`, and sync.
- **Patch surface.** 0 hunks.

### M6. Thin the hooks (15 to 25 agent-days, after the first sync)

- **Goal.** Under 400 hunks and under 150 in `ui/views`, with the budget enforced in CI.
- **Order.** Settings (adopt Helium's Layout section), sidebar-reveal (rebuild on Helium's expand-on-hover), look, spaces, pinned, sidebar-address-bar, ai, then the agent adapter around Chromium's actor code (`digests/chromium-agent-internals.md`, take 3).
- **Rule.** One upstream hook per registry. New logic goes in `chrome/browser/ui/rac/` or `ui/views/rac/`.
- **Acceptance.** The budget file shows each group at or under target. CI fails a PR that adds hunks without raising the budget in the same PR. Patches apply with fuzz 0.
- **Verification.** The screenshot matrix for each refactored group (sidebar full and hidden, light and dark, toolbar and sidebar address bar). No visual diff beyond noise.
- **Patch surface.** About −470 hunks.

### M7. Source overlay (3 to 5 agent-days, if 03-D8 is approved)

- **Goal.** rac-owned files are real files in the repo.
- **Tasks.** Move `chrome/browser/rac/**`, `chrome/browser/ui/views/rac/**`, and rac WebUI sources to an overlay folder. Make `he merge`, `he unmerge`, and `worktree.sh sync` copy or link them. Update `AGENTS.md` and `docs/internals/overview.md`.
- **Acceptance.** A clean apply produces a byte-identical `build/src` (Ardia's `series check`). A worktree build stays incremental.
- **Patch surface.** 0 upstream hunks. Patch lines drop by about 43,000.

### M8. Later and conditional: wake rac for a routine

Only if plan 07 schedules routines and the maintainer wants them while rac is closed (03-D4). An `SMAppService` launch agent with a calendar interval opens rac in the background with a routine id. macOS shows a "Background Items Added" notice (CLAIM, `digests/local-first-and-sidecars.md`). Off by default. No resident process. Every risky step still asks; a headless routine never skips the card (Aside's mistake, `digests/aside.md`). 3 to 5 agent-days. 0 engine hunks.

### Where each part lives

| Part | Runs in | Owner plan |
| --- | --- | --- |
| AI providers (keys, local models) | Browser process, `SimpleURLLoader` | 05 |
| Conversation and agent history | Browser process, SQLite in the profile | 04 |
| Agent runtime (built-in loop, ACP client, guard) | Browser process; ACP agents as children | 05 |
| Outside-agent door (MCP, CLI, skills) | Browser socket plus signed relay | 03 transport, 05 policy |
| Automations | Browser process while running; optional launchd wake | 07 |
| Sync | Browser process, sealed files in a user folder | 04 |
| Assistant, settings, command bar results | WebUI as clients of the core; Views for chrome | 01 |

## Fit with the non-negotiables

- **Private.** No port, no server, no new network traffic. The socket is per user and exists only while the switch is on. Nothing calls home. Holds.
- **Never slower than Helium.** No resident process. The service is lazy. M0 measures it, and M6 must not regress tab switching. The warm agent costs the agent's own memory (0.7 to 1.1 GB for long Claude sessions) only while its panel is open. Holds, provided M0's benchmark is in place.
- **AI off costs nothing.** With both switches off, no service, socket, or child exists. The door is separate from AI. Developers can use outside agents with the built-in assistant off. Chromium's own idle `ActorKeyedService` objects stay unmeasured and must stay on, because the renderer `CHECK`s the feature (`digests/chromium-agent-internals.md`). Holds.
- **Cheap to update.** M1 to M4 add about 4 to 5 upstream hunks. M6 removes about 470. The relay adds one more signed part. Net strongly better.
- **Calm UI.** New surfaces are a switch, a list, and a card. Holds.
- **GPL.** All new code is rac's. Zed's GPL code and MIT or Apache code can be used with credit. BrowserOS is AGPL, so ideas only (`digests/browseros.md`). Holds.
- **Bent.** M4's warm agent changes the documented rule "a run is one prompt, and nothing of it outlives it" (`docs/internals/ai.md:241-245`). That needs the maintainer's sign-off (03-D3). M3 changes "rac's MCP server serves only the agent it launched" (`docs/roadmap.md`, "Later"). The maintainer brief already asks for that change.

## Dependencies on other plans

- **01 ui-shell.** This plan keeps Views (03-D7). 01 builds the command bar and settings rows on the action table (M2). 01 follows the one-hook-per-registry rule (M6).
- **02 visual-design-and-motion.** Styles the switch, list, and pairing card. A spring helper for Views answers the "Views can't animate" argument for S2.
- **04 data-storage-import-sync.** Owns the history schema, retention, encryption migration, backups, and sync files (M5).
- **05 agents-and-ai.** Owns the `auto` gap fix and injection evals before M3 ships. Also owns tool list, pairing, per-agent levels, and outside-agent defaults. Co-owns M1.
- **06 engineering-and-shipping.** Owns the benchmark (M0), the first Helium sync (before M6), the hunk budget in CI, the no-fuzz gate, the drift detector, and signing the relay in the release flow.
- **07 power-features.** Automations, Little Arc, and Air Traffic Control call the action table. 07 decides whether M8 is needed.

## Risks and unknowns

- **The first sync blocks M6.** M2 to M4 can go first, since they are mostly new files.
- **Sandboxed agents cannot reach a Unix socket** (FACT, ego #188, `digests/ego-lite.md`). Claude Code or Codex in sandbox mode may need loopback HTTP or an allowlisted path. Untested.
- **A TCC prompt is possible** if the socket sits under Application Support. A short `$TMPDIR` path avoids it (INFERENCE, `digests/local-first-and-sidecars.md`). Untested.
- **Peer identity is weak.** The audit token names the relay, not the agent, and interpreters such as `node` vouch for nothing (FACT, Crest notes, `digests/long-tail.md`). The real boundary is the same user. Pairing is consent and revocation, and the UI should say so.
- **MCP churn.** MCP 2026-07-28 drops `initialize`. ACP v2 is a breaking draft (FACT, `digests/local-first-and-sidecars.md`). The action table isolates rac, but the MCP adapter needs updates.
- **The `parts.py` hunk sits in a Helium-patched file.** It is small but will conflict sometimes.
- **The warm agent and memory.** One Claude session can hold about 1 GB. Without the cap, this breaks "never slower" on 8 GB Macs (INFERENCE).
- **The shrink can regress UI.** Only one UI test exists today (FACT, `digests/rac-baseline.md`). The screenshot matrix is the safety net.
- **The numbers are thin.** Runtime figures come from existing binaries, and rac has no benchmark yet.
- **S1 may miss its target.** If Helium keeps rebuilding the sidebar, hooks into the vertical tab strip will keep conflicting. The S2 spike trigger covers that.

## Open questions

1. One socket per app or per profile? Recommended per app, with profile as a call parameter. How should incognito behave? Recommended: never reachable.
2. Should the relay open rac when it is closed, or fail with "open rac first"? Recommended: open it in the background, no window.
3. Do Claude Code and Codex need loopback HTTP for `mcp login`, or is stdio enough? Test before building HTTP.
4. Should outside agents start at read-only, `ask`, or `careful`? Plan 05 decides. This plan recommends read-only until the evals pass.
5. What are the right CLI verbs beyond `mcp` and `skill`? Keep under 10.
6. Is the 5-minute warm cap right, and should the agent prewarm when the panel opens?
7. Does the overlay folder (03-D8) break any `he` or Factory setup step for worktrees?
8. Will Helium's experimental vault sync carry `rac.*` prefs? It affects whether plan 04 needs its own sync files.
9. Does Anthropic's rule on third-party use of Claude credentials touch the ACP adapter path? Unclear (`matrices/architecture-and-storage.md`, question 10).

## Draft thread brief

**DRAFT. Do not launch until the maintainer approves this plan and its decisions.**

> **Thread: rac core and the outside-agent door (architecture and backend)**
>
> **Model.** Claude Opus 5.5 for design and C++ review. Sonnet 5.5 or a strong open-weight model for scoped tasks, such as tests and the relay. Opus for all security-sensitive code: socket peer checks, the guard path, and signing.
>
> **Read first.** `AGENTS.md`, `VISION.md`, `docs/internals/ai.md`, `docs/internals/overview.md`, `plans/03-core-architecture.md`, the approved parts of plans 05 and 06, and `plans/research/matrices/architecture-and-storage.md`.
>
> **Goal.** Land M0 to M4 of plan 03 as separate PRs, in order: measure, close side doors, action table, door, agent lifecycle. Then M6 and M7 after the first Helium sync lands.
>
> **Hard rules.**
> - Feature worktrees only. Build with `source dev.sh && he build`. Run with `devutils/rac/worktree.sh run`. Never `he run` or `open` in a worktree.
> - Never touch real profiles, `helium-chromium/`, or Helium's patch folders. Post nothing upstream.
> - No resident process, no TCP port, no new entitlements, no telemetry.
> - With AI and the door both off, rac must create no service, socket, or child. Prove it with `ps` and `lsof` in a fresh profile.
> - Every call goes through `AgentController::HandleToolCall` and the guard. No policy at the MCP layer. No raw CDP.
> - M3 ships only after plan 05's `auto` fix and injection evals are green.
> - Count upstream hunks before and after each PR, and report the delta.
>
> **Done means.** Each PR has: unit tests run locally; benchmark numbers against Helium where relevant; screenshots for every visible surface, light and dark; a video for the door (Claude Code driving a background tab with AI off) and for the warm agent; updated docs where a decision changed; and the hunk delta.
>
> **Stop and ask** if any step needs a full build, more than 10 new upstream hunks, a new signed part beyond the relay, or a change to "a run is one prompt" that 03-D3 did not approve.
