#!/usr/bin/env bash
# Runs rac's heavy work — Chromium compiles and browser launches for
# screenshots — on the maintainer's MacBook Pro over ssh, so the shared
# Air stays responsive. Threads, git, and reviews stay on the Air.
#
# usage: devutils/rac/remote-build.sh [--dry-run] <command> [args...]
#   setup-host                        check the Pro and create ~/rac-remote
#   seed-base <sync worktree> <tag>   push the tag and seed a base tree
#   push <worktree>                   push its branch, make or update its clone
#   build <worktree> [-- targets...]  build the clone through the remote queue
#   run <worktree> [--timeout S] [-- args...]
#                                     launch the clone's browser, then stop it
#   pull <worktree> <remote path> <local path>
#                                     rsync a file inside the clone back
#   status                            remote uptime, disk, and build queue
#
# The remote host comes from RAC_REMOTE_HOST (default kainoas-macbook-pro).
# Everything on the Pro lives under ~/rac-remote there and nowhere else:
# the bare repos rac.git and helium-chromium.git, a base/ checkout at the
# seeded tag, one clone per feature worktree in wt/<name>, and the build
# queue's state in build-queue/. The Pro is the maintainer's own Mac: no
# command here deletes anything there, starts a build outside the queue,
# or launches a browser other than a clone's own, in the background.
set -euo pipefail

die() { echo "rac remote: $*" >&2; exit 1; }
refuse() { echo "rac remote: refusing: $*" >&2; exit 2; }
log() { echo "rac remote: $*" >&2; }

host=${RAC_REMOTE_HOST:-kainoas-macbook-pro}
# The remote root, relative to the remote home so a different $HOME (such
# as a test's) moves the whole thing.
rdir=rac-remote
repo="$host:$rdir/rac.git"
core_repo="$host:$rdir/helium-chromium.git"
# Free disk seeding needs under the remote home, in GB.
min_free_gb=${RAC_REMOTE_MIN_FREE_GB:-60}
# A non-interactive ssh has no Homebrew on PATH, so quilt, greadlink, and
# Homebrew's python3 would look missing; prepend it to every remote
# command's PATH.
rpath_prefix=${RAC_REMOTE_PATH_PREFIX:-/opt/homebrew/bin:/opt/homebrew/sbin}
# Cores the Pro keeps for its owner while a build runs.
reserve_cores=${RAC_REMOTE_RESERVE_CORES:-4}
dry=0
# Never stop at a password or host-key prompt; fail instead. git and rsync
# use the same ssh.
ssh_cmd=(ssh -o BatchMode=yes)
export GIT_SSH_COMMAND="ssh -o BatchMode=yes"

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
# files (series.merged and Helium's merged copies), except a new rac patch
# under patches/rac/ that was never committed. safe_name accepts a clone
# name that can't leave wt/.
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
    /^\?\? / || /^.?D "?patches\/series"?$/ { next }
    { print }')" ]
}

safe_name() {
  case "$1" in
    '' | .* | *[!A-Za-z0-9._-]*) return 1 ;;
  esac
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

# Prints both machines' Xcode build and macOS SDK version, and refuses
# when either differs: a base tree seeded under one toolchain recompiles
# all of Chromium under another (the Xcode build stamps it, CR_XCODE_BUILD).
check_toolchain() {
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
  echo "rac remote: refusing: the base tree was built with Xcode $2/SDK $3," >&2
  echo "but the Pro has Xcode $rbuild/SDK $rsdk. A copy built with a different" >&2
  echo "SDK recompiles everything (a different Xcode build stamps the tree" >&2
  echo "via CR_XCODE_BUILD). Fix it by installing the same Xcode on the Pro," >&2
  echo "or by a native cold build there; that choice is the maintainer's." >&2
  exit 2
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

# Prints PIDs of processes whose command line contains $1 (worktree.sh's).
pids_matching() {
  ps -axo pid=,command= | P="$1" SELF="$$" awk 'index($0, ENVIRON["P"]) && $1 != ENVIRON["SELF"] { print $1 }'
}

cmd_setup_host() {
  check_toolchain
  remote "$min_free_gb" <<'EOS'
set -e
echo "host: $(hostname)"
echo "macOS: $(sw_vers -productVersion)"
echo "cores: $(sysctl -n hw.ncpu)"
echo "RAM: $(($(sysctl -n hw.memsize) / 1073741824)) GB"
free=$(df -g "$HOME" | awk 'NR==2 {print $4}')
echo "free disk under $HOME: ${free} GB"
if [ "$free" -lt "$1" ]; then
  echo "rac remote: refusing: ${free} GB free under $HOME, under the $1 GB floor for seeding" >&2
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
echo "rac remote: ready at $HOME/rac-remote"
EOS
}

cmd_seed_base() {
  check_toolchain
  local wt tag=$2
  wt=$(worktree_root "$1") || exit 1
  # siso's state holds the tree's physical path, so rewrite from that.
  local src=$wt/build/src
  [ -d "$src" ] || die "no build tree at $src"
  [ -f "$src/out/Default/.siso_fs_state" ] || \
    die "$src has no finished build (no out/Default/.siso_fs_state)"
  [ -z "$(pids_matching "$src/third_party/siso")" ] || \
    die "a build is running in $wt; wait for it to finish"
  git -C "$wt" rev-parse -q --verify "refs/tags/$tag" >/dev/null \
    || die "no tag $tag in $wt"
  local branch sub head
  branch=$(git -C "$wt" symbolic-ref -q --short HEAD) \
    || die "$wt is on a detached HEAD"
  head=$(git -C "$wt" rev-parse HEAD)
  # base/ checks out the tag, and its tree has to be what the tag builds.
  [ "$head" = "$(git -C "$wt" rev-parse "refs/tags/$tag^{commit}")" ] \
    || die "$wt is not at $tag; seed from the worktree whose tree $tag built"
  [ -e "$wt/helium-chromium/.git" ] || die "$wt has no helium-chromium checkout"
  sub=$(git -C "$wt" ls-tree HEAD helium-chromium | awk '$2 == "commit" {print $3}')
  [ -n "$sub" ] || die "$wt pins no helium-chromium commit"
  run_dry git -C "$wt" push --force "$repo" \
    "refs/tags/$tag:refs/tags/$tag" "refs/heads/$branch:refs/heads/$branch"
  run_dry git -C "$wt/helium-chromium" push --force "$core_repo" "$sub:refs/heads/base"
  remote "$tag" <<'EOS'
set -e
cd "$HOME/rac-remote"
[ -e base ] || git clone -q rac.git base
git -C base fetch -q origin \
  '+refs/heads/*:refs/remotes/origin/*' '+refs/tags/*:refs/tags/*'
git -C base checkout -q "$1"
git -C base -c protocol.file.allow=always \
  -c "submodule.helium-chromium.url=$HOME/rac-remote/helium-chromium.git" \
  submodule update --init --quiet helium-chromium
# rsync makes only the last folder of its destination.
mkdir -p base/build
EOS
  # Air to Pro, never the other way, and nothing deleted on either side.
  # Rerunning resumes: --partial keeps half-sent files, and -a skips the
  # ones that arrived.
  xrsync "$src/" "$host:$rdir/base/build/src/"
  remote "$src" <<'EOS'
set -e
cd "$HOME/rac-remote/base"
src=build/src
xcode=$(xcode_dir) || exit 1
# The seeded .pc still points at the Air's patches dir.
printf '%s\n' "$PWD/patches" > "$src/.pc/.quilt_patches"
# update_patches.sh merge fails once merged, so a rerun skips it.
[ -f patches/series.merged ] || devutils/update_patches.sh merge
# Move siso's file state off the Air's paths, like worktree.sh's setup.
siso="$src/third_party/siso/cipd/siso"
DEVELOPER_DIR=$xcode "$siso" fs export -C "$src/out/Default" \
  | python3 -c 'import sys; o, n = sys.argv[1:]; sys.stdout.write(sys.stdin.read().replace(o, n))' \
      "$1/" "$PWD/$src/" \
  | DEVELOPER_DIR=$xcode "$siso" fs import -C "$src/out/Default"
(cd "$src" && DEVELOPER_DIR=$xcode buildtools/mac/gn gen out/Default \
  --fail-on-unused-args --export-compile-commands)
# The Air's record says which patch versions its tree applied; keep it,
# as worktree.sh's setup does, and write one only when it has none.
[ -f "$src/.pc/.rac_applied" ] || python3 devutils/rac/worktree_state.py "$src" "$PWD/patches" record
EOS
  log "seeded $host:$rdir/base at $tag"
}

cmd_push() {
  local wt name=$2
  wt=$(worktree_root "$1") || exit 1
  local branch commit
  branch=$(git -C "$wt" symbolic-ref -q --short HEAD) \
    || die "$wt is on a detached HEAD"
  commit=$(git -C "$wt" rev-parse HEAD)
  git -C "$wt" status --porcelain | only_patch_state \
    || refuse "$wt has uncommitted changes; commit or stash them before pushing"
  run_dry git -C "$wt" push --force "$repo" "refs/heads/$branch:refs/heads/$branch"
  remote "$name" "$branch" "$commit" <<'EOS'
set -e
safe_name "$1" || { echo "rac remote: bad clone name '$1'" >&2; exit 2; }
base="$HOME/rac-remote/base"
[ -d "$base" ] || {
  echo "rac remote: no base checkout at $base; run seed-base first" >&2
  exit 1
}
clone="$HOME/rac-remote/wt/$1"
if [ ! -d "$clone" ]; then
  git -C "$base" fetch -q origin "+refs/heads/$2:refs/remotes/origin/$2"
  mkdir -p "$HOME/rac-remote/wt"
  # -B points the clone's branch at the pushed commit even if base kept a
  # stale branch of that name.
  git -C "$base" worktree add -q -B "$2" "$clone" "$3"
  cd "$clone"
  devutils/rac/worktree.sh setup "$base"
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
  git status --porcelain | only_patch_state || {
    echo "rac remote: refusing: $clone has local changes; pushing would lose them" >&2
    exit 2
  }
  git -C "$base" fetch -q origin "+refs/heads/$2:refs/remotes/origin/$2"
  # What `he unmerge` and `he merge` call; there is no interactive he here.
  # A clone that isn't merged has nothing to unmerge.
  [ ! -f patches/series.merged ] || devutils/update_patches.sh unmerge
  git reset -q --hard "$3"
  devutils/update_patches.sh merge
  if [ -d build/src ]; then
    devutils/rac/worktree.sh sync
  else
    devutils/rac/worktree.sh setup "$base"
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

# Refuses a browser argument that could reach outside the clone or into
# the foreground. Chromium takes `-switch` as well as `--switch`, and the
# last copy of a switch wins, so the checks cover both spellings; paths
# are compared without case, as APFS does.
check_run_arg() {
  local arg=$1 lower name value
  lower=$(printf '%s' "$arg" | tr '[:upper:]' '[:lower:]')
  case "$lower" in
    *"application support"* | *me.kainoa.rac* | *net.imput.helium*)
      refuse "run args may not touch a real profile folder ($arg)" ;;
  esac
  case "$arg" in
    --) return 0 ;;
    -[!-]*) refuse "spell switches with two dashes, not '$arg'" ;;
  esac
  name=${lower#--}
  name=${name%%=*}
  case "$lower" in
    --*)
      case "$name" in
        user-data-dir) refuse "worktree.sh run sets the clone's own --user-data-dir" ;;
        rac-window-screenshot-activate)
          refuse "--rac-window-screenshot-activate takes the foreground on the Pro" ;;
        rac-window-screenshot)
          case "$arg" in
            *=?*) ;;
            *) refuse "give the screenshot file as --rac-window-screenshot=<name>.png" ;;
          esac ;;
      esac ;;
  esac
  value=$arg
  case "$arg" in --*=*) value=${arg#*=} ;; esac
  # Relative paths resolve in the clone, where the browser runs.
  case "$value" in
    /* | '~'*)
      refuse "run args can't name absolute paths ($arg); relative ones land in the clone" ;;
    .. | ../* | */../* | */..)
      refuse "run args can't leave the clone ($arg)" ;;
  esac
}

cmd_run() {
  local name=$1 timeout=90
  shift
  while [ $# -gt 0 ]; do
    case "$1" in
      --timeout)
        [ $# -ge 2 ] || die "run: --timeout needs seconds"
        case "$2" in '' | *[!0-9]*) die "run: --timeout needs seconds" ;; esac
        timeout=$2
        shift 2 ;;
      --) shift; break ;;
      *) die "usage: remote-build.sh run <worktree> [--timeout S] [-- args...]" ;;
    esac
  done
  local arg
  for arg in "$@"; do
    check_run_arg "$arg"
  done
  remote "$name" "$timeout" "$@" <<'EOS'
set -e
safe_name "$1" || { echo "rac remote: bad clone name '$1'" >&2; exit 2; }
clone="$HOME/rac-remote/wt/$1"
timeout=$2
shift 2
[ -d "$clone" ] || {
  echo "rac remote: no clone at $clone; run push first" >&2
  exit 1
}
clone=$(cd "$clone" && pwd -P)
cd "$clone"
# Screenshots land in build/shots; the Air checked they are relative names
# that stay inside it.
shot=
args=()
for arg in "$@"; do
  case "$arg" in
    --rac-window-screenshot=*)
      shot="$clone/build/shots/${arg#--rac-window-screenshot=}"
      arg="--rac-window-screenshot=$shot" ;;
  esac
  args+=("$arg")
done
if [ -n "$shot" ]; then
  mkdir -p "$(dirname "$shot")"
  # A shot left by an earlier run would end the wait at once.
  rm -f "$shot"
fi
# Every process running from the clone's app, never anything else.
app="$clone/build/src/out/Default/rac.app/"
clone_pids() {
  ps -axo pid=,command= | P="$app" awk '{ pid = $1; sub(/^ *[0-9]+ +/, ""); if (index($0, ENVIRON["P"]) == 1) print pid }'
}
stop_clone() {
  local pids i
  for i in 1 2 3 4 5 6 7 8 9 10; do
    pids=$(clone_pids)
    [ -n "$pids" ] || return 0
    kill $pids 2>/dev/null || true
    sleep 1
  done
  pids=$(clone_pids)
  [ -z "$pids" ] || kill -9 $pids 2>/dev/null || true
}
launcher=
trap '[ -z "$launcher" ] || kill "$launcher" 2>/dev/null || true; stop_clone; exit 130' INT TERM HUP
# nice and taskpolicy exec in place, so $launcher is the queue, which
# stops the browser's whole process tree when it is killed.
nice -n 10 taskpolicy -c utility devutils/rac/build-queue.sh \
  devutils/rac/worktree.sh run --rac-launch-in-background ${args[@]+"${args[@]}"} &
launcher=$!
end=$((SECONDS + timeout))
last=-1
while [ "$SECONDS" -lt "$end" ]; do
  if [ -n "$shot" ] && [ -f "$shot" ]; then
    size=$(stat -f %z "$shot" 2>/dev/null || echo 0)
    # Settled: a real file whose size stopped changing between checks.
    if [ "$size" -gt 0 ] && [ "$size" = "$last" ]; then break; fi
    last=$size
  fi
  sleep 1
  kill -0 "$launcher" 2>/dev/null || break
done
killed=0
if kill -0 "$launcher" 2>/dev/null; then
  killed=1
  kill "$launcher" 2>/dev/null || true
fi
status=0
wait "$launcher" 2>/dev/null || status=$?
launcher=
stop_clone
[ "$killed" = 0 ] || status=0
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
  echo "rac remote: no base checkout yet; run seed-base first"
fi
EOS
}

if [ "${1:-}" = "--dry-run" ]; then
  dry=1
  shift
fi
case "${1:-}" in
  setup-host)
    [ $# = 1 ] || die "usage: remote-build.sh setup-host"
    cmd_setup_host ;;
  seed-base)
    [ $# = 3 ] || die "usage: remote-build.sh seed-base <sync worktree> <tag>"
    cmd_seed_base "$2" "$3" ;;
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
    [ $# -ge 2 ] || die "usage: remote-build.sh run <worktree> [--timeout S] [-- args...]"
    name=$(clone_name "$2")
    shift 2
    cmd_run "$name" "$@" ;;
  pull)
    [ $# = 4 ] || die "usage: remote-build.sh pull <worktree> <remote path> <local path>"
    name=$(clone_name "$2")
    cmd_pull "$name" "$3" "$4" ;;
  status)
    [ $# = 1 ] || die "usage: remote-build.sh status"
    cmd_status ;;
  *) die "usage: remote-build.sh [--dry-run] <setup-host|seed-base|push|build|run|pull|status>" ;;
esac
