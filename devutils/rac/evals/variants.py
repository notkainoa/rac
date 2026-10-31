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

# The only prefs a variant may seed: the agent level and the site rules under
# test. Everything else run.py seeds into the profile — AI on, the provider at
# the fake model, the download folder — is a safety pref a variant must never
# override, so flat_prefs refuses any other key.
PREF_KEYS = ("rac.ai.agent_permission_level", "rac.ai.agent_site_rules")

# --variants spec suffixes: the window's appearance and the side panel's
# width, after a base id — "chain-canonical_dark_wide". run.py seeds the
# prefs for them. Order in a spec is free; run_id puts them in this
# canonical order so _wide_dark and _dark_wide name the same run.
APPEARANCE_SUFFIXES = ("light", "dark")
WIDTH_SUFFIXES = ("narrow", "wide")
SUFFIXES = APPEARANCE_SUFFIXES + WIDTH_SUFFIXES


class VariantError(Exception):
    pass


def parse_spec(spec):
    """One --variants item as (base_id, appearance, width):
    "chain-canonical_light_narrow" -> ("chain-canonical", "light", "narrow").
    Either suffix may be left out and the order is free. An empty part, an
    unknown suffix, or a second suffix of one kind is a VariantError."""
    base, *rest = spec.split("_")
    if not base:
        raise VariantError(f"{spec!r}: no variant id")
    appearance = width = None
    for s in rest:
        if s in APPEARANCE_SUFFIXES:
            if appearance is not None:
                raise VariantError(f"{spec!r}: two appearance suffixes")
            appearance = s
        elif s in WIDTH_SUFFIXES:
            if width is not None:
                raise VariantError(f"{spec!r}: two width suffixes")
            width = s
        else:
            raise VariantError(f"{spec!r}: unknown suffix {s!r} "
                               f"(one of {', '.join(SUFFIXES)})")
    return base, appearance, width


def run_id(base, appearance=None, width=None):
    """A suffixed run's canonical name — base plus suffixes, appearance
    then width — used for the record's `variant`, its results file and the
    shot names, so several appearances of one variant can run in a single
    invocation without overwriting each other."""
    parts = [base]
    if appearance:
        parts.append(appearance)
    if width:
        parts.append(width)
    return "-".join(parts)


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
    merged = {}  # a child merges prefs/origins/leak/attacker into its parent's and replaces the rest
    parent = raw.get("extends")
    if parent:
        merged = load_variant(parent, root, _seen + (variant_id,))
        merged = copy.deepcopy(merged)
    for key, value in raw.items():
        if key in ("prefs", "origins", "leak", "attacker") and isinstance(merged.get(key), dict) \
                and isinstance(value, dict):
            merged[key] = {**merged[key], **value}
        else:
            merged[key] = value
    merged["id"] = variant_id
    # The fixture this variant was loaded from. run.py may put a suffixed
    # run name in `id`, but `base_id` always points back at the fixture.
    merged["base_id"] = variant_id
    merged["dir"] = vdir
    own_pages = os.path.isdir(os.path.join(vdir, "pages"))
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
    for key in (v.get("prefs") or {}):
        if key not in PREF_KEYS:
            problems.append(f"prefs key {key!r} is not allowed; a variant may only "
                            f"set {', '.join(PREF_KEYS)}")
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
