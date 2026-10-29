#!/usr/bin/env bash
# Feature trees: git worktrees that each get a copy-on-write clone of the main
# checkout's built Chromium tree. See docs/operations/worktrees.md.
#
# usage: devutils/rac/worktree.sh <setup [<checkout>]|sync [--discard]|run|cleanup>
#   run every command from the root of the worktree
#   setup clones the main checkout's build tree, or the given checkout's
#   sync --discard throws away edits that aren't saved in a patch
set -euo pipefail

die() { echo "rac worktree: $*" >&2; exit 1; }
log() { echo "rac worktree: $*" >&2; }

# Worktree setup scripts may run with a minimal PATH.
case ":$PATH:" in
  *:/opt/homebrew/bin:*) ;;
  *) [ ! -d /opt/homebrew/bin ] || PATH="/opt/homebrew/bin:$PATH" ;;
esac
for tool in git python3 quilt greadlink; do
  command -v "$tool" >/dev/null || die "$tool not found; install it with Homebrew"
done

root=$(cd "$(git rev-parse --show-toplevel)" && pwd -P)
base=${REPO_ROOT_PATH:-$(git -C "$root" worktree list --porcelain | sed -n '1s/^worktree //p')}
base=$(cd "$base" && pwd -P)
src="$root/build/src"
out="$src/out/Default"
record="$src/.pc/.rac_applied"
trash="$base/build/.trash"

quilt_() {
  (cd "$src" && QUILT_PATCHES="$root/patches" QUILT_SERIES=series.merged \
    QUILT_PATCH_OPTS="--unified --reject-format=unified" \
    quilt --quiltrc - "$@")
}

# Prints PIDs of processes whose command line contains $1.
pids_matching() {
  # The pattern goes through the environment so awk's own command line
  # doesn't match it.
  ps -axo pid=,command= | P="$1" SELF="$$" awk 'index($0, ENVIRON["P"]) && $1 != ENVIRON["SELF"] { print $1 }'
}

# Setup and sync --discard set this: sync then throws away edits that aren't
# saved in a patch, including edits to string files. A fresh clone holds no
# work of its own, so setup may drop whatever its source left unsaved.
force=0

dev_names() {
  local args=("$1")
  [ "$1" != unsub ] || [ "$force" = 0 ] || args+=(--force)
  python3 "$root/devutils/rac/dev_names.py" "${args[@]}" -t "$src" >&2 \
    || die "dev_names.py $1 failed"
}

clone_tree() {
  python3 - "$1" "$2" <<'EOF'
import ctypes, os, sys
libc = ctypes.CDLL("/usr/lib/libSystem.B.dylib", use_errno=True)
CLONE_NOFOLLOW = 1
if libc.clonefile(sys.argv[1].encode(), sys.argv[2].encode(), CLONE_NOFOLLOW) != 0:
    sys.exit("clonefile failed: " + os.strerror(ctypes.get_errno()))
EOF
}

# gn and siso run xcodebuild, which fails ("xcodebuild requires Xcode") when
# xcode-select points at the Command Line Tools. Prints the developer dir to
# give them: DEVELOPER_DIR or xcode-select's if that's an Xcode, otherwise
# the first Xcode in $1 (default /Applications). Like xcrun, it takes an
# Xcode's .app path as well as its Contents/Developer.
xcode_dir() {
  local dir
  for dir in "${DEVELOPER_DIR:-}" "$(xcode-select -p 2>/dev/null || true)"; do
    case "$dir" in *.app | *.app/) dir="${dir%/}/Contents/Developer" ;; esac
    if [ -n "$dir" ] && [ -x "$dir/usr/bin/xcodebuild" ]; then
      echo "$dir"
      return 0
    fi
  done
  for dir in "${1:-/Applications}"/Xcode.app "${1:-/Applications}"/Xcode*.app; do
    if [ -x "$dir/Contents/Developer/usr/bin/xcodebuild" ]; then
      log "using $dir for gn and siso, since xcode-select doesn't point at Xcode"
      echo "$dir/Contents/Developer"
      return 0
    fi
  done
  die "gn needs Xcode, and none was found; install Xcode or set DEVELOPER_DIR"
}

# Patch bookkeeping for sync; see worktree_state.py for the commands.
stack() {
  python3 "$root/devutils/rac/worktree_state.py" "$src" "$root/patches" "$@"
}

# Makes the applied quilt stack match this tree's patches, popping only the
# patches that changed (and everything above them) so the rebuild stays small.
cmd_sync() {
  [ -d "$src/.pc" ] || die "no build tree at $src"
  [ -f "$root/patches/series.merged" ] || die "patches are not merged; run: source dev.sh && he merge"
  [ -f "$record" ] || stack record || die "couldn't record the applied patches"

  local keep applied wanted plan
  plan=$(stack compare) || die "couldn't compare the applied patches with the series"
  read -r keep applied wanted <<< "$plan"

  # quilt can't pop or push patches on string files that the name passes
  # changed (pop -f would even restore stale copies), so revert the names
  # first. The end of sync applies them again. unsub refuses if a string file
  # changed since the names were applied.
  if [ "$keep" -lt "$applied" ] || [ "$applied" -lt "$wanted" ]; then
    dev_names unsub
  fi

  # Popping with -f throws away edits that haven't been saved into a patch.
  # The check compares each popped patch's files with the version that was
  # applied and with the current patch file (which matches after a refresh).
  if [ "$keep" -lt "$applied" ] && [ "$force" = 0 ]; then
    stack check "$keep" \
      || die "sync stopped before changing any patch; rac's names stay reverted until it finishes"
  fi

  if [ "$keep" -lt "$applied" ]; then
    log "popping $((applied - keep)) changed or removed patches"
    local target=-a
    [ "$keep" -eq 0 ] || target=$(sed -n "${keep}p" "$src/.pc/applied-patches")
    quilt_ pop -f -q "$target" >/dev/null || die "quilt pop failed; see the error above"
  fi

  local status=0 push_log
  push_log=$(quilt_ push -a -q 2>&1) || status=$?
  # quilt exits 2 when there is nothing left to push.
  if { [ "$status" -ne 0 ] && [ "$status" -ne 2 ]; } || ! stack matches; then
    printf '%s\n' "$push_log" >&2
    die "quilt push failed; fix the patch or series, then rerun sync"
  fi

  stack record
  dev_names sub
  python3 "$root/devutils/rac/rac_version.py" -t "$src" || die "rac_version.py failed"
  log "patch stack is in sync ($(wc -l < "$src/.pc/applied-patches" | tr -d ' ') applied)"
}

cmd_setup() {
  local from=$base
  [ -z "${1:-}" ] || from=$(cd "$1" && pwd -P) || die "no checkout at $1"
  local from_src="$from/build/src"
  [ "$root" != "$base" ] || die "run setup in a worktree, not in the main checkout"
  [ "$root" != "$from" ] || die "a worktree can't clone its own build tree"
  [ -f "$from_src/out/Default/.siso_fs_state" ] || die "$from has no finished build at $from_src"
  [ ! -e "$src" ] || die "$src already exists"
  if [ -n "$(pids_matching "$from_src/third_party/siso")" ]; then
    die "a build is running in $from; wait for it to finish"
  fi

  if [ ! -e "$root/helium-chromium/.git" ]; then
    # Take the submodule from the checkout being cloned: it has the Helium
    # commit this branch needs, which the main checkout may not (a newer base).
    # An uninitialized submodule folder would resolve to rac's own git dir, so
    # use it only if it is a checkout of its own.
    local modules="$base/.git/modules/helium-chromium"
    if [ "$(git -C "$from/helium-chromium" rev-parse --show-toplevel 2>/dev/null)" = "$from/helium-chromium" ]; then
      modules=$(git -C "$from/helium-chromium" rev-parse --absolute-git-dir)
    fi
    log "checking out helium-chromium from $modules"
    git -C "$root" -c protocol.file.allow=always \
      -c "submodule.helium-chromium.url=$modules" \
      submodule update --init --quiet helium-chromium
  fi

  if [ ! -f "$root/patches/series.merged" ]; then
    local merge_log
    merge_log=$(mktemp)
    "$root/devutils/update_patches.sh" merge >"$merge_log" 2>&1 \
      || { cat "$merge_log" >&2; die "patch merge failed"; }
    rm -f "$merge_log"
  fi
  local xcode
  xcode=$(xcode_dir) || exit 1

  log "cloning $from_src (copy-on-write)"
  mkdir -p "$root/build"
  clone_tree "$from_src" "$src"

  # The clone still points at its source checkout in a few places.
  printf '%s\n' "$root/patches" > "$src/.pc/.quilt_patches"
  # Hash the versions the source checkout applied, from its patches/ (or its
  # submodule's, for Helium's patches while it's unmerged).
  [ -f "$record" ] || python3 "$root/devutils/rac/worktree_state.py" "$src" "$from/patches" record \
    || die "couldn't record the patches $from applied"
  local siso="$src/third_party/siso/cipd/siso"
  DEVELOPER_DIR=$xcode "$siso" fs export -C "$out" \
    | python3 -c 'import sys; o, n = sys.argv[1:]; sys.stdout.write(sys.stdin.read().replace(o, n))' \
        "$from_src/" "$src/" \
    | DEVELOPER_DIR=$xcode "$siso" fs import -C "$out" \
    || die "couldn't move siso's build state to this worktree; see the error above"
  local gn_log
  gn_log=$(cd "$src" && DEVELOPER_DIR=$xcode buildtools/mac/gn gen out/Default --fail-on-unused-args \
    --export-compile-commands 2>&1) \
    || { printf '%s\n' "$gn_log" >&2; die "gn gen failed in $out"; }

  force=1
  cmd_sync
  empty_trash

  log "ready. build with: devutils/rac/build-queue.sh he build"
  log "then run with: devutils/rac/worktree.sh run"
}

cmd_run() {
  [ "$root" != "$base" ] || die "in the main checkout, use he run"
  local app="$out/rac.app/Contents/MacOS/rac"
  [ -x "$app" ] || die "no build at $out; run: devutils/rac/build-queue.sh he build"
  # Chromium keeps its crash database next to the default data folder and
  # ignores --user-data-dir, so without this every run writes to the real
  # me.kainoa.rac/Crashpad.
  BREAKPAD_DUMP_LOCATION="$root/build/profile/Crashpad" exec "$app" \
    --user-data-dir="$root/build/profile" \
    --enable-ui-devtools \
    --use-mock-keychain \
    --disable-features=DialMediaRouteProvider \
    "$@"
}

cmd_cleanup() {
  [ "$root" != "$base" ] || die "refusing to clean up the main checkout"
  [ -d "$root/build" ] || return 0

  local pids
  pids=$(pids_matching "$root/build/")
  if [ -n "$pids" ]; then
    log "stopping builds and browsers running from this worktree"
    kill $pids 2>/dev/null || true
    sleep 2
  fi

  # Deleting a full tree takes minutes, so move it aside and delete it in the
  # background. The trash must be on the same volume or mv would copy it.
  mkdir -p "$trash"
  if [ "$(stat -f %d "$root/build")" = "$(stat -f %d "$trash")" ]; then
    mv "$root/build" "$trash/tree.$$.$RANDOM"
    empty_trash
  else
    rm -rf "$root/build"
  fi
  log "removed this worktree's build tree"
}

# Deletes everything in the trash, including trees left behind by an
# interrupted delete. The rm runs in its own session so it survives whoever
# ran this script stopping its leftover processes.
empty_trash() {
  [ -d "$trash" ] || return 0
  (python3 -c 'import os, sys; os.setsid(); os.execvp("rm", ["rm", "-rf", *sys.argv[1:]])' \
    "$trash"/tree.* >/dev/null 2>&1 &)
}

# Tests source this file for its functions.
[ "${BASH_SOURCE[0]}" = "$0" ] || return 0

case "${1:-}" in
  setup) shift; cmd_setup "$@" ;;
  sync)
    case "${2:-}" in
      "") ;;
      --discard) force=1 ;;
      *) die "usage: devutils/rac/worktree.sh sync [--discard]" ;;
    esac
    cmd_sync ;;
  run) shift; cmd_run "$@" ;;
  cleanup) cmd_cleanup ;;
  *) die "usage: devutils/rac/worktree.sh <setup [<checkout>]|sync [--discard]|run|cleanup>" ;;
esac
