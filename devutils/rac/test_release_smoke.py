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


def paeth(a, b, c):
    guess = a + b - c
    da, db, dc = abs(guess - a), abs(guess - b), abs(guess - c)
    if da <= db and da <= dc:
        return a
    return b if db <= dc else c


def filter_scanline(kind, recon, prev, bpp):
    """Encodes one scanline with PNG filter `kind` (0-4). recon and prev are
    the raw and previous reconstructed rows."""
    out = bytearray(len(recon))
    for i in range(len(recon)):
        left = recon[i - bpp] if i >= bpp else 0
        up = prev[i]
        up_left = prev[i - bpp] if i >= bpp else 0
        if kind == 0:
            predictor = 0
        elif kind == 1:
            predictor = left
        elif kind == 2:
            predictor = up
        elif kind == 3:
            predictor = (left + up) >> 1
        else:
            predictor = paeth(left, up, up_left)
        out[i] = (recon[i] - predictor) & 0xFF
    return out


def write_png(path, width, height, pixel, extra=b'', filters=None,
              color_type=2):
    """Writes a valid PNG. pixel(x, y) returns a tuple whose length matches
    the color type's channel count (RGB by default); `extra` is appended
    between IHDR and IDAT (used to pad a file past the minimum size without
    changing its pixels); `filters` may be a callable y -> filter type or a
    list of per-row filter types (default all 0 = none)."""
    chunk = png_chunk
    channels = {0: 1, 2: 3, 4: 2, 6: 4}[color_type]
    stride = width * channels
    raw = bytearray()
    prev = bytearray(stride)
    for y in range(height):
        if callable(filters):
            kind = filters(y)
        elif filters is not None:
            kind = filters[y]
        else:
            kind = 0
        recon = bytearray()
        for x in range(width):
            recon += bytes(pixel(x, y))
        raw.append(kind)
        raw += filter_scanline(kind, recon, prev, channels)
        prev = recon
    ihdr = struct.pack('>IIBBBBB', width, height, 8, color_type, 0, 0, 0)
    data = (release_smoke.PNG_SIGNATURE + chunk(b'IHDR', ihdr) + extra
            + chunk(b'IDAT', zlib.compress(bytes(raw))) + chunk(b'IEND', b''))
    Path(path).write_bytes(data)


def noisy_pixel(x, y):
    """Incompressible-looking pixels, so the PNG lands above the size floor."""
    value = (x * 2654435761) ^ (y * 40503) ^ ((x * y) << 5)
    return (value & 0xFF, (value >> 8) & 0xFF, (value >> 16) & 0xFF)


def gradient_pixel(x, y):
    """A painted-looking frame: plenty of distinct colors, still compressible."""
    return ((x * 7 + y) & 0xFF, (x + y * 5) & 0xFF, (x * y) & 0xFF)


def padding_chunk():
    return png_chunk(b'tEXt', b'x' * (release_smoke.PNG_MIN_BYTES + 1024))


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


class CheckFeedTest(unittest.TestCase):
    """The compiled-in feed check must prove the binary carries rac's own
    feed URL, not just any string that happens to contain the same fragments
    (a fork's build shares every fragment but the host)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.strings = Path(self._tmp.name) / 'strings.txt'

    def write_strings(self, *lines):
        self.strings.write_text('\n'.join(lines) + '\n')

    def test_rac_feed_passes(self):
        self.write_strings('https://github.com/notkainoa/rac/releases/'
                           'latest/download/', 'appcast-arm64.xml')
        ok, detail = release_smoke.check_feed(self.strings, 'arm64')
        self.assertTrue(ok, detail)

    def test_someone_elses_feed_fails(self):
        # Same "releases/latest/download/" and "appcast-arm64.xml" fragments,
        # wrong project: the old fragment check passed on this.
        self.write_strings('https://github.com/someone-else/rac/releases/'
                           'latest/download/', 'appcast-arm64.xml')
        ok, detail = release_smoke.check_feed(self.strings, 'arm64')
        self.assertFalse(ok, detail)

    def test_wrong_arch_filename_fails(self):
        self.write_strings('https://github.com/notkainoa/rac/releases/'
                           'latest/download/', 'appcast-x86_64.xml')
        ok, detail = release_smoke.check_feed(self.strings, 'arm64')
        self.assertFalse(ok, detail)
        self.assertIn('appcast-arm64.xml', detail)

    def test_missing_base_fails(self):
        self.write_strings('appcast-arm64.xml')
        ok, detail = release_smoke.check_feed(self.strings, 'arm64')
        self.assertFalse(ok, detail)
        self.assertIn(release_smoke.FEED_BASE_URL, detail)

    def test_cli_exit_status(self):
        self.write_strings('https://github.com/notkainoa/rac/releases/'
                           'latest/download/', 'appcast-arm64.xml')
        result = run_helper('check-feed', str(self.strings), 'arm64')
        self.assertEqual(result.returncode, 0, result)
        self.write_strings('https://github.com/someone-else/rac/releases/'
                           'latest/download/')
        result = run_helper('check-feed', str(self.strings), 'arm64')
        self.assertEqual(result.returncode, 1, result)


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
        padding = padding_chunk()
        write_png(path, 128, 128, lambda _x, _y: (0, 0, 0), extra=padding)
        self.assertGreater(path.stat().st_size, release_smoke.PNG_MIN_BYTES)
        ok, detail = release_smoke.check_png(path)
        self.assertFalse(ok)
        self.assertIn('uniform', detail)

    def test_filtered_solid_frames_fail(self):
        # Every row uses a different filter, so the compressed bytes vary even
        # though the pixels are all identical. A byte-level distinctness check
        # passes on this; a decoded-pixel check must not.
        for name, color in (('black', (0, 0, 0)), ('white', (255, 255, 255)),
                            ('color', (200, 30, 30))):
            path = self.dir / f'solid-{name}.png'
            write_png(path, 96, 96, lambda _x, _y, c=color: c,
                      filters=lambda y: (y % 4) + 1, extra=padding_chunk())
            ok, detail = release_smoke.check_png(path)
            self.assertFalse(ok, f'solid {name}: unexpectedly passed')

    def test_filtered_solid_rgba_fails(self):
        path = self.dir / 'solid-rgba.png'
        write_png(path, 96, 96, lambda _x, _y: (10, 20, 30, 255),
                  filters=lambda y: (y % 4) + 1, extra=padding_chunk(),
                  color_type=6)
        ok, detail = release_smoke.check_png(path)
        self.assertFalse(ok, detail)

    def test_filtered_gradient_passes(self):
        path = self.dir / 'gradient.png'
        write_png(path, 96, 96, gradient_pixel, filters=lambda y: y % 5,
                  extra=padding_chunk())
        ok, detail = release_smoke.check_png(path)
        self.assertTrue(ok, detail)

    def test_filtered_rgba_gradient_passes(self):
        path = self.dir / 'gradient-rgba.png'
        write_png(path, 96, 96,
                  lambda x, y: gradient_pixel(x, y) + (255,),
                  filters=lambda y: (y % 4) + 1, extra=padding_chunk(),
                  color_type=6)
        ok, detail = release_smoke.check_png(path)
        self.assertTrue(ok, detail)

    def test_few_colors_fail(self):
        # A frame with real structure but fewer distinct colors than a real
        # window shows: two flat halves, no antialiasing.
        path = self.dir / 'two-tone.png'
        write_png(path, 96, 96,
                  lambda x, _y: (255, 255, 255) if x < 48 else (0, 0, 0),
                  extra=padding_chunk())
        ok, detail = release_smoke.check_png(path)
        self.assertFalse(ok, detail)

    def test_not_a_png_fails(self):
        path = self.dir / 'fake.png'
        path.write_bytes(b'x' * (release_smoke.PNG_MIN_BYTES + 1))
        ok, detail = release_smoke.check_png(path)
        self.assertFalse(ok)
        self.assertIn('signature', detail)


class PrefsMarkerTest(unittest.TestCase):
    """The update smoke seeds a random marker into the old profile's
    Default/Preferences and requires the same value after the new build
    runs: proof a real setting carried over, not just that a file parses."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.prefs = Path(self._tmp.name) / 'Preferences'

    def test_marker_roundtrip_keeps_other_keys(self):
        self.prefs.write_text('{"browser": {"show_home_button": true}}')
        release_smoke.set_marker(self.prefs, 'abc123')
        ok, detail = release_smoke.check_marker(self.prefs, 'abc123')
        self.assertTrue(ok, detail)
        self.assertIn('"show_home_button": true', self.prefs.read_text())

    def test_wrong_value_fails(self):
        release_smoke.set_marker(self.prefs, 'abc123')
        ok, detail = release_smoke.check_marker(self.prefs, 'different')
        self.assertFalse(ok)
        self.assertIn('abc123', detail)

    def test_marker_stripped_by_update_fails(self):
        release_smoke.set_marker(self.prefs, 'abc123')
        # The "new build" rewrote Preferences and dropped rac_smoke.
        self.prefs.write_text('{"browser": {"show_home_button": true}}')
        ok, detail = release_smoke.check_marker(self.prefs, 'abc123')
        self.assertFalse(ok, detail)

    def test_unparseable_prefs_fail(self):
        self.prefs.write_text('{not json')
        ok, detail = release_smoke.check_marker(self.prefs, 'abc123')
        self.assertFalse(ok)
        self.assertIn('does not parse', detail)

    def test_cli_exit_status(self):
        self.prefs.write_text('{}')
        result = run_helper('set-marker', str(self.prefs), 'cli-marker')
        self.assertEqual(result.returncode, 0, result)
        result = run_helper('check-marker', str(self.prefs), 'cli-marker')
        self.assertEqual(result.returncode, 0, result)
        result = run_helper('check-marker', str(self.prefs), 'nope')
        self.assertEqual(result.returncode, 1, result)


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


FAKE_PREAMBLE = """#!/bin/bash
profile=""
for arg in "$@"; do
  case "$arg" in --user-data-dir=*) profile="${arg#*=}" ;; esac
done
"""

# The rac-window-screenshot literal makes the scripts' `strings` probe treat
# this fake as a build with the screenshot switch.
FAKE_PREAMBLE_SHOT = """#!/bin/bash
profile=""
shot=""
for arg in "$@"; do
  case "$arg" in
    --user-data-dir=*) profile="${arg#*=}" ;;
    --rac-window-screenshot=*) shot="${arg#*=}" ;;
  esac
done
"""

FAKE_WRITE_PREFS = """
mkdir -p "$profile/Default"
printf '{}' > "$profile/Default/Preferences"
printf '{}' > "$profile/Local State"
"""

FAKE_DROP_PREFS = """
mkdir -p "$profile/Default"
printf '{"browser": {}}' > "$profile/Default/Preferences"
printf '{}' > "$profile/Local State"
"""

FAKE_STAY = "\nsleep 300\n"
FAKE_EXIT = "\nexit 0\n"


def fake_write_shot(fixture):
    return f'\nsleep 1\ncp "{fixture}" "$shot"\nsleep 300\n'


@unittest.skipUnless(MACOS, 'end-to-end runs need hdiutil and a Mac')
class EndToEndTest(unittest.TestCase):
    """Drives the real scripts against fake rac.app bundles inside real
    DMGs. A fake is a shell script at Contents/MacOS/rac that honors
    --user-data-dir like rac does; hdiutil mounts it exactly like a shipped
    disk image."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)

    def build_dmg(self, name, version, body, screenshot_switch=False):
        src = self.dir / name / 'src'
        app = src / 'rac.app' / 'Contents'
        (app / 'MacOS').mkdir(parents=True)
        (app / 'Info.plist').write_bytes(plistlib.dumps(
            {'CFBundleShortVersionString': version,
             'CFBundleExecutable': 'rac'}))
        exe = app / 'MacOS' / 'rac'
        preamble = FAKE_PREAMBLE_SHOT if screenshot_switch else FAKE_PREAMBLE
        exe.write_text(preamble + body)
        exe.chmod(0o755)
        dmg = self.dir / f'{name}.dmg'
        subprocess.run(['hdiutil', 'create', '-srcfolder', str(src),
                        '-format', 'UDZO', '-ov', '-volname', 'rac', str(dmg)],
                       check=True, capture_output=True)
        return dmg

    def run_script(self, script, *args):
        return subprocess.run(['bash', str(script), *map(str, args)],
                              capture_output=True, text=True, check=False,
                              timeout=180)

    def painted_png(self, path):
        write_png(path, 96, 96, noisy_pixel, extra=padding_chunk())


class UpdateSmokeEndToEndTest(EndToEndTest):

    def read_summary(self, out):
        return (Path(out) / 'update-smoke.md').read_text()

    def test_old_build_exiting_fails_first_launch(self):
        # A build that writes Default/Preferences and immediately exits is a
        # broken launch, not a success — even though the file exists.
        old = self.build_dmg('old', '0.1.0', FAKE_WRITE_PREFS + FAKE_EXIT)
        new = self.build_dmg('new', '0.2.0', FAKE_STAY)
        out = self.dir / 'out'
        self.run_script(UPDATE_SMOKE, old, new, out)
        self.assertIn('**FAIL** first launch', self.read_summary(out))

    def test_stale_screenshot_cannot_pass_window_painted(self):
        # A painted update-smoke.png left over from a previous run must not
        # satisfy this run's wait: the new build never writes one.
        old = self.build_dmg('old', '0.1.0', FAKE_WRITE_PREFS + FAKE_STAY)
        new = self.build_dmg('new', '0.2.0', FAKE_EXIT,
                             screenshot_switch=True)
        out = self.dir / 'out'
        out.mkdir()
        self.painted_png(out / 'update-smoke.png')
        self.run_script(UPDATE_SMOKE, old, new, out)
        self.assertIn('**FAIL** window painted', self.read_summary(out))

    def test_marker_survives_and_marker_loss_fails(self):
        old = self.build_dmg('old', '0.1.0', FAKE_WRITE_PREFS + FAKE_STAY)
        # The "new build" rewrites Preferences without rac_smoke and exits.
        new = self.build_dmg('new', '0.2.0', FAKE_DROP_PREFS + FAKE_EXIT)
        out = self.dir / 'out'
        self.run_script(UPDATE_SMOKE, old, new, out)
        self.assertIn('**FAIL** setting carried over', self.read_summary(out))


class InstallSmokeEndToEndTest(EndToEndTest):

    def read_summary(self, out):
        return (Path(out) / 'install-smoke.md').read_text()

    def test_stale_screenshot_cannot_pass_launch(self):
        # Same trap on the install side: a leftover install-smoke.png.
        dmg = self.build_dmg('app', '0.1.0', FAKE_EXIT,
                             screenshot_switch=True)
        out = self.dir / 'out'
        out.mkdir()
        self.painted_png(out / 'install-smoke.png')
        self.run_script(INSTALL_SMOKE, dmg, out)
        self.assertIn('**FAIL** launch', self.read_summary(out))

    def test_launch_passes_when_the_window_paints(self):
        # The fake honors --rac-window-screenshot and writes a real painted
        # PNG: proof the fixed path still passes.
        fixture = self.dir / 'paint.png'
        self.painted_png(fixture)
        dmg = self.build_dmg('app', '0.1.0', fake_write_shot(fixture),
                             screenshot_switch=True)
        out = self.dir / 'out'
        self.run_script(INSTALL_SMOKE, dmg, out)
        self.assertIn('**PASS** launch', self.read_summary(out))


SMOKE_YML = REPO / '.github' / 'workflows' / 'smoke.yml'


class WorkflowTest(unittest.TestCase):
    """smoke.yml decides which DMG to test; the checks are textual because
    the logic lives in embedded bash steps."""

    def setUp(self):
        self.text = SMOKE_YML.read_text()

    def test_downloads_cover_whichever_arches_exist(self):
        # An arm64-only fetch pattern makes gh fail before the script can
        # decide anything, so downloads must match every rac macOS DMG.
        self.assertNotIn("-p 'rac_*_arm64-macos.dmg'", self.text)
        self.assertIn("-p 'rac_*-macos.dmg'", self.text)

    def test_intel_only_downloads_skip_with_a_notice(self):
        # Both jobs need a clean skip path, not a hard failure, when the
        # release or run has no arm64 DMG.
        self.assertIn('::notice::', self.text)
        self.assertIn('Intel runner', self.text)
        self.assertGreaterEqual(self.text.count('::notice::'), 2)

    def test_arm64_dmg_is_still_the_one_picked(self):
        # The skip is for x86_64-only downloads; when arm64 exists the jobs
        # still run it.
        self.assertIn("-name 'rac_*_arm64-macos.dmg'", self.text)

    def test_update_job_drops_unused_expect_notarized(self):
        # The update script has no --expect-notarized flag; a dead env var
        # reads like it does something.
        update_job = self.text[self.text.index('  update-smoke:'):]
        self.assertNotIn('EXPECT_NOTARIZED', update_job)


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

    def test_install_comment_matches_behavior(self):
        # _install doesn't detach — mounts wait for _cleanup — so its comment
        # must not claim it does.
        self.assertNotIn('copies rac.app to $2, detaches',
                         UPDATE_SMOKE.read_text())


if __name__ == '__main__':
    unittest.main()
