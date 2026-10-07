#!/usr/bin/env python3
# Copyright 2025 The rac Authors
# You can use, redistribute, and/or modify this source code under
# the terms of the GPL-3.0 license that can be found in the LICENSE file.
"""Focused tests; never read or mutate a real Chromium tree."""

from pathlib import Path
import io
import json
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
