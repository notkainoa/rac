#!/usr/bin/env python3

# Copyright 2026 The rac Authors
# You can use, redistribute, and/or modify this source code under
# the terms of the GPL-3.0 license that can be found in the LICENSE file.
"""remote_requests.py against the harness's grammar (window_screenshot.mm
and dev/*): every path it writes is marked, and nothing it can't
recognise passes.

Run from the repository root:
    python3 -m unittest discover -s devutils/rac -p 'test_remote_*.py' -v
"""

from pathlib import Path
import os
import sys
import unittest
import unittest.mock

HERE = Path(__file__).resolve().parent


class RemoteRequestsTest(unittest.TestCase):

    def setUp(self):
        sys.path.insert(0, str(HERE))
        self.addCleanup(sys.path.remove, str(HERE))
        import remote_requests
        self.rr = remote_requests

    def ok(self, line):
        out, outputs, _ = self.rr.check_line(line)
        return out, outputs

    def refused(self, line):
        with self.assertRaises(self.rr.Refused, msg=repr(line)):
            self.rr.check_line(line)

    def test_marks_every_path_the_harness_writes(self):
        for line, out, outputs in [
            ('a/b.png', '@SHOTS@/a/b.png', ['expect a/b.png']),
            ('hit 10 20 views.txt', 'hit 10 20 @SHOTS@/views.txt', ['file views.txt']),
            ('windows list', 'windows @SHOTS@/list', ['file list']),
            ('record rec 500 0.5', 'record @SHOTS@/rec 500 0.5', ['dir rec']),
            ('burst b 3 100', 'burst @SHOTS@/b 3 100',
             ['dir b', 'expect b/f00.png', 'expect b/f01.png', 'expect b/f02.png']),
            ('burst b 0 100', 'burst @SHOTS@/b 0 100', ['dir b']),
            ('capture-window app:x c.png', 'capture-window app:x @SHOTS@/c.png',
             ['expect c.png']),
            ('after 5 after 6 d.png', 'after 5 after 6 @SHOTS@/d.png', ['expect d.png']),
            ('click 1 2 ; after 10 e.png', 'click 1 2 ; after 10 @SHOTS@/e.png',
             ['expect e.png']),
        ]:
            self.assertEqual(self.ok(line), (out, outputs), line)

    def test_passes_input_verbs_unchanged(self):
        for line in ('command 34000', 'move 1 2', 'click -1 2', 'wheel 1 2 -3',
                     'key escape', 'nspress t cmd,shift', 'nspress pagedown',
                     'nskey tab down ctrl', 'nsflags none', 'swipe 1 2 end',
                     'swipe 1 2 -4.5 10 hold', 'appearance dark', 'contrast on',
                     'space-theme 3 dark', 'space-theme -', 'space-new',
                     'pointer off', 'pointer 1.5 2', 'pointer-path 0 0 10 10 200',
                     'target name:x', 'target #2', 'profile-window Profile_2',
                     'open-urls https://example.com/a?b chrome://settings about:blank',
                     'type hello world', 'nstype a*b'):
            self.assertEqual(self.ok(line), (line, []), line)

    def test_refuses_what_the_harness_would_misread(self):
        for line in [
            # Whitespace the harness keeps inside a word would let the
            # checker see one request (typed text) where it sees two.
            'type\u00a0;\u00a0after 0 x.png', 'type a\u2003; b.png',
            # An `after` whose request the harness doesn't recognise is
            # captured to a file named after the request's text.
            'after 5 unknown words', 'after 5 click a b', 'after 5 windows x',
            'after 5 hit 1 2 x', 'after 99999999999 x.png', 'after \u00b2 x.png',
            # Paths in every verb that writes one.
            'hit 1 2 /tmp/x', 'windows /tmp/x', 'windows ../x', 'record /tmp 5',
            'record ../x 5', 'burst ~/x 1 1', 'capture-window app ../x.png',
            'capture-window app x.txt', 'x.PNG', 'a//b.png', './a.png',
            # Downloads and external schemes land outside the clone.
            'open-urls data:application/octet-stream,x', 'open-urls javascript:x',
            'open-urls file:///etc/hosts', 'open-urls example.com',
            'open-urls https://files.example/payload.dmg',
            # Unknown verbs and arguments, a bare PNG among several requests,
            # a lone ';' in typed text, and too many burst frames.
            'rm x', 'click 1', 'key ../x.json', 'appearance x', 'a.png ; b.png',
            'type a ; ; b.png', 'nstype ;', 'burst b 100000 1', 'hit 1 2 x ; key tab',
            '', 'x.png\ny.png', '@SHOTS@/x.png', 'type a\tb',
        ]:
            self.refused(line)

    def test_open_urls_only_opens_allowed_urls(self):
        # A URL outside the allowlist can fetch a payload into the Pro's
        # own Downloads, or hand an external scheme to another app.
        for line in ('open-urls https://files.example/payload.dmg',
                     'open-urls http://169.254.169.254/meta',
                     'open-urls https://example.com.evil.org/',
                     'open-urls https://localhost@evil.com/',
                     'open-urls https://user@evil.com/',
                     'open-urls file:///etc/hosts',
                     'open-urls data:text/html,x',
                     'open-urls javascript:alert(1)',
                     'open-urls view-source:https://example.com',
                     'open-urls ftp://example.com/x',
                     'open-urls smb://server/share',
                     'open-urls mailto:x@y.z',
                     'open-urls localhost.evil.com/x',
                     'open-urls https://internal/x',
                     # Parser tricks: the host the browser connects to
                     # is never the one a looser split would see.
                     'open-urls http://evil.com\\@localhost/x.dmg',
                     'open-urls http://127.0.0.1@evil.com/',
                     'open-urls http://localhost:@evil.com/',
                     'open-urls https://evil.com#.test',
                     'open-urls https://evil.com?.test',
                     'open-urls http://127.0.0.1.evil.com/',
                     'open-urls http://localhost./',
                     'open-urls http://2130706433/',
                     'open-urls http://[::ffff:7f00:1]/',
                     'open-urls http://ex\u0430mple.com/',
                     'open-urls http://localhost:999999/',
                     'open-urls HTTP://EVIL.COM/',
                     'open-urls FILE:///etc/hosts',
                     'open-urls View-Source:http://localhost/',
                     # host:port reaches openURLs: as an unknown scheme.
                     'open-urls localhost:8000/x',
                     'open-urls localhost:@evil.com/x.dmg'):
            self.refused(line)
        for line in ('open-urls chrome://settings',
                     'open-urls chrome://version about:blank rac:welcome',
                     'open-urls http://localhost/',
                     'open-urls http://localhost:8000/x',
                     'open-urls HTTP://LOCALHOST:8000/x',
                     'open-urls http://127.0.0.1:3000/',
                     'open-urls http://[::1]:8080/',
                     'open-urls https://example.com/x',
                     'open-urls https://www.example.org/a?b=1',
                     'open-urls https://app.example.net:8443/x',
                     'open-urls https://myapp.test/',
                     'open-urls http://foo.test/bar',
                     'open-urls https://dev.localhost/'):
            self.assertEqual(self.ok(line), (line, []), line)

    def test_open_urls_env_allowed_hosts(self):
        # RAC_REMOTE_ALLOWED_HOSTS adds exact names and *.suffixes.
        extra = {'RAC_REMOTE_ALLOWED_HOSTS': 'build.local, *.internal'}
        with unittest.mock.patch.dict(os.environ, extra):
            self.ok('open-urls https://build.local/x')
            self.ok('open-urls https://ci.internal/run')
            self.ok('open-urls https://deep.ci.internal/run')
            self.refused('open-urls https://internal/')
            self.refused('open-urls https://notbuild.local/')
            self.refused('open-urls https://evil.com/')
        self.refused('open-urls https://build.local/x')
        # An entry that isn't a hostname refuses every line, even one that
        # needs no extra host: a typo must not pass silently.
        for entry in ('bad;host', 'http://x', '.internal', '-.bad',
                      'build.local, evil.com/x', '*.'):
            with unittest.mock.patch.dict(
                    os.environ, {'RAC_REMOTE_ALLOWED_HOSTS': entry}):
                self.refused('open-urls https://build.local/x')
                self.refused('open-urls http://localhost/')
                self.refused('key tab')
        with unittest.mock.patch.dict(
                os.environ, {'RAC_REMOTE_ALLOWED_HOSTS': ' build.local ,'}):
            self.ok('open-urls https://build.local/x')

    def test_typed_text_cannot_navigate(self):
        # The review's bypass: a typed file:// URL submitted by a return
        # keypress, then a screenshot of what the page showed.
        self.refused('command 34000 ; type file:///Users/knewton/.ssh/id_rsa'
                     ' ; key return ; after 3000 leak.png')
        # No scheme or path can be typed at all, so none can be submitted
        # by return, a click on a suggestion, or anything else.
        for line in ('type file:///etc/hosts',
                     'type data:text/html,x',
                     'type javascript:alert(1)',
                     'type view-source:https://example.com',
                     'type http://evil.com/x',
                     'type ~/Library/x',
                     'type /etc/hosts',
                     'type C:\\Windows\\system32',
                     'type foo%20bar',
                     'nstype //evil.com/x',
                     'after 5 type file:///etc/hosts',
                     # Allowed URLs too: editing keys can turn one into
                     # another (chrome:///Users/... minus "chrome").
                     'type chrome://settings',
                     'type localhost:8000/x',
                     'type chrome:///Users/knewton/.ssh/id_rsa ; nspress home',
                     # Pieces that only spell a URL once joined.
                     'command 39001 ; type file ; type :Users/knewton/.ssh/id_rsa'
                     ' ; after 500 click 300 60 ; after 3000 leak.png',
                     'nstype view-source ; nstype :file ; nstype :Users',
                     'type localhost:@evil.com/x.dmg'):
            self.refused(line)
        # A host name the omnibox would open must be an allowed one, also
        # when typed in pieces or with nspress letters between them.
        for line in ('type evil.com ; key return',
                     'type evil ; type .com ; key return',
                     'type evil ; nspress x ; type .com',
                     'type 192.168.1.1', 'type see e.g. this',
                     'type me@evil.com', 'type evil.com#x.test',
                     'type evil.com?q'):
            self.refused(line)
        for line in ('type hello world',
                     'type Summarize this page.',
                     'type hello, world! (twice)',
                     'nstype a*b',
                     'type *.png files',
                     'type example.com',
                     'type me@app.test',
                     'type localhost ; key return',
                     'type plain words ; after 5 key return',
                     'type safe ; click 1 2 ; key tab',
                     'type search terms ; nspress return',
                     'type x ; nspress t cmd ; type .test'):
            self.assertEqual(self.ok(line), (line, []), line)

    def test_shortcuts_and_commands_that_leave_the_clone(self):
        # Paste (the Pro's clipboard), open/print dialogs, DevTools, view
        # source and services that hand text to other apps.
        for line in ('command 39001 ; nspress v cmd ; after 500 clip.png',
                     'nspress v cmd,shift,alt', 'nspress o cmd', 'nspress p cmd',
                     'nspress c cmd', 'nspress x cmd', 'nspress e cmd',
                     'nspress i cmd,alt', 'nspress j cmd,alt', 'nspress u cmd,alt',
                     'nspress c cmd,alt', 'nspress i cmd,shift',
                     'nspress l cmd,shift', 'after 5 nspress v cmd',
                     'command 36003', 'command 40256', 'command 40000',
                     'command 35004', 'command 35003', 'command 35007',
                     'command 35002', 'command 40004', 'command 40254',
                     'command 40002', 'command 40014', 'command 35006',
                     'command 34071', 'after 5 command 40000'):
            self.refused(line)
        for line in ('nspress t cmd', 'nspress s cmd', 'nspress l cmd',
                     'nspress 1 cmd', 'nspress v', 'nspress c ctrl',
                     'nspress left cmd,alt', 'nspress t cmd,shift',
                     'command 34000', 'command 39001', 'command 34014'):
            self.assertEqual(self.ok(line), (line, []), line)

    def test_lists_every_verb_the_line_uses(self):
        # The Pro refuses a verb missing from the clone's harness sources;
        # the list has to cover nested `after` requests and skip paths.
        out, outputs, verbs = self.rr.check_line(
            'click 1 2 ; after 5 key tab ; after 9 x.png')
        self.assertEqual(out, 'click 1 2 ; after 5 key tab ; '
                              'after 9 @SHOTS@/x.png')
        self.assertEqual(outputs, ['expect x.png'])
        self.assertEqual(verbs, ['after', 'click', 'key'])
        self.assertEqual(
            self.rr.check_line('a.png')[2], [])
        self.assertEqual(
            self.rr.check_line('type a ; record r 500')[2],
            ['record', 'type'])

    def test_refuses_unsafe_whitespace_and_bad_paths(self):
        # The harness splits on plain spaces only; other whitespace in a
        # word would reach it unchecked or split the line differently.
        for line in ('type a\tb', 'click 1\r2', 'x\x00.png',
                     'click 1\x0b2', 'type a b', 'type a　b',
                     'key tab\x7f'):
            self.refused(line)
        # An output path part may not be empty, '.', or '..'.
        for line in ('../x.png', 'a/../x.png', 'a/./x.png', 'a//x.png',
                     'windows ../list', 'record a/../r 500',
                     'burst b/../c 1 1', 'capture-window first a/../x.png',
                     'hit 1 2 a/../v.txt'):
            self.refused(line)

    def test_grammar_matches_the_harness(self):
        # window_state.mm rejects a space-theme preset >= kPresetCount (8);
        # an unrecognized request inside `after` becomes an output path.
        for line in ('space-theme 8', 'space-theme 42', 'space-theme 800',
                     'after 5 space-theme 9'):
            self.refused(line)
        for line in ('space-theme 0', 'space-theme 7', 'space-theme 07',
                     'space-theme -', 'space-theme - dark',
                     'space-theme 3 auto', 'space-new',
                     'after 5 space-theme 2'):
            self.assertEqual(self.ok(line), (line, []), line)


if __name__ == '__main__':
    unittest.main()
