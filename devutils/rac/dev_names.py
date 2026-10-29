#!/usr/bin/env python3

# Copyright 2025 The rac Authors
# You can use, redistribute, and/or modify this source code under
# the terms of the GPL-3.0 license that can be found in the LICENSE file.
"""Applies or reverts rac's names in a dev build tree.

Release builds run Helium's name substitution and then rac's name pass on a
fresh tree. A dev tree keeps its quilt patches applied, so here each pass
saves the files it changes in build/src/.rac_names, and unsub restores them
before quilt touches any string file.

sub also records a hash of each file the passes changed, so unsub can refuse
to overwrite a string file that was edited while the names were applied.

unsub saves each changed file's mtime and content hash; a later sub puts the
mtime back on files the passes rewrite byte-identical, so the build doesn't
reprocess ~2,700 unchanged string files after every sync.

usage: dev_names.py <sub|unsub [--force]|status> [-t <build/src>]
"""

from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = '.rac_names'
EXPECTED = 'expected.json'
MTIMES = 'mtimes.json'
# Applied in this order and reverted in reverse.
PASSES = [
    ('helium', ROOT / 'helium-chromium' / 'utils' / 'name_substitution.py'),
    ('rac', ROOT / 'devutils' / 'rac' / 'name_pass.py'),
]


def backup_path(tree, name):
    """Where a pass keeps the original contents of the files it changed."""
    return tree / STATE_DIR / f'{name}.tar'


def file_digest(path):
    """sha256 of a file, or None if it doesn't exist."""
    if not path.is_file():
        return None
    sha = hashlib.sha256()
    with open(path, 'rb') as file:
        for chunk in iter(lambda: file.read(1 << 20), b''):
            sha.update(chunk)
    return sha.hexdigest()


def archived_files(tree, backup):
    """The files in a pass's backup. Refuses anything that isn't a plain file
    inside the tree, before unsub writes anything."""
    with tarfile.open(backup, 'r:gz') as tar:
        members = tar.getmembers()
    for member in members:
        if not member.isfile() or not (tree / member.name).resolve().is_relative_to(tree):
            raise ValueError(f'{backup.name} has an unexpected entry: {member.name}')
    return [member.name for member in members]


def applied_backups(tree):
    """(name, backup) for each pass that has run, newest first."""
    return [(name, backup_path(tree, name)) for name, _ in reversed(PASSES)
            if backup_path(tree, name).exists()]


def record_expected(tree):
    """Saves a hash of each file the passes changed, as it is now."""
    files = set()
    for _, backup in applied_backups(tree):
        files.update(archived_files(tree, backup))
    path = tree / STATE_DIR / EXPECTED
    temporary = path.with_name(EXPECTED + '.tmp')
    temporary.write_text(json.dumps({name: file_digest(tree / name) for name in sorted(files)},
                                    indent=0, sort_keys=True))
    temporary.replace(path)


def check_unchanged(tree, files):
    """Raises if a file the passes changed was edited since."""
    path = tree / STATE_DIR / EXPECTED
    if not path.exists():
        print('dev_names: these names were applied by an older dev_names.py, so '
              "edits made to string files since then can't be detected",
              file=sys.stderr)
        return
    expected = json.loads(path.read_text())
    if set(expected) != files:
        raise ValueError(f'{path} doesn\'t match the backups; if no string file was '
                         'edited, rerun with unsub --force')
    edited = sorted(name for name, digest in expected.items()
                    if file_digest(tree / name) != digest)
    if edited:
        shown = ', '.join(edited[:5]) + (f' and {len(edited) - 5} more' if len(edited) > 5 else '')
        raise ValueError(f'{shown} changed since rac\'s names were applied, and unsub '
                         'would overwrite the change. Copy the change somewhere safe, run '
                         'devutils/rac/dev_names.py unsub --force, then make it again.')


def status(tree):
    """Returns 'applied', 'not applied', or 'partial'."""
    present = [backup_path(tree, name).exists() for name, _ in PASSES]
    if all(present):
        return 'applied'
    return 'partial' if any(present) else 'not applied'


def sub(tree):
    """Runs every pass that hasn't run yet."""
    (tree / STATE_DIR).mkdir(exist_ok=True)
    for name, script in PASSES:
        backup = backup_path(tree, name)
        if backup.exists():
            continue
        result = subprocess.run(
            [sys.executable, script, '--sub', '-t', tree, '--backup-path', backup],
            capture_output=True,
            text=True,
            check=False)
        if result.returncode != 0:
            sys.stderr.write(result.stdout + result.stderr)
            sys.exit(f'dev_names: the {name} name pass failed')
        record_expected(tree)
        summary = result.stdout.strip().splitlines()[-1:] or ['done']
        print(f'dev_names: {name} pass: {summary[0]}')
    restore_mtimes(tree)


def build_marker(tree):
    """When each build output folder last saved its state. A build between
    unsub and sub records different content under the mtimes unsub saved, so
    putting them back could hide a real change from the next build."""
    return {str(state.relative_to(tree)): state.stat().st_mtime_ns
            for pattern in ('out/*/.siso_fs_state', 'out/*/.ninja_log')
            for state in sorted(tree.glob(pattern))}


def restore_mtimes(tree):
    """Puts back the mtimes unsub saved for files the passes wrote back
    byte-identical, so the build doesn't reprocess them. Files whose content
    differs, because a patch really changed them, keep their new mtime."""
    path = tree / STATE_DIR / MTIMES
    if not path.exists():
        return
    try:
        record = json.loads(path.read_text())
        saved, marker = record['files'], record['build']
    except (ValueError, KeyError, TypeError):
        saved, marker = None, None
    usable = isinstance(saved, dict) and isinstance(marker, dict) and all(
        isinstance(name, str)
        and (tree / name).resolve().is_relative_to(tree.resolve())
        and isinstance(entry, dict)
        and isinstance(entry.get('mtime_ns'), int) and 0 <= entry['mtime_ns'] < 1 << 63
        and isinstance(entry.get('sha256'), str)
        for name, entry in saved.items())
    path.unlink()
    if not usable or marker != build_marker(tree):
        print('dev_names: not keeping mtimes: the saved ones are unusable or the '
              'tree was built since unsub', file=sys.stderr)
        return
    kept = 0
    for name, record in saved.items():
        file = tree / name
        if file_digest(file) != record['sha256']:
            continue
        stat_result = file.stat()
        os.utime(file, ns=(stat_result.st_atime_ns, record['mtime_ns']))
        kept += 1
    print(f'dev_names: kept mtimes on {kept} unchanged files '
          f'({len(saved) - kept} changed)')


def unsub(tree, force=False):
    """Restores the files each pass changed, newest pass first.

    Each file it replaces moves to a recovery folder beside the tree, where
    the name passes don't look. If restoring fails, they move back. If that
    fails too, the folder stays and the error names it.
    """
    backups = applied_backups(tree)
    expected = tree / STATE_DIR / EXPECTED
    if not backups:
        expected.unlink(missing_ok=True)
        # A pending mtime record stays: a sync that failed after the last
        # unsub retries unsub before its sub, and the record is what lets
        # that sub keep the files' mtimes.
        return
    counts = {name: archived_files(tree, backup) for name, backup in backups}
    files = {file for files in counts.values() for file in files}
    if not force:
        check_unchanged(tree, files)

    # Taken while the names are still applied, but written only once the
    # restore below has succeeded. A later sub puts these mtimes back on
    # files it rewrites byte-identical.
    marker = build_marker(tree)
    snapshot = {}
    for name in sorted(files):
        path = tree / name
        if path.is_file():
            snapshot[name] = {'mtime_ns': path.stat().st_mtime_ns,
                              'sha256': file_digest(path)}

    recovery = Path(tempfile.mkdtemp(prefix='.rac_names_unsub-', dir=tree.parent))
    moved = {}  # path -> its copy in recovery, or None if it didn't exist

    def move_aside(path, copy):
        copy.parent.mkdir(parents=True, exist_ok=True)
        # Noted first, so an interrupt right after the rename can't lose it.
        moved[path] = copy
        os.rename(path, copy)

    try:
        for _, backup in backups:
            with tarfile.open(backup, 'r:gz') as tar:
                for member in tar:
                    path = tree / member.name
                    if path not in moved:
                        if path.exists():
                            move_aside(path, recovery / 'files' / member.name)
                        else:
                            moved[path] = None
                    path.parent.mkdir(parents=True, exist_ok=True)
                    with tar.extractfile(member) as data, open(path, 'wb') as file:
                        shutil.copyfileobj(data, file)
                    if moved[path]:
                        os.chmod(path, stat.S_IMODE(moved[path].stat().st_mode))
        # The backups go last, so a failure above leaves the names applied.
        for path in [backup for _, backup in backups] + [expected]:
            if path.exists():
                move_aside(path, recovery / STATE_DIR / path.name)
        # The mtime record goes after the restore, so an interrupt or a
        # rollback above never leaves one for a sub that shouldn't see it.
        record = tree / STATE_DIR / MTIMES
        temporary = record.with_name(MTIMES + '.tmp')
        temporary.write_text(json.dumps({'files': snapshot, 'build': marker},
                                        indent=0, sort_keys=True))
        temporary.replace(record)
    except BaseException as error:  # including Ctrl-C, which would leave half the files
        failed = []
        for path, copy in reversed(moved.items()):
            try:
                if copy and not copy.exists() and path.exists():
                    continue  # interrupted before the rename; path is untouched
                if copy:
                    os.replace(copy, path)
                else:
                    path.unlink(missing_ok=True)
            except OSError as rollback_error:
                failed.append(f'{path}: {rollback_error}')
        if failed:
            raise OSError(f'{error}; putting the files back also failed ({"; ".join(failed)}). '
                          f'The files from before unsub are in {recovery}') from error
        shutil.rmtree(recovery, ignore_errors=True)
        if isinstance(error, OSError):
            raise OSError(f'{error}; nothing was changed') from error
        raise

    shutil.rmtree(recovery, ignore_errors=True)
    for name, files in counts.items():
        print(f'dev_names: reverted the {name} pass ({len(files)} files)')


def main():
    """CLI entrypoint"""
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('command', choices=['sub', 'unsub', 'status'])
    parser.add_argument('-t', metavar='source_tree', type=Path, default=ROOT / 'build' / 'src')
    parser.add_argument('--force',
                        action='store_true',
                        help='unsub: overwrite string files even if they were edited')
    args = parser.parse_args()

    tree = args.t.resolve()
    if not (tree / 'OWNERS').exists():
        sys.exit(f'dev_names: {tree} is not a Chromium source tree')

    try:
        if args.command == 'sub':
            sub(tree)
        elif args.command == 'unsub':
            unsub(tree, args.force)
        else:
            print(status(tree))
    except (OSError, ValueError, tarfile.TarError) as error:
        sys.exit(f'dev_names: {error}')


if __name__ == '__main__':
    main()
