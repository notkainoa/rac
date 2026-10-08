#!/bin/bash -eux
# Signs a release's disk images and deltas, and writes one Sparkle feed per
# architecture into release_asset/. The feeds are uploaded with the release, so
# releases/latest/download/appcast-<arch>.xml always describes the newest one.

_root_dir="$(dirname "$(greadlink -f "$0")")"
_tag="$1"
_rac_version=$(python3 "$_root_dir/devutils/rac/rac_version.py" --print)
_base_url="https://github.com/${GITHUB_REPOSITORY}/releases/download/${_tag}/"

if [ -z "${PROD_MACOS_SPARKLE_ED_PUB_KEY:-}" ]; then
  echo "warn: PROD_MACOS_SPARKLE_ED_PUB_KEY is not set, so this build can't update itself; skipping feeds" >&2
  exit 0
fi

for _arch in arm64 x86_64; do
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
