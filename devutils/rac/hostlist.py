#!/usr/bin/env python3

# Copyright 2026 The rac Authors
# You can use, redistribute, and/or modify this source code under
# the terms of the GPL-3.0 license that can be found in the LICENSE file.
"""Lists every host a rac build connected to, from a Chromium net-log.

`--log-net-log=<file> --net-log-capture-mode=Default` makes Chromium write a
JSON document: {"constants": {"logEventTypes": {<name>: <id>, ...},
"logSourceType": {...}}, "events": [{...}, ...]}. The capture workflow
(.github/workflows/net-capture.yml) kills the browser when its wait is up,
so the file may end mid-event or mid-list — parse_netlog keeps every
complete event and drops only the torn tail.

  hostlist.py hosts <netlog.json> [more.json ...] [--json] [--ignore-dev]
      Prints each distinct host the browser tried to reach, sorted, with the
      number of events that mentioned it and the event type where it was
      first seen. Hosts come from every place a net-log records one: request
      URLs (URL_REQUEST_START_JOB params.url, WebSocket URLs), resolver and
      DNS events (params.host / hostname / qname), connect jobs and sockets
      (group_name, destination, host_and_port, address), HTTP/2 and QUIC
      session params, the Host header on sent requests, and proxy resolution
      (pac_url, PAC-style proxy lists). Hosts are normalized to lowercase
      without a port; punycode stays punycode.
      Loopback (localhost, 127.0.0.1, ::1) and Helium's dev-build placeholder
      (*.qjz9zk) are reported in their own section, or hidden entirely with
      --ignore-dev.

  hostlist.py compare <netlog.json> [...] --list <doc.md>
      Compares what the capture saw with the list published in <doc.md>
      (docs/network.md), which carries a fenced ```hosts block: one host or
      wildcard (*.example.com, which also matches example.com itself) per
      line, with # comments. Prints hosts seen but not listed and exits 1;
      listed-but-unseen entries and loopback/dev hosts are informational.

Every command exits 0 on success, 1 when compare finds unlisted hosts, and
2 on bad arguments or unreadable input.
"""

import argparse
import ipaddress
import json
import re
import sys
from urllib.parse import urlsplit

# Hosts in a published list come from request URLs, so only schemes that can
# reach a remote host count. chrome://, data:, file:, blob:, extension and
# internal rac:// pages yield no entry.
_URL_SCHEMES = {'http', 'https', 'ws', 'wss', 'ftp', 'ftps'}

# A normalized host is all lowercase: letters, digits, dots, hyphens and
# underscores, plus what bare IPv6 literals need. Anything else (spaces,
# parens from a PAC annotation) isn't a host.
_HOST_CHARS = re.compile(r'^[a-z0-9._:%\-]+$')

# params keys that hold a bare hostname, possibly with a port.
_HOST_KEYS = ('host', 'hostname', 'qname', 'alt_svc_host')

# params keys that hold a full URL.
_URL_KEYS = ('url', 'pac_url', 'proxy_url')

# params keys that hold "host:port", "scheme://host:port", or "IP:port".
_HOSTPORT_KEYS = ('host_and_port', 'host_port_pair', 'destination',
                  'group_name', 'server_endpoint', 'address',
                  'remote_address', 'socket_address')

# Keys that record the IP a socket resolved to. Those IPs are answers to a
# hostname already listed, so they are not hosts the browser chose to reach
# (a direct-to-IP request still shows up through its URL or host key).
_ADDRESS_KEYS = ('address', 'remote_address', 'socket_address')

# params keys that hold PAC-style text: "PROXY h:8080; SOCKS5 s:1080; DIRECT"
# or a single proxy spec like "DIRECT" / "https://proxy:443".
_PROXY_TEXT_KEYS = ('proxy', 'proxy_server', 'pac_string', 'proxy_list',
                    'resolved_proxy_list', 'proxy_config')

# Scheme words in a PAC proxy list that aren't hosts themselves.
_PROXY_WORDS = {'direct', 'proxy', 'http', 'https', 'socks', 'socks4',
                'socks5', 'quic', 'pac'}

# ungoogled-chromium's domain substitution points Google endpoints at the
# nonexistent .qjz9zk TLD in dev builds; release builds never emit it.
_DEV_TLD = 'qjz9zk'


def _is_ip(host):
    try:
        ipaddress.ip_address(host)
    except ValueError:
        return False
    return True


def normalize_host(text):
    """(host): lowercase, no scheme, userinfo, path or port. Returns '' for
    anything that isn't a host."""
    if not isinstance(text, str):
        return ''
    host = text.strip().lower()
    if not host or any(c.isspace() for c in host):
        return ''
    # Socket pool group ids look like "ssl/host:443", "pm/ssl/host:443" or
    # "https://host:443", and may end in "<proxy or network key>".
    host = host.split('<', 1)[0]
    if '://' in host:
        host = host.rsplit('://', 1)[1]
    elif '/' in host:
        host = host.rsplit('/', 1)[1]
    host = host.split('/', 1)[0].split('?', 1)[0].split('#', 1)[0]
    host = host.rsplit('@', 1)[-1]
    if host.startswith('['):
        end = host.find(']')
        host = host[1:end] if end >= 0 else ''
    elif host.count(':') == 1:
        host = host.split(':', 1)[0]
    # A bare IPv6 literal (more than one colon, no brackets) keeps its colons.
    host = host.rstrip('.')
    if not _HOST_CHARS.match(host) or not re.search(r'[a-z0-9]', host):
        return ''
    return host


def host_from_url(url):
    """(host): the host a remote-scheme URL reaches, else ''."""
    if not isinstance(url, str) or '://' not in url.strip():
        return ''
    try:
        parts = urlsplit(url.strip())
        hostname = parts.hostname
    except ValueError:
        return ''
    if parts.scheme.lower() not in _URL_SCHEMES or not hostname:
        return ''
    return normalize_host(hostname)


def _proxy_text_hosts(text):
    """(hosts): every host:port token in a PAC-style proxy string."""
    found = set()
    if not isinstance(text, str):
        return found
    for token in re.split(r'[;\s,]+', text.strip()):
        if not token or token.lower() in _PROXY_WORDS:
            continue
        host = normalize_host(token)
        if host:
            found.add(host)
    return found


def _header_hosts(value):
    """(hosts): the host in a net-log header block — a list of "Name: value"
    strings or a dict — via its Host line."""
    found = set()
    if isinstance(value, dict):
        items = [(name, content) for name, content in value.items()]
    elif isinstance(value, list):
        items = [line.partition(':')[::2] for line in value
                 if isinstance(line, str)]
    else:
        return found
    for name, content in items:
        if isinstance(content, str) and name.strip().lower() == 'host':
            host = normalize_host(content)
            if host:
                found.add(host)
    return found


def iter_event_hosts(event_name, params):
    """(hosts): the hosts one event's params say the browser tried to reach.
    The scan is by param key, not event name: any net-log event that carries
    a URL, hostname, host:port pair, proxy spec or a sent Host header is
    evidence of contact."""
    found = set()
    if not isinstance(params, dict):
        return found
    for key in _URL_KEYS:
        host = host_from_url(params.get(key))
        if host:
            found.add(host)
    for key in _HOST_KEYS + _HOSTPORT_KEYS:
        host = normalize_host(params.get(key))
        if host and not (key in _ADDRESS_KEYS and _is_ip(host)):
            found.add(host)
    for key in _PROXY_TEXT_KEYS:
        found |= _proxy_text_hosts(params.get(key))
    if 'SEND_REQUEST' in (event_name or ''):
        for key in ('headers', 'request_headers'):
            found |= _header_hosts(params.get(key))
    return found


def event_type_names(constants):
    """{id: name} from constants.logEventTypes. Real net-logs map name to id;
    accept the id-as-key direction too so hand-written files work."""
    types = {}
    mapping = constants.get('logEventTypes') if isinstance(constants, dict) \
        else None
    for key, value in (mapping or {}).items():
        if isinstance(value, int):
            types[value] = key
        elif isinstance(value, str):
            try:
                types[int(key)] = value
            except (TypeError, ValueError):
                continue
    return types


def parse_netlog(text):
    """(constants, events). A whole document parses directly. A truncated one
    — the browser was killed mid-write — is repaired by decoding the
    constants object and then each event until the torn tail."""
    try:
        doc = json.loads(text)
        if isinstance(doc, dict):
            return (doc.get('constants') if isinstance(
                doc.get('constants'), dict) else {},
                    doc.get('events') if isinstance(
                        doc.get('events'), list) else [])
    except json.JSONDecodeError:
        pass
    decoder = json.JSONDecoder()
    constants = {}
    events = []
    pos = 0
    key = text.find('"constants"')
    if key >= 0:
        brace = text.find('{', key + len('"constants"'))
        if brace >= 0:
            try:
                constants, pos = decoder.raw_decode(text, brace)
            except json.JSONDecodeError:
                pass
    key = text.find('"events"', pos)
    if key >= 0:
        bracket = text.find('[', key + len('"events"'))
        if bracket >= 0:
            pos = bracket + 1
            while True:
                while pos < len(text) and text[pos] in ' \t\r\n,':
                    pos += 1
                if pos >= len(text) or text[pos] == ']':
                    break
                try:
                    event, pos = decoder.raw_decode(text, pos)
                except json.JSONDecodeError:
                    break  # the torn tail: drop the partial event
                events.append(event)
    return constants if isinstance(constants, dict) else {}, events


def is_loopback(host):
    """localhost (and its subdomains), 127.0.0.0/8, ::1 and 0.0.0.0."""
    return (host == 'localhost' or host.endswith('.localhost')
            or host.startswith('127.')
            or host in ('::1', '0:0:0:0:0:0:0:1', '0.0.0.0'))


def is_dev_placeholder(host):
    """Helium's dev-build placeholder TLD: qjz9zk or any *.qjz9zk."""
    return host == _DEV_TLD or host.endswith('.' + _DEV_TLD)


def collect_hosts(paths):
    """{host: {count, first_seen}} over every net-log, in argument order.
    count is the number of events that mentioned the host; first_seen is the
    event type of the first that did."""
    found = {}
    for path in paths:
        try:
            with open(path, encoding='utf-8') as stream:
                text = stream.read()
        except OSError as error:
            raise ValueError(f'cannot read {path}: {error}')
        constants, events = parse_netlog(text)
        names = event_type_names(constants)
        for event in events:
            if not isinstance(event, dict):
                continue
            type_id = event.get('type')
            name = names.get(type_id, f'type {type_id}')
            for host in iter_event_hosts(name, event.get('params')):
                entry = found.setdefault(host, {'count': 0, 'first_seen': name})
                entry['count'] += 1
    return found


def split_hosts(found):
    """(public, ignored): ignored hosts get a 'reason' of loopback or
    dev-placeholder."""
    public, ignored = {}, {}
    for host, entry in found.items():
        if is_loopback(host):
            ignored[host] = {**entry, 'reason': 'loopback'}
        elif is_dev_placeholder(host):
            ignored[host] = {**entry, 'reason': 'dev-placeholder'}
        else:
            public[host] = entry
    return public, ignored


def _print_host_lines(hosts, stream):
    for host in sorted(hosts):
        entry = hosts[host]
        print(f'{host:<45} {entry["count"]:>5}  {entry["first_seen"]}',
              file=stream)


def cmd_hosts(found, as_json, ignore_dev):
    public, ignored = split_hosts(found)
    if as_json:
        doc = {'hosts': [{'host': host, **public[host]}
                         for host in sorted(public)]}
        if not ignore_dev:
            doc['ignored'] = [{'host': host, **ignored[host]}
                              for host in sorted(ignored)]
        print(json.dumps(doc, indent=2))
        return 0
    print(f'# {len(public)} host{"s" if len(public) != 1 else ""}')
    _print_host_lines(public, sys.stdout)
    if not ignore_dev and ignored:
        print(f'\n# {len(ignored)} loopback/dev hosts '
              f'(excluded above; --ignore-dev hides them)')
        _print_host_lines(ignored, sys.stdout)
    return 0


def parse_host_list(text):
    """(patterns, found_block): the entries of the fenced ```hosts block in
    a docs page — one host or *.wildcard per line, # comments allowed.
    Several hosts blocks merge."""
    patterns = []
    in_block = False
    found_block = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith('```'):
            if in_block:
                in_block = False
            elif stripped == '```hosts':
                in_block = found_block = True
            continue
        if in_block:
            entry = stripped.split('#', 1)[0].strip().lower()
            if entry:
                patterns.append(entry)
    return patterns, found_block


def host_listed(host, patterns):
    """Matches a published pattern: exact, or *.example.com covering
    example.com and every subdomain of it."""
    for pattern in patterns:
        if pattern.startswith('*.'):
            suffix = pattern[2:]
            if host == suffix or host.endswith('.' + suffix):
                return True
        elif host == pattern:
            return True
    return False


def cmd_compare(found, list_path, ignore_dev):
    try:
        with open(list_path, encoding='utf-8') as stream:
            text = stream.read()
    except OSError as error:
        raise ValueError(f'cannot read {list_path}: {error}')
    patterns, found_block = parse_host_list(text)
    if not found_block:
        print(f'warning: no ```hosts block in {list_path}; '
              'treating the list as empty')
    public, ignored = split_hosts(found)
    unlisted = [host for host in sorted(public)
                if not host_listed(host, patterns)]
    unseen = [p for p in patterns
              if not any(host_listed(host, [p]) for host in public)]
    if unlisted:
        print(f'error: seen but not listed in {list_path}:')
        for host in unlisted:
            entry = public[host]
            print(f'  {host} ({entry["count"]} events, '
                  f'first seen {entry["first_seen"]})')
    else:
        print(f'ok: all {len(public)} hosts seen are listed in {list_path}')
    if unseen:
        print('info: listed but never seen in this capture:')
        for pattern in unseen:
            print(f'  {pattern}')
    if ignored and not ignore_dev:
        print('info: loopback/dev hosts seen (never part of the published '
              'list):')
        for host in sorted(ignored):
            print(f'  {host} ({ignored[host]["reason"]})')
    return 1 if unlisted else 0


def _run(arguments):
    found = collect_hosts(arguments.netlogs)
    if arguments.command == 'hosts':
        return cmd_hosts(found, arguments.json, arguments.ignore_dev)
    if arguments.command == 'compare':
        return cmd_compare(found, arguments.list, arguments.ignore_dev)
    return 2


def main(argv=None):
    parser = argparse.ArgumentParser(prog='hostlist.py',
                                   description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest='command', required=True)

    hosts = commands.add_parser('hosts',
                                help='print every host a net-log contacted')
    hosts.add_argument('netlogs', nargs='+', metavar='netlog.json')
    hosts.add_argument('--json', action='store_true',
                       help='emit JSON instead of aligned text')
    hosts.add_argument('--ignore-dev', action='store_true',
                       help='hide loopback and *.qjz9zk dev-placeholder hosts')

    compare = commands.add_parser('compare',
                                  help='check a capture against a published list')
    compare.add_argument('netlogs', nargs='+', metavar='netlog.json')
    compare.add_argument('--list', required=True, metavar='doc.md',
                         help='docs page carrying the ```hosts block')
    compare.add_argument('--ignore-dev', action='store_true',
                         help='hide loopback and *.qjz9zk dev-placeholder hosts')

    arguments = parser.parse_args(argv)
    try:
        return _run(arguments)
    except ValueError as error:
        print(f'error: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
