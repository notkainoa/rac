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

    def test_expand_fills_keys_values_and_nested_lists(self):
        self.assertEqual(run.expand({"{origin:a}": ["x {origin:b}", 3]}, ORIGINS),
                         {ORIGINS["a"]: ["x " + ORIGINS["b"], 3]})

    def test_deep_set(self):
        d = {}
        run.deep_set(d, "x.y.z", 1)
        run.deep_set(d, "x.y.w", 2)
        self.assertEqual(d, {"x": {"y": {"z": 1, "w": 2}}})


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
            args = run.launch_args("/tmp/rac-evals-x", 9333, wt)
        self.assertTrue(args[0].endswith("devutils/rac/build-queue.sh"))
        self.assertEqual(args[1], "--run")
        self.assertEqual(args[2], binary)
        self.assertEqual(args[3:], [
            "--user-data-dir=/tmp/rac-evals-x", "--use-mock-keychain",
            "--disable-features=DialMediaRouteProvider",
            "--remote-debugging-port=9333", "--remote-debugging-address=127.0.0.1",
            "--rac-launch-in-background",  # never takes the foreground
            "--no-first-run", "--no-default-browser-check",
            "--disable-background-networking", "--disable-component-update"])
        self.assertNotIn("open", args)
        self.assertFalse([a for a in args if "remote-allow-origins" in a])
        self.assertFalse([a for a in args if "Application Support" in a or "me.kainoa.rac" in a])

    def test_no_queue_env_launches_the_binary_directly(self):
        with tempfile.TemporaryDirectory() as wt, \
                mock.patch.dict(os.environ, {"RAC_EVALS_NO_QUEUE": "1"}):
            binary = self.make_worktree(wt)
            args = run.launch_args("/tmp/rac-evals-x", 9333, wt)
        self.assertEqual(args[0], binary)
        self.assertEqual(args[1], "--user-data-dir=/tmp/rac-evals-x")
        self.assertFalse([a for a in args if "build-queue" in a or "remote-allow-origins" in a])

    def test_a_missing_binary_or_queue_fails_clearly(self):
        with tempfile.TemporaryDirectory() as wt, mock.patch.dict(os.environ) as env:
            env.pop("RAC_EVALS_NO_QUEUE", None)
            with self.assertRaisesRegex(RuntimeError, "no built rac"):
                run.launch_args("/tmp/rac-evals-x", 9333, wt)
            binary = self.make_worktree(wt)
            os.remove(os.path.join(wt, "devutils", "rac", "build-queue.sh"))
            with self.assertRaisesRegex(RuntimeError, "no build queue"):
                run.launch_args("/tmp/rac-evals-x", 9333, wt)
            with mock.patch.dict(os.environ, {"RAC_EVALS_NO_QUEUE": "1"}):
                self.assertEqual(run.launch_args("/tmp/rac-evals-x", 9333, wt)[0], binary)

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
            args = run.launch_args("/tmp/p", 9333, wt, shots)
            self.assertIn(f"--rac-window-screenshot={shots.boot}", args)
            self.assertIn(f"--rac-window-screenshot-requests={shots.requests}", args)
            args = run.launch_args("/tmp/p", 9333, wt)
            self.assertEqual(args[0], binary)
            self.assertFalse([a for a in args if "screenshot" in a])


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
