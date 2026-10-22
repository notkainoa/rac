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
        return
    counts = {name: archived_files(tree, backup) for name, backup in backups}
    if not force:
        check_unchanged(tree, {file for files in counts.values() for file in files})

    recovery = Path(tempfile.mkdtemp(prefix='.rac_names_unsub-', dir=tree.parent))
    moved = {}  # path -> its copy in recovery, or None if it didn't exist

    def move_aside(path, copy):
        copy.parent.mkdir(parents=True, exist_ok=True)
        os.rename(path, copy)
        moved[path] = copy

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
    except BaseException as error:  # including Ctrl-C, which would leave half the files
        failed = []
        for path, copy in reversed(moved.items()):
            try:
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
