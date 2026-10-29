#!/usr/bin/env python3

# Copyright 2025 The rac Authors
# You can use, redistribute, and/or modify this source code under
# the terms of the GPL-3.0 license that can be found in the LICENSE file.
"""Runs .github/scripts/github_check_release_binary.sh (the G6 gate) against
small fake app bundles.

The fake binaries are a Mach-O magic number followed by text, which is all the
gate looks at: it finds Mach-O files by their first four bytes and reads every
byte with `strings`. Nothing here needs a real build.

Run from the repository root:
    python3 -m unittest discover -s devutils/rac -p 'test_*.py' -v
"""

from pathlib import Path
import os
import shutil
import subprocess
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / '.github' / 'scripts' / 'github_check_release_binary.sh'

MACHO_64 = bytes.fromhex('cffaedfe')  # MH_MAGIC_64, little-endian
MACHO_FAT = bytes.fromhex('cafebabe')  # FAT_MAGIC
FRAMEWORK = 'Contents/Frameworks/rac Framework.framework'


def fake_binary(*texts, magic=MACHO_64):
    """A fake Mach-O: magic, padding, then each text NUL-terminated."""
    body = b''.join(b'\x00\x01\x02' + text.encode() + b'\x00' for text in texts)
    return magic + b'\x00' * 12 + body


@unittest.skipUnless(shutil.which('strings'), 'needs strings (binutils or Xcode)')
class ReleaseBinaryGateTest(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.app = self.root / 'rac.app'
        self.env = dict(os.environ, TMPDIR=str(self.root))
        self.env.pop('RAC_G6_GATE', None)
        self.make_clean_app()

    def write(self, rel, data):
        path = self.app / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        path.chmod(0o755)
        return path

    def make_clean_app(self):
        self.write('Contents/MacOS/rac', fake_binary('ChromeMain', 'rac main executable'))
        self.write(f'{FRAMEWORK}/Versions/146.0.0.0/rac Framework',
                   fake_binary('--user-data-dir', '--enable-features', 'some-other-switch'))
        self.write(f'{FRAMEWORK}/Versions/146.0.0.0/Helpers/rac Helper (GPU).app/Contents/MacOS/rac Helper (GPU)',
                   fake_binary('helper main'))
        self.write(f'{FRAMEWORK}/Versions/146.0.0.0/Helpers/chrome_crashpad_handler',
                   fake_binary('crashpad handler'))
        self.write('Contents/Resources/app.icns', b'icns' + b'\x00' * 32)
        self.write('Contents/Info.plist', b'<?xml version="1.0"?><plist></plist>\n')
        # Framework symlinks, as in a real bundle.
        versions = self.app / FRAMEWORK / 'Versions'
        (versions / 'Current').symlink_to('146.0.0.0')
        (self.app / FRAMEWORK / 'rac Framework').symlink_to('Versions/Current/rac Framework')

    def run_gate(self, mode=None, app=None):
        env = dict(self.env)
        if mode is not None:
            env['RAC_G6_GATE'] = mode
        result = subprocess.run(
            ['bash', str(SCRIPT), str(app if app is not None else self.app)],
            env=env, capture_output=True, text=True, errors='replace', timeout=60,
            check=False,
        )
        return result.returncode, result.stdout + result.stderr

    def test_clean_app_passes_in_both_modes(self):
        for mode in ('warn', 'enforce'):
            with self.subTest(mode=mode):
                code, out = self.run_gate(mode)
                self.assertEqual(code, 0, out)
                self.assertIn('G6 passed', out)
                self.assertIn('in 4 binaries', out)

    def test_enforce_fails_and_names_binary_and_match(self):
        self.write(f'{FRAMEWORK}/Versions/146.0.0.0/rac Framework',
                   fake_binary('--user-data-dir', 'rac-window-screenshot-delay', 'rac-agent-debug'))
        code, out = self.run_gate('enforce')
        self.assertEqual(code, 1, out)
        rel = f'{FRAMEWORK}/Versions/146.0.0.0/rac Framework'
        self.assertIn(f"::error::G6: 'rac-window-screenshot' found in {rel}", out)
        self.assertIn(f"::error::G6: 'rac-agent-debug' found in {rel}", out)
        self.assertIn(f'    {rel}: rac-window-screenshot-delay', out)
        self.assertIn('2 forbidden string match(es) in 1 of 4 binaries', out)

    def test_symlinked_framework_binary_is_scanned_once(self):
        self.write(f'{FRAMEWORK}/Versions/146.0.0.0/rac Framework', fake_binary('rac-agent-mcp-echo'))
        code, out = self.run_gate('enforce')
        self.assertEqual(code, 1, out)
        self.assertEqual(out.count("'rac-agent-mcp-echo' found in"), 1, out)
        self.assertNotIn('Versions/Current', out)

    def test_warn_reports_but_passes(self):
        self.write('Contents/MacOS/rac', fake_binary('rac-launch-in-background'))
        code, out = self.run_gate('warn')
        self.assertEqual(code, 0, out)
        self.assertIn("::warning::G6: 'rac-launch-in-background' found in Contents/MacOS/rac", out)
        self.assertIn('RAC_G6_GATE=warn', out)
        self.assertNotIn('::error::', out)

    def test_default_mode_is_warn(self):
        self.write('Contents/MacOS/rac', fake_binary('rac-launch-in-background'))
        code, out = self.run_gate()
        self.assertEqual(code, 0, out)
        self.assertIn('::warning::G6', out)

    def test_helper_app_with_spaces_in_path(self):
        rel = f'{FRAMEWORK}/Versions/146.0.0.0/Helpers/rac Helper (GPU).app/Contents/MacOS/rac Helper (GPU)'
        self.write(rel, fake_binary('rac-agent-mcp-echo'))
        code, out = self.run_gate('enforce')
        self.assertEqual(code, 1, out)
        self.assertIn(f"'rac-agent-mcp-echo' found in {rel}", out)

    def test_universal_binary_is_scanned(self):
        self.write(f'{FRAMEWORK}/Versions/146.0.0.0/Helpers/chrome_crashpad_handler',
                   fake_binary('rac-agent-debug', magic=MACHO_FAT))
        code, out = self.run_gate('enforce')
        self.assertEqual(code, 1, out)
        self.assertIn("'rac-agent-debug' found in", out)

    def test_string_deep_in_a_large_binary_is_found(self):
        # Past the point where a section-aware scan of the fake header would
        # stop; the gate must read every byte.
        data = fake_binary('start') + b'\x00' * (4 * 1024 * 1024) + b'rac-window-screenshot\x00'
        self.write(f'{FRAMEWORK}/Versions/146.0.0.0/rac Framework', data)
        code, out = self.run_gate('enforce')
        self.assertEqual(code, 1, out)
        self.assertIn("'rac-window-screenshot' found in", out)

    def test_match_next_to_invalid_utf8_is_found(self):
        # Real binaries put bytes like 0xc3 right before a string, which
        # `strings` keeps on the same line. A UTF-8 grep would skip it.
        for locale in ('C.UTF-8', 'en_US.UTF-8'):
            with self.subTest(locale=locale):
                self.env['LC_ALL'] = locale
                self.env['LANG'] = locale
                self.write('Contents/MacOS/rac',
                           MACHO_64 + b'\x00' * 12 + b']\xc3rac-agent-mcp-echo\x00')
                code, out = self.run_gate('enforce')
                self.assertEqual(code, 1, out)
                self.assertIn("'rac-agent-mcp-echo' found in Contents/MacOS/rac", out)
                self.assertIn('rac-agent-mcp-echo', out.split('found in Contents/MacOS/rac', 1)[1])

    def test_non_macho_files_are_ignored(self):
        self.write('Contents/Resources/resources.pak', b'PAK\x00rac-window-screenshot\x00')
        self.write('Contents/Resources/script.sh', b'#!/bin/sh\necho rac-agent-debug\n')
        code, out = self.run_gate('enforce')
        self.assertEqual(code, 0, out)

    def test_split_string_is_not_a_match(self):
        self.write('Contents/MacOS/rac', fake_binary('rac-agent', 'debug'))
        code, out = self.run_gate('enforce')
        self.assertEqual(code, 0, out)

    def test_unknown_mode_is_an_error(self):
        code, out = self.run_gate('off')
        self.assertEqual(code, 2, out)
        self.assertIn("RAC_G6_GATE must be 'warn' or 'enforce'", out)

    def test_bundle_without_binaries_fails_in_both_modes(self):
        empty = self.root / 'empty.app'
        (empty / 'Contents').mkdir(parents=True)
        (empty / 'Contents' / 'Info.plist').write_text('<plist/>\n')
        for mode in ('warn', 'enforce'):
            with self.subTest(mode=mode):
                code, out = self.run_gate(mode, app=empty)
                self.assertEqual(code, 2, out)
                self.assertIn('no Mach-O files', out)

    def test_missing_bundle_fails(self):
        code, out = self.run_gate('warn', app=self.root / 'missing.app')
        self.assertEqual(code, 2, out)


if __name__ == '__main__':
    unittest.main()
