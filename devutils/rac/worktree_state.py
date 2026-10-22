#!/usr/bin/env python3

# Copyright 2025 The rac Authors
# You can use, redistribute, and/or modify this source code under
# the terms of the GPL-3.0 license that can be found in the LICENSE file.
"""Tracks which version of each patch is applied in a build tree.

The record ($tree/.pc/.rac_applied) holds "<sha256> <patch>" for each applied
patch, so sync can tell which patch files changed since they were applied.
A copy of each applied version is kept in $tree/.pc/.rac_patch_bytes/<sha256>,
so sync can check for unsaved edits even after the patch file changed.

usage: worktree_state.py <tree> <patches dir> <command>
  record            write the record and the copies from the patches dir
  compare           print "<keep> <applied> <wanted>": how many applied
                    patches still match the series and the record, how many
                    are applied, and how many the series lists
  matches           exit 0 if the applied stack equals the series
  check <keep>      exit 1 if popping the patches above the first <keep>
                    would throw away edits that aren't saved in a patch
"""

from pathlib import Path
import hashlib
import os
import subprocess
import sys
import tempfile

RECORD = '.rac_applied'
SAVED = '.rac_patch_bytes'
QUILT_PATCH_OPTS = '--unified --reject-format=unified'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def file_digest(path):
    return digest(path.read_bytes()) if path.exists() else 'missing'


def series(patches):
    names = []
    for line in (patches / 'series.merged').read_text().split('\n'):
        line = line.split(' #', 1)[0].strip()
        if line and not line.startswith('#'):
            names.append(line)
    return names


def applied(tree):
    return list(filter(None, (tree / '.pc' / 'applied-patches').read_text().split('\n')))


def read_record(tree):
    lines = filter(None, (tree / '.pc' / RECORD).read_text().split('\n'))
    return dict(line.split(' ', 1)[::-1] for line in lines)


def patch_source(patches, name):
    """The patch file in a checkout. An unmerged checkout (he unmerge) keeps
    Helium's patches in its submodule instead of in patches/."""
    path = patches / name
    core = patches.parent / 'helium-chromium' / 'patches' / name
    return core if not path.exists() and core.exists() else path


def record(tree, patches):
    saved = tree / '.pc' / SAVED
    saved.mkdir(exist_ok=True)
    lines = []
    for name in applied(tree):
        path = patch_source(patches, name)
        if path.exists():
            data = path.read_bytes()
            fingerprint = digest(data)
            if not (saved / fingerprint).exists():
                (saved / fingerprint).write_bytes(data)
        else:
            fingerprint = 'missing'
        lines.append(f'{fingerprint} {name}\n')
    path = tree / '.pc' / RECORD
    temporary = path.with_name(RECORD + '.tmp')
    temporary.write_text(''.join(lines))
    temporary.replace(path)
    kept = {line.split(' ', 1)[0] for line in lines}
    for copy in saved.iterdir():
        if copy.name not in kept:
            copy.unlink()


def compare(tree, patches):
    wanted = series(patches)
    names = applied(tree)
    recorded = read_record(tree)
    keep = 0
    for i, name in enumerate(names):
        path = patches / name
        if (i >= len(wanted) or wanted[i] != name or not path.exists()
                or digest(path.read_bytes()) != recorded.get(name)):
            break
        keep = i + 1
    print(keep, len(names), len(wanted))


def preimages(tree, name):
    """The files a patch touches, as quilt saved them before applying it.
    quilt saves a file the patch creates as an empty backup."""
    folder = tree / '.pc' / name
    return {
        path.relative_to(folder).as_posix(): path.read_bytes()
        for path in folder.rglob('*')
        if path.is_file() and not path.is_symlink() and path.name != '.timestamp'
    }


def may_have_changed(tree, name, files):
    """Like quilt pop: a patch whose files are all older than the moment it was
    applied can't hold unsaved edits."""
    stamp = tree / '.pc' / name / '.timestamp'
    if not stamp.exists():
        return True
    applied_at = stamp.stat().st_mtime_ns
    for file in files:
        path = tree / file
        if not path.exists() or path.stat().st_mtime_ns >= applied_at:
            return True
    return False


def replay(data, before):
    """Applies a patch to its preimages with quilt in a temporary tree and
    returns the result, or None if it doesn't apply."""
    with tempfile.TemporaryDirectory(prefix='rac-patch-check-') as directory:
        root = Path(directory)
        for file, contents in before.items():
            if contents:
                (root / file).parent.mkdir(parents=True, exist_ok=True)
                (root / file).write_bytes(contents)
        (root / 'patches').mkdir()
        (root / 'patches' / 'check.patch').write_bytes(data)
        (root / 'patches' / 'series').write_text('check.patch\n')
        env = dict(os.environ, QUILT_PATCHES='patches', QUILT_SERIES='series', QUILT_PC='.pc',
                   QUILT_PATCH_OPTS=QUILT_PATCH_OPTS)
        result = subprocess.run(['quilt', '--quiltrc', '-', 'push', '-q'],
                                cwd=root,
                                env=env,
                                capture_output=True,
                                check=False)
        if result.returncode != 0:
            return None
        return {
            file: (root / file).read_bytes() if (root / file).is_file() else b''
            for file in before
        }


def check(tree, patches, keep):
    """Before sync pops the patches above `keep` with quilt pop -f, checks that
    each one's files hold exactly what the patch produced, so popping loses
    nothing. Sync reverts rac's names first, so string files compare cleanly.
    A missing file counts as empty, as it does for quilt."""
    names = applied(tree)[keep:]
    recorded = read_record(tree)
    saved = tree / '.pc' / SAVED
    for index, name in enumerate(names):
        before = preimages(tree, name)
        if not may_have_changed(tree, name, before):
            continue

        # A file's state after this patch is the backup of the next patch that
        # touches it, or the file itself if no later patch does.
        expected = {}
        for file in before:
            later = next((tree / '.pc' / n / file
                          for n in names[index + 1:] if (tree / '.pc' / n / file).is_file()),
                         tree / file)
            expected[file] = later.read_bytes() if later.is_file() else b''

        # The version that was applied, and the current file, which matches
        # the tree if the edits were saved with quilt refresh.
        fingerprint = recorded.get(name)
        copy = saved / (fingerprint or 'none')
        has_copy = copy.is_file() and file_digest(copy) == fingerprint
        current = patches / name
        candidates = [copy.read_bytes()] if has_copy else []
        candidates.append(current.read_bytes() if current.exists() else b'')
        results = [replay(data, before) for data in candidates]
        if expected in results:
            continue

        # Records written before sync kept copies only have the hash, which
        # can't rebuild a version that has since changed or been removed.
        if fingerprint and not has_copy and (fingerprint == 'missing'
                                             or file_digest(current) != fingerprint):
            print(f"rac worktree: can't check {name} for unsaved edits; it was "
                  'applied before sync kept copies of applied patches',
                  file=sys.stderr)
            continue
        result = next((r for r in results if r is not None), before)
        changed = sorted(f for f in before if result.get(f, b'') != expected[f])
        sys.exit(f"rac worktree: {', '.join(changed) or 'a file'} in {name} has changes that "
                 "aren't saved in the patch, and popping it would throw them away")


def main():
    tree, patches, command = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
    if command == 'record':
        record(tree, patches)
    elif command == 'compare':
        compare(tree, patches)
    elif command == 'matches':
        sys.exit(0 if series(patches) == applied(tree) else 1)
    elif command == 'check':
        check(tree, patches, int(sys.argv[4]))
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main()
