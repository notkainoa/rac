#!/bin/bash
# Install smoke test: mounts a rac disk image, copies rac.app the way a user
# would (drag to a folder), checks the signature, launches it once against a
# throwaway profile, and proves it draws a real window. Writes
# <out>/install-smoke.md (one line per check) and <out>/install-smoke.png.
#
# Usage: github_install_smoke.sh <rac.dmg> <out-dir> [--expect-notarized] [--expect-feed]
#
#   --expect-notarized  Fail unless Gatekeeper (spctl) and the notarization
#                       ticket (stapler) both accept the app. Off by default:
#                       CI builds are signed ad hoc, so their assessments are
#                       recorded but not required.
#   --expect-feed       Fail unless the app's update feed answers. Off by
#                       default: the feed URL is allowed to return 404 before
#                       the first release is published.
#
# Launch check: dev/CI builds understand --rac-window-screenshot, which makes
# rac write its own window after the first paint. That switch may be compiled
# out of release builds later, so when the binary doesn't contain the string
# "rac-window-screenshot" the script falls back to checking that the process
# stays alive and writes a Default/Preferences file. The summary says which
# mode was used.
#
# Meant for CI runners. Every launch uses a throwaway --user-data-dir and
# Crashpad folder, but rac shares its bundle id with the installed app, so
# Sparkle's defaults (me.kainoa.rac) and caches are still written to the
# running user's home. Don't run it on a Mac whose rac state you care about.

set -u

_here="$(cd "$(dirname "$0")" && pwd)"
_smoke_py="$_here/release_smoke.py"

_dmg=""
_out_dir=""
_expect_notarized=0
_expect_feed=0

while [ $# -gt 0 ]; do
  case "$1" in
    --expect-notarized) _expect_notarized=1; shift ;;
    --expect-feed) _expect_feed=1; shift ;;
    -*) echo "error: unknown option $1" >&2; exit 2 ;;
    *)
      if [ -z "$_dmg" ]; then _dmg="$1"
      elif [ -z "$_out_dir" ]; then _out_dir="$1"
      else echo "error: unexpected argument $1" >&2; exit 2
      fi
      shift ;;
  esac
done

if [ -z "$_dmg" ] || [ -z "$_out_dir" ]; then
  echo "usage: $0 <rac.dmg> <out-dir> [--expect-notarized] [--expect-feed]" >&2
  exit 2
fi
if [ ! -f "$_dmg" ]; then
  echo "error: no disk image at $_dmg" >&2
  exit 2
fi

mkdir -p "$_out_dir"
# rac wants an absolute screenshot path.
_out_dir="$(cd "$_out_dir" && pwd)"
_mnt="$(mktemp -d "${TMPDIR:-/tmp}/rac-install-mnt.XXXXXX")" || exit 1
_work="$(mktemp -d "${TMPDIR:-/tmp}/rac-install.XXXXXX")" || exit 1
_profile="$_work/profile"
_png="$_out_dir/install-smoke.png"
_results="$_work/results.txt"
: > "$_results"
_mounted=0

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
  if [ "$_mounted" = 1 ]; then
    hdiutil detach "$_mnt" -quiet 2>/dev/null || hdiutil detach "$_mnt" -force -quiet 2>/dev/null || true
  fi
  rm -rf "$_mnt" "$_work"
}
trap _cleanup EXIT
# A cancelled job (SIGINT/SIGTERM) still leaves through _cleanup.
trap 'exit 143' INT TERM

# Appends one check line to the results file and echoes it to the log.
# Usage: record PASS|FAIL|SKIP <name> <detail>
record() {
  _status="$1"; _name="$2"
  _detail="$(printf '%s' "$3" | tr '\n\t' '  ')"
  printf '%s\t%s\t%s\n' "$_status" "$_name" "$_detail" >> "$_results"
  printf '%s %s: %s\n' "$_status" "$_name" "$_detail"
}

_finish() {
  python3 "$_smoke_py" render-summary \
    --title "Install smoke" --results "$_results" --out "$_out_dir/install-smoke.md"
}

if hdiutil attach -nobrowse -readonly -mountpoint "$_mnt" "$_dmg" >/dev/null; then
  _mounted=1
else
  record FAIL "disk image" "hdiutil attach failed for $_dmg"
  _finish
  exit $?
fi

if [ ! -d "$_mnt/rac.app" ]; then
  record FAIL "disk image" "no rac.app inside $_dmg"
  _finish
  exit $?
fi

# Like a user dragging rac.app out of the disk image.
if ditto "$_mnt/rac.app" "$_work/rac.app"; then
  record PASS "disk image" "$(basename "$_dmg") mounted; rac.app copied out"
else
  record FAIL "disk image" "could not copy rac.app out of $_dmg"
  _finish
  exit $?
fi

_app="$_work/rac.app"
_exe="$_app/Contents/MacOS/rac"
if [ ! -x "$_exe" ]; then
  record FAIL "app bundle" "no executable at Contents/MacOS/rac"
  _finish
  exit $?
fi

# The copy carries the disk image's quarantine xattr; a real install would ask
# Gatekeeper once. The checks below assess it explicitly instead.
xattr -dr com.apple.quarantine "$_app" >/dev/null 2>&1 || true

_version="$(python3 "$_smoke_py" plist-value "$_app/Contents/Info.plist" CFBundleShortVersionString 2>/dev/null)"

if _out="$(codesign --verify --deep --strict --verbose=2 "$_app" 2>&1)"; then
  record PASS "code signature" "codesign --verify --deep --strict passed"
else
  record FAIL "code signature" "$_out"
fi

_out="$(spctl -a -vv -t exec "$_app" 2>&1)"
if [ $? -eq 0 ]; then
  record PASS "gatekeeper" "spctl accepted the app"
elif [ "$_expect_notarized" = 1 ]; then
  record FAIL "gatekeeper" "spctl rejected the app: $_out"
else
  record SKIP "gatekeeper" "spctl rejected the app (allowed without --expect-notarized): $_out"
fi

_out="$(xcrun stapler validate "$_app" 2>&1)"
if [ $? -eq 0 ]; then
  record PASS "notarization" "stapler found a ticket"
elif [ "$_expect_notarized" = 1 ]; then
  record FAIL "notarization" "stapler found no ticket: $_out"
else
  record SKIP "notarization" "no stapled ticket (allowed without --expect-notarized)"
fi

# Architecture decides which feed the build should point at.
_arch=""
_arches="$(lipo -archs "$_exe" 2>/dev/null)"
case " $_arches " in
  *" arm64 "*) _arch="arm64" ;;
  *" x86_64 "*) _arch="x86_64" ;;
esac
if [ -n "$_arch" ]; then
  record PASS "architecture" "$_arches -> rac $_version"
else
  record FAIL "architecture" "could not read lipo -archs on the main executable"
fi

# The bundled strings below answer two questions: whether this binary has the
# screenshot switch, and whether the update feed is compiled in.
_strings="$_work/strings.txt"
_fw_bin=""
for _fw in "$_app"/Contents/Frameworks/*.framework; do
  _fw_name="$(basename "$_fw" .framework)"
  case "$_fw_name" in Sparkle|Squirrel|Mantle|ReactiveObjC) continue ;; esac
  for _cand in "$_fw/Versions/Current/$_fw_name" "$_fw/$_fw_name"; do
    if [ -f "$_cand" ]; then _fw_bin="$_cand"; break; fi
  done
  [ -n "$_fw_bin" ] && break
done
strings "$_exe" ${_fw_bin:+"$_fw_bin"} > "$_strings" 2>/dev/null || true

if grep -qF "rac-window-screenshot" "$_strings"; then
  _has_screenshot=1
else
  _has_screenshot=0
fi

# Updater check. rac's feed URL lives in code (rac::GetUpdateFeedURL), not in
# Info.plist — Helium never writes SUFeedURL — so a plist value wins when
# present, and otherwise the compiled-in base + file name are the evidence.
if [ -n "$_arch" ]; then
  _feed_url="$(python3 "$_smoke_py" feed-url "$_arch")"
  _su_feed="$(python3 "$_smoke_py" plist-value "$_app/Contents/Info.plist" SUFeedURL 2>/dev/null)"
  if [ -n "$_su_feed" ]; then
    if [ "$_su_feed" = "$_feed_url" ]; then
      record PASS "updater feed" "SUFeedURL is $_feed_url"
    else
      record FAIL "updater feed" "SUFeedURL is $_su_feed, expected $_feed_url"
    fi
  elif _feed_result="$(python3 "$_smoke_py" check-feed "$_strings" "$_arch")"; then
    record PASS "updater feed" "SUFeedURL not in Info.plist; $_feed_result"
  else
    record FAIL "updater feed" "SUFeedURL not in Info.plist; $_feed_result"
  fi

  _http="$(curl -sSL -o /dev/null -w '%{http_code}' --max-time 30 "$_feed_url" 2>/dev/null || echo 000)"
  if [ "$_http" = "200" ]; then
    record PASS "feed reachable" "$_feed_url answers HTTP 200"
  elif [ "$_expect_feed" = 1 ]; then
    record FAIL "feed reachable" "$_feed_url answered HTTP $_http (--expect-feed)"
  else
    record SKIP "feed reachable" "$_feed_url answered HTTP $_http (allowed before the first release)"
  fi
else
  record SKIP "updater feed" "skipped: architecture unknown"
fi

# Launch once against a throwaway profile. A screenshot from an earlier run
# must not satisfy this one's wait, so the target PNG starts deleted.
mkdir -p "$_profile/Crashpad"
_log="$_work/rac.log"
rm -f "$_png"
if [ "$_has_screenshot" = 1 ]; then
  _mode="screenshot"
  env BREAKPAD_DUMP_LOCATION="$_profile/Crashpad" \
    "$_exe" --user-data-dir="$_profile" --no-first-run --disable-backgrounding-occluded-windows --use-mock-keychain \
    --custom-update-server-url=http://127.0.0.1:9/ \
    "--rac-window-screenshot=$_png" --rac-window-screenshot-delay=8 about:blank \
    > "$_log" 2>&1 &
  _pid=$!
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
    record PASS "launch" "screenshot mode: window painted after ${_waited}s ($_png_result)"
  else
    if kill -0 "$_pid" 2>/dev/null; then
      record FAIL "launch" "screenshot mode: $_png_result"
    else
      record FAIL "launch" "screenshot mode: rac exited before painting; $_png_result (see log in the artifact)"
    fi
  fi
else
  _mode="alive"
  env BREAKPAD_DUMP_LOCATION="$_profile/Crashpad" \
    "$_exe" --user-data-dir="$_profile" --no-first-run --disable-backgrounding-occluded-windows --use-mock-keychain \
    --custom-update-server-url=http://127.0.0.1:9/ about:blank \
    > "$_log" 2>&1 &
  _pid=$!
  _alive=1
  _waited=0
  while [ "$_waited" -lt 20 ]; do
    if ! kill -0 "$_pid" 2>/dev/null; then _alive=0; break; fi
    sleep 1
    _waited=$((_waited + 1))
  done
  if [ "$_alive" = 1 ] && [ -f "$_profile/Default/Preferences" ]; then
    record PASS "launch" "alive mode: rac stayed up ${_waited}s and wrote Default/Preferences"
  elif [ "$_alive" = 1 ]; then
    record FAIL "launch" "alive mode: rac stayed up but wrote no Default/Preferences"
  else
    record FAIL "launch" "alive mode: rac exited after ${_waited}s (see log in the artifact)"
  fi
fi
_stop_app

echo "launch check used $_mode mode"
cp "$_log" "$_out_dir/rac-launch.log" 2>/dev/null || true
_finish
exit $?
