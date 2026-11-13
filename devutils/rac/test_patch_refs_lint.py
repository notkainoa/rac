#!/usr/bin/env python3

# Copyright 2026 The rac Authors
# You can use, redistribute, and/or modify this source code under
# the terms of the GPL-3.0 license that can be found in the LICENSE file.
"""Tests for patch_refs_lint.py, on tiny fake patch series in temp folders.

Run from the repository root:
    python3 -m unittest discover -s devutils/rac -p 'test_*.py' -v
"""

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import patch_refs_lint as refs

SCRIPT = Path(__file__).resolve().parent / 'patch_refs_lint.py'
STAMP = '\t2026-11-01 00:00:00.000000000 -0700'


def create(path, lines=(), prefix='b', stamp=''):
    """A patch section creating path with the given lines."""
    body = ''.join(f'+{line}\n' for line in lines)
    return (f'--- /dev/null{stamp}\n+++ {prefix}/{path}{stamp}\n'
            f'@@ -0,0 +1,{len(lines)} @@\n{body}')


def edit(path, removed=(), added=(), old_prefix='a', new_prefix='b', stamp=''):
    """One hunk in path: a context line, then the removed and added lines."""
    body = ' keep\n'
    body += ''.join(f'-{line}\n' for line in removed)
    body += ''.join(f'+{line}\n' for line in added)
    body += ' keep\n'
    return (f'--- {old_prefix}/{path}{stamp}\n+++ {new_prefix}/{path}{stamp}\n'
            f'@@ -1,{2 + len(removed)} +1,{2 + len(added)} @@\n{body}')


def delete(path, lines=('x',)):
    body = ''.join(f'-{line}\n' for line in lines)
    return f'--- a/{path}\n+++ /dev/null\n@@ -1,{len(lines)} +0,0 @@\n{body}'


class LintTest(unittest.TestCase):

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.helium = self.root / 'helium'
        self.platform = self.root / 'platform'
        self.resources = self.root / 'resources'
        self.series = {self.helium: [], self.platform: []}

    def add(self, root, name, text):
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_text(text)
        self.series[root].append(name)

    def lint(self, allowlist=()):
        for root, names in self.series.items():
            root.mkdir(exist_ok=True)
            (root / 'series').write_text('\n'.join(names) + '\n')
        resource_files = [self.resources / 'platform_resources.txt',
                          self.resources / 'branding.txt']
        return refs.lint(self.helium, self.platform, resource_files, allowlist)

    def missing(self):
        return [(r.patch, r.file, r.path, r.kind) for r in self.lint().missing]

    def test_missing_include_fails(self):
        self.add(self.platform, 'rac/x/a.patch',
                 edit('chrome/browser/ui/foo.cc',
                      added=['#include "chrome/browser/ui/rac/missing.h"']))
        self.assertEqual(self.missing(),
                         [('rac/x/a.patch', 'chrome/browser/ui/foo.cc',
                           'chrome/browser/ui/rac/missing.h', 'include')])

    def test_include_of_a_file_created_by_an_earlier_patch_passes(self):
        self.add(self.platform, 'rac/x/a.patch',
                 create('chrome/browser/ui/rac/x.h', ['// x']))
        self.add(self.platform, 'rac/x/b.patch',
                 edit('chrome/browser/ui/foo.cc',
                      added=['#include "chrome/browser/ui/rac/x.h"']))
        self.assertEqual(self.missing(), [])

    def test_include_of_a_file_created_by_a_later_patch_passes(self):
        self.add(self.platform, 'rac/x/a.patch',
                 edit('chrome/browser/ui/foo.cc',
                      added=['#include "chrome/browser/ui/rac/x.h"']))
        self.add(self.platform, 'rac/x/b.patch',
                 create('chrome/browser/ui/rac/x.h', ['// x']))
        self.assertEqual(self.missing(), [])

    def test_created_then_deleted_fails(self):
        self.add(self.platform, 'rac/x/a.patch', create('chrome/browser/rac/x.h'))
        self.add(self.platform, 'rac/x/b.patch',
                 edit('chrome/browser/ui/foo.cc',
                      added=['#include "chrome/browser/rac/x.h"']))
        self.add(self.platform, 'rac/x/c.patch', delete('chrome/browser/rac/x.h'))
        self.assertEqual([r.path for r in self.lint().missing],
                         ['chrome/browser/rac/x.h'])

    def test_a_renamed_file_moves_to_its_new_name(self):
        self.add(self.platform, 'rac/x/a.patch', create('chrome/browser/rac/old.h', ['x']))
        self.add(self.platform, 'rac/x/b.patch',
                 '--- a/chrome/browser/rac/old.h\n+++ b/chrome/browser/rac/new.h\n'
                 '@@ -1 +1 @@\n-x\n+y\n')
        self.add(self.platform, 'rac/x/c.patch',
                 edit('chrome/browser/ui/foo.cc',
                      added=['#include "chrome/browser/rac/new.h"',
                             '#include "chrome/browser/rac/old.h"']))
        self.assertEqual([r.path for r in self.lint().missing],
                         ['chrome/browser/rac/old.h'])

    def test_a_rename_carries_its_references(self):
        # The include moves to new.cc with the rename; a later patch that
        # removes it from new.cc cancels it.
        self.add(self.platform, 'rac/x/a.patch',
                 edit('chrome/browser/ui/old.cc',
                      added=['#include "chrome/browser/rac/gone.h"']))
        self.add(self.platform, 'rac/x/b.patch',
                 '--- a/chrome/browser/ui/old.cc\n+++ b/chrome/browser/ui/new.cc\n'
                 '@@ -1 +1 @@\n-x\n+y\n')
        self.add(self.platform, 'rac/x/c.patch',
                 edit('chrome/browser/ui/new.cc',
                      removed=['#include "chrome/browser/rac/gone.h"']))
        self.assertEqual(self.missing(), [])

    def test_a_removed_gen_dir_output_no_longer_counts(self):
        self.add(self.platform, 'rac/x/a.patch',
                 create('chrome/browser/ui/views/rac/BUILD.gn',
                        ['  outputs = [ "$target_gen_dir/spaces/emoji_data.inc" ]']))
        self.add(self.platform, 'rac/x/b.patch',
                 edit('chrome/browser/ui/views/rac/BUILD.gn',
                      removed=['  outputs = [ "$target_gen_dir/spaces/emoji_data.inc" ]']))
        self.add(self.platform, 'rac/x/c.patch',
                 edit('chrome/browser/ui/views/rac/spaces/emoji_data.cc',
                      added=['#include "chrome/browser/ui/views/rac/spaces/emoji_data.inc"']))
        self.assertEqual([r.path for r in self.lint().missing],
                         ['chrome/browser/ui/views/rac/spaces/emoji_data.inc'])

    def test_gn_data_directory_is_satisfied_by_a_resource_under_it(self):
        self.resources.mkdir()
        (self.resources / 'platform_resources.txt').write_text(
            'assets/a.json chrome/test/data/rac/fixtures/a.json\n')
        self.add(self.platform, 'rac/x/a.patch',
                 create('chrome/browser/rac/BUILD.gn',
                        ['data = [ "//chrome/test/data/rac/fixtures/" ]']))
        self.assertEqual(self.missing(), [])

    def test_a_line_a_later_patch_removes_cancels_its_reference(self):
        include = '#include "chrome/browser/ui/rac/missing.h"'
        self.add(self.platform, 'rac/x/a.patch',
                 edit('chrome/browser/ui/foo.cc', added=[include]))
        self.add(self.platform, 'rac/x/b.patch',
                 edit('chrome/browser/ui/foo.cc', removed=[include]))
        self.assertEqual(self.missing(), [])

    def test_deleting_the_file_that_held_a_reference_drops_it(self):
        self.add(self.platform, 'rac/x/a.patch',
                 create('chrome/browser/rac/foo.cc',
                        ['#include "chrome/browser/rac/missing.h"']))
        self.add(self.platform, 'rac/x/b.patch', delete('chrome/browser/rac/foo.cc'))
        self.assertEqual(self.missing(), [])

    def test_gn_source_paths_resolve_against_the_build_file(self):
        self.add(self.platform, 'rac/x/a.patch',
                 create('chrome/browser/ui/rac/BUILD.gn',
                        ['sources = [ "x.cc", "../rac_sibling/y.cc" ]']) +
                 create('chrome/browser/ui/rac/x.cc') +
                 create('chrome/browser/ui/rac_sibling/y.cc'))
        self.assertEqual(self.missing(), [])

    def test_missing_gn_source_fails(self):
        self.add(self.platform, 'rac/x/a.patch',
                 create('chrome/browser/ui/rac/BUILD.gn',
                        ['sources = [ "x.cc", "../rac_sibling/y.cc" ]']) +
                 create('chrome/browser/ui/rac/x.cc'))
        self.assertEqual([r.path for r in self.lint().missing],
                         ['chrome/browser/ui/rac_sibling/y.cc'])

    def test_gn_label_needs_a_build_file_in_its_directory(self):
        self.add(self.platform, 'rac/x/a.patch',
                 edit('chrome/browser/ui/BUILD.gn',
                      added=['    "//chrome/browser/ui/rac/tabs:logic",']))
        self.assertEqual(self.missing(),
                         [('rac/x/a.patch', 'chrome/browser/ui/BUILD.gn',
                           '//chrome/browser/ui/rac/tabs:logic', 'gn label')])

    def test_gn_label_passes_when_the_build_file_is_created(self):
        self.add(self.platform, 'rac/x/a.patch',
                 edit('chrome/browser/ui/BUILD.gn',
                      added=['    "//chrome/browser/ui/rac/tabs:logic",',
                             '    "//chrome/browser/rac/ai",']) +
                 create('chrome/browser/ui/rac/tabs/BUILD.gn') +
                 create('chrome/browser/rac/ai/BUILD.gn'))
        self.assertEqual(self.missing(), [])

    def test_gn_data_directory_is_satisfied_by_files_under_it(self):
        self.add(self.platform, 'rac/x/a.patch',
                 create('chrome/browser/rac/import/BUILD.gn',
                        ['data = [ "//chrome/test/data/rac/import/" ]']) +
                 create('chrome/test/data/rac/import/arc/User_Data/Default/Preferences',
                        ['{}']))
        self.assertEqual(self.missing(), [])

    def test_gni_import_is_a_file_not_a_label(self):
        self.add(self.platform, 'rac/x/a.patch',
                 create('chrome/browser/rac/dev/BUILD.gn',
                        ['import("//chrome/browser/rac/dev/x.gni")']) +
                 create('chrome/browser/rac/dev/x.gni'))
        self.assertEqual(self.missing(), [])

    def test_generated_headers_pass_when_their_source_exists(self):
        self.add(self.platform, 'rac/x/a.patch',
                 create('chrome/common/rac/a.mojom') +
                 create('chrome/browser/rac/x.proto') +
                 create('chrome/browser/rac/dev/BUILD.gn',
                        ['buildflag_header("buildflags") { header = "buildflags.h" }']) +
                 edit('chrome/browser/rac/user.cc',
                      added=['#include "chrome/common/rac/a.mojom.h"',
                             '#include "chrome/common/rac/a.mojom-forward.h"',
                             '#include "chrome/browser/rac/x.pb.h"',
                             '#include "chrome/browser/rac/dev/buildflags.h"']))
        self.assertEqual(self.missing(), [])

    def test_generated_headers_fail_without_their_source(self):
        self.add(self.platform, 'rac/x/a.patch',
                 edit('chrome/browser/rac/user.cc',
                      added=['#include "chrome/common/rac/a.mojom.h"',
                             '#include "chrome/browser/rac/x.pb.h"',
                             '#include "chrome/browser/rac/dev/buildflags.h"']))
        self.assertEqual([r.path for r in self.lint().missing],
                         ['chrome/common/rac/a.mojom.h', 'chrome/browser/rac/x.pb.h',
                          'chrome/browser/rac/dev/buildflags.h'])

    def test_gen_dir_outputs_of_a_build_file_are_generated(self):
        self.add(self.platform, 'rac/x/a.patch',
                 create('chrome/browser/ui/views/rac/BUILD.gn',
                        ['action("emoji_data_inc") {',
                         '  outputs = [ "$target_gen_dir/spaces/emoji_data.inc" ]',
                         '}']) +
                 edit('chrome/browser/ui/views/rac/spaces/emoji_data.cc',
                      added=['#include "chrome/browser/ui/views/rac/spaces/emoji_data.inc"']))
        self.assertEqual(self.missing(), [])

    def test_framework_names_are_libraries_not_files(self):
        self.add(self.platform, 'rac/x/a.patch',
                 create('chrome/browser/rac/pip/BUILD.gn',
                        ['libs = [ "AppKit.framework" ]']))
        self.assertEqual(self.missing(), [])

    def test_grit_and_gen_paths_are_skipped_not_checked(self):
        self.add(self.platform, 'rac/x/a.patch',
                 edit('chrome/browser/rac/user.cc',
                      added=['#include "chrome/grit/rac_strings.h"',
                             '#include "chrome/browser/gen/rac/x.h"']))
        result = self.lint()
        self.assertEqual(result.missing, [])
        self.assertEqual(result.skipped, 2)

    def test_non_rac_paths_are_ignored(self):
        self.add(self.platform, 'rac/x/a.patch',
                 edit('chrome/browser/ui/foo.cc',
                      added=['#include "chrome/browser/ui/helium/absent.h"']) +
                 edit('chrome/browser/ui/BUILD.gn',
                      added=['    "absent.cc",',
                             '    "//chrome/browser/helium:absent",']))
        self.assertEqual(self.missing(), [])

    def test_a_resource_list_destination_passes(self):
        self.resources.mkdir()
        (self.resources / 'platform_resources.txt').write_text(
            '# comment\nassets/logo.png chrome/browser/ui/rac/logo.png\n')
        self.add(self.platform, 'rac/x/a.patch',
                 create('chrome/browser/ui/rac/BUILD.gn',
                        ['sources = [ "logo.png" ]']))
        self.assertEqual(self.missing(), [])

    def test_references_in_helium_and_platform_patches_are_not_checked(self):
        self.add(self.helium, 'h/one.patch',
                 edit('chrome/browser/ui/foo.cc',
                      added=['#include "chrome/browser/ui/rac/nothing.h"']))
        self.add(self.platform, 'mac/two.patch',
                 edit('chrome/browser/ui/bar.cc',
                      added=['#include "chrome/browser/rac/nothing.cc"']))
        self.assertEqual(self.missing(), [])

    def test_src_header_style_with_timestamps(self):
        self.add(self.platform, 'rac/x/a.patch',
                 create('chrome/browser/rac/x.inc', ['// x'], prefix='src',
                        stamp=STAMP))
        self.add(self.platform, 'rac/x/b.patch',
                 'Index: src/chrome/browser/rac/user.cc\n' + '=' * 67 + '\n' +
                 edit('chrome/browser/rac/user.cc',
                      added=['#include "chrome/browser/rac/x.inc"'],
                      old_prefix='src.orig', new_prefix='src', stamp=STAMP))
        self.assertEqual(self.missing(), [])

    def test_allowlisted_path_passes(self):
        self.add(self.platform, 'rac/x/a.patch',
                 edit('chrome/browser/ui/foo.cc',
                      added=['#include "chrome/browser/ui/rac/missing.h"']))
        result = self.lint(allowlist={'chrome/browser/ui/rac/missing.h'})
        self.assertEqual(result.missing, [])
        self.assertEqual(result.allowed, 1)


class CommandTest(unittest.TestCase):

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def run_lint(self, *argv):
        return subprocess.run([sys.executable, '-I', str(SCRIPT), *map(str, argv)],
                              capture_output=True, text=True, check=False,
                              env={'PATH': '/usr/bin:/bin'})

    def test_exit_codes_and_summary(self):
        for name, series in (('helium', []), ('patches', ['rac/x/a.patch'])):
            (self.root / name).mkdir(parents=True, exist_ok=True)
            (self.root / name / 'series').write_text('\n'.join(series) + '\n')
        (self.root / 'patches/rac/x').mkdir(parents=True)
        (self.root / 'patches/rac/x/a.patch').write_text(
            edit('chrome/browser/ui/foo.cc',
                 added=['#include "chrome/browser/ui/rac/missing.h"']))
        argv = ('--helium-patches', self.root / 'helium',
                '--patches', self.root / 'patches',
                '--resources', self.root / 'resources')
        done = self.run_lint(*argv)
        self.assertEqual(done.returncode, 1, done.stdout + done.stderr)
        self.assertIn('references chrome/browser/ui/rac/missing.h (include)',
                      done.stdout)
        self.assertIn('1 missing', done.stdout)
        (self.root / 'patches/rac/x/a.patch').write_text(
            create('chrome/browser/ui/rac/missing.h'))
        done = self.run_lint(*argv)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertIn('0 missing', done.stdout)


if __name__ == '__main__':
    unittest.main()
