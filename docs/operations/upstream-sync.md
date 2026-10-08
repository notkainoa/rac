# Syncing with Helium

rac follows Helium by merging `imputnet/helium-macos` into this repo. Each
helium-macos update also moves the `helium-chromium` submodule to the Helium
core version it was tested with. Never move the submodule independently.

## Remotes

| Remote | URL | Use |
| --- | --- | --- |
| `origin` | `github.com/notkainoa/rac` | rac's own repo. Push here. |
| `upstream` | `github.com/imputnet/helium-macos` | Fetch-only. Push URL is `no_push`. |

If you have a fresh clone, restore `upstream` with:

```sh
git remote add upstream https://github.com/imputnet/helium-macos.git
git remote set-url --push upstream no_push
```

## Update steps

1. Start from a clean working tree on `main`, with `build/src` patches popped
   (`cd build/src && quilt pop -a`) and unmerged (`he unmerge`).
2. Fetch and merge upstream on a new branch:
   ```sh
   git fetch upstream
   git switch -c sync/helium-<version>
   git merge upstream/main
   git submodule update --init --recursive
   ```
   Merge conflicts should be rare and mostly in `patches/series`. Keep all of
   Helium's new entries, and keep the `rac/` entries at the end.
3. If the Chromium version changed, rebuild the source tree. Run
   `he reset`, then `he presetup` and `he merge`. Otherwise, just run
   `he merge`.
4. Apply and refresh every patch from `build/src`:
   `quilt push -a --refresh`.
   - If a rac patch fails, run `quilt push -f`, fix the rejected parts
     (using `quilt edit` / `quilt add`), run `quilt refresh`, and continue.
   - If a Helium patch fails, the submodule or `patches/` didn't update
     correctly. Don't edit Helium patches to fix it.
5. Finish setup and verify: `he configure`, then `he build && he run`.
   Check that rac's features still work.
6. Pop and unmerge (`he pop`, `he unmerge`), then check consistency with
   `he validate series` and `he validate config`.
7. Commit the refreshed rac patches, then merge the sync branch into `main`.

## Things to watch for

- **`he pull` is for Helium developers.** It rebases the submodule onto
  Helium's latest `main`, which may not match the version helium-macos pins.
  Don't use it in rac.
- **If Helium adds something rac also built,** consider dropping the rac
  patch and building on Helium's version.
- **Helium's CI workflows** in `.github/` come in with every merge. Review
  them before turning on GitHub Actions for rac. `bump.yml` in particular
  runs Helium's submodule bump action, which moves the submodule on its own.

## Upstream files rac replaces

rac has its own version of these helium-macos files. If a merge conflicts in
one of them, keep rac's version and bring over only changes that also make
sense for rac:

- `README.md`
- `.github/PULL_REQUEST_TEMPLATE.md`
- `.github/ISSUE_TEMPLATE/`

rac also changes a few lines in Helium's release files: the `.github/`
release scripts, `.github/workflows/build.yml`,
`devutils/generate_sparkle_deltas.py`, and `sign_and_package_app.sh`. If one
conflicts, take Helium's change and keep rac's file names (`rac_<version>`,
`rac.app`), rac's version from `rac_version.txt`, and the update feed steps
(see [Releases](releases.md)). Also keep certificate import conditional on
`MACOS_CERTIFICATE` being set, and the ad-hoc signing fallback when
`MACOS_CERTIFICATE_NAME` is absent, so builds without Apple secrets work.

Every other helium-macos file stays Helium's. rac-only files (`AGENTS.md`,
`CLAUDE.md`, `VISION.md`, `CONTRIBUTING.md`, `.github/SECURITY.md`,
`docs/README.md`, `docs/roadmap.md`, `docs/internals/`, `docs/operations/`,
`patches/rac/`) don't exist upstream and never conflict.
