# 07. Customization, automation, and power features

## In plain English

This plan covers the small tools that make a browser feel like yours. These are copying clean links, editing bangs, Arc's shortcuts, sending links to the right space, clearing old tabs, naming groups for you, and restyling sites with Boosts.

What a user notices first: Shift+Cmd+C copies a link without the tracking junk, and Arc's shortcuts do what Arc users expect. New groups get a sensible name. Plan 01 builds the Clear button. This plan sets what Clear may close, and whether old tabs are ever cleared for you.

Next comes a bangs page where you add and fix your own bangs. Typing `cats !w` then shows "Search Wikipedia", not "Google search". After that comes link routing. A Slack link from another app opens in your Work space.

Boosts come last. Hide an annoying page element, or add your own CSS to a site. Boosts change looks only. Code-running Boosts wait, because userscript extensions already do that job.

Everything works with AI off and costs nothing until used. Nothing is downloaded, synced, or sent anywhere. Most of this lands after the first release. None of it decides whether an Arc user can switch.

## What you need to decide

1. **07-D1. What can a Boost do?** Options: looks only (CSS and hide element) / also JavaScript / no Boosts. **Recommended: looks only for now.** JavaScript waits for real demand. This narrows `VISION.md`, which says "CSS and JavaScript".
2. **07-D2. Tab clean-up: manual or automatic?** Options: manual Clear only / opt-in auto-clean, off by default / auto-clean on by default. **Recommended: manual Clear plus the archive now. Opt-in auto-clean later, off by default, that keeps an imported Arc user's own setting.** This is the same question as 01-D6, with the same answer, so answer it once. Opt-in auto-clean bends `VISION.md` "Not planned: auto-archiving".
3. **07-D3. Which links does Air Traffic Control route?** Options: links from other apps only / every navigation. **Recommended: links from other apps only**, plus a manual "Open in space" menu item.
4. **07-D4. Clean links: on copy, or on open too?** Options: copy only / copy and open / neither. **Recommended: copy only, always on, no setting.** For links you open, rely on uBlock Origin's URL-cleaning lists.
5. **07-D5. How are groups named?** Options: simple rule only / AI names automatically when on / simple rule plus "Name with AI" on request. **Recommended: the simple rule always. "Name with AI" is a button, only when AI is on.**
6. **07-D6. Where does the bangs editor live?** Options: inside Chromium's site search list / its own page under Search. **Recommended: its own "Bangs" page under Search.** Your edits are stored as changes on top of Helium's list.
7. **07-D7. Browser mods and Web Store themes?** Options: support Zen-style UI mods / no mods. For Web Store themes: let them override space colors with a notice / always ignore them. **Recommended: no mods. Web Store themes keep working, and the space editor says when one is overriding.**
8. **07-D8. Whose shortcuts win?** Options: Arc's keymap everywhere / Chrome's keymap, plus Arc's for rac-only actions. **Recommended: Chrome's for standard actions, Arc's for rac's own.** All rebindable in Helium's shortcuts page.
9. **07-D9. Developer extras now?** Options: localhost dev bar and AppleScript for spaces now / later. **Recommended: later.** The `chrome://inspect` toggle is plan 05's call.
10. **07-D10. Link other browsers' password-manager connections (Cra-style)?** Options: yes / no / test first. **Recommended: test 1Password and Bitwarden first. If needed, link an allow-list only, never agent hosts.**

## Where we are today

- **Bangs** come from Helium (`helium-chromium/patches/helium/core/add-native-bangs.patch`, `helium/ui/bangs-ui.patch`). `BangManager` downloads `bangs.json` from Helium services. It falls back to cache only when the setting is off (`build/src/components/search_engines/template_url_bang_manager.cc:86-112`, FACT). Each trigger becomes a `TemplateURL` (`template_url_service.cc:1737-1741`). The list holds 10,730 entries and 13,421 triggers (`plans/research/helium.md:74`, FACT). Nothing is editable. `cats !w` still says "Google search" (`docs/internals/bangs.md`). Helium's bangs touch about 30 files, many in the omnibox (FACT, `+++` lines of both patches). So an address-bar rework edits Helium-patched files.
- **Keyboard shortcuts.** Helium ships a full custom-shortcut system and settings page (`helium/core/custom-keyboard-shortcuts.patch`, 2,222 lines; `helium/settings/custom-keyboard-shortcuts-page.patch`). rac registers space commands by adding `case` labels to Helium's `browser_shortcut_metadata.cc` (`patches/rac/spaces/commands.patch:157-190`, FACT). So every new rac command adds another hunk to that file. Shift+Cmd+C already copies the page URL by default, through `kCopyPageUrlShortcut` (`build/src/chrome/browser/ui/browser_ui_prefs.cc:205`, `browser_command_controller.cc:1577-1585`, FACT).
- **Copying links.** `FormatURLForCopy` (`build/src/chrome/browser/ui/browser_commands.cc:284`) feeds `CopyURL` and `CopyURLs`. Nothing strips tracking parameters (FACT). Chromium has no built-in parameter stripper (INFERENCE, grep of `components/`).
- **Groups.** Chromium tab groups exist among open tabs. rac locks "auto-pin new tab groups" off (`patches/rac/settings/behavior-autopin-tab-groups-off.patch`). New groups and folders start unnamed (INFERENCE, no naming code found).
- **Tab clean-up.** There is none. Hidden spaces unload after 15 minutes but keep their tabs (`plans/research/digests/long-tail.md`, citing `spaces_window_manager.h:65,134-137`). `VISION.md` lists "auto-archiving old tabs" as not planned.
- **Air Traffic Control.** There is none. Links from other apps enter at `-application:openURLs:` (`build/src/chrome/browser/app_controller_mac.mm:2062`, FACT). It sits in the roadmap's "Later" (`docs/roadmap.md`).
- **Boosts.** There are none. `VISION.md` and `docs/internals/glossary.md` define them as "custom CSS and JavaScript". They are in roadmap phase 5.
- **Themes and mods.** There are 8 space themes and no editor (`plans/research/matrices/ui-and-feel.md`, space theming row). Chrome Web Store themes survive rac's reset (`patches/rac/spaces/space-owns-appearance.patch`, `ResetBrowserTheme`). Their colors "run later and still win" (`patches/rac/spaces/dia-colors.patch:168`, FACT). There are no browser mods.
- **Extensions.** These are the Chrome Web Store through Helium's anonymizing proxy, plus full MV2 uBlock Origin (`plans/research/digests/helium.md`). In the sidebar address bar layout, extensions are listed in site controls (`patches/rac/sidebar-address-bar/site-controls.patch`).
- **Developer features.** DevTools comes from Chromium. Dev switches such as `--rac-window-screenshot-requests` are ungated in every build (`plans/research/digests/rac-baseline.md`). Chromium's `chrome://inspect` remote-debugging toggle is on for macOS and unpatched (`plans/research/digests/long-tail.md`, B1). No outside-agent door exists (plan 05).

## What others do

Sources: `plans/research/matrices/features.md`, `plans/research/matrices/ui-and-feel.md`, and the digests named below.

| Feature | Who ships it, and how | Lesson for rac |
|---|---|---|
| Boosts | Arc: no-code (colors, fonts, Zap) and CSS/JS code Boosts, a gallery, sync. Its cloud rule let anyone attach a JS Boost to another account (CVE-2024-45489, 9.8) (`digests/closed-ai-browsers.md`). Zen: CSS only, recolor, Zap, element picker, "Focus" (`zen.md:137`). Yab: "Look" Boosts run no code, plus userscripts and a reviewed store. Ardia: userscripts. Aside: "Remix" beta | Looks first, local only, never synced as code |
| Mods | Zen: CSS packages for the browser's own UI, unsigned, auto-updated from a store (`zen.md:135,587`) | rac's UI is C++ Views, not CSS. Skip |
| Link routing | Arc ATC ("contains", "is equal to", from other apps). Zen adds regex and "Add route for domain" (`digests/zen.md`). Nook: domain or path, longest match, never sign-in pages (`digests/nook.md`). Crest, Stedding, Refrax ship it (`digests/long-tail.md`) | Two rule types, top to bottom, skip sign-in flows |
| Clean links | Arc Supercopy (Shift+Cmd+C). Ardia: clean-link copy and Copy as Markdown (`ardia.md:64`). Stedding strips on open too: 14 behaviors and a Blink loader hook (`stedding:docs/features/clean-links.md`) | Copy is cheap. Open is costly and fragile |
| Tab clean-up | Arc auto-archives after 12 h, sparing media (`digests/closed-ai-browsers.md`). Dia offers Cleanup at 10+ stale tabs. Cra archives with a reason (`digests/cra.md`). Arc and Dia have Clear with Undo | Manual first. Recoverable always |
| Auto-named groups | Dia names groups (AI). Ardia uses a deterministic title-and-host rule, no AI (`ardia/apps/browser/src/store/groupNames.ts`, Apache-2.0) | A rule covers most cases |
| Bangs | Helium, Ardia, Nook, Ora. Ora's tab-to-search chip with one border sweep (`digests/ora.md`, take 4) | Show where the search goes |
| Shortcuts | Helium, Crest, Dia, Cra (`keybindings.json`), Zen | Reuse Helium's system |
| Developer | Nook DevMCP and element picker (`digests/nook.md`). Crest and Arc localhost dev bar (`long-tail.md` "Other" table). Dia and Helium AppleScript (`digests/helium.md`, take 11) | Mostly plan 05. Dev bar later |
| Extensions | Cra links other browsers' native-messaging hosts so 1Password connects. It excluded ChatGPT's host after it "took over Cra" (`cra.md:339-344,451`) | Allow-list, deliberately |

Arc's own usage data: 5.52% of daily users used more than one space, and 4.17% used live folders (`digests/closed-ai-browsers.md`, CLAIM). Habits that need no setup matter more than power features. The features matrix ranks Boosts 6th and ATC 9th among reasons Arc users hesitate (`matrices/features.md`, "Gaps").

## Options

### Option A: Arc parity sprint

Build everything Arc had, the way Arc had it, before Arc shuts down on 2026-12-22. That means Boosts with JavaScript, auto-archive on by default, routing for every link, and Arc's keymap everywhere.

- **Details.** It would be a JS and CSS Boost editor, a gallery-free local store, auto-archive at 12 h, ATC on all navigations, Arc shortcuts replacing Chrome's, and AI group naming whenever AI is on.
- **Pros.** It has the most familiarity for Arc refugees. It is easy to market.
- **Cons.** It competes for the same 56 days as release, Arc import, and the command bar (plans 06, 04, 01). JavaScript Boosts repeat Arc's worst incident class. Auto-archive on by default contradicts `VISION.md`. Arc's keymap breaks Chrome users. AI naming sends tab titles to a provider without a request.
- **Effort.** L to XL, about 40 to 55 agent-days.
- **Risk.** High: security, patch surface, and calm.
- **Locks in.** JS execution and an archive data model, before anyone has used either.

### Option B: Inherit first, small hooks

Use what Helium, Chromium, and uBlock Origin already have. Add a thin rac layer only where nothing exists. Copy cleaning goes in one function. Shortcuts go through Helium's system. "Hide element" can start from uBlock's picker. Routing and Clear are new, small, rac-owned code.

- **Details.** Clean copy is a hook in `FormatURLForCopy` with a compiled-in parameter table. Shortcuts are one rac table behind a single hook in Helium's metadata. Bangs are an overlay file on top of Helium's list. ATC reuses plan 01's external-link hook. Clear (plan 01's) asks one rac predicate which tabs it may close. Boosts use CSS only, injected through Chromium's content-script machinery.
- **Pros.** Fewest upstream hunks. Each piece ships alone. Everything costs nothing until used.
- **Cons.** Some seams show, such as uBlock's picker styling if used as-is. Per-site features end up scattered across settings pages.
- **Effort.** M to L, about 27 to 37 agent-days over three to four months. Clear and the archive are counted in plan 01.
- **Risk.** Low to medium. The main risk is Helium's omnibox churn under bangs.
- **Locks in.** Little. CSS-only Boosts can grow later.

### Option C: One "Sites and rules" platform

Build one local rules engine first. Every per-site customization becomes a rule: route, boost, keep loaded, clean-link exception, and later auto-clean. One store, one settings page, one data model, and one door for plan 05's recipes and outside agents.

- **Details.** A `SiteRule` has a matcher and a list of actions. The site control center edits rules for the current site. A "Sites" page lists them all.
- **Pros.** It is coherent. Import, backup, and future sync handle one thing. Agents get one permissioned surface.
- **Cons.** Platform work comes before any user value. ATC must be global (it picks a profile), but Boosts are per profile, so "one store" splits anyway. It is a generic engine, which the vision's "opinionated" rule warns against.
- **Effort.** L, about 35 to 45 agent-days, with value arriving late.
- **Risk.** Medium. It is easy to over-design.
- **Locks in.** A schema every later feature must fit.

### Recommendation

**Option B, with two pieces grafted from C and one from A.**

- From C: one shared, tested `SitePattern` matcher ("domain is" or "URL contains", with registrable-domain logic). ATC, Boosts, and clean-link exceptions all use it. Also from C: the site control center as the single per-site entry point ("Boost this site", "Always open in…"). The stores stay separate, so there is no rules engine.
- From A: Arc's keymap for rac-only actions, and carrying an imported Arc user's own auto-archive setting.

B is the only option that fits next to the release, import, and sync work without adding risk. It also keeps the patch-surface budget plan 03 is cutting.

## Recommended plan

All work is new files under `chrome/browser/rac/<feature>/` and `chrome/browser/ui/rac/<feature>/`, with hooks only. Patch groups are `patches/rac/power/` (clean links, shortcuts, groups), `patches/rac/bangs/`, `patches/rac/routing/`, `patches/rac/cleanup/`, and `patches/rac/boosts/`. Effort is in agent-days for one maintainer directing agents (INFERENCE).

### M0. Shared pieces (2 to 3 agent-days, after the first Helium sync)

- **Goal.** Two foundations that make later hooks one line each.
- **Tasks.**
  1. Write `rac::SitePattern` with unit tests: host match covering subdomains, "URL contains", and lowercase. Use Chromium's registrable-domain helper, not a suffix list (Nook's mistake, `digests/nook.md`).
  2. Write one rac command table (id, label, default shortcut, availability), Zen-style (`digests/zen.md`, take 6). Helium's shortcuts page reads it through `rac::shortcuts::GetLabel(command_id)`, which replaces the per-command `case` hunks in `browser_shortcut_metadata.cc` with one call. Do the same for `global_keyboard_shortcuts_mac.mm`. Plan 01's command-bar action table should be this same table, and so should plan 05's tool list where it names browser actions (`plans/05-agents-and-ai.md`, plan 07 dependency). Agree that with both threads before building.
- **Acceptance.** Existing space shortcuts still show in Helium's shortcuts page and still rebind. `browser_shortcut_metadata.cc` carries exactly one rac hunk.
- **Verification.** Unit tests (`rac_power_unittests`). A screenshot of the shortcuts page listing rac commands.
- **Patch surface.** Net negative. About 2 hunks replace the current per-command hunks.

### M1. Arc muscle memory (4 to 6 agent-days; can land with or right after 0.1.x)

- **Goal.** The no-setup habits Arc users reach for daily.
- **Tasks.**
  1. **Clean link copy.** `FormatURLForCopy` passes through `rac::CleanLink()`. This covers Shift+Cmd+C, the tab menu's Copy URL, and multi-tab copy (INFERENCE that Helium's tab-menu copy uses `CopyURLs`; verify). Also hook the page menu's "Copy link address" (`render_view_context_menu.cc`, one hunk). Strip only a conservative compiled-in list: `utm_*`, `fbclid`, `gclid`, `dclid`, `msclkid`, `mc_eid`, `igshid`, `_hsenc`, `mkt_tok`, `si` on known share hosts, and similar. Base the table on Stedding's L2 list, which is BSD-3, with the notice kept (`long-tail.md`, C7). Keep the fragment and the order of other parameters. Cmd+C in the address bar stays exact.
  2. **Copy as Markdown** (Shift+Opt+Cmd+C): `[title](clean url)` (Crest and Ardia).
  3. **Arc keymap for rac actions.** These are command bar, Clear, Copy as Markdown, the little window, and route to space. Check each against Chromium's and Helium's tables before adding. For example, Shift+Cmd+C is already copy, and Opt+Cmd+C stays Inspect (`global_keyboard_shortcuts_mac.mm:164-165`, FACT). Helium already uses Opt+Cmd+N, Arc's Little Arc key, for a new split tab (`plans/01-ui-shell.md`, risks). Plan 01 decides that one. Every rac command appears in the menu bar and in Helium's shortcuts page.
  4. **Auto-named groups, AI off.** When a tab group or folder is created unnamed, fill in a name from a port of Ardia's rule (`groupNames.ts`, 99 lines, Apache-2.0, credited). It takes the shared site name from titles, else a tidy host, else "site + page" when all tabs share both. The name is pre-selected, so typing replaces it. Two hooks: the tab group editor and rac's folder creation.
  5. **Clean-up rules, for plan 01's Clear and archive** (plan 01, M2 task 4 builds both; plan 04 stores the archive). This plan owns one rac-owned predicate, `rac::cleanup::MayClear(tab)`, with unit tests. Clear never closes pinned tabs or favorites, or a tab that is playing media, in picture-in-picture, in a split view, being used by the agent, or holding unsent form text (Chromium's before-unload check). Each archive entry records a reason (cleared, closed, little window, auto, space removed), as Cra does (`digests/cra.md`, take 7). The same predicate later drives auto clean-up (M5), so both paths spare the same tabs.
- **Acceptance.** Copying `https://x.com/a?utm_source=y&id=3#c` gives `https://x.com/a?id=3#c`. A group of three GitHub PR tabs is named "GitHub". `MayClear` spares every listed case. Everything works with AI off and in a fresh profile.
- **Verification.**
  - Unit tests for the strip table (including the cases that must not change), the naming rule (port Ardia's cases), and `MayClear`.
  - Screenshots via `--rac-window-screenshot` of the copied-link toast and a named group and folder, in light and dark, sidebar full and hidden, and in a second space.
  - A video of a space with a playing video being cleared, showing that tab stays.
- **Patch surface.** About 6 upstream hunks: copy, page menu, two accelerator rows, and two naming hooks. Clear's hunks are counted in plan 01.

### M2. Bangs you can edit (design 2 days, build 6 to 9 agent-days)

- **Goal.** Do what `docs/internals/bangs.md` asks, and rewrite that page as decisions land.
- **Tasks.**
  1. **Overlay store.** `rac.bangs.overrides` holds changes keyed by trigger: added, edited, or deleted. Apply them once in a hook after `BangsLoadedCallback` (one hunk in `template_url_service.cc`). A deleted bang stays deleted. An edited bang keeps the user's version. User bangs load even with Helium services off, or before the list arrives. If an update changes a bang the user edited, the user's version wins, and the settings row shows "Updated by the list" with a revert link.
  2. **Bangs page** under Search. It is searchable, groups "Yours" above the list, and has add, edit, and delete. Reuse Chromium's site-search edit dialog where it fits. First check whether 13,421 triggers already flood the site-search page (open question).
  3. **Address bar flow.** Whenever a bang is present, at the start or the end, the default match reads "Search Wikipedia for cats" with the bang's chip. An unknown bang reads as a normal search, with no chip. Add Ora's single border sweep on the chip, skipped under Reduce Motion (`digests/ora.md`, take 4). Plan 01's command bar uses the same omnibox engine, so it inherits this behavior.
- **Acceptance.** Every row in `bangs.md` "What the maintainer wants" holds. Typing latency with bangs on stays within the perf bench's noise of Helium (plan 06).
- **Verification.** Unit tests for overlay merge, including an update arriving after an edit. Screenshots of the page and of the address bar in each state: start bang, end bang, unknown bang, top bar and sidebar address bar. Run the typing benchmark.
- **Patch surface.** 3 to 6 hunks, several in Helium-patched omnibox files. Do this after the first Helium sync. If Helium ships its own bangs editor first, adopt it (`VISION.md`, "Relationship with Helium").

### M3. Air Traffic Control (5 to 8 agent-days; Arc rule import with plan 04)

- **Goal.** Links from other apps open in the right space.
- **Tasks.**
  1. Rules live in Local State, because they pick a profile. Each rule is a `SitePattern` plus a target (profile and space id). The first match from the top wins. With no match, the link goes where plan 01 sends it: the little window by default (01-D5).
  2. Plan 01 adds one hook in the macOS "open URLs" path for the little window (`plans/01-ui-shell.md`, M2 task 2). ATC adds no second hook. It plugs a rule lookup into the same rac-owned router, which runs before the little window. The command-line URL path goes through the same router.
  3. Never route sign-in and OAuth flows. Skip when the URL is an OAuth callback or the target space has no window open and the link came within seconds of a sign-in redirect (Nook's rule, `digests/nook.md`). The exact test is an open question.
  4. Entry points: "Always open <site> in this space" in site controls; a "Link routing" list under Settings > Spaces (where plan 01 places it); "Open link in space…" in the link context menu (manual); a command bar action.
  5. With plan 04: import Arc's `StorableLinkRouting.json` (the path is read by Cra, `digests/cra.md`).
- **Acceptance.** `open -a` of a matching URL from Terminal lands in the right space of the right profile window. A missing space falls back without error. With no rules, there is zero extra work: one empty-list check.
- **Verification.** Unit tests for matching and fallbacks. Screenshots of the settings list and the site controls row. A video of a link from another app landing in a background space.
- **Patch surface.** 0 to 1 hunks, since the external-link hook is plan 01's. The context-menu entry may need one.

### M4. Boosts: looks (spike 2 days, build 10 to 15 agent-days)

- **Goal.** Restyle a site without running code.
- **Tasks.**
  1. **Spike.** Choose the injection path: (a) a built-in component extension that registers content scripts at `document_start`, the precedent being Helium's uBlock component (`helium.md:112`); or (b) a native host type in Chromium's user-script system. Measure the flash of unstyled content and the cost with zero Boosts. It must load nothing when no Boost exists.
  2. **Hide element ("Zap").** Pick an element, it fades out in 150 ms (not Zen's 1,400 ms dissolve), and the choice is remembered per site. Undo is available, along with a list in site controls. Consider starting from uBlock's existing picker as a stopgap (INFERENCE that it is enabled in Helium; verify).
  3. **CSS Boost editor.** A WebUI page with a plain monospace editor and live preview on the current tab. Boosts are per profile, local, and exportable as a `.css` file. There is no gallery, store, or sync.
  4. **"Boost this site"** in site controls, and an on/off for each Boost there. One global switch exists only in the Boosts list, as Arc added after its incident.
  5. **Later in M4 or M5:** per-site dark pages. This needs the `AUTO_DARK_WEB_CONTENT` setting registered for desktop. It is Android-only today (`content_settings_registry.cc:601-612`, FACT; Stedding did this, `long-tail.md` take 8).
- **Acceptance.** Boosts survive restart and apply before first paint on a test page. Zero Boosts means no extension, no script, and no file read at startup.
- **Verification.** Before and after screenshots of a boosted site. A video of Zap and Undo. A startup trace with zero Boosts compared against Helium (plan 06 bench).
- **Patch surface.** 1 to 3 hunks (component registration, menu entry).

### M5. Later backlog (each needs its own go-ahead)

- **Opt-in auto clean-up** (S-M). One choice, "Clean up tabs I haven't used in: Never / 12 hours / 1 day / 1 week", default Never. Arc import carries the user's `autoArchiveTimeThreshold` (`digests/cra.md`). It never touches tabs that are playing media, in PiP, in split view, used by the agent, or pinned. It checks on space switch and window focus only, so there is no timer when set to Never. Needs a `VISION.md` edit.
- **"Name with AI"** (XS, AI on only) in the rename field. It sends titles and hosts, which the button's tooltip says.
- **"Describe a change" for Boosts** (S, AI on only). The model writes CSS only, shown before it applies. Coordinate with plan 05.
- **Abandoned new tabs clear themselves** (XS, Dia 1.38, `long-tail.md`).
- **AppleScript dictionary for spaces** (S-M), for Raycast and Shortcuts users. Coordinate with plan 05's outside-agent door.
- **Localhost developer bar** (M): viewport presets, console error count.
- **JavaScript Boosts** (M), only if the maintainer reopens 07-D1. If built, they are local only, run in an isolated world, never on pages with password or payment fields, and the agent never writes one without a card.
- **Native-messaging host linking** (S), only if 07-D10's test fails.

## Fit with the non-negotiables

- **Private.** Nothing in this plan makes a network request. The strip table and naming rule are compiled in. Bangs edits, routes, Boosts, and the archive are local files. Helium's bangs list stays behind Helium's consent. No Boost store, gallery, or sync exists. Executable customizations in the cloud are how Arc's CVE happened (`digests/closed-ai-browsers.md`). "Name with AI" and "Describe a change" send data only when the user clicks, only with AI on.
- **Never slower than Helium.** Each feature is idle until used. Copy runs on copy. Routing runs on a link from another app. Bangs add one merge at list load. Boosts load nothing with zero Boosts. Auto clean-up, if ever built, has no timer at Never. Bangs typing and Boost startup are measured in plan 06's bench. *Bent:* nothing, but M2 and M4 cannot ship until those numbers exist.
- **AI off costs nothing.** Every feature works fully with AI off. The two AI extras are buttons that exist only when `AiServiceFactory` returns a service (`docs/internals/ai.md`, "AI off costs nothing").
- **Cheap to update.** About 11 to 17 upstream hunks across M0 to M4. M0 removes several. The riskiest hunks are bangs in Helium's omnibox code, so M2 waits for the Helium sync.
- **Calm UI.** Motion is limited to short fades (Zap 150 ms, Clear rows using plan 02's tokens), one-shot chip sweeps, and Reduce Motion paths. Nothing loops. There are few new settings: one Bangs page, one Link routing list, one Boosts list. Auto clean-up is a single choice, if built.
- **Opinionated.** Clean copy has no setting. Group naming has no setting. *Bent:* auto clean-up (M5) is a setting, because Arc users genuinely split on it.
- **GPL.** Ardia's naming rule (Apache-2.0) and Stedding's parameter table (BSD-3) are compatible with credit and notices kept (`digests/ardia.md`; `long-tail.md`, C7).
- **`VISION.md` conflicts to resolve.** (1) Boosts "CSS and JavaScript" becomes looks first (07-D1). (2) "Auto-archiving: not planned" changes if M5 auto clean-up is approved (07-D2). Manual Clear does not conflict.

## Dependencies on other plans

- **01 ui-shell.** It owns where things appear and builds several pieces: the command bar (which lists every action here with its shortcut), Clear and the archive (01 M2, using this plan's `MayClear`), the little window and its external-link hook (which ATC reuses), the site control center, and Settings > Spaces (where Boosts and routing lists go). 01-D6 and 07-D2 are one decision. The Ctrl+Tab switcher is plan 01's. Plan 07 owns behavior and data, and gives plan 01 the action list from M1 to M4. Plan 01 lists "media controls behavior" under plan 07 (`plans/01-ui-shell.md`, dependencies). That was not in this plan's brief. Chromium's global media controls already provide the behavior, so plan 01 should own media controls end to end.
- **02 visual-design-and-motion.** Motion tokens for toasts, row removal, and Zap. The custom space theme editor (Zen harmony, T3 Code OKLCH) is plan 02's, not this plan's. The Web Store theme notice (07-D7) needs a design.
- **03 core-architecture.** The hook-and-table pattern and hunk budget. Per-space sign-ins make ATC much more valuable. Order: the first Helium sync before M0 and M2.
- **04 data-storage-import-sync.** Arc import of routing rules, the auto-archive threshold, and extensions by store id. The format and backups for the archive, Boosts, and overrides. Any later sync must never carry JavaScript.
- **05 agents-and-ai.** It owns routines, scheduled tasks, recipes (05-D10, 05-D11), skills, the outside-agent door, the `chrome://inspect` decision (`long-tail.md`, B1), dev tools over MCP, and AppleScript as an agent channel. This plan builds no rule engine or scheduler, so routines stay in one place. Plan 05 asks for a command bar that shares the agent's action table. M0's command table is offered as that shared source. Plan 05 also asks that Boost JavaScript never run on sensitive sites. With 07-D1 as recommended, no Boost runs JavaScript at all. Rule for both plans: an agent never creates or edits a Boost, route, or bang override without a confirmation card. Plan 07 provides "Name with AI" and "Describe a change" as small AI-on extras.
- **06 engineering-and-shipping.** The perf bench (typing, startup with zero Boosts), CI running `rac_power_unittests`, gating dev switches out of release builds, and a network capture proving no new hosts.

## Risks and unknowns

- **Helium churn under bangs.** Helium's bangs touch about 30 files and the omnibox is busy upstream. M2 waits for the sync and keeps logic in rac files.
- **Helium may ship the same thing.** It has open requests for a command palette (`digests/helium.md`, open questions). If it adds a bangs editor or shortcuts, adopt it.
- **Clean-copy false positives.** A stripped parameter could break a shared link. Keep the list conservative, with known share hosts only for `si`-style names. Add tests for "must not change".
- **Boost injection path.** MV3 content-script rules or user-script gating may block the component-extension route. The spike decides. A native host type would cost more hunks.
- **ATC and sign-in flows.** Routing an OAuth redirect into another space breaks sign-in. The detection rule is unproven.
- **Arc file formats after shutdown.** Routing and archive files may change or vanish (`digests/closed-ai-browsers.md`, caveats).
- **Shortcut conflicts.** System, input-method, and extension shortcuts can collide. Check every default against Chromium's table.
- **1Password.** Its desktop app may reject unknown browsers by code signature (INFERENCE). It is untested in rac.

## Open questions

1. Does Helium's uBlock ship any URL-cleaning (`removeparam`) list on by default? If not, should rac turn one on? That changes Helium's defaults. (07-D4)
2. Does Chromium's site-search settings page already list all 13,421 bang triggers?
3. Is uBlock's "Block element" picker enabled in Helium's build, and is it good enough as a stopgap Zap?
4. What exactly counts as a sign-in flow ATC must skip?
5. Should Clear also clear a space's split views, or leave them? (`MayClear` spares them for now.)
6. How long should the archive keep entries? Plan 04 sets the bound. Cra keeps 1,500 (`digests/cra.md`).
7. Do 1Password and Bitwarden desktop apps connect to rac today?
8. Can Arc's local Boosts be read for import at all? Cra did not read them (`cra.md:637`).
9. If plan 03 adds per-space sign-ins, should Boosts and routes be per space too? The default assumption is no.

## Draft thread brief

**DRAFT. Not to launch until the maintainer approves plan 07 and its decisions.**

> **Thread: power features (rac)**
>
> You are building plan 07 (`plans/07-power-features.md`) in rac, a quilt-patch Chromium fork on Helium. Read `AGENTS.md`, `VISION.md`, `docs/internals/overview.md`, `docs/internals/bangs.md`, `docs/internals/ai.md` ("AI off costs nothing"), and plan 07 in full. The maintainer's answers to 07-D1 through 07-D10 are final. Where they differ from the plan's recommendations, follow the answers.
>
> **Order.** M0, then M1, then M2 to M4 in parallel worktrees (one per milestone, `devutils/rac/worktree.sh setup`). Start M0 and M2 only after the first Helium sync has merged. M5 items need a separate go-ahead.
>
> **Rules.**
> - Feature code goes in new files under `chrome/browser/rac/<feature>/` and `chrome/browser/ui/rac/<feature>/`. Upstream edits are hooks only. Report the upstream hunk count for each patch in its PR.
> - Never edit `helium-chromium/` or Helium's patch folders. Never send anything upstream.
> - Nothing in this thread makes a network request. Everything works with AI off. Prove both in each PR (a fresh profile, AI off, and a net-log host list).
> - Register every new command through the M0 shortcut table, the menu bar, and the command bar action list from plan 01.
> - Credit Ardia (`groupNames.ts`, Apache-2.0) and Stedding (parameter table, BSD-3) with their notices.
>
> **Done means.** Unit tests in `rac_power_unittests` pass. You have opened the feature in your own build (`devutils/rac/worktree.sh run`). The PR embeds screenshots from `--rac-window-screenshot` covering: light and dark, sidebar full and hidden, top bar and sidebar address bar, two spaces, and incognito where it applies. Motion gets a short video with Reduce Motion on and off. Write it in AGENTS.md's "I tested" format, and list surfaces you could not check.
>
> **Models.** UI and settings pages: Claude Opus. Matchers, stores, and tests: Sonnet. Review: a separate Opus pass on each PR before the maintainer looks.
