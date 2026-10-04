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
import os
import subprocess
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = '.rac_names'
# Applied in this order and reverted in reverse.
PASSES = [
    ('helium', ROOT / 'helium-chromium' / 'utils' / 'name_substitution.py'),
    ('rac', ROOT / 'devutils' / 'rac' / 'name_pass.py'),
]


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
        summary = result.stdout.strip().splitlines()[-1:] or ['done']
        print(f'dev_names: {name} pass: {summary[0]}')


def unsub(tree):
    """Restores the files each pass changed, newest pass first."""
    for name, _ in reversed(PASSES):
        backup = backup_path(tree, name)
        if not backup.exists():
            continue
        with tarfile.open(backup, 'r:gz') as tar:
            members = tar.getmembers()
            tar.extractall(path=tree, filter='data')
        # The backups store no timestamps, so restored files would look
        # older than the build outputs made from the substituted versions.
        for member in members:
            os.utime(tree / member.name)
        backup.unlink()
        print(f'dev_names: reverted the {name} pass ({len(members)} files)')


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

    if args.command == 'sub':
        sub(tree)
    elif args.command == 'unsub':
        unsub(tree)
    else:
        print(status(tree))


if __name__ == '__main__':
    main()
