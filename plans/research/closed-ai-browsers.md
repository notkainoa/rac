# Closed AI and Arc-like browsers: research dossier

Researched 2026-10-25. Subjects: Arc, Dia, Perplexity Comet, ChatGPT Atlas, Yab, Opera Neon, Chrome with
Gemini, and Edge with Copilot. All eight are closed source, so most evidence is vendor docs, changelogs,
engineering posts, security research, and a few open side repos.

How to read the evidence:

- **FACT** = primary source (vendor docs or changelog, the vendor's own engineering post, code, a CVE record).
  **CLAIM** = vendor marketing or self-report. **INFERENCE** = my reasoning.
- Path prefixes: `A:` = Ardia clone at `/tmp/rac-overhaul/src/ardia` (its `docs/dia-spec.md` holds Dia and
  Arc timings that Ardia's owner recovered from Dia's binary and from 120–240 fps screen recordings; treat as
  FACT about what Ardia measured, not a vendor statement). `Y:` = `yetanotherbrowser/yab-mcp` clone at
  `/tmp/rac-overhaul/src/yab-mcp`. `O:` = `operasoftware/opera-devtools-mcp` clone at
  `/tmp/rac-overhaul/src/opera-devtools-mcp`. `C:` = rac's Chromium 154 tree at
  `/Users/knewton/Dev/Github/rac/build/src` (read-only). `R:` = this repo.
- Web pages are cited by reference links that resolve in [Sources](#sources).
- Prompt-injection research is summarized at the level of "what went wrong and what was fixed". Exploit
  recipes are left out on purpose.

**Four status changes in 2026 shape everything below** (all FACT):

1. Arc stops working on **2026-12-22**. No new accounts since 2026-10-22. Accounts are deleted within 30 days
   after that ([TechCrunch][tc-arc-sunset], [How-To Geek][htg-arc]).
2. OpenAI **shut down ChatGPT Atlas on 2026-08-09**, 292 days after launch, and moved its browser agent into
   the ChatGPT desktop app and a Chrome extension ([9to5Mac][9to5-atlas-end], [MacRumors][mr-atlas-end]).
3. Microsoft **retired Edge's Copilot Mode on 2026-05-13**. Its features moved into normal Edge, and the agent
   became "Browse with Copilot" for paying Microsoft 365 Premium users in the US ([Edge blog][edge-may26]).
4. Dia **retired its Memory feature on 2026-09-24** and deleted the stored data, "since newer models no longer
   need it" ([Dia 1.50.0][dia-150]).

## In plain English (at most 150 words)

This covers eight closed browsers: Arc, Dia, Comet, ChatGPT Atlas, Yab, Opera Neon, Chrome with Gemini,
and Edge with Copilot. Arc matters most to rac now. It stops working on December 22, and its users need a
new home. Arc's own numbers say only about 1 in 18 daily users used more than one space. So rac should first
copy the Arc habits that need no setup. Those are quick link previews, a small window for outside links, tab
clean-up, and a fast command bar. The other seven bet on AI, and several pulled back. OpenAI shut Atlas in
August. Microsoft folded Edge's Copilot Mode back into Edge. Dia deleted its memory feature. Hidden text on
web pages has tricked most of these AI helpers. The defenses that held were fixed rules, not smarter AI. rac
should add rules like these, plus an opt-in door for outside AI agents.

## Snapshot

Table 1: what each product is.

| | What it is | Engine | Platforms | License | Open parts | Stars (open parts) |
|---|---|---|---|---|---|---|
| **Arc** (The Browser Company, now Atlassian) | Sidebar browser with spaces, Peek, Little Arc, Boosts; light AI ("Arc Max") | Chromium 155.0.8059.80 in v1.169.0, 2026-10-15 (FACT, [Arc release notes][arc-rn]) | macOS, Windows; Arc Search on iOS/Android | Proprietary | None. CEO: open-sourcing Arc would mean open-sourcing ADK, "core to our company's value" (FACT, [letter][tbc-letter]) | n/a |
| **Dia** (same company) | AI-first browser: chat with tabs, Skills, connected-app tools, Morning Brief; now has Arc-style sidebar and pinned tabs | Chromium M156 in 1.54.0, 2026-10-22 (FACT, [Dia changelog][dia-cl]) | macOS 14+ Apple silicon (binary's minimum OS 14.0, `A:docs/dia-spec.md:433`); Windows since 2026-10-01 ([changelog][dia-cl]) | Proprietary | None | n/a |
| **Comet** (Perplexity) | Chromium browser with the Comet Assistant side panel and an agent | Chromium (FACT, [Zenity][zenity-comet]) | macOS, Windows (2025-07-09), Android (2025-11-20), iOS (2026-03-18) (FACT, [MacRumors][mr-comet-ios]) | Proprietary | BrowseSafe injection detector and benchmark, MIT (FACT, [HF model][hf-browsesafe], [HF dataset][hf-browsesafe-bench]) | 53 likes model, 29 likes dataset (HF API, 2026-10-25) |
| **ChatGPT Atlas** (OpenAI) | ChatGPT-centred browser with agent mode | Chromium run as a separate process ("OWL") (FACT, [OWL post][oa-owl]) | macOS only | Proprietary | None | n/a |
| **Yab** ("Yet Another Browser", Serafim Korablev) | Arc-like browser whose agent runs on your own Claude or ChatGPT plan; built-in Gmail client | macOS system WebKit (FACT, [Yab][yab-home]) | macOS 15.4+; iPhone beta | Proprietary, free | `yab-mcp` launcher, MIT (FACT, `Y:README.md:305-307`) | 1 (gh API) |
| **Opera Neon** | Agentic browser: Chat, Do (local agent), Make (cloud builder), Tasks, Cards; MCP server | Chromium (Opera) | macOS, Windows | Proprietary | `opera-devtools-mcp` (Apache-2.0, fork of Google's chrome-devtools-mcp) and `opera-browser-cli` (MIT) (FACT, `O:README.md:1-4`) | 15 and 50 (gh API) |
| **Chrome + Gemini** | Gemini side panel, auto browse agent, Skills, Personal Intelligence | Chromium | Desktop; auto browse also Android | Chrome proprietary; actor framework is open in Chromium (`C:chrome/browser/actor/`) | Chromium code for the agent framework, origin gating, WebMCP | n/a |
| **Edge + Copilot** | Copilot in Edge (multi-tab, Journeys) and the Browse with Copilot agent | Chromium | Windows, macOS, mobile | Proprietary | None | n/a |

Table 2: age, pace, team, money, status.

| | First public release | Release cadence | Team | Business model | Status on 2026-10-25 |
|---|---|---|---|---|---|
| Arc | Invite beta 2022; Windows 2024 ([Wikipedia][wp-arc]) | Weekly Chromium-only updates since 2025 (FACT, [release notes][arc-rn]) | Unknown. Security team grew "from one to five" (FACT, [letter][tbc-letter]) | Free; account required | Sunsets 2026-12-22 |
| Dia | Beta June 2025; no waitlist 2025-10-09 (FACT, [changelog][dia-cl]) | Weekly, mostly Wednesdays (FACT, [changelog][dia-cl]) | Same company | Free browser; Pro about $20/month for AI limits (CLAIM, [MakerStack][dia-reviews]) | Active; Arc's successor |
| Comet | 2025-07-09, first for $200/month Max users; free 2025-10-02 (FACT, [MacRumors][mr-comet-ios], [Perplexity changelog][pplx-oct3]) | Unknown | Perplexity | Free; Pro/Max tiers; Comet Plus $5; CEO planned "hyper personalized" ads (FACT, [eMarketer][emarketer-comet]) | Active |
| Atlas | 2025-10-21 | Roughly weekly builds `1.2026.xx` (FACT, [Atlas notes via Releasebot][atlas-rb]) | OpenAI | Free with ChatGPT; agent for Plus, Pro, Business | Shut down 2026-08-09 |
| Yab | 2026-09-26 (v0.1) | 40 minor versions in 29 days (0.1 on 09-26 → 0.40 on 10-25) (FACT, [Yab changelog][yab-cl]) | One maker; 21st (YC W26) has 3 people (FACT, [YC][yc-21st]) | Free; uses the user's AI plan; no Yab account | Active, side project per maker's site (CLAIM, [serafim.cloud][serafim]) |
| Opera Neon | Invites 2025-09-30 at $19.90/month (FACT, [Opera][opera-neon-ship]) | Unknown | Opera | Free browser plus MCP/CLI since 2026-08-14; Neon's own AI is $19.90/month (FACT, [Opera][opera-free]) | Active |
| Chrome + Gemini | Gemini in Chrome US 2025-09-18 (FACT, [TechCrunch][tc-gemini-chrome]); auto browse 2026-01-28 (FACT, [Google][g-autobrowse]) | 4-week Chrome majors | Google | Auto browse only in paid Google AI Pro and Ultra, US only (FACT, [Google][g-autobrowse]) | Active |
| Edge + Copilot | Copilot Mode 2025-07-28; Actions 2025-10-23 (FACT, [SiliconANGLE][sa-edge], [MacRumors][mr-edge]) | 4-week Edge majors | Microsoft | Browse with Copilot needs Microsoft 365 Premium, US only (FACT, [Edge blog][edge-may26]) | Copilot Mode retired 2026-05-13 |

## Features

Status words: **shipped**, **beta** (preview, limited rollout, or nightly), **planned**, **retired**.
Arc gets the fullest inventory because Arc refugees are rac's near-term users.

### Tabs, sidebar, spaces

**Arc** (all FACT from [Arc release notes][arc-rn] and [older notes][arc-rn-old] unless marked)

- shipped: Vertical sidebar with Favorites (icon tiles at the top), Pinned tabs, and unpinned "Today" tabs
  below a line. Drag above the line or ⌘D to pin.
- shipped: Spaces with their own theme and icon; Profiles separate from spaces; per-profile settings
  (2024-01). Spaces Themes V2 with presets and dark mode.
- shipped: Folders in the pinned area; collapsible pinned section ("Collapse Pinned" in the command bar).
- shipped: **Auto Archive.** "Tabs that haven't been touched after 12 hours (change the timing in
  preferences!) are now stored in Archive." Downloads archive the same way. Tabs playing media are never
  archived or cleared. Per-profile archive timing since 2024-01. Exact longer options not confirmed from Arc
  (third parties list 24 h, 7 days, 30 days).
- shipped: **Clear** above unpinned tabs: closes unselected unpinned tabs, ⇧⌘K, with an Undo toast (FACT,
  from Arc's binary, `A:docs/dia-spec.md:276-291`).
- shipped: **Tidy Tabs** broom: AI groups Today tabs (Arc Max, early 2024).
- shipped: Pinned-tab reset: ⌘-click a pinned tab's icon returns to its pinned URL and keeps the drifted page
  in a new tab.
- shipped: Live Folders (GitHub PRs and review requests), Live Calendars (join button in the sidebar),
  hover Previews for Notion, Figma, Linear, Gmail, Calendar. GitHub Previews retired in favour of Live Folders.
- shipped: Multi-media tray in the sidebar; Mini Player keeps a playing video in the corner when you switch
  tabs; Meet chat in Picture-in-Picture.
- retired: Recent Tab indicator ("didn't see enough utility").
- **Usage reality** (FACT, [letter][tbc-letter]): "Only 5.52% of DAUs use more than one Space regularly."
  "Only 4.17% use Live Folders." "It's 0.4% for … Calendar Preview on Hover."

**Dia** (FACT, [Dia changelog][dia-cl] unless marked)

- shipped: Sidebar or top tabs, choice persists (1.25); sidebar refresh (1.28); rubber-banding (1.29).
- shipped: Tab Groups (1.9), auto-named (1.19) with a lighter model (1.49), pin groups (1.16), auto emoji.
- shipped: Arc-style pinned tabs outside favorites (1.52); new sidebar tabs can open at the top, Arc's order
  (1.54).
- shipped: Profiles you swipe between, with optional data sharing (1.43.1). Arc import turns **spaces into
  profiles** and **folders into tab groups** (FACT, Arc sunset notice at [arc.net][arc-sunset]).
- shipped: Live Groups for GitHub PRs (with CI status), Docs (Notion, Drive, Confluence), meetings; Arc's
  GitHub Live Folders import as Live Groups (1.53).
- shipped: Cleanup Tabs; Tidy offers clean-up when 10+ tabs go stale (1.30).
- shipped: Focus Mode: fully collapsing the sidebar (⌘S) (1.3.1, 1.5).

**Comet**: Chromium tabs plus tab grouping by the assistant (`BROWSER_GROUP_TABS` tool) (FACT,
[Zenity][zenity-comet]). No Arc-style sidebar found.

**Atlas**: vertical tabs (2025-11-18), tab groups (2026-01-21), auto-organize (2026-02-18) (FACT,
[Releasebot][atlas-rb], [9to5Mac][9to5-atlas-groups]). Retired with the app.

**Yab** (FACT, [Yab home][yab-home], [changelog][yab-cl]): spaces with colours, pins, folders and nested
folders, kept tabs, live folders, "Tidy" (0.36), Arc-style space sliding (0.9), top tabs with ⇧⌘S, right-side
sidebar option (0.10), sleeping tabs, "sites that never sleep" (0.16).

**Opera Neon**: **Tasks** are workspaces that group tabs, chats and context; TechCrunch called them "Tab
Groups combined with Arc Browser's Spaces" (FACT, [TechCrunch][tc-neon]).

**Chrome**: standard tabs, tab groups; Gemini can reason across selected tabs (FACT, [Google][g-autobrowse]).

**Edge**: multi-tab reasoning "with your permission"; **Journeys** group browsing history into topics with
summaries and next steps, free in English markets (FACT, [Edge blog][edge-may26]).

### Navigation and command bar

- **Arc** shipped: Command Bar ⌘T searches tabs, history, bookmarks and runs actions (press Tab right after
  ⌘T for actions); results follow the current space; Instant Links (⇧↩ opens the top result directly);
  "Ask ChatGPT" via Tab (Arc Max); Supercopy ⇧⌘C copies the URL without tracking parameters; Capture
  (⇧⌘2) screenshots with an editor (FACT, [release notes][arc-rn], [older][arc-rn-old]).
- **Arc** shipped: **Air Traffic Control** routes links from other apps to a space by rules "contains" or
  "is equal to" on the URL, with a default of a chosen space, the most recent space, or Little Arc (FACT for
  the feature and its 2023 launch line, [older notes][arc-rn-old]; rule details from
  [allthings.how][ath-atc], CLAIM-level).
- **Dia** shipped: command bar anchored over the URL field with no scrim; a small on-device model routes typed
  input between Chat and Google (1.50); ⌃⌘↩ forces Chat, ⇧⌘↩ forces Google (1.22); "new jira/figma…"
  shortcuts (1.9) (FACT, [changelog][dia-cl]; geometry in `A:docs/dia-spec.md:111-122`).
- **Atlas** shipped: new tab is a ChatGPT composer; an "Auto" option switches between ChatGPT and Google
  (2026-01) (FACT, [Releasebot][atlas-rb]). The omnibox once treated malformed URL-like text as a trusted
  prompt (FACT, [The Hacker News][thn-atlas]).
- **Yab** shipped: "the ⌘T field" suggests "The meeting in 12 minutes, the mail that waits on you, the tab
  you just had"; quick actions, clipboard history, calculator, emoji (FACT, [Yab home][yab-home],
  [manual][yab-manual]).
- **Comet** shipped: ⌥A opens the assistant, ⌥S summarizes, ⇧↩ searches Google instead of Perplexity
  (CLAIM, [fastshortcuts][comet-shortcuts]).

### Split view, Peek, small windows

- **Arc** shipped: **Peek** previews a link in a floating window. Links from pinned tabs and favorites open
  in Peek automatically; ⇧-click opens Peek (settable in Settings › Links). Peek has a Split button and an
  interactive dismiss gesture; the toolbar can render inside Peek (FACT, [older notes][arc-rn-old],
  [notes][arc-rn]).
- **Arc** shipped: **Little Arc**, a small window for quick lookups and for links from other apps (⌥⌘N;
  ⌥⌘-click). ⌘O moves its page into the main window; ⇧⌘O picks a space; links closed in Little Arc go to
  the Archive; extensions and full-screen video work there (FACT, [older notes][arc-rn-old], [notes][arc-rn]).
- **Arc** shipped: Split View up to 4 panes, "treated as a single unit" (pin, favorite, rename); drag a tab
  onto another to split; ⌥-click a link to split (FACT, [notes][arc-rn], [older][arc-rn-old]).
- **Dia** shipped: split targets when you drag a tab onto the page, split button, ⇧⌥-click opens a link in
  the right split, per-split nav bars (FACT, [changelog][dia-cl]; geometry `A:docs/dia-spec.md:769-836`). Dia
  has no Peek or Little Arc (FACT for absence from the changelog; `A:docs/dia-feature-parity.md:219` calls
  Peek "an Arc feature, not Dia's").
- **Yab** shipped: Peek (⇧-click), split from a Peek with one click, each half with its own address bar,
  pinnable splits (0.35), small window (manual page "Small window"), floating video (FACT, [Yab home][yab-home],
  [manual][yab-manual]).
- **Comet, Atlas, Chrome, Edge, Neon**: no Peek or Little Arc equivalent found. Comet has split view in its
  built-in extension (FACT, [Zenity][zenity-comet]).

### Import, sync, profiles

- **Arc** shipped: imports from other browsers; Arc Sync replaced iCloud sync (2024), described as
  "encrypted Sync"; Mac↔Windows tab sync (FACT, [notes][arc-rn]). **Export Data** in Settings › Advanced
  added for the sunset (FACT, [arc.net sunset][arc-sunset]).
- **Dia** shipped: Arc import (passwords, history, tabs, profiles, folders, bookmarks, extensions; keeps custom
  tab names 1.28); Sync with end-to-end encryption 2026-04-09, extended to unpinned tabs and per-profile
  extensions (FACT, [changelog][dia-cl], [bulletins][dia-bulletins]).
- **Comet**: desktop↔iOS sync of research threads and history (FACT,
  [MacRumors][mr-comet-ios]).
- **Atlas**: imported bookmarks, passwords, history at first run; at shutdown users had to export bookmarks by
  hand and "open tabs, history and logins did not carry over" (CLAIM, [Second Talent][st-atlas]).
- **Yab** shipped: imports from Arc (keeps pins and folder positions), Dia, Chrome, Safari, Firefox, Brave, Zen;
  `yab import chrome` brings sign-ins after a yes in Yab; end-to-end encrypted sync, off by default (FACT,
  [Yab home][yab-home], `Y:README.md:48`, [privacy][yab-privacy]).

### Privacy and blocking

- **Arc**: Google account integration, Google metrics and Google crash reports disabled (CLAIM,
  [arc.net/security][arc-security]). Account required. Telemetry SDKs observed in 2023: Segment, Sentry,
  LaunchDarkly (CLAIM, third-party traffic test, [Kostarelas][arc-privacy-blog]).
- **Dia**: ad blocking ("BCNY Blocklists", `A:docs/dia-spec.md:861-866`); per-site AI disable via MDM
  (FACT, [Dia security][dia-security]).
- **Comet**: built-in ad blocker; per-site "Block tasks on specific websites" (FACT, [Comet help][comet-help]).
- **Yab**: uBlock Origin lists, "about 160,000 rules"; sites blocked from the local network (0.10) (FACT,
  [Yab home][yab-home], [changelog][yab-cl]).
- **Neon**: Opera's ad blocker and free VPN in the free tier (CLAIM, [ToolChase][neon-toolchase]).

### AI assistant

- **Arc Max** shipped 2023-10, partly retired: Ask on Page (⌘F, retired 2025-08), 5-second link previews
  (hover + ⇧), ChatGPT in the command bar, Tidy Tab Titles, Tidy Downloads, Tidy Tabs, Instant Links.
  Enterprise policy `arcMaxDisabledByOrgPolicy` (FACT, [notes][arc-rn], [U-M IT][umich-arcmax]).
- **Dia** shipped: chat about the page, @-mentioned tabs, selected text, files; Skills (slash prompts, a
  gallery, natural-language builder 1.2); connected-app tools for Gmail, Calendar, Slack, Notion, Figma,
  Loom, Zoom, Outlook, Teams, SharePoint, Atlassian, with a "Request a tool" list of the top 400 SaaS apps
  (1.47.1); Morning Brief; queued and steerable chat (1.51); search past chats, history and artifacts (1.50).
  **Memory retired** (1.50) (FACT, [changelog][dia-cl], [1.50.0][dia-150]).
- **Comet** shipped: sidecar assistant with @tab targeting; Shortcuts (reusable "/" commands); Discover feed;
  email assistant (Max) (FACT, [Perplexity changelog][pplx-oct3]; CLAIM for shortcut details,
  [MakeUseOf][muo-comet]).
- **Atlas** (retired): "Ask ChatGPT" sidebar; "cursor chat" rewrites selected text in place; browser memories
  (opt-in) with a per-site visibility toggle in the address bar (FACT, [launch post][oa-intro]).
- **Yab** shipped: ask about the page, selected-text commands (on-device or on your plan), chat, Skills,
  Memory as plain Markdown notes, "Get to Know Me" (an agent reads your signed-in sites for about ten minutes
  to fill your profile) (FACT, [manual][yab-manual], [memory][yab-memory]).
- **Neon** shipped: Chat; Cards (saved prompts, a Cards store); Research (deep, one-minute, local) (FACT,
  [TechCrunch][tc-neon], `O:README.md:28-37`).
- **Chrome** shipped: Gemini side panel; Nano Banana image edits; Connected Apps (Gmail, Calendar, YouTube,
  Maps, Shopping, Flights); **Skills** (saved prompts run with "/" or "+", a preset library, synced) since
  2026-04-14; Personal Intelligence, opt-in, free US users since 2026-03-17 (FACT, [Google][g-autobrowse],
  [Yahoo Tech][yahoo-chrome-skills], [9to5Google][9to5g-pi]).
- **Edge** shipped: Copilot in the sidebar, multi-tab reasoning, browsing-history personalization "with
  your permission", Journeys, Voice and Vision (FACT, [Edge blog][edge-may26]).

### Agent

| Product | What exists | Status |
|---|---|---|
| Arc | None. "Browse for Me" on Arc Search builds a page from several results; ends 2026-11-23 | retired soon |
| Dia | No general clicking agent. Tools act through APIs and drafts: @Tabs opens and closes tabs (1.4), Autofill (1.1), Gmail and Calendar drafts that "stay in draft until you click Create" (FACT, [Dia security][dia-security], [changelog][dia-cl]) | shipped |
| Comet | Full agent in your signed-in tabs; Background Assistants run several tasks in parallel, Max only (FACT, [Perplexity changelog][pplx-oct3]) | shipped |
| Atlas | Agent mode in your session or in "logged-out" mode (FACT, [launch post][oa-intro]) | retired 2026-08-09 |
| Yab | Agent in its own tabs beside yours, signed in as you; routines on any schedule (0.18); watching threads; tasks steerable and queueable (FACT, `Y:README.md:189-268`) | shipped |
| Neon | **Do** acts locally in your session; **Make** builds apps in a cloud VM that keeps working when you disconnect; scheduled tasks (FACT, [Opera][opera-neon-ship], [InfoQ][infoq-neon]) | shipped (paid) |
| Chrome | **Auto browse**, Gemini 3, US AI Pro and Ultra; daily action limits (FACT, [Google][g-autobrowse], [9to5Google][9to5g-autobrowse]) | beta ("preview") |
| Edge | **Browse with Copilot** (was Copilot Actions), US Microsoft 365 Premium, "experimental", usage limits (FACT, [Microsoft support][ms-browse]) | beta |

### Extensibility (CLI, MCP, API, extensions, mods)

- **Arc** shipped: **Boosts**: no-code (colours, fonts, "Zap" to hide elements, "Shuffle") and code Boosts
  (CSS and JavaScript), a gallery, sharing. After CVE-2024-45489, JavaScript Boosts no longer sync-enable
  across devices, all were disabled until re-enabled per device, and a global Boosts toggle was added (FACT,
  [notes][arc-rn], [Tenable][tenable-arc]). Chrome extensions work. No MCP or CLI. AppleScript existed
  (INFERENCE from Yab shipping "Arc/Chrome-compatible AppleScript", [changelog][yab-cl]).
- **Dia** shipped: Chrome extensions (MV2 disabled 1.17); AppleScript and Raycast (1.7); no MCP named
  anywhere in the changelog (FACT, [changelog][dia-cl]).
- **Comet** shipped then pulled: a hidden `chrome.perplexity.mcp.addStdioServer` API in a built-in extension,
  limited to perplexity.ai pages, disabled in a silent update after SquareX's 2025-11-19 report; Perplexity
  said it needs developer mode and user consent (FACT for the API and both positions,
  [SecurityWeek][sw-squarex], [Help Net][hn-squarex]). Comet's Sidecar connects to MCP services like Slack,
  GitHub, Gmail, Notion (FACT, [Zenity][zenity-comet]).
- **Yab** shipped: built-in **MCP server** (`yab mcp`, stdio bridged to a socket "only your macOS user can
  open"); **69 tools** in the 0.0.18 snapshot (newer builds may have more); one-click install into Claude
  Code and Codex; `yab` CLI (`yab "task"`, `yab serve`, `yab setup`); a Claude Code and Codex plugin with a
  skill; **remote assistants** pair with an 8-character code through `https://yab-sync.21st.workers.dev`;
  Boosts and plugins with a reviewed Store (PRs to `yab-plugins`, daily live checks); userscripts (0.24)
  (FACT, `Y:README.md:9-40,189-268,272`, [Yab store][yab-store]).
- **Opera Neon** shipped: **MCP Connector** (2026-03-31): Neon is the MCP server; Opera runs "a persistent
  proxy server so the MCP connection stays alive even when Neon is closed"; OAuth2 with an Opera account. Read
  tools on by default (tabs, page content, screenshot); history off; **all write tools off by default**
  (FACT, [Opera MCP post][opera-mcp]). **opera-browser-cli / opera-devtools-mcp** (May 2026): local, CDP on
  port 9224, token-compact snapshots, plus `opera_do`, `opera_make`, `opera_research`; Neon can also connect
  *to* outside MCP servers (FACT, [Opera CLI post][opera-cli], `O:README.md:28-37`,
  `O:docs/tool-reference.md`). **Free since 2026-08-14 for bring-your-own agents** (FACT, [Opera][opera-free]).
- **Chrome** shipped/beta: Chrome extensions; **WebMCP** (sites register tools for agents) in early preview
  from Chrome 146 and an origin trial reported for 149–156 (FACT for the preview, [VentureBeat][vb-webmcp];
  CLAIM for the trial range, [mcpplayground][webmcp-moved]); rac's Chromium 154 already contains it
  (`C:third_party/blink/renderer/core/script_tools/model_context.idl:1-25`,
  `C:chrome/browser/actor/actor_script_tool_receiver.h:17-35`). Chrome 144+ lets an outside DevTools MCP
  client attach to the user's running browser after a consent dialog (FACT, `O:docs/advanced-usage.md:55-101`;
  the dialog and prefs exist in `C:chrome/browser/devtools/devtools_connection_dialog.cc:49-83` and
  `C:chrome/browser/devtools/remote_debugging_server.cc:163-189`).
- **Edge**: Chrome and Edge extensions; no MCP server for outside agents found.

### Other

- **Dia**: Morning Brief and Weekly; Live Calendar and meeting groups; PiP with corner throw; iPhone Handoff
  (FACT, [changelog][dia-cl]).
- **Yab**: a full Gmail client (triage, snippets, send later, read receipts by pixel, opt-in), calendar,
  call window for Meet, PDF fill and sign, translation, reading mode (FACT, [manual][yab-manual],
  [privacy][yab-privacy]).
- **Comet**: Comet Plus ($5, publisher revenue share news) (FACT, [TechCrunch][tc-comet-free]).

## UI, look, and feel

Only Arc and Dia have measured motion numbers in public. They come from Ardia's owner, who read Dia's and
Arc's binaries and traced high-frame-rate recordings (`A:docs/dia-spec.md`). Nobody has published timings for
Comet, Atlas, Neon, Chrome's agent, or Edge's agent. Durations below are seconds unless marked.

### Arc

- **Layout.** Sidebar on the left holds traffic lights, back and forward, the address field, favorites, pinned
  and Today tabs, and a footer with Library and space dots. The page sits in a rounded card inset **10 pt on
  every side**, docked or hidden; the docked sidebar is **227.5 pt** wide (FACT, measured,
  `A:docs/dia-spec.md:255-274`).
- **Hidden sidebar and edge peek.** With the sidebar hidden, pointing at the left edge slides in a floating
  panel inset 5 pt from the window's edges, 227.5 pt wide, with a 0.5 pt light border. Motion: a spring with
  **response 0.185, damping ratio 0.77**: 93 % of the travel in 66 ms, 1.5 % (3.5 pt) overshoot at about 0.12,
  at rest by about 0.22. It leaves with ease-in-out over about 150 ms. Hiding the docked sidebar is
  **ease-out cubic, 100 ms**. Docking from the peek is instant (FACT, measured, `A:docs/dia-spec.md:255-274`).
- **Space swipe.** rac already copies Arc's page spring: critically damped, ω = 2π/0.25 s, pages move at
  0.5× the scroll delta, rubber band coefficient 0.15 over 255 (FACT, `R:plans/research/rac-baseline.md:207`).
- **Visual language.** Per-space gradient themes with a grain layer, theme colours bleeding into the command
  bar and previews, custom tooltips that show shortcuts, emoji icons for spaces and tabs (FACT,
  [older notes][arc-rn-old]; grain is Arc's `ARC_WindowThemeUI`, `A:docs/dia-spec.md:16`).
- **Signature interactions that feel great** (INFERENCE from the feature set and from Arc fans' asks; the
  open-source clone `anthracite-browser` ranks Air Traffic Control the 4th most-missed Arc feature,
  [issue][anthracite-atc]): the space swipe with haptic detents; Peek from pinned tabs; Little Arc for outside
  links; ⌘T with actions; Clear and Undo; Supercopy; Boost Zap (click to delete a page element);
  Capture.
- **Things that feel bad.** "Too many new things to learn, for too little reward" (the "novelty tax");
  "Arc was bloated. We built too much, too quickly" (FACT, [letter][tbc-letter]). Large sidebars lagged,
  especially Little Arc, until a 2024 fix (FACT, [notes][arc-rn]). A mandatory account (FACT,
  [BGR][bgr-arc]).

### Dia

- **Window.** Behind-window blur (`NSVisualEffectView`, material 29 dark / 13 `.hudWindow` light), a base tint
  (black 0.4 dark, white 0.8 light), then a profile-colour vertical gradient at alpha 0.5 dark / 0.75 light
  whose bottom stop is the tint lightened by ΔL 0.25 in HSL. The page card is `#121212` at 0.5 (dark) or
  white 0.7 (light), radius 10, inset top 6, right 7, bottom 7. Dia never reads Reduce Transparency itself;
  the only accessibility query in the binary is Reduce Motion (FACT, `A:docs/dia-spec.md:27-60,84-89`).
- **Toolbar** 41 pt tall inside the card; SF Symbols at 13 pt regular; web pages show the host only; URL hover
  morphs the breadcrumb into a pill with the full URL (FACT, `A:docs/dia-spec.md:91-110`).
- **Sidebar** 190 pt. Pinned tiles 41 pt tall, 6 pt apart, radius about 10. Tab rows 34 pt on a 37 pt pitch,
  16 pt favicon, titles fade at the trailing edge instead of an ellipsis. The selected pinned tile is themed
  from its favicon: colourful icons get a blurred-icon ring (CIGaussianBlur radius 5), one-colour icons a
  filled tile (FACT, `A:docs/dia-spec.md:147-195`).
- **Motion, with exact parameters** (FACT, recovered from the binary or traced, `A:docs/dia-spec.md` lines given):

| Interaction | Parameters | Lines |
|---|---|---|
| Tab hover card show | opacity 0→1 over 0.10 on cubic-bezier(0.25, 0.46, 0.45, 0.94), plus a spring on scale 0.92→1, damping ratio 0.75, response 0.25; scales from its top-left corner; starts from the current presentation value so it is interruptible | 196-217 |
| Tab hover card dismiss | opacity →0 over 0.10, spring to scale 0.92, ratio 0.6, response 0.2 | 196-217 |
| Hover card delay | 0.5 or 0.1 before showing; 0 when another card is up; row to row jumps with no glide | 196-217 |
| Tab open and close | rows below slide one pitch in 0.14 on cubic-bezier(0.25, 0.1, 0.25, 1); a closed row fades out in 0.10 on ease-out (0, 0, 0.58, 1); the new row appears in place at once | 219-238 |
| Sidebar hide and show (⌘S) | one spring both ways, response 0.215, ratio 0.79: 90 % in 100 ms, 1–2 pt overshoot at about 0.15, rest by about 0.27 | 240-253 |
| Command panel from the URL field | grows out of the field's box with an exponential ease-out of about 130 ms; content is uncovered, not scaled | 350-367 |
| Profile paging (swipe) | page moves at −0.5× the scroll delta; rubber band 255·(1 − 1/(0.15·x/255 + 1)); a release over 5 pt/s goes to the next page; settle spring 0.25 critically damped; page-detent haptics | 527-558 |
| Drag a tab out | split targets slide in over about 0.11; dropping away from a target grows a new window in about 0.2 | 769-836 |
| PiP throw | fling over 350 pt/s picks the screen corner within ±45°; spring response 0.9, ratio 0.9; 10 pt corner inset; settled within 0.2 pt | 915-967 |
| New tab "area light" | 30 fps display link only while the window is key, stops for good at 60 s; Reduce Motion skips the entrance | 309-349 |

- **Signature interactions that feel great** (INFERENCE): the command panel that grows from the address field
  with no scrim; favicon-tinted selection; interruptible hover cards; a sidebar that springs rather than slides;
  the PiP throw. Dia's spring math is the standard response and damping-ratio form (stiffness (2π/response)²,
  damping 4πζ/response), so it ports directly to Chromium's or Core Animation's springs (FACT for the formula,
  `A:docs/dia-spec.md:204-206`).
- **Things that feel bad** (INFERENCE from changelogs): constant AI surface area (Brief chimes once took over
  headphones, fixed 1.53); a "Liquid Glass" redesign tied to macOS 26 (1.15); Memory shipped, then deleted.

### Comet

- Chromium's own UI with Perplexity's search as home; the assistant is a web app ("Sidecar", `/sidecar`)
  served from perplexity.ai in the right panel (FACT, [Zenity][zenity-comet]).
- During agent runs an `overlay.js` from the hidden agent extension draws on the page; HUMAN Security notes
  this leaves DOM traces, unlike Atlas (CLAIM, [HUMAN][human-atlas-comet] as summarized in search).
- Feels bad: one reviewer measured 84 % task success on text-heavy sites but 42 % on dynamic single-page apps
  with modals or Cloudflare checks (CLAIM, [Tabbit review][tabbit-comet]).

### ChatGPT Atlas (retired)

- Built "almost entirely in SwiftUI and AppKit", with Metal for "rich animations and visual effects for
  features like Agent mode" (FACT, [OWL post][oa-owl]). New tab is the ChatGPT composer; "Ask ChatGPT" is a
  right sidebar; "cursor chat" pops a bubble on selected text (FACT, [OpenAI help][oa-help-sidebar]).
- Vertical tabs with a "mini mode" and hover-to-reveal arrived in late 2025 (FACT, [Releasebot][atlas-rb]).
- Feels bad: reviewers saw the sidebar hang on summaries (CLAIM, [Cybernews][cybernews-atlas]); the
  agent-mode "may introduce risk" dialog offers logged-in or logged-out, and Zenity found that the first pick
  silently becomes the default for later runs (FACT, [Zenity on Atlas][zenity-atlas]).

### Yab

- Native AppKit and SwiftUI over WebKit. "Arc-sized rows" (0.19), spaces at the bottom of the column, glass
  in "Look", Arc-style icon picker, Arc's address menu (FACT, [changelog][yab-cl]).
- Approval cards sit "at the page or in the chat"; ⌘↩ approves a press, upload, message or Mac access; ↩
  approves tab use, sign-in, or an address fill; esc is "Not now"; holding ⌥ turns "Not now" into "Never here"
  (FACT, [Yab permissions][yab-perms]). Splitting the strong key (⌘↩) from the weak key (↩) is a good
  pattern (INFERENCE).
- Agent tabs live "in a window off screen" until you ask to see them (FACT, `Y:README.md:5`).
- Feels bad: WebKit means "a site tested only in Chrome can misbehave", in Yab's own words (FACT,
  [Yab compare page][yab-vs-chrome]); daily releases mean daily churn (INFERENCE from [changelog][yab-cl]).

### Opera Neon

- Tasks as workspaces with their own AI context; Cards styled like game cards that stack onto a prompt
  (FACT, [TechCrunch][tc-neon]). Do runs "locally, visibly, and in real-time. You can pause, guide, or take
  control at any moment" (CLAIM, [Opera press release][opera-neon-ship]).
- An MCP logo at the top right opens "Allow AI connection" with presets for Claude Code and others (FACT,
  [Opera MCP post][opera-mcp]).

### Chrome with Gemini

- The tab the agent works in glows; the side panel lists each step ("work log"); "Take over task" button
  (FACT, [9to5Google][9to5g-autobrowse], [Google security][g-sec]).

### Edge with Copilot

- "The tab where Copilot is working shows a cursor icon in the tab menu"; steps show in real time (FACT,
  [Microsoft support][ms-browse]). An optional animated avatar, Mico (FACT, [MacRumors][mr-edge]).

## Architecture

| | Process model | How it uses the engine | UI technology | Languages | Notes |
|---|---|---|---|---|---|
| Arc | Chromium in-process framework (INFERENCE) | Own Chromium build wrapped by "ADK, the Arc Development Kit … an internal SDK for building browsers … lets ex-iOS engineers prototype native browser UI quickly, without touching C++" (FACT, [letter][tbc-letter]) | SwiftUI and TCA (The Composable Architecture) on macOS; Swift on Windows via their Swift/WinRT bindings (FACT, [letter][tbc-letter] summary in [Gigazine][gigazine-letter]) | Swift, C++ | Firebase for auth, Notes and Easels storage, Boost sync, referral codes (FACT, [arc.net/security][arc-security]) |
| Dia | Same ADK base; the Chromium framework is called **ArcCore** (Dia 1.43.1: "arm64-only ArcCore" cut 265 MB) (FACT, [changelog][dia-cl]) | Same as Arc | AppKit-heavy: "sunsetting our use of TCA and SwiftUI to make Dia lightweight" (FACT, [letter][tbc-letter]); Core Animation springs and the `Motion` library (FACT, `A:docs/dia-spec.md:915-925`) | Swift, C++ | Page reading for AI moved out of process "for security" (1.34.1); agent context handling separated from execution (1.49) (FACT, [changelog][dia-cl]) |
| Comet | Chromium fork. The model and planner run on Perplexity's servers. Execution is three hidden built-in extensions: `comet-agent` (`agents.crx`, a ~700 KB service worker with an RPC dispatcher), `perplexity.crx` (tabs, side panels, split view, history access, Sentry), and a web-resources extension. They update from Perplexity's server (`/rest/browser/update-crx`), outside browser releases (FACT, [Zenity][zenity-comet]) | Agent reads pages through `chrome.debugger` (`Accessibility.getFullAXTree`, returned as YAML with `ref_N` ids) and acts via CDP (Chrome DevTools Protocol) input (FACT, [Zenity][zenity-comet]) | Chromium Views plus a web Sidecar from perplexity.ai | C++, TypeScript | Chat on an SSE stream; actions on a WebSocket RPC channel opened per task (FACT, [Zenity][zenity-comet]) |
| Atlas | **OWL**: Chromium's browser process runs outside the app process as the "OWL Host"; the Swift app is the "OWL Client". They talk over Mojo with custom Swift and TypeScript bindings (FACT, [OWL post][oa-owl]) | Pixels cross the boundary as a `CALayer` context ID embedded with the private `CALayerHost` API; the client translates `NSEvent` into Blink `WebInputEvent` itself; unhandled events come back and are re-synthesized (FACT) | SwiftUI, AppKit, Metal | Swift, C++ | "OWL ships internally as a prebuilt binary, so Atlas builds take minutes not hours"; Chromium hangs or crashes don't take the app down; startup paints before Chromium boots (FACT/CLAIM, [OWL post][oa-owl]) |
| Yab | One app process using system WebKit (`WKWebView`) (INFERENCE from "runs on the WebKit already inside your Mac", [Yab][yab-home]) | WebKit is the OS's; Yab cannot patch it and needs macOS 15.4+ (FACT, `R:plans/context/competitors-ardia-yab-2026-10-23.md`) | AppKit and SwiftUI (FACT, same context file) | Swift | Chrome extensions through Apple's API plus a 306 KB JavaScript shim for about 25 missing `chrome.*` areas (FACT per the context file); the agent is Claude Code or Codex run as child processes on the user's plan (FACT, [Yab connect][yab-connect]) |
| Opera Neon | Chromium (Opera's) | Do runs in the browser; Make runs "in a cloud-based virtual machine that works independently" (FACT, [InfoQ][infoq-neon]) | Opera's UI | C++, JS | MCP Connector goes through an Opera-run persistent proxy; the CLI is a local CDP client on port 9224 (FACT, [Opera MCP][opera-mcp], [Opera CLI][opera-cli]) |
| Chrome | Gemini in Chrome is "glic"; its agent is the **actor** framework: `GlicActorTaskManager` → `ActorKeyedService` (one per profile) → `ActorTask` → `ExecutionEngine` → `ToolController` → `Tool` (FACT, `C:chrome/browser/actor/README.md:1-60`) | Model in Google's cloud; actions run locally in the renderer (FACT, [9to5Google][9to5g-autobrowse]) | Chromium Views plus WebUI | C++, TypeScript | Origin gating is a separate component, `components/origin_gating` (events: navigation request, navigation response, page action; decision sources include same-origin, user-confirmed cache, enterprise policy, HTTPS-only, no raw IPs) (FACT, `C:components/origin_gating/core/types.h:33-79`). A remote-updated block list gates actions per URL (`GLIC_ACTION_PAGE_BLOCK` via Optimization Guide) (FACT, `C:chrome/browser/actor/site_policy.cc:39-78`) |
| Edge | Chromium; Copilot in a sidebar | "All actions run locally in your browser"; screenshots of the tabs Copilot works on go to the service (FACT, [Microsoft support][ms-browse]) | Edge's UI | C++, TS | Curated allow list of sites for Browse with Copilot (CLAIM, forum summary in [search][edge-allowlist]) |

What matters for rac (INFERENCE):

- **Two closed teams escaped Chromium's UI by moving away from Views.** TBC wrapped Chromium in ADK and wrote
  native UI; OpenAI went further and moved Chromium out of process. Both say the motive was UI freedom and a
  smaller upstream diff. rac's ~871 hunks in 217 upstream files (`R:plans/context/maintainer-brief.md:77-78`)
  are the cost those teams avoided. OWL is the cleanest public design for a "separate shell" option if rac
  ever leaves Views. It is also months of work for a team that had Chromium's original lead (Ben Goodger).
- **Comet ships agent code as hidden extensions that update from its server.** That lets agent fixes ship
  without a browser release. It also hid a powerful API from users, which is what SquareX attacked.
- **Chrome's agent framework is already in rac's tree.** rac uses the actor tools but not Glic's execution
  engine (`R:docs/internals/ai.md:388-405`). The origin-gating component and the WebMCP receiver are there too.

## Data and storage

| | Stored where, in what format | Encryption and keys | Sync | Servers | Telemetry | What leaves the machine |
|---|---|---|---|---|---|---|
| Arc | Chromium profile in `~/Library/Application Support/Arc/User Data`; sidebar (spaces, pinned, favorites, folders, themes) in `~/Library/Application Support/Arc/StorableSidebar.json` with `sidebar.containers[].spaces/items` and `topAppsContainerIDs` (FACT, `A:packages/import/ios/Core/Discovery.swift:67,299`, `A:packages/import/ios/Core/ArcSidebar.swift:7-57`) | Chromium's "Arc Safe Storage" keychain key (FACT, `Discovery.swift:67`) | Arc Sync, described as encrypted (CLAIM, [notes][arc-rn]) | Firebase: auth, Notes, Easels, Boosts (FACT, [arc.net/security][arc-security]) | Internal-action and crash telemetry; Arc says it doesn't log URLs or page content (CLAIM, [arc.net/security][arc-security]); third-party test saw Segment, Sentry, LaunchDarkly and no opt-out (CLAIM, [Kostarelas][arc-privacy-blog]) | Account data; Boosts to Firebase; Arc Max prompts to model vendors (INFERENCE) |
| Dia | Chromium profile in `Dia/User Data`; sidebar in an SQLCipher `tabs.db` (FACT, `A:packages/import/README.md:28`); "conversations, history, bookmarks, and files are encrypted and stored locally" (CLAIM, [Dia security][dia-security]) | Sync: per-device random 256-bit seed; HKDF-SHA256 derives an AES-256-GCM key and an Ed25519 key pair; 24-word BIP39 recovery phrase; new devices pair with SPAKE and a 6-character code, 3 wrong tries rotate it (FACT, [bulletins][dia-bulletins]) | End-to-end; "The server stores ciphertext it cannot decrypt"; outside review before launch (CLAIM, [bulletins][dia-bulletins]) | Chat goes "through our servers" to OpenAI (Azure), Anthropic (direct, Vertex, AWS), Gemini (Vertex), contractually barred from training (CLAIM, [Dia security][dia-security]) | **Content data for improvement on by default**, kept 30 days, not tied to the account, opt-out in Settings; may train small on-device models (FACT, [Dia security][dia-security]) | Prompts and relevant page content; Morning Brief sends data on its own schedule (FACT) |
| Comet | "By default, all Comet data is stored on your device only"; passwords and cards in the OS vault (CLAIM, [Comet privacy FAQ][comet-faq]) | OS keychain | Planned opt-in cloud sync (CLAIM); desktop↔iOS thread and history sync shipped (FACT, [MacRumors][mr-comet-ios]) | Perplexity runs the agent loop (FACT, [Zenity][zenity-comet]) | Sentry from a built-in extension (FACT, [Zenity][zenity-comet]); sensitive queries deleted after 30 days (CLAIM, [AlternativeTo][alt-comet]) | Current tab and relevant history when the assistant needs them; terms allow use "to provide and improve Comet and recommend relevant content" (FACT, [Proton][proton-comet]) |
| Atlas | Browser memories tied to the ChatGPT account (FACT, [launch post][oa-intro]) | n/a | ChatGPT account | OpenAI | n/a | Pages you attach; browsing not used for training unless you opt in to "include web browsing" (FACT, [launch post][oa-intro]) |
| Yab | Tabs, history, passwords, mail on the Mac; passwords, cards, addresses in the macOS keychain; agent memory as plain Markdown files (FACT, `Y:README.md:280-282`, [Yab memory][yab-memory]) | Sync key made on the first device, "never reaches our server"; moved by iCloud Keychain, a typed code, or a recovery key; passwords and cards encrypted twice (FACT, [Yab privacy][yab-privacy]) | Off by default; Cloudflare-hosted server sees record counts, sizes, times, device names, models and IP addresses (FACT) | Vercel and Neon hold daily-activity, crash, feedback and read-status data; remote assistants relay through a Cloudflare Worker (FACT, [privacy][yab-privacy], `Y:README.md:38`) | **Daily active installation ID plus a cross-device ID, on by default, opt-out** (FACT, [privacy][yab-privacy]) | Pages the agent reads go to Anthropic or OpenAI under the user's account; short memory notes go with every task (FACT, [Yab memory][yab-memory]) |
| Opera Neon | Credentials and payment details stay in the browser session (CLAIM, FAQ via [search][neon-faq]) | n/a | n/a | Chat and most research run in the cloud; Make runs in a cloud VM; the MCP proxy is Opera's (FACT) | n/a | MCP clients get tabs, page content and screenshots by default (FACT, [Opera MCP][opera-mcp]) |
| Chrome | Google account | Google | Chrome Sync | Gemini in Google's cloud | Chrome's usual | Pages Gemini reads; Personal Intelligence pulls Gmail, Calendar, Drive, Photos when the user connects them (FACT, [9to5Google][9to5g-pi]) |
| Edge | Microsoft account | Microsoft | Edge Sync | Copilot service | Microsoft's usual | **Screenshots kept up to 30 days** with the conversation, never used for training; deleting the chat deletes them (FACT, [Microsoft support][ms-browse]) |

Two lessons (INFERENCE): every vendor with sync ended up at the same design (a device-made key the server never
sees), so rac can copy it without inventing one. And every vendor except Yab routes AI traffic through its own
servers, while Yab and rac route it straight to the user's provider. That is a real, rare trust advantage.

## Agents and AI

### How each agent works

"Agent" here means the AI clicks, types, or navigates in the browser. Arc has none, so it is left out.

| | Where it runs | How it sees the page | Models; local models | Who says yes, and when | Data the agent is denied |
|---|---|---|---|---|---|
| **Dia** | TBC servers to OpenAI, Anthropic, Google; small on-device models route the command bar and name groups (FACT, [Dia security][dia-security], [changelog][dia-cl]) | Page text read out of process (1.34.1); "the assistant only sees what you saw and approved" (FACT) | GPT-5 for all queries as of 0.48, 2025-09 (FACT, [changelog][dia-cl]); current models not stated; thinking depth scales with difficulty (1.53) | "Dia's chat session starts with no access to other tabs or ability to take write actions." Inserting data into third-party sites needs approval, shown "in a Dia-controlled view"; calendar events stay drafts until the user clicks Create (FACT, [Dia security][dia-security]) | "Web form fields like passwords and irreversible action buttons are invisible to the agentic system" (FACT) |
| **Comet** | Planner on Perplexity servers; execution in the hidden `comet-agent` extension (FACT, [Zenity][zenity-comet]) | Accessibility tree as YAML with `ref_N` ids for interactable elements; HTML→markdown; screenshots with pixel actions (`ComputerBatch`) (FACT, [Zenity][zenity-comet]) | Perplexity's choice; none local | Confirmation "regardless of whether our systems detect suspicious activity" for sending email or messages, calendar changes, final orders, and entering user details the agent doesn't already have (FACT, [Perplexity][pplx-4layers]). Per-site "Block tasks on specific websites" (FACT, [Comet help][comet-help]) | "Comet never has access to your passwords or payment data" (CLAIM, [Comet help][comet-help]); hard blocks on `chrome://`, `comet://`, `file://`, admin list (FACT, [Zenity][zenity-comet]) |
| **Atlas** (retired) | OpenAI cloud; agent input routed "directly to the renderer, never through the privileged browser layer" (FACT, [OWL post][oa-owl]) | One screenshot per step for a computer-use model, with `<select>` popups composited back in (FACT, [OWL post][oa-owl]) | OpenAI; none local | "Will pause to ensure you're watching it take actions on specific sensitive sites such as financial institutions" ("Watch Mode"; Simon Willison could not trigger it on GitHub or his bank) (FACT, [launch post][oa-intro], [Willison][sw-atlas-ciso]) | Cannot run code, download files, install extensions, reach other apps or files, read or write ChatGPT memories, use saved passwords or autofill; agent pages stay out of history (FACT, [launch post][oa-intro], [Atlas notes][atlas-rb]) |
| **Yab** | Claude Code, Codex, and since 0.36 Gemini and Cursor, run locally on the user's plan (FACT, [Yab connect][yab-connect], [changelog][yab-cl]) | `snapshot` (accessibility tree with ref ids), `text`, `screenshot`; `run` and `eval` execute JavaScript in an isolated world (FACT, `Y:README.md:189-268`) | Vendor CLIs' models; no local LLM | **Three modes**: Ask (asks before using your tabs or Mac, signing in, and anything that sends, pays, deletes or uploads), **Auto** ("Auto, to start with": asks only for Mac access and send, pay, delete, upload), Bypass (asks never; captchas and passkeys stay with you). Pay-without-asking at $20, $50 or $100, capped at ten times that a month. "Always here" and ⌥ "Never here" per site (FACT, [Yab permissions][yab-perms]) | Passwords filled by Yab and never shown; card numbers after Touch ID; "Private tabs don't exist for agents"; "A task that has read your mail asks you before it sends any of mail's words to a site you haven't visited" (FACT, [Yab permissions][yab-perms], [privacy][yab-privacy]) |
| **Opera Neon** | Do in the browser with cloud models; Make in a cloud VM (FACT, [InfoQ][infoq-neon]) | n/a (Do); outside agents get Chromium's accessibility snapshot via CDP (FACT, `O:README.md`) | GPT-5.5, Opus, Gemini 3 and others on the paid plan (CLAIM, [ToolChase][neon-toolchase]) | "You can pause, guide, or take control at any moment" (CLAIM). Outside MCP clients: read tools on, **write tools off until the user enables them** (FACT, [Opera MCP][opera-mcp]) | Credentials stay in the browser (CLAIM) |
| **Chrome** | Gemini in Google's cloud; actions on device (FACT, [9to5Google][9to5g-autobrowse]) | Page content (Chromium's annotated page content) (INFERENCE from `C:third_party/blink/renderer/modules/content_extraction/ai_page_content_agent.cc`) | Gemini 3; none local for the agent | Confirms (1) visiting sensitive sites such as banking or medical, by a deterministic list; (2) signing in with Password Manager, "the model does not have direct access to stored passwords"; (3) purchases, payments, messages and other consequential actions (FACT, [Google security][g-sec]) | Origins outside the task: Agent Origin Sets split read-only from read-write origins, and "readable data can only be passed on to the writable origins"; shipped first as a simpler write-set-only version (FACT, [Google security][g-sec]) |
| **Edge** | Copilot service; "All actions run locally in your browser" (FACT, [Microsoft support][ms-browse]) | Screenshots of the tabs it works on, plus page context (FACT) | Microsoft's; none local | **Light / Balanced (default) / Strict**: Strict always asks per site; Balanced acts on popular sites and asks on unfamiliar ones; Light asks least. Prompts offer **Always allow / Allow once / Cancel**; allow and block lists (CLAIM, guides: [ElevenForum][eleven-edge], [Windows Central][wc-edge]). Asks before buying, booking, sending email, deleting events; asks you to watch or take over on banking or email sites (FACT, [Microsoft support][ms-browse]) | No autofill, passwords or wallet; site permissions (camera, microphone, location) "temporarily suspended" while it acts (FACT, [Microsoft support][ms-browse]) |
| **rac today** | rac's controller; direct providers, local models (Ollama, LM Studio), or ACP agents (FACT, `R:docs/internals/ai.md:49-91,193-306`) | Accessibility-style lines with `eN` refs, published vs private snapshots (FACT, `R:docs/internals/ai.md:367-386`) | Any; local supported | `ask` / `careful` / `auto` (default) plus per-site always/never; risky list always asks (FACT, `R:docs/internals/ai.md:436-444`) | Passwords and payment values redacted; non-http(s) URLs and URLs not from a user message or a shown link are blocked (FACT, `R:docs/internals/ai.md:416-421`) |

Outside agents, skills, automations, memory:

| | Outside agents can drive it | Skills (saved prompts) | Automations | Memory |
|---|---|---|---|---|
| Dia | No (AppleScript and Raycast only) | Skills, `/name`, gallery, can call other skills | Morning Brief | **Retired 2026-09-24**; replaced by on-demand search of chats, history, artifacts |
| Comet | No public door; a hidden MCP API was disabled | Shortcuts (`/tldr`…) | Background Assistants (Max) | Unclear; Discover feed personalizes |
| Atlas | No | Saved Prompts (2026-02) | No | Browser memories, opt-in; gone with the app |
| Yab | **Yes**: local MCP (stdio to a user-only socket), `yab` CLI, plugins for Claude Code and Codex, remote assistants through a Cloudflare relay | Site "skills" for agents (Gmail, GitHub, LinkedIn, Amazon) | Routines on any schedule; `watch` a thread every two hours | Markdown notes on the Mac, editable, with an off switch; short notes sent with every task |
| Opera Neon | **Yes**: MCP Connector through Opera's proxy (needs an Opera account), local CLI over CDP; **free** without Neon's own AI | Cards | Scheduled tasks (paid) | "Long memory" (paid; CLAIM) |
| Chrome | WebMCP lets *sites* offer tools to agents; DevTools MCP can attach after a consent dialog (developer path) | Skills, 50+ presets | No | Personal Intelligence, opt-in |
| Edge | No | No | No | History personalization and past chats "with your permission"; Journeys |

Sources for this table are in the rows above and in [Features](#features).

### Publicly reported incidents

Listed oldest first. "Fix" is what the vendor changed, if known. Exploit detail is deliberately thin.

| When | Product | Reported by | What went wrong (plain terms) | Fix or response |
|---|---|---|---|---|
| 2024-08 (CVE-2024-45489, CVSS 9.8) | Arc Boosts | Researcher "xyz3va" | A misconfigured cloud database rule let anyone attach a JavaScript Boost to another user's account, and that code ran in the victim's browser. User IDs leaked through referrals and shared Boosts and Easels | Fixed server-side within a day; JavaScript Boosts stopped auto-enabling across devices and were all switched off until re-enabled per device; a global Boosts switch; a bug bounty; a plan to move off Firebase (FACT, [Tenable][tenable-arc], [Arc notes][arc-rn]) |
| 2025-08-20 | Comet | Brave | Hidden text in a Reddit comment led "summarize this page" to read the user's email address and a one-time code from Gmail and post them publicly (FACT, [Brave][brave-comet]) | Several fix-and-retest rounds before disclosure (CLAIM, [Decryption Digest][dd-comet]); later the four-layer design below |
| 2025-08-20 | Comet | Guardio ("Scamlexity") | The agent bought from a fake shop and sometimes autofilled a saved card without asking; clicked through a phishing mail; obeyed hidden text in a fake CAPTCHA (FACT, [The Hacker News][thn-promptfix]) | Not stated |
| 2025-08 to 10 ("CometJacking") | Comet | LayerX | Instructions in a link's query string made the assistant pull mail and calendar data and send it out in encoded form, past checks for plain-text leaks (FACT, [BleepingComputer][bc-cometjack]) | Perplexity first said "no security impact", later said it patched it (FACT, [TIME][time-comet]) |
| 2025-10-21 | Comet, Fellou | Brave | Faint text inside a user's screenshot was read by text recognition and treated as the user's request (FACT, [Brave][brave-screens]) | Not stated |
| 2025-10-14 to 21 | Opera Neon | Brave | Invisible HTML made the assistant fetch the user's account details from another Opera site and send them to the attacker's page (FACT, [Brave][brave-neon]) | Fixed within a week; Opera first closed the report as "Not Applicable", then reversed (FACT, [Opera][opera-neon-pi]) |
| 2025-10 | Atlas | NeuralTrust | Text that looked like a web address, but wasn't one, was treated in the address bar as a trusted instruction (FACT, [The Hacker News][thn-atlas]) | Not stated |
| 2025-10 ("Tainted Memories") | Atlas / ChatGPT | LayerX | A malicious page could write hidden instructions into ChatGPT's memory through the user's logged-in session; they persisted across devices. LayerX also measured Atlas blocking 5.8 % of 103 phishing attacks, against Chrome 47 % and Edge 53 % (CLAIM, [The Hacker News][thn-atlas]) | Not stated |
| 2025-11-19 | Comet | SquareX | A hidden built-in extension API could start local programs if Perplexity's site or the extension were ever compromised (FACT, [SecurityWeek][sw-squarex]) | API disabled in a silent update; Perplexity called the report "entirely false" (FACT) |
| 2025-11 ("HashJack") | Comet, Copilot in Edge, Gemini in Chrome | Cato Networks | Instructions placed after `#` in a real site's link never reach the server but do reach the assistant (FACT, [Help Net][hn-hashjack]) | Not stated in coverage |
| 2025-12-01 | All "AI browsers" | Gartner | "CISOs must block all AI browsers in the foreseeable future" (FACT, [The Register][reg-gartner]) | n/a |
| 2025-12-22 | Atlas | OpenAI itself | An in-house attacker trained with reinforcement learning found attacks over "tens (or even hundreds) of steps", e.g. a planted email that made the agent send a resignation letter (FACT, [CyberScoop][cs-atlas]) | A newly adversarially trained agent model; "prompt injection … may never be fully solved" (FACT) |
| 2026-01 | BrowseSafe (Comet's detector) | Lasso Security | 36 % of attacks got past the detector using standard encodings (CLAIM, [Lasso][lasso-browsesafe]) | n/a |
| 2026-02-12 | Dia | TBC's own team | The web-fetch tool could leak secrets by fetching a URL the model built; months of detection-based fixes were all bypassed in-house (FACT, [Dia bulletins][dia-bulletins]) | Pulled before the June 2025 beta; rebuilt with **URL provenance** (below) |
| 2026-07-14 (CVE-2026-48561, CVSS 9.6) | Copilot in Edge for Android and iOS | Microsoft | A web page could make Edge send prompts to Copilot "without confirmation or origin validation" (FACT, [Action1][action1-cve]) | Patched in July Patch Tuesday; not seen exploited (FACT) |

UI-spoofing CVEs also hit Dia (a custom window that hid `about:blank`, CVE-2025-15032; fullscreen without the
toast, CVE-2025-13132) (FACT, [Dia bulletins][dia-bulletins]). These are classic browser bugs that a
custom shell reintroduces. rac keeps Chromium's own prompts, so it inherits Chromium's fixes (INFERENCE).

### Defenses the vendors adopted, from strongest to weakest

Strength here means "still works when the model is fooled" (INFERENCE, consistent with the "lethal trifecta"
framing: private data plus untrusted content plus a way to send data out, [Willison][sw-trifecta]; and with
design-pattern work such as CaMeL, [arXiv 2503.18813][camel], and [Beurer-Kellner et al.][design-patterns]).

1. **Architectural data-flow limits** (deterministic):
   - **Dia's URL provenance.** A URL is fetchable only if it came from something the user provided or
     viewed: links clicked or pasted, links on pages the user is viewing, links in mail or chats shared
     with Dia. A shared URL with an added query parameter is rejected "because that full URL was never in
     the user's context" (FACT, [Dia bulletins][dia-bulletins]).
   - **Chrome's Agent Origin Sets.** A trusted gating function, shielded from page content, decides which
     origins the task may read and which it may act on. Readable data may flow only to writable origins.
     The planner "cannot add new origins without the gating function's approval". Model-generated URLs are
     limited by "a deterministic check … to known, public URLs" (FACT, [Google security][g-sec]).
   - **Atlas's logged-out mode.** Each agent session gets a fresh in-memory storage partition, discarded at
     the end (FACT, [OWL post][oa-owl]). Brave does the same with a separate built-in profile (FACT,
     [Brave][brave-ai-browsing]).
   - **Hiding dangerous targets from the agent.** Dia makes password fields and irreversible buttons
     invisible to the agentic system (FACT, [Dia security][dia-security]).
2. **Confirmation held by the browser, not the model** (deterministic trigger, human decision): Yab's "the
   browser holds that yes, not the model" (FACT, `Y:README.md:5`); Comet's confirmation regardless of
   detection; Chrome's three confirmation categories; Edge's sensitive actions. Yab adds money thresholds and
   a monthly cap. Dia shows the exact content in a browser-owned view before it goes into a site.
3. **A second model that never sees the page**: Chrome's User Alignment Critic sees "only metadata about the
   proposed action" and can only approve or reject (FACT, [Google security][g-sec]); Brave's alignment
   checker likewise has no access to the site (FACT, [Brave][brave-ai-browsing]). rac's `careful` critic is the
   same idea (`R:docs/internals/ai.md:546-561`).
4. **Detection classifiers** run in parallel with the planner: Comet's BrowseSafe (fine-tuned
   Qwen3-30B-A3B, MIT, F1 up to 0.904 on its own benchmark, 36 % bypass in Lasso's test) and Chrome's
   classifier (FACT, [arXiv][browsesafe-paper], [HF][hf-browsesafe]; CLAIM for the bypass). Dia's team said
   every detector they built was bypassed in-house (FACT, [Dia bulletins][dia-bulletins]).
5. **Prompt-level marking** of untrusted content ("spotlighting", structured prompts) (FACT,
   [Google security][g-sec], [Perplexity][pplx-4layers]). TBC's AI lead: "While this can help, there are no
   guarantees" (CLAIM, talk notes via [AI Engineer][aie-samir]).
6. **Adversarial training and red teaming**: OpenAI's RL attacker; Google's generated malicious sandbox
   sites; Perplexity's Trail of Bits audit; bounties (Google pays up to $20,000 for agent boundary breaks)
   (FACT, [CyberScoop][cs-atlas], [Google security][g-sec], [Perplexity][pplx-dayone]).

Public benchmarks rac can use offline: **BrowseSafe-Bench** (14,719 examples, 11 attack types, MIT,
[HF][hf-browsesafe-bench]; FACT, [Perplexity][pplx-dayone]) and **WASP** (82 sandboxed tasks; attacks
"partially succeed in up to 86% of the case" but rarely complete the attacker's goal, [arXiv
2504.18575][wasp]) (FACT).

### Where rac's known gap sits against these

rac at `auto` lets the agent navigate to a site the user didn't name (if the link was shown to the model)
and type model-written text into a named site with no card (FACT, `R:docs/internals/ai.md:436-444`;
`R:plans/context/maintainer-brief.md:64-67`). Compared with the field (INFERENCE):

- rac already has Dia-style provenance for URLs (exact match to a user message or a shown link). That beats
  Comet, Atlas, and Edge.
- rac has no **data-flow** rule. Chrome's rule ("readable data only flows to writable origins") and Yab's
  mail rule ("asks before it sends any of mail's words to a site you haven't visited") are what would stop
  "read private text on site A, type it into a field on site B". Typing alone can leak, because pages see
  keystrokes before any submit.
- rac has no isolated agent context. Atlas and Brave do.
- rac's `auto` is close to Yab's default `Auto` and stricter than Yab's `Bypass`. Edge's default `Balanced`
  is stricter than both: it asks before acting on unfamiliar sites.

## Build, release, and engineering

Closed products publish little about build systems. What is public:

- **Arc** keeps shipping weekly Chromium-only releases in maintenance mode: 1.160.0 (2026-08-13) through
  1.169.0 (2026-10-15), Chromium 151 → 155.0.8059.80. On 2026-10-01 Arc 1.167.0 moved to Chromium
  154.0.8037.93, one patch above rac's 154.0.8037.92; two weeks later it was on 155 (FACT,
  [Arc release notes][arc-rn]; rac version from `R:plans/context/maintainer-brief.md:75-76`). An "Early Birds"
  pre-release group tests builds (FACT, [notes][arc-rn]). Arc Max can be disabled by enterprise policy
  (`arcMaxDisabledByOrgPolicy`) (FACT). Bug bounty since the 2024 CVE (FACT, [Tenable][tenable-arc]).
- **Dia** ships weekly and tracks Chromium closely: M141 in October 2025, M156 in October 2026, 15 majors in a
  year; one release notes "Chromium 149, patching 429 vulnerabilities" (FACT, [changelog][dia-cl]).
  Connected-app tools refresh "without requiring an app update", so some AI behaviour is server-configured
  (FACT, [changelog][dia-cl], Windows 1.2.0). Public security bulletin with CVEs, a HackerOne programme, and an
  outside review of Sync before launch (FACT, [bulletins][dia-bulletins], [Dia security][dia-security]).
  Dev builds carry a built-in prompt editor so non-engineers can test prompts against daily work (CLAIM,
  [AI Engineer talk notes][aie-samir]).
- **Comet** ships its agent as built-in extensions that update from Perplexity's server, separate from browser
  updates (FACT, [Zenity][zenity-comet]). Trail of Bits threat-modelled it before launch; a private bug bounty
  and disclosure programme exist (FACT, [Perplexity][pplx-dayone]).
- **Atlas** shipped OWL "internally as a prebuilt binary, so Atlas builds take minutes not hours"; "Every new
  engineer makes and merges a small change in the afternoon of their first day" (FACT, [OWL post][oa-owl]).
  Build numbers look weekly (`1.2025.316.6`, `1.2026.15.3`, `1.2026.28.6`, `1.2026.42.5`) (FACT,
  [Releasebot][atlas-rb]). After shutdown it "would stop getting the ongoing security maintenance" (FACT,
  [9to5Mac][9to5-atlas-end]).
- **Yab** ships several releases a day at times (three on 2026-10-03, three on 2026-10-07) and updates "while
  closed" (0.31) from its own server (FACT, [changelog][yab-cl], [privacy][yab-privacy]). Its boost Store
  re-checks every listing daily on the live site and marks a boost "Needs Fix" after two failing days (FACT,
  [Yab store][yab-store]). The open `yab-mcp` repo has a script that snapshots the app's real `tools/list`
  into the README, so docs can't drift from the app (FACT, `Y:README.md:294-303`).
- **Opera**'s `opera-browser-cli` repo uses release-please, keeps a `CLAUDE.md` for AI coding agents, and carry token
  benchmarks for page snapshots (`benchmarks/page-token-benchmark`, `snapshot-agentic-use`) (FACT,
  `/tmp/rac-overhaul/src/opera-browser-cli/{CLAUDE.md,benchmarks/}`).
- **Chrome** tracks agent attack success rates from automated red teaming as a regression signal across
  releases (FACT, [Google security][g-sec]).

INFERENCE for rac: a one-person Arc-style project in maintenance mode (Arc) stays within two weeks of
Chromium stable. rac has never synced. Shipping weekly security bumps is table stakes for an Arc refugee who
is trusting rac with signed-in sessions.

## Strengths and weaknesses (critical)

**Arc.** Strengths: the reference set of daily habits (Peek, Little Arc, Archive, Clear, Air Traffic
Control, ⌘T actions, Supercopy, Split as a unit); real motion craft; weekly security updates even now.
Weaknesses: the company's own data shows most features went unused (5.52 % used several spaces, 4.17 %
Live Folders, 0.4 % Calendar Preview); a mandatory account; a cloud backend that turned a customization
feature into a critical remote-code bug; bloat by its makers' admission; it dies on 2026-12-22.

**Dia.** Strengths: the most rigorous public security writing of any vendor (provenance over detection,
assume injection, drafts not actions, dangerous fields hidden from the agent); serious end-to-end sync;
weekly cadence; measured motion polish. Weaknesses: every chat goes through TBC's servers; content data for
improvement is on by default; the product changes direction often (Memory shipped and was deleted; spaces
became profiles); no outside-agent door; Arc users lose spaces as spaces.

**Comet.** Strengths: the most capable consumer agent with background tasks; detection research released as
open models and data; a clear four-layer write-up. Weaknesses: the most public incidents of any product here
(Brave ×2, Guardio, LayerX, SquareX, HashJack); dismissive first responses to two reports; hidden privileged
extensions; an ad-funded data posture stated by its CEO; agent success rates reported as low on dynamic sites.

**ChatGPT Atlas.** Strengths: the best public architecture write-up (OWL); sensible agent limits (no code,
no downloads, no file system, logged-out mode). Weaknesses: shut down after 292 days with a manual export;
early injection bugs in the omnibox and memory; Watch Mode didn't trigger in a public test. Lesson: an AI
company's browser is a product experiment that can vanish; that is a pitch for rac.

**Yab.** Strengths: the clearest permission UX in the market (Ask/Auto/Bypass, money thresholds, per-site
Always/Never, strong and weak approval keys, "the browser holds the yes"); a local MCP server and CLI done
well; no AI middleman; astonishing shipping pace. Weaknesses: WebKit compatibility and a JavaScript shim for
Chrome extensions; daily-active IDs on by default; several cloud services (Cloudflare, Vercel, Neon) and a
relay for remote assistants; breadth (mail, Messages, "Get to Know Me" crawls) that widens the attack surface;
closed source and a side project by its maker's description.

**Opera Neon.** Strengths: read-only-by-default MCP with writes off until enabled; a free bring-your-own-agent
tier, which answers the "let me use my own agent" demand directly; open CLI and MCP repos. Weaknesses: a cloud
proxy in the MCP path; a cloud VM for Make; an Opera account for MCP; one public injection bug at launch that
Opera first dismissed.

**Chrome with Gemini.** Strengths: the deepest published security architecture (origin sets, metadata-only
critic, deterministic URL checks, three confirmation classes, $20,000 bounties), and it lands in open
Chromium code rac already carries. Weaknesses: paid and US-only for the agent; tied to a Google account and
cloud model; the strongest part (read-only origins) shipped in simplified form first.

**Edge with Copilot.** Strengths: understandable three-level site trust (Light/Balanced/Strict) with Allow
once / Always allow; site permissions suspended while the agent acts. Weaknesses: Copilot Mode was retired
after ten months; the agent is behind a Microsoft 365 Premium paywall; screenshots stored up to 30 days; a
critical Copilot prompt bug on mobile in 2026.

## What rac should take (ranked, concrete, with rough cost) and what rac should avoid

### In plain English

Arc users must move within eight weeks. Few of them used several spaces. So first build the Arc habits that
need no setup. Those are link previews, the small window for outside links, tab clean-up, and the command bar.
Import their Arc sidebar as it was. Then fix one real hole in rac's agent. At the default level, it can read
private text on one site. It can then type that text into another site without asking. Chrome and Yab both
stop that, so rac should too. Add a test suite of tricky pages so this stays fixed. Next, let outside AI
agents use rac, but only when the user turns it on. They should start with read-only access, and rac's own
safety checks still apply. Don't add AI memory. Dia already deleted its memory feature. Don't add cloud
relays or usage counts either. They would break rac's promise of sending nothing home.

### Take, ranked

Costs are rough, for one maintainer directing agents, and assume a working build tree (INFERENCE).

1. **Arc import that keeps spaces as spaces** (1–2 weeks). Read `~/Library/Application Support/Arc/StorableSidebar.json`
   (spaces, pinned trees, Today tabs, favorites per profile in `topAppsContainerIDs`, themes in
   `customInfo.windowTheme`) plus the Chromium profiles in `Arc/User Data` with the user's consent for the
   "Arc Safe Storage" key (FACT for paths and fields, `A:packages/import/ios/Core/ArcSidebar.swift:7-57`,
   `A:packages/import/ios/Core/Discovery.swift:67,299`). Dia turns Arc spaces into profiles (FACT,
   [arc.net][arc-sunset]); rac can keep them as real spaces. Ship it before 2026-12-22, while users still have Arc
   installed and are choosing a browser; the files should outlive the app (INFERENCE). Also read Arc's new
   Export Data output once its format is known.
2. **Close the `auto` data-flow gap with a deterministic rule** (3–5 days plus tests). Proposal, three parts:
   (a) text the model types that isn't in the user's messages may go only into the origin it was read from;
   anywhere else gets a card that shows the exact text (Chrome's readable→writable rule, Yab's mail rule,
   Dia's "Dia-controlled view"); (b) at `auto`, the first action on an origin the user didn't name gets one
   card with **Allow once / Always on this site / Don't allow** (Edge's Balanced prompt); (c) keep rac's exact
   URL match, and drop model-added fragments and query strings (HashJack, Dia's query-parameter rule). Check
   whether Chromium's `components/origin_gating` (`C:components/origin_gating/core/types.h:33-79`) can carry
   the per-turn origin sets instead of new rac code.
3. **A prompt-injection eval suite that runs in CI** (1–2 weeks). Two layers: guard-level policy tests generated
   from BrowseSafe-Bench samples (MIT) rendered as local fixture pages, and a small end-to-end harness of
   WASP-style tasks on local pages with a scripted or local model. Report attack success rate and ratchet it,
   as Chrome does (FACT for both datasets' licenses and sizes, [HF][hf-browsesafe-bench], [WASP][wasp]).
4. **Arc's daily habits, with measured motion** (4–6 weeks total; each is independent). Peek (⇧-click, plus
   links from pinned tabs and favorites; promote with ⌘O; split button), Little Arc (⌥⌘N and the default target
   for links from other apps; ⌘O to promote), Clear plus a recoverable archive that never touches media tabs,
   Supercopy (clean link on ⇧⌘C), ⌘T actions. Use the measured curves in [UI](#ui-look-and-feel) as starting
   tokens. **Conflict:** `R:VISION.md:123-132` lists "Auto-archiving old tabs" and "Peek-style link previews"
   as not planned. The maintainer has to decide; the Arc usage data argues for both.
5. **An outside-agent door that is local, off by default, and read-only by default** (2–3 weeks). Take Opera's
   defaults (read tabs, page text, screenshot on; history and every write tool off until the user enables
   them), Yab's transport (an MCP stdio command that bridges to a user-only Unix socket and can start rac
   hidden), one-click setup for Claude Code and Codex, and a small `rac` CLI. Every call goes through the same
   controller and guard. Give it its own switch, separate from rac's built-in assistant, so a user can turn off
   rac's agent and keep the door (Opera's free tier; the Aside feedback in
   `R:plans/context/maintainer-brief.md:88-93`). When the switch is off, nothing listens.
6. **An isolated "clean" agent context** (about 1 week). Atlas's per-session in-memory storage partition, or
   Brave's separate profile: no cookies, no sign-ins, discarded at the end. Offer it as "Run without my
   sign-ins" on the task card; make it the default for outside agents' first runs (INFERENCE).
7. **Drafts, not sends** (2–3 days). For mail, posts, and calendar events, the agent fills and the user presses
   the final button, as Dia does. Show typed text on the card (FACT for Dia's pattern, [Dia security][dia-security]).
8. **Approval details** (a few days each): Comet's "what was blocked and why, and how to report a false
   positive" notice; Yab's money threshold with a monthly cap (only after payments exist); Atlas's Watch Mode
   idea (pause on sensitive sites when the agent's tab isn't visible). Keep rac's rule of no keyboard shortcut
   for Allow on risky cards (`R:docs/internals/ai.md:477`); Yab's ⌘↩ is faster but weaker.
9. **Skills as saved prompts with "/"** (2–4 days, on rac's saved prompts). Dia Skills, Chrome Skills, Comet
   Shortcuts, Neon Cards and Atlas Saved Prompts all converged on this (FACT, sources in [Features](#ai-assistant)).
10. **A public security bulletin page and disclosure address** (half a day). Dia's bulletin shows how cheap and
    credible this is (FACT, [bulletins][dia-bulletins]).
11. **WebMCP later** (about 1 week, after a Helium sync). Chromium 154 already has `document`/`navigator`
    `modelContext` and the actor's script-tool receiver (`C:third_party/blink/renderer/core/script_tools/model_context.idl`,
    `C:chrome/browser/actor/actor_script_tool_receiver.h`). Let rac's agent prefer a site's declared tools, still
    through the guard. Adoption is tiny today (INFERENCE).

### Avoid

1. **A cloud store or sync for executable customizations.** Arc's Boost bug came from a cloud rule, not the
   browser (FACT, [Tenable][tenable-arc]). Ship CSS-only Boosts first (Yab's "Look" boosts run no code); keep
   any JavaScript Boost local, never auto-enabled by sync, never on sign-in, password, or payment pages (Yab's
   rule, [Yab store][yab-store]).
2. **Any rac-run relay or proxy for agents.** Opera's persistent MCP proxy and Yab's Cloudflare relay put a
   server in the path. rac's promise is no servers. A remote hand-off, if ever, should be peer-to-peer or
   user-hosted (INFERENCE).
3. **Usage counting and data-on-by-default.** Yab's daily IDs, Dia's 30-day content data, Arc's mandatory
   account, Comet's ad profile. Arc refugees are leaving an account-bound browser (FACT for each,
   sources above).
4. **Detection as the main defense.** BrowseSafe was bypassed 36 % of the time with encodings; Dia's team
   bypassed every detector it built (FACT/CLAIM, [Lasso][lasso-browsesafe], [Dia bulletins][dia-bulletins]).
   A local classifier is at most an extra layer.
5. **Hidden privileged parts.** Comet's invisible built-in extensions carried a command-launching API. Every
   powerful rac component should be visible in settings and revocable (INFERENCE from [SecurityWeek][sw-squarex]).
6. **AI memory.** Dia deleted its memory; Atlas's went with the app; "Tainted Memories" showed memory as a way
   to keep an attack alive. If ever needed, copy Yab's plain local Markdown with an off switch, and never write
   memory from page content (FACT for the history; INFERENCE for the advice).
7. **Feature sprawl.** Arc's "novelty tax" and Yab's breadth (mail client, Messages, a "Get to Know Me" crawl
   of signed-in sites) are the opposite of "opinionated" and widen what an injection can reach.
8. **Raw DevTools access as the outside-agent door.** Chrome 144's attach-after-consent path and Opera's CLI give
   an agent the whole browser and bypass rac's guard (FACT for the path, `O:docs/advanced-usage.md:55-101`).
   Keep it a developer setting with a loud warning, or leave it off.
9. **Treating the address bar, URL fragments, or screenshot text as the user's voice.** Three public bugs
   (NeuralTrust, HashJack, Brave's screenshots) came from this (FACT, incidents table).
10. **Leaving Chromium's UI for a separate shell now.** OWL and ADK show it can work, but each took a funded
    team. Keep it as a long-range option to cut rac's 217-file upstream diff (INFERENCE).

## Open questions and things you could not verify

- **Arc's Export Data format** and whether `StorableSidebar.json` stays readable after 2026-12-22. The app
  stops working, but the file should remain on disk (INFERENCE). Nobody has published the export's format.
- **Arc's archive intervals** beyond the 12-hour default, and which model vendors powered Arc Max. Arc's help
  centre returned HTTP 403 to fetches; I used the Wayback copy of the release notes.
- **Arc's process model.** ADK is described only at a high level. I could not confirm whether Chromium runs in
  process.
- **Dia's "agentic mode".** Its security FAQ describes rules for an agentic mode, but the changelog shows no
  general clicking agent. Dia's 2026 pricing is from reviews, not Dia.
- **Comet today**: its Chromium version, whether the ad profile launched, and whether purchase confirmations
  now always fire (Guardio saw saved cards autofilled without a prompt in 2025).
- **Atlas's shutdown reasons** beyond "lessons absorbed"; no usage numbers were given.
- **Yab defaults.** The manual says "Auto, to start with" and never says "default". Whether non-mail agent
  traffic avoids Yab's servers is implied ("no server of ours can read your browsing"), not stated. Yab's
  current tool count is above 69 (that count is from 0.0.18).
- **Opera's MCP proxy**: whether page content passes through Opera's servers (likely, since remote clients
  connect through it; INFERENCE), and how long anything is kept.
- **Chrome**: the list behind "sensitive sites"; whether the full read-only origin set shipped; whether rac
  can use `components/origin_gating` without Glic.
- **Edge**: how "Balanced" decides which sites are "popular" or "commonly trusted".
- **Team sizes** for every vendor except 21st's three people.
- **Motion** for Comet, Atlas, Neon, Chrome's agent, and Edge's agent: no public numbers.
- **Provenance of reverse-engineered constants.** The Dia and Arc numbers above come from another project's
  binary analysis. `R:plans/research/rac-baseline.md:662` already flags the question of publishing a design
  system built on another vendor's values.
- Several facts rest on secondary coverage of primary posts I could not fetch: OpenAI's hardening post
  (HTTP 403), HUMAN Security's comparison (HTTP 403), Cato's HashJack write-up, Guardio's original post.

## Sources

All web sources were read on 2026-10-25. Where a page blocked fetches, the copy actually read is named.

### Local files (read-only)

- Ardia clone: `A:docs/dia-spec.md` (Dia 1.49–1.53 and Arc measurements), `A:docs/dia-feature-parity.md:219`,
  `A:packages/import/README.md:12-29`, `A:packages/import/ios/Core/ArcSidebar.swift:7-57`,
  `A:packages/import/ios/Core/Discovery.swift:67,74,299`.
- Yab's open launcher: `Y:README.md` (remote assistants 9-40, install 52-180, tools 189-268, what leaves the
  Mac 269-285, development 294-303).
- Opera: `O:README.md:1-45`, `O:docs/advanced-usage.md:55-101`, `O:docs/tool-reference.md`;
  `/tmp/rac-overhaul/src/opera-browser-cli/README.md:1-60`, `.../CLAUDE.md`, `.../benchmarks/`.
- Chromium 154 in rac's tree: `C:chrome/browser/actor/README.md`, `C:chrome/browser/actor/site_policy.cc:39-116`,
  `C:chrome/browser/actor/execution_engine.cc:179-340`, `C:chrome/browser/actor/actor_script_tool_receiver.h:17-35`,
  `C:components/origin_gating/core/types.h:33-79`, `C:components/origin_gating/core/origin_gating_checker.h:26-53`,
  `C:third_party/blink/renderer/core/script_tools/model_context.idl:1-25`,
  `C:chrome/browser/devtools/devtools_connection_dialog.cc:49-83`,
  `C:chrome/browser/devtools/remote_debugging_server.cc:163-189`,
  `C:third_party/blink/renderer/modules/content_extraction/ai_page_content_agent.cc`.
- This repo: `R:plans/context/maintainer-brief.md`, `R:plans/context/competitors-ardia-yab-2026-10-23.md`,
  `R:plans/research/rac-baseline.md:207,662`, `R:docs/internals/ai.md:49-91,193-332,333-580,677-750`,
  `R:VISION.md:123-132`.
- Text copies of pages that blocked direct fetches: `/tmp/rac-overhaul/web/arc-rn-wb.html.txt`,
  `/tmp/rac-overhaul/web/arc-rn-start.html.txt`, `/tmp/rac-overhaul/web/oa-owl.txt`,
  `/tmp/rac-overhaul/web/oa-intro-wb.txt`.

### Arc and The Browser Company

[tc-arc-sunset]: https://techcrunch.com/2026/10/22/arc-browser-sunsets-december-22-as-the-browser-company-doubles-down-on-dia/
[htg-arc]: https://www.howtogeek.com/arc-browser-shutdown-date/
[arc-sunset]: https://arc.net/blog/CVE-2024-45489-incident-response
[arc-rn]: https://web.archive.org/web/2026/https://resources.arc.net/hc/en-us/articles/20498293324823-Arc-for-macOS-2024-2026-Release-Notes
[arc-rn-old]: https://start.arc.net/release-notes
[tbc-letter]: https://browsercompany.substack.com/p/letter-to-arc-members-2025
[gigazine-letter]: https://gigazine.net/gsc_news/en/20250608-letter-to-arc-members
[wp-arc]: https://en.wikipedia.org/wiki/Arc_(web_browser)
[arc-security]: https://arc.net/security
[arc-privacy-blog]: https://adam.kostarelas.com/blog/arc-browser-privacy-check/
[bgr-arc]: https://www.bgr.com/tech/i-want-to-try-the-trendy-arc-browser-but-not-if-they-force-me-to-register-an-account/
[tenable-arc]: https://www.tenable.com/cve/CVE-2024-45489
[ath-atc]: https://allthings.how/how-to-route-links-to-specific-arc-spaces-using-air-traffic-control-in-the-arc-browser/
[anthracite-atc]: https://github.com/yttrium400/anthracite-browser/issues/23
[umich-arcmax]: https://michigan.it.umich.edu/news/2023/11/01/tech-tip-arc-max

- [TechCrunch: Arc sunsets December 22][tc-arc-sunset] (2026-10-22); [How-To Geek: shutdown dates][htg-arc].
- [Arc sunset notice][arc-sunset]: this arc.net URL, the old CVE incident report, now serves the sunset notice
  (export steps, "Spaces become Profiles and Folders become Tab Groups").
- [Arc for macOS 2024–2026 release notes][arc-rn] (Wayback copy; the help centre returns HTTP 403) and
  [older release notes][arc-rn-old].
- [Letter to Arc members 2025][tbc-letter] (usage statistics, ADK, TCA and SwiftUI) and [Gigazine's summary][gigazine-letter].
- [Wikipedia: Arc][wp-arc]; [arc.net/security][arc-security]; [Kostarelas traffic test][arc-privacy-blog];
  [BGR on the account requirement][bgr-arc].
- [Tenable: CVE-2024-45489][tenable-arc]; Arc's original incident report is no longer served (see above).
- [allthings.how: Air Traffic Control][ath-atc]; [anthracite-browser issue #23][anthracite-atc];
  [University of Michigan IT: Arc Max][umich-arcmax].

### Dia

[dia-cl]: https://www.diabrowser.com/changelog
[dia-150]: https://www.diabrowser.com/changelog/mac/1-50-0
[dia-security]: https://www.diabrowser.com/security
[dia-bulletins]: https://www.diabrowser.com/security/bulletins
[dia-reviews]: https://makerstack.co/reviews/dia-review/
[aie-samir]: https://ai.engineer/speakers/samir-mody

- [Dia changelog][dia-cl] and [1.50.0 "Retiring Memory"][dia-150].
- [Dia security FAQ][dia-security] (prompt-injection stance, providers, data use, MDM).
- [Dia security bulletins][dia-bulletins] (Sync design 2026-04-29, fetch_web_content provenance 2026-02-12,
  CVE-2025-15032, CVE-2025-13132).
- [MakerStack review][dia-reviews] (pricing, secondary); [Samir Mody, AI Engineer][aie-samir] ("From Arc to Dia").

### Comet and Perplexity

[zenity-comet]: https://labs.zenity.io/post/perplexity-comet-a-reversing-story
[mr-comet-ios]: https://www.macrumors.com/2026/03/18/perplexity-comet-browser-iphone/
[pplx-oct3]: https://www.perplexity.ai/changelog/what-we-shipped-october-3rd
[tc-comet-free]: https://techcrunch.com/2025/10/02/perplexitys-comet-ai-browser-now-free-max-users-get-new-background-assistant/
[emarketer-comet]: https://www.emarketer.com/content/perplexity-comet-browser-will-track-users-hyperpersonalized-ads-sponsored-content
[comet-help]: https://www.perplexity.ai/help-center/comet/en/articles/12658082-control-what-comet-assistant-can-use
[comet-faq]: https://www.perplexity.ai/comet/resources/articles/comet-data-privacy-security-faq-s
[alt-comet]: https://alternativeto.net/news/2025/11/perplexity-comet-introduces-homepage-privacy-widget-and-local-data-controls/
[proton-comet]: https://proton.me/blog/ai-browsers-perplexity-chrome-privacy
[comet-shortcuts]: https://fastshortcuts.com/shortcuts/comet/
[muo-comet]: https://www.makeuseof.com/best-perplexity-comet-shortcuts-i-wish-i-knew/
[tabbit-comet]: https://go.tabbit.ai/comet-browser-review
[human-atlas-comet]: https://www.humansecurity.com/learn/blog/chatgpt-atlas-vs-perplexity-comet-agentic-browsers/
[pplx-4layers]: https://www.perplexity.ai/hub/blog/mitigating-prompt-injection-in-comet
[pplx-dayone]: https://www.perplexity.ai/hub/blog/how-we-built-security-into-comet-from-day-one
[pplx-safer]: https://www.perplexity.ai/hub/blog/how-we-engineer-safer-agents
[hf-browsesafe]: https://huggingface.co/perplexity-ai/browsesafe
[hf-browsesafe-bench]: https://huggingface.co/datasets/perplexity-ai/browsesafe-bench
[browsesafe-paper]: https://arxiv.org/abs/2511.20597
[lasso-browsesafe]: https://www.lasso.security/blog/red-teaming-browsesafe-perplexity-prompt-injections-risks

- [Zenity Labs: Perplexity Comet, a reversing story][zenity-comet] (components, tools, page representation, blocks).
- [MacRumors: Comet for iPhone][mr-comet-ios]; [Perplexity changelog, 2025-10-03][pplx-oct3];
  [TechCrunch: Comet free, background assistant][tc-comet-free]; [eMarketer on ad plans][emarketer-comet].
- [Comet help: what the assistant can use][comet-help]; [Comet privacy FAQ][comet-faq];
  [AlternativeTo: privacy widget][alt-comet]; [Proton critique][proton-comet].
- [fastshortcuts][comet-shortcuts]; [MakeUseOf shortcuts][muo-comet]; [Tabbit review][tabbit-comet] (secondary);
  [HUMAN Security comparison][human-atlas-comet] (HTTP 403; used via search summary).
- Perplexity security: [four layers, 2025-10-22][pplx-4layers]; [security from day one, 2026-02-20][pplx-dayone];
  [how we engineer safer agents, 2026-09-29][pplx-safer].
- BrowseSafe: [model][hf-browsesafe] and [benchmark][hf-browsesafe-bench] (both MIT per the Hugging Face API);
  [paper][browsesafe-paper]; [Lasso red-team][lasso-browsesafe].

### ChatGPT Atlas

[oa-owl]: https://openai.com/index/building-chatgpt-atlas/
[oa-intro]: https://openai.com/index/introducing-chatgpt-atlas/
[oa-help-sidebar]: https://help.openai.com/en/articles/12628199-using-ask-chatgpt-sidebar-and-chatgpt-agent-on-atlas
[atlas-rb]: https://releasebot.io/updates/openai/chatgpt-atlas
[9to5-atlas-groups]: https://9to5mac.com/2026/01/22/you-can-now-group-tabs-on-openais-chatgpt-atlas-browser/
[9to5-atlas-end]: https://9to5mac.com/2026/07/09/openai-is-discontinuing-chatgpt-atlas-its-standalone-desktop-browser/
[mr-atlas-end]: https://www.macrumors.com/2026/07/10/openais-chatgpt-atlas-browser-shutting-down/
[st-atlas]: https://www.secondtalent.com/resources/chatgpt-atlas-review-ai-browser/
[sw-atlas-ciso]: https://simonwillison.net/2025/Oct/22/openai-ciso-on-atlas/
[zenity-atlas]: https://labs.zenity.io/post/exploring-the-risks-of-chatgpt-s-atlas-browser
[cybernews-atlas]: https://cybernews.com/ai-tools/i-tried-chatgpt-atlas-the-ai-browser-thats-both-amazing-and-terrifying/
[thn-atlas]: https://thehackernews.com/2025/10/new-chatgpt-atlas-browser-exploit-lets.html
[cs-atlas]: https://cyberscoop.com/openai-chatgpt-atlas-prompt-injection-browser-agent-security-update-head-of-preparedness/

- [How we built OWL][oa-owl] (2025-10-30; read via the Wayback Machine because openai.com returned 403) and
  [Introducing ChatGPT Atlas][oa-intro] (Wayback copy).
- [OpenAI help: sidebar and agent][oa-help-sidebar]; [Releasebot: Atlas notes][atlas-rb] (mirrors
  `help.openai.com/en/articles/12591856`); [9to5Mac: tab groups][9to5-atlas-groups].
- Shutdown: [9to5Mac][9to5-atlas-end], [MacRumors][mr-atlas-end], [Second Talent][st-atlas] (secondary).
- Security: [Simon Willison on the CISO's post][sw-atlas-ciso]; [Zenity on Atlas][zenity-atlas];
  [Cybernews hands-on][cybernews-atlas]; [The Hacker News: omnibox and memory issues][thn-atlas];
  [CyberScoop on OpenAI's hardening post][cs-atlas] (primary `openai.com/index/hardening-atlas-against-prompt-injection/`
  returned 403).

### Yab

[yab-home]: https://yetanotherbrowser.com/
[yab-cl]: https://yetanotherbrowser.com/changelog
[yab-manual]: https://yetanotherbrowser.com/manual
[yab-perms]: https://yetanotherbrowser.com/manual/permissions
[yab-memory]: https://yetanotherbrowser.com/manual/memory
[yab-connect]: https://yetanotherbrowser.com/manual/connect-agents
[yab-store]: https://yetanotherbrowser.com/manual/store
[yab-privacy]: https://yetanotherbrowser.com/privacy
[yab-vs-chrome]: https://yetanotherbrowser.com/compare/yab-vs-chrome
[yc-21st]: https://www.ycombinator.com/companies/21st
[serafim]: https://serafim.cloud/

- [Yab home][yab-home] (v0.39.1 at fetch time), [changelog][yab-cl] (0.1 on 2026-09-26 to 0.40 on 2026-10-25),
  [manual][yab-manual], [What agents ask first][yab-perms], [Memory][yab-memory], [Connecting Claude or
  ChatGPT][yab-connect], [Boosts and the Store][yab-store], [Privacy][yab-privacy] (updated 2026-10-19),
  [Yab vs Chrome][yab-vs-chrome] (Yab's own comparison).
- [YC: 21st][yc-21st]; [serafim.cloud][serafim].

### Opera Neon

[opera-neon-ship]: https://blogs.opera.com/news/2025/09/opera-neon-agentic-ai-browser-release/
[tc-neon]: https://techcrunch.com/2025/09/30/opera-launches-its-ai-centric-neon-browser/
[infoq-neon]: https://www.infoq.com/news/2025/06/opera-neon
[opera-mcp]: https://blogs.opera.com/news/2026/03/opera-neon-adds-mcp-connector-to-the-browser/
[opera-cli]: https://blogs.opera.com/news/2026/05/opera-browser-cli/
[opera-free]: https://blogs.opera.com/news/2026/08/your-ai-agents-can-use-opera-neon-free-of-charge/
[neon-toolchase]: https://toolchase.com/tool/opera-neon/
[neon-faq]: https://www.operaneon.com/
[opera-neon-pi]: https://blogs.opera.com/security/2025/10/prompt-injection-in-opera-neon-rapid-response-through-responsible-disclosure/

- [Opera Neon ships][opera-neon-ship] (2025-09-30); [TechCrunch launch][tc-neon]; [InfoQ preview][infoq-neon]
  (Make in a cloud VM).
- [MCP Connector][opera-mcp] (2026-03-31); [opera-browser-cli][opera-cli] (May 2026); [free for your own
  agents][opera-free] (2026-08-14); [ToolChase plans][neon-toolchase] (secondary); [Neon site and FAQ][neon-faq].
- [Opera's injection post-mortem][opera-neon-pi].

### Chrome with Gemini

[g-autobrowse]: https://blog.google/products-and-platforms/products/chrome/gemini-3-auto-browse/
[tc-gemini-chrome]: https://techcrunch.com/2025/09/18/google-brings-gemini-in-chrome-to-us-users-unveils-agentic-browsing-capabilities-and-more/
[9to5g-autobrowse]: https://9to5google.com/2026/01/28/chrome-gemini-auto-browse/
[g-sec]: https://blog.google/security/architecting-security-for-agentic/
[yahoo-chrome-skills]: https://tech.yahoo.com/ai/gemini/articles/now-save-reuse-gemini-prompts-182248269.html
[9to5g-pi]: https://9to5google.com/2026/03/17/gemini-personal-intelligence-free/
[vb-webmcp]: https://venturebeat.com/infrastructure/google-chrome-ships-webmcp-in-early-preview-turning-every-website-into-a
[webmcp-moved]: https://mcpplaygroundonline.com/blog/what-is-webmcp

- [TechCrunch: Gemini in Chrome for US users][tc-gemini-chrome] (2025-09-18); [Google: Gemini 3 in Chrome and auto browse][g-autobrowse] (2026-01-28); [9to5Google][9to5g-autobrowse].
- [Google: architecting security for agentic capabilities in Chrome][g-sec] (Nathan Parker, 2025-12-08; the old
  `security.googleblog.com/2025/12/architecting-security-for-agentic.html` redirects here).
- [Skills in Chrome][yahoo-chrome-skills] (2026-04-14, secondary); [Personal Intelligence][9to5g-pi].
- WebMCP: [VentureBeat][vb-webmcp] (preview in Chrome 146); [mcpplayground][webmcp-moved] (origin trial and
  `document.modelContext` rename, single source).

### Edge with Copilot

[sa-edge]: https://siliconangle.com/2025/07/28/microsoft-turns-edge-ai-agent-new-copilot-mode/
[mr-edge]: https://www.macrumors.com/2025/10/24/microsoft-edge-copilot-mode-ai-browser/
[edge-may26]: https://blogs.windows.com/msedgedev/2026/05/13/new-updates-to-edge-across-desktop-and-mobile/
[ms-browse]: https://support.microsoft.com/en-us/topic/copilot-actions-in-edge-5ed5e17e-42df-40a3-984a-20420eba86e2
[eleven-edge]: https://www.elevenforum.com/t/enable-or-disable-copilot-actions-in-microsoft-edge-on-windows-11.41278/
[wc-edge]: https://www.windowscentral.com/microsoft/windows-11/3-ai-features-you-must-enable-now-on-microsoft-edge
[edge-allowlist]: https://windowsforum.com/threads/edge-copilot-expansion-multi-tab-reasoning-journeys-and-new-ai-browser-control.418166/
[action1-cve]: https://www.action1.com/vulnerabilities/cve-2026-48561/

- [SiliconANGLE: Copilot Mode launch][sa-edge]; [MacRumors: Actions and Journeys][mr-edge].
- [Edge blog: retiring Copilot Mode][edge-may26] (Sean Lyndersay, 2026-05-13).
- [Microsoft support: Browse with Copilot][ms-browse]; guides on the three levels: [ElevenForum][eleven-edge],
  [Windows Central][wc-edge]; [WindowsForum on the allow list][edge-allowlist] (secondary).
- [Action1: CVE-2026-48561][action1-cve]; Microsoft's advisory is
  `https://msrc.microsoft.com/update-guide/vulnerability/CVE-2026-48561`.

### Prompt-injection research and frameworks

[brave-comet]: https://brave.com/blog/comet-prompt-injection/
[brave-screens]: https://brave.com/blog/unseeable-prompt-injections/
[brave-neon]: https://brave.com/blog/prompt-injection-flaw-opera-neon/
[brave-ai-browsing]: https://brave.com/blog/ai-browsing/
[dd-comet]: https://www.decryptiondigest.com/blog/agentic-browser-prompt-injection-comet-atlas-security
[thn-promptfix]: https://thehackernews.com/2025/08/experts-find-ai-browsers-can-be-tricked.html
[bc-cometjack]: https://www.bleepingcomputer.com/news/security/commetjacking-attack-tricks-comet-browser-into-stealing-emails/
[time-comet]: https://time.com/7323827/ai-browsers-perplexity-comet/
[sw-squarex]: https://www.securityweek.com/squarex-and-perplexity-quarrel-over-alleged-comet-browser-vulnerability/
[hn-squarex]: https://www.helpnetsecurity.com/2025/11/20/perplexity-comet-browser-security-mcp-api/
[hn-hashjack]: https://www.helpnetsecurity.com/2025/11/26/hashjack-hijack-ai-assistants-browsers/
[reg-gartner]: https://www.theregister.com/software/2025/12/08/block-all-ai-browsers-for-the-foreseeable-future-gartner/2793276
[sw-trifecta]: https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/
[camel]: https://arxiv.org/abs/2503.18813
[design-patterns]: https://arxiv.org/abs/2506.08837
[wasp]: https://arxiv.org/abs/2504.18575

- Brave's series: [Comet][brave-comet] (2025-08-20), [screenshots][brave-screens] (2025-10-21),
  [Opera Neon][brave-neon], [Brave's own isolated-profile agent][brave-ai-browsing].
- [Decryption Digest][dd-comet] (secondary); [The Hacker News: Guardio "Scamlexity"/PromptFix][thn-promptfix];
  [BleepingComputer: CometJacking][bc-cometjack]; [TIME on Perplexity's response][time-comet].
- [SecurityWeek][sw-squarex] and [Help Net Security][hn-squarex] on SquareX's report (primary:
  `labs.sqrx.com/comet-mcp-api-allows-ai-browsers-to-execute-local-commands-dec185fb524b`).
- [Help Net Security: HashJack][hn-hashjack] (primary: Cato CTRL blog
  `catonetworks.com/blog/cato-ctrl-hashjack-first-known-indirect-prompt-injection/`).
- [The Register: Gartner][reg-gartner] (Gartner document 7211030).
- Frameworks: [Willison, the lethal trifecta][sw-trifecta] (2025-06-16); [CaMeL][camel];
  [Design Patterns for Securing LLM Agents][design-patterns]; [WASP benchmark][wasp].
