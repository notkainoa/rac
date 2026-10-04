# Releases

rac is released from GitHub Actions with the **Build macOS binaries of
Helium** workflow (`.github/workflows/build.yml`). It builds both
architectures, packages and signs each disk image, writes the update feeds,
and publishes a GitHub release. Installed copies of rac find the new version
through that release. How updates work, and why, is in
[internals/overview.md](../internals/overview.md#versions-and-updates).

## One-time setup

1. Make an update signing key:
   ```sh
   pip install cryptography
   devutils/rac/sparkle.py keygen
   ```
   Keep a copy of both lines somewhere safe, such as a password manager. If
   the private key is lost, every installed copy of rac stops accepting
   updates, and people have to download rac again by hand.
2. Add these repository secrets in GitHub (**Settings > Secrets and
   variables > Actions**):

   | Secret | Value |
   | --- | --- |
   | `PROD_MACOS_SPARKLE_ED_PUB_KEY` | The `public:` line from `keygen` |
   | `RAC_SPARKLE_ED_PRIVATE_KEY` | The `private:` line from `keygen` |

3. For signed and notarized builds, add the Apple Developer secrets too:
   `PROD_MACOS_CERTIFICATE` (the Developer ID certificate as base64 `.p12`),
   `PROD_MACOS_CERTIFICATE_PWD`, `PROD_MACOS_CERTIFICATE_NAME`,
   `PROD_MACOS_CI_KEYCHAIN_PWD` (any new password),
   `PROD_MACOS_NOTARIZATION_APPLE_ID`, `PROD_MACOS_NOTARIZATION_TEAM_ID`, and
   `PROD_MACOS_NOTARIZATION_PWD` (an app-specific password). Without them,
   CI signs ad hoc, and macOS blocks the first launch of the downloaded app
   until it's allowed in **System Settings > Privacy & Security**. Updates
   still work, because Sparkle checks rac's own signature.

Never change the signing key once rac is released. Builds only accept updates
signed with the key they were built with.

## Making a release

1. Raise the version in `rac_version.txt` and commit it. Use a patch bump
   (`0.1.1`) for fixes, a minor bump (`0.2.0`) for features or a Helium
   sync. The workflow stops if the version isn't higher than every earlier
   release.
2. In GitHub, open **Actions > Build macOS binaries of Helium > Run
   workflow**, choose `main`, and check **Create a release after build is
   done**. A full build takes several hours.
3. When it finishes, check the new release. It should have both disk
   images, `appcast-arm64.xml`, `appcast-x86_64.xml`, and a `.delta` file
   for each recent version. It's tagged with the version, such as `0.1.1`.

Installed copies check the feed about once a day, download the update in
the background, and install it when rac quits. The feed's address
(`notkainoa/rac`) is built into rac, in `rac/updates/update-feed.patch`.

Don't mark a release as a prerelease or a draft. GitHub's `latest` link
skips them, so nobody would get the update.

## Testing an update locally

Dev builds don't include the updater. To try a change to it:

1. Make a throwaway key with `devutils/rac/sparkle.py keygen`.
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
   devutils/rac/sparkle.py appcast --arch arm64 --dmg <dmg> \
     --base-url http://127.0.0.1:8765/ --version <new version> \
     --out <folder>/appcast-arm64.xml
   ```
   Serve the folder with `python3 -m http.server 8765 --bind 127.0.0.1`.
5. Copy the current `rac.app` to another name inside `out/Default` (the
   copy only works there, because the dev build loads its libraries from
   that folder). Launch it with a throwaway profile and the local feed:
   ```sh
   out/Default/<copy>.app/Contents/MacOS/rac --user-data-dir=/tmp/<profile> \
     --custom-update-server-url=http://127.0.0.1:8765/
   ```
6. Quit the copy once About rac says to relaunch. Don't click **Relaunch**:
   it starts rac without `--user-data-dir`, which opens the real profile.

Sparkle stores its state in the `me.kainoa.rac` defaults and in
`~/Library/Caches/me.kainoa.rac`. Afterward, remove the `SU*` keys
(`defaults delete me.kainoa.rac SULastCheckTime`, and so on) so a later
test starts fresh.
