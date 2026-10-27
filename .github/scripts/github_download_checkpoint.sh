#!/bin/bash
# Checks a build checkpoint that actions/download-artifact just fetched into the
# current directory, and fetches it again with `gh run download` if it is
# missing or damaged. Three attempts in total: the action's own download counts
# as the first, so the step before this one should be allowed to fail.
#
# Usage: github_download_checkpoint.sh <artifact-name> (--sums FILE | --expect GLOB)
#                                      [--prior-attempts 0|1]
#
#   --sums FILE         FILE must exist and `sha256sum -c FILE` must pass.
#   --expect GLOB       At least one file must match GLOB (for the logs
#                       artifact, which has no checksums). Name a file that
#                       can't already be in the folder.
#   --prior-attempts N  1 when actions/download-artifact already ran (the
#                       default), 0 to go straight to `gh run download`.
#
# Environment: GITHUB_RUN_ID and GITHUB_REPOSITORY (set by Actions) and GH_TOKEN
# (the workflow needs `actions: read`). RAC_CHECKPOINT_RETRY_DELAY is the pause
# in seconds before each retry (default 20), and RAC_CHECKPOINT_ATTEMPT_TIMEOUT
# is how long one `gh` download may run (default 1200).

set -u

_max_attempts=3
_delay="${RAC_CHECKPOINT_RETRY_DELAY:-20}"
_attempt_timeout="${RAC_CHECKPOINT_ATTEMPT_TIMEOUT:-1200}"

_name=""
_sums=""
_expect=""
_attempts=1

while [ $# -gt 0 ]; do
  case "$1" in
    --sums) _sums="${2:?--sums needs a file name}"; shift 2 ;;
    --expect) _expect="${2:?--expect needs a glob}"; shift 2 ;;
    --prior-attempts) _attempts="${2:?--prior-attempts needs 0 or 1}"; shift 2 ;;
    -*) echo "error: unknown option $1" >&2; exit 2 ;;
    *) _name="$1"; shift ;;
  esac
done

if [ -z "$_name" ] || { [ -z "$_sums" ] && [ -z "$_expect" ]; }; then
  echo "usage: $0 <artifact-name> (--sums FILE | --expect GLOB) [--prior-attempts 0|1]" >&2
  exit 2
fi
case "$_attempts" in 0|1) ;; *) echo "error: --prior-attempts must be 0 or 1" >&2; exit 2 ;; esac

_run="${GITHUB_RUN_ID:-unknown}"
_reason=""

_sha256_check() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum -c "$1"
  else
    shasum -a 256 -c "$1"
  fi
}

# Checks the checkpoint in directory $1. Sets _reason when it is not usable.
_verify() {
  local dir="$1" out
  if [ -n "$_sums" ]; then
    if [ ! -f "$dir/$_sums" ]; then
      _reason="$_sums is missing"
      return 1
    fi
    if ! out=$(cd "$dir" && _sha256_check "$_sums" 2>&1); then
      _reason="the checksums in $_sums do not match"
      printf '%s\n' "$out" >&2
      return 1
    fi
  else
    if ! compgen -G "$dir/$_expect" >/dev/null; then
      _reason="no file matching $_expect"
      return 1
    fi
  fi
  return 0
}

# Runs a command, giving up after $_attempt_timeout seconds when a timeout
# tool is installed (the workflow step's timeout-minutes is the backstop).
_with_timeout() {
  if command -v timeout >/dev/null 2>&1; then
    timeout "$_attempt_timeout" "$@"
  elif command -v gtimeout >/dev/null 2>&1; then
    gtimeout "$_attempt_timeout" "$@"
  else
    "$@"
  fi
}

if [ "$_attempts" -ge 1 ]; then
  if _verify "."; then
    echo "Checkpoint $_name is complete (attempt 1 of $_max_attempts)."
    exit 0
  fi
  echo "Attempt 1 of $_max_attempts failed: $_reason."
fi

while [ "$_attempts" -lt "$_max_attempts" ]; do
  _attempts=$((_attempts + 1))
  sleep "$_delay"
  echo "Attempt $_attempts of $_max_attempts: gh run download $_run -n $_name"

  # Download into a fresh folder, so a partial earlier attempt can't get mixed
  # in and `gh` never has to overwrite anything.
  _tmp=$(mktemp -d "${TMPDIR:-/tmp}/checkpoint.XXXXXX") || exit 1
  if ! _with_timeout gh run download "$_run" -R "${GITHUB_REPOSITORY:?}" -n "$_name" -D "$_tmp"; then
    _reason="gh run download failed or timed out"
  elif _verify "$_tmp"; then
    # Dotglob so no stray hidden file is left behind in $_tmp.
    ( shopt -s dotglob nullglob; mv -f "$_tmp"/* . ) || { echo "::error::Could not move checkpoint $_name into place" >&2; rm -rf "$_tmp"; exit 1; }
    rm -rf "$_tmp"
    echo "Checkpoint $_name is complete (attempt $_attempts of $_max_attempts)."
    exit 0
  fi
  rm -rf "$_tmp"
  echo "Attempt $_attempts of $_max_attempts failed: $_reason."
done

echo "::error::Checkpoint artifact '$_name' from run $_run is unusable after $_max_attempts attempts: $_reason. The previous phase may have uploaded it incompletely; re-run that phase."
exit 1
