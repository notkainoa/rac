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

Prints the checked line, then one line per path in it, REL under
build/shots/, so the Pro side never has to parse the line: `file REL` (a
file it writes), `dir REL` (a folder it writes into) or `expect REL` (a
screenshot the run waits for: bare PNG paths, capture-window's OUT, and
each of a burst's DIR/fNN.png frames). Exits 2 on a refusal.
"""

import re
import sys

MARK = '@SHOTS@'
MAX_LINE = 4096
# The harness turns a burst's N into N tasks at once.
MAX_BURST = 1000
INT = re.compile(r'-?[0-9]{1,9}')
NUMBER = re.compile(r'-?[0-9]{1,9}(\.[0-9]{1,6})?')
PATH = re.compile(r'[A-Za-z0-9._/-]+')
# A data: URL that the page can't show downloads, and downloads land in the
# Pro's own Downloads folder, outside the clone.
SAFE_SCHEMES = {'http', 'https', 'chrome', 'rac', 'about'}
URL = re.compile(r'([A-Za-z][A-Za-z0-9+.-]*):[!-~]+')
MODS = {'ctrl', 'shift', 'cmd', 'alt'}
WINDOW_KINDS = {'first', 'normal', 'incognito', 'app', 'popup', 'devtools',
                'pip', 'browser', 'onboarding', 'child', 'other'}
KEYS = {'return', 'escape', 'tab', 'backspace', 'up', 'down', 'left', 'right'}
NSPRESS_KEYS = KEYS | {'space', 'home', 'end', 'pageup', 'pagedown'}


class Refused(Exception):
    pass


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
                match = URL.fullmatch(url)
                if not match or match.group(1).lower() not in SAFE_SCHEMES:
                    raise Refused('open-urls takes http, https, chrome, rac and '
                                  f'about URLs only: {url!r}')
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
            'space-theme': (n in (1, 2) and re.fullmatch(r'-|[0-9]{1,3}', args[0]) and
                            (n == 1 or args[1] in ('auto', 'light', 'dark'))),
            'space-new': n == 0,
            'pointer': (n == 1 and args[0] == 'off') or (n == 2 and nums(*args)),
            'pointer-path': (n == 5 and nums(*args[:4]) and
                             re.fullmatch(r'[0-9]{1,9}', args[4])),
        }
        if verb not in simple:
            raise Refused(f'unknown request verb {verb!r}')
        need(simple[verb], 'other arguments (see window_screenshot.mm)')
        return words


def check_line(text):
    """The checked line and the paths it writes, as `file REL`/`dir REL`."""
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
    return out, checker.outputs


def main(argv):
    if len(argv) != 2:
        sys.exit(__doc__)
    try:
        with open(argv[1], encoding='utf-8') as f:
            line, outputs = check_line(f.read())
    except (Refused, UnicodeDecodeError, OSError) as e:
        print(f'rac remote: refusing the requests file: {e}', file=sys.stderr)
        return 2
    print(line)
    for output in outputs:
        print(output)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
