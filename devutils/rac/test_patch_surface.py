#!/usr/bin/env python3

# Copyright 2026 The rac Authors
# You can use, redistribute, and/or modify this source code under
# the terms of the GPL-3.0 license that can be found in the LICENSE file.
"""Tests for patch_surface.py, on tiny fake trees and patches.

The apply tests need GNU patch (gpatch on macOS, patch on Linux). The Apple
patch tests need macOS's /usr/bin/patch and skip elsewhere.

Run from the repository root:
    python3 -m unittest discover -s devutils/rac -p 'test_*.py' -v
"""

from pathlib import Path
import hashlib
import io
import tarfile
import tempfile
import textwrap
import unittest
import unittest.mock
import zipfile

import patch_surface as surface

try:
    PATCH_BIN = surface.find_patch_bin()
except surface.SurfaceError:
    PATCH_BIN = None
needs_gnu_patch = unittest.skipUnless(PATCH_BIN, 'needs GNU patch (macOS: brew install gpatch)')
try:
    APPLE_BIN = surface.find_apple_patch()
except surface.SurfaceError:
    APPLE_BIN = None
needs_apple_patch = unittest.skipUnless(APPLE_BIN, "needs Apple's /usr/bin/patch (macOS)")

NUMBERS = ''.join(f'line {n}\n' for n in range(1, 41))


def diff(path, old, new, start=1):
    """A one-hunk patch with 3 lines of context, for a change in the middle."""
    return textwrap.dedent(f'''\
        --- a/{path}
        +++ b/{path}
        @@ -{start},7 +{start},7 @@
         line {start}
         line {start + 1}
         line {start + 2}
        -{old}
        +{new}
         line {start + 4}
         line {start + 5}
         line {start + 6}
        ''')


def create(path, text, quoted=False):
    """A new file. quoted names it as git does a name with a space."""
    body = ''.join(f'+{line}\n' for line in text.splitlines())
    count = len(text.splitlines())
    name = f'"b/{path}"' if quoted else f'b/{path}'
    return f'--- /dev/null\n+++ {name}\n@@ -0,0 +1,{count} @@\n{body}'


class PatchParsingTest(unittest.TestCase):

    def test_counts_hunks_and_names(self):
        text = diff('a/b.cc', 'line 4', 'changed') + diff('a/c.cc', 'line 4', 'x')
        files = surface.parse_patch(text)
        self.assertEqual([(f.old, f.new, f.hunks) for f in files],
                         [('a/b.cc', 'a/b.cc', 1), ('a/c.cc', 'a/c.cc', 1)])

    def test_creation_and_deletion_have_no_name_on_one_side(self):
        files = surface.parse_patch(create('new.cc', 'a\nb\n') +
                                    '--- a/gone.cc\n+++ /dev/null\n@@ -1 +0,0 @@\n-x\n')
        self.assertEqual([(f.old, f.new) for f in files], [(None, 'new.cc'), ('gone.cc', None)])

    def test_removed_line_that_looks_like_a_file_header(self):
        # "-- a" removed becomes "--- a"; "++ b" added becomes "+++ b".
        text = ('--- a/x\n+++ b/x\n@@ -1,2 +1,2 @@\n--- a\n+++ b\n keep\n'
                '--- a/y\n+++ b/y\n@@ -1 +1 @@\n-q\n+r\n')
        files = surface.parse_patch(text)
        self.assertEqual([(f.old, f.hunks) for f in files], [('x', 1), ('y', 1)])

    def test_no_newline_marker_and_timestamps(self):
        text = ('--- a/x\t2026-01-01\n+++ b/x\t2026-01-02\n@@ -1 +1 @@\n-q\n'
                '\\ No newline at end of file\n+r\n\\ No newline at end of file\n'
                '@@ -9 +9 @@\n-s\n+t\n')
        files = surface.parse_patch(text)
        self.assertEqual([(f.old, f.hunks) for f in files], [('x', 2)])

    def test_form_feeds_do_not_split_lines(self):
        text = '--- a/x\n+++ b/x\n@@ -1,2 +1,2 @@\n \x0c\n-q\n+r\n'
        self.assertEqual(surface.parse_patch(text)[0].hunks, 1)


class SeriesTest(unittest.TestCase):

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.helium = self.root / 'helium'
        self.platform = self.root / 'platform'

    def write(self, root, series, names=None):
        root.mkdir(exist_ok=True)
        (root / 'series').write_text('\n'.join(series) + '\n')
        for name in names if names is not None else [s.split(' #')[0] for s in series]:
            if name and not name.startswith('#'):
                (root / name).parent.mkdir(parents=True, exist_ok=True)
                (root / name).write_text(diff('f.cc', 'line 4', 'x'))

    def test_reads_comments_and_blank_lines_like_quilt(self):
        (self.root / 'series').write_text('# note\n\na.patch\nb.patch #why\n  \n')
        self.assertEqual(surface.read_series(self.root / 'series'), ['a.patch', 'b.patch'])

    def test_plan_orders_layers_and_groups(self):
        self.write(self.helium, ['h/one.patch'])
        self.write(self.platform, ['mac/two.patch', '', 'rac/look/a.patch', 'rac/pip/b.patch'])
        plan = surface.build_plan(self.helium, self.platform)
        self.assertEqual([(p.layer, p.name) for p in plan],
                         [('helium', 'h/one.patch'), ('platform', 'mac/two.patch'),
                          ('rac', 'rac/look/a.patch'), ('rac', 'rac/pip/b.patch')])
        self.assertEqual([p.group for p in plan[2:]], ['look', 'pip'])

    def test_rejects_rac_before_other_patches(self):
        self.write(self.helium, ['h/one.patch'])
        self.write(self.platform, ['rac/look/a.patch', 'mac/two.patch'])
        with self.assertRaisesRegex(surface.SurfaceError, 'rac must be last'):
            surface.build_plan(self.helium, self.platform)

    def test_rejects_duplicates_and_missing_files(self):
        self.write(self.helium, ['h/one.patch'])
        self.write(self.platform, ['h/one.patch', 'rac/x/missing.patch'], names=[])
        with self.assertRaisesRegex(surface.SurfaceError, 'listed twice') as caught:
            surface.build_plan(self.helium, self.platform)
        self.assertIn('missing.patch', str(caught.exception))

    def test_upstream_paths_leave_out_created_files(self):
        self.write(self.helium, ['h/one.patch'])
        self.write(self.platform, ['rac/x/a.patch'], names=[])
        (self.platform / 'rac/x').mkdir(parents=True)
        (self.platform / 'rac/x/a.patch').write_text(
            diff('f.cc', 'line 4', 'x') + create('new.cc', 'q\n'))
        plan = surface.build_plan(self.helium, self.platform)
        self.assertEqual(surface.upstream_paths(plan), ['f.cc'])


    def test_upstream_paths_leave_out_files_an_earlier_patch_creates(self):
        self.write(self.helium, ['h/one.patch'], names=[])
        (self.helium / 'h').mkdir()
        (self.helium / 'h/one.patch').write_text(create('made.cc', 'q\n') + diff('f.cc', 'line 4', 'x'))
        self.write(self.platform, ['mac/two.patch'], names=[])
        (self.platform / 'mac').mkdir()
        (self.platform / 'mac/two.patch').write_text(
            diff('made.cc', 'line 4', 'y') + diff('g.cc', 'line 4', 'y'))
        plan = surface.build_plan(self.helium, self.platform)
        self.assertEqual(surface.upstream_paths(plan), ['f.cc', 'g.cc'])


class ExtractTest(unittest.TestCase):

    def make_archive(self, members):
        buffer = io.BytesIO()
        with tarfile.open(fileobj=buffer, mode='w:xz') as archive:
            for name, data, kind in members:
                info = tarfile.TarInfo(name)
                info.type = kind
                if kind == tarfile.REGTYPE:
                    info.size = len(data)
                    archive.addfile(info, io.BytesIO(data))
                else:
                    info.linkname = '/etc/passwd'
                    archive.addfile(info)
        return buffer.getvalue()

    def source(self, prefix='chromium-1', output=''):
        return surface.Source('s', 'https://example.test/s.tar.xz', 's.tar.xz', output, prefix,
                              {})

    def test_extracts_only_wanted_regular_files(self):
        data = self.make_archive([('chromium-1/a/keep.cc', b'keep\n', tarfile.REGTYPE),
                                  ('chromium-1/a/other.cc', b'other\n', tarfile.REGTYPE),
                                  ('chromium-1/a/link.cc', b'', tarfile.SYMTYPE),
                                  ('chromium-1/../escape.cc', b'x\n', tarfile.REGTYPE),
                                  ('elsewhere/a/keep.cc', b'wrong\n', tarfile.REGTYPE)])
        with tempfile.TemporaryDirectory() as out:
            found = surface.extract_tar(io.BytesIO(data),
                                        {'a/keep.cc', 'a/link.cc', 'a/no.cc', '../escape.cc'},
                                        self.source(), out)
            self.assertEqual(found, {'a/keep.cc'})
            self.assertEqual((Path(out) / 'a/keep.cc').read_bytes(), b'keep\n')
            self.assertFalse((Path(out) / 'a/other.cc').exists())
            self.assertFalse((Path(out) / 'a/link.cc').exists())

    def test_extract_file_reads_xz_and_zip_and_checks_hashes(self):
        data = self.make_archive([('chromium-1/a.cc', b'a\n', tarfile.REGTYPE)])
        with tempfile.TemporaryDirectory() as folder:
            archive = Path(folder) / 'chromium-1.tar.xz'
            archive.write_bytes(data)
            source = self.source(output='third_party/x')
            source.hashes['sha256'] = hashlib.sha256(data).hexdigest()
            surface.verify_download(archive, source)
            source.hashes['sha256'] = '0' * 64
            with self.assertRaisesRegex(surface.SurfaceError, 'sha256'):
                surface.verify_download(archive, source)
            found = surface.extract_file(archive, {'third_party/x/a.cc'}, source,
                                         Path(folder) / 'out')
            self.assertEqual(found, {'third_party/x/a.cc'})
            self.assertEqual((Path(folder) / 'out/third_party/x/a.cc').read_bytes(), b'a\n')

            bundle = Path(folder) / 'x.zip'
            with zipfile.ZipFile(bundle, 'w') as zipped:
                zipped.writestr('uBlock/js/a.js', 'js\n')
                zipped.writestr('other/js/b.js', 'no\n')
            found = surface.extract_file(bundle, {'third_party/ublock/js/a.js'},
                                         self.source('uBlock', 'third_party/ublock'),
                                         Path(folder) / 'zip-out')
            self.assertEqual(found, {'third_party/ublock/js/a.js'})

    def test_download_without_a_hash_is_refused(self):
        with tempfile.TemporaryDirectory() as folder:
            archive = Path(folder) / 'a'
            archive.write_bytes(b'x')
            with self.assertRaisesRegex(surface.SurfaceError, 'no hash'):
                surface.verify_download(archive, self.source())

    def test_paths_go_to_the_download_that_unpacks_there(self):
        root = surface.Source('chromium', 'u', 'f', '', '', {})
        deps = surface.Source('onboarding', 'u', 'f', 'components/helium_onboarding', '', {})
        claims = surface.claim_paths([root, deps], {'a/b.cc', 'components/helium_onboarding/s.grdp',
                                                   'components/helium_onboarding_other.cc'})
        self.assertEqual(claims['onboarding'], {'components/helium_onboarding/s.grdp'})
        self.assertEqual(claims['chromium'], {'a/b.cc', 'components/helium_onboarding_other.cc'})

    def test_sources_read_the_downloads_files(self):
        with tempfile.TemporaryDirectory() as folder:
            ini = Path(folder) / 'downloads.ini'
            ini.write_text(textwrap.dedent('''\
                [chromium]
                url = https://example.test/chromium-%(_chromium_version)s-lite.tar.xz
                download_filename = chromium-%(_chromium_version)s-lite.tar.xz
                hash_url = chromium|chromium-%(_chromium_version)s-lite.tar.xz.hashes|https://example.test/h
                output_path = ./
                strip_leading_dirs = chromium-%(_chromium_version)s

                [onboarding]
                version = 5
                url = https://example.test/o-%(version)s.tar.gz
                download_filename = o-%(version)s.tar.gz
                sha256 = abc
                output_path = ./components/helium_onboarding
                '''))
            chromium, onboarding = surface.load_sources([ini], '9.8.7')
        self.assertEqual(chromium.url, 'https://example.test/chromium-9.8.7-lite.tar.xz')
        self.assertEqual((chromium.output, chromium.prefix), ('', 'chromium-9.8.7'))
        self.assertEqual(chromium.hash_url, 'https://example.test/h')
        self.assertEqual(chromium.tree_path('chromium-9.8.7/a/b.cc'), 'a/b.cc')
        self.assertIsNone(chromium.tree_path('other/a/b.cc'))
        self.assertEqual(onboarding.hashes, {'sha256': 'abc'})
        self.assertEqual(onboarding.output, 'components/helium_onboarding')
        self.assertEqual(onboarding.tree_path('./x.grdp'), 'components/helium_onboarding/x.grdp')

    def test_parse_hashes(self):
        text = 'md5  aa  f.tar.xz\nsha256  bb  f.tar.xz\nsha256  cc  g.tar.xz\n'
        self.assertEqual(surface.parse_hashes(text, 'f.tar.xz'), 'bb')
        self.assertIsNone(surface.parse_hashes(text, 'h.tar.xz'))


@needs_gnu_patch
class ApplyTest(unittest.TestCase):
    """Apply and count on a fake tree: files f1..f3.cc, each numbered lines."""

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.pristine = self.root / 'pristine'
        self.helium = self.root / 'helium'
        self.platform = self.root / 'platform'
        self.pristine.mkdir()
        for name in ('f1.cc', 'f2.cc', 'f3.cc'):
            (self.pristine / name).write_text(NUMBERS)
        self.series = {self.helium: [], self.platform: []}

    def add(self, root, name, text):
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_text(text)
        self.series[root].append(name)

    def run_all(self):
        for root, names in self.series.items():
            root.mkdir(exist_ok=True)
            (root / 'series').write_text('\n'.join(names) + '\n')
        plan = surface.build_plan(self.helium, self.platform)
        scratch = self.root / 'scratch'
        scratch.mkdir()
        return surface.apply_all(plan, self.pristine, self.root / 'work', scratch, PATCH_BIN)

    def test_clean_stack_is_counted_once_per_final_edit(self):
        self.add(self.helium, 'h/core.patch', diff('f1.cc', 'line 4', 'helium 4'))
        # Two groups edit the same lines of f1.cc, a third edits another file.
        self.add(self.platform, 'rac/look/a.patch', diff('f1.cc', 'helium 4', 'rac 4'))
        self.add(self.platform, 'rac/pip/b.patch',
                 diff('f1.cc', 'rac 4', 'rac again 4') + diff('f2.cc', 'line 4', 'pip 4') +
                 create('new.cc', 'one\ntwo\n'))
        self.add(self.platform, 'rac/pip/c.patch',
                 '--- a/new.cc\n+++ b/new.cc\n@@ -1,2 +1,2 @@\n-one\n+uno\n two\n')
        run = self.run_all()
        self.assertEqual(run.bad, [])
        s = run.surface
        self.assertEqual(s.groups, ['look', 'pip'])
        self.assertEqual(dict(s.patches), {'look': 1, 'pip': 2})
        # Stacked: look 1; pip 1 (f1) + 1 (f2) + 1 (create) + 1 (new.cc).
        self.assertEqual(dict(s.stacked), {'look': 1, 'pip': 4})
        # In upstream files only: the create and its edit are rac's own file.
        self.assertEqual(dict(s.stacked_upstream), {'look': 1, 'pip': 2})
        # f1.cc ended with one edit, f2.cc with one. Both go to their last group.
        self.assertEqual(s.net, {'f1.cc': 1, 'f2.cc': 1})
        self.assertEqual(s.net_by_group(), {'pip': 2})
        self.assertEqual(s.shared, {'f1.cc'})
        self.assertEqual({g: sorted(v) for g, v in s.added.items()}, {'pip': ['new.cc']})
        self.assertEqual(s.base_touched, {'f1.cc'})
        self.assertEqual((self.root / 'work/new.cc').read_text(), 'uno\ntwo\n')

    def test_offset_is_allowed(self):
        # Helium adds two lines at the top, so rac's hunk lands 2 lines lower.
        self.add(self.helium, 'h/core.patch',
                 '--- a/f1.cc\n+++ b/f1.cc\n@@ -1,3 +1,5 @@\n+extra a\n+extra b\n line 1\n line 2\n line 3\n')
        self.add(self.platform, 'rac/look/a.patch', diff('f1.cc', 'line 4', 'rac 4'))
        run = self.run_all()
        self.assertEqual(run.bad, [])
        self.assertEqual(run.results[1].offsets, 1)

    def test_failed_hunk_in_rac_is_reported_with_file_and_hunk(self):
        self.add(self.platform, 'rac/look/a.patch',
                 diff('f1.cc', 'line 4', 'rac 4') + diff('f2.cc', 'not there', 'rac'))
        run = self.run_all()
        self.assertEqual([r.ref.name for r in run.bad], ['rac/look/a.patch'])
        self.assertEqual(run.bad[0].failed, [('f2.cc', 1)])
        self.assertIn('#1 in `f2.cc`', surface.describe(run.bad[0]))

    def test_fuzz_in_rac_fails_instead_of_applying(self):
        # The context differs on one line: patch would take it at fuzz 1.
        text = diff('f1.cc', 'line 4', 'rac 4').replace(' line 6\n', ' line six\n')
        self.add(self.platform, 'rac/look/a.patch', text)
        run = self.run_all()
        self.assertEqual(len(run.bad), 1)
        self.assertEqual(run.bad[0].failed, [('f1.cc', 1)])
        self.assertEqual((self.root / 'work/f1.cc').read_text(), NUMBERS)

    def test_fuzz_in_helium_is_reported(self):
        text = diff('f1.cc', 'line 4', 'helium 4').replace(' line 6\n', ' line six\n')
        self.add(self.helium, 'h/core.patch', text)
        self.add(self.platform, 'rac/look/a.patch', diff('f2.cc', 'line 4', 'rac 4'))
        run = self.run_all()
        self.assertEqual([r.ref.name for r in run.bad], ['h/core.patch'])
        self.assertEqual([(f, h) for f, h, _ in run.bad[0].fuzz], [('f1.cc', 1)])
        self.assertIn('with fuzz', surface.describe(run.bad[0]))

    def test_missing_file_only_warns_for_helium(self):
        self.add(self.helium, 'h/core.patch', diff('gone.cc', 'line 4', 'x') +
                 diff('f1.cc', 'line 4', 'helium 4'))
        self.add(self.platform, 'rac/look/a.patch', diff('f2.cc', 'line 4', 'rac 4'))
        run = self.run_all()
        self.assertEqual(run.bad, [])
        self.assertEqual(run.results[0].missing, ['gone.cc'])
        self.assertIn('gone.cc', surface.render_report(run, None))
        self.assertEqual((self.root / 'work/f1.cc').read_text().splitlines()[3], 'helium 4')

    def test_missing_file_fails_rac(self):
        self.add(self.platform, 'rac/look/a.patch', diff('gone.cc', 'line 4', 'x'))
        run = self.run_all()
        self.assertEqual([r.ref.name for r in run.bad], ['rac/look/a.patch'])
        self.assertEqual(run.bad[0].missing, ['gone.cc'])

    def test_patch_applied_twice_fails(self):
        self.add(self.helium, 'h/core.patch', diff('f1.cc', 'line 4', 'helium 4'))
        self.add(self.platform, 'rac/look/a.patch', diff('f1.cc', 'line 4', 'helium 4'))
        run = self.run_all()
        self.assertEqual([r.ref.name for r in run.bad], ['rac/look/a.patch'])

    def test_rac_file_deleted_and_edits_outside_snapshot(self):
        self.add(self.platform, 'rac/look/a.patch',
                 '--- a/f3.cc\n+++ /dev/null\n@@ -1,40 +0,0 @@\n' +
                 ''.join(f'-line {n}\n' for n in range(1, 41)))
        run = self.run_all()
        self.assertEqual(run.bad, [])
        self.assertEqual(run.surface.net, {'f3.cc': 1})
        self.assertFalse((self.root / 'work/f3.cc').exists())

    def test_report_has_totals_and_table(self):
        self.add(self.platform, 'rac/look/a.patch', diff('f1.cc', 'line 4', 'rac 4'))
        self.add(self.platform, 'rac/pip/b.patch', diff('f2.cc', 'line 4', 'rac 4'))
        report = surface.render_report(self.run_all(), None)
        self.assertIn('| look | 1 | 1 | 1 | 1 | 1 | 0 |', report)
        self.assertIn('| Total | **2** | **2** | **2** | **2** | **2** | **0** |', report)
        self.assertIn('Net-diff hunks in upstream files: 2', report)
        self.assertIn('No patch broke the run.', report)

    def test_command_exit_codes_and_summary(self):
        self.add(self.platform, 'rac/look/a.patch', diff('f1.cc', 'line 4', 'rac 4'))
        for root, names in self.series.items():
            root.mkdir(exist_ok=True)
            (root / 'series').write_text('\n'.join(names) + '\n')
        summary = self.root / 'summary.md'
        arguments = [
            'apply', '--pristine', str(self.pristine), '--helium-patches', str(self.helium),
            '--platform-patches', str(self.platform), '--summary', str(summary)
        ]
        self.assertEqual(surface.main(arguments), 0)
        self.assertIn('## Patch surface', summary.read_text())
        self.add(self.platform, 'rac/look/b.patch', diff('f1.cc', 'nope', 'x'))
        (self.platform / 'series').write_text('\n'.join(self.series[self.platform]) + '\n')
        self.assertEqual(surface.main(arguments), 1)
        self.assertEqual(surface.main(['apply', '--pristine', str(self.pristine),
                                       '--helium-patches', str(self.root / 'nope')]), 2)


class AppleOutputTest(unittest.TestCase):
    """Apple's patch output, as patch 2.0-12u11-Apple prints it."""

    def parse(self, output, names, layer='rac'):
        result = surface.PatchResult(surface.PatchRef(layer, 'rac/x/a.patch', Path('a.patch')))
        surface.parse_apple_output(output, result, names)
        return result

    def test_clean_output(self):
        result = self.parse("patching file f.cc\npatching file 'sub/new.cc'\n",
                            [('f.cc', 'f.cc'), (None, 'sub/new.cc')])
        self.assertEqual((result.trouble, result.failed), ([], []))

    def test_name_cut_at_a_space(self):
        result = self.parse("patching file 'x/User'\n",
                            [('x/User Data/Prefs', 'x/User Data/Prefs')])
        self.assertEqual(len(result.trouble), 1)
        self.assertIn("wrote 'x/User'", result.trouble[0])
        self.assertIn('issues/74', result.trouble[0])

    def test_rejects(self):
        result = self.parse('patching file f.cc\nIgnoring previously applied (or reversed) patch.\n'
                            '1 out of 2 hunks ignored--saving rejects to f.cc.rej\n',
                            [('f.cc', 'f.cc')])
        self.assertEqual(len(result.trouble), 2)
        result = self.parse('patching file f.cc\n1 out of 1 hunks failed--saving rejects to '
                            'f.cc.rej\n', [('f.cc', 'f.cc')])
        self.assertEqual(result.trouble, ['1 out of 1 hunks failed--saving rejects to f.cc.rej'])

    def test_skipped_missing_file_is_left_to_the_missing_list(self):
        output = ('File to patch: \nNo file found--skip this patch? [y] \n'
                  '1 out of 1 hunks ignored--saving rejects to Oops.rej\n'
                  'patching file f.cc\n1 out of 1 hunks failed--saving rejects to f.cc.rej\n')
        result = self.parse(output, [('gone.cc', 'gone.cc'), ('f.cc', 'f.cc')])
        self.assertEqual(result.trouble, ['1 out of 1 hunks failed--saving rejects to f.cc.rej'])

    def test_a_cut_name_that_is_another_file_of_the_patch_still_fails(self):
        # x/User Data/a cut at the space is x/User, which the same patch
        # also names: only the order shows the wrong file was written.
        files = [('x/User Data/a', 'x/User Data/a'), ('x/User', 'x/User')]
        result = self.parse("patching file 'x/User'\npatching file 'x/User'\n", files)
        self.assertEqual(len(result.trouble), 1)
        self.assertIn('x/User Data/a', result.trouble[0])
        result = self.parse("patching file 'x/User Data/a'\npatching file 'x/User'\n", files)
        self.assertEqual(result.trouble, [])

    def test_runs_the_release_builds_exact_command(self):
        with tempfile.TemporaryDirectory() as folder:
            patch = Path(folder) / 'a.patch'
            patch.write_text(diff('f.cc', 'line 4', 'x'))
            ref = surface.PatchRef('rac', 'rac/x/a.patch', patch)
            done = unittest.mock.Mock(returncode=0, stdout='patching file f.cc\n', stderr='')
            with unittest.mock.patch.object(surface.subprocess, 'run', return_value=done) as run:
                result = surface.run_apple_patch('/usr/bin/patch', Path(folder) / 'tree', ref)
        self.assertEqual(run.call_args.args[0], [
            '/usr/bin/patch', '-p1', '--ignore-whitespace', '-i', str(patch.resolve()), '-d',
            str(Path(folder) / 'tree'), '--no-backup-if-mismatch', '--forward'
        ])
        self.assertIs(run.call_args.kwargs['stdin'], surface.subprocess.DEVNULL)
        self.assertFalse(result.bad)

    @unittest.skipUnless(PATCH_BIN, 'needs GNU patch')
    def test_gnu_patch_is_not_apple_patch(self):
        with self.assertRaisesRegex(surface.SurfaceError, "Apple's patch not found"):
            surface.find_apple_patch(PATCH_BIN)


@needs_apple_patch
class AppleApplyTest(ApplyTest):
    """The same fake tree, applied as the release build does."""

    def run_all(self):
        for root, names in self.series.items():
            root.mkdir(exist_ok=True)
            (root / 'series').write_text('\n'.join(names) + '\n')
        plan = surface.build_plan(self.helium, self.platform)
        scratch = self.root / 'scratch'
        scratch.mkdir()
        return surface.apply_all(plan, self.pristine, self.root / 'work', scratch, APPLE_BIN,
                                 apple=True)

    def test_quoted_name_with_a_space_fails(self):
        self.add(self.platform, 'rac/look/a.patch',
                 'diff --git "a/x/User Data/Prefs" "b/x/User Data/Prefs"\nnew file mode 100644\n'
                 '--- /dev/null\n+++ "b/x/User Data/Prefs"\n@@ -0,0 +1 @@\n+{}\n')
        run = self.run_all()
        self.assertEqual([r.ref.name for r in run.bad], ['rac/look/a.patch'])
        self.assertIn("wrote 'x/User'", surface.describe(run.bad[0]))

    def test_spaced_names_in_one_folder_reject(self):
        # The release run's failure: the second file lands on the first.
        self.add(self.platform, 'rac/look/a.patch',
                 create('x/User Data/Prefs', '{}\n', quoted=True) +
                 create('x/User Data/Local State', '{}\n', quoted=True))
        run = self.run_all()
        self.assertEqual([r.ref.name for r in run.bad], ['rac/look/a.patch'])
        self.assertTrue(any('.rej' in t for t in run.bad[0].trouble), run.bad[0].trouble)

    def test_plain_names_pass(self):
        self.add(self.platform, 'rac/look/a.patch',
                 diff('f1.cc', 'line 4', 'rac 4') + create('x/User_Data/Prefs', '{}\n'))
        run = self.run_all()
        self.assertEqual(run.bad, [])
        self.assertEqual((self.root / 'work/x/User_Data/Prefs').read_text(), '{}\n')

    # Apple's patch doesn't say which hunk failed or report offsets, applies
    # with fuzz, and leaves a deleted file empty, so these checks differ.
    def test_offset_is_allowed(self):
        self.add(self.helium, 'h/core.patch',
                 '--- a/f1.cc\n+++ b/f1.cc\n@@ -1,3 +1,5 @@\n+extra a\n+extra b\n line 1\n line 2\n line 3\n')
        self.add(self.platform, 'rac/look/a.patch', diff('f1.cc', 'line 4', 'rac 4'))
        run = self.run_all()
        self.assertEqual(run.bad, [])
        self.assertEqual((self.root / 'work/f1.cc').read_text().splitlines()[5], 'rac 4')

    def test_failed_hunk_in_rac_is_reported_with_file_and_hunk(self):
        self.add(self.platform, 'rac/look/a.patch',
                 diff('f1.cc', 'line 4', 'rac 4') + diff('f2.cc', 'not there', 'rac'))
        run = self.run_all()
        self.assertEqual([r.ref.name for r in run.bad], ['rac/look/a.patch'])
        self.assertIn('hunks failed--saving rejects to f2.cc.rej', surface.describe(run.bad[0]))

    def test_fuzz_in_rac_fails_instead_of_applying(self):
        self.skipTest('the release build applies with fuzz; the GNU run checks fuzz')

    def test_fuzz_in_helium_is_reported(self):
        self.skipTest('the release build applies with fuzz; the GNU run checks fuzz')

    def test_rac_file_deleted_and_edits_outside_snapshot(self):
        self.skipTest("Apple's patch empties a deleted file; the GNU run counts the surface")

    def test_clean_stack_is_counted_once_per_final_edit(self):
        self.skipTest('the GNU run counts the surface')

    def test_report_has_totals_and_table(self):
        self.add(self.platform, 'rac/look/a.patch', diff('f1.cc', 'line 4', 'rac 4'))
        report = surface.render_report(self.run_all(), None, apple=True)
        self.assertIn("## Patch apply with Apple's patch", report)
        self.assertIn('| rac | 1 | 0 | 0 |', report)
        self.assertNotIn('Patch surface', report)

    def test_command_exit_codes_and_summary(self):
        self.add(self.platform, 'rac/look/a.patch', diff('f1.cc', 'line 4', 'rac 4'))
        for root, names in self.series.items():
            root.mkdir(exist_ok=True)
            (root / 'series').write_text('\n'.join(names) + '\n')
        summary = self.root / 'summary.md'
        arguments = [
            'apply', '--apple-patch', '--pristine', str(self.pristine), '--helium-patches',
            str(self.helium), '--platform-patches', str(self.platform), '--summary', str(summary)
        ]
        self.assertEqual(surface.main(arguments), 0)
        self.assertIn("with Apple's patch", summary.read_text())
        self.add(self.platform, 'rac/look/b.patch', create('q/a b', 'x\n', quoted=True))
        (self.platform / 'series').write_text('\n'.join(self.series[self.platform]) + '\n')
        self.assertEqual(surface.main(arguments), 1)


if __name__ == '__main__':
    unittest.main()
