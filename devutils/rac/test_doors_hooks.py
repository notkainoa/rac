#!/usr/bin/env python3

# Copyright 2026 The rac Authors
# You can use, redistribute, and/or modify this source code under
# the terms of the GPL-3.0 license that can be found in the LICENSE file.
"""The debug-door patch still hooks rac's checks into Chromium.

Those hooks (decision D20) are one-line edits to upstream files. A rebase
that drops one, or a refresh that loses it, leaves everything building and
every unit test green while the doors stop being refused. A test that calls
the hook code needs Chromium's `unit_tests` target (a TestingProfileManager,
a ChromeMainDelegate), which a rac-owned test target can't link without
building the browser's whole UI layer. So this reads the patch and checks
that each hook is still added to the file that owns it.

Run from the repository root:
    python3 -m unittest discover -s devutils/rac -p 'test_doors_hooks.py' -v
"""

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
PATCH = ROOT / 'patches/rac/devtools/refuse-debug-doors.patch'
HEADER = '#include "chrome/browser/rac/devtools/default_dir.h"'


def added_lines(patch_text):
    """Maps each patched file to the lines the patch adds to it, in order."""
    files = {}
    current = None
    for line in patch_text.splitlines():
        if line.startswith('+++ '):
            current = line[4:].removeprefix('b/')
            files.setdefault(current, [])
        elif line.startswith('--- '):
            continue
        elif current is not None and line.startswith('+'):
            files[current].append(line[1:].strip())
    return files


def is_code(line):
    return bool(line) and not line.startswith('//')


class DoorsHooksTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.added = added_lines(PATCH.read_text(encoding='utf-8'))

    def added_to(self, path):
        self.assertIn(path, self.added, f'the patch no longer edits {path}')
        return self.added[path]

    def assert_hook(self, path, call, following=None):
        """`call` is added to `path` as code (not a comment), after an include
        of default_dir.h. With `following`, the next added line is it."""
        lines = self.added_to(path)
        self.assertIn(HEADER, [line.split('  //')[0] for line in lines],
                      f'{path} no longer includes default_dir.h')
        hits = [n for n, line in enumerate(lines)
                if is_code(line) and call in line]
        self.assertTrue(hits, f'{path} no longer calls {call}')
        if following is not None:
            self.assertTrue(
                any(n + 1 < len(lines) and lines[n + 1] == following
                    for n in hits),
                f'{path}: the call to {call} is no longer followed by '
                f'{following!r}')

    def test_profile_manager_refuses_a_profile_while_a_door_is_open(self):
        self.assert_hook(
            'chrome/browser/profiles/profile_manager.cc',
            'if (rac::RefusesProfileForDebugDoors(path))',
            following='return false;')

    def test_profiles_build_file_depends_on_the_check(self):
        self.assertIn('"//chrome/browser/rac/devtools",',
                      self.added_to('chrome/browser/profiles/BUILD.gn'))

    def test_main_delegate_forces_the_mock_keychain(self):
        self.assert_hook(
            'chrome/app/chrome_main_delegate.cc',
            'rac::ForceMockKeychainIfDebugDoorRequested();')

    def test_remote_debugging_server_refuses_the_doors(self):
        path = 'chrome/browser/devtools/remote_debugging_server.cc'
        self.assert_hook(path, 'rac::RefusesDebugDoors(')
        self.assert_hook(path, 'rac::SetDebugDoorOpen();')


if __name__ == '__main__':
    unittest.main()
