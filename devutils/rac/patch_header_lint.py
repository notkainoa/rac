#!/usr/bin/env python3

# Copyright 2026 The rac Authors
# You can use, redistribute, and/or modify this source code under
# the terms of the GPL-3.0 license that can be found in the LICENSE file.
"""Flags patch file headers whose file name is quoted or has a space.

The release build applies every patch with helium-chromium/utils/patches.py,
which on macOS runs Apple's /usr/bin/patch. Apple's patch cuts a file name at
the first space and doesn't understand git's quoted names, so a patch that
names `"b/x/User Data/Prefs"` writes `x/User` instead, or fails with a
reject. quilt and GNU patch take such names, so nothing else catches it.

This reads the headers of every file in a patch: `--- `, `+++ `, `Index: `,
`diff --git `, and git's `rename from/to` and `copy from/to`. A tab and a
timestamp after the name are fine, and so is /dev/null. Lines inside a hunk
are never headers.

usage: patch_header_lint.py [patch or folder ...]   (default: patches/)
"""

from pathlib import Path
import os
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
PATCHES = ROOT / 'patches'
ISSUE = 'https://github.com/notkainoa/rac/issues/74'
WHY = ("Apple's /usr/bin/patch (the release pipeline's) can't apply quoted or spaced file "
       f'names; rename the file. See {ISSUE}')

HUNK_HEADER = re.compile(r'^@@ -\d+(?:,(\d+))? \+\d+(?:,(\d+))? @@')
NAMED = ('Index: ', 'rename from ', 'rename to ', 'copy from ', 'copy to ')


class Hit:
    """A header line whose file name Apple's patch can't read."""

    def __init__(self, path, number, header):
        self.path = path
        self.number = number
        self.header = header

    def __repr__(self):
        return f'Hit({self.path}:{self.number}, {self.header!r})'


def bad_name(name):
    """Whether a file name in a header is quoted or has a space."""
    name = name.split('\t')[0].rstrip()
    if name == '/dev/null':
        return False
    return '"' in name or ' ' in name


def bad_header(line, previous, following):
    """Whether one line outside a hunk is a file header with a bad name."""
    if line.startswith('--- ') and following.startswith('+++ '):
        return bad_name(line[4:])
    if line.startswith('+++ ') and previous.startswith('--- '):
        return bad_name(line[4:])
    if line.startswith('diff --git '):
        rest = line[len('diff --git '):].rstrip()
        # Plain git headers are exactly "a/<name> b/<name>".
        return '"' in rest or len(rest.split(' ')) != 2
    for prefix in NAMED:
        if line.startswith(prefix):
            return bad_name(line[len(prefix):])
    return False


def lint_text(text, path='<patch>'):
    """Every bad header in a patch's text, in order."""
    lines = text.split('\n')
    hits = []
    i = 0
    while i < len(lines):
        line = lines[i].rstrip('\r')
        header = HUNK_HEADER.match(line)
        if header:
            # Skip the body by its counts: a removed "-- x" reads "--- x".
            old_left = 1 if header.group(1) is None else int(header.group(1))
            new_left = 1 if header.group(2) is None else int(header.group(2))
            i += 1
            while i < len(lines) and (old_left > 0 or new_left > 0):
                kind = lines[i][:1]
                if kind == '-':
                    old_left -= 1
                elif kind == '+':
                    new_left -= 1
                elif kind != '\\':
                    old_left -= 1
                    new_left -= 1
                i += 1
            continue
        previous = lines[i - 1] if i else ''
        following = lines[i + 1] if i + 1 < len(lines) else ''
        if bad_header(line, previous, following):
            hits.append(Hit(path, i + 1, line))
        i += 1
    return hits


def patch_files(targets):
    """The .patch files in the given files and folders, sorted."""
    files = []
    for target in targets:
        target = Path(target)
        if target.is_dir():
            files += sorted(target.rglob('*.patch'))
        else:
            files.append(target)
    return files


def display(path):
    try:
        return Path(path).resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def annotate(hit):
    if os.environ.get('GITHUB_ACTIONS') != 'true':
        return
    message = WHY.replace('%', '%25')
    print(f'::error file={hit.path},line={hit.number},title=Quoted or spaced file name::{message}')


def main(argv=None):
    """CLI entrypoint"""
    targets = sys.argv[1:] if argv is None else argv
    if any(t in ('-h', '--help') for t in targets):
        print(__doc__)
        return 0
    hits = []
    files = patch_files(targets or [PATCHES])
    for path in files:
        try:
            text = Path(path).read_bytes().decode('utf-8', errors='surrogateescape')
        except OSError as error:
            print(f'patch_header_lint: {error}', file=sys.stderr)
            return 2
        hits += lint_text(text, display(path))
    for hit in hits:
        print(f'{hit.path}:{hit.number}: {hit.header}\n    {WHY}')
        annotate(hit)
    if hits:
        print(f'patch_header_lint: {len(hits)} header(s) with quoted or spaced file names')
        return 1
    print(f'patch_header_lint: {len(files)} patches, no quoted or spaced file names')
    return 0


if __name__ == '__main__':
    sys.exit(main())
