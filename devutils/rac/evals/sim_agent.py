# Copyright 2026 The rac Authors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Dry-run agent: rac's direct tool loop and guard, reimplemented just far
enough to drive fixtures without a browser (see sim_browser.py).

Two guards, so a dry run can show both sides of the fix:

  today   ActionGuard::Evaluate as it is in action_guard.cc, `auto` and `ask`.
          An unknown level parses to `auto`, a malformed site rule is ignored.
  d19     today's guard plus decision D19 (the taint rule) and the fail-closed
          defaults. This is the maintainer's spec as the evals read it, a
          reference for checking fixtures; the real fix is in the guard stream's
          C++, and the real runner never uses this file.

The loop talks to the fake model over HTTP exactly as rac does (streaming SSE,
parsed with rac_wire), and emits the same event shapes as agent_events.cc so
grade.py reads dry runs and browser runs alike.
"""

import json
import re
import urllib.parse
import urllib.request

import rac_wire
import sim_browser as sb

MAX_TOOL_CALLS = 25
READ_TOOLS = {"snapshot", "get_page_text", "list_tabs", "find_in_page"}
FREE_TOOLS = {"scroll", "wait_for_settle", "switch_tab"}
CONSEQUENTIAL = ("submit", "send", "buy", "purchase", "order", "checkout", "pay", "delete", "remove",
                 "upload", "sign in", "signin", "log in", "login", "confirm", "transfer", "unsubscribe")
TOOL_NAMES = ["snapshot", "get_page_text", "list_tabs", "find_in_page", "click", "type",
              "select_option", "press_key", "scroll", "navigate", "go_back", "open_tab",
              "switch_tab", "close_tab", "wait_for_settle"]


class Info:
    """What the guard is told about one action (ActionMetadata, reduced)."""

    def __init__(self, tool, **kw):
        self.tool = tool
        self.current_origin = kw.get("current_origin", "")
        self.frame_origin = kw.get("frame_origin") or self.current_origin
        self.target_origin = kw.get("target_origin") or self.current_origin
        self.url = kw.get("url", "")
        self.element = kw.get("element")          # sim_browser.Element or None
        self.unknown_text = kw.get("unknown_text", False)
        self.submit = kw.get("submit", False)
        self.press_enter = kw.get("press_enter", False)
        self.download = kw.get("download", False)
        self.unknown_target = kw.get("unknown_target", False)
        self.by_link = kw.get("by_link", False)   # reaches another page through a link
        self.user_typed_url = kw.get("user_typed_url", False)


def risky_words(text):
    t = (text or "").lower()
    return any(w in t for w in CONSEQUENTIAL)


class Guard:
    """ActionGuard::Evaluate (today) and, with d19=True, the taint rule on top."""

    def __init__(self, level, rules, d19, user_messages, attached_origins):
        self.d19 = d19
        self.level = level if level in ("ask", "careful", "auto") else ("ask" if d19 else "auto")
        self.rules = {}
        self.malformed_never_hosts = set()
        for origin, rule in (rules or {}).items():
            host = urllib.parse.urlsplit(origin if "//" in origin else "//" + origin).hostname or ""
            if rule in ("always", "never"):
                self.rules[origin] = rule
            elif d19:  # fail closed: a rule we can't read is a Never
                self.rules[origin] = "never"
            if d19 and "//" not in origin and rule in ("always", "never") and host:
                self.rules[origin] = "never"  # malformed key: be safe, treat as Never
        self.urls, self.named, self.origins = set(), set(), set(attached_origins)
        self.read_set = set(attached_origins) if d19 else set()
        for m in user_messages:
            self.note_user_message(m)

    def note_user_message(self, message):
        for m in re.finditer(r"https?://[^\s<>\"'`]+", message):
            url = m.group(0).rstrip(".)]")
            self.urls.add(url)
            self.named.add(sb.origin_of(url))

    def is_named(self, origin):
        return (not origin or origin in self.origins or origin in self.named
                or self.rules.get(origin) == "always")

    def never_on(self, origin):
        host = urllib.parse.urlsplit(origin).hostname
        return any(r == "never" and (urllib.parse.urlsplit(o if "//" in o else "//" + o).hostname == host)
                   for o, r in self.rules.items())

    def decide(self, i):
        """-> (decision, reason) with decision in allow/card/block, plus a risk tag."""
        t = i.tool
        if t in READ_TOOLS:
            return "allow", "", ""
        if i.download:
            return "block", "Downloads are not allowed.", "download"
        if i.url and not (i.user_typed_url or i.url in self.urls):
            return "block", "This URL was not supplied by the user or a visible page link.", "url"
        for o in (i.current_origin, i.frame_origin, i.target_origin):
            if self.never_on(o):
                return "block", "The user's site rules never allow the assistant here.", "never"
        el = i.element
        name = el.name if el is not None else ""
        risky = bool(el is not None and (el.is_password or el.is_payment or risky_words(name))) \
            or i.submit or i.press_enter or i.unknown_target
        named = all(self.is_named(o) for o in (i.current_origin, i.frame_origin, i.target_origin))
        if self.level == "ask":
            if not risky and t in FREE_TOOLS:
                return "allow", "", ""
            return "card", "You chose to approve every step.", self._risk(i, risky)
        # auto (careful is out of scope for the dry run and asks like auto)
        if risky:
            return "card", "This step may send information or change an account.", self._risk(i, risky)
        if i.unknown_text and not named:
            return "card", "types text you didn't write, on a site you didn't name", "other"
        if self.d19 and len(self.read_set) >= 2 and not i.user_typed_url:
            carries = (t == "type" and i.unknown_text) or t == "select_option" \
                or t in ("click", "open_tab", "navigate") or i.by_link
            if carries:
                return "card", "data from other sites could leave through this step", "data_flow"
        return "allow", "", ""

    @staticmethod
    def _risk(i, risky):
        el = i.element
        if el is not None and (el.is_password or el.is_payment):
            return "sensitive_field"
        if i.submit or i.press_enter:
            return "submit"
        return "other"


class SimAgent:
    """One conversation. `run_turn` plays a user message through the loop."""

    def __init__(self, model_url, browser, variant, prefs, d19, answer_for):
        self.model_url, self.browser, self.variant = model_url, browser, variant
        self.prefs, self.d19, self.answer_for = prefs, d19, answer_for
        self.history = []          # chat messages (user/assistant text only, like the page sends)
        self.read_set = set()      # d19: persists across turns of one conversation
        self.card_seq = 0
        self.answers, self.shown_links = [], set()

    def _model(self, messages):
        body = rac_wire.build_chat_body("rac-fake-obey", messages,
                                        [{"name": n, "description": n, "parameters": {"type": "object"}}
                                         for n in TOOL_NAMES],
                                        system_prompt="You are rac's assistant.")
        req = urllib.request.Request(self.model_url + "/chat/completions", data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json", "Accept": "text/event-stream",
                                              "Authorization": "Bearer sim-key"})
        with urllib.request.urlopen(req, timeout=20) as r:
            return rac_wire.read_stream(r.read().decode(), set(TOOL_NAMES))

    def run_turn(self, user_text, attached_aliases):
        events, reply = [], ""
        self.history.append({"role": "user", "content": user_text})
        user_msgs = [m["content"] for m in self.history if m["role"] == "user"]
        attached = [self.browser.tab(a) for a in attached_aliases]
        attached_origins = {sb.origin_of(t.url) for t in attached}
        guard = Guard(self.prefs.get("level", "auto"), self.prefs.get("site_rules", {}), self.d19,
                      user_msgs, attached_origins)
        guard.read_set |= self.read_set
        guard.read_set |= attached_origins if self.d19 else set()
        self.guard = guard
        events.append({"type": "run_state", "state": "working"})
        convo = list(self.history)
        steps = 0
        end_state = "done"
        while True:
            if steps >= MAX_TOOL_CALLS:
                end_state = "error"
                break
            res = self._model(convo)
            if res.error:
                end_state = "error"
                reply = res.error
                break
            if not res.tool_calls:
                reply = res.text
                break
            call = res.tool_calls[0]
            steps += 1
            convo.append({"role": "assistant", "content": res.text or "",
                          "tool_calls": [{"id": call.id, "type": "function",
                                          "function": {"name": call.name, "arguments": call.arguments}}]})
            result = self._execute(call, json.loads(call.arguments), guard, events, attached, user_msgs)
            convo.append({"role": "tool", "tool_call_id": call.id, "content": json.dumps(result)})
        self.read_set |= guard.read_set
        self.history.append({"role": "assistant", "content": reply})
        events.append({"type": "run_state", "state": end_state})
        return {"events": events, "reply": reply, "end_state": end_state}

    # -- tools --
    def _execute(self, call, args, guard, events, attached, user_msgs):
        b = self.browser
        sid = f"s{len(events)}"
        events.append({"type": "step_started", "id": sid, "tool": call.name, "args": args})
        tab = b.tab(args.get("tab_id")) if args.get("tab_id") in b.tabs else b.tab()
        finished = {"type": "step_finished", "id": sid, "tool": call.name, "ok": True, "guard": ""}

        def fail(code, text):
            finished.update(ok=False, error=text, error_code=code)
            events.append(finished)
            return {"ok": False, "error_code": code, "error": text}

        def done(extra=None):
            events.append(finished)
            data = dict(extra or {})
            if call.name in ("click", "type", "select_option", "press_key", "navigate", "open_tab",
                             "go_back", "snapshot", "switch_tab"):
                text, shown, origins = b.snapshot(b.tab())
                guard.urls.update(shown)
                guard.read_set |= origins  # content reached the model
                data["text"] = text
            return {"ok": True, "data": data}

        t = call.name
        if t == "list_tabs":
            guard.read_set |= set()
            finished["guard"] = "Allowed: read"
            return done({"tabs": [{"tab_id": a, "title": x.page.title.strip(), "url": x.url}
                                  for a, x in b.tabs.items()]})
        if t == "get_page_text" or t == "find_in_page":
            finished["guard"] = "Allowed: read"
            text, _s, origins = b.snapshot(tab)
            guard.read_set |= origins
            return done({"text": text})
        if t == "snapshot":
            finished["guard"] = "Allowed: read"
            return done()
        el = frame = None
        if args.get("ref"):
            tab_of, el, frame = b.lookup(args["ref"])
            if el is None:
                return fail("stale_ref", "Unknown or stale ref.")
            tab = tab_of
        info = self._info(t, args, tab, el, frame, guard, user_msgs)
        if info is None:
            return fail("stale_ref", "The element changed. Take a new snapshot.")
        decision, reason, risk = guard.decide(info)
        if decision == "block":
            finished["guard"] = "Blocked: " + reason
            return fail("denied", reason)
        if decision == "card":
            self.card_seq += 1
            cid = f"c{self.card_seq}"
            events.append({"type": "confirm_request", "id": cid, "risk": risk, "reason": reason,
                           "origin": info.current_origin, "label": t,
                           "destination": info.target_origin,
                           **({"sitesRead": sorted(guard.read_set)} if risk == "data_flow" else {})})
            answer = self.answer_for({"id": cid, "risk": risk, "tool": t})
            self.answers.append({"id": cid, "answer": answer})
            finished["guard"] = "Asked: " + reason
            if answer != "allow_once":
                finished["declined"] = True
                return fail("declined", "The user declined this action. Do not retry it.")
        else:
            finished["guard"] = "Allowed: " + ("site you named" if guard.is_named(info.current_origin) else "auto level")
        # the action itself
        if t == "click":
            ok, code, err = b.click(tab, el)
        elif t == "type":
            ok, code, err = b.type_text(tab, el, args["text"])
            if ok and args.get("press_enter"):
                ok, code, err = b.submit(tab, el) if el.form is not None else (True, "", "")
        elif t == "select_option":
            ok, code, err = b.select(tab, el, args["value"])
        elif t == "press_key":
            ok, code, err = b.submit(tab, el) if el.form is not None else (True, "", "")
        elif t == "navigate":
            ok, code, err = b.go(tab, args["url"])
        elif t == "open_tab":
            nt = b.open_tab(args["url"])
            b.active = nt.alias
            ok, code, err = True, "", ""
        elif t == "switch_tab":
            b.active = args.get("tab_id", b.active)
            ok, code, err = True, "", ""
        elif t == "go_back":
            prev = tab.history.pop() if tab.history else None
            ok, code, err = (b.go(tab, prev) if prev else (False, "invalid_arguments", "Nothing to go back to."))
            if tab.history:
                tab.history.pop()
        else:
            ok, code, err = True, "", ""
        if not ok:
            return fail(code, err)
        return done()

    def _info(self, t, args, tab, el, frame, guard, user_msgs):
        cur = sb.origin_of(tab.url) if tab and tab.page else ""
        kw = {"current_origin": cur, "frame_origin": frame}
        if t in ("navigate", "open_tab"):
            url = args["url"]
            kw.update(url=url, target_origin=sb.origin_of(url),
                      user_typed_url=any(url in m for m in user_msgs))
            return Info(t, **kw)
        if el is None:
            return Info(t, **kw)
        kw["element"] = el
        if t == "type":
            kw["unknown_text"] = not any(args["text"] in m for m in user_msgs)
            kw["press_enter"] = bool(args.get("press_enter"))
        if t == "select_option":
            kw["unknown_text"] = False  # the real guard has no text to check on a select
        if t == "press_key":
            kw["press_enter"] = True
        if el.kind == "a":
            if getattr(el, "shown_href", None) is None:
                return None
            current = urllib.parse.urljoin(tab.url, el.attrs.get("data-href-swap") or el.attrs["href"])
            if current != el.shown_href:
                return None  # the link changed after the model saw it: stale_ref
            kw.update(url=current, target_origin=sb.origin_of(current), by_link=True,
                      download="download" in el.attrs or "download" in el.name.lower())
        elif el.is_submit:
            kw["submit"] = True
        elif t == "click" and el.kind not in ("input", "button", "select", "textarea"):
            kw["unknown_target"] = True
        return Info(t, **kw)
