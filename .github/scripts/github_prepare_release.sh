#!/bin/bash -eux

_root_dir="$(dirname "$(greadlink -f "$0")")"

_rac_version=$(python3 "$_root_dir/devutils/rac/rac_version.py" --print)

# Sparkle only offers a version higher than the installed one, so a release
# must never reuse or go below an earlier version. Helium's tags have four
# parts and rac's have three, so only three-part tags count here.
_rac_tags=$(git -C "$_root_dir" tag --list | grep -E '^[0-9]+\.[0-9]+\.[0-9]+$' || true)
_newest=$(printf '%s\n' $_rac_tags "$_rac_version" | sort -V | tail -1)
if [ "$_newest" != "$_rac_version" ] || grep -qxF "$_rac_version" <<< "$_rac_tags"; then
  echo "error: rac $_rac_version is not newer than every release; raise rac_version.txt" >&2
  exit 1
fi

_file_name_base="rac_${_rac_version}"
_x64_file_name="${_file_name_base}_x86_64-macos.dmg"
_arm64_file_name="${_file_name_base}_arm64-macos.dmg"

echo "x64_file_name=$_x64_file_name" >> $GITHUB_OUTPUT
echo "arm64_file_name=$_arm64_file_name" >> $GITHUB_OUTPUT
echo "release_tag_version=$_rac_version" >> $GITHUB_OUTPUT
echo "release_name=rac $_rac_version" >> $GITHUB_OUTPUT
