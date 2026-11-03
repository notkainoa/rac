#!/bin/bash
# Network capture: mounts a rac disk image, copies rac.app out, launches it
# once on a throwaway profile with net-log recording on, waits, and shuts it
# down. The captured hosts are compared against the published list in
# docs/network.md (launch gate G10: rac's promise of nothing phoning home is
# proven by recording, not asserted). Writes <out>/net-capture.md (one line
# per check plus the host list), <out>/netlog.json, <out>/hosts.txt,
# <out>/hosts.json, and <out>/rac-capture.log.
#
# Usage: github_net_capture.sh <rac.dmg> <out-dir> [--minutes N] [--services off|on] [--list doc.md]
#
#   --minutes N     How long the browser sits on its fresh window before
#                   shutdown. Default 10. Keep it under ~20; the workflow's
#                   timeout is 30 minutes.
#   --services on   Seed Helium services consent into the profile before
#                   launch, so the capture also records what a user who
#                   turns them on reaches. Default off: a fresh profile
#                   never consented, so nothing touches Helium's servers.
#   --list doc.md   The docs page carrying the ```hosts block to compare
#                   against. Default docs/network.md in this repo.
#
# The browser gets no URLs: it opens whatever a fresh profile shows (the
# new tab page or the first-run flow) and idles. The real update feed is
# left enabled on purpose — the point of the capture is to see every host,
# including github.com for the appcast check.
#
# Meant for CI runners. Every launch uses a throwaway --user-data-dir and
# Crashpad folder, but rac shares its bundle id with the installed app, so
# Sparkle's defaults (me.kainoa.rac) and caches are still written to the
# running user's home. Don't run it on a Mac whose rac state you care about.

set -u

_here="$(cd "$(dirname "$0")" && pwd)"
_repo="$(cd "$_here/../.." && pwd)"
_hostlist="$_repo/devutils/rac/hostlist.py"
_smoke_py="$_here/release_smoke.py"

_dmg=""
_out_dir=""
_minutes=10
_services="off"
_list="$_repo/docs/network.md"

while [ $# -gt 0 ]; do
  case "$1" in
    --minutes|--services|--list)
      if [ $# -lt 2 ]; then
        echo "error: $1 needs a value" >&2
        exit 2
      fi
      case "$1" in
        --minutes) _minutes="$2" ;;
        --services) _services="$2" ;;
        --list) _list="$2" ;;
      esac
      shift 2 ;;
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
  echo "usage: $0 <rac.dmg> <out-dir> [--minutes N] [--services off|on] [--list doc.md]" >&2
  exit 2
fi
case "$_services" in
  off|on) ;;
  *) echo "error: --services must be off or on, not '$_services'" >&2; exit 2 ;;
esac
case "$_minutes" in
  ''|*[!0-9]*) echo "error: --minutes must be a positive integer, not '$_minutes'" >&2; exit 2 ;;
esac
if [ "$_minutes" -lt 1 ]; then
  echo "error: --minutes must be at least 1" >&2
  exit 2
fi
if [ ! -f "$_dmg" ]; then
  echo "error: no disk image at $_dmg" >&2
  exit 2
fi

mkdir -p "$_out_dir"
_out_dir="$(cd "$_out_dir" && pwd)"
_mnt="$(mktemp -d "${TMPDIR:-/tmp}/rac-netlog-mnt.XXXXXX")" || exit 1
_work="$(mktemp -d "${TMPDIR:-/tmp}/rac-netlog.XXXXXX")" || exit 1
_profile="$_work/profile"
_netlog="$_work/netlog.json"
_results="$_work/results.txt"
: > "$_results"
_mounted=0

# Stops the launched rac, and only that process: SIGTERM first so Chromium
# shuts down cleanly and flushes the net-log (osascript isn't available
# headless), then SIGKILL if it hasn't exited after 30 seconds. A SIGKILLed
# browser leaves a torn net-log; hostlist.py's parser tolerates that.
_pid=""
_killed=0
_stop_app() {
  [ -n "$_pid" ] || return 0
  kill "$_pid" 2>/dev/null || true
  _stopped=0
  while kill -0 "$_pid" 2>/dev/null && [ "$_stopped" -lt 30 ]; do
    sleep 1
    _stopped=$((_stopped + 1))
  done
  if kill -0 "$_pid" 2>/dev/null; then _killed=1; kill -9 "$_pid" 2>/dev/null || true; fi
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
    --title "Network capture (services $_services)" --results "$_results" \
    --out "$_out_dir/net-capture.md"
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
xattr -dr com.apple.quarantine "$_app" >/dev/null 2>&1 || true

mkdir -p "$_profile/Default" "$_profile/Crashpad"

if [ "$_services" = "on" ]; then
  # Consent to Helium services the way the onboarding toggle does. Both are
  # profile prefs written to Default/Preferences — pref_names.h names them
  # helium.services.enabled and helium.services.user_consented, and
  # devutils/rac/evals seeds helium.services.enabled in this same file (its
  # comment cites kHeliumServicesEnabled). completed_onboarding mirrors what
  # the flow sets on the same click, so the profile looks like a user who
  # turned services on during onboarding, not a hand-edited exception.
  cat > "$_profile/Default/Preferences" <<'EOF'
{"helium":{"services":{"enabled":true,"user_consented":true},"completed_onboarding":true}}
EOF
  record PASS "profile" "seeded helium.services.enabled + user_consented into Default/Preferences"
else
  record PASS "profile" "fresh throwaway profile; nothing consented to Helium services"
fi

# Launch with the net-log recorder on and nothing to navigate to. Deliberately
# no --custom-update-server-url: the capture must show the real feed check.
_log="$_work/rac.log"
env BREAKPAD_DUMP_LOCATION="$_profile/Crashpad" \
  "$_exe" --user-data-dir="$_profile" --no-first-run --no-default-browser-check \
  --use-mock-keychain --disable-backgrounding-occluded-windows \
  --log-net-log="$_netlog" --net-log-capture-mode=Default \
  > "$_log" 2>&1 &
_pid=$!

_seconds=$((_minutes * 60))
_waited=0
while [ "$_waited" -lt "$_seconds" ]; do
  kill -0 "$_pid" 2>/dev/null || break
  sleep 5
  _waited=$((_waited + 5))
done
if kill -0 "$_pid" 2>/dev/null; then
  record PASS "capture" "rac idled on a fresh window for ${_minutes}m with the net-log on"
else
  record FAIL "capture" "rac exited after ${_waited}s (see rac-capture.log in the artifact)"
fi
_stop_app
if [ "$_killed" = 1 ]; then
  record SKIP "shutdown" "rac ignored SIGTERM for 30s and was killed; the net-log may end mid-event"
else
  record PASS "shutdown" "rac quit cleanly on SIGTERM"
fi

if [ -f "$_netlog" ]; then
  cp "$_netlog" "$_out_dir/netlog.json"
fi
cp "$_log" "$_out_dir/rac-capture.log" 2>/dev/null || true

if [ ! -f "$_out_dir/netlog.json" ]; then
  record FAIL "net-log" "no net-log was written at $_netlog"
  _finish
  exit $?
fi

_events="$(python3 - "$_hostlist" "$_out_dir/netlog.json" <<'EOF'
import importlib.util, sys
spec = importlib.util.spec_from_file_location('hostlist', sys.argv[1])
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
with open(sys.argv[2], encoding='utf-8') as f:
    print(len(m.parse_netlog(f.read())[1]))
EOF
)"

if [ "${_events:-0}" -gt 0 ]; then
  record PASS "net-log" "$_events events captured"
else
  record FAIL "net-log" "netlog.json holds no complete events (browser died too early?)"
fi

python3 "$_hostlist" hosts "$_out_dir/netlog.json" > "$_out_dir/hosts.txt"
python3 "$_hostlist" hosts "$_out_dir/netlog.json" --json > "$_out_dir/hosts.json"

_compare_out="$_work/compare.txt"
_compare_rc=0
python3 "$_hostlist" compare "$_out_dir/netlog.json" --list "$_list" \
  > "$_compare_out" 2>&1 || _compare_rc=$?
cat "$_compare_out"
if [ "$_compare_rc" = 0 ]; then
  record PASS "host list" "every host seen is published in $(basename "$_list")"
elif [ "$_compare_rc" = 1 ]; then
  _unlisted="$(awk '/^error: seen but not listed/{f=1;next} /^info:|^ok:|^warning:/{f=0} f&&/^  /{n++} END{print n+0}' "$_compare_out")"
  record FAIL "host list" "$_unlisted hosts seen but not listed in $(basename "$_list"); update it or explain them"
else
  record FAIL "host list" "compare itself failed (see net-capture.md)"
fi

_finish
_rc=$?
{
  echo '### Hosts seen'
  echo
  echo '```'
  cat "$_out_dir/hosts.txt"
  echo '```'
  echo
  echo '### Compare with the published list'
  echo
  echo '```'
  cat "$_compare_out"
  echo '```'
} >> "$_out_dir/net-capture.md"
exit "$_rc"
