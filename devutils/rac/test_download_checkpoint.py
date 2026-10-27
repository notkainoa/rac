#!/usr/bin/env python3

# Copyright 2025 The rac Authors
# You can use, redistribute, and/or modify this source code under
# the terms of the GPL-3.0 license that can be found in the LICENSE file.
"""Runs .github/scripts/github_download_checkpoint.sh against a fake `gh`.

The fake `gh` follows a plan, one word per call: `ok` writes a good
checkpoint, `nosums` writes the archive without sums.txt, `bad` writes a
checkpoint whose digest does not match, and `fail` exits with an error. Nothing
touches the network.

Run from the repository root:
    python3 -m unittest discover -s devutils/rac -p 'test_*.py' -v
"""

from pathlib import Path
import hashlib
import os
import subprocess
import tempfile
import textwrap
import unittest

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / '.github' / 'scripts' / 'github_download_checkpoint.sh'
ARTIFACT = 'github_build_artifact_arm64'
RUN_ID = '40222453249'

FAKE_GH = textwrap.dedent('''\
    #!/bin/bash
    # Fake gh: `gh run download <id> -R <repo> -n <name> -D <dir>`.
    set -eu
    [ "$1 $2" = "run download" ] || { echo "unexpected: $*" >&2; exit 2; }
    while [ $# -gt 0 ]; do
      case "$1" in -D) dir="$2"; shift 2 ;; *) shift ;; esac
    done
    echo x >> "$FAKE_GH_DIR/calls"
    n=$(wc -l < "$FAKE_GH_DIR/calls")
    step=$(sed -n "${n}p" "$FAKE_GH_DIR/plan")
    case "${step:-fail}" in
      ok)     printf 'archive' > "$dir/build_src.tar.zst"
              (cd "$dir" && sha256sum build_src.tar.zst > sums.txt 2>/dev/null \\
                 || shasum -a 256 build_src.tar.zst > sums.txt) ;;
      nosums) printf 'archive' > "$dir/build_src.tar.zst" ;;
      bad)    printf 'archive' > "$dir/build_src.tar.zst"
              printf '%064d  build_src.tar.zst\\n' 0 > "$dir/sums.txt" ;;
      logs)   printf 'x' > "$dir/build_times_arm64.log" ;;
      *)      echo "gh: download failed" >&2; exit 1 ;;
    esac
''')


def write_good_checkpoint(directory):
    data = b'archive'
    (directory / 'build_src.tar.zst').write_bytes(data)
    (directory / 'sums.txt').write_text(f'{hashlib.sha256(data).hexdigest()}  build_src.tar.zst\n')


class DownloadCheckpointTest(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        root = Path(self._tmp.name)
        self.work = root / 'work'
        self.work.mkdir()
        self.fake_dir = root / 'fake'
        self.fake_dir.mkdir()
        bin_dir = root / 'bin'
        bin_dir.mkdir()
        gh = bin_dir / 'gh'
        gh.write_text(FAKE_GH)
        gh.chmod(0o755)
        (self.fake_dir / 'calls').write_text('')
        self.env = dict(
            os.environ,
            PATH=f'{bin_dir}{os.pathsep}{os.environ["PATH"]}',
            TMPDIR=str(root),
            FAKE_GH_DIR=str(self.fake_dir),
            GITHUB_RUN_ID=RUN_ID,
            GITHUB_REPOSITORY='notkainoa/rac',
            RAC_CHECKPOINT_RETRY_DELAY='0',
        )

    def run_script(self, plan, *args):
        (self.fake_dir / 'plan').write_text(''.join(f'{step}\n' for step in plan))
        return subprocess.run(['bash', str(SCRIPT), *args], cwd=self.work, env=self.env,
                              capture_output=True, text=True, check=False)

    def gh_calls(self):
        return len((self.fake_dir / 'calls').read_text().splitlines())

    def error_lines(self, result):
        return [line for line in (result.stdout + result.stderr).splitlines()
                if line.startswith('::error::')]

    def test_good_download_needs_no_retry(self):
        write_good_checkpoint(self.work)
        result = self.run_script([], ARTIFACT, '--sums', 'sums.txt')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.gh_calls(), 0)

    def test_missing_sums_then_success_on_retry(self):
        (self.work / 'build_src.tar.zst').write_text('partial')
        result = self.run_script(['nosums', 'ok'], ARTIFACT, '--sums', 'sums.txt')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.gh_calls(), 2)
        self.assertIn('sums.txt is missing', result.stdout)
        self.assertEqual((self.work / 'build_src.tar.zst').read_text(), 'archive')
        self.assertTrue((self.work / 'sums.txt').is_file())
        self.assertEqual(self.error_lines(result), [])

    def test_digest_mismatch_in_first_download_is_retried(self):
        write_good_checkpoint(self.work)
        (self.work / 'build_src.tar.zst').write_text('truncated')
        result = self.run_script(['ok'], ARTIFACT, '--sums', 'sums.txt')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.gh_calls(), 1)
        self.assertEqual((self.work / 'build_src.tar.zst').read_text(), 'archive')

    def test_digest_mismatch_three_times_fails_clearly(self):
        write_good_checkpoint(self.work)
        (self.work / 'build_src.tar.zst').write_text('truncated')
        result = self.run_script(['bad', 'bad', 'bad'], ARTIFACT, '--sums', 'sums.txt')
        self.assertEqual(result.returncode, 1)
        # The action's download was attempt 1, so only two gh downloads follow.
        self.assertEqual(self.gh_calls(), 2)
        errors = self.error_lines(result)
        self.assertEqual(len(errors), 1, errors)
        self.assertIn(ARTIFACT, errors[0])
        self.assertIn(RUN_ID, errors[0])
        self.assertIn('3 attempts', errors[0])
        self.assertIn('do not match', errors[0])

    def test_nothing_downloaded_three_times_fails_clearly(self):
        result = self.run_script(['fail', 'fail', 'fail'], ARTIFACT, '--sums', 'sums.txt')
        self.assertEqual(result.returncode, 1)
        self.assertEqual(self.gh_calls(), 2)
        errors = self.error_lines(result)
        self.assertEqual(len(errors), 1, errors)
        self.assertIn(ARTIFACT, errors[0])
        self.assertIn(RUN_ID, errors[0])

    def test_missing_sums_three_times_says_sums_are_missing(self):
        result = self.run_script(['nosums', 'nosums', 'nosums'], ARTIFACT, '--sums', 'sums.txt',
                                 '--prior-attempts', '0')
        self.assertEqual(result.returncode, 1)
        self.assertEqual(self.gh_calls(), 3)
        errors = self.error_lines(result)
        self.assertEqual(len(errors), 1, errors)
        self.assertIn('sums.txt is missing', errors[0])

    def test_logs_artifact_needs_the_expected_file(self):
        (self.work / 'github_actions_setup_env_toolchain.log').write_text('setup')
        result = self.run_script(['fail', 'logs'], 'github_build_logs_arm64',
                                 '--expect', 'build_times_arm64.log')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.gh_calls(), 2)
        self.assertTrue((self.work / 'build_times_arm64.log').is_file())

    def test_usage_error_without_a_check(self):
        result = self.run_script([], ARTIFACT)
        self.assertEqual(result.returncode, 2)


if __name__ == '__main__':
    unittest.main()
