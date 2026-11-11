#!/usr/bin/env python3
# Copyright 2026 The rac Authors
# You can use, redistribute, and/or modify this source code under
# the terms of the GPL-3.0 license that can be found in the LICENSE file.
"""Tests for os_hosts.py."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import os_hosts  # noqa: E402

APP = '/tmp/x/rac.app'

DNS = '''\
12:00:00.100000 IP (tos 0x0, ttl 64, id 1, offset 0, flags [none], proto UDP (17), length 56)
    10.1.0.5.55555 > 168.63.129.16.53: 4660+ [1au] A? github.com. (39)
12:00:00.120000 IP (tos 0x0, ttl 128, id 2, offset 0, flags [none], proto UDP (17), length 72)
    168.63.129.16.53 > 10.1.0.5.55555: 4660 q: A? github.com. 1/0/1 github.com. [60s] A 140.82.113.4 ar: . OPT UDPsize=1232 (56)
12:00:01.000000 IP (tos 0x0, ttl 128, id 3, offset 0, flags [none], proto UDP (17), length 120)
    168.63.129.16.53 > 10.1.0.5.55556: 4661 q: A? objects.githubusercontent.com. 2/0/0 objects.githubusercontent.com. [1m] A 185.199.108.133, objects.githubusercontent.com. [1m] A 185.199.109.133 (90)
12:00:02.000000 IP6 (hlim 64, next-header UDP (17) payload length: 80) fe80::1.53 > fe80::2.5555: [udp sum ok] 4662 q: AAAA? pipelines.actions.githubusercontent.com. 1/0/0 pipelines.actions.githubusercontent.com. [5m] AAAA 2603:1030::1 (72)
'''

SYN = '''\
12:00:00.200000 (en0, proc rac:4242:abc, svc BE, out, so) IP 10.1.0.5.50001 > 140.82.113.4.443: Flags [S], seq 1, win 65535, length 0
12:00:01.200000 (en0, proc Runner.Listener:777:def, svc BE, out, so) IP6 fe80::2.50002 > 2603:1030::1.443: Flags [S], seq 2, win 65535, length 0
'''

LSOF = '''\
# 1794380000
COMMAND    PID   USER   FD   TYPE DEVICE SIZE/OFF NODE NAME
rac       4242 runner   40u  IPv4 0x1      0t0  TCP 10.1.0.5:50001->140.82.113.4:443 (ESTABLISHED)
rac\\x20H  4300 runner   41u  IPv4 0x2      0t0  TCP 10.1.0.5:50010->185.199.108.133:443 (ESTABLISHED)
rac       4242 runner   42u  IPv4 0x3      0t0  TCP 127.0.0.1:50020->127.0.0.1:9222 (ESTABLISHED)
'''


class OsHostsTest(unittest.TestCase):

    def test_dns_maps_answers_to_the_question(self):
        names = os_hosts.parse_dns(DNS)
        self.assertEqual(names['140.82.113.4'], {'github.com'})
        self.assertEqual(names['185.199.109.133'],
                         {'objects.githubusercontent.com'})
        self.assertEqual(names['2603:1030::1'],
                         {'pipelines.actions.githubusercontent.com'})

    def test_rac_connections_get_names_and_process_kinds(self):
        entries = os_hosts.collect(DNS, SYN, LSOF, APP)
        hosts = {e['host']: e for e in entries}
        self.assertEqual(hosts['github.com']['processes'], ['main'])
        self.assertEqual(hosts['github.com']['ips'], ['140.82.113.4'])
        self.assertEqual(hosts['objects.githubusercontent.com']['processes'],
                         ['helper'])

    def test_other_processes_and_loopback_are_left_out(self):
        hosts = {e['host'] for e in os_hosts.collect(DNS, SYN, LSOF, APP)}
        # The runner agent's own traffic is not rac's.
        self.assertNotIn('pipelines.actions.githubusercontent.com', hosts)
        self.assertNotIn('127.0.0.1', hosts)

    def test_unresolved_ip_is_listed_by_address(self):
        lsof = 'rac 4242 runner 40u IPv4 0x1 0t0 TCP 10.1.0.5:1->203.0.113.9:443 (SYN_SENT)\n'
        entries = os_hosts.collect('', '', lsof, APP)
        self.assertEqual([e['host'] for e in entries], ['203.0.113.9'])

    def test_render_names_the_main_process_as_outside_chromium(self):
        text = os_hosts.render(os_hosts.collect(DNS, SYN, LSOF, APP))
        self.assertIn("outside Chromium's net-log", text)
        self.assertIn('github.com', text)
        self.assertIn('NSURLSession', text)

    def test_empty_inputs(self):
        self.assertEqual(os_hosts.collect('', '', '', APP), [])


if __name__ == '__main__':
    unittest.main()
