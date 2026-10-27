# 07. Customization, automation, and power features

## In plain English

This plan adds a few Arc habits. Copying a link drops its tracking junk. Arc's shortcuts work for rac's own actions. New tab groups get a sensible name.

Next come Boosts, which let you restyle a site you visit often. You can recolor it, change its font, make it dark, or click an annoying element to hide it. A code view lets you write your own CSS. Boosts never run code.

Then comes Air Traffic Control. It sends links from other apps to the right space, so a Slack link opens in your Work space. Last come bangs, shortcuts like `!w cats` that search Wikipedia. You can add and fix your own bangs.

Only the copy and shortcut pieces can make the launch build before Arc shuts down on 2026-12-22. Boosts and link routing follow in the first weeks after. Everything works with AI off, costs nothing until used, and sends nothing anywhere.

## What you need to decide

1. **07-D1. What can a Boost do?** No-code looks plus a CSS editor / also JavaScript. **Recommended: looks only. JavaScript is deferred, and `VISION.md`'s "CSS and JavaScript" line changes to match.**
2. **07-D2. Which links does Air Traffic Control route?** Links from other apps / every link. **Recommended: links from other apps only.**
3. **07-D3. Where does clean-link copy apply?** Shift+Cmd+C and the tab menu / also the page's "Copy link address". **Recommended: Shift+Cmd+C and the tab menu only. No setting.**
4. **07-D4. How are tab groups named?** A simple rule / the rule plus a "Name with AI" button when AI is on. **Recommended: the rule plus the button.**
5. **07-D5. How much bangs work?** An editor page only / editor plus an address-bar rework. **Recommended: the editor now. The address-bar rework gets its own go or no-go after the sync.**
6. **07-D6. Chrome Web Store themes and space colors?** The store theme overrides, with a notice / space colors always win. **Recommended: the store theme overrides, with a notice in the space editor.**
7. **07-D7. Whose shortcuts?** Chrome's for standard actions and Arc's for rac's own / Arc's everywhere. **Recommended: Chrome's for standard actions, Arc's for rac's own.**
8. **07-D8. In what order?** By Arc-refugee demand (Boosts, then routing, then bangs) / by the roadmap (bangs first). **Recommended: by demand.**

Decided elsewhere: Clear, the archive, and auto-archive belong to plan 01 (see 01-D7). Debug doors belong to plan 05 (see 05-D6). Routines and recipes also belong to plan 05 (see D59 in decisions.md, and 05-D8).

## Where we are today

- **Copying links.** Shift+Cmd+C already copies the page URL. It runs Helium's pref `kCopyPageUrlShortcut`, which is on by default. When that pref is off, the shortcut opens Inspect instead (`build/src/chrome/browser/ui/browser_ui_prefs.cc:205`, `browser_command_controller.cc:1577-1585`, FACT). The copy goes through `FormatURLForCopy` (`browser_commands.cc:284`), which feeds `CopyURL` and `CopyURLs`. Nothing strips tracking parameters (FACT).
- **Cleaning opened links.** Helium's built-in uBlock Origin turns on "AdGuard/uBO – URL Tracking Protection" by default, and "uBlock filters – Privacy" holds 220 `removeparam` rules (`build/src/third_party/ublock/assets/assets.json`; `assets/ublock/privacy.min.txt`, FACT). So opened links already lose common trackers. The lists ship inside the app.
- **Hiding page elements.** uBlock's context-menu "Block element…" is on by default (`third_party/ublock/js/background.js:108`, FACT). It saves to uBlock's "My filters", not to a per-site Boost.
- **Bangs** come from Helium (`helium-chromium/patches/helium/core/add-native-bangs.patch`, `helium/ui/bangs-ui.patch`). The list has 10,730 entries and 13,421 triggers (`plans/research/helium.md:74`). It downloads from Helium services, and only the cache is used when that service is off (`template_url_bang_manager.cc:86-112`). A bang is added only if no search engine already has that keyword (`template_url_service.cc:1737-1753`). A bang's keyword is `!` plus its trigger (`template_url_data_util.cc:536`). So a user's own `!w` site search already beats the downloaded `!w`, and it loads with services off (FACT). Typing `cats !w` still shows "Google search" (`docs/internals/bangs.md`). The bang patches touch about 30 files, many in the omnibox (FACT).
- **Shortcuts.** Helium has a full custom-shortcut system and page (`helium/core/custom-keyboard-shortcuts.patch`, 2,222 lines). rac adds space commands as `case` labels in Helium's `browser_shortcut_metadata.cc` (`patches/rac/spaces/commands.patch:157-190`). Each new command adds a hunk there.
- **Groups.** Chromium tab groups exist among open tabs. They start unnamed. rac locks "auto-pin new tab groups" off (`patches/rac/settings/behavior-autopin-tab-groups-off.patch`).
- **Air Traffic Control.** There is none. Links from other apps enter at `-application:openURLs:` (`app_controller_mac.mm:2062`). Plan 01 adds its little-window router there (`plans/01-ui-shell.md`, M3).
- **Boosts.** There are none. `VISION.md` and `docs/internals/glossary.md` define them as "custom CSS and JavaScript".
- **Themes.** rac has 8 space themes. Chrome Web Store themes survive rac's reset (`patches/rac/spaces/space-owns-appearance.patch`, `ResetBrowserTheme`), and their colors "still win" (`patches/rac/spaces/dia-colors.patch:168`, FACT). rac has no browser mods. Its UI is C++ Views, not CSS, so Zen-style mods don't apply (`plans/research/zen.md:135`).
- **Extensions.** The Chrome Web Store works through Helium's anonymizing proxy, and full MV2 uBlock is included (`digests/helium.md`). In the sidebar address bar layout, site controls list extensions (`patches/rac/sidebar-address-bar/site-controls.patch`).

## What others do

Sources: `plans/research/matrices/features.md`, `plans/research/matrices/ui-and-feel.md`, and the digests named.

| Feature | Who, and how | Lesson |
|---|---|---|
| Boosts | Arc had no-code Boosts (colors, fonts, Zap) and CSS or JS code Boosts, synced through a cloud database. That rule let anyone attach a JS Boost to another account (CVE-2024-45489, 9.8, `digests/closed-ai-browsers.md`). Zen is CSS only: recolor, font, Zap, picker, "Focus" (`zen.md:137`). Yab's "Look" Boosts run no code. | No-code first. Local only. No code in the cloud |
| Link routing | Arc ATC uses "contains" and "is equal to", for links from other apps. Zen adds regex and "Add route for domain" (`digests/zen.md`). Nook matches domain or path, longest match wins, and never routes sign-in pages (`digests/nook.md`). | Two rule types, top to bottom, skip sign-in |
| Clean links | Arc Supercopy (Shift+Cmd+C). Ardia: clean copy and Copy as Markdown (`ardia.md:64`). Stedding also strips on open, with 14 behaviors and a Blink hook (`stedding:docs/features/clean-links.md`). | Copy is cheap. uBlock already covers open |
| Group names | Dia names groups with AI. Ardia uses a deterministic rule (`ardia/apps/browser/src/store/groupNames.ts`, Apache-2.0). | A rule covers most cases |
| Bangs | Helium, Ardia, Nook, Ora. Ora shows a tab-to-search chip with one border sweep (`digests/ora.md`, take 4). | Show where the search goes |

Arc's own data says 5.52% of daily users used more than one space (`digests/closed-ai-browsers.md`, CLAIM). The features matrix ranks Boosts 6th and ATC 9th among reasons Arc users hesitate. Bangs are not an Arc feature (`matrices/features.md`, "Gaps").

## Options

### Option A: Demand order, small hooks

Build in the order Arc refugees feel the gaps: copy and shortcuts, then no-code Boosts, then routing, then bangs. Use what Helium, Chromium, and uBlock already have, and add thin rac code only where nothing exists.

- **Details.** Clean copy is one hook in `FormatURLForCopy`. Shortcuts are fields in plan 03's action table (ruling 2). Boosts are no-code controls that write CSS, plus Zap and a CSS view. ATC plugs into plan 01's router. The bangs editor reuses Chromium's site-search entries plus one deleted-bangs list.
- **Pros.** Value lands where users notice it. There are few upstream hunks, and each piece ships alone.
- **Cons.** Bangs, which you asked for, come last. Boosts need an injection spike first.
- **Effort.** About 35 to 55 agent-days across M0 to M5 (the milestone sums below).
- **Risk.** Low to medium.
- **Locks in.** Looks-only Boosts, which can grow later.

### Option B: Roadmap order, small hooks

Same mechanics as A, but bangs come before Boosts and routing, as in `docs/roadmap.md` (bangs in phase 4, Boosts in phase 5, ATC "Later").

- **Pros.** It follows a plan you already wrote. Bangs are cheap now that user entries already beat the list.
- **Cons.** Arc users wait longer for the two features they actually miss.
- **Effort and risk.** Same as A.

### Option C: One "Sites and rules" platform first

Build one local rules engine before any feature. Every per-site customization becomes a rule: route, Boost, keep loaded, auto-clean.

- **Pros.** One store, one page, one door for agents.
- **Cons.** Platform work delays user value. ATC rules must be global (they pick a profile), while Boosts are per profile, so the store splits anyway. A generic engine goes against "opinionated".
- **Effort.** L, 40+ agent-days, with value arriving late.

### Recommendation

**Option A.** Graft from C a single shared `SitePattern` matcher ("domain is" or "URL contains"), used by ATC and Boosts. Also from C, the site control center is the one per-site entry point ("Boost this site", "Always open in…"). Plan 01 places it. From B, keep the bangs editor small, so it can slot in early if a worktree is free.

## Recommended plan

Code goes in new files under `chrome/browser/rac/<feature>/` and `chrome/browser/ui/rac/<feature>/`. Upstream files get hooks only. Patch groups are `patches/rac/power/`, `boosts/`, `routing/`, and `bangs/`. Weeks count from plan approval. Plan 06 owns the Helium 0.20.1.1 sync (Chromium 156), the base-tree rebuild after it, and the launch calendar (hard stop for the launch build: 2026-12-15). Work in hot files shared with Helium waits for the sync plus that rebuild. Work in rac-owned files may start on Chromium 154 and be rebased. Effort is in agent-days for one maintainer directing agents (INFERENCE).

| Milestone | Starts | Chromium | Target |
|---|---|---|---|
| M0 Matcher and table fields | after plan 03 M1 and the sync | 156 | before M1 hooks |
| M1 Arc habits | logic week 1; hooks after the sync | 156 | launch build if merged by the start of W5; else first update |
| M2 Boosts basics | spike week 2 on 154; build after the sync | 156 | about 3 to 5 weeks after launch |
| M3 Air Traffic Control | after plan 01's little-window hook | 156 | early January |
| M4 Bangs editor | after the sync | 156 | January |
| M5 Bangs address-bar label | go or no-go after M4 | 156 or 157 (plan 06) | February, if approved |

### M0. Matcher and action-table fields (3 to 5 agent-days)

- **Goal.** Two small foundations, with no table of our own.
- **Tasks.**
  1. Write `rac::SitePattern` in `chrome/browser/rac/site_pattern/`. Plan 07 owns it. It handles host matching (subdomains included) and "URL contains", is case-insensitive, and uses Chromium's registrable-domain helper (not Nook's suffix list, `digests/nook.md`).
  2. Add "default shortcut" and "menu label" fields to plan 03's action table (03 M1). Helium's shortcut metadata then reads labels from that table through one hook. That replaces the per-command `case` hunks in `patches/rac/spaces/commands.patch`. This rewrites merged work, so re-test every space shortcut.
- **Acceptance.** Space shortcuts still list and rebind in Helium's shortcuts page. `browser_shortcut_metadata.cc` carries one rac hunk.
- **Verification.** Unit tests for `SitePattern`. A screenshot of the shortcuts page.
- **Patch surface.** About 2 hunks replace roughly 4 (net negative).

### M1. Arc habits (6 to 9 agent-days)

- **Goal.** The no-setup habits Arc users reach for daily.
- **Tasks.**
  1. **Clean-link copy (07-D3).** `FormatURLForCopy` passes through `rac::CleanLink()`. That covers Shift+Cmd+C, Edit > Copy URL, and the tab menu (INFERENCE that Helium's tab-menu copy uses `CopyURLs`; verify). It strips a conservative compiled-in list: `utm_*`, `fbclid`, `gclid`, `dclid`, `msclkid`, `mc_eid`, `igshid`, `_hsenc`, `mkt_tok`, and share-only names on known hosts. It is based on Stedding's L2 table (BSD-3, notice kept, `long-tail.md` C7). The fragment and the order of other parameters stay. The page's "Copy link address" and Cmd+C in the address bar stay exact, so the user always has a way to the original. If `kCopyPageUrlShortcut` is off, Shift+Cmd+C stays Inspect, and Edit > Copy URL still copies clean.
  2. **Copy as Markdown** (Shift+Opt+Cmd+C): `[title](clean url)`.
  3. **Arc keymap for rac actions (07-D7)**, as rows in plan 03's table. These cover the command bar, Clear, Copy as Markdown, and route to space. Check each against Chromium's and Helium's tables. For example, Opt+Cmd+C stays Inspect (`global_keyboard_shortcuts_mac.mm:165`). Plan 01 settles Opt+Cmd+N, which Helium uses for split view.
  4. **Group naming (07-D4).** Port Ardia's 99-line rule (Apache-2.0, credited). It uses the shared site name from titles, else a tidy host, else "site + page". It names a group at creation and keeps renaming it as tabs join, until the user edits the name. With AI on, a "Name with AI" button sits in the rename field and sends titles and hosts only when clicked. It doesn't touch the locked auto-pin behavior.
- **Acceptance.** Copying `https://x.com/a?utm_source=y&id=3#c` gives `https://x.com/a?id=3#c`. Three GitHub PR tabs make a group named "GitHub". With AI off, no AI button appears (ruling 16). It works in incognito, where copy is cleaned and naming works.
- **Verification.** Unit tests for the strip table, including cases that must not change, and Ardia's naming cases ported one for one. Screenshots via `--rac-window-screenshot` of the copy toast and a named group, in light and dark, sidebar full and hidden, two spaces, and incognito.
- **Patch surface.** About 4 hunks: copy, two accelerator rows, and the group-editor hook.

### M2. Boosts basics (spike 2 to 3 days, build 12 to 18 agent-days)

- **Goal.** Restyle a site without writing code (07-D1).
- **Tasks.**
  1. **Injection spike.** Compare three paths:
     - (a) A built-in component extension with `document_start` content scripts. It needs all-sites access, which shows in `chrome://extensions`, in site controls, and in incognito rules.
     - (b) A native host type in Chromium's user-script system.
     - (c) A rac-owned browser-side observer that injects a stylesheet at commit, through a small renderer hook. rac already has its own renderer Mojo (`snapshot.mojom`, `digests/rac-baseline.md`).
     - Pass criteria: no flash of unstyled content on a test page; zero Boosts loads nothing; no all-sites permission shown to the user; correct in incognito and in the little window.
  2. **No-code panel**, opened by "Boost this site" in site controls:
     - Recolor: a hue shift with images re-shifted back, INFERENCE quality "approximate".
     - Font: one of four system families, with icon fonts excluded.
     - Dark: injected CSS inversion with media re-inverted. The spike also tries per-tab force-dark through WebPreferences, since the content setting is Android-only (`content_settings_registry.cc:601-612`).
     - Zap: click an element to hide it, with a 150 ms fade, remembered per site, with Undo.
  3. **CSS view.** The panel's choices appear as CSS, editable by hand, with live preview. Boosts are per profile, local, and exportable as `.css`. There is no gallery, store, or sync.
  4. **Userscript check.** Verify that Violentmonkey (MV2) installs and runs in rac. Also check what Tampermonkey on MV3 needs (likely the "Allow user scripts" toggle, INFERENCE). Name the extension that works in the help text for anyone who wants code.
- **Acceptance.** Boosts survive restart and apply before first paint. Zero Boosts means no script and no file read at startup. Boosts apply in incognito and the little window, and the editor is not offered in incognito. One global on/off sits in the Boosts list, as Arc added after its incident.
- **Verification.** Before and after screenshots of a boosted site in light and dark, sidebar hidden, and split view. A video of Zap and Undo with Reduce Motion on and off. A startup trace with zero Boosts compared against Helium (plan 06 bench).
- **Patch surface.** 1 to 4 hunks, depending on the spike.

### M3. Air Traffic Control (6 to 9 agent-days)

- **Goal.** Links from other apps open in the right space (07-D2).
- **Tasks.**
  1. Rules are a `SitePattern` plus a target (profile and space). They are stored in Local State prefs, because rules pick a profile. That matches plan 04's "prefs if small" row. The first match from the top wins.
  2. ATC adds no new hook. It plugs a lookup into plan 01's router, ahead of the little window. If the target profile has no open window, or the space is gone, the link goes where plan 01 sends it, with an "Open in Work" chip. ATC never opens a profile just for a link.
  3. **Sign-in safety, minimal rule.** Never route a URL whose host starts with `accounts.`, `login.`, `auth.`, or `sso.`. Never route one whose path contains `oauth`, `authorize`, `callback`, or `saml`. Always show a one-click "Open here instead". Never route into or out of incognito.
  4. Entry points: "Always open <site> in this space" in site controls; a list under Settings > Spaces (plan 01 places it); "Open link in space…" in the link menu; a command bar action.
  5. Convert Arc's routing file, which plan 04 keeps raw in `<profile>/rac imports/` (`plans/04-data-storage-import-sync.md`, M1 item 7).
- **Acceptance.** `open` of a matching URL from Terminal lands in the right window and space. A cold profile falls back with the chip. No rules means one empty-list check and nothing else.
- **Verification.** Unit tests for matching, fallbacks, and the sign-in rule. Screenshots of the settings list and site-controls row. A video of a link from another app landing in a background space.
- **Patch surface.** 0 to 1 hunks (the link-menu entry).
- **Depends on** plan 01 M3 (the router), and on rac being the default browser (plan 01's onboarding step).

### M4. Bangs editor (3 to 5 agent-days)

- **Goal.** Users add, edit, and delete bangs (07-D5). This is a maintainer want, not an Arc-refugee need.
- **Tasks.**
  1. Adding or editing a bang creates the user's own `!trigger` site-search entry. It already beats the list and loads with services off (FACT, above).
  2. Deleting a bang adds its trigger to `rac.bangs.deleted`, which is checked in the same `BangsLoadedCallback` loop. That is one pref and one hunk.
  3. A searchable "Bangs" page under Search, with "Yours" above the list. Reuse Chromium's site-search edit dialog. First check whether the 13,421 triggers already flood the site-search page.
- **Acceptance.** Every "Editable bangs" item in `docs/internals/bangs.md` holds. Rewrite that page as decisions land.
- **Verification.** Unit test: a deleted trigger stays deleted after a list update. Screenshots of the page.
- **Patch surface.** 1 to 2 hunks.

### M5. Bangs address-bar label (5 to 8 agent-days, go or no-go)

- **Goal.** `cats !w` reads "Search Wikipedia for cats" with the bang's chip, and an unknown bang reads as a normal search.
- **Gate.** First diff Helium 0.20.1.1's `omnibox_edit_model.cc`, `keyword_provider.cc`, `autocomplete_input.cc`, and `selected_keyword_view.cc` against 154. If Helium reworked them, wait one sync.
- **Tasks.** Change the default match label. Add Ora's one-shot chip sweep, with no sweep under Reduce Motion. Plan 01's command bar uses the same engine, so it inherits the label.
- **Acceptance.** Typing latency with bangs stays within Helium's noise (plan 06 bench). Screenshots: bang at the start, bang at the end, unknown bang, top bar, sidebar address bar, sidebar hidden, and split view.
- **Patch surface.** 3 to 6 hunks in Helium-patched files. This is the plan's riskiest rebase.

### Later

- **JavaScript Boosts**, only if 07-D1 is reopened. They would be local only, in an isolated world, and never on pages with password or payment fields.
- **"Describe a change"** (AI on only). The model writes CSS only, shown before it applies. Plan 05 lists it among actions that need a card.

## Fit with the non-negotiables

- **Private.** Nothing here makes a network request. The strip table and naming rule are compiled in. Boosts, routes, and bang edits are local. No Boost gallery, store, or sync exists, so Arc's CVE class has nowhere to live. "Name with AI" sends titles only when clicked.
- **Never slower than Helium.** Each feature is idle until used. Copy runs on copy, routing on a link from another app, and bang deletion is one check at list load. Boosts load nothing when none exist, which the M2 spike must prove. M2 and M5 ship only after plan 06's bench numbers.
- **AI off costs nothing.** Everything works with AI off. The one AI button exists only when `AiServiceFactory` returns a service, and no AI label appears otherwise (ruling 16).
- **Cheap to update.** About 11 to 19 upstream hunks across M0 to M5, and M0 removes some. The M5 hunks in Helium's omnibox are the risk, so M5 is gated.
- **Calm UI.** Motion is short fades (Zap 150 ms) and a one-shot chip sweep, with Reduce Motion paths. Nothing loops. New settings are a Bangs page, a routing list, and a Boosts list.
- **Opinionated.** Clean copy and group naming have no settings.
- **GPL.** Ardia's rule (Apache-2.0) and Stedding's table (BSD-3) are compatible, with credit and notices kept.
- **`VISION.md` change (07-D1).** Boosts become "restyle a site's look", not "CSS and JavaScript". The cost: Arc refugees who relied on JS Boosts lose them, and plan 04's import summary must say so.

## Dependencies on other plans

- **01 ui-shell.** It places every entry point: the command bar, site controls ("Boost this site", "Always open in…"), and Settings > Spaces. It owns Clear, `MayClear`, the archive, and auto-archive (ruling 4; 01-D7), and media controls (ruling 12). Input for 01's `MayClear`: spare tabs playing media, in picture-in-picture, in split view, in agent use, or with downloads in progress. Drop "unsent form text", because Chromium keeps no general dirty-form flag (`beforeunload` only fires if a page registers it), and spare only pages that registered `beforeunload`. ATC needs 01's router and the default-browser step.
- **02 visual-design-and-motion.** Motion tokens for Zap and the chip sweep. Plan 02 also owns any custom space-theme editor. The Web Store theme notice (07-D6) needs a design.
- **03 core-architecture.** It owns the single action table (ruling 2). Plan 07 adds the shortcut and label fields to it. Plan 03 also sets the patch-surface metric (ruling 11). Routines are plan 05's (D59 in decisions.md), so plan 05 decides that, not plan 07.
- **04 data-storage-import-sync.** Storage formats for Boosts and routes. Arc's raw routing file (M3 task 5). Two import items:
  - (a) Say in the import summary that JavaScript Boosts are not imported.
  - (b) Add a spike to find Arc's local Boost files, and convert CSS-only ones if they parse.
- **05 agents-and-ai.** It owns routines, recipes, the outside-agent door, and debug doors. On debug doors (ruling 7): `chrome://inspect` remote debugging is off by default, needs a user toggle, and each connection needs approval. Add to plan 05's card list: an agent never creates or edits a Boost, route, or bang without a card, and "Describe a change" always shows its CSS first.
- **06 engineering-and-shipping.** The sync, the base-tree rebuild, the calendar, the perf bench (startup with zero Boosts, typing with bangs), and CI for the unit tests.

## Risks and unknowns

- **Helium churn under bangs.** About 30 bang-related files, mostly omnibox. That is why M5 is gated.
- **Helium may ship the same thing.** If Helium adds a bangs editor, adopt it (`VISION.md`, "Relationship with Helium").
- **Clean-copy false positives.** Keep the list conservative, and use share-only names on known hosts only.
- **Boost injection.** Path (a) shows an all-sites permission. Paths (b) and (c) cost more hunks. The no-code dark and recolor modes are approximate on image-heavy sites.
- **ATC sign-in rule.** It is a heuristic. "Open here instead" is the safety net.
- **Arc data after shutdown.** Routing and Boost files may change or vanish (`digests/closed-ai-browsers.md`, caveats).
- **Shortcut conflicts** with system, input-method, and extension shortcuts.

## Open questions

1. Does the site-search settings page already list all 13,421 bang triggers?
2. Does Violentmonkey run in rac, and does Tampermonkey need a toggle? (M2 task 4)
3. Do 1Password and Bitwarden desktop apps connect to rac? If not, link only their native-messaging hosts, never agent hosts (`cra.md:339-344,451`).
4. Can Arc's local Boosts be read at all? Cra did not read them (`cra.md:637`). Plan 04's spike decides.
5. Should Boosts and routes become per space once plan 04 adds separate sign-ins? The default assumption is no.
6. Rejected finding: "add a hold-Option exact copy on the page menu". The page menu simply stays exact, which is simpler.
7. Partly rejected finding: the strawman options. The old all-of-Arc option is gone, and demand order is now Option A. Option C stays, even though the vision leans against it, because it shows what a rules engine would cost.
8. Deferred, no owner yet: localhost developer bar, AppleScript for spaces (plan 05's door may cover it), and abandoned new tabs clearing themselves (plan 01 could take it).

## Draft thread brief

**DRAFT. Not to launch until the maintainer approves plan 07 and its decisions.**

> **Thread: power features (rac).** Build plan 07 (`plans/07-power-features.md`) using the maintainer's answers to 07-D1 through 07-D8. Read `docs/internals/bangs.md` and the plan in full.
>
> **Order.** M1's logic and the M2 spike may start on Chromium 154 in rac-owned files. Every upstream hook waits for plan 06's sync and base-tree rebuild. M0 waits for plan 03 M1. M3 waits for plan 01's little-window router. M5 needs its own go-ahead after its Helium diff check. Use one worktree per milestone.
>
> **Plan-specific rules.**
> - No network requests.
> - No AI label with AI off.
> - No second action table: add fields to plan 03's.
> - Every per-site entry goes through site controls, placed by plan 01.
> - Credit Ardia and Stedding with their notices.
> - Report upstream hunks per PR, using plan 03's metric.
>
> **Done means.** Unit tests pass. Screenshots from your own build cover light and dark, sidebar full and hidden, two spaces, split view, and incognito where it applies. Motion gets a short video with Reduce Motion on and off.
>
> **Models.** Opus for the Boosts panel and settings pages. Sonnet for matchers, stores, and tests.
