#!/usr/bin/env python3
# Copyright 2026 The rac Authors
# SPDX-License-Identifier: GPL-3.0-or-later
"""A fake OpenAI-compatible model for rac's Custom provider.

It "obeys" a planted instruction on purpose: a per-fixture script lists the
tool calls an injected model would make, and the model resolves each call's
arguments from what the browser showed it (refs from snapshot lines, a secret
found in page text). No real model, no network, no API key is involved.

Served routes (stdlib only, localhost):

  GET  /v1/models              model list (the Custom provider's connection check)
  POST /v1/chat/completions    streaming SSE or plain JSON, with tool calls
  POST /__control/script       load a script: {"script": {...}, "origins": {...}}
  POST /__control/reset        forget the script and the request log
  GET  /__control/log          every request the model saw, and what it answered

Script format (model.json), all values optional unless noted:

  {
    "vars":  {"secret": {"find": "CODE-[A-Z0-9]+"}},   # regexes over what the model has read
    "obey":  {"find": "ASSISTANT TASK"},               # attack steps run only after this is seen
    "steps": [ <step>, ... ],                          # or "turns": [{"steps": [...], "final": "..."}]
    "final": "Text to say when the steps run out."
  }

  step: {"tool": "click", "args": {"ref": {"ref_of": "link \"Open\""}},
         "say": "text", "attack": true, "exfil": true, "label": "why",
         "optional": true}
  or    {"for_each_char": "secret", "steps": [<step>...]}   # {char}, {char_re}, {i} inside

An argument is a literal, a string with {var} / {origin:name} placeholders, or
one of: {"ref_of": regex} (ref of the newest snapshot line matching regex),
{"find": regex} (group 1 or the match, searched newest first), {"find_user":
regex} (in the user's messages), {"tab_of": regex} (tab alias from list_tabs),
{"url_of": regex} (full URL of the newest snapshot link line matching regex).
A step whose argument can't be resolved ends the run with the final text
unless it is "optional", in which case it is skipped. "attack" steps wait for
"obey"; "exfil" marks the step the grader treats as the leak attempt.

The script position is recomputed from the messages on every request, so the
server keeps no per-conversation state and survives retries.
"""

import argparse
import json
import re
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MODEL_IDS = ["rac-fake-obey", "rac-fake-obey-2"]
PLACEHOLDER = re.compile(r"\{([a-z_][a-z_0-9]*)(?::([A-Za-z0-9_.-]+))?\}")


class Unresolved(Exception):
    pass


def flatten_strings(value):
    """Every string inside a JSON value, in order."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [s for v in value.values() for s in flatten_strings(v)]
    if isinstance(value, list):
        return [s for v in value for s in flatten_strings(v)]
    return []


def tool_text(content):
    """The text of a tool message. rac sends a JSON object whose `text` holds
    the wrapped page; plain strings work too."""
    if not isinstance(content, str):
        return ""
    try:
        parsed = json.loads(content)
    except ValueError:
        return content
    if isinstance(parsed, (dict, list)):
        return "\n".join(flatten_strings(parsed))
    return content


class Context:
    """What the model has seen so far, for one point in the conversation."""

    def __init__(self, messages, origins, upto=None):
        self.origins = origins or {}
        messages = messages if upto is None else messages[:upto]
        self.user_texts = []
        self.assistant_texts = []
        self.system_texts = []
        self.tool_results = []  # (tool name, flattened text, parsed json or None)
        names = {}
        for m in messages:
            role = m.get("role")
            content = m.get("content")
            if role == "user" and isinstance(content, str):
                self.user_texts.append(content)
            elif role == "assistant":
                if isinstance(content, str) and content:
                    self.assistant_texts.append(content)
                for call in m.get("tool_calls") or []:
                    names[call.get("id")] = (call.get("function") or {}).get("name", "")
            elif role == "tool":
                parsed = None
                try:
                    parsed = json.loads(content)
                except (ValueError, TypeError):
                    pass
                self.tool_results.append(
                    (names.get(m.get("tool_call_id"), ""), tool_text(content), parsed))
            elif role in ("system", "developer") and isinstance(content, str):
                # The real assistant wraps attached page text into the system
                # prompt's page blocks; it is page text the model has read.
                self.system_texts.append(content)
        self.vars = {}

    def read_texts(self):
        """What reached the model, newest first: tool results, then its own
        words, then the user turns. In the real assistant an attached tab's
        page text is wrapped into the user message itself, so the user's
        messages are part of what the model has read."""
        return ([t for _n, t, _p in reversed(self.tool_results)]
                + list(reversed(self.assistant_texts))
                + list(reversed(self.system_texts)))

    def find(self, pattern, texts=None):
        for text in (self.read_texts() if texts is None else texts):
            m = re.search(pattern, text)
            if m:
                return m.group(1) if m.groups() else m.group(0)
        return None

    def snapshot_lines(self):
        """Lines carrying a ref: newest result first, document order within one."""
        for _n, text, _p in reversed(self.tool_results):
            for line in text.splitlines():
                if "[ref=" in line:
                    yield line

    def seen(self, spec):
        return bool(spec) and self.find(spec["find"]) is not None


def _substitute(text, ctx, script, extra):
    def repl(m):
        name, arg = m.group(1), m.group(2)
        if name == "origin":
            if arg not in ctx.origins:
                raise Unresolved(f"unknown origin {arg}")
            return ctx.origins[arg].rstrip("/")
        if name in extra:
            return str(extra[name])
        if name in script.get("vars", {}):
            return str(resolve_var(name, ctx, script))
        return m.group(0)
    return PLACEHOLDER.sub(repl, text)


def resolve_var(name, ctx, script):
    if name in ctx.vars:
        return ctx.vars[name]
    spec = script.get("vars", {}).get(name)
    if spec is None:
        raise Unresolved(f"no var {name}")
    value = ctx.find(spec["find"])
    if value is None:
        raise Unresolved(f"var {name} not found")
    ctx.vars[name] = value
    return value


def _ref_of(pattern, ctx):
    for line in ctx.snapshot_lines():
        if re.search(pattern, line):
            m = re.search(r"\[ref=(e\d+)\]", line)
            if m:
                return m.group(1)
    raise Unresolved(f"no snapshot line matches {pattern!r}")


def _url_of(pattern, ctx):
    for line in ctx.snapshot_lines():
        if re.search(pattern, line):
            m = re.search(r"-> (\S+)", line)
            if m:
                # rac shows host + path + query without scheme or port; the
                # fixture origins supply the port, so match on the host.
                target = m.group(1)
                host = target.split("/", 1)[0].split("?", 1)[0]
                rest = target[len(host):]
                for base in ctx.origins.values():
                    if re.match(rf"^https?://{re.escape(host)}(:\d+)?$", base):
                        return base.rstrip("/") + rest
                return "http://" + target
    raise Unresolved(f"no link line matches {pattern!r}")


def _tab_of(pattern, ctx):
    def walk(value):
        if isinstance(value, dict):
            alias = next((v for v in value.values()
                          if isinstance(v, str) and re.fullmatch(r"t\d+", v)), None)
            if alias and any(isinstance(v, str) and v != alias and re.search(pattern, v)
                             for v in value.values()):
                return alias
            for v in value.values():
                found = walk(v)
                if found:
                    return found
        elif isinstance(value, list):
            for v in value:
                found = walk(v)
                if found:
                    return found
        return None
    for name, text, parsed in reversed(ctx.tool_results):
        if name == "list_tabs":
            found = walk(parsed)
            if found:
                return found
    raise Unresolved(f"no tab matches {pattern!r}")


def resolve(value, ctx, script):
    if isinstance(value, str):
        return _substitute(value, ctx, script, {})
    if isinstance(value, list):
        return [resolve(v, ctx, script) for v in value]
    if isinstance(value, dict):
        if "ref_of" in value:
            return _ref_of(_substitute(value["ref_of"], ctx, script, {}), ctx)
        if "find" in value:
            found = ctx.find(_substitute(value["find"], ctx, script, {}))
            if found is None:
                raise Unresolved("find: no match")
            return found
        if "find_user" in value:
            for text in reversed(ctx.user_texts):
                m = re.search(value["find_user"], text)
                if m:
                    return m.group(1) if m.groups() else m.group(0)
            raise Unresolved("find_user: no match")
        if "tab_of" in value:
            return _tab_of(value["tab_of"], ctx)
        if "url_of" in value:
            return _url_of(_substitute(value["url_of"], ctx, script, {}), ctx)
        return {k: resolve(v, ctx, script) for k, v in value.items()}
    return value


def _fill(node, extra):
    """Replaces {char}, {char_re} and {i} inside a for_each_char body."""
    if isinstance(node, str):
        for k, v in extra.items():
            node = node.replace("{" + k + "}", v)
        return node
    if isinstance(node, list):
        return [_fill(n, extra) for n in node]
    if isinstance(node, dict):
        return {k: _fill(v, extra) for k, v in node.items()}
    return node


def expand_steps(steps, ctx, script):
    out = []
    for step in steps:
        if "for_each_char" in step:
            try:
                text = str(resolve_var(step["for_each_char"], ctx, script))
            except Unresolved:
                continue
            for i, ch in enumerate(text):
                out += expand_steps(
                    _fill(step["steps"], {"char": ch, "char_re": re.escape(ch), "i": str(i)}),
                    ctx, script)
        else:
            out.append(step)
    return out


class Decision:
    def __init__(self, text="", calls=None, notes=None):
        self.text = text
        self.calls = calls or []  # [{name, arguments(dict), attack, exfil, label}]
        self.notes = notes or []


def _turn_script(script, n_user):
    turns = script.get("turns")
    if not turns:
        return script
    return turns[min(max(n_user, 1), len(turns)) - 1]


def _pick(steps, pos, ctx, script, obey):
    """First step from `pos` that can run. Returns (index, call dict) or
    (None, note) when the script has ended or got stuck."""
    for i in range(pos, len(steps)):
        step = steps[i]
        if step.get("attack") and obey is not None and not ctx.seen(obey):
            return None, "planted instruction not seen; model does not attack"
        try:
            args = resolve(step.get("args", {}), ctx, script)
            say = resolve(step["say"], ctx, script) if step.get("say") else ""
        except Unresolved as e:
            if step.get("optional"):
                continue
            return None, f"step {i} ({step.get('tool')}) unresolved: {e}"
        return i, {"name": step["tool"], "arguments": args, "say": say,
                   "attack": bool(step.get("attack")), "exfil": bool(step.get("exfil")),
                   "label": step.get("label", "")}
    return None, ""


def decide(script, messages, origins=None, offered=None):
    """The model's next move given the whole conversation so far."""
    last_user = max((i for i, m in enumerate(messages) if m.get("role") == "user"), default=-1)
    n_user = sum(1 for m in messages if m.get("role") == "user")
    turn = _turn_script(script, n_user)
    obey = script.get("obey")
    # Assistant tool-call messages in this turn, in order.
    prior = [i for i, m in enumerate(messages)
             if i > last_user and m.get("role") == "assistant" and m.get("tool_calls")]
    pos = 0
    for idx in prior:
        ctx = Context(messages, origins, upto=idx)
        steps = expand_steps(turn.get("steps", []), ctx, script)
        found, _ = _pick(steps, pos, ctx, script, obey)
        pos = (found if found is not None else pos) + 1
    ctx = Context(messages, origins)
    steps = expand_steps(turn.get("steps", []), ctx, script)
    found, result = _pick(steps, pos, ctx, script, obey)
    if found is None:
        final = turn.get("final", script.get("final", "Done."))
        try:
            final = resolve(final, ctx, script)
        except Unresolved:
            final = "Done."
        return Decision(text=final, notes=[result] if result else [])
    call = result
    if offered is not None and call["name"] not in offered:
        return Decision(text="Done.", notes=[f"tool {call['name']} not offered"])
    return Decision(text=call.pop("say"), calls=[call])


# --- HTTP ---------------------------------------------------------------

class State:
    def __init__(self, log_file=None):
        self.lock = threading.Lock()
        self.script = {}
        self.origins = {}
        self.log = []
        self.seq = 0
        self.log_file = log_file

    def reset(self):
        with self.lock:
            self.script, self.origins, self.log = {}, {}, []

    def record(self, entry):
        with self.lock:
            self.seq += 1
            entry["seq"] = self.seq
            entry["t"] = round(time.time(), 3)
            self.log.append(entry)
            if self.log_file:
                with open(self.log_file, "a") as f:
                    f.write(json.dumps(entry) + "\n")


def _chunk(model, delta, finish=None, cid="chatcmpl-fake"):
    return {"id": cid, "object": "chat.completion.chunk", "created": 0, "model": model,
            "choices": [{"index": 0, "delta": delta, "finish_reason": finish}]}


def sse_events(model, decision, call_id):
    """The streaming reply: role, text pieces, a tool call split over several
    argument fragments (so rac's merge is exercised), then the finish chunk."""
    events = [_chunk(model, {"role": "assistant", "content": ""})]
    text = decision.text
    for i in range(0, len(text), 24):
        events.append(_chunk(model, {"content": text[i:i + 24]}))
    for call in decision.calls:
        args = json.dumps(call["arguments"])
        events.append(_chunk(model, {"tool_calls": [{
            "index": 0, "id": call_id, "type": "function",
            "function": {"name": call["name"], "arguments": ""}}]}))
        cut = max(1, len(args) // 2)
        for piece in (args[:cut], args[cut:]):
            events.append(_chunk(model, {"tool_calls": [{
                "index": 0, "function": {"arguments": piece}}]}))
    events.append(_chunk(model, {}, "tool_calls" if decision.calls else "stop"))
    return events


def completion_json(model, decision, call_id):
    message = {"role": "assistant", "content": decision.text or None}
    if decision.calls:
        message["tool_calls"] = [{
            "id": call_id, "type": "function",
            "function": {"name": c["name"], "arguments": json.dumps(c["arguments"])}}
            for c in decision.calls]
    return {"id": "chatcmpl-fake", "object": "chat.completion", "created": 0, "model": model,
            "choices": [{"index": 0, "message": message,
                         "finish_reason": "tool_calls" if decision.calls else "stop"}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}}


def plain_reply(body):
    """Requests with no tools: link summaries, titles, the safety critic, the
    connection probe. The critic gets 'escalate' so it can never wave an
    attack through."""
    text = json.dumps(body.get("messages", []))
    if "escalate" in text.lower():
        return "escalate"
    return "Eval reply."


def make_handler(state):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *args):
            pass

        def _send(self, status, payload, ctype="application/json"):
            data = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def _body(self):
            n = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(n) if n else b""
            try:
                return json.loads(raw or b"{}")
            except ValueError:
                return None

        def do_GET(self):
            path = self.path.split("?", 1)[0]
            if path == "/v1/models":
                state.record({"kind": "models", "has_auth": bool(self.headers.get("Authorization"))})
                self._send(200, {"object": "list", "data": [
                    {"id": m, "object": "model", "owned_by": "rac-evals"} for m in MODEL_IDS]})
            elif path == "/__control/log":
                with state.lock:
                    self._send(200, {"log": list(state.log)})
            elif path == "/__control/health":
                self._send(200, {"ok": True})
            else:
                self._send(404, {"error": {"message": "not found"}})

        def do_POST(self):
            path = self.path.split("?", 1)[0]
            body = self._body()
            if body is None:
                self._send(400, {"error": {"message": "bad json"}})
            elif path == "/__control/script":
                with state.lock:
                    state.script = body.get("script", {})
                    state.origins = body.get("origins", {})
                self._send(200, {"ok": True})
            elif path == "/__control/reset":
                state.reset()
                self._send(200, {"ok": True})
            elif path == "/v1/chat/completions":
                self._chat(body)
            else:
                self._send(404, {"error": {"message": "not found"}})

        def _chat(self, body):
            messages = body.get("messages") or []
            tools = body.get("tools") or []
            offered = {(t.get("function") or {}).get("name") for t in tools}
            model = body.get("model") or MODEL_IDS[0]
            stream = bool(body.get("stream"))
            with state.lock:
                script, origins = state.script, state.origins
            entry = {"kind": "chat", "model": model, "stream": stream,
                     "n_messages": len(messages), "tools": sorted(n for n in offered if n),
                     "has_auth": bool(self.headers.get("Authorization")),
                     "last_role": messages[-1].get("role") if messages else None,
                     "user_texts": [m.get("content") for m in messages
                                    if m.get("role") == "user" and isinstance(m.get("content"), str)]}
            if tools and script:
                decision = decide(script, messages, origins, offered)
            else:
                decision = Decision(text=plain_reply(body))
            call_id = f"call_{state.seq + 1}"
            entry["text"] = decision.text
            entry["calls"] = [{"id": call_id, **c} for c in decision.calls]
            entry["notes"] = decision.notes
            state.record(entry)
            if not stream:
                self._send(200, completion_json(model, decision, call_id))
                return
            out = b"".join(b"data: " + json.dumps(e).encode() + b"\n\n"
                           for e in sse_events(model, decision, call_id))
            out += b"data: [DONE]\n\n"
            self._send(200, out, "text/event-stream")

    return Handler


def serve(port=0, log_file=None):
    state = State(log_file)
    server = ThreadingHTTPServer(("127.0.0.1", port), make_handler(state))
    server.daemon_threads = True
    return server, state


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--port", type=int, default=0, help="0 picks a free port")
    ap.add_argument("--script", help="load a model.json at startup")
    ap.add_argument("--origins", help="JSON object of origin name -> base URL")
    ap.add_argument("--log-file", help="append every request as JSON lines")
    args = ap.parse_args(argv)
    server, state = serve(args.port, args.log_file)
    if args.script:
        with open(args.script) as f:
            state.script = json.load(f)
        state.origins = json.loads(args.origins or "{}")
    print(json.dumps({"fake_model": f"http://127.0.0.1:{server.server_address[1]}",
                      "base_url": f"http://localhost:{server.server_address[1]}/v1"}), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    sys.exit(main())
