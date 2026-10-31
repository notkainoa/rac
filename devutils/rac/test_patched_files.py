#!/usr/bin/env python3

# Copyright 2026 The rac Authors
# You can use, redistribute, and/or modify this source code under
# the terms of the GPL-3.0 license that can be found in the LICENSE file.
"""Tests for patched_files.py, with fixture patches. Only temporary folders.

Run from the repository root:
    python3 -m unittest discover -s devutils/rac -p 'test_patched_files.py' -v
"""

from pathlib import Path
import tempfile
import textwrap
import unittest

import patched_files

PATH = 'chrome/browser/rac/thing.ts'

CREATE = f"""\
Index: src/{PATH}
===================================================================
--- /dev/null
+++ src/{PATH}
@@ -0,0 +1,5 @@
+one
+two
+three
+four
+five
"""

# Hunk headers one line off, as after an edit to an earlier patch.
EDIT = f"""\
--- a/{PATH}
+++ b/{PATH}
@@ -2,2 +2,3 @@
 three
+three and a half
 four
@@ -5,1 +6,1 @@
-five
+six
"""


class PatchedFilesTest(unittest.TestCase):

    def series(self, *patches):
        folder = Path(self.enterContext(tempfile.TemporaryDirectory()))
        names = []
        for n, text in enumerate(patches):
            name = f'rac/test/{n:02}.patch'
            (folder / name).parent.mkdir(parents=True, exist_ok=True)
            (folder / name).write_text(text)
            names.append(name)
        series = folder / 'series'
        series.write_text('helium/other.patch\n' + '\n'.join(names) + '\n')
        return series

    def test_replays_rac_patches_in_series_order_with_offsets(self):
        series = self.series(CREATE, EDIT)
        self.assertEqual(
            patched_files.final_text(PATH, series),
            'one\ntwo\nthree\nthree and a half\nfour\nsix\n')

    def test_refuses_a_hunk_that_does_not_match(self):
        series = self.series(CREATE, EDIT.replace(' three\n', ' 3\n'))
        with self.assertRaisesRegex(patched_files.PatchedFileError,
                                    'does not match'):
            patched_files.final_text(PATH, series)

    def test_refuses_a_file_no_rac_patch_creates(self):
        with self.assertRaisesRegex(patched_files.PatchedFileError,
                                    'no rac patch creates'):
            patched_files.final_text(PATH, self.series())
        with self.assertRaisesRegex(patched_files.PatchedFileError,
                                    'no rac patch created'):
            patched_files.final_text(PATH, self.series(EDIT))

    def test_braced_body_and_call_args_skip_strings_and_comments(self):
        text = textwrap.dedent("""\
            function f(a: string) {
              // a } in a comment
              g('}', h(1, 2), `${x}`);
              return a;
            }
            function g(x) {}
            """)
        body = patched_files.braced_body(text, 'function f(')
        self.assertTrue(body.endswith('return a;\n}'))
        self.assertEqual(patched_files.call_args(text, 'g'),
                         [["'}'", 'h(1, 2)', '`${x}`']])


if __name__ == '__main__':
    unittest.main()
