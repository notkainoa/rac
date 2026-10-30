#!/usr/bin/env python3

# Copyright 2026 The rac Authors
# You can use, redistribute, and/or modify this source code under
# the terms of the GPL-3.0 license that can be found in the LICENSE file.
"""Reads a --rac-frame-log and says how the sidebar and page moved.

usage: devutils/rac/motion_trace.py LOG [--after TEXT] [--win N] [--ms MS]
                                    [--tsv OUT]

LOG is the JSON-lines file a developer build writes with
--rac-frame-log=PATH. "frame" lines mark every presented frame; "layout"
lines carry the sidebar's and page's bounds in the window as committed,
stamped with the time the frame showing them reached the screen. The trace
starts at the first harness request whose text contains TEXT (default: the
last request), and covers MS milliseconds (default 1000) of window N
(default: window 0).

It prints one row per layout shown: time after the request, the
sidebar's visible left edge and width, and the page's left edge and width.
Then a verdict per element: "snap" if its first frame after the request is
already where it ends, "moves over N frames (T ms)" if it travels, or
"still". A view can be laid out ahead of the frame on screen, so treat
one frame of difference as the tolerance.
"""

import argparse
import json
import sys


def edge(probe):
    if not probe or not probe.get('drawn', True):
        return None
    return probe['x'], probe['w']


def verdict(rows, key):
    values = [r[key] for r in rows]
    if not values:
        return 'no frames'
    final = values[-1]
    changes = [i for i in range(1, len(values)) if values[i] != values[i - 1]]
    if not changes and values[0] == final:
        return 'still' if len(rows) < 2 else f'at final place from frame 0 ({final})'
    last = changes[-1] if changes else 0
    if last <= 0 or (len(changes) == 1 and changes[0] == 1 and values[0] != final):
        return f'snap: final place {final} at {rows[last]["t"]:.1f} ms'
    span = rows[last]['t'] - rows[changes[0] - 1]['t']
    return (f'moves over {last - changes[0] + 2} frames ({span:.0f} ms), '
            f'{values[changes[0] - 1]} -> {final}, settled at '
            f'{rows[last]["t"]:.1f} ms')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('log')
    parser.add_argument('--after', default=None)
    parser.add_argument('--win', type=int, default=0)
    parser.add_argument('--ms', type=float, default=1000)
    parser.add_argument('--tsv')
    args = parser.parse_args()

    events = []
    for line in open(args.log, encoding='utf-8', errors='replace'):
        try:
            events.append(json.loads(line))
        except ValueError:
            continue
    requests = [e for e in events if e.get('ev') == 'req' and
                (args.after is None or args.after in e['line'])]
    if not requests:
        sys.exit('no matching request in the log')
    start = requests[-1]['t_us']
    if args.after is not None:
        start = requests[0]['t_us']
    def window(kind):
        return [e for e in events if e.get('ev') == kind and
                e['win'] == args.win and start <= e['t_us'] <=
                start + args.ms * 1000]
    frames = window('layout')
    presented = window('frame')

    rows = []
    for f in frames:
        rows.append({
            't': (f['t_us'] - start) / 1000,
            'sidebar': edge(f.get('sidebar')),
            'page': edge(f.get('page')),
        })
    out = ['t_ms\tsidebar_x\tsidebar_w\tpage_x\tpage_w']
    for r in rows:
        s = r['sidebar'] or ('-', '-')
        p = r['page'] or ('-', '-')
        out.append(f'{r["t"]:.1f}\t{s[0]}\t{s[1]}\t{p[0]}\t{p[1]}')
    text = '\n'.join(out) + '\n'
    if args.tsv:
        open(args.tsv, 'w').write(text)
    print(text, end='')
    gaps = [b['t'] - a['t'] for a, b in zip(rows, rows[1:])]
    print(f'# request: {requests[0 if args.after else -1]["line"]}')
    print(f'# {len(presented)} frames presented, {len(rows)} layouts, '
          f'in {args.ms:.0f} ms'
          + (f', median layout gap {sorted(gaps)[len(gaps) // 2]:.1f} ms'
             if gaps else ''))
    print(f'# sidebar: {verdict(rows, "sidebar")}')
    print(f'# page:    {verdict(rows, "page")}')


if __name__ == '__main__':
    main()
