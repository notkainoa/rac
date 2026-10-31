# Copyright 2026 The rac Authors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Checks every fixture without a browser: it is well formed, VARIANTS.md and
baseline.json agree with it, and the dry run plays it the way the spec says
(an attack that works against today's guard, and stops against the fix)."""

import json
import os
import re
import unittest

import grade
import run
import variants

ALL = [variants.load_variant(i) for i in variants.list_variant_ids()]
LIVE = [v for v in ALL if v["kind"] != "stub"]
ATTACK_KINDS = ("attack", "failclosed", "probe")
# The stand-in has no JavaScript dialogs, downloads or timers, so these pass
# trivially; only a real run tests them.
SIM_BLIND = {"dialog-trap", "download-silent"}


class FixtureFilesTest(unittest.TestCase):
    def test_the_expected_counts(self):
        kinds = [v["kind"] for v in ALL]
        self.assertEqual({k: kinds.count(k) for k in set(kinds)},
                         {"attack": 17, "failclosed": 4, "probe": 1, "budget": 4, "stub": 6})

    def test_every_fixture_is_well_formed(self):
        for v in ALL:
            with self.subTest(v["id"]):
                self.assertEqual(variants.validate_variant(v), [])

    def test_variants_md_lists_exactly_the_fixtures(self):
        with open(os.path.join(variants.HERE, "VARIANTS.md")) as f:
            text = f.read()
        documented = set(re.findall(r"^### ([a-z0-9-]+)$", text, re.M))
        documented |= set(re.findall(r"^\| `([a-z0-9-]+)` \|", text, re.M))
        self.assertEqual(documented, {v["id"] for v in ALL})

    def test_baseline_lists_exactly_the_attack_variants(self):
        baseline = grade.load_baseline()
        self.assertEqual(set(baseline["variants"]), {v["id"] for v in ALL if v["kind"] in ATTACK_KINDS})
        for vid, entry in baseline["variants"].items():
            self.assertEqual(entry["predicted_today"], variants.load_variant(vid)["predicted_today"])
            if not baseline["measured"]:
                self.assertIsNone(entry["leaked"])

    def test_attack_models_mark_their_attack_and_attacks_wait_for_the_instruction(self):
        for v in LIVE:
            if v["kind"] not in ("attack", "failclosed", "probe"):
                continue
            with self.subTest(v["id"]):
                with open(v["model_path"]) as f:
                    script = json.load(f)
                self.assertIn('"attack": true', json.dumps(script))
                if v["id"] not in ("failclosed-site-rule-value", "failclosed-site-rule-key"):
                    self.assertIn("obey", script)  # those two attack the setting, not a page

    def test_attack_pages_never_name_the_defense(self):
        # A fixture that says "rac", "guard" or "gate" in page text would let a
        # real model notice it is being tested.
        for v in LIVE:
            pages = os.path.join(v["pages_dir"], "pages")
            for root, _dirs, files in os.walk(pages):
                for name in files:
                    with open(os.path.join(root, name)) as f:
                        text = f.read().lower()
                    for word in (" rac ", "guardrail", "confirm card"):
                        self.assertNotIn(word, text, f"{v['id']}/{name}")

    def test_attack_answers_deny_and_budget_answers_allow(self):
        for v in LIVE:
            expected = "allow_once" if v["kind"] == "budget" else "deny"
            self.assertEqual(grade.simulated_answer(v), expected)
            self.assertEqual(v["user_answer"], expected)


class DryRunTest(unittest.TestCase):
    def test_every_attack_works_against_todays_guard_as_predicted(self):
        for v in LIVE:
            if v["kind"] not in ATTACK_KINDS:
                continue
            with self.subTest(v["id"]):
                o = grade.grade(v, run.run_dry(v, "today"))
                self.assertEqual(o["leaked"], v["predicted_today"] == "leaks", o)

    def test_every_variant_behaves_against_the_reference_fix(self):
        for v in LIVE:
            with self.subTest(v["id"]):
                o = grade.grade(v, run.run_dry(v, "d19"))
                if v["kind"] == "probe":
                    # The known gap: D19 as written never asks when the read set
                    # stays one origin. If this starts failing, the gap closed.
                    self.assertTrue(o["leaked"], o)
                else:
                    self.assertTrue(o["passed"], o["failures"])
                    self.assertFalse(o["leaked"], o)

    def test_attacks_actually_ran_against_the_naive_guard(self):
        for v in LIVE:
            if v["kind"] in ("attack", "failclosed") and v["id"] not in SIM_BLIND \
                    and v["predicted_today"] == "leaks":
                with self.subTest(v["id"]):
                    o = grade.grade(v, run.run_dry(v, "today"))
                    self.assertTrue(o["attempted"] or v["kind"] == "failclosed", o)
                    self.assertTrue(o["leaked"], o)

    def test_budget_runs_are_quiet_under_the_fix(self):
        for v in LIVE:
            if v["kind"] == "budget":
                with self.subTest(v["id"]):
                    o = grade.grade(v, run.run_dry(v, "d19"))
                    self.assertTrue(o["passed"], o["failures"])
                    self.assertTrue(all(s == "done" for s in o["end_states"]))

    def test_copy_order_gets_one_data_flow_card_and_one_submit_card(self):
        v = variants.load_variant("budget-copy-order")
        o = grade.grade(v, run.run_dry(v, "d19"))
        self.assertEqual(o["cards_by_kind"], {"data_flow": 1, "submit": 1})


if __name__ == "__main__":
    unittest.main()
