#!/usr/bin/env python3

# Copyright 2026 The rac Authors
# You can use, redistribute, and/or modify this source code under
# the terms of the GPL-3.0 license that can be found in the LICENSE file.
"""Checks that every file a rac patch points at is one the patches create.

A patch that adds `#include "chrome/browser/ui/rac/x.h"` or a BUILD.gn source
`"rac/x.cc"` applies cleanly even when no patch ever creates x.h or x.cc: the
edit lands, the patch-series checks pass, and the missing file only breaks
the build at `gn gen`. That is what broke main in
https://github.com/notkainoa/rac/pull/212 — a patch added includes, sources,
and a label for files nothing created.

This walks the same patch plan as patch_surface.py — Helium's patches, then
helium-macos's, then rac's — tracking which files the patches create and
delete, so a file one patch creates satisfies references in every other. From
the added lines of rac's own patches it collects the references a build
resolves:

    #include "X" and #import "X"    in any file
    import "X";                    in .mojom files
    "//dir:target" and "//dir"     in BUILD.gn and .gni files: GN labels, which
                                   need dir/BUILD.gn. "//dir/" is a data
                                   directory, and a name with a file
                                   extension ("//x/y.gni", "//x/y.cc" in
                                   sources) is a file path
    other quoted strings there     source paths relative to the file's
                                   directory (../ resolves)

Only rac-owned paths are checked — a path with a component named rac or
starting with rac_, which Chromium doesn't have and rac's tree must therefore
make. A reference is met when its file is patch-created and survives to the
end, is a destination of the resource lists he copies into the tree, or is
generated: X.mojom.h and its -forward/-shared/-blink/-blink-forward/
-test-utils/-webui forms come from X.mojom, X.pb.h from X.proto,
buildflags.h from a BUILD.gn in its directory, and a $target_gen_dir or
$root_gen_dir output from the patched build files. A path under a grit or gen
directory is generated and skipped instead. A line a later patch removes
cancels its reference, as does deleting the file that held it.

Run from the repository root:
    python3 -I devutils/rac/patch_refs_lint.py
"""

from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
import argparse
import os
import posixpath
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import patch_surface  # pylint: disable=wrong-import-position

ROOT = Path(__file__).resolve().parents[2]
ALLOWLIST = Path(__file__).resolve().with_name('patch_refs_allow.txt')

INCLUDE = re.compile(r'#\s*(?:include|import)\s*"([^"]+)"')
MOJOM_IMPORT = re.compile(r'\bimport\s+"([^"]+)"\s*;')
GN_STRING = re.compile(r'"([^"\n]*)"')
FILE_EXTENSION = re.compile(r'\.[0-9A-Za-z_]+$')
GENERATED_OUTPUT = re.compile(r'"\$(target|root)_gen_dir/([^"]+)"')

# Headers and bindings the mojom compiler makes from X.mojom.
MOJOM_OUTPUTS = ('.mojom.h', '.mojom-forward.h', '.mojom-shared.h', '.mojom-blink.h',
                 '.mojom-blink-forward.h', '.mojom-test-utils.h', '.mojom-webui.js',
                 '.mojom-webui.ts')


class RefsError(Exception):
    """A problem with the inputs, not with the patches."""


@dataclass
class Reference:
    """One reference an added line makes, and the tree path it needs."""
    patch: str    # the patch's name in the series
    file: str     # the file the reference sits in (-p1 name)
    path: str     # the reference as written, for the report
    target: str   # the tree path it needs: the path itself, or dir/BUILD.gn
    kind: str     # 'include', 'gn source', 'gn label', 'gn dir'


@dataclass
class Result:
    checked: int = 0       # rac-owned references whose target exists
    skipped: int = 0       # under a grit or gen directory, never checked
    allowed: int = 0       # named in the allowlist
    missing: list = field(default_factory=list)  # Reference objects


def file_sections(text):
    """Each file in a unified diff as (old, new, changed lines), -p1 names.

    The same header reading as patch_surface.parse_patch: a/ and b/ prefixes,
    src/ names with a tab timestamp, quoted names, and /dev/null. Changed
    lines keep their +/- sign; context lines are dropped.
    """
    lines = text.split('\n')
    sections, i = [], 0
    while i < len(lines):
        if not (lines[i].startswith('--- ') and i + 1 < len(lines)
                and lines[i + 1].startswith('+++ ')):
            i += 1
            continue
        old = patch_surface._strip_name(lines[i][4:])
        new = patch_surface._strip_name(lines[i + 1][4:])
        i += 2
        body = []
        while i < len(lines):
            header = patch_surface.HUNK_HEADER.match(lines[i])
            if not header:
                break
            old_left = 1 if header.group(1) is None else int(header.group(1))
            new_left = 1 if header.group(2) is None else int(header.group(2))
            i += 1
            # Count the body by its header, like parse_patch: a removed line
            # that starts with "-- " reads just like the next file's "--- ".
            while i < len(lines) and (old_left > 0 or new_left > 0):
                kind = lines[i][:1]
                if kind == '-':
                    old_left -= 1
                    body.append(lines[i])
                elif kind == '+':
                    new_left -= 1
                    body.append(lines[i])
                elif kind != '\\':
                    old_left -= 1
                    new_left -= 1
                i += 1
            while i < len(lines) and lines[i].startswith('\\'):
                i += 1
        sections.append((old, new, body))
    return sections


def is_gn_file(name):
    base = posixpath.basename(name)
    return base == 'BUILD.gn' or base.endswith('.gni')


def has_extension(name):
    return FILE_EXTENSION.search(posixpath.basename(name)) is not None


def references_in(file_name, text):
    """The references one added or removed line makes: (kind, written, target)."""
    refs = [('include', name, name) for name in INCLUDE.findall(text)]
    if file_name.endswith('.mojom'):
        refs += [('include', name, name) for name in MOJOM_IMPORT.findall(text)]
    if not is_gn_file(file_name):
        return refs
    directory = posixpath.dirname(file_name)
    for string in GN_STRING.findall(text):
        if string.startswith('//'):
            body = string[2:]
            if body.endswith('/'):
                # data = [ "//dir/" ] names a directory, not a target.
                refs.append(('gn dir', string, body.rstrip('/')))
            elif ':' in body:
                refs.append(('gn label', string, body.split(':')[0] + '/BUILD.gn'))
            elif has_extension(body):
                # "//dir/file.gni" in import() or "//dir/file.cc" in sources.
                refs.append(('gn source', body, body))
            else:
                # "//dir" means "//dir:dir".
                refs.append(('gn label', string, body + '/BUILD.gn'))
        elif (has_extension(string)
              # A libs entry ("AppKit.framework") names a system framework
              # bundle, not a file under the build file's directory.
              and not string.endswith('.framework')
              # "$dir/x", "{x}", "*.cc", ":target", "a b" aren't file paths.
              and not any(c in string for c in '${*: ')):
            path = posixpath.normpath(f'{directory}/{string}')
            refs.append(('gn source', path, path))
    return refs


def generated_in(file_name, text):
    """The include-visible paths a build-file line says it generates."""
    base = posixpath.dirname(file_name)
    for which, rest in GENERATED_OUTPUT.findall(text):
        if which == 'root':
            yield rest
        else:
            yield posixpath.normpath(f'{base}/{rest}')


def rac_owned(path):
    """Whether a path is rac's to make: a component named rac or rac_*."""
    return any(part == 'rac' or part.startswith('rac_') for part in path.split('/'))


def read_allowlist(path):
    """The allowlist file's paths, without blank lines and # comments."""
    try:
        lines = Path(path).read_text(encoding='utf-8').split('\n')
    except OSError:
        return set()
    allowed = set()
    for line in lines:
        name = line.split('#', 1)[0].strip()
        if name:
            allowed.add(name)
    return allowed


def read_destinations(paths):
    """The destinations the resource lists copy into the tree: <src> <dest>."""
    destinations = set()
    for path in paths:
        try:
            lines = Path(path).read_text(encoding='utf-8').split('\n')
        except OSError:
            continue
        for line in lines:
            fields = line.split('#', 1)[0].split()
            if len(fields) >= 2:
                destinations.add(fields[1])
    return destinations


def satisfies(path, created, resources, generated, seen=()):
    """Whether path exists once the patches land and the build generates."""
    if path in seen:
        return False
    if path in created or path in resources or path in generated:
        return True
    seen = seen + (path,)
    for suffix in MOJOM_OUTPUTS:
        if path.endswith(suffix):
            return satisfies(path[:-len(suffix)] + '.mojom', created, resources,
                             generated, seen)
    if path.endswith('.pb.h'):
        return satisfies(path[:-len('.pb.h')] + '.proto', created, resources,
                         generated, seen)
    if posixpath.basename(path).endswith('buildflags.h'):
        return posixpath.join(posixpath.dirname(path), 'BUILD.gn') in created
    return False


def lint(helium_patches, platform_patches, resources=None, allowlist=()):
    """The references rac's patches make that no patch creates or generates."""
    plan = patch_surface.build_plan(helium_patches, platform_patches)
    created = set()         # files the patches create, minus later deletions
    generated = {}          # $*_gen_dir output -> the build file that makes it
    live = []               # Reference objects not yet canceled
    for ref in plan:
        try:
            text = ref.path.read_bytes().decode('utf-8', errors='surrogateescape')
        except OSError as error:
            raise RefsError(f'cannot read {ref.path}: {error}') from error
        added = []          # this patch's references join live only after it,
                            # so its own - lines can't cancel its + lines
        for old, new, body in file_sections(text):
            name = new or old
            for line in body:
                content = line[1:]
                if line[0] == '-':
                    removed = {(target, kind)
                               for kind, _, target in references_in(name, content)}
                    live = [r for r in live
                            if r.file != name or (r.target, r.kind) not in removed]
                elif ref.layer == patch_surface.RAC:
                    added += [Reference(ref.name, name, written, target, kind)
                              for kind, written, target in references_in(name, content)]
                    if is_gn_file(name):
                        for path in generated_in(name, content):
                            generated[path] = name
            if old is None:
                created.add(new)
            elif new is None:
                created.discard(old)
                generated = {p: f for p, f in generated.items() if f != old}
                live = [r for r in live if r.file != old]
            elif old != new and old in created:
                # A rename (--- a/x, +++ b/y) moves a created file.
                created.discard(old)
                created.add(new)
        live += added
    resources = read_destinations(resources or [])
    allowlist = set(allowlist)
    result = Result()
    for ref in live:
        if not rac_owned(ref.target):
            continue
        if ref.target in allowlist:
            result.allowed += 1
        elif 'grit' in ref.target.split('/') or 'gen' in ref.target.split('/'):
            result.skipped += 1
        elif ref.kind == 'gn dir':
            if any(path.startswith(ref.target + '/') for path in created):
                result.checked += 1
            else:
                result.missing.append(ref)
        elif satisfies(ref.target, created, resources, set(generated)):
            result.checked += 1
        else:
            result.missing.append(ref)
    return result


def write_summary(result):
    """A short report for the GitHub job summary, if it wants one."""
    summary = os.environ.get('GITHUB_STEP_SUMMARY')
    if not summary:
        return
    lines = ['## Patch reference lint', '']
    if result.missing:
        lines.append(f'**{len(result.missing)} references point at files no patch '
                     'creates.**')
        lines.append('')
        by_patch = defaultdict(list)
        for ref in result.missing:
            by_patch[ref.patch].append(ref)
        for patch, refs in by_patch.items():
            lines.append(f'### {patch}')
            lines += [f'- `{ref.file}` references `{ref.path}` ({ref.kind})'
                      for ref in refs]
            lines.append('')
    else:
        lines.append('Every rac-owned reference points at a file the patches '
                     'make.')
        lines.append('')
    lines.append(f'{result.checked} checked, {result.skipped} skipped '
                 f'(grit/gen), {result.allowed} allowed, '
                 f'{len(result.missing)} missing.')
    try:
        with open(summary, 'a', encoding='utf-8') as output:
            output.write('\n'.join(lines) + '\n')
    except OSError as error:
        print(f'patch_refs_lint: could not write the job summary: {error}',
              file=sys.stderr)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description='Check that every rac-owned file a patch references is one '
                    'the patches create.')
    parser.add_argument('--helium-patches', type=Path, metavar='DIR',
                        default=ROOT / 'helium-chromium' / 'patches',
                        help="Helium core's patch directory (default: %(default)s)")
    parser.add_argument('--patches', type=Path, metavar='DIR', default=ROOT / 'patches',
                        help="helium-macos's patch directory (default: %(default)s)")
    parser.add_argument('--resources', type=Path, metavar='DIR',
                        default=ROOT / 'resources',
                        help="directory of resource lists (default: %(default)s)")
    parser.add_argument('--allowlist', type=Path, metavar='FILE', default=ALLOWLIST,
                        help='paths to accept as satisfied (default: %(default)s)')
    args = parser.parse_args(argv)
    resources = [args.resources / 'platform_resources.txt',
                 args.resources / 'branding.txt',
                 args.helium_patches.parent / 'resources' / 'helium_resources.txt']
    try:
        result = lint(args.helium_patches, args.patches, resources,
                      read_allowlist(args.allowlist))
    except (RefsError, patch_surface.SurfaceError) as error:
        print(f'patch_refs_lint: {error}', file=sys.stderr)
        return 2
    missing = defaultdict(list)
    for ref in result.missing:
        missing[ref.patch].append(ref)
    for patch, refs in missing.items():
        print(f'{patch}:')
        for ref in refs:
            print(f'  {ref.file}: references {ref.path} ({ref.kind}), '
                  'which no patch creates')
    print(f'patch_refs_lint: {result.checked} rac-owned references checked, '
          f'{result.skipped} skipped (grit/gen), {result.allowed} allowed, '
          f'{len(result.missing)} missing')
    write_summary(result)
    return 1 if result.missing else 0


if __name__ == '__main__':
    sys.exit(main())
