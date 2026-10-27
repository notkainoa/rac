# Digest: T3 Code research dossier

Source: `R:plans/research/t3code.md` (dossier of `pingdotgg/t3code`, commit
`1eb4071a497cf1388a41040283a4065245dbe977`, 2026-10-25). Its Verification section adversarially checked
45 claims, corrected 23, found no fabrications; corrected values used here are authoritative. `T:<path>`
= file in the T3 clone (`/tmp/rac-overhaul/src/t3code`); `R:<path>` = rac worktree. FACT / CLAIM /
INFERENCE tags are from the dossier; load-bearing facts name their source.

## In plain English

T3 Code is not a browser. It is how the maintainer runs many coding agents side by side, with no AI of
its own: it drives agent CLIs you already pay for (Claude Code, Codex, and more). A Node program, the
"server", runs on your Mac; it spawns the agents, stores everything in one SQLite file, and gives each
task its own Git worktree. The Electron desktop app, a web app, and a phone app are just clients of that
server, so a phone can watch and steer work. A browser panel lets agents open, read, and click pages.
For rac the lesson is the shape: one local service, many thin windows, one tool list for people and
agents, reachable by outside agents through a signed-in MCP door. Warnings: T3 phones home by default,
gives agents full access by default, stores history in an ever-growing database (one user hit 40 GB),
and its browser agent has no confirm cards.

## Key facts

### Identity, scale, engines

- Agent harness, not a browser: a Node WebSocket server wraps provider CLIs (Claude, Codex, Cursor,
  OpenCode, ACP agents, Pi) and serves web, desktop, mobile clients (FACT, `T:AGENTS.md:3`). MIT, T3
  Tools Inc.; repo created 2026-02-08. "Control plane" and "500,000+ users" are self-reports (CLAIM);
  free (CLAIM). 30,044 stars, 7,119 merged PRs, 473 contributors (FACT, 2026-10-25); ~27 merges and 3
  releases a day; last 100 commits span 22.6 h, 73 with AI co-author trailers (72 Claude Opus 5.5)
  (FACT, corrected in Verification).
- Server Node (pin 26.12.1) on Effect 4.0.5; desktop Electron 44.9.3 pinning Chromium 152.0.7977.167
  (FACT, Electron `DEPS`) — two majors behind rac's 154; T3's headless browser is
  `chrome-headless-shell` 156.0.8078.70 (size+SHA-256 pinned). ~1.49M lines of TypeScript. Platforms:
  macOS DMG, Windows, Linux, hosted web app, iOS/Android, `t3` CLI; no macOS x64 CLI (segfaults) (FACT).

### Releases and CI

- 730 releases in 237 days: 619 nightly, 52 preview, 58 stable/alpha (FACT, corrected). Nightly needs new
  commits + ≥6 h gap (~2.6/day observed). First "Beta" v0.1.0 2026-10-15; stables 0.1.0–0.1.2 that week.
- Stable promotes the latest nightly's commit, never `main` HEAD; the preview channel is fully signed
  but has no update feed, so nobody is offered it (FACT). Signed PR previews: the PR builds only the JS
  with no secrets; `main` checks label/commit/author versus a vouch list, then signs — but the PR's
  JavaScript still ships in the signed app (FACT).
- macOS Developer ID + notarization; passkey entitlement
  `com.apple.developer.web-browser.public-key-credential` needs a provisioning profile that grants it
  ("apps claiming more than their profile allow will not launch") (FACT, `release.md:557-612`).
- Updates: electron-updater via GitHub Releases (deltas, user-clicked install); server updates snapshot
  the DB, trial-run the new build against a "prepared" gate, else roll back (FACT).
- CI: 1,556 test files; server tests 8 shards; provider behavior tested against recorded real
  transcripts ("replay fixtures"), replacing only the provider process; lint bans sleeps/timeouts/
  polling in tests (FACT).

### Architecture and process model

- One server per environment (`t3 serve`, service, or desktop-app child), port 3773; 127.0.0.1 unless
  Network access → 0.0.0.0 + restart (FACT). Desktop spawns the server with the Electron binary as Node
  (`ELECTRON_RUN_AS_NODE=1`); the bootstrap JSON with one-time token rides fd 3, never argv; fd 6/7
  carry browser-panel CDP (FACT).
- The desktop renderer is a client like any other, loading the web UI from a local scheme, so it runs
  fine with only remote servers. Native modules never load in the Electron main process on the startup
  path; native capability runs in forked children with deadlines (FACT).
- Transport: typed WebSocket RPC, 203 methods, 31 streams; auth at WS upgrade with per-RPC scopes
  (FACT). Subscriptions send "snapshot at N, then events after N" (≤1 MiB / 10 turns); live command
  output never enters the event stream — a separate hub streams one bounded tail per command, only to
  an expanded row (FACT).
- Event-sourced with an outbox: events, projections, command receipt, and outbox effects commit in one
  transaction; an ack means "intent committed", not "work done"; duplicate ids return the stored
  receipt. Contract: 45 event types, 60 client + 8 internal commands = 68 (FACT, corrected).
- Model: AppThread → Run (one counted user turn) → RunAttempt → ExecutionNode tree; "App ids are
  primary. Provider ids are refs"; rollback via hidden Git checkpoint refs under `refs/t3/`; restart
  continuation caps at 3; capability negotiation, never versions (FACT).

### Providers and sessions

- Adapters driven by capability flags, not provider names; missing features degrade by policy: no
  steering → interrupt-and-restart; no fork → portable context (FACT).
- Sessions stay warm between turns: 30 idle minutes, 4 h pinned (FACT) — why follow-ups are fast,
  unlike rac's 15–25 s per-message start (FACT, `R:docs/internals/ai.md:707-716`).
- The server child inherits the app's env; from the login shell only a 22-name allowlist (PATH,
  SSH_AUTH_SOCK, locale, XDG, cert vars...) is copied — a `~/.zshrc` key is not picked up by a
  Dock-launched app (FACT, corrected in Verification). Health probes never start sessions that could
  run hooks or open a login browser (FACT).
- Provider/model switch moves context as a "portable handoff" (budgeted, 16k tokens); Claude threads
  compact 2 min before their prompt cache expires (FACT).

### Storage

- `~/.t3` home; state in `~/.t3/userdata`; worktrees `~/.t3/worktrees/<project>/<name>`; scratch
  threads `~/.t3/scratch/<date>-<first words>-<id>` (FACT).
- One SQLite `statev2.sqlite` per environment: WAL, `synchronous=NORMAL`, `checkpoint_fullfsync=ON`,
  `journal_size_limit` 32 MiB (truncation target, not a cap), 5 s busy timeout, foreign keys, separate
  reader/checkpoint threads; 69 migrations; `orchestration_v2_events` + ~18 projection tables + FTS5;
  raw provider frames go to rotating logs (64 KiB), not the event store (FACT).
- Growth is the open wound: the maintainer's own DB hit 2.68→2.93 GB in 14 days (FACT, `ls`). Reports:
  17 GiB / 2.55M events; 1.21M `node.updated` rows in two days (#21154); 40.4 GB over 16,900 threads,
  delete freed nothing, VACUUM down 27 min (#21371); 327 GB written in 21 h (#19105); a retention fix
  is still an open PR (#22630); 12,284 checkpoint refs slowed every `git fetch` (#24083). INFERENCE:
  persisting streamed updates as permanent events was the mistake.

### Secrets and privacy

- Server secrets are plain files in `userdata/secrets/` (0700 dir / 0600 files), no Keychain; 329 files
  on the maintainer's Mac, mostly pruned-daily DPoP markers (FACT). Connection credentials do use
  Electron `safeStorage` (Keychain) (FACT). `clerk-tokens.json` is 0666 on the maintainer's Mac
  (writer untraced, likely `@clerk/electron`) — a T3 issue.
- Agent secret requests: user types the value into a card; the agent gets a one-use reference
  (`secret-ref:<32 hex>`), valid 24 h in one project; the consuming tool moves the value so it never
  reaches transcripts, projections, or model context (FACT).
- Product analytics ON by default → `ingest.t3.codes` → PostHog with hashed T3 Connect/OpenAI/Claude
  account ids; the only off switch is env var `T3CODE_TELEMETRY_ENABLED=false`; no telemetry field in
  settings. Excluding prompts is CLAIM (untraced). Relay traces to Axiom by default (FACT).
- T3 Connect remote access needs Clerk accounts and a Cloudflare tunnel per environment; the relay
  never sees the session token but the tunnel is in the data path (INFERENCE; encryption past CF edge
  unverified). Push carries titles (120 chars) + status (40 chars) via Apple/Google push; the
  3-tunnel cap is an overridable default; cleanup defaults `off` (FACT, corrected).

### Agent and browser panel mechanics

- 84 MCP tools in 11 toolkits (orchestrator 18, thread 17, preview 19, PR 7, project 7, device 4); docs
  lag code; 17 permission scopes (corrected from 15). Every tool declares MCP annotations
  `Readonly`/`Destructive`/`Idempotent`/`OpenWorld`; undeclared access fails to compile (FACT,
  `McpToolAccess.ts`).
- Page representation: Playwright `ariaSnapshot({mode:"ai", boxes:true})` with `aria-ref`s; refs die
  on navigation, new snapshot, or control handoff; text caps ~20 KB; password fields masked (including
  copies elsewhere in the tree); the snapshot tool tells the model not to call it unasked (FACT).
- Control handoff: one owner at a time; taking control bumps an epoch and drains running work; agent
  actions on a tab it does not control fail with "Browser control changed. Refresh the snapshot"
  (FACT). Desktop tabs are Electron `<webview>`s in per-scope partitions, hardened at attach
  (`sandbox:true`, no Node); Electron's docs recommend against `<webview>` (FACT). Remote streaming:
  JPEG screencast, quality 70, 1280 px, acks, 8 MiB socket cap (FACT).
- Agents get per-session bearer credentials scoped to environment/thread/provider/session, 24 h max
  age, revoked at session close; Claude gets `mcp__t3-code__*` pre-allowed, so Claude's Supervised mode
  may not gate browser actions (INFERENCE); ACP agents get a stdio bridge (FACT).
- Permission modes: Supervised, Auto-accept, Auto, Full access — default for new threads is Full
  access (FACT, `providerPolicy.ts:32`); for Claude that is `bypassPermissions`; delegated children
  may never run broader than their caller. No guard, critic, or confirm cards on browser actions; a
  Full access agent can drive a panel tab holding cookies imported from the user's real browser
  (INFERENCE). rac's guard and cards are stronger (FACT, `R:docs/internals/ai.md:407-562`).
- Prompt-injection defenses are framing and gating, not a policy engine: webhook values wrapped in a
  tag with a per-request id; U+2060 inserted after `$`, currency signs, `@`, word-leading `/` so
  `$skill`/`@file`/`/command` cannot fire; credential headers redacted; an untrusted-data footer
  (FACT, `webhookTemplate.ts`; named placeholders skip it). Guest messages wait for owner Send; agent
  HTML renders in sandboxed iframes without `allow-same-origin` (FACT). No real injection incident
  through browser tools found (unverified).
- Outside agents: `/mcp` with OAuth 2.1 + PKCE, pairing codes, read-only default or a runtime-mode
  ceiling (never a scope list), 30-day sign-ins, 60 s auth codes (FACT). On the host `t3 thread
  start|send|show|list` works without sign-in (FACT).
- Cookie import into the panel from 10 browsers (Chrome, Edge, Brave, Vivaldi, Opera, Arc, Helium,
  Safari, Firefox, Zen); Chromium cookies decrypted with the browser's Keychain key, PBKDF2 salt
  `saltysalt`, 1003 iterations, AES-128-CBC; Safari needs Full Disk Access (FACT).

### UI and motion (verified values)

- Three columns: 256 px sidebar / thread / right panel with tabbed surfaces. shadcn on Base UI +
  Tailwind; call sites may not restyle. Radius 10 px; glass `blur(12px) saturate(1.14)` light /
  `blur(16px) saturate(1.08)` dark; OKLCH colors; lint bans em dashes in UI copy and native `title`
  tooltips (FACT).
- **Panels do not animate by default**: 0–400 ms slider, default 0 (FACT, `settings.ts:113-122`).
  INFERENCE: right for power users; abrupt for an Arc-like browser — rac should keep short Arc-style
  motion, honoring reduced motion.
- House default 150 ms `ease-out` (38 uses), then 200 ms (21); named curve for sliding surfaces:
  `--ease-drawer: cubic-bezier(0.32, 0.72, 0, 1)`; menus/popovers fade 0→full scaling from 98% (FACT).
- Streaming text: new paragraphs/code blocks fade in 600 ms, opacity only, one-shot, only while
  streaming — never replayed when opening a finished thread (FACT).
- **Stepped, visibility-gated loops**: skeleton pulse `steps(4)` (at 120 Hz: ~14 vs ~288 updates/s,
  per the code comment); status pulses `steps(6)`, pings `steps(8)`; text shine 2.2 s with `steps(30)`
  (~14 fps), play state default `paused`; one shared IntersectionObserver sets `running` only
  on-screen, page visible, and reduced motion off, and toggles `will-change` (FACT). House rule: "No
  continuously repainting animations; they peg the GPU on high-refresh displays" (FACT).
- Agent cursor: 150 ms ease-out; opacity 1 acting, 0.35 idle, 0.18 while human drives. Mobile swipe
  spring: stiffness 330, damping 26, mass 0.7, overshoot clamped; looping mobile animation must use
  native-driver `Animated` (Reanimated `withRepeat` froze the UI) (FACT).
- Signature interactions (FACT): Settle — auto-settle after 3 days idle or PR merge, dragged across
  many rows at once; Snooze until a time, early wake only on approval/question/failure/new message;
  5-second Undo + `mod+z` for unpin/settle/snooze/archive/discard; Shift-click several models to race
  one prompt across providers (own thread+worktree each); tool calls collapse to one expandable
  summary line — matching the quiet rows the maintainer chose for rac's agent; composer chips act
  like characters and survive copy/paste; default-browser mode lets any link land in front of an
  agent; themes from 3 hex colors, rest derived; font size 12–20 px, default 16.

## What rac should take (ranked)

Costs: S ≈ 1–3 days, M ≈ 1–2 weeks, L ≥ 3 weeks (INFERENCE). Full pattern map in the dossier.

1. **One local MCP door for outside agents, separate from the AI switch** (M–L). rac's MCP lives only
   during a run rac started, has no secret on its socket, and dies with AI off (FACT,
   `R:docs/internals/ai.md:307-332`). A setting "Let other apps' agents use rac", off by default; 0700
   Unix socket with a bundled stdio bridge; optionally loopback HTTP with OAuth+PKCE so `claude mcp
   add` / `codex mcp login` work; pairing card; per-agent level (read-only/`ask`/`careful`);
   everything still passes rac's guard and cards; revocation in Settings. Copy T3's read-only
   default, per-agent ceiling, 30-day sign-ins.
2. **One service, many doors** (M). Transports decode and call one service method with typed errors.
   rac: one table of browser actions (open tab, move to space, pin, archive, summarize) in rac-owned
   files; sidebar, command bar, shortcuts, built-in agent, outside-agent MCP, and a future CLI all
   call it; MCP schemas and command bar rows generated from it.
3. **Declare tool risk in types** (S). Annotate every agent tool `Readonly`/`Destructive`/
   `Idempotent`/`OpenWorld` plus rac's risk class; a unit test fails on a missing declaration.
   Read-only outside agents see only Readonly tools.
4. **Frame page text as untrusted** (S). Wrap snapshot text, link-summary input, and Ask context in
   a tag with a random per-request id, U+2060 after `$`/`@`/word-leading `/`, plus an untrusted-data
   footer. Defense in depth; does not close rac's known `auto`-level exfiltration gap — only a policy
   change does.
5. **Human/agent control handoff on a tab** (S–M). Any user input takes control, bumps an epoch,
   drains the running action, voids refs with a plain error; add the calm agent cursor (150 ms
   ease-out; opacity 1 / 0.35 / 0.18).
6. **Stepped, visibility-gated loops in WebUI** (S). Loops `steps(4)`–`steps(30)`,
   `animation-play-state: paused` default, one shared IntersectionObserver, plus the 600 ms
   streaming fade that only runs while streaming. Serves VISION's "nothing that repaints
   continuously".
7. **Secret cards with one-use, origin-bound references** (M). Agent gets `secret-ref`; a
   `fill_secret(ref, element)` types it without the value entering model context. Improve on T3:
   bind the ref to the site origin, keep values in the Keychain. Seam for the planned 1Password
   sign-in.
8. **Replay fixtures + injection evals** (M, after CI compiles tests). Record real ACP sessions and
   test pages once; replay through the real ACP client, guard, and controller — replacing only the
   agent process. Lint-ban sleeps/timeouts in tests.
9. **Release train** (S–M, once CI builds). Nightly is the release candidate; stables promote the
   verified nightly's commit; a preview channel with no update feed; the update feed points only at
   already-public binaries. Sparkle appcast items support channels (INFERENCE).
10. **Settle, snooze, and Undo for tabs** (M). Auto-archive idle tabs after N days, snooze until a
    time with early wake on defined events, 5-second Undo + Cmd+Z on close/archive/unpin. This is
    the roadmap's "tab clean-up".
11. **Secrets for helper processes on an inherited descriptor** (S). T3 passes its bootstrap token
    on fd 3, never argv; rac's `nc -U` path is visible in `ps` and carries no secret (FACT,
    `R:docs/internals/ai.md:311-319`).
12. **Warm agent option** (S–M). T3 keeps sessions 30 idle minutes. Options: keep rac's per-message
    process; keep the agent alive while its panel is open (5-min idle cap, MCP scoped to that
    session); or prewarm on panel open. Tension with rac's "nothing outlives the run" rule.
13. **Short tool outputs by design** (S). Cap snapshot text (T3: ~20 KB), short lists, tell the
    model in the tool description when not to call it.
14. **Themes from two colors** (S). Generate space themes from `canvas` + `accent` in OKLCH.
15. **MIT cookie import code as reference** (saves days). Importers cover Chrome, Arc, Safari (Full
    Disk Access flow), Firefox, Zen, Helium among 10 sources. GPL-3.0 ← MIT compatible; credit if
    copied.
16. **Reference patterns**: signed PR previews keeping signing secrets away from PR code;
    capability-flag adapters with policy fallbacks instead of provider-name checks.

## What rac should avoid

1. **Analytics on by default**, hashed account ids, or opt-out via a shell variable. Breaks rac's
   first rule (nothing phones home).
2. **Full access by default** and agents inheriting an unscrubbed environment. rac's
   empty-environment launch and `auto`-with-risky-list are better; keep them
   (`R:docs/internals/ai.md:208-213`).
3. **Persisting streamed updates as permanent events** and unbounded hidden state (checkpoint refs,
   live webviews). Root of the 17–40 GB databases, 327 GB in 21 h, the 12k-ref slowdown, the 2.7 GB
   hidden-tab leak. rac history should be one row per tool call, never per token, with retention.
4. **A cloud relay with accounts** (Clerk, Cloudflare tunnels, push with visible titles) for remote
   access. All phones home. If rac ever needs remote control: LAN/Tailscale pairing only (INFERENCE
   from VISION).
5. **Plain-file secrets** and one-file-per-nonce. Use the Keychain.
6. **Surface sprawl** (84 tools, 203 RPC methods, 88 doc pages from 473 contributors). One
   maintainer: keep the outside-agent tool list small and stable.
7. **Building browser UI on a deprecated or custom web view for its own sake.** T3's Electron
   `<webview>` is one Electron recommends against, with Chromium two majors behind. rac already has
   Chromium's real tab lifecycle (discarding, freezing).
8. **Seeding dev builds from live user data** (cookies/history). rac keeps separate dev profiles.

## Caveats

- T3 Code is not a browser; mapping its "browser features" onto rac is analogy (INFERENCE) except
  where the browser panel itself is cited.
- Verification corrected 23 of 45 claims — including count and line fixes behind numbers above (73
  AI trailers; 59 browser test files; mobile LOC 174,276; 3-tunnel cap overridable; cleanup defaults
  `off`; 17 scopes; commands 60+8; 22-name allowlist; the passkey entitlement line is an unchanged
  context line kept by Helium's patch).
- Snapshot numbers drift: stars, issue counts, the maintainer's local DB size (2.93 GB) and
  secret-file count (329) moved within hours of the original read.
- Still CLAIM/unverified: "500,000 users"; T3 Connect pricing; "events exclude prompts" (T3's doc,
  code-untraced); T3 Connect being free.
- rac question surfaced by the dossier: rac's Chromium entitlements claim
  `com.apple.developer.web-browser.public-key-credential`; T3 warns macOS will not launch an app
  whose entitlements exceed its provisioning profile. Check whether rac's
  `PROD_MACOS_SPECIAL_ENTITLEMENTS_PROFILE_B64` secret exists and Apple's profile grants it.
- Whether Claude Code/Codex can sign in to a Unix-socket MCP server is open; T3 uses loopback HTTP
  for outside agents and stdio only for agents that spawn the bridge, so loopback HTTP is likely
  needed for `mcp login` (INFERENCE).

## Three ways to build rac's local service (dossier options)

All keep the browser process owning tabs/spaces/windows and start nothing until outside agents or
automations are on. Dossier INFERENCE: Option C first, then A or B only if automations become a
priority; Option B fits if rac's agent work outgrows a Chromium patch. The maintainer should choose.

- **Option A: inside the browser process (C++)** — extend today's MCP server to a long-lived opt-in
  endpoint with pairing and per-agent levels; agent history in Chromium's `sql::Database`. For: no
  new binary to sign, reuses guard/cards. Against: Chromium rebuilds per change; more C++; nothing
  runs while the browser is closed. Cost M.
- **Option B: sidecar helper, T3-style** — a rac-owned executable in `rac.app/Contents/Helpers`
  (Swift/Rust), launched lazily with a bootstrap secret on an inherited fd (T3's fd 3); owns the
  outside-agent door, ACP processes, schedules, history; every browser action still passes the
  browser-side guard. For: fast iteration without Chromium rebuilds; a crash cannot take the browser
  down. Against: a second binary to sign/notarize; IPC to secure; two places for state. Cost L.
- **Option C: no service; be a great MCP target** — ship only the opt-in door; let outside
  harnesses be the "server" for agent work, history, schedules. For: least code; matches the "bring
  your own agent" wish. Against: no automations/history without such a harness; depends on others'
  UX. Cost S–M.

## Where to look in the full dossier

`plans/research/t3code.md` (936 lines). Snapshot 27–42; Features 43–136; UI/look/feel 137–245;
Architecture 246–402 (transports, event model, browser panel); Data and storage 403–498 (SQLite,
growth incidents, secrets); Agents and AI 499–563 (tools, permissions, injection defenses, outside
agents); Build/release 564–618; weaknesses 619–667; take/avoid 668–760; pattern map + options
761–823; open questions 825–848; sources 849–866; Verification table (all 45 claims) 867–936 — read
before relying on any number.
