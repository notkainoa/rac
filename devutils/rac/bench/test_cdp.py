# Copyright 2026 The rac Authors
# SPDX-License-Identifier: GPL-3.0-or-later
import base64
import hashlib
import json
import socket
import struct
import threading
import time
import unittest

import cdp


def server_frame(text, opcode=0x1, fin=True):
    data = text.encode() if isinstance(text, str) else text
    head = bytes([(0x80 if fin else 0) | opcode])
    n = len(data)
    if n < 126:
        head += bytes([n])
    elif n < 65536:
        head += bytes([126]) + struct.pack(">H", n)
    else:
        head += bytes([127]) + struct.pack(">Q", n)
    return head + data


def read_client_raw(conn):
    def need(n):
        buf = b""
        while len(buf) < n:
            chunk = conn.recv(n - len(buf))
            if not chunk:
                raise EOFError
            buf += chunk
        return buf
    b0, b1 = need(2)
    n = b1 & 0x7F
    if n == 126:
        n = struct.unpack(">H", need(2))[0]
    elif n == 127:
        n = struct.unpack(">Q", need(8))[0]
    assert b1 & 0x80, "client frames must be masked"
    mask = need(4)
    payload = bytes(b ^ mask[i % 4] for i, b in enumerate(need(n)))
    return b0 & 0x0F, payload


def read_client_frame(conn):
    opcode, payload = read_client_raw(conn)
    return payload.decode() if opcode == 0x1 else None  # control frames carry no message


class FakeBrowser:
    """A one-connection WebSocket server that answers CDP-style messages."""

    def __init__(self, handler):
        self.sock = socket.socket()
        self.sock.bind(("127.0.0.1", 0))
        self.sock.listen(1)
        self.port = self.sock.getsockname()[1]
        self.handler = handler
        self.controls = []
        threading.Thread(target=self.run, daemon=True).start()

    def run(self):
        conn, _ = self.sock.accept()
        head = b""
        while b"\r\n\r\n" not in head:
            head += conn.recv(4096)
        self.head = head
        key = [l.split(b": ")[1] for l in head.split(b"\r\n")
               if l.lower().startswith(b"sec-websocket-key")][0]
        accept = base64.b64encode(hashlib.sha1(key + cdp.GUID.encode()).digest())
        conn.sendall(b"HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\n"
                     b"Connection: Upgrade\r\n"
                     b"Sec-WebSocket-Accept: " + accept + b"\r\n\r\n")
        try:
            while True:
                opcode, payload = read_client_raw(conn)
                if opcode == 0x1:
                    self.handler(conn, json.loads(payload.decode()))
                else:
                    self.controls.append((opcode, payload))
        except (EOFError, OSError):
            pass
        finally:
            conn.close()
            self.sock.close()


class CdpTest(unittest.TestCase):
    def connect(self, handler):
        browser = self.browser = FakeBrowser(handler)
        client = cdp.Cdp(f"ws://127.0.0.1:{browser.port}/devtools/browser/x")
        self.addCleanup(client.close)
        return client

    def test_call_returns_the_result_and_buffers_events_that_arrive_first(self):
        def handler(conn, msg):
            conn.sendall(server_frame(json.dumps({"method": "Page.loadEventFired", "params": {}})))
            conn.sendall(server_frame(json.dumps({"id": msg["id"], "result": {"echo": msg["method"]}})))
        client = self.connect(handler)
        self.assertEqual(client.call("Browser.getVersion"), {"echo": "Browser.getVersion"})
        self.assertEqual([e["method"] for e in client.drain_events()], ["Page.loadEventFired"])
        self.assertEqual(client.drain_events(), [])

    def test_errors_raise_and_session_ids_are_forwarded(self):
        seen = []

        def handler(conn, msg):
            seen.append(msg)
            reply = {"id": msg["id"], "error": {"message": "nope"}} if msg["method"] == "Bad" \
                else {"id": msg["id"], "result": {}}
            conn.sendall(server_frame(json.dumps(reply)))
        client = self.connect(handler)
        with self.assertRaises(cdp.CdpError):
            client.call("Bad")
        client.call("Runtime.evaluate", {"expression": "1"}, session_id="S1")
        self.assertEqual(seen[1]["sessionId"], "S1")

    def test_wait_event_matches_method_and_session_and_sees_buffered_events(self):
        def handler(conn, msg):
            conn.sendall(server_frame(json.dumps(
                {"method": "Page.loadEventFired", "sessionId": "S2", "params": {"t": 1}})))
            conn.sendall(server_frame(json.dumps(
                {"method": "Page.loadEventFired", "sessionId": "S1", "params": {"t": 2}})))
            conn.sendall(server_frame(json.dumps({"id": msg["id"], "result": {}})))
        client = self.connect(handler)
        client.call("Page.enable", session_id="S1")
        # Both events were buffered during the call; S1's is returned even
        # though S2's arrived first, and S2's stays buffered for later.
        self.assertEqual(client.wait_event("Page.loadEventFired", "S1"), {"t": 2})
        self.assertEqual(client.wait_event("Page.loadEventFired", "S2"), {"t": 1})
        self.assertEqual(client.drain_events(), [])

    def test_wait_event_times_out(self):
        def handler(conn, msg):
            conn.sendall(server_frame(json.dumps({"id": msg["id"], "result": {}})))
        client = self.connect(handler)
        with self.assertRaises(cdp.CdpError):
            client.wait_event("Page.loadEventFired", timeout=0.2)

    def test_large_and_fragmented_messages_and_pings(self):
        big = "x" * 70000

        def handler(conn, msg):
            conn.sendall(server_frame(b"hi", opcode=0x9))  # ping: client must pong
            payload = json.dumps({"id": msg["id"], "result": {"big": big}})
            half = len(payload) // 2
            conn.sendall(server_frame(payload[:half], 0x1, fin=False) +
                         server_frame(payload[half:], 0x0))
        client = self.connect(handler)
        self.assertEqual(client.call("Big")["big"], big)
        deadline = time.time() + 3
        while not self.browser.controls and time.time() < deadline:
            time.sleep(0.01)
        # read_client_raw already asserted the pong was masked.
        self.assertEqual(self.browser.controls, [(0xA, b"hi")])

    def test_host_header_brackets_ipv6_and_empty_path_is_slash(self):
        import urllib.parse
        u = urllib.parse.urlsplit("ws://[::1]:9222")
        self.assertEqual(cdp.host_header(u), "[::1]:9222")
        self.assertEqual(cdp.request_target(u), "/")
        v = urllib.parse.urlsplit("ws://127.0.0.1:9/devtools/x?a=1")
        self.assertEqual(cdp.host_header(v), "127.0.0.1:9")
        self.assertEqual(cdp.request_target(v), "/devtools/x?a=1")

    def test_handshake_sends_no_origin_header(self):
        def handler(conn, msg):
            conn.sendall(server_frame(json.dumps({"id": msg["id"], "result": {}})))
        client = self.connect(handler)
        client.call("Browser.getVersion")
        self.assertNotIn(b"origin", self.browser.head.lower())

    def test_a_timeout_mid_frame_loses_nothing(self):
        payload = json.dumps({"id": 1, "result": {"ok": True}})
        frame = server_frame(payload)

        def handler(conn, msg):
            conn.sendall(frame[:5])      # header plus a few payload bytes
            time.sleep(0.5)
            conn.sendall(frame[5:])
        client = self.connect(handler)
        client.timeout = 0.2
        with self.assertRaises(cdp.CdpError):
            client.call("Slow")          # gives up part-way through the frame
        client.ws.sock.settimeout(3)
        self.assertEqual(json.loads(client.ws.recv())["result"], {"ok": True})

    def test_only_loopback_websockets_are_allowed(self):
        for url in ("ws://example.com:9222/x", "wss://127.0.0.1:9222/x",
                    "http://127.0.0.1:9222/x"):
            with self.assertRaises(cdp.CdpError):
                cdp.WebSocket(url)

    def test_a_refused_handshake_raises(self):
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        s.listen(1)
        port = s.getsockname()[1]

        def refuse():
            conn, _ = s.accept()
            conn.recv(4096)
            conn.sendall(b"HTTP/1.1 403 Forbidden\r\n\r\n")
            conn.close()
        threading.Thread(target=refuse, daemon=True).start()
        self.addCleanup(s.close)
        with self.assertRaises(cdp.CdpError):
            cdp.WebSocket(f"ws://127.0.0.1:{port}/x")


if __name__ == "__main__":
    unittest.main()
