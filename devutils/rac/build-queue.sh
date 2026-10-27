#!/usr/bin/env bash
# Shares this Mac's builds between agents: two build slots, two run slots.
# Use it in place of a bare `he build`. See build_queue.py for the options.
#
# usage: devutils/rac/build-queue.sh [options] he build
#        devutils/rac/build-queue.sh status
set -euo pipefail
exec python3 "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)/build_queue.py" "$@"
