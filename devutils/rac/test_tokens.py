#!/usr/bin/env python3

# Copyright 2026 The rac Authors
# You can use, redistribute, and/or modify this source code under
# the terms of the GPL-3.0 license that can be found in the LICENSE file.
"""Tests for tokens.py with fixture headers. Only temporary folders.

Run from the repository root:
    python3 -m unittest discover -s devutils/rac -p 'test_*.py' -v
"""

from pathlib import Path
import math
import subprocess
import sys
import tempfile
import unittest

import tokens

SCRIPT = Path(__file__).resolve().parent / 'tokens.py'

HEADER = """\
#include "base/time/time.h"

namespace rac {

struct Curve {
  double x1, y1, x2, y2;
  gfx::Tween::Type tween;
};

namespace tokens {

// Curves.

// Material 3 standard.
inline constexpr Curve kEaseStandard{0.2, 0, 0, 1, gfx::Tween::FAST_OUT_SLOW_IN_3};

// A fade.
inline constexpr Timing kFade{base::Milliseconds(100), kEaseStandard};
inline constexpr Timing kFadeAgain = kFade;
inline constexpr Timing kInline{base::Milliseconds(80),
                                {0, 0, 0.58, 1, gfx::Tween::EASE_OUT}};
inline constexpr base::TimeDelta kLoopStep = base::Hertz(15);
inline constexpr Spring kSpringPage{0.25, 1.0};
inline constexpr RestRule kSpringRest{0.25f, 15.0f, base::Hertz(240),
                                      base::Milliseconds(1500)};
inline constexpr int kRadius8 = 8;
inline constexpr int kRadiusControl = kRadius8;
inline constexpr int kFontWeightMedium = 500;
// A pill's radius is half its height.
constexpr int PillRadius(int height) {
  return height / 2;
}
// rac-css: --rac-radius-pill: 9999px;

}  // namespace tokens
}  // namespace rac
"""


def wrap(body):
    return f'namespace rac {{\nnamespace tokens {{\n{body}\n}}  // namespace tokens\n}}\n'


def by_name(items):
    return {item.name: item for item in items if not isinstance(item, str)}


class ParseTest(unittest.TestCase):

    def setUp(self):
        self.items = tokens.parse_header(HEADER)
        self.tokens = by_name(self.items)

    def test_kebab(self):
        self.assertEqual(tokens.kebab('kEaseFadeOut'), 'ease-fade-out')
        self.assertEqual(tokens.kebab('kRadius10'), 'radius-10')
        self.assertEqual(tokens.kebab('kSpacing2'), 'spacing-2')
        self.assertEqual(tokens.kebab('kFontSizeRow'), 'font-size-row')

    def test_reads_every_kind(self):
        t = self.tokens
        self.assertEqual(t['kEaseStandard'].value, {
            'bezier': (0.2, 0, 0, 1),
            'tween': 'FAST_OUT_SLOW_IN_3'
        })
        self.assertEqual(t['kFade'].value['duration'], 100_000)
        self.assertEqual(t['kFade'].value['curve_name'], 'kEaseStandard')
        self.assertEqual(t['kInline'].value['curve']['bezier'], (0, 0, 0.58, 1))
        # base::Hertz rounds down to whole microseconds.
        self.assertEqual(t['kLoopStep'].value, 66_666)
        self.assertEqual(t['kSpringPage'].value, (0.25, 1.0))
        self.assertEqual(t['kSpringRest'].value, (0.25, 15.0, 4166, 1_500_000))
        self.assertEqual(t['kRadiusControl'].value, 8)
        self.assertEqual(t['kRadiusControl'].alias, 'kRadius8')
        self.assertEqual(t['kFadeAgain'].alias, 'kFade')

    def test_keeps_comments_and_skips_functions(self):
        self.assertEqual(self.tokens['kEaseStandard'].comment, 'Material 3 standard.')
        self.assertEqual(self.tokens['kFade'].comment, 'A fade.')
        self.assertNotIn('PillRadius', self.tokens)
        self.assertIn('--rac-radius-pill: 9999px;', self.items)

    def test_rejects_what_it_cannot_read(self):
        bad = [
            'inline constexpr float kRadius3 = 3.5;',
            'inline constexpr int kRadius3 = 3.5;',
            'inline constexpr Spring kSpringBad{0, 1};',
            'inline constexpr Curve kEaseBad{0, 0, 1};',
            'constexpr int kRadius4 = 4;',
            'inline constexpr int kRadius4 = 4;\ninline constexpr int kRadius4 = 4;',
            'inline constexpr int kRadius4 = 4',
        ]
        for body in bad:
            with self.subTest(body=body), self.assertRaises(tokens.TokenError):
                tokens.parse_header(wrap(body))
        with self.assertRaises(tokens.TokenError):
            tokens.parse_header('namespace rac {}\n')

    def test_ints_need_a_unit_from_their_name(self):
        items = tokens.parse_header(wrap('inline constexpr int kWidth = 4;'))
        with self.assertRaises(tokens.TokenError):
            tokens.render_css(items)


class CssTest(unittest.TestCase):

    def setUp(self):
        self.css = tokens.render_css(tokens.parse_header(HEADER))

    def test_properties(self):
        for line in [
                '  --rac-ease-standard: cubic-bezier(0.2, 0, 0, 1);',
                '  --rac-duration-fade: 100ms;',
                '  --rac-motion-fade: var(--rac-duration-fade) var(--rac-ease-standard);',
                '  --rac-duration-fade-again: 100ms;',
                '  --rac-motion-fade-again: var(--rac-motion-fade);',
                '  --rac-motion-inline: var(--rac-duration-inline) cubic-bezier(0, 0, 0.58, 1);',
                '  --rac-duration-loop-step: 66.666ms;',
                '  --rac-spring-page-duration: 368ms;',
                '  --rac-spring-page: var(--rac-spring-page-duration) '
                'var(--rac-spring-page-easing);',
                '  --rac-radius-8: 8px;',
                '  --rac-radius-control: var(--rac-radius-8);',
                '  --rac-font-weight-medium: 500;',
                '  --rac-radius-pill: 9999px;',
                '  /* Material 3 standard. */',
        ]:
            self.assertIn(line + '\n', self.css)

    def test_rest_rules_have_no_css(self):
        self.assertNotIn('rest', self.css.replace('--rac-', ''))

    def test_generated_banner(self):
        self.assertIn('Generated by devutils/rac/tokens.py', self.css)
        self.assertTrue(self.css.endswith('}\n'))


class SpringTest(unittest.TestCase):

    def test_closed_forms(self):
        w = 2 * math.pi / 0.25
        self.assertAlmostEqual(tokens.spring_value(0.25, 1.0, 0.1),
                               1 - (1 + w * 0.1) * math.exp(-w * 0.1))
        for ratio in (0.6, 0.85, 1.0, 1.6):
            self.assertEqual(tokens.spring_value(0.2, ratio, 0), 0)
            self.assertAlmostEqual(tokens.spring_value(0.2, ratio, 5), 1)
        # Near 1, the other forms agree with the critical one.
        for t in (0.02, 0.08, 0.2):
            self.assertAlmostEqual(tokens.spring_value(0.25, 1 - 1e-7, t),
                                   tokens.spring_value(0.25, 1.0, t),
                                   places=6)

    def test_settle_matches_plan_two(self):
        # Plan 02: within 1% at 264 ms (page) and 192 ms (reveal), to the ms.
        self.assertEqual(tokens.spring_settle_ms(0.25, 1.0, 0.01), 265)
        self.assertEqual(tokens.spring_settle_ms(0.185, 0.77, 0.01), 193)

    def test_linear_stays_close_to_the_spring(self):
        for response, ratio in ((0.25, 1.0), (0.2, 0.85), (0.185, 0.77), (0.2, 0.6)):
            duration_ms, points = tokens.spring_points(response, ratio)
            self.assertEqual(points[0], (0.0, 0.0))
            self.assertEqual(points[-1], (1.0, 1.0))
            xs = [x for x, _ in points]
            self.assertEqual(xs, sorted(xs))
            for i in range(1001):
                x = i / 1000
                for (x0, y0), (x1, y1) in zip(points, points[1:]):
                    if x0 <= x <= x1:
                        y = y0 + (y1 - y0) * (x - x0) / (x1 - x0)
                        break
                exact = tokens.spring_value(response, ratio, x * duration_ms / 1000)
                if x < 1:
                    self.assertLess(abs(y - exact), 0.0035, (response, ratio, x))


class CommandTest(unittest.TestCase):

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='rac-test-tokens-')
        self.addCleanup(temporary.cleanup)
        self.folder = Path(temporary.name)
        self.header = self.folder / 'rac_tokens.h'
        self.css = self.folder / 'rac_tokens.css'
        self.header.write_text(HEADER)

    def run_tokens(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *args],
                              capture_output=True,
                              text=True,
                              check=False)

    def test_write_then_check(self):
        args = ['--header', str(self.header), '--css', str(self.css)]
        self.assertEqual(self.run_tokens('--check', *args).returncode, 1)
        self.assertEqual(self.run_tokens(*args).returncode, 0)
        self.assertEqual(self.run_tokens('--check', *args).returncode, 0)
        self.header.write_text(HEADER.replace('Milliseconds(100)', 'Milliseconds(90)'))
        result = self.run_tokens('--check', *args)
        self.assertEqual(result.returncode, 1)
        self.assertIn('+  --rac-duration-fade: 90ms;', result.stdout)

    def test_check_from_patches(self):
        patches = self.folder / 'patches' / 'rac' / 'look'
        patches.mkdir(parents=True)
        css = tokens.render_css(tokens.parse_header(HEADER))

        def new_file(path, text):
            lines = text.splitlines()
            return (f'Index: src/{path}\n'
                    '===================================================================\n'
                    '--- /dev/null\t1970-01-01 00:00:00.000000000 +0000\n'
                    f'+++ src/{path}\t2026-10-27 00:00:00.000000000 -0700\n'
                    f'@@ -0,0 +1,{len(lines)} @@\n' + ''.join(f'+{l}\n' for l in lines))

        patch = patches / 'tokens.patch'
        patch.write_text(new_file(tokens.HEADER.as_posix(), HEADER) +
                         new_file(tokens.CSS.as_posix(), css))
        root = str(self.folder / 'patches')
        self.assertEqual(self.run_tokens('--check', '--patches', root).returncode, 0)
        patch.write_text(new_file(tokens.HEADER.as_posix(), HEADER) +
                         new_file(tokens.CSS.as_posix(), css.replace('100ms', '99ms')))
        self.assertEqual(self.run_tokens('--check', '--patches', root).returncode, 1)

    def test_check_from_patches_with_b_paths(self):
        patches = self.folder / 'patches' / 'rac' / 'look'
        patches.mkdir(parents=True)
        css = tokens.render_css(tokens.parse_header(HEADER))

        def new_file(path, text):
            lines = text.splitlines()
            return ('--- /dev/null\n'
                    f'+++ b/{path}\n'
                    f'@@ -0,0 +1,{len(lines)} @@\n' + ''.join(f'+{l}\n' for l in lines))

        patch = patches / 'tokens.patch'
        patch.write_text(new_file(tokens.HEADER.as_posix(), HEADER) +
                         new_file(tokens.CSS.as_posix(), css))
        root = str(self.folder / 'patches')
        self.assertEqual(self.run_tokens('--check', '--patches', root).returncode, 0)
        self.assertEqual(self.run_tokens('--patches', root).returncode, 1)


if __name__ == '__main__':
    unittest.main()
