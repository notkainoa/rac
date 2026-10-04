#!/usr/bin/env python3
"""Signs rac updates and writes the Sparkle feeds that announce them.

  sparkle.py keygen
      Prints a new EdDSA key pair. The public key goes into builds; the
      private key signs updates. Store both as GitHub secrets, never in git.

  sparkle.py appcast --arch arm64 --dmg rac_0.2.0_arm64-macos.dmg \\
      --base-url https://github.com/<repo>/releases/download/0.2.0/ \\
      [--delta 0.1.0-arm64.delta ...] --out appcast-arm64.xml
      Signs the disk image and any deltas with the private key in
      RAC_SPARKLE_ED_PRIVATE_KEY and writes a feed with one update in it.

Keys use the same format as Sparkle's generate_keys: the base64 32-byte
Ed25519 seed for the private key, and the base64 32-byte public key.
"""

import argparse
import base64
import email.utils
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rac_version # pylint: disable=wrong-import-position

SPARKLE_NS = 'http://www.andymatuschak.org/xml-namespaces/sparkle'
PRIVATE_KEY_ENV = 'RAC_SPARKLE_ED_PRIVATE_KEY'
MINIMUM_MACOS = '13.0'
DELTA_NAME = re.compile(r'(?P<version>\d+\.\d+\.\d+)-(?P<arch>arm64|x86_64)\.delta')


def public_key_of(private_key):
    """Returns the base64 public key for a private key."""
    raw = private_key.public_key().public_bytes(serialization.Encoding.Raw,
                                                serialization.PublicFormat.Raw)
    return base64.b64encode(raw).decode()


def load_private_key(encoded):
    """Reads a base64 private key. Accepts the 32-byte seed, and the older
    64- and 96-byte forms that begin with the seed."""
    raw = base64.b64decode(encoded.strip(), validate=True)
    if len(raw) not in (32, 64, 96):
        raise ValueError(f'{PRIVATE_KEY_ENV}: expected a 32-byte seed, got {len(raw)} bytes')
    return Ed25519PrivateKey.from_private_bytes(raw[:32])


def sign(private_key, path):
    """Returns (base64 signature, length) for the file at path."""
    data = path.read_bytes()
    return base64.b64encode(private_key.sign(data)).decode(), len(data)


def enclosure(parent, tag, private_key, path, url, **attrs):
    """Adds an enclosure for the signed file at path to parent."""
    signature, length = sign(private_key, path)
    element = ET.SubElement(parent, tag)
    element.set('url', url)
    for name, value in attrs.items():
        element.set(f'{{{SPARKLE_NS}}}{name}', value)
    element.set('length', str(length))
    element.set('type', 'application/octet-stream')
    element.set(f'{{{SPARKLE_NS}}}edSignature', signature)
    return element


def build_appcast(private_key, version, args):
    """Returns the feed for the files named in the appcast command's args."""
    arch, dmg, deltas = args.arch, args.dmg, args.delta
    base_url = args.base_url if args.base_url.endswith('/') else args.base_url + '/'

    ET.register_namespace('sparkle', SPARKLE_NS)
    rss = ET.Element('rss', {'version': '2.0'})
    channel = ET.SubElement(rss, 'channel')
    ET.SubElement(channel, 'title').text = f'rac ({arch})'

    item = ET.SubElement(channel, 'item')
    ET.SubElement(item, 'title').text = f'rac {version}'
    ET.SubElement(item, 'pubDate').text = email.utils.formatdate(usegmt=True)
    ET.SubElement(item, f'{{{SPARKLE_NS}}}version').text = version
    ET.SubElement(item, f'{{{SPARKLE_NS}}}shortVersionString').text = version
    ET.SubElement(item, f'{{{SPARKLE_NS}}}minimumSystemVersion').text = MINIMUM_MACOS
    enclosure(item, 'enclosure', private_key, dmg, base_url + dmg.name)

    if deltas:
        deltas_element = ET.SubElement(item, f'{{{SPARKLE_NS}}}deltas')
        for delta in deltas:
            match = DELTA_NAME.fullmatch(delta.name)
            if not match or match['arch'] != arch:
                raise ValueError(f'{delta}: expected a name like 0.1.0-{arch}.delta')
            enclosure(deltas_element,
                      'enclosure',
                      private_key,
                      delta,
                      base_url + delta.name,
                      deltaFrom=match['version'])

    ET.indent(rss)
    return ET.ElementTree(rss)


def cmd_keygen(_args):
    """Prints a new key pair."""
    private_key = Ed25519PrivateKey.generate()
    seed = private_key.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw,
                                     serialization.NoEncryption())
    print(f'public:  {public_key_of(private_key)}')
    print(f'private: {base64.b64encode(seed).decode()}')
    return 0


def cmd_appcast(args):
    """Writes a signed feed."""
    encoded = os.environ.get(PRIVATE_KEY_ENV)
    if not encoded:
        print(f'{PRIVATE_KEY_ENV} is not set', file=sys.stderr)
        return 1
    private_key = load_private_key(encoded)
    if args.public_key and args.public_key != public_key_of(private_key):
        print('the private key does not match --public-key', file=sys.stderr)
        return 1

    version = args.version or '.'.join(str(part) for part in rac_version.read_version())
    tree = build_appcast(private_key, version, args)
    tree.write(args.out, encoding='utf-8', xml_declaration=True)
    print(f'wrote {args.out}: rac {version} ({args.arch}), {len(args.delta)} deltas',
          file=sys.stderr)
    return 0


def main():
    """CLI entrypoint"""
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest='command', required=True)

    commands.add_parser('keygen', help='print a new key pair').set_defaults(func=cmd_keygen)

    appcast = commands.add_parser('appcast', help='write a signed feed')
    appcast.add_argument('--arch', required=True, choices=('arm64', 'x86_64'))
    appcast.add_argument('--dmg', required=True, type=Path, help='the disk image to offer')
    appcast.add_argument('--base-url', required=True, help='URL of the folder holding the files')
    appcast.add_argument('--delta', type=Path, action='append', default=[])
    appcast.add_argument('--version', help='defaults to rac_version.txt')
    appcast.add_argument('--public-key', help='fail unless the private key matches this one')
    appcast.add_argument('--out', required=True, type=Path)
    appcast.set_defaults(func=cmd_appcast)

    args = parser.parse_args()
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
