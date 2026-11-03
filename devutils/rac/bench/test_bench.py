# Copyright 2026 The rac Authors
# SPDX-License-Identifier: GPL-3.0-or-later
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest import mock

import bench


class FakeProc:
    """A subprocess.run result stub: .stdout is what matters."""

    def __init__(self, stdout="", returncode=0):
        self.stdout, self.returncode = stdout, returncode


class StatsTest(unittest.TestCase):
    def test_summarize_gives_median_min_max_n(self):
        s = bench.summarize([3.0, 1.0, 2.0, None, "x"])
        self.assertEqual(s, {"median": 2.0, "min": 1.0, "max": 3.0, "n": 3})

    def test_summarize_is_none_over_no_numbers(self):
        self.assertIsNone(bench.summarize([]))
        self.assertIsNone(bench.summarize([None, "x"]))

    def test_fmt_cell_marks_missing_data(self):
        self.assertEqual(bench.fmt_cell(None), "—")
        cell = bench.fmt_cell({"median": 1.5, "min": 1.0, "max": 2.0, "n": 2})
        self.assertIn("1.5", cell)
        self.assertIn("n=2", cell)


def sample_doc():
    return {"format": 1, "started": "2026-01-01T00:00:00Z", "rounds": 2,
            "host": "Darwin 25.0.0 arm64",
            "apps": [{"name": "rac", "path": "/a/rac.app"},
                     {"name": "helium", "path": "/a/Helium.app"}],
            "samples": [
                {"app": "rac", "round": 1,
                 "metrics": {"cold_launch_ms": 900.0, "mem_1tab_mb": 400.0,
                             "idle_wakeups": 30, "extra_ms": 120.0},
                 "errors": []},
                {"app": "helium", "round": 1,
                 "metrics": {"cold_launch_ms": 600.0, "mem_1tab_mb": 300.0,
                             "idle_wakeups": 10},
                 "errors": []},
                {"app": "rac", "round": 2,
                 "metrics": {"cold_launch_ms": 1100.0, "mem_1tab_mb": 500.0,
                             "idle_wakeups": 50, "extra_ms": 160.0},
                 "errors": [{"metric": "tab_switch_ms",
                             "error": "rAF never fired; screenshot fallback"}]},
                {"app": "helium", "round": 2,
                 "metrics": {"cold_launch_ms": 700.0, "mem_1tab_mb": 350.0,
                             "idle_wakeups": 20},
                 "errors": []}]}


class ReportTest(unittest.TestCase):
    def test_plain_report_has_medians_and_rac_over_helium_ratio(self):
        out = bench.format_report(sample_doc())
        self.assertIn("cold_launch_ms", out)
        # rac median 1000, helium median 650 -> 1.538
        self.assertIn("1.538", out)
        self.assertIn("900–1100", out)      # rac's min–max
        self.assertIn("n=2", out)
        self.assertIn("rac/helium", out)
        self.assertIn("—", out)              # helium never got extra_ms
        self.assertIn("rAF never fired", out)  # fallback note listed

    def test_markdown_report_is_a_table(self):
        out = bench.format_report(sample_doc(), markdown=True)
        lines = out.splitlines()
        self.assertTrue(lines[0].startswith("| metric | rac | helium | rac/helium |"))
        self.assertIn("| --- | --- | --- | --- |", lines[1])
        row = next(l for l in lines if l.startswith("| cold_launch_ms"))
        self.assertIn("1.538", row)

    def test_report_with_one_app_has_no_ratio_column(self):
        doc = sample_doc()
        doc["apps"] = doc["apps"][:1]
        doc["samples"] = [s for s in doc["samples"] if s["app"] == "rac"]
        out = bench.format_report(doc)
        self.assertNotIn("rac/helium", out)

    def test_ratio_is_over_helium_even_with_two_rac_builds(self):
        self.assertEqual(bench.ratio_pair(["rac", "rac-next", "helium"]),
                         ("rac", "helium"))
        self.assertIsNone(bench.ratio_pair(["rac", "rac-next"]))

    def test_zero_helium_median_gives_no_ratio_not_a_crash(self):
        doc = sample_doc()
        for s in doc["samples"]:
            if s["app"] == "helium":
                s["metrics"]["idle_wakeups"] = 0
        out = bench.format_report(doc)
        line = next(l for l in out.splitlines() if l.startswith("idle_wakeups"))
        self.assertTrue(line.rstrip().endswith("—"), line)

    def test_an_app_with_no_cold_launch_is_a_failed_bench(self):
        doc = sample_doc()
        self.assertEqual(bench.missing_core(doc), [])
        for s in doc["samples"]:
            if s["app"] == "helium":
                s["metrics"] = {}
        self.assertEqual(bench.missing_core(doc), ["helium"])

    def test_report_cli_reads_the_file(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "results.json")
            with open(path, "w") as f:
                json.dump(sample_doc(), f)
            out = io.StringIO()
            with redirect_stdout(out):
                self.assertEqual(bench.main(["report", path]), 0)
            self.assertIn("cold_launch_ms", out.getvalue())


class ProfileTest(unittest.TestCase):
    def test_profile_is_fresh_under_the_temp_dir(self):
        with tempfile.TemporaryDirectory() as base:
            p = bench.make_profile(base)
            self.addCleanup(lambda: __import__("shutil").rmtree(p, ignore_errors=True))
            self.assertTrue(os.path.basename(p).startswith("rac-bench-"))
            self.assertEqual(os.path.dirname(p), os.path.realpath(base))

    def test_application_support_paths_are_refused(self):
        for base in ("/Users/someone/Library/Application Support/me.kainoa.rac",
                     os.path.expanduser("~/Library/Application Support")):
            with self.assertRaises(AssertionError):
                bench.make_profile(base)


class ArgsTest(unittest.TestCase):
    def test_every_app_gets_the_same_flags_and_none_is_rac_only(self):
        rac = bench.launch_args("/a/rac", "/tmp/rac-bench-x")[1:]
        helium = bench.launch_args("/a/Helium", "/tmp/rac-bench-y")[1:]
        self.assertEqual([a.replace("rac-bench-x", "P") for a in rac],
                         [a.replace("rac-bench-y", "P") for a in helium])
        self.assertFalse([a for a in rac if "rac-launch" in a])

    def test_launch_args_match_the_spec(self):
        argv = bench.launch_args("/a/Helium", "/tmp/rac-bench-p")
        self.assertEqual(argv, [
            "/a/Helium", "--user-data-dir=/tmp/rac-bench-p",
            "--no-first-run", "--no-default-browser-check",
            "--disable-background-networking", "--disable-component-update",
            "--use-mock-keychain",
            "--remote-debugging-port=0", "--remote-debugging-address=127.0.0.1"])
        self.assertFalse([a for a in argv if "Application Support" in a])

    def test_rounds_alternate_which_app_goes_first(self):
        apps = ["rac", "helium"]
        self.assertEqual(bench.round_order(apps, 1), ["rac", "helium"])
        self.assertEqual(bench.round_order(apps, 2), ["helium", "rac"])
        self.assertEqual(bench.round_order(apps, 3), ["rac", "helium"])

    def test_app_spec_parses_name_equals_path(self):
        self.assertEqual(bench.parse_app_spec("rac=/a/rac.app"),
                         {"name": "rac", "path": "/a/rac.app"})
        for bad in ("rac", "=/a", "rac="):
            with self.assertRaises(Exception):
                bench.parse_app_spec(bad)

    def test_launch_env_points_crashpad_into_the_profile(self):
        env = bench.launch_env("/tmp/rac-bench-p")
        self.assertEqual(env["BREAKPAD_DUMP_LOCATION"],
                         "/tmp/rac-bench-p/Crashpad")

    def test_app_executable_accepts_a_binary_or_a_bundle(self):
        with tempfile.TemporaryDirectory() as d:
            binary = os.path.join(d, "helium")
            open(binary, "w").close()
            self.assertEqual(bench.app_executable(binary), binary)
            bundle = os.path.join(d, "Helium.app")
            macos = os.path.join(bundle, "Contents", "MacOS")
            os.makedirs(macos)
            open(os.path.join(macos, "Helium"), "w").close()
            self.assertEqual(bench.app_executable(bundle),
                             os.path.join(macos, "Helium"))
            with self.assertRaises(RuntimeError):
                bench.app_executable(os.path.join(d, "nope.app"))


class ProcessTreeTest(unittest.TestCase):
    TREE = {
        ("pgrep", "-P"): {100: "101\n102\n", 101: "103\n", 102: "", 103: "104\n100\n", 104: ""},
    }

    def run_tree(self, cmd):
        if cmd[:2] == ["pgrep", "-P"]:
            return FakeProc(self.TREE[("pgrep", "-P")].get(int(cmd[2]), ""))
        if cmd[0] == "ps":
            return FakeProc(self.ps_output)
        return FakeProc("")

    def test_tree_pids_walks_descendants_without_cycles(self):
        self.ps_output = ""
        pids = bench.tree_pids(100, self.run_tree)
        self.assertEqual(pids, {100, 101, 102, 103, 104})

    def test_tree_rss_aggregates_the_whole_tree(self):
        self.ps_output = " 1000\n 2000\n  500\n junk\n"
        kb = bench.tree_rss_kb(100, self.run_tree)
        self.assertEqual(kb, 3500)

    def test_parse_cputime_handles_mm_ss_and_hh_mm_ss(self):
        self.assertEqual(bench.parse_cputime("0:01.50"), 1.5)
        self.assertEqual(bench.parse_cputime("1:02:03.50"), 3723.5)
        self.assertEqual(bench.parse_cputime("junk"), 0.0)

    def test_tree_cputime_sums_rows(self):
        self.ps_output = " 0:01.00\n 0:02.50\n"
        self.assertEqual(bench.tree_cputime_s(100, self.run_tree), 3.5)


TOP_OUTPUT = """Processes: 10 total, 1 running
PID    %CPU IDLEW
1      5.0  100
2      1.0  50
Processes: 11 total, 2 running
PID    %CPU IDLEW
100    0.5  7
101    0.0  3
999    9.9  42
"""


class CpuDeltaTest(unittest.TestCase):
    def test_idle_cpu_ignores_processes_that_started_mid_window(self):
        # Pid 102 is born during the window with 50 s of cpu already used;
        # only 100 and 101 count, 1 s each.
        state = {"after": False}

        def run(cmd):
            if cmd[:2] == ["pgrep", "-P"]:
                kids = "101\n102\n" if state["after"] else "101\n"
                return FakeProc(kids if cmd[2] == "100" else "")
            if cmd[0] == "top":
                state["after"] = True
                return FakeProc("")
            if cmd[0] == "ps":
                rows = (" 0:11.00\n 0:21.00\n 0:50.00\n" if state["after"]
                        else " 0:10.00\n 0:20.00\n")
                return FakeProc(rows)
            return FakeProc("")
        cpu, _ = bench.idle_sample(100, 30, run)
        self.assertAlmostEqual(cpu, 2.0 / 30 * 100)


class TopTest(unittest.TestCase):
    def test_parse_top_sample_reads_the_last_sample_only(self):
        rows = bench.parse_top_sample(TOP_OUTPUT)
        self.assertEqual(rows, {100: (0.5, 7), 101: (0.0, 3), 999: (9.9, 42)})

    def test_parse_top_sample_on_empty_output(self):
        self.assertEqual(bench.parse_top_sample(""), {})

    def test_idle_sample_combines_cputime_delta_and_top_wakeups(self):
        # pgrep reports no children, so the tree is {100} alone: top rows for
        # 101 and 999 don't count toward wakeups.
        calls = iter([" 0:10.00\n", " 0:11.50\n"])

        def run(cmd):
            if cmd[0] == "ps":
                return FakeProc(next(calls))
            if cmd[0] == "top":
                return FakeProc(TOP_OUTPUT)
            return FakeProc("")

        cpu, wake = bench.idle_sample(100, 30, run)
        self.assertAlmostEqual(cpu, (11.5 - 10.0) / 30 * 100)
        self.assertEqual(wake, 7)


class DevtoolsPortTest(unittest.TestCase):
    def test_reads_the_first_line_or_is_none(self):
        with tempfile.TemporaryDirectory() as profile:
            self.assertIsNone(bench.devtools_port(profile))
            path = os.path.join(profile, "DevToolsActivePort")
            open(path, "w").close()
            self.assertIsNone(bench.devtools_port(profile))
            with open(path, "w") as f:
                f.write("41234\n/devtools/browser/abc\n")
            self.assertEqual(bench.devtools_port(profile), 41234)


class ParseCliTest(unittest.TestCase):
    def test_run_rejects_duplicate_app_names(self):
        err = io.StringIO()
        with self.assertRaises(SystemExit), \
                mock.patch("sys.stderr", err):
            bench.main(["run", "--app", "x=/a", "--app", "x=/b",
                        "--rounds", "1", "--out", "/tmp/rac-bench-test.json"])

    def test_run_rejects_zero_rounds(self):
        err = io.StringIO()
        with self.assertRaises(SystemExit), \
                mock.patch("sys.stderr", err):
            bench.main(["run", "--app", "x=/a", "--rounds", "0",
                        "--out", "/tmp/rac-bench-test.json"])


if __name__ == "__main__":
    unittest.main()


class TypingTest(unittest.TestCase):
    def test_clock_stops_at_the_input_event_before_key_release(self):
        calls = []

        class FakePage:
            def eval(self, js, **kw):
                calls.append("eval-wait" if "timeout" in kw else "eval-arm")
                return "armed"

            def call(self, method, params):
                calls.append(params["type"])

        bench.measure_typing(FakePage())
        self.assertEqual(calls, ["eval-arm", "keyDown", "eval-wait", "keyUp"])
