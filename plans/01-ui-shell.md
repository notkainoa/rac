# 01. UI shell and information architecture

## In plain English

This plan decides what a rac window holds, where each feature lives, and what
gets built before Arc shuts down on 2026-12-22.

The window keeps its shape. The sidebar sits on the left, the page sits in a
card, and the assistant panel opens on the right. Four things get added for
Arc users, in this order: a command bar on Cmd+T, an Arc import that keeps
spaces, Peek link previews, and a little window for links from other apps.

Three rough edges get fixed. The sidebar snaps back on Cmd+S. Edge reveal
re-lays out the page on every frame. The AI panel opens slowly.

Built-in AI moves into the command bar instead of its own new tab page.
Agent work gets its own quiet section at the bottom of the sidebar.

Everything stays on Chromium's own toolkit, with web pages for rich panels.
There is no second toolkit and no new shell.

Every UI change ships with screenshots: light and dark, space themes, sidebar
states, several windows, incognito, and reduced motion.

Two items conflict with VISION.md: Peek and an optional auto-archive. Both
need your sign-off.

## What you need to decide

1. **01-D1. Which UI technology does rac use?** Options: native Views plus
   WebUI, chosen per surface; a web-page shell (Chromium's `kWebium`); a
   native AppKit or SwiftUI shell (Cra, Crest); an out-of-process shell
   (Atlas). **Recommended: Views for window chrome, WebUI (Lit) for rich
   panels, no new shell.**
2. **01-D2. What does Cmd+T open?** Options: the command bar over the page
   (Arc); a new tab page with a search box; a setting. **Recommended: the
   command bar by default, plus one setting that brings back the new tab
   page (VISION promises that choice).**
3. **01-D3. How is the command bar built?** Options: a rac Views panel on
   Chromium's autocomplete engine; a WebUI panel; an extended address bar
   popup. **Recommended: a rac Views panel on the autocomplete engine.**
4. **01-D4. Build Peek?** Options: now; after 0.1; never. **Recommended:
   build it right after the command bar and edit VISION.md.**
5. **01-D5. Do links from other apps open in a little window?** Options:
   yes, by default; opt-in; not built. **Recommended: yes, by default, with
   Cmd+O to move the page into a space.**
6. **01-D6. How do clean-up and archive work?** Options: manual Clear plus a
   searchable archive; auto-archive on; both with auto off. **Recommended:
   manual Clear and archive now; auto-archive later as one setting, off by
   default, copied from Arc's own value on import. Edit VISION.md.**
7. **01-D7. Keep both address bar layouts?** Options: both; sidebar only;
   top only. **Recommended: keep both, top bar stays the default, and Arc
   import copies the user's Arc choice.**
8. **01-D8. What happens to the AI new tab page?** Options: keep it; fold
   Ask into the command bar. **Recommended: fold Ask into the command bar
   and retire the AI new tab page.**
9. **01-D9. Where do agent tabs live?** Options: a hidden agent space
   (Nook); an "Agents" section in the sidebar (Aside); an off-screen window
   (Yab). **Recommended: an "Agents" section at the bottom of the sidebar,
   shown only while an agent has tabs.**
10. **01-D10. Separate sign-ins per space before 2026-12-22?** Options: yes;
    no. **Recommended: no. Design the toggle now and ship it after plan 04's
    spike proves the storage partition.**
11. **01-D11. How deep is the screenshot matrix?** Options: everything on
    every PR; tiered. **Recommended: tiered. A small set on each UI PR, the
    full set at each milestone.**
12. **01-D12. What must plan 06's early-December launch contain?**
    Options: everything listed here; a cut line. **Recommended: command bar,
    Arc import, and the AI panel fix. Peek, the little window, Clear, and the
    Cmd+S fix follow before 12-22 if they pass review.**

## Where we are today

All facts below come from code reading. Nobody has launched today's build
for this research, so no screenshot or video of it exists (FACT,
`plans/research/matrices/ui-and-feel.md`, Unknowns).

**The window.** Chromium Views draws all chrome: 67 rac files, 16,108 lines
in `ui/views/rac` (FACT, `plans/research/digests/rac-baseline.md`). The page
sits in a card with a 6 px inset and a 10 px gap beside the sidebar. The
address bar defaults to a 40 px top bar (`patches/rac/look/top-bar-default.patch`,
`Layout::kTopBar`). An Appearance setting moves it into the sidebar
(`patches/rac/sidebar-address-bar/`). The sidebar can sit on the right
(`patches/rac/look/right-sidebar.patch`).

**The sidebar.** It has two states, full and hidden, plus edge reveal. The
icons-only mode is off (`docs/internals/glossary.md`). From top to bottom:
favorites as 44 px tiles, at most 3 per row; the space header; pinned tabs
with folders one level deep; open tabs and a New tab row; the space dots
(`docs/internals/pinned-tabs.md`; `patches/rac/sidebar/`). Favorites are
Chromium's pinned tabs underneath. Pinned tabs are the first unpinned tabs
(`docs/internals/pinned-tabs.md`).

**Spaces.** Switching, dots, saving, unloading after 15 minutes, a space
editor, and 8 themes are built (`patches/rac/spaces/`, 26 patches). The swipe
runs on a real spring on the compositor. It is rac's best motion (FACT,
`plans/research/digests/motion-and-feel.md`). Spaces share one cookie jar
(FACT, `plans/research/matrices/features.md`).

**Other surfaces.** Site control center bubble (Views,
`patches/rac/sidebar-address-bar/site-controls.patch`). Auto PiP
(`patches/rac/pip/`). Helium's two-pane split view. Settings pages
Appearance, Behavior, General, About (WebUI, `patches/rac/settings/`).
Onboarding is a 940 by 620 WebUI window with 7 steps: welcome, address bar,
space color, import, assistant, Helium services, done
(`patches/rac/onboarding/04-window-first-and-polish.patch`).

**AI surfaces.** The assistant is one WebUI page, `chrome://rac-ai`, shown in
the right side panel and as the new tab page when AI is on
(`patches/rac/ai/06-new-tab-page-and-entry-points.patch`). Its `app.ts` is
2,822 lines. The find bar Ask pill, link summary card, edge pull handle, and
agent ring and pill are Views (`patches/rac/ai/17`, `19`, `13`;
`patches/rac/agent/10-indicators.patch`). With AI off, none of them exist
(`docs/internals/ai.md`).

**Missing for Arc users.** Command bar, Arc import that keeps spaces, Peek,
little window, Clear and archive, separate sign-ins per space, Boosts, sync
(FACT, `plans/research/matrices/features.md`, "Gaps that matter").

**Rough edges** (`plans/research/matrices/ui-and-feel.md`, Matrix B):

- Cmd+S hide slides out in 200 ms. Show "appears to snap" because the docked
  layout ignores the slide ratio (INFERENCE from code, never run).
- Edge reveal runs a full layout pass every frame while it slides (FACT,
  code). A Helium user saw dropped frames here (CLAIM, helium#1887).
- The AI panel opens in 350 ms with a slow start: 2% moved at 35 ms (FACT
  for the 350 ms default of `kSidePanelFlyoverDurationMs`; INFERENCE for the
  curve figures).
- About 22 different durations, no press state, and two hover fades that
  ignore Reduce Motion (FACT, motion digest).

**Upkeep.** The `look` group carries 161 upstream hunks for 792 lines of new
code. `settings` carries 91, `spaces` 127, `pinned` 95 (FACT, rac-baseline
digest). At Helium 0.20.1.1, all 5 `sidebar-reveal` patches fail, because
Helium rebuilt frameless mode around expand-on-hover (FACT,
`plans/research/digests/helium.md`).

## What others do

- **Command bar.** Arc, Dia, Zen, Cra, Ardia, Aside, and Yab ship one
  (`plans/research/matrices/features.md`). Zen keeps about 40 actions in one
  declarative table with a learned score per action (FACT,
  `plans/research/digests/zen.md`). Dia's grows out of the URL field in about
  130 ms, with no scrim (CLAIM, recorded by Ardia's owner, ui-and-feel matrix).
- **Peek.** Arc, Zen (Glance), Ardia, Nook, and Yab. Arc opens links from
  pinned tabs and favorites in Peek. Ardia's Peek is a real tab that is never
  saved or kept in Recently Closed (FACT, `plans/research/ardia.md` line 71).
  Zen once loaded peeked pages with system privileges, a security bug (FACT,
  zen digest, GHSA-vpvg).
- **Little window.** Arc, Ardia, Cra, Nook, and Yab. Arc makes it the default
  for links from other apps. Cmd+O moves it to the main window (FACT,
  `plans/research/digests/closed-ai-browsers.md`).
- **Clean-up.** Arc auto-archives unpinned tabs after 12 hours and spares
  media tabs. Arc has Clear with an Undo toast. Dia offers Cleanup once 10 or
  more tabs go stale (FACT, closed-ai-browsers digest).
- **Arc usage.** Only 5.52% of Arc's daily users used more than one space
  (FACT, CEO letter, closed-ai-browsers digest). Daily habits matter more
  than spaces.
- **UI toolkits.** Ardia's React Native shell made tab switching 40 ms
  against Helium's 8.5 ms (FACT, ardia digest). Dia moved from SwiftUI to
  AppKit for speed. Cra and Crest pay for Swift shells in private-API
  swizzles and re-hosted Chrome dialogs (cra and long-tail digests). Mori
  rewrote its shell three times, then settled on Views
  (`plans/research/long-tail.md` line 76).
- **Agent tabs.** ego(lite) gives each task a Space that never steals focus.
  Aside has an "Agent tabs" sidebar section. Nook hides an Agent space. Yab
  uses an off-screen window (FACT, `plans/research/matrices/agents.md`).
  Endless glows cost ego about 40% GPU for one idle agent Space (FACT, ego-lite digest).

## Options

### Option A: Arc parity on today's shell

Add the four missing Arc habits to the shell rac already has. Each new
surface goes in new rac-owned files with a small hook into Chromium. Work
that collides with the Helium sync waits for it. This is the ship-first
answer.

- **Details.** Command bar, Arc import screens, Peek, little window, and
  Clear land as new views under `chrome/browser/ui/views/rac/`. The AI panel
  fix is two one-line hooks. Cmd+S and edge reveal are rebuilt once, right
  after the sync, on Helium 0.20's frameless overlay.
- **Pros.** Fastest path to what Arc users miss first. Low rebase cost if
  every hook stays small. Reuses Chromium's dialogs, permission prompts, and
  security UI.
- **Cons.** Leaves today's heavy `look` and `settings` hunks in place for
  now. Views motion needs rac's own spring code for anything that moves.
- **Effort.** L. About 45 to 60 agent-days over M0 to M3 (one agent-day is
  one worktree's build-and-verify day).
- **Risk.** Medium. The command bar and Peek touch hot files
  (`browser_view.cc`, `browser_navigator.cc`).
- **Locks in.** Chromium Views as the shell for at least a year.

### Option B: Restructure first

Make the shell cheap to update before adding features. Move rac's sidebar
into one rac-owned view, cut upstream hunks, adopt Helium's new Layout
settings, then build the Arc features on top. This is the best-in-class
foundation answer.

- **Details.** Targets from the baseline: under 400 upstream hunks in total
  (from 869), under 150 in `ui/views` (from 320) (rac-baseline digest).
- **Pros.** Every later sync gets cheaper. Features land on a cleaner base.
- **Cons.** Two to four weeks with nothing new for users. Misses the Arc
  window almost entirely.
- **Effort.** XL. About 15 to 25 agent-days of restructuring before any
  feature work.
- **Risk.** High for the 12-22 date. Low technically.
- **Locks in.** The same toolkit as A, with a better seam.

### Option C: A new shell

Replace Chromium's window chrome with a different toolkit. That could be a
web-page shell (Chromium's `kWebium`, off by default in rac's tree, FACT
`chrome/common/chrome_features.cc:1966`), a native AppKit or SwiftUI shell
(Cra, Crest), or an out-of-process shell (Atlas OWL).

- **Pros.** CSS springs and fast rebuilds (web shell). A native shell could
  shrink Chromium edits to a thin seam (Cra: 11 hunks on top of CEF's 1,044).
- **Cons.** Every Chrome dialog must be re-hosted: permissions, extensions,
  sign-in, autofill, translate, PiP (FACT, long-tail digest, Crest). Custom
  shells reintroduce classic security bugs (Dia CVE-2025-15032 and
  CVE-2025-13132). A second toolkit cost Ardia tab-switch time and memory.
- **Effort.** XL plus. Several months. OWL and ADK each took a funded team
  (INFERENCE, closed-ai-browsers digest).
- **Risk.** Very high. Throws away 16,108 lines of working Views code.
- **Locks in.** A rewrite before the first release.

### Recommendation

**Option A, with B's guardrails grafted in, and C kept only as a measured
spike after 0.1.** The guardrails: each feature PR states its upstream hunk
count; new code goes in new files; no new work in `look`; sidebar motion
waits for the sync so it is done once. If the hunk targets from B are still
missed after the sync, run the one-week spike from
`plans/research/long-tail.md` (C6): Views against `kWebium` against a native
window, measured on files touched, dialogs rebuilt, tab-switch time, and
memory. Decide with numbers.

## Recommended plan

### Information architecture

Each profile opens in its own window, as today. Inside a window:

```
Window
├─ Sidebar (left or right; full / hidden / edge-revealed)
│  ├─ Header: window controls, Chat button, [address bar in sidebar layout]
│  ├─ Favorites grid (shared by every space in the profile)
│  ├─ Space header (name, icon, menu)
│  ├─ Pinned tabs and folders (this space; folders one level deep)
│  ├─ Divider with Clear (new)
│  ├─ Open tabs (this space) + New tab row (opens the command bar)
│  ├─ Agents section (new; only while an agent has tabs)
│  └─ Footer: space dots, media controls slot, archive and menu
├─ Top bar (top bar layout): address bar, site control center, Chat
├─ Page area: one card, or two in split view
│  └─ Agent ring and pill on the card the agent uses
└─ Right panel: assistant (AI on only)

Floating, over the window: command bar, Peek, site control center,
menus, toasts, link summary card, find bar (with Ask).
Separate windows: little window, PiP, onboarding, settings (a tab).
```

Rules that keep it calm and predictable:

- **Favorites are profile-wide. Pinned and open tabs belong to one space.**
  Rac's open tabs are Arc's Today tabs. Keep the glossary word "open tabs".
- **Folders stay one level deep, in pinned tabs only.** Open tabs get no
  folders or groups in 0.1. Nested Arc folders are flattened on import, and
  the result screen says so (plan 04 owns the mapping).
- **The command bar is the front door.** Cmd+T, Cmd+L, the New tab row, and
  the address bar click all open it (Cmd+L and the address bar pre-fill the
  current URL).
- **Every way in has a way out.** Peek has Close and Expand. The little
  window has Cmd+O and Close. Clear has Undo. Archive has Restore.
- **AI surfaces exist only with AI on.** The one exception is the Agents
  section for outside agents, which follows the outside-agent switch from
  plan 05, not the AI switch.

### UI technology per surface (01-D1, with plan 03)

Rule: **Views** for anything that opens many times a day, moves, or must
appear within a frame. **WebUI (Lit)** for rich, scrolling, text-heavy panels
opened a few times a day. Both already exist in rac. No React Native, no
SwiftUI, no CEF. WebUI pages share one `rac_motion.css` and one token sheet
(plan 02).

### Screens to design

"New" means it doesn't exist yet. M-numbers are the milestones below.

| # | Screen | Tech | Status | Milestone |
|---|---|---|---|---|
| 1 | Main window, top bar layout, sidebar full | Views | built | M0 baseline |
| 2 | Main window, sidebar address bar layout | Views | built | M0 |
| 3 | Sidebar hidden, top-edge toolbar reveal | Views | built | M3 rebuild |
| 4 | Edge-revealed floating sidebar | Views | built | M3 rebuild |
| 5 | Sidebar on the right | Views | built | M0 verify |
| 6 | Favorites grid: hover, press, drag snap | Views | built | M0 |
| 7 | Space header and space menu | Views | built | M0 |
| 8 | Pinned section with folders, reset to pinned page | Views | built | M0 |
| 9 | Open tabs and New tab row | Views | built | M1 (row opens command bar) |
| 10 | Divider with Clear, Undo toast | Views | new | M2 |
| 11 | Footer: space dots, media controls slot, archive entry | Views | partly built | M2 |
| 12 | Space editor (name, icon, theme, color mode) | Views | built | M0 |
| 13 | Separate sign-ins toggle in the space editor | Views | new | M5 (design in M1) |
| 14 | Command bar, empty state (recent tabs, actions) | Views | new | M1 |
| 15 | Command bar, typing: tabs in all spaces, history, search, bangs, actions, archive | Views | new | M1 |
| 16 | Command bar from Cmd+L, current URL selected | Views | new | M1 |
| 17 | Command bar Ask row (AI on), hand-off to the panel | Views + WebUI | new | M4 |
| 18 | Peek: open, loading, Expand, Split, Close | Views window + tab | new | M2 |
| 19 | Little window: page, origin, Open in space, Close | Views window + tab | new | M2 |
| 20 | Open in space picker (Cmd+O) | Views | new | M2 |
| 21 | Split view, two panes, drop targets | Helium Views | built | M3 restyle |
| 22 | Auto PiP window | Chromium | built | M0 verify |
| 23 | Address bar, quiet, host only, both layouts | Views | built | M0 |
| 24 | Site control center | Views | built | M0 |
| 25 | Archive page: search, restore, clear | WebUI | new | M2 |
| 26 | Settings: Appearance, Behavior, General, About | WebUI | built | M3 cleanup |
| 27 | Settings: Spaces and import | WebUI | new | M1 |
| 28 | Settings: Assistant; Agents (outside-agent door) | WebUI | partly built | M4 |
| 29 | Onboarding, 7 steps, Arc step first when Arc is found | WebUI window | built | M1 update |
| 30 | Arc import progress and result ("what came over, what didn't") | WebUI | new | M1 |
| 31 | Make rac the default browser (in onboarding's last step) | WebUI + system prompt | new | M2 |
| 32 | Assistant panel: thread, composer, model chips | WebUI | built | M1 timing |
| 33 | Plan and confirm cards, quiet step rows | WebUI | built | M4 polish |
| 34 | Agent ring and pill (Resume, Stop) | Views | built | M4 |
| 35 | Agents section: per-client group, Take over, Stop all | Views | new | M4 |
| 36 | Find bar Ask pill | Views | built | M0 |
| 37 | Link summary card | Views | built | M0 |
| 38 | Incognito window (no spaces items, no AI) | Views | built | M0 verify |

### Milestones

Dates assume today is 2026-10-27 and Arc closes in 56 days. Agent-days are
rough estimates (INFERENCE).

#### M0. See what we have (3 to 4 agent-days, start now)

- **Goal.** A real picture of today's build, and a harness that can prove
  every later change.
- **Tasks.**
  - Capture the Tier 1 matrix (below) of today's build in a worktree.
  - Record Cmd+S both ways, edge reveal, and the AI panel opening with the
    harness's `burst DIR N MS` verb (`patches/rac/dev/window-screenshot-swipe.patch:56`).
    This turns the "Cmd+S snaps" inference into a fact or retires it.
  - Extend the harness, in `patches/rac/dev/` only: capture a named
    secondary window (little window, onboarding, PiP); set a space's theme
    and color mode by request; open a second profile window and an
    incognito window by request; stitch burst frames into an MP4 locally.
- **Acceptance.** Every built screen in the table has a light and a dark PNG
  with real pixels. Three videos exist. The snap is confirmed or refuted.
- **Patch surface.** Dev patches only. Plan 06 decides whether these switches
  are gated out of release builds (`plans/research/digests/rac-baseline.md`, item 12).

#### M1. The front door (18 to 24 agent-days, target 2026-11-21)

Plan 06 syncs to Helium 0.20 from about 10-29 to 11-12 and freezes rac
merges meanwhile (06-D13). M1 is built during the freeze and lands after it,
on the synced base.

- **Goal.** An Arc user can import their spaces and press Cmd+T.
- **Tasks.**
  1. **Command bar** (10 to 14 agent-days). A rac-owned Views panel, built
     on first open.
     - It drives Chromium's `AutocompleteController`, so search, history,
       the default engine, and Helium's bangs behave as in the address bar.
     - rac providers run beside it and merge results in rac code: tabs in
       every space (including unloaded ones), pinned tabs, favorites,
       actions, and later the archive. No hunk in the autocomplete code.
     - Actions come from one declarative table (Zen's pattern, zen digest
       item 6): plan 03's action registry, which also generates MCP tools.
     - Cmd+T opens it with no tab yet. Enter on a URL or search creates
       the tab. Enter on a tab switches to it. Esc leaves nothing behind.
       Cmd+L opens it with the current URL selected. Ctrl+Tab stays the
       recent-tab cycle.
     - Motion is plan 02's `motion.command-bar`: it grows from the address
       field in 130 ms, with no entrance when there is no field.
  2. **Arc import screens** (3 to 4 agent-days; logic in plan 04). An
     onboarding step that leads when Arc is installed: "Bring your Arc
     spaces". A progress view and a result screen that lists what didn't come
     over (passwords if declined, nested folders flattened, live folders,
     Boosts). The same flow under Settings > Spaces and import.
  3. **AI panel timing** (half a day). Open 250 ms, close 200 ms,
     `FAST_OUT_SLOW_IN_3`, via the two one-line hooks
     (`side_panel_animations.cc`, `kSidePanelFlyoverDurationMs`; motion
     dossier M11).
  4. **Design only.** The separate sign-ins toggle and its explanation, so
     plan 04 can build to it.
- **Acceptance.**
  - Cmd+T to first result painted: under one frame after the first open
    (cache warm), measured with burst capture. First open under 100 ms.
  - Typing in the command bar sends nothing new over the network beyond
    what the address bar already sends (net-log check, plan 06's recorded run).
  - With AI off, the command bar shows no Ask row and loads no AI code.
  - Importing the fixture Arc data from plan 04 yields the same space count,
    pinned tabs, favorites, and themes; screenshots before and after.
- **Verification.** Tier 0 shots for each PR; a Tier 1 run at the end. Videos:
  Cmd+T open and close, Cmd+L, typing to a tab in another space. Unit tests
  for the action table and the result merge.
- **Patch surface.** About 8 to 12 new upstream hunks: command ids,
  accelerators, the menu bar entry, one `BUILD.gn` line, and a hook to
  anchor the panel to the address field.

#### M2. Arc's daily habits (19 to 27 agent-days, target 2026-12-12)

- **Goal.** Peek, the little window, and Clear behave the way Arc users'
  hands expect.
- **Tasks.**
  1. **Spike: one floating-window primitive** (2 agent-days). Peek and the
     little window are both a real tab in a small Chromium popup-type
     browser window, owned by rac. A real tab keeps Chromium's permission
     prompts, dialogs, find, extensions, and origin display working
     (INFERENCE; Ardia's Peek is also a real tab, ardia dossier line 71).
     The spike compares this with an overlay `WebView` inside the main
     window. Pick the one that keeps every Chrome dialog working.
  2. **Little window** (5 to 7 agent-days). Links from other apps open in it
     when rac is the default browser. A hook in the macOS "open URLs" path
     routes them (INFERENCE: `app_controller_mac.mm`). It shows the origin,
     "Open in space" (Cmd+O), and Close. Closing sends the page to the archive.
     Plan 07's Air Traffic Control later picks the space directly.
  3. **Peek** (8 to 12 agent-days). Shift-click opens a link in Peek, as in
     Arc, and so do links to another site from a pinned tab or favorite.
     Expand (Cmd+O) makes it a tab with no reload; Split and Close (Esc)
     also exist. It never enters the session or Recently Closed. It loads
     with the opener as initiator, never privileged (Zen GHSA-vpvg), and
     always shows its origin. Nothing preloads on hover. Motion is plan 02's
     `motion.grow`.
  4. **Clear and archive** (4 to 6 agent-days; storage in plan 04). Clear on
     the divider closes the space's open tabs, never pinned tabs or
     favorites, with an Undo toast (Helium's toasts). Closed tabs go to an
     archive searchable from the command bar and from an Archive page.
     Chromium's Recently Closed keeps only 25 entries (INFERENCE from
     Chromium's tab restore limit), so plan 04 provides a bounded archive
     store. Cra keeps 1,500 (FACT, cra digest).
  5. **Default browser prompt** in onboarding's last step, so the little
     window can matter.
- **Acceptance.**
  - Shift-click to the first Peek frame: under 100 ms. Expand keeps scroll
    position and form state.
  - A permission prompt (camera, notifications) inside Peek and the little
    window shows correctly and names the right origin.
  - Clear then Undo restores the same tabs in the same order.
  - Nothing new runs until first use: no window, no WebContents, no timers.
- **Verification.** Tier 0 per PR; Tier 1 at the end. Videos: Peek open,
  expand, close; little window from a link in Mail or Terminal (`open URL`);
  Clear and Undo. Reduced-motion versions of each.
- **Patch surface.** About 10 to 16 new upstream hunks: link-click routing,
  the external-URL hook, a session-restore and Recently Closed exclusion,
  and Shift-click handling.

#### M3. After the Helium sync (13 to 19 agent-days)

Starts the day plan 06's sync lands (expected about 11-12) and runs beside
M1 and M2, so it can finish before 12-22. If the sync slips past early
December, ship Cmd+S as it is rather than fix it twice.

- **Goal.** The sidebar's most-used motions feel right and cost nothing.
- **Tasks.**
  1. **Cmd+S both ways** on plan 02's dock spring. The sidebar layer moves on
     the compositor. The page either resizes per frame or uses Chromium's
     move-and-clip "fast resize", decided by measurement
     (`TimeOfLongestAnimationStep` at 8 ms or less at 120 Hz on a heavy
     page; motion dossier M1).
  2. **Edge reveal** rebuilt on Helium 0.20's frameless overlay. Lay out
     once, animate the layer transform, retarget with velocity. Keep rac's
     rules: full or hidden only, 100 ms dwell, 300 ms grace, top-edge
     toolbar reveal (helium digest item 3).
  3. **Forgiving reveal.** Keep the sidebar open while the pointer overshoots
     the window edge, within 200 px sideways and 100 px vertically. The
     mouse monitor exists only in that state (Zen's fix, zen digest item 4).
  4. **Settings cleanup.** Adopt Helium's new Layout section and hide what
     rac decides with one small hook (helium digest item 7). rac's own
     settings: address bar position, sidebar side, what Cmd+T opens, little
     window for outside links, and later auto-archive.
  5. **Split view restyle** to rac's card and radii. Two panes stay.
- **Acceptance.** No layout pass per frame during reveal (trace).
  Cmd+S show and hide both animate, with matching videos. Reduced motion
  turns both into short fades. `sidebar-reveal` and `settings` hunk counts
  drop compared with before the sync.
- **Patch surface.** Should shrink. The rebuilt reveal replaces rac edits to
  Helium's zen-mode code instead of adding to them.

#### M4. AI surfaces in their final places (17 to 25 agent-days, with plan 05)

- **Goal.** AI shows up where it helps and nowhere else.
- **Tasks.**
  1. **Ask in the command bar.** The local Search-or-Ask pick that the AI new
     tab page uses (`intent.ts`, `docs/internals/ai.md`) runs on each
     keystroke with no model call. Tab or the Ask row opens the reply in the
     assistant panel.
  2. **Retire the AI new tab page** once the Ask row ships. Blank tabs show
     Helium's quiet new tab page. If you keep the new tab page setting
     (01-D2), it shows the Ask box there too.
  3. **Agents section** (plan 05 owns behavior). One collapsible group per
     agent client, labelled with its name, in every space of the profile.
     Its tabs are muted and in the background, each with Take over and Stop,
     plus Stop all in the header. It exists only while an agent has tabs.
     The ring and pill stay still, painted once (motion dossier M12).
  4. **Settings > Agents** for the outside-agent door: switch, connect
     line, connected agents with Revoke (plan 05).
- **Acceptance.** With AI off and the outside-agent switch off, a fresh
  profile creates no AI objects and shows no AI surface (repeat the
  `MasterSwitchGatesEntryPoints` check plus screenshots). Idle CPU with an
  agent section visible is the same as without (plan 06's bench).

#### M5. Best in class (the following 12 months, any order)

- Auto-archive as one setting, off by default, set from Arc's
  `autoArchiveTimeThreshold` on import (Cra reads that key, cra digest).
  Media tabs never archive.
- Separate sign-ins per space: the editor toggle from M1, after plan 04's
  partition spike. On for imported Arc spaces that had their own profile.
- Split view up to 3 or 4 panes, only if users ask.
- Media controls in the sidebar footer.
- Boosts editor and Air Traffic Control rules (plan 07 builds them; this plan
  places them in the site control center and Settings > Spaces).
- A one-week shell spike (Option C) if the hunk targets are still missed.

### Screenshot and video matrix

The harness writes rac's own window after the first paint
(`--rac-window-screenshot`), because `screencapture -l` is blank on macOS 26
(AGENTS.md). Its request file can click, move, type, press keys, swipe, and
burst-capture (`patches/rac/dev/window-screenshot-popups.patch:297-320`,
`window-screenshot-swipe.patch:56-73`). Reduced motion uses
`--force-prefers-reduced-motion`.

**Dimensions and codes.**

| Dimension | Values |
|---|---|
| Appearance | L light, D dark |
| Space theme | Neutral, Red, Orange, Yellow, Green, Blue, Pink, Purple |
| Sidebar | F full, H hidden, E edge-revealed, T toolbar revealed while hidden |
| Address bar | TB top bar, SB sidebar |
| Side | left, right |
| Windows | one window; two profile windows; two spaces; incognito; split view; little window; Peek open |
| Motion | normal, RM (Reduce Motion on) |
| AI | off, on |

**Tier 0: every UI PR (about 12 shots plus videos for motion).**

- The changed surface in L and D, times F and (H or E), times TB and SB, on
  Neutral: 8 shots.
- The same surface on Blue in L and D: 2 shots.
- One incognito shot if the surface appears there; one AI-off shot if it has
  any AI part.
- If motion changed: a normal and an RM video, plus a burst sequence.

**Tier 1: each milestone (about 80 shots and 16 videos).**

- Main window: 8 themes in L and D (16); F, H, E, T times TB and SB in L and
  D on Neutral (16); sidebar on the right (2).
- Windows: two profile windows, two spaces, incognito, split view, little
  window, Peek, each in L and D where it applies (about 10).
- Surfaces: command bar empty, typing, and Ask (6); site control center (2);
  every settings page (about 10); onboarding with the Arc step (about 18).
- Videos, normal and RM: Cmd+S both ways, edge reveal, space swipe, command
  bar, Peek, Clear and Undo, agent ring appear and Stop.

Rule: a PNG counts only with real pixels, not a blank or all-black frame
(AGENTS.md). Goldens are not committed to `main`; plan 06 decides where they live.

## Fit with the non-negotiables

- **Private.** No new network calls. The command bar uses the address bar's
  existing search suggestions. Note: rac turns suggestions on by default
  (`patches/rac/settings/general-suggest-default.patch`), so queries typed to
  find a tab also reach the search engine. See Open questions. Peek never
  preloads on hover. Favicons come from the local cache.
- **Never slower than Helium.** Every new surface is built on first use. The
  command bar needs no renderer, so it can paint in one frame. Peek and the
  little window create nothing until clicked. The edge-reveal rebuild
  removes a per-frame layout. Plan 06's bench must cover Cmd+T and Peek.
- **AI off costs nothing.** The Ask row, AI new tab page, assistant panel,
  and ring exist only with AI on. The Agents section follows the separate
  outside-agent switch, which is also off by default.
- **Cheap to update.** About 20 to 30 new upstream hunks across M1 and M2,
  each counted in its PR. M3 should remove more than it adds. No new `look`
  hunks.
- **Calm UI.** Nothing loops while idle. The ring stays still. Reduce Motion
  turns every slide into a fade of 150 ms or less. Frequent actions get
  0 to 100 ms of motion (plan 02).
- **GPL.** Zen's ideas (MPL-2.0) and Ardia's (Apache-2.0) are reused as
  designs, not code. Any copied code keeps its notice and gets credit.
- **Bent, needing sign-off.**
  - VISION.md lists Peek-style previews and auto-archiving as "not planned".
    This plan builds Peek and adds an opt-in auto-archive later.
  - VISION.md says the command bar can replace the new tab page as a choice.
    This plan makes it the default.
  - `docs/roadmap.md` puts the command bar in phase 5 and Little Arc in
    "Later". This plan moves both before 12-22.
  - Two address bar layouts plus left or right sides double the screenshot
    matrix and strain "opinionated" (rac-baseline digest). Kept on purpose for
    Arc users who had the sidebar URL.

## Dependencies on other plans

- **02 visual-design-and-motion.** Owns tokens, springs, the dock and reveal
  numbers, the command bar grow, the Peek grow, press and hover states, and
  theme visuals. This plan owns where things sit and in what order they ship.
- **03 core-architecture.** Agrees on staying with Views (03-D7 matches
  01-D1). Owns the action registry the command bar reads. Owns the spike on
  keeping a hidden agent tab rendering (agents matrix, Unknowns). To
  reconcile: plan 03's "where each part lives" table lists command bar
  results as WebUI. This plan recommends Views (01-D3) for one-frame opening.
- **04 data-storage-import-sync.** Owns Arc import logic and fixtures, the
  archive store, the per-space storage partition, and dated backups before
  any storage change.
- **05 agents-and-ai.** Owns agent tab behavior, ownership states, the
  outside-agent door, and card behavior. This plan places them.
- **06 engineering-and-shipping.** Owns the release date, the Helium sync
  (which gates M3), the perf bench, screenshot CI, and gating dev switches.
- **07 power-features.** Owns Boosts, Air Traffic Control, clean links
  (Arc's Supercopy), and media controls behavior.

## Risks and unknowns

- **Nothing has been run.** Every rough edge is from code. M0 may show the
  Cmd+S snap does not exist, or that other things are worse.
- **The sync gates sidebar work.** All 5 `sidebar-reveal` patches fail on
  Helium 0.20.1.1. Work on Cmd+S before the sync would be done twice.
- **Shortcut clashes.** Helium binds Cmd+Opt+N to a new split tab (FACT,
  `plans/research/helium.md` line 87). Arc used Opt+Cmd+N for Little Arc.
  Chromium uses Shift-click for "open in new window", which Peek takes over.
- **Peek or the little window outside a normal tab strip may break Chromium
  features** that assume a tab: permission bubbles, find, extensions. The M2
  spike exists to find out.
- **Chromium is moving the address bar popup to WebUI.** `kWebUIOmniboxPopup`
  exists, disabled, in rac's Chromium 154 tree (FACT,
  `chrome/browser/ui/omnibox/omnibox_next_features.cc:41`). The command bar
  must depend on `AutocompleteController`, not on the Views popup.
- **Arc data may vanish.** After 12-22, `StorableSidebar.json` may stay
  readable, or not (INFERENCE, closed-ai-browsers digest). Import must be in
  users' hands before then.
- **Tight timeline.** M1 plus M2 is about 37 to 51 agent-days in 46 days,
  with a 1 to 2 week merge freeze in the middle. That needs 3 to 4 parallel
  worktrees and fast review.
- **Frame metrics.** Whether `BrowserAnimationController` histograms record in
  a metrics-removed build is unknown (ui-and-feel matrix). Burst capture is
  the fallback.

## Open questions

1. What is the little window called? "Little rac", "little window", or
   something else.
2. Which shortcut opens a little window by hand: Arc's Opt+Cmd+N (moves
   Helium's split shortcut) or another key?
3. Should command bar queries reach the search engine's suggestions while
   they match an open tab? Options: same as the address bar; only after
   local results run out; never in the command bar.
4. Should Peek pages go into history? Arc-like says yes. Session restore and
   Recently Closed say no.
5. Which space does a little window belong to before Cmd+O? This matters
   once spaces have separate sign-ins.
6. Do outside agents' tabs show in every space, or only in the space that was
   open when the agent connected?
7. Should rac support nested pinned folders, or keep one level and flatten
   Arc's nesting for good?
8. Is the default address bar layout still the top bar, given that Arc's
   default put the URL in the sidebar?
9. Should the space switcher show the space name on hover (Nook), or stay
   dots only?

## Draft thread brief

> **DRAFT. Do not launch until the maintainer approves this plan and its
> decisions.**

**Thread: rac UI shell (plan 01).** Model: Claude Opus for design and
review; Sonnet for routine UI subagents.

**Goal.** Build plan 01's milestones M0 to M4 in order, in feature
worktrees, each PR with visual proof. Read `plans/01-ui-shell.md`, the
decisions as the maintainer edited them, `VISION.md`, `AGENTS.md`,
`docs/internals/glossary.md`, `docs/internals/pinned-tabs.md`,
`docs/internals/ai.md`, and plan 02's motion tokens.

**Constraints.**

- Follow AGENTS.md exactly, including "Ways to hurt yourself", worktrees,
  and patch rules. New code goes under `chrome/browser/ui/views/rac/` or
  `chrome/browser/ui/rac/`.
- Never take the foreground on the shared Mac. Use the
  `--rac-window-screenshot` harness for all captures.
- No new network calls. No idle loops. Read Reduce Motion at every
  animation start. AI off costs nothing.
- State the upstream hunk count in every PR. Add no hunks to `look`.
- Land nothing during plan 06's sync freeze. Start M3 only after the sync
  is merged and the base build is updated.

**Order.**

1. M0: capture today's Tier 1 matrix, record the three rough edges, extend
   the harness. Report findings before building.
2. M1: command bar, Arc import screens (with plan 04's thread), AI panel
   timing.
3. M2: floating-window spike, then the little window, Peek, Clear and archive.
4. M3 after the sync: Cmd+S, edge reveal, forgiving reveal, settings, split
   restyle.
5. M4 with plan 05's thread: Ask in the command bar, Agents section,
   Settings > Agents.

**Done means.** For each PR: Tier 0 shots embedded in the PR, videos for
motion, focused unit tests where logic exists, the "Cover every surface"
list from AGENTS.md answered item by item, and the "I tested" block for the
maintainer. For each milestone: a Tier 1 run and a short report of what
changed, what was measured, and what is still rough.

**Ask the maintainer before.** Changing VISION.md, changing a default,
adding a setting, taking a shortcut that Helium or Chromium already uses,
or any upstream hunk outside the counts in the plan.
