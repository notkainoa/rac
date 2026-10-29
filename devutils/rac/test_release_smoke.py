#!/usr/bin/env python3

# Copyright 2026 The rac Authors
# You can use, redistribute, and/or modify this source code under
# the terms of the GPL-3.0 license that can be found in the LICENSE file.
"""Tests for .github/scripts/release_smoke.py, the shared helpers behind
github_install_smoke.sh and github_update_smoke.sh.

Everything here is stdlib-only: the PNG checks run against tiny generated
PNGs, and nothing needs a disk image, a signed build, or the network. The
tests that only make sense on macOS are skipped elsewhere.

Run from the repository root:
    python3 -m unittest devutils/rac/test_release_smoke.py -v
"""

import importlib.util
import plistlib
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
HELPER = REPO / '.github' / 'scripts' / 'release_smoke.py'
INSTALL_SMOKE = REPO / '.github' / 'scripts' / 'github_install_smoke.sh'
UPDATE_SMOKE = REPO / '.github' / 'scripts' / 'github_update_smoke.sh'

spec = importlib.util.spec_from_file_location('release_smoke', HELPER)
release_smoke = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release_smoke)

MACOS = sys.platform == 'darwin'


def run_helper(*args):
    return subprocess.run(['python3', str(HELPER), *args],
                          capture_output=True, text=True, check=False)


def png_chunk(kind, payload):
    body = kind + payload
    return (struct.pack('>I', len(payload)) + body
            + struct.pack('>I', zlib.crc32(body) & 0xFFFFFFFF))


def write_png(path, width, height, pixel, extra=b''):
    """Writes a valid RGB PNG. pixel(x, y) returns an (r, g, b) tuple;
    `extra` is appended between IHDR and IDAT (used to pad a file past the
    minimum size without changing its pixels)."""
    chunk = png_chunk
    raw = bytearray()
    for y in range(height):
        raw.append(0)  # filter: none
        for x in range(width):
            raw += bytes(pixel(x, y))
    ihdr = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    data = (release_smoke.PNG_SIGNATURE + chunk(b'IHDR', ihdr) + extra
            + chunk(b'IDAT', zlib.compress(bytes(raw))) + chunk(b'IEND', b''))
    Path(path).write_bytes(data)


def noisy_pixel(x, y):
    """Incompressible-looking pixels, so the PNG lands above the size floor."""
    value = (x * 2654435761) ^ (y * 40503) ^ ((x * y) << 5)
    return (value & 0xFF, (value >> 8) & 0xFF, (value >> 16) & 0xFF)


class FeedUrlTest(unittest.TestCase):

    def test_known_arches(self):
        self.assertEqual(release_smoke.feed_url('arm64'),
                         'https://github.com/notkainoa/rac/releases/latest/'
                         'download/appcast-arm64.xml')
        self.assertEqual(release_smoke.feed_url('x86_64'),
                         'https://github.com/notkainoa/rac/releases/latest/'
                         'download/appcast-x86_64.xml')

    def test_unknown_arch_is_an_error(self):
        with self.assertRaises(ValueError):
            release_smoke.feed_url('universal')
        result = run_helper('feed-url', 'universal')
        self.assertEqual(result.returncode, 2, result)


class VersionCompareTest(unittest.TestCase):

    def test_numeric_ordering(self):
        self.assertEqual(release_smoke.compare_versions('0.2.0', '0.1.9'), 1)
        self.assertEqual(release_smoke.compare_versions('0.10.0', '0.9.9'), 1)
        self.assertEqual(release_smoke.compare_versions('0.1.9', '0.2.0'), -1)

    def test_equal_and_missing_parts(self):
        self.assertEqual(release_smoke.compare_versions('0.1.1', '0.1.1'), 0)
        self.assertEqual(release_smoke.compare_versions('0.2', '0.2.0'), 0)
        self.assertEqual(release_smoke.compare_versions('0.2.1', '0.2'), 1)

    def test_cli_reports_newer_same_older(self):
        self.assertEqual(run_helper('compare-versions', '0.2.0', '0.1.0').stdout.strip(),
                         'newer')
        self.assertEqual(run_helper('compare-versions', '0.1.0', '0.1.0').stdout.strip(),
                         'same')
        self.assertEqual(run_helper('compare-versions', '0.1.0', '0.2.0').stdout.strip(),
                         'older')

    def test_junk_versions_are_an_argument_error(self):
        result = run_helper('compare-versions', 'banana', '0.1.0')
        self.assertEqual(result.returncode, 2, result)


class CheckPngTest(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)

    def test_real_screenshot_passes(self):
        path = self.dir / 'window.png'
        write_png(path, 128, 128, noisy_pixel)
        ok, detail = release_smoke.check_png(path)
        self.assertTrue(ok, detail)
        self.assertIn('128x128', detail)

    def test_missing_file_fails(self):
        ok, detail = release_smoke.check_png(self.dir / 'none.png')
        self.assertFalse(ok)
        self.assertIn('does not exist', detail)

    def test_tiny_file_fails(self):
        path = self.dir / 'tiny.png'
        write_png(path, 32, 32, noisy_pixel)
        self.assertLess(path.stat().st_size, release_smoke.PNG_MIN_BYTES)
        ok, detail = release_smoke.check_png(path)
        self.assertFalse(ok)
        self.assertIn('bytes', detail)

    def test_uniform_frame_fails_even_when_large(self):
        # A blank window: real dimensions and (via a padding chunk) real size,
        # but every decoded pixel identical.
        path = self.dir / 'blank.png'
        padding = png_chunk(b'tEXt', b'x' * (release_smoke.PNG_MIN_BYTES + 1024))
        write_png(path, 128, 128, lambda _x, _y: (0, 0, 0), extra=padding)
        self.assertGreater(path.stat().st_size, release_smoke.PNG_MIN_BYTES)
        ok, detail = release_smoke.check_png(path)
        self.assertFalse(ok)
        self.assertIn('uniform', detail)

    def test_not_a_png_fails(self):
        path = self.dir / 'fake.png'
        path.write_bytes(b'x' * (release_smoke.PNG_MIN_BYTES + 1))
        ok, detail = release_smoke.check_png(path)
        self.assertFalse(ok)
        self.assertIn('signature', detail)


class CheckJsonTest(unittest.TestCase):

    def test_preferences_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            prefs = Path(tmp) / 'Preferences'
            prefs.write_text('{"browser": {"show_home_button": true}}')
            self.assertTrue(release_smoke.check_json(prefs)[0])
            prefs.write_text('{not json')
            ok, detail = release_smoke.check_json(prefs)
            self.assertFalse(ok)
            self.assertIn('does not parse', detail)


@unittest.skipUnless(MACOS, 'Info.plist handling is only exercised on macOS')
class PlistValueTest(unittest.TestCase):

    def test_reads_and_misses_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            plist = Path(tmp) / 'Info.plist'
            with open(plist, 'wb') as stream:
                plistlib.dump({'CFBundleShortVersionString': '0.2.0',
                               'SUFeedURL': release_smoke.feed_url('arm64')}, stream)
            self.assertEqual(release_smoke.plist_value(plist, 'SUFeedURL'),
                             release_smoke.feed_url('arm64'))
            self.assertIsNone(release_smoke.plist_value(plist, 'SUPublicEDKey'))
            result = run_helper('plist-value', str(plist), 'SUPublicEDKey')
            self.assertEqual(result.returncode, 1, result)


class SummaryTest(unittest.TestCase):

    def test_renders_one_line_per_check_and_a_tally(self):
        checks = [('PASS', 'signature', 'valid'),
                  ('FAIL', 'feed', 'HTTP 404'),
                  ('SKIP', 'notarization', 'not required')]
        text = release_smoke.render_summary('Install smoke', checks)
        self.assertIn('- **PASS** signature — valid', text)
        self.assertIn('- **FAIL** feed — HTTP 404', text)
        self.assertIn('- **SKIP** notarization — not required', text)
        self.assertIn('1 passed, 1 failed, 1 skipped', text)

    def test_render_summary_exit_status_gates_on_failures(self):
        with tempfile.TemporaryDirectory() as tmp:
            results = Path(tmp) / 'results.txt'
            out = Path(tmp) / 'summary.md'
            results.write_text('PASS\tone\tfine\nSKIP\ttwo\tlater\n')
            result = run_helper('render-summary', '--title', 'T',
                                '--results', str(results), '--out', str(out))
            self.assertEqual(result.returncode, 0, result)
            self.assertTrue(out.is_file())
            results.write_text('PASS\tone\tfine\nFAIL\ttwo\tbroke\n')
            result = run_helper('render-summary', '--title', 'T',
                                '--results', str(results), '--out', str(out))
            self.assertEqual(result.returncode, 1, result)

    def test_malformed_result_lines_count_as_failures(self):
        with tempfile.TemporaryDirectory() as tmp:
            results = Path(tmp) / 'results.txt'
            results.write_text('PASS\tone\tfine\ntruncated line\n')
            checks = release_smoke.read_results(results)
        self.assertEqual(checks[1][0], 'FAIL')


class ArgumentErrorTest(unittest.TestCase):

    def test_no_command_is_a_usage_error(self):
        self.assertEqual(run_helper().returncode, 2)

    def test_missing_argument_is_a_usage_error(self):
        self.assertEqual(run_helper('plist-value', '/tmp/x').returncode, 2)


class BashScriptTest(unittest.TestCase):
    """The scripts themselves get a smoke test of their own: syntax and the
    usage-error paths, which need no disk image."""

    def test_scripts_parse(self):
        for script in (INSTALL_SMOKE, UPDATE_SMOKE):
            result = subprocess.run(['bash', '-n', str(script)],
                                    capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, f'{script}: {result.stderr}')

    def test_scripts_reject_missing_arguments(self):
        for script in (INSTALL_SMOKE, UPDATE_SMOKE):
            result = subprocess.run(['bash', str(script)],
                                    capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 2, f'{script}: {result.stderr}')

    def test_scripts_reject_missing_disk_image(self):
        result = subprocess.run(
            ['bash', str(INSTALL_SMOKE), '/tmp/no-such.dmg', '/tmp/out'],
            capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 2, result.stderr)


if __name__ == '__main__':
    unittest.main()
