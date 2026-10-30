#!/usr/bin/env python3

# Copyright 2026 The rac Authors
# You can use, redistribute, and/or modify this source code under
# the terms of the GPL-3.0 license that can be found in the LICENSE file.
"""Runs remote-build.sh with a fake ssh and rsync first on PATH.

The fake ssh runs the "remote" command locally with HOME pointed at a
temporary remote home, so tests exercise the real remote scripts without
contacting any host. The fake rsync copies inside the same temp dirs.
Nothing outside TemporaryDirectory is touched.

Run from the repository root:
    python3 -m unittest discover -s devutils/rac -p 'test_*.py' -v
"""

from pathlib import Path
import json
import re
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / 'remote-build.sh'

# Every remote command arrives either as `bash -s -- <args>` with the
# script on stdin, or as one joined command string. Both run locally with
# HOME at the fake remote home and the remote's own stub bin first.
FAKE_SSH = '''\
echo "ssh-argv $*" >> "$RAC_FAKE_LOG"
export HOME="$RAC_FAKE_REMOTE_HOME"
export PATH="$HOME/bin:${RAC_FAKE_PATH:-$PATH}"
cd "$HOME" || exit 1
[ -z "${RAC_FAKE_REMOTE_XCODE_BUILD:-}" ] || export XCODE_BUILD_FILE="$RAC_FAKE_REMOTE_XCODE_BUILD"
[ -z "${RAC_FAKE_REMOTE_XCODE_SDK:-}" ] || export XCODE_SDK_FILE="$RAC_FAKE_REMOTE_XCODE_SDK"
while [ "${1#-}" != "$1" ]; do
  case "$1" in -o) shift 2 ;; *) shift ;; esac
done
shift
echo "ssh $*" >> "$RAC_FAKE_LOG"
if [ "${1:-}" = "bash" ] && [ "${2:-}" = "-s" ]; then
  shift 2
  [ "${1:-}" = "--" ] && shift
  exec bash -s -- "$@"
fi
exec bash -c "$*"
'''

# The last two arguments are the source and destination; a `host:` prefix
# means the fake remote home, including for absolute paths so a test can
# never write outside it.
FAKE_RSYNC = '''\
if [ "${1:-}" = "--version" ]; then
  echo "${RSYNC_VERSION_LINE:-rsync  version 3.4.1  protocol version 32}"
  exit 0
fi
echo "rsync $*" >> "$RAC_FAKE_LOG"
args=("$@")
n=${#args[@]}
src="${args[n-2]}"
dst="${args[n-1]}"
# A `host:` path is remote; anything else is a local path left alone.
case "$dst" in *:*) dst="$RAC_FAKE_REMOTE_HOME/${dst#*:}" ;; esac
case "$src" in *:*) src="$RAC_FAKE_REMOTE_HOME/${src#*:}" ;; esac
if [ -d "${src%/}" ]; then
  [ -d "$(dirname "${dst%/}")" ] || { echo "rsync: mkdir $dst failed" >&2; exit 11; }
  mkdir -p "$dst"
  # A trailing slash copies the directory's contents; without it, the
  # directory lands inside the destination.
  if [ "$src" = "${src%/}" ]; then
    cp -Rp "$src" "$dst/"
  else
    cp -Rp "${src%/}/." "$dst/"
  fi
else
  mkdir -p "$(dirname "$dst")"
  cp -Rp "$src" "$dst"
fi
'''

# Tools the remote side finds on its stub bin. nice and taskpolicy strip
# their options and exec the rest; sysctl and df answer from the test's
# env; xcodebuild -version reads the build string from a file.
STUB_NICE = '''\
echo "nice $*" >> "$RAC_FAKE_LOG"
[ "$1" = "-n" ] && shift 2
exec "$@"
'''
STUB_TASKPOLICY = '''\
echo "taskpolicy $*" >> "$RAC_FAKE_LOG"
[ "$1" = "-c" ] && shift 2
exec "$@"
'''
STUB_SYSCTL = '''\
case "$*" in
  *ncpu*) echo "${FAKE_CORES:-8}" ;;
  *memsize*) echo "${FAKE_MEM:-34359738368}" ;;
  *) echo 0 ;;
esac
'''
STUB_DF = '''\
if [ -n "${DF_BROKEN:-}" ]; then
  echo "df: something unexpected happened"
elif [ -n "${DF_AVAILABLE:-}" ]; then
  echo "Filesystem 1G-blocks Used Available Capacity iused ifree %iused Mounted on"
  echo "/dev/fake 100 95 $DF_AVAILABLE 99% 0 0 0% /"
else
  exec /bin/df "$@"
fi
'''
STUB_XCODEBUILD = '''\
if [ "${1:-}" = "-version" ]; then
  echo "Xcode 16.4"
  echo "Build version $(cat "${XCODE_BUILD_FILE:-/dev/null}" 2>/dev/null || echo 16F6)"
fi
exit 0
'''
STUB_XCRUN = '''\
if [ "${1:-}" = "--show-sdk-version" ]; then
  cat "${XCODE_SDK_FILE:-/dev/null}" 2>/dev/null || echo "26.0"
fi
exit 0
'''

# Committed into fixture checkouts: they stand in for the real scripts on
# the remote side, logging each call to the test's log file.
STUB_WORKTREE_SH = '''\
echo "worktree.sh $*" >> "$RAC_FAKE_LOG"
# Like the real setup, leave the patches merged.
if [ "$1" = setup ] && [ ! -f patches/series.merged ]; then
  devutils/update_patches.sh merge
fi
# Like the real sync, record the applied stack (which needs quilt's .pc).
if [ "$1" = sync ] && [ -f build/src/.pc/applied-patches ]; then
  cp build/src/.pc/applied-patches build/src/.pc/.rac_applied
fi
if [ "$1" = "run" ]; then
  # A launch that never produces a browser-shaped process.
  [ -z "${NEVER_LAUNCH:-}" ] || exec sleep "$NEVER_LAUNCH"
  shot=
  for arg in "$@"; do
    case "$arg" in --rac-window-screenshot=*) shot="${arg#--rac-window-screenshot=}" ;; esac
  done
  if [ -n "$shot" ]; then
    mkdir -p "$(dirname "$shot")"
    sleep "${SHOT_DELAY:-1}"
    echo png > "$shot"
  fi
  # Like the harness, read the requests only after the first shot, then
  # write the screenshots they name REQ_DELAY later, all but REQ_SKIP.
  req=
  for arg in "$@"; do
    case "$arg" in --rac-window-screenshot-requests=*) req="${arg#*=}" ;; esac
  done
  if [ -n "$req" ]; then
    (sleep "${REQ_DELAY:-0}"; python3 - "$req" <<'PY'
import os, sys
skip = os.environ.get('REQ_SKIP', '')
for request in open(sys.argv[1]).read().strip().split(' ; '):
    words = request.split()
    while len(words) > 2 and words[0] == 'after':
        words = words[2:]
    outs = []
    if len(words) == 1 and words[0].endswith('.png'):
        outs = [words[0]]
    elif words[0] == 'capture-window':
        outs = [words[2]]
    elif words[0] == 'burst':
        outs = [f'{words[1]}/f{i:02d}.png' for i in range(int(words[2]))]
    for out in outs:
        if not (skip and out.endswith(skip)):
            with open(out, 'w') as f:
                f.write('png\\n')
PY
    ) &
  fi
  # Stand in for the browser: a sleeper titled with this clone's app path
  # so the run command's pgrep finds it and nothing else.
  exec bash -c 'exec -a "$1" sleep 600' _ \
    "$PWD/build/src/out/Default/rac.app/Contents/MacOS/rac"
fi
'''
STUB_QUEUE_SH = '''\
echo "queue $*" >> "$RAC_FAKE_LOG"
[ -z "${QUEUE_EXIT:-}" ] || { echo "build queue: refusing (fake)" >&2; exit "$QUEUE_EXIT"; }
# Like the real queue, a build waits in line with a ticket naming its
# checkout and pid (this process, which execs the build).
if [ "${1:-}" = --full ]; then
  mkdir -p "$RAC_BUILD_QUEUE_DIR/waiting"
  printf '{"pid": %s, "worktree": "%s", "kind": "full", "note": "%s"}\n' \
    "$$" "$(pwd -P)" "$2" > "$RAC_BUILD_QUEUE_DIR/waiting/0-$$.json"
fi
[ -z "${QUEUE_DELAY:-}" ] || sleep "$QUEUE_DELAY"
# The real build-queue.sh consumes its own options before the command.
while [ "${1#-}" != "$1" ]; do
  case "$1" in --full) shift 2 ;; *) shift ;; esac
done
exec "$@"
'''
STUB_UPDATE_PATCHES = '''\
echo "update_patches.sh $*" >> "$RAC_FAKE_LOG"
cd "$(dirname "$0")/.."
case "$1" in
  merge) [ -f patches/series ] || exit 1; mv patches/series patches/series.merged ;;
  unmerge) [ -f patches/series.merged ] || exit 1; mv patches/series.merged patches/series ;;
esac
'''
# dev.sh stand-in committed into fixture repos: `he` logs each first-build
# step the base bootstrap runs, and fakes just enough state for the
# bookkeeping that follows (series.merged, applied-patches, autoninja).
STUB_DEV_SH = '''\
he() {
  echo "he $*" >> "$RAC_FAKE_LOG"
  case "$1" in
    presetup)
      [ -z "${PRESETUP_EXIT:-}" ] || return "$PRESETUP_EXIT"
      [ ! -d build/src/out ] || return 0
      mkdir -p build/src/out/Default build/src/third_party/depot_tools
      echo 'is_debug = false' > build/src/out/Default/args.gn
      printf 'import sys\\nprint("autoninja " + " ".join(sys.argv[1:]))\\n' \\
        > build/src/third_party/depot_tools/autoninja.py
      ;;
    merge) devutils/update_patches.sh merge ;;
    configure)
      echo "configure DEVELOPER_DIR=$DEVELOPER_DIR" >> "$RAC_FAKE_LOG"
      : > build/src/out/Default/build.ninja ;;
  esac
}
'''
STUB_AUTONINJA = '''\
import sys
print('autoninja ' + ' '.join(sys.argv[1:]))
'''
# quilt on the Pro: logs how it was called; push "applies" series.merged
# into .pc (exit 2 once everything is applied, like quilt), or fails on
# QUILT_EXIT; next names the patch a failed push stopped at.
STUB_QUILT = '''\
echo "quilt $* QUILT_PATCHES=$QUILT_PATCHES QUILT_SERIES=$QUILT_SERIES pwd=$(pwd -P)" >> "$RAC_FAKE_LOG"
case "$*" in
  *push*)
    if [ -n "${QUILT_EXIT:-}" ]; then
      echo "Patch rac/x/broken.patch does not apply (enforce with -f)"
      exit "$QUILT_EXIT"
    fi
    [ ! -f .pc/applied-patches ] || { echo "File series fully applied"; exit 2; }
    mkdir -p .pc
    cp "$QUILT_PATCHES/$QUILT_SERIES" .pc/applied-patches ;;
  *next*) echo rac/x/broken.patch ;;
esac
'''
# Fixture python scripts append their argv to the test's call log.
STUB_LOG_PY = '''\
import os, sys
log = os.environ.get('RAC_FAKE_LOG')
if log:
    with open(log, 'a') as f:
        f.write('%s ' + ' '.join(sys.argv[1:]) + '\\n')
'''


def git(repo, *args, check=True):
    return subprocess.run(['git', '-C', str(repo), '-c', 'user.name=t', '-c',
                           'user.email=t@t', '-c', 'commit.gpgsign=false', *args],
                          check=check, capture_output=True, text=True)


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def tool(path, text):
    write(path, '#!/bin/bash\n' + textwrap.dedent(text))
    path.chmod(0o755)


@unittest.skipUnless(sys.platform == 'darwin',
                    'remote-build.sh drives macOS hosts')
class RemoteBuildTest(unittest.TestCase):

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='rac-test-remote-')
        self.addCleanup(temporary.cleanup)
        self.folder = Path(temporary.name).resolve()
        self.bin = self.folder / 'bin'
        self.bin.mkdir()
        self.remote = self.folder / 'remote'
        (self.remote / 'bin').mkdir(parents=True)
        self.log = self.folder / 'remote.log'
        # The transport fakes, first on PATH for both sides.
        tool(self.bin / 'ssh', FAKE_SSH)
        tool(self.bin / 'rsync', FAKE_RSYNC)
        # A fake Xcode both sides find through a stubbed xcode-select.
        xcode = self.folder / 'Xcode' / 'Contents' / 'Developer'
        tool(xcode / 'usr' / 'bin' / 'xcodebuild', 'exit 0\n')
        tool(self.bin / 'xcode-select', f'echo {xcode}\n')
        tool(self.bin / 'xcodebuild', STUB_XCODEBUILD)
        tool(self.bin / 'xcrun', STUB_XCRUN)
        self.xcode_build = self.folder / 'xcode-build'
        self.xcode_build.write_text('16F6\n')
        self.remote_xcode_build = self.folder / 'remote-xcode-build'
        self.remote_xcode_build.write_text('16F6\n')
        self.xcode_sdk = self.folder / 'xcode-sdk'
        self.xcode_sdk.write_text('26.0\n')
        self.remote_xcode_sdk = self.folder / 'remote-xcode-sdk'
        self.remote_xcode_sdk.write_text('26.0\n')
        # Stands in for the Pro's Homebrew bin, which a plain ssh PATH lacks;
        # the script's remote PATH prefix is pointed here.
        self.brew_bin = self.remote / 'brew' / 'bin'
        self.brew_bin.mkdir(parents=True)
        # Stubs the remote side finds first on its own PATH, including its
        # own xcode-select and xcodebuild so the versions can differ.
        for name, body in [('nice', STUB_NICE), ('taskpolicy', STUB_TASKPOLICY),
                           ('sysctl', STUB_SYSCTL), ('df', STUB_DF),
                           ('xcode-select', f'echo {xcode}\n'),
                           ('xcodebuild', STUB_XCODEBUILD),
                           ('xcrun', STUB_XCRUN)]:
            tool(self.remote / 'bin' / name, body)

    def env(self, **extra):
        env = dict(os.environ)
        env.pop('DEVELOPER_DIR', None)
        env.update({
            'PATH': f'{self.bin}:{os.environ["PATH"]}',
            'RAC_REMOTE_HOST': 'fake-host',
            'RAC_FAKE_REMOTE_HOME': str(self.remote),
            'RAC_FAKE_LOG': str(self.log),
            'RAC_FAKE_REMOTE_XCODE_BUILD': str(self.remote_xcode_build),
            'RAC_FAKE_REMOTE_XCODE_SDK': str(self.remote_xcode_sdk),
            'XCODE_BUILD_FILE': str(self.xcode_build),
            'XCODE_SDK_FILE': str(self.xcode_sdk),
            'RAC_RSYNC': str(self.bin / 'rsync'),
            'RAC_REMOTE_PATH_PREFIX': str(self.brew_bin),
        })
        for key, value in extra.items():
            if value is None:
                env.pop(key, None)
            else:
                env[key] = value
        return env

    def run_rb(self, *args, success=None, **env):
        result = subprocess.run(['/bin/bash', SCRIPT, *args],
                                env=self.env(**env), capture_output=True, text=True)
        if success is True:
            self.assertEqual(result.returncode, 0, result.stderr)
        elif success is False:
            self.assertNotEqual(result.returncode, 0, result.stderr)
        return result

    def calls(self):
        return self.log.read_text() if self.log.exists() else ''

    def procs_starting(self, prefix):
        """PIDs whose command line starts with prefix (the run command's
        clone_pids pattern)."""
        out = subprocess.run(['ps', '-axo', 'pid=,command='],
                             capture_output=True, text=True).stdout
        found = []
        for line in out.splitlines():
            pid, _, command = line.strip().partition(' ')
            if pid.isdigit() and command.strip().startswith(prefix):
                found.append(int(pid))
        return found

    def wait_for(self, fn, timeout=15):
        """Polls fn until it returns a truthy value; fails after timeout."""
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            result = fn()
            if result:
                return result
            time.sleep(0.25)
        self.fail('timed out waiting')

    def make_repo(self, path, branch='main'):
        """A git checkout holding stubs for what the remote side runs."""
        path.mkdir(parents=True)
        git(path, 'init', '-q', '-b', branch)
        write(path / 'dev.sh', '#!/bin/bash\n' + STUB_DEV_SH)
        write(path / 'devutils/rac/worktree.sh', '#!/bin/bash\n' + STUB_WORKTREE_SH)
        write(path / 'devutils/rac/build-queue.sh', '#!/bin/bash\n' + STUB_QUEUE_SH)
        write(path / 'devutils/update_patches.sh', '#!/bin/bash\n' + STUB_UPDATE_PATCHES)
        write(path / 'devutils/rac/dev_names.py', STUB_LOG_PY % 'dev_names.py')
        write(path / 'devutils/rac/rac_version.py', STUB_LOG_PY % 'rac_version.py')
        shutil.copy2(HERE / 'worktree_state.py', path / 'devutils/rac/worktree_state.py')
        write(path / 'patches/series', 'a.patch\n')
        write(path / 'patches/a.patch', '--- a/one\n+++ b/one\n@@ -1 +1 @@\n-base\n+saved\n')
        write(path / 'file.txt', 'base\n')
        # Like the real repo, build trees stay out of git.
        write(path / '.gitignore', 'build/\n.pc\n')
        for script in path.rglob('*.sh'):
            script.chmod(0o755)
        git(path, 'add', '-A')
        git(path, 'commit', '-qm', 'fixture')
        return path

    def seed_remote(self, base=True):
        """The layout setup-host leaves, plus what build-base leaves: a
        clone of a GitHub-stand-in repo with the `air` remote pointing at
        the bare rac.git that `push` fills."""
        root = self.remote / 'rac-remote'
        root.mkdir(parents=True, exist_ok=True)
        for repo in ('rac.git', 'helium-chromium.git'):
            git(root, 'init', '-q', '--bare', root / repo)
        if base:
            origin = self.make_origin_repo('base-origin')
            subprocess.run(['git', 'clone', '-q', str(origin), 'base'],
                           cwd=root, capture_output=True, check=True)
            git(root / 'base', 'remote', 'add', 'air', str(root / 'rac.git'))
            git(root / 'base', '-c', 'protocol.file.allow=always',
                'submodule', 'update', '--init', '--quiet', 'helium-chromium')
            # The finished cold build `worktree.sh setup` clones from.
            write(root / 'base/build/src/out/Default/.siso_fs_state', '')
        return root

    def make_origin_repo(self, name='gh-rac'):
        """A repo standing in for github.com/notkainoa/rac: the make_repo
        fixture plus a pinned helium-chromium submodule and a base tag."""
        core = self.make_repo(self.folder / f'{name}-core', branch='main')
        repo = self.make_repo(self.folder / name, branch='main')
        subprocess.run(['git', '-C', str(repo), '-c',
                        'protocol.file.allow=always', 'submodule', 'add', '-q',
                        str(core), 'helium-chromium'],
                       check=True, capture_output=True)
        git(repo, 'commit', '-qm', 'pin helium-chromium')
        git(repo, 'tag', 'base-156')
        return repo

    def remote_clone(self, name='feature'):
        """A clone on the remote, as push would leave it."""
        clone = self.remote / 'rac-remote/wt' / name
        src = self.make_repo(self.folder / f'remote-src-{name}')
        shutil.copytree(src, clone, ignore=shutil.ignore_patterns('.git'))
        return clone


@unittest.skipUnless(sys.platform == 'darwin',
                    'remote-build.sh drives macOS hosts')
class SetupHostTest(RemoteBuildTest):

    def test_prints_host_info_and_initializes(self):
        result = self.run_rb('setup-host', success=True, FAKE_CORES='10',
                             FAKE_MEM=str(64 * 2**30))
        for line in ('host:', 'macOS:', 'cores: 10', 'RAM: 64 GB',
                     'free disk under', 'this Mac: Xcode 16.4', 'the Pro:',
                     '16F6', 'SDK 26.0'):
            self.assertIn(line, result.stdout)
        root = self.remote / 'rac-remote'
        self.assertTrue(root.is_dir())
        for repo in ('rac.git', 'helium-chromium.git'):
            self.assertEqual(git(root / repo, 'rev-parse', '--is-bare-repository')
                             .stdout.strip(), 'true')

    def test_xcode_mismatch_is_only_reported(self):
        # The Pro builds its own base, so different Xcodes are reported,
        # not refused: a tree only has to be built with one toolchain.
        self.remote_xcode_build.write_text('16E100\n')
        result = self.run_rb('setup-host', success=True)
        self.assertIn('16F6', result.stdout)
        self.assertIn('16E100', result.stdout)
        self.assertTrue((self.remote / 'rac-remote').is_dir())

    def test_sdk_mismatch_is_only_reported(self):
        self.remote_xcode_sdk.write_text('25.2\n')
        result = self.run_rb('setup-host', success=True)
        self.assertIn('SDK 26.0', result.stdout)
        self.assertIn('SDK 25.2', result.stdout)
        self.assertTrue((self.remote / 'rac-remote').is_dir())

    def test_low_disk_refuses(self):
        result = self.run_rb('setup-host', success=False, DF_AVAILABLE='30')
        self.assertEqual(result.returncode, 2)
        self.assertIn('30 GB free', result.stderr)
        self.assertFalse((self.remote / 'rac-remote').exists())

    def test_disk_floor_is_configurable(self):
        result = self.run_rb('setup-host', success=True, DF_AVAILABLE='30',
                             RAC_REMOTE_MIN_FREE_GB='20')
        self.assertIn('ready', result.stdout)

    def test_missing_tools_get_a_brew_hint(self):
        # No brew tools on the remote PATH: quilt and greadlink go missing.
        result = self.run_rb('setup-host', success=False,
                             RAC_FAKE_PATH='/usr/bin:/bin')
        self.assertEqual(result.returncode, 2)
        self.assertIn('quilt', result.stderr)
        self.assertIn('greadlink', result.stderr)
        self.assertIn('brew install quilt', result.stderr)
        self.assertIn('brew install coreutils', result.stderr)

    def test_setup_host_refuses_a_nonnumeric_floor(self):
        result = self.run_rb('setup-host', success=False,
                             RAC_REMOTE_MIN_FREE_GB='sixty')
        self.assertIn('RAC_REMOTE_MIN_FREE_GB', result.stderr)
        # Refused on the Air before any ssh.
        self.assertEqual(self.calls(), '')

    def test_df_unparsable_refuses(self):
        # An empty or unparsable remote df is a refusal, not "0 GB free".
        result = self.run_rb('setup-host', success=False, DF_BROKEN='1')
        self.assertEqual(result.returncode, 2)
        self.assertIn('free disk', result.stderr)
        self.assertFalse((self.remote / 'rac-remote').exists())


@unittest.skipUnless(sys.platform == 'darwin',
                    'remote-build.sh drives macOS hosts')
class BuildBaseTest(RemoteBuildTest):
    """build-base: the Pro clones a GitHub ref into ~/rac-remote/base,
    bootstraps it like the repo's normal first build, and queues the cold
    build detached. RAC_REMOTE_REPO_URL points the clone at a local
    fixture so nothing here touches the network."""

    def setUp(self):
        super().setUp()
        self.remote_root = self.seed_remote(base=False)
        self.origin = self.make_origin_repo()
        tool(self.remote / 'bin' / 'quilt', STUB_QUILT)

    def run_base(self, *args, **env):
        env.setdefault('RAC_REMOTE_REPO_URL', str(self.origin))
        return self.run_rb(*args, **env)

    def hand_bootstrapped_base(self):
        """The real Pro's base: cloned and bootstrapped by hand, at the
        base-156 tag, with the handwritten toolchain record."""
        base = self.remote_root / 'base'
        subprocess.run(['git', 'clone', '-q', str(self.origin), str(base)],
                       check=True, capture_output=True)
        git(base, 'checkout', '-q', '--detach', 'base-156')
        (base / 'patches/series').rename(base / 'patches/series.merged')
        for path in ('build/src/out/Default/build.ninja',
                     'build/src/out/Default/args.gn'):
            write(base / path, '')
        write(base / 'build/src/third_party/depot_tools/autoninja.py',
              STUB_AUTONINJA)
        write(base / 'build/src/.pc/applied-patches', 'a.patch\n')
        write(base / 'build/src/.pc/.rac_applied', 'a.patch\n')
        write(base / '.rac-toolchain',
              'Xcode 16.4\nBuild version 16F6\nSDK 26.0\n'
              'DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer\n'
              'commit ' + git(base, 'rev-parse', 'HEAD').stdout.strip() + '\n')
        # Marks this exact clone: a reclone would lose it.
        write(base / '.git/rac-test-marker', 'x\n')
        return base

    def hold_queue(self, worktree, slot='build-1', pid=None):
        """A live queue holder (this test's own pid) for worktree."""
        path = self.remote_root / 'build-queue' / slot
        path.mkdir(parents=True, exist_ok=True)
        (path / 'holder.json').write_text(json.dumps({
            'pid': pid or os.getpid(), 'pgid': None,
            'worktree': str(worktree), 'kind': 'full',
            'note': 'maintainer, 2026-10-29'}, indent=1) + '\n')
        return path

    def test_seed_base_is_replaced(self):
        result = self.run_rb('seed-base', self.folder / 'x', 'v1',
                             success=False)
        self.assertIn('replaced by build-base', result.stderr)
        self.assertEqual(self.calls(), '')

    def test_build_base_prepares_the_base(self):
        result = self.run_base('build-base', 'base-156', success=True)
        base = self.remote_root / 'base'
        tag = git(self.origin, 'rev-parse',
                  'base-156^{commit}').stdout.strip()
        self.assertEqual(git(base, 'rev-parse', 'HEAD').stdout.strip(), tag)
        self.assertTrue((base / 'helium-chromium/.git').exists())
        # Clones fetch the Air's pushed branches through the `air` remote.
        self.assertEqual(git(base, 'remote', 'get-url', 'air').stdout.strip(),
                         str(self.remote_root / 'rac.git'))
        calls = self.calls()
        # Bootstrap = the repo's first build with the stack applied through
        # an explicit quilt push (which makes quilt's .pc) before
        # worktree.sh sync records it, then configure.
        order = [calls.index(step) for step in
                 ('he presetup', 'he merge', 'quilt --quiltrc - push -a --fuzz 0',
                  'worktree.sh sync', 'he configure')]
        self.assertEqual(order, sorted(order), calls)
        # Never `he push`: its --refresh rewrites patch files.
        self.assertNotIn('he push', calls)
        self.assertIn(f'QUILT_PATCHES={base}/patches QUILT_SERIES=series.merged '
                      f'pwd={base}/build/src', calls)
        self.assertIn('a.patch',
                      (base / 'build/src/.pc/.rac_applied').read_text())
        # Every phase printed a heartbeat to the caller and the bootstrap
        # log, in order.
        blog = (self.remote_root / 'logs/bootstrap.log').read_text()
        for phase in ('he presetup', 'he merge', 'quilt push -a --fuzz 0',
                      'worktree.sh sync', 'he configure', 'base prepared'):
            self.assertRegex(result.stdout,
                             r'rac remote: \[\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\] .*'
                             + re.escape(phase), phase)
            self.assertIn(phase, blog)
        beats = [l for l in result.stdout.splitlines() if l.startswith('rac remote: [')]
        self.assertTrue(all(l.endswith('…') for l in beats), beats)
        # Without --approved nothing was queued and no toolchain recorded.
        self.assertNotIn('queue --full', calls)
        self.assertFalse((base / '.rac-toolchain').exists())
        self.assertFalse((self.remote_root / 'logs/cold-build.log').exists())
        # The printed command starts the build.
        self.assertIn('build-base --resume', result.stderr)
        self.assertIn('--approved', result.stderr)

    def test_build_base_without_approval_prepares_but_does_not_build(self):
        # A branch ref resolves through origin/<branch>.
        result = self.run_base('build-base', 'main', success=True)
        base = self.remote_root / 'base'
        self.assertEqual(git(base, 'rev-parse', 'HEAD').stdout.strip(),
                         git(self.origin, 'rev-parse', 'main').stdout.strip())
        self.assertIn('build-base --resume', result.stderr)
        self.assertNotIn('--full', self.calls())

    def test_build_base_queues_the_full_build_detached(self):
        started = time.monotonic()
        result = self.run_base('build-base', 'base-156', '--approved',
                               'kainoa 2026-10-29', success=True,
                               QUEUE_DELAY='10')
        # The ssh call returns while the queued build is still waiting.
        self.assertLess(time.monotonic() - started, 10)
        self.assertIn('remote-build.sh status', result.stderr)
        self.assertIn('remote-build.sh log', result.stderr)
        # The detached build logs to cold-build.log, not to the session.
        log_file = self.remote_root / 'logs/cold-build.log'
        self.wait_for(lambda: log_file.exists()
                      and 'autoninja' in log_file.read_text(), timeout=30)
        self.assertIn('autoninja -C out/Default chrome chromedriver '
                      '-local_jobs=4 -k 0', log_file.read_text())
        self.wait_for(lambda: 'queue --full' in self.calls())
        calls = self.calls()
        self.assertIn('nice -n 10', calls)
        self.assertIn('taskpolicy -c utility', calls)
        self.assertIn('queue --full kainoa 2026-10-29 --allow-main --priority',
                      calls)
        # The Pro's own Xcode reached the he calls and the queued build.
        xcode = f'{self.folder}/Xcode/Contents/Developer'
        self.assertIn(f'configure DEVELOPER_DIR={xcode}', calls)
        self.assertIn(f'DEVELOPER_DIR={xcode}', calls)

    def test_build_base_records_the_toolchain(self):
        self.run_base('build-base', 'base-156', '--approved',
                      'kainoa 2026-10-29', success=True)
        # The record is the xcodebuild -version output plus SDK,
        # DEVELOPER_DIR=, and commit lines -- the same shape a by-hand
        # bootstrap writes, so either file parses the same way.
        record = (self.remote_root / 'base/.rac-toolchain').read_text()
        self.assertIn('Xcode 16.4', record)
        self.assertIn('Build version 16F6', record)
        self.assertIn('SDK 26.0', record)
        self.assertIn(f'DEVELOPER_DIR='
                      f'{self.folder}/Xcode/Contents/Developer', record)
        head = git(self.remote_root / 'base', 'rev-parse',
                   'HEAD').stdout.strip()
        self.assertIn(f'commit {head}', record)

    def test_build_base_resume_only_restarts_the_build(self):
        self.run_base('build-base', 'base-156', success=True)
        self.log.unlink()
        self.run_base('build-base', '--resume', '--approved',
                      'kainoa next day', success=True)
        calls = self.calls()
        # Nothing but the queued build: no clone, fetch, or bootstrap.
        self.assertNotIn('he presetup', calls)
        self.assertNotIn('dev_names.py', calls)
        self.wait_for(lambda: 'queue --full' in self.calls())
        self.assertIn('queue --full kainoa next day', self.calls())
        # The toolchain record is (re)stamped when the build starts.
        record = self.remote_root / 'base/.rac-toolchain'
        self.wait_for(lambda: record.exists())
        self.assertIn('Build version 16F6', record.read_text())

    def test_resume_needs_an_approval_note(self):
        result = self.run_base('build-base', '--resume', success=False)
        self.assertIn('--approved', result.stderr)
        self.assertEqual(self.calls(), '')

    def test_build_base_detects_a_hand_bootstrapped_base(self):
        # The real Pro's base was cloned and built by hand: a plain clone
        # at the ref's commit with a patched, recorded, configured tree and
        # the handwritten toolchain record. build-base adopts it -- no
        # reclone, no checkout, no bootstrap -- and gives it the `air`
        # remote clones fetch pushed branches through.
        base = self.hand_bootstrapped_base()
        record = (base / '.rac-toolchain').read_text()
        result = self.run_base('build-base', 'base-156', success=True)
        calls = self.calls()
        for step in ('he presetup', 'he merge', 'quilt', 'worktree.sh sync',
                     'he configure'):
            self.assertNotIn(step, calls)
        self.assertIn('already prepared', result.stdout)
        self.assertIn('build-base --resume', result.stderr)
        self.assertNotIn('queue', calls)
        self.assertTrue((base / '.git/rac-test-marker').exists())
        self.assertEqual(git(base, 'remote', 'get-url', 'air').stdout.strip(),
                         str(self.remote_root / 'rac.git'))
        # --approved on the prepared base queues only the build itself, and
        # keeps the toolchain record the tree was started with.
        self.log.unlink()
        self.run_base('build-base', 'base-156', '--approved', 'kainoa again',
                      success=True)
        self.wait_for(lambda: 'queue --full' in self.calls())
        calls = self.calls()
        self.assertNotIn('he presetup', calls)
        self.assertNotIn('he merge', calls)
        self.assertIn('queue --full kainoa again', calls)
        self.assertEqual((base / '.rac-toolchain').read_text(), record)

    def test_build_base_resume_refuses_without_a_tree(self):
        # A cloned-but-never-bootstrapped base has nothing to build.
        base = self.remote_root / 'base'
        subprocess.run(['git', 'clone', '-q', str(self.origin), str(base)],
                       check=True, capture_output=True)
        result = self.run_base('build-base', '--resume', '--approved', 'x',
                               success=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn('Chromium tree', result.stderr)

    def test_build_base_reuses_and_refuses_a_dirty_base(self):
        # A base cloned earlier whose bootstrap never got as far as a tree
        # is fetched and moved to the new ref, not recloned.
        base = self.remote_root / 'base'
        subprocess.run(['git', 'clone', '-q', str(self.origin), str(base)],
                       check=True, capture_output=True)
        write(base / '.git/rac-test-marker', 'x\n')
        write(self.origin / 'file.txt', 'v2\n')
        git(self.origin, 'commit', '-qam', 'v2')
        self.run_base('build-base', 'main', success=True)
        self.assertTrue((base / '.git/rac-test-marker').exists())
        self.assertEqual(git(base, 'rev-parse', 'HEAD').stdout.strip(),
                         git(self.origin, 'rev-parse', 'main').stdout.strip())
        # The Pro only builds: an edit to a tracked file in base refuses.
        write(base / 'file.txt', 'local edit\n')
        result = self.run_base('build-base', 'main', success=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn('local changes', result.stderr)

    def test_build_base_never_moves_a_tree_to_another_ref(self):
        # A base with a Chromium tree for one ref is never checked out to
        # another or bootstrapped again.
        base = self.hand_bootstrapped_base()
        head = git(base, 'rev-parse', 'HEAD').stdout.strip()
        write(self.origin / 'file.txt', 'v2\n')
        git(self.origin, 'commit', '-qam', 'v2')
        result = self.run_base('build-base', 'main', success=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn("won't move a tree", result.stderr)
        self.assertEqual(git(base, 'rev-parse', 'HEAD').stdout.strip(), head)
        self.assertNotIn('he presetup', self.calls())
        self.assertTrue((base / 'build/src/out/Default/build.ninja').exists())

    def test_bootstrap_resumes_a_stalled_base(self):
        # The hand bootstrap stalled after he presetup and he merge, with
        # no quilt .pc for worktree.sh sync. A rerun at the same ref picks
        # up there: presetup finds its tree, merge is skipped, and the
        # explicit quilt push makes .pc before sync.
        base = self.hand_bootstrapped_base()
        shutil.rmtree(base / 'build/src/.pc')
        (base / 'build/src/out/Default/build.ninja').unlink()
        result = self.run_base('build-base', 'base-156', success=True)
        calls = self.calls()
        self.assertTrue((base / '.git/rac-test-marker').exists())
        self.assertNotIn('he merge', calls)
        self.assertLess(calls.index('quilt --quiltrc - push'),
                        calls.index('worktree.sh sync'))
        self.assertTrue((base / 'build/src/.pc/.rac_applied').exists())
        self.assertIn('base prepared', result.stdout)

    def test_bootstrap_quilt_nothing_to_push_is_fine(self):
        # quilt exits 2 when the whole series is already applied.
        base = self.hand_bootstrapped_base()
        (base / 'build/src/.pc/.rac_applied').unlink()
        self.run_base('build-base', 'base-156', success=True)
        self.assertIn('quilt --quiltrc - push -a --fuzz 0', self.calls())
        self.assertIn('worktree.sh sync', self.calls())

    def test_bootstrap_stops_on_a_patch_that_does_not_apply(self):
        result = self.run_base('build-base', 'base-156', success=False,
                               QUILT_EXIT='1')
        self.assertEqual(result.returncode, 1)
        self.assertIn('quilt push failed (exit 1) at patch rac/x/broken.patch',
                      result.stderr)
        # The quilt output reached the caller through the log's tail.
        self.assertIn('does not apply', result.stderr)
        calls = self.calls()
        self.assertNotIn('worktree.sh sync', calls)
        self.assertNotIn('he configure', calls)
        blog = (self.remote_root / 'logs/bootstrap.log').read_text()
        self.assertIn('stopped: applying patches: rac/x/broken.patch', blog)
        # Nothing was queued, even with an approval.
        self.log.unlink()
        self.run_base('build-base', 'base-156', '--approved', 'k', success=False,
                      QUILT_EXIT='1')
        self.assertNotIn('queue', self.calls())

    def test_bootstrap_failure_names_the_phase(self):
        result = self.run_base('build-base', 'base-156', success=False,
                               PRESETUP_EXIT='3')
        self.assertEqual(result.returncode, 3)
        self.assertIn('stopped in: downloading and preparing Chromium', result.stderr)
        self.assertNotIn('he merge', self.calls())

    def test_bootstrap_refuses_while_the_base_is_busy(self):
        # A build of the base holds the queue: no bootstrap step may touch
        # its tree, with or without an approval.
        base = self.hand_bootstrapped_base()
        (base / 'build/src/.pc/.rac_applied').unlink()
        self.hold_queue(base)
        for args in (('base-156',), ('base-156', '--approved', 'k')):
            self.log.unlink(missing_ok=True)
            result = self.run_base('build-base', *args, success=False)
            self.assertEqual(result.returncode, 2)
            self.assertIn('queue holds or queues a build', result.stderr)
            calls = self.calls()
            for step in ('quilt', 'he presetup', 'he merge', 'he configure',
                         'worktree.sh sync', 'queue --full'):
                self.assertNotIn(step, calls)

    def test_bootstrap_refuses_while_another_bootstrap_runs(self):
        base = self.hand_bootstrapped_base()
        (base / 'build/src/.pc/.rac_applied').unlink()
        lock = self.remote_root / 'logs/.bootstrap.lock'
        lock.parent.mkdir(parents=True, exist_ok=True)
        holder = subprocess.Popen(
            ['python3', '-c', 'import fcntl, sys, time; f = open(sys.argv[1], "a"); '
             'fcntl.flock(f, fcntl.LOCK_EX); print("locked", flush=True); time.sleep(60)',
             str(lock)], stdout=subprocess.PIPE, text=True)
        self.addCleanup(lambda: (holder.kill(), holder.wait()))
        holder.stdout.readline()
        result = self.run_base('build-base', 'base-156', success=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn('another build-base bootstrap', result.stderr)
        self.assertNotIn('quilt', self.calls())
        # --resume refuses too, and `log` says the bootstrap still runs.
        (base / 'build/src/.pc/.rac_applied').write_text('a.patch\n')
        result = self.run_base('build-base', '--resume', '--approved', 'k',
                               success=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn('bootstrap is still running', result.stderr)
        write(self.remote_root / 'logs/bootstrap.log',
              'rac remote: [2026-10-29 22:00:00] applying patches…\n')
        result = self.run_rb('log', success=True)
        self.assertIn('still running', result.stdout)

    def test_resume_refuses_when_the_base_already_holds_the_queue(self):
        # The real Pro right now: a hand-queued cold build of the base
        # holds both build slots. --resume must see it and refuse, not
        # queue a second one behind it.
        base = self.hand_bootstrapped_base()
        record = (base / '.rac-toolchain').read_text()
        self.hold_queue(base, 'build-1')
        self.hold_queue(base, 'build-2')
        result = self.run_base('build-base', '--resume', '--approved', 'k',
                               success=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn('already holds or queues a build', result.stderr)
        self.assertIn('build-1/holder.json', result.stderr)
        self.assertIn('maintainer, 2026-10-29', result.stderr)
        self.assertNotIn('queue', self.calls())
        self.assertEqual((base / '.rac-toolchain').read_text(), record)
        self.assertFalse((self.remote_root / 'logs/cold-build.log').exists())
        # A waiting ticket for the base counts as well.
        shutil.rmtree(self.remote_root / 'build-queue')
        write(self.remote_root / 'build-queue/waiting/0-000000001.json',
              json.dumps({'pid': os.getpid(), 'worktree': str(base),
                          'pool': 'build', 'need': 2}) + '\n')
        self.run_base('build-base', '--resume', '--approved', 'k',
                      success=False)
        self.assertNotIn('queue', self.calls())
        # A holder whose process died is stale, and a live build of some
        # other checkout only means the cold build waits its turn.
        shutil.rmtree(self.remote_root / 'build-queue')
        dead = subprocess.Popen(['/usr/bin/true'])
        dead.wait()
        self.hold_queue(base, 'build-1', pid=dead.pid)
        self.hold_queue(self.remote_root / 'wt/other', 'build-2')
        self.run_base('build-base', '--resume', '--approved', 'k', success=True)
        self.wait_for(lambda: 'queue --full k' in self.calls())

    def test_resume_refuses_an_unfinished_bootstrap(self):
        # A tree whose bootstrap stalled (no quilt .pc, never configured)
        # must not be cold-built.
        base = self.hand_bootstrapped_base()
        shutil.rmtree(base / 'build/src/.pc')
        result = self.run_base('build-base', '--resume', '--approved', 'k',
                               success=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn('bootstrap never finished', result.stderr)
        self.assertNotIn('queue', self.calls())

    def test_resume_checks_the_ref_and_the_toolchain(self):
        base = self.hand_bootstrapped_base()
        result = self.run_base('build-base', '--resume', '--approved', 'k',
                               'no-such-tag', success=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn("no ref 'no-such-tag'", result.stderr)
        # The tree keeps its toolchain for life: a drifted Pro refuses
        # instead of restamping the record.
        record = (base / '.rac-toolchain').read_text()
        self.remote_xcode_build.write_text('17A1\n')
        result = self.run_base('build-base', '--resume', '--approved', 'k',
                               'base-156', success=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn('17A1', result.stderr)
        self.assertEqual((base / '.rac-toolchain').read_text(), record)
        self.assertNotIn('queue', self.calls())

    def test_build_base_reports_a_queue_that_refuses(self):
        self.hand_bootstrapped_base()
        result = self.run_base('build-base', '--resume', '--approved', 'k',
                               success=False, QUEUE_EXIT='75')
        self.assertEqual(result.returncode, 1)
        self.assertIn('queue exited 75', result.stderr)
        self.assertIn('refusing (fake)', result.stderr)

    def test_blank_approval_is_refused_here(self):
        for note in ('', '   '):
            result = self.run_base('build-base', '--resume', '--approved', note,
                                   success=False)
            self.assertIn('--approved', result.stderr)
        self.assertEqual(self.calls(), '')

    def test_log_shows_the_bootstrap_heartbeats(self):
        self.run_base('build-base', 'base-156', success=True)
        result = self.run_rb('log', success=True)
        self.assertIn('bootstrap phases', result.stdout)
        self.assertIn('(quilt push -a --fuzz 0)…', result.stdout)
        self.assertIn('base prepared', result.stdout)
        self.assertNotIn('still running', result.stdout)
        self.assertIn('no cold-build log', result.stdout)

    def test_build_base_refuses_under_120gb(self):
        result = self.run_base('build-base', 'base-156', success=False,
                               DF_AVAILABLE='80')
        self.assertEqual(result.returncode, 2)
        self.assertIn('80 GB free', result.stderr)
        self.assertFalse((self.remote_root / 'base').exists())

    def test_build_base_disk_floor_configurable(self):
        self.run_base('build-base', 'base-156', success=True,
                      DF_AVAILABLE='80', RAC_REMOTE_MIN_FREE_GB='60')
        self.assertTrue((self.remote_root / 'base').exists())

    def test_build_base_refuses_a_nonnumeric_floor(self):
        result = self.run_base('build-base', 'base-156', success=False,
                               RAC_REMOTE_MIN_FREE_GB='lots')
        self.assertIn('RAC_REMOTE_MIN_FREE_GB', result.stderr)
        # Refused on the Air before any ssh.
        self.assertEqual(self.calls(), '')

    def test_build_base_refuses_a_bad_ref(self):
        for ref in ('bad;ref', '$(id)', 'rev..x'):
            result = self.run_base('build-base', ref, success=False)
            self.assertIn('tag or branch', result.stderr, ref)
        self.assertEqual(self.calls(), '')

    def test_log_tails_the_cold_build_log(self):
        logs = self.remote_root / 'logs'
        logs.mkdir(parents=True)
        (logs / 'cold-build.log').write_text(
            ''.join(f'line {i}\n' for i in range(1, 51)))
        result = self.run_rb('log', success=True)
        self.assertIn('line 50', result.stdout)
        self.assertIn('line 11', result.stdout)
        self.assertNotIn('line 10\n', result.stdout)
        result = self.run_rb('log', '3', success=True)
        self.assertIn('line 50', result.stdout)
        self.assertNotIn('line 47', result.stdout)
        (logs / 'cold-build.log').unlink()
        result = self.run_rb('log', success=True)
        self.assertIn('no cold-build log', result.stdout)


@unittest.skipUnless(sys.platform == 'darwin',
                    'remote-build.sh drives macOS hosts')
class PushTest(RemoteBuildTest):

    def setUp(self):
        super().setUp()
        self.remote_root = self.seed_remote()
        self.wt = self.make_repo(self.folder / 'feature', branch='feat/x')

    def test_push_refuses_dirty_worktree(self):
        (self.wt / 'file.txt').write_text('dirty\n')
        result = self.run_rb('push', self.wt, success=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn('uncommitted', result.stderr)
        self.assertFalse((self.remote_root / 'wt/feature').exists())

    def test_push_allows_the_merged_patch_state(self):
        # he merge deletes patches/series and leaves merged patch copies
        # untracked; neither counts as uncommitted work.
        (self.wt / 'patches/series').unlink()
        write(self.wt / 'patches/series.merged', 'a.patch\n')
        write(self.wt / 'patches/series.orig', 'helium/x.patch\n')
        write(self.wt / 'patches/helium/core/x.patch', 'merged copy\n')
        write(self.wt / 'patches/ungoogled-chromium/y.patch', 'merged copy\n')
        self.run_rb('push', self.wt, success=True)
        self.assertTrue((self.remote_root / 'wt/feature').exists())

    def test_push_refuses_untracked_build_files(self):
        # Untracked files the build would need never reach the clone; the
        # refusal says to commit them.
        for path in ('resources/x.png', 'docs/note.md', 'file2.txt'):
            write(self.wt / path, 'uncommitted\n')
        result = self.run_rb('push', self.wt, success=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn('commit', result.stderr)
        self.assertFalse((self.remote_root / 'wt/feature').exists())

    def test_push_creates_and_updates_a_clone(self):
        self.run_rb('push', self.wt, success=True)
        clone = self.remote_root / 'wt/feature'
        head = git(self.wt, 'rev-parse', 'HEAD').stdout.strip()
        self.assertEqual(git(clone, 'rev-parse', 'HEAD').stdout.strip(), head)
        self.assertIn('worktree.sh setup', self.calls())
        # A second push resets the clone to the new commit and syncs the
        # tree setup made (a clone whose setup never made one gets setup).
        (clone / 'build/src').mkdir(parents=True)
        self.log.unlink()
        write(self.wt / 'file.txt', 'new\n')
        git(self.wt, 'commit', '-qam', 'more')
        self.run_rb('push', self.wt, success=True)
        calls = self.calls()
        self.assertEqual(git(clone, 'rev-parse', 'HEAD').stdout.strip(),
                         git(self.wt, 'rev-parse', 'HEAD').stdout.strip())
        self.assertIn('update_patches.sh unmerge', calls)
        self.assertIn('update_patches.sh merge', calls)
        self.assertIn('worktree.sh sync', calls)

    def test_push_refuses_an_uncommitted_rac_patch(self):
        (self.wt / 'patches/series').unlink()
        write(self.wt / 'patches/series.merged', 'a.patch\nrac/x/new.patch\n')
        write(self.wt / 'patches/rac/x/new.patch', 'new\n')
        result = self.run_rb('push', self.wt, success=False)
        self.assertEqual(result.returncode, 2)
        self.assertFalse((self.remote_root / 'wt/feature').exists())

    def test_push_refuses_a_clone_on_another_branch(self):
        self.run_rb('push', self.wt, success=True)
        other = self.make_repo(self.folder / 'elsewhere' / 'feature', branch='feat/y')
        result = self.run_rb('push', other, success=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn("not 'feat/y'", result.stderr)

    def test_push_refuses_unsafe_folder_names(self):
        for name in ('has space', 'dollar$x', '.hidden'):
            wt = self.make_repo(self.folder / name, branch='feat/z')
            result = self.run_rb('push', wt, success=False)
            self.assertIn("can't name a clone", result.stderr)
        self.assertEqual(self.calls(), '')

    def test_push_refuses_a_dirty_remote_clone(self):
        self.run_rb('push', self.wt, success=True)
        clone = self.remote_root / 'wt/feature'
        (clone / 'file.txt').write_text('edited on the pro\n')
        write(self.wt / 'file.txt', 'new\n')
        git(self.wt, 'commit', '-qam', 'more')
        result = self.run_rb('push', self.wt, success=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn('local changes', result.stderr)

    def holder(self, slot, pid, worktree):
        slot.mkdir(parents=True, exist_ok=True)
        (slot / 'holder.json').write_text(json.dumps({
            'pid': pid, 'pgid': pid, 'worktree': worktree,
            'kind': 'build', 'command': 'he build'}) + '\n')

    def test_push_refuses_a_busy_clone(self):
        self.run_rb('push', self.wt, success=True)
        clone = os.path.realpath(self.remote_root / 'wt/feature')
        queue = self.remote_root / 'build-queue'
        # A live slot holder for this clone refuses the push.
        self.holder(queue / 'build-1', os.getpid(), clone)
        result = self.run_rb('push', self.wt, success=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn('queued or running', result.stderr)
        shutil.rmtree(queue / 'build-1')
        # So does a waiter.
        (queue / 'waiting').mkdir(parents=True)
        write(queue / 'waiting/0-000000001.json',
              json.dumps({'pid': os.getpid(), 'worktree': clone,
                          'pool': 'build'}) + '\n')
        result = self.run_rb('push', self.wt, success=False)
        self.assertEqual(result.returncode, 2)
        shutil.rmtree(queue / 'waiting')
        # A dead holder is stale, not busy: the push goes through.
        stale = subprocess.Popen(['/usr/bin/true'])
        stale.wait()
        self.holder(queue / 'build-2', stale.pid, clone)
        self.run_rb('push', self.wt, success=True)
        shutil.rmtree(queue)
        # A process running from the clone's tree also refuses it.
        rogue = subprocess.Popen(
            ['bash', '-c', 'exec -a "$1" sleep 300', '_',
             f'{clone}/build/src/out/Default/rac.app/Contents/MacOS/rac'])
        self.addCleanup(lambda: (rogue.kill(), rogue.wait()))
        result = self.run_rb('push', self.wt, success=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn('running under', result.stderr)

    def test_push_refuses_on_toolchain_drift(self):
        # push runs worktree.sh setup/sync (gn gen) in the clone, so a
        # drifted Pro refuses before touching it.
        write(self.remote_root / 'base/.rac-toolchain',
              'xcode_build 16F6\nsdk 26.0\n')
        self.remote_xcode_build.write_text('16F99\n')
        result = self.run_rb('push', self.wt, success=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn('changed since the base was built', result.stderr)
        self.assertIn('16F99', result.stderr)
        self.assertFalse((self.remote_root / 'wt/feature').exists())

    def test_push_clone_inherits_the_toolchain_record(self):
        write(self.remote_root / 'base/.rac-toolchain',
              'xcode_build 16F6\nsdk 26.0\n')
        self.run_rb('push', self.wt, success=True)
        clone = self.remote_root / 'wt/feature'
        # It lives in the clone's ignored build/, so it never counts as
        # an untracked change that blocks the next push.
        self.assertEqual((clone / 'build/.rac-toolchain').read_text(),
                         'xcode_build 16F6\nsdk 26.0\n')
        self.assertFalse((clone / '.rac-toolchain').exists())
        # The clone keeps the toolchain it was built with even if the base
        # is rebuilt under a newer one: builds in it check its own record.
        write(self.remote_root / 'base/.rac-toolchain',
              'xcode_build 16F99\nsdk 26.0\n')
        write(clone / 'build/src/third_party/depot_tools/autoninja.py',
              STUB_AUTONINJA)
        self.remote_xcode_build.write_text('16F99\n')
        result = self.run_rb('build', self.wt, success=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn('16F6', result.stderr)

    def test_push_again_after_inheriting_the_toolchain_record(self):
        # The inherited record must not read as an untracked change that
        # blocks every later push; one left at the clone's top by an
        # earlier version doesn't either.
        write(self.remote_root / 'base/.rac-toolchain',
              'xcode_build 16F6\nsdk 26.0\n')
        self.run_rb('push', self.wt, success=True)
        clone = self.remote_root / 'wt/feature'
        write(clone / '.rac-toolchain', 'xcode_build 16F6\nsdk 26.0\n')
        write(self.wt / 'file.txt', 'new\n')
        git(self.wt, 'commit', '-qam', 'more')
        self.run_rb('push', self.wt, success=True)
        self.assertEqual(git(clone, 'rev-parse', 'HEAD').stdout.strip(),
                         git(self.wt, 'rev-parse', 'HEAD').stdout.strip())

    def test_push_waits_for_the_base_build(self):
        # A new clone copies the base's finished tree: not while the base's
        # cold build holds the queue, and not before it ever finished.
        base = self.remote_root / 'base'
        self.holder(self.remote_root / 'build-queue/build-1', os.getpid(),
                    str(base))
        result = self.run_rb('push', self.wt, success=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn("base's build is queued or running", result.stderr)
        self.assertFalse((self.remote_root / 'wt/feature').exists())
        shutil.rmtree(self.remote_root / 'build-queue')
        (base / 'build/src/out/Default/.siso_fs_state').unlink()
        result = self.run_rb('push', self.wt, success=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn('no finished build', result.stderr)
        self.assertFalse((self.remote_root / 'wt/feature').exists())

    def test_push_updates_the_submodule(self):
        # A worktree whose commits pin helium-chromium.
        core = self.make_repo(self.folder / 'push-core', branch='main')
        subprocess.run(['git', '-C', str(self.wt),
                        '-c', 'protocol.file.allow=always',
                        'submodule', 'add', '-q', str(core), 'helium-chromium'],
                       check=True, capture_output=True)
        git(self.wt, 'commit', '-qm', 'pin a')
        pin_a = git(core, 'rev-parse', 'HEAD').stdout.strip()
        self.run_rb('push', self.wt, success=True)
        clone = self.remote_root / 'wt/feature'
        self.assertEqual(git(clone / 'helium-chromium', 'rev-parse', 'HEAD')
                         .stdout.strip(), pin_a)
        # The Pro's bare repo got the pinned objects.
        self.assertEqual(git(self.remote_root / 'helium-chromium.git',
                             'cat-file', '-e', f'{pin_a}^{{commit}}')
                         .returncode, 0)
        # Repin to a newer core commit; the second push moves the clone's
        # submodule with it.
        write(core / 'file.txt', 'v2\n')
        git(core, 'commit', '-qam', 'b')
        pin_b = git(core, 'rev-parse', 'HEAD').stdout.strip()
        git(self.wt / 'helium-chromium', 'fetch', '-q', 'origin')
        git(self.wt / 'helium-chromium', 'checkout', '-q', pin_b)
        git(self.wt, 'add', 'helium-chromium')
        git(self.wt, 'commit', '-qm', 'pin b')
        self.run_rb('push', self.wt, success=True)
        self.assertEqual(git(clone / 'helium-chromium', 'rev-parse', 'HEAD')
                         .stdout.strip(), pin_b)


@unittest.skipUnless(sys.platform == 'darwin',
                    'remote-build.sh drives macOS hosts')
class BuildTest(RemoteBuildTest):

    def setUp(self):
        super().setUp()
        self.remote_root = self.seed_remote()
        self.remote_clone('feature')
        self.wt = self.make_repo(self.folder / 'feature', branch='feat/x')
        # autoninja itself, where the build's bash -c looks for it.
        src = self.remote_root / 'wt/feature/build/src'
        write(src / 'third_party/depot_tools/autoninja.py', STUB_AUTONINJA)
        # The toolchain record the base's cold build stamps (older shape).
        write(self.remote_root / 'base/.rac-toolchain',
              'xcode_build 16F6\nsdk 26.0\n')

    def test_build_composes_the_queued_autoninja_call(self):
        # The Pro has 18 cores; the default reserve of 4 leaves 14 jobs.
        result = self.run_rb('build', self.wt, success=True, FAKE_CORES='18')
        calls = self.calls()
        self.assertIn('nice -n 10', calls)
        self.assertIn('taskpolicy -c utility', calls)
        self.assertIn('queue bash -c', calls)
        self.assertIn('autoninja -C out/Default chrome chromedriver -local_jobs=14 -k 0',
                      result.stdout)

    def test_build_with_targets(self):
        result = self.run_rb('build', self.wt, '--', 'chrome', success=True)
        self.assertIn('autoninja -C out/Default chrome -local_jobs=4', result.stdout)
        self.assertNotIn('chromedriver', result.stdout)

    def test_build_reserves_fewer_cores_on_request(self):
        result = self.run_rb('build', self.wt, success=True, FAKE_CORES='18',
                             RAC_REMOTE_RESERVE_CORES='10')
        self.assertIn('-local_jobs=8', result.stdout)

    def test_build_jobs_floors_at_one(self):
        result = self.run_rb('build', self.wt, success=True, FAKE_CORES='2')
        self.assertIn('-local_jobs=1', result.stdout)

    def test_build_refuses_options_as_targets(self):
        for target in ('-t', '-C/tmp', 'a;b', '$(id)'):
            result = self.run_rb('build', self.wt, '--', target, success=False)
            self.assertEqual(result.returncode, 2, target)
        self.assertEqual(self.calls(), '')

    def test_build_exit_code_propagates(self):
        result = self.run_rb('build', self.wt, success=False, QUEUE_EXIT='7')
        self.assertEqual(result.returncode, 7)

    def test_build_refuses_on_toolchain_drift(self):
        # The Pro moved to a new Xcode since the base was built.
        self.remote_xcode_build.write_text('16F99\n')
        result = self.run_rb('build', self.wt, success=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn('16F99', result.stderr)
        self.assertIn('16F6', result.stderr)
        self.assertIn('recompile everything', result.stderr)
        self.assertNotIn('autoninja', self.calls())
        self.remote_xcode_build.write_text('16F6\n')
        # An SDK drift refuses too.
        self.remote_xcode_sdk.write_text('25.1\n')
        result = self.run_rb('build', self.wt, success=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn('25.1', result.stderr)

    def test_toolchain_record_parses_the_handwritten_format(self):
        # A by-hand bootstrap records the toolchain as the xcodebuild
        # -version output plus SDK, DEVELOPER_DIR=, and commit lines; the
        # drift check has to read that shape, not only remote-build.sh's
        # own. (The setUp record uses the older xcode_build/sdk shape.)
        record = self.remote_root / 'base/.rac-toolchain'
        write(record, 'Xcode 16.4\nBuild version 16F6\nSDK 26.0\n'
              f'DEVELOPER_DIR={self.folder}/Xcode/Contents/Developer\n'
              'commit 433a847\n')
        self.run_rb('build', self.wt, success=True)
        write(record, 'Xcode 26.0\nBuild version 17A100\nSDK 26.0\n'
              'DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer\n'
              'commit 433a847\n')
        result = self.run_rb('build', self.wt, success=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn('17A100', result.stderr)


    def test_a_partial_toolchain_record_refuses(self):
        # An SDK line without a build line can't prove the toolchain.
        record = self.remote_root / 'base/.rac-toolchain'
        write(record, 'SDK 26.0\ncommit 433a847\n')
        result = self.run_rb('build', self.wt, success=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn('no Xcode build or SDK line', result.stderr)

    def test_host_that_looks_like_an_ssh_option_is_refused(self):
        for bad in ('-oProxyCommand=evil', 'host name', 'h;x'):
            result = self.run_rb('status', success=False, RAC_REMOTE_HOST=bad)
            self.assertEqual(result.returncode, 2, bad)
            self.assertIn('plain host name', result.stderr)

@unittest.skipUnless(sys.platform == 'darwin',
                    'remote-build.sh drives macOS hosts')
class RunTest(RemoteBuildTest):

    # Every verb the deployed harness knows, as the checker lists them.
    HARNESS_VERBS = '''after appearance burst capture-window click command
        contrast hit key move nsflags nskey nspress nstype open-urls
        pointer pointer-path profile-window record space-new space-theme
        swipe target type wheel windows'''.split()

    def setUp(self):
        super().setUp()
        self.remote_root = self.seed_remote()
        self.clone = self.remote_clone('feature')
        self.wt = self.make_repo(self.folder / 'feature', branch='feat/x')
        self.seed_harness()

    def seed_harness(self, without=()):
        """The verbs the fake clone's harness knows, as string literals."""
        rac = self.clone / 'build/src/chrome/browser/ui/views/rac'
        write(rac / 'window_screenshot.mm',
              ''.join(f'if (verb == "{verb}") {{\n' for verb in
                      self.HARNESS_VERBS if verb not in without))

    def test_run_refuses_profile_and_foreground_args(self):
        for args, why in [
            (('--', '--user-data-dir=/tmp/x'), '--user-data-dir'),
            (('--', '--user-data-dir', '/tmp/x'), '--user-data-dir'),
            (('--', '~/Library/Application Support/x'), 'Application Support'),
            (('--', '--x=/Users/k/library/APPLICATION SUPPORT/me.kainoa.rac'),
             'real profile'),
            (('--', '--x=~/Library/Application%20Support/net.imput.helium'),
             'real profile'),
            (('--', '--rac-window-screenshot=/Users/k/Desktop/x.png'), 'absolute'),
            (('--', '--rac-window-screenshot=../../x.png'), 'leave the clone'),
            (('--', '--rac-window-screenshot', 'x.png'), '--rac-window-screenshot='),
            (('--', '--rac-window-screenshot='), '--rac-window-screenshot='),
            (('--', '--rac-arc-import-fixture='), 'needs a path'),
            (('--', '--rac-import-source-root='), 'needs a path'),
            # The delay takes 1-4 digits only.
            (('--', '--rac-window-screenshot-delay=x'), '1-4 digits'),
            (('--', '--rac-window-screenshot-delay='), '1-4 digits'),
            (('--', '--rac-window-screenshot-delay=12345'), '1-4 digits'),
            (('--', '--rac-window-screenshot-delay=1.5'), '1-4 digits'),
            # Chromium opens a bare argument as a URL, so it gets the
            # requests file's URL allowlist.
            (('--', 'file:///Users/k/.ssh/id_rsa', '--rac-window-screenshot=x.png'),
             'may only open'),
            (('--', 'view-source:file:///etc/hosts'), 'may only open'),
            (('--', 'https://evil.com/x.dmg'), 'may only open'),
            (('--', 'evil.com'), 'may only open'),
            (('--', 'notes.txt'), 'may only open'),
            (('--', 'chrome://settings/importData'), 'may only open'),
            (('--', 'chrome://flags'), 'may only open'),
            (('--', 'about:version'), 'may only open'),
        ]:
            result = self.run_rb('run', self.wt, *args, success=False)
            self.assertEqual(result.returncode, 2, (args, result.stderr))
            self.assertIn(why, result.stderr)
        self.assertEqual(self.calls(), '')

    def test_run_refuses_every_switch_off_the_allowlist(self):
        # After `--` only the allowlisted spellings pass; every other
        # switch — including the rest of the --rac-window-screenshot-*
        # family, single-dash forms and anything not spelled --foo=bar —
        # is refused with a pointer at the maintainer.
        for arg in (
            # The screenshot harness's own dangerous switches: a command
            # id it runs, foreground, unchecked output paths.
            '--rac-window-screenshot-command=40256',  # paste and go
            '--rac-window-screenshot-command=35006',  # email page location
            '--rac-window-screenshot-command=40004',  # DevTools
            '--rac-window-screenshot-command=40014',  # import settings
            '--rac-window-screenshot-command=35002',  # view source
            '--rac-window-screenshot-activate',
            '--rac-window-screenshot-requests=x.txt',
            '--rac-window-screenshot-requests',
            '--rac-window-screenshot-occlusion',
            # Driving, unsandboxing or reconfiguring the browser.
            '--remote-debugging-port=9222',
            '--remote-debugging-pipe',
            '--auto-open-devtools-for-tabs',
            '--allow-file-access-from-files',
            '--disable-web-security',
            '--no-sandbox',
            '--proxy-server=http://evil.com:8080',
            '--host-resolver-rules=MAP localhost 10.0.0.9',
            '--load-extension=ext',
            '--user-agent=x',
            '--js-flags=--expose-gc',
            '--enable-features=Foo',
            '--gpu-launcher=/bin/sh',
            '--utility-cmd-prefix=/bin/sh',
            '--app=file:///Users/k/.ssh/id_rsa',
            '--homepage=https://evil.com/',
            '--x=JavaScript:alert(1)',
            '--disk-cache-dir=/tmp/c',
            '--user-data-dir=/tmp/x',
            '-foo',
            '-rac-window-screenshot-requests=x.txt',
            '--RAC-WINDOW-SCREENSHOT-REQUESTS=x.txt',
            '--no-screenshot-run',
            '--rac-x=odd',
        ):
            result = self.run_rb('run', self.wt, '--', arg, success=False)
            self.assertEqual(result.returncode, 2, (arg, result.stderr))
            self.assertIn('ask Ship to allow it', result.stderr, arg)
        # The bare and two-token forms refuse too.
        for args in (('--', '--rac-window-screenshot-requests', 'x.txt'),
                     ('--', '--user-data-dir', '/tmp/x'),
                     ('--', '--host-resolver-rules', 'MAP localhost x')):
            result = self.run_rb('run', self.wt, *args, success=False)
            self.assertEqual(result.returncode, 2, (args, result.stderr))
            self.assertIn('ask Ship to allow it', result.stderr, args)
        self.assertEqual(self.calls(), '')

    def test_run_opens_allowed_url_args(self):
        self.run_rb('run', self.wt, '--timeout', '3', '--',
                    'http://localhost:8000/x', 'chrome://settings',
                    'chrome://version', 'about:blank', 'rac://rac-ai',
                    success=True)
        self.assertIn('http://localhost:8000/x chrome://settings', self.calls())

    def test_run_accepts_the_allowlisted_switches(self):
        write(self.clone / 'devutils/fixtures/arc/StorableSidebar.json', '{}\n')
        (self.clone / 'build/arc-root').mkdir(parents=True)
        self.run_rb('run', self.wt, '--timeout', '3', '--',
                    '--no-first-run', '--rac-launch-in-background',
                    '--rac-window-screenshot=x.png',
                    '--rac-window-screenshot-delay=1',
                    '--rac-window-screenshot-delay=9999',
                    '--rac-arc-import-fixture=devutils/fixtures/arc/StorableSidebar.json',
                    '--rac-import-source-root=build/arc-root',
                    success=True)
        calls = self.calls()
        for arg in ('--no-first-run', '--rac-window-screenshot-delay=1',
                    '--rac-window-screenshot-delay=9999'):
            self.assertIn(arg, calls, arg)

    def test_run_opening_chrome_setup_needs_an_import_input(self):
        # The Arc import screen would read the Pro's real Arc data, so a
        # run may open chrome://setup (requests file or URL arg) only
        # while also passing an import input.
        req = self.folder / 'req.txt'
        for line in ('open-urls chrome://setup', 'open-urls chrome://setup/a-1',
                     'open-urls rac://setup', 'open-urls chrome://version '
                     'chrome://setup'):
            write(req, line + '\n')
            result = self.run_rb('run', self.wt, '--requests-file', req,
                                 success=False)
            self.assertEqual(result.returncode, 2, line)
            self.assertIn('import', result.stderr, line)
        for arg in ('chrome://setup', 'chrome://setup/x-1', 'rac://setup',
                    'CHROME://SETUP'):
            result = self.run_rb('run', self.wt, '--', arg, success=False)
            self.assertEqual(result.returncode, 2, arg)
            self.assertIn('import', result.stderr, arg)
        self.assertEqual(self.calls(), '')
        # With either import input the setup page runs; other pages and
        # other pairs need no input.
        write(self.clone / 'devutils/fixtures/arc/StorableSidebar.json', '{}\n')
        (self.clone / 'build/arc-root').mkdir(parents=True)
        write(req, 'open-urls chrome://setup\n')
        self.run_rb('run', self.wt, '--requests-file', req, '--timeout', '3',
                    '--', '--rac-arc-import-fixture=devutils/fixtures/arc/StorableSidebar.json',
                    success=True)
        self.run_rb('run', self.wt, '--timeout', '3', '--', 'chrome://setup',
                    '--rac-import-source-root=build/arc-root', success=True)
        write(req, 'open-urls chrome://version\n')
        self.run_rb('run', self.wt, '--requests-file', req, '--timeout', '3',
                    success=True)
        # The pages lines never reach the Pro's path list.
        written = (self.clone / 'build/req/req.txt').read_text()
        self.assertNotIn('pages', written)

    def test_run_import_arc_now_needs_a_source_root(self):
        # Without --rac-import-source-root the dev import reads the Pro's
        # real Arc, and an Arc fixture file is not a source root.
        write(self.clone / 'devutils/fixtures/arc/StorableSidebar.json', '{}\n')
        (self.clone / 'build/arc-root').mkdir(parents=True)
        for extra in ([], ['--rac-arc-import-fixture=devutils/fixtures/arc/StorableSidebar.json']):
            result = self.run_rb('run', self.wt, '--', '--no-first-run',
                                 '--rac-import-arc-now', *extra, success=False)
            self.assertEqual(result.returncode, 2, extra)
            self.assertIn('real Arc', result.stderr, extra)
        for bad in ('--rac-import-arc-now=1', '--rac-import-arc-now=',
                    '-rac-import-arc-now', '--RAC-IMPORT-ARC-NOW'):
            result = self.run_rb('run', self.wt, '--',
                                 '--rac-import-source-root=build/arc-root', bad,
                                 success=False)
            self.assertEqual(result.returncode, 2, bad)
        self.assertEqual(self.calls(), '')
        self.run_rb('run', self.wt, '--timeout', '3', '--', '--no-first-run',
                    '--rac-import-source-root=build/arc-root',
                    '--rac-import-arc-now', success=True)
        self.assertIn('--rac-import-arc-now', self.calls())

    def test_run_refuses_a_malformed_allowed_hosts_list(self):
        req = self.folder / 'req.txt'
        write(req, 'key tab\n')
        result = self.run_rb('run', self.wt, '--requests-file', req,
                             success=False, RAC_REMOTE_ALLOWED_HOSTS='evil.com/x')
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn('RAC_REMOTE_ALLOWED_HOSTS', result.stderr)
        self.assertEqual(self.calls(), '')

    def test_run_screenshots_and_stops_the_clone(self):
        shot = self.clone / 'build/shots/x.png'
        app = f'{self.clone}/build/src/out/Default/rac.app/'
        # A process from another app must survive, and so must a browser
        # from this clone that this run did not launch.
        survivor = subprocess.Popen(['sleep', '300'])
        rogue = subprocess.Popen(
            ['bash', '-c', 'exec -a "$1" sleep 300', '_',
             f'{app}Contents/MacOS/rac Helper'])
        self.addCleanup(lambda: (survivor.kill(), survivor.wait()))
        self.addCleanup(lambda: (rogue.kill(), rogue.wait()))
        time.sleep(0.3)
        started = time.monotonic()
        result = self.run_rb('run', self.wt, '--timeout', '60', '--',
                             '--rac-window-screenshot=x.png', success=True)
        # The shot ends the wait well before the run's timeout.
        self.assertLess(time.monotonic() - started, 60)
        self.assertTrue(shot.exists())
        self.assertIn(str(shot), result.stderr)
        # The browser this run launched is gone; both outsiders live.
        self.assertEqual(self.procs_starting(app), [rogue.pid])
        survivor.poll()
        self.assertIsNone(survivor.returncode)
        self.assertIsNone(rogue.poll())

    def test_run_writes_a_checked_requests_file(self):
        # The line's paths are relative on the Air and land, absolute, in the
        # clone's build/shots on the Pro; the browser gets the file's path.
        req = self.folder / 'req.txt'
        write(req, 'after 500 nspress t cmd ; after 900 nstype quokka ; '
                   'after 1500 bar/first.png ; burst frames 3 100\n')
        shot = self.clone / 'build/shots/x.png'
        self.run_rb('run', self.wt, '--timeout', '30', '--requests-file', req,
                    '--', '--rac-window-screenshot=x.png', success=True)
        written = (self.clone / 'build/req/req.txt').read_text()
        shots = f'{os.path.realpath(self.clone)}/build/shots'
        self.assertIn(f'after 1500 {shots}/bar/first.png', written)
        self.assertIn(f'burst {shots}/frames 3 100', written)
        self.assertIn('nstype quokka', written)
        self.assertNotIn('@SHOTS@', written)
        self.assertTrue((self.clone / 'build/shots/bar').is_dir())
        # The harness writes a burst's frames into DIR without making it.
        self.assertTrue((self.clone / 'build/shots/frames').is_dir())
        self.assertIn(f'--rac-window-screenshot-requests={os.path.realpath(self.clone)}'
                      '/build/req/req.txt', self.log.read_text())
        self.assertTrue(shot.exists())

    def test_run_refuses_a_verb_the_clone_harness_lacks(self):
        # The Air's table can't know what this clone built: a verb absent
        # from the clone's harness sources would run as an output path
        # inside `after`, so the Pro refuses it before writing req.txt.
        self.seed_harness(without=('nspress',))
        req = self.folder / 'req.txt'
        write(req, 'after 5 nspress t cmd ; capture-window first x.png\n')
        result = self.run_rb('run', self.wt, '--requests-file', req, success=False)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn('nspress', result.stderr)
        self.assertFalse((self.clone / 'build/req/req.txt').exists())
        # With the verb in the clone's harness sources the same line runs.
        self.seed_harness()
        self.run_rb('run', self.wt, '--requests-file', req, success=True)

    def test_run_confines_downloads_to_the_clone(self):
        # A URL the harness opens can start a download; before the browser
        # launches, its profile Preferences must send downloads inside the
        # clone — never the Pro's own Downloads folder.
        prefs = self.clone / 'build/profile/Default/Preferences'
        write(prefs, '{"ui": {"scale": 2},'
                    ' "download": {"other": 1, "prompt_for_download": true}}\n')
        self.run_rb('run', self.wt, '--timeout', '3', success=True)
        data = json.loads(prefs.read_text())
        downloads = str(os.path.realpath(self.clone / 'build/downloads'))
        self.assertEqual(data['download']['default_directory'], downloads)
        self.assertEqual(data['download']['prompt_for_download'], False)
        self.assertEqual(data['download']['directory_upgrade'], True)
        self.assertEqual(data['savefile']['default_directory'], downloads)
        self.assertEqual(data['selectfile']['last_directory'], downloads)
        # No open, save or upload dialog can be walked to the Pro's files.
        state = json.loads((self.clone / 'build/profile/Local State').read_text())
        self.assertEqual(state['select_file_dialogs']['allowed'], False)
        # Every unrelated preference survives.
        self.assertEqual(data['download']['other'], 1)
        self.assertEqual(data['ui']['scale'], 2)
        self.assertTrue((self.clone / 'build/downloads').is_dir())
        self.assertFalse((self.remote / 'Downloads').exists())

    def test_run_patches_preferences_for_a_fresh_profile(self):
        prefs = self.clone / 'build/profile/Default/Preferences'
        write(prefs, '{"ui": {"scale": 2}}\n')
        self.run_rb('run', self.wt, '--timeout', '3', '--fresh-profile',
                    success=True)
        data = json.loads(prefs.read_text())
        downloads = str(os.path.realpath(self.clone / 'build/downloads'))
        self.assertEqual(data['download']['default_directory'], downloads)
        self.assertEqual(data['savefile']['default_directory'], downloads)

    def test_run_refuses_a_symlinked_preferences(self):
        prefs = self.clone / 'build/profile/Default/Preferences'
        write(prefs, '{}')
        target = self.folder / 'outside-prefs.json'
        write(target, '{"keep": true}')
        prefs.unlink()
        prefs.symlink_to(target)
        result = self.run_rb('run', self.wt, '--timeout', '3', success=False)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn('symlink', result.stderr)
        self.assertEqual(target.read_text(), '{"keep": true}')
        self.assertFalse((self.remote / 'Downloads').exists())

    def test_run_keeps_local_state_and_refuses_a_symlinked_one(self):
        state = self.clone / 'build/profile/Local State'
        write(state, '{"browser": {"x": 1}, "select_file_dialogs": 5}')
        self.run_rb('run', self.wt, '--timeout', '3', success=True)
        data = json.loads(state.read_text())
        self.assertEqual(data['browser'], {'x': 1})
        self.assertEqual(data['select_file_dialogs'], {'allowed': False})
        target = self.folder / 'outside-state.json'
        write(target, '{"keep": true}')
        state.unlink()
        state.symlink_to(target)
        result = self.run_rb('run', self.wt, '--timeout', '3', success=False)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn('symlink', result.stderr)
        self.assertEqual(target.read_text(), '{"keep": true}')

    def test_run_writes_prefs_through_no_planted_tmp_link(self):
        target = self.folder / 'outside-tmp.json'
        write(target, 'keep')
        prefs = self.clone / 'build/profile/Default/Preferences'
        write(prefs, '{}')
        (self.clone / 'build/profile/Default/Preferences.tmp').symlink_to(target)
        self.run_rb('run', self.wt, '--timeout', '3', success=True)
        self.assertEqual(target.read_text(), 'keep')
        self.assertFalse(prefs.is_symlink())
        self.assertIn('default_directory', prefs.read_text())

    def test_run_refuses_a_symlinked_downloads_dir(self):
        outside = self.folder / 'outside-downloads'
        outside.mkdir()
        (self.clone / 'build').mkdir(exist_ok=True)
        (self.clone / 'build/downloads').symlink_to(outside)
        result = self.run_rb('run', self.wt, '--timeout', '3', success=False)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn('symlink', result.stderr)

    def test_run_skips_the_prefs_patch_while_a_clone_browser_runs(self):
        # A running browser read its profile's Preferences at startup and
        # rewrites them on exit — patching them now would be lost anyway.
        app = f'{self.clone}/build/src/out/Default/rac.app/'
        rogue = subprocess.Popen(
            ['bash', '-c', 'exec -a "$1" sleep 60', '_',
             f'{app}Contents/MacOS/rac'])
        self.addCleanup(lambda: (rogue.kill(), rogue.wait()))
        time.sleep(0.3)
        prefs = self.clone / 'build/profile/Default/Preferences'
        write(prefs, '{"keep": true}')
        self.run_rb('run', self.wt, '--timeout', '3', success=True)
        self.assertEqual(prefs.read_text(), '{"keep": true}')
        # That browser polls the same req.txt: a requests run would hand it
        # the line under settings this run never saw, so it is refused.
        req = self.folder / 'req.txt'
        write(req, 'key tab\n')
        result = self.run_rb('run', self.wt, '--requests-file', req, success=False)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn('a browser from this clone is running', result.stderr)
        self.assertFalse((self.clone / 'build/req/req.txt').exists())

    def test_run_refuses_unsafe_requests_files(self):
        for line in ('/tmp/x.png', '../x.png', '~/x.png', 'burst /tmp 3 100',
                     'capture-window app /tmp/a.png', 'open-urls file:///etc/hosts',
                     'key ../x.json', 'a.png\nb.png', '@SHOTS@/x.png',
                     'record /tmp 500', 'after 5 unknown'):
            req = self.folder / 'bad.txt'
            write(req, line + '\n')
            result = self.run_rb('run', self.wt, '--requests-file', req, success=False)
            self.assertEqual(result.returncode, 2, line)
            self.assertIn('requests file', result.stderr, line)
        # Refused on the Air: nothing reached the Pro.
        self.assertNotIn('worktree.sh run', self.log.read_text() if self.log.exists() else '')

    def test_run_refuses_a_symlinked_requests_dir(self):
        outside = self.folder / 'outside'
        outside.mkdir()
        (self.clone / 'build').mkdir(exist_ok=True)
        (self.clone / 'build/req').symlink_to(outside)
        req = self.folder / 'req.txt'
        write(req, 'x.png\n')
        result = self.run_rb('run', self.wt, '--requests-file', req, success=False)
        self.assertEqual(result.returncode, 2)
        self.assertFalse((outside / 'req.txt').exists())

    def test_run_waits_for_every_requested_shot(self):
        # The harness reads requests only after the first shot; the run
        # must not end on that shot while the requested ones are pending.
        req = self.folder / 'req.txt'
        write(req, 'after 500 a.png ; burst frames 3 100 ; '
                   'capture-window first win.png\n')
        shots = self.clone / 'build/shots'
        for stale in ('a.png', 'frames/f00.png', 'win.png'):
            write(shots / stale, 'old\n')
        started = time.monotonic()
        result = self.run_rb('run', self.wt, '--timeout', '30', '--requests-file', req,
                             '--', '--rac-window-screenshot=x.png', success=True,
                             REQ_DELAY='5')
        self.assertGreaterEqual(time.monotonic() - started, 5, result.stderr)
        self.assertLess(time.monotonic() - started, 30, result.stderr)
        for name in ('x.png', 'a.png', 'frames/f00.png', 'frames/f01.png',
                     'frames/f02.png', 'win.png'):
            self.assertEqual((shots / name).read_text(), 'png\n', name)

    def test_run_names_requested_shots_missing_at_the_timeout(self):
        req = self.folder / 'req.txt'
        write(req, 'after 0 a.png ; burst frames 3 100\n')
        result = self.run_rb('run', self.wt, '--timeout', '6', '--requests-file', req,
                             '--', '--rac-window-screenshot=x.png', success=False,
                             REQ_SKIP='f02.png')
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn('still no', result.stderr)
        self.assertIn('build/shots/frames/f02.png', result.stderr)
        self.assertNotIn('f01.png', result.stderr)

    def test_run_never_globs_typed_text(self):
        # Typed text reaches the Pro inside the line; a `*` in it must not
        # expand to the clone's files, and nothing it names is touched.
        keep = self.clone / 'build/shots/keep.png'
        write(keep, 'old\n')
        req = self.folder / 'req.txt'
        write(req, 'type *.png * build shots\n')
        self.run_rb('run', self.wt, '--timeout', '3', '--requests-file', req,
                    success=True)
        self.assertTrue(keep.exists())
        written = (self.clone / 'build/req/req.txt').read_text()
        self.assertIn('type *.png * build shots', written)

    def test_run_writes_the_requests_file_through_no_symlink(self):
        # A planted req.txt.tmp or req.txt symlink must not redirect the
        # write or the rename out of the clone.
        outside = self.folder / 'outside'
        outside.mkdir()
        target = outside / 'victim.txt'
        write(target, 'keep\n')
        reqdir = self.clone / 'build/req'
        reqdir.mkdir(parents=True)
        (reqdir / 'req.txt.tmp').symlink_to(target)
        (reqdir / 'req.txt').symlink_to(outside)
        req = self.folder / 'req.txt'
        write(req, 'x.png\n')
        self.run_rb('run', self.wt, '--timeout', '3', '--requests-file', req,
                    success=True)
        self.assertEqual(target.read_text(), 'keep\n')
        self.assertEqual(sorted(p.name for p in outside.iterdir()), ['victim.txt'])
        self.assertFalse((reqdir / 'req.txt').is_symlink())

    def test_run_refuses_requests_for_a_clone_path_with_spaces(self):
        # The harness splits the line on spaces, so a shots path with one
        # would reach the browser as two words.
        self.remote_clone('odd')
        spaced = self.remote / 'rac-remote/wt/sp ace'
        spaced.mkdir()
        (self.remote / 'rac-remote/wt/odd').rename(spaced / 'odd')
        (self.remote / 'rac-remote/wt/odd').symlink_to(spaced / 'odd')
        wt = self.make_repo(self.folder / 'odd', branch='feat/odd')
        req = self.folder / 'req.txt'
        write(req, 'x.png\n')
        result = self.run_rb('run', wt, '--timeout', '3', '--requests-file', req,
                             success=False)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn('without spaces', result.stderr)
        self.assertFalse((spaced / 'odd/build/req/req.txt').exists())

    def test_run_maps_arc_import_inputs_into_the_clone(self):
        write(self.clone / 'devutils/fixtures/arc/StorableSidebar.json', '{}\n')
        (self.clone / 'build/arc-root').mkdir(parents=True)
        self.run_rb('run', self.wt, '--timeout', '3', '--',
                    '--rac-arc-import-fixture=devutils/fixtures/arc/StorableSidebar.json',
                    '--rac-import-source-root=build/arc-root', success=True)
        clone = os.path.realpath(self.clone)
        calls = self.calls()
        self.assertIn('--rac-arc-import-fixture='
                      f'{clone}/devutils/fixtures/arc/StorableSidebar.json', calls)
        self.assertIn(f'--rac-import-source-root={clone}/build/arc-root', calls)

    def test_run_refuses_arc_import_inputs_outside_the_clone(self):
        outside = self.folder / 'outside'
        outside.mkdir()
        write(outside / 'StorableSidebar.json', '{}\n')
        (self.clone / 'escape').symlink_to(outside)
        for args, why in [
            (('--rac-arc-import-fixture=escape/StorableSidebar.json',), 'leaves the clone'),
            (('--rac-import-source-root=escape',), 'leaves the clone'),
            (('--rac-arc-import-fixture=missing.json',), 'no '),
            (('--rac-import-source-root=build/none',), 'no '),
            (('--rac-import-source-root=',), 'needs a path'),
        ]:
            result = self.run_rb('run', self.wt, '--timeout', '3', '--', *args,
                                 success=False)
            self.assertEqual(result.returncode, 2, (args, result.stderr))
            self.assertIn(why, result.stderr, args)
        self.assertNotIn('worktree.sh run', self.calls())
        # Inputs are only read: nothing was made for the missing ones.
        self.assertFalse((self.clone / 'build/none').exists())
        # On the Air, absolute, ~ and .. values stay refused.
        for value in ('/tmp/x.json', '~/x.json', '../x.json'):
            result = self.run_rb('run', self.wt, '--',
                                 f'--rac-arc-import-fixture={value}', success=False)
            self.assertEqual(result.returncode, 2, value)

    def test_run_fresh_profile_deletes_only_the_clones_profile(self):
        # Data's import test: a clean profile and a source root in the clone.
        write(self.clone / 'build/profile/Default/Preferences', '{}\n')
        keep = self.clone / 'build/shots/keep.png'
        write(keep, 'old\n')
        sample = 'build/src/chrome/test/data/rac/import/arc/maintainer_sample'
        (self.clone / sample).mkdir(parents=True)
        result = self.run_rb('run', self.wt, '--timeout', '3', '--fresh-profile',
                             '--', f'--rac-import-source-root={sample}', success=True)
        # The run then points a fresh profile's downloads inside the clone
        # and turns its file dialogs off.
        self.assertEqual(
            sorted(str(p.relative_to(self.clone / 'build/profile'))
                   for p in (self.clone / 'build/profile').rglob('*')),
            ['Default', 'Default/Preferences', 'Local State'], result.stderr)
        self.assertTrue(keep.exists())
        self.assertIn(f'--rac-import-source-root={os.path.realpath(self.clone)}/{sample}',
                      self.calls())

    def test_run_fresh_profile_refuses_a_symlinked_profile(self):
        outside = self.folder / 'outside'
        write(outside / 'Default/Preferences', 'keep\n')
        (self.clone / 'build').mkdir(exist_ok=True)
        (self.clone / 'build/profile').symlink_to(outside)
        result = self.run_rb('run', self.wt, '--timeout', '3', '--fresh-profile',
                             success=False)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn('symlink', result.stderr)
        self.assertEqual((outside / 'Default/Preferences').read_text(), 'keep\n')
        self.assertTrue((self.clone / 'build/profile').is_symlink())
        self.assertNotIn('worktree.sh run', self.calls())

    def test_run_fresh_profile_refuses_a_symlinked_build_dir(self):
        outside = self.folder / 'outside'
        write(outside / 'profile/Default/Preferences', 'keep\n')
        shutil.rmtree(self.clone / 'build')
        (self.clone / 'build').symlink_to(outside)
        result = self.run_rb('run', self.wt, '--timeout', '3', '--fresh-profile',
                             success=False)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertTrue((outside / 'profile/Default/Preferences').exists())

    def test_run_fresh_profile_refuses_while_a_clone_browser_runs(self):
        write(self.clone / 'build/profile/Default/Preferences', '{}\n')
        app = f'{self.clone}/build/src/out/Default/rac.app/'
        running = subprocess.Popen(
            ['bash', '-c', 'exec -a "$1" sleep 300', '_', f'{app}Contents/MacOS/rac'])
        self.addCleanup(lambda: (running.kill(), running.wait()))
        time.sleep(0.3)
        result = self.run_rb('run', self.wt, '--timeout', '3', '--fresh-profile',
                             success=False)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn('is running', result.stderr)
        self.assertTrue((self.clone / 'build/profile/Default/Preferences').exists())
        self.assertIsNone(running.poll())

    def test_run_ignores_a_stale_screenshot(self):
        # An earlier run's shot must not end the wait before the new one.
        write(self.clone / 'build/shots/x.png', 'old\n')
        result = self.run_rb('run', self.wt, '--', '--rac-window-screenshot=x.png',
                             success=True, SHOT_DELAY='4')
        self.assertEqual((self.clone / 'build/shots/x.png').read_text(), 'png\n')

    def test_run_passes_odd_args_through_intact(self):
        # An allowed URL holding shell metacharacters reaches the Pro's
        # browser verbatim, through ssh and the Pro's own shell.
        odd = "http://localhost:8000/it's$HOME`id`*;x"
        self.run_rb('run', self.wt, '--timeout', '4', '--', odd, success=True)
        self.assertIn(odd, self.calls())

    def test_run_arg_paths_are_plain_names(self):
        # Path values take the requests file's characters only, and a
        # screenshot ends in .png.
        for arg, why in [
            ("--rac-window-screenshot=it's $HOME `id` *.png", 'may only use'),
            ('--rac-window-screenshot=a.png --rac-window-screenshot-command=40256',
             'may only use'),
            ('--rac-window-screenshot=a\nb.png', 'may only use'),
            ('--rac-window-screenshot=x.txt', 'ends in .png'),
            ('--rac-import-source-root=build/a b', 'may only use'),
        ]:
            result = self.run_rb('run', self.wt, '--', arg, success=False)
            self.assertIn(why, result.stderr, arg)

    def test_run_timeout_stops_the_browser(self):
        result = self.run_rb('run', self.wt, '--timeout', '4', '--',
                             '--no-first-run', success=True)
        self.assertIn('queue', self.calls())

    def test_run_refuses_a_symlinked_shots_dir(self):
        # build/shots -> outside the clone would write the PNG anywhere.
        outside = self.folder / 'outside'
        outside.mkdir()
        (self.clone / 'build').mkdir(exist_ok=True)
        (self.clone / 'build/shots').symlink_to(outside)
        result = self.run_rb('run', self.wt, '--timeout', '5', '--',
                             '--rac-window-screenshot=x.png', success=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn('symlink', result.stderr)
        self.assertFalse((outside / 'x.png').exists())

    def test_run_refuses_a_symlinked_build_dir_before_creating_anything(self):
        # build -> outside: the refusal has to come before mkdir, or mkdir
        # makes build/shots outside the clone first.
        outside = self.folder / 'outside'
        outside.mkdir()
        shutil.rmtree(self.clone / 'build')
        (self.clone / 'build').symlink_to(outside)
        result = self.run_rb('run', self.wt, '--timeout', '5', '--',
                             '--rac-window-screenshot=x.png', success=False)
        self.assertEqual(result.returncode, 2)
        self.assertFalse((outside / 'shots').exists())

    def test_run_refuses_a_symlink_under_shots(self):
        # A symlinked dir inside build/shots escapes the same way.
        outside = self.folder / 'outside'
        outside.mkdir()
        shots = self.clone / 'build/shots'
        shots.mkdir(parents=True)
        (shots / 'escape').symlink_to(outside)
        result = self.run_rb('run', self.wt, '--timeout', '5', '--',
                             '--rac-window-screenshot=escape/x.png', success=False)
        self.assertEqual(result.returncode, 2)
        self.assertFalse((outside / 'x.png').exists())

    def test_run_timeout_starts_at_slot_grant(self):
        # The queue makes the run wait before granting its slot; the
        # browser still gets its full timeout afterwards.
        started = time.monotonic()
        self.run_rb('run', self.wt, '--timeout', '4', '--',
                    '--no-first-run', success=True, QUEUE_DELAY='5')
        self.assertGreaterEqual(time.monotonic() - started, 8)

    def test_run_refuses_on_toolchain_drift(self):
        write(self.remote_root / 'base/.rac-toolchain',
              'xcode_build 16F6\nsdk 26.0\n')
        self.remote_xcode_build.write_text('16F99\n')
        result = self.run_rb('run', self.wt, '--timeout', '3', success=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn('changed since the base was built', result.stderr)
        self.assertIn('16F99', result.stderr)

    def test_run_fails_when_never_launched(self):
        result = self.run_rb('run', self.wt, '--timeout', '3', success=False,
                             NEVER_LAUNCH='600', RAC_REMOTE_QUEUE_WAIT='2')
        self.assertIn('never launched', result.stderr)

    def test_run_stops_only_the_browser_it_started(self):
        app = f'{self.clone}/build/src/out/Default/rac.app/'
        env = self.env()
        a = subprocess.Popen(['/bin/bash', SCRIPT, 'run', str(self.wt),
                              '--timeout', '8', '--', '--no-first-run'],
                             env=env, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, text=True)
        try:
            a_pids = self.wait_for(lambda: self.procs_starting(app))
            b = subprocess.Popen(['/bin/bash', SCRIPT, 'run', str(self.wt),
                                  '--timeout', '120', '--', '--no-first-run'],
                                 env=env, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, text=True,
                                 start_new_session=True)
            try:
                b_pid = self.wait_for(
                    lambda: [p for p in self.procs_starting(app)
                             if p not in a_pids])[0]
                out, err = a.communicate(timeout=40)
                self.assertEqual(a.returncode, 0, err)
                # A's stop took only its own browser; B's still runs.
                self.assertEqual(self.procs_starting(app), [b_pid])
            finally:
                if b.poll() is None:
                    os.killpg(b.pid, signal.SIGTERM)
                b.communicate(timeout=30)
            # Stopping B's run ended B's browser, nothing else's.
            self.wait_for(lambda: self.procs_starting(app) == [])
        finally:
            if a.poll() is None:
                a.kill()
                a.communicate()


@unittest.skipUnless(sys.platform == 'darwin',
                    'remote-build.sh drives macOS hosts')
class PullTest(RemoteBuildTest):

    def setUp(self):
        super().setUp()
        self.remote_root = self.seed_remote()
        self.remote_clone('feature')
        self.wt = self.make_repo(self.folder / 'feature', branch='feat/x')

    def test_pull_copies_back(self):
        remote_file = self.remote_root / 'wt/feature/build/shots/shot.png'
        write(remote_file, 'png\n')
        dest = self.folder / 'out/shot.png'
        self.run_rb('pull', self.wt, 'build/shots/shot.png', dest, success=True)
        self.assertEqual(dest.read_text(), 'png\n')
        self.assertIn(f'rsync -e ssh -o BatchMode=yes -o ConnectTimeout=15 '
                      f'-a --partial --info=progress2 '
                      f'fake-host:rac-remote/wt/feature/'
                      f'build/shots/shot.png {dest}', self.calls())

    def test_pull_refuses_profile_paths(self):
        result = self.run_rb('pull', self.wt, '../../Library/Application Support/x',
                             self.folder / 'x', success=False)
        self.assertEqual(result.returncode, 2)
        for rel in ('', '.', '/etc/x', 'a;b', 'a b', 'build/../../x'):
            result = self.run_rb('pull', self.wt, rel, self.folder / 'x', success=False)
            self.assertEqual(result.returncode, 2, rel)
        self.assertEqual(self.calls(), '')

    def test_pull_refuses_a_symlinked_source(self):
        # A symlink inside the clone pointing outside stays refused even
        # though the path itself looks fine.
        secret = self.folder / 'secret.txt'
        write(secret, 'key\n')
        shots = self.remote_root / 'wt/feature/build/shots'
        shots.mkdir(parents=True)
        (shots / 'leak.txt').symlink_to(secret)
        dest = self.folder / 'leak.txt'
        result = self.run_rb('pull', self.wt, 'build/shots/leak.txt', dest,
                             success=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn('symlink', result.stderr)
        self.assertFalse(dest.exists())

    def test_pull_refuses_a_symlinked_dir(self):
        # A symlinked directory on the way escapes the clone too.
        outside = self.folder / 'outside'
        write(outside / 'real.png', 'png\n')
        build = self.remote_root / 'wt/feature/build'
        build.mkdir(parents=True)
        (build / 'shots').symlink_to(outside)
        dest = self.folder / 'real.png'
        result = self.run_rb('pull', self.wt, 'build/shots/real.png', dest,
                             success=False)
        self.assertEqual(result.returncode, 2)
        self.assertFalse(dest.exists())


@unittest.skipUnless(sys.platform == 'darwin',
                    'remote-build.sh drives macOS hosts')
class RemotePathTest(RemoteBuildTest):
    """A non-interactive ssh has no Homebrew on PATH, so every remote
    command must prepend it. The fake ssh logs the command it was handed;
    the tests point RAC_REMOTE_PATH_PREFIX at a stub bin under the fake
    remote home."""

    def setUp(self):
        super().setUp()
        self.remote_root = self.seed_remote()
        queue = self.remote_root / 'base/devutils/rac/build-queue.sh'
        write(queue, '#!/bin/bash\necho "queue status here"\n')
        queue.chmod(0o755)
        self.wt = self.make_repo(self.folder / 'feature', branch='feat/x')

    def test_every_remote_command_gets_the_path_prefix(self):
        # push creates wt/feature from the pushed branch; the clone then
        # serves the build and run commands.
        for args in (['setup-host'], ['push', self.wt], ['status']):
            self.log.unlink(missing_ok=True)
            self.run_rb(*[str(a) for a in args], success=True)
            self.assertIn(f'ssh PATH={self.brew_bin}:', self.calls())
        clone = self.remote_root / 'wt/feature'
        write(clone / 'build/src/third_party/depot_tools/autoninja.py',
              STUB_AUTONINJA)
        for args in (['build', self.wt], ['run', self.wt, '--timeout', '3']):
            self.log.unlink(missing_ok=True)
            self.run_rb(*[str(a) for a in args], success=True)
            self.assertIn(f'ssh PATH={self.brew_bin}:', self.calls())
        # With the variable unset the built-in Homebrew prefix is used.
        result = self.run_rb('--dry-run', 'status', success=True,
                             RAC_REMOTE_PATH_PREFIX=None)
        self.assertIn('PATH=/opt/homebrew/bin:/opt/homebrew/sbin:',
                      result.stderr)

    def test_prefix_makes_brew_tools_visible(self):
        # With the prefix pointed at an empty dir, quilt and greadlink are
        # missing on a stock PATH and setup-host refuses (as before).
        result = self.run_rb('setup-host', success=False,
                             RAC_FAKE_PATH='/usr/bin:/bin', DF_AVAILABLE='80')
        self.assertIn('quilt', result.stderr)
        # Add the tools inside the prefix dir and the same check passes.
        for name in ('quilt', 'greadlink'):
            tool(self.brew_bin / name, 'exit 0\n')
        result = self.run_rb('setup-host', success=True,
                             RAC_FAKE_PATH='/usr/bin:/bin', DF_AVAILABLE='80')
        self.assertIn('ready', result.stdout)

    def test_ssh_uses_connect_timeout(self):
        # A dead Pro must fail fast, not hang on the default TCP timeout —
        # every ssh and the rsync's -e both get ConnectTimeout.
        self.run_rb('status', success=True)
        self.assertIn('ssh-argv -o BatchMode=yes -o ConnectTimeout=15',
                      self.calls())


@unittest.skipUnless(sys.platform == 'darwin',
                    'remote-build.sh drives macOS hosts')
class RsyncFlavorTest(RemoteBuildTest):
    """The local rsync flavour picks the flags: GNU rsync gets
    --info=progress2, macOS's openrsync (protocol 29) gets --stats, never
    a per-file --progress across ~500k files."""

    def setUp(self):
        super().setUp()
        self.remote_root = self.seed_remote()
        self.remote_clone('feature')
        self.wt = self.make_repo(self.folder / 'feature', branch='feat/x')
        write(self.remote_root / 'wt/feature/build/shots/x.png', 'png\n')

    def test_gnu_rsync_gets_progress2(self):
        dest = self.folder / 'x.png'
        self.run_rb('pull', self.wt, 'build/shots/x.png', dest, success=True)
        self.assertIn('-a --partial --info=progress2', self.calls())

    def test_openrsync_gets_stats_instead(self):
        dest = self.folder / 'x.png'
        self.run_rb('pull', self.wt, 'build/shots/x.png', dest, success=True,
                    RSYNC_VERSION_LINE='openrsync: protocol version 29')
        calls = self.calls()
        self.assertIn('-a --partial --stats', calls)
        self.assertNotIn('progress', calls.replace('partial', ''))


@unittest.skipUnless(sys.platform == 'darwin',
                    'remote-build.sh drives macOS hosts')
class StatusTest(RemoteBuildTest):

    def test_status(self):
        root = self.seed_remote()
        write(root / 'base/devutils/rac/build-queue.sh',
              '#!/bin/bash\necho "queue status here"\n')
        (root / 'base/devutils/rac/build-queue.sh').chmod(0o755)
        result = self.run_rb('status', success=True)
        self.assertIn('load average', result.stdout)
        self.assertIn('free disk under', result.stdout)
        self.assertIn('queue status here', result.stdout)


@unittest.skipUnless(sys.platform == 'darwin',
                    'remote-build.sh drives macOS hosts')
class DryRunTest(RemoteBuildTest):

    def setUp(self):
        super().setUp()
        self.remote_root = self.seed_remote()
        self.remote_clone('feature')
        self.wt = self.make_repo(self.folder / 'feature', branch='feat/x')

    def test_dry_run_prints_without_acting(self):
        before = self.calls()
        result = self.run_rb('--dry-run', 'build', self.wt, success=True)
        self.assertIn('ssh', result.stderr)
        self.assertIn('local_jobs', result.stderr)
        self.assertEqual(self.calls(), before)
        # pull prints the rsync it would run, and copies nothing.
        dest = self.folder / 'shot.png'
        result = self.run_rb('--dry-run', 'pull', self.wt, 'build/shots/x.png', dest,
                             success=True)
        self.assertIn('rsync', result.stderr)
        self.assertIn('rac-remote/wt/feature/build/shots/x.png', result.stderr)
        self.assertFalse(dest.exists())
        # push prints its pushes but sends nothing.
        wt = self.make_repo(self.folder / 'sync-wt', branch='main')
        result = self.run_rb('--dry-run', 'push', wt, success=True)
        self.assertIn('push --force', result.stderr)
        self.assertFalse((self.remote_root / 'wt/sync-wt').exists())

if __name__ == '__main__':
    unittest.main()
