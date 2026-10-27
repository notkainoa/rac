# Motion and feel — planning digest

Source: `plans/research/motion-and-feel.md` (2026-10-25, 814 lines; compares Arc, Dia, Zen, Nook, Ora, Ardia, T3 Code,
Chromium, Helium, rac; proposes a motion spec). **Not adversarially verified.** Tags: **FACT** = code or vendor docs,
**CLAIM** = self-report or recording-based, **INFERENCE** = reasoning. Spring timings ("90 % at 101 ms") are the
author's own arithmetic (INFERENCE). Prefixes: `R:` this repo, `B:` built tree
`/Users/knewton/Dev/Github/rac/build/src` (Chromium 154, older than `main`), `A:` Ardia. **[checked]** = I re-read
the source.

## In plain English

rac has no shared motion list: 22 different CSS durations and about a dozen curves. The space swipe is excellent
(real spring physics on the compositor, copied from Arc). The weakest parts are the most used: Cmd+S (hide slides,
show seems to snap), edge reveal (re-lays out every frame), and the AI panel (350 ms, slow start). The dossier
proposes one token table, one spring tool, and a rule per interaction. Frequent actions get little motion,
movement uses springs, nothing loops while idle, nothing blocks input, and Reduce Motion turns slides into short
fades.

## Key facts

### rac today (FACT from patches unless marked)

- **Space pages:** critically damped spring, omega 2π/0.25 s, on the compositor thread (custom
  `gfx::TransformAnimationCurve`) because `ui::LayerAnimator` takes only fixed curves that can't start at the swipe's
  speed. Drag 0.5x scroll; rubber band 0.15 over 255; flick 300 DIP/s after 4 DIP; rest when offset < 0.25 DIP and
  speed < 15 DIP/s, sampled 240 Hz, cap 1.5 s; release speed clamped so no visible overshoot. Only ζ = 1 supported.
  RM: swipe tracking off, 150 ms cross-fade. `R:patches/rac/spaces/sliding-pages.patch:242-262,303-339,341-344,505-529`.
  Tab list on space switch: opacity 0.35 to 1 + 24 px slide, 180 ms (0.4,0,0.2,1); RM 140 ms no slide. Swipe: axis lock
  15 DIP, switch at 75 DIP, reset 300 ms.
- **Edge reveal:** 100 ms dwell; Helium's 200 ms slide (0.2,0,0,1); leave grace 300 ms; expand-on-hover delay 100 ms;
  `RichAnimationDuration` read each reveal (RM 0 ms) (`sidebar-reveal/edge-reveal.patch:10,17-18,84-87,142-143,196`).
  Helium: trigger 6 px, leeway 8 px, 8 px padding, 3 s grace after pointer leaves window.
- **Cmd+S:** hide = page full width at once, floating sidebar slides out 200 ms (0.2,0,0,1), layout pass per frame.
  Show "appears to snap" (docked layout ignores slide ratio) — INFERENCE from code, **never run**.
- **Tab rows:** `TabCollectionAnimatingLayoutManager` 200 ms quadratic `EASE_IN_OUT`, new rows fade 0 to 1; RM read only at
  construction **[checked]**. Hover 50 ms. Drag snap glide 150 ms + 100 ms hand-off.
- **Press:** no distinct state; several rac buttons paint pressed like hovered. Chat button 150 ms hover, site tiles 120 ms.
- **AI side panel:** Chromium 350 ms (0.45,0,0.12,1) on width; shadow fades in from 150 ms (100 ms), out 100 ms; edge
  pull opens without slide **[checked: 350 ms is the default of `kSidePanelFlyoverDurationMs`, flyover off]**.
  2 % moved at 35 ms, 22 % at 88 ms (INFERENCE).
- Find "Ask" 120 ms linear; link summary 500 ms delay, 120 ms fade, 700 ms throb; new-tab Ask 160 ms; confirm cards
  240 ms (0.23,1,0.32,1); assistant loader 420 ms, orb (4 s, 2.8 s) and shimmer 2.4 s only while a reply is
  pending; step spinner 0.8 s only while a step runs; onboarding 120-400 ms.
- **Agent ring/pill:** still 2 px ring + 12 px glow painted once; fade in 240 ms, out 160 ms, `EASE_OUT`; RM instant;
  no loop (`agent/10-indicators.patch:95-260`).
- **No motion tokens** (25 color ids exist). 22 distinct CSS durations (120 ms x19, 160 ms x13, 150 ms x7), 6
  custom beziers; `--ease-out` is defined two ways in one WebUI. Space dots have no animation.
- **Reduce Motion covered on every animated rac surface found**; two inherited Chromium pieces read it only at
  construction (toggling affects new rows only). Neither rac nor Helium reads Reduce Transparency.

### Chromium and Helium (FACT, `B:`)

- Defaults: `SlideAnimation` 120 ms EASE_OUT; `LayerAnimator` 120 ms; `BoundsAnimator` 200 ms; button hover 150 ms;
  vertical tab strip 250 ms `EASE_IN_OUT_EMPHASIZED`; hover card delay 300-800 ms; omnibox popup 82 ms; Helium toasts
  300 ms in / 150 ms out.
- `gfx::Tween` as beziers: `FAST_OUT_SLOW_IN` (0.4,0,0.2,1); `_2` (0.2,0,0.2,1) (within 4 % of Core Animation default
  (0.25,0.1,0.25,1)); `_3` (0.2,0,0,1); `ACCEL_45_DECEL_88` (0.45,0,0.12,1); `ACCEL_5_70_DECEL_90` (0.05,0.7,0.1,1);
  `ACCEL_30_DECEL_20_85` (0.3,0,0.8,0.15). Quadratic `EASE_IN_OUT` trails Dia's curve by up to 13.5 pt of a 37 pt slide.
- **Reduce Motion:** `gfx::Animation::PrefersReducedMotion()` reads `NSWorkspace.accessibilityDisplayShouldReduceMotion`;
  `RichAnimationDuration()` returns 0. `--force-prefers-reduced-motion` / `--force-prefers-no-reduced-motion` override it
  for native UI, so agents can test without changing system settings.
- **`BrowserAnimationController`:** declarative motions, logs `.AnimationFPS` and `.TimeOfLongestAnimationStep`;
  `gfx::Tween` curves only, so redirects keep position not velocity (INFERENCE). **Fast resize:** `NativeViewHost`
  can move and clip without resizing the page, one real resize at the end. `ThrottleMainFrameTo60Hz` off on desktop.

### Competitors (CLAIM-quality for Dia/Arc: Ardia's recordings and binary reading)

- **Dia sidebar, one spring both ways:** response 0.215 s, ζ 0.79; 90 % at ~100 ms, 1-2 pt overshoot ~0.15 s, rest
  ~0.27 s; page resized every frame **[checked `A:docs/dia-spec.md:240-253`]**. **Arc edge peek in:** response 0.185
  s, ζ 0.77, slide with no fade, ~1.5 % overshoot; out ~150 ms ease-in-out; Arc docked hide 100 ms ease-out cubic.
- **Dia tab open:** new row instant, rows below 140 ms (0.25,0.1,0.25,1). **Close:** row fades 100 ms (0,0,0.58,1),
  rows up 140 ms drawn over it, hover follows final layout. **Hover card:** 0.5 s delay; show opacity 0.10 s
  (0.25,0.46,0.45,0.94) + scale spring 0.92 to 1 (response 0.25, ζ 0.75) from nearest corner; dismiss ζ 0.6;
  row to row no re-animation **[checked]**. **Command bar:** grows from URL field ~130 ms, matches expo-out
  (0.16,1,0.3,1) within 1.2 % (INFERENCE); 1.50 removed the new-tab bar entrance. Spinner 1.88 s linear. Pressed fill
  white 31 % / 70 %, no scale. Flick threshold 5 pt/s (rac 300 DIP/s).
- **Zen:** space switch spring bounce 0, 250 ms; reveal 0.25 s CSS `linear()` spring (1.09 % overshoot), hide 0.15 s
  `ease`; tab open 0.12 s scale 0.95 to 1, close 0.1 s; Glance 350 ms arc, page behind 0.97, spring bounce 0.2;
  press 0.98; blur only when `prefers-reduced-transparency` unset.
- **Ardia peek:** scale 0.12 from the link, spring (0.22, 0.9) overshoot clamped, fades in over first 35 %, close 150
  ms ease-in cubic, expand-to-tab 170 ms, RM 150 ms fade. Press 0.99 + opacity 0.95, 80/180 ms.
- **Nook** 5 tokens but 38 literals leak; peek from scale 0.001; Liquid Glass removed as not "calm". **Ora** springs
  (0.2,1.0), (0.3,0.8); no RM reads. **T3 Code** panels 0 ms by default, `steps(4)` loops paused off screen, agent
  cursor opacity 1 / 0.35 / 0.18. BrowserOS and Nook agent glows loop forever.
- **Spring conversion (FACT):** stiffness (2π/response)², damping 4πζ/response; SwiftUI bounce b gives ζ = 1 - b.

### Principles

- Apple: avoid motion on frequent actions; no overshoot unless the gesture has momentum; bounce 0 when unsure; RM =
  fades instead of slides, keep gesture tracking. Emil Kowalski: never animate keyboard actions; under 300 ms; press
  0.97; never from scale 0; transform and opacity only; transitions retarget, keyframes don't.

## What rac should take (ranked)

Cost: XS < 1 d; S 1-3 d; M ~1 w; L 2+ w (includes burst-frame proof and an RM pass).

1. **Token file plus spring primitive** — S-M. New `chrome/browser/ui/views/rac/motion/rac_motion.{h,cc}`:
   `rac::Spring{response, damping_ratio}` (closed forms ζ <1, =1, >1; `ValueAt`/`VelocityAt`/`SettleTime`, keep the
   240 Hz rest search), compositor `SpringTransformElement`/`SpringOpacityElement`/`CurveElement`, one Reduce
   Motion helper read at **every** animation start, shared `rac_motion.css` with `linear()` springs (C++
   `gfx::LinearTimingFunction` exists). Tokens: instant 0; hover 50; fade 100; list 140; exit 150; panel 250 ms;
   ease standard (0.2,0,0,1); list (0.2,0,0.2,1); fade-out (0,0,0.58,1); expo (0.16,1,0.3,1); in-out
   (0.65,0,0.35,1); springs dock 0.215/0.79, reveal 0.185/0.77, page 0.25/1.0, grow 0.22/0.9, pop 0.25/0.75, pop-out
   0.2/0.6, move 0.22/1.0. Add a lint so literals don't leak. Optional: two hunks in `ui/gfx/animation/tween.{h,cc}`
   for spring `Tween` types, or a rac `BrowserAnimationProvider` with 8-12 linear keyframes (no upstream edit).
2. **Quick AI panel (M11)** — XS. Open 250 ms (0.2,0,0,1), close 200 ms; two one-line hooks (flyover duration default;
   tween in `side_panel_animations.cc`). Keep pointer-following edge pull.
3. **Edge reveal on the compositor (M2)** — M, after the first Helium sync (replaces Helium's zen-mode reveal code).
   Keep 100 ms dwell and 300 ms grace; in = reveal spring, slide only, no fade; out 150 ms in-out; lay out once, animate
   layer transform, retarget with velocity; card inset 5-8 pt. RM: fade in 120, out 100 ms.
4. **Cmd+S both ways on the dock spring (M1)** — M-L. Sidebar and card's left edge move together. Page: A) resize
   per frame, or B) fast resize. Ship A only if `TimeOfLongestAnimationStep` <= 8 ms at 120 Hz on a heavy page. RM:
   sidebar fades 120 ms, page width changes once.
5. **Dia tab open/close (M4, M5)** — S-M. Open: row in slot at once, rows below slide 140 ms list ease. Close: selection
   moves first, row fades in place 100 ms, rows below slide up over it 140 ms, hover follows final layout. RM instant.
   Prefer per-row layer transforms (FLIP); minimal hook: settable duration/tween on the layout manager.
6. **Press and unified hover (M9, M10)** — S. Pressed fill at 0 ms; icon buttons scale 0.96 in 80 ms, back 160 ms; text
   rows fill only. Row hover stays 50 ms; other hovers 120 ms standard ease. Tooltips: first after 500 ms, then
   instant. RM: color only.
7. **Space wash cross-fade on the page spring (M3)** — S. Tint/gradient driven from pager progress (two layers); align
   tab-list header slide to the page spring; keep 150 ms RM cross-fade.
8. **Motion test recipe** — S. Burst capture (`burst DIR N MS`), synthesized 120 Hz swipes
   (`window-screenshot-swipe.patch:46,56-72`), `--force-prefers-reduced-motion`, pure-math spring unit tests (90 %
   time, overshoot, rest), the 8.3 ms frame gate.
9. **Reduce Transparency / Increase Contrast** — S. Use `ui::OsSettingsProvider::PrefersReducedTransparency()` for a
   solid tint; gate WebUI `backdrop-filter` on `prefers-reduced-transparency`.
10. **Command bar (M7) and peek (M8)** when built. Command bar: clip-rect grow from the field's box, 130 ms expo-out,
    content not scaled, close 80 ms, no entrance as new tab page, RM 80 ms fade. Peek: grow from link box (not below 0.12
    scale) on the grow spring, opaque by 35 %, page behind dims to black 25 % without scaling, close 150 ms, expand to
    tab 170 ms; contents render at final size, only layer scale/translate animate; RM 150 ms fade.
11. **Haptic tick on pin/favorite snaps (M6)** — XS-S (`NSHapticFeedbackManager`, new `.mm`); menu pins move on the move
    spring.
12. **Agent motion (M12-M14)**: keep the still ring; fade in 200 ms, out 150 ms; dim to 40 % while the user has the tab;
    confirm cards 200 ms, opacity + 4 px rise, no scale, CSS transitions; row expand 150 ms. Optional off-by-default:
    <=600 ms sweep at run start, 300 ms click ring. Progress loops stepped <=15 updates/s, only while a step runs and
    the tab is visible.
13. Hover cards (M, only if wanted). Keep Helium toasts.

**Rules to adopt:** frequency sets budget (hundreds/day: 0-100 ms color/opacity only; tens/day: 150-270 ms with
springs; rare: up to 400 ms); spatial changes move (Cmd+S, reveal, space switch, even by keyboard), content swaps
don't (Ctrl+Tab, Cmd+1-9, new-tab bar); springs for movement, fixed curves for opacity/color, exits faster than
entrances; always interruptible; compositor first; no idle repaint; Reduce Motion = <=150 ms fades with zero
overshoot; no motion settings.

**Cost of techniques (Chromium):** compositor layer animation (transform, opacity) stays smooth with a busy UI thread
(pager, reveal, peek, press scale, list slides, ring and card fades). Bounds/layout animation is costly and needs
measuring (Cmd+S dock, side panel, since the page changes width). WebUI transform/opacity transitions run on the
renderer compositor; `grid-template-rows`, width, height run layout each frame (INFERENCE).

## What rac should avoid

1. Idle loops (BrowserOS 3 s pulse, Nook rotating gradients) — continuous repaint.
2. Growing from nothing (Nook peek scale 0.001); start at a real rect or >= 0.9.
3. Slow starts/long durations on frequent surfaces (side panel 350 ms; Zen Glance 350 ms is a rare-surface ceiling).
4. Motion settings (T3 Code slider, Zen's 156 prefs); Reduce Motion is the only switch.
5. Private macOS APIs for looks (Ardia's material 29, `CAFilter` by class name). Chasing Liquid Glass (Nook reverted in
   two weeks; HIG: sparingly).
6. Per-frame page resize without measurement (Chrome side panel, Dia sidebar do it).
7. Keyframes for flippable state; bounce on consent/safety UI (Aside ~6 % overshoot); animating keyboard content swaps.
8. Copying The Browser Company's artwork or shaders. Values are facts; images and shaders rebuilt from a binary are not
   (INFERENCE, not legal advice). rac's `rac_color_mixer.cc:33,53` comments already cite Dia asset catalogs.
9. Effects that defeat compositor caching (Zen #6302: rounded content corners, 30-45 % GPU).
10. Leaving `ThrottleMainFrameTo60Hz` on without a perf-bench reason.

## Caveats

- **Whole dossier unverified.** The author did not run rac; Cmd+S "show snaps" is code-reading only (I confirmed the
  layout applies the slide ratio only to the floating strip, consistent but not proof).
- **I checked:** side panel 350 ms / `ACCEL_45_DECEL_88` / shadow timings, tab list 200 ms `EASE_IN_OUT`, Dia sidebar,
  Arc peek and hover-card numbers (as written in Ardia's `dia-spec.md`). Everything else (Zen constants, Nook/Ora/T3
  values, other Chromium defaults, patch line numbers) is **unverified**.
- **Inconsistency:** Ardia's note says Arc peek hits 93 % in 66 ms; the dossier's fitted-spring table says 90 % at
  85 ms and M2 says "93 % in ~85 ms". Stated overshoots also differ from the fitted springs (Dia 1.75 % fitted vs
  "1-2 pt" stated; Arc 2.26 % vs 1.5 %). Treat settle figures as approximate.
- **Dia/Arc numbers are CLAIM:** one developer, ±1 frame. No Arc data for command bar, Peek, Little Arc, tab
  open/close, or Cmd+S show.
- Build tree lags `main`; WebUI values come from patches. Helium commit 899e8eb ("bouncing at the window edge" fix) is
  not in rac. Helium issue #1887 (frame drops) is a Windows 240 Hz report, not Mac.
- Unknown: `NSVisualEffectView` under Reduce Transparency; whether histograms record in a metrics-removed build; real
  120 Hz layout cost. AI-off cost is INFERENCE; the token/spring code loads regardless and must cost nothing idle.
- **Open decisions for the maintainer:** dock ζ 0.79 vs 1.0 (both settle ~0.27 s); per-frame resize vs move-and-clip;
  edge dwell (keep 100 ms / shorten / pointer-speed check; Zen's top complaint is early close); 1:1 swipe tracking
  under RM; flick threshold; keyboard rule (spec animates spatial changes only); `gfx::Tween` hook vs keyframe
  provider; keep both address-bar layouts (doubles every check); card radius 11 vs 10 against Helium's 17 px macOS 26
  corner (INFERENCE); agent click marker/sweep; hover cards.

## Where to look in the full dossier

`plans/research/motion-and-feel.md`: snapshot 38-53; per-feature inventory 55-137; spring math and table 143-174;
principles 176-229; **rac today from patches** 231-267; **Chromium/Helium defaults, tween table, Reduce Motion,
BrowserAnimationController, fast resize** 269-325; competitors 327-378; visual language 380-397; signature and bad
interactions 399-435; **spec: rules 451-471, tokens 473-496, M1-M16 table 502-519**, accessibility 521-527;
architecture 529-583; data 585-595; agents 597-611; testing/frame budget 613-634; strengths/weaknesses 636-664;
ranked take/avoid 666-719; open questions 721-754; sources 756-815.
