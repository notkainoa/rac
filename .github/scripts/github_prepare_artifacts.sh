#!/bin/bash -eux
# Simple script for packing Helium macOS build artifacts on GitHub Actions

_target_cpu="${1:-x86_64}"

_root_dir="$(dirname "$(greadlink -f "$0")")"
_main_repo="$_root_dir/helium-chromium"
_src_dir="$_root_dir/build/src"

# If the build finished, pack the unsigned app for the `sign` job, which runs on
# a GitHub-hosted runner. Build runners never see the signing keys.
if [ -f "$_root_dir/build_finished_$_target_cpu.log" ]; then
  cd "$_src_dir/out/Default"

  xattr -cs rac.app

  # sign_chrome.py and pkg-dmg come from the packaging folder; deltas need
  # Sparkle's BinaryDelta, which is only built with the updater.
  _app_files=(rac.app "rac Packaging")
  for _optional in BinaryDelta Sparkle.framework; do
    if [ -e "$_optional" ]; then
      _app_files+=("$_optional")
    fi
  done

  mkdir -p "$_root_dir/upload_app"
  # tar keeps the framework symlinks and permissions that a zip artifact loses.
  ( set -o pipefail
    tar --format pax --no-mac-metadata -c -f - "${_app_files[@]}" \
      | zstd -vv -10 -T0 -o "$_root_dir/upload_app/rac_unsigned.tar.zst" )
  zstd -t "$_root_dir/upload_app/rac_unsigned.tar.zst"
  (cd "$_root_dir/upload_app" && sha256sum rac_unsigned.tar.zst | tee app_sums.txt)

  cd "$_root_dir"
  ls -kahl upload_app/
fi

gsync --file-system "$_src_dir"

# Needs to be compressed to stay below GitHub's upload limit 2 GB (?!) 2020-11-24; used to be  5-8GB (?)
# pax keeps sub-second mtimes. bsdtar's default "restricted pax" drops them for
# files without xattrs, and siso compares mtimes to the nanosecond, so the next
# phase would rebuild almost everything.
tar --format pax -C build -c -f - src | zstd -vv -11 -T0 -o build_src.tar.zst

# A short or damaged archive should fail here, in the job that made it, and not
# in the next phase after it has been uploaded and downloaded. A real checkpoint
# holds the whole source tree, far above this floor.
zstd -t build_src.tar.zst
_archive_bytes=$(wc -c < build_src.tar.zst)
_min_archive_bytes="${RAC_MIN_CHECKPOINT_BYTES:-268435456}"
if [ "$_archive_bytes" -lt "$_min_archive_bytes" ]; then
  echo "::error::build_src.tar.zst is only $_archive_bytes bytes (expected at least $_min_archive_bytes); the archive is incomplete"
  exit 1
fi

sha256sum ./build_src.tar.zst | tee ./sums.txt

mkdir -p upload_part_build
mv build_src.tar.zst sums.txt upload_part_build/
cp -va ./*.log upload_part_build/

ls -kahl upload_part_build/
du -hs upload_part_build/

mkdir upload_logs
mv -vn ./*.log upload_logs/

ls -kahl upload_logs/
du -hs upload_logs/

echo "ready for upload action"
