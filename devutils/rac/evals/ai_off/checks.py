# Copyright 2026 The rac Authors
# SPDX-License-Identifier: GPL-3.0-or-later
"""The "AI off costs nothing" checks, set 1 (plan 05, "Proving AI off costs
nothing", items 2-6; item 1 is a unit-test matter and not checked here).

Every function takes text or paths that something else collected and returns a
list of problem strings. An empty list is a pass. Nothing here launches a
browser or touches the network, so each check runs against fabricated input
(see test_checks.py and `run_ai_off.py --self-test`).

Where the real output of a tool is guessed, it is marked TODO(binary): the
format has never been captured from a real rac build.
"""

import collections
import glob
import json
import os
import posixpath
import re
import urllib.parse

# --- item 2: no rac-agent-mcp directory, no listening socket ------------------

MCP_DIR_NAME = "rac-agent-mcp"


def check_no_mcp_dir(profile, tmp="/tmp", uid=None, ignore=()):
    """The MCP server never started: `<profile>/rac-agent-mcp` is absent (an
    empty directory counts as present, because the server creates it before
    anything is listening) and so is the long-path fallback
    `<tmp>/rac-mcp-<uid>-<token>/` (ai.md, "The rac MCP server").

    `ignore` lists fallback directory names that already existed before the
    launch. They can belong to another rac that has AI on (the fallback lives
    in a shared /tmp), so only directories that appeared during the run count.
    """
    problems = []
    uid = os.getuid() if uid is None else uid
    mcp = os.path.join(profile, MCP_DIR_NAME)
    if os.path.lexists(mcp):
        kind = "directory" if os.path.isdir(mcp) else "entry"
        listing = sorted(os.listdir(mcp)) if os.path.isdir(mcp) else []
        problems.append(f"{mcp} exists ({kind}, {len(listing)} entries): the MCP server started")
    for path in sorted(glob.glob(os.path.join(glob.escape(tmp), f"rac-mcp-{uid}-*"))):
        if os.path.basename(path) not in ignore:
            problems.append(f"{path} exists: the MCP server started (long-path fallback)")
    return problems


# --- item 3: no child processes beyond Helium's baseline ----------------------

# Chromium's own processes, which AI off must leave exactly as Helium does.
# TODO(binary): this is Helium's baseline as written from memory of Chromium's
# process model. It must be confirmed against `ps` from a real rac run with AI
# off, and trimmed or extended to what actually appears. Keep it as tight as
# the real run allows: every entry is a process the check can no longer catch.
BASELINE_PROCESS_TYPES = {"gpu-process", "renderer", "utility"}
BASELINE_UTILITY_SUBTYPES = {
    "network.mojom.NetworkService",
    "storage.mojom.StorageService",
    "audio.mojom.AudioService",
    "video_capture.mojom.VideoCaptureService",
    "data_decoder.mojom.DataDecoderService",
    "proxy_resolver.mojom.ProxyResolverFactory",
    "tracing.mojom.TracingService",
    "device.mojom.DeviceService",
    "unzip.mojom.Unzipper",
}
# Deliberately absent: on_device_model.mojom.OnDeviceModelService. Chromium's
# own on-device AI would be a real cost of "AI off".
CRASHPAD_MARK = "crashpad_handler"

# Tools an agent or the MCP socket would bring. Used only to say so in the
# problem text; anything outside the baseline fails regardless.
AGENT_TOOLS = {
    "node", "npx", "npm", "bun", "deno", "claude", "codex", "opencode", "nc", "ncat",
    "gemini", "goose", "copilot", "cursor", "cursor-agent", "python", "python3",
}


def parse_ps(text):
    """Parses `ps -axo pid=,ppid=,command=`. Returns dicts with pid, ppid,
    command, and exe. `ps` gives one flat string, so exe is the part before
    the first " -" (a flag); that keeps bundle paths with spaces, such as
    "rac Helper (Renderer)", whole. Malformed lines are skipped."""
    procs = []
    for line in text.splitlines():
        m = re.match(r"^\s*(\d+)\s+(\d+)\s+(\S.*?)\s*$", line)
        if not m:
            continue
        command = m.group(3)
        cut = command.find(" -")
        procs.append({"pid": int(m.group(1)), "ppid": int(m.group(2)), "command": command,
                      "exe": command if cut < 0 else command[:cut]})
    return procs


def descendants(procs, root_pid):
    """Every process below root_pid (not root itself), in breadth-first order."""
    kids = collections.defaultdict(list)
    for p in procs:
        kids[p["ppid"]].append(p)
    seen, out, queue = {root_pid}, [], [root_pid]
    while queue:
        for child in kids.get(queue.pop(0), []):
            if child["pid"] not in seen:
                seen.add(child["pid"])
                out.append(child)
                queue.append(child["pid"])
    return out


def _flag(command, name):
    m = re.search(r"(?:^|\s)--" + re.escape(name) + r"=(\S+)", command)
    return m.group(1) if m else None


def _in_bundle(exe, bundle_path):
    bundle = posixpath.normpath(bundle_path)
    return posixpath.normpath(exe).startswith(bundle.rstrip("/") + "/")


def check_process_tree(ps_text, root_pid, bundle_path):
    """Every descendant of root_pid is one of Chromium's own: an executable
    inside the rac.app bundle that is a gpu, renderer, or allow-listed utility
    process, or the crashpad handler. Anything else, such as a node/npx/claude
    child, an `nc` bound to the MCP socket, or a binary outside the bundle, is
    a problem. See the TODO(binary) on BASELINE_PROCESS_TYPES."""
    procs = parse_ps(ps_text)
    if not any(p["pid"] == root_pid for p in procs):
        return [f"root pid {root_pid} is not in the ps output (the browser is not running?)"]
    problems = []
    for p in descendants(procs, root_pid):
        exe, cmd = p["exe"], p["command"]
        where = f"pid {p['pid']} ({cmd[:100]})"
        tool = posixpath.basename(exe.split()[0]) if exe.split() else ""
        if not _in_bundle(exe, bundle_path):
            what = "agent tool" if tool in AGENT_TOOLS else "executable"
            problems.append(f"{where}: {what} outside the app bundle")
        elif CRASHPAD_MARK in posixpath.basename(exe):
            continue
        else:
            ptype = _flag(cmd, "type")
            if ptype is None:
                problems.append(f"{where}: no --type, so not one of Chromium's helpers")
            elif ptype not in BASELINE_PROCESS_TYPES:
                problems.append(f"{where}: process type {ptype!r} is not in the baseline")
            elif ptype == "utility":
                sub = _flag(cmd, "utility-sub-type")
                if sub is None:
                    problems.append(f"{where}: utility process without a --utility-sub-type")
                elif sub not in BASELINE_UTILITY_SUBTYPES:
                    problems.append(f"{where}: utility sub-type {sub!r} is not in the baseline")
    return problems


def exe_name(exe):
    """A process's name: the last path part, except that an interpreter line
    like "node /x/agent.js" is named for the interpreter. Paths inside an .app
    bundle may hold spaces ("rac Helper (GPU)"), so they are taken whole."""
    if ".app/" in exe:
        return posixpath.basename(exe)
    return posixpath.basename(exe.split()[0]) if exe.split() else ""


def child_names(ps_text, root_pid):
    """Sorted executable names of root_pid's descendants (for compare_states)."""
    return sorted(exe_name(p["exe"]) for p in descendants(parse_ps(ps_text), root_pid))


# --- item 2: no listening socket ----------------------------------------------

# Chromium's process singleton binds <tmp dir>/SingletonSocket and symlinks it
# into the profile. lsof may show either path; neither is the agent socket.
BENIGN_SOCKET_BASENAMES = {"SingletonSocket"}

_LSOF_ROW = re.compile(
    r"^(?P<command>\S.*?)\s+(?P<pid>\d+)\s+(?P<user>\S+)\s+(?P<fd>\S+)\s+(?P<type>unix)\s+"
    r"(?P<device>\S+)\s+(?P<size>\S+)(?:\s+(?P<rest>.*?))?\s*$")


def parse_lsof_unix(text):
    """Parses `lsof -nP -U -a -p <pids>` (columns COMMAND PID USER FD TYPE
    DEVICE SIZE/OFF NODE NAME). Returns dicts with command, pid, user, fd,
    type, device, size, node, and name. On macOS NODE is usually blank and
    NAME follows SIZE/OFF directly, on Linux NODE is an inode, so a leading
    bare number in the remainder is NODE and the rest is NAME. TODO(binary):
    confirm on the real output. Header and malformed lines are skipped."""
    rows = []
    for line in text.splitlines():
        m = _LSOF_ROW.match(line)
        if not m or m.group("command") == "COMMAND":
            continue
        rest = m.group("rest") or ""
        node, name = "", rest
        n = re.match(r"^(\d+)(?:\s+(.*))?$", rest)
        if n:
            node, name = n.group(1), n.group(2) or ""
        rows.append({"command": m.group("command"), "pid": int(m.group("pid")),
                     "user": m.group("user"), "fd": m.group("fd"), "type": m.group("type"),
                     "device": m.group("device"), "size": m.group("size"), "node": node,
                     "name": name.strip()})
    return rows


def _profile_variants(profile):
    p = posixpath.normpath(profile)
    out = {p, os.path.realpath(p)}
    for top in ("/var/", "/tmp/", "/etc/"):  # macOS symlinks these into /private
        if p.startswith(top):
            out.add("/private" + p)
    return out


def socket_paths(rows):
    """The filesystem paths of the sockets in parsed lsof rows. Anonymous
    socketpairs (empty NAME, or `->0x...` peer addresses) have none."""
    paths = []
    for row in rows:
        for part in re.split(r"\s*->\s*", row["name"]):
            part = re.sub(r"\s*\(.*\)$", "", part).strip()
            if part.startswith("/"):
                paths.append(part)
    return sorted(set(paths))


def check_no_agent_sockets(lsof_text, profile):
    """No unix socket under the profile, and none whose path mentions rac-mcp
    or rac-agent (the long-path fallback lives in /tmp, outside the profile).
    Anonymous socketpairs and sockets without a path are fine."""
    problems = []
    variants = _profile_variants(profile)
    for row in parse_lsof_unix(lsof_text):
        for path in socket_paths([row]):
            if posixpath.basename(path) in BENIGN_SOCKET_BASENAMES:
                continue
            inside = any(path == v or path.startswith(v.rstrip("/") + "/") for v in variants)
            if inside or "rac-mcp" in path or "rac-agent" in path:
                problems.append(f"{row['command']} pid {row['pid']} has a unix socket at {path}")
    return problems


# --- item 4: no provider requests ---------------------------------------------

ANNOTATION_IDS = ("rac_ai_chat", "rac_ai_models")
_ANNOTATION_MOD = 138003713


def traffic_annotation_hash(unique_id):
    """The int32 Chromium puts in a net-log event's `traffic_annotation` for
    `net::DefineNetworkTrafficAnnotation(unique_id, ...)`.

    Ported from `net::internal::ComputeAnnotationHash` in
    net/traffic_annotation/network_traffic_annotation.h (NOT
    base::PersistentHash, which that header does not use): a rolling
    `ret = (ret * 31 + char) % 138003713` over the characters, with each char
    a signed byte widened to uint32 as the C++ does. URLRequest puts it in the
    URL_REQUEST_START_JOB params (net/url_request/url_request.cc).

    Verified against the reference values in
    tools/traffic_annotation/scripts/auditor/auditor_test.py (test_iterative_hash:
    "test" -> 3556498, "unique_id" -> 10236504, "123_id" -> 70581310, "ID123" ->
    69491511, "bébé" -> 124751853), which test_checks.py repeats. It is not
    checked against a real net-log from rac.
    """
    ret = 0
    for b in unique_id.encode("utf-8"):
        c = b - 256 if b > 127 else b
        ret = (((ret * 31) & 0xFFFFFFFF) + (c & 0xFFFFFFFF) & 0xFFFFFFFF) % _ANNOTATION_MOD
    return ret


ANNOTATION_HASHES = {traffic_annotation_hash(i): i for i in ANNOTATION_IDS}

_HOST_PARAMS = ("url", "address", "host", "host_port", "hostname", "origin")


def _hostport_forms(model_hostport):
    """Equivalent spellings of the fake model's host:port. The model is
    served on localhost, which Chromium may log as 127.0.0.1 or [::1]."""
    host, _, port = model_hostport.rpartition(":")
    hosts = {host}
    if host in ("localhost", "127.0.0.1", "[::1]", "::1"):
        hosts |= {"localhost", "127.0.0.1", "[::1]"}
    return {f"{h}:{port}" for h in hosts}


def _param_hostports(value):
    """The host:port strings a net-log param value mentions."""
    if not isinstance(value, str):
        return set()
    if "://" in value:
        u = urllib.parse.urlsplit(value)
        try:
            port = u.port or {"http": 80, "https": 443}.get(u.scheme)
        except ValueError:
            return set()
        return {f"{u.hostname}:{port}"} if u.hostname and port else set()
    return {value.strip()}


def load_netlog(path):
    """Reads a Chromium net-log. A browser that was killed leaves
    `{"constants":...,"events":[...` without the closing `]}`, so a missing
    tail is repaired once. Raises ValueError if it still doesn't parse."""
    with open(path, encoding="utf-8", errors="replace") as f:
        text = f.read()
    try:
        return json.loads(text)
    except ValueError:
        pass
    try:
        return json.loads(text.rstrip().rstrip(",") + "]}")
    except ValueError as e:
        raise ValueError(f"net-log is not valid JSON, even with the tail repaired: {e}")


def check_netlog(data, model_hostport=None):
    """Problems in a parsed net-log: a URL_REQUEST_START_JOB with a rac AI
    traffic annotation, or any event that names the fake model's host:port."""
    problems = []
    types = (data.get("constants") or {}).get("logEventTypes") or {}
    by_number = {v: k for k, v in types.items()}
    wanted = _hostport_forms(model_hostport) if model_hostport else set()
    for ev in data.get("events") or []:
        params = ev.get("params") or {}
        name = by_number.get(ev.get("type"), str(ev.get("type")))
        ann = params.get("traffic_annotation")
        if name == "URL_REQUEST_START_JOB" and ann in ANNOTATION_HASHES:
            problems.append(f"net-log: {name} with annotation {ANNOTATION_HASHES[ann]} "
                            f"({params.get('url', '?')})")
        if wanted:
            for key in _HOST_PARAMS:
                if _param_hostports(params.get(key)) & wanted:
                    problems.append(f"net-log: {name} {key}={params[key]} reaches the fake model")
                    break
    return problems


def check_no_provider_requests(model_log, netlog_path=None, model_hostport=None):
    """No request ever reached an AI provider.

    The test profile points the Custom provider at the fake model, so a stray
    request would land in `model_log` (fake_model's State.log: dicts with kind
    "chat" or "models"). ANY entry is a problem. With `netlog_path`, the
    Chromium net-log is checked as well: a URL_REQUEST_START_JOB carrying the
    rac_ai_chat or rac_ai_models annotation hash, and any event that mentions
    `model_hostport` ("localhost:PORT"), since the hash is only verified
    against Chromium's reference values, not against a real rac net-log.
    """
    problems = [f"the fake model got a {e.get('kind', '?')} request: "
                f"{json.dumps(e, sort_keys=True)[:140]}" for e in model_log]
    if netlog_path:
        try:
            problems += check_netlog(load_netlog(netlog_path), model_hostport)
        except (OSError, ValueError) as e:
            problems.append(f"cannot read the net-log {netlog_path}: {e}")
    return problems


# --- item 5: no AI labels ---------------------------------------------------------

# Words that must not appear on any surface while AI is off. Matched whole
# words, case-insensitively.
FORBIDDEN_LABELS = (
    "Assistant", "Ask AI", "Ask", "AI", "Chat", "Summarize", "Summarise",
    "Summarizing", "Summarising", "Agent", "Let AI", "LLM", "Browser control",
)

# Surfaces that may show AI words with AI off: Settings > Assistant holds the
# switch that turns it on. Everything else must be clean.
ALLOWED_SURFACES = {"settings-assistant"}

# Chromium and Helium strings that contain a forbidden word and are not AI.
# TODO(binary): extend from the real settings pages; these are the ones known
# from stock Chromium.
BENIGN_PHRASES = (
    "Ask websites not to track you",
    "Ask where to save each file before downloading",
    "Ask before closing multiple tabs",
)


def _word_pattern(word):
    body = r"\s+".join(re.escape(w) for w in word.split())
    return body + (r"(?:s)?" if len(word) > 3 else "")


def find_forbidden_labels(text, forbidden=FORBIDDEN_LABELS, ignore=()):
    """The forbidden words found in text, case-insensitive on word boundaries
    (so "AI" is not found in "Maintain" or "Gmail", and "AI-powered" is).
    Longest phrase wins, so "Ask AI" reports once, not as "Ask" and "AI". A
    trailing plural s counts for words over 3 letters ("Chats"). Phrases in
    `ignore` are removed first. Returns the entries of `forbidden`, in that
    order."""
    for phrase in ignore:
        text = re.sub(r"(?<!\w)" + _word_pattern(phrase) + r"(?!\w)", " ", text, flags=re.I)
    ordered = sorted(forbidden, key=lambda w: -len(w))
    rx = re.compile(r"(?<![\w])(" + "|".join(_word_pattern(w) for w in ordered) + r")(?![\w])",
                    re.I)
    found = set()
    for m in rx.finditer(text):
        norm = " ".join(m.group(1).lower().split())
        for w in forbidden:
            if norm == w.lower() or (len(w) > 3 and norm == w.lower() + "s"):
                found.add(w)
                break
    return [w for w in forbidden if w in found]


def check_surface_text(surface_id, text, ignore=BENIGN_PHRASES):
    """Problems for the text read from one surface. Allowed surfaces pass."""
    if surface_id in ALLOWED_SURFACES:
        return []
    return [f"{surface_id}: shows {w!r}" for w in find_forbidden_labels(text, ignore=ignore)]


# --- item 6: on and off returns to the baseline -------------------------------------

def make_state(ps_text, root_pid, lsof_text, profile, model_log, tmp="/tmp", uid=None, ignore=()):
    """Collects the observable state compare_states looks at, from the same
    inputs the individual checks use."""
    uid = os.getuid() if uid is None else uid
    dirs = [d for d in (os.path.join(profile, MCP_DIR_NAME),) if os.path.lexists(d)]
    dirs += [p for p in sorted(glob.glob(os.path.join(glob.escape(tmp), f"rac-mcp-{uid}-*")))
             if os.path.basename(p) not in ignore]
    return {"children": child_names(ps_text, root_pid),
            "sockets": [p for p in socket_paths(parse_lsof_unix(lsof_text))
                        if posixpath.basename(p) not in BENIGN_SOCKET_BASENAMES],
            "mcp_dirs": dirs, "provider_requests": len(model_log)}


def compare_states(before, after):
    """Problems when `after` has anything `before` doesn't. A state is
    {"children": [exec names, sorted], "sockets": [...], "mcp_dirs": [...],
    "provider_requests": int}.

    Turning AI off leaves an existing AiService in memory, dormant (ai.md), so
    only what can be observed counts: processes, sockets, directories,
    requests (and, outside this function, UI). Children are compared by name,
    not count, because Chromium may add another renderer for a page opened in
    between; what matters is that no new kind of process stays."""
    problems = []
    for key in ("children", "sockets", "mcp_dirs", "provider_requests"):
        for name, state in (("before", before), ("after", after)):
            if key not in state:
                problems.append(f"{name} state has no {key!r}")
    if problems:
        return problems
    for key in ("children", "sockets", "mcp_dirs"):
        for item in sorted(set(after[key]) - set(before[key])):
            problems.append(f"{key}: {item!r} is new after turning AI on and off")
    if after["provider_requests"] > before["provider_requests"]:
        problems.append(f"provider_requests rose from {before['provider_requests']} "
                        f"to {after['provider_requests']}")
    return problems
