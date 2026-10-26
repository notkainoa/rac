# Motion and feel: research dossier

Comparative study of how Arc, Dia, Zen, Nook, Ora, Ardia, T3 Code, Chromium, Helium, and rac move and look,
plus a proposed motion spec for rac. Written 2026-10-25.

Path prefixes used below (all read-only):

- `R:` this repo, `/Users/knewton/.t3/worktrees/rac/t3-bb0e4397` (branch `plans/overhaul`, same as `main` at d3f0d66
  apart from `plans/`). Line numbers in `.patch` files are lines of the patch file.
- `B:` the built tree `/Users/knewton/Dev/Github/rac/build/src` (Chromium 154 + Helium 0.18.2.1 + rac). Caveat: the main
  checkout sits at commit 9b4d949 (2026-10-22), so its rac WebUI files lag `main` (for example `B:.../rac_ai/app.css:459`
  still has a 696 ms loader that `R:patches/rac/ai/polish-sidebar-ui.patch:258-262` replaced). I use `B:` only for
  Chromium and Helium code and for rac C++ that I checked is unchanged on `main`.
- `Z:` `/tmp/rac-overhaul/src/zen` @9b604fe; `A:` `/tmp/rac-overhaul/src/ardia` @4309c15; `N:` `/tmp/rac-overhaul/src/Nook`
  @242c7fb; `O:` `/tmp/rac-overhaul/src/ora` @4e6cfd1; `T:` `/tmp/rac-overhaul/src/t3code` @1eb4071; `H:`
  `/tmp/rac-overhaul/src/helium` @f29a259 (Helium's newest core, Chromium 156, newer than rac's base).
- `SDK:` `/Applications/Xcode.app/.../MacOSX.sdk/System/Library/Frameworks/SwiftUICore.framework/Modules/SwiftUICore.swiftmodule/arm64e-apple-macos.swiftinterface`
  (Xcode 27.1).
- `D:` sibling dossiers in `R:plans/research/` (zen.md, ardia.md, nook.md, ora.md, t3code.md, helium.md, rac-baseline.md,
  aside.md, browseros.md, closed-ai-browsers.md). I re-checked the motion values I reuse from them against code.

Tags: **FACT** (primary source: code, binary-derived record, or vendor docs), **CLAIM** (self-report or marketing),
**INFERENCE** (my reasoning or arithmetic). Spring numbers like "90 % at 101 ms" are my own arithmetic from the stated
parameters, done with a small script outside the repo; they are INFERENCE unless marked.

## In plain English

Motion is how rac moves when you click, swipe, or hover. Today each part of rac picked its own timing. There are
more than 20 different durations and about a dozen speed curves, with no shared list. Swiping between spaces
already feels like Arc. Other parts feel slower than they should. The AI panel takes a third of a second and starts
slowly. Showing the sidebar with Cmd+S appears to jump instead of slide.

This dossier collects real numbers from Arc, Dia, Zen, Nook, Ora, T3 Code, Chromium, and Helium. Arc and Dia are
closed, so their numbers come from frame-by-frame recordings. It then proposes one motion spec for rac. Each row
gives a time, a curve or spring, and what happens when Reduce Motion is on. Frequent actions get
less motion. Things that move use springs. Nothing loops while idle. Nothing blocks your next click.

## Snapshot

This is a comparative study, so the snapshot has one row per product whose motion I read. Fuller snapshots are in
the sibling dossiers.

| Product | What it is | Engine | Platforms | License | Repo | Stars | Age | Release cadence | Team | Business model |
|---|---|---|---|---|---|---|---|---|---|---|
| rac | Arc-style macOS browser on Helium | Chromium 154 (Helium 0.18.2.1) | macOS | GPL-3.0 | github.com/notkainoa/rac | 0 | repo created 2026-10-02 | 0 releases | 1 maintainer + agents | none (FACT: `gh api repos/notkainoa/rac`; maintainer brief) |
| Helium | Private Chromium browser, rac's base | Chromium 156 in 0.20.1.1 | macOS, Windows, Linux | GPL-3.0 | imputnet/helium (+ helium-macos) | 21,985 (+1,172) | 2025-02-15 | ~2 a week | 2 | tips (FACT: gh api; `D:helium.md` snapshot) |
| Zen | Arc-style Firefox fork | Gecko | macOS, Windows, Linux | MPL-2.0 | zen-browser/desktop | 45,279 | 2024-03-28 | ~1 every 5.4 days | 1 lead + 258 contributors | donations (FACT: gh api; `D:zen.md:36-43`) |
| Dia | The Browser Company's AI browser | Chromium ("ArcCore") | macOS | closed | none | n/a | beta June 2025 | weekly | company (Atlassian-owned) | free; Pro about $20/month (CLAIM, `D:closed-ai-browsers.md:63`) |
| Arc | Dia's predecessor; shuts down 2026-12-22 | Chromium | macOS, Windows | closed | none | n/a | public since 2023 (beta 2022) | maintenance only | company | free (FACT: maintainer brief) |
| Ardia | Open Dia clone with Arc sidebar; records Dia's motion | Chromium 155 + Helium 0.19.4 | macOS 14+, Apple silicon | GPL-3.0 for the app since 2026-10-23 (own files Apache-2.0) | mantrakp04/ardia | 807 | first release 2026-09-25 | 80 releases in 31 days | 1 person + agents | free (FACT: gh api; `D:ardia.md` snapshot) |
| Nook | SwiftUI Arc-like browser | system WebKit | macOS 15.5+ | GPL-3.0 | nook-browser/Nook | 1,980 | 2025-08-01 | ~2 a week | 1 | none (FACT: gh api; `D:nook.md`) |
| Ora | SwiftUI Arc-like browser | system WebKit | macOS 15+ | GPL-3.0 | the-ora/browser | 2,241 | 2025-08-09 | none since 2026-04-07 | 2 | donations (FACT: gh api; `D:ora.md`) |
| T3 Code | Agent workbench (Electron, web, mobile) | Electron 44 | macOS, Windows, Linux, web, iOS, Android | MIT | pingdotgg/t3code | 30,059 | 2026-02-08 | ~3 nightlies a day | T3 Tools Inc. | free (FACT: gh api; `D:t3code.md`) |

## Features

A motion inventory by feature area. For rac, **built** means merged on `main` but never released (rac has zero
releases), **planned** means on the roadmap only. Other products' entries are **shipped** unless marked.

### Tabs, sidebar, spaces

| Surface | rac | Dia / Arc | Zen | Nook / Ora / Ardia |
|---|---|---|---|---|
| Sidebar hide and show (Cmd+S) | **built**. Hide: page widens at once, sidebar slides out over it, 200 ms `cubic-bezier(0.2,0,0,1)`. Show: appears to snap (INFERENCE from code, see UI section) | Dia: one spring both ways, response 0.215 s, damping ratio 0.79; page resized every frame. Arc: hide 100 ms ease-out cubic (CLAIM-quality measurement, `A:docs/dia-spec.md:240-253,255-274`) | Compact Mode toggle: spring `bounce 0`, 0.1 s (`D:zen.md:206`) | Nook `easeInOut` 0.1 s; Ora spring (0.2, 1.0) (FACT `D:nook.md:294`, `O:ora/Features/Sidebar/State/SidebarManager.swift:27`) |
| Edge reveal (hidden sidebar) | **built**. 100 ms dwell, then 200 ms `(0.2,0,0,1)`, 300 ms leave grace | Arc: spring 0.185 / 0.77 in, ~150 ms ease-in-out out | 0.25 s CSS `linear()` spring with 1.09 % overshoot; hide 0.15 s `ease` (FACT `Z:src/zen/compact-mode/sidebar.inc.css:84,172-276`) | Nook `easeInOut` 0.15 s; Ora `easeOut` 0.1 s |
| Space switch | **built**. Critically damped spring, 0.25 s response, on the compositor; RM cross-fade 150 ms | Dia/Arc: 0.25 s critically damped (same ARCUI pager) | Spring `bounce 0`, 250 ms; background cross-fades on the same spring | Nook 0.18 s `(0.16,1,0.3,1)`; Ora AppKit page controller |
| Tab open / close | **built** (Chromium's list animation, 200 ms quadratic ease-in-out) | Dia: neighbours slide 140 ms, closed row fades 100 ms | open 120 ms, close 100 ms, scale 0.95 + fade | Ora spring (0.3, 0.8); Ardia = Dia |
| Pin / unpin, favorites drag | **built**. Drag snap glide 150 ms, 100 ms hand-off; moves use the 200 ms list animation | Ardia: pins don't animate | macOS drop-landing animation; haptic ticks | Ora drag spring (0.2, 0.8) |
| Folders | **built** (same list animation) | n/a | 0.18 s `ease-in-out` | Nook `standard` 0.22 s |
| Row hover | **built**. 50 ms fade in and out (Chromium) | Dia: hover fill token white 16 % / 55 % | hover black 10 % | Nook 0.12 s ease-out; Ora 0.15 s |
| Press | none distinct (pressed = hover fill) | Dia: pressed fill white 31 % / 70 %, no scale | scale 0.98 | Ardia scale 0.99, 80 / 180 ms; Ora 0.95 |
| Tab hover card | none of rac's own | Dia: 0.5 s delay, 0.10 s fade + scale spring (0.25, 0.75) from the corner | n/a | Ardia = Dia |
| Space dots | **built**; no dot animation found (FACT: grep of `patches/rac/spaces`, `patches/rac/sidebar`) | Dia: alpha 0.85 / 0.4 / 0.2, 6 pt dots | overflow dots grow 150 ms | n/a |
| Loading spinner | Chromium/Helium | Dia: 1.88 s per turn, linear | n/a | n/a |

### Navigation and command bar

| Surface | rac | Others |
|---|---|---|
| Omnibox popup | **built** (Chromium): 82 ms opacity, `FAST_OUT_SLOW_IN` (FACT `B:chrome/browser/ui/views/omnibox/omnibox_popup_view_views.cc:216-226`) | Zen floating URL bar: no open animation, 1 s glow on search mode |
| Command bar | **planned** (`R:docs/roadmap.md:137`) | Dia: grows from the URL field, ~130 ms exponential ease-out; NTP bar entrance removed in 1.50. Nook palette spring `snappy` 0.3 s. Ora launcher 0.1 s ease-out, scale 0.9 + blur 2 |
| Find bar "Ask" pill | **built**: 120 ms linear fade (`R:patches/rac/ai/17-find-ask.patch:573-581`) | n/a |
| Site controls | **built**: 150 ms reveal, 120 ms tile hovers (`R:patches/rac/sidebar-address-bar/site-controls.patch:309,364,390`) | Dia panels: no recorded motion |

### Split view, peek, small windows

| Surface | rac | Others |
|---|---|---|
| Split drop target | Helium: 300 ms, 500 ms timers (`D:helium.md:203-213`) | Dia: targets slide in ~0.11 s, grow ~0.12 s; Zen drop spring bounce 0.4 |
| Peek (link preview) | **planned** | Zen Glance 350 ms arc; Ardia spring (0.22, 0.9) from the link; Nook scale from 0.001 |
| Little Arc / small window | **planned** | Arc only; no public numbers |
| Picture in picture | **built** (Chromium window) | Dia: controls fade 200 ms ease-in-out; close 100 ms; throw spring (0.9, 0.9) |

### Import, sync, profiles

| Surface | rac | Others |
|---|---|---|
| Onboarding | **built**: `cubic-bezier(0.2,0.8,0.2,1)`, overshoot `cubic-bezier(0.34,1.4,0.64,1)` at 180–220 ms, 120–400 ms elsewhere, RM block (`R:patches/rac/onboarding/01-first-run-flow.patch:109,719-731`; `04-window-first-and-polish.patch:485,595`) | Zen onboarding springs up to 22 % overshoot (INFERENCE from stiffness 300, damping 20, mass 1.8) |
| Import progress | **planned** (Arc import) | n/a |
| Profiles / sync | no motion | n/a |

### Privacy and blocking

| Surface | rac | Others |
|---|---|---|
| Site controls tiles | **built** (above) | n/a |
| Permission prompts, infobars | infobars restyled as cards (**built**); their motion not checked | n/a |

### AI assistant

| Surface | rac | Others |
|---|---|---|
| Panel open / close | **built**: Chromium side panel, 350 ms `cubic-bezier(0.45,0,0.12,1)` on panel width; edge pull opens with no animation (`B:chrome/browser/ui/views/animations/side_panel_animations.cc:51-84`; `R:patches/rac/ai/13-chat-edge-pull.patch:136-143`) | Nook AI column `easeInOut` 0.2 s |
| Reply loading | **built**: orb loader 420 ms ease-out-quint; two orb layers rotate (4 s, 2.8 s) and a shimmer (2.4 s) only while waiting; RM off (`R:patches/rac/ai/polish-sidebar-ui.patch:255-262,362-379,577-606,938-943`) | T3 Code streaming fade 600 ms one-shot |
| Link summary card | **built**: 500 ms hover delay, 120 ms fade, 100 ms height coalescing, 700 ms throb (`R:patches/rac/ai/19-link-summary.patch:691-697,1459-1482`) | n/a |
| New tab "Ask" | **built**: 160 ms WAAPI `(0.2,0,0,1)` (`R:patches/rac/ai/18-ntp-auto-pick.patch:211`) | Dia NTP power-up band: Metal shader for ~3.75 s, then stops |

### Agent

| Surface | rac | Others |
|---|---|---|
| Tab ring and pill | **built**: still ring + glow painted once; fade in 240 ms, out 160 ms, `EASE_OUT`; RM instant (`R:patches/rac/agent/10-indicators.patch:95-171`) | BrowserOS: infinite 3 s inset box-shadow pulse; Nook: three blurred gradients rotating forever; Chrome/Gemini: tab glows |
| Step rows | **built**: chevron 150 ms, title in 150 ms, row expand by `grid-template-rows` 150 ms, step spinner 0.8 s while a step runs (`R:patches/rac/agent/15-quiet-step-rows.patch:1751-1852,1993-2006`) | T3 Code: one plain summary row that expands |
| Confirm cards | **built**: 240 ms `(0.23,1,0.32,1)` (`R:patches/rac/ai/polish-sidebar-ui.patch:1009-1012`) | Aside approval card: 0.3 s expo-out + bouncy scale spring (6 % overshoot, INFERENCE) |
| Agent cursor | none | T3 Code: 150 ms ease-out; opacity 1 acting, 0.35 idle, 0.18 under human control |

### Extensibility

CLI, MCP, and Boosts carry no motion. Boosts are **planned**.

### Other

| Surface | rac | Others |
|---|---|---|
| Toasts | Helium: in 300 ms `ACCEL_5_70_DECEL_90`, out 150 ms `ACCEL_30_DECEL_20_85` | Ora Sonner-style stack; Zen spring bounce 0.2 |
| Address-bar progress line | Helium: 180 ms progress, 700 ms pulse while loading, 320 ms fade | T3 Code 4 %→90 % over 5.3 s |
| Hibernated favicon | Helium: 250 ms fade | n/a |

## UI, look, and feel

### How to read the numbers

- **Spring.** A spring is described by its *response* (seconds; roughly how long one swing takes) and its *damping
  ratio* ζ (1.0 = no overshoot; lower = some bounce). For mass 1: stiffness = (2π / response)², damping =
  4πζ / response. Dia's binary uses exactly this conversion (FACT as recorded by Ardia, `A:docs/dia-spec.md:204`;
  `A:apps/browser/src/components/layout/dockMotion.ts:12-15`).
- **Apple's `duration` and `bounce`.** SwiftUI's `spring(duration: d, bounce: b)` is `spring(response: d,
  dampingFraction: 1 − b)` for b ≥ 0 (FACT `SDK:16765-16792`). So `.smooth` = (0.5 s, ζ 1.0), `.snappy` = (0.5 s, ζ
  0.85), `.bouncy` = (0.5 s, ζ 0.7) (FACT `SDK:3885-3899,16808-16825`). The old `.spring` default is (0.5 s, ζ 0.825)
  and `.interactiveSpring` is (0.15 s, ζ 0.86) (FACT `SDK:16795,16799`). Nook's `snappy(duration: 0.3)` is therefore
  (0.3 s, ζ 0.85) and `smooth(duration: 0.22)` is (0.22 s, ζ 1.0) (INFERENCE from `N:Packages/NookDesign/Sources/NookDesign/NookDesign.swift:135-141`).
- **Cubic-bezier.** `cubic-bezier(x1, y1, x2, y2)` is a fixed speed curve. Chromium names its curves in `gfx::Tween`;
  the mapping is in the Chromium table below.

What the springs in this study actually do (INFERENCE: computed from the stated parameters; "D" is the travel used
for the pixel figures):

| Spring (response s, ζ) | Used by | 50 % | 90 % | Overshoot | Within 1 % |
|---|---|---|---|---|---|
| 0.215, 0.79 | Dia sidebar hide/show | 51 ms | 101 ms | 1.75 % (3.5 px of 200) at 175 ms | 220 ms |
| 0.185, 0.77 | Arc edge peek in | 44 ms | 85 ms | 2.26 % (5.1 px of 227) at 145 ms | 193 ms |
| 0.25, 0.75 | Dia hover card scale | 58 ms | 112 ms | 2.84 % | 262 ms |
| 0.25, 1.0 | Arc/Dia/rac space settle | 67 ms | 155 ms | 0 | 264 ms |
| 0.22, 0.9 | Ardia peek grow (clamped) | 56 ms | 120 ms | 0.15 % | 179 ms |
| 0.2, 1.0 | Ora sidebar | 54 ms | 124 ms | 0 | 211 ms |
| 0.3, 0.85 | Nook `spring` token | 74 ms | 152 ms | 0.63 % | 213 ms |
| 0.5, 0.825 | SwiftUI `.spring` default | 122 ms | 245 ms | 1.0 % | 458 ms |
| stiffness 720, damping 47, mass 1.2 (≈ 0.257 s, ζ 0.80) | Zen library | n/a | 122 ms | 1.5 % | 260 ms |
| stiffness 300, damping 20, mass 1.8 (≈ 0.487 s, ζ 0.43) | Zen onboarding | n/a | 155 ms | 22.4 % | 847 ms |

A caveat on the Dia and Arc records. Ardia says Dia's sidebar overshoots "1–2 pt" and Arc's peek "1.5 % (3.5 pt)"
(`A:docs/dia-spec.md:250-253,264-266`). The springs Ardia fitted to those same recordings overshoot more: 1.75 % (3.3 pt
of 190) and 2.26 % (5.1 pt). The fits were least-squares with 2–3 % residuals, so the stated overshoot is probably
the better guide to how it looks, and the fitted spring the better guide to timing (INFERENCE).

### Principles from Apple, Emil Kowalski, and The Browser Company

Apple (FACT unless marked):

- "Add motion purposefully, supporting the experience without overshadowing it." "Aim for brevity and precision in
  feedback animations." "In apps, generally avoid adding motion to UI interactions that occur frequently." "Let people
  cancel motion." Apple's HIG gives no durations, and "No additional considerations" for macOS
  ([HIG Motion](https://developer.apple.com/design/human-interface-guidelines/motion)).
- Reduce Motion: reduce "automatic and repetitive animations, including zooming, scaling, and peripheral motion";
  tighten springs to reduce bounce; track animations directly with gestures; avoid animating depth (z-axis);
  replace x, y, and z transitions with fades; avoid animating into and out of blurs
  ([HIG Accessibility](https://developer.apple.com/design/human-interface-guidelines/accessibility)).
- Springs: "start with 100% damping, or no overshoot"; "if the gesture that's driving the motion itself has momentum,
  then you should reward that momentum with a little bit of overshoot". Now Playing opens with 100 % damping on a tap
  and dismisses with 80 % on a swipe. Interfaces must be "fully redirectable", and every timer adds latency
  ([WWDC18 "Designing Fluid Interfaces"](https://developer.apple.com/videos/play/wwdc2018/803/)).
- "When you're not sure, use a spring with bounce 0"; "be cautious about using values higher than around 0.4";
  springs keep velocity when retargeted, so interruptions "feel smooth and natural"
  ([WWDC23 "Animate with springs"](https://developer.apple.com/videos/play/wwdc2023/10158/)).
- Core Animation's default curve is `cubic-bezier(0.25, 0.1, 0.25, 1.0)`, "used as the default by most animations"
  ([CAMediaTimingFunctionName.default](https://developer.apple.com/documentation/quartzcore/camediatimingfunctionname/default)).
  Dia's tab-list slide uses exactly this curve (`A:docs/dia-spec.md:230-231`).
- Liquid Glass belongs to the controls layer, "sparingly"; standard materials and vibrancy for the content layer;
  macOS blends "behind window" or "within window"
  ([HIG Materials](https://developer.apple.com/design/human-interface-guidelines/materials)).

Emil Kowalski (author of animations.dev; FACT that he wrote these, the advice itself is opinion):

- "Never animate keyboard initiated actions" (Raycast "hundreds of times a day" has no open animation); "UI animations
  should generally stay under 300ms"; "A 180ms dropdown animation feels more responsive than a 400ms one"
  ([You don't need animations](https://emilkowal.ski/ui/you-dont-need-animations);
  [Great animations](https://emilkowal.ski/ui/great-animations)).
- Press scale 0.97; never animate from `scale(0)`, start at 0.9 or more; first tooltip delayed, later ones "no delay
  and no animation"; `ease-out` for entering and exiting; origin-aware popovers that scale from the trigger; a little
  `blur()` to hide an imperfect cross-fade
  ([7 practical animation tips](https://emilkowal.ski/ui/7-practical-animation-tips)).
- Animate `transform` and `opacity`; use transitions rather than keyframes when the state can flip mid-way, because
  transitions retarget ([Great animations](https://emilkowal.ski/ui/great-animations)).
- His curve set, as taught in the local `emil-design-eng` skill (secondary source): `--ease-out:
  cubic-bezier(0.23, 1, 0.32, 1)`, `--ease-in-out: cubic-bezier(0.77, 0, 0.175, 1)`, `--ease-drawer:
  cubic-bezier(0.32, 0.72, 0, 1)`; durations: press 100–160 ms, tooltips 125–200, dropdowns 150–250, modals and
  drawers 200–500 (`~/.claude/skills/emil-design-eng/SKILL.md:112-132`). rac's assistant already uses the first curve
  and T3 Code the third.

The Browser Company (FACT):

- Dia: "We fluidly animate the most commonly used UI like the Assistant Bar"; "a single obvious way to accomplish any
  task"; hiding the bookmark button and site settings until hover "helps preserve a sense of calmness"; no update
  banners ([The strategy behind Dia's design](https://browsercompany.substack.com/p/the-strategy-behind-dias-design)).
- Dia dropped SwiftUI on the Mac: "On Mac, we now use AppKit exclusively. We found that any use of SwiftUI (on Mac
  specifically) consistently regressed performance" ([quoted by Michael Tsai](https://mjtsai.com/blog/2025/05/30/arc-and-dia/)).
- No public Arc motion spec exists. Arc's founding designer lists Command Bar, Split View, Focus Mode, Little Arc and
  Previews among his work but publishes no numbers ([Nate Parrott](https://nateparrott.com/arc/index.html)). The only
  Arc numbers are Ardia's recordings and the ARCUI pager constants rac already copies.

### rac today, from the patches

| Surface | Duration and curve | Reduced Motion | Source (FACT) |
|---|---|---|---|
| Space pages after a swipe or switch | critically damped spring, ω = 2π/0.25 s, on the compositor thread (custom `gfx::TransformAnimationCurve`); drag at 0.5× scroll; rubber band 0.15 over 255; flick 300 DIP/s after 4 DIP; rest when offset < 0.25 DIP and speed < 15 DIP/s, sampled at 240 Hz, capped at 1.5 s; release speed clamped so the page never visibly overshoots | swipe tracking off; 150 ms opacity cross-fade | `R:patches/rac/spaces/sliding-pages.patch:242-262,303-339,505-529,557-560,651-654,838-860` |
| Tab list on space switch | opacity 0.35 → 1 and slide 24 px, 180 ms `FAST_OUT_SLOW_IN` = `(0.4,0,0.2,1)` | 140 ms, no slide | `R:patches/rac/spaces/sidebar-motion.patch:262-286` |
| Trackpad swipe gesture | axis lock 15 DIP, switch at 75 DIP, reset after 300 ms | n/a | `R:patches/rac/spaces/switcher.patch:200-209` |
| Edge reveal | 100 ms dwell; Helium's 200 ms slide `(0.2,0,0,1)`; leave grace 150 → 300 ms; expand-on-hover delay 350 → 100 ms, velocity heuristic off | `RichAnimationDuration` read on every reveal → 0 ms | `R:patches/rac/sidebar-reveal/edge-reveal.patch:10,17-18,84-87,142-143,196` |
| Cmd+S hide / show | Hide: page takes full width at once; the now-floating sidebar slides out 200 ms `(0.2,0,0,1)` with a layout pass per frame. Show: the docked layout ignores the slide ratio, so it appears in one frame | 0 ms | INFERENCE from `B:chrome/browser/ui/views/frame/browser_view.cc:1916-1950,6956-6976` and `B:.../layout/browser_view_tabbed_layout_impl.cc:134-141,1013-1030`; not checked by running |
| Tab rows add, remove, move | Chromium `TabCollectionAnimatingLayoutManager`: 200 ms quadratic `EASE_IN_OUT` on bounds; new rows fade 0 → 1 | 0 ms, but read once when the manager is built | `B:chrome/browser/ui/views/tabs/common/tab_collection_animating_layout_manager.cc:84-104`; `R:docs/internals/pinned-tabs-drag.md:37-44` |
| Favorites and pinned drag snap | glide 150 ms, 100 ms hand-off window, only while dragging | `RichAnimationDuration` → 0 | `R:patches/rac/pinned/snap.patch:28,40,215` |
| Tab row hover | Chromium glow hover: 50 ms, `EASE_OUT` in, `EASE_IN` out | controller not created | `B:chrome/browser/ui/views/tabs/common/tab_view.h:64-65`; `tab_view.cc:317-321`; `tab/glow_hover_controller.cc:39-60` |
| Top bar Chat button, site-control tiles | 150 ms / 120 ms hover fades; alpha 0x10→0x22 and 0x0F→0x1C | n/a | `R:patches/rac/ai/09-dia-chat-panel.patch:819,851`; `R:patches/rac/sidebar-address-bar/site-controls.patch:309-390` |
| Press | no distinct pressed state: several rac buttons paint pressed like hovered | n/a | `R:patches/rac/sidebar/new-tab-row.patch:111`; `R:patches/rac/pinned/pinned-section.patch:134`; `R:patches/rac/sidebar/space-section.patch:1222` |
| AI side panel | Chromium: 350 ms `ACCEL_45_DECEL_88` = `(0.45,0,0.12,1)` on width; shadow fades in from 150–250 ms, out in 100 ms; edge pull opens without sliding | Chromium skips the animation | `B:chrome/browser/ui/views/animations/side_panel_animations.cc:51-84`; `B:chrome/browser/ui/ui_features.cc:276-286`; `R:patches/rac/ai/13-chat-edge-pull.patch:136-143` |
| Find "Ask" pill | 120 ms `LINEAR` | instant | `R:patches/rac/ai/17-find-ask.patch:573-581` |
| Link summary card | appears after 500 ms hover; 120 ms fade; 100 ms height coalescing; 700 ms throb while loading | no throb, no fade | `R:patches/rac/ai/19-link-summary.patch:691-697,1459-1482,1679,1732` |
| Agent ring and pill | fade in 240 ms, out 160 ms, `EASE_OUT`; the ring is painted once, no loop | instant | `R:patches/rac/agent/10-indicators.patch:95-171,180-260` |
| Assistant WebUI | `--ease-out` is `(0.2,0,0,1)` in one patch and `(0.23,1,0.32,1)` in a later one; loader 420 ms; confirm card 240 ms; rows expand by `grid-template-rows` 150–200 ms; hovers 120–160 ms; empty state 400 ms; loops only while waiting | `prefers-reduced-motion` blocks | `R:patches/rac/ai/10-dia-chat-thread.patch:45`; `polish-sidebar-ui.patch:237,255-262,1009-1012,1207,938-943`; `R:patches/rac/agent/15-quiet-step-rows.patch:1852,1993-2006` |
| Onboarding | `(0.2,0.8,0.2,1)` and overshoot `(0.34,1.4,0.64,1)` | block | `R:patches/rac/onboarding/01-first-run-flow.patch:109,719-731` |

Observations:

- **No motion tokens.** rac has color tokens (`R:patches/rac/look/tokens.patch:70-115`, 25 `kColorRac*` ids) but no
  motion tokens. Added lines in `patches/rac` hold 22 distinct CSS durations (most common: 120 ms ×19, 160 ms ×13,
  150 ms ×7) and 6 custom `cubic-bezier`s plus `ease` ×25, `ease-out` ×18, `linear` ×9 (FACT: grep over
  `patches/rac`). Consistency depends on review, not structure (INFERENCE).
- **Reduced Motion is covered** in every animated rac surface I found (FACT: grep of `PrefersReducedMotion`,
  `RichAnimationDuration`, `prefers-reduced-motion`). Two inherited Chromium pieces read it only when they are built
  (the list layout manager and the tab hover controller), so flipping the setting affects new rows only (INFERENCE
  from `B:.../tab_collection_animating_layout_manager.cc:84-86`, `B:.../tab_view.cc:317-321`). rac's own edge
  reveal re-reads it per reveal (FACT `R:patches/rac/sidebar-reveal/edge-reveal.patch:139-143`).
- **Nothing loops while idle.** The orb and shimmer run only while a reply is pending and stop under Reduce Motion
  (FACT `R:patches/rac/ai/polish-sidebar-ui.patch:362-379,577-606,938-943`).
- **rac already owns the hard primitive.** The space pager runs a spring as a compositor curve because "ui::LayerAnimator's
  own transitions only take fixed curves, which can't start at the swipe's speed" (FACT
  `R:patches/rac/spaces/sliding-pages.patch:341-344`). It supports only critical damping today (FACT `:505-516`).

### Chromium and Helium defaults (what rac inherits)

| Default | Value | Source (FACT) |
|---|---|---|
| `gfx::SlideAnimation` | 120 ms, `EASE_OUT` (quadratic). Reversing mid-way shortens the duration by `(1 − progress^dampening)` | `B:ui/gfx/animation/slide_animation.h:108,121`; `slide_animation.cc:46-51` |
| `ui::LayerAnimator` implicit transitions | 120 ms | `B:ui/compositor/layer_animator.cc:43` |
| `views::BoundsAnimator` | 200 ms | `B:ui/views/animation/bounds_animator.h:205` |
| `gfx::LinearAnimation` frame rate | 60 fps default, but views delegates tick on compositor frames | `B:ui/gfx/animation/linear_animation.cc:28`; `B:ui/views/animation/animation_delegate_views.cc:77-89` |
| Button hover | 150 ms; toggle 250 ms | `B:ui/views/controls/button/button.cc:674`; `toggle_button.cc:195` |
| Ink-drop highlight | 250 ms; ripples are off on Mac, and Helium turns them off everywhere | `B:ui/views/animation/ink_drop_impl.cc:25-26`; `H:patches/helium/ui/disable-ink-ripple-effect.patch` |
| Vertical tab strip expand/collapse | 250 ms `EASE_IN_OUT_EMPHASIZED`; expand-on-hover 250 ms, collapse 200 ms; opacity 100 ms | `B:chrome/browser/ui/views/animations/tab_strip_animations.cc:56-71` |
| Tab hover card | trigger delay 300–800 ms by tab width | `B:chrome/browser/ui/views/tabs/hovercard/tab_hover_card_controller.cc:134-146` |
| Helium frameless reveal | 200 ms `FAST_OUT_SLOW_IN_3`; trigger 6 px; leeway 8 px; floating sidebar padded 8 px; 3 s grace after the pointer leaves the window | `B:chrome/browser/ui/views/frame/browser_view.cc:441-447,1035-1042`; `B:.../browser_view_tabbed_layout_impl.cc:82` |
| Helium toasts, progress line, split drop, favicon | 300/150 ms; 180 / 700 / 320 ms; 300 ms; 250 ms | `D:helium.md:203-213` (H patch line refs there) |

`gfx::Tween` curves as cubic-beziers (FACT `B:ui/gfx/animation/tween.cc:37-190`). Several are Material 3 tokens
under Chromium names (INFERENCE from matching values,
[M3 tokens](https://m3.material.io/styles/motion/easing-and-duration/tokens-specs)):

| Chromium name | Curve | Note |
|---|---|---|
| `EASE_OUT` | `1 − (1 − t)²` | default for `SlideAnimation` |
| `EASE_IN_OUT` | quadratic in-out | the tab list uses this |
| `FAST_OUT_SLOW_IN` | `(0.4, 0, 0.2, 1)` | Material standard (old) |
| `FAST_OUT_SLOW_IN_2` | `(0.2, 0, 0.2, 1)` | within 4 % of Core Animation's default (INFERENCE, computed) |
| `FAST_OUT_SLOW_IN_3` | `(0.2, 0, 0, 1)` | M3 standard; Helium's reveal |
| `ACCEL_45_DECEL_88` | `(0.45, 0, 0.12, 1)` | the side panel; slow start |
| `ACCEL_5_70_DECEL_90` | `(0.05, 0.7, 0.1, 1)` | M3 emphasized decelerate |
| `ACCEL_30_DECEL_20_85` | `(0.3, 0, 0.8, 0.15)` | M3 emphasized accelerate |
| `EASE_IN_OUT_EMPHASIZED` | three-point bezier | M3 emphasized |

How much these differ, computed (INFERENCE): over a 37 pt row slide, Dia's curve and `FAST_OUT_SLOW_IN_2` never differ
by more than 1.5 pt; Dia's curve and the quadratic `EASE_IN_OUT` that rac's list uses differ by up to 13.5 pt. At a
quarter of the time, `EASE_IN_OUT` has moved 12.5 % and Dia's curve 41 %. The side panel's `ACCEL_45_DECEL_88` has
moved 2 % at 10 % of the time and 22 % at 25 %.

Reduced Motion plumbing (FACT):

- `gfx::Animation::PrefersReducedMotion()` reads `NSWorkspace.accessibilityDisplayShouldReduceMotion`;
  `RichAnimationDuration()` returns zero when it is set (`B:ui/gfx/animation/animation_mac.mm:15-42`).
- `--force-prefers-reduced-motion` and `--force-prefers-no-reduced-motion` override the system for native UI too
  (`B:ui/gfx/animation/animation.cc:146-159`). This lets an agent test Reduce Motion without changing a shared Mac's
  settings.
- Reduce Transparency is available natively (`B:ui/native_theme/os_settings_provider_mac.mm:129-131`) and to WebUI as
  `prefers-reduced-transparency` (`B:third_party/blink/renderer/core/css/media_feature_names.json5:66`). Neither rac
  nor Helium reads it (FACT: grep finds nothing in `R:patches/` or `H:patches/helium/ui/native-frame-materials.patch`).

Chromium 154 also has a declarative motion system, `BrowserAnimationController`. A group has motions; a motion has
sequences of keyframes, segments, and snaps with their own tweens. It redirects mid-way ("start at", "cap at", or
"ignore" the old value), and it can log two histograms per motion, `.AnimationFPS` and `.TimeOfLongestAnimationStep`
(FACT `B:chrome/browser/ui/animation/README.md:1-12,630-660,749-800`;
`B:chrome/browser/ui/animation/browser_animation_controller.h:56-58`). It takes only `gfx::Tween` curves, so redirects
keep position but not velocity (INFERENCE). Chromium's side panel and vertical tab strip already use it.

Chromium can also "fast resize" a web view: move and clip it without resizing the page during an animation, then do
"a real resize at the end" (FACT `B:ui/views/controls/native/native_view_host.h:98-104`). This matters for the sidebar
spec below.

### Competitors, from code

Values re-checked in code for this dossier; fuller tables live in the sibling dossiers.

- **Zen** (Gecko UI in HTML, CSS and JS; Motion library v13.2.0 loaded lazily). Space switch: spring `bounce: 0`,
  250 ms, with the background cross-faded on the same spring (FACT `Z:src/zen/spaces/ZenSpaceManager.mjs:2365-2378`;
  `Z:prefs/zen/workspaces.yaml:26-27`). Compact sidebar reveal: 0.25 s on a CSS `linear()` curve sampled from a spring
  that peaks at 1.0109 at 73 % (FACT `Z:src/zen/compact-mode/sidebar.inc.css:172-276`); hide 0.15 s `ease` (`:84`). Tab
  open: opacity 0 → 1, scale 0.95 → 1, the row's space opens, 0.12 s ease-out; close 0.1 s; both skipped under Reduce
  Motion (FACT `Z:src/zen/common/modules/ZenVerticalTabsManager.mjs:101,153-166,186-209`). Glance (peek): 350 ms along
  an arc from the link, page behind scales to 0.97 and fades with spring `bounce: 0.2` (FACT
  `Z:src/zen/glance/ZenGlanceManager.mjs:36-40,635-646`). Floating URL bar: radius 15, shadow `0 30px 140px -15px`
  black 80 % / 60 %, 40 px backdrop blur only when `prefers-reduced-transparency` is not set (FACT
  `Z:src/zen/common/styles/zen-omnibox.css:269-293`). Drag drops use macOS's own landing animation (FACT
  `Z:src/zen/drag-and-drop/nsZenDropLandingCocoa.mm`).
- **Dia and Arc, as recorded by Ardia** (CLAIM-quality: one developer's binary reading and 60–240 fps recordings).
  The full table is in `D:ardia.md` and `D:closed-ai-browsers.md`; the rows used in the spec are in the comparison
  table below. Dia 1.50 *removed* its new-tab bar entrance spring: "the bar is at scale 1 from the first frame"
  (`A:docs/dia-spec.md:396-400,500-502`).
- **Ardia's own choices** (FACT, code): peek starts at scale 0.12 from the link, grows on spring (0.22, 0.9) with
  overshoot clamped, fades in over the first 35 % of progress, closes in 150 ms ease-in cubic, expands to a tab in 170
  ms ease-out cubic, and under Reduce Motion fades in 150 ms ease-out quad (`A:apps/browser/src/components/peek/PeekOverlay.tsx:16-21,76-115`).
  Row press: scale 0.99 and opacity 0.95, 80 ms in, 180 ms out (`A:docs/dia-spec.md:181-183`).
- **Nook** (SwiftUI): five tokens, `quick` ease-out 0.12 s, `standard` smooth 0.22 s, `spring` snappy 0.3 s, `settle`
  0.6 s, `flight` ease-in 0.6 s (FACT `N:Packages/NookDesign/Sources/NookDesign/NookDesign.swift:133-141`). Peek scales
  from 0.001, which Emil's rule forbids (FACT `D:nook.md:297`). Reduce Motion honored in one place (FACT `D:nook.md:330`).
- **Ora** (SwiftUI): sidebar spring (0.2, 1.0); tab insert/remove spring (0.3, 0.8); hover ease-out 0.15 s; no
  Reduce Motion reads anywhere (FACT `O:ora/Features/Sidebar/State/SidebarManager.swift:27`;
  `O:ora/Features/Sidebar/Views/TabList/NormalTabsList.swift:52`; `D:ora.md:206`).
- **T3 Code** (CSS and the Web Animations API, no motion library): panels don't animate by default (slider 0–400
  ms, default 0) (FACT `T:packages/contracts/src/settings.ts:113-122`); sidebar list moves 150 ms ease-out with travel
  capped at 40 px (FACT `T:apps/web/src/components/Sidebar.motion.ts:1-2`); dialogs 200 ms ease-in-out from scale 0.98
  (FACT `T:apps/web/src/components/ui/dialog-styles.ts:1-8`); loops stepped with `steps(4)` so a 120 Hz display draws
  ~14 frames per cycle instead of ~288 (FACT `T:apps/web/src/index.css:290-308`); `--ease-drawer:
  cubic-bezier(0.32,0.72,0,1)` (FACT `:192`).
- **Aside and BrowserOS** (shipped JS, see `D:aside.md:182-196`, `D:browseros.md:244-248`): web-tech panels with
  Motion springs; BrowserOS's agent glow pulses forever.

### The same interaction, product by product

| Interaction | rac today | Dia | Arc | Zen | Nook | Ora | Others |
|---|---|---|---|---|---|---|---|
| Sidebar toggle | hide 200 ms `(0.2,0,0,1)`; show snaps (INFERENCE) | spring 0.215 / 0.79 both ways | hide 100 ms ease-out cubic | spring bounce 0, 0.1 s | ease-in-out 0.1 s | spring 0.2 / 1.0 | T3 Code: none by default |
| Edge reveal in / out | 200 / 200 ms `(0.2,0,0,1)` after 100 ms dwell | n/a | spring 0.185 / 0.77; out ~150 ms ease-in-out | 0.25 s spring-`linear()`; 0.15 s `ease` | ease-in-out 0.15 s | ease-out 0.1 s | Helium 200 ms |
| Space switch | spring 0.25 / 1.0 (compositor) | spring 0.25 / 1.0 | same ARCUI pager | spring bounce 0, 0.25 s | 0.18 s `(0.16,1,0.3,1)` | AppKit default | n/a |
| Tab open | rows 200 ms quad in-out, fade in | new row instant; rows below 140 ms `(0.25,0.1,0.25,1)` | n/a | 0.12 s fade + scale 0.95 | n/a | spring 0.3 / 0.8 | T3: 150 ms ease-out |
| Tab close | same | fade 100 ms `(0,0,0.58,1)`; rows up 140 ms | n/a | 0.1 s | n/a | spring 0.3 / 0.8 | n/a |
| Command bar | none (planned) | grow from field, ~130 ms expo-out | n/a | no open motion | spring 0.3 / 0.85 | 0.1 s ease-out, scale 0.9, blur 2 | Chromium popup 82 ms fade |
| Peek | none (planned) | n/a | not measured | 350 ms arc | scale from 0.001, 0.3 / 0.85 | n/a | Ardia spring 0.22 / 0.9 |
| Row hover | 50 ms | fill token only | n/a | n/a | 0.12 s ease-out | 0.15 s ease-out | Ardia hover card 0.1 s |
| Press | none | color only | n/a | scale 0.98 | n/a | scale 0.95 | Ardia 0.99, 80/180 ms |
| Side panel | 350 ms `(0.45,0,0.12,1)` | not recorded | n/a | n/a | ease-in-out 0.2 s | n/a | T3: none by default |

### Visual language

| | Window material | Page card | Radii | Shadows | Type | Color and themes |
|---|---|---|---|---|---|---|
| **rac** | Helium's behind-window `NSVisualEffectView` (Sidebar material dark, Menu light, always active) whenever a space wash applies, under a tint of `#121212` at 60 % / white at 80 % (FACT `R:patches/rac/look/dia-chrome.patch:2047-2051`; `H:patches/helium/ui/native-frame-materials.patch:307-372`; `B:chrome/browser/ui/color/rac_color_mixer.cc:21-23`) | inset 6, gap beside sidebar 10 (FACT `B:chrome/browser/ui/views/rac/rac_look.h:23-28`) | 12 popups, 10 URL pill and infobar cards, 8 tiles and controls, 6 menu rows, 4 small buttons (FACT `D:rac-baseline.md:189`) | card: black 60 % dark / 20 % light; selected tab `0 2px 8px` white 15 % dark / black 12 % light (FACT `rac_color_mixer.cc:25-44`; `rac_look.cc:25,69-71`) | system font via Chromium typography; assistant 15 px / 1.5 (FACT `D:rac-baseline.md:195`) | Dia's tab tokens copied (hover white 16 % / 55 %, unselected 6 %, titles 78 % / 68 %); 8 Dia-named space themes; per-space color mode; accent `#FCBF49`; focus `#6395FC` (FACT `rac_color_mixer.cc:33-85`; `D:rac-baseline.md:199-200`) |
| **Dia** | private material 29 dark / `.hudWindow` light, tint, profile gradient α 0.5 / 0.75 | card `#121212` 0.5 / white 0.7, radius 10, inset 6/7/7 | rows 34 on a 37 pitch; tiles ~10; command panel ~16–20 continuous | 1.50 command bar: black 0.08 r2 y0.5 + black 0.04 r1 y2 | SF, 13 pt rows, 13 pt symbols | profile color drives tint, NTP, edge light (CLAIM-quality, `A:docs/dia-spec.md:27-57,84-89,173-177,352-356,493-494`) |
| **Arc** | gradient themes with grain | inset 10 on all sides; sidebar 227.5 pt | not measured | not measured | SF | per-space gradients, grain (CLAIM-quality, `A:docs/dia-spec.md:255-274`; `D:closed-ai-browsers.md:309-311`) |
| **Zen** | `NSVisualEffectView` behind window | separation 8 px | squircles (CSS `corner-shape`), base 7 × 1.3, tabs 8 | card `0 3px 8px` black 24 %; URL bar `0 30px 140px -15px` | SF Pro | 3-dot gradient generator with harmony modes, grain (FACT `D:zen.md:174-192`) |
| **Nook** | none (Liquid Glass removed in 1.2.1 as not "calm") | rounded card or flush | continuous 4/6/8/12/16/24 | floating 16 % r32 y12; raised 5 % r2 y1 | system 13 pt medium | one accent per space, static gradient (FACT `N:.../NookDesign.swift:22-28,227-236`; `D:nook.md:264-281`) |
| **Ora** | `.underWindowBackground` + 30 % tint | n/a | 10 tabs, 20 launcher, 99 capsules; `ConcentricRectangle` on macOS 26 | launcher 10 % r40 y24 | system, 12–14 pt | fixed cream/orange brand palette; no space themes (FACT `D:ora.md:165-180`) |
| **Ardia** | Dia's stack; Liquid Glass on macOS 26 for tiles and URL field, tinted 15 % toward the profile color | Dia's | Dia's | Dia's | SF 12/13 pt | OKLab 3-color themes, grain 0.1 (FACT `A:apps/browser/src/components/glass.tsx:7-9`; `D:ardia.md`) |
| **T3 Code** | CSS glass `blur(12px) saturate(1.14)` light, `blur(16px) saturate(1.08)` dark | n/a | base 10 | composer `0 12px 28px -18px` black 40 % | system stack, 16 px default (12–20 setting) | theme editor, OKLCH (FACT `D:t3code.md:150-180`) |
| **Helium** | materials opt-in, marked experimental | rounded frame | window 17 (macOS 26) / 12; buttons 7; menus 8 | n/a | Chromium default | indigo palette `#516BEC` (FACT `D:helium.md:171-197`) |

Two notes. CSS `corner-shape: squircle` is on by default in rac's Blink, so WebUI can use squircles (FACT, no runtime
flag on `B:third_party/blink/renderer/core/css/css_properties.json5:3272-3290`); native Views have no superellipse
helper (FACT: none in `B:ui/gfx/geometry`). And rac's card radius 10 inside a 6 px inset is not concentric with
Helium's 17 px macOS 26 window corner (17 − 6 = 11) (INFERENCE).

### Signature interactions that feel great

1. **Space swipe with Arc's own physics.** rac's pager matches Dia's ARCUI pager: 0.5× tracking, Apple's rubber band,
   0.25 s critically damped settle, on the compositor (FACT, above). This is rac's best piece of motion today.
2. **Dia's command bar grows out of the address field.** The text stays on its baseline; the panel shape uncovers it
   in ~130 ms. At 60 fps it is 63, 82, 92, 95, 99 % done on frames 1–5 (CLAIM-quality, `A:docs/dia-spec.md:358-367`).
   An expo-out `cubic-bezier(0.16, 1, 0.3, 1)` matches within 1.2 % (INFERENCE, computed). It reads as instant
   but still shows where the panel came from.
3. **Dia's tab close.** The row fades in place while rows below slide over it, and hover follows the final layout at
   once, so the next click lands where you aim (`A:docs/dia-spec.md:225-238`).
4. **Dia's hover cards.** They scale from the corner nearest the row, and from row to row they jump with no
   re-animation (`A:docs/dia-spec.md:196-217`).
5. **Zen's Glance** grows from the clicked link along an arc and shrinks back into a snapshot of it (FACT `Z:src/zen/glance/ZenGlanceManager.mjs`).
6. **T3 Code's stepped loops** cut repaint cost on 120 Hz screens (FACT `T:apps/web/src/index.css:290-308`).
7. **Ora's one-shot color sweep** on Tab-to-search plays once, then stops (FACT `D:ora.md:196`).

### Things that feel bad

1. **The AI panel is slow to start.** 350 ms on `(0.45, 0, 0.12, 1)`: 2 % of the way at 35 ms, 22 % at 88 ms
   (INFERENCE, computed from FACT `B:.../side_panel_animations.cc:51-55`). Emil's rule is under 300 ms, ease-out.
2. **Cmd+S is lopsided.** Hide slides; show appears to snap (INFERENCE from code, see the rac table). Dia and Arc
   both slide both ways. A Helium user describes the same shortcut in frameless mode as a "janky animation where whole
   UI jumps around" ([helium#1971](https://github.com/imputnet/helium/issues/1971), open, CLAIM).
3. **Edge reveal re-lays out the sidebar on the UI thread every frame.** Helium's frameless slide moves the sidebar's
   bounds each frame (`SlideBoundsFromSide`, `B:.../browser_view_tabbed_layout_impl.cc:1013-1018`). A user reported
   "obvious frame drops" in this slide on a 240 Hz screen (Windows 11, Helium 0.13.1.1;
   [helium#1887](https://github.com/imputnet/helium/issues/1887), open, CLAIM). The Mac build was not tested.
4. **The tab list starts slowly and runs long.** Chromium's quadratic in-out runs 200 ms, against Dia's 140 ms, and
   at the same point in time it trails Dia's curve by up to 36 % of the travel (INFERENCE, computed).
5. **No press feedback.** Pressed paints like hovered in rac's own buttons; Chromium's ripples are off on Mac (FACT
   above). WWDC18: "the button should highlight immediately when I touch down on it."
6. **Layout-driven CSS transitions** in the assistant (`grid-template-rows`, and width/height on the orb in the older
   build) run layout every frame instead of only compositing (INFERENCE; FACT for the properties,
   `R:patches/rac/ai/polish-sidebar-ui.patch:1207`).
7. **Elsewhere:** Zen's rounded content corners once cost 30–45 % GPU and choppy scrolling until a Gecko fix
   ([zen#6302](https://github.com/zen-browser/desktop/issues/6302), FACT per `D:zen.md:266-271`); Nook's and BrowserOS's
   agent glows repaint forever (FACT `D:nook.md:335-337`, `D:browseros.md:244,274`); Ora ignores Reduce Motion (FACT).

### Proposed motion spec for rac

#### In plain English

Every animation in rac would come from one short list of times, curves, and springs. A "spring" is motion that
starts fast and settles like a real object, and it can change direction mid-way without a jerk. Here is what you
would notice. Cmd+S slides the sidebar in and out in about a quarter second, and the page edge follows it. Swiping
between spaces stays as it is today. The AI panel opens faster, in a quarter second instead of a third, and starts
moving at once. A new tab appears at once while the rows below slide down. Closing a tab fades it while its
neighbors slide up. Buttons darken the moment you press them. The agent's ring around the page stays still; it only
fades in and out. Things you do hundreds of times a day, like switching tabs with the keyboard, do not animate. With
Reduce Motion on, every slide becomes a short fade. Nothing waits for an animation to finish before taking your next
click.

#### Rules

1. **Frequency decides the budget** (Apple HIG; Emil). Hundreds of times a day: 0–100 ms, color or opacity only.
   Tens of times a day: 150–270 ms, springs for anything that moves. Rare (onboarding, first run): up to 400 ms, may
   delight.
2. **Spatial changes move; content swaps don't.** Cmd+S, edge reveal, and space switches explain where something went,
   so they move even when triggered from the keyboard (Arc and Dia do this, `A:docs/dia-spec.md:240-253,527-547`).
   Tab switches (Ctrl+Tab, Cmd+1–9, clicks), selection changes, and the new-tab command bar don't animate (Emil; Dia
   1.50 removed its NTP bar entrance, `A:docs/dia-spec.md:396-400`).
3. **Springs for movement, fixed curves for opacity and color.** No ease-in starts on entrances (Emil). Exits are
   faster than entrances.
4. **Interruptible always.** Input during an animation acts on the final layout (Dia's close: "Hover follows the final
   layout at once", `A:docs/dia-spec.md:228-229`). Springs retarget with their current velocity (WWDC23).
5. **Compositor first.** Animate layer `transform` and `opacity`. A web page is never resized per frame unless the
   frame-time check passes (see M1).
6. **No idle repaint.** Loops run only while work is visibly in progress, only while the window and tab are visible,
   stepped to about 15 updates a second (T3 Code's `steps()`), and stop under Reduce Motion.
7. **Reduce Motion means fades, not nothing** (Apple HIG; Emil): movement and scale become ≤150 ms opacity changes;
   color changes stay; overshoot goes to zero; gesture tracking may stay 1:1.
8. **No motion settings.** rac stays opinionated: no duration slider (T3 Code has one; Zen declares 156 `zen.*` prefs, `D:zen.md:282-284`). Reduce
   Motion is the only switch.

#### Tokens

One table, in one new header (`chrome/browser/ui/views/rac/motion/rac_motion.h`) and one shared CSS file for rac's
WebUI. Names are proposals.

| Token | Value | Origin |
|---|---|---|
| `kInstant` | 0 ms | selection, keyboard tab switch |
| `kHover` | 50 ms | Chromium tab hover today (`B:.../tab_view.h:64-65`) |
| `kFade` | 100 ms | Dia close fade, hover cards (`A:docs/dia-spec.md:202-203,231-232`) |
| `kList` | 140 ms | Dia row slide (`A:docs/dia-spec.md:230`) |
| `kExit` | 150 ms | Arc edge peek out (`A:docs/dia-spec.md:266-267`); Ardia peek close |
| `kPanel` | 250 ms | panels that resize the page, until springs reach them |
| `kEaseStandard` | `cubic-bezier(0.2, 0, 0, 1)` = `gfx::Tween::FAST_OUT_SLOW_IN_3` | M3 standard; Helium reveal |
| `kEaseList` | `cubic-bezier(0.2, 0, 0.2, 1)` = `gfx::Tween::FAST_OUT_SLOW_IN_2` | within 4 % of Core Animation's default (INFERENCE) |
| `kEaseFadeOut` | `cubic-bezier(0, 0, 0.58, 1)` | Dia close fade |
| `kEaseExpo` | `cubic-bezier(0.16, 1, 0.3, 1)` | Dia command bar (INFERENCE, fitted) |
| `kEaseInOut` | `cubic-bezier(0.65, 0, 0.35, 1)` (ease-in-out cubic) | Arc peek out; Ardia `easeInOutCubic` (`A:.../dockMotion.ts:10`) |
| `kSpringDock` | 0.215 s, ζ 0.79 | Dia sidebar |
| `kSpringReveal` | 0.185 s, ζ 0.77 | Arc edge peek |
| `kSpringPage` | 0.25 s, ζ 1.0 | Arc/Dia pager; rac today |
| `kSpringGrow` | 0.22 s, ζ 0.9, overshoot clamped | Ardia peek |
| `kSpringPop` / `kSpringPopOut` | 0.25 s ζ 0.75 / 0.2 s ζ 0.6 | Dia hover card show / hide |
| `kSpringMove` | 0.22 s, ζ 1.0 | rows moving between sections; Ora sidebar (0.2, 1.0) is the nearest |

#### The spec

"Today" repeats the rac inventory above. Spring timing figures are computed (INFERENCE).

| # | Interaction | rac today | Proposed | Reduce Motion | How to build it in Chromium | Sources |
|---|---|---|---|---|---|---|
| M1 | **Sidebar hide and show** (Cmd+S, sidebar button) | hide 200 ms `(0.2,0,0,1)`, page widens at once; show snaps (INFERENCE) | `kSpringDock` both ways: 90 % at ~100 ms, at rest ~270 ms, ≤ 2 % overshoot. The sidebar and the card's left edge move together; the card's right edge stays | sidebar fades 120 ms `kEaseStandard`; page width changes once | Sidebar layer translated on the compositor with rac's spring curve. Page: **Option A** resize every frame, as Arc and Dia do; **Option B** Chromium fast resize (move and clip, one real resize at the end). Ship A only if `TimeOfLongestAnimationStep` stays ≤ 8 ms at 120 Hz on a heavy page; else B | `A:docs/dia-spec.md:240-253`; Arc alternative 100 ms ease-out cubic `:270-272`; `B:ui/views/controls/native/native_view_host.h:98-104` |
| M2 | **Edge reveal** (sidebar hidden, pointer at the left edge) | 100 ms dwell, 200 ms `(0.2,0,0,1)` slide with a layout pass per frame; 300 ms leave grace; instant under RM | keep the 100 ms dwell and 300 ms grace. In: `kSpringReveal`, slide only, no fade (93 % in ~85 ms). Out: 150 ms `kEaseInOut`. Floating card inset 5–8 pt with a soft shadow | fade in 120 ms, out 100 ms, no slide | Lay the floating sidebar out once at rest; animate its layer transform on the compositor (the space pager's `SpringCurve` pattern). Retarget with current velocity if the pointer returns | `A:docs/dia-spec.md:255-267`; `R:patches/rac/sidebar-reveal/edge-reveal.patch`; [helium#1887](https://github.com/imputnet/helium/issues/1887) |
| M3 | **Space switch** (swipe, dots, Ctrl+←/→, Ctrl+1–9) | `kSpringPage` on the compositor; list header 180 ms slide 24 px; RM cross-fade 150 ms, swipe tracking off | keep `kSpringPage` and the pager physics. Add: the window tint and gradient cross-fade on the same spring progress, not after it. Keys and dots already start the same spring at zero velocity (`R:patches/rac/spaces/sliding-pages.patch:617-665`); keep that. Align the tab-list header's 180 ms slide to the page spring | keep the 150 ms cross-fade; decide whether swipes may track 1:1 (HIG allows it) | Drive the wash's opacity from the pager's progress; the wash is painted once per space and cross-faded as two layers | `R:patches/rac/spaces/sliding-pages.patch:242-262`; `Z:src/zen/spaces/ZenSpaceManager.mjs:2365-2378`; Nook complaint, [PR #395](https://github.com/nook-browser/Nook/pull/395) (CLAIM) |
| M4 | **Tab open** (Cmd+T, + row, link in new tab) | Chromium list: 200 ms quadratic in-out on bounds, new row fades in | the new row is in its slot at once, opaque, already selected. Rows below slide down one pitch in `kList` 140 ms `kEaseList`, drawn under the new row | instant | Prefer per-row layer transforms (FLIP) to bounds animation. Minimal hook: make `TabCollectionAnimatingLayoutManager`'s duration and tween settable (one small upstream edit) | `A:docs/dia-spec.md:219-224`; `B:.../tab_collection_animating_layout_manager.cc:84-104` |
| M5 | **Tab close** (Cmd+W, ✕) | same as M4 | selection moves to the neighbor at once. The closed row fades out in place, `kFade` 100 ms `kEaseFadeOut`. Rows below slide up `kList` 140 ms `kEaseList`, drawn over it. Hover follows the final layout at once. Several closes fade together | instant | as M4; keep the removed row's layer for 100 ms, inert | `A:docs/dia-spec.md:225-238` |
| M6 | **Pin and unpin** (menu, shortcut, drag), favorites | drag snap 150 ms + 100 ms hand-off; moves use the 200 ms list animation | menu or shortcut: the row moves from its old slot to its new one on `kSpringMove` (no overshoot), the section divider opens on `kList`. Drag: keep today's snap glide; the drop settles on `kSpringMove`. A trackpad haptic "alignment" tick when a drag crosses into the pinned section | instant moves; no haptics change | FLIP on layers; haptics via `NSHapticFeedbackManager` in a new `.mm` file | `R:patches/rac/pinned/snap.patch:28,40`; Zen haptics `D:zen.md:247-249` |
| M7 | **Command bar open and close** (planned) | none; Chromium's omnibox popup fades 82 ms | from the address field: the panel grows out of the field's box in 130 ms `kEaseExpo`; content isn't scaled, the growing shape uncovers it; text keeps its baseline; no scrim. Close: 80 ms opacity. As the new tab page: no entrance at all | 80 ms fade in, no grow | rac-owned view: animate a clip rect or rounded-rect bounds with a rac curve object; the result list itself doesn't move | `A:docs/dia-spec.md:358-367,396-400`; `B:chrome/browser/ui/views/omnibox/omnibox_popup_view_views.cc:216-226`; Emil (Raycast) |
| M8 | **Peek open and close** (planned) | none | grows from the clicked link's box, never from less than 0.12 of its final scale; `kSpringGrow` (90 % at ~120 ms); the card is fully opaque by 35 % of progress; the page behind dims to black 25 % on the same progress, without scaling. Close: 150 ms `kEaseStandard` back toward the link (fade if it scrolled away). Expand to a tab: 170 ms ease-out cubic | 150 ms fade in and out, no scale, no dim change beyond the fade | The peek's web contents render at their final size from the first frame; only its layer scale and translate animate | `A:apps/browser/src/components/peek/PeekOverlay.tsx:16-21,76-115`; Zen Glance `Z:src/zen/glance/ZenGlanceManager.mjs:36-40,635-646`; Emil (origin-aware, never from 0) |
| M9 | **Hover** | rows 50 ms; Chat button 150 ms; site tiles 120 ms; WebUI 120–160 ms | rows: `kHover` 50 ms in and out (keep Chromium's). Icon buttons, tiles, chips: 120 ms `kEaseStandard` both ways (unify today's 120/150/160). Tooltips and hover cards: first after 500 ms, later ones immediately with no animation; show `kFade` opacity on `(0.25,0.46,0.45,0.94)` plus `kSpringPop` scale 0.92 → 1 from the corner nearest the trigger; hide `kFade` plus `kSpringPopOut` to 0.92; row to row jumps | keep color fades; no scale | Shared helper that reads Reduce Motion each time, not at construction | `B:.../tab_view.h:64-65`; `A:docs/dia-spec.md:196-217`; Emil tooltip tip |
| M10 | **Press** | pressed paints like hovered | the pressed fill appears on mouse down, 0 ms (Dia's pressed tokens: white 31 % dark / 70 % light). Icon buttons also scale to 0.96 in 80 ms `kEaseStandard`, back in 160 ms. Text rows don't scale | color only | layer transform on the button; rows change fill only (scaling text layers can blur it, INFERENCE) | WWDC18 803; Emil (0.97); `A:docs/dia-spec.md:180-183,410-411` |
| M11 | **AI panel open and close** | Chromium side panel 350 ms `(0.45,0,0.12,1)`; edge pull follows the pointer | open `kPanel` 250 ms `kEaseStandard`; close 200 ms. Later, `kSpringDock` so both side panels share one feel. The thread never replays entrance animations when the panel opens. Edge pull: keep pointer-following | instant (Chromium already) | Short term: two one-line hooks, the default of `kSidePanelFlyoverDurationMs` and the tween in `side_panel_animations.cc`. Long term: a spring `gfx::Tween` (see Architecture) | `B:chrome/browser/ui/views/animations/side_panel_animations.cc:51-84`; `B:chrome/browser/ui/ui_features.cc:283-286` |
| M12 | **Agent ring and pill** | still ring, fades 240 / 160 ms `EASE_OUT` | keep the still ring. Fade in 200 ms `kEaseStandard`, out 150 ms. While the user takes over the tab, the ring dims to 40 % over 150 ms. Optional (off by default): one sweep along the ring when a run starts, ≤ 600 ms, once. Any progress loop is stepped (≤ 15 updates a second), runs only while a step runs and the tab is visible | instant on and off; no sweep | Ring stays a once-painted layer; only opacity animates | `R:patches/rac/agent/10-indicators.patch:95-171`; T3 Code agent cursor opacities 1 / 0.35 / 0.18 (`D:t3code.md:211-213`); avoid BrowserOS/Nook loops |
| M13 | **Confirm and plan cards** | 240 ms `(0.23,1,0.32,1)` | 200 ms `kEaseStandard`: opacity plus 4 px rise, no scale. Never auto-dismiss under the pointer | opacity only | CSS transition (retargets), not keyframes | `R:patches/rac/ai/polish-sidebar-ui.patch:1009-1012`; Emil (transitions retarget) |
| M14 | **Row expand** (agent steps, settings sections) | `grid-template-rows` 150–200 ms | 150 ms `kEaseStandard`; content fades in over the last 100 ms | instant | keep `grid-template-rows` only for short lists; otherwise clip plus transform | `R:patches/rac/agent/15-quiet-step-rows.patch:1852` |
| M15 | **Toasts** | Helium: 300 ms in, 150 ms out (M3 emphasized curves) | keep Helium's | Helium's handling | no change, no upstream edit | `D:helium.md:203-213` |
| M16 | **Loading** | Helium progress line; assistant orb and shimmer while waiting | keep; spinner turns no slower than 1.88 s per turn (Dia); all loops stop when the work stops or the window is hidden | static | n/a | `A:docs/dia-spec.md:510-516`; `R:patches/rac/ai/polish-sidebar-ui.patch:362-379` |

Accessibility beyond motion:

- **Reduce Transparency.** Read `ui::OsSettingsProvider::PrefersReducedTransparency()` and swap the behind-window
  material for the solid tint; in WebUI, gate any `backdrop-filter` on `prefers-reduced-transparency` as Zen does
  (FACT for the APIs above; INFERENCE that `NSVisualEffectView` already goes opaque by itself, not verified).
- **Increase Contrast.** Raise hairlines and the selected-row border (HIG asks for a higher-contrast scheme when the
  setting is on). Not checked in rac today.

## Architecture

### How each product builds motion

| Product | UI technology | Motion engine | Where frames are computed | Reduce Motion | Shared tokens |
|---|---|---|---|---|---|
| Chromium Views (rac's base) | C++ Views on a `ui::Compositor` | `gfx::SlideAnimation` / `LinearAnimation` (values on the UI thread, ticked on compositor frames); `ui::LayerAnimator` (transform and opacity run on the compositor thread); `views::AnimationBuilder`; `BrowserAnimationController` (declarative, logs FPS); raw `cc::KeyframeModel` curves | UI thread for anything that changes layout or paint; compositor thread for layer transform and opacity | `PrefersReducedMotion()`, `RichAnimationDuration()`, force flags | Material-named `gfx::Tween` enum only (FACT, Chromium section above) |
| rac | Views patches + WebUI pages (HTML, CSS, TypeScript) | all of the above, plus its own compositor spring curve for spaces; CSS transitions, keyframes and WAAPI in WebUI | mixed: pager and fades on the compositor; edge reveal, Cmd+S, side panel and tab list via layout | everywhere found | none for motion; 25 color ids (FACT) |
| Helium | Views patches | `SlideAnimation` for frameless reveal; Chromium elsewhere | UI thread, layout per frame (`B:.../browser_view.cc:6956-6976`) | via `RichAnimationDuration` | none |
| Zen | Gecko chrome in HTML, CSS, JS | Motion v13.2.0 (lazy), Web Animations, CSS `linear()` springs | content process compositor for CSS/WAAPI; main thread for Motion's JS values | partial (`gReduceMotion` in some paths; 87-vote request for a global switch) | prefs, not tokens (FACT `D:zen.md:194-234`) |
| Dia / Arc | AppKit (Dia: AppKit only on Mac) | Core Animation (`CASpringAnimation`, `CABasicAnimation`, keyframes sampled at 240 Hz), Metal shaders | render server | Dia reads only Reduce Motion (CLAIM-quality `D:closed-ai-browsers.md:326-328`) | asset-catalog color tokens |
| Ardia | React Native macOS shell + native ArdiaCore (Obj-C++) around Chromium | RN `Animated` (94 native-driver, 22 JS-thread animations), Core Animation in native code, Metal | mostly native driver | per surface | constants per file (FACT `D:ardia.md:190-192`) |
| Nook | SwiftUI + AppKit | SwiftUI animations; `NSAnimationContext` | render server | one place | `NookDesign.Motion`, 5 tokens, 38 literals leak (FACT `D:nook.md:248-251`) |
| Ora | SwiftUI + AppKit | SwiftUI springs; `NSPageController` | render server | none | none |
| T3 Code | React + Base UI + Tailwind in Electron | CSS transitions, `@starting-style`, WAAPI; no motion library; an IntersectionObserver pauses loops off screen | Chromium compositor | everywhere checked | CSS custom properties (`--ease-drawer`) and Tailwind defaults |

What this means for rac (INFERENCE): rac's chrome is Chromium Views, so SwiftUI and RN techniques don't transfer;
Core Animation's model does, because Chromium's compositor offers the same split (layer properties on another thread,
layout on the main one). Every motion in the spec fits one of three Chromium mechanisms:

1. **Compositor layer animation** (transform, opacity): pager, edge reveal, peek, press scale, list slides, ring and
   card fades. Runs smoothly even when the UI thread is busy.
2. **Layout animation** (bounds change per frame): Cmd+S dock and the AI side panel, because the page must change
   width. Costly; measure it.
3. **WebUI CSS** for the assistant, onboarding and settings: transitions on `transform` and `opacity` run on the
   renderer's compositor.

### Proposed motion system for rac

Small, mostly new files, in line with "prefer new files and small hooks" (`R:AGENTS.md`).

1. **`chrome/browser/ui/views/rac/motion/rac_motion.{h,cc}`** (new). The token table above. A `rac::Spring
   {response, damping_ratio}` with closed forms for ζ < 1, = 1 and > 1, `ValueAt`, `VelocityAt`, and `SettleTime`
   (keep today's 240 Hz rest search and its 0.25 DIP / 15 DIP/s rest thresholds). It generalizes
   `SpacePager::Spring`, which only handles ζ = 1 (`R:patches/rac/spaces/sliding-pages.patch:505-529`).
2. **Compositor elements** (new, moved out of `sliding-pages.patch`): `SpringTransformElement`,
   `SpringOpacityElement`, and a `CurveElement` that takes any `gfx::CubicBezier`. Today's `SpringCurve` /
   `SpringElement` pair is the template (`:303-422`). Chromium already has `gfx::LinearTimingFunction`, the C++ form
   of CSS `linear()` (`B:ui/gfx/animation/keyframe/timing_function.h:130-170`), so one sampled spring can feed both
   the compositor and CSS.
3. **One Reduce Motion helper** that is read on every animation start, never cached in a constructor. It returns a
   fade or zero per token.
4. **WebUI tokens** (new `rac_motion.css`, shared by `rac_ai`, onboarding and settings): `--rac-dur-*`,
   `--rac-ease-*`, `--rac-spring-*` as `linear(...)` strings generated from the same table by a small dev script.
   Zen ships springs to CSS the same way (`Z:src/zen/compact-mode/sidebar.inc.css:172-276`).
5. **Optional upstream hook.** Two small hunks in `ui/gfx/animation/tween.{h,cc}` could add rac's springs as fixed
   `gfx::Tween` types. That would let `SlideAnimation` users and `BrowserAnimationController` (side panel, vertical
   tab strip) use the same springs without forking them. Cost: two upstream hunks that conflict only if Chromium edits
   the enum's tail. Alternative: a rac `BrowserAnimationProvider` that approximates a spring with 8–12 linear
   keyframes, no `tween.cc` edit.
6. **Measurement.** Give rac's layout-driven motions histogram names so `BrowserAnimationController` records
   `.AnimationFPS` and `.TimeOfLongestAnimationStep` locally (`B:chrome/browser/ui/animation/README.md:749-800`).

Code size today: motion code is spread over about 15 rac files; the pager alone is the largest piece (the
`sliding-pages.patch` spring, curve and element code is about 120 lines of C++) (INFERENCE from the patch).

## Data and storage

- **No motion data is stored.** rac has no motion preferences, by design ("Opinionated", `R:VISION.md`). T3 Code
  stores a panel-animation duration (0–400 ms, default 0) (FACT `T:packages/contracts/src/settings.ts:113-122`); Zen
  keeps durations as prefs such as `zen.workspaces.switch-animation-duration` = 250 and `zen.glance.animation-duration`
  (FACT `Z:prefs/zen/workspaces.yaml:26-27`; `Z:src/zen/glance/ZenGlanceManager.mjs:42-44`).
- **Inputs come from macOS.** Reduce Motion from `NSWorkspace.accessibilityDisplayShouldReduceMotion`, Reduce
  Transparency from `accessibilityDisplayShouldReduceTransparency` (FACT, Chromium section). Neither is stored.
- **Animation histograms stay on the machine.** `BrowserAnimationController` records FPS histograms in memory; they
  appear at `chrome://histograms`. Helium is built from ungoogled-chromium, which removes metrics reporting, so nothing
  is uploaded (INFERENCE; not traced for these histograms). Nothing about motion leaves the machine.

## Agents and AI

Motion matters most where the agent acts, because it signals "something other than you is driving this tab".

| Surface | rac today | Others | Proposal |
|---|---|---|---|
| Tab ring | still 2 px ring + 12 px inner glow, painted once; fades 240 / 160 ms; space-colored (FACT `R:patches/rac/agent/10-indicators.patch:95-260`) | BrowserOS: orange inset glow pulsing every 3 s forever; Nook: three blurred angular gradients rotating forever; Chrome with Gemini: the tab glows (FACT `D:browseros.md:244,274`; `D:nook.md:304,335-337`; `D:closed-ai-browsers.md:399`) | keep still (M12). The ring is a state, not a progress bar |
| Working pill and orb | static orb, text "Working…", Stop/Resume (FACT `R:patches/rac/agent/10-indicators.patch:103-126,277-523`) | T3 Code: text shine stepped at ~14 fps, paused off screen (FACT `T:apps/web/src/index.css:528-553`; `T:apps/web/src/lib/visibleAnimation.ts:10-62`) | if the orb animates at all, stepped, only while a step runs |
| Step rows | quiet rows; chevron 150 ms; spinner 0.8 s while a step runs (FACT) | T3 Code: one plain summary row that expands | keep; spinner only on the live step |
| Confirm cards | 240 ms ease-out-quint (FACT) | Aside: expo-out 0.3 s with a bouncy scale spring (~6 % overshoot, INFERENCE from 185/18/1) | 200 ms, no scale, no bounce (M13). A consent card should feel steady |
| Agent cursor or click marker | none | T3 Code: cursor moves 150 ms ease-out; opacity 1 acting, 0.35 idle, 0.18 under human control (FACT `D:t3code.md:211-213`) | option: a 300 ms ring at each agent click, static dot under Reduce Motion. Helps trust; costs one layer |
| Take-over | "Paused while you use this tab" pill (FACT) | T3 Code: explicit Take control / Release control | dim the ring to 40 % while paused (M12) |

AI-off cost: every agent animation lives behind the agent's own views, which are not created when AI is off, so the
motion system adds nothing to an AI-off profile (INFERENCE; matches `R:docs/internals/ai.md` "AI off costs nothing").

## Build, release, and engineering

- **How rac can test motion today.** The dev screenshot harness can synthesize trackpad swipes at 120 Hz (`swipe X Y DX
  N`) and capture bursts of frames (`burst DIR N MS`, e.g. 30 frames 8 ms apart) (FACT
  `R:patches/rac/dev/window-screenshot-swipe.patch:46,56-72`). That is enough to trace a curve frame by frame, the way
  Ardia traced Dia, and to stitch frames into a short video for PRs (INFERENCE). Launch with
  `--force-prefers-reduced-motion` to record the Reduce Motion path without touching the shared Mac's settings
  (FACT `B:ui/gfx/animation/animation.cc:146-159`).
- **Fit, don't eyeball.** Ardia keeps traced points next to its springs in a test (`dockMotion.test.mjs`, FACT
  `A:docs/dia-spec.md:274`). rac could add a unit test per spring token asserting 90 % time, overshoot, and rest
  time, so a retune is always deliberate. These are pure-math tests, cheap to run even before CI runs the rest
  (INFERENCE; CI runs no unit tests today per the maintainer brief).
- **Frame budget.** At 120 Hz a frame is 8.3 ms. Gate layout-driven motion (M1, M11) on
  `TimeOfLongestAnimationStep` ≤ 8 ms on a heavy page, read from `chrome://histograms` in the planned perf bench
  (INFERENCE). Ardia measured its own UI with an injected frame rig (display-link ticks, main-thread busy time)
  (FACT `A:docs/perf/README.md`, `acframes.m` row).
- **120 Hz.** Chromium's `ThrottleMainFrameTo60Hz` is off on desktop by default (FACT `B:cc/base/features.cc:178-185`),
  so renderer main frames are not capped at 60 Hz; Ardia turns it on for power and then patches around it (FACT
  `A:docs/engine-build.md:70-71`). rac should leave it off unless the perf bench says otherwise (INFERENCE).
- **Upstream tracking.** Helium touches motion rarely. Since 0.18.2.1 the relevant change is a fix for the frameless
  sidebar "bouncing at the window edge" (FACT `H:` commit 899e8eb, 2026-10-18). Its zen-mode reveal code is what M2
  replaces, so the first Helium sync should land before M2 is built (INFERENCE).

## Strengths and weaknesses (critical)

Strengths of rac's motion today:

- The space pager is real physics on the compositor with Arc's constants and Apple's rubber band. Few Chromium forks
  have anything like it (FACT for rac; INFERENCE for "few").
- Reduce Motion is handled everywhere I found, and the agent and assistant never loop while idle (FACT).
- Color tokens already match Dia's measured values, so the look is close to Dia before any motion work (FACT
  `B:chrome/browser/ui/color/rac_color_mixer.cc:33-63` vs `A:docs/dia-spec.md:407-429`).

Weaknesses:

- No motion tokens; 22 CSS durations and two different `--ease-out` definitions in the same WebUI (FACT).
- The three most-used panel motions are the weakest: Cmd+S show (snap), edge reveal (layout per frame), AI panel
  (350 ms slow start) (FACT for values, INFERENCE for feel).
- No press state, no hover cards, and the tab list uses Chromium's generic 200 ms in-out (FACT).
- Two layouts (top bar and sidebar address bar) double the surfaces each motion must be checked on (INFERENCE,
  `D:rac-baseline.md:239`).
- rac copies values from The Browser Company's asset catalogs and binaries (comments say so,
  `B:chrome/browser/ui/color/rac_color_mixer.cc:33,53`). Numbers are facts, but publishing a "design system" that
  cites another company's catalogs deserves a look first (INFERENCE).

Weaknesses of the evidence:

- Dia and Arc numbers come from one developer's binary reading and recordings (CLAIM). Their stated overshoots
  disagree with their own fitted springs (INFERENCE, computed above).
- No Arc numbers exist for the command bar, Peek, Little Arc, or tab open/close.
- Apple gives principles but no durations; Emil's advice is opinion, if widely followed.
- I did not run rac. The Cmd+S "show snaps" finding is read from code only.

## What rac should take (ranked, concrete, with rough cost) and what rac should avoid

Costs assume one agent-driven worktree: **XS** under a day, **S** 1–3 days, **M** about a week, **L** two weeks or
more. Each includes building, burst-frame proof, and a Reduce Motion pass.

### Take

1. **A motion token file and one spring primitive** (`rac_motion.h`, `rac::Spring` with any damping ratio,
   compositor spring and curve elements, a Reduce Motion helper, shared WebUI CSS tokens). Everything else builds on
   it, and it replaces 22 scattered durations. Cost **S–M**. Source: the pager's existing spring
   (`R:patches/rac/spaces/sliding-pages.patch:303-529`); Nook's token file as a cautionary model (38 literals leaked,
   `D:nook.md:248-251`), so add a lint or review check.
2. **Make the AI panel quick** (M11): 250 ms `(0.2, 0, 0, 1)` open, 200 ms close. Two one-line upstream hooks. The
   panel is opened often (INFERENCE), and today it barely moves for its first 90 ms. Cost **XS**.
3. **Edge reveal on the compositor with Arc's spring** (M2). Arc users lean on the edge reveal (INFERENCE); Helium's
   layout-per-frame slide has a frame-drop report. Cost **M** (touches Helium's zen-mode code, so do it after the
   first Helium sync).
4. **Cmd+S slides both ways on Dia's spring** (M1), shipped only behind the frame-time gate, with Chromium's fast
   resize as the fallback. Cost **M–L**.
5. **Dia's tab open and close choreography** (M4, M5): new row in place at once, neighbors slide 140 ms, closed row
   fades 100 ms, hover follows the final layout. Cost **S–M**.
6. **Press states and unified hovers** (M9, M10): pressed fill on mouse down, 0.96 scale on icon buttons, 120 ms
   hovers everywhere outside rows. Cost **S**.
7. **Space wash cross-fade on the page spring** (M3), so color changes with the slide, not after it. Cost **S**.
8. **A motion test recipe** in the docs: burst capture, synthesized swipes, `--force-prefers-reduced-motion`, spring
   unit tests, and the `TimeOfLongestAnimationStep` gate. Cost **S**. It turns "feels right" into a reviewable PR
   artifact, which the maintainer asked for.
9. **Reduce Transparency and Increase Contrast** handling. Cost **S**.
10. **Command bar and Peek motion as specified** (M7, M8) when those features are built: grow from the field in
    130 ms expo-out; peek from the link on a 0.22 s / ζ 0.9 spring. Cost included in each feature.
11. **Trackpad haptics** on pin and favorites snaps (M6). Cost **XS–S**.
12. **Hover cards with Dia's choreography** (M9), if rac wants tab hover cards at all. Cost **M**.

### Avoid

- **Loops that run while nothing is happening:** BrowserOS's forever-pulsing glow, Nook's rotating tool glow
  (`D:browseros.md:244,274`; `D:nook.md:335-337`). They break "nothing repaints continuously".
- **Growing from nothing:** Nook's peek starts at scale 0.001 (`D:nook.md:297`). Start at a real rect or ≥ 0.9 scale.
- **Slow starts and long durations on frequent surfaces:** Chromium's side panel (350 ms, slow start); Zen's 350 ms
  Glance is the upper bound for a rare surface.
- **Motion settings.** T3 Code's 0–400 ms slider and Zen's prefs grow the settings surface; rac's vision says no.
- **Private macOS APIs for looks.** Ardia uses private material 29 and `CAFilter` by class name
  (`D:ardia.md:138`), which can break on any macOS update (INFERENCE).
- **Chasing Liquid Glass.** Nook added it and removed it within two weeks as not "calm" (`D:nook.md:264-281`); the HIG
  says use it "sparingly", in the controls layer only.
- **Resizing the web page every frame without measuring it.** Chrome's side panel does it for 350 ms; Dia does it for
  its sidebar. In rac it must pass the frame-time gate first.
- **Keyframe animations for state that can flip** (hover, open/close). Use transitions or springs that retarget.
- **Bounce on consent and safety UI.** Aside's approval card overshoots about 6 % (INFERENCE from its spring). A
  confirmation should feel steady.
- **Animating keyboard-driven content swaps** (Ctrl+Tab, Cmd+1–9, the new-tab command bar).
- **Copying The Browser Company's artwork or shaders.** Values and timings are facts; images, paintings and Metal
  shaders rebuilt from a disassembled binary are another matter (Ardia's power-up band, `D:ardia.md:150`)
  (INFERENCE; not legal advice).

## Open questions and things you could not verify

Decisions for the maintainer:

1. **Dock damping.** Dia's ζ 0.79 (a 1–3 pt overshoot) or Apple's rule of no overshoot for taps and keys (ζ 1.0)?
   Both settle in about 0.27 s.
2. **Page resizing during Cmd+S.** Per-frame resize (what Arc and Dia do) or move-and-clip with one resize at the
   end? Decide after a measurement on a heavy page at 120 Hz.
3. **Edge reveal dwell.** Keep 100 ms, shorten it, or replace it with a pointer-speed check? Apple warns that every
   timer adds latency; Zen's most-reacted sidebar complaints are about it closing early, not opening late.
4. **Reduce Motion and swipes.** rac turns swipe tracking off; the HIG lists "tracking animations directly with
   people's gestures" as a good Reduce Motion practice. Allow 1:1 tracking with a fade on commit?
5. **Flick threshold.** rac turns the page at 300 DIP/s; Dia's record says 5 pt/s (`A:docs/dia-spec.md:535-537`). Is
   rac's swipe harder to flick than Arc's?
6. **Keyboard rule.** Emil says never animate keyboard actions; Arc and Dia animate Cmd+S and space keys. The spec
   sides with Arc and Dia for spatial changes only. Agree?
7. **Upstream hook.** Add rac springs to `gfx::Tween` (two hunks, reach everywhere) or approximate them with keyframes
   in a rac animation provider (no upstream edit)?
8. **One layout or two.** Top bar and sidebar address bar double every motion check. Keep both?
9. **macOS 26 look.** Match Helium's 17 px window corner with an 11 px concentric card radius? Adopt any Liquid Glass?
10. **Agent extras.** A click marker at each agent click? A one-time sweep when a run starts?
11. **Hover cards.** Does rac want Dia-style tab hover cards?

Not verified:

- I did not run rac. "Cmd+S show snaps" and "hide slides" come from reading `browser_view.cc` and the layout code.
- The main checkout's build tree is from 2026-10-22, older than `main`; WebUI values here come from the patches, not
  from a build.
- Whether `NSVisualEffectView` already turns opaque under Reduce Transparency inside Chromium's window.
- Whether `BrowserAnimationController` histograms are recorded in a Helium build with metrics removed.
- The frame cost of a per-frame layout of rac's sidebar and page at 120 Hz.
- Dia 1.50's "tab row background change fades 0.3 s easeOut": which change it covers (`A:docs/dia-spec.md:517`).
- Arc's motion for the command bar, Peek, Little Arc, and tab open and close: no public data.
- Every Dia and Arc number rests on one developer's recordings and binary reading (CLAIM).

## Sources

Primary, local (read-only):

- rac patches: `R:patches/rac/spaces/sliding-pages.patch`, `sidebar-motion.patch`, `switcher.patch`;
  `R:patches/rac/sidebar-reveal/edge-reveal.patch`; `R:patches/rac/pinned/snap.patch`, `motion.patch`;
  `R:patches/rac/agent/10-indicators.patch`, `09-confirm-ui.patch`, `15-quiet-step-rows.patch`, `16-error-rows.patch`;
  `R:patches/rac/ai/03-side-panel-chat.patch`, `09-dia-chat-panel.patch`, `10-dia-chat-thread.patch`,
  `13-chat-edge-pull.patch`, `17-find-ask.patch`, `18-ntp-auto-pick.patch`, `19-link-summary.patch`,
  `polish-sidebar-ui.patch`; `R:patches/rac/onboarding/*.patch`; `R:patches/rac/look/tokens.patch`, `dia-chrome.patch`;
  `R:patches/rac/dev/window-screenshot-swipe.patch`; `R:docs/internals/pinned-tabs-drag.md`; `R:VISION.md`; `R:AGENTS.md`.
- Chromium and Helium in the built tree: `B:ui/gfx/animation/{tween.cc,slide_animation.{h,cc},animation.cc,animation_mac.mm,linear_animation.cc}`;
  `B:ui/gfx/animation/keyframe/timing_function.h`; `B:ui/compositor/layer_animator.cc`;
  `B:ui/views/animation/{bounds_animator.h,ink_drop_impl.cc,animation_delegate_views.cc}`;
  `B:ui/views/controls/{button/button.cc,button/toggle_button.cc,native/native_view_host.h}`;
  `B:chrome/browser/ui/animation/{README.md,browser_animation_controller.h}`;
  `B:chrome/browser/ui/views/animations/{side_panel_animations.cc,tab_strip_animations.cc}`; `B:chrome/browser/ui/ui_features.cc`;
  `B:chrome/browser/ui/views/frame/{browser_view.cc,layout/browser_view_tabbed_layout_impl.cc}`;
  `B:chrome/browser/ui/views/tabs/{common/tab_collection_animating_layout_manager.cc,common/tab_view.{h,cc},tab/glow_hover_controller.cc,hovercard/tab_hover_card_controller.cc}`;
  `B:chrome/browser/ui/views/omnibox/omnibox_popup_view_views.cc`; `B:chrome/browser/ui/color/rac_color_mixer.cc`;
  `B:chrome/browser/ui/views/rac/rac_look.{h,cc}`; `B:ui/native_theme/os_settings_provider_mac.mm`;
  `B:third_party/blink/renderer/core/css/{media_feature_names.json5,css_properties.json5}`; `B:cc/base/features.cc`.
- Helium core: `H:patches/helium/ui/native-frame-materials.patch`, `disable-ink-ripple-effect.patch`; commits 899e8eb, f85e84a.
- Zen: `Z:src/zen/spaces/ZenSpaceManager.mjs`, `Z:src/zen/compact-mode/sidebar.inc.css`,
  `Z:src/zen/common/modules/ZenVerticalTabsManager.mjs`, `Z:src/zen/glance/ZenGlanceManager.mjs`,
  `Z:src/zen/common/styles/zen-omnibox.css`, `Z:src/zen/drag-and-drop/nsZenDropLandingCocoa.mm`, `Z:prefs/zen/workspaces.yaml`.
- Ardia and its Dia record: `A:docs/dia-spec.md`, `A:apps/browser/src/components/layout/dockMotion.ts`,
  `A:apps/browser/src/components/peek/PeekOverlay.tsx`, `A:apps/browser/src/components/glass.tsx`,
  `A:docs/engine-build.md`, `A:docs/perf/README.md`.
- Nook: `N:Packages/NookDesign/Sources/NookDesign/NookDesign.swift`. Ora: `O:ora/Features/Sidebar/State/SidebarManager.swift`,
  `O:ora/Features/Sidebar/Views/TabList/NormalTabsList.swift`, `O:ora/Features/Sidebar/Views/SidebarView.swift`.
- T3 Code: `T:apps/web/src/index.css`, `T:apps/web/src/components/Sidebar.motion.ts`, `T:apps/web/src/panelAnimations.ts`,
  `T:apps/web/src/components/ui/{dialog-styles.ts,popover.tsx}`, `T:packages/contracts/src/settings.ts`.
- Apple SDK: `SDK:` SwiftUICore `.swiftinterface`, lines 3880-3899, 16765-16825.
- Sibling dossiers: `R:plans/research/{zen,ardia,nook,ora,t3code,helium,rac-baseline,aside,browseros,closed-ai-browsers}.md`.
- My arithmetic: `/tmp/rac-overhaul/scratch/motion_math.py` (spring metrics) and `curves.py` (curve comparisons),
  outside the repo.

Web:

- Apple HIG, Motion: https://developer.apple.com/design/human-interface-guidelines/motion
- Apple HIG, Accessibility: https://developer.apple.com/design/human-interface-guidelines/accessibility
- Apple HIG, Materials: https://developer.apple.com/design/human-interface-guidelines/materials
- WWDC18, Designing Fluid Interfaces: https://developer.apple.com/videos/play/wwdc2018/803/
- WWDC23, Animate with springs: https://developer.apple.com/videos/play/wwdc2023/10158/
- Core Animation default timing function: https://developer.apple.com/documentation/quartzcore/camediatimingfunctionname/default
- Emil Kowalski, You don't need animations: https://emilkowal.ski/ui/you-dont-need-animations
- Emil Kowalski, 7 practical animation tips: https://emilkowal.ski/ui/7-practical-animation-tips
- Emil Kowalski, Great animations: https://emilkowal.ski/ui/great-animations
- animations.dev course outline: https://animations.dev/
- The Browser Company, The strategy behind Dia's design: https://browsercompany.substack.com/p/the-strategy-behind-dias-design
- Michael Tsai, Arc and Dia (quotes the AppKit-only letter): https://mjtsai.com/blog/2025/05/30/arc-and-dia/
- Nate Parrott, Arc and the Browser Company: https://nateparrott.com/arc/index.html
- Material 3 easing and duration tokens: https://m3.material.io/styles/motion/easing-and-duration/tokens-specs
- Helium issue #1887 (frameless slide frame drops): https://github.com/imputnet/helium/issues/1887
- Helium issue #1971 (Cmd+S in frameless mode): https://github.com/imputnet/helium/issues/1971
- Zen issue #6302 (rounded corners and scrolling): https://github.com/zen-browser/desktop/issues/6302
- Nook PR #395 (space switch polish): https://github.com/nook-browser/Nook/pull/395
- GitHub API repo metadata (stars, dates, licenses), queried 2026-10-25 with `gh api repos/<owner>/<repo>`.
