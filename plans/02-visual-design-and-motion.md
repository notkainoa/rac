# 02. Visual design system and motion

## In plain English

Today every part of rac picks its own sizes, corners, speeds, and curves. The space swipe already feels like
Arc. Other parts feel slow or rough. Buttons don't react when you press them, and the AI panel starts slowly.
Cmd+S may jump instead of slide when the sidebar comes back.

This plan gives rac one list of design values and one small motion system. Things that move use springs, which
start fast and settle smoothly. Things you do hundreds of times a day get little or no motion. Nothing loops
while you're idle. Under Reduce Motion, slides become short fades. Increase Contrast strengthens edges. Spaces
gain custom colors, so imported Arc spaces keep theirs in light and dark mode.

What ships first, before the launch build's hard stop on 2026-12-15: press states, calmer hovers, quieter AI
loops, and custom space colors. These touch only rac's own files. Faster AI panel and tab motion, and Cmd+S and
edge reveal on springs, need the Helium sync first. They make launch only if that sync lands by 2026-12-01.

Cost: about 30 to 45 agent-days over roughly six weeks after approval. Each change ships with video and a frame log.

## What you need to decide

1. **02-D1. How springy is Cmd+S?** Dia's spring (about 3.4 px of bounce on a 200 px sidebar) / calmer (1.2 px)
   / none. **Recommended: calmer. This is a compromise: Apple's rule favors none. Confirm with a side-by-side
   video.**
2. **02-D2. Glass or solid?** Solid, as today / blur behind the window by default. **Recommended: solid.**
3. **02-D3. Space themes.** Eight presets / presets plus custom colors / a full gradient editor.
   **Recommended: presets plus custom colors.**
4. **02-D4. Do buttons shrink when pressed?** Never, like Dia / favorites tiles only / every icon button.
   **Recommended: never.**
5. **02-D5. Do keyboard shortcuts animate?** Spatial changes only (Cmd+S, space switches) / never.
   **Recommended: spatial changes only.**
6. **02-D6. Page card corner on macOS 26.** Match the window corner (11 px) / Dia's 10 px.
   **Recommended: 11 px on macOS 26; keep 10 px on older macOS.**
7. **02-D7. Under Reduce Motion, does a swipe follow your fingers?** No, as today / yes, then a fade on release.
   **Recommended: yes. Apple's guidelines allow gesture tracking.**

The plan decides the rest: how springs are built, the 8 ms frame gate for page resizes, and dropping Arc's
noise texture on import. Edge-reveal dwell and grace times belong to plan 01.

## Where we are today

Nothing was run for this plan. The values below come from code (FACT unless tagged). The build tree lags `main`,
since it was built from 9b4d949 on 2026-10-22. Prefixes: `R:` this repo, `B:` `/Users/knewton/Dev/Github/rac/build/src`.

**Design tokens.**

- Color is the only real token system: 25 `kColorRac*` ids (`R:patches/rac/look/tokens.patch:70-115`). Many values
  and comments cite Dia's asset catalogs (`R:patches/rac/spaces/dia-colors.patch:95-160`).
- Radii, spacing, and type are scattered. `B:chrome/browser/ui/views/rac/` holds 116 numeric `constexpr` literals and
  17 `base::Milliseconds(...)` calls (FACT, grep).
- Shared geometry lives only in `B:.../views/rac/rac_look.h:23-33`: card inset 6, gap beside the sidebar 10.
- Radii in use: 12, 11, 10, 8, 6, and 4, plus dots at 3 and 3.5 (`plans/research/digests/rac-baseline.md:66`).
- Tab rows are 34 px (`B:chrome/browser/ui/layout_constants.cc:154-155`).
- Helium's window corner is 17 px on macOS 26 and 12 px earlier (`B:.../helium/frame_corner_radius_mac.mm:7-11`).
- The type is the system font. The assistant uses 15 px / 1.5.

**Materials.** This corrects the UI matrix, which says rac blurs whenever a space wash applies.

- rac paints each wash as an opaque base plus a gradient (`B:.../rac/spaces/space_tint_background.cc:181-245`).
- No rac patch creates an `NSVisualEffectView`.
- Helium's blur is gated three times:
  - its feature flag is off by default (`B:chrome/browser/ui/ui_features.cc:38`);
  - its pref defaults to false (`B:chrome/browser/ui/browser_ui_prefs.cc:140`);
  - its settings toggle is hidden unless the flag is on (`R:patches/rac/settings/appearance-page.patch:122,249`).
- The one WebUI blur was added and then removed (`R:patches/rac/ai/11-dia-chat-composer.patch:720`,
  `12-native-menus.patch:12-13`).
- So no shipped setup is translucent, and Reduce Transparency has nothing to act on today.
- Increase Contrast is real work. Nothing reads it, though `ColorProviderKey::contrast_mode` exists
  (`B:ui/color/color_provider_key.h:38,138`).

**Space themes.**

- `SpaceTheme` stores two arbitrary color stops (`color1`, `color2`) and a mode (`B:chrome/browser/rac/spaces/space.h:24-44`).
- There are eight presets named after Dia's BrandColors; Neutral is flat gray.
- `GetStops` looks up a dark pair only for presets. Any other colors paint unchanged in dark mode
  (`B:.../space.cc:85-95`). That is the real gap: custom colors work in storage but have no dark version, and
  there's no picker.
- The wash is not a layer. `SpaceTintBackground` is installed on several views, and each paints a full-window
  gradient. `GetActiveTabFill` and the assistant container read the theme too (`space_tint_background.cc:142-180`).

**Motion.** The full inventory is in `plans/research/motion-and-feel.md:231-267`.

- The best piece is the space pager. It runs a critically damped spring (response 0.25 s) on the compositor
  thread, with Arc's tracking (`R:patches/rac/spaces/sliding-pages.patch:242-262,303-529`). Its spring supports
  damping 1.0 only.
- The weak parts are the busiest:
  - Cmd+S show seems to snap (INFERENCE, never run).
  - Edge reveal re-lays out on every frame.
  - The AI panel takes 350 ms on a slow-start curve (`B:chrome/browser/ui/ui_features.cc:283-286`).
  - The tab list uses 200 ms quadratic in-out.
  - Buttons have no press state.
- Patches hold 22 CSS durations and 6 custom curves, and `--ease-out` has two definitions (FACT, grep).
- Eight `infinite` CSS animations run only while work is pending (FACT per the dossier). They tick at the full
  display rate.
- Reduce Motion is covered nearly everywhere. Two hover fades miss it, and two Chromium classes read it only when
  built.

**Verification tools.** The dev harness takes screenshots, captures bursts (`burst DIR N MS`), and fakes 120 Hz
swipes (`R:patches/rac/dev/window-screenshot-swipe.patch:46-80`). `--force-prefers-reduced-motion` works for native
UI (`B:ui/gfx/animation/animation.cc:146-159`). Missing: a frame log, a video tool (`ffmpeg` isn't installed), and
a forcing flag for Increase Contrast.

## What others do

Details are in `plans/research/matrices/ui-and-feel.md` and `plans/research/digests/motion-and-feel.md`.

- **Dia and Arc** (CLAIM: one developer's recordings, about ±1 frame):
  - Sidebar on one spring both ways (0.215 s, 0.79).
  - Edge peek in on (0.185 s, 0.77), out in about 150 ms.
  - New tab row instant while the rows below slide 140 ms. A closing row fades 100 ms in place.
  - Pressed fill, no scale.
  - Command bar grows from the URL field in about 130 ms.
- **Zen:** springs as CSS `linear()` curves; its blur respects `prefers-reduced-transparency`; grain themes.
- **Nook:** 38 literals leaked past its token file; it removed Liquid Glass as "not calm"; its agent glows loop
  forever.
- **Ardia:** tests traced points next to its springs. **T3 Code:** stepped loops that pause off screen.
  **Cra:** ignores Reduce Motion.
- **Stedding:** a recorded paint of the old space cut frame cost from 4.6 to 8.8 ms down to 0.7 ms (FACT, its docs).
- **Apple:** no bounce for taps without momentum; Reduce Motion means fades. **Emil Kowalski:** stay under 300
  ms, don't animate keyboard content swaps, never grow from scale 0 (`plans/research/motion-and-feel.md:176-229`).

## Options

### Motion engine: one recommended path

rac adds a small motion system made of new files:

- one token header and one CSS token file;
- one spring type with three runners: compositor layers, the UI thread, and CSS `linear()`;
- a Reduce Motion helper read at every start;
- a lint;
- a frame log.

Retunes that need no springs, like press states and timing changes, land first.

- **Pros:** springs keep their speed when interrupted; values are checked by a lint and by tests.
- **Cons:** more work up front.
- **Effort:** about 30 to 45 agent-days for all milestones.
- **Risk:** medium, mostly in M4.
- **Locks in:** rac owns its spring math.

Rejected alternatives:

- **Retune only.** Keep each mechanism and change its numbers. This is a strict subset of the path above.
- **Spring types inside `gfx::Tween`, driven through `BrowserAnimationController`.** This puts edits in a file
  that every Chromium release touches. The controller takes only fixed curves, so springs can't hand off a
  swipe's speed (INFERENCE, `motion-and-feel.md:316-321`). Revisit only if Chromium adds spring support.

### Materials

**Option M-A: Solid (recommended).** Keep the opaque wash. Add one guard: under Reduce Transparency, treat Helium's
blur as off. Add one test that the wash base stays opaque.

- Effort XS, under 1 day.

**Option M-B: Blur behind the window by default.** Use the public `NSVisualEffectView` under the tint, which is
closer to Dia.

- The window server must blend whatever sits behind the window, while Helium's own default is off. That risks
  "never slower than Helium".
- Helium warns of "UI clarity issues".
- Needs a full Reduce Transparency path and a measured budget.
- Effort M.

Liquid Glass is out. Nook removed it, and Apple says to use it "sparingly".

### Space themes

**Option T-A: Presets only.** Polish and contrast checks. S, 2 agent-days.

**Option T-B: Presets plus custom colors (recommended).** A picker in the edit-space bubble writes `color1` and
`color2` directly. It offers one color, or two for a gradient. The model doesn't change. `GetStops` gains a dark
pair for non-preset colors, derived at paint time in OKLCH, a color space where equal steps look equal. That
derivation also fixes dark mode for spaces imported from Arc. Plan 04's import keeps copying Arc's first two
gradient colors into `color1` and `color2` (plan 04, import step 156).

- S to M, 4 to 6 agent-days, all in rac-owned files.

**Option T-C: Full gradient editor.** Zen-style, with up to three colors, harmony modes, and grain. M to L. It adds
settings and contrast cases.

**Arc's noise texture:** dropped on import (plan decides). A full-window grain layer adds blending cost during
swipes and Cmd+S, which is exactly where "never slower" is judged (INFERENCE). Revisit only with a frame-log
measurement.

## Recommended plan

### Rules

1. **Frequency sets the budget.** Hundreds of times a day: 0 to 100 ms, color or opacity only. Tens a day: 120 to
   250 ms, springs for movement. Rare surfaces: up to 400 ms.
2. **Spatial changes move. Content swaps don't** (02-D5). Ctrl+Tab, Cmd+1 to 9, selection, and the command bar
   as the new tab page are instant.
3. **Springs move things. Fixed curves fade and recolor.** Movement exits use a fast, bounce-free spring.
4. **Interruptible.** Input always acts on the final layout. rac's springs retarget and keep their speed.
   Exception: Chromium's tab list manager retargets position only. That is accepted for 140 ms row slides.
5. **Compositor first.** Any per-frame page resize, including the AI panel's, must pass the frame gate below.
6. **Nothing repaints while idle.** Loops run only while work is visible and in progress. They step at no more
   than 15 updates a second and stop under Reduce Motion.
7. **Accessibility settings are read at every start and every paint, never cached.**
8. **No motion or look settings.**
9. **AI off means no AI buttons, rows, or labels anywhere** (alignment ruling 16). Motion code for AI surfaces
   isn't created.

### Tokens

Every value carries a status:

- `rec`: CLAIM, recorded from Arc or Dia;
- `code`: FACT;
- `calc`: INFERENCE, recomputed for this plan by simulating each spring (the critique re-ran these and they match);
- `proposal`: a choice nobody has measured.

**Changed** marks a departure from the research. **Nothing here has been measured on rac.**

**Durations and curves.** WebUI uses recorded curves exactly, since CSS takes any curve. Native code uses the
nearest `gfx::Tween`, so it needs no custom curve objects. Each departure is tagged.

| Token | Value | Native mapping | Status |
|---|---|---|---|
| `kInstant` | 0 ms | none | proposal |
| `kHoverRow` | 50 ms in and out | Chromium's glow hover | code |
| `kHoverControl` | 120 ms, `kEaseStandard` | `FAST_OUT_SLOW_IN_3` | proposal (matrix); replaces 120, 150, and 160 ms |
| `kPress` | fill at 0 ms; release fades back over `kHoverControl` | paint | Dia's fill `rec`; release proposal |
| `kFade` | 100 ms, (0, 0, 0.58, 1) | `EASE_OUT` (quadratic), 6.9% from the recorded curve | `rec` in WebUI; **changed** natively, `calc` |
| `kList` | 140 ms, (0.2, 0, 0.2, 1) | `FAST_OUT_SLOW_IN_2` | `rec` duration; curve within 4% of Dia's, `calc` |
| `kExit` | 150 ms, (0.65, 0, 0.35, 1), opacity exits only | `EASE_IN_OUT_2` (0.33, 0, 0.67, 1), 11% gentler | `rec` in WebUI; **changed** natively, `calc` |
| `kCard` | 200 ms, `kEaseStandard`, opacity plus a 4 px rise | `FAST_OUT_SLOW_IN_3` | proposal |
| `kPanelOpen` / `kPanelClose` | 250 / 200 ms, `kEaseStandard` | `FAST_OUT_SLOW_IN_3` | proposal |
| `kCommandBarGrow` | 130 ms, (0.16, 1, 0.3, 1) | rac curve element | `rec` duration; curve `calc` |
| `kReducedFade` | 150 ms, `kFade` curve, zero overshoot | as `kFade` | code (today's cross-fade) |
| `kLoopStep` | at most 15 updates a second | CSS `steps()` | proposal |
| `kTooltipDelay` | 500 ms for the first; later ones within 1.5 s appear at once | none | `code` (Ardia), plus a proposal |

**Springs**, written as (response in seconds, damping ratio). Timings are `calc`.

| Token | Spring | 90% at | Overshoot | Within 1% at | Used by | Status |
|---|---|---|---|---|---|---|
| `kSpringPage` | (0.25, 1.0) | 155 ms | 0 | 264 ms | space pager, wash, dots | code |
| `kSpringDock` | (0.2, 0.85) by default (02-D1) | 101 ms | 0.61% | 142 ms | Cmd+S; the AI panel later | proposal, **untested**; Dia's (0.215, 0.79) gives 101 ms, 1.72%, 220 ms |
| `kSpringMove` | (0.22, 1.0) | 136 ms | 0 | 233 ms | rows moving between sections | proposal (matrix) |
| `kSpringReveal` | (0.185, 0.77) | 84 ms | 2.2% | 192 ms | edge reveal in | `rec` (Arc); the recorder's note of 93% in 66 ms disagrees with this fit |
| `kSpringExit` | (0.16, 1.0) | 99 ms | 0 | 169 ms | edge reveal out; movement exits | proposal; **changed** from Arc's 150 ms curve so speed carries across a reversal |

Deferred until their features exist:

- `kSpringGrow` (0.22, 0.9) for peek (Ardia `code`);
- Dia's hover-card pair, (0.25, 0.75) to show and (0.2, 0.6) to hide.

**Names in other plans** map to these tokens. Plan 01's "dock spring" is `kSpringDock`, `motion.grow` is
`kSpringGrow`, and `motion.command-bar` is `kCommandBarGrow`. Its `rac_motion.css` is `rac_tokens.css`.

**Non-motion tokens.**

- **Color:** stays in the color mixer. Add pressed fills (Dia: white 31% dark, 70% light, `rec`) and
  high-contrast variants (see M2).
- **Radius:** 4, 6, 8, 10, 12, and pill (height / 2). The page card is concentric on macOS 26: 17 − 6 = 11
  (02-D6). On older macOS the formula gives 12 − 6 = 6, which looks too square, so it stays 10. Corners stay
  circular, because Views has no squircle and mixing shapes would show at the seams.
- **Spacing:** 2, 4, 6, 8, 10, 12, 16, 20, 24.
- **Type:** system font. 11 caption, 12 secondary and URL, 13 rows (Dia's 13 pt), 15 assistant, 17 titles.
  Weights 400, 500, and 600.

### Motion spec

"How": **L** = compositor layer, **U** = UI-thread layout, **C** = WebUI CSS.

| # | Interaction | Spec | Reduce Motion | How |
|---|---|---|---|---|
| S1 | Cmd+S, both ways | `kSpringDock`; the sidebar and the card's left edge move together | sidebar fades `kReducedFade`; page width changes once | L sidebar; page resize per frame only if it passes the gate, otherwise Chromium's move-and-clip "fast resize" (`B:ui/views/controls/native/native_view_host.h:98-104`) |
| S2 | Edge reveal (timings from plan 01) | in `kSpringReveal`, slide only; out `kSpringExit`; reversal keeps speed; laid out once at rest | fade in `kReducedFade`, out `kFade` | L |
| S3 | Space switch | keep the pager. The wash and the active dot follow the pager's progress; the tab-list header joins the page spring | 150 ms cross-fade; swipe tracking per 02-D7 | L; the wash structure comes from the M0 spike |
| S4 | Tab open | new row in place at once; rows below slide `kList` | instant | Chromium list manager with settable duration and curve; FLIP only if the trace misses |
| S5 | Tab close | selection moves at once; the row fades `kFade` in place while the rows below slide up over it; hover follows the final layout | instant | as S4 |
| S6 | Pin, unpin, favorite, folder move | `kSpringMove`, no bounce; divider `kList`; drag keeps today's glide; haptic tick on snap | instant | L; `NSHapticFeedbackManager` in a new `.mm` |
| S7 | Folder open and close | chevron and children `kList` | instant | L |
| S8 | Hover | rows `kHoverRow`; controls `kHoverControl`; row close button `kFade` | unchanged | paint or C |
| S9 | Press | pressed fill on mouse down at 0 ms; no scale (02-D4) | unchanged | paint |
| S10 | AI panel | `kPanelOpen` / `kPanelClose`; edge pull follows the pointer; no entrance replays | instant | U, behind the frame gate |
| S11 | Rare popovers (edit space, site controls) | opacity `kFade` plus scale 0.96 to 1 from the trigger's side, 120 ms `kEaseStandard`; close `kFade` | fade only | L or C. Source: Emil's origin-aware popovers, proposal. Not the link summary card, which appears on hover often and keeps its 120 ms fade |
| S12 | Confirm and plan cards | `kCard`, no scale or bounce, never auto-dismiss under the pointer | opacity only | C transitions |
| S13 | Row expand | `kList`; content fades in over the last 100 ms; long lists clip and translate instead of `grid-template-rows` | instant | C |
| S14 | Agent ring and pill | still ring; fade in `kCard`, out `kExit`; dims to 40% while the user holds the tab | instant | L, opacity |
| S15 | Waiting loops | spinner no faster than 1.88 s per turn (`rec`); orb and shimmer stepped to `kLoopStep`, paused when hidden | static | C |
| S16 | Toasts, split drop, progress line | keep Helium's | Helium's | none |
| S17 | Keyboard tab switch, selection, new-tab command bar | instant | instant | none |
| S18 | Command bar (Views, plan 01) | grows from the field `kCommandBarGrow`; content uncovered, not scaled; close `kFade` | `kFade` | L clip rect |
| S19 | Peek (if plan 01 builds it) | from the link's box, never below 0.9 scale; `kSpringGrow`; page dims 25%; close `kSpringExit` | `kReducedFade` | L |

Micro-interactions, optional and XS each: dots that follow the swipe, a haptic tick on snap, and a fading row close
button. Ideas that need sign-off: a 0.97 press scale on favorites tiles, and Dia's favicon-tinted selected tile.

### Performance budget

- **Idle frames (this plan):** one window, 10 static tabs, pointer still, 30 s. The browser compositor presents
  **0 frames**, with AI off and with AI on and the panel closed. An open, idle AI panel's renderer also presents 0.
- **Idle CPU, wakeups, startup:** plan 06's bench owns these: interleaved runs against Helium, medians, and a 5%
  gate. This plan adds no second bench.
- **Frame gate** for every animation, and for every per-frame page resize (S1, S10):
  - Measured with the M0 frame log and a heavy local page loaded (a 10,000-node `file://` page).
  - Pass: 99% of presented-frame intervals are at most 1.5 times the display interval, with at most 1 dropped
    frame per animation, at 120 Hz and at 60 Hz.
  - UI-thread step time is a secondary number.
  - S10 must also be no worse than Chromium's current 350 ms panel on the same page.
- **Measurement hygiene:**
  - Use a quiet machine, with rac's window unoccluded. Occluded windows throttle, and other agents compete for
    CPU.
  - Run at least 5 paired, interleaved repeats against the baseline, and compare medians.
- **Cost when off:** tokens are `constexpr`. Spring math runs only during an animation. There are no new startup
  observers or timers. Per-row layers exist only while animating.

### Milestones

Weeks count from plan approval. Hot files shared with Helium wait for plan 06's sync (its M2) and the base-tree
rebuild that follows. rac-owned files are built on Chromium 154 and rebased onto 156. The launch hard stop is
2026-12-15 (plan 06 M5). Anything not merged one week before it waits until after launch.

Upstream hunks are counted in plan 03's metric: net-diff hunks in upstream files.

**M0. Baseline, rig, and wash spike** (week 1; Chromium 154; 4 to 5 agent-days)

- Tasks:
  1. Dev patch `patches/rac/dev/frame-log.patch`. `--rac-frame-log=PATH` writes the time of each presented
     frame (`ui::CompositorObserver::OnDidPresentCompositorFrame`, `B:ui/compositor/compositor_observer.h:70`)
     and rac animation steps as JSON lines.
  2. `record DIR MS`, which captures every presented frame. Timing runs and capture runs stay separate.
  3. `--rac-force-increased-contrast`.
  4. `devutils/rac/frames_to_video.swift` (AVFoundation, no install).
  5. `devutils/rac/motion_trace.py`, which fits a spring or curve to a moving edge.
  6. Baseline videos of Cmd+S both ways, swipe, tab open and close, and the AI panel.
  7. A 1 to 2 day spike on S3. Can the wash become shared layers that cross-fade, including Neutral, without
     breaking `GetActiveTabFill` or the assistant container?
- Acceptance:
  - The videos answer whether Cmd+S show snaps.
  - The spike returns an approach and an estimate.
  - All new switches are compiled out of release builds through plan 06's GN arg.
- Patch surface: dev patches, and one hook next to the existing screenshot hook.

**M1. Token and spring foundation** (weeks 1 to 2; Chromium 154; 6 to 8 agent-days)

- Tasks:
  1. `chrome/browser/ui/views/rac/rac_tokens.h`.
  2. `motion/rac_spring.{h,cc}`: `rac::Spring` with closed forms below, at, and above a damping of 1, plus
     `ValueAt`, `VelocityAt`, and `SettleTime`.
  3. `motion/rac_motion.{h,cc}`:
     - compositor `SpringTransformElement` and `SpringOpacityElement`, generalized from the pager;
     - a `CurveElement`;
     - `rac::SpringAnimation`, a `gfx::Animation` subclass that retargets and keeps its speed.
       `GetCurrentValue` is virtual (`B:ui/gfx/animation/animation.h:58`), so `tween.h` stays untouched;
     - `rac::motion::ReducedMotion()`.
  4. `rac_tokens.css`, generated with `devutils/rac/tokens.py`, which also checks for drift. It is served to
     `rac_ai`, onboarding, and settings. Confirm the serving hook (INFERENCE: one resource-list hunk).
  5. Move the pager onto `rac::Spring` with no change in behavior.
  6. `motion_lint.py`. It flags duration, bezier, radius, inset, gap, and padding literals on added lines outside
     the token files, with a shrinking allowlist.
  7. Spring unit tests in an existing rac test target. Plan 06 makes CI compile them.
- Acceptance:
  - Spring timings match the table within 1 ms.
  - The pager's trace matches its baseline within 1 frame.
  - The lint runs clean on this milestone's own patches.
- Patch surface: new files, plus about 2 to 3 BUILD hunks. After plan 03's source overlay move (03-D8, 06-D12),
  `motion/` moves with `ui/views/rac/**`.

**M2. Visible polish in rac-owned files** (weeks 2 to 4; Chromium 154; 9 to 13 agent-days)

- Tasks:
  1. Press and hover (S8, S9). Pressed color ids, and fixes for buttons in at least four patches.
  2. Increase Contrast. High-contrast variants of hairlines, the selected-row border, tertiary text, and focus
     rings, out of about 25 color ids. 2 to 3 days.
  3. The Reduce Transparency guard and the opaque-base test (M-A). Under a day.
  4. WebUI: move literals onto `rac_tokens.css` (one `--ease-out`), step and gate the loops (S15), and retime
     S12 to S14.
  5. Migrate radii, spacing, and type on every surface this milestone touches. Apply 02-D6 to the card.
  6. Wash cross-fade (S3), as the spike defines it. 3 to 5 days.
- Acceptance, per PR:
  - Traces within 1 frame of their tokens.
  - Idle frames at 0.
  - Before-and-after videos in light and dark, in both address-bar layouts, with Reduce Motion and with Increase
    Contrast.
  - PWA windows checked (alignment ruling 17).
  - With AI off, no AI rows or buttons appear.
- Patch surface: rac-owned files, plus the existing color hooks.

**M3. Custom space colors, T-B** (weeks 2 to 3; Chromium 154; 4 to 6 agent-days)

- Tasks:
  1. A picker that writes `color1` and `color2`.
  2. The OKLCH dark pair in `GetStops`.
  3. A contrast floor of 4.5:1 for tab titles on the wash.
  4. A fixture of Arc `windowTheme` colors from plan 04.
- Acceptance: screenshots of 8 presets and 3 custom colors in light, dark, and Increase Contrast. Unit tests for
  the derivation and the contrast floor.
- Patch surface: rac-owned spaces files. No model change.

**M4. After the sync** (Chromium 156; starts when plan 06's sync and base rebuild land; 8 to 13 agent-days)

- Tasks:
  1. AI panel S10: two one-line hooks, in `ui_features.cc` (a file Helium also touches) and
     `side_panel_animations.cc`. Gated.
  2. Tab open and close S4 and S5: 1 to 2 hunks in `tab_collection_animating_layout_manager`.
  3. Cmd+S and edge reveal motion (S1, S2) on plan 06's port of sidebar-reveal onto Helium 0.20's overlay, with
     plan 01's dwell and grace times (alignment ruling 6). Includes the A/B video for 02-D1 and the S1 resize
     choice from the frame gate.
- Cutoff: if the sync hasn't landed by 2026-12-01, M4 ships after launch, and Cmd+S ships as it is (matching
  plan 01's rule). If M0 shows that show snaps, list it as a known issue in the launch notes.
- Acceptance: both directions trace to their tokens, pass the gate, and fade under Reduce Motion. A pointer
  reversal mid-slide is smooth.
- Patch surface: about 4 to 6 hunks, plus the motion hooks into plan 06's ported frameless code. This plan owns
  only the motion. Plan 01 should drop its Cmd+S and edge-reveal motion estimate (about 6 to 9 of its 13 to 19
  days).

**M5. Future surfaces** (inside each feature's own estimate): the command bar (S18), peek (S19), hover cards if
plan 01 wants them, and the AI panel moving onto `kSpringDock`.

**What Arc refugees see by 2026-12-22.**

- For certain: press states, calmer hovers, quieter assistant loops, contrast support, and custom space colors.
- If the sync lands by 12-01: the quick AI panel, Dia-style tab open and close, and Cmd+S and edge reveal on
  springs.

## Fit with the non-negotiables

- **Privacy:** frame logs are dev-only and compiled out of release. Nothing leaves the machine.
- **Never slower than Helium:** every per-frame resize passes the frame gate, and staying solid avoids blur cost.
  Plan 06's bench catches regressions. Watch the brief GPU memory of FLIP layers.
- **AI off costs nothing:** tokens and classes do nothing until an animation runs. AI motion lives in views that
  aren't created with AI off. With AI off, no AI buttons appear.
- **Cheap to update:** new files, plus about 6 to 10 upstream hunks. Hot-file hunks wait for the sync. There is no
  `tween.h` edit. M4 bends this rule most, which is why it rides on plan 06's port.
- **Calm UI:** no idle loops, no glass, no visible bounce on row moves, a still agent ring, and no settings.
- **GPL:** new code is GPL-3.0. Recorded timings are facts, and no artwork or shaders are copied (INFERENCE, not
  legal advice).

## Dependencies on other plans

- **01 ui-shell:** owns behavior (reveal dwell and grace, forgiving reveal), the layouts, and future surfaces. It
  uses these token names.
- **03 core-architecture:** owns the hunk metric and the source overlay move (03-D8), which moves `motion/`.
- **04 data-storage-import-sync:** copies Arc colors into `color1` and `color2`, and drops the noise texture.
  M3's dark pair makes imported spaces work in dark mode.
- **05 agents-and-ai:** cards, ring, and loops follow S12 to S15. Any agent marker obeys the rules here.
- **06 engineering-and-shipping:**
  - owns the sync, its calendar, and the port of sidebar-reveal;
  - owns the idle and startup bench;
  - owns release gating of dev switches;
  - owns CI for the spring tests and `tokens.py --check`.
- **07 power-features:** inherits the tokens.

## Risks and unknowns

- **Nothing was run.** M0 confirms "show snaps", opaque-by-default, and loop gating.
- **Arc and Dia numbers are CLAIM, and the sources disagree** (Arc peek 66 vs 85 ms). So decisions go by video.
- **The wash cross-fade may be bigger than estimated.** The M0 spike bounds it, and S3 can ship without it.
- **The sync date drives M4.** If it slips, the most-used motions miss launch.
- **The capture rig perturbs timing.** Shape runs and timing runs stay separate.
- **Display rates differ.** The MacBook Air runs at 60 Hz, so test at 60 and at 120 Hz.
- **Stepped CSS loops may still wake every frame** (INFERENCE). The frame log settles it.

## Open questions

1. **Q1.** The color values and comments cite Dia's asset catalogs. Keep them, or replace them before any public
   design-system doc?
2. **Q2.** Is rac's 300 DIP/s flick threshold harder than Dia's (5 pt/s, `rec`)? M0's traces answer it, so it is
   not a decision.
3. **Q3.** Do the critique's suggested cuts drop glass vs solid (02-D2) and the keyboard rule (02-D5)? Rejected:
   both are one-line taste calls that change what users see, so they stay.

## Draft thread brief

**DRAFT. Not to launch until the maintainer approves.**

> **Thread: rac visual design and motion (plan 02).** Model: Claude Opus. One worktree per milestone
> (`git worktree add -b feat/motion-<m> <path> main`, then `devutils/rac/worktree.sh setup`).
>
> Read: `AGENTS.md`, `VISION.md`, this plan as edited by the maintainer, `plans/research/digests/motion-and-feel.md`,
> and `plans/research/motion-and-feel.md` lines 437-583. Use plan 06 for the calendar.
>
> Goal: M0 to M3 on Chromium 154 in weeks 1 to 4. Then M4 after plan 06's sync and base rebuild, and only if they
> land by 2026-12-01 for launch. Nothing merges in the week before 2026-12-15.
>
> Rules:
> - Every value comes from `rac_tokens.h` or `rac_tokens.css`.
> - Upstream edits stay small hooks, and hot files wait for the sync.
> - Never edit `helium-chromium/` or Helium's patches.
> - Never use a real profile, and never take the foreground. Use `worktree.sh run` and synthesized input.
> - Force Reduce Motion and Increase Contrast with flags, never with system settings.
>
> Done, per changed interaction:
> - before-and-after videos at real time and 4x;
> - a `motion_trace.py` report within 1 frame of the token;
> - a frame log that passes the gate;
> - screenshots in light and dark, both address-bar layouts, sidebar full, hidden, and revealed, two windows,
>   incognito, and a PWA window;
> - Reduce Motion and Increase Contrast captures;
> - idle frames at 0 with AI off and on;
> - with AI off, no AI buttons.
>
> Run focused unit tests only. Open PRs only when asked, with videos attached via `gh --attach`. Stop before M4 if
> the sync hasn't landed, and before acting on any unanswered 02-D decision.
