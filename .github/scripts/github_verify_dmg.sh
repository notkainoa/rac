#!/bin/bash
# Checks a packaged rac disk image the way a downloading Mac will: mounts it
# read-only and verifies the app's signature, its entitlements and, for a
# Developer ID build, Gatekeeper's verdict and the stapled tickets on both the
# app and the disk image.
#
# Usage: github_verify_dmg.sh <path/to/rac.dmg>
#
# Environment:
#   RAC_EXPECT_NOTARIZED  1 for a Developer ID build (the default), 0 for an
#                         ad hoc build, which only gets the signature and
#                         entitlement checks.
#   RAC_EXPECT_TEAM_ID    When set, the app must be signed by this team.

set -eu -o pipefail

_dmg="${1:?usage: $0 <path/to/rac.dmg>}"
_notarized="${RAC_EXPECT_NOTARIZED:-1}"
_team="${RAC_EXPECT_TEAM_ID:-}"

_mnt=$(mktemp -d "${TMPDIR:-/tmp}/rac-dmg.XXXXXX")
_detach() {
  hdiutil detach "$_mnt" -quiet || hdiutil detach "$_mnt" -force -quiet || true
  rmdir "$_mnt" 2>/dev/null || true
}
if ! hdiutil attach "$_dmg" -readonly -nobrowse -noautoopen -mountpoint "$_mnt" -quiet; then
  echo "::error::Could not mount $_dmg"
  rmdir "$_mnt" 2>/dev/null || true
  exit 1
fi
trap _detach EXIT

_app="$_mnt/rac.app"
if [ ! -d "$_app" ]; then
  echo "::error::$_dmg has no rac.app at its top level"
  exit 1
fi

echo "== codesign --verify --deep --strict (app)"
codesign --verify --deep --strict --verbose=2 "$_app"

_signer=$(codesign -dv "$_app" 2>&1 || true)
_app_team=$(sed -n 's/^TeamIdentifier=//p' <<< "$_signer")
echo "App team identifier: ${_app_team:-none}"

# An app that claims a restricted entitlement without a provisioning profile
# that grants it is killed at launch, and notarization doesn't catch that.
echo "== entitlements (main executable)"
codesign -d --entitlements - --xml "$_app" 2>/dev/null > "$_mnt.entitlements.plist" || true
_has_profile=0
[ -f "$_app/Contents/embedded.provisionprofile" ] && _has_profile=1
python3 - "$_mnt.entitlements.plist" "$_has_profile" "$_app_team" <<'EOF'
import plistlib
import sys

path, has_profile, team = sys.argv[1], sys.argv[2] == '1', sys.argv[3]
try:
    with open(path, 'rb') as f:
        data = f.read()
    entitlements = plistlib.loads(data) if data.strip() else {}
except Exception as e:  # A malformed blob is a failure, not "no entitlements".
    print(f'::error::Could not read the app entitlements: {e}')
    sys.exit(1)

for key in sorted(entitlements):
    print(f'  {key}')

restricted = [
    key for key in entitlements
    if key in ('com.apple.application-identifier', 'keychain-access-groups')
    or key.startswith('com.apple.developer.')
]
if restricted and not has_profile:
    print('::error::The app claims entitlements that need a provisioning '
          f'profile, and has none, so macOS would refuse to launch it: {", ".join(restricted)}')
    sys.exit(1)

app_id = entitlements.get('com.apple.application-identifier')
if app_id is not None and (team in ('', 'not set') or not app_id.startswith(team + '.')):
    print(f'::error::com.apple.application-identifier is "{app_id}", which does not start '
          f'with the signing team "{team}." (is MAC_TEAM_ID empty in BRANDING?)')
    sys.exit(1)
EOF
rm -f "$_mnt.entitlements.plist"

if [ "$_notarized" != 1 ]; then
  echo "Ad hoc build: skipping Gatekeeper and stapling checks."
  exit 0
fi

if [ -n "$_team" ] && [ "$_app_team" != "$_team" ]; then
  echo "::error::The app is signed by team '${_app_team:-none}', not the notarization team."
  exit 1
fi

echo "== spctl (app)"
spctl -a -vv "$_app"
echo "== stapler validate (app)"
xcrun stapler validate "$_app"
echo "== codesign --verify (disk image)"
codesign --verify --strict --verbose=2 "$_dmg"
echo "== spctl -t install (disk image)"
spctl -a -vv -t install "$_dmg"
echo "== stapler validate (disk image)"
xcrun stapler validate "$_dmg"

echo "Disk image verified: signed, notarized and stapled."
