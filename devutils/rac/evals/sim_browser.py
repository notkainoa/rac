# Copyright 2026 The rac Authors
# SPDX-License-Identifier: GPL-3.0-or-later
"""A tiny stand-in for the browser, used only by `run.py --dry-run` and the
unit tests. It fetches pages over HTTP from the fixture server, runs the
data-* behaviors from eval_js.py in Python, and prints snapshots in rac's line
format (snapshot_serializer.cc). It is not a browser and proves nothing about
rac; it proves the fixtures contain a working attack and that the runner and
grader plumbing agree with each other.
"""

import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser

SKIP = {"script", "style", "noscript", "head", "title"}
TEXTBOXES = {"text", "search", "email", "tel", "url", "number", ""}


def fetch(url, data=None, timeout=10):
    """GET or POST; returns (status, headers, final_url, text). 4xx/5xx are returned."""
    req = urllib.request.Request(url, data=data, method="POST" if data is not None else "GET")
    if data is not None:
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, dict(r.headers), r.geturl(), r.read(512 * 1024).decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), url, e.read(64 * 1024).decode("utf-8", "replace")


def origin_of(url):
    p = urllib.parse.urlsplit(url)
    return f"{p.scheme}://{p.netloc}" if p.scheme in ("http", "https") else "null"


class Element:
    def __init__(self, kind, attrs, form=None, frame=None):
        self.kind, self.attrs, self.form, self.frame = kind, attrs, form, frame
        self.text = ""
        self.value = attrs.get("value", "")
        self.options = []
        self.ref = None

    @property
    def name(self):
        return (self.attrs.get("aria-label") or self.text.strip() or self.attrs.get("placeholder")
                or self.attrs.get("title") or self.attrs.get("name") or self.attrs.get("id") or self.kind)

    @property
    def is_password(self):
        return self.attrs.get("type", "").lower() == "password"

    @property
    def is_payment(self):
        return self.attrs.get("autocomplete", "").lower().startswith("cc-")

    @property
    def is_submit(self):
        t = self.attrs.get("type", "").lower()
        return (self.kind == "input" and t in ("submit", "image")) or \
               (self.kind == "button" and t in ("", "submit") and self.form is not None)


class Page(HTMLParser):
    def __init__(self, url, html, depth=0):
        super().__init__(convert_charrefs=True)
        self.url, self.title, self.depth = url, "", depth
        self.elements, self.texts, self.forms, self.iframes = [], [], [], []
        self.body_attrs = {}
        self._stack, self._form, self._skip, self._open, self._in_title = [], None, 0, [], False
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        a = {k: (v if v is not None else "") for k, v in attrs}
        if tag in SKIP:
            self._skip += 1
            self._in_title = tag == "title"
            return
        if tag == "body":
            self.body_attrs = a
        elif tag == "form":
            self._form = len(self.forms)
            self.forms.append({"action": a.get("action", ""), "method": a.get("method", "get").lower()})
        elif tag == "a" and "href" in a:
            self._open.append(Element("a", a))
            self.elements.append(self._open[-1])
        elif tag == "input":
            self.elements.append(Element("input", a, self._form))
        elif tag == "textarea":
            self._open.append(Element("textarea", a, self._form))
            self.elements.append(self._open[-1])
        elif tag == "button":
            self._open.append(Element("button", a, self._form))
            self.elements.append(self._open[-1])
        elif tag == "select":
            self._open.append(Element("select", a, self._form))
            self.elements.append(self._open[-1])
        elif tag == "option" and self._open and self._open[-1].kind == "select":
            self._open.append(Element("option", a))
        elif tag == "iframe" and a.get("src"):
            self.iframes.append(urllib.parse.urljoin(self.url, a["src"]))
            self.elements.append(Element("iframe", a))

    def handle_endtag(self, tag):
        if tag in SKIP:
            self._skip = max(0, self._skip - 1)
            self._in_title = False
        elif tag == "form":
            self._form = None
        elif tag in ("a", "textarea", "button", "select") and self._open:
            self._open.pop()
        elif tag == "option" and self._open and self._open[-1].kind == "option":
            opt = self._open.pop()
            sel = self._open[-1]
            sel.options.append((opt.attrs.get("value", opt.text.strip()), opt.text.strip(),
                                "selected" in opt.attrs))

    def handle_data(self, data):
        if self._in_title:
            self.title += data
            return
        if self._skip:
            return
        for el in self._open:
            if el.kind != "select":
                el.text += data
        if data.strip() and not any(e.kind in ("a", "button", "option", "textarea") for e in self._open):
            self.texts.append(data.strip())
            self.elements.append(Element("text", {}))
            self.elements[-1].text = data.strip()


class Tab:
    def __init__(self, alias):
        self.alias, self.url, self.page, self.frames, self.history = alias, "", None, [], []

    def load(self, url, data=None):
        status, headers, final, html = fetch(url, data)
        if status == 204:
            return status, headers
        self.history.append(self.url) if self.url else None
        self.url = final
        self.page = Page(final, html)
        self.frames = [Page(u, fetch(u)[3], depth=1) for u in self.page.iframes[:3]]
        return status, headers

    def all_elements(self):
        """(element, frame_origin or None) in document order, frames after the page."""
        out = [(e, None) for e in self.page.elements]
        for fr in self.frames:
            out += [(e, origin_of(fr.url)) for e in fr.elements]
        return out


class SimBrowser:
    def __init__(self):
        self.tabs, self.next_alias, self.ref_counter, self.refs = {}, 1, 0, {}
        self.active = None

    def open_tab(self, url):
        tab = Tab(f"t{self.next_alias}")
        self.next_alias += 1
        self.tabs[tab.alias] = tab
        tab.load(url)
        self.active = self.active or tab.alias
        return tab

    def tab(self, alias=None):
        return self.tabs[alias or self.active]

    # -- snapshot --
    def _ref_for(self, tab, el):
        if el.ref is None:
            self.ref_counter += 1
            el.ref = f"e{self.ref_counter}"
            self.refs[el.ref] = (tab.alias, el)
        return el.ref

    def snapshot(self, tab):
        """Wrapped page text in rac's format, plus the link URLs shown."""
        lines, shown = [], []
        for el, frame in tab.all_elements():
            prefix = f"[frame {frame}] " if frame else ""
            if el.kind == "text":
                lines.append(f'- text "{el.text[:300]}"')
            elif el.kind == "iframe":
                lines.append("- iframe")
            elif el.kind == "a":
                href = urllib.parse.urljoin(tab.url, el.attrs["href"])
                u = urllib.parse.urlsplit(href)
                target = u.hostname + u.path + ("?" + u.query if u.query else "")
                el.shown_href = href
                shown.append(href)
                lines.append(f'{prefix}- link "{el.name}" [ref={self._ref_for(tab, el)}] -> {target}')
            elif el.kind in ("input", "textarea"):
                t = el.attrs.get("type", "").lower()
                if t == "hidden":
                    continue
                ref = self._ref_for(tab, el)
                if el.is_submit:
                    lines.append(f'{prefix}- button "{el.name}" [ref={ref}] [submit]')
                elif t == "checkbox":
                    lines.append(f'{prefix}- checkbox "{el.name}" [ref={ref}] [unchecked]')
                else:
                    shown_value = "[redacted]" if (el.is_password or el.is_payment) else el.value
                    lines.append(f'{prefix}- textbox "{el.name}" [ref={ref}]' +
                                 (f": {shown_value}" if shown_value else ""))
            elif el.kind == "button":
                ref = self._ref_for(tab, el)
                lines.append(f'{prefix}- button "{el.name}" [ref={ref}]' + (" [submit]" if el.is_submit else ""))
            elif el.kind == "select":
                opts = "|".join(("*" if sel else "") + (label or val) for val, label, sel in el.options[:8])
                lines.append(f'{prefix}- combobox "{el.name}" [ref={self._ref_for(tab, el)}]: [{opts}]')
        origin = origin_of(tab.url)
        text = (f"<<<page nonce=simnonce origin={origin}>>>\nTitle: {tab.page.title.strip()}\n"
                f"URL: {tab.url}\n" + "\n".join(lines) + "\n<<<end nonce=simnonce>>>")
        origins = {origin} | {origin_of(f.url) for f in tab.frames}
        return text, shown, origins

    # -- element lookup --
    def lookup(self, ref):
        if ref not in self.refs:
            return None, None, None
        alias, el = self.refs[ref]
        tab = self.tabs[alias]
        frame = next((fo for e, fo in tab.all_elements() if e is el), None)
        return tab, el, frame

    # -- actions; each returns (ok, error_code, error) and may change the tab --
    def click(self, tab, el):
        if el.kind == "a":
            href = el.attrs.get("data-href-swap") or el.attrs["href"]  # the swap has happened by click time
            return self.go(tab, urllib.parse.urljoin(tab.url, href))
        if el.is_submit:
            return self.submit(tab, el)
        return True, "", ""

    def go(self, tab, url):
        tab.load(url)
        return True, "", ""

    def type_text(self, tab, el, text):
        el.value = text
        self._beacon(tab, el, text)
        return True, "", ""

    def select(self, tab, el, value):
        if el.options and value not in [v for v, _l, _s in el.options]:
            return False, "invalid_arguments", "No such option."
        el.value = value
        self._beacon(tab, el, value)
        return True, "", ""

    def _beacon(self, tab, el, value):
        tpl = el.attrs.get("data-beacon")
        if tpl:  # the page's own script, running on the input event
            fetch(tpl.replace("${value}", urllib.parse.quote(value, safe="")))

    def submit(self, tab, el):
        page = tab.page if any(el is e for e in tab.page.elements) else None
        frame_page = None
        if page is None:
            frame_page = next((f for f in tab.frames if any(el is e for e in f.elements)), None)
        owner = page or frame_page
        form = owner.forms[el.form] if el.form is not None else {"action": "", "method": "get"}
        fields = {}
        for e in owner.elements:
            if e.form == el.form and e.kind in ("input", "textarea", "select") and e.attrs.get("name"):
                if e.attrs.get("type", "").lower() in ("submit", "image", "checkbox"):
                    continue
                fields[e.attrs["name"]] = e.value
        if el.attrs.get("name"):
            fields[el.attrs["name"]] = el.attrs.get("value", "")
        target = urllib.parse.urljoin(owner.url, form["action"] or owner.url)
        body = urllib.parse.urlencode(fields)
        if form["method"] == "post":
            tab.load(target, body.encode())
        else:
            tab.load(target.split("?", 1)[0] + "?" + body)
        return True, "", ""
