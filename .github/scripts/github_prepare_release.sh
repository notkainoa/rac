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

# RAC_ARCHES lists the architectures this run built, such as "arm64" or
# "arm64 x86_64". Only those get a disk image name; later steps skip the rest.
_arches="${RAC_ARCHES:?RAC_ARCHES must list the architectures that were built}"
for _arch in $_arches; do
  case "$_arch" in
    arm64|x86_64) ;;
    *) echo "error: unknown architecture '$_arch' in RAC_ARCHES" >&2; exit 1 ;;
  esac
done

_file_name_base="rac_${_rac_version}"
_x64_file_name=""
_arm64_file_name=""
case " $_arches " in *" x86_64 "*) _x64_file_name="${_file_name_base}_x86_64-macos.dmg" ;; esac
case " $_arches " in *" arm64 "*) _arm64_file_name="${_file_name_base}_arm64-macos.dmg" ;; esac

echo "x64_file_name=$_x64_file_name" >> $GITHUB_OUTPUT
echo "arm64_file_name=$_arm64_file_name" >> $GITHUB_OUTPUT
echo "release_tag_version=$_rac_version" >> $GITHUB_OUTPUT
echo "release_name=rac $_rac_version" >> $GITHUB_OUTPUT
