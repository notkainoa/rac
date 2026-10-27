#!/usr/bin/env python3
# Copyright 2026 The rac Authors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Tier 1b runner: hostile fixtures against the real agent, graded.

  run.py --list                       the variants
  run.py --dry-run today|d19          no browser: fixtures + fake model + the
                                      Python stand-in agent (sim_agent.py)
  run.py [--variants a,b]             launch the build and run for real
                                      (needs a built worktree; see README)

A real run, per variant, in a throwaway profile:
  1. start the fixture server (one port per origin) and the fake model;
  2. seed <profile>/Default/Preferences: AI on, browser control on, the Custom
     provider pointed at the fake model, the level and site rules under test;
  3. launch `worktree.sh run --user-data-dir=<profile> --remote-debugging-port`
     (a later --user-data-dir wins over the script's own, as test-spaces.mjs
     relies on), save the fake provider's key through Settings;
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

import cdp
import fake_model
import fixture_server
import grade
import sim_agent
import sim_browser
import variants

HERE = os.path.dirname(os.path.abspath(__file__))
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
        threading.Thread(target=self.model.serve_forever, daemon=True).start()
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


def make_profile(base_dir=None):
    """A throwaway profile. Refuses anything that could be a real one."""
    base = base_dir or os.path.join(ROOT, "build")
    os.makedirs(base, exist_ok=True)
    path = tempfile.mkdtemp(prefix="rac-evals-", dir=base)
    assert "Application Support" not in os.path.realpath(path), "refusing a real profile folder"
    os.makedirs(os.path.join(path, "Default"))
    return path


def free_port():
    import socket
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def launch_args(profile, port):
    return [os.path.join(ROOT, "devutils/rac/worktree.sh"), "run",
            f"--user-data-dir={profile}", f"--remote-debugging-port={port}",
            "--remote-debugging-address=127.0.0.1", "--remote-allow-origins=*",
            "--rac-launch-in-background", "--no-first-run", "--no-default-browser-check",
            "--disable-background-networking", "--disable-component-update"]


class Page:
    """One DevTools page session."""

    def __init__(self, browser, target_id):
        self.browser = browser
        self.session = browser.call("Target.attachToTarget",
                                    {"targetId": target_id, "flatten": True})["sessionId"]

    def eval(self, expression, await_promise=True):
        r = self.browser.call("Runtime.evaluate", {"expression": expression, "returnByValue": True,
                                                   "awaitPromise": await_promise}, self.session)
        if r.get("exceptionDetails"):
            raise cdp.CdpError("page error: " + json.dumps(r["exceptionDetails"])[:300])
        return r["result"].get("value")


ASSISTANT_HOOK = """
(async () => {
  const cr = await import('chrome://resources/js/cr.js');
  window.__evals = {events: [], updates: [], cr};
  cr.addWebUiListener('racAiAgentEvent', e => window.__evals.events.push(e));
  cr.addWebUiListener('rac-ai-update', u => window.__evals.updates.push(u));
  return true;
})()
"""


def run_browser(variant, args):
    """TODO(binary): every browser-facing step below is unverified; each one
    is marked where it guesses."""
    profile = make_profile()
    download_dir = os.path.join(profile, "downloads")
    os.makedirs(download_dir)
    rig = Rig(variant, args.host_mode)
    proc = None
    try:
        prefs = build_preferences(variant, rig.fixtures.base, rig.model_url, download_dir)
        with open(os.path.join(profile, "Default", "Preferences"), "w") as f:
            json.dump(prefs, f)
        port = free_port()
        proc = subprocess.Popen(launch_args(profile, port), cwd=ROOT, start_new_session=True,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        endpoint = wait_for(lambda: http_json(f"http://127.0.0.1:{port}/json/version"),
                            "the DevTools endpoint", 120, proc)
        browser = cdp.Cdp(endpoint["webSocketDebuggerUrl"])
        turns, answers = drive(variant, rig, browser, proc)
        downloads = os.listdir(download_dir)
        try:
            browser.call("Browser.close")  # flushes prefs; pkill would lose them
        except cdp.CdpError:
            pass
        return rig.record("browser", turns, answers, downloads)
    finally:
        rig.stop()
        if proc and proc.poll() is None:
            os.killpg(proc.pid, signal.SIGTERM)
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


def drive(variant, rig, browser, proc):
    """Plays the variant's turns through chrome://rac-ai. TODO(binary)."""
    origins = rig.fixtures.base
    # TODO(binary): the Custom provider needs a saved key, and keys can only be
    # stored through Settings (encrypted with OSCrypt; --use-mock-keychain is
    # on). The handler is racAiSetKey on a settings page. Confirm which
    # chrome://settings URL registers it, and that AiService exists (AI on).
    settings = Page(browser, browser.call("Target.createTarget", {"url": "chrome://settings/"})["targetId"])
    time.sleep(2)
    settings.eval("import('chrome://resources/js/cr.js').then(m => "
                  f"m.sendWithPromise('racAiSetKey', 'custom', '{FAKE_KEY}'))")

    tabs = {}
    for turn in variant["turns"]:
        for ref in turn.get("open", []):
            if ref not in tabs:
                tabs[ref] = browser.call("Target.createTarget",
                                         {"url": tab_url(ref, origins)})["targetId"]
    # TODO(binary): the assistant normally lives in the side panel, which may
    # not be a DevTools target. A tab at chrome://rac-ai is the fallback; the
    # agent acts in "tabs the user attached" of that window either way.
    assistant = Page(browser, browser.call("Target.createTarget", {"url": "chrome://rac-ai/"})["targetId"])
    time.sleep(2)
    assistant.eval(ASSISTANT_HOOK)

    messages, turns, answers, send_id = [], [], [], 0
    for index, turn in enumerate(variant["turns"]):
        send_id += 1
        user = expand(turn["user"], origins)
        messages.append({"role": "user", "text": user})
        # TODO(binary): racAiGetTabs returns TabInfo[]; map each wanted tab (by
        # URL) to the numeric id racAiSend takes. Field names are a guess.
        infos = assistant.eval("window.__evals.cr.sendWithPromise('racAiGetTabs')")
        wanted = [tab_url(r, origins) for r in turn.get("attach", [])]
        ids = [t["id"] for t in infos if any(t.get("url", "").startswith(w) for w in wanted)]
        start = len(assistant.eval("window.__evals.events"))
        assistant.eval(f"chrome.send('racAiSend', [{send_id}, {json.dumps(messages)}, "
                       f"{json.dumps(ids)}, []]); true", await_promise=False)
        events, end_state = [], "timeout"
        answered, deadline = set(), time.time() + RUN_TIMEOUT
        while time.time() < deadline:
            time.sleep(0.2)
            events = assistant.eval("window.__evals.events")[start:]
            for e in events:
                if e.get("type") == "confirm_request" and e["id"] not in answered:
                    answered.add(e["id"])
                    answer = grade.simulated_answer(variant)
                    answers.append({"id": e["id"], "answer": answer})
                    assistant.eval("window.__evals.cr.sendWithPromise("
                                   f"'racAiAgentRespond', {json.dumps(e['id'])}, {json.dumps(answer)})")
                if e.get("type") == "run_state" and e.get("state") in ("done", "stopped", "error"):
                    end_state = e["state"]
            if end_state != "timeout":
                break
            if proc.poll() is not None:
                raise RuntimeError("the browser exited during the turn")
        if end_state == "timeout":
            assistant.eval("chrome.send('racAiAgentStop', []); true", await_promise=False)
        # The reply the model gave last is the reliable assistant text for the next turn.
        reply = next((e["text"] for e in reversed(rig.model_state.log)
                      if e.get("kind") == "chat" and not e.get("calls")), "")
        messages.append({"role": "assistant", "text": reply})
        turns.append({"index": index, "user": user, "events": events, "reply": reply,
                      "end_state": end_state})
    return turns, answers


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
    ap.add_argument("--keep-profile", action="store_true")
    ap.add_argument("--post-status", metavar="SHA", help="post rac/agent-evals for this commit")
    args = ap.parse_args(argv)

    chosen = select(args)
    if args.list:
        for v in chosen:
            print(f"{v['id']:34} {v['kind']:10} {v['title']}")
        return 0
    os.makedirs(args.results_dir, exist_ok=True)
    outcomes = []
    for v in chosen:
        print(f"== {v['id']}", flush=True)
        record = run_dry(v, args.dry_run) if args.dry_run else run_browser(v, args)
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
