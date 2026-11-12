#!/usr/bin/env python3

# Copyright 2026 The rac Authors
# You can use, redistribute, and/or modify this source code under
# the terms of the GPL-3.0 license that can be found in the LICENSE file.
"""Checks a window-screenshot request line before remote-build.sh hands it
to a browser on the MacBook Pro.

The dev harness (--rac-window-screenshot-requests, window_screenshot.mm and
dev/*) reads one line from a file and acts on it, writing files to whatever
paths the line names. On the maintainer's own Mac that must never reach
outside the clone, so only requests the harness is known to accept pass,
spelled the way it reads them, and every path in them has to be relative;
it is rewritten to sit under the clone's build/shots/ (marked @SHOTS@ here;
the Pro side fills it in). A request the harness wouldn't recognise is
refused rather than passed on: inside `after`, the harness captures an
unrecognised request to a file named after its text.

usage: remote_requests.py [--serve] <file>
       remote_requests.py [--serve] --url <url>   (exit 0 if a run may open it)

--serve says the run passes `--serve DIR`, so `@SERVE@` URLs (the run's
own loopback file server, see SERVE_URL) may open; without it they are
refused.

Prints the checked line, a `verbs VERB...` line listing every request
verb it uses (the Pro checks each is a string literal in the clone's own
harness sources, and the Air reads them back: a settings page opened as
a run arg allows no input verb), a `pages URL` line per chrome:/rac:
page open-urls visits (the Air reads them back too: a run that opens
chrome://setup needs an Arc import input in the same run), a
`needs SWITCH` line per run switch the line depends on (the Air refuses
the run unless SWITCH is among its args: `needs --test-type` for the PWA
commands), a `commands ID...` line with the ids of the line's command
verbs (the Air reads it back: a settings page opened as a run arg allows
only the zoom commands; the Air strips it before the Pro sees the
stream), then one line per path in it, REL
under build/shots/, so the Pro side never has to parse the line:
`file REL` (a file it writes), `dir REL` (a folder it writes into) or
`expect REL` (a screenshot the run waits for: bare PNG paths,
capture-window's OUT, and each of a burst's DIR/fNN.png frames). Exits 2
on a refusal.
"""

import os
import re
import sys

MARK = '@SHOTS@'
MAX_LINE = 4096
# The harness turns a burst's N into N tasks at once.
MAX_BURST = 1000
INT = re.compile(r'-?[0-9]{1,9}')
NUMBER = re.compile(r'-?[0-9]{1,9}(\.[0-9]{1,6})?')
PATH = re.compile(r'[A-Za-z0-9._/-]+')
# URLs open-urls may send the browser to. http(s) only reaches loopback
# and the reserved test names (anything else could fetch a payload or
# open an external scheme). There is no userinfo, backslash or
# non-ASCII, so the host checked is the host the browser connects to.
# RAC_REMOTE_ALLOWED_HOSTS (comma-separated hostnames or *.suffixes)
# adds hosts for a setup that needs them; a malformed entry is refused,
# never skipped. chrome: and rac: match only INTERNAL_PAGES (plus the
# setup/<segment> import screens), and about: only about:blank: a page
# like chrome://flags or chrome://settings/importData does as much harm
# as a fetch, so internal URLs are a fixed list, not "any chrome: page".
HTTP_URL = re.compile(r'https?://(?P<host>\[::1\]|[A-Za-z0-9.-]+)(:[0-9]{1,5})?'
                      r'([/?#][!-\[\]-~]*)?', re.ASCII | re.I)
# The internal pages a run may open, as host+path after chrome:// or
# rac:// (the Arc import screens live under setup/, matched by
# SETUP_STEP). Matching is case-insensitive on scheme and host with one
# optional trailing slash; a query, fragment, ".." or percent-escape can
# never match. Never add pages that read the maintainer's data or open
# the browser to control (importData, passwords, flags, downloads,
# history, devtools, ...). The settings root is off the list on purpose:
# only these sub-pages may open, and a run that opens one may take
# screenshots only -- the script may not send input (see check_line).
# chrome://credits (the build's static license page) is screenshot-only
# the same way: its links lead to the open web.
INTERNAL_PAGES = frozenset((
    'setup', 'version', 'newtab', 'settings/assistant',
    'settings/privacy', 'settings/appearance', 'settings/general',
    'settings/system', 'settings/system/shortcuts', 'settings/bangs',
    'rac-ai', 'credits',
))
INTERNAL_URL = re.compile(r'(?:chrome|rac)://([!-\[\]-~]*)', re.ASCII | re.I)
SETUP_STEP = re.compile(r'setup/[A-Za-z0-9-]+')
# The welcome tour opened straight at its Arc import step. The query must
# be exactly "arc"; only the host's case is free.
SETUP_ARC = re.compile(r'(?i:setup)\?arc')
# The run's own file server (`run --serve DIR`): the Pro serves DIR on
# 127.0.0.1 at a port it picks and replaces the placeholder with
# http://127.0.0.1:PORT. Only a path may follow, starting with `/`, of
# plain URL characters with no `..`, `%`, `@`, `:`, query or fragment:
# nothing after the placeholder can name another host or port.
SERVE = '@SERVE@'
SERVE_URL = re.compile(r'@SERVE@(/[A-Za-z0-9._~/-]*)?', re.ASCII)
TEST_HOSTS = {'localhost', '127.0.0.1', '[::1]',
              'example.com', 'example.org', 'example.net'}
TEST_SUFFIXES = ('.test', '.localhost',
                 '.example.com', '.example.org', '.example.net')
# A RAC_REMOTE_ALLOWED_HOSTS wildcard whose suffix is itself a public
# suffix would let a run open a whole slice of the internet, not one
# host's family, so it is refused as malformed like any other bad entry.
# Any single-label suffix is refused (every TLD, including ones nobody
# lists, like *.horse) except the reserved names below, and so are the
# well-known two-label public suffixes.
RESERVED_LABELS = frozenset(('test', 'localhost', 'internal', 'example',
                             'invalid'))
PUBLIC_SUFFIXES = frozenset((
    'co.uk', 'com.au', 'github.io', 'pages.dev', 'vercel.app',
    'netlify.app', 'herokuapp.com',
))
HOSTNAME = re.compile(r'[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?'
                      r'(\.[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?)*', re.ASCII | re.I)
MODS = {'ctrl', 'shift', 'cmd', 'alt'}
WINDOW_KINDS = {'first', 'normal', 'incognito', 'app', 'popup', 'devtools',
                'pip', 'browser', 'onboarding', 'child', 'other'}
KEYS = {'return', 'escape', 'tab', 'backspace', 'up', 'down', 'left', 'right'}
NSPRESS_KEYS = KEYS | {'space', 'home', 'end', 'pageup', 'pagedown'}
# Typed text is plain words only: ASCII letters, digits, spaces, '-',
# '_' and '!' (a bang, as in `cats !w`). Without dots, colons or slashes
# it can't spell a URL, a host name or a path, however the pieces join or
# whatever submits it. Text with a '!' may never be submitted (see
# check_line), so a bang only ever shows suggestions.
TYPED_TEXT = re.compile(r'[A-Za-z0-9 _!-]+')
# IDC_FOCUS_LOCATION: focuses the address bar, the one place a script's
# typed text should land. A typing script may send it; it moves focus to a
# known field rather than walking the page.
FOCUS_LOCATION = 39001
# Whole words the typed text may never spell: the denied page names,
# checked against every run of letters and digits in the joined typed
# text (spaces, '-' and '_' separate words; case is folded). `type my
# history book` refuses on `history`; `type histories` and `type
# chromebook` pass. `about` is on the list because about:blank is the
# only allowed about: page, and setup/import/chrome because those pages
# read the maintainer's real data.
TYPED_PAGE_TOKENS = frozenset((
    'importdata', 'passwords', 'password', 'clearbrowserdata',
    'extensions', 'inspect', 'flags', 'netinternals', 'downloads',
    'history', 'autofill', 'prefsinternals', 'localstate', 'policy',
    'syncsetup', 'resetprofilesettings', 'devtools', 'people',
    'viewsource', 'chromeurls', 'about',
    # The Arc import screens and the import dialog read the Mac's own
    # browser data (also found through the settings search box).
    'setup', 'import', 'chrome',
))
# Cmd shortcuts that reach outside the clone: the open and print dialogs,
# the clipboard (paste, copy, cut, find pasteboard), view source,
# DevTools, mailing the page; with Shift, the Search With Google and
# sticky-note services, which hand the selection to another app. Cmd+S
# stays: rac's sidebar toggle, and remote-build.sh turns file dialogs off
# in the clone profile, so its Save Page fallback can't pick a folder.
CMD_DENIED = set('ceijopuvx')
CMD_SHIFT_DENIED = CMD_DENIED | set('ly')
# Cmd chords (accelerators_cocoa.mm, global_keyboard_shortcuts_mac.mm)
# that open an internal page off the allowlist: history (Cmd+Y),
# downloads (Opt+Cmd+L), the bookmark manager (Opt+Cmd+B) and clear
# browsing data (Shift+Cmd+Backspace; any Cmd+Backspace is refused).
CMD_CHORDS_DENIED = (('y', set()), ('l', {'alt'}), ('b', {'alt'}),
                     ('backspace', set()))
# chrome_command_ids.h: the only commands a run may send. A fixed list,
# like the run args: a denylist of ~300 ids always misses one that opens
# an internal page (history, downloads, settings, extensions, passwords),
# a dialog, another app, the clipboard or DevTools.
# Zoom in, reset and out (IDC_ZOOM_PLUS/NORMAL/MINUS): drawing only, so a
# settings run may use them.
COMMANDS_ZOOM = frozenset((38001, 38002, 38003))
COMMANDS_ALLOWED = frozenset((
    33000, 33001, 33002, 33003, 33006, 33007,  # back, forward, reload, home, stop
    34000, 34001, 34012, 34014, 34015, 34016, 34017,  # windows and tabs
    *range(34018, 34027), 34027, 34028, 34030, 34032, 34033,
    34046, 34047, 34052, 34056, 34057, 34058, 34060, 34061, 34062, 34063,
    *range(34082, 34087), 34091,  # layouts, zen mode pin
    *range(34100, 34106), 34107, 34108,  # tab groups
    37000, 37001, 37002, 37003,  # find
    38001, 38002, 38003,  # zoom
    39000, 39001, 39002, 39004, 39005, 39006, 39009,  # focus
    40009,  # bookmark bar
    40701,  # rac assistant
    *range(40710, 40727),  # rac spaces, favorites, pinned tabs
    # rac_action_ids.h (core/action-table.patch): the command bar, the
    # command bar holding the current URL, clear tabs, little window.
    # Not the rest of rac's 40800-40999 range: 40804
    # (IDC_RAC_COPY_AS_MARKDOWN) writes the Mac's clipboard, and the later
    # ids are unreviewed.
    40800, 40801, 40802, 40803,
))
# Commands a run may send only when it also passes --test-type (the Air
# checks the run args; see `needs` in main): IDC_CREATE_SHORTCUT (40002,
# the PWA install dialog) and IDC_OPEN_IN_PWA_WINDOW (34055). Installing
# a PWA writes an app shim into ~/Applications, outside the clone, unless
# --test-type makes AppShimCreationAndLaunchDisabledForTest() true
# (chrome/browser/web_applications/os_integration/mac/
# web_app_shortcut_mac.mm, lines 39-44); shim creation and launch then
# skip (same file, 195 and 324; app_shim_launch.mm 259;
# app_shim_manager_mac.cc 746 and 1955).
COMMANDS_NEED_TEST_TYPE = frozenset((40002, 34055))


class Refused(Exception):
    pass


def extra_allowed_hosts():
    """RAC_REMOTE_ALLOWED_HOSTS as exact names and `.suffix`es (from
    `*.suffix`). An entry that isn't a hostname is refused: skipping it
    would quietly leave out a host the run needs."""
    hosts = set()
    for raw in os.environ.get('RAC_REMOTE_ALLOWED_HOSTS', '').split(','):
        entry = raw.strip().lower()
        if not entry:
            continue
        name = entry[2:] if entry.startswith('*.') else entry
        if not HOSTNAME.fullmatch(name):
            raise Refused('RAC_REMOTE_ALLOWED_HOSTS entries are hostnames or '
                          f'*.suffixes, not {raw.strip()!r}')
        if entry.startswith('*.') and (
                name in PUBLIC_SUFFIXES
                or ('.' not in name and name not in RESERVED_LABELS)):
            raise Refused('RAC_REMOTE_ALLOWED_HOSTS wildcards may not cover a '
                          f'public suffix: {raw.strip()!r}')
        hosts.add('.' + name if entry.startswith('*.') else name)
    return hosts


def host_allowed(host):
    host = host.lower()
    if host in TEST_HOSTS or any(host.endswith(s) for s in TEST_SUFFIXES):
        return True
    return any(host == entry or (entry.startswith('.') and host.endswith(entry))
               for entry in extra_allowed_hosts())


def internal_page(word):
    """The internal page a chrome:/rac: `word` opens when it is
    allowlisted, else None. Scheme and host are case-insensitive and one
    trailing slash is optional; a query, fragment, '..' or
    percent-escape can never match, since host+path must come out to an
    INTERNAL_PAGES entry or setup/<one segment of [A-Za-z0-9-]>. The one
    query allowed is setup?arc, the Arc import step."""
    match = INTERNAL_URL.fullmatch(word)
    if not match:
        return None
    page = match.group(1)
    if SETUP_ARC.fullmatch(page):
        return 'setup?arc'
    if page.endswith('/'):
        page = page[:-1]
    host, slash, path = page.partition('/')
    page = host.lower() + slash + path
    if page in INTERNAL_PAGES or SETUP_STEP.fullmatch(page):
        return page
    return None


def url_allowed(word, serve=False):
    """True for a URL open-urls (or a run's URL argument) may open: an
    allowlisted internal page, about:blank, http(s) to an allowed host
    and port, or (with `serve`) the run's own file server as
    `@SERVE@/path`. A word holding `@SERVE@` anywhere else is refused,
    so the Pro's substitution can only ever produce that server's URL."""
    if SERVE in word:
        return serve and bool(SERVE_URL.fullmatch(word)) and '..' not in word
    if internal_page(word) is not None or word.lower() == 'about:blank':
        return True
    match = HTTP_URL.fullmatch(word)
    return bool(match) and host_allowed(match.group('host'))


def check_typed(text):
    """Typed text is plain words: ASCII letters, digits, spaces, '-', '_'
    and '!'. With no dot, colon or slash it can't spell a URL, a host name or
    a path, and with no other characters there is nothing to smuggle one
    in with. (Non-ASCII fails the charset too, so the omnibox's
    full-width look-alike mapping stays out.)"""
    if not TYPED_TEXT.fullmatch(text):
        raise Refused('typed text is plain words only: ASCII letters, '
                      'digits, spaces, "-", "_" and "!": ' + repr(text))


def harness_words(request):
    """How the harness splits a request: on single spaces, empty words
    dropped. Python's split() also splits on other whitespace, which the
    harness keeps inside a word."""
    return [word for word in request.split(' ') if word]


def harness_requests(line):
    """How the harness splits a line into requests."""
    if ' ; ' not in line:
        return [line]
    return [r.strip(' ') for r in line.split(' ; ') if r.strip(' ')]


class Checker:

    def __init__(self, serve=False):
        self.serve = serve
        self.outputs = []
        self.verbs = []
        # The ids of the command verbs the line validated, in order.
        self.command_ids = []
        # Every character typed into the focused field, in order: pieces
        # typed one after another can join into a page name.
        self.typed = ''
        # Each input-ish request, in order: 'type' for type/nstype,
        # 'letter' for an unmodified nspress letter (which types too),
        # 'return' for key return, 'wheel' for a scroll, and 'input' for
        # everything else that moves the caret, the pointer or the app.
        # Capture and state verbs record nothing.
        self.events = []
        # A chrome:/rac: settings page the line opens.
        self.settings = False

    def path(self, word, kind='file', png=False):
        if word.startswith(('/', '~')) or '\\' in word:
            raise Refused(f'paths must be relative to build/shots, not {word!r}')
        if not PATH.fullmatch(word):
            raise Refused('paths may only use letters, digits, ".", "_", "-" '
                          f'and "/": {word!r}')
        if any(part in ('', '.', '..') for part in word.split('/')):
            raise Refused(f'paths may not contain empty, "." or ".." parts: {word!r}')
        if png and not word.endswith('.png'):
            raise Refused(f'a screenshot path ends in .png: {word!r}')
        self.outputs.append(f'{kind} {word}')
        return f'{MARK}/{word}'

    def check(self, words, top, after):
        """The checked words of one request. `top` is a request alone on its
        line; `after` one run later by `after`, which skips window verbs."""
        if not words:
            raise Refused('empty request')
        verb, args = words[0], words[1:]
        n = len(args)
        # A bare screenshot path is an output, not a verb.
        if not (n == 0 and verb.endswith('.png')) and verb not in self.verbs:
            self.verbs.append(verb)

        def need(ok, usage):
            if not ok:
                raise Refused(f'{verb} takes: {usage}; got {" ".join(words)!r}')

        def ints(*items):
            return all(INT.fullmatch(item) for item in items)

        def nums(*items):
            return all(NUMBER.fullmatch(item) for item in items)

        def mods(item):
            return item == 'none' or all(m in MODS for m in item.split(','))

        def selector(item):
            return (item in WINDOW_KINDS or re.fullmatch(r'#[0-9]{1,4}', item) or
                    re.fullmatch(r'(app|profile|name):[A-Za-z0-9._-]+', item))

        if verb == 'after':
            need(n >= 2 and re.fullmatch(r'[0-9]{1,9}', args[0]), 'MS REQUEST')
            return [verb, args[0]] + self.check(args[1:], top=False, after=True)
        # Typed text: no paths, and the harness types the rest of the
        # request as it stands. ';' alone would split it in two.
        if verb in ('type', 'nstype'):
            need(n >= 1, 'TEXT')
            if ';' in args:
                raise Refused(f'{verb} text may not hold " ; ": {" ".join(words)!r}')
            check_typed(' '.join(args))
            self.typed += ' '.join(args)
            self.events.append('type')
            return words
        if n == 0 and verb.endswith('.png'):
            if not (top or after):
                raise Refused('a bare PNG path only captures alone on its line or '
                              f'after `after MS`: {verb!r}')
            return [self.path(verb, 'expect', png=True)]
        window_verbs = {'windows', 'target', 'profile-window', 'hit'}
        if verb in window_verbs and after:
            raise Refused(f'`after` can only run input requests, not {verb!r}')
        if verb == 'hit':
            need(top and n == 3 and ints(*args[:2]), 'X Y OUT, alone on its line')
            return [verb, *args[:2], self.path(args[2])]
        if verb == 'windows':
            need(n == 1, 'OUT')
            return [verb, self.path(args[0])]
        # Lists the open menu, or with main:TITLE a main-menu submenu. It
        # runs in HandleInput, so `after MS` may delay it until a click has
        # opened the menu.
        if verb == 'menu-dump':
            need(n == 1 or (n in (2, 3) and re.fullmatch(r'main:[A-Za-z0-9._-]+', args[1])
                            and (n == 2 or args[2] == 'validate')),
                 'OUT [main:TITLE [validate]]')
            return [verb, self.path(args[0]), *args[1:]]
        if verb == 'target':
            need(n == 1 and selector(args[0]), 'SELECTOR')
            return words
        if verb == 'profile-window':
            need(n == 1 and re.fullmatch(r'[A-Za-z0-9_-]+', args[0]), 'FOLDER')
            return words
        if verb == 'record':
            need(n in (2, 3) and ints(args[1]) and int(args[1]) > 0 and
                 (n == 2 or (nums(args[2]) and 0 < float(args[2]) <= 1)),
                 'DIR MS [SCALE]')
            return [verb, self.path(args[0], 'dir'), *args[1:]]
        if verb == 'burst':
            need(n == 3 and ints(*args[1:]) and 0 <= int(args[1]) <= MAX_BURST,
                 f'DIR N MS, N up to {MAX_BURST}')
            marked = self.path(args[0], 'dir')
            # The harness names a burst's frames f%02d.png.
            self.outputs += [f'expect {args[0]}/f{i:02d}.png'
                             for i in range(int(args[1]))]
            return [verb, marked, *args[1:]]
        if verb == 'capture-window':
            need(n == 2 and selector(args[0]), 'SELECTOR OUT')
            return [verb, args[0], self.path(args[1], 'expect', png=True)]
        if verb == 'open-urls':
            need(n >= 1, 'URL...')
            for url in args:
                if SERVE in url and not self.serve:
                    raise Refused(f'{SERVE} URLs need `run --serve DIR`: {url!r}')
                if not url_allowed(url, self.serve):
                    raise Refused('open-urls may open the allowlisted '
                                  'internal pages (chrome://version, '
                                  'chrome://settings/appearance and its '
                                  'kin, chrome://setup, rac://..., '
                                  'about:blank) or http(s) to an allowed '
                                  'host (localhost, 127.0.0.1, [::1], '
                                  'example.*, *.test, *.localhost), or '
                                  f'{SERVE}/<path> with --serve: {url!r}')
                page = internal_page(url)
                # The Air checks pages it opened against the run args: a
                # chrome://setup run needs an Arc import input. A
                # settings page makes the whole run screenshot-only.
                if page is not None:
                    self.outputs.append(f'pages {url}')
                    if (page == 'settings' or page.startswith('settings/')
                            or page == 'credits'):
                        self.settings = True
            return words
        simple = {
            # `command ID [SELECTOR]`: SELECTOR is capture-window's.
            'command': (n == 1 and ints(args[0])) or (
                n == 2 and ints(args[0]) and selector(args[1])),
            'move': n == 2 and ints(*args),
            'click': n == 2 and ints(*args),
            'wheel': n == 3 and ints(*args),
            'key': n == 1 and args[0] in KEYS,
            'nspress': (n in (1, 2) and
                        (re.fullmatch(r'[a-z0-9]', args[0]) or args[0] in NSPRESS_KEYS)
                        and (n == 1 or mods(args[1]))),
            'nskey': (n in (2, 3) and args[0] in ('tab', 'w', 'escape') and
                      args[1] in ('down', 'up') and (n == 2 or mods(args[2]))),
            'nsflags': n == 1 and mods(args[0]),
            'swipe': ((n == 3 and ints(*args[:2]) and args[2] == 'end') or
                      (n in (4, 5) and ints(*args[:2]) and nums(args[2]) and
                       ints(args[3]) and (n == 4 or args[4] == 'hold'))),
            'appearance': n == 1 and args[0] in ('light', 'dark', 'system'),
            'contrast': n == 1 and args[0] in ('on', 'off'),
            # window_state.mm: a preset is `-` or < SpaceTheme::kPresetCount.
            'space-theme': (n in (1, 2) and re.fullmatch(r'-|0*[0-7]', args[0]) and
                            (n == 1 or args[1] in ('auto', 'light', 'dark'))),
            'space-new': n == 0,
            'pointer': (n == 1 and args[0] == 'off') or (n == 2 and nums(*args)),
            'pointer-path': (n == 5 and nums(*args[:4]) and
                             re.fullmatch(r'[0-9]{1,9}', args[4])),
        }
        if verb not in simple:
            raise Refused(f'unknown request verb {verb!r}')
        need(simple[verb], 'other arguments (see window_screenshot.mm)')
        if verb == 'command' and int(args[0]) in COMMANDS_NEED_TEST_TYPE:
            # The Air refuses the run unless it passes --test-type.
            if 'needs --test-type' not in self.outputs:
                self.outputs.append('needs --test-type')
        elif verb == 'command' and int(args[0]) not in COMMANDS_ALLOWED:
            raise Refused(f'command {args[0]} is not an allowed command id '
                          '(see COMMANDS_ALLOWED); ask Ship to allow it')
        if verb == 'command':
            self.command_ids.append(int(args[0]))
        if verb == 'key':
            self.events.append('return' if args[0] == 'return' else 'input')
        elif verb == 'wheel':
            self.events.append('wheel')
        elif verb == 'command' and int(args[0]) in COMMANDS_ZOOM:
            self.events.append('zoom')
        elif verb == 'command' and int(args[0]) == FOCUS_LOCATION:
            self.events.append('focus')
        elif verb in ('click', 'move', 'swipe', 'pointer',
                      'pointer-path', 'nskey', 'nsflags', 'command'):
            self.events.append('input')
        elif verb == 'nspress':
            held = (set() if n == 1 or args[1] == 'none'
                    else set(args[1].split(',')))
            if 'cmd' in held and any(args[0] == key and mods <= held
                                     for key, mods in CMD_CHORDS_DENIED):
                raise Refused(f'nspress {" ".join(args)} opens an internal '
                              'page that is not on the allowlist')
            if len(args[0]) == 1:
                if 'cmd' in held and args[0] in (
                        CMD_SHIFT_DENIED if 'shift' in held else CMD_DENIED):
                    raise Refused(f'nspress {" ".join(args)} reaches a dialog, '
                                  'the clipboard, DevTools or another app')
                if not held - {'shift'}:
                    # An unmodified letter types into the focused field.
                    self.typed += args[0]
                    self.events.append('letter')
                else:
                    self.events.append('input')
            else:
                self.events.append('input')
        return words


def check_line(text, serve=False, command_ids=None):
    """The checked line and the paths it writes, as `file REL`/`dir REL`.
    `serve` says the run passes --serve, so `@SERVE@` URLs may open."""
    # A malformed RAC_REMOTE_ALLOWED_HOSTS refuses every line, not only one
    # whose host would have needed it.
    extra_allowed_hosts()
    lines = text.splitlines()
    if len(lines) != 1 or not lines[0].strip():
        raise Refused('a requests file holds exactly one non-empty line')
    line = lines[0].strip()
    if len(line) > MAX_LINE:
        raise Refused(f'the request line is longer than {MAX_LINE} characters')
    if any(ord(c) < 32 or ord(c) == 127 or (c.isspace() and c != ' ') for c in line):
        raise Refused('the request line has control characters or whitespace '
                      'other than spaces')
    if MARK in line:
        raise Refused(f'the request line may not contain {MARK}')
    pieces = line.split(' ; ')
    checker = Checker(serve)
    checked = [checker.check(harness_words(piece), top=len(pieces) == 1, after=False)
               for piece in pieces]
    out = ' ; '.join(' '.join(words) for words in checked)
    # The harness has to split the line it gets exactly as it was checked.
    if [harness_words(r) for r in harness_requests(out)] != checked:
        raise Refused('the request line splits differently in the browser')
    # A script that types (type/nstype, or unmodified nspress letters)
    # may not also move the caret, the pointer or the app: the text lands
    # wherever focus happens to be, and only the plain-words rule keeps
    # it harmless. With a real type/nstype present even nspress letters
    # are refused. At most one `key return` may follow the last typed
    # piece; the rest stay capture and state verbs.
    events = checker.events
    if 'type' in events or 'letter' in events:
        if ('input' in events or 'wheel' in events or 'zoom' in events or
                ('type' in events and 'letter' in events)):
            raise Refused('a script that types may not move the caret or '
                          'click; ask Ship')
        # A return between typed pieces would submit the first and start
        # a fresh field, so the joined-words check below would miss it.
        last = max(i for i, e in enumerate(events)
                   if e in ('type', 'letter'))
        if events[:last].count('return') or events[last + 1:].count('return') > 1:
            raise Refused('a script that types may press return at most '
                          'once, after its last typed text; ask Ship')
        # A bang only shows suggestions: submitting it would navigate to
        # whatever site the bang names.
        if '!' in checker.typed and 'return' in events:
            raise Refused('typed text with a "!" (a bang) may not be '
                          'submitted: no key return')
    # A run that opens a settings page may only take screenshots and
    # scroll: every other recorded event is an input the settings UI could
    # be walked with. `wheel X Y DY` sends an unmodified scroll (the
    # harness's MouseWheelEvent carries EF_NONE), which only moves the
    # page; nothing can focus a control for it to change.
    # Zoom only changes how the page is drawn, so a settings run may also
    # zoom out to fit a card the window is too short for.
    if checker.settings and any(e not in ('wheel', 'zoom') for e in events):
        raise Refused('a run that opens a settings page may only take '
                      'screenshots, scroll (wheel) and zoom (command '
                      '38001-38003); the script may not send other input')
    # Every placeholder sits at the start of an open-urls word that
    # passed SERVE_URL; nothing else in the line may hold one.
    if line.count(SERVE) != sum(word.startswith(SERVE) and bool(SERVE_URL.fullmatch(word))
                                for words in checked for word in words):
        raise Refused(f'{SERVE} may only start an open-urls URL')
    # The typed words themselves are checked against the denied page
    # names: pieces join in order, and a whole word naming a page the
    # browser may not open edits the open page's URL into it.
    typed_words = {w for w in re.split(r'[\s_!-]+', checker.typed.lower()) if w}
    denied = sorted(typed_words & TYPED_PAGE_TOKENS)
    if denied:
        raise Refused('typed text spells a page the browser may not open: '
                      + ', '.join(denied))
    if command_ids is not None:
        command_ids.extend(sorted(set(checker.command_ids)))
    return out, checker.outputs, sorted(checker.verbs)


def main(argv):
    serve = len(argv) > 1 and argv[1] == '--serve'
    if serve:
        argv = argv[:1] + argv[2:]
    if len(argv) == 3 and argv[1] == '--url':
        try:
            extra_allowed_hosts()
            if url_allowed(argv[2], serve):
                return 0
            print('rac remote: refusing: a run may only open the '
                  'allowlisted internal pages, about:blank, http(s) '
                  'URLs to an allowed host, or @SERVE@/<path> with '
                  f'--serve, not {argv[2]!r}',
                  file=sys.stderr)
        except Refused as e:
            print(f'rac remote: refusing: {e}', file=sys.stderr)
        return 2
    if len(argv) != 2:
        sys.exit(__doc__)
    try:
        with open(argv[1], encoding='utf-8') as f:
            ids = []
            line, outputs, verbs = check_line(f.read(), serve, ids)
    except (Refused, UnicodeDecodeError, OSError) as e:
        print(f'rac remote: refusing the requests file: {e}', file=sys.stderr)
        return 2
    print(line)
    # The Pro checks each verb is a string literal in the clone's own
    # harness sources before it sends the line, without parsing it again.
    print('verbs ' + ' '.join(verbs))
    # The command ids, for a settings page passed as a run arg: such a run
    # may only zoom. The Air strips this line before the Pro sees it.
    if ids:
        print('commands ' + ' '.join(str(i) for i in ids))
    for output in outputs:
        print(output)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
