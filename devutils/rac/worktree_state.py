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
  snapshot <keep>   record a hash and the mtime of every file the patches
                    above the first <keep> touched, so restore can give the
                    mtime back when a push writes the same bytes
  restore           set the recorded mtime on each file whose content is
                    unchanged, then delete the record
"""

from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import tempfile

RECORD = '.rac_applied'
SAVED = '.rac_patch_bytes'
MTIMES = '.rac_mtimes.json'
QUILT_PATCH_OPTS = '--unified --reject-format=unified'
# How many committed versions of a patch check() tries before refusing.
GIT_VERSIONS = 20


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
            copy = saved / fingerprint
            # Rewrites a copy that an interrupted record left short. The rename
            # means a copy is either whole or absent.
            if file_digest(copy) != fingerprint:
                temporary = copy.with_name(fingerprint + '.tmp')
                temporary.write_bytes(data)
                temporary.replace(copy)
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


def committed_versions(patches, name):
    """(commit, bytes) for recent committed versions of a patch file, newest
    first. --reflog also reaches the side of a rebase that HEAD no longer
    does, such as a refresh committed before the rebase changed the patch.
    Helium's patches live in the submodule's repository."""
    checkout = patches.parent
    for repo in (checkout, checkout / 'helium-chromium'):
        path = Path('patches') / name
        if not (repo / path).exists() and repo != checkout:
            continue
        log = subprocess.run(['git', '-C', repo, 'log', '--all', '--reflog', '--format=%H',
                              f'-n{GIT_VERSIONS}', '--', path.as_posix()],
                             capture_output=True, text=True, check=False)
        if log.returncode != 0:
            continue
        for commit in log.stdout.split():
            show = subprocess.run(['git', '-C', repo, 'show', f'{commit}:{path.as_posix()}'],
                                  capture_output=True, check=False)
            if show.returncode == 0:
                yield commit, show.stdout


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
    each one's files hold exactly what some saved version of the patch
    produced, so popping loses nothing. Sync reverts rac's names first, so
    string files compare cleanly. A missing file counts as empty, as it does
    for quilt."""
    names = applied(tree)[keep:]
    recorded = read_record(tree)
    saved = tree / '.pc' / SAVED
    # Records written before sync kept copies have no copies folder at all.
    old_record = not saved.is_dir()
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

        tried = {}

        def produces_tree(data):
            key = digest(data)
            if key not in tried:  # an unchanged patch's copy equals its file
                tried[key] = replay(data, before)
            return tried[key] == expected

        # The version sync applied, then the current file, which matches the
        # tree after a quilt refresh.
        fingerprint = recorded.get(name)
        copy = saved / (fingerprint or 'none')
        has_copy = fingerprint not in (None, 'missing') and file_digest(copy) == fingerprint
        current = patches / name
        if has_copy and produces_tree(copy.read_bytes()):
            continue
        if produces_tree(current.read_bytes() if current.exists() else b''):
            continue
        # A refresh that was committed, and then changed again by a rebase
        # before any sync, is only in git. Popping that loses nothing.
        commit = next((c for c, data in committed_versions(patches, name) if produces_tree(data)),
                      None)
        if commit:
            print(f'rac worktree: {name} holds the version committed in {commit[:12]}',
                  file=sys.stderr)
            continue

        # An old record has only the hash, which can't rebuild a version that
        # has since changed or been removed.
        if old_record and fingerprint and (fingerprint == 'missing'
                                           or file_digest(current) != fingerprint):
            print(f"rac worktree: can't check {name} for unsaved edits; it was "
                  'applied before sync kept copies of applied patches',
                  file=sys.stderr)
            continue
        result = next((r for r in tried.values() if r is not None), before)
        changed = sorted(f for f in before if result.get(f, b'') != expected[f])
        sys.exit(
            f"rac worktree: {', '.join(changed) or 'a file'} in {name} doesn't match "
            'any saved or committed version of the patch, so popping it would throw '
            'those edits away.\n'
            f'  See them with: (cd build/src && quilt diff -z -P {name})\n'
            '  That diff is against the patch file as it is now. If a rebase or pull '
            "changed the patch, a quilt refresh would undo that change, so don't refresh "
            'to keep the edits until you have compared them with git log -p on the patch.\n'
            '  To throw the edits away instead, run: devutils/rac/worktree.sh sync --discard')


def build_marker(tree):
    """The mtimes a build updates, per output dir. If one changed between
    snapshot and restore, a build ran in between: its outputs were made from
    other content, so giving sources their old mtimes back would let siso
    take stale outputs as up to date. gn gen alone counts too: build.ninja
    made from a popped BUILD.gn would look newer than the restored file."""
    marker = {}
    for name in ('.siso_fs_state', '.ninja_log', 'build.ninja', 'build.ninja.stamp'):
        for path in sorted((tree / 'out').glob(f'*/{name}')):
            if path.is_file():
                marker[path.relative_to(tree).as_posix()] = path.stat().st_mtime_ns
    return marker


def touched(tree, name):
    """The files quilt saved before applying a patch, without reading them."""
    folder = tree / '.pc' / name
    return [
        path.relative_to(folder).as_posix() for path in folder.rglob('*')
        if path.is_file() and not path.is_symlink() and path.name != '.timestamp'
    ]


def snapshot(tree, keep):
    """Records a hash and the mtime of every file the patches above `keep`
    touched, so restore() can tell a rewrite of the same bytes from a real
    change and give the old mtime back.

    A record left by a sync that failed after its pop is kept, as long as no
    build ran since: its files were rewritten by that pop, and the retry
    pops less, so a fresh record alone would miss them. Its entries win over
    the new ones, since they hold the tree from before that sync."""
    marker = build_marker(tree)
    pending = read_mtimes(tree)
    files = {}
    if pending is not None and pending['build'] == marker:
        files = pending['files']
    elif pending is not None:
        print('rac worktree: the tree was built since the last snapshot; '
              'dropping it', file=sys.stderr)
    for name in applied(tree)[keep:]:
        for file in touched(tree, name):
            path = tree / file
            if file not in files and path.is_file() and not path.is_symlink():
                files[file] = {'mtime_ns': path.stat().st_mtime_ns,
                               'sha256': file_digest(path)}
    path = tree / '.pc' / MTIMES
    temporary = path.with_name(MTIMES + '.tmp')
    temporary.write_text(json.dumps({'build': marker, 'files': files},
                                    indent=0, sort_keys=True))
    temporary.replace(path)


def read_mtimes(tree):
    """The mtime record, checked like dev_names.py checks its backups: every
    entry must be a plain relative path inside the tree with the right
    fields. A malformed record is dropped with a warning."""
    path = tree / '.pc' / MTIMES
    if not path.exists():
        return None
    root = tree.resolve()
    try:
        record = json.loads(path.read_text())
        files, build = record['files'], record['build']
        if not isinstance(files, dict) or not isinstance(build, dict):
            raise ValueError('expected {"files": {...}, "build": {...}}')
        for name, entry in files.items():
            if (not isinstance(name, str)
                    or not (root / name).resolve().is_relative_to(root)):
                raise ValueError(f'unexpected path: {name}')
            if (not isinstance(entry, dict) or set(entry) != {'mtime_ns', 'sha256'}
                    or not isinstance(entry['mtime_ns'], int)
                    or not 0 <= entry['mtime_ns'] < 1 << 63
                    or not isinstance(entry['sha256'], str)):
                raise ValueError(f'unexpected entry for {name}')
        if not all(isinstance(name, str) and isinstance(mtime, int)
                   for name, mtime in build.items()):
            raise ValueError('unexpected build marker')
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f'rac worktree: ignoring malformed {MTIMES}: {error}', file=sys.stderr)
        path.unlink(missing_ok=True)
        return None
    return record


def restore(tree):
    """Gives the recorded mtime back to each file a pop and push left with
    the same bytes, so mtime-based builds see no change. Runs after the push
    while the name passes are still reverted, matching the state snapshot()
    saw. The record is used once, then deleted. If the loop is interrupted
    (Ctrl-C, a failed utime), the record stays so a retry can finish: files
    already given back their mtime still match their digest."""
    path = tree / '.pc' / MTIMES
    record = read_mtimes(tree)
    if record is None:
        return
    if record['build'] != build_marker(tree):
        path.unlink()
        print('rac worktree: the tree was built since the snapshot; '
              'keeping the new mtimes', file=sys.stderr)
        return
    kept = changed = 0
    for name, entry in record['files'].items():
        target = tree / name
        if (not target.is_file() or target.is_symlink()
                or file_digest(target) != entry['sha256']):
            changed += 1
            continue
        os.utime(target, ns=(target.stat().st_atime_ns, entry['mtime_ns']))
        kept += 1
    path.unlink()
    print(f'rac worktree: kept mtimes on {kept} unchanged files ({changed} changed)',
          file=sys.stderr)


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
    elif command == 'snapshot':
        snapshot(tree, int(sys.argv[4]))
    elif command == 'restore':
        restore(tree)
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main()
