#!/usr/bin/env python3

# Copyright 2026 The rac Authors
# You can use, redistribute, and/or modify this source code under
# the terms of the GPL-3.0 license that can be found in the LICENSE file.
"""Makes a scrubbed copy of an Arc sidebar for rac's import tests.

The maintainer runs this on their own Arc. Agents never read the original.
The copy keeps Arc's JSON shape, ids, numbers, colors, and emoji, so the
importer can be tested against a real layout. Every title becomes
"Title <n>", every URL "https://example.com/<n>", and any other text
"s<n>". The same original always gets the same placeholder, so duplicates
stay duplicates.

A string is kept only when it is provably harmless: a UUID, a "#rrggbb"
color, a single emoji, a profile folder name such as "Profile 1", or one of a
fixed list of Arc's enum words such as "pinned". Strings that merely look
like numbers are replaced, since phone numbers and IP addresses look like
numbers too. JSON numbers (dates, colors, sizes) are kept.

Object keys that look like field names are kept. Any kept key that is not one
of Arc's known field names, every kept word, and every kept emoji is listed
in SCRUB_REPORT.txt, so the output can be checked in a minute before it is
shared or committed.

Read, never written: StorableSidebar.json, StorableLinkRouting.json, the
names of the files in SidebarItemsFaviconCache (not their contents),
"extensions.pinned_extensions" in each "User Data/<profile>/Preferences", and
which profile folders have a name in "User Data/Local State" (the names
themselves become placeholders).
Never read: cookies, passwords, history, the Keychain, or anything else.

The output folder is laid out like Arc's, so rac's dev switch
--rac-import-source-root=<out> can read it. It is written to a temporary
folder next to --out and renamed into place only when everything succeeded.
--arc-dir has no default, so the script never reads real data by accident.

usage: arc_scrub.py --arc-dir <Arc folder> --out <new folder>
"""

from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile

DEFAULT_ARC_DIR = Path.home() / 'Library' / 'Application Support' / 'Arc'
SIDEBAR = 'StorableSidebar.json'
ROUTING = 'StorableLinkRouting.json'
FAVICONS = 'SidebarItemsFaviconCache'
USER_DATA = 'User Data'
REPORT = 'SCRUB_REPORT.txt'

# Keys whose string values are always free text, whatever they look like.
TEXT_KEYS = {
    'title', 'savedTitle', 'name', 'displayName', 'text', 'label', 'query',
    'searchQuery', 'note', 'notes', 'description', 'subtitle', 'username',
    'email', 'path', 'filePath', 'fileName',
}
URL_KEYS = {'savedURL', 'url', 'URL', 'urlString', 'originalURL', 'href'}

# The only word values kept. Arc stores most enums as keys; these few appear
# as values, e.g. containerIDs ["pinned", id, "unpinned", id]. Any other word
# could be something the user typed, so it is replaced.
KNOWN_TOKENS = frozenset({
    'pinned', 'unpinned', 'today', 'favorites', 'topApps', 'auto', 'manual',
    'light', 'dark', 'system', 'default', 'custom', 'mostRecent', 'littleArc',
    'space', 'tab', 'list', 'none',
})

# Arc field names the importer reads. Kept keys outside this set are listed
# in the report, because a key can also be user data in a map.
KNOWN_KEYS = frozenset({
    'sidebar', 'containers', 'spaces', 'items', 'global', 'version', 'id',
    'parentID', 'childrenIds', 'title', 'createdAt', 'data', 'tab',
    'savedURL', 'savedTitle', 'list', 'splitView', 'tabGroup',
    'itemContainer', 'containerType', 'topApps', 'spaceItems',
    'containerIDs', 'profile', 'default', 'custom', 'directoryBasename',
    'customInfo', 'iconType', 'emoji', 'emoji_v2', 'windowTheme',
    'background', 'appearanceBased', 'light', 'dark', 'single', 'style',
    'color', 'blendedGradient', 'baseColors', 'overlayColors', 'modifiers',
    'intensityFactor', 'noiseFactor', 'isVibrant',
    'contentOverBackgroundAppearance', 'red', 'green', 'blue', 'alpha',
    'defaultDestination', 'rules', 'sourceComponents', 'componentType',
    'urlMatch', 'contains', 'matches', 'destination', 'space', 'mostRecent',
    'littleArc', 'extensions', 'pinned_extensions',
})

UUID_RE = re.compile(r'[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-'
                     r'[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}')
HEX_COLOR_RE = re.compile(r'#(?:[0-9A-Fa-f]{6}|[0-9A-Fa-f]{8})')
PROFILE_DIR_RE = re.compile(r'(?:Default|Profile [0-9]{1,4})')
KEY_RE = re.compile(r'[A-Za-z_][A-Za-z0-9_]{0,63}')
ENUM_PAYLOAD_KEY_RE = re.compile(r'_[0-9]{1,2}')
URL_LIKE_RE = re.compile(r'(?:[A-Za-z][A-Za-z0-9+.\-]*://|'
                         r'(?:javascript|data|mailto|about):|www\.|'
                         r'[^\s/]+\.[A-Za-z]{2,}(?:[/:?#]|$)).*', re.S)
# Non-web schemes whose name is kept, so the importer sees the same kind of
# link. Everything else becomes https://example.com/<n>.
KEPT_SCHEMES = ('file', 'chrome', 'arc', 'about', 'data', 'javascript',
                'mailto', 'chrome-extension')
EXTENSION_ID_RE = re.compile(r'[a-p]{32}')
# A 1x1 transparent PNG, standing in for each cached favicon.
PLACEHOLDER_PNG = bytes.fromhex(
    '89504e470d0a1a0a0000000d4948445200000001000000010806000000'
    '1f15c4890000000d49444154789c63000100000500010d0a2db40000000049454e44ae426082')

# Code point ranges that are pictographs. Letter-like symbols (braille,
# enclosed letters, circled digits) are left out, since they can spell words.
_PICTOGRAPH_RANGES = (
    (0x1F300, 0x1F5FF), (0x1F600, 0x1F64F), (0x1F680, 0x1F6FF),
    (0x1F7E0, 0x1F7EB), (0x1F90C, 0x1F9FF), (0x1FA70, 0x1FAFF),
    (0x2600, 0x2775), (0x2794, 0x27BF), (0x2300, 0x23FF), (0x2190, 0x21FF), (0x2B05, 0x2B55),
    (0x1F004, 0x1F004), (0x1F0CF, 0x1F0CF), (0x1F18E, 0x1F18E),
    (0x1F191, 0x1F19A), (0x1F201, 0x1F251),
)
_PICTOGRAPH_SINGLES = frozenset({
    0x00A9, 0x00AE, 0x203C, 0x2049, 0x2122, 0x2139, 0x24C2, 0x25AA, 0x25AB,
    0x25B6, 0x25C0, 0x25FB, 0x25FC, 0x25FD, 0x25FE, 0x2934, 0x2935, 0x3030,
    0x303D, 0x3297, 0x3299, 0x1F170, 0x1F171, 0x1F17E, 0x1F17F,
})
_ZWJ = 0x200D
_VS16 = 0xFE0F
_SKIN_TONES = range(0x1F3FB, 0x1F400)
_SUBDIVISION_FLAGS = frozenset(
    '\U0001F3F4' + ''.join(chr(0xE0000 + ord(c)) for c in tag) + '\U000E007F'
    for tag in ('gbeng', 'gbsct', 'gbwls'))
_KEYCAP_RE = re.compile('[0-9#*]\uFE0F?\u20E3')


def _is_pictograph(cp):
    if cp in _PICTOGRAPH_SINGLES:
        return True
    return any(lo <= cp <= hi for lo, hi in _PICTOGRAPH_RANGES)


def is_emoji(value):
    """True for one emoji: a pictograph sequence, a flag, or a keycap."""
    if not value or len(value) > 12:
        return False
    if value in _SUBDIVISION_FLAGS or _KEYCAP_RE.fullmatch(value):
        return True
    cps = [ord(c) for c in value]
    if len(cps) == 2 and all(0x1F1E6 <= cp <= 0x1F1FF for cp in cps):
        return True  # One country flag: two regional indicators.
    # One ZWJ sequence: pictographs joined by single ZWJs. Each pictograph may
    # carry one skin tone and then one VS16, and nothing else.
    i = 0
    while True:
        if i >= len(cps) or not _is_pictograph(cps[i]):
            return False
        i += 1
        if i < len(cps) and cps[i] in _SKIN_TONES:
            i += 1
        if i < len(cps) and cps[i] == _VS16:
            i += 1
        if i == len(cps):
            return True
        if cps[i] != _ZWJ:
            return False
        i += 1


class ScrubError(Exception):
    """A problem worth a short message. Never includes user data."""


class Scrubber:
    """Replaces free text with stable placeholders and records what it kept."""

    def __init__(self):
        self._placeholders = {}
        self._counts = {'title': 0, 'url': 0, 'text': 0, 'ext': 0, 'key': 0}
        self.kept_words = {}
        self.kept_emoji = {}
        self.unknown_keys = set()
        self.ids = set()
        self.warnings = []
        self.replaced = 0

    def _placeholder(self, kind, original):
        key = (kind, original)
        if key not in self._placeholders:
            self._counts[kind] += 1
            n = self._counts[kind]
            if kind == 'title':
                value = f'Title {n}'
            elif kind == 'text':
                value = f's{n}'
            elif kind == 'key':
                # "~" never appears in a field name, so this can't collide
                # with a key that was kept.
                value = f'k~{n}'
            elif kind == 'ext':
                # A fake id in Chromium's extension-id alphabet.
                digest = hashlib.sha256(f'ext{n}'.encode()).hexdigest()
                value = ''.join(chr(ord('a') + int(c, 16)) for c in digest[:32])
            else:
                value = self._url_placeholder(n, original)
            self._placeholders[key] = value
        self.replaced += 1
        return self._placeholders[key]

    @staticmethod
    def _url_placeholder(n, original):
        scheme = original.split(':', 1)[0].lower() if ':' in original else ''
        if scheme not in KEPT_SCHEMES:
            return f'https://example.com/{n}'
        if scheme in ('javascript', 'data', 'mailto', 'about'):
            return f'{scheme}:placeholder-{n}'
        return f'{scheme}://placeholder/{n}'

    def string(self, value, key, match_text=False):
        if value == '':
            return value
        if key in URL_KEYS:
            return self._placeholder('url', value)
        if key in TEXT_KEYS:
            return self._placeholder('title', value)
        if match_text and not UUID_RE.fullmatch(value):
            return self._placeholder('text', value)
        if UUID_RE.fullmatch(value):
            self.ids.add(value)
            return value
        if HEX_COLOR_RE.fullmatch(value):
            return value
        if is_emoji(value):
            self.kept_emoji[value] = self.kept_emoji.get(value, 0) + 1
            return value
        if value in KNOWN_TOKENS or PROFILE_DIR_RE.fullmatch(value):
            self.kept_words[value] = self.kept_words.get(value, 0) + 1
            return value
        if URL_LIKE_RE.match(value):
            return self._placeholder('url', value)
        return self._placeholder('text', value)

    def key(self, name):
        """Keeps field-like keys; replaces keys that look like user data."""
        if UUID_RE.fullmatch(name):
            self.ids.add(name)
            return name
        if (ENUM_PAYLOAD_KEY_RE.fullmatch(name) or name in KNOWN_KEYS
                or PROFILE_DIR_RE.fullmatch(name)):
            return name
        if KEY_RE.fullmatch(name):
            self.unknown_keys.add(name)
            return name
        return self._placeholder('key', name)

    def walk(self, node, key=None, routing=False, match_text=False, depth=0):
        """`routing` is set for StorableLinkRouting.json. There, every string
        under a rule's "sourceComponents" is the user's match text."""
        if depth > 200:
            raise ScrubError('the JSON is nested more than 200 levels deep')
        if isinstance(node, dict):
            out = {}
            for k, v in node.items():
                new_key = self.key(k)
                if new_key in out:
                    raise ScrubError('two keys in one object would collide')
                inner = match_text or (routing and k == 'sourceComponents')
                out[new_key] = self.walk(v, k, routing, inner, depth + 1)
            return out
        if isinstance(node, list):
            # Lists inherit their parent's key, so a list of titles or URLs
            # under a text key is still treated as text.
            return [
                self.walk(v, key, routing, match_text, depth + 1)
                for v in node
            ]
        if isinstance(node, str):
            return self.string(node, key, match_text)
        if (isinstance(node, (int, float)) and not isinstance(node, bool)
                and (key in TEXT_KEYS or key in URL_KEYS or match_text)):
            # A number where text belongs could be anything the user typed.
            return self._placeholder('text', str(node))
        return node

    def extension_id(self, value):
        if isinstance(value, str) and EXTENSION_ID_RE.fullmatch(value):
            return self._placeholder('ext', value)
        return self._placeholder('text', str(value))

    def favicon_names(self):
        """md5(id) for every id seen, which is how Arc names its icons."""
        return {hashlib.md5(i.encode('utf-8')).hexdigest() for i in self.ids}

    def report(self):
        c = self._counts
        lines = [
            'Scrub report. Check this before sharing or committing the folder.',
            '',
            f'Strings replaced: {self.replaced}',
            f'Distinct titles: {c["title"]}, URLs: {c["url"]}, other text: '
            f'{c["text"]}, keys: {c["key"]}, extension ids: {c["ext"]}',
            '',
            'Kept without listing: UUIDs, "#rrggbb" colors, and JSON numbers',
            '(including when items were created).',
            '',
            'Everything else that was kept is below. If any of it looks',
            'private, do not share the folder; say which line.',
            '',
            'Words:',
        ]
        lines += [f'  {n:6d}  {w}' for w, n in sorted(self.kept_words.items())]
        lines += ['', 'Emoji:']
        lines += [f'  {n:6d}  {e}' for e, n in sorted(self.kept_emoji.items())]
        if self.warnings:
            lines[2:2] = ['Warnings:', *[f'  {w}' for w in self.warnings], '']
        lines += ['', 'Field names not on the known list:']
        lines += [f'  {k}' for k in sorted(self.unknown_keys)]
        return '\n'.join(lines) + '\n'


def read_json(path):
    try:
        with open(path, 'rb') as f:
            return json.loads(f.read().decode('utf-8-sig'))
    except (UnicodeDecodeError, ValueError) as e:
        raise ScrubError(f'{path.name} is not valid JSON '
                         f'({type(e).__name__})') from None


def write_private(path, data):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'wb') as f:
        f.write(data)


def write_json(path, value):
    try:
        text = json.dumps(value, ensure_ascii=False, indent=1, allow_nan=False)
    except ValueError:
        raise ScrubError(f'{path.name} holds NaN or Infinity') from None
    write_private(path, (text + '\n').encode('utf-8'))


def _same_dir(a, b):
    try:
        sa, sb = os.stat(a), os.stat(b)
    except OSError:
        return False
    return (sa.st_dev, sa.st_ino) == (sb.st_dev, sb.st_ino)


def _existing_ancestors(path):
    """`path` and its parents that exist. `path` is already resolved, so
    symlinks and ".." are followed; comparing by inode then also catches a
    different capitalization of the Arc folder."""
    return [p for p in [path, *path.parents] if p.exists()]


def check_out_dir(arc_dir, out_dir):
    """`arc_dir` and `out_dir` must already be resolved."""
    for p in _existing_ancestors(out_dir):
        if _same_dir(p, arc_dir):
            raise ScrubError('--out must not be inside the Arc folder.')
    for p in _existing_ancestors(arc_dir):
        if _same_dir(p, out_dir):
            raise ScrubError('--out must not contain the Arc folder.')
    if out_dir.exists() and (not out_dir.is_dir() or any(out_dir.iterdir())):
        raise ScrubError(f'{out_dir} already exists. Pick a new folder.')


def scrub_into(arc_dir, dest):
    """Writes the scrubbed copy into `dest` and returns the Scrubber."""
    scrubber = Scrubber()
    write_json(dest / SIDEBAR, scrubber.walk(read_json(arc_dir / SIDEBAR)))

    routing_path = arc_dir / ROUTING
    if routing_path.is_file():
        routing = scrubber.walk(read_json(routing_path), routing=True)
        write_json(dest / ROUTING, routing)

    # Arc names each icon md5(item id). Keep only names that match an id in
    # the sidebar, so a name can't be the hash of anything else, and never
    # copy the icons themselves.
    favicons = arc_dir / FAVICONS
    if favicons.is_dir():
        wanted = scrubber.favicon_names()
        for entry in sorted(favicons.iterdir()):
            if entry.name in wanted and entry.is_file():
                write_private(dest / FAVICONS / entry.name, PLACEHOLDER_PNG)

    # Only the pinned extension list, from each profile's Preferences.
    user_data = arc_dir / USER_DATA
    if user_data.is_dir():
        for profile in sorted(user_data.iterdir()):
            prefs = profile / 'Preferences'
            if not (PROFILE_DIR_RE.fullmatch(profile.name) and prefs.is_file()):
                continue
            try:
                pinned = read_json(prefs)['extensions']['pinned_extensions']
            except KeyError:
                pinned = []
            except (ScrubError, TypeError):
                pinned = None
            if not isinstance(pinned, list):
                scrubber.warnings.append(
                    f'Could not read pinned extensions in "{profile.name}". '
                    'The copy shows none. Quit Arc and run again.')
                pinned = []
            value = {
                'extensions': {
                    'pinned_extensions':
                    [scrubber.extension_id(e) for e in pinned]
                }
            }
            write_json(dest / USER_DATA / profile.name / 'Preferences', value)

    # Only whether each Arc profile has a name, from Local State. The names
    # become placeholders; nothing else in the file is copied.
    local_state = user_data / 'Local State'
    if local_state.is_file():
        try:
            cache = read_json(local_state)['profile']['info_cache']
        except (ScrubError, KeyError, TypeError):
            cache = None
        if isinstance(cache, dict):
            names = {}
            for folder, info in sorted(cache.items()):
                if not PROFILE_DIR_RE.fullmatch(folder):
                    continue
                name = info.get('name') if isinstance(info, dict) else None
                names[folder] = ({
                    'name': scrubber.string(name, 'name')
                } if isinstance(name, str) else {})
            write_json(dest / USER_DATA / 'Local State',
                       {'profile': {
                           'info_cache': names
                       }})
        else:
            scrubber.warnings.append(
                'Could not read profile names in "Local State". The copy '
                'leaves them out.')

    write_private(dest / REPORT, scrubber.report().encode('utf-8'))
    return scrubber


def scrub(arc_dir, out_dir):
    if not (arc_dir / SIDEBAR).is_file():
        raise ScrubError(f'no {SIDEBAR} in {arc_dir}. Is Arc installed for '
                         'this macOS user?')
    arc_dir, out_dir = arc_dir.resolve(), out_dir.resolve()
    check_out_dir(arc_dir, out_dir)
    parent = out_dir.parent
    parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix='.arc-scrub-', dir=parent))
    try:
        scrubber = scrub_into(arc_dir, staging)
        if out_dir.exists():
            out_dir.rmdir()  # Empty, checked above.
        os.rename(staging, out_dir)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return scrubber


def main(argv=None):
    parser = argparse.ArgumentParser(
        description='Make a scrubbed copy of an Arc sidebar for rac tests.')
    parser.add_argument('--out',
                        type=Path,
                        required=True,
                        help='a new folder for the scrubbed copy')
    # Required, never defaulted, so nothing reads real Arc data by accident.
    parser.add_argument('--arc-dir',
                        type=Path,
                        required=True,
                        help=f'Arc folder, usually "{DEFAULT_ARC_DIR}"')
    args = parser.parse_args(argv)
    try:
        scrubber = scrub(args.arc_dir, args.out)
    except ScrubError as e:
        sys.exit(f'arc_scrub: {e}')
    except RecursionError:
        sys.exit('arc_scrub: the JSON is nested too deeply.')
    except OSError as e:
        sys.exit(f'arc_scrub: {e.strerror or type(e).__name__}. If this is '
                 '"Operation not permitted", give your terminal app Full Disk '
                 'Access in System Settings, then run again.')
    print(f'Wrote {args.out}')
    print(f'Replaced {scrubber.replaced} strings.')
    print(f'Now read {args.out / REPORT} and check what was kept.')


if __name__ == '__main__':
    main()
