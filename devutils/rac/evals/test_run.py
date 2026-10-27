# Copyright 2026 The rac Authors
# SPDX-License-Identifier: GPL-3.0-or-later
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout

import fake_model
import run
import variants

ORIGINS = {"a": "http://mail.localhost:1111", "b": "http://forms.localhost:2222", "evil": "http://evil.localhost:3333"}


class SeedingTest(unittest.TestCase):
    def prefs(self, vid="chain-canonical"):
        v = variants.load_variant(vid)
        return run.build_preferences(v, ORIGINS, "http://localhost:4444/v1", "/tmp/dl")

    def test_ai_and_browser_control_on_with_the_custom_provider_at_the_fake_model(self):
        p = self.prefs()["rac"]["ai"]
        self.assertIs(p["enabled"], True)
        self.assertIs(p["browser_control"], True)
        self.assertEqual(p["provider"], "custom")
        custom = p["provider_settings"]["custom"]
        self.assertEqual(custom["base_url"], "http://localhost:4444/v1")
        self.assertEqual(custom["model"], fake_model.MODEL_IDS[0])
        self.assertEqual(p["agent_permission_level"], "auto")

    def test_the_base_url_is_one_rac_accepts(self):
        # providers.cc IsAcceptableBaseUrl: https, or http only for localhost, no query or credentials
        url = self.prefs()["rac"]["ai"]["provider_settings"]["custom"]["base_url"]
        self.assertRegex(url, r"^http://localhost:\d+/v1$")

    def test_downloads_go_to_a_throwaway_folder_without_prompting(self):
        d = self.prefs()["download"]
        self.assertEqual((d["default_directory"], d["prompt_for_download"]), ("/tmp/dl", False))

    def test_the_level_and_site_rules_under_test_are_seeded_with_origins_filled_in(self):
        self.assertEqual(self.prefs("failclosed-level-bypass")["rac"]["ai"]["agent_permission_level"], "bypass")
        rules = self.prefs("failclosed-site-rule-value")["rac"]["ai"]["agent_site_rules"]
        self.assertEqual(rules, {ORIGINS["b"]: "maybe"})
        rules = self.prefs("failclosed-site-rule-key")["rac"]["ai"]["agent_site_rules"]
        self.assertEqual(rules, {ORIGINS["b"] + "/signup": "always"})

    def test_expand_fills_keys_values_and_nested_lists(self):
        self.assertEqual(run.expand({"{origin:a}": ["x {origin:b}", 3]}, ORIGINS),
                         {ORIGINS["a"]: ["x " + ORIGINS["b"], 3]})

    def test_deep_set(self):
        d = {}
        run.deep_set(d, "x.y.z", 1)
        run.deep_set(d, "x.y.w", 2)
        self.assertEqual(d, {"x": {"y": {"z": 1, "w": 2}}})


class LaunchTest(unittest.TestCase):
    def test_launch_uses_worktree_run_a_throwaway_profile_and_loopback_debugging(self):
        args = run.launch_args("/tmp/rac-evals-x", 9333)
        self.assertTrue(args[0].endswith("devutils/rac/worktree.sh"))
        self.assertEqual(args[1], "run")
        self.assertIn("--user-data-dir=/tmp/rac-evals-x", args)
        self.assertIn("--remote-debugging-port=9333", args)
        self.assertIn("--remote-debugging-address=127.0.0.1", args)
        self.assertIn("--rac-launch-in-background", args)  # never takes the foreground
        self.assertNotIn("open", args)
        self.assertFalse([a for a in args if "Application Support" in a or "me.kainoa.rac" in a])

    def test_profile_is_a_fresh_folder_named_for_evals_under_the_given_base(self):
        with tempfile.TemporaryDirectory() as base:
            p = run.make_profile(base)
            self.assertTrue(os.path.isdir(os.path.join(p, "Default")))
            self.assertTrue(os.path.basename(p).startswith("rac-evals-"))
            self.assertEqual(os.path.dirname(p), os.path.realpath(base))
            self.assertEqual(os.listdir(os.path.join(p, "Default")), [])

    def test_the_default_profile_base_is_inside_the_worktree_build_folder(self):
        self.assertTrue(os.path.join(run.ROOT, "build").endswith("build"))
        self.assertNotIn("Library", run.ROOT.split(os.sep)[-3:])

    def test_a_real_profile_folder_is_refused(self):
        for base in ("/Users/someone/Library/Application Support/me.kainoa.rac.dev-test",
                     os.path.expanduser("~/Library/Application Support"), "/etc", os.path.expanduser("~")):
            with self.assertRaises(AssertionError):
                run.make_profile(base)

    def test_free_port_is_usable(self):
        self.assertGreater(run.free_port(), 1023)


class StatusTest(unittest.TestCase):
    def test_status_command_targets_the_agent_evals_context(self):
        cmd = run.status_command("abc123", "success", "21/21 variants pass")
        self.assertEqual(cmd[:3], ["gh", "api", "repos/notkainoa/rac/statuses/abc123"])
        self.assertIn("context=rac/agent-evals", cmd)
        self.assertIn("state=success", cmd)

    def test_posting_prints_instead_of_posting_unless_asked(self):
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertIsNone(run.post_status("abc", "failure", "x"))
        self.assertIn("would post: gh api", out.getvalue())


class CliTest(unittest.TestCase):
    def main(self, *argv):
        out = io.StringIO()
        with redirect_stdout(out):
            code = run.main(list(argv))
        return code, out.getvalue()

    def test_list_shows_live_variants_and_hides_stubs(self):
        code, out = self.main("--list")
        self.assertEqual(code, 0)
        self.assertIn("chain-canonical", out)
        self.assertNotIn("outside-levels", out)

    def test_dry_run_of_two_variants_writes_records_and_exits_zero(self):
        with tempfile.TemporaryDirectory() as results:
            code, out = self.main("--dry-run", "d19", "--variants", "chain-canonical,budget-own-words",
                                  "--results-dir", results)
            self.assertEqual(code, 0, out)
            self.assertEqual(sorted(os.listdir(results)), ["budget-own-words.json", "chain-canonical.json"])
            with open(os.path.join(results, "chain-canonical.json")) as f:
                record = json.load(f)
            self.assertEqual(record["mode"], "sim-d19")
            self.assertTrue(record["model_log"] and record["answers"])

    def test_unknown_variant_is_an_error(self):
        with self.assertRaises(SystemExit):
            self.main("--dry-run", "d19", "--variants", "nope")


class LaunchEnvTest(unittest.TestCase):
    def test_crash_dumps_stay_in_the_throwaway_profile(self):
        env = run.launch_env("/tmp/rac-evals-x")
        self.assertEqual(env["BREAKPAD_DUMP_LOCATION"], "/tmp/rac-evals-x/Crashpad")


if __name__ == "__main__":
    unittest.main()
