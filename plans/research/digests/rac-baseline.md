# Digest: rac baseline (2026-10-25)

Digest of `plans/research/rac-baseline.md`, audited at `main` `d3f0d66`. Its Verification section (32 claims re-checked) is authoritative; its corrections are folded in.

## In plain English

Nothing here changes a screen yet; it is the map later plans start from. rac is a working private Mac browser nobody else can install: one person built it in 23 days with AI agents, and it has never been released. It is Chromium 154 plus Helium plus 180 patch files. Spaces, pinned tabs, favorites and an optional AI agent work in the author's build. The risk is upkeep, not features. Chromium now ships every two weeks; rac is two versions behind and has never synced. Tests exist, but CI never runs them. The short fix list: ship one release, do one sync, shrink the patch surface, make the agent default safe, run tests in CI.

## Key facts

### What rac is

- Private macOS browser, GPL-3.0, fork of `imputnet/helium-macos`; repo `github.com/notkainoa/rac` (0 stars, 0 releases, created 2026-10-02). Chromium 154.0.8037.92 via Helium 0.18.2.1; `main` = tag `0.18.2.1` + 286 commits; macOS 13+, arm64 + x86_64. FACT
- 269 non-merge commits, one author; 259 (96%) have AI co-author trailers. No accounts, no server, no telemetry. FACT

### Upstream gap and cadence

- Helium-macos at 0.20.1.1 / Chromium 156.0.8078.47 (2026-10-22). rac is **6 releases** behind (0.18.3.1, 0.19.1.2 prerelease, 0.19.2.1, 0.19.3.1, 0.19.4.1, 0.20.1.1) and 2 Chromium majors. The brief's "seven" counted a nonexistent 0.19.1.1. FACT
- Chromium ships a stable major every two weeks from M153 (2026-09-08): M154 09-22, M155 10-06, M156 10-20, M157 11-03. FACT ([Chrome blog](https://developer.chrome.com/blog/chrome-two-week-release), [chromiumdash](https://chromiumdash.appspot.com/fetch_milestone_schedule?mstone=157)). `docs/internals/overview.md:69` still says four weeks. Helium minor = Chromium major (0.17=153 … 0.20=156); 12 releases 2026-09-12→10-22, one per ~3.3 days. FACT
- **rac has never synced**; neither checkout has the `upstream` remote. The first sync reworks CI: upstream removed `retrieve_and_unpack_resource.sh` and `devutils/build_tools.sh`, which rac's scripts call. FACT

### Patch stack (architecture)

- rac is a **quilt patch layer**, not a wrapper. Order: Chromium → ungoogled-chromium → Helium core (343 series entries: 254 helium, 71 ungoogled, 18 other) → Helium macOS (24) → rac (180, `patches/series:29-208`). It compiles into Chromium's own binary; **no rac process, daemon, or server**. FACT
- 180 patches, 110,741 patch lines, 325 new files (43,282 lines), 435 upstream entries, 869 hunks, 216 upstream files, +3,429/−1,049. Later rac patches edit rac files: +26,116/−6,368 (658 edits). FACT
- 66 patches touch no upstream file; 47 touch 1–3 hunks. Group cost (patches / upstream hunks): `ai` 39 / 98; `agent` 19 / 58; `spaces` 26 / 127; `pinned` 18 / 95; `look` 20 / **161** for only 792 new-file lines; `settings` 13 / 91; `sidebar-address-bar` 10 / 64. FACT
- 320 hunks (37%) are in `chrome/browser/ui/views`; settings resources 110, `ui/tabs` 63, `ui/webui` 39. Hot files: `chrome/browser/ui/BUILD.gn` (26 rac patches), `settings_localized_strings_provider.cc` (13), `prefs_util.cc` (11), `browser_command_controller.cc` (10), `browser_view.cc` (9), `vertical_tab_strip_region_view.cc` (9), `browser_view_tabbed_layout_impl.cc` (8). FACT
- Rebase risk: 139 of 216 upstream files are also patched by Helium/ungoogled, holding **663 of 869 hunks (76%)**. Between base and 0.20.1.1 at least 206 Helium core patch files changed; ≥117 rac files (624 hunks, 72%) sit in files those changed patches touch (lower bound: compare caps at 300 files). FACT for counts; per-file conflict is INFERENCE.
- 24 `fix-*` patches; PR #11 folded 13 (6 ai, 7 agent). Large repairs: `ai/11` (+1,350/−684), `agent/12-hardening` (+1,648/−233), `agent/15` (+1,045/−310), `ai/fix-agent-run-lifecycle` (+557/−511), `ai/fix-review-followups` (+964/−92). FACT
- Dead code: `look/horizontal-tabs` restyles tabs while layout is locked vertical; two prefs added then removed. Deletion candidates. FACT/INFERENCE

### Process model

- **Browser UI thread:** almost everything (spaces, sidebar, Views, AI service, chat, ACP, controller, guard, critic, link summaries, onboarding). **IO/pool:** MCP Unix socket, ACP stdio, spaces/history writes. **Network:** `SimpleURLLoader` with `rac_ai_chat` / `rac_ai_models`.
- **Renderers:** rac Mojo (`snapshot.mojom`), `semantic_validator`, `snapshot_agent`, edits to Chromium actor tools. **WebUI:** `chrome://rac-ai`, `chrome://setup/?tour`, settings; hidden cookie-less OTR profile per link summary. **Children:** ACP agents (own process group, scrubbed env) and `/usr/bin/nc -U <socket>`.

FACT (`docs/internals/ai.md:199-239,316-325`).

### Code and UI technology

- 323 rac files, 63,030 lines. C++ 151 `.cc` + 126 `.h` (50,805 with ObjC++, 5,937 tests); TS 17 (11,017 with CSS/HTML). AI + agent ≈38.6k lines = **61%**. FACT/INFERENCE
- Native chrome: Views C++ `ui/views/rac/**` 67 files, 16,108 lines. Assistant WebUI: plain TS/CSS, `chrome.send` (30 + 11 messages), `app.ts` 2,822, `app.css` 2,484; settings mix Polymer and Lit; colors via `AddRacColorMixer`. FACT
- Page reading/actions depend on `optimization_guide` AnnotatedPageContent (34 refs in 18 non-test files) and Google Glic actor internals; `kGlicActorToctouValidation` on. Breakage risk at a two-week cadence. FACT/INFERENCE

### Storage (under `~/Library/Application Support/me.kainoa.rac`)

- **No rac SQLite.** Spaces `rac.spaces` (JSON in `Preferences`); hidden tabs `<profile>/rac spaces` (`kVersion=1`, `.bak`, atomic, 1 s coalesce); window/tab mapping in session extra data; favorites/pinned `rac.sidebar.lists`; `rac.browser.*`, `rac.onboarding.*`; update toggle Local State `rac.browser_updates` (on); AI `rac.ai.*`. Keys `rac.ai.encrypted_keys`, base64 `os_crypt_async`, keychain **"rac Storage Key"**. Chat history `<profile>/rac_ai_history.json` **plaintext**, 16 MB cap, saved by default. ACP scratch `<profile>/Cache/rac-agent/scratch/<agent>`; MCP socket `<profile>/rac-agent-mcp/<token>/s` (0700/0600) or `/tmp/…` over 103 bytes. FACT

### What leaves the machine

- rac: never (no rac endpoints). GitHub: update check at launch then hourly (`SUScheduledCheckInterval` 3600), default on. Helium traffic (extensions/filters/spell/bangs/components) behind consent, asked in onboarding. FACT
- AI provider only with AI on: page text ≤8,192 tokens per block, `GET /models` with the key, link summary ≤3,000 tokens, critic metadata at `careful`. Link summaries fetch the site cookie-less from the user's IP. FACT

### Agent and AI mechanics

- 15 tools: snapshot, page text, tabs list/find, click, type, select, key, scroll, navigate, back, open/switch/close tab (agent-opened only), wait. Settle 4 s (10 s around navigations). 25 calls per turn. MCP versions `2024-11-05`…`2025-11-25`. FACT
- Levels `ask`, `careful`, `auto` (**default `auto`**); per-site Always/Never; no level skips risky. With AI on: control **on**, attach tab on, save history on, AI NTP on; every send starts a turn. Incognito/guest get no AI. ACP timeouts 45/3/90 s; critic 4 s / 4,000 bytes, fails closed. "AI off costs nothing": `AiServiceFactory` null unless regular + enabled; only test `MasterSwitchGatesEntryPoints`. FACT
- Models: `gpt-4.1-mini`, `claude-sonnet-4-5`, `gemini-2.5-flash`, `openai/gpt-4o-mini`; Ollama `llama3.2`, LM Studio. ACP pinned `claude-agent-acp@0.93.0`, `codex-acp@2.2.2`; Cursor, Gemini, Copilot (shell/write/URL denied), OpenCode, Goose, custom. FACT
- Safety: TOCTOU re-validation of element/URL/form at every boundary; published-vs-private snapshots; URL provenance; containment surviving Stop; cards (no default, no Allow shortcut); pause on real input; Stop via Cmd+./Esc/pill. ACP auto-approves only rac's own MCP tools via runtime-set fields (Claude, Codex verified; Cursor own allowlist; Gemini/Copilot/Goose cannot use rac tools). FACT
- **Known gap at `auto`**: cross-site `navigate` and typing model-written text into the attached tab are free (`AutoAsksOnlyForRiskAndForeignTyping`, `action_guard_unittest.cc:196-223`). Chain: open link, read a logged-in page, type what it read into the attached page, page script exfiltrates. The test disables URL provenance for its `navigate` case, so a hostile page's link still counts. FACT policy; exploitability untested. No eval or red-team suite exists. FACT
- Agents cold-start every message by design: Cursor ≈15 s, Claude Code ≈25 s to first tool call. CLAIM
- Outside agents: **none**. MCP serves only rac's launched agent, only during a run; AI off removes it. No CLI, HTTP API, skills, routines, Slack/Telegram. FACT

### Look, motion, exact values

- 6 px card inset, 10 px gap; **Top bar default** (40 px, pill radius 10, Chat 8) or Sidebar (bar at sidebar top); left/right; full/hidden only; Cmd+S frameless. Favorites 44 px; **≤3 per row in full sidebar** (4 only outside). Tint dark `#121212` 0x99 / light white 0xCC; selected tab solid with `0 2px 8px`; radii 12/10/11/8/6/4, dots 3/3.5; accent `#FCBF49`; focused pill border `#6395FC`; 8 Dia BrandColor themes; hidden spaces unload at 15 min. FACT
- Motion: space pager critically damped spring ω = 2π/0.25 s, 0.5× drag delta, rubber band 0.15/dimension 255, flick 300 DIP/s, 240 Hz sampling ≤1.5 s; cross-fade 150 ms. Sidebar 180 ms `FAST_OUT_SLOW_IN` (140 ms reduced). Swipe: axis lock 15 DIP, threshold 75 DIP, reset 300 ms. Edge reveal: 100 ms dwell, 150→300 ms exit grace, 3 s cursor grace, 350→100 ms expand (Helium 200 ms). Drag snap 150/100 ms. Hovers 150/120 ms. Find pill 120 ms `LINEAR`. Link summary 500 ms hold, 120 ms fade, 100 ms height, 700 ms throb. Agent indicator 240/160 ms `EASE_OUT`. Assistant CSS `cubic-bezier(0.23,1,0.32,1)`; onboarding `(0.2,0.8,0.2,1)` and overshoot `(0.34,1.4,0.64,1)` at 180–220 ms. FACT
- Reduce Motion respected everywhere found except two hover fades (Chat, site tiles). Infinite animations only while a reply streams. Literals in ~15 files; no tokens. FACT

### Build, CI, release

- `build.sh`, `dev.sh`/`he`, quilt, GN + siso (ninja→siso 2026-09-13). Worktrees get a 30 s APFS clone of ~100 GB `build/src`; first build "a minute or two" (CLAIM); own profile each. Main checkout is 71 commits behind `main` at `9b4d949`. FACT
- CI: `lint` passes; `sanity` applies all patches and **passes on a 30 s timeout** (139 runs: 103 pass, 30 fail, 6 cancelled); `build.yml` → 10 chained 6-hour phases per arch (4 runs: 3 fail, 1 cancel; 5th in progress); `pullfrog` 53 manual runs, 0 success. **CI never compiles or runs a rac test**, and `main` has no protection or rulesets. FACT
- Release blocker: macOS `tar` truncates mtimes to seconds, siso compares nanoseconds, so phases restart near step 0 (50,287 of 59,933 phase-3 reruns were `stale-deps`). Fix `tar --format pax` is PR #20, unmerged. CLAIM (secondary), FACT for PR.
- Tests: 278 cases in 33 files, 5 targets — `rac_ai` 153, `rac_agent` 85, `rac_spaces` 25, `rac_pip` 9, `rac_updates` 6. Zero for the UI groups; pinned tabs has 1. Tooling: 71 Python tests + `test-spaces.mjs` (398 lines), neither in CI. FACT
- 0 releases, `rac_version.txt` 0.1.0; 9 secrets exist (Developer ID, notarization, Sparkle EdDSA); `MAC_TEAM_ID` empty; download page hidden (`RELEASE_READY = false`); dev builds have no updater; feed `…/releases/latest/download/appcast-<arch>.xml`; versions must rise, no prerelease/draft. FACT
- 20 PRs (#1–#5 closed, #6–#19 merged, #20 open); 112 reviews, **all `COMMENTED`, 0 approvals**; 189/269 commits (70%) direct to `main`. FACT
- Built: spaces, pinned/favorites, two layouts, right sidebar, edge reveal, auto PiP, site control center, quiet address bar, onboarding (940×620, 7 steps), branding, assistant, agent, screenshot harness. Missing: command bar, Arc/Dia import, media controls, boosts, outside agents, sync, auto-archive. Dev switches in every build, ungated: `--rac-window-screenshot` (+ `-requests`, can click/type/swipe), `--rac-launch-in-background`, `--rac-agent-debug`, `--rac-agent-mcp-echo`. FACT
- Doc drift: site "thin layer" (110,741 patch lines), "It asks before it acts", "four weeks", "no Developer account", "seven releases", missing `acp-design.md`. Onboarding says the AI "never acts … without your confirmation", contradicted by default `auto`. FACT

## What rac should take (ranked)

Costs are INFERENCE.

1. **Keep the agent safety core; close the `auto` chain before any release.** Keep TOCTOU, published refs, containment, page-blind critic. Change one rule: after reading an unnamed site, typing model text needs a card; or cross-site navigation asks at `auto` once text is typed. Add 30–50 hostile local pages as an eval against 3–4 models and both run modes. *Guard 1–2 days; eval 1–2 weeks.* Needs sign-off.
2. **Do the first Helium sync now; pick a two-week-aware cadence.** Sync to 0.20.1.1 (Chromium 156), rework the CI scripts upstream changed, restore `upstream`. Then every Helium release, or each Extended Stable milestone (8 weeks) plus security releases. *3–7 days plus rebuild (needs approval); 1–2 days per sync if hunks shrink.*
3. **Shrink the UI groups' upstream surface.** Targets: <400 total upstream hunks (from 869), <150 in `ui/views` (from 320). Move `look`, `settings`, `spaces`, `sidebar-address-bar` logic behind single hooks; one `//chrome/browser/ui/rac` dependency instead of 26 patches on `ui/BUILD.gn` where rules allow. *2–4 weeks; repays every sync.*
4. **Fold repair patches into parents.** Finish the 24 `fix-*` and big repairs, splitting ones that fix several parents first. Target ~120 self-readable patches. *1–3 days per group with a local build.*
5. **Grow the per-run MCP server into an opt-in local endpoint for outside agents.** Reuse `mcp_server.cc` (672 lines), `mcp_protocol.cc` (286), the single controller entry and guard; add per-client permissions and a "connected agents" list; decouple from chat so chat can be off. *2–4 weeks plus design.* Conflicts with "lives exactly as long as its run"; needs sign-off.
6. **Put tests in CI.** Run 71 Python tests now (1 hour); compile/run the 5 C++ targets on a self-hosted Mac or in the release chain after the checkpoint fix (1–3 days plus a machine). Protect `main`.
7. **Keep the event contract as the UI seam.** `agent_events.cc` → `parseAgentEvent` is one typed, capped boundary; a new assistant UI can replace `app.ts` without touching the controller. *Free.*
8. **Collect motion into tokens.** One C++ header + one CSS file (now ~15 files of literals); keep Reduce Motion. *1–2 days.*
9. **Encrypt chat history at rest** with the `os_crypt_async` path used for keys. *1–2 days plus migration.*
10. **Put one seam around Chromium's AI internals** (`apc_extract`, `renderer_tools`). *~1 week.*
11. **Fix public claims and doc drift.** Hours.
12. **Gate the dev harness out of release builds**, especially `--rac-window-screenshot-requests`. *Hours plus a CI variant if needed.*

## What rac should avoid

- New features as more edits to hot upstream files (`browser_view.cc`, `prefs_util.cc`, `settings_localized_strings_provider.cc`, and similar), each already patched 3–37 times upstream and 4–13 times by rac. FACT for counts.
- Landing big features as follow-up fix chains on `main` without CI (121 fix commits and 658 self-edits are the result).
- Expanding the agent before injection evals exist; capability grows the blast radius of the `auto` chain.
- Growing `app.ts` further; choose a structure first (Chromium already ships Lit).
- Scheduling on a four-week Chromium cycle. It is two weeks.
- Publishing a design system built on Arc/Dia asset-catalog values without deciding that is acceptable (comments cite "BoostBrowser_TabUI", "ARCClients_BaseAssets", "SharedAssets").
- Treating "every message cold-starts the agent" as fixed for interactive features; it costs 15–25 s.
- More layouts and toggles; two layouts plus left/right already strain "opinionated" and the screenshot matrix.

## Caveats

- Nothing was launched: no screenshots, video, or feel. Look/motion notes come from code; a favorites-per-row claim was wrong until the call site was checked.
- No benchmark exists: "never slower than Helium" and "AI off costs nothing" are unmeasured. Sync cost is exposure, not conflicts; compare caps at 300 files.
- Unchecked: Chromium 155–156 APC/actor API changes; Helium features rac may duplicate; grit-string translations. siso diagnosis is CLAIM; PR #20 was still validating.
- Empty `MAC_TEAM_ID` under a real Developer ID: effects unknown. Exploitability of `auto` untested; policy confirmed. No agreement covers use of Helium's services.
- Main checkout's build is 71 commits behind `main`, so the daily build may lack PRs #11–#19. Not re-verified: repo traffic, merge-time medians, per-week commits; the ≥117 files overlap needs changed Helium patches' content.

## Where to look in the full dossier

- **Snapshot** (11–27); **patch groups** (39–64); **hooks into upstream files** (301–315); **process model** (245–315); **code layout** (273–300).
- **Data and storage** (317–365) — every path, format, key, egress row. **Agents and AI** (367–458) — defaults, tools, permission table, injection gap, MCP seam.
- **Motion table** (203–226) — starting point for tokens. **Build/release** (460–523); **strengths/weaknesses** (539–565); **decisions** (567–635); **take/avoid** (637–665).
- **Verification** (715–779) — 32 re-checked claims and six corrections (favorites 3/row, 1 off-switch test, onboarding promise, hourly updates, macOS 13, siso date).
