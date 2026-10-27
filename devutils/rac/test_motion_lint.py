#!/usr/bin/env python3

# Copyright 2026 The rac Authors
# You can use, redistribute, and/or modify this source code under
# the terms of the GPL-3.0 license that can be found in the LICENSE file.
"""Tests for motion_lint.py with fixture patches. Only temporary folders.

Run from the repository root:
    python3 -m unittest discover -s devutils/rac -p 'test_*.py' -v
"""

from collections import Counter
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import motion_lint

SCRIPT = Path(__file__).resolve().parent / 'motion_lint.py'
VIEW = 'chrome/browser/ui/views/rac/thing_view.cc'
CSS = 'chrome/browser/resources/rac_ai/app.css'


def patch(path, added=(), removed=(), new=False):
    """A quilt-style patch of one file."""
    old = '/dev/null' if new else f'src.orig/{path}'
    body = ''.join(f'-{l}\n' for l in removed) + ''.join(f'+{l}\n' for l in added)
    return (f'Index: src/{path}\n'
            '===================================================================\n'
            f'--- {old}\t2026-10-27 00:00:00.000000000 -0700\n'
            f'+++ src/{path}\t2026-10-27 00:00:00.000000000 -0700\n'
            f'@@ -1,{len(removed)} +1,{len(added)} @@\n{body}')


class LiteralTest(unittest.TestCase):

    def kinds(self, line, path=VIEW):
        return motion_lint.literals(path, line)

    def test_cxx(self):
        cases = {
            'constexpr base::TimeDelta kFade = base::Milliseconds(120);': ['duration'],
            'SetAnimationDuration(base::Milliseconds(150));': ['duration'],
            'constexpr base::TimeDelta kStep = base::Hertz(240);': ['duration'],
            'settings.SetTweenType(gfx::Tween::EASE_OUT);': ['curve'],
            'static const gfx::CubicBezier bezier(0.2, 0, 0, 1);': ['curve'],
            'gfx::CubicBezier bezier(curve.x1, curve.y1, curve.x2, curve.y2);': [],
            'constexpr int kPanelRadius = 12;': ['radius'],
            'constexpr float kSwatchRadius = 8.5f;': ['radius'],
            'layer()->SetRoundedCornerRadius(gfx::RoundedCornersF(12));': ['radius'],
            'SetBorder(views::CreateEmptyBorder(gfx::Insets::VH(6, 10)));': ['inset'],
            'constexpr int kRowInset = 8;': ['inset'],
            'constexpr int kPadding = 14;': ['padding'],
            'constexpr int kTitleGap = 7;': ['gap'],
            'constexpr int kTileSpacing = 8;': ['gap'],
            'layout->SetBetweenChildSpacing(6);': ['gap'],
            'views::BoxLayout::Orientation::kHorizontal, gfx::Insets(), 8));': ['gap'],
            'gfx::Insets::VH(0, 10), 6));': ['inset', 'gap'],
        }
        for line, kinds in cases.items():
            with self.subTest(line=line):
                self.assertEqual(self.kinds(line), kinds)

    def test_cxx_not_literals(self):
        for line in [
                'constexpr int kPillRadius = kPillHeight / 2;',
                'canvas->DrawRoundRect(bounds, radius - 0.5f, edge);',
                'canvas->DrawRoundRect(bounds, tokens::kRadiusControl, flags);',
                'CreateRoundedRectBackground(FaintFill(provider, 0x0F), kControlRadius)',
                'SetBorder(views::CreateEmptyBorder(gfx::Insets(0)));',
                'SetBorder(views::CreateEmptyBorder(gfx::Insets::VH(tokens::kSpacing4, 1)));',
                'base::TimeDelta duration = tokens::kFade.duration;',
                '// Fades over base::Milliseconds(100), as Dia.',
                ' * corner radius 12',
                '#include "ui/gfx/geometry/insets.h"',
                'constexpr int kMaxRows = 12;',
        ]:
            with self.subTest(line=line):
                self.assertEqual(self.kinds(line), [])

    def test_only_durations_can_be_excused(self):
        self.assertEqual(
            self.kinds('constexpr base::TimeDelta kTimeout = base::Seconds(30);  '
                       '// motion-lint: not motion (network timeout)'), [])
        self.assertEqual(
            self.kinds('constexpr base::TimeDelta kTimeout = base::Seconds(30);  '
                       '// motion-lint: not motion'), ['duration'])
        self.assertEqual(
            self.kinds('constexpr int kPadding = 4;  // motion-lint: not motion (why)'),
            ['padding'])

    def test_css(self):
        cases = {
            'transition: opacity 150ms ease;': ['duration', 'curve'],
            'transition: opacity var(--rac-motion-fade);': [],
            'transition: rotate 150ms var(--ease-out);': ['duration'],
            'animation: spin 1.88s linear infinite;': ['duration'],
            '--ease-out: cubic-bezier(0.23, 1, 0.32, 1);': ['curve'],
            'border-radius: 8px;': ['radius'],
            'border-radius: 50%;': [],
            'border-top-left-radius: 4px;': ['radius'],
            'border-radius: var(--rac-radius-control);': [],
            '--radius-card: 10px;': ['radius'],
            'padding: 0;': [],
            'padding: 0 var(--rac-spacing-8);': [],
            'padding: 4px var(--rac-spacing-8);': ['padding'],
            'padding-inline: 14px;': ['padding'],
            'gap: 6px;': ['gap'],
            'gap: 0.25rem;': ['gap'],
            'row-gap: calc(var(--rac-spacing-4) * 2);': [],
            'inset: 0;': [],
            'inset-inline-start: 8px;': ['inset'],
            'box-shadow: inset 0 1px 0 var(--rac-hairline);': [],
            '/* padding: 8px; */': [],
            ' * transition 150ms ease': [],
            'transition-duration: 0ms;': [],
        }
        for line, kinds in cases.items():
            with self.subTest(line=line):
                self.assertEqual(self.kinds(line, CSS), kinds)

    def test_script(self):
        path = 'chrome/browser/resources/rac_ai/app.ts'
        self.assertEqual(
            self.kinds("{duration: 160, easing: 'cubic-bezier(0.2, 0, 0, 1)'});", path),
            ['duration', 'curve'])
        self.assertEqual(self.kinds('setTimeout(() => this.close(), 300);', path), [])

    def test_scope(self):
        self.assertTrue(motion_lint.in_scope(VIEW))
        self.assertTrue(motion_lint.in_scope('ui/views/controls/button/button.cc'))
        self.assertTrue(motion_lint.in_scope(CSS))
        self.assertTrue(motion_lint.in_scope('ui/webui/resources/cr_elements/cr_button.css'))
        for path in [
                'chrome/browser/ui/views/rac/rac_tokens.h',
                'ui/webui/resources/css/rac_tokens.css',
                'chrome/browser/ui/views/rac/motion/rac_spring_unittest.cc',
                'chrome/browser/ui/views/rac/motion/rac_motion.cc',
                'chrome/browser/rac/agent/action_guard.cc',
                'chrome/test/data/webui/rac/app_test.ts',
                'chrome/browser/ui/views/rac/BUILD.gn',
        ]:
            with self.subTest(path=path):
                self.assertFalse(motion_lint.in_scope(path))


class PatchTest(unittest.TestCase):

    def find(self, *patches):
        return [f.key() for f in motion_lint.find_literals(list(patches))]

    def test_added_lines_only(self):
        text = patch(VIEW,
                     added=['constexpr int kGap = 6;'],
                     removed=['constexpr int kOldGap = 4;'])
        self.assertEqual(self.find(('rac/a/one.patch', text)),
                         [('gap', VIEW, 'constexpr int kGap = 6;')])

    def test_later_patches_take_lines_back(self):
        first = patch(VIEW, added=['constexpr int kGap = 6;'], new=True)
        second = patch(VIEW,
                       added=['constexpr int kGap = tokens::kSpacing6;'],
                       removed=['constexpr int kGap = 6;'])
        self.assertEqual(self.find(('rac/a/one.patch', first), ('rac/a/two.patch', second)), [])

    def test_deleted_files_take_their_lines(self):
        first = patch(VIEW, added=['constexpr int kGap = 6;'], new=True)
        gone = (f'--- src.orig/{VIEW}\n+++ /dev/null\n@@ -1 +0,0 @@\n'
                '-constexpr int kGap = 6;\n')
        self.assertEqual(self.find(('rac/a/one.patch', first), ('rac/a/two.patch', gone)), [])

    def test_removed_line_that_looks_like_a_header(self):
        # Removing "-- 8px" shows as "--- 8px"; it isn't a new file header.
        text = (f'--- src.orig/{CSS}\n+++ src/{CSS}\n@@ -1,2 +1,2 @@\n'
                '--- old: 8px;\n'
                '+  gap: 6px;\n')
        self.assertEqual(self.find(('rac/a/one.patch', text)), [('gap', CSS, 'gap: 6px;')])

    def test_blank_lines_in_a_hunk(self):
        text = patch(VIEW, added=['constexpr int kGap = 6;']) + '\n'
        self.assertEqual(len(self.find(('rac/a/one.patch', text))), 1)

    def test_dev_patches_are_exempt(self):
        text = patch(VIEW, added=['constexpr base::TimeDelta kWait = base::Milliseconds(50);'])
        self.assertEqual(self.find(('rac/dev/harness.patch', text)), [])
        self.assertEqual(len(self.find(('rac/look/thing.patch', text))), 1)


class AllowlistTest(unittest.TestCase):

    def test_compare(self):
        finding = motion_lint.Finding('gap', VIEW, 'constexpr int kGap = 6;', 'rac/a.patch')
        allowed = Counter({finding.key(): 1, ('radius', VIEW, 'gone'): 1})
        new, stale = motion_lint.compare([finding, finding], allowed)
        self.assertEqual(new, [finding])
        self.assertEqual(stale, [('radius', VIEW, 'gone')])

    def test_growth_is_per_file_and_kind(self):
        old = Counter({('gap', VIEW, 'a = 6;'): 1})
        self.assertEqual(motion_lint.growth(old, Counter({('gap', VIEW, 'a=6;'): 1})), [])
        self.assertEqual(motion_lint.growth(old, Counter({('gap', VIEW, 'a = 6;'): 2})),
                         [('gap', VIEW, 1, 2)])
        self.assertEqual(motion_lint.growth(old, Counter({('gap', CSS, 'a = 6;'): 1})),
                         [('gap', CSS, 0, 1)])

    def test_round_trip(self):
        finding = motion_lint.Finding('gap', VIEW, 'constexpr int kGap = 6;', 'rac/a.patch')
        text = motion_lint.render_allowlist([finding])
        self.assertEqual(motion_lint.read_allowlist(text), Counter({finding.key(): 1}))
        with self.assertRaises(ValueError):
            motion_lint.read_allowlist('margin\tx\ty\n')


class CommandTest(unittest.TestCase):

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='rac-test-motion-lint-')
        self.addCleanup(temporary.cleanup)
        self.folder = Path(temporary.name)
        self.allowlist = self.folder / 'allowlist.txt'
        self.patch = self.folder / 'one.patch'

    def lint(self, *args):
        return subprocess.run(
            [sys.executable,
             str(SCRIPT), '--allowlist',
             str(self.allowlist), *args,
             str(self.patch)],
            capture_output=True,
            text=True,
            check=False)

    def write(self, *lines):
        self.patch.write_text(patch(VIEW, added=lines, new=True))

    def test_allowlist_only_shrinks(self):
        self.write('constexpr int kGap = 6;', 'constexpr int kPadding = 4;')
        self.assertEqual(self.lint().returncode, 1)
        self.assertEqual(self.lint('--init').returncode, 0)
        self.assertEqual(self.lint('--init').returncode, 1)
        self.assertEqual(self.lint().returncode, 0)

        # A new literal fails, and --refresh won't take it in.
        self.write('constexpr int kGap = 6;', 'constexpr int kPadding = 4;',
                   'constexpr int kOtherGap = 8;')
        result = self.lint()
        self.assertEqual(result.returncode, 1)
        self.assertIn('constexpr int kOtherGap = 8;', result.stdout)
        self.assertEqual(self.lint('--refresh').returncode, 1)

        # Fixing one leaves a stale entry, which --refresh drops.
        self.write('constexpr int kGap = 6;', 'constexpr int kPadding = tokens::kSpacing4;')
        self.assertEqual(self.lint().returncode, 1)
        self.assertEqual(self.lint('--refresh').returncode, 0)
        self.assertEqual(self.lint().returncode, 0)
        self.assertEqual(len(motion_lint.read_allowlist(self.allowlist.read_text())), 1)

        # Rewording an allowed line keeps its file's count, so it may refresh.
        self.write('constexpr int kGap =  6;  // Wider.')
        self.assertEqual(self.lint('--refresh').returncode, 0)

    def test_drafts_as_files(self):
        folder = self.folder / 'drafts' / 'sidebar'
        folder.mkdir(parents=True)
        (folder / 'rac_thing.cc').write_text('constexpr int kGap = 6;\n')
        (folder / 'rac_thing_unittest.cc').write_text('constexpr int kGap = 6;\n')
        result = subprocess.run([
            sys.executable,
            str(SCRIPT), '--allowlist',
            str(self.allowlist), '--files',
            str(self.folder / 'drafts'), '--prefix', 'chrome/browser/ui/views/rac'
        ],
                                capture_output=True,
                                text=True,
                                check=False)
        self.assertEqual(result.returncode, 1)
        self.assertIn('chrome/browser/ui/views/rac/sidebar/rac_thing.cc', result.stdout)
        self.assertNotIn('unittest', result.stdout)


class RepositoryTest(unittest.TestCase):

    def test_rac_patches_match_the_allowlist(self):
        result = subprocess.run([sys.executable, str(SCRIPT)],
                                capture_output=True,
                                text=True,
                                check=False)
        self.assertEqual(result.returncode, 0, result.stdout)


if __name__ == '__main__':
    unittest.main()
