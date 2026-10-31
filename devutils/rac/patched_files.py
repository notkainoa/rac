#!/usr/bin/env python3

# Copyright 2026 The rac Authors
# You can use, redistribute, and/or modify this source code under
# the terms of the GPL-3.0 license that can be found in the LICENSE file.
"""Rebuilds a file a rac patch creates, from the patches alone.

A check over the code rac ships (a WebUI page, a handler) wants the file as
the build sees it, but the repository holds only patches, and CI has no
Chromium tree. A file that one of rac's patches creates needs no tree: start
empty at the patch that creates it and apply, in series order, every rac
patch hunk for it after. Hunks must match exactly; an offset is allowed, as
it is for GNU patch, but no fuzz.

    import patched_files
    text = patched_files.final_text('chrome/browser/resources/rac_ai/app.ts')
"""

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
PATCHES = ROOT / 'patches'
SERIES = PATCHES / 'series'

HUNK = re.compile(r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@')


class PatchedFileError(Exception):
    """The file can't be rebuilt from rac's patches."""


def series_patches(series=SERIES):
    """rac's patches, in the order patches/series applies them."""
    names = [line.strip() for line in series.read_text().splitlines()]
    return [series.parent / n for n in names if n.startswith('rac/')]


def _tree_path(header):
    """The tree path in a `--- ` or `+++ ` line, or None for /dev/null."""
    target = header[4:].split('\t')[0].strip()
    if target == '/dev/null':
        return None
    return re.sub(r'^(?:src|src\.orig|a|b)/', '', target)


def file_hunks(text):
    """Yields (old_path, new_path, hunks) for each file in a patch, where a
    hunk is (old_start, old_lines, new_lines)."""
    raw = text.splitlines()
    i = 0
    while i < len(raw):
        line = raw[i]
        if not (line.startswith('--- ') and i + 1 < len(raw)
                and raw[i + 1].startswith('+++ ')):
            i += 1
            continue
        old, new = _tree_path(line), _tree_path(raw[i + 1])
        i += 2
        hunks = []
        while i < len(raw):
            match = HUNK.match(raw[i])
            if not match:
                break
            old_count = int(match.group(2) or 1)
            new_count = int(match.group(4) or 1)
            old_lines, new_lines = [], []
            i += 1
            while (len(old_lines) < old_count or len(new_lines) < new_count) \
                    and i < len(raw):
                body = raw[i]
                i += 1
                if body.startswith('\\'):
                    continue
                # Some tools write an empty context line with no space.
                sign, rest = (body[:1] or ' '), body[1:]
                if sign in ' -':
                    old_lines.append(rest)
                if sign in ' +':
                    new_lines.append(rest)
            while i < len(raw) and raw[i].startswith('\\'):
                i += 1
            hunks.append((int(match.group(1)), old_lines, new_lines))
        yield old, new, hunks


def _apply(lines, hunks, where):
    out = list(lines)
    delta = 0
    for old_start, old_lines, new_lines in hunks:
        # A hunk that adds to an empty file says 0; others count from 1.
        expected = max(old_start - 1, 0) + delta
        size = len(old_lines)
        found = None
        for offset in range(len(out) + 1):
            for at in (expected - offset, expected + offset):
                if 0 <= at <= len(out) - size and out[at:at + size] == old_lines:
                    found = at
                    break
            if found is not None:
                break
        if found is None:
            raise PatchedFileError(f'{where}: a hunk at line {old_start} '
                                   'does not match')
        out[found:found + size] = new_lines
        delta += len(new_lines) - size + (found - expected)
    return out


def final_text(path, series=SERIES):
    """`path` (a tree path) after all of rac's patches, as text."""
    lines = None
    for patch in series_patches(series):
        text = patch.read_text(encoding='utf-8', errors='replace')
        if path not in text:
            continue
        for old, new, hunks in file_hunks(text):
            if path not in (old, new):
                continue
            where = f'{patch.relative_to(series.parent)} ({path})'
            if old is None:
                lines = []
            elif lines is None:
                raise PatchedFileError(
                    f'{where}: edits a file no rac patch created')
            if new is None:
                lines = None
                continue
            lines = _apply(lines, hunks, where)
    if lines is None:
        raise PatchedFileError(f'no rac patch creates {path}')
    return '\n'.join(lines) + '\n'


def braced_body(text, opening):
    """The text from `opening` (which ends its line's first `{`, or is
    followed by one) through the brace that closes it. Strings, template
    literals, and comments don't count."""
    start = text.find(opening)
    if start < 0:
        raise PatchedFileError(f'{opening!r} is gone')
    brace = text.find('{', start + len(opening) - 1)
    depth, i, quote = 0, brace, None
    while i < len(text):
        c = text[i]
        if quote:
            if c == '\\':
                i += 2
                continue
            if c == quote:
                quote = None
        elif text.startswith('//', i):
            i = text.find('\n', i)
            if i < 0:
                break
        elif text.startswith('/*', i):
            i = text.find('*/', i) + 1
        elif c in '\'"`':
            quote = c
        elif c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
        i += 1
    raise PatchedFileError(f'{opening!r} never closes')


def call_args(text, name):
    """Each call to `name(...)` or `x.name(...)` in `text`, as its list of
    top-level argument strings. A `function name(` declaration isn't one."""
    calls = []
    for match in re.finditer(r'(?<!\w)' + re.escape(name) + r'\(', text):
        if text[:match.start()].endswith('function '):
            continue
        i, depth, quote = match.end(), 1, None
        args, current = [], ''
        while i < len(text) and depth:
            c = text[i]
            if quote:
                current += c
                if c == '\\':
                    current += text[i + 1]
                    i += 1
                elif c == quote:
                    quote = None
            elif c in '\'"`':
                quote = c
                current += c
            elif c in '([{':
                depth += 1
                current += c
            elif c in ')]}':
                depth -= 1
                if depth:
                    current += c
            elif c == ',' and depth == 1:
                args.append(current.strip())
                current = ''
            else:
                current += c
            i += 1
        if current.strip():
            args.append(current.strip())
        calls.append(args)
    return calls
