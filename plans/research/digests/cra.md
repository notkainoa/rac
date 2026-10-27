# Cra: digest

Full dossier: `plans/research/cra.md`. Researched 2026-10-27 from the repo
(`VictorKildahl/cra`, commit `94c3034`), the CEF repo, the GitHub API, and
crabrowser.app. I did not run Cra. Tags: FACT (primary source), CLAIM
(self-report), INFERENCE (my reasoning).

## In plain English

Cra is a free, open-source Mac browser that copies Arc closely. It is a Swift
app that wraps Chromium through CEF, a library built to embed Chromium in other
apps. The author builds the engine on their own Mac and downloads it in CI.
Cra adds only 5 small patches to Chromium. That looks cheap next to rac's
roughly 180. It is not free, though. CEF itself carries 118 patches touching
about 470 files, and someone else maintains them. Cra pays instead at the seam,
with private-API hacks and a loss of Helium's privacy patches. It is three
days old, with 14 releases, one developer, and Claude co-authoring most
commits. It has no AI, no sync, and a domain-list ad blocker. Take its Arc
import and its exact Arc measurements. Do not copy the engine choice.

## Key facts

**Engine (the key question).**
- FACT: CEF `156.0.14` (Chromium 156.0.8078.48), pinned in one line of
  `scripts/fetch-cef.sh`. Not the content API, not a stock prebuilt, not a fork.
- FACT: default mode is CEF's Chrome-style runtime. **Every tab is its own
  frameless Chrome window**, attached as a child of one AppKit window and moved
  to follow the sidebar card. An embedded-NSView ("Alloy") mode is the fallback.
  Chrome style is needed for extensions and Chrome DevTools.
- FACT: Cra builds its own CEF (H.264/AAC on) on the author's Mac, about 80 GB
  and hours, and uploads it as a GitHub pre-release (135 MB). CI downloads it.
- FACT: a daily workflow compares the pin with Spotify's CEF index and opens an
  issue with the command to run. Building is manual. The 154-to-156 jump took
  one afternoon on 2026-10-26 (engine builds 5.5 h apart; v0.1.10 shipped after).

**Patch surface compared with rac.**
- FACT: Cra's own patches are 5 files of patch, 11 hunks, 6 Chromium files, 195
  lines. They fix extension window type, extension install crash, a CORS
  `Origin` header for 1Password, the keychain item name, and the passkey group.
- FACT: CEF's own patches on Chromium are 118 files, 475 file diffs (473
  distinct files), 1,044 hunks. rac's are about 870 hunks in about 216 files.
- INFERENCE: Cra did not remove the patch surface. It put most of it under CEF
  and kept a thin, documented seam. The cost moved into the Swift shell:
  swizzles of private AppKit/Chromium methods (window corners, hover across
  sibling windows, accessibility focus), no tests.
- FACT (`ardia.md`): Ardia started on CEF Chrome style on 2026-09-25, said "Most
  of our fighting is with CEF, not with Chrome" on 2026-10-01, and had removed
  CEF by 2026-10-09. Cra's patches and swizzles are the same fights.

**UI and motion.** FACT: AppKit for windows, layout, and animation; SwiftUI for
sidebar, command bar, and settings. Fitted-to-Arc values: sidebar hide 0.085 s
bezier (0.15, 0.7, 0.3, 1); space settle `interpolatingSpring(duration 0.4,
bounce 0)` with release velocity; row moves `snappy(0.22)`; split pane add and
remove has no animation; sidebar default 328 pt, row 40 pt, command bar 766 pt;
blur lift 0.35 and dim 0.36. No Reduce Motion handling found.

**Data.** FACT: no database, no server. One `JSONStore<T>` class writes
`sidebar.json`, `archive.json`, `windows.json`, `settings.json`, `history.json`,
`commandbar.json`, `keybindings.json` in `~/Library/Application Support/Cra/`.
Atomic writes, 0.4 s debounce, one `.bak`, corrupt file moved aside. Item model
is Arc's: flat dictionary of items with child lists; `tab | folder | container |
split`; containers `favorites | pinned | today` per space. The site's
"timestamped backups" is wrong (code keeps one `.bak`).

**Arc import (exact reads).** FACT: `Arc/StorableSidebar.json` (spaces, items,
`topApps` favorites, `containerIDs`, `customInfo.iconType`, `windowTheme`
blended gradient), `SidebarItemsFaviconCache/<md5(id)>`, `StorableArchiveItems.json`
(newest 1,500), `StorableWindows.json` (sidebar width), `StorableLinkRouting.json`
(Air Traffic Control rules), `defaults` keys `topBarURLEnabled` and
`autoArchiveTimeThreshold`, and Arc's Chromium profile for passwords, cookies,
extensions (Keychain "Arc Safe Storage"). Dia: `StorableProfileContainers.json`,
`User Data/*/Bookmarks`, `StorableAutoArchive.json`. Same-name spaces merge,
duplicates skip, so it is safe to rerun. Credentials are re-encrypted and staged
(mode 0600), then written before Chromium opens its databases.

**Blocker.** FACT: a CEF `OnBeforeResourceLoad` handler cancels third-party
subresource requests to 22,513 bundled domains (AdAway + Anudeep). Lock-free
atomic set, approximate eTLD+1. INFERENCE: no cosmetic rules, no path rules, no
first-party ads, no updates between app releases. Much weaker than Helium's
uBlock Origin.

**Extensions.** FACT: Chrome Web Store install, unpacked folders, import from
Chromium/Arc/Dia. Unpacked ones load with `--load-extension` at launch. Cra
draws its own toolbar buttons and triggers them through a private
`--remote-debugging-pipe` (`Extensions.triggerAction`). Native-messaging host
manifests are symlinked from other browsers so 1Password and Bitwarden desktop
apps connect.

**Release and updates.** FACT: tag push runs signing, notarization, stapling,
DMG, EdDSA-signed Sparkle 2 appcast, and `gh release create`. Updates check
GitHub every 8 hours, install on quit or after idle. 14 releases, about 400 DMG
downloads in 3 days. CI builds only; no tests exist. FACT: the privacy page says
Cra "does not check for updates," but Sparkle does.

**Maturity.** FACT: created 2026-10-24, 27 commits by one author (23 with
`Co-Authored-By: Claude`), 49 stars, 0 open issues. Two real security faults were
fixed in 0.1.11: a public mock-keychain key protected cookies and passwords, and
web pages could call `cra://` scripting.

**No AI or agent.** CLAIM and FACT: none, and "not planned." `cra://` URL
scheme drives actions; external links reach only `commandbar`, `dismiss`, `open`;
the rest needs a `defaults` flag. Raw DevTools calls exist behind that flag.

## What rac should take

1. **Arc import**, using the exact key paths above (rac has none). Reader in C++
   or a helper; paths transfer unchanged. Add Dia, Zen, Chromium browsers.
2. **Credential import pattern:** Keychain secret via the macOS prompt, PBKDF2
   and AES-128-CBC "v10", stage encrypted rows, insert before the database opens.
3. **Release pipeline shape:** tag-triggered, secrets-optional, stable asset
   names, appcast signed in the same job, retry on stapling. Compare with
   `docs/operations/releases.md`.
4. **Daily engine-update detector** that opens an issue with the exact command.
   For rac: watch helium-macos releases (read-only; post nothing upstream).
5. **Motion numbers** from the table, especially the 85 ms sidebar curve, the
   zero-bounce space settle, `snappy(0.22)` rows, and no animation for split
   pane changes. The method is also worth copying: fit to captured frames, write
   the result in a comment.
6. **A hunk budget** for rac, since Cra's 11-hunk set shows what a thin seam
   looks like. Add a CI check that counts hunks per area.
7. **Lazy tab runtime and archive-with-reason.** Searchable archive feeding the
   command bar.
8. **Native-messaging host linking**, with a deliberate exclusion list.
9. **An allow-listed external scripting door** for rac's outside-agent plan: three
   safe verbs by default, everything else behind an explicit switch.

## What rac should avoid

1. **Do not move rac to CEF.** It would drop Helium's privacy patches and the
   in-process UI, add per-tab windows and private-API swizzles, and still leave a
   patch surface (CEF's is larger than rac's). Ardia tried it and left.
2. **Do not ship without the renderer sandbox.** FACT: Cra sets
   `no_sandbox = true`, builds CEF with `USE_SANDBOX=OFF`, and the helper never
   initializes a sandbox. INFERENCE: a renderer exploit gets the user's full
   rights. The site does not say so.
3. **Do not put the engine build on one laptop,** and do not binary-patch a
   shipped framework (Cra does this once for the keychain name).
4. **Do not claim "no phone-home" without a network capture.** Cra has none,
   and its own updater contradicts its page.
5. **Do not copy Arc's strings or assets.** Cra's notes mine Arc's binary
   strings and reuse its copy. Copy behavior, not text.
6. **Do not ignore Reduce Motion.**

## Caveats

- I did not run or build Cra, so every look-and-feel claim comes from code and the
  author's notes. The site text came through a summarizing fetch tool, so
  re-check any quote before publishing it.
- Not measured: whether Cra's Chromium contacts Google (Safe Browsing, component
  updater, variations), whether MV2 extensions load, tab-switch latency and
  memory with one window per page. All are open questions in the dossier.
- The CEF patch totals are from CEF's `master` on 2026-10-23, not its 8078
  release branch. They may differ slightly. rac's totals come from the brief and
  `rac-baseline.md`.
- Cra is three days old, one developer, one engine builder. Its numbers
  (speed of releases, 154 to 156 in an afternoon) say little about how it will
  hold up over months.
- `docs/arc-reverse-engineering.md` still says "Cra uses WKWebView," and the site
  says favorites are shared across spaces; both are stale. Trust the code.
