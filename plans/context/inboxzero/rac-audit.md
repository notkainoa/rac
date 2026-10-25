> **ERRATA (verified by the orchestrator, overrides the text below):**
> - rac DOES have an Apple Developer ID. All seven PROD_MACOS_* signing and notarization secrets plus both Sparkle keys exist as repository secrets (checked with `gh secret list` on 2026-10-25). Release builds are meant to be Developer ID signed and notarized. What's true is that this path has never completed: no CI release build has finished yet. Treat every "no Apple Developer account / ad-hoc signing / Gatekeeper wall" statement below as "signing and notarization are configured but unproven".
> - The auto-level exfiltration chain (finding 3) was re-checked against `patches/rac/agent/13-permission-levels.patch` test `AutoAsksOnlyForRiskAndForeignTyping`: cross-origin navigate and typing model-generated text into the attached tab are both kAllow at auto. The policy finding stands; whether models actually follow such injections is unmeasured.
> - Upstream gap confirmed: rac is on Helium 0.18.2.1 / Chromium 154.0.8037.92; helium-macos latest is 0.20.1.1 (2026-10-22), seven releases ahead.

# rac: an evidence-based audit

Audited 2026-10-25 against `main` at `d3f0d66` (worktree `/Users/knewton/.t3/worktrees/rac/t3-bb0e4397`), GitHub `notkainoa/rac`, and upstream `imputnet/helium-macos`. I only read things. I built nothing and ran nothing. Every number below comes from a command I ran: `git log`, `gh api`, `wc`, or a diff parser over `patches/rac/**`. Where something is my inference rather than a measurement, I say so.

## 0. Headline numbers (for side-by-side with Inbox Zero)

| Metric | rac |
| --- | --- |
| Age of rac's own work | 23 days (first rac commit 2026-10-02, last 2026-10-24). Before that the history is helium-macos back to 2019 |
| Commits by rac (non-merge) | 269, all by one human account (`notkainoa`) |
| Commits with an AI co-author trailer | 259 of 269 (96%): factory-droid 131, Claude Opus 5.5 108, Claude Fable 5.1 17, Cursor 13, Claude Sonnet 5.5 3 |
| Commits landed directly on `main` (first-parent, no PR) | 189 of 269 (70%) |
| Pull requests | 19 total: 14 merged, 5 closed. Median time to merge 1.6 h, max 17.7 h |
| Human approvals on any PR | 0. All 112 reviews have state `COMMENTED`: 74 by the maintainer's account, 25 by cubic-dev-ai, 13 by greptile-apps. CodeRabbit, Cursor, Pullfrog, and Vercel bots also comment on every PR |
| Branch protection on `main` | None ("Branch not protected") |
| Releases | 0. `rac_version.txt` = `0.1.0` |
| Stars / forks / watchers | 0 / 0 / 0 |
| Issues ever filed | 0 |
| Repo views in the last 14 days | 3 (2 unique). Clones 1,573 (221 unique), almost all from CI checkouts |
| External contributors to rac's layer | 0 |
| Revenue | None. No model exists |
| License | GPL-3.0 (inherited from Helium) |
| Code size | 180 quilt patches (110,741 patch lines). About 63k net lines in 325 new files, plus 3,429 added and 1,096 removed lines across 871 hunks in 217 existing Chromium files |
| Automated tests | 33 test files, about 284 `TEST`/`TEST_F` cases, in 5 test targets. **CI never compiles or runs them** |

The GitHub repo is still a fork of `imputnet/helium-macos`. Its description still says "Helium Browser for macOS", and its homepage still points at `racbrowser.vercel.app`, not racbrowser.com.

## 1. Product scope

### What exists as code

Patch groups in `patches/rac/` (patch count, approximate net added lines):

- **ai (39, ~19.5k net).** Settings and providers, a Dia-style chat side panel, page attachment, history and saved prompts, a new tab page that picks Search or Ask, find-in-page Ask, link hover summaries, an ACP client for Claude Code, Codex, Cursor, Gemini, Copilot, OpenCode, Goose, or a custom agent, model lists, and native menus.
- **agent (19, ~16.6k net).** Snapshot and refs, tools, an action runner on Chromium's actor framework, an MCP server over a Unix socket, the direct-provider tool loop, the guard, the critic, confirmation cards, the tab indicator, hardening, permission levels, site rules, and step rows.
- **spaces (26, ~9.6k net).** Data model, switching, saving, unloading, switcher dots, management, per-space appearance and colors, sliding transitions, and crash fixes.
- **pinned (18, ~5.2k net).** Sidebar store, favorites, pinned section, folders, drag, snap, and 6 fix patches.
- **look (20), sidebar-address-bar (10), sidebar-reveal (5), sidebar (4).** Restyle, top bar, address bar in the sidebar, edge reveal, and full/hidden modes.
- **settings (13), onboarding (6), pip (5), updates (4), branding (4), privacy (2), dev (5).**

### What is shipped

Nothing. There are no releases, no downloadable build, and nobody outside the maintainer has ever run rac (zero issues, zero stars). The site's download page is hidden (`RELEASE_READY = false` in `site/src/config.ts`).

### Status by roadmap phase (`docs/roadmap.md` claims "phase 3")

| Phase | Claimed | Evidence |
| --- | --- | --- |
| 0 Working build | done | Plausible. Local builds only |
| 1 Make it rac | done | Branding, privacy, and updates patches exist. **The updater has never run end to end**: no release has ever been published, so no feed exists |
| 2 Foundations | "built" | Spaces, pinned tabs and favorites, sidebar hide/reveal, sidebar address bar, and auto PiP all have patches. 24 of the 180 patches are named `fix-*`, and `fix` commits (121) outnumber `feat` commits (99). Spaces and pinned tabs alone have 1 and 22 tests |
| 3 Finish features | in progress | Space themes: partly done (colors, appearance, `dia-colors`). AI basics: built. **Media controls in the sidebar: no patch exists.** Settings cleanup: 13 patches, partial |
| 4 Ready to release | partly | Icons and DMG art: merged (PRs #7, #8). Onboarding: built. **Bangs: "nothing on this page is a design"** (`docs/internals/bangs.md`). **Performance check: not done; no benchmark exists anywhere.** Micro-interactions: partial. **CI and releases: not working yet** (§5). **No Apple Developer account** (team ID empty), so builds are signed ad hoc |
| 5 After release | optional | Agent: built early (about 17k lines, the riskiest code in the project). Command bar, Boosts, **Arc import**, and Dia import: none exist |

Effort has gone almost backwards relative to the roadmap. The optional phase-5 agent and the AI layer together hold about 36k of the ~63k net new lines (57%). Meanwhile release blockers (signing, notarization, a working release pipeline, performance proof, an upstream sync) are unfinished, and Arc import, the obvious feature for Arc refugees, doesn't exist. Two features the vision calls core, the command bar and boosts, are absent.

## 2. Size and rebase burden

My parser normalizes `a/`, `b/`, and `src/` path prefixes. It classifies each file a patch touches as one of three kinds:

- **new:** the patch creates it from `/dev/null`.
- **rac-own:** a later rac patch edits a file an earlier rac patch created.
- **upstream:** an existing Chromium, Helium, or ungoogled-chromium file.

| Group | Patches | New files | Lines in new files | Upstream file edits | Upstream hunks | +/− in upstream files | Patch-on-patch edits | Lines added by those edits |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ai | 39 | 107 | 13,139 | 56 | 98 | +299/−41 | 261 | 12,695 |
| agent | 19 | 72 | 10,456 | 26 | 58 | +198/−9 | 153 | 6,557 |
| spaces | 26 | 48 | 7,782 | 69 | 127 | +526/−64 | 70 | 2,100 |
| pinned | 18 | 26 | 3,920 | 44 | 95 | +377/−45 | 41 | 1,365 |
| sidebar-address-bar | 10 | 11 | 2,643 | 24 | 64 | +216/−35 | 12 | 260 |
| onboarding | 6 | 14 | 2,101 | 13 | 24 | +47/−22 | 21 | 718 |
| look | 20 | 13 | 792 | 71 | **161** | **+1,020/−324** | 50 | 1,232 |
| settings | 13 | 12 | 793 | 44 | 91 | +342/−320 | 12 | 84 |
| sidebar | 4 | 4 | 526 | 6 | 11 | +34/−28 | 13 | 391 |
| pip | 5 | 7 | 419 | 17 | 28 | +99/−7 | 5 | 149 |
| dev | 5 | 2 | 345 | 2 | 3 | +3/−0 | 6 | 502 |
| updates | 4 | 5 | 227 | 19 | 34 | +92/−28 | 3 | 38 |
| sidebar-reveal | 5 | 4 | 139 | 31 | 60 | +135/−126 | 8 | 23 |
| branding | 4 | 0 | 0 | 9 | 11 | +35/−16 | 1 | 2 |
| privacy | 2 | 0 | 0 | 6 | 6 | +6/−31 | 0 | 0 |
| **Total** | **180** | **325** | **43,282** | **437** | **871** | **+3,429/−1,096** | **656** | **26,116** |

What this says:

- **Good:** the AI and agent code mostly follows the "new files, small hooks" rule. ai and agent together add about 23.6k lines of new files against only 156 upstream hunks.
- **Bad:** the UI groups do not follow it. `look`, `settings`, `sidebar-reveal`, `spaces`, and `pinned` account for 534 of the 871 upstream hunks. 320 of all upstream hunks land in `chrome/browser/ui/views/`, which `docs/internals/overview.md` itself calls the upstream area that "changes often" and needs "the most refresh work".
- 217 distinct upstream files are touched, and 36 of them by three or more rac patches. The worst are `chrome/browser/ui/BUILD.gn` (26 patches), `settings_localized_strings_provider.cc` (13), `prefs_util.cc` (11), `browser_command_controller.cc` (10), `browser_view.cc` (9), `vertical_tab_strip_region_view.cc` (9), and `browser_view_tabbed_layout_impl.cc` (8). The same hot file is edited by many ordered patches, so one upstream change there cascades into several patch refreshes.
- **Patch-on-patch layering is heavy.** There are 656 later edits to rac-owned files (+26k/−6.3k lines). One example is `agent/12-hardening.patch`, a 3,781-line patch whose job is to repair earlier agent patches. PR #11 ("fold agent fix patches into the patches they fix") shows the maintainer knows. The result is still a deep, order-dependent stack of 180 patches that only quilt holds together.
- **It depends on Google's moving AI internals.** The AI and agent code builds on `optimization_guide` AnnotatedPageContent (about 60 call sites) and the Glic `actor` framework. It patches `chrome/renderer/actor/*` and `chrome/common/actor.mojom`, and flips `kGlicActorToctouValidation` on. Google is actively developing these as part of Gemini-in-Chrome. Expect them to break or change shape across Chromium majors, and ungoogled-chromium may strip pieces.
- **"A thin layer on top of Helium"** (the site's own words) is false by any measure. This is a 110k-line patch stack, about two thirds the size of a mid-sized app, touching 217 Chromium files.

## 3. AI architecture (as designed in `docs/internals/ai.md`, spot-checked in code)

### Providers

- **Your own key:** OpenAI, Anthropic, Gemini, OpenRouter, or a custom OpenAI-compatible endpoint. Keys are encrypted with `os_crypt_async`. Base URLs must be https, or http only for localhost.
- **Local:** Ollama and LM Studio, through their OpenAI-compatible endpoints.
- **Installed agents over ACP v1 (JSON-RPC over stdio):**
  - Claude Code and Codex through npx adapters pinned to exact versions, so they need Node.js.
  - Cursor, Gemini, Copilot, OpenCode, Goose, or a custom command.
  - The agent starts in an empty scratch directory with a scrubbed environment.
  - `initialize` advertises no file, write, or terminal capability, and each agent's recipe removes its shell, file, and web tools. The docs themselves call those recipes a soft second layer.

### Data flow and what leaves the machine

- **Chat:** with a page attached, the page text (APC extraction, hidden-text filtered, capped at 8192 tokens per block) plus the conversation goes to the chosen provider. For ACP agents it goes to whatever cloud that CLI uses (Anthropic, OpenAI, Cursor, and so on).
- **Model lists and connection checks:** `GET {base}/models` with the key, when the menu or the Assistant settings page opens.
- **Link summaries:** Option+hover for 500 ms fetches the linked page from the user's IP, in a throwaway off-the-record profile (cookies blocked, JS off). The text goes to the provider. The hover itself makes a network request to a site the user never opened.
- **Critic (only at `careful`):** goal, tool name, role, origins, and booleans go to the user's direct provider. It never sees page text.
- **Nothing goes to rac.** There is no rac server.

### Prompt-injection defenses

- Page text is wrapped in a nonce-delimited block, and a system prompt tells the model it is reference material. This defense is soft: it depends on the model obeying.
- The hidden-text filter is admitted incomplete. `opacity:0` text and text pushed above the page pass through.
- Refs are published versus private, with TOCTOU re-validation of element identity, target URL, and form submission at each boundary where page script can run.
- URL provenance: navigation targets must come from a user message or a link in a snapshot the model was shown.
- Containment: navigation, popups, downloads, and file pickers are restricted on documents the agent touched, and the restrictions survive Stop.
- The critic never sees page content.

### Action gating

`ActionGuard` returns block, plan, confirm, or allow:

- **Always blocked:** downloads, non-http(s) URLs, URLs of unknown provenance, closing the user's tabs, and `never` sites.
- **Always a card, at every level:** submit controls, Enter, password, payment, and file fields, risky verbs (buy, send, delete, sign in, upload), and unclassifiable clicks.
- **Levels:** `ask`, `careful` (plan card plus critic), and **`auto`, the default**.
- **Step cap:** 25 tool calls per turn.
- **ACP permission requests:** approved only when runtime-set metadata proves the tool is rac's MCP tool (verified for Claude and Codex). Gemini, Copilot, and Goose can't use rac's tools at all.

### "AI off costs nothing"

- `AiServiceFactory` returns null unless AI is on and the profile is regular. `AgentController` is created only when AI and browser control are on.
- Pref listeners stay registered, visible UI is created lazily, and turning AI off cancels and dismantles.
- **The guarantee rests on code review plus a manual audit patch (`ai/14-off-audit`).** No automated test asserts zero processes, requests, or allocations with AI off, and no performance measurement exists.
- After AI has been turned on once, services that were built stay in memory, dormant.

### Open concerns the doc itself lists

1. Script on an approved page can still `fetch()`, write storage, and so on. Containment covers input and navigation; it is not a sandbox.
2. Agents without a trusted identity are rejected: Gemini, Copilot, and Goose can't use rac's tools.
3. Provider terms for running a subscription through another app can change.
4. Setup (installing a CLI and Node, signing in) is hard for non-developers.
5. Speed: 15 s for Cursor and about 25 s for Claude Code from Send to the first tool call, because every message cold-starts the agent.
6. Agents' model lists aren't shown.
7. Rough edges in the tools (`press_key` only presses Enter, named-window forms are denied, tab ownership doesn't carry over between turns).

### A concern the doc does not list (my analysis, confirmed in code)

At the default `auto` level, `agent/13-permission-levels.patch` allows these without any card:

- a cross-origin `navigate` or link click to a site the user never named (`AutoAsksOnlyForRiskAndForeignTyping` asserts `navigate` to `other.com` is `kAllow`)
- every read
- **typing model-generated text into a plain field on the attached ("named") site**

That leaves an exfiltration path the default policy permits:

1. A hostile attached page contains injected instructions and a link to a site where the user is logged in. The provenance rule is satisfied, because the link is in the snapshot.
2. The agent opens that link in the user's real profile, with real cookies, and reads it. Both steps are free.
3. The agent types what it read into a field on the hostile page. This is also free.
4. The page's own key listeners send it out. No submit, and so no card, is needed.

Containment does not stop this, because step 4 is page script, which is exactly open concern #1. Whether real models follow such an injection is an empirical question nobody has measured: there is no red-team suite or eval in the repo. A browser agent shipping with `auto` as the default and no injection evals is the single biggest security exposure in the project.

Smaller items:

- During a run, any same-user process can connect to the MCP socket (the doc says so).
- The `--rac-window-screenshot` and `--rac-agent-debug` switches are compiled into release builds. They are not behind a build flag, although `--rac-agent-debug` is off unless the switch is passed.

## 4. Privacy posture

- **To rac:** nothing. There are no rac servers, accounts, telemetry, or analytics, and the site also has no analytics or third-party scripts (`docs/operations/site.md`, `site/src/pages/privacy.astro`). This matches the code I read.
- **Crash reports:** off by *disabling*, not removal. `privacy/disable-crash-uploads.patch` empties the upload URL and forces the mode to "disabled". Crashpad still writes reports locally, which are then deleted.
- **To Helium (imput) servers:** extension downloads, uBlock filter lists, spell check, the bangs list, and component updates, all behind Helium's consent screen at first run. rac's privacy story therefore depends on a third party's servers and policy, and on that third party continuing to serve a fork that isn't affiliated with it.
- **To GitHub:** the Sparkle update check against `github.com/notkainoa/rac/releases/latest/download/appcast-<arch>.xml`, at launch and then hourly. It is on by default, can be turned off on About rac, and exposes IP and version to GitHub/Microsoft.
- **To Google:** inherits ungoogled-chromium's removals. I did not audit residual Chromium endpoints. rac adds none that I saw.
- **To AI providers:** only with AI on. Page content goes to the chosen cloud, or stays local with Ollama or LM Studio.
- **Site claims:** "Nothing phones home" is a slogan, but the site's own table discloses Helium services, the update check, and the AI provider, which is honest. "Never slower than Helium" has no measurement behind it.

## 5. Engineering process

### Velocity

- 269 commits in 12 active days. Per ISO week: 20 in W40, 0 in W41, 117 in W42, 132 in W43.
- Per day: 60 on Oct 12 and 45 on Oct 17.
- About 110k patch lines were produced in about 3 weeks. That is only possible because of the parallel worktrees, each driven by an AI agent (factory-droid, Claude, Cursor), which the trailers confirm.
- Fix churn is high: 121 `fix` versus 99 `feat` commits, and 67 of those fixes are in ai/agent.

### Review practice

- 70% of commits bypass PRs entirely.
- The 19 PRs each get 4–6 AI review bots (CodeRabbit, Greptile, cubic, Cursor Bugbot, Pullfrog), and the maintainer's account replies in threads.
- No PR has ever been approved. The merge median is 1.6 h, for PRs of up to +9,310 lines (#15) and +4,657 (#6).
- Pullfrog's workflow (`.github/workflows/pullfrog.yml`) has **failed or been cancelled on every one of about 50 runs**, and nobody has fixed it.
- In practice the review is AI reviewing AI, with one human accountable for it. The early PRs #1–#5 (5–8k lines each) were closed, and those features later landed by other routes, mostly direct pushes.

### Tests

- Five targets: `rac_ai_unittests`, `rac_agent_unittests`, `rac_spaces_unittests`, `rac_updates_unittests`, and `rac_pip_tests`.
- About 284 cases: ai 157, agent 87, spaces 22, pip 9, updates 6, look 2, pinned 1. There is 1 browser test (`page_context_browsertest.cc`).
- **0 tests for:** sidebar, sidebar-reveal, sidebar-address-bar, settings, onboarding, branding, and privacy. Pinned tabs (18 patches, ~5k lines, 6 fix patches) has a single test.
- There are no UI or integration tests. Verification is a policy in AGENTS.md: the agent takes screenshots of a running build.
- **CI never builds or runs any test.**

### CI state

- `lint.yml` checks patch series syntax.
- `sanity.yml` applies all patches to a Chromium tarball and **runs the build for 30 seconds, then succeeds on timeout**. It catches patches that fail to apply or apply with offsets. It does not catch compile errors, link errors, or test failures in rac code. Historically 30 of 137 sanity runs failed.
- The release workflow (`build.yml` → 10 chained `build-phase.yml` jobs) has never succeeded:
  - 3 failures: once in resource download, twice in `do-build`.
  - The current run (40149762883) is on branch `ci/sccache-gha-runtime`, not `main`. It started 01:13Z.
  - Phases 1 and 2 took about 4.5 h and 5.1 h. At 15:09Z, about 14 h in, phase 3 of up to 10 was still running.
  - **Even if it passes, it signs ad hoc** (`sign_and_package_app.sh` falls back to `codesign --sign -` and skips notarization) **and runs a sccache configuration that has never been proven.**
  - A release cycle is measured in many hours to days of macOS runner time.

### Upstream sync burden and risk

- rac's base is helium-macos `992a020`, Helium **0.18.2.1, Chromium 154.0.8037.92**.
- Upstream is now Helium **0.20.1.1, Chromium 156.0.8078.47**. rac is 15 upstream commits and 7 Helium releases behind, and **two Chromium majors behind** (`gh api compare`: `ahead_by 15`). The missing releases are 0.18.3.1, 0.19.1.1, 0.19.1.2, 0.19.2.1, 0.19.3.1, 0.19.4.1, and 0.20.1.1.
- Upstream also changed its build toolchain in the meantime ("remove toolchain workarounds, use full chromium toolchain").
- **rac has never performed a sync.** `docs/operations/upstream-sync.md` is an untested procedure, and this worktree has no `upstream` remote configured.
- Chromium ships a major version about every 4 weeks, so every month each of the 871 upstream hunks has to be refreshed against new code, plus the Glic/actor/APC dependencies.
- A browser that ships two majors behind ships with known, public Chromium security bugs. Every month of feature work instead of syncing makes the first sync bigger.
- PR #10 ("refresh rac patches that applied with offsets") shows the patches already drift against a *fixed* base.

### Bus factor

1 human, who is also the sole user. Everything depends on:

- that maintainer's attention, Mac, and roughly 100 GB build tree
- paid AI agent capacity
- Helium's small core team (wukko, dumbmoron, and Cubik do most upstream commits)

Helium bans AI-written contributions (AGENTS.md), so rac can never upstream fixes and has no relationship with the project it depends on.

## 6. Distribution and business

- **Distribution:** none.
  - No release and no Apple Developer account (signing and notarization are unproven; `PROD_MACOS_*` secrets are not configured, per the docs).
  - An ad-hoc-signed browser downloaded from the web is blocked by Gatekeeper on first launch. Since macOS 15 it can only be opened through System Settings › Privacy & Security, a hard wall for the non-developer Arc refugees rac targets.
  - **Inference, not tested:** with ad-hoc signing, the code identity changes on every build, so Keychain access to "rac Storage Key" (which protects cookies, passwords, and the encrypted API keys) will probably prompt the user after each update.
- **Site:** Astro, Tailwind, and React islands on Vercel. Live at racbrowser.com (HTTP 200) with download buttons that say "Coming soon, star the repo". The repo has 0 stars.
- **Audience signal:** 2 unique repo visitors in 14 days, 0 issues, 0 community. No waitlist, newsletter, or other audience capture on the site, by design (no data collection).
- **Business:** no revenue model, no stated intention of one, no accounts, and GPL-3.0. The AI costs the user's own key or subscription, so there is no margin to capture.
- **Market timing:**
  - Arc shuts down 2026-12-22, about 58 days from this audit, which is the obvious acquisition window.
  - Competitors are shipping: Ardia (open source, Dia-like, 70 releases) and Yab (closed, AI-first, WebKit, 35+ versions).
  - rac has 0 releases and **no Arc import** (phase 5, not started).
- **Positioning:** "Arc on Helium with optional AI" is coherent and the privacy stance is genuinely differentiated. But it is a personal project with public docs, not a product with users.

## 7. The ten most serious risks and weaknesses (ranked)

1. **It ships nothing, and the release path is unproven end to end.**
   - 0 releases.
   - The release workflow has never succeeded (3 failures, 1 run in flight on a non-main branch, about 14 h in at phase 3 of up to 10).
   - No Apple Developer account, so signing is ad hoc and notarization is skipped.
   - The Sparkle feed has never been exercised in production.
   - The update key and feed URL can never change once released (AGENTS.md "Ways to hurt yourself" #6). A rushed first release locks in whatever is wrong.

2. **Two Chromium majors behind, and the sync has never been done.**
   - The base is Chromium 154 / Helium 0.18.2.1; upstream is Chromium 156 / Helium 0.20.1.1.
   - 871 hunks across 217 upstream files, 320 of them in `chrome/browser/ui/views/`.
   - Sole-maintainer refresh, monthly, forever.
   - A browser that can't keep pace with Chromium security releases is unsafe to recommend. This is the structural risk that kills most Chromium forks.

3. **The default agent policy permits a prompt-injection exfiltration chain.**
   - At `auto` (the default): cross-origin navigation is free (test `AutoAsksOnlyForRiskAndForeignTyping`), reads in the user's logged-in profile are free, and typing model text on the attached site is free.
   - Page script can read the typed text, which is admitted open concern #1.
   - The injection defense against the model itself is a nonce-wrapped prompt, which is soft.
   - No red-team or eval suite exists. For a privacy-first browser this is the sharpest contradiction.

4. **No CI build or test of rac code.**
   - "Sanity" builds for 30 seconds and passes on timeout.
   - About 284 unit tests exist, but nothing runs them automatically.
   - Seven feature groups (sidebar, reveal, address bar, settings, onboarding, branding, privacy) have zero tests, and pinned tabs has one.
   - Correctness rests on agents' screenshots and the maintainer's daily use.

5. **AI-only review on a security-sensitive codebase.**
   - 96% of commits are AI co-authored, 70% go straight to `main`, and `main` has no branch protection.
   - 0 PR approvals ever, with a 1.6 h median merge on PRs up to +9k lines. The review bots review AI output, and one of them (Pullfrog) fails on every run.
   - The agent's guard, containment, and MCP permission logic are about 17k lines of security-critical C++ that no second human has read.

6. **Bus factor of one, plus a hostile-by-policy upstream.**
   - One human; zero contributors, stars, or issues.
   - It depends on paid agent capacity and a 100 GB local tree. CI release builds take a day or more.
   - Helium bans AI contributions, so rac can't upstream anything and must absorb every Helium change unilaterally.
   - It also uses Helium's servers for extensions, filter lists, spell check, and bangs, with no agreement in place.

7. **Priorities are inverted relative to the market window.**
   - About 57% of new code is AI and agent, and the agent is formally a phase-5 "optional, after release" feature.
   - Meanwhile Arc import, the command bar, boosts, media controls, a performance check, and bangs are missing or undesigned, with Arc shutting down in about 58 days.
   - Competitors have 35 and 70 releases. rac has spent its runway on the feature least likely to make an Arc refugee switch.

8. **Rebase debt inside rac itself.**
   - 180 strictly ordered patches.
   - 656 patch-on-patch edits (+26k/−6.3k), and 24 `fix-*` patches.
   - Hot upstream files are edited by many patches (`ui/BUILD.gn` by 26, `settings_localized_strings_provider.cc` by 13).
   - Spike and "review-followups" patches (`ai/00-apc-spike`, `ai/fix-review-followups`) remain in the series.
   - Fix commits outnumber feature commits (121 to 99): the code is still being stabilized, not finished.

9. **Heavy dependence on Google's Gemini-in-Chrome internals.**
   - The AI and agent are built on `optimization_guide` AnnotatedPageContent and the Glic `actor` framework.
   - rac patches the renderer actor tools and `actor.mojom`, and flips `kGlicActorToctouValidation` on.
   - Google can rename, restructure, gate, or remove these in any milestone, and ungoogled-chromium may strip parts. The most valuable rac code sits on the least stable foundation.

10. **Unbacked claims, no distribution, no business.**
    - "Never slower than Helium" and "AI off costs nothing" have no benchmark or automated check behind them; the phase-4 performance check isn't done.
    - The site calls rac "a thin layer on top of Helium", but it is 110k patch lines.
    - The GitHub repo still describes itself as "Helium Browser for macOS".
    - An ad-hoc-signed download faces a Gatekeeper wall for mainstream users.
    - There is no revenue model or audience capture, GPL-3.0 limits any proprietary upside, and there is zero measured demand (2 unique visitors in 14 days).
    - As a business it does not exist yet. As a project it is one person's well-documented, AI-built daily driver.

### What is genuinely strong

So the comparison is fair:

- The docs are unusually rigorous. `docs/internals/ai.md` records concrete traps and the reasons behind decisions, not marketing.
- The agent safety design is thoughtful well beyond typical hobby projects: TOCTOU re-validation, published versus private refs, containment that survives Stop, a critic that never sees page text, runtime-identity checks on ACP permissions, and fail-closed timeouts.
- AI is off by default and incognito is excluded.
- The privacy posture is honest and disclosed.
- The new-file discipline is real in the ai and agent groups.
- The worktree system lets one person run 3–5 features in parallel.

The weakness is not the quality of the thinking. It is everything around the code: shipping, syncing, testing, review, and users.
