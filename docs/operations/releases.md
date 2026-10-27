# Releases

rac is released from GitHub Actions with the **Build macOS binaries of
Helium** workflow (`.github/workflows/build.yml`). It builds Apple Silicon
by default (Intel or both are options), signs and packages each disk image,
writes the update feeds, and publishes a GitHub release. Installed copies
of rac find the new version through that release. How updates work, and why,
is in [internals/overview.md](../internals/overview.md#versions-and-updates).

The build phases only compile. They run on the **Runner** input's machine
and get no signing or notarization secrets; the phase that finishes uploads
the unsigned app. A last `sign` job in `building.yml`, always on GitHub's
own `macos-latest`, then:

1. checks the binaries for rac's developer switches (the G6 gate, below);
2. imports the certificate into a temporary keychain, which is deleted
   when the job ends, even if it fails;
3. signs, notarizes and staples the app, packages the disk image, then
   signs, notarizes and staples the disk image too;
4. mounts the disk image and checks it (`codesign --verify --deep
   --strict`, `spctl` saying `Notarized Developer ID` for the app and the
   disk image, `stapler validate`, the signing team, and no entitlement that
   needs a provisioning profile it doesn't have). The mount has no
   quarantine flag, so this doesn't replay a first launch from a browser;
5. makes the update deltas.

The release job also runs on GitHub's runner, because it holds the update
signing key. So moving the compile to another provider never moves a key.
Before it writes the update feeds, it runs the same disk image check on every
downloaded image (notarized builds only), so an artifact swapped after the
`sign` job isn't signed into a feed.

The one thing a build phase learns about the entitlements profile is whether
it exists: the `settings` job in `building.yml` turns that into a plain
`true` or `false` for `RAC_BRANDED_ENTITLEMENTS`. The profile itself only
reaches the `sign` job.

## One-time setup

1. Make an update signing key:
   ```sh
   python3 -m venv /tmp/sparkle-venv
   /tmp/sparkle-venv/bin/pip install cryptography
   /tmp/sparkle-venv/bin/python devutils/rac/sparkle.py keygen
   ```
   Keep a copy of both lines somewhere safe, such as a password manager. If
   the private key is lost, every installed copy of rac stops accepting
   updates, and people have to download rac again by hand.
2. Add these repository secrets in GitHub (**Settings > Secrets and
   variables > Actions**):

   | Secret | Value |
   | --- | --- |
   | `PROD_MACOS_SPARKLE_ED_PUB_KEY` | The key after `public:` from `keygen`, without the label |
   | `RAC_SPARKLE_ED_PRIVATE_KEY` | The key after `private:` from `keygen`, without the label |

3. For signed and notarized builds, add the Apple Developer secrets too:
   `PROD_MACOS_CERTIFICATE` (the Developer ID certificate as base64 `.p12`),
   `PROD_MACOS_CERTIFICATE_PWD`, `PROD_MACOS_CERTIFICATE_NAME`,
   `PROD_MACOS_CI_KEYCHAIN_PWD` (any new password),
   `PROD_MACOS_NOTARIZATION_APPLE_ID`, `PROD_MACOS_NOTARIZATION_TEAM_ID`, and
   `PROD_MACOS_NOTARIZATION_PWD` (an app-specific password). Only the
   `sign` job reads them. Without them, CI signs ad hoc, and macOS blocks
   the first launch of the downloaded app until it's allowed in **System
   Settings > Privacy & Security**. Updates still work, because Sparkle
   checks rac's own signature.
   `PROD_MACOS_SPECIAL_ENTITLEMENTS_PROFILE_B64` (a base64 provisioning
   profile) is optional; without it the build has no branded entitlements,
   so passkeys saved with Touch ID or in iCloud Keychain, and other features
   that need keychain access groups, are unavailable.
   Before adding it, set `MAC_TEAM_ID` in `rac/branding/identity.patch`
   (it's empty), or the app claims an application identifier with no team
   and won't launch. The `sign` job fails on that rather than ship it.

Never change the signing key once rac is released. Builds only accept updates
signed with the key they were built with.

## The website

Do this once, when the first release is out. Until then the site's
download page is hidden and shows sample data.

1. Set `RELEASE_READY` to `true` in `site/src/config.ts`. The download
   buttons and the nav then go to `/download`, search engines may index it,
   and it shows the latest release instead of sample data.
2. Add a `GITHUB_TOKEN` environment variable to the Vercel project: a
   fine-grained token with no permissions beyond public repositories. The
   site reads the latest release from GitHub's API at build time, and
   without a token, builds share a low rate limit and can fail.
3. Rebuild the site after each release, so the download page shows it. In
   Vercel, create a deploy hook for `main` (**Settings > Git > Deploy
   Hooks**), save its URL as the repository secret `VERCEL_DEPLOY_HOOK`,
   and add a last step to the release job in `.github/workflows/build.yml`:
   ```yaml
   - name: Rebuild the website
     run: curl -fsS -X POST "${{ secrets.VERCEL_DEPLOY_HOOK }}"
   ```

## Making a release

1. Raise the version in `rac_version.txt` and commit it. Use a patch bump
   (`0.1.1`) for fixes, a minor bump (`0.2.0`) for features or a Helium
   sync. The workflow stops if the version isn't higher than every earlier
   release.
2. In GitHub, open **Actions > Build macOS binaries of Helium > Run
   workflow**, choose `main`, and check **Create a release after build is
   done**. **Architectures** defaults to `arm64`; choose `x86_64` or `both`
   to build Intel too. A full build takes several hours per architecture. One
   architecture failing doesn't cancel the other. If a build phase can't
   download the previous phase's checkpoint, it retries twice before failing.
   If only the `sign` job fails (a notarization timeout, say), use **Re-run
   failed jobs**: the unsigned app is kept, so nothing is compiled again.
3. When it finishes, check the new release. It should have a disk image and
   `appcast-<arch>.xml` for each architecture you built, and a `.delta` file
   from each of the last few releases (none on the first). A release only
   has the feeds of the architectures it built, so installed copies of an
   architecture that was left out stop seeing updates until a release
   includes it again. It's tagged with the version, such as `0.1.1`, on the
   commit the workflow was started from.
4. Open <https://racbrowser.com/download> and check that it shows the new
   version.

Installed copies check the feed at launch and then hourly, download the update in
the background, and install it when rac quits. The feed's address
(`notkainoa/rac`) is built into rac, in `rac/updates/update-feed.patch`.

Don't mark a release as a prerelease or a draft. GitHub's `latest` link
skips them, so nobody would get the update.

### The developer-switch gate (G6)

Release builds must not contain rac's developer switches
(`--rac-agent-debug`, `--rac-agent-mcp-echo`, `--rac-window-screenshot`,
`--rac-launch-in-background`). Before signing, the `sign` job runs
`.github/scripts/github_check_release_binary.sh`, which reads every Mach-O
file in the app with `strings` and names each binary and match it finds.

The workflow's **Developer switches (G6)** input decides what a match does:
`warn` (the default) annotates the run and carries on; `enforce` fails the
build. It stays `warn` until the switches are compiled only into dev builds;
then change the input's default in `build.yml` to `enforce`.

## Testing an update locally

Dev builds don't include the updater. To try a change to it:

1. Make a throwaway key with `/tmp/sparkle-venv/bin/python
   devutils/rac/sparkle.py keygen` (the venv from the one-time setup).
2. Add to `build/src/out/Default/args.gn`:
   ```
   enable_sparkle=true
   sparkle_ed_key="<public key>"
   ```
   Then build. Remove the lines and rebuild when you're done.
3. Make a newer copy of `rac.app`: raise `CFBundleVersion` and
   `CFBundleShortVersionString` in its `Info.plist`, run `codesign --force
   --deep --sign -` on it, and put it in a disk image with `hdiutil create`.
4. Write a feed for it, with the private key in
   `RAC_SPARKLE_ED_PRIVATE_KEY`:
   ```sh
   /tmp/sparkle-venv/bin/python devutils/rac/sparkle.py appcast --arch arm64 --dmg <dmg> \
     --base-url http://127.0.0.1:8765/ --version <new version> \
     --out <folder>/appcast-arm64.xml
   ```
   Serve it with
   `python3 -m http.server 8765 --bind 127.0.0.1 --directory <folder>`.
5. Copy the current `rac.app` to another name inside
   `build/src/out/Default` (the copy only works there, because the dev
   build loads its libraries from that folder). Launch it with a throwaway
   profile and the local feed:
   ```sh
   build/src/out/Default/<copy>.app/Contents/MacOS/rac --user-data-dir=/tmp/<profile> \
     --custom-update-server-url=http://127.0.0.1:8765/
   ```
6. Quit the copy once About rac says to relaunch. Don't click **Relaunch**:
   it starts rac without `--user-data-dir`, which opens the real profile.

Sparkle stores its state in the `me.kainoa.rac` defaults and in
`~/Library/Caches/me.kainoa.rac`. Afterward, remove the `SU*` keys
(`defaults delete me.kainoa.rac SULastCheckTime`, and so on) so a later
test starts fresh.
