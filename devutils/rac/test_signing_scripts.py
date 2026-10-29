#!/usr/bin/env python3

# Copyright 2025 The rac Authors
# You can use, redistribute, and/or modify this source code under
# the terms of the GPL-3.0 license that can be found in the LICENSE file.
"""Checks the CI signing scripts without a real signed build.

github_verify_dmg.sh is run end to end against stub hdiutil, codesign, spctl
and xcrun binaries on PATH, so its team-ID and entitlement checks are
exercised for real. github_sign_app.sh can't run without keychains and a
Chromium build, so the test scans the text of its log messages instead.

Run from the repository root:
    python3 -m unittest discover -s devutils/rac -p 'test_*.py' -v
"""

from pathlib import Path
import os
import re
import subprocess
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[2]
VERIFY = REPO / '.github' / 'scripts' / 'github_verify_dmg.sh'
SIGN = REPO / '.github' / 'scripts' / 'github_sign_app.sh'
BUILD_YML = REPO / '.github' / 'workflows' / 'build.yml'

EMPTY_PLIST = '<?xml version="1.0" encoding="UTF-8"?><plist version="1.0"><dict/></plist>'
TEAM_ID = 'ABCDE12345'

STUBS = {
    # `attach` makes a fake rac.app at the -mountpoint; `detach` succeeds.
    'hdiutil': '''\
#!/bin/bash
if [ "${1:-}" = attach ]; then
  mnt=
  while [ $# -gt 0 ]; do
    [ "$1" = -mountpoint ] && mnt="$2"
    shift
  done
  mkdir -p "$mnt/rac.app/Contents/MacOS"
  : > "$mnt/rac.app/Contents/MacOS/rac"
  exit 0
fi
[ "${1:-}" = detach ] && exit 0
exit 1
''',
    # Behaves by flag: --verify always passes, -dv reports FAKE_CODESIGN_TEAM,
    # --entitlements prints FAKE_CODESIGN_ENTITLEMENTS or fails when
    # FAKE_CODESIGN_ENTITLEMENTS_FAIL=1.
    'codesign': '''\
#!/bin/bash
for arg in "$@"; do
  case "$arg" in
    --entitlements)
      if [ "${FAKE_CODESIGN_ENTITLEMENTS_FAIL:-0}" = 1 ]; then
        echo "stub codesign: could not read entitlements" >&2
        exit 3
      fi
      printf '%s' "${FAKE_CODESIGN_ENTITLEMENTS-}"
      exit 0
      ;;
    --verify) exit 0 ;;
    -dv)
      printf 'TeamIdentifier=%s\\n' "${FAKE_CODESIGN_TEAM:-ABCDE12345}" >&2
      exit 0
      ;;
  esac
done
exit 0
''',
    'spctl': '''\
#!/bin/bash
if [ "${1:-}" = --status ]; then
  echo "assessments enabled"
  exit 0
fi
echo "source=Notarized Developer ID"
exit 0
''',
    'xcrun': '#!/bin/bash\nexit 0\n',
}


class VerifyDmgTest(unittest.TestCase):
    """Runs github_verify_dmg.sh against stubbed macOS tools."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.dmg = self.root / 'rac.dmg'
        self.dmg.touch()
        bin_dir = self.root / 'bin'
        bin_dir.mkdir()
        for name, body in STUBS.items():
            stub = bin_dir / name
            stub.write_text(body)
            stub.chmod(0o755)
        self.env = dict(
            os.environ,
            PATH=f'{bin_dir}{os.pathsep}{os.environ["PATH"]}',
            TMPDIR=str(self.root),
            RAC_EXPECT_NOTARIZED='1',
            RAC_EXPECT_TEAM_ID=TEAM_ID,
            FAKE_CODESIGN_TEAM=TEAM_ID,
            FAKE_CODESIGN_ENTITLEMENTS=EMPTY_PLIST,
        )

    def run_verify(self, **env_overrides):
        env = dict(self.env)
        env.update(env_overrides)
        result = subprocess.run(
            ['bash', str(VERIFY), str(self.dmg)],
            env=env, capture_output=True, text=True, errors='replace',
            timeout=60, check=False,
        )
        return result.returncode, result.stdout + result.stderr

    def test_notarized_build_with_matching_team_passes(self):
        code, out = self.run_verify()
        self.assertEqual(code, 0, out)
        self.assertIn('Disk image verified', out)

    def test_expect_team_id_is_trimmed(self):
        # A secret pasted with a stray newline or space must still match the
        # team the app was signed by.
        for padded in (f'{TEAM_ID}\n', f' {TEAM_ID} ', f'\t{TEAM_ID}\r\n'):
            with self.subTest(padded=padded):
                code, out = self.run_verify(RAC_EXPECT_TEAM_ID=padded)
                self.assertEqual(code, 0, out)
                self.assertIn('Disk image verified', out)

    def test_wrong_team_id_still_fails(self):
        code, out = self.run_verify(RAC_EXPECT_TEAM_ID='ZZZZZ99999')
        self.assertEqual(code, 1, out)
        self.assertIn('not the notarization team', out)

    def test_entitlements_read_failure_is_an_error(self):
        # A failed codesign must not be mistaken for "no entitlements".
        code, out = self.run_verify(FAKE_CODESIGN_ENTITLEMENTS_FAIL='1')
        self.assertNotEqual(code, 0, out)
        self.assertIn('::error::', out)
        self.assertIn('entitlement', out.lower())

    def test_empty_entitlements_output_means_no_entitlements(self):
        code, out = self.run_verify(
            RAC_EXPECT_NOTARIZED='0', FAKE_CODESIGN_ENTITLEMENTS='')
        self.assertEqual(code, 0, out)
        self.assertIn('Ad hoc build', out)


class SignAppMessagesTest(unittest.TestCase):
    """No message that reaches the CI log may name or expand a secret.

    printf calls that feed a pipe (e.g. `| base64 --decode`) handle values
    rather than write messages, so they are not scanned.
    """

    SECRET_NAME = re.compile(r'PROD_MACOS_|MACOS_CERTIFICATE|MACOS_CI_KEYCHAIN')

    def messages_naming_secrets(self, path):
        bad = []
        logical = []
        for raw in path.read_text().splitlines():
            logical.append(raw)
            if raw.rstrip().endswith('\\'):
                continue
            line = ' '.join(logical).strip()
            logical = []
            if not re.match(r'(echo|printf)\b', line):
                continue
            if '|' in line or '>' in line:
                continue
            if self.SECRET_NAME.search(line):
                bad.append(line)
        return bad

    def test_sign_app_messages_do_not_name_secrets(self):
        bad = self.messages_naming_secrets(SIGN)
        self.assertEqual(bad, [], '\n'.join(bad))

    def test_build_yml_messages_do_not_name_secrets(self):
        bad = self.messages_naming_secrets(BUILD_YML)
        self.assertEqual(bad, [], '\n'.join(bad))


if __name__ == '__main__':
    unittest.main()
