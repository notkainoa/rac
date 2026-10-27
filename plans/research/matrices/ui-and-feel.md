# Matrix: UI, looks, animation, and feel

Compares rac with Arc, Dia, Zen, Nook, Ora, Ardia, and Cra. Built on 2026-10-27 from the 18 digests in
`plans/research/digests/`, with exact numbers re-read from `plans/research/motion-and-feel.md` (the "motion
dossier") and the Zen, Ardia, Nook, Ora, Cra, and closed-browser dossiers. No new measurement was done.

## In plain English

rac's best motion, the space swipe, already matches Arc. The rest is uneven: about 22 different durations, no
shared list, and no press feedback. Cmd+S probably snaps when the sidebar returns, edge reveal re-lays out the
page every frame, and the AI panel starts slowly. This file compares how rac and seven other browsers look and
move. The Arc and Dia numbers come from one developer's recordings. Nobody ran these browsers in this research,
so every number is read from code or reported by someone else. The plan is one token table, one spring tool,
springs for things that move, short fades for frequent actions, nothing looping while idle, and Reduce Motion
turning slides into fades. Copy Dia's sidebar and tab motion. Skip endless glows, second UI toolkits, and
private Apple materials.

## How to read the tables

- **Source tags.** FACT = primary source (code or vendor docs). CLAIM = self-report, or a number someone else
  recorded. INFERENCE = reasoning or arithmetic. Each is followed by how it was obtained.
  - `code` = read from source code.
  - `rec` = recorded by Ardia's owner from 60 to 240 fps screen recordings or binary reading. Accuracy is CLAIM
    (one developer, about plus or minus one frame). Used for every Arc and Dia number.
  - `calc` = arithmetic done by the dossier author from the stated parameters.
  - `unrun` = nobody ran the product. This applies to every cell for rac, Zen, Nook, Ora, Ardia, Cra, Arc, and
    Dia, so no cell is "measured by us". The tag `rec` is the nearest thing to a measurement.
- **Springs** are written `spring(response s, damping ratio)`. Damping 1.0 means no overshoot. Conversion:
  stiffness = (2 pi / response)^2, damping = 4 pi x ratio / response, mass 1 (FACT, code, `dockMotion.ts:12-15`).
  SwiftUI `bounce b` gives ratio 1 - b. SwiftUI `.snappy` is (0.5, 0.85) (FACT, SDK interface).
- **Curves** are CSS `cubic-bezier(x1,y1,x2,y2)`. Chromium names for them are in the token section.
- **"?"** = not in the digests or dossiers, or not recorded. Nothing was filled in by guessing.
- **RM** = macOS Reduce Motion.
- "Dia" and "Arc" columns also stand in for The Browser Company's shared `ARCUI` code where the dossier says so.
- Extra products (Crest, Stedding, T3 Code, Aside, Chrome's agent) appear only in notes under the tables.

---

## Matrix A: the visual system

| Item | rac today | Arc | Dia | Zen | Nook | Ora | Ardia | Cra |
|---|---|---|---|---|---|---|---|---|
| **UI toolkit** | Chromium Views (C++, `ui/views/rac`, 67 files, 16,108 lines) for chrome; WebUI in plain TS and CSS for the assistant (`app.ts` 2,822 lines, `app.css` 2,484) and onboarding; settings in Polymer and Lit; colors from `AddRacColorMixer`. FACT, code | ? Not stated. Shares `ARCUI` pager constants with Dia. CLAIM | AppKit only on Mac. Quoted: "any use of SwiftUI (on Mac specifically) consistently regressed performance". CLAIM, quote via Michael Tsai | HTML, CSS, and privileged JS in Firefox's chrome document (Gecko). Motion library v13.2.0, Web Animations, CSS `linear()` springs. UI-only rebuild is front-end only. FACT, code | SwiftUI and AppKit shell over system WKWebView. One token file, `NookDesign.swift`. FACT, code | SwiftUI and AppKit over WKWebView. Vendored SwiftUI `HSplit`. FACT, code | React Native macOS (no Reanimated) plus native Obj-C++ `ArdiaCore`, around Chromium. Metal for New Tab shaders. 94 animations native-driver, 22 on the JS thread. FACT, code | AppKit for windows, layout, animation. SwiftUI for sidebar, command bar, settings. Each page is its own frameless Chrome window (CEF), moved to follow the card. FACT, code |
| **Sidebar width and states** | Width ? (not in digests). States: full or hidden only, plus edge reveal. No icons-only mode. Left or right. Top bar default (40 px, pill radius 10, Chat 8) or sidebar address bar. Favorites tiles 44 px, at most 3 per row in full sidebar. FACT, code | Docked 227.5 pt. Page card inset 10 pt on all sides, docked or hidden. Hidden: floating peek panel 227.5 pt wide, inset 5 pt, 0.5 pt light border. CLAIM, rec | 190 pt default. Sidebar or top strip. Top strip tabs 173 wide on a 177 pitch; selected tab joins the card with concave flares radius 15. CLAIM, rec | Width ? Compact Mode hides sidebar, toolbar, or both; reveals at the edge. Space header 44 px. Toolbar 38 px (42 in some modes). FACT, code | Minimum 206 pt, width otherwise ?. Left or right. Hide plus edge reveal. FACT, code | Width ? (draggable `HSplit`; drag to hide). Toolbar can hide (Cmd+Shift+D). FACT, code | 190 pt default (Dia's numbers). Sidebar or top strip per window (Shift+Cmd+S). FACT, code | 220 to 520 pt, default 328. Floating sidebar: 2 pt edge trigger, 24 pt leave slack, 12 pt corners, 8 pt margin. FACT, code |
| **Corner radii, padding, window chrome** | Card inset 6, gap beside sidebar 10. Radii: 12 popups, menus, link cards, space editor; 10 URL pill and infobar cards (margin 8); 11 find Ask pill; 8 tiles, controls, swatches; 6 menu rows; 4 pinned page button; space dots 3 and 3.5. Helium window corner 17 px on macOS 26 (12 older). Card 10 or 11 inside a 6 px inset is not concentric with 17 (17 - 6 = 11). Infobars become cards. FACT, code; concentricity INFERENCE | Card inset 10 on every side. Radii not measured. CLAIM, rec | Card inset top 6, right 7, bottom 7, radius 10. Toolbar 41 pt. Rows 34 on a 37 pitch, inset 6. Pinned tiles 41 tall, 6 apart, radius about 10, 0.5 pt hairline white 0.14. Hover square about 30 pt, radius 7. Panels: inset 16, radius 12, rows 32. Command panel about 16 to 20, continuous. CLAIM, rec | Floating card inset 8 px, shadow `0 3px 8px` black 24%. Squircles through CSS `corner-shape`: base 7 x 1.3, tabs 8, tab margin 2. Floating URL bar radius 15. FACT, code | Continuous squircles 4 / 6 / 8 / 12 / 16 / 24. Spacing 2/4/6/8/12/16/20/24. Rows 32 pt, 2 pt gaps, folder indent 20. Shadows: `floating` black 16% r32 y12; `raised` 5% r2 y1. FACT, code | Tabs and URL 10, launcher 20, settings cards 16, password popup 18, dialogs 11, switcher 32, capsules 99. macOS 26 uses system `ConcentricRectangle`. Hidden title bar, custom traffic lights from images. Launcher shadow black 10% r40 y24. FACT, code | Dia's, matched: card inset 6/7/7 radius 10, rows 34/37, toolbar 41. FACT, code | Sidebar rows 40 pt, spacing 1, row corner 10, indent 18. Card corner 6 (square at the toolbar join in 0.1.12). Toolbar 32. Command bar 766 wide. Find bar 300 x 38. Space cells 34 x 32 pt with no gap, 6 pt hover corners. FACT, code |
| **Translucency and materials** | Helium's behind-window `NSVisualEffectView` (Sidebar material dark, Menu light, always active) whenever a space wash applies, under a tint: dark `#121212` at alpha 0x99, light white at 0xCC. Helium keeps vibrancy off by default and calls it experimental. **Reduce Transparency is not read by rac or Helium.** FACT, code | Gradient themes with a grain layer. Material ? CLAIM | Private `NSVisualEffectView` material 29 dark / 13 (`.hudWindow`) light, base tint black 0.4 dark / white 0.8 light, then a profile-color vertical gradient at alpha 0.5 / 0.75 (bottom stop = tint with HSL lightness +0.25). Card `#121212` at 0.5 / white 0.7. Dia never reads Reduce Transparency; its only accessibility query is Reduce Motion. CLAIM, rec and binary | Behind-window `NSVisualEffectView`. Optional acrylic `blur(42px) saturate(110%) brightness(0.5)` on sidebar and URL bar (beta, Twilight default), skipped when `prefers-reduced-transparency`. Floating URL bar 40 px backdrop blur, same guard. FACT, code | **None.** No blur, vibrancy, or Liquid Glass. Glass shipped in 1.1.1 and 1.2.0, removed in 1.2.1 ("did not match our calm browser philosophy"). Sidebar = static two-stop accent gradient blended 55% toward the window background (80% inactive). FACT, code and changelog | `.underWindowBackground` behind window with 30% theme tint. Find bar `.ultraThinMaterial`. FACT, code | Dia's private material 29 / 13 plus private `CAFilter` gaussianBlur (breaks on OS updates, INFERENCE). Real Liquid Glass (`NSGlassEffectView`) on pinned tiles and URL field on macOS 26, tinted 15% toward profile color. FACT, code | Behind-window blur, default `.hudWindow`. Tuning: active lift 0.35 (bottom 0.37), blur dim 0.36, inactive lift 0.28 dim 1.0, toolbar black overlay 0.40. Light path uses private `CABackdropLayer` and `CAFilter`. FACT, code |
| **Space theming: gradients and colors** | 8 themes named and colored after Dia's `BrandColors`: Neutral (flat gray), Red, Orange, Yellow, Green, Blue, Pink, Purple. Each has a light and a dark gradient pair. 8 older Arc presets migrate. Each space owns a color mode (Auto, Light, Dark). Accent `#FCBF49`; focused URL pill border `#6395FC`. Assistant panel uses the space colors. No theme editor. FACT, code | Per-space gradients with grain, theme colors bleed into command bar and previews. CLAIM, rec and release notes | Profile color drives window tint, New Tab band, edge light, and name. Selected pinned tile themed from its favicon: colorful icon gets a blurred copy as fill plus a 3 pt ring (CIGaussianBlur radius 5); one-color icon gets a flat fill and white template icon. CLAIM, rec | Gradient from up to 3 dots on a color wheel. Harmony modes: complementary 180, split complementary 150 and 210, analogous 50 and 310, triadic 120 and 240, free. Grain PNG with adjustable opacity. Text tinted by accent since 2026-10-25. Space icons shrink to 4 px dots on overflow (150 ms). FACT, code | One accent per space tints the sidebar gradient, folder icons, active dot, load bar. Private window: neutral gray plus purple overlay at 38%. Agent space: fixed amber-to-magenta. FACT, code | One fixed palette: cream `#f3e5d6` light, `#141414` dark, background `#0F0E0E`, accent `#F16D34` / `#FF9B51`. No space themes (rejected, issue #153). FACT, code | OKLab themes from up to 3 colors, grain default opacity 0.1, optional pass-through blur; Arc import carries themes. FACT, code | Gradient imported from Arc's `windowTheme`. Space themes otherwise ?. FACT for import |
| **Typography** | System font through Chromium typography contexts, semibold titles, size deltas of -2 and +1. Assistant: `system-ui` 15 px / 1.5 thread, 12 to 13 px controls, weights 500 and 600, SF Mono for code. FACT, code | SF. CLAIM | SF. 13 pt rows, 13 pt SF Symbols (regular), tab titles 13 to 14, top-strip titles 12. Unselected title white 0.78 dark / black 0.68 light; selected 1.0. Titles fade at the trailing edge, not an ellipsis. CLAIM, rec | SF Pro. FACT, code | System font only: body 13 medium, URL bar 12, captions 11, palette input 15, dialog titles 17. FACT, code | System font only, mostly 12 to 14 pt. FACT, code | SF. 12 pt (127 uses) and 13 pt (95 uses) dominate. FACT, code | System in app; website uses Instrument Serif headings, Geist body (CLAIM). App sizes ? |
| **Iconography** | ? Not covered in the digests. Assistant orb and ring are custom-drawn. FACT for the orb only | Emoji icons for spaces and tabs; custom tooltips that show shortcuts. CLAIM | SF Symbols at 13 pt regular. CLAIM, rec | Emoji or icon per space; Essentials show favicons; Library, footer icons. FACT, code | Space accent without icon; favicons 4 radius; 55% opacity for unloaded tabs. FACT, code | Custom traffic lights from image assets; brand-colored search capsules. FACT, code | SF Symbols as Dia; Arc-style emoji icons imported. FACT, code | Emoji and icon types imported from Arc `iconType`; own toolbar buttons for extensions. FACT, code |
| **Light and dark mode** | Per-space color mode; the browser-wide color scheme and seed color are reset because rac has no setting for them. Dia-derived tab tokens: hover white 16% / 55%, unselected 6%, titles 78% / 68%. Selected tab solid white (light) or black (dark), `0 2px 8px` shadow (white 15% dark / black 12% light) and 1 px hairline. FACT, code | ? | Tokens as the row at left; pressed fill white 31% / 70%; tint and card values differ by mode (see materials). CLAIM, rec | Selected tab white 85% light / 20% dark; hover black 10% light. FACT, code | Light, dark, or system. FACT, code | Light, dark, or system. FACT, code | Dia's tokens copied as a table (hover white 0.16 / 0.55, pressed 0.31 / 0.70, selected black / white). FACT, code | ? Private vibrant light path exists. FACT for the path |
| **Density** | Tabs at rest have no fill. Favorites 44 px, up to 3 per row. Row height ? Top bar 40 px. One density, no setting. FACT, code | ? Peek panel 227.5 wide | Rows 34 on a 37 pitch (dense), pinned tiles 41, one density. CLAIM, rec | Tab radius 8, margin 2, toolbar 38 to 42. FACT, code | Rows 32 pt, 2 pt gaps. One density. FACT, code | 12 to 14 pt type, tabs radius 10. Row height ? | Dia's. FACT, code | Rows 40 pt. The loosest of the set. FACT, code |

Notes on Matrix A:

- **The same three looks recur.** Dia family (blur plus tint plus a profile gradient): rac, Dia, Ardia, Cra.
  Flat accent gradient with no blur: Nook. Pure palette, no themes: Ora. Zen alone adds grain, harmony presets, and
  acrylic.
- **rac's colors already match Dia's catalog** (`rac_color_mixer.cc:33-63` vs `dia-spec.md:407-429`). The rac code
  comments cite "BoostBrowser_TabUI", "ARCClients_BaseAssets", and "SharedAssets". Colors are facts more than
  expression, but publishing a design system on them is an open maintainer decision.
- **Squircles.** CSS `corner-shape: squircle` is on by default in rac's Blink (FACT, code), so WebUI can use it.
  Native Views have no superellipse helper (FACT).
- Outside the eight columns: T3 Code (CSS glass `blur(12px) saturate(1.14)` light, `blur(16px) saturate(1.08)`
  dark; OKLCH; radius 10; themes from 3 hex colors). Helium (window 17 / 12, buttons 7, dialogs and menus 8,
  indigo `#516BEC`). BrowserOS neo (Signal Blue `#0254ec`, editorial). All FACT, code.

---

## Matrix B: motion, one row per interaction

Each cell: duration, curve or spring, what moves, then `[tag, how]`. "RM" notes are included when the source gave
them.

### B1. Space switch, sidebar hide and show, edge reveal

| Interaction | rac today | Arc | Dia | Zen | Nook | Ora | Ardia | Cra |
|---|---|---|---|---|---|---|---|---|
| **Space switch** | Pages slide on a critically damped spring spring(0.25, 1.0) on the compositor thread (custom `gfx::TransformAnimationCurve`). Drag at 0.5x scroll, rubber band 0.15 over 255, flick 300 DIP/s after 4 DIP, rest at under 0.25 DIP and under 15 DIP/s, sampled at 240 Hz, cap 1.5 s. Keys and dots start the spring at zero velocity. Tab-list header: opacity 0.35 to 1 plus 24 px slide, 180 ms (0.4,0,0.2,1). Swipe: axis lock 15 DIP, commit at 75 DIP, reset 300 ms. RM: no swipe tracking, 150 ms cross-fade (140 ms no slide on the header). [FACT, code, unrun] The tint is not tied to the pager progress [INFERENCE] | Same `ARCUI` pager: spring(0.25, 1.0), 0.5x tracking, rubber band `255(1-1/(0.15x/255+1))`. [CLAIM, rec; rac comments copy it] | spring(0.25, 1.0); 0.5x tracking; release at 5 pt/s or more goes to the next page; detent haptics. [CLAIM, rec] | Motion spring `bounce 0`, 250 ms on transform; background cross-fades on the same spring; safety timeout ends the switch at duration plus 50 ms. Rubber band `1 - abs(x)/(4.5 x strip width)`. Swiping past the last space creates one. [FACT, code] | Swipe settle 0.18 s (0.16,1,0.3,1), one haptic at 15% travel, commit past 30% or 0.8 widths/s. Chrome change 0.2 s easeInOut. A contributor reports chrome changes after the slide, not during it. [FACT, code; complaint CLAIM] | AppKit `NSPageController`: `easeOut(0.1)` on state; page move uses `NSAnimationContext` default, about 0.25 s. [FACT, code; duration INFERENCE] | 0.25 s critically damped (0.4 s without Dia's flag), sampled at 1/240 s; wheel bursts within 49 ms add up, then 250 ms cooldown; detent haptics. [FACT, code] | `interpolatingSpring(duration 0.4, bounce 0, initialVelocity = release speed)`, follows the trackpad live. [FACT, code] |
| **Sidebar hide and show (Cmd+S)** | Hide: the page takes full width at once; the now-floating sidebar slides out 200 ms (0.2,0,0,1) with a layout pass per frame. **Show appears to snap** (docked layout ignores the slide ratio). RM: 0 ms. [FACT, code for hide; show is INFERENCE from code, never run] | Docked hide: 100 ms ease-out cubic. Docking from the peek is instant. [CLAIM, rec] | One spring both ways: spring(0.215, 0.79). 90% in about 100 ms, 1 to 2 pt overshoot at about 0.15 s, rest at about 0.27 s. Page is resized every frame. [CLAIM, rec at 240 fps; calc: fitted overshoot 1.75%, 3.5 px of 200] | Compact Mode toggle: Motion spring `bounce 0`, 0.1 s on margins. [FACT, code] | easeInOut 0.1 s. [FACT, code] | spring(0.2, 1.0). [FACT, code] | DOCK_SPRING spring(0.215, 0.79) both ways. [FACT, code] | 0.085 s, (0.15,0.7,0.3,1); comment says "66 / 87 / 96 / 99 % of the travel after frames 1-4" at 60 fps, fitted to Arc. [FACT, code] |
| **Edge reveal or peek** | 100 ms dwell, then Helium's 200 ms (0.2,0,0,1) slide with a layout pass per frame; leave grace 300 ms (was 150); cursor-exit grace 3 s; expand-on-hover delay 100 ms (was 350). Helium trigger 6 px, leeway 8 px. `RichAnimationDuration` read on each reveal (RM 0 ms). [FACT, code] A user reported frame drops in this slide on Windows at 240 Hz (CLAIM, Helium #1887) | In: spring(0.185, 0.77), slide with no fade; the recorder says 93% in 66 ms, about 1.5% (3.5 pt) overshoot at 0.12 s, rest about 0.22 s. Out: about 150 ms ease-in-out. Panel inset 5 pt. [CLAIM, rec; the fitted spring computes 90% at 85 ms and 2.26% overshoot, calc, so figures disagree] | ? Not recorded | 0.25 s CSS `linear()` curve sampled from a spring (peak 1.0109 at 73%); hide 0.15 s `ease`. Keep open 150 ms after leaving; toolbar hides 1,000 ms after hover; pointer may go 200 px sideways or 100 px vertically outside the window (an `NSEvent` monitor that runs only after the pointer leaves while the sidebar shows). [FACT, code] | easeInOut 0.15 s, slide plus fade. Trigger 6 pt, overshoot slack 12 pt, keep-open zone 52 pt past the sidebar, 24 pt vertical slack. Global `NSEvent` mouse monitor per window, started even while the sidebar is shown. [FACT, code; cost INFERENCE] | `.move(edge:)` plus `easeOut(0.1)`. Trigger strip 10 pt, then 40 pt armed padding. [FACT, code] | Arc spring(0.185, 0.77) in, out 150 ms `easeInOutCubic`. Dia-style variant: 180 ms ease-out cubic, hide delay 120 ms. [FACT, code] | Same 0.085 s curve as Cmd+S; 2 pt trigger, 24 pt leave slack, 12 pt corners, 8 pt margin. [FACT, code] |

### B2. Tabs, command bar, hover cards

| Interaction | rac today | Arc | Dia | Zen | Nook | Ora | Ardia | Cra |
|---|---|---|---|---|---|---|---|---|
| **Tab open, close, reorder** | Chromium `TabCollectionAnimatingLayoutManager`: 200 ms quadratic `EASE_IN_OUT` on bounds, new rows fade 0 to 1. RM 0 ms, read only when the manager is built. Hover glow 50 ms (`EASE_OUT` in, `EASE_IN` out). Pin/favorite drag snap: glide 150 ms, 100 ms hand-off; other moves use the 200 ms list animation. No distinct press state. [FACT, code, unrun] The 200 ms quad curve trails Dia's by up to 13.5 pt on a 37 pt slide [INFERENCE, calc] | ? No data | Open: new row instant, already selected; rows below slide 140 ms (0.25,0.1,0.25,1), drawn under it. Close: row fades 100 ms (0,0,0.58,1) in place, rows up 140 ms (fits omega about 40, zeta 0.9), hover follows the final layout. Top-strip reorder: neighbor 91% in 43 ms, done by about 76 ms (omega about 90). [CLAIM, rec] | Open: 0.12 s ease-out, opacity 0 to 1 and scale 0.95 to 1, space opens. Close: 0.1 s, opacity and scale to 0.95, space collapses. Both skipped under RM. Folder open 0.18 s ease-in-out. Press scale 0.98. [FACT, code] | Row move, drag reorder: `snappy` 0.3 s (spring token). Open and close: ? [FACT, code] | Insert from bottom and remove to top, spring(0.3, 0.8). Drag spring(0.2, 0.8) with a 1 pt dashed `[5,5]` outline; drop reorder spring(0.3, 0.8). No RM. [FACT, code] | SLIDE 140 ms, FADE 100 ms, same curves as Dia. Press: scale 0.99 and opacity 0.95, 80 ms in and 180 ms out (no scale under RM). Pins do not animate. [FACT, code] | Row move, folder open, archive: `snappy(0.22, extraBounce 0)`, about spring(0.22, 0.85) [INFERENCE]. Drop indicator `snappy(0.2)`. Pinned collapse `easeInOut(0.25)`. Hover fills `easeOut(0.15)`. Open and close: ? [FACT, code] |
| **Command bar open** | None yet (planned). Chromium omnibox popup: 82 ms opacity, `FAST_OUT_SLOW_IN`. Find-bar "Ask" pill: 120 ms linear fade. New-tab "Ask": 160 ms (0.2,0,0,1). [FACT, code, unrun] | ? Cmd-T bar exists; no numbers | Grows out of the URL field's box in about 130 ms, exponential ease-out (63 / 82 / 92 / 95 / 99% on frames 1 to 5 at 60 fps; (0.16,1,0.3,1) matches within 1.2%, calc). Content is uncovered, not scaled; text keeps its baseline; no scrim. The new-tab bar entrance was removed in 1.50. [CLAIM, rec] | Floating URL bar: no open animation. Search mode: scale `[1,0.98,1]` 0.25 s plus a 1 s accent glow; skipped under RM. [FACT, code] | Palette: `snappy` 0.3 s, spring(0.3, 0.85) [calc]. Icon scales from 0.6 with blur 2; site chip blur 8. [FACT, code] | Launcher: backdrop black 30%, card scale 0.9 to 1, opacity and blur 2 to 0, `easeOut(0.1)`; fixed 250 pt from the top. Tab-to-search: one 0.8 s border sweep (2 pt plus 8 pt glow), then 0.3 s fade. [FACT, code] | GROW_MS 130, `Easing.out(Easing.exp)`. [FACT, code] | 766 pt wide. Open and close timing ? [FACT, code for width] |
| **Hover cards** | None of rac's own. Chromium tab hover card delay 300 to 800 ms by tab width. Link summary card: 500 ms hold, 120 ms fade, 100 ms height coalescing, 700 ms throb while loading (RM: none). [FACT, code, unrun] | ? | Delay 0.5 s (0.1 s with a flag), 0 if a card is already up. Show: opacity 0 to 1 over 0.10 s (0.25,0.46,0.45,0.94) plus scale 0.92 to 1 on spring(0.25, 0.75) from the nearest corner. Hide: 0.10 s plus spring(0.2, 0.6) to 0.92. Row to row the card jumps with no glide. Starts from current values, so it is interruptible. [CLAIM, rec] | ? None found | ? None found | ? A link preview overlay exists; timing ? | Same numbers; leave delay 160 ms, aim 200 ms. Peak scale 1.0022 at 180 ms, settled by 340 ms. Tooltip delay 500 ms, fade 100 ms. [FACT, code] | ? |

### B3. Split, PiP, toasts, agent, page load

| Interaction | rac today | Arc | Dia | Zen | Nook | Ora | Ardia | Cra |
|---|---|---|---|---|---|---|---|---|
| **Split view** | Helium's split drop target: 300 ms (Chromium default 450), 500 ms timers. No rac motion. [FACT, code, unrun] | ? | Targets appear when the pointer is 26 pt below the strip and slide in about 0.11 s; they grow to 322 x 532 over about 0.12 s, no overshoot; the target under the card grows to 362 x 600 and leans 43% toward the pointer. Drop away from a target: a window grows from the card in about 0.2 s. [CLAIM, rec] | Drop: Motion spring `bounce 0.4`, 0.2 s after 0.1 s delay, scale 0.97 to 1 and opacity 0 to 1; haptic tick. [FACT, code] | Drop cards pull 45% toward the cursor within 50 pt, `snappy` 0.3 s, haptic on enter and exit. [FACT, code] | No split view (the website advertises one that does not exist). | ZONE_SLIDE 110 ms; ZONE_SPRING stiffness 987, damping 56.5 = spring(0.2, 0.9). [FACT, code] | Pane add and remove: 0 s (none). [FACT, code] |
| **PiP** | Chromium PiP window, auto-PiP built. No rac motion found. [FACT, code, unrun] | ? | Appears about 125 ms after the tab switch, no fade. Hover scrim black 35%, fade 200 ms ease-in-out. Close fade about 100 ms. Back to tab about 70 ms. Throw: fling over 350 pt/s, nearest corner within 45 degrees, 10 pt inset, spring(0.9, 0.9) (50% at 0.23 s, 90% at 0.49 s). [CLAIM, rec and binary] | ? | ? | ? | Same numbers; 28 pt edge stash; no tilt. [FACT, code] | Controls fade in 0.15 s, out 0.25 s, ease-out. [FACT, code] |
| **Toasts** | Helium: in 300 ms `ACCEL_5_70_DECEL_90` (0.05,0.7,0.1,1), out 150 ms `ACCEL_30_DECEL_20_85` (0.3,0,0.8,0.15), fade 50 ms. [FACT, code] | ? | ? | Motion spring `bounce 0.2`, 0.5 s, scale 0 to 1; hide: opacity and scale to 0.5 in 0.2 s; hover pauses auto-hide; passes `reduceMotion: false`. [FACT, code] | Opacity plus blur 8 to 0, `smooth` 0.25 s. [FACT, code] | Sonner-style stack: show spring bounce 0.2 (0.4 s), dismiss bounce 0.15, restack bounce 0.5; genie exit (width -15%, height -25%, 3.4 degree tilt, 16 pt slide); max 3, 4.0 s. [FACT, code] | ? | ? |
| **Agent-running indicator** | Still 2 px ring plus 12 px glow painted once; fades in 240 ms, out 160 ms, `EASE_OUT`; RM instant; no loop. Working pill with static orb. Step spinner 0.8 s only while a step runs. Assistant orb layers (4 s, 2.8 s) and shimmer (2.4 s) only while a reply is pending. Confirm cards 240 ms (0.23,1,0.32,1). [FACT, code, unrun] | n/a (no agent) | n/a. Dia's AI surface motion was not measured. | n/a (no agent) | Amber-to-magenta gradient, a framed "Agent" label, pulsing sidebar row, and three angular gradients (widths 4/8/12, blur 4/12/24) rotating forever at 2, 2.5, and 3 s; repaints every frame. [FACT, code] | n/a (no agent) | No agent of its own. A "controlling, Stop" pill exists for outside agents; its timing ? [FACT for the pill] | n/a (no AI, "not planned") |
| **Page load** | Helium progress line: 180 ms move, 700 ms pulse, 320 ms fade. Hibernated favicon 250 ms fade. [FACT, code] | ? | Spinner 12 x 12 pt ring (1.5 pt, strokeEnd 0.72), 1.88 s per turn, linear, clockwise. Tab row background change: 0.3 s ease-out. New Tab power-up band: Metal, 60 fps, stops at 3.75 s; halo stops at 2 s; paused under RM. [CLAIM, rec and binary] | ? | Accent-tinted load bar; timing ? [FACT for the bar] | Toolbar tint is re-sampled every 0.25 s during load (a polling loop). [FACT, code] | Dia's spinner implemented in the shell; band 3.75 s and halo 2 s, both paused under RM. [FACT, code] | ? |

Notes on Matrix B:

- **Where the sources disagree.**
  - Sidebar docked hide for Arc: 100 ms ease-out cubic (Ardia) vs 85 ms (0.15,0.7,0.3,1) (Cra, says "fitted to Arc"). One frame at 60 fps apart.
  - Arc edge peek: "93% in 66 ms" (recording note) vs "90% in 85 ms" (the fitted spring's arithmetic).
  - Dia sidebar overshoot: stated 1 to 2 pt, fitted spring 1.75%. Use the fitted spring for timing and the stated figure for feel.
  - Cra's `snappy(0.22)` converts to about spring(0.22, 0.85), while Ardia's matching row-move values are different springs. Treat them as the same feel, not the same math.
- **Outside the eight columns (agent motion).**
  - Chrome's agent: inset glow `box-shadow: inset 0 0 35px 12px #4C8DF6`, opacity 0.6 to 0 to 0 to 0.6 over 4,000 ms, infinite, **no RM guard**. Magic cursor 24 px, 1.5 px/ms clamped 50 to 300 ms, (0.6,0,0.4,1), RM 0 ms. Click 400 ms `ease-out`, scale 0.85. Thinking loop 3,200 ms infinite (off under RM). All FACT, code.
  - T3 Code: agent cursor 150 ms ease-out, opacity 1 acting / 0.35 idle / 0.18 while the human drives. Loops use `steps(4)` to `steps(30)`, default `paused`, one shared `IntersectionObserver`. Panels animate 0 ms by default (slider 0 to 400). FACT, code.
  - BrowserOS: inset glow `box-shadow` 3 s infinite at 60% opacity. FACT, code.
  - Aside approval card: 0.3 s (0.19,1,0.22,1), scale spring 185/18 (about 6% overshoot, INFERENCE). FACT, shipped JS.
  - Crest (not in the eight): sidebar morph 0.28 s, retreat 0.30 s, space swipe 0.32 s snappy, palette 0.18 s, hover 0.14 s, press 0.14 s, collection change 0.22 s, agent pointer 0.35 s, all behind a reduce-motion gate (RM = 0.20 s cross-fade). FACT, code.
  - Stedding (not in the eight): Chromium's "emphasized" curve moved a collapsing sidebar 33% (88 DIP) in one frame at 120 Hz. It switched to `gfx::Tween::EASE_OUT` at Chromium's Mac times (350/400 ms, hover 200/250 ms); the largest step fell to 7 to 14% per frame. Space switch keeps the departing space as a compositor-rastered paint recording (4.6 to 8.8 ms down to 0.7 ms). FACT, docs and code, own measurement by that project.

---

## Matrix C: feel and craft

| Item | rac today | Arc | Dia | Zen | Nook | Ora | Ardia | Cra |
|---|---|---|---|---|---|---|---|---|
| **Reduced-motion support** | Covered on every animated rac surface found; swipe tracking off with a 150 ms cross-fade. Exceptions: two Button hover fades (Chat button 150 ms, site tiles 120 ms) never check it. Two inherited Chromium pieces (tab list manager, tab hover controller) read it only at construction, so toggling affects new rows only. Reduce Transparency and Increase Contrast not read. Test flag: `--force-prefers-reduced-motion`. [FACT, code, unrun] | ? | Reads Reduce Motion (skips the new-tab entrance and power-up). Never reads Reduce Transparency. [CLAIM, binary] | Partial: tab open and close, search mode, space creation, 11 CSS rules. Toasts pass `reduceMotion: false`. No global "disable animations" switch (87 votes, open). Blur skipped under `prefers-reduced-transparency`. [FACT, code] | One place only (the separator, which swaps in a spinner). Space swipes, Peek, dialogs, toasts ignore it. PR #395 adds it to space switching (not merged). [FACT, code] | None. No reads of `accessibilityReduceMotion`. [FACT, code] | Per surface: Peek becomes a 150 ms fade, press scale off, power-up band paused. [FACT, code] | None found in `Sources/`. [FACT, code, grep] |
| **Interruptibility** | Space pager starts from the drag position; keys and dots start at zero velocity. Chromium `SlideAnimation` shortens on reversal. `BrowserAnimationController` redirects keep position, not velocity. [FACT, code; velocity point INFERENCE] | ? | Hover card "starts from the current presentation value" (interruptible). Hover follows the final layout at once after a close. [CLAIM, rec] | Hard per-animation timeout (duration plus 50 ms) so a switch always ends. [FACT, code] | Space switching is not interruptible today; PR #395 would add it. [CLAIM] | SwiftUI springs; behavior when retargeted not checked. ? | Hover card interruptible (as Dia). Spring helper uses Apple's conversion. [FACT, code] | Space settle hands off release velocity (`initialVelocity`). Others ? [FACT, code] |
| **Input never blocked** | No input-blocking animation found in the digests. Agent confirm cards and cards in the thread; Stop via Cmd+. or Esc or the pill. Not tested. [FACT for Stop; INFERENCE for the rest, unrun] | ? | Not stated | Safety timeout ends the space switch. Early closing of edge reveal is Zen's top complaint (#15995, #16002, #16054, fixed in 1.23.4b). [FACT] | Agent approvals are blocking `NSAlert.runModal` "AI Tool Request" and freeze the app. [FACT, code] | JS alert, confirm, and prompt use `NSAlert.runModal` and block the whole app. Launcher fixed 250 pt from the top. [FACT, code] | Tab switch was 40 ms vs Helium 8.5 ms, cut to 10 to 16 ms; dropped frames with the vertical sidebar (#333). [FACT, perf doc] | ? |
| **Idle repaint or CPU** | Nothing loops while idle. Infinite CSS animations only while a reply streams or a step runs. Ring painted once. No benchmark exists, so "never slower than Helium" is unmeasured. Edge reveal re-lays out each frame while sliding. [FACT, code, unrun] | ? | New-tab area light (1.49): 30 fps display link only while key, breathing on a 6 s cycle, stops at 60 s; removed in 1.50. Band 3.75 s and halo 2 s then stop. [CLAIM, rec] | Rounded content corners once cost 30 to 45% GPU (#6302, fixed with Firefox 141). Monitor runs only after the pointer leaves with the sidebar showing. Speedometer 31.6 vs Chrome 37.7, Jan 2025, unverified. [FACT; benchmark CLAIM] | Tool glow and the update card repaint every frame while shown; global mouse monitor per window always on; separator `TimelineView` paused when idle. [FACT, code] | 500 ms `setInterval` URL poll and whole-document `MutationObserver` in every page; 60 s timer walks every tab; one shortcut-recorder pulse is `repeatForever`. [FACT, code] | 20 tabs 1,183 MB vs Chrome 919 and Helium 1,125. New Tab shaders self-stop. [FACT, perf doc] | ? Not measured |
| **Keyboard-first** | Cmd+S hides or shows the sidebar; Cmd+F Ask; Cmd+. or Esc stops the agent; Ctrl+arrows and Ctrl+1 to 9 switch spaces (in the M3 spec). No command bar yet; MRU Ctrl+Tab switcher unconfirmed. Rule: do not animate keyboard content swaps. [FACT, docs; command bar planned] | Cmd-T bar with actions, Shift-Cmd-K Clear, Shift-Cmd-C Supercopy, Opt-Cmd-N Little Arc. [FACT, release notes] | Command bar over the URL field; Cmd+S sidebar. [FACT, changelog] | About 40 declarative command actions, learned score -5 to +5 per command; Cmd+T opens the floating bar; Opt+Shift+L Library. [FACT, code] | Palette has no commands; Ctrl+1 to 9, Cmd+Opt+arrows for spaces. [FACT, code] | Ctrl+Tab switcher with thumbnails (commit on Ctrl release, mouse ignored until it moves); launcher; tab-to-search. [FACT, code] | Cmd+L bar, Ctrl+Tab switcher shows after 140 ms, Shift+Cmd+S layout, `ardia` CLI. [FACT, code] | Cmd+S, command bar, custom `keybindings.json`, `cra://` scripting. [FACT, code] |

---

## Proposed rac motion tokens

Source for the structure: the motion dossier's spec (rules at lines 451-471, tokens at 473-496, spec table M1-M16
at 502-519). Names here use `motion.<name>`; the dossier uses `k...` constants. One header
(`chrome/browser/ui/views/rac/motion/rac_motion.h`) and one shared `rac_motion.css`. Springs are written
`spring(response, damping ratio)`. All are proposals; the maintainer decides.

**Chromium mapping column.** "Tween" = fixed curve usable through `gfx::Tween`, `gfx::SlideAnimation`,
`ui::LayerAnimator`, or `BrowserAnimationController`. "Compositor element" = a rac-owned curve on the compositor
thread, like today's pager `SpringCurve` / `SpringElement` pair, because `LayerAnimator` takes only fixed curves
and cannot start at a gesture's speed (FACT, `sliding-pages.patch:341-344`). Where the digests do not say which
Chromium class to use, the cell says so.

### Durations and curves

| Token | Value | Derived from | Chromium mapping |
|---|---|---|---|
| `motion.instant` | 0 ms | Keyboard tab switches, selection, new-tab bar (Emil Kowalski; Dia removed its new-tab entrance in 1.50) | Set duration to 0. `RichAnimationDuration()` already returns 0 under RM. |
| `motion.hover-row` | 50 ms | Chromium tab hover today (`tab_view.h:64-65`) | Keep Chromium's `GlowHoverController` (50 ms, `EASE_OUT` in, `EASE_IN` out). Note it reads RM only at construction. |
| `motion.hover-control` | 120 ms, `ease-standard` | Unifies rac's 120 / 150 / 160 ms hovers. Nook `quick` 0.12 s; Ora buttons 0.12 s | `FAST_OUT_SLOW_IN_3`. Button hover is 150 ms by default (`button.cc:674`); the digests do not name the hook for changing it. |
| `motion.press` | Fill at 0 ms; icon buttons scale to 0.96 in 80 ms, back in 160 ms; text rows fill only | Dia pressed fill white 31% / 70%; Ardia 0.99 and 0.95 at 80 / 180 ms; Zen 0.98; Emil 0.97 | Layer transform through `ui::LayerAnimator`; compositor-friendly. Today pressed paints like hover. |
| `motion.fade` | 100 ms, `ease-fade-out` | Dia close fade and hover-card opacity (`dia-spec.md:202-203,231-232`) | No named `gfx::Tween` matches (0,0,0.58,1). Use a compositor curve element holding a `gfx::CubicBezier`. |
| `motion.list` | 140 ms, `ease-list` | Dia row slide | `ease-list` = `FAST_OUT_SLOW_IN_2` (0.2,0,0.2,1), within 4% of Dia's (0.25,0.1,0.25,1) [INFERENCE, calc]. Chromium's list manager runs 200 ms quadratic `EASE_IN_OUT` today; the digests propose a settable duration and tween on `TabCollectionAnimatingLayoutManager` (one small upstream edit). |
| `motion.exit` | 150 ms, `ease-in-out` | Arc edge peek out; Ardia peek close | (0.65,0,0.35,1) has no `gfx::Tween` entry; use the compositor curve element. |
| `motion.panel` | Open 250 ms, close 200 ms, `ease-standard` | Replaces the AI side panel's 350 ms `ACCEL_45_DECEL_88`; rare-surface ceiling 400 ms | Two one-line hooks: the default of `kSidePanelFlyoverDurationMs` and the tween in `side_panel_animations.cc`. `ease-standard` = `FAST_OUT_SLOW_IN_3`. |
| `motion.card` | 200 ms, `ease-standard`; opacity plus 4 px rise, no scale | Today 240 ms (0.23,1,0.32,1); calm consent UI | WebUI CSS transitions (they retarget; keyframes do not). |
| `motion.row-expand` | 150 ms, `ease-standard`; content fades over the last 100 ms | Today 150 to 200 ms `grid-template-rows` | WebUI; `grid-template-rows` runs layout each frame, so use only for short lists. |
| `motion.toast` | In 300 ms, out 150 ms (keep Helium's) | Helium toasts | `ACCEL_5_70_DECEL_90` in, `ACCEL_30_DECEL_20_85` out. No change. |
| `motion.command-bar` | Grow 130 ms `ease-expo`; close 80 ms opacity; none as new-tab page | Dia 1.52 (63 / 82 / 92 / 95 / 99% per frame) | `ease-expo` = (0.16,1,0.3,1); no `gfx::Tween`. Animate a clip rect or rounded-rect bounds with a rac curve object; content is not scaled. |
| `motion.tooltip` | First after 500 ms, later ones at 0 ms with no animation | Ardia 500 ms; Emil | Shared helper; Chromium hover-card delay today is 300 to 800 ms. |
| `motion.loop` | Stepped at 15 updates/s or fewer; only while work runs and the tab is visible; spinner no faster than 1.88 s per turn | T3 Code `steps(4)` to `steps(30)`; Dia spinner 1.88 s | WebUI: `animation-play-state: paused` by default plus one shared `IntersectionObserver`. Views: no idle timers. |
| `motion.rm` | At most 150 ms fade, zero overshoot, color changes stay, gesture tracking may stay 1:1 | Apple HIG; Emil | One helper reading `gfx::Animation::PrefersReducedMotion()` at **every** animation start, never in a constructor. |

### Easing curves

| Token | Value | Chromium mapping |
|---|---|---|
| `ease-standard` | (0.2,0,0,1) | `gfx::Tween::FAST_OUT_SLOW_IN_3` (Material 3 standard; Helium's reveal) |
| `ease-list` | (0.2,0,0.2,1) | `gfx::Tween::FAST_OUT_SLOW_IN_2` |
| `ease-fade-out` | (0,0,0.58,1) | None. `gfx::CubicBezier` in a compositor element. |
| `ease-expo` | (0.16,1,0.3,1) | None. `gfx::CubicBezier` in a compositor element. |
| `ease-in-out` | (0.65,0,0.35,1) | None. Quadratic `EASE_IN_OUT` differs (up to 13.5 pt on a 37 pt slide). |

### Springs

All springs live as a `rac::Spring{response, damping_ratio}` with closed forms for ratio under, at, and over 1,
generalizing today's `SpacePager::Spring` (critical damping only). Keep the 240 Hz rest search (rest at under
0.25 DIP and 15 DIP/s). Chromium has no spring `gfx::Tween` type. Two routes, both from the digest:
(a) a rac compositor element, as the pager does; (b) two small hunks in `ui/gfx/animation/tween.{h,cc}` adding
fixed spring `Tween` types, or a rac `BrowserAnimationProvider` that approximates a spring with 8 to 12
`gfx::LinearTimingFunction` keyframes (no upstream edit). `BrowserAnimationController` takes only `gfx::Tween`
curves, so retargeting keeps position but not velocity [INFERENCE]; it logs `.AnimationFPS` and
`.TimeOfLongestAnimationStep` locally.

| Token | Value | Derived from | Notes |
|---|---|---|---|
| `motion.space-switch` | spring(0.25, 1.0) | rac today; Arc/Dia pager; Zen 250 ms bounce 0; Cra 0.4 s bounce 0 | Keep the pager physics. RM: 150 ms cross-fade. Add tint cross-fade driven by pager progress. |
| `motion.space-header` | 180 ms `FAST_OUT_SLOW_IN` (0.4,0,0.2,1), 24 px slide | rac today | Align to the page spring. RM: 140 ms, no slide. |
| `motion.dock` (Cmd+S both ways) | spring(0.215, 0.79); 90% at about 100 ms, rest about 270 ms, 2% overshoot or less | Dia | Open decision: ratio 0.79 vs 1.0 (both settle about 0.27 s). Sidebar layer on the compositor. Page: resize every frame (ship only if `TimeOfLongestAnimationStep` is 8 ms or less at 120 Hz on a heavy page) or Chromium "fast resize" (`NativeViewHost` move and clip, one real resize at the end). RM: sidebar fades 120 ms. |
| `motion.reveal` | In spring(0.185, 0.77), slide only, no fade; out 150 ms `ease-in-out`; dwell 100 ms; leave grace 300 ms | Arc edge peek | Lay out once, animate layer transform, retarget with velocity. Replaces Helium zen-mode reveal code, so do it after the first Helium sync. RM: fade in 120 ms, out 100 ms. |
| `motion.move` | spring(0.22, 1.0) | Cra `snappy(0.22)`; Ora sidebar (0.2, 1.0) | Pin and unpin from menu or shortcut, section dividers. Drag keeps today's 150 ms glide plus 100 ms hand-off. |
| `motion.pop` | opacity 100 ms (0.25,0.46,0.45,0.94) plus spring(0.25, 0.75), scale 0.92 to 1 from the nearest corner | Dia hover card | Row to row: no re-animation. |
| `motion.pop-out` | 100 ms plus spring(0.2, 0.6) to 0.92 | Dia | |
| `motion.grow` (peek) | spring(0.22, 0.9), overshoot clamped; opaque by 35%; close 150 ms; expand to tab 170 ms | Ardia peek; Zen Glance 350 ms arc is the rare-surface ceiling | Starts at the link's box; never from less than 0.12 scale (Emil prefers 0.9 or more, see Unknowns). Contents render at final size; only layer scale and translate animate. Background dims to black 25%, no scaling. RM: 150 ms fade. |
| `motion.pip-throw` | spring(0.9, 0.9); fling over 350 pt/s; nearest corner within 45 degrees | Dia 1.53 | Only if rac wraps Chromium's PiP window; not in the digests how. PiP control fades: 200 ms in-out, close 100 ms. |
| `motion.split-target` | Slide 110 ms; grow spring(0.2, 0.9); pane add and remove instant | Ardia/Dia; Cra "no animation" for pane add and remove | **Added by this matrix (INFERENCE), not in the motion dossier.** |
| `motion.agent-ring` | Fade in 200 ms, out 150 ms; dim to 40% over 150 ms while the user holds the tab | Today 240 / 160 ms; T3 Code opacities 1 / 0.35 / 0.18 | Ring stays a once-painted layer; only opacity animates. RM: instant. |
| `motion.agent-cursor` (optional) | Move up to 300 ms (0.6,0,0.4,1), press 400 ms | Chromium's agent cursor numbers without its glow or loops | Off by default; static under RM. |

### Test hooks that go with the tokens

- Pure-math unit tests per spring: 90% time, overshoot, rest time (Ardia keeps traced points next to its
  springs in a test).
- Burst capture (`burst DIR N MS`) and synthesized 120 Hz swipes from the dev screenshot harness; launch with
  `--force-prefers-reduced-motion` to check the RM path.
- A lint that fails on literal durations and curves outside the token files (Nook leaks 38 literals despite its
  rule; rac has 22 distinct durations today).

---

## What rac's UI should copy

Ranked by value to "immaculate, calm", then by cost. Costs: XS under 1 day; S 1 to 3 days; M about 1 week; L 2 or
more weeks (the digests' scale).

1. **One motion-token file, one spring primitive, one Reduce Motion helper read at every start, plus a literal
   lint.** S-M. This is the base for everything else. It also fixes rac's two `--ease-out` definitions and the 22
   durations. Sources: Nook (tokens, and the leak lesson), Ardia, Cra (fit to frames and write the result in a
   comment).
2. **Dia's sidebar spring both ways, then Arc's edge-reveal spring, on the compositor.** M-L (Cmd+S M1) and M (reveal
   M2, after the Helium sync). The digests rank rac's weakest, most-used motions here: Cmd+S show snaps, reveal
   re-lays out every frame. Gate any per-frame page resize on an 8 ms frame budget.
3. **Quick AI panel: 250 ms open, 200 ms close, standard ease.** XS. Two one-line hooks. 350 ms with a slow start is
   too long for a frequent surface.
4. **Dia tab open and close choreography, plus a real press state and unified hover.** S-M. New row instant, rows
   below 140 ms; close fades in place, rows slide over it, hover follows the final layout. Pressed fill at 0 ms.
5. **Zen's forgiving edge reveal.** S. Keep the sidebar open while the pointer overshoots the window edge, with a
   monitor that exists only in that state. Zen's top complaint was closing too early; Nook's always-on global
   monitor is the cautionary version.
6. **Space wash cross-fade tied to pager progress.** S. rac's pager is its best motion; the tint should move with it.
7. **Command bar that grows from the URL field (Dia), and Peek from the link (Ardia, Zen Glance), when built.** M each.
   Both are in `VISION.md`-conflicted territory (Peek-style previews are listed as not planned), so the maintainer
   decides first.
8. **Stepped, visibility-gated loops and a calm agent cursor.** S. Matches "nothing that repaints continuously".
9. **Reduce Transparency and Increase Contrast.** S. Use `OsSettingsProvider::PrefersReducedTransparency()` and gate
   WebUI `backdrop-filter`. Zen is the only competitor found that guards its blur this way; Dia is known not to.
10. **Space theme depth from Zen and T3 Code.** S-M. Grain layer and harmony presets (Zen); generating a theme from
    two colors in OKLCH (T3 Code). Optional, only if rac allows multi-color themes.
11. **Small touches.** XS-S each. Haptic tick when a drag snaps into favorites or folders (`NSHapticFeedbackManager`).
    Dia's favicon-themed selected pinned tile (Ardia calls it Dia's best small touch, INFERENCE). Ora's copy-URL
    rolling label and one-shot tab-to-search sweep.
12. **A motion test recipe.** S. Burst frames, 120 Hz synthesized swipes, spring math tests, the 8.3 ms gate. This is
    how the Dia numbers were found, and how rac can re-measure them instead of trusting them.

## What it should not copy

Ranked by damage.

1. **Anything that loops while idle.** BrowserOS (3 s inset glow), Nook (three gradients rotating forever), Chrome's
   agent glow (4,000 ms infinite, no RM guard), ego(lite)'s overlay (about 40% GPU plus 18% WindowServer for one
   idle agent Space, per its issue #476). Keep the still ring.
2. **A second UI toolkit.** Ardia's React Native shell cost tab-switch latency (40 ms vs Helium 8.5 ms) and memory;
   Dia dropped SwiftUI for AppKit because it regressed performance. rac stays on Views and WebUI.
3. **Ignoring Reduce Motion.** Ora and Cra ignore it; Nook honors it in one place; Zen passes `false` for toasts.
4. **Private macOS APIs for looks** (material 29, `CAFilter` by class name, `CABackdropLayer`). They break on OS
   updates. Use public materials with a fallback.
5. **Chasing Liquid Glass.** Nook shipped it and removed it in two weeks as not calm. Apple's guidance is "sparingly".
6. **Growing from nothing, and bounce on consent UI.** Nook's Peek starts at scale 0.001; Zen's toast starts at 0;
   Aside's approval card overshoots about 6%. Start at a real rect, keep cards steady.
7. **Motion settings.** T3 Code's 0 to 400 ms slider and Zen's 156 prefs contradict "opinionated". Reduce Motion is the
   only switch.
8. **Per-frame page resize with no measurement, and layout-driven CSS transitions.** Chrome's side panel and Dia's
   sidebar do the first; rac's `grid-template-rows` does the second.
9. **Blocking system alerts and polling loops.** Nook's `NSAlert.runModal` approvals and Ora's JS dialogs freeze the
   whole app; Ora's 500 ms URL poll and 0.25 s tint sampling cost idle CPU.
10. **Copying The Browser Company's artwork, shaders, or strings, or disassembling Dia.** Dia's Terms forbid reverse
    engineering. Numbers are facts; rebuilt shaders and copy are not. rac's own `rac_color_mixer.cc` comments already
    cite Dia asset catalogs, which the maintainer should decide on before publishing a design system.
11. **Effects that defeat compositor caching.** Zen's rounded content corners cost 30 to 45% GPU (#6302). Measure scroll
    CPU and GPU before shipping edge decoration.
12. **Panels that do not animate by default (T3 Code).** Right for power users; abrupt for an Arc-like browser.

---

## Unknowns

- **Nothing was run.** No product in this matrix was launched by the researchers, including rac. rac's Cmd+S "show
  snaps" is code reading only. No screenshots, video, or feel exist for rac's current build.
- **Dia and Arc numbers are one developer's records** (Ardia's `dia-spec.md`): recordings plus some binary reading,
  about plus or minus one frame. Arc has no data for the command bar, Peek, Little Arc, tab open and close, or the
  Cmd+S show direction. Arc's toolkit, materials, radii, and light/dark tokens are unknown.
- **Many cells are "?".** Hover cards: Arc, Zen, Nook, Ora, Cra. PiP: Arc, Zen, Nook, Ora. Toasts: Arc, Dia, Ardia,
  Cra. Tab open and close: Arc, Nook, Cra. Sidebar width: rac, Zen, Ora. rac's iconography and row height.
- **Source conflicts** noted under Matrix B (Arc peek 66 vs 85 ms, Arc hide 100 vs 85 ms, Dia overshoot figures).
- **Reduce Transparency.** Whether `NSVisualEffectView` already goes opaque under the setting is unverified.
- **Real 120 Hz layout cost** of the Cmd+S dock and edge reveal on a heavy page; whether `BrowserAnimationController`
  histograms record in a metrics-removed build.
- **Scale-from rule conflict.** The motion dossier's peek spec allows growth from 0.12 of final scale at the link's
  box; its principles say never animate from scale 0 and start at 0.9 or more. Needs a maintainer or taste call.
- **Open maintainer decisions (from the motion dossier):** dock ratio 0.79 vs 1.0; per-frame resize vs move-and-clip;
  edge dwell (100 ms vs shorter vs pointer-speed check); 1:1 swipe tracking under RM; flick threshold (Dia 5 pt/s, rac
  300 DIP/s); whether keyboard-driven spatial changes animate; `gfx::Tween` spring hook vs keyframe provider; keeping
  both address-bar layouts (doubles every check); card radius 10 or 11 against Helium's 17 px corner; agent click
  marker or sweep; hover cards at all.
- **Rebase risk.** M2 replaces Helium's zen-mode reveal code, and Helium reworked frameless mode around
  expand-on-hover; at Helium 0.20.1.1, 104 of rac's hunks fail (46 first failures), and all 5 sidebar-reveal patches fail.
  Do the first Helium sync before M2.
- **AI-off cost** of the token and spring code is INFERENCE: it loads regardless and must cost nothing idle.
- **Whether publishing values from Dia's asset catalogs is acceptable** is a maintainer decision (INFERENCE, not
  legal advice).
- **Cra and Ardia fit methods.** Cra says its numbers are "fitted to Arc"; its notes were not re-checked here and
  the fit residuals are unknown.

## Sources

Digests (all under `plans/research/digests/`): `motion-and-feel.md`, `zen.md`, `ardia.md`, `nook.md`, `ora.md`,
`cra.md`, `closed-ai-browsers.md`, `rac-baseline.md`, `helium.md`, `aside.md`, `t3code.md`, `long-tail.md`,
`browseros.md`, `ego-lite.md`, `chromium-agent-internals.md` (motion table), `agent-stacks.md` (agent-visible UI).
Also read: `context/maintainer-brief.md`. Skimmed for UI terms and found nothing relevant: `local-first-and-sidecars.md`,
`pomerado.md`.

Dossiers re-read for exact numbers (all under `plans/research/`):

- `motion-and-feel.md`: inventory 55-137; UI and feel 139-527 (rac today 231-267, Chromium defaults 269-325,
  competitors 327-378, visual language 380-397, spec 437-527); architecture 529-583; agents 597-611; testing 613-634.
- `zen.md` 150-260 (layout, visual language, motion table).
- `ardia.md` 117-214 (layout, materials, motion table).
- `nook.md` 238-345 and `ora.md` 155-238 (tokens, materials, motion).
- `cra.md` 89-152 (metrics, motion table, reduced motion).
- `closed-ai-browsers.md` 290-405 (Arc and Dia layout and motion).
- `rac-baseline.md` 180-226 (visual language, typography, motion).

Primary-source file references (inside the dossiers; not re-opened): `A:docs/dia-spec.md` (Ardia's record of Dia and
Arc), `A:apps/browser/src/components/layout/dockMotion.ts`, `Z:src/zen/spaces/ZenSpaceManager.mjs`,
`Z:src/zen/compact-mode/sidebar.inc.css`, `Z:src/zen/glance/ZenGlanceManager.mjs`,
`N:Packages/NookDesign/Sources/NookDesign/NookDesign.swift`, `C:Sources/Cra/UI/ShellView.swift` and `Theme.swift`,
`R:patches/rac/spaces/sliding-pages.patch`, `R:patches/rac/sidebar-reveal/edge-reveal.patch`,
`R:patches/rac/agent/10-indicators.patch`, `B:ui/gfx/animation/tween.cc`,
`B:chrome/browser/ui/views/animations/side_panel_animations.cc`, `B:chrome/browser/ui/animation/README.md`.
Path prefixes are defined at the top of the motion dossier.
