#!/bin/bash
# Checks a packaged rac disk image: mounts it read-only and verifies the app's
# signature, its entitlements and, for a Developer ID build, Gatekeeper's
# verdict (it must say Notarized Developer ID) and the stapled tickets on both
# the app and the disk image. The image has no quarantine flag here, so this
# doesn't show what a first launch from a browser download will do.
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
# A secret pasted with a trailing newline or space would fail the team check.
_team=$(printf '%s' "${RAC_EXPECT_TEAM_ID:-}" | tr -d '[:space:]')

_mnt=$(mktemp -d "${TMPDIR:-/tmp}/rac-dmg.XXXXXX")
_detach() {
  rm -f "$_mnt.entitlements.plist"
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

# --strict=symlinks, not plain --strict: hdiutil's read-only image tags every
# file with com.apple.FinderInfo on macOS 26, and full --strict rejects that
# xattr. Gatekeeper doesn't care, and the signing pipeline already ran the
# full --strict check on the app before packaging.
echo "== codesign --verify --deep --strict=symlinks (app)"
codesign --verify --deep --strict=symlinks --verbose=2 "$_app"

_signer=$(codesign -dv "$_app" 2>&1 || true)
_app_team=$(sed -n 's/^TeamIdentifier=//p' <<< "$_signer")
echo "App team identifier: ${_app_team:-none}"

# An app that claims a restricted entitlement without a provisioning profile
# that grants it is killed at launch, and notarization doesn't catch that.
echo "== entitlements (main executable)"
if ! codesign -d --entitlements - --xml "$_app" 2>/dev/null > "$_mnt.entitlements.plist"; then
  echo "::error::Could not read the app entitlements from $_app"
  exit 1
fi
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

# Gatekeeper's verdict means nothing if assessments are switched off.
if ! spctl --status 2>&1 | grep -q 'assessments enabled'; then
  echo "::error::Gatekeeper assessments are disabled on this machine, so spctl would accept anything: $(spctl --status 2>&1)"
  exit 1
fi

# spctl prints its verdict on stderr. A notarized build must come from
# Notarized Developer ID; plain "Developer ID" means the ticket is missing.
_spctl_notarized() {
  local label="$1" out
  shift
  echo "== spctl ($label)"
  if ! out=$(spctl "$@" 2>&1); then
    echo "$out"
    echo "::error::spctl rejected the $label"
    exit 1
  fi
  echo "$out"
  if ! grep -qF 'source=Notarized Developer ID' <<< "$out"; then
    echo "::error::spctl did not report source=Notarized Developer ID for the $label"
    exit 1
  fi
}

_spctl_notarized app -a -vv "$_app"
echo "== stapler validate (app)"
xcrun stapler validate "$_app"
echo "== codesign --verify (disk image)"
codesign --verify --strict --verbose=2 "$_dmg"
_spctl_notarized "disk image" -a -vv -t open --context context:primary-signature "$_dmg"
echo "== stapler validate (disk image)"
xcrun stapler validate "$_dmg"

echo "Disk image verified: signed, notarized and stapled."
