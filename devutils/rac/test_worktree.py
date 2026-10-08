#!/usr/bin/env python3
# Copyright 2025 The rac Authors
# You can use, redistribute, and/or modify this source code under
# the terms of the GPL-3.0 license that can be found in the LICENSE file.
"""Temp git repositories and real quilt; no real build trees or profiles."""

from pathlib import Path
import difflib
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import dev_names
import worktree_state
from test_dev_names import make_archive

HERE = Path(__file__).resolve().parent


def patch_text(file, before, after):
    return ''.join(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
                                      fromfile=f'a/{file}', tofile=f'b/{file}'))


@unittest.skipUnless(shutil.which('quilt'), 'real quilt is required')
class SyncTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='rac-test-worktree-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.tree = self.root / 'build' / 'src'
        self.tree.mkdir(parents=True)
        self.patches = self.root / 'patches'
        self.patches.mkdir()
        tools = self.root / 'devutils' / 'rac'
        tools.mkdir(parents=True)
        for name in ['worktree.sh', 'worktree_state.py', 'dev_names.py']:
            shutil.copy2(HERE / name, tools / name)
        # Fake only unrelated naming/version passes. Quilt and sync are real.
        script = """import argparse, io, pathlib, tarfile
p = argparse.ArgumentParser()
p.add_argument('--sub', action='store_true')
p.add_argument('-t', type=pathlib.Path)
p.add_argument('--backup-path', type=pathlib.Path)
a = p.parse_args()
with tarfile.open(a.backup_path, 'w:gz') as t:
    pass
print('fixture name pass')
"""
        (tools / 'name_pass.py').write_text(script)
        helium = self.root / 'helium-chromium' / 'utils'
        helium.mkdir(parents=True)
        (helium / 'name_substitution.py').write_text(script)
        (tools / 'rac_version.py').write_text('pass\n')
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        (self.tree / 'OWNERS').write_text('fixture\n')
        (self.tree / 'one').write_text('base one\n')
        (self.tree / 'two').write_text('base two\n')
        self.write_patch('a.patch', 'one', 'base one\n', 'saved one\n')
        self.write_patch('b.patch', 'two', 'base two\n', 'saved two\n')
        self.series(['a.patch', 'b.patch'])
        self.quilt('push', '-a', '-q')
        worktree_state.record(self.tree, self.patches)

    def write_patch(self, name, file, before, after):
        (self.patches / name).write_text(patch_text(file, before, after))

    def series(self, names):
        (self.patches / 'series.merged').write_text(''.join(n + '\n' for n in names))

    def quilt(self, *args):
        env = dict(os.environ, QUILT_PATCHES=str(self.patches), QUILT_SERIES='series.merged',
                   QUILT_PATCH_OPTS='--unified --reject-format=unified')
        return subprocess.run(['quilt', '--quiltrc', '-', *args], cwd=self.tree,
                              env=env, check=True, capture_output=True)

    def sync(self, success=True):
        result = subprocess.run(['/bin/bash', self.root / 'devutils' / 'rac' / 'worktree.sh',
                                 'sync'], cwd=self.root, capture_output=True, text=True)
        if success:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn('preflight failed', result.stderr)
        return result

    def snapshot(self):
        return {p.relative_to(self.tree).as_posix(): p.read_bytes()
                for p in self.tree.rglob('*') if p.is_file()}

    def assert_refuses_unchanged(self):
        before = self.snapshot()
        self.sync(success=False)
        self.assertEqual(self.snapshot(), before)

    def test_incoming_clean(self):
        self.write_patch('b.patch', 'two', 'base two\n', 'incoming two\n')
        self.sync()
        self.assertEqual((self.tree / 'two').read_text(), 'incoming two\n')

    def test_incoming_dirty(self):
        self.write_patch('b.patch', 'two', 'base two\n', 'incoming two\n')
        (self.tree / 'two').write_text('UNSAVED\n')
        self.assert_refuses_unchanged()

    def test_refreshed_clean(self):
        (self.tree / 'two').write_text('refreshed two\n')
        self.quilt('refresh')
        self.sync()
        self.assertEqual((self.tree / 'two').read_text(), 'refreshed two\n')

    def test_refreshed_then_dirty(self):
        (self.tree / 'two').write_text('refreshed two\n')
        self.quilt('refresh')
        (self.tree / 'two').write_text('refreshed two\nUNSAVED\n')
        self.assert_refuses_unchanged()

    def append_refreshed_patch(self, file='three', before='base three\n',
                               after='saved three\n'):
        path = self.tree / file
        if not path.exists():
            path.write_text(before)
        self.quilt('new', 'c.patch')
        self.quilt('add', file)
        path.write_text(after)
        self.quilt('refresh')
        self.assertNotIn('c.patch',
                         (self.tree / '.pc' / '.rac_applied').read_text())

    def test_appended_refreshed_patch_clean(self):
        self.append_refreshed_patch()
        self.sync()
        self.assertEqual((self.tree / 'three').read_text(), 'saved three\n')
        self.assertEqual(worktree_state.applied(self.tree), ['a.patch', 'b.patch', 'c.patch'])
        self.assertIn('c.patch', worktree_state.read_record(
            self.tree, ['a.patch', 'b.patch', 'c.patch']))

    def test_appended_refreshed_patch_dirty(self):
        self.append_refreshed_patch()
        (self.tree / 'three').write_text('UNSAVED appended\n')
        self.assert_refuses_unchanged()

    def test_appended_refreshed_patch_overlapping_clean(self):
        self.append_refreshed_patch('two', after='saved two\nsaved upper\n')
        self.sync()
        self.assertEqual((self.tree / 'two').read_text(), 'saved two\nsaved upper\n')

    def test_appended_patch_does_not_hide_dirty_lower_preimage(self):
        (self.tree / 'one').write_text('UNSAVED lower\n')
        self.append_refreshed_patch('one', after='UNSAVED lower\nsaved upper\n')
        self.write_patch('a.patch', 'one', 'base one\n', 'incoming one\n')
        self.assert_refuses_unchanged()

    def test_appended_refreshed_patch_branded_clean(self):
        self.append_refreshed_patch('strings.grd', 'Chromium base\n', 'Chromium saved\n')
        make_archive(self.tree, 'helium', {'strings.grd': b'Chromium saved\n'})
        make_archive(self.tree, 'rac', {'strings.grd': b'Helium saved\n'})
        (self.tree / 'strings.grd').write_bytes(b'rac saved\n')
        dev_names.record_expected(self.tree)
        self.sync()
        self.assertEqual((self.tree / 'strings.grd').read_bytes(), b'Chromium saved\n')

    def test_appended_patch_prebranding_edits_refuse(self):
        self.append_refreshed_patch('strings.grd', 'Chromium base\n', 'Chromium saved\n')
        make_archive(self.tree, 'helium', {'strings.grd': b'Chromium UNSAVED\n'})
        make_archive(self.tree, 'rac', {'strings.grd': b'Helium UNSAVED\n'})
        (self.tree / 'strings.grd').write_bytes(b'rac UNSAVED\n')
        dev_names.record_expected(self.tree)
        self.assert_refuses_unchanged()

    def test_unrecorded_insertion_refuses(self):
        self.append_refreshed_patch()
        self.quilt('pop', '-a', '-f', '-q')
        self.series(['a.patch', 'c.patch', 'b.patch'])
        self.quilt('push', '-a', '-q')
        self.assert_refuses_unchanged()

    def test_unrecorded_suffix_with_reordered_recorded_prefix_refuses(self):
        self.append_refreshed_patch()
        self.quilt('pop', '-a', '-f', '-q')
        self.series(['b.patch', 'a.patch', 'c.patch'])
        self.quilt('push', '-a', '-q')
        self.assert_refuses_unchanged()

    def test_missing_recorded_entry_refuses(self):
        self.quilt('pop', '-q')
        self.series(['a.patch'])
        self.assert_refuses_unchanged()

    def register_unchanged_file(self, contents=b'registered original\n'):
        (self.tree / 'registered').write_bytes(contents)
        self.quilt('add', 'registered')
        self.quilt('refresh')
        self.assertIn('registered', worktree_state.preimages(self.tree, 'b.patch'))
        self.assertNotIn('registered', (self.patches / 'b.patch').read_text())
        self.write_patch('b.patch', 'two', 'base two\n', 'incoming two\n')

    def test_registered_unchanged_file_clean(self):
        self.register_unchanged_file()
        (self.tree / 'unrelated').write_text('UNSAVED unrelated\n')
        self.sync()
        self.assertEqual((self.tree / 'registered').read_bytes(), b'registered original\n')
        self.assertEqual((self.tree / 'unrelated').read_text(), 'UNSAVED unrelated\n')
        self.assertEqual((self.tree / 'two').read_text(), 'incoming two\n')

    def test_registered_unchanged_file_dirty(self):
        self.register_unchanged_file()
        (self.tree / 'registered').write_bytes(b'UNSAVED registered\n')
        self.assert_refuses_unchanged()

    def test_registered_unchanged_empty_file_refuses_ambiguous_backup(self):
        self.register_unchanged_file(b'')
        # Quilt's zero-byte backup cannot distinguish this original empty
        # file from an absent original, and pop would remove it.
        self.assert_refuses_unchanged()
        self.assertTrue((self.tree / 'registered').exists())

    def test_removed_clean(self):
        self.series(['a.patch'])
        (self.patches / 'b.patch').unlink()
        self.sync()
        self.assertEqual((self.tree / 'two').read_text(), 'base two\n')

    def test_removed_dirty(self):
        self.series(['a.patch'])
        (self.patches / 'b.patch').unlink()
        (self.tree / 'two').write_text('UNSAVED\n')
        self.assert_refuses_unchanged()

    def test_entire_stack_removed_clean(self):
        self.series([])
        (self.patches / 'a.patch').unlink()
        (self.patches / 'b.patch').unlink()
        self.sync()
        self.assertEqual(worktree_state.applied(self.tree), [])
        self.assertEqual((self.tree / 'one').read_text(), 'base one\n')
        self.assertEqual((self.tree / 'two').read_text(), 'base two\n')

    def test_unsaved_untouched_lower_file_is_preserved(self):
        # A patch that isn't popped must retain its source edits.
        (self.tree / 'one').write_text('UNSAVED lower\n')
        self.write_patch('b.patch', 'two', 'base two\n', 'incoming two\n')
        self.sync()
        self.assertEqual((self.tree / 'one').read_text(), 'UNSAVED lower\n')

    def test_lower_disjoint_edits(self):
        self.write_patch('a.patch', 'one', 'base one\n', 'incoming one\n')
        (self.tree / 'one').write_text('UNSAVED lower\n')
        self.assert_refuses_unchanged()

    def test_reordered_clean(self):
        self.series(['b.patch', 'a.patch'])
        self.sync()
        self.assertEqual(worktree_state.applied(self.tree), ['b.patch', 'a.patch'])

    def test_reordered_dirty(self):
        self.series(['b.patch', 'a.patch'])
        (self.tree / 'one').write_text('UNSAVED\n')
        self.assert_refuses_unchanged()

    def add_file_patch(self):
        self.write_patch('c.patch', 'added', '', 'saved added\n')
        self.series(['a.patch', 'b.patch', 'c.patch'])
        self.quilt('push', '-a', '-q')
        worktree_state.record(self.tree, self.patches)

    def test_added_file_clean(self):
        self.add_file_patch()
        self.write_patch('c.patch', 'added', '', 'incoming added\n')
        self.sync()
        self.assertEqual((self.tree / 'added').read_text(), 'incoming added\n')

    def test_added_file_dirty(self):
        self.add_file_patch()
        self.write_patch('c.patch', 'added', '', 'incoming added\n')
        (self.tree / 'added').write_text('UNSAVED new file\n')
        self.assert_refuses_unchanged()

    def test_deleted_file_recreated_with_unsaved_contents(self):
        (self.tree / 'deleted').write_text('base deleted\n')
        self.write_patch('c.patch', 'deleted', 'base deleted\n', '')
        self.series(['a.patch', 'b.patch', 'c.patch'])
        self.quilt('push', '-a', '-q')
        worktree_state.record(self.tree, self.patches)
        self.series(['a.patch', 'b.patch'])
        (self.patches / 'c.patch').unlink()
        (self.tree / 'deleted').write_text('UNSAVED recreated file\n')
        self.assert_refuses_unchanged()

    def genuine_deletion_patch(self):
        (self.tree / 'deleted').write_text('base deleted\n')
        data = ''.join(difflib.unified_diff(
            ['base deleted\n'], [], fromfile='a/deleted', tofile='/dev/null'))
        (self.patches / 'c.patch').write_text(data)
        self.series(['a.patch', 'b.patch', 'c.patch'])
        self.quilt('push', '-a', '-q')
        self.assertFalse((self.tree / 'deleted').exists())
        worktree_state.record(self.tree, self.patches)
        self.series(['a.patch', 'b.patch'])
        (self.patches / 'c.patch').unlink()

    def test_genuine_deletion_clean(self):
        self.genuine_deletion_patch()
        self.sync()
        self.assertEqual((self.tree / 'deleted').read_text(), 'base deleted\n')

    def test_genuine_deletion_recreated_empty_refuses(self):
        self.genuine_deletion_patch()
        (self.tree / 'deleted').write_bytes(b'')
        self.assert_refuses_unchanged()
        self.assertTrue((self.tree / 'deleted').exists())
        self.assertEqual((self.tree / 'deleted').read_bytes(), b'')

    def test_genuine_deletion_recreated_nonempty_refuses(self):
        self.genuine_deletion_patch()
        (self.tree / 'deleted').write_bytes(b'UNSAVED recreated\n')
        self.assert_refuses_unchanged()

    def deletion_recreation_patches(self):
        (self.tree / 'deleted').write_text('base deleted\n')
        deletion = ''.join(difflib.unified_diff(
            ['base deleted\n'], [], fromfile='a/deleted', tofile='/dev/null'))
        recreation = ''.join(difflib.unified_diff(
            [], ['saved recreation\n'], fromfile='/dev/null', tofile='b/deleted'))
        (self.patches / 'c.patch').write_text(deletion)
        (self.patches / 'd.patch').write_text(recreation)
        self.series(['a.patch', 'b.patch', 'c.patch', 'd.patch'])
        self.quilt('push', '-a', '-q')
        self.assertEqual((self.tree / '.pc' / 'd.patch' / 'deleted').read_bytes(), b'')
        self.assertEqual((self.tree / 'deleted').read_text(), 'saved recreation\n')

    def test_genuine_deletion_recreation_record(self):
        self.deletion_recreation_patches()
        worktree_state.record(self.tree, self.patches)
        self.assertEqual(set(worktree_state.read_record(
            self.tree, worktree_state.applied(self.tree))),
            {'a.patch', 'b.patch', 'c.patch', 'd.patch'})

    def test_genuine_deletion_recreation_sync(self):
        self.deletion_recreation_patches()
        worktree_state.record(self.tree, self.patches)
        self.series(['b.patch', 'a.patch', 'c.patch', 'd.patch'])
        self.sync()
        self.assertEqual((self.tree / 'deleted').read_text(), 'saved recreation\n')

    def test_genuine_deletion_recreation_empty_edit_refuses(self):
        self.deletion_recreation_patches()
        worktree_state.record(self.tree, self.patches)
        self.series(['b.patch', 'a.patch', 'c.patch', 'd.patch'])
        (self.tree / 'deleted').write_bytes(b'')
        self.assert_refuses_unchanged()

    def test_genuine_deletion_recreation_missing_file_refuses(self):
        self.deletion_recreation_patches()
        worktree_state.record(self.tree, self.patches)
        self.series(['b.patch', 'a.patch', 'c.patch', 'd.patch'])
        (self.tree / 'deleted').unlink()
        self.assert_refuses_unchanged()

    def test_overlapping_patch_boundary(self):
        self.write_patch('c.patch', 'one', 'saved one\n', 'upper one\n')
        self.series(['a.patch', 'b.patch', 'c.patch'])
        self.quilt('push', '-a', '-q')
        worktree_state.record(self.tree, self.patches)
        # The lower patch's postimage must be compared with c's preimage,
        # not with the currently visible upper contents.
        self.series(['b.patch', 'a.patch', 'c.patch'])
        self.sync()
        self.assertEqual((self.tree / 'one').read_text(), 'upper one\n')

    def test_missing_record_refuses(self):
        (self.tree / '.pc' / '.rac_applied').unlink()
        self.assert_refuses_unchanged()

    def test_malformed_record_refuses(self):
        (self.tree / '.pc' / '.rac_applied').write_text('not a baseline\n')
        self.assert_refuses_unchanged()

    def test_corrupt_saved_patch_refuses(self):
        fingerprint = worktree_state.read_record(self.tree, ['a.patch', 'b.patch'])['b.patch']
        (self.tree / '.pc' / '.rac_patch_bytes' / fingerprint).write_text('corrupt')
        self.write_patch('b.patch', 'two', 'base two\n', 'incoming two\n')
        self.assert_refuses_unchanged()

    def test_legacy_changed_bytes_refuse(self):
        shutil.rmtree(self.tree / '.pc' / '.rac_patch_bytes')
        self.write_patch('b.patch', 'two', 'base two\n', 'incoming two\n')
        self.assert_refuses_unchanged()

    def test_legacy_removed_bytes_refuse(self):
        shutil.rmtree(self.tree / '.pc' / '.rac_patch_bytes')
        self.series(['a.patch'])
        (self.patches / 'b.patch').unlink()
        self.assert_refuses_unchanged()

    def test_legacy_refreshed_bytes_refuse(self):
        shutil.rmtree(self.tree / '.pc' / '.rac_patch_bytes')
        (self.tree / 'two').write_text('refreshed two\n')
        self.quilt('refresh')
        self.assert_refuses_unchanged()

    def test_legacy_unchanged_bytes_can_be_verified(self):
        shutil.rmtree(self.tree / '.pc' / '.rac_patch_bytes')
        self.series(['b.patch', 'a.patch'])
        self.sync()
        self.assertEqual(worktree_state.applied(self.tree), ['b.patch', 'a.patch'])

    def brand(self):
        (self.tree / 'strings.grd').write_bytes(b'rac\n')
        make_archive(self.tree, 'helium', {'strings.grd': b'Chromium\n'})
        make_archive(self.tree, 'rac', {'strings.grd': b'Helium\n'})
        dev_names.record_expected(self.tree)

    def test_noop_plan_does_not_validate_brand_archives(self):
        self.brand()
        with mock.patch.object(dev_names, 'originals',
                               side_effect=AssertionError('no files will change')):
            worktree_state.plan(self.tree, self.patches)

    def test_noop_sync_preserves_file_bytes_and_timestamps(self):
        self.brand()
        for path in self.tree.rglob('*'):
            if path.is_file():
                os.utime(path, ns=(1_000_000_000, 1_000_000_000))
        before = {p.relative_to(self.tree): (p.read_bytes(), p.stat().st_mtime_ns)
                  for p in self.tree.rglob('*') if p.is_file()}
        self.sync()
        self.sync()
        self.assertEqual(
            {p.relative_to(self.tree): (p.read_bytes(), p.stat().st_mtime_ns)
             for p in self.tree.rglob('*') if p.is_file()}, before)

    def test_noop_sync_still_injects_changed_rac_version(self):
        self.brand()
        shutil.copy2(HERE / 'rac_version.py', self.root / 'devutils' / 'rac')
        version = self.tree / 'chrome' / 'VERSION'
        version.parent.mkdir()
        version.write_text('MAJOR=1\n')
        (self.root / 'rac_version.txt').write_text('0.2.3\n')
        self.sync()
        self.assertEqual(version.read_text(),
                         'MAJOR=1\nRAC_MAJOR=0\nRAC_MINOR=2\nRAC_PATCH=3\n')
        (self.root / 'rac_version.txt').write_text('0.2.4\n')
        self.sync()
        self.assertEqual(version.read_text(),
                         'MAJOR=1\nRAC_MAJOR=0\nRAC_MINOR=2\nRAC_PATCH=4\n')
        stamp = version.stat().st_mtime_ns
        self.sync()
        self.assertEqual(version.stat().st_mtime_ns, stamp)

    def test_noop_leaves_string_edits_until_restoration_is_needed(self):
        self.brand()
        (self.tree / 'strings.grd').write_bytes(b'rac UNSAVED\n')
        before = self.snapshot()
        self.sync()
        self.assertEqual(self.snapshot(), before)
        self.write_patch('b.patch', 'two', 'base two\n', 'incoming two\n')
        self.assert_refuses_unchanged()

    def test_noop_leaves_legacy_names_until_restoration_is_needed(self):
        self.brand()
        (self.tree / '.rac_names' / 'expected.json').unlink()
        before = self.snapshot()
        self.sync()
        self.assertEqual(self.snapshot(), before)
        self.write_patch('b.patch', 'two', 'base two\n', 'incoming two\n')
        self.assert_refuses_unchanged()

    def test_noop_does_not_adopt_legacy_patch_bytes(self):
        self.brand()
        shutil.rmtree(self.tree / '.pc' / '.rac_patch_bytes')
        before = self.snapshot()
        self.sync()
        self.assertEqual(self.snapshot(), before)
        self.write_patch('b.patch', 'two', 'base two\n', 'incoming two\n')
        self.assert_refuses_unchanged()

    def test_unsub_then_sync_reapplies_both_name_passes(self):
        self.brand()
        dev_names.unsub(self.tree)
        self.assertEqual(dev_names.status(self.tree), 'not applied')
        self.sync()
        self.assertEqual(dev_names.status(self.tree), 'applied')
        self.assertEqual((self.tree / 'strings.grd').read_bytes(), b'Chromium\n')

    def test_partial_names_sync_completes_remaining_pass(self):
        make_archive(self.tree, 'helium', {'strings.grd': b'Chromium\n'})
        (self.tree / 'strings.grd').write_bytes(b'Helium\n')
        dev_names.record_expected(self.tree)
        self.assertEqual(dev_names.status(self.tree), 'partial')
        self.sync()
        self.assertEqual(dev_names.status(self.tree), 'applied')
        self.assertEqual((self.tree / 'strings.grd').read_bytes(), b'Helium\n')

    def test_partial_names_with_string_edits_refuse(self):
        make_archive(self.tree, 'helium', {'strings.grd': b'Chromium\n'})
        (self.tree / 'strings.grd').write_bytes(b'Helium\n')
        dev_names.record_expected(self.tree)
        (self.tree / 'strings.grd').write_bytes(b'Helium UNSAVED\n')
        self.assert_refuses_unchanged()

    def test_names_baseline_without_archives_refuses(self):
        self.brand()
        for name, _ in dev_names.PASSES:
            dev_names.backup_path(self.tree, name).unlink()
        self.assert_refuses_unchanged()

    def test_branded_unrecorded_patch_still_verifies_postimages(self):
        self.append_refreshed_patch()
        self.brand()
        (self.tree / 'three').write_bytes(b'UNSAVED appended\n')
        self.assert_refuses_unchanged()

    def test_new_patch_checks_branding_before_push(self):
        self.brand()
        (self.tree / 'strings.grd').write_bytes(b'rac UNSAVED\n')
        self.write_patch('c.patch', 'three', '', 'incoming three\n')
        self.series(['a.patch', 'b.patch', 'c.patch'])
        self.assert_refuses_unchanged()

    def test_brand_archives_unchanged_when_patch_guard_refuses(self):
        self.brand()
        self.write_patch('b.patch', 'two', 'base two\n', 'incoming two\n')
        (self.tree / 'two').write_text('UNSAVED\n')
        self.assert_refuses_unchanged()

    def test_plan_checks_brand_archives_only_once(self):
        self.brand()
        self.write_patch('b.patch', 'two', 'base two\n', 'incoming two\n')
        with mock.patch.object(dev_names, 'originals', wraps=dev_names.originals) as check:
            worktree_state.plan(self.tree, self.patches)
        self.assertEqual(check.call_count, 1)

    def test_branded_source_edits_refuse_before_pop(self):
        self.brand()
        (self.tree / 'strings.grd').write_bytes(b'rac UNSAVED\n')
        self.write_patch('b.patch', 'two', 'base two\n', 'incoming two\n')
        self.assert_refuses_unchanged()

    def test_legacy_names_refuse_before_pop(self):
        self.brand()
        (self.tree / '.rac_names' / 'expected.json').unlink()
        self.write_patch('b.patch', 'two', 'base two\n', 'incoming two\n')
        self.assert_refuses_unchanged()

    def string_patch(self, unbranded='Chromium saved\n'):
        (self.tree / 'strings.grd').write_bytes(b'Chromium base\n')
        self.write_patch('c.patch', 'strings.grd', 'Chromium base\n', 'Chromium saved\n')
        self.series(['a.patch', 'b.patch', 'c.patch'])
        self.quilt('push', '-a', '-q')
        worktree_state.record(self.tree, self.patches)
        make_archive(self.tree, 'helium', {'strings.grd': unbranded.encode()})
        make_archive(self.tree, 'rac', {'strings.grd': b'Helium saved\n'})
        (self.tree / 'strings.grd').write_bytes(b'rac saved\n')
        dev_names.record_expected(self.tree)
        self.write_patch('c.patch', 'strings.grd', 'Chromium base\n', 'Chromium incoming\n')

    def test_branded_patch_comparison_uses_temporary_originals(self):
        self.string_patch()
        self.sync()
        # Fixture naming scripts are deliberately no-ops.
        self.assertEqual((self.tree / 'strings.grd').read_bytes(), b'Chromium incoming\n')

    def test_prebranding_unsaved_string_edits_are_not_hidden_by_archive(self):
        self.string_patch('Chromium UNSAVED\n')
        self.assert_refuses_unchanged()

    def test_clone_baseline_uses_base_versions(self):
        base = self.root / 'base-patches'
        shutil.copytree(self.patches, base)
        # A built main checkout can legitimately be unmerged for committing.
        (base / 'series.merged').unlink()
        base_before = {p.relative_to(base): p.read_bytes()
                       for p in base.rglob('*') if p.is_file()}
        (self.tree / '.pc' / '.rac_applied').unlink()
        shutil.rmtree(self.tree / '.pc' / '.rac_patch_bytes')
        self.write_patch('b.patch', 'two', 'base two\n', 'incoming two\n')
        worktree_state.seed(self.tree, base)
        fingerprint = worktree_state.read_record(self.tree, ['a.patch', 'b.patch'])['b.patch']
        self.assertEqual((self.tree / '.pc' / '.rac_patch_bytes' / fingerprint).read_bytes(),
                         (base / 'b.patch').read_bytes())
        self.assertEqual({p.relative_to(base): p.read_bytes()
                          for p in base.rglob('*') if p.is_file()}, base_before)
        self.sync()
        self.assertEqual((self.tree / 'two').read_text(), 'incoming two\n')

    def test_unmerged_base_seeds_hash_only_record(self):
        base = self.root / 'base-patches'
        shutil.copytree(self.patches, base)
        (base / 'series.merged').unlink()
        shutil.rmtree(self.tree / '.pc' / '.rac_patch_bytes')
        record = (self.tree / '.pc' / '.rac_applied').read_bytes()
        self.write_patch('b.patch', 'two', 'base two\n', 'incoming two\n')
        worktree_state.seed(self.tree, base)
        self.assertEqual((self.tree / '.pc' / '.rac_applied').read_bytes(), record)
        fingerprint = worktree_state.read_record(self.tree, ['a.patch', 'b.patch'])['b.patch']
        self.assertEqual((self.tree / '.pc' / '.rac_patch_bytes' / fingerprint).read_bytes(),
                         (base / 'b.patch').read_bytes())
        self.sync()
        self.assertEqual((self.tree / 'two').read_text(), 'incoming two\n')

    def test_unmerged_base_preserves_saved_record(self):
        base = self.root / 'base-patches'
        shutil.copytree(self.patches, base)
        (base / 'series.merged').unlink()
        # Even a replaced base patch cannot overwrite the clone's saved bytes.
        (base / 'b.patch').write_text(patch_text('two', 'base two\n', 'new base two\n'))
        self.write_patch('b.patch', 'two', 'base two\n', 'incoming two\n')
        before = self.snapshot()
        worktree_state.seed(self.tree, base)
        self.assertEqual(self.snapshot(), before)
        self.sync()
        self.assertEqual((self.tree / 'two').read_text(), 'incoming two\n')

    def test_unmerged_base_hash_only_record_refuses_replaced_base_patch(self):
        base = self.root / 'base-patches'
        shutil.copytree(self.patches, base)
        (base / 'series.merged').unlink()
        shutil.rmtree(self.tree / '.pc' / '.rac_patch_bytes')
        (base / 'b.patch').write_text(patch_text('two', 'base two\n', 'new base two\n'))
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, 'missing original patch bytes'):
            worktree_state.seed(self.tree, base)
        self.assertEqual(self.snapshot(), before)

    def test_unmerged_base_without_record_refuses_wrong_source_version(self):
        base = self.root / 'base-patches'
        shutil.copytree(self.patches, base)
        (base / 'series.merged').unlink()
        (self.tree / '.pc' / '.rac_applied').unlink()
        shutil.rmtree(self.tree / '.pc' / '.rac_patch_bytes')
        # Incoming worktree patches still match the source; seeding must
        # nevertheless verify only the supplied base versions.
        (base / 'b.patch').write_text(patch_text('two', 'base two\n', 'new base two\n'))
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, 'unverifiable saved patch'):
            worktree_state.seed(self.tree, base)
        self.assertEqual(self.snapshot(), before)

    def unmerge_mixed_base(self):
        """Use Helium's real unmerge, operating only on a temporary base."""
        self.quilt('pop', '-a', '-q')
        names = ['helium/core/upstream.patch', 'mac/platform.patch', 'rac/feature.patch']
        for name in names:
            (self.patches / name).parent.mkdir(parents=True, exist_ok=True)
        (self.patches / 'a.patch').rename(self.patches / names[0])
        (self.patches / 'b.patch').rename(self.patches / names[1])
        (self.tree / 'three').write_text('base three\n')
        self.write_patch(names[2], 'three', 'base three\n', 'saved three\n')
        self.series(names)
        self.quilt('push', '-a', '-q')
        worktree_state.record(self.tree, self.patches)

        base = self.root / 'base'
        patches = base / 'patches'
        core = base / 'helium-chromium' / 'patches'
        shutil.copytree(self.patches, patches)
        core.mkdir(parents=True)
        (patches / 'series.prepend').write_text(names[0] + '\n')
        (patches / 'series.orig').write_text('\n'.join(names[1:]) + '\n')
        script = """
import importlib.util, pathlib, sys
spec = importlib.util.spec_from_file_location('update_platform_patches', sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
sys.exit(0 if module.unmerge_platform_patches(
    pathlib.Path(sys.argv[2]), pathlib.Path(sys.argv[3])) else 1)
"""
        # -B prevents even imports from writing into the real submodule.
        subprocess.run(
            [sys.executable, '-B', '-c', script,
             HERE.parents[1] / 'helium-chromium' / 'devutils' / 'update_platform_patches.py',
             patches, core], cwd=base, check=True, capture_output=True)
        self.assertFalse((patches / names[0]).exists())
        self.assertTrue((core / names[0]).exists())
        self.assertFalse((patches / 'series.merged').exists())
        self.assertEqual((core / 'series').read_text(), names[0] + '\n')
        self.assertEqual((patches / 'series').read_text(), '\n'.join(names[1:]) + '\n')
        originals = {names[0]: (core / names[0]).read_bytes(),
                     **{name: (patches / name).read_bytes() for name in names[1:]}}
        for name, file in zip(names, ['one', 'two', 'three']):
            self.write_patch(name, file, f'base {file}\n', f'incoming {file}\n')
        return base, patches, names, originals

    def base_snapshot(self, base):
        return {p.relative_to(base): (p.stat().st_mode, p.stat().st_mtime_ns,
                                     p.read_bytes() if p.is_file() else None)
                for p in [base, *base.rglob('*')]}

    def test_real_unmerged_mixed_base_seeds_missing_record(self):
        base, patches, names, originals = self.unmerge_mixed_base()
        (self.tree / '.pc' / '.rac_applied').unlink()
        shutil.rmtree(self.tree / '.pc' / '.rac_patch_bytes')
        before = self.base_snapshot(base)
        worktree_state.seed(self.tree, patches)
        recorded = worktree_state.read_record(self.tree, names)
        for name in names:
            self.assertEqual(recorded[name], worktree_state.digest(originals[name]))
            self.assertEqual((self.tree / '.pc' / '.rac_patch_bytes' /
                              recorded[name]).read_bytes(), originals[name])
        self.assertEqual(self.base_snapshot(base), before)
        self.sync()
        for file in ['one', 'two', 'three']:
            self.assertEqual((self.tree / file).read_text(), f'incoming {file}\n')

    def test_real_unmerged_mixed_base_seeds_hash_only_record(self):
        base, patches, names, originals = self.unmerge_mixed_base()
        shutil.rmtree(self.tree / '.pc' / '.rac_patch_bytes')
        record = (self.tree / '.pc' / '.rac_applied').read_bytes()
        before = self.base_snapshot(base)
        worktree_state.seed(self.tree, patches)
        self.assertEqual((self.tree / '.pc' / '.rac_applied').read_bytes(), record)
        recorded = worktree_state.read_record(self.tree, names)
        for name in names:
            self.assertEqual((self.tree / '.pc' / '.rac_patch_bytes' /
                              recorded[name]).read_bytes(), originals[name])
        self.assertEqual(self.base_snapshot(base), before)
        self.sync()
        for file in ['one', 'two', 'three']:
            self.assertEqual((self.tree / file).read_text(), f'incoming {file}\n')

    def test_real_unmerged_mixed_base_preserves_full_saved_record(self):
        base, patches, names, _ = self.unmerge_mixed_base()
        # Cached originals remain sufficient even when base patch files
        # have subsequently been removed.
        for name in names:
            folder = patches if name != names[0] else base / 'helium-chromium' / 'patches'
            (folder / name).unlink()
        base_before = self.base_snapshot(base)
        clone_before = self.snapshot()
        worktree_state.seed(self.tree, patches)
        self.assertEqual(self.base_snapshot(base), base_before)
        self.assertEqual(self.snapshot(), clone_before)
        self.sync()
        for file in ['one', 'two', 'three']:
            self.assertEqual((self.tree / file).read_text(), f'incoming {file}\n')

    def test_real_unmerged_core_hash_mismatch_refuses_without_writes(self):
        base, patches, names, _ = self.unmerge_mixed_base()
        shutil.rmtree(self.tree / '.pc' / '.rac_patch_bytes')
        core = base / 'helium-chromium' / 'patches'
        (core / names[0]).write_bytes((self.patches / names[0]).read_bytes())
        base_before = self.base_snapshot(base)
        clone_before = self.snapshot()
        with self.assertRaisesRegex(ValueError, 'missing original patch bytes'):
            worktree_state.seed(self.tree, patches)
        self.assertEqual(self.base_snapshot(base), base_before)
        self.assertEqual(self.snapshot(), clone_before)

    def test_real_unmerged_core_wrong_postimage_refuses_without_writes(self):
        base, patches, names, _ = self.unmerge_mixed_base()
        (self.tree / '.pc' / '.rac_applied').unlink()
        shutil.rmtree(self.tree / '.pc' / '.rac_patch_bytes')
        core = base / 'helium-chromium' / 'patches'
        (core / names[0]).write_bytes((self.patches / names[0]).read_bytes())
        base_before = self.base_snapshot(base)
        clone_before = self.snapshot()
        with self.assertRaisesRegex(ValueError, 'unverifiable saved patch'):
            worktree_state.seed(self.tree, patches)
        self.assertEqual(self.base_snapshot(base), base_before)
        self.assertEqual(self.snapshot(), clone_before)

    def test_sync_does_not_fall_back_to_incoming_core_patch(self):
        _, _, names, originals = self.unmerge_mixed_base()
        shutil.rmtree(self.tree / '.pc' / '.rac_patch_bytes')
        core = self.root / 'helium-chromium' / 'patches'
        path = core / names[0]
        path.parent.mkdir(parents=True)
        path.write_bytes(originals[names[0]])
        (self.patches / names[0]).unlink()
        # The incoming core copy matches the original hash, but is not an
        # authorized substitute for a missing desired merged patch.
        self.assert_refuses_unchanged()


class PathTest(unittest.TestCase):
    def test_minimal_intel_arm_and_existing_path(self):
        text = (HERE / 'worktree.sh').read_text()
        bootstrap = text[text.index('for prefix in '):text.index('for tool in ')]
        with tempfile.TemporaryDirectory(prefix='rac-test-path-') as directory:
            root = Path(directory)
            intel, arm = root / 'intel', root / 'arm'
            intel.mkdir()
            arm.mkdir()
            # Model the prefixes, not the host's CPU or installed Homebrew.
            bootstrap = bootstrap.replace('/usr/local/bin', str(intel))
            bootstrap = bootstrap.replace('/opt/homebrew/bin', str(arm))
            for name, prefix in [('intel', intel), ('arm', arm)]:
                tool = prefix / name
                tool.write_text('#!/bin/sh\nprintf found\n')
                tool.chmod(0o755)
            for initial, expected in [
                    ('/usr/bin:/bin', f'{arm}:{intel}:/usr/bin:/bin'),
                    (f'{intel}:/usr/bin:/bin', f'{arm}:{intel}:/usr/bin:/bin'),
                    (f'{intel}:{arm}:/usr/bin:/bin', f'{intel}:{arm}:/usr/bin:/bin'),
                    (f'{arm}:/usr/bin:/bin', f'{intel}:{arm}:/usr/bin:/bin')]:
                result = subprocess.run(['/bin/bash', '-c', bootstrap +
                                         '\nprintf "%s\\n" "$PATH"\nintel\narm\n'],
                                        env={'PATH': initial}, text=True, capture_output=True,
                                        check=True)
                self.assertEqual(result.stdout, expected + '\nfoundfound')
            # Intel-only install: the ARM directory is absent.
            (arm / 'arm').unlink()
            arm.rmdir()
            result = subprocess.run(['/bin/bash', '-c', bootstrap + '\nprintf "%s" "$PATH"'],
                                    env={'PATH': '/usr/bin:/bin'}, text=True,
                                    capture_output=True, check=True)
            self.assertEqual(result.stdout, f'{intel}:/usr/bin:/bin')
            # ARM-only install, also under the same minimal PATH.
            (intel / 'intel').unlink()
            intel.rmdir()
            arm.mkdir()
            tool = arm / 'arm'
            tool.write_text('#!/bin/sh\nprintf found\n')
            tool.chmod(0o755)
            result = subprocess.run(['/bin/bash', '-c', bootstrap +
                                     '\nprintf "%s\\n" "$PATH"\narm\n'],
                                    env={'PATH': '/usr/bin:/bin'}, text=True,
                                    capture_output=True, check=True)
            self.assertEqual(result.stdout, f'{arm}:/usr/bin:/bin\nfound')


if __name__ == '__main__':
    unittest.main()
