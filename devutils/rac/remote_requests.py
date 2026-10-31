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

usage: remote_requests.py <file>
       remote_requests.py --url <url>   (exit 0 if a run may open it)

Prints the checked line, a `verbs VERB...` line listing every request
verb it uses (the Pro checks each is a string literal in the clone's own
harness sources, and the Air reads them back: a settings page opened as
a run arg allows no input verb), a `pages URL` line per chrome:/rac:
page open-urls visits (the Air reads them back too: a run that opens
chrome://setup needs an Arc import input in the same run), then one line
per path in it, REL
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
# only these three sub-pages may open, and a run that opens one may take
# screenshots only -- the script may not send input (see check_line).
INTERNAL_PAGES = frozenset((
    'setup', 'version', 'newtab', 'settings/assistant',
    'settings/privacy', 'settings/appearance', 'settings/general', 'rac-ai',
))
INTERNAL_URL = re.compile(r'(?:chrome|rac)://([!-\[\]-~]*)', re.ASCII | re.I)
SETUP_STEP = re.compile(r'setup/[A-Za-z0-9-]+')
# The welcome tour opened straight at its Arc import step. The query must
# be exactly "arc"; only the host's case is free.
SETUP_ARC = re.compile(r'(?i:setup)\?arc')
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
# Typed text is plain words only: ASCII letters, digits, spaces, '-'
# and '_'. Without dots, colons or slashes it can't spell a URL, a host
# name or a path, however the pieces join or whatever submits it.
TYPED_TEXT = re.compile(r'[A-Za-z0-9 _-]+')
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
))


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


def url_allowed(word):
    """True for a URL open-urls (or a run's URL argument) may open: an
    allowlisted internal page, about:blank, or http(s) to an allowed
    host and port."""
    if internal_page(word) is not None or word.lower() == 'about:blank':
        return True
    match = HTTP_URL.fullmatch(word)
    return bool(match) and host_allowed(match.group('host'))


def check_typed(text):
    """Typed text is plain words: ASCII letters, digits, spaces, '-' and
    '_'. With no dot, colon or slash it can't spell a URL, a host name or
    a path, and with no other characters there is nothing to smuggle one
    in with. (Non-ASCII fails the charset too, so the omnibox's
    full-width look-alike mapping stays out.)"""
    if not TYPED_TEXT.fullmatch(text):
        raise Refused('typed text is plain words only: ASCII letters, '
                      'digits, spaces, "-" and "_": ' + repr(text))


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

    def __init__(self):
        self.outputs = []
        self.verbs = []
        # Every character typed into the focused field, in order: pieces
        # typed one after another can join into a page name.
        self.typed = ''
        # Each input-ish request, in order: 'type' for type/nstype,
        # 'letter' for an unmodified nspress letter (which types too),
        # 'return' for key return, and 'input' for everything else that
        # moves the caret, the pointer or the app. Capture and state
        # verbs record nothing.
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
                if not url_allowed(url):
                    raise Refused('open-urls may open the allowlisted '
                                  'internal pages (chrome://version, '
                                  'chrome://settings/appearance and its '
                                  'kin, chrome://setup, rac://..., '
                                  'about:blank) or http(s) to an allowed '
                                  'host (localhost, 127.0.0.1, [::1], '
                                  f'example.*, *.test, *.localhost): {url!r}')
                page = internal_page(url)
                # The Air checks pages it opened against the run args: a
                # chrome://setup run needs an Arc import input. A
                # settings page makes the whole run screenshot-only.
                if page is not None:
                    self.outputs.append(f'pages {url}')
                    if page == 'settings' or page.startswith('settings/'):
                        self.settings = True
            return words
        simple = {
            'command': n == 1 and ints(*args),
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
        if verb == 'command' and int(args[0]) not in COMMANDS_ALLOWED:
            raise Refused(f'command {args[0]} is not an allowed command id '
                          '(see COMMANDS_ALLOWED); ask Ship to allow it')
        if verb == 'key':
            self.events.append('return' if args[0] == 'return' else 'input')
        elif verb in ('click', 'move', 'swipe', 'wheel', 'pointer',
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


def check_line(text):
    """The checked line and the paths it writes, as `file REL`/`dir REL`."""
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
    checker = Checker()
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
        if 'input' in events or ('type' in events and 'letter' in events):
            raise Refused('a script that types may not move the caret or '
                          'click; ask Ship')
        # A return between typed pieces would submit the first and start
        # a fresh field, so the joined-words check below would miss it.
        last = max(i for i, e in enumerate(events)
                   if e in ('type', 'letter'))
        if events[:last].count('return') or events[last + 1:].count('return') > 1:
            raise Refused('a script that types may press return at most '
                          'once, after its last typed text; ask Ship')
    # A run that opens a settings page may only take screenshots: every
    # recorded event is an input the settings UI could be walked with.
    if checker.settings and events:
        raise Refused('a run that opens a settings page may only take '
                      'screenshots; the script may not send input')
    # The typed words themselves are checked against the denied page
    # names: pieces join in order, and a whole word naming a page the
    # browser may not open edits the open page's URL into it.
    typed_words = {w for w in re.split(r'[\s_-]+', checker.typed.lower()) if w}
    denied = sorted(typed_words & TYPED_PAGE_TOKENS)
    if denied:
        raise Refused('typed text spells a page the browser may not open: '
                      + ', '.join(denied))
    return out, checker.outputs, sorted(checker.verbs)


def main(argv):
    if len(argv) == 3 and argv[1] == '--url':
        try:
            extra_allowed_hosts()
            if url_allowed(argv[2]):
                return 0
            print('rac remote: refusing: a run may only open the '
                  'allowlisted internal pages, about:blank or http(s) '
                  f'URLs to an allowed host, not {argv[2]!r}',
                  file=sys.stderr)
        except Refused as e:
            print(f'rac remote: refusing: {e}', file=sys.stderr)
        return 2
    if len(argv) != 2:
        sys.exit(__doc__)
    try:
        with open(argv[1], encoding='utf-8') as f:
            line, outputs, verbs = check_line(f.read())
    except (Refused, UnicodeDecodeError, OSError) as e:
        print(f'rac remote: refusing the requests file: {e}', file=sys.stderr)
        return 2
    print(line)
    # The Pro checks each verb is a string literal in the clone's own
    # harness sources before it sends the line, without parsing it again.
    print('verbs ' + ' '.join(verbs))
    for output in outputs:
        print(output)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
