#!/usr/bin/env python3

# Copyright 2025 The rac Authors
# You can use, redistribute, and/or modify this source code under
# the terms of the GPL-3.0 license that can be found in the LICENSE file.
"""Runs worktree.sh with real quilt in temporary git repositories.

The name passes, rac_version.py, siso and gn are small fakes. No real build
tree, checkout, or profile is touched.

Run from the repository root:
    python3 -m unittest discover -s devutils/rac -p 'test_*.py' -v
"""

from pathlib import Path
import difflib
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from unittest import mock

import worktree_state

HERE = Path(__file__).resolve().parent
QUILT_ENV = {'QUILT_SERIES': 'series.merged', 'QUILT_PATCH_OPTS': '--unified --reject-format=unified'}

# Brands *.grd files the way the real passes do: originals into the backup.
FAKE_PASS = '''\
import argparse, io, os, pathlib, tarfile
p = argparse.ArgumentParser()
p.add_argument('--sub', action='store_true')
p.add_argument('-t', type=pathlib.Path)
p.add_argument('--backup-path', type=pathlib.Path)
a = p.parse_args()
changed = []
for root, _, files in os.walk(a.t):
    if '.pc' in pathlib.Path(root).parts:
        continue
    for name in files:
        path = pathlib.Path(root) / name
        if name.endswith('.grd') and OLD in path.read_text():
            changed.append((str(path.relative_to(a.t)), path.read_bytes()))
            path.write_text(path.read_text().replace(OLD, NEW))
with tarfile.open(a.backup_path, 'w:gz') as tar:
    for name, data in changed:
        info = tarfile.TarInfo(name)
        info.size = len(data)
        tar.addfile(info, io.BytesIO(data))
print(f'Modified {len(changed)} files')
'''


def patch_text(file, before, after):
    return ''.join(
        difflib.unified_diff(before.splitlines(True),
                             after.splitlines(True),
                             fromfile=f'a/{file}',
                             tofile=f'b/{file}'))


def make_checkout(root):
    """A git repo with rac's scripts (and fakes for the rest) and patches."""
    tools = root / 'devutils' / 'rac'
    tools.mkdir(parents=True)
    for name in ['worktree.sh', 'worktree_state.py', 'dev_names.py']:
        shutil.copy2(HERE / name, tools / name)
    (tools / 'name_pass.py').write_text("OLD, NEW = 'Helium', 'rac'\n" + FAKE_PASS)
    (tools / 'rac_version.py').write_text('pass\n')
    helium = root / 'helium-chromium' / 'utils'
    helium.mkdir(parents=True)
    (helium / 'name_substitution.py').write_text("OLD, NEW = 'Chromium', 'Helium'\n" + FAKE_PASS)
    (root / 'helium-chromium' / '.git').write_text('fixture\n')
    (root / 'patches').mkdir()
    subprocess.run(['git', 'init', '-q', str(root)], check=True)


@unittest.skipUnless(shutil.which('quilt') and shutil.which('greadlink'),
                     'needs quilt and greadlink')
class WorktreeTestCase(unittest.TestCase):

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='rac-test-worktree-')
        self.addCleanup(temporary.cleanup)
        self.folder = Path(temporary.name).resolve()
        self.root = self.folder / 'checkout'
        self.tree = self.root / 'build' / 'src'
        self.patches = self.root / 'patches'
        make_checkout(self.root)
        self.tree.mkdir(parents=True)
        (self.tree / 'OWNERS').write_text('fixture\n')
        (self.tree / 'one').write_text('base one\n')
        (self.tree / 'two').write_text('base two\n')
        (self.tree / 'strings.grd').write_text('Chromium browser\n')
        self.write_patch('a.patch', 'one', 'base one\n', 'saved one\n')
        self.write_patch('s.patch', 'strings.grd', 'Chromium browser\n',
                         'Chromium browser\nChromium menu\n')
        self.write_patch('b.patch', 'two', 'base two\n', 'saved two\n')
        self.series(['a.patch', 's.patch', 'b.patch'])
        self.quilt('push', '-a', '-q')
        self.state('record')
        self.names('sub')

    def write_patch(self, name, file, before, after):
        (self.patches / name).write_text(patch_text(file, before, after))

    def series(self, names):
        (self.patches / 'series.merged').write_text(''.join(n + '\n' for n in names))

    def quilt(self, *args, tree=None):
        env = dict(os.environ, QUILT_PATCHES=str(self.patches), **QUILT_ENV)
        return subprocess.run(['quilt', '--quiltrc', '-', *args],
                              cwd=tree or self.tree,
                              env=env,
                              check=True,
                              capture_output=True)

    def state(self, *args, tree=None, patches=None):
        return subprocess.run([
            'python3', HERE / 'worktree_state.py', tree or self.tree, patches or self.patches,
            *args
        ],
                              check=True,
                              capture_output=True,
                              text=True)

    def names(self, *args):
        return subprocess.run(
            ['python3', self.root / 'devutils/rac/dev_names.py', *args, '-t', self.tree],
            check=True,
            capture_output=True,
            text=True)

    def worktree(self, *args, cwd=None, env=None, success=True):
        result = subprocess.run(['/bin/bash', self.root / 'devutils/rac/worktree.sh', *args],
                                cwd=cwd or self.root,
                                env=dict(os.environ, **(env or {})),
                                capture_output=True,
                                text=True,
                                check=False)
        if success:
            self.assertEqual(result.returncode, 0, result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stderr)
        return result

    def applied(self, tree=None):
        return (tree or self.tree).joinpath('.pc/applied-patches').read_text().split()

    def snapshot(self):
        return {
            p.relative_to(self.tree).as_posix(): p.read_bytes()
            for p in self.tree.rglob('*') if p.is_file() and '.pc' not in p.parts
        }


class SyncTest(WorktreeTestCase):

    def refuses(self, file):
        """Sync must stop before popping, keeping every source byte."""
        before = self.snapshot()
        applied = self.applied()
        result = self.worktree('sync', success=False)
        self.assertIn(f'{file} in ', result.stderr)
        self.assertIn("doesn't match any saved or committed version", result.stderr)
        self.assertEqual(self.applied(), applied)
        # Only the names were reverted (strings.grd), as the message says.
        after = self.snapshot()
        before.pop('strings.grd'), after.pop('strings.grd')
        self.assertEqual({k: v for k, v in after.items() if not k.startswith('.rac_names')},
                         {k: v for k, v in before.items() if not k.startswith('.rac_names')})
        return result

    # Normal flows must never be refused.

    def test_sync_without_changes(self):
        before = self.snapshot()
        self.worktree('sync')
        self.assertEqual(self.snapshot(), before)
        self.assertEqual((self.tree / 'strings.grd').read_text(), 'rac browser\nrac menu\n')

    def test_sync_after_rebase_changes_patches(self):
        self.write_patch('b.patch', 'two', 'base two\n', 'incoming two\n')
        self.write_patch('s.patch', 'strings.grd', 'Chromium browser\n',
                         'Chromium browser\nChromium tabs\n')
        self.worktree('sync')
        self.assertEqual((self.tree / 'two').read_text(), 'incoming two\n')
        self.assertEqual((self.tree / 'strings.grd').read_text(), 'rac browser\nrac tabs\n')

    def test_sync_after_quilt_refresh(self):
        (self.tree / 'two').write_text('refreshed two\n')
        self.quilt('refresh')
        self.worktree('sync')
        self.assertEqual((self.tree / 'two').read_text(), 'refreshed two\n')

    def test_documented_string_file_flow(self):
        # unsub, edit the string patch's file, refresh, then sync.
        self.names('unsub')
        self.quilt('pop', '-q', 'a.patch')  # s.patch is now on top... after pop it's a
        self.quilt('push', '-q')
        (self.tree / 'strings.grd').write_text('Chromium browser\nChromium edited\n')
        self.quilt('refresh')
        self.quilt('push', '-a', '-q')
        self.worktree('sync')
        self.assertEqual((self.tree / 'strings.grd').read_text(), 'rac browser\nrac edited\n')

    def test_sync_with_removed_patch(self):
        self.series(['a.patch', 's.patch'])
        (self.patches / 'b.patch').unlink()
        self.worktree('sync')
        self.assertEqual((self.tree / 'two').read_text(), 'base two\n')

    def test_sync_with_new_refreshed_patch(self):
        (self.tree / 'three').write_text('base three\n')
        self.quilt('new', 'c.patch')
        self.quilt('add', 'three')
        (self.tree / 'three').write_text('saved three\n')
        self.quilt('refresh')
        self.worktree('sync')
        self.assertEqual((self.tree / 'three').read_text(), 'saved three\n')

    # Homebrew's quilt 0.69 pushes a new patch whose file doesn't exist yet as
    # empty; Ubuntu's 0.67 refuses. worktree.sh only runs on macOS.
    @unittest.skipUnless(sys.platform == 'darwin', 'needs quilt 0.69 (Homebrew)')
    def test_sync_with_new_empty_patch(self):
        self.quilt('new', 'c.patch')
        self.quilt('add', 'two')
        self.worktree('sync')

    def test_older_record_without_copies_still_syncs(self):
        shutil.rmtree(self.tree / '.pc' / '.rac_patch_bytes')
        (self.tree / '.rac_names' / 'expected.json').unlink()
        self.write_patch('b.patch', 'two', 'base two\n', 'incoming two\n')
        # Touched since it was applied, so the check can't skip it.
        os.utime(self.tree / 'two')
        result = self.worktree('sync')
        self.assertIn("can't check b.patch", result.stderr)
        self.assertIn('older dev_names.py', result.stderr)
        self.assertEqual((self.tree / 'two').read_text(), 'incoming two\n')
        # The next sync has copies and hashes again.
        self.assertTrue(any((self.tree / '.pc' / '.rac_patch_bytes').iterdir()))
        self.assertTrue((self.tree / '.rac_names' / 'expected.json').exists())

    # Edits that popping would throw away.

    def test_incoming_patch_with_unsaved_edit(self):
        self.write_patch('b.patch', 'two', 'base two\n', 'incoming two\n')
        (self.tree / 'two').write_text('UNSAVED\n')
        self.refuses('two')

    def test_refreshed_patch_with_more_unsaved_edits(self):
        (self.tree / 'two').write_text('refreshed two\n')
        self.quilt('refresh')
        (self.tree / 'two').write_text('refreshed two\nUNSAVED\n')
        self.refuses('two')

    def test_new_patch_with_unsaved_edit(self):
        # main used to skip its check here: the patch isn't in the record.
        (self.tree / 'three').write_text('base three\n')
        self.quilt('new', 'c.patch')
        self.quilt('add', 'three')
        (self.tree / 'three').write_text('saved three\n')
        self.quilt('refresh')
        (self.tree / 'three').write_text('UNSAVED\n')
        self.refuses('three')

    def test_new_patch_never_refreshed(self):
        self.quilt('new', 'c.patch')
        self.quilt('add', 'two')
        (self.tree / 'two').write_text('UNSAVED\n')
        self.refuses('two')

    def test_unsaved_edit_in_a_lower_patch(self):
        # Not the top patch, so main's quilt diff -z check missed it.
        self.write_patch('a.patch', 'one', 'base one\n', 'incoming one\n')
        (self.tree / 'one').write_text('UNSAVED\n')
        self.refuses('one')

    def test_removed_patch_with_unsaved_edit(self):
        self.series(['a.patch', 's.patch'])
        (self.patches / 'b.patch').unlink()
        (self.tree / 'two').write_text('UNSAVED\n')
        self.refuses('two')

    def test_unchanged_patch_with_edit_is_checked_without_copies(self):
        shutil.rmtree(self.tree / '.pc' / '.rac_patch_bytes')
        self.write_patch('a.patch', 'one', 'base one\n', 'incoming one\n')
        (self.tree / 'two').write_text('UNSAVED\n')  # b.patch itself is unchanged
        self.refuses('two')

    def test_edit_below_the_changed_patches_is_kept(self):
        (self.tree / 'one').write_text('kept\n')
        self.write_patch('b.patch', 'two', 'base two\n', 'incoming two\n')
        self.worktree('sync')
        self.assertEqual((self.tree / 'one').read_text(), 'kept\n')

    def test_edited_string_file_refuses_before_any_change(self):
        self.write_patch('b.patch', 'two', 'base two\n', 'incoming two\n')
        (self.tree / 'strings.grd').write_text('rac browser\nrac menu\nUNSAVED\n')
        before = self.snapshot()
        result = self.worktree('sync', success=False)
        self.assertIn('strings.grd changed since', result.stderr)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.applied(), ['a.patch', 's.patch', 'b.patch'])

    def git(self, *args):
        subprocess.run(['git', '-C', self.root, '-c', 'user.name=t', '-c', 'user.email=t@t',
                        '-c', 'commit.gpgsign=false', *args],
                       check=True, capture_output=True)

    def refresh_a_and_commit(self, text):
        """Pops to a.patch, refreshes it with `text`, pushes the rest again and
        commits, without a sync: the saved copy stays the old version."""
        self.names('unsub')
        self.quilt('pop', 'a.patch')
        (self.tree / 'one').write_text(text)
        self.quilt('refresh')
        self.quilt('push', '-a')
        self.names('sub')
        # A later patch on the same file, or unsub rewriting a string file,
        # makes it newer than the refresh, so check() can't skip the patch.
        os.utime(self.tree / 'one')
        self.git('add', 'patches/a.patch')
        self.git('commit', '-q', '-m', 'refresh a')

    def test_refresh_then_rebase_of_a_lower_patch_is_not_refused(self):
        self.git('add', 'patches/a.patch')
        self.git('commit', '-q', '-m', 'base')
        self.refresh_a_and_commit('refreshed one\n')
        # A rebase replaces that commit; the refreshed version is only in the
        # reflog now, and a.patch changes again.
        self.git('reset', '-q', '--hard', 'HEAD~1')
        self.write_patch('a.patch', 'one', 'base one\n', 'rebased one\n')
        self.git('commit', '-q', '-am', 'rebased a')
        result = self.worktree('sync')
        self.assertIn('a.patch holds the version committed in', result.stderr)
        self.assertEqual((self.tree / 'one').read_text(), 'rebased one\n')

    def test_refresh_then_rebase_still_finds_unsaved_edits(self):
        self.git('add', 'patches/a.patch')
        self.git('commit', '-q', '-m', 'base')
        self.refresh_a_and_commit('refreshed one\n')
        self.write_patch('a.patch', 'one', 'base one\n', 'rebased one\n')
        self.git('commit', '-q', '-am', 'rebased a')
        (self.tree / 'one').write_text('refreshed one\nUNSAVED\n')
        self.refuses('one')

    def test_refusal_never_suggests_refreshing_blindly(self):
        self.write_patch('b.patch', 'two', 'base two\n', 'incoming two\n')
        (self.tree / 'two').write_text('UNSAVED\n')
        result = self.refuses('two')
        self.assertIn('quilt diff -z -P b.patch', result.stderr)
        self.assertIn("don't refresh", result.stderr)
        self.assertIn('sync --discard', result.stderr)
        self.assertNotIn('save or discard', result.stderr)

    def test_sync_discard_drops_unsaved_edits(self):
        self.write_patch('b.patch', 'two', 'base two\n', 'incoming two\n')
        (self.tree / 'two').write_text('UNSAVED\n')
        self.worktree('sync', '--discard')
        self.assertEqual((self.tree / 'two').read_text(), 'incoming two\n')
        self.worktree('sync', '--bogus', success=False)

    def copy_of(self, name):
        for line in (self.tree / '.pc' / '.rac_applied').read_text().splitlines():
            fingerprint, patch = line.split(' ', 1)
            if patch == name:
                return self.tree / '.pc' / '.rac_patch_bytes' / fingerprint
        raise AssertionError(name)

    def test_record_repairs_a_truncated_copy(self):
        copy = self.copy_of('b.patch')
        whole = copy.read_bytes()
        copy.write_bytes(whole[:10])
        self.state('record')
        self.assertEqual(copy.read_bytes(), whole)
        self.assertEqual(list((self.tree / '.pc' / '.rac_patch_bytes').glob('*.tmp')), [])

    def test_truncated_copy_refuses_instead_of_skipping(self):
        copy = self.copy_of('b.patch')
        copy.write_bytes(copy.read_bytes()[:10])
        self.write_patch('b.patch', 'two', 'base two\n', 'incoming two\n')
        (self.tree / 'two').write_text('UNSAVED\n')
        result = self.refuses('two')
        self.assertNotIn("can't check", result.stderr)

    def test_unchanged_patch_is_replayed_once(self):
        self.write_patch('a.patch', 'one', 'base one\n', 'incoming one\n')
        (self.tree / 'two').write_text('UNSAVED\n')  # b.patch is unchanged
        self.names('unsub')  # as sync does before the check
        calls = []
        real_replay = worktree_state.replay

        def counting(data, before):
            calls.append(set(before))
            return real_replay(data, before)

        with mock.patch.object(worktree_state, 'replay', side_effect=counting):
            with self.assertRaises(SystemExit):
                worktree_state.check(self.tree, self.patches, 0)
        self.assertEqual(calls.count({'two'}), 1)

    def test_copies_of_old_versions_are_pruned(self):
        self.write_patch('b.patch', 'two', 'base two\n', 'incoming two\n')
        self.worktree('sync')
        copies = {p.name for p in (self.tree / '.pc' / '.rac_patch_bytes').iterdir()}
        recorded = {
            line.split()[0]
            for line in (self.tree / '.pc' / '.rac_applied').read_text().splitlines()
        }
        self.assertEqual(copies, recorded)


@unittest.skipUnless(sys.platform == 'darwin',
                     'setup clones the tree with APFS clonefile(2) from libSystem')
class SetupTest(WorktreeTestCase):
    """setup in a worktree, cloning the fixture checkout's tree."""

    def setUp(self):
        super().setUp()
        out = self.tree / 'out' / 'Default'
        out.mkdir(parents=True)
        (out / '.siso_fs_state').write_text('state\n')
        self.siso_log = self.folder / 'siso.log'
        self.fake_tool(self.tree / 'third_party/siso/cipd/siso', f'''\
            echo "$*" >> {self.siso_log}
            [ -z "${{FAIL_SISO:-}}" ] || {{ echo "siso: broken" >&2; exit 1; }}
            [ "$2" = import ] && cat > /dev/null || echo "$PWD/out/Default/x"
            ''')
        self.gn_log = self.folder / 'gn.log'
        self.fake_tool(self.tree / 'buildtools/mac/gn', f'''\
            echo "$DEVELOPER_DIR" >> {self.gn_log}
            if [ -n "${{FAIL_GN:-}}" ]; then echo "ERROR: xcodebuild requires Xcode"; exit 1; fi
            echo "Done. Made 1 targets"
            ''')
        # An Xcode that xcode-select reports, so the test doesn't depend on
        # the host. Only gn and siso see it.
        self.xcode = self.folder / 'Xcode.app' / 'Contents' / 'Developer'
        self.fake_tool(self.xcode / 'usr' / 'bin' / 'xcodebuild', 'exit 0\n')
        self.fake_tool(self.folder / 'bin' / 'xcode-select', f'echo {self.xcode}\n')
        subprocess.run(['git', '-C', self.root, 'add', '-A', 'devutils', 'patches'], check=True)
        subprocess.run([
            'git', '-C', self.root, '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-qm',
            'fixture'
        ],
                       check=True)
        self.wt = self.folder / 'feature'
        subprocess.run(['git', '-C', self.root, 'worktree', 'add', '-q', self.wt], check=True)
        self.fake_submodule(self.wt)
        self.wt_src = self.wt / 'build' / 'src'

    def fake_submodule(self, checkout):
        """What setup's submodule checkout would bring: the Helium pass."""
        shutil.copytree(self.root / 'helium-chromium', checkout / 'helium-chromium',
                        dirs_exist_ok=True, ignore=shutil.ignore_patterns('patches'))

    def env(self, **extra):
        env = {'REPO_ROOT_PATH': str(self.root), 'PATH': f'{self.folder}/bin:{os.environ["PATH"]}'}
        return {**env, **extra}

    def fake_tool(self, path, body):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('#!/bin/bash\n' + textwrap.dedent(body))
        path.chmod(0o755)

    def setup_worktree(self, success=True, **env):
        return self.worktree('setup', cwd=self.wt, env=self.env(**env), success=success)

    def test_setup_clones_and_syncs(self):
        (self.wt / 'patches' / 'b.patch').write_text(
            patch_text('two', 'base two\n', 'feature two\n'))
        self.setup_worktree()
        self.assertEqual(self.gn_log.read_text(), f'{self.xcode}\n')
        self.assertEqual((self.wt_src / 'two').read_text(), 'feature two\n')
        self.assertEqual((self.wt_src / 'strings.grd').read_text(), 'rac browser\nrac menu\n')
        self.assertEqual((self.wt_src / '.pc' / '.quilt_patches').read_text().strip(),
                         str(self.wt / 'patches'))
        # The base's tree is untouched.
        self.assertEqual((self.tree / 'two').read_text(), 'saved two\n')

    def test_setup_discards_what_the_base_left_unsaved(self):
        # Edits in the base's tree are the base's; the clone may drop them.
        (self.tree / 'two').write_text('UNSAVED IN BASE\n')
        (self.tree / 'strings.grd').write_text('rac browser\nUNSAVED IN BASE\n')
        (self.wt / 'patches' / 'b.patch').write_text(
            patch_text('two', 'base two\n', 'feature two\n'))
        (self.wt / 'patches' / 's.patch').write_text(
            patch_text('strings.grd', 'Chromium browser\n', 'Chromium browser\nChromium x\n'))
        self.setup_worktree()
        self.assertEqual((self.wt_src / 'two').read_text(), 'feature two\n')
        self.assertEqual((self.wt_src / 'strings.grd').read_text(), 'rac browser\nrac x\n')

    def test_setup_from_an_unmerged_base_without_a_record(self):
        # he unmerge moves Helium's patches back into the submodule.
        (self.tree / '.pc' / '.rac_applied').unlink()
        core = self.root / 'helium-chromium' / 'patches'
        core.mkdir()
        shutil.move(self.patches / 'a.patch', core / 'a.patch')
        (self.patches / 'series.merged').unlink()
        result = self.setup_worktree()
        self.assertNotIn('popping', result.stderr)
        self.assertEqual(self.applied(self.wt_src), ['a.patch', 's.patch', 'b.patch'])

    def test_setup_from_another_worktree(self):
        self.setup_worktree()
        other = self.folder / 'other'
        subprocess.run(['git', '-C', self.root, 'worktree', 'add', '-q', other], check=True)
        self.fake_submodule(other)
        (self.wt_src / 'out' / 'Default' / 'from-feature').write_text('x\n')
        self.worktree('setup', str(self.wt), cwd=other, env=self.env())
        self.assertTrue((other / 'build/src/out/Default/from-feature').exists())

    def test_siso_failure_is_loud(self):
        result = self.setup_worktree(success=False, FAIL_SISO='1')
        self.assertIn('siso: broken', result.stderr)
        self.assertIn("couldn't move siso's build state", result.stderr)

    def test_gn_failure_shows_gn_output(self):
        result = self.setup_worktree(success=False, FAIL_GN='1')
        self.assertIn('ERROR: xcodebuild requires Xcode', result.stderr)
        self.assertIn('gn gen failed', result.stderr)


@unittest.skipUnless(shutil.which('quilt') and shutil.which('greadlink'),
                     'needs quilt and greadlink')
class XcodeDirTest(unittest.TestCase):
    """xcode_dir, with a fake xcode-select and a fake /Applications."""

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='rac-test-xcode-')
        self.addCleanup(temporary.cleanup)
        self.folder = Path(temporary.name).resolve()
        self.root = self.folder / 'checkout'
        make_checkout(self.root)
        self.apps = self.folder / 'Applications'
        self.bin = self.folder / 'bin'
        self.bin.mkdir()
        self.clt = self.folder / 'CommandLineTools'
        (self.clt / 'usr' / 'bin').mkdir(parents=True)

    def make_xcode(self, app):
        tool = self.apps / app / 'Contents' / 'Developer' / 'usr' / 'bin' / 'xcodebuild'
        tool.parent.mkdir(parents=True)
        tool.write_text('#!/bin/sh\n')
        tool.chmod(0o755)
        return tool.parents[2]

    def run_use_xcode(self, selected, developer_dir=None):
        select = self.bin / 'xcode-select'
        select.write_text(f'#!/bin/sh\necho "{selected}"\n')
        select.chmod(0o755)
        env = dict(os.environ, PATH=f'{self.bin}:{os.environ["PATH"]}')
        env.pop('DEVELOPER_DIR', None)
        # Set after sourcing: /usr/bin/git, which the script runs, would
        # follow a fake DEVELOPER_DIR.
        export = f'export DEVELOPER_DIR={developer_dir}; ' if developer_dir else ''
        script = (f'source {self.root}/devutils/rac/worktree.sh; {export}'
                  f'dir=$(xcode_dir {self.apps}) || exit 1; echo "DEVELOPER_DIR=$dir"')
        return subprocess.run(['/bin/bash', '-c', script],
                              cwd=self.root,
                              env=env,
                              capture_output=True,
                              text=True,
                              check=False)

    def assert_picks(self, result, path):
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), f'DEVELOPER_DIR={path}')

    def test_command_line_tools_selected_finds_xcode(self):
        xcode = self.make_xcode('Xcode.app')
        result = self.run_use_xcode(self.clt)
        self.assert_picks(result, xcode)
        self.assertIn("xcode-select doesn't point at Xcode", result.stderr)

    def test_prefers_xcode_app_over_other_versions(self):
        self.make_xcode('Xcode-beta.app')
        xcode = self.make_xcode('Xcode.app')
        self.assert_picks(self.run_use_xcode(self.clt), xcode)

    def test_finds_a_versioned_xcode(self):
        beta = self.make_xcode('Xcode-beta.app')
        self.assert_picks(self.run_use_xcode(self.clt), beta)

    def test_keeps_developer_dir_that_is_xcode(self):
        self.make_xcode('Xcode.app')
        mine = self.make_xcode('Xcode_16.app')
        self.assert_picks(self.run_use_xcode(self.clt, developer_dir=mine), mine)

    def test_replaces_developer_dir_that_is_not_xcode(self):
        xcode = self.make_xcode('Xcode.app')
        self.assert_picks(self.run_use_xcode(self.clt, developer_dir=self.clt), xcode)

    def test_keeps_xcode_select_choice(self):
        self.make_xcode('Xcode.app')
        chosen = self.make_xcode('Xcode-beta.app')
        result = self.run_use_xcode(chosen)
        self.assert_picks(result, chosen)
        self.assertEqual(result.stderr, '')

    def test_accepts_developer_dir_that_is_an_app(self):
        self.make_xcode('Xcode.app')
        beta = self.make_xcode('Xcode-beta.app')
        app = beta.parents[1]
        self.assert_picks(self.run_use_xcode(self.clt, developer_dir=app), beta)
        self.assert_picks(self.run_use_xcode(self.clt, developer_dir=f'{app}/'), beta)

    def test_no_xcode_dies_with_a_message(self):
        result = self.run_use_xcode(self.clt)
        self.assertEqual(result.returncode, 1)
        self.assertIn('gn needs Xcode, and none was found', result.stderr)


if __name__ == '__main__':
    unittest.main()
