# 01. UI shell and information architecture

## In plain English

This plan decides what a rac window holds, where each feature lives, and
what Arc users get before Arc shuts down on 2026-12-22.

The window keeps its shape: sidebar on the left, the page in a card, and the
assistant on the right. Three Arc habits come first. Cmd+T opens a command
bar that finds tabs, history, and actions. Shift-click opens a link in a
Peek preview. Links from other apps open in a little window.

If you agree (D28, D31), Cmd+L opens the command bar too, and Cmd+O moves a
Peek or little window into a space. A Clear button empties a space's open tabs, with Undo.

Plan 06's launch build carries the Helium update and the Arc import
screens. The command bar ships in the launch if it is merged by the start
of W5, otherwise as a point release in W6 before 12-22. Peek, the little
window, and Clear follow if they pass review in time.

With AI off, no AI button, row, or label appears anywhere.

Four changes need your sign-off: Peek, an optional auto-archive later, the
command bar as the default for Cmd+T, and moving these items ahead of the
roadmap.

Effort before 12-22 is about 38 to 55 agent-days. One shared Mac limits
parallel work, so stretch items may slip to January.

## What you need to decide

UI technology is plan 03's decision (03-D4: stay on Views); the command bar
is native Views (`plans/rulings.md`, ruling 3). Agent workspaces are 05-D3. Separate
sign-ins per space are 04-D6. Launch scope is plan 06's.

1. **01-D1. Does Cmd+T open the command bar?** Yes, plus one setting to get
   the new tab page back / yes, no setting / no. **Recommended: yes, plus
   one setting.**
2. **01-D2. What do Cmd+L and a click on the address bar do?** Both open the
   command bar (Arc) / Cmd+L opens it, a click edits in place / both edit in
   place. **Recommended: Cmd+L opens it; a click edits in place.**
3. **01-D3. When do command bar queries reach the search engine?** Same as
   the address bar / only after local results run out and typing pauses /
   never. **Recommended: only after local results run out and typing pauses.**
4. **01-D4. Build Peek, and does it enter history?** Yes, history only once
   expanded / yes, always in history / no. **Recommended: yes, history only
   once expanded.**
5. **01-D5. Do links from other apps open in a little window?** Yes by
   default / opt-in / not built. **Recommended: yes by default, in the
   last-used space, keeping nothing when closed.**
6. **01-D6. Which keys do the new actions take?** Arc's keys, with Cmd+O
   only inside Peek and the little window / new keys that clash with
   nothing. **Recommended: Arc's keys, scoped that way.**
7. **01-D7. How does clean-up work?** Manual Clear only / Clear now, opt-in
   auto-archive later (off by default, keeps an Arc user's own setting) /
   auto-archive on. **Recommended: Clear now, opt-in auto-archive later.**
8. **01-D8. Does Ask move from the AI new tab page into the command bar?**
   Yes, retire the AI new tab page / keep both. **Recommended: yes.**

## Where we are today

All facts come from code reading. Nobody has launched today's build for this
research, so no screenshot or video of it exists (FACT,
`plans/research/matrices/ui-and-feel.md`, Unknowns).

**Window and sidebar.** Chromium Views draws all chrome: 67 rac files,
16,108 lines (FACT, `plans/research/digests/rac-baseline.md`). The address
bar defaults to a 40 px top bar (`patches/rac/look/top-bar-default.patch`);
an Appearance setting moves it into the sidebar. The sidebar can sit on the
right (`patches/rac/look/right-sidebar.patch`). It is full or hidden, plus
edge reveal (`docs/internals/glossary.md`). Top to bottom: favorites
(Chromium's pinned tabs underneath), the space header, pinned tabs with
folders one level deep, open tabs and a New tab row, the space dots
(`docs/internals/pinned-tabs.md`).

**Spaces.** Switching, dots, saving, unloading after 15 minutes, an editor,
and 8 themes are built (`patches/rac/spaces/`). The swipe is rac's best
motion (FACT, `plans/research/digests/motion-and-feel.md`). All spaces share
one cookie jar (FACT, `plans/research/matrices/features.md`).

**Other surfaces.** Site control center (Views), auto PiP, Helium's
two-pane split view, and WebUI settings pages (`patches/rac/settings/`).
Onboarding is a WebUI window with 7 steps (`patches/rac/onboarding/`).
Ctrl+Tab uses most-recently-used order (FACT,
`patches/rac/settings/behavior-mru-cycling-default-on.patch`). Whether a
visible switcher exists is unconfirmed.

**AI surfaces.** The assistant is one WebUI page, `chrome://rac-ai`. It shows
in the right panel, and as the new tab page when AI is on
(`patches/rac/ai/06-new-tab-page-and-entry-points.patch`). The find bar Ask,
link summary card, and agent ring and pill are Views. With AI off, none of
them exist (`docs/internals/ai.md`).

**Missing for Arc users.** Command bar, Arc import that keeps spaces, Peek,
little window, Clear, separate sign-ins, Boosts, sync (features matrix).

**Rough edges** (ui-and-feel matrix, Matrix B):

- Cmd+S show "appears to snap" (INFERENCE from code, never run).
- Edge reveal recomputes the page layout on every frame of its slide (FACT,
  code). A Helium user saw dropped frames there (CLAIM, helium#1887).
- The AI panel opens in 350 ms on a slow-start curve. Plan 02 owns that fix
  (02, S10). The duration default it changes applies to every Chromium side
  panel, not only the AI one.

**Upkeep.** The `look` group carries 161 upstream hunks for 792 lines of new
code (FACT, rac-baseline digest). At Helium 0.20.1.1 all 5 `sidebar-reveal`
patches fail, because Helium rebuilt frameless mode (FACT,
`plans/research/digests/helium.md`). Plan 06 ports them during its sync.

**Installed web apps.** Nobody has checked whether rac's look and sidebar
patches break installed web app (PWA) windows (ruling 17).

## What others do

Full comparisons are in `plans/research/matrices/features.md` and
`ui-and-feel.md`. Points that shape this plan:

- **Command bar.** Arc, Dia, Zen, Cra, Ardia, Aside, and Yab ship one. Zen
  keeps about 40 actions in one declarative table (zen digest). Ardia offers
  Arc's Cmd+L and "new tab opens the bar" as opt-ins (FACT,
  `plans/research/ardia.md:62`).
- **Peek.** Ardia's Peek is a small window over the page, kept out of Recently
  Closed by a Chromium patch, and it becomes a tab without reloading (FACT,
  `plans/research/ardia.md:71,202`). Zen once loaded peeked pages with system
  privileges (zen digest, GHSA-vpvg).
- **Little window and clean-up.** Arc sends links from other apps to Little
  Arc, and Cmd+O moves them to the main window. It auto-archives after 12
  hours and has Clear with Undo (closed-ai-browsers digest). Only 5.52% of
  Arc's daily users used several spaces. That argues for habits that need no
  setup, not for any one feature.
- **Toolkits.** Ardia's React Native shell made tab switching 40 ms against
  Helium's 8.5 ms, later cut to 10 to 16 ms (ardia digest). Mori rewrote its
  shell three times, then settled on Views (`plans/research/long-tail.md:76`).

## Options

### The shape of the work

**Option A: features first, thinning after the sync.** New surfaces go in
rac-owned files on today's shell. Hooks into hot upstream files land after
plan 06's sync. Plan 03 (M4) and plan 06 (I2) thin the old hunks afterwards.

- Pros: Arc users get the command bar before 12-22. rac-owned code can be
  written on Chromium 154 now and rebased.
- Cons: the old `look` and `settings` hunks stay heavy until January.
- Effort: about 38 to 55 agent-days before 12-22 (table below).
- Risk: medium. Locks in Views for at least a year.

**Option B: thinning first, then features.** Do plan 03's S1 restructure
before any new surface.

- Pros: every new feature lands on a cleaner base.
- Cons: 15 to 25 agent-days with nothing new for users. It misses the Arc
  window (plan 03, S1 effort).

**Option C: a new shell.** Three different bets, each with one honest line:

- *Web-page shell* (`kWebium`, off by default in rac's tree, FACT
  `chrome/common/chrome_features.cc:1966`): experimental upstream, with
  memory and startup cost (INFERENCE). Mori rejected it.
- *Native AppKit or SwiftUI shell* (Cra, Crest): every Chrome dialog must be
  re-hosted, and Crest needed 205 hunks plus 14,406 lines of overlay (FACT,
  long-tail digest).
- *Out-of-process shell* (Atlas's OWL design; the Atlas product shut down on
  2026-08-09): it took a funded team (INFERENCE, closed-ai-browsers digest).

**Recommendation: A.** Plan 03 has already ruled out C for now (03-D4).
Graft from B: each feature PR states its upstream hunk count against plan
03's metric, and no new hunks go into `look`.

### Building the command bar (settled as Views by ruling 3)

| Build | New upstream hunks (INFERENCE) | Risk |
|---|---|---|
| rac Views panel driving Chromium's `AutocompleteController`, with rac rows merged in rac code | about 8 to 12 | Medium: new text field, list, accessibility, keyboard code |
| WebUI panel | about 6 to 10 | A renderer per window and a slower first open, against "never slower" |
| Extend the address bar's own popup | fewest new files, but about 15 to 25 hunks in hot omnibox files | High: Chromium is moving that popup to WebUI (`kWebUIOmniboxPopup`, disabled in 154, FACT `chrome/browser/ui/omnibox/omnibox_next_features.cc:41`) |

### Notes on each decision

- **D1 Cmd+T.** Pro: Arc's front door, with no empty tabs. Con: VISION.md
  makes it a choice; one setting keeps that promise.
- **D2 Cmd+L and click.** A click that edits in place keeps paste-and-go,
  extension keywords, and inline autocomplete. Con: two behaviors to learn.
- **D3 suggestions.** rac turns search suggestions on by default (FACT,
  `patches/rac/settings/general-suggest-default.patch`). In the command bar
  most typing is meant to find a tab. Sending "slack" to the search engine
  for that is a new leak. Asking only after local rows run out and a 300 ms
  pause cuts it. Con: this deliberately differs from the address bar.
- **D4 Peek.** Pro: the Arc habit with no setup. Con: VISION.md lists it as
  "not planned", and it has the most risk (dialogs, popups). Recording
  history only once expanded matches "a preview is not a visit".
- **D5 little window.** Pro: Arc's default, and outside links stop landing
  in the wrong space. Con: needs rac as the default browser. Keeping nothing
  on close avoids storing links the user never chose to keep.
- **D6 keys.** Cmd+O is Chromium's Open File (FACT,
  `chrome/browser/ui/cocoa/main_menu_builder.mm:154`). Scoped to Peek and the
  little window, Open File still works everywhere else. Opt+Cmd+N is
  Helium's new split tab (FACT, `plans/research/helium.md:87`). Arc users
  expect it for the little window, so split moves (plan 07's shortcut table).
  Shift-click is Chromium's "open in new window"; Peek takes it, and the
  context menu keeps "Open link in new window".
- **D7 clean-up.** Manual Clear is safe and needs no VISION change.
  Auto-archive is VISION "not planned"; off by default, it costs nothing.
- **D8 Ask.** Pro: one front door, and less WebUI. Con: users who liked the
  AI new tab page lose it, unless D1's setting keeps it.

## Recommended plan

### Information architecture

```
Window (one per profile)
├─ Sidebar (left or right; full / hidden / edge-revealed)
│  ├─ Header: window controls, Chat (AI on), [address bar in sidebar layout]
│  ├─ Favorites (shared by every space in the profile)
│  ├─ Space header (name, icon, menu)
│  ├─ Pinned tabs and folders (this space; one level)
│  ├─ Divider with Clear (new)
│  ├─ Open tabs + New tab row (opens the command bar)
│  ├─ Agents section: one group per client, shown only while it
│  │  has tabs (05-D3)
│  └─ Footer: space dots, media controls (new), menu
├─ Top bar (top bar layout): address bar, site control center, Chat
├─ Page area: one card, or two in split view; agent ring and pill
└─ Right panel: assistant (AI on only)

Floating: command bar, Peek, site control center, menus, toasts,
link summary card, find bar. Separate windows: little window, PiP,
installed web apps, onboarding. Settings open in a tab.
```

Rules:

- **Favorites are profile-wide. Pinned and open tabs belong to one space.**
  rac's open tabs are Arc's Today tabs. Keep the glossary term.
- **Folders stay one level deep, in pinned tabs only.** Arc's nested folders
  are flattened on import (plan 04 owns the mapping).
- **Every way in has a way out.** Peek has Close and Expand. The little
  window has Cmd+O and Close. Clear has Undo.
- **With AI off, no AI button, row, or label appears anywhere,** including
  the command bar (ruling 16). Outside-agent surfaces follow their own
  switch (D12 in decisions.md). Settings shows "Outside agents: on" next to the AI switch
  whenever the door is on (ruling 15).
- **Incognito.** The command bar shows only that window's tabs and its own
  history, never the regular profile's. A Peek from an incognito page is
  incognito. The little window never opens incognito.
- **Tech rule.** Views for anything opened many times a day, that moves, or
  must appear within a frame. WebUI (Lit) for rich, text-heavy panels. No
  second toolkit.

### New and changed screens

| # | Screen | Tech | Milestone |
|---|---|---|---|
| 1 | Arc import step in onboarding (leads when Arc is found), progress, result: "what came over, what didn't" | WebUI | M1 |
| 2 | Same flow under Settings > Spaces and import | WebUI | M1 |
| 3 | Command bar: empty state, typing, from Cmd+L with URL selected | Views | M2 |
| 4 | Command bar Ask row and hand-off to the panel (AI on only) | Views + WebUI | M2 |
| 5 | Peek: open, loading, Expand, Split, Close | per M0 spike | M3 |
| 6 | Little window: page, origin, Open in space (Cmd+O), Close | per M0 spike | M3 |
| 7 | Open-in-space picker | Views | M3 |
| 8 | Divider with Clear, Undo toast | Views | M3 |
| 9 | Make rac the default browser (Helium's existing prompt, last onboarding step) | WebUI + system | M3 |
| 10 | Edge reveal and Cmd+S with new timings and motion | Views | M4 |
| 11 | Agents section: one group per client (shown only while it has tabs), owner label, Take over, Stop all (per 05-D3) | Views | M5 |
| 12 | Settings > Outside agents, with the status line by the AI switch | WebUI | M5 |
| 13 | Archive page: search, restore | WebUI | M6 |
| 14 | Media controls in the sidebar footer | Views | M6 |
| 15 | Separate sign-ins toggle in the space editor (04-D6) | Views | M6 |

### The command bar in detail

- **Engine.** A rac Views panel drives Chromium's `AutocompleteController`.
  Search, history, the default engine, and Helium's bangs then behave as in
  the address bar. rac rows are merged in rac code, so the autocomplete code
  gets no hunk.
- **Rows.** Actions come from plan 03's single action table, with plan 07's
  label and shortcut fields (ruling 2). Tabs come from every space,
  including unloaded ones. Pinned tabs and favorites are included.
- **Ranking, v1.** What you typed comes first when it is a URL. Then open
  tabs: this space first, then other spaces. An open tab beats the same URL
  from history. Then pinned tabs and favorites, then history. Actions show
  only when the query starts one of their labels. Search suggestions come
  last. Zen's learned per-action score is left out of v1, because it adds
  stored state. Revisit after use.
- **Empty state.** Recent tabs in this space plus a few actions. It sends no
  request of any kind.
- **Behavior.** Cmd+T opens it with no tab yet. Enter on a URL or search
  creates the tab. Enter on a tab switches to it. Esc leaves nothing behind.
- **Motion.** Plan 02's S18: it grows from the address field with
  `kEaseExpo` in 140 ms. With no field showing, it appears at once (S17).
- **Accessibility.** VoiceOver reads it as a list with the selected row
  announced. It works fully from the keyboard, and focus returns to the page
  on close.
- **Strings.** New strings go in `chrome/app/rac_strings.grdp`. Follow
  AGENTS.md's string-file steps (`dev_names.py unsub`, then
  `worktree.sh sync`).

### Clear and archive (owned here, ruling 4)

- **MayClear rule.** One rac predicate, `rac::cleanup::MayClear(tab)`, with
  a reason per spared tab. Clear never closes pinned tabs or favorites, or a
  tab that is playing media, in PiP, in split view, used by an agent, or
  has a download in progress. It also spares a page that registered
  `beforeunload`. Chromium keeps no general dirty-form flag, so "unsent form
  text" is not a rule. The list comes from plan 07's draft, which now points
  here.
- **Before launch.** Clear with Undo, backed by Chromium's recently-closed
  restore. That keeps at most 25 entries (FACT,
  `components/sessions/core/tab_restore_service_helper.h:70`). The M0 spike
  checks whether one Clear is recorded as one entry. If not, Clear keeps an
  in-memory list for as long as the Undo toast shows.
- **After launch.** A bounded archive store (Cra keeps 1,500, cra digest),
  searchable in the command bar, with a reason per entry. Then the opt-in
  auto-archive: "Never / 12 hours / 1 day / 1 week", default Never. Arc
  import carries `autoArchiveTimeThreshold` (cra digest). It checks only on
  space switch and window focus, so Never runs no timer.

### Peek and the little window

The M0 spike decides between two builds. One is an overlay inside the main
window, hosting a page view. The other is a real tab in a small rac-owned
popup window.

- Plan 02's S19 dims the page behind Peek to 25% black. A separate window
  cannot dim the main page by itself. The parent window would draw the dim.
- The spike must cover these cases:
  - permission prompts;
  - `window.open` and sign-in popups opened from Peek;
  - downloads;
  - an incognito opener;
  - a cold launch from another app with no window open;
  - which profile and space own the popup;
  - expanding with no reload and no lost form state;
  - leaving Peek out of session restore and Recently Closed.
- Peek and the little window are re-estimated after the spike.

### Sidebar behavior after the sync (ruling 6)

Plan 06 ports `sidebar-reveal` onto Helium 0.20's overlay. Plan 02 owns the
motion. This plan sets the times, and keeps each rac edit inside Helium's new
code to one constant:

| Behavior | rac today | Helium 0.20 | Keep |
|---|---|---|---|
| Dwell before reveal | 100 ms | 350 ms expand-on-hover delay | rac's 100 ms (one constant) |
| Hide grace after leaving the sidebar | 300 ms | 150 ms | Helium's 150 ms, plus Zen's forgiving overshoot zone in a rac file (200 px sideways, 100 px vertical; zen digest item 4) |
| Grace after the pointer leaves the window | 3 s | 3 s | Helium's |
| States | full or hidden | full, collapsed, hidden | full or hidden |

This overrides plan 02's S2 note to keep the 300 ms grace.

### Milestones

Weeks count from plan approval. Anchors: launch build hard stop 2026-12-15
(plan 06), Arc shutdown 2026-12-22. Plan 06 owns the calendar.

**Dependency for every worktree after the sync:** the main checkout's
`build/src` is rebuilt on Chromium 156 first. Then worktrees are cloned
from it again, so each one doesn't need a near-full build of its own.
AGENTS.md says to ask the maintainer before any build of tens of thousands
of steps. Plan 06 lists the rebuild time as unknown.

#### M0. Prove the tools, run the spikes (weeks 1 to 2; Chromium 154; dev and rac-owned files only)

- **Tasks.**
  - Extend the harness in `patches/rac/dev/`: capture a named secondary
    window (little window, onboarding, PiP, installed web app); set a space's
    theme and color mode; open a second profile window and an incognito
    window. Plan 02 M0 builds the frame log and the frames-to-video tool, in
    the same UI worktree, one after the other.
  - Use plan 02 M0's frame-timing method. Burst PNG capture is accurate only
    to about one 60 Hz frame (16 ms, INFERENCE). Write the tolerance down.
  - Record Cmd+S both ways and edge reveal. This confirms or retires the
    snap inference.
  - Check installed web app windows on today's build (ruling 17).
  - Peek and little window spike (2 to 3 days). Clear and Undo spike (half
    a day).
  - Start the command bar's rac-owned code (panel, rows, merge) on 154,
    with no hooks.
- **Acceptance.** A written result for each spike. Three recordings. A
  stated frame tolerance. A PWA finding, with fixes filed.
- **Not in M0.** The full screenshot matrix. It is taken once, on the
  synced build, shared with plan 06's sync checks.

#### M1. Launch-build UI (weeks 1 to 4; lands on 156 after the sync; launch gate)

- **Goal.** The Arc import screens are in plan 06's launch build.
- **Tasks.** Screens 1 and 2 with plan 04's importer, plus the PWA fixes
  from M0. The result screen names what didn't come over: declined
  passwords, flattened folders, live folders, Boosts, and other Arc
  profiles' sign-ins until 04-D6 ships.
- **Acceptance.** Plan 04's fixture Arc data gives the same space count,
  pinned tabs, favorites, and themes, with screenshots before and after.
  The AI-off check passes on every screen.
- **Patch surface.** Rac-owned onboarding and settings files; about 0 to 2
  upstream hunks.

#### M2. Command bar (rac code from week 1 on 154; hooks after the sync on 156; ships in the launch if merged by the start of W5, otherwise a W6 point release via Sparkle, before 12-22)

- **Tasks.** The panel, rows, ranking, and motion described above. Hooks:
  command ids, accelerators, the menu bar entry, `BUILD.gn`, and the anchor
  to the address field.
- **Acceptance.**
  - The time from Cmd+T to the first painted result is measured with M0's
    method. The gate is one frame after the first open. If the gate fails,
    the number is reported, not hidden.
  - The empty state and local-only queries make no network request (net-log
    check). Search suggestions follow D3.
  - With AI off, there is no Ask row and no AI label.
  - Incognito shows only incognito tabs and history.
- **Verification.** Shots in hidden-sidebar, right-side, sidebar-layout,
  and split-view windows, plus incognito. Videos of open, close, and Cmd+L.
  Unit tests for the ranking and the merge.
- **Patch surface.** About 8 to 12 upstream hunks.
- **Launch rule (D16).** It is not a launch gate. It ships in the launch
  build if its hooks are merged by the start of W5. Otherwise it
  ships in plan 06's one optional W6 point release, only if `update-smoke`
  passes.

#### M3. Peek, little window, Clear (after M0's spikes and the sync; 156; stretch for before 12-22)

- **Tasks.**
  - **Little window.** One hook in the macOS "open URLs" path
    (INFERENCE: `app_controller_mac.mm`). Plan 07's Air Traffic Control
    later plugs into this same router.
  - **Peek.** Shift-click opens a link in Peek. So does a link to another
    site from a pinned tab or favorite. Expand (Cmd+O) turns it into a tab
    with no reload. It loads with the opener as initiator, never with
    privileges, and always shows its origin. Nothing preloads on hover.
    Motion follows S19.
  - **Clear.** Clear with MayClear and Undo.
  - **Default browser.** The prompt goes in onboarding's last step, reusing
    Helium's flow (`helium-chromium/patches/helium/core/add-default-browser-reject-button.patch`).
- **Acceptance.**
  - A permission prompt in Peek and in the little window names the right
    origin.
  - Clear then Undo restores the same tabs in order.
  - Nothing is created before first use: no window, page, or timer.
- **Verification.** Videos of Peek open, expand, and close; a link
  sent through a new harness verb, `open-urls URL`, that calls the same
  `application:openURLs:` router inside the worktree process; Clear and Undo. Reduced-motion versions too.
- **Patch surface.** Re-estimated after the spike. About 12 to 20 upstream
  hunks today (INFERENCE).

#### M4. Sidebar times and forgiving reveal (after plan 06's port; 156)

- **Tasks.** Apply the table above. Add the overshoot zone in a rac file. Its
  mouse monitor exists only while the revealed sidebar shows. Plan 02's
  thread lands S1 and S2 on top.
- **Acceptance.** The layout is computed once per reveal, not on every frame
  (trace). Cmd+S show and hide both animate. Reduce Motion gives short
  fades. The rac hunks in Helium's new code are one constant each.

#### M5. Agents section in the sidebar (with plan 05's M2 write tier; 156)

- **Tasks.** Design the rows in week 2, so plan 05 can build to them: the
  one group per client in the Agents section, with the owner label, Take
  over, and Stop all. No space dot. Build them with plan 05's M2, after its
  rendering spike confirms 05-D3. Also
  build Settings > Outside agents and the status line next to the AI switch.
- **Acceptance.** A client's group shows only while it has tabs. It never
  takes focus. The ring and pill stay still, painted once. With both
  switches off, nothing is created and nothing shows.

#### M6. After launch (January onward)

The archive store and page; opt-in auto-archive; media controls; the
separate sign-ins toggle when plan 04 ships partitions; a Spaces settings
page; split view up to 3 or 4 panes only if users ask.

### Effort and capacity

| Milestone | Agent-days | Before 12-22? |
|---|---|---|
| M0 tools and spikes | 6 to 8 | yes |
| M1 import screens | 3 to 5 | yes, launch gate |
| M2 command bar | 10 to 14 | yes, in the launch or a W6 point release |
| M3 little window, Peek, Clear | 16 to 23 (re-estimate after the spike) | stretch |
| M4 sidebar times | 3 to 5 | stretch |
| M5 Agents section UI | 5 to 8, plus 2 to 3 for settings | with plan 05 |
| M6 | 12 to 18 | no |

- **Critical path.** Plan 06's sync, then the base rebuild, then the
  command bar hooks, then the launch build, or the W6 point release through Sparkle.
- **Capacity.** The base machine is a shared M1 Air with 16 GB of memory and
  101 GB free (plan 06). Assume one full build at a time. Assume at most two
  incremental worktree builds at once (INFERENCE). Plans 04, 05, and 06 need
  the same machine. So this plan runs two UI worktrees at once, not four.

### Screenshot and video rules

The harness writes rac's own window after the first paint
(`--rac-window-screenshot`), because `screencapture -l` is blank on macOS 26
(AGENTS.md). Its request verbs can click, type, press keys, swipe, and
burst-capture (`patches/rac/dev/window-screenshot-popups.patch`,
`window-screenshot-swipe.patch`).

- **Tier 0, every UI PR.** The changed surface in light and dark, with the
  sidebar full and hidden, in both address bar layouts, on one colored
  theme. Add incognito and AI-off shots where the surface appears, and
  normal and Reduce Motion videos when motion changed.
- **Tier 1, each milestone, on the synced build.** It covers all 8 themes,
  every sidebar state, the right side, and two profile windows and two
  spaces. It also covers incognito, split view, installed web apps, Peek,
  and the little window. It adds videos of Cmd+S, reveal, swipe, command
  bar, Peek, Clear, and the agent ring.
- A PNG counts only with real pixels. Plan 06 decides where goldens live.

## Fit with the non-negotiables

- **Private.** The command bar's empty state and local queries send nothing.
  Search suggestions are narrowed on purpose (D3). Peek never preloads. A
  closed little window keeps nothing (D5). No new endpoints.
- **Never slower than Helium.** Every new surface is built on first use. The
  command bar's one-frame open is a measured gate. The reveal stops
  recomputing layout on every frame. Plan 06's bench should add Cmd+T and
  Peek.
- **AI off costs nothing.** No AI button, row, or label anywhere, as an
  acceptance check (ruling 16). Outside-agent surfaces follow their own
  switch, which is off by default.
- **Cheap to update.** About 20 to 34 new upstream hunks across M1 to M3,
  each counted in its PR with plan 03's metric. M4 keeps rac edits in
  Helium's new code to single constants. No new `look` hunks.
- **Calm UI.** Nothing loops while idle. The ring stays still. Reduce Motion
  turns slides into short fades (plan 02).
- **GPL.** Zen (MPL-2.0) and Ardia (Apache-2.0) are used as design
  references. Any copied code keeps its notice and gets credit.
- **Bent, needing sign-off.** VISION.md lists Peek (D4) and auto-archiving
  (D7) as "not planned", and makes the command bar a choice, not the default
  (D1). `docs/roadmap.md` places the command bar (phase 5) and Little Arc
  ("Later") later than this plan does. Two address bar layouts and two
  sidebar sides double the screenshot work; they are kept for Arc users.

## Dependencies on other plans

- **02.** Motion tokens and specs: S1, S2, S10 (AI panel), S17, S18, S19.
  This plan's reveal times override S2's grace (see above).
- **03.** 03-D4 (Views). The single action table (ruling 2). Its "where each
  part lives" row should read "command bar: Views; rows are C++ from the
  action table" (ruling 3). The hunk metric (ruling 11).
- **04.** The Arc importer and fixtures, the profile mapping (04-D2), and
  separate sign-ins (04-D6). Plan 04's table should point to plan 01 for the archive
  (ruling 4).
- **05.** 05-D3 (Agents section), its rendering spike, and its M2 write tier.
  Also the outside-agent policy and the door's own switch (D12 in decisions.md).
- **06.** The sync, the sidebar-reveal port, the base rebuild, the launch
  gate and calendar, screenshot CI, and gating dev switches.
- **07.** The shortcut and label fields in the action table, and moving
  Helium's split shortcut (D6). Air Traffic Control on this plan's router.
  07-D2 defers to D7.

## Risks and unknowns

- **Nothing has been run.** M0 may find the Cmd+S snap isn't real, or that
  other things are worse.
- **Peek outside a normal tab** may break features that assume one:
  permission prompts, find, extensions. The M0 spike exists to find out.
- **Arc data may vanish after 12-22** (INFERENCE, closed-ai-browsers
  digest). The import screens are a launch gate for that reason.
- **One shared Mac.** If plan 06's base rebuild runs long, M2 misses the
  W6 point release. The fallback is to ship M2 in January and say so on the site.
- **Frame metrics.** Chromium's animation histograms may not record in a
  metrics-removed build (ui-and-feel matrix). M0 picks a method that works.

## Open questions

- Decide later: the little window's name ("Little rac" or "little window").
- Decide later: whether the top bar stays the default layout, given Arc's
  sidebar URL. For now Arc import copies the user's Arc choice.
- Decide later: whether pinned folders ever nest, or Arc's nesting stays
  flattened.
- Decide later: whether space dots show the space name on hover (Nook).
- Note on the critique: I kept D1's setting inside the same decision instead
  of splitting it, because both halves take one line to answer.
- Note on the critique: D3's 300 ms pause is my estimate, not a measured
  value. M2 tunes it.

## Draft thread brief

Thread brief: see `plans/threads/ui.md`.
