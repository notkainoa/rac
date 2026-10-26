# T3 Code: research dossier

Researched 2026-10-25 from a shallow clone of `pingdotgg/t3code` at commit
`1eb4071a497cf1388a41040283a4065245dbe977` (2026-10-25 18:42 UTC), the GitHub API, t3.codes, Electron's docs,
and a read-only listing (names, sizes, modes only; no file opened) of the maintainer's own `~/.t3` folder,
because this research session itself runs inside T3 Code. Paths written `T:<path>:<lines>` are in the clone
(`/tmp/rac-overhaul/src/t3code`); on GitHub the same file is
`https://github.com/pingdotgg/t3code/blob/1eb4071a497cf1388a41040283a4065245dbe977/<path>`. Paths written
`R:<path>` are in the rac worktree. Counts I made myself (with grep, wc, or `gh api`) are marked "(count)".
Tags: **FACT** means a primary source (code, repo docs, GitHub API, a listing I ran). **CLAIM** means T3's own
marketing or self-report, or a third party repeating it. **INFERENCE** means my reasoning.

T3 Code is not a browser. Where this template asks about browser features, I map them to T3's nearest
equivalent and say so.

## In plain English (at most 150 words)

T3 Code is the app the maintainer uses to run many coding agents side by side. It has no AI of its own. It
drives the agent tools you already pay for, such as Claude Code and Codex. A background program, called the
server, runs on your computer. It starts the agents, saves every conversation in one database file, and gives
each task its own copy of the code. The desktop app, a website, and a phone app are only windows onto that
server. So a phone can watch and steer work from anywhere. A built-in browser panel lets agents open, read,
and click web pages. The lesson for rac is the shape: one local service, many thin windows, and one tool list
for people and agents. The warnings: it sends usage data by default, gives agents full access by default, and
one user's database grew to 40 GB.

## Snapshot

| Item | Value |
|---|---|
| What it is | "An agent harness control surface": a GUI that controls the coding agents already installed on a machine (FACT `T:README.md:3`). "A Node WebSocket server wraps provider CLIs and agents ... and serves web, desktop, and mobile clients" (FACT `T:AGENTS.md:3`). Marketing: "The open-source control plane for coding agents" (CLAIM, t3.codes). |
| Engine | No browser engine of its own. Server: Node (`engines` `^22.16 \|\| ^23.11 \|\| >=24.10`; dev and release pin Node 26.12.1) on Effect 4.0.5 (FACT `T:apps/server/package.json`, `T:package.json`, `T:pnpm-workspace.yaml:64`). Desktop: Electron 44.9.3 (FACT `T:apps/desktop/package.json`). The browser panel is an Electron `<webview>`; remote environments use `chrome-headless-shell` 156.0.8078.70, downloaded on first use and checked by SHA-256 (FACT `T:apps/server/src/preview/PreviewBrowser.ts:24-58`). |
| Platforms | macOS (arm64 and x64 DMG), Windows (x64 and arm64 NSIS, winget, scoop), Linux (AppImage, `.deb`, AUR), the hosted web app app.t3.codes, iOS and Android apps, and a `t3` CLI (FACT `T:README.md:1-80`; `T:docs/operations/release.md:33-45`). The CLI archive has no macOS x64 build, because Node single executables segfault there (FACT `T:docs/operations/release.md:45`). |
| License | MIT (FACT `gh api repos/pingdotgg/t3code`, `T:LICENSE`). |
| Repo | github.com/pingdotgg/t3code, created 2026-02-08 (FACT, GitHub API). |
| Stars and activity | 30,044 stars, 8,067 forks. 1,095 open issues, 2,251 open PRs, 7,119 merged PRs (FACT, GitHub API and search, 2026-10-25; a re-check hours later read 30,060, 1,096, 2,252 and 7,126). The 100 commits ending at the pinned commit span 22.6 hours (FACT, commits API). |
| Age | About 8.5 months. First release `v0.0.0-alpha.3` on 2026-03-02. `v0.1.0`, the first "Beta", on 2026-10-15 (FACT, releases API; "Beta is the product label, not a release channel", `T:docs/operations/release.md:7-10`). Its release notes call it "the first stable release of T3 Code Orchestrator V2" (FACT, v0.1.0 release body). |
| Release cadence | 730 releases in 237 days: 619 nightly, 52 preview, and 59 others, which are 58 desktop stable and alpha tags plus 1 `android-beta-93` prerelease (count, releases API). An automatic nightly needs new commits and at least six hours since the last one, so at most 4 a day; the observed rate is about 2.6 a day (619 in 237 days). Manual nightlies skip the gap (FACT `T:docs/operations/release.md:402-418`). Stables: 0.1.0 (10-15), 0.1.1 (10-21), 0.1.2 (10-22). The v0.1.2 `latest-mac.yml` update manifest was fetched 403,277 times in 3 days, and 408,019 times when re-checked later on 2026-10-25 (FACT, asset `download_count`). Every update check fetches it, so this counts checks, not people (INFERENCE). |
| Team | T3 Tools Inc. (FACT, t3.codes footer). Top committers: `juliusmarminge` 3,396, `t3dotgg` (Theo Browne) 888, `maria-rcks` 441, `t3-code[bot]` 121; 473 contributors listed (FACT, contributors API). Of the 100 commits ending at the pinned commit, 73 carry an AI co-author trailer: 72 "Claude Opus 5.5" and 1 "Claude Fable 5.1" (count, commits API at `1eb4071`). "Most T3 Code contributions will come from T3 Code itself, often controlled remotely" (FACT `T:AGENTS.md:41`). "Over 500,000 users" (CLAIM `T:AGENTS.md:9`). |
| Business model | Free, no paid tier; "doesn't resell tokens" (CLAIM, t3.codes). Users bring their own Claude, ChatGPT, Cursor or other subscriptions. The remote tunnel, T3 Connect, is free (CLAIM) and has a default cap of 3 managed tunnels per user, which a per-user row in the relay database can override (FACT `T:infra/relay/src/environments/ManagedTunnelLimits.ts:14,57-63`). Theo: "if the bill gets unacceptable we may have to change course" (CLAIM, [X post](https://x.com/theo/status/2082277789395501263) as quoted by search results). |
| Infrastructure | A Cloudflare Worker relay with Durable Objects and Postgres, Clerk for accounts, Cloudflare tunnels through a pinned `cloudflared`, Vercel for the hosted web app, PostHog via its own `ingest.t3.codes`, Axiom for relay traces, APNs and FCM for phone push, Blacksmith CI runners (FACT `T:infra/relay/package.json`, `T:docs/internals/t3-connect.md`, `T:docs/user/telemetry.md:3-14`, `T:.github/workflows/ci.yml:25`). |

## Features

Status: **shipped** (in stable 0.1.2 or earlier), **beta** (behind Settings → Beta), **planned**. Evidence is
the user docs in `T:docs/user/`, which the repo's own rules keep in step with the product
(`T:AGENTS.md`, "Documentation"), plus the code paths named.

### Tabs, sidebar, spaces (T3: threads, projects, environments)

- shipped: A sidebar of threads, grouped by project. Pin and reorder threads by dragging (FACT `T:docs/user/thread-sidebar.md:46-60`).
- shipped: **Settle** moves finished work out of the active list. Threads settle on their own after 3 days without activity, or when their pull request merges. Drag a Settle button across rows to settle many at once (FACT `T:docs/user/thread-sidebar.md:133-160`).
- shipped: **Snooze** until a time. A snoozed thread wakes early only for an approval, a question, a failure, or a new message (FACT `T:docs/user/thread-sidebar.md:243-251`).
- shipped: Undo for 5 seconds after unpin, settle, snooze, archive or discard; `mod+z` fires the latest Undo, even from the composer (FACT `T:docs/user/thread-sidebar.md:50-56`).
- shipped: Threads without a project, each in its own folder `~/.t3/scratch/<date>-<first words>-<id>` (FACT `T:docs/user/thread-sidebar.md:16-32`).
- shipped: A separate Git worktree per thread, a worktree location setting, and cleanup rules by inactivity or settlement (FACT `T:docs/user/project-settings.md:171-208`).
- shipped: Start a thread in the background (`Cmd+Enter`). Shift-click several models to send one prompt to each, every one in its own thread and worktree (FACT `T:docs/user/thread-sidebar.md:34-44`).
- beta: Fold working threads (FACT `T:docs/user/thread-sidebar.md:119`).
- shipped: Several environments (machines) in one sidebar; a project can exist on several (FACT `T:docs/internals/remote.md:9-18`).

### Navigation and command bar (T3: command palette, keybindings, search)

- shipped: A command palette for threads, projects, themes, appearance and "new thread in...". Its live Git and PR badges load only for rows in view, plus a small margin (FACT `T:docs/internals/performance-regressions.md:104-109`).
- shipped: A keybindings JSON file with `when` conditions, precedence rules and reserved shortcuts (FACT `T:docs/user/keybindings.md:78-180`).
- shipped: Full-text thread search over an SQLite FTS5 table (FACT `T:apps/server/src/persistence/Migrations/069_ThreadMessageSearch.ts:23`).
- shipped: Type `@` to reference another thread, `#` to insert a pull request chip, or drag a thread onto the composer (FACT `T:docs/user/composer.md:259-300`).
- shipped: Prompt links: app.t3.codes links that open as a draft (FACT `T:docs/user/prompt-links.md`).
- shipped: T3 Code can be the macOS default browser. Links from other apps open in the browser panel, or in a new projectless thread with the page ready to ask about (FACT `T:docs/user/default-browser.md:1-17`).

### Split view, peek, small windows (T3: right panel, mini player)

- shipped: A right panel with tabs for Browser, Device, Terminal, Diff, Files, File, Pull request and Pull requests (FACT `T:apps/web/src/rightPanelStore.ts:37-77`).
- shipped: A floating browser "mini player" over the chat, and "Float device over chat" (FACT `T:apps/web/src/components/preview/ThreadPreviewMiniPlayer.tsx`; `T:docs/user/devices.md:20-25`).
- shipped: Picture in picture on the phone for a streamed browser tab (FACT `T:docs/user/remote-access.md:214-216`).
- shipped: Visual replies: an agent's HTML page appears inline in the thread, can go full screen, and zooms (FACT `T:docs/user/html-renders.md:1-9`).

### Import, sync, profiles

- shipped: Cookie import into the browser panel from Chrome, Edge, Brave, Vivaldi, Opera, Arc, Helium, Safari, Firefox and Zen (FACT `T:apps/desktop/src/preview/BrowserImport/Sources.ts:79-180`; `T:docs/user/browser-import.md`). Chromium cookies are decrypted with the browser's Keychain key, PBKDF2 salt `saltysalt`, 1003 iterations, AES-128-CBC (FACT `T:apps/desktop/src/preview/BrowserImport/ChromiumKeys.ts:15-17`; `ChromiumCookies.ts:111`). Safari needs Full Disk Access (FACT `T:docs/user/browser-import.md:9-14`).
- shipped: Browser profiles as separate Electron partitions `persist:t3code-preview-<scope>` (FACT `T:apps/desktop/src/preview/BrowserSession.ts:14`).
- shipped: Several accounts per agent kind ("provider instances") (FACT `T:docs/internals/providers.md:8-10`).
- not built, by design: sync. Every device connects to the same server instead. Saved connections are local to each client (FACT `T:docs/internals/remote.md:11-14`).
- shipped: Server-published themes and defaults (FACT `T:docs/user/appearance.md:58-107`).

### Privacy and blocking

- shipped, **on by default**: product analytics to `ingest.t3.codes`, which archives every event and forwards them to PostHog. Events carry hashed T3 Connect, OpenAI and Claude account ids (FACT `T:docs/user/telemetry.md:3-12`; default `true` at `T:apps/server/src/telemetry/AnalyticsService.ts:70`). The only off switch is the environment variable `T3CODE_TELEMETRY_ENABLED=false`; the settings contract has no telemetry field (FACT `T:docs/user/telemetry.md:16-22`; count over `T:packages/contracts/src/settings.ts`).
- shipped: relay connection traces to Axiom (FACT `T:docs/user/telemetry.md:14`).
- shipped: export traces, metrics and logs to your own OpenTelemetry receiver (FACT `T:docs/user/telemetry.md:24-40`).
- shipped: 17 permission scopes (the `AuthEnvironmentScope` union, including the unexported `review:write`), pairing links, DPoP-bound tokens, and revocation under Settings → Connections (FACT `T:packages/contracts/src/auth.ts:30-66`, count; `T:docs/internals/environment-auth.md`).
- shipped: a background service with no configured host listens on every IPv4 interface and closes connections unless both peer addresses are loopback, private or tailnet IPv4. The doc itself says "It is not a firewall": tunnels arrive over loopback, and a proxy that rewrites the source address looks private (FACT `T:docs/internals/remote.md:57-64`).
- not applicable: no ad or tracker blocking. The browser panel is stock Electron Chromium (INFERENCE from dependencies).

### AI assistant (T3: the chat with each provider)

- shipped: Codex, Claude, Cursor, Grok Build, OpenCode 1.x and 2.x, Antigravity, Pi, Muse, and any agent in the official ACP Registry (FACT `T:README.md:5`; `T:docs/orchestration-v2/orchestrator-mcp-server.md:182-191`).
- shipped: switch provider or model mid-thread. Context moves as a "portable handoff": a budgeted selection of past messages, 16,000 tokens by default (FACT `T:docs/user/portable-handoffs.md:1-27`).
- shipped: fork a thread, merge a fork back, and roll back a turn through checkpoints (FACT `T:docs/internals/overview.md:82-85`).
- shipped: a composer with inline chips for terminal excerpts, review comments, browser annotations, picked page elements, files, pull requests and other threads (FACT `T:docs/user/composer.md:259-300`).
- shipped: queue, steer or restart while the agent works; queued messages on mobile while offline (FACT `T:docs/user/composer.md:52-86,198-222`).
- shipped: usage and subscription-limit tracking (FACT `T:docs/user/usage.md`), `/goal` goals (`composer.md:246`), voice input on iPhone (`composer.md:176`).
- shipped: Claude threads compact themselves 2 minutes before Claude's prompt cache expires (1 hour on subscriptions, 5 minutes on API keys) (FACT `T:apps/server/src/orchestration-v2/IdleCompaction.ts:1-30`).
- shipped: MCP Apps (interactive tool results) in the thread (FACT `T:docs/user/html-renders.md:11-17`).

### Agent (browser, devices, delegation)

- shipped: agents drive the browser panel through 19 `preview_*` tools: status, open, dialog, navigate, resize, set_appearance, snapshot, click, type, hover, select, drag, upload, press, scroll, evaluate, wait_for, recording start and stop (count, `T:apps/server/src/mcp/toolkits/preview/tools.ts`).
- shipped: an on-screen agent cursor; "Take control" and "Release control" between human and agent; element picking and annotations as composer chips (FACT `T:apps/web/src/components/preview/AgentBrowserCursor.tsx:76`; `T:apps/web/src/browser/ServerBrowserSurface.tsx:728`; `T:docs/user/composer.md:261-266`).
- shipped: a browser for remote environments: headless Chrome on the host, streamed to any device (FACT `T:docs/user/remote-access.md:194-220`).
- shipped: a Device panel for the iOS Simulator and Android Emulator, with `device_*` tools and the `agent-device` CLI (FACT `T:docs/user/devices.md:1-60`).
- shipped: delegation. `delegate_task` makes a child thread on any provider; `create_threads` makes 1 to 20 threads; `t3_thread_launch` picks a workspace; wait, read, send, interrupt (FACT `T:docs/orchestration-v2/orchestrator-mcp-server.md:193-449,497-534`).
- shipped: scheduled tasks on an interval, at a fixed time, or on a webhook (FACT `T:docs/user/project-settings.md:63-110`).
- shipped: `request_secret`: the user types a secret into a card; the agent gets a one-use reference, never the value (FACT `T:apps/server/src/secrets/SecretRequests.ts:1-3`).
- shipped: `watch_pull_request` wakes an agent on checks, comments or conflicts (FACT `T:AGENTS.md`, "Pull requests").
- beta: guest links let a teammate follow one thread and propose messages (FACT `T:docs/user/guest-links.md:7-12`).

### Extensibility (CLI, MCP, API, extensions, mods)

- shipped: the `t3` CLI: `serve`, `service install|status|restart|uninstall`, `update`, `connect`, `pair`, `auth`, `thread start|send|show|list`, `project`, `theme`, `doctor`, `trace`, `triage`, `browser setup`, `uninstall` (FACT `T:apps/server/src/cli/`; `T:docs/user/background-service.md:7-17`).
- shipped: an MCP server at `/mcp` for outside agents (Claude Code, Codex, ChatGPT, bots) with OAuth sign-in; read-only by default; sign-ins last 30 days (FACT `T:docs/user/outside-agents.md:1-121`).
- shipped: 84 MCP tools in 11 toolkits: orchestrator 18, thread 17, preview 19, pull requests 7, project 7, device 4, attachment 3, worktree 3, environment 2, preview controls 2, html 2 (count). The design doc still says "eleven orchestration tools" (FACT `T:docs/orchestration-v2/orchestrator-mcp-server.md:195`), while the orchestrator toolkit has 18 (count), so docs lag code.
- shipped: a typed RPC contract with 203 methods, 31 of them streams (count, `T:packages/contracts/src/rpc.ts`).
- shipped: per-repo `t3.json` scripts, such as setup on worktree creation and `runOnSettle` cleanup (FACT `T:t3.json`; `T:docs/user/thread-sidebar.md:146-152`).
- shipped: custom themes, VS Code theme import, and themes generated from two colors (FACT `T:docs/user/appearance.md:50-103`).
- shipped: ACP Registry agents install from settings into a managed, versioned cache with checksums (FACT `T:docs/orchestration-v2/orchestrator-mcp-server.md:117-144`).

### Other

- shipped: terminals (node-pty, libghostty-vt) with saved history (FACT `T:docs/user/terminal.md`).
- shipped: source control for GitHub, GitLab, Bitbucket, Azure DevOps, Forgejo or Gitea, and GitCafe; create, review and merge PRs; review guides; GitHub stacks (FACT `T:docs/user/source-control.md`).
- shipped: SnapShots, a global shortcut that captures another app's window and its text (FACT `T:docs/user/snap-shot.md`).
- shipped: SSH-launched remote servers and WSL backends (FACT `T:docs/internals/remote.md:89-95`).
- shipped: phone push and iOS Live Activities through the relay (FACT `T:infra/relay/src/agentActivity/`).
- shipped: passkeys inside the browser panel (Touch ID and the system passkey sheet), gated by Apple entitlements (FACT `T:docs/operations/release.md:600-612`).
- shipped: a welcome wizard that connects computers, checks agents and imports projects (FACT `T:docs/user/welcome-wizard.md`).

## UI, look, and feel

### Layout

- Three columns. A left sidebar of threads, 16rem (256 px) wide by default and resizable, with a 256 px
  minimum (FACT `T:apps/web/src/components/ui/sidebar.tsx:27-30`). A center thread with the composer docked
  at the bottom. A right panel of tabbed surfaces (browser, device, terminal, diff, files, PRs) plus a terminal
  drawer (FACT `T:apps/web/src/rightPanelStore.ts:37-77`).
- The composer floats on a soft shadow, `0 12px 28px -18px rgb(0 0 0 / 40%)`, that is shared by its context
  strip and banners (FACT `T:apps/web/src/index.css:195`).
- Mobile is a separate React Native app with its own navigation, not a shrunken web page (FACT
  `T:AGENTS.md`, "Multi-surface"; `T:docs/internals/mobile-navigation.md`).

### Visual language and materials

- shadcn-style components on Base UI primitives, styled with Tailwind 4.3.3 (FACT `T:apps/web/package.json`;
  `T:pnpm-workspace.yaml:72`). Components in `components/ui` own their look; call sites pick a `variant` or
  `size` and may not restyle with `className`. A lint rule (`shadcn/no-restyle`) fails violations (FACT
  `T:AGENTS.md`, "Taste"; `T:docs/internals/web-ui.md:3-22`).
- Base radius 0.625rem (10 px) (FACT `T:apps/web/src/index.css:1096`).
- "Glass" surfaces use `backdrop-filter: blur(12px) saturate(1.14)` in light mode and `blur(16px)
  saturate(1.08)` in dark mode, with a solid fallback when blur is unsupported (FACT
  `T:apps/web/src/index.css:117-119,143-148,343-346`).
- Colors are written in OKLCH (FACT `T:apps/web/src/index.css:219,385-398`).
- Icons are Lucide plus `morphicons`, which morph one icon into another, used in 29 components and gated by
  reduced motion (FACT `T:apps/web/src/components/MorphIcon.tsx`; count).
- A custom lint rule bans em dashes in UI copy (`no-em-dash-copy`) and another bans native `title` tooltips
  (FACT `T:oxlint-plugin-t3code/rules/`).

### Typography

- The system font stack, `-apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif` (FACT
  `T:apps/web/src/index.css:169`). Interface size is a setting from 12 to 20 px, default 16 (FACT
  `T:packages/contracts/src/settings.ts:124-130`). Text tokens go down to `--text-5xs` (0.4375rem) (FACT
  `T:apps/web/src/index.css:180-187`).

### Color and themes

- Built-in themes, a theme editor with an on-screen color picker, VS Code theme import, and JSON export
  (FACT `T:docs/user/appearance.md:50-56`).
- A theme can be generated from `appearance`, `canvas` and `accent` hex colors, with optional overrides; the
  app derives the rest (FACT `T:docs/user/appearance.md:84-103`; `culori` in `T:apps/web/package.json`).
- A server can publish themes and push a default to every connected client once (`t3 theme set`) (FACT
  `T:docs/user/appearance.md:58-83`). Android supports Material You (FACT `T:docs/user/appearance.md:16-21`).

### Motion (values from code)

- **Panels do not animate by default.** Sidebar, right panel and terminal drawer open instantly. A "Panel
  animations" slider goes from 0 to 400 ms; the default is 0 (FACT `T:packages/contracts/src/settings.ts:113-122`;
  `T:docs/user/appearance.md:41-46`). Switching threads never replays panel transitions (FACT, same doc).
- The house default is 150 ms `ease-out`: 38 uses of `duration-150` and 38 of `ease-out` in `.tsx` files, then
  200 ms (21), 100 ms (6), 180 ms (4), 220 ms (3) (count over `T:apps/web/src`).
- The one named curve: `--ease-drawer: cubic-bezier(0.32, 0.72, 0, 1)` for surfaces that slide or pop in
  (FACT `T:apps/web/src/index.css:188-192`).
- Composer banners enter in 150 ms `ease-out` (opacity and transform) and leave in 220 ms `ease-in`; the stack
  waits 220 ms before removing a dismissed notice (FACT
  `T:apps/web/src/components/chat/ComposerBannerStack.tsx:10,177-223`).
- Height changes: 200 ms `ease-out` on `height` (FACT `T:apps/web/src/components/AnimatedHeight.tsx:84`).
- Menus, popovers and dialogs: fade from opacity 0 and scale from 98% on enter and exit, through Base UI's
  `data-starting-style` and `data-ending-style` (count over `T:apps/web/src/components/ui/*.tsx`).
- Streaming text: each new paragraph or code block fades in over 600 ms `ease-out` with `@starting-style`, and
  only while the message streams, so opening a finished thread never replays it. Opacity only, one shot, no
  layout change (FACT `T:apps/web/src/index.css:2105-2120`).
- **Stepped loops.** The skeleton breath is an opacity pulse with `steps(4)`. The comment explains: "on a
  120Hz display [this] is the difference between ~14 and ~288 updates" (FACT `T:apps/web/src/index.css:290-308`).
  Status pulses use `steps(6)`, pings `steps(8)` (FACT `T:apps/web/src/index.css:309-335`).
- The "live tool" text shine runs 2.2 s with `steps(30)` (about 14 frames a second), and its play state is a CSS
  variable that defaults to `paused` (FACT `T:apps/web/src/index.css:528-553`). A shared IntersectionObserver sets
  it to `running` only when the element is on screen, the page is visible, and reduced motion is off; it also
  toggles `will-change` (FACT `T:apps/web/src/lib/visibleAnimation.ts:10-62`).
- Browser loading bar: grows from 4% to 90% over 5.3 s on `cubic-bezier(0.1, 0.5, 0.2, 1)`, then finishes in
  150 ms and fades after a 220 ms delay (FACT `T:apps/web/src/index.css:2305-2335`).
- Settings search highlights its target with two 650 ms `ease-in-out` pulses (FACT `T:apps/web/src/index.css:900-912`).
- Slider thumbs scale to 1.08 on hover over 120 ms (FACT `T:apps/web/src/index.css:990-1010`).
- The agent cursor moves with a 150 ms `ease-out` transition on opacity and transform. Its opacity is 1 while
  acting, 0.35 when idle, and 0.18 while a human controls the tab (FACT
  `T:apps/web/src/components/preview/AgentBrowserCursor.tsx:76`; `agentBrowserCursorLogic.ts:3-6`).
- Mobile thread swipe actions use a spring with stiffness 330, damping 26, mass 0.7 and overshoot clamping
  (FACT `T:apps/mobile/src/features/home/thread-swipe-actions.tsx:54-59`). Looping mobile animations must use
  React Native's native-driver `Animated`, not Reanimated's `withRepeat`, which froze the UI (FACT
  `T:docs/internals/performance-regressions.md:130-141`).
- Rule: "No continuously repainting animations; they peg the GPU on high-refresh displays" (FACT `T:AGENTS.md:197`).

### Signature interactions that feel great

- Settle by dragging across many rows, then Undo for 5 seconds or `Cmd+Z` (FACT, see Features).
- Composer chips behave like characters: type around them, cut and paste them, and they survive copy into
  another draft (FACT `T:docs/user/composer.md:259-300`).
- Shift-click several models to race one prompt across providers, each in its own worktree (FACT
  `T:docs/user/thread-sidebar.md:40-44`).
- Tool calls collapse into one plain summary, "Ran 2 commands and sent messages to 3 threads", that expands
  (FACT `T:docs/user/activity-log.md:3-14`). This matches the quiet rows the maintainer chose for rac's agent.
- A visible agent cursor plus an explicit Take control / Release control handoff (FACT, see Agent).
- Any link from any app can land in front of an agent, because T3 Code can be the default browser (FACT
  `T:docs/user/default-browser.md`).

### Things that feel bad

- Scale and churn. "We are very very early in this project. Expect bugs" (FACT `T:README.md:89`). 88 doc pages (39 for users, 30 internal, 9 operations, 9 orchestration design)
  in the repo. Settings live at the client, environment, project and "All environments" levels (FACT
  `T:docs/internals/overview.md:44-51`). INFERENCE: a newcomer faces many concepts (environment, project,
  thread, run, settle, snooze, provider instance, runtime mode, interaction mode) before the first prompt.
- Resource bugs open on 2026-10-25: 13 hidden browser tabs kept alive, unthrottled, about 2.7 GB until restart
  (FACT issue #15579); a nightly at about 11.5 GB of memory (#18485); about 467 MB of RAM across Electron
  processes at rest (#16997); opening a long thread blocks the database writer for 7 to 10 s (#21840); 12,284
  hidden checkpoint refs in one repo slow every `git fetch` (#24083).
- No panel motion by default. INFERENCE: this suits power users. It would read as abrupt in an Arc-like
  browser whose personality depends on motion.

## Architecture

### Process model

```text
 desktop (Electron main)  ── spawns ──▶  server (Node, Effect)  ── spawns ──▶ provider CLIs / SDKs
   │  renderer = web UI from t3code://      │  SQLite statev2.sqlite             (codex app-server, claude SDK,
   │  <webview> browser tabs                │  HTTP + WebSocket on :3773          cursor SDK, opencode, ACP, pi)
   │  CDP debugger ── fd 6/7 ─────────────▶ │  /mcp, /api, /oauth                ── spawns ──▶ helpers
   ▼                                        ▼                                     (expo-device-hub, headless
 web / mobile clients ── WebSocket RPC ───▶ same server (LAN, Tailscale, SSH, T3 Connect tunnel)   chrome, cloudflared)
```

- **One server per environment.** It is `t3 serve` from the CLI, a launchd or systemd service, or a child of
  the desktop app (FACT `T:docs/internals/overview.md:3-6`; `T:docs/user/background-service.md`). Default port
  3773 (FACT `T:apps/server/src/config.ts:17`).
- **The desktop app spawns the server as a child process**, using the Electron binary itself as Node
  (`ELECTRON_RUN_AS_NODE=1`). It passes a bootstrap JSON, including a one-time token and secret, on file
  descriptor 3, never on the command line. Descriptors 4 and 5 carry telemetry, 6 and 7 carry the browser's
  CDP traffic (FACT `T:apps/desktop/src/backend/DesktopBackendConfiguration.ts:498-541`;
  `T:apps/desktop/src/backend/DesktopBackendManager.ts:392-433`).
- The desktop server listens on `127.0.0.1` unless the user turns on Network access, which switches it to
  `0.0.0.0` and restarts the app (FACT `T:apps/desktop/src/backend/DesktopServerExposure.ts:32-33`;
  `T:docs/user/remote-access.md:35-42`).
- **The desktop renderer is a client like any other.** It loads the bundled web UI from a `t3code://` scheme on
  disk, not from the server, so the desktop can run with no local server and only remote ones (FACT
  `T:docs/internals/remote.md:103-113`; `T:apps/desktop/src/electron/ElectronProtocol.ts:16`).
- Native modules never load in the Electron main process on the startup path. Accessibility capture runs in
  forked children; new native capability goes in a child with a deadline, so a crash there must not take the
  app down. One exception: `ffi-rs` loads lazily in main for a few Win32 calls (FACT `T:docs/internals/overview.md:119-124`). A Rust
  `resource-monitor` and a small C `libsecret` helper are separate executables (FACT `T:native/`).
- The relay Worker is not in the data path. After bootstrap, clients talk to the environment's own tunnel
  hostname; the relay only forwards webhooks (FACT `T:docs/internals/t3-connect.md:1-12`). INFERENCE: the
  Cloudflare tunnel itself is in the data path, and T3's docs do not say whether traffic is encrypted end to
  end past Cloudflare's edge. I did not check.

### How clients connect

- **Effect RPC over WebSocket, JSON-encoded** (FACT `T:apps/server/src/ws.ts:3308,3344`). 203 methods, 31 of
  them streams, all typed in `packages/contracts` (count, `T:packages/contracts/src/rpc.ts`).
- Auth happens at the WebSocket upgrade: a browser cookie, a bearer token, or a short-lived ticket bound to a
  DPoP key. Every RPC also declares a required scope, which middleware checks before the handler runs (FACT
  `T:docs/internals/environment-auth.md:73-87`; `T:apps/server/src/ws.ts:3313`).
- Subscriptions send "snapshot at sequence N, then committed events after N", so reconnects resume from a
  cursor (FACT `T:docs/orchestration-v2/core-graph-and-data-model.md:31-38`). Snapshots stop at about 1 MiB or
  10 user turns; resume replays at most 128 events or 1 MiB before falling back to a snapshot (FACT
  `T:docs/internals/performance-regressions.md:15-32`).
- Live command output never enters the event stream. A separate output hub keeps one bounded tail per command
  and streams it only to an expanded command row (FACT `T:docs/internals/performance-regressions.md:42-48`).
- One shared connection owner per environment in `packages/client-runtime`, with jittered exponential retry
  capped at 5 minutes (FACT `T:docs/internals/connection-runtime.md:3-26`).
- Clients and servers upgrade on their own schedules. Features are negotiated through capabilities the
  environment advertises, never through a client's version (FACT `T:docs/internals/overview.md:21-38`;
  `T:docs/internals/remote.md:97-101`).

### Orchestration and the event model

- **Event-sourced, with commands, projections and an outbox.** "Clients send typed WebSocket requests. The
  server turns them into commands. The orchestrator ... serializes commands and decides events without doing
  any I/O. The event sink commits those events, the projections the UI reads, the command receipt, and outbox
  effects in one transaction. The effect worker then runs the effects ... and feeds results back as commands"
  (FACT `T:AGENTS.md:168-171`; `T:docs/internals/overview.md:53-71`).
- A command acknowledgement means "intent committed", not "work done" (FACT `T:docs/internals/overview.md:63-67`).
  Duplicate command ids return the stored receipt without re-running side effects (FACT
  `T:docs/orchestration-v2/README.md:108`).
- The V2 contract has 45 event types (`OrchestrationV2DomainEvent`, lines 1686-1829) and 60 client command types
  (`OrchestrationV2Command`, lines 2721-3184), plus 8 internal server commands (lines 3188-3280), so 68 command
  types in all (count, `T:packages/contracts/src/orchestrationV2.ts`).
- The data model is a graph: `AppThread` → `Run` (one counted user turn) → `RunAttempt` → a tree of
  `ExecutionNode`s (tools, approvals, subagents), with provider-native threads and sessions as references, and
  `ContextTransfer` records for forks, provider switches, merge-back and subagents (FACT
  `T:docs/orchestration-v2/core-graph-and-data-model.md:5-27,40-137`). "App ids are primary. Provider ids are
  refs" (FACT `T:docs/orchestration-v2/README.md:33`).
- Turn diffs come from **checkpoints**, hidden Git refs under `refs/t3/` that never touch the user's branch
  (FACT `T:apps/server/src/checkpointing/Utils.ts:4`; `T:docs/internals/overview.md:82-85`).
- Restart recovery continues interrupted runs, with a cap of 3 consecutive continuations so a crashing turn
  cannot loop (FACT `T:docs/internals/server-updates.md:66-98`).
- Core files are large: `Orchestrator.ts` 12,687 lines, `ProjectionStore.ts` 7,692, `ClaudeAdapterV2.ts`
  10,643, `CodexAdapterV2.ts` 7,514 (count).

### Providers and how sessions are supervised

- Each provider has an adapter that turns its native protocol into orchestration events: Codex through its
  `app-server` JSON-RPC (`packages/effect-codex-app-server`), Claude through `@anthropic-ai/claude-agent-sdk`,
  Cursor through `@cursor/sdk`, OpenCode through its SDK and server, Grok and registry agents through ACP
  (`packages/effect-acp`), Pi through its RPC mode (FACT `T:apps/server/package.json`;
  `T:apps/server/src/orchestration-v2/Adapters/`; `T:docs/internals/providers.md:12-37`).
- Behavior is driven by capability flags per adapter (sessions, threads, turns, streaming, tools, approvals,
  planning, subagents, context, checkpointing, identity), not provider-name checks (FACT
  `T:docs/orchestration-v2/provider-capability-system.md:1-22`). Missing features degrade by policy: no native
  steering becomes interrupt-and-restart; no native fork becomes portable context (FACT
  `T:docs/orchestration-v2/orchestrator-mcp-server.md:139-144`).
- **Sessions stay alive between turns.** A provider session closes after 30 idle minutes, or 4 hours when
  pinned (FACT `T:apps/server/src/orchestration-v2/ProviderSessionManager.ts:56-57`). INFERENCE: this is why
  follow-ups are fast, the opposite of rac's one-run-one-process rule (`R:docs/internals/ai.md:241-250,707-716`).
- The desktop's server child inherits the app's own environment (`extendEnv: true`) (FACT
  `T:apps/desktop/src/backend/DesktopBackendConfiguration.ts:536`). From the login shell (`-ilc`) it copies only
  an allowlist of 22 names: `PATH`, `SSH_AUTH_SOCK`, locale, Homebrew, XDG, Wayland/X11, certificate variables,
  `T3CODE_TELEMETRY_ENABLED` and `__MISE_DIFF` (FACT `T:apps/desktop/src/shell/DesktopShellEnvironment.ts:76-99,307-318`).
  So it is not the full login-shell environment; for an app opened from the Dock or Finder, an API key
  exported in `~/.zshrc` is not copied in (INFERENCE from the allowlist). Agents
  inherit the server's environment (INFERENCE, not traced through every adapter). A `t3 serve` started from a
  terminal inherits that terminal's full environment (INFERENCE). Either way, nothing like rac's empty-environment
  launch exists.
- Setup is never a side effect of a health check: probes avoid starting sessions that could run hooks or open
  a login browser (FACT `T:docs/internals/providers.md:52-58`).
- Provider updates run only through the installer that owns the binary (Homebrew, npm, native) (FACT
  `T:docs/internals/providers.md:81-102`).

### The built-in browser panel

- **Desktop:** each tab is an Electron `<webview>` in a `persist:t3code-preview-<scope>` partition. Every
  attach is checked and hardened (`sandbox: true`, no Node) in `will-attach-webview` (FACT
  `T:apps/desktop/src/window/DesktopWindow.ts:392,498-516`). Electron's own docs say "We currently recommend to
  not use the `webview` tag" (FACT, [Electron docs](https://www.electronjs.org/docs/latest/api/webview-tag)).
- The desktop attaches Chromium's debugger to the tab and relays CDP over descriptors 6 and 7 to the server.
  There a secret loopback WebSocket lets Playwright (`playwright-core` 1.60.0) connect as if to a browser. The
  relay answers some browser-level CDP methods itself and shares one debugger per tab (FACT
  `T:apps/desktop/src/preview/CdpRelay.ts:1-80`; `T:apps/server/src/preview/DesktopBrowserChannel.ts:1-2`).
- **Remote environments:** the server runs `chrome-headless-shell` 156.0.8078.70, pinned by size and SHA-256
  per platform, and never older than a version with a fixed certificate blocklist (FACT
  `T:apps/server/src/preview/PreviewBrowser.ts:24-58`). Frames stream as JPEG through `Page.startScreencast`
  over `/api/preview-stream` at quality 70 and 1280 px wide by default, with acks for flow control and an 8 MiB
  socket buffer cap (FACT `T:apps/server/src/preview/ServerBrowserStream.ts:28-33`;
  `T:apps/server/src/preview/ServerBrowser.ts:2260-2282`).
- **Page representation:** Playwright's `ariaSnapshot({ mode: "ai", boxes: true })`, with refs the agent passes
  back as `aria-ref=<ref>`. Refs die on navigation, a new snapshot, or a control handoff. Text caps near 20 KB
  (FACT `T:apps/server/src/preview/ServerBrowserPage.ts:544-575`; `T:apps/server/src/mcp/toolkits/preview/tools.ts:140`).
  Password fields and `-webkit-text-security` fields are masked, including copies of their value elsewhere in
  the tree (FACT `T:apps/server/src/preview/ServerBrowserPage.ts:212-224,357-377`).
- **Control:** one owner at a time. Taking control bumps an epoch and drains running work first; an agent
  action on a tab it does not control fails with "Browser control changed. Refresh the snapshot" (FACT
  `T:apps/server/src/preview/SessionControl.ts:1-80`). "Act only on your tab, or an unclaimed tab with no human
  in control" (FACT `T:apps/server/src/mcp/toolkits/preview/tools.ts:61`).
- A broker routes each tool call to a connected browser host (a desktop, or the server's own headless
  browser), preferring the focused one (FACT `T:apps/server/src/mcp/PreviewAutomationBroker.ts:60-120`).

### UI technology, languages, code layout and size

- Web: React 19.3 with the React Compiler enforced (no manual `useMemo`; a test compiles every file),
  TanStack Router, zustand and `@effect/atom-react`, Tiptap for the composer, `@legendapp/list` for long lists,
  `@pierre/diffs` for diffs (FACT `T:apps/web/package.json`; `T:docs/internals/web-ui.md:57-76`).
- Desktop: Electron 44.9.3, electron-builder 26.16.1, electron-updater 6.8.9; 16 IPC method groups (FACT
  `T:apps/desktop/package.json`; `T:apps/desktop/src/ipc/methods/`, count).
- Mobile: Expo 58, React Native 0.88, Reanimated 4.7.1 (FACT `T:apps/mobile/package.json:88,127,135`).
- Relay: Cloudflare Workers, Durable Objects, Postgres through Drizzle, deployed with Alchemy (FACT
  `T:infra/relay/package.json`).
- Tooling: Vite+ (`vp`), pnpm 12.14, a Rust TypeScript checker (`@tsc-rs/typescript` 0.8.0), oxlint with 23
  custom rules, knip for unused code (FACT `T:package.json`; `T:pnpm-workspace.yaml:74-77`;
  `T:oxlint-plugin-t3code/rules/`, count). 32 patched npm dependencies (count, `T:patches/`).
- Agents read vendored references (`.repos/effect-smol`, `.repos/alchemy-effect`) instead of guessing library
  APIs (FACT `T:AGENTS.md`, "Where code lives").
- Size: about 1.49 million lines of TypeScript (excluding `.repos`). `apps/server` 460,833 lines in 1,219 files;
  `apps/web` 331,568; `apps/mobile` 174,276; `packages/client-runtime` 81,899; `apps/desktop` 66,682;
  `infra/relay` 27,372 (count).

## Data and storage

### Where things live

- **T3 home** is `~/.t3` (override with `T3CODE_HOME`); runtime state is in `~/.t3/userdata`. Dev servers use a
  `dev` subfolder or the worktree's own gitignored `.t3` (FACT `T:apps/server/src/os-jank.ts:126`;
  `T:apps/server/src/config.ts:123-157`; `T:AGENTS.md`, "Dev servers").
- Worktrees: `~/.t3/worktrees/<project>/<name>`. This research session runs in
  `/Users/knewton/.t3/worktrees/rac/t3-bb0e4397` (FACT, config and working directory). Scratch threads:
  `~/.t3/scratch`. CLI runtimes: `~/.t3/runtime/versions/<version>`; launcher at `~/.t3/bin/t3` (FACT
  `T:docs/operations/release.md:39-44`; listing).
- Files under `userdata` (FACT `T:apps/server/src/config.ts:129-157`, and the maintainer's listing):
  `statev2.sqlite` (plus `-wal`, `-shm`), the legacy `state.sqlite`, `settings.json`, `keybindings.json`,
  `client-settings.json`, `desktop-settings.json`, `connection-catalog.json`, `model-manifest.json`,
  `environment-id`, `anonymous-id`, `server-runtime.json`, usage caches (`usage-scan-cache-v*.json`,
  `usage-model-rates.json` 2.2 MB), and folders `attachments/`, `browser-artifacts/`, `logs/`
  (`server.trace.ndjson`, `provider/events.log`, `terminals/`), `themes/`, `secrets/`.

### The database

- One SQLite file per environment, opened in WAL mode with `synchronous = NORMAL`, `checkpoint_fullfsync = ON`
  (macOS drive caches), `journal_size_limit` 32 MiB (the size the WAL is truncated back to after a checkpoint, not a
  hard cap), a 5 s busy timeout (the CLI and server write from separate
  processes), foreign keys on, incremental auto-vacuum for new files, and separate reader and checkpoint
  worker threads so fsyncs do not stall the event loop (FACT `T:apps/server/src/persistence/Sqlite.ts:12-61`).
- 69 numbered migrations (001 to 069) (count, `T:apps/server/src/persistence/Migrations/`). The core event
  table is `orchestration_v2_events(sequence INTEGER PRIMARY KEY AUTOINCREMENT, event_id, command_id,
  thread_id, run_id, node_id, provider, raw_event_id, event_type, occurred_at, payload_json)`, with six
  explicit indexes plus the `UNIQUE` index on `event_id`; next to it sit `orchestration_v2_command_receipts`, an effect outbox, about 18
  `orchestration_v2_projection_*` tables (threads, runs, run attempts, nodes, messages, turn items, provider
  sessions, provider threads, provider turns, checkpoints, context transfers and more), an FTS5 message search
  table, auth sessions and pairing links, scheduled tasks and webhook tables, and PR review tables (FACT
  `T:apps/server/src/persistence/Migrations/055_OrchestrationV2.ts:15-140`; table list by count).
- Raw provider frames are not durable app state. They go to rotating diagnostic logs, with a 64 KiB budget per
  payload (FACT `T:docs/orchestration-v2/README.md:56`; `T:docs/internals/providers.md:146-155`).
- **Growth is the open wound.** On the maintainer's Mac, `statev2.sqlite` was 2.68 GB plus a 30.7 MB WAL after
  14 days of use (2026-10-11 to 2026-10-25), and 2.93 GB (2,934,718,464 bytes) when re-listed at 13:05 PDT the
  same day (FACT, `ls -la ~/.t3/userdata`). User reports: 17 GiB with 2.55 M event rows; over two days,
  `node.updated` streaming updates were 1.21 M rows (1.94 GB), mostly from OpenCode threads (#21154, closed); 40.4 GB across 16,900 threads,
  where deleting threads freed nothing and an offline VACUUM took the server down for 27 minutes (#21371,
  closed); 327 GB written to disk in 21 hours (#19105, closed). The fix that deletes thread events older than
  24 hours, shrinking one database from 12.47 GB to 4.45 GB, is still an open PR (FACT #22630, open on
  2026-10-25). INFERENCE: storing every streamed update as a permanent event was the mistake; projections
  already held the current state.
- Server updates snapshot the database (main file, WAL and shared memory) before running migrations in a
  trial process, then commit or roll back (FACT `T:docs/internals/server-updates.md:16-50`). Copying a large
  database made updates slow on filesystems without reflink (FACT, issue #21715 title).

### Encryption and keys

- **The server's secret store is plain files**, one `<name>.bin` per secret in `userdata/secrets/`, a folder
  set to mode 0700. It does not use the macOS Keychain (FACT `T:apps/server/src/auth/ServerSecretStore.ts:160-171`).
  On the maintainer's Mac it held 371 files at research time: 291 DPoP replay markers, 64 cloud nonce and jti
  markers, and signing keys (`server-signing-key`, `mcp-oauth-signing-key`, `asset-access-signing-key`), plus
  one provider auth file. A re-listing at 13:06 PDT showed 329 files (251 DPoP markers), every file mode 0600
  (FACT, listing of names and modes only). Each file is written raw and set to 0600; nothing is encrypted
  (FACT `T:apps/server/src/auth/ServerSecretStore.ts:175-206`). Replay markers are pruned after one day (FACT
  `T:apps/server/src/auth/replayMarkers.ts:1-30`).
- **Agent secret requests.** The agent calls `request_secret`; the user types the value into a card. The value
  is stored as JSON `{projectId, value, savedAt}` under an HMAC-derived name, and the agent receives only a
  reference `secret-ref:<32 hex>`. A reference works once, within one project, for 24 hours. A consuming tool
  moves the value into its target so it never reaches transcripts, projections, clients or model context. A
  `file` request instead writes a 0600 file the agent's own shell can read (FACT
  `T:apps/server/src/secrets/SecretRequests.ts:1-3,30-35,187-284`).
- The desktop app encrypts saved connection credentials with Electron `safeStorage`, which is Keychain-backed
  on macOS (FACT `T:apps/desktop/src/electron/ElectronSafeStorage.ts`; `T:apps/desktop/src/app/DesktopConnectionCatalogStore.ts`).
- Provider logins stay with each provider's own CLI (`claude auth login`, `codex login`) (FACT `T:README.md:9-17`).
- Observed: `~/.t3/userdata/clerk-tokens.json` is mode 0666, writable by every local user (FACT, listing). I did
  not find its writer in the repo; INFERENCE: the `@clerk/electron` package writes it.

### Sync and server components

- No sync. Phones, browsers and other desktops connect to the same environment and read its state live (FACT
  `T:docs/internals/remote.md:1-7`).
- **T3 Connect** (optional, needs a Clerk account): the relay manages links between accounts and environments,
  allocates a Cloudflare tunnel per environment, and asks the environment to mint a one-time bootstrap
  credential bound to the client's DPoP key. The relay never sees the session token (FACT
  `T:docs/internals/t3-connect.md:36-57`). A five-minute maintenance job can reclaim tunnels that Cloudflare reports down for at least
  five minutes, but its mode defaults to `off`, and I could not see whether production turns it on (FACT
  `T:docs/internals/t3-connect.md:93-104`). Webhooks can optionally be held up to 24 hours (1 MiB each) while an
  environment is offline (FACT `T:docs/internals/t3-connect.md:14-31`).
- The hosted web app at app.t3.codes keeps its connection list in the browser and connects straight to each
  environment; pairing secrets travel in the URL fragment so the hosted origin never sees them (FACT
  `T:docs/internals/remote.md:69-80`).

### What leaves the machine

- By default: product analytics to `ingest.t3.codes` (archived, forwarded to PostHog) with provider, model,
  reasoning effort, permission mode, turn result, duration, release channel and token totals, keyed by hashed
  account and install ids (FACT `T:docs/user/telemetry.md:3-12`; `T:docs/internals/product-analytics.md:8-34,92-100`).
  Prompts, responses, file contents and conversation ids are excluded (CLAIM `T:docs/user/telemetry.md:11-12`).
- By default: relay connection traces to Axiom (FACT `T:docs/user/telemetry.md:14`).
- With T3 Connect linked: thread titles, project titles and model names (cut to 120 characters) and a status
  (40 characters) go through the relay to Apple and Google push services for notifications and Live
  Activities (FACT `T:infra/relay/src/agentActivity/agentActivityPayloads.ts:41-70`).
- Always: whatever the agents themselves send to their providers.

## Agents and AI

- **Where the agent runs.** As a provider subprocess on the environment's machine, in the project folder, a
  worktree, or a scratch folder, with the server's inherited environment plus about 22 variables from the
  login shell (FACT for the desktop path, Architecture above).
- **Page representation.** For the browser: an accessibility snapshot in Playwright's `ai` mode with element
  boxes and `aria-ref` refs, capped near 20 KB of text, an optional screenshot, password values masked (FACT,
  Architecture above). The snapshot tool tells the model not to use it unasked: "Never use it unasked to
  verify your own edit, or to repeat a snapshot from an earlier turn" (FACT `T:apps/server/src/mcp/toolkits/preview/tools.ts:140`).
- **Tools.** 84 MCP tools (count). Every tool carries MCP annotations: `Readonly`, `Destructive`, `Idempotent`,
  `OpenWorld`. Browser actions are `OpenWorld` and `Destructive`; reads are `Readonly` and `Idempotent` (FACT
  `T:apps/server/src/mcp/toolkits/preview/tools.ts:49-57`). Tool access is declared in one module, and a tool
  that does not declare who may call it does not compile (FACT `T:docs/internals/environment-auth.md:59-61`;
  `T:apps/server/src/mcp/McpToolAccess.ts:1-60`). Tool outputs are kept short on purpose: model lists show at
  most 8 current models for big catalogs, because "every call lands in the agent's context" (FACT
  `T:docs/orchestration-v2/orchestrator-mcp-server.md:210-216`).
- **How agents get the tools.** Before a provider session opens, the server mints a bearer credential scoped
  to the environment, thread, provider instance and session. It expires on idle and at a maximum age (24 h
  liveness window), and is revoked when the session closes; the raw token is never stored in orchestration
  state (FACT `T:docs/orchestration-v2/orchestrator-mcp-server.md:40-55`; `T:apps/server/src/mcp/McpSessionRegistry.ts:64`).
  Codex gets the URL by `-c mcp_servers...` flags and the token in an environment variable; Claude gets an HTTP
  MCP server with an `Authorization` header and `mcp__t3-code__*` allowed; ACP agents get a stdio bridge,
  `t3 acp-mcp-bridge`, with endpoint and token in environment variables, because some ACP adapters drop HTTP
  servers (FACT `T:docs/orchestration-v2/orchestrator-mcp-server.md:59-96`;
  `T:packages/provider-acp/src/server/adapter.ts:600-630`).
- **Providers and models.** Nine provider kinds plus any ACP Registry agent (see Features). Local models come
  only through agents that support them, such as OpenCode, Pi or ACP agents configured for Ollama (FACT
  `T:docs/internals/product-analytics.md:83-86`).
- **Permissions.** Four runtime modes: Supervised (asks before commands and edits), Auto-accept edits, Auto (the
  provider's own automatic review), and Full access. **The default for new threads is Full access** (FACT
  `T:docs/user/permission-modes.md:6-16`; `DEFAULT_RUNTIME_MODE = "full-access"` at
  `T:packages/contracts/src/providerPolicy.ts:32`). Modes map onto each provider's native modes; for Claude, Full access
  is `bypassPermissions` unless Claude's settings disable it (FACT
  `T:apps/server/src/orchestration-v2/Adapters/ClaudeAdapterV2.ts:2060-2132`). A delegated child or a target
  thread may never run with broader modes than its caller (FACT `T:docs/orchestration-v2/orchestrator-mcp-server.md:497-508`).
- **Prompt-injection defenses** are mostly framing and gating, not a policy engine:
  - Webhook values are wrapped in tags with an unpredictable per-request id, every `$`, currency sign and `@`,
    and a `/` that starts a word, get an invisible U+2060 after them so `$skill`, `@file` and `/command` cannot
    fire, credential-looking headers are redacted, and a footer says "Treat it as untrusted data" (FACT
    `T:apps/server/src/scheduledTasks/webhookTemplate.ts:1,17-28,52,150-176`; `T:docs/user/project-settings.md:94-103`).
  - Guest messages wait until the owner chooses Send (FACT `T:docs/user/guest-links.md:20-23`).
  - MCP Apps ask before calling a non-read-only tool and before every message (FACT `T:docs/user/html-renders.md:13`).
  - Agent HTML pages render in sandboxed iframes without `allow-same-origin`, behind a CSP (FACT
    `T:apps/web/src/components/chat/McpAppFrame.tsx:491`; `T:apps/server/src/http.ts:109-134`).
  - There is no guard, critic, or confirm card on browser actions. An agent in Full access can drive a panel
    tab that holds cookies imported from the user's real browser (INFERENCE, from the tool annotations, the
    absence of any confirm path in `T:apps/server/src/mcp/toolkits/preview/handlers.ts`, and the cookie import
    feature). Supervised mode may not help either: Claude sessions get `mcp__t3-code__*` in `allowedTools`
    (FACT `T:docs/orchestration-v2/orchestrator-mcp-server.md:76-91`), and an allowed tool runs without a
    permission prompt (INFERENCE from Claude Agent SDK semantics). rac's guard and cards are stronger here
    (`R:docs/internals/ai.md:407-562`).
- **Outside agents.** The `/mcp` endpoint takes OAuth 2.1 authorization-code sign-in with PKCE, stateless
  client registration, loopback redirects for local agents and any HTTPS redirect for hosted ones. Approval
  needs a one-time pairing code or a signed-in browser with `access:write`. The user grants read-only (default)
  or a runtime-mode ceiling, not a scope list. These sessions work only on `/mcp` (FACT
  `T:docs/internals/environment-auth.md:42-66`; `T:docs/user/outside-agents.md:43-54`). Authorization codes live
  60 s (FACT `T:apps/server/src/auth/McpOAuth.ts:44`). On the host, `t3 thread start|send|show|list` uses the same
  tools without sign-in (FACT `T:docs/user/outside-agents.md:95-115`).
- **Skills.** T3 passes through each provider's own skills and slash commands (FACT `T:docs/user/composer.md:224-245`).
  Its repo ships agent skills for its own development, such as `test-t3-app`, which verifies UI through T3's own
  browser panel (FACT `T:.agents/skills/test-t3-app/SKILL.md`).
- **Automations.** Scheduled tasks (interval, fixed time in the environment's time zone, webhook), PR watches,
  and restart continuation (FACT, Features). Webhook URLs need T3 Connect to be public (FACT
  `T:docs/user/project-settings.md:79-86`).

## Build, release, and engineering

- **Build.** `vp` (Vite+) over pnpm workspaces. One CI job builds the platform-independent JavaScript (server
  bundle, web client, Electron main) once; six platform jobs only package it (FACT
  `T:docs/operations/release.md:27-36`). The CLI ships as a Node single executable per platform with
  `SHA256SUMS`; the npm package `t3` is only a launcher that downloads that archive (FACT
  `T:docs/operations/release.md:38-48`).
- **No engine build.** Electron arrives prebuilt. Headless Chrome is downloaded at first use from Chrome for
  Testing and checked by size and SHA-256 (FACT `T:apps/server/src/preview/PreviewBrowser.ts:24-58`).
- **CI.** `ci.yml` detects affected jobs, then runs lint (format, knip, generated GraphQL checks, a ban on
  committed PR screenshots), build and typecheck, unit tests, web browser tests in Playwright Chromium, server
  tests in 8 shards, Rust tests, and mobile static analysis; Windows tests run separately. Runners are
  Blacksmith 2 to 8 vCPU machines (FACT `T:.github/workflows/ci.yml:23-551`; `windows-tests.yml`). Bots label PR
  size and enforce a contributor "vouch" list (FACT `T:.github/workflows/pr-size.yml`, `pr-vouch.yml`). AI review
  runs through CodeRabbit and Macroscope with house rules (FACT `T:.coderabbit.config.ts`; `T:.macroscope/check-run-agents/`).
- **Signing.** macOS: Developer ID plus notarization with an App Store Connect API key, and a provisioning
  profile for Associated Domains. Passkey entitlements are added only when the profile grants them, "because
  macOS will not launch an app that claims more than its profile allows". The system passkey sheet for any site
  needs `com.apple.developer.web-browser.public-key-credential`, a managed capability requested through Apple's
  "macOS Browsers Passkeys" form (FACT `T:docs/operations/release.md:557-612`). Windows: Azure Trusted Signing
  through `jsign` on Linux (FACT `T:docs/operations/release.md:615-640`).
- **Signed PR previews that keep signing secrets away from PR code.** Labeling a PR `preview:mac` builds only
  the JS bundle from the PR with no secrets; a second workflow on `main` checks the label, the commit, and the
  author against a vouch list, validates the bundle's ZIP entries, and packages and signs it with `main`'s
  packaging code (FACT `T:docs/operations/release.md:60-87`). The PR's JavaScript still ships inside the signed
  app, so each signed preview is a per-commit maintainer decision, as the doc says (FACT, same lines).
- **Update mechanism.** Desktop: electron-updater reading GitHub Releases (`latest*.yml`, `nightly*.yml`,
  blockmaps for delta downloads). Background checks, no automatic download; a rocket button downloads on one
  click and installs on the next (FACT `T:docs/operations/release.md:454-473`). Servers: a stable launcher owns
  the service, snapshots the database, boots the new version as a trial that must reach a "prepared" gate, then
  commits or rolls back (FACT `T:docs/internals/server-updates.md:1-50`). Clients can update a remote server to
  their own exact version; the release workflow publishes archives before the npm launcher and the web app so
  that never points at a missing version (FACT `T:docs/operations/release.md:420-452`).
- **Release cadence and channels.** Nightly at most every 6 hours when `main` changed. A stable release builds
  the commit of the latest nightly, not `main` HEAD: "Nightly is the release candidate: verify the nightly,
  then promote it." A `preview` channel can build any branch through the full sign, notarize and smoke flow,
  but carries no update feed, so nobody is offered it (FACT `T:docs/operations/release.md:14-27,401-418`).
- **Tests.** 1,556 test files, 59 browser test files (54 `.browser.test.tsx`, 5 `.browser.test.ts`), 23
  integration tests (count). Provider behavior is tested
  against recorded real transcripts ("replay fixtures"); only the provider process is replaced, never the
  orchestrator, adapter, normalizer or projections (FACT `T:docs/orchestration-v2/testing-strategy.md:1-50`;
  recorder scripts in `T:apps/server/package.json`). Lint bans sleeps, timeouts, wall-clock deltas, polling
  loops and reasonless skips in tests (FACT `T:AGENTS.md:109-119`). A focused perf suite pins payload budgets
  (`vp run test:perf:v2-wire`), and a transfer-budget test caps bytes for a 900-row turn (FACT
  `T:docs/internals/performance-regressions.md:1-68`). `vp run check:changed` runs CI's fast checks for changed
  files only (FACT `T:AGENTS.md`, "Verifying").
- **How they track upstream.** No engine fork to sync. Their moving targets are the provider CLIs: a model
  manifest, capability probes, owner-aware provider updates, pinned `cloudflared` and Chrome versions, and
  vendored library sources synced with `vpr sync:repos` (FACT `T:docs/internals/providers.md:81-102`;
  `T:docs/internals/t3-connect.md:134-157`; `T:AGENTS.md`, "Where code lives").
- **Working rules worth noting.** AGENTS.md lists "three ways to hurt yourself" (kill by pattern, write to the
  live install, bake in origins) and a "Hit every surface" checklist (FACT `T:AGENTS.md:59-84`). rac's
  AGENTS.md has the same shape ("Ways to hurt yourself", "Cover every surface") (FACT `R:AGENTS.md`).
  INFERENCE: rac already borrowed this structure from T3.

## Strengths and weaknesses

### Strengths

- **A clean ownership line.** The environment owns processes, files, credentials and state; every window is a
  client over one typed contract. That single rule is what makes desktop, web, phone, SSH and tunnels work
  with "no other execution model" (FACT `T:docs/internals/overview.md:3-19`; `T:docs/internals/remote.md:3-7`).
- **Durable, idempotent work.** Command receipts, an outbox committed in the same transaction, restart
  continuation with a loop cap, and server updates that snapshot the database and roll back on a failed trial
  (FACT, Architecture and Build above). Few desktop apps take crash and update safety this seriously.
- **Agent-first by construction.** "A capability a user can trigger is usually one an agent should reach
  through MCP tools, and scheduled tasks run the same paths. That only works when it is a service method, not
  handler code" (FACT `T:AGENTS.md`, "Hit every surface"). Outside agents get the same tools after a real
  sign-in (FACT `T:docs/user/outside-agents.md`).
- **Provider neutrality that holds.** Capability flags and policy-driven fallbacks let nine provider kinds and
  the whole ACP Registry share one orchestrator (FACT `T:docs/orchestration-v2/provider-capability-system.md`).
- **Performance as a written rule, with tests.** Bounded snapshots, an output hub outside the event log,
  viewport-leased lookups, stepped animations paused off screen, the React Compiler enforced on every file, a
  perf suite with byte budgets, and 23 house lint rules (FACT, sections above).
- **Velocity.** About 27 merged PRs and 3 releases a day, 1,556 test files, 8-way sharded server tests (count;
  FACT `T:.github/workflows/ci.yml:359-423`).
- **Careful security in the plumbing.** Scoped sessions, DPoP-bound tickets kept out of socket URLs, privilege
  ceilings for delegated agents, signing kept away from PR code, pinned and hashed helper downloads (FACT,
  sections above).

### Weaknesses

- **Privacy defaults that rac must never copy.** Analytics are on by default, carry hashed OpenAI, Claude and
  T3 Connect account ids, and can be turned off only with an environment variable read from the shell profile
  (FACT `T:docs/user/telemetry.md:3-22`; `T:apps/server/src/telemetry/AnalyticsService.ts:70`).
- **Safety defaults.** New threads start in Full access, agents inherit the server's environment (not scrubbed
  the way rac's is), and the browser agent has no confirm step (FACT `T:docs/user/permission-modes.md:8`; INFERENCE for the browser, see
  Agents). The defense against injected instructions is mostly framing and tool descriptions.
- **Storage that grows without bound.** Databases of 12.5 to 40.4 GB, 327 GB written in 21 hours, and an
  unmerged retention fix (FACT #21371, #19105, #22630). 12,284 checkpoint refs in one repo (FACT #24083).
- **Memory and process leaks.** Hidden browser tabs never discarded (2.7 GB, #15579), 11.5 GB nightly
  (#18485), a headless Chrome GPU process spinning about 5 cores while idle on Windows (#18165) (FACT, issue
  titles and bodies).
- **Complexity.** 1.49 M lines in 8.5 months; a 12,687-line orchestrator; docs that lag code (the "eleven
  orchestration tools" doc against 18 tools in the orchestrator toolkit) (count; FACT `T:docs/orchestration-v2/orchestrator-mcp-server.md:195`). 1,095 open
  issues and 2,251 open PRs (FACT, GitHub search).
- **Cloud dependence for remote features.** T3 Connect needs Clerk accounts, Cloudflare tunnels, a 3-tunnel cap
  and a relay that sees thread titles for push (FACT, Data above). Its price may change (CLAIM, Theo's post).
- **Secrets in plain files** under a 0700 folder, and one file per replay nonce (291 on the maintainer's Mac at
  research time)
  (FACT, Data above).
- **A deprecated embedding API.** The browser panel uses Electron's `<webview>`, which Electron recommends
  against (FACT, Electron docs).

## What rac should take (ranked, concrete, with rough cost) and what rac should avoid

Cost scale for one maintainer directing agents: **S** about 1 to 3 days, **M** about 1 to 2 weeks, **L** 3 weeks
or more. All costs are INFERENCE.

### Take

1. **One local MCP door for outside agents, separate from the AI switch.** T3 serves `/mcp` with sign-in, a
   read-only default, a per-agent ceiling, a revocation list and 30-day sign-ins (FACT, Agents above). rac's
   MCP server today lives only during a run that rac started, has no secret on its socket, and disappears with AI
   off (FACT `R:docs/internals/ai.md:307-332`; brief). Proposal: a setting "Let other apps' agents use rac", off
   by default. When on, rac listens on a 0700 Unix socket with a stdio bridge in the app bundle, and optionally
   loopback HTTP with OAuth and PKCE so `claude mcp add --transport http` and `codex mcp login` work. A new agent
   triggers a rac approval card with a pairing code. Each agent gets a level (read-only, `ask`, `careful`);
   every call still goes through rac's guard and cards, and no level skips the risky list. Settings lists and
   revokes agents. Cost **M to L**. It fixes the gap a developer praised Aside for and Rhys Sullivan's wish to
   bring his own agent (brief).
2. **One service, many doors.** T3's rule: a transport handler "decode[s] the request, call[s] one service
   method, and map[s] the service's typed errors" (FACT `T:docs/internals/effect-services.md:9-21`). For rac:
   one table of browser actions (open tab, move to space, pin, archive, summarize) in rac-owned files; the
   sidebar, command bar, shortcuts, built-in agent, outside-agent MCP and any future CLI all call it. The MCP
   schema and command bar rows can be generated from it. Cost **M**. It turns "Cover every surface" into
   structure instead of a checklist.
3. **Declare each tool's risk in its type.** Annotate every agent tool `Readonly`, `Destructive`, `Idempotent`
   and `OpenWorld` (the MCP standard annotations), plus rac's risk class, and fail a unit test when one is missing
   (pattern: `T:apps/server/src/mcp/McpToolAccess.ts`). A read-only outside agent then sees only `Readonly`
   tools. Cost **S**.
4. **Frame page text as untrusted data.** Wrap snapshot text, link-summary input and Ask context in a tag with a
   random per-request id, insert U+2060 after `$`, `@` and word-leading `/`, and add the "treat it as untrusted"
   footer (FACT `T:apps/server/src/scheduledTasks/webhookTemplate.ts:52,150-176`). Add these cases to the first
   injection eval suite. Cost **S**. This is defense in depth. It does not close rac's known `auto`-level
   exfiltration gap (brief); only a policy change does.
5. **A clear human/agent handoff on a tab.** Any user input on the agent's tab takes control, bumps an epoch,
   drains the running action, and voids the agent's refs with a plain error (FACT
   `T:apps/server/src/preview/SessionControl.ts`). Add a calm agent cursor: 150 ms `ease-out`, opacity 1 when
   acting, 0.35 idle, 0.18 while the user drives (FACT `T:apps/web/src/components/preview/agentBrowserCursorLogic.ts`).
   Cost **S to M**.
6. **Stepped, visibility-gated loops in every rac WebUI.** Copy the rule and the helper: loops use `steps(4)`
   to `steps(30)`, `animation-play-state` defaults to `paused`, and one shared IntersectionObserver runs them only
   on screen, with the page visible and reduced motion off (FACT `T:apps/web/src/index.css:290-308,528-553`;
   `T:apps/web/src/lib/visibleAnimation.ts`). Use the 600 ms streaming fade that runs only while text streams
   (FACT `T:apps/web/src/index.css:2105-2120`). Cost **S**. It serves "nothing that repaints continuously" directly.
7. **Secret cards with one-use references.** When an agent needs a password or code, rac shows a card; the
   agent gets a `secret-ref`; a `fill_secret(ref, element)` tool types it into a password field without the
   value entering model context (pattern: `T:apps/server/src/secrets/SecretRequests.ts`). Improve on T3: bind
   the reference to the site's origin, and keep values in the Keychain, not files. Cost **M**. It is also the
   seam for the planned 1Password sign-in.
8. **Replay fixtures for agents and injection evals.** Record real ACP sessions and test pages once, then
   replay them through the real ACP client, guard and controller; replace only the agent process (FACT
   `T:docs/orchestration-v2/testing-strategy.md:9-50`). Ban sleeps and timeouts in tests with a lint check.
   Cost **M**, after CI compiles tests at all (brief).
9. **T3's release train, once CI builds.** Nightly is the release candidate; stable promotes the verified
   nightly's commit; a preview channel with no update feed exists for risky branches; the update feed is written
   only after the binary it points to is public (FACT `T:docs/operations/release.md:14-27,401-452`). Sparkle
   supports per-channel appcast items, so this maps over (INFERENCE). Cost **S to M**.
10. **Settle, snooze and Undo for tabs.** Auto-archive idle tabs after N days, snooze a tab until a time,
    wake it early on defined events, and give a 5-second Undo plus `Cmd+Z` for close, archive and unpin (FACT
    `T:docs/user/thread-sidebar.md:46-56,133-160,243-251`). Cost **M**. This is the roadmap's "tab clean-up".
11. **Short tool outputs by design.** Cap snapshot text (T3: near 20 KB), keep lists short, and tell the model
    in the tool description when not to call a tool (FACT `T:apps/server/src/mcp/toolkits/preview/tools.ts:140`;
    `T:docs/orchestration-v2/orchestrator-mcp-server.md:210-216`). Cost **S**. Check rac's current caps first.
12. **Themes from two colors.** Generate a space theme from `canvas` and `accent` in OKLCH, with optional
    overrides (FACT `T:docs/user/appearance.md:84-103`). Cost **S**.
13. **Secrets for helper processes on an inherited descriptor.** T3 passes its bootstrap token on fd 3 (FACT
    `T:apps/desktop/src/backend/DesktopBackendManager.ts:392-433`). rac's `nc -U` path is visible in `ps` and
    has no secret (FACT `R:docs/internals/ai.md:311-319`). Cost **S**.
14. **Import code as a reference.** T3's MIT cookie importers cover Arc, Chrome, Safari (with the Full Disk
    Access flow), Firefox, Zen and Helium (FACT `T:apps/desktop/src/preview/BrowserImport/`). Credit it if any
    code is copied (rac is GPL-3.0, MIT is compatible). Cost: saves days on Arc import.
15. **A short-lived warm agent, as an option.** T3 keeps a provider session for 30 idle minutes (FACT
    `T:apps/server/src/orchestration-v2/ProviderSessionManager.ts:56`). rac restarts the agent per message, 15 to
    25 s each (FACT `R:docs/internals/ai.md:707-716`). See the options in the map below. Cost **S to M**.

### Avoid

1. **Analytics on by default**, hashed account ids, or an opt-out that needs a shell variable. It breaks rac's
   first rule.
2. **Full access by default** and agents that inherit an unscrubbed environment. rac's empty-environment launch
   and `auto`-with-risky-list are better; keep them (FACT `R:docs/internals/ai.md:208-213`).
3. **Saving streamed updates as permanent events**, unbounded hidden state (refs, webviews), and long reads on
   the writer connection (FACT #21154, #24083, #15579, #21840).
4. **A cloud relay with accounts** for remote access. Clerk, Cloudflare tunnels and push through a relay that
   sees titles all phone home. If rac ever needs remote control, use LAN or Tailscale pairing only (INFERENCE,
   from `R:VISION.md` and AGENTS.md rule 1).
5. **Plain-file secrets** and one file per nonce. Use the Keychain.
6. **Surface sprawl.** 84 tools, 203 RPC methods and 88 docs come from a funded team with 473 contributors. rac
   is one maintainer; keep the outside-agent tool list small and stable.
7. **Embedding pages in a deprecated or custom web view** to build browser UI in web tech for its own sake. rac
   already has Chromium's tab lifecycle (discarding, freezing). T3's hidden-tab leak (#15579) is what skipping it
   costs.
8. **Seeding dev builds from live user data.** T3 copies its live database into dev worktrees (FACT `T:AGENTS.md`,
   "Test data"). For a browser that means cookies and history. Keep rac's separate dev profiles.

## Mapping T3 Code's patterns onto rac

### In plain English (at most 200 words)

rac already acts as the "server" for your tabs: the browser's main process owns them. What rac lacks is a home for
agent work. Today an agent's run vanishes when it ends. Outside agents cannot reach rac at all. T3 Code shows
a tidy fix. One local service owns the agents, their history and their tools. Every window, and every outside
agent, uses the same tool list through one door. The door checks who is asking and what they may do. For rac,
that door would let Claude Code in your terminal open a tab, read it, and ask you before risky clicks. It stays
shut until you turn it on, so a browser with it off does no extra work. rac should not copy T3's cloud relay,
its accounts, its default full access, or its habit of saving every streamed word forever. There are three
ways to build the service, listed below. The maintainer should pick one.

### Pattern map

| T3 pattern | What it does in T3 | rac today | Proposed rac form | Cost | Rules at stake |
|---|---|---|---|---|---|
| Local server, thin clients | Server owns state; desktop, web, phone are clients over one contract (`T:docs/internals/overview.md:3-19`) | Browser process owns tabs and prefs; the agent's run state lives only during a run (`R:docs/internals/ai.md:241-272`) | Keep tabs and spaces where they are. Add a small rac service for agent runs, automations and the outside-agent door (options below) | M to L | Fast (lazy start), cheap to update (new files) |
| One typed contract | `packages/contracts` shared by server and every client (`T:AGENTS.md`, "Contracts") | Agent tool schemas live in agent patches | One action table generates MCP tool schemas, command bar rows and agent tools | M | Opinionated, cheap to update |
| Event log, projections, outbox | Every change is an event; projections in the same transaction (`T:docs/internals/overview.md:53-71`) | No durable agent history | Do **not** event-source the browser. If history is wanted: one SQLite file in the profile with runs and one row per tool call (never per token), 30-day retention | M | Private (local only), fast |
| Capability negotiation | Clients ask what the server supports (`T:docs/internals/overview.md:21-38`) | Per-agent recipes (`R:docs/internals/ai.md:236-240`) | Expose a `rac_capabilities` tool so outside agents learn the browser's level, tools and limits | S | Cheap to update |
| Session kept warm | 30 min idle timeout (`ProviderSessionManager.ts:56`) | New process per message, 15 to 25 s start | Option A: keep as is. Option B: keep the agent alive while its panel is open, 5 min idle cap, MCP scoped to that session. Option C: prewarm on panel open | S to M | Fast vs "nothing outlives the run" |
| `/mcp` for outside agents | OAuth + PKCE, read-only default, ceiling, revoke (`T:docs/internals/environment-auth.md:42-66`) | None; AI off removes MCP | Setting off by default; Unix socket plus bundled stdio bridge; optional loopback HTTP OAuth; pairing card; per-agent level; revoke list | M to L | Private (local only), AI off costs nothing |
| Tool annotations, must-declare access | `Readonly`/`Destructive`/`Idempotent`/`OpenWorld`; compile fails without access (`McpToolAccess.ts`) | Guard risk list | Same annotations plus rac risk class; a unit test enforces them | S | Safety |
| Human/agent control epochs | Takeover drains work and voids refs (`SessionControl.ts`) | Tab indicator, Stop | Any user input on the agent tab takes control; agent cursor overlay | S to M | Calm, safety |
| Untrusted framing | Random tag, U+2060, footer (`webhookTemplate.ts`) | Guard and critic | Frame all page-derived text; add eval cases | S | Safety |
| Secret refs | One-use, 24 h, out of model context (`SecretRequests.ts`) | None | Secret card, `fill_secret`, origin-bound, Keychain | M | Private |
| Scheduled tasks and webhooks | Interval, fixed time, webhook via relay (`T:docs/user/project-settings.md:63-110`) | Not built ("automations", phase 6) | Local schedules only (run when rac is open, or a login item later). No public webhooks without a relay, so skip them | M | Private, fast |
| Settle, snooze, Undo | Auto-settle after 3 days; snooze; 5 s Undo (`thread-sidebar.md`) | Unloading spaces; no auto-archive | Tab auto-archive, snooze, Undo toast and `Cmd+Z` | M | Calm, opinionated |
| Stepped loops gated by visibility | `steps(N)`, paused off screen (`visibleAnimation.ts`) | Some WebUI motion | Adopt as a WebUI rule plus a lint or review check | S | Calm, fast |
| Panels open instantly by default | 0 ms default, 0 to 400 ms slider (`settings.ts:113-122`) | Arc-style motion is part of the vision | Do not copy the 0 ms default; keep short motion, honor reduced motion | none | Beautiful |
| Release train | Nightly as candidate, preview channel without feed (`release.md`) | No release yet | Adopt once CI completes one build | S to M | Cheap to update, update safety |
| Replay fixtures | Real transcripts, real code paths (`testing-strategy.md`) | 284 unit tests, never run in CI | Record ACP sessions and pages; replay through guard and controller | M | Safety |
| Default browser handoff | Any link can open in front of an agent (`default-browser.md`) | rac is the browser | "Send this page to my agent" action that hands the URL and selection to the outside agent via MCP | S | Opinionated |

### Three ways to build rac's local service

All three keep the browser process as the owner of tabs, spaces and windows. All three start nothing until
the user turns on outside agents or automations. Costs are INFERENCE.

- **Option A: inside the browser process (C++).** Extend today's MCP server to a long-lived, opt-in endpoint
  with pairing and per-agent levels. Store agent history with Chromium's own `sql::Database` in the profile.
  - For: no new binary to sign; reuses the guard, cards and tool provider as they are; one process to reason
    about.
  - Against: every change is a Chromium rebuild (minutes in a worktree); more C++ in rac patches; the service
    cannot run while the browser is closed. Cost **M**.
- **Option B: a sidecar helper, T3-style.** A small rac-owned executable in `rac.app/Contents/Helpers`
  (Swift or Rust), launched lazily by the browser with a bootstrap secret on an inherited descriptor, like T3's
  fd 3. It owns the outside-agent door, ACP agent processes, schedules and history. The browser exposes a narrow,
  typed "browser actions" channel to it, and every action still passes the browser-side guard.
  - For: fast iteration without Chromium rebuilds; a crash cannot take the browser down (T3's rule for native
    code, `T:docs/internals/overview.md:119-124`); replay tests run without a browser; mostly new files.
  - Against: a second binary to sign and notarize; an IPC protocol to secure and version; two places for state.
    Cost **L**.
- **Option C: no service; be a great MCP target.** Ship only the opt-in door (Option A's endpoint) and let
  outside harnesses such as T3 Code, Claude Code or Codex be the "server" for agent work, history and schedules.
  - For: least code; matches the developer quote in the brief ("so obviously good features", but let me bring my
    own agent).
  - Against: no automations or history for people without such a harness; rac depends on others' UX. Cost **S to M**.

INFERENCE: Option C first, then A or B only if automations become a priority, avoids building a T3-sized
system. Option B is the right shape if rac's agent work grows past what a Chromium patch can carry. The
maintainer should choose.

## Open questions and things you could not verify

- Does PR #22630 (delete thread events older than 24 hours) merge, and does it hold under heavy use? It was open
  on 2026-10-25.
- How far the browser panel lags Chrome's security fixes. Resolved in verification: Electron 44.9.3
  (2026-10-21) pins Chromium 152.0.7977.167 (FACT, `DEPS` at tag `v44.9.3` in `electron/electron`). That is two
  majors behind the pinned headless shell (156) and rac's Chromium 154.
- Is there an in-app telemetry switch on mobile or web? I found none in the settings contract, only a privacy
  link (`T:apps/web/src/components/settings/SettingsPanels.tsx:1899`).
- Who writes `~/.t3/userdata/clerk-tokens.json`, and why is it mode 0666 on the maintainer's Mac? This may be a
  local security issue for the maintainer to look at in T3, not in rac.
- When a person clicks inside an agent-controlled desktop `<webview>`, does control pass to them automatically?
  The server browser has explicit Take and Release buttons; I did not trace the desktop path to the end.
- T3 Connect's long-term price and its 3-tunnel cap.
- The "500,000 users" claim. Update-manifest fetches (403,277 for v0.1.2 in 3 days) are only a proxy.
- Any real prompt-injection incident through T3's browser tools. I did not search exhaustively.
- For rac (found while checking T3's signing notes): Chromium's entitlements file claims
  `com.apple.developer.web-browser.public-key-credential`, and Helium's signing patch keeps that line while
  removing others (it is an unchanged context line, FACT `R:patches/helium/macos/chromium-signing.patch:70-85`).
  T3 warns that macOS will not launch an app whose entitlements exceed its provisioning profile. Is rac's
  `PROD_MACOS_SPECIAL_ENTITLEMENTS_PROFILE_B64` secret set, and does Apple's profile grant that capability?
- Whether Claude Code and Codex can sign in to a Unix-socket MCP server, or whether rac needs loopback HTTP for
  `mcp login`. T3 uses HTTP for outside agents; stdio works only for agents that spawn the bridge themselves.

## Sources

- Repository and code: https://github.com/pingdotgg/t3code (clone at `1eb4071a497cf1388a41040283a4065245dbe977`;
  all `T:` paths).
- GitHub API: https://api.github.com/repos/pingdotgg/t3code (stars, forks, created date, license);
  `/releases` (730 releases, asset download counts); `/contributors`; `/commits`; search API for issue and PR
  counts.
- Issues cited: https://github.com/pingdotgg/t3code/issues/15579, /16997, /18165, /18485, /19105, /21154,
  /21371, /21715, /21840, /22630, /24083.
- Product site: https://t3.codes (positioning, "free", T3 Tools Inc.).
- Theo on T3 Connect pricing (via search results): https://x.com/theo/status/2082277789395501263
- Electron `<webview>` warning: https://www.electronjs.org/docs/latest/api/webview-tag
- Secondary, not relied on for facts: https://flaviocopes.com/t3-code/ ,
  https://enterprisedna.co/resources/ai-pulse/ai-pulse-2026-08-08-t3-code-doubles-down-on-zero-markup-pricing-as-a-trust-play/
- Local listings (names, sizes and modes only): `~/.t3/`, `~/.t3/userdata/`, `~/.t3/userdata/secrets/`.
- rac files: `R:docs/internals/ai.md`, `R:AGENTS.md`, `R:VISION.md`, `R:patches/rac/agent/`,
  `R:patches/helium/macos/chromium-signing.patch`, `R:plans/context/maintainer-brief.md`.

## Verification

An adversarial fact-check ran on 2026-10-25 against the same clone (`1eb4071`), `gh api`, t3.codes, Electron's
docs, and a names-sizes-modes listing of `~/.t3/userdata`. I opened no file contents there. Each row says what I
checked and what changed. "Confirmed" means the primary source matches the text.

| # | Claim | Source checked | Result |
|---|---|---|---|
| 1 | License MIT, T3 Tools Inc. | `T:LICENSE:1-3`; `gh api repos/...` (`MIT`); t3.codes footer | Confirmed |
| 2 | Node engines, Node 26.12.1 pin, Effect 4.0.5, Electron 44.9.3, electron-builder 26.16.1, electron-updater 6.8.9 | `T:apps/server/package.json:89-91`; `T:package.json:62-65`; `T:pnpm-workspace.yaml:64`; `T:apps/desktop/package.json:26-40` | Confirmed |
| 3 | `chrome-headless-shell` 156.0.8078.70, pinned by size and SHA-256, never below that version | `T:apps/server/src/preview/PreviewBrowser.ts:23-55` | Confirmed (the floor is about the CRLSet and SPKI blocklist) |
| 4 | Stars, forks, created date, open issues and PRs, merged PRs | `gh api` and search API | Confirmed; drift of a few units within hours, noted |
| 5 | 730 releases; 619 nightly, 52 preview, 59 "stable" | Paginated releases API | Counts confirmed. **Fixed:** the 59 include one `android-beta-93` prerelease; "about 3 nightlies a day" became the observed 2.6 a day; 238 days became 237 |
| 6 | v0.1.0 is the first "Beta" | v0.1.0 release body; `T:docs/operations/release.md:7-10` | Confirmed; added the citation |
| 7 | Last 100 commits: 21.5 h, 69 AI trailers, 68 Opus | Commits API at `1eb4071` | **Fixed:** 22.6 h, 73 AI trailers (72 "Claude Opus 5.5", 1 "Claude Fable 5.1"). The original likely used a different commit window |
| 8 | 473 contributors; top committers | Contributors API | Confirmed (counts drift by a few) |
| 9 | Analytics on by default; env var is the only off switch; no settings field | `T:apps/server/src/telemetry/AnalyticsService.ts:70`; `T:docs/user/telemetry.md:3-22`; grep of `T:packages/contracts/src/` | Confirmed |
| 10 | T3 Connect capped at 3 tunnels | `T:infra/relay/src/environments/ManagedTunnelLimits.ts:14,57-63` | **Fixed:** 3 is a default with a per-user override; "free" re-tagged CLAIM |
| 11 | 84 MCP tools in 11 toolkits; 19 `preview_*` tools | Counted `Tool.make(` in `T:apps/server/src/mcp/toolkits/*/tools.ts` | Confirmed (83 string-literal names plus `HTML_RENDER_TOOL_NAME`) |
| 12 | Docs lag code: "eleven tools" against 84 | `T:docs/orchestration-v2/orchestrator-mcp-server.md:195` | **Fixed:** the doc counts orchestration tools only; that toolkit has 18, not 84 |
| 13 | 203 RPC methods, 31 streams | `grep -c 'Rpc.make('` and `stream: true` in `T:packages/contracts/src/rpc.ts` | Confirmed |
| 14 | 69 command types, 45 event types | Parsed both unions in `T:packages/contracts/src/orchestrationV2.ts` | **Fixed:** 45 events confirmed; commands are 60 client plus 8 internal (68). The original line ranges were also swapped |
| 15 | 15 permission scopes | `T:packages/contracts/src/auth.ts:30-66` | **Fixed:** 17 in the `AuthEnvironmentScope` union |
| 16 | Panel animations 0 to 400 ms, default 0; font size 12 to 20, default 16 | `T:packages/contracts/src/settings.ts:113-130` | Confirmed |
| 17 | Motion values: `--ease-drawer`, composer shadow, `steps(4/6/8)` with the 120 Hz quote, 2.2 s `steps(30)` shine paused by default, 600 ms streaming fade, 5.3 s loading bar, 650 ms pulses, 1.08 thumb scale, utility counts | `T:apps/web/src/index.css:186-195,290-335,526-553,912,1008,2106-2121,2305-2330`; `grep` counts over `.tsx` | Confirmed, including 38/38/21/6/4/3 |
| 18 | Visibility-gated loops through one shared IntersectionObserver | `T:apps/web/src/lib/visibleAnimation.ts:10-62` | Confirmed |
| 19 | Agent cursor 150 ms `ease-out`; opacity 1, 0.35, 0.18 | `T:apps/web/src/components/preview/agentBrowserCursorLogic.ts:3-6`; `AgentBrowserCursor.tsx:76` | Confirmed. "1" is a timed active flag, not a mode |
| 20 | Mobile spring 330/26/0.7, overshoot clamped | `T:apps/mobile/src/features/home/thread-swipe-actions.tsx:54-59` | Confirmed |
| 21 | SQLite: WAL, `synchronous=NORMAL`, `checkpoint_fullfsync`, 32 MiB, 5 s busy, foreign keys, incremental vacuum, worker threads | `T:apps/server/src/persistence/Sqlite.ts:12-61` | Confirmed. **Clarified:** 32 MiB is `journal_size_limit`, a truncation target, not a hard cap |
| 22 | 69 migrations; FTS5 search; event table and indexes; about 18 projection tables | `T:apps/server/src/persistence/Migrations/` | 69, FTS5 and 18 tables confirmed. **Fixed:** six explicit indexes, not five |
| 23 | Desktop spawns the server with `ELECTRON_RUN_AS_NODE`; bootstrap on fd 3, telemetry fd 4/5, CDP fd 6/7 | `T:apps/desktop/src/backend/DesktopBackendConfiguration.ts:498-541`; `DesktopBackendManager.ts:392-433` | Confirmed (WSL uses stdin) |
| 24 | Agents get the "full login-shell environment" | `T:apps/desktop/src/shell/DesktopShellEnvironment.ts:76-99,307-318` | **Fixed, in four places:** only a 22-name allowlist comes from the login shell. The server inherits the app's environment. Agent inheritance is now tagged INFERENCE |
| 25 | Provider sessions close after 30 idle minutes, 4 h when pinned | `T:apps/server/src/orchestration-v2/ProviderSessionManager.ts:56-57` | Confirmed |
| 26 | Default runtime mode is Full access | `T:docs/user/permission-modes.md:8`; `T:packages/contracts/src/providerPolicy.ts:32` | Confirmed; added the code citation |
| 27 | Secret store is plain 0600 files in a 0700 folder; secret refs are one-use, 24 h, HMAC-named | `T:apps/server/src/auth/ServerSecretStore.ts:160-206`; `T:apps/server/src/secrets/SecretRequests.ts:1-40` | Confirmed |
| 28 | Chromium cookie decryption: `saltysalt`, 1003 iterations, AES-128-CBC; 10 sources | `T:apps/desktop/src/preview/BrowserImport/ChromiumKeys.ts:15-17`; `ChromiumCookies.ts:111`; `Sources.ts:79-180` | Confirmed; line range fixed |
| 29 | Webhook framing with U+2060 and the "untrusted data" footer | `T:apps/server/src/scheduledTasks/webhookTemplate.ts:1-28,52,150-176` | Confirmed. Named placeholders and `raw` mode skip some of it |
| 30 | OAuth codes 60 s; MCP session liveness 24 h; sign-ins 30 days; read-only default | `T:apps/server/src/auth/McpOAuth.ts:44`; `T:apps/server/src/mcp/McpSessionRegistry.ts:64`; `T:apps/server/src/auth/EnvironmentAuth.ts:75`; `T:docs/user/outside-agents.md:50,120` | Confirmed; one line number fixed |
| 31 | Lines of code | `git ls-files` plus `cat \| wc -l` | Total 1,487,475 confirmed. **Fixed:** `apps/mobile` is 174,276, not 287,742. Others are within 0.01% |
| 32 | Core file sizes (12,687 / 7,692 / 10,643 / 7,514) | `wc -l` | Confirmed |
| 33 | 1,556 test files, 54 browser tests, 23 integration tests, 23 lint rules, 32 patches | `git ls-files`; `T:oxlint-plugin-t3code/rules/`; `T:patches/` | **Fixed:** 59 browser test files. Others confirmed |
| 34 | CI on Blacksmith, 8 server shards | `T:.github/workflows/ci.yml:25-569` | Confirmed (2 to 8 vCPU Ubuntu, plus a 6 vCPU macOS runner) |
| 35 | Nightly gate, stable promotes nightly, preview has no feed, no macOS x64 CLI | `T:docs/operations/release.md:13-45,402-418` | Confirmed; line numbers fixed |
| 36 | Signed PR previews "without trusting PR code" | `T:docs/operations/release.md:60-87` | **Reworded:** secrets stay away from PR code, but the PR's JavaScript ships inside the signed app |
| 37 | Idle tunnels reclaimed after 5 minutes | `T:docs/internals/t3-connect.md:93-104` | **Fixed:** the cleanup mode defaults to `off` |
| 38 | Push payloads cut to 120 and 40 characters | `T:infra/relay/src/agentActivity/agentActivityPayloads.ts:44-109` | Confirmed |
| 39 | Restart continuation capped at 3 | `T:docs/internals/server-updates.md:94`; `T:apps/server/src/orchestration-v2/RestartContinuation.ts:33` | Confirmed |
| 40 | Issues #15579, #16997, #18165, #18485, #19105, #21154, #21371, #21715, #21840, #24083; PR #22630 open | `gh api .../issues/<n>` | States and titles confirmed. **Clarified** #21154: `node.updated` was 1.21 M of 2.55 M rows, mostly OpenCode threads |
| 41 | Maintainer's `statev2.sqlite` 2.68 GB; 371 secret files; `clerk-tokens.json` mode 0666 | `ls -la` (names, sizes, modes only) | 0666 confirmed. Size and count are snapshots: 2.93 GB and 329 files at 13:05 PDT. Both kept with times |
| 42 | Electron recommends against `<webview>` | electronjs.org webview-tag page | Confirmed |
| 43 | Helium's signing patch "claims" the passkey entitlement | `R:patches/helium/macos/chromium-signing.patch:70-85` | **Fixed:** it is an unchanged context line from Chromium's file, kept by Helium's patch |
| 44 | rac-side facts: run lifecycle, `nc -U` socket with no secret, 15 s and 25 s agent starts, scrubbed environment | `R:docs/internals/ai.md:205-213,242-250,311-332,707-716` | Confirmed |
| 45 | Open question: Chromium in Electron 44.9.3 | `gh api repos/electron/electron/contents/DEPS?ref=v44.9.3` | **Resolved:** 152.0.7977.167 |

Other edits: the plain-English summary now says one user's database reached 40 GB, not "some users'". The
peer-address rule now notes that it applies when no host is configured, and that the doc says it is "not a
firewall" (`T:docs/internals/remote.md:57-64`). The native-code rule now says "on the startup path" and names
the `ffi-rs` exception (`T:docs/internals/overview.md:119-124`). Added from verification: Claude sessions
pre-allow `mcp__t3-code__*`, so Supervised mode may not gate browser actions (INFERENCE). Also added: the
Cloudflare tunnel is in the data path even though the relay Worker is not (INFERENCE).

Not verified, still tagged CLAIM: "over 500,000 users" (`T:AGENTS.md:9`, self-report); Theo's X post on T3
Connect pricing (seen only through search results; I did not fetch x.com); "Events do not include prompts"
(T3's own doc, not traced in code); that T3 Connect is free.

Overall confidence: **high** for code-derived numbers, versions, motion values, storage, and agent plumbing. 45
claims checked. 23 were corrected or clarified: 16 substantive fixes, 3 line-number fixes, 1 refreshed snapshot
and 3 wording fixes. I found no fabrications. **Medium** for time-varying GitHub and
local-listing numbers, which drift by the hour. **Medium** for the INFERENCE lines on agent environment
inheritance and browser-action gating, which I did not trace through every provider adapter.
