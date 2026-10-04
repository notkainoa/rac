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
  if [ -n "${CI:-}" ]; then
    CREDENTIAL_ARGS+=("--keychain=$HOME/Library/Keychains/build.keychain-db")
    NOTARY_ARGS+=("--notary-arg=--keychain=$HOME/Library/Keychains/build.keychain-db")
  fi

  xcrun notarytool \
    "${CREDENTIAL_ARGS[@]}" \
    --apple-id "$PROD_MACOS_NOTARIZATION_APPLE_ID" \
    --team-id "$PROD_MACOS_NOTARIZATION_TEAM_ID" \
    --password "$PROD_MACOS_NOTARIZATION_PWD"

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

# Package the app
chrome/installer/mac/pkg-dmg \
  --sourcefile --source "$_app" \
  --target "$OUT_DMG_PATH" \
  --volname rac --format ULMO \
  --icon "$_app/Contents/Resources/app.icns" \
  --symlink /Applications:/Applications \
  --mkdir .background \
  --copy "$_root_dir/resources/dmg_background.png:/.background/dmg_background.png" \
  --copy "$_root_dir/resources/dmg_dsstore:/.DS_Store" \
  --verbosity 2

if [ -n "${MACOS_CERTIFICATE_NAME:-}" ]; then
  codesign \
    --sign "$MACOS_CERTIFICATE_NAME" \
    --identifier me.kainoa.rac --force \
    "$OUT_DMG_PATH"
fi
