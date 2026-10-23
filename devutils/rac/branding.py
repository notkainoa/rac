#!/usr/bin/env python3
"""Generates rac's in-browser branding from the app icon.

Helium ships its own logo images and vector icons. rac replaces them with
files built here from two sources in resources/assets:

- AppIcon.icon/Assets/wordmark.svg, the "rac" wordmark
- legacy.png, the 1024 px render of the app icon

The outputs go to resources/branding, and resources/branding.txt copies
them over Helium's after Helium's resources are applied. Run it again
whenever the icon changes.

Needs Pillow: pip install Pillow
"""

import re
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / 'resources' / 'assets'
WORDMARK = ASSETS / 'AppIcon.icon' / 'Assets' / 'wordmark.svg'
ICON = ASSETS / 'legacy.png'
OUT = ROOT / 'resources' / 'branding'

# Background of the flat logo variants, sampled from the app icon
NAVY = (0x0A, 0x12, 0x4A)
WHITE = (0xFB, 0xFC, 0xFF)
SUPERSAMPLE = 8
CURVE_STEPS = 12


def read_wordmark():
    """Returns the wordmark as a list of contours in the SVG's own units.

    Each contour is a list of ('M'|'L'|'Q', points) segments with y pointing
    down. The SVG is a font outline: an outer flip and one translate per
    glyph, absolute M, L, H, V, Q and Z commands only."""
    svg = WORDMARK.read_text(encoding='utf-8')
    outer = re.search(r'<g transform="translate\(([-\d.]+) ([-\d.]+)\) scale\(1 -1\)"', svg)
    ox, oy = float(outer.group(1)), float(outer.group(2))
    contours = []
    for tx, data in re.findall(
            r'<path transform="translate\(([-\d.]+) [-\d.]+\)" d="([^"]+)"', svg):
        tx = float(tx)
        point = lambda x, y: (x + tx + ox, oy - y)
        tokens = re.findall(r'[MLHVQZ]|-?\d*\.?\d+', data)
        i, cur, contour = 0, (0.0, 0.0), None
        cmd = None
        while i < len(tokens):
            if tokens[i].isalpha():
                cmd = tokens[i]
                i += 1
                if cmd == 'Z':
                    contours.append(contour)
                    contour = None
                    continue
            nums = lambda n: [float(t) for t in tokens[i:i + n]]
            if cmd == 'M':
                x, y = nums(2); i += 2
                cur = (x, y); contour = [('M', [point(x, y)])]
            elif cmd == 'L':
                x, y = nums(2); i += 2
                cur = (x, y); contour.append(('L', [point(x, y)]))
            elif cmd == 'H':
                (x,) = nums(1); i += 1
                cur = (x, cur[1]); contour.append(('L', [point(*cur)]))
            elif cmd == 'V':
                (y,) = nums(1); i += 1
                cur = (cur[0], y); contour.append(('L', [point(*cur)]))
            elif cmd == 'Q':
                cx, cy, x, y = nums(4); i += 4
                cur = (x, y); contour.append(('Q', [point(cx, cy), point(x, y)]))
            else:
                raise ValueError(f'unsupported path command {cmd!r}')
    return contours


def bounds(contours):
    pts = [p for c in contours for _, ps in c for p in ps]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def fit(contours, box):
    """Scales and moves contours to sit centred in box (x0, y0, x1, y1)."""
    bx0, by0, bx1, by1 = bounds(contours)
    s = min((box[2] - box[0]) / (bx1 - bx0), (box[3] - box[1]) / (by1 - by0))
    dx = box[0] + ((box[2] - box[0]) - (bx1 - bx0) * s) / 2 - bx0 * s
    dy = box[1] + ((box[3] - box[1]) - (by1 - by0) * s) / 2 - by0 * s
    return [[(cmd, [(x * s + dx, y * s + dy) for x, y in ps]) for cmd, ps in c]
            for c in contours]


def polygon(contour):
    pts, cur = [], None
    for cmd, ps in contour:
        if cmd == 'Q':
            (cx, cy), (x, y) = ps
            for k in range(1, CURVE_STEPS + 1):
                t = k / CURVE_STEPS
                pts.append(((1 - t) ** 2 * cur[0] + 2 * (1 - t) * t * cx + t * t * x,
                            (1 - t) ** 2 * cur[1] + 2 * (1 - t) * t * cy + t * t * y))
        else:
            pts.append(ps[0])
        cur = pts[-1]
    return pts


def mask(contours, size):
    """Anti-aliased coverage mask. Glyph contours don't overlap, so XOR-ing
    them gives the same counters as the nonzero rule."""
    w, h = size
    k = SUPERSAMPLE
    out = Image.new('L', (w * k, h * k), 0)
    for c in contours:
        m = Image.new('L', out.size, 0)
        ImageDraw.Draw(m).polygon([(x * k, y * k) for x, y in polygon(c)], fill=255)
        out = ImageChops.logical_xor(out.convert('1'), m.convert('1')).convert('L')
    return out.resize(size, Image.LANCZOS)


def solid(size, rgb, coverage):
    img = Image.new('RGBA', size, rgb + (0,))
    img.putalpha(coverage)
    return img


def lockup(contours, size, rgb, path):
    """The wordmark on a transparent strip, left-aligned like Helium's."""
    w, h = size
    pad = h * 0.16
    placed = fit(contours, (0, pad, w, h - pad))
    bx0, _, _, _ = bounds(placed)
    placed = [[(cmd, [(x - bx0, y) for x, y in ps]) for cmd, ps in c] for c in placed]
    solid(size, rgb, mask(placed, size)).save(path)


def tile(contours, size, inset):
    return fit(contours, (inset, inset, size - inset, size - inset))


def icon_commands(contours):
    lines = []
    for c in contours:
        for cmd, ps in c:
            nums = ', '.join(f'{v:.2f}f' for p in ps for v in p)
            lines.append({'M': 'MOVE_TO', 'L': 'LINE_TO', 'Q': 'QUADRATIC_TO'}[cmd] + ', ' + nums + ',')
        lines.append('CLOSE,')
    lines[-1] = 'CLOSE'
    return lines


HEADER = ('// Copyright 2026 The rac Authors\n'
          '// You can use, redistribute, and/or modify this source code under\n'
          '// the terms of the GPL-3.0 license that can be found in the LICENSE file.\n\n')


def svg_path(contours):
    out = []
    for c in contours:
        for cmd, ps in c:
            out.append(cmd + ' '.join(f'{v:.1f}' for p in ps for v in p))
        out.append('Z')
    return ''.join(out)


def main():
    words = read_wordmark()
    OUT.mkdir(exist_ok=True)

    # App icon at the sizes Helium generates from raw.png, cropped to the tile
    icon = Image.open(ICON).convert('RGBA')
    icon = icon.crop(icon.getchannel('A').point(lambda a: 255 if a > 8 else 0).getbbox())
    (OUT / 'product_icon').mkdir(exist_ok=True)
    for s in (16, 24, 32, 48, 64, 128, 256):
        icon.resize((s, s), Image.LANCZOS).save(OUT / 'product_icon' / f'{s}x{s}.png')

    # Wordmark lockups for light and dark backgrounds
    for name, rgb in (('product_logo', (0, 0, 0)), ('product_logo_white', (255, 255, 255))):
        lockup(words, (140, 32), rgb, OUT / f'{name}.png')
        lockup(words, (280, 64), rgb, OUT / f'{name}_200.png')

    # New Tab page favicon, in the grey Chromium uses for its page icons
    for s in (16, 32):
        solid((s, s), (0x3C, 0x40, 0x43), mask(tile(words, s, s / 16), (s, s))).save(
            OUT / f'favicon_ntp_{s}.png')

    # macOS menu bar template: black on transparent
    solid((22, 22), (0, 0, 0), mask(tile(words, 22, 1), (22, 22))).save(
        OUT / 'product_logo_22_mono.png')

    # Rounded tile with the wordmark, for WebUI
    color = tile(words, 256, 40)
    (OUT / 'product_logo.svg').write_text(
        '<svg width="256" height="256" viewBox="0 0 256 256" fill="none" '
        'xmlns="http://www.w3.org/2000/svg">'
        f'<rect width="256" height="256" rx="67" fill="#{"%02X%02X%02X" % NAVY}"/>'
        f'<path d="{svg_path(color)}" fill="#{"%02X%02X%02X" % WHITE}"/></svg>\n',
        encoding='utf-8')

    # Monochrome vector icon (tinted by the caller)
    (OUT / 'product_logo.icon').write_text(
        HEADER + 'CANVAS_DIMENSIONS, 56,\nFILL_RULE_NONZERO,\n' +
        '\n'.join(icon_commands(tile(words, 56, 1))) + '\n', encoding='utf-8')

    # Colour vector icon: navy tile, white wordmark
    (OUT / 'product_logo_color.icon').write_text(
        HEADER + 'CANVAS_DIMENSIONS, 256,\nNEW_PATH,\n'
        'PATH_COLOR_ARGB, 0xFF, 0x%02X, 0x%02X, 0x%02X,\n' % NAVY +
        'ROUND_RECT, 0, 0, 256, 256, 67,\nNEW_PATH,\nFILL_RULE_NONZERO,\n'
        'PATH_COLOR_ARGB, 0xFF, 0x%02X, 0x%02X, 0x%02X,\n' % WHITE +
        '\n'.join(icon_commands(color)) + '\n', encoding='utf-8')
    return 0


if __name__ == '__main__':
    sys.exit(main())
