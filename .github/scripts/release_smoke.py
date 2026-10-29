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

  release_smoke.py plist-value <Info.plist> <key>
      Prints the value of a top-level key. Fails when the key is absent or
      the plist can't be read.

  release_smoke.py check-png <path>
      Passes when the file looks like a real screenshot: a PNG of useful
      dimensions and size whose decoded pixels aren't all identical. A blank
      first frame (transparent or solid black) is not a painted window.

  release_smoke.py check-json <path>
      Passes when the file parses as JSON. Chromium's Local State and
      Default/Preferences are JSON; their surviving an update is what the
      update smoke test is for.

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
# Decompressing a whole screenshot would use hundreds of megabytes; sampling
# the first chunk of image data is enough to tell a painted window from a
# blank frame.
PNG_DECODE_LIMIT = 4 * 1024 * 1024
PNG_SAMPLE_COUNT = 4096

SUMMARY_STATUSES = ('PASS', 'FAIL', 'SKIP')


def feed_url(arch):
    """Returns the update feed URL for a build of the given architecture."""
    try:
        return FEED_BASE_URL + FEED_FILES[arch]
    except KeyError:
        raise ValueError(f"unknown architecture {arch!r} "
                         f"(expected one of: {', '.join(sorted(FEED_FILES))})")


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


def check_png(path):
    """(ok, detail): the file is a PNG that looks like a painted window."""
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
    if kind != b'IHDR' or len(ihdr) < 8:
        return False, 'first chunk is not a usable IHDR'
    width, height = struct.unpack('>II', ihdr[:8])
    if width < PNG_MIN_SIDE or height < PNG_MIN_SIDE:
        return False, f'{width}x{height} is too small to be a window'
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
    step = max(1, len(decoded) // PNG_SAMPLE_COUNT)
    if len(set(decoded[::step])) <= 1:
        return False, f'{width}x{height} decodes to a uniform frame (blank window)'
    return True, f'{width}x{height}, {len(data)} bytes, non-uniform pixels'


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

    plist = commands.add_parser('plist-value', help='read a plist key')
    plist.add_argument('plist')
    plist.add_argument('key')

    for name in ('check-png', 'check-json'):
        command = commands.add_parser(name)
        command.add_argument('path')

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
