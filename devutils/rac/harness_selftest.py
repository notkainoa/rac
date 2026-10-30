#!/usr/bin/env python3

# Copyright 2026 The rac Authors
# You can use, redistribute, and/or modify this source code under
# the terms of the GPL-3.0 license that can be found in the LICENSE file.
"""End-to-end checks for the dev screenshot-harness fixes on the tools branch.

Each case launches rac once through the build queue's run slot with the
request-file harness (--rac-window-screenshot-requests), drives it by writing
request lines, then quits it with `command 34031` (IDC_EXIT) and asserts on
the files it left behind:

  onboarding    profile-window must not end an existing profile's tour
    (stunfin: a profile dir seeded with an empty Preferences and no
    helium.completed_onboarding must still lack it after a clean quit;
    stnew: a profile the verb created gets it set)
  record_dir    a recording into a brand-new nested dir captures frame 0
    and every logged frame is on disk; an unwritable dir stops the record
    and keeps the harness alive
  record_fail   a write failure mid-recording counts as skipped and is
    not logged
  record_stale  a second, shorter recording into the same dir leaves no
    stale fNNNN.png behind
  pointer       pointer-path then `pointer off` applies no further moves,
    and a new `pointer` cancels a running path
  space_theme   `space-theme <valid> <invalid-mode>` saves nothing

usage: devutils/rac/harness_selftest.py [--only CASE[,CASE...]]
"""

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
PROFILE = ROOT / 'build' / 'profile'
SCRATCH = ROOT / 'build' / 'scratch'

# `command` runs a browser command by ID; 34031 is IDC_EXIT, a clean quit.
IDC_EXIT = 'command 34031'

POLL = 0.25


def is_frame_filename(name):
    """True for a recording's frame file: f, four or more digits, .png.

    Mirrors IsFrameFileName in window_record.cc: files are written as
    f%04d.png, so nothing shorter than f0000.png can be one, and the digits
    run to the .png suffix. Only these may be deleted between recordings.
    """
    if not name.startswith('f') or not name.endswith('.png'):
        return False
    digits = name[1:-4]
    return len(digits) >= 4 and digits.isdigit() and digits.isascii()


def frame_index(name):
    """The frame number a frame filename holds, or None."""
    if not is_frame_filename(name):
        return None
    return int(name[1:-4])


def parse_frames_jsonl(text):
    """(frame indices, done dict or None) from a frames.jsonl's contents."""
    indices = []
    done = None
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        if entry.get('done'):
            done = entry
        elif isinstance(entry.get('i'), int):
            indices.append(entry['i'])
    return indices, done


def parse_frame_log(text):
    """Frame-log lines as dicts: request events keep 'line'."""
    events = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        events.append(entry)
    return events


def read_prefs(profile_dir):
    """A profile's Preferences as a dict, or None if absent/unreadable."""
    try:
        return json.loads((Path(profile_dir) / 'Preferences').read_text())
    except (OSError, ValueError):
        return None


def pref(prefs, name):
    """A dotted pref name looked up the way Chromium stores it: nested."""
    for key in name.split('.'):
        if not isinstance(prefs, dict):
            return None
        prefs = prefs.get(key)
    return prefs


def onboarding_done(profile_dir):
    return pref(read_prefs(profile_dir), 'helium.completed_onboarding')


def spaces_dict(profile_dir):
    return pref(read_prefs(profile_dir), 'rac.spaces')


def space_themes(spaces):
    """(space id, theme) per space, ignoring fields such as last_active."""
    if not isinstance(spaces, dict):
        return None
    return [(space.get('id'), space.get('theme'))
            for space in spaces.get('spaces', [])
            if isinstance(space, dict)]


# Profile folders the cases create in the worktree's build/profile.
SELFTEST_PROFILES = ('stunfin', 'stnew', 'stmain')


def forget_selftest_profiles():
    """Keeps the next launch from reopening the cases' profiles.

    Chromium reopens the profiles that had windows at the last quit. Only
    call this while no browser runs on build/profile.
    """
    path = PROFILE / 'Local State'
    try:
        state = json.loads(path.read_text())
    except (OSError, ValueError):
        return
    profile = state.get('profile')
    if not isinstance(profile, dict):
        return
    active = profile.get('last_active_profiles')
    changed = False
    if isinstance(active, list):
        kept = [name for name in active if name not in SELFTEST_PROFILES]
        changed = kept != active
        profile['last_active_profiles'] = kept
    if profile.get('last_used') in SELFTEST_PROFILES:
        profile['last_used'] = 'Default'
        changed = True
    if changed:
        tmp = path.with_suffix('.selftest-tmp')
        tmp.write_text(json.dumps(state))
        os.replace(tmp, path)


def finish_default_onboarding():
    """Marks the Default profile's tour finished, if it isn't yet.

    The harness answers requests only once a browser window has shown, and
    a Default profile with its tour unfinished opens the tour instead. Only
    call this while no browser runs on build/profile.
    """
    path = PROFILE / 'Default' / 'Preferences'
    prefs = read_prefs(path.parent)
    if not isinstance(prefs, dict) or pref(
            prefs, 'helium.completed_onboarding') is True:
        return
    helium = prefs.setdefault('helium', {})
    if not isinstance(helium, dict):
        return
    helium['completed_onboarding'] = True
    tmp = path.with_suffix('.selftest-tmp')
    tmp.write_text(json.dumps(prefs))
    os.replace(tmp, path)
    print('marked build/profile/Default onboarded so a browser window opens',
          flush=True)


def running_browsers():
    """PIDs of browsers started from this worktree's build."""
    result = subprocess.run(
        ['pgrep', '-f', str(ROOT / 'build' / 'src' / 'out')],
        capture_output=True, text=True, check=False)
    return [int(pid) for pid in result.stdout.split()]


def png_indices(dirpath):
    """Frame indices of the fNNNN.png files present in dirpath."""
    found = set()
    try:
        names = os.listdir(dirpath)
    except OSError:
        return found
    for name in names:
        index = frame_index(name)
        if index is not None:
            found.add(index)
    return found


def wait_until(cond, timeout, label, interval=POLL):
    """Polls cond() until true; raises TimeoutError with label."""
    deadline = time.monotonic() + timeout
    while True:
        if cond():
            return
        if time.monotonic() >= deadline:
            raise TimeoutError(label)
        time.sleep(interval)


class Harness:
    """One rac run under the queue, driven through the request file."""

    def __init__(self, case):
        self.case = case
        self.dir = Path(tempfile.mkdtemp(prefix=f'rac-selftest-{case}-'))
        self.req = self.dir / 'request'
        self.log = self.dir / 'browser.log'
        self.proc = None
        self._log_fd = None
        self.quit_note = None

    def __enter__(self):
        self._log_fd = open(self.log, 'wb')
        args = [
            str(ROOT / 'devutils/rac/build-queue.sh'),
            str(ROOT / 'devutils/rac/worktree.sh'), 'run',
            '--rac-launch-in-background',
            '--no-first-run',
            '--no-default-browser-check',
            '--enable-logging=stderr',
            # With several profiles in build/profile, startup may show the
            # profile picker, which is no browser window, so the harness
            # would never start answering requests.
            '--profile-directory=Default',
            f'--rac-window-screenshot={self.dir / "boot.png"}',
            f'--rac-window-screenshot-requests={self.req}',
            f'--rac-frame-log={self.dir / "frames.log"}',
        ]
        self.proc = subprocess.Popen(
            args, cwd=ROOT, stdout=self._log_fd, stderr=subprocess.STDOUT)
        # The queue may hold the run for a while; requests only work once
        # the first window has painted and been captured.
        boot = self.dir / 'boot.png'
        try:
            # The queue may make the run wait for a slot first.
            wait_until(lambda: 'build queue: got run' in self.browser_log()
                       or self.proc.poll() is not None,
                       3600, 'the queue never gave the run a slot')
            wait_until(lambda: boot.exists() or self.proc.poll() is not None,
                       180, 'no browser window was captured at startup')
            if self.proc.poll() is not None:
                raise RuntimeError(
                    f'browser run ended early with {self.proc.returncode}')
        except BaseException:
            # __exit__ doesn't run when __enter__ raises.
            self.__exit__()
            raise
        return self

    def __exit__(self, *exc):
        self.stop()
        if self._log_fd:
            self._log_fd.close()
            self._log_fd = None
        return False

    def request(self, line, timeout=30):
        """Writes one request line and waits until the browser takes it."""
        tmp = self.req.with_suffix('.tmp')
        tmp.write_text(line)
        os.replace(tmp, self.req)
        wait_until(lambda: not self.req.exists(), timeout,
                   f'request never consumed: {line}')

    def windows(self, timeout=15):
        """The `windows` verb's listing, as text."""
        out = self.dir / 'windows.txt'
        out.unlink(missing_ok=True)
        self.request(f'windows {out}', timeout)
        wait_until(lambda: out.exists()
                   and out.read_text().endswith('\n'), timeout,
                   'windows listing never written')
        return out.read_text()

    def browser_log(self):
        try:
            self._log_fd.flush()
        except (OSError, ValueError):
            pass
        try:
            return self.log.read_text(errors='replace')
        except OSError:
            return ''

    def frame_log(self):
        try:
            return (self.dir / 'frames.log').read_text()
        except OSError:
            return ''

    def frames_done(self, dirpath, timeout):
        """Waits for frames.jsonl in dirpath to get its done line."""
        parsed = ([], None)

        def check():
            nonlocal parsed
            try:
                parsed = parse_frames_jsonl(
                    (dirpath / 'frames.jsonl').read_text())
            except OSError:
                pass
            return parsed[1] is not None

        wait_until(check, timeout, f'no done line in {dirpath}')
        return parsed

    def quit(self, timeout=45):
        """Quits the browser cleanly and waits for the run to end."""
        try:
            self.request('target first')
        except TimeoutError:
            pass
        self.request(IDC_EXIT)
        try:
            self.proc.wait(timeout)
        except subprocess.TimeoutExpired:
            # An open welcome tour keeps IDC_EXIT from quitting. SIGTERM
            # through the queue is a clean shutdown too: Chromium commits
            # every profile's prefs before it exits.
            self.quit_note = 'quit by SIGTERM (IDC_EXIT left the tour open)'
            self.stop()
            return
        if self.proc.returncode != 0:
            raise RuntimeError(
                f'browser exited with {self.proc.returncode}')

    def stop(self):
        """Tears the run down if it is still up."""
        if self.proc is None or self.proc.poll() is not None:
            return
        # The queue stops its child's whole process tree on SIGTERM.
        try:
            self.proc.terminate()
            self.proc.wait(30)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait(10)


def setup_onboarding():
    """Runs before launch, so neither profile is loaded while it changes."""
    unfin = PROFILE / 'stunfin'
    fresh = PROFILE / 'stnew'
    for path in (unfin, fresh):
        if path.exists():
            shutil.rmtree(path)
    # An existing-but-unfinished profile: the folder has a Preferences
    # file, so profile-window loads it instead of creating it.
    unfin.mkdir()
    (unfin / 'Preferences').write_text('{}')


def case_onboarding(h):
    """profile-window leaves an existing profile's onboarding alone."""
    unfin = PROFILE / 'stunfin'
    fresh = PROFILE / 'stnew'
    h.request('profile-window stunfin')
    h.request('profile-window stnew')
    wait_until(lambda: 'stnew' in h.windows(), 40,
               'stnew window never appeared')
    # The unfinished profile may open its tour rather than a browser
    # window; either way its profile must be loaded by now.
    time.sleep(3)
    h.quit()
    if not read_prefs(unfin):
        raise AssertionError('stunfin was never loaded (Preferences still {})')
    done = onboarding_done(unfin)
    if done is True:
        raise AssertionError(
            'stunfin: profile-window marked an existing profile onboarded')
    if onboarding_done(fresh) is not True:
        raise AssertionError(
            'stnew: profile-window did not mark the profile it made')
    return 'stunfin kept onboarding unfinished; stnew was marked'


def case_record_dir(h):
    """The first frame lands only once the output dir exists."""
    target = h.dir / 'deep' / 'nested' / 'rec'
    h.request(f'record {target} 1500 0.5')
    indices, done = h.frames_done(target, 40)
    if not indices:
        raise AssertionError('no frames logged')
    if not (target / 'f0000.png').is_file():
        raise AssertionError('f0000.png missing in a brand-new dir')
    missing = [i for i in indices
               if not (target / f'f{i:04d}.png').is_file()]
    if missing:
        raise AssertionError(f'logged frames missing on disk: {missing[:5]}')
    # An unwritable dir must stop the record without wedging the harness.
    sfile = h.dir / 'afile'
    sfile.write_text('x')
    h.request(f'record {sfile / "rec"} 300')
    time.sleep(2)
    if 'cannot write to' not in h.browser_log():
        raise AssertionError('no error logged for an unwritable record dir')
    if 'normal' not in h.windows():
        raise AssertionError('harness wedged after failed record')
    return f'{len(indices)} frames, every logged PNG on disk'


def case_record_fail(h):
    """A frame whose write fails counts as skipped, not logged."""
    target = h.dir / 'ro'
    h.request(f'record {target} 2500 0.5')

    def first_frame():
        jsonl = target / 'frames.jsonl'
        if not jsonl.exists():
            return False
        indices, _ = parse_frames_jsonl(jsonl.read_text())
        return len(indices) >= 1

    wait_until(first_frame, 30, 'first frame never landed')
    os.chmod(target, 0o555)
    try:
        indices, done = h.frames_done(target, 45)
    finally:
        os.chmod(target, 0o755)
    if done['skipped'] < 1:
        raise AssertionError(
            f'write failures were not skipped: {done}')
    if 'write failed' not in h.browser_log():
        raise AssertionError('no write failure reached the browser log')
    missing = [i for i in indices
               if not (target / f'f{i:04d}.png').is_file()]
    if missing:
        raise AssertionError(f'failed writes still logged: {missing[:5]}')
    stray = [i for i in png_indices(target) if i not in set(indices)]
    if stray:
        raise AssertionError(f'partial PNGs left behind: {stray[:5]}')
    return f'{done["skipped"]} skipped, logged frames all on disk'


def case_record_stale(h):
    """A shorter second recording leaves no stale frames behind."""
    target = h.dir / 'reuse'
    h.request(f'record {target} 2000 0.5')
    first, _ = h.frames_done(target, 40)
    h.request(f'record {target} 700 0.5')
    second, _ = h.frames_done(target, 40)
    leftover = [i for i in png_indices(target) if i not in set(second)]
    if leftover:
        raise AssertionError(
            f'stale frames after re-record: f{leftover[0]:04d}.png '
            f'(+{len(leftover) - 1} more)')
    if len(second) >= len(first):
        return (f'second recording was not shorter '
                f'({len(second)} vs {len(first)} frames), check weaker')
    return f'{len(first)} frames -> {len(second)}, none stale'


def pointer_steps_after(events, req_text, name='pointer.x'):
    """Step events between the req line for req_text and the next req."""
    out = []
    seen = False
    for event in events:
        if event.get('ev') == 'req':
            if seen:
                break
            seen = req_text in event.get('line', '')
            continue
        if seen and event.get('ev') == 'step' and event.get('name') == name:
            out.append(event)
    return out


def case_pointer(h):
    """pointer off and a new pointer both cancel a running path."""
    h.request('profile-window stmain')
    wait_until(lambda: 'stmain' in h.windows(), 40,
               'stmain window never appeared')
    h.request('target profile:stmain')
    h.request('pointer-path 100 100 500 500 2200')
    time.sleep(0.7)
    h.request('pointer off')
    time.sleep(2.4)
    h.request('pointer-path 100 100 500 500 2200')
    time.sleep(0.7)
    h.request('pointer 40 40')
    time.sleep(2.4)
    h.quit()
    events = parse_frame_log(h.frame_log())
    ran = pointer_steps_after(events, 'pointer-path')
    if not ran:
        raise AssertionError('the path never moved the pointer')
    after_off = pointer_steps_after(events, 'pointer off')
    if after_off:
        raise AssertionError(
            f'pointer-path kept stepping after pointer off: '
            f'{len(after_off)} moves')
    after_new = pointer_steps_after(events, 'pointer 40 40')
    if len(after_new) != 1 or abs(after_new[0].get('v', -1) - 40) > 1:
        raise AssertionError(
            f'a new pointer did not cancel the path: {len(after_new)} '
            'moves after it')
    return f'path ran ({len(ran)} moves), off stopped it, new pointer won'


def case_space_theme(h):
    """A rejected space-theme saves nothing."""
    h.request('profile-window stmain')
    wait_until(lambda: 'stmain' in h.windows(), 40,
               'stmain window never appeared')
    h.request('target profile:stmain')
    h.request('space-theme 3 dark')
    # The valid call must be on disk before a later read can prove a
    # rejected call wrote nothing.
    wait_until(lambda: any(
        s.get('theme', {}).get('mode') == 'dark'
        for s in (spaces_dict(PROFILE / 'stmain') or {}).get('spaces', [])),
        90, 'space-theme 3 dark never reached stmain/Preferences')
    before = None
    for _ in range(5):
        before = spaces_dict(PROFILE / 'stmain')
        if before is not None:
            break
        time.sleep(1)
    h.request('space-theme 5 bogus')
    h.request('space-theme - bogus')
    time.sleep(8)
    after = None
    for _ in range(5):
        after = spaces_dict(PROFILE / 'stmain')
        if after is not None:
            break
        time.sleep(1)
    h.quit()
    final = spaces_dict(PROFILE / 'stmain')
    before, after, final = (space_themes(s) for s in (before, after, final))
    if before is None or before != after or before != final:
        raise AssertionError(
            f'a rejected space-theme changed the space: '
            f'{before!r} -> {final!r}')
    return 'rac.spaces identical before, during and after rejected calls'


CASES = [
    ('onboarding', case_onboarding, setup_onboarding),
    ('record_dir', case_record_dir, None),
    ('record_fail', case_record_fail, None),
    ('record_stale', case_record_stale, None),
    ('pointer', case_pointer, None),
    ('space_theme', case_space_theme, None),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--only', help='run only these cases, comma-separated')
    args = parser.parse_args()
    only = set(args.only.split(',')) if args.only else None

    if running_browsers():
        print('a browser from this worktree is already running; quit it first')
        return 2
    failures = 0
    for name, run, setup in CASES:
        if only and name not in only:
            continue
        print(f'== {name}', flush=True)
        started = time.monotonic()
        try:
            forget_selftest_profiles()
            finish_default_onboarding()
            if setup:
                setup()
            with Harness(name) as h:
                note = run(h) or 'ok'
                if h.quit_note and h.quit_note not in note:
                    note += f'; {h.quit_note}'
            shutil.rmtree(h.dir, ignore_errors=True)
            print(f'   PASS ({time.monotonic() - started:.0f}s) {note}',
                  flush=True)
        except KeyboardInterrupt:
            raise
        except BaseException as e:  # noqa: BLE001 - report, keep cases going
            failures += 1
            print(f'   FAIL ({time.monotonic() - started:.0f}s) '
                  f'{type(e).__name__}: {e}', flush=True)
            print(f'   browser log: '
                  f'{Path(tempfile.gettempdir())}/rac-selftest-{name}-*/'
                  'browser.log', flush=True)
    forget_selftest_profiles()
    # Crashpad and the code-sign clone cleanup outlive the browser briefly.
    try:
        wait_until(lambda: not running_browsers(), 90, 'helpers linger',
                   interval=1)
    except TimeoutError:
        pass
    leftover = running_browsers()
    if leftover:
        print(f'browsers still running after the cases: {leftover}')
        failures += 1
    if failures:
        print(f'{failures} case(s) failed')
        return 1
    print('all cases passed')
    return 0


if __name__ == '__main__':
    sys.exit(main())
