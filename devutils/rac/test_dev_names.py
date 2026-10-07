#!/usr/bin/env python3
# Copyright 2025 The rac Authors
# You can use, redistribute, and/or modify this source code under
# the terms of the GPL-3.0 license that can be found in the LICENSE file.
"""Focused tests; never read or mutate a real Chromium tree."""

from pathlib import Path
import io
import json
import os
import stat
import tarfile
import tempfile
import unittest
from unittest import mock

import dev_names


def make_archive(tree, name, contents):
    folder = tree / dev_names.STATE_DIR
    folder.mkdir(exist_ok=True)
    with tarfile.open(folder / f'{name}.tar', 'w:gz') as archive:
        for path, data in contents.items():
            member = tarfile.TarInfo(path)
            member.size = len(data)
            archive.addfile(member, io.BytesIO(data))


class NamesTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='rac-test-names-')
        self.addCleanup(self.temporary.cleanup)
        self.tree = Path(self.temporary.name)
        (self.tree / 'OWNERS').write_text('fixture\n')
        (self.tree / 'strings.grd').write_bytes(b'rac\n')
        make_archive(self.tree, 'helium', {'strings.grd': b'Chromium\n'})
        make_archive(self.tree, 'rac', {'strings.grd': b'Helium\n'})
        dev_names.record_expected(self.tree)

    def snapshot(self):
        return {p.relative_to(self.tree).as_posix(): p.read_bytes()
                for p in self.tree.rglob('*') if p.is_file()}

    def add_second_file(self):
        (self.tree / 'other.grd').write_bytes(b'rac other\n')
        make_archive(self.tree, 'helium',
                     {'strings.grd': b'Chromium\n', 'other.grd': b'Chromium other\n'})
        make_archive(self.tree, 'rac',
                     {'strings.grd': b'Helium\n', 'other.grd': b'Helium other\n'})
        dev_names.record_expected(self.tree)

    def test_second_write_failure_rolls_back_and_can_retry(self):
        self.add_second_file()
        before = self.snapshot()
        write_bytes = Path.write_bytes
        failed = False

        def fail_second(path, data):
            nonlocal failed
            if path == self.tree / 'other.grd' and not failed:
                failed = True
                raise OSError('injected second write failure')
            return write_bytes(path, data)

        with mock.patch.object(Path, 'write_bytes', fail_second):
            with self.assertRaisesRegex(OSError, 'injected second write failure'):
                dev_names.unsub(self.tree)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(dev_names.status(self.tree), 'applied')
        dev_names.unsub(self.tree)
        self.assertEqual((self.tree / 'strings.grd').read_bytes(), b'Chromium\n')
        self.assertEqual((self.tree / 'other.grd').read_bytes(), b'Chromium other\n')

    def test_partial_failed_write_restores_the_failed_target_too(self):
        self.add_second_file()
        before = self.snapshot()
        write_bytes = Path.write_bytes
        failed = False

        def truncate_then_fail(path, data):
            nonlocal failed
            if path == self.tree / 'other.grd' and not failed:
                failed = True
                write_bytes(path, b'part')
                raise OSError('injected partial write failure')
            return write_bytes(path, data)

        with mock.patch.object(Path, 'write_bytes', truncate_then_fail):
            with self.assertRaisesRegex(OSError, 'injected partial write failure'):
                dev_names.unsub(self.tree)
        self.assertEqual(self.snapshot(), before)
        dev_names.unsub(self.tree)
        self.assertEqual((self.tree / 'other.grd').read_bytes(), b'Chromium other\n')

    def test_timestamp_failure_restores_contents_mode_and_mtime(self):
        self.add_second_file()
        paths = [self.tree / name for name in ['strings.grd', 'other.grd']]
        for path in paths:
            path.chmod(0o640)
            os.utime(path, ns=(1_700_000_000_000_000_000, 1_700_000_001_000_000_000))
        before = self.snapshot()
        times = {path: path.stat().st_mtime_ns for path in paths}
        utime = os.utime
        failed = False

        def fail_second(path, *args, **kwargs):
            nonlocal failed
            if path == paths[1] and not args and not kwargs and not failed:
                failed = True
                raise OSError('injected timestamp failure')
            return utime(path, *args, **kwargs)

        with mock.patch.object(dev_names.os, 'utime', fail_second):
            with self.assertRaisesRegex(OSError, 'injected timestamp failure'):
                dev_names.unsub(self.tree)
        self.assertEqual(self.snapshot(), before)
        for path in paths:
            self.assertEqual(path.stat().st_mtime_ns, times[path])
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o640)
        dev_names.unsub(self.tree)
        for path in paths:
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o640)

    def test_staging_failure_never_writes_sources_or_deletes_archives(self):
        self.add_second_file()
        before = self.snapshot()
        copy2 = dev_names.shutil.copy2

        def fail_second(source, destination):
            if source == self.tree / 'other.grd':
                raise OSError('injected staging failure')
            return copy2(source, destination)

        with mock.patch.object(dev_names.shutil, 'copy2', fail_second):
            with self.assertRaisesRegex(OSError, 'injected staging failure'):
                dev_names.unsub(self.tree)
        self.assertEqual(self.snapshot(), before)
        dev_names.unsub(self.tree)

    def test_archive_cleanup_failure_rolls_back_all_files_and_archives(self):
        self.add_second_file()
        before = self.snapshot()
        archive = self.tree / dev_names.STATE_DIR / 'helium.tar'
        archive.chmod(0o640)
        os.utime(archive, ns=(1_700_000_000_000_000_000, 1_700_000_001_000_000_000))
        unlink = Path.unlink

        def fail_archive(path, *args, **kwargs):
            if path == archive:
                raise OSError('injected archive cleanup failure')
            return unlink(path, *args, **kwargs)

        with mock.patch.object(Path, 'unlink', fail_archive):
            with self.assertRaisesRegex(OSError, 'injected archive cleanup failure'):
                dev_names.unsub(self.tree)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(stat.S_IMODE(archive.stat().st_mode), 0o640)
        self.assertEqual(archive.stat().st_mtime_ns, 1_700_000_001_000_000_000)
        dev_names.unsub(self.tree)

    def test_ledger_cleanup_failure_restores_already_deleted_archives(self):
        before = self.snapshot()
        ledger = self.tree / dev_names.STATE_DIR / 'expected.json'
        unlink = Path.unlink

        def fail_ledger(path, *args, **kwargs):
            if path == ledger:
                raise OSError('injected ledger cleanup failure')
            return unlink(path, *args, **kwargs)

        with mock.patch.object(Path, 'unlink', fail_ledger):
            with self.assertRaisesRegex(OSError, 'injected ledger cleanup failure'):
                dev_names.unsub(self.tree)
        self.assertEqual(self.snapshot(), before)
        dev_names.unsub(self.tree)
        self.assertEqual(dev_names.status(self.tree), 'not applied')

    def test_deleted_ledger_before_cleanup_error_is_also_restored(self):
        before = self.snapshot()
        ledger = self.tree / dev_names.STATE_DIR / 'expected.json'
        unlink = Path.unlink

        def delete_then_fail(path, *args, **kwargs):
            result = unlink(path, *args, **kwargs)
            if path == ledger:
                raise OSError('injected error after ledger deletion')
            return result

        with mock.patch.object(Path, 'unlink', delete_then_fail):
            with self.assertRaisesRegex(OSError, 'injected error after ledger deletion'):
                dev_names.unsub(self.tree)
        self.assertEqual(self.snapshot(), before)
        dev_names.unsub(self.tree)

    def test_readonly_source_is_not_replaced_or_made_writable(self):
        path = self.tree / 'strings.grd'
        path.chmod(0o444)
        inode = path.stat().st_ino
        before = self.snapshot()
        write_bytes = Path.write_bytes

        def deny_source_write(target, data):
            # Inject permissions deterministically, without relying on UID.
            if target == path:
                raise PermissionError('injected readonly source')
            return write_bytes(target, data)

        with mock.patch.object(Path, 'write_bytes', deny_source_write):
            with self.assertRaisesRegex(PermissionError, 'injected readonly source'):
                dev_names.unsub(self.tree)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(path.stat().st_ino, inode)
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o444)

    def test_failed_rollback_retains_every_recovery_copy_and_metadata(self):
        self.add_second_file()
        before = self.snapshot()
        write_bytes = Path.write_bytes

        def fail_write_and_rollback(path, data):
            if path == self.tree / 'other.grd' and data == b'Chromium other\n':
                write_bytes(path, b'partial')
                raise OSError('injected source failure')
            if path == self.tree / 'strings.grd' and data == b'rac\n':
                raise OSError('injected rollback failure')
            return write_bytes(path, data)

        with mock.patch.object(Path, 'write_bytes', fail_write_and_rollback):
            with self.assertRaisesRegex(OSError, 'names rollback failed') as raised:
                dev_names.unsub(self.tree)
        folders = list((self.tree / dev_names.STATE_DIR).glob('unsub-*'))
        self.assertEqual(len(folders), 1)
        recovery = folders[0]
        self.assertIn(str(recovery), str(raised.exception))
        self.assertIn('injected rollback failure', str(raised.exception))
        self.assertEqual((self.tree / 'other.grd').read_bytes(), b'rac other\n')
        metadata = json.loads((recovery / 'metadata.json').read_text())
        for name in ['strings.grd', 'other.grd', '.rac_names/helium.tar',
                     '.rac_names/rac.tar', '.rac_names/expected.json']:
            self.assertEqual((recovery / 'files' / name).read_bytes(), before[name])
            self.assertIn('mtime_ns', metadata[name])
            self.assertIn('atime_ns', metadata[name])
            self.assertIn('mode', metadata[name])
        # The retained copies allow recovery after the filesystem fault clears.
        for name, info in metadata.items():
            path = self.tree / name
            path.write_bytes((recovery / 'files' / name).read_bytes())
            path.chmod(info['mode'])
            os.utime(path, ns=(info['atime_ns'], info['mtime_ns']))
        dev_names.unsub(self.tree)
        self.assertEqual((self.tree / 'strings.grd').read_bytes(), b'Chromium\n')
        self.assertTrue(recovery.exists())

    def test_failed_archive_rollback_retains_deleted_archive_and_ledger(self):
        before = self.snapshot()
        ledger = self.tree / dev_names.STATE_DIR / 'expected.json'
        archive = self.tree / dev_names.STATE_DIR / 'rac.tar'
        unlink = Path.unlink
        write_bytes = Path.write_bytes

        def fail_cleanup(path, *args, **kwargs):
            if path == ledger:
                raise OSError('injected ledger cleanup failure')
            return unlink(path, *args, **kwargs)

        def fail_archive_rollback(path, data):
            if path == archive:
                raise OSError('injected archive rollback failure')
            return write_bytes(path, data)

        with mock.patch.object(Path, 'unlink', fail_cleanup), \
                mock.patch.object(Path, 'write_bytes', fail_archive_rollback):
            with self.assertRaisesRegex(OSError, 'names rollback failed'):
                dev_names.unsub(self.tree)
        folders = list((self.tree / dev_names.STATE_DIR).glob('unsub-*'))
        self.assertEqual(len(folders), 1)
        self.assertEqual((folders[0] / 'files/.rac_names/rac.tar').read_bytes(),
                         before['.rac_names/rac.tar'])
        self.assertEqual((folders[0] / 'files/.rac_names/expected.json').read_bytes(),
                         before['.rac_names/expected.json'])
        self.assertEqual((self.tree / 'strings.grd').read_bytes(), before['strings.grd'])

    def test_failed_timestamp_rollback_retains_data_and_metadata(self):
        before = self.snapshot()
        path = self.tree / 'strings.grd'
        utime = os.utime

        def fail_source_timestamp(target, *args, **kwargs):
            if target == path:
                raise OSError('injected persistent timestamp failure')
            return utime(target, *args, **kwargs)

        with mock.patch.object(dev_names.os, 'utime', fail_source_timestamp):
            with self.assertRaisesRegex(OSError, 'names rollback failed') as raised:
                dev_names.unsub(self.tree)
        self.assertIn('injected persistent timestamp failure', str(raised.exception))
        recovery, = (self.tree / dev_names.STATE_DIR).glob('unsub-*')
        self.assertEqual((recovery / 'files/strings.grd').read_bytes(), before['strings.grd'])
        self.assertEqual(path.read_bytes(), before['strings.grd'])
        self.assertIn('strings.grd', json.loads((recovery / 'metadata.json').read_text()))
        self.assertEqual(dev_names.status(self.tree), 'applied')
        dev_names.unsub(self.tree)

    def test_recovery_cleanup_failure_after_success_keeps_valid_unbranded_state(self):
        with mock.patch.object(dev_names.shutil, 'rmtree',
                               side_effect=OSError('injected recovery cleanup failure')):
            with self.assertRaisesRegex(OSError, 'names reverted, but recovery cleanup failed'):
                dev_names.unsub(self.tree)
        self.assertEqual((self.tree / 'strings.grd').read_bytes(), b'Chromium\n')
        self.assertEqual(dev_names.originals(self.tree), {})
        self.assertEqual(dev_names.status(self.tree), 'not applied')
        self.assertEqual(len(list((self.tree / dev_names.STATE_DIR).glob('unsub-*'))), 1)
        dev_names.unsub(self.tree)

    def test_recovery_cleanup_failure_after_rollback_reports_restored_state(self):
        write_bytes = Path.write_bytes

        def fail_source(path, data):
            if path == self.tree / 'strings.grd' and data == b'Chromium\n':
                raise OSError('injected source failure')
            return write_bytes(path, data)

        with mock.patch.object(Path, 'write_bytes', fail_source), \
                mock.patch.object(dev_names.shutil, 'rmtree',
                                  side_effect=OSError('injected recovery cleanup failure')):
            with self.assertRaisesRegex(OSError, 'pre-restore names state preserved') as raised:
                dev_names.unsub(self.tree)
        self.assertIn('injected recovery cleanup failure', str(raised.exception))
        self.assertEqual(dev_names.originals(self.tree), {'strings.grd': b'Chromium\n'})
        self.assertEqual(dev_names.status(self.tree), 'applied')
        dev_names.unsub(self.tree)

    def test_originals_are_nonmutating(self):
        before = self.snapshot()
        self.assertEqual(dev_names.originals(self.tree), {'strings.grd': b'Chromium\n'})
        self.assertEqual(self.snapshot(), before)

    def test_safe_unsub(self):
        dev_names.unsub(self.tree)
        self.assertEqual((self.tree / 'strings.grd').read_bytes(), b'Chromium\n')
        self.assertEqual(dev_names.status(self.tree), 'not applied')
        self.assertFalse((self.tree / '.rac_names' / 'expected.json').exists())

    def test_edited_file_refuses_unsub_and_preserves_archives(self):
        (self.tree / 'strings.grd').write_bytes(b'rac UNSAVED\n')
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, 'edited branded string'):
            dev_names.unsub(self.tree)
        self.assertEqual(self.snapshot(), before)

    def test_empty_branded_file_can_be_restored(self):
        (self.tree / 'strings.grd').write_bytes(b'')
        dev_names.record_expected(self.tree)
        dev_names.unsub(self.tree)
        self.assertEqual((self.tree / 'strings.grd').read_bytes(), b'Chromium\n')

    def test_deleted_empty_branded_file_refuses_unsub(self):
        (self.tree / 'strings.grd').write_bytes(b'')
        dev_names.record_expected(self.tree)
        (self.tree / 'strings.grd').unlink()
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, 'edited branded string'):
            dev_names.unsub(self.tree)
        self.assertEqual(self.snapshot(), before)

    def test_source_bytes_distinguishes_empty_and_missing(self):
        path = self.tree / 'empty'
        path.write_bytes(b'')
        self.assertEqual(dev_names.source_bytes(self.tree, 'empty', missing=True), b'')
        path.unlink()
        self.assertIsNone(dev_names.source_bytes(self.tree, 'empty', missing=True))

    def test_lower_pass_file_is_checked_before_either_pass_restores(self):
        (self.tree / 'other.grd').write_bytes(b'Helium UNSAVED\n')
        make_archive(self.tree, 'helium',
                     {'strings.grd': b'Chromium\n', 'other.grd': b'Chromium\n'})
        # Model the known post-substitution contents, then a later edit.
        (self.tree / 'other.grd').write_bytes(b'Helium\n')
        dev_names.record_expected(self.tree)
        (self.tree / 'other.grd').write_bytes(b'Helium UNSAVED\n')
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, 'edited branded string'):
            dev_names.unsub(self.tree)
        self.assertEqual(self.snapshot(), before)

    def test_legacy_archives_refuse_without_adopting_live_files(self):
        (self.tree / '.rac_names' / 'expected.json').unlink()
        before = self.snapshot()
        for operation in [dev_names.unsub, dev_names.sub]:
            with self.assertRaisesRegex(ValueError, 'legacy names archives'):
                operation(self.tree)
            self.assertEqual(self.snapshot(), before)

    def test_corrupt_archive_refuses(self):
        make_archive(self.tree, 'rac', {'strings.grd': b'Wrong\n'})
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, 'verified baseline'):
            dev_names.unsub(self.tree)
        self.assertEqual(self.snapshot(), before)

    def test_sub_records_expected_completed_passes(self):
        dev_names.unsub(self.tree)

        def substitute(command, **_kwargs):
            name = 'helium' if command[1] == 'helium-script' else 'rac'
            path = self.tree / 'strings.grd'
            make_archive(self.tree, name, {'strings.grd': path.read_bytes()})
            path.write_bytes(b'Helium\n' if name == 'helium' else b'rac\n')
            return mock.Mock(returncode=0, stdout='done\n')

        with mock.patch.object(dev_names, 'PASSES',
                               [('helium', 'helium-script'), ('rac', 'rac-script')]), \
                mock.patch.object(dev_names.subprocess, 'run', side_effect=substitute):
            dev_names.sub(self.tree)
        baseline = json.loads((self.tree / '.rac_names' / 'expected.json').read_text())
        self.assertEqual(baseline['files']['strings.grd'], dev_names.digest(b'rac\n'))
        dev_names.unsub(self.tree)
        self.assertEqual((self.tree / 'strings.grd').read_bytes(), b'Chromium\n')


if __name__ == '__main__':
    unittest.main()
