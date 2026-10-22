#!/usr/bin/env python3

# Copyright 2025 The rac Authors
# You can use, redistribute, and/or modify this source code under
# the terms of the GPL-3.0 license that can be found in the LICENSE file.
"""Tests for name_pass.py and for running both name passes with dev_names.py.

The GRIT tests need a prepared Chromium tree for tools/grit: this checkout's
build/src, or the main checkout's. They only read it; fixtures get a copy.

Run from the repository root:
    python3 -m unittest discover -s devutils/rac -p 'test_*.py' -v
"""

from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import xml.etree.ElementTree as xml

# Never write bytecode into the tree GRIT is read from.
sys.dont_write_bytecode = True
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import dev_names  # pylint: disable=wrong-import-position
import name_pass  # pylint: disable=wrong-import-position

ROOT = Path(__file__).resolve().parents[2]


def find_grit_tree():
    """A Chromium tree with tools/grit, or None."""
    candidates = [ROOT / 'build' / 'src']
    listing = subprocess.run(['git', '-C', str(ROOT), 'worktree', 'list', '--porcelain'],
                             capture_output=True,
                             text=True,
                             check=False).stdout
    if listing.startswith('worktree '):
        candidates.append(Path(listing.split('\n', 1)[0][len('worktree '):]) / 'build' / 'src')
    for tree in candidates:
        if (tree / 'tools' / 'grit' / 'grit' / 'extern' / 'tclib.py').exists():
            return tree
    return None


GRIT_TREE = find_grit_tree()
needs_grit = unittest.skipUnless(GRIT_TREE, 'needs build/src/tools/grit')


class ReplaceTextTest(unittest.TestCase):

    def test_sanity_table(self):
        name_pass.replacement_sanity()

    def test_service_names_stay_helium(self):
        for service in ('service', 'services', 'server', 'servers', 'partner', 'Service',
                        'Services', 'Server', 'Servers', 'Partner', 'sErViCe', 'pArTnEr'):
            with self.subTest(service=service):
                phrase = f'Helium {service}'
                self.assertEqual(name_pass.replace_text(phrase), phrase)
                self.assertIsNotNone(name_pass.PROTECTED_REGEX.search(phrase))

    def test_longer_words_are_not_service_names(self):
        for suffix in ('serverless', 'serviceability', 'servicesX', 'partners'):
            with self.subTest(suffix=suffix):
                self.assertEqual(name_pass.replace_text(f'Helium {suffix}'), f'rac {suffix}')
                self.assertIsNone(name_pass.PROTECTED_REGEX.search(f'Helium {suffix}'))

    def test_existing_rules(self):
        cases = (
            ("Helium's memory", "rac's memory"),
            ('helium://settings', 'rac://settings'),
            ('HeliumNoise', 'HeliumNoise'),
            ('development of Helium', 'development of Helium'),
            ('verified by Helium', 'verified by Helium'),
        )
        for source, expected in cases:
            with self.subTest(source=source):
                self.assertEqual(name_pass.replace_text(source), expected)


@needs_grit
class GritFingerprintTest(unittest.TestCase):
    """Translations must follow their messages to the ids GRIT computes."""

    @classmethod
    def setUpClass(cls):
        name_pass.util.add_grit_to_path(GRIT_TREE)
        # pylint: disable=import-outside-toplevel,import-error
        from grit import constants, grd_reader
        from grit.node import message

        cls.grd_reader = grd_reader
        cls.message_node = message.MessageNode
        cls.gender = constants.DEFAULT_GENDER

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.tree = Path(temporary.name)
        self.grd = self.tree / 'messages.grd'
        self.xtb = self.tree / 'messages_fr.xtb'

    def write_message(self, content, meaning=''):
        self.grd.write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<grit latest_public_release="0" current_release="1" '
            'source_lang_id="en" base_dir=".">'
            '<translations><file path="messages_fr.xtb" lang="fr" /></translations>'
            '<release seq="1"><messages>'
            f'<message name="IDS_TEST" meaning="{meaning}">{content}</message>'
            '</messages></release></grit>',
            encoding='utf-8')

    def parse_message(self):
        root = self.grd_reader.Parse(str(self.grd))
        message, = root.GetChildrenOfType(self.message_node)
        return root, message

    def check_translation(self, content, translation, expected, meaning='', protected=False):
        self.write_message(content, meaning)
        _, before = self.parse_message()
        old_fp = before.GetCliques()[0].GetMessage().GetId()
        self.xtb.write_text(
            '<translationbundle lang="fr">'
            f'<translation id="{old_fp}">{translation}</translation>'
            '</translationbundle>',
            encoding='utf-8')

        result = name_pass.substitute_grit_file((self.grd, self.tree, False))
        self.assertIsNotNone(result)
        _, _, fp_map = result
        root, after = self.parse_message()
        new_fp = after.GetCliques()[0].GetMessage().GetId()
        self.assertNotEqual(old_fp, new_fp)
        self.assertEqual(fp_map, {old_fp: (new_fp, protected)})
        self.assertIsNotNone(name_pass.substitute_xtb_file((self.xtb, self.tree, fp_map, False)))
        self.assertEqual(xml.parse(self.xtb).find('translation').get('id'), new_fp)

        root.SetOutputLanguage('fr')
        root.RunGatherers()
        self.assertEqual(after.Translate('fr', self.gender), expected)
        return old_fp, new_fp

    def test_literal_dollar_uses_grit_ids(self):
        old_fp, new_fp = self.check_translation('Helium accepts &#36; payments',
                                                'Helium accepte les paiements en &#36;',
                                                'rac accepte les paiements en $')
        # The same ids as the plain "$" message: GRIT hashes the decoded text.
        self.assertEqual(old_fp, '3092480736714754993')
        self.assertEqual(new_fp, '688624895589579962')
        self.assertIn('rac accepts &#36; payments', self.grd.read_text(encoding='utf-8'))
        self.assertIn('rac accepte les paiements en &#36;', self.xtb.read_text(encoding='utf-8'))

    def test_plain_dollar(self):
        old_fp, new_fp = self.check_translation('Helium accepts $ payments',
                                                'Helium accepte les paiements en $',
                                                'rac accepte les paiements en $')
        self.assertEqual(old_fp, '3092480736714754993')
        self.assertEqual(new_fp, '688624895589579962')

    def test_numeric_literal_dollar_stays_an_entity(self):
        self.check_translation('Helium costs &#36;50', 'Helium coûte &#36;50', 'rac coûte $50')
        # GRIT rejects a raw "$50" as an unwrapped formatter.
        self.assertIn('rac costs &#36;50', self.grd.read_text(encoding='utf-8'))

    def test_dollars_in_text_and_placeholder_tails(self):
        self.check_translation(
            'Helium pays &#36; <ph name="user_name">$1<ex>Ada</ex></ph> '
            'and &#36;50 with <ph name="count">&#36;2<ex>2</ex></ph> items',
            'Helium verse &#36; à <ph name="USER_NAME"/> et &#36;50 pour '
            '<ph name="COUNT"/> objets', 'rac verse $ à $1 et $50 pour $2 objets')
        serialized = self.grd.read_text(encoding='utf-8')
        self.assertIn('</ph> and &#36;50 with', serialized)
        self.assertIn('<ph name="count">&#36;2<ex>2</ex></ph>', serialized)

    def test_dollars_only_in_placeholder_values(self):
        self.check_translation('Helium greets <ph name="user_name">&#36;1<ex>&#36;50</ex></ph>',
                               'Helium accueille <ph name="USER_NAME"/>', 'rac accueille $1')

    def test_dollar_in_meaning(self):
        self.check_translation('Helium accepts payments',
                               'Helium accepte les paiements',
                               'rac accepte les paiements',
                               meaning='payments in &#36;')
        self.assertIn('meaning="payments in &#36;"', self.grd.read_text(encoding='utf-8'))

    def test_service_translations_keep_their_text(self):
        for service in ('service', 'Server', 'partner'):
            with self.subTest(service=service):
                self.check_translation(f'Helium connects to Helium {service}',
                                       'Helium se connecte au service Helium',
                                       'Helium se connecte au service Helium',
                                       protected=True)
                self.assertIn(f'rac connects to Helium {service}',
                              self.grd.read_text(encoding='utf-8'))


@needs_grit
class DevNamesRealPassesTest(unittest.TestCase):
    """Both real passes on a fixture tree, through dev_names.py."""

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='rac-test-names-')
        self.addCleanup(temporary.cleanup)
        self.folder = Path(temporary.name).resolve()
        self.tree = self.folder / 'src'
        (self.tree / 'tools').mkdir(parents=True)
        shutil.copytree(GRIT_TREE / 'tools' / 'grit',
                        self.tree / 'tools' / 'grit',
                        ignore=shutil.ignore_patterns('__pycache__', 'testdata', '*_unittest.py'))
        (self.tree / 'OWNERS').write_text('fixture\n')
        # The passes run in subprocesses and use the copy; this process reads
        # GRIT from the source tree.
        name_pass.util.add_grit_to_path(GRIT_TREE)
        self.grd = self.tree / 'messages.grd'
        self.xtb = self.tree / 'messages_fr.xtb'
        fingerprint = name_pass.compute_fp(
            xml.fromstring('<message name="IDS_TEST">Chromium browser</message>'))
        self.grd.write_text(
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<grit latest_public_release="0" current_release="1" '
            'source_lang_id="en" base_dir=".">'
            '<translations><file path="messages_fr.xtb" lang="fr" /></translations>'
            '<release seq="1"><messages>'
            '<message name="IDS_TEST">Chromium browser</message>'
            '</messages></release></grit>',
            encoding='utf-8')
        self.xtb.write_text(
            '<translationbundle lang="fr">'
            f'<translation id="{fingerprint}">Chromium navigateur</translation>'
            '</translationbundle>',
            encoding='utf-8')
        self.originals = {path: path.read_bytes() for path in (self.grd, self.xtb)}

    def sub(self):
        run = subprocess.run

        def one_worker(command, **kwargs):
            return run([*command, '--workers', '1'], **kwargs)

        with mock.patch.object(dev_names.subprocess, 'run', side_effect=one_worker):
            dev_names.sub(self.tree)

    def test_sub_then_unsub_round_trip(self):
        self.sub()
        self.assertIn('rac browser', self.grd.read_text())
        self.assertIn('rac navigateur', self.xtb.read_text())
        self.assertEqual(dev_names.status(self.tree), 'applied')
        dev_names.unsub(self.tree)
        for path, data in self.originals.items():
            self.assertEqual(path.read_bytes(), data)
        self.assertEqual(dev_names.status(self.tree), 'not applied')

    def test_recovery_folder_is_outside_the_scanned_tree(self):
        self.sub()
        branded = {path.name: path.read_bytes() for path in (self.grd, self.xtb)}
        # Keep the recovery folder, as a failed rollback would.
        with mock.patch.object(dev_names.shutil, 'rmtree'):
            dev_names.unsub(self.tree)
        recovery, = self.folder.glob('.rac_names_unsub-*')
        self.assertEqual(recovery.parent, self.tree.parent)
        kept = {path: path.read_bytes() for path in recovery.rglob('*') if path.is_file()}
        self.assertEqual(kept[recovery / 'files' / 'messages.grd'], branded['messages.grd'])

        # A later sub must neither rebrand the kept copies nor back them up.
        self.sub()
        self.assertEqual({path: path.read_bytes() for path in kept}, kept)
        for name, _ in dev_names.PASSES:
            self.assertEqual(
                set(dev_names.archived_files(self.tree, dev_names.backup_path(self.tree, name))),
                {'messages.grd', 'messages_fr.xtb'})
        dev_names.unsub(self.tree)
        for path, data in self.originals.items():
            self.assertEqual(path.read_bytes(), data)


if __name__ == '__main__':
    unittest.main()
