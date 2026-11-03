#!/usr/bin/env python3
# Copyright 2026 The rac Authors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Speed bench: rac vs Helium on the same machine, over DevTools.

  bench.py run --app rac=/path/to/rac.app --app helium=/path/to/Helium.app \
               --rounds 10 --out results.json [--pages DIR]
  bench.py report results.json [--markdown]

Each round launches every app once. The order alternates round to round
(rac, helium; helium, rac; ...) so neither app always runs first and a slow
drift of the machine lands on both sides. One untimed warm-up launch per app
comes first (--warmup, default 1) so first-run costs of a freshly copied app
(code-signature checks, cold disk cache) aren't charged to whichever app
happens to launch first. Both apps get byte-identical flags. A run uses a fresh throwaway profile under the system temp dir
(never a real one: paths under "Application Support" are refused), reads the
DevTools port out of <profile>/DevToolsActivePort, drives the browser with
cdp.py, measures the round's metrics, then kills the whole process tree and
deletes the profile.

Metrics and how each is measured:

  cold_launch_ms      process exec -> the first page target reports
                      document.readyState "complete" (the load event has
                      fired — the check resolves a page-side promise that
                      resolves on 'load' if it hasn't yet). Also recorded:
  devtools_port_ms    exec -> <profile>/DevToolsActivePort first readable.
  new_tab_ms          Target.createTarget about:blank -> its load event (the
                      same readyState/load promise once attached).
  tab_switch_ms       Target.activateTarget of a second loaded tab -> the
                      tab paints a frame: a requestAnimationFrame promise
                      resolved through Runtime.evaluate. Median of 5 switches
                      per round. One method only: if rAF never runs the
                      sample is dropped (and noted), never swapped for a
                      different measurement, so the apps stay comparable.
  scroll_ms           Input.dispatchMouseEvent wheel step on the long page
                      -> the page's scroll listener has run and painted a
                      frame (rAF inside the listener).
  type_latency_ms     Input.dispatchKeyEvent 'x' on the input page -> the
                      element's 'input' event fired (flag read through a
                      resolved promise; event timeStamp stays in-page).
  mem_1tab_mb / mem_10tab_mb / mem_20tab_mb
                      sum of `ps -o rss=` over the app's whole process tree
                      (pgrep -P recursion), after all that level's tabs
                      loaded plus a settle.
  idle_cpu_pct        (tree cputime after - before) / idle window * 100,
                      via `ps -o cputime=`, over a 30 s idle window with all
                      20 tabs open.
  idle_wakeups        sum of the tree's IDLEW column in `top -l 2 -s <idle>`
                      second sample (top -l reports deltas after the first
                      sample). powermetrics would need root; this doesn't.

Results append to --out after every app-round so an interrupted run still
has data. A round's browser stderr log lands in <out stem>-logs/ whenever
the round reported an error.
"""

import argparse
import json
import os
import platform
import re
import shutil
import signal
import statistics
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

# The bench's own modules sit next to it; make that work under python3 -I too.
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import cdp  # noqa: E402

PROFILE_PREFIX = "rac-bench-"
PORT_TIMEOUT = 120        # seconds to wait for DevToolsActivePort / the endpoint
LOAD_TIMEOUT = 30         # a page may take this long to finish loading
RAF_TIMEOUT = 10          # frame-painted waits (tab switch, reveal)
MEM_SETTLE_S = 2.0        # quiet time after each memory level's loads
IDLE_SECONDS = 30         # the idle-CPU/wakeups window
CDP_TIMEOUT = 15          # default per-call
# Tabs opened for the memory ladder cycle these pages, so tabs 1/2/3 are
# index/long/input and the scroll and typing steps reuse them.
PAGES_CYCLE = ["index.html", "long.html", "input.html"]

# Report row order; metrics outside it (future ones) print after, sorted.
METRIC_ORDER = ["cold_launch_ms", "devtools_port_ms", "new_tab_ms",
                "tab_switch_ms", "scroll_ms", "type_latency_ms",
                "mem_1tab_mb", "mem_10tab_mb",
                "mem_20tab_mb", "idle_cpu_pct", "idle_wakeups"]


# --- stats ------------------------------------------------------------

def summarize(values):
    """median/min/max/n for one metric's samples; None over an empty set."""
    xs = [v for v in values if isinstance(v, (int, float))]
    if not xs:
        return None
    return {"median": statistics.median(xs), "min": min(xs), "max": max(xs),
            "n": len(xs)}


def fmt_num(v):
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    return f"{v:.1f}" if isinstance(v, float) else str(v)


def fmt_cell(s):
    if s is None:
        return "—"
    return f"{fmt_num(s['median'])} ({fmt_num(s['min'])}–{fmt_num(s['max'])}, n={s['n']})"


# --- safety: throwaway profiles only -------------------------------------

def make_profile(base=None):
    """A fresh temp dir for one run's --user-data-dir. `base` exists so tests
    can redirect the check; it defaults to the system temp dir. Any path
    containing "Application Support" — a real browser profile's home on
    macOS — is refused outright."""
    root = os.path.realpath(base or tempfile.gettempdir())
    assert "Application Support" not in root, f"refusing profile folder {root}"
    path = tempfile.mkdtemp(prefix=PROFILE_PREFIX, dir=root)
    real = os.path.realpath(path)
    assert "Application Support" not in real, f"refusing profile folder {real}"
    return real


# --- launch ---------------------------------------------------------------

def app_executable(path):
    """Accepts either a .app bundle dir or the binary inside it. For a
    bundle, Contents/MacOS holds the main executable; the file named after
    the bundle wins if there are several."""
    if os.path.isfile(path):
        return path
    macos = os.path.join(path, "Contents", "MacOS")
    if not os.path.isdir(macos):
        raise RuntimeError(f"no such app or binary: {path}")
    files = sorted(f for f in os.listdir(macos)
                   if os.path.isfile(os.path.join(macos, f)))
    if not files:
        raise RuntimeError(f"no executable under {macos}")
    want = re.sub(r"\.app$", "", os.path.basename(path), flags=re.I)
    for f in files:
        if f.lower() == want.lower():
            return os.path.join(macos, f)
    if len(files) == 1:
        return os.path.join(macos, files[0])
    raise RuntimeError(f"can't pick an executable in {macos}: {files}")


def launch_args(binary, profile):
    """The launch command, identical for every app. The flags keep the run
    quiet and offline: no first-run UI, no default-browser prompt, no
    background networking or component updates, and a mock keychain so no
    Keychain prompt can stall a launch (or touch the real keychain). Port 0
    lets Chromium pick the DevTools port and write it to
    <profile>/DevToolsActivePort.

    rac's --rac-launch-in-background is deliberately NOT passed: it changes
    how the window is shown (never activates the app, paints it as active),
    and Helium has no equivalent, so using it for one side would skew
    launch and frame timings. Run the bench on a machine nobody is using;
    in CI there is no foreground to protect."""
    return [binary,
            f"--user-data-dir={profile}",
            "--no-first-run", "--no-default-browser-check",
            "--disable-background-networking", "--disable-component-update",
            "--use-mock-keychain",
            "--remote-debugging-port=0", "--remote-debugging-address=127.0.0.1"]


def launch_env(profile):
    """A small explicit environment — the browser doesn't need this shell's
    secrets, and crash dumps go inside the throwaway profile so a run never
    writes a real Crashpad folder."""
    env = {k: os.environ[k] for k in ("HOME", "PATH", "TMPDIR", "LANG")
           if k in os.environ}
    env["BREAKPAD_DUMP_LOCATION"] = os.path.join(profile, "Crashpad")
    return env


def devtools_port(profile):
    """The port --remote-debugging-port=0 picked: the first line of
    <profile>/DevToolsActivePort. None until the browser writes it."""
    try:
        with open(os.path.join(profile, "DevToolsActivePort")) as f:
            return int(f.readline().strip())
    except (OSError, ValueError):
        return None


def http_json(url):
    try:
        with urllib.request.urlopen(url, timeout=2) as r:
            return json.load(r)
    except (OSError, ValueError):
        return None


def wait_for(check, what, timeout, proc=None):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if proc is not None and proc.poll() is not None:
            raise RuntimeError("the browser exited while waiting for " + what)
        value = check()
        if value:
            return value
        time.sleep(0.1)
    raise RuntimeError("timed out waiting for " + what)


def _profile_pids(profile):
    out = subprocess.run(["pgrep", "-f", "--", f"--user-data-dir={profile}"],
                         capture_output=True, text=True).stdout
    return {int(p) for p in out.split() if p.isdigit()}


def kill_tree(proc, profile, grace=20):
    """End the launch's whole process tree and wait for it. The tree is
    snapshotted first (children, found by parent pid, and anything carrying
    this throwaway profile's --user-data-dir — no other browser, and
    certainly not a real one, can match), the launch's process group gets
    SIGTERM, and whatever is still alive after `grace` seconds gets SIGKILL.
    Returns True once nothing of the tree is left."""
    pids = set()
    if proc.poll() is None:
        pids |= tree_pids(proc.pid)
    pids |= _profile_pids(profile)
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except (ProcessLookupError, PermissionError):
        pass
    try:
        proc.wait(timeout=grace)
    except subprocess.TimeoutExpired:
        pass
    deadline = time.time() + grace
    while time.time() < deadline and _alive(pids):
        time.sleep(0.25)
    for pid in _alive(pids):
        try:
            os.kill(pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        pass
    deadline = time.time() + 10
    while time.time() < deadline:
        if not _alive(pids):
            return True
        time.sleep(0.25)
    return False


def _alive(pids):
    out = set()
    for pid in pids:
        try:
            os.kill(pid, 0)
            out.add(pid)
        except ProcessLookupError:
            pass
        except PermissionError:
            out.add(pid)
    return out


# --- the process tree (memory / cpu / wakeups) ------------------------------

def _run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def tree_pids(root_pid, run=_run):
    """root plus every descendant found by `pgrep -P`, breadth-first."""
    seen, queue = {root_pid}, [root_pid]
    while queue:
        parent = queue.pop()
        out = run(["pgrep", "-P", str(parent)]).stdout
        for word in out.split():
            if word.isdigit() and int(word) not in seen:
                seen.add(int(word))
                queue.append(int(word))
    return seen


def _ps_field(pids, field, run):
    out = run(["ps", "-o", f"{field}=", "-p", ",".join(str(p) for p in pids)])
    return out.stdout


def tree_rss_kb(root_pid, run=_run):
    """Sum of RSS (KiB) over the process tree; a line that isn't a bare
    number is ignored rather than parsed."""
    total = 0
    for word in _ps_field(tree_pids(root_pid, run), "rss", run).split():
        if word.isdigit():
            total += int(word)
    return total


def parse_cputime(text):
    """A `ps -o cputime=` value like "0:01.23" or "1:02:03.50" -> seconds."""
    try:
        nums = [float(p) for p in text.strip().split(":")]
    except ValueError:
        return 0.0
    seconds = 0.0
    for n in nums:
        seconds = seconds * 60 + n
    return seconds


def tree_cputimes(root_pid, run=_run):
    """{pid: cumulative cpu seconds} for the process tree. `ps` prints rows
    in pid order, so the pids are asked for sorted and zipped back."""
    pids = sorted(tree_pids(root_pid, run))
    rows = [w for w in _ps_field(pids, "cputime", run).split("\n") if w.strip()]
    return dict(zip(pids, (parse_cputime(w) for w in rows)))


def tree_cputime_s(root_pid, run=_run):
    return sum(tree_cputimes(root_pid, run).values())


def parse_top_sample(output):
    """The LAST sample block of `top -l N -stats pid,cpu,idlew`, as
    {pid: (cpu_pct, idlew)}. With -l, every sample after the first reports
    deltas over the -s interval, so the last block is the measured window."""
    samples = output.split("Processes:")
    if len(samples) < 3:  # header text before the first "Processes:" line
        return {}
    rows = {}
    for line in samples[-1].splitlines():
        m = re.match(r"\s*(\d+)\s+([0-9.]+)\s+(\d+)\b", line)
        if m:
            rows[int(m.group(1))] = (float(m.group(2)), int(m.group(3)))
    return rows


def idle_sample(root_pid, seconds, run=_run):
    """idle_cpu_pct over `seconds` from the cputime delta, and idle_wakeups
    from top's IDLEW column over the same window. top itself runs `seconds`
    long, so one wait covers both."""
    cpu0 = tree_cputimes(root_pid, run)
    top = run(["top", "-l", "2", "-s", str(seconds), "-stats", "pid,cpu,idlew"])
    cpu1 = tree_cputimes(root_pid, run)
    pids = set(cpu1)
    # Per-pid delta over processes alive at both ends: a helper born (or
    # gone) mid-window would otherwise add (or drop) its whole lifetime.
    cpu_pct = sum(cpu1[p] - cpu0[p] for p in cpu1 if p in cpu0) / seconds * 100
    rows = parse_top_sample(top.stdout)
    wakeups = sum(v[1] for p, v in rows.items() if p in pids)
    return cpu_pct, (wakeups if rows else None)


# --- pages server -----------------------------------------------------------

class _Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def serve_pages(directory):
    """A quiet stdlib http.server on 127.0.0.1 with an ephemeral port."""
    handler = lambda *a, **kw: _Quiet(*a, directory=directory, **kw)  # noqa: E731
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever,
                     kwargs={"poll_interval": 0.1}, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


# --- driving the browser ----------------------------------------------------

WAIT_LOADED_JS = (
    "new Promise(r => {"
    " if (document.readyState === 'complete') r(1);"
    " else addEventListener('load', () => r(1), {once: true});"
    " })")


class Page:
    """One DevTools page session (attached with flatten=True)."""

    def __init__(self, browser, target_id):
        self.browser, self.target_id = browser, target_id
        self.session = browser.call("Target.attachToTarget",
                                    {"targetId": target_id, "flatten": True})["sessionId"]

    def call(self, method, params=None):
        return self.browser.call(method, params, self.session)

    def eval(self, expression, await_promise=True, timeout=None):
        old = self.browser.timeout
        self.browser.timeout = timeout or old
        try:
            r = self.call("Runtime.evaluate",
                          {"expression": expression, "returnByValue": True,
                           "awaitPromise": await_promise})
        finally:
            self.browser.timeout = old
        if r.get("exceptionDetails"):
            raise cdp.CdpError("page error: " + json.dumps(r["exceptionDetails"])[:300])
        return r["result"].get("value")

    def wait_loaded(self, timeout=LOAD_TIMEOUT):
        self.eval(WAIT_LOADED_JS, timeout=timeout)


def open_tab(browser, url, timeout=LOAD_TIMEOUT, background=True):
    """createTarget + attach + wait for the load event. `background` keeps
    the currently active tab in front."""
    tid = browser.call("Target.createTarget",
                       {"url": url, "background": background})["targetId"]
    page = Page(browser, tid)
    page.wait_loaded(timeout)
    return page


def activate(browser, page):
    browser.call("Target.activateTarget", {"targetId": page.target_id})


def measure_tab_switch(browser, a, b):
    """activateTarget B -> B paints a frame (rAF through Runtime.evaluate),
    after activating A so B starts hidden. One method for every app; raises
    CdpError if rAF never fires rather than substituting another."""
    activate(browser, a)
    time.sleep(0.3)
    t0 = time.monotonic()
    activate(browser, b)
    b.eval("new Promise(r => requestAnimationFrame(() => r(1)))",
           timeout=RAF_TIMEOUT)
    return (time.monotonic() - t0) * 1000


SCROLL_ARM_JS = (
    "(() => { window.__benchScroll = 0;"
    " addEventListener('scroll', () => requestAnimationFrame("
    "   () => { window.__benchScroll = scrollY; }), {once: true});"
    " return 'armed'; })()")
SCROLL_WAIT_JS = ("new Promise(r => { const h = () => window.__benchScroll"
                  " ? r(window.__benchScroll) : setTimeout(h, 2); h(); })")


def measure_scroll(page):
    """One wheel step -> the scroll listener ran and a frame painted."""
    page.eval(SCROLL_ARM_JS, await_promise=False)
    t0 = time.monotonic()
    page.call("Input.dispatchMouseEvent",
              {"type": "mouseWheel", "x": 400, "y": 300,
               "deltaX": 0, "deltaY": 600})
    page.eval(SCROLL_WAIT_JS, timeout=RAF_TIMEOUT)
    return (time.monotonic() - t0) * 1000


TYPE_ARM_JS = (
    "(() => { const i = document.getElementById('t'); if (!i) return 'no-input';"
    " i.focus(); window.__benchIn = 0;"
    " i.addEventListener('input', () => { window.__benchIn = performance.now(); },"
    " {once: true}); return 'armed'; })()")
TYPE_WAIT_JS = ("new Promise(r => { const h = () => window.__benchIn"
                " ? r(window.__benchIn) : setTimeout(h, 1); h(); })")


def measure_typing(page):
    """dispatchKeyEvent 'x' -> the input element's 'input' event fired."""
    if page.eval(TYPE_ARM_JS, await_promise=False) != "armed":
        raise cdp.CdpError("the input page has no #t element")
    t0 = time.monotonic()
    page.call("Input.dispatchKeyEvent",
              {"type": "keyDown", "key": "x", "code": "KeyX", "text": "x"})
    page.call("Input.dispatchKeyEvent",
              {"type": "keyUp", "key": "x", "code": "KeyX"})
    page.eval(TYPE_WAIT_JS, timeout=RAF_TIMEOUT)
    return (time.monotonic() - t0) * 1000


# --- one round --------------------------------------------------------------

def measure_round(app, page_base, settle_s, idle_s, log_dir=None):
    """One launch -> measure -> kill cycle for one app. Returns (metrics,
    errors, info): a metric that couldn't be taken is absent and named in
    errors; info holds non-numeric facts such as the startup page's URL."""
    profile = make_profile()
    os.makedirs(os.path.join(profile, "Crashpad"))
    m, errors, info = {}, [], {}
    log_path = os.path.join(profile, "browser.log")
    log = open(log_path, "wb")
    proc, browser = None, None
    try:
        t0 = time.monotonic()
        proc = subprocess.Popen(
            launch_args(app["binary"], profile),
            stdout=log, stderr=subprocess.STDOUT,
            env=launch_env(profile), start_new_session=True)
        port = wait_for(lambda: devtools_port(profile), "the DevTools port file",
                        PORT_TIMEOUT, proc)
        m["devtools_port_ms"] = (time.monotonic() - t0) * 1000
        endpoint = wait_for(
            lambda: http_json(f"http://127.0.0.1:{port}/json/version"),
            "the DevTools endpoint", PORT_TIMEOUT, proc)
        browser = cdp.Cdp(endpoint["webSocketDebuggerUrl"], timeout=CDP_TIMEOUT)
        # The window's first page target may appear a moment after the
        # endpoint does; poll for it rather than failing the round.
        def first_page():
            targets = browser.call("Target.getTargets").get("targetInfos", [])
            return next((t for t in targets if t.get("type") == "page"), None)
        first = wait_for(first_page, "the first page target", PORT_TIMEOUT, proc)
        info["startup_url"] = first.get("url", "")
        page0 = Page(browser, first["targetId"])
        page0.wait_loaded(PORT_TIMEOUT)
        m["cold_launch_ms"] = (time.monotonic() - t0) * 1000

        # Memory ladder: tab 1 is the startup page navigated to our local
        # index; 9 and 10 more cycle the three pages. Navigating a loaded
        # page can't reuse the readyState trick — the old document is already
        # complete — so Page.enable + a Page.loadEventFired event does it.
        page0.call("Page.enable")
        page0.call("Page.navigate", {"url": page_base + "/" + PAGES_CYCLE[0]})
        browser.wait_event("Page.loadEventFired", page0.session, LOAD_TIMEOUT)
        tabs = [page0]
        for count in (1, 10, 20):
            while len(tabs) < count:
                url = page_base + "/" + PAGES_CYCLE[len(tabs) % len(PAGES_CYCLE)]
                tabs.append(open_tab(browser, url))
            time.sleep(settle_s)
            m[f"mem_{count}tab_mb"] = tree_rss_kb(proc.pid) / 1024

        # New tab: about:blank createTarget -> load, then close it.
        t = time.monotonic()
        nt = open_tab(browser, "about:blank")
        m["new_tab_ms"] = (time.monotonic() - t) * 1000
        browser.call("Target.closeTarget", {"targetId": nt.target_id})

        # Tab switch between the two first local pages.
        try:
            # Five alternating switches; the round keeps their median.
            samples = [measure_tab_switch(browser, *pair) for pair in
                       ((tabs[0], tabs[1]), (tabs[1], tabs[0])) * 2 +
                       ((tabs[0], tabs[1]),)]
            m["tab_switch_ms"] = statistics.median(samples)
        except (cdp.CdpError, OSError) as e:
            errors.append({"metric": "tab_switch_ms", "error": str(e)})

        # Scroll on tab 2 (long.html), typing on tab 3 (input.html).
        for metric, index, fn in (("scroll_ms", 1, measure_scroll),
                                  ("type_latency_ms", 2, measure_typing)):
            try:
                page = tabs[index]
                activate(browser, page)
                time.sleep(0.3)  # let the switch finish before timing input
                m[metric] = fn(page)
            except (cdp.CdpError, OSError, IndexError) as e:
                errors.append({"metric": metric, "error": str(e)})

        # Idle: everything above is done; a short settle, then a quiet
        # window with all 20 tabs open.
        time.sleep(settle_s)
        try:
            cpu, wake = idle_sample(proc.pid, idle_s)
            m["idle_cpu_pct"], m["idle_wakeups"] = cpu, wake
            if wake is None:
                errors.append({"metric": "idle_wakeups",
                               "error": "top -l produced no samples"})
        except (OSError, RuntimeError) as e:
            errors.append({"metric": "idle_cpu_pct", "error": str(e)})
        return m, errors, info
    except Exception as e:
        # A stray failure costs this app its round, never the whole bench:
        # the other app's rounds still have to run.
        errors.append({"metric": "round", "error": f"{type(e).__name__}: {e}"})
        return m, errors, info
    finally:
        if browser is not None:
            browser.close()
        if proc is not None:
            if not kill_tree(proc, profile):
                errors.append({"metric": "round",
                               "error": "process tree survived SIGKILL"})
        log.close()
        if errors and log_dir:
            os.makedirs(log_dir, exist_ok=True)
            try:
                shutil.copy(log_path, os.path.join(
                    log_dir, f"{app['name']}-{app.get('round', 0)}.log"))
            except OSError:
                pass
        if os.path.basename(profile).startswith(PROFILE_PREFIX):
            shutil.rmtree(profile, ignore_errors=True)


# --- report -----------------------------------------------------------------

def load_results(path):
    with open(path) as f:
        return json.load(f)


def metric_names(doc):
    names = [m for m in METRIC_ORDER
             if any(m in s.get("metrics", {}) for s in doc["samples"])]
    extra = sorted({m for s in doc["samples"] for m in s.get("metrics", {})}
                   - set(names))
    return names + extra


def ratio_pair(app_names):
    """(numerator, denominator) for the ratio column: the first rac* app
    over the first non-rac* app — rac/Helium on the usual pair."""
    rac = next((n for n in app_names if n.startswith("rac")), None)
    other = next((n for n in app_names if n != rac), None)
    return (rac, other) if rac and other else None


def format_report(doc, markdown=False):
    apps = [a["name"] for a in doc["apps"]]
    by_app = {n: [s.get("metrics", {}) for s in doc["samples"] if s["app"] == n]
              for n in apps}
    pair = ratio_pair(apps)
    names = metric_names(doc)
    ratio_title = f"{pair[0]}/{pair[1]}" if pair else None
    rows = []
    for metric in names:
        cells, stats = [], {}
        for n in apps:
            s = summarize([mm.get(metric) for mm in by_app[n]])
            stats[n] = s
            cells.append(fmt_cell(s))
        ratio = "—"
        if pair and stats.get(pair[0]) and stats.get(pair[1]):
            ratio = f"{stats[pair[0]]['median'] / stats[pair[1]]['median']:.3f}"
        rows.append((metric, cells, ratio))

    # Notes on skipped/fallback samples, and any whole-round failures.
    notes = []
    for s in doc["samples"]:
        for e in s.get("errors", []):
            where = f"{s['app']} r{s['round']}"
            notes.append(f"{e.get('metric', 'round')}: {where}: {e['error']}")

    if markdown:
        header = "| metric | " + " | ".join(apps) + \
                 (" | " + ratio_title if ratio_title else "") + " |"
        lines = [header, "| --- " * (len(apps) + 1 + bool(ratio_title)) + "|"]
        for metric, cells, ratio in rows:
            lines.append("| " + metric + " | " + " | ".join(cells) +
                         (f" | {ratio}" if ratio_title else "") + " |")
    else:
        col = max([len(r[0]) for r in rows] + [len("metric")])
        width = max([len(c) for r in rows for c in r[1]] + [1])
        head = "metric".ljust(col) + "  " + "  ".join(n.ljust(width) for n in apps)
        if ratio_title:
            head += "  " + ratio_title
        lines = [head, "-" * len(head)]
        for metric, cells, ratio in rows:
            line = metric.ljust(col) + "  " + "  ".join(c.ljust(width) for c in cells)
            lines.append(line + (f"  {ratio}" if ratio_title else ""))
    if notes:
        lines += ["", "samples skipped / measured with fallback:"]
        lines += ["  " + n for n in notes]
    for n in apps:
        urls = sorted({x["startup_url"] for x in doc["samples"]
                       if x["app"] == n and x.get("startup_url")})
        if urls:
            lines.append(f"{n} startup page: {', '.join(urls)}")
    note = f"{len(doc['samples'])} samples, {doc.get('rounds', '?')} rounds requested"
    if doc.get("host"):
        note += f", {doc['host']}"
    lines.append(note)
    return "\n".join(lines)


# --- run orchestration ------------------------------------------------------

def parse_app_spec(spec):
    if "=" not in spec:
        raise argparse.ArgumentTypeError(f"--app wants NAME=PATH, got {spec!r}")
    name, path = spec.split("=", 1)
    if not name or not path:
        raise argparse.ArgumentTypeError(f"--app wants NAME=PATH, got {spec!r}")
    return {"name": name, "path": path}


def round_order(apps, r):
    """Apps in launch order for round r (1-based): reversed on even rounds,
    so over the run each app is first as often as last."""
    return list(apps) if r % 2 else list(reversed(apps))


def run_bench(apps, rounds, pages_dir, idle_s, settle_s, log_dir=None,
              warmup=1):
    """Yields the results doc after every app-round so the caller can persist
    it: an interrupted bench still has data. `warmup` untimed rounds run
    first, in the same alternating order, and are not recorded."""
    for app in apps:
        app["binary"] = app_executable(app["path"])
    doc = {"format": 2,
           "started": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "rounds": rounds,
           "warmup": warmup,
           "host": f"{platform.system()} {platform.release()} {platform.machine()}",
           "apps": [{"name": a["name"], "path": a["path"]} for a in apps],
           "samples": []}
    server, page_base = serve_pages(pages_dir)
    try:
        for r in range(1 - warmup, rounds + 1):
            order = round_order(apps, r if r >= 1 else r + 1)
            for app in order:
                app["round"] = r
                label = f"round {r}/{rounds}" if r >= 1 else "warm-up"
                print(f"{label} {app['name']}: launching", flush=True)
                metrics, errors, info = measure_round(
                    app, page_base, settle_s, idle_s, log_dir)
                for e in errors:
                    print(f"  note: {e['metric']}: {e['error']}", flush=True)
                print(f"  {len(metrics)} metrics ok", flush=True)
                if r < 1:
                    continue
                doc["samples"].append({"app": app["name"], "round": r,
                                       "metrics": metrics, "errors": errors,
                                       **info})
                yield doc
    finally:
        server.shutdown()
        server.server_close()


def write_results(path, doc):
    tmp = path + ".tmp"
    doc["finished"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with open(tmp, "w") as f:
        json.dump(doc, f, indent=1, sort_keys=True)
    os.replace(tmp, path)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=__doc__.split("\n")[0],
        formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    run = sub.add_parser("run", help="launch the apps and measure")
    run.add_argument("--app", action="append", type=parse_app_spec, required=True,
                     metavar="NAME=PATH", help="an app to bench (repeatable); "
                     "PATH may be the .app bundle or its binary")
    run.add_argument("--rounds", type=int, default=10)
    run.add_argument("--out", required=True, metavar="RESULTS_JSON")
    run.add_argument("--pages", default=os.path.join(HERE, "pages"),
                     help="dir of test pages to serve (default: pages/ here)")
    run.add_argument("--idle-seconds", type=int, default=IDLE_SECONDS)
    run.add_argument("--warmup", type=int, default=1,
                     help="untimed launches per app before the rounds")
    run.add_argument("--settle-seconds", type=float, default=MEM_SETTLE_S)
    rep = sub.add_parser("report", help="summarize a results file")
    rep.add_argument("results")
    rep.add_argument("--markdown", action="store_true",
                     help="emit a GitHub markdown table")
    args = parser.parse_args(argv)

    if args.cmd == "report":
        try:
            doc = load_results(args.results)
        except (OSError, ValueError) as e:
            parser.error(f"can't read {args.results}: {e}")
        print(format_report(doc, args.markdown))
        return 0
    if args.rounds < 1:
        parser.error("--rounds must be at least 1")
    if args.idle_seconds < 5:
        parser.error("--idle-seconds must be at least 5")
    if args.warmup < 0:
        parser.error("--warmup must be at least 0")
    if args.settle_seconds < 0:
        parser.error("--settle-seconds must be at least 0")
    if len({a["name"] for a in args.app}) != len(args.app):
        parser.error("app names must be unique")
    if not os.path.isdir(args.pages):
        parser.error(f"no pages dir at {args.pages}")
    log_dir = os.path.splitext(args.out)[0] + "-logs"
    try:
        for doc in run_bench(args.app, args.rounds, args.pages,
                             args.idle_seconds, args.settle_seconds, log_dir,
                             args.warmup):
            write_results(args.out, doc)
    except RuntimeError as e:
        parser.error(str(e))
    print(f"wrote {args.out}", flush=True)
    print(format_report(load_results(args.out)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
