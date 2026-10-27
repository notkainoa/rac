#!/usr/bin/env python3

# Copyright 2026 The rac Authors
# You can use, redistribute, and/or modify this source code under
# the terms of the GPL-3.0 license that can be found in the LICENSE file.
"""Runs build-queue.sh against a temporary queue directory.

The builds are small Python commands that print siso-style progress lines and
wait for a file, so no real build runs. The real ~/.rac-build-queue is never
touched, and the queue sees a fake process list instead of the real one.

Run from the repository root:
    python3 -m unittest discover -s devutils/rac -p 'test_*.py' -v
"""

from pathlib import Path
import fcntl
import importlib.util
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest

HERE = Path(__file__).resolve().parent
QUEUE = HERE / 'build-queue.sh'

_spec = importlib.util.spec_from_file_location('build_queue', HERE / 'build_queue.py')
build_queue = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(build_queue)

# argv: release-file code line...  Prints each line, then waits until the
# release file exists ('-' for no wait) and exits with code (negative: kill
# itself with that signal). `@wait PATH` waits for a file mid-way; `@spam N`
# prints N filler lines.
FAKE_BUILD = '''
import os, pathlib, sys, time
release, code, *lines = sys.argv[1:]
def wait(path):
    while path != '-' and not pathlib.Path(path).exists():
        time.sleep(0.02)
for line in lines:
    if line.startswith('@wait '):
        wait(line[6:])
    elif line.startswith('@spam '):
        for _ in range(int(line[6:])):
            print('x' * 99)
        sys.stdout.flush()
    else:
        print(line, flush=True)
wait(release)
code = int(code)
if code < 0:
    os.kill(os.getpid(), -code)
sys.exit(code)
'''

# Ignores SIGTERM and starts a helper in its own session, like siso's
# spawn-helper, then trips the step cap.
STUBBORN_BUILD = '''
import pathlib, signal, subprocess, sys, time
signal.signal(signal.SIGTERM, signal.SIG_IGN)
helper = subprocess.Popen([sys.executable, '-c',
    'import signal, time; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(60)'],
    start_new_session=True)
pathlib.Path(sys.argv[1]).write_text(str(helper.pid))
print('[20001/84903] 1.00s S CXX obj/fake.o', flush=True)
time.sleep(60)
'''

# Runs the queue with a bug planted right after the build starts.
CRASHING_QUEUE = f'''
import sys
sys.path.insert(0, {str(HERE)!r})
import build_queue
def boom(self):
    print(f'child {{self.child.pid}}', file=sys.stderr, flush=True)
    raise RuntimeError('planted bug')
build_queue.Queue.update_holders = boom
sys.exit(build_queue.main(sys.argv[1:]))
'''

PROGRESS = '[0/100] 0.01s S CXX obj/fake.o'


def gone(pid):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return True
    return False


class StepCapTest(unittest.TestCase):

    def run_cap(self, lines, cap=20000, clock=None):
        checker = build_queue.StepCap(cap, **({'clock': clock} if clock else {}))
        return [checker.check(line.encode()) for line in lines]

    def test_shrinking_total_is_not_capped(self):
        # A real worktree incremental build.
        reasons = self.run_cap(['[0/73938] 8.17s S CXX a.o',
                                '[12/29795] 30.02s F CXX b.o',
                                '[40/19870] 43.80s F CXX c.o',
                                '[3016/3020] 95.10s F LINK rac'])
        self.assertEqual(reasons, [None] * 4)

    def test_slow_shrink_like_ci_is_not_capped(self):
        reasons = self.run_cap(['[0/60000] 5.00s S CXX a.o',
                                '[10/48000] 40.00s F CXX a.o',
                                '[30/36000] 80.00s F CXX a.o',
                                '[50/24000] 127.90s F CXX a.o',
                                '[60/15000] 128.50s F CXX a.o'])
        self.assertEqual(reasons, [None] * 5)

    def test_settled_total_is_capped(self):
        reasons = self.run_cap(['[0/84903] 181.00s S CXX a.o'])
        self.assertIn('84,903 steps', reasons[0])

    def test_stable_total_is_capped(self):
        reasons = self.run_cap(['[0/84903] 10.00s S CXX a.o',
                                '[5/84500] 75.00s F CXX a.o'])
        self.assertIsNone(reasons[0])
        self.assertIn('84,500 steps', reasons[1])

    def test_done_count_backstop(self):
        reasons = self.run_cap(['[20001/84903] 2.00s F CXX a.o'])
        self.assertIn('20,001 steps', reasons[0])

    def test_ninja_lines_use_the_clock(self):
        now = [0.0]
        clock = lambda: now[0]
        checker = build_queue.StepCap(20000, clock=clock)
        self.assertIsNone(checker.check(b'[0/84903] CXX a.o'))
        now[0] = 200
        self.assertIsNotNone(checker.check(b'[1/84903] CXX a.o'))

    def test_parse_elapsed(self):
        parse = build_queue.parse_elapsed
        self.assertEqual(parse(b'47.80s'), 47.8)
        self.assertEqual(parse(b'1m2.5s'), 62.5)
        self.assertEqual(parse(b'1h0m3s'), 3603)
        self.assertEqual(parse(b'850ms'), 0.85)
        self.assertIsNone(parse(b'CXX'))
        self.assertIsNone(parse(None))


class UntrackedBuildsTest(unittest.TestCase):

    def test_caffeinate_and_siso_count_once(self):
        siso = '/x/src/third_party/siso/cipd/siso'
        ps = '\n'.join([
            f'  101 {siso} ninja --offline -C /x/src/out/Default chrome -k 0',
            f'  102 caffeinate {siso} ninja --offline -C /x/src/out/Default chrome -k 0',
            f'  103 {siso} spawn-helper -conn_fd 3 -log_file /x/src/out/Default/h',
            f'  104 /bin/zsh -c grep {siso} ninja',
            f'  105 /w/build/src/third_party/siso/cipd/siso ninja -C /w/build/src/out/Default',
            f'  106 {siso} ninja -C/y/out/Default',
        ])
        old = os.environ.get('_RAC_BUILD_QUEUE_PS')
        os.environ['_RAC_BUILD_QUEUE_PS'] = ps
        try:
            found = build_queue.untracked_builds(['/w'])
        finally:
            if old is None:
                del os.environ['_RAC_BUILD_QUEUE_PS']
            else:
                os.environ['_RAC_BUILD_QUEUE_PS'] = old
        self.assertEqual(sorted(b['out'] for b in found),
                         ['/x/src/out/Default', '/y/out/Default'])


class QueueTest(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(subprocess.run, ['rm', '-rf', str(self.tmp)])
        self.state = self.tmp / 'queue'
        self.state.mkdir()
        # Not a git repository, so the main-checkout guard stays out of the way.
        self.cwd = self.workdir('work')
        self.env = {
            **os.environ,
            'RAC_BUILD_QUEUE_DIR': str(self.state),
            'RAC_BUILD_QUEUE_POLL': '0.05',
            'RAC_BUILD_QUEUE_MIN_FREE_GB': '0',
            'RAC_BUILD_QUEUE_STOP_GRACE': '0.5',
            '_RAC_BUILD_QUEUE_PRESSURE': '1',
            '_RAC_BUILD_QUEUE_PS': '',
        }
        self.procs = []
        self.addCleanup(self.stop_all)

    def workdir(self, name):
        path = self.tmp / name
        path.mkdir(exist_ok=True)
        return path

    def stop_all(self):
        # SIGTERM lets a queue stop its fake build; SIGKILL would orphan it.
        for proc in self.procs:
            if proc.poll() is None:
                proc.terminate()
        for proc in self.procs:
            try:
                proc.wait(10)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
            for stream in (proc.stdout, proc.stderr):
                if stream:
                    stream.close()

    def popen(self, args, cwd=None, env=None, **kwargs):
        proc = subprocess.Popen(
            args, cwd=cwd or self.cwd, env={**self.env, **(env or {})},
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **kwargs)
        self.procs.append(proc)
        return proc

    def start(self, name, *options, lines=(PROGRESS,), code=0, env=None,
              cwd=None):
        """Queues a fake build. Each name builds in its own directory."""
        release = self.tmp / f'release-{name}'
        proc = self.popen([str(QUEUE), *options, sys.executable, '-c', FAKE_BUILD,
                           str(release), str(code), *lines],
                          cwd=cwd or self.workdir(f'work-{name}'), env=env)
        return proc, release

    def queue(self, *args, env=None, cwd=None):
        return subprocess.run([str(QUEUE), *args], cwd=cwd or self.cwd,
                              env={**self.env, **(env or {})},
                              capture_output=True, text=True, timeout=30)

    def held(self):
        return sorted(p.name for p in self.state.glob('*-[12]')
                      if (p / 'holder.json').exists())

    def waiting(self):
        return len(list((self.state / 'waiting').glob('*.json')))

    def wait_until(self, check, timeout=10):
        end = time.time() + timeout
        while time.time() < end:
            if check():
                return
            time.sleep(0.05)
        self.fail(f'timed out; held {self.held()}, waiting {self.waiting()}')

    def events(self):
        log = self.state / 'queue.log'
        return [json.loads(l)['event'] for l in log.read_text().splitlines()]

    def sleeper(self, new_session=False):
        proc = subprocess.Popen(['sleep', '30'], start_new_session=new_session)
        self.addCleanup(proc.wait)
        self.addCleanup(proc.kill)
        return proc

    def dead_pid(self):
        proc = subprocess.Popen(['true'])
        proc.wait()
        return proc.pid

    def write_holder(self, slot, lock=True, **holder):
        path = self.state / slot
        path.mkdir()
        if lock:
            (path / 'lock').touch()
        (path / 'holder.json').write_text(json.dumps(
            {'worktree': '/elsewhere', 'command': 'he build', **holder}))

    # Slots and order.

    def test_two_builds_run_and_a_third_waits(self):
        _, release1 = self.start('1')
        _, release2 = self.start('2')
        self.wait_until(lambda: self.held() == ['build-1', 'build-2'])
        third, release3 = self.start('3')
        self.wait_until(lambda: self.waiting() == 1)
        status = self.queue('status').stdout
        self.assertIn('waiting for a build slot', status)
        self.assertNotIn('build-1  free', status)
        self.assertNotIn('build-2  free', status)
        release1.touch()
        self.wait_until(lambda: self.waiting() == 0)
        self.assertEqual(self.held(), ['build-1', 'build-2'])
        release2.touch()
        release3.touch()
        self.assertEqual(third.wait(10), 0)
        self.wait_until(lambda: self.held() == [])

    def test_full_build_takes_both_slots(self):
        full, release_full = self.start('full', '--full', 'D6 item 2')
        self.wait_until(lambda: self.held() == ['build-1', 'build-2'])
        other, release_other = self.start('other')
        self.wait_until(lambda: self.waiting() == 1)
        release_other.touch()
        time.sleep(0.3)
        self.assertIsNone(other.poll())
        release_full.touch()
        self.assertEqual(full.wait(10), 0)
        self.assertEqual(other.wait(10), 0)

    def test_full_build_waits_for_both_slots(self):
        _, release1 = self.start('1')
        self.wait_until(lambda: self.held() == ['build-1'])
        full, release_full = self.start('full', '--full', 'D6 item 2')
        self.wait_until(lambda: self.waiting() == 1)
        # A later normal build doesn't jump the full build's place in line.
        later, release_later = self.start('later')
        self.wait_until(lambda: self.waiting() == 2)
        time.sleep(0.3)
        self.assertEqual(self.held(), ['build-1'])
        release1.touch()
        self.wait_until(lambda: self.held() == ['build-1', 'build-2'])
        self.assertEqual(self.waiting(), 1)
        release_full.touch()
        release_later.touch()
        self.assertEqual(full.wait(10), 0)
        self.assertEqual(later.wait(10), 0)

    def test_priority_goes_first(self):
        holder, release_holder = self.start('h', '--full', 'D6 item 2')
        self.wait_until(lambda: self.held() == ['build-1', 'build-2'])
        normal, release_normal = self.start('normal')
        self.wait_until(lambda: self.waiting() == 1)
        urgent, release_urgent = self.start('urgent', '--priority')
        self.wait_until(lambda: self.waiting() == 2)
        names = sorted(p.name for p in (self.state / 'waiting').glob('*.json'))
        self.assertTrue(names[0].startswith('0-'), names)
        # Only one slot frees up, and it goes to the priority waiter.
        release_holder.touch()
        self.assertEqual(holder.wait(10), 0)
        self.wait_until(lambda: self.waiting() == 0)
        release_urgent.touch()
        release_normal.touch()
        self.assertEqual(urgent.wait(10), 0)
        self.assertEqual(normal.wait(10), 0)
        starts = [json.loads(l) for l in (self.state / 'queue.log').read_text().splitlines()]
        order = [e['priority'] for e in starts if e['event'] == 'start']
        self.assertEqual(order, [False, True, False])

    def test_run_slots_are_separate(self):
        full, release_full = self.start('full', '--full', 'D6 item 2')
        self.wait_until(lambda: self.held() == ['build-1', 'build-2'])
        run, release_run = self.start('run', '--run')
        self.wait_until(lambda: 'run-1' in self.held())
        release_run.touch()
        release_full.touch()
        self.assertEqual(run.wait(10), 0)
        self.assertEqual(full.wait(10), 0)

    def test_second_build_in_one_worktree_is_refused(self):
        _, release = self.start('a', cwd=self.cwd)
        self.wait_until(lambda: self.held() == ['build-1'])
        result = self.queue('true')
        self.assertEqual(result.returncode, 75)
        self.assertIn('already building', result.stderr)
        release.touch()

    # The step cap.

    def test_settled_step_count_stops_build_and_frees_slot(self):
        proc, _ = self.start('big', lines=['[0/84903] 200.00s S CXX obj/fake.o'])
        out, err = proc.communicate(timeout=20)
        self.assertEqual(proc.returncode, 76)
        self.assertIn('84,903 steps', err)
        self.assertEqual(self.held(), [])
        self.assertIn('cap', self.events())
        self.assertIn('84,903 steps', self.queue('log').stdout)

    def test_shrinking_total_is_not_capped(self):
        proc, release = self.start('incremental', lines=[
            '[0/73938] 8.17s S CXX a.o', '[12/29795] 30.02s F CXX b.o',
            '[40/19870] 43.80s F CXX c.o', '[3016/3020] 95.10s F LINK rac'])
        release.touch()
        self.assertEqual(proc.wait(20), 0)

    def test_done_count_backstop_stops_build(self):
        proc, _ = self.start('runaway', lines=['[20001/84903] 2.00s F CXX a.o'])
        _, err = proc.communicate(timeout=20)
        self.assertEqual(proc.returncode, 76)
        self.assertIn('already run 20,001 steps', err)

    def test_full_build_has_no_step_cap(self):
        proc, release = self.start('big', '--full', 'D6 item 2', lines=[
            '[0/84903] 200.00s S CXX a.o', '[30000/84903] 900.00s F CXX a.o'])
        self.wait_until(lambda: self.held() == ['build-1', 'build-2'])
        time.sleep(0.3)
        self.assertIsNone(proc.poll())
        release.touch()
        self.assertEqual(proc.wait(10), 0)

    def test_max_steps_option(self):
        proc, _ = self.start('small', '--max-steps', '50',
                             lines=['[0/60] 200.00s S CXX a.o'])
        self.assertEqual(proc.wait(20), 76)

    def test_stop_reaches_the_whole_tree(self):
        helper_file = self.tmp / 'helper'
        proc = self.popen([str(QUEUE), sys.executable, '-c', STUBBORN_BUILD,
                           str(helper_file)])
        _, err = proc.communicate(timeout=30)
        self.assertEqual(proc.returncode, 76, err)
        helper = int(helper_file.read_text())
        self.wait_until(lambda: gone(helper), timeout=5)
        self.assertEqual(self.held(), [])

    # Ending.

    def test_build_failure_passes_exit_code_and_frees_slot(self):
        proc, release = self.start('fail', code=3)
        release.touch()
        self.assertEqual(proc.wait(10), 3)
        self.assertEqual(self.held(), [])

    def test_build_killed_by_signal_exits_128_plus_n(self):
        proc, release = self.start('killed', code=-signal.SIGKILL)
        release.touch()
        self.assertEqual(proc.wait(10), 128 + signal.SIGKILL)
        self.assertEqual(self.held(), [])

    def test_output_passes_through(self):
        proc, release = self.start('out')
        release.touch()
        out, _ = proc.communicate(timeout=10)
        self.assertIn(PROGRESS, out)

    def test_signals_stop_build_and_free_slot(self):
        for sig in (signal.SIGTERM, signal.SIGHUP, signal.SIGINT):
            with self.subTest(sig=sig):
                proc, _ = self.start(f'sig{sig}')
                self.wait_until(lambda: self.held() == ['build-1'])
                proc.send_signal(sig)
                self.assertEqual(proc.wait(20), 128 + sig)
                self.assertEqual(self.held(), [])

    def test_broken_pipe_keeps_draining_and_frees_slot(self):
        go = self.tmp / 'go'
        proc, release = self.start('pipe', lines=[PROGRESS, f'@wait {go}',
                                                  '@spam 3000'])
        self.assertIn('[0/100]', proc.stdout.readline())
        proc.stdout.close()  # like `| head -1` exiting
        go.touch()
        time.sleep(1)
        # The build is still running and still holds its slot.
        self.assertIsNone(proc.poll())
        self.assertEqual(self.held(), ['build-1'])
        release.touch()
        self.assertEqual(proc.wait(20), 0)
        self.assertEqual(self.held(), [])

    def test_queue_error_stops_build_and_frees_slot(self):
        release = self.tmp / 'never'
        proc = self.popen([sys.executable, '-c', CRASHING_QUEUE, sys.executable,
                           '-c', FAKE_BUILD, str(release), '0', PROGRESS])
        _, err = proc.communicate(timeout=30)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn('planted bug', err)
        child = int(err.split('child ')[1].split()[0])
        self.assertTrue(gone(child))
        self.assertEqual(self.held(), [])

    # Liveness.

    def test_dead_holder_is_reaped(self):
        dead = self.dead_pid()
        self.write_holder('build-1', pid=dead, pgid=dead)
        self.write_holder('build-2', lock=False, pid=dead, pgid=None)
        proc, release = self.start('next', '--full', 'D6 item 2')
        self.wait_until(lambda: self.waiting() == 0 and self.held() == ['build-1', 'build-2'])
        release.touch()
        self.assertEqual(proc.wait(10), 0)
        self.assertEqual(self.events().count('reap'), 2)

    def test_unlocked_holder_with_reused_pid_is_reaped(self):
        # The pid is alive (it's this test), but the lock says its queue died.
        self.write_holder('build-1', pid=os.getpid(), pgid=None)
        proc, release = self.start('next', '--full', 'D6 item 2')
        release.touch()
        self.assertEqual(proc.wait(10), 0)
        self.assertIn('reap', self.events())

    def test_first_version_holder_with_live_pid_is_held(self):
        live = self.sleeper()
        self.write_holder('build-1', lock=False, pid=live.pid, pgid=12345678)
        proc, release = self.start('full', '--full', 'D6 item 2')
        self.wait_until(lambda: self.waiting() == 1)
        time.sleep(0.3)
        self.assertEqual(self.held(), ['build-1'])
        status = self.queue('status').stdout
        self.assertIn(f'pid {live.pid}', status)
        self.assertNotIn('holder gone', status)
        live.kill()
        live.wait()
        self.wait_until(lambda: self.waiting() == 0)
        release.touch()
        self.assertEqual(proc.wait(10), 0)

    def test_build_outliving_its_queue_still_holds_the_slot(self):
        build = self.sleeper(new_session=True)
        self.write_holder('build-1', pid=self.dead_pid(), pgid=build.pid)
        proc, release = self.start('full', '--full', 'D6 item 2')
        self.wait_until(lambda: self.waiting() == 1)
        self.assertIn('still running', self.queue('status').stdout)
        build.kill()
        build.wait()
        self.wait_until(lambda: self.waiting() == 0)
        release.touch()
        self.assertEqual(proc.wait(10), 0)

    def test_dead_tickets_are_reaped(self):
        waiting = self.state / 'waiting'
        waiting.mkdir()
        # A new-style ticket whose lock is free, though its pid lives on.
        (waiting / '0-000000001.json').write_text(json.dumps(
            {'pid': os.getpid(), 'pool': 'build', 'need': 1}))
        (waiting / '0-000000001.lock').touch()
        # A first-version ticket whose pid died.
        (waiting / '0-000000002.json').write_text(json.dumps(
            {'pid': self.dead_pid(), 'pool': 'build', 'need': 2}))
        self.assertEqual(self.queue('true').returncode, 0)
        self.assertEqual(list(waiting.iterdir()), [])

    def test_stale_mutex_does_not_block(self):
        # A first-version mutex directory is ignored.
        (self.state / '.mutex').mkdir()
        # A process that died holding the mutex file releases it.
        locker = subprocess.Popen([sys.executable, '-c', (
            'import fcntl, os, sys, time\n'
            f'fd = os.open({str(self.state / ".mutex.lock")!r}, os.O_RDWR | os.O_CREAT)\n'
            'fcntl.flock(fd, fcntl.LOCK_EX)\n'
            'print("locked", flush=True)\n'
            'time.sleep(60)\n')], stdout=subprocess.PIPE, text=True)
        self.addCleanup(locker.stdout.close)
        self.assertEqual(locker.stdout.readline().strip(), 'locked')
        blocked = self.popen([str(QUEUE), 'true'])
        time.sleep(0.5)
        self.assertIsNone(blocked.poll())
        locker.kill()
        locker.wait()
        self.assertEqual(blocked.wait(10), 0)

    # Guards.

    def test_manual_lock_holds_build_slots(self):
        (self.state / 'manual').mkdir(parents=True)
        proc, release = self.start('blocked')
        self.wait_until(lambda: self.waiting() == 1)
        self.assertEqual(self.held(), [])
        (self.state / 'manual').rmdir()
        self.wait_until(lambda: self.held() == ['build-1'])
        release.touch()
        self.assertEqual(proc.wait(10), 0)
        _, err = proc.communicate(timeout=10)
        self.assertIn('the manual lock', err)
        self.assertIn('has held both build slots for', err)

    def test_outside_build_counts_once_and_holders_are_excluded(self):
        mine = self.workdir('work-mine')
        siso = '/x/src/third_party/siso/cipd/siso'
        outside = '\n'.join([
            f'  101 {siso} ninja --offline -C /x/src/out/Default chrome',
            f'  102 caffeinate {siso} ninja --offline -C /x/src/out/Default chrome',
        ])
        # The first queue's own build, once it runs.
        ps = outside + (f'\n  103 {mine}/build/src/third_party/siso/cipd/siso '
                        f'ninja -C {mine}/build/src/out/Default')
        env = {'_RAC_BUILD_QUEUE_PS': outside}
        first, release_first = self.start('mine', env=env)
        self.wait_until(lambda: self.held() == ['build-1'])
        second, release_second = self.start('second', env=env)
        self.wait_until(lambda: self.waiting() == 1)
        time.sleep(0.3)
        self.assertEqual(self.held(), ['build-1'])
        status = self.queue('status', env={'_RAC_BUILD_QUEUE_PS': ps}).stdout
        self.assertEqual(status.count('outside the queue'), 1, status)
        self.assertIn('/x/src/out/Default', status)
        release_first.touch()
        self.wait_until(lambda: self.waiting() == 0)
        release_second.touch()
        self.assertEqual(first.wait(10), 0)
        self.assertEqual(second.wait(10), 0)

    def test_refuses_on_low_disk(self):
        proc, release = self.start('disk', env={'RAC_BUILD_QUEUE_MIN_FREE_GB': '1e12'})
        _, err = proc.communicate(timeout=10)
        self.assertEqual(proc.returncode, 75)
        self.assertIn('GB free', err)
        self.assertEqual(self.held(), [])
        self.assertEqual(self.waiting(), 0)

    def test_waits_under_critical_memory_pressure(self):
        proc, release = self.start('mem', env={'_RAC_BUILD_QUEUE_PRESSURE': '4'})
        self.wait_until(lambda: self.waiting() == 1)
        time.sleep(0.3)
        self.assertEqual(self.held(), [])
        proc.kill()

    def test_refuses_main_checkout(self):
        repo = self.tmp / 'repo'
        repo.mkdir()
        subprocess.run(['git', 'init', '-q', str(repo)], check=True)
        result = self.queue('true', cwd=repo)
        self.assertEqual(result.returncode, 75)
        self.assertIn('main checkout', result.stderr)
        result = self.queue('--allow-main', 'true', cwd=repo)
        self.assertEqual(result.returncode, 0)

    # Arguments.

    def test_argument_checks(self):
        cases = [
            ('--full', ' ', 'true'),
            ('--full', 'D6', 'devutils/rac/worktree.sh', 'run'),
            ('--run', '--full', 'D6', 'true'),
            ('--run', 'he', 'build'),
            ('--max-steps', '0', 'true'),
            ('--max-steps', '-5', 'true'),
            ('log', 'abc'),
            ('log', '0'),
        ]
        for case in cases:
            with self.subTest(case=case):
                result = self.queue(*case)
                self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(self.waiting(), 0)

    def test_he_without_dev_sh_is_refused_before_queueing(self):
        result = self.queue('he', 'build')
        self.assertEqual(result.returncode, 75)
        self.assertIn('no dev.sh', result.stderr)
        self.assertFalse((self.state / 'queue.log').exists())

    def test_missing_command_frees_slot(self):
        result = self.queue('/nonexistent/command')
        self.assertEqual(result.returncode, 127)
        self.assertEqual(self.held(), [])

    # Log.

    def test_log_lists_events_and_survives_bad_lines(self):
        self.assertEqual(self.queue('true').returncode, 0)
        with open(self.state / 'queue.log', 'a') as f:
            f.write('not json\n[1, 2]\n{"event": "cap", "steps": "x"}\n')
        self.assertEqual(self.queue('true').returncode, 0)
        result = self.queue('log')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('wait', result.stdout)
        self.assertIn('start', result.stdout)
        self.assertIn('end', result.stdout)
        self.assertIn('unreadable line', result.stdout)
        self.assertEqual(len(self.queue('log', '2').stdout.splitlines()), 2)


if __name__ == '__main__':
    unittest.main()
