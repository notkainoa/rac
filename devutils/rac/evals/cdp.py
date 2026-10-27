# Copyright 2026 The rac Authors
# SPDX-License-Identifier: GPL-3.0-or-later
"""A minimal Chrome DevTools Protocol client over a plain WebSocket, because
the Python standard library has none. Text frames only, one thread, blocking.
Enough for run.py: connect to the browser endpoint, call methods, read events.
"""

import base64
import collections
import hashlib
import json
import os
import socket
import struct
import time
import urllib.parse

GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


class CdpError(Exception):
    pass


class WebSocket:
    def __init__(self, url, timeout=15):
        u = urllib.parse.urlsplit(url)
        if u.scheme != "ws" or u.hostname not in ("127.0.0.1", "localhost", "::1"):
            raise CdpError("only ws:// to loopback is allowed")
        self.sock = socket.create_connection((u.hostname, u.port), timeout=timeout)
        key = base64.b64encode(os.urandom(16)).decode()
        path = u.path + ("?" + u.query if u.query else "")
        self.sock.sendall((f"GET {path} HTTP/1.1\r\nHost: {u.hostname}:{u.port}\r\nUpgrade: websocket\r\n"
                           f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\n"
                           f"Sec-WebSocket-Version: 13\r\n\r\n").encode())
        head = b""
        while b"\r\n\r\n" not in head:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise CdpError("closed during handshake")
            head += chunk
        head, _, self.buf = head.partition(b"\r\n\r\n")
        if b" 101 " not in head.split(b"\r\n")[0]:
            raise CdpError("handshake refused: " + head.split(b"\r\n")[0].decode(errors="replace"))
        want = base64.b64encode(hashlib.sha1((key + GUID).encode()).digest()).decode().lower()
        if want not in head.decode(errors="replace").lower():
            raise CdpError("bad Sec-WebSocket-Accept")

    def send(self, text):
        data = text.encode()
        header = bytearray([0x81])
        n = len(data)
        if n < 126:
            header.append(0x80 | n)
        elif n < 65536:
            header += bytes([0x80 | 126]) + struct.pack(">H", n)
        else:
            header += bytes([0x80 | 127]) + struct.pack(">Q", n)
        mask = os.urandom(4)
        header += mask
        self.sock.sendall(bytes(header) + bytes(b ^ mask[i % 4] for i, b in enumerate(data)))

    def _read(self, n):
        while len(self.buf) < n:
            chunk = self.sock.recv(65536)
            if not chunk:
                raise CdpError("connection closed")
            self.buf += chunk
        out, self.buf = self.buf[:n], self.buf[n:]
        return out

    def recv(self):
        """The next complete text message (answers pings, joins fragments)."""
        message = b""
        while True:
            b0, b1 = self._read(2)
            opcode, n = b0 & 0x0F, b1 & 0x7F
            if n == 126:
                n = struct.unpack(">H", self._read(2))[0]
            elif n == 127:
                n = struct.unpack(">Q", self._read(8))[0]
            payload = self._read(n)  # servers never mask
            if opcode == 0x8:
                raise CdpError("connection closed by the browser")
            if opcode == 0x9:
                self.sock.sendall(bytes([0x8A, 0x80]) + os.urandom(4))
                continue
            if opcode == 0xA:
                continue
            message += payload
            if b0 & 0x80:
                return message.decode()

    def close(self):
        try:
            self.sock.close()
        except OSError:
            pass


class Cdp:
    def __init__(self, url, timeout=15):
        self.ws, self.timeout, self.next_id = WebSocket(url, timeout), timeout, 0
        self.events = collections.deque()

    def call(self, method, params=None, session_id=None):
        self.next_id += 1
        mid = self.next_id
        msg = {"id": mid, "method": method, "params": params or {}}
        if session_id:
            msg["sessionId"] = session_id
        self.ws.send(json.dumps(msg))
        deadline = time.time() + self.timeout
        while time.time() < deadline:
            self.ws.sock.settimeout(max(0.1, deadline - time.time()))
            try:
                data = json.loads(self.ws.recv())
            except socket.timeout:
                break
            if data.get("id") == mid:
                if "error" in data:
                    raise CdpError(f"{method}: {data['error']}")
                return data.get("result", {})
            self.events.append(data)
        raise CdpError(f"timed out: {method}")

    def drain_events(self):
        out = list(self.events)
        self.events.clear()
        return out

    def close(self):
        self.ws.close()
