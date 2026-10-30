#!/usr/bin/env python3

# Copyright 2026 The rac Authors
# You can use, redistribute, and/or modify this source code under
# the terms of the GPL-3.0 license that can be found in the LICENSE file.
"""Unit tests for the pure helpers in harness_selftest.py.

Run from the repository root:
    python3 -m unittest discover -s devutils/rac -p 'test_*.py' -v
"""

import json
import tempfile
import unittest
from pathlib import Path

import harness_selftest as st


class FrameFileNameTest(unittest.TestCase):
    """is_frame_filename mirrors IsFrameFileName in window_record.cc."""

    def test_accepts_recorded_names(self):
        for name in ('f0000.png', 'f0001.png', 'f0123.png', 'f9999.png',
                     'f10000.png', 'f123456.png'):
            self.assertTrue(st.is_frame_filename(name), name)

    def test_rejects_lookalikes(self):
        for name in ('f000.png', 'f00.png', 'f.png', 'f.png.png', 'f000a.png',
                     'f000o.png', 'x0000.png', 'ff000.png', 'f-000.png',
                     'f 000.png', 'f0000.pn', 'f0000.pngx', 'f0000.PNG',
                     'af0000.png', 'frames.jsonl', 'f٠٠٠٠.png', 'f0000.jpeg',
                     '.png', 'f', 'png', ''):
            self.assertFalse(st.is_frame_filename(name), name)

    def test_frame_index(self):
        self.assertEqual(st.frame_index('f0000.png'), 0)
        self.assertEqual(st.frame_index('f0427.png'), 427)
        self.assertEqual(st.frame_index('f12345.png'), 12345)
        self.assertIsNone(st.frame_index('f123.png'))
        self.assertIsNone(st.frame_index('other.png'))


class ParseFramesJsonlTest(unittest.TestCase):

    def test_frames_and_done(self):
        text = ('{"i":0,"req_us":1,"res_us":2,"w":10,"h":10,"skipped":0}\n'
                '{"i":1,"req_us":3,"res_us":4,"w":10,"h":10,"skipped":0}\n'
                '{"done":true,"requested":2,"skipped":0}\n')
        indices, done = st.parse_frames_jsonl(text)
        self.assertEqual(indices, [0, 1])
        self.assertEqual(done['skipped'], 0)
        self.assertEqual(done['requested'], 2)

    def test_skipped_writes(self):
        text = ('{"i":0,"req_us":1,"res_us":2,"w":10,"h":10,"skipped":0}\n'
                '{"done":true,"requested":5,"skipped":4}\n')
        indices, done = st.parse_frames_jsonl(text)
        self.assertEqual(indices, [0])
        self.assertEqual(done['skipped'], 4)

    def test_empty_and_garbage(self):
        self.assertEqual(st.parse_frames_jsonl(''), ([], None))
        self.assertEqual(st.parse_frames_jsonl('not json\n{'), ([], None))
        self.assertEqual(st.parse_frames_jsonl('{"i":"0"}'), ([], None))


class FrameLogTest(unittest.TestCase):

    def _log(self, lines):
        return '\n'.join(json.dumps(e) for e in lines)

    def test_steps_between_requests(self):
        events = st.parse_frame_log(self._log([
            {'ev': 'req', 'line': 'pointer-path 0 0 9 9 900'},
            {'ev': 'step', 'name': 'pointer.x', 'v': 1.0},
            {'ev': 'step', 'name': 'pointer.y', 'v': 1.0},
            {'ev': 'step', 'name': 'pointer.x', 'v': 2.0},
            {'ev': 'req', 'line': 'pointer off'},
            {'ev': 'req', 'line': 'pointer 40 40'},
            {'ev': 'step', 'name': 'pointer.x', 'v': 40.0},
            {'ev': 'step', 'name': 'pointer.y', 'v': 40.0},
            {'ev': 'req', 'line': 'command 34031'},
        ]))
        self.assertEqual(
            len(st.pointer_steps_after(events, 'pointer-path')), 2)
        self.assertEqual(st.pointer_steps_after(events, 'pointer off'), [])
        after = st.pointer_steps_after(events, 'pointer 40 40')
        self.assertEqual(len(after), 1)
        self.assertEqual(after[0]['v'], 40.0)

    def test_missing_request(self):
        events = st.parse_frame_log(self._log([
            {'ev': 'step', 'name': 'pointer.x', 'v': 1.0}]))
        self.assertEqual(st.pointer_steps_after(events, 'pointer off'), [])


class PrefsHelpersTest(unittest.TestCase):

    def test_onboarding_done(self):
        with tempfile.TemporaryDirectory() as d:
            prof = Path(d)
            self.assertIsNone(st.onboarding_done(prof))
            (prof / 'Preferences').write_text('{}')
            self.assertIsNone(st.onboarding_done(prof))
            (prof / 'Preferences').write_text(
                '{"helium": {"completed_onboarding": true}}')
            self.assertIs(st.onboarding_done(prof), True)
            (prof / 'Preferences').write_text(
                '{"helium": {"completed_onboarding": false}}')
            self.assertIs(st.onboarding_done(prof), False)

    def test_spaces_dict(self):
        with tempfile.TemporaryDirectory() as d:
            prof = Path(d)
            self.assertIsNone(st.spaces_dict(prof))
            # Chromium stores a dotted pref name nested, not flat.
            (prof / 'Preferences').write_text(
                '{"rac": {"spaces": {"spaces": [], "version": 1}}}')
            self.assertEqual(st.spaces_dict(prof),
                             {'spaces': [], 'version': 1})
            (prof / 'Preferences').write_text(
                '{"rac.spaces": {"spaces": [], "version": 1}}')
            self.assertIsNone(st.spaces_dict(prof))
            (prof / 'Preferences').write_text('{"rac": 1}')
            self.assertIsNone(st.spaces_dict(prof))

    def test_space_themes(self):
        spaces = {'spaces': [
            {'id': 'a', 'last_active': '1', 'theme': {'mode': 'dark'}},
            {'id': 'b', 'last_active': '2'},
        ]}
        self.assertEqual(st.space_themes(spaces),
                         [('a', {'mode': 'dark'}), ('b', None)])
        self.assertIsNone(st.space_themes(None))

    def test_png_indices(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for name in ('f0000.png', 'f0003.png', 'f00.png', 'keep.png',
                         'frames.jsonl'):
                (root / name).write_text('x')
            self.assertEqual(st.png_indices(root), {0, 3})
            self.assertEqual(st.png_indices(root / 'missing'), set())


if __name__ == '__main__':
    unittest.main()
