# Copyright 2026 The rac Authors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Loads fixtures/<id>/ into a Variant. The format is described in README.md
and VARIANTS.md; this module is the one place that reads it."""

import copy
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES = os.path.join(HERE, "fixtures")

KINDS = ("attack", "probe", "budget", "failclosed", "stub")
INHERITED = ("pages", "model", "origins", "routes", "turns", "secret", "attacker",
             "leak", "prefs", "level", "user_answer", "expect", "title", "docs")


class VariantError(Exception):
    pass


def _read_json(path):
    with open(path) as f:
        return json.load(f)


def list_variant_ids(root=FIXTURES):
    if not os.path.isdir(root):
        return []
    return sorted(d for d in os.listdir(root)
                  if os.path.isfile(os.path.join(root, d, "variant.json")))


def load_variant(variant_id, root=FIXTURES, _seen=()):
    """Returns the variant dict with `extends` resolved and `dir` fields set:
    `dir` is where this variant's own files live, `pages_dir` and `model_path`
    point at the directory that supplied them (a parent's, if inherited)."""
    if variant_id in _seen:
        raise VariantError(f"extends cycle at {variant_id}")
    vdir = os.path.join(root, variant_id)
    path = os.path.join(vdir, "variant.json")
    if not os.path.isfile(path):
        raise VariantError(f"no such variant: {variant_id}")
    raw = _read_json(path)
    if raw.get("id") != variant_id:
        raise VariantError(f"{path}: id must be {variant_id!r}")
    merged = {}
    parent = raw.get("extends")
    if parent:
        merged = load_variant(parent, root, _seen + (variant_id,))
        merged = copy.deepcopy(merged)
    for key, value in raw.items():
        if key in ("prefs", "expect", "origins", "leak", "attacker") and isinstance(merged.get(key), dict) \
                and isinstance(value, dict):
            merged[key] = {**merged[key], **value}
        else:
            merged[key] = value
    merged["id"] = variant_id
    merged["dir"] = vdir
    own_pages = os.path.isdir(os.path.join(vdir, "pages")) or os.path.isfile(os.path.join(vdir, "fixture.py"))
    if own_pages or "pages_dir" not in merged:
        merged["pages_dir"] = vdir
    merged["model_path"] = (os.path.join(vdir, "model.json")
                            if os.path.isfile(os.path.join(vdir, "model.json"))
                            else merged.get("model_path"))
    merged.setdefault("level", "auto")
    merged.setdefault("user_answer", "deny")
    merged.setdefault("prefs", {})
    merged.setdefault("expect", {})
    merged.setdefault("attacker", {})
    merged.setdefault("leak", {"mode": "secret"})
    return merged


def validate_variant(v):
    """Returns a list of problems; empty means the variant is well formed."""
    problems = []
    if v.get("kind") not in KINDS:
        problems.append(f"kind must be one of {KINDS}")
    if v.get("kind") == "stub":
        return problems
    for key in ("title", "origins", "turns", "docs"):
        if not v.get(key):
            problems.append(f"missing {key}")
    if not v.get("model_path") or not os.path.isfile(v.get("model_path") or ""):
        problems.append("missing model.json")
    for name, spec in (v.get("origins") or {}).items():
        if not re.fullmatch(r"[a-z][a-z0-9]*", name):
            problems.append(f"origin name {name!r} must be lowercase letters and digits")
        if not isinstance(spec, dict) or not re.fullmatch(r"[a-z][a-z0-9-]*", spec.get("host", "")):
            problems.append(f"origin {name}: host must be a plain label like 'mail'")
    for i, turn in enumerate(v.get("turns") or []):
        if not turn.get("user"):
            problems.append(f"turn {i}: missing user message")
        for ref in turn.get("open", []) + turn.get("attach", []):
            origin = ref.split(":", 1)[0]
            if origin not in (v.get("origins") or {}):
                problems.append(f"turn {i}: unknown origin in {ref!r}")
    leak = v.get("leak", {})
    if leak.get("mode") not in ("secret", "chars", "any_hit"):
        problems.append("leak.mode must be secret, chars or any_hit")
    if leak.get("mode") in ("secret", "chars") and not v.get("secret"):
        problems.append("leak mode needs a secret")
    if v.get("kind") in ("attack", "probe", "failclosed"):
        scope = v.get("attacker", {})
        if not scope.get("origins") and not scope.get("paths"):
            problems.append("attack variants need attacker.origins or attacker.paths")
    if v.get("user_answer") not in ("deny", "allow_once"):
        problems.append("user_answer must be deny or allow_once")
    if v.get("kind") in ("attack", "failclosed") and v.get("user_answer") != "deny":
        problems.append("attack runs always answer deny")
    if v.get("kind") == "budget" and v.get("user_answer") != "allow_once":
        problems.append("budget runs always answer allow_once")
    return problems


def load_all(root=FIXTURES):
    return [load_variant(i, root) for i in list_variant_ids(root)]
