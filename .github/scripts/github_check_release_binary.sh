#!/bin/bash
# Release-binary gate (G6): a release build must not contain rac's developer
# switches. Scans every Mach-O file in an app bundle (the main executable, the
# framework binaries under Contents/Frameworks/*.framework/Versions/*/, the
# helper apps and helper tools) with `strings` and reports each forbidden
# string it finds, with the binary it is in.
#
# Usage: github_check_release_binary.sh <path/to/rac.app>
#
# RAC_G6_GATE decides what a match does:
#   warn     (default) print a warning for each match and exit 0
#   enforce  print an error for each match and exit 1
#
# Exits 2 when it can't do the check at all (no bundle, nothing to scan, no
# `strings`, unknown RAC_G6_GATE), whatever the mode: a gate that scanned
# nothing has not passed.

set -u -o pipefail

# `strings` output holds arbitrary bytes. Under a UTF-8 locale, grep and cut
# skip a line with an invalid byte before the match, as real binaries have.
export LC_ALL=C

_forbidden=(
  rac-agent-debug
  rac-agent-mcp-echo
  rac-window-screenshot
  rac-launch-in-background
)

_mode="${RAC_G6_GATE:-warn}"
case "$_mode" in
  warn) _level=warning ;;
  enforce) _level=error ;;
  *) echo "::error::RAC_G6_GATE must be 'warn' or 'enforce', not '$_mode'"; exit 2 ;;
esac

_app="${1:-}"
if [ -z "$_app" ] || [ ! -d "$_app" ]; then
  echo "::error::usage: $0 <path/to/rac.app> (got '${_app}', which is not a directory)"
  exit 2
fi
_app="${_app%/}"

if ! command -v strings >/dev/null 2>&1; then
  echo "::error::strings is not installed; can't check the release binaries"
  exit 2
fi

# Mach-O thin (32/64-bit, both byte orders) and fat (universal) headers.
_is_macho() {
  local magic
  magic=$(od -An -tx1 -N4 "$1" 2>/dev/null | tr -d ' \n')
  case "$magic" in
    feedface|feedfacf|cefaedfe|cffaedfe|cafebabe|bebafeca|cafebabf|bfbafeca) return 0 ;;
  esac
  return 1
}

_strings_out=$(mktemp "${TMPDIR:-/tmp}/g6-strings.XXXXXX") || exit 2
trap 'rm -f "$_strings_out"' EXIT

_scanned=0
_hits=0
_hit_binaries=0

# `find -type f` skips symlinks, so a framework's Versions/Current and
# top-level links don't make the same binary count twice.
while IFS= read -r -d '' _file; do
  _is_macho "$_file" || continue
  _scanned=$((_scanned + 1))
  _rel="${_file#"$_app"/}"

  # Reading from stdin makes `strings` scan every byte. Given a file name,
  # Apple's `strings` parses the Mach-O and skips some sections.
  if ! strings -a -n 12 < "$_file" > "$_strings_out"; then
    echo "::error::strings failed on $_rel"
    exit 2
  fi

  _binary_hit=0
  for _needle in "${_forbidden[@]}"; do
    _lines=$(grep -F -m 3 -- "$_needle" "$_strings_out" | cut -c1-200)
    [ -n "$_lines" ] || continue
    _hits=$((_hits + 1))
    _binary_hit=1
    echo "::${_level}::G6: '$_needle' found in $_rel"
    while IFS= read -r _line; do
      printf '    %s: %s\n' "$_rel" "$_line"
    done <<< "$_lines"
  done
  _hit_binaries=$((_hit_binaries + _binary_hit))
done < <(find "$_app" -type f -print0)

if [ "$_scanned" -eq 0 ]; then
  echo "::error::no Mach-O files under $_app; is this a built app bundle?"
  exit 2
fi

if [ "$_hits" -eq 0 ]; then
  echo "G6 passed: none of ${_forbidden[*]} in $_scanned binaries."
  exit 0
fi

_summary="G6: $_hits forbidden string match(es) in $_hit_binaries of $_scanned binaries."
if [ "$_mode" = enforce ]; then
  echo "::error::$_summary Release builds must not contain developer switches."
  exit 1
fi
echo "::warning::$_summary Not failing because RAC_G6_GATE=warn; set it to enforce once the switches are behind a build flag."
exit 0
