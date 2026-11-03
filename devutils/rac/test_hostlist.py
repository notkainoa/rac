#!/usr/bin/env python3

# Copyright 2026 The rac Authors
# You can use, redistribute, and/or modify this source code under
# the terms of the GPL-3.0 license that can be found in the LICENSE file.
"""Tests for devutils/rac/hostlist.py, the net-log host extractor behind the
network capture workflow.

Fixtures live in devutils/rac/fixtures/netlog/: basic.json covers one of each
event shape hostlist reads, truncated.json is cut mid-event the way a killed
browser leaves the file, and dev.json holds the loopback and .qjz9zk hosts a
dev build can emit. Compare tests write their own ```hosts docs.

Run from the repository root:
    python3 -m unittest devutils/rac/test_hostlist.py -v
"""

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
HELPER = REPO / 'devutils' / 'rac' / 'hostlist.py'
FIXTURES = REPO / 'devutils' / 'rac' / 'fixtures' / 'netlog'
BASIC = FIXTURES / 'basic.json'
TRUNCATED = FIXTURES / 'truncated.json'
DEV = FIXTURES / 'dev.json'

spec = importlib.util.spec_from_file_location('hostlist', HELPER)
hostlist = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hostlist)


def run_helper(*args):
    return subprocess.run(['python3', str(HELPER), *args],
                          capture_output=True, text=True, check=False)


def doc_with_hosts(*lines):
    return '---\n# doc\n\n```hosts\n' + '\n'.join(lines) + '\n```\n'


class NormalizeTest(unittest.TestCase):
    def test_lowercase_and_port(self):
        self.assertEqual(hostlist.normalize_host('EXAMPLE.com:443'),
                         'example.com')
        self.assertEqual(hostlist.normalize_host('ssl://CDN.Example.com:443'),
                         'cdn.example.com')
        self.assertEqual(hostlist.normalize_host('Example.COM.'),
                         'example.com')

    def test_socket_pool_group_ids(self):
        for text in ('ssl/example.com:443', 'pm/ssl/example.com:443',
                     'ssl/example.com:443<https://proxy.test.org:8080>'):
            self.assertEqual(hostlist.normalize_host(text), 'example.com')

    def test_resolved_socket_ips_are_not_hosts(self):
        self.assertEqual(hostlist.iter_event_hosts(
            'SOCKET_CONNECT', {'address': '93.184.216.34:443'}), set())
        self.assertEqual(hostlist.iter_event_hosts(
            'URL_REQUEST_START_JOB', {'url': 'https://93.184.216.34/'}),
            {'93.184.216.34'})

    def test_wildcard_does_not_match_lookalike(self):
        self.assertFalse(hostlist.host_listed('example.com.evil.net',
                                              ['*.example.com']))
        self.assertFalse(hostlist.host_listed('badexample.com',
                                              ['*.example.com']))

    def test_ipv6(self):
        self.assertEqual(hostlist.normalize_host('[::1]:8080'), '::1')
        self.assertEqual(hostlist.normalize_host('::1'), '::1')

    def test_rejects_non_hosts(self):
        for bad in ('', '  ', 'DIRECT()()', '(filtered)', 'host name:80',
                    '...', '--'):
            self.assertEqual(hostlist.normalize_host(bad), '', bad)

    def test_url_schemes(self):
        self.assertEqual(hostlist.host_from_url('https://A.com:8443/x'), 'a.com')
        self.assertEqual(hostlist.host_from_url('wss://ws.example.com/'),
                         'ws.example.com')
        for dead in ('chrome://newtab/', 'data:text/plain,x', 'file:///etc',
                     'about:blank', 'chrome-extension://abc/page.html',
                     'not a url'):
            self.assertEqual(hostlist.host_from_url(dead), '', dead)


class ParseTest(unittest.TestCase):
    def test_whole_document(self):
        constants, events = hostlist.parse_netlog(BASIC.read_text())
        self.assertEqual(len(events), 16)
        self.assertIn('logEventTypes', constants)

    def test_truncated_tail(self):
        constants, events = hostlist.parse_netlog(TRUNCATED.read_text())
        self.assertEqual(len(events), 2)  # the torn third event is dropped
        self.assertEqual(constants['logEventTypes']['TCP_CONNECT'], 485)

    def test_missing_events_key(self):
        constants, events = hostlist.parse_netlog('{"constants":{}}')
        self.assertEqual(events, [])


class HostsTest(unittest.TestCase):
    def setUp(self):
        self.found = hostlist.collect_hosts([str(BASIC)])
        self.public, self.ignored = hostlist.split_hosts(self.found)

    def test_every_event_shape(self):
        expected = {
            'example.com',          # url with case and port + resolver, count 2
            'cdn.example.com',      # url
            'api.test.org',         # Host header on a sent request
            'dns.test.org',         # HOST_RESOLVER params.host
            'secure-dns.test.org',  # DNS attempt params.qname
            'dns-tx.test.org',      # DNS_TRANSACTION params.qname
            'connect.test.org',     # connect-job group_name ssl://host:443
            'h2.test.org',          # HTTP/2 session params
            'quic.test.org',        # QUIC session params, port stripped
            'socket.test.org',      # wss:// WebSocket URL
            'wpad.test.org',        # pac_url
            'proxy.test.org',       # PROXY token in a PAC list
            'socks.test.org',       # SOCKS5 token in a PAC list
        }
        self.assertEqual(set(self.public), expected)

    def test_count_and_first_seen(self):
        entry = self.public['example.com']
        self.assertEqual(entry['count'], 2)
        self.assertEqual(entry['first_seen'], 'URL_REQUEST_START_JOB')
        self.assertEqual(self.public['api.test.org']['first_seen'],
                         'HTTP_TRANSACTION_SEND_REQUEST')

    def test_internal_schemes_skipped(self):
        # chrome://newtab/ and data: in the fixture must yield no hosts.
        self.assertNotIn('newtab', self.public)
        self.assertNotIn('data', self.public)

    def test_headers_as_dict(self):
        hosts = hostlist.iter_event_hosts(
            'HTTP_TRANSACTION_SEND_REQUEST',
            {'headers': {'Host': 'dict.test.org', 'Accept': '*/*'}})
        self.assertEqual(hosts, {'dict.test.org'})

    def test_response_headers_ignored(self):
        # Only sent request headers count: a Host line in a response header
        # block must not produce a host.
        hosts = hostlist.iter_event_hosts(
            'HTTP_TRANSACTION_READ_RESPONSE_HEADERS',
            {'headers': ['HTTP/1.1 200 OK', 'Host: sneaky.test.org']})
        self.assertEqual(hosts, set())


class DevHostsTest(unittest.TestCase):
    def setUp(self):
        self.found = hostlist.collect_hosts([str(DEV)])
        self.public, self.ignored = hostlist.split_hosts(self.found)

    def test_loopback_and_placeholder_split_out(self):
        self.assertEqual(set(self.public), {'public.test.org',
                                            'qjz9zk.example.com'})
        self.assertEqual(set(self.ignored),
                         {'127.0.0.1', 'localhost', '::1', '9oo91e.qjz9zk'})
        self.assertEqual(self.ignored['9oo91e.qjz9zk']['reason'],
                         'dev-placeholder')
        self.assertEqual(self.ignored['::1']['reason'], 'loopback')

    def test_ignore_dev_flag_hides_them(self):
        result = run_helper('hosts', str(DEV), '--ignore-dev')
        self.assertEqual(result.returncode, 0)
        self.assertIn('public.test.org', result.stdout)
        self.assertNotIn('9oo91e.qjz9zk', result.stdout)
        self.assertNotIn('127.0.0.1', result.stdout)
        plain = run_helper('hosts', str(DEV))
        self.assertIn('9oo91e.qjz9zk', plain.stdout)
        self.assertIn('loopback/dev', plain.stdout)


class OutputTest(unittest.TestCase):
    def test_text_output(self):
        result = run_helper('hosts', str(BASIC))
        self.assertEqual(result.returncode, 0)
        self.assertIn('# 13 hosts', result.stdout)
        line = next(l for l in result.stdout.splitlines()
                    if l.startswith('example.com'))
        self.assertIn('2', line)
        self.assertIn('URL_REQUEST_START_JOB', line)

    def test_json_output(self):
        result = run_helper('hosts', str(BASIC), str(DEV), '--json')
        self.assertEqual(result.returncode, 0)
        doc = json.loads(result.stdout)
        hosts = {h['host']: h for h in doc['hosts']}
        self.assertIn('example.com', hosts)
        self.assertIn('public.test.org', hosts)
        ignored = {h['host']: h for h in doc['ignored']}
        self.assertEqual(ignored['9oo91e.qjz9zk']['reason'], 'dev-placeholder')

    def test_json_ignore_dev(self):
        result = run_helper('hosts', str(DEV), '--json', '--ignore-dev')
        doc = json.loads(result.stdout)
        self.assertNotIn('ignored', doc)
        self.assertEqual([h['host'] for h in doc['hosts']],
                         ['public.test.org', 'qjz9zk.example.com'])


class CompareTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.doc = Path(self._tmp.name) / 'network.md'

    def write_doc(self, *lines):
        self.doc.write_text(doc_with_hosts(*lines))

    def test_pass(self):
        self.write_doc('*.test.org  # test hosts', 'example.com',
                       'cdn.example.com')
        result = run_helper('compare', str(BASIC), '--list', str(self.doc))
        self.assertEqual(result.returncode, 0)
        self.assertIn('ok: all 13 hosts seen are listed', result.stdout)

    def test_fail_lists_unseen(self):
        self.write_doc('example.com')
        result = run_helper('compare', str(BASIC), '--list', str(self.doc))
        self.assertEqual(result.returncode, 1)
        self.assertIn('seen but not listed', result.stdout)
        self.assertIn('cdn.example.com', result.stdout)

    def test_wildcard_matches_apex_and_subdomain(self):
        self.assertTrue(hostlist.host_listed('test.org', ['*.test.org']))
        self.assertTrue(hostlist.host_listed('a.b.test.org', ['*.test.org']))
        self.assertFalse(hostlist.host_listed('nottest.org', ['*.test.org']))
        self.assertFalse(hostlist.host_listed('test.org.evil.com',
                                              ['*.test.org']))

    def test_unseen_listed_is_info_not_failure(self):
        self.write_doc('*.test.org', 'example.com', 'cdn.example.com',
                       'extra.example.net')
        result = run_helper('compare', str(BASIC), '--list', str(self.doc))
        self.assertEqual(result.returncode, 0)
        self.assertIn('listed but never seen', result.stdout)
        self.assertIn('extra.example.net', result.stdout)

    def test_dev_hosts_never_fail_compare(self):
        self.write_doc('public.test.org', 'qjz9zk.example.com')
        result = run_helper('compare', str(DEV), '--list', str(self.doc))
        self.assertEqual(result.returncode, 0)
        self.assertIn('loopback/dev', result.stdout)

    def test_missing_block_warns_and_fails_on_hosts(self):
        self.doc.write_text('# no hosts block here\n')
        result = run_helper('compare', str(BASIC), '--list', str(self.doc))
        self.assertEqual(result.returncode, 1)
        self.assertIn('treating the list as empty', result.stdout)

    def test_missing_file_is_an_error(self):
        result = run_helper('compare', str(BASIC), '--list',
                            str(self.doc))  # never written
        self.assertEqual(result.returncode, 2)
        self.assertIn('error:', result.stderr)
        missing_netlog = run_helper('hosts', str(self.doc))
        self.assertEqual(missing_netlog.returncode, 2)


if __name__ == '__main__':
    unittest.main()
