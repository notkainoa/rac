#!/usr/bin/env python3

# Copyright 2025 The rac Authors
# You can use, redistribute, and/or modify this source code under
# the terms of the GPL-3.0 license that can be found in the LICENSE file.
"""Applies or reverts rac's names in a dev build tree.

Release builds run Helium's name substitution and then rac's name pass on a
fresh tree. A dev tree keeps its quilt patches applied, so here each pass
saves the files it changes in build/src/.rac_names, and unsub restores them
before quilt touches any string file.

usage: dev_names.py <sub|unsub|status> [-t <build/src>]
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
# Applied in this order and reverted in reverse.
PASSES = [
    ('helium', ROOT / 'helium-chromium' / 'utils' / 'name_substitution.py'),
    ('rac', ROOT / 'devutils' / 'rac' / 'name_pass.py'),
]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def archive_contents(backup):
    """Reads only regular, tree-relative files from a names archive."""
    contents = {}
    with tarfile.open(backup, 'r:gz') as tar:
        for member in tar.getmembers():
            path = Path(member.name)
            if (not member.isfile() or path.is_absolute() or '..' in path.parts
                    or member.name in contents):
                raise ValueError(f'unsafe names archive member: {member.name}')
            contents[member.name] = tar.extractfile(member).read()
    return contents


def source_bytes(tree, name, missing=False):
    """Reads bytes; with missing=True, None means absent, not an empty file."""
    tree = tree.resolve()
    path = tree / name
    current = path
    while current != tree:
        if current.is_symlink():
            raise ValueError(f'cannot restore names through a symlink: {name}')
        current = current.parent
    if missing and not path.exists():
        return None
    return path.read_bytes()


def originals(tree):
    """Checks branding without writing; returns the pre-branding contents.

    Old archives have no trustworthy post-substitution baseline. Refuse them
    rather than turning the current (possibly edited) files into a baseline.
    """
    backups = {name: backup_path(tree, name) for name, _ in PASSES
               if backup_path(tree, name).exists()}
    expected_path = tree / STATE_DIR / 'expected.json'
    if not backups:
        if expected_path.exists():
            raise ValueError('names baseline exists without its archives')
        return {}
    if not expected_path.exists():
        raise ValueError('legacy names archives have no verified baseline; '
                         'preserve string edits and archives before restoring '
                         'the original names manually')
    expected = json.loads(expected_path.read_text())
    archives = {name: digest(path.read_bytes()) for name, path in backups.items()}
    contents = {}
    for name, _ in reversed(PASSES):
        if name in backups:
            contents.update(archive_contents(backups[name]))
    if (not isinstance(expected, dict) or not isinstance(expected.get('files'), dict)
            or expected.get('version') != 1 or expected.get('archives') != archives
            or set(expected.get('files', {})) != set(contents)):
        raise ValueError('names archives do not match their verified baseline')
    for name, fingerprint in expected['files'].items():
        data = source_bytes(tree, name, missing=True)
        if data is None or digest(data) != fingerprint:
            raise ValueError(f'edited branded string file: {name}; preserve your '
                             'edit before reverting names')
    return contents


def record_expected(tree):
    """Records the completed passes, never retroactively adopting old ones."""
    backups = {name: backup_path(tree, name) for name, _ in PASSES
               if backup_path(tree, name).exists()}
    files = set()
    for backup in backups.values():
        files.update(archive_contents(backup))
    expected = {
        'version': 1,
        'archives': {name: digest(path.read_bytes()) for name, path in backups.items()},
        'files': {name: digest(source_bytes(tree, name)) for name in sorted(files)},
    }
    path = tree / STATE_DIR / 'expected.json'
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(expected, sort_keys=True) + '\n')
    temporary.replace(path)


def backup_path(tree, name):
    """Where a pass keeps the original contents of the files it changed."""
    return tree / STATE_DIR / f'{name}.tar'


def status(tree):
    """Returns 'applied', 'not applied', or 'partial'."""
    present = [backup_path(tree, name).exists() for name, _ in PASSES]
    if all(present):
        return 'applied'
    return 'partial' if any(present) else 'not applied'


def sub(tree):
    """Runs every pass that hasn't run yet."""
    originals(tree)
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


def unsub(tree):
    """Restores names, rolling back caught filesystem failures.

    Recovery copies protect both branded files and the verified archives
    until restoration and ledger cleanup finish. This is not crash-atomic.
    """
    contents = originals(tree)
    # Validate every pass before touching any file or deleting any archive.
    backups = {}
    for name, _ in reversed(PASSES):
        backup = backup_path(tree, name)
        if backup.exists():
            backups[name] = (backup, len(archive_contents(backup)))
    if not backups:
        return

    expected = tree / STATE_DIR / 'expected.json'
    recovery = Path(tempfile.mkdtemp(prefix='unsub-', dir=tree / STATE_DIR))
    saved = {}
    touched = []
    try:
        # Copy everything before the first source write. Keep metadata separate
        # because reading a recovery copy can itself change its access time.
        paths = [tree / name for name in contents]
        paths.extend(backup for backup, _ in backups.values())
        paths.append(expected)
        metadata = {}
        for path in paths:
            relative = path.relative_to(tree)
            copy = recovery / 'files' / relative
            copy.parent.mkdir(parents=True, exist_ok=True)
            info = path.stat()
            shutil.copy2(path, copy)
            saved[path] = (copy, info)
            metadata[relative.as_posix()] = {
                'mode': stat.S_IMODE(info.st_mode),
                'atime_ns': info.st_atime_ns,
                'mtime_ns': info.st_mtime_ns,
            }
        (recovery / 'metadata.json').write_text(json.dumps(metadata, sort_keys=True) + '\n')

        for name, data in contents.items():
            path = tree / name
            # A failed write can already have truncated this target.
            touched.append(path)
            path.write_bytes(data)
            os.utime(path)
        for backup, _ in backups.values():
            touched.append(backup)
            backup.unlink()
        touched.append(expected)
        expected.unlink()
    except OSError as error:
        failures = []
        for path in reversed(touched):
            copy, info = saved[path]
            try:
                data = copy.read_bytes()
                if source_bytes(tree, path.relative_to(tree), missing=True) != data:
                    path.write_bytes(data)
                if stat.S_IMODE(path.stat().st_mode) != stat.S_IMODE(info.st_mode):
                    path.chmod(stat.S_IMODE(info.st_mode))
                os.utime(path, ns=(info.st_atime_ns, info.st_mtime_ns))
            except (OSError, ValueError) as rollback_error:
                failures.append(f'{path.relative_to(tree)}: {rollback_error}')
        if failures:
            raise OSError(f'{error}; names rollback failed ({"; ".join(failures)}); '
                          f'recovery files and metadata retained at {recovery}; '
                          'restore these copies before retrying') from error
        try:
            shutil.rmtree(recovery)
        except OSError as cleanup_error:
            raise OSError(f'{error}; pre-restore names state preserved, but recovery '
                          f'cleanup failed at {recovery}: {cleanup_error}') from error
        raise

    try:
        shutil.rmtree(recovery)
    except OSError as error:
        raise OSError(f'names reverted, but recovery cleanup failed at {recovery}: '
                      f'{error}') from error
    for name, (_, count) in backups.items():
        print(f'dev_names: reverted the {name} pass ({count} files)')


def main():
    """CLI entrypoint"""
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('command', choices=['sub', 'unsub', 'status'])
    parser.add_argument('-t', metavar='source_tree', type=Path, default=ROOT / 'build' / 'src')
    args = parser.parse_args()

    tree = args.t.resolve()
    if not (tree / 'OWNERS').exists():
        sys.exit(f'dev_names: {tree} is not a Chromium source tree')

    try:
        if args.command == 'sub':
            sub(tree)
        elif args.command == 'unsub':
            unsub(tree)
        else:
            print(status(tree))
    except (OSError, ValueError, tarfile.TarError) as error:
        sys.exit(f'dev_names: {error}')


if __name__ == '__main__':
    main()
