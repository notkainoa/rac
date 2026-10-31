#!/usr/bin/env python3
# Copyright 2026 The rac Authors
# SPDX-License-Identifier: GPL-3.0-or-later
"""AI off costs nothing, set 1 (plan 05, "Proving AI off costs nothing", 2-6).

  run_ai_off.py --self-test    every check against fabricated healthy and
                               unhealthy input; no browser, no network
                               (--dry-run means the same)
  run_ai_off.py --plan         the steps of a real run, without doing any
  run_ai_off.py                a real run against a built worktree (needs the
                               binary; see README.md)

A real run, in a throwaway profile under <repo>/build/rac-evals-*:
  1. start the fake model and a tiny local web page;
  2. seed <profile>/Default/Preferences: AI OFF, but the Custom provider
     pointed at the fake model and browser control on, so a stray provider
     request would be seen rather than lost;
  3. session A: launch, sit idle, open a normal page and the WebUI surfaces,
     collect ps, lsof, the profile listing, the fake model's log; close
     through DevTools (so the net-log flushes); run the checks;
  4. session B (item 6): relaunch the same profile, turn AI on and off
     through Settings, compare the state before and after.

Everything that needs the binary is marked TODO(binary) and untested: nothing
here has driven a real build yet. Never point this at a real profile.
"""

import argparse
import glob
import http.server
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time

try:
    from . import checks, surfaces
except ImportError:  # run as a script: ai_off/ itself is on sys.path
    import checks
    import surfaces

HERE = os.path.dirname(os.path.abspath(__file__))
EVALS = os.path.dirname(HERE)
ROOT = os.path.abspath(os.path.join(EVALS, "..", "..", ".."))
PROFILE_PREFIX = "rac-evals-"
IDLE_SECONDS = 15   # how long the browser sits untouched before the first look
SETTLE_SECONDS = 5  # after each AI toggle


# --- the profile guard ------------------------------------------------------------

def assert_safe_profile(path, worktree=ROOT):
    """Raises unless path is a throwaway profile: <worktree>/build/rac-evals-*,
    or inside the system temp dir. Compared on real paths, so symlinks and
    `..` can't smuggle a real profile folder in."""
    real = os.path.realpath(path)
    build = os.path.realpath(os.path.join(worktree, "build"))
    tmp = os.path.realpath(tempfile.gettempdir())
    if "Application Support" in real:
        raise AssertionError(f"refusing a real profile folder: {path}")
    in_build = (os.path.dirname(real) == build
                and os.path.basename(real).startswith(PROFILE_PREFIX))
    in_tmp = real.startswith(tmp.rstrip("/") + "/")
    if not (in_build or in_tmp):
        raise AssertionError(f"profile must be {build}/{PROFILE_PREFIX}* or under {tmp}: {path}")


def seed_preferences(model_url):
    """Default/Preferences with AI off. Pref names checked against ai_prefs.h
    (kEnabled, kProvider, kProviderSettings, kBrowserControl,
    kAgentPermissionLevel) and pref_names.h (kHeliumServicesEnabled, so a
    throwaway profile never reaches Helium's services)."""
    prefs = {}

    def put(dotted, value):
        d, keys = prefs, dotted.split(".")
        for k in keys[:-1]:
            d = d.setdefault(k, {})
        d[keys[-1]] = value

    put("rac.ai.enabled", False)
    put("rac.ai.provider", "custom")
    put("rac.ai.provider_settings.custom.base_url", model_url)
    put("rac.ai.browser_control", True)
    put("rac.ai.agent_permission_level", "auto")
    put("helium.services.enabled", False)
    return prefs


def find_browser_pid(ps_text, profile, bundle_path):
    """The browser (main) process of the launch: inside the bundle, started
    with this profile, and without --type. The build queue may wrap it, so the
    pid Popen returned can't be trusted."""
    for p in checks.parse_ps(ps_text):
        if (f"--user-data-dir={profile}" in p["command"] and "--type=" not in p["command"]
                and checks._in_bundle(p["exe"], bundle_path)):
            return p["pid"]
    return None


# --- fabricated input (the self-test and test_checks.py use these) -----------------

BUNDLE = "/work/build/src/out/Default/rac.app"
PROFILE = "/work/build/rac-evals-abc123"
_HELPERS = BUNDLE + "/Contents/Frameworks/rac Framework.framework/Versions/1/Helpers"


def fabricate_ps(unhealthy=False):
    rows = [
        f"    1     0 /sbin/launchd",
        f"  100     1 {BUNDLE}/Contents/MacOS/rac --user-data-dir={PROFILE} --no-first-run",
        f"  101   100 {_HELPERS}/rac Helper (GPU).app/Contents/MacOS/rac Helper (GPU) --type=gpu-process",
        f"  102   100 {_HELPERS}/rac Helper.app/Contents/MacOS/rac Helper --type=utility "
        f"--utility-sub-type=network.mojom.NetworkService",
        f"  103   100 {_HELPERS}/rac Helper.app/Contents/MacOS/rac Helper --type=utility "
        f"--utility-sub-type=storage.mojom.StorageService",
        f"  104   100 {_HELPERS}/rac Helper (Renderer).app/Contents/MacOS/rac Helper (Renderer) "
        f"--type=renderer --lang=en-US",
        f"  105   100 {BUNDLE}/Contents/Frameworks/rac Framework.framework/Helpers/"
        f"chrome_crashpad_handler --monitor-self-annotation=ptype=crashpad-handler",
        f"  900     1 /usr/bin/ssh-agent -l",           # unrelated to the browser
        f"  901     1 node /Users/x/other-tool.js",      # unrelated to the browser
    ]
    if unhealthy:
        rows += [
            f"  300   100 node /Users/x/.npm/_npx/acp-agent.js --stdio",
            f"  301   300 /Users/x/.local/bin/claude --acp",
            f"  302   100 /usr/bin/nc -U {PROFILE}/rac-agent-mcp/tok/s",
            f"  303   100 {_HELPERS}/rac Helper.app/Contents/MacOS/rac Helper --type=utility "
            f"--utility-sub-type=on_device_model.mojom.OnDeviceModelService",
        ]
    return "\n".join(rows) + "\n"


def fabricate_lsof(unhealthy=False):
    rows = [
        "COMMAND     PID USER   FD   TYPE             DEVICE SIZE/OFF NODE NAME",
        "rac         100 kn      3u  unix 0x6f2c1a3e8b21c4d5      0t0      ->0x6f2c1a3e8b21c4d6",
        "rac         100 kn      4u  unix 0x6f2c1a3e8b21c4d7      0t0      ",
        "rac         100 kn      7u  unix 0x6f2c1a3e8b21c4d8      0t0      "
        "/var/folders/ab/cd/T/.org.chromium.Chromium.Xy12/SingletonSocket",
        "rac\\x20Helper 101 kn   5u  unix 0x6f2c1a3e8b21c4d9      0t0      ->0x6f2c1a3e8b21c4da",
    ]
    if unhealthy:
        rows += [
            f"rac         100 kn     12u  unix 0x6f2c1a3e8b21c4db      0t0      "
            f"{PROFILE}/rac-agent-mcp/tok/s",
            "nc          302 kn      3u  unix 0x6f2c1a3e8b21c4dc      0t0      "
            "/tmp/rac-mcp-501-tok/s",
        ]
    return "\n".join(rows) + "\n"


def fabricate_netlog(path, unhealthy=False, model_hostport="localhost:41234", truncated=False):
    types = {"REQUEST_ALIVE": 1, "URL_REQUEST_START_JOB": 2, "HOST_RESOLVER_IMPL_REQUEST": 3}
    events = [
        {"type": 1, "phase": 1, "params": {}},
        {"type": 2, "phase": 1, "params": {"url": "https://example.com/", "method": "GET",
                                           "traffic_annotation": checks.traffic_annotation_hash("other")}},
    ]
    if unhealthy:
        events.append({"type": 2, "phase": 1, "params": {
            "url": "https://api.example.org/v1/models", "method": "GET",
            "traffic_annotation": checks.traffic_annotation_hash("rac_ai_models")}})
        events.append({"type": 3, "phase": 1, "params": {"host": model_hostport}})
    text = json.dumps({"constants": {"logEventTypes": types}, "events": events})
    if truncated:  # what a killed browser leaves behind
        text = text[:-2]
    with open(path, "w") as f:
        f.write(text)


def fabricate_state(unhealthy=False):
    state = {"children": ["rac Helper", "rac Helper (GPU)", "rac Helper (Renderer)"],
             "sockets": [], "mcp_dirs": [], "provider_requests": 0}
    if unhealthy:
        state.update(children=state["children"] + ["node"], sockets=["/tmp/rac-mcp-501-tok/s"],
                     mcp_dirs=[PROFILE + "/rac-agent-mcp"], provider_requests=2)
    return state


HEALTHY_TEXT = "New Tab\nSearch or enter address\nBookmarks\nMaintain your Gmail inbox\nAsk websites not to track you"
UNHEALTHY_TEXT = "New Tab\nAsk AI anything\nOpen the Assistant\nSummarize this page"


# --- the self-test --------------------------------------------------------------------

def self_test(out=print):
    """Runs every check on fabricated healthy and unhealthy input. Returns
    (ok, rows) where each row is (name, passed, detail)."""
    rows = []

    def case(name, healthy, unhealthy):
        h, u = healthy(), unhealthy()
        ok = h == [] and u != []
        detail = (f"healthy clean, unhealthy flagged {len(u)}" if ok else
                  f"healthy gave {h[:2]}" if h else "unhealthy gave nothing")
        rows.append((name, ok, detail))

    with tempfile.TemporaryDirectory(prefix="rac-evals-selftest-") as tmp:
        good, bad = os.path.join(tmp, "good"), os.path.join(tmp, "bad")
        for d in (good, bad, os.path.join(tmp, "tmp-good"), os.path.join(tmp, "tmp-bad")):
            os.makedirs(d)
        os.makedirs(os.path.join(bad, checks.MCP_DIR_NAME))
        os.makedirs(os.path.join(tmp, "tmp-bad", f"rac-mcp-{os.getuid()}-tok"))
        case("no MCP dir", lambda: checks.check_no_mcp_dir(good, os.path.join(tmp, "tmp-good")),
             lambda: checks.check_no_mcp_dir(good, os.path.join(tmp, "tmp-bad"))
             + checks.check_no_mcp_dir(bad, os.path.join(tmp, "tmp-good")))
        case("process tree", lambda: checks.check_process_tree(fabricate_ps(), 100, BUNDLE),
             lambda: checks.check_process_tree(fabricate_ps(True), 100, BUNDLE))
        case("no agent sockets", lambda: checks.check_no_agent_sockets(fabricate_lsof(), PROFILE),
             lambda: checks.check_no_agent_sockets(fabricate_lsof(True), PROFILE))
        nl_good, nl_bad = os.path.join(tmp, "good.json"), os.path.join(tmp, "bad.json")
        fabricate_netlog(nl_good)
        fabricate_netlog(nl_bad, unhealthy=True)
        case("no provider requests",
             lambda: checks.check_no_provider_requests([], nl_good, "localhost:41234"),
             lambda: checks.check_no_provider_requests([{"kind": "models"}], nl_bad, "localhost:41234"))
        case("net-log annotation only",
             lambda: checks.check_no_provider_requests([], nl_good),
             lambda: checks.check_no_provider_requests([], nl_bad))
        case("no AI labels", lambda: surfaces.check_text({"id": "new-tab-page"}, HEALTHY_TEXT),
             lambda: surfaces.check_text({"id": "new-tab-page"}, UNHEALTHY_TEXT))
        case("AI words allowed in settings-assistant",
             lambda: surfaces.check_text({"id": "settings-assistant"}, UNHEALTHY_TEXT),
             lambda: surfaces.check_text({"id": "settings-main"}, UNHEALTHY_TEXT))
        case("back to baseline",
             lambda: checks.compare_states(fabricate_state(), fabricate_state()),
             lambda: checks.compare_states(fabricate_state(), fabricate_state(True)))
        case("surfaces.json valid", lambda: surfaces.validate(surfaces.load()),
             lambda: surfaces.validate([{"id": "a", "how": "x", "must_not_show": ["y"]},
                                        {"id": "a", "how": "x"}]))
        case("profile guard",
             lambda: [] if _guard_ok(os.path.join(ROOT, "build", PROFILE_PREFIX + "x")) else ["refused"],
             lambda: [] if _guard_ok(os.path.expanduser("~/Library/Application Support/me.kainoa.rac"))
             else ["refused"])
        ps = fabricate_ps()
        case("find browser pid",
             lambda: [] if find_browser_pid(ps, PROFILE, BUNDLE) == 100 else ["not 100"],
             lambda: [] if find_browser_pid(ps, "/other/profile", BUNDLE) else ["not found"])
        cut_good, cut_bad = os.path.join(tmp, "cut-good.json"), os.path.join(tmp, "cut-bad.json")
        fabricate_netlog(cut_good, truncated=True)
        fabricate_netlog(cut_bad, unhealthy=True, truncated=True)
        case("truncated net-log is still read",
             lambda: checks.check_no_provider_requests([], cut_good),
             lambda: checks.check_no_provider_requests([], cut_bad))
        vectors = {"test": 3556498, "unique_id": 10236504, "123_id": 70581310,
                   "ID123": 69491511, "bébé": 124751853}
        wrong = [k for k, v in vectors.items() if checks.traffic_annotation_hash(k) != v]
        case("annotation hash vectors", lambda: [f"wrong: {wrong}"] if wrong else [], lambda: ["x"])
    for name, ok, detail in rows:
        out(f"{'PASS' if ok else 'FAIL'}  {name}: {detail}")
    return all(ok for _, ok, _ in rows), rows


def _guard_ok(path):
    try:
        assert_safe_profile(path)
        return True
    except AssertionError:
        return False


# --- the plan -------------------------------------------------------------------------

def plan_steps():
    return [
        f"make a throwaway profile under {ROOT}/build/{PROFILE_PREFIX}* (assert it is safe)",
        "start the fake model (fake_model.serve(0)) and a local web page",
        "seed Default/Preferences: rac.ai.enabled=false, provider=custom -> the fake model, "
        "browser_control=true, agent_permission_level=auto",
        "session A: launch the built rac binary with the profile, DevTools on 127.0.0.1, "
        "--log-net-log, --rac-launch-in-background",
        f"session A: sit idle {IDLE_SECONDS} s, open the local page, open each WebUI surface and "
        "read its text (item 5)",
        "session A: collect ps, lsof -U, the profile listing, /tmp/rac-mcp-*, the fake model log",
        "session A: Browser.close over DevTools (flushes the net-log), then run checks 2, 3, 4, 5",
        "session B (item 6): relaunch the same profile, record the baseline state",
        "session B: set rac.ai.enabled true via chrome.settingsPrivate on chrome://settings, "
        f"wait {SETTLE_SECONDS} s, set it false, wait {SETTLE_SECONDS} s, record the state",
        "session B: close, compare_states(before, after)",
        "print a summary table; exit non-zero on any problem; delete the profile "
        "unless --keep-profile",
    ]


# --- the real run (TODO(binary), untested) ---------------------------------------------

class Rig:
    """The fake model and a tiny web page, in this process."""

    def __init__(self):
        import fake_model  # evals/fake_model.py; real_run puts evals/ on sys.path
        self.model, self.model_state = fake_model.serve(0)
        threading.Thread(target=self.model.serve_forever, daemon=True).start()

        class Page(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                body = b"<!doctype html><title>plain page</title><p>A plain page for the idle check.</p>"
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *_):
                pass

        self.web = fake_model.QuietHTTPServer(("127.0.0.1", 0), Page)
        threading.Thread(target=self.web.serve_forever, daemon=True).start()

    @property
    def model_port(self):
        return self.model.server_address[1]

    @property
    def model_url(self):
        return f"http://localhost:{self.model_port}/v1"

    @property
    def model_hostport(self):
        return f"localhost:{self.model_port}"

    @property
    def page_url(self):
        return f"http://127.0.0.1:{self.web.server_address[1]}/"

    def stop(self):
        for s in (self.model, self.web):
            s.shutdown()
            s.server_close()


def sh(*argv):
    r = subprocess.run(argv, capture_output=True, text=True, timeout=30)
    return r.stdout


class Session:
    """One launch of the browser on the profile."""

    def __init__(self, run, worktree, profile, bundle, netlog):
        self.run, self.worktree, self.profile = run, worktree, profile
        self.bundle, self.netlog = bundle, netlog
        self.log = open(os.path.join(profile, "launch.log"), "ab")
        # Session B relaunches on session A's profile: the stale
        # DevToolsActivePort must go first, or the wait below reads the
        # dead port and the new launch looks like it never came up.
        try:
            os.remove(os.path.join(profile, "DevToolsActivePort"))
        except OSError:
            pass
        # run.launch_args launches the app binary itself and passes the extra
        # flags through to the browser; the build queue wraps it unless
        # RAC_EVALS_NO_QUEUE=1.
        argv = run.launch_args(profile, worktree) + [
            f"--log-net-log={netlog}", "--net-log-capture-mode=Everything"]
        self.proc = subprocess.Popen(argv, cwd=worktree, start_new_session=True,
                                     env=run.launch_env(profile),
                                     stdout=self.log, stderr=subprocess.STDOUT)
        try:
            self.port = run.wait_for(lambda: run.devtools_port(profile),
                                     "the DevTools port file", 120, self.proc)
            endpoint = run.wait_for(lambda: run.http_json(f"http://127.0.0.1:{self.port}/json/version"),
                                    "the DevTools endpoint", 120, self.proc)
            import cdp
            self.cdp = cdp.Cdp(endpoint["webSocketDebuggerUrl"])
            self.pid = run.wait_for(lambda: find_browser_pid(sh("ps", "-axo", "pid=,ppid=,command="),
                                                             profile, bundle),
                                    "the browser process", 30, self.proc)
        except Exception:
            # A launch that never came up must not leak: kill it before
            # real_run's finally deletes the profile out from under it.
            run.kill_run(self.proc, profile)
            self.log.close()
            raise

    def open_page(self, url):
        target = self.cdp.call("Target.createTarget", {"url": url})["targetId"]
        return self.run.Page(self.cdp, target)

    def collect(self):
        ps_text = sh("ps", "-axo", "pid=,ppid=,command=")
        pids = [self.pid] + [p["pid"] for p in checks.descendants(checks.parse_ps(ps_text), self.pid)]
        lsof_text = sh("lsof", "-nP", "-U", "-a", "-p", ",".join(map(str, pids)))
        return ps_text, lsof_text

    def close(self):
        try:
            self.cdp.call("Browser.close")  # flushes the net-log and prefs; kill would lose them
        except Exception:
            pass
        try:
            self.proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            self.run.kill_run(self.proc, self.profile)
        self.log.close()


def find_bundle(worktree):
    """The dev build's app, in <worktree>/build/src/out/Default."""
    found = sorted(glob.glob(os.path.join(worktree, "build", "src", "out", "Default", "*.app")))
    return found[0] if found else None


# Writes rac.ai.enabled through the same call the toggle makes, then reads the
# pref back, resolving to {ok, value}: ok false when settingsPrivate reports a
# lastError, value the read-back pref (null when it can't be read). Without
# the read-back a failed write is silent and the run ends up comparing
# "never on" with "still off".
SETTINGS_SET_PREF = (
    "new Promise(r => chrome.settingsPrivate.setPref('rac.ai.enabled', %s, '', () => {"
    "  const e = chrome.runtime.lastError;"
    "  if (e) { r({ok: false, value: null, error: e.message}); return; }"
    "  try {"
    "    chrome.settingsPrivate.getPref('rac.ai.enabled', p => r({ok: true, value: p ? p.value : null}));"
    "  } catch (err) { r({ok: true, value: null}); }"
    "}))")


def set_ai_enabled(settings, enabled):
    """One toggle: setPref(rac.ai.enabled, `enabled`) on the Settings page,
    verified. True only when the write went through without a lastError and
    the pref reads back as `enabled` (or can't be read back at all); False
    means the toggle provably didn't take."""
    try:
        got = settings.eval(SETTINGS_SET_PREF % json.dumps(enabled))
    except Exception:
        return False
    if not isinstance(got, dict) or not got.get("ok"):
        return False
    return got.get("value") in (None, enabled)


def surface_coverage():
    """(covered, uncovered) surface ids: `covered` are read by the run's WebUI
    text check (the same predicate real_run uses), `uncovered` are everything
    else — screenshot-only surfaces nobody's text check reads."""
    covered = {s["id"] for s in surfaces.load()
               if s.get("capture") == "devtools+screenshot" and s.get("url")}
    all_ids = [s["id"] for s in surfaces.load()]
    return [i for i in all_ids if i in covered], [i for i in all_ids if i not in covered]


def real_run(args):
    """Returns a list of (check, problems)."""
    sys.path.insert(0, EVALS)
    import run
    worktree = os.path.realpath(args.worktree)
    bundle = args.bundle or find_bundle(worktree)
    if not bundle or not os.path.isdir(bundle):
        sys.exit("no app bundle found; build first (source dev.sh && he build) or pass --bundle")
    profile = run.make_profile(worktree)
    assert_safe_profile(profile, worktree)
    rig = Rig()
    results = []
    session = None
    try:
        with open(os.path.join(profile, "Default", "Preferences"), "w") as f:
            json.dump(seed_preferences(rig.model_url), f)
        tmp_before = {os.path.basename(p) for p in glob.glob("/tmp/rac-mcp-*")}

        # session A: items 2-5
        netlog = os.path.join(profile, "netlog.json")
        session = Session(run, worktree, profile, bundle, netlog)
        time.sleep(IDLE_SECONDS)
        session.open_page(rig.page_url)
        time.sleep(2)
        label_problems = []
        for s in surfaces.load():
            # TODO(binary): only WebUI pages with a url can be read this way;
            # the rest need the screenshot driver (see README).
            if s.get("capture") == "devtools+screenshot" and s.get("url"):
                page = session.open_page(s["url"])
                time.sleep(2)
                label_problems += surfaces.check_text(s, page.eval(surfaces.PAGE_TEXT_JS) or "")
        ps_text, lsof_text = session.collect()
        listing = sorted(os.listdir(profile))
        model_log = list(rig.model_state.log)
        session.close()
        session = None
        results += [
            ("no MCP dir", checks.check_no_mcp_dir(profile, ignore=tmp_before)),
            ("no extra child processes", checks.check_process_tree(ps_text, find_browser_pid(
                ps_text, profile, bundle) or -1, bundle)),
            ("no agent sockets", checks.check_no_agent_sockets(lsof_text, profile)),
            ("no provider requests", checks.check_no_provider_requests(
                model_log, netlog, rig.model_hostport)),
            ("no AI labels (WebUI text)", label_problems),
        ]
        print("profile listing:", ", ".join(listing))

        # session B: item 6
        session = Session(run, worktree, profile, bundle, os.path.join(profile, "netlog-b.json"))
        time.sleep(IDLE_SECONDS)
        ps_text, lsof_text = session.collect()
        before = checks.make_state(ps_text, session.pid, lsof_text, profile, [], ignore=tmp_before)
        settings = session.open_page("chrome://settings/")
        time.sleep(2)
        # rac.ai.enabled is in the settingsPrivate allow-list (prefs_util.cc),
        # so the same call the toggle button makes flips it. Each write is
        # verified: a toggle that didn't take would make the before/after
        # comparison meaningless ("never on" vs "still off" both look clean).
        toggle = []
        if not set_ai_enabled(settings, True):
            toggle.append("setPref(rac.ai.enabled, true) did not take; "
                          "the 'on' half of this item never ran")
        time.sleep(SETTLE_SECONDS)
        off_at = len(rig.model_state.log)
        if not set_ai_enabled(settings, False):
            toggle.append("setPref(rac.ai.enabled, false) did not take; "
                          "AI may still be on")
        time.sleep(SETTLE_SECONDS)
        ps_text, lsof_text = session.collect()
        after = checks.make_state(ps_text, session.pid, lsof_text, profile,
                                  rig.model_state.log[off_at:], ignore=tmp_before)
        session.close()
        session = None
        results.append(("AI on then off returns to baseline",
                        toggle + checks.compare_states(before, after)))
    finally:
        if session:
            session.close()
        rig.stop()
        if not args.keep_profile and os.path.basename(profile).startswith(PROFILE_PREFIX):
            assert_safe_profile(profile, worktree)
            shutil.rmtree(profile, ignore_errors=True)
    return results


def print_summary(results, out=print):
    out(f"{'check':40} result")
    for name, problems in results:
        out(f"{name:40} {'PASS' if not problems else 'FAIL (%d)' % len(problems)}")
        for p in problems:
            out(f"    {p}")
    # Never let a green summary imply every surface was checked: only the
    # WebUI surfaces have a text check; the rest are screenshot-only.
    covered, uncovered = surface_coverage()
    out(f"\nWebUI text checks cover {len(covered)} of "
        f"{len(covered) + len(uncovered)} surfaces:")
    out("    " + ", ".join(covered))
    out(f"NOT covered by text checks ({len(uncovered)} surfaces; screenshots "
        "need a person or a driver against must_not_show):")
    out("    " + ", ".join(uncovered))
    return all(not p for _, p in results)


def _raise_interrupt(signum, frame):
    raise KeyboardInterrupt


def main(argv=None):
    # A killed run must still reach real_run's finally: without this,
    # SIGTERM/SIGHUP drop the process outright and leave the browser up
    # with an open DevTools port.
    for sig in (signal.SIGTERM, signal.SIGHUP):
        signal.signal(sig, _raise_interrupt)
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--self-test", "--dry-run", dest="self_test", action="store_true",
                    help="check the checks on fabricated input; no browser")
    ap.add_argument("--plan", action="store_true", help="print the steps of a real run")
    ap.add_argument("--bundle", help="path to the built .app (default: guess in build/src/out/Default)")
    ap.add_argument("--worktree", default=ROOT,
                    help="the checkout whose built rac runs (its devutils/rac and build/)")
    ap.add_argument("--keep-profile", action="store_true")
    args = ap.parse_args(argv)
    if args.self_test:
        ok, _ = self_test()
        print("self-test:", "ok" if ok else "FAILED")
        return 0 if ok else 1
    if args.plan:
        for i, step in enumerate(plan_steps(), 1):
            print(f"{i:2}. {step}")
        print(f"\nsurfaces ({len(surfaces.load())}):", ", ".join(s["id"] for s in surfaces.load()))
        return 0
    return 0 if print_summary(real_run(args)) else 1


if __name__ == "__main__":
    sys.exit(main())
