#!/usr/bin/env python3

# Copyright 2025 The rac Authors
# You can use, redistribute, and/or modify this source code under
# the terms of the GPL-3.0 license that can be found in the LICENSE file.
"""Tests for dev_names.py with fake name passes. Only temporary folders.

Run from the repository root:
    python3 -m unittest discover -s devutils/rac -p 'test_*.py' -v
"""

from pathlib import Path
import io
import json
import os
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest import mock

import dev_names


def make_archive(tree, name, contents):
    """Writes a pass backup holding `contents` ({path: bytes})."""
    backup = dev_names.backup_path(tree, name)
    backup.parent.mkdir(exist_ok=True)
    with tarfile.open(backup, 'w:gz') as tar:
        for path, data in contents.items():
            info = tarfile.TarInfo(path)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))


class NamesTest(unittest.TestCase):

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='rac-test-dev-names-')
        self.addCleanup(temporary.cleanup)
        self.folder = Path(temporary.name).resolve()
        self.tree = self.folder / 'src'
        (self.tree / 'ui').mkdir(parents=True)
        (self.tree / 'OWNERS').write_text('fixture\n')
        self.grd = self.tree / 'ui' / 'strings.grd'
        self.xtb = self.tree / 'ui' / 'strings_fr.xtb'
        # Both passes changed the .grd; only the helium pass changed the .xtb.
        make_archive(self.tree, 'helium', {
            'ui/strings.grd': b'Chromium\n',
            'ui/strings_fr.xtb': b'Chromium fr\n'
        })
        make_archive(self.tree, 'rac', {'ui/strings.grd': b'Helium\n'})
        self.grd.write_bytes(b'rac\n')
        self.xtb.write_bytes(b'Helium fr\n')
        dev_names.record_expected(self.tree)

    def state(self):
        """Every file under the fixture folder, including recovery folders."""
        return {
            path.relative_to(self.folder).as_posix(): path.read_bytes()
            for path in self.folder.rglob('*') if path.is_file()
        }

    def assert_restored(self):
        self.assertEqual(self.grd.read_bytes(), b'Chromium\n')
        self.assertEqual(self.xtb.read_bytes(), b'Chromium fr\n')
        self.assertEqual(dev_names.status(self.tree), 'not applied')
        self.assertFalse((self.tree / dev_names.STATE_DIR / dev_names.EXPECTED).exists())
        self.assertEqual(list(self.folder.glob('.rac_names_unsub-*')), [])

    def test_unsub_restores_oldest_originals(self):
        dev_names.unsub(self.tree)
        self.assert_restored()

    def test_restored_files_look_newer_than_build_outputs(self):
        os.utime(self.grd, (1, 1))
        dev_names.unsub(self.tree)
        self.assertGreater(self.grd.stat().st_mtime, 1000)

    def test_restored_file_keeps_its_mode(self):
        self.grd.chmod(0o600)
        dev_names.unsub(self.tree)
        self.assertEqual(self.grd.stat().st_mode & 0o777, 0o600)

    def test_edited_string_file_refuses_and_changes_nothing(self):
        self.grd.write_bytes(b'rac\nmy unsaved edit\n')
        before = self.state()
        with self.assertRaisesRegex(ValueError, r'ui/strings\.grd changed since'):
            dev_names.unsub(self.tree)
        self.assertEqual(self.state(), before)

    def test_deleted_string_file_refuses(self):
        self.xtb.unlink()
        with self.assertRaisesRegex(ValueError, 'strings_fr.xtb changed since'):
            dev_names.unsub(self.tree)

    def test_force_overwrites_an_edit(self):
        self.grd.write_bytes(b'rac\nmy unsaved edit\n')
        dev_names.unsub(self.tree, force=True)
        self.assert_restored()

    def test_older_backups_without_hashes_still_restore(self):
        (self.tree / dev_names.STATE_DIR / dev_names.EXPECTED).unlink()
        with mock.patch('sys.stderr', new_callable=io.StringIO) as stderr:
            dev_names.unsub(self.tree)
        self.assertIn('older dev_names.py', stderr.getvalue())
        self.assert_restored()

    def test_hashes_that_dont_match_the_backups_refuse(self):
        make_archive(self.tree, 'rac', {'ui/other.grd': b'Helium\n'})
        before = self.state()
        with self.assertRaisesRegex(ValueError, "doesn't match the backups"):
            dev_names.unsub(self.tree)
        self.assertEqual(self.state(), before)

    def test_unsafe_archive_entries_refuse_before_writing(self):
        for entry in ('../outside', '/tmp/rac-test-absolute'):
            with self.subTest(entry=entry):
                make_archive(self.tree, 'rac', {entry: b'x'})
                before = self.state()
                with self.assertRaisesRegex(ValueError, 'unexpected entry'):
                    dev_names.unsub(self.tree, force=True)
                self.assertEqual(self.state(), before)

    def test_symlink_archive_entry_refuses(self):
        backup = dev_names.backup_path(self.tree, 'rac')
        with tarfile.open(backup, 'w:gz') as tar:
            info = tarfile.TarInfo('ui/strings.grd')
            info.type = tarfile.SYMTYPE
            info.linkname = '/etc/hosts'
            tar.addfile(info)
        with self.assertRaisesRegex(ValueError, 'unexpected entry'):
            dev_names.unsub(self.tree, force=True)

    def test_no_backups_clears_a_stale_hash_file(self):
        dev_names.unsub(self.tree)
        expected = self.tree / dev_names.STATE_DIR / dev_names.EXPECTED
        expected.write_text('{}')
        dev_names.unsub(self.tree)
        self.assertFalse(expected.exists())

    def test_write_failure_rolls_back(self):
        real_open = open

        def fail_on_xtb(path, mode='r', *args, **kwargs):
            if str(path).endswith('strings_fr.xtb') and 'w' in mode:
                real_open(path, 'wb').close()  # a failed write can truncate first
                raise OSError('disk full')
            return real_open(path, mode, *args, **kwargs)

        before = self.state()
        with mock.patch('builtins.open', side_effect=fail_on_xtb):
            with self.assertRaisesRegex(OSError, 'disk full; nothing was changed'):
                dev_names.unsub(self.tree)
        self.assertEqual(self.state(), before)
        self.assertEqual(dev_names.status(self.tree), 'applied')
        dev_names.unsub(self.tree)
        self.assert_restored()

    def test_failure_moving_the_backups_rolls_back_files_and_backups(self):
        real_rename = os.rename

        def fail_on_helium_backup(source, destination):
            if str(source).endswith('helium.tar'):
                raise OSError('busy')
            return real_rename(source, destination)

        before = self.state()
        with mock.patch.object(dev_names.os, 'rename', side_effect=fail_on_helium_backup):
            with self.assertRaisesRegex(OSError, 'busy; nothing was changed'):
                dev_names.unsub(self.tree)
        self.assertEqual(self.state(), before)

    def test_interrupt_rolls_back(self):
        real_copy = dev_names.shutil.copyfileobj
        calls = []

        def interrupt_second(*args):
            calls.append(1)
            if len(calls) == 2:
                raise KeyboardInterrupt
            return real_copy(*args)

        before = self.state()
        with mock.patch.object(dev_names.shutil, 'copyfileobj', side_effect=interrupt_second):
            with self.assertRaises(KeyboardInterrupt):
                dev_names.unsub(self.tree)
        self.assertEqual(self.state(), before)

    def test_failed_rollback_keeps_the_recovery_folder(self):
        real_open = open

        def fail_on_xtb(path, mode='r', *args, **kwargs):
            if str(path).endswith('strings_fr.xtb') and 'w' in mode:
                raise OSError('disk full')
            return real_open(path, mode, *args, **kwargs)

        with mock.patch('builtins.open', side_effect=fail_on_xtb), \
                mock.patch.object(dev_names.os, 'replace', side_effect=OSError('read-only')):
            with self.assertRaises(OSError) as raised:
                dev_names.unsub(self.tree)
        recovery, = self.folder.glob('.rac_names_unsub-*')
        self.assertIn(str(recovery), str(raised.exception))
        self.assertIn('putting the files back also failed', str(raised.exception))
        # The branded versions are kept outside the tree the passes scan.
        self.assertEqual((recovery / 'files' / 'ui' / 'strings.grd').read_bytes(), b'rac\n')
        self.assertEqual((recovery / 'files' / 'ui' / 'strings_fr.xtb').read_bytes(),
                         b'Helium fr\n')

    def test_sub_records_hashes_of_the_branded_files(self):
        dev_names.unsub(self.tree)

        def fake_pass(command, **_kwargs):
            backup = Path(command[command.index('--backup-path') + 1])
            name = backup.stem
            make_archive(self.tree, name, {'ui/strings.grd': self.grd.read_bytes()})
            self.grd.write_bytes(self.grd.read_bytes() + name.encode() + b'\n')
            return subprocess.CompletedProcess(command, 0, 'Modified 1 files\n', '')

        with mock.patch.object(dev_names.subprocess, 'run', side_effect=fake_pass):
            dev_names.sub(self.tree)
        expected = json.loads((self.tree / dev_names.STATE_DIR / dev_names.EXPECTED).read_text())
        self.assertEqual(expected, {'ui/strings.grd': dev_names.file_digest(self.grd)})
        self.grd.write_bytes(b'edited\n')
        with self.assertRaisesRegex(ValueError, 'changed since'):
            dev_names.unsub(self.tree)

    def test_cli_reports_refusals_without_a_traceback(self):
        self.grd.write_bytes(b'edited\n')
        script = Path(dev_names.__file__)
        result = subprocess.run([sys.executable, script, 'unsub', '-t', self.tree],
                                capture_output=True,
                                text=True,
                                check=False)
        self.assertEqual(result.returncode, 1)
        self.assertIn('dev_names: ui/strings.grd changed since', result.stderr)
        self.assertNotIn('Traceback', result.stderr)
        result = subprocess.run([sys.executable, script, 'unsub', '--force', '-t', self.tree],
                                capture_output=True,
                                text=True,
                                check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_restored()


if __name__ == '__main__':
    unittest.main()
