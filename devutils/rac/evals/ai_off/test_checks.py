# Copyright 2026 The rac Authors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Tests for the AI-off checks, on fabricated input only. Run from evals/:
  python3 -m unittest discover -s . -t . -p 'test_*.py' -v
"""

import json
import os
import re
import tempfile
import unittest

from ai_off import checks, run_ai_off, surfaces
from ai_off.run_ai_off import BUNDLE, PROFILE, fabricate_lsof, fabricate_netlog, fabricate_ps, fabricate_state


class McpDirTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.profile = os.path.join(self.tmp.name, "profile")
        self.fallback = os.path.join(self.tmp.name, "tmp")
        os.makedirs(self.profile)
        os.makedirs(self.fallback)

    def test_clean(self):
        self.assertEqual(checks.check_no_mcp_dir(self.profile, self.fallback), [])

    def test_empty_dir_fails(self):
        os.makedirs(os.path.join(self.profile, "rac-agent-mcp"))
        self.assertEqual(len(checks.check_no_mcp_dir(self.profile, self.fallback)), 1)

    def test_populated_dir_fails(self):
        os.makedirs(os.path.join(self.profile, "rac-agent-mcp", "tok"))
        self.assertIn("rac-agent-mcp", checks.check_no_mcp_dir(self.profile, self.fallback)[0])

    def test_a_file_in_its_place_fails(self):
        open(os.path.join(self.profile, "rac-agent-mcp"), "w").close()
        self.assertTrue(checks.check_no_mcp_dir(self.profile, self.fallback))

    def test_fallback_dir_for_this_uid_fails(self):
        os.makedirs(os.path.join(self.fallback, "rac-mcp-501-abc"))
        self.assertEqual(len(checks.check_no_mcp_dir(self.profile, self.fallback, uid=501)), 1)

    def test_fallback_dir_of_another_uid_is_ignored(self):
        os.makedirs(os.path.join(self.fallback, "rac-mcp-502-abc"))
        self.assertEqual(checks.check_no_mcp_dir(self.profile, self.fallback, uid=501), [])

    def test_preexisting_fallback_dir_is_ignored(self):
        os.makedirs(os.path.join(self.fallback, "rac-mcp-501-old"))
        os.makedirs(os.path.join(self.fallback, "rac-mcp-501-new"))
        problems = checks.check_no_mcp_dir(self.profile, self.fallback, uid=501, ignore={"rac-mcp-501-old"})
        self.assertEqual(len(problems), 1)
        self.assertIn("new", problems[0])

    def test_unrelated_tmp_entries_are_ignored(self):
        os.makedirs(os.path.join(self.fallback, "rac-mcp-notes"))
        os.makedirs(os.path.join(self.fallback, "other-501-abc"))
        self.assertEqual(checks.check_no_mcp_dir(self.profile, self.fallback, uid=501), [])


class ProcessTreeTest(unittest.TestCase):
    def check(self, text, root=100):
        return checks.check_process_tree(text, root, BUNDLE)

    def test_parse_ps(self):
        procs = checks.parse_ps(fabricate_ps())
        by = {p["pid"]: p for p in procs}
        self.assertEqual(by[101]["ppid"], 100)
        self.assertTrue(by[101]["exe"].endswith("rac Helper (GPU)"))
        self.assertEqual(by[100]["exe"], BUNDLE + "/Contents/MacOS/rac")

    def test_parse_ps_skips_junk(self):
        self.assertEqual(checks.parse_ps("garbage\n\n  PID PPID COMMAND\n  7 1 /bin/x\n"),
                         [{"pid": 7, "ppid": 1, "command": "/bin/x", "exe": "/bin/x"}])

    def test_healthy_baseline_passes(self):
        self.assertEqual(self.check(fabricate_ps()), [])

    def test_unrelated_processes_are_not_descendants(self):
        names = [p["pid"] for p in checks.descendants(checks.parse_ps(fabricate_ps()), 100)]
        self.assertNotIn(900, names)
        self.assertNotIn(901, names)
        self.assertNotIn(100, names)

    def test_root_missing(self):
        self.assertIn("not in the ps output", self.check(fabricate_ps(), root=4242)[0])

    def test_each_unhealthy_process_is_flagged(self):
        problems = self.check(fabricate_ps(unhealthy=True))
        joined = "\n".join(problems)
        self.assertEqual(len(problems), 4)
        for pid in (300, 301, 302, 303):
            self.assertIn(f"pid {pid}", joined)
        self.assertIn("agent tool", joined)
        self.assertIn("OnDeviceModelService", joined)

    def test_grandchild_is_found(self):
        self.assertTrue(any("pid 301" in p for p in self.check(fabricate_ps(unhealthy=True))))

    def _one(self, command):
        return self.check(f"  100 1 {BUNDLE}/Contents/MacOS/rac\n  200 100 {command}\n")

    def test_each_agent_tool_is_flagged(self):
        for tool in ("node", "npx", "claude", "codex", "opencode", "nc", "gemini", "goose",
                     "copilot", "cursor"):
            with self.subTest(tool=tool):
                problems = self._one(f"/usr/local/bin/{tool} --serve")
                self.assertEqual(len(problems), 1)
                self.assertIn("agent tool", problems[0])

    def test_binary_outside_bundle_fails_even_if_it_looks_like_a_helper(self):
        problems = self._one("/Applications/Helium.app/Contents/MacOS/Helium Helper --type=renderer")
        self.assertIn("outside the app bundle", problems[0])

    def test_bundle_prefix_lookalike_fails(self):
        problems = self._one(BUNDLE + "-evil/Contents/MacOS/rac Helper --type=renderer")
        self.assertEqual(len(problems), 1)

    def test_dotdot_out_of_the_bundle_fails(self):
        problems = self._one(BUNDLE + "/../../evil --type=renderer")
        self.assertEqual(len(problems), 1)

    def test_unknown_type_fails(self):
        self.assertIn("'zygote'", self._one(BUNDLE + "/Contents/MacOS/rac Helper --type=zygote")[0])

    def test_missing_type_fails(self):
        self.assertIn("no --type", self._one(BUNDLE + "/Contents/MacOS/rac --foo")[0])

    def test_utility_without_subtype_fails(self):
        self.assertIn("without a --utility-sub-type",
                      self._one(BUNDLE + "/Contents/MacOS/rac Helper --type=utility")[0])

    def test_allowed_utility_subtypes_pass(self):
        for sub in ("network.mojom.NetworkService", "storage.mojom.StorageService",
                    "audio.mojom.AudioService", "video_capture.mojom.VideoCaptureService"):
            with self.subTest(sub=sub):
                self.assertEqual(self._one(
                    f"{BUNDLE}/Contents/MacOS/rac Helper --type=utility --utility-sub-type={sub}"), [])

    def test_crashpad_handler_passes(self):
        self.assertEqual(self._one(BUNDLE + "/Contents/Helpers/chrome_crashpad_handler --database=/x"), [])

    def test_crashpad_name_outside_bundle_fails(self):
        self.assertEqual(len(self._one("/tmp/crashpad_handler --database=/x")), 1)

    def test_child_names(self):
        self.assertEqual(checks.child_names(fabricate_ps(), 100),
                         sorted(["rac Helper (GPU)", "rac Helper", "rac Helper", "rac Helper (Renderer)",
                                 "chrome_crashpad_handler"]))


class SocketTest(unittest.TestCase):
    def test_parse_lsof(self):
        rows = checks.parse_lsof_unix(fabricate_lsof())
        self.assertEqual([r["pid"] for r in rows], [100, 100, 100, 101])
        self.assertEqual(rows[0]["name"], "->0x6f2c1a3e8b21c4d6")
        self.assertEqual(rows[1]["name"], "")
        self.assertEqual(rows[2]["name"],
                         "/var/folders/ab/cd/T/.org.chromium.Chromium.Xy12/SingletonSocket")
        self.assertEqual(rows[3]["command"], "rac\\x20Helper")

    def test_parse_lsof_command_with_a_space_and_a_linux_node(self):
        row = checks.parse_lsof_unix(
            "rac Helper 12 kn 3u unix 0xabc 0t0 98765 /tmp/x/s\n")[0]
        self.assertEqual((row["command"], row["pid"], row["node"], row["name"]),
                         ("rac Helper", 12, "98765", "/tmp/x/s"))

    def test_parse_lsof_skips_header_and_junk(self):
        self.assertEqual(checks.parse_lsof_unix("COMMAND PID USER FD TYPE DEVICE SIZE/OFF NODE NAME\nnope\n"), [])

    def test_healthy_passes(self):
        self.assertEqual(checks.check_no_agent_sockets(fabricate_lsof(), PROFILE), [])

    def test_anonymous_and_pathless_pass(self):
        text = ("rac 1 kn 3u unix 0xa 0t0 ->0xb\n"
                "rac 1 kn 4u unix 0xc 0t0\n")
        self.assertEqual(checks.check_no_agent_sockets(text, PROFILE), [])

    def test_socket_in_profile_fails(self):
        text = f"rac 1 kn 12u unix 0xa 0t0 {PROFILE}/anything/s\n"
        self.assertEqual(len(checks.check_no_agent_sockets(text, PROFILE)), 1)

    def test_profile_lookalike_directory_passes(self):
        text = f"rac 1 kn 12u unix 0xa 0t0 {PROFILE}-other/s\n"
        self.assertEqual(checks.check_no_agent_sockets(text, PROFILE), [])

    def test_private_alias_of_the_profile_fails(self):
        text = "rac 1 kn 12u unix 0xa 0t0 /private/var/x/rac-evals-q/s\n"
        self.assertEqual(len(checks.check_no_agent_sockets(text, "/var/x/rac-evals-q")), 1)

    def test_rac_mcp_anywhere_fails(self):
        text = "nc 2 kn 3u unix 0xa 0t0 /tmp/rac-mcp-501-tok/s\n"
        self.assertEqual(len(checks.check_no_agent_sockets(text, PROFILE)), 1)

    def test_rac_agent_anywhere_fails(self):
        text = "x 2 kn 3u unix 0xa 0t0 /var/rac-agent/s\n"
        self.assertEqual(len(checks.check_no_agent_sockets(text, PROFILE)), 1)

    def test_path_in_the_peer_half_fails(self):
        text = "rac 2 kn 3u unix 0xa 0t0 ->/tmp/rac-mcp-1-t/s\n"
        self.assertEqual(len(checks.check_no_agent_sockets(text, PROFILE)), 1)

    def test_singleton_socket_symlink_in_profile_passes(self):
        text = f"rac 2 kn 3u unix 0xa 0t0 {PROFILE}/SingletonSocket\n"
        self.assertEqual(checks.check_no_agent_sockets(text, PROFILE), [])

    def test_unhealthy_fixture(self):
        self.assertEqual(len(checks.check_no_agent_sockets(fabricate_lsof(True), PROFILE)), 2)


class AnnotationHashTest(unittest.TestCase):
    # Reference values from tools/traffic_annotation/scripts/auditor/auditor_test.py.
    VECTORS = {"test": 3556498, "unique_id": 10236504, "123_id": 70581310, "ID123": 69491511,
               "a_unique_looooooooooooooooooooooooooooooooooooooooooooooooooooooong_id": 98652091,
               "bébé": 124751853}

    def test_chromium_reference_values(self):
        for text, want in self.VECTORS.items():
            with self.subTest(text=text):
                self.assertEqual(checks.traffic_annotation_hash(text), want)

    def test_rac_ids_are_distinct_and_in_range(self):
        h = [checks.traffic_annotation_hash(i) for i in checks.ANNOTATION_IDS]
        self.assertEqual(len(set(h)), 2)
        self.assertTrue(all(0 <= x < 138003713 for x in h))
        self.assertEqual(set(checks.ANNOTATION_HASHES), set(h))


class ProviderRequestTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def netlog(self, **kw):
        path = os.path.join(self.tmp.name, "n%d.json" % len(os.listdir(self.tmp.name)))
        fabricate_netlog(path, **kw)
        return path

    def test_empty_log_passes(self):
        self.assertEqual(checks.check_no_provider_requests([]), [])

    def test_any_entry_fails(self):
        for kind in ("chat", "models"):
            with self.subTest(kind=kind):
                self.assertEqual(len(checks.check_no_provider_requests([{"kind": kind}])), 1)

    def test_entries_are_counted(self):
        self.assertEqual(len(checks.check_no_provider_requests([{"kind": "models"}, {"kind": "chat"}])), 2)

    def test_healthy_netlog_passes(self):
        self.assertEqual(checks.check_no_provider_requests([], self.netlog(), "localhost:41234"), [])

    def test_annotation_in_netlog_fails(self):
        problems = checks.check_no_provider_requests([], self.netlog(unhealthy=True))
        self.assertEqual(len(problems), 1)
        self.assertIn("rac_ai_models", problems[0])

    def test_chat_annotation_fails(self):
        path = os.path.join(self.tmp.name, "chat.json")
        data = {"constants": {"logEventTypes": {"URL_REQUEST_START_JOB": 7}},
                "events": [{"type": 7, "params": {
                    "url": "https://x/", "traffic_annotation": checks.traffic_annotation_hash("rac_ai_chat")}}]}
        with open(path, "w") as f:
            json.dump(data, f)
        self.assertIn("rac_ai_chat", checks.check_no_provider_requests([], path)[0])

    def test_annotation_on_another_event_type_is_not_flagged(self):
        data = {"constants": {"logEventTypes": {"URL_REQUEST_START_JOB": 7, "OTHER": 8}},
                "events": [{"type": 8, "params": {
                    "traffic_annotation": checks.traffic_annotation_hash("rac_ai_chat")}}]}
        self.assertEqual(checks.check_netlog(data), [])

    def test_fake_model_hostport_is_flagged_anywhere(self):
        problems = checks.check_no_provider_requests([], self.netlog(unhealthy=True), "localhost:41234")
        self.assertEqual(len(problems), 2)  # the annotation and the host lookup

    def test_hostport_aliases(self):
        data = {"constants": {"logEventTypes": {"URL_REQUEST_START_JOB": 7}},
                "events": [{"type": 7, "params": {"url": "http://127.0.0.1:5555/v1/models",
                                                  "traffic_annotation": 1}}]}
        self.assertEqual(len(checks.check_netlog(data, "localhost:5555")), 1)
        self.assertEqual(checks.check_netlog(data, "localhost:5556"), [])

    def test_url_default_port(self):
        data = {"constants": {"logEventTypes": {"X": 1}},
                "events": [{"type": 1, "params": {"url": "http://localhost/v1"}}]}
        self.assertEqual(len(checks.check_netlog(data, "localhost:80")), 1)

    def test_truncated_netlog_is_repaired(self):
        self.assertEqual(checks.check_no_provider_requests([], self.netlog(truncated=True)), [])
        self.assertEqual(len(checks.check_no_provider_requests([], self.netlog(unhealthy=True, truncated=True))), 1)

    def test_garbage_and_missing_netlog_fail(self):
        path = os.path.join(self.tmp.name, "garbage.json")
        with open(path, "w") as f:
            f.write("not json")
        self.assertIn("cannot read", checks.check_no_provider_requests([], path)[0])
        self.assertIn("cannot read", checks.check_no_provider_requests([], path + ".missing")[0])


class LabelTest(unittest.TestCase):
    def test_finds_the_words(self):
        self.assertEqual(checks.find_forbidden_labels("Open the Assistant, then Chat"), ["Assistant", "Chat"])

    def test_case_insensitive(self):
        self.assertEqual(checks.find_forbidden_labels("summarize THIS agent"), ["Summarize", "Agent"])

    def test_longest_phrase_wins(self):
        self.assertEqual(checks.find_forbidden_labels("Ask AI"), ["Ask AI"])
        self.assertEqual(checks.find_forbidden_labels("Let AI do it"), ["Let AI"])
        self.assertEqual(checks.find_forbidden_labels("Ask AI or just Ask"), ["Ask AI", "Ask"])

    def test_ai_is_a_whole_word(self):
        for text in ("Maintain", "Gmail", "Said", "Rails", "Aimless", "mail", "waiting", "AIR", "Available",
                     "Chair", "Asked", "Basket", "Ask-less is fine? no: Task", "Chatham", "Agenda",
                     "Assistance", "Tai chi", "Summary"):
            with self.subTest(text=text):
                found = checks.find_forbidden_labels(text)
                self.assertNotIn("AI", found)
        self.assertEqual(checks.find_forbidden_labels("Maintain your Gmail inbox"), [])

    def test_ai_standing_alone_or_hyphenated(self):
        for text in ("AI", "ai", "Use AI.", "(AI)", "AI-powered", "the AI's answer", "turn on AI\nnow"):
            with self.subTest(text=text):
                self.assertEqual(checks.find_forbidden_labels(text), ["AI"])

    def test_multi_word_with_odd_whitespace(self):
        self.assertEqual(checks.find_forbidden_labels("Ask   AI"), ["Ask AI"])
        self.assertEqual(checks.find_forbidden_labels("Ask\nAI"), ["Ask AI"])

    def test_plurals(self):
        self.assertEqual(checks.find_forbidden_labels("Chats and Agents"), ["Chat", "Agent"])

    def test_empty_and_clean(self):
        self.assertEqual(checks.find_forbidden_labels(""), [])
        self.assertEqual(checks.find_forbidden_labels("Search or enter address"), [])

    def test_custom_list_and_ignore(self):
        self.assertEqual(checks.find_forbidden_labels("foo bar", forbidden=("Foo",)), ["Foo"])
        self.assertEqual(checks.find_forbidden_labels(
            "Ask websites not to track you", ignore=checks.BENIGN_PHRASES), [])
        self.assertEqual(checks.find_forbidden_labels("Ask websites not to track you"), ["Ask"])

    def test_allowed_surfaces(self):
        self.assertEqual(checks.ALLOWED_SURFACES, {"settings-assistant"})
        self.assertEqual(checks.check_surface_text("settings-assistant", "Turn on AI Assistant"), [])
        self.assertEqual(len(checks.check_surface_text("settings-main", "Turn on AI Assistant")), 2)

    def test_required_words_are_forbidden(self):
        for w in ("Assistant", "Ask AI", "Ask", "AI", "Chat", "Summarize", "Summarise", "Agent", "Let AI"):
            self.assertIn(w, checks.FORBIDDEN_LABELS)


class CompareStatesTest(unittest.TestCase):
    def test_same_state_passes(self):
        self.assertEqual(checks.compare_states(fabricate_state(), fabricate_state()), [])

    def test_less_is_fine(self):
        after = fabricate_state()
        after["children"] = after["children"][:1]
        self.assertEqual(checks.compare_states(fabricate_state(), after), [])

    def test_new_child_socket_dir_request_each_fail(self):
        for key, value in (("children", ["node"]), ("sockets", ["/tmp/s"]), ("mcp_dirs", ["/x"])):
            with self.subTest(key=key):
                after = fabricate_state()
                after[key] = after[key] + value
                self.assertEqual(len(checks.compare_states(fabricate_state(), after)), 1)

    def test_requests_rise_fails_but_equal_passes(self):
        after = fabricate_state()
        after["provider_requests"] = 1
        self.assertEqual(len(checks.compare_states(fabricate_state(), after)), 1)
        before = fabricate_state()
        before["provider_requests"] = 1
        self.assertEqual(checks.compare_states(before, after), [])

    def test_an_extra_renderer_of_a_known_kind_passes(self):
        after = fabricate_state()
        after["children"] = after["children"] + [after["children"][-1]]
        self.assertEqual(checks.compare_states(fabricate_state(), after), [])

    def test_unhealthy_fixture(self):
        self.assertEqual(len(checks.compare_states(fabricate_state(), fabricate_state(True))), 4)

    def test_missing_keys(self):
        self.assertTrue(checks.compare_states({}, fabricate_state()))

    def test_make_state_reads_the_same_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = checks.make_state(fabricate_ps(True), 100, fabricate_lsof(True), PROFILE,
                                      [{"kind": "chat"}], tmp=tmp)
            self.assertIn("node", state["children"])
            self.assertIn("/tmp/rac-mcp-501-tok/s", state["sockets"])
            self.assertEqual(state["provider_requests"], 1)
            self.assertFalse(any("SingletonSocket" in s for s in state["sockets"]))
            os.makedirs(os.path.join(tmp, f"rac-mcp-{os.getuid()}-t"))
            self.assertEqual(len(checks.make_state("", 1, "", PROFILE, [], tmp=tmp)["mcp_dirs"]), 1)
            self.assertEqual(checks.make_state("", 1, "", PROFILE, [], tmp=tmp,
                                               ignore={f"rac-mcp-{os.getuid()}-t"})["mcp_dirs"], [])
            clean = checks.make_state(fabricate_ps(), 100, fabricate_lsof(), PROFILE, [], tmp=tmp,
                                      ignore={f"rac-mcp-{os.getuid()}-t"})
            self.assertEqual(checks.compare_states(clean, clean), [])


class SurfacesTest(unittest.TestCase):
    def test_json_is_valid(self):
        self.assertGreaterEqual(len(surfaces.load()), 20)
        self.assertEqual(surfaces.validate(surfaces.load()), [])

    def test_required_surfaces_exist(self):
        ids = set(surfaces.by_id(surfaces.load()))
        for want in ("new-tab-page", "sidebar-full", "sidebar-hidden-edge-reveal", "right-edge-pull-handle",
                     "address-bar-toolbar", "address-bar-sidebar", "command-bar", "context-menu-page-text",
                     "context-menu-link", "context-menu-tab", "find-bar-no-match", "link-hover-option",
                     "rac-ai-page", "onboarding", "settings-main", "settings-privacy", "settings-assistant"):
            self.assertIn(want, ids)
        for menu in ("file", "edit", "view", "history", "bookmarks", "tab", "window", "help"):
            self.assertIn("menu-bar-" + menu, ids)

    def test_settings_assistant_is_the_allowed_surface(self):
        self.assertTrue(set(checks.ALLOWED_SURFACES) <= set(surfaces.by_id(surfaces.load())))

    def test_find_bar_query_has_four_words(self):
        how = surfaces.by_id(surfaces.load())["find-bar-no-match"]["how"]
        self.assertEqual(len(re.search(r"'([^']+)'", how).group(1).split()), 4)

    def test_validate_catches_problems(self):
        ok = {"id": "a-b", "how": "do it", "must_not_show": ["x"]}
        self.assertEqual(surfaces.validate([ok]), [])
        cases = {
            "empty": [],
            "not a list": {"id": "a"},
            "missing key": [{"id": "a", "how": "x"}],
            "duplicate": [ok, dict(ok)],
            "bad id": [dict(ok, id="Not Kebab")],
            "empty how": [dict(ok, how=" ")],
            "empty must_not_show": [dict(ok, must_not_show=[])],
            "bad flags": [dict(ok, launch_flags="--x")],
            "bad capture": [dict(ok, capture="video")],
            "unknown key": [dict(ok, extra=1)],
            "not an object": ["x"],
        }
        for name, bad in cases.items():
            with self.subTest(name):
                self.assertTrue(surfaces.validate(bad))

    def test_load_rejects_invalid_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "s.json")
            with open(path, "w") as f:
                json.dump({"surfaces": [{"id": "a"}]}, f)
            with self.assertRaises(ValueError):
                surfaces.load(path)

    def test_plan_outputs(self):
        plan = surfaces.plan_outputs(surfaces.load(), "/abs/out")
        self.assertEqual(len({p["screenshot"] for p in plan}), len(plan))
        self.assertTrue(all(p["screenshot"].startswith("/abs/out/") for p in plan))
        first = plan[0]
        self.assertEqual(first["screenshot"], "/abs/out/01-new-tab-page.png")
        self.assertEqual(first["text"], "/abs/out/01-new-tab-page.txt")
        self.assertIn("--rac-window-screenshot=" + first["screenshot"], first["launch_flags"])
        native = next(p for p in plan if p["id"] == "sidebar-full")
        self.assertIsNone(native["text"])
        onboarding = next(p for p in plan if p["id"] == "onboarding")
        self.assertIn("--force-first-run", onboarding["launch_flags"])

    def test_plan_outputs_wants_an_absolute_dir(self):
        with self.assertRaises(ValueError):
            surfaces.plan_outputs(surfaces.load(), "relative/dir")

    def test_check_text(self):
        by = surfaces.by_id(surfaces.load())
        self.assertEqual(surfaces.check_text(by["settings-privacy"], "Ask websites not to track you"), [])
        self.assertTrue(surfaces.check_text(by["settings-privacy"], "Assistant"))
        self.assertEqual(surfaces.check_text(by["settings-assistant"], "Assistant, Ask AI, Chat"), [])
        self.assertEqual(surfaces.check_text(by["onboarding"], "Enable AI now? Later"), [])
        self.assertTrue(surfaces.check_text(by["onboarding"], "Chat with Assistant"))


class RunnerTest(unittest.TestCase):
    def test_self_test_passes(self):
        self.assertEqual(run_ai_off.main(["--self-test"]), 0)

    def test_dry_run_means_self_test(self):
        self.assertEqual(run_ai_off.main(["--dry-run"]), 0)

    def test_plan(self):
        self.assertEqual(run_ai_off.main(["--plan"]), 0)
        self.assertGreaterEqual(len(run_ai_off.plan_steps()), 8)

    def test_self_test_rows_all_pass(self):
        ok, rows = run_ai_off.self_test(out=lambda *_: None)
        self.assertTrue(ok)
        self.assertGreaterEqual(len(rows), 10)

    def test_profile_guard(self):
        run_ai_off.assert_safe_profile(os.path.join(run_ai_off.ROOT, "build", "rac-evals-x1"))
        with tempfile.TemporaryDirectory() as tmp:
            run_ai_off.assert_safe_profile(tmp)
        for bad in (os.path.expanduser("~/Library/Application Support/me.kainoa.rac"),
                    os.path.expanduser("~/Library/Application Support/net.imput.helium"),
                    os.path.join(run_ai_off.ROOT, "build", "profile"),
                    os.path.join(run_ai_off.ROOT, "build", "rac-evals-x1", "Default"),
                    os.path.join(run_ai_off.ROOT, "build", "..", "x"),
                    "/Users/someone/Documents"):
            with self.subTest(bad=bad):
                with self.assertRaises(AssertionError):
                    run_ai_off.assert_safe_profile(bad)

    def test_seeded_preferences(self):
        prefs = run_ai_off.seed_preferences("http://localhost:1/v1")
        self.assertIs(prefs["rac"]["ai"]["enabled"], False)
        self.assertEqual(prefs["rac"]["ai"]["provider"], "custom")
        self.assertEqual(prefs["rac"]["ai"]["provider_settings"]["custom"]["base_url"], "http://localhost:1/v1")
        self.assertIs(prefs["rac"]["ai"]["browser_control"], True)
        self.assertEqual(prefs["rac"]["ai"]["agent_permission_level"], "auto")

    def test_find_browser_pid(self):
        self.assertEqual(run_ai_off.find_browser_pid(fabricate_ps(), PROFILE, BUNDLE), 100)
        self.assertIsNone(run_ai_off.find_browser_pid(fabricate_ps(), "/nope", BUNDLE))

    def test_print_summary(self):
        lines = []
        self.assertTrue(run_ai_off.print_summary([("a", [])], out=lines.append))
        self.assertFalse(run_ai_off.print_summary([("a", []), ("b", ["bad"])], out=lines.append))
        self.assertTrue(any("FAIL" in l for l in lines))


if __name__ == "__main__":
    unittest.main()
