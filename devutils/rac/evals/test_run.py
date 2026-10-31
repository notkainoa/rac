# Copyright 2026 The rac Authors
# SPDX-License-Identifier: GPL-3.0-or-later
import io
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from contextlib import redirect_stdout
from unittest import mock

import cdp
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

    def suffixed_prefs(self, spec):
        [v] = run.select(mock.Mock(variants=spec, fixtures_dir=variants.FIXTURES))
        return run.build_preferences(v, ORIGINS, "http://localhost:4444/v1", "/tmp/dl")

    def test_an_unsuffixed_run_seeds_no_space_or_panel_width(self):
        p = self.prefs()
        self.assertNotIn("spaces", p["rac"])
        self.assertNotIn("side_panel", p)

    def test_a_dark_run_seeds_one_space_in_dark_mode(self):
        stored = self.suffixed_prefs("chain-canonical_dark")["rac"]["spaces"]
        self.assertEqual(stored["version"], 1)
        [space] = stored["spaces"]
        self.assertEqual(space["theme"]["mode"], "dark")
        # SpaceTheme::FromDict needs both stops or the theme never parses.
        self.assertRegex(space["theme"]["color1"], r"^#[0-9A-Fa-f]{6}$")
        self.assertRegex(space["theme"]["color2"], r"^#[0-9A-Fa-f]{6}$")
        self.assertTrue(space["id"])

    def test_a_light_run_seeds_light_and_no_panel_width(self):
        p = self.suffixed_prefs("chain-canonical_light")
        self.assertEqual(p["rac"]["spaces"]["spaces"][0]["theme"]["mode"], "light")
        self.assertNotIn("side_panel", p)

    def test_narrow_seeds_the_panels_minimum_width(self):
        p = self.suffixed_prefs("chain-canonical_narrow")
        self.assertEqual(p["side_panel"]["id_to_width"],
                         {"kRacAi": run.PANEL_NARROW_WIDTH})
        # kSidePanelMinimumContentWidth 200 + the 11 px border insets.
        self.assertEqual(run.PANEL_NARROW_WIDTH, 211)

    def test_wide_seeds_560_and_no_space(self):
        p = self.suffixed_prefs("chain-canonical_wide")
        self.assertEqual(p["side_panel"]["id_to_width"],
                         {"kRacAi": run.PANEL_WIDE_WIDTH})
        self.assertEqual(run.PANEL_WIDE_WIDTH, 560)
        self.assertNotIn("spaces", p["rac"])

    def test_expand_fills_keys_values_and_nested_lists(self):
        self.assertEqual(run.expand({"{origin:a}": ["x {origin:b}", 3]}, ORIGINS),
                         {ORIGINS["a"]: ["x " + ORIGINS["b"], 3]})

    def test_only_the_agent_level_and_site_rules_may_come_from_a_variant(self):
        self.assertEqual(variants.PREF_KEYS,
                         ("rac.ai.agent_permission_level", "rac.ai.agent_site_rules"))
        v = variants.load_variant("chain-canonical")
        v["prefs"] = {"rac.ai.agent_site_rules": {"{origin:b}/signup": "always"}}
        flat = run.flat_prefs(v, ORIGINS)
        self.assertEqual(flat["rac.ai.agent_site_rules"], {ORIGINS["b"] + "/signup": "always"})

    def test_every_other_variant_pref_key_is_refused(self):
        for key in ("rac.ai.enabled", "rac.ai.browser_control", "rac.ai.provider",
                    "download.prompt_for_download", "helium.services.enabled",
                    "side_panel.id_to_width", "rac.spaces"):
            with self.subTest(key=key):
                v = variants.load_variant("chain-canonical")
                v["prefs"] = {key: False}
                with self.assertRaisesRegex(variants.VariantError, "not allowed"):
                    run.flat_prefs(v, ORIGINS)
                self.assertTrue(any("not allowed" in p for p in variants.validate_variant(v)))

    def test_the_safety_prefs_are_applied_last(self):
        # flat_prefs can no longer produce a safety key, but the order closes
        # the rest: whatever the variant layer returns is written first and
        # the safety block overwrites it.
        v = variants.load_variant("chain-canonical")
        hostile = {"rac.ai.enabled": False, "rac.ai.browser_control": False,
                   "helium.services.enabled": True, "download.prompt_for_download": True}
        with mock.patch.object(run, "flat_prefs", return_value=hostile):
            prefs = run.build_preferences(v, ORIGINS, "http://localhost:4444/v1", "/tmp/dl")
        self.assertIs(prefs["rac"]["ai"]["enabled"], True)
        self.assertIs(prefs["rac"]["ai"]["browser_control"], True)
        self.assertIs(prefs["helium"]["services"]["enabled"], False)
        self.assertIs(prefs["download"]["prompt_for_download"], False)

    def test_deep_set(self):
        d = {}
        run.deep_set(d, "x.y.z", 1)
        run.deep_set(d, "x.y.w", 2)
        self.assertEqual(d, {"x": {"y": {"z": 1, "w": 2}}})


class VariantSpecTest(unittest.TestCase):
    def parse(self, spec):
        return variants.parse_spec(spec)

    def test_a_bare_id_has_no_suffixes(self):
        self.assertEqual(self.parse("chain-canonical"),
                         ("chain-canonical", None, None))

    def test_one_suffix_of_either_kind(self):
        for spec, want in (("v_light", ("v", "light", None)),
                           ("v_dark", ("v", "dark", None)),
                           ("v_narrow", ("v", None, "narrow")),
                           ("v_wide", ("v", None, "wide"))):
            self.assertEqual(self.parse(spec), want, spec)

    def test_both_suffixes_in_either_order(self):
        self.assertEqual(self.parse("v_dark_narrow"), ("v", "dark", "narrow"))
        self.assertEqual(self.parse("v_narrow_dark"), ("v", "dark", "narrow"))

    def test_unknown_empty_or_duplicate_suffixes_are_errors(self):
        for spec in ("v_sepia", "v_", "v_light_", "_light", "v_light_dark",
                     "v_wide_narrow", "v_light_light", "v__light"):
            with self.assertRaises(variants.VariantError, msg=spec):
                self.parse(spec)

    def test_run_id_joins_the_parts_in_a_fixed_order(self):
        self.assertEqual(variants.run_id("chain-canonical"), "chain-canonical")
        self.assertEqual(variants.run_id("v", "dark"), "v-dark")
        self.assertEqual(variants.run_id("v", None, "narrow"), "v-narrow")
        self.assertEqual(variants.run_id("v", "light", "narrow"), "v-light-narrow")

    def selected(self, spec):
        return run.select(mock.Mock(variants=spec, fixtures_dir=variants.FIXTURES))

    def test_a_suffixed_run_keeps_the_base_fixture_under_a_new_id(self):
        [v] = self.selected("chain-canonical_dark_wide")
        self.assertEqual(v["id"], "chain-canonical-dark-wide")
        self.assertEqual(v["base_id"], "chain-canonical")
        self.assertEqual(v["appearance"], "dark")
        self.assertEqual(v["panel_width"], "wide")
        # Same fixture content: the run drives the base variant's steps.
        self.assertEqual(v["turns"], variants.load_variant("chain-canonical")["turns"])

    def test_each_combination_names_its_own_record_and_shots(self):
        vs = self.selected("chain-canonical,chain-canonical_light,"
                           "chain-canonical_dark_narrow,chain-canonical_narrow_dark")
        self.assertEqual([v["id"] for v in vs], ["chain-canonical",
                                                 "chain-canonical-light",
                                                 "chain-canonical-dark-narrow"])
        # Records are <id>.json, shots <id>-*.png: distinct ids can't collide.
        self.assertEqual(len({v["id"] for v in vs}), len(vs))

    def test_an_unsuffixed_run_carries_no_suffix_metadata(self):
        [v] = self.selected("chain-canonical")
        self.assertNotIn("appearance", v)
        self.assertNotIn("panel_width", v)
        self.assertEqual(v["base_id"], "chain-canonical")

    def test_bad_specs_and_unknown_bases_exit(self):
        for spec in ("nope", "chain-canonical_sepia", "chain-canonical_light_dark",
                     "chain-canonical:", "_light"):
            with self.assertRaises(SystemExit, msg=spec):
                self.selected(spec)


class LaunchTest(unittest.TestCase):
    def make_worktree(self, wt):
        """A fake worktree with just the binary and the queue script."""
        binary = run.browser_binary(wt)
        os.makedirs(os.path.dirname(binary))
        open(binary, "w").close()
        queue = os.path.join(wt, "devutils", "rac", "build-queue.sh")
        os.makedirs(os.path.dirname(queue))
        open(queue, "w").close()
        return binary

    def test_launch_wraps_the_app_binary_in_a_queue_run_slot(self):
        with tempfile.TemporaryDirectory() as wt, mock.patch.dict(os.environ) as env:
            env.pop("RAC_EVALS_NO_QUEUE", None)
            binary = self.make_worktree(wt)
            args = run.launch_args("/tmp/rac-evals-x", wt)
        self.assertTrue(args[0].endswith("devutils/rac/build-queue.sh"))
        self.assertEqual(args[1], "--run")
        self.assertEqual(args[2], binary)
        self.assertEqual(args[3:], [
            "--user-data-dir=/tmp/rac-evals-x", "--use-mock-keychain",
            "--disable-features=DialMediaRouteProvider",
            "--remote-debugging-port=0",  # the port comes from DevToolsActivePort
            "--rac-launch-in-background",  # never takes the foreground
            "--no-first-run", "--no-default-browser-check",
            "--disable-background-networking", "--disable-component-update"])
        self.assertNotIn("open", args)
        self.assertFalse([a for a in args if "remote-allow-origins" in a])
        self.assertFalse([a for a in args if "remote-debugging-address" in a])
        self.assertFalse([a for a in args if "Application Support" in a or "me.kainoa.rac" in a])

    def test_no_queue_env_launches_the_binary_directly(self):
        with tempfile.TemporaryDirectory() as wt, \
                mock.patch.dict(os.environ, {"RAC_EVALS_NO_QUEUE": "1"}):
            binary = self.make_worktree(wt)
            args = run.launch_args("/tmp/rac-evals-x", wt)
        self.assertEqual(args[0], binary)
        self.assertEqual(args[1], "--user-data-dir=/tmp/rac-evals-x")
        self.assertFalse([a for a in args if "build-queue" in a or "remote-allow-origins" in a])

    def test_a_missing_binary_or_queue_fails_clearly(self):
        with tempfile.TemporaryDirectory() as wt, mock.patch.dict(os.environ) as env:
            env.pop("RAC_EVALS_NO_QUEUE", None)
            with self.assertRaisesRegex(RuntimeError, "no built rac"):
                run.launch_args("/tmp/rac-evals-x", wt)
            binary = self.make_worktree(wt)
            os.remove(os.path.join(wt, "devutils", "rac", "build-queue.sh"))
            with self.assertRaisesRegex(RuntimeError, "no build queue"):
                run.launch_args("/tmp/rac-evals-x", wt)
            with mock.patch.dict(os.environ, {"RAC_EVALS_NO_QUEUE": "1"}):
                self.assertEqual(run.launch_args("/tmp/rac-evals-x", wt)[0], binary)

    def test_profile_is_a_fresh_folder_named_for_evals_under_the_given_base(self):
        with tempfile.TemporaryDirectory() as base:
            p = run.make_profile("/wt", base)
            self.assertTrue(os.path.isdir(os.path.join(p, "Default")))
            self.assertTrue(os.path.basename(p).startswith("rac-evals-"))
            self.assertEqual(os.path.dirname(p), os.path.realpath(base))
            self.assertEqual(os.listdir(os.path.join(p, "Default")), [])

    def test_the_default_profile_base_is_inside_the_worktree_build_folder(self):
        with tempfile.TemporaryDirectory() as wt:
            p = run.make_profile(wt)
            self.assertEqual(os.path.dirname(p), os.path.realpath(os.path.join(wt, "build")))

    def test_a_real_profile_folder_is_refused(self):
        for base in ("/Users/someone/Library/Application Support/me.kainoa.rac.dev-test",
                     os.path.expanduser("~/Library/Application Support"), "/etc", os.path.expanduser("~")):
            with self.assertRaises(AssertionError):
                run.make_profile("/wt", base)

    def test_free_port_is_usable(self):
        self.assertGreater(run.free_port(), 1023)

    def test_devtools_port_reads_the_active_port_file_or_is_none(self):
        with tempfile.TemporaryDirectory() as profile:
            self.assertIsNone(run.devtools_port(profile))
            with open(os.path.join(profile, "DevToolsActivePort"), "w") as f:
                f.write("")  # created but not written yet
            self.assertIsNone(run.devtools_port(profile))
            with open(os.path.join(profile, "DevToolsActivePort"), "w") as f:
                f.write("41234\n/devtools/browser/abc-123\n")
            self.assertEqual(run.devtools_port(profile), 41234)


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

    def test_the_browser_gets_a_minimal_environment(self):
        # The browser loads hostile fixture pages: it must not inherit the
        # shell's secrets (SSH_AUTH_SOCK under ssh, API keys, ...).
        env = {"HOME": "/h", "PATH": "/p", "TMPDIR": "/t", "LANG": "en_US.UTF-8",
               "SSH_AUTH_SOCK": "/tmp/ssh-agent.sock", "AWS_SECRET_ACCESS_KEY": "x",
               "OPENAI_API_KEY": "sk-x", "RAC_EVALS_NO_QUEUE": "1", "EDITOR": "vim"}
        with mock.patch.dict(os.environ, env, clear=True):
            got = run.launch_env("/tmp/rac-evals-x")
        self.assertEqual(set(got) - {"BREAKPAD_DUMP_LOCATION"},
                         {"HOME", "PATH", "TMPDIR", "LANG"})
        for leaked in ("SSH_AUTH_SOCK", "AWS_SECRET_ACCESS_KEY", "OPENAI_API_KEY",
                       "RAC_EVALS_NO_QUEUE", "EDITOR"):
            self.assertNotIn(leaked, got)

    def test_lang_is_optional(self):
        with mock.patch.dict(os.environ, {"HOME": "/h", "PATH": "/p"}, clear=True):
            got = run.launch_env("/tmp/p")
        self.assertNotIn("LANG", got)
        self.assertNotIn("TMPDIR", got)


class StaleProfileTest(unittest.TestCase):
    def test_old_unused_profiles_go_and_new_ones_stay(self):
        with tempfile.TemporaryDirectory() as wt:
            build = os.path.join(wt, "build")
            old = os.path.join(build, "rac-evals-old")
            new = os.path.join(build, "rac-evals-new")
            other = os.path.join(build, "profile")
            for d in (old, new, other):
                os.makedirs(d)
            past = time.time() - 7 * 3600
            os.utime(old, (past, past))
            os.utime(other, (past, past))
            run.clean_stale_profiles(wt)
            self.assertFalse(os.path.exists(old))
            self.assertTrue(os.path.exists(new))
            self.assertTrue(os.path.exists(other))


class ShotsTest(unittest.TestCase):
    def test_prepare_creates_the_folder_and_a_second_call_is_fine(self):
        with tempfile.TemporaryDirectory() as results:
            shots = run.Shots.prepare(results)
            self.assertEqual(shots.dir, os.path.join(os.path.abspath(results), "shots"))
            self.assertTrue(os.path.isdir(shots.dir))
            self.assertEqual(shots.requests, os.path.join(shots.dir, "requests"))
            run.Shots.prepare(results)

    def test_prepare_refuses_a_symlinked_shots_folder(self):
        with tempfile.TemporaryDirectory() as results, \
                tempfile.TemporaryDirectory() as elsewhere:
            os.symlink(elsewhere, os.path.join(results, "shots"))
            with self.assertRaisesRegex(RuntimeError, "symlink"):
                run.Shots.prepare(results)

    def test_request_writes_the_line_atomically(self):
        with tempfile.TemporaryDirectory() as d:
            shots = run.Shots(d)
            shots.request("/tmp/one.png")
            with open(shots.requests) as f:
                self.assertEqual(f.read(), "/tmp/one.png")
            shots.request("click 10 20")
            with open(shots.requests) as f:
                self.assertEqual(f.read(), "click 10 20")
            self.assertNotIn("requests.tmp", os.listdir(d))

    def serve_pngs(self, shots, stop):
        """Plays the browser: takes the request, writes the named PNG."""
        while not stop:
            if os.path.exists(shots.requests):
                with open(shots.requests) as f:
                    out = f.read().strip()
                os.remove(shots.requests)
                if out.endswith(".png"):
                    with open(out, "wb") as f:
                        f.write(b"\x89PNG pretend")
            time.sleep(0.02)

    def test_capture_activates_the_tab_then_waits_for_a_real_png(self):
        with tempfile.TemporaryDirectory() as d:
            shots = run.Shots(d)
            stop, calls = [], []
            browser = mock.Mock()
            browser.call.side_effect = lambda m, p=None: calls.append((m, p)) or {}
            t = threading.Thread(target=self.serve_pngs, args=(shots, stop), daemon=True)
            t.start()
            try:
                self.assertTrue(shots.capture("v-1-card.png", browser=browser,
                                              activate="T1", timeout=5))
            finally:
                stop.append(True)
                t.join()
            self.assertEqual(calls, [("Target.activateTarget", {"targetId": "T1"})])
            self.assertEqual(shots.taken,
                             [{"name": "v-1-card.png", "ok": True, "error": None}])
            self.assertGreater(os.path.getsize(os.path.join(d, "v-1-card.png")), 0)

    def test_a_missing_png_is_an_error_entry_never_an_exception(self):
        with tempfile.TemporaryDirectory() as d:
            shots = run.Shots(d)
            self.assertFalse(shots.capture("v-2-after.png", timeout=0.5))
            self.assertEqual(len(shots.taken), 1)
            entry = shots.taken[0]
            self.assertEqual(entry["name"], "v-2-after.png")
            self.assertFalse(entry["ok"])
            self.assertIn("timed out", entry["error"])

    def test_an_activate_failure_is_an_error_entry_too(self):
        with tempfile.TemporaryDirectory() as d:
            shots = run.Shots(d)
            browser = mock.Mock()
            browser.call.side_effect = cdp.CdpError("ws gone")
            self.assertFalse(shots.capture("v-1-card.png", browser=browser,
                                           activate="T1", timeout=0.5))
            self.assertIn("ws gone", shots.taken[0]["error"])

    def test_launch_args_adds_the_screenshot_switches_only_with_shots(self):
        wt_test = LaunchTest()
        with tempfile.TemporaryDirectory() as wt, tempfile.TemporaryDirectory() as d, \
                mock.patch.dict(os.environ, {"RAC_EVALS_NO_QUEUE": "1"}):
            binary = wt_test.make_worktree(wt)
            shots = run.Shots(d)
            shots.boot = os.path.join(d, "v-boot.png")
            args = run.launch_args("/tmp/p", wt, shots)
            self.assertIn(f"--rac-window-screenshot={shots.boot}", args)
            self.assertIn(f"--rac-window-screenshot-requests={shots.requests}", args)
            args = run.launch_args("/tmp/p", wt)
            self.assertEqual(args[0], binary)
            self.assertFalse([a for a in args if "screenshot" in a])


class PanelTargetTest(unittest.TestCase):
    """Picking the side panel out of a Target.getTargets list."""

    AI_TAB = {"targetId": "T-AI", "type": "page", "url": "chrome://rac-ai/"}
    PANEL = {"targetId": "T-P", "type": "page", "url": "chrome://rac-ai/?mode=panel"}
    PAGE = {"targetId": "T1", "type": "page", "url": "http://site/"}

    def test_only_the_chat_tab_means_no_panel(self):
        self.assertIsNone(run.panel_target([self.AI_TAB, self.PAGE], "T-AI"))

    def test_the_mode_panel_url_picks_the_panel(self):
        got = run.panel_target([self.PAGE, self.AI_TAB, self.PANEL], "T-AI")
        self.assertIs(got, self.PANEL)

    def test_a_second_rac_ai_target_is_the_panel_even_without_the_marker(self):
        other = {"targetId": "T-P2", "type": "other", "url": "rac://rac-ai"}
        got = run.panel_target([self.AI_TAB, self.PAGE, other], "T-AI")
        self.assertIs(got, other)

    def test_the_assistant_tab_itself_is_never_the_panel(self):
        self.assertIsNone(run.panel_target([self.AI_TAB], "T-AI"))

    def test_urls_that_arent_the_assistant_never_match(self):
        targets = [{"targetId": "T1", "url": "chrome://settings/assistant"},
                   {"targetId": "T2", "url": "http://rac-ai.example/"}]
        self.assertIsNone(run.panel_target(targets, "T-AI"))


class AgentPageTest(unittest.TestCase):
    """Which page tab the -1-card shot puts in front of the panel."""

    def test_the_turns_attached_tab_wins(self):
        pages = {"a:/inbox": mock.Mock(target_id="T1"),
                 "b:/form": mock.Mock(target_id="T2")}
        self.assertIs(run.agent_page(pages, {"attach": ["b:/form", "a:/inbox"]}),
                      pages["b:/form"])

    def test_an_unopened_attach_ref_is_skipped(self):
        self.assertEqual(run.agent_page({"a:/inbox": "P1"}, {"attach": ["b:/x"]}), "P1")

    def test_without_attach_the_last_opened_page_is_used(self):
        pages = {"a:/x": "P1", "b:/y": "P2"}
        self.assertEqual(run.agent_page(pages, {"user": "x"}), "P2")

    def test_no_pages_means_none(self):
        self.assertIsNone(run.agent_page({}, {"attach": ["a:/x"]}))


class OpenPanelTest(unittest.TestCase):
    """open_panel: the panel is toggled on once, only while it's closed."""

    class FakeBrowser:
        """Answers open_panel's CDP calls. `open` reports the side panel's
        target from getTargets; the serve thread sets it when a "command"
        request arrives, like the real browser."""
        def __init__(self):
            self.calls = []
            self.open = False

        def call(self, method, params=None, session_id=None):
            self.calls.append((method, params))
            if method == "Target.getTargets":
                infos = []
                if self.open:
                    infos.append({"targetId": "T-P", "type": "page",
                                  "url": "chrome://rac-ai/?mode=panel"})
                return {"targetInfos": infos}
            if method == "Target.attachToTarget":
                return {"sessionId": "S-" + params["targetId"]}
            return {}

    @staticmethod
    def serve(shots, browser, lines, stop):
        """The browser's end of the requests file: "command ID" opens the
        fake panel."""
        while not stop:
            if os.path.exists(shots.requests):
                with open(shots.requests) as f:
                    line = f.read().strip()
                os.remove(shots.requests)
                lines.append(line)
                if line.startswith("command "):
                    browser.open = True
            time.sleep(0.02)

    def open_panel(self, browser, timeout=5):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        shots = run.Shots(d.name)
        lines, stop = [], []
        t = threading.Thread(target=self.serve, args=(shots, browser, lines, stop),
                             daemon=True)
        t.start()
        try:
            page = run.open_panel(browser, shots, None, timeout=timeout)
        finally:
            stop.append(True)
            t.join()
        return page, lines

    def test_a_closed_panel_gets_the_toggle_command_then_its_page(self):
        page, lines = self.open_panel(self.FakeBrowser())
        self.assertEqual(lines, ["command 40701"])
        self.assertEqual(page.target_id, "T-P")
        self.assertEqual(page.session, "S-T-P")

    def test_an_open_panel_is_never_sent_the_toggle(self):
        browser = self.FakeBrowser()
        browser.open = True
        page, lines = self.open_panel(browser)
        self.assertEqual(lines, [])
        self.assertEqual(page.target_id, "T-P")

    def test_a_panel_that_never_opens_raises(self):
        with tempfile.TemporaryDirectory() as d:
            shots = run.Shots(d)
            with self.assertRaisesRegex(RuntimeError, "side panel"):
                run.open_panel(self.FakeBrowser(), shots, None, timeout=0.5)


class CardShotTest(unittest.TestCase):
    """capture_card: the window arrangement behind the -1-card shot."""

    class FakeBrowser:
        """capture_card only activates the acted-on page through this."""
        def __init__(self):
            self.calls = []

        def call(self, method, params=None, session_id=None):
            self.calls.append((method, params))
            return {}

    @staticmethod
    def serve(shots, stop):
        """The browser's end of the requests file: a PNG path gets written."""
        while not stop:
            if os.path.exists(shots.requests):
                with open(shots.requests) as f:
                    out = f.read().strip()
                os.remove(shots.requests)
                if out.endswith(".png"):
                    with open(out, "wb") as f:
                        f.write(b"\x89PNG pretend")
            time.sleep(0.02)

    class FakePanel:
        """The panel Page: eval answers whether the card is in the DOM."""
        def __init__(self, present=True):
            self.present = present
            self.evals = []
            self.browser = mock.Mock()
            self.browser.timeout = 5

        def eval(self, expr, await_promise=True):
            self.evals.append(expr)
            return self.present

    def run_shot(self, browser, panel, page=None, card_id="c7", timeout=5):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        shots = run.Shots(d.name)
        stop = []
        t = threading.Thread(target=self.serve, args=(shots, stop), daemon=True)
        t.start()
        try:
            ok = shots.capture_card("v-1-card.png", browser, panel,
                                    page or mock.Mock(target_id="T1"),
                                    card_id=card_id, timeout=timeout)
        finally:
            stop.append(True)
            t.join()
        return shots, ok

    def test_the_page_is_activated_then_the_card_waited_for_in_the_panel(self):
        browser, panel = self.FakeBrowser(), self.FakePanel()
        shots, ok = self.run_shot(browser, panel)
        self.assertTrue(ok)
        self.assertEqual(browser.calls[0],
                         ("Target.activateTarget", {"targetId": "T1"}))
        # the card check ran against this card's own id in the panel page
        self.assertEqual(panel.evals, [run.card_present_js("c7")])
        self.assertIn("data-confirm-id", panel.evals[0])
        self.assertEqual(shots.taken,
                         [{"name": "v-1-card.png", "ok": True, "error": None}])

    def test_no_card_in_the_panel_still_writes_the_png_marked(self):
        shots, ok = self.run_shot(self.FakeBrowser(), self.FakePanel(False),
                                  timeout=1)
        self.assertFalse(ok)
        entry = shots.taken[0]
        self.assertFalse(entry["ok"])
        self.assertEqual(entry["error"], "card not in side panel")
        self.assertTrue(os.path.exists(os.path.join(shots.dir, "v-1-card.png")))


class SendPathTest(unittest.TestCase):
    """Which way a turn is driven — the gate without --screenshots is wire."""

    def test_no_shots_is_the_wire_path(self):
        self.assertEqual(run.send_path(None), "wire")

    def test_shots_is_the_panel_ui_path(self):
        self.assertEqual(run.send_path(run.Shots("/tmp/x")), "ui")


class PanelJsTest(unittest.TestCase):
    """The selectors and flows the panel UI drive relies on — pure strings,
    checked against chrome/browser/resources/rac_ai/index.html + app.ts +
    agent_cards.ts (see the comment above run.send_path)."""

    def test_typing_sets_the_composer_textarea_and_fires_input(self):
        js = run.panel_type_js('say "hi" <there>')
        self.assertIn("getElementById('input')", js)
        self.assertIn("dispatchEvent(new Event('input'", js)
        self.assertIn('"say \\"hi\\" <there>"', js)  # JSON-escaped text

    def test_submit_clicks_the_real_send_button(self):
        self.assertIn("getElementById('send')", run.PANEL_SUBMIT_JS)
        self.assertIn(".click()", run.PANEL_SUBMIT_JS)

    def test_stop_clicks_the_real_stop_button(self):
        self.assertIn("getElementById('stop')", run.PANEL_STOP_JS)

    def test_chips_are_the_attachment_cards_and_their_title_is_the_url(self):
        self.assertIn("#chips .attachment", run.CHIP_URLS)
        self.assertIn(".title", run.CHIP_URLS)

    def test_attach_opens_the_addtab_picker_then_replays_the_menu_pick(self):
        js = run.panel_attach_js(9)
        self.assertIn("getElementById('addTab')", js)
        self.assertIn(".click()", js)
        self.assertIn("'tab:9'", js)  # the menu entry's id is tab:<id>
        self.assertIn("rac-ai-menu", js)

    def test_the_card_selector_covers_confirm_and_plan_ids(self):
        sel = run._card_selector("c9")
        self.assertIn('.agent-card[data-confirm-id="c9"]', sel)
        self.assertIn('.agent-card[data-plan-id="c9"]', sel)

    def test_card_present_looks_up_that_card(self):
        self.assertIn('data-confirm-id', run.card_present_js("c9"))

    def test_resolved_is_a_gone_card_or_a_decided_plan_card(self):
        js = run.card_resolved_js("c9")
        self.assertIn("!c ||", js)
        self.assertIn("dataset.status", js)
        self.assertIn("'pending'", js)

    def test_click_answers_with_the_right_button_after_the_arm_delay(self):
        js = run.card_click_js("c9", "allow_once")
        self.assertIn(".agent-actions", js)
        self.assertIn("button.pill-action", js)
        self.assertIn("classList.contains('primary')", js)
        self.assertIn("actions.inert", js)  # waits out CONFIRM_ARM_MS
        self.assertIn("pick.click()", js)
        # deny prefers the plain "Don't allow", never grant/always
        deny = run.card_click_js("c9", "deny")
        self.assertIn("!b.classList.contains('primary')", deny)
        self.assertIn("!b.classList.contains('quiet')", deny)


class PanelAttachTest(unittest.TestCase):
    """attach_panel_turn: chips and the + menu attach the turn's tabs."""

    class FakePanel:
        """Dispatches on the eval expressions the panel helpers send."""
        def __init__(self):
            self.chips = []
            self.keep = []  # the URLs the turn wants, for the prune answer
            self.pick = "picked"
            self.present = True
            self.resolved = True
            self.click = "clicked"
            self.evals = []
            self.browser = mock.Mock()
            self.browser.timeout = 5

        def eval(self, expr, await_promise=True):
            self.evals.append(expr)
            if expr == run.CHIP_URLS:
                return list(self.chips)
            if expr.startswith("!!document.querySelector"):
                return self.present
            if "pill-action" in expr:
                return self.click
            if "rac-ai-menu" in expr:
                if self.pick == "picked":
                    self.chips.append("http://picked/")  # the pick lands a chip
                return self.pick
            if "card-remove" in expr:
                for c in list(self.chips):
                    if not any(c.startswith(u) for u in self.keep):
                        self.chips.remove(c)  # one unwanted chip per call
                        return "removed"
                return "clean"
            if "dataset.status" in expr:
                return self.resolved
            return None

    def test_a_tab_the_chip_already_covers_needs_no_pick(self):
        panel = self.FakePanel()
        panel.chips = ["http://site/inbox"]
        panel.keep = ["http://site/inbox"]
        run.attach_panel_turn(panel, {"http://site/inbox": 5}, None)
        self.assertIn(run.CHIP_URLS, panel.evals)
        self.assertFalse(any("rac-ai-menu" in e for e in panel.evals))

    def test_an_uncovered_tab_is_picked_in_the_addtab_menu(self):
        panel = self.FakePanel()
        run.attach_panel_turn(panel, {"http://picked/": 9}, None)
        self.assertIn(run.CHIP_URLS, panel.evals)
        self.assertTrue(any("rac-ai-menu" in e for e in panel.evals))

    def test_a_chip_the_turn_did_not_ask_for_is_removed(self):
        panel = self.FakePanel()
        panel.chips = ["http://site/inbox", "http://extra/"]
        panel.keep = ["http://site/inbox"]
        run.attach_panel_turn(panel, {"http://site/inbox": 5}, None)
        self.assertEqual(panel.chips, ["http://site/inbox"])
        self.assertTrue(any("card-remove" in e for e in panel.evals))

    def test_a_pick_that_never_opens_is_retried_then_gives_up(self):
        panel = self.FakePanel()
        panel.pick = "no-addTab"  # the menu never opens, no chip lands
        run.attach_panel_turn(panel, {"http://picked/": 9}, None, timeout=1.5)
        picks = [e for e in panel.evals if "rac-ai-menu" in e]
        self.assertGreaterEqual(len(picks), 1)

    def test_panel_answer_clicks_the_card_that_is_there(self):
        panel = self.FakePanel()
        self.assertEqual(run.panel_answer(panel, "c9", "deny", None), "clicked")
        click = next(e for e in panel.evals if "pill-action" in e)
        self.assertIn("c9", click)

    def test_panel_answer_reports_a_card_that_never_renders(self):
        panel = self.FakePanel()
        panel.present = False
        self.assertEqual(run.panel_answer(panel, "c9", "deny", None, timeout=0.3),
                         "no-card")


class AnswerCardTest(unittest.TestCase):
    """answer_card records the simulated user's answer only after the click
    or the respond call is confirmed — a card nobody answered is a recorded
    failure, never a deny."""

    class FakeAssistant:
        """The wire path's Page: eval returns whatever the handler resolved
        and raises when the evaluate fails (a rejected sendWithPromise lands
        in exceptionDetails)."""
        def __init__(self, exc=None):
            self.exc = exc
            self.evals = []

        def eval(self, expr, await_promise=True):
            self.evals.append(expr)
            if self.exc is not None:
                raise self.exc
            return None

    def test_a_successful_respond_call_records_the_answer(self):
        assistant = self.FakeAssistant()
        rec = run.answer_card(assistant, "c9", "deny", None, None)
        self.assertEqual(rec, {"id": "c9", "answer": "deny"})
        self.assertIn("racAiAgentRespond", assistant.evals[0])
        self.assertIn('"deny"', assistant.evals[0])

    def test_a_rejected_respond_records_the_failure_not_the_answer(self):
        rec = run.answer_card(self.FakeAssistant(cdp.CdpError("ws gone")),
                              "c9", "deny", None, None)
        self.assertNotIn("answer", rec)
        self.assertEqual(rec["id"], "c9")
        self.assertIn("ws gone", rec["error"])

    def test_a_landed_button_click_records_the_answer(self):
        shots = run.Shots("/tmp/answer-card-test")
        rec = run.answer_card(PanelAttachTest.FakePanel(), "c9", "deny", None, shots)
        self.assertEqual(rec, {"id": "c9", "answer": "deny"})

    def test_a_click_that_never_landed_records_the_failure(self):
        for status in ("no-button", "no-card", "eval-failed"):
            panel = PanelAttachTest.FakePanel()
            panel.click = status if status != "no-card" else "no-card"
            panel.present = status != "no-card"
            rec = run.answer_card(panel, "c9", "deny", None, run.Shots("/tmp/x"))
            self.assertNotIn("answer", rec, status)
            self.assertIn(status, rec["error"], status)


class RelaunchTest(unittest.TestCase):
    def test_port_open(self):
        import socket
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        s.listen(1)
        port = s.getsockname()[1]
        self.assertTrue(run._port_open(port))
        s.close()
        self.assertFalse(run._port_open(port))

    def hold_profile(self, profile, seconds):
        """A process whose argv carries the flag, as a launched browser's
        does; pgrep -f sees it until it exits."""
        proc = subprocess.Popen([sys.executable, "-c",
                                 f"import time; time.sleep({seconds})",
                                 f"--user-data-dir={profile}"])
        threading.Thread(target=proc.wait, daemon=True).start()  # reap the zombie
        for _ in range(100):  # wait until exec makes it visible to pgrep
            if subprocess.run(["pgrep", "-f", "--", f"--user-data-dir={profile}"],
                              capture_output=True).returncode == 0:
                return proc
            time.sleep(0.05)
        proc.kill()
        self.fail("the holder never became visible to pgrep")

    def test_wait_released_returns_at_once_when_nothing_holds(self):
        self.assertTrue(run.wait_released("/tmp/rac-evals-none", run.free_port(), timeout=2))

    def test_wait_released_blocks_until_the_holder_exits(self):
        profile = "/tmp/rac-evals-hold-test"
        proc = self.hold_profile(profile, 1.2)
        try:
            start = time.time()
            self.assertTrue(run.wait_released(profile, run.free_port(), timeout=10))
            self.assertGreater(time.time() - start, 0.5)
        finally:
            proc.kill()

    def test_wait_released_gives_up_when_still_held(self):
        profile = "/tmp/rac-evals-stuck-test"
        proc = self.hold_profile(profile, 30)
        try:
            start = time.time()
            self.assertFalse(run.wait_released(profile, run.free_port(), timeout=1))
            self.assertGreaterEqual(time.time() - start, 1)
        finally:
            proc.kill()


class AttachWaitTest(unittest.TestCase):
    class FakeAssistant:
        def __init__(self, payload):
            self.payload = payload

        def eval(self, expression, await_promise=True):
            return self.payload

    def test_returns_once_every_wanted_url_is_listed(self):
        infos = [{"id": 1, "url": "http://wanted/page"}, {"id": 2, "url": "http://other/"}]
        got = run.await_attached_tabs(self.FakeAssistant(infos), ["http://wanted/"],
                                      mock.Mock(), None, timeout=2)
        self.assertEqual(got, infos)

    def test_timeout_raises_with_the_last_payload_and_get_targets(self):
        assistant = self.FakeAssistant([{"id": 1, "url": "http://other/"}])
        browser = mock.Mock()
        browser.call.return_value = {"targetInfos": [{"targetId": "t9",
                                                      "url": "chrome://rac-ai/"}]}
        try:
            run.await_attached_tabs(assistant, ["http://wanted/"], browser, None, timeout=0.3)
            self.fail("should have timed out")
        except RuntimeError as e:
            msg = str(e)
        self.assertIn("racAiGetTabs", msg)
        self.assertIn("http://other/", msg)
        self.assertIn("Target.getTargets", msg)
        self.assertIn("t9", msg)

    def test_get_targets_failure_is_reported_not_raised(self):
        browser = mock.Mock()
        browser.call.side_effect = cdp.CdpError("ws gone")
        try:
            run.await_attached_tabs(self.FakeAssistant([]), ["http://wanted/"],
                                    browser, None, timeout=0.3)
            self.fail("should have timed out")
        except RuntimeError as e:
            self.assertIn("ws gone", str(e))

    def test_listed_tabs_stashes_the_raw_payload_for_diagnosis(self):
        last = {}
        infos = [{"id": 1, "url": "http://x/page"}]
        self.assertEqual(run._listed_tabs(self.FakeAssistant(infos), ["http://x/"], last), infos)
        self.assertEqual(last["get_tabs"], infos)


if __name__ == "__main__":
    unittest.main()
