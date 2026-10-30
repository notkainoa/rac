#!/usr/bin/env python3

# Copyright 2026 The rac Authors
# You can use, redistribute, and/or modify this source code under
# the terms of the GPL-3.0 license that can be found in the LICENSE file.
"""Shared logic for the release smoke tests.

github_install_smoke.sh and github_update_smoke.sh are thin shell wrappers;
the checks worth testing live here so devutils/rac/test_release_smoke.py can
cover them without a disk image, a signed build, or a Mac.

  release_smoke.py feed-url <arch>
      Prints the Sparkle feed URL a build of that architecture must use.

  release_smoke.py check-feed <strings-file> <arch>
      Passes when the output of `strings` on the app binaries contains the
      full expected feed base (FEED_BASE_URL) and the exact feed file name
      for <arch>. Matching fragments like "releases/latest/download/" is
      not enough: a build pointing at someone else's release shares every
      fragment but the host.

  release_smoke.py plist-value <Info.plist> <key>
      Prints the value of a top-level key. Fails when the key is absent or
      the plist can't be read.

  release_smoke.py check-png <path>
      Passes when the file looks like a real screenshot: a PNG of useful
      dimensions and size whose decoded pixels show a painted window.
      Scanlines are actually reconstructed (each row's filter — None, Sub,
      Up, Average, or Paeth — is undone) and whole pixels compared, because
      a solid-color PNG still produces varied filtered bytes. A frame needs
      at least PNG_MIN_DISTINCT_COLORS distinct pixel values to count as
      painted; 8-bit gray, gray+alpha, RGB, and RGBA are supported, and
      anything else (palette, 16-bit, interlaced) can't be verified and
      fails.

  release_smoke.py check-json <path>
      Passes when the file parses as JSON. Chromium's Local State and
      Default/Preferences are JSON; their surviving an update is what the
      update smoke test is for.

  release_smoke.py set-marker <prefs> <value>
      Writes {"rac_smoke": {"marker": <value>}} into a JSON prefs file,
      keeping every other key. The update smoke seeds a random marker into
      the old profile: Chromium preserves unknown top-level prefs, so the
      same marker's presence after the update proves a setting carried
      over — stronger evidence than "the file still parses".

  release_smoke.py check-marker <prefs> <value>
      Passes when the prefs file parses and rac_smoke.marker equals value.

  release_smoke.py compare-versions <new> <old>
      Prints "newer", "same", or "older" for <new> relative to <old>.
      Dotted versions compare numerically, so 0.10.0 is newer than 0.9.9.

  release_smoke.py render-summary --title TITLE --results FILE --out FILE
      Writes the markdown summary the workflow shows. FILE holds one check
      per line as STATUS<TAB>name<TAB>detail, with STATUS one of PASS, FAIL,
      or SKIP. Fails when any line is a FAIL, so the scripts can use this
      command's exit status as their own.

Every command exits 0 on success, 1 on a failed check, and 2 on bad
arguments.
"""

import argparse
import json
import plistlib
import struct
import sys
import zlib
from pathlib import Path

# rac::GetUpdateFeedURL() in patches/rac/updates/update-feed.patch resolves
# the per-architecture file against this base. It must match what the binary
# was built with; if the feed moves, every installed copy stops updating.
FEED_BASE_URL = 'https://github.com/notkainoa/rac/releases/latest/download/'
FEED_FILES = {'arm64': 'appcast-arm64.xml', 'x86_64': 'appcast-x86_64.xml'}

PNG_SIGNATURE = b'\x89PNG\r\n\x1a\n'
PNG_MIN_BYTES = 20 * 1024
PNG_MIN_SIDE = 16
# Decompressing a whole screenshot would use hundreds of megabytes; the
# first chunk of image data is enough scanlines to tell a painted window
# from a blank frame.
PNG_DECODE_LIMIT = 4 * 1024 * 1024
# A painted window — text, icons, antialiased edges — shows far more than a
# handful of distinct pixel values; a blank frame shows one. Sixteen is the
# bar: under it a frame is treated as flat even if it isn't uniform.
PNG_MIN_DISTINCT_COLORS = 16
# Channels per pixel for the PNG color types check_png can reconstruct:
# grayscale, truecolor (RGB), grayscale+alpha, and truecolor+alpha (RGBA).
PNG_COLOR_CHANNELS = {0: 1, 2: 3, 4: 2, 6: 4}

SUMMARY_STATUSES = ('PASS', 'FAIL', 'SKIP')


def feed_url(arch):
    """Returns the update feed URL for a build of the given architecture."""
    try:
        return FEED_BASE_URL + FEED_FILES[arch]
    except KeyError:
        raise ValueError(f"unknown architecture {arch!r} "
                         f"(expected one of: {', '.join(sorted(FEED_FILES))})")


def check_feed(strings_path, arch):
    """(ok, detail): a `strings` dump holds the full expected feed for arch —
    the complete FEED_BASE_URL and the exact feed file name. Anything less is
    a fragment match that a wrong-host binary can satisfy."""
    try:
        expected = FEED_FILES[arch]
    except KeyError:
        raise ValueError(f"unknown architecture {arch!r} "
                         f"(expected one of: {', '.join(sorted(FEED_FILES))})")
    try:
        dump = Path(strings_path).read_bytes()
    except OSError as error:
        return False, f'could not read strings dump: {error}'
    missing = [needle for needle in (FEED_BASE_URL, expected)
               if needle.encode() not in dump]
    if missing:
        return False, ('binary strings lack ' + ' and '.join(missing)
                       + f'; expected the feed {FEED_BASE_URL}{expected}')
    return True, (f'full feed base and {expected} found in the binary '
                  f'(feed is {FEED_BASE_URL}{expected})')


def version_parts(version):
    """Parses a dotted version into a tuple of ints. Raises ValueError."""
    parts = version.strip().split('.')
    if not parts or any(not part.isdigit() for part in parts):
        raise ValueError(f'not a dotted version: {version!r}')
    return tuple(int(part) for part in parts)


def compare_versions(new, old):
    """Returns 1, 0, or -1 for new >, ==, or < old. Missing parts count as 0,
    so 0.2 and 0.2.0 are the same version."""
    left, right = version_parts(new), version_parts(old)
    width = max(len(left), len(right))
    left += (0,) * (width - len(left))
    right += (0,) * (width - len(right))
    return (left > right) - (left < right)


def plist_value(plist_path, key):
    """Reads a top-level key from an XML or binary plist. Returns None when
    the file can't be read or the key is absent."""
    try:
        with open(plist_path, 'rb') as stream:
            plist = plistlib.load(stream)
    except (OSError, plistlib.InvalidFileException, ValueError):
        return None
    value = plist.get(key)
    return None if value is None else str(value)


MARKER_KEY = 'rac_smoke'


def set_marker(path, value):
    """Writes rac_smoke.marker = value into a JSON prefs file, preserving
    every other key. Creates the file when missing; raises ValueError when
    it exists but can't be treated as a prefs object."""
    candidate = Path(path)
    if candidate.is_file():
        try:
            data = json.loads(candidate.read_text())
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError(f'cannot seed a marker in {candidate}: {error}')
    else:
        data = {}
    if not isinstance(data, dict):
        raise ValueError(f'{candidate} is not a JSON object')
    bucket = data.setdefault(MARKER_KEY, {})
    if not isinstance(bucket, dict):
        bucket = data[MARKER_KEY] = {}
    bucket['marker'] = value
    candidate.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n')


def check_marker(path, expected):
    """(ok, detail): the prefs file parses and rac_smoke.marker == expected."""
    candidate = Path(path)
    if not candidate.is_file():
        return False, f'{candidate} does not exist'
    try:
        data = json.loads(candidate.read_text())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        return False, f'{candidate.name} does not parse as JSON: {error}'
    bucket = data.get(MARKER_KEY) if isinstance(data, dict) else None
    actual = bucket.get('marker') if isinstance(bucket, dict) else None
    if actual == expected:
        return True, (f'rac_smoke.marker kept its seeded value across the '
                      f'update ({expected})')
    return False, (f'rac_smoke.marker is {actual!r}, expected {expected!r} — '
                   'a setting did not survive the update')


def check_json(path):
    """(ok, detail): the file exists and parses as JSON."""
    candidate = Path(path)
    if not candidate.is_file():
        return False, f'{candidate} does not exist'
    try:
        json.loads(candidate.read_text())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        return False, f'{candidate.name} does not parse as JSON: {error}'
    return True, f'{candidate.name} parses as JSON'


def _png_chunks(data):
    """Yields (type, payload) for each chunk. Raises ValueError on a file
    that stops mid-chunk."""
    offset = len(PNG_SIGNATURE)
    while offset + 8 <= len(data):
        (length,) = struct.unpack('>I', data[offset:offset + 4])
        kind = data[offset + 4:offset + 8]
        payload = data[offset + 8:offset + 8 + length]
        if len(payload) < length:
            raise ValueError(f'truncated {kind.decode("ascii", "replace")} chunk')
        yield kind, payload
        offset += 12 + length  # length + type + payload + CRC
        if kind == b'IEND':
            return


def _paeth(left, up, up_left):
    """PNG's Paeth predictor: the neighbor closest to left + up - up_left."""
    guess = left + up - up_left
    d_left, d_up, d_up_left = (abs(guess - left), abs(guess - up),
                             abs(guess - up_left))
    if d_left <= d_up and d_left <= d_up_left:
        return left
    return up if d_up <= d_up_left else up_left


def _recon_rows(decoded, stride, bpp):
    """Yields each complete scanline in `decoded` with its PNG filter undone.
    `decoded` holds the inflated IDAT stream: one filter byte per row of
    `stride` filtered bytes. Raises ValueError on an unknown filter byte."""
    prev = bytearray(stride)
    prev_uniform = True  # the virtual row above row 0 is all zeros
    pos = 0
    width = stride // bpp
    while pos + 1 + stride <= len(decoded):
        kind = decoded[pos]
        raw = decoded[pos + 1:pos + 1 + stride]
        if kind == 0:  # None
            recon = bytearray(raw)
        elif kind == 1 and not any(raw[bpp:]):
            # Sub whose only residual is the first pixel: every other pixel
            # copies its left neighbor, so the row is one pixel repeated.
            recon = raw[:bpp] * width
            yield recon
            prev, prev_uniform = recon, True
            pos += 1 + stride
            continue
        elif not any(raw) and (kind == 2 or (kind == 4 and prev_uniform)):
            # Up or Paeth with a zero residual (Paeth needs a uniform row
            # above for this to hold): the row equals the one above it.
            yield prev
            pos += 1 + stride
            continue
        elif kind == 1:  # Sub
            recon = bytearray(stride)
            for i in range(stride):
                left = recon[i - bpp] if i >= bpp else 0
                recon[i] = (raw[i] + left) & 0xFF
        elif kind == 2:  # Up
            recon = bytearray(stride)
            for i in range(stride):
                recon[i] = (raw[i] + prev[i]) & 0xFF
        elif kind == 3:  # Average
            recon = bytearray(stride)
            for i in range(stride):
                left = recon[i - bpp] if i >= bpp else 0
                recon[i] = (raw[i] + ((left + prev[i]) >> 1)) & 0xFF
        elif kind == 4:  # Paeth
            recon = bytearray(stride)
            for i in range(stride):
                left = recon[i - bpp] if i >= bpp else 0
                up_left = prev[i - bpp] if i >= bpp else 0
                recon[i] = (raw[i] + _paeth(left, prev[i], up_left)) & 0xFF
        else:
            raise ValueError(f'unknown scanline filter type {kind}')
        prev_uniform = recon[:bpp] * width == recon
        yield recon
        prev = recon
        pos += 1 + stride


def check_png(path):
    """(ok, detail): the file is a PNG whose decoded pixels look painted."""
    candidate = Path(path)
    if not candidate.is_file():
        return False, f'{candidate} does not exist'
    data = candidate.read_bytes()
    if len(data) <= PNG_MIN_BYTES:
        return False, f'only {len(data)} bytes (expected more than {PNG_MIN_BYTES})'
    if not data.startswith(PNG_SIGNATURE):
        return False, 'not a PNG (bad signature)'
    try:
        chunks = _png_chunks(data)
        kind, ihdr = next(chunks)
    except (StopIteration, ValueError) as error:
        return False, f'malformed PNG: {error}'
    if kind != b'IHDR' or len(ihdr) < 13:
        return False, 'first chunk is not a usable IHDR'
    width, height, depth, color, _comp, _filt, interlace = \
        struct.unpack('>IIBBBBB', ihdr[:13])
    if width < PNG_MIN_SIDE or height < PNG_MIN_SIDE:
        return False, f'{width}x{height} is too small to be a window'
    if depth != 8 or color not in PNG_COLOR_CHANNELS or interlace != 0:
        return False, (f'unsupported PNG layout (bit depth {depth}, color '
                       f'type {color}, interlace {interlace}); expected '
                       '8-bit gray/RGB/RGBA, non-interlaced')
    try:
        idat = [payload for kind, payload in chunks if kind == b'IDAT']
    except ValueError as error:
        return False, f'malformed PNG: {error}'
    if not idat:
        return False, 'PNG has no image data'
    inflater = zlib.decompressobj()
    decoded = bytearray()
    for payload in idat:
        if len(decoded) >= PNG_DECODE_LIMIT:
            break
        try:
            decoded += inflater.decompress(payload, PNG_DECODE_LIMIT - len(decoded))
        except zlib.error as error:
            return False, f'could not decode image data: {error}'
    if not decoded:
        return False, 'PNG decodes to no image data'
    bpp = PNG_COLOR_CHANNELS[color]
    stride = width * bpp
    colors = set()
    rows = 0
    try:
        for row in _recon_rows(decoded, stride, bpp):
            rows += 1
            if row == row[:bpp] * width:
                colors.add(bytes(row[:bpp]))
            else:
                for x in range(0, stride, bpp):
                    colors.add(bytes(row[x:x + bpp]))
            if len(colors) >= PNG_MIN_DISTINCT_COLORS:
                return True, (f'{width}x{height}, {len(data)} bytes, '
                              f'{len(colors)}+ distinct colors in the first '
                              f'{rows} scanlines')
    except ValueError as error:
        return False, f'malformed PNG: {error}'
    if rows == 0:
        return False, 'PNG decodes to no complete scanlines'
    if len(colors) <= 1:
        return False, f'{width}x{height} decodes to a uniform frame (blank window)'
    return False, (f'{width}x{height} decodes to only {len(colors)} distinct '
                   f'colors across {rows} scanlines (flat frame, not a '
                   f'painted window)')


def read_results(path):
    """Parses a results file into (status, name, detail) tuples. Unknown or
    malformed lines become FAILs so a truncated write can't hide as a pass."""
    checks = []
    for line in Path(path).read_text().splitlines():
        if not line.strip():
            continue
        status, _, rest = line.partition('\t')
        name, _, detail = rest.partition('\t')
        if status not in SUMMARY_STATUSES or not rest:
            checks.append(('FAIL', 'malformed result', line))
        else:
            checks.append((status, name, detail))
    return checks


def render_summary(title, checks):
    """Formats the markdown summary: one line per check, then a tally."""
    lines = [f'## {title}', '']
    lines += [f'- **{status}** {name} — {detail}' for status, name, detail in checks]
    lines += [
        '',
        '{} passed, {} failed, {} skipped'.format(
            *(sum(1 for check in checks if check[0] == status)
              for status in SUMMARY_STATUSES)),
        '',
    ]
    return '\n'.join(lines)


def _run(arguments):
    if arguments.command == 'feed-url':
        print(feed_url(arguments.arch))
        return 0
    if arguments.command == 'check-feed':
        ok, detail = check_feed(arguments.path, arguments.arch)
        print(detail)
        return 0 if ok else 1
    if arguments.command == 'plist-value':
        value = plist_value(arguments.plist, arguments.key)
        if value is None:
            print(f'{arguments.key} is not in {arguments.plist}', file=sys.stderr)
            return 1
        print(value)
        return 0
    if arguments.command == 'check-png':
        ok, detail = check_png(arguments.path)
        print(detail)
        return 0 if ok else 1
    if arguments.command == 'check-json':
        ok, detail = check_json(arguments.path)
        print(detail)
        return 0 if ok else 1
    if arguments.command == 'set-marker':
        set_marker(arguments.path, arguments.value)
        return 0
    if arguments.command == 'check-marker':
        ok, detail = check_marker(arguments.path, arguments.value)
        print(detail)
        return 0 if ok else 1
    if arguments.command == 'compare-versions':
        result = compare_versions(arguments.new, arguments.old)
        print({1: 'newer', 0: 'same', -1: 'older'}[result])
        return 0
    if arguments.command == 'render-summary':
        checks = read_results(arguments.results)
        Path(arguments.out).write_text(render_summary(arguments.title, checks))
        return 1 if any(status == 'FAIL' for status, _, _ in checks) else 0
    return 2


def main(argv=None):
    parser = argparse.ArgumentParser(prog='release_smoke.py',
                                     description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest='command', required=True)

    feed = commands.add_parser('feed-url', help='print the update feed URL')
    feed.add_argument('arch')

    feed_check = commands.add_parser('check-feed',
                                     help='check a strings dump for the feed')
    feed_check.add_argument('path')
    feed_check.add_argument('arch')

    plist = commands.add_parser('plist-value', help='read a plist key')
    plist.add_argument('plist')
    plist.add_argument('key')

    for name in ('check-png', 'check-json'):
        command = commands.add_parser(name)
        command.add_argument('path')

    for name in ('set-marker', 'check-marker'):
        command = commands.add_parser(name)
        command.add_argument('path')
        command.add_argument('value')

    compare = commands.add_parser('compare-versions',
                                  help='compare two dotted versions')
    compare.add_argument('new')
    compare.add_argument('old')

    summary = commands.add_parser('render-summary', help='write the markdown summary')
    summary.add_argument('--title', required=True)
    summary.add_argument('--results', required=True)
    summary.add_argument('--out', required=True)

    arguments = parser.parse_args(argv)
    try:
        return _run(arguments)
    except ValueError as error:
        print(f'error: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
