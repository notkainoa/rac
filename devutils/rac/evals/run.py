#!/usr/bin/env python3
# Copyright 2026 The rac Authors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Tier 1b runner: hostile fixtures against the real agent, graded.

  run.py --list                       the variants
  run.py --dry-run today|d19          no browser: fixtures + fake model + the
                                      Python stand-in agent (sim_agent.py)
  run.py [--variants a,b]             launch the build and run for real
                                      (needs a built worktree; see README)
  run.py --screenshots ...            also write proof PNGs of the window to
                                      <results-dir>/shots/ (real runs only)

A real run, per variant, in a throwaway profile:
  1. start the fixture server (one port per origin) and the fake model;
  2. seed <profile>/Default/Preferences: AI on, browser control on, the Custom
     provider pointed at the fake model, the level and site rules under test;
  3. launch the built binary `build/src/out/Default/rac.app/Contents/MacOS/rac`
     with `--user-data-dir=<profile> --remote-debugging-port` (through the
     build queue's run slot unless RAC_EVALS_NO_QUEUE=1), save the fake
     provider's key through Settings;
  4. open the fixture tabs, open chrome://rac-ai, send each turn with
     racAiSend, answer every card as grade.simulated_answer says, wait for
     the run to end;
  5. write results/<id>.json (the run record grade.py reads) and grade it.

Everything that needs the binary is marked TODO(binary) and untested: nothing
here has driven a real build yet. Never point this at a real profile.
"""

import argparse
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request

# The runner's own modules sit next to it; make that work under python3 -I too.
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import cdp  # noqa: E402
import fake_model
import fixture_server
import grade
import sim_agent
import sim_browser
import variants

ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
STATUS_CONTEXT = "rac/agent-evals"
RUN_TIMEOUT = 120          # seconds a turn may take before it counts as timed out
FAKE_KEY = "eval-fake-key"  # the fake model ignores it; Custom insists on one


# --- small helpers ---------------------------------------------------------

def deep_set(d, dotted, value):
    keys = dotted.split(".")
    for k in keys[:-1]:
        d = d.setdefault(k, {})
    d[keys[-1]] = value


def expand(obj, origins):
    """Replaces {origin:NAME} in every string, dict keys included."""
    if isinstance(obj, str):
        return re.sub(r"\{origin:([a-z0-9]+)\}", lambda m: origins[m.group(1)], obj)
    if isinstance(obj, list):
        return [expand(o, origins) for o in obj]
    if isinstance(obj, dict):
        return {expand(k, origins): expand(v, origins) for k, v in obj.items()}
    return obj


def flat_prefs(variant, origins):
    prefs = {"rac.ai.agent_permission_level": variant["level"]}
    prefs.update(variant.get("prefs", {}))
    return expand(prefs, origins)


def tab_url(ref, origins):
    origin, path = ref.split(":", 1)
    return origins[origin] + path


def post_json(url, payload):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.load(r)


class Rig:
    """Fixture server + fake model for one variant, in this process."""

    def __init__(self, variant, host_mode="names"):
        self.variant = variant
        self.fixtures = fixture_server.FixtureServer(variant, host_mode).start()
        self.model, self.model_state = fake_model.serve(0)
        threading.Thread(target=self.model.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()
        with open(variant["model_path"]) as f:
            self.model_state.script = json.load(f)
        self.model_state.origins = self.fixtures.base

    @property
    def model_url(self):
        return f"http://localhost:{self.model.server_address[1]}/v1"

    def record(self, mode, turns, answers, downloads=()):
        return {"variant": self.variant["id"], "mode": mode, "level": self.variant["level"],
                "turns": turns, "model_log": list(self.model_state.log),
                "attacker_log": self.fixtures.snapshot_log(), "answers": answers,
                "downloads": list(downloads)}

    def stop(self):
        self.fixtures.stop()
        self.model.shutdown()
        self.model.server_close()


# --- dry run -----------------------------------------------------------------

def run_dry(variant, mode):
    """`mode` is "today" (the guard as it is) or "d19" (the reference fix)."""
    rig = Rig(variant)
    try:
        browser, aliases = sim_browser.SimBrowser(), {}
        prefs = flat_prefs(variant, rig.fixtures.base)
        sim_prefs = {"level": prefs["rac.ai.agent_permission_level"],
                     "site_rules": prefs.get("rac.ai.agent_site_rules", {})}
        agent = sim_agent.SimAgent(rig.model_url, browser, variant, sim_prefs, mode == "d19",
                                   lambda _card: grade.simulated_answer(variant))
        turns = []
        for i, turn in enumerate(variant["turns"]):
            for ref in turn.get("open", []):
                if ref not in aliases:
                    aliases[ref] = browser.open_tab(tab_url(ref, rig.fixtures.base)).alias
            run = agent.run_turn(expand(turn["user"], rig.fixtures.base),
                                 [aliases[r] for r in turn.get("attach", [])])
            turns.append({"index": i, "user": expand(turn["user"], rig.fixtures.base), **run})
        return rig.record("sim-" + mode, turns, agent.answers)
    finally:
        rig.stop()


# --- real browser ---------------------------------------------------------------

def build_preferences(variant, origins, model_base_url, download_dir):
    """The seeded Default/Preferences, as nested JSON."""
    prefs = {}
    for dotted, value in {
        "rac.ai.enabled": True,
        "rac.ai.provider": "custom",
        "rac.ai.provider_settings": {"custom": {
            "base_url": model_base_url, "model": fake_model.MODEL_IDS[0],
            "models": [fake_model.MODEL_IDS[0]]}},
        "rac.ai.browser_control": True,
        "rac.ai.save_history": False,
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "helium.browser.layout": 2,
    }.items():
        deep_set(prefs, dotted, value)
    for dotted, value in flat_prefs(variant, origins).items():
        deep_set(prefs, dotted, value)
    return prefs


def make_profile(worktree, base_dir=None):
    """A throwaway profile, only ever under <worktree>/build or a temp dir."""
    base = os.path.realpath(base_dir or os.path.join(worktree, "build"))
    allowed = [os.path.realpath(os.path.join(worktree, "build")),
               os.path.realpath(tempfile.gettempdir())]
    assert "Application Support" not in base and any(
        base == a or base.startswith(a + os.sep) for a in allowed), f"refusing profile folder {base}"
    os.makedirs(base, exist_ok=True)
    path = tempfile.mkdtemp(prefix="rac-evals-", dir=base)
    os.makedirs(os.path.join(path, "Default"))
    return path


def clean_stale_profiles(worktree, max_age_s=6 * 3600):
    """Removes rac-evals-* profiles a killed run or --keep-profile left in
    <worktree>/build, once they are older than max_age_s and no process
    still uses them."""
    base = os.path.join(worktree, "build")
    if not os.path.isdir(base):
        return
    now = time.time()
    for name in os.listdir(base):
        path = os.path.join(base, name)
        if not name.startswith("rac-evals-") or not os.path.isdir(path):
            continue
        if now - os.path.getmtime(path) < max_age_s:
            continue
        busy = subprocess.run(["pgrep", "-f", "--", f"--user-data-dir={path}"],
                              capture_output=True).returncode == 0
        if not busy:
            shutil.rmtree(path, ignore_errors=True)


def free_port():
    import socket
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def launch_env(profile):
    """The launch environment. Crash dumps go into the throwaway profile, so a
    dev run never writes the real me.kainoa.rac/Crashpad (PR #25 does the
    same in worktree.sh; this holds even without it)."""
    env = dict(os.environ)
    env["BREAKPAD_DUMP_LOCATION"] = os.path.join(profile, "Crashpad")
    return env


def browser_binary(worktree):
    """The dev build's binary inside the app bundle."""
    return os.path.join(worktree, "build", "src", "out", "Default",
                        "rac.app", "Contents", "MacOS", "rac")


def launch_args(profile, port, worktree, shots=None):
    """The launch command: the app binary itself, so a remote eval host needs
    only the build output, not the checkout's run scripts. --use-mock-keychain
    lets OSCrypt store the fake provider's key without the real keychain (what
    worktree.sh supplied). The build queue wraps the launch in a run slot;
    RAC_EVALS_NO_QUEUE=1 runs the binary directly. `shots`, a Shots, adds the
    window-screenshot dev switches."""
    binary = browser_binary(worktree)
    if not os.path.exists(binary):
        raise RuntimeError(f"no built rac at {binary}; build the worktree first")
    argv = [binary,
            f"--user-data-dir={profile}", "--use-mock-keychain",
            "--disable-features=DialMediaRouteProvider",
            f"--remote-debugging-port={port}", "--remote-debugging-address=127.0.0.1",
            "--rac-launch-in-background", "--no-first-run", "--no-default-browser-check",
            "--disable-background-networking", "--disable-component-update"]
    if shots is not None:
        # window_screenshot.mm only polls the requests file when the main
        # screenshot switch is also set, so a boot capture has to come too.
        argv += [f"--rac-window-screenshot={shots.boot}",
                 f"--rac-window-screenshot-requests={shots.requests}"]
    if os.environ.get("RAC_EVALS_NO_QUEUE") == "1":
        return argv
    queue = os.path.join(worktree, "devutils", "rac", "build-queue.sh")
    if not os.path.exists(queue):
        raise RuntimeError(f"no build queue at {queue}; set RAC_EVALS_NO_QUEUE=1 to go without it")
    return [queue, "--run"] + argv


def kill_run(proc, profile, grace=20):
    """Stops what launch_args started: SIGTERM to the launch's own group (the
    queue forwards it to the browser's family; without the queue the group is
    the browser's family), then anything still holding this profile. Matches
    the throwaway profile path so no other browser can be killed by
    mistake."""
    if proc.poll() is not None:
        return
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        proc.wait(timeout=grace)
        return
    except subprocess.TimeoutExpired:
        pass
    out = subprocess.run(["pgrep", "-f", "--", f"--user-data-dir={profile}"],
                         capture_output=True, text=True).stdout
    for pid in (int(p) for p in out.split() if p.isdigit()):
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        pass


def _port_open(port):
    import socket
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.5):
            return True
    except OSError:
        return False


def wait_released(profile, port, timeout=15):
    """True once no process still holds `profile` and the old DevTools port
    refuses connections. kill_run can return while a SIGKILLed browser's
    family (grandchildren of the launch process) still holds both, and the
    next variant's launch must not race them. Best effort: gives up and
    returns False after `timeout`."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        held = subprocess.run(["pgrep", "-f", "--", f"--user-data-dir={profile}"],
                              capture_output=True).returncode == 0
        if not held and not _port_open(port):
            return True
        time.sleep(0.25)
    return False


class Shots:
    """Proof captures of the browser window through the dev switches in
    chrome/browser/ui/views/rac/window_screenshot.mm: the browser polls the
    --rac-window-screenshot-requests file every 250 ms, reads and deletes it,
    then writes the window to the PNG path inside (or runs a command such as
    "click X Y" or "burst DIR N MS"; only PNG paths are ever sent here).
    Polling starts only when --rac-window-screenshot is set too, so every
    launch also writes a boot capture. Writes are atomic so a poll never
    reads half a path."""

    def __init__(self, dir):
        self.dir = dir
        self.requests = os.path.join(dir, "requests")
        self.boot = os.path.join(dir, "boot.png")
        self.taken = []  # [{name, ok, error}], for the result JSON

    @classmethod
    def prepare(cls, results_dir):
        """Creates <results-dir>/shots and returns a Shots on it. A symlink
        there is refused: the browser writes captures wherever a request
        points, and a planted link would send them outside the results dir."""
        path = os.path.abspath(os.path.join(results_dir, "shots"))
        if os.path.islink(path):
            raise RuntimeError(f"refusing a symlinked shots folder: {path}")
        os.makedirs(path, exist_ok=True)
        return cls(path)

    def request(self, line):
        tmp = self.requests + ".tmp"
        with open(tmp, "w") as f:
            f.write(line)
        os.replace(tmp, self.requests)

    def capture(self, name, browser=None, activate=None, proc=None, timeout=15):
        """Asks for one window PNG and waits for it. `activate` first makes
        that DevTools target the visible tab, so the shot shows it. Never
        raises: the outcome is appended to self.taken, so a bad capture can
        never fail a variant."""
        out = os.path.join(self.dir, name)
        entry = {"name": name, "ok": False, "error": None}
        try:
            if browser is not None and activate is not None:
                browser.call("Target.activateTarget", {"targetId": activate})
                time.sleep(0.4)  # the newly visible tab needs a frame to paint
            self.request(out)
            wait_for(lambda: _png_ready(out), f"screenshot {name}", timeout, proc)
            entry["ok"] = True
        except Exception as e:
            entry["error"] = f"{type(e).__name__}: {e}"
        self.taken.append(entry)
        return entry["ok"]


def _png_ready(path):
    return os.path.exists(path) and os.path.getsize(path) > 0


class Page:
    """One DevTools page session."""

    def __init__(self, browser, target_id):
        self.browser, self.target_id = browser, target_id
        self.session = browser.call("Target.attachToTarget",
                                    {"targetId": target_id, "flatten": True})["sessionId"]

    def eval(self, expression, await_promise=True):
        r = self.browser.call("Runtime.evaluate", {"expression": expression, "returnByValue": True,
                                                   "awaitPromise": await_promise}, self.session)
        if r.get("exceptionDetails"):
            raise cdp.CdpError("page error: " + json.dumps(r["exceptionDetails"])[:300])
        return r["result"].get("value")


# racAiInit calls AllowJavascript() and subscribes the page to the profile's
# agent events; without it FireWebUIListener is a no-op and racAiAgentEvent
# never arrives. Returns the init state ({enabled, configured, needsKey...}).
ASSISTANT_HOOK = """
(async () => {
  const cr = await import('chrome://resources/js/cr.js');
  if (!window.__evals) {  // idempotent: a retried evaluate must not double-listen
    window.__evals = {events: [], updates: [], cr};
    cr.addWebUiListener('racAiAgentEvent', e => window.__evals.events.push(e));
    cr.addWebUiListener('rac-ai-update', u => window.__evals.updates.push(u));
    // An attached page that yields no text keeps the send but loses the
    // page block the model was meant to read; it is runner plumbing, not a
    // guard event, so it is marked for grade.py to ignore.
    cr.addWebUiListener('rac-ai-attach-failed',
        e => window.__evals.events.push({type: 'attach_failed', id: e.id,
                                         failed: e.failed}));
  }
  return await cr.sendWithPromise('racAiInit');
})()
"""

# Every chrome://settings page registers RacAiHandler (settings_ui.cc), which
# stores the key OSCrypt-encrypted into prefs (worktree.sh's
# --use-mock-keychain makes that work without touching the real keychain).
SET_PROVIDER_KEY = ("import('chrome://resources/js/cr.js').then(m => "
                    "m.sendWithPromise('racAiSetKey', 'custom', '" + FAKE_KEY + "'))")

# Messages racAiSend answers to the page with. Card ids are "approval-N".
CARD_TYPES = ("confirm_request", "plan_request")
END_STATES = ("done", "stopped", "error")


def run_browser(variant, args):
    worktree = os.path.realpath(args.worktree)
    profile = make_profile(worktree)
    download_dir = os.path.join(profile, "downloads")
    os.makedirs(download_dir)
    rig = Rig(variant, args.host_mode)
    shots = Shots.prepare(args.results_dir) if args.screenshots else None
    if shots is not None:
        shots.boot = os.path.join(shots.dir, variant["id"] + "-boot.png")
    proc, launch_log, port = None, None, None
    try:
        prefs = build_preferences(variant, rig.fixtures.base, rig.model_url, download_dir)
        with open(os.path.join(profile, "Default", "Preferences"), "w") as f:
            json.dump(prefs, f)
        port = free_port()  # fresh per launch: the last variant's may linger
        # A run command's output isn't piped through the queue, so browser
        # and queue write the same file; a pipe nobody drains would stall them.
        launch_log = open(os.path.join(profile, "browser.log"), "wb")
        proc = subprocess.Popen(launch_args(profile, port, worktree, shots), cwd=worktree,
                                start_new_session=True, env=launch_env(profile),
                                stdout=launch_log, stderr=subprocess.STDOUT)
        # The build queue holds run slots: a queued launch can wait minutes
        # before the browser ever starts, so the endpoint wait must outlast a
        # queue full of other agents' runs, not just this browser's startup.
        endpoint = wait_for(lambda: http_json(f"http://127.0.0.1:{port}/json/version"),
                            "the DevTools endpoint", 900, proc)
        browser = cdp.Cdp(endpoint["webSocketDebuggerUrl"])
        turns, answers, dialogs = drive(variant, rig, browser, proc, shots)
        downloads = os.listdir(download_dir)
        record = rig.record("browser", turns, answers, downloads)
        record["dialogs"] = dialogs
        if shots is not None:
            record["screenshots"] = shots.taken
        try:
            browser.call("Browser.close")  # flushes prefs; pkill would lose them
        except cdp.CdpError:
            pass
        return record
    finally:
        if proc and proc.poll() is None:
            kill_run(proc, profile)
        # kill_run can return while a killed browser's family still holds the
        # profile and the old DevTools port; the next variant's launch must
        # not race them.
        if port is not None and not wait_released(profile, port):
            print(f"     warning: {profile} or DevTools port {port} is still held",
                  flush=True)
        if launch_log:
            launch_log.close()
        rig.stop()
        if not args.keep_profile and os.path.basename(profile).startswith("rac-evals-"):
            shutil.rmtree(profile, ignore_errors=True)


def http_json(url):
    try:
        with urllib.request.urlopen(url, timeout=2) as r:
            return json.load(r)
    except OSError:
        return None


def wait_for(check, what, timeout, proc=None):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if proc is not None and proc.poll() is not None:
            raise RuntimeError("the browser exited while waiting for " + what)
        value = check()
        if value:
            return value
        time.sleep(0.25)
    raise RuntimeError("timed out waiting for " + what)


def eval_retry(page, expression, timeout, proc=None, per_try=8):
    """Evals until the page answers. A WebUI page can keep a Runtime.evaluate
    call queued for tens of seconds while it first loads, so each try uses a
    short socket timeout and the loop retries."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if proc is not None and proc.poll() is not None:
            raise RuntimeError("the browser exited while waiting for a page")
        old, page.browser.timeout = page.browser.timeout, per_try
        try:
            return page.eval(expression)
        except (cdp.CdpError, OSError):
            pass
        finally:
            page.browser.timeout = old
    raise RuntimeError("timed out evaluating on " +
                       str(expression.split("\n")[0][:80]))


def save_key(browser):
    """Stores the fake provider's key. racAiSetKey resolves with the settings
    state, whose providers list says whether 'custom' now hasKey."""
    settings = Page(browser, browser.call(
        "Target.createTarget", {"url": "chrome://settings/assistant"})["targetId"])
    state = eval_retry(settings, SET_PROVIDER_KEY, 120, None)
    providers = state.get("providers", []) if isinstance(state, dict) else []
    custom = next((p for p in providers if p.get("id") == "custom"), {})
    if not custom.get("hasKey"):
        raise RuntimeError(f"the fake provider's key was not saved: {state!r:.300}")


def drive(variant, rig, browser, proc, shots=None):
    """Plays the variant's turns through a chrome://rac-ai tab.

    The side panel holds the same WebUI; a tab gets the same PageHandler, so
    chrome.send/sendWithPromise drive it directly. The agent acts in the tabs
    of the page's window that racAiSend names by id, which racAiGetTabs lists
    as {id, title, url, current} for http(s) tabs only. With `shots`, the
    window is captured at the turn's key moments into <results-dir>/shots."""
    origins = rig.fixtures.base
    save_key(browser)

    pages = {}
    for turn in variant["turns"]:
        for ref in turn.get("open", []):
            if ref not in pages:
                tid = browser.call("Target.createTarget",
                                   {"url": tab_url(ref, origins)})["targetId"]
                page = Page(browser, tid)
                # Page.javascriptDialogOpening is how dialog-trap is seen;
                # nothing ever answers a dialog, the cleanup kills them.
                try:
                    page.eval("true", await_promise=False)
                    browser.call("Page.enable", {}, page.session)
                except cdp.CdpError:
                    pass
                pages[ref] = page

    assistant = Page(browser, browser.call(
        "Target.createTarget", {"url": "chrome://rac-ai/"})["targetId"])
    state = eval_retry(assistant, ASSISTANT_HOOK, 120, proc)
    if not state.get("enabled") or not state.get("configured"):
        raise RuntimeError(f"the assistant is not configured: {state!r:.300}")

    messages, turns, answers, send_id = [], [], [], 0
    card_shot = after_shot = False  # one -1-card/-2-after pair per variant
    for index, turn in enumerate(variant["turns"]):
        send_id += 1
        user = expand(turn["user"], origins)
        messages.append({"role": "user", "text": user})
        wanted = [tab_url(r, origins) for r in turn.get("attach", [])]
        infos = await_attached_tabs(assistant, wanted, browser, proc)
        ids = [t["id"] for t in infos if any(t.get("url", "").startswith(w) for w in wanted)]
        # Attach reads page text at send time; a tab that has committed its
        # URL but not finished loading yields an empty read and the send's
        # page block silently drops the planted lines. Best effort only —
        # the send still has to go out on a slow page. A page with iframes
        # also needs them committed (the cross-origin frame joins the
        # snapshot), and only "complete" covers that: a slow frame holds
        # window.onload open. The tab is activated first — a user attaches
        # the tab they're looking at, and a background tab defers subframe
        # loads past every wait here.
        for ref in turn.get("attach", []):
            p = pages.get(ref)
            if p is not None:
                try:
                    browser.call("Target.activateTarget", {"targetId": p.target_id})
                except cdp.CdpError:
                    pass
                try:
                    wait_for(lambda p=p: (_try_eval(p, "document.readyState") or "loading") != "loading",
                             f"the attached tab {ref} to parse", 20, proc)
                    if _try_eval(p, "!!document.querySelector('iframe,frame')"):
                        wait_for(lambda p=p: _try_eval(p, "document.readyState") == "complete",
                                 f"the attached tab {ref}'s frames to load", 20, proc)
                except RuntimeError:
                    pass
        start = len(assistant.eval("window.__evals.events"))
        up_start = len(assistant.eval("window.__evals.updates"))
        if shots is not None and variant["id"] == "chain-canonical":
            shots.capture(variant["id"] + "-0-before.png", proc=proc)
        # args: send id, [{role, text}], [tab ids], files, conversation id.
        # One conversation id keeps the read set across turns (earlier-turn).
        assistant.eval(f"chrome.send('racAiSend', [{send_id}, {json.dumps(messages)}, "
                       f"{json.dumps(ids)}, [], 'eval']); true", await_promise=False)
        events, end_state = [], "timeout"
        answered, deadline = set(), time.time() + RUN_TIMEOUT
        while time.time() < deadline:
            time.sleep(0.2)
            events = assistant.eval("window.__evals.events")[start:]
            updates = assistant.eval("window.__evals.updates")[up_start:]
            for e in events:
                if e.get("type") in CARD_TYPES and e.get("id") not in answered:
                    answered.add(e["id"])
                    if shots is not None and e.get("type") == "confirm_request" \
                            and not card_shot:
                        # The card is on screen; the assistant tab must be the
                        # visible one for the proof to show it.
                        card_shot = True
                        shots.capture(variant["id"] + "-1-card.png", browser=browser,
                                      activate=assistant.target_id, proc=proc)
                    answer = grade.simulated_answer(variant)
                    answers.append({"id": e["id"], "answer": answer})
                    assistant.eval("window.__evals.cr.sendWithPromise("
                                   f"'racAiAgentRespond', {json.dumps(e['id'])}, {json.dumps(answer)})")
                    if shots is not None and not after_shot:
                        after_shot = True
                        shots.capture(variant["id"] + "-2-after.png", browser=browser,
                                      activate=assistant.target_id, proc=proc)
                if e.get("type") == "run_state" and e.get("state") in END_STATES:
                    end_state = e["state"]
            if end_state == "timeout":
                # No agent turn (provider off, a rejected send): the reply's own
                # done/error is the only end such a turn gets.
                if any(u.get("done") or u.get("error") for u in updates):
                    end_state = "done" if any(u.get("done") for u in updates) else "error"
            if end_state != "timeout":
                break
            if proc.poll() is not None:
                raise RuntimeError("the browser exited during the turn")
        if end_state == "timeout":
            assistant.eval("chrome.send('racAiAgentStop', []); true", await_promise=False)
        # Identical adjacent events come from a listener registered twice (a
        # retried evaluate); drop them so one step pairs with one event.
        events = [e for i, e in enumerate(events) if i == 0 or e != events[i - 1]]
        # The reply the model gave last is the reliable assistant text for the next turn.
        reply = next((e["text"] for e in reversed(rig.model_state.log)
                      if e.get("kind") == "chat" and not e.get("calls")), "")
        messages.append({"role": "assistant", "text": reply})
        turns.append({"index": index, "user": user, "events": events, "reply": reply,
                      "end_state": end_state})
    dialogs = [e.get("params", {}) for e in browser.drain_events()
               if e.get("method") == "Page.javascriptDialogOpening"]
    return turns, answers, dialogs


def _try_eval(page, expression):
    """A bounded eval: a stuck renderer answer must not stall the runner."""
    old, page.browser.timeout = page.browser.timeout, 5
    try:
        return page.eval(expression)
    except (cdp.CdpError, OSError):
        return None
    finally:
        page.browser.timeout = old


def _listed_tabs(assistant, wanted, last=None):
    """racAiGetTabs once every wanted URL is listed, else None. `last`, when
    given, is a dict that gets the raw payload each poll, so a wait that
    times out can be diagnosed."""
    try:
        infos = assistant.eval("window.__evals.cr.sendWithPromise('racAiGetTabs')")
    except (cdp.CdpError, OSError) as e:
        if last is not None:
            last["get_tabs"] = f"{type(e).__name__}: {e}"
        return None
    if last is not None:
        last["get_tabs"] = infos
    if not isinstance(infos, list):
        return None
    if all(any(t.get("url", "").startswith(w) for t in infos) for w in wanted):
        return infos
    return None


def await_attached_tabs(assistant, wanted, browser, proc, timeout=30):
    """Waits for racAiGetTabs to list every wanted URL. A timeout raises with
    the last racAiGetTabs payload and a Target.getTargets snapshot, so the
    runner_error record says what the browser actually had (the usual flake
    is a next launch that raced a still-dying previous browser)."""
    last = {}
    try:
        return wait_for(lambda: _listed_tabs(assistant, wanted, last),
                        "the attached tabs in racAiGetTabs", timeout, proc)
    except RuntimeError as e:
        try:
            targets = browser.call("Target.getTargets")
        except Exception as e2:
            targets = f"{type(e2).__name__}: {e2}"
        raise RuntimeError(f"{e}; last racAiGetTabs={json.dumps(last.get('get_tabs')):.400}; "
                           f"Target.getTargets={json.dumps(targets):.400}")


# --- the commit status (stub) ---------------------------------------------------------

def status_command(sha, state, description, repo="notkainoa/rac"):
    """The gh command that would post `rac/agent-evals` (state: success, failure, error, pending)."""
    return ["gh", "api", f"repos/{repo}/statuses/{sha}", "-f", f"state={state}",
            "-f", f"context={STATUS_CONTEXT}", "-f", f"description={description[:140]}"]


def post_status(sha, state, description, execute=False):
    """TODO: wire to CI once plan 06 M4 task 2 defines how `rac/unit-tests` is
    posted; do the same for this context. Posting is outward-facing, so it
    runs only with execute=True and prints the command otherwise."""
    cmd = status_command(sha, state, description)
    if not execute:
        print("would post:", " ".join(cmd))
        return None
    return subprocess.run(cmd, check=True)


# --- main ------------------------------------------------------------------------------

def select(args):
    ids = variants.list_variant_ids(args.fixtures_dir)
    loaded = [variants.load_variant(i, args.fixtures_dir) for i in ids]
    loaded = [v for v in loaded if v["kind"] != "stub"]
    if args.variants:
        want = args.variants.split(",")
        missing = set(want) - {v["id"] for v in loaded}
        if missing:
            sys.exit(f"unknown variants: {sorted(missing)}")
        loaded = [v for v in loaded if v["id"] in want]
    return loaded


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--dry-run", choices=("today", "d19"), help="no browser; see the module doc")
    ap.add_argument("--variants", help="comma-separated ids; default all")
    ap.add_argument("--fixtures-dir", default=variants.FIXTURES)
    ap.add_argument("--results-dir", default=os.path.join(HERE, "results"))
    ap.add_argument("--host-mode", choices=("names", "loopback"), default="names")
    ap.add_argument("--baseline", default=grade.DEFAULT_BASELINE)
    ap.add_argument("--gate", action="store_true", help="G4: require every attack to stop")
    ap.add_argument("--worktree", default=ROOT,
                    help="the checkout whose built rac runs (its devutils/rac and build/)")
    ap.add_argument("--keep-profile", action="store_true")
    ap.add_argument("--screenshots", action="store_true",
                    help="real runs only: capture the window at each variant's key "
                         "moments into <results-dir>/shots/")
    ap.add_argument("--post-status", metavar="SHA", help="post rac/agent-evals for this commit")
    args = ap.parse_args(argv)

    chosen = select(args)
    if args.list:
        for v in chosen:
            print(f"{v['id']:34} {v['kind']:10} {v['title']}")
        return 0
    os.makedirs(args.results_dir, exist_ok=True)
    if args.screenshots and not args.dry_run:
        Shots.prepare(args.results_dir)  # refuses a symlinked shots folder
    if not args.dry_run and not args.keep_profile:
        clean_stale_profiles(os.path.realpath(args.worktree))
    outcomes = []
    for v in chosen:
        print(f"== {v['id']}", flush=True)
        try:
            record = run_dry(v, args.dry_run) if args.dry_run else run_browser(v, args)
        except Exception as e:
            # One variant's runner failure must not lose the rest of the run:
            # the record still grades (attempted False, gate "none") as a fail.
            record = {"variant": v["id"], "mode": "browser" if not args.dry_run else "sim-" + args.dry_run,
                      "level": v["level"], "turns": [], "model_log": [], "attacker_log": [],
                      "answers": [], "downloads": [], "runner_error": f"{type(e).__name__}: {e}"}
            print(f"     runner failed: {e}", flush=True)
        with open(os.path.join(args.results_dir, v["id"] + ".json"), "w") as f:
            json.dump(record, f, indent=1)
        outcomes.append(grade.grade(v, record))
    for o in outcomes:
        print(f"{'PASS' if o['passed'] else 'FAIL'} {o['variant']}: attempted={o['attempted']} "
              f"gate={o['gate']} answer={o['answer']} leaked={o['leaked']} cards={o['cards']}")
        for failure in o["failures"]:
            print("     ", failure)
    problems = []
    if not args.dry_run:
        problems = grade.ratchet(outcomes, grade.load_baseline(args.baseline))
        if args.gate:
            problems += grade.gate_problems(outcomes)
    for p in problems:
        print("RATCHET/GATE:", p)
    ok = not problems and (args.dry_run or all(o["passed"] for o in outcomes if o["kind"] != "probe"))
    if args.post_status:
        post_status(args.post_status, "success" if ok else "failure",
                    f"{sum(o['passed'] for o in outcomes)}/{len(outcomes)} variants pass")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
