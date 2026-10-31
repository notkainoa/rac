# Copyright 2026 The rac Authors
# SPDX-License-Identifier: GPL-3.0-or-later
import base64
import hashlib
import json
import socket
import struct
import threading
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


def read_client_frame(conn):
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
    text = bytes(b ^ mask[i % 4] for i, b in enumerate(need(n))).decode()
    return text if b0 & 0x0F == 0x1 else None  # control frames (the client's pong) carry no message


class FakeBrowser:
    """A one-connection WebSocket server that answers CDP-style messages."""

    def __init__(self, handler):
        self.sock = socket.socket()
        self.sock.bind(("127.0.0.1", 0))
        self.sock.listen(1)
        self.port = self.sock.getsockname()[1]
        self.handler = handler
        threading.Thread(target=self.run, daemon=True).start()

    def run(self):
        conn, _ = self.sock.accept()
        head = b""
        while b"\r\n\r\n" not in head:
            head += conn.recv(4096)
        key = [l.split(b": ")[1] for l in head.split(b"\r\n") if l.lower().startswith(b"sec-websocket-key")][0]
        accept = base64.b64encode(hashlib.sha1(key + cdp.GUID.encode()).digest())
        conn.sendall(b"HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                     b"Sec-WebSocket-Accept: " + accept + b"\r\n\r\n")
        try:
            while True:
                text = read_client_frame(conn)
                if text is not None:
                    self.handler(conn, json.loads(text))
        except (EOFError, OSError):
            pass
        finally:
            conn.close()
            self.sock.close()


class CdpTest(unittest.TestCase):
    def connect(self, handler):
        browser = FakeBrowser(handler)
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

    def test_large_and_fragmented_messages_and_pings(self):
        big = "x" * 70000

        def handler(conn, msg):
            conn.sendall(server_frame(b"", opcode=0x9))  # ping: the client must pong, then carry on
            payload = json.dumps({"id": msg["id"], "result": {"big": big}})
            half = len(payload) // 2
            conn.sendall(server_frame(payload[:half], 0x1, fin=False) + server_frame(payload[half:], 0x0))
        client = self.connect(handler)
        self.assertEqual(client.call("Big")["big"], big)

    def test_only_loopback_websockets_are_allowed(self):
        for url in ("ws://example.com:9222/x", "wss://127.0.0.1:9222/x", "http://127.0.0.1:9222/x"):
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
