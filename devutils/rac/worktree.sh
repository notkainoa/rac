#!/usr/bin/env bash
# Feature trees: git worktrees that each get a copy-on-write clone of the main
# checkout's built Chromium tree. See docs/operations/worktrees.md.
#
# usage: devutils/rac/worktree.sh <setup|sync|run|cleanup>
#   run every command from the root of the worktree
set -euo pipefail

die() { echo "rac worktree: $*" >&2; exit 1; }
log() { echo "rac worktree: $*" >&2; }

# Worktree setup scripts may run with a minimal PATH on Intel or Apple Silicon.
# Prepend in reverse order; don't reorder any entries already present.
for prefix in /usr/local/bin /opt/homebrew/bin; do
  case ":$PATH:" in
    *:"$prefix":*) ;;
    *) [ ! -d "$prefix" ] || PATH="$prefix:$PATH" ;;
  esac
done
for tool in git python3 quilt greadlink; do
  command -v "$tool" >/dev/null || die "$tool not found; install it with Homebrew"
done

root=$(cd "$(git rev-parse --show-toplevel)" && pwd -P)
base=${REPO_ROOT_PATH:-$(git -C "$root" worktree list --porcelain | sed -n '1s/^worktree //p')}
base=$(cd "$base" && pwd -P)
src="$root/build/src"
base_src="$base/build/src"
out="$src/out/Default"
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

dev_names() {
  python3 "$root/devutils/rac/dev_names.py" "$1" -t "$src" >&2 \
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

# Patch hashes and original bytes live beside quilt's preimages in .pc.
# The helper verifies saved postimages in temporary trees before any pop.
stack() {
  python3 "$root/devutils/rac/worktree_state.py" "$1" "$src" "${2:-$root/patches}"
}

# Makes the applied quilt stack match this tree's patches, popping only the
# patches that changed (and everything above them) so the rebuild stays small.
cmd_sync() {
  [ -d "$src/.pc" ] || die "no build tree at $src"
  [ -f "$root/patches/series.merged" ] || die "patches are not merged; run: source dev.sh && he merge"
  local keep applied wanted noop plan
  # Command substitution propagates verification failure (a process
  # substitution would hide it). This preflight does not change names, their
  # archives, the patch stack, or source files.
  plan=$(stack plan) || die "sync preflight failed; no source files were changed"
  read -r keep applied wanted noop <<< "$plan"

  # A fully branded, unchanged stack needs no quilt or baseline writes.
  if [ "$noop" -ne 1 ]; then
    # quilt can't pop or push patches on string files that the name passes
    # changed (pop -f would even restore stale copies), so revert the names
    # first. The end of sync applies them again.
    if [ "$keep" -lt "$applied" ] || [ "$applied" -lt "$wanted" ]; then
      dev_names unsub
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

    stack save
    dev_names sub
  fi
  # rac_version.txt can change independently of the patch stack.
  python3 "$root/devutils/rac/rac_version.py" -t "$src" || die "rac_version.py failed"
  log "patch stack is in sync ($wanted applied)"
}

cmd_setup() {
  [ "$root" != "$base" ] || die "run setup in a worktree, not in the main checkout"
  [ -f "$base_src/out/Default/.siso_fs_state" ] || die "the main checkout has no finished build at $base_src"
  [ ! -e "$src" ] || die "$src already exists"
  if [ -n "$(pids_matching "$base_src/third_party/siso")" ]; then
    die "a build is running in the main checkout; wait for it to finish"
  fi

  if [ ! -e "$root/helium-chromium/.git" ]; then
    log "checking out helium-chromium from the main checkout"
    git -C "$root" -c protocol.file.allow=always \
      -c "submodule.helium-chromium.url=$base/.git/modules/helium-chromium" \
      submodule update --init --quiet helium-chromium
  fi

  if [ ! -f "$root/patches/series.merged" ]; then
    local merge_log
    merge_log=$(mktemp)
    "$root/devutils/update_patches.sh" merge >"$merge_log" 2>&1 \
      || { cat "$merge_log" >&2; die "patch merge failed"; }
    rm -f "$merge_log"
  fi

  log "cloning $base_src (copy-on-write)"
  mkdir -p "$root/build"
  clone_tree "$base_src" "$src"

  # The clone still points at the main checkout in a few places.
  printf '%s\n' "$root/patches" > "$src/.pc/.quilt_patches"
  # Seed from the clone's original base versions, never incoming patches.
  stack seed "$base/patches" || die "the cloned base has no verified patch baseline"
  local siso="$src/third_party/siso/cipd/siso"
  "$siso" fs export -C "$out" \
    | python3 -c 'import sys; o, n = sys.argv[1:]; sys.stdout.write(sys.stdin.read().replace(o, n))' \
        "$base_src/" "$src/" \
    | "$siso" fs import -C "$out"
  (cd "$src" && buildtools/mac/gn gen out/Default --fail-on-unused-args --export-compile-commands >/dev/null)

  cmd_sync
  empty_trash

  log "ready. build with: source dev.sh && he build"
  log "then run with: devutils/rac/worktree.sh run"
}

cmd_run() {
  [ "$root" != "$base" ] || die "in the main checkout, use he run"
  local app="$out/rac.app/Contents/MacOS/rac"
  [ -x "$app" ] || die "no build at $out; run: source dev.sh && he build"
  exec "$app" \
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

case "${1:-}" in
  setup) cmd_setup ;;
  sync) cmd_sync ;;
  run) shift; cmd_run "$@" ;;
  cleanup) cmd_cleanup ;;
  *) die "usage: devutils/rac/worktree.sh <setup|sync|run|cleanup>" ;;
esac
