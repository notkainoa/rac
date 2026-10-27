#!/usr/bin/env python3

# Copyright 2026 The rac Authors
# You can use, redistribute, and/or modify this source code under
# the terms of the GPL-3.0 license that can be found in the LICENSE file.
"""Runs build-queue.sh against a temporary queue directory.

The builds are small Python commands that wait for a file, so no real build
runs. The real ~/.rac-build-queue is never touched.

Run from the repository root:
    python3 -m unittest discover -s devutils/rac -p 'test_*.py' -v
"""

from pathlib import Path
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

# Prints a siso-style progress line, then waits until its release file exists.
FAKE_BUILD = '''
import pathlib, sys, time
print(f"[0/{sys.argv[2]}] 0.01s S CXX obj/fake.o", flush=True)
release = pathlib.Path(sys.argv[1])
while not release.exists():
    time.sleep(0.05)
sys.exit(int(sys.argv[3]))
'''


class QueueTest(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(subprocess.run, ['rm', '-rf', str(self.tmp)])
        self.state = self.tmp / 'queue'
        # Not a git repository, so the main-checkout guard stays out of the way.
        self.cwd = self.tmp / 'work'
        self.cwd.mkdir()
        self.env = {
            **os.environ,
            'RAC_BUILD_QUEUE_DIR': str(self.state),
            'RAC_BUILD_QUEUE_POLL': '0.05',
            'RAC_BUILD_QUEUE_MIN_FREE_GB': '0',
            '_RAC_BUILD_QUEUE_PRESSURE': '1',
        }
        self.procs = []
        self.addCleanup(self.stop_all)

    def stop_all(self):
        for proc in self.procs:
            if proc.poll() is None:
                proc.kill()
            proc.communicate()

    def start(self, name, *options, steps=100, code=0, env=None):
        release = self.tmp / f'release-{name}'
        proc = subprocess.Popen(
            [str(QUEUE), *options, sys.executable, '-c', FAKE_BUILD,
             str(release), str(steps), str(code)],
            cwd=self.cwd, env={**self.env, **(env or {})},
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.procs.append(proc)
        return proc, release

    def queue(self, *args, env=None):
        return subprocess.run([str(QUEUE), *args], cwd=self.cwd,
                              env={**self.env, **(env or {})},
                              capture_output=True, text=True)

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
        time.sleep(0.3)
        self.assertEqual(self.held(), ['build-1'])
        release1.touch()
        self.wait_until(lambda: self.held() == ['build-1', 'build-2'])
        self.assertEqual(self.waiting(), 1)
        release_full.touch()
        release_later.touch()
        self.assertEqual(full.wait(10), 0)
        self.assertEqual(later.wait(10), 0)

    def test_step_cap_stops_build_and_frees_slot(self):
        proc, _ = self.start('big', steps=84903)
        out, err = proc.communicate(timeout=20)
        self.assertEqual(proc.returncode, 76)
        self.assertIn('84,903 steps', err)
        self.assertEqual(self.held(), [])
        self.assertIn('cap', self.events())

    def test_full_build_has_no_step_cap(self):
        proc, release = self.start('big', '--full', 'D6 item 2', steps=84903)
        self.wait_until(lambda: self.held() == ['build-1', 'build-2'])
        time.sleep(0.3)
        self.assertIsNone(proc.poll())
        release.touch()
        self.assertEqual(proc.wait(10), 0)

    def test_max_steps_option(self):
        proc, release = self.start('small', '--max-steps', '50', steps=60)
        self.assertEqual(proc.wait(20), 76)

    def test_build_failure_passes_exit_code_and_frees_slot(self):
        proc, release = self.start('fail', code=3)
        release.touch()
        self.assertEqual(proc.wait(10), 3)
        self.assertEqual(self.held(), [])

    def test_output_passes_through(self):
        proc, release = self.start('out')
        release.touch()
        out, _ = proc.communicate(timeout=10)
        self.assertIn('[0/100] 0.01s S CXX obj/fake.o', out)

    def test_dead_holder_is_reaped(self):
        slot = self.state / 'build-1'
        slot.mkdir(parents=True)
        dead = subprocess.Popen(['true'])
        dead.wait()
        (slot / 'holder.json').write_text(json.dumps({'pid': dead.pid, 'pgid': dead.pid}))
        (self.state / 'build-2').mkdir()
        (self.state / 'build-2' / 'holder.json').write_text(
            json.dumps({'pid': dead.pid, 'pgid': None}))
        proc, release = self.start('next', '--full', 'D6 item 2')
        self.wait_until(lambda: self.held() == ['build-1', 'build-2'])
        release.touch()
        self.assertEqual(proc.wait(10), 0)
        self.assertIn('reap', self.events())

    def test_manual_lock_holds_build_slots(self):
        (self.state / 'manual').mkdir(parents=True)
        proc, release = self.start('blocked')
        self.wait_until(lambda: self.waiting() == 1)
        self.assertEqual(self.held(), [])
        (self.state / 'manual').rmdir()
        self.wait_until(lambda: self.held() == ['build-1'])
        release.touch()
        self.assertEqual(proc.wait(10), 0)

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

    def test_interrupt_stops_build_and_frees_slot(self):
        proc, release = self.start('int')
        self.wait_until(lambda: self.held() == ['build-1'])
        proc.send_signal(signal.SIGTERM)
        self.assertEqual(proc.wait(20), 130)
        self.assertEqual(self.held(), [])

    def test_refuses_main_checkout(self):
        repo = self.tmp / 'repo'
        repo.mkdir()
        subprocess.run(['git', 'init', '-q', str(repo)], check=True)
        result = subprocess.run([str(QUEUE), 'true'], cwd=repo, env=self.env,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 75)
        self.assertIn('main checkout', result.stderr)
        result = subprocess.run([str(QUEUE), '--allow-main', 'true'], cwd=repo,
                                env=self.env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)

    def test_full_needs_note(self):
        result = self.queue('--full', ' ', 'true')
        self.assertEqual(result.returncode, 2)

    def test_log_lists_events(self):
        self.assertEqual(self.queue('true').returncode, 0)
        out = self.queue('log').stdout
        self.assertIn('wait', out)
        self.assertIn('start', out)
        self.assertIn('end', out)


if __name__ == '__main__':
    unittest.main()
