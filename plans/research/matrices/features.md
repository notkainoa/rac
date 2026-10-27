# Feature matrix: rac vs the field (2026-10-27)

Rows are user-facing features. Columns are rac today and 13 other browsers. Built from the 18 digests in `plans/research/digests/`, with the full dossiers opened where a digest was thin (feature tables in `zen.md`, `nook.md`, `ora.md`, `cra.md`, `ardia.md`, `aside.md`, `browseros.md`, `ego-lite.md`, `helium.md`, `closed-ai-browsers.md`) and `VISION.md` and `docs/roadmap.md` for what rac does not plan.

How to read a cell:

- **yes** = shipped in a release (or inherited from Helium, for rac).
- **no** = the researcher looked in code, docs or changelogs and found nothing. For closed products this means "not in their docs".
- **partial: x** = exists in a reduced, off-by-default, beta or different form.
- **n/a** = the product has no AI or agent, so the row does not apply.
- **?** = not covered by any digest. Not guessed.
- "Other closed" = Comet, ChatGPT Atlas (shut down 2026-08-09), Opera Neon, Chrome with Gemini, Edge with Copilot. Arc and Dia come from the closed-browser digest plus Ardia's notes on Dia.
- rac's "yes" for blocker, split view, tab search, Arc import, other-browser import and bangs is inherited from Helium. rac's only default network call is the GitHub update check.

## In plain English

rac already matches the core Arc layout: spaces, pinned tabs, favorites, folders, sidebar hide with edge reveal, auto picture-in-picture, plus split view and tab search from Helium. Its optional AI assistant and browser agent are ahead of most rivals.

It is behind where Arc refugees look first. There is no release to download, no command bar, no Arc import that keeps spaces, no separate sign-ins per space, no Boosts, no Peek or Little Arc, no sync, and no way for an outside agent to drive it. Cra, Nook, Yab and Ardia ship most of those today.

rac leads on a rare mix: open source, Chromium, full uBlock Origin, nothing sent to rac, and an agent whose permissions the browser holds. Closed rivals cannot claim that, and the open ones have no AI.

## Matrix

### Tabs and sidebar

| Feature | rac (today) | Arc | Dia | Zen | Ardia | Cra | Helium | Nook | Ora | BrowserOS | Aside | ego(lite) | Yab | Other closed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Spaces (separate tab sets in a window) | yes | yes | partial: profiles | yes | partial: profiles | yes | no | yes | yes | no | partial: profiles | yes | yes | partial: Neon Tasks |
| Separate sign-ins per space | no | yes | yes | yes | yes | yes | no | yes | yes | no | yes | yes | ? | ? |
| Pinned tabs (remember URL, reset) | yes | yes | yes | yes | yes | yes | partial: Chromium pinned | yes | partial: no reset | partial: Chromium pinned | yes | ? | yes | ? |
| Favorites (icon grid) | yes | yes | yes | yes | yes | yes | yes | yes | yes | no | no | partial: icon grid | ? | ? |
| Folders | yes | yes | partial: tab groups | yes | yes | yes | partial: tab groups | yes | no | partial: tab groups | partial: tab groups | partial: tab groups | yes | ? |
| Today list, auto-archive, Clear | no | yes | partial: Cleanup tabs | partial: Clear button | partial: Clean Up | yes | no | no | partial: auto-close | no | partial: Tidy/Clear | ? | partial: Tidy | ? |
| Little Arc / Little Windows | no | yes | no | no | yes | yes | no | yes | no | no | no | ? | yes | no |
| Peek (link preview overlay) | no | yes | no | yes | yes | no | no | yes | no | no | no | ? | yes | no |
| Split view | yes | yes | yes | yes | yes | yes | yes | yes | no | yes | yes | ? | yes | partial: Comet only |
| Tab search | yes | yes | ? | yes | yes | yes | yes | yes | yes | ? | yes | ? | ? | ? |
| Vertical sidebar, hide, edge reveal | yes | yes | yes | yes | yes | yes | yes | yes | yes | partial: no hide | yes | yes | ? | ? |
| Space themes (color, gradient) | yes | yes | ? | yes | yes | yes | no | partial: accent only | no | no | ? | ? | yes | ? |
| Link routing to a space (Air Traffic Control) | no | yes | ? | yes | no | yes | no | yes | no | no | ? | ? | ? | ? |
| Ctrl+Tab recent-tab switcher | partial: MRU opt-in | yes | ? | ? | yes | yes | partial: MRU opt-in | ? | yes | ? | yes | ? | ? | ? |

### Command bar and navigation

| Feature | rac (today) | Arc | Dia | Zen | Ardia | Cra | Helium | Nook | Ora | BrowserOS | Aside | ego(lite) | Yab | Other closed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Command bar (tabs, history, actions) | no | yes | yes | yes | yes | yes | no | partial: no commands | partial: no actions | no | yes | ? | yes | partial: AI-first |
| !bangs and site-search shortcuts | yes | ? | ? | ? | yes | no | yes | yes | yes | no | ? | ? | ? | ? |
| Address bar inside the sidebar | yes | yes | ? | yes | ? | ? | no | yes | yes | no | ? | ? | ? | ? |

### Import and migration

| Feature | rac (today) | Arc | Dia | Zen | Ardia | Cra | Helium | Nook | Ora | BrowserOS | Aside | ego(lite) | Yab | Other closed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Arc import that keeps spaces | partial: bookmarks only | n/a | partial: as profiles | partial: beta | partial: as profiles | yes | partial: bookmarks only | yes | partial: pins only | no | partial: data only | ? | yes | ? |
| Dia import | yes | ? | n/a | partial: beta | partial: no pinned | yes | yes | yes | no | no | yes | yes | yes | ? |
| Other browsers (Chrome, Safari, Firefox) | yes | ? | ? | yes | yes | yes | yes | partial: Safari, Dia | no | partial: Chrome only | yes | yes | yes | ? |
| Credentials (passwords, cookies) | no | ? | yes | partial: beta | partial: CSV only | yes | no | no | no | yes | yes | yes | yes | ? |

### Privacy and blocking

| Feature | rac (today) | Arc | Dia | Zen | Ardia | Cra | Helium | Nook | Ora | BrowserOS | Aside | ego(lite) | Yab | Other closed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Built-in ad and tracker blocker | yes | ? | yes | partial: not bundled | yes | partial: domain list | yes | partial: off by default | partial: off by default | no | yes | ? | yes | partial: Comet, Neon |
| Engine-level privacy (no Google services, fingerprint noise) | yes | partial: Google metrics off | ? | yes | yes | ? | yes | ? | partial: JS spoofing | no | no | ? | ? | no |
| Nothing phones home by default | yes | no | no | partial: Safe Browsing | partial: daily ping | partial: unverified | yes | yes | partial: Google suggest | no | no | no | no | no |
| Built-in password manager, passkeys | no | ? | ? | yes | partial: no iCloud passkeys | yes | no | no | yes | ? | yes | partial: passkeys | yes | ? |

### Media and page tools

| Feature | rac (today) | Arc | Dia | Zen | Ardia | Cra | Helium | Nook | Ora | BrowserOS | Aside | ego(lite) | Yab | Other closed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Auto picture-in-picture | yes | yes | yes | ? | yes | yes | no | yes | yes | no | partial: off by default | ? | yes | ? |
| Media controls in the sidebar | no | yes | ? | yes | ? | ? | ? | yes | yes | no | ? | ? | ? | ? |
| Netflix-class DRM (Widevine) | no | ? | ? | ? | partial: WebKit fallback | ? | no | partial: FairPlay only | ? | yes | partial: unreliable | yes | partial: FairPlay only | ? |
| Page translation | partial: selection only | ? | ? | yes | yes | ? | partial: selection only | yes | ? | ? | yes | ? | yes | ? |

### Per-site tools

| Feature | rac (today) | Arc | Dia | Zen | Ardia | Cra | Helium | Nook | Ora | BrowserOS | Aside | ego(lite) | Yab | Other closed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Boosts (restyle sites) | no | yes | ? | partial: CSS only | partial: userscripts | no | no | no | no | no | partial: Remix beta | ? | yes | ? |
| Per-site controls (permissions, cookies, cache) | yes | ? | ? | ? | partial: Chromium's | yes | partial: Chromium's | partial: Privacy Cleanup | partial: no permissions | partial: Chromium's | partial: Chromium's | ? | ? | ? |
| Clean links (strip tracking on copy or open) | no | yes | ? | ? | yes | ? | ? | partial: needs blocker | ? | ? | ? | ? | ? | ? |

### AI assistant

| Feature | rac (today) | Arc | Dia | Zen | Ardia | Cra | Helium | Nook | Ora | BrowserOS | Aside | ego(lite) | Yab | Other closed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Side-panel chat | yes | partial: Max, trimmed | yes | no | no | no | no | yes | no | yes | yes | no | yes | yes |
| Ask about the page | yes | no | yes | no | no | no | no | yes | no | yes | yes | no | yes | yes |
| Summaries (links, pages) | yes | partial: link previews | ? | no | no | no | no | ? | no | ? | yes | no | ? | yes |
| Writing help, selected-text commands | no | ? | partial: via chat | no | no | no | no | ? | no | ? | yes | no | yes | partial: Atlas retired |
| Choose your own provider (key, local, own agent) | yes | ? | ? | n/a | n/a | n/a | n/a | yes | n/a | yes | yes | yes | partial: your plan | no |
| AI off by default and free when off | yes | ? | ? | n/a | n/a | n/a | n/a | partial: on by default | n/a | no | no | n/a | ? | ? |

### Agent features (user level)

| Feature | rac (today) | Arc | Dia | Zen | Ardia | Cra | Helium | Nook | Ora | BrowserOS | Aside | ego(lite) | Yab | Other closed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Agent acting in your tabs | yes | no | partial: drafts, tools | no | no | no | no | partial: chat tools | no | yes | yes | partial: your agent only | yes | yes |
| Browser-held permissions (ask, per-site rules) | yes | n/a | partial: approvals | n/a | no | n/a | n/a | partial: modal asks | n/a | no | partial: loose default | no | yes | partial: varies |
| Agent works in its own tabs, no focus theft | no | n/a | ? | n/a | ? | n/a | n/a | yes | n/a | yes | yes | yes | yes | ? |
| Routines, scheduled tasks | no | n/a | partial: Morning Brief | n/a | n/a | n/a | n/a | no | n/a | yes | yes | ? | yes | yes |
| CLI for outside agents | no | no | no | partial: 2 flags | yes | partial: cra:// scheme | no | no | no | no | yes | yes | yes | yes |
| MCP server for outside agents | partial: own run only | no | no | no | no | no | no | yes | no | yes | yes | ? | yes | yes |
| One-click skill install for coding agents | no | no | no | no | yes | no | no | no | no | yes | yes | yes | yes | ? |
| Saved prompts, Skills (slash) | no | no | yes | no | no | no | no | no | no | no | yes | n/a | yes | yes |
| Chat channels, remote control (Slack, phone) | no | no | ? | no | no | no | no | no | no | no | yes | ? | yes | ? |

### Sync and backup

| Feature | rac (today) | Arc | Dia | Zen | Ardia | Cra | Helium | Nook | Ora | BrowserOS | Aside | ego(lite) | Yab | Other closed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Cross-device sync of tabs and spaces | no | yes | yes | yes | yes | no | partial: planned flag | partial: unreleased | no | no | yes | ? | yes | partial: Comet iOS |
| Sync with no vendor server | no | no | no | no | yes | n/a | partial: planned | partial: unreleased | n/a | n/a | no | ? | no | no |
| Automatic local backup of tab data | partial: .bak files | ? | ? | yes | ? | partial: one .bak | ? | yes | no | ? | ? | ? | ? | ? |

### Extensions

| Feature | rac (today) | Arc | Dia | Zen | Ardia | Cra | Helium | Nook | Ora | BrowserOS | Aside | ego(lite) | Yab | Other closed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Chrome Web Store extensions | yes | yes | yes | no | yes | yes | yes | partial: WebKit limits | no | yes | yes | yes | partial: shim | yes |
| MV2 extensions (full uBlock Origin) | yes | ? | no | yes | yes | ? | yes | no | no | no | ? | ? | ? | ? |
| Password-manager extensions | yes | ? | ? | ? | partial: untested | yes | yes | yes | no | ? | partial: manual setup | ? | ? | ? |

### Onboarding

| Feature | rac (today) | Arc | Dia | Zen | Ardia | Cra | Helium | Nook | Ora | BrowserOS | Aside | ego(lite) | Yab | Other closed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| First-run onboarding flow | yes | ? | ? | yes | ? | yes | yes | yes | ? | partial: neo only | yes | yes | ? | ? |
| Import offered during onboarding | yes | ? | ? | yes | ? | ? | yes | ? | ? | partial: neo only | ? | ? | ? | ? |

## Gaps that matter for Arc refugees

Arc shuts down on 2026-12-22, 56 days from today. Ranked by how likely each gap is to stop an Arc user from switching.

1. **No release to download (blocks everyone).** rac has 0 releases, and the download page is hidden. Every rival in the matrix can be installed today. Not a feature, but it ranks above all of them.
2. **No Arc import that keeps spaces.** rac inherits Helium's importer, which turns Arc pinned tabs into bookmarks and Top Apps into bookmark-bar entries. Cra, Nook, Yab and Ardia import real spaces. Cra, Dia, Yab and ego also bring passwords and sign-ins; rac brings none (Helium strips them). Without this, an Arc user starts from an empty sidebar and logs in again everywhere.
3. **No command bar.** Cmd+T search over tabs, history and actions is Arc's front door. Zen, Cra, Ardia, Dia, Aside and Yab have one. Helium has an open request, and rac has none.
4. **No separate sign-ins per space.** Arc users who split work and personal accounts by space cannot do that in rac, because its spaces share one cookie jar. Arc, Dia, Zen, Ardia, Cra, Nook and Ora all offer it.
5. **No Peek, Little Arc or auto-archive.** `VISION.md` lists auto-archive and Peek-style previews as "not planned". Little Windows are in Arc, Ardia, Cra, Nook and Yab. Auto-archive is in Arc and Cra. Arc's own data says few people used multiple spaces, so these daily habits may matter more than spaces. This one needs a maintainer decision.
6. **No Boosts.** The signature Arc feature. Only Zen (CSS only) and Yab ship an equivalent. Many users will tolerate the gap. The vision lists Boosts, but no work has started.
7. **No sync across Macs.** Arc, Dia, Zen, Aside, Ardia and Yab sync. `VISION.md` says "maybe later". It stops people who use two Macs.
8. **No sidebar media controls, and no Netflix-style playback.** Helium has no Widevine, so Netflix and Prime Video fail. Only BrowserOS and ego clearly play DRM video; Ardia (WebKit fallback, beta), Nook and Yab (FairPlay only) cover part of it, and Aside is unreliable. Marketing to Arc users must not promise streaming.
9. **No Air Traffic Control.** Link routing is in Arc, Zen, Cra and Nook. It is on rac's roadmap and is a smaller reason to leave.
10. **No live folders** (Arc, Dia, Zen, Ardia, Nook, Yab). Arc's own figures put usage at about 4%, so this should not block anyone.

## Where rac can lead

1. **The only open-source Chromium Arc-like with AI and nothing sent home.** Yab and Aside are closed, Ardia, Cra, Zen and Ora have no AI, BrowserOS ships telemetry with no off switch, and Nook is on WebKit.
2. **An agent whose permissions the browser holds.** In this matrix only rac and Yab have a browser-held ask/careful/auto model with per-site rules; BrowserOS, Ardia and ego have no approval step. Fix the known `auto` gap, publish an injection eval suite (no rival publishes one), and this becomes the headline.
3. **An outside-agent door that keeps the guard.** Aside, ego, Yab, BrowserOS and Nook all ship CLI or MCP; ego has no approvals and BrowserOS opens an unauthenticated port. A rac door that is off by default, independent of the AI switch, and routed through the same guard would be the safe version.
4. **Any model, including local ones and the agents you already pay for.** Ollama, LM Studio, API keys and ACP agents such as Claude Code and Codex are supported. Yab is limited to your Claude/Codex plan and Apple's on-device model.
5. **Arc import done properly.** Keep Arc spaces as spaces (Dia and Ardia flatten them into profiles), keep pins and folders, and bring sign-ins (Nook does not). Nobody does all of this on an open Chromium engine.
6. **Separate sign-ins per space without heavy profiles.** Only Stedding and Brave Containers use a lightweight storage partition on Chromium. An opt-in version also gives a clean, sign-in-free context for agents.
7. **Full uBlock Origin and the Chrome Web Store.** Dia, BrowserOS and Nook (no webRequestBlocking) have lost or cannot offer full MV2. Cra's blocker is a domain list. rac inherits the strongest blocker from Helium.
8. **Calm motion that respects Reduce Motion.** rac honors Reduce Motion nearly everywhere. Ora and Cra ignore it, Nook honors it in one place, and BrowserOS and Nook run endless glows.
9. **Sync with no rac server, later.** Ardia's encrypted folder sync is the template and has not been tested on two Macs. rac can test it properly before shipping.
10. **A privacy claim backed by a recorded network run.** Stedding publishes one. Ardia, Cra, Aside and ego all have gaps between what they say and what they send.

## Unknowns

"?" cells that change a decision:

- **Widevine/Netflix for Arc, Dia, Zen, Cra, Ora and Yab.** Decides how hard rac's DRM gap hurts.
- **Dia: command-bar details, tab search, space themes, Boosts, link routing, sidebar address bar, built-in provider choice.** Dia is the other product Arc users are told to move to.
- **Arc's own built-in blocker and password manager.** Arc is the baseline users compare against.
- **ego(lite)'s browser UI.** The digest covers its agent side. Whether it has Peek, split view, folders, a command bar, sync or a blocker is unknown.
- **Yab: favorites, auto-archive, tab search, link routing, per-space sign-ins, onboarding.** Yab is the closest AI-first rival.
- **Cra: clean links, MV2 support, network traffic.** The privacy page and the updater disagree, and nothing was measured.
- **Clean links in Zen, Dia, Helium, Aside, Ora, Yab.** Likely cheap for rac, but nothing shows who ships it.
- **Whether Helium's importer brings more than bookmarks from Dia and other sources.** It sets rac's real import floor.
- **Aside, BrowserOS and ego: password-manager extension support, MV2 and sync.** Needed to rank the closed AI browsers fairly.
- **"Other closed" import and sync.** Comet, Atlas, Neon, Chrome and Edge are mostly "?" outside AI and agent rows, and are weak for tabs, sidebar and import comparisons.
- **Nothing was run.** Every cell comes from code, docs or changelogs, never from a hands-on session. No performance, memory or feel was compared.

## Sources

- **rac (today):** `rac-baseline.md` digest, the maintainer brief (including the "Added 2026-10-27" notes), `VISION.md` ("Not planned for now") and `docs/roadmap.md`. Inherited features come from the Helium digest and `helium.md` feature tables.
- **Arc, Dia, Other closed (Comet, Atlas, Neon, Chrome, Edge):** `closed-ai-browsers.md` digest and its feature tables. Dia details also from the Ardia digest, which cites Ardia's notes on Dia. Treat Dia "?" cells as unresearched.
- **Zen:** `zen.md` digest and the feature tables in `zen.md`.
- **Ardia:** `ardia.md` digest and `ardia.md` features.
- **Cra:** `cra.md` digest and `cra.md` features and data sections.
- **Helium:** `helium.md` digest and `helium.md` feature tables.
- **Nook:** `nook.md` digest and `nook.md` features.
- **Ora:** `ora.md` digest and `ora.md` features.
- **BrowserOS:** `browseros.md` digest and `browseros.md` features.
- **Aside:** `aside.md` digest and `aside.md` features.
- **ego(lite):** `ego-lite.md` digest and the browser and agent sections of `ego-lite.md`.
- **Yab:** `closed-ai-browsers.md` digest and the Yab entries in its dossier, plus `plans/context/competitors-ardia-yab-2026-10-23.md`.
- **Also read, not a matrix column:** `agent-stacks`, `chromium-agent-internals`, `local-first-and-sidecars`, `motion-and-feel`, `pomerado` and `t3code` digests (used for agent and outside-agent context only), and `long-tail.md` (Crest, Stedding, Refrax, Mori, Brave Containers; used for the per-space sign-ins gap and the lightweight-partition idea).
