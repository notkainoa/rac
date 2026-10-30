#!/bin/bash -eux
# Signs a release's disk images and deltas, and writes one Sparkle feed per
# architecture into release_asset/. The feeds are uploaded with the release, so
# releases/latest/download/appcast-<arch>.xml always describes the newest one.

_root_dir="$(dirname "$(greadlink -f "$0")")"
_tag="$1"
_rac_version=$(python3 "$_root_dir/devutils/rac/rac_version.py" --print)
_base_url="https://github.com/${GITHUB_REPOSITORY}/releases/download/${_tag}/"

# Tracing stays off while the signing key is checked and cleaned, so the key
# never reaches the log even if GitHub's masking misses it.
{ set +x; } 2>/dev/null

# A release without feeds strands every installed copy until the next good
# release, so refuse to publish one.
if [ -z "${PROD_MACOS_SPARKLE_ED_PUB_KEY:-}" ] || [ -z "${RAC_SPARKLE_ED_PRIVATE_KEY:-}" ]; then
  echo "error: PROD_MACOS_SPARKLE_ED_PUB_KEY and RAC_SPARKLE_ED_PRIVATE_KEY must both be set to write the update feeds" >&2
  exit 1
fi
# Secrets pasted into GitHub sometimes carry a trailing newline.
PROD_MACOS_SPARKLE_ED_PUB_KEY=$(printf '%s' "$PROD_MACOS_SPARKLE_ED_PUB_KEY" | tr -d '[:space:]')
export RAC_SPARKLE_ED_PRIVATE_KEY
RAC_SPARKLE_ED_PRIVATE_KEY=$(printf '%s' "$RAC_SPARKLE_ED_PRIVATE_KEY" | tr -d '[:space:]')
set -x

# RAC_ARCHES lists the architectures this run built. A feed is written only for
# those, so an arm64-only release has no appcast-x86_64.xml.
_arches="${RAC_ARCHES:?RAC_ARCHES must list the architectures that were built}"

for _arch in arm64 x86_64; do
  case " $_arches " in *" $_arch "*) ;; *) continue ;; esac
  _delta_args=()
  for _delta in ./release_asset/*-"$_arch".delta; do
    if [ -e "$_delta" ]; then
      _delta_args+=(--delta "$_delta")
    fi
  done

  python3 "$_root_dir/devutils/rac/sparkle.py" appcast \
    --arch "$_arch" \
    --dmg "./release_asset/rac_${_rac_version}_${_arch}-macos.dmg" \
    --base-url "$_base_url" \
    ${_delta_args[@]+"${_delta_args[@]}"} \
    --public-key "$PROD_MACOS_SPARKLE_ED_PUB_KEY" \
    --out "./release_asset/appcast-$_arch.xml"
done
