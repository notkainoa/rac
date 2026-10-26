# Long tail of Arc and Dia alternatives: research dossier

Swept on 2026-10-25, 58 days before Arc stops working (2026-12-22). I read code in shallow clones under `/tmp/rac-overhaul/src/` (`crest`, `stedding`, `refrax`, `mori`, `floorp`, `min`, `sidebery`, plus the existing `opera-browser-cli` and `opera-devtools-mcp` clones), used read-only `gh api` calls, web search, and read-only greps of rac's worktree and its built Chromium 154 tree at `/Users/knewton/Dev/Github/rac/build/src`. I built, installed, and ran nothing.

Evidence tags: **FACT** (primary source: code, official docs, release notes, the vendor's own repo), **CLAIM** (vendor marketing, self-report, or a secondary article), **INFERENCE** (my reasoning). Paths written `crest:<path>:<line>` mean `/tmp/rac-overhaul/src/crest/<path>`; same pattern for other clones. `chromium:<path>` means rac's built tree.

Scope. This file covers everything *not* already given its own dossier. Zen, Nook, Ora, Ardia, Helium, BrowserOS, T3 Code, and rac itself have dossiers in `plans/research/`. Yab and Aside are in `plans/context/competitors-ardia-yab-2026-10-23.md` and the maintainer brief. They appear here only as one-line pointers.

## In plain English

Many small teams are building Arc replacements right now. Most are weeks old, and many are largely written by AI agents, like rac. The strongest one, Crest, already ships on Mac and iPhone. Big browsers have caught up on the basics. Chrome, Edge, and Firefox now all have vertical tabs. So a vertical sidebar alone wins no one. Arc users will miss other things. In Arc, each space could use a different account, like work Gmail in one space and personal Gmail in another, in one window. rac can't do that yet. rac also can't carry a sidebar to a second Mac. It may also stop a Slack tab in a hidden space after 15 minutes. This file gives each browser one short entry. Then it ranks the ideas rac lacks, by value to Arc users and by cost. It also lists traps big browsers already removed.

## Snapshot

Stars and dates from `gh api` on 2026-10-25 unless marked. Rows for products with their own dossier are omitted.

### New open-source Arc and Dia clones (2026)

| Name | What it is | Engine | Platforms | License | Repo, stars | Age | Release cadence | Team | Business model |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Crest | Arc-style browser; SwiftUI shell over a C# core; two engines on Mac | ungoogled-chromium 155.0.8059.84 by default, WebKit per page (FACT `crest:CrestEngines/Chromium/source.lock.json:5`, `crest:README.md:38-48`) | Mac (Apple silicon, macOS 26.1+), iPhone, iPad | MPL-2.0 | `pauljoda/Crest`, 788 | 2026-08-15 | 268 releases incl. nightly/dev; 12 stable tags, v0.4.0 (08-18) to v0.8.50 (10-23) | 1 main author (560 commits) + 11 other human contributors (next largest: 30 commits) | Ko-fi sponsors (`crest:SPONSORS.md`) |
| Stedding | Arc parity as a Chromium patch series (like rac) | Chromium 156 stable, plain (not ungoogled) | macOS (Apple silicon), Windows | BSD-3-Clause | `ysalitrynskyi/stedding-browser`, 55 | 2026-08-30 | 38 releases, 0.1.0-beta.1 (09-01) to 0.3.0-beta.16 (10-25) | 1 owner + agents (`AGENTS.md`) | None stated |
| Refrax | Swift browser; each tab picks WebKit or Chromium | WebKit built in; Chromium as a separately installed, signed, out-of-process engine bundle (FACT `refrax:REFERENCE.md:7-21`) | macOS 26+ | GPL-3.0 | `kageroumado/refrax-browser`, 48 | 2026-05-21 | 9 releases | 1 main author (181 commits) | None stated |
| Mori | Arc-like on Chromium Views; Codex as assistant | ungoogled-chromium 156.0.8078.47 | Windows preview (unsigned); Linux and macOS scripts unvalidated; separate iOS app | MIT | `FujiwaraChoki/mori-browser`, 140 | 2026-05-31 | Preview builds | 1 author + agents | None |
| Yalqen | Keyboard-first developer browser | Electron 44 (FACT `apps/browser/package.json:39`) | macOS 13+ (Apple silicon), Linux preview | MIT | `YSamed/yalqen`, 31 | 2026-09-25 | 100+ releases, v0.3.73 on 10-21 | 1 author | None |
| Meridian | Arc clone "built for AI agents" | Electron (JavaScript) | macOS, Windows, Linux (CLAIM) | MIT | `Undermove/meridian-browser`, 8 | 2026-10-23 | 24 releases in about 2 days | 1 author | None |
| Tangent | Arc ideas on Electron | Electron | Desktop | MIT | `davidjbeveridge/tangent`, 0 | 2026-10-22 | none | 1 | None |
| Flow | Arc-like Electron browser | Electron | macOS, Windows, Linux | GPL-3.0 | `MultiboxLabs/flow-browser`, 1,086 | 2025-03-16 | Last release v0.12.1 on 2026-04-16 | small | None |
| Aura | Arc-like for Apple platforms | WebKit | iOS, iPadOS, macOS, visionOS | MPL-2.0 | `doorhinge-apps/Aura-Browser`, 198, **archived** | 2024-04 | Stopped; "being rewritten" (CLAIM) | small | None |

### Established open-source browsers and extensions

| Name | What it is | Engine | Platforms | License | Repo, stars | Age | Release cadence | Team | Business model |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Floorp | Feature-heavy Firefox fork from Japan | Firefox 157.0.1 runtime ("Noraneko") (FACT, v12.20.0 notes) | Windows, macOS, Linux | MPL-2.0 | `Floorp-Projects/Floorp`, 8,459 | 2021-12 | About every 1-2 weeks (v12.16.2 07-16 to v12.20.2 10-17) | 30+ contributors (first API page) | Sponsors (1Password, CubeSoft, SignPath) |
| Min | Minimal browser | Electron 43.4.1 (FACT `min:package.json:54`) | Windows, macOS, Linux | Apache-2.0 | `minbrowser/min`, 9,223 | 2015-10 | Every 1-3 months (v1.35.7, 08-23) | 1 main author | GitHub Sponsors |
| Brave | Privacy Chromium fork | Chromium (`brave-core`) | All | MPL-2.0 | `brave/brave-browser`, 23,980 | 2017 | Follows Chromium majors | Company | Opt-in ads, search, Leo Premium, VPN |
| DuckDuckGo browser | Privacy browser with Fire Button | WebKit (Mac) | macOS, iOS, Windows, Android | Apache-2.0 | `duckduckgo/apple-browsers`, 266 | 2024-12 (old repo archived) | Frequent | Company | Search ads, subscription |
| Thorium | Speed-tuned Chromium fork | Chromium; skips milestones, each release labelled "Beta" (2026: M144, M150, M151, M152, M154, M156) | Linux; Win, Mac, RasPi in other repos | BSD-3-Clause | `Alex313031/thorium`, 7,592 | 2021-10 | One milestone every ~4 weeks | 1 author | Donations |
| Supermium | Chromium for old Windows | Chromium 150.0.7871.255 (6 majors behind) | Windows XP and later | None listed by GitHub | `win32ss/supermium`, 4,857 | 2023-05 | Point releases on M150 | 1 author | Donations |
| Ladybird | A new, independent engine | LibWeb/LibJS (own), some Rust | Linux, macOS (alpha targeted 2026; not out on 10-25) | BSD-2-Clause | `LadybirdBrowser/ladybird`, 66,673 | 2024-05 (from SerenityOS) | No releases | 8 full-time engineers (CLAIM) | Non-profit, donations |
| Glide | Keyboard-first Firefox fork, TypeScript config | Firefox | macOS, Linux | MPL-2.0 | `glide-browser/glide`, 1,500 | 2025-04 | 0.1.65a on 10-21; roughly monthly | 1 author | None |
| qutebrowser / Nyxt | Vim-like / Lisp-scriptable browsers | Qt WebEngine / WebKitGTK and others | Desktop | GPL-3.0 / custom | 11,729 / 11,040 | 2014 / 2017 | Active | small | Donations |
| Sidebery | Firefox sidebar extension: panels, trees, snapshots | Firefox WebExtension | Firefox | MIT | `mbnuqw/sidebery`, 4,746 | 2018 | v5.6.1 on 2026-07-16 | 1 author | Donations |
| Tree Style Tab | Firefox tree-tabs extension with a public API | Firefox WebExtension | Firefox | MPL-2.0 by default (FACT, LICENSE) | `piroor/treestyletab`, 3,786 | 2010 | 4.4.9 on 2026-09-30 | 1 author | Donations |

### Closed browsers and built-in features of the big four

| Name | What it is | Engine | Platforms | Status on 2026-10-25 | Business model |
| --- | --- | --- | --- | --- | --- |
| Arc | The reference | Chromium | macOS, Windows | Stops working 2026-12-22; no new accounts since 10-22 (CLAIM, How-To Geek, Neowin) | Was free; Atlassian-owned |
| Dia | The Browser Company's AI browser | Chromium M156 (Mac 1.54.0, 10-22) | macOS; Windows since 1.0 on 10-06 | Weekly releases (FACT, changelog) | Free + paid AI; Atlassian |
| Vivaldi | Power-user Chromium browser, no generative AI | Chromium; own web-tech UI | Desktop, Android, iOS | 8.0 "Unified" redesign 2026-05-21; 8.2 on 2026-09-24 (CLAIM, gHacks, Wikipedia) | Search and partner deals |
| Orion | Kagi's WebKit browser that runs Chrome and Firefox extensions | WebKit | macOS, iOS | 1.0 on 2025-11-25; 1.1 on 2026-06-24 adds containers; Linux and Windows dropped 2026-10-02 and to be open-sourced (FACT for 1.0 and the 10-02 decision, Kagi blog; 1.1 date CLAIM) | Free; Orion+ $5/mo, $50/yr, $150 lifetime; 6 developers, 2,480 subscribers (CLAIM) |
| SigmaOS | YC WebKit browser with workspaces as to-do lists | WebKit | macOS | Last build 1.21.0 on 2026-03-03 (CLAIM, MacUpdate); stalled | $20 and $30/mo tiers (CLAIM) |
| Sidekick | Chromium "work browser" with app sidebar | Chromium | — | Shut down 2025-08-03 after Perplexity bought the team (CLAIM) | — |
| Wavebox | Chromium browser for many work accounts | Chromium 156.0.8078.48 | Desktop | Active, frequent | Subscription |
| Opera Air | "Mindful" Opera | Chromium | Desktop | Redesign 2026-10-15 (CLAIM, 9to5Mac) | Free; partners |
| Opera Neon | Opera's agent browser | Chromium | macOS, Windows | Free since 2026-08-14 for outside agents; $19.90/mo for Opera's agents (FACT, Opera blog; price CLAIM) | Subscription |
| Chrome | Native vertical tabs | Chromium | All | Vertical tabs stable in 146 (2026-03), rolled out 2026-04 (CLAIM, Engadget) | Google |
| Edge | Vertical tabs, split screen, Workspaces | Chromium | All | Edge 149 (2026-06-04) removed Collections and the sidebar app list (CLAIM, Windows Latest) | Microsoft |
| Firefox | Vertical tabs, groups, profiles, split view | Gecko | All | Split view 149 (2026-03-24); AI kill switch 148 (2026-02-24) | Mozilla |
| Safari | Profiles, web apps, Distraction Control | WebKit | Apple | Safari 26 Liquid Glass; compact tab bar back in macOS 26.4 (2026-03-24) | Apple |
| ChatGPT Atlas | OpenAI's browser | Chromium out of process ("OWL"), SwiftUI UI | macOS | **Reported shut down on 2026-08-09**, folded into the ChatGPT desktop app and a Chrome extension (CLAIM, Wikipedia, Digital Trends); had vertical tabs since 2025-11-18 | ChatGPT plans |
| Comet | Perplexity's agent browser | Chromium | Desktop, mobile | Free since 2025-10-02; background agents on $200/mo Max (CLAIM) | Subscription |
| Others | Genspark, Fellou, Strawberry, Norton Neo, Island, Ghost Browser, Horse, Shift | Mostly Chromium | Varies | See entries | Mostly subscription |

### One entry each

**Crest** (open source; most important finding). Engine: ungoogled-chromium by default, WebKit per site or page; WebKit takes over automatically for FairPlay video (FACT `crest:Documentation/ARCHITECTURE.md:3`). Standout ideas: each space owns a full engine profile with its own cookies, history, archive, passwords, and permissions (FACT `crest:Documentation/ARCHITECTURE.md:26-36`); Peek, Quick Window, link routing, and Split View with 2-4 pages (FACT `crest:README.md:62-71`); shared windows onto the same spaces with separate selection, and disposable "Blank Windows" that borrow a space's sign-in (FACT `ARCHITECTURE.md:44-54`); "Keep Loaded" per tab and a recoverable Archive (FACT `README.md:89`); Private Spaces that relock with Touch ID (FACT `README.md:87`); iCloud CloudKit sync with fractional ordering and tombstones (FACT `ARCHITECTURE.md:42`); Arc import of spaces, folders, splits, colours, icons, extensions, and passwords (FACT `crest:HelpCenter/docs/getting-started/move-to-crest.md:18`); an outside-agent MCP server shipped as a helper in the app bundle, with agents identified by macOS code signature (FACT `crest:HelpCenter/docs/browsing/coding-agents.md:27,57`). Maturity: "Early access. Security not independently audited" (FACT `crest:Website/index.html:603`). Very fast: 0.4 to 0.8.50 in 66 days. 92,023 lines of C# and 239,940 lines of Swift, 12,567 of them in test targets (FACT, `wc -l` at `838acaa`). Developed with coding agents: the repo ships agent instructions and a contribution skill that every AI-assisted pull request must follow (FACT `crest:AGENTS.md:1-15`).

**Stedding** (open source; rac's closest twin). A Chromium patch fork with Arc parity, on Chromium directly rather than ungoogled. Standout ideas: per-space sign-ins inside one profile, built on Chromium storage partitions with one upstream hunk (FACT `stedding:docs/decisions/0019-space-sessions-are-storage-partitions.md:29-58`); "Dark pages" that darken every site from the first frame (FACT `stedding:README.md:51-53`); web apps that keep their space's sign-in (FACT `README.md:54-57`); "Clear Site Cookies and Reload" (FACT `README.md:58-60`); sidebar sync through a folder the user's own sync tool carries, with no server (FACT `README.md:61-63`); tracking parameters stripped from links you open, not only copy (FACT `stedding:docs/features/clean-links.md:33`). No built-in AI: no bundled model, no default key, and Ask on Page and command-bar chat are listed as "never"; a later ADR could still allow an opt-in local or own-key feature (FACT `stedding:docs/decisions/0020-no-bundled-model.md:22-37`). Maturity: beta; many spec rows say "written, tests not yet run" (FACT, `docs/features/*.md`). 103 patches touching 504 upstream files with 3,086 upstream hunks (FACT, my count with `/tmp/rac-overhaul/count_patch2.py`), against rac's ~217 files and 869 hunks (FACT, `plans/research/rac-baseline.md`).

**Refrax** (open source, GPL-3.0, so code is license-compatible with rac). A Swift browser whose Chromium runs as its own app and shows pages in Refrax windows through remote layers (FACT `refrax:Engines/CONTRACT.md:326`). Only 7 Chromium patches, 22 files, 42 hunks, plus a 6,812-line overlay in 66 files (FACT, `wc -l` of `refrax:Engines/Chromium/refrax/` at `5e02009`). Engines speak a documented "events out, commands in" contract and are untrusted input: 256 KiB message cap, 8 KiB strings, close after 32 bad messages (FACT `refrax:Engines/CONTRACT.md:300-312`). Touch ID space locks; `refrax-ctl` CLI for scripts and agents (FACT `refrax:README.md:3-15`). Maturity: early; 48 stars; whether Chrome extensions work in its Chromium engine is unverified.

**Mori** (open source, MIT). Useful mostly as a cautionary history. Mori 2 was a SwiftUI overlay on Chromium; Mori 3 was Rust GPUI around CEF; on 2026-10-17 it moved to Chromium Views (FACT `mori:docs/archive/DECISIONS-linux-chromium.md:7-45`). It dropped CEF because extensions don't work, CEF ships only even milestones, every frame is copied, and nothing can be dragged out of a page (CLAIM, same file `:15-28`). It rejected a WebUI shell "as Vivaldi does" and Chromium's `kWebium` experiment (same file `:43-45`). Crest's native window code adapts Mori 2's (FACT `crest:CrestEngines/Chromium/ThirdParty/README.md`). The assistant talks to a local `codex app-server` (FACT `mori:docs/ARCHITECTURE.md`).

**Yalqen, Meridian, Tangent, Flow, Aura** (open source, small). Yalqen is a polished Electron developer browser with 100+ releases in a month. Meridian ships a built-in Claude assistant, an MCP server, and a terminal "Workbench"; it moved Claude Code and Gemini CLI into that terminal because "their terms don't allow apps to power features with a subscription login" (FACT that Meridian says this, in its README line 29; CLAIM as a reading of the terms; the v0.2.5 release notes say only that AI features "now follow each provider's terms"). Tangent has no releases. Flow has been quiet since April. Aura is archived. None changes rac's plans; Meridian's terms note matters (see Open questions).

**Floorp** (open source). A Firefox fork with nearly every power feature: workspaces, web panels, split view, tab stacks, PWAs, mouse gestures, a command palette, notes that export Markdown (FACT `floorp:browser-features/chrome/common/`, v12.20.0 notes). Two unusual ideas: installing Chrome Web Store extensions into Firefox by converting the CRX (FACT `floorp:browser-features/modules/modules/chrome-web-store/CRXConverter.sys.mts`), and "Floorp OS", a local HTTP automation server on port 58261 (FACT `os-server/server.sys.mts:68`). Floorp OS is off by default (FACT `floorp:static/gecko/pref/override.ini:90`), loopback-only, with an optional token that is empty by default (FACT `server.sys.mts:10,166-176`), and its event streams send `Access-Control-Allow-Origin: *` (FACT `server.sys.mts:595`). Maturity: mature, frequent releases.

**Min** (open source). Electron, minimal. "Tasks" are its spaces. Standouts: full-text search of pages you visited, automatic reader view, 1Password and Bitwarden autofill through their command-line tools (FACT `min:js/passwordManager/onePassword.js:45-72,192`), and macOS Handoff of the current page (FACT `min:main/main.js:449-451`). It uploads usage statistics with a client ID unless you turn it off (FACT `min:js/statistics.js:23,50-58`).

**Brave**. Chromium fork, MPL-2.0. Standouts for rac: built-in Containers since 1.92 (2026-07-02), the first Chromium browser to do it (FACT, brave.com/blog/containers; "first" is CLAIM, AlternativeTo); `brave-core` has ~135 container files (FACT, `gh api` tree); a documented trap and fix for restoring container tabs after restart (FACT, `brave-core:docs/containers/session_persistence.md`). The agent ("AI browsing") runs only in a separate built-in profile with its own cookies and logins; it is off by default behind a `brave://flags` entry, in early testing on all release channels since 2026-05-05 (FACT, brave.com/blog/ai-browsing). Crypto wallet and rewards are things rac will never do (`VISION.md`).

**DuckDuckGo browser** (open source, Apache-2.0). WebKit on Mac. Standouts: the Fire Button with "Fireproof" exceptions; a one-click "Use DuckDuckGo Without AI" button that turns off Duck.ai and AI answers (FACT, duckduckgo.com/updates); an optional global Option-Space Duck.ai prompt, off by default (FACT, same).

**Thorium and Supermium**. Thorium turns on PGO, LTO, and CPU-specific builds, plus JPEG XL and extra codecs (FACT, Thorium README lines 14-32). It skips milestones (2026 releases: M144, M150, M151, M152, M154, M156) and labels each one a beta (FACT, `gh api repos/Alex313031/thorium/releases`). Supermium keeps Chromium alive on Windows XP and is six majors behind (FACT, releases). Lesson: one-person Chromium forks fall behind fast. Neither is a Mac product.

**Ladybird**. A new engine with 8 full-time engineers (CLAIM). Alpha for Linux and macOS was promised for 2026 and has not shipped as of 2026-10-25 (CLAIM, ladybird.org; PiunikaWeb). Watch, don't plan around.

**Glide, qutebrowser, Nyxt**. Keyboard-first browsers. Glide's config is a TypeScript file that can run processes (CLAIM, launch post). Link hints on `f`. Niche; conflicts with rac's "few settings".

**Sidebery** (extension). Panels of tabs, bookmarks, or history; tree or flat; each panel can force a container for new tabs and auto-move tabs by URL rules (FACT `sidebery:src/defaults/panels.ts:68-71`); per-container proxy and user agent (FACT `src/defaults/containers.ts:10-15`); timed snapshots with auto-export to JSON or Markdown (FACT `src/defaults/settings.ts:220-226`).

**Tree Style Tab** (extension). Tabs opened from a page become its children; branches fold. A public API lets other add-ons extend the sidebar (FACT, README). It conflicts with other tab add-ons (FACT, Sidebery README).

**Arc** (closed; the baseline). Spaces with a profile per space; favorites with hover previews of Gmail, Calendar, GitHub, Linear and others (FACT, resources.arc.net "Previews"); auto-archive of unpinned tabs after 12 hours by default (CLAIM, MakeUseOf); Little Arc, Air Traffic Control, Peek, Split View, Boosts, Easels, Library, Live Folders, Arc Max (Ask on Page, 5-second previews, tidy titles and downloads) (CLAIM, gHacks 2023).

**Dia** (closed). Moving toward Arc since Arc's end: Arc-style pinned tabs (1.52, 10-08), "Swipeable Profiles" (1.43.1, 08-06), new tabs at the top "matching Arc's familiar tab order" (Windows 1.3.0), a "close unpinned tabs" button (1.52), Arc Live Folders imported as "Live Groups" with GitHub PR stacks (1.53), Skills and a Skills gallery, connectors to Slack, Notion, Gmail, Figma, Atlassian (FACT, diabrowser.com/changelog). It retired its Memory feature and deleted memory data in 1.50.0 (2026-09-24), saying newer models no longer need it (FACT, changelog). End-to-end encrypted sync since 2026-04-09 (CLAIM, Wikipedia).

**Vivaldi** (closed UI on open Chromium). The most features of any browser: workspaces, tab stacks, tiling, web panels, command chains, notes, mail, calendar, feeds. 8.0 made the UI one continuous frame with rounded page corners and six preset layouts (CLAIM, gHacks, OMG Ubuntu). Public stance since 2025-08-28: no LLM chatbot, summaries, or form-fill suggestions "until more rigorous ways to do those things are available" (FACT, vivaldi.com/blog/keep-exploring).

**Orion** (closed). WebKit that runs many Chrome and Firefox extensions (about 70% of the WebExtensions API, CLAIM). "Zero telemetry"; "no built-in AI code in its core" (FACT, Kagi blog "Orion 1.0"). Profiles as separate apps, Focus Mode, link preview. Orion+ perks include always-on-top floating windows (CLAIM, same post). Kagi stopped Linux and Windows work on 2026-10-02 to focus on Apple (FACT, blog.kagi.com).

**SigmaOS** (closed). WebKit; workspaces you mark done like a to-do list; "Airis" AI. Last build March 2026 (CLAIM). Reviews cite lag and weak extension support (CLAIM, Product Hunt).

**Sidekick** (closed, dead). App sidebar and sessions; shut down 2025-08-03 after Perplexity acquired the team (CLAIM).

**Wavebox** (closed). Spaces are cookie containers; "Groups" are permanent sidebar spots; a "Link Opening Engine" routes links to the right account by rules; Brainbox AI with your own OpenAI, Anthropic, or Ollama models and 11 built-in skills; an MCP server; split screen across spaces; per-space proxy with PAC files (CLAIM, hub.wavebox.io).

**Opera Air and Opera Neon** (closed). Air: break reminders (45-180 minutes, off by default), breathing exercises, binaural "Boosts", free VPN (CLAIM, 9to5Mac). Neon: free tier lets *your* agents drive it through a local CLI or an MCP server, with no built-in agent; Opera's own agents cost extra (FACT, blogs.opera.com 2026-08). Its MCP needs an Opera account (FACT, same post) and connects with OAuth2 through an Opera-built "persistent proxy server" that stays up while Neon is closed (FACT, blogs.opera.com 2026-03-31); the CLI needs no account (FACT, 2026-08-14 post). The CLI forks `chrome-devtools-axi` and claims up to 80% fewer tokens through compact snapshots and next-step hints (CLAIM `opera-browser-cli:README.md`). `opera-devtools-mcp` forks Google's `chrome-devtools-mcp`, Apache-2.0 (FACT, LICENSE).

**Chrome native vertical tabs**. Right-click a tab, "Show tabs vertically" (CLAIM, ChromeStory). Collapsible; groups are coloured headers; no workspaces (CLAIM, same). Expand-on-hover on by default from 156 (CLAIM). Split view reported around 2026-02 (CLAIM, unconfirmed). Gemini "auto browse" agent for US AI Pro and Ultra (CLAIM, MacRumors 2026-01-29). Since Chrome 144, `chrome-devtools-mcp --autoConnect` attaches to the user's running Chrome after a toggle at `chrome://inspect/#remote-debugging` (FACT, developer.chrome.com).

**Edge**. Vertical tabs since 2021, split screen in one tab, Workspaces. In 2026 Workspaces lost sharing and collaboration (FACT, Microsoft message MC1192661), Collections and the sidebar app list were removed in Edge 149 (CLAIM, Windows Latest quoting release notes), and Copilot Mode was folded into the normal UI on 2026-05-13 (CLAIM).

**Firefox**. Vertical tabs (136, 2025-03-04), tab groups (137-138, 2025-04), profiles with name, avatar, and colour (138, 2025-04-29), AI Controls with one "Block AI enhancements" switch that also keeps future AI features off (148, 2026-02-24), split view for two tabs (149, 2026-03-24), opt-in "Smart Window" AI mode (2026-08-18), compact mode back in a September 2026 redesign (FACT for 138 and 153 ESR release notes; others CLAIM from cited press).

**Safari**. Profiles and "Add to Dock" web apps that share no cookies with Safari (FACT, support.apple.com/en-us/104996); Distraction Control hides page items you pick, remembered per device (FACT, Apple Newsroom 2024-09); Liquid Glass in Safari 26; the compact tab bar was removed in 26.0 and restored in 26.4 after complaints (CLAIM, MacRumors).

**ChatGPT Atlas**. Runs Chromium's browser process outside the app ("OWL"), with a SwiftUI and AppKit UI; engineers get Chromium as a prebuilt binary, so builds take minutes (FACT, openai.com/index/building-chatgpt-atlas; the page returned 403 on re-check, so confirmed through search excerpts only). Vertical tabs, tab groups, agent mode, browser memories. OpenAI reportedly shut Atlas down on 2026-08-09 (CLAIM, en.wikipedia.org/wiki/ChatGPT_Atlas, citing Lifehacker and TechRepublic). It is now an architecture reference, not a competitor.

**Comet, Genspark, Fellou, Strawberry, Norton Neo**. Agent-first Chromium browsers. Comet is free with paid background agents. Genspark offers 169 on-device open-weight models and a 700-tool MCP store (CLAIM). Strawberry sells role "companions" that ask before critical actions (CLAIM). Norton Neo pairs AI with Norton's phishing shield (CLAIM). None is privacy-first or open.

**Island, Ghost Browser, Horse, Shift**. Island: enterprise Chromium with cloud policy, watermarking, session recording (CLAIM). Ghost: Chromium "identities", each a separate cookie jar in one window (CLAIM). Horse: tree-of-pages "Trails" instead of tabs, two developers, paid (CLAIM, MacStories). Shift: Electron mail-and-apps workstation. Each shows a niche, not a direction for rac.

**Pointers to other dossiers.** Zen, Nook, Ora, Ardia, Helium, BrowserOS, T3 Code: `plans/research/*.md`. Yab, Aside: `plans/context/`.

## Features

Inventory across the long tail. Status words: **shipped**, **beta**, **planned**, **removed**. "rac today" comes from `plans/research/rac-baseline.md` and `docs/roadmap.md` (built means merged on `main`, never released).

### Tabs, sidebar, spaces

| Feature | Who ships it (status) | rac today | Evidence |
| --- | --- | --- | --- |
| Native vertical tabs | Chrome (shipped, 146), Edge (shipped), Firefox (shipped, 136), Atlas (shipped), Dia (shipped), Vivaldi, Brave, Opera | Built (Helium's, restyled) | CLAIM, press cited above |
| Expand-on-hover collapsed sidebar | Chrome (default from 156, CLAIM), Firefox (shipped), Edge (shipped), Stedding (rail expands after a pause, FACT patch 0040), Floorp (overlay and hover controls, 12.20.0) | Not built: rac chose full or hidden only | `docs/internals/glossary.md`; Floorp notes |
| Separate sign-ins per space in one window | Arc (profile per space), Crest (engine profile per space), Stedding (opt-in storage partition per space, beta), Brave Containers (per tab, shipped 1.92), Wavebox Spaces, Orion 1.1 containers, Zen (containers), Ghost identities, Firefox Multi-Account Containers (extension) | **Not built.** One profile per window; spaces share cookies | FACT `stedding:docs/decisions/0019-...md`; brave.com/blog/containers; `crest:Documentation/ARCHITECTURE.md:26-36` |
| Swipe between profiles in one window | Dia "Swipeable Profiles" (shipped 1.43.1) | Swipe between spaces only | FACT, Dia changelog |
| Same space in two windows, separate selection | Crest (shipped), Stedding (one sidebar for every window, patch 0036), Arc | Not built; rac shows an "open in another window" screen | FACT `crest:README.md:68`; rac `spaces_window_manager.h:47-56` |
| Disposable window that borrows a space's sign-in | Crest "Blank Window" (shipped), Stedding "throwaway" (spec) | Not built | FACT `crest:Documentation/ARCHITECTURE.md:54` |
| Keep a tab loaded when its space hides | Crest "Keep Loaded" (shipped) | Hidden spaces unload after 15 min; only audio, PiP, loading tabs stay | FACT `crest:README.md:89`; rac `spaces_window_manager.h:65,134-137` |
| Recoverable archive of closed tabs | Arc (Library), Crest (Archive with retention), Stedding (archive view, patch 0028), Dia (close unpinned tabs button) | Not built; VISION rules out *auto*-archive | FACT `crest:README.md:89`; Dia 1.52.0 |
| "Clear" all open tabs in a space | Arc, Dia (1.52, sidebar button) | Not built | FACT, Dia changelog |
| New tabs at the top of the list (Arc order) | Dia (setting, Windows 1.3.0), Arc | Unverified; Chromium appends | FACT, Dia changelog; INFERENCE for rac |
| Abandoned new tab pages clear themselves when you switch apps or lock the screen | Dia (1.38.0, 2026-07-02) | Not built | FACT, Dia changelog |
| Tree tabs (children under opener) | Tree Style Tab, Sidebery, Horse "Trails", Vivaldi window panel, Floorp | Not built; not planned | FACT, READMEs |
| Tab stacks / accordion | Vivaldi, Floorp (`tab-stacks`) | Folders in pinned section only | FACT `floorp:browser-features/chrome/common/tab-stacks` |
| Auto-move tabs into a space by URL rule | Sidebery `moveRules`, Wavebox rules | Not built (ATC planned "Later") | FACT `sidebery:src/defaults/panels.ts:70` |
| Favorites hover previews (inbox, calendar, PRs) | Arc (shipped, Mac only) | Not built | FACT, resources.arc.net "Previews" |
| Live folders (GitHub PRs, feeds) | Arc, Dia "Live Groups" with PR stacks (shipped 1.53), Vivaldi feeds | Not planned (the roadmap revision rules out live folders) | FACT, Dia changelog; `roadmap-revision-2026-10-22.md` |
| Space themes with personality | Crest Studio heraldic crests per space (shipped), Zen gradients | Built: 8 colour themes, emoji or icon | FACT `crest:README.md:53` |
| Sidebar material thickness | Crest (Ultra Thin to Ultra Thick) | Not built | FACT, Crest 0.8.0 notes |

### Navigation and command bar

| Feature | Who ships it (status) | rac today | Evidence |
| --- | --- | --- | --- |
| One field for URL, search, open tabs, history, commands | Crest command palette (0.8), Stedding ⌘T plus ⇧⌘P actions list, Vivaldi Quick Commands, Floorp, Flow, Yalqen, Dia | Planned (phase 5 command bar) | FACT, Crest CHANGELOG 0.8.0; Stedding README |
| Tab to search a site or ask an AI from the bar | Crest (0.8), Ora (dossier), Dia | Bangs inherited from Helium | FACT, Crest CHANGELOG |
| Ctrl+Tab recent-tabs switcher in Arc's layout | Dia (1.51, capped at 5 tabs) | MRU cycling on; visual switcher unverified | FACT, Dia changelog |
| Rebindable shortcuts | Crest, Dia, Vivaldi, Floorp, Glide | Helium's shortcut system | FACT, changelogs |
| Address-bar calculator | Vivaldi 8.2 | Unverified | CLAIM, Releasebot |
| Copy link as Markdown | Crest page tools | Not built | FACT `crest:README.md:79` |
| Strip tracking parameters from links you *open* | Stedding (coded, unbuilt), Brave, Safari private browsing | Proposed for *copy* only | FACT `stedding:docs/features/clean-links.md:11-12,33` |
| Link routing to a space (Air Traffic Control) | Arc, Crest (shipped), Stedding (patch 0027), Wavebox (shipped), Refrax (shipped) | Later | FACT `crest:HelpCenter/docs/browsing/link-routing.md` |

### Split view, peek, small windows

| Feature | Who ships it (status) | rac today | Evidence |
| --- | --- | --- | --- |
| Split view | Edge, Firefox (2 tabs), Crest (2-4), Zen (4), Vivaldi tiling, Wavebox (across spaces), Chrome (CLAIM, unconfirmed), Brave (containers in split) | Inherited from Helium | cited above |
| Peek for links | Arc, Crest, Stedding, Zen, Nook, Norton Neo | Not planned in VISION; Zen dossier proposes it | FACT `crest:README.md:66` |
| Little window for links from other apps | Arc, Crest Quick Window, Stedding (patch 0035), Mori "Little Mori" | Later | FACT, READMEs |
| Sign-in popups open as small windows over their opener | Crest (shipped) | Chromium popup windows | FACT `crest:Documentation/ARCHITECTURE.md:60` |
| Always-on-top floating window | Orion+ (paid) | PiP only | CLAIM, Kagi blog |
| PiP: stash at screen edge; click domain to return | Dia (1.36, 1.46) | Auto-PiP built | FACT, Dia changelog |

### Import, sync, profiles

| Feature | Who ships it (status) | rac today | Evidence |
| --- | --- | --- | --- |
| Arc import with spaces | Crest (spaces, folders, splits, colours, icons, extensions, passwords), Stedding (patch 0026, 0038), Dia, Zen, Ardia, Meridian (CLAIM) | Planned (phase 5) | FACT `crest:HelpCenter/docs/getting-started/move-to-crest.md:18`; `crest:CrestCore/src/CrestCore/Application/Portability/ArcSidebar.cs` |
| Import from Dia, Comet, Aside, Brave, Edge, Vivaldi, Opera | Crest 0.8 | Chromium importer only | FACT, Crest CHANGELOG 0.8.0 |
| Portable export of the whole browser | Crest archive (no passwords, cookies, or site data), Stedding sidebar file | Not built | FACT `move-to-crest.md:37-39` |
| Sync with no vendor server | Stedding (a file in a folder your own tool syncs, beta), Crest (your private CloudKit database), Sidebery (Firefox sync storage or Google Drive) | Not planned | FACT `stedding:docs/features/sidebar-file.md`; `crest:Documentation/ARCHITECTURE.md:42`; `sidebery:src/services/google.drive.ts` |
| Vendor E2E sync | Dia (2026-04-09), Vivaldi, Wavebox | — | CLAIM |
| Timed snapshots and backups | Sidebery (interval, auto-export JSON or Markdown), Firefox 153 (profile backup and restore), Zen (dossier) | Not built | FACT `sidebery:src/defaults/settings.ts:220-226`; Firefox 153 ESR notes |
| Profile manager with avatar and colour | Firefox 138 | Chromium's profile picker | FACT, Firefox 138 notes |
| Handoff of the current page to iPhone | Min, Chromium on Mac | Inherited (Chromium has `components/handoff`); unverified in Helium | FACT `chromium:components/handoff/handoff_manager.mm` |

### Privacy and blocking

| Feature | Who ships it (status) | rac today | Evidence |
| --- | --- | --- | --- |
| Clear one site's cookies and reload | Stedding (⌥⇧⌘R), DuckDuckGo Fire Button (whole browser, with Fireproof exceptions) | Built: site control center "…" has Clear cookies | FACT `stedding:README.md:58`; rac baseline |
| Lock a space with Touch ID | Crest Private Spaces, Refrax | Not built | FACT `crest:README.md:87`; `refrax:README.md:3` |
| Force dark mode for every site, no white flash | Stedding "Dark pages" (beta), Vivaldi page actions, Orion Page Tweak | Not built | FACT `stedding:docs/features/dark-pages.md:36,42` |
| Hide distracting page items, remembered per site | Safari Distraction Control (shipped), Arc Boosts "Zap" | Boosts planned | FACT, Apple Newsroom 2024-09 |
| One "no AI" master switch | Firefox 148 AI Controls (also blocks *future* AI features), DuckDuckGo "Use Without AI" | AI off by default; no single page listing every AI surface | FACT, Firefox 148 coverage; duckduckgo.com/updates |
| Zero telemetry | Orion, Crest, Stedding, Vivaldi (CLAIM each) | Built (nothing to rac) | Kagi blog; `crest:Website/privacy/` |

### AI assistant

| Feature | Who ships it (status) | rac today | Evidence |
| --- | --- | --- | --- |
| Chat about the page and @-mentioned tabs | Dia, Atlas, Comet, Edge, Wavebox Brainbox, Meridian, Opera, Brave Leo, Firefox Smart Window | Built | changelogs |
| Bring your own key or local model | Wavebox (OpenAI, Anthropic, Ollama), Meridian (Ollama, LM Studio), Brave Leo (BYOM, CLAIM), Genspark (169 local models, CLAIM) | Built (7 providers + ACP agents) | cited |
| Skills: saved prompts users share | Dia (gallery), Wavebox (11 built in), Opera Neon | Saved prompts built | FACT, Dia changelog |
| Memory | Atlas (memories; Atlas itself reportedly closed 2026-08-09), Dia (**removed** 2026-09-24) | Not built | FACT, Dia 1.50.0 |
| Connectors to SaaS (Slack, Notion, Gmail, Figma) | Dia, Genspark, Wavebox | Not built | FACT, Dia changelog |
| On-device router choosing search or chat | Dia (1.50.0) | Built (local intent on NTP) | FACT |
| No AI by stated policy | Vivaldi, Orion core, Stedding | AI optional | FACT, vivaldi.com/blog/keep-exploring; Kagi blog |

### Agent

| Feature | Who ships it (status) | rac today | Evidence |
| --- | --- | --- | --- |
| Built-in agent acting in your signed-in tabs | Atlas, Comet, Chrome auto browse, Edge, Opera Neon (paid), Strawberry, Fellou, Genspark, Dia | Built (`auto` default) | cited |
| Agent only in a separate, logged-out profile | Brave AI browsing (early access, flag) | Not built | FACT, brave.com/blog/ai-browsing |
| Outside agents drive the browser over MCP | Crest (shipped, per space), Opera Neon free tier, Wavebox, Meridian, Yab, Aside, Chrome via `chrome-devtools-mcp --autoConnect` | MCP only for the agent rac launches | FACT `crest:HelpCenter/docs/browsing/coding-agents.md`; Opera blog |
| Agent identity checked by code signature | Crest | Not built | FACT `crest:CrestMac/Infrastructure/Agents/BrowserAgentPeer.swift:64-80` |
| Agent badge, colour outline, visible pointer | Crest (pointer glides 0.35 s) | Tab ring and pill | FACT `BrowserWebPageSurfaceMetrics.swift:55` |
| CLI for scripts and agents | Refrax `refrax-ctl`, Opera Browser CLI, Yab | None | FACT, READMEs |
| Local HTTP automation API | Floorp OS (off by default) | None | FACT `floorp:.../os-server/server.sys.mts` |

### Extensibility

| Feature | Who ships it (status) | rac today | Evidence |
| --- | --- | --- | --- |
| Chrome Web Store extensions | All Chromium browsers; Orion (WebKit, partial); Floorp (CRX conversion into Firefox) | Inherited | FACT, cited |
| Per-space extensions | Crest (engine profile per space) | Per profile | FACT `crest:CHANGELOG.md` 0.7.0 |
| Sidebar API for other extensions | Tree Style Tab | None | FACT, TST README |
| Userscripts | Min, Floorp | Boosts planned | FACT `min:README.md` |
| Config as code | Glide (TypeScript), Nyxt (Lisp), qutebrowser (Python) | None | CLAIM |
| Password manager CLIs (1Password, Bitwarden) | Min | 1Password "Later" | FACT `min:js/passwordManager/` |

### Other

| Feature | Who ships it (status) | rac today | Evidence |
| --- | --- | --- | --- |
| On-device page translation inside Chromium | Crest (Apple Translation, 0.8.50) | Phase 6 idea | FACT, Crest CHANGELOG 0.8.50 |
| Developer toolbar on localhost (viewports, capture) | Crest, Arc developer mode, Stedding local tabs | None | FACT `crest:README.md:81` |
| Screenshot of page or region | Stedding (patch 0014), Vivaldi, Crest | Inherited share-menu tools only (unverified) | FACT, Stedding patches |
| Web apps in the Dock | Safari, Orion, Stedding (keep the space's sign-in), Floorp, Vivaldi 8.2 | Chromium's "install page as app" (unverified in Helium) | FACT, support.apple.com/en-us/104996 |
| Break reminders and focus sounds | Opera Air | — | CLAIM |
| Mail, calendar, feeds, notes | Vivaldi, Floorp (notes) | Notes "Later" | CLAIM |

## UI, look, and feel

### Layout

- **The big four converged on Arc's layout, but plain.** Chrome, Edge, and Firefox (and Atlas, before its reported shutdown) all offer a left vertical tab list with collapsible groups (CLAIM, press cited in Snapshot). None has spaces with their own colour, pinned tabs that reset, or a hidden-sidebar mode as complete as Arc's. INFERENCE: rac's differentiation is spaces, pinned-tab behaviour, motion, and privacy, not "vertical tabs".
- **Hover-expanding rails are now the default elsewhere.** Chrome 156 expands a collapsed rail on hover by default (CLAIM, ChromeStory); Firefox, Edge, Floorp 12.20, and Stedding have rails. rac decided against an icons-only rail (FACT, `docs/internals/glossary.md`). That decision is defensible for calm, but Arc users who used Arc's narrow sidebar will look for it. INFERENCE.
- **Pages framed as cards with rounded corners** are the 2026 house style: Vivaldi 8 "Unified" frames page content with rounded corners on one continuous surface (CLAIM, OMG Ubuntu); Crest's page corners follow the window's corners (FACT, Crest 0.8.0 notes); Arc and Zen did it first. rac already has a page card (FACT, rac baseline `look/`).
- **Settings inside the browsing canvas, not a separate tab.** Crest shows Settings in the page area at regular width and as a sheet at compact width (FACT `crest:Documentation/ARCHITECTURE.md:90`). INFERENCE: worth copying for a calm feel; rac uses Chromium's WebUI settings tab.
- **Layout presets instead of dozens of toggles.** Vivaldi 8 ships six preset layouts (CLAIM); Crest's Appearance starts from presets and can reset single settings (FACT `crest:README.md:55`). This fits rac's "opinionated" rule better than Floorp's or Vivaldi's long settings pages. INFERENCE.

### Visual language, materials, typography

- **Native materials.** Crest lets users pick the sidebar's material from Ultra Thin to Ultra Thick, and floating panels (Site Controls, Peek, notices) use the sidebar's material (FACT, Crest 0.8.0 notes). Safari 26 uses Liquid Glass, with a later "tinted" option that makes it more opaque (CLAIM, MacRumors). Dia matched sidebar typography to macOS (FACT, Dia Windows 1.2.0). INFERENCE: rac's Views UI draws its own fills; true vibrancy needs an `NSVisualEffectView` under the sidebar, which is a known Chromium-on-Mac technique but untested in rac.
- **Personality per space.** Crest Studio builds a heraldic crest per space from shape, field, band, emblem, border, and finish, each with its own colour (FACT `crest:README.md:53`). Crest's 0.8.50 setup asks whether spaces use banners and crests or "a modern gradient and icon" (FACT, CHANGELOG). This is the most Arc-like playfulness found in the sweep. INFERENCE.
- **A private window "wears a different coat"** (FACT, Stedding patch 0034 title). Small, clear signal.

### Motion (exact values from code)

Crest names motion by role, routes every animation through a reduce-motion gate, and keeps durations short (FACT `crest:CrestShared/DesignSystem/Tokens/CrestMotion.swift:1-121`):

| Role | Duration | Curve | Source line |
| --- | --- | --- | --- |
| Hover | 0.14 s | `.easeInOut` | `CrestMotion.swift:67,145` |
| Press feedback | 0.14 s (compact 0.12 s) | `.easeOut` | `:25-27` |
| Surface, content reveal | 0.12 s | `.easeInOut` (surface), `.easeOut` (content reveal) | `:31,89,125,169-170` |
| Palette open | 0.18 s | `.easeInOut` | `:91,172` |
| Dismissal | 0.18 s | `.easeOut` | `:65` |
| Disclosure, selection | 0.20 s | `.snappy` (disclosure), `.easeInOut` (selection) | `:69,73,146,150` |
| Collection change | 0.22 s | `.snappy` | `:33` |
| Sidebar dock approach / attach | 0.22 s / 0.16 s | `.smooth` | `:43-45` |
| Floating pane, toolbar | 0.24 s | `.smooth` / `.snappy` | `:61-63` |
| Sidebar morph, chrome | 0.28 s | `.smooth` | `:39-41`, `:131` |
| Sidebar retreat | 0.30 s | `.smooth` | `:47` |
| Space swipe | 0.32 s | `.snappy`, no extra bounce | `:81`, `:159` |
| Quick Peek entrance | 0.34 s | `.smooth` | `:87`, `:167` |
| Boundary shake (no more spaces) | 0.36 s | — | `:83` |
| Reduced motion | 0.20 s cross-fade | — | `:85` |
| Download "flight" to the toolbar | spring, duration 0.68 s, bounce 0.16 | spring | `crest:CrestShared/Features/Utilities/BrowserUtilityListContent/Models/BrowserDownloadFeedbackPresentation.swift:11` |
| Agent pointer glide | 0.35 s | `.smooth` | `crest:CrestMac/.../BrowserWebPageSurfaceMetrics.swift:55` |

Stedding measured Chromium's own curves in Views and changed them (FACT `stedding:docs/features/motion.md:22-23`):

- Chromium's "emphasized" curve moved the collapsing sidebar 33% of the way, 88 DIP, in one frame at 120 Hz. Stedding switched sidebar collapse, expand, and hover overlay to `gfx::Tween::EASE_OUT` at Chromium's Mac times: 350 and 400 ms, and 200 and 250 ms for hover. Its largest step became 7-14% per frame.
- A space switch keeps the departing space as a paint *recording* rastered by the compositor, not a bitmap rastered on the UI thread. Rasterizing had cost 4.6-8.8 ms with ten rows; recording costs 0.7 ms; the whole switch fell from 18-22 ms to 13-14 ms.
- A frame-by-frame test (`MotionFramesTest`) logs how many views were laid out and painted per frame and how long each took.

INFERENCE: both are directly usable in rac. Stedding's are measured in the same toolkit rac uses (Views on Chromium for Mac). Crest's give target durations for a native feel.

### Signature interactions that feel great

- **Downloads that fly** to their button on a 0.68 s spring (FACT, Crest). Cheap delight on a rare event, so it never repaints continuously.
- **Space swipe that wraps around** from the last space to the first, with a boundary shake when wrap is off (FACT, Crest 0.8.50 notes; `CrestMotion.swift:83`).
- **Sideways mouse-wheel scroll over the sidebar** changes space, one per notch (FACT, Stedding README "New in 0.3"). Works for mouse users who lack a trackpad swipe.
- **Pinned tab ⌘W returns it to its pinned page, asleep, in place** (FACT, Stedding README). rac already does this (FACT, `docs/internals/pinned-tabs.md:93-118`).
- **Agent pointer in the agent's colour** with a named bar on the page (FACT, `crest:HelpCenter/docs/browsing/coding-agents.md:33-34`). Makes outside agents legible.
- **Arc favorites previews**: hover Gmail to see unread mail, hover Calendar for the next meeting and a "join" button (FACT, resources.arc.net). Arc users cite this as a daily habit (CLAIM, reviews).

### Things that feel bad

- **Removing a layout people use.** Safari 26 removed the compact tab bar, then restored it in 26.4 (CLAIM, MacRumors). Edge removed Collections and the sidebar app list in 149 and users reported lost data (CLAIM, Windows Latest; Microsoft Q&A threads). Lesson for rac: removing Helium's icons-only state is fine before release, but don't remove things after users depend on them. INFERENCE.
- **Setting sprawl.** Floorp, Vivaldi, and Sidebery offer hundreds of options (FACT, their settings files). Users praise power, reviewers call Vivaldi 8 "eye candy" with no new features (CLAIM, gHacks comments).
- **Lag and glitches in small WebKit browsers.** SigmaOS reviews cite lag and broken SSO (CLAIM, Product Hunt). Orion users cite extension gaps (CLAIM).
- **Agent-first chrome everywhere.** Edge replaced its Copilot button with "a more prominent Chat interface" (CLAIM). Vivaldi's 95% "no" from its users on AI features (CLAIM, OtonTechnology) suggests a sizeable group wants AI out of sight. rac's "AI off by default" fits them.

## Architecture

### How the long tail integrates an engine

| Model | Who | Upstream footprint | UI technology | Gains | Costs |
| --- | --- | --- | --- | --- | --- |
| **Patch series, UI in Chromium Views** | rac, Stedding, Mori (since 2026-10-17), Helium, Brave, Thorium, Supermium | rac ~217 files / 869 hunks; Stedding 504 files / 3,086 hunks (FACT, my counts) | C++ Views | Every Chromium feature and Chrome UI (permission bubbles, extension popups, DevTools) for free | Rebase every two weeks; Views motion is tween-based; vibrancy and springs are hand-built |
| **Native shell in Chromium's process, own `BrowserWindow`** | Crest | `native-host.patch`: 95 files, 205 hunks, plus a 14,406-line overlay; 4,963 lines of Swift engine glue (FACT, my counts) | SwiftUI + AppKit, C# core over a C ABI | SwiftUI motion and materials; spaces with separate Chromium profiles in one window; the same UI drives WebKit too | Chrome's own UI has to be re-hosted piece by piece: Crest patches permission prompts, extension install dialogs, login prompts, PiP overlay, translate bubble, autofill (FACT, `+++` list of `native-host.patch`) |
| **Chromium out of process, pages shown through remote layers** | ChatGPT Atlas "OWL" (closed), Refrax (open, GPL-3.0) | Refrax: 7 patches, 22 files, 42 hunks, plus a 6,812-line `//refrax` overlay (FACT, my counts) | SwiftUI / AppKit | App starts before Chromium; a Chromium hang or crash leaves the UI alive; engineers can use a prebuilt engine (FACT/CLAIM, openai.com OWL post) | Every interaction crosses IPC; extension UI, input, accessibility, drag and drop must be bridged; two signed apps (INFERENCE) |
| **Chromium's own HTML browser UI** | Chromium `kWebium` experiment (off by default); Vivaldi's UI is web tech (CLAIM, Mori record) | Upstream-owned | WebUI (HTML, CSS, TS) | CSS springs, fast iteration | Experimental; memory and startup cost (INFERENCE) |
| **CEF embedding** | Mori 3 (retired), Refrax interim engine | Small | Any | Easy embedding | No Chrome extensions, even milestones only, offscreen copies every frame (CLAIM, `mori:docs/archive/DECISIONS-linux-chromium.md:15-28`) |
| **Electron** | Min, Flow, Yalqen, Meridian, Tangent | None | HTML/JS | Fastest to build | Chromium lags Electron's schedule; Chrome extension support partial; feels like a web app (INFERENCE) |
| **Gecko fork or extension** | Floorp, Glide, Firefox; Sidebery, Tree Style Tab | Firefox patches or none | HTML/CSS/JS | Containers, CSS-built UI | Firefox add-ons, not Chrome's |
| **WebKit, native** | Orion, SigmaOS, DuckDuckGo, Safari, Aura (and Nook, Ora, Yab) | None | Swift | Small, energy-efficient, Apple features | Engine updates only with macOS; Chrome extensions need shims |
| **Two engines** | Crest, Refrax | Both of the above | Swift | Per-site fallback (FairPlay, Reader, translation) | Two test surfaces; sign-ins don't carry across engines (FACT, Crest 0.7.0 "Upgrading") |
| **New engine** | Ladybird | — | Qt / AppKit / GTK front ends | Independence | Not usable yet |

### Details worth knowing

- **Crest's control plane.** Every state change is an intent object (`core.send(OpenTab(...))`) and the UI reads only `core.state`; a grep for `core.send(` lists every state change the UI can make (FACT `crest:Documentation/Architecture/CoreArchitecture.md:36-58`). Engines report a `PageSnapshot` at most once per run-loop turn (FACT `crest:Documentation/ARCHITECTURE.md`, "Engine boundary"). INFERENCE: the same "intents in, snapshots out" discipline would help rac's agent and any outside-agent API, whatever the UI toolkit.
- **Crest's native host is launched in a mode.** `native-host.patch` selects Crest's window only with `--crest-control-plane`; the stock Chromium UI stays the default for review builds (FACT `crest:CrestEngines/Chromium/README.md:143-144`). The product bundle resolves its own engine data directory in `main` before Chromium loads, and moves only its own `Crest-*` profiles out of the shared `~/Library/Application Support/Chromium` folder (FACT, same file `:184-200`).
- **Refrax treats the engine as untrusted.** Messages over 256 KiB are rejected, strings capped at 8 KiB, a page sending 32 bad messages is closed, and engines get no keychain or history (FACT `refrax:Engines/CONTRACT.md:300-312`). Its Chromium engine runs the browser process as "Refrax Chromium Host.app" (FACT `refrax:Engines/Chromium/args.gn:7`). Patches let Chromium's message pump attach to Refrax's own `NSApplication` run loop (FACT `refrax:Engines/Chromium/patches/README.md`).
- **Mori's three rewrites in five months** (SwiftUI overlay, then Rust GPUI with CEF, then Views) ended on Views because Chromium owns the window, extensions need Chrome's browser layer, and CEF trails releases (FACT/CLAIM `mori:docs/archive/DECISIONS-linux-chromium.md:11-45`). INFERENCE: a strong data point that "native shell" rewrites are expensive even for small products.
- **Per-space cookie jars are possible in a normal Chromium window.** The Zen dossier says "Chromium has no per-tab cookie jar in a normal window" (`plans/research/zen.md:716-717`, tagged INFERENCE). That is wrong. Brave 1.92 ships Containers per tab (FACT, brave.com/blog/containers), and Stedding opens an isolated space's tabs with `SiteInstance::CreateForFixedStoragePartition` against `StoragePartitionConfig::Create(context, "spaces", profile_id, false)`, with one upstream hunk in `browser_navigator.cc` (FACT `stedding:docs/decisions/0019-...md:37-55`). Known trap: Chromium's session restore drops the partition, so a restored tab would land in the default jar. Brave fixes it by writing a virtual URL prefix `containers+<uuid>:` into the saved navigation entry and page state (FACT, `brave-core:docs/containers/session_persistence.md`). Another limit: `chrome.cookies` without a partition sees only the default jar, so cookie extensions miss isolated spaces (FACT, Stedding ADR 0019 `:58`).
- **rac's Chromium already contains two things the architecture thread should know about.** (1) `chrome/browser/ui/webui_browser/` with `kWebium`, disabled by default (FACT `chromium:chrome/common/chrome_features.cc:1966`). (2) `kDevToolsAcceptDebuggingConnections`, enabled by default on macOS, which lets a user turn on remote debugging in a running browser from `chrome://inspect` (FACT `chromium:chrome/browser/devtools/features.cc:203-211`; `chromium:chrome/browser/ui/webui/inspect/inspect_ui.cc:682-694`). Neither Helium nor rac patches it (FACT, grep of `patches/` and `helium-chromium/patches` found nothing). See Agents and AI.
- **Code sizes.** Crest: 92,023 lines of C# and 239,940 lines of Swift, 12,567 of them in test targets (FACT, `wc -l` at `838acaa`). Stedding: 581 new files in its patches (FACT). Refrax: about 10.7 MB of Swift by GitHub's language bytes (FACT, `gh api languages`). Floorp: TypeScript modules on Deno and Vite over a Firefox runtime (FACT `floorp:deno.json`, `browser-features/`).

## Data and storage

| Product | What is stored, where, in what format | Keys and secrets | Sync and servers | What leaves the machine by default |
| --- | --- | --- | --- | --- |
| Crest | Browser state in one SQLite file holding JSON-backed records, owned by the C# core (FACT `crest:CrestCore/README.md:12`); Chromium engine data in `~/Library/Application Support/Crest/Chromium` (FACT `crest:CrestEngines/Chromium/README.md:184-186`); agent sockets in `~/Library/Application Support/Crest/Agents` (FACT `crest:CrestAgents/AgentSocketLocation.swift:26`) | Passwords in the macOS Keychain, matched by origin and space; reveal and export need device authentication (FACT `crest:Documentation/ARCHITECTURE.md`, "Credentials and privacy") | Optional iCloud sync to the user's private CloudKit database; fractional ordering, deterministic merge, deletion tombstones; passwords never enter CloudKit (FACT `ARCHITECTURE.md:42`; `crest:Website/privacy/index.html`) | Nothing to Crest; Sparkle update checks to GitHub; Chrome Web Store extension updates go to Google (FACT, privacy page). Says it *may* later add a fixed search "source" parameter (FACT `privacy/index.html:142`) |
| Stedding | Spaces registry in the profile; a portable sidebar file (Arc's own JSON shape plus extras) for export and import; sync through a user-picked folder (FACT `stedding:docs/features/sidebar-file.md`) | Chromium's | No Stedding server; "Stedding never talks to Syncthing or iCloud" (FACT, same file) | Publishes a **recorded run** of every host a fresh profile contacts, taken from Chromium's network log; it found Google push check-ins and an account check and removed them (FACT `stedding:docs/PRIVACY.md:72-95`) |
| Brave Containers | Each container is a storage partition `("containers", <uuid>)` inside the profile; restored tabs keep it through a `containers+<uuid>:` prefix in saved navigation entries (FACT, `brave-core:docs/containers/session_persistence.md`) | Profile's | Brave Sync carries container tabs (FACT, same doc) | — |
| Sidebery | Panels, snapshots in extension storage; optional auto-export to `Downloads/Sidebery/snapshot-%Y.%M.%D-%h.%m.%s` as JSON or Markdown (FACT `sidebery:src/defaults/settings.ts:220-226`) | — | Firefox sync storage or Google Drive (FACT `sidebery:src/services/google.drive.ts`) | Nothing unless sync is set up (INFERENCE) |
| Min | Settings and history in Electron storage; full-text page index for history search (FACT, README) | 1Password and Bitwarden through their CLIs (FACT `min:js/passwordManager/`) | None | **Usage statistics** with a client ID, install time, OS, language, version to `services.minbrowser.org` unless turned off (FACT `min:js/statistics.js:23,50-58`) |
| Floorp | Firefox profile | Firefox's | Firefox Sync | Optional local server for automation, off by default (FACT `floorp:static/gecko/pref/override.ini:90`) |
| Edge Workspaces | Moved in 2026 from OneDrive and SharePoint to Edge Sync; sharing removed (FACT, Microsoft MC1192661) | Microsoft account | Microsoft | Users reported workspaces lost in the migration and recovered 95-97% by hand (CLAIM, Microsoft Q&A threads) |
| Dia | Memory data **deleted** in 1.50.0 (FACT, changelog) | — | E2E-encrypted sync since 2026-04-09 (CLAIM) | AI requests to The Browser Company's providers (INFERENCE) |
| Orion | WebKit stores | — | iCloud-free; Kagi account optional | "Zero telemetry" (CLAIM, Kagi blog) |
| Opera Neon | — | — | Its MCP needs an Opera account and OAuth2 and runs through an Opera-built persistent proxy server; the CLI works without an account (FACT, Opera blogs 2026-03-31 and 2026-08-14) | MCP traffic between the agent and Neon passes Opera's proxy (FACT that the proxy exists; INFERENCE that page data transits it); the CLI path stays local (INFERENCE) |
| Firefox | Profiles with name, avatar, colour; profile backup and restore in 153 ESR (FACT, 138 and 153 ESR notes) | — | Firefox Sync | Telemetry on by default (widely documented; not re-checked here) |

Patterns worth noting (INFERENCE unless tagged):

- **Server-free sync is a real, shipped pattern.** Crest uses the user's own CloudKit database; Stedding uses a folder the user's own sync tool carries. Neither runs a server. rac's "Sync (maybe later)" can choose between these without breaking "no rac servers". Crest's merge rules (fractional positions, tombstones, refusing stale merges) are the hard part (FACT `crest:Documentation/ARCHITECTURE.md:42,50`).
- **Portable exports deliberately leave secrets out.** Crest's archive excludes passwords, cookies, site storage, permissions, downloads, favicons, and extensions; password export is a separate, authenticated, plaintext operation (FACT `crest:HelpCenter/docs/getting-started/move-to-crest.md:37-39`).
- **Migrations lose data.** Edge Workspaces' 2026 move cost some users their workspaces (CLAIM). Zen's dossier ranks automatic backups first for the same reason (`plans/research/zen.md`, Take 1).
- **A "recorded run" turns a privacy promise into a test.** Stedding's table is the only one in the sweep that shows, host by host, what a fresh profile contacted, with before-and-after runs (FACT `stedding:docs/PRIVACY.md:72-95`).

## Agents and AI

### Where agents run, and whose agent it is

| Product | Built-in agent | Outside agents | Where the model runs | Evidence |
| --- | --- | --- | --- | --- |
| Crest | None | Yes: MCP server as a helper inside the app bundle, stdio, per space | The user's own agent | FACT `crest:HelpCenter/docs/browsing/coding-agents.md:57-60` |
| Opera Neon | Paid ("Do", "Make", research, Skills) | Free: local Opera Browser CLI, or MCP with an Opera account | Opera's cloud for its agents; user's for theirs | FACT, Opera blog 2026-08-14 |
| Brave | "AI browsing", early access, opt-in flag | — | Brave's Leo models | FACT, brave.com/blog/ai-browsing |
| Chrome | Gemini "auto browse" (US AI Pro and Ultra) | `chrome-devtools-mcp --autoConnect` (Chrome 144+) | Google's cloud | CLAIM, MacRumors; FACT, developer.chrome.com |
| Wavebox | Brainbox chat with 11 skills; can change Wavebox settings | MCP | User's key, Ollama, or bundled models | CLAIM, hub.wavebox.io |
| Meridian | Claude assistant | MCP server; other CLIs as text-only, in an empty folder | User's key or local | CLAIM, Meridian releases |
| Mori | Assistant | — | A local `codex app-server` process | FACT `mori:docs/ARCHITECTURE.md` |
| Floorp | — | Local HTTP API, off by default | — | FACT `floorp:.../os-server/server.sys.mts` |
| Dia | Yes (1.49.0 "separated" agent context handling "from execution, reducing duplicated cleanup work": an internal cleanup, not a stated safety feature) | — | The Browser Company's providers | FACT, Dia changelog |
| Comet, Edge, Fellou, Strawberry, Genspark (Atlas until its reported 2026-08-09 shutdown) | Yes | Genspark: 700-tool MCP store (CLAIM) | Vendor cloud; Genspark also on-device | CLAIM |
| Vivaldi, Orion core, Stedding | None, by policy | Orion: "will connect to AI tools users pick" (CLAIM) | — | FACT, vivaldi.com; Kagi blog; Stedding ADR 0020 |

### Page representation and tools

- **Crest** exposes 29 tools (FACT, 29 distinct `name:` entries in `crest:CrestAgents/AgentToolDefinition*.swift`): `identify`, `list_spaces`, `list_tabs`, `take_snapshot` (element `uid`s), `click`, `hover`, `fill`, `scroll`, `open_tab`, `navigate`, `show_tab`, `close_tab`, `screenshot`, `type_text`, `press_key`, `wait_for`, `list_console_messages`, `list_network_requests`, `get_network_request`, `evaluate_script`, `read_page_text` (Markdown without any form value), `handle_dialog` (never "leave page?"), `search_history`, `delete_history`, `list_search_providers`, and four window openers (FACT `coding-agents.md:60-77`). The shape follows `chrome-devtools-mcp`. On WebKit pages, input arrives as script events that some pages ignore (FACT, same doc).
- **Opera Browser CLI** returns a compact accessibility snapshot with `uid=N` refs and a "help" line suggesting the next command (FACT `opera-browser-cli:README.md`, Quick Start). It claims up to 80% fewer tokens than raw MCP (CLAIM, same).
- **Floorp OS** serves `/instances/:id/ax-tree`, `/text`, `/html`, `/screenshot`, `/click`, `/input`, `/cookies` and more over loopback HTTP (FACT, route strings in `floorp:browser-features/modules/modules/os-server/`).
- rac today: snapshot with refs, 15 tools, 25-call cap (FACT, rac baseline).

### Permissions and safety

- **Crest identifies the connecting program by what macOS vouches for, not what the agent says.** It reads the peer's audit token from the Unix socket (`LOCAL_PEERTOKEN`), checks that the peer is Crest's own signed helper, then walks up to four parent processes to find the first non-shell program and reads its Team ID and signing identifier with `SecCodeCopyGuestWithAttributes` and `SecCodeCopySigningInformation` (FACT `crest:CrestMac/Infrastructure/Agents/BrowserAgentPeer.swift:64-137`). Interpreters (`node`, `python`, `bun`, `uv`, `npx`, `osascript`, and others) vouch for nothing, so their key also includes the name the agent gives (FACT, same file `:48-52`). The doc is honest that this "is not a defense against harmful software already on your Mac" (FACT `coding-agents.md:50`).
- **Crest's reach limits.** Only spaces the user turned on; a locked space shows its name and nothing else; never private windows, browser pages, or files; only `http`, `https`, and blank pages; password field values omitted; cookies and sign-in headers hidden from network reads; request and response bodies never shown; page-world scripts only behind a separate toggle; deleting history asks, naming the agent, address, and space; opening a window asks unless allowed until disconnect, and private windows always ask (FACT `coding-agents.md:17-48`).
- **Crest's visibility.** Agent badge and outline in the agent's colour on each tab; a bar naming the agent; a pointer showing where it clicks; "Stop Agent in This Tab"; "Stop All Agents" in the app menu; a list of what each agent did lately (FACT `coding-agents.md:31-40`).
- **Brave isolates the agent from your logins.** AI browsing runs in a brand-new profile; "cookies, logged-in state, caches, and other site data do not cross profiles", which "limits harm if defenses fail and a model is manipulated into a dangerous action". A second model checks that the task model's actions match the user's intent, and it "does not directly receive raw website content" (FACT, brave.com/blog/ai-browsing, read 2026-10-25). This is the opposite trade-off to rac's agent and Nook's agent space, which borrow the user's sign-ins (FACT, rac baseline; `plans/research/nook.md` Take 2).
- **Chromium's built-in back door for outside agents.** `chrome-devtools-mcp --autoConnect` reads the `DevToolsActivePort` file in the browser's data folder (FACT `chrome-devtools-mcp:src/BrowserManager.ts:384`) after the user enables remote debugging at `chrome://inspect/#remote-debugging`, and Chrome then shows an Allow dialog (FACT, developer.chrome.com). In rac's Chromium 154 tree the server starts in `kWithApprovalOnly` mode, and a code comment says "each incoming connection needs to be approved by the user" (FACT `chromium:chrome/browser/devtools/remote_debugging_server.cc:247,403-405`); not seen running. The toggle's code is in rac's tree, enabled on macOS, and unpatched by Helium or rac (FACT `chromium:chrome/browser/devtools/features.cc:203-211`). A connected CDP client "can read your cookies, saved passwords, and every active session" (CLAIM, lite.ego.app). INFERENCE: if this works in rac builds, any outside agent can bypass rac's guard, critic, confirm cards, and per-site rules once the user flips one switch in a developer page. It needs a decision either way (see Take).
- **Floorp OS is a cautionary design.** Loopback HTTP, token optional and empty by default, and `Access-Control-Allow-Origin: *` on streams (FACT `server.sys.mts:10,166-176,595`). INFERENCE: when enabled with no token, a web page could probably send it simple requests and read its event streams. Off by default limits the damage.

### Prompt-injection defenses seen

- Isolation of the agent from credentials (Brave). Data minimization in tool output (Crest: no form values, no cookies, no bodies). Approval before "critical actions" (Strawberry, CLAIM). "Take over task" button (Chrome, CLAIM). None of the long tail publishes injection evals or a red-team suite. INFERENCE: rac's guard plus critic is already above the median; its known `auto` gap is the issue (maintainer brief).

### AI off, and saying so

- Firefox 148's AI Controls page has one "Block AI enhancements" switch that also keeps *future* AI features off and lists each AI feature with its own switch (Mozilla's 148 release notes confirm only that an AI Controls section was added on 2026-02-24, FACT; the switch's details are CLAIM from TechCrunch, Thurrott, and others). DuckDuckGo has a one-click "Use DuckDuckGo Without AI" (FACT, duckduckgo.com/updates). Vivaldi and Orion advertise having none (FACT, their posts). INFERENCE: privacy-minded Arc refugees respond to a visible, single place that proves AI is off.

### Skills, memory, automations

- Skills are now a standard: Dia (with a public gallery), Wavebox (11 built in), Opera Neon, and `opera-devtools-mcp` ships `skills/` for coding agents (FACT `opera-devtools-mcp/skills/`: `a11y-debugging`, `chrome-devtools`, `cookie-debugging`, and others).
- Memory is retreating: Dia deleted its memory feature and data on 2026-09-24, saying newer models no longer need it (FACT, Dia changelog).
- Automations: Fellou "Workflow" with scheduled runs (CLAIM); Comet background assistants on the $200 plan (CLAIM); Dia "Morning Brief" (CLAIM).

### Using a person's AI subscription through a coding agent

- Anthropic's Claude Code legal page (read 2026-10-25) says subscription sign-in "is designed to support ordinary use of Claude Code and other native Anthropic applications". Developers building on the Agent SDK "should use API key authentication". Third parties may not "route requests through Free, Pro, or Max plan credentials on behalf of their users". The page also says this does not "prevent an end user from signing in to the unmodified Claude Code binary with their own Claude subscription" (FACT, code.claude.com/docs/en/legal-and-compliance). The February 2026 wording The Register reported is older (CLAIM). rac's Claude path runs `npx @agentclientprotocol/claude-agent-acp@0.93.0` (FACT `patches/rac/ai/21-agent-providers.patch:668`), an adapter built on `@anthropic-ai/claude-agent-sdk` (FACT `claude-agent-acp:package.json:69`). INFERENCE: rac sits between the page's two cases, the user's own unmodified Claude Code login and an Agent SDK product. Meridian's README says it keeps Claude Code and Gemini CLI in a terminal for this reason (FACT that it says so). See Open questions.

## Build, release, and engineering

### How the others build and ship

| Product | Build system | Engine in CI | Signing, updates | Cadence | Tests | Tracking upstream |
| --- | --- | --- | --- | --- | --- | --- |
| Crest | XcodeGen (`project.yml`), .NET NativeAOT core, Python fork scripts | **Prebuilt engine.** A job checks whether an engine for the exact recipe is already published; only if missing does it build on a registered self-hosted Mac (`[self-hosted, macOS, ARM64, crest-chromium]`, 1,440-minute timeout); app builds reuse it on GitHub's `xcode-27` runners (FACT `crest:.github/workflows/chromium-engine.yml:14-48`, `ci.yml`) | Developer ID, notarized DMG on GitHub Releases, Sparkle, Homebrew cask `crest-browser`; iOS via App Store and TestFlight (FACT `crest:README.md:106-110`) | Development build on each merged PR, nightly at 08:15 UTC (FACT `release.yml:10-13`); 268 releases in 71 days | 487 test functions in 168 files (FACT, grep of `func test`, `@Test`, `[Fact]`, `[Theory]` at `838acaa`); Python contract tests for the fork and releases (FACT `Scripts/Tests/`) | Pins an ungoogled-chromium-macos tag with archive hashes (FACT `source.lock.json`); a 6-hourly job checks upstream (FACT `chromium.yml:8-9`); an update must apply every hunk **without fuzz** or it stops; a new milestone needs `--allow-major` and review (FACT `crest:CrestEngines/Chromium/README.md:22-25`; `fork.json` `automaticMajorUpdates: false`) |
| Stedding | Patch series + `tooling/` scripts | Built on the owner's two machines; GitHub Actions only for checks (FACT, `runs-on: ubuntu-latest` in all workflows) | GitHub Releases (ADR 0014), Sparkle on Mac (ADR 0022) | 38 releases from 09-01 to 10-25 | Unit and browser tests named in every spec row, many "not yet run" (FACT, `docs/features/*.md`) | One pin file; security fixes within 7 days for in-the-wild exploits and 14 otherwise; a new milestone waits until it reaches 1% of stable users; "M157 waits" because a rebuild takes six hours on both machines (FACT `stedding:docs/decisions/0007-chromium-version-pin.md:16-37`) |
| Refrax | Xcode + `Scripts/forge/forge` | Chromium engine bundle built separately and installed from Settings | Engine bundles must be signed by Refrax's team; in-app updates (FACT `refrax:Engines/CONTRACT.md` §2; `README.md`) | 9 releases | An engine conformance suite drives a bundle against loopback fixtures (FACT `CONTRACT.md` §7) | Patches applied after ungoogled-chromium's in filename order (FACT `patches/README.md`) |
| Mori | Python scripts per platform | Trusted builds on the owner's Windows PC and WSL runners (FACT, README "Tests") | Unsigned preview installers with SHA-256 sums (FACT, README) | Previews | Playwright CLI suites launch the built browser headless, sandbox on, temporary profiles (FACT, README "Tests") | Patch hashes recorded; a changed applied patch is rejected (FACT `mori:docs/ARCHITECTURE.md`, "Build boundary") |
| Floorp | Deno, Vite, pnpm over a separately built Firefox "runtime" | The runtime is pinned by release and commit in `floorp-runtime.lock.json`; the UI layer builds without rebuilding Firefox (FACT `floorp:floorp-runtime.lock.json:1-12`) | Signed installers, PPA (FACT, 12.20.0 notes) | Every 1-2 weeks | `test/` folders per feature | Follows Firefox releases (157.0.1 in 12.20.0) |
| Thorium | GN args and patches | Owner's machines | — | Skips milestones, labelled Beta | — | Lags: M152, M154, M156 betas |
| ChatGPT Atlas | Internal | OWL ships to engineers as a prebuilt binary; "build times drop from hours to minutes" (CLAIM, OpenAI OWL post via ByteByteGo) | — | Frequent | — | "Keep Chromium patches small" (CLAIM, same) |

### What this means for rac (INFERENCE)

- **Two projects ship Chromium browsers weekly from a self-hosted Mac.** Crest builds the engine only when its recipe changes, keyed by hashes, on a Mac it controls, then reuses it. Stedding and Mori build on the owner's machines. rac's GitHub-hosted 6-hour phases restart siso from step zero and never finish (maintainer brief; `plans/context/ci-status.md`). Crest's split (engine artifact keyed by recipe, app layer rebuilt on every change) is the closest working answer. For rac, the "engine" would be Chromium + Helium + the rac patches that touch upstream, so the split is less clean than Crest's. A self-hosted runner on the maintainer's Mac is still the cheapest way to get one signed build out.
- **"No fuzz" is a cheap guard.** rac applies patches with quilt; Crest refuses any hunk that needs fuzz. That catches silent misapplication after a Helium sync.
- **Upstream pace.** Chromium ships a major every two weeks (FACT, rac baseline). Stedding already defers milestones nobody runs yet. Thorium and Supermium show what happens to one-person forks that can't keep up: six majors behind.
- **Recorded network runs** (Stedding) and **headless Playwright launches of the built browser** (Mori) are two cheap, automatable checks rac's CI lacks today.

## Strengths and weaknesses

### Of the field, as rac's competition (critical)

- **Crest is the real threat, not the big browsers.** It is open source, sends nothing to its maker (CLAIM, privacy page), has Arc import with spaces and passwords, per-space sign-ins, Peek, Quick Window, link routing, a nightly channel, Homebrew, iPhone and iPad apps, and outside-agent MCP with signature-checked identity (FACT, sections above). It needs macOS 26.1 and Apple silicon (FACT `crest:README.md:106`), it is "early access, security not independently audited" (FACT), and running two engines doubles its testing. rac's remaining edges over Crest: uBlock Origin built in through Helium (Crest says to install a blocker for Chromium pages, FACT `crest:README.md:89`); Helium's privacy patches on top of ungoogled-chromium; macOS 13+ support (FACT `chromium:build/config/mac/mac_sdk.gni:29,38`; `site/src/pages/index.astro:133`); an optional built-in assistant with local models; a Views UI that gets every Chrome dialog for free. rac has zero releases; Crest has 12 stable ones.
- **Stedding is rac's mirror image** with a bigger upstream footprint (504 files vs ~217) and Windows support, no AI, many features "written, tests not yet run" (FACT). It proves the per-space partition approach and the sidebar file, but not yet at scale.
- **The big four made "vertical tabs" table stakes** in 2025-2026 (CLAIM, press). A rac pitch of "Arc-style sidebar" alone no longer differentiates. INFERENCE.
- **AI-first browsers crowd the "agent" story.** Comet, Chrome, Edge, Neon, Dia, Genspark, Strawberry, Fellou all ship agents; Atlas did until its reported shutdown (CLAIM). The open niche is the opposite: *your* agent, local, permissioned, with AI off by default. Opera Neon's free tier and Crest show that niche is real (FACT).
- **Small projects die or stall quickly.** Sidekick shut down; SigmaOS stalled; Aura archived; Flow quiet since April; Kagi cut two platforms (CLAIM/FACT cited above). Shipping cadence and focus matter more than feature count. INFERENCE.
- **Privacy claims are mostly self-reported.** Only Stedding publishes a host-by-host recorded run (FACT). Min ships opt-out usage stats (FACT). Crest reserves the right to add a search source parameter (FACT).

### What the long tail does better than rac today

- Ships: Crest 268 releases, Yalqen 100+, Stedding 38, rac 0 (FACT).
- Per-space sign-ins (Crest, Stedding, Brave, Wavebox, Orion 1.1) where rac has none (FACT).
- Cross-Mac sidebar without a server (Crest via CloudKit, Stedding via a folder) where rac has none (FACT).
- Outside agents with identity, scope, and visibility (Crest) where rac's MCP serves only its own launched agent (FACT).
- Engineering hygiene: prebuilt engine artifacts, no-fuzz gates, scheduled upstream checks (Crest); recorded network runs (Stedding); headless launch tests of the built app (Mori) (FACT).

### What rac does better than most of the long tail

- Calm, opinionated defaults versus Floorp's and Vivaldi's setting sprawl (FACT for their settings; judgment INFERENCE).
- An agent with a guard, a critic, confirm cards, and permission levels, above the median here (FACT, rac baseline). Nobody in the long tail publishes injection evals either.
- Local models and installed ACP agents as providers (FACT, rac baseline); Wavebox and Meridian are the only long-tail peers.
- Chromium plus Helium's privacy baseline, where Crest leaves Chromium pages unblocked by default (FACT).

## What rac should take (ranked, concrete, with rough cost) and what rac should avoid

Cost scale for one agent-driven worktree, including tests and screenshots: **XS** under a day; **S** 1-3 days; **M** 1-2 weeks; **L** 3-6 weeks. "Thread" is the planned long-running thread: UI or architecture. Costs are INFERENCE.

**Plain English.** The most valuable idea is letting each space use its own accounts. Arc users often kept work and personal Gmail in two spaces of one window. rac can't do that yet, and other Chromium browsers now show it can be built. Next come cheap fixes that stop Arc habits from breaking. Keep a Slack tab alive in a hidden space. Let people clear the day's tabs and get them back later. Let them carry their sidebar to another Mac without any rac server. For outside agents, check who is connecting using the Mac's own code-signing records, and limit which spaces they can touch. One Chromium switch may already let outside tools take full control of rac. Check that first. For engineering, build the heavy engine once on the maintainer's Mac and reuse it. Avoid what others removed: web panels, shared online workspaces, and AI "memory".

### A. Product ideas rac doesn't have, ranked for Arc refugees

| # | Idea | Seen in | Why it matters to Arc refugees | rac today | Cost, thread |
| --- | --- | --- | --- | --- | --- |
| 1 | **Separate sign-ins per space, in one window.** A space setting "Use separate sign-ins", off by default, on for imported Arc spaces that had their own profile. Tabs in that space open in a storage partition named by a random token; favorites stay shared. Options: **(A)** storage partition per space (Brave 1.92, Stedding ADR 0019): one upstream hunk in `browser_navigator.cc` plus Brave's session-restore prefix; extensions, history, passwords stay shared. **(B)** a full Chromium profile per space in one window (Arc, Crest): needs Crest-style window ownership; per-space extensions. **(C)** keep profile = window; add Dia-style swiping between profile windows. | Arc, Crest, Stedding, Brave, Zen, Wavebox, Orion 1.1, Ghost | Arc let each space use its own profile, so work and personal accounts lived side by side in one window. Planned Arc import can't reproduce this today. Every serious Arc clone in this sweep ships it. | Not built; spaces share cookies (rac baseline) | A: M-L, architecture. B: L+ (architecture change). C: S-M, UI. Note: rac's `pinned/close-and-navigate.patch` and Helium's `ui/layout/zen-mode.patch` and `core/override-chrome-protocol.patch` already edit `browser_navigator.cc` (FACT, grep of `+++` lines), so the hunk shares a file with all three |
| 2 | **"Keep loaded" and smarter unloading.** A tab or pin menu item "Keep loaded". Also never unload tabs with an open WebSocket or WebRTC connection or with notification permission. | Crest "Keep Loaded"; Ardia's freezing rule (`plans/research/ardia.md` Take 4) | Arc users pin Slack, WhatsApp, or Gmail in a work space. rac unloads hidden spaces after 15 min, keeping only audio, PiP, and loading tabs, so those apps can go quiet. INFERENCE: notifications stop until the space is opened. | Unload after 15 min (FACT `spaces_window_manager.h:65,134-137`) | S, architecture |
| 3 | **Carry the sidebar to another Mac, no server.** Step 1: "Export spaces…" and "Import spaces…" with stable ids; import merges and never closes an open tab (Stedding Sf2). Step 2: optional "Sync through a folder" (iCloud Drive or any synced folder), one file per Mac, merged on launch. Use Crest's merge rules: fractional positions, deletion tombstones, refuse stale merges. Doubles as a backup (Zen Take 1). | Stedding (beta), Crest (CloudKit), Sidebery (snapshots) | Arc Sync dies on 2026-12-22. People with two Macs lose a shared sidebar; rac has no sync. A folder needs no rac server, so it keeps "Private". | Not built; Sync "maybe later" (VISION) | Step 1 S; step 2 M; architecture |
| 4 | **"Clear" today's tabs, with an Archive.** A quiet "Clear" on the open-tabs header closes this space's unpinned tabs with an Undo toast. Closed tabs land in a searchable per-space Archive for 30 days. No *automatic* archiving, so VISION holds. | Arc, Dia 1.52 ("close unpinned tabs" button), Crest Archive, Stedding archive | Clearing the day's tabs is a daily Arc ritual. Dia added the button in October 2026 (FACT); INFERENCE that Arc users asked for it. | Not built | Clear S; Archive M; UI |
| 5 | **On-device page translation, moved up from phase 6.** Apple's Translation framework on Chromium pages, as Crest does. Gate by macOS version. | Crest 0.8.50 (FACT) | Helium removes the Translate section from settings (FACT `helium-chromium/patches/series:242`), so rac likely has no page translation. INFERENCE: non-English Arc users had Chrome's translate and will notice. | Phase 6 idea | M, UI + architecture |
| 6 | **Link routing (Air Traffic Control), moved from Later to the import wave.** Rules "Contains" or "Exact", evaluated top to bottom, then the default for outside links (Quick Window, last space, or a chosen space). Hide rules for locked spaces. | Arc, Crest, Wavebox, Refrax, Stedding patch 0027 | With idea 1, a Zoom or Figma link opens in the right space *and* the right account. It shares a site-to-space model with Arc import. | Later | M, architecture |
| 7 | **Favorite previews, local only.** Hover a *loaded* favorite for ~400 ms to see a small live preview of its own page. Show an unread count parsed from the title, like "(3) Inbox". No OAuth, no integrations, no work until hover. | Arc Previews (Gmail, Calendar, GitHub, Linear, Notion, Figma) | Arc users checked mail and the next meeting this way many times a day (feature FACT, habit CLAIM). Nobody else offers a privacy-safe version. | Not built | M, UI |
| 8 | **Dark pages.** One switch plus per-site exceptions, on Chromium's `force_dark_mode_enabled` preference and the `AUTO_DARK_WEB_CONTENT` content setting registered for desktop. Paint `#121212` under the page before its first frame to avoid a white flash. | Stedding Dk1, Dk7, Dk12 (FACT `stedding:docs/features/dark-pages.md:36-47`) | Calm at night. Arc users leaned on Dark Reader or Boosts. | Not built | S-M, UI |
| 9 | **"Hide distracting items" as the first Boost.** Pick page elements to hide; remembered per site; Undo. | Safari 18 Distraction Control (FACT), Arc Boosts Zap | Arc's Zap is the Boost most people used (CLAIM, unverified). Safari shows a simple, safe UX. | Boosts planned | S-M, UI |
| 10 | **Arc muscle-memory bundle.** New tabs at the top of the open list (Arc's order; Dia setting). Empty new tab pages clear themselves when abandoned (Dia 1.38). A Ctrl+Tab switcher in Arc's layout, if rac's MRU cycling has no visual (Dia 1.51). Copy URL as Markdown (Crest). PiP: click the title to return to its tab (Dia 1.46). Sideways mouse wheel over the sidebar switches space (Stedding). | Dia, Crest, Stedding | Each is a small habit that makes rac feel like Arc on day one. | Not built or unverified | XS-S each, UI |
| 11 | **Lock a space with Touch ID.** A space can require Touch ID and relock when rac goes to the background. Only meaningful after idea 1 separates its cookies. | Crest Private Spaces, Refrax | Personal space on a work Mac, or a shared family Mac. | Not built | S-M, UI |
| 12 | **An "AI controls" page.** List every AI surface, what it sends, and to whom; one master switch; promise in writing that new AI features ship off. | Firefox 148, DuckDuckGo | Makes "AI off costs nothing" visible to refugees who distrust AI browsers. | AI off by default; no single list | S, UI |
| 13 | **Web apps that keep a space's sign-ins** ("Add to Dock"). | Stedding, Safari, Orion, Vivaldi 8.2 | Arc favorites often stood in for apps. Low priority. | Chromium's app install (unverified) | S after idea 1 |
| 14 | **The same space in two windows**, each with its own selected tab. | Arc, Crest, Stedding | Two-monitor Arc users. Chromium allows a page in one window at a time, so Crest mirrors a preview in the other window (FACT `crest:Documentation/ARCHITECTURE.md:50-52`). | "Open in another window" screen | L, architecture |
| 15 | **Localhost developer bar**: viewport presets, capture, DevTools, shown on `localhost` or with a shortcut. | Arc developer mode, Crest | Many Arc users are developers. | Not built | M, UI |

### B. Agent and outside-agent ideas, ranked

| # | Idea | Seen in | Why | Cost, thread |
| --- | --- | --- | --- | --- |
| 1 | **Decide Chromium's `chrome://inspect` remote-debugging toggle now.** Verify on a build whether `chrome-devtools-mcp --autoConnect` can attach to rac (XS). Then pick: (a) compile it out or hide it in rac (S); (b) keep it with a plain warning that it bypasses rac's agent safety; (c) keep it off until rac's own outside-agent MCP exists. | Chrome 144+; code in rac's tree (FACT `chromium:chrome/browser/devtools/features.cc:203-211`) | If it works, one developer switch lets any local tool read every tab and cookie, skipping rac's guard, critic, and cards (INFERENCE). If it works, the brief's "rac can't be driven by an outside agent at all" is not quite true. | XS-S, architecture |
| 2 | **Identify outside agents by code signature.** Read the peer's audit token from the socket, check rac's own helper, walk up to the first non-shell parent, key on Team ID and signing ID; for interpreters (`node`, `python`, `uv`, `npx`…), add the agent's declared name. Ask once per new agent; "Forget" to revoke. | Crest (FACT `BrowserAgentPeer.swift:48-137`) | Per-agent permissions (roadmap revision phase 5) need a name the agent can't fake. | M, architecture |
| 3 | **Scope and minimise what outside agents see.** Per-space access switches; never private windows or `rac://` pages; `read_page_text` without form values; network reads without cookies, auth headers, or bodies; page-world scripts behind their own switch; deleting history always asks. | Crest (FACT `coding-agents.md:42-48`) | Less data in the model's context is the cheapest injection defense. | S-M on top of rac's guard |
| 4 | **Ship the MCP server inside the app** (`rac.app/Contents/Helpers/<helper> mcp`, stdio), with "Copy setup" per agent and a background-launch flag. No npm package. | Crest; Refrax `refrax-ctl`; Opera CLI as the npm counter-example | One path to paste; nothing downloaded at run time; the helper's signature is part of the identity check in B2. | S-M, architecture |
| 5 | **A clean-room agent space.** "Run this task in a space with no sign-ins." With A1 this is just a fresh partition. | Brave AI browsing (FACT) | Research tasks don't need your accounts; an injected page then finds nothing to steal. Complements Nook's "agent space with your sign-ins". | S after A1 |
| 6 | **Agent colour, badge, outline, and pointer** (glide 0.35 s), plus "Stop all agents" in the menu bar. | Crest | Makes outside agents legible and stoppable. | S, UI |
| 7 | **Compact snapshots with a next-step hint** in CLI output. | Opera Browser CLI (CLAIM: up to 80% fewer tokens) | Cheaper, faster outside agents. Measure before adopting. | S, architecture |

### C. Engineering and architecture, ranked

| # | Idea | Seen in | Why | Cost, thread |
| --- | --- | --- | --- | --- |
| 1 | **Build the engine once on a self-hosted Mac, keyed by a recipe hash, and reuse it.** A job checks whether an engine for the exact inputs is published; only if not does a registered Mac build it (24-hour timeout); signing and packaging reuse the artifact. Run only on trusted events. | Crest (FACT `chromium-engine.yml:14-48`); Stedding and Mori build on owners' machines | rac's hosted 6-hour phases never finish. No release means no Arc refugees. Needs the maintainer's approval for a runner on their Mac. | S-M, architecture |
| 2 | **No-fuzz gate plus a scheduled upstream check.** Fail a sync if any hunk needs fuzz; check helium-macos tags every 6 hours; open a review PR; require an explicit flag for a new Chromium milestone. | Crest (FACT `crest:CrestEngines/Chromium/README.md:22-25`; `chromium.yml:8-9`) | Catches silent misapplication; keeps the Helium gap from growing. Overlaps Zen Take 2. | S, architecture |
| 3 | **A recorded network run.** Fresh profile, 5-10 minutes, `--log-net-log`, list every host, compare with an allowlist published in docs. | Stedding (FACT `docs/PRIVACY.md:72-95`) | Turns "nothing phones home" into a test. It found two Google calls in Stedding. | S, architecture |
| 4 | **Frame-level motion checks and the space-switch recording trick.** Log views laid out and painted per frame; keep the departing space as a paint recording, not a UI-thread bitmap; use `EASE_OUT` instead of Chromium's emphasized curve for the sidebar. | Stedding O4, O6, O7 (FACT `motion.md:20-23`) | Measured in Views on Mac: switch time fell from 18-22 ms to 13-14 ms. Supports "never slower than Helium". | S-M, UI |
| 5 | **Measure PGO and ThinLTO.** Helium sets `chrome_pgo_phase=0` (FACT `helium-chromium/flags.gn:1`). Crest's performance preset uses Chromium's published mac-arm profile with ThinLTO (FACT `crest:CrestEngines/Chromium/README.md`). Profiles come from Google's storage at build time only (INFERENCE: no runtime privacy cost; it departs from ungoogled's binary-pruning stance). | Crest, Thorium | Possible free speed. Needs a full build, so the maintainer's approval. | S to try, architecture |
| 6 | **A one-week architecture spike before any UI rewrite.** Compare: stay on Views; Crest-style native window in Chromium's process; Refrax/Atlas-style out-of-process Chromium with remote layers; Chromium's `kWebium` HTML UI. Measure upstream files touched, which Chrome dialogs must be rebuilt, tab-switch time, and memory. | Crest, Refrax, Atlas, Mori, `kWebium` in rac's tree (FACT `chrome_features.cc:1966`) | Mori rewrote three times in five months (FACT). Decide with numbers. | M, architecture |
| 7 | **Know what code can be borrowed.** Refrax is GPL-3.0, directly compatible. Stedding (BSD-3), Mori (MIT): copy with notices. Crest, Floorp, Brave (MPL-2.0): file-level copyleft; MPL files can sit inside a GPL-3.0 work unless marked "Incompatible With Secondary Licenses" (INFERENCE, MPL-2.0 §3.3; check each file). | — | Saves time on the Arc importer (`crest:.../Portability/ArcSidebar.cs`), signature checks, partitions. | XS |

### Avoid

| Avoid | Evidence | Why |
| --- | --- | --- |
| A second engine (WebKit fallback) | Crest 0.7.0: switching engines can require signing in again (FACT) | Doubles testing; fights "cheap to update" |
| Web panels and sidebar apps | Edge 149 removed the sidebar app list (CLAIM); Sidekick shut down (CLAIM) | Clutter; not "calm" |
| Server-backed shared spaces | Edge Workspaces dropped sharing in 2026 (FACT, MC1192661) | Needs accounts and servers; breaks "Private" |
| An AI "memory" feature | Dia deleted memory on 2026-09-24 (FACT) | Privacy cost; the leader removed it |
| Loopback HTTP automation with an optional token and wildcard CORS | Floorp OS (FACT `server.sys.mts:10,595`) | Web pages may reach it; use a Unix socket and peer checks |
| Opt-out usage statistics or daily IDs | Min (FACT `statistics.js:50-58`); Yab (context file) | Breaks "nothing phones home" |
| Search partner parameters | Crest says it "may" add one (FACT `privacy/index.html:142`) | Even app-wide tags erode trust |
| Outside-agent MCP through a vendor account | Opera Neon MCP needs an Opera account and OAuth (FACT) | rac has no accounts; keep it local |
| Wellness and suite features (break reminders, binaural sounds, mail, calendar, feeds) | Opera Air, Vivaldi (CLAIM) | Scope creep, settings sprawl |
| Config as code, modal keys, mouse gestures, hundreds of settings | Glide, Floorp, Vivaldi, Sidebery (FACT/CLAIM) | Fights "opinionated" |
| CEF | Mori: no Chrome extensions, even milestones only (CLAIM) | Dead end for a Chrome-extension audience |
| More platforms before the Mac app ships | Kagi cut Orion for Linux and Windows (FACT); Stedding delays milestones for two-machine rebuilds (FACT) | One maintainer, two-week Chromium majors |
| Removing a layout after users depend on it | Safari 26 compact tab bar removed then restored (CLAIM); Edge Collections removal lost data (CLAIM) | Decide removals before release |
| Tree tabs as a default | Tree Style Tab conflicts with other tab add-ons (FACT, Sidebery README) | Arc used folders, not trees |

## Open questions and things you could not verify

1. **Does Chromium's "remote debugging in a running browser" work in rac builds?** The feature flag and `chrome://inspect` toggle are in rac's Chromium 154 tree and unpatched (FACT). I did not launch a build, so I could not confirm that `chrome-devtools-mcp --autoConnect` attaches, or see the approval dialog. Chromium 154's code says each incoming connection needs approval (FACT `remote_debugging_server.cc:403-405`).
2. **Which tabs does rac's 15-minute space unload actually hit?** The baseline says audio, PiP, and loading tabs stay live. I did not confirm whether pinned tabs with notification permission or open WebSockets unload (Take A2 rests on this; INFERENCE).
3. **Does page translation work at all in Helium?** Helium removes the Translate section from settings (FACT `helium-chromium/patches/series:242`). I did not test whether the translate bubble or engine still runs.
4. **Where does rac insert new tabs, and does MRU cycling show a switcher?** Not found in a quick grep of `patches/rac/` (Take A10).
5. **Crest's real-world quality.** I read docs and code, not the running app. Memory cost of one Chromium profile per space, extension coverage on its native host, and crash rates are unknown.
6. **Refrax's Chromium engine and extensions.** The contract mentions extension artifacts; I did not confirm that Chrome Web Store extensions run on its out-of-process host.
7. **Stedding's partition approach on top of Helium.** Its one upstream hunk is in `browser_navigator.cc`, which Helium's `zen-mode.patch` and `override-chrome-protocol.patch` and rac's `pinned/close-and-navigate.patch` already edit (FACT, grep). Merge cost unknown until tried. Brave's session-restore fix covers restart, "Reopen closed tab", and sync; rac would need the first two.
8. **Anthropic's terms for rac's ACP path.** Anthropic's legal page lets an end user sign in to the unmodified Claude Code binary with their own subscription, but tells Agent SDK developers to use API keys (FACT, code.claude.com/docs/en/legal-and-compliance, read 2026-10-25). rac's Claude path goes through an Agent SDK-based ACP adapter (FACT, see Agents and AI). Which rule applies is unclear (INFERENCE); only Anthropic can settle it.
9. **Chrome split view.** One index lists "Chrome finally gets split view" on 2026-02-20 (CLAIM, AlternativeTo); another 2026 comparison says Chrome has no split view (CLAIM). Unresolved.
10. **Firefox AI Controls default.** Whether "Block AI enhancements" starts on or off is disputed in press (CLAIM). Mozilla's 148 release notes don't say, and its support page did not load for me.
11. **Arc details from memory or press only.** Favorites "Previews" are confirmed by Arc's help center (FACT). Unread badges on favorites, Zap's popularity, and Arc's exact new-tab order are not confirmed.
12. **Status of SigmaOS, Ladybird's alpha, and Orion's promised Linux and Windows source release** (Kagi promised *details* within 30 days of 2026-10-02, so about 2026-11-01, with no date for the code itself; FACT, blog.kagi.com) could change within weeks.
13. **Vivaldi's UI technology and telemetry.** "Built with web technology" comes from Mori's decision record (CLAIM); I did not check Vivaldi's privacy policy for its daily user ping.
14. **Opera Neon's MCP data path.** The MCP path needs an Opera account and OAuth2, and Opera built a "persistent proxy server so the MCP connection stays alive even when Neon is closed" (FACT, blogs.opera.com 2026-03-31). So MCP traffic goes through Opera; what Opera logs there is not stated.
15. **Brave Containers and extensions or passwords.** Brave's doc covers session persistence only; Stedding notes `chrome.cookies` sees only the default jar (FACT). Password-manager behaviour in Brave containers is unverified.
16. **Licence fine print for borrowing.** I did not check individual Crest or Floorp files for an "Incompatible With Secondary Licenses" notice before suggesting MPL code could be adapted (Take C7).

## Sources

### Code read (local clones, read-only)

- Crest (`/tmp/rac-overhaul/src/crest`, commit `838acaa`, 2026-10-25): `README.md`; `CHANGELOG.md` (0.4.0-0.8.50); `Documentation/ARCHITECTURE.md`; `Documentation/Architecture/CoreArchitecture.md`; `CrestEngines/Chromium/{README.md,fork.json,source.lock.json,Patches/*.patch,ThirdParty/README.md}`; `CrestShared/DesignSystem/Tokens/CrestMotion.swift`; `CrestMac/Infrastructure/Agents/BrowserAgentPeer.swift`; `CrestAgents/*.swift`; `HelpCenter/docs/browsing/{coding-agents,link-routing}.md`; `HelpCenter/docs/getting-started/move-to-crest.md`; `.github/workflows/{chromium-engine,chromium,release,ci}.yml`; `Website/{index.html,privacy/index.html}`; `SPONSORS.md`; `AGENTS.md`.
- Stedding (`/tmp/rac-overhaul/src/stedding`): `README.md`; `docs/decisions/{0007,0019,0020,0029}-*.md`; `docs/features/{sessions,sidebar-file,dark-pages,clean-links,motion}.md`; `docs/PRIVACY.md`; `patches/*.patch` (counted with `/tmp/rac-overhaul/count_patch2.py`).
- Refrax (`/tmp/rac-overhaul/src/refrax`): `README.md`, `REFERENCE.md`, `Engines/CONTRACT.md`, `Engines/Chromium/{args.gn,patches/README.md,patches/*.patch,refrax/}`.
- Mori (`/tmp/rac-overhaul/src/mori`): `README.md`, `docs/ARCHITECTURE.md`, `docs/archive/DECISIONS-linux-chromium.md`.
- Floorp (`/tmp/rac-overhaul/src/floorp`): `browser-features/chrome/common/`, `browser-features/modules/modules/{os-server,chrome-web-store}/`, `static/gecko/pref/override.ini`, `floorp-runtime.lock.json`.
- Min (`/tmp/rac-overhaul/src/min`): `README.md`, `package.json`, `js/statistics.js`, `js/passwordManager/onePassword.js`, `main/main.js`.
- Sidebery (`/tmp/rac-overhaul/src/sidebery`): `README.md`, `src/defaults/{panels,containers,settings}.ts`, `src/services/`.
- Opera (`/tmp/rac-overhaul/src/opera-browser-cli`, `/tmp/rac-overhaul/src/opera-devtools-mcp`): READMEs, LICENSE, `skills/`.
- rac worktree: `VISION.md`, `docs/roadmap.md`, `plans/context/*.md`, `plans/research/{rac-baseline,zen,nook,ardia,ora,browseros}.md`, `patches/rac/`, `helium-chromium/patches/series`, `helium-chromium/flags.gn`, `flags.macos.gn`.
- rac's Chromium tree (`/Users/knewton/Dev/Github/rac/build/src`): `chrome/common/chrome_features.cc:1966`; `chrome/browser/ui/webui_browser/`; `chrome/browser/devtools/features.cc:203-211`; `chrome/browser/devtools/remote_debugging_server.cc`; `chrome/browser/ui/webui/inspect/inspect_ui.cc:682-694,874-886`; `components/handoff/`.

### GitHub API (read-only, 2026-10-25)

- Repo metadata, releases, contributors: `pauljoda/Crest`, `ysalitrynskyi/stedding-browser`, `kageroumado/refrax-browser`, `FujiwaraChoki/mori-browser`, `YSamed/yalqen`, `Undermove/meridian-browser`, `davidjbeveridge/tangent`, `MultiboxLabs/flow-browser`, `doorhinge-apps/Aura-Browser`, `Floorp-Projects/Floorp`, `minbrowser/min`, `Alex313031/thorium`, `win32ss/supermium`, `LadybirdBrowser/ladybird`, `glide-browser/glide`, `mbnuqw/sidebery`, `piroor/treestyletab`, `brave/brave-browser`, `brave/brave-core` (tree and `docs/containers/session_persistence.md`), `duckduckgo/apple-browsers`, `duckduckgo/macos-browser`, `atlas-engineer/nyxt`, `qutebrowser/qutebrowser`.

### Web

- Crest: https://github.com/pauljoda/Crest ; https://crestbrowser.com/
- Stedding: https://github.com/ysalitrynskyi/stedding-browser
- Refrax: https://github.com/kageroumado/refrax-browser
- Mori: https://github.com/FujiwaraChoki/mori-browser
- Meridian: https://github.com/Undermove/meridian-browser/releases/tag/v0.2.5 ; https://github.com/Undermove/meridian-browser
- Arc shutdown: https://www.howtogeek.com/arc-browser-shutdown-date/ ; https://www.neowin.net/news/arc-browser-is-shutting-down-this-year/ ; https://toolfolio.com/articles/best-arc-browser-alternatives-for-mac-and-windows-after-the-december-2026-shutdown-dia-zen-and-ai-browsers
- Arc features: https://resources.arc.net/hc/en-us/articles/19335284431639-Previews-Glance-Top-Sites ; https://arc.net/integrations/gmail ; https://www.ghacks.net/2023/10/04/arc-max-browser-features/ ; https://www.makeuseof.com/features-arc-browser/
- Dia: https://www.diabrowser.com/changelog ; https://en.wikipedia.org/wiki/Dia_(web_browser) ; https://piunikaweb.com/2026/10/16/dia-update-github-live-groups-custom-skills/
- Chrome: https://chromeunboxed.com/google-is-officially-rolling-out-native-vertical-tabs-to-the-stable-version-of-chrome/ ; https://www.engadget.com/computing/chrome-finally-adds-support-for-vertical-tabs-170000081.html ; https://chromestory.com/2026/06/how-to-enable-vertical-tabs-in-google-chrome/ ; https://www.macrumors.com/2026/01/29/google-chrome-gemini-side-panel-ai-features/ ; https://developer.chrome.com/docs/devtools/agents/get-started/configuration ; https://lite.ego.app/article/devtools-mcp-existing-browser ; https://alternativeto.net/software/google-chrome/news
- Edge: https://www.windowslatest.com/2026/06/06/microsoft-just-killed-edges-collections-and-sidebar-for-more-copilot-after-years-of-pushing-both-features/ ; https://whysogeek.com/microsoft-edge-retires-copilot-mode-sidebar-2026/ ; https://mc.merill.net/message/MC1192661 ; https://learn.microsoft.com/en-us/answers/questions/5825522/workspaces-are-gone-with-the-new-update
- Firefox: https://www.firefox.com/en-US/firefox/138.0/releasenotes/ ; https://www.firefox.com/en-US/firefox/153.0esr/releasenotes/ ; https://support.mozilla.org/en-US/kb/split-view-firefox ; https://www.privacyguides.org/news/2026/02/27/firefox-148-releases-with-promised-ai-killswitch-feature/ ; https://www.techspot.com/news/111453-firefox-148-rolls-out-promised-ai-kill-switch.html ; https://blog.mozilla.org/en/firefox/firefox-smart-window/ ; https://www.engadget.com/2272664/mozilla-deploys-a-new-look-firefox-across-desktop-and-mobile/
- Safari: https://support.apple.com/en-us/104996 ; https://www.apple.com/newsroom/2024/09/ios-18-is-available-today-making-iphone-more-personal-and-capable-than-ever/ ; https://www.macrumors.com/2026/02/16/macos-tahoe-26-4-compact-tab-bar/ ; https://www.macrumors.com/2026/03/24/macos-tahoe-26-4-now-available/
- Vivaldi: https://vivaldi.com/blog/keep-exploring/ ; https://www.ghacks.net/2026/05/21/vivaldi-8-0-launches-with-unified-design-and-no-ai-features-free-for-windows-macos-and-linux/ ; https://www.omgubuntu.co.uk/2026/05/vivaldi-8-0-released-redesigned ; https://en.wikipedia.org/wiki/Vivaldi_(web_browser) ; https://otontechnology.com/vivaldi-anti-ai-browser-4-million-users/
- Orion: https://blog.kagi.com/orion ; https://blog.kagi.com/update-orion-linux-windows ; https://supasidebar.com/blog/orion-browser-mac-review-2026
- SigmaOS: https://sigmaos.macupdate.com/ ; https://www.producthunt.com/products/sigmaos/reviews ; https://efficient.app/apps/sigmaos
- Sidekick: https://www.superchargebrowser.com/library/sidekick-browser-shutdown-chrome-alternative/ ; https://efficient.app/apps/sidekick
- Wavebox: https://hub.wavebox.io/round-up-brainbox-redesign-on-device-ai-new-languages-grammar-checking-tab-groups-more/ ; https://hub.wavebox.io/brainbox/ ; https://hub.wavebox.io/wavebox-interface-terminology/
- Opera: https://blogs.opera.com/news/2026/08/your-ai-agents-can-use-opera-neon-free-of-charge/ ; https://blogs.opera.com/news/2026/03/opera-neon-adds-mcp-connector-to-the-browser/ ; https://9to5mac.com/2026/10/15/opera-air-gets-a-minimalist-makeover-with-a-focus-on-distraction-free-browsing/ ; https://toolchase.com/tool/opera-neon/
- Brave: https://brave.com/blog/containers/ ; https://alternativeto.net/news/2026/7/brave-now-has-working-containers-like-firefox-for-tab-isolation-and-account-separation/ ; https://brave.com/blog/ai-browsing/
- DuckDuckGo: https://duckduckgo.com/updates ; https://techcrunch.com/2026/06/01/duckduckgo-makes-its-no-ai-search-engine-easier-to-access-as-its-traffic-booms/
- ChatGPT Atlas: https://openai.com/index/building-chatgpt-atlas/ ; https://blog.bytebytego.com/p/the-architecture-behind-atlas-openais ; https://help.openai.com/en/articles/12591856-chatgpt-atlas-release-notes
- Comet: https://www.perplexity.ai/hub/blog/comet-is-now-available-to-everyone-worldwide ; https://www.eesel.ai/blog/perplexity-comet-pricing
- Ladybird: https://ladybird.org/index ; https://piunikaweb.com/2026/06/05/ladybird-browser-closes-public-contributions/ ; https://en.wikipedia.org/wiki/Ladybird_(web_browser)
- Glide: https://blog.craigie.dev/introducing-glide/ ; https://news.ycombinator.com/item?id=45430294
- Floorp: https://github.com/Floorp-Projects/Floorp/releases/tag/v12.20.0
- AI browsers: https://www.genspark.ai/blog/genspark-ai-browser-and-on-device-free-ai ; https://fellou.ai/ ; https://www.producthunt.com/products/strawberry ; https://us.norton.com/blog/privacy/introducing-norton-neo-ai-browser
- Others: https://www.macstories.net/reviews/horse-browser-tries-its-hooves-at-a-new-take-on-tabs/ ; https://www.selecthub.com/enterprise-browsers/island-browser-vs-ghost-browser/
- Anthropic terms: https://www.theregister.com/software/2026/02/20/anthropic-clarifies-ban-on-third-party-tool-access-to-claude/5014546 ; https://autonomee.ai/blog/claude-code-terms-of-service-explained/ ; https://www.betterclaw.io/blog/openclaw-anthropic-subscription-ban

## Verification

Adversarial fact-check on 2026-10-25. I re-read the clones under `/tmp/rac-overhaul/src/` (Crest `838acaa`, Stedding `95face2`, Refrax `5e02009`, Mori `39ca397`, Floorp `8b1f3b0`, Min `c92079c`, Sidebery `e6da8e8`, `opera-browser-cli` `7e75b26`, `opera-devtools-mcp` `698f63c`, `chrome-devtools-mcp` `ada7963`, `claude-agent-acp` `739dde3`), rac's worktree and its built Chromium 154 tree, read-only `gh api`, and vendor pages. I ran no cloned code. Counts were redone with `grep`, `wc`, and `awk`.

### Claims checked

| # | Claim | Checked against | Result | Change made |
| --- | --- | --- | --- | --- |
| 1 | Crest pins ungoogled-chromium 155.0.8059.84; MPL-2.0; Apple silicon, macOS 26.1+ | `crest:CrestEngines/Chromium/source.lock.json:5`; `LICENSE`; `README.md:106`; `gh api` | Confirmed | None |
| 2 | Crest: 268 releases, 12 stable (v0.4.0 08-18 to v0.8.50 10-23), created 08-15 | `gh api repos/pauljoda/Crest/releases` (268 rows, 12 non-prerelease) | Confirmed | None |
| 3 | Crest: 1 main author + ~9 contributors | `gh api .../contributors` | Wrong: 11 other humans (plus 2 bots) | Fixed |
| 4 | Crest: 92,023 lines of C#, 221,019 of Swift | `find` + `wc -l` at `838acaa` | C# confirmed; Swift is 239,940 (12,567 in test targets) | Fixed (2 places) |
| 5 | Crest space = own engine profile, cookies, passwords, permissions; CloudKit with fractional order and tombstones; Blank Window; Settings in canvas | `crest:Documentation/ARCHITECTURE.md:26-36,42,52,54,60,90` | Confirmed | None |
| 6 | Crest MCP helper in bundle; 29 tools; identity by code signature (`LOCAL_PEERTOKEN`, 4-level ancestry, interpreter list) | `coding-agents.md:27,54-60`; 29 unique `name:` in `CrestAgents/AgentToolDefinition*.swift`; `BrowserAgentPeer.swift:48-55,66-79,114,126` | Confirmed | None |
| 7 | Crest motion table: durations and curves | `CrestMotion.swift:21-187` | Durations right. Four curves wrong: hover, surface, palette, and selection use `.easeInOut`, not `.snappy` or `.easeOut` | Fixed |
| 8 | Crest download spring 0.68 s, bounce 0.16; agent pointer 0.35 s `.smooth` | `BrowserDownloadFeedbackPresentation.swift:11`; `BrowserWebPageSurfaceMetrics.swift:55`; `BrowserAgentPointerOverlay.swift:52` | Confirmed | None |
| 9 | Crest CI: self-hosted Mac, 1,440-minute timeout, nightly 08:15 UTC, 6-hourly upstream check, no-fuzz rule, `automaticMajorUpdates: false` | `chromium-engine.yml:14-48`; `release.yml:13`; `chromium.yml:9`; `CrestEngines/Chromium/README.md:22-25`; `fork.json:6` | Confirmed | None |
| 10 | Crest `native-host.patch`: 95 files, 205 hunks; 14,406-line overlay; 4,963 lines of Swift engine glue | `grep -c '^+++ '`, `grep -c '^@@'`, `wc -l` | Confirmed | None |
| 11 | Crest tests: 195 files, ~487 functions | `grep` for the four markers | 487 functions confirmed; files are 168, not 195 | Fixed |
| 12 | Stedding: partition per space via `CreateForFixedStoragePartition`, one hunk in `browser_navigator.cc`; `chrome.cookies` sees only the default jar | `stedding:docs/decisions/0019-...md:25-59` | Confirmed (line numbers slightly shifted) | None |
| 13 | Stedding: 104 patches, 504 upstream files, 3,086 hunks, 581 new files | `awk` over `patches/*.patch` | Files, hunks, new files confirmed; 103 patches, not 104 | Fixed |
| 14 | Stedding: 37 releases | `gh api .../releases` | 38 releases, 09-01 to 10-25 | Fixed (3 places) |
| 15 | Stedding motion numbers (33%, 88 DIP, 350/400 and 200/250 ms, 4.6-8.8 ms to 0.7 ms, 18-22 to 13-14 ms) | `stedding:docs/features/motion.md:22-23` | Confirmed; O6 is marked "not yet seen by the owner" | None |
| 16 | Stedding recorded run found Google push check-in and account check; version pin rules (7/14 days, 1% rollout, M157 waits) | `stedding:docs/PRIVACY.md:72-88`; `docs/decisions/0007-...md:27-38` | Confirmed | None |
| 17 | Stedding "No AI at all" | `0020-no-bundled-model.md:22-37` | Too strong: no bundled model, but a later ADR could allow opt-in local or own-key AI | Reworded |
| 18 | Refrax: GPL-3.0; 256 KiB, 8 KiB, 32 bad messages; 7 patches, 22 files, 42 hunks; 6,427-line overlay | `refrax:Engines/CONTRACT.md:302-306`; patch counts; `wc -l` | All confirmed except overlay: 6,812 lines in 66 files | Fixed (2 places) |
| 19 | Floorp OS: port 58261, off by default, optional empty token, `Access-Control-Allow-Origin: *` | `server.sys.mts:10,68,92,168,471,595`; `static/gecko/pref/override.ini:90` | Confirmed | None |
| 20 | Min uploads stats with client ID unless turned off; Electron 43.4.1 | `min:js/statistics.js:23-58`; `package.json:54` | Confirmed | None |
| 21 | rac's tree: `kWebium` off; `kDevToolsAcceptDebuggingConnections` on for macOS; no Helium or rac patch touches it | `chromium:chrome/common/chrome_features.cc:1966`; `chrome/browser/devtools/features.cc:203-211`; `grep` of `patches/` and `helium-chromium/patches` | Confirmed. New: the server runs in `kWithApprovalOnly` mode, and a comment says each incoming connection needs approval (`remote_debugging_server.cc:247,403-405`) | Added; Open question 1 narrowed |
| 22 | `--autoConnect` reads `DevToolsActivePort` (attributed to developer.chrome.com) | developer.chrome.com page; `chrome-devtools-mcp:src/BrowserManager.ts:384` | The page doesn't mention the file; the MCP code does | Citation fixed |
| 23 | `browser_navigator.cc` is already edited by 2 patches | `grep '^+++ '` across patch folders | 3 patches: also Helium's `core/override-chrome-protocol.patch` | Fixed (2 places) |
| 24 | rac: hidden spaces unload after 15 min; agent has 15 tools and a 25-call cap | `patches/rac/spaces/unloading.patch:136`; `chromium:.../spaces_window_manager.h:65,134-137`; 15 unique `t.name` in `patches/rac/*`; `05-direct-loop.patch:1130` | Confirmed | None |
| 25 | Helium removes the Translate settings section; `chrome_pgo_phase=0` | `helium-chromium/patches/series:242`; `helium-chromium/flags.gn:1` | Confirmed | None |
| 26 | Brave Containers 1.92 on 2026-07-02; `containers+<uuid>:` restore prefix | brave.com/blog/containers; `gh api` of `brave-core/docs/containers/session_persistence.md` | Confirmed. "First Chromium browser" is not in Brave's post; stays CLAIM | None |
| 27 | Brave AI browsing quote "so sensitive accounts stay protected even if other defenses fail" | brave.com/blog/ai-browsing | Quote is not on the page | Replaced with the page's real wording |
| 28 | Opera Neon MCP needs an account and OAuth; CLI doesn't | blogs.opera.com 2026-08-14 and 2026-03-31 | Account: 08-14 post. OAuth2: 03-31 post. New: MCP runs through an Opera-built persistent proxy server | Fixed; Open question 14 updated |
| 29 | Meridian quote on subscription terms, cited to v0.2.5 notes | `gh api .../releases/tags/v0.2.5`; README | The quote is in the README (line 29), not the release notes | Citation fixed |
| 30 | Dia items: memory removed 1.50.0 (09-24); pinned tabs and "close unpinned" 1.52; Live Groups 1.53; M156 in 1.54.0; 1.49.0 "context separated from execution" | diabrowser.com/changelog | Confirmed. But 1.49.0's note ends "reducing duplicated cleanup work": a cleanup, not a defense. 1.38.0 new tabs "clear", not "close" | Removed from injection defenses; wording fixed |
| 31 | Anthropic subscription terms (CLAIM via The Register and blogs) | code.claude.com/docs/en/legal-and-compliance (primary) | Current wording quoted. Also found: rac's Claude path is an Agent SDK-based adapter (`patches/rac/ai/21-agent-providers.patch:668`; `claude-agent-acp:package.json:69`) | Upgraded to FACT; Open question 8 rewritten |
| 32 | ChatGPT Atlas listed as a live product | Wikipedia; Digital Trends; search results | Reportedly shut down 2026-08-09 (CLAIM; OpenAI's help page returned 403) | Marked in 6 places |
| 33 | Thorium ships only even milestones | `gh api repos/Alex313031/thorium/releases` | Wrong: M151 shipped 2026-08-03; it skips milestones | Fixed (3 places) |
| 34 | Edge Workspaces moved to Edge Sync and lost sharing (MC1192661) | mc.merill.net/message/MC1192661 | Confirmed (published 2025-12-06, rollout mid-February 2026) | None |
| 35 | Orion: 1.0 on 2025-11-25, zero telemetry, no AI in core; Linux and Windows dropped 2026-10-02, source due ~11-01 | blog.kagi.com/orion; blog.kagi.com/update-orion-linux-windows | Confirmed, except only *details* are due within 30 days; no date for the code | Open question 12 fixed |
| 36 | rac supports macOS 13+ (CLAIM, website) | `chromium:build/config/mac/mac_sdk.gni:29,38`; `site/src/pages/index.astro:133` | Confirmed | Upgraded to FACT |
| 37 | Firefox 148 AI Controls; Vivaldi's no-AI stance | firefox.com 148 release notes; vivaldi.com/blog/keep-exploring | Firefox notes confirm the section and the date only. Vivaldi's pledge holds "until more rigorous ways" exist | Tags and wording refined |
| 38 | Zen dossier citation `zen.md:681-682` | `plans/research/zen.md` | The text is now at lines 716-717 | Fixed |

### Not re-checked (left as tagged)

Press-only items stay CLAIM: Chrome vertical tabs and split view dates, Edge Collections removal, Safari compact tab bar, SigmaOS, Sidekick, Wavebox, Genspark, Comet, Ladybird staffing, Orion's 70% extension figure, and the Opera Neon $19.90 price (the 2026-08-14 post gives no price). GitHub star counts drift daily: Crest showed 791 and Stedding 56 at re-check.

### Overall confidence

**Medium-high.** The code-backed claims about Crest, Stedding, Refrax, Floorp, Min, Sidebery, rac's tree, and Helium's patches held up. The errors were miscounts (Swift lines, overlay size, patch and release counts), four wrong motion curves, one invented quote (Brave), one misread changelog line (Dia 1.49), one wrong pattern (Thorium), one misplaced citation (Meridian), and one stale fact (Atlas is reportedly gone). None of these changes the ranked takes. The Anthropic terms finding matters for rac's Claude Code provider and needs a decision. Verification sources added: https://code.claude.com/docs/en/legal-and-compliance ; https://blogs.opera.com/news/2026/03/opera-neon-adds-mcp-connector-to-the-browser/ ; https://en.wikipedia.org/wiki/ChatGPT_Atlas ; https://www.digitaltrends.com/computing/chatgpt-atlas-is-shutting-down-and-it-has-some-homework-left-before-you-migrate/ ; https://www.firefox.com/en-US/firefox/148.0/releasenotes/ ; https://blog.kagi.com/update-orion-linux-windows .
