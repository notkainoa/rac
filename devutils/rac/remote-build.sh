#!/usr/bin/env bash
# Runs rac's heavy work — Chromium compiles and browser launches for
# screenshots — on the maintainer's MacBook Pro over ssh, so the shared
# Air stays responsive. Threads, git, and reviews stay on the Air.
#
# usage: devutils/rac/remote-build.sh [--dry-run] <command> [args...]
#   setup-host                        check the Pro and create ~/rac-remote
#   build-base [--resume] [--approved "who/when"] <ref>
#                                     fetch <ref> from GitHub on the Pro and
#                                     cold-build its base tree there
#   push <worktree>                   push its committed state, making or
#                                     updating its clone
#   build <worktree> [-- targets...]  build the clone through the remote queue
#   run <worktree> [--timeout S] [--requests-file F] [--fresh-profile]
#       [-- args...]                  launch the clone's browser directly (no
#                                     UI DevTools: worktree.sh run's
#                                     --enable-ui-devtools is never passed),
#                                     then stop it; --fresh-profile first
#                                     deletes the clone's throwaway
#                                     build/profile (never while a browser
#                                     from the clone runs); F is a
#                                     screenshot-requests line on the Air,
#                                     checked by remote_requests.py. After
#                                     --, args are a fixed allowlist:
#                                     --no-first-run (skip first-run UI),
#                                     --rac-launch-in-background (never
#                                     activate the browser),
#                                     --rac-import-arc-now (import at startup,
#                                     only with --rac-import-source-root=),
#                                     --rac-arc-import-fixture=<path> and
#                                     --rac-import-source-root=<path> (Arc
#                                     import inputs, relative to the clone,
#                                     that must exist there),
#                                     --rac-window-screenshot=<name>.png
#                                     (first shot; lands in build/shots) and
#                                     --rac-window-screenshot-delay=<1-4
#                                     digits> (ms before it fires),
#                                     --log-net-log=<name>.json and
#                                     --rac-frame-log=<name>.log (logs; land
#                                     in build/logs),
#                                     --net-log-capture-mode=Default|
#                                     IncludeSensitive|Everything,
#                                     --enable-logging=stderr,
#                                     --vmodule=<spec> (verbose logging),
#                                     --force-prefers-reduced-motion,
#                                     --rac-force-increased-contrast,
#                                     --disable-backgrounding-occluded-windows,
#                                     --rac-force-color-mode=light|dark|
#                                     system. A bare arg is a URL and gets
#                                     open-urls' allowlist. A run that opens
#                                     chrome://setup needs an import input; a
#                                     run that opens a settings page may only
#                                     take screenshots, so its requests file
#                                     may not send input. In the requests
#                                     line, pages and command ids are
#                                     allowlists, typed text is plain words
#                                     only, and a script that types may not
#                                     move the caret or click (at most one
#                                     `key return`, after the last type).
#   pull <worktree> <remote path> <local path>
#                                     rsync a file inside the clone back
#   log [lines]                       the base's bootstrap phases and the
#                                     end of its cold-build log
#   status                            remote uptime, disk, and build queue
#
# The remote host comes from RAC_REMOTE_HOST (default kainoas-macbook-pro).
# Everything on the Pro lives under ~/rac-remote there and nowhere else:
# the bare repos rac.git and helium-chromium.git, a base/ checkout that
# build-base fetched from GitHub and cold-built natively (the Air→Pro link
# is far too slow to copy a built tree), one clone per feature worktree in
# wt/<name>, the build queue's state in build-queue/, and the bootstrap and
# cold-build logs in logs/. The Pro is the maintainer's own Mac: no command
# here deletes anything outside ~/rac-remote, starts a build outside the
# queue, or launches a browser other than a clone's own, in the background.
set -euo pipefail

die() { echo "rac remote: $*" >&2; exit 1; }
refuse() { echo "rac remote: refusing: $*" >&2; exit 2; }
log() { echo "rac remote: $*" >&2; }
# The comment block at the top of this file is the manual.
usage() {
  awk 'NR == 1 { next } /^#/ { sub(/^# ?/, ""); print; next } { exit }' "$0"
}
here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)

host=${RAC_REMOTE_HOST:-kainoas-macbook-pro}
# A host starting with - or holding spaces would reach ssh as options.
case "$host" in
  -* | '' | *[!A-Za-z0-9._@-]*)
    echo "rac remote: RAC_REMOTE_HOST must be a plain host name, not '$host'" >&2
    exit 2 ;;
esac
# The remote root, relative to the remote home so a different $HOME (such
# as a test's) moves the whole thing.
rdir=rac-remote
repo="$host:$rdir/rac.git"
core_repo="$host:$rdir/helium-chromium.git"
# The repo the Pro clones its base from; tests point it at a local fixture.
repo_url=${RAC_REMOTE_REPO_URL:-https://github.com/notkainoa/rac.git}
# Free disk setup-host wants under the remote home, in GB. build-base sets
# its own floor (a cold Chromium build needs much more).
min_free_gb=${RAC_REMOTE_MIN_FREE_GB:-60}
# A non-interactive ssh has no Homebrew on PATH, so quilt, greadlink, and
# Homebrew's python3 would look missing; prepend it to every remote
# command's PATH.
rpath_prefix=${RAC_REMOTE_PATH_PREFIX:-/opt/homebrew/bin:/opt/homebrew/sbin}
# Cores the Pro keeps for its owner while a build runs.
reserve_cores=${RAC_REMOTE_RESERVE_CORES:-4}
# Seconds a run may wait on the Pro's queue for a run slot on top of the
# browser's own --timeout, which only starts once the slot is granted.
queue_wait=${RAC_REMOTE_QUEUE_WAIT:-1800}
dry=0
# Never stop at a password or host-key prompt; fail instead. git and rsync
# use the same ssh, and a dead or unreachable Pro fails fast.
ssh_cmd=(ssh -o BatchMode=yes -o ConnectTimeout=15)
export GIT_SSH_COMMAND="ssh -o BatchMode=yes -o ConnectTimeout=15"

# Runs "$@" unless --dry-run was given; then prints the command instead.
run_dry() {
  if [ "$dry" = 1 ]; then
    printf '+' >&2
    printf ' %q' "$@" >&2
    printf '\n' >&2
    return 0
  fi
  "$@"
}

# Functions the remote scripts share, sent ahead of every one and eval'd
# here so the same code serves the local checks. xcode_dir picks the Xcode
# to hand gn and siso (the same logic worktree.sh uses). only_patch_state
# reads `git status --porcelain` on stdin and exits 0 when it holds only
# what a merged patch stack explains: patches/series deleted, and untracked
# files under patches/ (series.merged and Helium's merged copies), except a
# new rac patch under patches/rac/ that was never committed, plus the
# .rac-toolchain record clones made by an earlier version keep at their
# top; anything else untracked is real work only a commit can carry.
# inside_clone fails when
# its second argument leaves the real path of clone $1 -- the probe is the
# path itself, or its parent when it doesn't exist yet, resolved with
# os.path.realpath so a symlinked directory on the way out counts.
# safe_name accepts a clone name that can't leave wt/. The rest serve the
# Pro side only and are described where they are defined.
read -r -d '' REMOTE_LIB <<'EOS' || true
xcode_dir() {
  local dir
  for dir in "${DEVELOPER_DIR:-}" "$(xcode-select -p 2>/dev/null || true)"; do
    case "$dir" in *.app | *.app/) dir="${dir%/}/Contents/Developer" ;; esac
    if [ -n "$dir" ] && [ -x "$dir/usr/bin/xcodebuild" ]; then
      echo "$dir"
      return 0
    fi
  done
  for dir in /Applications/Xcode.app /Applications/Xcode*.app; do
    if [ -x "$dir/Contents/Developer/usr/bin/xcodebuild" ]; then
      echo "$dir/Contents/Developer"
      return 0
    fi
  done
  echo "rac remote: gn and siso need Xcode; install it or set DEVELOPER_DIR" >&2
  return 1
}

only_patch_state() {
  [ -z "$(awk '/^\?\? "?patches\/rac\// { print; next }
    /^\?\? "?patches\// { next }
    /^\?\? "?\.rac-toolchain"?$/ { next }
    /^\?\? / { print; next }
    /^.?D "?patches\/series"?$/ { next }
    { print }')" ]
}

inside_clone() {
  local probe=$2
  [ -d "$1" ] || return 1
  [ -e "$probe" ] || [ -L "$probe" ] || probe=$(dirname "$probe")
  python3 -c 'import os.path, sys; r = os.path.realpath(sys.argv[1]); p = os.path.realpath(sys.argv[2]); sys.exit(0 if p == r or p.startswith(r + os.sep) else 1)' \
    "$1" "$probe"
}

safe_name() {
  case "$1" in
    '' | .* | *[!A-Za-z0-9._-]*) return 1 ;;
  esac
}

# The toolchain record a tree answers to: a clone's own copy in its
# (ignored) build/, inherited from the base at setup; a checkout's own
# .rac-toolchain (the base's, or an older clone's); else the base's.
toolchain_record() {
  if [ -f "$1/build/.rac-toolchain" ]; then
    echo "$1/build/.rac-toolchain"
  elif [ -f "$1/.rac-toolchain" ]; then
    echo "$1/.rac-toolchain"
  else
    echo "$HOME/rac-remote/base/.rac-toolchain"
  fi
}

# Refuses when the Pro's Xcode build or SDK drifted from the record the
# tree was built with: a build under another toolchain recompiles all of
# Chromium. $1 is a clone or base dir; a missing record passes (a base
# whose bootstrap never started records nothing), a partial one refuses.
# The record is the xcodebuild -version output plus SDK, DEVELOPER_DIR=,
# and commit lines -- the shape a by-hand bootstrap writes -- and the
# older xcode_build/sdk key lines still parse too.
check_toolchain_record() {
  local record xcode rver rbuild rsdk was_build was_sdk
  record=$(toolchain_record "$1")
  [ -f "$record" ] || return 0
  was_build=$(awk '/^xcode_build / { print $2; exit }
                  /^Build version / { print $3; exit }' "$record")
  was_sdk=$(awk 'tolower($1) == "sdk" { print $2; exit }' "$record")
  if [ -z "$was_build" ] || [ -z "$was_sdk" ]; then
    echo "rac remote: refusing: $record has no Xcode build or SDK line;" >&2
    echo "  can't tell which toolchain built this tree" >&2
    return 2
  fi
  xcode=$(xcode_dir) || return 1
  rver=$(DEVELOPER_DIR=$xcode xcodebuild -version)
  rbuild=${rver##*Build version }
  rsdk=$(DEVELOPER_DIR=$xcode xcrun --show-sdk-version)
  if [ "$rbuild" != "$was_build" ] || [ "$rsdk" != "$was_sdk" ]; then
    echo "rac remote: refusing: the Pro's Xcode changed since the base was built" >&2
    echo "  (was Xcode $was_build/SDK $was_sdk, now $rbuild/SDK $rsdk); a build" >&2
    echo "  now would recompile everything. Put Xcode $was_build/SDK $was_sdk" >&2
    echo "  back on the Pro, or ask the maintainer about a new base." >&2
    return 2
  fi
}

# Prints the entry and succeeds when the Pro's build queue holds or queues
# work for checkout $1: a slot holder or waiting ticket whose worktree is
# $1 and whose queue process (or, for a holder, its build's process group)
# still lives. An entry without a pid counts as live, and so does a queue
# this can't read: the answer fails closed.
queue_busy() {
  local status=0
  python3 -c '
import glob, json, os, sys
want = os.path.realpath(sys.argv[1])
root = sys.argv[2]
def alive(pid, group=False):
    if not isinstance(pid, int) or pid <= 1:
        return False
    try:
        (os.killpg if group else os.kill)(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True
entries = glob.glob(os.path.join(root, "*", "holder.json"))
entries += glob.glob(os.path.join(root, "waiting", "*.json"))
for path in sorted(entries):
    try:
        with open(path) as f:
            data = json.load(f)
    except (OSError, ValueError):
        continue
    if not isinstance(data, dict) or not isinstance(data.get("worktree"), str):
        continue
    if os.path.realpath(data["worktree"]) != want:
        continue
    pid = data.get("pid")
    if pid is None or alive(pid) or alive(data.get("pgid"), group=True):
        note = data.get("note") or ""
        print("%s, pid %s%s" % (path, pid, " [%s]" % note if note else ""))
        sys.exit(0)
sys.exit(3)
' "$1" "${RAC_BUILD_QUEUE_DIR:-$HOME/rac-remote/build-queue}" || status=$?
  case "$status" in
    0) return 0 ;;
    3) return 1 ;;
  esac
  echo "couldn't read the build queue's state"
}

# Prints the pids of processes whose command line names a path under $1
# (as given or as its real path), other than this shell.
tree_procs() {
  local real
  real=$(cd "$1" 2>/dev/null && pwd -P) || real=$1
  ps -axo pid=,command= | P="$1/" P2="$real/" SELF="$$" \
    awk '(index($0, ENVIRON["P"]) || index($0, ENVIRON["P2"])) && $1 != ENVIRON["SELF"] { print $1 }'
}

# A base whose bootstrap finished: patches merged and applied through quilt,
# the applied stack recorded by worktree.sh sync, and gn's files generated.
base_prepared() {
  [ -f "$1/patches/series.merged" ] \
    && [ -f "$1/build/src/.pc/applied-patches" ] \
    && [ -f "$1/build/src/.pc/.rac_applied" ] \
    && [ -f "$1/build/src/out/Default/build.ninja" ]
}

# A build-base bootstrap holds an flock on this file (through a descriptor
# its children inherit) for as long as any part of it runs, even after the
# ssh session that started it went away.
bootstrap_lock="$HOME/rac-remote/logs/.bootstrap.lock"
bootstrap_running() {
  [ -f "$bootstrap_lock" ] || return 1
  ! python3 -c 'import fcntl, sys; f = open(sys.argv[1], "a"); fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)' \
    "$bootstrap_lock" 2>/dev/null
}

# Prints one phase line, `rac remote: [<time>] <phase>…`, to the caller and
# to the bootstrap log `log` reads. Neither write can fail the caller: the
# ssh session that would show it may be long gone.
beat() {
  local line
  line="rac remote: [$(date '+%Y-%m-%d %H:%M:%S')] $*…"
  mkdir -p "$HOME/rac-remote/logs" 2>/dev/null || true
  printf '%s\n' "$line" >> "$HOME/rac-remote/logs/bootstrap.log" 2>/dev/null || true
  printf '%s\n' "$line" 2>/dev/null || true
}
EOS
eval "$REMOTE_LIB"

# Runs the stdin script on the remote host with "$@" as its arguments.
# Remote stdout and stderr stream back, and ssh returns the exit status.
# The arguments travel inside the script (quoted for bash by printf %q),
# so the Pro's login shell, which may be zsh, only ever sees a fixed
# command. The script is wrapped in a function so bash reads all of it
# before running any of it: a dropped connection can't run half a script,
# and no command it runs can read the rest of the script from stdin.
remote() {
  local command script
  command=$(printf 'PATH=%q:$PATH bash -s' "$rpath_prefix")
  script=$(
    printf '%s\n' "$REMOTE_LIB"
    # git never looks above ~/rac-remote for a repository.
    printf '%s\n' 'export GIT_CEILING_DIRECTORIES="$HOME/rac-remote"'
    printf '%s\n' 'export RAC_BUILD_QUEUE_DIR="$HOME/rac-remote/build-queue"'
    # gn picks sccache as the compiler wrapper when it's installed; keep a
    # server this starts caching under ~/rac-remote, not ~/Library/Caches.
    printf '%s\n' 'export SCCACHE_DIR="$HOME/rac-remote/sccache"'
    printf '%s\n' 'rac_main() {'
    cat
    printf '\n%s\n' '}'
    printf 'set --'
    [ $# = 0 ] || printf ' %q' "$@"
    printf '\n%s\n' 'rac_main "$@" </dev/null'
  )
  if [ "$dry" = 1 ]; then
    printf '+ %s %s %s\n' "${ssh_cmd[*]}" "$host" "$command" >&2
    printf '%s\n' "$script" | sed 's/^/|   /' >&2
    return 0
  fi
  printf '%s\n' "$script" | "${ssh_cmd[@]}" "$host" "$command"
}

# The transfer rsync and its flags. Homebrew's GNU rsync is preferred;
# macOS's openrsync (protocol 29) has no --info=progress2, and a per-file
# --progress would print a line for each of the tree's ~500k files, so it
# gets --stats instead. The remote end stays openrsync either way; a GNU
# client talks to it fine. No transfer uses --delete.
xrsync() {
  local bin version
  bin=${RAC_RSYNC:-}
  if [ -z "$bin" ]; then
    if [ -x /opt/homebrew/bin/rsync ]; then
      bin=/opt/homebrew/bin/rsync
    else
      bin=rsync
    fi
  fi
  version=$("$bin" --version 2>/dev/null || true)
  local -a flags
  case "${version%%$'\n'*}" in
    *openrsync*) flags=(-a --partial --stats) ;;
    *) flags=(-a --partial --info=progress2) ;;
  esac
  run_dry "$bin" -e "${ssh_cmd[*]}" "${flags[@]}" "$@"
}

# Prints both machines' Xcode build and macOS SDK version. They don't have
# to match: the Pro builds its own base from GitHub with its own Xcode.
# What matters is that a tree is built and used with one toolchain, which
# base/.rac-toolchain records and check_toolchain_record enforces.
show_toolchain() {
  local xcode ver build sdk
  xcode=$(xcode_dir) || exit 1
  ver=$(DEVELOPER_DIR=$xcode xcodebuild -version)
  build=${ver##*Build version }
  ver=${ver%%$'\n'*}
  sdk=$(DEVELOPER_DIR=$xcode xcrun --show-sdk-version)
  [ -n "$build" ] || die "couldn't read this Mac's Xcode build version"
  [ -n "$sdk" ] || die "couldn't read this Mac's SDK version"
  remote "$ver" "$build" "$sdk" <<'EOS'
set -e
xcode=$(xcode_dir) || exit 1
rver=$(DEVELOPER_DIR=$xcode xcodebuild -version)
rbuild=${rver##*Build version }
rver=${rver%%$'\n'*}
rsdk=$(DEVELOPER_DIR=$xcode xcrun --show-sdk-version)
echo "this Mac: $1 (build $2, SDK $3)"
echo "the Pro:  $rver (build $rbuild, SDK $rsdk)"
if [ "$rbuild" != "$2" ] || [ "$rsdk" != "$3" ]; then
  echo "note: the toolchains differ, which is fine; the Pro builds its own"
  echo "base with its Xcode $rbuild/SDK $rsdk (recorded in base/.rac-toolchain)"
fi
EOS
}

# The physical top of the worktree holding $1.
worktree_root() {
  local top
  top=$(git -C "$1" rev-parse --show-toplevel 2>/dev/null) || die "no git worktree at $1"
  (cd "$top" && pwd -P)
}

# A worktree's remote clone name is its folder name. Two worktrees with
# the same folder name would share a clone; push refuses when the clone is
# on another branch.
clone_name() {
  local root name
  root=$(worktree_root "$1") || exit 1
  name=$(basename "$root")
  safe_name "$name" || die "can't name a clone after '$name'; worktree folder names need letters, digits, '.', '_', or '-', and no leading '.'"
  echo "$name"
}

cmd_setup_host() {
  case "$min_free_gb" in
    '' | *[!0-9]*)
      die "RAC_REMOTE_MIN_FREE_GB must be a whole number, not '$min_free_gb'" ;;
  esac
  show_toolchain
  remote "$min_free_gb" <<'EOS'
set -e
echo "host: $(hostname)"
echo "macOS: $(sw_vers -productVersion)"
echo "cores: $(sysctl -n hw.ncpu)"
echo "RAM: $(($(sysctl -n hw.memsize) / 1073741824)) GB"
free=$(df -g "$HOME" | awk 'NR==2 {print $4}')
case "$free" in
  '' | *[!0-9]*)
    echo "rac remote: refusing: couldn't read free disk under $HOME" >&2
    exit 2 ;;
esac
echo "free disk under $HOME: ${free} GB"
if [ "$free" -lt "$1" ]; then
  echo "rac remote: refusing: ${free} GB free under $HOME, under the $1 GB floor" >&2
  exit 2
fi
missing=
for tool in rsync git python3 caffeinate quilt greadlink; do
  command -v "$tool" >/dev/null 2>&1 || missing="$missing $tool"
done
if [ -n "$missing" ]; then
  echo "rac remote: missing tools on the Pro:$missing" >&2
  for tool in $missing; do
    case "$tool" in
      greadlink) echo "  install with: brew install coreutils" >&2 ;;
      caffeinate) echo "  caffeinate ships with macOS; something is wrong with the remote PATH" >&2 ;;
      *) echo "  install with: brew install $tool" >&2 ;;
    esac
  done
  exit 2
fi
mkdir -p "$HOME/rac-remote"
cd "$HOME/rac-remote"
for r in rac.git helium-chromium.git; do
  [ -d "$r" ] || git init --bare -q "$r"
done
# Clones' submodule updates fetch pinned commits by sha, and a pin need
# not be an advertised ref, so the bare repo serves any commit it holds.
git -C helium-chromium.git config uploadpack.allowAnySHA1InWant true
echo "rac remote: ready at $HOME/rac-remote"
EOS
}

# Queues the base's cold build on the Pro, detached from this ssh session
# (nohup plus a new session via python3 os.setsid) so it survives a dropped
# connection; its output lands in ~/rac-remote/logs/cold-build.log for `log`
# to tail. It refuses while anything already builds or bootstraps the base:
# a second cold build would only fight the first for the tree. The tree
# keeps one toolchain for life, so an existing record is checked, never
# rewritten; a missing one is stamped with what the Pro runs at launch.
start_cold_build() {
  remote "$@" <<'EOS'
set -e
note=$1
reserve=$2
ref=$3
floor=$4
base="$HOME/rac-remote/base"
[ -d "$base" ] || {
  echo "rac remote: no base checkout at $base; run build-base <ref> first" >&2
  exit 1
}
cd "$base"
if [ -n "$ref" ]; then
  commit=$(git rev-parse -q --verify "refs/tags/$ref^{commit}" 2>/dev/null \
    || git rev-parse -q --verify "refs/remotes/origin/$ref" 2>/dev/null \
    || git rev-parse -q --verify "$ref^{commit}" 2>/dev/null || true)
  [ -n "$commit" ] || {
    echo "rac remote: refusing: base has no ref '$ref'; run: build-base $ref" >&2
    exit 2
  }
  if [ "$(git rev-parse HEAD)" != "$commit" ]; then
    echo "rac remote: refusing: base is not at $ref; run: build-base $ref" >&2
    exit 2
  fi
fi
base_prepared "$base" || {
  echo "rac remote: refusing: base has no patched, configured Chromium tree" >&2
  echo "  at $base/build/src (its bootstrap never finished); run: build-base <ref>" >&2
  exit 2
}
if busy=$(queue_busy "$base"); then
  echo "rac remote: refusing: the Pro's queue already holds or queues a build" >&2
  echo "  of the base ($busy); follow it with status and log" >&2
  exit 2
fi
if bootstrap_running; then
  echo "rac remote: refusing: a build-base bootstrap is still running; see: log" >&2
  exit 2
fi
procs=$(tree_procs "$base/build/src")
[ -z "$procs" ] || {
  echo "rac remote: refusing: processes are still running under $base/build/src:" >&2
  echo "$procs" >&2
  exit 2
}
free=$(df -g "$HOME" | awk 'NR==2 {print $4}')
case "$free" in
  '' | *[!0-9]*)
    echo "rac remote: refusing: couldn't read free disk under $HOME" >&2
    exit 2 ;;
esac
if [ "$free" -lt "$floor" ]; then
  echo "rac remote: refusing: ${free} GB free under $HOME, under the" >&2
  echo "$floor GB floor a cold Chromium build needs" >&2
  exit 2
fi
check_toolchain_record "$base"
xcode=$(xcode_dir) || exit 1
if [ ! -f .rac-toolchain ]; then
  # The record's shape matches what a by-hand bootstrap writes: the
  # xcodebuild -version output, then SDK, DEVELOPER_DIR=, and commit lines.
  { DEVELOPER_DIR=$xcode xcodebuild -version
    echo "SDK $(DEVELOPER_DIR=$xcode xcrun --show-sdk-version)"
    echo "DEVELOPER_DIR=$xcode"
    echo "commit $(git rev-parse HEAD)"
  } > .rac-toolchain
fi
cores=$(sysctl -n hw.ncpu)
jobs=$(( cores > reserve ? cores - reserve : 1 ))
src="$base/build/src"
mkdir -p "$HOME/rac-remote/logs"
log="$HOME/rac-remote/logs/cold-build.log"
beat "queueing the cold build ($note)"
nohup python3 -c 'import os,sys; os.setsid(); os.execvp(sys.argv[1], sys.argv[1:])' \
  nice -n 10 taskpolicy -c utility devutils/rac/build-queue.sh \
  --full "$note" --allow-main --priority \
  bash -c 'cd "$1" && shift && exec "$@"' rac-base "$src" \
  env "SISO_PATH=$src/third_party/siso/cipd/siso" "DEVELOPER_DIR=$xcode" \
  python3 third_party/depot_tools/autoninja.py -C out/Default \
  chrome chromedriver "-local_jobs=$jobs" -k 0 \
  >> "$log" 2>&1 < /dev/null &
pid=$!
# The queue refuses some things only once it runs (a blank note, too little
# disk for its own floor); wait until it has queued the build, or say why
# it ended.
tries=40
while :; do
  if queue_busy "$base" >/dev/null; then
    echo "cold build for base queued detached, pid $pid (log: $log)" >&2
    break
  fi
  if ! kill -0 "$pid" 2>/dev/null; then
    status=0
    wait "$pid" || status=$?
    if [ "$status" = 0 ]; then
      echo "cold build for base already finished (log: $log)" >&2
      exit 0
    fi
    beat "the cold build's queue exited $status"
    echo "rac remote: the cold build's queue exited $status; the end of $log:" >&2
    tail -n 15 "$log" >&2 || true
    exit 1
  fi
  tries=$((tries - 1))
  if [ "$tries" -le 0 ]; then
    echo "rac remote: started the cold build (pid $pid), but the queue hasn't" >&2
    echo "  listed it yet; check: remote-build.sh status" >&2
    break
  fi
  sleep 0.5
done
echo "follow it with:" >&2
echo "  remote-build.sh status    who holds the Pro's queue slots" >&2
echo "  remote-build.sh log       bootstrap phases and the cold-build log" >&2
EOS
}

cmd_build_base() {
  local ref=$1 resume=$2 approved=$3
  # A cold Chromium build needs far more disk than a running remote does.
  local floor=${RAC_REMOTE_MIN_FREE_GB:-120}
  case "$floor" in
    '' | *[!0-9]*)
      die "RAC_REMOTE_MIN_FREE_GB must be a whole number, not '$floor'" ;;
  esac
  case "$reserve_cores" in
    '' | *[!0-9]*)
      die "RAC_REMOTE_RESERVE_CORES must be a whole number, not '$reserve_cores'" ;;
  esac
  if [ "$resume" = 0 ]; then
    prepare_base "$repo_url" "$ref" "$floor"
    if [ -z "$approved" ]; then
      log "the base is prepared at $host:$rdir/base; start its cold build with:"
      log "  devutils/rac/remote-build.sh build-base --resume --approved \"<who/when>\" $ref"
      return 0
    fi
  fi
  start_cold_build "$approved" "$reserve_cores" "$ref" "$floor"
}

# Fetches or clones the base from GitHub over the Pro's own internet and
# bootstraps it like the repo's first build. It never builds, never
# reclones, and never moves a base that already holds a Chromium tree to
# another ref. A base already at the ref with a finished bootstrap is
# adopted as it is; one at the ref whose bootstrap stopped picks up where
# it stopped. Each phase prints a heartbeat to the caller and to
# ~/rac-remote/logs/bootstrap.log, which also gets every step's output. The
# bootstrap survives a dropped ssh session, and its lock keeps a second one
# (or a cold build) out until it ends.
prepare_base() {
  remote "$@" <<'EOS'
set -e
repo_url=$1
ref=$2
floor=$3
mkdir -p "$HOME/rac-remote/logs"
cd "$HOME/rac-remote"
for r in rac.git helium-chromium.git; do
  [ -d "$r" ] || git init --bare -q "$r"
done
# Clones' submodule updates fetch pinned commits by sha, and a pin need
# not be an advertised ref, so the bare repo serves any commit it holds.
git -C helium-chromium.git config uploadpack.allowAnySHA1InWant true
free=$(df -g "$HOME" | awk 'NR==2 {print $4}')
case "$free" in
  '' | *[!0-9]*)
    echo "rac remote: refusing: couldn't read free disk under $HOME" >&2
    exit 2 ;;
esac
if [ "$free" -lt "$floor" ]; then
  echo "rac remote: refusing: ${free} GB free under $HOME, under the" >&2
  echo "$floor GB floor a cold Chromium build needs" >&2
  exit 2
fi
base="$HOME/rac-remote/base"
# An origin with or without .git or a trailing slash is the same repo.
same_repo() {
  local a=${1%/} b=${2%/}
  [ "${a%.git}" = "${b%.git}" ]
}
if [ -d base ]; then
  url=$(git -C base remote get-url origin 2>/dev/null || true)
  same_repo "$url" "$repo_url" || {
    echo "rac remote: refusing: base's origin is '$url', not '$repo_url'" >&2
    exit 2
  }
  # Build products and logs are untracked, and a merged stack leaves
  # patches/series deleted; only edits to tracked files block the checkout.
  dirty=$(git -C base status --porcelain \
    | grep -cvE '^\?\?|^.D "?patches/series"?$' || true)
  [ "$dirty" = 0 ] || {
    echo "rac remote: refusing: base has local changes to tracked files;" >&2
    echo "the Pro only builds, it doesn't carry edits" >&2
    exit 2
  }
  beat "fetching $repo_url into $base"
  git -C base fetch -q --no-recurse-submodules origin \
    '+refs/heads/*:refs/remotes/origin/*' '+refs/tags/*:refs/tags/*'
else
  beat "cloning $repo_url into $base"
  git clone -q "$repo_url" base
fi
commit=$(git -C base rev-parse -q --verify "refs/tags/$ref^{commit}" \
  || git -C base rev-parse -q --verify "refs/remotes/origin/$ref" \
  || git -C base rev-parse -q --verify "$ref^{commit}") || {
  echo "rac remote: no ref '$ref' in $repo_url" >&2
  exit 1
}
# Clones get the Air's pushed branches by fetching the bare rac.git.
if git -C base remote get-url air >/dev/null 2>&1; then
  git -C base remote set-url air "$HOME/rac-remote/rac.git"
else
  git -C base remote add air "$HOME/rac-remote/rac.git"
fi
head=$(git -C base rev-parse HEAD)
if [ "$head" = "$commit" ] && base_prepared "$base"; then
  # Bootstrapped already (by hand or by an earlier build-base): adopt it.
  # Rerunning the bootstrap could redownload all of Chromium.
  echo "rac remote: base is already prepared at $commit ($ref); leaving it alone"
  exit 0
fi

# From here on the bootstrap changes the base, so nothing else may be
# using it: not a second bootstrap, a queued or running build, or any
# process under its tree.
exec 9>>"$bootstrap_lock"
python3 -c 'import fcntl; fcntl.flock(9, fcntl.LOCK_EX | fcntl.LOCK_NB)' 2>/dev/null || {
  echo "rac remote: refusing: another build-base bootstrap is running; see: log" >&2
  exit 2
}
if busy=$(queue_busy "$base"); then
  echo "rac remote: refusing: the Pro's queue holds or queues a build of the" >&2
  echo "  base ($busy); bootstrapping now would pull its tree away" >&2
  exit 2
fi
procs=$(tree_procs "$base/build")
[ -z "$procs" ] || {
  echo "rac remote: refusing: processes are still running under $base/build:" >&2
  echo "$procs" >&2
  exit 2
}
if [ "$head" != "$commit" ]; then
  # A tree for another ref stays: moving it would mean unapplying and
  # reapplying the whole stack, or downloading another Chromium.
  if [ -e base/build/src ] || [ -f base/patches/series.merged ]; then
    echo "rac remote: refusing: base holds a Chromium tree or merged patches" >&2
    echo "  for $head, not $ref ($commit); build-base won't move a tree to" >&2
    echo "  another ref. Ask the maintainer how to update the base." >&2
    exit 2
  fi
  git -C base checkout -q --detach "$commit"
fi
if [ -f base/patches/series.merged ] && [ -f base/patches/series ]; then
  echo "rac remote: refusing: base has both patches/series and series.merged," >&2
  echo "  a merge that half happened; ask the maintainer to look at it" >&2
  exit 2
fi

blog="$HOME/rac-remote/logs/bootstrap.log"
# Keep going if the ssh session drops (the heartbeats only stop reaching
# the caller), and stay out of the owner's way like the builds do.
trap '' HUP PIPE
renice -n 10 -p $$ >/dev/null 2>&1 || true
phase=
report() {
  status=$?
  [ "$status" != 0 ] && [ -n "$phase" ] || return 0
  beat "stopped: $phase (exit $status)"
  echo "rac remote: the bootstrap stopped in: $phase (exit $status); the end of $blog:" >&2
  tail -n 30 "$blog" >&2 || true
}
trap report EXIT
next() {
  phase=$1
  beat "$1"
}
cd base
next "checking out helium-chromium"
# The submodule comes from GitHub over the Pro's own internet, like the
# Chromium download below.
git -c protocol.file.allow=always \
  submodule update --init --quiet helium-chromium >> "$blog" 2>&1
xcode=$(xcode_dir) || exit 1
export DEVELOPER_DIR=$xcode
# The repo's normal first build, minus `he push` (its --refresh rewrites
# patch files): download Chromium, merge, apply the stack through quilt,
# let worktree.sh sync record it with rac's dev names and version, then
# configure siso and gn. dev.sh only resolves itself relative to the
# current directory, so source it from the repo root, and outside set -e,
# which it doesn't survive. `he` steps never run in an `||`: that would
# switch off the set -e inside them.
set +e
source dev.sh >> "$blog" 2>&1
sourced=$?
set -e
[ "$sourced" = 0 ] || {
  echo "rac remote: couldn't source $base/dev.sh" >&2
  exit 1
}
next "downloading and preparing Chromium (he presetup)"
he presetup >> "$blog" 2>&1
[ -f build/src/out/Default/args.gn ] || {
  echo "rac remote: he presetup left no build/src/out/Default/args.gn; an" >&2
  echo "  earlier presetup stopped part way. Ask the maintainer before" >&2
  echo "  removing $base/build/src to start it over." >&2
  exit 1
}
if [ ! -f patches/series.merged ]; then
  next "merging patches (he merge)"
  he merge >> "$blog" 2>&1
fi
next "applying patches (quilt push -a --fuzz 0)"
quilt_base() {
  (cd build/src && QUILT_PATCHES="$base/patches" QUILT_SERIES=series.merged \
    QUILT_PATCH_OPTS="--unified --reject-format=unified" \
    quilt --quiltrc - "$@")
}
status=0
quilt_base push -a --fuzz 0 >> "$blog" 2>&1 || status=$?
# quilt exits 2 when every patch is applied already.
if [ "$status" != 0 ] && [ "$status" != 2 ]; then
  failed=$(quilt_base next 2>/dev/null || true)
  echo "rac remote: quilt push failed (exit $status) at patch ${failed:-unknown}" >&2
  phase="applying patches: ${failed:-unknown} does not apply"
  exit 1
fi
next "recording the stack and rac's names (worktree.sh sync)"
devutils/rac/worktree.sh sync >> "$blog" 2>&1
next "configuring siso and gn (he configure)"
he configure >> "$blog" 2>&1
phase=
beat "base prepared at $base ($ref)"
EOS
}

# The last few bootstrap heartbeats, so a stalled phase shows, then the end
# of the cold-build log.
cmd_log() {
  remote "$1" <<'EOS'
blog="$HOME/rac-remote/logs/bootstrap.log"
log="$HOME/rac-remote/logs/cold-build.log"
if [ -f "$blog" ]; then
  beats=$(grep -a '^rac remote: \[' "$blog" | tail -n 8 || true)
  if [ -n "$beats" ]; then
    echo "bootstrap phases ($blog):"
    printf '%s\n' "$beats"
    if bootstrap_running; then
      echo "(the bootstrap is still running)"
    fi
    echo
  fi
fi
if [ -f "$log" ]; then
  tail -n "$1" "$log"
else
  echo "rac remote: no cold-build log at $log; build-base hasn't started one"
fi
EOS
}

cmd_push() {
  local wt name=$2
  wt=$(worktree_root "$1") || exit 1
  local branch commit
  branch=$(git -C "$wt" symbolic-ref -q --short HEAD) \
    || die "$wt is on a detached HEAD"
  commit=$(git -C "$wt" rev-parse HEAD)
  git -C "$wt" status --porcelain | only_patch_state \
    || refuse "$wt has uncommitted changes or untracked files; commit them first, push sends only committed state"
  # The clone's submodule update needs the pushed commit's helium-chromium
  # pin in the Pro's bare repo; send it before the remote side needs it.
  local sub
  sub=$(git -C "$wt" ls-tree HEAD helium-chromium | awk '$2 == "commit" {print $3}')
  if [ -n "$sub" ]; then
    if remote "$sub" <<'EOS'
set -e
git -C "$HOME/rac-remote/helium-chromium.git" cat-file -e "$1^{commit}" 2>/dev/null
EOS
    then
      : # the Pro already has the pinned commit
    else
      [ -e "$wt/helium-chromium/.git" ] || die "the pushed branch pins helium-chromium $sub, the Pro's bare repo lacks it, and $wt has no helium-chromium checkout to send it from"
      run_dry git -C "$wt/helium-chromium" push --force "$core_repo" \
        "$sub:refs/heads/$branch"
    fi
  fi
  run_dry git -C "$wt" push --force "$repo" "refs/heads/$branch:refs/heads/$branch"
  remote "$name" "$branch" "$commit" <<'EOS'
set -e
safe_name "$1" || { echo "rac remote: bad clone name '$1'" >&2; exit 2; }
base="$HOME/rac-remote/base"
[ -d "$base" ] || {
  echo "rac remote: no base checkout at $base; run build-base first" >&2
  exit 1
}
clone="$HOME/rac-remote/wt/$1"
# The submodule updates below fetch pinned commits by sha; let the bare
# repo serve any commit it holds, not only advertised refs. (Set here too
# so a remote set up before this config still works.)
git -C "$HOME/rac-remote/helium-chromium.git" \
  config uploadpack.allowAnySHA1InWant true
# gn gen in setup/sync needs the toolchain the tree was built with; a clone
# without its own record yet answers to the base's.
check_toolchain_record "$clone"
# A clone without a tree gets one from setup, which clones the base's: the
# base has to be built, and not being built right now.
if [ ! -d "$clone/build/src" ]; then
  if busy=$(queue_busy "$base"); then
    echo "rac remote: refusing: the base's build is queued or running" >&2
    echo "  ($busy); push once it finishes (see: status, log)" >&2
    exit 2
  fi
  [ -f "$base/build/src/out/Default/.siso_fs_state" ] || {
    echo "rac remote: refusing: the base has no finished build to clone yet;" >&2
    echo "  run build-base first, or wait for its cold build (see: log)" >&2
    exit 2
  }
fi
if [ ! -d "$clone" ]; then
  # The pushed branch lives in the bare rac.git, which base knows as `air`.
  # --no-recurse-submodules: the new commit can pin a helium-chromium the
  # base's own submodule remote (GitHub) doesn't hold; the clone's update
  # below fetches it from the Pro's bare repo instead.
  git -C "$base" fetch -q --no-recurse-submodules \
    air "+refs/heads/$2:refs/remotes/air/$2"
  mkdir -p "$HOME/rac-remote/wt"
  # -B points the clone's branch at the pushed commit even if base kept a
  # stale branch of that name.
  git -C "$base" worktree add -q -B "$2" "$clone" "$3"
  cd "$clone"
  # The clone's helium-chromium objects come from the Pro's bare repo,
  # which is where the Air's pushed pins live -- not the GitHub url
  # .gitmodules records. --worktree keeps the override out of the shared
  # config that base's own submodule updates to GitHub rely on.
  git config extensions.worktreeConfig true
  git config --worktree submodule.helium-chromium.url \
    "$HOME/rac-remote/helium-chromium.git"
  # Seed the pinned core from the Pro's bare repo, before setup's own
  # submodule step (which would look in base's module dir and can miss it).
  sub=$(git ls-tree HEAD helium-chromium | awk '$2 == "commit" {print $3}')
  if [ -n "$sub" ]; then
    git -c protocol.file.allow=always \
      submodule update --init --quiet helium-chromium
  fi
  devutils/rac/worktree.sh setup "$base"
  # The clone keeps the toolchain record of the tree it was made from, in
  # its build/, which git ignores.
  [ ! -f "$base/.rac-toolchain" ] \
    || { mkdir -p build && cp "$base/.rac-toolchain" build/.rac-toolchain; }
else
  cd "$clone"
  [ "$(git rev-parse --show-toplevel 2>/dev/null)" = "$(pwd -P)" ] || {
    echo "rac remote: refusing: $clone is not a git worktree" >&2
    exit 2
  }
  current=$(git symbolic-ref -q --short HEAD || true)
  [ "$current" = "$2" ] || {
    echo "rac remote: refusing: $clone is on '$current', not '$2'; another" >&2
    echo "worktree with the same folder name owns it" >&2
    exit 2
  }
  # A build or browser running from this clone would lose its tree to the
  # reset below: refuse while the Pro's queue holds or queues one, or any
  # process still runs under the clone.
  if busy=$(queue_busy "$clone"); then
    echo "rac remote: refusing: a queued or running build or run owns $clone" >&2
    echo "  ($busy); let it finish or stop it first" >&2
    exit 2
  fi
  procs=$(tree_procs "$clone")
  [ -z "$procs" ] || {
    echo "rac remote: refusing: processes are still running under $clone:" >&2
    echo "$procs" >&2
    exit 2
  }
  git status --porcelain | only_patch_state || {
    echo "rac remote: refusing: $clone has local changes; pushing would lose them" >&2
    exit 2
  }
  git -C "$base" fetch -q --no-recurse-submodules \
    air "+refs/heads/$2:refs/remotes/air/$2"
  # What `he unmerge` and `he merge` call; there is no interactive he here.
  # A clone that isn't merged has nothing to unmerge.
  [ ! -f patches/series.merged ] || devutils/update_patches.sh unmerge
  git reset -q --hard "$3"
  # The pushed commit can pin a different helium-chromium; check it out.
  # The worktree override (set above for new clones, again here for ones
  # made before it existed) aims the submodule at the Pro's bare repo.
  git config extensions.worktreeConfig true
  git config --worktree submodule.helium-chromium.url \
    "$HOME/rac-remote/helium-chromium.git"
  [ ! -e helium-chromium/.git ] || git -C helium-chromium \
    remote set-url origin "$HOME/rac-remote/helium-chromium.git"
  sub=$(git ls-tree HEAD helium-chromium | awk '$2 == "commit" {print $3}')
  if [ -n "$sub" ]; then
    git -c protocol.file.allow=always \
      submodule update --init --quiet helium-chromium
  fi
  devutils/update_patches.sh merge
  if [ -d build/src ]; then
    devutils/rac/worktree.sh sync
  else
    devutils/rac/worktree.sh setup "$base"
    # A clone that just got its tree also inherits the toolchain record.
    [ ! -f "$base/.rac-toolchain" ] \
      || { mkdir -p build && cp "$base/.rac-toolchain" build/.rac-toolchain; }
  fi
fi
EOS
}

cmd_build() {
  local name=$1
  shift
  if [ $# -gt 0 ]; then
    [ "$1" = "--" ] || die "usage: remote-build.sh build <worktree> [-- targets...]"
    shift
  fi
  local target
  for target in "$@"; do
    case "$target" in
      '' | -* | *[!A-Za-z0-9_./:+-]*)
        refuse "build targets are ninja target names, not '$target'" ;;
    esac
  done
  case "$reserve_cores" in
    '' | *[!0-9]*) die "RAC_REMOTE_RESERVE_CORES must be a whole number, not '$reserve_cores'" ;;
  esac
  remote "$name" "$reserve_cores" "$@" <<'EOS'
set -e
safe_name "$1" || { echo "rac remote: bad clone name '$1'" >&2; exit 2; }
clone="$HOME/rac-remote/wt/$1"
reserve=$2
shift 2
[ -d "$clone" ] || {
  echo "rac remote: no clone at $clone; run push first" >&2
  exit 1
}
cd "$clone"
# A tree built under another Xcode or SDK recompiles all of Chromium, so
# the Pro's toolchain must still match the record the clone inherited.
check_toolchain_record "$clone"
cores=$(sysctl -n hw.ncpu)
jobs=$(( cores > reserve ? cores - reserve : 1 ))
src=$clone/build/src
xcode=$(xcode_dir) || exit 1
targets=("$@")
[ $# -gt 0 ] || targets=(chrome chromedriver)
# The build is helium_build's autoninja call, capped at cores-reserve
# local jobs (autoninja passes -local_jobs through to siso ninja) so the
# Pro stays usable for the maintainer while it compiles. The queue's step
# cap stops a build that turned out to be a full one.
exec nice -n 10 taskpolicy -c utility devutils/rac/build-queue.sh \
  bash -c 'cd "$1" && shift && exec "$@"' rac-build "$src" \
  env "SISO_PATH=$src/third_party/siso/cipd/siso" "DEVELOPER_DIR=$xcode" \
  python3 third_party/depot_tools/autoninja.py -C out/Default \
  "${targets[@]}" "-local_jobs=$jobs" -k 0
EOS
}

# Browser args after `--` are a fixed allowlist, not a denylist: a
# denylist always misses a switch (Chromium takes `-s` as well as `--s`,
# and the last copy of a switch wins), so only the spellings below pass
# and every other argument starting with `-` is refused. Paths are
# compared without case, as APFS does. The tool's own switches never go
# through here: the Pro's launch adds the clone's --user-data-dir itself,
# and --rac-window-screenshot-requests for a requests run.
check_run_arg() {
  local arg=$1 lower value
  lower=$(printf '%s' "$arg" | tr '[:upper:]' '[:lower:]')
  case "$lower" in
    *"application support"* | *me.kainoa.rac* | *net.imput.helium*)
      refuse "run args may not touch a real profile folder ($arg)" ;;
  esac
  case "$arg" in
    --no-first-run | --rac-launch-in-background | --rac-import-arc-now | \
      --force-prefers-reduced-motion | --rac-force-increased-contrast | \
      --disable-backgrounding-occluded-windows)
      return 0 ;;
    --rac-window-screenshot=?* | --rac-arc-import-fixture=?* | \
      --rac-import-source-root=?* | --log-net-log=?* | --rac-frame-log=?*)
      value=${arg#*=} ;;
    --rac-window-screenshot | --rac-window-screenshot=)
      refuse "give the screenshot file as --rac-window-screenshot=<name>.png" ;;
    --log-net-log | --log-net-log=)
      refuse "give the net log as --log-net-log=<name>.json" ;;
    --rac-frame-log | --rac-frame-log=)
      refuse "give the frame log as --rac-frame-log=<name>.log" ;;
    --rac-arc-import-fixture= | --rac-import-source-root=)
      refuse "${arg%%=*} needs a path in the clone" ;;
    --rac-window-screenshot-delay=*)
      value=${arg#*=}
      case "$value" in
        '' | *[!0-9]* | ?????*)
          refuse "--rac-window-screenshot-delay takes 1-4 digits, not '$value'" ;;
      esac
      return 0 ;;
    --net-log-capture-mode=*)
      case "${arg#*=}" in
        Default | IncludeSensitive | Everything) return 0 ;;
      esac
      refuse "--net-log-capture-mode takes Default, IncludeSensitive or Everything, not '${arg#*=}'" ;;
    --enable-logging=*)
      [ "$arg" = --enable-logging=stderr ] \
        || refuse "--enable-logging only takes stderr, not '${arg#*=}'"
      return 0 ;;
    --vmodule=*)
      value=${arg#*=}
      case "$value" in
        '' | *[!A-Za-z0-9_=,\*/-]*)
          refuse "--vmodule takes a spec of letters, digits and _=,*/-, not '$value'" ;;
      esac
      [ "${#value}" -le 200 ] \
        || refuse "--vmodule takes at most 200 characters"
      return 0 ;;
    --rac-force-color-mode=*)
      case "${arg#*=}" in
        light | dark | system) return 0 ;;
      esac
      refuse "--rac-force-color-mode takes light, dark or system, not '${arg#*=}'" ;;
    -*)
      refuse "'$arg' is not an allowed run arg; ask Ship to allow it" ;;
    *)
      # A bare argument is a URL Chromium opens: the same allowlist the
      # requests file's open-urls gets, including chrome://setup, which
      # the run then has to pair with an Arc import input.
      python3 "$here/remote_requests.py" --url "$arg" || exit 2
      return 0 ;;
  esac
  # Path values resolve in the clone, where the browser runs.
  case "$value" in
    /* | '~'*)
      refuse "run args can't name absolute paths ($arg); relative ones land in the clone" ;;
    .. | ../* | */../* | */..)
      refuse "run args can't leave the clone ($arg)" ;;
    *[!A-Za-z0-9._/-]*)
      refuse "run arg paths may only use letters, digits, '.', '_', '-' and '/' ($arg)" ;;
  esac
  case "$arg" in
    --rac-window-screenshot=*.png) ;;
    --rac-window-screenshot=*)
      refuse "a screenshot path ends in .png ($arg)" ;;
    --log-net-log=*.json) ;;
    --log-net-log=*)
      refuse "a net log path ends in .json ($arg)" ;;
    --rac-frame-log=*.log) ;;
    --rac-frame-log=*)
      refuse "a frame log path ends in .log ($arg)" ;;
  esac
}

cmd_run() {
  local name=$1 timeout=90 requests='' outputs='' fresh=0 checked
  local req_pages='' req_verbs='' import_input=0 setup_page=0 source_root=0
  local arc_now=0 settings_page=0
  shift
  while [ $# -gt 0 ]; do
    case "$1" in
      --requests-file)
        [ $# -ge 2 ] || die "run: --requests-file needs a file on this Mac"
        # The checked line, then `verbs VERB...`, a `pages URL` per
        # internal page open-urls visits, and one `file REL` / `dir REL`
        # / `expect REL` per path in it. The pages are read back here for
        # the setup check and stripped from the stream the Pro gets.
        checked=$(python3 "$here/remote_requests.py" "$2") || exit 2
        requests=${checked%%$'\n'*}
        outputs=
        case "$checked" in *$'\n'*) outputs=${checked#*$'\n'} ;; esac
        req_pages=$(printf '%s\n' "$outputs" | awk '$1 == "pages" { print $2 }')
        req_verbs=$(printf '%s\n' "$outputs" | awk '$1 == "verbs" { $1=""; print }')
        outputs=$(printf '%s\n' "$outputs" | awk '$1 != "pages"')
        shift 2 ;;
      --fresh-profile) fresh=1; shift ;;
      --timeout)
        [ $# -ge 2 ] || die "run: --timeout needs seconds"
        case "$2" in '' | *[!0-9]*) die "run: --timeout needs seconds" ;; esac
        timeout=$2
        shift 2 ;;
      --) shift; break ;;
      *) die "usage: remote-build.sh run <worktree> [--timeout S] [--requests-file F] [--fresh-profile] [-- args...]" ;;
    esac
  done
  case "$queue_wait" in
    '' | *[!0-9]*) die "RAC_REMOTE_QUEUE_WAIT must be whole seconds, not '$queue_wait'" ;;
  esac
  local arg lower
  for arg in "$@"; do
    check_run_arg "$arg"
    case "$arg" in
      --rac-arc-import-fixture=*) import_input=1 ;;
      --rac-import-source-root=*) import_input=1; source_root=1 ;;
      --rac-import-arc-now) arc_now=1 ;;
    esac
    lower=$(printf '%s' "$arg" | tr '[:upper:]' '[:lower:]')
    case "$lower" in
      chrome://setup | chrome://setup/* | rac://setup | rac://setup/*)
        setup_page=1 ;;
      chrome://settings | chrome://settings/* | rac://settings | rac://settings/*)
        settings_page=1 ;;
    esac
  done
  for arg in $req_pages; do
    lower=$(printf '%s' "$arg" | tr '[:upper:]' '[:lower:]')
    case "$lower" in
      chrome://setup | chrome://setup/* | rac://setup | rac://setup/*)
        setup_page=1 ;;
      chrome://settings | chrome://settings/* | rac://settings | rac://settings/*)
        settings_page=1 ;;
    esac
  done
  # chrome://setup is the Arc import screen: without an import input in
  # the same run it would read the maintainer's real Arc data.
  if [ "$setup_page" = 1 ] && [ "$import_input" = 0 ]; then
    refuse "opening chrome://setup needs --rac-arc-import-fixture= or --rac-import-source-root= in the same run, so the import screen reads a fixture, not the Pro's real Arc data"
  fi
  # --rac-import-arc-now imports at startup from --rac-import-source-root,
  # and from the maintainer's real Arc when that switch is missing.
  if [ "$arc_now" = 1 ] && [ "$source_root" = 0 ]; then
    refuse "--rac-import-arc-now needs --rac-import-source-root= in the same run, or it imports the Pro's real Arc data"
  fi
  # A run that opens a settings page may only take screenshots. A script
  # that opens settings itself was refused by the checker if it carries
  # input; a settings page passed as a run arg is checked against the
  # requests file's verbs here.
  if [ "$settings_page" = 1 ]; then
    for arg in $req_verbs; do
      case "$arg" in
        click | command | key | move | nspress | nsflags | nskey | nstype | \
        pointer | pointer-path | swipe | type | wheel)
          refuse "a run that opens a settings page may only take screenshots; the requests file may not send input" ;;
      esac
    done
  fi
  remote "$name" "$timeout" "$queue_wait" "$requests" "$outputs" "$fresh" "$@" <<'EOS'
set -e
safe_name "$1" || { echo "rac remote: bad clone name '$1'" >&2; exit 2; }
clone="$HOME/rac-remote/wt/$1"
timeout=$2
queue_wait=$3
requests=$4
outputs=$5
fresh=$6
shift 6
[ -d "$clone" ] || {
  echo "rac remote: no clone at $clone; run push first" >&2
  exit 1
}
clone=$(cd "$clone" && pwd -P)
cd "$clone"
# The clone's next build needs the toolchain record it inherited; catch a
# drifted Pro here rather than mid-work.
check_toolchain_record "$clone"
# Screenshots land in build/shots; the Air checked they are relative names
# that stay inside it.
shot=
args=()
# The files a requests run waits for; the first shot alone ends a plain run.
expected=()
# Log files the browser is asked to write, mapped under build/logs.
logfiles=()
for arg in "$@"; do
  case "$arg" in
    --rac-window-screenshot=*)
      shot="$clone/build/shots/${arg#--rac-window-screenshot=}"
      arg="--rac-window-screenshot=$shot" ;;
    # Logs land in build/logs under the same checks screenshots get in
    # build/shots: never inside build/profile.
    --log-net-log=* | --rac-frame-log=*)
      log="$clone/build/logs/${arg#*=}"
      arg="${arg%%=*}=$log"
      logfiles+=("$log") ;;
    # Inputs rac reads Arc data from, which need absolute paths: relative
    # to the clone, existing, and still inside it once symlinks resolve.
    # Nothing is created for them.
    --rac-arc-import-fixture=* | --rac-import-source-root=*)
      input=${arg#*=}
      [ -n "$input" ] || { echo "rac remote: refusing: ${arg%%=*} needs a path in the clone" >&2; exit 2; }
      input="$clone/$input"
      [ -e "$input" ] || { echo "rac remote: refusing: ${arg%%=*}: no $input" >&2; exit 2; }
      inside_clone "$clone" "$input" || { echo "rac remote: refusing: ${arg%%=*} leaves the clone ($input)" >&2; exit 2; }
      arg="${arg%%=*}=$input" ;;
  esac
  args+=("$arg")
done
if [ -n "$shot" ]; then
  # A symlinked build/shots would write the PNG anywhere on the Pro, and a
  # symlink anywhere on the way escapes just the same; the real path has
  # to stay inside the clone.
  [ ! -L "$clone/build/shots" ] || {
    echo "rac remote: refusing: $clone/build/shots is a symlink" >&2
    exit 2
  }
  # Check before creating anything: a symlinked build/ (or any folder on
  # the way) would otherwise let mkdir make folders outside the clone.
  inside_clone "$clone" "$shot" || {
    echo "rac remote: refusing: $shot leaves the clone through a symlink" >&2
    exit 2
  }
  mkdir -p "$(dirname "$shot")"
  inside_clone "$clone" "$shot" || {
    echo "rac remote: refusing: $shot leaves the clone through a symlink" >&2
    exit 2
  }
  # A shot left by an earlier run would end the wait at once.
  rm -f "$shot"
fi
if [ "${#logfiles[@]}" -gt 0 ]; then
  # The same checks screenshots get: a symlinked build/logs, or a symlink
  # anywhere on the way, would write the log outside the clone -- and
  # build/logs can never be build/profile.
  [ ! -L "$clone/build/logs" ] || {
    echo "rac remote: refusing: $clone/build/logs is a symlink" >&2
    exit 2
  }
  for log in ${logfiles[@]+"${logfiles[@]}"}; do
    inside_clone "$clone" "$log" || {
      echo "rac remote: refusing: $log leaves the clone through a symlink" >&2
      exit 2
    }
    mkdir -p "$(dirname "$log")"
    inside_clone "$clone" "$log" || {
      echo "rac remote: refusing: $log leaves the clone through a symlink" >&2
      exit 2
    }
    # A stale log isn't this run's output.
    rm -f "$log"
  done
fi
# Every process running from the clone's app, never anything else.
app="$clone/build/src/out/Default/rac.app/"
clone_pids() {
  ps -axo pid=,command= | P="$app" awk '{ pid = $1; sub(/^ *[0-9]+ +/, ""); if (index($0, ENVIRON["P"]) == 1) print pid }'
}
if [ -n "$requests" ]; then
  # A browser already running from this clone polls the same req.txt and
  # would take this line, under whatever profile settings it started with.
  [ -z "$(clone_pids)" ] || {
    echo "rac remote: refusing requests: a browser from this clone is running" >&2
    exit 2
  }
  # The Air checked the line and listed every path in it, each relative to
  # build/shots and marked @SHOTS@ in the line. The harness splits on
  # spaces, so the clone's own path has to be one plain word.
  case "$clone" in
    *[!A-Za-z0-9._/-]*)
      echo "rac remote: refusing: requests need a clone path without spaces or symbols ($clone)" >&2
      exit 2 ;;
  esac
  shots="$clone/build/shots"
  for dir in "$shots" "$clone/build/req"; do
    [ ! -L "$dir" ] || { echo "rac remote: refusing: $dir is a symlink" >&2; exit 2; }
    inside_clone "$clone" "$dir" || { echo "rac remote: refusing: $dir leaves the clone" >&2; exit 2; }
    mkdir -p "$dir"
  done
  # Each destination stays in the clone before and after its folder is
  # made. Read from the list, never by splitting the line: typed text in
  # it would glob. `expect` files are the screenshots the run waits for.
  verbs=
  while read -r kind rel; do
    [ -n "$kind" ] || continue
    # The checker lists the line's verbs for the harness check below.
    if [ "$kind" = verbs ]; then
      verbs=$rel
      continue
    fi
    case "$rel" in
      '' | /* | *[!A-Za-z0-9._/-]* | . | .. | ./* | ../* | */. | */.. | */./* | */../* | *//*)
        echo "rac remote: refusing: bad requests path '$rel'" >&2
        exit 2 ;;
    esac
    word="$shots/$rel"
    inside_clone "$clone" "$word" || { echo "rac remote: refusing: $word leaves the clone" >&2; exit 2; }
    case "$kind" in
      dir) mkdir -p "$word" ;;
      file | expect) mkdir -p "$(dirname "$word")" ;;
      *) echo "rac remote: refusing: bad requests output '$kind'" >&2; exit 2 ;;
    esac
    inside_clone "$clone" "$word" || { echo "rac remote: refusing: $word leaves the clone" >&2; exit 2; }
    # A shot left by an earlier run would look like this run's.
    case "$kind/$word" in file/*.png | expect/*) rm -f "$word" ;; esac
    [ "$kind" != expect ] || expected+=("$word")
  done <<<"$outputs"
  # Every verb the Air's checker saw must be a string literal in this
  # clone's own harness sources: a verb the clone never built would run
  # as an output path inside `after`.
  harness=$clone/build/src/chrome/browser/ui/views/rac
  for verb in $verbs; do
    case "$verb" in
      '' | *[!A-Za-z-]*)
        echo "rac remote: refusing: bad verb '$verb'" >&2
        exit 2 ;;
    esac
    if ! grep -F -q "\"$verb\"" "$harness/window_screenshot.mm" \
         "$harness"/dev/*.mm "$harness"/dev/*.cc 2>/dev/null; then
      echo "rac remote: refusing: the clone's harness has no \"$verb\" request" >&2
      exit 2
    fi
  done
  requests=${requests//@SHOTS@/$shots}
  # Write beside the file and rename, so the polling harness never reads
  # half a line; remove both names first so neither can be a symlink the
  # write or the rename would follow.
  req="$clone/build/req/req.txt"
  rm -f "$req.tmp" "$req"
  (set -C; printf '%s\n' "$requests" > "$req.tmp")
  mv -f "$req.tmp" "$req"
  args+=("--rac-window-screenshot-requests=$req")
  [ -z "$shot" ] || expected+=("$shot")
fi
# $launcher plus every descendant: the queue starts the browser in a new
# session, so only a parent-pid walk finds its whole tree.
family_pids() {
  ps -axo pid=,ppid= | ROOT="$launcher" awk '
    { kids[$2] = kids[$2] " " $1 }
    END {
      root = ENVIRON["ROOT"]; seen[root] = 1; out = root
      n = split(kids[root], q, " ")
      for (i = 1; i <= n; i++) {
        p = q[i]
        if (p == "" || (p in seen)) continue
        seen[p] = 1; out = out " " p
        m = split(kids[p], k, " ")
        for (j = 1; j <= m; j++) q[++n] = k[j]
      }
      printf "%s", out
    }'
}
# Clone-app pids this launch started; a browser from another run of the
# same clone isn't in this family and is left alone.
our_pids() {
  local fam p
  fam=" $(family_pids) "
  for p in $(clone_pids); do
    case "$fam" in *" $p "*) printf ' %s' "$p" ;; esac
  done
}
stop_own() {
  local i p left
  for i in 1 2 3 4 5 6 7 8 9 10; do
    left=
    for p in $spawned $browser_pids; do
      kill -0 "$p" 2>/dev/null || continue
      left="$left $p"
    done
    [ -n "$left" ] || return 0
    kill $left 2>/dev/null || true
    # The browser leads its own session; killing its group reaches helper
    # processes even after it has been reparented.
    for p in $browser_pids; do kill -- "-$p" 2>/dev/null || true; done
    sleep 1
  done
  for p in $left; do
    kill -9 "$p" 2>/dev/null || true
    kill -9 -- "-$p" 2>/dev/null || true
  done
}
if [ "$fresh" = 1 ]; then
  # Only the clone's own throwaway profile, the --user-data-dir the launch
  # below gives it, and never one a running browser holds.
  [ -n "$clone" ] && [ "$clone" != / ] || { echo "rac remote: refusing: no clone path" >&2; exit 2; }
  profile="$clone/build/profile"
  for dir in "$clone/build" "$profile"; do
    [ ! -L "$dir" ] || { echo "rac remote: refusing --fresh-profile: $dir is a symlink" >&2; exit 2; }
  done
  inside_clone "$clone" "$profile" || { echo "rac remote: refusing --fresh-profile: $profile leaves the clone" >&2; exit 2; }
  [ -z "$(clone_pids)" ] || {
    echo "rac remote: refusing --fresh-profile: a browser from this clone is running" >&2
    exit 2
  }
  rm -rf -- "$profile"
  echo "rac remote: deleted $profile" >&2
fi
# Downloads land only in the clone: a URL the harness opens can start
# one, and the default folder is the Pro's own Downloads. Before every
# launch, point the clone profile's downloads and saves at build/downloads
# and turn file dialogs off (Local State's select_file_dialogs.allowed,
# the AllowFileSelectionDialogs policy's pref), so no open, save or upload
# dialog can be steered to the Pro's own files. A browser already running
# from this clone (another run's, which did the same; a requests run
# refused above) read its prefs at startup and rewrites them on exit.
profile=$clone/build/profile
downloads=$clone/build/downloads
if [ -n "$(clone_pids)" ]; then
  echo "rac remote: a browser from this clone is running; its profile already points downloads inside the clone" >&2
else
  for path in "$clone/build" "$profile" "$profile/Default" "$downloads" \
              "$profile/Default/Preferences" "$profile/Local State"; do
    [ ! -L "$path" ] || { echo "rac remote: refusing: $path is a symlink" >&2; exit 2; }
    inside_clone "$clone" "$path" || { echo "rac remote: refusing: $path leaves the clone" >&2; exit 2; }
  done
  mkdir -p "$profile/Default" "$downloads"
  # Keep every other preference; a missing or unreadable file starts
  # empty. Write a new file beside each (never through a planted link)
  # and rename it over, so the browser never reads half a file.
  python3 - "$profile" "$downloads" <<'PY'
import json, os, sys
profile, downloads = sys.argv[1:3]

def patch(path, values):
    try:
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
        if not isinstance(data, dict):
            data = {}
    except (OSError, ValueError):
        data = {}
    for dotted, value in values.items():
        section, key = dotted.split('.')
        if not isinstance(data.get(section), dict):
            data[section] = {}
        data[section][key] = value
    tmp = path + '.tmp'
    try:
        os.unlink(tmp)
    except FileNotFoundError:
        pass
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        json.dump(data, f)
    os.replace(tmp, path)

patch(os.path.join(profile, 'Default', 'Preferences'), {
    'download.default_directory': downloads,
    'download.prompt_for_download': False,
    'download.directory_upgrade': True,
    'savefile.default_directory': downloads,
    'selectfile.last_directory': downloads,
})
patch(os.path.join(profile, 'Local State'), {
    'select_file_dialogs.allowed': False,
})
PY
fi
launcher=
browser_pids=
spawned=
cleanup() {
  if [ -n "$launcher" ]; then
    kill "$launcher" 2>/dev/null || true
    wait "$launcher" 2>/dev/null || true
    launcher=
  fi
  stop_own
}
trap 'cleanup; exit 130' INT TERM HUP
# The clone's own worktree.sh run would add --enable-ui-devtools: a
# full-UI-control WebSocket a mistake in a request could drive the whole
# browser with. Launch the built binary directly instead, with exactly
# worktree.sh's own flags minus that one. The queue gets --run: nothing
# in this command still says "worktree.sh run".
app_bin="$clone/build/src/out/Default/rac.app/Contents/MacOS/rac"
[ -x "$app_bin" ] || {
  echo "rac remote: no built browser at $app_bin; run build first" >&2
  exit 1
}
# setsid gives the launcher its own session, so a signal that hits this
# script's process group can't take the tree down before the trap can
# choose what to stop.
python3 -c 'import os,sys; os.setsid(); os.execvp(sys.argv[1], sys.argv[1:])' \
  env BREAKPAD_DUMP_LOCATION="$clone/build/profile/Crashpad" \
  nice -n 10 taskpolicy -c utility devutils/rac/build-queue.sh --run \
  "$app_bin" --user-data-dir="$clone/build/profile" --use-mock-keychain \
  --disable-features=DialMediaRouteProvider --rac-launch-in-background \
  ${args[@]+"${args[@]}"} &
launcher=$!
spawned=$launcher
end=
deadline=$((SECONDS + queue_wait + timeout))
last=-1
settled_at=0
# The expected files not yet written, one per line.
missing_outputs() {
  local f
  for f in ${expected[@]+"${expected[@]}"}; do
    [ -s "$f" ] || printf '%s\n' "$f"
  done
}
while [ "$SECONDS" -lt "$deadline" ]; do
  fam=$(family_pids)
  [ -n "$fam" ] && spawned=$fam
  ours=$(our_pids)
  [ -n "$ours" ] && browser_pids="$browser_pids$ours"
  if [ -z "$end" ]; then
    # The browser's clock starts once the queue grants it a slot and it
    # actually runs, not while it waits in line.
    if [ -n "$ours" ] || { [ -n "$shot" ] && [ -f "$shot" ]; }; then
      end=$((SECONDS + timeout))
    fi
  elif [ "$SECONDS" -ge "$end" ]; then
    break
  elif [ -n "$requests" ]; then
    # The harness only reads requests after the first shot, so a requests
    # run ends when every file it expects is there and none has changed
    # size for 2s. With none expected, it runs to the timeout.
    if [ "${#expected[@]}" -gt 0 ] && [ -z "$(missing_outputs)" ]; then
      sizes=$(stat -f %z "${expected[@]}" 2>/dev/null | tr '\n' ' ' || true)
      if [ "$sizes" != "$last" ]; then
        last=$sizes
        settled_at=$SECONDS
      elif [ $((SECONDS - settled_at)) -ge 2 ]; then
        break
      fi
    fi
  elif [ -n "$shot" ] && [ -f "$shot" ]; then
    size=$(stat -f %z "$shot" 2>/dev/null || echo 0)
    # Settled: a real file whose size stopped changing between checks.
    if [ "$size" -gt 0 ] && [ "$size" = "$last" ]; then break; fi
    last=$size
  fi
  sleep 1
  kill -0 "$launcher" 2>/dev/null || break
done
launched=${end:+yes}
killed=0
if kill -0 "$launcher" 2>/dev/null; then
  killed=1
  kill "$launcher" 2>/dev/null || true
fi
status=0
wait "$launcher" 2>/dev/null || status=$?
launcher=
stop_own
if [ -z "$launched" ]; then
  echo "rac remote: the browser never launched (no clone process seen" >&2
  echo "within a ${queue_wait}s queue wait plus ${timeout}s timeout)" >&2
  exit 1
fi
[ "$killed" = 0 ] || status=0
missing=$(missing_outputs)
if [ -n "$requests" ] && [ -n "$missing" ]; then
  echo "rac remote: after ${timeout}s, still no:" >&2
  printf '%s\n' "$missing" | sed 's/^/  /' >&2
  exit 1
fi
if [ -n "$shot" ]; then
  if [ -s "$shot" ]; then
    echo "rac remote: screenshot: $shot" >&2
  else
    echo "rac remote: no screenshot at $shot after ${timeout}s" >&2
    exit 1
  fi
fi
exit "$status"
EOS
}

cmd_pull() {
  local name=$1 rel=$2 dest=$3
  case "$rel" in
    *"Application Support"*) refuse "pull may not touch a real profile folder" ;;
    '' | . | ./) refuse "pull takes one file or folder inside the clone, not the whole clone" ;;
    /*) refuse "pull takes a path relative to the clone, not $rel" ;;
    .. | ../* | */../* | */..) refuse "pull paths stay inside the clone, not $rel" ;;
    # The path goes through the remote rsync's argument parsing.
    *[!A-Za-z0-9._/-]*) refuse "pull paths need letters, digits, '.', '_', '-', or '/', not $rel" ;;
  esac
  case "$dest" in
    *"Application Support"*) refuse "pull may not touch a real profile folder" ;;
    '') die "pull needs a local path" ;;
    /*) ;;
    # rsync reads `a:b` as a remote path; ./ keeps it local.
    *) dest=./$dest ;;
  esac
  # Lexical checks can't see a symlink inside the clone; the remote side
  # resolves the source for real before anything is copied.
  remote "$name" "$rel" <<'EOS'
set -e
safe_name "$1" || { echo "rac remote: bad clone name '$1'" >&2; exit 2; }
clone="$HOME/rac-remote/wt/$1"
[ -d "$clone" ] || {
  echo "rac remote: no clone at $clone; run push first" >&2
  exit 1
}
inside_clone "$clone" "$clone/$2" || {
  echo "rac remote: refusing: $2 leaves the clone through a symlink" >&2
  exit 2
}
EOS
  # Pro to Air: the clone is only read.
  xrsync "$host:$rdir/wt/$name/$rel" "$dest"
}

cmd_status() {
  remote <<'EOS'
uptime
echo "free disk under $HOME: $(df -g "$HOME" | awk 'NR==2 {print $4}') GB"
if [ -d "$HOME/rac-remote/base" ]; then
  cd "$HOME/rac-remote/base"
  devutils/rac/build-queue.sh status
else
  echo "rac remote: no base checkout yet; run build-base first"
fi
EOS
}

if [ "${1:-}" = "--dry-run" ]; then
  dry=1
  shift
fi
case "${1:-}" in
  help | --help | -h)
    usage ;;
  setup-host)
    [ $# = 1 ] || die "usage: remote-build.sh setup-host"
    cmd_setup_host ;;
  build-base)
    shift
    resume=0 approved='' ref=''
    while [ $# -gt 0 ]; do
      case "$1" in
        --approved)
          [ $# -ge 2 ] || die "build-base: --approved needs \"<who/when>\""
          approved=$2
          shift 2 ;;
        --resume) resume=1; shift ;;
        --)
          shift
          [ $# -le 1 ] || die "build-base takes one ref"
          if [ $# = 1 ]; then
            [ -z "$ref" ] || die "build-base takes one ref, not also '$1'"
            ref=$1
            shift
          fi ;;
        -*)
          die "usage: remote-build.sh build-base [--resume] [--approved \"<who/when>\"] <ref>" ;;
        *)
          [ -z "$ref" ] || die "build-base takes one ref, not also '$1'"
          ref=$1
          shift ;;
      esac
    done
    # The queue rejects a blank approval note, but only once the detached
    # build runs; catch it here.
    if [ -n "$approved" ] && [ -z "$(printf '%s' "$approved" | tr -d '[:space:]')" ]; then
      die "build-base: --approved needs a note saying who approved it and when"
    fi
    if [ "$resume" = 0 ] && [ -z "$ref" ]; then
      die "usage: remote-build.sh build-base [--approved \"<who/when>\"] <ref>"
    fi
    if [ -n "$ref" ]; then
      case "$ref" in
        *..* | *[!A-Za-z0-9._/-]* | -* | /* | */)
          die "build-base takes a tag or branch name, not '$ref'" ;;
      esac
    fi
    if [ "$resume" = 1 ] && [ -z "$approved" ]; then
      die "build-base --resume needs --approved \"<who/when>\""
    fi
    cmd_build_base "$ref" "$resume" "$approved" ;;
  seed-base)
    die "seed-base was replaced by build-base; the Pro builds its own base from GitHub: remote-build.sh build-base <ref> --approved \"<who/when>\"" ;;
  push)
    [ $# = 2 ] || die "usage: remote-build.sh push <worktree>"
    name=$(clone_name "$2")
    cmd_push "$2" "$name" ;;
  build)
    [ $# -ge 2 ] || die "usage: remote-build.sh build <worktree> [-- targets...]"
    name=$(clone_name "$2")
    shift 2
    cmd_build "$name" "$@" ;;
  run)
    [ $# -ge 2 ] || die "usage: remote-build.sh run <worktree> [--timeout S] [--requests-file F] [--fresh-profile] [-- args...]"
    name=$(clone_name "$2")
    shift 2
    cmd_run "$name" "$@" ;;
  pull)
    [ $# = 4 ] || die "usage: remote-build.sh pull <worktree> <remote path> <local path>"
    name=$(clone_name "$2")
    cmd_pull "$name" "$3" "$4" ;;
  log)
    case $# in
      1) cmd_log 40 ;;
      2)
        case "$2" in
          '' | *[!0-9]*) die "log takes a line count, not '$2'" ;;
        esac
        cmd_log "$2" ;;
      *) die "usage: remote-build.sh log [lines]" ;;
    esac ;;
  status)
    [ $# = 1 ] || die "usage: remote-build.sh status"
    cmd_status ;;
  *) die "usage: remote-build.sh [--dry-run] <setup-host|build-base|push|build|run|pull|log|status>" ;;
esac
