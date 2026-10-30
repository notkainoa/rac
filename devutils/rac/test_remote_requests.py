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
                     'type hello world', 'nstype plain-words_ok'):
            self.assertEqual(self.ok(line), (line, []), line)
        # Internal pages also report themselves so the Air can check a
        # chrome://setup run carries an import input.
        self.assertEqual(
            self.ok('open-urls https://example.com/a?b '
                    'chrome://settings/appearance about:blank'),
            ('open-urls https://example.com/a?b '
             'chrome://settings/appearance about:blank',
             ['pages chrome://settings/appearance']))

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
        for line, outputs in (
                ('open-urls chrome://settings/assistant',
                 ['pages chrome://settings/assistant']),
                ('open-urls chrome://version about:blank rac://newtab',
                 ['pages chrome://version', 'pages rac://newtab']),
                ('open-urls http://localhost/', []),
                ('open-urls http://localhost:8000/x', []),
                ('open-urls HTTP://LOCALHOST:8000/x', []),
                ('open-urls http://127.0.0.1:3000/', []),
                ('open-urls http://[::1]:8080/', []),
                ('open-urls https://example.com/x', []),
                ('open-urls https://www.example.org/a?b=1', []),
                ('open-urls https://app.example.net:8443/x', []),
                ('open-urls https://myapp.test/', []),
                ('open-urls http://foo.test/bar', []),
                ('open-urls https://dev.localhost/', [])):
            self.assertEqual(self.ok(line), (line, outputs), line)

    def test_internal_pages_are_an_exact_allowlist(self):
        # Every internal page the browser may open is named; anything
        # else chrome:/rac:/about: is refused outright.
        for line, outputs in (
                ('open-urls chrome://setup', ['pages chrome://setup']),
                ('open-urls chrome://setup/arc-import-1',
                 ['pages chrome://setup/arc-import-1']),
                ('open-urls CHROME://Setup/X9', ['pages CHROME://Setup/X9']),
                ('open-urls chrome://setup/', ['pages chrome://setup/']),
                ('open-urls chrome://version', ['pages chrome://version']),
                ('open-urls chrome://newtab', ['pages chrome://newtab']),
                ('open-urls chrome://settings/assistant '
                 'chrome://settings/privacy chrome://settings/appearance',
                 ['pages chrome://settings/assistant',
                  'pages chrome://settings/privacy',
                  'pages chrome://settings/appearance']),
                ('open-urls chrome://rac-ai', ['pages chrome://rac-ai']),
                ('open-urls rac://version rac://settings/privacy rac://rac-ai',
                 ['pages rac://version', 'pages rac://settings/privacy',
                  'pages rac://rac-ai']),
                ('open-urls about:blank ABOUT:Blank', [])):
            self.assertEqual(self.ok(line), (line, outputs), line)
        for line in ('open-urls chrome://settings',
                     'open-urls chrome://settings/',
                     'open-urls rac://settings',
                     'open-urls rac://settings/',
                     'open-urls chrome://settings/importData',
                     'open-urls chrome://settings/passwords',
                     'open-urls chrome://settings/clearBrowserData',
                     'open-urls chrome://extensions',
                     'open-urls chrome://inspect',
                     'open-urls chrome://flags',
                     'open-urls chrome://net-internals',
                     'open-urls chrome://downloads',
                     'open-urls chrome://history',
                     'open-urls chrome://settings/autofill',
                     'open-urls chrome://prefs-internals',
                     'open-urls chrome://local-state',
                     'open-urls chrome://policy',
                     'open-urls chrome://settings/people',
                     'open-urls chrome://settings/syncSetup',
                     'open-urls chrome://settings/resetProfileSettings',
                     'open-urls chrome://devtools',
                     'open-urls chrome://chrome-urls',
                     'open-urls chrome://about',
                     'open-urls chrome://view-source',
                     'open-urls rac://flags',
                     'open-urls rac://settings/importData',
                     # Not the exact page: deeper paths, queries,
                     # fragments, '..', escapes, extra slashes, and
                     # anything past one path segment on setup.
                     'open-urls chrome://settings/appearance/x',
                     'open-urls chrome://version?x',
                     'open-urls chrome://version#x',
                     'open-urls chrome://settings/../version',
                     'open-urls chrome://version%2fsetup',
                     'open-urls chrome://version//',
                     'open-urls chrome://setup/a/b',
                     'open-urls chrome://version.',
                     'open-urls chrome://version:80/',
                     'open-urls chrome://version@evil/',
                     # about: is about:blank only.
                     'open-urls about:',
                     'open-urls about:version',
                     'open-urls about://blank',
                     'open-urls rac:welcome',
                     'open-urls chrome:version'):
            self.refused(line)

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
        # Typed text is plain words only, so no host name, path or
        # punctuation can be typed at all -- and a script that types may
        # not also move the caret or click.
        for line in ('type evil.com ; key return',
                     'type evil ; type .com ; key return',
                     'type evil ; nspress x ; type .com',
                     'type 192.168.1.1', 'type see e.g. this',
                     'type me@evil.com', 'type evil.com#x.test',
                     'type evil.com?q',
                     'type Summarize this page.',
                     'type hello, world! (twice)',
                     'nstype a*b',
                     'type *.png files',
                     'type example.com',
                     'type me@app.test',
                     'type safe ; click 1 2 ; key tab',
                     'type search terms ; nspress return',
                     'type x ; nspress t cmd ; type .test'):
            self.refused(line)
        for line in ('type hello world',
                     'type words with_underscore-and-dash',
                     'type localhost ; key return',
                     'type plain words ; after 5 key return'):
            self.assertEqual(self.ok(line), (line, []), line)

    def test_typed_text_cannot_edit_into_a_denied_page(self):
        # The review's follow-up: after open-urls lands on an allowed
        # page, focusing the omnibox and typing onto the end of its URL
        # reaches a denied page without typing a scheme. Caret and
        # pointer input can't appear in a script that types at all, and
        # the joined typed text's whole words may never spell a denied
        # page name.
        for line in ('open-urls chrome://version ; nspress end '
                     '; type importData ; key return',
                     'open-urls chrome://version ; key end '
                     '; type importData ; key return',
                     'open-urls chrome://version ; nspress end '
                     '; type /importData ; key return',
                     'type import ; type Data',
                     'type import ; nstype Data',
                     'type im ; type portData',
                     'type IMPORT ; nspress d ; type ATA',
                     'type import- ; type data ; key return',
                     'nstype pass ; nstype words',
                     'type my pass ; type words ; key return',
                     'type view ; type source',
                     'type the flags page',
                     'type chrome ; nstype urls',
                     'type about',
                     # 'people' and 'about' are denied page names, so
                     # even innocuous text spelling them is refused.
                     'type the people i know',
                     'type download ; nspress s',
                     'type local ; type state'):
            self.refused(line)
        for line in ('type hello world',
                     'type load a fixture',
                     # Whole words only: 'profilesettings' never spells
                     # 'resetprofilesettings', and 'settings' alone names
                     # no denied page.
                     'type reset profile ; type settings',
                     'type settings ; key return'):
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

    def test_commands_are_an_allowlist(self):
        # History, downloads, clear data, import, settings, passwords,
        # about, the app menu, extensions, task manager, cast, translate,
        # Helium services, open in Chrome: none is on COMMANDS_ALLOWED.
        for line in ('command 40010', 'command 40012', 'command 40013',
                     'command 40014', 'command 40015', 'command 40017',
                     'command 40018', 'command 40021', 'command 40022',
                     'command 40006', 'command 35011', 'command 35009',
                     'command 40700', 'command 34072', 'command 35041',
                     'command 99999', 'after 5 command 40010'):
            self.refused(line)
        for line in ('command 34014', 'command 034014', 'command 40721',
                     'command 37000', 'command 38001'):
            self.assertEqual(self.ok(line), (line, []), line)

    def test_cmd_chords_to_unlisted_pages(self):
        # Cmd+Y history, Opt+Cmd+L downloads, Opt+Cmd+B bookmark manager,
        # Shift+Cmd+Backspace clear browsing data.
        for line in ('nspress y cmd', 'nspress l cmd,alt', 'nspress b cmd,alt',
                     'nspress backspace cmd,shift', 'nspress backspace cmd',
                     'after 5 nspress y cmd'):
            self.refused(line)
        for line in ('nspress backspace', 'nspress y', 'nspress b cmd,shift',
                     'nspress l cmd'):
            self.assertEqual(self.ok(line), (line, []), line)

    def test_typed_text_is_ascii(self):
        # The omnibox maps full-width letters and dots onto ASCII hosts and
        # page names, which the ASCII token and host checks would miss.
        for line in ('type \uff49\uff4d\uff50\uff4f\uff52\uff54',
                     'type \uff45\uff56\uff49\uff4c\u3002com',
                     'type caf\u00e9'):
            self.refused(line)

    def test_typed_text_never_spells_setup_or_import(self):
        # Editing chrome://version into chrome://setup would open the Arc
        # import screen on the Pro's real Arc data; import reaches the
        # import dialog through the settings search box.
        for line in ('open-urls chrome://version ; key end ; type setup ; key return',
                     'type set ; type up', 'type import', 'nstype chrome'):
            self.refused(line)

    def test_typing_scripts_carry_no_caret_or_clicks(self):
        # A script that types may not also move the caret, the pointer or
        # the app; unmodified nspress letters count as typing too.
        for line in ('click 300 40 ; key right ; key backspace ; type tData '
                     '; key left ; type impor ; key return',
                     'click 300 40 ; type com ; key left ; type evil ; key return',
                     'type evil.com ; key return',
                     'type hello ; key return ; key return',
                     'type hello ; nspress a',
                     'nspress h ; nspress i ; click 10 10',
                     'type a ; command 34014',
                     'type x ; move 1 2', 'type x ; wheel 1 2 3',
                     'type x ; swipe 1 2 end', 'type x ; pointer 1 2',
                     'type x ; pointer-path 0 0 1 1 5',
                     'type x ; key tab', 'type x ; nskey tab down',
                     'type x ; nsflags cmd', 'nstype y ; nspress a',
                     'type x ; command 34000',
                     'type x ; after 5 click 1 2'):
            self.refused(line)
        for line in ('type hello world ; key return',
                     'open-urls http://localhost:8000/ ; type hello ; key return',
                     'type x ; after 5 key return',
                     'type x ; type y ; key return',
                     'nspress h ; nspress i ; key return'):
            self.assertEqual(self.ok(line), (line, []), line)

    def test_typing_scripts_press_return_only_at_the_end(self):
        # A return between typed pieces submits the first and starts a
        # fresh field, which the joined-words check can't see.
        for line in ('type my ; key return ; type history ; key return',
                     'key return ; type x ; key return',
                     'key return ; type x',
                     'nspress a ; key return ; nspress b'):
            self.refused(line)
        self.assertEqual(
            self.ok('type hello ; burst shots 3 100'),
            ('type hello ; burst @SHOTS@/shots 3 100',
             ['dir shots', 'expect shots/f00.png', 'expect shots/f01.png',
              'expect shots/f02.png']))

    def test_typing_refusal_names_the_rule(self):
        try:
            self.rr.check_line('type a ; click 1 2')
            self.fail('not refused')
        except self.rr.Refused as e:
            self.assertIn('a script that types may not move the caret or '
                          'click; ask Ship', str(e))

    def test_settings_pages_take_screenshots_only(self):
        # The three settings pages that may open take shots only: any
        # input verb in the same script refuses, on top of the typing
        # rule's own restrictions.
        for line in ('open-urls chrome://settings/privacy ; click 10 10',
                     'open-urls chrome://settings/assistant ; key tab',
                     'open-urls chrome://settings/appearance ; type x',
                     'open-urls chrome://settings/privacy ; nspress a',
                     'open-urls rac://settings/privacy ; wheel 1 2 3',
                     'open-urls chrome://settings/appearance ; move 1 2',
                     'open-urls chrome://settings/assistant ; command 34000',
                     'open-urls chrome://settings/privacy ; swipe 1 2 end',
                     'open-urls chrome://settings/assistant ; pointer 1 2',
                     'open-urls chrome://settings/appearance '
                     '; after 5 click 1 2'):
            self.refused(line)
        for line, outputs in (
                ('open-urls chrome://settings/appearance ; burst shots 3 100',
                 ['pages chrome://settings/appearance', 'dir shots',
                  'expect shots/f00.png', 'expect shots/f01.png',
                  'expect shots/f02.png']),
                ('open-urls chrome://settings/privacy '
                 '; capture-window first shot.png',
                 ['pages chrome://settings/privacy', 'expect shot.png']),
                ('open-urls chrome://settings/appearance ; windows windows.txt',
                 ['pages chrome://settings/appearance', 'file windows.txt'])):
            self.assertEqual(self.ok(line)[1], outputs, line)

    def test_env_wildcards_may_not_cover_public_suffixes(self):
        # *.com or *.github.io would open a slice of the internet, not one
        # host's family; like any malformed entry they refuse every line.
        for entry in ('*.com', '*.dev', '*.io', '*.horse', '*.zz',
                      '*.local', '*.co.uk', '*.com.au',
                      '*.github.io', '*.pages.dev', '*.vercel.app',
                      '*.netlify.app', '*.herokuapp.com',
                      'build.local, *.ai'):
            with unittest.mock.patch.dict(
                    os.environ, {'RAC_REMOTE_ALLOWED_HOSTS': entry}):
                self.refused('open-urls https://a.github.io/x')
                self.refused('key tab')
        for entry in ('*.test', '*.localhost', '*.example.com',
                      '*.internal', '*.example', '*.invalid',
                      '*.co.uk.evil.test', '*.foo.horse', 'horse'):
            with unittest.mock.patch.dict(
                    os.environ, {'RAC_REMOTE_ALLOWED_HOSTS': entry}):
                self.ok('key tab')

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
