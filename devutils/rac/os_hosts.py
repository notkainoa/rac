#!/usr/bin/env python3
# Copyright 2026 The rac Authors
# You can use, redistribute, and/or modify this source code under
# the terms of the GPL-3.0 license that can be found in the LICENSE file.
"""Hosts rac reached according to the OS, not Chromium's net-log.

Some of rac's traffic never passes through Chromium's network stack, so
--log-net-log can't see it: Sparkle checks the update feed and downloads
updates with macOS NSURLSession in rac's main process. The network capture
(.github/scripts/github_net_capture.sh) records it from outside instead:

  dns.txt   `tcpdump -n -l -vv port 53`: the runner's DNS answers, which
            map each IP to the name that was asked for.
  syn.txt   `tcpdump -k NP` of outgoing TCP SYNs: every new connection,
            tagged with the process that opened it (pktap metadata).
  lsof.txt  `lsof -nP -iTCP -iUDP -a -p <rac pids>` polled every second,
            each block headed by "# <unix time>".

usage: os_hosts.py --app-path <rac.app path> [--dns dns.txt] [--syn syn.txt]
                   [--lsof lsof.txt] [--json]

A connection counts as rac's when lsof lists it under one of rac's
processes, or when the SYN's process metadata names one of them. The main
process (…/Contents/MacOS/rac) is where NSURLSession runs, so its hosts are
the ones outside Chromium's stack; helpers (the network service) are listed
separately and also appear in the net-log. Loopback is left out. Exits 0,
or 2 on bad arguments.
"""

import argparse
import ipaddress
import json
import re
import sys

# An answer inside a tcpdump -vv DNS response: "name. [1m] A 1.2.3.4" or
# "name. AAAA 2001:db8::1". The question is "q: A? name." on the same line.
QUESTION = re.compile(r'\bq: (?:A|AAAA|HTTPS|SVCB)\? (\S+?)\.? ')
ANSWER = re.compile(r'(?:\[[0-9a-z]+\] )?(A|AAAA) ([0-9a-fA-F:.]+)')
# A tcpdump endpoint: "1.2.3.4.443" or "2001:db8::1.443".
ENDPOINT = r'([0-9a-fA-F:.]+)\.(\d+)'
SYN = re.compile(ENDPOINT + r' > ' + ENDPOINT + r':')
# pktap metadata: "proc rac:1234:" (name, pid) or "pid 1234".
SYN_PROC = re.compile(r'proc ([^:,)]+):(\d+)')
# lsof: "rac  1234 runner 23u IPv4 0x... TCP 10.0.0.5:5555->1.2.3.4:443 (...)".
LSOF_LINE = re.compile(r'^(\S+)\s+(\d+)\s.*?(?:TCP|UDP) (\S+?)->(\S+?)(?: \(|$)')


def _ip(text):
    text = text.strip('[]')
    try:
        return str(ipaddress.ip_address(text))
    except ValueError:
        return None


def _split_host_port(endpoint):
    """'1.2.3.4:443' or '[2001:db8::1]:443' -> (ip, port)."""
    if endpoint.startswith('['):
        host, _, port = endpoint[1:].partition(']:')
    else:
        host, _, port = endpoint.rpartition(':')
    return _ip(host), port


def parse_dns(text):
    """{ip: set(names)} from tcpdump -vv DNS responses. tcpdump -vv wraps
    each packet over two lines, so lines are joined per packet first."""
    names = {}
    packets, current = [], ''
    for line in text.splitlines():
        if line[:1].isdigit() and current:
            packets.append(current)
            current = ''
        current += ' ' + line.strip()
    if current:
        packets.append(current)
    for packet in packets:
        question = QUESTION.search(packet)
        if not question:
            continue
        name = question.group(1).rstrip('.').lower()
        rest = packet[question.end():]
        for _, address in ANSWER.findall(rest):
            ip = _ip(address)
            if ip:
                names.setdefault(ip, set()).add(name)
    return names


def is_loopback(ip):
    return ipaddress.ip_address(ip).is_loopback


def parse_lsof(text, app_path):
    """{ip: set(process kinds)} for connections lsof listed under rac's
    processes. The poller only lists rac's pids; the command name
    distinguishes the main process ('rac') from helpers."""
    found = {}
    for line in text.splitlines():
        match = LSOF_LINE.match(line)
        if not match:
            continue
        command, _, _, remote = match.groups()
        ip, _ = _split_host_port(remote)
        if not ip or is_loopback(ip):
            continue
        kind = 'main' if command == 'rac' else 'helper'
        found.setdefault(ip, set()).add(kind)
    return found


def parse_syn(text, rac_names=('rac', 'rac Helper')):
    """{ip: set(process kinds)} for SYNs whose pktap metadata names one of
    rac's processes."""
    found = {}
    for line in text.splitlines():
        proc = SYN_PROC.search(line)
        endpoints = SYN.search(line)
        if not proc or not endpoints:
            continue
        name = proc.group(1).strip()
        if not any(name == n or name.startswith(n + ' ') for n in rac_names):
            continue
        ip = _ip(endpoints.group(3))
        if not ip or is_loopback(ip):
            continue
        found.setdefault(ip, set()).add('main' if name == 'rac' else 'helper')
    return found


def collect(dns_text, syn_text, lsof_text, app_path):
    """[{host, ips, processes}], sorted by host; an IP with no DNS answer
    is listed under its address."""
    names = parse_dns(dns_text)
    reached = parse_lsof(lsof_text, app_path)
    for ip, kinds in parse_syn(syn_text).items():
        reached.setdefault(ip, set()).update(kinds)
    hosts = {}
    for ip, kinds in reached.items():
        for host in sorted(names.get(ip, {ip})):
            entry = hosts.setdefault(host, {'host': host, 'ips': set(),
                                            'processes': set()})
            entry['ips'].add(ip)
            entry['processes'] |= kinds
    return [{'host': e['host'], 'ips': sorted(e['ips']),
             'processes': sorted(e['processes'])}
            for e in sorted(hosts.values(), key=lambda e: e['host'])]


def render(entries):
    lines = [f'# {len(entries)} hosts reached by rac (OS record, outside '
             "Chromium's net-log)"]
    for entry in entries:
        where = ('main process (NSURLSession, e.g. Sparkle)'
                 if entry['processes'] == ['main'] else
                 ', '.join(entry['processes']))
        lines.append(f'{entry["host"]:<45} {where}  [{", ".join(entry["ips"])}]')
    return '\n'.join(lines) + '\n'


def _read(path):
    if not path:
        return ''
    try:
        with open(path, encoding='utf-8', errors='replace') as stream:
            return stream.read()
    except OSError as error:
        raise ValueError(f'cannot read {path}: {error}')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--app-path', required=True)
    parser.add_argument('--dns')
    parser.add_argument('--syn')
    parser.add_argument('--lsof')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args(argv)
    try:
        entries = collect(_read(args.dns), _read(args.syn), _read(args.lsof),
                          args.app_path)
    except ValueError as error:
        print(f'error: {error}', file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(entries, indent=2))
    else:
        sys.stdout.write(render(entries))
    return 0


if __name__ == '__main__':
    sys.exit(main())
