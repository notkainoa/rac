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

  hostlist.py hosts <netlog.json> [more.json ...] [--json] [--ignore-placeholder]
      Prints each distinct host the browser tried to reach, sorted, with the
      number of events that mentioned it and the event type where it was
      first seen. Hosts come from every place a net-log records one: request
      URLs (URL_REQUEST_START_JOB params.url, WebSocket URLs), resolver and
      DNS events (params.host / hostname / qname), connect jobs and sockets
      (group_name, destination, host_and_port, address), HTTP/2 and QUIC
      session params, the Host header on sent requests, and proxy resolution
      (pac_url, PAC-style proxy lists). Hosts are normalized to lowercase
      without a port; punycode stays punycode.
      Only hosts that left the browser count. Requests that never reach the
      network are listed apart, in "seen but never sent", with the reason:
      cache-only (load_flags has LOAD_ONLY_FROM_CACHE), blocked (ended with
      ERR_BLOCKED_BY_CLIENT and never opened a socket or stream), and
      local-only lookup (the network quality estimator's DNS-cache-only
      check). A host also seen in any ordinary event is contacted. When in
      doubt, a host counts as contacted.
      Loopback (localhost, 127.0.0.1, ::1) and Helium's placeholder
      (*.qjz9zk) are reported in their own section, or hidden entirely with
      --ignore-placeholder (--ignore-dev is the old name and still works).

  hostlist.py compare <netlog.json> [...] --list <doc.md> [--also NAME]
      Compares what the capture saw with the list published in <doc.md>
      (docs/network.md), which carries a fenced ```hosts block: one host or
      wildcard (*.example.com, which also matches example.com itself) per
      line, with # comments. A block fenced ```hosts NAME counts only with
      --also NAME (repeatable), for hosts a setting adds, such as Helium
      services once consented. Prints hosts seen but not listed and exits 1;
      listed-but-unseen entries, never-sent hosts and loopback/placeholder
      hosts are informational.

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
# nonexistent .qjz9zk TLD, and Helium uses it as the address of services
# the user hasn't consented to. Release builds use it too.
_PLACEHOLDER_TLD = 'qjz9zk'


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


def is_placeholder(host):
    """Helium's placeholder TLD: qjz9zk or any *.qjz9zk."""
    return host == _PLACEHOLDER_TLD or host.endswith('.' + _PLACEHOLDER_TLD)


# net-log event names that show a request got as far as a socket, a stream
# or a sent transaction. A request that carries one of these was not
# stopped locally.
_SENT_PREFIXES = ('SOCKET', 'TCP_', 'SSL_', 'HTTP2_', 'QUIC_',
                  'HTTP_STREAM', 'HTTP_TRANSACTION', 'HTTP3_')

# Events that prove the resolver really went to DNS or the OS for a host.
_REAL_RESOLVE_EVENTS = {'HOST_RESOLVER_MANAGER_JOB',
                        'HOST_RESOLVER_DNS_TASK',
                        'HOST_RESOLVER_SYSTEM_TASK', 'DNS_TRANSACTION'}

_LOAD_ONLY_FROM_CACHE = 8
_ERR_BLOCKED_BY_CLIENT = -20
_PHASE_BEGIN = 1
_PHASE_END = 2


def _source_type_names(constants):
    """{id: name} from constants.logSourceType (name to id in real logs)."""
    types = {}
    mapping = constants.get('logSourceType') if isinstance(constants, dict) \
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


def _source_id(event):
    source = event.get('source')
    return source.get('id') if isinstance(source, dict) else None


def _classify_sources(events, names, source_types):
    """{source id: reason} for URL_REQUEST sources that never reached the
    network: 'cache-only' or 'blocked'."""
    cache_only, blocked, sent = set(), set(), set()
    url_requests = set()
    for event in events:
        if not isinstance(event, dict):
            continue
        sid = _source_id(event)
        source = event.get('source')
        if (isinstance(source, dict) and
                source_types.get(source.get('type')) == 'URL_REQUEST'):
            url_requests.add(sid)
        name = names.get(event.get('type'), '')
        params = event.get('params')
        params = params if isinstance(params, dict) else {}
        phase = event.get('phase')
        if name.startswith(_SENT_PREFIXES) or 'SEND_REQUEST' in name:
            sent.add(sid)
        if name == 'URL_REQUEST_START_JOB' and phase == _PHASE_BEGIN:
            flags = params.get('load_flags')
            if isinstance(flags, int) and flags & _LOAD_ONLY_FROM_CACHE:
                cache_only.add(sid)
        if (name in ('URL_REQUEST_START_JOB', 'REQUEST_ALIVE') and
                phase == _PHASE_END and
                params.get('net_error') == _ERR_BLOCKED_BY_CLIENT):
            blocked.add(sid)
    reasons = {}
    for sid in url_requests:
        if sid in cache_only:
            reasons[sid] = 'cache-only'
        elif sid in blocked and sid not in sent:
            reasons[sid] = 'blocked'
    return reasons


def collect_capture(paths):
    """(contacted, never_sent) over every net-log, in argument order.
    contacted is {host: {count, first_seen}}: count is the number of events
    that mentioned the host, first_seen the event type of the first that did.
    never_sent is {host: {count, first_seen, reasons}} for hosts whose every
    mention came from a request that stayed on the machine; a host with any
    ordinary mention is contacted instead."""
    contacted = {}
    local = {}
    real_resolved = set()
    # A real resolver job whose params name no host could be for any host,
    # so then no estimator lookup counts as local-only (fail closed).
    unnamed_real_resolve = False
    pending = []  # (host, event name, reason or None) for NQE lookups
    for path in paths:
        try:
            with open(path, encoding='utf-8') as stream:
                text = stream.read()
        except OSError as error:
            raise ValueError(f'cannot read {path}: {error}')
        constants, events = parse_netlog(text)
        names = event_type_names(constants)
        source_types = _source_type_names(constants)
        reasons = _classify_sources(events, names, source_types)
        for event in events:
            if not isinstance(event, dict):
                continue
            name = names.get(event.get('type'), f'type {event.get("type")}')
            params = event.get('params')
            hosts = iter_event_hosts(name, params)
            if name in _REAL_RESOLVE_EVENTS:
                real_resolved |= hosts
                if not hosts:
                    unnamed_real_resolve = True
            if not hosts:
                continue
            source = event.get('source')
            reason = reasons.get(_source_id(event))
            if (reason is None and name == 'HOST_RESOLVER_MANAGER_REQUEST' and
                    isinstance(source, dict) and source_types.get(
                        source.get('type')) == 'NETWORK_QUALITY_ESTIMATOR'):
                reason = 'local-only lookup'
                for host in hosts:
                    pending.append((host, name))
                continue
            for host in hosts:
                if reason is None:
                    entry = contacted.setdefault(
                        host, {'count': 0, 'first_seen': name})
                    entry['count'] += 1
                else:
                    entry = local.setdefault(
                        host, {'count': 0, 'first_seen': name,
                               'reasons': set()})
                    entry['count'] += 1
                    entry['reasons'].add(reason)
    for host, name in pending:
        if host in real_resolved or unnamed_real_resolve:
            entry = contacted.setdefault(host, {'count': 0,
                                                'first_seen': name})
            entry['count'] += 1
        else:
            entry = local.setdefault(host, {'count': 0, 'first_seen': name,
                                            'reasons': set()})
            entry['count'] += 1
            entry['reasons'].add('local-only lookup')
    never_sent = {host: {**entry, 'reasons': sorted(entry['reasons'])}
                  for host, entry in local.items() if host not in contacted}
    return contacted, never_sent


def collect_hosts(paths):
    """{host: {count, first_seen}}: the hosts that were contacted."""
    return collect_capture(paths)[0]


def split_hosts(found):
    """(public, ignored): ignored hosts get a 'reason' of loopback or
    placeholder."""
    public, ignored = {}, {}
    for host, entry in found.items():
        if is_loopback(host):
            ignored[host] = {**entry, 'reason': 'loopback'}
        elif is_placeholder(host):
            ignored[host] = {**entry, 'reason': 'placeholder'}
        else:
            public[host] = entry
    return public, ignored


def _print_host_lines(hosts, stream):
    for host in sorted(hosts):
        entry = hosts[host]
        print(f'{host:<45} {entry["count"]:>5}  {entry["first_seen"]}',
              file=stream)


def _print_never_sent(never_sent):
    print(f'\n# {len(never_sent)} seen but never sent '
          f'(stayed on this machine, not contacted)')
    for host in sorted(never_sent):
        entry = never_sent[host]
        print(f'{host:<45} {entry["count"]:>5}  '
              f'{", ".join(entry["reasons"])}')


def cmd_hosts(found, never_sent, as_json, ignore_placeholder):
    public, ignored = split_hosts(found)
    if as_json:
        doc = {'hosts': [{'host': host, **public[host]}
                         for host in sorted(public)],
               'never_sent': [{'host': host, **never_sent[host]}
                              for host in sorted(never_sent)]}
        if not ignore_placeholder:
            doc['ignored'] = [{'host': host, **ignored[host]}
                              for host in sorted(ignored)]
        print(json.dumps(doc, indent=2))
        return 0
    print(f'# {len(public)} host{"s" if len(public) != 1 else ""}')
    _print_host_lines(public, sys.stdout)
    if never_sent:
        _print_never_sent(never_sent)
    if not ignore_placeholder and ignored:
        print(f'\n# {len(ignored)} loopback/placeholder hosts '
              f'(excluded above; --ignore-placeholder hides them)')
        _print_host_lines(ignored, sys.stdout)
    return 0


def parse_host_list(text, also=()):
    """(patterns, found_block): the entries of the fenced ```hosts block in
    a docs page — one host or *.wildcard per line, # comments allowed.
    Several hosts blocks merge. A ```hosts NAME block counts only when NAME
    is in `also`, so hosts a setting adds never widen the default list."""
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
            elif stripped.startswith('```hosts ') and \
                    stripped[len('```hosts '):].strip() in also:
                in_block = True
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


def cmd_compare(found, never_sent, list_path, ignore_placeholder, also=()):
    try:
        with open(list_path, encoding='utf-8') as stream:
            text = stream.read()
    except OSError as error:
        raise ValueError(f'cannot read {list_path}: {error}')
    patterns, found_block = parse_host_list(text, also)
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
    if never_sent:
        print('info: seen but never sent (not part of the published list):')
        for host in sorted(never_sent):
            print(f'  {host} ({", ".join(never_sent[host]["reasons"])})')
    if ignored and not ignore_placeholder:
        print('info: loopback/placeholder hosts seen (never part of the '
              'published list):')
        for host in sorted(ignored):
            print(f'  {host} ({ignored[host]["reason"]})')
    return 1 if unlisted else 0


def _run(arguments):
    found, never_sent = collect_capture(arguments.netlogs)
    if arguments.command == 'hosts':
        return cmd_hosts(found, never_sent, arguments.json,
                         arguments.ignore_placeholder)
    if arguments.command == 'compare':
        return cmd_compare(found, never_sent, arguments.list,
                           arguments.ignore_placeholder, arguments.also)
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
    hosts.add_argument('--ignore-placeholder', '--ignore-dev',
                       dest='ignore_placeholder', action='store_true',
                       help='hide loopback and *.qjz9zk placeholder hosts '
                       '(--ignore-dev is the old name)')

    compare = commands.add_parser('compare',
                                  help='check a capture against a published list')
    compare.add_argument('netlogs', nargs='+', metavar='netlog.json')
    compare.add_argument('--list', required=True, metavar='doc.md',
                         help='docs page carrying the ```hosts block')
    compare.add_argument('--also', action='append', default=[], metavar='NAME',
                         help='also count the ```hosts NAME block (repeatable)')
    compare.add_argument('--ignore-placeholder', '--ignore-dev',
                         dest='ignore_placeholder', action='store_true',
                         help='hide loopback and *.qjz9zk placeholder hosts '
                         '(--ignore-dev is the old name)')

    arguments = parser.parse_args(argv)
    try:
        return _run(arguments)
    except ValueError as error:
        print(f'error: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
