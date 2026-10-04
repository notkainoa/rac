# rac project overview

rac is a macOS browser built from Chromium in several layers. Each layer is
a set of patches applied on top of the one below. rac is the top layer.

```
Chromium source tarball          (downloaded during setup into build/src)
  + ungoogled-chromium patches   (privacy and de-Googling)       ┐ helium-chromium/
  + Helium core patches          (Helium features and UI)        ┘ submodule
  + Helium macOS patches         (macOS fixes, Sparkle updater)  ┐ this repo,
  + rac patches                  (Arc-style features, branding)  ┘ patches/
```

## Repository layout

| Path | Owner | What it is |
| --- | --- | --- |
| `helium-chromium/` | Helium | Submodule of `imputnet/helium`, the platform-independent core: core patch series, build utilities, translations, and resources. Do not edit. |
| `patches/series` | Shared | Ordered list of macOS-layer patches. Helium's entries come first. rac's `rac/` entries go last, after a blank line. Don't add `#` comments: Helium's lint, which CI runs, reads them as patch names. |
| `patches/helium/`, `patches/rebel/`, `patches/ungoogled-chromium/` | Helium | Helium's macOS patches. Do not edit. |
| `patches/rac/` | rac | rac's patches. |
| `build.sh` | Helium | Full release build: downloads sources, applies all patches, builds, signs, and packages a `.dmg`. |
| `dev.sh`, `devutils/`, `env.sh` | Helium | Development tooling (the `he` command) and shared paths. |
| `resources/` | Shared | macOS app icons, assets, and DMG layout. Mapped into the source tree by `resources/platform_resources.txt`. |
| `flags.macos.gn`, `downloads.ini` | Helium | macOS build flags and extra downloads. |
| `.github/` | Helium | Helium's CI and release workflows, changed to use rac's file names, version, and update feeds. See [Releases](../operations/releases.md). |
| `build/` | Local | Gitignored working area: download cache, the patched source tree (`build/src`), and build output. |

## How patches are applied

`devutils/shared.sh` runs `helium-chromium/utils/patches.py apply`, passing
`helium-chromium/patches` first and then this repo's `patches/`. Each
directory's `series` file sets the order. Blank lines are ignored. Lines
starting with `#` are skipped when patches are applied, but Helium's lint
fails on them, so rac's series has none.

After patching, Helium runs name and domain substitution and applies its
translations. Then rac's name pass runs (see
[Branding](#branding-and-helium-services)), and resources are copied into the
tree.

For development, `he merge` combines both series into
`patches/series.merged` so quilt can manage the whole stack from `build/src`.
`he unmerge` splits it back. A new patch added after the existing macOS
patches ends up in this repo's `patches/series`.

## Making a rac change

Install the requirements in [building.md](../building.md) first.

1. Set up a dev tree once: `source dev.sh && he setup`.
2. Go to `build/src` and make sure all patches are applied
   (`quilt push -a`).
3. Start a new patch: `quilt new rac/<area>/<name>.patch`.
4. Register each file before you modify it: `quilt add <path>`. For new
   files, run `quilt add` before creating them.
5. Edit, then test with `he build && he run`.
6. Save the patch: `quilt refresh`. Format it with `he format`.
7. Run `he unmerge`, check that the new entry sits with the other `rac/`
   entries at the end of `patches/series`, then commit the patch together
   with the series change.

### Patch design for low-maintenance updates

Chromium releases a new major version roughly every four weeks, and Helium
follows quickly. Every rac patch has to be refreshed against each new release.
To keep that cheap:

- Put as much code as possible in new files. A patch that only adds files
  rarely breaks.
- Keep edits to existing Chromium files to small hooks: an include, a
  registration call, a build-file entry.
- Split work by feature (for example `rac/sidebar/`, `rac/spaces/`,
  `rac/command-bar/`, `rac/branding/`) so one broken patch doesn't block
  everything else.
- Build on what Chromium and Helium already have (vertical tabs, side panel,
  split view, Helium's UI) instead of replacing it.
- `chrome/browser/ui/views/` changes often upstream. Expect patches there to
  need the most refresh work.

## Branding and Helium services

`patches/rac/branding/` gives rac its own identity, so rac and Helium can be
installed side by side:

- `rac.app`, bundle ID `me.kainoa.rac`, data directory
  `~/Library/Application Support/me.kainoa.rac`, and keychain item
  `rac Storage Key`. The bundle ID and data directory are permanent once
  people install rac. Changing them strands everyone's profile.
- Internal pages use `rac://` instead of `helium://`. The address bar turns
  `rac://` into `chrome://`, which is what the browser actually loads.
  Automation that navigates directly, such as DevTools, must use
  `chrome://`.
- The Apple team ID is empty until rac has its own developer account.
- The icons are still Helium's.

`devutils/rac/name_pass.py` turns "Helium" into "rac" in user-facing
strings and translations. It runs in release builds after Helium's own pass
(which turns "Chrome" into "Helium"), so it only ever sees Helium's wording.
Phrases about things Helium runs, such as "Helium services" and "Helium
Partner", stay as they are. Translations of those strings keep their text,
because the phrase can't be found reliably in every language.

Dev trees get the same wording. `devutils/rac/dev_names.py sub` runs both
passes on `build/src` and saves the files it changes in
`build/src/.rac_names/`, so `dev_names.py unsub` can put them back.
`devutils/rac/worktree.sh sync` keeps this up to date: it reverts the names
before quilt pops or pushes patches, then applies them again. Applying them
takes about a minute, and the next build redoes the string packs (about 500
steps). Dev trees skip Helium's translations of its own strings, so those
show in English in other languages.

While the names are applied, string files (`.grd`, `.grdp`, `.xtb`) in
`build/src` don't match what the patches expect:

- **Before a patch edits a string file**, run `devutils/rac/dev_names.py
  unsub`. Otherwise `quilt refresh` saves rac's wording into the patch, and
  the patch won't apply in release builds. Run `devutils/rac/worktree.sh
  sync` after refreshing to apply the names again.
- **Don't pop or push patches with plain quilt** while the names are
  applied. Use `worktree.sh sync`, or run `unsub` first.
- **Don't use `he sub` or `he namesub`.** They run only Helium's pass, with
  separate backups.

What still connects to Helium's servers:

| What | Status |
| --- | --- |
| Browser updates (`updates.helium.computer`) | Never. rac checks its own feed on GitHub instead (see [Versions and updates](#versions-and-updates)). Helium's feed would replace rac with Helium. |
| Crash reports (`crash.helium.computer`) | Off, but not removed. `rac/privacy/disable-crash-uploads.patch` only empties the upload URL, makes the mode always "disabled" (so reports are deleted, never offered or sent), and hides the setting. Helium's crash reporting code is untouched, so rac can add its own later (see [Crash reports](#crash-reports)). |
| Helium services (extension downloads, uBlock lists, spell check, bangs, component updates) | Kept as they are, behind Helium's consent screen and labeled as Helium's. The onboarding links to Helium's privacy policy and terms for them. rac may host its own copy later; Helium's server code is open source (`imputnet/helium-services`). |

The [roadmap](../roadmap.md) tracks the rest of this work in phase 1.

### Crash reports

rac may get its own crash reports later. Helium's pieces are all still
there: Crashpad writes the reports, the browser can ask after a crash, and
the settings handler and strings for the "Disabled / Ask after a crash /
Send automatically" choice exist. Turning them back on means replacing
`disable-crash-uploads.patch` with one that returns rac's upload URL and
restores the setting. Helium's crash server (`minidumpster` in
`imputnet/helium-services`) is open source and could be hosted for rac.

How it should work, as the maintainer decided:

- Crash reporting is off by default. Users can turn it on in the
  onboarding, and turn it on or off later in settings.
- When it's on, rac asks after every crash whether to send that report.
  Nothing is ever sent without a yes for that crash. There's no "send
  automatically" choice.

How to build this (the prompt, the server, how long reports are kept) is
for when it's implemented. A crash report can contain parts of the
browser's memory, including pages the user had open, so the server should
keep reports only as long as needed to fix the crash.

## Versions and updates

rac has its own version, `MAJOR.MINOR.PATCH`, in `rac_version.txt`. It's
separate from Helium's version (four parts, such as `0.18.2.1`) and from
Chromium's. `devutils/rac/rac_version.py` writes it into `chrome/VERSION`
during `prepare_sources` and `worktree.sh sync`, and
`rac/updates/version.patch` puts it in the app bundle, `--version`, About
rac, and `rac://version`, next to the Helium and Chromium versions.

The version may only go up. Sparkle installs an update only when the feed's
version is higher than the bundle's, so a release that reuses or lowers a
version is never offered to anyone. The release workflow refuses to run in
that case.

Updates use Helium's Sparkle integration, pointed at rac's own feed:

- **The feed is a GitHub release asset.** Each release uploads
  `appcast-arm64.xml` and `appcast-x86_64.xml`, and rac reads
  `releases/latest/download/appcast-<arch>.xml` from this repo. GitHub's
  `latest` skips prereleases, so releases must not be marked as
  prereleases. rac runs no update server.
- **It doesn't depend on Helium services.** `rac/updates/update-feed.patch`
  replaces Helium's consent check with rac's own setting,
  `rac.browser_updates` (on by default), shown as "Update rac automatically"
  on the About rac page. Helium's services toggle now covers only component
  updates.
- **Updates are signed with rac's EdDSA key.** Builds embed the public key,
  and `devutils/rac/sparkle.py` signs each disk image and delta with the
  private key. Both live only in GitHub secrets. Losing the private key
  means installed copies can't verify any future update, so keep a backup.
- **Dev builds have no updater.** Sparkle is only built when
  `PROD_MACOS_SPARKLE_ED_PUB_KEY` is set, which only CI does. To test the
  updater locally, follow [Releases](../operations/releases.md#testing-an-update-locally).
- **Chromium compares the wrong versions.** Its upgrade detector compares
  the bundle's version with Chromium's, which would always look like an
  update and nag about relaunching. `version.patch` makes it compare with
  rac's version on macOS.
