#!/usr/bin/env python3

# Copyright 2026 The rac Authors
# You can use, redistribute, and/or modify this source code under
# the terms of the GPL-3.0 license that can be found in the LICENSE file.
"""Tests for arc_scrub.py on an invented Arc folder. Only temporary folders.

Run from the repository root:
    python3 -m unittest discover -s devutils/rac -p 'test_*.py' -v
"""

from pathlib import Path
import contextlib
import hashlib
import io
import json
import os
import stat
import tempfile
import unittest

import arc_scrub

SPACE_A = '11111111-AAAA-4AAA-8AAA-111111111111'
SPACE_B = '22222222-BBBB-4BBB-8BBB-222222222222'
PINNED = '33333333-CCCC-4CCC-8CCC-333333333333'
TAB = '44444444-DDDD-4DDD-8DDD-444444444444'
TAB2 = '55555555-EEEE-4EEE-8EEE-555555555555'
FOLDER = '66666666-FFFF-4FFF-8FFF-666666666666'
EXT = 'abcdefghijklmnopabcdefghijklmnop'

# Free text that must never survive a scrub.
SECRETS = [
    'Kainoa Personal', 'Bank of Somewhere', 'https://mail.example.org/u/0',
    'secret-project.internal', 'my private note', 'jira', 'Taxes 2026',
    'http://intranet/wiki', 'Diary', 'personal', EXT,
]


def sidebar():
    tab = {
        'id': TAB,
        'title': 'Taxes 2026',
        'parentID': PINNED,
        'childrenIds': [],
        'createdAt': 783000000.5,
        'data': {
            'tab': {
                'savedURL': 'https://mail.example.org/u/0',
                'savedTitle': 'Bank of Somewhere',
                'savedMuteStatus': 'allowAudio',
            }
        },
    }
    tab2 = {
        'id': TAB2,
        'childrenIds': [],
        'data': {
            'tab': {
                'savedURL': 'http://intranet/wiki',
                'savedTitle': 'Taxes 2026',
            }
        },
        'freeform': 'my private note',
        'someLabel': 'personal',
    }
    folder = {
        'id': FOLDER,
        'title': 'Diary',
        'childrenIds': [TAB2],
        'data': {
            'list': {}
        },
    }
    pinned = {
        'id': PINNED,
        'childrenIds': [TAB, FOLDER],
        'data': {
            'itemContainer': {
                'containerType': {
                    'spaceItems': {
                        '_0': SPACE_A
                    }
                }
            }
        },
    }
    space_a = {
        'id': SPACE_A,
        'title': 'Kainoa Personal',
        'containerIDs': ['pinned', PINNED, 'unpinned', PINNED],
        'profile': {
            'custom': {
                '_0': {
                    'directoryBasename': 'Profile 1'
                }
            }
        },
        'customInfo': {
            'iconType': {
                'emoji_v2': '👩🏽‍💻'
            },
            'windowTheme': {
                'background': {
                    'single': {
                        '_0': {
                            'style': {
                                'color': {
                                    '_0': {
                                        'blendedGradient': {
                                            '_0': {
                                                'baseColors': [{
                                                    'red': 0.25,
                                                    'green': 0.5,
                                                    'blue': 1,
                                                    'alpha': 1,
                                                }],
                                                'hex': '#3366FF',
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
        },
    }
    space_b = {
        'id': SPACE_B,
        'title': 'jira',
        'containerIDs': [],
        'profile': {
            'default': True
        },
        'customInfo': {
            'iconType': {
                'emoji': 127881
            }
        },
    }
    return {
        'sidebar': {
            'containers': [
                {
                    'global': {}
                },
                {
                    'spaces': [SPACE_A, space_a, SPACE_B, space_b],
                    'items': [
                        PINNED, pinned, TAB, tab, TAB2, tab2, FOLDER, folder
                    ],
                    # A map keyed by a domain: user data in a key.
                    'byHost': {
                        'secret-project.internal': 1
                    },
                },
            ]
        },
        'version': 1,
    }


def routing():
    return {
        'defaultDestination': {
            'space': {
                '_0': {
                    'mostRecent': {}
                }
            }
        },
        'rules': [{
            'sourceComponents': [{
                'componentType': {
                    'urlMatch': {
                        '_0': {
                            'contains': {}
                        },
                        '_1': 'jira'
                    }
                }
            }],
            'destination': {
                'space': {
                    '_0': SPACE_B
                }
            },
        }],
    }


def md5(text):
    return hashlib.md5(text.encode()).hexdigest()


class ArcScrubTest(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        self.arc = root / 'Arc'
        self.out = root / 'out'
        self.arc.mkdir()
        (self.arc / arc_scrub.SIDEBAR).write_text(json.dumps(sidebar()))
        (self.arc / arc_scrub.ROUTING).write_text(json.dumps(routing()))
        icons = self.arc / arc_scrub.FAVICONS
        icons.mkdir()
        (icons / md5(TAB)).write_bytes(b'real icon bytes')
        # The md5 of a URL, not of an id: its name must not be copied.
        (icons / md5('https://mail.example.org/')).write_bytes(b'x')
        (icons / 'notes.txt').write_text('ignored')
        prefs = self.arc / arc_scrub.USER_DATA / 'Profile 1'
        prefs.mkdir(parents=True)
        (prefs / 'Preferences').write_text(
            json.dumps({
                'extensions': {
                    'pinned_extensions': [EXT]
                },
                'profile': {
                    'name': 'Kainoa Personal'
                },
            }))
        (prefs / 'Cookies').write_text('never read')
        (self.arc / arc_scrub.USER_DATA / 'Local State').write_text(
            json.dumps({
                'profile': {
                    'info_cache': {
                        'Default': {'name': 'Kainoa Personal',
                                    'gaia_name': 'Kainoa Newton'},
                        'Profile 1': {'name': 'Taxes 2026'},
                        'System Profile': {'name': 'Diary'},
                    },
                    'last_used': 'Profile 1',
                },
                'os_crypt': {'encrypted_key': 'my private note'},
            }))

    def tearDown(self):
        self._tmp.cleanup()

    def run_scrub(self):
        with contextlib.redirect_stdout(io.StringIO()):
            arc_scrub.main(['--arc-dir', str(self.arc), '--out', str(self.out)])

    def all_output(self):
        return '\n'.join(
            p.read_bytes().decode('utf-8', 'replace')
            for p in self.out.rglob('*') if p.is_file())

    def test_no_secret_survives(self):
        self.run_scrub()
        text = self.all_output()
        for secret in SECRETS:
            self.assertNotIn(secret, text)
        self.assertNotIn('real icon bytes', text)

    def test_shape_ids_colors_and_emoji_are_kept(self):
        self.run_scrub()
        out = json.loads((self.out / arc_scrub.SIDEBAR).read_text())
        main = out['sidebar']['containers'][1]
        self.assertEqual(main['spaces'][0], SPACE_A)
        space_a = main['spaces'][1]
        self.assertEqual(space_a['containerIDs'],
                         ['pinned', PINNED, 'unpinned', PINNED])
        self.assertEqual(space_a['customInfo']['iconType']['emoji_v2'],
                         '👩🏽‍💻')
        self.assertEqual(
            space_a['profile']['custom']['_0']['directoryBasename'],
            'Profile 1')
        gradient = (space_a['customInfo']['windowTheme']['background']
                    ['single']['_0']['style']['color']['_0']
                    ['blendedGradient']['_0'])
        self.assertEqual(gradient['baseColors'][0]['green'], 0.5)
        self.assertEqual(gradient['hex'], '#3366FF')
        self.assertEqual(main['spaces'][3]['customInfo']['iconType']['emoji'],
                         127881)
        self.assertEqual(main['items'][3]['createdAt'], 783000000.5)
        # Not a known enum word, so it is replaced even though it looks safe.
        self.assertRegex(main['items'][3]['data']['tab']['savedMuteStatus'],
                         r'^s[0-9]+$')

    def test_placeholders_are_stable(self):
        self.run_scrub()
        main = json.loads((self.out / arc_scrub.SIDEBAR).read_text()
                         )['sidebar']['containers'][1]
        tab, tab2 = main['items'][3], main['items'][5]
        # "Taxes 2026" is a custom title on one tab and a page title on the
        # other; both get the same placeholder.
        self.assertEqual(tab['title'], tab2['data']['tab']['savedTitle'])
        self.assertTrue(tab['title'].startswith('Title '))
        self.assertTrue(
            tab['data']['tab']['savedURL'].startswith('https://example.com/'))
        self.assertNotEqual(tab['data']['tab']['savedURL'],
                            tab2['data']['tab']['savedURL'])

    def test_routing_match_text_is_scrubbed(self):
        self.run_scrub()
        out = json.loads((self.out / arc_scrub.ROUTING).read_text())
        match = (out['rules'][0]['sourceComponents'][0]['componentType']
                 ['urlMatch'])
        self.assertRegex(match['_1'], r'^s[0-9]+$')
        self.assertIn('contains', match['_0'])
        self.assertEqual(out['rules'][0]['destination']['space']['_0'],
                         SPACE_B)

    def test_only_pinned_extensions_are_copied(self):
        self.run_scrub()
        profile = self.out / arc_scrub.USER_DATA / 'Profile 1'
        self.assertEqual(sorted(p.name for p in profile.iterdir()),
                         ['Preferences'])
        self.assertEqual(
            sorted(p.name for p in (self.out / arc_scrub.USER_DATA).iterdir()),
            ['Local State', 'Profile 1'])
        prefs = json.loads((profile / 'Preferences').read_text())
        self.assertEqual(list(prefs), ['extensions'])
        (fake, ) = prefs['extensions']['pinned_extensions']
        self.assertRegex(fake, r'^[a-p]{32}$')
        self.assertNotEqual(fake, EXT)

    def test_profile_names_are_placeholders(self):
        self.run_scrub()
        state = json.loads(
            (self.out / arc_scrub.USER_DATA / 'Local State').read_text())
        self.assertEqual(list(state), ['profile'])
        cache = state['profile']['info_cache']
        self.assertEqual(sorted(cache), ['Default', 'Profile 1'])
        self.assertEqual(list(cache['Default']), ['name'])
        self.assertRegex(cache['Profile 1']['name'], r'^Title [0-9]+$')

    def test_favicons_are_placeholders(self):
        self.run_scrub()
        icons = sorted((self.out / arc_scrub.FAVICONS).iterdir())
        self.assertEqual([p.name for p in icons], [md5(TAB)])
        self.assertEqual(icons[0].read_bytes(), arc_scrub.PLACEHOLDER_PNG)

    def test_files_are_private(self):
        self.run_scrub()
        self.assertEqual(stat.S_IMODE(os.stat(self.out).st_mode), 0o700)
        for path in self.out.rglob('*'):
            if path.is_file():
                self.assertEqual(stat.S_IMODE(os.stat(path).st_mode), 0o600,
                                 path)

    def test_report_lists_kept_tokens(self):
        self.run_scrub()
        report = (self.out / arc_scrub.REPORT).read_text()
        self.assertIn('pinned', report)
        self.assertIn('Profile 1', report)
        self.assertIn('👩🏽\u200d💻', report)
        self.assertIn('byHost', report)  # Not a known Arc field: listed.
        self.assertNotIn('allowAudio', report)
        self.assertNotIn('jira', report)

    def test_source_is_not_changed(self):
        before = {
            p: p.read_bytes()
            for p in self.arc.rglob('*') if p.is_file()
        }
        self.run_scrub()
        after = {p: p.read_bytes() for p in self.arc.rglob('*') if p.is_file()}
        self.assertEqual(before, after)

    def test_refuses_out_inside_arc(self):
        with self.assertRaises(SystemExit):
            arc_scrub.main(
                ['--arc-dir',
                 str(self.arc), '--out',
                 str(self.arc / 'copy')])

    def test_arc_dir_is_required(self):
        with self.assertRaises(SystemExit), contextlib.redirect_stderr(
                io.StringIO()):
            arc_scrub.main(['--out', str(self.out)])

    def test_unreadable_prefs_are_reported(self):
        prefs = self.arc / arc_scrub.USER_DATA / 'Profile 1' / 'Preferences'
        prefs.write_text('{"extensions": {"pinned_extens')
        self.run_scrub()
        report = (self.out / arc_scrub.REPORT).read_text()
        self.assertIn('Could not read pinned extensions in "Profile 1"', report)

    def test_refuses_non_empty_out(self):
        self.out.mkdir()
        (self.out / 'x').write_text('x')
        with self.assertRaises(SystemExit):
            self.run_scrub()

    def test_refuses_out_inside_arc_with_other_case(self):
        other = self.arc.parent / 'ARC' / 'copy'
        if not (self.arc.parent / 'ARC').exists():
            self.skipTest('file system is case-sensitive')
        with self.assertRaises(SystemExit):
            arc_scrub.main(['--arc-dir', str(self.arc), '--out', str(other)])
        self.assertFalse((self.arc / 'copy').exists())

    def test_refuses_out_through_symlink_into_arc(self):
        (self.arc / 'inner').mkdir()
        link = self.arc.parent / 'link'
        link.symlink_to(self.arc / 'inner')
        for out in (link / 'copy', link / '..' / 'copy2', link / 'a' / 'b'):
            with self.assertRaises(SystemExit, msg=str(out)):
                arc_scrub.main(['--arc-dir', str(self.arc), '--out', str(out)])
        self.assertEqual(sorted(p.name for p in (self.arc / 'inner').iterdir()),
                         [])
        self.assertFalse((self.arc / 'copy2').exists())

    def test_failure_leaves_no_output(self):
        (self.arc / arc_scrub.ROUTING).write_bytes(b'\xff\xfe not json')
        with self.assertRaises(SystemExit):
            self.run_scrub()
        self.assertFalse(self.out.exists())
        self.assertEqual([p.name for p in self.out.parent.iterdir()],
                         ['Arc'])

    def test_routing_destination_id_is_kept(self):
        value = routing()
        value['rules'][0]['destination'] = {
            'space': {
                '_0': {
                    'specific': {
                        '_0': 'x',
                        '_1': SPACE_B
                    }
                }
            }
        }
        (self.arc / arc_scrub.ROUTING).write_text(json.dumps(value))
        self.run_scrub()
        out = json.loads((self.out / arc_scrub.ROUTING).read_text())
        self.assertEqual(
            out['rules'][0]['destination']['space']['_0']['specific']['_1'],
            SPACE_B)

    def test_missing_sidebar_fails_cleanly(self):
        (self.arc / arc_scrub.SIDEBAR).unlink()
        with self.assertRaises(SystemExit):
            self.run_scrub()
        self.assertFalse(self.out.exists())


class StringRulesTest(unittest.TestCase):

    def test_trailing_newline_is_not_kept(self):
        s = arc_scrub.Scrubber()
        for value in ('Profile 1\n', '#3366ff\n', SPACE_A + '\n', '1\u20e3\n'):
            self.assertNotEqual(s.string(value, 'k'), value, repr(value))
        self.assertNotEqual(s.key('abc\n'), 'abc\n')

    def test_numbers_under_text_keys_are_replaced(self):
        out = arc_scrub.Scrubber().walk({'title': 8085550199, 'n': 3,
                                         'isVibrant': True})
        self.assertEqual(out, {'title': 's1', 'n': 3, 'isVibrant': True})

    def test_all_routing_match_text_is_replaced(self):
        rule = {'sourceComponents': [{'componentType': {
            'hostMatch': {'_0': 'today', '_2': ['contains', 'Profile 2', '🍕'],
                          '_3': SPACE_A}}}]}
        out = arc_scrub.Scrubber().walk(rule, routing=True)
        host = out['sourceComponents'][0]['componentType']['hostMatch']
        self.assertEqual(host['_0'], 's1')
        self.assertEqual(host['_2'], ['s2', 's3', 's4'])
        self.assertEqual(host['_3'], SPACE_A)

    def test_text_with_a_colon_is_not_a_url(self):
        s = arc_scrub.Scrubber()
        self.assertEqual(s.string('Note: call mom', 'k'), 's1')
        self.assertEqual(s.string('localhost:3000', 'k'), 's2')

    def test_number_like_strings_are_replaced(self):
        s = arc_scrub.Scrubber()
        for value in ('+1-808-555-0199', '192.168.1.10', '203.0.113.7:8080',
                      '4111-1111-1111-1111', '123-45-6789', '1990-05-17',
                      '8085550199', 'facade', 'deadbeef', '20261027'):
            self.assertNotEqual(s.string(value, 'k'), value, value)
        self.assertEqual(s.string('#3366ff', 'k'), '#3366ff')

    def test_letter_like_symbols_are_not_emoji(self):
        for value in ('🎉\u200d\ufe0f\u200d\u200d\ufe0f\u200d', '🏻🏿🏽🏻🏿🏽🏻',
                      '🎉\ufe0f\ufe0f', '🎉\u200d', '\u200d🎉',
                      '❶\u200d❷\u200d❸', '⠅⠁⠊⠝⠕⠁', '🄺🄰🄸🄽🄾🄰', '🇰🇦🇮🇳🇴🇦', '8085550199⃣',
                      ''.join(chr(0xE0000 + ord(c)) for c in 'kainoa'),
                      '🏴' + ''.join(chr(0xE0000 + ord(c)) for c in 'secret')
                      + chr(0xE007F), '🍕a', 'a🍕'):
            self.assertFalse(arc_scrub.is_emoji(value), value)
        for value in ('🎉', '👩🏽\u200d💻', '🇯🇵', '1️⃣', '#⃣', '❤️', '©️', '™️',
                      '🏴\U000E0067\U000E0062\U000E0065\U000E006E'
                      '\U000E0067\U000E007F', '🏳️\u200d🌈', '⭐', '🅰️'):
            self.assertTrue(arc_scrub.is_emoji(value), value)

    def test_keys(self):
        s = arc_scrub.Scrubber()
        out = s.walk({'a.b': 'first', 's1': 'second', 'k~1': 3})
        self.assertEqual(len(out), 3)
        self.assertNotIn('a.b', out)
        self.assertEqual(out['s1'], 's2')

    def test_deep_nesting_fails_cleanly(self):
        node = 'x'
        for _ in range(300):
            node = [node]
        with self.assertRaises(arc_scrub.ScrubError):
            arc_scrub.Scrubber().walk(node)

    def test_rules(self):
        s = arc_scrub.Scrubber()
        self.assertEqual(s.string('ftp.example.net/x', 'k'),
                         'https://example.com/1')
        self.assertEqual(s.string('chrome://settings', 'k'),
                         'chrome://placeholder/2')
        self.assertEqual(s.string('Hello World', 'k'), 's1')
        self.assertEqual(s.string('🇯🇵', 'k'), '🇯🇵')
        self.assertEqual(s.string('1️⃣', 'k'), '1️⃣')
        self.assertEqual(s.string('topApps', 'k'), 'topApps')
        self.assertEqual(s.string('work', 'k'), 's2')
        self.assertEqual(s.string('', 'title'), '')


if __name__ == '__main__':
    unittest.main()
