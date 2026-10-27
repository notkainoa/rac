#!/bin/bash -eux
# Signs, notarizes and packages the app that the build phases left unsigned,
# then writes the disk image, its hashes and the update deltas the release job
# expects. Runs in the `sign` job of building.yml, on a GitHub-hosted runner,
# so the Developer ID certificate and notarization credentials never reach a
# build runner.
#
# Expects the unsigned build in build/src/out/Default (rac.app, "rac
# Packaging", and Sparkle's BinaryDelta). Without MACOS_CERTIFICATE, the app is
# signed ad hoc and nothing is notarized, as before.
#
# The temporary keychain is deleted by the workflow's cleanup step, which runs
# even when this script fails.

_target_cpu="${1:?usage: $0 arm64|x86_64}"

_root_dir="$(dirname "$(greadlink -f "$0")")"
_src_dir="$_root_dir/build/src"
_keychain=build.keychain
_keychain_path="$HOME/Library/Keychains/$_keychain-db"

_rac_version=$(python3 "$_root_dir/devutils/rac/rac_version.py" --print)
_file_name="rac_${_rac_version}_${_target_cpu}-macos.dmg"
_hash_name="${_file_name}.hashes.md"

# Tracing stays off from here until the signing script starts, so it never
# echoes a credential. GitHub masks secrets in logs, but a decoded or derived
# value wouldn't be masked. Even the `[ -n ... ]` checks are traced with the
# secret's value expanded.
{ set +x; } 2>/dev/null

_notarized=0
if [ -n "${MACOS_CERTIFICATE:-}" ]; then
  _notarized=1
  # A secret pasted with a trailing newline would break the checks below.
  PROD_MACOS_NOTARIZATION_TEAM_ID=$(printf '%s' "${PROD_MACOS_NOTARIZATION_TEAM_ID:-}" | tr -d '[:space:]')
  MACOS_CERTIFICATE_NAME=$(printf '%s' "${MACOS_CERTIFICATE_NAME:-}" | tr -d '\r\n' | sed 's/^[[:space:]]*//; s/[[:space:]]*$//')
  export PROD_MACOS_NOTARIZATION_TEAM_ID MACOS_CERTIFICATE_NAME
  _missing=()
  for _var in MACOS_CERTIFICATE_PWD MACOS_CERTIFICATE_NAME MACOS_CI_KEYCHAIN_PWD \
      PROD_MACOS_NOTARIZATION_APPLE_ID PROD_MACOS_NOTARIZATION_TEAM_ID PROD_MACOS_NOTARIZATION_PWD; do
    [ -n "${!_var:-}" ] || _missing+=("$_var")
  done
  if [ "${#_missing[@]}" -gt 0 ]; then
    echo "::error::PROD_MACOS_CERTIFICATE is set but these are empty: ${_missing[*]} (the PROD_ secret names map onto them in building.yml)"
    exit 1
  fi
  if ! [[ "$PROD_MACOS_NOTARIZATION_TEAM_ID" =~ ^[A-Z0-9]{10}$ ]]; then
    echo "::error::PROD_MACOS_NOTARIZATION_TEAM_ID is not a 10-character Apple team ID"
    exit 1
  fi
  # A Developer ID identity is named "Developer ID Application: <name> (<team>)".
  # codesign also accepts a part of the name or the certificate hash, so this
  # only warns; github_verify_dmg.sh checks the team the app was signed by.
  if [[ "$MACOS_CERTIFICATE_NAME" != "Developer ID Application: "*" ($PROD_MACOS_NOTARIZATION_TEAM_ID)" ]]; then
    echo "::warning::PROD_MACOS_CERTIFICATE_NAME doesn't look like 'Developer ID Application: <name> (<notarization team>)'"
  fi

  _p12="${RUNNER_TEMP:-$TMPDIR}/certificate.p12"
  printf '%s' "$MACOS_CERTIFICATE" | base64 --decode > "$_p12"

  security create-keychain -p "$MACOS_CI_KEYCHAIN_PWD" "$_keychain"
  # No auto-lock during a long notarization wait.
  security set-keychain-settings -lut 21600 "$_keychain"
  security unlock-keychain -p "$MACOS_CI_KEYCHAIN_PWD" "$_keychain"
  security import "$_p12" -k "$_keychain" -P "$MACOS_CERTIFICATE_PWD" -T /usr/bin/codesign
  rm -f "$_p12"
  # Lets codesign use the key without a dialog, which would hang the job.
  security set-key-partition-list -S apple-tool:,apple:,codesign: -s -k "$MACOS_CI_KEYCHAIN_PWD" "$_keychain" > /dev/null
  # Put it first in the search list, keeping the rest, so codesign finds it.
  _search=()
  while IFS= read -r _kc; do
    _kc="${_kc#"${_kc%%[![:space:]]*}"}"; _kc="${_kc#\"}"; _kc="${_kc%\"}"
    if [ -n "$_kc" ]; then _search+=("$_kc"); fi
  done < <(security list-keychains -d user)
  security list-keychains -d user -s "$_keychain_path" ${_search[@]+"${_search[@]}"}
  security default-keychain -s "$_keychain"

  if ! security find-identity -v -p codesigning "$_keychain" | grep -qF -- "$MACOS_CERTIFICATE_NAME"; then
    echo "::error::The imported certificate has no valid code signing identity named PROD_MACOS_CERTIFICATE_NAME"
    security find-identity -v -p codesigning "$_keychain" | sed -n 's/.*valid identities found.*/&/p'
    exit 1
  fi
  echo "Signing identity found in the temporary keychain."
else
  echo "::warning::PROD_MACOS_CERTIFICATE is not set; the app is signed ad hoc and not notarized."
fi

if [ -n "${PROD_MACOS_SPECIAL_ENTITLEMENTS_PROFILE_B64:-}" ]; then
  # A fixed name, so the workflow's cleanup step can remove it if this fails.
  export PROD_MACOS_SPECIAL_ENTITLEMENTS_PROFILE_PATH="${RUNNER_TEMP:-$TMPDIR}/entitlements.provisionprofile"
  printf '%s' "$PROD_MACOS_SPECIAL_ENTITLEMENTS_PROFILE_B64" \
    | base64 --decode > "$PROD_MACOS_SPECIAL_ENTITLEMENTS_PROFILE_PATH"
fi
set -x

# Signs and notarizes the app, staples it, packages the disk image, and signs,
# notarizes and staples that too.
cd "$_src_dir"
export OUT_DMG_PATH="$_root_dir/$_file_name"
"$_root_dir/sign_and_package_app.sh"

if [ -n "${PROD_MACOS_SPECIAL_ENTITLEMENTS_PROFILE_PATH:-}" ]; then
  rm -f "$PROD_MACOS_SPECIAL_ENTITLEMENTS_PROFILE_PATH"
fi

cd "$_root_dir"
RAC_EXPECT_NOTARIZED="$_notarized" RAC_EXPECT_TEAM_ID="${PROD_MACOS_NOTARIZATION_TEAM_ID:-}" \
  "$_root_dir/github_verify_dmg.sh" "$_root_dir/$_file_name"

# Hash the disk image as it is published: stapling changes it.
echo -e "md5: \nsha1: \nsha256: " | tee ./hash_types.txt
{ md5sum "$_file_name" ; sha1sum "$_file_name" ; sha256sum "$_file_name" ; } | tee ./sums.txt

_hash_md=$(paste ./hash_types.txt ./sums.txt | awk '{print $1 " " $2}')

echo "file_name=$_file_name" >> "$GITHUB_OUTPUT"

# shellcheck disable=SC2016 # Markdown backticks, not command substitution.
printf 'Hashes for the disk image `%s`: \n' "$_file_name" | tee -a "./${_hash_name}"
# shellcheck disable=SC2016
printf '\n```\n%s\n```\n' "$_hash_md" | tee -a "./${_hash_name}"

# A separate folder for the disk image, so it can be used as an individual
# asset if the release job fails.
mkdir -p release_asset
mv "$_file_name" release_asset/

if [ "$_target_cpu" = "x86_64" ]; then
  DELTA_ARG="--x86"
else
  DELTA_ARG="--arm"
fi

PATH="$_src_dir/out/Default:$PATH" python3 "$_root_dir/devutils/generate_sparkle_deltas.py" \
  "$DELTA_ARG" "./release_asset/$_file_name" \
  --out ./release_asset

{
  echo 'deltas<<EOF'
  find ./release_asset/ -name '*.delta'
  echo EOF
} >> "$GITHUB_OUTPUT"

ls -kahl release_asset/
du -hs release_asset/
