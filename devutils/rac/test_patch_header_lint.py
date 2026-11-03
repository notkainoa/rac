#!/usr/bin/env python3

# Copyright 2026 The rac Authors
# You can use, redistribute, and/or modify this source code under
# the terms of the GPL-3.0 license that can be found in the LICENSE file.
"""Tests for patch_header_lint.py with fixture patches. Only temporary folders.

Run from the repository root:
    python3 -m unittest discover -s devutils/rac -p 'test_*.py' -v
"""

from pathlib import Path
import contextlib
import io
import subprocess
import sys
import tempfile
import unittest
import unittest.mock

import patch_header_lint as lint

SCRIPT = Path(__file__).resolve().parent / 'patch_header_lint.py'
STAMP = '\t2026-10-27 00:00:00.000000000 -0700'


def new_file(name, old='--- /dev/null', lines=('one', 'two')):
    body = ''.join(f'+{l}\n' for l in lines)
    return f'{old}\n+++ {name}\n@@ -0,0 +1,{len(lines)} @@\n{body}'


def edit(old, new, index=None):
    head = f'Index: {index}\n{"=" * 67}\n' if index else ''
    return f'{head}--- {old}\n+++ {new}\n@@ -1,3 +1,3 @@\n keep\n-q\n+r\n keep\n'


class LintTest(unittest.TestCase):

    def headers(self, text):
        return [hit.header for hit in lint.lint_text(text)]

    def test_quoted_name(self):
        text = new_file('"b/test/data/User Data/Default/Preferences"')
        self.assertEqual(self.headers(text),
                         ['+++ "b/test/data/User Data/Default/Preferences"'])

    def test_quoted_git_headers(self):
        text = ('diff --git "a/x/User Data/Local State" "b/x/User Data/Local State"\n'
                'new file mode 100644\n' + new_file('"b/x/User Data/Local State"'))
        self.assertEqual(len(self.headers(text)), 2)

    def test_spaced_name_without_quotes(self):
        text = edit('a/x/User Data/Prefs', 'b/x/User Data/Prefs')
        self.assertEqual(self.headers(text), ['--- a/x/User Data/Prefs', '+++ b/x/User Data/Prefs'])

    def test_index_with_space(self):
        text = edit(f'src.orig/x/a.cc{STAMP}', f'src/x/a.cc{STAMP}', index='src/x/a b.cc')
        self.assertEqual(self.headers(text), ['Index: src/x/a b.cc'])

    def test_git_rename_and_copy(self):
        text = ('diff --git a/old name.cc b/new.cc\nsimilarity index 100%\n'
                'rename from old name.cc\nrename to new.cc\n'
                'diff --git a/x.cc b/y y.cc\ncopy from x.cc\ncopy to y y.cc\n')
        self.assertEqual(self.headers(text), [
            'diff --git a/old name.cc b/new.cc', 'rename from old name.cc',
            'diff --git a/x.cc b/y y.cc', 'copy to y y.cc'
        ])

    def test_timestamps_are_not_part_of_the_name(self):
        text = edit(f'src.orig/chrome/a.cc{STAMP}', f'src/chrome/a.cc{STAMP}',
                    index='src/chrome/a.cc')
        self.assertEqual(self.headers(text), [])

    def test_dev_null_is_fine(self):
        text = new_file(f'src/chrome/new.cc{STAMP}', old=f'--- /dev/null{STAMP}')
        text += '--- a/gone.cc\n+++ /dev/null\n@@ -1 +0,0 @@\n-x\n'
        self.assertEqual(self.headers(text), [])

    def test_clean_patch(self):
        text = ('From: someone\nSubject: a change -- with dashes\n---\n a.cc | 2 +-\n\n'
                'diff --git a/a.cc b/a.cc\nindex 1234..5678 100644\n' + edit('a/a.cc', 'b/a.cc') +
                'rename from x.cc\nrename to y.cc\n')
        self.assertEqual(self.headers(text), [])

    def test_hunk_lines_that_look_like_headers(self):
        # Removing "-- a b" reads "--- a b"; adding "++ c d" reads "+++ c d".
        text = ('--- a/x\n+++ b/x\n@@ -1,3 +1,4 @@\n--- a b\n+++ c d\n'
                '+Index: e f\n keep\n-diff --git g h\n+rename from i j\n')
        self.assertEqual(self.headers(text), [])

    def test_line_numbers(self):
        text = edit('a/a.cc', 'b/a.cc') + new_file('"b/q r"')
        hits = lint.lint_text(text, 'p.patch')
        self.assertEqual([(h.path, h.number) for h in hits], [('p.patch', 9)])


class CommandTest(unittest.TestCase):

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def run_lint(self, *targets):
        return subprocess.run([sys.executable, '-I', str(SCRIPT), *map(str, targets)],
                              capture_output=True, text=True, check=False,
                              env={'PATH': '/usr/bin:/bin'})

    def test_fails_with_file_line_and_reason(self):
        (self.root / 'rac/import').mkdir(parents=True)
        (self.root / 'rac/import/a.patch').write_text(edit('a/a.cc', 'b/a.cc') +
                                                      new_file('"b/User Data/x"'))
        (self.root / 'rac/ok.patch').write_text(edit('a/a.cc', 'b/a.cc'))
        (self.root / 'notes.txt').write_text(new_file('"b/User Data/x"'))
        done = self.run_lint(self.root)
        self.assertEqual(done.returncode, 1, done.stdout + done.stderr)
        self.assertIn('a.patch:9: +++ "b/User Data/x"', done.stdout)
        self.assertIn("Apple's /usr/bin/patch (the release pipeline's) can't apply quoted "
                      'or spaced file names; rename the file. See '
                      'https://github.com/notkainoa/rac/issues/74', done.stdout)
        self.assertNotIn('notes.txt', done.stdout)
        self.assertIn('1 header(s)', done.stdout)

    def test_passes_clean_patches(self):
        (self.root / 'a.patch').write_text(edit(f'src.orig/a.cc{STAMP}', f'src/a.cc{STAMP}',
                                                index='src/a.cc'))
        done = self.run_lint(self.root, self.root / 'a.patch')
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertIn('2 patches, no quoted', done.stdout)

    def test_github_annotation(self):
        (self.root / 'a.patch').write_text(new_file('"b/q r"'))
        out = io.StringIO()
        with unittest.mock.patch.dict('os.environ', {'GITHUB_ACTIONS': 'true'}), \
                contextlib.redirect_stdout(out):
            self.assertEqual(lint.main([str(self.root / 'a.patch')]), 1)
        self.assertIn(f'::error file={self.root / "a.patch"},line=2,', out.getvalue())


if __name__ == '__main__':
    unittest.main()
