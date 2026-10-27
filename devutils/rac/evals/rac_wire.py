# Copyright 2026 The rac Authors
# SPDX-License-Identifier: GPL-3.0-or-later
"""A Python port of the parts of rac's Custom (OpenAI-compatible) provider that
read a model server's replies, so tests can prove the fake model speaks what
rac actually parses without a browser.

Ported from chrome/browser/rac/ai/{sse_parser,chat_protocol,chat_stream}.cc.
If those change, change this file too. Quirks kept on purpose:

* A chunk whose `finish_reason` is non-empty ends the stream at once; a later
  `[DONE]` is never read.
* Tool call deltas need an `index` in 0..31. `id`, `name` and `arguments` are
  concatenated per index; the finished call needs a non-empty, unique id, a
  non-empty name, JSON-object arguments (empty means `{}`), and a name rac
  offered in the request.
* The request is POST {base}/chat/completions with `stream: true`,
  `parallel_tool_calls: false` when tools are offered, and an
  `Authorization: Bearer <key>` header.
"""

import json
from dataclasses import dataclass, field

MAX_PENDING_BYTES = 1024 * 1024


class SseParser:
    """Port of rac::ai::SseParser: events are `data:` lines ended by a blank line."""

    def __init__(self):
        self.line = ""
        self.pending_type = ""
        self.pending_data = ""
        self.has_data = False
        self.last_was_cr = False
        self.in_bom_check = True
        self.overflowed = False

    def feed(self, chunk: str):
        events = []
        if self.overflowed:
            return events
        for c in chunk:
            if self.in_bom_check:
                bom = "﻿"
                if c == bom:
                    self.in_bom_check = False
                    continue
                self.in_bom_check = False
            if c == "\n" and self.last_was_cr:
                self.last_was_cr = False
                continue
            self.last_was_cr = c == "\r"
            if c in "\r\n":
                self._process_line(self.line, events)
                self.line = ""
                continue
            self.line += c
            if len(self.line) + len(self.pending_data) > MAX_PENDING_BYTES:
                self.overflowed = True
                return events
        return events

    def _process_line(self, line, events):
        if not line:
            if self.has_data:
                events.append((self.pending_type, self.pending_data))
            self.pending_type = ""
            self.pending_data = ""
            self.has_data = False
            return
        if line[0] == ":":
            return
        field_name, value = line, ""
        if ":" in line:
            field_name, value = line.split(":", 1)
            if value.startswith(" "):
                value = value[1:]
        if field_name == "data":
            if self.has_data:
                self.pending_data += "\n"
            self.pending_data += value
            self.has_data = True
        elif field_name == "event":
            self.pending_type = value


@dataclass
class ToolCall:
    id: str = ""
    name: str = ""
    arguments: str = ""


@dataclass
class StreamUpdate:
    text_delta: str = ""
    tool_deltas: list = field(default_factory=list)  # (index, id, name, arguments)
    done: bool = False
    error: str = ""


def _error_from(d):
    err = d.get("error")
    if err is None:
        return None
    if isinstance(err, dict):
        msg = err.get("message")
        return msg if isinstance(msg, str) else "The provider reported an error."
    if isinstance(err, str):
        return err
    return "The provider reported an error."


def decode_openai(data: str):
    """Port of DecodeOpenAi for one SSE event's data."""
    updates = []
    if data == "[DONE]":
        return [StreamUpdate(done=True)]
    try:
        d = json.loads(data)
    except ValueError:
        return updates
    if not isinstance(d, dict):
        return updates
    error = _error_from(d)
    if error is not None:
        return [StreamUpdate(error=error)]
    choices = d.get("choices")
    if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
        return updates
    choice = choices[0]
    delta = choice.get("delta")
    if isinstance(delta, dict):
        calls = delta.get("tool_calls")
        if isinstance(calls, list):
            update = StreamUpdate()
            for call in calls:
                if not isinstance(call, dict):
                    continue
                index = call.get("index")
                index = index if isinstance(index, int) and not isinstance(index, bool) else -1
                function = call.get("function") if isinstance(call.get("function"), dict) else {}
                update.tool_deltas.append((
                    index,
                    call["id"] if isinstance(call.get("id"), str) else "",
                    function["name"] if isinstance(function.get("name"), str) else "",
                    function["arguments"] if isinstance(function.get("arguments"), str) else "",
                ))
            updates.append(update)
        content = delta.get("content")
        if isinstance(content, str) and content:
            updates.append(StreamUpdate(text_delta=content))
    finish = choice.get("finish_reason")
    if isinstance(finish, str) and finish:
        updates.append(StreamUpdate(done=True))
    return updates


class ProtocolError(Exception):
    pass


def merge_tool_call_deltas(calls: dict, deltas):
    for index, call_id, name, arguments in deltas:
        if index < 0 or index >= 32:
            raise ProtocolError("Invalid tool call index.")
        call = calls.setdefault(index, ToolCall())
        call.id += call_id
        call.name += name
        call.arguments += arguments
        if len(call.id) > 200 or len(call.name) > 100 or len(call.arguments) > 64 * 1024:
            raise ProtocolError("The provider's tool call was too large.")


def complete_tool_calls(calls: dict, offered_names):
    ids = set()
    complete = []
    for index in sorted(calls):
        call = calls[index]
        if not call.arguments:
            call.arguments = "{}"
        try:
            args = json.loads(call.arguments)
        except ValueError:
            args = None
        if not call.id or not call.name or call.id in ids or not isinstance(args, dict):
            raise ProtocolError("The provider returned a malformed tool call.")
        ids.add(call.id)
        if call.name not in offered_names:
            raise ProtocolError("The provider requested an unavailable tool.")
        complete.append(call)
    return complete


@dataclass
class Reply:
    text: str = ""
    tool_calls: list = field(default_factory=list)
    error: str = ""


def read_stream(body: str, offered_names, chunk_size: int = 7) -> Reply:
    """Decodes a whole SSE body the way ChatStream + the tool loop do, feeding
    it in small pieces so chunk boundaries can't hide a bug."""
    parser = SseParser()
    reply = Reply()
    calls = {}
    for i in range(0, len(body), chunk_size):
        for _type, data in parser.feed(body[i:i + chunk_size]):
            for update in decode_openai(data):
                if update.error:
                    reply.error = update.error
                    return reply
                reply.text += update.text_delta
                try:
                    merge_tool_call_deltas(calls, update.tool_deltas)
                except ProtocolError as e:
                    reply.error = str(e)
                    return reply
                if update.done:
                    try:
                        reply.tool_calls = complete_tool_calls(calls, offered_names)
                    except ProtocolError as e:
                        reply.error = str(e)
                    return reply
    if parser.overflowed:
        reply.error = "The reply was malformed."
        return reply
    try:
        reply.tool_calls = complete_tool_calls(calls, offered_names)
    except ProtocolError as e:
        reply.error = str(e)
    return reply


def build_chat_body(model, messages, tools, system_prompt="", stream=True):
    """What BuildChatRequest sends for an OpenAI-compatible provider."""
    out_messages = []
    if system_prompt:
        out_messages.append({"role": "system", "content": system_prompt})
    out_messages += messages
    body = {"model": model, "stream": stream, "messages": out_messages}
    if tools:
        body["tools"] = [{"type": "function", "function": t} for t in tools]
        body["parallel_tool_calls"] = False
    return body
