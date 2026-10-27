#!/bin/bash -eux

_root_dir="$(dirname "$(greadlink -f "$0")")"
_app="out/Default/rac.app"
_packaging="out/Default/rac Packaging"

if [ -n "${MACOS_CERTIFICATE_NAME:-}" ]; then
  if [ -n "${PROD_MACOS_SPECIAL_ENTITLEMENTS_PROFILE_PATH:-}" ]; then
    # Chromium embeds this profile from its packaging inputs during signing.
    cp "$PROD_MACOS_SPECIAL_ENTITLEMENTS_PROFILE_PATH" "$_packaging/Helium.provisionprofile"
  fi

  CREDENTIAL_ARGS=(store-credentials notarytool-profile)
  NOTARY_ARGS=(--notary-arg=--keychain-profile=notarytool-profile)
  NOTARYTOOL_AUTH=(--keychain-profile notarytool-profile)
  if [ -n "${CI:-}" ]; then
    CREDENTIAL_ARGS+=("--keychain=$HOME/Library/Keychains/build.keychain-db")
    NOTARY_ARGS+=("--notary-arg=--keychain=$HOME/Library/Keychains/build.keychain-db")
    NOTARYTOOL_AUTH+=(--keychain "$HOME/Library/Keychains/build.keychain-db")
  fi

  # Tracing would print the expanded Apple ID and password.
  { set +x; } 2>/dev/null
  xcrun notarytool \
    "${CREDENTIAL_ARGS[@]}" \
    --apple-id "$PROD_MACOS_NOTARIZATION_APPLE_ID" \
    --team-id "$PROD_MACOS_NOTARIZATION_TEAM_ID" \
    --password "$PROD_MACOS_NOTARIZATION_PWD"
  set -x

  python3 "$_packaging/sign_chrome.py" \
    --input out/Default \
    --output out/Default/signed \
    --identity "$MACOS_CERTIFICATE_NAME" \
    --disable-packaging --notarize \
    "${NOTARY_ARGS[@]}"

  _app="out/Default/signed/stable/rac.app"
else
  echo "warn: MACOS_CERTIFICATE_NAME is missing; skipping notarization" >&2
  codesign --force --deep --sign - "$_app"
fi

if [ -z "${OUT_DMG_PATH:-}" ]; then
  _rac_version=$(python3 "$_root_dir/devutils/rac/rac_version.py" --print)
  OUT_DMG_PATH="$_root_dir/build/rac_${_rac_version}_macos.dmg"
fi

# RAC_DMG_STYLE=beta packages beta builds with the dark background on a
# "rac Beta" volume. Each style's .DS_Store names its own volume, so Finder
# shows the right background when both DMGs are mounted.
_dmg_volume=rac
_dmg_background="$_root_dir/resources/dmg_background.png"
_dmg_dsstore="$_root_dir/resources/dmg_dsstore"
if [ "${RAC_DMG_STYLE:-}" = beta ]; then
  _dmg_volume="rac Beta"
  _dmg_background="$_root_dir/resources/dmg_beta_background.png"
  _dmg_dsstore="$_root_dir/resources/dmg_beta_dsstore"
elif [ -n "${RAC_DMG_STYLE:-}" ]; then
  echo "error: unknown RAC_DMG_STYLE=$RAC_DMG_STYLE (expected beta or unset)" >&2
  exit 1
fi

# The build copies pkg-dmg into the packaging folder, which is all the CI
# signing job has of the source tree.
_pkg_dmg="$_packaging/pkg-dmg"
[ -x "$_pkg_dmg" ] || _pkg_dmg=chrome/installer/mac/pkg-dmg

# Package the app
"$_pkg_dmg" \
  --sourcefile --source "$_app" \
  --target "$OUT_DMG_PATH" \
  --volname "$_dmg_volume" --format ULMO \
  --icon "$_app/Contents/Resources/app.icns" \
  --symlink /Applications:/Applications \
  --mkdir .background \
  --copy "$_dmg_background:/.background/dmg_background.png" \
  --copy "$_dmg_dsstore:/.DS_Store" \
  --verbosity 2

if [ -n "${MACOS_CERTIFICATE_NAME:-}" ]; then
  # Notarization needs a secure timestamp on every signature.
  codesign \
    --sign "$MACOS_CERTIFICATE_NAME" \
    --identifier me.kainoa.rac --force --timestamp \
    "$OUT_DMG_PATH"

  # The app inside is already notarized and stapled. Notarizing the disk image
  # too lets Gatekeeper accept the download itself offline.
  _notary_field() {
    python3 -c 'import json, sys
try: print(json.loads(sys.stdin.read()).get(sys.argv[1], ""))
except Exception: print("")' "$1" <<< "$_notary_json"
  }
  # A submission that Apple judged has a status (Accepted, Invalid, Rejected).
  # No status means the upload or the connection failed, which is worth
  # another try; a verdict is not.
  _notary_delay="${RAC_NOTARY_RETRY_DELAY:-30}"
  for _notary_try in 1 2 3; do
    _notary_json=$(xcrun notarytool submit "$OUT_DMG_PATH" "${NOTARYTOOL_AUTH[@]}" \
      --wait --timeout 2h --output-format json) || true
    echo "$_notary_json"
    _notary_status=$(_notary_field status)
    if [ -n "$_notary_status" ] || [ "$_notary_try" -eq 3 ]; then
      break
    fi
    echo "warn: notarytool submit gave no status (attempt $_notary_try of 3); trying again in ${_notary_delay}s" >&2
    sleep "$_notary_delay"
  done
  if [ "$_notary_status" != Accepted ]; then
    _notary_id=$(_notary_field id)
    if [ -n "$_notary_id" ]; then
      xcrun notarytool log "$_notary_id" "${NOTARYTOOL_AUTH[@]}" || true
    fi
    echo "error: notarization of the disk image ended with status '${_notary_status:-none}'" >&2
    exit 1
  fi

  # Apple's ticket can take a moment to reach the CDN, so stapling right after
  # "Accepted" sometimes fails with 65 (record not found) or 68 (a network
  # error). Chromium's signing/notarize.py retries these the same way.
  _staple_delay="${RAC_STAPLE_RETRY_DELAY:-30}"
  for _staple_try in 1 2 3 4 5; do
    _staple_rc=0
    xcrun stapler staple "$OUT_DMG_PATH" || _staple_rc=$?
    if [ "$_staple_rc" -eq 0 ]; then
      break
    fi
    if { [ "$_staple_rc" -ne 65 ] && [ "$_staple_rc" -ne 68 ]; } || [ "$_staple_try" -eq 5 ]; then
      echo "error: stapler staple failed with exit code $_staple_rc (attempt $_staple_try of 5)" >&2
      exit "$_staple_rc"
    fi
    echo "warn: stapler staple exited $_staple_rc (attempt $_staple_try of 5); trying again in ${_staple_delay}s" >&2
    sleep "$_staple_delay"
  done
fi
