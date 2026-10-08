#!/usr/bin/env python3
# Copyright 2025 The rac Authors
# You can use, redistribute, and/or modify this source code under
# the terms of the GPL-3.0 license that can be found in the LICENSE file.
"""Verify quilt's saved postimages before worktree sync force-pops patches.

.pc holds preimages, not the applied patch bytes. Keep those bytes beside
.rac_applied so an incoming patch cannot hide an unsaved source edit.
Reconstruction uses real quilt in tiny temporary trees, never the build tree.
"""

from pathlib import Path
import argparse
import hashlib
import os
import re
import subprocess
import sys
import tarfile
import tempfile

import dev_names


def digest(data):
    return hashlib.sha256(data).hexdigest()


def relative(name):
    path = Path(name)
    if (not name or path.is_absolute() or '..' in path.parts
            or name != path.as_posix() or any(c.isspace() for c in name)):
        raise ValueError(f'unsupported quilt path: {name!r}')
    return path


def applied(tree):
    path = tree / '.pc' / 'applied-patches'
    names = path.read_text().splitlines() if path.exists() else []
    for name in names:
        relative(name)
    if len(set(names)) != len(names):
        raise ValueError('duplicate applied patches')
    return names


def series(patches):
    names = []
    for line in (patches / 'series.merged').read_text().splitlines():
        fields = line.split('#', 1)[0].split()
        if not fields:
            continue
        if len(fields) != 1:
            raise ValueError('sync verification supports the default quilt -p1 '
                             'series only')
        relative(fields[0])
        names.append(fields[0])
    if len(set(names)) != len(names):
        raise ValueError('duplicate patches in series')
    return names


def read_record(tree, names):
    path = tree / '.pc' / '.rac_applied'
    if not path.exists():
        if names:
            raise ValueError('missing applied-patch baseline; preserve edits and '
                             'restore the originally applied patch versions '
                             'before explicitly recording them')
        return {}
    recorded = {}
    for line in path.read_text().splitlines():
        fields = line.split(' ', 1)
        if len(fields) != 2 or not re.fullmatch('[0-9a-f]{64}', fields[0]):
            raise ValueError('malformed applied-patch baseline')
        fingerprint, name = fields
        relative(name)
        if name in recorded:
            raise ValueError('duplicate patch in applied-patch baseline')
        recorded[name] = fingerprint
    # Quilt new/add/refresh appends saved patches without updating our record.
    # Only accept that exact recorded prefix, or the previous exact-set case.
    # The unrecorded suffix still needs full postimage verification in plan.
    if set(recorded) != set(names) and list(recorded) != names[:len(recorded)]:
        raise ValueError('applied stack differs from its baseline; preserve '
                         'edits and explicitly verify/record the saved stack')
    return recorded


def preimages(tree, name):
    folder = tree / '.pc' / relative(name)
    if not folder.is_dir():
        raise ValueError(f'missing quilt preimages for {name}')
    result = {}
    for path in folder.rglob('*'):
        if path.is_symlink():
            raise ValueError(f'unsupported symlink preimage: {path}')
        if path.is_file() and path != folder / '.timestamp':
            key = path.relative_to(folder).as_posix()
            relative(key)
            result[key] = path.read_bytes()
    return result


def postimages(data, before):
    """Let quilt parse/apply the patch and report every file it changes."""
    with tempfile.TemporaryDirectory(prefix='rac-quilt-check-') as directory:
        root = Path(directory)
        for name, contents in before.items():
            # Quilt represents missing originals with empty backup files.
            # An unchanged registered empty file is ambiguous: replay it as
            # absent so verification refuses rather than letting pop drop it.
            if contents != b'':
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(contents)
        patches = root / 'patches'
        patches.mkdir()
        (patches / 'check.patch').write_bytes(data)
        (patches / 'series').write_text('check.patch\n')
        env = dict(os.environ, QUILT_PATCHES=str(patches), QUILT_SERIES='series',
                   QUILT_PC='.pc',
                   QUILT_PATCH_OPTS='--unified --reject-format=unified')
        result = subprocess.run(['quilt', '--quiltrc', '-', 'push', '-q'],
                                cwd=root, env=env, capture_output=True, check=False)
        if result.returncode != 0:
            return None
        touched = preimages(root, 'check.patch')
        return {name: dev_names.source_bytes(root, name, missing=True)
                for name in before.keys() | touched.keys()}


def patch_path(patches, name, core_patches=None):
    """Only seeding may read core patches moved back by the base's unmerge."""
    path = patches / name
    if core_patches is not None and not path.exists():
        return core_patches / name
    return path


def verify(tree, patches, names, recorded, start=0, *, core_patches=None):
    """Check each affected postimage against its next preimage or live source.

    A refreshed patch is accepted only if its current bytes fully reconstruct
    that saved boundary. An additional unsaved edit still fails verification.
    """
    originals = dev_names.originals(tree)
    names = names[start:]
    images = [preimages(tree, name) for name in names]
    for index, name in enumerate(names):
        before = images[index]
        expected = {}
        missing_markers = set()
        for file in before:
            later = next((image[file] for image in images[index + 1:] if file in image), None)
            if later is not None:
                expected[file] = later
                if later == b'':
                    missing_markers.add(file)
            elif file in originals:
                expected[file] = originals[file]
            else:
                expected[file] = dev_names.source_bytes(tree, file, missing=True)
        candidates = []
        current = patch_path(patches, name, core_patches)
        fingerprint = recorded.get(name)
        if fingerprint:
            saved = tree / '.pc' / '.rac_patch_bytes' / fingerprint
            if saved.exists():
                data = saved.read_bytes()
                if digest(data) != fingerprint:
                    raise ValueError(f'corrupt saved patch baseline: {name}')
                candidates.append(data)
            else:
                # A legacy hash alone is useful only while the patch is
                # unchanged. Never adopt an incoming replacement or removal.
                if not current.exists() or digest(current.read_bytes()) != fingerprint:
                    raise ValueError(f'missing original patch bytes for {name}; '
                                     'restore that recorded version first')
        if current.exists():
            candidates.append(current.read_bytes())

        def matches(data):
            actual = postimages(data, before)
            if actual is None:
                return False
            # Quilt stores missing preimages as empty files. Normalize only
            # intermediate backups; live sources keep strict existence checks.
            for file in missing_markers:
                if file in actual and actual[file] is None:
                    actual[file] = b''
            return actual == expected

        if not any(matches(data) for data in candidates):
            raise ValueError(f'unrefreshed changes or unverifiable saved patch: '
                             f'{name}; preserve edits or run quilt refresh '
                             'with the originally applied patches')


def record(tree, patches, check=True, *, core_patches=None):
    names = applied(tree)
    # Explicit initialization, including setup, verifies the supplied source
    # versions. Setup supplies the BASE patches, not incoming worktree patches.
    # The applied names are authoritative here: a built base may be unmerged
    # for committing and have no generated series.
    if check:
        verify(tree, patches, names, {}, core_patches=core_patches)
    saved = tree / '.pc' / '.rac_patch_bytes'
    saved.mkdir(exist_ok=True)
    lines = []
    for name in names:
        data = patch_path(patches, name, core_patches).read_bytes()
        fingerprint = digest(data)
        (saved / fingerprint).write_bytes(data)
        lines.append(f'{fingerprint} {name}\n')
    path = tree / '.pc' / '.rac_applied'
    temporary = path.with_suffix('.tmp')
    temporary.write_text(''.join(lines))
    temporary.replace(path)


def seed(tree, patches):
    """Preserve a clone's existing record, filling only verified legacy bytes."""
    # he unmerge returns upstream patches to this BASE's core submodule.
    # Never enable this fallback for plan/record/save in the incoming tree.
    core_patches = patches.parent / 'helium-chromium' / 'patches'
    names = applied(tree)
    path = tree / '.pc' / '.rac_applied'
    if not path.exists():
        record(tree, patches, core_patches=core_patches)
        return
    recorded = read_record(tree, names)
    verify(tree, patches, names, recorded, core_patches=core_patches)
    saved = tree / '.pc' / '.rac_patch_bytes'
    saved.mkdir(exist_ok=True)
    for name, fingerprint in recorded.items():
        if not (saved / fingerprint).exists():
            data = patch_path(patches, name, core_patches).read_bytes()
            if digest(data) != fingerprint:
                raise ValueError(f'base patch no longer matches its record: {name}')
            (saved / fingerprint).write_bytes(data)


def plan(tree, patches):
    names = applied(tree)
    wanted = series(patches)
    recorded = read_record(tree, names)
    keep = 0
    for name, desired in zip(names, wanted):
        path = patches / name
        if name != desired or not path.exists() or digest(path.read_bytes()) != recorded.get(name):
            break
        keep += 1
    noop = (keep == len(names) == len(wanted)
            and dev_names.status(tree) == 'applied')
    if keep < len(names):
        verify(tree, patches, names, recorded, keep)
    elif not noop:
        # Check branding before either restoring it for a push or completing
        # missing name passes. A true no-op does neither, preserving edits
        # and legacy archives until an operation actually needs to alter them.
        dev_names.originals(tree)
    print(keep, len(names), len(wanted), int(noop))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['plan', 'record', 'save', 'seed', 'matches'])
    parser.add_argument('tree', type=Path)
    parser.add_argument('patches', type=Path)
    args = parser.parse_args()
    try:
        if args.command == 'plan':
            plan(args.tree, args.patches)
        elif args.command == 'record':
            record(args.tree, args.patches)
        elif args.command == 'save':
            # Internal to sync: its affected sources were already verified
            # and quilt has now applied the wanted versions without force.
            record(args.tree, args.patches, check=False)
        elif args.command == 'seed':
            seed(args.tree, args.patches)
        else:
            sys.exit(0 if applied(args.tree) == series(args.patches) else 1)
    except (OSError, ValueError, tarfile.TarError) as error:
        sys.exit(f'rac worktree: {error}')


if __name__ == '__main__':
    main()
