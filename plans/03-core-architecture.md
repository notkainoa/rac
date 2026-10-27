# 03. Core architecture and a local "rac core" service

Paths are relative to the repo root unless they start with `CR:`, which means the read-only Chromium tree at `/Users/knewton/Dev/Github/rac/build/src`. Digests live in `plans/research/digests/`, matrices in `plans/research/matrices/`. Tags: FACT (primary source), CLAIM (self-report), INFERENCE (reasoning).

## In plain English

For most people nothing changes. rac stays one app, and the browser itself acts as the "server". There is no background program that runs all the time.

Developers get one new switch: "Let other apps' agents use rac." With it on, Claude Code or Codex can drive rac through a small command inside the app. With it off, nothing listens and nothing extra runs.

rac's own assistant answers follow-ups faster. Its agent can stay ready for 5 minutes while the panel is open, instead of restarting for every message.

Everything rac can do goes into one list of actions. The sidebar, the command bar, shortcuts, rac's agent, and outside agents all use it. So the safety rules live in one place.

We also cut how much of Chromium rac edits. That makes each Helium update cheaper.

Nothing here is needed for the Arc shutdown on 2026-12-22. It is the ground the next stage is built on.

### Is there a server?

**Yes: the browser is the server.** It opens a private local socket only while you allow outside agents. No network port is involved.

```
Claude Code ─stdio─> rac (tiny relay inside rac.app) ─private socket─> rac browser
                                                                        ├ rac core: action list + guard
                                                                        └ your tabs and logins
```

Compared with a T3 Code-style server, you give up four things:
- Agent runs end when rac quits, crashes, or updates.
- No phone or second Mac can connect.
- Sessions don't survive a restart.
- Nothing runs with rac fully closed.

In return, nothing listens or uses memory while the switch is off. Safety checks also stay in one process.

## What you need to decide

Terms: a **daemon** or **sidecar** is a separate background program. A **utility process** is a helper process that Chromium starts and stops itself. **CDP** is Chrome's debugging protocol.

1. **03-D1. Does rac run a separate local server or helper program?** No, the browser is the server / Rust helper / Node sidecar. **Recommended: no. rac also adds no Swift helper, so local models stay Ollama and LM Studio.**
2. **03-D2. How do outside agents connect?** Per-profile socket, signed relay, per-client tokens / loopback HTTP with OAuth. **Recommended: socket, relay, and tokens. Add HTTP only if the door spike shows a client needs it.**
3. **03-D3. Keep a rac-launched agent warm between messages?** Restart each message / one warm agent per profile, 5-minute idle cap. **Recommended: warm, one per profile, 5-minute cap.** Plan 05 refers to this decision.
4. **03-D4. How do we shrink rac's Chromium edits?** Stay on Views and thin the hooks / native AppKit shell now. **Recommended: Views with thin hooks. Spike a native shell only if the target in 03-D5 is missed after the second sync.**
5. **03-D5. Which patch-surface number do we hold?** Net-diff hunks plus dry-run failures per sync / raw stacked hunks. **Recommended: net-diff hunks and failures per sync. Accept up to 630 stacked hunks including other plans' additions; aim for 550.**
6. **03-D6. Add a scoped promise for the door to VISION.md?** Yes / no. **Recommended: yes. "Outside-agent access has its own switch, off by default. When off, it costs nothing."** The same decision (D12 in decisions.md) also settles that the door works with AI off.

Decided elsewhere: the debugging doors are 05-D6. Moving rac's own files into a plain folder is 06-D12. Routines while rac is closed are plan 05's (D59 in decisions.md).

## Where we are today

**One process.** rac compiles into Chromium's binary. There is no rac daemon or server (FACT, `digests/rac-baseline.md`). Almost everything runs on the browser UI thread. The MCP socket and ACP stdio run on an IO thread (FACT, `docs/internals/ai.md:199-239`).

**Services.** rac has two `KeyedService`s, which are per-profile objects Chromium creates and destroys with the profile: `SpacesService` and `AiService` (FACT, `CR:chrome/browser/rac/spaces/spaces_service.h:34`, `CR:chrome/browser/rac/ai/ai_service.h:33`). Each factory has its own hunk in `CR:chrome/browser/profiles/chrome_browser_main_extra_parts_profiles.cc:210-211`.

**The agent is tied to AI.** `AiServiceFactory` returns null unless AI is on. `AgentController` exists only when AI and browser control are both on. The MCP server hangs off `AiService` (FACT, `docs/internals/ai.md:157-191`). So an outside agent can't use rac with AI off until these pieces move.

**Agent runs.** A run is one prompt, and nothing of it outlives it. Each message relaunches the agent: about 15 s for Cursor and 25 s for Claude Code to the first tool call (FACT for the rule, CLAIM for timings, `docs/internals/ai.md:241-272,708-716`). The run owns its tools. A provider that once outlived the server's raw pointer crashed the browser (FACT, `docs/internals/ai.md`, "Runs").

**MCP.** This is a per-run Unix socket at `<profile>/rac-agent-mcp/<token>/s`, reached with `/usr/bin/nc -U`. The path shows in `ps`, and there is no secret. All authorization is in `AgentController::HandleToolCall` (FACT, `docs/internals/ai.md:307-332`).

**Tool names already match Chrome's** for the most part: `click`, `type`, `navigate`, `scroll`, `switch_tab`, `go_back` (FACT, `docs/internals/ai.md:388-392`; `digests/chromium-agent-internals.md`, take 11).

**JSON parsing is memory-safe.** `base::JSONReader` is backed by Rust `serde_json_lenient` (FACT, `CR:base/json/json_reader.cc:14-20`). rac's MCP, ACP and chat code use it (FACT, grep of `CR:chrome/browser/rac`).

**Debugging doors.** `--remote-debugging-port` on the real profile is refused only in Google-branded builds (FACT, `CR:chrome/browser/devtools/remote_debugging_server.cc:160-180`). Remote debugging from `chrome://inspect` is off by default. The user must turn it on, and each connection needs approval (FACT, same file, as summarized in `plans/research/long-tail.md:630`). Plan 05 decides both (05-D6). The Core thread builds the refusal inside 05 M0, on 156 after the sync.

**Patch surface.** rac carries 180 patches with 871 stacked hunks in 217 upstream files. 320 hunks are in `ui/views`. 76% sit in files that Helium or ungoogled also patch (FACT, `digests/rac-baseline.md`; per-group recount from `/tmp/rac-overhaul/rac_hunks.tsv`). A dry run to Helium 0.20.1.1 fails 104 hunks at fuzz 2, 46 of them first failures (FACT, `digests/helium.md`).

**Signing.** Only parts listed in `parts.py` are signed. Helium already patches it for Sparkle (FACT, `CR:chrome/installer/mac/signing/parts.py:261-266`).

## What others do

Full tables are in `matrices/architecture-and-storage.md` and `matrices/agents.md`.

- **T3 Code** runs a Node server as its hub: 323 MB after 22 hours, with 17 to 40 GB event stores for some users. It needs a server because its clients are remote and its work needs no browser (FACT, `digests/t3code.md`).
- **Aside** runs an always-on 159 MB Node daemon on a loopback port, with analytics on by default (FACT, `digests/aside.md`).
- **BrowserOS** starts a Bun sidecar and an open CDP port on every launch, with no off switch (FACT, `digests/browseros.md`).
- **ego(lite)** has no daemon. A bundled helper talks over Chromium's single-instance socket, with no auth beyond the OS user (INFERENCE, `digests/ego-lite.md`).
- **Crest** ships a stdio MCP helper that names its caller from the socket's audit token and parent chain (FACT, `digests/long-tail.md`).
- **Cra, Zen, Nook, Ardia, Arc, and Dia** run no local server (FACT, `matrices/architecture-and-storage.md`).
- **Shells.** Ardia runs Chrome's browser process with a React Native UI: 492 hunks in 205 files, 26 in `ui/views`. Its tab switch is 10 to 16 ms, against Helium's 8.5 ms (FACT, `digests/ardia.md`). Cra wraps CEF, which carries 1,044 hunks of its own, and runs with no sandbox (FACT, `digests/cra.md`).

## Options

### Where the backend runs (03-D1)

Every option keeps the browser holding each permission decision, through `AgentController::HandleToolCall` and the guard. None exposes raw CDP.

**Option A: in-browser rac core.** A static action table plus one per-profile service for agent dispatch and the door. A tiny signed relay connects outside agents. *Pros:* no new runtime, the guard is reused, and the engine diff is smallest. *Cons:* runs end when rac quits, crashes, or updates. Nothing runs with rac closed. A rac bug can crash the browser. *Effort:* L, 22 to 32 agent-days for M1 to M3.

**Option B: Chromium utility process.** Agent parsing moves into a child that Chromium idles out (`CR:content/public/browser/service_process_host.h:67`). *Cons:* it still needs A's door, plus mojom and sandbox plumbing. Parsing is already Rust. *Effort:* A plus 5 to 8 days.

**Option C: bundled Rust helper.** `Contents/Helpers/rac-agentd` owns MCP, ACP, history, and schedules (`matrices/architecture-and-storage.md`, Option 3). *Pros:* no Chromium rebuilds, and crash isolation. *Cons:* a second binary to sign and update, two places for state, and a second CI job before the first release build has ever finished. *Effort:* L+, 30 to 45 days.

**Option D: Node or Bun sidecar.** *Cons:* needs JIT and library-validation exceptions, which make it rac's least hardened process. Every product that took this path ended up always on (FACT, `digests/local-first-and-sidecars.md`). Rejected.

**Option E: MCP target only.** Ship the door, nothing else. Least code, but rac's own assistant gets no better. Its small surface is grafted into A.

| | A. In-browser | B. Utility process | C. Rust helper | D. Bun / Node |
| --- | --- | --- | --- | --- |
| Memory, feature off | 0 | 0 | 0 | 0 if lazy |
| Memory, door on, idle | No new process (INFERENCE) | 16 to 38 MB | 5 to 10 MB (estimate) | Bun 22.5 MB; Node 54 to 67 MB |
| Start cost | 0 at launch (lazy) | Spawn, unmeasured | About 14 ms | 7 to 35 ms |
| Added to the app | Relay under 1 MB (INFERENCE) | 0 | 1 to 8 MB | 64 to 146 MB |
| New entitlements | None | None | None | JIT, unsigned memory |
| Engine hunks | 7 to 12 | 15 to 25 | 9 to 16 | 9 to 16 |
| Rebase cost | Low | Medium | Low, plus cargo crates | Low, plus npm churn |

Timings come from existing binaries, measured warm on the maintainer's Mac (`digests/local-first-and-sidecars.md`, "Runtime comparison"). Hunks are estimates.

**Recommendation: A.** On this point the matrix and this plan agree. The disagreement is narrow. The matrix treats a warm agent as a reason for a Rust helper. It isn't one: ACP agents are already child processes, so keeping one alive is a lifecycle change (M3). The matrix's other triggers stand:
- **Routines with rac fully closed.** These would need the browser anyway. Plan 05 decides them (D59 in decisions.md). This plan adds no helper.
- **Crash isolation.** JSON parsing is Rust-backed. The new exposure is a socket feeding C++ handlers, so M2 hardens it.

A future helper is justified only by a named feature that must run without opening rac, such as phone remote control. None is planned.

### How outside agents connect (03-D2)

| Transport | For | Against |
| --- | --- | --- |
| **Socket plus signed relay (stdio MCP)** | No port. Works with `claude mcp add`. Audit-token check possible (`CR:base/mac/code_signature.h:34`) | Sandboxed agents may not reach it (ego #188). The peer shows as the relay, not the agent |
| Loopback HTTP plus OAuth (T3) | `mcp login` flows | A port, Origin checks, more surface |
| Single-instance socket (ego) | Already exists (`CR:chrome/browser/process_singleton_posix.cc:141-143`) | A hot upstream file; no auth |
| Raw CDP (Ardia) | Agents know it | Bypasses the guard |

**Recommendation: socket, relay, and per-client tokens** (M2). The real boundary is the OS user, because any same-user process can run the relay. Tokens give each client a name, a level, and a way to revoke it. The audit-token check adds defence in depth.

### How to shrink the patch surface (03-D4, 03-D5)

**S1: stay on Views, thin the hooks.** Keep Chromium's window, and keep building on Helium's vertical tabs, frameless mode, and split view. Each upstream registry gets one rac call. Today `prefs_util.cc` carries 11 rac patches, `settings_localized_strings_provider.cc` 13, `browser_command_controller.cc` 10, and `ui/BUILD.gn` 26 (FACT, `digests/rac-baseline.md`). *Pros:* no rewrite, and every Chrome dialog and the sandbox come free. *Cons:* motion in Views is harder; plan 02's spring helper answers that. *Effort:* L, 25 to 35 agent-days.

**S2: native AppKit shell in Chromium's process** (Ardia, Dia, Crest). Ardia still has 492 hunks in 205 files. Crest's native host is 205 hunks plus a 14,406-line overlay, and every Chrome dialog must be rebuilt (FACT, `digests/ardia.md`, `digests/long-tail.md`). It would rewrite rac's 67 Views files (16,108 lines) and drop Helium's UI work. React Native added a tab-switch tax (`digests/ardia.md`). *Effort:* XL, 40 to 80 days.

**Rejected:**

| Option | Why not |
| --- | --- |
| Out-of-process Chromium (Atlas, Refrax) | XL+. Extension support is unverified, and Atlas needed a funded team (`digests/closed-ai-browsers.md`, `digests/long-tail.md`) |
| CEF (Cra) | CEF carries 1,044 hunks itself. Cra runs with no sandbox and loses Helium's privacy patches. Ardia and Mori both left CEF (`digests/cra.md`, `digests/ardia.md`, `plans/research/long-tail.md:76`) |
| HTML browser UI (`kWebium`) | An experiment, off by default (`CR:chrome/common/chrome_features.cc:1966`). Mori rejected it |

**The metric (03-D5).** Raw stacked hunks can be gamed. Folding fix patches, for example, lowers the count without lowering conflicts. So hold two numbers, and have plan 06 run them as a check:
1. **Net-diff hunks.** Hunks in the diff between the Helium-patched tree and rac's final tree, in upstream files, reported separately for the files Helium also touches.
2. **First-failure hunks** in each sync's fuzz-0 dry run. Today that is 46 at two majors behind.

Plan 06 M0 builds the counter and reports the net-diff baseline. Until then, the stacked counts below stand in.

| Group | Stacked hunks today | Target | How |
| --- | --- | --- | --- |
| look | 161 | 60 | Delete the dead `horizontal-tabs` restyle; move logic into one rac-owned view (plan 01) |
| spaces | 127 | 85 | Thin hooks into rac-owned views; one command-table hook |
| ai | 98 | 60 | One registration hook each for prefs, strings, WebUI, factories |
| pinned | 95 | 65 | As spaces |
| settings | 91 | 35 | Adopt Helium's Layout section; one strings hook, one prefs hook |
| sidebar-address-bar | 64 | 45 | Thin location-bar hooks |
| sidebar-reveal | 60 | 20 | Rebuilt on Helium's overlay during the sync (plan 06) |
| agent | 58 | 45 | One adapter around Chromium's actor code (`digests/chromium-agent-internals.md`, take 3) |
| others (updates, pip, onboarding, sidebar, branding, privacy, dev) | 117 | 105 | Mostly leave |
| **Today's features** | **871** | **520** | |
| Added by plans 01, 02, 04, 05, 07 | 0 | +60 to 110 | Each through single hooks |
| **Total** | **871** | **580 to 630** | **Accept 630; aim for 550 by routing new features through existing hooks; stretch 450** |

Ardia, with no AI and a native shell, sits at 492 (FACT, `digests/ardia.md`). So under 400 is not credible for rac's shape. Plan 06's dates for "under 400" should use these targets instead.

**Spike trigger.** Run a one-week S2 spike if, after the second sync on the thinner base, either holds: stacked hunks are above 650, or a sync has more than 30 first-failure hunks. The spike measures files touched, dialogs to rebuild, tab-switch time, and memory (`digests/long-tail.md`, item C6).

**Why it matters.** Chromium ships a major every two weeks (FACT, `digests/helium.md`). Plan 06 budgets 1 to 3 days per sync and lets the cadence vary (06-D7). That puts the yearly cost somewhere between about 15 and 75 agent-days (INFERENCE from plan 06).

## Recommended plan

Calendar rules (`/tmp/rac-overhaul/alignment.md`, ruling 1). Weeks count from the maintainer's approval. Plan 06 owns the sync (06 M2), the launch build (hard stop 2026-12-15), and the weeks. Work in rac-owned files may start on Chromium 154 and be rebased. Work in hot files shared with Helium waits for the sync to 156 and for each worktree's base-tree rebuild.

**Before 2026-12-22.** Nothing here gates launch or helps Arc refugees directly. M0, and M1's rac-owned parts, may run in parallel if they don't slow plan 06. The door, the warm agent, and M4 come after launch.

### M0. Spikes (weeks 1 to 2; Chromium 154; 2 to 3 agent-days)

- **Goal.** Replace the unknowns behind M2 and M3 with measurements.
- **Agent startup (half a day).** Time where Claude Code's 25 s goes: `npx` resolve, Node start, adapter init, `session/new`, first model token. If `session/new` plus the first token dominate, warmth saves less, and M3's target changes.
- **Door (1 to 2 days).** Results go in a pass/fail table:

| Check | Pass means |
| --- | --- |
| Claude Code over `rac mcp`, sandbox off and on | Lists tools in both, or a documented allowlist path |
| Codex, Cursor, and OpenCode over `rac mcp` | Lists tools |
| Socket under Application Support vs a short `$TMPDIR` path | No TCC prompt (macOS's privacy permission dialog) on the chosen path |
| `mcp add` with a token vs `mcp login` | stdio is enough, or loopback HTTP moves into M2 |
| Relay with rac closed | Opens the right profile hidden, waits for the socket, and handles the single-instance handoff with no window or focus change |

- **Acceptance.** Both tables committed in the M2 PR description. HTTP is in or out of the plan.
- **Patch surface.** None.

### M1. Action table and the rac core split (weeks 2 to 5; 10 to 14 agent-days)

- **Goal.** One list of actions, and agent pieces that no longer depend on the AI switch.
- **Build slots.** Per the master plan's build-slot rule, launch-gate work gets slots first. This milestone writes code and waits for a free slot.
- **Tasks.**
  1. **Static table** `rac_actions.{h,cc}`. It is compiled-in data, with no service. Fields: id, label, default shortcut and availability (plan 07's fields), JSON schema, MCP annotations (read-only, destructive, idempotent, open-world), rac's risk class, and surfaces. The sidebar, command bar (Views, plan 01), and shortcuts call handlers directly. That is one function call, and plan 01 measures the one-frame open. AI-only actions are marked "AI on" and never show with AI off.
  2. **`RacCoreService`**, built only when the assistant's browser control or the door needs it. Move `AgentController`, the guard, containment, and the MCP server under it. `AiService` becomes one client. Lifetime rule: the service owns the controller. Each run or warm session owns its `AgentMcpTools`. The MCP server stops before its tool provider is deleted, which is the crash in `docs/internals/ai.md`, "Runs". Cost: 5 to 7 days of the 10 to 14.
  3. Generate MCP `tools/list` from the table. Keep today's tool names. New tools use Chrome's names.
  4. After the sync, one `rac::EnsureFactoriesBuilt()` hook replaces the two factory registrations.
- **Acceptance.**
  - A test fails if an action lacks an annotation or risk class.
  - `tools/list` output is identical for today's 15 tools.
  - With AI and the door off, no `RacCoreService` or controller exists. `ps` and `lsof` in a fresh profile show no rac child and no rac socket.
  - With AI off, no AI row or label appears in the command bar or menus.
- **Verification.** Unit tests in `rac_agent_unittests`. A video of one agent turn, unchanged. Screenshots of the command bar with AI off and on.
- **Chromium.** Tasks 1 to 3 on 154, in rac-owned files. Task 4 on 156.
- **Patch surface.** Net −1 hunk. Plan 07's shortcut hook also removes the per-command hunks.

### M2. The outside-agent door (after launch; Chromium 156; 9 to 13 agent-days)

- **Gate.** Plan 05's `auto` fix and injection evals are green (05 M0).
- **One milestone with plan 05 M1.** This milestone and plan 05's M1 (the read-only door) are one piece of work, after launch (W7 or later). It may be built on a branch from W4 if a build slot is free. M1's split may still land before launch.
- **Tasks.**
  1. **Relay.** `rac.app/Contents/Helpers/rac`, a small GN C++ program that copies bytes between stdio and the socket. It holds no state. Commands are `rac mcp`, `rac skill`, and verbs that map one-to-one to table actions (plan 05 picks them).
  2. **Socket.** One per profile, existing only while `rac.agents.outside_access` is on for that profile. Folder mode 0700, socket mode 0600, on the path M0 chose. Incognito and guest profiles are never reachable.
  3. **Tokens.**
     - Pairing in Settings mints a 256-bit token per client. "Add to Claude Code" writes it into that agent's MCP config, or Settings shows a copy line containing it.
     - The browser keeps only a SHA-256 hash, plus the client's name, level, and last use.
     - The relay sends the token as its first frame. It is compared in constant time. Revoke deletes the hash, so the next call fails.
     - A connection with no valid token is refused with "Pair this agent in rac Settings". The card flow is plan 05's.
  4. **Defence in depth.** Accept only peers whose audit token is rac's signed relay. The relay walks its parent chain, Crest-style, to show the agent's name (`digests/long-tail.md`). Unsigned dev builds skip the signature check, but never the token check.
  5. **Input hardening.** No handler runs before the peer and token checks. Frames are capped at 1 MiB and JSON nesting at 64 levels. Each client is rate-limited to 20 calls a second, with at most 4 clients per profile. Parsing happens on the IO thread with the Rust reader, and only typed structs reach the UI thread. A fuzz test covers the framing parser.
  6. **rac-launched ACP agents** use the relay instead of `nc -U`. The token rides an inherited file descriptor, so nothing shows in `ps` (T3's fd-3 pattern, `digests/t3code.md`).
  7. **When rac is closed**, the relay opens it as M0 proved.
  8. **Packaging.** Bundle data and the dependency in `chrome/BUILD.gn` (1 to 2 hunks). Signing in `parts.py`, which Helium also patches (1 to 2). Possibly one in the signing pipeline (0 to 1). No new entitlements.
- **Acceptance.**
  - With AI off and the door on, `claude mcp add` with the token lists tools.
  - With the door off, `lsof` shows no socket.
  - A revoked token is refused.
  - Oversized and garbage frames are dropped without crashing.
  - Every call passes the guard.
- **Signed-build acceptance** depends on plan 06's first signed release (06 M1). `codesign --verify --deep --strict` and notarization pass, and an unsigned peer is refused.
- **Verification.** Screenshots of the Settings switch, the client list, and the "Outside agents: on" label beside the AI switch, in light and dark. A video of Claude Code in Terminal driving a background tab with AI off.
- **Patch surface.** About 4 to 6 hunks here, plus about 2 in plan 05 for prefs and strings.

### M3. Warm agent (03-D3; after M1; ships after launch; 4 to 6 agent-days)

- **Model.**
  - One warm ACP agent per profile, kept alive while its panel is open.
  - It reuses one ACP session, so the conversation carries over.
  - The session's MCP endpoint lives as long as the session. The session owns its tool provider.
  - The controller refuses tool calls outside an active turn ("no active turn"), so idle time grants nothing.
  - The tool list is fixed for the session's life. A changed level or site rule applies at the guard on the next call.
- **Ends on:** 5 idle minutes, panel close, Stop, AI off, or moderate memory pressure (`base::MemoryPressureListener`). Quit, crash, and Sparkle's relaunch kill the process group. An unfinished turn shows "Stopped when rac quit" on the next open.
- **Acceptance.**
  - The second message is at least 5 times faster to its first tool call than a cold start, or meets the target M0 sets.
  - No agent process remains 5 minutes after the panel closes.
  - Run-id checks hold across warm turns.
  - Update `docs/internals/ai.md`, "Runs".
- **Verification.** A side-by-side video, cold versus warm, and a `ps` listing after close.
- **Patch surface.** 0 hunks.

### M4. Thin the hooks (after launch and the sync; Chromium 156 or later; 25 to 35 agent-days)

- **Goal.** Reach the per-group targets above.
- **Order.** settings, look, spaces, pinned, sidebar-address-bar, ai, then agent. sidebar-reveal is done in plan 06's sync.
- **Order rule.** Refactor a group only when no feature thread has an open PR on it.
- **Acceptance.**
  - Each group meets its target, or its PR explains why.
  - Plan 06's ratchet fails PRs that grow net-diff hunks without a budget change.
  - Patches apply with fuzz 0.
- **Verification.** The screenshot matrix per group: sidebar full and hidden, edge reveal, light and dark, address bar in the toolbar and the sidebar, installed web app windows. No visual change beyond noise.
- **Patch surface.** About −350 stacked hunks.

### Where each part lives

| Part | Runs in | Owner |
| --- | --- | --- |
| AI providers | Browser process, `SimpleURLLoader`. No Swift helper; local models stay Ollama and LM Studio | 05 |
| Conversation and agent history | Browser process, SQLite through `sql::Database` in the profile, encrypted, bounded | 04 |
| Agent runtime (loop, ACP client, guard) | `RacCoreService` in the browser; ACP agents as child processes | 03 placement, 05 policy |
| Outside-agent door (MCP, CLI, skills) | Per-profile socket plus signed relay | 03 transport, 05 policy |
| Action table | Static data in the browser | 03; 07 adds fields; 01 and 05 consume it |
| Command bar | Views; rows are C++ from the action table | 01 |
| Assistant panel, settings | WebUI, as clients of the core | 01 |
| Routines | Browser process, while rac runs | 05 (D59) |
| Sync | Browser process, sealed files in a user folder | 04 |

## Fit with the non-negotiables

- **Private.** No port, no server, no new traffic. The socket exists per profile, only while its switch is on. Holds.
- **Never slower than Helium.** No resident process. The table is static data, and the service is lazy. A warm agent costs the agent's own memory, 0.7 to 1.1 GB for long Claude sessions (FACT, `digests/local-first-and-sidecars.md`), only while its panel is open, and memory pressure ends it. Holds once plan 06's benchmark confirms it.
- **AI off costs nothing.** With AI and the door off, no service, socket, or child exists (M1 acceptance). Chromium's idle `ActorKeyedService` stays on because the renderer `CHECK`s it, and its cost is unmeasured (`digests/chromium-agent-internals.md`). Holds.
- **Door off costs nothing.** This is the new scoped promise (03-D6). M2's `lsof` acceptance covers it.
- **Cheap to update.** M1 to M3 add about 4 to 6 hunks and remove a few. M4 removes about 350. Holds.
- **Calm UI.** New surfaces are a switch, a list, and a label. Holds.
- **GPL.** All new code is rac's. BrowserOS is AGPL, so ideas only (`digests/browseros.md`). Holds.
- **Bent.** M3 changes "a run is one prompt, and nothing of it outlives it" (`docs/internals/ai.md:243`). That needs sign-off through 03-D3. M2 changes "rac's MCP server serves only the agent it launched" (`docs/roadmap.md`, "Later"), which the maintainer brief asks for.

## Dependencies on other plans

- **01 ui-shell.** Builds the command bar in Views on the action table. Follows one hook per registry. Draws the Outside agents settings page. Its shell spike uses this plan's trigger.
- **02 visual-design-and-motion.** Styles the new settings rows and supplies the Views spring helper. Owns token names.
- **04 data-storage-import-sync.** Owns the history schema, encryption migration, retention, and sync files.
- **05 agents-and-ai.** Owns door policy, pairing UX, tool list, levels, evals (the gate for M2), the debug doors (05-D6), routines (D59), and the agent workspace rendering spike. It refers to 03-D3 for the warm agent.
- **06 engineering-and-shipping.** Owns the sync, the launch calendar, the base-tree rebuild, the benchmark, the hunk counter and ratchet using 03-D5's metric, signed builds (gating M2's signed acceptance), and the plain-folder move (06-D12). That move needs a throwaway-worktree spike on copy versus link, because copies change mtimes.
- **07 power-features.** Adds shortcut and label fields to the table, and keeps only its site-pattern matcher.

## Risks and unknowns

- **Sandboxed agents and TCC.** These can block the socket design. M0 tests both before M2 starts.
- **Peer identity is weak.** The real boundary is the OS user. Tokens in agent config files can be read by that user. The UI must say that pairing is consent and revocation, not proof of identity.
- **Warm sessions.** Reusing one ACP session may hit adapter bugs or context growth. The fallback is a new session per turn on a live process.
- **Hidden launch.** Opening rac with no window may still restore a session or show a Dock icon. M0 checks this.
- **MCP churn.** MCP 2026-07-28 drops `initialize`, and ACP v2 is a breaking draft (FACT, `digests/local-first-and-sidecars.md`). The table isolates rac from both.
- **Shrinking can regress UI.** There is one UI test today, so the screenshot matrix is the safety net.
- **The hunk targets are estimates** until plan 06's counter gives net-diff numbers.

## Open questions

1. Should a client with no token trigger a "pair this agent?" card, or only a refusal? Plan 05's call.
2. Is 1 MiB the right frame cap for large snapshots? Plan 05's limits on tool output may allow a lower one.
3. Does the warm agent prewarm when the panel opens, or only after the first message?
4. Will Helium's experimental vault sync carry `rac.*` prefs? This affects plan 04.
5. Does Anthropic's rule on third-party use of Claude credentials touch the ACP adapter path? Unclear (`matrices/architecture-and-storage.md`, question 10).
6. Rejected finding: critique item 13's versioned tool list. Tool names don't change, so no version is needed.
7. Rejected finding: critique item 14's four-decision list. It placed the overlay here, but the overlay belongs to plan 06 (06-D12) under the rulings.

## Draft thread brief

**DRAFT. Do not launch until the maintainer approves this plan and its decisions.**

> **Thread: rac core and the outside-agent door (architecture and backend)**
>
> **Model.** Claude Opus 5.5 for design, the core split, socket checks, tokens, and signing. Sonnet 5.5 or a strong open-weight model for scoped tasks such as the relay, tests, and the fuzz harness.
>
> **Read first.** `AGENTS.md`, `VISION.md`, `docs/internals/ai.md`, `plans/03-core-architecture.md`, the approved plans 05 and 06, and `/tmp/rac-overhaul/alignment.md`.
>
> **Order.** M0 spikes, then M1 (rac-owned parts on 154, the hook after the sync), then M3, then M2 once plan 05's evals pass, then M4 after launch. Follow plan 06's weeks and sync freeze (plan 06's default list, D11 in decisions.md).
>
> **Hard rules.**
> - Feature worktrees only: `source dev.sh && he build`, then `devutils/rac/worktree.sh run`. Never `he run` or `open` there.
> - Never touch real profiles, `helium-chromium/`, or Helium's patch folders. Post nothing upstream.
> - No resident process, no TCP port unless M0 proves it is needed, no new entitlements, no telemetry.
> - With AI and the door off, rac creates no service, socket, or child. Prove it with `ps` and `lsof` in a fresh profile.
> - Every call goes through `AgentController::HandleToolCall`. No policy at the MCP layer. No raw CDP.
> - Report the net-diff hunk delta in every PR.
>
> **Done means.** Unit tests run locally. Benchmark numbers where relevant. Screenshots of every visible surface in light and dark. Videos for the door and the warm agent. Updated docs where a decision changed.
>
> **Stop and ask** before any full build, more than 10 new upstream hunks, a new signed part beyond the relay, or a socket design that M0 failed.
