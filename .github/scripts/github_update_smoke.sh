#!/bin/bash
# Update smoke test: installs the OLD rac.app from its disk image, launches it
# once against a throwaway profile, then replaces the bundle with the NEW one
# — the state Sparkle leaves behind after installing an update — and launches
# it again on the same profile.
#
# This proves the two things that can't wait for a maintainer to notice:
#   * the new version is higher than the old one (Sparkle only ever offers a
#     higher version, so a release that isn't is silently never offered), and
#   * the profile carries over — Local State and Default/Preferences still
#     exist and still parse as JSON — and the updated app runs.
# It does NOT exercise Sparkle's download, verification, or install path:
# there is no headless way to drive Sparkle's UI. That stays a by-hand check
# in the release runbook (docs/operations/releases.md).
#
# Usage: github_update_smoke.sh <old-rac.dmg> <new-rac.dmg> <out-dir>
#
# Writes <out>/update-smoke.md (one line per check), <out>/update-smoke.png
# when the new build has the screenshot switch, and exits non-zero if any
# check fails.
#
# Meant for CI runners. Every launch uses a throwaway --user-data-dir and
# Crashpad folder, but rac shares its bundle id with the installed app, so
# Sparkle's defaults (me.kainoa.rac) and caches are still written to the
# running user's home. Don't run it on a Mac whose rac state you care about.

set -u

_here="$(cd "$(dirname "$0")" && pwd)"
_smoke_py="$_here/release_smoke.py"

if [ $# -ne 3 ]; then
  echo "usage: $0 <old-rac.dmg> <new-rac.dmg> <out-dir>" >&2
  exit 2
fi
_old_dmg="$1"
_new_dmg="$2"
_out_dir="$3"

for _f in "$_old_dmg" "$_new_dmg"; do
  if [ ! -f "$_f" ]; then
    echo "error: no disk image at $_f" >&2
    exit 2
  fi
done

mkdir -p "$_out_dir"
# rac wants an absolute screenshot path.
_out_dir="$(cd "$_out_dir" && pwd)"
_mnt_old="$(mktemp -d "${TMPDIR:-/tmp}/rac-update-old.XXXXXX")" || exit 1
_mnt_new="$(mktemp -d "${TMPDIR:-/tmp}/rac-update-new.XXXXXX")" || exit 1
_work="$(mktemp -d "${TMPDIR:-/tmp}/rac-update.XXXXXX")" || exit 1
_profile="$_work/profile"
_apps="$_work/Applications"
_png="$_out_dir/update-smoke.png"
_results="$_work/results.txt"
: > "$_results"
_mounted=""

# Stops the launched rac, and only that process: SIGTERM first so Chromium
# shuts down cleanly, then SIGKILL if it hasn't exited after 20 seconds.
_pid=""
_stop_app() {
  [ -n "$_pid" ] || return 0
  kill "$_pid" 2>/dev/null || true
  _stopped=0
  while kill -0 "$_pid" 2>/dev/null && [ "$_stopped" -lt 20 ]; do
    sleep 1
    _stopped=$((_stopped + 1))
  done
  if kill -0 "$_pid" 2>/dev/null; then kill -9 "$_pid" 2>/dev/null || true; fi
  wait "$_pid" 2>/dev/null || true
  _pid=""
}

_cleanup() {
  _stop_app
  for _m in $_mounted; do
    hdiutil detach "$_m" -quiet 2>/dev/null || hdiutil detach "$_m" -force -quiet 2>/dev/null || true
  done
  rm -rf "$_mnt_old" "$_mnt_new" "$_work"
}
trap _cleanup EXIT
# A cancelled job (SIGINT/SIGTERM) still leaves through _cleanup.
trap 'exit 143' INT TERM

# Appends one check line to the results file and echoes it to the log.
record() {
  _status="$1"; _name="$2"
  _detail="$(printf '%s' "$3" | tr '\n\t' '  ')"
  printf '%s\t%s\t%s\n' "$_status" "$_name" "$_detail" >> "$_results"
  printf '%s %s: %s\n' "$_status" "$_name" "$_detail"
}

_finish() {
  python3 "$_smoke_py" render-summary \
    --title "Update smoke" --results "$_results" --out "$_out_dir/update-smoke.md"
}

# Mounts $1 at $4, copies rac.app to $2, and leaves the mount in $_mounted
# for _cleanup to detach. On failure records a FAIL under check-name $3 and
# returns 1.
_install() {
  _image="$1"; _dest="$2"; _check="$3"; _mount="$4"
  if ! hdiutil attach -nobrowse -readonly -mountpoint "$_mount" "$_image" >/dev/null; then
    record FAIL "$_check" "hdiutil attach failed for $_image"
    return 1
  fi
  _mounted="$_mounted $_mount"
  if [ ! -d "$_mount/rac.app" ] || ! ditto "$_mount/rac.app" "$_dest"; then
    record FAIL "$_check" "no usable rac.app inside $_image"
    return 1
  fi
  # Sparkle strips quarantine when it installs; a hand copy must too.
  xattr -dr com.apple.quarantine "$_dest" >/dev/null 2>&1 || true
  return 0
}

mkdir -p "$_apps" "$_profile/Crashpad"
_installed="$_apps/rac.app"

if ! _install "$_old_dmg" "$_installed" "old build" "$_mnt_old"; then
  _finish
  exit $?
fi
_old_version="$(python3 "$_smoke_py" plist-value "$_installed/Contents/Info.plist" CFBundleShortVersionString 2>/dev/null)"
record PASS "old build" "installed rac ${_old_version:-unknown} from $(basename "$_old_dmg")"

# First launch: give the old build a profile to leave behind.
env BREAKPAD_DUMP_LOCATION="$_profile/Crashpad" \
  "$_installed/Contents/MacOS/rac" --user-data-dir="$_profile" --no-first-run --disable-backgrounding-occluded-windows \
  --use-mock-keychain --custom-update-server-url=http://127.0.0.1:9/ \
  about:blank > "$_work/rac-old.log" 2>&1 &
_pid=$!
_waited=0
while [ "$_waited" -lt 60 ]; do
  [ -f "$_profile/Default/Preferences" ] && break
  kill -0 "$_pid" 2>/dev/null || break
  sleep 1
  _waited=$((_waited + 1))
done
sleep 2  # let it finish flushing the profile to disk
# The profile files only count if the build stayed up: a build that writes
# Preferences and then exits crashed on first run, which is a failed smoke
# test even though the file exists.
if kill -0 "$_pid" 2>/dev/null; then _old_alive=1; else _old_alive=0; fi
_stop_app
if [ "$_old_alive" != 1 ]; then
  record FAIL "first launch" "old build exited within ${_waited}s of launch (see log in the artifact)"
  cp "$_work/rac-old.log" "$_out_dir/rac-old.log" 2>/dev/null || true
  _finish
  exit $?
elif [ -f "$_profile/Default/Preferences" ]; then
  record PASS "first launch" "old build stayed up and wrote a profile after ${_waited}s"
else
  record FAIL "first launch" "old build left no Default/Preferences (see log in the artifact)"
  cp "$_work/rac-old.log" "$_out_dir/rac-old.log" 2>/dev/null || true
  _finish
  exit $?
fi

# Seed a marker setting the update must not lose. Chromium keeps unknown
# top-level prefs, so the same value after the new build runs is proof a
# real setting carried over — not just that a file named Preferences exists.
_marker="$(python3 -c 'import secrets; print(secrets.token_hex(8))')"
if ! python3 "$_smoke_py" set-marker "$_profile/Default/Preferences" "$_marker"; then
  record FAIL "first launch" "old profile's Default/Preferences would not take a marker pref"
  cp "$_work/rac-old.log" "$_out_dir/rac-old.log" 2>/dev/null || true
  _finish
  exit $?
fi

# The update itself: swap the bundle at the same path, keep the profile.
rm -rf "$_installed"
if ! _install "$_new_dmg" "$_installed" "new build" "$_mnt_new"; then
  _finish
  exit $?
fi
_new_version="$(python3 "$_smoke_py" plist-value "$_installed/Contents/Info.plist" CFBundleShortVersionString 2>/dev/null)"

case "$(python3 "$_smoke_py" compare-versions "$_new_version" "$_old_version" 2>/dev/null)" in
  newer) record PASS "version ordering" "$_old_version -> $_new_version is a real update" ;;
  same)  record FAIL "version ordering" "new build is also $_new_version; Sparkle would never offer it" ;;
  older) record FAIL "version ordering" "new build is $_new_version, below $_old_version" ;;
  *)     record FAIL "version ordering" "could not compare '$_new_version' with '$_old_version'" ;;
esac

# Does the new build have the screenshot switch?
_exe="$_installed/Contents/MacOS/rac"
_strings="$_work/strings.txt"
_fw_bin=""
for _fw in "$_installed"/Contents/Frameworks/*.framework; do
  _fw_name="$(basename "$_fw" .framework)"
  case "$_fw_name" in Sparkle|Squirrel|Mantle|ReactiveObjC) continue ;; esac
  for _cand in "$_fw/Versions/Current/$_fw_name" "$_fw/$_fw_name"; do
    if [ -f "$_cand" ]; then _fw_bin="$_cand"; break; fi
  done
  [ -n "$_fw_bin" ] && break
done
strings "$_exe" ${_fw_bin:+"$_fw_bin"} > "$_strings" 2>/dev/null || true
if grep -qF "rac-window-screenshot" "$_strings"; then
  _shot_args=("--rac-window-screenshot=$_png" "--rac-window-screenshot-delay=8")
else
  _shot_args=()
fi

# Relaunch on the same profile and keep it up for 20 seconds. A screenshot
# from an earlier run must not satisfy this one's wait.
rm -f "$_png"
env BREAKPAD_DUMP_LOCATION="$_profile/Crashpad" \
  "$_exe" --user-data-dir="$_profile" --no-first-run --disable-backgrounding-occluded-windows --use-mock-keychain \
  --custom-update-server-url=http://127.0.0.1:9/ \
  ${_shot_args[@]+"${_shot_args[@]}"} about:blank > "$_work/rac-new.log" 2>&1 &
_pid=$!
_alive=1
_waited=0
while [ "$_waited" -lt 20 ]; do
  if ! kill -0 "$_pid" 2>/dev/null; then _alive=0; break; fi
  sleep 1
  _waited=$((_waited + 1))
done
if [ "$_alive" = 1 ]; then
  record PASS "updated app runs" "rac $_new_version stayed up ${_waited}s on the old profile"
else
  record FAIL "updated app runs" "rac $_new_version exited after ${_waited}s (see log in the artifact)"
fi

if [ ${#_shot_args[@]} -gt 0 ]; then
  _waited=0
  while [ "$_waited" -lt 90 ]; do
    [ -s "$_png" ] && break
    kill -0 "$_pid" 2>/dev/null || break
    sleep 1
    _waited=$((_waited + 1))
  done
  # rac writes the PNG in place, so give a file that just appeared time to finish.
  [ -s "$_png" ] && sleep 2
  if _png_result="$(python3 "$_smoke_py" check-png "$_png")"; then
    record PASS "window painted" "screenshot mode: $_png_result"
  else
    record FAIL "window painted" "screenshot mode: $_png_result"
  fi
else
  record SKIP "window painted" "no rac-window-screenshot in this build; the 20s alive check above is the evidence"
fi
_stop_app

# The point of the whole exercise: the profile survived the swap, marker
# setting included.
if _marker_result="$(python3 "$_smoke_py" check-marker "$_profile/Default/Preferences" "$_marker")"; then
  record PASS "setting carried over" "$_marker_result"
else
  record FAIL "setting carried over" "$_marker_result"
fi
for _piece in "Local State" "Default/Preferences"; do
  if _json_result="$(python3 "$_smoke_py" check-json "$_profile/$_piece")"; then
    record PASS "profile carried over" "$_json_result"
  else
    record FAIL "profile carried over" "$_json_result"
  fi
done

cp "$_work/rac-old.log" "$_out_dir/rac-old.log" 2>/dev/null || true
cp "$_work/rac-new.log" "$_out_dir/rac-new.log" 2>/dev/null || true
_finish
exit $?
