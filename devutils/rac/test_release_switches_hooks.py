#!/usr/bin/env python3

# Copyright 2026 The rac Authors
# You can use, redistribute, and/or modify this source code under
# the terms of the GPL-3.0 license that can be found in the LICENSE file.
"""The release-switches patch still hooks rac's check into Chromium.

ChromeMainDelegate calls rac::RefuseProfileReadSwitchesInBrowserProcess(),
which drops --load-extension and full-capture net logs in release builds
(issue #65). rac_devtools_unittests tests the function, not the call, and a
rebase that drops the call leaves every build and test green. So, like
test_doors_hooks.py, this reads the patch and checks the hook is still there,
ahead of the process singleton.

Run from the repository root:
    python3 -m unittest discover -s devutils/rac -p 'test_release_switches_hooks.py' -v
"""

from pathlib import Path
import unittest

from test_doors_hooks import added_lines, is_code

ROOT = Path(__file__).resolve().parents[2]
PATCH = ROOT / 'patches/rac/devtools/refuse-profile-read-switches.patch'
SERIES = ROOT / 'patches/series'
DELEGATE = 'chrome/app/chrome_main_delegate.cc'
HEADER = '#include "chrome/browser/rac/devtools/release_switches.h"'
CALL = 'rac::RefuseProfileReadSwitchesInBrowserProcess();'


def hunks(patch_text, path):
    """The hunks of `path` in the patch, each as a list of its lines."""
    found, current, inside = [], None, False
    for line in patch_text.splitlines():
        if line.startswith('+++ '):
            inside = line[4:].removeprefix('b/') == path
            current = None
        elif line.startswith('--- '):
            continue
        elif inside and line.startswith('@@'):
            current = []
            found.append(current)
        elif inside and current is not None:
            current.append(line)
    return found


class ReleaseSwitchesHooksTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.text = PATCH.read_text(encoding='utf-8')
        cls.added = added_lines(cls.text)

    def test_main_delegate_includes_and_calls_the_check(self):
        lines = self.added.get(DELEGATE, [])
        self.assertIn(HEADER, [line.split('  //')[0] for line in lines])
        self.assertTrue(any(is_code(line) and line == CALL for line in lines),
                        f'{DELEGATE} no longer calls {CALL}')

    def test_the_call_comes_before_the_process_singleton(self):
        # The singleton forwards this process's command line to a running rac,
        # so the switches must be gone before it runs.
        for hunk in hunks(self.text, DELEGATE):
            body = [line[1:].strip() for line in hunk]
            if CALL in body:
                after = body[body.index(CALL):]
                self.assertIn('#if BUILDFLAG(ENABLE_PROCESS_SINGLETON)', after)
                before = body[:body.index(CALL)]
                self.assertIn('#if !defined(BUILDING_CHROME_RENDERER)', before)
                return
        self.fail(f'no {DELEGATE} hunk calls {CALL}')

    def test_the_check_is_built(self):
        build = self.added.get('chrome/browser/rac/devtools/BUILD.gn', [])
        self.assertIn('"release_switches.cc",', build)
        self.assertIn('"release_switches_unittest.cc",', build)

    def test_the_patch_is_in_the_series(self):
        self.assertIn('rac/devtools/refuse-profile-read-switches.patch',
                      SERIES.read_text(encoding='utf-8').splitlines())


if __name__ == '__main__':
    unittest.main()
