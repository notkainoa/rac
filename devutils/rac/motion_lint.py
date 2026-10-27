#!/usr/bin/env python3

# Copyright 2026 The rac Authors
# You can use, redistribute, and/or modify this source code under
# the terms of the GPL-3.0 license that can be found in the LICENSE file.
"""Flags design literals that rac's patches add instead of using tokens.

Durations, curves, corner radii, insets, gaps, and padding belong in
rac_tokens.h (C++) or rac_tokens.css (WebUI). This reads the rac patches in
series order, keeps the lines they still add once later patches have run,
and flags literals of those kinds in UI files: C++ under chrome/browser/ui/
and ui/, and WebUI CSS, HTML, and TypeScript. The token files themselves,
tests, the motion engine in views/rac/motion/, and the dev harness patches are
exempt.

Literals that were there before the lint are listed in
motion_lint_allowlist.txt. The list may only shrink: --refresh rewrites it
from the current literals but refuses if any file gains one, and --base
checks the same against another commit's list.

A duration that isn't motion, such as a network timeout in UI code, can say
so on its line: `// motion-lint: not motion (why)`. Nothing else can be
excused that way.

usage: motion_lint.py [--refresh | --init] [--base <git ref>] [--counts]
                      [--files <dir> --prefix <tree path>] [patch ...]
"""

from collections import Counter, defaultdict
from pathlib import Path
import argparse
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
PATCHES = ROOT / 'patches'
SERIES = PATCHES / 'series'
ALLOWLIST = Path(__file__).resolve().parent / 'motion_lint_allowlist.txt'

KINDS = ('duration', 'curve', 'radius', 'inset', 'gap', 'padding')

TOKEN_FILES = {
    'chrome/browser/ui/views/rac/rac_tokens.h',
    'ui/webui/resources/css/rac_tokens.css',
}
# The motion engine turns tokens into Chromium's animation types, which can
# need Chromium's own curve names.
ENGINE_DIR = 'chrome/browser/ui/views/rac/motion/'
EXEMPT_PATCH_DIRS = ('rac/dev/',)
CXX = ('.cc', '.h', '.mm')
WEB = ('.css', '.html', '.ts', '.js', '.mjs')
# C++ in these folders is UI; WebUI files count wherever they are.
UI_DIRS = ('chrome/browser/ui/', 'ui/')
TEST_NAME = re.compile(r'(_unittest|_browsertest|_uitest|_interactive_uitest|_test)\.\w+$'
                       r'|(^|/)test(s|_data)?/|\.test\.\w+$')
EXCUSE = re.compile(r'motion-lint:\s*not motion\s*\(\s*\S[^)]*\)')

# A number that isn't part of a name, a hex color, or arithmetic on a token.
_NUM = r'(?<![\w.#])(?<![*/]\s)(?<![*/])(\d+\.?\d*|\.\d+)f?(?![\w.]|\s*[*/])'
# Numbers that never need a token: none, a half-pixel nudge, one.
TRIVIAL = {0.0, 0.5, 1.0}

# Each rule finds where a literal would be; group 1, if any, is the text
# whose numbers count. A rule without a group flags on its own.
CXX_RULES = [
    ('duration', re.compile(r'base::(?:Milliseconds|Seconds|Microseconds|Minutes|Hertz)'
                            r'\(([^()]*)\)|TimeDelta::FromMilliseconds\(([^()]*)\)')),
    ('curve', re.compile(r'gfx::Tween::[A-Z][A-Z0-9_]+')),
    ('curve', re.compile(r'(?:gfx::CubicBezier\b(?:\s+\w+)?\s*|'
                         r'CubicBezierTimingFunction::Create)[({]([^)}]*)')),
    ('radius', re.compile(r'\bk\w*(?:Radius|Corner)\w*\s*=\s*([^;]*)')),
    ('radius', re.compile(r'(?:SetRoundedCornerRadius|RoundedCornersF|DrawRoundRect|RoundRect|'
                          r'CreateRoundedRectBackground|CreateThemedRoundedRectBackground|'
                          r'CreateRoundedRectBorder|CreateThemedRoundedRectBorder|'
                          r'SetCornerRadius|set_corner_radius|setRectXY|MakeRectXY)\b\s*'
                          r'(?:\(|\{)(.*)')),
    ('inset', re.compile(r'\bk\w*(?:Inset|Outset)\w*\s*=\s*([^;]*)')),
    ('inset', re.compile(r'(?:gfx::Insets|gfx::Outsets)(?:::\w+)?\(([^()]*)')),
    ('inset', re.compile(r'(?:CreateEmptyBorder|CreatePaddedBorder)\(([^()]*)\)')),
    ('padding', re.compile(r'\bk\w*Padding\w*\s*=\s*([^;]*)')),
    ('gap', re.compile(r'\bk\w*(?:Gap|Spacing|Margin)\w*\s*=\s*([^;]*)')),
    ('gap', re.compile(r'(?:SetBetweenChildSpacing|set_between_child_spacing)\(([^()]*)\)')),
    # BoxLayout(orientation, insets, between_child_spacing).
    ('gap', re.compile(r'gfx::Insets(?:::\w+)?\([^()]*\)\s*,\s*([^,()]*)')),
]

_LENGTH = r'(?<![\w.#-])(\d+\.?\d*|\.\d+)(px|rem|em|%)?(?![\w.%])'
_CSS_TIME = re.compile(r'(?<![\w.#-])(\d+\.?\d*|\.\d+)(ms|s)\b')
WEB_RULES = [
    ('curve', re.compile(r'cubic-bezier\(|\blinear\(\s*-?[\d.]|'
                         r'(?:transition|animation)[\w-]*\s*:[^;]*\bease(?:-in-out|-in|-out)?\b')),
    ('radius', re.compile(r'(?:border(?:-[\w-]+)?-radius|--[\w-]*radius[\w-]*)\s*:\s*([^;]*)')),
    ('padding', re.compile(r'(?<![\w-])(?:--[\w-]*)?padding(?:-[\w-]+)?\s*:\s*([^;]*)')),
    ('gap', re.compile(r'(?<![\w-])(?:row-|column-)?gap\s*:\s*([^;]*)')),
    ('inset', re.compile(r'(?<![\w-])inset(?:-[\w-]+)?\s*:\s*([^;]*)')),
]
WEB_DURATION_LINE = re.compile(r'(?:transition|animation|duration|delay)', re.I)
# The Web Animations API takes milliseconds without a unit.
SCRIPT_DURATION = re.compile(r'\b(?:duration|delay)\s*:\s*([1-9]\d*)\b')


class Finding:
    """A literal on a line a patch adds."""

    def __init__(self, kind, path, line, patch):
        self.kind = kind
        self.path = path
        self.line = line
        self.patch = patch

    def key(self):
        return (self.kind, self.path, self.line)

    def __repr__(self):
        return f'Finding({self.kind}, {self.path}, {self.line!r})'


def normalize(line):
    return ' '.join(line.split())


def in_scope(path):
    if path in TOKEN_FILES or path.startswith(ENGINE_DIR) or TEST_NAME.search(path):
        return False
    if path.endswith(CXX):
        return path.startswith(UI_DIRS)
    return path.endswith(WEB)


def has_length(values):
    """Whether a CSS value holds a length other than 0 (or 50% for circles)."""
    for match in re.finditer(_LENGTH, re.sub(r'var\([^)]*\)|calc\(', ' ', values)):
        number, unit = float(match.group(1)), match.group(2) or ''
        if number == 0 or (unit == '%' and number == 50):
            continue
        # Unitless numbers in CSS are factors, not lengths.
        if unit:
            return True
    return False


def css_code(line):
    """The line without CSS and // comments."""
    line = re.sub(r'/\*.*?\*/', '', line)
    return re.sub(r'(^|\s)//.*$', '', line)


def literals(path, line):
    """The kinds of literal on one added line of `path`."""
    kinds = []
    if path.endswith(CXX):
        code = re.sub(r'//.*$', '', line)
        if not code.strip() or code.lstrip().startswith(('*', '/*', '#include')):
            return kinds
        for kind, rule in CXX_RULES:
            if kind in kinds or (kind == 'duration' and EXCUSE.search(line)):
                continue
            for match in rule.finditer(code):
                if match.re.groups and not any(
                        float(n) not in TRIVIAL
                        for span in match.groups() if span
                        for n in re.findall(_NUM, span)):
                    continue
                kinds.append(kind)
                break
        return kinds
    code = css_code(line)
    if not code.strip() or code.lstrip().startswith(('*', '/*', '<!--')):
        return kinds
    if WEB_DURATION_LINE.search(code) and not EXCUSE.search(line):
        times = _CSS_TIME.finditer(re.sub(r'var\([^)]*\)', ' ', code))
        script = path.endswith(('.ts', '.js', '.mjs')) and SCRIPT_DURATION.search(code)
        if script or any(float(m.group(1)) != 0 for m in times):
            kinds.append('duration')
    # A token named like a keyword, such as var(--ease-out), isn't one.
    plain = re.sub(r'var\([^)]*\)', ' ', code)
    for kind, rule in WEB_RULES:
        match = rule.search(plain if kind == 'curve' else code)
        if not match:
            continue
        if match.groups() and not has_length(match.group(1)):
            continue
        kinds.append(kind)
    return kinds


def series_patches():
    """rac's patches, in the order patches/series applies them."""
    names = [l.strip() for l in SERIES.read_text().splitlines()]
    return [PATCHES / n for n in names if n.startswith('rac/')]


def diff_path(header):
    """The tree path in a `--- ` or `+++ ` line, or None for /dev/null."""
    target = header[4:].split('\t')[0].strip()
    if target == '/dev/null':
        return None
    return re.sub(r'^(?:src|src\.orig|a|b)/', '', target)


def file_diffs(text):
    """Yields (path, [(sign, line)], deleted) for each file in a patch."""
    raw = text.splitlines()
    path, lines, deleted, in_hunk = None, [], False, False
    for i, line in enumerate(raw):
        # A removed line reading "-- x" shows as "--- x", so a header is only
        # a "--- " line followed by a "+++ " line.
        if line.startswith('--- ') and i + 1 < len(raw) and raw[i + 1].startswith('+++ '):
            if path:
                yield path, lines, deleted
            old, new = diff_path(line), diff_path(raw[i + 1])
            path, deleted, lines, in_hunk = new or old, new is None, [], False
            continue
        if line.startswith('+++ ') and i > 0 and raw[i - 1].startswith('--- '):
            continue
        if line.startswith('@@'):
            in_hunk = True
        elif line.startswith(('Index: ', '=====', 'diff ')):
            in_hunk = False
        elif path and in_hunk and line[:1] in ('+', '-'):
            lines.append((line[0], line[1:]))
    if path:
        yield path, lines, deleted


def net_added(patches):
    """{path: [(line, patch)]} for lines the patches still add at the end."""
    added = defaultdict(list)
    for patch, text in patches:
        for path, lines, deleted in file_diffs(text):
            if deleted:
                added.pop(path, None)
                continue
            for sign, line in lines:
                key = normalize(line)
                if sign == '+':
                    added[path].append((key, patch))
                    continue
                for i in range(len(added[path]) - 1, -1, -1):
                    if added[path][i][0] == key:
                        del added[path][i]
                        break
    return added


def find_literals(patches):
    """Every literal on the lines `patches` add, in UI files."""
    findings = []
    for path, lines in sorted(net_added(patches).items()):
        if not in_scope(path):
            continue
        for line, patch in lines:
            if patch.startswith(EXEMPT_PATCH_DIRS):
                continue
            for kind in literals(path, line):
                findings.append(Finding(kind, path, line, patch))
    return findings


def read_patches(paths):
    out = []
    for path in paths:
        path = Path(path).resolve()
        try:
            name = path.relative_to(PATCHES).as_posix()
        except ValueError:
            name = path.name
        out.append((name, path.read_text(encoding='utf-8', errors='replace')))
    return out


def read_files(folder, prefix):
    """Plain files as if a patch created each under `prefix`."""
    out = []
    for path in sorted(Path(folder).rglob('*')):
        if not path.is_file() or not path.name.endswith(CXX + WEB):
            continue
        tree_path = f'{prefix.rstrip("/")}/{path.relative_to(folder).as_posix()}'
        lines = path.read_text(encoding='utf-8').splitlines()
        body = '\n'.join('+' + l for l in lines)
        out.append((f'files/{path.name}', f'--- /dev/null\n+++ src/{tree_path}\n'
                    f'@@ -0,0 +1,{len(lines)} @@\n{body}\n'))
    return out


def read_allowlist(text):
    entries = Counter()
    for line in text.splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        kind, path, code = line.split('\t', 2)
        if kind not in KINDS:
            raise ValueError(f'unknown kind in allowlist: {kind}')
        entries[(kind, path, code)] += 1
    return entries


def render_allowlist(findings):
    lines = [
        '# Literals rac patches added before motion_lint.py. This list may only',
        '# shrink: replace a literal with a token, then run',
        '# `devutils/rac/motion_lint.py --refresh`.',
        '# kind<TAB>file<TAB>line',
    ]
    lines += sorted('\t'.join(f.key()) for f in findings)
    return '\n'.join(lines) + '\n'


def per_file(entries):
    counts = Counter()
    for (kind, path, _), n in entries.items():
        counts[(kind, path)] += n
    return counts


def growth(old, new):
    """(kind, file, old count, new count) wherever `new` has more."""
    old_counts, new_counts = per_file(old), per_file(new)
    return [(k, p, old_counts[(k, p)], n) for (k, p), n in sorted(new_counts.items())
            if n > old_counts[(k, p)]]


def compare(findings, allowed):
    """(findings not allowed, allowlist entries no longer found)."""
    remaining = Counter(allowed)
    new = []
    for finding in findings:
        if remaining[finding.key()] > 0:
            remaining[finding.key()] -= 1
        else:
            new.append(finding)
    stale = [key for key, n in remaining.items() for _ in range(n)]
    return new, stale


def print_counts(findings):
    by_kind = Counter(f.kind for f in findings)
    by_group = defaultdict(Counter)
    for f in findings:
        by_group[f.patch.split('/')[1] if f.patch.startswith('rac/') else f.patch][f.kind] += 1
    print('group'.ljust(22) + ''.join(k.rjust(10) for k in KINDS) + 'total'.rjust(8))
    for group in sorted(by_group):
        row = by_group[group]
        print(group.ljust(22) + ''.join(str(row[k]).rjust(10) for k in KINDS) +
              str(sum(row.values())).rjust(8))
    print('total'.ljust(22) + ''.join(str(by_kind[k]).rjust(10) for k in KINDS) +
          str(len(findings)).rjust(8))


def git_show(ref, path):
    relative = path.relative_to(ROOT).as_posix()
    result = subprocess.run(['git', '-C', str(ROOT), 'show', f'{ref}:{relative}'],
                            capture_output=True,
                            text=True,
                            check=False)
    return result.stdout if result.returncode == 0 else ''


def main():
    """CLI entrypoint"""
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('patches', nargs='*', type=Path, help='default: rac patches in series')
    parser.add_argument('--files', type=Path, help='lint plain files in this folder instead')
    parser.add_argument('--prefix', help='--files: the tree path the folder stands for')
    parser.add_argument('--allowlist', type=Path, default=ALLOWLIST)
    parser.add_argument('--refresh',
                        action='store_true',
                        help='rewrite the allowlist from the current literals, if none grew')
    parser.add_argument('--init', action='store_true', help='write the first allowlist')
    parser.add_argument('--base', help='fail if the allowlist grew since this git ref')
    parser.add_argument('--counts', action='store_true', help='print literals per group')
    args = parser.parse_args()

    try:
        if args.files:
            if not args.prefix:
                sys.exit('motion_lint: --files needs --prefix')
            patches = read_files(args.files, args.prefix)
        else:
            patches = read_patches(args.patches or series_patches())
        findings = find_literals(patches)
        exists = args.allowlist.exists()
        allowed = read_allowlist(args.allowlist.read_text()) if exists else Counter()
    except (OSError, ValueError) as error:
        sys.exit(f'motion_lint: {error}')

    if args.counts:
        print_counts(findings)

    if args.init:
        if exists:
            sys.exit(f'motion_lint: {args.allowlist} exists; use --refresh')
        args.allowlist.write_text(render_allowlist(findings))
        print(f'motion_lint: wrote {len(findings)} literals to {args.allowlist}')
        return

    failed = False
    current = Counter(f.key() for f in findings)
    if args.refresh:
        grew = growth(allowed, current)
        for kind, path, old, new in grew:
            print(f'{path}: {kind} literals grew from {old} to {new}')
        if grew:
            sys.exit('motion_lint: the allowlist only shrinks; use tokens instead')
        args.allowlist.write_text(render_allowlist(findings))
        print(f'motion_lint: allowlist now holds {len(findings)} literals')
        return

    if args.base:
        base = read_allowlist(git_show(args.base, args.allowlist))
        for kind, path, old, new in growth(base, allowed):
            print(f'{path}: allowlisted {kind} literals grew from {old} to {new} since '
                  f'{args.base}')
            failed = True

    new, stale = compare(findings, allowed)
    for finding in new:
        print(f'{finding.path}: {finding.kind} literal, added by {finding.patch}:\n'
              f'    {finding.line}')
    if stale:
        print(f'motion_lint: {len(stale)} allowlisted literals are gone; run '
              '`devutils/rac/motion_lint.py --refresh` to drop them')
    if new:
        print(f'motion_lint: {len(new)} literals need tokens (see rac_tokens.h)')
    if new or stale or failed:
        sys.exit(1)


if __name__ == '__main__':
    main()
