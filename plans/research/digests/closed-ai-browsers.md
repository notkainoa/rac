# Closed AI and Arc-like browsers — planning digest

Source: `plans/research/closed-ai-browsers.md` (researched 2026-10-25; **not adversarially verified**). Covers Arc, Dia, Comet, ChatGPT Atlas, Yab, Opera Neon, Chrome with Gemini, Edge with Copilot. All closed source, so evidence is vendor docs, changelogs, security research, and a few open side repos. Tags: **FACT** = primary source, **CLAIM** = marketing or self-report, **INFERENCE** = dossier author's reasoning. Dia/Arc motion numbers are FACT only about what Ardia's owner measured from binaries and recordings, not vendor statements.

## In plain English

Eight closed browsers. Arc matters most: it stops on 2026-12-22 and its users need a new home. Arc's own data says only about 1 in 18 daily users used several spaces, so rac should first copy the Arc habits that need no setup: link previews, a small window for outside links, tab clean-up, a fast command bar, and a faithful Arc import. The AI-first products pulled back: OpenAI shut Atlas, Microsoft folded Copilot Mode into Edge, Dia deleted Memory. Hidden page text fooled most AI helpers. The defenses that held were fixed rules, not smarter models. rac should add such rules, test them, and offer an opt-in door for outside agents.

## Key facts

### 2026 status changes (FACT)
- Arc ends **2026-12-22**; no new accounts since 2026-10-22; accounts deleted within 30 days after. "Export Data" exists; its format is unpublished.
- **Atlas shut down 2026-08-09** after 292 days; agent moved to the ChatGPT desktop app and a Chrome extension.
- **Edge Copilot Mode retired 2026-05-13**; agent is now "Browse with Copilot" (US, Microsoft 365 Premium).
- **Dia retired Memory 2026-09-24** and deleted the data.

### Products
- **Arc / Dia**: Chromium via internal SDK "ADK" (Dia: "ArcCore"); Dia moved from SwiftUI/TCA to AppKit to "make Dia lightweight" (FACT). Dia 1.54.0 (2026-10-22) on Chromium M156, weekly.
- **Comet**: planner on Perplexity servers; execution in three hidden built-in extensions updated from Perplexity's server (FACT, Zenity). CEO planned "hyper personalized" ads (FACT).
- **Yab**: one maker, system WebKit, 40 versions in 29 days, no account; agent runs as child processes of the user's Claude Code, Codex, Gemini or Cursor plan.
- **Opera Neon**: Do (local agent), Make (cloud VM). MCP and CLI free for bring-your-own agents since 2026-08-14.
- **Chrome + Gemini**: auto browse in paid US tiers (beta). The actor framework, `components/origin_gating` and WebMCP receiver are already in rac's Chromium 154 tree (FACT, tree paths).

### Arc features worth knowing (FACT, release notes)
- **Peek**: floating link preview; links from pinned tabs/favorites open in Peek; Shift-click; Split button; interactive dismiss.
- **Little Arc**: small window (Opt-Cmd-N), default target for links from other apps; Cmd-O promotes to main window; closed pages go to Archive.
- Split view up to 4 panes as one unit. **Auto Archive**: unpinned tabs untouched 12 h; media tabs never archived.
- **Clear** (Shift-Cmd-K) with Undo toast; **Supercopy** (Shift-Cmd-C, URL without tracking params); Cmd-T command bar with actions.
- **Air Traffic Control**: route outside links to a space by "contains"/"is equal to" URL rules.
- **Usage (FACT, CEO letter)**: 5.52% of DAUs use more than one Space; 4.17% use Live Folders; 0.4% Calendar Preview.

### Dia features worth knowing (FACT, changelog)
- Arc-style pinned tabs; auto-named tab groups; Cleanup offered when 10+ tabs go stale.
- Command bar over the URL field, no scrim; a small on-device model routes input between Chat and Google. Skills (slash prompts). No Peek or Little Arc.
- Arc import: **spaces become profiles, folders become tab groups**.
- E2E sync: per-device 256-bit seed, HKDF to AES-256-GCM and Ed25519, 24-word recovery phrase, SPAKE pairing with 6-character code (FACT, bulletins). Yab's sync has the same shape: device-made key the server never sees.

### Measured motion (Ardia's measurements; see Caveats)
- **Arc edge peek**: panel inset 5 pt, 227.5 pt wide, 0.5 pt border; spring response 0.185, damping 0.77 (~1.5% overshoot, rest ~0.22 s); exits ease-in-out ~150 ms. Docked hide: ease-out cubic 100 ms. Page card inset 10 pt.
- **Dia sidebar** hide/show: one spring both ways, response 0.215, ratio 0.79. **Tab hover card**: opacity 0.10 s, scale spring 0.92 to 1 (ratio 0.75, response 0.25), interruptible, none-delay when another card is up. **Tab open/close**: rows slide 0.14 s; closed row fades 0.10 s. **Command panel** grows out of the URL field in ~130 ms, content uncovered not scaled. **PiP throw**: fling over 350 pt/s snaps to a corner, spring response 0.9 ratio 0.9. rac already copies Arc's page spring (`rac-baseline.md:207`).

### Architecture
- **Atlas OWL** (FACT): Chromium's browser process runs outside the app ("OWL Host"), Swift app is the client, over Mojo; pixels via `CALayerHost`. Builds take minutes; Chromium crashes don't kill the app. Cleanest public "separate shell" design; needed a funded team (INFERENCE).
- **Chrome actor chain**: `GlicActorTaskManager` -> `ActorKeyedService` -> `ActorTask` -> `ExecutionEngine` -> `ToolController`. rac uses actor tools, not Glic's engine (FACT).
- Comet, Yab, Neon agents read pages as accessibility snapshots with ref ids. Yab's agent tabs live in an off-screen window until asked (FACT).

### Agent permission models
- **Yab** (FACT): **Ask / Auto / Bypass**. Auto asks only for Mac access and send/pay/delete/upload; Bypass never asks. Per-site Always here / Opt "Never here". Cmd-Return approves strong actions, Return weak ones, Esc "Not now". "The browser holds that yes, not the model." "Private tabs don't exist for agents." A task that read mail asks before sending its words to a site not yet visited.
- **Edge**: Light / **Balanced (default)** / Strict; Always allow / Allow once / Cancel (CLAIM). Camera/mic/location suspended during agent runs; screenshots kept up to 30 days (FACT).
- **Chrome** (FACT, Google security post): confirms sensitive sites (deterministic list), sign-in (model never sees passwords), purchases/messages. **Agent Origin Sets**: read-only vs read-write origins; "readable data can only be passed on to the writable origins"; planner cannot add origins without the gating function. Shipped first as simpler write-set-only. **User Alignment Critic** sees only action metadata. Glowing tab, work log, "Take over task".
- **Dia** (FACT): chat starts with no other-tab access and no write actions; inserts into third-party sites need approval in a Dia-controlled view; calendar events stay drafts; password fields and irreversible buttons invisible to the agentic system. **URL provenance**: a URL is fetchable only if it came from the user or a page they viewed; an added query parameter is rejected. Adopted after the team's own fetch-tool leak (2026-02-12).
- **Atlas** (FACT): logged-in or logged-out (fresh in-memory storage, discarded after); no code, downloads, extensions, files, autofill, memories; "Watch Mode" on sensitive sites (Willison could not trigger it); first pick silently became the default (Zenity).
- **Comet** (FACT): confirms email/messages, calendar changes, final orders "regardless of whether our systems detect suspicious activity"; per-site "Block tasks".
- **Neon** (FACT): MCP read tools (tabs, page content, screenshot) on by default; history off; **all write tools off until enabled**.
- **rac today** (FACT, `ai.md`): `ask`/`careful`/`auto`, per-site rules, exact URL provenance, redaction. Versus the field (INFERENCE): provenance beats Comet/Atlas/Edge; no data-flow rule; no isolated agent context; `auto` is near Yab Auto and looser than Edge Balanced.

### Outside-agent doors
- **Yab** (FACT): `yab mcp` (stdio bridged to a socket only the macOS user can open), 69 tools at the 0.0.18 snapshot, `yab` CLI, Claude Code/Codex plugin, one-click install; remote assistants pair by 8-character code through a Cloudflare Worker relay.
- **Neon** (FACT): MCP Connector through an Opera-run persistent proxy with Opera-account OAuth; local CLI over CDP with token-compact snapshots.
- **Comet** had a hidden `chrome.perplexity.mcp.addStdioServer` API, disabled after SquareX's report (FACT).
- Dia, Atlas, Edge, Arc: none. Chrome: WebMCP for sites; DevTools MCP attach after consent (144+).

### Incidents (FACT unless marked)
- Arc CVE-2024-45489 (9.8): cloud database rule let anyone attach a JS Boost to another user's account. Fixed server-side in a day; JS Boosts no longer auto-enable across devices; global Boosts switch.
- Comet: Brave 2025-08 (hidden Reddit text exfiltrated email and one-time code); Guardio (fake shop purchase, saved card autofilled); LayerX CometJacking (link query string; Perplexity first said "no security impact"); screenshot text read as user request; HashJack (text after `#`; also Edge, Gemini in Chrome); Lasso bypassed BrowseSafe 36% (CLAIM).
- Neon (Brave, 2025-10): invisible HTML exfiltrated account details; Opera first closed it "Not Applicable", then fixed it.
- Atlas: omnibox treated URL-like text as a trusted prompt; "Tainted Memories" planted instructions in ChatGPT memory. OpenAI: injection "may never be fully solved".
- Dia CVE-2025-15032 (hid `about:blank`) and CVE-2025-13132 (fullscreen without toast): custom shells reintroduce classic bugs; rac keeps Chromium's prompts (INFERENCE).

### Defense ranking (INFERENCE: "still works when the model is fooled")
1. Deterministic data-flow limits. 2. Browser-held confirmation. 3. Second model that never sees the page (rac's `careful` critic). 4. Detection classifiers (BrowseSafe: MIT, F1 up to 0.904). 5. Prompt marking. 6. Red teaming. Offline benchmarks: **BrowseSafe-Bench** (14,719 examples, 11 attack types, MIT) and **WASP** (82 sandboxed tasks; attacks partially succeed in up to 86% of cases).

### Privacy and data
- Every vendor except Yab (and rac) routes AI traffic through its own servers (INFERENCE). Dia: content data for improvement **on by default**, 30 days, opt-out (FACT). Yab: daily active installation ID plus cross-device ID **on by default**, opt-out; Cloudflare, Vercel, Neon (FACT). Arc: mandatory account, Firebase. Comet: terms allow use "to ... improve Comet and recommend relevant content" (FACT).
- Arc data: `~/Library/Application Support/Arc/User Data` plus `StorableSidebar.json` (`sidebar.containers[].spaces/items`, favorites in `topAppsContainerIDs`, themes in `customInfo.windowTheme`), keychain key "Arc Safe Storage" (FACT).

### Pricing
Arc free with account, dying. Dia Pro ~$20/month (CLAIM). Comet free/Max, Plus $5. Neon AI $19.90/month, MCP/CLI free. Chrome and Edge agents paid, US-only. Atlas, Copilot Mode and Dia Memory vanished within a year: a pitch for rac (INFERENCE).

## What rac should take

Costs are the dossier's rough estimates (INFERENCE).

1. **Arc import that keeps spaces as spaces** (1–2 weeks). Parse `StorableSidebar.json` (spaces, pinned trees, Today tabs, favorites, themes) plus Chromium profiles with user consent for the "Arc Safe Storage" key. Dia flattens spaces into profiles. Ship before 2026-12-22.
2. **Close the `auto` data-flow gap** (3–5 days plus tests). (a) Model-typed text not in the user's messages may go only to the origin it was read from; elsewhere a card shows the exact text. (b) At `auto`, the first action on an origin the user didn't name gets one card: Allow once / Always on this site / Don't allow. (c) Keep exact URL match; drop model-added fragments and query strings. Check whether `components/origin_gating` can carry the origin sets.
3. **Prompt-injection eval suite in CI** (1–2 weeks). Guard-level tests from BrowseSafe-Bench samples as local fixture pages, plus a small WASP-style end-to-end harness; ratchet the attack success rate, as Chrome does.
4. **Arc's daily habits with measured motion** (4–6 weeks, independent): Peek, Little Arc (target for outside links), Clear with recoverable archive that spares media tabs, Supercopy, Cmd-T actions. **Conflict**: `VISION.md:123-132` lists auto-archive and Peek-style previews as not planned; the maintainer must decide. Arc usage data argues for both.
5. **Outside-agent door: local, off by default, read-only by default** (2–3 weeks). Opera's defaults (read tabs/page text/screenshot on; history and writes off), Yab's transport (stdio command to a user-only Unix socket, can start rac hidden), one-click Claude Code/Codex setup, small `rac` CLI. Every call goes through the same controller and guard. Its own switch, separate from the built-in assistant; when off, nothing listens. Answers the Aside feedback.
6. **Isolated "clean" agent context** (~1 week). Atlas-style in-memory partition: no cookies or sign-ins, discarded after. Offer "Run without my sign-ins"; default for outside agents' first runs (INFERENCE).
7. **Drafts, not sends** (2–3 days): the agent fills mail, posts, calendar events; the user presses the final button; show typed text on the card.
8. **Approval details** (days each): Comet's "what was blocked and why" notice; Yab's money cap ($20/$50/$100 thresholds, monthly cap; once payments exist); Atlas-style pause on sensitive sites. Keep rac's no-shortcut rule for Allow on risky cards (`ai.md:477`).
9. **Skills as saved prompts with "/"** (2–4 days); five products converged here.
10. **Public security bulletin page** (half a day).
11. **WebMCP later** (~1 week, after a Helium sync). Chromium 154 has `modelContext`; prefer a site's declared tools, through the guard.
12. **Process** (INFERENCE): stay within two weeks of Chromium stable (Arc does; rac has never synced).


## What rac should avoid

1. **Cloud store or sync for executable customizations** (Arc CVE). CSS-only Boosts first; JS Boosts local, never auto-enabled by sync, never on sign-in/password/payment pages.
2. **Any rac-run relay or proxy for agents** (Opera proxy, Yab Cloudflare relay); any remote hand-off peer-to-peer or user-hosted (INFERENCE).
3. **Usage counting and data-on-by-default** (Yab IDs, Dia content data, Arc account, Comet ads).
4. **Detection as the main defense**: BrowseSafe bypassed 36% (CLAIM); Dia bypassed all its own detectors (FACT).
5. **Hidden privileged components** (Comet's extensions). Every powerful part visible and revocable (INFERENCE).
6. **AI memory.** Dia deleted it; Atlas's died; Tainted Memories. If ever, plain local Markdown with an off switch, never written from page content.
7. **Feature sprawl** (Arc's novelty tax; Yab's mail and "Get to Know Me" crawl).
8. **Raw DevTools/CDP as the outside-agent door**; it bypasses rac's guard.
9. **Treating address-bar text, URL fragments or screenshot text as the user's voice.**
10. **Leaving Chromium Views for a separate shell now.** OWL and ADK each took a funded team; long-range option to shrink the 217-file diff (INFERENCE).
11. **Silent permission defaults** (Atlas) and **custom shells that drop Chromium's security UI** (Dia's CVEs).

## Caveats

- **Not adversarially verified.** Treat vendor safety descriptions as CLAIM-grade on effectiveness.
- **Unverified or weak decision-driving claims:**
  - Arc/Dia motion constants and layouts are third-party reverse engineering (Ardia); publishing a design system on another vendor's values is an open question (`rac-baseline.md:662`).
  - Arc usage percentages are self-reported.
  - Yab "Auto" as default: manual never says "default"; 69 tools is from 0.0.18; whether agent traffic avoids Yab servers is implied, not stated.
  - Edge's three levels come from forum and guide summaries (CLAIM); how "popular site" is decided is unknown.
  - Arc Export Data format, and whether `StorableSidebar.json` stays readable after shutdown (INFERENCE). Arc's help centre returned 403, so Wayback copies were used.
  - Some incidents rest on secondary coverage (OpenAI, HUMAN Security, Cato, Guardio primaries not fetched). CLAIM-level: Lasso's 36% BrowseSafe bypass, Dia Pro pricing.
  - Chrome: the "sensitive sites" list, whether the full read-only origin set shipped, and whether rac can use `components/origin_gating` without Glic are unknown.
  - Opera's proxy data handling is INFERENCE. Comet's current state and Atlas shutdown reasons are unknown. No public motion numbers for non-Arc/Dia products.
- Rankings and costs are INFERENCE.

## Where to look in the full dossier

`plans/research/closed-ai-browsers.md` — status changes and legend 1–30; snapshot tables 43–69; features 71–288 (Arc inventory 78–100, Peek/Little Arc 155–174, import/sync 176–190, agent table 231–242, MCP/CLI 244–279); UI and the **motion table** 290–405; architecture 407–430; data and storage 432–447; **agents and AI** 449–564 (per-product 451–478, incidents 480–504, defenses 506–548, rac's gap 550–564); build/release 566–604; strengths and weaknesses 606–650; **ranked take/avoid** 652–748; open questions 750–777; sources 779–1015.
