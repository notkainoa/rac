#!/usr/bin/env python3

# Copyright 2026 The rac Authors
# You can use, redistribute, and/or modify this source code under
# the terms of the GPL-3.0 license that can be found in the LICENSE file.
"""Applies rac's patches to a sparse Chromium tree and counts the patch surface.

CI runs this on Linux for every pull request, so a patch that no longer applies
cleanly is caught before a build. It works on only the Chromium files that the
patches touch, so it needs no full checkout:

    files    lists the files the patches modify (to know what to extract)
    extract  pulls those files out of the downloads the build unpacks
             (Chromium's source archive, Helium's onboarding page, and so on)
    apply    applies Helium's, then helium-macos's, then rac's patches in
             series order and prints the patch-surface numbers

Apply uses GNU patch, with no fuzz for rac's patches. Any failed hunk or any
hunk applied with fuzz fails the run; offsets are fine. The patch surface is
counted in net-diff hunks in upstream files: the hunks of the diff between the
tree after Helium's patches and the tree after rac's, so a final edit counts
once however many patches stack on it.

Layers, in the order the build applies them (patches/series after Helium's):
    helium    Helium core's patches (helium-chromium/patches/series)
    platform  helium-macos's own patches (patches/series, outside rac/)
    rac       rac's patches (patches/series lines starting with rac/)

Run from the repository root:
    python3 -I devutils/rac/patch_surface.py --help
"""

from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
import argparse
import configparser
import filecmp
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.request
import zipfile

HELIUM, PLATFORM, RAC = 'helium', 'platform', 'rac'
LAYER_TITLES = {HELIUM: 'Helium core', PLATFORM: 'helium-macos', RAC: 'rac'}

HUNK_HEADER = re.compile(r'^@@ -\d+(?:,(\d+))? \+\d+(?:,(\d+))? @@')


class SurfaceError(Exception):
    """A problem with the inputs, not with the patches."""


# Series and patch files


def read_series(path):
    """The entries of a quilt series file, without blank lines and comments."""
    entries = []
    try:
        lines = Path(path).read_text(encoding='utf-8').split('\n')
    except OSError as error:
        raise SurfaceError(f'cannot read the series file: {error}') from error
    for line in lines:
        if not line.strip() or line.startswith('#'):
            continue
        entries.append(line.strip().split(' #')[0])
    return entries


@dataclass
class PatchRef:
    layer: str
    name: str
    path: Path

    @property
    def group(self):
        """patches/rac/<group>/<name>.patch belongs to <group>."""
        parts = self.name.split('/')
        return parts[1] if self.layer == RAC and len(parts) > 2 else '(none)'


def build_plan(helium_patches, platform_patches):
    """Every patch in the order the build applies it. Raises on a bad series."""
    helium_patches, platform_patches = Path(helium_patches), Path(platform_patches)
    plan, problems, seen = [], [], {}
    sources = [(helium_patches, read_series(helium_patches / 'series'), None),
               (platform_patches, read_series(platform_patches / 'series'), PLATFORM)]
    for root, entries, layer in sources:
        for name in entries:
            this_layer = layer or HELIUM
            if layer == PLATFORM and name.startswith('rac/'):
                this_layer = RAC
            if name in seen:
                problems.append(f'{name} is listed twice ({seen[name]} and {root})')
                continue
            seen[name] = root
            path = root / name
            if not path.is_file():
                problems.append(f'{name} is in {root / "series"} but the file is missing')
            plan.append(PatchRef(this_layer, name, path))
    first_rac = next((i for i, ref in enumerate(plan) if ref.layer == RAC), len(plan))
    for ref in plan[first_rac:]:
        if ref.layer != RAC:
            problems.append(f'{ref.name} comes after rac/ patches, but rac must be last')
    if problems:
        raise SurfaceError('bad patch series:\n  ' + '\n  '.join(problems))
    return plan


@dataclass
class FilePatch:
    """One file's part of a patch. Names are relative to the tree (-p1)."""
    old: str
    new: str
    hunks: int = 0


def _strip_name(raw):
    name = raw.split('\t')[0].strip()
    if name == '/dev/null':
        return None
    if name.startswith('"') and name.endswith('"'):
        name = name[1:-1]
    return name.split('/', 1)[1] if '/' in name else name


def parse_patch(text):
    """The files in a unified diff and how many hunks each has (patch -p1)."""
    lines = text.split('\n')
    files, i = [], 0
    while i < len(lines):
        if not (lines[i].startswith('--- ') and i + 1 < len(lines)
                and lines[i + 1].startswith('+++ ')):
            i += 1
            continue
        current = FilePatch(_strip_name(lines[i][4:]), _strip_name(lines[i + 1][4:]))
        i += 2
        while i < len(lines):
            header = HUNK_HEADER.match(lines[i])
            if not header:
                break
            old_left = 1 if header.group(1) is None else int(header.group(1))
            new_left = 1 if header.group(2) is None else int(header.group(2))
            i += 1
            # Count the body by its header, since a removed line that starts
            # with "-- " looks just like the next file's "--- " line.
            while i < len(lines) and (old_left > 0 or new_left > 0):
                kind = lines[i][:1]
                if kind == '-':
                    old_left -= 1
                elif kind == '+':
                    new_left -= 1
                elif kind != '\\':
                    old_left -= 1
                    new_left -= 1
                i += 1
            while i < len(lines) and lines[i].startswith('\\'):
                i += 1
            current.hunks += 1
        files.append(current)
    return files


def read_patch(path):
    return parse_patch(Path(path).read_bytes().decode('utf-8', errors='surrogateescape'))


def resolve_target(tree, file_patch):
    """(path patch will edit, whether it exists now). Path is None if missing."""
    for candidate in (file_patch.old, file_patch.new):
        if candidate and (Path(tree) / candidate).is_file():
            return candidate, True
    if file_patch.old is None:
        return file_patch.new, False
    return None, False


def upstream_paths(plan):
    """Sorted paths the patches modify or delete that no earlier patch creates:
    what the downloads have to supply."""
    paths, created = set(), set()
    for ref in plan:
        for file_patch in read_patch(ref.path):
            for name in {file_patch.old, file_patch.new} - {None} - created:
                if file_patch.old is not None:
                    paths.add(name)
            if file_patch.old is None:
                created.add(file_patch.new)
            elif file_patch.new is None:
                created.discard(file_patch.old)
    return sorted(paths)


# Getting the pristine files


@dataclass
class Source:
    """One download that the build unpacks into the Chromium tree."""
    name: str
    url: str
    filename: str
    output: str  # folder in the tree, '' for the root
    prefix: str  # leading folder inside the archive to drop
    hashes: dict  # algorithm -> hex digest
    hash_url: str = ''

    def tree_path(self, member):
        """Where an archive member lands in the tree, or None if it is outside."""
        parts = [part for part in member.split('/') if part not in ('', '.')]
        if '..' in parts:
            return None
        prefix = [part for part in self.prefix.split('/') if part]
        if parts[:len(prefix)] != prefix:
            return None
        parts = [part for part in self.output.split('/') if part] + parts[len(prefix):]
        return '/'.join(parts)


def load_sources(ini_paths, version):
    """The downloads in Helium's and rac's .ini files, as the build reads them."""
    sources = []
    for ini_path in ini_paths:
        config = configparser.ConfigParser(defaults={'_chromium_version': version})
        if not config.read(ini_path, encoding='utf-8'):
            raise SurfaceError(f'cannot read {ini_path}')
        for name in config.sections():
            section = config[name]
            hashes = {a: section[a] for a in ('sha256', 'sha512') if section.get(a)}
            spec = section.get('hash_url')
            sources.append(
                Source(name=name, url=section['url'], filename=section['download_filename'],
                       output='/'.join(p for p in section.get('output_path', '').split('/')
                                       if p not in ('', '.')),
                       prefix=(section.get('strip_leading_dirs') or '').strip('/'),
                       hashes=hashes, hash_url=spec.split('|')[2] if spec else ''))
    return sources


def parse_hashes(text, filename):
    """The SHA-256 for filename from a Chromium ".hashes" file."""
    for line in text.splitlines():
        fields = line.split()
        if len(fields) == 3 and fields[0] == 'sha256' and fields[2] == filename:
            return fields[1]
    return None


def claim_paths(sources, wanted):
    """Splits wanted paths among the sources by the folder each unpacks into."""
    claims = {source.name: set() for source in sources}
    for path in wanted:
        owners = [s for s in sources if not s.output or path.startswith(s.output + '/')]
        if owners:
            claims[max(owners, key=lambda s: len(s.output)).name].add(path)
    return claims


def file_digest(path, algorithm):
    digest = hashlib.new(algorithm)
    with open(path, 'rb') as source:
        while chunk := source.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def verify_download(path, source):
    """Checks the file against the hash the .ini file gives. Raises if none."""
    hashes = dict(source.hashes)
    if not hashes and source.hash_url:
        expected = parse_hashes(fetch_text(source.hash_url), source.filename)
        if expected:
            hashes['sha256'] = expected
    if not hashes:
        raise SurfaceError(f'no hash for {source.name}; refusing to trust the download')
    for algorithm, expected in hashes.items():
        actual = file_digest(path, algorithm)
        if actual != expected:
            raise SurfaceError(f'{path} has {algorithm} {actual}, expected {expected}')


def extract_tar(fileobj, wanted, source, out_dir, mode='r|*'):
    """Writes the wanted files from a tar stream to out_dir.

    Only regular files named in wanted are written, each where the build would
    put it. Nothing else in the archive is touched, whatever it says. Returns
    the paths found. The caller checks the archive's hash.
    """
    out_dir = Path(out_dir)
    found = set()
    with tarfile.open(fileobj=fileobj, mode=mode) as archive:
        for member in archive:
            relative = source.tree_path(member.name) if member.isreg() else None
            if relative not in wanted:
                continue
            target = out_dir / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.extractfile(member) as stream, open(target, 'wb') as sink:
                shutil.copyfileobj(stream, sink)
            target.chmod(0o755 if member.mode & 0o111 else 0o644)
            found.add(relative)
    return found


def extract_zip(path, wanted, source, out_dir):
    out_dir = Path(out_dir)
    found = set()
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            relative = source.tree_path(info.filename) if not info.is_dir() else None
            if relative not in wanted:
                continue
            target = out_dir / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(info) as stream, open(target, 'wb') as sink:
                shutil.copyfileobj(stream, sink)
            found.add(relative)
    return found


def extract_file(path, wanted, source, out_dir):
    """Extracts from an archive file. xz decodes on all cores, which Python's own
    lzma can't, and Chromium's archive has dozens of independent blocks."""
    if str(path).endswith('.zip'):
        return extract_zip(path, wanted, source, out_dir)
    # Chromium 156's prepared tarballs are zstd; earlier ones were xz.
    for suffix, tool in (('.xz', 'xz'), ('.zst', 'zstd')):
        if str(path).endswith(suffix) and shutil.which(tool):
            with subprocess.Popen([tool, '-dc', '-T0', str(path)],
                                  stdout=subprocess.PIPE) as decoder:
                found = extract_tar(decoder.stdout, wanted, source, out_dir, 'r|')
                while decoder.stdout.read(1 << 20):
                    pass
            if decoder.returncode != 0:
                raise SurfaceError(f'{tool} could not decode {path}')
            return found
    with open(path, 'rb') as stream:
        return extract_tar(stream, wanted, source, out_dir)


# tarballs.imput.net answers Python's default User-Agent with 403 Forbidden.
USER_AGENT = 'rac-checks (+https://github.com/notkainoa/rac)'


def open_url(url, timeout):
    request = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    return urllib.request.urlopen(request, timeout=timeout)  # nosec: fixed https URLs


def fetch_text(url):
    with open_url(url, timeout=60) as response:
        return response.read().decode('utf-8')


def download(url, destination):
    with open_url(url, timeout=120) as response:
        with open(destination, 'wb') as sink:
            shutil.copyfileobj(response, sink, 1 << 20)


def fetch_and_verify(source, folder, cache_dir=None, attempts=3):
    """A verified copy of the source's archive: from cache_dir, else downloaded."""
    if cache_dir and (Path(cache_dir) / source.filename).is_file():
        path = Path(cache_dir) / source.filename
        verify_download(path, source)
        return path
    path = Path(folder) / source.filename
    for attempt in range(1, attempts + 1):
        try:
            print(f'downloading {source.url} (attempt {attempt}/{attempts})', file=sys.stderr)
            download(source.url, path)
            verify_download(path, source)
            return path
        except (OSError, SurfaceError) as error:
            print(f'download failed: {error}', file=sys.stderr)
            if attempt == attempts:
                raise SurfaceError(f'could not download {source.name}: {error}') from error
            time.sleep(10 * attempt)
    return path


def extract_sources(wanted, out_dir, sources, cache_dir=None):
    """Extracts the wanted paths, fetching only the archives that hold some."""
    found = set()
    claims = claim_paths(sources, set(wanted))
    for source in sources:
        if not claims[source.name]:
            continue
        with tempfile.TemporaryDirectory(prefix='rac-download-') as folder:
            path = fetch_and_verify(source, folder, cache_dir)
            try:
                got = extract_file(path, claims[source.name], source, out_dir)
            except (OSError, tarfile.TarError, zipfile.BadZipFile) as error:
                raise SurfaceError(f'could not read {source.name}: {error}') from error
        print(f'{source.name}: {len(got)} of {len(claims[source.name])} files', file=sys.stderr)
        found |= got
    return found


# Applying patches


def find_patch_bin(requested=None):
    """GNU patch: gpatch on macOS, patch on Linux."""
    for candidate in [requested] if requested else ['gpatch', 'patch']:
        path = shutil.which(candidate)
        if not path:
            continue
        version = subprocess.run([path, '--version'], capture_output=True, text=True,
                                 check=False).stdout
        if 'GNU patch' in version:
            return path
    raise SurfaceError('GNU patch not found (macOS: brew install gpatch)')


PATCHING_FILE = re.compile(r"^patching file '?(.*?)'?$")
HUNK_APPLIED = re.compile(r'^Hunk #(\d+) succeeded at (\d+)(?: with fuzz (\d+))?'
                          r'(?: \(offset (-?\d+) lines?\))?\.')
HUNK_FAILED = re.compile(r'^Hunk #(\d+) FAILED at (\d+)')
TROUBLE = re.compile(r'(?i)^(?:patch: \*\*\*\* |.*(?:malformed patch|only garbage was found'
                     r'|reversed \(or previously applied\)|which already exists'
                     r'|can\'t create|permission denied|no such file))')


@dataclass
class PatchResult:
    ref: PatchRef
    returncode: int = 0
    output: str = ''
    fuzz: list = field(default_factory=list)  # (file, hunk, fuzz level)
    offsets: int = 0
    failed: list = field(default_factory=list)  # (file, hunk)
    missing: list = field(default_factory=list)  # files the tree lacks
    trouble: list = field(default_factory=list)  # other messages

    @property
    def bad(self):
        """Whether this patch breaks the run. Missing files in Helium's and
        helium-macos's patches only warn: some files come from sources other
        than the Chromium archive."""
        if self.fuzz or self.failed or self.trouble:
            return True
        if self.missing and self.ref.layer == RAC:
            return True
        if self.returncode != 0 and not self.missing:
            return True
        return False


def parse_patch_output(output, result):
    current = ''
    for line in output.split('\n'):
        match = PATCHING_FILE.match(line)
        if match:
            current = match.group(1)
            continue
        match = HUNK_APPLIED.match(line)
        if match:
            if match.group(3) and int(match.group(3)) > 0:
                result.fuzz.append((current, int(match.group(1)), int(match.group(3))))
            if match.group(4):
                result.offsets += 1
            continue
        match = HUNK_FAILED.match(line)
        if match:
            result.failed.append((current, int(match.group(1))))
            continue
        if TROUBLE.match(line):
            result.trouble.append(line.strip())


def run_patch(patch_bin, tree, ref, fuzz_zero, ignore_whitespace):
    """Applies one patch with GNU patch and reads what it says."""
    command = [
        patch_bin, '-p1', '--forward', '--batch', '--no-backup-if-mismatch', '--reject-file=-',
        '-d', str(tree), '-i', str(ref.path.resolve())
    ]
    if fuzz_zero:
        command.append('--fuzz=0')
    if ignore_whitespace:
        command.append('--ignore-whitespace')
    env = dict(os.environ, LC_ALL='C', LANG='C')
    done = subprocess.run(command, stdin=subprocess.DEVNULL, capture_output=True, text=True,
                          errors='surrogateescape', env=env, check=False)
    result = PatchResult(ref, done.returncode, done.stdout + done.stderr)
    parse_patch_output(result.output, result)
    return result


def count_hunks(old, new):
    """Hunks of `diff -U3 old new`. A deleted or binary file counts as one."""
    if not new.exists():
        return 1
    done = subprocess.run(['diff', '-a', '-U3', str(old), str(new)], capture_output=True,
                          check=False, env=dict(os.environ, LC_ALL='C'))
    if done.returncode > 1:
        raise SurfaceError(f'diff failed on {new}')
    return sum(1 for line in done.stdout.split(b'\n') if line.startswith(b'@@ '))


@dataclass
class Surface:
    """What rac's patches add up to."""
    groups: list = field(default_factory=list)  # in series order
    stacked: dict = field(default_factory=lambda: defaultdict(int))  # all hunks
    stacked_upstream: dict = field(default_factory=lambda: defaultdict(int))
    patches: dict = field(default_factory=lambda: defaultdict(int))
    files: dict = field(default_factory=lambda: defaultdict(set))  # upstream
    added: dict = field(default_factory=lambda: defaultdict(set))  # rac's new files
    last_group: dict = field(default_factory=dict)  # path -> group
    net: dict = field(default_factory=dict)  # path -> net-diff hunks
    shared: set = field(default_factory=set)  # touched by more than one group
    base_touched: set = field(default_factory=set)  # also patched by Helium

    def net_by_group(self):
        totals = defaultdict(int)
        for path, hunks in self.net.items():
            totals[self.last_group[path]] += hunks
        return totals


@dataclass
class Run:
    results: list
    surface: Surface

    @property
    def bad(self):
        return [result for result in self.results if result.bad]


def apply_all(plan, pristine, work, scratch, patch_bin, ignore_whitespace=False):
    """Applies the whole plan to a copy of pristine, measuring rac's surface."""
    work, scratch = Path(work), Path(scratch)
    shutil.copytree(pristine, work, symlinks=True)
    before_rac = scratch / 'before-rac'
    surface = Surface()
    origin = {}  # path -> 'upstream' (present before rac) or 'rac' (rac added it)
    created_in = {}  # rac-added path -> group of the patch that added it
    results = []
    for ref in plan:
        file_patches = read_patch(ref.path)
        missing = []
        for file_patch in file_patches:
            target, exists = resolve_target(work, file_patch)
            if target is None:
                missing.append(file_patch.old or file_patch.new)
            elif ref.layer != RAC:
                surface.base_touched.add(target)
            elif target not in origin:
                origin[target] = 'upstream' if exists else 'rac'
                created_in[target] = ref.group
                if exists:
                    saved = before_rac / target
                    saved.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(work / target, saved)
        if ref.layer == RAC:
            group = ref.group
            if group not in surface.groups:
                surface.groups.append(group)
            surface.patches[group] += 1
            for file_patch in file_patches:
                target, _ = resolve_target(work, file_patch)
                target = target or file_patch.old or file_patch.new
                surface.stacked[group] += file_patch.hunks
                if origin.get(target) == 'upstream':
                    surface.stacked_upstream[group] += file_patch.hunks
                    if surface.last_group.get(target, group) != group:
                        surface.shared.add(target)
                    surface.last_group[target] = group
                    surface.files[group].add(target)
        result = run_patch(patch_bin, work, ref, ref.layer == RAC, ignore_whitespace)
        result.missing = missing
        results.append(result)
    for target, kind in origin.items():
        if kind == 'rac':
            if (work / target).is_file():
                surface.added[created_in[target]].add(target)
        else:
            old, new = before_rac / target, work / target
            if new.exists() and filecmp.cmp(old, new, shallow=False):
                continue
            surface.net[target] = count_hunks(old, new)
    return Run(results, surface)


# Reporting


def table(headers, rows):
    lines = ['| ' + ' | '.join(headers) + ' |', '|' + '|'.join(['---'] + ['---:'] * (len(headers) - 1)) + '|']
    lines += ['| ' + ' | '.join(str(cell) for cell in row) + ' |' for row in rows]
    return '\n'.join(lines)


def annotate(level, title, message, path=None):
    if os.environ.get('GITHUB_ACTIONS') != 'true':
        return
    where = f',file={path}' if path else ''
    message = message.replace('%', '%25').replace('\r', '%0D').replace('\n', '%0A')
    print(f'::{level} title={title}{where}::{message}')


def render_report(run, plan):
    """Markdown for the job summary; it reads fine in a terminal too."""
    surface = run.surface
    lines = ['## Patch apply', '']
    rows = []
    for layer in (HELIUM, PLATFORM, RAC):
        results = [result for result in run.results if result.ref.layer == layer]
        rows.append([
            LAYER_TITLES[layer] + (' (fuzz 0)' if layer == RAC else ' (fuzz up to 2)'),
            len(results),
            sum(len(result.failed) for result in results),
            sum(len(result.fuzz) for result in results),
            sum(result.offsets for result in results),
            sum(len(result.missing) for result in results),
        ])
    lines.append(table(['Layer', 'Patches', 'Failed hunks', 'Hunks with fuzz',
                        'Hunks with offset', 'Files not found'], rows))
    lines.append('')
    bad = run.bad
    lines.append(f'**{len(bad)} patch(es) broke the run.**' if bad else 'No patch broke the run.')
    if bad:
        lines.append('')
    for result in bad:
        lines.append(f'- `{result.ref.name}` ({LAYER_TITLES[result.ref.layer]}): ' + describe(result))
    warnings = [r for r in run.results if r.missing and not r.bad]
    if warnings:
        lines += [
            '', '<details><summary>Files that Helium\'s or helium-macos\'s patches name but the '
            'Chromium archive lacks (' + str(sum(len(r.missing) for r in warnings)) +
            ', not a failure)</summary>', ''
        ]
        for result in warnings:
            lines.append(f'- `{result.ref.name}`: ' + ', '.join(f'`{m}`' for m in result.missing))
        lines += ['', '</details>']

    lines += ['', '## Patch surface', '']
    rows = []
    net = surface.net_by_group()
    for group in surface.groups:
        rows.append([
            group, surface.patches[group], surface.stacked[group], surface.stacked_upstream[group],
            len(surface.files[group]), net.get(group, 0), len(surface.added[group])
        ])
    total = ['Total', sum(surface.patches.values()), sum(surface.stacked.values()),
             sum(surface.stacked_upstream.values()), len(surface.last_group),
             sum(surface.net.values()), sum(len(v) for v in surface.added.values())]
    rows.append([f'**{cell}**' if i else cell for i, cell in enumerate(total)])
    lines.append(table(['Group', 'Patches', 'Stacked hunks', 'Stacked in upstream files',
                        'Upstream files touched', 'Net-diff hunks', 'Files added'], rows))
    both = sum(h for p, h in surface.net.items() if p in surface.base_touched)
    only = sum(surface.net.values()) - both
    files_both = sum(1 for p in surface.net if p in surface.base_touched)
    lines += [
        '',
        f'- **Net-diff hunks in upstream files: {sum(surface.net.values())}** '
        f'in {len(surface.net)} changed files (of {len(surface.last_group)} touched). '
        f'{both} hunks are in {files_both} files that Helium or helium-macos also patch; '
        f'{only} are in files only rac patches.',
        f'- Stacked hunks, all rac patches including new files: {sum(surface.stacked.values())}. '
        f'Only those in upstream files: {sum(surface.stacked_upstream.values())}. '
        '(For reference, the budget is 630 of the second number, aiming for 550.)',
        f'- Failed hunks in rac\'s patches at fuzz 0: '
        f'{sum(len(r.failed) for r in run.results if r.ref.layer == RAC)}.',
        '- A file\'s net-diff hunks, and its upstream file, count under the group of the last '
        f'rac patch that touches it. {len(surface.shared)} files are touched by more than one '
        'group, so a group\'s own work can be larger than its column. The totals are exact.',
    ]
    top = sorted(surface.net.items(), key=lambda item: (-item[1], item[0]))[:15]
    if top:
        lines += ['', '<details><summary>Files with the most net-diff hunks</summary>', '']
        lines += [f'- {hunks}: `{path}` ({surface.last_group[path]})' for path, hunks in top]
        lines += ['', '</details>']
    return '\n'.join(lines) + '\n'


def describe(result):
    parts = []
    if result.failed:
        parts.append('failed hunks: ' + ', '.join(
            f'#{hunk} in `{name}`' for name, hunk in result.failed[:5]))
    if result.fuzz:
        parts.append('applied with fuzz: ' + ', '.join(
            f'#{hunk} in `{name}` (fuzz {level})' for name, hunk, level in result.fuzz[:5]))
    if result.missing and result.ref.layer == RAC:
        parts.append('file(s) not found: ' + ', '.join(f'`{m}`' for m in result.missing[:5]))
    if result.trouble:
        parts.append('patch said: ' + '; '.join(result.trouble[:3]))
    if not parts:
        parts.append(f'patch exited {result.returncode}')
    return '; '.join(parts)


def report_failures(run):
    for result in run.bad:
        print(f'\n--- {LAYER_TITLES[result.ref.layer]}: {result.ref.name}: {describe(result)}')
        print(result.output.rstrip()[-4000:])
        annotate('error', 'Patch does not apply cleanly', describe(result),
                 f'patches/{result.ref.name}' if result.ref.layer != HELIUM else None)


# Commands


def cmd_files(args):
    plan = build_plan(args.helium_patches, args.platform_patches)
    paths = upstream_paths(plan)
    text = '\n'.join(paths) + '\n'
    if args.output:
        Path(args.output).write_text(text, encoding='utf-8')
    else:
        sys.stdout.write(text)
    print(f'{len(plan)} patches touch {len(paths)} existing files', file=sys.stderr)
    return 0


def cmd_extract(args):
    wanted = [line for line in Path(args.list).read_text(encoding='utf-8').split('\n') if line]
    sources = load_sources(args.ini, args.version)
    found = extract_sources(wanted, args.out, sources, args.cache_dir)
    absent = sorted(set(wanted) - found)
    print(f'extracted {len(found)} of {len(wanted)} files; {len(absent)} are in no download '
          '(rac or Helium patches create them)', file=sys.stderr)
    for path in absent[:25]:
        print(f'  in no download: {path}', file=sys.stderr)
    if not found:
        raise SurfaceError('the downloads held none of the files; is the prefix right?')
    return 0


def cmd_apply(args):
    plan = build_plan(args.helium_patches, args.platform_patches)
    patch_bin = find_patch_bin(args.patch_bin)
    with tempfile.TemporaryDirectory(prefix='rac-surface-') as scratch:
        work = Path(args.work) if args.work else Path(scratch) / 'tree'
        if work.exists():
            raise SurfaceError(f'{work} already exists')
        run = apply_all(plan, args.pristine, work, scratch, patch_bin, args.ignore_whitespace)
    report_failures(run)
    report = render_report(run, plan)
    print('\n' + report)
    summary = args.summary or os.environ.get('GITHUB_STEP_SUMMARY')
    if summary:
        with open(summary, 'a', encoding='utf-8') as out:
            out.write(report)
    return 1 if run.bad else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    commands = parser.add_subparsers(dest='command', required=True)

    def patch_dirs(sub):
        sub.add_argument('--helium-patches', default='helium-chromium/patches',
                         help="Helium core's patches directory")
        sub.add_argument('--platform-patches', default='patches',
                         help="this repository's patches directory")

    sub = commands.add_parser('files', help='list the existing files the patches modify')
    patch_dirs(sub)
    sub.add_argument('-o', '--output')
    sub.set_defaults(func=cmd_files)

    sub = commands.add_parser('extract', help='extract those files from the Chromium archive')
    sub.add_argument('--list', required=True, help='file from the files command')
    sub.add_argument('--out', required=True)
    sub.add_argument('--ini', action='append', help='a downloads file (default: Helium\'s '
                     'downloads.ini and deps.ini, and the one at the root)')
    sub.add_argument('--version', required=True, help='the Chromium version')
    sub.add_argument('--cache-dir', help='use archives found here (by file name) instead of '
                     'downloading them; they are still verified')
    sub.set_defaults(func=cmd_extract)

    sub = commands.add_parser('apply', help='apply the patches and count the surface')
    patch_dirs(sub)
    sub.add_argument('--pristine', required=True, help='the extracted Chromium files')
    sub.add_argument('--work', help='where to apply (default: a temporary folder)')
    sub.add_argument('--patch-bin', help='GNU patch (default: gpatch, then patch)')
    sub.add_argument('--ignore-whitespace', action='store_true',
                     help='like the release build (quilt does not)')
    sub.add_argument('--summary', help='append the report here (default: $GITHUB_STEP_SUMMARY)')
    sub.set_defaults(func=cmd_apply)

    args = parser.parse_args(argv)
    if args.command == 'extract' and not args.ini:
        args.ini = ['helium-chromium/downloads.ini', 'helium-chromium/deps.ini', 'downloads.ini']
    try:
        return args.func(args)
    except SurfaceError as error:
        print(f'patch_surface: {error}', file=sys.stderr)
        annotate('error', 'patch_surface', str(error))
        return 2


if __name__ == '__main__':
    sys.exit(main())
