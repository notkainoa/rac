#!/usr/bin/env python3
"""Closes rac's welcome tour window in a running browser, for net-capture.

The tour (chrome://setup/?tour) is a views widget, not a Browser, so
Chromium's AppleScript dictionary cannot see it. This asks the browser's
DevTools HTTP endpoint to close the tour's page (/json/close/<id>), which
runs WebContents::ClosePage and ends in the tour's CloseContents handler:
the same path as the page closing itself, and the same outcome as the red
button. Nothing is written to prefs; the browser opens its first window and
the tour stays pending for the next launch.

Usage: close_onboarding.py <user-data-dir> [--wait SECONDS]
Exit 0: the tour page was found and closed. Exit 1: it never appeared or
the endpoint was unreachable (the caller falls back to System Events).
"""
import json
import sys
import time
import urllib.request


def main():
    argv = sys.argv[1:]
    if not argv:
        print('usage: close_onboarding.py <user-data-dir> [--wait N]', file=sys.stderr)
        return 2
    profile, wait = argv[0], 60
    if len(argv) == 3 and argv[1] == '--wait':
        wait = int(argv[2])
    deadline = time.time() + wait
    while time.time() < deadline:
        try:
            with open(f'{profile}/DevToolsActivePort', encoding='utf-8') as f:
                port = int(f.readline().strip())
            with urllib.request.urlopen(f'http://127.0.0.1:{port}/json/list', timeout=5) as r:
                targets = json.load(r)
            for t in targets:
                if t.get('url', '').startswith('chrome://setup'):
                    with urllib.request.urlopen(
                            f'http://127.0.0.1:{port}/json/close/{t["id"]}', timeout=5):
                        pass
                    print(f'closed {t["url"]}')
                    return 0
        except (OSError, ValueError, json.JSONDecodeError):
            pass
        time.sleep(1)
    print('tour page never appeared on the DevTools endpoint', file=sys.stderr)
    return 1


if __name__ == '__main__':
    sys.exit(main())
