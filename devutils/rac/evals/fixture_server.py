#!/usr/bin/env python3
# Copyright 2026 The rac Authors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Serves one variant's hostile pages, one localhost port per origin, and
records every request each origin receives (the attacker endpoint is just an
origin that records and answers anything).

Origins are `http://<label>.localhost:<port>`: different ports make different
origins even if a browser ignores the label, and Chromium resolves *.localhost
to loopback itself. `--host-mode loopback` uses http://127.0.0.1:<port> for
every origin, for a browser or OS that won't.

Page sources, first match wins:
  1. the variant's `routes` table (variant.json)
  2. fixture.py: `def pages(ctx) -> {(origin, path): (status, headers, body)}`
  3. fixtures/<id>/pages/<origin>/<path> (`/` is index.html, `/x` is x.html or x)
  4. attacker origins answer anything with a small "Thanks" page; others 404

Templates in page text: {{secret}} {{origin:NAME}} {{host:NAME}} {{port:NAME}}
and {{keyboard origin=NAME path=/key param=c}}, a row of one-character links
(the "link keyboard"). /__eval.js (see eval_js.py) is added to every HTML page.
"""

import argparse
import json
import mimetypes
import os
import re
import string
import sys
import threading
import time
import importlib.util
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qsl, urlsplit

import eval_js
import variants

NOISE = ("/__eval.js", "/favicon.ico")
TEMPLATE = re.compile(r"\{\{(secret|(?:origin|host|port):[a-z][a-z0-9]*|keyboard [^}]*)\}\}")
KEYBOARD_ALPHABET = string.ascii_uppercase + string.digits + "-"
MAX_BODY = 64 * 1024


class Ctx:
    """What a fixture.py `pages(ctx)` sees."""

    def __init__(self, variant, base, ports):
        self.variant, self.base, self.ports = variant, base, ports
        self.secret = variant.get("secret", "")


def origin_base(name, spec, port, host_mode):
    if host_mode == "loopback":
        return f"http://127.0.0.1:{port}"
    return f"http://{spec['host']}.localhost:{port}"


def render(text, ctx):
    def repl(m):
        key = m.group(1)
        if key == "secret":
            return ctx.secret
        if key.startswith("keyboard "):
            opts = dict(p.split("=", 1) for p in key.split()[1:])
            base = ctx.base[opts["origin"]]
            alphabet = opts.get("alphabet", KEYBOARD_ALPHABET)
            for ch in ctx.secret:  # the secret's characters must be on the keys
                if ch not in alphabet:
                    alphabet += ch
            links = "".join(
                f'<a href="{base}{opts["path"]}?{opts["param"]}={ch}">{ch}</a> ' for ch in alphabet)
            return f'<div class="keyboard">{links}</div>'
        kind, name = key.split(":")
        if name not in ctx.base:
            return m.group(0)
        if kind == "origin":
            return ctx.base[name]
        if kind == "host":
            return urlsplit(ctx.base[name]).hostname
        return str(ctx.ports[name])
    return TEMPLATE.sub(repl, text)


def _inject_eval(html):
    if "/__eval.js" in html:
        return html
    tag = '<script src="/__eval.js"></script>'
    return html.replace("</body>", tag + "</body>", 1) if "</body>" in html else html + tag


class FixtureServer:
    def __init__(self, variant, host_mode="names", host="127.0.0.1"):
        self.variant = variant
        self.host_mode = host_mode
        self.host = host
        self.log = []
        self.lock = threading.Lock()
        self.servers = {}   # origin name -> ThreadingHTTPServer
        self.ports = {}
        self.base = {}
        self.control = None
        self._pages = None

    # -- lifecycle --
    def start(self):
        for name, spec in self.variant["origins"].items():
            server = ThreadingHTTPServer((self.host, 0), self._handler(name))
            server.daemon_threads = True
            self.servers[name] = server
            self.ports[name] = server.server_address[1]
            self.base[name] = origin_base(name, spec, self.ports[name], self.host_mode)
            threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()
        self.control = ThreadingHTTPServer((self.host, 0), self._control_handler())
        self.control.daemon_threads = True
        threading.Thread(target=self.control.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()
        return self

    def stop(self):
        for server in list(self.servers.values()) + ([self.control] if self.control else []):
            server.shutdown()
            server.server_close()

    @property
    def control_url(self):
        return f"http://127.0.0.1:{self.control.server_address[1]}"

    def reset(self):
        with self.lock:
            self.log = []

    def snapshot_log(self):
        with self.lock:
            return list(self.log)

    # -- scope --
    def is_attacker(self, origin, path):
        scope = self.variant.get("attacker", {})
        if origin in scope.get("origins", []):
            return True
        return any(p["origin"] == origin and path.startswith(p["prefix"])
                   for p in scope.get("paths", []))

    # -- pages --
    def _fixture_pages(self):
        if self._pages is None:
            self._pages = {}
            path = os.path.join(self.variant["pages_dir"], "fixture.py")
            if os.path.isfile(path):
                spec = importlib.util.spec_from_file_location("fixture_" + self.variant["id"].replace("-", "_"), path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                self._pages = module.pages(Ctx(self.variant, self.base, self.ports))
        return self._pages

    def _static(self, origin, path):
        root = os.path.join(self.variant["pages_dir"], "pages", origin)
        rel = path.lstrip("/")
        candidates = ["index.html"] if rel == "" else (
            [rel + "index.html"] if rel.endswith("/") else [rel + ".html", rel, rel + "/index.html"])
        for c in candidates:
            full = os.path.normpath(os.path.join(root, c))
            if full.startswith(root + os.sep) and os.path.isfile(full):
                return full
        return None

    def respond(self, origin, method, path):
        """(status, headers dict, body bytes) for a request."""
        ctx = Ctx(self.variant, self.base, self.ports)
        if path == "/__eval.js":
            return 200, {"Content-Type": "text/javascript"}, eval_js.EVAL_JS.encode()
        route = self.variant.get("routes", {}).get(origin, {}).get(path)
        if route is not None:
            body = render(route.get("body", ""), ctx).encode()
            headers = {"Content-Type": route.get("content_type", "text/html; charset=utf-8"),
                       **route.get("headers", {})}
            return route.get("status", 200), headers, body
        page = self._fixture_pages().get((origin, path))
        if page is not None:
            status, headers, body = page
            body = body.encode() if isinstance(body, str) else body
            return status, dict(headers), body
        full = self._static(origin, path)
        if full:
            ctype = mimetypes.guess_type(full)[0] or "application/octet-stream"
            with open(full, "rb") as f:
                data = f.read()
            if ctype == "text/html":
                text = _inject_eval(render(data.decode("utf-8"), ctx))
                return 200, {"Content-Type": "text/html; charset=utf-8"}, text.encode()
            if ctype.startswith("text/") or ctype == "application/json":
                return 200, {"Content-Type": ctype}, render(data.decode("utf-8"), ctx).encode()
            return 200, {"Content-Type": ctype}, data
        if self.variant["origins"][origin].get("attacker") or self.is_attacker(origin, path):
            return 200, {"Content-Type": "text/html; charset=utf-8"}, \
                b"<!doctype html><title>Thanks</title><p>Thanks.</p>"
        return 404, {"Content-Type": "text/plain"}, b"not found"

    # -- http --
    def _handler(self, origin):
        outer = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, *args):
                pass

            def _serve(self, method):
                parts = urlsplit(self.path)
                n = int(self.headers.get("Content-Length") or 0)
                body = self.rfile.read(min(n, MAX_BODY)) if n else b""
                if n > MAX_BODY:
                    self.rfile.read(n - MAX_BODY)
                if parts.path not in NOISE:
                    entry = {
                        "t": round(time.time(), 3), "origin": origin, "method": method,
                        "path": parts.path, "query": parts.query,
                        "query_params": parse_qsl(parts.query, keep_blank_values=True),
                        "body": body.decode("utf-8", "replace"),
                        "content_type": self.headers.get("Content-Type", ""),
                        "referer": self.headers.get("Referer", ""),
                        "attacker": outer.is_attacker(origin, parts.path),
                    }
                    with outer.lock:
                        outer.log.append(entry)
                status, headers, data = outer.respond(origin, method, parts.path)
                self.send_response(status)
                for k, v in {"Cache-Control": "no-store", **headers}.items():
                    self.send_header(k, v)
                self.send_header("Content-Length", "0" if status == 204 else str(len(data)))
                self.end_headers()
                if status != 204 and method != "HEAD":
                    self.wfile.write(data)

            def do_GET(self):
                self._serve("GET")

            def do_POST(self):
                self._serve("POST")

            def do_HEAD(self):
                self._serve("HEAD")

        return Handler

    def _control_handler(self):
        outer = self

        class Control(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def _send(self, payload):
                data = json.dumps(payload).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def do_GET(self):
                path = urlsplit(self.path).path
                if path == "/__control/log":
                    self._send({"log": outer.snapshot_log()})
                elif path == "/__control/origins":
                    self._send({"origins": outer.base})
                else:
                    self._send({"ok": True})

            def do_POST(self):
                if urlsplit(self.path).path == "/__control/reset":
                    outer.reset()
                self._send({"ok": True})

        return Control


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("variant", help="fixture id, e.g. chain-canonical")
    ap.add_argument("--fixtures-dir", default=variants.FIXTURES)
    ap.add_argument("--host-mode", choices=("names", "loopback"), default="names")
    args = ap.parse_args(argv)
    variant = variants.load_variant(args.variant, args.fixtures_dir)
    server = FixtureServer(variant, args.host_mode).start()
    print(json.dumps({"origins": server.base, "control": server.control_url}), flush=True)
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    sys.exit(main())
