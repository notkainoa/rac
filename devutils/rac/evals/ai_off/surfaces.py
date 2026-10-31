# Copyright 2026 The rac Authors
# SPDX-License-Identifier: GPL-3.0-or-later
"""The surfaces to capture with AI off (surfaces.json), and what to do with
what is captured.

A driver follows each surface's `how`, writes a screenshot by launching rac
with `--rac-window-screenshot=<path>` (rac writes its own window PNG after
the first paint; `screencapture -l` of another app is blank on macOS 26), and,
for WebUI pages, also reads the page text through DevTools. The text goes
through check_text(); native surfaces (menus, context menus, the pull handle)
are judged from the screenshot against `must_not_show`.
"""

import json
import os
import re

try:
    from . import checks
except ImportError:  # run as a script: ai_off/ itself is on sys.path
    import checks

HERE = os.path.dirname(os.path.abspath(__file__))
SURFACES_JSON = os.path.join(HERE, "surfaces.json")
REQUIRED = ("id", "how", "must_not_show")
OPTIONAL = {"launch_flags": list, "capture": str, "url": str, "allowed_phrases": list}
CAPTURES = ("screenshot", "devtools+screenshot")
SCREENSHOT_FLAG = "--rac-window-screenshot="


def validate(surfaces):
    """Problems with a list of surface dicts (empty = valid): required keys,
    types, unique kebab-case ids, a known `capture`."""
    problems, seen = [], set()
    if not isinstance(surfaces, list) or not surfaces:
        return ["surfaces must be a non-empty list"]
    for i, s in enumerate(surfaces):
        if not isinstance(s, dict):
            problems.append(f"surface {i} is not an object")
            continue
        sid = s.get("id")
        label = f"surface {sid!r}" if isinstance(sid, str) else f"surface {i}"
        for key in REQUIRED:
            if key not in s:
                problems.append(f"{label}: missing {key!r}")
        if isinstance(sid, str):
            if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", sid):
                problems.append(f"{label}: id must be kebab-case")
            if sid in seen:
                problems.append(f"{label}: duplicate id")
            seen.add(sid)
        elif "id" in s:
            problems.append(f"{label}: id must be a string")
        if "how" in s and not (isinstance(s["how"], str) and s["how"].strip()):
            problems.append(f"{label}: how must be a non-empty string")
        mns = s.get("must_not_show")
        if "must_not_show" in s and not (isinstance(mns, list) and mns and
                                         all(isinstance(x, str) and x for x in mns)):
            problems.append(f"{label}: must_not_show must be a non-empty list of strings")
        for key, typ in OPTIONAL.items():
            if key in s and not isinstance(s[key], typ):
                problems.append(f"{label}: {key} must be a {typ.__name__}")
        for key in ("launch_flags", "allowed_phrases"):
            if isinstance(s.get(key), list) and not all(isinstance(x, str) for x in s[key]):
                problems.append(f"{label}: {key} must hold strings")
        if "capture" in s and s["capture"] not in CAPTURES:
            problems.append(f"{label}: capture must be one of {CAPTURES}")
        for key in s:
            if key not in REQUIRED and key not in OPTIONAL:
                problems.append(f"{label}: unknown key {key!r}")
    return problems


def load(path=SURFACES_JSON):
    """The surfaces from surfaces.json. Raises ValueError if they are invalid."""
    with open(path, encoding="utf-8") as f:
        surfaces = json.load(f)["surfaces"]
    problems = validate(surfaces)
    if problems:
        raise ValueError("invalid surfaces: " + "; ".join(problems))
    return surfaces


def plan_outputs(surfaces, out_dir):
    """Where each surface's files go: <out_dir>/NN-<id>.png and, for surfaces
    read through DevTools, NN-<id>.txt. `launch_flags` gains the
    --rac-window-screenshot flag with the absolute PNG path. out_dir must be
    absolute (rac resolves the path itself, not relative to this process)."""
    if not os.path.isabs(out_dir):
        raise ValueError("out_dir must be an absolute path")
    plan = []
    for n, s in enumerate(surfaces, 1):
        stem = os.path.join(out_dir, f"{n:02d}-{s['id']}")
        png = stem + ".png"
        plan.append({"id": s["id"], "screenshot": png,
                     "text": stem + ".txt" if s.get("capture") == "devtools+screenshot" else None,
                     "launch_flags": list(s.get("launch_flags", [])) + [SCREENSHOT_FLAG + png]})
    return plan


# One script for DevTools: the page text including shadow roots, which WebUI
# pages (settings, new tab) put nearly everything in.
PAGE_TEXT_JS = """
(() => {
  const out = [];
  const walk = (node) => {
    if (node.nodeType === Node.TEXT_NODE) { out.push(node.textContent); return; }
    if (node.nodeType === Node.ELEMENT_NODE) {
      if (['SCRIPT', 'STYLE'].includes(node.tagName)) return;
      for (const a of ['aria-label', 'title', 'placeholder', 'label']) {
        if (node.getAttribute && node.getAttribute(a)) out.push(node.getAttribute(a));
      }
      if (node.shadowRoot) walk(node.shadowRoot);
    }
    for (const c of node.childNodes) walk(c);
  };
  walk(document.documentElement);
  return out.join('\\n');
})()
"""


def by_id(surfaces):
    return {s["id"]: s for s in surfaces}


def check_text(surface, text):
    """Problems in the text read from one surface: forbidden labels, after
    the surface's `allowed_phrases` and stock-Chromium look-alikes are
    ignored. Surfaces in checks.ALLOWED_SURFACES always pass. Text is
    collected by a driver (PAGE_TEXT_JS over DevTools); native surfaces have
    none and are judged from the screenshot."""
    ignore = tuple(checks.BENIGN_PHRASES) + tuple(surface.get("allowed_phrases", ()))
    return checks.check_surface_text(surface["id"], text, ignore=ignore)
