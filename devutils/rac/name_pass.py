#!/usr/bin/env python3

# Copyright 2025 The rac Authors
# You can use, redistribute, and/or modify this source code under
# the terms of the GPL-3.0 license that can be found in the LICENSE file.
"""Replaces Helium with rac in user-visible strings.

Runs after Helium's name_substitution.py and i18n_apply.py, which have
already turned Chrome/Chromium into Helium. Mentions of Helium's own
services stay as they are, since those servers are run by Helium.
"""

from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import argparse
import os
import re
import sys
import xml.etree.ElementTree as xml

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'helium-chromium' / 'utils'))

# pylint: disable=import-error,wrong-import-position
import name_substitution as helium_namesub
import name_substitution_utils as util

# Phrases about something Helium runs or does, not the browser itself.
_KEEP_AFTER = (r'(?! (?i:services|servers|partner)\b)'
               r'(?<!development of Helium)(?<!verified by Helium)')
PROTECTED_REGEX = re.compile(r'\bHelium (?i:services|servers|partner)\b'
                             r'|(?:development of|verified by) Helium\b')
REPLACEMENT_REGEXES = [
    (re.compile(r'\bhelium://'), 'rac://'),
    (re.compile(r'\bHelium\b' + _KEEP_AFTER), 'rac'),
]

DOLLAR_LITERAL = '&#36;'
DOLLAR_PLACEHOLDER = '!!dollar-sign-literal!!'


def replace_text(text):
    """Returns text with Helium replaced by rac, keeping protected phrases."""
    for regex, replacement in REPLACEMENT_REGEXES:
        text = regex.sub(replacement, text)
    return text


def replace_element(elem, include_tail=False):
    """Replaces text in an element and its children. Returns True if changed."""
    changed = False
    if elem.text:
        new = replace_text(elem.text)
        changed |= new != elem.text
        elem.text = new
    for child in elem:
        changed |= replace_element(child, include_tail=True)
    if include_tail and elem.tail:
        new = replace_text(elem.tail)
        changed |= new != elem.tail
        elem.tail = new
    return changed


def element_text(elem):
    """All text inside an element, for detecting protected phrases."""
    return ''.join(elem.itertext())


def replacement_sanity():
    """Checks that the replacement regexes behave as intended."""
    before_after = [
        ('Helium', 'rac'),
        ("Helium's memory", "rac's memory"),
        ('Meet Helium', 'Meet rac'),
        ('helium://settings', 'rac://settings'),
        ('Helium services', 'Helium services'),
        ('Allow connecting to Helium Services', 'Allow connecting to Helium Services'),
        ('blocking downloads from Helium servers', 'blocking downloads from Helium servers'),
        ('Helium Partner', 'Helium Partner'),
        ('support the development of Helium.', 'support the development of Helium.'),
        ("Its privacy wasn't verified by Helium.", "Its privacy wasn't verified by Helium."),
        ('Helium will use Helium services', 'rac will use Helium services'),
        ('HeliumNoise', 'HeliumNoise'),
    ]
    for source, expected in before_after:
        actual = replace_text(source)
        assert actual == expected, f'sanity: {source!r} -> {actual!r}, expected {expected!r}'


def read_xml(path):
    """Reads a GRIT file, protecting literal dollar signs from the XML parser."""
    with open(path, 'r', encoding='utf-8') as file:
        original = file.read()
    return original, original.replace(DOLLAR_LITERAL, DOLLAR_PLACEHOLDER)


def write_xml(path, tree):
    """Writes a GRIT file, restoring literal dollar signs."""
    text = xml.tostring(tree, encoding='unicode', xml_declaration=True)
    with open(path, 'w', encoding='utf-8') as file:
        file.write(text.replace(DOLLAR_PLACEHOLDER, DOLLAR_LITERAL))


def substitute_grit_file(args):
    """
    Replaces strings in a .grd or .grdp file.

    Returns (arcname, original_text, fp_map), where fp_map maps each changed
    message's old fingerprint to (new fingerprint, protected). Returns None if
    nothing changed.
    """
    path, tree, dry_run = args
    original, text = read_xml(path)
    if 'Helium' not in text and 'helium://' not in text:
        return None

    root = xml.fromstring(text, util.get_parser())
    fp_map = {}
    for message in root.findall('.//message'):
        old_fp = util.compute_fp(message)
        protected = bool(PROTECTED_REGEX.search(element_text(message)))
        if replace_element(message):
            new_fp = util.compute_fp(message)
            if new_fp != old_fp:
                fp_map[old_fp] = (new_fp, protected)

    if not fp_map:
        return None

    arcname = str(path.relative_to(tree))
    print(f'Replaced strings in {arcname}')
    if not dry_run:
        write_xml(path, root)
    return arcname, original, fp_map


def substitute_xtb_file(args):
    """
    Moves translations to the new fingerprints of changed messages.

    A translation of a message that also names Helium's services keeps its
    text, since it can't be edited reliably in every language.
    """
    path, tree, fp_map, dry_run = args
    original, text = read_xml(path)
    if not any(f'id="{fp}"' in text for fp in fp_map):
        return None

    root = xml.fromstring(text, util.get_parser())
    changed = False
    seen = set()
    for translation in root.findall('.//translation'):
        entry = fp_map.get(translation.get('id'))
        if entry:
            new_fp, protected = entry
            if not protected:
                replace_element(translation)
            translation.set('id', new_fp)
            changed = True
        util.dedup_translations_in_place(translation, seen)

    if not changed:
        return None

    arcname = str(path.relative_to(tree))
    if not dry_run:
        write_xml(path, root)
    return arcname, original


def do_substitution(tree, tarpath, workers, dry_run):
    """Performs name substitutions on all candidate files."""
    util.add_grit_to_path(tree)

    grit_files = list(helium_namesub.get_substitutable_files(tree, ['grd', 'grdp']))
    with ProcessPoolExecutor(max_workers=workers) as executor:
        results = [
            r for r in executor.map(substitute_grit_file, [(f, tree, dry_run) for f in grit_files])
            if r
        ]

    fp_map = {}
    for _, _, file_fp_map in results:
        fp_map.update(file_fp_map)
    modified = [(arcname, original) for arcname, original, _ in results]

    xtb_files = list(helium_namesub.get_substitutable_files(tree, ['xtb']))
    with ProcessPoolExecutor(max_workers=workers) as executor:
        modified += [
            r for r in executor.map(
                substitute_xtb_file, [(f, tree, fp_map, dry_run) for f in xtb_files], chunksize=32)
            if r
        ]

    protected = sum(1 for _, is_protected in fp_map.values() if is_protected)
    print(f'Changed {len(fp_map)} messages ({protected} also name Helium services)')
    print(f'Modified {len(modified)} files')
    helium_namesub.maybe_make_tarball(tarpath, modified)


def parse_args():
    """CLI argument parsing logic"""
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--sub', action='store_true')
    group.add_argument('--unsub', action='store_true')
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument('--backup-path', metavar='<tarball-path>', type=Path)
    group.add_argument('--dry-run', action='store_true')
    parser.add_argument('-t', metavar='source_tree', type=Path, required=True)
    parser.add_argument('--workers', type=int, default=os.cpu_count())

    args = parser.parse_args()
    if args.unsub and not args.backup_path:
        parser.error('--unsub needs --backup-path')
    return args


def main():
    """CLI entrypoint"""
    replacement_sanity()
    args = parse_args()

    if not (args.t / 'OWNERS').exists():
        raise ValueError('wrong src directory')

    if args.sub:
        if args.backup_path is not None and args.backup_path.exists():
            raise FileExistsError('unsub tarball already exists, aborting')
        do_substitution(args.t, args.backup_path, args.workers, args.dry_run)
    elif args.unsub and not args.dry_run:
        helium_namesub.do_unsubstitution(args.t, args.backup_path)


if __name__ == '__main__':
    main()
