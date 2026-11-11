#!/bin/bash
# Network capture: mounts a rac disk image, copies rac.app out, launches it
# once on a throwaway profile with net-log recording on, waits, and shuts it
# down. The captured hosts are compared against the published list in
# docs/network.md (launch gate G10: rac's promise of nothing phoning home is
# proven by recording, not asserted). Writes <out>/net-capture.md (one line
# per check plus the host list), <out>/netlog.json, <out>/hosts.txt,
# <out>/hosts.json, and <out>/rac-capture.log, plus <out>/os-hosts.txt: the
# hosts rac's processes reached according to the OS (DNS and new
# connections from tcpdump, rac's sockets from polled lsof), which covers
# traffic outside Chromium's network stack that the net-log can't see, such
# as Sparkle's update check through NSURLSession. The raw os-*.txt records
# are kept next to it.
#
# Usage: github_net_capture.sh <rac.dmg> <out-dir> [--minutes N] [--services off|on]
#                              [--first-run skip|onboarding-open|onboarding-closed] [--list doc.md]
#
#   --minutes N     How long the browser sits on its fresh window before
#                   shutdown. Default 10. Keep it under ~20; the workflow's
#                   timeout is 30 minutes.
#   --services on   Seed Helium services consent into the profile before
#                   launch, so the capture also records what a user who
#                   turns them on reaches. Default off: a fresh profile
#                   never consented, so nothing touches Helium's servers.
#   --first-run M   skip (default): launch with --no-first-run, which skips
#                   rac's welcome tour. onboarding-open: launch without it,
#                   so a real first launch shows the tour, and leave it
#                   open for the whole idle. onboarding-closed: same, then
#                   after ~30s close the tour without finishing it, the way
#                   a user does with the red button, and idle on the
#                   browser window that opens. Closing writes no pref
#                   (patches/rac/onboarding/04-window-first-and-polish.patch
#                   runs the launch continuation from the tour's destructor;
#                   only the "done" step writes helium.completed_onboarding),
#                   so consent stays off and the tour is still pending.
#                   The tour is a views window that AppleScript can't see,
#                   so the close goes through the DevTools HTTP endpoint
#                   (close_onboarding.py, needs --remote-debugging-port on
#                   loopback, which the capture reports separately), with
#                   System Events clicking the close button as a fallback
#                   that needs Accessibility permission on the runner.
#                   Seeding prefs instead would not be faithful: the tour
#                   shows until helium.completed_onboarding is true, and
#                   closing it early leaves that false.
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
_os_hosts="$_repo/devutils/rac/os_hosts.py"
_smoke_py="$_here/release_smoke.py"

_dmg=""
_out_dir=""
_minutes=10
_services="off"
_first_run="skip"
_close_py="$_here/close_onboarding.py"
_list="$_repo/docs/network.md"

while [ $# -gt 0 ]; do
  case "$1" in
    --minutes|--services|--first-run|--list)
      if [ $# -lt 2 ]; then
        echo "error: $1 needs a value" >&2
        exit 2
      fi
      case "$1" in
        --minutes) _minutes="$2" ;;
        --services) _services="$2" ;;
        --first-run) _first_run="$2" ;;
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
  echo "usage: $0 <rac.dmg> <out-dir> [--minutes N] [--services off|on] [--first-run skip|onboarding-open|onboarding-closed] [--list doc.md]" >&2
  exit 2
fi
case "$_services" in
  off|on) ;;
  *) echo "error: --services must be off or on, not '$_services'" >&2; exit 2 ;;
esac
case "$_first_run" in
  skip|onboarding-open|onboarding-closed) ;;
  *) echo "error: --first-run must be skip, onboarding-open or onboarding-closed, not '$_first_run'" >&2; exit 2 ;;
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
_stopped_for=0
_stop_app() {
  [ -n "$_pid" ] || return 0
  kill "$_pid" 2>/dev/null || true
  _stopped=0
  while kill -0 "$_pid" 2>/dev/null && [ "$_stopped" -lt 30 ]; do
    sleep 1
    _stopped=$((_stopped + 1))
  done
  _stopped_for=$_stopped
  if kill -0 "$_pid" 2>/dev/null; then _killed=1; kill -9 "$_pid" 2>/dev/null || true; fi
  wait "$_pid" 2>/dev/null || true
  _pid=""
}

# The OS-level record: two root tcpdumps (their pids in pidfiles, since a
# root process can't be signaled by the runner user) and an lsof poller.
_os_dir=""
_os_poller=""
_os_stop() {
  [ -n "$_os_dir" ] || return 0
  [ -z "$_os_poller" ] || { kill "$_os_poller" 2>/dev/null || true; wait "$_os_poller" 2>/dev/null || true; }
  _os_poller=""
  local f
  for f in "$_os_dir"/tcpdump-*.pid; do
    [ -f "$f" ] || continue
    sudo -n kill "$(cat "$f")" 2>/dev/null || true
    rm -f "$f"
  done
  sleep 1
}

_cleanup() {
  _os_stop
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
    --title "Network capture (services $_services, first-run $_first_run)" --results "$_results" \
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
  if [ "$_first_run" = "skip" ]; then
    cat > "$_profile/Default/Preferences" <<'EOF'
{"helium":{"services":{"enabled":true,"user_consented":true},"completed_onboarding":true}}
EOF
    record PASS "profile" "seeded helium.services.enabled + user_consented into Default/Preferences"
  else
    # A real first launch must still show the tour, so completed_onboarding
    # stays unset; only the consent is seeded.
    cat > "$_profile/Default/Preferences" <<'EOF'
{"helium":{"services":{"enabled":true,"user_consented":true}}}
EOF
    record PASS "profile" "seeded helium.services consent only (completed_onboarding left unset so the tour shows)"
  fi
else
  record PASS "profile" "fresh throwaway profile; nothing consented to Helium services"
fi

# Record rac's traffic from outside Chromium too. Sparkle checks the update
# feed with NSURLSession in the main process, which --log-net-log never
# sees. Flush the OS DNS cache first so rac's lookups reach the wire even
# for names the runner resolved already (github.com, for the checkout).
_os_dir="$_work/os"
mkdir -p "$_os_dir"
_os_started=0
if sudo -n true 2>/dev/null; then
  sudo -n dscacheutil -flushcache 2>/dev/null || true
  sudo -n killall -HUP mDNSResponder 2>/dev/null || true
  # $1: name, $2: output, rest: tcpdump args. pktap covers every interface
  # and tags packets with the process that sent them.
  _os_tcpdump() {
    local name=$1 out=$2
    shift 2
    sudo -n sh -c 'echo $$ > "$1"; shift; exec tcpdump "$@"' _ \
      "$_os_dir/tcpdump-$name.pid" "$@" > "$out" 2> "$_os_dir/tcpdump-$name.err" &
  }
  _os_tcpdump dns "$_os_dir/os-dns.txt" -i pktap -n -l -vv 'port 53'
  _os_tcpdump syn "$_os_dir/os-syn.txt" -i pktap -k NP -n -l \
    'tcp[tcpflags] & (tcp-syn|tcp-ack) == tcp-syn'
  sleep 2
  # A tcpdump that couldn't open pktap has exited by now; record DNS on the
  # primary interface instead (no process tags needed for DNS).
  if [ ! -s "$_os_dir/tcpdump-dns.pid" ] || ! sudo -n kill -0 "$(cat "$_os_dir/tcpdump-dns.pid")" 2>/dev/null; then
    _os_tcpdump dns "$_os_dir/os-dns.txt" -i en0 -n -l -vv 'port 53'
    sleep 1
  fi
  _os_started=1
fi
(
  while :; do
    _pids="$(pgrep -f -- "$_app/Contents/" | paste -sd, - || true)"
    if [ -n "$_pids" ]; then
      echo "# $(date +%s)"
      lsof -nP -a -p "$_pids" -i 2>/dev/null || true
    fi
    sleep 1
  done
) > "$_os_dir/os-lsof.txt" 2>/dev/null &
_os_poller=$!

# Launch with the net-log recorder on and nothing to navigate to. Deliberately
# no --custom-update-server-url: the capture must show the real feed check.
_log="$_work/rac.log"
_launch_args=(--user-data-dir="$_profile" --no-default-browser-check)
if [ "$_first_run" = "skip" ]; then
  _launch_args+=(--no-first-run)
elif [ "$_first_run" = "onboarding-closed" ]; then
  # Loopback only; the DevTools endpoint is how the tour gets closed.
  _launch_args+=(--remote-debugging-port=0)
fi
env BREAKPAD_DUMP_LOCATION="$_profile/Crashpad" \
  "$_exe" "${_launch_args[@]}" \
  --use-mock-keychain --disable-backgrounding-occluded-windows \
  --log-net-log="$_netlog" --net-log-capture-mode=Default \
  > "$_log" 2>&1 &
_pid=$!

_seconds=$((_minutes * 60))
_waited=0
if [ "$_first_run" = "onboarding-closed" ]; then
  # Let the tour show and settle first, then close it without finishing.
  sleep 30
  _close_method=""
  if python3 "$_close_py" "$_profile" --wait 60; then
    _close_method="DevTools HTTP close of chrome://setup"
  elif osascript -e 'tell application "System Events" to tell (first process whose unix id is '"$_pid"') to click button 1 of window 1' >/dev/null 2>&1; then
    _close_method="System Events click on the window close button"
  fi
  if [ -n "$_close_method" ]; then
    record PASS "onboarding" "tour shown, then closed without finishing via $_close_method; no consent given"
  else
    record FAIL "onboarding" "could not close the tour (DevTools endpoint and System Events both failed); the rest of the run is an onboarding-open capture"
  fi
  _waited=35
  sleep 5
elif [ "$_first_run" = "onboarding-open" ]; then
  record PASS "onboarding" "launched without --no-first-run; tour left open"
fi
while [ "$_waited" -lt "$_seconds" ]; do
  kill -0 "$_pid" 2>/dev/null || break
  sleep 5
  _waited=$((_waited + 5))
done
if kill -0 "$_pid" 2>/dev/null; then
  record PASS "capture" "rac idled for ${_minutes}m with the net-log on (first-run $_first_run)"
else
  record FAIL "capture" "rac exited after ${_waited}s (see rac-capture.log in the artifact)"
fi
_stop_app
_os_stop
if [ "$_killed" = 1 ]; then
  record SKIP "shutdown" "rac ignored SIGTERM for 30s and was killed; the net-log may end mid-event"
else
  record PASS "shutdown" "rac quit on SIGTERM within ${_stopped_for}s; the net-log was flushed"
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

# With services on, the ```hosts services block (what consenting adds)
# counts too; a services-off capture is held to the default list alone.
_also=()
[ "$_services" != "on" ] || _also=(--also services)

if [ "${_events:-0}" -gt 0 ]; then
  record PASS "net-log" "$_events events captured"
else
  record FAIL "net-log" "netlog.json holds no complete events (browser died too early?)"
fi

# The OS record: hosts rac's own processes reached, named from DNS. A
# resolved name missing from the published list fails like a net-log host;
# an address with no DNS answer in the record is reported, not failed.
for f in os-dns.txt os-syn.txt os-lsof.txt tcpdump-dns.err tcpdump-syn.err; do
  cp "$_os_dir/$f" "$_out_dir/$f" 2>/dev/null || true
done
python3 "$_os_hosts" --app-path "$_app" --dns "$_os_dir/os-dns.txt" \
  --syn "$_os_dir/os-syn.txt" --lsof "$_os_dir/os-lsof.txt" > "$_out_dir/os-hosts.txt" 2>&1 || true
python3 "$_os_hosts" --app-path "$_app" --dns "$_os_dir/os-dns.txt" \
  --syn "$_os_dir/os-syn.txt" --lsof "$_os_dir/os-lsof.txt" --json > "$_out_dir/os-hosts.json" 2>/dev/null || echo '[]' > "$_out_dir/os-hosts.json"
_os_compare="$_work/os-compare.txt"
_os_rc=0
python3 - "$_hostlist" "$_list" "$_out_dir/os-hosts.json" ${_also[@]+"${_also[@]}"} > "$_os_compare" <<'EOF' || _os_rc=$?
import importlib.util, ipaddress, json, sys
spec = importlib.util.spec_from_file_location('hostlist', sys.argv[1])
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
also = [a for a in sys.argv[4:] if a != '--also']
with open(sys.argv[2], encoding='utf-8') as f:
    patterns, _ = m.parse_host_list(f.read(), also)
entries = json.load(open(sys.argv[3]))
unlisted, unresolved = [], []
for e in entries:
    try:
        ipaddress.ip_address(e['host']); unresolved.append(e); continue
    except ValueError:
        pass
    if not m.host_listed(e['host'], patterns):
        unlisted.append(e)
for e in unlisted:
    print(f"error: reached outside the net-log but not listed: {e['host']} ({', '.join(e['processes'])})")
for e in unresolved:
    print(f"info: address with no DNS answer in the record: {e['host']} ({', '.join(e['processes'])})")
if not unlisted:
    print(f'ok: all {len(entries) - len(unresolved)} named hosts are listed')
sys.exit(1 if unlisted else 0)
EOF
if [ "$_os_started" = 0 ]; then
  record SKIP "os hosts" "no passwordless sudo for tcpdump; only lsof polling ran ($(grep -vc '^#' "$_out_dir/os-hosts.txt" 2>/dev/null || echo 0) hosts)"
elif [ "$_os_rc" = 0 ]; then
  record PASS "os hosts" "every host rac reached outside the net-log is published in $(basename "$_list")"
else
  record FAIL "os hosts" "a host rac reached outside the net-log isn't listed in $(basename "$_list") (see os-hosts.txt)"
fi

python3 "$_hostlist" hosts "$_out_dir/netlog.json" > "$_out_dir/hosts.txt"
python3 "$_hostlist" hosts "$_out_dir/netlog.json" --json > "$_out_dir/hosts.json"

_compare_out="$_work/compare.txt"
_compare_rc=0
python3 "$_hostlist" compare "$_out_dir/netlog.json" --list "$_list" ${_also[@]+"${_also[@]}"} \
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
  echo
  echo "### Hosts reached outside Chromium's net-log (OS record)"
  echo
  echo 'From tcpdump (DNS, new connections) and polled lsof of rac'"'"'s own processes.'
  echo "The main process's hosts come from NSURLSession, e.g. Sparkle's update check."
  echo
  echo '```'
  cat "$_out_dir/os-hosts.txt" 2>/dev/null
  cat "$_os_compare" 2>/dev/null
  echo '```'
} >> "$_out_dir/net-capture.md"
exit "$_rc"
