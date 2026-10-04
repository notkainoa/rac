#!/usr/bin/env python3
"""Reads rac's version from rac_version.txt and writes it into a build tree.

rac's version is separate from Helium's. Sparkle compares it with the
version in each update feed, so it may only ever go up.
"""

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERSION_FILE = ROOT / 'rac_version.txt'
PARTS = ('RAC_MAJOR', 'RAC_MINOR', 'RAC_PATCH')


def read_version(path=VERSION_FILE):
    """Returns the version in path as a tuple of three ints."""
    text = path.read_text(encoding='utf-8').strip()
    if not re.fullmatch(r'\d+\.\d+\.\d+', text):
        raise ValueError(f'{path}: expected MAJOR.MINOR.PATCH, found {text!r}')
    return tuple(int(part) for part in text.split('.'))


def inject(src):
    """Writes the RAC_* lines into src/chrome/VERSION. Returns True if the file
    changed. Leaves the file untouched otherwise, so builds don't redo work."""
    chrome_version = src / 'chrome' / 'VERSION'
    old = chrome_version.read_text(encoding='utf-8')
    lines = [line for line in old.splitlines() if not line.startswith('RAC_')]
    lines += [f'{name}={value}' for name, value in zip(PARTS, read_version())]
    new = '\n'.join(lines) + '\n'
    if new == old:
        return False
    chrome_version.write_text(new, encoding='utf-8')
    return True


def main():
    """CLI entrypoint"""
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--print', action='store_true', help='print the version')
    group.add_argument('-t', '--tree', type=Path, help='build tree to update')
    args = parser.parse_args()

    if args.print:
        print('.'.join(str(part) for part in read_version()))
        return 0

    if inject(args.tree):
        print(f'rac version set to {VERSION_FILE.read_text().strip()}', file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main())
