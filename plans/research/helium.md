# Helium: research dossier

Researched 2026-10-25. Subject: [imputnet/helium](https://github.com/imputnet/helium)
(core, at `f29a259`, Chromium 156.0.8078.47) and
[imputnet/helium-macos](https://github.com/imputnet/helium-macos) (tag
`0.20.1.1`, commit `9aa975a`). rac is on helium-macos `0.18.2.1` (`992a020`),
Helium core `76141e1`, Chromium 154.0.8037.92.

Citation shorthand: **H:** = imputnet/helium at `f29a259`; **HM:** =
imputnet/helium-macos at `9aa975a`; **HS:** = imputnet/helium-services at
`110144e`; **R:** = this rac worktree at `cfdcf83`. Line numbers refer to those
commits. Local read-only clones are in `/tmp/rac-overhaul/src/`. Tags: FACT =
primary source (code, API, official docs). CLAIM = vendor or self-report.
INFERENCE = my reasoning.

## In plain English

Helium is the browser rac is built on. Two people make it. It is Chrome with
Google taken out, an ad blocker built in, and a calmer look. Nothing goes out
until you agree on the first screen. After that, Helium's servers fetch
extensions, filter lists, spell check files, and !bangs for you without
knowing who you are. Helium has vertical tabs, a "frameless" mode that hides
everything, split view, and custom shortcuts. It has no AI, no spaces, no sync
yet, and no Netflix-style video protection. Chrome now ships a new version
every two weeks. Helium follows within two to four days. rac has not synced
for six releases. My test shows 121 of rac's 180 patches still apply to the
newest Helium. The other 59 need hand fixes, mostly in sidebar and settings
code that Helium just rewrote.

## Snapshot

| Field | Value |
| --- | --- |
| What it is | "Private, fast, and honest web browser" (repo description). A de-Googled Chromium with built-in uBlock Origin, consent-gated "Helium services", and its own UI layouts. Officially "in beta" (H: `README.md` L13-15). FACT |
| Engine | Chromium 156.0.8078.47 in 0.20.1.1 (H: `chromium_version.txt`). Patch stack derived from ungoogled-chromium. FACT |
| Version scheme | `0.<Chromium major - 136>.<core revision>.<platform revision>`, so 0.20 = Chromium 156 (H: `utils/helium_version.py` L14, L50-62). FACT |
| Platforms | macOS arm64 and x86_64, Windows, Linux. Mobile "Not yet" (helium.computer). The tarball builder already prepares `android` and `ios` overlays ([chromium-tarballs README](https://github.com/imputnet/chromium-tarballs)); onboarding has `platform.is.android` branches (helium-onboarding `src/lib/onboarding-flow.ts`). Mobile plans: INFERENCE |
| License | Browser GPL-3.0; services AGPL-3.0 (HS: `README.md`); code imported from ungoogled-chromium stays BSD-3-Clause (H: `README.md` "License"). FACT |
| Repos | `helium` (core patches, tooling, i18n), `helium-macos`, `helium-linux`, `helium-windows`, `helium-services`, `helium-onboarding` (Svelte), `helium-prism` (Svelte UI kit), `chromium-tarballs`, `uBlock` (fork), `helium-filters`, `helium-legal`, `helium-nonfree-assets`, `helium-pdfjs` (WIP) (`gh api orgs/imputnet/repos`). FACT |
| Stars (2026-10-25) | helium 21,983; helium-windows 1,462; helium-macos 1,172; helium-linux 1,092; helium-services 94 (`gh api`). FACT |
| Age | `helium` and `helium-macos` created 2025-02-15; `helium-services` 2025-03-02; `helium-windows` 2025-08-07; `helium-linux` 2025-08-23 (`gh api repos/imputnet/<repo>`). First macOS release 0.0.1.1 on 2025-05-04 (`gh api .../releases`). About 17.7 months of releases. FACT |
| Release cadence | 134 macOS releases since 2025-05-04. 25 in the 90 days from 2026-07-27 to 2026-10-25, about 2 a week. Since Chrome moved to a two-week cycle (Chrome 153, 2026-09-08), Helium shipped each new major 2 to 4 days after Chrome stable: 153 to 0.17.0.1 (Sep 12), 154 to 0.18.1.1 (Sep 24), 155 to 0.19.2.1 (Oct 9), 156 to 0.20.1.1 (Oct 22). FACT (release API; Chrome dates from [developer.chrome.com](https://developer.chrome.com/blog/chrome-two-week-release) and [secondary reports](https://browserhow.com/chrome-156-stable-update-windows-mac-linux/)) |
| Team size | Two maintainers: `wukko` and `jj` (`dumbmoron`). The org bio says "two guys behind helium, cobalt, and meow.camera" (`gh api orgs/imputnet`); the sponsor page says "maintained by two people". Of all 169 PRs merged into `helium` since 2026-07-25, 166 were by those two (`dumbmoron` 98, `wukko` 68; `gh api search/issues`). Chromium bumps come from ungoogled-chromium's Blaise (GitHub `Ahrotahn`, e.g. commit `ffeb45a2`). FACT |
| Business model | User tips only: Stripe one-time, Liberapay recurring; "no browser ads, paid allowlists, or pay-to-remove-bloat tiers" and "We don't require any form of payment to get the full experience" ([helium.computer/sponsor](https://helium.computer/sponsor)). CI runners sponsored by Depot (HM: `README.md` L17-21). A "Helium Partner" badge exists in onboarding ("Paying for this service will support the development of Helium") but no service sets `partner: true` in onboarding 202610161403 (`src/lib/password-managers.ts` L7). FACT |

## Features

Status key: **shipped** (on in 0.20.1.1), **opt-in** (shipped, off by
default or in settings), **flag** (behind `chrome://flags` or a disabled
feature), **planned** (code in progress or open request), **absent**.

### Tabs, sidebar, spaces

| Feature | Status | Evidence |
| --- | --- | --- |
| Four layouts: Classic, Compact, Vertical, Dynamic | shipped | `HeliumLayoutType` enum kClassic/kCompact=1/kVertical=2/kDynamic=3 (H: `patches/helium/ui/layout/core.patch` L288-293). FACT |
| Vertical tabs on Chromium's native vertical tab strip | shipped | Helium rewires Chromium's `vertical_tabs.enabled` into its layout pref (core.patch L7-60). FACT |
| Tabs on the right side | opt-in | `helium.browser.vertical_right_aligned`; string "Show vertical tabs on right side" (H: `i18n/source.gen.json` entry 182). FACT |
| Cmd+S collapses or expands the vertical tab strip | shipped | `IDC_CTRL_S_SHORTCUT` bound to `kVK_ANSI_S` (H: `patches/helium/ui/layout/shortcuts.patch` L131). Only in the Vertical layout and only while `helium.settings.behavior.vertical_collapse_shortcut` is on (default true); otherwise Cmd+S still saves the page (same file L21, L50-54, L74-88). FACT |
| Collapse to icons, expand on hover | opt-in | Expand on hover came back in 0.20.1.1, off by default, and now works with frameless mode (H commit `48e91cb`). FACT |
| Frameless mode ("zen mode" in code) with pin sidebar / pin top bar | opt-in | Prefs `helium.browser.zen_mode`, `..._sidebar_pinned`, `..._top_chrome_pinned` (H: `i18n/source.gen.json` 201-204). FACT |
| MRU Ctrl+Tab cycling | opt-in | `helium.browser.mru_tab_cycling` (H: `patches/helium/core/tab-cycling-mru.patch`). FACT |
| New tab next to active tab | opt-in | `open-new-tabs-next-to-active-tab-option.patch`. FACT |
| Tab context menu: close tabs to left, copy URL, hibernate, mute (new in 0.18.3.1) | shipped | `close-tabs-to-left.patch`, `copy-url-tab-context-menu.patch`, `hibernate-tab-context-menu.patch`, `mute-tab-context-menu.patch` (H commit `b0e3abb`). FACT |
| Tab hover cards | shipped | `enable-tab-hover-cards.patch`. FACT |
| Tab groups, pinned tabs (Chromium's) | shipped | Chromium features kept. rac calls these pinned tabs "favorites". FACT |
| Spaces / workspaces | absent | Open requests [#1351](https://github.com/imputnet/helium/issues/1351) (58 reactions), [#215](https://github.com/imputnet/helium/issues/215), [#245](https://github.com/imputnet/helium/issues/245); [#2579](https://github.com/imputnet/helium/issues/2579) closed. No maintainer statement found. FACT |
| Address bar in the sidebar | absent | Community PR [#2367](https://github.com/imputnet/helium/issues/2367), opened 2026-08-22. One maintainer comment that day asked how it interacts with the omnibox; no maintainer review. Its author closed it unmerged on 2026-10-09, about seven weeks later. FACT |

### Navigation and command bar

| Feature | Status | Evidence |
| --- | --- | --- |
| !bangs, parsed locally from a downloaded list | shipped (needs services) | `add-native-bangs.patch`, `bangs-ui.patch`. List is Kagi's bangs plus extras; 10,730 entries with 13,421 triggers in HS: `svc/bangs/bangs.json` (my count). The site's "13,000+" matches the trigger count. FACT |
| Minimal location bar (host only), centered address bar | opt-in | `minimal-location-bar.patch`, `centered-address-bar.patch`. FACT |
| Loading progress line in the location bar | opt-in | `helium.browser.show_progress_bar` (`progress-bar.patch`). FACT |
| Cleaned omnibox suggestions, default search icon | shipped | `clean-omnibox-suggestions.patch`, `search/*`. FACT |
| Tab search button in toolbar | shipped | `tab-search-in-toolbar.patch`. FACT |
| Custom keyboard shortcuts page | shipped | `custom-keyboard-shortcuts.patch`, settings page, `browser_shortcuts` service. FACT |
| Command palette | absent | Open request [#317](https://github.com/imputnet/helium/issues/317), 62 reactions. FACT |

### Split view, peek, small windows

| Feature | Status | Evidence |
| --- | --- | --- |
| Split view (Chromium's, restyled) | shipped | `split-view.patch`, `multi-contents-view.patch`, `multi-contents-drop-target.patch`. FACT |
| New split tab: Cmd+Opt+N | shipped | `keyboard-shortcuts.patch` L184. FACT |
| Alt-click to split, bigger drop targets | absent | Community PR [#2776](https://github.com/imputnet/helium/issues/2776), opened 2026-10-23, closed unmerged by `dumbmoron` on 2026-10-24 without a comment. FACT |
| Peek, Little Arc-style mini windows | absent | No code found. FACT (absence in `patches/series`) |
| PWA installs with a Helium toolbar | shipped | `pwa-toolbar.patch`. FACT |

### Import, sync, profiles

| Feature | Status | Evidence |
| --- | --- | --- |
| Import from Chrome, Brave, Edge, Vivaldi, Opera, Yandex, Whale, Dia, Perplexity Comet | shipped | Brave-derived importers (H: `patches/brave/chrome-importer-files.patch` L456-524). FACT |
| Import from Arc, including the sidebar | shipped | `ArcSidebarImporter` reads `StorableSidebar.json`. Top Apps become bookmark-bar entries. Each space's pinned tabs become bookmarks, inside a folder named by the space's internal ID ("Personal" for the default) when there is more than one space (H: `patches/helium/core/add-arc-importer.patch` L166-206, L288-330). Not imported as tabs or spaces. FACT |
| Import from Zen (Firefox-based) | shipped | `add-zen-importer.patch`. FACT |
| Import extensions | shipped | `EXTENSIONS = 1 << 7` importer item (H: `patches/brave/custom-importer.patch` L195). FACT |
| Password and autofill import | absent (removed) | Stripped for every source (H: `patches/helium/core/disable-unsupported-importers.patch`). FACT |
| macOS 27 permission prompt for importing from "protected" browsers | shipped (0.19.4.1) | Opens Privacy & Security > Files & Folders when macOS ≥ 27 (H commit `1280992`). FACT |
| Sync | planned (flag) | End-to-end encrypted "private vault" sync: the browser encrypts with AEAD and an extension implementing `syncVaultProvider` stores opaque objects. `kApiSyncVaultProvider` is `FEATURE_DISABLED_BY_DEFAULT` (H: `patches/helium/core/sync/provider/api.patch` L7). 17 patches, about 8,900 lines; 22 commits touched `patches/helium/core/sync` since Sep 1 (`gh api .../commits?path=`). Site says sync: "Not yet". FACT |
| Profiles with custom avatars | shipped | `custom-profile-avatar.patch`. FACT |

### Privacy and blocking

| Feature | Status | Evidence |
| --- | --- | --- |
| Consent before any Helium service request | shipped | `ShouldAccessServices` = `services.enabled` (default true) AND `services.user_consented` (default false, set in onboarding) (H: `patches/helium/core/services-prefs.patch` L417, L529; `onboarding-page.patch` L15-31, L676-679). FACT |
| Per-service toggles and self-hosted origin override | shipped | `helium.services.{ext_proxy,ublock_assets,spellcheck_files,bangs,browser_updates}`; `origin_override` accepts only HTTPS or localhost (services-prefs.patch L492-502). FACT |
| Versioned services consent with a changelog | shipped | `kHeliumCurrentSchemaVersion = 1` plus changelog text (services-prefs.patch L700-743). FACT |
| uBlock Origin (MV2 fork) as a built-in component, Helium filter lists, CNAME uncloaking | shipped | `ublock-install-as-component.patch`, `ublock-dns-uncloaking.patch`; uBO 1.75.0 from imputnet/uBlock (H: `deps.ini`); MV2 kept by `ungoogled-chromium/extensions-manifestv2.patch`. FACT |
| Extension downloads through an anonymizing proxy | shipped | Requests are normalized (random RAM size 4/8/16, random Chromium version, fresh UUIDs, shuffled order) and padded with `ceil(2*(1+log2(n)))` decoy extensions from a pool of up to 2,048 (HS: `svc/extension-proxy/lib/omaha/request.ts` L74, L93-96; `mixins.ts` L11, L68). FACT |
| Fingerprint noise (canvas, audio, hardwareConcurrency) | shipped | `helium.noise.enabled` default true (H: `patches/helium/core/noise/core.patch` L1443). FACT |
| Global Privacy Control | opt-in | default false (`network/global-privacy-control-pref.patch` L20). FACT |
| WebRTC: public interface only | shipped | (`webrtc-default-handling-policy.patch` L8). FACT |
| HTTPS-first, reduced Accept-Language, DNS-over-HTTPS presets | shipped | `prefer-https-by-default.patch`, `reduce-accept-language-headers.patch`, `network/dns-providers.patch`. FACT |
| ECH off, QUIC v2, split TLS ClientHello, ignore system proxy | flag | `network/*-flag.patch`. FACT |
| No password manager | shipped | A policy handler forces `kCredentialsEnableService` and passkeys off (H: `patches/helium/core/disable-password-manager.patch` L10-25). Onboarding offers Proton Pass, Bitwarden, 1Password, KeePassXC, Dashlane, iCloud Passwords extensions. FACT |
| Google compatibility exceptions (sign-in, sessions, security keys) | shipped (0.19.2.1) | `ridiculous-google-compat-exceptions.patch` (H commit `12f09ae`). FACT |
| Widevine DRM (Netflix and similar) | absent | Site: no Widevine because of Google licensing and third-party fees ([helium.computer](https://helium.computer/)). CLAIM |
| Telemetry | absent | "no analytics", "zero web requests on first launch" ([helium.computer](https://helium.computer/)). CLAIM. ungoogled-chromium domain substitution and patches such as `disable-webrtc-log-uploader.patch` and `disable-network-time-tracker.patch` cut Google endpoints. FACT (series) |

### AI assistant and agent

| Feature | Status | Evidence |
| --- | --- | --- |
| Any AI | absent, actively removed | `ungoogled-chromium/disable-ai.patch`; 0.19.3.1 also drops Glic, Lens, Compose, actor overlay, Skills, and AI-mode WebUI bundles, about 1.45 MiB (H commit `aec023c`, `patches/helium/core/remove-unused-ai-resources.patch`). FACT |

### Extensibility

| Feature | Status | Evidence |
| --- | --- | --- |
| All Chromium extensions, including MV2 | shipped | `extensions-manifestv2.patch`. FACT |
| AppleScript (Chromium's dictionary plus a new `select` tab command) | shipped | HM: `patches/helium/macos/applescript-tab-select-command.patch`. Chromium's dictionary already has `execute` javascript for a tab. FACT |
| `syncVaultProvider` extension API | flag | See Sync. FACT |
| Helium flags (`chrome://flags` entries tagged "Helium flag") | shipped | `helium_flag_entries.h` in several patches. FACT |
| Managed policies for components | shipped | `add-component-managed-schema-support.patch`. FACT |
| CLI, MCP, local API | absent | Only Chromium's `--remote-debugging-port`. INFERENCE (no Helium code found) |

### Other

| Feature | Status | Evidence |
| --- | --- | --- |
| Native macOS translation of selected text | shipped (macOS) | The context menu item Translate “…” uses the private `TranslationUI.framework` (`LTUITranslationViewController`) loaded at runtime (HM: `patches/helium/macos/native-translation-context-option.patch` L115-148). Selection only, not whole pages. FACT |
| Immersive fullscreen (controls in Helium's own chrome) | shipped (macOS) | HM: `helium-immersive-fullscreen.patch`. FACT |
| Native frame materials (vibrancy) | flag + opt-in | `kHeliumNativeFrameMaterials` disabled by default; setting labelled "experimental… May cause UI clarity issues" (H: `patches/helium/ui/native-frame-materials.patch` L19, L97-101). FACT |
| Memory Saver on, infinite tab freezing, lazy session restore | shipped | `memory-saving-by-default.patch`, `infinite-tab-freezing.patch`, `lazy-session-restore.patch` (restored tabs stay unloaded until activated). FACT |
| Energy Saver frame cap (30/60/120/off), default 30 fps | flag | `add-low-power-framerate-flag.patch` L7-58. FACT |
| Hide native window buttons | flag (0.20.1.1) | `--hide-window-buttons` (H: `patches/ungoogled-chromium/add-flag-to-hide-window-buttons.patch`). FACT |
| Toasts (copy link, new tab opened in frameless), page zoom indicator, screenshots | shipped | `toast.patch`, `page-zoom-indicator.patch`, `enable-screenshots.patch`. FACT |
| 81 UI languages, translated by an LLM in batches | shipped | H: `i18n/languages.json` (81 keys), `i18n/prompt.md`, `devutils/i18n_translate.py` L26-40 (`LLM_MODEL`). Volunteer native reviewers are named for only 12 of 81 languages (H: `i18n/owners.yml`). FACT |
| Automatic updates (Sparkle 2) with stable/beta channel flag | shipped | `add-update-channel-flag.patch`; feed `updates.helium.computer/mac/appcast-<arch>.xml` (`add-updater-preference.patch` L54-57). FACT |

## UI, look, and feel

**Layout.** Four layouts, picked in Settings or the View > Browser Layout
menu. Classic is Chrome's top tab strip. Compact puts tabs into the toolbar
row. Vertical uses Chromium's vertical tab strip on the left or right.
Dynamic overlaps toolbar and tab strip to clamp margins
(`patches/helium/ui/layout/dynamic.patch`). 0.20.1.1 moved these into their
own "Layout" section with skeleton previews of each layout (H commit
`cb10d7c`). Frameless mode hides the sidebar and top bar until the cursor
touches a window edge. FACT

**Visual language.** Quiet and flat. Helium removes toolbar dividers, toolbar
corners, ink ripples, NTP footer and Google promos, and squares off NTP
monograms (`remove-toolbar-dividers.patch`, `disable-ink-ripple-effect.patch`,
`square-ntp-monograms.patch`, `clean-new-tab-page.patch`). Web content sits
in a rounded frame inset from the window (`rounded-frame-corners.patch`).
FACT

Exact shape values (FACT):

| Token | Value | Source |
| --- | --- | --- |
| Generic frame radius | 8 px | H: `patches/helium/ui/frame-radius-helper.patch` L28-29 |
| macOS window radius | 17 px on macOS 26+, 12 px before | same file L51-55 |
| Padded frame radius | window radius − `kHeliumBasePadding` | same file L38-40 |
| Buttons | 7 px (new `kMSmall` token, Chromium uses pill `kFull`) | H: `patches/helium/ui/layout-provider.patch` L17, L37-38 |
| Dialogs, menus, combobox, find bar | 8 px | same file L20-28 |
| Button horizontal padding | 14 px (Chromium 16) | same file L8 |

**Materials.** Off by default. The experimental "native frame materials"
setting puts an `NSVisualEffectView` behind the window, using the Sidebar
material in dark mode and the Menu material in light mode, with blending
"behind window" (H: `patches/helium/ui/native-frame-materials.patch` L19,
L308-309, L371). Helium itself warns it "May cause UI clarity issues". FACT

**Typography.** I found no Helium font changes. It uses Chromium's system
font stack. INFERENCE (no font patches in `patches/series`)

**Color and themes.** Helium replaces Chromium's blue reference palette with
an indigo one (tone 50 = `#516BEC`) (H: `patches/helium/ui/helium-color-scheme.patch`
L19-24). Since 0.19.3.1 Chrome Web Store themes and system themes keep their
own frame colors; the active tab starts from the omnibox color and is pushed
to contrast 1.5 (dark) or 1.25 (light) against the frame (H commit `888f0fb`).
FACT

**Motion.** Taken from code. `RichAnimationDuration` returns zero when the
system asks for reduced motion. On macOS that reads
`accessibilityDisplayShouldReduceMotion` (Chromium 154:
`ui/gfx/animation/animation.cc` L114-116, `animation_mac.mm` L15-17, L41).
FACT. Only the rows marked `RichAnimationDuration` below are covered; the
others use plain durations.

| Motion | Duration | Curve | Source (FACT) |
| --- | --- | --- | --- |
| Frameless reveal of sidebar and top bar | 200 ms (`RichAnimationDuration`) | `FAST_OUT_SLOW_IN_3` | H: `patches/helium/ui/layout/zen-mode.patch` L23-30, L59-65 |
| Frameless edge trigger | 6 px strip, 8 px hover leeway | — | same, L23-24 |
| Frameless hide grace | 150 ms after hover exit; 3,000 ms after the cursor leaves the window | — | same, L27-30 |
| Vertical tabs expand/collapse | 250 ms both ways (Chromium: expand 300 or 400 ms, collapse 250 or 350 ms, by flyover flag) | `EASE_IN_OUT_EMPHASIZED` (Chromium uses `ACCEL_80_DECEL_20` with the flyover flag) | H: `patches/helium/ui/layout/vertical.patch` L1300-1315 |
| Toast in / out | 300 ms / 150 ms; opacity 50 ms | `ACCEL_5_70_DECEL_90` / `ACCEL_30_DECEL_20_85` | H: `patches/helium/ui/toast.patch` L33-34, L208-211, L283-287 |
| Location-bar progress line | 180 ms progress, 700 ms pulse loop while loading, 320 ms fade | `EASE_OUT` / `EASE_IN_OUT` / `EASE_OUT` | H: `patches/helium/ui/progress-bar.patch` L149-151, L177-179 |
| Split view drop target | 300 ms (Chromium 450 ms); 500 ms timers | — | H: `patches/helium/ui/multi-contents-drop-target.patch` L23, L415 |
| Hibernated favicon fade | 250 ms; the 1 s discard ring animation removed | — | H: `patches/helium/ui/tab-icon.patch` L220-232 |
| Fullscreen exit bubble | 2,500 ms shown, 300 ms slide | — | H: `patches/helium/ui/exclusive-access-bubble.patch` L8, L19 |

**Signature interactions that feel good.**
- Cmd+S collapses or expands the sidebar in the Vertical layout. FACT
- Frameless mode with pin toggles for sidebar and top bar, plus a toast
  ("New tab opened") when a link opens a tab you can't see (H:
  `i18n/source.gen.json` 205). FACT
- Cmd+Shift+C copies the URL with a toast; it inspects instead when DevTools
  has focus (`keyboard-shortcuts.patch` L103-108, L183). FACT
- MRU Ctrl+Tab, one-click hibernate, bangs that skip the results page. FACT

**Things that feel bad.**
- Cmd+S in frameless mode hides the whole sidebar and makes "the whole UI
  jump around", unlike normal mode ([#1971](https://github.com/imputnet/helium/issues/1971), open). FACT (user report)
- Frame drops in the frameless sidebar slide on a 240 Hz display ([#1887](https://github.com/imputnet/helium/issues/1887), open). FACT (user report)
- Clicks on right-side vertical tabs in frameless mode reach the page
  underneath on Windows ([#2733](https://github.com/imputnet/helium/issues/2733), dup of #1946). FACT (user report)
- The sidebar bounced at the window edge until 0.20.1.1 (H commit `899e8eb`). FACT
- Reviewers call it "barebones to a fault" next to Brave ([Techlore](https://techlore.tech/helium-browser-review-a-truly-minimal-privacy-focused-chromium-browser/)) and note it lacks Arc's spaces and command bar ([Supasidebar](https://supasidebar.com/blog/helium-vs-arc)). CLAIM
- Many toggles: four layouts, right side, minimal/centered location bar,
  per-button toolbar switches, frameless pins. Less opinionated than rac
  wants. INFERENCE

## Architecture

**Process model.** Unchanged Chromium multi-process (browser, renderers, GPU,
network service, utility processes). Importers run in the utility process
(`chrome/utility/importer/arc_sidebar_importer.cc`). FACT

**How it integrates the engine: patches on a source tarball.**

```
Chromium source archive (now from tarballs.imput.net)
  + Helium core series (imputnet/helium/patches/series: 346 patches, ~91k lines)
      71 ungoogled-chromium, 6 inox, 4 brave, 3 bromite, 3 iridium,
      1 debian, 2 upstream-fixes, 256 helium/{core,ui,settings}
  + helium-macos series (23 patches, ~4.8k lines)
  + rac (180 patches, ~110.7k lines)        <- rac's layer is larger than Helium's
then: domain substitution, "Chrome"→"Helium" name substitution, i18n injection,
version stamping, resource copy
```

Counts: FACT, from `patches/series` and `wc -l` at each tag. Order of steps:
FACT (HM: `devutils/shared.sh` L50-62). Patches apply with GNU `patch -p1
--ignore-whitespace --forward`, with fuzz allowed by default; its dry-run check and
the bot use `--fuzz=0` (H: `utils/patches.py` L93-103, L132-145, L240-243).
FACT

Helium core's patches touch 1,645 files and create 195 of them. FACT
(counted from `+++` headers). Helium is not a GitHub fork of
ungoogled-chromium; it merges ungoogled's history ("merge: update
ungoogled-chromium to …" commits, Blaise's "Update to Chromium …" commits).
FACT (`git log`)

**UI technology.**
- Browser chrome: C++ Views (sidebar, toolbar, frameless, split view). FACT
- Settings and internal pages: Chromium WebUI (TypeScript, Lit/Polymer). FACT
- Onboarding (`helium://setup`): a Svelte 5 + Vite app in its own repo,
  shipped as a prebuilt tarball with a GN `BUILD.gn` and a `.grdp` of strings
  (H: `deps.ini` `[onboarding]`; tarball contents). Uses `@imput/helium-prism`
  components. Flow: Welcome, Helium services, Search engine, Data import,
  Password manager, Default browser, Finish (`src/lib/onboarding-flow.ts`).
  FACT
- macOS pieces in Objective-C++: Sparkle 2, immersive fullscreen, private
  TranslationUI, keychain retry. FACT

**Languages.** C++, Objective-C++, TypeScript, Python (build utils), Bash,
Deno TypeScript (services). FACT

**Code layout (core).** `patches/` by vendor; `utils/` (download, prune,
patch, substitute, i18n apply); `devutils/` (lint, validate, i18n tools);
`resources/` (branding, generated assets); `i18n/`; `flags.gn`,
`downloads.ini`, `deps.ini`, `pruning.list`, `domain_substitution.list`.
Platform repos add `dev.sh` (the `he` command), `build.sh`, `devutils/shared.sh`,
`.github/`, `patches/`, `resources/`. FACT

**Coupling with rac.** rac's 871 hunks on upstream files hit 217 files. 134 of
those files (62%) are also patched by Helium, carrying 629 of the 871 hunks
(72%). Eight are files Helium creates (20 rac hunks), such as
`browser_shortcut_service.cc`, `frame_corner_radius.cc`,
`onboarding_page_ui.cc`, `sparkle_glue.mm`. FACT (my count from `+++`
headers of R: `patches/rac/**` against H and HM series)

## Data and storage

| What | Where / format | Evidence |
| --- | --- | --- |
| Profile data | `~/Library/Application Support/net.imput.helium` (dev builds `.dev`); standard Chromium files: `Preferences` JSON, SQLite (History, Cookies, Web Data), LevelDB | HM: `patches/helium/macos/change-product-dir-name.patch`. FACT |
| Encryption key | macOS Keychain item "Helium Storage Key" (Chromium's os_crypt) | HM: `change-keychain-name.patch`. FACT |
| Keychain failure handling | Retries reads and preserves the error so a denied Keychain doesn't wipe encrypted data | HM: `prevent-reset-on-keychain-unavailability.patch` L20-36, L89-90. FACT |
| Helium settings | `helium.*` prefs in `Preferences`, e.g. `helium.browser.layout`, `helium.services.*`, `helium.noise.enabled`, `helium.completed_onboarding` | grep of H patches. FACT |
| Sync | Not shipped. Experimental vault: snapshots plus deltas in immutable commit objects with a conditional "head" write; one AEAD key per vault, role and vault ID as associated data; the local checkpoint lives "only in OS-protected local state"; providers can wrap the 32-byte vault key with account credentials after user consent | H: `patches/helium/core/sync/vault-format.patch`, `vault-encryption.patch`, `provider/api.patch` comments; commit `abe6d5f`. FACT |
| Server component | helium-services: nginx front, Deno services (extension-proxy ×2, ubo list mirror, bangs, minidumpster crash handler, minipush Web Push), sparkler (Sparkle appcast from GitHub releases), release-collector; Docker Compose plus Ansible, BGP and firewall playbooks | HS: `README.md`, `compose.yml`, `deploy/`. FACT |
| Endpoints | `services.helium.imput.net` (ext proxy, uBO lists, `bangs.json`, `/dict/` spell check, `/com` component updates); `updates.helium.computer` (Cloudflare-cached appcast); `crash.helium.computer` | services-prefs.patch L559-560; HS: `svc/*/README.md`. FACT |
| Logging | Services: anonymized logs kept at most 24 h; crash reports 30 days, access limited to imputnet org members, IPs used in memory for rate limits | [helium.computer/privacy](https://helium.computer/privacy) (revision 2026-07-16); HS: `svc/minidumpster/README.md`. CLAIM (policy) |
| Telemetry | None in the browser. The website uses self-hosted Plausible | privacy policy. CLAIM |

**What leaves the machine.** Before consent: nothing from Helium itself
(site claim of zero requests on first launch, CLAIM; code gate is FACT).
After consent: extension update checks and downloads through the proxy,
filter lists, spell-check dictionaries, the bangs list, component updates via
the `/com` Omaha proxy, and the update appcast. Crash reports only if
enabled. Plus the user's own browsing, search suggestions to the chosen
engine, and DNS-over-HTTPS if chosen. FACT/INFERENCE

**Privacy design worth noting.** The extension proxy hides which extensions a
user has by mixing in decoys from other users' requests. The anonymity
improves with more users in the pool (HS: `mixins.ts` L66-80). A rac-hosted
copy would serve far fewer users, so it would hide less. INFERENCE

## Agents and AI

Helium has none, and removes Chromium's. It disables AI code paths
(`ungoogled-chromium/disable-ai.patch`, which also empties
`ActorKeyedService::GetTaskFromTab`) and since 0.19.3.1 strips the Glic,
Lens, Compose, actor overlay, actor-internals and Skills WebUI bundles
(`remove-unused-ai-resources.patch`). FACT

Implications for rac:
- rac's agent drives Chromium's renderer "actor" tools directly
  (`chrome/renderer/actor/*`, `components/actor/core/*`; 20+ distinct actor
  symbols in R: `patches/rac/agent/`). rac does not use the removed overlay
  or Glic resources. FACT (grep)
- Helium keeps pruning AI code. Each prune can hit rac's agent. The actor
  code is also churning upstream: `type_tool.cc` changed 332 lines and
  `ToolBase::ExecutionObservationDelay` was removed between 154 and 156.
  FACT (diff of Chromium files at both tags)
- Outside-agent access that exists today with AI off: Chromium's AppleScript
  dictionary (windows, tabs, URL, `execute` javascript) plus Helium's `select`
  command. macOS asks the user before another app can send Apple Events.
  This is a zero-cost, already-built channel. FACT (sdef); usefulness:
  INFERENCE

## Build, release, and engineering

### Build system

- GN + siso via `autoninja`, targets `chrome chromedriver` (HM:
  `devutils/shared.sh` L138). CI adds `chrome/installer/mac` (HM:
  `.github/scripts/github_build.sh` L26-27). FACT
- Release builds use `is_official_build` and `chrome_pgo_phase=2`; dev builds
  swap to `is_component_build` (same file L97-105). FACT
- Compiler cache: `cc_wrapper="sccache"` in CI and when installed locally,
  ccache as a fallback (L76-92). FACT
- Optional remote execution: if `SISO_REAPI_ADDRESS` is set, dev builds use
  `use_remoteexec` against a NativeLink backend, with a Linux clang wrapper
  for macOS workers (L40-45, L86-87, L110-120; `rbe-nativelink-config.patch`,
  HM `rbe-linux-clang-wrapper.patch`). FACT. Whether the team runs a
  NativeLink cluster: unknown.
- Since 0.19.3.1, sources come from **prepared Chromium archives** on
  `tarballs.imput.net`: a shared base layer (1.98 GB) plus a host layer
  (mac-arm64 1.39 GB, mac-x64 1.43 GB) that already contains dependencies and
  toolchains, so no `gclient sync` (H: `downloads.ini`; HM: `downloads.arm64.ini`;
  [chromium-tarballs](https://github.com/imputnet/chromium-tarballs); sizes
  from HTTP `content-length`). Google's own lite tarball is 2.01 GB without
  toolchains. `he setup -c` / `build.sh -c` still clone instead. FACT

### CI (helium-macos `.github/`)

| Workflow | What it does | Evidence |
| --- | --- | --- |
| `lint.yml` | Runs Helium's `devutils/lint.py` on the series, about 10 s, on Ubuntu | HM: `.github/workflows/lint.yml`; run 39651825776. FACT |
| `sanity.yml` | Caches the unpatched source, applies all patches with quilt, **fails if any patch applies with an offset**, then runs a 30-second build and passes on timeout. Also a "substitution" check. About 10-24 min | HM: `.github/scripts/sanity-check.sh` L44-46, L53-54; run 39651825730. FACT |
| `build.yml` → `building.yml` → `build-phase.yml` | Manual dispatch. One "retrieve resources" job per arch (prepare sources, zstd archive, upload), then up to **10 chained phases** per arch. Each phase gets 6 h minus 1 h for setup and upload, builds under `timeout -k 7m`, then tars all of `build/src` with `zstd -11` as a checkpoint artifact for the next phase | HM: `building.yml` L45-140; `github_build.sh` L11, L26; `github_prepare_artifacts.sh` L82. FACT |
| Release job | Downloads both DMGs and the Sparkle deltas, writes release notes, and creates a GitHub **prerelease** with `imputnet/action-gh-release@v2.5` | HM: `build.yml` L32-86 (prerelease L79). FACT |
| `bump.yml` | Runs core's `bump-platform` action: moves the submodule, bumps `revision.txt`, applies core patches with `--no-fuzz`, runs `quilt push -a --refresh` on the platform patches on an Ubuntu runner, and opens an "update: helium X" PR as helium-bot | H: `.github/actions/bump-platform/action.yml` L33-119. FACT |

**Runners and cache, the reason Helium's chain finishes.**
- Every job of the 0.20.1.1 build ran on `depot-macos-latest` (run
  39651879454). FACT
- That label is macOS 26 on M4 with 8 CPUs, 24 GB RAM, a 400 GB disk, at
  $0.08/min ([Depot runner types](https://depot.dev/docs/github-actions/runner-types)).
  GitHub's free `macos-latest` for public repos is 3 M1 CPUs, 7 GB RAM, 14 GB
  SSD ([GitHub docs](https://docs.github.com/en/actions/reference/runners/github-hosted-runners)). FACT
- "WebDAV sccache" is Depot Cache. Depot runners start with
  `SCCACHE_WEBDAV_ENDPOINT` preset ([Depot sccache docs](https://depot.dev/docs/cache/reference/sccache)).
  Helium's script only falls back to the GitHub Actions cache when no
  `SCCACHE*` variable exists, and sets `SCCACHE_WEBDAV_KEY_PREFIX=<arch>`
  (HM: `github_build.sh` L18-23). FACT
- Timings for 0.20.1.1: dispatch 18:20 UTC Oct 21, release 08:41 Oct 22
  (14 h 21 min). arm64 needed 2 phases (4 h 31 min + 2 h 12 min). x86_64
  needed 3 (4 h 31 min + 5 h 16 min + 3 h 18 min). Resource jobs about 22 min
  each. FACT (job timestamps)
- Helium's checkpoint is a plain `tar -c` of `build/src` (HM:
  `github_prepare_artifacts.sh` L82). rac found that this tar format drops
  sub-second mtimes, so siso reruns almost everything after each phase; the
  fix is `tar --format pax` (`plans/context/ci-status.md`, rac PR #20). Helium
  very likely has the same reset and simply has faster runners and cache.
  INFERENCE
- Rough Depot cost for a rac release at Helium's timings: about 20.6 runner
  hours, about $99 for both arches, about $34 for arm64 only, plus a $20/month
  plan ([pricing](https://depot.dev/pricing)). INFERENCE. A first build with
  a cold cache will cost more. Depot's open-source discount is not published.

### Signing, notarization, updates

- Signing uses Chromium's `sign_chrome.py` with the Developer ID identity, and
  `notarytool` with a keychain profile; ad hoc signing without a certificate
  (HM: `sign_and_package_app.sh` L13-36). FACT
- Sparkle 2 with EdDSA; deltas against the last 5 GitHub releases (HM:
  `devutils/generate_sparkle_deltas.py` L34). DMGs are about 113 MB (arm64)
  and 130 MB (x86_64); deltas 40-53 MB (0.20.1.1 release assets). FACT
- The appcast is generated by `sparkler` from GitHub releases and served from
  `updates.helium.computer` behind Cloudflare (HS: `util/sparkler/README.md`).
  FACT

### Tests

- No Chromium unit or browser tests run in any Helium CI. FACT (all workflows
  read)
- Core CI runs yapf, pylint and pytest on `utils/` and `devutils/`, plus
  patch lint and i18n drift and lint checks (H: `.github/workflows/ci.yml`,
  `lint.yml`). FACT
- rac inherited this. rac's "Sanity passes on timeout" is Helium's design
  (`test "$_status_code" -eq 124`). FACT

### How Helium tracks upstream

1. ungoogled-chromium updates its patches for a new Chromium (Blaise).
2. Helium merges ungoogled, refreshes its own patches, updates
   `exclude-irrelevant-flags`, and merges as "merge: update to chromium X".
3. `bump-platform` opens a refresh PR in helium-macos; a maintainer
   dispatches the Depot build and publishes.

FACT (H `git log`, e.g. `0673f87` → `4339fde` → `46c7ea4` → `f29a259`). Since
September 2026 this loop runs every two weeks, because Chrome itself moved to
a two-week stable cycle starting with Chrome 153 on 2026-09-08, while
Extended Stable stays on eight weeks
([developer.chrome.com](https://developer.chrome.com/blog/chrome-two-week-release)).
FACT. Chrome 157 is due 2026-11-03, and its tarball already exists
(`chromium-157.0.8103.15`, chromium-tarballs releases). FACT/CLAIM

### Contribution policy

- Core `AGENTS.md`: agents must refuse all code changes, must not open PRs on
  any imputnet repo, and contributors who send "vibe-coded" PRs will be
  "permanently banned and publicly shamed" (H: `AGENTS.md` L1-13). FACT
- `CONTRIBUTING.md`: no AI-written issue or PR descriptions ("banned for spam
  without review"); non-trivial changes need an approved issue first;
  "permanently ban you if you spam our repos with AI slop". FACT
- In practice outside PRs rarely land: 166 of 169 PRs merged since
  2026-07-25 are by the two maintainers. Community PR #2367 was closed by its
  author after seven weeks without a maintainer review, and #2776 was closed
  by a maintainer a day after it opened. FACT
- This matches rac's rule never to send anything upstream. rac must also keep
  Helium's submodule `AGENTS.md` out of its agents' instructions for rac's own
  files (rac's `AGENTS.md` already says so). FACT

### What changed from 0.18.2.1 to 0.20.1.1

Six tagged releases: 0.18.3.1, 0.19.1.2 (prerelease), 0.19.2.1, 0.19.3.1,
0.19.4.1, 0.20.1.1. 85 core commits; 277 core patch files changed (9 added,
6 deleted); 32 helium-macos files changed (release notes and `git diff`).
Chromium went 154.0.8037.92 → .97 → 155.0.8059.39 → .79 → .84 →
156.0.8078.47. FACT

User-visible:
- Mute tab(s) in the tab context menu (`b0e3abb`). FACT
- Expand on hover restored (off by default) and reused by frameless mode;
  corners shrink as the strip collapses; no top outline on hover-expanded
  tabs; frameless sidebar no longer bounces at the edge; crash fix when
  closing a frameless window (`48e91cb`, `7e73387`, `bc5de42`, `899e8eb`,
  `f756c6f`). FACT
- New Layout section in Settings with skeleton previews (`cb10d7c`). FACT
- Store and system themes work with Helium colors (`888f0fb`). FACT
- Vertical tab width kept across session restore (`4f8b31a`); brighter
  hibernated favicons in dark mode (`ee37182`); stacked split view corner fix
  (`7c66a44`). FACT
- Onboarding: browser discovery with an explicit "Allow" step, stable import
  IDs, and the macOS 27 Files & Folders action (`bfc28ba`, `1280992`,
  onboarding 202609160835 → 202610161403). FACT
- Fewer Chrome nags on the Web Store; Google sign-in compatibility
  exceptions; `--proxy-server` flags; `--hide-window-buttons` flag. FACT
- About 1.45 MiB less installed, from removed AI and experimental WebUI. FACT

Under the hood:
- Private sync work: profile repository, local/custom/disabled backends,
  simpler vault protocol. Still behind a disabled feature. FACT
- Password manager disablement moved from the "HOP" policy provider to a
  policy handler (`helium/hop/*` deleted). rac doesn't use HOP. FACT (grep)
- Build: prepared archives; full Chromium toolchain with workarounds removed
  (HM `cf1388f`); `retrieve_and_unpack_resource.sh` and
  `devutils/build_tools.sh` deleted; `prepare_sources` and `configure_build`
  take new arguments; Xcode 26.5 in CI. FACT

### How hard the rac sync will be

**Method.** For each of the 217 upstream files rac patches, I downloaded
Chromium's copy at the old and new tags from the GitHub mirror, applied the
full Helium core and macOS series with GNU patch, then applied rac's 180
patches in order. Files outside that set were skipped. I validated it on the
current base first: on Chromium 154 + Helium 0.18.2.1, all 180 rac patches
apply with zero failed hunks. FACT. Scripts: `/tmp/rac-overhaul/scripts/dryrun.sh`
(sketch in the appendix below). It checks text only, not compilation.

**Results.** FACT (dry run)

| Target | Fuzz | rac patches applying cleanly | Failed hunks | Missing files |
| --- | --- | --- | --- | --- |
| Current base (154 / 0.18.2.1) | 0 | 180 / 180 | 0 | 0 |
| 0.19.4.1 (Chromium 155.0.8059.84) | 2 (release default) | 143 / 180 | 43 | 2 files moved by Chromium (4 patch-file pairs in 3 patches) |
| 0.19.4.1 | 0 | 130 / 180 | 75 | same |
| **0.20.1.1 (Chromium 156.0.8078.47)** | **2** | **121 / 180** | **104** | same |
| 0.20.1.1 | 0 | 107 / 180 | 173 | same |

rac has 3,341 hunks in total. Many failures cascade: once a hunk fails, later
rac patches on the same file lose their context. For 0.20.1.1 with fuzz, only
**46 hunks in 32 patch-file pairs fail first**; the other 68 are knock-on
failures. For 0.19.4.1 it is 19 first failures. FACT (dry run)

Failures by rac group at 0.20.1.1, fuzz 2 (failing patches / group size,
failed hunks): sidebar-reveal 5/5 (12), settings 6/13 (15), sidebar-address-bar
3/10 (12), spaces 11/26 (18), look 9/20 (14), pinned 6/18 (7), ai 7/39 (7),
sidebar 3/4 (7), agent 3/19 (6), onboarding 2/6 (2), branding 2/4 (2),
updates 1/4 (1), pip 1/5 (1), privacy 0/2, dev 0/5. FACT

Where it breaks, and why:
- `chrome/browser/ui/BUILD.gn` (25 failed hunks, mostly cascades): file
  lists moved. Mechanical. FACT
- `vertical_tab_strip_region_view.cc` (16), `vertical_tab_strip_state_controller.cc`
  (13): Helium reworked frameless mode around expand on hover. rac's
  `sidebar-reveal/edge-reveal.patch` changes the same expand-on-hover
  parameters (350 → 100 ms) (R: `patches/rac/sidebar-reveal/edge-reveal.patch`
  L9-10). This is a design merge, not a text fix. FACT/INFERENCE
- `appearance_page.ts` (11), `appearance_page.html.ts` (9),
  `settings_menu.html` (4): Helium's new Layout section. FACT
- Files Chromium moved under `chrome/browser/ui/views/`:
  `tabs/{horizontal,vertical}_tab_style_views.cc` to `tabs/common/`, and
  `tabs/new_tab_button_menu_model.h` to `tabs/shared/` (HTTP 200/404 checks of
  raw files at both tags). FACT. Both are part of Chromium's "Unified
  Tabstrip" work. [Chromium commit 8277d76](https://github.com/chromium/chromium/commit/8277d76b10)
  moved only `new_tab_button_menu_model.{h,cc}`; I did not identify the commit
  that moved the style files. Three rac patches touch the style files;
  `sidebar/new-tab-row.patch` includes the moved header. FACT
- Helium removed `SetZenModeFloatingStyleForLayout`, which appears in rac's
  `sidebar-address-bar/header.patch` L237 context. FACT
- Renderer actor files (`tool_base.cc`, `key_dispatcher.cc`,
  `click_dispatcher.cc`, `chrome_render_frame_observer.cc`) in
  `agent/12-hardening.patch`: Chromium churn. FACT
- Of 470 non-generated headers rac's patches include, only
  `new_tab_button_menu_model.h` is gone in 156. FACT (HTTP checks against the
  156 tag)

Repo-level merge. A test merge of tag 0.20.1.1 into a scratch clone of rac
conflicts only in `patches/series` (Helium deleted
`fix-window-resize-jank.patch`). `dev.sh`, `devutils/shared.sh` and rac's CI
edits auto-merge. FACT. The merged CI calls the new `prepare_sources` and
`configure_build` signatures, and the stricter sanity check will fail on any
patch offset until rac's patches are refreshed. FACT

What the dry run can't see. Compile errors from Chromium API changes in
rac's 325 new files; behavior changes in frameless mode, layout settings and
onboarding; and string files changed by rac's name pass. INFERENCE

**Sync in plain English.** About two thirds of rac's changes still fit the
new Helium as they are. The rest need hand fixes. Most of those are
bookkeeping, such as lists of file names. The hard part is the sidebar.
Helium rebuilt how its hidden sidebar slides in. rac's version of that
feature sits on the same code. rac has to redo it on top of Helium's new
version, or drop parts of it. The settings page also moved things around. A
stepping stone exists: Helium 0.19.4.1 breaks less than half as much. Going
there first splits the work, but needs two full builds instead of one. Each
new Chromium version also means rebuilding the big source tree. That now
happens every two weeks.

<details><summary>Appendix: dry-run sketch</summary>

```sh
# inputs: CR=dir of Chromium files at the target tag (only files rac touches),
# HC=helium core patches dir, HM=helium-macos patches dir, RAC=rac repo
series() { grep -v '^[[:space:]]*$' "$1" | grep -v '^#'; }
cp -R "$CR"/. tree/
for p in $(series "$HC/series"); do
  gpatch -p1 --ignore-whitespace --forward -f --no-backup-if-mismatch -r - -d tree -i "$HC/$p"; done
for p in $(series "$HM/series" | grep -v '^rac/'); do
  gpatch -p1 --ignore-whitespace --forward -f --no-backup-if-mismatch -r - -d tree -i "$HM/$p"; done
for p in $(grep '^rac/' "$RAC/patches/series"); do
  gpatch -p1 --ignore-whitespace --forward -f --no-backup-if-mismatch --fuzz=2 -r - -d tree \
    -i "$RAC/patches/$p" 2>&1 | grep -E 'FAILED|No file to patch' && echo "FAIL $p"; done
# Chromium files: https://raw.githubusercontent.com/chromium/chromium/<tag>/<path>
# Onboarding strings come from the helium-onboarding release tarball in deps.ini.
```
</details>

## Strengths and weaknesses

**Strengths**
- **Security cadence.** New Chromium majors ship 2-4 days after Chrome
  stable, even on the new two-week cycle. FACT (release dates)
- **A privacy model you can check in code.** One gate
  (`ShouldAccessServices`) guards every service, consent defaults to false,
  each service has its own toggle, and the server code is public down to the
  Ansible playbooks. FACT
- **Clever extension privacy.** Decoy mixing and request normalization are
  real engineering, not marketing. FACT (HS `mixins.ts`, `request.ts`)
- **Calm UI with careful numbers.** Short, emphasized curves (200-300 ms),
  tight radii. The frameless reveal and favicon fade honor reduced motion
  through `RichAnimationDuration`. FACT
- **Good import coverage**, including Arc's sidebar, Zen, Dia and Comet. FACT
- **Tooling that saves time**: prepared Chromium archives, a bump bot that
  refreshes platform patches, strict "no offsets" sanity check, patch lint.
  FACT
- **Fast CI for free**, thanks to Depot runners and Depot Cache. FACT

**Weaknesses**
- **Bus factor of two.** Outside PRs rarely land: 3 of 169 merged PRs since
  2026-07-25 came from outside. #2367 sat seven weeks without a maintainer
  review; #2776 was closed within a day. A rac that needs a Helium fix can't
  get it upstream, by policy and in practice. FACT
- **No real tests.** CI never compiles more than 30 seconds of the build and
  runs no Chromium tests. Regressions surface after release. FACT
- **Feature gaps for Arc users**: no spaces, command bar, sync, peek, or DRM
  video. FACT/CLAIM
- **Churny UI internals.** 38 commits touched `helium/ui/layout` since
  2026-09-01, and Chromium's own tab strip is being reorganized. rac's
  sidebar sits right on top of both. FACT
- **Frameless and vertical tabs still have rough edges** (#1971, #1887,
  #2733). FACT (user reports)
- **Central services with no promise to forks.** The terms are silent on
  third-party builds, and the privacy policy excludes them. FACT
- **Less opinionated than rac.** Four layouts and many toggles mean rac must
  hide things, and every hide is a patch. INFERENCE
- **Fragile platform bets.** Private Apple frameworks (TranslationUI) and
  MV2 extensions both depend on others not breaking them. INFERENCE

## What rac should take (ranked) and what rac should avoid

Costs are rough agent-effort estimates (S ≤ 1 day, M = 2-5 days, L > 1 week).
All are INFERENCE unless noted.

1. **A "Helium fit" check that runs on every Helium release. Cost S.**
   Copy the idea of Helium's `bump-platform` action, but for rac. On a free
   Ubuntu runner, merge the new helium-macos tag into a scratch branch, apply
   Helium's and rac's patches, and post which rac patches fail. The sparse
   method above takes minutes; a full tree from the prepared base archive is
   still cheap. With Chrome on a two-week cycle, rac needs this every two
   weeks.
2. **Sync to 0.20.1.1 now. Cost M.** Two options for the maintainer:
   - *One jump:* one tree rebuild; about 46 first-failure hunks plus the
     sidebar design merge.
   - *Two steps via 0.19.4.1:* 19 first-failure hunks first (mostly
     `BUILD.gn`), then the layout and settings conflicts; two rebuilds.
     The earlier roadmap draft said "Sync to Helium 0.19"
     (R: `plans/context/roadmap-revision-2026-10-22.md` L64).
   Either way, take Helium's new `prepare_sources` and `configure_build`
   calls in CI, and refresh every rac patch so the stricter sanity check
   sees no offsets. No script in R: `devutils/rac/` calls the deleted
   `retrieve_and_unpack_resource.sh` or `build_tools.sh`. rac's inherited CI
   does: R: `.github/scripts/sanity-check.sh` L16-17 and
   `.github/workflows/sanity.yml` L42. The scratch test merge drops those
   calls and keeps rac's two sanity-check edits, without conflict. FACT
3. **Rebuild rac's sidebar hide and reveal on Helium 0.20's frameless
   overlay. Cost M (during the sync).** Helium now floats the sidebar using
   the expand-on-hover overlay with a "keep expanded" lock (H `48e91cb`).
   Keep only what is rac's: full-or-hidden, the 100 ms dwell, the top-edge
   toolbar reveal. This shrinks rac's hunks in the two files that broke most.
4. **Build release CI the way Helium does: big macOS runners plus a WebDAV
   compiler cache. Cost S to switch; about $34 per arm64 release or $99 for
   both arches, plus $20/month.** Depot's 8-core M4 runners finish Helium in
   2-3 phases. GitHub's free 3-core M1 runners have not finished rac so far.
   Once the tar fix (rac PR #20) lets phases resume, free runners may finish
   within 10 phases; Depot then becomes a speed choice (about 14 h vs. likely
   more than a day), not a must. Ask Depot about open-source terms, since it
   sponsors Helium.
5. **Ship arm64 first. Cost S.** macOS 27 runs only on Apple silicon
   ([Tom's Hardware](https://www.tomshardware.com/software/macos/macos-tahoe-is-the-last-release-for-intel-macs-apple-silicon-exclusivity-will-mark-end-of-hackintoshes)),
   and Helium's x86_64 build took 13 h against 6.7 h for arm64. The cost:
   Intel Macs on macOS 26 or older get no rac until an x86_64 build exists.
6. **Arc import built on Helium's `ArcSidebarImporter`. Cost M.** Helium
   already parses `StorableSidebar.json` and made
   `ChromeImporter::ImportBookmarks` virtual (H: `add-arc-importer.patch`
   L453). A rac subclass in a new file can map Top Apps → favorites,
   each space → a rac space (with a readable name; Helium uses the
   internal ID, and whether Arc stores a title there is unverified), and
   pinned containers → pinned tabs with folders. Reuse Helium's macOS 27
   Files & Folders prompt. Arc shuts down 2026-12-22.
7. **Use Helium's settings layout instead of re-patching it. Cost S-M.**
   Take the new Layout section with skeleton previews. Hide the layouts rac
   doesn't support with one small hook, not edits across templates.
8. **Keep Helium services, with the override as the escape hatch. Cost S
   (a doc).** The origin override already accepts HTTPS or localhost. Don't
   self-host yet: a smaller crowd weakens the extension proxy's mixing.
9. **Prepare rac data for Helium's coming sync. Cost S now, M later.**
   `rac.spaces` and `rac.sidebar.lists` are plain dictionary prefs today
   (R: `patches/rac/spaces/model.patch` L364,
   `patches/rac/pinned/sidebar-store.patch` L411). Choose a form Chromium
   sync can carry, so rac gets end-to-end sync when Helium enables it. Don't
   build a rac sync server.
10. **Reuse Helium's versioned consent pattern. Cost S.** A schema version
    plus a changelog notice (services-prefs.patch L700-743) fits rac's AI
    opt-in and future crash-report consent.
11. **Offer AppleScript as the first outside-agent channel. Cost S-M.** It
    works with AI off, costs nothing until used, and macOS asks the user
    before any app can control rac. Add rac spaces to the dictionary later.
12. **Adopt Helium's motion and shape numbers as rac's baseline. Cost S.**
    Document them (table above) and reuse `ShouldUseNativeFrameMaterials`
    for sidebar vibrancy. rac's patches mention it 9 times, but only 1 line
    adds a call (`look/dia-chrome.patch` L2049). 4 lines remove Helium's calls
    and 4 are unchanged context. FACT (grep of R: `patches/rac/`)
13. **Copy Helium's translation pipeline for rac strings. Cost M.** Helium
    ships 81 locales with LLM batch translation; volunteer reviewers cover
    12 of them (H: `devutils/i18n_translate.py`, `i18n/owners.yml`). rac's own strings are English only.
14. **Later: self-host `minidumpster` for opt-in crash reports. Cost M plus
    hosting.** AGPL, symbolicated, 30-day retention by default.

**Avoid**
- **Letting the gap grow.** Failed hunks more than doubled between 0.19.4.1
  and 0.20.1.1 (43 → 104), and each Chrome release carries security fixes.
- **Building deeper into Chromium's tab strip.** Files move every release
  ("Unified Tabstrip"). Keep rac's sidebar in rac-owned views with thin
  hooks.
- **Editing files Helium created** (8 files, 20 hunks today) or Helium's
  settings templates line by line.
- **Spreading the agent across Chromium's actor internals.** Helium and
  ungoogled keep pruning AI code, and Chromium keeps changing it. Put one
  rac-owned adapter between rac's agent and `chrome/renderer/actor`.
- **Sending anything upstream**, or planning on an upstream fix.
- **Promising Netflix or Spotify playback.** Helium has no Widevine. Decide
  this before marketing to Arc users.
- **Copying Helium's many toggles.** Pick one layout story and hide the rest.
- **Stale docs.** R: `docs/internals/overview.md` L69 says Chromium ships
  "roughly every four weeks"; it is two. R: `docs/operations/upstream-sync.md`
  L78 says rac has no Apple developer account; the brief says it does.

## Open questions and things you could not verify

- **Compile errors after the sync.** The dry run checks text only. API
  changes in rac's 325 new files are unknown until a build.
- **Helium's view of forks using its services.** Terms are silent; the
  privacy policy excludes third-party builds. No statement found.
- **When private sync ships**, and whether it will carry prefs that Helium
  doesn't own, like `rac.spaces`.
- **Whether Helium plans spaces or a command palette.** Requests are open
  (#1351, #317) with no maintainer reply found.
- **How much of Helium's phase 2 is real resume.** Its arm64 phase 2 took
  2 h 12 min. Helium checkpoints with the same plain `tar -c` (HM:
  `github_prepare_artifacts.sh` L82) that `plans/context/ci-status.md` now
  blames for dropping sub-second mtimes on macOS, so Helium most likely
  restarts siso too and is rescued by Depot's faster cache. INFERENCE; not
  checked against Helium's logs.
- **Depot open-source terms** are not published.
- **Whether "Allow JavaScript from Apple Events"** is still reachable in
  Helium's menus after `clean-main-menu.patch`.
- **Whether macOS 27's Files & Folders gate** applies to Arc's data folder.
- **Whether Arc's `StorableSidebar.json` holds readable space titles.** Helium
  uses only the space ID; I did not inspect a real Arc file.
- **Helium mobile.** Android and iOS tarball layers exist; no announcement.
- **Performance.** Helium publishes no benchmarks ("Faster than you blink").
- **How long MV2 survives** in ungoogled-chromium as Chromium deletes code.
- **Whether imputnet runs a NativeLink build cluster** for remote builds.

## Sources

Code (read-only clones in `/tmp/rac-overhaul/src/`):
- Helium core: https://github.com/imputnet/helium/tree/f29a25968e483f8bb85e47829ccd487bbe229199
  (rac's pin: `76141e139aa079aa24977d861e67bdb64923c3e8`)
- helium-macos: https://github.com/imputnet/helium-macos/tree/9aa975a (tag
  `0.20.1.1`); rac's base: tag `0.18.2.1` (`992a020`)
- helium-services: https://github.com/imputnet/helium-services/tree/110144e
- helium-onboarding release tarballs `202609160835` and `202610161403`
  (sha256 matches `deps.ini`):
  https://github.com/imputnet/helium-onboarding/releases
- chromium-tarballs: https://github.com/imputnet/chromium-tarballs
- Chromium files at `154.0.8037.92`, `155.0.8059.84`, `156.0.8078.47`:
  https://github.com/chromium/chromium (raw files per tag)
- Chromium Unified Tabstrip move of `new_tab_button_menu_model`: https://github.com/chromium/chromium/commit/8277d76b10
- rac: this worktree (`cfdcf83`), `patches/series`, `patches/rac/**`,
  `docs/internals/overview.md`, `docs/operations/upstream-sync.md`,
  `plans/context/*`

GitHub API (read-only `gh api`):
- Repo metadata, contributors, releases, issues: `repos/imputnet/{helium,helium-macos,helium-services}`,
  `orgs/imputnet`, `users/{wukko,dumbmoron}`
- Release notes: https://github.com/imputnet/helium-macos/releases (0.18.3.1 to 0.20.1.1)
- Build run and jobs: https://github.com/imputnet/helium-macos/actions/runs/39651879454
- Issues and PRs: https://github.com/imputnet/helium/issues/90,
  /1351, /215, /245, /2579, /317, /2367, /2776, /1971, /1887, /2733, /1946

Web:
- https://helium.computer/ (features, claims)
- https://helium.computer/blog/transparency
- https://helium.computer/privacy (revision 2026-07-16)
- https://helium.computer/terms (revision 2026-07-08)
- https://helium.computer/sponsor
- https://developer.chrome.com/blog/chrome-two-week-release
- https://browserhow.com/chrome-156-stable-update-windows-mac-linux/ (secondary)
- https://chromereleases.googleblog.com/2026/10/early-stable-update-for-desktop.html
- https://depot.dev/docs/cache/reference/sccache
- https://depot.dev/docs/github-actions/runner-types
- https://depot.dev/pricing
- https://docs.github.com/en/actions/reference/runners/github-hosted-runners
- https://www.tomshardware.com/software/macos/macos-tahoe-is-the-last-release-for-intel-macs-apple-silicon-exclusivity-will-mark-end-of-hackintoshes
- https://techlore.tech/helium-browser-review-a-truly-minimal-privacy-focused-chromium-browser/ (review)
- https://supasidebar.com/blog/helium-vs-arc (review)

My own measurements (reproducible with the appendix sketch):
- Dry runs: `/tmp/rac-overhaul/dryrun/{old_f0,mid_f0,mid_f2,new_f0,new_f2}/log/rac.tsv`
- rac file and hunk counts: `/tmp/rac-overhaul/rac_upstream_files.txt`,
  `rac_upstream_file_hunks.txt`, `rac_files_also_helium.txt`
- Chromium 154 → 156 churn per rac file: `/tmp/rac-overhaul/cr_churn.tsv`
- Test merge: `/tmp/rac-overhaul/src/rac-scratch` (scratch clone, not the rac repo)

## Verification

Fact-checked 2026-10-25 against the clones in `/tmp/rac-overhaul/src/`
(helium `f29a259`, helium-macos `9aa975a` = tag `0.20.1.1`, helium-services
`110144e`; all match the commits cited above), `gh api`, raw Chromium files
at the 154 and 156 tags, HTTP HEAD requests, and the official pages named
below. My scratch files are in `/tmp/rac-overhaul/verify/`. Verdicts:
**OK** = matches the primary source; **FIXED** = was wrong and is now
corrected above; **RETAGGED** = moved to a different tag.

### Claims checked

| # | Claim | Verdict | How I checked |
| --- | --- | --- | --- |
| 1 | Pins: core `f29a259` at Chromium 156.0.8078.47; rac's core pin `76141e1` | OK | `chromium_version.txt`; `gh api repos/imputnet/helium-macos/contents/helium-chromium?ref=0.18.2.1` |
| 2 | Version scheme `0.<major − 136>.<rev>.<platform rev>` | OK | H: `utils/helium_version.py` L14, L51-63; `version.txt` = 0 |
| 3 | Licenses: browser GPL-3.0, services AGPL-3.0, ungoogled code BSD-3 | OK | H: `README.md` L106-113; HS: `README.md` L45-46 and `LICENSE`; `gh api` SPDX ids |
| 4 | Stars, repo ages | OK / FIXED | Stars drifted by 2 (21,985). Only `helium` and `helium-macos` date from 2025-02-15; the other repo dates were added |
| 5 | 134 macOS releases; 26 in 90 days | FIXED | `gh api --paginate .../releases`: 134 total, but 25 in 2026-07-27..2026-10-25 |
| 6 | New Chromium majors ship 2-4 days after Chrome stable | OK | Release API dates; Chrome 153 stable 2026-09-08 ([developer.chrome.com](https://developer.chrome.com/blog/chrome-two-week-release)); Chrome 156 stable 2026-10-20 and 157 due 2026-11-03 ([chromestatus](https://chromestatus.com/release-notes/156)). Chrome 154 and 155 dates follow from the two-week rule; I did not fetch them separately |
| 7 | Two maintainers; outside PRs rarely land | OK, sharpened | All 169 merged PRs since 2026-07-25: 166 by `dumbmoron`/`wukko`. Org bio and sponsor page both say two people. Blaise = `Ahrotahn` (commit `ffeb45a2`) |
| 8 | PRs #2367 and #2776 "closed unmerged" | FIXED | Issue events: #2367 was closed by its own author after ~7 weeks with one maintainer comment and no review; #2776 was closed by `dumbmoron` the day after it opened. #2776's feature status changed from "planned" to "absent" |
| 9 | Consent gate: `services.enabled` (true) AND `services.user_consented` (false) | OK | H: `services-prefs.patch` L417, L529-531; `onboarding-page.patch` L15-16, L31, L676-679 |
| 10 | Override accepts only HTTPS or localhost; schema version 1 | OK | `services-prefs.patch` L502, L743 |
| 11 | Extension proxy: pool 2,048, `ceil(2*(1+log2(n)))` decoys, RAM 4/8/16, fresh UUIDs, shuffle | OK | HS: `mixins.ts` L11, L68; `request.ts` L74-76, L93-96 |
| 12 | Arc importer: Top Apps → bookmark bar; pinned → bookmarks in a folder named by space ID, "Personal" for default | OK | H: `add-arc-importer.patch` L166-206, L288-330, L453 (`virtual void ImportBookmarks()`). Only the first Top Apps container is read |
| 13 | Sync vault: disabled feature, 17 patches, ~8,900 lines | OK (commit count FIXED 21 → 22) | `api.patch` L7; `patches/series` grep; 8,920 lines; `gh api commits?path=patches/helium/core/sync&since=2026-09-01` |
| 14 | Motion table (frameless 200 ms `FAST_OUT_SLOW_IN_3`, 6 px / 8 px, 150 / 3,000 ms; toast 300/150/50 ms; progress 180/700/320 ms; drop target 300 ms and 500 ms timers; favicon 250 ms; bubble 2,500 / 300 ms) | OK | Each cited patch line read. Vertical tabs 250 ms OK, but Chromium's comparison was incomplete (collapse is 250 or 350 ms): FIXED |
| 15 | Reduced motion zeroes `RichAnimationDuration` | RETAGGED INFERENCE → FACT | Chromium 154 tree: `ui/gfx/animation/animation.cc` L114-116, `animation_mac.mm` L15-17, L41 |
| 16 | Shape tokens (8 / 17 / 12 / 7 / 8 px, padding 14) and indigo tone 50 `#516BEC` | OK | `frame-radius-helper.patch`, `layout-provider.patch`, `helium-color-scheme.patch` |
| 17 | Native frame materials: disabled feature; Sidebar (dark) / Menu (light); behind-window blending | OK | `native-frame-materials.patch` L19, L51, L98-101, L307-309, L371 |
| 18 | Series sizes: 346 core patches (~91k lines, vendor split as listed), 23 macOS (~4.8k), 180 rac (~110.7k); core touches 1,645 files and creates 195 | OK | Recounted from `patches/series` and `+++`/`--- /dev/null` headers |
| 19 | Patch flags: `-p1 --ignore-whitespace --forward`, fuzz on by default, `--fuzz=0` for dry run and bump bot | OK | H: `utils/patches.py` L93-103, L132-145, L240-243; bump action L92-93 (`--no-fuzz`) |
| 20 | rac coupling: 871 hunks on 217 upstream files; 134 shared with Helium carrying 629; 8 Helium-created files with 20 hunks; 325 new rac files; 320 hunks in `ui/views` | OK | Recomputed. Note: rac patches mix `b/` and `src/` path prefixes; both must be stripped or the counts come out wrong (1,301 / 334) |
| 21 | CI: sanity fails on any offset and passes on timeout 124; 10 chained phases; 6 h − 1 h; `timeout -k 7m`; plain `tar -c` piped to `zstd -11`; prerelease via `imputnet/action-gh-release@v2.5`; bump bot flow | OK | HM: `sanity-check.sh` L44-54; `building.yml` L46-140; `github_build.sh` L11, L18-27; `github_prepare_artifacts.sh` L82; `build.yml` L75, L79; H: `bump-platform/action.yml` L60-118 |
| 22 | 0.20.1.1 build run: all `depot-macos-latest`; arm64 2 phases, x86_64 3; 14 h 21 min end to end | OK | `gh api .../runs/39651879454/jobs`. Phase times match to the minute; run spans 18:20:48 to 08:41:02 (14 h 20 min) |
| 23 | Depot M4, 8 CPU, 24 GB, 400 GB, $0.08/min; WebDAV endpoint preset; $20/month plan; open-source terms unpublished. GitHub `macos-latest` 3 M1 CPU, 7 GB, 14 GB | OK | [Depot runner types](https://depot.dev/docs/github-actions/runner-types), [Depot sccache](https://depot.dev/docs/cache/reference/sccache), [Depot pricing](https://depot.dev/pricing), [GitHub runners](https://docs.github.com/en/actions/reference/runners/github-hosted-runners). The cost estimate (~$99 both arches, ~$34 arm64) is re-derived arithmetic and stays INFERENCE |
| 24 | Prepared tarballs 1.98 / 1.39 / 1.43 GB; Google lite 2.01 GB; Chrome 157 tarball exists | OK | HTTP `content-length`; `gh api repos/imputnet/chromium-tarballs/releases` |
| 25 | Sparkle: deltas against last 5 releases; DMG 113 / 130 MB; deltas 18-53 MB | FIXED (deltas 40-53 MB) | HM: `generate_sparkle_deltas.py` (`per_page=5`); 0.20.1.1 asset sizes in bytes |
| 26 | Feed URL, product dir `net.imput.helium`, Keychain "Helium Storage Key" | OK | H: `add-updater-preference.patch` L54-57; HM: `change-product-dir-name.patch` L14, `change-keychain-name.patch` L14 |
| 27 | Privacy policy: logs ≤ 24 h, crash reports 30 days, third-party builds excluded, Plausible; crash access limited to the imputnet org | OK | [helium.computer/privacy](https://helium.computer/privacy) (revision 2026-07-16). The org-access rule is in HS: `svc/minidumpster/README.md` L17-19, not in the policy |
| 28 | Bangs 10,730 entries; "13,000+" likely counts triggers | RETAGGED FACT/CLAIM → FACT | Counted 10,730 entries and 13,421 triggers |
| 29 | AGENTS.md and CONTRIBUTING.md policy wording | OK | H: `AGENTS.md` L1-13; `CONTRIBUTING.md` L19-20, L36-37, L144 |
| 30 | AI removal (~1.45 MiB) arrived in 0.19.3.1 | OK | Commit `aec023c` message; `gh api compare` shows it is not in 0.19.2.1's core and is in 0.19.3.1's |
| 31 | 0.18.2.1 → 0.20.1.1: six tags, 85 core commits, 277 patch files (9 added, 6 deleted), 32 macOS files | OK | `git diff --name-status 76141e1 f29a259 -- patches` (277 includes `series`); `gh api compare`; tag list. The maintainer brief says "seven releases ahead"; six tags is correct |
| 32 | Dry-run table and per-group failures | OK (logs only) | Re-summed `/tmp/rac-overhaul/dryrun/*/log/rac.tsv`; every row matches. Group counts include 3 patches that fail only on moved files. I did not re-run the dry run or re-derive the "46 first-failure hunks" |
| 33 | Test merge conflicts only in `patches/series`; Helium deleted `fix-window-resize-jank.patch`; `SetZenModeFloatingStyleForLayout` gone | OK | `git ls-files -u` in `rac-scratch`; HM series at both tags; grep of H at both pins |
| 34 | Chromium moves and the "Unified Tabstrip" commit | FIXED | The moves are real, but `8277d76b10` moved only `new_tab_button_menu_model`, not the style files |
| 35 | Actor churn: `type_tool.cc` 332 lines; `ExecutionObservationDelay` removed | OK | Raw files at both tags: 146 added + 186 removed; method present in 154 `tool_base.h` L98, absent in 156 |
| 36 | Cmd+S "toggles vertical tabs" | FIXED | It collapses or expands the strip, only in the Vertical layout and behind a pref; otherwise Save Page (`shortcuts.patch` L21, L50-54, L74-88) |
| 37 | "rac already calls `ShouldUseNativeFrameMaterials` 9 times" | FIXED | 9 mentions, but 1 added call, 4 removals, 4 context lines |
| 38 | "81 locales … with native reviewers" | FIXED | Only 12 of 81 languages name a reviewer in `i18n/owners.yml` |
| 39 | Sponsor page "no paid features" quote | FIXED | Replaced with the page's exact wording |
| 40 | "No rac-owned script calls the deleted scripts" | FIXED (clarified) | True for `devutils/rac/`, but rac's inherited CI calls `retrieve_and_unpack_resource.sh` (R: `.github/scripts/sanity-check.sh` L16-17, `sanity.yml` L42). The scratch merge replaces those lines cleanly |
| 41 | rac file citations (`overview.md` L69, `upstream-sync.md` L78, roadmap L64, `edge-reveal.patch` L9-10 350 → 100 ms) and `ci-status.md` tar finding | OK | Read each line. The tar root cause is rac's own finding (PR #20, still open), not re-tested |

### Not verified (left as tagged)

- Marketing claims on helium.computer: no Widevine, zero requests on first
  launch, mobile "Not yet". They stay CLAIM.
- User reports #1971, #1887, #2733 and the two reviews. Not opened.
- Most feature-table rows that only cite a patch name (MRU, hover cards,
  PWA toolbar, importers for Zen, toasts). Spot checks only.
- helium-services deploy details (minipush, sparkler, release-collector,
  Ansible, BGP). Not read.
- Onboarding flow steps and the macOS 27 Files & Folders behavior. Only
  the commit title was checked.
- Tom's Hardware claim that macOS 27 is Apple-silicon only. Not fetched.

### Overall confidence

High for code-derived facts: patch contents, constants, counts, CI
mechanics, and release and run data. Every load-bearing number I recomputed
matched, except the fixes listed above. Most fixes were wording or
off-by-one problems. Three changed meaning: the PR narratives (#2367,
#2776), the 9 native-material "calls", and the "native reviewers" claim.
None of the fixes changes the dossier's main conclusions: the sync is
mostly mechanical except the sidebar, Depot explains Helium's CI speed, and
upstream contribution is closed. Medium for the dry-run results, which I
confirmed against the logs but did not re-run. Medium for the Depot cost
estimate, which is arithmetic on one run.
