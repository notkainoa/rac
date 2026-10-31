#!/usr/bin/env python3
# Copyright 2026 The rac Authors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Tier 1b runner: hostile fixtures against the real agent, graded.

  run.py --list                       the variants
  run.py --dry-run today|d19          no browser: fixtures + fake model + the
                                      Python stand-in agent (sim_agent.py)
  run.py [--variants a[:light|dark][:narrow|wide],b]
                                      launch the build and run for real
                                      (needs a built worktree; see README)
  run.py --screenshots ...            also write proof PNGs of the window to
                                      <results-dir>/shots/ (real runs only)

A real run, per variant, in a throwaway profile:
  1. start the fixture server (one port per origin) and the fake model;
  2. seed <profile>/Default/Preferences: AI on, browser control on, the Custom
     provider pointed at the fake model, the level and site rules under test,
     plus the space theme mode and side-panel width a suffixed spec asks for;
  3. launch the built binary `build/src/out/Default/rac.app/Contents/MacOS/rac`
     with `--user-data-dir=<profile> --remote-debugging-port=0` (through the
     build queue's run slot unless RAC_EVALS_NO_QUEUE=1), save the fake
     provider's key through Settings;
  4. open the fixture tabs and drive the assistant: with --screenshots
     through the side panel's own UI (the + menu attaches, the composer
     sends, a card's buttons answer — only the sending page owns the run
     and renders its cards), otherwise racAiSend/racAiAgentRespond on a
     chrome://rac-ai tab. Every card is answered as grade.simulated_answer
     says; then wait for the run to end;
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
# chrome/app/chrome_command_ids.h: toggles the assistant side panel, sent
# through the screenshot requests file as "command 40701".
IDC_RAC_ASSISTANT_TOGGLE = 40701

# --- prefs the :light/:dark and :narrow/:wide spec suffixes seed -----------
#
# Appearance is rac's per-space theme mode, seeded as one space in
# rac.spaces. SpacesWindowManager::UpdateColorMode turns theme.mode into the
# window widget's SetColorModeOverride
# (chrome/browser/ui/rac/spaces/spaces_window_manager.cc), which wins over
# ThemeService in BrowserWidget::GetColorProviderKey
# (chrome/browser/ui/views/frame/browser_widget.cc) and so decides every
# WebContents' color mode in the window — page tabs through
# ColorProviderBrowserHelper, the assistant side panel through
# WebView::AddedToWidget — which is what blink's prefers-color-scheme reads
# (chrome_content_browser_client.cc GetPreferredColorScheme). Chromium's own
# browser.theme.color_scheme2 can't be used instead: rac forces it back to
# system on startup and on every theme change
# (SpacesWindowManager::ResetBrowserTheme).
SPACES_PREF = "rac.spaces"
# A fixed id: the seeded space only lives in the throwaway profile.
EVALS_SPACE_ID = "0e5af240-0000-4000-8000-000000000000"
# SpaceTheme::FromDict needs both stops to parse at all; Neutral's
# (chrome/browser/rac/spaces/space.cc kPresets[0]) paint the default flat
# gray, so :light and :dark differ only in mode.
EVALS_SPACE_COLORS = {"color1": "#FFFFD7", "color2": "#FFD9FB"}

# side_panel.id_to_width maps SidePanelEntryIdToString of a SidePanelEntryId
# — "kRacAi" for the assistant (chrome/browser/ui/side_panel/
# side_panel_entry_id.h) — to the panel's whole width, borders included
# (SidePanel::UpdateSidePanelWidthPref/UpdateWidthOnEntryChanged,
# chrome/browser/ui/views/side_panel/side_panel.cc).
PANEL_WIDTH_PREF = "side_panel.id_to_width"
ASSISTANT_PANEL_ID = "kRacAi"
# SidePanel::GetMinimumSize().width(): kSidePanelMinimumContentWidth (200)
# plus the borders — content margin 3 + separator 1 on one side, resize
# area 6 + separator 1 on the other. A smaller seeded width still lays out
# at this.
PANEL_NARROW_WIDTH = 211
# SidePanelType::kContent panels get at most 2/3 of the window's client
# width (kMaxContentsHeightSidePanelFraction in
# browser_view_tabbed_layout_impl.cc), so this is wide while still fitting
# an ~840 px window.
PANEL_WIDE_WIDTH = 560
PANEL_WIDTHS = {"narrow": PANEL_NARROW_WIDTH, "wide": PANEL_WIDE_WIDTH}


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
    """The variant's own prefs. Only the allow-listed keys (variants.PREF_KEYS:
    the agent level and site rules under test) may come from the fixture —
    anything else would let a variant rewrite the safety prefs the run depends
    on, so an unknown key is refused outright."""
    prefs = {"rac.ai.agent_permission_level": variant["level"]}
    for key, value in variant.get("prefs", {}).items():
        if key not in variants.PREF_KEYS:
            raise variants.VariantError(
                f"{variant['id']}: pref {key!r} is not allowed; a variant may only "
                f"set {', '.join(variants.PREF_KEYS)}")
        prefs[key] = value
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
        return {"variant": self.variant["id"], "base_id": self.variant["base_id"],
                "mode": mode, "level": self.variant["level"],
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
    """The seeded Default/Preferences, as nested JSON. The variant's own
    (allow-listed) prefs go first; the safety prefs go last so nothing — a
    variant pref, a spec suffix — can override them."""
    prefs = {}
    for dotted, value in flat_prefs(variant, origins).items():
        deep_set(prefs, dotted, value)
    # The run's :light/:dark and :narrow/:wide suffixes; see the constants
    # above for why these prefs and not Chromium's color-scheme pref.
    if variant.get("appearance"):
        deep_set(prefs, SPACES_PREF, {"version": 1, "spaces": [
            {"id": EVALS_SPACE_ID, "name": "",
             "theme": {**EVALS_SPACE_COLORS, "mode": variant["appearance"]}}]})
    if variant.get("panel_width"):
        deep_set(prefs, PANEL_WIDTH_PREF,
                 {ASSISTANT_PANEL_ID: PANEL_WIDTHS[variant["panel_width"]]})
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
        # pref_names.h kHeliumServicesEnabled: a throwaway profile never
        # reaches Helium's services (filter lists through their proxy).
        "helium.services.enabled": False,
    }.items():
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
    """The launch environment: an explicit minimal set, because the browser
    loads hostile fixture pages and must not inherit this shell's secrets —
    under ssh that means SSH_AUTH_SOCK and whatever else is exported. Crash
    dumps go into the throwaway profile, so a dev run never writes the real
    me.kainoa.rac/Crashpad (PR #25 does the same in worktree.sh; this holds
    even without it)."""
    env = {key: os.environ[key] for key in ("HOME", "PATH", "TMPDIR", "LANG")
           if key in os.environ}
    env["BREAKPAD_DUMP_LOCATION"] = os.path.join(profile, "Crashpad")
    return env


def browser_binary(worktree):
    """The dev build's binary inside the app bundle."""
    return os.path.join(worktree, "build", "src", "out", "Default",
                        "rac.app", "Contents", "MacOS", "rac")


def launch_args(profile, worktree, shots=None):
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
            # Port 0: Chromium picks the port and writes it to
            # <profile>/DevToolsActivePort, so two launches can never be
            # handed the same "free" port. Headed Chromium's DevTools
            # server only ever binds loopback (remote_debugging_server.cc
            # CreateLocalHostServerSocket), so no
            # --remote-debugging-address.
            "--remote-debugging-port=0",
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


def devtools_port(profile):
    """The port the launch's --remote-debugging-port=0 picked, read from
    the first line of <profile>/DevToolsActivePort (what ChromeDriver and
    Telemetry read). None until the browser writes it."""
    try:
        with open(os.path.join(profile, "DevToolsActivePort")) as f:
            return int(f.readline().strip())
    except (OSError, ValueError):
        return None


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
    "click X Y", "command ID", or "burst DIR N MS"; capture_card sends one
    command, IDC_RAC_ASSISTANT_TOGGLE, to open the side panel). Polling
    starts only when --rac-window-screenshot is set too, so every launch
    also writes a boot capture. Writes are atomic so a poll never reads
    half a path."""

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

    def capture_card(self, name, browser, panel, page, card_id=None,
                     proc=None, timeout=10):
        """The -1-card shot. The panel is already open (drive opens it
        before the first turn) and the run's events render the card in it,
        so the window only needs arranging: the tab the agent acts on
        becomes the visible one, then the PNG waits for this card's element
        in the panel's own page. A panel that never shows one is captured
        anyway, marked "card not in side panel"."""
        present = card_present_js(card_id) if card_id else CARD_PRESENT
        error = None
        try:
            if page is not None:
                browser.call("Target.activateTarget", {"targetId": page.target_id})
            wait_for(lambda: _try_eval(panel, present),
                     "the card in the side panel", timeout, proc)
        except RuntimeError:
            error = "card not in side panel"
        except (cdp.CdpError, OSError) as e:
            error = f"{type(e).__name__}: {e}"
        self.capture(name, browser=browser,
                     activate=page.target_id if page is not None else None,
                     proc=proc)
        entry = self.taken[-1]
        if error is not None:
            entry["ok"] = False
            entry["error"] = "; ".join(e for e in (entry["error"], error) if e)
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


def rac_ai_targets(target_infos):
    """The assistant's entries in a Target.getTargets list: the chat tab,
    and the side panel's page while it's open."""
    return [t for t in target_infos
            if t.get("url", "").startswith(("chrome://rac-ai", "rac://rac-ai"))]


def panel_target(target_infos, assistant_tid):
    """The side panel's target, or None while the panel is closed. It's a
    second rac-ai page next to the assistant tab: mode=panel in the URL
    marks it, but any rac-ai target that isn't the tab itself counts. The
    tab's own id is passed so it never counts — or None when the run never
    opened a chat tab (screenshot runs work in the panel alone)."""
    ai = rac_ai_targets(target_infos)
    for t in ai:
        if "mode=panel" in t.get("url", ""):
            return t
    return next((t for t in ai if t.get("targetId") != assistant_tid), None)


def _panel_info(browser, assistant_tid):
    """panel_target on a live Target.getTargets call; None while closed."""
    infos = browser.call("Target.getTargets").get("targetInfos", [])
    return panel_target(infos, assistant_tid)


def agent_page(pages, turn):
    """The page tab the agent is acting on this turn — what the -1-card
    shot puts beside the panel: the first attached tab, else the most
    recently opened one."""
    for ref in turn.get("attach", []):
        if ref in pages:
            return pages[ref]
    return list(pages.values())[-1] if pages else None


# --- the side panel's real UI (screenshot runs) -----------------------------
#
# With --screenshots, turns go through chrome://rac-ai/?mode=panel the way a
# user's do instead of calling the message handler from the chat tab: the
# composer's textarea takes the text, the send button submits it, the +
# menu attaches tabs, and a card's own buttons answer it. Only the panel
# that sent a turn hears its agent events (PageHandler::OnAgentTaskEvent
# fires racAiAgentEvent on the run's owner alone), which is also why the
# chat-tab send left the panel empty: its PageHandler never owned the run.
#
# The page's own listeners and click handlers do the work — selectors and
# flows come from chrome/browser/resources/rac_ai/index.html and app.ts /
# agent_cards.ts next to it:
#   #input   the composer's <textarea>; its 'input' listener runs
#            resizeInput/onTextChanged/updateControls, which arms #send
#   #send    the send button; its click runs submit() -> send()
#   #addTab  the attach button; its click runs toggleMenu -> openPicker,
#            which lists racAiGetTabs and opens a native menu through
#            racAiShowMenu. A pick fires "rac-ai-menu" {token, id:"tab:<id>"}
#            into the page's onMenuEvent -> attachTabs
#   #chips   the attached tabs' chips; a chip's title is the tab's URL
#   .agent-card   a card in the thread: [data-confirm-id] or [data-plan-id]
#            is the confirm_request/plan_request event's id. The actions
#            row's buttons are .pill-action: Allow once/Allow is .primary,
#            "Don't allow" is the plain one, grant/always and the plan
#            card's Stop are .quiet. Confirm buttons arm ~300 ms after the
#            card appears (CONFIRM_ARM_MS).
#   #stop    the composer's stop button; its click runs stop(), which ends
#            the chat session and the agent turn both


def send_path(shots):
    """How a turn is driven: "ui" through the side panel's composer and
    cards when --screenshots is on, "wire" — the chat tab's handler called
    directly — otherwise. The gate run without --screenshots is unchanged."""
    return "ui" if shots is not None else "wire"


def open_panel(browser, shots, proc, timeout=30):
    """The side panel's Page. The toggle is a command request, and the
    command also closes the panel, so it's sent only while Target.getTargets
    shows no panel; the target that appears is then hooked like the chat
    tab."""
    info = _panel_info(browser, None)
    if info is None:
        shots.request(f"command {IDC_RAC_ASSISTANT_TOGGLE}")
        info = wait_for(lambda: _panel_info(browser, None),
                        "the assistant side panel", timeout, proc)
    return Page(browser, info["targetId"])


def panel_type_js(text):
    """Puts `text` into the composer the way the textarea's own 'input'
    listener expects (app.ts): set the value, then dispatch input."""
    return ("(() => { const i = document.getElementById('input');"
            " if (!i) return 'no-input';"
            " i.value = " + json.dumps(text) + ";"
            " i.dispatchEvent(new Event('input', {bubbles: true}));"
            " return 'typed'; })()")


# #send's click is submit(); it's only enabled once updateControls sees text.
PANEL_SUBMIT_JS = (
    "(() => { const s = document.getElementById('send');"
    " if (!s || s.disabled) return 'send-disabled';"
    " s.click(); return 'sent'; })()")

# #stop's click is stop(): racAiAgentStop + racAiStop + streaming=false, so a
# timed-out turn doesn't leave the composer stuck.
PANEL_STOP_JS = (
    "(() => { const s = document.getElementById('stop');"
    " if (!s) return 'no-stop'; s.click(); return 'stopped'; })()")

# The titles of the composer's chips — one per attached tab (the current
# tab's card plus the picked extras); a tab chip's title is the tab's URL.
CHIP_URLS = ("[...document.querySelectorAll('#chips .attachment')]"
             ".map(e => e.title)")


def panel_attach_js(tab_id):
    """Attaches one tab the way the + menu does: #addTab's click runs
    openPicker, which shows a native menu through chrome.send
    ('racAiShowMenu', token). The menu is native, so the pick is replayed
    through cr.webUIListenerCallback — the exact call the menu's answer
    takes (a pick lands in onMenuEvent -> attachTabs, which then closes
    the real menu with racAiCloseMenu). If the token can't be captured
    (chrome.send unwrappable), recent tokens are tried; a wrong token is
    ignored by onMenuEvent, as is a 'tab:<id>' no menu ever offered."""
    return ("(async () => {\n"
            "  const e = window.__evals;\n"
            "  if (!e || !e.cr || typeof chrome === 'undefined' || !chrome.send)"
            " return 'no-hook';\n"
            "  if (!e.menu) {\n"
            "    e.menu = {token: 0};\n"
            "    const send = chrome.send;\n"
            "    try {\n"
            "      chrome.send = function (name, args) {\n"
            "        if (name === 'racAiShowMenu' && args && args.length)\n"
            " e.menu.token = args[0];\n"
            "        return send.apply(chrome, arguments);\n"
            "      };\n"
            "    } catch (err) {}\n"
            "  }\n"
            "  const add = document.getElementById('addTab');\n"
            "  if (!add || add.disabled) return 'no-addTab';\n"
            "  e.menu.token = 0;\n"
            "  add.click();\n"
            "  const deadline = Date.now() + 4000;\n"
            "  while (!e.menu.token && Date.now() < deadline)\n"
            "    await new Promise(r => setTimeout(r, 50));\n"
            "  const tab = 'tab:" + str(int(tab_id)) + "';\n"
            "  if (!e.menu.token) {\n"
            "    for (let t = 1; t <= 40; t++)\n"
            "      e.cr.webUIListenerCallback('rac-ai-menu', {token: t, id: tab});\n"
            "    return 'picked-guessed';\n"
            "  }\n"
            "  e.cr.webUIListenerCallback('rac-ai-menu',\n"
            "      {token: e.menu.token, id: tab});\n"
            "  return 'picked';\n"
            "})()")


def _card_selector(card_id):
    """The card element for one confirm_request/plan_request event id:
    buildConfirmCard/buildPlanCard keep it on data-confirm-id/data-plan-id."""
    q = json.dumps(card_id)
    return (".agent-card[data-confirm-id=" + q + "]," +
            ".agent-card[data-plan-id=" + q + "]")


def card_present_js(card_id):
    return "!!document.querySelector(" + json.dumps(_card_selector(card_id)) + ")"


def card_resolved_js(card_id):
    """True once the card's answer is applied: a confirm card leaves the
    DOM; the plan card stays as a collapsed row with data-status set."""
    return ("(() => { const c = document.querySelector(" +
            json.dumps(_card_selector(card_id)) + ");"
            " return !c || (c.dataset.status && c.dataset.status !== 'pending');"
            " })()")


def card_click_js(card_id, answer):
    """Clicks the card's own button for the simulated answer after the
    buttons arm: 'allow_once' the .primary Allow once/Allow; 'deny' the
    plain "Don't allow" — never the .quiet grant/always — or, on a plan
    card, its quiet Stop."""
    return ("(async () => {\n"
            "  const card = document.querySelector(" +
            json.dumps(_card_selector(card_id)) + ");\n"
            "  if (!card) return 'no-card';\n"
            "  const actions = card.querySelector('.agent-actions');\n"
            "  const buttons = actions ?"
            " [...actions.querySelectorAll('button.pill-action')] : [];\n"
            "  const pick = " + json.dumps(answer) + " === 'allow_once'\n"
            "      ? buttons.find(b => b.classList.contains('primary'))\n"
            "      : buttons.find(b => !b.classList.contains('primary') &&"
            " !b.classList.contains('quiet')) ||\n"
            "        (card.classList.contains('plan-card') ?"
            " buttons.find(b => b.classList.contains('quiet')) : null);\n"
            "  if (!pick) return 'no-button';\n"
            "  const deadline = Date.now() + 4000;\n"
            "  while (actions.inert && Date.now() < deadline)\n"
            "    await new Promise(r => setTimeout(r, 25));\n"
            "  pick.click();\n"
            "  return 'clicked';\n"
            "})()")


def _chip_covers(panel, url):
    """True once a composer chip carries this URL — the current tab's card
    (followCurrent) or one picked in the + menu."""
    have = _try_eval(panel, CHIP_URLS)
    return isinstance(have, list) and any(str(u).startswith(url) for u in have)


def panel_prune_js(wanted):
    """Clicks the .card-remove of one chip whose URL isn't wanted — the
    remove control removeTab is bound to (app.ts). One chip per call, so
    the loop in attach_panel_turn sees the re-render each time."""
    return ("(() => { const keep = " + json.dumps(list(wanted)) + ";"
            " for (const c of document.querySelectorAll('#chips .attachment')) {"
            "   const t = c.title || '';"
            "   if (t && !keep.some(u => t.startsWith(u))) {"
            "     const r = c.querySelector('.card-remove');"
            "     if (r) { r.click(); return 'removed'; }"
            "   }"
            " } return 'clean'; })()")


def attach_panel_turn(panel, wanted_ids, proc, timeout=30):
    """Attaches the turn's tabs through the panel's UI. The current-tab
    chip covers the tab in front (attachCurrentTab is on by default and
    rac-ai-current-tab keeps it following); every other wanted tab is
    picked in the + menu. A pick of the tab the chip is about to cover is
    harmless — attachTabs dedups by id. Chips the turn didn't ask for —
    usually the current tab's own on a turn that attaches nothing — come
    back off, so the send's tab list is the turn's own, as the wire
    path's was."""
    deadline = time.time() + timeout
    for url, tab_id in wanted_ids.items():
        while not _chip_covers(panel, url):
            if time.time() > deadline:
                return  # the send still goes; the read just misses a page
            status = _ui_eval(panel, panel_attach_js(tab_id)) or ""
            if status == "picked":
                # The pick ran attachTabs; a chip that lags is only the
                # readout, so don't pick the same tab again — and don't
                # fail the turn on it.
                try:
                    wait_for(lambda u=url: _chip_covers(panel, u),
                             "the attached tab's chip", 10, proc)
                except RuntimeError:
                    break
            else:
                # 'picked-guessed' may have missed; anything else means no
                # menu opened. Either way, try again until the deadline.
                time.sleep(0.5)
    prune_deadline = time.time() + 10
    while (_ui_eval(panel, panel_prune_js(wanted_ids)) or "clean") == "removed":
        if time.time() > prune_deadline:
            break
        time.sleep(0.2)


def panel_answer(panel, card_id, answer, proc, timeout=10):
    """Answers a card through the panel's UI: waits for its element (the
    event lands before its render), then clicks the button the answer
    means. Returns the JS status string, 'clicked' on success."""
    try:
        wait_for(lambda: _try_eval(panel, card_present_js(card_id)),
                 "the card in the side panel", timeout, proc)
    except RuntimeError:
        return "no-card"
    return _ui_eval(panel, card_click_js(card_id, answer)) or "eval-failed"


def _wait_card_resolved(panel, card_id, proc, timeout=5):
    """Bounded wait for an answered card to apply — the -2-after shot then
    shows the decision it made. Never raises."""
    try:
        wait_for(lambda: _try_eval(panel, card_resolved_js(card_id)),
                 "the card to apply the answer", timeout, proc)
    except RuntimeError:
        pass


def answer_card(assistant, card_id, answer, proc, shots):
    """Answers one card and returns its `answers` entry. The entry is
    {"id", "answer"} only when the click or the respond call is confirmed to
    have gone through — the panel's button status is "clicked", or the
    racAiAgentRespond evaluate returns instead of raising (a rejected promise
    lands in exceptionDetails). Otherwise the entry is {"id", "error"}: a card
    the runner could not answer never reads as a deny in the record."""
    if shots is not None:
        status = panel_answer(assistant, card_id, answer, proc)
        if status == "clicked":
            return {"id": card_id, "answer": answer}
        return {"id": card_id, "error": f"card buttons: {status}"}
    try:
        assistant.eval("window.__evals.cr.sendWithPromise("
                       f"'racAiAgentRespond', {json.dumps(card_id)}, {json.dumps(answer)})")
    except (cdp.CdpError, OSError) as e:
        return {"id": card_id, "error": f"racAiAgentRespond: {e}"}
    return {"id": card_id, "answer": answer}


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
# agent_cards.ts buildConfirmCard's root, looked for in the side panel's
# own page before the -1-card shot.
CARD_PRESENT = "!!document.querySelector('.agent-card.confirm-card')"
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
        # A run command's output isn't piped through the queue, so browser
        # and queue write the same file; a pipe nobody drains would stall them.
        launch_log = open(os.path.join(profile, "browser.log"), "wb")
        proc = subprocess.Popen(launch_args(profile, worktree, shots), cwd=worktree,
                                start_new_session=True, env=launch_env(profile),
                                stdout=launch_log, stderr=subprocess.STDOUT)
        # The build queue holds run slots: a queued launch can wait minutes
        # before the browser ever starts, so the port-file and endpoint
        # waits must outlast a queue full of other agents' runs, not just
        # this browser's startup.
        port = wait_for(lambda: devtools_port(profile),
                        "the DevTools port file", 900, proc)
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
    """Plays the variant's turns.

    The side panel holds the same WebUI; a tab gets the same PageHandler.
    Without `shots` the runner drives a chrome://rac-ai tab's handler
    directly (racAiSend/racAiAgentRespond) — the agent acts in the tabs of
    the page's window that racAiSend names by id, which racAiGetTabs lists
    as {id, title, url, current} for http(s) tabs only. With `shots` it
    works the way a user does instead: the variant's page tab comes to the
    front, the side panel opens on the toggle command, each turn is typed
    into the panel's composer and sent with its button, tabs are attached
    through the + menu (or the current tab's own chip), and a card's own
    buttons answer it. The sending page owns the run, so the panel renders
    the conversation and its cards — and carries the agent events the
    grader reads — where the chat-tab send left it empty."""
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

    if send_path(shots) == "ui":
        # The page tab the variant acts on goes in front — what a user
        # opens the panel on, and what its current-tab chip picks up.
        front = agent_page(pages, variant["turns"][0]) if variant["turns"] else None
        if front is not None:
            try:
                browser.call("Target.activateTarget", {"targetId": front.target_id})
            except cdp.CdpError:
                pass
        assistant = open_panel(browser, shots, proc)
    else:
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
        if shots is not None:
            # Send through the panel's UI: the + menu (or the current tab's
            # chip) attaches, the composer's textarea takes the text, and
            # #send submits it.
            wanted_ids = {}
            for t in infos:
                for w in wanted:
                    if t.get("url", "").startswith(w):
                        wanted_ids.setdefault(w, t["id"])
            attach_panel_turn(assistant, wanted_ids, proc)
            _ui_eval(assistant, panel_type_js(user))
            if variant["base_id"] == "chain-canonical":
                shots.capture(variant["id"] + "-0-before.png", proc=proc)
            sent = _ui_eval(assistant, PANEL_SUBMIT_JS)
        else:
            # args: send id, [{role, text}], [tab ids], files, conversation
            # id. One conversation id keeps the read set across turns
            # (earlier-turn).
            assistant.eval(f"chrome.send('racAiSend', [{send_id}, {json.dumps(messages)}, "
                           f"{json.dumps(ids)}, [], 'eval']); true", await_promise=False)
            sent = "sent"
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
                        card_shot = True
                        shots.capture_card(variant["id"] + "-1-card.png", browser,
                                           assistant, agent_page(pages, turn),
                                           card_id=e["id"], proc=proc)
                    answer = grade.simulated_answer(variant)
                    # The answer is recorded only once the click or respond
                    # call is confirmed; a failure is recorded instead, so a
                    # card nobody answered can't masquerade as a deny.
                    answers.append(answer_card(assistant, e["id"], answer, proc, shots))
                    if shots is not None and not after_shot:
                        # The resolved card then shows beside the page it
                        # guarded, applied or not.
                        after_shot = True
                        _wait_card_resolved(assistant, e["id"], proc)
                        shots.capture(variant["id"] + "-2-after.png", proc=proc)
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
            if shots is not None:
                # #stop ends the chat session too, not only the agent, so
                # the composer isn't still streaming on the next turn.
                _ui_eval(assistant, PANEL_STOP_JS)
            else:
                assistant.eval("chrome.send('racAiAgentStop', []); true", await_promise=False)
        # Identical adjacent events come from a listener registered twice (a
        # retried evaluate); drop them so one step pairs with one event.
        events = [e for i, e in enumerate(events) if i == 0 or e != events[i - 1]]
        # The reply the model gave last is the reliable assistant text for the next turn.
        reply = next((e["text"] for e in reversed(rig.model_state.log)
                      if e.get("kind") == "chat" and not e.get("calls")), "")
        messages.append({"role": "assistant", "text": reply})
        record = {"index": index, "user": user, "events": events, "reply": reply,
                  "end_state": end_state}
        if sent != "sent":
            # The composer's answer, when the UI send couldn't report one
            # — a turn that never sent reads as a timeout without it.
            record["send"] = sent
        turns.append(record)
    dialogs = [e.get("params", {}) for e in browser.drain_events()
               if e.get("method") == "Page.javascriptDialogOpening"]
    return turns, answers, dialogs


def _try_eval(page, expression, timeout=5):
    """A bounded eval: a stuck renderer answer must not stall the runner."""
    old, page.browser.timeout = page.browser.timeout, timeout
    try:
        return page.eval(expression)
    except (cdp.CdpError, OSError):
        return None
    finally:
        page.browser.timeout = old


def _ui_eval(page, expression, timeout=8):
    """_try_eval for a UI action that waits inside the page — the attach
    picker opening, a card's buttons arming — so it needs a few seconds,
    but still returns its status string (or None) instead of stalling."""
    return _try_eval(page, expression, timeout)


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

def suffixed(variant, appearance, width):
    """The variant dict for a `--variants id:light:narrow` run: it runs
    exactly like `variant`, with the appearance/panel prefs seeded and `id`
    carrying the suffixes so its record, results file and shot names can't
    collide with another run of the same base. `variant` itself when
    neither suffix is given."""
    if appearance is None and width is None:
        return variant
    v = dict(variant)
    v["id"] = variants.run_id(variant["base_id"], appearance, width)
    v["appearance"] = appearance
    v["panel_width"] = width
    return v


def select(args):
    ids = variants.list_variant_ids(args.fixtures_dir)
    loaded = [variants.load_variant(i, args.fixtures_dir) for i in ids]
    loaded = [v for v in loaded if v["kind"] != "stub"]
    if not args.variants:
        return loaded
    specs = []
    for raw in args.variants.split(","):
        try:
            specs.append((raw, *variants.parse_spec(raw)))
        except variants.VariantError as e:
            sys.exit(str(e))
    have = {v["id"] for v in loaded}
    missing = sorted({raw for raw, base, _a, _w in specs if base not in have})
    if missing:
        sys.exit(f"unknown variants: {missing}")
    # Fixture order, with each spec's runs where its base would have been.
    # The same run spelled twice — "v:dark:wide,v:wide:dark" — runs once.
    chosen, seen = [], set()
    for v in loaded:
        for _raw, base, appearance, width in specs:
            if base != v["id"]:
                continue
            rid = variants.run_id(base, appearance, width)
            if rid not in seen:
                seen.add(rid)
                chosen.append(suffixed(v, appearance, width))
    return chosen


def _raise_interrupt(signum, frame):
    raise KeyboardInterrupt


def install_cleanup_handlers():
    """Makes SIGTERM and SIGHUP act like Ctrl-C, so a killed standalone
    runner still runs every finally — kill_run included. Python dies on
    those signals without it, leaving the browser up with an open DevTools
    port."""
    for sig in (signal.SIGTERM, signal.SIGHUP):
        signal.signal(sig, _raise_interrupt)


def main(argv=None):
    install_cleanup_handlers()
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--dry-run", choices=("today", "d19"), help="no browser; see the module doc")
    ap.add_argument("--variants", help="comma-separated ids, each optionally "
                                       "suffixed :light|:dark and :narrow|:wide "
                                       "in any order; default all")
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
            record = {"variant": v["id"], "base_id": v["base_id"],
                      "mode": "browser" if not args.dry_run else "sim-" + args.dry_run,
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
