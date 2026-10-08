#!/usr/bin/env python3

# Copyright 2025 The rac Authors
# You can use, redistribute, and/or modify this source code under
# the terms of the GPL-3.0 license that can be found in the LICENSE file.
"""Branding regressions against GRIT from a prepared build/src tree.

Run from the repository root with:
    python3 -m unittest devutils.rac.test_name_pass -v

Only temporary fixtures are modified.
"""

from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import xml.etree.ElementTree as xml

from devutils.rac import dev_names, name_pass


class NamePassTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source_tree = Path(__file__).resolve().parents[2] / 'build' / 'src'
        name_pass.util.add_grit_to_path(source_tree)
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

    def check_translation(self, content, translation, expected, meaning='',
                          protected=False):
        self.write_message(content, meaning)
        _, before = self.parse_message()
        old_fp = before.GetCliques()[0].GetMessage().GetId()
        self.xtb.write_text(
            '<translationbundle lang="fr">'
            f'<translation id="{old_fp}">{translation}</translation>'
            '</translationbundle>', encoding='utf-8')

        result = name_pass.substitute_grit_file((self.grd, self.tree, False))
        self.assertIsNotNone(result)
        _, _, fp_map = result
        root, after = self.parse_message()
        new_fp = after.GetCliques()[0].GetMessage().GetId()
        self.assertNotEqual(old_fp, new_fp)
        self.assertEqual(fp_map, {old_fp: (new_fp, protected)})
        self.assertIsNotNone(
            name_pass.substitute_xtb_file((self.xtb, self.tree, fp_map, False)))
        translated = xml.parse(self.xtb).find('translation')
        self.assertEqual(translated.get('id'), new_fp)

        root.SetOutputLanguage('fr')
        root.RunGatherers()
        self.assertEqual(after.Translate('fr', self.gender), expected)
        return old_fp, new_fp

    def test_literal_dollar_translation_uses_grit_ids(self):
        old_fp, new_fp = self.check_translation(
            'Helium accepts &#36; payments',
            'Helium accepte les paiements en &#36;',
            'rac accepte les paiements en $')
        self.assertEqual(old_fp, '3092480736714754993')
        self.assertEqual(new_fp, '688624895589579962')
        self.assertIn('rac accepts &#36; payments',
                      self.grd.read_text(encoding='utf-8'))
        self.assertIn('rac accepte les paiements en &#36;',
                      self.xtb.read_text(encoding='utf-8'))

    def test_plain_dollar_translation(self):
        old_fp, new_fp = self.check_translation(
            'Helium accepts $ payments',
            'Helium accepte les paiements en $',
            'rac accepte les paiements en $')
        self.assertEqual(old_fp, '3092480736714754993')
        self.assertEqual(new_fp, '688624895589579962')
        self.assertIn('rac accepts $ payments',
                      self.grd.read_text(encoding='utf-8'))

    def test_numeric_literal_dollar_stays_an_entity(self):
        self.check_translation('Helium costs &#36;50',
                               'Helium coûte &#36;50', 'rac coûte $50')
        # A raw "$50" here is rejected by GRIT as an unwrapped formatter.
        self.assertIn('rac costs &#36;50', self.grd.read_text(encoding='utf-8'))
        self.assertIn('rac coûte &#36;50', self.xtb.read_text(encoding='utf-8'))

    def test_dollar_entities_in_text_and_placeholder_tails(self):
        self.check_translation(
            'Helium pays &#36; <ph name="user_name">$1<ex>Ada</ex></ph> '
            'and &#36;50 with <ph name="count">&#36;2<ex>2</ex></ph> items',
            'Helium verse &#36; à <ph name="USER_NAME"/> et &#36;50 pour '
            '<ph name="COUNT"/> objets',
            'rac verse $ à $1 et $50 pour $2 objets')
        serialized = self.grd.read_text(encoding='utf-8')
        self.assertIn('rac pays &#36;', serialized)
        self.assertIn('</ph> and &#36;50 with', serialized)
        self.assertIn('<ph name="user_name">$1<ex>Ada</ex></ph>', serialized)
        self.assertIn('<ph name="count">&#36;2<ex>2</ex></ph>', serialized)

    def test_dollar_entities_only_in_placeholder_values(self):
        self.check_translation(
            'Helium greets <ph name="user_name">&#36;1<ex>&#36;50</ex></ph>',
            'Helium accueille <ph name="USER_NAME"/>',
            'rac accueille $1')
        self.assertIn('<ph name="user_name">&#36;1<ex>&#36;50</ex></ph>',
                      self.grd.read_text(encoding='utf-8'))

    def test_dollar_entities_in_meaning(self):
        self.check_translation('Helium accepts payments',
                               'Helium accepte les paiements',
                               'rac accepte les paiements',
                               meaning='payments in &#36;')
        self.assertIn('meaning="payments in &#36;"',
                      self.grd.read_text(encoding='utf-8'))

    def test_service_names_and_mixed_translations_stay_helium(self):
        for service in ('service', 'services', 'server', 'servers', 'partner',
                        'Service', 'Services', 'Server', 'Servers', 'Partner',
                        'sErViCe', 'sErViCeS', 'sErVeR', 'sErVeRs', 'pArTnEr'):
            with self.subTest(service=service):
                phrase = f'Helium {service}'
                self.assertEqual(name_pass.replace_text(phrase), phrase)
                self.assertIsNotNone(name_pass.PROTECTED_REGEX.search(phrase))
                self.check_translation(
                    f'Helium connects to {phrase}',
                    'Helium se connecte au service Helium',
                    'Helium se connecte au service Helium', protected=True)
                self.assertIn(f'rac connects to {phrase}',
                              self.grd.read_text(encoding='utf-8'))
                self.assertIn('Helium se connecte au service Helium',
                              self.xtb.read_text(encoding='utf-8'))

    def test_service_boundaries_do_not_protect_generic_branding(self):
        for suffix in ('serverless', 'serviceability', 'servicesX', 'partners'):
            with self.subTest(suffix=suffix):
                self.assertIsNone(name_pass.PROTECTED_REGEX.search(f'Helium {suffix}'))
                self.check_translation(
                    f'Helium {suffix}', 'Helium propose cette fonctionnalité',
                    'rac propose cette fonctionnalité')
                self.assertIn(f'rac {suffix}', self.grd.read_text(encoding='utf-8'))

    def test_existing_branding_and_protection_rules(self):
        name_pass.replacement_sanity()
        cases = (
            ('Helium', 'rac'),
            ("Helium's memory", "rac's memory"),
            ('helium://settings', 'rac://settings'),
            ('HeliumNoise', 'HeliumNoise'),
            ('helium service', 'helium service'),
            ('HELIUM server', 'HELIUM server'),
            ('development of Helium', 'development of Helium'),
            ('verified by Helium', 'verified by Helium'),
        )
        for source, expected in cases:
            with self.subTest(source=source):
                self.assertEqual(name_pass.replace_text(source), expected)


class DevNamesRecoveryTest(unittest.TestCase):
    def test_retained_recovery_is_not_rebranded_or_registered(self):
        root = Path(__file__).resolve().parents[2]
        for complete in (False, True):
            with self.subTest(complete=complete), \
                    tempfile.TemporaryDirectory(prefix='rac-test-recovery-') as folder:
                tree = Path(folder) / 'src'
                tree.mkdir()
                (tree / 'OWNERS').write_text('fixture\n')
                (tree / 'tools').mkdir()
                (tree / 'tools/grit').symlink_to(root / 'build/src/tools/grit',
                                               target_is_directory=True)
                grd = tree / 'messages.grd'
                xtb = tree / 'messages_fr.xtb'
                message = xml.fromstring(
                    '<message name="IDS_TEST">Chromium browser</message>')
                name_pass.util.add_grit_to_path(root / 'build/src')
                fingerprint = name_pass.compute_fp(message)
                grd.write_text(
                    '<?xml version="1.0" encoding="UTF-8"?>'
                    '<grit latest_public_release="0" current_release="1" '
                    'source_lang_id="en" base_dir=".">'
                    '<translations><file path="messages_fr.xtb" lang="fr" /></translations>'
                    '<release seq="1"><messages>'
                    '<message name="IDS_TEST">Chromium browser</message>'
                    '</messages></release></grit>', encoding='utf-8')
                xtb.write_text(
                    '<translationbundle lang="fr">'
                    f'<translation id="{fingerprint}">Chromium navigateur</translation>'
                    '</translationbundle>', encoding='utf-8')
                originals = {path: path.read_bytes() for path in (grd, xtb)}
                state = tree / dev_names.STATE_DIR
                state.mkdir()
                run = subprocess.run

                def run_pass(command, **kwargs):
                    return run([*command, '--workers', '1'], **kwargs)

                if complete:
                    with mock.patch.object(dev_names.subprocess, 'run',
                                           side_effect=run_pass):
                        dev_names.sub(tree)
                else:
                    run_pass([sys.executable, dev_names.PASSES[0][1], '--sub',
                              '-t', tree, '--backup-path', state / 'helium.tar'],
                             capture_output=True, text=True, check=True)
                    dev_names.record_expected(tree)

                branded = {path: path.read_bytes() for path in (grd, xtb)}
                with mock.patch.object(dev_names.shutil, 'rmtree',
                                       side_effect=OSError('injected recovery cleanup failure')):
                    with self.assertRaisesRegex(OSError, 'recovery cleanup failed') as raised:
                        dev_names.unsub(tree)
                # Find either layout so this test reproduces the old scanner bug.
                recovery, = Path(folder).rglob('unsub-*')
                self.assertIn(str(recovery), str(raised.exception))
                for path, data in branded.items():
                    self.assertEqual((recovery / 'files' / path.name).read_bytes(), data)
                saved = {path: path.read_bytes() for path in recovery.rglob('*')
                         if path.is_file()}
                with mock.patch.object(dev_names.subprocess, 'run', side_effect=run_pass):
                    dev_names.sub(tree)
                self.assertEqual({path: path.read_bytes() for path in saved}, saved)
                self.assertEqual(recovery.parent, tree.parent)
                expected_files = {'messages.grd', 'messages_fr.xtb'}
                ledger = json.loads((state / 'expected.json').read_text())
                self.assertEqual(set(ledger['files']), expected_files)
                for name, _ in dev_names.PASSES:
                    self.assertEqual(set(dev_names.archive_contents(state / f'{name}.tar')),
                                     expected_files)
                dev_names.shutil.rmtree(recovery)
                dev_names.unsub(tree)
                for path, data in originals.items():
                    self.assertEqual(path.read_bytes(), data)


if __name__ == '__main__':
    unittest.main()
