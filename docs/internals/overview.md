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
| `patches/series` | Shared | Ordered list of macOS-layer patches. Helium's entries come first. rac's entries go last, under `# rac`. |
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
directory's `series` file sets the order. Blank lines and lines starting with
`#` are ignored. After patching, Helium runs name and domain substitution and
copies resources into the tree.

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
7. Run `he unmerge`, check that the new entry sits under `# rac` at the end
   of `patches/series`, then commit the patch together with the series change.
   The `# rac` comment doesn't exist until the first rac patch. Add it on the
   line directly above that patch's entry.

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

rac currently still builds and identifies itself as Helium. This includes the
app name, bundle ID (`net.imput.helium`), keychain name, data directory, and
icons. Rebranding is planned as its own `rac/branding/` patch group plus rac
icons in `resources/`. It must give rac a separate bundle ID and data directory
so rac and Helium can be installed side by side.

The build also still talks to Helium's servers. Until rac patches change this,
treat it as a blocker for sharing builds with anyone:

| What | Where it's set | Why it matters |
| --- | --- | --- |
| Update checks (`updates.helium.computer`) and Sparkle | `helium-chromium/patches/helium/core/add-updater-preference.patch`, `patches/helium/macos/updater/` | A rac install could update itself into Helium. |
| Crash reports (`crash.helium.computer`) | `helium-chromium/patches/helium/core/crash-reporting-prefs.patch` | rac crashes would go to Helium. |
| Helium services (`services.helium.imput.net`) | `helium-chromium/patches/helium/core/services-prefs.patch` | Extension downloads and other features use Helium's infrastructure. |
| Apple team ID and signing identity | `helium-chromium/patches/helium/core/change-chromium-branding.patch`, `sign_and_package_app.sh` | Builds are configured for imput's Apple account. |

The [roadmap](../roadmap.md) tracks this work in phase 1.
