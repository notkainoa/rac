#!/usr/bin/env python3
"""Applies resources/dmg.json to resources/dmg_dsstore and dmg_beta_dsstore.

Run it after devutils/generate_dmg_dsstore.sh, or on its own to move icons.
It sets what appdmg can't:

- Labels are 13 pt and sit under the icon. Finder draws them black on any
  background picture, so both backgrounds keep that area light.
- Window height includes the 32 pt macOS 26 title bar. appdmg adds 22 pt,
  which cuts off the bottom of the background.
- The beta copy points its background at a volume named "rac Beta". Finder
  finds the background by volume name, so with one shared file a mounted
  stable DMG would lend its background to the beta window.

Needs the ds_store package: pip install ds_store
"""

import json
import sys
from pathlib import Path

from ds_store import DSStore, DSStoreEntry
from ds_store.store import ILocCodec
from mac_alias import Alias

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / 'resources' / 'dmg.json'
DSSTORE = ROOT / 'resources' / 'dmg_dsstore'
BETA_DSSTORE = ROOT / 'resources' / 'dmg_beta_dsstore'
BETA_VOLUME = 'rac Beta'
TITLE_BAR = 32
TEXT_SIZE = 13.0


def write(path, entries, positions, volume=None):
    """Writes entries and icon positions to path, pointing the background
    alias at volume when given."""
    if path.exists():
        path.unlink()
    with DSStore.open(str(path), 'w+') as store:
        for filename, code, kind, value in entries:
            if volume and filename == '.' and code == b'icvp':
                value = dict(value)
                alias = Alias.from_bytes(value['backgroundImageAlias'])
                alias.volume.name = volume
                alias.volume.posix_path = f'/Volumes/{volume}'
                value['backgroundImageAlias'] = alias.to_bytes()
            store.insert(DSStoreEntry(filename, code, kind, value))
        for name, position in positions.items():
            store.insert(DSStoreEntry(name, b'Iloc', ILocCodec, position))


def main():
    config = json.loads(CONFIG.read_text(encoding='utf-8'))
    size = config['window']['size']
    positions = {
        item.get('name') or Path(item['path']).name: (item['x'], item['y'])
        for item in config['contents']
    }

    entries = []
    with DSStore.open(str(DSSTORE), 'r') as store:
        for e in store:
            if e.code == b'Iloc':
                continue
            value = e.value
            if e.filename == '.' and e.code == b'bwsp':
                value = dict(value)
                value['WindowBounds'] = '{{100, 100}, {%d, %d}}' % (
                    size['width'], size['height'] + TITLE_BAR)
            if e.filename == '.' and e.code == b'icvp':
                value = dict(value)
                value['iconSize'] = float(config['icon-size'])
                value['textSize'] = TEXT_SIZE
                value['labelOnBottom'] = True
            entries.append((e.filename, e.code, e.type, value))

    write(DSSTORE, entries, positions)
    write(BETA_DSSTORE, entries, positions, BETA_VOLUME)
    return 0


if __name__ == '__main__':
    sys.exit(main())
