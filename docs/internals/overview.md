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
| `.github/` | Helium | Helium's CI and release workflows. Not yet adapted for rac. |
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
- Internal pages use `rac://` instead of `helium://`.
- The Apple team ID is empty until rac has its own developer account.
- The icons are still Helium's.

`devutils/rac/name_pass.py` turns "Helium" into "rac" in user-facing
strings and translations. It runs in release builds after Helium's own pass
(which turns "Chrome" into "Helium"), so it only ever sees Helium's wording.
Phrases about things Helium runs, such as "Helium services" and "Helium
Partner", stay as they are. Translations of those strings keep their text,
because the phrase can't be found reliably in every language.

Dev builds (`he build`) skip both name passes, as in Helium. Dev builds show
"Chromium" and Helium's own wording in the UI. That's expected. Check wording
in a release build.

What still connects to Helium's servers:

| What | Status |
| --- | --- |
| Browser updates (`updates.helium.computer`) | Off. `rac/updates/disable-browser-updates.patch` never returns Helium's feed, and Sparkle is only built when CI has a signing key. Helium's feed would replace rac with Helium. |
| Crash reports (`crash.helium.computer`) | Off. `rac/privacy/disable-crash-uploads.patch` removes the upload URL and the setting. |
| Helium services (extension downloads, uBlock lists, spell check, bangs, component updates) | Kept, behind Helium's consent screen and labeled as Helium's. Decide whether to keep them, go direct, or host rac's own before public releases. The onboarding also links to Helium's privacy policy and terms for them. |

The [roadmap](../roadmap.md) tracks the rest of this work in phase 1.
