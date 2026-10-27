# 02. Visual design system and motion

## In plain English

Today every part of rac picks its own sizes, corners, speeds, and curves. The space swipe already feels like
Arc. Other things feel slower or rougher than they should. The AI panel starts slowly. Showing the sidebar with
Cmd+S may jump instead of slide. Buttons don't react when you press them.

This plan gives rac one short list of design values and one motion system. Every view and web page in rac reads
from it. Things that move use springs, so they start fast and settle smoothly. Things you do hundreds of times a
day, like switching tabs, get little or no motion. Buttons darken the instant you press them. Nothing loops while
you aren't doing anything. With macOS Reduce Motion on, slides become short fades. With Reduce Transparency on,
rac stays solid. With Increase Contrast on, edges get stronger.

Spaces keep their eight color themes. One custom color per space is added, so imported Arc spaces keep their
colors.

Each change ships with frame-by-frame video and a frame-timing log. The maintainer judges the feel by watching,
not by trusting numbers. Most of this is new files and a few small hooks, so Helium updates stay cheap.

## What you need to decide

1. **02-D1. How springy is Cmd+S?** Dia's exact spring (1 to 2 px bounce) / a calmer spring with the same speed
   (under 1.5 px) / no bounce. **Recommended: the calmer spring, confirmed by a side-by-side video.**
2. **02-D2. Does the page resize every frame during Cmd+S?** Every frame, like Arc and Dia / slide and clip, one
   resize at the end / pick after measuring. **Recommended: measure; ship every-frame only if each frame takes 8 ms
   or less.**
3. **02-D3. Glass or solid?** Stay solid, as today / blur behind the window by default / Liquid Glass.
   **Recommended: stay solid, and honor Reduce Transparency.**
4. **02-D4. Space themes.** Eight presets only / presets plus one custom color / a full gradient editor.
   **Recommended: presets plus one custom color.**
5. **02-D5. Do buttons shrink when pressed?** Never, like Dia / favorites tiles only / every icon button.
   **Recommended: favorites tiles only.**
6. **02-D6. Do keyboard shortcuts animate?** Only spatial changes like Cmd+S and space switches / never.
   **Recommended: spatial changes only.**
7. **02-D7. Where do springs live?** rac-owned classes, no Chromium edit / new spring types inside Chromium's
   `gfx::Tween` / Chromium's declarative animation controller. **Recommended: rac-owned classes.**
8. **02-D8. Page card corner on macOS 26.** Match the window corner (11 px) / keep Dia's 10 px.
   **Recommended: match the window corner.**

## Where we are today

Nothing here was run for this plan. Values come from code and patches (FACT unless tagged). The main checkout's
build tree lags `main` (commit 9b4d949, 2026-10-22), so `B:` facts can be stale. Prefixes as in
`plans/research/motion-and-feel.md`: `R:` this repo, `B:` `/Users/knewton/Dev/Github/rac/build/src`.

**Design tokens.**

- Color is the one real token system: 25 `kColorRac*` ids in `R:patches/rac/look/tokens.patch:70-115`, set in
  `rac_color_mixer.cc`. Many values come from Dia's asset catalogs, and the comments say so
  (`R:patches/rac/spaces/dia-colors.patch:95-160`).
- Radii, spacing, and type are scattered constants. The build tree's `chrome/browser/ui/views/rac/` holds 116
  numeric `constexpr` literals and 17 `base::Milliseconds(...)` calls (FACT, grep of `B:`). Shared geometry lives
  only in `B:chrome/browser/ui/views/rac/rac_look.h:23-33`: card inset 6, gap beside sidebar 10, row gaps 1.
- Radii in use: 12 popups, 11 find Ask pill, 10 URL pill and infobar cards, 8 tiles and controls, 6 menu rows, 4
  small buttons, dots 3 and 3.5 (`plans/research/digests/rac-baseline.md:66`). Tab rows are 34 px tall
  (`B:chrome/browser/ui/layout_constants.cc:154-155`). Off-scale spacing exists (title gap 7, divider 9).
- Type is the system font through Chromium typography. The assistant uses 15 px / 1.5, with 12 to 13 px controls
  (`plans/research/matrices/ui-and-feel.md`, Matrix A).

**Materials and transparency.** This corrects the UI matrix, which says rac uses Helium's behind-window blur
whenever a space wash applies.

- rac paints each space's wash as an opaque base plus a gradient on a textured layer
  (`B:chrome/browser/ui/views/rac/spaces/space_tint_background.cc:181-245`).
- Helium's blur (`NSVisualEffectView`) runs only behind the pref `helium.browser.native_frame_materials`. That pref
  defaults to false (`B:chrome/browser/ui/browser_ui_prefs.cc:140`), and its feature flag is off by default
  (`B:chrome/browser/ui/ui_features.cc:38`). Helium calls it experimental (`plans/research/digests/helium.md:164`).
- The one WebUI blur, on the composer, was added and then removed (`R:patches/rac/ai/11-dia-chat-composer.patch:720`,
  `R:patches/rac/ai/12-native-menus.patch:12-13`).
- So by default rac shows no translucency at all (INFERENCE from code; confirm in M0).
- Neither rac nor Helium reads Reduce Transparency or Increase Contrast. Both are available:
  `ui::NativeTheme::prefers_reduced_transparency()` (`B:ui/native_theme/native_theme.h:519`), the macOS provider
  (`B:ui/native_theme/os_settings_provider_mac.mm:122-131`), `ColorProviderKey::contrast_mode`
  (`B:ui/color/color_provider_key.h:38,138`), and the CSS media queries.

**Space themes.** There are eight presets named after Dia's BrandColors: Neutral (flat gray), Red, Orange, Yellow,
Green, Blue, Pink, Purple. Each has a light and a dark gradient pair, and each space has a color mode (Auto, Light,
Dark). Eight older Arc presets migrate to the nearest one (`R:patches/rac/spaces/dia-colors.patch:1-50`). There is
no custom color and no editor. The wash repaints when the space changes. It is not tied to the slide's progress
(INFERENCE, `plans/research/digests/motion-and-feel.md`).

**Motion.** Full inventory in `plans/research/motion-and-feel.md:231-267`.

- The best piece is the space pager. It runs a critically damped spring (response 0.25 s) on the compositor
  thread, with Arc's tracking and rubber band (`R:patches/rac/spaces/sliding-pages.patch:242-262,303-422,505-529`).
  Its `SpringCurve` and `SpringElement` handle only damping ratio 1.0.
- The weak parts are the busiest:
  - Cmd+S hide slides for 200 ms. Show seems to snap (INFERENCE from code, never run).
  - Edge reveal re-lays out the sidebar on every frame.
  - The AI panel runs 350 ms on a slow-start curve (`B:chrome/browser/ui/ui_features.cc:283-286`).
  - The tab list uses Chromium's 200 ms quadratic in-out.
  - No press state. Pressed paints like hovered.
- Patches hold 22 distinct CSS durations and 6 custom curves. `--ease-out` has two different definitions (FACT,
  grep of `R:patches/rac`).
- Reduce Motion is covered on every animated rac surface found. Exceptions: two hover fades, and two Chromium
  pieces that read it only when built.
- Eight `infinite` CSS animations exist in the assistant. All are said to run only while a reply or step is
  pending (FACT per the dossier; re-audit in M0). They tick at the full display rate, not stepped.

**Verification tools.** The dev harness takes screenshots, captures bursts (`burst DIR N MS`), and fakes 120 Hz
swipes (`R:patches/rac/dev/window-screenshot-swipe.patch:46-80`). `--force-prefers-reduced-motion` covers native UI
(`B:ui/gfx/animation/animation.cc:146-159`). `devutils/rac/test-spaces.mjs` is the pattern for real-browser tests.
Missing: a frame timer, a video tool (no `ffmpeg` on this Mac), and forcing flags for the other two settings.

## What others do

Details are in `plans/research/matrices/ui-and-feel.md` and `plans/research/digests/motion-and-feel.md`.

- **Dia and Arc** (CLAIM: one developer's recordings, via the dossier): sidebar on one spring both ways (0.215 s,
  0.79); edge peek in on (0.185 s, 0.77), out about 150 ms; new tab row instant while rows below slide 140 ms;
  closing row fades 100 ms in place; pressed fill, no scale. Dia reads Reduce Motion only.
- **Zen:** CSS `linear()` springs; blur skipped under `prefers-reduced-transparency`; grain and harmony themes.
- **Nook:** 38 literals leaked past its token file; Liquid Glass removed as "not calm"; agent glows loop forever.
- **Ardia:** Dia's numbers, private materials, traced points tested next to its springs. **Cra:** one 85 ms curve,
  no Reduce Motion. **T3 Code:** stepped loops paused off screen.
- **Stedding:** a recorded paint of the old space cut frame cost from 4.6 to 8.8 ms down to 0.7 ms (FACT, its own
  docs, via the matrix).
- **Principles:** Apple: no bounce for taps without momentum; Reduce Motion means fades. Emil Kowalski: under 300
  ms, no keyboard content-swap motion, never grow from scale 0 (`plans/research/motion-and-feel.md:176-229`).

## Options

The plan has three separate choices: how motion is built, how surfaces look, and how themes work.

### Motion engine

**Option A: Retune in place.** Keep each surface's current mechanism and change its numbers to a shared table.
Fix the AI panel, the tab list, and press states. Leave Cmd+S and edge reveal on Helium's layout slide.

- Pros: fastest, fewest new files.
- Cons: no springs outside the pager, no velocity hand-off, and the layout-per-frame slides stay. Cmd+S and edge
  reveal are the motions Arc users touch most.
- Effort S, 4 to 6 agent-days. Risk low.
- Locks in: Chromium's fixed curves for everything except the pager.

**Option B: A small rac motion system (recommended).** Add one token header, one spring type, and three ways to
run it: compositor layers, the UI thread, and CSS. Add one Reduce Motion and Reduce Transparency helper and a
verification rig. Then move each surface over in priority order.

- Pros: everything that moves can use a spring that keeps its speed when interrupted. Tokens are checked by a lint
  and by tests. It is all new files plus about 6 to 10 small upstream hunks across the milestones.
- Cons: more up-front work. Cmd+S and edge reveal must wait for the first Helium sync.
- Effort M to L, 25 to 35 agent-days in total. Risk medium, from the Helium frameless rework.
- Locks in: rac owns its spring math, and new motion code must use the tokens.

**Option C: Chromium's declarative controller everywhere.** Add spring types to `gfx::Tween` (two hunks in
`ui/gfx/animation/tween.{h,cc}`). Then drive all rac motion through `BrowserAnimationController`, which already runs
the side panel and vertical tab strip and logs frame histograms.

- Pros: one engine shared with Chromium's panels; histograms for free.
- Cons: fixed curves only, so interruptions lose speed (INFERENCE, `plans/research/motion-and-feel.md:316-321`).
  The API shifts between releases. It can't run the pager's gesture-speed hand-off.
- Effort L, 35 or more agent-days. Risk medium to high on rebases.
- Locks in: rac's motion depends on an internal Chromium API.

**Recommendation: B.** It is the only option that fixes the most-used motions properly and stays cheap to rebase.
Graft from A: ship the retunes (AI panel, tab list, press) first, before any spring work, so Arc refugees see the
gains before 2026-12-22. Graft from C: give rac's UI-thread animations their own frame-time log, so the 8 ms gate
works without Chromium's histograms.

### Materials

**Option M-A: Solid, as today (recommended).** Keep the opaque wash. Under Reduce Transparency, force Helium's
optional blur off and keep any future overlay solid.

- Pros: calmest and cheapest. It matches Arc, which used gradients and grain rather than blur (CLAIM, Matrix A).
- Effort XS to S, 1 to 2 agent-days. Locks in nothing.

**Option M-B: Blur behind the window by default.** Use the public `NSVisualEffectView` under the space tint, like
Dia but with public materials.

- Pros: closer to Dia. Cons: the window server blends whatever is behind the window, while Helium's default is
  off, so it risks "never slower than Helium". Helium warns of "UI clarity issues". Effort M. Risk medium.

**Option M-C: Liquid Glass on macOS 26 controls.** Rejected. Nook removed it as not calm. Apple says to use it
"sparingly", and it splits the look by OS version.

### Space themes

**Option T-A: Eight presets only.** Polish only: tie the wash to the slide, check contrast, add Increase Contrast.
S, 2 agent-days.

**Option T-B: Presets plus one custom color (recommended).** One color picker per space. rac derives the light and
dark gradient pair in OKLCH (a color space where equal steps look equal), the way T3 Code builds themes from a few
colors. Arc import (plan 04) maps each Arc `windowTheme` to the nearest preset, or to a custom color when nothing is
close.

- Effort S to M, 4 to 6 agent-days.
- Locks in one new field in the space model, so plan 03 and plan 04 must agree on it.

**Option T-C: A full gradient editor.** Zen-style: up to three colors, harmony modes, and a grain slider. M to L.
Rich, but it adds settings ("opinionated" says no), many contrast cases, and more to check.

**Recommendation: M-A and T-B.** Grain is a later option. A grain texture is painted once, so it costs nothing at
idle (INFERENCE). Add it only if the maintainer wants Arc's texture.

## Recommended plan

### The rules (apply to every milestone)

1. **Frequency sets the budget.** Hundreds of times a day: 0 to 100 ms, color or opacity only. Tens a day: 140 to
   250 ms, springs for movement. Rare surfaces like onboarding: up to 400 ms.
2. **Spatial changes move. Content swaps don't.** Cmd+S, edge reveal, and space switches animate, even from the
   keyboard (02-D6). Ctrl+Tab, Cmd+1 to 9, selection, and the command bar used as the new tab page are instant.
3. **Springs move things. Fixed curves fade and recolor.** Exits run faster than entrances.
4. **Always interruptible.** Input acts on the final layout at once. Springs retarget and keep their speed.
5. **Compositor first.** Animate layer transform and opacity. Resize the page per frame only after the 8 ms gate
   passes.
6. **Nothing repaints while idle.** Loops run only while work is visibly in progress and the window and tab are
   visible. They step at no more than 15 updates a second and stop under Reduce Motion.
7. **Accessibility settings are read at every animation start and every paint, never cached.**
8. **No motion or look settings.** macOS's Reduce Motion, Reduce Transparency, and Increase Contrast are the
   switches.

### Tokens: refined from the UI matrix

The matrix proposes 14 duration tokens, 5 curves, and 12 springs. This plan cuts that to a 6-step duration scale,
5 curves, and 3 springs now (2 more if hover cards are approved). Fewer values make leaks visible and keep the look
consistent. Every number has a status:

- `code`: FACT, read from code.
- `rec`: CLAIM, from Ardia's recordings of Arc and Dia.
- `calc`: INFERENCE, recomputed for this plan with a small script that simulates each spring. The results match
  the dossier's table within 1 ms.
- `proposal`: a choice nobody has measured.

**Nothing in this table has been measured on rac.** M0 and M2 measure it.

**Durations.** The scale is 0, 50, 100, 140, 200, and 250 ms, with 400 ms as the ceiling for rare surfaces.

| Token | Value | Changed from the matrix, and why | Status |
|---|---|---|---|
| `kInstant` | 0 | none | proposal |
| `kHoverRow` | 50, in and out | keep Chromium's tab hover | code |
| `kHoverControl` | 100, `kEaseStandard` | was 120. Snaps to the scale, and today's 120, 150, and 160 ms hovers become one value | proposal |
| `kPress` | fill at 0 ms; release fades back in 140 ms | matrix had a scale on every icon button (see 02-D5) | proposal; Dia's fill `rec` |
| `kFade` | 100, `kEaseFade` | none | `rec` |
| `kList` | 140, `kEaseList` | none | `rec` |
| `kExit` | 140, `kEaseExit` | was 150. One frame at 60 Hz is about 17 ms, so the two are near-identical (INFERENCE), and it keeps the scale short | proposal |
| `kCard` | 200, `kEaseStandard`; opacity plus a 4 px rise | none | proposal |
| `kPanelOpen` / `kPanelClose` | 250 / 200, `kEaseStandard` | none | proposal |
| `kReducedFade` | 140, `kEaseFade`, zero overshoot | was "at most 150" | proposal |
| `kLoopStep` | at most 15 updates a second | none | proposal |
| `kTooltipDelay` | 500 for the first; later ones within 1.5 s show at once | adds the 1.5 s window | `code` (Ardia) plus proposal |

**Curves.** All but one map to an existing `gfx::Tween`, so native code needs no custom curve objects.

| Token | Curve | Native mapping | Status and note |
|---|---|---|---|
| `kEaseStandard` | (0.2, 0, 0, 1) | `FAST_OUT_SLOW_IN_3` | code; Helium's reveal |
| `kEaseList` | (0.2, 0, 0.2, 1) | `FAST_OUT_SLOW_IN_2` | calc: within 4% of the Core Animation default Dia uses. Don't merge it with standard, which differs by 17% |
| `kEaseFade` | quadratic ease-out; CSS (0.25, 0.46, 0.45, 0.94) | `EASE_OUT` | calc: Dia's hover-card opacity curve is the usual bezier stand-in for this curve (2.5% apart). Replaces the matrix's (0, 0, 0.58, 1), which has no native form and is 6.9% away |
| `kEaseExit` | (0.33, 0, 0.67, 1) | `EASE_IN_OUT_2` | calc: 11% gentler than the ease-in-out cubic Ardia measured. Accepted so both sides match without a custom curve (proposal) |
| `kEaseExpo` | (0.16, 1, 0.3, 1) | none; rac curve element | calc: 59/83/93/97/99% on frames 1 to 5 at 60 fps against Dia's recorded 63/82/92/95/99. Command bar only |

**Springs.** Written as (response in seconds, damping ratio). Timing is `calc`. A ratio of 1.0 means no bounce.

| Token | Spring | 90% at | Overshoot | Within 1% at | Used by | Status |
|---|---|---|---|---|---|---|
| `kSpringPage` | (0.25, 1.0) | 155 ms | 0 | 264 ms | space pager, wash, dots | code (rac today; Arc's pager `rec`) |
| `kSpringSnappy` | (0.2, 0.85) | 101 ms | 0.61% (about 1.2 px of 190) | 142 ms | Cmd+S, rows moving between sections, peek grow, the side panel later | proposal (02-D1) |
| `kSpringReveal` | (0.185, 0.77) | 84 ms | 2.2% | 192 ms | edge reveal in | `rec` (Arc). The recorder's own 93%-in-66 ms note disagrees with this fit |

`kSpringSnappy` replaces three matrix springs: dock (0.215, 0.79), move (0.22, 1.0), and grow (0.22, 0.9). It
reaches 90% as fast as Dia's dock. Its overshoot is about a third as large, and it settles 78 ms sooner (calc). This
follows Apple's advice: no visible bounce for a key press, a little for gestures with momentum. Edge reveal is
driven by the pointer, so it keeps Arc's livelier spring. Dia's hover-card pair, (0.25, 0.75) to show and (0.2,
0.6) to hide, joins the table only if hover cards are approved.

**Design tokens (non-motion).**

- **Color:** stays in the color mixer, which already handles dark mode, contrast, and themes. Add pressed fills
  (Dia: white 31% dark, 70% light, `rec`) and high-contrast variants of hairlines, the selected-row border, and
  tertiary text.
- **Radius:** 4, 6, 8, 10, 12, plus "pill" (height / 2) in place of today's 11. The page card is concentric with
  the window: radius = window radius − inset, so 17 − 6 = 11 on macOS 26 (02-D8), and 10 on older macOS. Keep
  circular corners everywhere. Views has no squircle, so WebUI doesn't use one either. Mixing the two would show at
  the seams.
- **Spacing:** 2, 4, 6, 8, 10, 12, 16, 20, 24. Existing off-scale values (7, 9) get audited, not mass-changed.
- **Type:** system font. 11 caption, 12 secondary and URL, 13 rows and body (Dia's 13 pt), 15 assistant thread,
  17 titles. Weights 400, 500, and 600.

### Motion spec, one row per interaction

"RM" means Reduce Motion. "How" names the mechanism: **L** = compositor layer, **U** = UI-thread animation
(layout), **C** = WebUI CSS.

| # | Interaction | Spec | RM | How |
|---|---|---|---|---|
| S1 | Cmd+S and the sidebar button, both ways | `kSpringSnappy`. The sidebar and the card's left edge move together. The right edge stays put | sidebar fades `kReducedFade`; page width changes once | L for the sidebar; page per 02-D2 (U per frame, or slide and clip) |
| S2 | Edge reveal | keep the 100 ms dwell and 300 ms leave grace. In: `kSpringReveal`, slide only. Out: `kExit`. Retargets with speed when the pointer comes back. Lay out once at rest | fade in `kReducedFade`, out `kFade` | L |
| S3 | Space switch (swipe, dots, Ctrl+arrows, Ctrl+1 to 9) | keep the pager physics. The wash cross-fades on the same spring progress. The active dot's opacity follows that progress. The tab-list header joins the page spring instead of its own 180 ms | keep the 150 ms cross-fade (open question Q2) | L; two wash layers painted once |
| S4 | Tab open | new row in its slot at once, selected. Rows below slide `kList` | instant | L per-row transforms (FLIP); fallback is a settable duration and curve on Chromium's list manager |
| S5 | Tab close | selection moves at once. The row fades `kFade` in place while the rows below slide up over it. Hover follows the final layout at once | instant | L; the removed row's layer is kept for 100 ms and ignores input |
| S6 | Pin, unpin, favorite, folder move (menu or shortcut) | row moves on `kSpringSnappy`; the divider opens `kList`. Drag keeps today's snap glide. A trackpad haptic tick fires when a drag snaps into place | instant; haptic unchanged | L; `NSHapticFeedbackManager` in a new `.mm` |
| S7 | Folder open and close | chevron turns and children slide, `kList` | instant | L |
| S8 | Hover | rows `kHoverRow`; controls, tiles, chips `kHoverControl`; close button on a row fades `kFade` | unchanged (color) | U paint, or C |
| S9 | Press | pressed fill on mouse down at 0 ms; release `kPress`. Favorites tiles also scale to 0.97 in 100 ms and back in 140 ms (02-D5). Text rows never scale | fill only | U paint; tiles L |
| S10 | AI panel | open `kPanelOpen`, close `kPanelClose`; edge pull keeps following the pointer; the thread never replays entrance animations on open. Later `kSpringSnappy` | instant (Chromium) | U (Chromium side panel) |
| S11 | Popovers and bubbles (site controls, edit space, link summary) | opacity `kFade` plus scale 0.96 to 1 from the trigger's side, `kEaseStandard` 140 ms. Close `kFade`, no scale | fade only | L or C |
| S12 | Confirm and plan cards | `kCard`, no scale, no bounce; never auto-dismiss under the pointer | opacity only | C transitions, not keyframes |
| S13 | Row expand (agent steps, settings) | `kList` height; content fades in over the last 100 ms. Long lists clip plus transform instead of `grid-template-rows` | instant | C |
| S14 | Agent ring and pill | stays a still, once-painted ring. Fade in `kCard`, out `kExit`. Dims to 40% over `kList` while the user holds the tab | instant | L, opacity only |
| S15 | Loading and waiting loops | spinner no faster than 1.88 s per turn (Dia `rec`). Orb and shimmer stepped to `kLoopStep`, only while pending and visible, paused when hidden | static | C `steps()` plus a visibility gate |
| S16 | Toasts, split drop, progress line | keep Helium's | Helium's | unchanged, no edit |
| S17 | Keyboard tab switch, selection, new-tab command bar | instant | instant | none |
| S18 | Command bar from the URL field (when plan 01 builds it) | grows out of the field's box `kEaseExpo` 140 ms; content is uncovered, not scaled; close `kFade` | `kFade` fade | L clip-rect |
| S19 | Peek (only if plan 01 overturns VISION's "not planned") | grows from the link's box, never below 0.9 scale (Emil's rule, which beats the dossier's 0.12); `kSpringSnappy`; page behind dims to black 25%; close `kExit` | `kReducedFade` | L; contents render at final size |
| S20 | Onboarding | may keep its small overshoot curve (rare surface); move its literals onto tokens | its existing RM block | C |

Reduce Motion also turns off scale everywhere, and zero overshoot applies to every spring.

### Micro-interactions shortlist

Small touches that feel alive without looping, XS to S each: pressed fills everywhere (S9); dots that follow the
swipe (S3); a haptic tick on snap (S6); the row close button fading in on hover (S8); popovers growing from their
trigger (S11). Optional: Dia's favicon-tinted selected favorites tile, painted once (CLAIM, matrix item 11).

### Performance budget

Every target below is a proposal. M0 measures the Helium baseline first and may adjust the absolute numbers. The
comparisons with Helium stay fixed.

- **Idle frames.** One window, 10 static tabs, sidebar full, pointer still, for 30 s: the browser UI compositor
  presents **0 frames**. Run it with AI off, and with AI on and the panel closed. With the panel open and idle, its
  renderer also presents 0 frames.
- **Idle CPU and wakeups.** Browser plus GPU process CPU, averaged over 60 s, within **0.2 percentage points** of
  Helium in the same setup. Idle wakeups per second no more than **Helium + 10%**. Measure with macOS `top -stats
  pid,cpu,idlew` sampling, which needs no sudo.
- **Animation frames.**
  - Compositor-driven motion (L, C): 99% of frame intervals at most 1.5 times the display interval. At most 1
    dropped frame per animation, at 120 Hz and at 60 Hz.
  - UI-thread motion (U): longest step at most **8 ms** at 120 Hz on a heavy local page. Otherwise it falls back
    to the compositor version.
- **Feedback.** Hover and press fills appear on the first frame after the event.
- **Cost when off.** Tokens are `constexpr`. Spring math runs only while an animation runs. No new observers or
  timers at startup. Per-row layers exist only during an animation.
- **Never.** No `infinite` animation outside S15. No polling timer. No `backdrop-filter` without a
  `prefers-reduced-transparency` guard.

### Milestones

**M0. Baseline and rig** (3 to 4 agent-days, before the release)

- Goal: see and time today's rac before changing it.
- Tasks:
  1. Dev patch `patches/rac/dev/frame-log.patch`: `--rac-frame-log=PATH` writes each compositor presentation time
     (`ui::CompositorObserver::OnDidPresentCompositorFrame`, `B:ui/compositor/compositor_observer.h:70`) and rac
     animation step times as JSON lines. Without the flag it costs one switch check per window.
  2. `record DIR MS`: capture on every presented frame. Today's `burst` is timer-driven and drifts. Capture costs
     GPU time, so timing runs and capture runs stay separate (INFERENCE).
  3. `--rac-force-reduced-transparency` and `--rac-force-increased-contrast`, so agents never touch system settings.
  4. `devutils/rac/frames_to_video.swift` (AVFoundation, no install): real-time and 4x slow MP4s.
  5. `devutils/rac/motion_trace.py`: finds a moving edge per frame, fits a spring or curve, and reports 90% time,
     overshoot, and settle time.
  6. Baselines of Cmd+S both ways, edge reveal, swipe, tab open and close, and the AI panel; idle tests vs Helium.
  7. Audit the eight infinite CSS loops and today's translucency.
- Acceptance: the videos answer whether Cmd+S show snaps. There are idle numbers for rac and Helium. Every
  "unverified" item in "Where we are today" is confirmed or corrected.
- Patch surface: two new dev patches (new files plus one hook each next to the existing screenshot hooks) and new
  devutils files.

**M1. Token and spring foundation** (4 to 6 agent-days, before the release)

- Goal: one source for every value.
- Tasks:
  1. New `chrome/browser/ui/views/rac/rac_tokens.h` (radius, spacing, type, and duration `constexpr` values, plus
     curve names).
  2. New `chrome/browser/ui/views/rac/motion/rac_spring.{h,cc}`: `rac::Spring{response, damping_ratio}` with
     closed forms below, at, and above a ratio of 1, plus `ValueAt`, `VelocityAt`, and `SettleTime`. It keeps the
     pager's 240 Hz rest search.
  3. New `rac_motion.{h,cc}`:
     - compositor `SpringTransformElement` and `SpringOpacityElement`, generalized from the pager's pair;
     - a `CurveElement` for `kEaseExpo`;
     - `rac::SpringAnimation`, a `gfx::Animation` subclass whose `GetCurrentValue()` follows the spring and which
       can retarget and keep its speed. This is the UI-thread route with no `tween.h` edit, because
       `GetCurrentValue` is virtual (`B:ui/gfx/animation/animation.h:58`);
     - `rac::motion::ReducedMotion()` and `ReducedTransparency()`, read on every call.
  4. New `rac_tokens.css` with `--rac-dur-*`, `--rac-ease-*`, and `--rac-spring-*` as `linear()` strings. It is
     generated by `devutils/rac/tokens.py` from one table, which also checks the header and CSS for drift. The
     shared CSS file is served to `rac_ai`, onboarding, and settings. The exact serving hook gets confirmed in this
     milestone (INFERENCE: one resource-list hunk).
  5. Move the pager onto `rac::Spring`, with no change in behavior.
  6. Add a lint (`devutils/rac/motion_lint.py`, run by `he validate`-style checks and later CI) that flags
     duration and bezier literals on added lines of rac patches outside the token files. Existing literals go on
     an allowlist that shrinks over time.
  7. Add unit tests. `rac_spring_unittest.cc` asserts 90% time, overshoot, and settle time per token within 1 ms
     of the table. Pure math, so it runs fast.
- Acceptance: tests pass; the pager's before and after traces match within 1 frame; the lint runs clean on the
  milestone's own patches.
- Patch surface: new files plus BUILD.gn entries (about 2 to 3 hunks).

**M2. Quick wins** (6 to 9 agent-days, before the release; these land in this order)

- Goal: fix what users touch most without touching Helium's frameless code.
- Tasks:
  1. AI panel S10 (2 one-line hooks: the default in `ui_features.cc:283-286`, and the tween in
     `side_panel_animations.cc`).
  2. Press and hover S8 and S9, with pressed color ids in the mixer.
  3. Tab open and close S4 and S5. Start with the settable duration and curve (1 to 2 hunks in
     `tab_collection_animating_layout_manager`). Try FLIP only if the trace still misses Dia's shape.
  4. Space wash and dots on the pager progress, S3.
  5. Reduce Transparency and Increase Contrast: force Helium's material off under Reduce Transparency, add high-
     contrast color variants, and guard any WebUI blur.
  6. Step and visibility-gate the WebUI loops, S15.
  7. Move WebUI literals onto `rac_tokens.css`, which fixes the two `--ease-out` definitions.
  8. Re-time cards and rows, S12 to S14.
- Acceptance: each traced curve within 1 frame of its token; idle budget passes; before-and-after videos (real
  time and 4x) in light and dark, both address-bar layouts, plus the three accessibility captures, in each PR.
- Patch surface: about 4 to 6 small upstream hunks; everything else in rac files.

**M3. Space themes T-B** (4 to 6 agent-days; can run in parallel with M2)

- Tasks: add a custom color per space in the model, coordinated with plans 03 and 04; derive the gradient pair in
  OKLCH; add a picker in the edit-space bubble; add a contrast check that keeps tab titles at 4.5:1 or better on
  the wash; agree the Arc `windowTheme` mapping with plan 04.
- Acceptance: screenshots of all 8 presets plus 3 custom colors in light, dark, and Increase Contrast; a unit test
  covers the derivation and the contrast floor.
- Patch surface: rac-owned spaces files only.

**M4. Cmd+S and edge reveal on springs** (8 to 12 agent-days, after the first Helium sync in plan 03)

- Goal: S1 and S2.
- Why after the sync: all 5 sidebar-reveal patches fail on Helium 0.20.1.1, and Helium reworked frameless mode
  (`plans/research/matrices/ui-and-feel.md`, Unknowns).
- Tasks:
  1. Lay out the floating sidebar once and move its layer.
  2. Measure per-frame page resize against the 8 ms gate on a heavy local page (for example a 10,000-node
     file:// page) at 120 Hz.
  3. Pick 02-D2 from that measurement and implement it, using Chromium's fast resize as the fallback
     (`B:ui/views/controls/native/native_view_host.h:98-104`).
  4. Make a side-by-side video of Dia's exact spring and `kSpringSnappy` for 02-D1.
- Acceptance: both directions trace to their tokens; no frame over budget; RM fades work; the pointer returning
  mid-slide reverses smoothly.
- Patch surface: edits to Helium's frameless code in `browser_view.cc` and its layout. These are the highest-risk
  hunks in this plan, so keep them to hooks into new rac files.

**M5. Future surfaces** (included in their features' estimates)

- Command bar S18 and peek S19 when plan 01 builds them. Hover cards with Dia's choreography if approved. The
  side panel moves to `kSpringSnappy`.

**Totals.** About 25 to 37 agent-days. M0 to M3 fit before 2026-12-22 if they start now. M4 depends on when the
sync lands. Maintainer time: about 20 minutes of video review per PR.

## Fit with the non-negotiables

- **Privacy:** no data leaves the machine. Frame logs are dev-only files behind a flag. Nothing reports anything.
- **Never slower than Helium:** the budget compares with Helium directly and gates per-frame layout. Staying solid
  avoids the blur's cost. Watch the brief GPU memory of FLIP and press-scale layers.
- **AI off costs nothing:** constants and classes that do nothing until an animation starts. Agent and assistant
  motion lives in views not created with AI off (INFERENCE, `plans/research/motion-and-feel.md:610-611`).
- **Cheap to update:** new files plus about 6 to 10 small hunks. M4's Helium frameless hunks bend this most, so
  M4 waits for the sync. No `tween.h` edit (02-D7).
- **Calm UI:** no idle loops, no Liquid Glass, little or no visible bounce on key presses, a still agent ring, and
  no motion settings.
- **GPL:** all new code is GPL-3.0 rac files. Numbers measured from Arc and Dia are facts. No artwork, shaders, or
  strings are copied (INFERENCE, not legal advice). Open question Q1 covers the Dia-sourced palette.

## Dependencies on other plans

- **01 ui-shell:** owns which surfaces exist (command bar, peek, Little Arc, hover cards) and whether both
  address-bar layouts stay; each layout doubles motion checks. Its views use `rac_tokens.h` from M1 on.
- **03 core-architecture:** the first Helium sync lands before M4. It agrees the storage shape of M3's custom color.
- **04 data-storage-import-sync:** Arc import maps `windowTheme` to presets or custom colors (M3).
- **05 agents-and-ai:** S10 and S12 to S15 cover the panel, cards, ring, and loops. Any agent click marker follows
  this plan's rules (no loops, off under Reduce Motion).
- **06 engineering-and-shipping:** the perf bench reuses M0's tests. CI runs `rac_spring_unittest`,
  `tokens.py --check`, and `motion_lint.py`.
- **07 power-features:** new features inherit the tokens.

## Risks and unknowns

- **Nothing was run.** "Show snaps", opaque-by-default, and loop gating come from code. M0 confirms them.
- **Arc and Dia numbers are CLAIM** (one developer, about one frame of error), and the sources disagree (Arc peek
  66 vs 85 ms to 90%). So the plan decides by video, not by matching numbers.
- **The capture rig perturbs what it measures,** so shape runs and timing runs stay separate.
- **60 Hz vs 120 Hz.** The MacBook Air runs at 60 Hz. Test on both.
- **Helium's frameless rework** can reshape M4. Re-read the code after the sync.
- **Chromium's tab list manager** may change under the duration hook. Keep the hook to one or two lines.
- **Unverified:** whether macOS's blur view goes opaque by itself under Reduce Transparency (matters only if
  Helium's blur is on), and whether stepped CSS loops still request a frame every tick (INFERENCE; M0 settles it).

## Open questions

1. **Q1.** The color values and code comments cite Dia's asset catalogs (`BoostBrowser_TabUI`,
   `ARCClients_BaseAssets`). Keep them as they are, or let M3's derived palette become rac's own before any public
   design-system doc?
2. **Q2.** Under Reduce Motion, may a swipe follow the fingers 1:1 and then fade (Apple allows tracking), or stay
   untracked as today?
3. **Q3.** Edge reveal dwell: keep 100 ms, shorten it, or use a pointer-speed check? Zen's top complaints were
   about closing early, not opening late.
4. **Q4.** Flick threshold: rac turns a page at 300 DIP/s, and Dia's record says 5 pt/s. Is rac harder to flick?
   M0 can trace it.
5. **Q5.** Grain on space washes, Arc's texture: wanted?
6. **Q6.** Dia-style tab hover cards: wanted? This adds two springs and an M-size task.
7. **Q7.** May agents install `ffmpeg`, or should the plan stay on the AVFoundation script?

## Draft thread brief

**DRAFT. Not to launch until the maintainer approves.**

> **Thread: rac visual design and motion (plan 02).** Model: Claude Opus for design and motion work. Use worktrees
> per milestone (`git worktree add -b feat/motion-<m> <path> main`, then `devutils/rac/worktree.sh setup`).
>
> Read first: `AGENTS.md`, `VISION.md`, `plans/02-visual-design-and-motion.md` (as edited by the maintainer),
> `plans/research/digests/motion-and-feel.md`, `plans/research/matrices/ui-and-feel.md`, and the spec and
> architecture sections of `plans/research/motion-and-feel.md` (lines 437-583).
>
> Goal: deliver M0 to M3, then M4 after plan 03's Helium sync. Each milestone is its own PR with one problem per
> PR.
>
> Rules: every value comes from `rac_tokens.h` or `rac_tokens.css`; new code uses no literal durations or curves;
> keep upstream hunks to small hooks; never edit `helium-chromium/` or Helium's patch folders; never point a build
> at a real profile; never take the foreground. Launch with `devutils/rac/worktree.sh run`, the background flag,
> and the harness's synthesized input. Test Reduce Motion, Reduce Transparency, and Increase Contrast with the
> force flags, never by changing system settings.
>
> Done means, per changed interaction: real-time and 4x videos before and after; a `motion_trace.py` report
> within 1 frame of the token; a frame log meeting the budget; screenshots in light and dark, both address-bar
> layouts, sidebar full, hidden, and edge-revealed, two windows, incognito; the three accessibility captures; and
> the idle test with AI off and on.
>
> Run only focused unit tests. Open PRs only when the maintainer asks, with videos via `gh --attach`. Stop and ask
> before M4 if the sync hasn't landed, and before acting on any unanswered 02-D decision.
