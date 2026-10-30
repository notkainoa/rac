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
import os
import shutil
import subprocess
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
if [ -n "${DF_AVAILABLE:-}" ]; then
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
if [ "$1" = "run" ]; then
  shot=
  for arg in "$@"; do
    case "$arg" in --rac-window-screenshot=*) shot="${arg#--rac-window-screenshot=}" ;; esac
  done
  if [ -n "$shot" ]; then
    mkdir -p "$(dirname "$shot")"
    sleep "${SHOT_DELAY:-1}"
    echo png > "$shot"
  fi
  # Stand in for the browser: a sleeper titled with this clone's app path
  # so the run command's pgrep finds it and nothing else.
  exec bash -c 'exec -a "$1" sleep 600' _ \
    "$PWD/build/src/out/Default/rac.app/Contents/MacOS/rac"
fi
'''
STUB_QUEUE_SH = '''\
echo "queue $*" >> "$RAC_FAKE_LOG"
[ -z "${QUEUE_EXIT:-}" ] || exit "$QUEUE_EXIT"
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
STUB_AUTONINJA = '''\
import sys
print('autoninja ' + ' '.join(sys.argv[1:]))
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

    def make_repo(self, path, branch='main'):
        """A git checkout holding stubs for what the remote side runs."""
        path.mkdir(parents=True)
        git(path, 'init', '-q', '-b', branch)
        write(path / 'devutils/rac/worktree.sh', '#!/bin/bash\n' + STUB_WORKTREE_SH)
        write(path / 'devutils/rac/build-queue.sh', '#!/bin/bash\n' + STUB_QUEUE_SH)
        write(path / 'devutils/update_patches.sh', '#!/bin/bash\n' + STUB_UPDATE_PATCHES)
        write(path / 'devutils/rac/dev_names.py', 'pass\n')
        write(path / 'devutils/rac/rac_version.py', 'pass\n')
        shutil.copy2(HERE / 'worktree_state.py', path / 'devutils/rac/worktree_state.py')
        write(path / 'patches/series', 'a.patch\n')
        write(path / 'patches/a.patch', '--- a/one\n+++ b/one\n@@ -1 +1 @@\n-base\n+saved\n')
        write(path / 'file.txt', 'base\n')
        for script in path.rglob('*.sh'):
            script.chmod(0o755)
        git(path, 'add', '-A')
        git(path, 'commit', '-qm', 'fixture')
        return path

    def seed_remote(self):
        """The layout setup-host leaves: the bare repos and a base clone."""
        root = self.remote / 'rac-remote'
        root.mkdir(parents=True, exist_ok=True)
        for repo in ('rac.git', 'helium-chromium.git'):
            git(root, 'init', '-q', '--bare', root / repo)
        subprocess.run(['git', 'clone', '-q', 'rac.git', 'base'],
                       cwd=root, capture_output=True)
        return root

    def remote_clone(self, name='feature'):
        """A clone on the remote, as push would leave it."""
        clone = self.remote / 'rac-remote/wt' / name
        src = self.make_repo(self.folder / f'remote-src-{name}')
        shutil.copytree(src, clone, ignore=shutil.ignore_patterns('.git'))
        return clone


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

    def test_xcode_mismatch_refuses(self):
        self.remote_xcode_build.write_text('16E100\n')
        result = self.run_rb('setup-host', success=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn('CR_XCODE_BUILD', result.stderr)
        self.assertIn('16E100', result.stderr)
        self.assertIn('Xcode 16F6/SDK 26.0', result.stderr)
        self.assertFalse((self.remote / 'rac-remote').exists())

    def test_sdk_mismatch_refuses(self):
        self.remote_xcode_sdk.write_text('25.2\n')
        result = self.run_rb('setup-host', success=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn('SDK', result.stderr)
        self.assertIn('25.2', result.stderr)
        self.assertIn('cold build', result.stderr)
        self.assertFalse((self.remote / 'rac-remote').exists())

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


class SeedBaseTest(RemoteBuildTest):

    def make_sync_worktree(self):
        """A sync worktree with a tag, a submodule, and a built tree."""
        core = self.make_repo(self.folder / 'core', branch='main')
        wt = self.make_repo(self.folder / 'sync-wt', branch='main')
        subprocess.run(['git', '-C', str(wt), '-c', 'protocol.file.allow=always',
                        'submodule', 'add', '-q', str(core), 'helium-chromium'],
                       check=True, capture_output=True)
        git(wt, 'commit', '-qm', 'submodule')
        git(wt, 'tag', 'v1')
        self.sub_commit = git(core, 'rev-parse', 'HEAD').stdout.strip()
        # The built tree: siso state, a quilt record, and stubbed tools.
        src = wt / 'build/src'
        write(src / '.pc/applied-patches', 'a.patch\n')
        write(src / '.pc/.quilt_patches', f'{wt}/patches\n')
        write(src / 'out/Default/.siso_fs_state', 'state\n')
        tool(src / 'third_party/siso/cipd/siso', f'''\
            echo "siso $*" >> "$RAC_FAKE_LOG"
            if [ "${{2:-}}" = export ]; then echo "{src}/out/Default/fs"; fi
            if [ "${{2:-}}" = import ]; then cat > "$4/imported.txt"; fi
            ''')
        tool(src / 'buildtools/mac/gn',
             'echo "gn $* DEVELOPER_DIR=$DEVELOPER_DIR" >> "$RAC_FAKE_LOG"\n'
             'echo "Done. Made 1 targets"\n')
        return wt

    def test_seed_base(self):
        wt = self.make_sync_worktree()
        self.seed_remote()
        result = self.run_rb('seed-base', wt, 'v1', success=True)
        calls = self.calls()
        # The tag, branch, and submodule objects reached the bare repos.
        remote = self.remote / 'rac-remote'
        head = git(wt, 'rev-parse', 'HEAD').stdout.strip()
        self.assertEqual(git(remote / 'rac.git', 'rev-parse', 'refs/heads/main')
                         .stdout.strip(), head)
        self.assertEqual(git(remote / 'rac.git', 'rev-parse', 'v1^{commit}')
                         .stdout.strip(), head)
        self.assertEqual(git(remote / 'helium-chromium.git', 'rev-parse', 'base')
                         .stdout.strip(), self.sub_commit)
        # base/ is at the tag with its submodule checked out.
        base = remote / 'base'
        self.assertEqual(git(base, 'rev-parse', 'HEAD').stdout.strip(), head)
        self.assertTrue((base / 'helium-chromium/.git').exists())
        # The tree seeded, siso's state rewritten, gn gen and record done.
        src = base / 'build/src'
        self.assertTrue((src / 'out/Default/.siso_fs_state').exists())
        self.assertIn('--partial', calls)
        self.assertIn('--info=progress2', calls)
        imported = (src / 'out/Default/imported.txt').read_text()
        self.assertIn(str(src), imported)
        self.assertNotIn(str(wt), imported)
        self.assertIn(f'DEVELOPER_DIR={self.folder}/Xcode', calls)
        self.assertEqual((src / '.pc/.quilt_patches').read_text().strip(),
                         str(base / 'patches'))
        self.assertIn('update_patches.sh merge', calls)
        record = (src / '.pc/.rac_applied').read_text()
        self.assertIn('a.patch', record)
        # Idempotent: seeding again succeeds.
        self.run_rb('seed-base', wt, 'v1', success=True)

    def test_seed_base_keeps_the_record_and_takes_relative_paths(self):
        wt = self.make_sync_worktree()
        self.seed_remote()
        write(wt / 'build/src/.pc/.rac_applied', 'abc a.patch\n')
        result = subprocess.run(['/bin/bash', SCRIPT, 'seed-base', 'sync-wt', 'v1'],
                                cwd=self.folder, env=self.env(),
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        src = self.remote / 'rac-remote/base/build/src'
        self.assertEqual((src / '.pc/.rac_applied').read_text(), 'abc a.patch\n')
        # siso's paths were rewritten from the physical path, not 'sync-wt'.
        self.assertNotIn(str(wt), (src / 'out/Default/imported.txt').read_text())

    def test_seed_base_refuses_a_worktree_off_the_tag(self):
        wt = self.make_sync_worktree()
        self.seed_remote()
        write(wt / 'file.txt', 'later\n')
        git(wt, 'commit', '-qam', 'after the tag')
        result = self.run_rb('seed-base', wt, 'v1', success=False)
        self.assertIn('not at v1', result.stderr)
        self.assertFalse((self.remote / 'rac-remote/base/build').exists())

    def test_seed_base_refuses_on_toolchain_mismatch(self):
        wt = self.make_sync_worktree()
        self.seed_remote()
        self.remote_xcode_sdk.write_text('25.2\n')
        result = self.run_rb('seed-base', wt, 'v1', success=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn('SDK', result.stderr)
        # Refused before any push: the bare repo has no refs.
        remote = self.remote / 'rac-remote'
        self.assertNotEqual(
            git(remote / 'rac.git', 'rev-parse', '-q', '--verify',
                'refs/heads/main', check=False).returncode, 0)


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
        self.run_rb('push', self.wt, success=True)
        self.assertTrue((self.remote_root / 'wt/feature').exists())

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


class BuildTest(RemoteBuildTest):

    def setUp(self):
        super().setUp()
        self.remote_root = self.seed_remote()
        self.remote_clone('feature')
        self.wt = self.make_repo(self.folder / 'feature', branch='feat/x')
        # autoninja itself, where the build's bash -c looks for it.
        src = self.remote_root / 'wt/feature/build/src'
        write(src / 'third_party/depot_tools/autoninja.py', STUB_AUTONINJA)

    def test_build_composes_the_queued_autoninja_call(self):
        # The Pro has 18 cores; the default reserve of 4 leaves 14 jobs.
        result = self.run_rb('build', self.wt, success=True, FAKE_CORES='18')
        calls = self.calls()
        self.assertIn('nice -n 10', calls)
        self.assertIn('taskpolicy -c utility', calls)
        self.assertIn('queue bash -c', calls)
        self.assertIn('autoninja -C out/Default chrome chromedriver -local_jobs=14',
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


class RunTest(RemoteBuildTest):

    def setUp(self):
        super().setUp()
        self.remote_root = self.seed_remote()
        self.clone = self.remote_clone('feature')
        self.wt = self.make_repo(self.folder / 'feature', branch='feat/x')

    def test_run_refuses_profile_and_foreground_args(self):
        for args, why in [
            (('--', '--user-data-dir=/tmp/x'), '--user-data-dir'),
            (('--', '--user-data-dir', '/tmp/x'), '--user-data-dir'),
            (('--', '--flag', '~/Library/Application Support/x'), 'Application Support'),
            (('--', '--rac-window-screenshot-activate'), 'foreground'),
            (('--', '-user-data-dir=/tmp/x'), 'two dashes'),
            (('--', '-rac-window-screenshot-activate'), 'two dashes'),
            (('--', '--x=/Users/k/library/APPLICATION SUPPORT/me.kainoa.rac'),
             'real profile'),
            (('--', '--x=~/Library/Application%20Support/net.imput.helium'),
             'real profile'),
            (('--', '--rac-window-screenshot=/Users/k/Desktop/x.png'), 'absolute'),
            (('--', '--rac-window-screenshot-requests=/Users/k/notes.txt'), 'absolute'),
            (('--', '--rac-window-screenshot=../../x.png'), 'leave the clone'),
            (('--', '--rac-window-screenshot', 'x.png'), '--rac-window-screenshot='),
            (('--', '--disk-cache-dir=/tmp/c'), 'absolute'),
        ]:
            result = self.run_rb('run', self.wt, *args, success=False)
            self.assertEqual(result.returncode, 2, (args, result.stderr))
            self.assertIn(why, result.stderr)
        self.assertEqual(self.calls(), '')

    def test_run_screenshots_and_stops_the_clone(self):
        shot = self.clone / 'build/shots/x.png'
        # A process from another app must survive; one from this clone must not.
        survivor = subprocess.Popen(['sleep', '300'])
        rogue = subprocess.Popen(
            ['bash', '-c', 'exec -a "$1" sleep 300', '_',
             f'{self.clone}/build/src/out/Default/rac.app/Contents/MacOS/rac Helper'])
        self.addCleanup(lambda: (survivor.kill(), survivor.wait()))
        self.addCleanup(lambda: (rogue.kill(), rogue.wait()))
        time.sleep(0.3)
        started = time.monotonic()
        result = self.run_rb('run', self.wt, '--', '--rac-window-screenshot=x.png',
                             success=True)
        self.assertLess(time.monotonic() - started, 60)
        self.assertTrue(shot.exists())
        self.assertIn(str(shot), result.stderr)
        # The fake browser and the rogue proc are gone; the outsider lives.
        # (A killed child waits as a zombie until polled, so wait for it.)
        rogue.wait(timeout=10)
        survivor.poll()
        self.assertIsNone(survivor.returncode)

    def test_run_ignores_a_stale_screenshot(self):
        # An earlier run's shot must not end the wait before the new one.
        write(self.clone / 'build/shots/x.png', 'old\n')
        result = self.run_rb('run', self.wt, '--', '--rac-window-screenshot=x.png',
                             success=True, SHOT_DELAY='4')
        self.assertEqual((self.clone / 'build/shots/x.png').read_text(), 'png\n')

    def test_run_passes_odd_args_through_intact(self):
        odd = "it's $HOME `id` *"
        self.run_rb('run', self.wt, '--timeout', '3', '--', odd, success=True)
        self.assertIn(f'--rac-launch-in-background {odd}', self.calls())

    def test_run_timeout_stops_the_browser(self):
        result = self.run_rb('run', self.wt, '--timeout', '4', '--',
                             '--no-screenshot-run', success=True)
        self.assertIn('queue', self.calls())


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
        self.assertIn(f'rsync -e ssh -o BatchMode=yes -a --partial --info=progress2 '
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
        # seed-base prints its pushes but sends nothing.
        wt = self.make_repo(self.folder / 'sync-wt', branch='main')
        result = self.run_rb('--dry-run', 'push', wt, success=True)
        self.assertIn('push --force', result.stderr)
        self.assertFalse((self.remote_root / 'wt/sync-wt').exists())


if __name__ == '__main__':
    unittest.main()
