# Long tail of Arc and Dia alternatives: planning digest

Source dossier: `plans/research/long-tail.md` (swept 2026-10-25; Arc stops 2026-12-22; clones in `/tmp/rac-overhaul/src/`). Its Verification section (38 items) is authoritative and already folded in. Zen, Nook, Ora, Ardia, Helium, BrowserOS, T3 Code have their own dossiers. Tags: **FACT** = primary source, **CLAIM** = vendor or press, **INFERENCE** = reasoning. `crest:<path>` means a file in the Crest clone.

## In plain English

Many small teams are building Arc replacements right now. Most are weeks old and written with AI agents, like rac. The strongest, Crest, already ships. Chrome, Edge and Firefox now have vertical tabs, so a sidebar alone wins nobody. Arc users will miss other things. Each Arc space could use different accounts. rac can't do that yet. rac also can't carry a sidebar to a second Mac, and it may quietly stop a Slack tab in a hidden space. Other projects show cheap fixes. One Chromium switch may also let outside tools control rac. Check that first.

## Key facts

### The field (stars and dates from `gh api`, 2026-10-25)

- **Crest** (`pauljoda/Crest`, MPL-2.0, 788 stars, created 2026-08-15) is the real threat (INFERENCE). SwiftUI shell over a C# core. Engine: ungoogled-chromium 155.0.8059.84, WebKit per page (auto for FairPlay). macOS 26.1+, Apple silicon, plus iPhone and iPad. 268 releases (12 stable, v0.4.0 to v0.8.50 in 66 days). 1 main author (560 commits) plus 11 other humans. 92,023 lines C#, 239,940 Swift (12,567 tests), 487 test functions in 168 files. "Early access. Security not independently audited." Ships AI-contribution rules (`crest:AGENTS.md`).
- **Stedding** (BSD-3-Clause, 55 stars, 2026-08-30): rac's mirror image. Patch series on plain Chromium 156, macOS and Windows, 38 releases. 103 patches, 504 upstream files, 3,086 hunks, 581 new files (rac: ~217 files, ~870 hunks). No bundled model; a later ADR could allow opt-in AI. Many spec rows "written, tests not yet run."
- **Refrax** (GPL-3.0, 48 stars): Swift; per-tab WebKit or Chromium, the latter a separate signed app shown through remote layers. Only 7 patches, 22 files, 42 hunks, plus a 6,812-line overlay. `refrax-ctl` CLI.
- **Mori** (MIT, 140 stars): three rewrites in five months, ending on Chromium Views. Dropped CEF: no extensions (CLAIM).
- Small Electron clones (Yalqen, Meridian, Tangent, Flow) and archived Aura change nothing for rac. Thorium and Supermium are one-person forks far behind Chromium; Ladybird has no release.
- Closed: Dia (Chromium M156, weekly), Vivaldi, Orion, SigmaOS (stalled), Sidekick (dead), Wavebox, Opera Neon. **Atlas reportedly shut down 2026-08-09** (CLAIM). Chrome vertical tabs stable in 146 (CLAIM), Firefox 136, Edge since 2021.

### Per-space sign-ins in one window (rac has none)

- Ships in Arc, Crest (full engine profile per space), Stedding (opt-in storage partition, beta), Brave Containers (1.92, 2026-07-02), Wavebox, Orion 1.1, Zen. rac spaces share cookies.
- **Correction to the Zen digest:** "Chromium has no per-tab cookie jar in a normal window" is wrong. Stedding uses `SiteInstance::CreateForFixedStoragePartition` against `StoragePartitionConfig::Create(context, "spaces", profile_id, false)`, one upstream hunk in `browser_navigator.cc` (**FACT** ADR 0019).
- Trap: session restore drops the partition. Brave writes a virtual URL prefix `containers+<uuid>:` into saved navigation entries (**FACT** `brave-core:docs/containers/session_persistence.md`). Limit: `chrome.cookies` without a partition sees only the default jar.
- `browser_navigator.cc` is already edited by 3 patches (rac `pinned/close-and-navigate.patch`; Helium `zen-mode.patch`, `override-chrome-protocol.patch`).

### Architecture models

- Patch series + Views (rac, Stedding, Mori, Brave): all Chrome UI free; rebase every two weeks.
- Native shell in Chromium's process (Crest): `native-host.patch` 95 files, 205 hunks, plus 14,406-line overlay and 4,963 lines of Swift glue. Chrome's dialogs (permissions, extension install, login, PiP, translate, autofill) must be re-hosted.
- Out-of-process Chromium (Atlas "OWL", Refrax): UI survives engine hangs; all interaction crosses IPC.
- `kWebium` HTML browser UI exists in rac's tree, off by default (`chrome_features.cc:1966`).
- Crest control plane: every state change is an intent (`core.send(OpenTab(...))`); UI reads only `core.state`. Refrax treats the engine as untrusted: 256 KiB message cap, 8 KiB strings, page closed after 32 bad messages, no keychain or history (`CONTRACT.md:300-312`).

### Motion (exact values, **FACT**)

Crest (`CrestMotion.swift`, all behind a reduce-motion gate; reduced motion = 0.20 s cross-fade): hover 0.14 s easeInOut; press 0.14 s (compact 0.12) easeOut; surface/content reveal 0.12 s; palette open and dismissal 0.18 s; disclosure and selection 0.20 s; collection change 0.22 s snappy; floating pane/toolbar 0.24 s; sidebar morph 0.28 s smooth, retreat 0.30 s; space swipe 0.32 s snappy, no bounce; Quick Peek entrance 0.34 s; boundary shake 0.36 s; download "flight" spring 0.68 s, bounce 0.16; agent pointer glide 0.35 s.

Stedding (`docs/features/motion.md:22-23`), measured in Views on Mac:
- Chromium's "emphasized" curve moved a collapsing sidebar 33% (88 DIP) in one frame at 120 Hz. Switched to `gfx::Tween::EASE_OUT` at Chromium's Mac times (350/400 ms; hover 200/250 ms); largest step fell to 7-14% per frame.
- Space switch keeps the departing space as a compositor-rastered paint recording, not a UI-thread bitmap: 4.6-8.8 ms down to 0.7 ms; whole switch 18-22 ms down to 13-14 ms (O6 not yet seen by the owner). `MotionFramesTest` logs views laid out and painted per frame.

Feel: wrap-around space swipe with boundary shake; sideways wheel over sidebar switches space (Stedding).

### Data and storage

- **Crest:** one SQLite file of JSON-backed records; engine data in `~/Library/Application Support/Crest/Chromium`; agent sockets in `.../Crest/Agents`; passwords in Keychain by origin and space. Optional CloudKit sync to the user's private database (fractional ordering, deterministic merge, deletion tombstones, refuses stale merges; passwords never enter it). Portable archive excludes passwords, cookies, site storage, extensions. Says it "may" add a search source parameter.
- **Stedding:** spaces registry in the profile; portable sidebar file (Arc's JSON shape plus extras); sync through a user-picked folder, no server. `docs/PRIVACY.md:72-95` publishes a **recorded run** of every host a fresh profile contacts; it found and removed a Google push check-in and an account check.
- Sidebery: timed snapshots, auto-export JSON/Markdown. Min: uploads usage stats with a client ID unless turned off. Edge Workspaces: sharing removed (**FACT** MC1192661), users reported lost workspaces (CLAIM). Dia deleted its memory feature in 1.50.0 (2026-09-24).
- Server-free sync is a shipped pattern, so "Sync maybe later" need not break "no rac servers" (INFERENCE).

### Agents and AI

- No long-tail product publishes injection evals. rac's guard plus critic is above median (INFERENCE).
- **Crest outside-agent MCP:** helper inside the app bundle (stdio), per space, 29 tools shaped like `chrome-devtools-mcp` (snapshot uids, click, fill, evaluate_script, `read_page_text` without form values, `handle_dialog` never "leave page?"). rac: 15 tools, 25-call cap, MCP only for its own launched agent.
- **Identity by code signature:** read the peer's audit token from the Unix socket (`LOCAL_PEERTOKEN`), check it is Crest's signed helper, walk up to four parents to the first non-shell program, read Team ID and signing ID. Interpreters (`node`, `python`, `bun`, `uv`, `npx`, `osascript`) vouch for nothing, so the key adds the agent's declared name (`BrowserAgentPeer.swift:48-137`). Doc admits it is not a defense against malware already on the Mac.
- **Crest reach limits:** only spaces the user enabled; never private windows, browser pages or files; http/https/blank only; password values omitted; cookies, auth headers and bodies hidden; page-world scripts behind a separate toggle; history deletes and opening windows ask. Visibility: badge and outline in the agent's colour, a bar naming the agent, a pointer, "Stop Agent in This Tab", "Stop All Agents".
- **Brave AI browsing** (flag, early access): agent runs only in a brand-new profile, so logins do not cross; a second model checks intent and never sees raw page content. Opposite of rac and Nook.
- **Chromium back door (FACT in rac's tree):** `kDevToolsAcceptDebuggingConnections` is on for macOS (`features.cc:203-211`), unpatched by Helium or rac. After the user toggles `chrome://inspect/#remote-debugging`, `chrome-devtools-mcp --autoConnect` (Chrome 144+) reads `DevToolsActivePort`. Chromium 154 runs the server in `kWithApprovalOnly` mode; a comment says each connection needs approval (`remote_debugging_server.cc:247,403-405`). Code reading only; never seen running. If it works, an outside agent bypasses rac's guard, critic, cards and site rules (INFERENCE).
- **Opera Neon:** free tier for your own agents via local CLI (no account) or MCP (Opera account, OAuth2, Opera proxy). CLI claims up to 80% fewer tokens via compact snapshots and next-step hints (CLAIM). **Floorp OS:** loopback HTTP port 58261, off by default, empty token by default, `Access-Control-Allow-Origin: *` (**FACT**).
- **Subscription terms:** Anthropic's legal page bars third parties routing requests through Free/Pro/Max credentials, allows signing in to the unmodified Claude Code binary, and says Agent SDK developers "should use API key authentication." rac runs `npx @agentclientprotocol/claude-agent-acp@0.93.0` (`patches/rac/ai/21-agent-providers.patch:668`), built on `@anthropic-ai/claude-agent-sdk`. Which rule applies is unclear (INFERENCE).

### Build, release, engineering

- **Crest CI:** checks whether an engine for the exact recipe is published; if not, builds on a self-hosted Mac (1,440-minute timeout); app builds reuse it on GitHub runners. Developer ID, notarized DMG, Sparkle. Nightly. 6-hourly upstream check; update must apply every hunk **without fuzz**; new milestone needs `--allow-major`.
- **Stedding:** security fixes within 7 days (in the wild) or 14; new milestone waits until 1% of stable users. **Mori:** headless Playwright suites launch the built browser.
- Helium sets `chrome_pgo_phase=0` (`flags.gn:1`); Crest uses Chromium's mac-arm PGO profile with ThinLTO. Helium removes the Translate settings section (`patches/series:242`). rac supports macOS 13+; Crest needs 26.1.

## What rac should take (ranked)

Cost: XS <1 d; S 1-3 d; M 1-2 w; L 3-6 w (INFERENCE). Thread = UI or architecture.

Product ideas for Arc refugees:

1. **Separate sign-ins per space** — M-L, arch. Setting "Use separate sign-ins", off by default, on for imported Arc spaces that had their own profile; favorites stay shared. Options: (A) storage partition per space (Brave, Stedding), one upstream hunk plus Brave's restore prefix, covering restart and Reopen closed tab; extensions, history, passwords stay shared. (B) full profile per space in one window (Arc, Crest): L+. (C) keep profile = window, add Dia-style swipe between windows: S-M, UI.
2. **"Keep loaded" and smarter unloading** — S, arch. Never unload tabs with an open WebSocket, WebRTC or notification permission. rac unloads hidden spaces after 15 min, keeping audio, PiP, loading tabs (**FACT** `spaces_window_manager.h:65,134-137`).
3. **Carry the sidebar to another Mac, no server** — S then M, arch. Export/Import spaces with stable ids (import merges, never closes an open tab); then sync through a folder, one file per Mac, using Crest's merge rules. Doubles as backup (Zen Take 1).
4. **"Clear" today's tabs plus Archive** — S then M, UI. Undo toast; per-space Archive for 30 days; no automatic archiving.
5. **On-device page translation** (Apple Translation), up from phase 6 — M.
6. **Link routing (Air Traffic Control)** moved into the import wave — M, arch. Contains/Exact rules, top to bottom.
7. **Favorite previews, local only** — M, UI. Hover a loaded favorite ~400 ms; unread count from the title; no OAuth.
8. **Dark pages** — S-M, UI. `force_dark_mode_enabled` plus `AUTO_DARK_WEB_CONTENT`; paint `#121212` before first frame.
9. **"Hide distracting items" as first Boost** — S-M, UI.
10. **Arc muscle-memory bundle** — XS-S each, UI: new tabs at top; abandoned empty new tabs clear (Dia 1.38); Arc-style Ctrl+Tab switcher; Copy URL as Markdown; PiP title returns to tab.
11. **Touch ID space lock** — S-M (after #1). 12. **AI controls page** (every AI surface, what it sends, master switch) — S, UI. 13. Web apps keeping a space's sign-in — S after #1. 14. Same space in two windows — L. 15. Localhost developer bar — M.

Agent ideas:

- **B1. Decide the `chrome://inspect` toggle now** — XS to verify on a build, then S: (a) compile out or hide, (b) keep with a plain warning, (c) keep off until rac's own outside-agent MCP exists. Do before the rest.
- **B2. Identify outside agents by code signature**; ask once per agent, "Forget" to revoke — M, arch.
- **B3. Scope and minimise outside-agent data** (Crest's list) — S-M.
- **B4. Ship the MCP server inside the app** (`rac.app/Contents/Helpers/<helper> mcp`, stdio, "Copy setup") — S-M. No npm package.
- **B5. Clean-room agent space** with no sign-ins — S after #1.
- **B6. Agent colour, badge, outline, 0.35 s pointer, "Stop all agents"** — S, UI.
- **B7. Compact snapshots with next-step hints** — S; measure first.

Engineering:

- **C1. Engine built once on a self-hosted Mac, keyed by a recipe hash** — S-M, arch. Cheapest route to one signed build; needs approval. Less clean for rac (Chromium + Helium + rac patches).
- **C2. No-fuzz gate plus scheduled upstream check** — S (overlaps Zen Take 2).
- **C3. Recorded network run** (fresh profile, 5-10 min, `--log-net-log`, hosts vs published allowlist) — S.
- **C4. Frame-level motion checks, paint-recording space switch, EASE_OUT sidebar** — S-M, UI.
- **C5. Measure PGO and ThinLTO** — S; needs a full build and approval.
- **C6. One-week architecture spike before any UI rewrite**: Views vs Crest-style native window vs Refrax/Atlas out-of-process vs `kWebium`; measure files touched, rebuilt dialogs, tab-switch time, memory — M.
- **C7. Licence map:** Refrax GPL-3.0 (direct); Stedding BSD-3, Mori MIT (copy with notices); Crest, Floorp, Brave MPL-2.0 (usable in GPL-3.0 unless a file says "Incompatible With Secondary Licenses"; INFERENCE). Useful for Crest's `ArcSidebar.cs` importer.

Also (INFERENCE): layout presets over many toggles; vibrancy needs an `NSVisualEffectView` under the sidebar (untested).

## What rac should avoid

- A second engine (WebKit fallback): doubles testing; sign-ins don't carry across engines (Crest 0.7.0).
- Web panels and sidebar apps (Edge 149 removed its list, CLAIM; Sidekick died).
- Server-backed shared spaces (Edge dropped sharing); an AI "memory" feature (Dia deleted it).
- Loopback HTTP automation with optional token and wildcard CORS (Floorp OS): use a Unix socket plus peer checks.
- Opt-out usage stats (Min, Yab); search partner parameters (Crest "may"); outside-agent MCP through a vendor account (Opera).
- Wellness and suite features; config as code, hundreds of settings.
- CEF; more platforms before the Mac app ships; tree tabs as default; native-shell rewrites without the spike.
- Removing a layout after users depend on it (Safari 26 compact bar, Edge Collections; CLAIM).

## Caveats

- Crest, Stedding and the rest were read as code and docs, **not run**. Crest's per-profile memory, extension coverage and crash rate are unknown; Refrax extension support is unverified.
- Unconfirmed: which tabs the 15-minute unload hits; where rac inserts new tabs; whether MRU cycling has a switcher; whether Helium's translate runs; merge cost of Stedding's hunk.
- Press-only items stay CLAIM: Chrome vertical-tab and split-view dates (split view contradicted across sources), Edge 149 removals, Safari compact bar, SigmaOS, Sidekick, Wavebox, Comet, Opera Neon price. Atlas shutdown is CLAIM. Firefox AI Controls default is disputed. Arc unread badges, Zap's popularity, new-tab order unconfirmed.
- Brave Containers with extensions and password managers is unverified. Star counts drift daily. All costs are INFERENCE.
- The Anthropic terms point needs a maintainer decision.

## Where to look in the full dossier

`plans/research/long-tail.md` — snapshot tables 13-67; one entry per product 68-128; feature tables 130-249; layout and visual language 251-265; **motion** 267-297; feel 299-313; **architecture** 315-340; **data and storage** 342-363; **agents and safety** 365-415; **build and CI** 417-436; strengths and weaknesses 438-462; **ranked take and avoid** 464-531; open questions 533-550; sources 552-600; **Verification** 602-655.
